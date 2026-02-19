"""Core application routes (index, static files, error handlers, diagnostics).

Blueprint name: core
"""

from flask import Blueprint, send_file, request, jsonify, session, g, Response, make_response
from routes._shared import handle_api_errors, api_error_response, config, logger, sanitize_static_path, require_csrf
from config_logging import VERSION, get_version, generate_csrf_token, log_production_error, read_recent_error_logs
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import platform
import os
import re

core_bp = Blueprint('core', __name__)


# Error handlers
@core_bp.app_errorhandler(400)
def bad_request(e):
    error_id = log_production_error(e if isinstance(e, Exception) else Exception(str(e)), context={'flask_errorhandler': 400}, include_system_info=False)
    logger.warning(f'Bad request: {e}', error_id=error_id)
    return (jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': str(e), 'error_id': error_id}}), 400)


@core_bp.app_errorhandler(404)
def not_found(e):
    logger.debug(f'Not found: {request.path}')
    return (jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Resource not found'}}), 404)


@core_bp.app_errorhandler(413)
def payload_too_large(e):
    max_mb = config.max_content_length / 1048576
    error_id = log_production_error(e if isinstance(e, Exception) else Exception(str(e)), context={'flask_errorhandler': 413, 'max_mb': max_mb}, include_system_info=False)
    logger.warning(f'File too large: max={max_mb}MB', error_id=error_id)
    return (jsonify({'success': False, 'error': {'code': 'FILE_TOO_LARGE', 'message': f'File exceeds maximum size of {max_mb:.0f}MB', 'error_id': error_id}}), 413)


@core_bp.app_errorhandler(429)
def rate_limit_exceeded(e):
    logger.warning('Rate limit exceeded (429 handler)')
    return (jsonify({'success': False, 'error': {'code': 'RATE_LIMIT', 'message': 'Too many requests'}}), 429)


@core_bp.app_errorhandler(500)
def internal_error(e):
    error_id = log_production_error(e if isinstance(e, Exception) else Exception(str(e)), context={'flask_errorhandler': 500})
    logger.exception(f'Internal server error: {e}')
    return (jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'An internal error occurred', 'correlation_id': getattr(g, 'correlation_id', 'unknown'), 'error_id': error_id}}), 500)


