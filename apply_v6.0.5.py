#!/usr/bin/env python3
"""
AEGIS v6.0.5 → v6.0.7 Update Applier
=======================================
SharePoint Online Modern Auth — Preemptive SSPI + MSAL OAuth 2.0

Downloads updated files from GitHub and applies them to the AEGIS installation.
Creates timestamped backups of each file before overwriting.
Installs required dependencies using the CORRECT Python (embedded or system).

Changes:
- sharepoint_connector.py — Multi-strategy auth + validate_folder_path fix
- requirements.txt — Added msal>=1.20.0 and PyJWT>=2.0.0
- version.json / static/version.json — Version bump
- Install_AEGIS_OneClick.bat / repair_aegis.py — Updated
- pywin32 — Required for preemptive SSPI Negotiate (sspi + win32security modules)
- msal + PyJWT — Required for OAuth 2.0 fallback

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.0.5.py

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
    'sharepoint_connector.py': 'SharePoint connector with modern auth + folder validation fix',
    'requirements.txt': 'Updated dependencies (msal, PyJWT, pywin32)',
    'version.json': 'Version 6.0.7',
    'static/version.json': 'Version 6.0.7 (static copy)',
    'CLAUDE.md': 'Session notes with Lessons 139-140',
    'static/js/help-docs.js': 'Help docs with v6.0.7 changelog',
    'Install_AEGIS_OneClick.bat': 'Updated installer (MSAL + pywin32)',
    'repair_aegis.py': 'Repair tool with MSAL support',
}

# Binary wheel files (downloaded separately)
WHEEL_FILES = {
    'wheels/msal-1.35.0-py3-none-any.whl': 'MSAL wheel (120KB)',
    'wheels/pyjwt-2.11.0-py3-none-any.whl': 'PyJWT wheel (28KB)',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.7'})
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
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.7'})
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

    The embedded Python is what AEGIS uses at runtime — packages MUST
    be installed there, not in the system Python.
    """
    cwd = os.getcwd()

    # Check for embedded Python (OneClick installer layout)
    embedded_paths = [
        os.path.join(cwd, 'python', 'python.exe'),      # Standard layout
        os.path.join(cwd, 'python', 'python3.exe'),      # Alternate
        os.path.join(cwd, '..', 'python', 'python.exe'), # If run from app/ subfolder
    ]

    for p in embedded_paths:
        if os.path.isfile(p):
            abs_path = os.path.abspath(p)
            print(f'  [FOUND] Embedded Python: {abs_path}')
            return abs_path

    # Fall back to whatever launched this script
    print(f'  [INFO] No embedded Python found — using: {sys.executable}')
    return sys.executable


