#!/usr/bin/env python3
"""
AEGIS v6.2.7 Apply Script
=========================
FIX: SP cinematic dashboard hardened with outer try/catch and forced visibility.

Changes:
- app.js: Outer try/catch wraps entire _showSpCinematicDashboard() — 280 lines
  of setup code were previously UNPROTECTED
- app.js: _startSPSelectedScan() now AWAITS _showSpCinematicDashboard() — errors
  were invisible unhandled promise rejections
- app.js: Aggressive inline styles force dashboard visibility even if CSS fails
- app.js: Outer catch re-enables buttons and restores sections — no more hard
  refresh needed
- app.js: Fallback dashboard element created if #batch-progress missing from DOM
- app.js: Error details captured in window._aegisLastDashboardError for diagnostics
- version.json / static/version.json: Bumped to 6.2.7

Run from AEGIS install directory:
    python apply_v6.2.7.py
    python3 apply_v6.2.7.py
"""

import os
import sys
import ssl
import shutil
import hashlib
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

FILES = {
    "static/js/app.js": "static/js/app.js",
    "version.json": "version.json",
    "static/version.json": "static/version.json",
}

EXPECTED_VERSION = "6.2.7"
BACKUP_DIR = f"backups/pre_v{EXPECTED_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def download_file(url, dest, max_retries=3, timeout=120):
    """Download a file with retry logic and SSL fallback."""
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(url, headers={"User-Agent": "AEGIS-Updater/6.2.7"})
            # Try with normal SSL first
            try:
                resp = urlopen(req, timeout=timeout)
            except (URLError, ssl.SSLError):
                # SSL fallback for corporate networks
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                resp = urlopen(req, timeout=timeout, context=ctx)

            data = resp.read()
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            return len(data)

        except Exception as e:
            print(f"    Attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                raise
            import time
            time.sleep(2 * attempt)
    return 0


def main():
    print("=" * 60)
    print(f"  AEGIS v{EXPECTED_VERSION} Apply Script")
    print("=" * 60)

    # Verify we're in the right directory
    if not os.path.exists("app.py"):
        print("\n[ERROR] app.py not found. Run this from the AEGIS install directory.")
        print("  Expected: cd ~/Desktop/Work_Tools/TechWriterReview")
        print("  Or:       cd C:\\path\\to\\AEGIS")
        sys.exit(1)

    if not os.path.exists("static"):
        print("\n[ERROR] static/ directory not found. Run this from the AEGIS install directory.")
        sys.exit(1)

    print(f"\nInstall directory: {os.getcwd()}")
    print(f"Backup directory:  {BACKUP_DIR}")

    # Step 1: Create backups
    print("\n-- Step 1: Creating backups --")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for rel_path in FILES.values():
        if os.path.exists(rel_path):
            backup_path = os.path.join(BACKUP_DIR, rel_path.replace("/", "_"))
            shutil.copy2(rel_path, backup_path)
            size = os.path.getsize(backup_path)
            print(f"  [BACKUP] {rel_path} ({size:,} bytes)")
        else:
            print(f"  [SKIP]   {rel_path} (not present)")

    # Step 2: Download files
    print("\n-- Step 2: Downloading files --")
    results = {}
    for remote_path, local_path in FILES.items():
        url = f"{BASE_URL}/{remote_path}"
        print(f"  Downloading {local_path}...", end=" ", flush=True)
        try:
            size = download_file(url, local_path)
            results[local_path] = size
            print(f"OK ({size:,} bytes)")
        except Exception as e:
            results[local_path] = 0
            print(f"FAILED: {e}")

    # Step 3: Verify downloads
    print("\n-- Step 3: Verifying files --")
    all_ok = True

    # Check app.js size (should be ~800KB)
    app_js_size = results.get("static/js/app.js", 0)
    if app_js_size < 100000:
        print(f"  [WARN] app.js is only {app_js_size:,} bytes — expected ~800KB!")
        print(f"         This may indicate a download failure.")
        all_ok = False
    else:
        print(f"  [OK]   app.js: {app_js_size:,} bytes")

    # Verify key markers in app.js
    try:
        with open("static/js/app.js", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()  # Read FULL file — SP code is at ~line 11745 (~700KB in)
        if "__AEGIS_SP_CINEMATIC" in content:
            print(f"  [OK]   app.js contains SP cinematic marker")
        else:
            print(f"  [WARN] app.js missing SP cinematic marker")
            all_ok = False

        if "_showSpCinematicDashboard" in content:
            print(f"  [OK]   app.js contains standalone dashboard function")
        else:
            print(f"  [WARN] app.js missing standalone dashboard function")
            all_ok = False

        if "_aegisLastDashboardError" in content:
            print(f"  [OK]   app.js contains diagnostic error capture")
        else:
            print(f"  [WARN] app.js missing diagnostic error capture (_aegisLastDashboardError)")
            all_ok = False
    except Exception as e:
        print(f"  [ERROR] Could not read app.js: {e}")
        all_ok = False

    # Check version.json
    try:
        import json
        with open("version.json", "r") as f:
            vdata = json.load(f)
        ver = vdata.get("version", "???")
        if ver == EXPECTED_VERSION:
            print(f"  [OK]   version.json: v{ver}")
        else:
            print(f"  [WARN] version.json shows v{ver}, expected v{EXPECTED_VERSION}")
    except Exception as e:
        print(f"  [ERROR] Could not read version.json: {e}")

    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print(f"  v{EXPECTED_VERSION} applied successfully!")
    else:
        print(f"  v{EXPECTED_VERSION} applied with warnings (see above)")

    print(f"\n  Backups saved to: {BACKUP_DIR}")
    print(f"\n  Next steps:")
    print(f"  1. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)")
    print(f"  2. Open F12 console and type: window.__AEGIS_SP_CINEMATIC")
    print(f"     -> Should show 'v{EXPECTED_VERSION}' immediately (no click needed)")
    print(f"  3. Test SP scan: Connect & Scan -> Select files -> Scan Selected")
    print(f"     -> Cinematic dashboard should appear automatically")
    print(f"  4. If dashboard fails, check: window._aegisLastDashboardError")
    print(f"     -> Will contain error details for diagnostics")
    print("=" * 60)

    if sys.platform == "win32":
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
