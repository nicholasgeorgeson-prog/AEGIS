"""
Data Routes Blueprint

Routes for:
- SOW generation
- Metrics dashboard  
- Configuration sharing
- Function categories management
- Role-function tags
- Document categories
- Role required actions
- Role reports
- Decision learner operations
- Data utilities
- Report generation
"""

import json
import socket
from typing import Dict
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, make_response, Response, send_file, g, current_app
from routes._shared import (
    require_csrf,
    handle_api_errors,
    api_error_response,
    api_success_response,
    config,
    logger,
    SessionManager,
    ValidationError
)
import routes._shared as _shared


data_bp = Blueprint('data', __name__)


def get_scan_history_db():
    """Get scan history database instance."""
    from scan_history import get_scan_history_db as _get_db
    return _get_db()


def db_connection(db_path):
    """Get a database connection context manager."""
    from scan_history import db_connection as _db_conn
    return _db_conn(db_path)


@data_bp.route('/api/sow/generate', methods=['POST'])
@handle_api_errors
def generate_sow():
    """
    Generate a Statement of Work HTML document.
    Accepts configuration JSON and returns a standalone HTML file.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        data = request.get_json()
        if not data:
            return (jsonify({'success': False, 'error': 'No configuration provided'}), 400)
        else:
            config = data.get('config', {})
            db = get_scan_history_db()
            dictionary = db.get_role_dictionary(include_inactive=False)
            with db.connection() as (conn, cursor):
                cursor.execute('\n        SELECT rft.role_name, rft.function_code,\n               fc.name as function_name, fc.color as function_color\n        FROM role_function_tags rft\n        LEFT JOIN function_categories fc ON fc.code = rft.function_code\n    ')
                tag_rows = cursor.fetchall()
                tag_lookup = {}
                for tr in tag_rows:
                    rn = tr['role_name'].lower().strip()
                    if rn not in tag_lookup:
                        tag_lookup[rn] = []
                    tag_lookup[rn].append({'code': tr['function_code'], 'name': tr['function_name'] or tr['function_code'], 'color': tr['function_color'] or '#3b82f6'})
                for role in dictionary:
                    rn = role.get('role_name', '').lower().strip()
                    role['function_tags'] = tag_lookup.get(rn, [])
                cursor.execute('SELECT * FROM function_categories WHERE is_active = 1 ORDER BY sort_order, code')
                function_cats = [dict(row) for row in cursor.fetchall()]
                cursor.execute('SELECT * FROM role_relationships')
                relationships = [dict(row) for row in cursor.fetchall()]
                cursor.execute('\n        SELECT d.id, d.filename, d.filepath, d.word_count, d.paragraph_count,\n               COUNT(s.id) as scan_count,\n               MAX(s.score) as latest_score,\n               MAX(s.grade) as latest_grade\n        FROM documents d\n        LEFT JOIN scans s ON s.document_id = d.id\n        GROUP BY d.id ORDER BY d.filename\n    ')
                documents = [dict(row) for row in cursor.fetchall()]
                cursor.execute('\n        SELECT ss.*, d.filename as source_document\n        FROM scan_statements ss\n        JOIN scans s ON s.id = ss.scan_id\n        JOIN documents d ON d.id = s.document_id\n        WHERE s.id IN (SELECT MAX(id) FROM scans GROUP BY document_id)\n        ORDER BY ss.document_id, ss.position_index\n    ')
                statements = [dict(row) for row in cursor.fetchall()]
            selected_doc_ids = config.get('document_ids')
            if selected_doc_ids:
                selected_set = set(selected_doc_ids)
                documents = [d for d in documents if d.get('id') in selected_set]
                statements = [s for s in statements if s.get('document_id') in selected_set]
            import socket as _socket
            from sow_generator import generate_sow_html
            metadata = {'version': '4.6.1', 'export_date': datetime.now(timezone.utc).isoformat(), 'hostname': _socket.gethostname()}
            html_content = generate_sow_html(config=config, roles=dictionary, statements=statements, documents=documents, function_categories=function_cats, relationships=relationships, metadata=metadata)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            title_slug = config.get('title', 'SOW').replace(' ', '_')[:30]
            date_str = datetime.now().strftime('%Y-%m-%d')
            response.headers['Content-Disposition'] = f'attachment; filename=AEGIS_SOW_{title_slug}_{date_str}.html'
            return response
@data_bp.route('/api/metrics/landing', methods=['GET'])
@handle_api_errors
def get_metrics_landing():
    """
    v4.8.3: Lightweight metrics for the landing page — single DB call.
    Returns just the counts/summaries needed for dashboard tiles.
    Replaces 4 separate API calls (scan-history, roles/dictionary, extraction/capabilities, version).
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Metrics not available'})

    db = get_scan_history_db()
    with db.connection() as (conn, cursor):
        # Core scan/doc counts (always available)
        cursor.execute('''
            SELECT
                (SELECT COUNT(*) FROM scans) as total_scans,
                (SELECT COUNT(*) FROM documents) as total_docs,
                (SELECT COALESCE(ROUND(AVG(score)), 0) FROM scans WHERE score IS NOT NULL) as avg_score
        ''')
        core = cursor.fetchone()
        total_scans = core[0] or 0
        total_docs = core[1] or 0
        avg_score = core[2] or 0

        # v5.0.5: Role counts — try role_dictionary first, fall back to roles table
        total_roles = 0
        adjudicated = 0
        deliverable = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM role_dictionary WHERE is_active = 1')
            total_roles = cursor.fetchone()[0] or 0
            if total_roles > 0:
                cursor.execute('''SELECT COUNT(*) FROM role_dictionary WHERE is_active = 1
                    AND role_disposition IS NOT NULL AND role_disposition != '' AND role_disposition != 'pending' ''')
                adjudicated = cursor.fetchone()[0] or 0
                cursor.execute('SELECT SUM(CASE WHEN is_deliverable = 1 THEN 1 ELSE 0 END) FROM role_dictionary WHERE is_active = 1')
                deliverable = cursor.fetchone()[0] or 0
        except Exception:
            pass

        # Fallback: if role_dictionary is empty/missing, count from roles table
        if total_roles == 0:
            try:
                cursor.execute('SELECT COUNT(DISTINCT role_name) FROM roles')
                total_roles = cursor.fetchone()[0] or 0
            except Exception:
                pass

        # Total statements from latest scan per document (newer table — safe query)
        total_statements = 0
        try:
            cursor.execute('''
                SELECT COALESCE(SUM(stmt_count), 0) FROM (
                    SELECT COUNT(*) as stmt_count FROM scan_statements ss
                    JOIN scans s ON s.id = ss.scan_id
                    WHERE s.id IN (SELECT MAX(id) FROM scans GROUP BY document_id)
                    GROUP BY s.document_id
                )
            ''')
            total_statements = cursor.fetchone()[0] or 0
        except Exception:
            pass

        # Recent scans for the "Recent Documents" section
        cursor.execute('''
            SELECT s.id, d.filename, s.scan_time, s.score, s.grade, s.issue_count,
                   s.word_count, d.id as document_id
            FROM scans s JOIN documents d ON d.id = s.document_id
            ORDER BY s.scan_time DESC LIMIT 5
        ''')
        recent_scans = [dict(r) for r in cursor.fetchall()]

    # Checker count from version.json (file read, not DB)
    checker_count = 84  # default
    try:
        version_path = Path(__file__).resolve().parent.parent / 'version.json'
        if version_path.exists():
            with open(version_path, encoding='utf-8') as f:
                vdata = json.load(f)
                checker_count = vdata.get('checker_count', 84)
    except Exception as e:
        current_app.logger.warning(f'Could not read checker_count from version.json: {e}')

    return jsonify({'success': True, 'data': {
        'total_scans': total_scans,
        'total_docs': total_docs,
        'total_roles': total_roles,
        'avg_score': avg_score,
        'adjudicated': adjudicated,
        'deliverable': deliverable,
        'total_statements': total_statements,
        'checker_count': checker_count,
        'recent_scans': recent_scans
    }})


