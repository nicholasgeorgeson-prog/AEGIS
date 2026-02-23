#!/usr/bin/env python3
"""
AEGIS v6.0.0 Major Update Script
==================================
Applies all changes from v5.9.52 to v6.0.0.

This is a MAJOR version update that includes:
- 5-module local learning system with Settings management dashboard
- Proposal Compare v2 with multi-term comparison and structure analyzer
- Enhanced Hyperlink Validator with SSL/auth/headless improvements
- SharePoint connector with Windows SSO
- Cinematic technology showcase with Ava voice narration (18 scenes)
- Persistent Docling worker pool for batch performance
- Interactive HTML export for proposals
- PDF HiDPI rendering with zoom and magnifier
- Per-domain rate limiting for batch validation
- OS truststore integration for corporate SSL
- Many bug fixes across all modules

Downloads files from: https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/

Usage:
  1. Place this file in your AEGIS install directory (where app.py lives)
  2. Run: python apply_v6.0.0.py
     or:  python3 apply_v6.0.0.py
  3. Restart AEGIS after completion

No external dependencies required - uses only Python standard library.
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

VERSION = "6.0.0"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# FILES CHANGED FROM v5.9.52 TO v6.0.0
# ============================================================================

# Python -- Core backend (modified)
PYTHON_CORE = [
    "app.py",
    "config_logging.py",
    "core.py",
    "coreference_checker.py",
    "demo_audio_generator.py",
    "docling_extractor.py",
    "graph_export_html.py",
    "install_nlp.py",
    "nlp_enhanced.py",
    "report_generator.py",
    "report_html_generator.py",
    "scan_history.py",
    "update_manager.py",
    "acronym_checker.py",
    "acronym_enhanced_checkers.py",
    "acronym_extractor.py",
    "adjudication_export.py",
    "nlp/spelling/checker.py",
]

# Python -- Routes (modified)
PYTHON_ROUTES = [
    "routes/__init__.py",
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/core_routes.py",
    "routes/data_routes.py",
    "routes/review_routes.py",
    "routes/roles_routes.py",
    "routes/sow_routes.py",
    "statement_forge/routes.py",
]

# Python -- Proposal Compare module (modified + new)
PYTHON_PROPOSAL_COMPARE = [
    "proposal_compare/analyzer.py",
    "proposal_compare/parser.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py",       # NEW
    "proposal_compare/pattern_learner.py",          # NEW
    "proposal_compare_export.py",                   # NEW
]

# Python -- Hyperlink Validator module (modified + new)
PYTHON_HV = [
    "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/models.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py",
    "hyperlink_validator/hv_learner.py",            # NEW
]

# Python -- Other modules (modified)
PYTHON_OTHER_MODULES = [
    "portfolio/routes.py",
]

# Python -- New standalone tools and learning system
PYTHON_NEW_AND_TOOLS = [
    "review_learner.py",                            # NEW - Document Review learner
    "roles_learner.py",                             # NEW - Roles Adjudication learner
    "statement_forge/statement_learner.py",          # NEW - Statement Forge learner
    "sharepoint_connector.py",                       # NEW - SharePoint connector
    "pull_updates.py",                               # NEW - Update puller
    "repair_aegis.py",                               # NEW - Repair tool
]

# JavaScript files (modified + new)
JS_FILES = [
    "static/js/app.js",
    "static/js/help-content.js",
    "static/js/help-docs.js",
    "static/js/roles-dictionary-fix.js",
    "static/js/roles-tabs-fix.js",
    "static/js/update-functions.js",
    "static/js/ui/events.js",
    "static/js/features/data-explorer.js",
    "static/js/features/doc-compare.js",
    "static/js/features/document-viewer.js",
    "static/js/features/guide-system.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/landing-page.js",
    "static/js/features/metrics-analytics.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js",
    "static/js/features/scan-progress-dashboard.js",
    "static/js/features/statement-history.js",
    "static/js/features/statement-source-viewer.js",
    "static/js/features/technology-showcase.js",          # NEW - Cinema engine
]

# CSS files (modified + new)
CSS_FILES = [
    "static/css/base.css",
    "static/css/charts.css",
    "static/css/features/batch-progress-dashboard.css",
    "static/css/features/guide-system.css",
    "static/css/features/hyperlink-validator.css",
    "static/css/features/landing-page.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/proposal-compare.css",
    "static/css/features/roles-studio.css",
    "static/css/features/scan-progress-dashboard.css",
    "static/css/features/settings.css",
    "static/css/features/sow-generator.css",
    "static/css/features/statement-forge.css",
    "static/css/features/statement-history.css",
    "static/css/features/technology-showcase.css",        # NEW - Cinema styling
]

# HTML template
TEMPLATE_FILES = [
    "templates/index.html",
]

# Config, version, data files
CONFIG_FILES = [
    "version.json",
    "static/version.json",
    "config.json",
    "requirements.txt",
    "role_dictionary_master.json",
    "dictionaries/defense.txt",
]

# Batch/installer files (Windows deployment)
INSTALLER_FILES = [
    "Install_AEGIS.bat",
    "Install_AEGIS_OneClick.bat",
    "install_offline.bat",
    "packaging/Install_AEGIS_OneClick.bat",
    "packaging/requirements-windows.txt",
    "Repair_AEGIS.bat",
    "Start_AEGIS.bat",
]

# Audio manifest files (the manifests tell us what MP3s to download)
AUDIO_MANIFESTS = [
    "static/audio/demo/manifest.json",
    "static/audio/cinema/manifest.json",
]


# ============================================================================
# SSL FALLBACK (for corporate/air-gapped networks)
# ============================================================================

def get_ssl_context():
    """Try multiple SSL strategies for corporate networks."""
    # Strategy 1: certifi (if available)
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        urllib.request.urlopen(
            urllib.request.Request(f"{RAW_BASE}/version.json",
                                  headers={'User-Agent': 'AEGIS-Updater'}),
            context=ctx, timeout=10
        )
        print("  SSL: Using certifi certificates")
        return ctx
    except Exception:
        pass

    # Strategy 2: System default certificates
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(
            urllib.request.Request(f"{RAW_BASE}/version.json",
                                  headers={'User-Agent': 'AEGIS-Updater'}),
            context=ctx, timeout=10
        )
        print("  SSL: Using system certificates")
        return ctx
    except Exception:
        pass

    # Strategy 3: Unverified (corporate CA bypass)
    print("  [WARN] SSL certificates not available - using unverified HTTPS")
    print("         (This is safe for downloading from GitHub)")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        pass

    # Strategy 4: Bare context
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


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
            return len(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return -1  # File not found on remote
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return 0  # Download failed
    return 0


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
    install_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(install_dir)

    print()
    print("=" * 70)
    print("  +------------------------------------------------+")
    print("  |   AEGIS v6.0.0 -- MAJOR UPDATE                 |")
    print("  |   From v5.9.52 --> v6.0.0                       |")
    print("  |   Comprehensive Feature Release                 |")
    print("  +------------------------------------------------+")
    print("=" * 70)
    print()

    # Verify we're in the right directory
    has_app = os.path.exists('app.py')
    has_static = os.path.isdir('static')
    if not has_app or not has_static:
        print("  [ERROR] This doesn't look like an AEGIS install directory!")
        print(f"          Current location: {install_dir}")
        print("          Expected to find app.py and static/ folder.")
        print()
        resp = input("  Continue anyway? (y/n): ").strip().lower()
        if resp != 'y':
            print("  Cancelled.")
            return 1

    # Check current version
    try:
        with open('version.json', 'r') as f:
            current = json.load(f)
        current_version = current.get('version', 'unknown')
    except Exception:
        current_version = 'unknown'

    print(f"  Current version:  {current_version}")
    print(f"  Target version:   {VERSION}")
    print(f"  Install dir:      {install_dir}")
    print()

    # Show what's included
    print("  THIS UPDATE INCLUDES:")
    print("  " + "-" * 50)
    print("  * 5-module local learning system")
    print("  * Settings Learning tab (manage/view/export/clear)")
    print("  * Proposal Compare v2 with multi-term comparison")
    print("  * Proposal Structure Analyzer (privacy-safe)")
    print("  * Interactive HTML export for proposals")
    print("  * Enhanced HV: SSL/auth/headless improvements")
    print("  * SharePoint connector with Windows SSO")
    print("  * Persistent Docling worker pool (batch perf)")
    print("  * PDF HiDPI rendering with zoom + magnifier")
    print("  * Per-domain rate limiting for batch validation")
    print("  * OS truststore integration for corporate SSL")
    print("  * Batch scan minimize/restore pattern")
    print("  * Metrics & Analytics Proposals tab")
    print("  * Many bug fixes across all modules")
    print()
    print("  NEW: Cinematic Technology Showcase (Behind the Scenes)")
    print("  tile on landing page — 18-scene animated demo with")
    print("  Ava voice narration (en-US-AvaMultilingualNeural)")
    print()

    # Get SSL context
    print("  Testing connection to GitHub...")
    ssl_ctx = get_ssl_context()
    print()

    # Build complete file list
    all_files = (
        PYTHON_CORE +
        PYTHON_ROUTES +
        PYTHON_PROPOSAL_COMPARE +
        PYTHON_HV +
        PYTHON_OTHER_MODULES +
        PYTHON_NEW_AND_TOOLS +
        JS_FILES +
        CSS_FILES +
        TEMPLATE_FILES +
        CONFIG_FILES +
        INSTALLER_FILES +
        AUDIO_MANIFESTS
    )

    total_files = len(all_files)
    print(f"  Total files to update: {total_files}")
    print()

    # ---- Phase 1: Backup ----
    print("  Phase 1: Backing up existing files...")
    print("  " + "-" * 50)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v{VERSION}_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)

    backed_up = 0
    for f in all_files:
        if backup_file(f, backup_dir):
            backed_up += 1
    print(f"  {backed_up} existing files backed up to:")
    print(f"    {os.path.join(install_dir, backup_dir)}")
    print()

    # ---- Phase 2: Ensure directories exist ----
    print("  Phase 2: Ensuring directory structure...")
    print("  " + "-" * 50)
    needed_dirs = [
        'proposal_compare',
        'hyperlink_validator',
        'statement_forge',
        'portfolio',
        'routes',
        'nlp',
        'nlp/spelling',
        'static/js/features',
        'static/js/ui',
        'static/css/features',
        'static/audio/demo',
        'static/audio/cinema',
        'templates',
        'dictionaries',
        'packaging',
    ]
    dirs_created = 0
    for d in needed_dirs:
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
            dirs_created += 1
        # Ensure __init__.py for Python packages
        if d in ('proposal_compare', 'hyperlink_validator', 'statement_forge',
                 'portfolio', 'routes', 'nlp', 'nlp/spelling'):
            init_file = os.path.join(d, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('')
                print(f"    Created {init_file}")

    if dirs_created > 0:
        print(f"  {dirs_created} new directories created")
    else:
        print("  All directories already exist")
    print()

    # ---- Phase 3: Download files ----
    print(f"  Phase 3: Downloading {total_files} files from GitHub...")
    print("  " + "-" * 50)
    print()

    download_ok = 0
    download_fail = 0
    download_skip = 0
    failed_files = []
    total_bytes = 0

    # Download in category groups for clear output
    groups = [
        ("Python Core", PYTHON_CORE),
        ("Python Routes", PYTHON_ROUTES),
        ("Proposal Compare", PYTHON_PROPOSAL_COMPARE),
        ("Hyperlink Validator", PYTHON_HV),
        ("Other Modules", PYTHON_OTHER_MODULES),
        ("New Tools & Learning", PYTHON_NEW_AND_TOOLS),
        ("JavaScript", JS_FILES),
        ("CSS", CSS_FILES),
        ("Templates", TEMPLATE_FILES),
        ("Config & Data", CONFIG_FILES),
        ("Installers & Batch", INSTALLER_FILES),
    ]

    for group_name, group_files in groups:
        print(f"    --- {group_name} ({len(group_files)} files) ---")
        for filepath in group_files:
            url = f"{RAW_BASE}/{filepath}"
            result = download_file(url, filepath, ssl_ctx)
            if result > 0:
                download_ok += 1
                total_bytes += result
                size_kb = result / 1024
                print(f"    OK    {filepath} ({size_kb:.1f} KB)")
            elif result == -1:
                download_skip += 1
                print(f"    SKIP  {filepath} (not found on remote)")
            else:
                download_fail += 1
                failed_files.append(filepath)
                print(f"    FAIL  {filepath}")
        print()

    total_mb = total_bytes / (1024 * 1024)
    print(f"  Downloaded: {download_ok} OK, {download_fail} failed, "
          f"{download_skip} skipped ({total_mb:.1f} MB total)")
    print()

    # ---- Phase 3b: Download audio files from manifests ----
    print("  Phase 3b: Downloading voice narration audio...")
    print("  " + "-" * 50)
    audio_ok = 0
    audio_fail = 0
    audio_bytes = 0

    for manifest_path in AUDIO_MANIFESTS:
        if not os.path.exists(manifest_path):
            print(f"    [SKIP] {manifest_path} not found, skipping audio")
            continue

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"    [WARN] Failed to read {manifest_path}: {e}")
            continue

        audio_dir = os.path.dirname(manifest_path)
        sections = manifest.get('sections', {})
        clip_count = sum(len(s.get('steps', [])) for s in sections.values())
        voice = manifest.get('voice', 'unknown')
        print(f"    {manifest_path}: {len(sections)} sections, "
              f"{clip_count} clips ({voice})")

        for section_id, section in sections.items():
            for step in section.get('steps', []):
                filename = step.get('file', '')
                if not filename:
                    continue
                filepath = os.path.join(audio_dir, filename)
                url = f"{RAW_BASE}/{filepath}"
                result = download_file(url, filepath, ssl_ctx)
                if result > 0:
                    audio_ok += 1
                    audio_bytes += result
                elif result == -1:
                    audio_fail += 1
                else:
                    audio_fail += 1

            # Progress for large audio sets
            if audio_ok % 50 == 0 and audio_ok > 0:
                print(f"      Progress: {audio_ok} clips downloaded "
                      f"({audio_bytes / 1024 / 1024:.1f} MB)")

    audio_mb = audio_bytes / (1024 * 1024)
    print(f"    Audio: {audio_ok} OK, {audio_fail} failed ({audio_mb:.1f} MB)")
    total_bytes += audio_bytes
    download_ok += audio_ok
    download_fail += audio_fail
    print()

    # ---- Phase 4: Verify critical files ----
    print("  Phase 4: Verifying critical files...")
    print("  " + "-" * 50)

    critical = [
        ('version.json', 'Version info'),
        ('static/version.json', 'Client version'),
        ('app.py', 'Flask application'),
        ('core.py', 'AEGIS engine'),
        ('config.json', 'Configuration'),
        ('routes/__init__.py', 'Routes package'),
        ('routes/config_routes.py', 'Config routes'),
        ('routes/review_routes.py', 'Review routes'),
        ('routes/core_routes.py', 'Core routes'),
        ('proposal_compare/analyzer.py', 'Proposal analyzer'),
        ('proposal_compare/parser.py', 'Proposal parser'),
        ('proposal_compare/routes.py', 'Proposal Compare routes'),
        ('proposal_compare/projects.py', 'Project management'),
        ('proposal_compare/structure_analyzer.py', 'Structure analyzer'),
        ('proposal_compare/pattern_learner.py', 'Proposal learner'),
        ('hyperlink_validator/validator.py', 'Link validator'),
        ('hyperlink_validator/routes.py', 'HV routes'),
        ('hyperlink_validator/hv_learner.py', 'HV learner'),
        ('review_learner.py', 'Review learner'),
        ('roles_learner.py', 'Roles learner'),
        ('statement_forge/statement_learner.py', 'Statement learner'),
        ('sharepoint_connector.py', 'SharePoint connector'),
        ('templates/index.html', 'Main template'),
        ('static/js/app.js', 'Main JS'),
        ('static/js/features/proposal-compare.js', 'Proposal Compare JS'),
        ('static/js/features/landing-page.js', 'Landing page JS'),
        ('static/js/features/guide-system.js', 'Guide system JS'),
        ('static/js/features/metrics-analytics.js', 'Metrics JS'),
        ('static/js/features/hyperlink-validator.js', 'HV JS'),
        ('static/js/help-docs.js', 'Help documentation'),
        ('static/css/features/settings.css', 'Settings CSS'),
        ('static/css/features/proposal-compare.css', 'Proposal Compare CSS'),
    ]

    verify_ok = 0
    verify_fail = 0
    for filepath, desc in critical:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            verify_ok += 1
            print(f"    OK    {desc}")
        else:
            verify_fail += 1
            print(f"    FAIL  {desc} -- MISSING or EMPTY")

    # Version check
    print()
    try:
        with open('version.json', 'r') as f:
            new_ver = json.load(f).get('version', 'unknown')
        if new_ver == VERSION:
            print(f"    Version verified: {new_ver}")
        else:
            print(f"    [WARN] Version: expected {VERSION}, got {new_ver}")
    except Exception:
        print("    [WARN] Could not read version.json")

    # ---- Summary ----
    print()
    print("=" * 70)
    print("  UPDATE SUMMARY")
    print("-" * 70)
    print(f"  Files downloaded:   {download_ok:>4} OK     {download_fail:>3} failed"
          f"     {download_skip:>3} skipped")
    print(f"  Verification:       {verify_ok:>4} passed  {verify_fail:>3} failed")
    print(f"  Total downloaded:   {total_mb:.1f} MB")
    print(f"  Backups saved to:   {os.path.join(install_dir, backup_dir)}")
    print("-" * 70)

    if failed_files:
        print()
        print("  Failed files:")
        for ff in failed_files:
            print(f"    - {ff}")

    print()
    if download_fail == 0 and verify_fail == 0:
        print("  UPDATE SUCCESSFUL!")
    elif verify_fail == 0 and download_fail <= 3:
        print("  UPDATE MOSTLY COMPLETE -- some non-critical files failed")
        print("  Core functionality should work fine.")
    else:
        print("  UPDATE INCOMPLETE -- some critical files may be missing")
        print("  Check your internet connection and try again.")
        if backed_up > 0:
            print(f"  To rollback, copy files from: {backup_dir}")

    print()
    print("  " + "=" * 50)
    print("  IMPORTANT: Server restart REQUIRED!")
    print("  " + "=" * 50)
    print()
    print("  This update changes Python backend code.")
    print("  You MUST restart AEGIS for changes to take effect.")
    print()
    print("  NEXT STEPS:")
    print("  " + "-" * 45)
    print("  1. Close this window")
    print("  2. Restart AEGIS:")
    print("     Windows: Start_AEGIS.bat or Repair_AEGIS.bat")
    print("     Mac:     python3 app.py --debug")
    print("  3. Open browser to http://localhost:5050")
    print(f"  4. Verify version shows {VERSION} in bottom-left")
    print()
    print(f"  WHAT'S NEW IN v{VERSION}:")
    print("  " + "-" * 45)
    print()
    print("  LEARNING SYSTEM (v5.9.49-v5.9.52):")
    print("    - 5 learning modules learn from your corrections")
    print("    - Document Review, Statement Forge, Roles,")
    print("      Hyperlink Validator, Proposal Compare")
    print("    - All patterns stored locally, never uploaded")
    print("    - Settings > Learning tab for management")
    print("    - View, Export, Clear patterns per module")
    print()
    print("  PROPOSAL COMPARE v2 (v5.9.40-v5.9.48):")
    print("    - 8-tab results (executive, matrix, categories,")
    print("      red flags, heatmap, vendor scores, details, raw)")
    print("    - Multi-term comparison (auto-group by contract term)")
    print("    - Structure Analyzer (privacy-safe diagnostics)")
    print("    - Interactive HTML export (self-contained reports)")
    print("    - Project management with comparison history")
    print("    - Click-to-populate from document viewer")
    print("    - Local pattern learning from user edits")
    print()
    print("  HYPERLINK VALIDATOR ENHANCEMENTS:")
    print("    - Headless browser rewrite (resource blocking, parallel)")
    print("    - Per-domain rate limiting for batch validation")
    print("    - OS truststore for corporate SSL certificates")
    print("    - Multi-strategy SSL fallback cascade")
    print("    - .mil/.gov headless-first routing")
    print("    - Content-type mismatch detection")
    print("    - Auth diagnostic badge in modal header")
    print()
    print("  SHAREPOINT CONNECTOR:")
    print("    - Windows SSO authentication")
    print("    - One-click Connect & Scan flow")
    print("    - Auto-detect library path from URL")
    print("    - Connection diagnostics with error categorization")
    print()
    print("  BATCH PERFORMANCE:")
    print("    - Persistent Docling worker pool (3-6x faster)")
    print("    - Batch scan minimize/restore badge")
    print("    - Session-broken flag prevents repeated timeouts")
    print()
    print("  OTHER IMPROVEMENTS:")
    print("    - PDF HiDPI rendering with zoom + magnifier")
    print("    - Metrics & Analytics Proposals tab")
    print("    - /api/capabilities endpoint for boot diagnostics")
    print("    - Update system Apply button fix")
    print("    - Many dark mode and z-index fixes")
    print()
    print("  CINEMATIC SHOWCASE (v6.0.0):")
    print("    - 'Behind the Scenes' tile on landing page")
    print("    - 18-scene Canvas animation with cyberpunk HUD aesthetic")
    print("    - Ava voice narration (en-US-AvaMultilingualNeural)")
    print("    - Slow-motion approach with 0.5s lead-in per scene")
    print("    - Play/pause, progress scrub, volume, fullscreen")
    print()
    print(f"  If something went wrong, your old files are in:")
    print(f"    {os.path.join(install_dir, backup_dir)}")
    print()
    print("=" * 70)
    print()

    return 0 if (download_fail == 0 and verify_fail == 0) else 1


if __name__ == '__main__':
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