# Diagnostics endpoints
@core_bp.route('/api/diagnostics/logs')
def get_error_logs():
    """
    Return recent structured error entries from logs/aegis.log.

    Query params:
      count  - number of entries (default 50, max 200)
      level  - filter by level (ERROR, WARNING, CRITICAL)
      search - substring search across error_type, error_message, handler
    """
    try:
        count = min(int(request.args.get('count', 50)), 200)
        level_filter = request.args.get('level', '').upper()
        search_term = request.args.get('search', '').lower()
        entries = read_recent_error_logs(count=count * 2)
        if level_filter:
            entries = [e for e in entries if e.get('level', 'ERROR').upper() == level_filter]
        if search_term:
            def _matches(entry):
                searchable = ' '.join([str(entry.get('error_type', '')), str(entry.get('error_message', '')), str(entry.get('context', {}).get('handler', '')), str(entry.get('request', {}).get('filename', ''))]).lower()
                return search_term in searchable
            entries = [e for e in entries if _matches(e)]
        entries = entries[:count]
        return jsonify({'success': True, 'data': {'entries': entries, 'total': len(entries), 'log_file': str(config.log_dir / 'aegis.log')}})
    except Exception as e:
        logger.exception(f'Error reading error logs: {e}')
        return (jsonify({'success': False, 'error': {'code': 'LOG_READ_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/logs/<error_id>')
def get_error_log_detail(error_id):
    """Look up a specific error entry by its error_id."""
    try:
        entries = read_recent_error_logs(count=500)
        match = next((e for e in entries if e.get('error_id') == error_id), None)
        if not match:
            return (jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'No error entry with id {error_id}'}}), 404)
        else:
            return jsonify({'success': True, 'data': match})
    except Exception as e:
        logger.exception(f'Error looking up error {error_id}: {e}')
        return (jsonify({'success': False, 'error': {'code': 'LOG_READ_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/summary')
@handle_api_errors
def diagnostics_summary():
    """
    Get comprehensive diagnostics summary for troubleshooting.

    Returns:
    - Recent error logs (last 10 errors)
    - App version and uptime
    - System information
    - Configuration status
    - Feature availability
    """
    try:
        # Collect recent errors
        entries = read_recent_error_logs(count=10)

        # System info (non-sensitive)
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'app_version': get_version(),
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'
        }

        # Check log file size
        log_file = config.log_dir / 'aegis.log'
        log_size_mb = 0
        if log_file.exists():
            log_size_mb = round(log_file.stat().st_size / (1024 * 1024), 2)

        # Error summary
        error_types = {}
        for entry in entries:
            err_type = entry.get('error_type', 'Unknown')
            error_types[err_type] = error_types.get(err_type, 0) + 1

        return jsonify({
            'success': True,
            'data': {
                'system': system_info,
                'recent_errors': entries,
                'error_summary': {
                    'total_recent': len(entries),
                    'by_type': error_types
                },
                'log_file': {
                    'path': str(log_file),
                    'size_mb': log_size_mb
                },
                'config': {
                    'debug_mode': config.debug,
                    'log_level': config.log_level,
                    'auth_enabled': config.auth_enabled,
                    'csrf_enabled': config.csrf_enabled
                }
            }
        })
    except Exception as e:
        logger.exception(f'Error generating diagnostics summary: {e}')
        return (jsonify({'success': False, 'error': {'code': 'DIAGNOSTICS_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/errors')
@handle_api_errors
def diagnostics_errors():
    """
    Return recent errors with filtering options.

    Query params:
      count  - number of entries (default 50, max 200)
      level  - filter by level (ERROR, WARNING, CRITICAL)
      type   - filter by error_type
      search - substring search
    """
    try:
        count = min(int(request.args.get('count', 50)), 200)
        level_filter = request.args.get('level', '').upper()
        type_filter = request.args.get('type', '').lower()
        search_term = request.args.get('search', '').lower()

        entries = read_recent_error_logs(count=count * 2)

        # Apply filters
        if level_filter:
            entries = [e for e in entries if e.get('level', 'ERROR').upper() == level_filter]

        if type_filter:
            entries = [e for e in entries if type_filter in e.get('error_type', '').lower()]

        if search_term:
            def _matches(entry):
                searchable = ' '.join([
                    str(entry.get('error_type', '')),
                    str(entry.get('error_message', '')),
                    str(entry.get('context', {}).get('handler', '')),
                    str(entry.get('request', {}).get('filename', ''))
                ]).lower()
                return search_term in searchable
            entries = [e for e in entries if _matches(e)]

        entries = entries[:count]

        return jsonify({
            'success': True,
            'data': {
                'entries': entries,
                'total': len(entries),
                'filters_applied': {
                    'level': level_filter or None,
                    'type': type_filter or None,
                    'search': search_term or None
                }
            }
        })
    except Exception as e:
        logger.exception(f'Error fetching diagnostics errors: {e}')
        return (jsonify({'success': False, 'error': {'code': 'DIAGNOSTICS_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/export', methods=['POST'])
@require_csrf
@handle_api_errors
def diagnostics_export():
    """
    Export diagnostics as a downloadable JSON or TXT file.

    Expects JSON body:
      format             - 'json' or 'txt' (default 'json')
      include_system_info - bool (default True)
      include_request_log - bool (default True)
    """
    try:
        data = request.get_json(silent=True) or {}
        fmt = data.get('format', 'json')
        include_system = data.get('include_system_info', True)
        include_requests = data.get('include_request_log', True)

        # Collect diagnostic data
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'app_version': get_version()
        }

        # System info
        if include_system:
            export_data['system'] = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'architecture': platform.machine(),
                'processor': platform.processor() or 'unknown',
                'app_version': get_version()
            }

        # Configuration (non-sensitive)
        export_data['config'] = {
            'debug_mode': config.debug,
            'log_level': config.log_level,
            'auth_enabled': config.auth_enabled,
            'csrf_enabled': config.csrf_enabled,
            'max_content_length_mb': config.max_content_length / 1048576
        }

        # Log file info
        log_file = config.log_dir / 'aegis.log'
        log_size_mb = 0
        if log_file.exists():
            log_size_mb = round(log_file.stat().st_size / (1024 * 1024), 2)
        export_data['log_file'] = {
            'path': str(log_file),
            'size_mb': log_size_mb,
            'exists': log_file.exists()
        }

        # Recent errors
        entries = read_recent_error_logs(count=50)
        export_data['recent_errors'] = entries
        export_data['error_summary'] = {
            'total': len(entries),
            'by_type': {}
        }
        for entry in entries:
            err_type = entry.get('error_type', 'Unknown')
            export_data['error_summary']['by_type'][err_type] = export_data['error_summary']['by_type'].get(err_type, 0) + 1

        # Feature availability
        try:
            import importlib
            features = {}
            for mod_name, label in [
                ('docx', 'python-docx'),
                ('nltk', 'NLTK'),
                ('spacy', 'spaCy'),
                ('textstat', 'textstat'),
                ('openpyxl', 'openpyxl'),
                ('requests', 'requests'),
            ]:
                try:
                    mod = importlib.import_module(mod_name)
                    ver = getattr(mod, '__version__', 'installed')
                    features[label] = {'available': True, 'version': ver}
                except ImportError:
                    features[label] = {'available': False, 'version': None}
            export_data['features'] = features
        except Exception:
            pass

        # Build response
        import json as json_mod
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if fmt == 'txt':
            # Build plain text report
            lines = []
            lines.append('=' * 60)
            lines.append('AEGIS DIAGNOSTIC EXPORT')
            lines.append('=' * 60)
            lines.append(f"Exported: {export_data['export_timestamp']}")
            lines.append(f"Version:  {export_data['app_version']}")
            lines.append('')

            if include_system and 'system' in export_data:
                lines.append('--- System Information ---')
                for k, v in export_data['system'].items():
                    lines.append(f"  {k}: {v}")
                lines.append('')

            lines.append('--- Configuration ---')
            for k, v in export_data['config'].items():
                lines.append(f"  {k}: {v}")
            lines.append('')

            lines.append('--- Log File ---')
            for k, v in export_data['log_file'].items():
                lines.append(f"  {k}: {v}")
            lines.append('')

            if 'features' in export_data:
                lines.append('--- Feature Availability ---')
                for name, info in export_data['features'].items():
                    status = f"v{info['version']}" if info['available'] else 'NOT INSTALLED'
                    lines.append(f"  {name}: {status}")
                lines.append('')

            lines.append(f"--- Recent Errors ({export_data['error_summary']['total']}) ---")
            for entry in export_data['recent_errors'][:20]:
                lines.append(f"  [{entry.get('level', 'ERROR')}] {entry.get('timestamp', '?')} - {entry.get('error_type', '?')}: {entry.get('error_message', '?')}")
            lines.append('')

            content = '\n'.join(lines)
            resp = make_response(content)
            resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
            resp.headers['Content-Disposition'] = f'attachment; filename="aegis_diagnostics_{timestamp}.txt"'
            return resp
        else:
            # JSON export
            content = json_mod.dumps(export_data, indent=2, default=str)
            resp = make_response(content)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            resp.headers['Content-Disposition'] = f'attachment; filename="aegis_diagnostics_{timestamp}.json"'
            return resp

    except Exception as e:
        logger.exception(f'Error exporting diagnostics: {e}')
        return (jsonify({'success': False, 'error': {'code': 'EXPORT_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/email', methods=['POST'])
@require_csrf
@handle_api_errors
def diagnostics_email():
    """
    Generate a .eml file with diagnostic logs attached.

    The .eml format is a standard RFC 2822 email message that Outlook and
    Apple Mail can open as a pre-composed draft with attachments already
    included. This solves the mailto: limitation of not being able to attach files.

    Expects JSON body:
      to_email - recipient email address (optional, defaults to configured support email)
    """
    import json as json_mod
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    import io

    try:
        data = request.get_json(silent=True) or {}
        to_email = data.get('to_email', '')

        # --- Collect diagnostic data (same as diagnostics_export) ---
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'app_version': get_version()
        }

        export_data['system'] = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.machine(),
            'processor': platform.processor() or 'unknown',
            'app_version': get_version()
        }

        export_data['config'] = {
            'debug_mode': config.debug,
            'log_level': config.log_level,
            'auth_enabled': config.auth_enabled,
            'csrf_enabled': config.csrf_enabled,
            'max_content_length_mb': config.max_content_length / 1048576
        }

        # Log file info
        log_file = config.log_dir / 'aegis.log'
        log_size_mb = 0
        if log_file.exists():
            log_size_mb = round(log_file.stat().st_size / (1024 * 1024), 2)
        export_data['log_file'] = {
            'path': str(log_file),
            'size_mb': log_size_mb,
            'exists': log_file.exists()
        }

        # Recent errors
        entries = read_recent_error_logs(count=50)
        export_data['recent_errors'] = entries
        export_data['error_summary'] = {'total': len(entries), 'by_type': {}}
        for entry in entries:
            err_type = entry.get('error_type', 'Unknown')
            export_data['error_summary']['by_type'][err_type] = export_data['error_summary']['by_type'].get(err_type, 0) + 1

        # Feature availability
        try:
            import importlib
            features = {}
            for mod_name, label in [
                ('docx', 'python-docx'), ('nltk', 'NLTK'), ('spacy', 'spaCy'),
                ('textstat', 'textstat'), ('openpyxl', 'openpyxl'), ('requests', 'requests'),
            ]:
                try:
                    mod = importlib.import_module(mod_name)
                    ver = getattr(mod, '__version__', 'installed')
                    features[label] = {'available': True, 'version': ver}
                except ImportError:
                    features[label] = {'available': False, 'version': None}
            export_data['features'] = features
        except Exception:
            pass

        # Health check data
        health_data = {}
        try:
            import importlib as il2
            pkgs = {}
            for mod_name, label in [
                ('flask', 'Flask'), ('docx', 'python-docx'), ('nltk', 'NLTK'),
                ('spacy', 'spaCy'), ('textstat', 'textstat'), ('openpyxl', 'openpyxl'),
                ('requests', 'requests'), ('waitress', 'Waitress'), ('mammoth', 'mammoth'),
            ]:
                try:
                    mod = il2.import_module(mod_name)
                    ver = getattr(mod, '__version__', 'installed')
                    pkgs[label] = {'status': 'installed', 'version': ver, 'available': True}
                except ImportError:
                    pkgs[label] = {'status': 'missing', 'version': None, 'available': False}
            health_data['packages'] = pkgs
        except Exception:
            pass

        # --- Build email body text ---
        version_str = get_version()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        body_lines = [
            'AEGIS DIAGNOSTIC REPORT',
            '=' * 50,
            f'Generated: {date_str}',
            f'Version: {version_str}',
            '',
            'SYSTEM INFORMATION',
            '-' * 30,
            f"  Platform: {export_data['system']['platform']}",
            f"  Python: {export_data['system']['python_version']}",
            f"  Architecture: {export_data['system']['architecture']}",
            '',
            'CONFIGURATION',
            '-' * 30,
            f"  Debug Mode: {export_data['config']['debug_mode']}",
            f"  Log Level: {export_data['config']['log_level']}",
            f"  Max Upload: {export_data['config']['max_content_length_mb']:.0f} MB",
            '',
            'LOG FILE',
            '-' * 30,
            f"  Path: {export_data['log_file']['path']}",
            f"  Size: {export_data['log_file']['size_mb']} MB",
            f"  Exists: {export_data['log_file']['exists']}",
            '',
        ]

        # Feature availability
        if 'features' in export_data:
            body_lines.append('FEATURE AVAILABILITY')
            body_lines.append('-' * 30)
            for name, info in export_data['features'].items():
                status = f"v{info['version']}" if info['available'] else 'NOT INSTALLED'
                body_lines.append(f"  {name}: {status}")
            body_lines.append('')

        # Health check packages
        if health_data.get('packages'):
            pkgs = health_data['packages']
            installed = [k for k, v in pkgs.items() if v.get('available')]
            missing = [k for k, v in pkgs.items() if not v.get('available')]
            body_lines.append('DEPENDENCY HEALTH')
            body_lines.append('-' * 30)
            body_lines.append(f"  Installed: {len(installed)} | Missing: {len(missing)}")
            if missing:
                body_lines.append(f"  Missing: {', '.join(missing)}")
            body_lines.append('')

        # Recent errors summary
        error_count = export_data['error_summary']['total']
        body_lines.append(f'RECENT ERRORS ({error_count})')
        body_lines.append('-' * 30)
        if error_count == 0:
            body_lines.append('  No recent errors logged.')
        else:
            for entry in export_data['recent_errors'][:15]:
                ts = entry.get('timestamp', '?')
                etype = entry.get('error_type', '?')
                emsg = entry.get('error_message', '?')
                body_lines.append(f"  [{ts}] {etype}: {emsg}")
            if error_count > 15:
                body_lines.append(f"  ... and {error_count - 15} more (see attached log)")
        body_lines.append('')
        body_lines.append('Full diagnostic data and log entries are attached to this email.')

        body_text = '\n'.join(body_lines)

        # --- Build .eml with MIME ---
        subject = f'AEGIS Diagnostic Report - {date_str} - v{version_str}'

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['To'] = to_email
        msg['From'] = ''
        msg['X-Unsent'] = '1'  # Mark as draft (Outlook/Apple Mail will open as unsent)

        # Email body
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Attachment 1: Diagnostic JSON
        diag_json = json_mod.dumps(export_data, indent=2, default=str)
        diag_attachment = MIMEBase('application', 'json')
        diag_attachment.set_payload(diag_json.encode('utf-8'))
        encoders.encode_base64(diag_attachment)
        diag_filename = f'aegis_diagnostics_{timestamp}.json'
        diag_attachment.add_header('Content-Disposition', 'attachment', filename=diag_filename)
        msg.attach(diag_attachment)

        # Attachment 2: aegis.log (if it exists and is non-empty)
        if log_file.exists() and log_file.stat().st_size > 0:
            try:
                log_content = log_file.read_bytes()
                # Cap at 5MB to prevent huge email
                if len(log_content) > 5 * 1024 * 1024:
                    log_content = log_content[-5 * 1024 * 1024:]  # Last 5MB
                log_attachment = MIMEBase('text', 'plain')
                log_attachment.set_payload(log_content)
                encoders.encode_base64(log_attachment)
                log_attachment.add_header('Content-Disposition', 'attachment', filename='aegis.log')
                msg.attach(log_attachment)
            except Exception as log_err:
                logger.warning(f'Could not attach aegis.log: {log_err}')

        # Attachment 3: Other .log files (only non-trivial ones, capped at 10MB total)
        try:
            total_attached = 0
            max_total = 10 * 1024 * 1024  # 10MB budget for additional logs
            # Sort by size descending so we get the most important logs first
            other_logs = sorted(
                [f for f in config.log_dir.glob('*.log') if f.name != 'aegis.log' and f.stat().st_size > 1024],
                key=lambda f: f.stat().st_size,
                reverse=True
            )
            for other_log in other_logs:
                if total_attached >= max_total:
                    break
                try:
                    content_bytes = other_log.read_bytes()
                    if len(content_bytes) > 2 * 1024 * 1024:
                        content_bytes = content_bytes[-2 * 1024 * 1024:]  # Last 2MB
                    total_attached += len(content_bytes)
                    att = MIMEBase('text', 'plain')
                    att.set_payload(content_bytes)
                    encoders.encode_base64(att)
                    att.add_header('Content-Disposition', 'attachment', filename=other_log.name)
                    msg.attach(att)
                except Exception:
                    pass
        except Exception:
            pass

        # Save .eml to temp file and open in default mail client
        import subprocess
        import tempfile

        eml_content = msg.as_string()
        eml_filename = f'aegis_diagnostic_email_{timestamp}.eml'

        # Save to a temp directory (persists until manually cleaned or reboot)
        eml_dir = Path(tempfile.gettempdir()) / 'aegis_emails'
        eml_dir.mkdir(exist_ok=True)
        eml_path = eml_dir / eml_filename
        eml_path.write_text(eml_content, encoding='utf-8')

        # Auto-open in the default mail client (Outlook / Apple Mail)
        opened = False
        try:
            if platform.system() == 'Darwin':
                # macOS: try Outlook first, fall back to default handler
                try:
                    subprocess.Popen(['open', '-a', 'Microsoft Outlook', str(eml_path)])
                    opened = True
                except Exception:
                    try:
                        subprocess.Popen(['open', str(eml_path)])
                        opened = True
                    except Exception:
                        pass
            elif platform.system() == 'Windows':
                os.startfile(str(eml_path))
                opened = True
        except Exception as open_err:
            logger.warning(f'Could not auto-open .eml: {open_err}')

        return jsonify({
            'success': True,
            'opened': opened,
            'filename': eml_filename,
            'path': str(eml_path),
            'attachments': len(msg.get_payload()) - 1  # subtract body part
        })

    except Exception as e:
        logger.exception(f'Error generating diagnostic email: {e}')
        return (jsonify({'success': False, 'error': {'code': 'EMAIL_EXPORT_ERROR', 'message': str(e)}}), 500)


@core_bp.route('/api/diagnostics/frontend', methods=['POST'])
def diagnostics_frontend():
    """
    Receive frontend diagnostic logs from the browser.
    Accepts batched log entries from frontend-logger.js.
    """
    try:
        data = request.get_json(silent=True) or {}
        logs = data.get('logs', [])
        if logs:
            logger.debug(f'Received {len(logs)} frontend log entries')
        return jsonify({'success': True, 'received': len(logs)})
    except Exception as e:
        return jsonify({'success': True, 'received': 0})


@core_bp.route('/api/diagnostics/frontend-logs', methods=['POST'])
def diagnostics_frontend_logs():
    """
    Receive frontend console capture logs from the browser.
    Accepts batched console entries from console-capture.js.
    """
    try:
        data = request.get_json(silent=True) or {}
        logs = data.get('logs', [])
        if logs:
            logger.debug(f'Received {len(logs)} frontend console entries')
        return jsonify({'success': True, 'received': len(logs)})
    except Exception as e:
        return jsonify({'success': True, 'received': 0})


@core_bp.route('/api/diagnostics/health')
@handle_api_errors
def diagnostics_health():
    """
    Dependency health check — verify all required packages and NLP models are installed.
    Returns per-package status with version info and NLP model availability.
    """
    try:
        import importlib
        results = {'packages': {}, 'nlp_models': {}, 'overall': 'healthy'}

        # Check required Python packages
        required_packages = [
            # Core framework
            ('flask', 'Flask'),
            ('werkzeug', 'Werkzeug'),
            ('jinja2', 'Jinja2'),
            ('waitress', 'Waitress'),
            # Document processing
            ('docx', 'python-docx'),
            ('mammoth', 'mammoth'),
            ('openpyxl', 'openpyxl'),
            ('pymupdf4llm', 'pymupdf4llm'),
            ('reportlab', 'reportlab'),
            # NLP & text analysis
            ('nltk', 'NLTK'),
            ('spacy', 'spaCy'),
            ('textstat', 'textstat'),
            ('proselint', 'proselint'),
            ('symspellpy', 'symspellpy'),
            # Scientific computing
            ('numpy', 'NumPy'),
            ('pandas', 'pandas'),
            ('scipy', 'SciPy'),
            ('sklearn', 'scikit-learn'),
            ('torch', 'PyTorch'),
            # Web & parsing
            ('requests', 'requests'),
            ('chardet', 'chardet'),
            ('bs4', 'BeautifulSoup4'),
            ('lxml', 'lxml'),
            ('yaml', 'PyYAML'),
            # Imaging
            ('PIL', 'Pillow'),
        ]

        all_ok = True
        for mod_name, display_name in required_packages:
            try:
                mod = importlib.import_module(mod_name)
                ver = getattr(mod, '__version__', getattr(mod, 'VERSION', 'installed'))
                if isinstance(ver, tuple):
                    ver = '.'.join(str(v) for v in ver)
                results['packages'][display_name] = {
                    'status': 'ok',
                    'version': str(ver),
                    'module': mod_name
                }
            except ImportError:
                results['packages'][display_name] = {
                    'status': 'missing',
                    'version': None,
                    'module': mod_name
                }
                all_ok = False

        # Check NLTK data
        try:
            import nltk
            nltk_data_items = ['punkt', 'punkt_tab', 'averaged_perceptron_tagger',
                               'averaged_perceptron_tagger_eng', 'stopwords', 'wordnet']
            for item in nltk_data_items:
                try:
                    nltk.data.find(f'tokenizers/{item}' if 'punkt' in item else f'corpora/{item}' if item in ('stopwords', 'wordnet') else f'taggers/{item}')
                    results['nlp_models'][f'nltk/{item}'] = {'status': 'ok'}
                except LookupError:
                    results['nlp_models'][f'nltk/{item}'] = {'status': 'missing'}
                    all_ok = False
        except ImportError:
            results['nlp_models']['nltk'] = {'status': 'nltk not installed'}
            all_ok = False

        # Check spaCy model
        try:
            import spacy
            try:
                nlp = spacy.load('en_core_web_sm')
                results['nlp_models']['spacy/en_core_web_sm'] = {
                    'status': 'ok',
                    'version': nlp.meta.get('version', 'unknown')
                }
            except OSError:
                results['nlp_models']['spacy/en_core_web_sm'] = {'status': 'missing'}
                all_ok = False
        except ImportError:
            results['nlp_models']['spacy'] = {'status': 'spacy not installed'}
            all_ok = False

        if not all_ok:
            results['overall'] = 'degraded'

        # Count
        pkg_ok = sum(1 for p in results['packages'].values() if p['status'] == 'ok')
        pkg_total = len(results['packages'])
        nlp_ok = sum(1 for m in results['nlp_models'].values() if m['status'] == 'ok')
        nlp_total = len(results['nlp_models'])
        results['summary'] = {
            'packages': f'{pkg_ok}/{pkg_total} installed',
            'nlp_models': f'{nlp_ok}/{nlp_total} available',
            'all_healthy': all_ok
        }

        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logger.exception(f'Error running health check: {e}')
        return (jsonify({'success': False, 'error': {'code': 'HEALTH_CHECK_ERROR', 'message': str(e)}}), 500)


# Demo endpoints
@core_bp.route('/loader-demo')
def loader_demo():
    """Demo page for the AEGIS cinematic loader."""
    demo_path = config.base_dir / 'templates' / 'loader-demo.html'
    if demo_path.exists():
        with open(demo_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), content_type='text/html')
    else:
        return ('Demo not found', 404)


# Main index route
@core_bp.route('/')
def index():
    """Serve the main application page.

    v3.0.49: Check templates/index.html first (transport layout),
    then fall back to index.html (legacy flat layout).
    """
    index_path = config.base_dir / 'templates' / 'index.html'
    if not index_path.exists():
        index_path = config.base_dir / 'index.html'
    if not index_path.exists():
        logger.error('index.html not found', checked_paths=[str(config.base_dir / 'templates' / 'index.html'), str(config.base_dir / 'index.html')])
        return (jsonify({'success': False, 'error': {'code': 'CONFIG_ERROR', 'message': 'Application not properly installed'}}), 500)
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        logger.exception(f'Failed to read index.html: {e}')
        return (jsonify({'success': False, 'error': {'code': 'IO_ERROR', 'message': 'Failed to load application'}}), 500)
    csrf_token = session.get('csrf_token') or generate_csrf_token()
    session['csrf_token'] = csrf_token
    # v4.9.9: Read version FRESH from version.json every request (never stale)
    ver = get_version()
    csrf_meta = f'<meta name="csrf-token" content="{csrf_token}">'
    version_meta = f'<meta name="aegis-version" content="{ver}">'
    content = content.replace('<head>', f'<head>\n    {csrf_meta}\n    {version_meta}')
    # v4.7.0: Inject version into all display elements server-side (single source of truth)
    # This ensures correct version even when JS files are browser-cached
    content = content.replace('id="lp-version"></span>', f'id="lp-version">v{ver}</span>')
    content = content.replace('id="version-label"></span>', f'id="version-label">Enterprise v{ver}</span>')
    content = content.replace('id="footer-version"></div>', f'id="footer-version">v{ver}</div>')
    content = content.replace('id="help-version"></span>', f'id="help-version">v{ver}</span>')
    # v4.9.9: Cache-bust static JS/CSS — replace any existing ?v= with fresh version
    content = re.sub(r'\.js\?v=[^"\']*(["\'])', rf'.js?v={ver}\1', content)
    content = re.sub(r'\.css\?v=[^"\']*(["\'])', rf'.css?v={ver}\1', content)
    # Also add ?v= to any JS/CSS that don't have it yet (negative lookahead for ?)
    content = re.sub(r'\.js(["\'])(?!\?)', rf'.js?v={ver}\1', content)
    content = re.sub(r'\.css(["\'])(?!\?)', rf'.css?v={ver}\1', content)
    # v4.7.0: Prevent browser from caching the HTML page (contains dynamic CSRF + version)
    from flask import make_response as _make_response
    resp = _make_response(content)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


# Session management
@core_bp.route('/api/clear-session')
def clear_session_endpoint():
    """Clear session cookie for troubleshooting. v4.0.3 dev utility."""
    resp = make_response(jsonify({'success': True, 'message': 'Session cleared'}))
    resp.delete_cookie('session', path='/')
    session.clear()
    return resp


# Static file serving routes
@core_bp.route('/static/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files.
    
    v3.0.49: Uses sanitize_static_path for proper nested path handling.
    Checks multiple locations for compatibility with different
    installation layouts (flat vs structured).
    """
    safe_name = sanitize_static_path(filename, {'.css'})
    if not safe_name:
        return api_error_response('INVALID_PATH', 'Invalid path', 400)
    else:
        possible_paths = [config.base_dir / 'static' / 'css' / safe_name, config.base_dir / 'css' / safe_name, config.base_dir / safe_name]
        for css_path in possible_paths:
            if css_path.exists():
                return send_file(css_path, mimetype='text/css')
        return api_error_response('NOT_FOUND', f'CSS file not found: {safe_name}', 404)


@core_bp.route('/static/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files.
    
    v3.0.49: Uses sanitize_static_path to properly handle nested paths
    like ui/state.js, features/roles.js, api/client.js.
    """
    safe_name = sanitize_static_path(filename, {'.js'})
    if not safe_name:
        return api_error_response('INVALID_PATH', 'Invalid path', 400)
    else:
        possible_paths = [config.base_dir / 'static' / 'js' / safe_name, config.base_dir / 'js' / safe_name, config.base_dir / safe_name]
        for js_path in possible_paths:
            if js_path.exists():
                return send_file(js_path, mimetype='application/javascript')
        logger.debug('JS file not found', requested=filename, safe_name=safe_name, checked_paths=[str(p) for p in possible_paths])
        return api_error_response('NOT_FOUND', f'JavaScript file not found: {safe_name}', 404)


@core_bp.route('/static/js/vendor/<path:filename>')
def serve_vendor_js(filename):
    """Serve vendored JavaScript libraries.

    v3.0.49: Uses sanitize_static_path for security.
    Checks multiple locations for compatibility with different
    installation layouts. Returns 404 for missing files so that
    onerror CDN fallback triggers properly.
    """
    safe_name = sanitize_static_path(filename, {'.js', '.mjs'})
    if not safe_name:
        return api_error_response('INVALID_PATH', 'Invalid path', 400)
    else:
        possible_paths = [config.base_dir / 'vendor' / safe_name, config.base_dir / 'static' / 'js' / 'vendor' / safe_name, config.base_dir / 'js' / 'vendor' / safe_name]
        mimetype = 'application/javascript'
        for vendor_path in possible_paths:
            if vendor_path.exists():
                return send_file(vendor_path, mimetype=mimetype)
        return api_error_response('NOT_FOUND', f'Vendor file not found: {safe_name}', 404)


@core_bp.route('/static/images/<path:filename>')
def serve_images(filename):
    """Serve image files.
    
    v3.0.49: Uses sanitize_static_path for consistency.
    SECURITY: Only serves allowed image extensions and restricts root fallback
    to a strict allowlist to prevent arbitrary file disclosure.
    """
    allowed_extensions = {'.webp', '.gif', '.svg', '.ico', '.jpeg', '.png', '.jpg'}
    safe_name = sanitize_static_path(filename, allowed_extensions)
    if not safe_name:
        logger.warning('Blocked invalid image request to /static/images', requested_file=filename)
        return api_error_response('NOT_FOUND', 'Image not found', 404)
    else:
        ext = Path(safe_name).suffix.lower()
        root_allowed_files = {'logo.png', 'favicon.ico'}
        img_path = config.base_dir / 'images' / safe_name
        if not img_path.exists() and safe_name in root_allowed_files:
                img_path = config.base_dir / safe_name
        if img_path.exists():
            mime_types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webp': 'image/webp'}
            mime = mime_types.get(ext, 'image/png')
            return send_file(img_path, mimetype=mime)
        else:
            return api_error_response('NOT_FOUND', f'Image not found: {safe_name}', 404)


@core_bp.route('/favicon.ico')
def serve_favicon():
    """Serve favicon with fallback to app root.
    
    Checks both /images subdirectory and app root for compatibility
    with different installation methods.
    """
    favicon_path = config.base_dir / 'images' / 'favicon.ico'
    if not favicon_path.exists():
        favicon_path = config.base_dir / 'favicon.ico'
    if favicon_path.exists():
        return send_file(favicon_path, mimetype='image/x-icon')
    else:
        return ('', 204)


# CSRF token endpoint
@core_bp.route('/api/csrf-token', methods=['GET'])
@handle_api_errors
def get_csrf_token():
    """Get a fresh CSRF token."""
    token = generate_csrf_token()
    session['csrf_token'] = token
    return jsonify({'csrf_token': token})
