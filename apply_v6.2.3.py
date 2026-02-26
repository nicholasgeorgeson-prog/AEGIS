#!/usr/bin/env python3
"""
AEGIS v6.2.3 — Comprehensive Update from v5.9.47
==================================================
Downloads ALL changed files from GitHub and applies them directly.
Covers versions v5.9.47 through v6.2.3 (140+ files).

Changes include:
  - Unified Auth Service (auth_service.py) for shared SPO sessions
  - SharePoint Link Validator (parity with HV auth cascade)
  - SharePoint file selection after discovery
  - Headless browser SSO with Edge/Chrome persistent context
  - Update Manager rollback fixes (manifest format + Windows restart)
  - Proposal Compare v2.0 (8 tabs, projects, multi-term, learning)
  - Universal pattern learning system (5 modules)
  - Settings Learning tab with per-module management
  - Cinematic Technology Showcase (Canvas animation engine)
  - Hyperlink Validator enhancements (headless, rate-limiting, SSL)
  - Statement History HTML rendering + PDF.js viewer
  - Fix Assistant reviewer/owner mode toggle
  - Export Suite (5 formats, pre-export filters, PDF report)
  - Batch scan stability (persistent Docling, crash protection)
  - Responsive CSS breakpoints (1366/1280/1024/768px)
  - 160+ bug fixes and optimizations

Usage:
  python apply_v6.2.3.py          (from AEGIS install directory)
  python\\python.exe apply_v6.2.3.py   (using embedded Python)

Author: AEGIS
"""

import os
import sys
import json
import shutil
import ssl
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# =============================================================================
# Configuration
# =============================================================================

VERSION = '6.2.3'
GITHUB_RAW = 'https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main'

# Directories that must exist before file placement
NEW_DIRS = [
    'routes',
    'statement_forge',
    'proposal_compare',
    'hyperlink_validator',
    'portfolio',
    'nlp/spelling',
    'dictionaries',
    'packaging',
    'document_compare',
    'static/js/features',
    'static/js/vendor/pdfjs',
    'static/js/api',
    'static/js/ui',
    'static/css/features',
    'static/audio/demo',
    'static/audio/cinema',
    'templates',
]

# =============================================================================
# File Lists — organized by category
# =============================================================================

# Python core modules
PYTHON_CORE = {
    'app.py': 'app.py',
    'core.py': 'core.py',
    'config_logging.py': 'config_logging.py',
    'scan_history.py': 'scan_history.py',
    'update_manager.py': 'update_manager.py',
    'docling_extractor.py': 'docling_extractor.py',
    'nlp_enhanced.py': 'nlp_enhanced.py',
    'install_nlp.py': 'install_nlp.py',
    'report_generator.py': 'report_generator.py',
    'report_html_generator.py': 'report_html_generator.py',
    'coreference_checker.py': 'coreference_checker.py',
    'acronym_checker.py': 'acronym_checker.py',
    'acronym_enhanced_checkers.py': 'acronym_enhanced_checkers.py',
    'acronym_extractor.py': 'acronym_extractor.py',
    'adjudication_export.py': 'adjudication_export.py',
    'export_module.py': 'export_module.py',
    'markup_engine.py': 'markup_engine.py',
    'review_report.py': 'review_report.py',
    'comprehensive_hyperlink_checker.py': 'comprehensive_hyperlink_checker.py',
    'spell_checker.py': 'spell_checker.py',
    'demo_audio_generator.py': 'demo_audio_generator.py',
    'graph_export_html.py': 'graph_export_html.py',
    'proposal_compare_export.py': 'proposal_compare_export.py',
    'role_dictionary_master.json': 'role_dictionary_master.json',
}

# New modules (v5.9.44+)
PYTHON_NEW = {
    'auth_service.py': 'auth_service.py',
    'sharepoint_connector.py': 'sharepoint_connector.py',
    'sharepoint_link_validator.py': 'sharepoint_link_validator.py',
    'review_learner.py': 'review_learner.py',
    'roles_learner.py': 'roles_learner.py',
    'repair_aegis.py': 'repair_aegis.py',
    'pull_updates.py': 'pull_updates.py',
}

