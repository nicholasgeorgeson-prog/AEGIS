#!/usr/bin/env python3
"""
AEGIS Fresh Install Script v5.9.42
===================================
Downloads ALL application files from GitHub and places them into the AEGIS
install directory. This is a COMPLETE overwrite of all code files.

PRESERVES:
  - scan_history.db (your data)
  - config.json (your settings)
  - wheels/ directory (pip packages)
  - Any .db files
  - Any files in temp/, backups/, updates/, logs/
  - Audio files in static/audio/

OVERWRITES:
  - All .py files (backend code)
  - All .js files (frontend code)
  - All .css files (stylesheets)
  - templates/index.html
  - version.json
  - requirements.txt
  - .bat files (installers)
  - dictionaries/

Usage:
  python fresh_install.py              # Normal install
  python fresh_install.py --dry-run    # Show what would be downloaded
  python fresh_install.py --no-backup  # Skip backup step
"""

import os
import sys
import ssl
import json
import shutil
import hashlib
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
VERSION = "5.9.42"

# ─── All files to download (relative to repo root) ──────────────────────────
FILES = [
    # ── Core Application ──────────────────────────────────────────────────
    "__main__.py",
    "app.py",
    "config_logging.py",
    "database.py",
    "core.py",
    "scan_history.py",
    "job_manager.py",
    "update_manager.py",

    # ── Utilities & Helpers ───────────────────────────────────────────────
    "context_utils.py",
    "export_module.py",
    "markup_engine.py",
    "api_extensions.py",
    "nlp_utils.py",
    "diagnostic_export.py",
    "sow_generator.py",
    "sharepoint_connector.py",
    "install_nlp.py",
    "install_nlp_offline.py",

    # ── Report & Export Generators ────────────────────────────────────────
    "report_generator.py",
    "report_html_generator.py",
    "review_report.py",
    "adjudication_export.py",
    "adjudication_report.py",
    "hierarchy_export.py",
    "role_template_export.py",
    "graph_export_html.py",
    "sipoc_parser.py",
    "proposal_compare_export.py",

    # ── Document Extraction ───────────────────────────────────────────────
    "docling_extractor.py",
    "pdf_extractor.py",
    "pdf_extractor_v2.py",
    "pdf_extractor_enhanced.py",
    "ocr_extractor.py",
    "table_processor.py",
    "enhanced_table_extractor.py",

    # ── Base Checker Framework ────────────────────────────────────────────
    "base_checker.py",

    # ── Quality Checkers: Grammar & Language ──────────────────────────────
    "grammar_checker.py",
    "enhanced_grammar_checker.py",
    "punctuation_checker.py",
    "sentence_checker.py",
    "word_language_checker.py",
    "terminology_checker.py",
    "terminology_consistency_checker.py",

    # ── Quality Checkers: Style & Clarity ─────────────────────────────────
    "clarity_checkers.py",
    "style_consistency_checkers.py",
    "readability_enhanced.py",
    "enhanced_passive_checker.py",
    "passivepy_checker.py",

    # ── Quality Checkers: Document & Compliance ───────────────────────────
    "document_checker.py",
    "document_quality_checkers.py",
    "document_comparison_checker.py",
    "image_figure_checker.py",
    "requirements_checker.py",
    "requirement_quality_checkers.py",
    "compliance_checkers.py",
    "incose_checker.py",
    "ste100_checker.py",

    # ── Quality Checkers: Advanced ────────────────────────────────────────
    "extended_checkers.py",
    "advanced_analysis_checkers.py",
    "prose_quality_checkers.py",
    "procedural_writing_checkers.py",

    # ── Link & Reference ──────────────────────────────────────────────────
    "hyperlink_checker.py",
    "comprehensive_hyperlink_checker.py",
    "hyperlink_health.py",
    "cross_reference_validator.py",

    # ── Acronym ───────────────────────────────────────────────────────────
    "acronym_checker.py",
    "acronym_enhanced_checkers.py",
    "acronym_extractor.py",
    "acronym_database.py",

    # ── AI & ML ───────────────────────────────────────────────────────────
    "fix_assistant_api.py",
    "adaptive_learner.py",
    "decision_learner.py",

    # ── Role Analysis ─────────────────────────────────────────────────────
    "role_analyzer.py",
    "role_extractor_v3.py",
    "role_integration.py",
    "role_consolidation.py",
    "role_consolidation_engine.py",
    "role_management_studio_v3.py",
    "role_comparison.py",

    # ── Requirements ──────────────────────────────────────────────────────
    "requirements_analyzer.py",

    # ── NLP Integration ───────────────────────────────────────────────────
    "nlp_enhanced.py",
    "nlp_enhancer.py",
    "nlp_integration.py",

    # ── Specialized Checkers ──────────────────────────────────────────────
    "coreference_checker.py",
    "negation_checker.py",
    "structure_analyzer.py",
    "prose_linter.py",
    "fragment_checker.py",
    "technical_dictionary.py",

    # ── Legacy/Analysis ───────────────────────────────────────────────────
    "auto_fixer.py",
    "comment_inserter.py",
    "semantic_analyzer.py",
    "similarity_checker.py",
    "subjectivity_checker.py",
    "summarization_checker.py",
    "srl_checker.py",
    "spell_checker.py",
    "style_presets.py",
    "text_metrics_checker.py",
    "text_statistics.py",
    "textacy_checkers.py",
    "vocabulary_checker.py",
    "yake_checker.py",

    # ── Update & Repair Scripts ───────────────────────────────────────────
    "pull_updates.py",
    "repair_aegis.py",
    "download_win_wheels.py",
    "demo_audio_generator.py",

    # ── Routes (Blueprints) ───────────────────────────────────────────────
    "routes/__init__.py",
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/core_routes.py",
    "routes/data_routes.py",
    "routes/roles_routes.py",
    "routes/review_routes.py",
    "routes/scan_history_routes.py",
    "routes/jobs_routes.py",
    "routes/sow_routes.py",

    # ── Proposal Compare Module ───────────────────────────────────────────
    "proposal_compare/__init__.py",
    "proposal_compare/parser.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",

    # ── Hyperlink Validator Module ────────────────────────────────────────
    "hyperlink_validator/__init__.py",
    "hyperlink_validator/validator.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/models.py",
    "hyperlink_validator/storage.py",
    "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/docx_extractor.py",
    "hyperlink_validator/excel_extractor.py",

    # ── Statement Forge Module ────────────────────────────────────────────
    "statement_forge/__init__.py",
    "statement_forge/extractor.py",
    "statement_forge/models.py",
    "statement_forge/export.py",
    "statement_forge/routes.py",

    # ── Document Compare Module ───────────────────────────────────────────
    "document_compare/__init__.py",
    "document_compare/models.py",
    "document_compare/differ.py",
    "document_compare/routes.py",

    # ── Portfolio Module ──────────────────────────────────────────────────
    "portfolio/__init__.py",
    "portfolio/routes.py",

    # ── NLP Package ───────────────────────────────────────────────────────
    "nlp/__init__.py",
    "nlp/base.py",
    "nlp/config.py",
    "nlp/languagetool/__init__.py",
    "nlp/languagetool/client.py",
    "nlp/languagetool/checker.py",
    "nlp/readability/__init__.py",
    "nlp/readability/enhanced.py",
    "nlp/semantics/__init__.py",
    "nlp/semantics/checker.py",
    "nlp/semantics/wordnet.py",
    "nlp/spacy/__init__.py",
    "nlp/spacy/analyzer.py",
    "nlp/spacy/checkers.py",
    "nlp/spelling/__init__.py",
    "nlp/spelling/checker.py",
    "nlp/spelling/enchant.py",
    "nlp/spelling/symspell.py",
    "nlp/style/__init__.py",
    "nlp/style/checker.py",
    "nlp/style/proselint.py",
    "nlp/verbs/__init__.py",
    "nlp/verbs/checker.py",
    "nlp/verbs/pattern_en.py",

    # ── Templates ─────────────────────────────────────────────────────────
    "templates/index.html",

    # ── JavaScript: Root ──────────────────────────────────────────────────
    "static/js/adjudication-lookup.js",
    "static/js/app.js",
    "static/js/button-fixes.js",
    "static/js/function-tags.js",
    "static/js/help-content.js",
    "static/js/help-docs.js",
    "static/js/history-fixes.js",
    "static/js/presets_visualizations.js",
    "static/js/roles-dictionary-fix.js",
    "static/js/roles-export-fix.js",
    "static/js/roles-tabs-fix.js",
    "static/js/run-state-fixes.js",
    "static/js/statement-review-lookup.js",
    "static/js/twr-loader.js",
    "static/js/update-functions.js",

    # ── JavaScript: UI Module ─────────────────────────────────────────────
    "static/js/ui/events.js",
    "static/js/ui/modals.js",
    "static/js/ui/renderers.js",
    "static/js/ui/state.js",
    "static/js/ui/storage.js",

    # ── JavaScript: API Module ────────────────────────────────────────────
    "static/js/api/client.js",

    # ── JavaScript: Utils ─────────────────────────────────────────────────
    "static/js/utils/dom.js",

    # ── JavaScript: Features ──────────────────────────────────────────────
    "static/js/features/a11y-manager.js",
    "static/js/features/cinematic-loader.js",
    "static/js/features/cinematic-progress.js",
    "static/js/features/console-capture.js",
    "static/js/features/data-explorer.js",
    "static/js/features/demo-simulator.js",
    "static/js/features/doc-compare.js",
    "static/js/features/doc-compare-state.js",
    "static/js/features/document-viewer.js",
    "static/js/features/families.js",
    "static/js/features/fix-assistant-state.js",
    "static/js/features/frontend-logger.js",
    "static/js/features/graph-export.js",
    "static/js/features/guide-system.js",
    "static/js/features/hv-cinematic-progress.js",
    "static/js/features/hyperlink-validator.js",
    "static/js/features/hyperlink-validator-state.js",
    "static/js/features/hyperlink-visualizations.js",
    "static/js/features/landing-dashboard.js",
    "static/js/features/landing-page.js",
    "static/js/features/learner-client.js",
    "static/js/features/link-history.js",
    "static/js/features/mass-statement-review.js",
    "static/js/features/metrics-analytics.js",
    "static/js/features/minimap.js",
    "static/js/features/molten-progress.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/portfolio.js",
    "static/js/features/preview-modes.js",
    "static/js/features/proposal-compare.js",
    "static/js/features/report-client.js",
    "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js",
    "static/js/features/scan-progress-dashboard.js",
    "static/js/features/sound-effects.js",
    "static/js/features/sow-generator.js",
    "static/js/features/statement-history.js",
    "static/js/features/statement-review-mode.js",
    "static/js/features/statement-source-viewer.js",
    "static/js/features/style-presets.js",
    "static/js/features/triage.js",

    # ── JavaScript: Vendor Libraries ──────────────────────────────────────
    "static/js/vendor/chart.min.js",
    "static/js/vendor/d3.v7.min.js",
    "static/js/vendor/gsap.min.js",
    "static/js/vendor/Sortable.min.js",
    "static/js/vendor/lottie.min.js",
    "static/js/vendor/lucide.min.js",

    # ── CSS: Root ─────────────────────────────────────────────────────────
    "static/css/base.css",
    "static/css/charts.css",
    "static/css/components.css",
    "static/css/dark-mode.css",
    "static/css/layout.css",
    "static/css/modals.css",
    "static/css/print.css",
    "static/css/style.css",

    # ── CSS: Features ─────────────────────────────────────────────────────
    "static/css/features/batch-progress-dashboard.css",
    "static/css/features/cinematic-loader.css",
    "static/css/features/cinematic-progress.css",
    "static/css/features/data-explorer.css",
    "static/css/features/doc-compare.css",
    "static/css/features/export-suite.css",
    "static/css/features/fix-assistant.css",
    "static/css/features/guide-system.css",
    "static/css/features/hv-cinematic-progress.css",
    "static/css/features/hyperlink-enhanced.css",
    "static/css/features/hyperlink-validator.css",
    "static/css/features/landing-dashboard.css",
    "static/css/features/landing-page.css",
    "static/css/features/link-history.css",
    "static/css/features/mass-statement-review.css",
    "static/css/features/metrics-analytics.css",
    "static/css/features/molten-progress.css",
    "static/css/features/portfolio.css",
    "static/css/features/proposal-compare.css",
    "static/css/features/roles-studio.css",
    "static/css/features/scan-history.css",
    "static/css/features/scan-progress-dashboard.css",
    "static/css/features/settings.css",
    "static/css/features/sow-generator.css",
    "static/css/features/statement-forge.css",
    "static/css/features/statement-history.css",

    # ── Configuration ─────────────────────────────────────────────────────
    "version.json",
    "static/version.json",
    "requirements.txt",
    "requirements-nlp.txt",
    "role_dictionary_master.json",

    # ── Dictionaries ──────────────────────────────────────────────────────
    "dictionaries/aerospace.txt",
    "dictionaries/defense.txt",
    "dictionaries/software.txt",

    # ── Windows Batch Files ───────────────────────────────────────────────
    "Install_AEGIS.bat",
    "Install_AEGIS_OneClick.bat",
    "install_offline.bat",
    "Start_AEGIS.bat",
    "Restart_AEGIS.bat",
    "Repair_AEGIS.bat",
    "packaging/Install_AEGIS_OneClick.bat",
    "packaging/requirements-core.txt",
    "packaging/requirements-windows.txt",

    # ── Documentation ─────────────────────────────────────────────────────
    "CHANGELOG.md",
    "README.md",
]

