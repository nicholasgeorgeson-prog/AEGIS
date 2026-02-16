from flask import Blueprint, request, jsonify, send_file, g
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import os
import urllib.parse

from routes._shared import (
    require_csrf,
    handle_api_errors,
    config,
    logger,
    SessionManager,
    ValidationError,
    get_engine
)
import routes._shared as _shared


scan_bp = Blueprint('scan', __name__)


def get_scan_history_db():
    """Get scan history database instance."""
    from scan_history import get_scan_history_db as _get_db
    return _get_db()


def get_document_extractor(filepath, analyze_quality=False):
    """Get document extractor for file."""
    from routes._shared import get_document_extractor as _get_extractor
    return _get_extractor(filepath, analyze_quality)


class FileError(Exception):
    """File error exception."""
    pass


class ProcessingError(Exception):
    """Processing error exception."""
    pass


@scan_bp.route('/api/roles/extract', methods=['POST'])
@require_csrf
@handle_api_errors
def extract_roles():
    """
    Extract roles from the current document.

    v3.4.0: Supports extraction mode parameter.

    Request body (optional):
        mode: \"discovery\" (default) or \"strict\"
              - discovery: Pattern-based, may include unverified roles
              - strict: Whitelist-only, 100% accuracy guarantee
    """
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('current_file'):
        raise ValidationError('No document loaded')
    else:
        filepath = Path(session_data['current_file'])
        if not filepath.exists():
            raise FileError('Document file not found')
        else:
            data = request.get_json() or {}
            extraction_mode = data.get('mode', 'discovery').lower()
            if extraction_mode not in ['discovery', 'strict']:
                extraction_mode = 'discovery'
            try:
                from role_integration import RoleIntegration
                integration = RoleIntegration(extraction_mode=extraction_mode)
                if not integration.is_available():
                    raise ProcessingError('Role extraction module not available', stage='role_extraction')
                else:
                    extractor, _, _ = get_document_extractor(filepath)
                    result = integration.extract_roles(str(filepath), extractor.full_text, extractor.paragraphs)
                    result['extraction_mode'] = extraction_mode
                    return jsonify(result)
            except ImportError as e:
                logger.exception(f'Role module import error: {e}')
                raise ProcessingError(f'Role module not installed: {e}', stage='role_extraction')


@scan_bp.route('/api/roles/export', methods=['GET'])
@handle_api_errors
def export_roles():
    """Export extracted roles as JSON."""
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('review_results'):
        raise ValidationError('No review results available')
    else:
        role_data = session_data['review_results'].get('roles')
        if not role_data or not role_data.get('success'):
            raise ValidationError('No role data available. Run review first.')
        else:
            export_data = {'export_date': datetime.now(timezone.utc).isoformat() + 'Z', 'source_document': session_data.get('original_filename'), 'roles': {}}
            for role_name, data in role_data.get('roles', {}).items():
                export_data['roles'][role_name] = {'role_name': role_name, 'role_title': data.get('canonical_name', role_name), 'frequency': data.get('frequency', 0), 'confidence': data.get('confidence', 0), 'responsibilities': [{'text': r, 'type': 'extracted'} for r in data.get('responsibilities', [])], 'action_types': data.get('action_types', {}), 'variants': data.get('variants', [])}
            return jsonify(export_data)


@scan_bp.route('/api/documents', methods=['GET'])
@handle_api_errors
def get_documents_list():
    """Get unique list of analyzed documents (de-duplicated from scan history)."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Documents not available'})
    else:
        limit = request.args.get('limit', 500, type=int)
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        SELECT\n            d.id,\n            d.filename,\n            d.word_count,\n            d.first_scan,\n            d.last_scan,\n            d.scan_count,\n            (SELECT COUNT(DISTINCT dr.role_id) FROM document_roles dr WHERE dr.document_id = d.id) as role_count\n        FROM documents d\n        ORDER BY d.filename\n        LIMIT ?\n    ', (limit,))
            documents = []
            for row in cursor.fetchall():
                documents.append({'id': row['id'], 'filename': row['filename'], 'word_count': row['word_count'], 'first_scan': row['first_scan'], 'last_scan': row['last_scan'], 'scan_count': row['scan_count'] or 1, 'role_count': row['role_count'] or 0})
        return jsonify({'success': True, 'data': {'documents': documents, 'total': len(documents)}})


@scan_bp.route('/api/scan-history', methods=['GET'])
@handle_api_errors
def get_scan_history():
    """Get document scan history."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        filename = request.args.get('filename')
        limit = int(request.args.get('limit', 50))
        db = get_scan_history_db()
        history = db.get_scan_history(filename, limit)
        return jsonify({'success': True, 'data': history})


