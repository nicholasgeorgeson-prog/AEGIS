#!/usr/bin/env python3
"""
AEGIS v6.2.4 — SP Scan Dashboard Fix + Tour Robot Voice Fix

Fixes:
1. SP Scan Dashboard: Hides #batch-dropzone when SP scan starts so dashboard
   is visible above the fold (was pushing dashboard below modal viewport)
2. Tour Robot Voice: Adds _isIntro flag to startFullTour() transition scenes
   so TTS doesn't read "Now let's explore: Dashboard" in robot voice

Downloads: JS-only changes — NO server restart needed, just hard refresh
"""

import os
import sys
import ssl
import shutil
import urllib.request
from datetime import datetime

GITHUB_RAW = 'https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main'

FILES = {
    'static/js/app.js': 'Hide dropzone during SP scan so dashboard is visible above the fold',
    'static/js/features/guide-system.js': 'Fix robot voice on tour transition scenes (_isIntro flag)',
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

def download_file(url, dest, ssl_ctx):
    """Download a file with SSL fallback."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AEGIS-Updater/6.2.4'})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=60) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else '.', exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'  [FAIL] {e}')
        return False

def main():
    print('=' * 60)
    print('  AEGIS v6.2.4 — SP Dashboard Fix + Tour Voice Fix')
    print('=' * 60)
    print()

    # Verify we're in the right directory
    if not os.path.exists('app.py') or not os.path.isdir('static'):
        print('[ERROR] Please run this script from the AEGIS install directory.')
        print('  Expected: app.py and static/ folder in current directory')
        sys.exit(1)

    ssl_ctx = make_ssl_context()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v6.2.4v4_{timestamp}')

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
    success = 0
    for rel_path, desc in FILES.items():
        url = f'{GITHUB_RAW}/{rel_path}'
        print(f'  Downloading {rel_path} — {desc}')
        if download_file(url, rel_path, ssl_ctx):
            size = os.path.getsize(rel_path)
            print(f'  [OK] {rel_path} ({size:,} bytes)')
            success += 1
        else:
            print(f'  [FAIL] {rel_path}')
    print()

    print('=' * 60)
    print(f'  Done! {success}/{len(FILES)} files updated.')
    print()
    print('  Next step: Hard refresh the browser (Ctrl+Shift+R)')
    print('  NO server restart needed — these are JS-only changes.')
    print('=' * 60)

if __name__ == '__main__':
    main()
