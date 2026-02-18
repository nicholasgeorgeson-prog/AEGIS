"""
Statement Forge Flask Routes
============================
API endpoints for Statement Forge functionality.

v2.9.3 F07: Statement Forge Module Integration
v3.0.30: Flat mode imports (no package directory)
v3.0.49: Support both package and flat import layouts
v3.0.103: Added standardized error handling decorator and CSRF enforcement
"""

import os
import json
import tempfile
import time
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, send_file, session, g

# v3.0.103: Import logging and exceptions for standardized error handling
try:
    from config_logging import get_logger, ValidationError, ProcessingError
    logger = get_logger('statement_forge')
except ImportError:
    # Fallback if config_logging not available
    import logging
    logger = logging.getLogger('statement_forge')
    class ValidationError(Exception):
        pass
    class ProcessingError(Exception):
        pass

# v3.0.49: Support both package and flat import layouts
try:
    # Package imports (transport installer layout)
    from statement_forge.extractor import (
        StatementExtractor,
        extract_statements,
        ACTION_VERBS,
        ACTION_VERB_CATEGORIES,
        detect_directive
    )
    from statement_forge.models import Statement, DocumentType, ExtractionResult
    from statement_forge.export import (
        export_to_nimbus_csv,
        export_to_excel,
        export_to_json,
        export_to_word,
        get_export_stats
    )
except ImportError:
    # Flat mode imports (legacy layout: statement_forge__xxx)
    from statement_forge__extractor import (
        StatementExtractor,
        extract_statements,
        ACTION_VERBS,
        ACTION_VERB_CATEGORIES,
        detect_directive
    )
    from statement_forge__models import Statement, DocumentType, ExtractionResult
    from statement_forge__export import (
        export_to_nimbus_csv,
        export_to_excel,
        export_to_json,
        export_to_word,
        get_export_stats
    )


# Create blueprint
sf_blueprint = Blueprint('statement_forge', __name__)


# =============================================================================
# v3.0.103: STANDARDIZED ERROR HANDLING DECORATOR
# =============================================================================