# Route blueprints
PYTHON_ROUTES = {
    'routes/__init__.py': 'routes/__init__.py',
    'routes/_shared.py': 'routes/_shared.py',
    'routes/config_routes.py': 'routes/config_routes.py',
    'routes/core_routes.py': 'routes/core_routes.py',
    'routes/data_routes.py': 'routes/data_routes.py',
    'routes/review_routes.py': 'routes/review_routes.py',
    'routes/roles_routes.py': 'routes/roles_routes.py',
    'routes/sow_routes.py': 'routes/sow_routes.py',
}

# Sub-packages
PYTHON_PACKAGES = {
    'statement_forge/routes.py': 'statement_forge/routes.py',
    'statement_forge/statement_learner.py': 'statement_forge/statement_learner.py',
    'proposal_compare/__init__.py': 'proposal_compare/__init__.py',
    'proposal_compare/analyzer.py': 'proposal_compare/analyzer.py',
    'proposal_compare/parser.py': 'proposal_compare/parser.py',
    'proposal_compare/projects.py': 'proposal_compare/projects.py',
    'proposal_compare/routes.py': 'proposal_compare/routes.py',
    'proposal_compare/structure_analyzer.py': 'proposal_compare/structure_analyzer.py',
    'proposal_compare/pattern_learner.py': 'proposal_compare/pattern_learner.py',
    'hyperlink_validator/export.py': 'hyperlink_validator/export.py',
    'hyperlink_validator/headless_validator.py': 'hyperlink_validator/headless_validator.py',
    'hyperlink_validator/models.py': 'hyperlink_validator/models.py',
    'hyperlink_validator/routes.py': 'hyperlink_validator/routes.py',
    'hyperlink_validator/validator.py': 'hyperlink_validator/validator.py',
    'hyperlink_validator/hv_learner.py': 'hyperlink_validator/hv_learner.py',
    'portfolio/routes.py': 'portfolio/routes.py',
    'nlp/spelling/checker.py': 'nlp/spelling/checker.py',
}

# Templates
HTML_FILES = {
    'templates/index.html': 'templates/index.html',
}

# JavaScript — core
JS_CORE = {
    'static/js/app.js': 'static/js/app.js',
    'static/js/api/client.js': 'static/js/api/client.js',
    'static/js/help-content.js': 'static/js/help-content.js',
    'static/js/help-docs.js': 'static/js/help-docs.js',
    'static/js/update-functions.js': 'static/js/update-functions.js',
    'static/js/roles-tabs-fix.js': 'static/js/roles-tabs-fix.js',
    'static/js/roles-dictionary-fix.js': 'static/js/roles-dictionary-fix.js',
    'static/js/ui/events.js': 'static/js/ui/events.js',
}

# JavaScript — feature modules
JS_FEATURES = {
    'static/js/features/batch-results.js': 'static/js/features/batch-results.js',
    'static/js/features/data-explorer.js': 'static/js/features/data-explorer.js',
    'static/js/features/doc-compare.js': 'static/js/features/doc-compare.js',
    'static/js/features/doc-review-viewer.js': 'static/js/features/doc-review-viewer.js',
    'static/js/features/document-viewer.js': 'static/js/features/document-viewer.js',
    'static/js/features/fix-assistant-state.js': 'static/js/features/fix-assistant-state.js',
    'static/js/features/guide-system.js': 'static/js/features/guide-system.js',
    'static/js/features/hyperlink-validator.js': 'static/js/features/hyperlink-validator.js',
    'static/js/features/hyperlink-validator-state.js': 'static/js/features/hyperlink-validator-state.js',
    'static/js/features/landing-page.js': 'static/js/features/landing-page.js',
    'static/js/features/metrics-analytics.js': 'static/js/features/metrics-analytics.js',
    'static/js/features/pdf-viewer.js': 'static/js/features/pdf-viewer.js',
    'static/js/features/proposal-compare.js': 'static/js/features/proposal-compare.js',
    'static/js/features/role-source-viewer.js': 'static/js/features/role-source-viewer.js',
    'static/js/features/roles.js': 'static/js/features/roles.js',
    'static/js/features/scan-progress-dashboard.js': 'static/js/features/scan-progress-dashboard.js',
    'static/js/features/statement-history.js': 'static/js/features/statement-history.js',
    'static/js/features/statement-source-viewer.js': 'static/js/features/statement-source-viewer.js',
    'static/js/features/technology-showcase.js': 'static/js/features/technology-showcase.js',
}

# JavaScript — vendor libraries
JS_VENDOR = {
    'static/js/vendor/pdfjs/pdf.min.mjs': 'static/js/vendor/pdfjs/pdf.min.mjs',
    'static/js/vendor/pdfjs/pdf.worker.min.mjs': 'static/js/vendor/pdfjs/pdf.worker.min.mjs',
}

