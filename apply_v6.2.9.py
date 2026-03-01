#!/usr/bin/env python3
"""
AEGIS v6.2.9 Update Script
===========================
Covers ALL changes from v6.2.3 to v6.2.9 (incremental update).
If coming from an older version, run apply_v6.2.3.py first.

Major changes in this update:
  v6.2.9 - CRITICAL: SharePoint scan-selected no longer blocks HTTP response.
           HeadlessSPConnector creation + SSO auth moved to background thread.
           Frontend fetch has 30-second AbortController timeout.
           New 'connecting' phase in scan state for dashboard display.
  v6.2.8 - Diagnostic email includes full console log capture.
  v6.2.7 - SP cinematic dashboard visibility fixes.
  v6.2.6 - SP cinematic dashboard direct launch.
  v6.2.5 - Apply script improvements.
  v6.2.4 - SP scan uses cinematic batch progress dashboard, minimize badge.
  v6.2.3 - Update manager rollback manifest format, Windows restart via Start_AEGIS.bat.

Also includes auth_service.py safety net hotfix (v6.2.2), responsive CSS (v6.2.1),
D3.js graph scaling (v6.2.1), async batch scan (v6.2.0), unified auth service (v6.2.0),
batch results IIFE (v6.2.0), and all SP improvements from v6.1.x.

Usage:
  1. Copy this script to your AEGIS install directory
  2. Open Command Prompt in that directory
  3. Run: python apply_v6.2.9.py
     (or: python\\python.exe apply_v6.2.9.py  for OneClick installs)
"""

import os
import sys
import json
import shutil
import ssl
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ── Configuration ──────────────────────────────────────────────────────────
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
EXPECTED_VERSION = "6.2.9"
BACKUP_DIR = f"backups/pre_v{EXPECTED_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Files to download: {remote_path: local_path}
# Organized by category for clarity
FILES = {}

# ── Python Core ────────────────────────────────────────────────────────────
FILES.update({
    "app.py": "app.py",
    "core.py": "core.py",
    "auth_service.py": "auth_service.py",
    "update_manager.py": "update_manager.py",
    "sharepoint_connector.py": "sharepoint_connector.py",
    "sharepoint_link_validator.py": "sharepoint_link_validator.py",
    "comprehensive_hyperlink_checker.py": "comprehensive_hyperlink_checker.py",
    "review_learner.py": "review_learner.py",
    "config_logging.py": "config_logging.py",
})

# ── Python Routes ──────────────────────────────────────────────────────────
FILES.update({
    "routes/__init__.py": "routes/__init__.py",
    "routes/_shared.py": "routes/_shared.py",
    "routes/review_routes.py": "routes/review_routes.py",
    "routes/config_routes.py": "routes/config_routes.py",
    "routes/core_routes.py": "routes/core_routes.py",
    "routes/data_routes.py": "routes/data_routes.py",
    "routes/roles_routes.py": "routes/roles_routes.py",
})

# ── Hyperlink Validator ────────────────────────────────────────────────────
FILES.update({
    "hyperlink_validator/__init__.py": "hyperlink_validator/__init__.py",
    "hyperlink_validator/validator.py": "hyperlink_validator/validator.py",
    "hyperlink_validator/headless_validator.py": "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/routes.py": "hyperlink_validator/routes.py",
    "hyperlink_validator/models.py": "hyperlink_validator/models.py",
    "hyperlink_validator/export.py": "hyperlink_validator/export.py",
    "hyperlink_validator/storage.py": "hyperlink_validator/storage.py",
    "hyperlink_validator/hv_learner.py": "hyperlink_validator/hv_learner.py",
})

# ── Proposal Compare ──────────────────────────────────────────────────────
FILES.update({
    "proposal_compare/__init__.py": "proposal_compare/__init__.py",
    "proposal_compare/parser.py": "proposal_compare/parser.py",
    "proposal_compare/analyzer.py": "proposal_compare/analyzer.py",
    "proposal_compare/routes.py": "proposal_compare/routes.py",
    "proposal_compare/projects.py": "proposal_compare/projects.py",
    "proposal_compare/structure_analyzer.py": "proposal_compare/structure_analyzer.py",
    "proposal_compare/pattern_learner.py": "proposal_compare/pattern_learner.py",
})

