#!/usr/bin/env python3
"""
AEGIS v6.2.1 Apply Script — Full Update from v6.1.11+
======================================================
Downloads and applies ALL changes from v6.1.11 through v6.2.1 directly from GitHub.

Changes in v6.2.0:
  - NEW: Unified Auth Service (auth_service.py) — singleton pattern for shared SSO sessions
  - NEW: Batch Results module with multi-dimensional filtering (batch-results.js/css)
  - NEW: Document Review Viewer IIFE module (doc-review-viewer.js/css)
  - NEW: Async batch scan with progress polling and per-file phase tracking
  - NEW: Responsive CSS breakpoints (1366/1280/1024/768px) across 13 CSS files
  - NEW: UNC path support for folder scans on Windows
  - ENH: SharePoint file selection after discovery (pick which files to scan)
  - ENH: SP Link Validation parity with full auth cascade
  - ENH: Progress callback wired in batch scans for per-file phase tracking
  - ENH: Cinematic progress minimize/restore badge during batch operations
  - ENH: All 5 learning modules with Settings UI management dashboard

Changes in v6.2.1:
  - FIX: Relationship Graph Edge Bundling — circle radius scales with data size
  - FIX: Relationship Graph Force-Directed — parameters scale with node count
  - FIX: Modal max-width changed to min(95vw, 1100px)
  - FIX: html_preview default value corrected from 0 to '' in review API

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
from datetime import datetime
from pathlib import Path

VERSION = "6.2.1"
GITHUB_RAW = "https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main"

# ============================================================
# ALL files that changed from v6.1.11 through v6.2.1
# Organized by category for clarity
# ============================================================
FILES = {
    # === Core Python Backend ===
    "app.py": "app.py",
    "core.py": "core.py",
    "config.json": "config.json",
    "config_logging.py": "config_logging.py",
    "scan_history.py": "scan_history.py",
    "update_manager.py": "update_manager.py",
    "requirements.txt": "requirements.txt",
    "spell_checker.py": "spell_checker.py",
    "nlp_enhanced.py": "nlp_enhanced.py",
    "install_nlp.py": "install_nlp.py",
    "report_generator.py": "report_generator.py",
    "report_html_generator.py": "report_html_generator.py",
    "coreference_checker.py": "coreference_checker.py",
    "acronym_checker.py": "acronym_checker.py",
    "acronym_enhanced_checkers.py": "acronym_enhanced_checkers.py",
    "acronym_extractor.py": "acronym_extractor.py",
    "adjudication_export.py": "adjudication_export.py",
    "comprehensive_hyperlink_checker.py": "comprehensive_hyperlink_checker.py",
    "docling_extractor.py": "docling_extractor.py",
    "graph_export_html.py": "graph_export_html.py",
    "demo_audio_generator.py": "demo_audio_generator.py",
    "role_dictionary_master.json": "role_dictionary_master.json",

    # === Auth & SharePoint (v6.2.0 new + updated) ===
    "auth_service.py": "auth_service.py",
    "sharepoint_connector.py": "sharepoint_connector.py",
    "sharepoint_link_validator.py": "sharepoint_link_validator.py",

    # === Learning Modules (v5.9.50+) ===
    "review_learner.py": "review_learner.py",
    "roles_learner.py": "roles_learner.py",
    "hyperlink_validator/hv_learner.py": "hyperlink_validator/hv_learner.py",
    "statement_forge/statement_learner.py": "statement_forge/statement_learner.py",
    "proposal_compare/pattern_learner.py": "proposal_compare/pattern_learner.py",

    # === Routes (all blueprints) ===
    "routes/__init__.py": "routes/__init__.py",
    "routes/_shared.py": "routes/_shared.py",
    "routes/config_routes.py": "routes/config_routes.py",
    "routes/core_routes.py": "routes/core_routes.py",
    "routes/data_routes.py": "routes/data_routes.py",
    "routes/review_routes.py": "routes/review_routes.py",
    "routes/roles_routes.py": "routes/roles_routes.py",
    "routes/sow_routes.py": "routes/sow_routes.py",

    # === Proposal Compare ===
    "proposal_compare/analyzer.py": "proposal_compare/analyzer.py",
    "proposal_compare/parser.py": "proposal_compare/parser.py",
    "proposal_compare/projects.py": "proposal_compare/projects.py",
    "proposal_compare/routes.py": "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py": "proposal_compare/structure_analyzer.py",
    "proposal_compare_export.py": "proposal_compare_export.py",

    # === Hyperlink Validator ===
    "hyperlink_validator/export.py": "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py": "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/models.py": "hyperlink_validator/models.py",
    "hyperlink_validator/routes.py": "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py": "hyperlink_validator/validator.py",

    # === Statement Forge ===
    "statement_forge/routes.py": "statement_forge/routes.py",

    # === Portfolio ===
    "portfolio/routes.py": "portfolio/routes.py",

    # === NLP ===
    "nlp/spelling/checker.py": "nlp/spelling/checker.py",

    # === Dictionaries ===
    "dictionaries/defense.txt": "dictionaries/defense.txt",

    # === Templates ===
    "templates/index.html": "templates/index.html",

    # === Version & Docs ===
    "version.json": "version.json",
    "static/version.json": "static/version.json",

    # === JavaScript — Core Modules ===
    "static/js/app.js": "static/js/app.js",
    "static/js/api/client.js": "static/js/api/client.js",
    "static/js/ui/events.js": "static/js/ui/events.js",
    "static/js/help-content.js": "static/js/help-content.js",
    "static/js/help-docs.js": "static/js/help-docs.js",
    "static/js/update-functions.js": "static/js/update-functions.js",
    "static/js/roles-tabs-fix.js": "static/js/roles-tabs-fix.js",
    "static/js/roles-dictionary-fix.js": "static/js/roles-dictionary-fix.js",

    # === JavaScript — Feature Modules ===
    "static/js/features/batch-results.js": "static/js/features/batch-results.js",
    "static/js/features/data-explorer.js": "static/js/features/data-explorer.js",
    "static/js/features/doc-compare.js": "static/js/features/doc-compare.js",
    "static/js/features/doc-review-viewer.js": "static/js/features/doc-review-viewer.js",
    "static/js/features/document-viewer.js": "static/js/features/document-viewer.js",
    "static/js/features/fix-assistant-state.js": "static/js/features/fix-assistant-state.js",
    "static/js/features/guide-system.js": "static/js/features/guide-system.js",
    "static/js/features/hyperlink-validator.js": "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js": "static/js/features/hyperlink-validator-state.js",
    "static/js/features/landing-page.js": "static/js/features/landing-page.js",
    "static/js/features/metrics-analytics.js": "static/js/features/metrics-analytics.js",
    "static/js/features/pdf-viewer.js": "static/js/features/pdf-viewer.js",
    "static/js/features/proposal-compare.js": "static/js/features/proposal-compare.js",
    "static/js/features/role-source-viewer.js": "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js": "static/js/features/roles.js",
    "static/js/features/scan-progress-dashboard.js": "static/js/features/scan-progress-dashboard.js",
    "static/js/features/statement-history.js": "static/js/features/statement-history.js",
    "static/js/features/statement-source-viewer.js": "static/js/features/statement-source-viewer.js",
    "static/js/features/technology-showcase.js": "static/js/features/technology-showcase.js",

    # === CSS — Core ===
    "static/css/base.css": "static/css/base.css",
    "static/css/charts.css": "static/css/charts.css",
    "static/css/layout.css": "static/css/layout.css",
    "static/css/modals.css": "static/css/modals.css",

    # === CSS — Features ===
    "static/css/features/batch-progress-dashboard.css": "static/css/features/batch-progress-dashboard.css",
    "static/css/features/batch-results.css": "static/css/features/batch-results.css",
    "static/css/features/doc-compare.css": "static/css/features/doc-compare.css",
    "static/css/features/doc-review-viewer.css": "static/css/features/doc-review-viewer.css",
    "static/css/features/export-suite.css": "static/css/features/export-suite.css",
    "static/css/features/fix-assistant.css": "static/css/features/fix-assistant.css",
    "static/css/features/guide-system.css": "static/css/features/guide-system.css",
    "static/css/features/hyperlink-enhanced.css": "static/css/features/hyperlink-enhanced.css",
    "static/css/features/hyperlink-validator.css": "static/css/features/hyperlink-validator.css",
    "static/css/features/landing-page.css": "static/css/features/landing-page.css",
    "static/css/features/metrics-analytics.css": "static/css/features/metrics-analytics.css",
    "static/css/features/proposal-compare.css": "static/css/features/proposal-compare.css",
    "static/css/features/roles-studio.css": "static/css/features/roles-studio.css",
    "static/css/features/scan-history.css": "static/css/features/scan-history.css",
    "static/css/features/scan-progress-dashboard.css": "static/css/features/scan-progress-dashboard.css",
    "static/css/features/settings.css": "static/css/features/settings.css",
    "static/css/features/sow-generator.css": "static/css/features/sow-generator.css",
    "static/css/features/statement-forge.css": "static/css/features/statement-forge.css",
    "static/css/features/statement-history.css": "static/css/features/statement-history.css",
    "static/css/features/technology-showcase.css": "static/css/features/technology-showcase.css",

    # === Installers ===
    "Install_AEGIS.bat": "Install_AEGIS.bat",
    "Install_AEGIS_OneClick.bat": "Install_AEGIS_OneClick.bat",

    # === Packaging ===
    "packaging/Install_AEGIS_OneClick.bat": "packaging/Install_AEGIS_OneClick.bat",
    "packaging/prepare_offline_data.py": "packaging/prepare_offline_data.py",
    "packaging/requirements-windows.txt": "packaging/requirements-windows.txt",

    # === Config/Misc ===
    ".gitignore": ".gitignore",
}

# Directories that must exist for new files
REQUIRED_DIRS = [
    "routes",
    "proposal_compare",
    "hyperlink_validator",
    "statement_forge",
    "portfolio",
    "nlp/spelling",
    "dictionaries",
    "packaging",
    "static/js/features",
    "static/js/api",
    "static/js/ui",
    "static/css/features",
    "templates",
    "backups",
]


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
        # Preserve directory structure in backup
        rel_dir = os.path.dirname(filepath)
        if rel_dir:
            os.makedirs(os.path.join(backup_dir, rel_dir), exist_ok=True)
        backup_path = os.path.join(backup_dir, filepath)
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


def ensure_init_files():
    """Ensure __init__.py exists in package directories."""
    pkg_dirs = [
        "routes",
        "proposal_compare",
        "hyperlink_validator",
        "statement_forge",
        "portfolio",
        "nlp",
        "nlp/spelling",
        "nlp/languagetool",
        "nlp/readability",
        "nlp/semantics",
        "nlp/spacy",
        "nlp/style",
        "nlp/verbs",
    ]
    for pkg in pkg_dirs:
        init_file = os.path.join(pkg, "__init__.py")
        if os.path.isdir(pkg) and not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("")
            print(f"  Created {init_file}")


def main():
    print(f"""
