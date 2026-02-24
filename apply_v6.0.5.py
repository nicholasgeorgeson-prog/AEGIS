#!/usr/bin/env python3
"""
AEGIS v6.0.5 Update Applier
============================
SharePoint Online Modern Auth — Preemptive SSPI + MSAL OAuth 2.0

Downloads updated files from GitHub and applies them to the AEGIS installation.
Creates timestamped backups of each file before overwriting.

Changes in v6.0.5:
- sharepoint_connector.py — Multi-strategy auth: preemptive SSPI Negotiate + MSAL OAuth 2.0 + standard Negotiate
- requirements.txt — Added msal>=1.20.0 and PyJWT>=2.0.0
- version.json / static/version.json — Version bump to 6.0.5
- CLAUDE.md — Lesson 139: SharePoint Online legacy auth deprecation
- static/js/help-docs.js — Changelog entry and SharePoint auth documentation
- wheels/msal-1.35.0-py3-none-any.whl — MSAL wheel for offline install
- wheels/pyjwt-2.11.0-py3-none-any.whl — PyJWT wheel for offline install

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.0.5.py

After applying:
  1. Restart AEGIS (double-click restart_aegis.sh or Ctrl+C + python3 app.py --debug)
  2. On Windows: pip install msal PyJWT (or pip install --no-index --find-links=wheels msal PyJWT)
  3. Hard refresh browser (Ctrl+Shift+R)
"""

import os
import sys
import shutil
import ssl
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector with modern auth',
    'requirements.txt': 'Updated dependencies (msal, PyJWT)',
    'version.json': 'Version 6.0.5',
    'static/version.json': 'Version 6.0.5 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 139',
    'static/js/help-docs.js': 'Help docs with v6.0.5 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.5'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            mode = 'wb' if is_binary else 'wb'
            with open(dest_path, mode) as f:
                f.write(data)
            return True
    except Exception as e:
        print(f'  [ERROR] Download failed: {e}')
        # Try without SSL verification
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.0.5'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            print(f'  [ERROR] SSL fallback also failed: {e2}')
            return False


def main():
    print('=' * 60)
    print('  AEGIS v6.0.5 Update Applier')
    print('  SharePoint Online Modern Auth')
    print('=' * 60)
    print()

    # Verify we're in the correct directory
    if not os.path.exists('app.py') or not os.path.exists('static'):
        print('[ERROR] This script must be run from the AEGIS installation directory.')
        print('        Expected to find app.py and static/ folder.')
        print(f'        Current directory: {os.getcwd()}')
        sys.exit(1)

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.0.5_{timestamp}')
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

    # Summary
    print('=' * 60)
    print(f'  Update complete: {success_count} succeeded, {fail_count} failed')
    print('=' * 60)
    print()
    print('Next steps:')
    print('  1. Restart AEGIS server (python3 app.py --debug)')
    print('  2. On Windows, install new dependencies:')
    print('     pip install --no-index --find-links=wheels msal PyJWT')
    print('     (or: pip install msal PyJWT  if internet available)')
    print('  3. Hard refresh browser (Ctrl+Shift+R)')
    print()
    print('  Optional: Configure OAuth for SharePoint Online:')
    print('  Add to config.json:')
    print('    "sharepoint_oauth": {')
    print('      "client_id": "<your-azure-app-id>",')
    print('      "tenant_id": "<your-tenant-id>",')
    print('      "client_secret": "<your-client-secret>"')
    print('    }')
    print()
    if fail_count > 0:
        print(f'  [WARN] {fail_count} file(s) failed to download.')
        print('  You may need to download them manually from GitHub.')
    print(f'  Backups saved to: {backup_dir}')


if __name__ == '__main__':
    main()
