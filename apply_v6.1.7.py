#!/usr/bin/env python3
"""
AEGIS v6.1.6 → v6.1.7 Update Applier
=======================================
HeadlessSP Document Discovery Diagnostics

v6.1.6 fixed SSO authentication (browser authenticates via Edge).
But document discovery returns 0 files for the T&E library path.

This update adds comprehensive diagnostic logging throughout the
discovery chain so logs/sharepoint.log will reveal exactly where
the chain breaks on the next Connect & Scan attempt.

Changes:
- sharepoint_connector.py — Diagnostic logging in validate_folder_path(),
  _list_files_recursive(), connect_and_discover(), _api_get().
  Defensive URL-decode check for library_path.
- routes/review_routes.py — Route-level logging of parsed site_url and
  library_path. URL guard added to ALL 3 folder scan endpoints.
- scan_history.py — get_statement_review_stats method (fixes 500 errors)
- routes/scan_history_routes.py — Statement review stats endpoint
- version.json / static/version.json — Version bump to 6.1.7
- static/js/help-docs.js — v6.1.7 changelog
- CLAUDE.md — Lesson #152 (Diagnostic-first approach)

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.7.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan with your T&E URL
  4. Share logs/sharepoint.log — it will show exactly where discovery fails
"""

import os
import sys
import ssl
import shutil
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — diagnostic logging + URL-decode guard',
    'routes/review_routes.py': 'Review routes — SP logging + URL guard on all folder endpoints',
    'scan_history.py': 'Scan history DB — get_statement_review_stats method (fixes 500 errors)',
    'routes/scan_history_routes.py': 'Scan history routes — statement review stats endpoint',
    'version.json': 'Version 6.1.7',
    'static/version.json': 'Version 6.1.7 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.7 changelog',
    'CLAUDE.md': 'Session notes — Lesson #152 (diagnostic approach)',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.7'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.7'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            print(f'  [ERROR] Download failed: {e2}')
            return False


def main():
    print()
    print('=' * 70)
    print('  AEGIS v6.1.7 Update — HeadlessSP Document Discovery Diagnostics')
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
        print('  python apply_v6.1.7.py')
        sys.exit(1)

    print(f'  Install directory: {os.getcwd()}')
    print()

    # ── Step 1: Create timestamped backup ──
    print('Step 1: Backing up current files...')
    backup_dir = os.path.join('backups', f'v6.1.7_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
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

    # ── Step 2: Ensure directories exist ──
    print('Step 2: Ensuring directory structure...')
    dirs_needed = set()
    for rel_path in FILES:
        parent = os.path.dirname(rel_path)
        if parent:
            dirs_needed.add(parent)
    for d in sorted(dirs_needed):
        os.makedirs(d, exist_ok=True)
        print(f'  [DIR] {d}/')

    # Ensure logs/ directory exists for sharepoint.log
    os.makedirs('logs', exist_ok=True)
    print(f'  [DIR] logs/')
    print()

    # ── Step 3: Download updated files from GitHub ──
    print('Step 3: Downloading updated files from GitHub...')
    all_ok = True
    for rel_path, description in FILES.items():
        url = f'{RAW_BASE}/{rel_path}'
        print(f'  [{rel_path}] {description}')

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

    # ── Summary ──
    print()
    print('=' * 70)
    print('  v6.1.7 Update Summary')
    print('=' * 70)
    print()
    print('  Files updated:')
    for rel_path, desc in FILES.items():
        print(f'    • {rel_path} — {desc}')
    print()
    print('  What this update does:')
    print()
    print('    1. DIAGNOSTIC LOGGING (SharePoint document discovery):')
    print('       Adds detailed logging to the HeadlessSP discovery chain so')
    print('       logs/sharepoint.log reveals exactly why 0 documents are found.')
    print('       • validate_folder_path() — input path, encoded path, result')
    print('       • _list_files_recursive() — file counts, names, subfolders')
    print('       • connect_and_discover() — validation/truncation/auto-detect chain')
    print('       • _api_get() — full URL being fetched')
    print('       • Route handler — parsed site_url and library_path')
    print('       • Defensive URL-decode check (if library_path has %26, decode it)')
    print()
    print('    2. FIX: SharePoint URL guard on ALL folder scan endpoints')
    print('       Previously only the async endpoint had the guard.')
    print('       The sync endpoint and preview endpoint now also detect URLs.')
    print()
    print('    3. FIX: get_statement_review_stats method (500 errors)')
    print('       Deploys scan_history.py with the missing method that caused')
    print('       repeated 500 errors on the Statement History endpoints.')
    print()
    print('  Backups at:')
    print(f'    {os.path.abspath(backup_dir)}')
    print()
    print('  Next steps:')
    print('    1. Restart AEGIS (Restart_AEGIS.bat or Ctrl+C → python app.py)')
    print('    2. Hard refresh browser (Ctrl+Shift+R)')
    print('    3. Try SharePoint Connect & Scan with your T&E URL')
    print('    4. Share the file: logs/sharepoint.log')
    print('       This will show exactly where the discovery chain breaks.')
    print()


if __name__ == '__main__':
    main()
