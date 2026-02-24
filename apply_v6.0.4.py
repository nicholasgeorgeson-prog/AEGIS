#!/usr/bin/env python3
"""
AEGIS v6.0.4 Update
Downloads changed files from GitHub and places them directly into your AEGIS install.

Creates a timestamped backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v6.0.4.py
    python3 apply_v6.0.4.py

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

# ============================================================
# FILES CHANGED IN v6.0.4
# ============================================================
CODE_FILES = [
    # --- Version files (always first) ---
    "version.json",
    "static/version.json",

    # --- PDF viewer zoom/pan fix ---
    "static/js/features/pdf-viewer.js",

    # --- Proposal Compare duplicate detection + CSS fix ---
    "static/js/features/proposal-compare.js",
    "static/css/features/proposal-compare.css",

    # --- Documentation & Help ---
    "CLAUDE.md",
    "static/js/help-docs.js",
    "static/js/features/guide-system.js",

    # --- Demo audio (new subDemos) ---
    "static/audio/demo/manifest.json",
    "static/audio/demo/pdf_zoom_pan__step0.mp3",
    "static/audio/demo/pdf_zoom_pan__step1.mp3",
    "static/audio/demo/pdf_zoom_pan__step2.mp3",
    "static/audio/demo/pdf_zoom_pan__step3.mp3",
    "static/audio/demo/duplicate_detection__step0.mp3",
    "static/audio/demo/duplicate_detection__step1.mp3",
    "static/audio/demo/duplicate_detection__step2.mp3",
    "static/audio/demo/duplicate_detection__step3.mp3",
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


def download_file(filepath, ssl_ctx, timeout=30):
    """Download a single file from GitHub raw content. Returns bytes or None."""
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{filepath}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
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
        print("=" * 60)
        print("  WARNING: This doesn't look like an AEGIS directory!")
        print(f"  Current location: {install_dir}")
        print()
        print("  Expected to find app.py and static/ folder here.")
        print("  Place this script in your AEGIS installation directory.")
        print("=" * 60)
        print()
        resp = input("  Continue anyway? (y/n): ").strip().lower()
        if resp != 'y':
            print("  Cancelled.")
            return 1

    print()
    print("  " + "=" * 58)
    print("    AEGIS v6.0.4 Update")
    print("  " + "=" * 58)
    print()
    print("  Changes in v6.0.4:")
    print("    - FIX: PDF viewer zoom preserves viewport center")
    print("    - FIX: PDF click-and-drag panning scrolls correctly")
    print("    - FIX: PDF auto-fits to container width on render")
    print("    - NEW: Proposal Compare duplicate detection")
    print("    - ENH: Duplicate upload prompt (replace/keep)")
    print("    - ENH: Post-extraction project duplicate check")
    print("    - DOC: Help docs updated with v6.0.2-6.0.4 changelog")
    print("    - DOC: PDF zoom/pan + duplicate detection demo scenes")
    print("    - DOC: 8 new voiceover audio clips for demos")
    print()
    print(f"  Install dir:  {install_dir}")
    print(f"  Files:        {len(CODE_FILES)}")
    print()

    # Set up SSL
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v6.0.4_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"  Backup dir: {backup_dir}")
    print()

    # ========================================================
    # Download and apply files
    # ========================================================
    print("  Downloading and applying files...")
    print("  " + "-" * 54)
    success = 0
    failed = 0
    backed_up = 0

    for filepath in CODE_FILES:
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

        # Write the new file (binary safe)
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

    # ========================================================
    # SUMMARY
    # ========================================================
    print("  " + "=" * 58)
    print("  SUMMARY")
    print("  " + "=" * 58)
    print(f"  Files:   {success} applied, {failed} failed, {backed_up} backed up")
    print()

    if failed == 0:
        print("  All files applied successfully!")
        print()
        print("  This update only changes frontend files (JS/CSS).")
        print("  A hard browser refresh (Ctrl+Shift+R) should suffice.")
        print("  If issues persist, restart AEGIS.")
        print()
        print("  NEXT STEPS:")
        print("    1. Hard refresh your browser (Ctrl+Shift+R)")
        print("    2. Verify version shows 6.0.4 in the footer")
        print("    3. Test PDF viewer zoom/pan in Proposal Compare")
        print("    4. Test duplicate proposal upload detection")
        print()
        print(f"  If something went wrong, your old files are in:")
        print(f"    {backup_dir}")
    else:
        print(f"  WARNING: {failed} file(s) failed to download/apply.")
        print("  Check your internet connection and try again.")
        print()
        print(f"  Successfully applied files are already in place.")
        print(f"  Old files backed up to: {backup_dir}")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n  Cancelled.")
        code = 1
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        code = 1
    sys.exit(code)
