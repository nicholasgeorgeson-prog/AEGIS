#!/usr/bin/env python3
"""
AEGIS v6.1.0 → v6.1.1 Update Applier
=======================================
Fix: MSAL instance_discovery=False + verify=False for GCC High

The v6.1.0 fix resolved the tenant identifier format (ngc → ngc.onmicrosoft.us
or GUID), but MSAL still failed with "Unable to get authority configuration"
because of TWO missing constructor parameters:

1. instance_discovery=False — MSAL validates GCC High authority against the
   COMMERCIAL cloud's instance discovery endpoint, which fails. This param
   tells MSAL to skip that validation.

2. verify=False — Corporate SSL inspection replaces TLS certs with internal
   CA certs that Python's certifi doesn't trust. MSAL uses its own internal
   requests session, so the connector's verify=False doesn't apply to MSAL.

Also fixed:
- OIDC tenant discovery endpoint now uses verify=False (same SSL issue)
- Removed dead IWA code (acquire_token_by_integrated_windows_auth doesn't
  exist in MSAL Python — only in MSAL.NET)
- ConfidentialClientApplication also gets instance_discovery=False + verify=False

Changes:
- sharepoint_connector.py — Fixed MSAL app creation, OIDC SSL, dead IWA removal
- version.json / static/version.json — Version bump to 6.1.1
- static/js/help-docs.js — v6.1.1 changelog
- CLAUDE.md — Lesson 144

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.1.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
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
    'sharepoint_connector.py': 'SharePoint connector — MSAL instance_discovery=False, verify=False, dead IWA removal',
    'version.json': 'Version 6.1.1',
    'static/version.json': 'Version 6.1.1 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 144',
    'static/js/help-docs.js': 'Help docs with v6.1.1 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.1'})
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
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.1'})
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
    result = subprocess.run(
        [python_exe, '-c', f'import {module_name}; print(getattr({module_name}, "__version__", "ok"))'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ver = result.stdout.strip()
        print(f'  [OK] {display_name} {ver}')
        return True
    else:
        err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown error'
        print(f'  [FAIL] {display_name} — {err[:100]}')
        return False


def verify_msal_gcc_high(python_exe):
    """
    v6.1.1: Verify MSAL can create an app with instance_discovery=False.
    This is the EXACT operation that was failing before.
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
    # Older MSAL without instance_discovery support
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


def main():
    print('=' * 60)
    print('  AEGIS v6.1.1 Update Applier')
    print('  Fix: MSAL GCC High Authority Validation + Corporate SSL')
    print('=' * 60)
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

    py_version = subprocess.run(
        [python_exe, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'],
        capture_output=True, text=True
    )
    if py_version.returncode == 0:
        print(f'  Python version: {py_version.stdout.strip()}')
    print()

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.1.1_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[INFO] Backup directory: {backup_dir}')
    print()

    # Ensure directories exist
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # Download and apply files
    print('[STEP 1] Downloading updated source files...')
    success_count = 0
    fail_count = 0

    for rel_path, description in FILES.items():
        print(f'  Updating {rel_path} ({description})...')

        # Backup existing file
        if os.path.exists(rel_path):
            backup_path = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            os.makedirs(os.path.dirname(backup_path) if os.path.dirname(backup_path) else '.', exist_ok=True)
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

    # Verify auth dependencies are still installed (from v6.0.9)
    print('[STEP 2] Verifying auth dependencies...')
    msal_verified = verify_import(python_exe, 'msal', 'MSAL (OAuth 2.0)')
    jwt_verified = verify_import(python_exe, 'jwt', 'PyJWT')
    if sys.platform == 'win32':
        sspi_verified = verify_import(python_exe, 'sspi', 'sspi (pywin32 SSPI)')
        win32sec_verified = verify_import(python_exe, 'win32security', 'win32security (pywin32)')
    print()

    # v6.1.1: Verify MSAL can actually create an app for GCC High
    print('[STEP 3] Verifying MSAL GCC High compatibility...')
    if msal_verified:
        gcc_ok = verify_msal_gcc_high(python_exe)
    else:
        print('  [SKIP] MSAL not installed — cannot verify GCC High compatibility')
        gcc_ok = False
    print()

    # Summary
    print('=' * 60)
    print(f'  Files: {success_count} succeeded, {fail_count} failed')
    print(f'  MSAL: {"✓ INSTALLED" if msal_verified else "✗ NOT INSTALLED"}')
    print(f'  PyJWT: {"✓ INSTALLED" if jwt_verified else "✗ NOT INSTALLED"}')
    if sys.platform == 'win32':
        print(f'  pywin32: {"✓ INSTALLED" if sspi_verified else "✗ NOT INSTALLED"}')
    print(f'  MSAL GCC High: {"✓ WORKING" if gcc_ok else "✗ NOT WORKING"}')
    print('=' * 60)
    print()

    if not msal_verified:
        print('  [CRITICAL] MSAL is required for SharePoint Online authentication.')
        print('  Run apply_v6.0.9.py first to install MSAL, then run this script.')
        print()

    print("What's new in v6.1.1:")
    print('  - Fix: MSAL instance_discovery=False (skip commercial cloud validation for GCC High)')
    print('  - Fix: MSAL verify=False (bypass corporate SSL inspection)')
    print('  - Fix: OIDC discovery endpoint also uses verify=False')
    print('  - Fix: Removed dead IWA code (does not exist in MSAL Python)')
    print()
    print('  These changes fix the "Unable to get authority configuration" error')
    print('  that persisted after v6.1.0 fixed the tenant identifier format.')
    print()
    print('Next steps:')
    print('  1. Restart AEGIS (double-click Restart_AEGIS.bat)')
    print('  2. Hard refresh browser (Ctrl+Shift+R)')
    print('  3. Try SharePoint Connect & Scan')
    print()
    print('What to look for in the terminal after restart:')
    print('  ✓ "MSAL app created successfully"')
    print('  ✓ "SharePoint tenant discovery: Found tenant GUID via OIDC"')
    print('  ✓ "Auth strategies active: Preemptive-SSPI, OAuth-Bearer, Negotiate-SSO"')
    print()
    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download.')
        print('  You may need to download them manually from GitHub.')
    print(f'  Backups saved to: {backup_dir}')


if __name__ == '__main__':
    main()
