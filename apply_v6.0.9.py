#!/usr/bin/env python3
"""
AEGIS v6.0.8 → v6.0.9 Update Applier
=======================================
Fix: OAuth dependency installation — online pip fallback

The v6.0.8 apply script failed to install msal/PyJWT/pywin32 because it used
--no-index (offline-only), but the wheel files don't exist in the wheels/
directory on the Windows machine. This version tries offline first, then falls
back to online pip install.

Changes:
- sharepoint_connector.py — Enhanced startup logging (auth method visibility)
- static/js/app.js — Fix UI freeze after SharePoint connection failure
- version.json / static/version.json — Version bump to 6.0.9
- static/js/help-docs.js — v6.0.9 changelog
- CLAUDE.md — Lessons 142
- msal + PyJWT + pywin32 — CRITICAL: Installed via online pip if offline fails

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.0.9.py

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
    'sharepoint_connector.py': 'SharePoint connector — enhanced auth logging',
    'static/js/app.js': 'Fix UI freeze after SharePoint connection failure',
    'version.json': 'Version 6.0.9',
    'static/version.json': 'Version 6.0.9 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 142',
    'static/js/help-docs.js': 'Help docs with v6.0.9 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.9'})
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
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.9'})
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


def pip_install_offline(python_exe, packages, wheels_dirs, label=''):
    """Try installing packages from local wheels (offline)."""
    find_links = []
    for d in wheels_dirs:
        if os.path.isdir(d):
            find_links.extend(['--find-links', d])

    if not find_links:
        return False

    cmd = [
        python_exe, '-m', 'pip', 'install',
        '--no-index',
        *find_links,
        '--no-warn-script-location',
        *packages
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def pip_install_online(python_exe, packages, label=''):
    """Install packages from PyPI (online)."""
    cmd = [
        python_exe, '-m', 'pip', 'install',
        '--no-warn-script-location',
        *packages
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True
    # Show error for debugging
    stderr = result.stderr.strip() if result.stderr else ''
    if stderr:
        err_lines = [l for l in stderr.split('\n') if l.strip() and 'WARNING' not in l]
        for line in err_lines[:5]:
            print(f'           {line[:150]}')
    return False


def pip_install(python_exe, packages, wheels_dirs, label=''):
    """Install packages with offline-first, online-fallback strategy."""
    if label:
        print(f'  Installing {label}...')

    # Strategy 1: Try offline (local wheels)
    if pip_install_offline(python_exe, packages, wheels_dirs, label):
        print(f'    [OK] {label or " ".join(packages)} installed from local wheels')
        return True

    print(f'    [INFO] Offline install failed — trying online (PyPI)...')

    # Strategy 2: Try online (PyPI)
    if pip_install_online(python_exe, packages, label):
        print(f'    [OK] {label or " ".join(packages)} installed from PyPI')
        return True

    print(f'    [FAIL] Could not install {label or " ".join(packages)}')
    print(f'           Try manually: {python_exe} -m pip install {" ".join(packages)}')
    return False


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
    print('  AEGIS v6.0.9 Update Applier')
    print('  Fix: OAuth Dependency Installation')
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

    # Check if pip exists
    pip_check = subprocess.run(
        [python_exe, '-m', 'pip', '--version'],
        capture_output=True, text=True
    )
    if pip_check.returncode != 0:
        print(f'  [WARN] pip not available for {python_exe}')
        print(f'         Packages will need to be installed manually')
    else:
        pip_ver = pip_check.stdout.strip().split('\n')[0]
        print(f'  pip: {pip_ver[:80]}')
    print()

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.0.9_{timestamp}')
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

    # Build list of wheels directories
    wheels_dirs = []
    for d in ['wheels', os.path.join('packaging', 'wheels')]:
        full = os.path.join(os.getcwd(), d)
        if os.path.isdir(full):
            wheels_dirs.append(full)
    if not wheels_dirs:
        wheels_dirs = [os.path.join(os.getcwd(), 'wheels')]

    print(f'[INFO] Wheels directories: {wheels_dirs}')
    print()

    # ===========================================================
    # CRITICAL: Install OAuth dependencies (msal, PyJWT, pywin32)
    # v6.0.9 FIX: Try offline first, then ONLINE fallback
    # ===========================================================
    print('[STEP 2] Installing OAuth dependencies...')
    print(f'  Target Python: {python_exe}')
    print()

    # Install msal (required for SharePoint Online OAuth 2.0)
    print('  --- MSAL (Microsoft Authentication Library) ---')
    msal_ok = pip_install(python_exe, ['msal'], wheels_dirs, 'msal (OAuth 2.0)')
    print()

    # Install PyJWT (required by MSAL)
    print('  --- PyJWT ---')
    jwt_ok = pip_install(python_exe, ['PyJWT'], wheels_dirs, 'PyJWT')
    print()

    # Install pywin32 (required for preemptive SSPI Negotiate tokens)
    if sys.platform == 'win32':
        print('  --- pywin32 (Windows SSPI) ---')
        pywin_ok = pip_install(python_exe, ['pywin32'], wheels_dirs, 'pywin32 (Windows SSPI auth)')
        print()

    print()

    # Verify
    print('[STEP 3] Verifying auth dependencies...')
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
        print('  SharePoint will NOT work without MSAL.')
        print()
        print('  To install manually, run:')
        print(f'    "{python_exe}" -m pip install msal')
        print()

    print("What's new in v6.0.9:")
    print('  - Fix: OAuth packages now install via online pip if local wheels missing')
    print('  - MSAL auto-detects tenant from SharePoint URL (zero config)')
    print('  - No config.json editing required for enterprise deployment')
    print('  - UI no longer freezes after a failed SharePoint connection')
    print()
    print('Next steps:')
    print('  1. Restart AEGIS (double-click Restart_AEGIS.bat)')
    print('  2. Hard refresh browser (Ctrl+Shift+R)')
    print('  3. Try SharePoint Connect & Scan')
    print()
    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download.')
        print('  You may need to download them manually from GitHub.')
    print(f'  Backups saved to: {backup_dir}')


if __name__ == '__main__':
    main()