# CSS files
CSS_FILES = {
    'static/css/base.css': 'static/css/base.css',
    'static/css/charts.css': 'static/css/charts.css',
    'static/css/features/batch-progress-dashboard.css': 'static/css/features/batch-progress-dashboard.css',
    'static/css/features/batch-results.css': 'static/css/features/batch-results.css',
    'static/css/features/doc-compare.css': 'static/css/features/doc-compare.css',
    'static/css/features/doc-review-viewer.css': 'static/css/features/doc-review-viewer.css',
    'static/css/features/export-suite.css': 'static/css/features/export-suite.css',
    'static/css/features/fix-assistant.css': 'static/css/features/fix-assistant.css',
    'static/css/features/guide-system.css': 'static/css/features/guide-system.css',
    'static/css/features/hyperlink-enhanced.css': 'static/css/features/hyperlink-enhanced.css',
    'static/css/features/hyperlink-validator.css': 'static/css/features/hyperlink-validator.css',
    'static/css/features/landing-page.css': 'static/css/features/landing-page.css',
    'static/css/features/metrics-analytics.css': 'static/css/features/metrics-analytics.css',
    'static/css/features/proposal-compare.css': 'static/css/features/proposal-compare.css',
    'static/css/features/roles-studio.css': 'static/css/features/roles-studio.css',
    'static/css/features/scan-history.css': 'static/css/features/scan-history.css',
    'static/css/features/scan-progress-dashboard.css': 'static/css/features/scan-progress-dashboard.css',
    'static/css/features/settings.css': 'static/css/features/settings.css',
    'static/css/features/sow-generator.css': 'static/css/features/sow-generator.css',
    'static/css/features/statement-forge.css': 'static/css/features/statement-forge.css',
    'static/css/features/statement-history.css': 'static/css/features/statement-history.css',
    'static/css/features/technology-showcase.css': 'static/css/features/technology-showcase.css',
}

# Audio manifests (MP3 files can be regenerated with demo_audio_generator.py)
AUDIO_MANIFESTS = {
    'static/audio/demo/manifest.json': 'static/audio/demo/manifest.json',
    'static/audio/cinema/manifest.json': 'static/audio/cinema/manifest.json',
}

# Config / version files
CONFIG_FILES = {
    'config.json': 'config.json',
    'requirements.txt': 'requirements.txt',
    'version.json': 'version.json',
    'static/version.json': 'static/version.json',
    'dictionaries/defense.txt': 'dictionaries/defense.txt',
}

# Installer / batch scripts (Windows)
INSTALLER_FILES = {
    'Install_AEGIS.bat': 'Install_AEGIS.bat',
    'Install_AEGIS_OneClick.bat': 'Install_AEGIS_OneClick.bat',
    'install_offline.bat': 'install_offline.bat',
    'packaging/Install_AEGIS_OneClick.bat': 'packaging/Install_AEGIS_OneClick.bat',
    'packaging/requirements-windows.txt': 'packaging/requirements-windows.txt',
    'Repair_AEGIS.bat': 'Repair_AEGIS.bat',
    'Start_AEGIS.bat': 'Start_AEGIS.bat',
}

# Combine all file categories
ALL_FILES = {}
for category in [PYTHON_CORE, PYTHON_NEW, PYTHON_ROUTES, PYTHON_PACKAGES,
                 HTML_FILES, JS_CORE, JS_FEATURES, JS_VENDOR,
                 CSS_FILES, AUDIO_MANIFESTS, CONFIG_FILES, INSTALLER_FILES]:
    ALL_FILES.update(category)

# Packages to install (offline-first, online fallback)
PIP_PACKAGES = [
    'msal>=1.20.0',
    'PyJWT>=2.0.0',
    'truststore>=0.9.0',
    'playwright',
]
PIP_PACKAGES_WINDOWS = [
    'pywin32>=300',
    'sspilib>=0.3.0',
    'colorama>=0.4.6',
    'typer>=0.9.0',
]


# =============================================================================
# Helpers
# =============================================================================

