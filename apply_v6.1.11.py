#!/usr/bin/env python3
"""
AEGIS v6.1.10 → v6.1.11 Update Applier
========================================
SharePoint File Selection + SP Link Validation Parity

Two major features:

1. FILE SELECTION AFTER SHAREPOINT DISCOVERY
   Instead of auto-scanning every file found on SharePoint, users now get a
   file picker UI with checkboxes, Select All/Deselect All, extension filter
   chips, and a "Scan Selected (N)" button. Only chosen documents are scanned.

   - Backend: discover_only mode in Connect & Scan + new POST /api/review/
     sharepoint-scan-selected endpoint
   - Frontend: _renderSpFileSelector(), _applySpExtensionFilter(),
     _updateSpSelectionCount(), _startSPSelectedScan()

2. SHAREPOINT LINK VALIDATION PARITY
   Documents (DOCX/Excel) containing SharePoint links now get those links
   validated using the SAME auth cascade everywhere — both the Hyperlink
   Validator and Document Review's ComprehensiveHyperlinkChecker.

   Shared utility: sharepoint_link_validator.py
   - Fresh SSO session per URL (thread-safe)
   - SSL bypass for corporate CAs (verify=False)
   - HEAD → GET fallback (SP servers reject HEAD)
   - SharePoint REST API probe
   - Content-Type mismatch detection (login redirect detection)

Changes (11 files):
  - sharepoint_link_validator.py — NEW shared SP URL validation utility
  - comprehensive_hyperlink_checker.py — SP URL detection + shared validator
  - hyperlink_validator/validator.py — Strategy 3c → sharepoint_full
  - routes/review_routes.py — discover_only + scan-selected endpoint
  - static/js/app.js — File picker UI helpers
  - templates/index.html — #sp-file-selector container
  - static/css/features/batch-progress-dashboard.css — File picker styles
  - version.json / static/version.json — v6.1.11
  - static/js/help-docs.js — v6.1.11 release notes
  - CLAUDE.md — Updated patterns + Lesson #156

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.11.py

After applying:
  1. Restart AEGIS (Ctrl+C + python app.py --debug, or Restart_AEGIS.bat)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Test SharePoint Connect & Scan — should show file picker after discovery
  4. Upload a DOCX with SP links to Document Review — SP links should validate
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

# Source files to update (relative path -> description)
FILES = {
    'sharepoint_link_validator.py': 'NEW — Shared SharePoint URL validation utility',
    'comprehensive_hyperlink_checker.py': 'SP URL detection + shared validator integration',
    'hyperlink_validator/validator.py': 'Strategy 3c → sharepoint_full with shared validator',
    'routes/review_routes.py': 'discover_only param + sharepoint-scan-selected endpoint',
    'static/js/app.js': 'File picker UI (renderSpFileSelector, applySpExtensionFilter, etc.)',
    'templates/index.html': '#sp-file-selector container HTML',
    'static/css/features/batch-progress-dashboard.css': 'File picker CSS styles',
    'version.json': 'Version 6.1.11',
    'static/version.json': 'Version 6.1.11 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.11 release notes',
    'CLAUDE.md': 'Updated patterns + Lesson #156',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.11'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.11'})
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
    print('  AEGIS v6.1.11 Update')
    print('  SharePoint File Selection + SP Link Validation Parity')
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
        print('  python apply_v6.1.11.py')
        sys.exit(1)

    print(f'  Install directory: {os.getcwd()}')
    print()

    # ── Step 1: Create timestamped backup ──
    print('Step 1: Backing up current files...')
    backup_dir = os.path.join('backups', f'v6.1.11_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    os.makedirs(backup_dir, exist_ok=True)

    backed_up = 0
    for rel_path in FILES:
        if os.path.isfile(rel_path):
            dest = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(rel_path, dest)
            print(f'  [BACKUP] {rel_path}')
            backed_up += 1
        else:
            print(f'  [NEW] {rel_path} (will be created)')

    print(f'  {backed_up} files backed up to: {backup_dir}')
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
    print()

    # ── Step 3: Download updated source files from GitHub ──
    print('Step 3: Downloading updated source files from GitHub...')
    print(f'  Source: {RAW_BASE}')
    print()
    success_count = 0
    fail_count = 0
    for rel_path, description in FILES.items():
        url = f'{RAW_BASE}/{rel_path}'
        print(f'  [{rel_path}]')
        print(f'    {description}')

        if download_file(url, rel_path, description):
            size = os.path.getsize(rel_path)
            print(f'    ✓ OK ({size:,} bytes)')
            success_count += 1
        else:
            print(f'    ✗ FAILED')
            fail_count += 1

    print()
    if fail_count > 0:
        print(f'[WARNING] {fail_count} file(s) failed to download.')
        print('          You can restore from backups at:')
        print(f'          {os.path.abspath(backup_dir)}')
        print()
    else:
        print(f'  All {success_count} files downloaded successfully.')
    print()

    # ── Summary ──
    print('=' * 70)
    print('  v6.1.11 Update Summary')
    print('=' * 70)
    print()
    print('  FEATURE 1: SharePoint File Selection')
    print()
    print('    After Connect & Scan discovers files on SharePoint, you now')
    print('    see a file picker instead of auto-scanning everything:')
    print('      • Checkboxes for individual file selection')
    print('      • Select All / Deselect All toggle')
    print('      • Extension filter chips (.docx, .pdf, .xlsx, etc.)')
    print('      • "Scan Selected (N)" button')
    print('      • File size and modified date columns')
    print()
    print('  FEATURE 2: SharePoint Link Validation Parity')
    print()
    print('    Documents containing SharePoint links now get validated')
    print('    using the same auth cascade in both Document Review AND')
    print('    the Hyperlink Validator:')
    print('      • Fresh SSO session per URL (thread-safe)')
    print('      • SSL bypass for corporate CA certificates')
    print('      • HEAD → GET fallback (SP servers reject HEAD)')
    print('      • SharePoint REST API probe')
    print('      • Content-Type mismatch detection (login redirects)')
    print()
    print('  NEXT STEPS:')
    print()
    print('    1. Restart AEGIS:')
    print('       Ctrl+C the running server, then: python app.py --debug')
    print('       Or double-click Restart_AEGIS.bat')
    print()
    print('    2. Hard refresh browser: Ctrl+Shift+R')
    print()
    print('    3. Test SharePoint Connect & Scan:')
    print('       - Paste your SharePoint URL')
    print('       - Click Connect & Scan')
    print('       - You should see the file picker (not auto-scan)')
    print('       - Select files and click "Scan Selected"')
    print()
    print('    4. Test SP link validation:')
    print('       - Upload a DOCX containing SharePoint links')
    print('       - Run Document Review')
    print('       - SP links should show SSL_WARNING or AUTH_REQUIRED')
    print('         (not BROKEN)')
    print()
    print('  ROLLBACK:')
    print(f'    Backups at: {os.path.abspath(backup_dir)}')
    print('    Copy files back to restore previous version.')
    print()


if __name__ == '__main__':
    main()
