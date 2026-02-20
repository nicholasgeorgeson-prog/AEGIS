#!/usr/bin/env python3
"""
AEGIS v5.9.35 Direct Updater
Downloads all changed files from GitHub and places them
directly into the correct locations in your AEGIS install.

Creates a backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v5.9.35.py
    python3 apply_v5.9.35.py

No dependencies required - uses only Python standard library.
"""

import urllib.request
import ssl
import os
import sys
import shutil
from datetime import datetime

# -- Configuration --
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"

# Files to download - these go directly into the AEGIS install directory
FILES = [
    # Python backend
    "version.json",
    "static/version.json",
    "sharepoint_connector.py",
    "Start_AEGIS.bat",

    # Routes
    "routes/review_routes.py",

    # Hyperlink Validator
    "hyperlink_validator/validator.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/models.py",

    # Templates
    "templates/index.html",

    # JavaScript
    "static/js/app.js",
    "static/js/ui/events.js",
    "static/js/features/guide-system.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/statement-source-viewer.js",
    "static/js/features/statement-history.js",

    # CSS
    "static/css/features/hyperlink-validator.css",
    "static/css/features/statement-forge.css",

    # Audio manifest (MP3 files downloaded separately)
    "static/audio/demo/manifest.json",
]


def get_ssl_context():
    """Get SSL context with aggressive fallback for embedded Python."""
    # Try 1: certifi
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using certifi certificates")
        return ctx
    except Exception:
        pass

    # Try 2: system certs
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using system certificates")
        return ctx
    except Exception:
        pass

    # Try 3: unverified (SSLContext directly, not create_default_context)
    print("  [WARN] SSL certificates not available - using unverified HTTPS")
    print("         (This is safe for downloading from GitHub)")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(filepath, ssl_ctx):
    """Download a single file from GitHub raw content. Returns bytes or None."""
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{filepath}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        print(f"  FAIL  {filepath} -- {e}")
        return None


def download_audio_files(install_dir, ssl_ctx):
    """Download pre-generated MP3 narration files from GitHub."""
    print()
    print("  Downloading demo narration audio files...")
    print("  (478 MP3 files, ~45MB total - this may take a few minutes)")
    print()

    # Download manifest to know which files to get
    manifest_path = os.path.join(install_dir, "static", "audio", "demo", "manifest.json")
    if not os.path.exists(manifest_path):
        print("  [SKIP] No manifest found - audio will be downloaded next run")
        return 0, 0

    import json
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"  [WARN] Could not read manifest: {e}")
        return 0, 0

    sections = manifest.get('sections', {})
    audio_dir = os.path.join(install_dir, "static", "audio", "demo")
    os.makedirs(audio_dir, exist_ok=True)

    # Collect all MP3 filenames from manifest
    mp3_files = []
    for section_id, section in sections.items():
        for step in section.get('steps', []):
            if step and step.get('file'):
                mp3_files.append(step['file'])

    # Skip files that already exist
    to_download = []
    for f in mp3_files:
        full_path = os.path.join(audio_dir, f)
        if not os.path.exists(full_path):
            to_download.append(f)

    if not to_download:
        print(f"  All {len(mp3_files)} audio files already present")
        return len(mp3_files), 0

    print(f"  {len(to_download)} audio files to download ({len(mp3_files) - len(to_download)} already present)")

    downloaded = 0
    failed = 0
    for i, filename in enumerate(to_download):
        data = download_file(f"static/audio/demo/{filename}", ssl_ctx)
        if data:
            dest = os.path.join(audio_dir, filename)
            try:
                with open(dest, "wb") as f:
                    f.write(data)
                downloaded += 1
            except Exception:
                failed += 1
        else:
            failed += 1

        # Progress every 50 files
        if (i + 1) % 50 == 0:
            print(f"    Progress: {i + 1}/{len(to_download)} downloaded...")

    print(f"  Audio: {downloaded} downloaded, {failed} failed")
    return downloaded, failed


