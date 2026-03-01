#!/usr/bin/env python3
"""
AEGIS v6.3.0 Update Script
===========================
Fixes SharePoint scan timeout issue.

ROOT CAUSE: v6.2.9 moved HeadlessSP connector creation to a background thread
so the HTTP endpoint returns immediately. However, Python file changes require
a SERVER RESTART to take effect. If the server wasn't restarted after applying
v6.2.9, the old synchronous code was still running in memory, causing 30+ second
hangs that triggered the frontend's 30-second timeout.

CHANGES IN v6.3.0:
  - Frontend AbortController timeout increased from 30s to 120s (safety net)
  - Timeout error message now suggests server restart after updates
  - Enhanced diagnostic email with SP/auth diagnostics
  - Version bump to 6.3.0

CRITICAL: After running this script, you MUST restart the AEGIS server!
  Double-click Start_AEGIS.bat (or close and reopen AEGIS)
"""

import os
import sys
import ssl
import json
import shutil
import urllib.request
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
EXPECTED_VERSION = "6.3.0"
BACKUP_DIR = f"backups/pre_v{EXPECTED_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Files to update: {remote_path: local_path}
FILES = {
    # Core Python (REQUIRE SERVER RESTART)
    "routes/review_routes.py": "routes/review_routes.py",
    "routes/core_routes.py": "routes/core_routes.py",

    # Frontend (take effect on browser refresh)
    "static/js/app.js": "static/js/app.js",

    # Version files
    "version.json": "version.json",
    "static/version.json": "static/version.json",
}


def download_file(url, dest):
    """Download with SSL fallback for corporate networks."""
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx) as resp:
                with open(dest, 'wb') as f:
                    f.write(resp.read())
            return True
        except Exception as e:
            print(f"    [ERROR] Download failed: {e}")
            return False