+============================================================+
|           AEGIS v{VERSION} Full Update Applicator               |
|                                                              |
|  Complete update from v6.1.11+ to v6.2.1                     |
|  {len(FILES)} files to download                                      |
|                                                              |
|  v6.2.0: Auth service, batch results, responsive CSS,        |
|          doc review viewer, async batch scan, learners        |
|  v6.2.1: Graph scaling, modal fixes, html_preview fix         |
+============================================================+
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

    # Step 2: Create required directories
    print("\n[Step 2] Ensuring directory structure...")
    for dir_path in REQUIRED_DIRS:
        os.makedirs(dir_path, exist_ok=True)
    print("  [OK] All directories verified")

    # Step 3: Create SSL context
    print("\n[Step 3] Setting up secure connection...")
    ssl_ctx = get_ssl_context()
    print("  [OK] SSL context ready")

    # Step 4: Download files
    print(f"\n[Step 4] Downloading {len(FILES)} files from GitHub...")
    print("  This may take a few minutes...\n")
    success_count = 0
    fail_count = 0
    new_count = 0

    for remote_path, local_path in FILES.items():
        url = f"{GITHUB_RAW}/{remote_path}"

        is_new = not os.path.exists(local_path)
        label = "NEW" if is_new else "UPD"

        print(f"  [{label}] {local_path}...", end=" ", flush=True)

        # Backup existing file
        backup = backup_file(local_path)

        if download_file(url, local_path, ssl_ctx):
            print("[OK]")
            success_count += 1
            if is_new:
                new_count += 1
        else:
            fail_count += 1
            # Restore backup if download failed
            if backup and os.path.exists(backup):
                shutil.copy2(backup, local_path)
                print(f"  [RESTORED] Original file restored from backup")

    # Step 5: Ensure __init__.py files exist
    print("\n[Step 5] Checking package init files...")
    ensure_init_files()
    print("  [OK] Package structure verified")

    # Step 6: Summary
    print(f"""
+============================================================+
|                    Update Summary                            |
+============================================================+
|  Files updated:   {success_count - new_count:>3} / {len(FILES) - new_count:<3}                                |
|  New files added: {new_count:>3}                                       |
|  Files failed:    {fail_count:>3}                                       |
|  Target version:  {VERSION:<10}                                  |
+============================================================+
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

Key changes from v6.1.11 to v{VERSION}:
  v6.2.0:
    * Unified Auth Service — singleton SSO session management
    * Batch Results module with multi-dimensional filtering
    * Document Review Viewer module (DOCX/PDF/XLSX rendering)
    * Async batch scan with per-file progress tracking
    * Responsive CSS across 13 feature CSS files
    * SharePoint file selection after discovery
    * SP Link Validation parity (auth cascade)
    * UNC path support for Windows folder scans
    * Settings Learning tab — manage all 5 learning modules

  v6.2.1:
    * Relationship Graph circles scale with data size
    * Force-Directed graph parameters scale with node count
    * Modal max-width: min(95vw, 1100px)
    * html_preview API default value fix
    """)


if __name__ == "__main__":
    main()
