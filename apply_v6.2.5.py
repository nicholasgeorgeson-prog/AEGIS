#!/usr/bin/env python3
"""
AEGIS v6.2.5 — Robust SP Scan Diagnostic Build

Fixes:
1. Retry logic: Large files (app.js ~800KB) now retry 3 times with 120s timeout
   to survive corporate network throttling that caused v6.2.4 downloads to fail
2. File size verification: Warns if app.js is suspiciously small (< 100KB)
3. Diagnostic logging throughout SP scan chain for F12 console debugging

Downloads: JS-only changes — NO server restart needed, just hard refresh
"""

import os
import sys
import ssl
import time
import shutil
import urllib.request
from datetime import datetime

GITHUB_RAW = 'https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main'

FILES = {
    'static/js/app.js': 'SP scan cinematic dashboard + diagnostic logging (~800KB)',
    'static/js/features/guide-system.js': 'Fix robot voice on tour transition scenes (_isIntro flag)',
    'version.json': 'Version bump to 6.2.5',
    'static/version.json': 'Version bump to 6.2.5 (browser copy)',
}

# Files that are large and need extra download attempts
LARGE_FILES = {'static/js/app.js'}

# Minimum expected sizes for verification (bytes)
MIN_SIZES = {
    'static/js/app.js': 100000,  # app.js should be >100KB (currently ~800KB)
}

def make_ssl_context():
    """Create SSL context with fallback for corporate networks."""
    try:
        return ssl.create_default_context()
    except Exception:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def make_insecure_ssl_context():
    """Create SSL context that skips certificate verification (for corporate proxies)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def download_file(url, dest, ssl_ctx, timeout=60, max_retries=1):
    """Download a file with SSL fallback and retry logic."""
    last_error = None

    for attempt in range(max_retries):
        if attempt > 0:
            wait = min(5 * attempt, 15)
            print(f'    Retry {attempt}/{max_retries-1} in {wait}s...')
            time.sleep(wait)

        # Try with provided SSL context first
        for ctx_label, ctx in [('default SSL', ssl_ctx), ('no-verify SSL', make_insecure_ssl_context())]:
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'AEGIS-Updater/6.2.5',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                })
                with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                    data = resp.read()

                os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else '.', exist_ok=True)
                with open(dest, 'wb') as f:
                    f.write(data)
                return True, len(data)
            except Exception as e:
                last_error = e
                if 'SSL' in str(type(e).__name__) or 'certificate' in str(e).lower():
                    # SSL error — try next context
                    continue
                elif 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
                    print(f'    Timeout on attempt {attempt+1} ({ctx_label}) — will retry')
                    break  # Skip to next retry attempt
                else:
                    print(f'    Error on attempt {attempt+1} ({ctx_label}): {e}')
                    break  # Skip to next retry attempt

    print(f'  [FAIL] All {max_retries} attempts failed: {last_error}')
    return False, 0

def main():
    print('=' * 60)
    print('  AEGIS v6.2.5 — Robust SP Scan Diagnostic Build')
    print('=' * 60)
    print()

    # Verify we're in the right directory
    if not os.path.exists('app.py') or not os.path.isdir('static'):
        print('[ERROR] Please run this script from the AEGIS install directory.')
        print('  Expected: app.py and static/ folder in current directory')
        sys.exit(1)

    ssl_ctx = make_ssl_context()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.2.5_{timestamp}')

    print(f'[Step 1] Backing up files to {backup_dir}/')
    for rel_path in FILES:
        if os.path.exists(rel_path):
            bak = os.path.join(backup_dir, rel_path)
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            shutil.copy2(rel_path, bak)
            print(f'  [OK] Backed up {rel_path}')
        else:
            print(f'  [SKIP] {rel_path} (not found, will be created)')
    print()

    print('[Step 2] Downloading updated files from GitHub...')
    print('  (Large files get 3 attempts with 120s timeout)')
    print()
    success = 0
    warnings = []

    for rel_path, desc in FILES.items():
        url = f'{GITHUB_RAW}/{rel_path}'
        is_large = rel_path in LARGE_FILES
        max_retries = 3 if is_large else 1
        timeout = 120 if is_large else 60

        size_note = ' [LARGE FILE — 3 attempts, 120s timeout]' if is_large else ''
        print(f'  Downloading {rel_path}{size_note}')
        print(f'    {desc}')

        ok, size = download_file(url, rel_path, ssl_ctx, timeout=timeout, max_retries=max_retries)

        if ok:
            print(f'  [OK] {rel_path} ({size:,} bytes)')

            # Verify file size for critical files
            min_size = MIN_SIZES.get(rel_path, 0)
            if min_size > 0 and size < min_size:
                msg = f'  [WARN] {rel_path} is only {size:,} bytes — expected >{min_size:,}. File may be incomplete!'
                print(msg)
                warnings.append(msg)

            success += 1
        else:
            print(f'  [FAIL] {rel_path}')
            if is_large:
                warnings.append(f'  [CRITICAL] {rel_path} failed to download after {max_retries} attempts!')
    print()

    # Step 3: Verify app.js was actually updated
    print('[Step 3] Verifying critical files...')
    app_js_path = 'static/js/app.js'
    if os.path.exists(app_js_path):
        actual_size = os.path.getsize(app_js_path)
        print(f'  app.js size: {actual_size:,} bytes')

        # Check for the diagnostic marker
        try:
            with open(app_js_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 50KB to check for marker (much faster than reading entire file)
                head = f.read(50000)

            # Search the entire file for the marker
            with open(app_js_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if '__AEGIS_SP_CINEMATIC' in content:
                print('  [OK] Diagnostic marker found in app.js — v6.2.5 code is present')
            else:
                print('  [WARN] Diagnostic marker NOT found — app.js may be an older version!')
                warnings.append('  app.js does not contain v6.2.5 diagnostic code')

            if actual_size < 100000:
                print(f'  [WARN] app.js is only {actual_size:,} bytes — expected ~800,000+. Download may have been truncated!')
                warnings.append(f'  app.js appears truncated ({actual_size:,} bytes)')
        except Exception as e:
            print(f'  [WARN] Could not verify app.js content: {e}')
    else:
        print('  [FAIL] app.js does not exist!')
        warnings.append('  app.js missing after download')
    print()

    print('=' * 60)
    if warnings:
        print(f'  Done! {success}/{len(FILES)} files updated. {len(warnings)} WARNING(s):')
        for w in warnings:
            print(w)
    else:
        print(f'  Done! {success}/{len(FILES)} files updated successfully.')
    print()
    print('  What changed:')
    print('  * SP scan cinematic dashboard (rewrite from v6.2.4)')
    print('  * Diagnostic logging for F12 console debugging')
    print('  * Tour robot voice fix')
    print()
    print('  VERIFICATION — after hard refresh, open F12 Console and type:')
    print('    window.__AEGIS_SP_CINEMATIC')
    print('  Expected: "6.2.4-diag"')
    print('  If undefined: app.js did not update — see warnings above')
    print()
    print('  Next step: Hard refresh the browser (Ctrl+Shift+R)')
    print('  NO server restart needed — these are JS-only changes.')
    print('=' * 60)

if __name__ == '__main__':
    main()
