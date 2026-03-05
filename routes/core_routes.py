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




def _collect_manager_diagnostics():
    """
    Collect Manager-level diagnostics directly from the running AEGIS process.
    Includes: package health (subprocess imports), pip list, disk space,
    Python details, wheels inventory, torch wheel status, server info,
    Manager version.  All via stdlib — no Manager import needed.
    """
    import shutil
    import time as _time

    diag = {}
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python = _find_python_exe()

    # --- 1. Package health (subprocess imports) ---
    CRITICAL_PACKAGES = [
        ('flask', 'Flask'), ('numpy', 'numpy'), ('pandas', 'pandas'),
        ('scipy', 'scipy'), ('sklearn', 'scikit-learn'), ('nltk', 'NLTK'),
        ('spacy', 'spaCy'), ('docx', 'python-docx'), ('openpyxl', 'openpyxl'),
        ('requests', 'requests'), ('waitress', 'Waitress'), ('mammoth', 'mammoth'),
        ('textstat', 'textstat'), ('torch', 'torch'),
        ('sentence_transformers', 'sentence-transformers'),
    ]
    pkg_health = {}
    for import_name, label in CRITICAL_PACKAGES:
        try:
            result = subprocess.run(
                [python, '-c', f'import {import_name}; v=getattr({import_name},"__version__","installed"); print("OK|"+str(v))'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and 'OK|' in result.stdout:
                ver = result.stdout.strip().split('OK|', 1)[1]
                pkg_health[label] = {'status': 'ok', 'version': ver}
            else:
                err = (result.stderr or result.stdout or 'unknown error').strip()[:120]
                pkg_health[label] = {'status': 'fail', 'error': err}
        except subprocess.TimeoutExpired:
            pkg_health[label] = {'status': 'timeout'}
        except Exception as e:
            pkg_health[label] = {'status': 'error', 'error': str(e)[:80]}
    diag['package_health'] = pkg_health

    # --- 2. pip list ---
    try:
        import json as _json
        result = subprocess.run(
            [python, '-m', 'pip', 'list', '--format=json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            pip_pkgs = _json.loads(result.stdout)
            diag['pip_packages'] = {p['name']: p['version'] for p in pip_pkgs}
            diag['pip_package_count'] = len(pip_pkgs)
        else:
            diag['pip_packages'] = None
            diag['pip_error'] = (result.stderr or 'unknown')[:200]
    except Exception as e:
        diag['pip_packages'] = None
        diag['pip_error'] = str(e)[:120]

    # --- 3. Disk space ---
    try:
        usage = shutil.disk_usage(app_dir)
        diag['disk_space'] = {
            'total_gb': round(usage.total / (1024 ** 3), 1),
            'free_gb': round(usage.free / (1024 ** 3), 1),
            'used_gb': round(usage.used / (1024 ** 3), 1),
            'free_pct': round(100 * usage.free / usage.total, 1),
        }
    except Exception as e:
        diag['disk_space'] = {'error': str(e)[:80]}

    # --- 4. Python details ---
    diag['python'] = {
        'executable': sys.executable,
        'version': sys.version,
        'prefix': sys.prefix,
        'platform': sys.platform,
    }

    # --- 5. Wheels inventory ---
    wheels_dirs = _find_wheels_dirs()
    wheels_info = {}
    torch_wheel_found = False
    total_wheel_count = 0
    for wd in wheels_dirs:
        whl_files = glob.glob(os.path.join(wd, '*.whl'))
        total_wheel_count += len(whl_files)
        total_size = sum(os.path.getsize(f) for f in whl_files)
        wheels_info[wd] = {
            'count': len(whl_files),
            'total_size_mb': round(total_size / (1024 * 1024), 1),
        }
        # Check for torch wheel
        for whl in whl_files:
            if 'torch' in os.path.basename(whl).lower():
                torch_wheel_found = True
                wheels_info['torch_wheel'] = {
                    'path': whl,
                    'size_mb': round(os.path.getsize(whl) / (1024 * 1024), 1),
                }
                break
    # Also check torch_split
    split_dir = os.path.join(app_dir, 'packaging', 'wheels', 'torch_split')
    if not torch_wheel_found and os.path.isdir(split_dir):
        parts = glob.glob(os.path.join(split_dir, 'torch_part_*'))
        if parts:
            wheels_info['torch_split_parts'] = len(parts)

    diag['wheels'] = {
        'directories': wheels_info,
        'total_wheels': total_wheel_count,
        'torch_wheel_found': torch_wheel_found,
    }

    # --- 6. Server process info ---
    diag['server'] = {
        'pid': os.getpid(),
        'python_exe': python,
    }
    # Try to get server start time from /proc or psutil
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        start_time = proc.create_time()
        uptime_secs = _time.time() - start_time
        hours, rem = divmod(int(uptime_secs), 3600)
        mins, secs = divmod(rem, 60)
        diag['server']['uptime'] = f'{hours}h {mins}m {secs}s'
        diag['server']['started_at'] = datetime.fromtimestamp(start_time).isoformat()
    except ImportError:
        # No psutil — use a rough estimate from module load time
        pass
    except Exception:
        pass

    # --- 7. Manager version ---
    manager_path = os.path.join(app_dir, 'aegis_manager.py')
    if os.path.exists(manager_path):
        try:
            with open(manager_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if 'MANAGER_VERSION' in line and '=' in line:
                        # Extract version from line like:  MANAGER_VERSION = "2.4.0"
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            ver = parts[1].strip().strip('"').strip("'")
                            diag['manager_version'] = ver
                        break
        except Exception:
            diag['manager_version'] = 'unknown'
    else:
        diag['manager_version'] = 'not installed'

    # --- 8. aegis_manager.log info ---
    manager_log = os.path.join(app_dir, 'aegis_manager.log')
    if os.path.exists(manager_log):
        try:
            stat = os.stat(manager_log)
            diag['manager_log'] = {
                'exists': True,
                'size_kb': round(stat.st_size / 1024, 1),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception:
            diag['manager_log'] = {'exists': True}
    else:
        diag['manager_log'] = {'exists': False}

    return diag


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
        to_email = data.get('to_email', '') or 'nicholas.georgeson@gmail.com'
        # v6.2.7: Frontend sends console logs, dashboard errors, SP state, DOM state
        frontend_diagnostics = data.get('frontend_diagnostics', None)

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

        # --- v6.2.10: Collect SharePoint/Auth/Scan diagnostic data ---
        sp_diag = {}
        try:
            # Auth service state
            try:
                from auth_service import AEGISAuthService
                auth_svc = AEGISAuthService()
                sp_diag['auth_service'] = auth_svc.get_auth_summary()
            except Exception as auth_e:
                sp_diag['auth_service'] = {'error': str(auth_e)}

            # SharePoint connector availability
            try:
                from sharepoint_connector import (
                    HEADLESS_SP_AVAILABLE, MSAL_AVAILABLE,
                    SSPI_PREEMPTIVE_AVAILABLE
                )
                sp_diag['sp_connector'] = {
                    'headless_available': HEADLESS_SP_AVAILABLE,
                    'msal_available': MSAL_AVAILABLE,
                    'sspi_preemptive_available': SSPI_PREEMPTIVE_AVAILABLE,
                }
            except Exception as sp_e:
                sp_diag['sp_connector'] = {'error': str(sp_e)}

            # Active scan states (batch + folder + SP)
            try:
                from routes.review_routes import (
                    _batch_scan_state, _folder_scan_state,
                    _batch_scan_state_lock, _folder_scan_state_lock
                )
                scan_states = {}
                with _batch_scan_state_lock:
                    for scan_id, state in _batch_scan_state.items():
                        scan_states[f'batch_{scan_id}'] = {
                            'phase': state.get('phase'),
                            'total': state.get('total'),
                            'processed': state.get('processed'),
                            'errors': state.get('errors'),
                            'current_file': state.get('current_file'),
                            'elapsed': state.get('elapsed_seconds'),
                            'started_at': state.get('started_at'),
                        }
                # Folder scan states (separate dict, separate lock)
                with _folder_scan_state_lock:
                    for scan_id, state in _folder_scan_state.items():
                        scan_states[f'folder_{scan_id}'] = {
                            'phase': state.get('phase'),
                            'total': state.get('total'),
                            'processed': state.get('processed'),
                            'errors': state.get('errors'),
                            'current_file': state.get('current_file'),
                            'started_at': state.get('started_at'),
                        }
                sp_diag['active_scans'] = scan_states if scan_states else 'none'
            except Exception as scan_e:
                sp_diag['active_scans'] = {'error': str(scan_e)}

            # Playwright/headless availability
            try:
                import subprocess as sp_sub
                r = sp_sub.run(
                    [sys.executable, '-c',
                     'from playwright.sync_api import sync_playwright; '
                     'p = sync_playwright().start(); '
                     'print(p.chromium.executable_path); p.stop()'],
                    capture_output=True, text=True, timeout=10
                )
                sp_diag['playwright'] = {
                    'available': r.returncode == 0,
                    'browser_path': r.stdout.strip()[:200] if r.returncode == 0 else None,
                    'error': r.stderr.strip()[:200] if r.returncode != 0 else None,
                }
            except Exception as pw_e:
                sp_diag['playwright'] = {'available': False, 'error': str(pw_e)}

            # truststore state
            try:
                import truststore
                sp_diag['truststore'] = {'available': True, 'file': getattr(truststore, '__file__', 'unknown')}
            except ImportError:
                sp_diag['truststore'] = {'available': False}

            # Log file listing with sizes
            try:
                log_dir = config.log_dir
                if log_dir.exists():
                    log_files = {}
                    for lf in sorted(log_dir.glob('*.log')):
                        log_files[lf.name] = {
                            'size_kb': round(lf.stat().st_size / 1024, 1),
                            'modified': datetime.fromtimestamp(lf.stat().st_mtime).isoformat()
                        }
                    sp_diag['log_files'] = log_files
            except Exception:
                pass

            export_data['sharepoint_diagnostics'] = sp_diag
        except Exception as diag_e:
            export_data['sharepoint_diagnostics'] = {'error': str(diag_e)}

        # --- v6.7.0: Collect Manager-level diagnostics ---
        try:
            manager_diag = _collect_manager_diagnostics()
            export_data['manager_diagnostics'] = manager_diag
        except Exception as mgr_e:
            logger.warning(f'Could not collect manager diagnostics: {mgr_e}')
            export_data['manager_diagnostics'] = {'error': str(mgr_e)}
            manager_diag = {}

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

        # Manager-level diagnostics (v6.7.0)
        if manager_diag:
            body_lines.append('MANAGER-LEVEL DIAGNOSTICS')
            body_lines.append('=' * 50)

            # Manager version
            mgr_ver = manager_diag.get('manager_version', 'unknown')
            body_lines.append(f'  Manager Version: {mgr_ver}')

            # Python
            py_info = manager_diag.get('python', {})
            if py_info:
                py_ver = py_info.get('version', '').split()[0] if py_info.get('version') else '?'
                py_exe = py_info.get('executable', '?')
                body_lines.append(f'  Python: {py_ver} ({py_exe})')

            # Disk space
            disk = manager_diag.get('disk_space', {})
            if disk and 'error' not in disk:
                body_lines.append(f"  Disk: {disk.get('free_gb', '?')} GB free / {disk.get('total_gb', '?')} GB total")

            # Server info
            srv = manager_diag.get('server', {})
            if srv:
                uptime = srv.get('uptime', 'unknown')
                body_lines.append(f"  Server PID: {srv.get('pid', '?')}, Uptime: {uptime}")

            body_lines.append('')

            # Package health (critical)
            pkg_h = manager_diag.get('package_health', {})
            if pkg_h:
                body_lines.append('  Package Health (Critical):')
                # Build compact 3-per-line display
                items = []
                for label, info in pkg_h.items():
                    if info.get('status') == 'ok':
                        items.append(f"\u2713 {label} {info.get('version', '')}")
                    elif info.get('status') == 'fail':
                        err_short = info.get('error', 'ImportError')
                        # Extract just the error type
                        if 'Error' in err_short:
                            err_short = err_short.split('Error')[0] + 'Error'
                        items.append(f"\u2717 {label} ({err_short})")
                    elif info.get('status') == 'timeout':
                        items.append(f"\u2717 {label} (timeout)")
                    else:
                        items.append(f"? {label}")
                # Print items 3 per line
                for i in range(0, len(items), 3):
                    chunk = items[i:i + 3]
                    body_lines.append('    ' + '  '.join(chunk))
                body_lines.append('')

            # Torch wheel status
            wheels = manager_diag.get('wheels', {})
            if wheels:
                torch_found = wheels.get('torch_wheel_found', False)
                torch_status = '\u2713 FOUND' if torch_found else '\u2717 NOT FOUND'
                body_lines.append(f'  Torch Wheel: {torch_status}')
                total_whl = wheels.get('total_wheels', 0)
                dirs_info = wheels.get('directories', {})
                dir_parts = []
                for dpath, dinfo in dirs_info.items():
                    if isinstance(dinfo, dict) and dinfo.get('count', 0) > 0:
                        dir_name = os.path.basename(dpath) or dpath
                        dir_parts.append(f"{dinfo['count']} files in {dir_name}")
                if dir_parts:
                    body_lines.append(f"  Wheels: {', '.join(dir_parts)}")
                else:
                    body_lines.append(f'  Wheels: {total_whl} total')

            # Manager log info
            mgr_log = manager_diag.get('manager_log', {})
            if mgr_log.get('exists'):
                body_lines.append(f"  Manager log: {mgr_log.get('size_kb', '?')} KB, modified {mgr_log.get('modified', '?')}")
            else:
                body_lines.append('  Manager log: not found')

            body_lines.append('')

        # SharePoint / Auth diagnostics (v6.2.10)
        if sp_diag:
            body_lines.append('SHAREPOINT / AUTH DIAGNOSTICS')
            body_lines.append('=' * 50)

            auth_info = sp_diag.get('auth_service', {})
            if isinstance(auth_info, dict) and 'error' not in auth_info:
                body_lines.append(f"  Windows SSO: {auth_info.get('windows_auth', 'unknown')}")
                body_lines.append(f"  Auth method: {auth_info.get('auth_method', 'unknown')}")
                body_lines.append(f"  MSAL OAuth: {auth_info.get('msal_available', 'unknown')}")
                body_lines.append(f"  Truststore: {auth_info.get('truststore', 'unknown')}")
            elif isinstance(auth_info, dict):
                body_lines.append(f"  Auth service error: {auth_info.get('error', 'unknown')}")

            sp_conn = sp_diag.get('sp_connector', {})
            if isinstance(sp_conn, dict) and 'error' not in sp_conn:
                body_lines.append(f"  Headless SP: {sp_conn.get('headless_available', 'unknown')}")
                body_lines.append(f"  SSPI preemptive: {sp_conn.get('sspi_preemptive_available', 'unknown')}")
                body_lines.append(f"  MSAL: {sp_conn.get('msal_available', 'unknown')}")
            elif isinstance(sp_conn, dict):
                body_lines.append(f"  SP connector error: {sp_conn.get('error', 'unknown')}")

            pw = sp_diag.get('playwright', {})
            if isinstance(pw, dict):
                body_lines.append(f"  Playwright available: {pw.get('available', False)}")
                if pw.get('browser_path'):
                    body_lines.append(f"  Browser: {pw['browser_path'][:100]}")
                if pw.get('error'):
                    body_lines.append(f"  Playwright error: {pw['error'][:150]}")

            ts = sp_diag.get('truststore', {})
            if isinstance(ts, dict):
                body_lines.append(f"  truststore installed: {ts.get('available', False)}")

            scans = sp_diag.get('active_scans', 'none')
            if isinstance(scans, dict):
                for sid, sinfo in scans.items():
                    body_lines.append(f"  Scan {sid}: phase={sinfo.get('phase')}, "
                                      f"{sinfo.get('processed', 0)}/{sinfo.get('total', 0)} files, "
                                      f"errors={sinfo.get('errors', 0)}")
            else:
                body_lines.append(f"  Active scans: {scans}")

            log_files = sp_diag.get('log_files', {})
            if log_files:
                body_lines.append('  Log files:')
                for name, info in log_files.items():
                    body_lines.append(f"    {name}: {info.get('size_kb', 0)} KB, modified {info.get('modified', '?')}")

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

        # v6.2.8: Frontend diagnostic sections from ConsoleCapture + dashboard state
        if frontend_diagnostics and isinstance(frontend_diagnostics, dict):
            # Dashboard error (critical for debugging invisible dashboard issues)
            dash_err = frontend_diagnostics.get('dashboardError')
            if dash_err:
                body_lines.append('*** DASHBOARD ERROR ***')
                body_lines.append('=' * 50)
                if isinstance(dash_err, dict):
                    body_lines.append(f"  Error: {dash_err.get('error', 'unknown')}")
                    body_lines.append(f"  Phase: {dash_err.get('phase', 'unknown')}")
                    body_lines.append(f"  Time: {dash_err.get('timestamp', 'unknown')}")
                    if dash_err.get('stack'):
                        body_lines.append(f"  Stack: {str(dash_err['stack'])[:500]}")
                else:
                    body_lines.append(f"  {str(dash_err)[:500]}")
                body_lines.append('')

            # SP Scan state
            sp_state = frontend_diagnostics.get('spScanState')
            if sp_state and isinstance(sp_state, dict):
                body_lines.append('SP SCAN STATE')
                body_lines.append('-' * 30)
                buttons = sp_state.get('buttons', {})
                if buttons:
                    for btn_name, btn_info in buttons.items():
                        if isinstance(btn_info, dict):
                            body_lines.append(f"  {btn_name}: disabled={btn_info.get('disabled')}, text={btn_info.get('text', '?')[:50]}")
                        else:
                            body_lines.append(f"  {btn_name}: {btn_info}")
                fs = sp_state.get('fileSelector', {})
                if fs:
                    body_lines.append(f"  File selector visible: {fs.get('visible')}, count: {fs.get('selectedCount')}")
                bm = sp_state.get('batchModal', {})
                if bm:
                    body_lines.append(f"  Batch modal display: {bm.get('display')}, class: {bm.get('classList', '')[:80]}")
                body_lines.append('')

            # DOM state for dashboard elements
            dom_state = frontend_diagnostics.get('domState')
            if dom_state and isinstance(dom_state, dict):
                body_lines.append('DASHBOARD DOM STATE')
                body_lines.append('-' * 30)
                bp = dom_state.get('batchProgress', {})
                if bp:
                    body_lines.append(f"  #batch-progress exists: {bp.get('exists')}")
                    if bp.get('computedStyles'):
                        cs = bp['computedStyles']
                        body_lines.append(f"  display: {cs.get('display')}")
                        body_lines.append(f"  visibility: {cs.get('visibility')}")
                        body_lines.append(f"  opacity: {cs.get('opacity')}")
                        body_lines.append(f"  height: {cs.get('height')}")
                        body_lines.append(f"  z-index: {cs.get('zIndex')}")
                        body_lines.append(f"  position: {cs.get('position')}")
                        body_lines.append(f"  overflow: {cs.get('overflow')}")
                css = dom_state.get('cssLoaded', {})
                if css:
                    body_lines.append(f"  batch-progress-dashboard.css loaded: {css.get('batchProgressDashboard')}")
                vis = dom_state.get('sectionVisibility', {})
                if vis:
                    body_lines.append(f"  Visible sections: {', '.join(k for k, v in vis.items() if v) or 'none'}")
                modals = dom_state.get('activeModals', [])
                if modals:
                    body_lines.append(f"  Active modals: {', '.join(str(m) for m in modals[:5])}")
                body_lines.append('')

            # Console log summary
            console_logs = frontend_diagnostics.get('consoleLogs')
            if console_logs and isinstance(console_logs, dict):
                body_lines.append('CONSOLE LOG SUMMARY')
                body_lines.append('-' * 30)
                body_lines.append(f"  Total captured: {console_logs.get('total', 0)}")
                stats = console_logs.get('stats', {})
                if stats.get('byLevel'):
                    levels = stats['byLevel']
                    body_lines.append(f"  By level: {', '.join(f'{k}={v}' for k, v in levels.items())}")

                # SP-specific logs (most important for debugging SP dashboard issues)
                sp_logs = console_logs.get('spLogs', [])
                if sp_logs:
                    body_lines.append(f"  SP-related logs ({len(sp_logs)}):")
                    for sp_log in sp_logs[-20:]:  # Last 20 SP logs
                        ts = sp_log.get('timestamp', '?')
                        if 'T' in ts:
                            ts = ts.split('T')[1][:8]  # Just time portion
                        body_lines.append(f"    [{ts}] {sp_log.get('level', '?')}: {str(sp_log.get('message', ''))[:120]}")
                    if len(sp_logs) > 20:
                        body_lines.append(f"    ... and {len(sp_logs) - 20} more SP logs in console_logs.json")

                # Console errors
                errors = console_logs.get('errors', [])
                if errors:
                    body_lines.append(f"  Console errors ({len(errors)}):")
                    for err in errors[-10:]:  # Last 10 errors
                        ts = err.get('timestamp', '?')
                        if 'T' in ts:
                            ts = ts.split('T')[1][:8]
                        body_lines.append(f"    [{ts}] {str(err.get('message', ''))[:150]}")
                    if len(errors) > 10:
                        body_lines.append(f"    ... and {len(errors) - 10} more errors in console_logs.json")
                body_lines.append('')
                body_lines.append('  >> Full console logs attached as console_logs.json')
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

        # Attachment 4: Frontend console logs + dashboard diagnostics (v6.2.8)
        if frontend_diagnostics and isinstance(frontend_diagnostics, dict):
            try:
                fe_json = json_mod.dumps(frontend_diagnostics, indent=2, default=str)
                fe_bytes = fe_json.encode('utf-8')
                # Cap at 3MB to prevent huge email
                if len(fe_bytes) > 3 * 1024 * 1024:
                    # Trim console log entries to fit
                    trimmed = dict(frontend_diagnostics)
                    if 'consoleLogs' in trimmed and isinstance(trimmed['consoleLogs'], dict):
                        entries = trimmed['consoleLogs'].get('entries', [])
                        if len(entries) > 50:
                            trimmed['consoleLogs']['entries'] = entries[-50:]
                            trimmed['consoleLogs']['_trimmed'] = True
                            trimmed['consoleLogs']['_original_count'] = len(entries)
                    fe_json = json_mod.dumps(trimmed, indent=2, default=str)
                    fe_bytes = fe_json.encode('utf-8')
                fe_attachment = MIMEBase('application', 'json')
                fe_attachment.set_payload(fe_bytes)
                encoders.encode_base64(fe_attachment)
                fe_attachment.add_header('Content-Disposition', 'attachment', filename='console_logs.json')
                msg.attach(fe_attachment)
            except Exception as fe_err:
                logger.warning(f'Could not attach console_logs.json: {fe_err}')

        # Attachment 5: aegis_manager.log (v6.7.0 — in project root, not log_dir)
        try:
            _mgr_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mgr_log_path = Path(os.path.join(_mgr_app_dir, 'aegis_manager.log'))
            if mgr_log_path.exists() and mgr_log_path.stat().st_size > 0:
                mgr_log_content = mgr_log_path.read_bytes()
                # Cap at 3MB
                if len(mgr_log_content) > 3 * 1024 * 1024:
                    mgr_log_content = mgr_log_content[-3 * 1024 * 1024:]
                mgr_att = MIMEBase('text', 'plain')
                mgr_att.set_payload(mgr_log_content)
                encoders.encode_base64(mgr_att)
                mgr_att.add_header('Content-Disposition', 'attachment', filename='aegis_manager.log')
                msg.attach(mgr_att)
        except Exception:
            pass

        # --- Try Outlook COM auto-send first (Windows), then .eml fallback ---
        import subprocess
        import tempfile

        eml_content = msg.as_string()
        eml_filename = f'aegis_diagnostic_email_{timestamp}.eml'

        # Save to a temp directory (persists until manually cleaned or reboot)
        eml_dir = Path(tempfile.gettempdir()) / 'aegis_emails'
        eml_dir.mkdir(exist_ok=True)
        eml_path = eml_dir / eml_filename
        eml_path.write_text(eml_content, encoding='utf-8')

        sent_via_com = False
        com_error = None

        # Strategy 1: Outlook COM auto-send (Windows only)
        if platform.system() == 'Windows':
            try:
                import win32com.client
                logger.info(f'[DiagEmail] Attempting Outlook COM auto-send to {to_email}')
                outlook = win32com.client.Dispatch("Outlook.Application")
                mail = outlook.CreateItem(0)  # 0 = olMailItem
                mail.To = to_email
                mail.Subject = subject
                mail.Body = body_text

                # Save attachments as temp files for Outlook COM
                att_paths = []

                # Attachment 1: Diagnostic JSON
                diag_path = eml_dir / diag_filename
                diag_path.write_text(diag_json, encoding='utf-8')
                att_paths.append(str(diag_path))

                # Attachment 2: aegis.log
                if log_file.exists() and log_file.stat().st_size > 0:
                    try:
                        log_content = log_file.read_bytes()
                        if len(log_content) > 5 * 1024 * 1024:
                            log_content = log_content[-5 * 1024 * 1024:]
                        att_log_path = eml_dir / 'aegis.log'
                        att_log_path.write_bytes(log_content)
                        att_paths.append(str(att_log_path))
                    except Exception:
                        pass

                # Attachment 3: Other log files
                try:
                    total_att = 0
                    max_att = 10 * 1024 * 1024
                    other_logs = sorted(
                        [f for f in config.log_dir.glob('*.log')
                         if f.name != 'aegis.log' and f.stat().st_size > 1024],
                        key=lambda f: f.stat().st_size, reverse=True
                    )
                    for other_log in other_logs:
                        if total_att >= max_att:
                            break
                        try:
                            cb = other_log.read_bytes()
                            if len(cb) > 2 * 1024 * 1024:
                                cb = cb[-2 * 1024 * 1024:]
                            total_att += len(cb)
                            att_other_path = eml_dir / other_log.name
                            att_other_path.write_bytes(cb)
                            att_paths.append(str(att_other_path))
                        except Exception:
                            pass
                except Exception:
                    pass

                # Attachment 4: Frontend console logs
                if frontend_diagnostics and isinstance(frontend_diagnostics, dict):
                    try:
                        fe_json_str = json_mod.dumps(frontend_diagnostics, indent=2, default=str)
                        fe_bytes = fe_json_str.encode('utf-8')
                        if len(fe_bytes) > 3 * 1024 * 1024:
                            trimmed = dict(frontend_diagnostics)
                            if 'consoleLogs' in trimmed and isinstance(trimmed['consoleLogs'], dict):
                                entries = trimmed['consoleLogs'].get('entries', [])
                                if len(entries) > 50:
                                    trimmed['consoleLogs']['entries'] = entries[-50:]
                                    trimmed['consoleLogs']['_trimmed'] = True
                            fe_json_str = json_mod.dumps(trimmed, indent=2, default=str)
                        att_fe_path = eml_dir / 'console_logs.json'
                        att_fe_path.write_text(fe_json_str, encoding='utf-8')
                        att_paths.append(str(att_fe_path))
                    except Exception:
                        pass

                # Attachment 5: aegis_manager.log (v6.7.0)
                try:
                    _mgr_app_dir2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    mgr_log_p = Path(os.path.join(_mgr_app_dir2, 'aegis_manager.log'))
                    if mgr_log_p.exists() and mgr_log_p.stat().st_size > 0:
                        mgr_content = mgr_log_p.read_bytes()
                        if len(mgr_content) > 3 * 1024 * 1024:
                            mgr_content = mgr_content[-3 * 1024 * 1024:]
                        att_mgr_path = eml_dir / 'aegis_manager.log'
                        att_mgr_path.write_bytes(mgr_content)
                        att_paths.append(str(att_mgr_path))
                except Exception:
                    pass

                # Add all attachment files to the Outlook mail item
                for att_p in att_paths:
                    try:
                        mail.Attachments.Add(att_p)
                    except Exception as att_err:
                        logger.warning(f'[DiagEmail] Could not attach {att_p}: {att_err}')

                # Auto-send (try Send first, fall back to Display)
                try:
                    mail.Send()
                    sent_via_com = True
                    logger.info(f'[DiagEmail] ✓ Sent via Outlook COM to {to_email} with {len(att_paths)} attachments')
                except Exception as send_err:
                    logger.warning(f'[DiagEmail] mail.Send() blocked: {send_err}, trying Display()...')
                    try:
                        mail.Display()
                        sent_via_com = True  # Display counts as success — user sees pre-filled email
                        logger.info(f'[DiagEmail] ✓ Opened in Outlook via Display() — user clicks Send')
                    except Exception as disp_err:
                        logger.warning(f'[DiagEmail] mail.Display() also failed: {disp_err}')

            except ImportError:
                com_error = 'win32com not installed'
                logger.info(f'[DiagEmail] win32com not available, falling back to .eml')
            except Exception as com_err:
                com_error = str(com_err)
                logger.warning(f'[DiagEmail] Outlook COM failed: {com_err}, falling back to .eml')

        # Strategy 2: .eml file opened in default mail client (fallback)
        opened = False
        if not sent_via_com:
            try:
                if platform.system() == 'Darwin':
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
            'sent': sent_via_com,
            'opened': opened,
            'to_email': to_email,
            'filename': eml_filename,
            'path': str(eml_path),
            'attachments': len(msg.get_payload()) - 1,
            'com_error': com_error
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


@core_bp.route('/api/diagnostics/beacon', methods=['POST'])
def diagnostics_beacon():
    """
    Lightweight diagnostic beacon — logs scan steps at INFO level so they
    appear in app.log. Used by frontend to confirm which steps actually execute.
    No CSRF required. Returns 200 immediately.
    """
    try:
        data = request.get_json(silent=True) or {}
        step = data.get('step', 'unknown')
        scan_id = data.get('scan_id', '?')
        detail = data.get('detail', '')
        error = data.get('error', '')
        if error:
            logger.warning(f'[BEACON] scan={scan_id} step={step} ERROR: {error} {detail}')
        else:
            logger.info(f'[BEACON] scan={scan_id} step={step} {detail}')
    except Exception:
        pass
    return jsonify({'ok': True})


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


# ─────────────────────────────────────────────────────────────────
# Package Repair — v6.7.0
# Background thread repairs broken packages via pip reinstall
# Uses ordered sequential installs + subprocess verification
# to prevent the "pass then break" cycle (Lesson 188)
# ─────────────────────────────────────────────────────────────────
import threading
import subprocess
import sys
import time
import uuid
import glob

_repair_state = {}  # {repair_id: {phase, progress, message, packages, started_at, ...}}
_repair_state_lock = threading.Lock()

# Packages that are known incompatible — skip them entirely
INCOMPATIBLE_PACKAGES = {
    'coreferee': 'Incompatible with spaCy 3.6+ (pattern-based fallback active)',
    'negspacy': 'Incompatible with spaCy 3.6+ (regex fallback active)',
    'passivepy': 'No pre-built wheel available (rule-based fallback active)',
}

# Install critical packages in dependency order so downstream
# packages find their deps already available
CRITICAL_INSTALL_ORDER = [
    ('numpy', 'numpy'),
    ('pandas', 'pandas'),
    ('scipy', 'scipy'),
    ('sklearn', 'scikit-learn'),
    ('nltk', 'nltk'),
    ('spacy', 'spacy'),
]


def _find_python_exe():
    """Find the correct Python executable (embedded or system)."""
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Embedded Python (Windows OneClick installer)
    embedded = os.path.join(app_dir, 'python', 'python.exe')
    if os.path.exists(embedded):
        return embedded
    return sys.executable


def _find_wheels_dirs():
    """Find all wheels directories."""
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs = []
    for candidate in ['wheels', os.path.join('packaging', 'wheels')]:
        full = os.path.join(app_dir, candidate)
        if os.path.isdir(full):
            dirs.append(full)
    return dirs


def _pip_install(packages, wheels_dirs, force=False, timeout=300):
    """Install packages via pip. Returns (success, output)."""
    python = _find_python_exe()
    cmd = [python, '-m', 'pip', 'install']
    if force:
        cmd.append('--force-reinstall')
    if wheels_dirs:
        cmd.append('--no-index')
        for d in wheels_dirs:
            cmd.extend(['--find-links', d])
    cmd.append('--no-warn-script-location')
    if isinstance(packages, str):
        packages = [packages]
    cmd.extend(packages)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, 'Installation timed out'
    except Exception as e:
        return False, str(e)


def _pip_install_online(packages, force=False, timeout=300):
    """Fallback: install packages from PyPI (online)."""
    python = _find_python_exe()
    cmd = [python, '-m', 'pip', 'install']
    if force:
        cmd.append('--force-reinstall')
    cmd.append('--no-warn-script-location')
    if isinstance(packages, str):
        packages = [packages]
    cmd.extend(packages)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, 'Installation timed out'
    except Exception as e:
        return False, str(e)


def _check_import(module_name):
    """Check if a module can be imported in a subprocess (clean slate).

    Always uses subprocess to avoid false passes from in-process
    importlib (Lesson 188: packages can appear OK in-process but
    fail in a clean interpreter).
    """
    python = _find_python_exe()
    try:
        result = subprocess.run(
            [python, '-c', f'import {module_name}; print("OK")'],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0 and 'OK' in result.stdout
    except Exception:
        return False


def _check_wheel_exists(pip_name, wheels_dirs):
    """Check if a wheel file exists for the given package in any wheels dir."""
    # Normalize pip name for wheel file matching (PEP 427: - and _ are equivalent)
    normalized = pip_name.lower().replace('-', '_').replace('.', '_')
    for wd in wheels_dirs:
        for whl in glob.glob(os.path.join(wd, '*.whl')):
            whl_base = os.path.basename(whl).lower().replace('-', '_')
            if whl_base.startswith(normalized):
                return True
    return False


def _ensure_torch_wheel():
    """Check if torch wheel exists. Try to reassemble from split parts if needed.

    Returns the wheel path if found/reassembled, None otherwise.
    """
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wheels_dirs = _find_wheels_dirs()

    # Check existing wheels
    for wd in wheels_dirs:
        for whl in glob.glob(os.path.join(wd, 'torch-*.whl')):
            return whl

    # Check split parts
    split_dir = os.path.join(app_dir, 'packaging', 'wheels', 'torch_split')
    if os.path.isdir(split_dir):
        parts = sorted(glob.glob(os.path.join(split_dir, 'torch_part_*')))
        if len(parts) >= 3:
            dest_dir = os.path.join(app_dir, 'packaging', 'wheels')
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, 'torch-2.10.0+cpu-cp310-cp310-win_amd64.whl')
            try:
                with open(dest, 'wb') as out:
                    for part in parts:
                        with open(part, 'rb') as inp:
                            out.write(inp.read())
                return dest
            except Exception:
                pass

    return None


def _run_repair(repair_id):
    """Background thread: repair broken packages.

    v6.7.0: Uses ordered sequential installs + subprocess verification
    to prevent the "pass then break" cycle (Lesson 188).
    """
    started_at = time.time()

    def _update(phase, progress, message, **extra):
        with _repair_state_lock:
            state = _repair_state.get(repair_id, {})
            state.update({
                'phase': phase,
                'progress': progress,
                'message': message,
                'elapsed_seconds': round(time.time() - started_at, 1),
            })
            state.update(extra)
            _repair_state[repair_id] = state

    try:
        _update('checking', 5, 'Running health check (subprocess)...')

        # 1. Identify broken packages using subprocess (not importlib)
        #    Subprocess catches real failures that in-process testing misses
        packages_to_check = [
            ('flask', 'Flask', False),
            ('werkzeug', 'Werkzeug', False),
            ('waitress', 'Waitress', False),
            ('docx', 'python-docx', False),
            ('mammoth', 'mammoth', False),
            ('openpyxl', 'openpyxl', False),
            ('reportlab', 'reportlab', False),
            ('nltk', 'NLTK', False),
            ('spacy', 'spaCy', False),
            ('numpy', 'NumPy', False),
            ('pandas', 'pandas', False),
            ('scipy', 'SciPy', False),
            ('sklearn', 'scikit-learn', True),
            ('torch', 'PyTorch', True),
            ('requests', 'requests', False),
            ('lxml', 'lxml', False),
            ('yaml', 'PyYAML', False),
            ('PIL', 'Pillow', False),
            ('textstat', 'textstat', True),
            ('proselint', 'proselint', True),
            ('symspellpy', 'symspellpy', True),
            ('chardet', 'chardet', False),
            ('bs4', 'BeautifulSoup4', False),
            ('pymupdf4llm', 'pymupdf4llm', True),
        ]

        broken = []
        for mod_name, display_name, is_optional in packages_to_check:
            # Skip known incompatible packages
            pip_name_map = {
                'docx': 'python-docx', 'sklearn': 'scikit-learn',
                'yaml': 'PyYAML', 'PIL': 'Pillow',
                'bs4': 'beautifulsoup4', 'cv2': 'opencv-python',
            }
            pip_name = pip_name_map.get(mod_name, display_name.lower().replace(' ', '-'))
            if pip_name in INCOMPATIBLE_PACKAGES:
                continue

            # Use subprocess for ALL imports — catches real failures
            if not _check_import(mod_name):
                broken.append((mod_name, display_name, is_optional))

        if not broken:
            _update('complete', 100, 'All packages are healthy — no repair needed.',
                    repaired=[], failed=[], already_ok=True)
            return

        _update('checking', 10, f'Found {len(broken)} broken package(s). Starting repair...',
                broken_count=len(broken), broken_names=[b[1] for b in broken])

        wheels_dirs = _find_wheels_dirs()
        repaired = []
        failed = []

        # 2. Fix setuptools first (Lesson 70)
        _update('repairing', 15, 'Checking setuptools version...')
        try:
            import setuptools
            sv = getattr(setuptools, '__version__', '0')
            major = int(sv.split('.')[0]) if sv else 0
            if major >= 81:
                _update('repairing', 18, 'Downgrading setuptools (v82 broke pkg_resources)...')
                ok, _ = _pip_install(['setuptools<81'], wheels_dirs, force=True, timeout=120)
                if not ok:
                    ok, _ = _pip_install_online(['setuptools<81'], force=True, timeout=120)
        except Exception:
            pass

        # 3. Install packages in dependency order (Lesson 188)
        #    Foundation packages first, then dependents
        pip_name_map = {
            'docx': 'python-docx', 'sklearn': 'scikit-learn',
            'yaml': 'PyYAML', 'PIL': 'Pillow',
            'bs4': 'beautifulsoup4', 'cv2': 'opencv-python',
        }
        broken_mods = {b[0] for b in broken}  # set of broken module names

        # Phase 3a: Install ordered critical packages first
        ordered_installed = set()
        for order_idx, (import_name, pip_name) in enumerate(CRITICAL_INSTALL_ORDER):
            if import_name not in broken_mods:
                continue

            display = next((b[1] for b in broken if b[0] == import_name), pip_name)
            pct = 20 + int(30 * (order_idx / len(CRITICAL_INSTALL_ORDER)))
            _update('repairing', pct, f'Installing {display} (ordered {order_idx+1}/{len(CRITICAL_INSTALL_ORDER)})...',
                    current_package=display, current_strategy='ordered install')

            # Check if torch — ensure wheel exists first
            if import_name == 'torch':
                torch_whl = _ensure_torch_wheel()
                if not torch_whl:
                    _update('repairing', pct, f'No torch wheel available, skipping...',
                            current_package=display, current_strategy='skipped (no wheel)')
                    continue

            # Check wheel existence for packages without wheels
            if not _check_wheel_exists(pip_name, wheels_dirs):
                if pip_name in INCOMPATIBLE_PACKAGES:
                    ordered_installed.add(import_name)
                    continue

            # Strategy 1: offline install
            ok, output = _pip_install([pip_name], wheels_dirs, force=True, timeout=600)

            # Strategy 2: online fallback
            if not ok:
                ok, output = _pip_install_online([pip_name], force=True, timeout=600)

            # Verify with subprocess
            if ok and _check_import(import_name):
                repaired.append(display)
                ordered_installed.add(import_name)
            else:
                # One retry with force
                ok2, _ = _pip_install([pip_name], wheels_dirs, force=True, timeout=600)
                if ok2 and _check_import(import_name):
                    repaired.append(display)
                    ordered_installed.add(import_name)
                else:
                    failed.append(display)
                    ordered_installed.add(import_name)  # Don't retry below

        # Phase 3b: Install remaining broken packages not in the ordered list
        remaining = [(m, d, o) for m, d, o in broken if m not in ordered_installed]
        total_remaining = len(remaining)
        for i, (mod_name, display_name, is_optional) in enumerate(remaining):
            pct = 55 + int(35 * (i / max(total_remaining, 1)))
            _update('repairing', pct, f'Repairing {display_name} ({i+1}/{total_remaining})...',
                    current_package=display_name)

            pip_name = pip_name_map.get(mod_name, display_name.lower().replace(' ', '-'))

            # Skip packages without wheels (prevents setuptools BUILD dep error)
            if pip_name in INCOMPATIBLE_PACKAGES:
                continue
            if is_optional and not _check_wheel_exists(pip_name, wheels_dirs):
                _update('repairing', pct, f'Skipping {display_name} (no wheel available)...',
                        current_package=display_name, current_strategy='skipped')
                continue

            # Strategy 1: offline install from wheels
            _update('repairing', pct, f'Repairing {display_name}...',
                    current_package=display_name, current_strategy='offline install')
            ok, output = _pip_install([pip_name], wheels_dirs, force=False, timeout=300)

            # Strategy 2: offline with force-reinstall
            if not ok:
                _update('repairing', pct, f'Force reinstalling {display_name}...',
                        current_package=display_name, current_strategy='force reinstall')
                ok, output = _pip_install([pip_name], wheels_dirs, force=True, timeout=300)

            # Strategy 3: online fallback
            if not ok:
                _update('repairing', pct, f'Trying online install for {display_name}...',
                        current_package=display_name, current_strategy='online fallback')
                ok, output = _pip_install_online([pip_name], force=False, timeout=300)

            # Verify import with subprocess
            if ok:
                if _check_import(mod_name):
                    repaired.append(display_name)
                else:
                    ok2, _ = _pip_install([pip_name], wheels_dirs, force=True, timeout=300)
                    if ok2 and _check_import(mod_name):
                        repaired.append(display_name)
                    else:
                        failed.append(display_name)
            else:
                failed.append(display_name)

        # 4. Summary
        if failed:
            msg = f'Repaired {len(repaired)} package(s). {len(failed)} still broken: {", ".join(failed)}'
            _update('complete', 100, msg, repaired=repaired, failed_packages=failed,
                    fixed=len(repaired), still_broken=len(failed), already_ok=False)
        else:
            msg = f'Successfully repaired {len(repaired)} package(s)!'
            _update('complete', 100, msg, repaired=repaired, failed_packages=failed,
                    fixed=len(repaired), still_broken=0, already_ok=False)

    except Exception as e:
        logger.exception(f'Repair thread error: {e}')
        _update('error', 0, f'Repair failed: {str(e)}')


@core_bp.route('/api/diagnostics/repair', methods=['POST'])
@handle_api_errors
def diagnostics_repair():
    """Start a background package repair. Returns repair_id for progress polling."""
    repair_id = uuid.uuid4().hex[:12]
    with _repair_state_lock:
        _repair_state[repair_id] = {
            'phase': 'starting',
            'progress': 0,
            'message': 'Initializing repair...',
            'started_at': time.time(),
            'elapsed_seconds': 0,
        }

    thread = threading.Thread(target=_run_repair, args=(repair_id,), daemon=True)
    thread.start()

    return jsonify({'success': True, 'data': {'repair_id': repair_id}})


@core_bp.route('/api/diagnostics/repair-progress/<repair_id>', methods=['GET'])
@handle_api_errors
def diagnostics_repair_progress(repair_id):
    """Poll repair progress."""
    with _repair_state_lock:
        state = _repair_state.get(repair_id)
    if not state:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Repair not found'}}), 404

    # Compute live elapsed
    started = state.get('started_at', time.time())
    state['elapsed_seconds'] = round(time.time() - started, 1)

    return jsonify({'success': True, 'data': state})


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
        root_allowed_files = {'logo.png', 'logo.svg', 'favicon.ico'}
        possible_paths = [
            config.base_dir / 'static' / 'images' / safe_name,
            config.base_dir / 'images' / safe_name,
        ]
        if safe_name in root_allowed_files:
            possible_paths.append(config.base_dir / safe_name)
        img_path = None
        for p in possible_paths:
            if p.exists():
                img_path = p
                break
        if img_path:
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