def main():
    # Detect install directory (where this script is running)
    install_dir = os.path.dirname(os.path.abspath(__file__))

    # Verify we're in the right place
    has_app = os.path.exists(os.path.join(install_dir, "app.py"))
    has_static = os.path.isdir(os.path.join(install_dir, "static"))
    if not has_app and not has_static:
        print("=" * 55)
        print("  WARNING: This doesn't look like an AEGIS directory!")
        print(f"  Current location: {install_dir}")
        print()
        print("  Expected to find app.py and static/ folder here.")
        print("  Place this script in your AEGIS installation directory.")
        print("=" * 55)
        print()
        resp = input("  Continue anyway? (y/n): ").strip().lower()
        if resp != 'y':
            print("  Cancelled.")
            return 1

    print()
    print("  =============================================")
    print("    AEGIS v5.9.35 Direct Updater")
    print("    Multi-issue fix + enhancements")
    print("  =============================================")
    print()
    print("  FIXES:")
    print("    - Batch scan word count showing 0")
    print("    - SharePoint SSL + auto-detect library")
    print("    - Exclusion list persistence")
    print("    - Loading screen timing")
    print("    - HV header/upload/modes")
    print("    - SF modal z-index")
    print("    - Doc Review dropzone")
    print("    - Source Viewer save")
    print()
    print("  NEW:")
    print("    - 478 MP3 demo narrations (Jenny Neural)")
    print("    - SharePoint REST API in HV")
    print("    - Document viewer text/preview toggle")
    print("    - Start_AEGIS.bat (minimized terminal)")
    print()
    print(f"  Install dir: {install_dir}")
    print(f"  Code files:  {len(FILES)}")
    print()

    # Set up SSL
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v5.9.35_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"  Backup dir: {backup_dir}")
    print()

    # Download and apply each file
    print("  Downloading and applying code files...")
    print("  " + "-" * 50)
    success = 0
    failed = 0
    backed_up = 0

    for filepath in FILES:
        # Download from GitHub
        data = download_file(filepath, ssl_ctx)
        if data is None:
            failed += 1
            continue

        dest = os.path.join(install_dir, filepath)

        # Backup existing file
        if os.path.exists(dest):
            backup_dest = os.path.join(backup_dir, filepath)
            backup_dest_dir = os.path.dirname(backup_dest)
            if backup_dest_dir:
                os.makedirs(backup_dest_dir, exist_ok=True)
            try:
                shutil.copy2(dest, backup_dest)
                backed_up += 1
            except Exception as e:
                print(f"  [WARN] Could not backup {filepath}: {e}")

        # Create directory structure if needed
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the new file
        try:
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  OK    {filepath} ({size_kb:.1f} KB)")
            success += 1
        except Exception as e:
            print(f"  FAIL  {filepath} -- write error: {e}")
            failed += 1

    # Download audio files
    audio_ok, audio_fail = download_audio_files(install_dir, ssl_ctx)

    print()
    print("  " + "=" * 50)
    print(f"  Code:  {success} applied, {failed} failed, {backed_up} backed up")
    if audio_ok or audio_fail:
        print(f"  Audio: {audio_ok} downloaded, {audio_fail} failed")
    print()

    if failed == 0:
        print("  All code files applied successfully!")
        print()
        print("  IMPORTANT: This update changes Python backend files.")
        print("  You MUST restart AEGIS for changes to take effect.")
        print()
        print("  NEXT STEPS:")
        print("    1. Close this window")
        print("    2. Restart AEGIS with Start_AEGIS.bat or Restart_AEGIS.bat")
        print()
        print(f"  If something went wrong, your old files are in:")
        print(f"    {backup_dir}")
    else:
        print(f"  WARNING: {failed} file(s) failed.")
        print("  Check your internet connection and try again.")
        print()
        print(f"  Successfully applied files are already in place.")
        print(f"  Old versions backed up to: {backup_dir}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n  Cancelled.")
        code = 1
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        code = 1

    print()
    input("  Press Enter to exit...")
    sys.exit(code)
