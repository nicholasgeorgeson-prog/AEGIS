"""
SOW (Statement of Work) Generator Routes
==========================================
Provides API endpoints for the SOW Generator module:
- GET /api/sow/data — Fetch documents, statements, roles, function categories
- POST /api/sow/generate — Generate HTML SOW or populate DOCX template

v5.9.26: Initial implementation (endpoints were previously missing)
"""
import io
import os
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file, current_app

from config_logging import get_logger, get_version

logger = get_logger('sow_routes')

sow_bp = Blueprint('sow', __name__)


def _get_db():
    """Get scan history database instance."""
    from scan_history import get_scan_history_db
    return get_scan_history_db()


def _get_db_path():
    """Get path to the scan_history.db file."""
    db = _get_db()
    return db.db_path


# =============================================================================
# GET /api/sow/data — Fetch all data for SOW generation
# =============================================================================

@sow_bp.route('/api/sow/data')
def sow_data():
    """
    Fetch documents, statements, roles, function categories, and relationships
    for the SOW Generator modal.

    Returns:
        {
            success: true,
            data: {
                documents: [...],
                statements: [...],
                roles: [...],
                function_categories: [...],
                relationships: [...],
                counts: { documents, statements, roles, categories }
            }
        }
    """
    try:
        db = _get_db()
        db_path = _get_db_path()

        # 1. Documents — from documents table
        documents = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, filename, filepath, file_hash, first_scan, last_scan,
                       scan_count, word_count, paragraph_count
                FROM documents
                ORDER BY last_scan DESC
            ''')
            for row in cursor.fetchall():
                documents.append(dict(row))

            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching documents: {e}')

        # 2. Statements — from scan_statements table (latest scan per doc)
        statements = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get latest scan ID per document
            cursor.execute('''
                SELECT ss.id, ss.document_id, ss.description, ss.directive,
                       ss.role_name, ss.section, ss.level, ss.confidence,
                       ss.fingerprint
                FROM scan_statements ss
                INNER JOIN (
                    SELECT document_id, MAX(scan_id) as latest_scan_id
                    FROM scan_statements
                    GROUP BY document_id
                ) latest ON ss.document_id = latest.document_id
                           AND ss.scan_id = latest.latest_scan_id
                ORDER BY ss.document_id, ss.id
            ''')
            for row in cursor.fetchall():
                statements.append(dict(row))

            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching statements: {e}')

        # 3. Roles — from role_dictionary (active only)
        roles = []
        try:
            role_list = db.get_role_dictionary(include_inactive=False)
            roles = role_list if isinstance(role_list, list) else []
        except Exception as e:
            logger.warning(f'Error fetching roles: {e}')

        # 4. Function categories
        function_categories = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT code, name, parent_code, color, description
                FROM function_categories
                ORDER BY code
            ''')
            for row in cursor.fetchall():
                function_categories.append(dict(row))

            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching function categories: {e}')

        # 5. Relationships
        relationships = []
        try:
            rels = db.get_role_relationships()
            relationships = rels if isinstance(rels, list) else []
        except Exception as e:
            logger.warning(f'Error fetching relationships: {e}')

        # Build response
        data = {
            'documents': documents,
            'statements': statements,
            'roles': roles,
            'function_categories': function_categories,
            'relationships': relationships,
            'counts': {
                'documents': len(documents),
                'statements': len(statements),
                'roles': len(roles),
                'categories': len(function_categories)
            }
        }

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        logger.exception(f'Error loading SOW data: {e}')
        return jsonify({
            'success': False,
            'error': {'code': 'SOW_DATA_ERROR', 'message': str(e)}
        }), 500


# =============================================================================
# POST /api/sow/generate — Generate SOW (HTML or populated DOCX template)
# =============================================================================

