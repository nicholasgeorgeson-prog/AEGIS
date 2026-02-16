"""
Shared utilities for route blueprints.
======================================
v4.7.0: Extracted from app.py to support blueprint architecture.

All shared decorators, helpers, and state are imported here from the main app
module to provide a single import point for blueprint modules.
"""
import io
import json
import os
import re
import time
import uuid
import traceback
import threading
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, Dict, Any, Callable

from flask import request, jsonify, send_file, session, g, Response, make_response
from werkzeug.utils import secure_filename

from config_logging import (
    get_config, get_logger, get_rate_limiter, VERSION, get_version, APP_NAME,
    TechWriterError, ValidationError, FileError, ProcessingError, RateLimitError,
    sanitize_filename, validate_file_extension, generate_csrf_token, verify_csrf_token,
    StructuredLogger, log_production_error, read_recent_error_logs
)

# These will be set by init_shared() called from app.py
config = get_config()
logger = get_logger('routes')

# Lazy imports for optional modules
_engine_class = None
_module_version = None


def get_engine():
    """Get the AEGISEngine class (lazy import)."""
    global _engine_class, _module_version
    if _engine_class is None:
        from core import AEGISEngine, MODULE_VERSION
        _engine_class = AEGISEngine
        _module_version = MODULE_VERSION
    return _engine_class


def get_module_version():
    """Get core module version."""
    global _module_version
    if _module_version is None:
        from core import MODULE_VERSION
        _module_version = MODULE_VERSION
    return _module_version


# Feature availability flags - set during app initialization
SCAN_HISTORY_AVAILABLE = False
HYPERLINK_HEALTH_AVAILABLE = False
JOB_MANAGER_AVAILABLE = False
STATEMENT_FORGE_AVAILABLE = False
FIX_ASSISTANT_V2_AVAILABLE = False
DIAGNOSTICS_AVAILABLE = False

# Shared instances
decision_learner = None
report_generator = None


def init_shared(app_module):
    """Initialize shared state from the main app module.

    Called once during startup to copy feature flags and shared objects
    from app.py into this module so blueprints can access them.
    """
    global SCAN_HISTORY_AVAILABLE, HYPERLINK_HEALTH_AVAILABLE, JOB_MANAGER_AVAILABLE
    global STATEMENT_FORGE_AVAILABLE, FIX_ASSISTANT_V2_AVAILABLE, DIAGNOSTICS_AVAILABLE
    global decision_learner, report_generator

    SCAN_HISTORY_AVAILABLE = getattr(app_module, 'SCAN_HISTORY_AVAILABLE', False)
    HYPERLINK_HEALTH_AVAILABLE = getattr(app_module, 'HYPERLINK_HEALTH_AVAILABLE', False)
    JOB_MANAGER_AVAILABLE = getattr(app_module, 'JOB_MANAGER_AVAILABLE', False)
    STATEMENT_FORGE_AVAILABLE = getattr(app_module, 'STATEMENT_FORGE_AVAILABLE', False)
    FIX_ASSISTANT_V2_AVAILABLE = getattr(app_module, 'FIX_ASSISTANT_V2_AVAILABLE', False)
    DIAGNOSTICS_AVAILABLE = getattr(app_module, 'DIAGNOSTICS_AVAILABLE', False)
    decision_learner = getattr(app_module, 'decision_learner', None)
    report_generator = getattr(app_module, 'report_generator', None)


# ---------------------------------------------------------------------------
# Decorators (extracted from app.py)
# ---------------------------------------------------------------------------

