"""
Document Comparison Flask Routes
================================
API endpoints for document comparison functionality.

v1.0.0: Initial implementation with scan comparison endpoints
"""

import json
import sqlite3
import time
import hmac
from contextlib import contextmanager
from functools import wraps
from flask import Blueprint, request, jsonify, session, g

# Import db_connection context manager
try:
    from scan_history import db_connection
except ImportError:
    @contextmanager
    def db_connection(db_path):
        """Context manager for SQLite operations."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        try:
            yield (conn, cursor)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# Import logging and exceptions
try:
    from config_logging import get_logger, ValidationError, ProcessingError
    logger = get_logger('document_compare')
except ImportError:
    import logging
    logger = logging.getLogger('document_compare')

    class ValidationError(Exception):
        pass

    class ProcessingError(Exception):
        pass

# Import differ
from .differ import DocumentDiffer
from .models import IssueComparison

# Create blueprint
dc_blueprint = Blueprint('document_compare', __name__)


# =============================================================================
# STANDARDIZED ERROR HANDLING DECORATOR
# =============================================================================

def handle_dc_errors(f):
    """
    Decorator for standardized API error handling in Document Compare routes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)

            # Log slow operations
            elapsed = time.time() - start_time
            if elapsed > 5.0:
                logger.warning(f"Slow DC API call: {f.__name__} took {elapsed:.1f}s")

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
# CSRF ENFORCEMENT FOR WRITE OPERATIONS
# =============================================================================