@data_bp.route('/api/metrics/dashboard', methods=['GET'])
@handle_api_errors
def get_metrics_dashboard():
    """
    v4.6.1: Comprehensive metrics endpoint for the Analytics Command Center.
    Returns all data needed for the metrics dashboard in a single call.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})

    db = get_scan_history_db()
    data = {}

    def _safe_query(cursor, query, default=None):
        """Execute query safely, returning default on table/column errors."""
        try:
            cursor.execute(query)
            return cursor.fetchall() if default is None else cursor.fetchone()
        except Exception as e:
            if 'no such table' in str(e).lower() or 'no such column' in str(e).lower():
                current_app.logger.warning(f'Metrics query skipped (missing table/column): {e}')
                return default if default is not None else []
            raise

    with db.connection() as (conn, cursor):
        # === OVERVIEW (core tables — documents, scans) ===
        cursor.execute('SELECT COUNT(*) FROM documents')
        total_docs = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COUNT(*) FROM scans')
        total_scans = cursor.fetchone()[0] or 0

        # scan_statements count (newer table — safe query)
        total_stmts = 0
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM scan_statements ss
                JOIN scans s ON s.id = ss.scan_id
                WHERE s.id IN (SELECT MAX(id) FROM scans GROUP BY document_id)
            ''')
            total_stmts = cursor.fetchone()[0] or 0
        except Exception:
            pass

        # role_dictionary count (newer table — safe query)
        total_roles = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM role_dictionary WHERE is_active = 1')
            total_roles = cursor.fetchone()[0] or 0
        except Exception:
            try:
                cursor.execute('SELECT COUNT(DISTINCT role_name) FROM roles')
                total_roles = cursor.fetchone()[0] or 0
            except Exception:
                pass

        cursor.execute('SELECT AVG(score), SUM(issue_count), SUM(word_count), MAX(scan_time) FROM scans')
        agg = cursor.fetchone()
        avg_score = round(agg[0], 1) if agg[0] else 0
        total_issues = agg[1] or 0
        total_words = agg[2] or 0
        last_scan = agg[3] or None
        cursor.execute('SELECT AVG(word_count) FROM documents WHERE word_count > 0')
        avg_wc_row = cursor.fetchone()
        avg_word_count = round(avg_wc_row[0]) if avg_wc_row[0] else 0

        data['overview'] = {
            'total_documents': total_docs, 'total_scans': total_scans,
            'total_statements': total_stmts, 'total_roles': total_roles,
            'total_issues': total_issues, 'avg_score': avg_score,
            'avg_word_count': avg_word_count, 'total_word_count': total_words,
            'last_scan_time': last_scan
        }

        # === DOCUMENTS LIST ===
        documents = []
        try:
            cursor.execute('''
                SELECT d.id, d.filename, d.word_count, d.scan_count, d.first_scan, d.last_scan,
                       s.score as latest_score, s.grade as latest_grade, s.issue_count,
                       (SELECT COUNT(DISTINCT dr.role_id) FROM document_roles dr WHERE dr.document_id = d.id) as role_count,
                       dc.category_type, dc.function_code
                FROM documents d
                LEFT JOIN scans s ON s.document_id = d.id AND s.id = (SELECT MAX(id) FROM scans WHERE document_id = d.id)
                LEFT JOIN document_categories dc ON dc.document_id = d.id
                ORDER BY d.filename
            ''')
            for row in cursor.fetchall():
                documents.append({
                    'id': row['id'], 'filename': row['filename'],
                    'word_count': row['word_count'] or 0, 'scan_count': row['scan_count'] or 0,
                    'first_scan': row['first_scan'], 'last_scan': row['last_scan'],
                    'latest_score': row['latest_score'], 'latest_grade': row['latest_grade'],
                    'issue_count': row['issue_count'] or 0, 'role_count': row['role_count'] or 0,
                    'statement_count': 0,
                    'category_type': row['category_type'], 'function_code': row['function_code']
                })
        except Exception as e:
            current_app.logger.warning(f'Metrics documents query failed, using fallback: {e}')
            cursor.execute('''
                SELECT d.id, d.filename, d.word_count, d.scan_count, d.first_scan, d.last_scan,
                       s.score as latest_score, s.grade as latest_grade, s.issue_count
                FROM documents d
                LEFT JOIN scans s ON s.document_id = d.id AND s.id = (SELECT MAX(id) FROM scans WHERE document_id = d.id)
                ORDER BY d.filename
            ''')
            for row in cursor.fetchall():
                documents.append({
                    'id': row['id'], 'filename': row['filename'],
                    'word_count': row['word_count'] or 0, 'scan_count': row['scan_count'] or 0,
                    'first_scan': row['first_scan'], 'last_scan': row['last_scan'],
                    'latest_score': row['latest_score'], 'latest_grade': row['latest_grade'],
                    'issue_count': row['issue_count'] or 0, 'role_count': 0,
                    'statement_count': 0, 'category_type': None, 'function_code': None
                })
        data['documents'] = documents

        # === SCANS LIST ===
        cursor.execute('''
            SELECT s.id, s.document_id, d.filename, s.scan_time, s.score, s.grade,
                   s.issue_count, s.word_count
            FROM scans s
            JOIN documents d ON d.id = s.document_id
            ORDER BY s.scan_time DESC
            LIMIT 200
        ''')
        scans = []
        for row in cursor.fetchall():
            scans.append({
                'id': row['id'], 'document_id': row['document_id'],
                'filename': row['filename'], 'scan_time': row['scan_time'],
                'score': row['score'], 'grade': row['grade'],
                'issue_count': row['issue_count'] or 0, 'word_count': row['word_count'] or 0
            })
        data['scans'] = scans

        # === STATEMENTS (scan_statements — newer table) ===
        by_directive = {}
        by_role = {}
        by_doc = {}
        by_level = {}
        try:
            cursor.execute('''
                SELECT ss.directive, ss.role, ss.level, ss.document_id, d.filename
                FROM scan_statements ss
                JOIN scans s ON s.id = ss.scan_id
                JOIN documents d ON d.id = ss.document_id
                WHERE s.id IN (SELECT MAX(id) FROM scans GROUP BY document_id)
            ''')
            for sr in cursor.fetchall():
                d_val = (sr['directive'] or '').lower().strip()
                if d_val:
                    by_directive[d_val] = by_directive.get(d_val, 0) + 1
                r = (sr['role'] or '').strip()
                if r:
                    by_role[r] = by_role.get(r, 0) + 1
                did = sr['document_id']
                fn = sr['filename']
                if did not in by_doc:
                    by_doc[did] = {'doc_id': did, 'filename': fn, 'count': 0}
                by_doc[did]['count'] += 1
                lv = str(sr['level'] or 1)
                by_level[lv] = by_level.get(lv, 0) + 1
        except Exception as e:
            current_app.logger.warning(f'Metrics statements query skipped: {e}')

        data['statements'] = {
            'total': total_stmts, 'by_directive': by_directive,
            'by_role': sorted([{'role': k, 'count': v} for k, v in by_role.items()], key=lambda x: -x['count'])[:20],
            'by_document': sorted(list(by_doc.values()), key=lambda x: -x['count'])[:20],
            'by_level': by_level
        }

        # === ROLES (role_dictionary — newer table) ===
        total_extracted = 0
        total_adj = 0
        adj_confirmed = 0
        adj_deliverable = 0
        adj_rejected = 0
        by_category = []
        by_source = []
        top_roles = []
        func_coverage = []
        try:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN is_active = 1 AND is_deliverable = 0 THEN 1 ELSE 0 END) as confirmed,
                       SUM(CASE WHEN is_deliverable = 1 THEN 1 ELSE 0 END) as deliverable,
                       SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as rejected
                FROM role_dictionary
            ''')
            ra = cursor.fetchone()
            total_adj = ra['total'] or 0
            adj_confirmed = ra['confirmed'] or 0
            adj_deliverable = ra['deliverable'] or 0
            adj_rejected = ra['rejected'] or 0
            cursor.execute('SELECT COUNT(*) FROM roles')
            total_extracted = cursor.fetchone()[0] or 0
            cursor.execute('''
                SELECT category, COUNT(*) as cnt FROM role_dictionary
                WHERE is_active = 1 GROUP BY category ORDER BY cnt DESC
            ''')
            by_category = [{'category': row['category'] or 'Uncategorized', 'count': row['cnt']} for row in cursor.fetchall()]
            cursor.execute('''
                SELECT source, COUNT(*) as cnt FROM role_dictionary
                GROUP BY source ORDER BY cnt DESC
            ''')
            by_source = [{'source': row['source'] or 'unknown', 'count': row['cnt']} for row in cursor.fetchall()]
        except Exception as e:
            current_app.logger.warning(f'Metrics role_dictionary query skipped: {e}')
            try:
                cursor.execute('SELECT COUNT(*) FROM roles')
                total_extracted = cursor.fetchone()[0] or 0
            except Exception:
                pass

        try:
            cursor.execute('''
                SELECT role_name, document_count, total_mentions FROM roles
                ORDER BY document_count DESC LIMIT 15
            ''')
            top_roles = [{'role': row['role_name'], 'document_count': row['document_count'] or 0, 'mention_count': row['total_mentions'] or 0} for row in cursor.fetchall()]
        except Exception:
            pass

        try:
            cursor.execute('''
                SELECT fc.code, fc.name, fc.color, COUNT(rft.id) as role_count
                FROM function_categories fc
                LEFT JOIN role_function_tags rft ON rft.function_code = fc.code
                WHERE fc.is_active = 1
                GROUP BY fc.code
                ORDER BY role_count DESC
            ''')
            func_coverage = [{'code': row['code'], 'name': row['name'], 'color': row['color'] or '#3b82f6', 'role_count': row['role_count'] or 0} for row in cursor.fetchall()]
        except Exception:
            pass

        data['roles'] = {
            'total_extracted': total_extracted, 'total_adjudicated': total_adj,
            'total_deliverable': adj_deliverable, 'total_rejected': adj_rejected,
            'total_confirmed': adj_confirmed, 'by_category': by_category,
            'by_source': by_source, 'top_by_documents': top_roles,
            'function_coverage': func_coverage
        }

        # === QUALITY ANALYSIS ===
        cursor.execute('SELECT score FROM scans WHERE score IS NOT NULL')
        scores = [row['score'] for row in cursor.fetchall()]
        score_dist = {}
        for s in scores:
            bucket = min(s // 10 * 10, 90)
            label = f'{bucket}-{bucket + 10}'
            score_dist[label] = score_dist.get(label, 0) + 1
        for i in range(0, 100, 10):
            label = f'{i}-{i + 10}'
            if label not in score_dist:
                score_dist[label] = 0

        cursor.execute('SELECT grade, COUNT(*) as cnt FROM scans WHERE grade IS NOT NULL GROUP BY grade')
        grade_dist = {row['grade']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute('SELECT results_json FROM scans WHERE results_json IS NOT NULL ORDER BY id DESC LIMIT 100')
        issue_cats = {}
        top_issue_msgs = {}
        for row in cursor.fetchall():
            try:
                results = json.loads(row['results_json']) if row['results_json'] else {}
                for issue in results.get('issues', []):
                    cat = issue.get('category', 'Unknown')
                    issue_cats[cat] = issue_cats.get(cat, 0) + 1
                    msg = issue.get('message', '')[:80]
                    if msg:
                        key = (msg, cat)
                        top_issue_msgs[key] = top_issue_msgs.get(key, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue

        data['quality'] = {
            'score_distribution': sorted([{'range': k, 'count': v} for k, v in score_dist.items()], key=lambda x: int(x['range'].split('-')[0])),
            'grade_distribution': grade_dist,
            'score_trend': [{'scan_time': s['scan_time'], 'score': s['score'], 'filename': s['filename']} for s in reversed(scans[:50]) if s['score'] is not None],
            'issue_categories': sorted([{'category': k, 'count': v} for k, v in issue_cats.items()], key=lambda x: -x['count'])[:15],
            'top_issues': sorted([{'message': k[0], 'category': k[1], 'count': v} for k, v in top_issue_msgs.items()], key=lambda x: -x['count'])[:10]
        }

        # === DOCUMENTS META (document_categories — newer table) ===
        by_cat_type = []
        by_func = []
        try:
            cursor.execute('''
                SELECT category_type, COUNT(*) as cnt FROM document_categories
                GROUP BY category_type ORDER BY cnt DESC
            ''')
            by_cat_type = [{'type': row['category_type'], 'count': row['cnt']} for row in cursor.fetchall()]
            cursor.execute('''
                SELECT fc.code, fc.name, fc.color, COUNT(dc.id) as cnt
                FROM function_categories fc
                LEFT JOIN document_categories dc ON dc.function_code = fc.code
                WHERE fc.is_active = 1
                GROUP BY fc.code ORDER BY cnt DESC
            ''')
            by_func = [{'code': row['code'], 'name': row['name'], 'color': row['color'] or '#3b82f6', 'count': row['cnt'] or 0} for row in cursor.fetchall()]
        except Exception as e:
            current_app.logger.warning(f'Metrics document_categories query skipped: {e}')

        wc_buckets = {'< 1K': 0, '1K-5K': 0, '5K-10K': 0, '10K-25K': 0, '25K+': 0}
        for doc in documents:
            wc = doc.get('word_count', 0) or 0
            if wc < 1000:
                wc_buckets['< 1K'] += 1
            elif wc < 5000:
                wc_buckets['1K-5K'] += 1
            elif wc < 10000:
                wc_buckets['5K-10K'] += 1
            elif wc < 25000:
                wc_buckets['10K-25K'] += 1
            else:
                wc_buckets['25K+'] += 1

        data['documents_meta'] = {
            'by_category_type': by_cat_type, 'by_function': by_func,
            'word_count_distribution': [{'range': k, 'count': v} for k, v in wc_buckets.items()]
        }

        # === RELATIONSHIPS (role_relationships — newer table) ===
        rel_types = []
        total_rels = 0
        try:
            cursor.execute('SELECT relationship_type, COUNT(*) as cnt FROM role_relationships GROUP BY relationship_type')
            rel_types = [{'type': row['relationship_type'], 'count': row['cnt']} for row in cursor.fetchall()]
            cursor.execute('SELECT COUNT(*) FROM role_relationships')
            total_rels = cursor.fetchone()[0] or 0
        except Exception as e:
            current_app.logger.warning(f'Metrics role_relationships query skipped: {e}')
        data['relationships'] = {'total': total_rels, 'by_type': rel_types}

        # === HYPERLINK HISTORY (separate DB) ===
        hv_data = {'total_scans': 0, 'total_links_checked': 0, 'latest_results': None}
        try:
            hv_db_path = Path(__file__).parent / 'data' / 'hyperlink_history.db'
            if hv_db_path.exists():
                with db_connection(str(hv_db_path)) as (hv_conn, hv_c):
                    hv_c.execute('SELECT COUNT(*) FROM scan_history')
                    hv_data['total_scans'] = hv_c.fetchone()[0] or 0
                    hv_c.execute('SELECT total_links, valid_count, broken_count, warning_count, skipped_count FROM scan_history ORDER BY id DESC LIMIT 1')
                    latest = hv_c.fetchone()
                    if latest:
                        hv_data['total_links_checked'] = latest['total_links'] or 0
                        hv_data['latest_results'] = {
                            'valid': latest['valid_count'] or 0, 'broken': latest['broken_count'] or 0,
                            'warning': latest['warning_count'] or 0, 'skipped': latest['skipped_count'] or 0
                        }
        except Exception as e:
            current_app.logger.warning(f'Error loading hyperlink history data: {e}')
        data['hyperlinks'] = hv_data

    return jsonify({'success': True, 'data': data})
@data_bp.route('/api/config/sharing', methods=['GET'])
@handle_api_errors
def get_sharing_config():
    """Get current sharing configuration."""
    config_file = config.base_dir / 'config.json'
    sharing_config = {'shared_dictionary_path': ''}
    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                data = json.load(f)
                sharing = data.get('sharing', {})
                sharing_config['shared_dictionary_path'] = sharing.get('shared_dictionary_path', '')
        except Exception as e:
            logger.warning(f'Could not read config file: {e}')
    return jsonify({'success': True, 'data': sharing_config})
@data_bp.route('/api/config/sharing', methods=['POST'])
@require_csrf
@handle_api_errors
def save_sharing_config():
    """Save sharing configuration (shared dictionary path)."""
    data = request.get_json() or {}
    shared_path = data.get('shared_dictionary_path', '')
    config_file = config.base_dir / 'config.json'
    config_data = {}
    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                config_data = json.load(f)
        except Exception as e:
            current_app.logger.warning(f'Could not parse config.json for sharing settings: {e}')
    if 'sharing' not in config_data:
        config_data['sharing'] = {}
    config_data['sharing']['shared_dictionary_path'] = shared_path
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        return jsonify({'success': True, 'message': 'Sharing configuration saved'})
    except Exception as e:
        logger.error(f'Failed to save config: {e}')
        return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/config/sharing/test', methods=['POST'])
@require_csrf
@handle_api_errors
def test_sharing_path():
    """Test if a shared path is accessible."""
    data = request.get_json() or {}
    test_path = data.get('path', '')
    if not test_path:
        return jsonify({'success': True, 'data': {'accessible': False, 'error': 'No path provided'}})
    else:
        test_path = Path(test_path)
        result = {'accessible': False, 'has_master_file': False, 'error': None}
    try:
        if test_path.exists():
            result['accessible'] = True
            master_file = test_path / 'role_dictionary_master.json'
            if master_file.exists():
                result['has_master_file'] = True
                try:
                    with open(master_file, encoding='utf-8') as f:
                        data = json.load(f)
                        roles = data.get('roles', []) if isinstance(data, dict) else data
                        result['role_count'] = len(roles)
                except Exception as e:
                    current_app.logger.warning(f'Could not read master dictionary file: {e}')
        else:
            result['error'] = 'Path does not exist'
    except PermissionError:
        result['error'] = 'Permission denied'
    except Exception as e:
        result['error'] = str(e)
    return jsonify({'success': True, 'data': result})

@data_bp.route('/api/config/browse-folder', methods=['POST'])
@require_csrf
@handle_api_errors
def browse_folder():
    """Open a native folder picker dialog. Works because Flask runs on localhost."""
    import threading
    result = {'path': None, 'error': None}

    def _pick_folder():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)  # Bring dialog to front
            data = request.get_json() or {}
            initial = data.get('initial_path', '')
            folder = filedialog.askdirectory(
                title='Select Shared Folder',
                initialdir=initial if initial and Path(initial).exists() else None
            )
            root.destroy()
            if folder:
                result['path'] = folder
        except Exception as e:
            result['error'] = str(e)

    # Run in thread to avoid blocking (tkinter needs main thread on some OS,
    # but on Windows it works from any thread)
    import platform
    if platform.system() == 'Windows':
        _pick_folder()
    else:
        # On macOS/Linux, tkinter may need main thread — use thread with timeout
        t = threading.Thread(target=_pick_folder)
        t.start()
        t.join(timeout=60)  # 60 second timeout
        if t.is_alive():
            result['error'] = 'Folder picker timed out'

    if result['error']:
        return jsonify({'success': False, 'error': result['error']})
    if not result['path']:
        return jsonify({'success': True, 'data': {'path': None, 'cancelled': True}})
    return jsonify({'success': True, 'data': {'path': result['path']}})

@data_bp.route('/api/function-categories', methods=['GET'])
@handle_api_errors
def get_function_categories():
    """Get all function categories (hierarchical organizational functions)."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Function categories not available'})
    else:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        SELECT fc.*,\n               (SELECT COUNT(*) FROM role_function_tags rft WHERE rft.function_code = fc.code) as role_count,\n               (SELECT COUNT(*) FROM document_categories dc WHERE dc.function_code = fc.code) as doc_count\n        FROM function_categories fc\n        WHERE fc.is_active = 1\n        ORDER BY fc.sort_order, fc.code\n    ')
            categories = []
            for row in cursor.fetchall():
                cat = dict(row)
                categories.append(cat)
        return jsonify({'success': True, 'data': {'categories': categories, 'total': len(categories)}})
