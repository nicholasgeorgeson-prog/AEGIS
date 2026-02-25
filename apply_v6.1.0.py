#!/usr/bin/env python3
"""
AEGIS v6.0.9 → v6.1.0 Update Applier
=======================================
Fix: SharePoint OAuth tenant identifier — OIDC-based discovery

The v6.0.9 fix installed msal/pywin32 successfully, but MSAL failed with:
  "Unable to get authority configuration for https://login.microsoftonline.us/ngc"

Root cause: The bare subdomain 'ngc' from 'ngc.sharepoint.us' is NOT a valid
Azure AD tenant identifier. MSAL needs either the tenant GUID or the full
domain format '{tenant}.onmicrosoft.us'.

This version fixes _auto_detect_oauth_config() to:
1. Discover tenant GUID via Microsoft's public OIDC endpoint
2. Fall back to '{tenant}.onmicrosoft.us' domain format
3. Try multiple authority URLs if first attempt fails

Changes:
- sharepoint_connector.py — Fixed tenant discovery, OIDC GUID resolution,
  authority fallback cascade, enhanced startup logging
- version.json / static/version.json — Version bump to 6.1.0
- static/js/help-docs.js — v6.1.0 changelog
- CLAUDE.md — Lesson 143

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.0.py

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
    'sharepoint_connector.py': 'SharePoint connector — OIDC tenant discovery, authority fallback',
    'version.json': 'Version 6.1.0',
    'static/version.json': 'Version 6.1.0 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 143',
    'static/js/help-docs.js': 'Help docs with v6.1.0 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.0'})
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
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.0'})
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


def main():
    print('=' * 60)
    print('  AEGIS v6.1.0 Update Applier')
    print('  Fix: SharePoint OAuth Tenant Discovery')
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
    backup_dir = os.path.join('backups', f'pre_v6.1.0_{timestamp}')
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

    # Summary
    print('=' * 60)
    print(f'  Files: {success_count} succeeded, {fail_count} failed')
    print(f'  MSAL: {"✓ INSTALLED" if msal_verified else "✗ NOT INSTALLED"}')
    print(f'  PyJWT: {"✓ INSTALLED" if jwt_verified else "✗ NOT INSTALLED"}')
    if sys.platform == 'win32':
        print(f'  pywin32: {"✓ INSTALLED" if sspi_verified else "✗ NOT INSTALLED"}')
    print('=' * 60)
    print()

    if not msal_verified:
        print('  [CRITICAL] MSAL is required for SharePoint Online authentication.')
        print('  Run apply_v6.0.9.py first to install MSAL, then run this script.')
        print()

    print("What's new in v6.1.0:")
    print('  - Fix: Tenant identifier format for MSAL authority URLs')
    print('    Before: "ngc" (bare subdomain — invalid for Azure AD)')
    print('    After:  "ngc.onmicrosoft.us" or actual tenant GUID')
    print('  - New: OIDC-based tenant GUID discovery (public endpoint, zero-config)')
    print('  - New: Authority fallback cascade (GUID → domain → organizations)')
    print('  - Enhanced auth startup logging for diagnostics')
    print()
    print('Next steps:')
    print('  1. Restart AEGIS (double-click Restart_AEGIS.bat)')
    print('  2. Hard refresh browser (Ctrl+Shift+R)')
    print('  3. Try SharePoint Connect & Scan')
    print()
    print('What to look for in the terminal after restart:')
    print('  ✓ "SharePoint tenant discovery: Found tenant GUID via OIDC"')
    print('  ✓ "MSAL app created successfully"')
    print('  ✓ "Auth strategies active: Preemptive-SSPI, OAuth-Bearer, Negotiate-SSO"')
    print()
    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download.')
        print('  You may need to download them manually from GitHub.')
    print(f'  Backups saved to: {backup_dir}')


if __name__ == '__main__':
    main()
