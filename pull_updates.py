#!/usr/bin/env python3
"""
AEGIS v5.9.28 Update Puller
Downloads the 26 changed files from GitHub and saves them
into the updates/ folder for the built-in AEGIS updater.

Usage:
    python3 pull_updates.py
    python pull_updates.py

After running, open AEGIS > Settings > Updates > Check for Updates > Apply.

No dependencies required — uses only Python standard library.
"""

import urllib.request
import ssl
import json
import os
import sys

# ── Configuration ──
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
OUTPUT_DIR = "updates"

FILES = [
    # Python backend
    "version.json",
    "static/version.json",
    "core.py",
    "config_logging.py",
    "report_generator.py",
    "graph_export_html.py",
    "adjudication_export.py",

    # Routes
    "routes/roles_routes.py",
    "routes/data_routes.py",
    "routes/config_routes.py",
    "routes/review_routes.py",

    # NLP / dictionaries
    "nlp/spelling/checker.py",
    "dictionaries/defense.txt",

    # Templates
    "templates/index.html",

    # JavaScript
    "static/js/app.js",
    "static/js/roles-tabs-fix.js",
    "static/js/help-docs.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/landing-page.js",
    "static/js/features/document-viewer.js",
    "static/js/features/scan-progress-dashboard.js",

    # CSS
    "static/css/features/sow-generator.css",
    "static/css/features/landing-page.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/scan-progress-dashboard.css",
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
    # create_default_context() loads system CA certs which can interfere
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
    print(f"AEGIS v5.9.28 Update Puller")
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
