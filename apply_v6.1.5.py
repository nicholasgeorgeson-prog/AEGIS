#!/usr/bin/env python3
"""
AEGIS v6.1.4 → v6.1.5 Update Applier
=======================================
Fully Offline Chromium Browser Install + Auth Allowlist Dedup

The v6.1.4 update fixed the HeadlessSPConnector authentication logic,
but the headless browser still failed because the Playwright Chromium
browser BINARY was never installed. On air-gapped / restricted networks,
'playwright install chromium' cannot download from the internet.

This update installs the Chromium headless shell COMPLETELY OFFLINE:
  1. Downloads chromium-headless-shell-win64.zip from the AEGIS GitHub
     Release (same as torch, models, etc.)
  2. Extracts it to the correct Playwright browser directory
  3. Creates marker files so Playwright recognises it as installed

Changes:
- sharepoint_connector.py — Deduplicated auth-server-allowlist entries,
  added PLAYWRIGHT_BROWSERS_PATH auto-detection for offline installs
- hyperlink_validator/headless_validator.py — Same PLAYWRIGHT_BROWSERS_PATH
- version.json / static/version.json — Version bump to 6.1.5
- static/js/help-docs.js — v6.1.5 changelog

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.5.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan — check logs/sharepoint.log for diagnostics
"""

import os
import sys
import shutil
import ssl
import subprocess
import zipfile
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# GitHub Release for large binaries (same release as torch, models, etc.)
RELEASE_TAG = 'v5.9.21'
RELEASE_BASE = f'https://github.com/{REPO}/releases/download/{RELEASE_TAG}'

# Chromium headless shell details (must match Playwright version)
# These come from {playwright_package}/driver/package/browsers.json
CHROMIUM_REVISION = '1208'
CHROMIUM_VERSION = '145.0.7632.6'
CHROMIUM_ZIP = 'chromium-headless-shell-win64.zip'
CHROMIUM_DIR_NAME = f'chromium_headless_shell-{CHROMIUM_REVISION}'
CHROMIUM_EXE_SUBDIR = 'chrome-headless-shell-win64'
CHROMIUM_EXE_NAME = 'chrome-headless-shell.exe'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — deduplicated auth allowlist + offline browser path',
    'hyperlink_validator/headless_validator.py': 'Headless validator — offline browser path support',
    'version.json': 'Version 6.1.5',
    'static/version.json': 'Version 6.1.5 (static copy)',
    'static/js/help-docs.js': 'Help docs with v6.1.5 changelog',
}


def create_ssl_context():
    """Create SSL context with fallback for certificate issues."""
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        ctx = ssl._create_unverified_context()
        return ctx