def download_file(url, dest_path, timeout=30):
    """Download a file from URL with SSL fallback for corporate networks."""
    headers = {'User-Agent': 'AEGIS-Updater/6.2.3'}
    req = Request(url, headers=headers)

    # Strategy 1: Normal SSL
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest_path) or '.', exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True
    except (URLError, HTTPError, ssl.SSLError):
        pass

    # Strategy 2: SSL bypass (corporate proxy / internal CA)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest_path) or '.', exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'    [FAIL] Download error: {e}')
        return False


def find_python():
    """Find the correct Python executable (embedded or system)."""
    # Check for embedded Python (OneClick installer layout)
    candidates = [
        os.path.join('.', 'python', 'python.exe'),
        os.path.join('.', 'python', 'python3.exe'),
    ]
    for p in candidates:
        if os.path.isfile(p):
            print(f'  Found embedded Python: {p}')
            return os.path.abspath(p)

    # Fall back to system Python
    print(f'  Using system Python: {sys.executable}')
    return sys.executable


def pip_install(python_exe, packages, wheels_dirs=None):
    """Install packages with offline-first, online fallback."""
    if not packages:
        return

    # Build --find-links args
    find_links = []
    if wheels_dirs:
        for wd in wheels_dirs:
            if os.path.isdir(wd):
                find_links.extend(['--find-links', wd])

    for pkg in packages:
        print(f'  Installing {pkg}...', end=' ')

        # Strategy 1: Offline from wheels
        if find_links:
            cmd = [python_exe, '-m', 'pip', 'install',
                   '--no-index'] + find_links + [
                   '--no-warn-script-location', '--quiet', pkg]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print('[OK - offline]')
                continue

        # Strategy 2: Online
        cmd = [python_exe, '-m', 'pip', 'install',
               '--no-warn-script-location', '--quiet', pkg]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print('[OK - online]')
        else:
            print(f'[SKIP] {result.stderr.strip()[:80] if result.stderr else ""}')


def find_wheels_dirs():
    """Find all wheels directories."""
    dirs = []
    for candidate in ['wheels', 'packaging/wheels', '../wheels']:
        if os.path.isdir(candidate):
            dirs.append(os.path.abspath(candidate))
    return dirs


# =============================================================================
# Main
# =============================================================================