@sow_bp.route('/api/sow/generate', methods=['POST'])
def sow_generate():
    """
    Generate a Statement of Work document.

    Accepts two modes:
    1. JSON body: { config: {...} } — generates standalone HTML
    2. FormData with 'template' file + 'config' JSON — populates DOCX template

    Returns:
        - HTML file (mode 1)
        - DOCX file (mode 2)
    """
    try:
        db = _get_db()
        db_path = _get_db_path()

        # Determine mode: FormData (with template) or JSON
        template_file = None
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Template mode
            config_json = request.form.get('config', '{}')
            config = json.loads(config_json)
            template_file = request.files.get('template')
        else:
            # Standard JSON mode
            data = request.get_json(silent=True) or {}
            config = data.get('config', {})

        if not config:
            return jsonify({
                'success': False,
                'error': {'code': 'INVALID_CONFIG', 'message': 'No configuration provided'}
            }), 400

        # Get document IDs filter
        doc_ids = config.get('document_ids', None)

        # Fetch all required data
        # Documents
        documents = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if doc_ids:
                placeholders = ','.join('?' * len(doc_ids))
                cursor.execute(f'''
                    SELECT id, filename, filepath, first_scan, last_scan,
                           scan_count, word_count, paragraph_count
                    FROM documents
                    WHERE id IN ({placeholders})
                    ORDER BY filename
                ''', doc_ids)
            else:
                cursor.execute('''
                    SELECT id, filename, filepath, first_scan, last_scan,
                           scan_count, word_count, paragraph_count
                    FROM documents
                    ORDER BY filename
                ''')
            documents = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching documents for SOW: {e}')

        # Statements (filtered by document_ids if provided)
        statements = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if doc_ids:
                placeholders = ','.join('?' * len(doc_ids))
                cursor.execute(f'''
                    SELECT ss.id, ss.document_id, ss.description, ss.directive,
                           ss.role_name, ss.section, ss.level, ss.confidence
                    FROM scan_statements ss
                    INNER JOIN (
                        SELECT document_id, MAX(scan_id) as latest_scan_id
                        FROM scan_statements
                        WHERE document_id IN ({placeholders})
                        GROUP BY document_id
                    ) latest ON ss.document_id = latest.document_id
                               AND ss.scan_id = latest.latest_scan_id
                    ORDER BY ss.document_id, ss.id
                ''', doc_ids)
            else:
                cursor.execute('''
                    SELECT ss.id, ss.document_id, ss.description, ss.directive,
                           ss.role_name, ss.section, ss.level, ss.confidence
                    FROM scan_statements ss
                    INNER JOIN (
                        SELECT document_id, MAX(scan_id) as latest_scan_id
                        FROM scan_statements
                        GROUP BY document_id
                    ) latest ON ss.document_id = latest.document_id
                               AND ss.scan_id = latest.latest_scan_id
                    ORDER BY ss.document_id, ss.id
                ''')
            statements = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching statements for SOW: {e}')

        # Roles (active, from dictionary)
        roles = []
        try:
            role_list = db.get_role_dictionary(include_inactive=False)
            roles = role_list if isinstance(role_list, list) else []
        except Exception as e:
            logger.warning(f'Error fetching roles for SOW: {e}')

        # Function categories
        function_categories = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT code, name, parent_code, color, description FROM function_categories ORDER BY code')
            function_categories = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning(f'Error fetching function categories for SOW: {e}')

        # Relationships
        relationships = []
        try:
            rels = db.get_role_relationships()
            relationships = rels if isinstance(rels, list) else []
        except Exception as e:
            logger.warning(f'Error fetching relationships for SOW: {e}')

        # Build metadata
        metadata = {
            'version': get_version(),
            'export_date': datetime.now(timezone.utc).isoformat(),
        }

        # Generate output
        if template_file:
            # DOCX template mode
            from sow_generator import populate_sow_template

            # Save uploaded template to temp file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                template_file.save(tmp)
                tmp_path = tmp.name

            try:
                docx_bytes = populate_sow_template(
                    template_path=tmp_path,
                    config=config,
                    roles=roles,
                    statements=statements,
                    documents=documents,
                    function_categories=function_categories,
                    relationships=relationships,
                    metadata=metadata
                )

                title = config.get('title', 'SOW').replace(' ', '_')
                filename = f'AEGIS_SOW_{title}_{datetime.now().strftime("%Y%m%d")}.docx'

                return send_file(
                    io.BytesIO(docx_bytes),
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    as_attachment=True,
                    download_name=filename
                )
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        else:
            # HTML generation mode
            from sow_generator import generate_sow_html

            html = generate_sow_html(
                config=config,
                roles=roles,
                statements=statements,
                documents=documents,
                function_categories=function_categories,
                relationships=relationships,
                metadata=metadata
            )

            title = config.get('title', 'SOW').replace(' ', '_')
            filename = f'AEGIS_SOW_{title}_{datetime.now().strftime("%Y%m%d")}.html'

            return send_file(
                io.BytesIO(html.encode('utf-8')),
                mimetype='text/html',
                as_attachment=True,
                download_name=filename
            )

    except ImportError as e:
        logger.exception(f'SOW generator module not available: {e}')
        return jsonify({
            'success': False,
            'error': {'code': 'MODULE_ERROR', 'message': f'SOW generator module not available: {e}'}
        }), 500
    except Exception as e:
        logger.exception(f'SOW generation failed: {e}')
        return jsonify({
            'success': False,
            'error': {'code': 'SOW_GENERATE_ERROR', 'message': str(e)}
        }), 500