def _cleanup_partial(path):
    """Remove a partially downloaded file if it exists."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def download_file(url, dest_path, description=''):
    """Download a file from URL to dest_path with SSL fallback.
    Cleans up partial downloads on failure."""
    ctx = create_ssl_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.5'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        _cleanup_partial(dest_path)
        # SSL fallback
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.5'})
            with urllib.request.urlopen(req, context=ctx) as response:
                data = response.read()
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e2:
            _cleanup_partial(dest_path)
            print(f'  [ERROR] Download failed: {e2}')
            return False


def download_large_file(url, dest_path, expected_size_mb=0):
    """Download a large file with progress reporting and SSL fallback.
    Prints progress at 10% intervals to avoid flooding the console.
    Cleans up partial downloads on failure."""
    for attempt in range(2):
        ctx = create_ssl_context() if attempt == 0 else ssl._create_unverified_context()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.5'})
            with urllib.request.urlopen(req, context=ctx) as response:
                total = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 512 * 1024  # 512KB chunks (fewer iterations)
                last_pct_reported = -10  # Track last reported percentage
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Report progress at 10% intervals only
                        if total > 0:
                            pct = int(downloaded * 100 / total)
                            if pct >= last_pct_reported + 10:
                                last_pct_reported = (pct // 10) * 10
                                mb_done = downloaded / (1024 * 1024)
                                mb_total = total / (1024 * 1024)
                                print(f'    [{last_pct_reported:3d}%] {mb_done:.1f} / {mb_total:.1f} MB')
                        else:
                            mb_done = downloaded / (1024 * 1024)
                            # Report every ~10 MB when total unknown
                            mb_int = int(mb_done)
                            if mb_int > 0 and mb_int % 10 == 0 and mb_int != getattr(download_large_file, '_last_mb', -1):
                                download_large_file._last_mb = mb_int
                                print(f'    {mb_done:.0f} MB downloaded...')
                # Final line
                mb_final = downloaded / (1024 * 1024)
                print(f'    [100%] {mb_final:.1f} MB — download complete')
                return True
        except Exception as e:
            _cleanup_partial(dest_path)
            if attempt == 0:
                continue  # Try SSL fallback
            print(f'  [ERROR] Download failed: {e}')
            return False
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


def verify_playwright_package(python_exe):
    """Verify Playwright Python package is installed (NOT the browser binary)."""
    try:
        result = subprocess.run(
            [python_exe, '-c', 'from playwright.sync_api import sync_playwright; print("PLAYWRIGHT_OK")'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and 'PLAYWRIGHT_OK' in result.stdout:
            return True
        return False
    except Exception:
        return False


def get_playwright_browsers_dir(python_exe):
    """
    Determine where Playwright expects browser binaries.
    Priority: PLAYWRIGHT_BROWSERS_PATH env var → default location
    """
    # Check env var first
    env_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
    if env_path and env_path != '0':
        return env_path

    # Default: %LOCALAPPDATA%\ms-playwright on Windows
    if sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            return os.path.join(local_app_data, 'ms-playwright')

    # macOS/Linux default
    home = os.path.expanduser('~')
    if sys.platform == 'darwin':
        return os.path.join(home, 'Library', 'Caches', 'ms-playwright')
    else:
        return os.path.join(home, '.cache', 'ms-playwright')


def find_chromium_zip_locally():
    """
    Search for the Chromium zip file in common local locations.
    This supports truly air-gapped installs where the user has manually
    copied the zip file to the AEGIS directory.
    """
    search_paths = [
        # Same directory as the apply script
        os.path.join(os.getcwd(), CHROMIUM_ZIP),
        # In a browsers/ subdirectory
        os.path.join(os.getcwd(), 'browsers', CHROMIUM_ZIP),
        # In packaging/browsers/
        os.path.join(os.getcwd(), 'packaging', 'browsers', CHROMIUM_ZIP),
        # In wheels/ (alongside other large binaries)
        os.path.join(os.getcwd(), 'wheels', CHROMIUM_ZIP),
        # In packaging/wheels/
        os.path.join(os.getcwd(), 'packaging', 'wheels', CHROMIUM_ZIP),
    ]

    for path in search_paths:
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > 50:  # Sanity check — real zip is ~109MB
                print(f'  [FOUND] Local Chromium zip: {path} ({size_mb:.1f} MB)')
                return path
            else:
                print(f'  [SKIP] {path} too small ({size_mb:.1f} MB) — probably not the full binary')

    return None


def install_chromium_offline(python_exe):
    """
    Install Chromium headless shell binary for Playwright — FULLY OFFLINE.

    Strategy:
      1. Check if Chromium binary already exists at the expected path
      2. Look for the zip file locally (user may have copied it)
      3. Download the zip from GitHub Release (same server as torch, models)
      4. Extract to the correct Playwright browser directory
      5. Create marker files (DEPENDENCIES_VALIDATED, INSTALLATION_COMPLETE)

    Returns: (success: bool, exe_path: str or None)
    """
    browsers_dir = get_playwright_browsers_dir(python_exe)
    chromium_dir = os.path.join(browsers_dir, CHROMIUM_DIR_NAME)
    exe_path = os.path.join(chromium_dir, CHROMIUM_EXE_SUBDIR, CHROMIUM_EXE_NAME)

    print(f'  Playwright browsers directory: {browsers_dir}')
    print(f'  Expected Chromium path: {exe_path}')

    # ── Check if already installed ──
    if os.path.isfile(exe_path):
        print(f'  [OK] Chromium binary already exists!')
        return True, exe_path

    print(f'  [MISSING] Chromium binary not found — installing offline...')
    print()

    # ── Find or download the zip ──
    zip_path = find_chromium_zip_locally()

    if not zip_path:
        # Download from GitHub Release
        download_url = f'{RELEASE_BASE}/{CHROMIUM_ZIP}'
        zip_path = os.path.join(os.getcwd(), CHROMIUM_ZIP)
        print(f'  Downloading Chromium from GitHub Release...')
        print(f'    URL: {download_url}')
        print(f'    (This is ~109 MB — same server as torch, models, etc.)')
        print()

        if not download_large_file(download_url, zip_path, expected_size_mb=109):
            # download_large_file already cleans up partial files
            _cleanup_partial(zip_path)  # belt-and-suspenders
            print(f'  [FAIL] Could not download Chromium zip')
            print()
            print(f'  For air-gapped installs, manually copy the file to:')
            print(f'    {os.path.join(os.getcwd(), CHROMIUM_ZIP)}')
            print()
            print(f'  Download URL:')
            print(f'    {download_url}')
            return False, None

    # ── Verify the zip ──
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f'  Chromium zip: {zip_path} ({zip_size_mb:.1f} MB)')

    if not zipfile.is_zipfile(zip_path):
        print(f'  [ERROR] File is not a valid zip archive!')
        return False, None

    # ── Extract to Playwright's browser directory ──
    print(f'  Extracting to: {chromium_dir}')
    os.makedirs(chromium_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # List contents to verify structure
            names = zf.namelist()
            print(f'    Archive contains {len(names)} files')

            # The zip typically has chrome-headless-shell-win64/ as top-level dir
            zf.extractall(chromium_dir)
            print(f'    [OK] Extracted successfully')
    except Exception as e:
        print(f'    [ERROR] Extraction failed: {e}')
        # Clean up partially extracted directory
        try:
            if os.path.isdir(chromium_dir):
                shutil.rmtree(chromium_dir, ignore_errors=True)
                print(f'    [CLEANUP] Removed partial extraction: {chromium_dir}')
        except Exception:
            pass
        return False, None

    # ── Create Playwright marker files ──
    # These empty files tell Playwright the browser is properly installed
    markers = ['DEPENDENCIES_VALIDATED', 'INSTALLATION_COMPLETE']
    for marker in markers:
        marker_path = os.path.join(chromium_dir, marker)
        try:
            with open(marker_path, 'w') as f:
                pass  # Empty file
            print(f'    [OK] Created {marker}')
        except Exception as e:
            print(f'    [WARN] Could not create {marker}: {e}')

    # ── Verify the exe exists after extraction ──
    if os.path.isfile(exe_path):
        print()
        print(f'  [OK] Chromium binary installed successfully!')
        print(f'       Path: {exe_path}')

        # Clean up the zip to save disk space
        if zip_path.startswith(os.getcwd()):
            try:
                os.remove(zip_path)
                print(f'  [OK] Cleaned up {CHROMIUM_ZIP} ({zip_size_mb:.0f} MB freed)')
            except Exception:
                pass

        return True, exe_path
    else:
        # The zip might have a different internal structure
        # Let's search for the exe in the extraction directory
        print(f'  [WARN] Expected exe not at: {exe_path}')
        print(f'  Searching for chrome-headless-shell.exe...')

        for root, dirs, files in os.walk(chromium_dir):
            for f in files:
                if f == CHROMIUM_EXE_NAME or f == 'chrome-headless-shell':
                    found_path = os.path.join(root, f)
                    print(f'  [FOUND] {found_path}')
                    return True, found_path

        print(f'  [ERROR] Could not find {CHROMIUM_EXE_NAME} after extraction')
        print(f'  Contents of {chromium_dir}:')
        try:
            for item in os.listdir(chromium_dir):
                item_path = os.path.join(chromium_dir, item)
                if os.path.isdir(item_path):
                    print(f'    [DIR]  {item}/')
                    for sub in os.listdir(item_path)[:5]:
                        print(f'           └── {sub}')
                else:
                    print(f'    [FILE] {item}')
        except Exception:
            pass

        return False, None


def pip_install(python_exe, packages):
    """Install packages with offline-first, online fallback."""
    wheels_dirs = []
    for d in ['wheels', os.path.join('packaging', 'wheels')]:
        if os.path.isdir(d):
            wheels_dirs.append(d)

    for pkg in packages:
        # Try offline first
        if wheels_dirs:
            cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location']
            for wd in wheels_dirs:
                cmd.extend(['--no-index', '--find-links', wd])
            cmd.append(pkg)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f'    [OK] {pkg} (offline)')
                continue

        # Try online
        cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location', pkg]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f'    [OK] {pkg} (online)')
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            print(f'    [FAIL] {pkg} — {err[:100]}')


def main():
    print('=' * 65)
    print('  AEGIS v6.1.5 Update Applier')
    print('  Offline Chromium Browser Install + Allowlist Dedup')
    print('=' * 65)
    print()

    # Verify we're in the correct directory
    if not os.path.exists('app.py') or not os.path.exists('static'):
        print('[ERROR] This script must be run from the AEGIS installation directory.')
        print('        Expected to find app.py and static/ folder.')
        print(f'        Current directory: {os.getcwd()}')
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════
    # STEP 0: Find the correct Python
    # ═══════════════════════════════════════════════════════════
    print('[STEP 0] Finding AEGIS Python...')
    python_exe = find_aegis_python()
    try:
        py_version = subprocess.run(
            [python_exe, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'],
            capture_output=True, text=True, timeout=10
        )
        if py_version.returncode == 0:
            print(f'  Python version: {py_version.stdout.strip()}')
    except Exception:
        pass
    print()

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.1.5_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[INFO] Backup directory: {backup_dir}')
    print()

    # Ensure directories exist
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('hyperlink_validator', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # ═══════════════════════════════════════════════════════════
    # STEP 1: Download updated source files
    # ═══════════════════════════════════════════════════════════
    print('[STEP 1] Downloading updated source files...')
    success_count = 0
    fail_count = 0

    for rel_path, description in FILES.items():
        print(f'  Updating {rel_path} ({description})...')

        # Backup existing file
        if os.path.exists(rel_path):
            backup_path = os.path.join(backup_dir, rel_path.replace('/', os.sep))
            backup_parent = os.path.dirname(backup_path)
            if backup_parent:
                os.makedirs(backup_parent, exist_ok=True)
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

    # ═══════════════════════════════════════════════════════════
    # STEP 2: Ensure Playwright Python package is installed
    # ═══════════════════════════════════════════════════════════
    print('[STEP 2] Checking Playwright Python package...')
    pw_package_ok = verify_playwright_package(python_exe)
    if pw_package_ok:
        print('  [OK] Playwright Python package is installed')
    else:
        print('  [MISSING] Installing playwright package...')
        pip_install(python_exe, ['playwright'])
        pw_package_ok = verify_playwright_package(python_exe)
        if pw_package_ok:
            print('  [OK] Playwright Python package installed successfully')
        else:
            print('  [FAIL] Could not install Playwright Python package')
            print('         Try manually:')
            print(f'           "{python_exe}" -m pip install playwright')
    print()

    # ═══════════════════════════════════════════════════════════
    # STEP 3: Install Chromium browser binary (OFFLINE)
    # ═══════════════════════════════════════════════════════════
    print('[STEP 3] Installing Chromium browser binary (OFFLINE)...')
    print()
    print('  ┌──────────────────────────────────────────────────────────┐')
    print('  │ This installs the Chromium headless browser OFFLINE.     │')
    print('  │                                                          │')
    print('  │ Strategy:                                                │')
    print('  │  1. Look for chromium zip in local AEGIS directory       │')
    print('  │  2. Download from AEGIS GitHub Release if not found      │')
    print('  │  3. Extract to Playwright\'s browser directory            │')
    print('  │  4. Create validation marker files                       │')
    print('  │                                                          │')
    print('  │ No internet to playwright.azureedge.net is needed.       │')
    print('  └──────────────────────────────────────────────────────────┘')
    print()

    chromium_ok = False
    chromium_exe = None

    if pw_package_ok:
        chromium_ok, chromium_exe = install_chromium_offline(python_exe)
    else:
        print('  [SKIP] Cannot install Chromium — Playwright package not available')

    print()

    # ═══════════════════════════════════════════════════════════
    # STEP 4: Verify auth stack
    # ═══════════════════════════════════════════════════════════
    print('[STEP 4] Verifying auth stack...')
    msal_ok = verify_import(python_exe, 'msal', 'MSAL (OAuth 2.0)')
    requests_ok = verify_import(python_exe, 'requests', 'requests')
    if sys.platform == 'win32':
        sspi_ok = verify_import(python_exe, 'sspi', 'sspi (pywin32)')
    else:
        sspi_ok = None
    print()

    # ═══════════════════════════════════════════════════════════
    # STEP 5: Verify v6.1.5 changes
    # ═══════════════════════════════════════════════════════════
    print('[STEP 5] Verifying v6.1.5 changes...')

    # Check for deduplication in sharepoint_connector.py
    sp_dedup = False
    sp_3phase = False
    sp_filelog = False
    try:
        with open('sharepoint_connector.py', 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        sp_dedup = '_seen = set()' in content or '_seen' in content
        sp_3phase = 'Phase 1:' in content and 'Phase 2:' in content and 'Phase 3:' in content
        sp_filelog = 'sharepoint.log' in content

        if sp_dedup:
            print('  [OK] Auth allowlist deduplication present')
        else:
            print('  [WARN] Auth allowlist deduplication not detected')
        if sp_3phase:
            print('  [OK] 3-phase federated SSO authentication present')
        else:
            print('  [FAIL] 3-phase auth NOT found in sharepoint_connector.py')
        if sp_filelog:
            print('  [OK] File logging to sharepoint.log configured')
        else:
            print('  [FAIL] File logging NOT found in sharepoint_connector.py')
    except Exception as e:
        print(f'  [FAIL] Could not verify: {e}')

    # Check version
    try:
        import json
        with open('version.json', 'r') as f:
            v = json.load(f)
        ver = v.get('version', 'unknown')
        if ver == '6.1.5':
            print(f'  [OK] version.json: {ver}')
        else:
            print(f'  [WARN] version.json: {ver} (expected 6.1.5)')
    except Exception as e:
        print(f'  [FAIL] version.json: {e}')
    print()

    # ═══════════════════════════════════════════════════════════
    # COMPREHENSIVE SUMMARY
    # ═══════════════════════════════════════════════════════════
    print('=' * 65)
    print('  UPDATE SUMMARY')
    print('=' * 65)
    print()

    if fail_count == 0:
        print(f'  FILES:  {success_count}/{success_count} downloaded successfully')
    else:
        print(f'  FILES:  {success_count} succeeded, {fail_count} FAILED')
    print()

    print('  AUTH STACK:')
    print(f'    requests:              {"OK" if requests_ok else "NOT INSTALLED"}')
    print(f'    MSAL (OAuth 2.0):      {"OK" if msal_ok else "NOT INSTALLED"}')
    if sys.platform == 'win32':
        print(f'    pywin32 (SSPI):        {"OK" if sspi_ok else "NOT INSTALLED"}')
    print(f'    Playwright package:    {"OK" if pw_package_ok else "NOT INSTALLED"}')
    print(f'    Chromium binary:       {"INSTALLED" if chromium_ok else "*** NOT INSTALLED ***"}')
    if chromium_exe:
        print(f'    Chromium path:         {chromium_exe}')
    print()

    print('  v6.1.5 FIXES:')
    print(f'    Auth allowlist dedup:  {"PRESENT" if sp_dedup else "MISSING"}')
    print(f'    3-phase federated SSO: {"PRESENT" if sp_3phase else "MISSING"}')
    print(f'    SharePoint file log:   {"PRESENT" if sp_filelog else "MISSING"}')
    print(f'    Offline Chromium:      {"INSTALLED" if chromium_ok else "NOT INSTALLED"}')
    print()

    all_ok = (fail_count == 0 and chromium_ok and sp_3phase and sp_filelog)
    if all_ok:
        print('  STATUS: UPDATE APPLIED SUCCESSFULLY')
    elif chromium_ok:
        print('  STATUS: UPDATE APPLIED WITH MINOR ISSUES — see details above')
    else:
        print('  STATUS: CHROMIUM NOT INSTALLED — see manual steps below')
    print()

    print('=' * 65)
    print()

    # What changed
    print("What changed in v6.1.5:")
    print()
    print("  v6.1.4 fixed the headless browser SSO authentication logic,")
    print("  but Playwright's Chromium browser binary was never installed.")
    print()
    print("  On air-gapped networks, 'playwright install chromium' cannot")
    print("  reach playwright.azureedge.net to download the binary.")
    print()
    print("  v6.1.5 fixes this with fully offline Chromium installation:")
    print("    1. The binary is hosted on the AEGIS GitHub Release")
    print("    2. The apply script extracts it to the correct location")
    print("    3. Marker files tell Playwright it's installed")
    print("    4. No internet to playwright.azureedge.net needed")
    print()

    # Next steps
    print('NEXT STEPS:')
    print()
    print('  1. Restart AEGIS:')
    print('     - Double-click Restart_AEGIS.bat')
    print('     - Or: Ctrl+C then: python app.py --debug')
    print()
    print('  2. Hard refresh browser: Ctrl+Shift+R')
    print()
    print('  3. Try Connect & Scan with your SharePoint URL')
    print()
    print('  4. If it fails, check logs/sharepoint.log for detailed diagnostics')
    print()

    if not chromium_ok:
        print('  MANUAL CHROMIUM INSTALL (if automatic install failed):')
        print()
        print(f'  Option A — Download zip and place in AEGIS directory:')
        print(f'    1. Download: {RELEASE_BASE}/{CHROMIUM_ZIP}')
        print(f'    2. Copy to: {os.path.join(os.getcwd(), CHROMIUM_ZIP)}')
        print(f'    3. Re-run: python apply_v6.1.5.py')
        print()
        print(f'  Option B — Manual extraction:')
        print(f'    1. Download the same zip file')
        print(f'    2. Extract to: {os.path.join(get_playwright_browsers_dir(python_exe), CHROMIUM_DIR_NAME)}')
        print(f'    3. Create empty files in the extraction directory:')
        print(f'       - DEPENDENCIES_VALIDATED')
        print(f'       - INSTALLATION_COMPLETE')
        print()


if __name__ == '__main__':
    main()
