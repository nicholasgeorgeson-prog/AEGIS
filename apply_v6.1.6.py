#!/usr/bin/env python3
"""
AEGIS v6.1.5 → v6.1.6 Update Applier
=======================================
HeadlessSP SSO Fix — 3 Root Causes Fixed

The v6.1.3-v6.1.5 headless browser SSO authentication failed because of
THREE compounding issues:

1. chrome-headless-shell (bundled Playwright binary) lacks full SSPI/Negotiate
   support for Windows Integrated Auth. Fix: Use system Microsoft Edge via
   channel='msedge' (always available on Win10/11).

2. Playwright's new_context() creates incognito-like ephemeral contexts where
   Chrome 81+ disables ambient NTLM/Negotiate auth. Fix: Switch to
   launchPersistentContext() with a temp user_data_dir.

3. No explicit ambient auth enablement. Fix: Add Chromium flag
   --enable-features=EnableAmbientAuthenticationInIncognito.

Changes:
- sharepoint_connector.py — Rewritten _ensure_browser() with 3-part fix,
  updated __init__() and close() for persistent context + temp dir cleanup
- version.json / static/version.json — Version bump to 6.1.6
- static/js/help-docs.js — v6.1.6 changelog
- CLAUDE.md — Lesson #150 (HeadlessSP SSO root causes)

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.6.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan — check logs/sharepoint.log for diagnostics
"""

import os
import sys
import ssl
import shutil
import subprocess
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — launchPersistentContext + msedge + ambient auth fix',
    'version.json': 'Version 6.1.6',
    'static/version.json': 'Version 6.1.6 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.6 changelog',
    'CLAUDE.md': 'Session notes — Lesson #150 (HeadlessSP SSO root causes)',
}


def create_ssl_context():
    """Create SSL context with fallback for certificate issues."""
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        ctx = ssl._create_unverified_context()
        return ctx


def download_file(url, dest_path, description=''):
    """Download a file from URL to dest_path with SSL fallback."""
    ctx = create_ssl_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.6'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.6'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            print(f'  [ERROR] Download failed: {e2}')
            return False


def find_aegis_python():
    """
    Find the correct Python executable for AEGIS.
    Priority: embedded Python in python/ subdirectory → sys.executable
    """
    cwd = os.getcwd()
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


def check_edge_installed():
    """Check if Microsoft Edge is installed on the system."""
    if sys.platform != 'win32':
        print('  [SKIP] Edge check — not on Windows')
        return False

    edge_paths = [
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    ]

    for p in edge_paths:
        if p and os.path.isfile(p):
            print(f'  [OK] Microsoft Edge found: {p}')
            return True

    print('  [WARN] Microsoft Edge not found at standard paths')
    print('         (This is unexpected on Windows 10/11 — Edge is pre-installed)')
    return False


