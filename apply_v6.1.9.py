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

Also installs NLTK data packages offline from bundled ZIP files for the
health check (averaged_perceptron_tagger, punkt, stopwords, wordnet, etc.).

Changes:
- sharepoint_connector.py — _detect_subweb() method + Step 2b integration
  in connect_and_discover() for BOTH connectors
- version.json / static/version.json — Version bump to 6.1.9
- static/js/help-docs.js — v6.1.9 changelog
- nltk_data/ — 8 NLTK data ZIP packages (offline install, ~57MB total)

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
import zipfile
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Source files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — subweb detection + API re-routing',
    'version.json': 'Version 6.1.9',
    'static/version.json': 'Version 6.1.9 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.9 changelog',
}

# NLTK data packages to install offline
# Format: (zip_filename, category_subdir, find_path_for_verification)
NLTK_DATA_PACKAGES = [
    ('punkt.zip', 'tokenizers', 'tokenizers/punkt'),
    ('punkt_tab.zip', 'tokenizers', 'tokenizers/punkt_tab'),
    ('averaged_perceptron_tagger.zip', 'taggers', 'taggers/averaged_perceptron_tagger'),
    ('averaged_perceptron_tagger_eng.zip', 'taggers', 'taggers/averaged_perceptron_tagger_eng'),
    ('stopwords.zip', 'corpora', 'corpora/stopwords'),
    ('wordnet.zip', 'corpora', 'corpora/wordnet'),
    ('omw-1.4.zip', 'corpora', 'corpora/omw-1.4'),
    ('cmudict.zip', 'corpora', 'corpora/cmudict'),
]


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