def main():
    print("=" * 60)
    print(f"  AEGIS v{EXPECTED_VERSION} Update")
    print("=" * 60)
    print()

    # ─── Verify we're in the right directory ─────────────────────────────
    if not os.path.isfile("app.py") or not os.path.isdir("static"):
        print("  [ERROR] Must run from the AEGIS install directory.")
        print("  Expected to find app.py and static/ folder.")
        print()
        # Try common locations
        for path in [
            r"C:\Users\M26402\OneDrive - NGC\Desktop\Doc Review\AEGIS",
            os.path.expanduser("~/Desktop/Work_Tools/TechWriterReview"),
        ]:
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, "app.py")):
                print(f"  Found AEGIS at: {path}")
                print(f"  Please run: cd \"{path}\" && python apply_v{EXPECTED_VERSION}.py")
                break
        input("\nPress Enter to exit...")
        sys.exit(1)

    # ─── Detect Python (embedded vs system) ──────────────────────────────
    python_exe = sys.executable
    if os.path.exists("python/python.exe"):
        python_exe = os.path.join(os.getcwd(), "python", "python.exe")
        print(f"  Using embedded Python: python/python.exe")
    else:
        print(f"  Using Python: {python_exe}")
    print()

    # ─── Step 1: Backup existing files ───────────────────────────────────
    print("  Step 1: Backing up existing files...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backed_up = 0
    for remote, local in FILES.items():
        if os.path.isfile(local):
            dest = os.path.join(BACKUP_DIR, local.replace("/", "_").replace("\\", "_"))
            try:
                shutil.copy2(local, dest)
                backed_up += 1
            except Exception as e:
                print(f"    [WARN] Could not backup {local}: {e}")
    print(f"    Backed up {backed_up} files to {BACKUP_DIR}/")
    print()

    # ─── Step 2: Ensure directories exist ────────────────────────────────
    print("  Step 2: Checking directories...")
    dirs_needed = set()
    for local in FILES.values():
        d = os.path.dirname(local)
        if d:
            dirs_needed.add(d)
    for d in sorted(dirs_needed):
        os.makedirs(d, exist_ok=True)
        init = os.path.join(d, "__init__.py")
        if not os.path.isfile(init) and not d.startswith("static"):
            with open(init, "w") as f:
                f.write("")
    print("    OK")
    print()

    # ─── Step 3: Download files ──────────────────────────────────────────
    print(f"  Step 3: Downloading {len(FILES)} files from GitHub...")
    success = 0
    failed = 0
    for remote, local in FILES.items():
        url = f"{BASE_URL}/{remote}"
        short = remote.split("/")[-1]
        print(f"    {short}...", end=" ", flush=True)
        if download_file(url, local):
            size = os.path.getsize(local)
            print(f"OK ({size:,} bytes)")
            success += 1
        else:
            print("FAILED")
            failed += 1
    print(f"\n    Downloaded: {success}/{len(FILES)}", end="")
    if failed:
        print(f" ({failed} FAILED)")
    else:
        print(" (all OK)")
    print()

    # ─── Step 4: Verify key changes ─────────────────────────────────────
    print("  Step 4: Verifying updates...")
    checks_passed = 0
    checks_total = 0

    # Check version
    checks_total += 1
    try:
        with open("version.json", "r", encoding="utf-8", errors="replace") as f:
            vdata = json.load(f)
        if vdata.get("version") == EXPECTED_VERSION:
            print(f"    [OK] version.json = {EXPECTED_VERSION}")
            checks_passed += 1
        else:
            print(f"    [WARN] version.json = {vdata.get('version')} (expected {EXPECTED_VERSION})")
    except Exception as e:
        print(f"    [WARN] Could not read version.json: {e}")

    # Check frontend timeout fix (120s instead of 30s)
    checks_total += 1
    try:
        with open("static/js/app.js", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "120000" in content and "timeout after 120s" in content:
            print("    [OK] Frontend SP timeout = 120 seconds")
            checks_passed += 1
        else:
            print("    [WARN] Frontend timeout change not found")
    except Exception as e:
        print(f"    [WARN] Could not verify app.js: {e}")

    # Check async scan endpoint (background thread pattern)
    checks_total += 1
    try:
        with open("routes/review_routes.py", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "connecting" in content and "_process_sharepoint_scan_async" in content:
            print("    [OK] review_routes.py has async SP scan endpoint")
            checks_passed += 1
        else:
            print("    [WARN] Async SP scan pattern not found in review_routes.py")
    except Exception as e:
        print(f"    [WARN] Could not verify review_routes.py: {e}")

    # Check enhanced diagnostics
    checks_total += 1
    try:
        with open("routes/core_routes.py", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "auth_service" in content or "sharepoint" in content.lower():
            print("    [OK] core_routes.py has enhanced diagnostics")
            checks_passed += 1
        else:
            print("    [WARN] Enhanced diagnostics not found in core_routes.py")
    except Exception as e:
        print(f"    [WARN] Could not verify core_routes.py: {e}")

    print(f"\n    Checks: {checks_passed}/{checks_total} passed")
    print()

    # ─── Summary ─────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"  AEGIS v{EXPECTED_VERSION} Update Complete")
    print("=" * 60)
    print()
    print("  What's New:")
    print("    - SP scan frontend timeout: 30s → 120s (safety net)")
    print("    - Better error message on timeout (suggests server restart)")
    print("    - Enhanced diagnostic email with SP/auth info")
    print("    - v6.2.9 async SP endpoint (server restart loads it)")
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║                                                      ║")
    print("  ║   >>> IMPORTANT: RESTART THE AEGIS SERVER NOW <<<    ║")
    print("  ║                                                      ║")
    print("  ║   Python backend changes only take effect after a    ║")
    print("  ║   server restart. Without restarting, the old code   ║")
    print("  ║   stays in memory and SharePoint scans will hang.    ║")
    print("  ║                                                      ║")
    print("  ║   To restart:                                        ║")
    print("  ║     1. Close the AEGIS terminal/browser window       ║")
    print("  ║     2. Double-click Start_AEGIS.bat                  ║")
    print("  ║                                                      ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    print(f"  Backup location: {BACKUP_DIR}/")
    print()
    input("  Press Enter to exit...")


if __name__ == "__main__":
    main()