@scan_bp.route('/api/scan-history/<int:scan_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_scan_history(scan_id):
    """Delete a scan from history."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        db = get_scan_history_db()
        result = db.delete_scan(scan_id)
        return jsonify(result)


@scan_bp.route('/api/scan-history/document/<int:doc_id>/roles', methods=['GET'])
@handle_api_errors
def get_document_roles(doc_id):
    """Get roles for a specific document.
    
    v3.0.80: Added for per-document role export functionality.
    
    Args:
        doc_id: Document ID from scan history
        
    Returns:
        JSON with roles list including name, category, mentions, responsibilities
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        db = get_scan_history_db()
        roles = db.get_document_roles(doc_id)
        return jsonify({'success': True, 'data': roles})


@scan_bp.route('/api/scan-history/stats', methods=['GET'])
@handle_api_errors
def api_scan_history_stats():
    """Get scan history statistics.
    
    v3.0.109: Added for scan history panel functionality.
    
    Returns:
        JSON with total_scans, unique_documents, last_scan timestamp
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        try:
            db = get_scan_history_db()
            history = db.get_scan_history(limit=1000)
            unique_docs = set((h.get('filename', '') for h in history if h.get('filename')))
            last_scan = None
            if history:
                last_scan = history[0].get('timestamp') or history[0].get('scan_time') or history[0].get('created_at')
            return jsonify({'success': True, 'total_scans': len(history), 'unique_documents': len(unique_docs), 'last_scan': last_scan})
        except Exception as e:
            return (jsonify({'success': False, 'error': str(e)}), 500)


@scan_bp.route('/api/scan-history/clear', methods=['POST'])
@require_csrf
@handle_api_errors
def api_scan_history_clear():
    """Clear scan history.

    v3.0.109: Added for scan history management.
    v4.0.0: Added support for clear_all and older_than_days parameters.

    Request Body:
        clear_all: bool - If true, delete all scans
        older_than_days: int - Delete scans older than N days

    Returns:
        JSON with success status, deleted count, and message
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    try:
        from datetime import datetime, timedelta
        data = request.get_json() or {}
        clear_all = data.get('clear_all', False)
        older_than_days = data.get('older_than_days')
        db = get_scan_history_db()
        history = db.get_scan_history(limit=10000)
        deleted_count = 0
        cutoff_date = None
        if older_than_days and (not clear_all):
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        for scan in history:
            scan_id = scan.get('id')
            if not scan_id:
                continue
            if cutoff_date:
                scan_time_str = scan.get('scan_time', '')
                try:
                    scan_time = datetime.fromisoformat(scan_time_str.replace('Z', '+00:00'))
                    if scan_time.replace(tzinfo=None) > cutoff_date:
                        continue
                except (ValueError, AttributeError):
                    continue
            db.delete_scan(scan_id)
            deleted_count += 1
        message = f'Cleared {deleted_count} scans'
        if older_than_days and (not clear_all):
            message += f' older than {older_than_days} days'
        return jsonify({'success': True, 'deleted': deleted_count, 'message': message})
    except Exception as e:
        return (jsonify({'success': False, 'error': str(e)}), 500)


@scan_bp.route('/api/scan-history/document-text', methods=['GET'])
@handle_api_errors
def api_scan_history_document_text():
    """Get document text for a historical scan.

    v3.1.9: Added for Role Source Viewer to display actual document content.

    Retrieves the full_text stored in results_json from the most recent scan
    of the specified document.

    Query params:
        filename: Document filename to get text for
        doc_id: Document ID (alternative to filename)
        scan_id: Specific scan ID (optional, defaults to most recent)

    Returns:
        JSON with document text from stored scan results
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    filename = request.args.get('filename', '').strip()
    doc_id = request.args.get('doc_id', '').strip()
    scan_id = request.args.get('scan_id', '').strip()
    if not filename and (not doc_id) and (not scan_id):
        return (jsonify({'success': False, 'error': 'filename, doc_id, or scan_id required'}), 400)
    try:
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            if scan_id:
                cursor.execute('''
                    SELECT s.results_json, d.filename
                    FROM scans s
                    JOIN documents d ON s.document_id = d.id
                    WHERE s.id = ?
                ''', (int(scan_id),))
            elif doc_id:
                cursor.execute('''
                    SELECT s.results_json, d.filename
                    FROM scans s
                    JOIN documents d ON s.document_id = d.id
                    WHERE d.id = ?
                    ORDER BY s.scan_time DESC LIMIT 1
                ''', (int(doc_id),))
            else:
                cursor.execute('''
                    SELECT s.results_json, d.filename
                    FROM scans s
                    JOIN documents d ON s.document_id = d.id
                    WHERE d.filename = ?
                    ORDER BY s.scan_time DESC LIMIT 1
                ''', (filename,))
            row = cursor.fetchone()
        if not row:
            return (jsonify({'success': False, 'error': 'Document not found'}), 404)
        results_json, doc_filename = row
        try:
            results = json.loads(results_json) if results_json else {}
            full_text = results.get('full_text', '')
            if not full_text:
                return (jsonify({'success': False, 'error': 'Document text not available in scan history', 'filename': doc_filename}), 404)
            html_preview = results.get('html_preview', '')
            return jsonify({'success': True, 'text': full_text, 'html_preview': html_preview, 'format': 'html' if html_preview else 'text', 'filename': doc_filename, 'word_count': len(full_text.split())})
        except json.JSONDecodeError:
            return (jsonify({'success': False, 'error': 'Could not parse scan results'}), 500)
    except Exception as e:
        return (jsonify({'success': False, 'error': str(e)}), 500)


@scan_bp.route('/api/scan-history/statements/search', methods=['GET'])
@handle_api_errors
def api_scan_history_search_statements():
    """Search statements across all scans.

    Query params:
        q: Search text (required, min 2 chars)
        directive: Optional directive filter
        limit: Max results (default 50, max 200)
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return (jsonify({'success': False, 'error': 'Query must be at least 2 characters'}), 400)
        else:
            directive = request.args.get('directive', '').strip() or None
            limit = min(int(request.args.get('limit', 50)), 200)
            db = get_scan_history_db()
            results = db.search_statements(query, directive=directive, limit=limit)
            return jsonify({'success': True, 'data': results, 'count': len(results), 'query': query})


@scan_bp.route('/api/scan-history/statements/batch', methods=['PUT'])
@require_csrf
@handle_api_errors
def api_scan_history_batch_update_statements():
    """Batch update multiple statements.

    Body: { updates: [{id: int, updates: {directive?, role?, level?}}, ...] }
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        data = request.get_json() or {}
        updates = data.get('updates', [])
        if not updates or not isinstance(updates, list):
            return (jsonify({'success': False, 'error': 'updates array required'}), 400)
        else:
            if len(updates) > 500:
                return (jsonify({'success': False, 'error': 'Maximum 500 updates per batch'}), 400)
            else:
                db = get_scan_history_db()
                result = db.batch_update_statements(updates)
                return jsonify(result)


@scan_bp.route('/api/scan-history/statements/<int:stmt_id>/review', methods=['PUT'])
@require_csrf
@handle_api_errors
def api_update_statement_review(stmt_id):
    """Update review status of a single statement.
    v4.6.0: Statement review lifecycle.
    Body: { review_status: \'reviewed\'|\'rejected\'|\'pending\', confirmed: bool, reviewer: str }
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        data = request.get_json() or {}
        review_status = data.get('review_status', 'reviewed')
        confirmed = data.get('confirmed', False)
        reviewer = data.get('reviewer', '')
        db = get_scan_history_db()
        result = db.update_statement_review(stmt_id, review_status, confirmed, reviewer)
        return jsonify(result)


@scan_bp.route('/api/scan-history/statements/batch-review', methods=['PUT'])
@require_csrf
@handle_api_errors
def api_batch_review_statements():
    """Batch update review status for multiple statements.
    v4.6.0: Statement review lifecycle.
    Body: { updates: [{id, review_status, confirmed?, reviewer?}, ...] }
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        data = request.get_json() or {}
        updates = data.get('updates', [])
        if not updates or not isinstance(updates, list):
            return (jsonify({'success': False, 'error': 'updates array required'}), 400)
        else:
            if len(updates) > 500:
                return (jsonify({'success': False, 'error': 'Maximum 500 updates per batch'}), 400)
            else:
                db = get_scan_history_db()
                result = db.batch_update_statement_review(updates)
                return jsonify(result)


@scan_bp.route('/api/scan-history/statements/review-stats', methods=['GET'])
@handle_api_errors
def api_statement_review_stats():
    """Get statement review statistics.
    v4.6.0: Statement review lifecycle.
    Query params: document_id (optional)
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        document_id = request.args.get('document_id', type=int)
        db = get_scan_history_db()
        stats = db.get_statement_review_stats(document_id)
        return jsonify({'success': True, 'data': stats})


@scan_bp.route('/api/scan-history/statements/duplicates', methods=['GET'])
@handle_api_errors
def api_find_duplicate_statements():
    """Find duplicate statements based on fingerprint.
    v4.6.0: Statement deduplication.
    Query params: document_id (optional)
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        document_id = request.args.get('document_id', type=int)
        db = get_scan_history_db()
        result = db.find_duplicate_statements(document_id)
        return jsonify(result)


@scan_bp.route('/api/scan-history/statements/deduplicate', methods=['POST'])
@require_csrf
@handle_api_errors
def api_deduplicate_statements():
    """Execute duplicate statement cleanup.
    v4.6.0: Statement deduplication.
    Body: { document_id: int (optional), keep: \'latest\'|\'earliest\' }
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        data = request.get_json() or {}
        document_id = data.get('document_id')
        keep = data.get('keep', 'latest')
        db = get_scan_history_db()
        result = db.deduplicate_statements(document_id, keep)
        return jsonify(result)


@scan_bp.route('/api/roles/<path:role_name>/statements', methods=['GET'])
@handle_api_errors
def api_get_role_statements(role_name):
    """Get all statements assigned to a specific role.
    v4.6.0: Role-statement responsibility review.
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        role_name = urllib.parse.unquote(role_name)
        db = get_scan_history_db()
        with db.connection() as (conn, cursor):
            cursor.execute('\n        SELECT ss.id, ss.statement_number, ss.title, ss.description, ss.level,\n               ss.role, ss.directive, ss.section, ss.review_status, ss.confirmed,\n               ss.scan_id, ss.document_id, ss.position_index,\n               d.filename as document_name\n        FROM scan_statements ss\n        JOIN documents d ON ss.document_id = d.id\n        WHERE LOWER(ss.role) = LOWER(?)\n        ORDER BY d.filename, ss.position_index\n    ', (role_name,))
            statements = []
            for row in cursor.fetchall():
                statements.append({
                    'id': row['id'],
                    'number': row['statement_number'] or '',
                    'title': row['title'] or '',
                    'description': row['description'] or '',
                    'level': row['level'],
                    'role': row['role'] or '',
                    'directive': row['directive'] or '',
                    'section': row['section'] or '',
                    'review_status': row['review_status'] or 'pending',
                    'confirmed': bool(row['confirmed']),
                    'scan_id': row['scan_id'],
                    'document_id': row['document_id'],
                    'document_name': row['document_name'] or '',
                    'position_index': row['position_index']
                })
        return jsonify({'success': True, 'data': statements, 'total': len(statements)})


@scan_bp.route('/api/roles/<path:role_name>/statements/bulk-reassign', methods=['PUT'])
@require_csrf
@handle_api_errors
def api_bulk_reassign_role_statements(role_name):
    """Reassign multiple statements from one role to another.
    v4.6.0: Role-statement responsibility management.
    Body: { statement_ids: [int, ...], new_role: str }
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    data = request.get_json() or {}
    stmt_ids = data.get('statement_ids', [])
    new_role = data.get('new_role', '')
    if not stmt_ids:
        return (jsonify({'success': False, 'error': 'statement_ids array required'}), 400)
    db = get_scan_history_db()
    try:
        with db.connection() as (conn, cursor):
            updated = 0
            for stmt_id in stmt_ids:
                cursor.execute('UPDATE scan_statements SET role = ? WHERE id = ?', (new_role, stmt_id))
                updated += cursor.rowcount
        return jsonify({'success': True, 'updated': updated})
    except Exception as e:
        return (jsonify({'success': False, 'error': str(e)}), 500)


@scan_bp.route('/api/scan-history/document-file', methods=['GET'])
@handle_api_errors
def api_scan_history_document_file():
    """Serve the original document file for PDF.js rendering.

    Query params:
        scan_id: Specific scan ID (required)
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        scan_id = request.args.get('scan_id', '').strip()
        if not scan_id:
            return (jsonify({'success': False, 'error': 'scan_id required'}), 400)
        else:
            db = get_scan_history_db()
            with db.connection() as (conn, cursor):
                cursor.execute('\n        SELECT d.filepath, d.filename\n        FROM scans s\n        JOIN documents d ON s.document_id = d.id\n        WHERE s.id = ?\n    ', (int(scan_id),))
                row = cursor.fetchone()
            if not row:
                return (jsonify({'success': False, 'error': 'Scan not found'}), 404)
            else:
                filepath, filename = row
                path = Path(filepath)
                if not path.exists():
                    temp_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp'))
                    stem = Path(filename).stem
                    temp_candidates = list(temp_dir.glob(f'*{stem}*'))
                    if temp_candidates:
                        path = temp_candidates[0]
                    else:
                        return (jsonify({'success': False, 'error': 'Original file no longer available'}), 404)
                return send_file(str(path), as_attachment=False)


@scan_bp.route('/api/scan-history/<scan_id>/recall', methods=['POST'])
@require_csrf
@handle_api_errors
def api_scan_history_recall(scan_id):
    """Recall a specific scan from history.

    v3.0.109: Added for restoring previous scan results.
    
    Args:
        scan_id: The scan ID (can be string or int)
        
    Returns:
        JSON with scan data including results, roles, options
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        try:
            db = get_scan_history_db()
            try:
                scan_id_int = int(scan_id)
            except (ValueError, TypeError):
                raise ValidationError(f'Invalid scan ID: {scan_id}')
            history = db.get_scan_history(limit=10000)
            scan = next((h for h in history if h.get('id') == scan_id_int), None)
            if not scan:
                raise ValidationError(f'Scan {scan_id} not found in history')
            else:
                return jsonify({'success': True, 'scan': scan})
        except ValidationError:
            raise
        except Exception as e:
            return (jsonify({'success': False, 'error': str(e)}), 500)


@scan_bp.route('/api/score-trend', methods=['GET'])
@handle_api_errors
def get_score_trend():
    """Get quality score trend for a document.
    
    v3.0.33 Chunk E: Returns score history for sparkline visualization.
    v3.0.35: Added document_id as alternative to filename for reliability.
    
    Query params:
        filename: Document filename (optional if document_id provided)
        document_id: Document ID from scan history (optional if filename provided)
        limit: Max number of historical scores (default: 10)
    
    Returns:
        List of score data points (oldest to newest)
    """
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan history not available'})
    else:
        filename = request.args.get('filename')
        document_id = request.args.get('document_id')
        if not filename and (not document_id):
            raise ValidationError('filename or document_id parameter required')
        else:
            limit = int(request.args.get('limit', 10))
            db = get_scan_history_db()
            if document_id:
                try:
                    document_id = int(document_id)
                    trend = db.get_score_trend_by_id(document_id, limit)
                except (ValueError, TypeError):
                    raise ValidationError('document_id must be an integer')
            else:
                trend = db.get_score_trend(filename, limit)
            return jsonify({'success': True, 'data': {'filename': filename, 'document_id': document_id, 'trend': trend, 'count': len(trend)}})


@scan_bp.route('/api/scan-profiles', methods=['GET'])
@handle_api_errors
def get_scan_profiles():
    """Get saved scan profiles."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan profiles not available'})
    else:
        db = get_scan_history_db()
        profiles = db.get_scan_profiles()
        return jsonify({'success': True, 'data': profiles})


@scan_bp.route('/api/scan-profiles', methods=['POST'])
@require_csrf
@handle_api_errors
def save_scan_profile():
    """Save a scan profile."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan profiles not available'})
    else:
        data = request.get_json() or {}
        name = data.get('name')
        options = data.get('options', {})
        description = data.get('description', '')
        set_default = data.get('set_default', False)
        if not name:
            raise ValidationError('Profile name is required')
        else:
            db = get_scan_history_db()
            profile_id = db.save_scan_profile(name, options, description, set_default)
            return jsonify({'success': True, 'data': {'id': profile_id, 'name': name}})


@scan_bp.route('/api/scan-profiles/<int:profile_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def delete_scan_profile(profile_id):
    """Delete a scan profile."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan profiles not available'})
    else:
        db = get_scan_history_db()
        deleted = db.delete_scan_profile(profile_id)
        return jsonify({'success': deleted, 'data': {'id': profile_id}})


@scan_bp.route('/api/scan-profiles/default', methods=['GET'])
@handle_api_errors
def get_default_profile():
    """Get the default scan profile."""
    if not _shared.SCAN_HISTORY_AVAILABLE:
        return jsonify({'success': False, 'error': 'Scan profiles not available'})
    else:
        db = get_scan_history_db()
        profile = db.get_default_profile()
        return jsonify({'success': True, 'data': profile})
