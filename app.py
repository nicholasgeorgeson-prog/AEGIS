"""
AEGIS Flask Application v4.7.0
============================================
Enterprise-grade Technical Writing Review Tool

v4.7.0 - Architecture Refactor:
- Route modules split into blueprints (routes/ package)
- Shared utilities extracted to routes/_shared.py
- Decompiler artifacts cleaned
- app.py reduced from 6,165 lines to ~300 lines (initialization only)

Security Features:
- CSRF protection on all state-changing endpoints
- File size limits and type validation
- Rate limiting per IP
- Structured JSON logging
- Secure session handling
- Input sanitization
- Authentication support (trusted-header or API key)
- Content Security Policy headers
- No debug mode by default

Created by Nicholas Georgeson
"""
import os
import sys
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, timezone, timedelta

_APP_START_TIME = time.time()

# ==========================================================================
# v5.0.0: OFFLINE MODE - Block ALL internet callouts before any imports
# Corporate/air-gapped networks block external access. These env vars MUST
# be set before importing any ML/NLP libraries that phone home.
# ==========================================================================
os.environ['HF_HUB_OFFLINE'] = '1'              # huggingface_hub: never download
os.environ['TRANSFORMERS_OFFLINE'] = '1'          # transformers: never download
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'     # disable HF telemetry
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '5'      # fast fail if somehow attempted
os.environ['DO_NOT_TRACK'] = '1'                  # general telemetry opt-out
os.environ['TOKENIZERS_PARALLELISM'] = 'false'    # avoid fork warnings
# NLTK: point to local data directory (set before nltk is imported)
_nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
if os.path.isdir(_nltk_data_dir):
    os.environ['NLTK_DATA'] = _nltk_data_dir
# Sentence-transformers: point to local model cache
_models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'sentence_transformers')
if os.path.isdir(_models_dir):
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = _models_dir

# v5.0.0: Ensure site-packages is on sys.path for embedded Python (Windows)
# Embedded Python uses ._pth files which may exclude site-packages by default
_app_dir = Path(__file__).parent
_possible_site_packages = [
    _app_dir / 'python' / 'Lib' / 'site-packages',
    _app_dir / 'python' / 'lib' / 'site-packages',
]
for _sp in _possible_site_packages:
    if _sp.exists() and str(_sp) not in sys.path:
        sys.path.insert(0, str(_sp))
# Also add DLL directory for compiled extensions (spaCy, numpy, etc.)
if sys.platform == 'win32':
    _python_dir = _app_dir / 'python'
    if _python_dir.exists():
        os.environ.setdefault('PATH', '')
        os.environ['PATH'] = str(_python_dir) + os.pathsep + os.environ['PATH']
        try:
            os.add_dll_directory(str(_python_dir))
        except (AttributeError, OSError):
            pass  # add_dll_directory only available in Python 3.8+ on Windows