@data_bp.route('/api/function-categories', methods=['POST'])
@require_csrf
@handle_api_errors
def create_function_category():
    """Create a new function category."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Function categories not available'})
    else:
        data = request.get_json() or {}
        code = data.get('code', '').strip().upper()
        name = data.get('name', '').strip()
        if not code or not name:
            return jsonify({'success': False, 'error': 'Code and name are required'})
        else:
            db = get_scan_history_db()
            try:
                with db.connection() as (conn, cursor):
                    cursor.execute('\n            INSERT INTO function_categories (code, name, description, parent_code, sort_order, color)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ', (code, name, data.get('description'), data.get('parent_code'), data.get('sort_order', 99), data.get('color', '#3b82f6')))
                return jsonify({'success': True, 'message': f'Function category \"{name}\" created', 'data': {'code': code}})
            except sqlite3.IntegrityError:
                return jsonify({'success': False, 'error': f'Category code \"{code}\" already exists'})
@data_bp.route('/api/function-categories/<code>', methods=['PUT'])
@require_csrf
@handle_api_errors
def update_function_category(code):
    """Update a function category."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Function categories not available'})
    else:
        data = request.get_json() or {}
        old_code = code.upper()
        new_code = data.get('code', old_code).strip().upper()
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('SELECT id FROM function_categories WHERE code = ?', (old_code,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': f'Category \"{old_code}\" not found'})
            else:
                try:
                    cursor.execute('\n            UPDATE function_categories SET\n                code = ?,\n                name = ?,\n                description = ?,\n                parent_code = ?,\n                sort_order = ?,\n                color = ?,\n                updated_at = CURRENT_TIMESTAMP\n            WHERE code = ?\n        ', (new_code, data.get('name'), data.get('description'), data.get('parent_code'), data.get('sort_order'), data.get('color'), old_code))
                    if new_code!= old_code:
                        cursor.execute('\n                UPDATE role_function_tags SET function_code = ? WHERE function_code = ?\n            ', (new_code, old_code))
                        cursor.execute('\n                UPDATE document_categories SET function_code = ? WHERE function_code = ?\n            ', (new_code, old_code))
                        cursor.execute('\n                UPDATE function_categories SET parent_code = ? WHERE parent_code = ?\n            ', (new_code, old_code))
                    return jsonify({'success': True, 'message': 'Category updated successfully', 'data': {'old_code': old_code, 'new_code': new_code}})
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/function-categories/<code>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_function_category(code):
    """Delete a function category (soft delete - sets inactive)."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Function categories not available'})
    else:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        UPDATE function_categories SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?\n    ', (code.upper(),))
            affected = cursor.rowcount
        if affected:
            return jsonify({'success': True, 'message': f'Category \"{code}\" deactivated'})
        else:
            return jsonify({'success': False, 'error': f'Category \"{code}\" not found'})
@data_bp.route('/api/role-function-tags', methods=['GET'])
@handle_api_errors
def get_role_function_tags():
    """Get all role-to-function assignments."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role function tags not available'})
    else:
        role_name = request.args.get('role_name')
        function_code = request.args.get('function_code')
        db = get_scan_history_db()
        query = '\n        SELECT rft.*, fc.name as function_name, fc.color as function_color\n        FROM role_function_tags rft\n        LEFT JOIN function_categories fc ON rft.function_code = fc.code\n        WHERE 1=1\n    '
        params = []
        if role_name:
            query += ' AND rft.role_name = ?'
            params.append(role_name)
        if function_code:
            query += ' AND rft.function_code = ?'
            params.append(function_code.upper())
        with db.connection() as (conn, cursor):
            cursor.execute(query, params)
            tags = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'data': {'tags': tags, 'total': len(tags)}})