def pip_install(python_exe, packages, wheels_dirs, label=''):
    """
    Install packages from local wheels only (offline, no internet).

    Returns True if install succeeded, False otherwise.
    """
    if label:
        print(f'  Installing {label}...')

    # Build --find-links args
    find_links = []
    for d in wheels_dirs:
        find_links.extend(['--find-links', d])

    # Install from local wheels only — no internet
    cmd = [
        python_exe, '-m', 'pip', 'install',
        '--no-index',
        *find_links,
        '--no-warn-script-location',
        *packages
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f'    [OK] {label or " ".join(packages)} installed from wheels')
        return True

    # Show error for debugging
    print(f'    [FAIL] Could not install {label or " ".join(packages)}')
    stderr = result.stderr.strip() if result.stderr else ''
    if stderr:
        err_lines = [l for l in stderr.split('\n') if l.strip() and 'WARNING' not in l]
        for line in err_lines[:3]:
            print(f'           {line[:120]}')

    # List available wheels for debugging
    for d in wheels_dirs:
        matching = [f for f in os.listdir(d) if any(p.lower().replace('-', '_') in f.lower() for p in packages)]
        if matching:
            print(f'    [DEBUG] Found wheels in {d}: {", ".join(matching[:5])}')
        else:
            print(f'    [DEBUG] No matching wheels found in {d}')

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
    print('  AEGIS v6.0.7 Update Applier')
    print('  SharePoint Online Modern Auth')
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

    # Show which Python to verify
    py_version = subprocess.run(
        [python_exe, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'],
        capture_output=True, text=True
    )
    if py_version.returncode == 0:
        print(f'  Python version: {py_version.stdout.strip()}')

    # Show site-packages location
    sp_loc = subprocess.run(
        [python_exe, '-c', 'import site; print(site.getusersitepackages() if hasattr(site, "getusersitepackages") else "N/A"); [print(p) for p in site.getsitepackages()]'],
        capture_output=True, text=True
    )
    if sp_loc.returncode == 0:
        print(f'  Site-packages: {sp_loc.stdout.strip().split(chr(10))[-1]}')
    print()

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.0.7_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[INFO] Backup directory: {backup_dir}')
    print()

    # Ensure directories exist
    os.makedirs('wheels', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # Download and apply text files
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

    # Download wheel files
    print('[STEP 2] Downloading wheel files...')
    for rel_path, description in WHEEL_FILES.items():
        print(f'  Downloading {rel_path} ({description})...')

        # Backup existing file
        if os.path.exists(rel_path):
            backup_path = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            os.makedirs(os.path.dirname(backup_path) if os.path.dirname(backup_path) else '.', exist_ok=True)
            shutil.copy2(rel_path, backup_path)

        # Download wheel (binary)
        url = f'{RAW_BASE}/{rel_path}'
        if download_file(url, rel_path, is_binary=True):
            file_size = os.path.getsize(rel_path)
            print(f'    [OK] Downloaded ({file_size:,} bytes)')
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

    # Install dependencies
    print('[STEP 3] Installing SharePoint auth dependencies...')
    print(f'  Target Python: {python_exe}')
    print()

    # 3a: pywin32 — needed for preemptive SSPI (sspi + win32security modules)
    # This is the PRIMARY auth strategy for SharePoint Online
    if sys.platform == 'win32':
        pip_install(python_exe, ['pywin32'], wheels_dirs, 'pywin32 (Windows SSPI auth)')

        # pywin32 needs a post-install step to register COM objects
        # Run the post-install script if it exists
        postinstall = subprocess.run(
            [python_exe, '-c',
             'import os, sys; '
             'scripts = os.path.join(os.path.dirname(sys.executable), "Scripts", "pywin32_postinstall.py"); '
             'print(scripts if os.path.exists(scripts) else "NOT_FOUND")'],
            capture_output=True, text=True
        )
        if postinstall.returncode == 0 and 'NOT_FOUND' not in postinstall.stdout:
            script_path = postinstall.stdout.strip()
            print(f'    Running pywin32 post-install: {script_path}')
            subprocess.run([python_exe, script_path, '-install'],
                         capture_output=True, text=True)
    else:
        print('  [SKIP] pywin32 — not on Windows')

    print()

    # 3b: msal + PyJWT — needed for OAuth 2.0 fallback
    pip_install(python_exe, ['msal', 'PyJWT'], wheels_dirs, 'msal + PyJWT (OAuth 2.0 auth)')

    print()

    # Verify imports
    print('[STEP 4] Verifying auth dependencies...')
    all_ok = True

    if sys.platform == 'win32':
        # Check pywin32 modules (needed for preemptive SSPI)
        if not verify_import(python_exe, 'sspi', 'sspi (pywin32 — SSPI preemptive auth)'):
            all_ok = False
        if not verify_import(python_exe, 'win32security', 'win32security (pywin32 — SSPI)'):
            all_ok = False

        # Check requests-negotiate-sspi (needed for standard SSO)
        verify_import(python_exe, 'requests_negotiate_sspi', 'requests-negotiate-sspi (standard SSO)')

    # Check MSAL (needed for OAuth fallback)
    if not verify_import(python_exe, 'msal', 'MSAL (SharePoint Online OAuth)'):
        all_ok = False

    verify_import(python_exe, 'jwt', 'PyJWT (JSON Web Tokens)')

    print()

    # Auth strategy summary
    print('[STEP 5] SharePoint Auth Strategy Summary:')

    # Check each strategy
    strat1 = subprocess.run(
        [python_exe, '-c', 'import sspi, win32security; print("OK")'],
        capture_output=True, text=True
    )
    strat2 = subprocess.run(
        [python_exe, '-c', 'from requests_negotiate_sspi import HttpNegotiateAuth; print("OK")'],
        capture_output=True, text=True
    )
    strat3 = subprocess.run(
        [python_exe, '-c', 'import msal; print("OK")'],
        capture_output=True, text=True
    )

    s1_ok = strat1.returncode == 0
    s2_ok = strat2.returncode == 0
    s3_ok = strat3.returncode == 0

    print(f'  Strategy 1 — Preemptive SSPI Negotiate: {"[OK]" if s1_ok else "[NOT AVAILABLE]"}')
    print(f'    Uses pywin32 sspi + win32security to generate auth token before first request.')
    print(f'    This is the PRIMARY strategy for SharePoint Online (GCC High).')
    print()
    print(f'  Strategy 2 — Standard Negotiate SSO:    {"[OK]" if s2_ok else "[NOT AVAILABLE]"}')
    print(f'    Uses requests-negotiate-sspi reactive auth (needs WWW-Authenticate header).')
    print(f'    Works for on-premises SharePoint but NOT SharePoint Online.')
    print()
    print(f'  Strategy 3 — MSAL OAuth 2.0:            {"[OK]" if s3_ok else "[NOT AVAILABLE]"}')
    print(f'    Uses Azure AD app registration for modern auth.')
    print(f'    Requires client_id + tenant_id + client_secret in config.json.')
    print()

    if s1_ok:
        print('  >>> Preemptive SSPI is available — this should work for SharePoint Online!')
    elif s3_ok:
        print('  >>> MSAL is available — configure OAuth in config.json for SharePoint Online.')
    elif s2_ok:
        print('  >>> Only standard Negotiate available — may not work for SharePoint Online.')
        print('      SharePoint Online has disabled legacy auth (empty WWW-Authenticate).')
        print('      Install pywin32 for preemptive SSPI or msal for OAuth.')
    else:
        print('  >>> NO SharePoint auth strategies available!')
        print('      Install pywin32 (for SSPI) or msal (for OAuth).')

    print()

    # Summary
    print('=' * 60)
    print(f'  Update complete: {success_count} succeeded, {fail_count} failed')
    print('=' * 60)
    print()
    print('Next steps:')
    print('  1. Restart AEGIS (double-click Restart_AEGIS.bat)')
    print('  2. Hard refresh browser (Ctrl+Shift+R)')
    print('  3. Try SharePoint Connect & Scan')
    print()
    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download or install.')
        print('  You may need to download them manually from GitHub.')
    print(f'  Backups saved to: {backup_dir}')


if __name__ == '__main__':
    main()