def main():
    print('=' * 60)
    print(f'  AEGIS v{VERSION} — Comprehensive Update')
    print(f'  Updating from v5.9.47 to v{VERSION}')
    print(f'  {len(ALL_FILES)} files to download')
    print('=' * 60)
    print()

    # --- Step 0: Verify we're in the AEGIS directory ---
    if not os.path.isfile('app.py'):
        print('[ERROR] app.py not found in current directory.')
        print('        Please run this script from the AEGIS install directory.')
        print(f'        Current directory: {os.getcwd()}')
        sys.exit(1)

    if not os.path.isdir('static'):
        print('[ERROR] static/ directory not found.')
        print('        Please run this script from the AEGIS install directory.')
        sys.exit(1)

    print(f'[OK] Running from: {os.getcwd()}')
    print()

    # --- Step 1: Create backup ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('backups', f'pre_v{VERSION}_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    print(f'[Step 1] Creating backup in: {backup_dir}')

    backed_up = 0
    for src_path in ALL_FILES.values():
        if os.path.isfile(src_path):
            backup_path = os.path.join(backup_dir, src_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            try:
                shutil.copy2(src_path, backup_path)
                backed_up += 1
            except Exception as e:
                print(f'  [WARN] Could not backup {src_path}: {e}')

    print(f'  Backed up {backed_up} existing files')
    print()

    # --- Step 2: Create directories ---
    print('[Step 2] Creating directories...')
    for d in NEW_DIRS:
        os.makedirs(d, exist_ok=True)
        # Ensure __init__.py for Python packages
        if not d.startswith('static') and not d.startswith('templates') and \
           not d.startswith('dictionaries') and not d.startswith('packaging'):
            init_file = os.path.join(d, '__init__.py')
            if not os.path.isfile(init_file):
                with open(init_file, 'w') as f:
                    f.write('')
    print('  Done')
    print()

    # --- Step 3: Download files ---
    print(f'[Step 3] Downloading {len(ALL_FILES)} files from GitHub...')
    print()

    categories = [
        ('Python Core', PYTHON_CORE),
        ('New Modules', PYTHON_NEW),
        ('Route Blueprints', PYTHON_ROUTES),
        ('Sub-packages', PYTHON_PACKAGES),
        ('Templates', HTML_FILES),
        ('JavaScript Core', JS_CORE),
        ('JavaScript Features', JS_FEATURES),
        ('JavaScript Vendor', JS_VENDOR),
        ('CSS', CSS_FILES),
        ('Audio Manifests', AUDIO_MANIFESTS),
        ('Config/Version', CONFIG_FILES),
        ('Installers', INSTALLER_FILES),
    ]

    total_ok = 0
    total_fail = 0
    failed_files = []

    for cat_name, cat_files in categories:
        print(f'  --- {cat_name} ({len(cat_files)} files) ---')
        for github_path, local_path in cat_files.items():
            url = f'{GITHUB_RAW}/{github_path}'
            ok = download_file(url, local_path)
            if ok:
                total_ok += 1
                print(f'    [OK] {local_path}')
            else:
                total_fail += 1
                failed_files.append(local_path)
                print(f'    [FAIL] {local_path}')
        print()

    print(f'  Downloads complete: {total_ok} OK, {total_fail} failed')
    if failed_files:
        print(f'  Failed files:')
        for f in failed_files:
            print(f'    - {f}')
    print()

    # --- Step 4: Install Python packages ---
    print('[Step 4] Installing Python packages...')
    python_exe = find_python()
    wheels_dirs = find_wheels_dirs()

    # Install common packages
    pip_install(python_exe, PIP_PACKAGES, wheels_dirs)

    # Install Windows-only packages
    if sys.platform == 'win32':
        pip_install(python_exe, PIP_PACKAGES_WINDOWS, wheels_dirs)

    print()

    # --- Step 5: Install Playwright browser (for headless validation) ---
    print('[Step 5] Installing Playwright Chromium browser...')
    try:
        result = subprocess.run(
            [python_exe, '-m', 'playwright', 'install', 'chromium'],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            print('  [OK] Playwright Chromium installed')
        else:
            print(f'  [SKIP] Playwright install failed: {result.stderr.strip()[:100]}')
            print('  You can install it manually later:')
            print(f'    {python_exe} -m playwright install chromium')
    except FileNotFoundError:
        print('  [SKIP] Playwright not available (pip install playwright first)')
    except subprocess.TimeoutExpired:
        print('  [SKIP] Playwright install timed out (600s). Try manually:')
        print(f'    {python_exe} -m playwright install chromium')
    except Exception as e:
        print(f'  [SKIP] Playwright error: {e}')
    print()

    # --- Step 6: Verify key imports ---
    print('[Step 6] Verifying key imports...')
    checks = [
        ('flask', 'Flask'),
        ('mammoth', 'mammoth (DOCX → HTML)'),
        ('openpyxl', 'openpyxl (Excel export)'),
        ('reportlab', 'reportlab (PDF reports)'),
    ]
    if sys.platform == 'win32':
        checks.extend([
            ('msal', 'MSAL (OAuth 2.0)'),
            ('requests_negotiate_sspi', 'Windows SSO (Negotiate)'),
        ])

    for module, label in checks:
        try:
            result = subprocess.run(
                [python_exe, '-c', f'import {module}'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                print(f'  [OK] {label}')
            else:
                print(f'  [MISS] {label} — install from wheels or pip')
        except Exception:
            print(f'  [SKIP] {label} — could not verify')
    print()

    # --- Summary ---
    print('=' * 60)
    print(f'  AEGIS v{VERSION} Update Complete!')
    print('=' * 60)
    print()
    print(f'  Files downloaded:  {total_ok}/{len(ALL_FILES)}')
    if total_fail:
        print(f'  Files failed:      {total_fail}')
    print(f'  Backup location:   {backup_dir}')
    print()
    print('  Next steps:')
    print('  1. Restart AEGIS (double-click Start_AEGIS.bat)')
    print('  2. Open http://localhost:5050 in your browser')
    print('  3. Check Settings > About to verify version')
    print()
    if total_fail:
        print('  NOTE: Some files failed to download. These may be')
        print('  optional files or files not yet pushed to GitHub.')
        print('  AEGIS should still work — check the failed list above.')
        print()
    print('  To regenerate demo audio (optional):')
    print(f'    {python_exe} demo_audio_generator.py')
    print()
    print('  To rollback this update:')
    print(f'    Copy files from {backup_dir} back to the AEGIS directory')
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nUpdate cancelled by user.')
        sys.exit(1)
    except Exception as e:
        print(f'\n[FATAL ERROR] {e}')
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Keep window open on Windows
        if sys.platform == 'win32':
            input('\nPress Enter to close...')
