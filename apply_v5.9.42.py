#!/usr/bin/env python3
"""
AEGIS v5.9.42 Direct Updater (Comprehensive)
Downloads ALL needed files from GitHub and places them
directly into the correct locations in your AEGIS install.

This is a FULL update - it includes everything from v5.9.40
through v5.9.42 to ensure nothing is missed.

Creates a backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v5.9.42.py
    python3 apply_v5.9.42.py

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

# COMPREHENSIVE file list - includes ALL files changed from v5.9.40 through v5.9.42
# plus any files the Windows machine may be missing from earlier updates
FILES = [
    # ── Version files (always first) ──
    "version.json",
    "static/version.json",

    # ── Python backend (core) ──
    "core.py",
    "scan_history.py",
    "docling_extractor.py",
    "config_logging.py",

    # ── Routes ──
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/scan_history_routes.py",

    # ── Hyperlink Validator (HV fix: except ImportError -> except Exception) ──
    "hyperlink_validator/__init__.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py",
    "hyperlink_validator/models.py",

    # ── Proposal Compare (v2.0 + Project Dashboard + Edit Persistence) ──
    "proposal_compare/__init__.py",
    "proposal_compare/parser.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/routes.py",
    "proposal_compare/projects.py",

    # ── Proposal Compare HTML Export (NEW in v5.9.42) ──
    "proposal_compare_export.py",

    # ── Templates ──
    "templates/index.html",

    # ── JavaScript ──
    "static/js/app.js",
    "static/js/update-functions.js",
    "static/js/help-docs.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/metrics-analytics.js",
    "static/js/features/guide-system.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/landing-page.js",

    # ── CSS ──
    "static/css/features/proposal-compare.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/landing-page.css",
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
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=60) as resp:
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
    print("  =========================================================")
    print("    AEGIS v5.9.42 Comprehensive Updater")
    print("    Includes ALL changes from v5.9.40 through v5.9.42")
    print("  =========================================================")
    print()
    print("  v5.9.42 NEW FEATURES:")
    print("    - Project Dashboard (browse, edit, drill-down)")
    print("    - Edit Persistence (auto-save proposal edits)")
    print("    - Tag to Project (assign/move proposals)")
    print("    - Interactive HTML Export (6-tab standalone report)")
    print("    - Live Demo Scenes for Proposal Compare")
    print()
    print("  v5.9.42 BUG FIXES:")
    print("    - HV 'resource not found' on Windows/OneDrive")
    print("    - Statement review stats missing method")
    print("    - PDF viewer error propagation")
    print()
    print("  v5.9.40 FEATURES (included for completeness):")
    print("    - Proposal Compare v2.0 (8 result tabs)")
    print("    - M&A Proposals tab")
    print("    - /api/capabilities endpoint")
    print("    - Export Highlighted Windows fix")
    print("    - Batch scan stability improvements")
    print()
    print(f"  Install dir: {install_dir}")
    print(f"  Total files: {len(FILES)}")
    print()

    # Ensure directories exist
    for dirname in ["proposal_compare", "hyperlink_validator", "routes",
                    "static/js/features", "static/css/features", "templates"]:
        dirpath = os.path.join(install_dir, dirname)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath, exist_ok=True)
            print(f"  Created directory: {dirname}/")

    # Ensure __init__.py files exist for Python packages
    for pkg in ["proposal_compare", "hyperlink_validator", "routes"]:
        init_file = os.path.join(install_dir, pkg, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# {pkg} module\n")
            print(f"  Created {pkg}/__init__.py")

    # Set up SSL
    print()
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v5.9.42_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"  Backup dir: {backup_dir}")
    print()

    # Download and apply each file
    print(f"  Downloading and applying {len(FILES)} files...")
    print("  " + "-" * 55)
    success = 0
    failed = 0
    backed_up = 0
    new_files = 0

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
        else:
            new_files += 1

        # Create directory structure if needed
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the new file
        try:
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            marker = " [NEW]" if not os.path.exists(os.path.join(backup_dir, filepath)) else ""
            print(f"  OK    {filepath} ({size_kb:.1f} KB){marker}")
            success += 1
        except Exception as e:
            print(f"  FAIL  {filepath} -- write error: {e}")
            failed += 1

    print()
    print("  " + "=" * 55)
    print(f"  Results: {success} applied, {failed} failed")
    print(f"           {backed_up} backed up, {new_files} new files")
    print()

    if failed == 0:
        print("  *** All files applied successfully! ***")
        print()
        print("  IMPORTANT: This update changes Python backend code.")
        print("  You MUST restart AEGIS for changes to take effect.")
        print()
        print("  NEXT STEPS:")
        print("    1. Close this window")
        print("    2. Double-click Restart_AEGIS.bat (or Start_AEGIS.bat)")
        print("    3. Open AEGIS in your browser (http://localhost:5050)")
        print("    4. Verify Hyperlink Validator loads (no 'resource not found')")
        print("    5. Try Proposal Compare > Projects button for dashboard")
        print("    6. Run a comparison > click 'Export Interactive HTML'")
        print()
        print(f"  Backups saved to: {backup_dir}")
    else:
        print(f"  WARNING: {failed} file(s) failed to download.")
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
        import traceback
        traceback.print_exc()
        code = 1
    sys.exit(code)
