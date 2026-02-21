#!/usr/bin/env python3
"""
AEGIS v5.9.44 Update Script
============================
Applies all changes from v5.9.42 through v5.9.44:
- v5.9.42: Project Dashboard, edit persistence, tag-to-project, HTML export, vendor badges, PDF viewer zoom
- v5.9.43: HV export URL matching fix, contract term preservation, multi-term comparison awareness
- v5.9.44: HV headless browser rewrite, per-domain rate limiting, content-type mismatch detection, OS truststore

Downloads files from: https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/

Usage:
  1. Place this file in your AEGIS install directory
  2. Run: python apply_v5.9.44.py
  3. Restart AEGIS after completion
"""

import os
import sys
import json
import shutil
import urllib.request
import urllib.error
import ssl
import time
from datetime import datetime

VERSION = "5.9.44"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# ALL FILES CHANGED FROM v5.9.42 TO v5.9.44
# ============================================================================

# Python files - project root
PYTHON_ROOT = [
    "app.py",
    "config_logging.py",
    "core.py",
    "demo_audio_generator.py",
    "docling_extractor.py",
    "graph_export_html.py",
    "nlp_enhanced.py",
    "report_generator.py",
    "report_html_generator.py",
    "scan_history.py",
    "update_manager.py",
    "adjudication_export.py",
    "coreference_checker.py",
    "install_nlp.py",
    "acronym_checker.py",
    "acronym_enhanced_checkers.py",
    "acronym_extractor.py",
    # New files
    "sharepoint_connector.py",
    "pull_updates.py",
    "repair_aegis.py",
    "proposal_compare_export.py",
]

# Python files - proposal_compare/
PYTHON_PROPOSAL_COMPARE = [
    "proposal_compare/analyzer.py",
    "proposal_compare/parser.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",
]

# Python files - routes/
PYTHON_ROUTES = [
    "routes/__init__.py",
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/core_routes.py",
    "routes/data_routes.py",
    "routes/review_routes.py",
    "routes/roles_routes.py",
    "routes/sow_routes.py",
]

# Python files - hyperlink_validator/
PYTHON_HV = [
    "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/models.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py",
]

# Python files - other subdirectories
PYTHON_OTHER = [
    "statement_forge/routes.py",
    "nlp/spelling/checker.py",
    "portfolio/routes.py",
]

# JavaScript files
JS_FILES = [
    "static/js/app.js",
    "static/js/help-content.js",
    "static/js/help-docs.js",
    "static/js/roles-dictionary-fix.js",
    "static/js/roles-tabs-fix.js",
    "static/js/ui/events.js",
    "static/js/update-functions.js",
    "static/js/features/data-explorer.js",
    "static/js/features/doc-compare.js",
    "static/js/features/document-viewer.js",
    "static/js/features/guide-system.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/landing-page.js",
    "static/js/features/metrics-analytics.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js",
    "static/js/features/scan-progress-dashboard.js",
    "static/js/features/statement-history.js",
    "static/js/features/statement-source-viewer.js",
]

# CSS files
CSS_FILES = [
    "static/css/base.css",
    "static/css/charts.css",
    "static/css/features/batch-progress-dashboard.css",
    "static/css/features/hyperlink-validator.css",
    "static/css/features/landing-page.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/proposal-compare.css",
    "static/css/features/roles-studio.css",
    "static/css/features/scan-progress-dashboard.css",
    "static/css/features/sow-generator.css",
    "static/css/features/statement-forge.css",
    "static/css/features/statement-history.css",
]

# HTML template
HTML_FILES = [
    "templates/index.html",
]

# Config/data files
CONFIG_FILES = [
    "version.json",
    "static/version.json",
    "config.json",
    "requirements.txt",
    "role_dictionary_master.json",
    "dictionaries/defense.txt",
    ".gitignore",
    "CLAUDE.md",
]

# Installer / batch files
INSTALLER_FILES = [
    "Install_AEGIS_OneClick.bat",
    "Install_AEGIS.bat",
    "install_offline.bat",
    "Repair_AEGIS.bat",
    "packaging/Install_AEGIS_OneClick.bat",
    "packaging/requirements-windows.txt",
]


# ============================================================================
# SSL FALLBACK (for corporate networks)
# ============================================================================

def get_ssl_context():
    """Try multiple SSL strategies for corporate networks."""
    # Strategy 1: Default (certifi)
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(
            urllib.request.Request(f"{RAW_BASE}/version.json",
                                  headers={'User-Agent': 'AEGIS-Updater'}),
            context=ctx, timeout=10
        )
        return ctx
    except Exception:
        pass
    # Strategy 2: Unverified (corporate CA bypass)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        pass
    # Strategy 3: No context
    return None