def _capture_startup_error(error: Exception, context: str = ''):
    """Write startup errors to file since logging may not be initialized."""
    import traceback as _tb
    try:
        startup_log = Path(__file__).parent / 'startup_error.log'
        with open(startup_log, 'w', encoding='utf-8') as f:
            f.write('======================================================================\n')
            f.write('AEGIS STARTUP ERROR\n')
            f.write('======================================================================\n')
            f.write(f'Timestamp: {datetime.now().isoformat()}\n')
            f.write(f'Context: {context}\n')
            f.write(f'Error Type: {type(error).__name__}\n')
            f.write(f'Error Message: {error}\n')
            f.write('\nFull Traceback:\n')
            f.write(_tb.format_exc())
            f.write('\n======================================================================\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Core imports
# ---------------------------------------------------------------------------
try:
    from flask import Flask, request, jsonify, session, g, Response
except Exception as e:
    _capture_startup_error(e, 'Flask imports - is Flask installed?')
    raise

try:
    from config_logging import (
        get_config, get_logger, get_rate_limiter, VERSION, APP_NAME,
        generate_csrf_token, verify_csrf_token, StructuredLogger,
        log_production_error
    )
except Exception as e:
    _capture_startup_error(e, 'config_logging import failed')
    raise

try:
    from core import AEGISEngine, MODULE_VERSION
except Exception as e:
    _capture_startup_error(e, 'core.py import failed')
    raise

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------
config = get_config()
logger = get_logger('app')

app = Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Fix Waitress Secure cookie stripping
from flask.sessions import SecureCookieSessionInterface as _BaseSessionInterface


class _LocalDevSessionInterface(_BaseSessionInterface):
    def save_session(self, app, session, response):
        super().save_session(app, session, response)
        if not app.config.get('SESSION_COOKIE_SECURE', False):
            cookies = response.headers.getlist('Set-Cookie')
            if cookies:
                response.headers.remove('Set-Cookie')
                for cookie in cookies:
                    response.headers.add('Set-Cookie', cookie.replace('; Secure', ''))


app.session_interface = _LocalDevSessionInterface()

config.temp_dir.mkdir(exist_ok=True)
config.backup_dir.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Optional module loading
# ---------------------------------------------------------------------------
SCAN_HISTORY_AVAILABLE = False
try:
    from scan_history import get_scan_history_db, db_connection
    SCAN_HISTORY_AVAILABLE = True
except ImportError:
    pass

DIAGNOSTICS_AVAILABLE = False
try:
    from diagnostic_export import (
        DiagnosticCollector, setup_flask_error_capture,
        register_diagnostic_routes, capture_errors,
        register_ai_troubleshoot_routes, log_user_action, get_ai_troubleshoot
    )
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    def capture_errors(func):
        return func
    def log_user_action(action, details=None):
        return None
    def get_ai_troubleshoot():
        return None

try:
    from api_extensions import register_api_extensions
    register_api_extensions(app)
    logger.info('API extensions loaded successfully')
except ImportError as e:
    logger.warning(f'API extensions not available: {e}')

try:
    from update_manager import UpdateManager, register_update_routes
    update_manager = UpdateManager(base_dir=config.base_dir, app_dir=config.base_dir)
    register_update_routes(app, update_manager)
    logger.info('Update manager loaded successfully')
except (ImportError, Exception) as e:
    logger.warning(f'Update manager not available: {e}')

if DIAGNOSTICS_AVAILABLE:
    try:
        setup_flask_error_capture(app)
        register_diagnostic_routes(app)
        register_ai_troubleshoot_routes(app)
        logger.info('Diagnostic error capture enabled')
    except Exception as e:
        logger.warning(f'Could not setup diagnostics: {e}')

# Existing blueprints (feature modules)
STATEMENT_FORGE_AVAILABLE = False
try:
    from statement_forge.routes import sf_blueprint
    app.register_blueprint(sf_blueprint, url_prefix='/api/statement-forge')
    STATEMENT_FORGE_AVAILABLE = True
    logger.info('Statement Forge routes loaded (package mode)')
except ImportError:
    try:
        from statement_forge__routes import sf_blueprint
        app.register_blueprint(sf_blueprint, url_prefix='/api/statement-forge')
        STATEMENT_FORGE_AVAILABLE = True
        logger.info('Statement Forge routes loaded (flat mode)')
    except (ImportError, Exception) as e:
        logger.info(f'Statement Forge not available: {e}')

DOCUMENT_COMPARE_AVAILABLE = False
try:
    from document_compare import dc_blueprint
    app.register_blueprint(dc_blueprint, url_prefix='/api/compare')
    DOCUMENT_COMPARE_AVAILABLE = True
    logger.info('Document Comparison routes loaded')
except (ImportError, Exception) as e:
    logger.info(f'Document Comparison not available: {e}')

PORTFOLIO_AVAILABLE = False
try:
    from portfolio import portfolio_blueprint
    app.register_blueprint(portfolio_blueprint, url_prefix='/api/portfolio')
    PORTFOLIO_AVAILABLE = True
    logger.info('Portfolio routes loaded')
except (ImportError, Exception) as e:
    logger.info(f'Portfolio not available: {e}')

HYPERLINK_VALIDATOR_AVAILABLE = False
try:
    from hyperlink_validator.routes import hv_blueprint
    app.register_blueprint(hv_blueprint, url_prefix='/api/hyperlink-validator')
    HYPERLINK_VALIDATOR_AVAILABLE = True
    logger.info('Hyperlink Validator routes loaded')
except (ImportError, Exception) as e:
    logger.info(f'Hyperlink Validator not available: {e}')

HYPERLINK_HEALTH_AVAILABLE = False
try:
    from hyperlink_health import (
        HyperlinkHealthValidator, HealthMode,
        validate_document_links, export_report_json, export_report_html, export_report_csv
    )
    HYPERLINK_HEALTH_AVAILABLE = True
    logger.info('Hyperlink Health module loaded')
except (ImportError, Exception) as e:
    logger.info(f'Hyperlink Health not available: {e}')

JOB_MANAGER_AVAILABLE = False
try:
    from job_manager import (
        get_job_manager, JobManager, Job, JobPhase, JobStatus,
        create_review_job, get_job_status, get_job_result
    )
    JOB_MANAGER_AVAILABLE = True
    logger.info('Job Manager module loaded')
except (ImportError, Exception) as e:
    logger.info(f'Job Manager not available: {e}')

FIX_ASSISTANT_V2_AVAILABLE = False
decision_learner = None
report_generator = None
try:
    from fix_assistant_api import (
        build_document_content, group_similar_fixes,
        build_confidence_details, compute_fix_statistics,
        export_decision_log_csv, enhance_review_response,
        register_fix_assistant_routes
    )
    from decision_learner import DecisionLearner
    from report_generator import ReportGenerator
    decision_learner = DecisionLearner()
    report_generator = ReportGenerator()
    FIX_ASSISTANT_V2_AVAILABLE = True
    register_fix_assistant_routes(app)
    logger.info('Fix Assistant v2 loaded')
except (ImportError, Exception) as e:
    logger.info(f'Fix Assistant v2 not available: {e}')

# ---------------------------------------------------------------------------
# Initialize shared state and register route blueprints
# ---------------------------------------------------------------------------
from routes._shared import SessionManager, init_shared
import routes._shared as _shared_module

# Copy feature flags into the shared module so blueprints can access them
init_shared(sys.modules[__name__])

# Store SessionManager on app config for backwards compatibility
app.config['SESSION_MANAGER'] = SessionManager

# Register all route blueprints (core, review, config, roles, scan, jobs, data)
from routes import register_all_blueprints
register_all_blueprints(app)
logger.info('Route blueprints registered (7 modules)')

# ---------------------------------------------------------------------------
# Request lifecycle hooks
# ---------------------------------------------------------------------------

def check_authentication():
    """Check authentication if enabled. Returns None if OK, or (response, status_code) if denied."""
    if not config.auth_enabled:
        return None
    auth_provider = config.auth_provider
    if auth_provider == 'trusted_header':
        user = request.headers.get('X-Authenticated-User')
        if not user:
            logger.warning('Authentication failed: missing header', client_ip=request.remote_addr)
            return (jsonify({'success': False, 'error': {'code': 'AUTH_REQUIRED', 'message': 'Authentication required.'}}), 401)
        g.authenticated_user = user
        g.authenticated_groups = request.headers.get('X-Authenticated-Groups', '').split(',')
    elif auth_provider == 'api_key':
        api_key = request.headers.get('X-API-Key')
        expected_key = os.environ.get('TWR_API_KEY', '')
        if not expected_key:
            return (jsonify({'success': False, 'error': {'code': 'CONFIG_ERROR', 'message': 'Server auth not configured.'}}), 500)
        if not api_key or api_key != expected_key:
            return (jsonify({'success': False, 'error': {'code': 'AUTH_REQUIRED', 'message': 'Invalid or missing API key.'}}), 401)
        g.authenticated_user = 'api_key_user'
        g.authenticated_groups = ['api']
    return None


@app.before_request
def before_request():
    """Setup request context."""
    import json as _json
    correlation_id = StructuredLogger.new_correlation_id()
    g.correlation_id = correlation_id
    g.request_start = datetime.now()

    session_id = request.cookies.get('twr_session') or session.get('session_id')
    if not session_id:
        session_id = SessionManager.create()
        session['session_id'] = session_id
    elif not SessionManager.get(session_id):
        SessionManager.create(session_id)
    g.session_id = session_id

    if request.path.startswith('/api/'):
        exempt_paths = ['/api/health', '/api/health/assets', '/api/ready', '/api/csrf-token', '/api/version']
        if request.path not in exempt_paths:
            auth_result = check_authentication()
            if auth_result is not None:
                return auth_result

    if config.rate_limit_enabled:
        client_ip = request.remote_addr or 'unknown'
        # v5.0.0: Exempt localhost from rate limiting (single-user desktop app)
        is_localhost = client_ip in ('127.0.0.1', '::1', 'localhost')
        rate_limit_exempt = (
            is_localhost,
            request.path in ['/api/health', '/api/health/assets', '/api/ready', '/api/version', '/api/csrf-token'],
            request.path.startswith('/static/'),
            request.path.startswith('/vendor/'),
            request.path in ['/favicon.ico', '/logo.png']
        )
        if not any(rate_limit_exempt):
            rate_limiter = get_rate_limiter()
            if not rate_limiter.is_allowed(client_ip):
                retry_after = rate_limiter.get_retry_after(client_ip)
                logger.warning('Rate limit exceeded', client_ip=client_ip, retry_after=retry_after)
                return (jsonify({'success': False, 'error': {'code': 'RATE_LIMIT', 'message': 'Too many requests', 'retry_after': retry_after}}), 429)

    logger.debug('Request started', method=request.method, path=request.path, client_ip=request.remote_addr)
    return None


@app.after_request
def after_request(response: Response) -> Response:
    """Add security headers, correlation ID, and log request completion."""
    import json as _json

    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # v4.7.0: Prevent proxy/browser caching of API responses (fixes stale data issue)
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    correlation_id = StructuredLogger.get_correlation_id()
    response.headers['X-Correlation-ID'] = correlation_id

    # Content Security Policy
    allow_cdn = False
    try:
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                cfg = _json.load(f)
                allow_cdn = cfg.get('security', {}).get('allow_cdn_fallback', False)
    except Exception:
        pass

    if allow_cdn:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com "
            "https://cdn.jsdelivr.net https://d3js.org; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; font-src 'self'; connect-src 'self'"
        )
    else:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "font-src 'self'; connect-src 'self'"
        )

    if 'csrf_token' not in session:
        session['csrf_token'] = generate_csrf_token()
    response.headers['X-CSRF-Token'] = session['csrf_token']

    # v4.8.3: Gzip compression for text-based responses (JS, CSS, HTML, JSON)
    # Reduces ~8MB of static assets to ~1-2MB, dramatically improving page load
    # IMPORTANT: Skip streaming/file responses (direct_passthrough) — Flask's send_file()
    # uses file wrappers that break with get_data(). Only compress buffered responses.
    if (response.status_code == 200
            and not response.direct_passthrough
            and 'Content-Encoding' not in response.headers
            and 'gzip' in request.headers.get('Accept-Encoding', '')):
        content_type = response.content_type or ''
        compressible = any(ct in content_type for ct in [
            'text/', 'application/json', 'application/javascript',
            'application/xml', 'image/svg+xml'
        ])
        if compressible:
            try:
                import gzip as _gzip
                raw_data = response.get_data()
                if len(raw_data) > 500:
                    compressed = _gzip.compress(raw_data, compresslevel=6)
                    if len(compressed) < len(raw_data):
                        response.set_data(compressed)
                        response.headers['Content-Encoding'] = 'gzip'
                        response.headers['Content-Length'] = len(compressed)
                        response.headers['Vary'] = 'Accept-Encoding'
            except Exception:
                pass  # If compression fails, serve uncompressed

    # Add cache headers for static assets (JS/CSS don't change without cache-busting param)
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour

    duration_ms = 0
    if hasattr(g, 'request_start'):
        duration_ms = (datetime.now() - g.request_start).total_seconds() * 1000
    logger.info('Request completed', method=request.method, path=request.path,
                status=response.status_code, duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id)
    return response


