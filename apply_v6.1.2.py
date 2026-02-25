#!/usr/bin/env python3
"""
AEGIS v6.1.1 → v6.1.2 Update Applier
=======================================
SharePoint Device Code Flow UI + URL Misroute Fix

This update addresses TWO SharePoint Connect & Scan issues:

1. URL MISROUTE FIX: When a SharePoint URL is pasted into the local folder
   scan field (top input), it previously showed "Folder not found" with the
   full URL as if it were a filesystem path. Now it detects URLs and shows
   a clear message directing users to the "Paste SharePoint link" field.

2. DEVICE CODE FLOW UI: When SharePoint Online requires browser-based OAuth
   (device code flow), the frontend now shows a styled authentication panel
   with the verification URL and code. Users can complete auth in their
   browser and click "I've Completed Authentication" to retry.

Changes:
- sharepoint_connector.py — get_pending_device_flow() + complete_device_flow()
- routes/review_routes.py — URL guard in folder_scan_start, device code in
  connect-and-scan error response, new device-code-complete endpoint
- static/js/app.js — Device code flow UI panel in Connect & Scan handler
- version.json / static/version.json — Version bump to 6.1.2
- static/js/help-docs.js — v6.1.2 changelog
- CLAUDE.md — Lesson 145

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.2.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan with a SharePoint URL
"""

import os
import sys
import shutil
import ssl
import subprocess
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — device code flow functions',
    'routes/review_routes.py': 'Review routes — URL guard, device code response, completion endpoint',
    'static/js/app.js': 'Frontend — device code flow UI panel',
    'version.json': 'Version 6.1.2',
    'static/version.json': 'Version 6.1.2 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 145',
    'static/js/help-docs.js': 'Help docs with v6.1.2 changelog',
}


def create_ssl_context():
    """Create SSL context with fallback for certificate issues."""
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        ctx = ssl._create_unverified_context()
        return ctx


def download_file(url, dest_path, is_binary=False):
    """Download a file from URL to dest_path."""
    ctx = create_ssl_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.2'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f'  [ERROR] Download failed: {e}')
        # Try without SSL verification
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.2'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            print(f'  [ERROR] SSL fallback also failed: {e2}')
            return False


def find_aegis_python():
    """
    Find the correct Python executable for AEGIS.

    Priority:
    1. Embedded Python in python/ subdirectory (OneClick install)
    2. The Python that launched this script (sys.executable)
    """
    cwd = os.getcwd()

    # Check for embedded Python (OneClick installer layout)
    embedded_paths = [
        os.path.join(cwd, 'python', 'python.exe'),
        os.path.join(cwd, 'python', 'python3.exe'),
        os.path.join(cwd, '..', 'python', 'python.exe'),
    ]

    for p in embedded_paths:
        if os.path.isfile(p):
            abs_path = os.path.abspath(p)
            print(f'  [FOUND] Embedded Python: {abs_path}')
            return abs_path

    print(f'  [INFO] No embedded Python found — using: {sys.executable}')
    return sys.executable


