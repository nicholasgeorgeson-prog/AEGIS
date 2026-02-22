#!/usr/bin/env python3
"""
AEGIS v5.9.48 Update Script
============================
Applies all changes from v5.9.45 through v5.9.48:
- v5.9.45: Proposal Compare bug fixes (heatmap, charts, validation, docling)
- v5.9.46: Multi-term comparison (auto-group by contract term)
- v5.9.47: Proposal Structure Analyzer (privacy-safe parser diagnostics)
- v5.9.48: Batch Structure Analysis (multi-file combined report)

Downloads files from: https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/

Usage:
  1. Place this file in your AEGIS install directory
  2. Run: python apply_v5.9.48.py
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

VERSION = "5.9.48"
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# ============================================================================
# FILES CHANGED FROM v5.9.45 TO v5.9.48
# ============================================================================

# Python files - proposal_compare/
PYTHON_PROPOSAL_COMPARE = [
    "proposal_compare/__init__.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/parser.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py",   # NEW in v5.9.47, updated v5.9.48
]

# JavaScript files
JS_FILES = [
    "static/js/features/proposal-compare.js",
    "static/js/help-docs.js",
]

# CSS files
CSS_FILES = [
    "static/css/features/proposal-compare.css",
]

# Config/data files
CONFIG_FILES = [
    "version.json",
    "static/version.json",
    "CLAUDE.md",
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
    print("  \u2551   AEGIS v5.9.48 Update                       \u2551")
    print("  \u2551   From v5.9.44 \u2192 v5.9.48                     \u2551")
    print("  \u2551   Batch Structure Analysis                    \u2551")
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
        PYTHON_PROPOSAL_COMPARE +
        JS_FILES +
        CSS_FILES +
        CONFIG_FILES
    )

    # ---- Phase 1: Backup ----
    print("  Phase 1: Backing up existing files...")
    backed_up = 0
    for f in all_files:
        if backup_file(f, backup_dir):
            backed_up += 1
    print(f"  \u2713 {backed_up} files backed up to {backup_dir}/\n")

    # ---- Phase 2: Ensure directories exist ----
    needed_dirs = [
        'proposal_compare',
        'static/js/features',
        'static/css/features',
    ]
    for d in needed_dirs:
        os.makedirs(d, exist_ok=True)
        if d == 'proposal_compare':
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
            print(f"    \u2713 {filepath}")
        else:
            download_fail += 1
            failed_files.append(filepath)
            print(f"    \u2717 FAILED: {filepath}")

    print(f"\n  Downloaded: {download_ok}, Failed: {download_fail}\n")

    # ---- Phase 4: Verify critical files ----
    print("  Phase 3: Verifying critical files...")
    critical = [
        ('version.json', 'Version info'),
        ('static/version.json', 'Client version'),
        ('proposal_compare/routes.py', 'Proposal Routes'),
        ('proposal_compare/parser.py', 'Proposal Parser'),
        ('proposal_compare/analyzer.py', 'Proposal Analyzer'),
        ('proposal_compare/structure_analyzer.py', 'Structure Analyzer'),
        ('static/js/features/proposal-compare.js', 'Proposal Compare JS'),
        ('static/js/help-docs.js', 'Help Documentation'),
        ('static/css/features/proposal-compare.css', 'Proposal Compare CSS'),
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
    print(f"  WHAT'S NEW (v5.9.45 \u2192 v5.9.48):")
    print("  " + "\u2500" * 45)
    print("  v5.9.45:")
    print("  \u2022 Heatmap fixes \u2014 single-vendor cells show 'only vendor' label")
    print("  \u2022 Chart.js grouped bar chart for category comparison")
    print("  \u2022 Pre-comparison validation (min 2 proposals, amounts)")
    print("  \u2022 Docling artifacts_path auto-detection")
    print()
    print("  v5.9.46:")
    print("  \u2022 Multi-term comparison \u2014 auto-group by contract term")
    print("  \u2022 Term selector bar \u2014 gold pills above 8-tab results")
    print("  \u2022 All Terms Summary \u2014 cross-term vendor cost table")
    print("  \u2022 Smart Compare button \u2014 adapts label for multi-term")
    print()
    print("  v5.9.47:")
    print("  \u2022 Proposal Structure Analyzer \u2014 privacy-safe parser diagnostics")
    print("  \u2022 Analyze Structure button in upload phase")
    print("  \u2022 Downloads redacted JSON (no $, no names, no descriptions)")
    print("  \u2022 Reports table shapes, column patterns, category distribution")
    print()
    print("  v5.9.48:")
    print("  \u2022 Batch Structure Analysis \u2014 analyze ALL selected files at once")
    print("  \u2022 Single combined JSON with per-file analysis + cross-file summary")
    print("  \u2022 Button shows file count: 'Analyze Structure (3 files)'")
    print("  \u2022 Cross-file summary: merged categories, common issues, quality ranking")
    print()
    print(f"  Backups: {backup_dir}/")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