# ---------------------------------------------------------------------------
# Cleanup utilities
# ---------------------------------------------------------------------------
_cleanup_thread = None
_cleanup_stop_event = None


def cleanup_temp_files(max_age_hours: int = 24):
    """Remove temporary files older than max_age_hours."""
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


def start_periodic_cleanup(interval_hours: int = 6):
    """Start background thread for periodic temp/session cleanup."""
    global _cleanup_thread, _cleanup_stop_event
    if _cleanup_thread is not None and _cleanup_thread.is_alive():
        return
    _cleanup_stop_event = threading.Event()

    def cleanup_loop():
        interval_seconds = interval_hours * 3600
        while not _cleanup_stop_event.wait(interval_seconds):
            try:
                logger.info('Running periodic cleanup...')
                cleanup_temp_files(max_age_hours=24)
            except Exception as e:
                logger.error(f'Periodic cleanup failed: {e}')

    _cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True, name='PeriodicCleanup')
    _cleanup_thread.start()
    logger.info(f'Started periodic cleanup thread (every {interval_hours}h)')


def stop_periodic_cleanup():
    """Stop the periodic cleanup thread."""
    global _cleanup_thread
    if _cleanup_stop_event:
        _cleanup_stop_event.set()
    if _cleanup_thread:
        _cleanup_thread.join(timeout=1)
        _cleanup_thread = None


