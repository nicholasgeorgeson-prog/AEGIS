#!/usr/bin/env python3
"""
AEGIS v5.9.53 Update Script
============================
Applies all changes from v5.9.42 through v5.9.53:
- v5.9.42: Interactive HTML export, PDF HiDPI viewer, project dashboard
- v5.9.43: Multi-term awareness, openpyxl hyperlink fix, ProposalData fields
- v5.9.44: Headless rewrite, rate limiting, content-type mismatch, truststore
- v5.9.45: Heatmap fixes, Chart.js grouped bars, pre-comparison validation
- v5.9.46: Multi-term comparison (auto-group by contract term)
- v5.9.47: Proposal Structure Analyzer (privacy-safe parser diagnostics)
- v5.9.48: Batch Structure Analysis (multi-file combined report)
- v5.9.49: Local Pattern Learning (Proposal Compare)
- v5.9.50: Universal Learning System (all 5 modules)
- v5.9.51: Learning system demos + audio clips
- v5.9.52: Settings Learning tab (management dashboard)
- v5.9.53: Guided Tour auto-advance, PDF pan/drag, PC re-analysis,
           project financial dashboard, Learning tab fixes

Downloads files from: https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/

Usage:
  1. Place this file in your AEGIS install directory
  2. Run: python apply_v5.9.53.py
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

VERSION = "5.9.53"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# FILES CHANGED FROM v5.9.41 TO v5.9.53
# ============================================================================

# Python — Core backend
PYTHON_CORE = [
    "app.py",
    "core.py",
    "config_logging.py",
    "scan_history.py",
    "update_manager.py",
    "docling_extractor.py",
    "nlp_enhanced.py",
    "coreference_checker.py",
    "acronym_checker.py",
    "acronym_enhanced_checkers.py",
    "acronym_extractor.py",
    "adjudication_export.py",
    "report_generator.py",
    "report_html_generator.py",
    "graph_export_html.py",
    "demo_audio_generator.py",
    "install_nlp.py",
    "nlp/spelling/checker.py",
]

# Python — Routes
PYTHON_ROUTES = [
    "routes/__init__.py",
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/core_routes.py",
    "routes/data_routes.py",
    "routes/review_routes.py",
    "routes/roles_routes.py",
    "routes/sow_routes.py",                     # NEW in v5.9.42
]

# Python — Proposal Compare module
PYTHON_PROPOSAL_COMPARE = [
    "proposal_compare/__init__.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/parser.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py",    # NEW in v5.9.47
    "proposal_compare/pattern_learner.py",       # NEW in v5.9.49
    "proposal_compare_export.py",                # NEW in v5.9.42
]

# Python — Hyperlink Validator module
PYTHON_HV = [
    "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/models.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py",
    "hyperlink_validator/hv_learner.py",         # NEW in v5.9.50
]

# Python — Other modules
PYTHON_OTHER_MODULES = [
    "portfolio/routes.py",
    "statement_forge/routes.py",
    "statement_forge/statement_learner.py",      # NEW in v5.9.50
]

# Python — Learning system + standalone tools
PYTHON_LEARNING_AND_TOOLS = [
    "review_learner.py",                         # NEW in v5.9.50
    "roles_learner.py",                          # NEW in v5.9.50
    "sharepoint_connector.py",                   # NEW in v5.9.42
    "repair_aegis.py",                           # NEW in v5.9.44
    "pull_updates.py",                           # NEW in v5.9.44
    "proposal_structure_tool.py",                # NEW in v5.9.47
]

# JavaScript files
JS_FILES = [
    "static/js/app.js",
    "static/js/help-docs.js",
    "static/js/help-content.js",
    "static/js/update-functions.js",
    "static/js/roles-tabs-fix.js",
    "static/js/roles-dictionary-fix.js",
    "static/js/ui/events.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/landing-page.js",
    "static/js/features/guide-system.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/metrics-analytics.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/statement-history.js",
    "static/js/features/scan-progress-dashboard.js",
    "static/js/features/doc-compare.js",
    "static/js/features/document-viewer.js",
    "static/js/features/data-explorer.js",
    "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js",
    "static/js/features/statement-source-viewer.js",
]

# CSS files
CSS_FILES = [
    "static/css/base.css",
    "static/css/charts.css",
    "static/css/features/proposal-compare.css",
    "static/css/features/landing-page.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/hyperlink-validator.css",
    "static/css/features/guide-system.css",
    "static/css/features/batch-progress-dashboard.css",
    "static/css/features/scan-progress-dashboard.css",
    "static/css/features/roles-studio.css",
    "static/css/features/settings.css",
    "static/css/features/sow-generator.css",
    "static/css/features/statement-forge.css",
    "static/css/features/statement-history.css",
]

# Templates
TEMPLATE_FILES = [
    "templates/index.html",
]

# Config / Version / Data
CONFIG_FILES = [
    "version.json",
    "static/version.json",
    "config.json",
    "requirements.txt",
    "dictionaries/defense.txt",
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
                'User-Agent': f'AEGIS-Updater/{VERSION}'
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


# ============================================================================
# MAIN
# ============================================================================

def main():
    print()
    print("=" * 70)
    print("  \u2554" + "\u2550" * 47 + "\u2557")
    print("  \u2551   AEGIS v5.9.53 Update                       \u2551")
    print("  \u2551   From v5.9.41 \u2192 v5.9.53                     \u2551")
    print("  \u2551   12 Version Rollup                            \u2551")
    print("  \u255a" + "\u2550" * 47 + "\u255d")
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
        print("  \u2713 Connection established\n")
    else:
        print("  \u26a0 Using fallback connection (no SSL verify)\n")

    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v{VERSION}_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)

    # Build complete file list
    all_files = (
        PYTHON_CORE +
        PYTHON_ROUTES +
        PYTHON_PROPOSAL_COMPARE +
        PYTHON_HV +
        PYTHON_OTHER_MODULES +
        PYTHON_LEARNING_AND_TOOLS +
        JS_FILES +
        CSS_FILES +
        TEMPLATE_FILES +
        CONFIG_FILES
    )

    total_files = len(all_files)

    # ---- Phase 1: Backup ----
    print(f"  Phase 1: Backing up existing files ({total_files} total)...")
    backed_up = 0
    for f in all_files:
        if backup_file(f, backup_dir):
            backed_up += 1
    print(f"  \u2713 {backed_up} files backed up to {backup_dir}/\n")

    # ---- Phase 2: Ensure directories exist ----
    needed_dirs = [
        'proposal_compare',
        'hyperlink_validator',
        'statement_forge',
        'portfolio',
        'routes',
        'nlp/spelling',
        'static/js/features',
        'static/js/ui',
        'static/css/features',
        'templates',
        'dictionaries',
    ]
    for d in needed_dirs:
        os.makedirs(d, exist_ok=True)
        # Ensure __init__.py for Python packages
        if d in ('proposal_compare', 'hyperlink_validator', 'statement_forge',
                 'portfolio', 'routes', 'nlp', 'nlp/spelling'):
            init_file = os.path.join(d, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('')

    # ---- Phase 3: Download files ----
    print(f"  Phase 2: Downloading {total_files} files...")
    print()
    download_ok = 0
    download_fail = 0
    failed_files = []

    # Download in category groups for clear output
    groups = [
        ("Python Core", PYTHON_CORE),
        ("Python Routes", PYTHON_ROUTES),
        ("Proposal Compare", PYTHON_PROPOSAL_COMPARE),
        ("Hyperlink Validator", PYTHON_HV),
        ("Other Modules", PYTHON_OTHER_MODULES),
        ("Learning & Tools", PYTHON_LEARNING_AND_TOOLS),
        ("JavaScript", JS_FILES),
        ("CSS", CSS_FILES),
        ("Templates", TEMPLATE_FILES),
        ("Config/Version", CONFIG_FILES),
    ]

    for group_name, group_files in groups:
        print(f"    --- {group_name} ({len(group_files)} files) ---")
        for filepath in group_files:
            url = f"{RAW_BASE}/{filepath}"
            if download_file(url, filepath, ssl_ctx):
                download_ok += 1
                print(f"    \u2713 {filepath}")
            else:
                download_fail += 1
                failed_files.append(filepath)
                print(f"    \u2717 FAILED: {filepath}")
        print()

    print(f"  Downloaded: {download_ok}, Failed: {download_fail}\n")

    # ---- Phase 4: Verify critical files ----
    print("  Phase 3: Verifying critical files...")
    critical = [
        ('version.json', 'Version info'),
        ('static/version.json', 'Client version'),
        ('app.py', 'Flask application'),
        ('core.py', 'AEGIS engine'),
        ('routes/config_routes.py', 'Config routes'),
        ('routes/review_routes.py', 'Review routes'),
        ('proposal_compare/routes.py', 'Proposal Compare routes'),
        ('proposal_compare/parser.py', 'Proposal parser'),
        ('proposal_compare/analyzer.py', 'Proposal analyzer'),
        ('proposal_compare/projects.py', 'Project management'),
        ('hyperlink_validator/validator.py', 'Link validator'),
        ('hyperlink_validator/routes.py', 'HV routes'),
        ('templates/index.html', 'Main template'),
        ('static/js/app.js', 'Main JS'),
        ('static/js/features/proposal-compare.js', 'Proposal Compare JS'),
        ('static/js/features/landing-page.js', 'Landing page JS'),
        ('static/js/features/guide-system.js', 'Guide system JS'),
        ('static/js/features/pdf-viewer.js', 'PDF viewer JS'),
        ('static/js/features/metrics-analytics.js', 'Metrics JS'),
        ('static/js/help-docs.js', 'Help documentation'),
        ('static/css/features/proposal-compare.css', 'Proposal Compare CSS'),
        ('static/css/features/settings.css', 'Settings CSS'),
    ]

    verify_ok = 0
    verify_fail = 0
    for filepath, desc in critical:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            verify_ok += 1
            print(f"    \u2713 {desc}")
        else:
            verify_fail += 1
            print(f"    \u2717 {desc} \u2014 MISSING or EMPTY")

    # Version check
    try:
        with open('version.json', 'r') as f:
            new_ver = json.load(f).get('version', 'unknown')
        if new_ver == VERSION:
            print(f"\n    \u2713 Version verified: {new_ver}")
        else:
            print(f"\n    \u26a0 Version: expected {VERSION}, got {new_ver}")
    except Exception:
        print("\n    \u26a0 Could not read version.json")

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
        print("\n  \u2705 UPDATE SUCCESSFUL!")
    elif verify_fail == 0:
        print("\n  \u26a0 UPDATE MOSTLY COMPLETE \u2014 some non-critical files failed")
    else:
        print("\n  \u274c UPDATE INCOMPLETE \u2014 critical files missing")

    print()
    print("  NEXT STEPS:")
    print("  " + "\u2500" * 45)
    print("  1. Restart AEGIS server:")
    print("     Windows:  python app.py --debug")
    print("     Mac:      python3 app.py --debug")
    print("  2. Open browser to http://localhost:5050")
    print(f"  3. Verify version shows {VERSION} in bottom-left")
    print()
    print(f"  WHAT'S NEW (v5.9.42 \u2192 v5.9.53):")
    print("  " + "\u2500" * 45)
    print()
    print("  v5.9.53 \u2014 Guided Tour + Financial Dashboard:")
    print("  \u2022 Guided Tour auto-advance with voice narration")
    print("  \u2022 Post-demo navigation (Back to Dashboard button)")
    print("  \u2022 Document Review tile no longer auto-opens file picker")
    print("  \u2022 PDF viewer click-to-drag panning + click-to-populate fix")
    print("  \u2022 Proposal Compare re-analysis + add proposal + exclusion toggles")
    print("  \u2022 Project Financial Dashboard (vendor cards, price range, risk flags)")
    print("  \u2022 Landing page project dropdown with Go button")
    print("  \u2022 Learning tab loading state + Clear All button styling fix")
    print("  \u2022 SharePoint CSRF token error fix")
    print()
    print("  v5.9.52 \u2014 Settings Learning Tab:")
    print("  \u2022 Learning management dashboard in Settings")
    print("  \u2022 Per-module View/Export/Clear with JSON viewer")
    print("  \u2022 Global toggle (dual-persisted localStorage + config.json)")
    print("  \u2022 7 new backend endpoints for pattern management")
    print()
    print("  v5.9.50-51 \u2014 Universal Learning System:")
    print("  \u2022 5 learning modules (Review, Forge, Roles, HV, Proposals)")
    print("  \u2022 Pattern files stay 100% local, never uploaded")
    print("  \u2022 Safety thresholds (count >= 2 to activate)")
    print("  \u2022 Demo scenes + MP3 audio for learning features")
    print()
    print("  v5.9.46-49 \u2014 Multi-Term + Pattern Learning:")
    print("  \u2022 Auto-group proposals by contract term")
    print("  \u2022 Term selector bar with All Terms Summary")
    print("  \u2022 Proposal Structure Analyzer (privacy-safe diagnostics)")
    print("  \u2022 Local pattern learning from user corrections")
    print()
    print("  v5.9.42-45 \u2014 Headless + Export + Charts:")
    print("  \u2022 Headless browser rewrite (resource blocking, parallel)")
    print("  \u2022 Per-domain rate limiting for batch validation")
    print("  \u2022 OS truststore integration for corporate SSL")
    print("  \u2022 Interactive HTML export (self-contained reports)")
    print("  \u2022 PDF HiDPI rendering + zoom + magnifier")
    print("  \u2022 Content-type mismatch detection for login redirects")
    print()
    print(f"  Backups: {backup_dir}/")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
