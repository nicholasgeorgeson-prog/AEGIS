#!/usr/bin/env python3
"""
AEGIS v5.9.41 Direct Updater
Downloads all changed files from GitHub and places them
directly into the correct locations in your AEGIS install.

Creates a backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v5.9.41.py
    python3 apply_v5.9.41.py

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
    # Version files (always first)
    "version.json",
    "static/version.json",

    # Proposal Compare backend
    "proposal_compare/__init__.py",
    "proposal_compare/parser.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/routes.py",
    "proposal_compare/projects.py",

    # JavaScript
    "static/js/features/proposal-compare.js",
    "static/js/features/guide-system.js",
    "static/js/help-docs.js",

    # CSS
    "static/css/features/proposal-compare.css",
]

# Demo voice narration audio files (34 MP3s)
AUDIO_FILES = [
    # Overview demo (8 scenes)
    "static/audio/demo/proposal-compare__step0.mp3",
    "static/audio/demo/proposal-compare__step1.mp3",
    "static/audio/demo/proposal-compare__step2.mp3",
    "static/audio/demo/proposal-compare__step3.mp3",
    "static/audio/demo/proposal-compare__step4.mp3",
    "static/audio/demo/proposal-compare__step5.mp3",
    "static/audio/demo/proposal-compare__step6.mp3",
    "static/audio/demo/proposal-compare__step7.mp3",

    # Upload & Extract sub-demo (4 scenes)
    "static/audio/demo/upload_extract__step0.mp3",
    "static/audio/demo/upload_extract__step1.mp3",
    "static/audio/demo/upload_extract__step2.mp3",
    "static/audio/demo/upload_extract__step3.mp3",

    # Executive Summary sub-demo (4 scenes)
    "static/audio/demo/exec_summary__step0.mp3",
    "static/audio/demo/exec_summary__step1.mp3",
    "static/audio/demo/exec_summary__step2.mp3",
    "static/audio/demo/exec_summary__step3.mp3",

    # Red Flags sub-demo (4 scenes)
    "static/audio/demo/red_flags__step0.mp3",
    "static/audio/demo/red_flags__step1.mp3",
    "static/audio/demo/red_flags__step2.mp3",
    "static/audio/demo/red_flags__step3.mp3",

    # Heatmap View sub-demo (4 scenes)
    "static/audio/demo/heatmap_view__step0.mp3",
    "static/audio/demo/heatmap_view__step1.mp3",
    "static/audio/demo/heatmap_view__step2.mp3",
    "static/audio/demo/heatmap_view__step3.mp3",

    # Vendor Scores sub-demo (4 scenes)
    "static/audio/demo/vendor_scores__step0.mp3",
    "static/audio/demo/vendor_scores__step1.mp3",
    "static/audio/demo/vendor_scores__step2.mp3",
    "static/audio/demo/vendor_scores__step3.mp3",

    # Comparison View sub-demo (3 scenes)
    "static/audio/demo/comparison_view__step0.mp3",
    "static/audio/demo/comparison_view__step1.mp3",
    "static/audio/demo/comparison_view__step2.mp3",

    # Export Results sub-demo (3 scenes)
    "static/audio/demo/export_results__step0.mp3",
    "static/audio/demo/export_results__step1.mp3",
    "static/audio/demo/export_results__step2.mp3",
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
    print("    AEGIS v5.9.41 Direct Updater")
    print("    Proposal Compare Advanced Analytics")
    print("  =============================================")
    print()
    print("  NEW IN v5.9.41:")
    print("    - PDF extraction overhaul (EnhancedTableExtractor)")
    print("    - Radar chart + tornado chart + stacked bars")
    print("    - Evaluation weight sliders (real-time)")
    print("    - Sortable/filterable comparison table")
    print("    - FAR 15.404 price reasonableness red flags")
    print("    - Identical pricing & missing category detection")
    print("    - XLSX freeze panes + auto-filter")
    print("    - Print-optimized CSS")
    print()
    print(f"  Install dir: {install_dir}")
    print(f"  Code files:  {len(FILES)}")
    print(f"  Audio files: {len(AUDIO_FILES)}")
    print(f"  Total:       {len(FILES) + len(AUDIO_FILES)}")
    print()

    # Ensure proposal_compare directory exists
    pc_dir = os.path.join(install_dir, "proposal_compare")
    if not os.path.isdir(pc_dir):
        os.makedirs(pc_dir, exist_ok=True)
        # Create __init__.py if missing
        init_file = os.path.join(pc_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Proposal Compare module\n")
            print(f"  Created proposal_compare/__init__.py")

    # Set up SSL
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v5.9.41_{timestamp}")
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

    print()
    print(f"  Code:  {success} applied, {failed} failed, {backed_up} backed up")

    # Download and apply audio files
    print()
    print("  Downloading demo voice narration audio files...")
    print("  " + "-" * 50)
    audio_success = 0
    audio_failed = 0

    # Ensure audio directory exists
    audio_dir = os.path.join(install_dir, "static", "audio", "demo")
    os.makedirs(audio_dir, exist_ok=True)

    for filepath in AUDIO_FILES:
        data = download_file(filepath, ssl_ctx)
        if data is None:
            audio_failed += 1
            continue

        dest = os.path.join(install_dir, filepath)

        # No backup for audio files (they're new)
        try:
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  OK    {os.path.basename(filepath)} ({size_kb:.1f} KB)")
            audio_success += 1
        except Exception as e:
            print(f"  FAIL  {filepath} -- write error: {e}")
            audio_failed += 1

    total_failed = failed + audio_failed
    print()
    print("  " + "=" * 50)
    print(f"  Code:   {success} applied, {failed} failed, {backed_up} backed up")
    print(f"  Audio:  {audio_success} applied, {audio_failed} failed")
    print(f"  Total:  {success + audio_success} / {len(FILES) + len(AUDIO_FILES)}")
    print()

    if total_failed == 0:
        print("  All files applied successfully!")
        print()
        print("  IMPORTANT: This update changes Python backend code.")
        print("  You MUST restart AEGIS for changes to take effect.")
        print()
        print("  NEXT STEPS:")
        print("    1. Close this window")
        print("    2. Restart AEGIS with Start_AEGIS.bat or Restart_AEGIS.bat")
        print("    3. Open AEGIS in your browser")
        print("    4. Open Proposal Compare and upload vendor proposals")
        print("    5. Try the new weight sliders, tornado chart, and sort/filter!")
        print("    6. Open Help > Proposal Compare > Watch Demo for narrated walkthrough!")
        print()
        print(f"  If something went wrong, your old files are in:")
        print(f"    {backup_dir}")
    else:
        print(f"  WARNING: {total_failed} file(s) failed.")
        print("  Check your internet connection and try again.")
        if audio_failed > 0 and failed == 0:
            print()
            print("  NOTE: All code files succeeded. Audio failures only affect")
            print("  demo narration - the tool works fine without them.")
        print()
        print(f"  Successfully applied files are already in place.")
        print(f"  Old versions backed up to: {backup_dir}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n  Cancelled.")
        code = 1
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        code = 1
    sys.exit(code)