def main():
    print()
    print('=' * 70)
    print('  AEGIS v6.1.6 Update — HeadlessSP SSO Fix (3 Root Causes)')
    print('=' * 70)
    print()

    # ── Step 0: Verify we're in the right directory ──
    if not os.path.isfile('app.py') or not os.path.isdir('static'):
        print('[ERROR] This script must be run from the AEGIS install directory.')
        print('        Expected to find app.py and static/ in the current directory.')
        print(f'        Current directory: {os.getcwd()}')
        print()
        print('Usage:')
        print('  cd <AEGIS_INSTALL_DIR>')
        print('  python apply_v6.1.6.py')
        sys.exit(1)

    print(f'  Install directory: {os.getcwd()}')
    print()

    # ── Step 1: Create timestamped backup ──
    print('Step 1: Backing up current files...')
    backup_dir = os.path.join('backups', f'v6.1.6_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    os.makedirs(backup_dir, exist_ok=True)

    for rel_path in FILES:
        if os.path.isfile(rel_path):
            dest = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(rel_path, dest)
            print(f'  [BACKUP] {rel_path}')
        else:
            print(f'  [SKIP] {rel_path} (not present — will be created)')

    print(f'  Backups saved to: {backup_dir}')
    print()

    # ── Step 2: Download updated files from GitHub ──
    print('Step 2: Downloading updated files from GitHub...')
    all_ok = True
    for rel_path, description in FILES.items():
        url = f'{RAW_BASE}/{rel_path}'
        print(f'  [{rel_path}] {description}')

        # Ensure parent directory exists
        parent = os.path.dirname(rel_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if download_file(url, rel_path, description):
            size = os.path.getsize(rel_path)
            print(f'    ✓ Downloaded ({size:,} bytes)')
        else:
            print(f'    ✗ FAILED')
            all_ok = False

    print()
    if not all_ok:
        print('[WARNING] Some files failed to download.')
        print('          You can restore from backups at:')
        print(f'          {os.path.abspath(backup_dir)}')
        print()

    # ── Step 3: Find Python and verify Playwright ──
    print('Step 3: Verifying Playwright installation...')
    python_exe = find_aegis_python()

    pw_ok = verify_import(python_exe, 'playwright.sync_api', 'Playwright')
    if not pw_ok:
        print()
        print('  [WARN] Playwright is not installed.')
        print('         The headless SP connector requires Playwright.')
        print(f'         Install with: {python_exe} -m pip install playwright')
        print()

    # ── Step 4: Check Edge availability ──
    print()
    print('Step 4: Checking Microsoft Edge availability...')
    edge_ok = check_edge_installed()

    # ── Step 5: Verify auth strategy availability ──
    print()
    print('Step 5: Checking auth strategy availability...')

    strategies = []

    # Strategy 1: msedge channel (primary — uses system Edge)
    if edge_ok:
        strategies.append(('msedge', 'System Microsoft Edge (new headless mode, full SSPI)'))
    else:
        print('  [1] msedge — NOT AVAILABLE (Edge not found)')

    # Strategy 2: chrome channel (uses system Chrome)
    chrome_paths = []
    if sys.platform == 'win32':
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        ]
    chrome_found = any(p and os.path.isfile(p) for p in chrome_paths)
    if chrome_found:
        strategies.append(('chrome', 'System Google Chrome (new headless mode, full SSPI)'))
    else:
        print('  [2] chrome — NOT AVAILABLE (Chrome not found)')

    # Strategy 3: bundled chromium (headless shell — last resort)
    if pw_ok:
        strategies.append(('bundled', 'Bundled Chromium headless shell (last resort)'))
    else:
        print('  [3] bundled — NOT AVAILABLE (Playwright not installed)')

    print()
    if strategies:
        print('  Available browser strategies (in priority order):')
        for i, (channel, desc) in enumerate(strategies, 1):
            marker = '★' if i == 1 else ' '
            print(f'  {marker} [{i}] {channel}: {desc}')
    else:
        print('  [ERROR] No browser strategies available!')
        print('          HeadlessSP connector will not work.')

    # ── Summary ──
    print()
    print('=' * 70)
    print('  v6.1.6 Update Summary')
    print('=' * 70)
    print()
    print('  Files updated:')
    for rel_path, desc in FILES.items():
        print(f'    • {rel_path}')
    print()
    print('  What changed in sharepoint_connector.py:')
    print('    1. _ensure_browser() uses launchPersistentContext()')
    print('       (not launch() + new_context() which was incognito-like)')
    print('    2. Tries channel=msedge first (system Edge, full SSPI)')
    print('       then chrome, then bundled chromium as fallback')
    print('    3. Adds --enable-features=EnableAmbientAuthenticationInIncognito')
    print('    4. User-Agent includes Edg/ for AD FS WiaSupportedUserAgents')
    print('    5. Temp user_data_dir cleaned up in close()')
    print()
    print('  Backups at:')
    print(f'    {os.path.abspath(backup_dir)}')
    print()
    print('  Next steps:')
    print('    1. Restart AEGIS (Restart_AEGIS.bat or Ctrl+C → python app.py)')
    print('    2. Hard refresh browser (Ctrl+Shift+R)')
    print('    3. Try SharePoint Connect & Scan')
    print('    4. Check logs/sharepoint.log for diagnostics')
    print('       Look for: "[HeadlessSP] Browser started: Microsoft Edge"')
    print()


if __name__ == '__main__':
    main()
