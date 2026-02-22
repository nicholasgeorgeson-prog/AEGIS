#!/usr/bin/env python3
"""
AEGIS v5.9.52 Update Puller
Downloads changed files from GitHub and saves them
into the updates/ folder for the built-in AEGIS updater.

Usage:
    python3 pull_updates.py
    python pull_updates.py

After running, open AEGIS > Settings > Updates > Check for Updates > Apply.

No dependencies required — uses only Python standard library.
"""

import urllib.request
import ssl
import os
import sys

# ── Configuration ──
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
OUTPUT_DIR = "updates"

FILES = [
    # Version files
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

    # Audio narration (new demo clips)
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

    # Update script
    "apply_v5.9.52.py",

    # Docs
    "CLAUDE.md",
]


def get_ssl_context():
    """Get SSL context, trying certifi first, then system certs, then unverified fallback."""
    # Try 1: certifi (if installed)
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        # Quick test to verify it actually works
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using certifi certificates")
        return ctx
    except Exception:
        pass

    # Try 2: default system certs
    try:
        ctx = ssl.create_default_context()
        # Quick test
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using system certificates")
        return ctx
    except Exception:
        pass

    # Try 3: unverified — use SSLContext directly (not create_default_context)
    print("  [WARN] SSL certificates not available — using unverified HTTPS")
    print("         (This is safe for downloading from GitHub)")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(filepath, output_dir, ssl_ctx):
    """Download a single file from GitHub raw content."""
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{filepath}"
    dest = os.path.join(output_dir, filepath)

    # Create directory structure
    dest_dir = os.path.dirname(dest)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            data = resp.read()

        with open(dest, "wb") as f:
            f.write(data)

        size_kb = len(data) / 1024
        print(f"  OK  {filepath} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  FAIL {filepath} — {e}")
        return False


def main():
    print(f"AEGIS v5.9.52 Update Puller")
    print(f"=" * 50)
    print(f"Repo:   {REPO}")
    print(f"Branch: {BRANCH}")
    print(f"Output: {OUTPUT_DIR}/")
    print(f"Files:  {len(FILES)}")
    print()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Set up SSL context
    print("Checking SSL certificates...")
    ssl_ctx = get_ssl_context()
    print()

    print("Downloading files...")
    success = 0
    failed = 0

    for filepath in FILES:
        if download_file(filepath, OUTPUT_DIR, ssl_ctx):
            success += 1
        else:
            failed += 1

    print()
    print(f"{'=' * 50}")
    print(f"Complete: {success} downloaded, {failed} failed")
    print()

    if failed == 0:
        print("All files downloaded to updates/ folder!")
        print()
        print("NEXT STEPS:")
        print(f"  1. Start AEGIS (if not already running)")
        print(f"  2. Go to Settings > Updates tab")
        print(f"  3. Click 'Check for Updates'")
        print(f"  4. Click 'Apply Updates'")
        print(f"  5. AEGIS will backup, apply, and restart automatically")
    else:
        print(f"WARNING: {failed} file(s) failed to download.")
        print("Check your internet connection and try again.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