def open_browser():
    """Open browser after short delay."""
    time.sleep(1.5)
    webbrowser.open(f'http://{config.host}:{config.port}')


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    """Main entry point."""
    cleanup_temp_files()
    start_periodic_cleanup()
    SessionManager.start_auto_cleanup(interval_seconds=3600, max_age_hours=24)

    # v5.0.0: Debug mode is ONLY allowed when explicitly passing --debug AND
    # TWR_ENV is NOT set to 'production'. For cyber security compliance,
    # debug mode is NEVER auto-enabled. The default environment is 'production'
    # to ensure no debug artifacts leak in deployed installations.
    env = os.environ.get('TWR_ENV', 'production')
    no_browser = '--no-browser' in sys.argv
    use_debug = '--debug' in sys.argv and env != 'production'
    if env == 'production':
        use_debug = False

    logger.info(f'Starting {APP_NAME}', version=VERSION, core_version=MODULE_VERSION,
                environment=env, debug=use_debug)

    print(f"\n{'=' * 60}")
    print(f'  {APP_NAME} v{VERSION}')
    print(f'  Core Engine v{MODULE_VERSION}')
    print(f'  Environment: {env}')
    print(f"{'=' * 60}")
    print(f'\n  Server: http://{config.host}:{config.port}')
    print(f"  CSRF Protection: {'Enabled' if config.csrf_enabled else 'Disabled'}")
    print(f"  Rate Limiting: {'Enabled' if config.rate_limit_enabled else 'Disabled'}")
    print(f"  Authentication: {'Enabled (' + config.auth_provider + ')' if config.auth_enabled else 'Disabled'}")
    print(f'  Max Upload: {config.max_content_length / 1048576:.0f}MB')

    if not config.auth_enabled:
        logger.warning('Authentication is DISABLED.')
        if config.host not in ('127.0.0.1', 'localhost'):
            logger.error('SECURITY RISK: Auth disabled AND bound to non-localhost address %s', config.host)
            print('  ⚠️  WARNING: Auth disabled on non-localhost — set TWR_AUTH=true')

    print('\n  Press Ctrl+C to stop\n')

    if not no_browser and not use_debug:
        threading.Thread(target=open_browser, daemon=True).start()

    if use_debug:
        logger.warning('DEBUG MODE ENABLED - DO NOT USE IN PRODUCTION')
        print('  ⚠️  DEBUG MODE - NOT FOR PRODUCTION USE')
        app.run(host=config.host, port=config.port, debug=use_debug)
    else:
        is_localhost = config.host in ['127.0.0.1', 'localhost', '0.0.0.0']
        if is_localhost and env != 'production':
            logger.info('Starting with Flask threaded server (localhost)')
            app.run(host=config.host, port=config.port, debug=False, threaded=True)
        else:
            try:
                from waitress import serve
                logger.info('Starting with Waitress WSGI server')
                serve(app, host=config.host, port=config.port, threads=4)
            except ImportError:
                logger.warning('Waitress not available, using Flask with threading')
                app.run(host=config.host, port=config.port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
