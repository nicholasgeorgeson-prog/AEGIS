#!/usr/bin/env python3
"""
AEGIS v6.1.2 → v6.1.3 Update Applier
=======================================
Headless Browser SharePoint Connector

This update adds a Playwright-powered headless browser fallback for SharePoint
Connect & Scan. When the REST API authentication fails (e.g., AADSTS65002 error
on GCC High where first-party OAuth client IDs are blocked), AEGIS now
automatically falls back to a headless browser that uses the same Windows SSO
credentials as Chrome — zero OAuth tokens, zero config editing required.

Changes:
- sharepoint_connector.py — HeadlessSPConnector class + HEADLESS_SP_AVAILABLE flag
- routes/review_routes.py — Auto-fallback to headless when REST API auth fails,
  max_workers=1 for headless batch downloads
- version.json / static/version.json — Version bump to 6.1.3
- static/js/help-docs.js — v6.1.3 changelog
- CLAUDE.md — Lesson 146

Usage:
  cd <AEGIS_INSTALL_DIR>
  python apply_v6.1.3.py

After applying:
  1. Restart AEGIS (double-click Restart_AEGIS.bat or Ctrl+C + python app.py --debug)
  2. Hard refresh browser (Ctrl+Shift+R)
  3. Try SharePoint Connect & Scan — if REST API auth fails, headless browser
     will auto-activate using your Windows login credentials
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
    'sharepoint_connector.py': 'SharePoint connector — HeadlessSPConnector class + HEADLESS_SP_AVAILABLE',
    'routes/review_routes.py': 'Review routes — headless auto-fallback + max_workers=1',
    'version.json': 'Version 6.1.3',
    'static/version.json': 'Version 6.1.3 (static copy)',
    'CLAUDE.md': 'Session notes with Lesson 146',
    'static/js/help-docs.js': 'Help docs with v6.1.3 changelog',
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
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.3'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f'  [ERROR] Download failed: {e}')
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.1.3'})
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


def verify_headless_sp_available():
    """Verify HEADLESS_SP_AVAILABLE flag exists in sharepoint_connector.py."""
    try:
        with open('sharepoint_connector.py', 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'HEADLESS_SP_AVAILABLE' in content and 'class HeadlessSPConnector' in content:
            print('  [OK] HeadlessSPConnector class and HEADLESS_SP_AVAILABLE flag present')
            return True
        elif 'HEADLESS_SP_AVAILABLE' in content:
            print('  [WARN] HEADLESS_SP_AVAILABLE flag present but HeadlessSPConnector class missing')
            return False
        else:
            print('  [FAIL] HEADLESS_SP_AVAILABLE flag NOT found in sharepoint_connector.py')
            return False
    except Exception as e:
        print(f'  [FAIL] Could not verify: {e}')
        return False


def verify_headless_fallback():
    """Verify headless fallback code exists in review_routes.py."""
    routes_path = os.path.join('routes', 'review_routes.py')
    if not os.path.exists(routes_path):
        print('  [FAIL] routes/review_routes.py not found')
        return False
    try:
        with open(routes_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        checks = [
            ('HeadlessSPConnector' in content, 'HeadlessSPConnector import'),
            ('headless browser (Windows SSO)' in content, 'fallback log message'),
            ('_is_headless_sp' in content, 'max_workers=1 detection'),
        ]
        all_ok = True
        for check, name in checks:
            if check:
                print(f'  [OK] {name} present in review_routes.py')
            else:
                print(f'  [FAIL] {name} NOT found in review_routes.py')
                all_ok = False
        return all_ok
    except Exception as e:
        print(f'  [FAIL] Could not verify headless fallback: {e}')
        return False


def verify_playwright(python_exe):
    """Verify Playwright is installed and chromium is available."""
    try:
        result = subprocess.run(
            [python_exe, '-c', 'from playwright.sync_api import sync_playwright; print("PLAYWRIGHT_OK")'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and 'PLAYWRIGHT_OK' in result.stdout:
            print('  [OK] Playwright sync API available')
            return True
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'not installed'
            print(f'  [INFO] Playwright not installed: {err[:100]}')
            print('         Install with: pip install playwright && playwright install chromium')
            return False
    except Exception as e:
        print(f'  [INFO] Playwright check: {e}')
        return False


def verify_version():
    """Verify version.json shows 6.1.3."""
    try:
        import json
        with open('version.json', 'r') as f:
            v = json.load(f)
        ver = v.get('version', 'unknown')
        if ver == '6.1.3':
            print(f'  [OK] version.json: {ver}')
            return True
        else:
            print(f'  [WARN] version.json: {ver} (expected 6.1.3)')
            return False
    except Exception as e:
        print(f'  [FAIL] version.json: {e}')
        return False


def pip_install(python_exe, packages):
    """Install packages with offline-first, online fallback."""
    wheels_dirs = []
    for d in ['wheels', os.path.join('packaging', 'wheels')]:
        if os.path.isdir(d):
            wheels_dirs.append(d)

    for pkg in packages:
        if wheels_dirs:
            cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location']
            for wd in wheels_dirs:
                cmd.extend(['--no-index', '--find-links', wd])
            cmd.append(pkg)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f'    [OK] {pkg} (offline)')
                continue

        cmd = [python_exe, '-m', 'pip', 'install', '--no-warn-script-location', pkg]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f'    [OK] {pkg} (online)')
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            print(f'    [FAIL] {pkg} — {err[:100]}')


def main():
    print('=' * 65)
    print('  AEGIS v6.1.3 Update Applier')
    print('  Headless Browser SharePoint Connector')
    print('=' * 65)
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
    backup_dir = os.path.join('backups', f'pre_v6.1.3_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[INFO] Backup directory: {backup_dir}')
    print()

    # Ensure directories exist
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('routes', exist_ok=True)

    # Download and apply files
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

    # Install and verify Playwright (REQUIRED for SharePoint GCC High headless browser)
    print('[STEP 2] Installing Playwright (headless browser engine)...')
    pw_ok = verify_playwright(python_exe)
    if not pw_ok:
        print('  Installing playwright package...')
        pip_install(python_exe, ['playwright'])
        pw_ok = verify_playwright(python_exe)

    if pw_ok:
        # Install Chromium browser binary
        print('  Installing Chromium browser for Playwright...')
        try:
            result = subprocess.run(
                [python_exe, '-m', 'playwright', 'install', 'chromium'],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print('  [OK] Chromium browser installed')
            else:
                err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown error'
                print(f'  [WARN] Chromium install: {err[:120]}')
                print('         Try manually: python -m playwright install chromium')
        except subprocess.TimeoutExpired:
            print('  [WARN] Chromium install timed out (may still be downloading)')
            print('         Try manually: python -m playwright install chromium')
        except Exception as e:
            print(f'  [WARN] Chromium install: {e}')
    else:
        print()
        print('  [FAIL] Could not install Playwright.')
        print('         The headless browser fallback for SharePoint GCC High will NOT work.')
        print('         Try manually:')
        print(f'           "{python_exe}" -m pip install playwright')
        print(f'           "{python_exe}" -m playwright install chromium')
    print()

    # Verify existing auth dependencies
    print('[STEP 3] Verifying existing auth stack...')
    msal_ok = verify_import(python_exe, 'msal', 'MSAL (OAuth 2.0)')
    requests_ok = verify_import(python_exe, 'requests', 'requests')
    if sys.platform == 'win32':
        sspi_ok = verify_import(python_exe, 'sspi', 'sspi (pywin32)')
    else:
        sspi_ok = None
    print()

    # v6.1.3-specific verifications
    print('[STEP 4] Verifying v6.1.3 changes...')
    headless_class_ok = verify_headless_sp_available()
    fallback_ok = verify_headless_fallback()
    version_ok = verify_version()
    print()

    # ═══════════════════════════════════════════════════════════
    # COMPREHENSIVE SUMMARY
    # ═══════════════════════════════════════════════════════════
    print('=' * 65)
    print('  UPDATE SUMMARY')
    print('=' * 65)
    print()

    # File download results
    if fail_count == 0:
        print(f'  FILES:  {success_count}/{success_count} downloaded successfully')
    else:
        print(f'  FILES:  {success_count} succeeded, {fail_count} FAILED')
    print()

    # Auth stack
    print('  AUTH STACK:')
    print(f'    requests:              {"OK" if requests_ok else "NOT INSTALLED"}')
    print(f'    MSAL (OAuth 2.0):      {"OK" if msal_ok else "NOT INSTALLED"}')
    if sys.platform == 'win32':
        print(f'    pywin32 (SSPI):        {"OK" if sspi_ok else "NOT INSTALLED"}')
    print(f'    Playwright (headless): {"OK" if pw_ok else "NOT INSTALLED — headless fallback DISABLED"}')
    print()

    # v6.1.3 features
    print('  v6.1.3 FEATURES:')
    print(f'    HeadlessSPConnector:   {"PRESENT" if headless_class_ok else "MISSING"}')
    print(f'    Auto-fallback route:   {"PRESENT" if fallback_ok else "MISSING"}')
    print(f'    Version 6.1.3:         {"CORRECT" if version_ok else "INCORRECT"}')
    print()

    # Auth strategy availability
    print('  SHAREPOINT AUTH STRATEGY PRIORITY:')
    print('    1. Preemptive SSPI Negotiate   (Windows SSO via pywin32)')
    print('    2. MSAL OAuth 2.0              (device code flow)')
    print('    3. Standard Negotiate           (requests-negotiate-sspi)')
    if pw_ok:
        print('    4. Headless browser fallback    ** NEW v6.1.3 ** AVAILABLE')
    else:
        print('    4. Headless browser fallback    ** NEW v6.1.3 ** unavailable (install Playwright)')
    print()

    # Overall status
    all_ok = (fail_count == 0 and headless_class_ok and fallback_ok and version_ok)
    if all_ok:
        print('  STATUS: UPDATE APPLIED SUCCESSFULLY')
    else:
        print('  STATUS: UPDATE APPLIED WITH ISSUES — see details above')
    print()

    print('=' * 65)
    print()

    # How it works
    print("How the headless browser fallback works:")
    print()
    print("  When you click 'Connect & Scan' with a SharePoint URL:")
    print()
    print("  1. AEGIS tries the standard REST API auth cascade")
    print("     (SSPI → MSAL OAuth → standard Negotiate)")
    print()
    print("  2. If ALL REST API auth fails (e.g., AADSTS65002):")
    print("     - AEGIS launches a headless Chromium browser")
    print("     - Browser authenticates via Windows SSO automatically")
    print("       (same credentials Chrome uses)")
    print("     - SharePoint REST API is called from within the browser")
    print("     - Files are discovered and downloaded through the browser")
    print()
    print("  3. The result is identical to REST API — same scan pipeline,")
    print("     same progress dashboard, same results")
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
    if not pw_ok:
        print('  *** CRITICAL: Playwright is NOT installed ***')
        print('  The headless browser fallback for SharePoint GCC High will NOT work.')
        print('  You MUST install Playwright for Connect & Scan to work:')
        print(f'     "{python_exe}" -m pip install playwright')
        print(f'     "{python_exe}" -m playwright install chromium')
        print()


if __name__ == '__main__':
    main()