def download_file(url, dest_path, ssl_ctx=None, retries=3):
    """Download a file from URL to dest_path with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'AEGIS-Updater/5.9.44'
            })
            kwargs = {'timeout': 60}
            if ssl_ctx:
                kwargs['context'] = ssl_ctx
            response = urllib.request.urlopen(req, **kwargs)
            data = response.read()

            # Ensure parent directory exists
            dirpath = os.path.dirname(dest_path)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)

            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False
    return False


def backup_file(filepath, backup_dir):
    """Create backup of a file preserving directory structure."""
    if os.path.exists(filepath):
        dest = os.path.join(backup_dir, filepath)
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        try:
            shutil.copy2(filepath, dest)
            return True
        except Exception:
            return False
    return False


def progress_bar(current, total, width=40):
    """Simple progress bar."""
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = '█' * filled + '░' * (width - filled)
    return f"  [{bar}] {current}/{total} ({pct*100:.0f}%)"


# ============================================================================
# MAIN
# ============================================================================

def main():
    print()
    print("=" * 70)
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║   AEGIS v5.9.44 Update                       ║")
    print("  ║   From v5.9.42 → v5.9.44                     ║")
    print("  ║   HV headless rewrite + rate limiting         ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print("=" * 70)
    print()

    # Verify we're in the right directory
    if not os.path.exists('app.py') or not os.path.exists('static'):
        print("  [ERROR] This script must be run from the AEGIS install directory.")
        print(f"          Current directory: {os.getcwd()}")
        print("          Expected to find app.py and static/ folder.")
        sys.exit(1)

    # Check current version
    try:
        with open('version.json', 'r') as f:
            current = json.load(f)
        current_version = current.get('version', 'unknown')
    except Exception:
        current_version = 'unknown'

    print(f"  Current version: {current_version}")
    print(f"  Target version:  {VERSION}")
    print()

    # Get SSL context
    print("  Testing connection to GitHub...")
    ssl_ctx = get_ssl_context()
    if ssl_ctx:
        print("  ✓ Connection established\n")
    else:
        print("  ⚠ Using fallback connection (no SSL verify)\n")

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v{VERSION}_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)

    # Build complete file list
    all_files = (
        PYTHON_ROOT +
        PYTHON_PROPOSAL_COMPARE +
        PYTHON_ROUTES +
        PYTHON_HV +
        PYTHON_OTHER +
        JS_FILES +
        CSS_FILES +
        HTML_FILES +
        CONFIG_FILES +
        INSTALLER_FILES
    )

    # ---- Phase 1: Backup ----
    print("  Phase 1: Backing up existing files...")
    backed_up = 0
    for f in all_files:
        if backup_file(f, backup_dir):
            backed_up += 1
    print(f"  ✓ {backed_up} files backed up to {backup_dir}/\n")

    # ---- Phase 2: Ensure directories exist ----
    needed_dirs = [
        'proposal_compare', 'routes', 'hyperlink_validator',
        'statement_forge', 'nlp', 'nlp/spelling', 'portfolio',
        'static/js/features', 'static/js/ui',
        'static/css/features',
        'templates', 'dictionaries', 'packaging', 'backups',
    ]
    for d in needed_dirs:
        os.makedirs(d, exist_ok=True)
        # Create __init__.py for Python packages
        if d in ['proposal_compare', 'routes', 'hyperlink_validator',
                  'statement_forge', 'nlp', 'nlp/spelling', 'portfolio']:
            init_file = os.path.join(d, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('')

    # ---- Phase 3: Download files ----
    total_files = len(all_files)
    print(f"  Phase 2: Downloading {total_files} files...")
    download_ok = 0
    download_fail = 0
    failed_files = []

    for i, filepath in enumerate(all_files, 1):
        url = f"{RAW_BASE}/{filepath}"
        if download_file(url, filepath, ssl_ctx):
            download_ok += 1
        else:
            download_fail += 1
            failed_files.append(filepath)
            print(f"    ✗ FAILED: {filepath}")

        if i % 20 == 0 or i == total_files:
            print(progress_bar(i, total_files))

    print(f"\n  Downloaded: {download_ok}, Failed: {download_fail}\n")

    # ---- Phase 4: Verify critical files ----
    print("  Phase 3: Verifying critical files...")
    critical = [
        ('app.py', 'Flask entry point'),
        ('version.json', 'Version info'),
        ('static/version.json', 'Client version'),
        ('templates/index.html', 'Main template'),
        ('core.py', 'AEGIS Engine'),
        ('scan_history.py', 'Database operations'),
        ('hyperlink_validator/validator.py', 'HV Validator (headless rewrite)'),
        ('hyperlink_validator/routes.py', 'HV Routes'),
        ('hyperlink_validator/export.py', 'HV Export'),
        ('hyperlink_validator/models.py', 'HV Models'),
        ('proposal_compare/analyzer.py', 'Proposal Analyzer'),
        ('proposal_compare/parser.py', 'Proposal Parser'),
        ('proposal_compare/routes.py', 'Proposal Routes'),
        ('proposal_compare/projects.py', 'Proposal Projects'),
        ('proposal_compare_export.py', 'Proposal Export (XLSX+HTML)'),
        ('sharepoint_connector.py', 'SharePoint Connector'),
        ('repair_aegis.py', 'Repair Tool'),
        ('pull_updates.py', 'Update Puller'),
        ('routes/sow_routes.py', 'SOW Routes (new)'),
        ('routes/config_routes.py', 'Config Routes'),
        ('routes/review_routes.py', 'Review Routes'),
        ('static/js/app.js', 'Main App JS'),
        ('static/js/features/proposal-compare.js', 'Proposal Compare JS'),
        ('static/js/features/hyperlink-validator.js', 'HV Frontend'),
        ('static/js/features/guide-system.js', 'Guide System'),
        ('static/js/features/metrics-analytics.js', 'Metrics & Analytics'),
        ('static/js/features/pdf-viewer.js', 'PDF Viewer'),
        ('static/js/help-docs.js', 'Help Documentation'),
        ('static/js/update-functions.js', 'Update Functions'),
        ('static/css/features/proposal-compare.css', 'Proposal Compare CSS'),
        ('static/css/features/hyperlink-validator.css', 'HV CSS'),
        ('requirements.txt', 'Python requirements'),
    ]

    verify_ok = 0
    verify_fail = 0
    for filepath, desc in critical:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            verify_ok += 1
            print(f"    ✓ {desc}")
        else:
            verify_fail += 1
            print(f"    ✗ {desc} — MISSING or EMPTY")

    # Version check
    try:
        with open('version.json', 'r') as f:
            new_ver = json.load(f).get('version', 'unknown')
        if new_ver == VERSION:
            print(f"\n    ✓ Version verified: {new_ver}")
        else:
            print(f"\n    ⚠ Version: expected {VERSION}, got {new_ver}")
    except Exception:
        print("\n    ⚠ Could not read version.json")

    # ---- Summary ----
    print()
    print("=" * 70)
    print("  UPDATE SUMMARY")
    print("-" * 70)
    print(f"  Files downloaded:  {download_ok:>4} OK     {download_fail:>3} failed")
    print(f"  Verification:      {verify_ok:>4} passed  {verify_fail:>3} failed")
    print(f"  Backups saved to:  {backup_dir}/")
    print("-" * 70)

    if failed_files:
        print("\n  Failed files:")
        for ff in failed_files:
            print(f"    - {ff}")

    if download_fail == 0 and verify_fail == 0:
        print("\n  ✅ UPDATE SUCCESSFUL!")
    elif verify_fail == 0:
        print("\n  ⚠ UPDATE MOSTLY COMPLETE — some non-critical files failed")
    else:
        print("\n  ❌ UPDATE INCOMPLETE — critical files missing")

    print()
    print("  NEXT STEPS:")
    print("  ─────────────────────────────────────────────")
    print("  1. Restart AEGIS server:")
    print("     Windows:  python app.py --debug")
    print("     Mac:      python3 app.py --debug")
    print("  2. Open browser to http://localhost:5050")
    print("  3. Verify version shows 5.9.44 in bottom-left")
    print()
    print("  WHAT'S NEW (v5.9.42 → v5.9.44):")
    print("  ─────────────────────────────────────────────")
    print("  v5.9.42:")
    print("  • Project Dashboard — Browse projects, drill into detail")
    print("  • Edit Persistence — Review edits auto-save to database")
    print("  • Tag to Project — Assign proposals to any project")
    print("  • Interactive HTML Export — Standalone reports with charts")
    print("  • PDF Viewer Zoom & Magnifier — Better document viewing")
    print("  • Vendor Color Badges — Visual proposal identification")
    print()
    print("  v5.9.43:")
    print("  • HV Export URL Matching — Fixed multicolor Excel highlighting")
    print("  • Contract Term Preservation — Terms survive re-comparison")
    print("  • Multi-Term Comparison — Disambiguation for same-vendor bids")
    print()
    print("  v5.9.44:")
    print("  • HV Headless Browser Rewrite — More reliable link validation")
    print("  • Per-Domain Rate Limiting — Avoids overwhelming servers")
    print("  • Content-Type Mismatch Detection — Catches soft 404s")
    print("  • OS Truststore Integration — Trusts corporate CA certs")
    print("  • SharePoint Connector — One-click connect & scan")
    print("  • Repair Tool — Diagnose and fix installation issues")
    print("  • SOW Routes — Statement of Work generation endpoints")
    print()
    print(f"  Backups: {backup_dir}/")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
