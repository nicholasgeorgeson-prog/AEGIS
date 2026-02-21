#!/usr/bin/env python3
"""
AEGIS v5.9.42 Update Script — From v5.9.40 to v5.9.42
========================================================
Downloads ALL changed files from GitHub and places them directly
into the AEGIS install directory. Includes voice narration MP3s
and live demo assets.

Changes in v5.9.41:
  - Proposal Compare v2.1: Review phase, document viewer, line item editor
  - Comparison history with auto-save and reload
  - PDF extraction overhaul with 5-strategy company name detection
  - Contract term detection and multi-term vendor disambiguation
  - Indirect rate analysis (fringe, overhead, G&A, fee/profit)
  - Auto-calculation of missing financial fields
  - Click-to-populate from document viewer
  - HV auth diagnostic endpoint and status badge
  - Headless-first routing for .mil/.gov domains
  - SharePoint corporate domain auto-detect and SSL bypass

Changes in v5.9.42:
  - Project Dashboard: browse projects, drill into detail, edit proposals
  - Edit persistence: review edits auto-save to database
  - Tag to project: assign proposals to projects from anywhere
  - Interactive HTML export: standalone report with charts
  - License category, vendor color badges, PDF viewer zoom/magnifier
  - Quality indicator badges, comparison preview card
  - Enhanced XLSX export with 8 sheets
  - Live demo scenes with simulated data injection
  - HV blueprint import fix (except Exception)
  - fresh_install.py comprehensive installer

Usage:
  1. Place this file in your AEGIS install directory
  2. Run: python apply_v5.9.42.py
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

VERSION = "5.9.42"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# ALL FILES CHANGED FROM v5.9.40 TO v5.9.42
# ============================================================================

# Python files - project root
PYTHON_ROOT = [
    "app.py",
    "config_logging.py",
    "core.py",
    "demo_audio_generator.py",
    "docling_extractor.py",
    "fresh_install.py",
    "graph_export_html.py",
    "nlp_enhanced.py",
    "proposal_compare_export.py",
    "pull_updates.py",
    "repair_aegis.py",
    "report_generator.py",
    "report_html_generator.py",
    "scan_history.py",
    "sharepoint_connector.py",
    "update_manager.py",
    "adjudication_export.py",
    "coreference_checker.py",
    "install_nlp.py",
    "acronym_checker.py",
    "acronym_enhanced_checkers.py",
    "acronym_extractor.py",
]

# Python files - proposal_compare/
PYTHON_PROPOSAL_COMPARE = [
    "proposal_compare/__init__.py",
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
    "static/js/features/demo-simulator.js",
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
    "static/css/features/guide-system.css",
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
    "requirements.txt",
    "dictionaries/defense.txt",
]

# PDF.js vendor files (needed for Proposal Compare document viewer)
VENDOR_FILES = [
    "static/js/vendor/pdfjs/pdf.min.mjs",
    "static/js/vendor/pdfjs/pdf.worker.min.mjs",
]

# Installer files
INSTALLER_FILES = [
    "Install_AEGIS_OneClick.bat",
    "Install_AEGIS.bat",
    "packaging/Install_AEGIS_OneClick.bat",
    "packaging/requirements-windows.txt",
]

# Audio manifest
AUDIO_MANIFEST = "static/audio/demo/manifest.json"


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
                'User-Agent': 'AEGIS-Updater/5.9.42'
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
    print("  ║   AEGIS v5.9.42 Update                       ║")
    print("  ║   From v5.9.40 → v5.9.42                     ║")
    print("  ║   Includes voice narration & live demo files  ║")
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

    # Build complete code file list
    all_code_files = (
        PYTHON_ROOT +
        PYTHON_PROPOSAL_COMPARE +
        PYTHON_ROUTES +
        PYTHON_HV +
        PYTHON_OTHER +
        JS_FILES +
        CSS_FILES +
        HTML_FILES +
        CONFIG_FILES +
        VENDOR_FILES +
        INSTALLER_FILES
    )

    # ---- Phase 1: Backup ----
    print("  Phase 1: Backing up existing files...")
    backed_up = 0
    for f in all_code_files:
        if backup_file(f, backup_dir):
            backed_up += 1
    print(f"  ✓ {backed_up} files backed up to {backup_dir}/\n")

    # ---- Phase 2: Ensure directories exist ----
    needed_dirs = [
        'proposal_compare', 'routes', 'hyperlink_validator',
        'statement_forge', 'nlp', 'nlp/spelling', 'portfolio',
        'static/js/features', 'static/js/ui', 'static/js/vendor/pdfjs',
        'static/css/features', 'static/audio/demo',
        'templates', 'dictionaries', 'packaging'
    ]
    for d in needed_dirs:
        os.makedirs(d, exist_ok=True)
        init_file = os.path.join(d, '__init__.py')
        if d in ['proposal_compare', 'routes', 'hyperlink_validator',
                  'statement_forge', 'nlp', 'nlp/spelling', 'portfolio']:
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('')

    # ---- Phase 3: Download code files ----
    total_code = len(all_code_files)
    print(f"  Phase 2: Downloading {total_code} code files...")
    code_ok = 0
    code_fail = 0

    for i, filepath in enumerate(all_code_files, 1):
        url = f"{RAW_BASE}/{filepath}"
        if download_file(url, filepath, ssl_ctx):
            code_ok += 1
        else:
            code_fail += 1
            print(f"    ✗ FAILED: {filepath}")

        if i % 20 == 0 or i == total_code:
            print(progress_bar(i, total_code))

    print(f"\n  Code: {code_ok} downloaded, {code_fail} failed\n")

    # ---- Phase 4: Download audio files ----
    print("  Phase 3: Downloading voice narration files...")
    audio_ok = 0
    audio_fail = 0
    audio_total = 0

    # Download manifest first
    manifest_url = f"{RAW_BASE}/{AUDIO_MANIFEST}"
    if download_file(manifest_url, AUDIO_MANIFEST, ssl_ctx):
        print("    ✓ Downloaded manifest.json")

        # Parse manifest to get ALL MP3 filenames
        try:
            with open(AUDIO_MANIFEST, 'r') as f:
                manifest = json.load(f)

            mp3_files = set()

            # Overview demo audio
            for section_id, section_data in manifest.get('sections', {}).items():
                for step in section_data.get('steps', []):
                    if 'file' in step:
                        mp3_files.add(step['file'])

            # Sub-demo audio
            for demo_id, demo_data in manifest.get('sub_demos', {}).items():
                for step in demo_data.get('steps', []):
                    if 'file' in step:
                        mp3_files.add(step['file'])

            audio_total = len(mp3_files)
            print(f"    Found {audio_total} audio files in manifest")

            for i, mp3_name in enumerate(sorted(mp3_files), 1):
                mp3_url = f"{RAW_BASE}/static/audio/demo/{mp3_name}"
                mp3_path = f"static/audio/demo/{mp3_name}"

                if download_file(mp3_url, mp3_path, ssl_ctx, retries=2):
                    audio_ok += 1
                else:
                    audio_fail += 1

                if i % 100 == 0 or i == audio_total:
                    print(progress_bar(i, audio_total))

        except Exception as e:
            print(f"    ⚠ Manifest parse error: {e}")
    else:
        print("    ⚠ Could not download audio manifest")
        print("    Voice narration will use Web Speech API fallback")

    print(f"\n  Audio: {audio_ok} downloaded, {audio_fail} failed\n")

    # ---- Phase 5: Verify ----
    print("  Phase 4: Verifying critical files...")
    critical = [
        ('app.py', 'Flask entry point'),
        ('version.json', 'Version info'),
        ('static/version.json', 'Client version'),
        ('templates/index.html', 'Main template'),
        ('static/js/features/proposal-compare.js', 'Proposal Compare JS'),
        ('static/css/features/proposal-compare.css', 'Proposal Compare CSS'),
        ('static/js/features/guide-system.js', 'Guide System'),
        ('static/js/features/metrics-analytics.js', 'Metrics & Analytics'),
        ('static/js/features/pdf-viewer.js', 'PDF Viewer'),
        ('static/js/vendor/pdfjs/pdf.min.mjs', 'PDF.js Library'),
        ('hyperlink_validator/routes.py', 'HV Routes (exception fix)'),
        ('proposal_compare/routes.py', 'PC Routes'),
        ('proposal_compare/projects.py', 'PC Projects'),
        ('proposal_compare_export.py', 'PC Export (XLSX+HTML)'),
        ('static/js/help-docs.js', 'Help Documentation'),
        ('static/js/update-functions.js', 'Update Functions'),
        ('fresh_install.py', 'Fresh Installer'),
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
    total_ok = code_ok + audio_ok
    total_fail = code_fail + audio_fail
    print(f"  Code files:        {code_ok:>4} downloaded   {code_fail:>3} failed")
    print(f"  Audio files:       {audio_ok:>4} downloaded   {audio_fail:>3} failed")
    print(f"  Total:             {total_ok:>4} downloaded   {total_fail:>3} failed")
    print(f"  Verification:      {verify_ok:>4} passed       {verify_fail:>3} failed")
    print("-" * 70)

    if code_fail == 0 and verify_fail == 0:
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
    print("  3. Verify version shows 5.9.42 in bottom-left")
    print()
    print("  NEW FEATURES IN v5.9.41 + v5.9.42:")
    print("  ─────────────────────────────────────────────")
    print("  • Project Dashboard — Click 'Projects' in Proposal Compare")
    print("  • Edit Persistence — Edits auto-save across sessions")
    print("  • Tag to Project — Assign proposals to any project")
    print("  • Interactive HTML Export — Standalone reports with charts")
    print("  • PDF Zoom & Magnifier — Better document viewing")
    print("  • Review Phase — Split-pane doc viewer + metadata editor")
    print("  • Comparison History — Browse & reload past analyses")
    print("  • Live Demo Scenes — Watch animated feature walkthroughs")
    print("  • 535+ Voice Narration Files — Neural TTS for all demos")
    print("  • HV Windows Fix — Corporate network auth works")
    print("  • .mil/.gov Headless-First — Faster government link validation")
    print()
    print(f"  Backups: {backup_dir}/")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