# ── Statement Forge ────────────────────────────────────────────────────────
FILES.update({
    "statement_forge/statement_learner.py": "statement_forge/statement_learner.py",
    "statement_forge/routes.py": "statement_forge/routes.py",
})

# ── Other Python ───────────────────────────────────────────────────────────
FILES.update({
    "roles_learner.py": "roles_learner.py",
    "scan_history.py": "scan_history.py",
    "portfolio/routes.py": "portfolio/routes.py",
})

# ── JavaScript Core ────────────────────────────────────────────────────────
FILES.update({
    "static/js/app.js": "static/js/app.js",
    "static/js/help-docs.js": "static/js/help-docs.js",
    "static/js/update-functions.js": "static/js/update-functions.js",
})

# ── JavaScript Features ───────────────────────────────────────────────────
FILES.update({
    "static/js/features/batch-results.js": "static/js/features/batch-results.js",
    "static/js/features/landing-page.js": "static/js/features/landing-page.js",
    "static/js/features/roles.js": "static/js/features/roles.js",
    "static/js/features/metrics-analytics.js": "static/js/features/metrics-analytics.js",
    "static/js/features/hyperlink-validator.js": "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js": "static/js/features/hyperlink-validator-state.js",
    "static/js/features/scan-progress-dashboard.js": "static/js/features/scan-progress-dashboard.js",
    "static/js/features/proposal-compare.js": "static/js/features/proposal-compare.js",
    "static/js/features/guide-system.js": "static/js/features/guide-system.js",
    "static/js/features/pdf-viewer.js": "static/js/features/pdf-viewer.js",
    "static/js/features/doc-compare.js": "static/js/features/doc-compare.js",
    "static/js/features/statement-history.js": "static/js/features/statement-history.js",
})

# ── CSS Files ──────────────────────────────────────────────────────────────
FILES.update({
    "static/css/layout.css": "static/css/layout.css",
    "static/css/modals.css": "static/css/modals.css",
    "static/css/base.css": "static/css/base.css",
    "static/css/features/batch-progress-dashboard.css": "static/css/features/batch-progress-dashboard.css",
    "static/css/features/batch-results.css": "static/css/features/batch-results.css",
    "static/css/features/hyperlink-enhanced.css": "static/css/features/hyperlink-enhanced.css",
    "static/css/features/hyperlink-validator.css": "static/css/features/hyperlink-validator.css",
    "static/css/features/metrics-analytics.css": "static/css/features/metrics-analytics.css",
    "static/css/features/roles-studio.css": "static/css/features/roles-studio.css",
    "static/css/features/guide-system.css": "static/css/features/guide-system.css",
    "static/css/features/settings.css": "static/css/features/settings.css",
    "static/css/features/export-suite.css": "static/css/features/export-suite.css",
    "static/css/features/landing-page.css": "static/css/features/landing-page.css",
    "static/css/features/proposal-compare.css": "static/css/features/proposal-compare.css",
    "static/css/features/scan-progress-dashboard.css": "static/css/features/scan-progress-dashboard.css",
    "static/css/features/doc-compare.css": "static/css/features/doc-compare.css",
    "static/css/features/statement-history.css": "static/css/features/statement-history.css",
})

# ── HTML & Config ──────────────────────────────────────────────────────────
FILES.update({
    "templates/index.html": "templates/index.html",
    "version.json": "version.json",
    "static/version.json": "static/version.json",
    "README.md": "README.md",
    "requirements.txt": "requirements.txt",
})

# ── Wheel packages (offline pip install) ──────────────────────────────────
FILES.update({
    "wheels/truststore-0.10.4-py3-none-any.whl": "wheels/truststore-0.10.4-py3-none-any.whl",
})


