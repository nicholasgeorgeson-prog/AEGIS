#!/usr/bin/env python3
"""
AEGIS v6.1.7 → v6.1.8 Update Applier
=======================================
SharePoint List Items API Fallback — Zero-File Discovery Fix

v6.1.7 confirmed that HeadlessSP authenticates and validates the folder
(ItemCount=69) but /Files returns 0 items and /Folders returns 0 subfolders.

Root cause: SharePoint's /Files endpoint only returns files stored as
traditional file-system entries. When content is stored as list items
(SharePoint's modern document management mode), /Files returns empty.

This update adds a 3-strategy List Items API fallback cascade:
  Strategy 1: GetList(path)/Items — when path IS the library root
  Strategy 2: Walk up path to find library root, filter by FileDirRef
  Strategy 3: RenderListDataAsStream POST (what the SharePoint web UI uses)

Changes:
- sharepoint_connector.py — 3 new fallback methods + fallback trigger
  in _list_files_recursive() for BOTH HeadlessSP and REST connectors
- version.json / static/version.json — Version bump to 6.1.8
- static/js/help-docs.js — v6.1.8 changelog

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.8.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan with your library URL
  4. Check logs/sharepoint.log for the fallback chain diagnostics
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
    'sharepoint_connector.py': 'SharePoint connector — List Items API fallback (3 strategies)',
    'version.json': 'Version 6.1.8',
    'static/version.json': 'Version 6.1.8 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.8 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.8'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.8'})
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
    print('  AEGIS v6.1.8 Update — SharePoint List Items API Fallback')
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
        print('  python apply_v6.1.8.py')
        sys.exit(1)

    print(f'  Install directory: {os.getcwd()}')
    print()

    # ── Step 1: Create timestamped backup ──
    print('Step 1: Backing up current files...')
    backup_dir = os.path.join('backups', f'v6.1.8_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
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
            print(f'    OK ({size:,} bytes)')
        else:
            print(f'    FAILED')
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
    print('  v6.1.8 Update Summary')
    print('=' * 70)
    print()
    print('  THE FIX:')
    print()
    print('    SharePoint /Files endpoint returned 0 items despite')
    print('    validate_folder_path() confirming ItemCount=69.')
    print()
    print('    Root cause: /Files only returns traditional file-system')
    print('    entries. When content is stored as SharePoint list items')
    print('    (the modern default), /Files returns empty.')
    print()
    print('    Solution: 3-strategy List Items API fallback cascade:')
    print()
    print('      Strategy 1: GetList(path)/Items')
    print('        Queries the library as a list, returns all file items.')
    print('        Works when the target path IS the library root.')
    print()
    print('      Strategy 2: Walk-up parent discovery')
    print('        If path is a subfolder, walks up to find library root,')
    print('        queries all Items, filters by FileDirRef to match the')
    print('        target subfolder.')
    print()
    print('      Strategy 3: RenderListDataAsStream POST')
    print('        Same API that SharePoint web UI uses internally.')
    print('        Gets X-RequestDigest token, POSTs with RecursiveAll.')
    print('        Last resort fallback.')
    print()
    print('    The fallback triggers only when /Files AND /Folders both')
    print('    return empty at the root level. Normal file-system libraries')
    print('    are unaffected — the standard code path handles them first.')
    print()
    print('  NEXT STEPS:')
    print()
    print('    1. Restart AEGIS:')
    print('       Ctrl+C the running server, then: python app.py --debug')
    print('       Or double-click Restart_AEGIS.bat')
    print()
    print('    2. Hard refresh browser: Ctrl+Shift+R')
    print()
    print('    3. Try SharePoint Connect & Scan with your library URL')
    print()
    print('    4. Check logs/sharepoint.log — it will show which strategy')
    print('       was used and how many files were discovered.')
    print()
    print('  ROLLBACK:')
    print(f'    Backups at: {os.path.abspath(backup_dir)}')
    print('    Copy files back to restore previous version.')
    print()


if __name__ == '__main__':
    main()
