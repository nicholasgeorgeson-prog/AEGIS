#!/usr/bin/env python3
"""
AEGIS v6.2.1 Apply Script
=========================
Downloads and applies v6.2.1 updates directly from GitHub.

Changes in v6.2.1:
  - FIX: Relationship Graph Edge Bundling — circle radius scales dynamically with data size
  - FIX: Relationship Graph Force-Directed — parameters scale with node count
  - ENH: Responsive CSS breakpoints added to 7 feature CSS files
  - FIX: Modal max-width changed to min(95vw, 1100px)
  - FIX: html_preview default value corrected from 0 to '' in review API
  - VERIFIED: Document rendering pipeline across all 4 review locations
  - VERIFIED: Fix Assistant export pipeline for Owner + Reviewer modes

Usage:
  python apply_v6.2.1.py

  Run from the AEGIS install directory (where app.py lives).
"""

import os
import sys
import json
import shutil
import urllib.request
import ssl
import hashlib
from datetime import datetime
from pathlib import Path

VERSION = "6.2.1"
GITHUB_RAW = "https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main"

# Files to download and their local paths
FILES = {
    # Core backend
    "routes/review_routes.py": "routes/review_routes.py",

    # Frontend - JavaScript
    "static/js/features/roles.js": "static/js/features/roles.js",
    "static/js/app.js": "static/js/app.js",

    # Frontend - CSS (responsive fixes)
    "static/css/features/metrics-analytics.css": "static/css/features/metrics-analytics.css",
    "static/css/features/landing-page.css": "static/css/features/landing-page.css",
    "static/css/features/hyperlink-enhanced.css": "static/css/features/hyperlink-enhanced.css",
    "static/css/features/settings.css": "static/css/features/settings.css",
    "static/css/features/export-suite.css": "static/css/features/export-suite.css",
    "static/css/features/guide-system.css": "static/css/features/guide-system.css",
    "static/css/modals.css": "static/css/modals.css",

    # New files from v6.2.0 (ensure they exist)
    "static/js/features/batch-results.js": "static/js/features/batch-results.js",
    "static/js/features/doc-review-viewer.js": "static/js/features/doc-review-viewer.js",
    "static/css/features/batch-results.css": "static/css/features/batch-results.css",
    "static/css/features/doc-review-viewer.css": "static/css/features/doc-review-viewer.css",
    "static/css/features/batch-progress-dashboard.css": "static/css/features/batch-progress-dashboard.css",

    # Auth service (v6.2.0)
    "auth_service.py": "auth_service.py",

    # SharePoint modules (v6.2.0)
    "sharepoint_connector.py": "sharepoint_connector.py",
    "sharepoint_link_validator.py": "sharepoint_link_validator.py",

    # Version + docs
    "version.json": "version.json",
    "static/version.json": "static/version.json",
    "CLAUDE.md": "CLAUDE.md",

    # Templates
    "templates/index.html": "templates/index.html",

    # Help docs
    "static/js/help-docs.js": "static/js/help-docs.js",
}


def get_ssl_context():
    """Create SSL context with fallback for certificate issues."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass

    ctx = ssl.create_default_context()
    try:
        ctx.load_default_certs()
    except Exception:
        pass

    # Fallback: disable verification (corporate networks)
    ctx_no_verify = ssl.create_default_context()
    ctx_no_verify.check_hostname = False
    ctx_no_verify.verify_mode = ssl.CERT_NONE
    return ctx_no_verify


def download_file(url, dest_path, ssl_ctx):
    """Download a file from URL to dest_path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-Updater/6.2.1"})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            content = resp.read()

        os.makedirs(os.path.dirname(dest_path) or '.', exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def backup_file(filepath):
    """Create timestamped backup of existing file."""
    if os.path.exists(filepath):
        backup_dir = os.path.join("backups", f"v{VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, os.path.basename(filepath))
        try:
            shutil.copy2(filepath, backup_path)
            return backup_path
        except Exception:
            return None
    return None


def verify_aegis_dir():
    """Verify we're in the AEGIS install directory."""
    if not os.path.exists("app.py"):
        print("\n[ERROR] app.py not found in current directory.")
        print("Please run this script from the AEGIS install directory.")
        print(f"  cd /path/to/AEGIS && python apply_v{VERSION}.py")
        return False
    if not os.path.isdir("static"):
        print("\n[ERROR] static/ directory not found.")
        print("Please run this script from the AEGIS install directory.")
        return False
    return True


def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           AEGIS v{VERSION} Update Applicator              ║
║                                                          ║
║  Relationship Graph scaling, responsive CSS fixes,       ║
║  html_preview bug fix, pipeline verifications             ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Step 1: Verify directory
    print("[Step 1] Verifying AEGIS installation directory...")
    if not verify_aegis_dir():
        sys.exit(1)
    print("  [OK] AEGIS directory confirmed")

    # Read current version
    try:
        with open("version.json", "r") as f:
            current = json.load(f)
        print(f"  Current version: {current.get('version', 'unknown')}")
    except Exception:
        print("  [WARN] Could not read current version")

    # Step 2: Create SSL context
    print("\n[Step 2] Setting up secure connection...")
    ssl_ctx = get_ssl_context()
    print("  [OK] SSL context ready")

    # Step 3: Download files
    print(f"\n[Step 3] Downloading {len(FILES)} files from GitHub...")
    success_count = 0
    fail_count = 0

    for remote_path, local_path in FILES.items():
        url = f"{GITHUB_RAW}/{remote_path}"
        print(f"  Downloading: {local_path}...", end=" ", flush=True)

        # Backup existing file
        backup = backup_file(local_path)

        if download_file(url, local_path, ssl_ctx):
            print("[OK]", end="")
            if backup:
                print(f" (backed up)")
            else:
                print(" (new file)")
            success_count += 1
        else:
            fail_count += 1
            # Restore backup if download failed
            if backup and os.path.exists(backup):
                shutil.copy2(backup, local_path)
                print(f"  [RESTORED] Original file restored from backup")

    # Step 4: Ensure required directories exist
    print("\n[Step 4] Ensuring directory structure...")
    for dir_path in ["routes", "static/js/features", "static/css/features", "templates", "backups"]:
        os.makedirs(dir_path, exist_ok=True)
    print("  [OK] All directories verified")

    # Step 5: Summary
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Update Summary                        ║
╠══════════════════════════════════════════════════════════╣
║  Files downloaded:  {success_count:>3} / {len(FILES):<3}                              ║
║  Files failed:      {fail_count:>3}                                    ║
║  Target version:    {VERSION:<10}                              ║
╚══════════════════════════════════════════════════════════╝
    """)

    if fail_count > 0:
        print(f"[WARN] {fail_count} file(s) failed to download.")
        print("  Check your internet connection and try again.")
        print("  Backups are in the backups/ directory.")
    else:
        print("[SUCCESS] All files updated successfully!")

    print(f"""
Next steps:
  1. Restart AEGIS server:
     - Double-click restart_aegis.sh (Mac)
     - Or: python3 app.py --debug

  2. Hard-refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

  3. Verify version shows {VERSION} in the bottom-right footer

Changes in v{VERSION}:
  • Relationship Graph circles now scale with data size
  • 7 CSS files now have responsive breakpoints (1366/1280/1024/768px)
  • Modals won't overflow on smaller screens
  • html_preview API default value fixed
  • Document rendering pipeline verified across all locations
  • Fix Assistant export verified for Owner + Reviewer modes
    """)


if __name__ == "__main__":
    main()