def require_csrf(f: Callable) -> Callable:
    """Decorator to require CSRF token on state-changing requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not config.csrf_enabled:
            return f(*args, **kwargs)
        else:
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            expected = session.get('csrf_token')
            if not token or not expected or (not verify_csrf_token(token, expected)):
                logger.warning('CSRF validation failed', path=request.path, client_ip=request.remote_addr)
                return (jsonify({'success': False, 'error': {'code': 'CSRF_ERROR', 'message': 'Invalid or missing CSRF token'}}), 403)
            else:
                return f(*args, **kwargs)
    return decorated


def handle_api_errors(f: Callable) -> Callable:
    """Decorator for standardized API error handling."""
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            elapsed = time.time() - start_time
            if elapsed > 5.0:
                logger.warning(f'Slow API call: {f.__name__} took {elapsed:.1f}s')
            return result
        except TechWriterError as e:
            error_id = log_production_error(e, context={'handler': f.__name__, 'error_code': e.code, 'details': e.details, 'elapsed_seconds': round(time.time() - start_time, 3)})
            logger.error(f'API error: {e.message}', code=e.code, status=e.status_code, error_id=error_id)
            resp = e.to_dict()
            resp['error']['error_id'] = error_id
            return (jsonify(resp), e.status_code)
        except FileNotFoundError as e:
            error_id = log_production_error(e, context={'handler': f.__name__, 'elapsed_seconds': round(time.time() - start_time, 3)})
            logger.exception(f'File not found: {e}')
            return (jsonify({'success': False, 'error': {'code': 'FILE_NOT_FOUND', 'message': str(e), 'error_id': error_id}}), 404)
        except PermissionError as e:
            error_id = log_production_error(e, context={'handler': f.__name__, 'elapsed_seconds': round(time.time() - start_time, 3)})
            logger.exception(f'Permission denied: {e}')
            return (jsonify({'success': False, 'error': {'code': 'PERMISSION_DENIED', 'message': str(e), 'error_id': error_id}}), 403)
        except ValueError as e:
            error_id = log_production_error(e, context={'handler': f.__name__, 'elapsed_seconds': round(time.time() - start_time, 3)})
            logger.exception(f'Validation error: {e}')
            return (jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': str(e), 'error_id': error_id}}), 400)
        except Exception as e:
            error_id = log_production_error(e, context={'handler': f.__name__, 'elapsed_seconds': round(time.time() - start_time, 3)})
            logger.exception(f'Unexpected error in {f.__name__}: {e}')
            return (jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred', 'correlation_id': getattr(g, 'correlation_id', 'unknown'), 'error_id': error_id}}), 500)
    return decorated


def require_admin(f: Callable) -> Callable:
    """Decorator to require admin role for sensitive endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not config.auth_enabled:
            return f(*args, **kwargs)
        else:
            groups = getattr(g, 'authenticated_groups', [])
            if 'admin' not in groups and 'administrators' not in groups and (config.auth_provider != 'api_key'):
                logger.warning('Admin access denied', user=getattr(g, 'authenticated_user', 'unknown'), path=request.path)
                return (jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Admin access required for this endpoint.'}}), 403)
            else:
                return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def api_error_response(code: str, message: str, status_code: int = 400, details: Dict = None):
    """Create a standardized API error response."""
    error_data = {'code': code, 'message': message, 'correlation_id': getattr(g, 'correlation_id', 'unknown')}
    if details:
        error_data['details'] = details
    return (jsonify({'success': False, 'error': error_data}), status_code)


def api_success_response(data: Any = None, message: str = None):
    """Create a standardized API success response."""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return jsonify(response)


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------

def get_document_extractor(filepath: Path, analyze_quality: bool = False):
    """Get the appropriate document extractor based on file extension."""
    suffix = filepath.suffix.lower()
    if suffix == '.pdf':
        quality_info = None
        try:
            from pdf_extractor_v2 import PDFExtractorV2
            extractor = PDFExtractorV2(str(filepath), analyze_quality=analyze_quality)
            if analyze_quality:
                quality_info = extractor.get_quality_summary()
        except ImportError:
            from pdf_extractor import PDFExtractor
            extractor = PDFExtractor(str(filepath))
        return (extractor, 'pdf', quality_info)
    else:
        from core import DocumentExtractor
        extractor = DocumentExtractor(str(filepath))
        return (extractor, 'docx', None)


def sanitize_static_path(filename: str, allowed_extensions: set = None) -> str:
    """Sanitize a relative file path while preserving directory structure."""
    if not filename:
        return None
    else:
        normalized = filename.replace('\\', '/')
        if '..' in normalized or normalized.startswith('/'):
            logger.warning('Path traversal attempt blocked', file_name=filename)
            return None
        else:
            parts = normalized.split('/')
            safe_parts = []
            for part in parts:
                if not part:
                    continue
                else:
                    if part.startswith('.') or not all((c.isalnum() or c in '-_.' for c in part)):
                        safe_part = secure_filename(part)
                        if not safe_part:
                            return
                        else:
                            safe_parts.append(safe_part)
                    else:
                        safe_parts.append(part)
            if not safe_parts:
                return None
            else:
                safe_path = '/'.join(safe_parts)
                if allowed_extensions:
                    ext = Path(safe_path).suffix.lower()
                    if ext not in allowed_extensions:
                        return None
                return safe_path


# ---------------------------------------------------------------------------
# SessionManager (moved from app.py)
# ---------------------------------------------------------------------------

class SessionManager:
    """Manages document sessions in a thread-safe manner."""
    _sessions: Dict[str, Dict] = {}
    _lock = threading.Lock()
    _cleanup_thread: Optional[threading.Thread] = None
    _cleanup_running = False
    _cleanup_interval = 3600
    _max_session_age_hours = 24

    @classmethod
    def create(cls, session_id: str = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        with cls._lock:
            cls._sessions[session_id] = {
                'created': datetime.now().isoformat(),
                'current_file': None,
                'original_filename': None,
                'review_results': None,
                'filtered_issues': [],
                'selected_issues': set()
            }
        return session_id

    @classmethod
    def get(cls, session_id: str) -> Optional[Dict]:
        with cls._lock:
            return cls._sessions.get(session_id)

    @classmethod
    def update(cls, session_id: str, **kwargs):
        with cls._lock:
            if session_id in cls._sessions:
                cls._sessions[session_id].update(kwargs)

    @classmethod
    def delete(cls, session_id: str):
        with cls._lock:
            cls._sessions.pop(session_id, None)

    @classmethod
    def cleanup_old(cls, max_age_hours: int = None):
        from datetime import timedelta
        max_age = max_age_hours if max_age_hours is not None else cls._max_session_age_hours
        cutoff = datetime.now() - timedelta(hours=max_age)
        with cls._lock:
            to_delete = []
            for sid, data in cls._sessions.items():
                try:
                    created = datetime.fromisoformat(data['created'])
                    if created < cutoff:
                        to_delete.append(sid)
                except (KeyError, ValueError):
                    to_delete.append(sid)
            for sid in to_delete:
                del cls._sessions[sid]
        return len(to_delete)

    @classmethod
    def get_session_count(cls) -> int:
        with cls._lock:
            return len(cls._sessions)

    @classmethod
    def start_auto_cleanup(cls, interval_seconds: int = 3600, max_age_hours: int = 24):
        if cls._cleanup_running:
            return None
        cls._cleanup_interval = interval_seconds
        cls._max_session_age_hours = max_age_hours
        cls._cleanup_running = True

        def cleanup_loop():
            while cls._cleanup_running:
                time.sleep(cls._cleanup_interval)
                if not cls._cleanup_running:
                    break
                try:
                    count = cls.cleanup_old()
                    if count > 0:
                        logger.info(f'SessionManager auto-cleanup removed {count} expired sessions')
                except Exception as e:
                    logger.warning(f'SessionManager auto-cleanup error: {e}')

        cls._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cls._cleanup_thread.start()
        logger.info(f'SessionManager auto-cleanup started (interval={interval_seconds}s, max_age={max_age_hours}h)')

    @classmethod
    def stop_auto_cleanup(cls):
        cls._cleanup_running = False
        if cls._cleanup_thread:
            cls._cleanup_thread = None
        logger.info('SessionManager auto-cleanup stopped')


# ---------------------------------------------------------------------------
# Timeout utility
# ---------------------------------------------------------------------------

class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


def run_with_timeout(func, timeout_seconds=60, default=None):
    """Run a function with a timeout. Used by the export endpoint."""
    result = [default]
    error = [None]
    completed = [False]

    def target():
        try:
            result[0] = func()
            completed[0] = True
        except Exception as e:
            error[0] = e
            completed[0] = True

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    if not completed[0]:
        logger.warning(f'Operation timed out after {timeout_seconds}s')
        if default is None:
            raise TimeoutError(f'Operation timed out after {timeout_seconds} seconds')
        else:
            return default
    else:
        if error[0]:
            raise error[0]
        else:
            return result[0]


# Batch constants
# v5.5.0: Increased from 10/100MB to support large document repositories
MAX_BATCH_SIZE = 50  # Max files per single HTTP upload batch
MAX_BATCH_TOTAL_SIZE = 524288000  # 500MB per upload batch

# v5.5.0: Folder scan constants
MAX_FOLDER_SCAN_FILES = 500  # Max files per folder scan operation
FOLDER_SCAN_CHUNK_SIZE = 5  # Files per processing chunk
FOLDER_SCAN_MAX_WORKERS = 3  # Concurrent threads per chunk
