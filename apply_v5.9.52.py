#!/usr/bin/env python3
"""
AEGIS v5.9.52 Direct Updater
Downloads all changed files from v5.9.49-v5.9.52 (Learning System)
and places them directly into the correct locations in your AEGIS install.

Creates a backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v5.9.52.py
    python3 apply_v5.9.52.py

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

    # Learner modules (NEW in v5.9.50)
    "review_learner.py",
    "roles_learner.py",
    "statement_forge/statement_learner.py",
    "hyperlink_validator/hv_learner.py",
    "proposal_compare/pattern_learner.py",

    # Backend routes (modified for learning endpoints)
    "routes/config_routes.py",
    "routes/_shared.py",

    # Core integration (learned pattern suppression)
    "core.py",
    "scan_history.py",

    # Statement Forge (learning triggers)
    "statement_forge/routes.py",

    # Hyperlink Validator (learning triggers)
    "hyperlink_validator/routes.py",

    # Review routes (Fix Assistant learning)
    "routes/review_routes.py",

    # Proposal Compare (parser fixes, learning, structure analyzer)
    "proposal_compare/parser.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py",

    # Frontend JS
    "static/js/app.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/guide-system.js",
    "static/js/help-docs.js",

    # Frontend CSS
    "static/css/features/settings.css",
    "static/css/features/proposal-compare.css",

    # HTML template
    "templates/index.html",
]

# Audio narration files for new demo scenes
AUDIO_FILES = [
    "static/audio/demo/manifest.json",
    "static/audio/demo/pattern_learning__step0.mp3",
    "static/audio/demo/pattern_learning__step1.mp3",
    "static/audio/demo/pattern_learning__step2.mp3",
    "static/audio/demo/pattern_learning__step3.mp3",
    "static/audio/demo/learning_system__step0.mp3",
    "static/audio/demo/learning_system__step1.mp3",
    "static/audio/demo/learning_system__step2.mp3",
    "static/audio/demo/learning_system__step3.mp3",
    "static/audio/demo/learning_system__step4.mp3",
    "static/audio/demo/learning_system__step5.mp3",
]


def get_ssl_context():
    """Get SSL context with aggressive fallback for embedded Python."""
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
    install_dir = os.path.dirname(os.path.abspath(__file__))

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
    print("    AEGIS v5.9.52 Direct Updater")
    print("    Learning System + Settings UI")
    print("  =============================================")
    print()
    print("  v5.9.49 — LOCAL PATTERN LEARNING:")
    print("    - Proposal Compare learns from user edits")
    print("    - Category overrides, company patterns")
    print("    - 5 parser extraction fixes")
    print()
    print("  v5.9.50 — UNIVERSAL LEARNING SYSTEM:")
    print("    - Extended to all 5 AEGIS modules")
    print("    - Document Review, Statement Forge, Roles,")
    print("      Hyperlink Validator, Proposal Compare")
    print("    - All patterns stored locally, never uploaded")
    print()
    print("  v5.9.51 — DEMO SCENES + AUDIO:")
    print("    - Pattern learning sub-demo (4 scenes)")
    print("    - Learning system sub-demo (6 scenes)")
    print("    - 10 new MP3 narration clips")
    print()
    print("  v5.9.52 — SETTINGS UI:")
    print("    - New Learning tab in Settings modal")
    print("    - Global on/off toggle")
    print("    - Per-module View/Export/Clear actions")
    print("    - Export All / Clear All global actions")
    print("    - Pattern viewer modal")
    print()
    print(f"  Install dir:  {install_dir}")
    print(f"  Code files:   {len(FILES)}")
    print(f"  Audio files:  {len(AUDIO_FILES)}")
    print()

    # Ensure required directories exist
    for subdir in ["proposal_compare", "statement_forge", "hyperlink_validator",
                    "routes", os.path.join("static", "audio", "demo")]:
        d = os.path.join(install_dir, subdir)
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
            init_file = os.path.join(d, "__init__.py")
            if subdir in ("proposal_compare", "statement_forge", "hyperlink_validator", "routes"):
                if not os.path.exists(init_file):
                    with open(init_file, "w") as f:
                        f.write(f"# {subdir} module\n")
                    print(f"  Created {subdir}/__init__.py")

    # Set up SSL
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v5.9.52_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"  Backup dir: {backup_dir}")
    print()

    # Download and apply code files
    print("  Downloading and applying code files...")
    print("  " + "-" * 50)
    success = 0
    failed = 0
    backed_up = 0

    for filepath in FILES:
        data = download_file(filepath, ssl_ctx)
        if data is None:
            failed += 1
            continue

        dest = os.path.join(install_dir, filepath)

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

        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

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
    print()

    # Download and apply audio files
    print("  Downloading audio narration files...")
    print("  " + "-" * 50)
    audio_success = 0
    audio_failed = 0

    for filepath in AUDIO_FILES:
        data = download_file(filepath, ssl_ctx)
        if data is None:
            audio_failed += 1
            continue

        dest = os.path.join(install_dir, filepath)
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        try:
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  OK    {filepath} ({size_kb:.1f} KB)")
            audio_success += 1
        except Exception as e:
            print(f"  FAIL  {filepath} -- write error: {e}")
            audio_failed += 1

    print()
    print("  " + "=" * 50)
    print(f"  Code:   {success} applied, {failed} failed")
    print(f"  Audio:  {audio_success} applied, {audio_failed} failed")
    print()

    total_failed = failed + audio_failed
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
        print("    4. Go to Settings > Learning tab to see the new controls")
        print("    5. Try editing proposals — AEGIS now learns your patterns!")
        print()
        print(f"  If something went wrong, your old files are in:")
        print(f"    {backup_dir}")
    else:
        print(f"  WARNING: {total_failed} file(s) failed.")
        print("  Check your internet connection and try again.")
        if audio_failed > 0 and failed == 0:
            print()
            print("  NOTE: Code files applied OK. Audio failures are non-critical.")
            print("  Demos will use Web Speech API fallback for missing audio.")
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