def verify_import(python_exe, module_name, display_name):
    """Verify a module can be imported by the target Python."""
    try:
        result = subprocess.run(
            [python_exe, '-c', f'import {module_name}; print(getattr({module_name}, "__version__", "ok"))'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            ver = result.stdout.strip()
            print(f'  [OK] {display_name} {ver}')
            return True
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown error'
            print(f'  [FAIL] {display_name} — {err[:120]}')
            return False
    except subprocess.TimeoutExpired:
        print(f'  [FAIL] {display_name} — import timed out')
        return False
    except Exception as e:
        print(f'  [FAIL] {display_name} — {e}')
        return False


def verify_msal_gcc_high(python_exe):
    """
    Verify MSAL can create an app with instance_discovery=False.
    This is the EXACT operation needed for GCC High SharePoint.
    """
    test_code = """
import msal
try:
    app = msal.PublicClientApplication(
        'd3590ed6-52b3-4102-aeff-aad2292ab01c',
        authority='https://login.microsoftonline.us/organizations',
        instance_discovery=False,
        verify=False,
    )
    print('MSAL_GCC_HIGH_OK')
except TypeError as te:
    try:
        app = msal.PublicClientApplication(
            'd3590ed6-52b3-4102-aeff-aad2292ab01c',
            authority='https://login.microsoftonline.us/organizations',
        )
        print('MSAL_GCC_HIGH_OK_MINIMAL')
    except Exception as e2:
        print(f'MSAL_GCC_HIGH_FAIL: {e2}')
except Exception as e:
    print(f'MSAL_GCC_HIGH_FAIL: {e}')
"""
    try:
        result = subprocess.run(
            [python_exe, '-c', test_code],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if 'MSAL_GCC_HIGH_OK' in output:
            if 'MINIMAL' in output:
                print('  [OK] MSAL GCC High app creation works (minimal params — older MSAL)')
            else:
                print('  [OK] MSAL GCC High app creation works (instance_discovery=False, verify=False)')
            return True
        else:
            err = output or result.stderr.strip().split('\n')[-1]
            print(f'  [FAIL] MSAL GCC High: {err[:150]}')
            return False
    except subprocess.TimeoutExpired:
        print('  [FAIL] MSAL GCC High test timed out')
        return False
    except Exception as e:
        print(f'  [FAIL] MSAL GCC High test error: {e}')
        return False


def verify_device_code_functions(python_exe):
    """
    v6.1.2: Verify the new device code flow functions exist in sharepoint_connector.py
    """
    test_code = """
try:
    from sharepoint_connector import get_pending_device_flow, complete_device_flow
    print('DEVICE_CODE_FUNCS_OK')
except ImportError as ie:
    print(f'DEVICE_CODE_FUNCS_FAIL: {ie}')
except Exception as e:
    print(f'DEVICE_CODE_FUNCS_FAIL: {e}')
"""
    try:
        result = subprocess.run(
            [python_exe, '-c', test_code],
            capture_output=True, text=True, timeout=15,
            cwd=os.getcwd()
        )
        output = result.stdout.strip()
        if 'DEVICE_CODE_FUNCS_OK' in output:
            print('  [OK] Device code flow functions available (get_pending_device_flow, complete_device_flow)')
            return True
        else:
            err = output or result.stderr.strip().split('\n')[-1]
            print(f'  [FAIL] Device code functions: {err[:150]}')
            return False
    except subprocess.TimeoutExpired:
        print('  [FAIL] Device code function test timed out')
        return False
    except Exception as e:
        print(f'  [FAIL] Device code function test: {e}')
        return False


def verify_url_guard():
    """
    v6.1.2: Verify the URL detection guard exists in review_routes.py
    """
    routes_path = os.path.join('routes', 'review_routes.py')
    if not os.path.exists(routes_path):
        print('  [FAIL] routes/review_routes.py not found')
        return False
    try:
        with open(routes_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'sharepoint' in content and 'This looks like a SharePoint URL' in content:
            print('  [OK] URL misroute detection guard present in folder_scan_start')
            return True
        else:
            print('  [FAIL] URL misroute detection guard NOT found in review_routes.py')
            return False
    except Exception as e:
        print(f'  [FAIL] Could not verify URL guard: {e}')
        return False


def verify_device_code_endpoint():
    """
    v6.1.2: Verify the device code completion endpoint exists in review_routes.py
    """
    routes_path = os.path.join('routes', 'review_routes.py')
    if not os.path.exists(routes_path):
        print('  [FAIL] routes/review_routes.py not found')
        return False
    try:
        with open(routes_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'sharepoint-device-code-complete' in content and 'complete_device_flow' in content:
            print('  [OK] Device code completion endpoint present (/api/review/sharepoint-device-code-complete)')
            return True
        else:
            print('  [FAIL] Device code completion endpoint NOT found in review_routes.py')
            return False
    except Exception as e:
        print(f'  [FAIL] Could not verify device code endpoint: {e}')
        return False


def verify_frontend_device_code_ui():
    """
    v6.1.2: Verify the device code UI exists in app.js
    """
    app_js = os.path.join('static', 'js', 'app.js')
    if not os.path.exists(app_js):
        print('  [FAIL] static/js/app.js not found')
        return False
    try:
        with open(app_js, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'Authentication Required' in content and 'device_code' in content:
            print('  [OK] Device code flow UI panel present in app.js')
            return True
        else:
            print('  [FAIL] Device code flow UI NOT found in app.js')
            return False
    except Exception as e:
        print(f'  [FAIL] Could not verify frontend UI: {e}')
        return False


def verify_version():
    """Verify version.json shows 6.1.2"""
    try:
        import json
        with open('version.json', 'r') as f:
            v = json.load(f)
        ver = v.get('version', 'unknown')
        if ver == '6.1.2':
            print(f'  [OK] version.json: {ver}')
            return True
        else:
            print(f'  [WARN] version.json: {ver} (expected 6.1.2)')
            return False
    except Exception as e:
        print(f'  [FAIL] version.json: {e}')
        return False


def pip_install(python_exe, packages):
    """Install packages with offline-first, online fallback."""
    wheels_dirs = []
    for d in ['wheels', os.path.join('packaging', 'wheels')]:
        if os.path.isdir(d):
            wheels_dirs.append(d)

    for pkg in packages:
        # Try offline first
        if wheels_dirs:
            cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location']
            for wd in wheels_dirs:
                cmd.extend(['--no-index', '--find-links', wd])
            cmd.append(pkg)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f'    [OK] {pkg} (offline)')
                continue

        # Try online
        cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location', pkg]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f'    [OK] {pkg} (online)')
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            print(f'    [FAIL] {pkg} — {err[:100]}')


def main():
    print('=' * 65)
    print('  AEGIS v6.1.2 Update Applier')
    print('  SharePoint Device Code Flow UI + URL Misroute Fix')
    print('=' * 65)
    print()

    # Verify we're in the correct directory
    if not os.path.exists('app.py') or not os.path.exists('static'):
        print('[ERROR] This script must be run from the AEGIS installation directory.')
        print('        Expected to find app.py and static/ folder.')
        print(f'        Current directory: {os.getcwd()}')
        sys.exit(1)

    # Find the correct Python
    print('[STEP 0] Finding AEGIS Python...')
    python_exe = find_aegis_python()

    try:
        py_version = subprocess.run(
            [python_exe, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'],
            capture_output=True, text=True, timeout=10
        )
        if py_version.returncode == 0:
            print(f'  Python version: {py_version.stdout.strip()}')
    except Exception:
        pass
    print()

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.1.2_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[INFO] Backup directory: {backup_dir}')
    print()

    # Ensure directories exist
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('routes', exist_ok=True)

    # Download and apply files
    print('[STEP 1] Downloading updated source files...')
    success_count = 0
    fail_count = 0

    for rel_path, description in FILES.items():
        print(f'  Updating {rel_path} ({description})...')

        # Backup existing file
        if os.path.exists(rel_path):
            backup_path = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            backup_parent = os.path.dirname(backup_path)
            if backup_parent:
                os.makedirs(backup_parent, exist_ok=True)
            shutil.copy2(rel_path, backup_path)
            print(f'    Backed up to {backup_path}')

        # Download new version
        url = f'{RAW_BASE}/{rel_path}'
        if download_file(url, rel_path):
            print(f'    [OK] Updated')
            success_count += 1
        else:
            print(f'    [FAIL] Could not download')
            fail_count += 1

    print()

    # Verify auth dependencies
    print('[STEP 2] Verifying auth dependencies...')
    msal_ok = verify_import(python_exe, 'msal', 'MSAL (OAuth 2.0)')
    jwt_ok = verify_import(python_exe, 'jwt', 'PyJWT')
    if sys.platform == 'win32':
        sspi_ok = verify_import(python_exe, 'sspi', 'sspi (pywin32)')
        win32_ok = verify_import(python_exe, 'win32security', 'win32security (pywin32)')
    else:
        sspi_ok = win32_ok = None  # Not applicable on non-Windows
    print()

    # Install missing deps if needed
    missing = []
    if not msal_ok:
        missing.append('msal')
    if not jwt_ok:
        missing.append('PyJWT')
    if sys.platform == 'win32':
        if not sspi_ok or not win32_ok:
            missing.append('pywin32')

    if missing:
        print(f'[STEP 2b] Installing missing packages: {", ".join(missing)}')
        pip_install(python_exe, missing)
        print()
        # Re-verify
        if not msal_ok:
            msal_ok = verify_import(python_exe, 'msal', 'MSAL (re-check)')
        if not jwt_ok:
            jwt_ok = verify_import(python_exe, 'jwt', 'PyJWT (re-check)')
        print()

    # MSAL GCC High compatibility
    print('[STEP 3] Verifying MSAL GCC High compatibility...')
    if msal_ok:
        gcc_ok = verify_msal_gcc_high(python_exe)
    else:
        print('  [SKIP] MSAL not installed — cannot verify GCC High compatibility')
        gcc_ok = False
    print()

    # v6.1.2-specific verifications
    print('[STEP 4] Verifying v6.1.2 changes...')
    url_guard_ok = verify_url_guard()
    endpoint_ok = verify_device_code_endpoint()
    frontend_ok = verify_frontend_device_code_ui()
    dc_funcs_ok = verify_device_code_functions(python_exe) if msal_ok else False
    version_ok = verify_version()
    print()

    # ═══════════════════════════════════════════════════════════
    # COMPREHENSIVE SUMMARY
    # ═══════════════════════════════════════════════════════════
    print('=' * 65)
    print('  UPDATE SUMMARY')
    print('=' * 65)
    print()

    # File download results
    if fail_count == 0:
        print(f'  FILES:  {success_count}/{success_count} downloaded successfully ✓')
    else:
        print(f'  FILES:  {success_count} succeeded, {fail_count} FAILED ✗')
    print()

    # Auth stack
    print('  AUTH STACK:')
    print(f'    MSAL (OAuth 2.0):       {"✓ INSTALLED" if msal_ok else "✗ NOT INSTALLED"}')
    print(f'    PyJWT:                   {"✓ INSTALLED" if jwt_ok else "✗ NOT INSTALLED"}')
    if sys.platform == 'win32':
        print(f'    pywin32 (SSPI):          {"✓ INSTALLED" if sspi_ok else "✗ NOT INSTALLED"}')
    print(f'    MSAL GCC High:           {"✓ WORKING" if gcc_ok else "✗ NOT WORKING"}')
    print()

    # v6.1.2 features
    print('  v6.1.2 FEATURES:')
    print(f'    URL misroute guard:      {"✓ PRESENT" if url_guard_ok else "✗ MISSING"}')
    print(f'    Device code endpoint:    {"✓ PRESENT" if endpoint_ok else "✗ MISSING"}')
    print(f'    Device code UI:          {"✓ PRESENT" if frontend_ok else "✗ MISSING"}')
    print(f'    Device code functions:   {"✓ PRESENT" if dc_funcs_ok else "✗ MISSING"}')
    print(f'    Version 6.1.2:           {"✓ CORRECT" if version_ok else "✗ INCORRECT"}')
    print()

    # Overall status
    all_ok = (fail_count == 0 and url_guard_ok and endpoint_ok and frontend_ok and version_ok)
    if all_ok:
        print('  STATUS: ✓ UPDATE APPLIED SUCCESSFULLY')
    else:
        print('  STATUS: ⚠ UPDATE APPLIED WITH ISSUES — see details above')
    print()

    print('=' * 65)
    print()

    # What's new
    print("What's new in v6.1.2:")
    print()
    print('  1. URL MISROUTE FIX:')
    print('     SharePoint URLs pasted into the local "Enter folder path"')
    print('     field now show a clear error directing you to the')
    print('     "Paste SharePoint link" field below.')
    print()
    print('  2. DEVICE CODE FLOW UI:')
    print('     When Connect & Scan needs browser-based OAuth, you will')
    print('     see a panel showing:')
    print('       - The Microsoft login URL (clickable)')
    print('       - A device code to enter')
    print('       - A button to retry after authenticating')
    print()
    print('  EXPECTED CONNECT & SCAN FLOW:')
    print('    1. Paste SharePoint URL in "Paste SharePoint link" field')
    print('    2. Click "Connect & Scan"')
    print('    3. If device code appears:')
    print('       a. Click the Microsoft URL to open in your browser')
    print('       b. Enter the device code shown')
    print('       c. Complete authentication in browser')
    print('       d. Click "I\'ve Completed Authentication" in AEGIS')
    print('    4. On success, documents will be listed for scanning')
    print()
    print('Next steps:')
    print('  1. Restart AEGIS (double-click Restart_AEGIS.bat)')
    print('  2. Hard refresh browser (Ctrl+Shift+R)')
    print('  3. Paste your SharePoint URL and click Connect & Scan')
    print()

    if not msal_ok:
        print('  [CRITICAL] MSAL is required for SharePoint Online authentication.')
        print('  Run: python -m pip install msal')
        print()

    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download.')
        print('  You may need to download them manually from GitHub.')
        print()

    print(f'  Backups saved to: {backup_dir}')
    print()

    # What to look for in AEGIS terminal after restart
    print('What to look for in the AEGIS terminal after restart:')
    print('  ✓ "MSAL app created successfully"')
    print('  ✓ "SharePoint tenant discovery: Found tenant GUID via OIDC"')
    print('  ✓ "Auth strategies active: ..." (should include OAuth-Bearer)')
    print()
    print('If Connect & Scan shows a device code panel:')
    print('  ✓ This is EXPECTED — it means MSAL is working correctly')
    print('  ✓ Complete the auth flow in your browser')
    print('  ✓ Click "I\'ve Completed Authentication" to continue')
    print()


if __name__ == '__main__':
    main()