# Directories that must exist before downloading
REQUIRED_DIRS = [
    "routes",
    "proposal_compare",
    "hyperlink_validator",
    "statement_forge",
    "document_compare",
    "portfolio",
    "nlp",
    "nlp/languagetool",
    "nlp/readability",
    "nlp/semantics",
    "nlp/spacy",
    "nlp/spelling",
    "nlp/style",
    "nlp/verbs",
    "templates",
    "static/js",
    "static/js/ui",
    "static/js/api",
    "static/js/utils",
    "static/js/features",
    "static/js/vendor",
    "static/css",
    "static/css/features",
    "dictionaries",
    "packaging",
]

# Files/directories to NEVER touch
PRESERVE = {
    "scan_history.db",
    "config.json",
    "wheels",
    "packaging/wheels",
    "temp",
    "backups",
    "updates",
    "logs",
    "static/audio",
    "static/img",
    "static/images",
    "test_docs",
    "test_documents",
    "__pycache__",
    ".git",
    "docling_models",
}


# ─── SSL Context Builder ────────────────────────────────────────────────────
def get_ssl_context():
    """Try multiple SSL strategies for corporate/air-gapped environments."""
    # Strategy 1: Default with certifi
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return ctx
    except Exception:
        pass

    # Strategy 2: System certificates
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        pass

    # Strategy 3: Unverified (last resort)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(rel_path, install_dir, ssl_ctx, dry_run=False):
    """Download a single file from GitHub."""
    url = f"{BASE_URL}/{rel_path}"
    dest = os.path.join(install_dir, rel_path.replace("/", os.sep))

    if dry_run:
        print(f"  [DRY] Would download: {rel_path}")
        return True

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AEGIS-FreshInstall/5.9.42",
            "Accept": "*/*",
        })
        response = urllib.request.urlopen(req, context=ssl_ctx, timeout=30)
        data = response.read()

        # Ensure parent directory exists
        parent = os.path.dirname(dest)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(dest, "wb") as f:
            f.write(data)

        return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  [SKIP] {rel_path} — not found in repo (may be local-only)")
        else:
            print(f"  [FAIL] {rel_path} — HTTP {e.code}: {e.reason}")
        return False

    except Exception as e:
        print(f"  [FAIL] {rel_path} — {str(e)[:80]}")
        return False