@dc_blueprint.before_request
def enforce_csrf_on_writes():
    """
    Enforce CSRF protection on all non-GET requests.
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
        logger.warning("CSRF validation failed on document_compare",
                       extra={'path': request.path, 'method': request.method})
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'Invalid or missing CSRF token'
            }
        }), 403

    # Compare tokens securely
    try:
        if not hmac.compare_digest(str(token), str(expected)):
            logger.warning("CSRF token mismatch on document_compare")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CSRF_ERROR',
                    'message': 'Invalid CSRF token'
                }
            }), 403
    except Exception:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'CSRF validation failed'
            }
        }), 403

    return None


# =============================================================================
# DATABASE HELPER FUNCTIONS
# =============================================================================

def _get_db_path():
    """Get the scan history database path."""
    import os
    from pathlib import Path

    # Try to use the same path as scan_history.py
    try:
        from scan_history import get_scan_history_db
        db = get_scan_history_db()
        if hasattr(db, 'db_path'):
            logger.debug(f"Using scan_history db_path: {db.db_path}")
            return db.db_path
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not get db_path from scan_history: {e}")

    # Fallback to calculating from file location
    app_dir = Path(__file__).resolve().parent.parent
    db_path = str(app_dir / "scan_history.db")
    logger.debug(f"Using calculated db_path: {db_path}")
    return db_path


def _reconstruct_text_from_paragraphs(results: dict) -> str:
    """
    v4.7.0-fix: Reconstruct full document text from paragraphs data.
    Older scans may not have full_text stored but do have paragraphs
    as a list of [index, text] pairs.
    """
    paragraphs = results.get('paragraphs', [])
    if not paragraphs:
        return ''
    texts = []
    for p in paragraphs:
        if isinstance(p, list) and len(p) >= 2:
            texts.append(str(p[1]))
        elif isinstance(p, dict) and 'text' in p:
            texts.append(str(p['text']))
        elif isinstance(p, str):
            texts.append(p)
    return '\n'.join(texts)


def _get_scan_with_results(scan_id: int) -> dict:
    """
    Fetch scan data including results_json.

    Args:
        scan_id: Scan ID to fetch

    Returns:
        Dict with scan data and parsed results, or None if not found
    """
    db_path = _get_db_path()

    with db_connection(db_path) as (conn, cursor):
        cursor.execute('''
            SELECT s.id, s.document_id, s.scan_time, s.score, s.grade,
                   s.issue_count, s.word_count, s.results_json,
                   d.filename
            FROM scans s
            JOIN documents d ON s.document_id = d.id
            WHERE s.id = ?
        ''', (scan_id,))

        row = cursor.fetchone()

    if not row:
        return None

    # Parse results_json
    results = {}
    if row['results_json']:
        try:
            results = json.loads(row['results_json'])
        except json.JSONDecodeError:
            pass

    return {
        'id': row['id'],
        'document_id': row['document_id'],
        'scan_time': row['scan_time'],
        'score': row['score'] or 0,
        'grade': row['grade'] or 'N/A',
        'issue_count': row['issue_count'] or 0,
        'word_count': row['word_count'] or 0,
        'filename': row['filename'],
        'results': results
    }


def _get_scans_for_document(doc_id: int) -> list:
    """
    Get all scans for a document.

    Args:
        doc_id: Document ID

    Returns:
        List of scan dicts sorted by scan_time descending
    """
    db_path = _get_db_path()

    with db_connection(db_path) as (conn, cursor):
        cursor.execute('''
            SELECT s.id, s.scan_time, s.score, s.grade, s.issue_count, s.word_count
            FROM scans s
            WHERE s.document_id = ?
            ORDER BY s.scan_time DESC
        ''', (doc_id,))

        rows = cursor.fetchall()

    return [{
        'id': row['id'],
        'scan_time': row['scan_time'],
        'score': row['score'] or 0,
        'grade': row['grade'] or 'N/A',
        'issue_count': row['issue_count'] or 0,
        'word_count': row['word_count'] or 0
    } for row in rows]


def _get_document_by_id(doc_id: int) -> dict:
    """Get document info by ID."""
    db_path = _get_db_path()

    with db_connection(db_path) as (conn, cursor):
        cursor.execute('''
            SELECT id, filename, scan_count
            FROM documents
            WHERE id = ?
        ''', (doc_id,))

        row = cursor.fetchone()

    if not row:
        return None

    return {
        'id': row['id'],
        'filename': row['filename'],
        'scan_count': row['scan_count'] or 0
    }


def _get_documents_with_multiple_scans() -> list:
    """Get all documents that have more than one scan."""
    db_path = _get_db_path()

    with db_connection(db_path) as (conn, cursor):
        cursor.execute('''
            SELECT d.id, d.filename, d.scan_count, d.last_scan
            FROM documents d
            WHERE d.scan_count > 1
            ORDER BY d.last_scan DESC
        ''')

        rows = cursor.fetchall()

    return [{
        'id': row['id'],
        'filename': row['filename'],
        'scan_count': row['scan_count'],
        'last_scan': row['last_scan']
    } for row in rows]


# =============================================================================
# API ENDPOINTS
# =============================================================================

@dc_blueprint.route('/documents', methods=['GET'])
@handle_dc_errors
def get_comparable_documents():
    """
    Get all documents that have multiple scans (can be compared).

    Returns:
        {
            success: true,
            documents: [
                { id, filename, scan_count, last_scan }
            ]
        }
    """
    documents = _get_documents_with_multiple_scans()

    # BUG-M14 FIX: Add message when no comparable documents found
    if not documents:
        # Get count of total documents to provide helpful message
        db_path = _get_db_path()
        with db_connection(db_path) as (conn, cursor):
            cursor.execute('SELECT COUNT(*) FROM documents')
            total = cursor.fetchone()[0] or 0

        return jsonify({
            'success': True,
            'documents': [],
            'count': 0,
            'message': f'No documents with multiple scans found. You have {total} document(s) scanned once. Scan a document again to enable comparison.'
        })

    return jsonify({
        'success': True,
        'documents': documents,
        'count': len(documents)
    })


@dc_blueprint.route('/scans/<int:doc_id>', methods=['GET'])
@handle_dc_errors
def get_document_scans(doc_id: int):
    """
    Get all scans for a document for selection dropdown.

    Args:
        doc_id: Document ID

    Returns:
        {
            success: true,
            document: { id, filename, scan_count },
            scans: [
                { id, scan_time, score, grade, issue_count, word_count }
            ]
        }
    """
    logger.info(f"get_document_scans called with doc_id={doc_id}")

    # Get document info
    document = _get_document_by_id(doc_id)
    if not document:
        logger.warning(f"Document {doc_id} not found in database")
        raise ValidationError(f"Document {doc_id} not found")

    logger.info(f"Found document: {document.get('filename')}")

    # Get all scans
    scans = _get_scans_for_document(doc_id)
    logger.info(f"Found {len(scans)} scans for document {doc_id}")

    if len(scans) < 2:
        logger.warning(f"Document {doc_id} only has {len(scans)} scan(s), need at least 2")
        raise ValidationError(
            f"Document needs at least 2 scans for comparison. "
            f"Found: {len(scans)}"
        )

    return jsonify({
        'success': True,
        'document': document,
        'scans': scans
    })


@dc_blueprint.route('/diff', methods=['POST'])
@handle_dc_errors
def compute_diff():
    """
    Compare two scans and return line-level diff with word highlighting.

    Request body:
        { old_scan_id: int, new_scan_id: int }

    Returns:
        {
            success: true,
            diff: {
                old_scan_id, new_scan_id, document_id,
                old_scan_time, new_scan_time, filename,
                rows: [...],
                changes: [...],
                stats: { total_rows, unchanged, added, deleted, modified, total_changes }
            }
        }
    """
    data = request.get_json() or {}
    old_scan_id = data.get('old_scan_id')
    new_scan_id = data.get('new_scan_id')

    if not old_scan_id or not new_scan_id:
        raise ValidationError("Both old_scan_id and new_scan_id are required")

    if old_scan_id == new_scan_id:
        raise ValidationError("Cannot compare a scan with itself")

    # Fetch scan data
    old_scan = _get_scan_with_results(old_scan_id)
    new_scan = _get_scan_with_results(new_scan_id)

    if not old_scan:
        raise ValidationError(f"Old scan {old_scan_id} not found")
    if not new_scan:
        raise ValidationError(f"New scan {new_scan_id} not found")

    # Verify same document
    if old_scan['document_id'] != new_scan['document_id']:
        raise ValidationError(
            "Cannot compare scans from different documents"
        )

    # Extract full_text from results (reconstruct from paragraphs if missing)
    old_text = old_scan['results'].get('full_text', '')
    new_text = new_scan['results'].get('full_text', '')

    # v4.7.0-fix: Reconstruct full_text from paragraphs for older scans
    if not old_text:
        old_text = _reconstruct_text_from_paragraphs(old_scan['results'])
    if not new_text:
        new_text = _reconstruct_text_from_paragraphs(new_scan['results'])

    if not old_text:
        raise ValidationError(
            f"Old scan {old_scan_id} does not contain document text. "
            "Re-scan the document to enable comparison."
        )
    if not new_text:
        raise ValidationError(
            f"New scan {new_scan_id} does not contain document text. "
            "Re-scan the document to enable comparison."
        )

    # Compute diff
    differ = DocumentDiffer()
    diff_result = differ.align_and_diff(
        old_text=old_text,
        new_text=new_text,
        old_scan_id=old_scan_id,
        new_scan_id=new_scan_id,
        document_id=old_scan['document_id'],
        old_scan_time=old_scan['scan_time'],
        new_scan_time=new_scan['scan_time'],
        filename=old_scan['filename']
    )

    logger.info(
        f"Computed diff for document {old_scan['filename']}: "
        f"{diff_result.stats['total_changes']} changes"
    )

    return jsonify({
        'success': True,
        'diff': diff_result.to_dict()
    })


@dc_blueprint.route('/issues/<int:old_scan_id>/<int:new_scan_id>', methods=['GET'])
@handle_dc_errors
def compare_issues(old_scan_id: int, new_scan_id: int):
    """
    Compare issues between two scans.

    Args:
        old_scan_id: ID of older scan
        new_scan_id: ID of newer scan

    Returns:
        {
            success: true,
            comparison: {
                fixed: [...],
                new_issues: [...],
                unchanged: [...],
                old_score, new_score, score_change,
                old_issue_count, new_issue_count,
                fixed_count, new_count
            }
        }
    """
    # Fetch scan data
    old_scan = _get_scan_with_results(old_scan_id)
    new_scan = _get_scan_with_results(new_scan_id)

    if not old_scan:
        raise ValidationError(f"Old scan {old_scan_id} not found")
    if not new_scan:
        raise ValidationError(f"New scan {new_scan_id} not found")

    # Extract issues
    old_issues = old_scan['results'].get('issues', [])
    new_issues = new_scan['results'].get('issues', [])

    # Create fingerprints for matching
    def fingerprint(issue):
        """Create a fingerprint for issue matching."""
        return (
            issue.get('category', ''),
            issue.get('message', '')[:50],
            issue.get('paragraph_index', 0)
        )

    old_fps = {fingerprint(i): i for i in old_issues}
    new_fps = {fingerprint(i): i for i in new_issues}

    old_keys = set(old_fps.keys())
    new_keys = set(new_fps.keys())

    # Categorize issues
    fixed = [old_fps[k] for k in (old_keys - new_keys)]
    new_only = [new_fps[k] for k in (new_keys - old_keys)]
    unchanged = [old_fps[k] for k in (old_keys & new_keys)]

    comparison = IssueComparison(
        fixed=fixed,
        new_issues=new_only,
        unchanged=unchanged,
        old_score=old_scan['score'],
        new_score=new_scan['score'],
        old_issue_count=len(old_issues),
        new_issue_count=len(new_issues)
    )

    logger.info(
        f"Issue comparison: {len(fixed)} fixed, {len(new_only)} new, "
        f"score {old_scan['score']} -> {new_scan['score']}"
    )

    return jsonify({
        'success': True,
        'comparison': comparison.to_dict()
    })


@dc_blueprint.route('/status', methods=['GET'])
def status_check():
    """Lightweight status endpoint for CSRF token refresh.
    v4.6.0: Added to fix intermittent 403 errors in document comparison.
    The frontend fetches this on CSRF failure to get a fresh token."""
    return jsonify({'success': True, 'status': 'ok'})


@dc_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with database diagnostics."""
    import os

    db_path = _get_db_path()
    db_exists = os.path.exists(db_path)
    doc_count = 0
    scan_count = 0
    comparable_count = 0

    if db_exists:
        try:
            with db_connection(db_path) as (conn, cursor):
                # Count documents
                cursor.execute('SELECT COUNT(*) FROM documents')
                doc_count = cursor.fetchone()[0]

                # Count scans
                cursor.execute('SELECT COUNT(*) FROM scans')
                scan_count = cursor.fetchone()[0]

                # Count documents with 2+ scans
                cursor.execute('SELECT COUNT(*) FROM documents WHERE scan_count >= 2')
                comparable_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Health check database error: {e}")

    return jsonify({
        'success': True,
        'module': 'document_compare',
        'version': '1.0.1',
        'status': 'healthy',
        'database': {
            'path': db_path,
            'exists': db_exists,
            'documents': doc_count,
            'scans': scan_count,
            'comparable_documents': comparable_count
        }
    })