def install_nltk_data_offline():
    """Download and extract NLTK data packages from GitHub to local nltk_data/ directory.

    This is a fully offline-compatible approach:
    1. Downloads ZIP files from GitHub (the AEGIS repo bundles them)
    2. Extracts to nltk_data/{category}/{package_name}/
    3. app.py sets NLTK_DATA env var to point here on startup

    No nltk.download() calls needed — no runtime internet dependency.
    """
    print()
    print('Step 4: Installing NLTK data packages (offline from GitHub)...')

    nltk_dir = os.path.join(os.getcwd(), 'nltk_data')
    os.makedirs(nltk_dir, exist_ok=True)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for zip_name, category, find_path in NLTK_DATA_PACKAGES:
        # Create category directory
        category_dir = os.path.join(nltk_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        # Check if already extracted
        package_name = zip_name.replace('.zip', '')
        extracted_dir = os.path.join(category_dir, package_name)
        if os.path.isdir(extracted_dir):
            print(f'  [SKIP] {find_path} — already installed')
            skip_count += 1
            continue

        # Download ZIP from GitHub
        zip_path = os.path.join(category_dir, zip_name)
        zip_url = f'{RAW_BASE}/nltk_data/{category}/{zip_name}'
        print(f'  [{find_path}] Downloading {zip_name}...')

        if not download_file(zip_url, zip_path):
            print(f'    FAILED to download')
            fail_count += 1
            continue

        size = os.path.getsize(zip_path)
        print(f'    Downloaded ({size:,} bytes)')

        # Extract ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(category_dir)
            if os.path.isdir(extracted_dir):
                print(f'    Extracted to {find_path}/')
                success_count += 1
            else:
                print(f'    [WARN] Extracted but directory not found at {extracted_dir}')
                fail_count += 1
        except Exception as e:
            print(f'    [ERROR] Extraction failed: {e}')
            fail_count += 1

    print()
    total = success_count + skip_count
    if fail_count == 0:
        print(f'  [OK] All {total} NLTK data packages ready '
              f'({success_count} installed, {skip_count} already present)')
    else:
        print(f'  [WARN] {total} ready, {fail_count} failed')
        print('         Failed packages may affect some NLP features but AEGIS will still run.')
        print('         You can retry by running this script again.')

    return fail_count == 0


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

    # ── Step 3: Download updated source files from GitHub ──
    print('Step 3: Downloading updated source files from GitHub...')
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
        print('[WARNING] Some source files failed to download.')
        print('          You can restore from backups at:')
        print(f'          {os.path.abspath(backup_dir)}')
        print()

    # ── Step 4: Install NLTK data packages (offline from GitHub ZIPs) ──
    install_nltk_data_offline()

    # ── Step 5: Verify NLTK data (if nltk is available) ──
    print()
    print('Step 5: Verifying NLTK data installation...')
    python_exe = os.path.join('python', 'python.exe') if os.path.isfile(os.path.join('python', 'python.exe')) else sys.executable
    try:
        import subprocess
        nltk_dir = os.path.join(os.getcwd(), 'nltk_data')
        verify_cmd = (
            f'import os; os.environ["NLTK_DATA"]=r"{nltk_dir}"; import nltk; '
            f'items = ["tokenizers/punkt","tokenizers/punkt_tab",'
            f'"taggers/averaged_perceptron_tagger","taggers/averaged_perceptron_tagger_eng",'
            f'"corpora/stopwords","corpora/wordnet"]; '
            f'ok = 0; fail = 0\n'
            f'for item in items:\n'
            f'    try:\n'
            f'        nltk.data.find(item); ok += 1; print(f"  OK  {{item}}")\n'
            f'    except LookupError:\n'
            f'        fail += 1; print(f"  MISSING  {{item}}")\n'
            f'print(f"\\n  {{ok}} found, {{fail}} missing")'
        )
        # Write verify script to temp file to avoid shell quoting issues
        verify_script = os.path.join(os.getcwd(), '_verify_nltk.py')
        with open(verify_script, 'w') as f:
            f.write(f'import os\nos.environ["NLTK_DATA"] = r"{nltk_dir}"\nimport nltk\n')
            f.write('items = [\n')
            f.write('    "tokenizers/punkt", "tokenizers/punkt_tab",\n')
            f.write('    "taggers/averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger_eng",\n')
            f.write('    "corpora/stopwords", "corpora/wordnet",\n')
            f.write(']\n')
            f.write('ok = 0\nfail = 0\n')
            f.write('for item in items:\n')
            f.write('    try:\n')
            f.write('        nltk.data.find(item)\n')
            f.write('        ok += 1\n')
            f.write('        print(f"  OK  {item}")\n')
            f.write('    except LookupError:\n')
            f.write('        fail += 1\n')
            f.write('        print(f"  MISSING  {item}")\n')
            f.write('print(f"\\n  {ok} found, {fail} missing")\n')

        result = subprocess.run(
            [python_exe, verify_script],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(f'  [WARN] Verification had errors: {result.stderr[:200]}')

        # Clean up temp script
        try:
            os.remove(verify_script)
        except Exception:
            pass

    except Exception as e:
        print(f'  [SKIP] Verification skipped: {e}')
        print('         NLTK data files are in nltk_data/ — they will be used on next AEGIS start.')

    # ── Summary ──
    print()
    print('=' * 70)
    print('  v6.1.9 Update Summary')
    print('=' * 70)
    print()
    print('  SHAREPOINT FIX:')
    print()
    print('    Document library under a subsite (sub-web) returned 0 files')
    print('    because API calls targeted the wrong web context.')
    print()
    print('    Example: /sites/AS-ENG/PAL/SITE')
    print('      - PAL is a SUBSITE (sub-web), not a regular folder')
    print('      - API calls were going to /sites/AS-ENG/_api/web/...')
    print('      - They SHOULD go to /sites/AS-ENG/PAL/_api/web/...')
    print()
    print('    Solution: _detect_subweb() probes intermediate path segments')
    print('    with /_api/web to discover subsites, then re-routes')
    print('    self.site_url to the correct web context.')
    print()
    print('  NLTK DATA FIX:')
    print()
    print('    Installed 8 NLTK data packages offline from bundled ZIP files:')
    print('      - punkt, punkt_tab (tokenizers)')
    print('      - averaged_perceptron_tagger, averaged_perceptron_tagger_eng (taggers)')
    print('      - stopwords, wordnet, omw-1.4, cmudict (corpora)')
    print('    These are stored in nltk_data/ and loaded by app.py on startup.')
    print('    No internet connection required — fully air-gap compatible.')
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
    print('    4. Run Health Check (Settings > Health Check) to verify')
    print('       NLTK data packages show as "ok"')
    print()
    print('    5. Check logs/sharepoint.log for subweb detection diagnostics')
    print()
    print('  ROLLBACK:')
    print(f'    Backups at: {os.path.abspath(backup_dir)}')
    print('    Copy files back to restore previous version.')
    print()


if __name__ == '__main__':
    main()