def create_backup(install_dir):
    """Create a timestamped backup of key files."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_fresh_install_{ts}")
    os.makedirs(backup_dir, exist_ok=True)

    # Back up critical files only (not entire tree — too slow)
    critical = [
        "app.py", "core.py", "scan_history.py", "config_logging.py",
        "version.json", "config.json", "templates/index.html",
        "static/js/app.js", "static/js/features/proposal-compare.js",
        "static/js/features/hyperlink-validator.js",
        "hyperlink_validator/routes.py", "hyperlink_validator/validator.py",
        "routes/config_routes.py", "routes/review_routes.py",
        "proposal_compare/routes.py", "proposal_compare/parser.py",
    ]

    backed = 0
    for f in critical:
        src = os.path.join(install_dir, f.replace("/", os.sep))
        if os.path.exists(src):
            dst_dir = os.path.join(backup_dir, os.path.dirname(f))
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(backup_dir, f.replace("/", os.sep)))
            backed += 1

    return backup_dir, backed


def verify_install_dir(path):
    """Verify this is actually an AEGIS install directory."""
    markers = ["app.py", "static", "templates"]
    for m in markers:
        if not os.path.exists(os.path.join(path, m)):
            return False
    return True


def main():
    print("=" * 70)
    print(f"  AEGIS Fresh Install — v{VERSION}")
    print(f"  Downloads ALL code files from GitHub")
    print("=" * 70)
    print()

    # Parse args
    dry_run = "--dry-run" in sys.argv
    no_backup = "--no-backup" in sys.argv

    # Determine install directory
    install_dir = os.path.dirname(os.path.abspath(__file__))

    # Verify we're in the right place
    if not verify_install_dir(install_dir):
        print(f"[ERROR] This doesn't look like an AEGIS install directory:")
        print(f"  {install_dir}")
        print()
        print("Expected to find: app.py, static/, templates/")
        print("Please place this script in your AEGIS folder and run again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"Install directory: {install_dir}")
    print(f"Total files to download: {len(FILES)}")
    print(f"Source: github.com/{REPO} (branch: {BRANCH})")
    print()

    if dry_run:
        print("[DRY RUN MODE — no files will be modified]\n")

    # Step 1: Backup
    if not no_backup and not dry_run:
        print("Step 1/4: Creating backup of critical files...")
        backup_dir, backed = create_backup(install_dir)
        print(f"  Backed up {backed} files to: {os.path.basename(backup_dir)}")
        print()
    else:
        print("Step 1/4: Backup skipped")
        print()

    # Step 2: Create directories
    print("Step 2/4: Ensuring directory structure...")
    if not dry_run:
        for d in REQUIRED_DIRS:
            full = os.path.join(install_dir, d.replace("/", os.sep))
            os.makedirs(full, exist_ok=True)
        print(f"  Created/verified {len(REQUIRED_DIRS)} directories")
    print()

    # Step 3: Download all files
    print("Step 3/4: Downloading files from GitHub...")
    print()

    ssl_ctx = get_ssl_context()

    success = 0
    failed = 0
    skipped = 0
    total = len(FILES)

    # Group files by category for display
    categories = {}
    for f in FILES:
        if "/" in f:
            cat = f.split("/")[0]
            if cat == "static":
                parts = f.split("/")
                if len(parts) >= 3:
                    cat = f"static/{parts[1]}/{parts[2]}" if parts[2] == "features" else f"static/{parts[1]}"
                else:
                    cat = "static"
        else:
            ext = os.path.splitext(f)[1]
            if ext == ".py":
                cat = "python-root"
            elif ext == ".bat":
                cat = "batch"
            else:
                cat = "config"
        categories.setdefault(cat, []).append(f)

    # Download file by file with progress
    for i, rel_path in enumerate(FILES, 1):
        pct = int((i / total) * 100)
        # Progress bar
        bar_len = 30
        filled = int(bar_len * i / total)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  [{bar}] {pct:3d}% ({i}/{total}) {rel_path[:50]:<50}")
        sys.stdout.flush()

        result = download_file(rel_path, install_dir, ssl_ctx, dry_run=dry_run)
        if result:
            success += 1
        else:
            failed += 1

    # Clear progress line
    sys.stdout.write("\r" + " " * 100 + "\r")
    sys.stdout.flush()

    print(f"  Downloaded: {success}")
    if failed > 0:
        print(f"  Failed/Skipped: {failed}")
    print()

    # Step 4: Post-install verification
    print("Step 4/4: Verifying installation...")
    if not dry_run:
        checks = {
            "app.py": "Flask entry point",
            "core.py": "AEGIS Engine",
            "templates/index.html": "HTML template",
            "static/js/app.js": "Main JavaScript",
            "static/js/features/proposal-compare.js": "Proposal Compare",
            "static/js/features/hyperlink-validator.js": "Hyperlink Validator",
            "hyperlink_validator/routes.py": "HV Routes (critical fix)",
            "routes/config_routes.py": "Config Routes (/api/capabilities)",
            "scan_history.py": "Database operations",
            "version.json": "Version info",
        }

        all_ok = True
        for f, desc in checks.items():
            full = os.path.join(install_dir, f.replace("/", os.sep))
            if os.path.exists(full):
                size = os.path.getsize(full)
                if size > 0:
                    print(f"  [OK] {desc} ({f}) — {size:,} bytes")
                else:
                    print(f"  [WARN] {desc} ({f}) — EMPTY FILE")
                    all_ok = False
            else:
                print(f"  [FAIL] {desc} ({f}) — MISSING")
                all_ok = False

        # Verify version
        vfile = os.path.join(install_dir, "version.json")
        if os.path.exists(vfile):
            try:
                with open(vfile) as vf:
                    vdata = json.load(vf)
                print(f"\n  Version: {vdata.get('version', 'unknown')}")
            except:
                pass

        print()
        if all_ok:
            print("=" * 70)
            print("  ✓ FRESH INSTALL COMPLETE")
            print("=" * 70)
        else:
            print("=" * 70)
            print("  ⚠ INSTALL COMPLETE WITH WARNINGS — check items above")
            print("=" * 70)
    else:
        print("  [DRY RUN] Verification skipped")

    # Summary
    print()
    print("PRESERVED (not touched):")
    print("  • scan_history.db — your scan data")
    print("  • config.json — your settings")
    print("  • wheels/ — pip packages")
    print("  • static/audio/ — demo narration files")
    print()
    print("NEXT STEPS:")
    print("  1. Restart AEGIS:")
    print("     • Double-click Restart_AEGIS.bat")
    print("     • Or: python app.py --debug")
    print()
    print("  2. Open browser to http://localhost:5050")
    print()
    print("  3. Verify Hyperlink Validator loads (should show auth badge)")
    print()

    if not dry_run:
        print(f"Total: {success} files installed, {failed} failed")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