def handle_sf_errors(f):
    """
    Decorator for standardized API error handling in Statement Forge routes.
    
    v3.0.103: Provides consistent error responses matching app.py's format.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            
            # Log slow operations
            elapsed = time.time() - start_time
            if elapsed > 5.0:
                logger.warning(f"Slow SF API call: {f.__name__} took {elapsed:.1f}s")
            
            return result
            
        except ValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 400
        except ProcessingError as e:
            logger.error(f"Processing error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROCESSING_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500
        except FileNotFoundError as e:
            logger.warning(f"File not found in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 404
        except PermissionError as e:
            logger.error(f"Permission denied in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 403
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_JSON',
                    'message': f'Invalid JSON format: {e}',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 400
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500
    return decorated


# =============================================================================
# v3.0.103: CSRF ENFORCEMENT FOR WRITE OPERATIONS
# =============================================================================

@sf_blueprint.before_request
def enforce_csrf_on_writes():
    """
    Enforce CSRF protection on all non-GET requests to Statement Forge.
    
    v3.0.103: Provides consistent CSRF protection across all write endpoints.
    """
    # Skip CSRF check for GET, HEAD, OPTIONS (safe methods)
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return None
    
    # Check if CSRF is enabled via config module
    try:
        from config_logging import get_config
        config = get_config()
        if not config.csrf_enabled:
            return None
    except (ImportError, AttributeError):
        # If config_logging not available, skip CSRF check
        return None
    
    # Get token from header or form
    token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    expected = session.get('csrf_token')
    
    if not token or not expected:
        logger.warning("CSRF validation failed on statement_forge",
                      path=request.path,
                      method=request.method,
                      client_ip=request.remote_addr)
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'Invalid or missing CSRF token'
            }
        }), 403
    
    # Timing-safe comparison
    import hmac
    if not hmac.compare_digest(token, expected):
        logger.warning("CSRF token mismatch on statement_forge",
                      path=request.path,
                      method=request.method)
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'Invalid or missing CSRF token'
            }
        }), 403
    
    return None  # Continue to route handler


# Session storage for statements (in production, use database)
_session_statements = {}


def _get_session_key():
    """Get unique session key for storing statements."""
    if 'sf_session_id' not in session:
        import uuid
        session['sf_session_id'] = str(uuid.uuid4())
    return session['sf_session_id']


def _store_statements(statements):
    """Store statements in session."""
    key = _get_session_key()
    _session_statements[key] = {
        'statements': [s.to_dict() for s in statements],
        'timestamp': datetime.now().isoformat()
    }


def _get_statements():
    """Get statements from session."""
    key = _get_session_key()
    data = _session_statements.get(key, {})
    statements_data = data.get('statements', [])
    return [Statement.from_dict(s) for s in statements_data]


# =============================================================================
# v3.0.35: SESSION-BASED EXTRACTION ENDPOINT
# =============================================================================

@sf_blueprint.route('/extract-from-session', methods=['POST'])
@handle_sf_errors
def extract_from_session():
    """
    Extract statements from the currently uploaded document in session.
    
    v3.0.35: Enables Statement Forge to work immediately after upload,
    without requiring a review to be run first.
    v3.0.103: Added standardized error handling decorator.
    
    Reads the uploaded file from session, extracts text using the same
    pipeline as review, then runs statement extraction.
    
    Returns:
    {
        "success": true,
        "data": {
            "statements": [...],
            "total": N,
            "document_name": "filename"
        }
    }
    """
    from flask import current_app
    from pathlib import Path
    
    # v3.0.36: SessionManager must be in current_app.config (set by app.py)
    # Removed fallback import to eliminate circular import risk
    SessionManager = current_app.config.get('SESSION_MANAGER')
    if not SessionManager:
        raise ProcessingError('SessionManager not configured. This is a server configuration error.')
    
    # Get session ID from Flask g object (set by before_request)
    session_id = getattr(g, 'session_id', None)
    if not session_id:
        raise ValidationError('No active session')
    
    session_data = SessionManager.get(session_id)
    if not session_data:
        raise ValidationError('No active session')
    
    current_file = session_data.get('current_file')
    if not current_file or not Path(current_file).exists():
        raise ValidationError('No document uploaded. Please upload a document first.')
    
    # Determine file type and extract text
    current_file = Path(current_file)
    file_ext = current_file.suffix.lower()
    text = None
    paragraphs = []
    
    # Try Docling first (v3.0.91+) for superior extraction
    if file_ext in ('.pdf', '.docx', '.pptx', '.xlsx', '.html', '.htm'):
        try:
            from docling_extractor import DoclingExtractor
            docling = DoclingExtractor(fallback_to_legacy=False)
            if docling.is_available:
                doc_result = docling.extract(str(current_file))
                text = doc_result.full_text
                paragraphs = [(p.text, p.location) for p in doc_result.paragraphs]
        except Exception:
            pass  # Fall back to legacy
    
    # Legacy extraction fallback
    if text is None:
        if file_ext == '.pdf':
            # Use PDF extractor
            try:
                from pdf_extractor_v2 import PDFExtractorV2
                extractor = PDFExtractorV2(str(current_file))
            except ImportError:
                from pdf_extractor import PDFExtractor
                extractor = PDFExtractor(str(current_file))
            
            text = extractor.full_text
            paragraphs = extractor.paragraphs
        else:
            # Use DOCX extractor
            from core import DocumentExtractor
            extractor = DocumentExtractor(str(current_file))
            text = extractor.full_text
            paragraphs = extractor.paragraphs
    
    if not text or not text.strip():
        raise ValidationError('Document appears empty or unreadable')
    
    # Get document name
    doc_name = session_data.get('original_filename', current_file.name)
    
    # Run statement extraction
    statements = extract_statements(text, doc_name, None)
    
    # Store in both SF session and main session for persistence
    _store_statements(statements)
    
    # Also store in main session for cross-module access
    session_data['sf_statements'] = [s.to_dict() for s in statements]
    SessionManager.update(session_id, sf_statements=session_data['sf_statements'])
    
    # Get stats
    stats = get_export_stats(statements)
    
    return jsonify({
        'success': True,
        'data': {
            'statements': [s.to_dict() for s in statements],
            'total': len(statements),
            'document_name': doc_name,
            'directive_count': stats.get('by_directive', {}),
            'unique_roles': len(stats.get('by_role', {})),
            'action_count': stats.get('total', 0)
        }
    })


# =============================================================================
# EXTRACTION ENDPOINTS
# =============================================================================

@sf_blueprint.route('/extract', methods=['POST'])
@handle_sf_errors
def extract():
    """
    Extract statements from document text.
    
    v3.0.103: Added standardized error handling decorator.
    
    Request body:
    {
        "text": "document text content",
        "title": "document title (optional)",
        "doc_type": "requirements|work_instruction|procedures (optional)"
    }
    
    Returns:
    {
        "success": true,
        "statements": [...],
        "stats": {...}
    }
    """
    data = request.get_json()
    
    if not data:
        raise ValidationError('No data provided')
    
    text = data.get('text', '')
    title = data.get('title', '')
    doc_type_str = data.get('doc_type')
    
    if not text:
        raise ValidationError('No text provided')
    
    # Parse document type
    doc_type = None
    if doc_type_str:
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            pass  # Invalid doc_type, use default
    
    # Extract statements
    statements = extract_statements(text, title, doc_type)
    
    # Store in session
    _store_statements(statements)
    
    # Get stats
    stats = get_export_stats(statements)
    
    return jsonify({
        'success': True,
        'statements': [s.to_dict() for s in statements],
        'stats': stats
    })


@sf_blueprint.route('/statements', methods=['GET'])
@handle_sf_errors
def get_statements():
    """Get current session statements."""
    statements = _get_statements()
    stats = get_export_stats(statements) if statements else {}
    
    return jsonify({
        'success': True,
        'statements': [s.to_dict() for s in statements],
        'stats': stats
    })


@sf_blueprint.route('/statements', methods=['POST'])
def update_statements():
    """
    Update statements (after editing).
    
    Request body:
    {
        "statements": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'statements' not in data:
            return jsonify({'success': False, 'error': 'No statements provided'}), 400
        
        statements = [Statement.from_dict(s) for s in data['statements']]
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'count': len(statements)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# EDITING ENDPOINTS
# =============================================================================

@sf_blueprint.route('/statements/<statement_id>', methods=['PUT'])
def update_statement(statement_id):
    """
    Update a single statement.
    
    Request body:
    {
        "title": "new title (optional)",
        "description": "new description (optional)",
        "level": 2 (optional),
        "directive": "shall" (optional),
        ...
    }
    """
    try:
        data = request.get_json()
        
        statements = _get_statements()
        
        # Find and update statement
        found = False
        for stmt in statements:
            if stmt.id == statement_id:
                if 'title' in data:
                    stmt.title = data['title']
                if 'description' in data:
                    stmt.description = data['description']
                if 'level' in data:
                    stmt.level = data['level']
                if 'directive' in data:
                    stmt.directive = data['directive']
                if 'number' in data:
                    stmt.number = data['number']
                if 'role' in data:
                    stmt.role = data['role']
                if 'notes' in data:
                    stmt.notes = data['notes']
                stmt.modified = True
                found = True
                break
        
        if not found:
            return jsonify({'success': False, 'error': 'Statement not found'}), 404
        
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'statement': stmt.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/statements/<statement_id>', methods=['DELETE'])
def delete_statement(statement_id):
    """Delete a statement."""
    try:
        statements = _get_statements()
        
        original_count = len(statements)
        statements = [s for s in statements if s.id != statement_id]
        
        if len(statements) == original_count:
            return jsonify({'success': False, 'error': 'Statement not found'}), 404
        
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'remaining': len(statements)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/statements/merge', methods=['POST'])
def merge_statements():
    """
    Merge two statements into one.
    
    Request body:
    {
        "statement_ids": ["id1", "id2"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'statement_ids' not in data:
            return jsonify({'success': False, 'error': 'Statement IDs required'}), 400
        
        ids = data['statement_ids']
        if len(ids) < 2:
            return jsonify({'success': False, 'error': 'Need at least 2 statements to merge'}), 400
        
        statements = _get_statements()
        
        # Find statements to merge
        to_merge = [s for s in statements if s.id in ids]
        
        if len(to_merge) < 2:
            return jsonify({'success': False, 'error': 'Statements not found'}), 404
        
        # Merge into first statement
        merged = to_merge[0]
        for stmt in to_merge[1:]:
            merged.description = f"{merged.description} {stmt.description}".strip()
            merged.notes.extend(stmt.notes)
        merged.modified = True
        
        # Remove other statements
        other_ids = ids[1:]
        statements = [s for s in statements if s.id not in other_ids]
        
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'merged': merged.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/statements/split', methods=['POST'])
def split_statement():
    """
    Split a statement on conjunction.
    
    Request body:
    {
        "statement_id": "id",
        "split_point": 50 (character index)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'statement_id' not in data:
            return jsonify({'success': False, 'error': 'Statement ID required'}), 400
        
        statement_id = data['statement_id']
        split_point = data.get('split_point')
        
        statements = _get_statements()
        
        # Find statement
        stmt_index = None
        stmt = None
        for i, s in enumerate(statements):
            if s.id == statement_id:
                stmt_index = i
                stmt = s
                break
        
        if stmt is None:
            return jsonify({'success': False, 'error': 'Statement not found'}), 404
        
        # Split the description
        desc = stmt.description
        
        if split_point is None:
            # Auto-detect split point (look for "and", ";", etc.)
            split_patterns = [' and ', '; ', ', and ']
            for pattern in split_patterns:
                pos = desc.lower().find(pattern)
                if pos > 20:  # Must have some content before split
                    split_point = pos + len(pattern)
                    break
        
        if split_point is None or split_point >= len(desc) - 20:
            return jsonify({'success': False, 'error': 'Could not find suitable split point'}), 400
        
        # Create two statements
        stmt1_desc = desc[:split_point].strip().rstrip(',;')
        stmt2_desc = desc[split_point:].strip().lstrip(',;')
        
        stmt.description = stmt1_desc
        stmt.modified = True
        
        new_stmt = stmt.clone()
        new_stmt.description = stmt2_desc
        new_stmt.number = f"{stmt.number}a" if stmt.number else ""
        
        # Insert new statement after original
        statements.insert(stmt_index + 1, new_stmt)
        
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'original': stmt.to_dict(),
            'new': new_stmt.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/statements/add', methods=['POST'])
def add_statement():
    """
    Add a new statement.
    
    Request body:
    {
        "title": "title",
        "description": "description",
        "level": 2,
        "after_id": "id" (optional - insert after this statement)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        new_stmt = Statement(
            title=data.get('title', 'New Statement'),
            description=data.get('description', ''),
            level=data.get('level', 2),
            directive=data.get('directive', ''),
            role=data.get('role', ''),
            modified=True
        )
        
        statements = _get_statements()
        
        # Insert at position
        after_id = data.get('after_id')
        if after_id:
            for i, s in enumerate(statements):
                if s.id == after_id:
                    statements.insert(i + 1, new_stmt)
                    break
            else:
                statements.append(new_stmt)
        else:
            statements.append(new_stmt)
        
        _store_statements(statements)
        
        return jsonify({
            'success': True,
            'statement': new_stmt.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/statements/reorder', methods=['POST'])
def reorder_statements():
    """
    Reorder statements.
    
    Request body:
    {
        "order": ["id1", "id2", "id3", ...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'order' not in data:
            return jsonify({'success': False, 'error': 'Order required'}), 400
        
        new_order = data['order']
        statements = _get_statements()
        
        # Create ID to statement map
        stmt_map = {s.id: s for s in statements}
        
        # Reorder
        reordered = []
        for stmt_id in new_order:
            if stmt_id in stmt_map:
                reordered.append(stmt_map[stmt_id])
        
        # Add any statements not in the new order at the end
        for stmt in statements:
            if stmt.id not in new_order:
                reordered.append(stmt)
        
        _store_statements(reordered)
        
        return jsonify({
            'success': True,
            'count': len(reordered)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@sf_blueprint.route('/export', methods=['POST'])
def export():
    """
    Export statements to file.
    
    Request body:
    {
        "format": "nimbus_csv|xlsx|json|docx",
        "scope": "all|filtered|selected",
        "statement_ids": [...] (for selected scope),
        "source_document": "filename"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        export_format = data.get('format', 'nimbus_csv')
        scope = data.get('scope', 'all')
        source_doc = data.get('source_document', '')
        
        statements = _get_statements()
        
        if not statements:
            return jsonify({'success': False, 'error': 'No statements to export'}), 400
        
        # Filter by scope
        if scope == 'selected' and 'statement_ids' in data:
            ids = set(data['statement_ids'])
            statements = [s for s in statements if s.id in ids]
        elif scope == 'filtered' and 'filter' in data:
            filter_val = data['filter'].lower()
            statements = [s for s in statements 
                         if filter_val in s.directive.lower() or 
                            filter_val in s.title.lower() or
                            filter_val in s.description.lower()]
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'nimbus_csv':
            filename = f'statements_{timestamp}.csv'
            filepath = os.path.join(temp_dir, filename)
            result = export_to_nimbus_csv(statements, filepath)
        elif export_format == 'xlsx':
            filename = f'statements_{timestamp}.xlsx'
            filepath = os.path.join(temp_dir, filename)
            result = export_to_excel(statements, filepath, source_doc)
        elif export_format == 'json':
            filename = f'statements_{timestamp}.json'
            filepath = os.path.join(temp_dir, filename)
            result = export_to_json(statements, filepath, source_doc)
        elif export_format == 'docx':
            filename = f'statements_{timestamp}.docx'
            filepath = os.path.join(temp_dir, filename)
            result = export_to_word(statements, filepath, source_doc)
        else:
            return jsonify({'success': False, 'error': f'Unknown format: {export_format}'}), 400
        
        if not result.get('success'):
            return jsonify(result), 500
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/export/preview', methods=['POST'])
def export_preview():
    """Get export preview (stats and sample)."""
    try:
        statements = _get_statements()
        
        if not statements:
            return jsonify({'success': False, 'error': 'No statements'}), 400
        
        stats = get_export_stats(statements)
        
        # Sample first 5 statements
        sample = [s.to_dict() for s in statements[:5]]
        
        return jsonify({
            'success': True,
            'stats': stats,
            'sample': sample
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@sf_blueprint.route('/verbs', methods=['GET'])
def get_verbs():
    """Get action verbs and categories."""
    return jsonify({
        'success': True,
        'total_verbs': len(ACTION_VERBS),
        'categories': {k: list(v) for k, v in ACTION_VERB_CATEGORIES.items()}
    })


@sf_blueprint.route('/detect-directive', methods=['POST'])
def detect_directive_endpoint():
    """Detect directive in text."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        directive = detect_directive(text)
        
        return jsonify({
            'success': True,
            'directive': directive
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sf_blueprint.route('/clear', methods=['POST'])
def clear_session():
    """Clear session statements."""
    try:
        key = _get_session_key()
        if key in _session_statements:
            del _session_statements[key]
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# HEALTH ENDPOINT (v3.0.30)
# =============================================================================

@sf_blueprint.route('/health', methods=['GET'])
def health():
    """
    Statement Forge health check endpoint.
    
    Returns:
    {
        "success": true,
        "version": "3.0.33",
        "status": "operational",
        "verb_count": 1000+
    }
    """
    return jsonify({
        'success': True,
        'version': '3.0.33',
        'status': 'operational',
        'verb_count': len(ACTION_VERBS),
        'verb_categories': len(ACTION_VERB_CATEGORIES)
    })


# =============================================================================
# v3.0.33 Chunk C: AUTO-AVAILABILITY ENDPOINT
# =============================================================================

@sf_blueprint.route('/availability', methods=['GET'])
def check_availability():
    """
    Check if statements are already extracted and available.
    
    v3.0.33 Chunk C: This endpoint allows the UI to check if statements
    were auto-extracted during review, avoiding redundant extraction.
    
    Returns:
    {
        "success": true,
        "statements_ready": true/false,
        "statement_count": N,
        "timestamp": "ISO timestamp"
    }
    """
    try:
        key = _get_session_key()
        data = _session_statements.get(key, {})
        
        statements_data = data.get('statements', [])
        timestamp = data.get('timestamp')
        
        return jsonify({
            'success': True,
            'statements_ready': len(statements_data) > 0,
            'statement_count': len(statements_data),
            'timestamp': timestamp
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'statements_ready': False,
            'error': str(e)
        })


# =============================================================================
# v3.0.41: STATEMENT FORGE → ROLE MAPPING
# =============================================================================

@sf_blueprint.route('/map-to-roles', methods=['POST'])
def map_statements_to_roles():
    """
    Map Statement Forge statements to extracted roles.
    
    v3.0.41: Batch H - Creates bidirectional mapping between SF statements
    and roles extracted from the document.
    
    Requires:
    - Statement Forge extraction to have been run (statements in session)
    - Document review to have been run (roles in session)
    
    Returns JSON:
    {
        "success": true,
        "role_to_statements": {
            "Role Name": [{"id": "...", "number": "...", "description": "..."}]
        },
        "statement_to_roles": {"stmt_id": ["Role1", "Role2"]},
        "unmapped_statements": ["stmt_id1", "stmt_id2"],
        "stats": {
            "total_statements": N,
            "mapped_statements": N,
            "coverage_percent": N.N
        }
    }
    """
    from flask import current_app, g
    
    try:
        # Get SessionManager from app config (blueprint pattern)
        SessionManager = current_app.config.get('SESSION_MANAGER')
        if not SessionManager:
            return jsonify({
                'success': False,
                'error': 'Session manager not available'
            }), 500
        
        # Get session data
        session_id = getattr(g, 'session_id', None)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID'
            }), 400
        
        session_data = SessionManager.get(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'No active session. Upload a document first.'
            }), 400
        
        # Get SF statements
        statements = _get_statements()
        if not statements:
            return jsonify({
                'success': False,
                'error': 'No Statement Forge statements available. Run extraction first.'
            }), 400
        
        # Convert Statement objects to dicts
        statements_dicts = [s.to_dict() for s in statements]
        
        # Get extracted roles from review results
        review_results = session_data.get('review_results', {})
        extracted_roles = review_results.get('roles', {})
        
        if not extracted_roles:
            return jsonify({
                'success': False,
                'error': 'No roles extracted. Run document review first.'
            }), 400
        
        # Import and run mapping
        from role_integration import RoleIntegration
        integration = RoleIntegration()
        
        mapping_result = integration.map_statements_to_roles(
            statements_dicts,
            {'roles': extracted_roles.get('roles', {})}
        )
        
        return jsonify({
            'success': True,
            **mapping_result
        })
        
    except ImportError as e:
        return jsonify({
            'success': False,
            'error': f'Role integration module not available: {str(e)}'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Mapping failed: {str(e)}'
        }), 500


@sf_blueprint.route('/role-mapping-status', methods=['GET'])
def role_mapping_status():
    """
    Check if statement-to-role mapping is available.
    
    v3.0.41: Helper endpoint to check prerequisites.
    
    Returns JSON:
    {
        "success": true,
        "statements_available": true/false,
        "roles_available": true/false,
        "can_map": true/false
    }
    """
    from flask import current_app, g
    
    try:
        # Check statements
        statements = _get_statements()
        statements_available = len(statements) > 0
        
        # Check roles
        roles_available = False
        SessionManager = current_app.config.get('SESSION_MANAGER')
        if SessionManager:
            session_id = getattr(g, 'session_id', None)
            if session_id:
                session_data = SessionManager.get(session_id)
                if session_data:
                    review_results = session_data.get('review_results', {})
                    extracted_roles = review_results.get('roles', {})
                    roles_available = bool(extracted_roles.get('roles'))
        
        return jsonify({
            'success': True,
            'statements_available': statements_available,
            'roles_available': roles_available,
            'can_map': statements_available and roles_available
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'statements_available': False,
            'roles_available': False,
            'can_map': False,
            'error': str(e)
        })


# =============================================================================
# v4.2.0: STATEMENT FORGE HISTORY ENDPOINTS
# =============================================================================

def _get_scan_db():
    """Get scan history database instance."""
    try:
        from scan_history import get_scan_history_db
        return get_scan_history_db()
    except ImportError:
        raise ProcessingError('Scan history module not available')


@sf_blueprint.route('/history/<int:document_id>', methods=['GET'])
@handle_sf_errors
def statement_history(document_id):
    """
    Get Statement Forge extraction history for a document.
    Returns summary stats per scan.
    """
    db = _get_scan_db()
    history = db.get_statement_history(document_id)

    return jsonify({
        'success': True,
        'data': history,
        'document_id': document_id,
        'total_scans': len(history)
    })


@sf_blueprint.route('/scan/<int:scan_id>', methods=['GET'])
@handle_sf_errors
def get_scan_statements_endpoint(scan_id):
    """Get all statements from a specific historical scan."""
    db = _get_scan_db()
    statements = db.get_scan_statements(scan_id)

    return jsonify({
        'success': True,
        'data': statements,
        'scan_id': scan_id,
        'total': len(statements)
    })


@sf_blueprint.route('/trends/<int:document_id>', methods=['GET'])
@handle_sf_errors
def statement_trends(document_id):
    """Get trending data for Statement Forge across document scans."""
    db = _get_scan_db()
    limit = request.args.get('limit', 20, type=int)
    trends = db.get_statement_trends(document_id, limit)

    return jsonify({
        'success': True,
        'data': trends,
        'document_id': document_id
    })


@sf_blueprint.route('/compare/<int:scan_id_1>/<int:scan_id_2>', methods=['GET'])
@handle_sf_errors
def compare_statements(scan_id_1, scan_id_2):
    """Diff Statement Forge results between two scans."""
    db = _get_scan_db()
    diff = db.compare_scan_statements(scan_id_1, scan_id_2)

    return jsonify({
        'success': True,
        'data': diff
    })


@sf_blueprint.route('/scan/statements/<int:statement_id>', methods=['PUT'])
@handle_sf_errors
def update_historical_statement(statement_id):
    """Update a historical scan statement in the scan_statements table.

    v4.2.0: Enables inline editing in Statement History Document Viewer.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    db = _get_scan_db()

    updates = {}
    for field in ['title', 'description', 'directive', 'role', 'level',
                  'statement_number', 'section']:
        if field in data:
            updates[field] = data[field]

    success = db.update_scan_statement(statement_id, updates)

    if success:
        return jsonify({'success': True, 'message': 'Statement updated'})
    else:
        return jsonify({'success': False, 'error': 'Statement not found or no changes made'}), 400


# =========================================================================
# v4.4.0: Statement Diff Export (CSV / PDF)
# =========================================================================

@sf_blueprint.route('/compare/<int:scan_id_1>/<int:scan_id_2>/export-csv', methods=['GET'])
@handle_sf_errors
def export_compare_csv(scan_id_1, scan_id_2):
    """Export statement comparison as CSV."""
    import csv as _csv
    import io as _io

    db = _get_scan_db()
    diff = db.compare_scan_statements(scan_id_1, scan_id_2)

    output = _io.StringIO()
    writer = _csv.writer(output)
    writer.writerow(['Number', 'Title', 'Description', 'Directive', 'Role',
                     'Level', 'Diff Status', 'Changed Fields'])

    # Newer scan statements (added, modified, unchanged)
    for stmt in diff['statements_1']:
        ds = stmt.get('_diff_status', 'unknown')
        changed = ''
        if ds in ('modified_new', 'modified'):
            for mod in diff['modified']:
                if mod['new'].get('id') == stmt.get('id'):
                    changes = []
                    for fld in ('directive', 'role', 'level'):
                        if mod['old'].get(fld) != mod['new'].get(fld):
                            changes.append(f"{fld}: {mod['old'].get(fld)} -> {mod['new'].get(fld)}")
                    changed = '; '.join(changes)
                    break
        writer.writerow([
            stmt.get('statement_number', '') or stmt.get('number', ''),
            stmt.get('title', ''),
            (stmt.get('description', '') or '')[:500],
            stmt.get('directive', ''),
            stmt.get('role', ''),
            stmt.get('level', 1),
            ds, changed
        ])

    # Removed statements from older scan
    for stmt in diff['removed']:
        writer.writerow([
            stmt.get('statement_number', '') or stmt.get('number', ''),
            stmt.get('title', ''),
            (stmt.get('description', '') or '')[:500],
            stmt.get('directive', ''),
            stmt.get('role', ''),
            stmt.get('level', 1),
            'removed', ''
        ])

    output.seek(0)
    resp = send_file(
        _io.BytesIO(output.getvalue().encode('utf-8-sig')),
        as_attachment=True,
        download_name=f'aegis_statement_diff_{scan_id_1}_vs_{scan_id_2}.csv',
        mimetype='text/csv'
    )
    return resp


@sf_blueprint.route('/compare/<int:scan_id_1>/<int:scan_id_2>/export-pdf', methods=['GET'])
@handle_sf_errors
def export_compare_pdf(scan_id_1, scan_id_2):
    """Export statement comparison as PDF report."""
    import io as _io

    db = _get_scan_db()
    diff = db.compare_scan_statements(scan_id_1, scan_id_2)

    try:
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
    except ImportError:
        return jsonify({'success': False, 'error': 'reportlab not installed'}), 500

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='DiffTitle', parent=styles['Heading1'],
        fontSize=16, alignment=TA_CENTER, spaceAfter=4,
        textColor=rl_colors.HexColor('#B8743A')
    ))
    styles.add(ParagraphStyle(
        name='DiffSub', parent=styles['Normal'],
        fontSize=9, alignment=TA_CENTER, spaceAfter=14,
        textColor=rl_colors.HexColor('#64748b')
    ))
    styles.add(ParagraphStyle(
        name='CellText', parent=styles['Normal'],
        fontSize=7, leading=9
    ))

    story = []

    # Title
    story.append(Paragraph('AEGIS Statement Comparison Report', styles['DiffTitle']))
    story.append(Paragraph(
        f'Scan {scan_id_1} vs Scan {scan_id_2} &bull; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        styles['DiffSub']
    ))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=rl_colors.HexColor('#D6A84A'), spaceAfter=12))

    # Summary stats
    summary_data = [
        ['Newer Scan', 'Older Scan', 'Added', 'Removed', 'Modified', 'Unchanged'],
        [str(diff['total_scan_1']), str(diff['total_scan_2']),
         str(diff['added_count']), str(diff['removed_count']),
         str(diff['modified_count']), str(diff['unchanged_count'])]
    ]
    summary_table = Table(summary_data, colWidths=[1.1 * inch] * 6)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.HexColor('#334155')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Statement detail table
    DIFF_COLORS = {
        'added': rl_colors.HexColor('#f0fdf4'),
        'removed': rl_colors.HexColor('#fef2f2'),
        'modified_new': rl_colors.HexColor('#fffbeb'),
        'modified': rl_colors.HexColor('#fffbeb'),
        'unchanged': rl_colors.white,
    }
    DIFF_LABELS = {
        'added': 'Added', 'removed': 'Removed',
        'modified_new': 'Modified', 'modified': 'Modified',
        'unchanged': 'Unchanged'
    }

    headers = ['#', 'Description', 'Directive', 'Role', 'Status']
    col_widths = [0.35 * inch, 4.2 * inch, 0.7 * inch, 1.1 * inch, 0.75 * inch]
    table_data = [headers]
    row_colors = []

    # Build rows: newer scan statements then removed
    all_stmts = list(diff['statements_1']) + list(diff['removed'])
    for idx, stmt in enumerate(all_stmts):
        ds = stmt.get('_diff_status', 'unchanged')
        desc_text = (stmt.get('description', '') or '')[:120]
        table_data.append([
            stmt.get('statement_number', '') or stmt.get('number', '') or str(idx + 1),
            Paragraph(desc_text.replace('&', '&amp;').replace('<', '&lt;'), styles['CellText']),
            stmt.get('directive', '') or '-',
            (stmt.get('role', '') or '-')[:25],
            DIFF_LABELS.get(ds, ds)
        ])
        row_colors.append(DIFF_COLORS.get(ds, rl_colors.white))

    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    # Apply row colors
    for i, color in enumerate(row_colors):
        style_cmds.append(('BACKGROUND', (0, i + 1), (-1, i + 1), color))

    detail_table.setStyle(TableStyle(style_cmds))
    story.append(detail_table)

    doc.build(story)
    buf.seek(0)

    return send_file(
        buf, as_attachment=True,
        download_name=f'aegis_statement_diff_{scan_id_1}_vs_{scan_id_2}.pdf',
        mimetype='application/pdf'
    )
