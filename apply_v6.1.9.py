#!/usr/bin/env python3
"""
AEGIS v6.1.8 → v6.1.9 Update Applier
=======================================
SharePoint Subsite (Sub-Web) Detection — API Routing Fix

v6.1.8 added List Items API fallback strategies, but ALL 3 strategies returned
HTTP 500 "Incorrect function (0x80070001)" because the API calls were targeting
the wrong web context.

Root cause: PAL in /sites/AS-ENG/PAL/SITE is a SharePoint subsite (sub-web),
not a regular folder. API calls must target /sites/AS-ENG/PAL/_api/web/...
instead of /sites/AS-ENG/_api/web/...

SharePoint's GetFolderByServerRelativePath resolves folder metadata globally
(works from any web context), which is why validate_folder_path() succeeded.
But /Files, /Folders, and GetList() collections only return data owned by the
CURRENT web — causing empty results or 500 errors.

This update adds _detect_subweb() to both HeadlessSP and REST connectors that
probes intermediate path segments with /_api/web to discover subsites, then
re-routes self.site_url before file listing begins.

Also fixes NLTK averaged_perceptron_tagger missing from health check.

Changes:
- sharepoint_connector.py — _detect_subweb() method + Step 2b integration
  in connect_and_discover() for BOTH connectors
- version.json / static/version.json — Version bump to 6.1.9
- static/js/help-docs.js — v6.1.9 changelog

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.9.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan with your library URL
  4. Check logs/sharepoint.log for subweb detection diagnostics
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
    'sharepoint_connector.py': 'SharePoint connector — subweb detection + API re-routing',
    'version.json': 'Version 6.1.9',
    'static/version.json': 'Version 6.1.9 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.9 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.9'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.9'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            print(f'  [ERROR] Download failed: {e2}')
            return False


def find_python_exe():
    """Find the correct Python executable (embedded or system)."""
    # Check for embedded Python (OneClick installer layout)
    embedded = os.path.join('python', 'python.exe')
    if os.path.isfile(embedded):
        return embedded
    # Fall back to current interpreter
    return sys.executable


def install_nltk_data(python_exe):
    """Download required NLTK data packages."""
    print()
    print('Step 4: Installing NLTK data packages...')

    nltk_packages = [
        'averaged_perceptron_tagger',
        'averaged_perceptron_tagger_eng',
        'punkt',
        'punkt_tab',
        'stopwords',
        'wordnet',
    ]

    # Build a Python command that downloads all NLTK data
    nltk_cmd = '; '.join([f"nltk.download('{pkg}', quiet=True)" for pkg in nltk_packages])
    full_cmd = f'import nltk; {nltk_cmd}; print("NLTK data download complete")'

    import subprocess
    try:
        result = subprocess.run(
            [python_exe, '-c', full_cmd],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print('  [OK] NLTK data packages installed successfully')
            for pkg in nltk_packages:
                print(f'    ✓ {pkg}')
            return True
        else:
            print(f'  [WARN] NLTK download returned non-zero exit code')
            if result.stderr:
                print(f'    stderr: {result.stderr[:200]}')
            # Try installing packages one at a time
            print('  Retrying individual packages...')
            for pkg in nltk_packages:
                try:
                    r = subprocess.run(
                        [python_exe, '-c', f"import nltk; nltk.download('{pkg}', quiet=True)"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    status = '✓' if r.returncode == 0 else '✗'
                    print(f'    {status} {pkg}')
                except Exception:
                    print(f'    ✗ {pkg} (timeout/error)')
            return True
    except FileNotFoundError:
        print(f'  [WARN] Python executable not found: {python_exe}')
        print('         NLTK data can be installed manually:')
        print(f'         {python_exe} -c "import nltk; nltk.download(\'averaged_perceptron_tagger\')"')
        return False
    except subprocess.TimeoutExpired:
        print('  [WARN] NLTK download timed out after 120s')
        print('         This may work on next attempt. Try running:')
        print(f'         {python_exe} -c "import nltk; nltk.download(\'averaged_perceptron_tagger\')"')
        return False
    except Exception as e:
        print(f'  [WARN] NLTK download failed: {e}')
        return False


def main():
    print()
    print('=' * 70)
    print('  AEGIS v6.1.9 Update — SharePoint Subsite Detection Fix')
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
        print('  python apply_v6.1.9.py')
        sys.exit(1)

    print(f'  Install directory: {os.getcwd()}')
    print()

    # ── Step 1: Create timestamped backup ──
    print('Step 1: Backing up current files...')
    backup_dir = os.path.join('backups', f'v6.1.9_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
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

    # ── Step 4: Install NLTK data packages ──
    python_exe = find_python_exe()
    print(f'  Using Python: {python_exe}')
    install_nltk_data(python_exe)

    # ── Summary ──
    print()
    print('=' * 70)
    print('  v6.1.9 Update Summary')
    print('=' * 70)
    print()
    print('  THE FIX:')
    print()
    print('    SharePoint document library under a subsite (sub-web) returned')
    print('    0 files because API calls targeted the wrong web context.')
    print()
    print('    Example: /sites/AS-ENG/PAL/SITE')
    print('      - PAL is a SUBSITE (sub-web), not a regular folder')
    print('      - API calls were going to /sites/AS-ENG/_api/web/...')
    print('      - They SHOULD go to /sites/AS-ENG/PAL/_api/web/...')
    print()
    print('    Why validation passed but listing failed:')
    print('      - GetFolderByServerRelativePath resolves globally (any web)')
    print('      - /Files, /Folders, GetList() are web-scoped (current web only)')
    print('      - validate_folder_path() succeeded → ItemCount=69')
    print('      - But /Files returned 0, GetList returned 500')
    print()
    print('    Solution: _detect_subweb() probes intermediate path segments')
    print('    with /_api/web to discover subsites, then re-routes')
    print('    self.site_url to the correct web context.')
    print()
    print('  NLTK FIX:')
    print()
    print('    Downloaded averaged_perceptron_tagger and other NLTK data')
    print('    packages required by the health check endpoint.')
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
    print('    4. Check logs/sharepoint.log — it will show:')
    print('       - Subweb detection probes and results')
    print('       - The site_url re-route (if subweb found)')
    print('       - File listing from the correct web context')
    print()
    print('  ROLLBACK:')
    print(f'    Backups at: {os.path.abspath(backup_dir)}')
    print('    Copy files back to restore previous version.')
    print()


if __name__ == '__main__':
    main()
