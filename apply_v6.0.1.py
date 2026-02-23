#!/usr/bin/env python3
"""
AEGIS v6.0.1 Update Script
============================
Applies all changes from v6.0.0 to v6.0.1.

This update includes:
- Fix company name overflow in Proposal Compare (2-line clamp + hover tooltip)
- Re-Analyze button on project detail with auto term grouping
- Contract term badges on proposal cards
- Compare All now uses multi-term-aware frontend pipeline
- Backend extracts contract_term from proposal JSON for summaries
- Cinematic Technology Showcase: MP4 video player (Behind the Scenes tile)
  NOTE: The 379MB showcase video is NOT included in this script (too large).
  You must manually copy aegis-showcase.mp4 to: static/video/aegis-showcase.mp4
  The system falls back to the Canvas animation if the video file is not found.
- Fix PDF viewer in Proposal Compare (PDF.js vendor files deployed)
- Fix guided tour demo audio (robot voice at start + audio-visual drift)

Downloads files from: https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/

Usage:
  1. Place this file in your AEGIS install directory (where app.py lives)
  2. Run: python apply_v6.0.1.py
     or:  python3 apply_v6.0.1.py
  3. Restart AEGIS after completion
  4. (Optional) Copy aegis-showcase.mp4 to static/video/ for the Behind the Scenes video

No external dependencies required - uses only Python standard library.
"""

import os
import sys
import json
import shutil
import urllib.request
import urllib.error
import ssl
import time
from datetime import datetime

VERSION = "6.0.1"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# FILES CHANGED FROM v6.0.0 TO v6.0.1
# ============================================================================

# Python backend (modified)
PYTHON_FILES = [
    "proposal_compare/projects.py",       # contract_term extraction from JSON blob
]

# JavaScript files (modified + cinema prerequisite + PDF.js vendor)
JS_FILES = [
    "static/js/features/proposal-compare.js",    # Re-Analyze button, term badges, button wiring
    "static/js/features/technology-showcase.js",  # Cinema engine (ensure deployed from v6.0.0)
    "static/js/features/landing-page.js",         # Dashboard tiles + cinema tile handler
    "static/js/features/guide-system.js",         # v6.0.1: Fix robot voice + audio-visual drift in demo
    "static/js/features/pdf-viewer.js",           # PDF.js viewer module
    "static/js/vendor/pdfjs/pdf.min.mjs",         # PDF.js library (for Proposal Compare PDF viewer)
    "static/js/vendor/pdfjs/pdf.worker.min.mjs",  # PDF.js worker (1.3MB — required for PDF rendering)
]

# CSS files (modified + cinema prerequisite)
CSS_FILES = [
    "static/css/features/proposal-compare.css",    # 2-line clamp, term badge styling
    "static/css/features/technology-showcase.css",  # Cinema styling (ensure deployed from v6.0.0)
]

# HTML template (cinema script/link tags)
HTML_FILES = [
    "templates/index.html",
]

# Config/version files
CONFIG_FILES = [
    "version.json",
    "static/version.json",
    "CLAUDE.md",
]

# Cinema audio files (manifest + MP3 clips for narration)
CINEMA_AUDIO = [
    "static/audio/cinema/manifest.json",
]


# ============================================================================
# SSL FALLBACK (for corporate/air-gapped networks)
# ============================================================================

