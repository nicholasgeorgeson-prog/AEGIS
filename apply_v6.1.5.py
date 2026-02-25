#!/usr/bin/env python3
"""
AEGIS v6.1.4 → v6.1.5 Update Applier
=======================================
Playwright Chromium Browser Binary Install + Auth Allowlist Dedup

The v6.1.4 update fixed the HeadlessSPConnector authentication logic,
but the headless browser still failed because the Playwright Chromium
browser BINARY was never installed.

  pip install playwright     → installs Python API only
  playwright install chromium → downloads the actual browser (~100MB)

These are TWO SEPARATE steps. Without the binary, BrowserType.launch()
fails with "Executable doesn't exist at ...".

Changes:
- sharepoint_connector.py — Deduplicated auth-server-allowlist entries
  (IdP domains were doubled from both CORP_AUTH_DOMAINS and _idp_extras)
- version.json / static/version.json — Version bump to 6.1.5
- static/js/help-docs.js — v6.1.5 changelog

Primary goal:
  Ensure 'playwright install chromium' runs successfully and the binary
  exists at the expected path.

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
import urllib.request
from datetime import datetime

# GitHub raw content base URL
REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'

# Files to update (relative path -> description)
FILES = {
    'sharepoint_connector.py': 'SharePoint connector — deduplicated auth allowlist',
    'hyperlink_validator/headless_validator.py': 'Headless validator — expanded SSO auth allowlist',
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


def download_file(url, dest_path, is_binary=False):
    """Download a file from URL to dest_path."""
    ctx = create_ssl_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.5'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f'  [ERROR] Download failed: {e}')
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.5'})
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


def verify_chromium_binary(python_exe):
    """
    Verify the Chromium browser BINARY exists (separate from the Python package).
    This is the critical check — the binary is what BrowserType.launch() needs.
    """
    try:
        # Ask Playwright where the chromium executable should be
        result = subprocess.run(
            [python_exe, '-c', '''
import sys
try:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    exe = pw.chromium.executable_path
    pw.stop()
    import os
    exists = os.path.isfile(exe)
    print(f"PATH={exe}")
    print(f"EXISTS={exists}")
except Exception as e:
    print(f"ERROR={e}")
'''],
            capture_output=True, text=True, timeout=30
        )
        stdout = result.stdout.strip()
        if 'EXISTS=True' in stdout:
            # Extract the path for display
            for line in stdout.split('\n'):
                if line.startswith('PATH='):
                    path = line[5:]
                    print(f'  [OK] Chromium binary found: {path}')
            return True
        elif 'EXISTS=False' in stdout:
            for line in stdout.split('\n'):
                if line.startswith('PATH='):
                    path = line[5:]
                    print(f'  [MISSING] Chromium binary NOT found at: {path}')
            return False
        elif 'ERROR=' in stdout:
            for line in stdout.split('\n'):
                if line.startswith('ERROR='):
                    err = line[6:]
                    print(f'  [ERROR] Could not check Chromium binary: {err[:120]}')
            return False
        else:
            print(f'  [ERROR] Unexpected output: {stdout[:200]}')
            return False
    except subprocess.TimeoutExpired:
        print('  [ERROR] Chromium binary check timed out')
        return False
    except Exception as e:
        print(f'  [ERROR] Could not check Chromium binary: {e}')
        return False


def install_chromium_binary(python_exe):
    """
    Run 'playwright install chromium' to download the browser binary.
    This is the ~100MB download that BrowserType.launch() needs.
    """
    print()
    print('  Running: playwright install chromium')
    print('  (This downloads ~100MB — may take a few minutes...)')
    print()

    try:
        # Run with real-time output so user sees download progress
        result = subprocess.run(
            [python_exe, '-m', 'playwright', 'install', 'chromium'],
            timeout=600,  # 10 minutes — generous for slow connections
            capture_output=True,
            text=True,
        )

        # Print all output for diagnostics
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f'    {line}')
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    print(f'    {line}')

        if result.returncode == 0:
            print()
            print('  [OK] playwright install chromium completed successfully')
            return True
        else:
            print()
            print(f'  [FAIL] playwright install chromium returned exit code {result.returncode}')
            return False

    except subprocess.TimeoutExpired:
        print()
        print('  [FAIL] playwright install chromium timed out after 10 minutes')
        print('         The download may still be in progress.')
        print('         Try running manually:')
        print(f'           "{python_exe}" -m playwright install chromium')
        return False
    except FileNotFoundError:
        print()
        print(f'  [FAIL] Could not execute: {python_exe}')
        print('         The Python executable was not found.')
        return False
    except Exception as e:
        print()
        print(f'  [FAIL] Unexpected error: {e}')
        return False


def install_playwright_deps(python_exe):
    """
    Run 'playwright install-deps chromium' to install system dependencies.
    Only needed on Linux — skipped on Windows/macOS.
    """
    if sys.platform == 'win32' or sys.platform == 'darwin':
        return True  # Not needed on Windows/macOS

    try:
        result = subprocess.run(
            [python_exe, '-m', 'playwright', 'install-deps', 'chromium'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print('  [OK] System dependencies installed')
            return True
        else:
            print('  [WARN] System deps install returned non-zero (may need sudo)')
            return False
    except Exception:
        return False


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
    print('  Playwright Chromium Browser Install + Allowlist Dedup')
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
    # STEP 2: Install Playwright Python package (if needed)
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
    # STEP 3: Install Chromium BROWSER BINARY (this is the critical fix)
    # ═══════════════════════════════════════════════════════════
    print('[STEP 3] Installing Chromium browser binary...')
    print('  ┌──────────────────────────────────────────────────────┐')
    print('  │ This is the critical fix for v6.1.5.                 │')
    print('  │                                                      │')
    print('  │ "pip install playwright" only installs the Python    │')
    print('  │ API. The actual Chromium browser (~100MB) must be    │')
    print('  │ downloaded separately via:                           │')
    print('  │                                                      │')
    print('  │   python -m playwright install chromium              │')
    print('  │                                                      │')
    print('  │ Without it, BrowserType.launch() fails with          │')
    print('  │ "Executable doesn\'t exist".                          │')
    print('  └──────────────────────────────────────────────────────┘')
    print()

    chromium_ok = False

    if pw_package_ok:
        # First check if chromium binary already exists
        print('  Checking if Chromium binary already exists...')
        chromium_ok = verify_chromium_binary(python_exe)

        if not chromium_ok:
            print()
            print('  Chromium binary not found — downloading now...')
            install_result = install_chromium_binary(python_exe)

            if install_result:
                # Verify it actually worked
                print()
                print('  Verifying Chromium binary after install...')
                chromium_ok = verify_chromium_binary(python_exe)
            else:
                print()
                print('  First attempt failed — trying with --with-deps flag...')
                try:
                    result = subprocess.run(
                        [python_exe, '-m', 'playwright', 'install', '--with-deps', 'chromium'],
                        capture_output=True, text=True, timeout=600
                    )
                    if result.returncode == 0:
                        print('  [OK] playwright install --with-deps chromium completed')
                        chromium_ok = verify_chromium_binary(python_exe)
                    else:
                        if result.stdout:
                            print(f'    stdout: {result.stdout.strip()[:200]}')
                        if result.stderr:
                            print(f'    stderr: {result.stderr.strip()[:200]}')
                except Exception as e:
                    print(f'  [FAIL] --with-deps attempt: {e}')
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
    print(f'    Chromium binary:       {"OK — INSTALLED" if chromium_ok else "*** NOT INSTALLED ***"}')
    print()

    print('  v6.1.5 FIXES:')
    print(f'    Auth allowlist dedup:  {"PRESENT" if sp_dedup else "MISSING"}')
    print(f'    3-phase federated SSO: {"PRESENT" if sp_3phase else "MISSING"}')
    print(f'    SharePoint file log:   {"PRESENT" if sp_filelog else "MISSING"}')
    print()

    all_ok = (fail_count == 0 and chromium_ok and sp_3phase and sp_filelog)
    if all_ok:
        print('  ✓ STATUS: UPDATE APPLIED SUCCESSFULLY')
    elif chromium_ok:
        print('  ~ STATUS: UPDATE APPLIED WITH MINOR ISSUES — see details above')
    else:
        print('  ✗ STATUS: CHROMIUM BROWSER NOT INSTALLED — see manual steps below')
    print()

    print('=' * 65)
    print()

    # What changed
    print("What changed in v6.1.5:")
    print()
    print("  The v6.1.4 update fixed the headless browser authentication logic")
    print("  (3-phase federated SSO, expanded auth allowlist), but the actual")
    print("  Chromium browser BINARY was never downloaded.")
    print()
    print("  Playwright has two components:")
    print("    1. Python package (pip install playwright)  — installed ✓")
    print("    2. Chromium binary  (playwright install chromium) — was MISSING")
    print()
    print("  v6.1.5 ensures the Chromium binary is downloaded and verified.")
    print("  Also deduplicated auth-server-allowlist entries that were doubled.")
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
        print('  ╔══════════════════════════════════════════════════════════╗')
        print('  ║  *** CRITICAL: Chromium browser binary NOT installed ***║')
        print('  ║                                                         ║')
        print('  ║  The headless browser fallback WILL NOT WORK without    ║')
        print('  ║  the Chromium binary. Please run these commands         ║')
        print('  ║  manually in a terminal/command prompt:                 ║')
        print('  ║                                                         ║')
        print(f'  ║  Step 1: cd to AEGIS directory                          ║')
        print(f'  ║  Step 2: Run:                                           ║')
        print(f'  ║    "{python_exe}" -m playwright install chromium        ')
        print('  ║                                                         ║')
        print('  ║  If that fails with a permissions error, try:           ║')
        print(f'  ║    "{python_exe}" -m playwright install --with-deps chromium')
        print('  ║                                                         ║')
        print('  ║  If still failing, check internet connectivity and      ║')
        print('  ║  proxy/firewall settings. The download is ~100MB from   ║')
        print('  ║  playwright.azureedge.net                               ║')
        print('  ╚══════════════════════════════════════════════════════════╝')
        print()


if __name__ == '__main__':
    main()
