#!/usr/bin/env python3
"""
AEGIS v6.2.8 Apply Script
=========================
ENHANCE: Diagnostic email now includes full console log capture, dashboard errors,
SP scan state, DOM state, and new console_logs.json attachment.

Changes:
- app.js: Enhanced collectDiagnosticData() with ConsoleCapture logs, dashboard error,
  SP scan state, DOM state (computed styles, CSS loading, section visibility)
- app.js: Enhanced formatDiagnosticsForEmail() with Dashboard Error, SP Scan State,
  Dashboard DOM State, Console Log Summary sections in email body text
- app.js: Enhanced emailDiagnosticsViaOutlook() sends frontend_diagnostics to backend
- core_routes.py: Parses frontend_diagnostics from POST body, adds to email body text,
  attaches as console_logs.json (capped at 3MB with smart trimming)
- version.json / static/version.json: Bumped to 6.2.8

Run from AEGIS install directory:
    python apply_v6.2.8.py
    python3 apply_v6.2.8.py
"""

import os
import sys
import ssl
import shutil
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

FILES = {
    "static/js/app.js": "static/js/app.js",
    "routes/core_routes.py": "routes/core_routes.py",
    "version.json": "version.json",
    "static/version.json": "static/version.json",
}

EXPECTED_VERSION = "6.2.8"
BACKUP_DIR = f"backups/pre_v{EXPECTED_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def download_file(url, dest, max_retries=3, timeout=120):
    """Download a file with retry logic and SSL fallback."""
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(url, headers={"User-Agent": f"AEGIS-Updater/{EXPECTED_VERSION}"})
            try:
                resp = urlopen(req, timeout=timeout)
            except (URLError, ssl.SSLError):
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

    if not os.path.exists("app.py"):
        print("\n[ERROR] app.py not found. Run this from the AEGIS install directory.")
        sys.exit(1)

    if not os.path.exists("static"):
        print("\n[ERROR] static/ directory not found.")
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

    # Step 3: Verify
    print("\n-- Step 3: Verifying files --")
    all_ok = True

    # Check app.js size
    app_js_size = results.get("static/js/app.js", 0)
    if app_js_size < 100000:
        print(f"  [WARN] app.js is only {app_js_size:,} bytes -- expected ~800KB!")
        all_ok = False
    else:
        print(f"  [OK]   app.js: {app_js_size:,} bytes")

    # Verify diagnostic enhancements in app.js
    try:
        with open("static/js/app.js", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "ConsoleCapture.getLogs" in content:
            print(f"  [OK]   app.js contains ConsoleCapture integration")
        else:
            print(f"  [WARN] app.js missing ConsoleCapture integration")
            all_ok = False
        if "frontend_diagnostics" in content:
            print(f"  [OK]   app.js sends frontend_diagnostics to backend")
        else:
            print(f"  [WARN] app.js missing frontend_diagnostics")
            all_ok = False
    except Exception as e:
        print(f"  [ERROR] Could not read app.js: {e}")
        all_ok = False

    # Verify core_routes.py
    try:
        with open("routes/core_routes.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "console_logs.json" in content:
            print(f"  [OK]   core_routes.py contains console_logs.json attachment")
        else:
            print(f"  [WARN] core_routes.py missing console_logs.json attachment")
            all_ok = False
    except Exception as e:
        print(f"  [ERROR] Could not read core_routes.py: {e}")
        all_ok = False

    # Check version
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
    print(f"\n  What's new in v{EXPECTED_VERSION}:")
    print(f"  - Diagnostic emails now include full console log capture")
    print(f"  - Dashboard errors, SP scan state, DOM state in email body")
    print(f"  - New console_logs.json attachment with all frontend diagnostics")
    print(f"  - SP-related logs highlighted in email for quick debugging")
    print(f"\n  Next steps:")
    print(f"  1. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)")
    print(f"  2. Test: Send a diagnostic email from Settings > Diagnostics")
    print(f"     -> Email should now include console_logs.json attachment")
    print(f"     -> Email body should show Dashboard DOM State section")
    print("=" * 60)

    if sys.platform == "win32":
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