@data_bp.route('/api/role-function-tags', methods=['POST'])
@require_csrf
@handle_api_errors
def assign_role_function_tag():
    """Assign a function tag to a role."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role function tags not available'})
    else:
        data = request.get_json() or {}
        role_name = data.get('role_name', '').strip()
        function_code = data.get('function_code', '').strip().upper()
        if not role_name or not function_code:
            return jsonify({'success': False, 'error': 'role_name and function_code are required'})
        else:
            db = get_scan_history_db()
            try:
                with db.connection() as (conn, cursor):
                    cursor.execute('\n            INSERT INTO role_function_tags (role_name, function_code, assigned_by)\n            VALUES (?, ?, ?)\n        ', (role_name, function_code, data.get('assigned_by', 'user')))
                return jsonify({'success': True, 'message': f'Role \"{role_name}\" assigned to function \"{function_code}\"'})
            except sqlite3.IntegrityError:
                return jsonify({'success': False, 'error': 'Assignment already exists'})
@data_bp.route('/api/role-function-tags/<int:tag_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_role_function_tag(tag_id):
    """Remove a function tag from a role."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role function tags not available'})
    else:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('DELETE FROM role_function_tags WHERE id = ?', (tag_id,))
            affected = cursor.rowcount
        if affected:
            return jsonify({'success': True, 'message': 'Tag removed'})
        else:
            return jsonify({'success': False, 'error': 'Tag not found'})
@data_bp.route('/api/document-category-types', methods=['GET'])
@handle_api_errors
def get_document_category_types():
    """Get all document category types (Procedures, Knowledgebase, etc.)."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        SELECT dct.*,\n               (SELECT COUNT(*) FROM document_categories dc WHERE dc.category_type = dct.name) as doc_count\n        FROM document_category_types dct\n        WHERE dct.is_active = 1\n        ORDER BY dct.name\n    ')
            types = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'data': {'types': types, 'total': len(types)}})
@data_bp.route('/api/document-categories', methods=['GET'])
@handle_api_errors
def get_document_categories():
    """Get document category assignments."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        document_id = request.args.get('document_id', type=int)
        function_code = request.args.get('function_code')
        category_type = request.args.get('category_type')
        db = get_scan_history_db()
        query = '\n        SELECT dc.*, fc.name as function_name, fc.color as function_color\n        FROM document_categories dc\n        LEFT JOIN function_categories fc ON dc.function_code = fc.code\n        WHERE 1=1\n    '
        params = []
        if document_id:
            query += ' AND dc.document_id = ?'
            params.append(document_id)
        if function_code:
            query += ' AND dc.function_code = ?'
            params.append(function_code.upper())
        if category_type:
            query += ' AND dc.category_type = ?'
            params.append(category_type)
        query += ' ORDER BY dc.document_name'
        with db.connection() as (conn, cursor):
            cursor.execute(query, params)
            categories = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'data': {'categories': categories, 'total': len(categories)}})