# ── Download helper ────────────────────────────────────────────────────────
def download_file(url, dest, retries=3):
    """Download with SSL fallback for corporate networks."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "AEGIS-Updater/6.2.9"})
            try:
                resp = urlopen(req, timeout=30)
            except (URLError, ssl.SSLError):
                # SSL fallback for corporate CA certificates
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                resp = urlopen(req, timeout=30, context=ctx)

            data = resp.read()
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            return True

        except Exception as e:
            if attempt < retries - 1:
                print(f"    Retry {attempt + 1}/{retries - 1}: {e}")
                time.sleep(2 ** attempt)
            else:
                print(f"    FAILED: {e}")
                return False
    return False


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"  AEGIS v{EXPECTED_VERSION} Update Script")
    print(f"  Covers changes from v6.2.3 to v{EXPECTED_VERSION}")
    print("=" * 60)
    print()

    # Verify we're in the right directory
    if not os.path.exists("app.py"):
        print("[ERROR] app.py not found in current directory.")
        print("        Please run this script from the AEGIS install directory.")
        print()
        if os.path.exists("python/python.exe"):
            print("  Hint: Try running from the parent directory:")
            print("        cd ..")
            print(f"        python\\python.exe apply_v{EXPECTED_VERSION}.py")
        sys.exit(1)

    if not os.path.exists("static"):
        print("[ERROR] static/ folder not found. Not an AEGIS directory.")
        sys.exit(1)

    # ── Step 1: Create backups ─────────────────────────────────────────
    print(f"Step 1/4: Creating backups in {BACKUP_DIR}/")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backed_up = 0

    for remote_path, local_path in FILES.items():
        if os.path.exists(local_path):
            backup_path = os.path.join(BACKUP_DIR, local_path)
            os.makedirs(os.path.dirname(backup_path) if os.path.dirname(backup_path) else BACKUP_DIR, exist_ok=True)
            try:
                shutil.copy2(local_path, backup_path)
                backed_up += 1
            except Exception as e:
                print(f"  [WARN] Could not backup {local_path}: {e}")

    print(f"  Backed up {backed_up} existing files")
    print()

    # ── Step 2: Ensure directories exist ───────────────────────────────
    print("Step 2/4: Ensuring directories exist...")
    dirs_to_create = [
        "routes", "hyperlink_validator", "proposal_compare",
        "statement_forge", "portfolio", "static/js/features",
        "static/css/features", "templates", "static/js/vendor/pdfjs",
        "wheels",
    ]
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)

    # Ensure __init__.py files exist
    for pkg in ["routes", "hyperlink_validator", "proposal_compare", "statement_forge", "portfolio"]:
        init_file = os.path.join(pkg, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("")
            print(f"  Created {init_file}")
    print()

    # ── Step 3: Download all files ─────────────────────────────────────
    print(f"Step 3/4: Downloading {len(FILES)} files from GitHub...")
    print()

    success = 0
    failed = 0
    failed_files = []

    for i, (remote_path, local_path) in enumerate(FILES.items(), 1):
        url = f"{BASE_URL}/{remote_path}"
        label = local_path
        if len(label) > 50:
            label = "..." + label[-47:]

        sys.stdout.write(f"  [{i:3d}/{len(FILES)}] {label}")
        sys.stdout.flush()

        if download_file(url, local_path):
            size = os.path.getsize(local_path)
            print(f"  ({size:,} bytes)")
            success += 1
        else:
            print(f"  [FAILED]")
            failed += 1
            failed_files.append(local_path)

        # Rate limit to avoid GitHub throttling
        if i % 30 == 0:
            time.sleep(1)

    print()
    print(f"  Downloaded: {success}/{len(FILES)} files")
    if failed:
        print(f"  Failed: {failed} files:")
        for f in failed_files:
            print(f"    - {f}")
    print()

    # ── Step 4: Verify key files ───────────────────────────────────────
    print("Step 4/4: Verifying update...")
    errors = []

    # Check version.json
    try:
        with open("version.json", "r", encoding="utf-8") as f:
            vdata = json.load(f)
        if vdata.get("version") == EXPECTED_VERSION:
            print(f"  [OK] version.json = {EXPECTED_VERSION}")
        else:
            print(f"  [WARN] version.json = {vdata.get('version')} (expected {EXPECTED_VERSION})")
            errors.append("version mismatch")
    except Exception as e:
        print(f"  [FAIL] version.json: {e}")
        errors.append("version.json")

    # Check critical v6.2.9 feature: background thread for SP connector
    try:
        with open("routes/review_routes.py", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "connecting" in content and "background" in content.lower():
            print("  [OK] review_routes.py has v6.2.9 async SP scan")
        else:
            print("  [WARN] review_routes.py may not have v6.2.9 changes")
            errors.append("review_routes.py")
    except Exception as e:
        print(f"  [FAIL] review_routes.py: {e}")
        errors.append("review_routes.py")

    # Check auth_service.py exists (v6.2.0)
    if os.path.exists("auth_service.py"):
        print("  [OK] auth_service.py exists (unified auth)")
    else:
        print("  [WARN] auth_service.py missing")
        errors.append("auth_service.py")

    # Check AbortController in app.js (v6.2.9)
    try:
        with open("static/js/app.js", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "AbortController" in content:
            print("  [OK] app.js has AbortController (v6.2.9)")
        else:
            print("  [WARN] app.js may not have v6.2.9 changes")
            errors.append("app.js")
    except Exception as e:
        print(f"  [FAIL] app.js: {e}")
        errors.append("app.js")

    # Check batch-results.js exists (v6.2.0)
    if os.path.exists("static/js/features/batch-results.js"):
        print("  [OK] batch-results.js exists (v6.2.0)")
    else:
        print("  [WARN] batch-results.js missing")
        errors.append("batch-results.js")

    # Check sharepoint_link_validator.py exists (v6.1.11)
    if os.path.exists("sharepoint_link_validator.py"):
        print("  [OK] sharepoint_link_validator.py exists (v6.1.11)")
    else:
        print("  [WARN] sharepoint_link_validator.py missing")
        errors.append("sharepoint_link_validator.py")

    print()

    # ── Step 5: Install new pip packages if needed ─────────────────────
    print("Step 5: Checking optional packages...")

    # Find the correct Python executable
    python_exe = sys.executable
    if os.path.exists("python/python.exe"):
        python_exe = os.path.join(os.getcwd(), "python", "python.exe")
        print(f"  Using embedded Python: {python_exe}")

    def try_pip_install(package, pip_name=None):
        """Try offline-first, then online pip install."""
        pip_name = pip_name or package
        # Try import first
        try:
            __import__(package)
            print(f"  [OK] {pip_name} already installed")
            return True
        except ImportError:
            pass

        # Try offline
        wheels_dirs = []
        for d in ["wheels", "packaging/wheels"]:
            if os.path.isdir(d):
                wheels_dirs.append(d)

        if wheels_dirs:
            find_links = []
            for d in wheels_dirs:
                find_links.extend(["--find-links", d])
            import subprocess
            try:
                subprocess.run(
                    [python_exe, "-m", "pip", "install", "--no-index"] + find_links + ["--no-warn-script-location", pip_name],
                    capture_output=True, timeout=120
                )
                __import__(package)
                print(f"  [OK] {pip_name} installed (offline)")
                return True
            except Exception:
                pass

        # Try online
        import subprocess
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--no-warn-script-location", pip_name],
                capture_output=True, timeout=120
            )
            __import__(package)
            print(f"  [OK] {pip_name} installed (online)")
            return True
        except Exception:
            print(f"  [SKIP] {pip_name} not available (optional)")
            return False

    try_pip_install("msal", "msal>=1.20.0")
    try_pip_install("jwt", "PyJWT>=2.0.0")
    try_pip_install("truststore", "truststore>=0.9.0")

    # Windows-only packages
    if sys.platform == "win32":
        try_pip_install("win32security", "pywin32>=300")

    print()

    # ── Summary ────────────────────────────────────────────────────────
    print("=" * 60)
    if not errors and failed == 0:
        print("  UPDATE SUCCESSFUL!")
    elif errors or failed:
        print("  UPDATE COMPLETED WITH WARNINGS")
    print("=" * 60)
    print()
    print(f"  Version: {EXPECTED_VERSION}")
    print(f"  Files updated: {success}/{len(FILES)}")
    print(f"  Backups in: {BACKUP_DIR}/")
    print()
    print("  What's new in v6.2.9:")
    print("    - SharePoint scan no longer freezes the UI (async background thread)")
    print("    - Cinematic progress dashboard for SharePoint scans")
    print("    - 30-second timeout on SharePoint connection attempts")
    print("    - Unified auth service for all SharePoint/HV modules")
    print("    - Responsive CSS for smaller screens (1366px, 1280px, 1024px, 768px)")
    print("    - Async batch scan with per-file progress tracking")
    print("    - Batch results with multi-dimensional filtering")
    print("    - D3.js graph scaling for large datasets")
    print("    - Update rollback with version-aware manifests")
    print()
    print("  Next steps:")
    print("    1. Restart AEGIS (double-click Start_AEGIS.bat)")
    print("    2. Hard-refresh browser (Ctrl+Shift+R)")
    print("    3. Verify version in Settings > About shows v6.2.9")
    print()

    if sys.platform == "win32":
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