def get_ssl_context():
    """Try multiple SSL strategies for corporate networks."""
    # Strategy 1: certifi (if available)
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        urllib.request.urlopen(
            urllib.request.Request(f"{RAW_BASE}/version.json",
                                  headers={'User-Agent': 'AEGIS-Updater'}),
            context=ctx, timeout=10
        )
        print("  SSL: Using certifi certificates")
        return ctx
    except Exception:
        pass

    # Strategy 2: System default certificates
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(
            urllib.request.Request(f"{RAW_BASE}/version.json",
                                  headers={'User-Agent': 'AEGIS-Updater'}),
            context=ctx, timeout=10
        )
        print("  SSL: Using system certificates")
        return ctx
    except Exception:
        pass

    # Strategy 3: Unverified (corporate CA bypass)
    print("  [WARN] SSL certificates not available - using unverified HTTPS")
    print("         (This is safe for downloading from GitHub)")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        pass

    # Strategy 4: Bare context
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(url, dest_path, ssl_ctx=None, retries=3):
    """Download a file from URL to dest_path with retries."""
    for attempt in range(retries):
        try:
            # Add cache-bust param to prevent GitHub CDN from serving stale content
            cache_bust = f"{'&' if '?' in url else '?'}cb={int(time.time())}"
            req = urllib.request.Request(url + cache_bust, headers={
                'User-Agent': f'AEGIS-Updater/{VERSION}',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
            })
            kwargs = {'timeout': 60}
            if ssl_ctx:
                kwargs['context'] = ssl_ctx
            response = urllib.request.urlopen(req, **kwargs)
            data = response.read()

            # Ensure parent directory exists
            dirpath = os.path.dirname(dest_path)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)

            with open(dest_path, 'wb') as f:
                f.write(data)
            return len(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return -1  # File not found on remote
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    [ERR]  {dest_path}: {type(e).__name__}: {e}")
                return 0  # Download failed
    return 0


def backup_file(filepath, backup_dir):
    """Create backup of a file preserving directory structure."""
    if os.path.exists(filepath):
        dest = os.path.join(backup_dir, filepath)
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        try:
            shutil.copy2(filepath, dest)
            return True
        except Exception:
            return False
    return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    install_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(install_dir)

    print()
    print("=" * 70)
    print("  +------------------------------------------------+")
    print("  |   AEGIS v6.0.1 -- Proposal Compare Update      |")
    print("  |   Smart Re-Analyze with Auto Term Grouping      |")
    print("  +------------------------------------------------+")
    print("=" * 70)
    print()

    # Verify we're in the right directory
    has_app = os.path.exists('app.py')
    has_static = os.path.isdir('static')
    if not has_app or not has_static:
        print("  [ERROR] This doesn't look like an AEGIS install directory!")
        print(f"          Current location: {install_dir}")
        print("          Expected to find app.py and static/ folder.")
        print()
        resp = input("  Continue anyway? (y/n): ").strip().lower()
        if resp != 'y':
            print("  Cancelled.")
            return 1

    # Check current version
    try:
        with open('version.json', 'r') as f:
            current = json.load(f)
        current_version = current.get('version', 'unknown')
    except Exception:
        current_version = 'unknown'

    print(f"  Current version:  {current_version}")
    print(f"  Target version:   {VERSION}")
    print(f"  Install dir:      {install_dir}")
    print()

    # Show what's included
    print("  THIS UPDATE INCLUDES:")
    print("  " + "-" * 50)
    print("  * Fix company name overflow (2-line clamp)")
    print("  * Hover tooltip shows full company name")
    print("  * Re-Analyze button on project detail")
    print("  * Auto-detect contract terms across proposals")
    print("  * Togglable term-grouped comparison views")
    print("  * Contract term badges on proposal cards")
    print("  * Compare All uses multi-term pipeline")
    print("  * Cinematic Technology Showcase (Behind the Scenes)")
    print("    — ensures all cinema files are deployed")
    print("  * Fix PDF viewer in Proposal Compare (PDF.js vendor files)")
    print("  * Fix guided tour demo audio (robot voice + alignment)")
    print()

    # Get SSL context
    print("  Testing connection to GitHub...")
    ssl_ctx = get_ssl_context()
    print()

    # Build complete file list
    all_files = PYTHON_FILES + JS_FILES + CSS_FILES + HTML_FILES + CONFIG_FILES + CINEMA_AUDIO
    total_files = len(all_files)
    print(f"  Total files to update: {total_files} (+ cinema audio clips)")
    print()

    # ---- Phase 1: Backup ----
    print("  Phase 1: Backing up existing files...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backups/v{VERSION}_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    backed_up = 0
    for filepath in all_files:
        if backup_file(filepath, backup_dir):
            backed_up += 1
    print(f"           Backed up {backed_up} existing files to {backup_dir}/")
    print()

    # ---- Phase 2: Ensure directories exist ----
    print("  Phase 2: Ensuring directories exist...")
    dirs_needed = set()
    for filepath in all_files:
        d = os.path.dirname(filepath)
        if d:
            dirs_needed.add(d)
    for d in sorted(dirs_needed):
        os.makedirs(d, exist_ok=True)
        # Ensure __init__.py for Python packages
        if not d.startswith('static') and not d.startswith('templates'):
            init_file = os.path.join(d, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('')
                print(f"    Created {init_file}")
    # Create static/video/ directory for manual video deployment
    os.makedirs('static/video', exist_ok=True)
    print("           Done.")
    print()

    # ---- Phase 3: Download files ----
    print("  Phase 3: Downloading updated files from GitHub...")
    print()

    success_count = 0
    fail_count = 0
    skip_count = 0

    file_groups = [
        ("Python Backend", PYTHON_FILES),
        ("JavaScript", JS_FILES),
        ("CSS", CSS_FILES),
        ("HTML Template", HTML_FILES),
        ("Config & Version", CONFIG_FILES),
        ("Cinema Audio Manifest", CINEMA_AUDIO),
    ]

    for group_name, files in file_groups:
        if not files:
            continue
        print(f"    {group_name}:")
        for filepath in files:
            url = f"{RAW_BASE}/{filepath}"
            result = download_file(url, filepath, ssl_ctx)
            if result > 0:
                size_kb = result / 1024
                print(f"      [OK]   {filepath} ({size_kb:.1f} KB)")
                success_count += 1
            elif result == -1:
                print(f"      [SKIP] {filepath} (not found on remote)")
                skip_count += 1
            else:
                print(f"      [FAIL] {filepath}")
                fail_count += 1
        print()

    # ---- Phase 4: Download cinema audio clips from manifest ----
    print("  Phase 4: Checking cinema audio clips...")
    audio_dir = "static/audio/cinema"
    os.makedirs(audio_dir, exist_ok=True)
    manifest_path = os.path.join(audio_dir, "manifest.json")
    audio_downloaded = 0
    audio_skipped = 0
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            sections = manifest.get('sections', {})
            for sec_id, sec_data in sections.items():
                steps = sec_data.get('steps', [])
                for step in steps:
                    mp3_file = step.get('file', '')
                    if not mp3_file:
                        continue
                    mp3_path = os.path.join(audio_dir, mp3_file)
                    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
                        audio_skipped += 1
                        continue
                    url = f"{RAW_BASE}/{audio_dir}/{mp3_file}"
                    result = download_file(url, mp3_path, ssl_ctx)
                    if result > 0:
                        audio_downloaded += 1
                    elif result == -1:
                        pass  # Not on remote — will use Web Speech fallback
                    else:
                        pass  # Download failed — Web Speech fallback handles it
            print(f"           Audio: {audio_downloaded} downloaded, {audio_skipped} already present")
        except Exception as e:
            print(f"           [WARN] Could not process audio manifest: {e}")
    else:
        print("           No cinema manifest found — audio will use Web Speech API fallback")
    print()

    # ---- Summary ----
    print("=" * 70)
    print(f"  UPDATE COMPLETE: v{VERSION}")
    print("=" * 70)
    print()
    print(f"  Files updated:   {success_count}")
    if skip_count:
        print(f"  Files skipped:   {skip_count}")
    if fail_count:
        print(f"  Files FAILED:    {fail_count}")
    print(f"  Backup location: {backup_dir}/")
    print()

    if fail_count > 0:
        print("  [WARNING] Some files failed to download.")
        print("  You can re-run this script to retry, or manually download from:")
        print(f"  https://github.com/{REPO}")
        print()

    print("  NEXT STEPS:")
    print("  " + "-" * 50)
    print("  1. Restart AEGIS (Python files changed)")
    print("     - Double-click restart_aegis.sh")
    print("     - Or: python3 app.py --debug")
    print("  2. Hard refresh browser (Ctrl+Shift+R)")
    print("  3. (Optional) Copy aegis-showcase.mp4 to static/video/ for Behind the Scenes video")
    print("     - Without it, the Behind the Scenes tile plays the Canvas animation fallback")
    print("  4. Click 'Behind the Scenes' tile to play cinematic showcase")
    print("  5. Open Proposal Compare > Projects > Select project")
    print("  6. Verify:")
    print("     - Company names wrap to 2 lines (hover for full name)")
    print("     - Term badges appear on proposal cards")
    print("     - Click 'Re-Analyze' to see term-grouped comparison")
    print()

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