@data_bp.route('/api/document-categories', methods=['POST'])
@require_csrf
@handle_api_errors
def assign_document_category():
    """Assign category to a document."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        data = request.get_json() or {}
        document_name = data.get('document_name', '').strip()
        category_type = data.get('category_type', '').strip()
        if not document_name or not category_type:
            return jsonify({'success': False, 'error': 'document_name and category_type are required'})
        else:
            db = get_scan_history_db()
            try:
                with db.connection() as (conn, cursor):
                    cursor.execute('\n            INSERT OR REPLACE INTO document_categories\n            (document_id, document_name, category_type, function_code, doc_number, document_owner, auto_detected, assigned_by)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        ', (data.get('document_id'), document_name, category_type, data.get('function_code', '').upper() if data.get('function_code') else None, data.get('doc_number'), data.get('document_owner'), data.get('auto_detected', 0), data.get('assigned_by', 'user')))
                return jsonify({'success': True, 'message': 'Document category assigned'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/document-categories/<int:category_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_document_category(category_id):
    """Remove a document category tag."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        db = get_scan_history_db()
        try:
            with db.connection() as (conn, cursor):
                cursor.execute('SELECT document_name FROM document_categories WHERE id = ?', (category_id,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({'success': False, 'error': 'Category not found'})
                else:
                    document_name = row[0]
                    cursor.execute('DELETE FROM document_categories WHERE id = ?', (category_id,))
            return jsonify({'success': True, 'message': f'Tag removed from {document_name}'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/document-categories/by-document/<document_name>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_document_category_by_name(document_name):
    """Remove all category tags for a specific document."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        from urllib.parse import unquote
        document_name = unquote(document_name)
        db = get_scan_history_db()
        try:
            with db.connection() as (conn, cursor):
                cursor.execute('DELETE FROM document_categories WHERE document_name = ?', (document_name,))
                deleted_count = cursor.rowcount
            return jsonify({'success': True, 'message': f'Removed {deleted_count} tag(s) from {document_name}'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/document-categories/auto-detect', methods=['POST'])
@require_csrf
@handle_api_errors
def auto_detect_document_category():
    """
    Auto-detect document category and function from document number/name.

    Parses document numbers like \"E-1234\" to detect function (E=Engineering)
    and category type patterns.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Document categories not available'})
    else:
        data = request.get_json() or {}
        document_name = data.get('document_name', '').strip()
        document_content = data.get('document_content', '')
        if not document_name:
            return jsonify({'success': False, 'error': 'document_name is required'})
        else:
            import re
            result = {'detected': False, 'function_code': None, 'function_name': None, 'category_type': None, 'doc_number': None, 'document_owner': None, 'match_reason': None}
            db = get_scan_history_db()
            with db.connection() as (conn, cursor):
                cursor.execute('SELECT code, name FROM function_categories WHERE is_active = 1 ORDER BY LENGTH(code) DESC')
                function_codes = {row['code']: row['name'] for row in cursor.fetchall()}
                doc_name_upper = document_name.upper()
                for code in function_codes.keys():
                    pattern1 = f'^{re.escape(code)}[-_]?\\d'
                    pattern2 = f'[-_]{re.escape(code)}[-_]?\\d'
                    pattern3 = f'\\b{re.escape(code)}0\\d'
                    pattern4 = f'{re.escape(code)}[-_]\\d{2,}'
                    for i, pattern in enumerate([pattern1, pattern2, pattern3, pattern4], 1):
                        match = re.search(pattern, doc_name_upper)
                        if match:
                            result['function_code'] = code
                            result['function_name'] = function_codes[code]
                            result['detected'] = True
                            result['match_reason'] = f'Pattern {i}: {pattern}'
                            doc_num_match = re.search(f'{re.escape(code)}[-_]?(\\d+)', doc_name_upper)
                            if doc_num_match:
                                result['doc_number'] = f'{code}-{doc_num_match.group(1)}'
                            break
                    if result['detected']:
                        break
                if not result['category_type']:
                    cursor.execute('SELECT name, doc_number_patterns FROM document_category_types WHERE is_active = 1')
                    for row in cursor.fetchall():
                        patterns = (row['doc_number_patterns'] or '').split(',')
                        for pattern in patterns:
                            pattern = pattern.strip()
                            if pattern and pattern in doc_name_upper:
                                result['category_type'] = row['name']
                                if not result['detected']:
                                    result['detected'] = True
                                break
            if document_content:
                owner_patterns = ['Document Owner[:\\s]+([A-Za-z\\s]+?)(?:\\n|$)', 'Owner[:\\s]+([A-Za-z\\s]+?)(?:\\n|$)', 'Author[:\\s]+([A-Za-z\\s]+?)(?:\\n|$)', 'Prepared [Bb]y[:\\s]+([A-Za-z\\s]+?)(?:\\n|$)']
                for pattern in owner_patterns:
                    match = re.search(pattern, document_content[:5000])
                    if match:
                        result['document_owner'] = match.group(1).strip()
                        break
            return jsonify({'success': True, 'data': result})
@data_bp.route('/api/role-required-actions', methods=['GET'])
@handle_api_errors
def get_role_required_actions():
    """Get required actions/statements for roles."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role required actions not available'})
    else:
        role_name = request.args.get('role_name')
        document_id = request.args.get('document_id', type=int)
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        db = get_scan_history_db()
        query = '\n        SELECT rra.*\n        FROM role_required_actions rra\n        WHERE 1=1\n    '
        params = []
        if role_name:
            query += ' AND rra.role_name = ?'
            params.append(role_name)
        if document_id:
            query += ' AND rra.source_document_id = ?'
            params.append(document_id)
        if verified_only:
            query += ' AND rra.is_verified = 1'
        query += ' ORDER BY rra.role_name, rra.created_at'
        with db.connection() as (conn, cursor):
            cursor.execute(query, params)
            actions = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'data': {'actions': actions, 'total': len(actions)}})
@data_bp.route('/api/role-required-actions', methods=['POST'])
@require_csrf
@handle_api_errors
def add_role_required_action():
    """Add a required action/statement for a role."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role required actions not available'})
    else:
        data = request.get_json() or {}
        role_name = data.get('role_name', '').strip()
        statement_text = data.get('statement_text', '').strip()
        if not role_name or not statement_text:
            return jsonify({'success': False, 'error': 'role_name and statement_text are required'})
        else:
            db = get_scan_history_db()
            try:
                with db.connection() as (conn, cursor):
                    cursor.execute('\n            INSERT INTO role_required_actions\n            (role_name, statement_text, statement_type, source_document_id, source_document_name, source_location, confidence_score)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n        ', (role_name, statement_text, data.get('statement_type', 'requirement'), data.get('source_document_id'), data.get('source_document_name'), data.get('source_location'), data.get('confidence_score', 1.0)))
                    action_id = cursor.lastrowid
                return jsonify({'success': True, 'message': 'Required action added', 'data': {'id': action_id}})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
@data_bp.route('/api/role-required-actions/<int:action_id>/verify', methods=['POST'])
@require_csrf
@handle_api_errors
def verify_role_required_action(action_id):
    """Mark a required action as verified."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role required actions not available'})
    else:
        data = request.get_json() or {}
        verified_by = data.get('verified_by', 'user')
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        UPDATE role_required_actions\n        SET is_verified = 1, verified_by = ?, verified_at = CURRENT_TIMESTAMP\n        WHERE id = ?\n    ', (verified_by, action_id))
            affected = cursor.rowcount
        if affected:
            return jsonify({'success': True, 'message': 'Action verified'})
        else:
            return jsonify({'success': False, 'error': 'Action not found'})
@data_bp.route('/api/role-required-actions/<int:action_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_role_required_action(action_id):
    """Delete a required action."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role required actions not available'})
    else:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('DELETE FROM role_required_actions WHERE id = ?', (action_id,))
            affected = cursor.rowcount
        if affected:
            return jsonify({'success': True, 'message': 'Action deleted'})
        else:
            return jsonify({'success': False, 'error': 'Action not found'})
@data_bp.route('/api/role-required-actions/extract', methods=['POST'])
@require_csrf
@handle_api_errors
def extract_role_required_actions():
    """
    Extract required actions from document text where roles are mentioned.

    Parses sentences that mention a role and extracts the action/requirement
    following the role mention.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role required actions not available'})
    else:
        data = request.get_json() or {}
        document_content = data.get('document_content', '')
        document_name = data.get('document_name', '')
        document_id = data.get('document_id')
        known_roles = data.get('known_roles', [])
        if not document_content:
            return jsonify({'success': False, 'error': 'document_content is required'})
        else:
            import re
            if not known_roles:
                db = get_scan_history_db()
                with db.connection() as (conn, cursor):
                    cursor.execute('SELECT role_name, aliases FROM role_dictionary WHERE is_active = 1')
                    for row in cursor.fetchall():
                        known_roles.append(row['role_name'])
                        aliases = row['aliases']
                        if aliases:
                            try:
                                alias_list = json.loads(aliases) if isinstance(aliases, str) else aliases
                                known_roles.extend(alias_list)
                            except Exception as e:
                                logger.warning(f'Error parsing role aliases: {e}')
            if not known_roles:
                return jsonify({'success': True, 'data': {'extracted': [], 'message': 'No roles in dictionary'}})
            else:
                role_patterns = [re.escape(role) for role in known_roles if role]
                role_regex = re.compile('\\b(' + '|'.join(role_patterns) + ')\\b[^.]*?(shall|must|will|is responsible for|is required to|needs to)[^.]+\\.', re.IGNORECASE)
                extracted = []
                for match in role_regex.finditer(document_content):
                    role_name = match.group(1)
                    full_statement = match.group(0).strip()
                    extracted.append({'role_name': role_name, 'statement_text': full_statement, 'statement_type': 'requirement', 'source_document_name': document_name, 'source_document_id': document_id, 'source_location': f'Position {match.start()}', 'confidence_score': 0.8})
                return jsonify({'success': True, 'data': {'extracted': extracted, 'total': len(extracted)}})
@data_bp.route('/api/roles/reports/by-function', methods=['GET'])
@handle_api_errors
def roles_report_by_function():
    """
    Generate HTML report of roles by function, showing which documents each role appears in.
    Supports check_only=true to just return counts for validation.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role reports not available'})
    else:
        function_code = request.args.get('function_code')
        export_format = request.args.get('format', 'json')
        check_only = request.args.get('check_only', 'false').lower() == 'true'
        db = get_scan_history_db()
        query = '\n        SELECT fc.code, fc.name as function_name, fc.color,\n               rft.role_name\n        FROM function_categories fc\n        LEFT JOIN role_function_tags rft ON fc.code = rft.function_code\n        WHERE fc.is_active = 1\n    '
        params = []
        if function_code:
            query += ' AND fc.code = ?'
            params.append(function_code.upper())
        query += ' ORDER BY fc.sort_order, fc.code, rft.role_name'
        with db.connection() as (conn, cursor):
            cursor.execute(query, params)
            rows = cursor.fetchall()
            functions = {}
            for row in rows:
                code = row['code']
                if code not in functions:
                    functions[code] = {'code': code, 'name': row['function_name'], 'color': row['color'], 'roles': []}
                if row['role_name']:
                    functions[code]['roles'].append(row['role_name'])
            result_functions = []
            for func_data in functions.values():
                func_result = {'code': func_data['code'], 'name': func_data['name'], 'color': func_data['color'], 'roles': []}
                for role_name in func_data['roles']:
                    cursor.execute('\n                SELECT DISTINCT d.filename, d.id\n                FROM roles r\n                JOIN document_roles dr ON r.id = dr.role_id\n                JOIN documents d ON dr.document_id = d.id\n                WHERE r.role_name = ? OR r.normalized_name = ?\n            ', (role_name, role_name))
                    docs = [{'id': row['id'], 'filename': row['filename']} for row in cursor.fetchall()]
                    cursor.execute('\n                SELECT statement_text, source_document_name\n                FROM role_required_actions\n                WHERE role_name = ?\n            ', (role_name,))
                    actions = [{'statement': row['statement_text'], 'source': row['source_document_name']} for row in cursor.fetchall()]
                    func_result['roles'].append({'name': role_name, 'documents': docs, 'document_count': len(docs), 'required_actions': actions})
                result_functions.append(func_result)
        total_roles = sum((len(f['roles']) for f in result_functions))
        if check_only:
            return jsonify({'success': True, 'data': {'total_functions': len(result_functions), 'total_roles': total_roles, 'functions': [{'code': f['code'], 'name': f['name'], 'role_count': len(f['roles'])} for f in result_functions]}})
        else:
            if export_format == 'html':
                try:
                    from report_html_generator import generate_comprehensive_roles_report, detect_cross_functional_references
                    with db.connection() as (conn2, cursor2):
                        cursor2.execute('\n                SELECT dc.document_name, dc.function_code, fc.name as function_name, fc.color as function_color\n                FROM document_categories dc\n                LEFT JOIN function_categories fc ON dc.function_code = fc.code\n            ')
                        document_categories = [dict(row) for row in cursor2.fetchall()]
                        role_documents = {}
                        for func in result_functions:
                            for role in func.get('roles', []):
                                role_name = role.get('name')
                                if role_name:
                                    role_documents[role_name] = role.get('documents', [])
                        cross_refs = detect_cross_functional_references(result_functions, document_categories, role_documents)
                        cursor2.execute('SELECT COUNT(*) FROM documents')
                        total_docs = cursor2.fetchone()[0]
                    html = generate_comprehensive_roles_report(functions=result_functions, cross_references=cross_refs, role_stats={'total_roles': total_roles}, document_stats={'total_documents': total_docs}, report_title='Roles by Function Report')
                    current_app.logger.info('Using comprehensive roles report generator')
                except Exception as e:
                    current_app.logger.warning(f'Falling back to basic report: {e}')
                    html = _generate_roles_by_function_html(result_functions)
                response = make_response(html)
                response.headers['Content-Type'] = 'text/html'
                response.headers['Content-Disposition'] = 'attachment; filename=roles_by_function_report.html'
                return response
            else:
                return jsonify({'success': True, 'data': {'functions': result_functions, 'total_functions': len(result_functions), 'total_roles': total_roles}})
@data_bp.route('/api/roles/reports/by-document', methods=['GET'])
@handle_api_errors
def roles_report_by_document():
    """
    Generate HTML report of documents by function, showing which roles appear in each.
    Supports check_only=true to just return counts for validation.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role reports not available'})
    else:
        function_code = request.args.get('function_code')
        document_owner = request.args.get('document_owner')
        export_format = request.args.get('format', 'json')
        check_only = request.args.get('check_only', 'false').lower() == 'true'
        db = get_scan_history_db()
        query = '\n        SELECT DISTINCT dc.document_name, dc.document_id, dc.category_type,\n               dc.function_code, dc.doc_number, dc.document_owner,\n               fc.name as function_name, fc.color as function_color\n        FROM document_categories dc\n        LEFT JOIN function_categories fc ON dc.function_code = fc.code\n        WHERE 1=1\n    '
        params = []
        if function_code:
            query += ' AND dc.function_code = ?'
            params.append(function_code.upper())
        if document_owner:
            query += ' AND dc.document_owner LIKE ?'
            params.append(f'%{document_owner}%')
        query += ' ORDER BY dc.function_code, dc.document_name'
        with db.connection() as (conn, cursor):
            cursor.execute(query, params)
            documents = []
            for row in cursor.fetchall():
                doc = dict(row)
                if doc['document_id']:
                    cursor.execute('\n                SELECT r.role_name, dr.mention_count as occurrence_count, dr.responsibilities_json as responsibilities\n                FROM document_roles dr\n                JOIN roles r ON dr.role_id = r.id\n                WHERE dr.document_id = ?\n            ', (doc['document_id'],))
                    roles = []
                    for r in cursor.fetchall():
                        role_data = {'name': r['role_name'], 'count': r['occurrence_count']}
                        if r['responsibilities']:
                            try:
                                role_data['responsibilities'] = json.loads(r['responsibilities'])[:5]
                            except Exception:
                                pass
                        roles.append(role_data)
                    doc['roles'] = roles
                    doc['role_count'] = len(roles)
                else:
                    doc['roles'] = []
                    doc['role_count'] = 0
                documents.append(doc)
        grouped = {}
        for doc in documents:
            fc = doc['function_code'] or 'Unassigned'
            if fc not in grouped:
                grouped[fc] = {'function_code': fc, 'function_name': doc.get('function_name', 'Unassigned'), 'function_color': doc.get('function_color', '#888'), 'documents': []}
            grouped[fc]['documents'].append(doc)
        result_functions = list(grouped.values())
        if check_only:
            return jsonify({'success': True, 'data': {'total_documents': len(documents), 'total_functions': len(result_functions), 'documents': [{'name': d['document_name'], 'function': d.get('function_code')} for d in documents[:10]]}})
        else:
            if export_format == 'html':
                try:
                    from report_html_generator import generate_comprehensive_documents_report, detect_cross_functional_references
                    with db.connection() as (conn2, cursor2):
                        cursor2.execute('\n                SELECT fc.code, fc.name, fc.color, rft.role_name\n                FROM function_categories fc\n                LEFT JOIN role_function_tags rft ON fc.code = rft.function_code\n                WHERE fc.is_active = 1\n            ')
                        func_roles = {}
                        for row in cursor2.fetchall():
                            code = row['code']
                            if code not in func_roles:
                                func_roles[code] = {'code': code, 'name': row['name'], 'color': row['color'], 'roles': []}
                            if row['role_name']:
                                func_roles[code]['roles'].append({'name': row['role_name']})
                        role_documents = {}
                        for doc in documents:
                            for role in doc.get('roles', []):
                                role_name = role.get('name', role) if isinstance(role, dict) else role
                                if role_name not in role_documents:
                                    role_documents[role_name] = []
                                role_documents[role_name].append({'filename': doc.get('document_name', doc.get('name'))})
                        cursor2.execute('\n                SELECT dc.document_name, dc.function_code, fc.name as function_name, fc.color as function_color\n                FROM document_categories dc\n                LEFT JOIN function_categories fc ON dc.function_code = fc.code\n            ')
                        document_categories = [dict(row) for row in cursor2.fetchall()]
                    cross_refs = detect_cross_functional_references(list(func_roles.values()), document_categories, role_documents)
                    html = generate_comprehensive_documents_report(functions=result_functions, cross_references=cross_refs, document_stats={'total_documents': len(documents)}, role_stats={}, report_title='Documents by Function Report')
                except Exception as e:
                    current_app.logger.warning(f'Falling back to basic documents report: {e}')
                    html = _generate_docs_by_function_html(result_functions)
                response = make_response(html)
                response.headers['Content-Type'] = 'text/html'
                response.headers['Content-Disposition'] = 'attachment; filename=documents_by_function_report.html'
                return response
            else:
                return jsonify({'success': True, 'data': {'functions': result_functions, 'total_documents': len(documents)}})
@data_bp.route('/api/roles/reports/by-owner', methods=['GET'])
@handle_api_errors
def roles_report_by_owner():
    """
    Generate report of documents grouped by document owner.
    Supports check_only=true to just return counts for validation.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Role reports not available'})
    else:
        export_format = request.args.get('format', 'json')
        check_only = request.args.get('check_only', 'false').lower() == 'true'
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        SELECT dc.document_owner, dc.document_name, dc.document_id,\n               dc.category_type, dc.function_code,\n               fc.name as function_name\n        FROM document_categories dc\n        LEFT JOIN function_categories fc ON dc.function_code = fc.code\n        WHERE dc.document_owner IS NOT NULL AND dc.document_owner != \'\'\n        ORDER BY dc.document_owner, dc.document_name\n    ')
            owners = {}
            for row in cursor.fetchall():
                owner = row['document_owner']
                if owner not in owners:
                    owners[owner] = {'owner': owner, 'documents': []}
                owners[owner]['documents'].append({'name': row['document_name'], 'id': row['document_id'], 'category_type': row['category_type'], 'function_code': row['function_code'], 'function_name': row['function_name']})
        result_owners = list(owners.values())
        for owner_data in result_owners:
            owner_data['document_count'] = len(owner_data['documents'])
        total_documents = sum((o['document_count'] for o in result_owners))
        if check_only:
            return jsonify({'success': True, 'data': {'total_owners': len(result_owners), 'total_documents': total_documents, 'owners': [{'name': o['owner'], 'doc_count': o['document_count']} for o in result_owners[:10]]}})
        else:
            if export_format == 'html':
                try:
                    from report_html_generator import generate_comprehensive_owners_report
                    html = generate_comprehensive_owners_report(owners=result_owners, document_stats={'total_documents': total_documents}, report_title='Documents by Owner Report')
                except Exception as e:
                    current_app.logger.warning(f'Falling back to basic owners report: {e}')
                    html = _generate_docs_by_owner_html(result_owners)
                response = make_response(html)
                response.headers['Content-Type'] = 'text/html'
                response.headers['Content-Disposition'] = 'attachment; filename=documents_by_owner_report.html'
                return response
            else:
                return jsonify({'success': True, 'data': {'owners': result_owners, 'total_owners': len(result_owners), 'total_documents': total_documents}})
def _generate_roles_by_function_html(functions):
    """Generate HTML report for roles by function."""
    html = '<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>AEGIS - Roles by Function Report</title>\n    <style>\n        * { box-sizing: border-box; margin: 0; padding: 0; }\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; padding: 20px; }\n        .container { max-width: 1200px; margin: 0 auto; }\n        .header { background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }\n        .header h1 { font-size: 28px; margin-bottom: 8px; }\n        .header p { opacity: 0.9; }\n        .function-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }\n        .function-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #e5e7eb; }\n        .function-badge { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; }\n        .function-title { font-size: 18px; font-weight: 600; }\n        .function-count { margin-left: auto; background: #f3f4f6; padding: 4px 12px; border-radius: 20px; font-size: 13px; color: #6b7280; }\n        .role-list { padding: 16px 20px; }\n        .role-item { padding: 12px 16px; background: #f9fafb; border-radius: 8px; margin-bottom: 12px; }\n        .role-name { font-weight: 600; color: #1f2937; margin-bottom: 8px; }\n        .role-docs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }\n        .doc-tag { background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 4px; font-size: 12px; }\n        .role-actions { margin-top: 8px; padding-top: 8px; border-top: 1px dashed #d1d5db; }\n        .action-item { font-size: 13px; color: #4b5563; padding: 4px 0; padding-left: 16px; position: relative; }\n        .action-item::before { content: \'→\'; position: absolute; left: 0; color: #9ca3af; }\n        .no-data { text-align: center; padding: 40px; color: #9ca3af; }\n        .timestamp { text-align: center; margin-top: 30px; font-size: 13px; color: #9ca3af; }\n        @media print { body { background: white; } .function-card { break-inside: avoid; } }\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <div class=\"header\">\n            <h1>📋 Roles by Function Report</h1>\n            <p>Organizational functions with their assigned roles and document appearances</p>\n        </div>\n'
    def _abbrev(code):
        """Abbreviate function code for badge display."""
        if not code or len(code) <= 4:
            return code or '?'
        else:
            if '-' in code:
                parts = code.split('-')
                if len(parts[0]) <= 2:
                    return (parts[0] + ''.join((p[0] for p in parts[1:] if p)))[:4]
                else:
                    return ''.join((p[0] for p in parts if p))[:4]
            else:
                return code[:4]
    if not functions:
        html += '<div class=\"no-data\">No function data available</div>'
    else:
        for func in functions:
            color = func.get('color', '#3b82f6')
            html += f"\n        <div class=\"function-card\">\n            <div class=\"function-header\">\n                <div class=\"function-badge\" style=\"background: {color}\" title=\"{func['code']}\">{_abbrev(func['code'])}</div>\n                <div class=\"function-title\">{func['name']}</div>\n                <div class=\"function-count\">{len(func['roles'])} roles</div>\n            </div>\n            <div class=\"role-list\">\n"
            if func['roles']:
                for role in func['roles']:
                    html += f"\n                <div class=\"role-item\">\n                    <div class=\"role-name\">{role['name']}</div>\n                    <div class=\"role-docs\">\n"
                    for doc in role.get('documents', [])[:10]:
                        html += f"<span class=\"doc-tag\">{doc['filename']}</span>"
                    if len(role.get('documents', [])) > 10:
                        html += f"<span class=\"doc-tag\">+{len(role['documents']) - 10} more</span>"
                    html += '</div>'
                    if role.get('required_actions'):
                        html += '<div class=\"role-actions\">'
                        for action in role['required_actions'][:5]:
                            stmt = action['statement'][:150] + '...' if len(action['statement']) > 150 else action['statement']
                            html += f'<div class=\"action-item\">{stmt}</div>'
                        html += '</div>'
                    html += '</div>'
            else:
                html += '<div class=\"no-data\">No roles assigned to this function</div>'
            html += '\n            </div>\n        </div>\n'
    html += f"\n        <div class=\"timestamp\">Generated by AEGIS on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>\n    </div>\n</body>\n</html>"
    return html
def _generate_docs_by_function_html(functions):
    """Generate HTML report for documents by function."""
    html = '<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>AEGIS - Documents by Function Report</title>\n    <style>\n        * { box-sizing: border-box; margin: 0; padding: 0; }\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; padding: 20px; }\n        .container { max-width: 1200px; margin: 0 auto; }\n        .header { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }\n        .header h1 { font-size: 28px; margin-bottom: 8px; }\n        .header p { opacity: 0.9; }\n        .function-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }\n        .function-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #e5e7eb; }\n        .function-badge { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; }\n        .function-title { font-size: 18px; font-weight: 600; }\n        .function-count { margin-left: auto; background: #f3f4f6; padding: 4px 12px; border-radius: 20px; font-size: 13px; color: #6b7280; }\n        .doc-list { padding: 16px 20px; }\n        .doc-item { padding: 12px 16px; background: #f9fafb; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-start; }\n        .doc-info { flex: 1; }\n        .doc-name { font-weight: 600; color: #1f2937; margin-bottom: 4px; }\n        .doc-meta { font-size: 13px; color: #6b7280; }\n        .doc-roles { display: flex; flex-wrap: wrap; gap: 4px; max-width: 300px; }\n        .role-tag { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 11px; }\n        .no-data { text-align: center; padding: 40px; color: #9ca3af; }\n        .timestamp { text-align: center; margin-top: 30px; font-size: 13px; color: #9ca3af; }\n        @media print { body { background: white; } .function-card { break-inside: avoid; } }\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <div class=\"header\">\n            <h1>📁 Documents by Function Report</h1>\n            <p>Documents organized by function with their assigned roles</p>\n        </div>\n'
    if not functions:
        html += '<div class=\"no-data\">No document data available</div>'
    else:
        for func in functions:
            color = func.get('function_color', '#10b981')
            html += f"\n        <div class=\"function-card\">\n            <div class=\"function-header\">\n                <div class=\"function-badge\" style=\"background: {color}\">{func['function_code']}</div>\n                <div class=\"function-title\">{func['function_name']}</div>\n                <div class=\"function-count\">{len(func['documents'])} documents</div>\n            </div>\n            <div class=\"doc-list\">\n"
            for doc in func['documents']:
                owner_str = f' | Owner: {doc["document_owner"]}' if doc.get('document_owner') else ''
                html += f"\n                <div class=\"doc-item\">\n                    <div class=\"doc-info\">\n                        <div class=\"doc-name\">{doc['document_name']}</div>\n                        <div class=\"doc-meta\">\n                            {doc.get('category_type', 'N/A')} | {doc.get('doc_number', 'No doc #')}\n                            {owner_str}\n                        </div>\n                    </div>\n                    <div class=\"doc-roles\">\n"
                for role in doc.get('roles', [])[:8]:
                    html += f"<span class=\"role-tag\">{role['name']}</span>"
                if len(doc.get('roles', [])) > 8:
                    html += f"<span class=\"role-tag\">+{len(doc['roles']) - 8}</span>"
                html += '\n                    </div>\n                </div>\n'
            html += '\n            </div>\n        </div>\n'
    html += f"\n        <div class=\"timestamp\">Generated by AEGIS on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>\n    </div>\n</body>\n</html>"
    return html
def _generate_docs_by_owner_html(owners):
    """Generate HTML report for documents by owner."""
    html = '<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>AEGIS - Documents by Owner Report</title>\n    <style>\n        * { box-sizing: border-box; margin: 0; padding: 0; }\n        body { font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; padding: 20px; }\n        .container { max-width: 1200px; margin: 0 auto; }\n        .header { background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }\n        .header h1 { font-size: 28px; margin-bottom: 8px; }\n        .header p { opacity: 0.9; }\n        .owner-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }\n        .owner-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(90deg, #f3e8ff 0%, white 100%); }\n        .owner-avatar { width: 40px; height: 40px; border-radius: 50%; background: #8b5cf6; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px; }\n        .owner-name { font-size: 18px; font-weight: 600; }\n        .owner-count { margin-left: auto; background: #ede9fe; padding: 4px 12px; border-radius: 20px; font-size: 13px; color: #6d28d9; }\n        .doc-list { padding: 16px 20px; }\n        .doc-item { padding: 10px 12px; border-left: 3px solid #8b5cf6; background: #faf5ff; margin-bottom: 8px; border-radius: 0 8px 8px 0; }\n        .doc-name { font-weight: 500; color: #1f2937; }\n        .doc-meta { font-size: 12px; color: #6b7280; margin-top: 2px; }\n        .no-data { text-align: center; padding: 40px; color: #9ca3af; }\n        .timestamp { text-align: center; margin-top: 30px; font-size: 13px; color: #9ca3af; }\n        @media print { body { background: white; } .owner-card { break-inside: avoid; } }\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <div class=\"header\">\n            <h1>👤 Documents by Owner Report</h1>\n            <p>Documents grouped by document owner</p>\n        </div>\n'
    if not owners:
        html += '<div class=\"no-data\">No owner data available</div>'
    else:
        for owner_data in owners:
            initials = ''.join([n[0].upper() for n in owner_data['owner'].split()[:2]])
            html += f"\n        <div class=\"owner-card\">\n            <div class=\"owner-header\">\n                <div class=\"owner-avatar\">{initials}</div>\n                <div class=\"owner-name\">{owner_data['owner']}</div>\n                <div class=\"owner-count\">{owner_data['document_count']} documents</div>\n            </div>\n            <div class=\"doc-list\">\n"
            for doc in owner_data['documents']:
                html += f"\n                <div class=\"doc-item\">\n                    <div class=\"doc-name\">{doc['name']}</div>\n                    <div class=\"doc-meta\">{doc.get('category_type', '')} | {doc.get('function_name', 'Unassigned')}</div>\n                </div>\n"
            html += '\n            </div>\n        </div>\n'
    html += f"\n        <div class=\"timestamp\">Generated by AEGIS on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>\n    </div>\n</body>\n</html>"
    return html
def _get_default_user_config() -> Dict:
    """Get default user configuration."""
    return {'reviewer_name': 'TechWriter Review', 'default_checks': {'check_acronyms': True, 'check_passive_voice': True, 'check_weak_language': True, 'check_wordy_phrases': True, 'check_nominalization': True, 'check_jargon': True, 'check_ambiguous_pronouns': True, 'check_requirements_language': True, 'check_gender_language': True, 'check_punctuation': True, 'check_sentence_length': True, 'check_repeated_words': True, 'check_capitalization': True, 'check_contractions': True, 'check_references': True, 'check_document_structure': True, 'check_tables_figures': True, 'check_track_changes': True, 'check_consistency': True, 'check_lists': True}}
def cleanup_temp_files(max_age_hours: int=24):
    """Remove temporary files older than max_age_hours."""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    deleted = 0
    for f in config.temp_dir.iterdir():
        if f.is_file():
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    deleted += 1
            except OSError as e:
                logger.warning(f'Failed to delete temp file: {f}', error=str(e))
    if deleted > 0:
        logger.info(f'Cleaned up {deleted} temporary files')
    sessions_cleaned = SessionManager.cleanup_old(max_age_hours)
    if sessions_cleaned > 0:
        logger.info(f'Cleaned up {sessions_cleaned} old sessions')
@data_bp.route('/api/learner/record', methods=['POST'])
@require_csrf
@handle_api_errors
def learner_record():
    """Record a review decision for pattern learning."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return (jsonify({'success': False, 'error': 'Fix Assistant v2 not available'}), 503)
    else:
        data = request.get_json()
        if not data:
            return (jsonify({'success': False, 'error': 'No data provided'}), 400)
        else:
            fix = data.get('fix', {})
            decision = data.get('decision')
            note = data.get('note', '')
            doc_id = data.get('document_id')
            if not decision:
                return (jsonify({'success': False, 'error': 'Decision required'}), 400)
            else:
                decision_map = {'accept': 'accepted', 'reject': 'rejected'}
                normalized_decision = decision_map.get(decision, decision)
                result = _shared.decision_learner.record_decision(fix=fix, decision=normalized_decision, note=note, document_id=doc_id)
                return jsonify({'success': result})
@data_bp.route('/api/learner/predict', methods=['POST'])
@handle_api_errors
def learner_predict():
    """Get prediction for a fix based on learned patterns."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        data = request.get_json()
        if not data:
            return api_error_response('NO_DATA', 'No data provided', 400)
        else:
            fix = data.get('fix', {})
            prediction = _shared.decision_learner.get_prediction(fix)
            return jsonify(prediction)
@data_bp.route('/api/learner/patterns', methods=['GET'])
@handle_api_errors
def learner_patterns():
    """Get all learned patterns."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        category = request.args.get('category')
        if category:
            patterns = _shared.decision_learner.get_patterns_by_category(category)
        else:
            patterns = _shared.decision_learner.get_all_patterns()
        return jsonify({'patterns': patterns})
@data_bp.route('/api/learner/patterns/clear', methods=['POST'])
@require_csrf
@handle_api_errors
def learner_clear_patterns():
    """Clear all learned patterns."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        _shared.decision_learner.clear_patterns()
        return jsonify({'success': True})
@data_bp.route('/api/learner/dictionary', methods=['GET', 'POST', 'DELETE'])
@handle_api_errors
def learner_dictionary():
    """Manage custom dictionary terms."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        if request.method == 'GET':
            terms = _shared.decision_learner.get_dictionary()
            return jsonify({'dictionary': terms})
        else:
            if request.method == 'POST':
                data = request.get_json()
                term = data.get('term', '').strip() if data else ''
                category = data.get('category', 'custom')
                notes = data.get('notes', '')
                if not term:
                    return api_error_response('VALIDATION_ERROR', 'Term required', 400)
                else:
                    if len(term) > 200:
                        return api_error_response('VALIDATION_ERROR', 'Term too long (max 200 characters)', 400)
                    else:
                        if not re.match('^[\\w\\s\\-\\.\\\'\\(\\)]+$', term, re.UNICODE):
                            return api_error_response('VALIDATION_ERROR', 'Term contains invalid characters. Allowed: letters, numbers, spaces, hyphens, periods, apostrophes, parentheses', 400)
                        else:
                            if category and len(category) > 50:
                                return api_error_response('VALIDATION_ERROR', 'Category too long (max 50 characters)', 400)
                            else:
                                if notes and len(notes) > 500:
                                    return api_error_response('VALIDATION_ERROR', 'Notes too long (max 500 characters)', 400)
                                else:
                                    _shared.decision_learner.add_to_dictionary(term, category, notes)
                                    return jsonify({'success': True})
            else:
                if request.method == 'DELETE':
                    data = request.get_json()
                    term = data.get('term', '').strip() if data else ''
                    if not term:
                        return api_error_response('VALIDATION_ERROR', 'Term required', 400)
                    else:
                        _shared.decision_learner.remove_from_dictionary(term)
                        return jsonify({'success': True})
@data_bp.route('/api/learner/statistics', methods=['GET'])
@handle_api_errors
def learner_statistics():
    """Get learning statistics.
    
    v3.0.105: BUG-002 FIX - Now returns standard {success: true, data: {...}} envelope.
    """
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        stats = _shared.decision_learner.get_statistics()
        return jsonify({'success': True, 'data': stats})
@data_bp.route('/api/learner/export', methods=['GET'])
@require_csrf
@handle_api_errors
def learner_export():
    """Export all learning data."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        data = _shared.decision_learner.export_data()
        return jsonify(data)
@data_bp.route('/api/learner/import', methods=['POST'])
@require_csrf
@handle_api_errors
def learner_import():
    """Import learning data."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.decision_learner:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        data = request.get_json()
        if not data:
            return api_error_response('NO_DATA', 'No data provided', 400)
        else:
            _shared.decision_learner.import_data(data)
            return jsonify({'success': True})
@data_bp.route('/api/data/clear-roles', methods=['POST'])
@require_csrf
@handle_api_errors
def clear_role_dictionary():
    """Clear all roles from the role dictionary database.

    v4.0.0: Added for factory reset functionality.
    """
    try:
        from pathlib import Path
        db_path = Path(__file__).parent / 'data' / 'techwriter.db'
        if db_path.exists():
            with db_connection(str(db_path)) as (conn, cursor):
                cursor.execute('DELETE FROM roles')
                cursor.execute('DELETE FROM role_responsibilities')
                cursor.execute('DELETE FROM role_documents')
                deleted = cursor.rowcount
            return jsonify({'success': True, 'message': 'Cleared role dictionary'})
        else:
            return jsonify({'success': True, 'message': 'No role database found'})
    except Exception as e:
        logger.exception(f'Error clearing role dictionary: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
@data_bp.route('/api/data/clear-statements', methods=['POST'])
@require_csrf
@handle_api_errors
def clear_statement_data():
    """Clear all statement data from scan_statements table.
    v4.6.0: Added for statement data management."""
    try:
        if _shared.SCAN_HISTORY_AVAILABLE:
            db = get_scan_history_db()
            result = db.clear_statement_data()
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': 'Scan history not available'})
    except Exception as e:
        logger.exception(f'Error clearing statement data: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
@data_bp.route('/api/data/clear-learning', methods=['POST'])
@require_csrf
@handle_api_errors
def clear_learning_data():
    """Clear adaptive learning and decision pattern data.
    v4.6.0: Added for data management."""
    try:
        from pathlib import Path
        cleared = []
        AL_TABLES = {'role_patterns', 'user_preferences', 'decisions', 'patterns', 'acronym_patterns', 'context_patterns'}
        DP_TABLES = {'decisions', 'patterns'}
        al_path = Path(__file__).parent / 'data' / 'adaptive_learning.db'
        if al_path.exists():
            with db_connection(str(al_path)) as (conn, cursor):
                for tbl in AL_TABLES:
                    try:
                        cursor.execute(f'DELETE FROM {tbl}')
                    except Exception:
                        pass
            cleared.append('adaptive_learning')
        dp_path = Path(__file__).parent / 'data' / 'decision_patterns.db'
        if dp_path.exists():
            with db_connection(str(dp_path)) as (conn, cursor):
                for tbl in DP_TABLES:
                    try:
                        cursor.execute(f'DELETE FROM {tbl}')
                    except Exception:
                        pass
            cleared.append('decision_patterns')
        return jsonify({'success': True, 'message': f"Cleared: {', '.join(cleared) or 'none'}"})
    except Exception as e:
        logger.exception(f'Error clearing learning data: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
@data_bp.route('/api/data/recalculate-role-counts', methods=['POST'])
@require_csrf
@handle_api_errors
def recalculate_role_counts():
    """v4.6.1: Recalculate role document_count and total_mentions from actual data."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return (jsonify({'success': False, 'error': 'Scan history not available'}), 503)
    else:
        db = get_scan_history_db()
        result = db.recalculate_role_counts()
        return jsonify(result)
@data_bp.route('/api/data/cleanup-false-positives', methods=['POST'])
@require_csrf
@handle_api_errors
def cleanup_false_positives():
    """v4.6.1: Remove false positive roles (sentence fragments, non-role nouns)."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return (jsonify({'success': False, 'error': 'Scan history not available'}), 503)
    else:
        db = get_scan_history_db()
        result = db.cleanup_false_positive_roles()
        return jsonify(result)
@data_bp.route('/api/data/factory-reset', methods=['POST'])
@require_csrf
@handle_api_errors
def factory_reset():
    """Factory reset - clear all user data and restore defaults.

    v4.0.0: Added for complete data reset functionality.

    Clears:
    - Scan history database
    - Role dictionary
    - Adaptive learning data
    - User preferences (localStorage cleared via frontend)
    """
    try:
        from pathlib import Path
        results = {'scan_history': False, 'roles': False, 'learning': False}
        if _shared.SCAN_HISTORY_AVAILABLE:
            try:
                db = get_scan_history_db()
                with db.connection() as (conn, cursor):
                    for table in ['scan_statements', 'issue_changes', 'document_roles', 'document_categories', 'role_required_actions', 'role_function_tags', 'role_relationships', 'role_dictionary', 'function_categories', 'document_category_types', 'roles', 'scans', 'documents', 'scan_profiles']:
                        try:
                            cursor.execute(f'DELETE FROM {table}')
                        except Exception:
                            pass
                results['scan_history'] = True
            except Exception as e:
                logger.warning(f'Could not clear scan history: {e}')
        try:
            db_path = Path(__file__).parent / 'data' / 'techwriter.db'
            if db_path.exists():
                with db_connection(str(db_path)) as (conn, cursor):
                    for table in ['roles', 'role_responsibilities', 'role_documents']:
                        try:
                            cursor.execute(f'DELETE FROM {table}')
                        except Exception:
                            pass
                results['roles'] = True
        except Exception as e:
            logger.warning(f'Could not clear roles: {e}')
        try:
            learning_db = Path(__file__).parent / 'data' / 'adaptive_learning.db'
            if learning_db.exists():
                with db_connection(str(learning_db)) as (conn, cursor):
                    for table in ['decisions', 'patterns', 'dictionary']:
                        try:
                            cursor.execute(f'DELETE FROM {table}')
                        except Exception:
                            pass
                results['learning'] = True
        except Exception as e:
            logger.warning(f'Could not clear learning data: {e}')
        try:
            patterns_db = Path(__file__).parent / 'data' / 'decision_patterns.db'
            if patterns_db.exists():
                with db_connection(str(patterns_db)) as (conn, cursor):
                    for table in ['decisions', 'patterns', 'dictionary', 'correction_patterns']:
                        try:
                            cursor.execute(f'DELETE FROM {table}')
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f'Could not clear decision patterns: {e}')
        return jsonify({'success': True, 'message': 'Factory reset complete', 'results': results})
    except Exception as e:
        logger.exception(f'Factory reset error: {e}')
        return (jsonify({'success': False, 'error': str(e)}), 500)
@data_bp.route('/api/data/stats', methods=['GET'])
@handle_api_errors
def data_stats():
    """Get data statistics for the Data Management settings tab.

    v4.0.0: Added to show data counts before clearing.
    """
    try:
        from pathlib import Path
        stats = {'scan_count': 0, 'role_count': 0, 'learning_count': 0}
        if _shared.SCAN_HISTORY_AVAILABLE:
            try:
                db = get_scan_history_db()
                history = db.get_scan_history(limit=10000)
                stats['scan_count'] = len(history)
            except Exception:
                pass
        try:
            db_path = Path(__file__).parent / 'data' / 'techwriter.db'
            if db_path.exists():
                with db_connection(str(db_path)) as (conn, cursor):
                    cursor.execute('SELECT COUNT(*) FROM roles')
                    stats['role_count'] = cursor.fetchone()[0] or 0
        except Exception:
            pass
        try:
            learning_db = Path(__file__).parent / 'data' / 'adaptive_learning.db'
            if learning_db.exists():
                with db_connection(str(learning_db)) as (conn, cursor):
                    cursor.execute('SELECT COUNT(*) FROM decisions')
                    stats['learning_count'] = cursor.fetchone()[0] or 0
        except Exception:
            pass
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return (jsonify({'success': False, 'error': str(e)}), 500)
@data_bp.route('/api/report/generate', methods=['POST'])
@require_csrf
@handle_api_errors
def generate_report():
    """Generate PDF summary report."""
    if not _shared.FIX_ASSISTANT_V2_AVAILABLE or not _shared.report_generator:
        return api_error_response('SERVICE_UNAVAILABLE', 'Fix Assistant v2 not available', 503)
    else:
        data = request.get_json()
        if not data:
            return api_error_response('NO_DATA', 'No data provided', 400)
        else:
            document_name = data.get('document_name', 'document')
            reviewer_name = data.get('reviewer_name', '')
            review_data = data.get('review_data', {})
            options = data.get('options', {})
            pdf_bytes = _shared.report_generator.generate(document_name=document_name, reviewer_name=reviewer_name, review_data=review_data, **options)
            if not pdf_bytes:
                return api_error_response('GENERATION_FAILED', 'Failed to generate report', 500)
            else:
                return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename=\"TWR_Report_{document_name}.pdf\"'})
