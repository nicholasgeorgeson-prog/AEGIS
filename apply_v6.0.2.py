#!/usr/bin/env python3
"""
AEGIS v6.0.2 Direct Updater
Downloads all changed files from GitHub and places them
directly into the correct locations in your AEGIS install.

Creates a backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v6.0.2.py
    python3 apply_v6.0.2.py

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

    # Python backend
    "routes/review_routes.py",
    "nlp/spelling/checker.py",
    "demo_audio_generator.py",

    # Templates
    "templates/index.html",

    # JavaScript
    "static/js/app.js",
    "static/js/features/fix-assistant-state.js",
    "static/js/help-docs.js",

    # CSS
    "static/css/features/fix-assistant.css",

    # Docs
    "CLAUDE.md",
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
    print("    AEGIS v6.0.2 Direct Updater")
    print("    Fix Assistant Reviewer Mode + Audio Fix")
    print("  =============================================")
    print()
    print("  FIX ASSISTANT REVIEWER MODE:")
    print("    - Reviewer / Document Owner mode toggle")
    print("    - Reviewer: accepted fixes become")
    print("      recommendation comments (no text changes)")
    print("    - Reviewer: rejected fixes skipped entirely")
    print("    - Owner (default): existing Track Changes +")
    print("      rejection comments behavior preserved")
    print("    - Role persists via localStorage")
    print("    - Export label updates based on role")
    print()
    print("  AUDIO FIX:")
    print("    - Demo audio voice changed to en-US-AvaNeural")
    print("    - Prevents accent shifts (English-only voice)")
    print()
    print("  OTHER:")
    print("    - US English spelling dictionary (from v6.0.1)")
    print("    - Updated help docs with reviewer workflow")
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
    backup_dir = os.path.join(install_dir, "backups", f"pre_v6.0.2_{timestamp}")
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
    print("  " + "=" * 50)
    print(f"  Code:  {success} applied, {failed} failed, {backed_up} backed up")
    print()

    if failed == 0:
        print("  All code files applied successfully!")
        print()
        print("  IMPORTANT: This update changes Python backend code.")
        print("  You MUST restart AEGIS for changes to take effect.")
        print()
        print("  DEMO AUDIO REGENERATION (optional):")
        print("  542 demo audio files need to be regenerated with")
        print("  the new en-US-AvaNeural voice. Run this after")
        print("  restarting AEGIS (requires internet + edge-tts):")
        print()
        regen_cmd = (
            '    python3 -c "\n'
            "    import sys; sys.path.insert(0, '.')\n"
            "    from demo_audio_generator import get_demo_scenes_from_js, generate_demo_audio\n"
            "    scenes = get_demo_scenes_from_js()\n"
            "    result = generate_demo_audio(scenes, output_dir='static/audio/demo', voice='en-US-AvaNeural', force=True)\n"
            "    print('Generated: %d, Errors: %d' % (result['stats']['generated'], result['stats']['errors']))\n"
            '    "'
        )
        print(regen_cmd)
        print()
        print("  NEXT STEPS:")
        print("    1. Close this window")
        print("    2. Restart AEGIS with Start_AEGIS.bat or Restart_AEGIS.bat")
        print("    3. Open AEGIS in your browser")
        print("    4. Open Fix Assistant to see the new Reviewer mode toggle")
        print("    5. (Optional) Regenerate demo audio with command above")
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
    sys.exit(code)
