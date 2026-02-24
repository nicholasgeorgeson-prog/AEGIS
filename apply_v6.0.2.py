#!/usr/bin/env python3
"""
AEGIS v6.0.2 Comprehensive Update
Downloads ALL changed files from v6.0.0, v6.0.1, and v6.0.2 from GitHub
and places them directly into the correct locations in your AEGIS install.

Creates a timestamped backup of each file before overwriting.

Usage:
    Place this script in your AEGIS installation directory
    (where app.py, core.py, etc. live) and run:

    python apply_v6.0.2.py
    python3 apply_v6.0.2.py

No dependencies required - uses only Python standard library.
"""

import urllib.request
import ssl
import os
import sys
import shutil
from datetime import datetime

# -- Configuration --
REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"

# ============================================================
# CODE FILES - downloaded in main phase with backups
# ============================================================
CODE_FILES = [
    # --- Version files (always first) ---
    "version.json",
    "static/version.json",

    # --- Python backend - root ---
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
    "export_module.py",
    "markup_engine.py",
    "review_report.py",
    "proposal_compare_export.py",
    "pull_updates.py",
    "repair_aegis.py",
    "review_learner.py",
    "roles_learner.py",
    "sharepoint_connector.py",
    "requirements.txt",
    "role_dictionary_master.json",

    # --- Python backend - nlp/spelling ---
    "nlp/spelling/checker.py",

    # --- Python backend - routes ---
    "routes/__init__.py",
    "routes/_shared.py",
    "routes/config_routes.py",
    "routes/core_routes.py",
    "routes/data_routes.py",
    "routes/review_routes.py",
    "routes/roles_routes.py",
    "routes/sow_routes.py",

    # --- Python backend - statement_forge ---
    "statement_forge/routes.py",
    "statement_forge/statement_learner.py",

    # --- Python backend - proposal_compare ---
    "proposal_compare/__init__.py",
    "proposal_compare/analyzer.py",
    "proposal_compare/parser.py",
    "proposal_compare/projects.py",
    "proposal_compare/routes.py",
    "proposal_compare/structure_analyzer.py",
    "proposal_compare/pattern_learner.py",

    # --- Python backend - hyperlink_validator ---
    "hyperlink_validator/export.py",
    "hyperlink_validator/headless_validator.py",
    "hyperlink_validator/models.py",
    "hyperlink_validator/routes.py",
    "hyperlink_validator/validator.py",
    "hyperlink_validator/hv_learner.py",

    # --- Python backend - portfolio ---
    "portfolio/routes.py",

    # --- Templates ---
    "templates/index.html",

    # --- JavaScript ---
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
    "static/js/features/proposal-compare.js",
    "static/js/features/role-source-viewer.js",
    "static/js/features/roles.js",
    "static/js/features/scan-progress-dashboard.js",
    "static/js/features/statement-history.js",
    "static/js/features/statement-source-viewer.js",
    "static/js/features/pdf-viewer.js",
    "static/js/features/technology-showcase.js",
    "static/js/features/fix-assistant-state.js",

    # --- CSS ---
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
    "static/css/features/technology-showcase.css",
    "static/css/features/fix-assistant.css",

    # --- Dictionaries ---
    "dictionaries/defense.txt",

    # --- Installers / batch files ---
    "Install_AEGIS.bat",
    "Install_AEGIS_OneClick.bat",
    "install_offline.bat",
    "packaging/Install_AEGIS_OneClick.bat",
    "packaging/requirements-windows.txt",
    "Repair_AEGIS.bat",
    "Start_AEGIS.bat",

    # --- Audio manifests ---
    "static/audio/demo/manifest.json",
    "static/audio/cinema/manifest.json",

    # --- Docs ---
    "CLAUDE.md",
]

# ============================================================
# CINEMA AUDIO FILES - 18 clips
# ============================================================
CINEMA_AUDIO_FILES = [
    "static/audio/cinema/cinema_aegis_boot__step0.mp3",
    "static/audio/cinema/cinema_architecture_overview__step0.mp3",
    "static/audio/cinema/cinema_breaking_point__step0.mp3",
    "static/audio/cinema/cinema_classified_ready__step0.mp3",
    "static/audio/cinema/cinema_convergence__step0.mp3",
    "static/audio/cinema/cinema_doc_chaos__step0.mp3",
    "static/audio/cinema/cinema_document_scan__step0.mp3",
    "static/audio/cinema/cinema_fortress__step0.mp3",
    "static/audio/cinema/cinema_hud_activates__step0.mp3",
    "static/audio/cinema/cinema_hyperlink_validator__step0.mp3",
    "static/audio/cinema/cinema_learning_system__step0.mp3",
    "static/audio/cinema/cinema_logo_reveal__step0.mp3",
    "static/audio/cinema/cinema_proposal_compare__step0.mp3",
    "static/audio/cinema/cinema_review_engine__step0.mp3",
    "static/audio/cinema/cinema_roles_studio__step0.mp3",
    "static/audio/cinema/cinema_standards_wall__step0.mp3",
    "static/audio/cinema/cinema_stat_cascade__step0.mp3",
    "static/audio/cinema/cinema_statement_forge__step0.mp3",
]

# ============================================================
# DEMO AUDIO FILES - 542 clips (generated programmatically)
# Each tuple is (section_name, number_of_steps)
# ============================================================
DEMO_AUDIO_SECTIONS = [
    ("accessibility_features", 4),
    ("adjudication", 6),
    ("adjudication_exports", 5),
    ("adjudication_sharing", 4),
    ("auto_adjudicate", 4),
    ("batch", 6),
    ("batch_grouping", 4),
    ("categories_view", 3),
    ("change_navigation", 3),
    ("chart_interactions", 5),
    ("checker_categories", 5),
    ("checker_config", 5),
    ("compare", 6),
    ("compare_doc_switcher", 4),
    ("compare_export", 3),
    ("compare_viewer", 4),
    ("comparison_history", 3),
    ("comparison_view", 3),
    ("data_management", 3),
    ("data_mgmt", 4),
    ("data_operations", 5),
    ("deep_validate", 4),
    ("details_source", 4),
    ("diagnostics_deep", 5),
    ("diagnostics_tab", 3),
    ("dictionary", 6),
    ("dictionary_exports", 5),
    ("dictionary_imports", 5),
    ("diff_views", 4),
    ("display_settings", 3),
    ("document_config", 4),
    ("document_selection", 4),
    ("document_viewer", 4),
    ("documents_analytics", 4),
    ("documents_tab", 4),
    ("domain_analytics", 3),
    ("edit_role", 4),
    ("exclusions", 3),
    ("exec_summary", 4),
    ("export_docx", 4),
    ("export_excel_csv", 4),
    ("export_filters", 5),
    ("export_pdf", 4),
    ("export_results", 4),
    ("export_suite", 6),
    ("extraction", 5),
    ("family_patterns", 4),
    ("feature_tiles", 5),
    ("file_input", 4),
    ("file_loading", 4),
    ("fix_assistant", 4),
    ("folder_scan", 5),
    ("forge", 8),
    ("forge_sub_modals", 5),
    ("function_tags", 5),
    ("general_tab", 4),
    ("getting_started", 4),
    ("graph_controls", 5),
    ("graph_view", 5),
    ("heatmap_view", 4),
    ("help_navigation", 4),
    ("history", 5),
    ("history_actions", 4),
    ("history_overview", 3),
    ("history_table", 4),
    ("hv_export_formats", 5),
    ("inline_editing", 4),
    ("keyboard_shortcuts", 5),
    ("landing", 7),
    ("learning_system", 6),
    ("link_history_export", 3),
    ("metric_cards", 5),
    ("metrics", 8),
    ("metrics_export", 5),
    ("modes_settings", 4),
    ("network_auth", 3),
    ("output_preview", 3),
    ("overview_cards", 4),
    ("overview_dashboard", 5),
    ("overview_tab", 5),
    ("pattern_learning", 4),
    ("portfolio", 5),
    ("portfolio_actions", 3),
    ("preview_discovery", 3),
    ("profile_management", 4),
    ("profiles", 4),
    ("progress_dashboard", 4),
    ("project_dashboard", 3),
    ("proposal-compare", 8),
    ("proposals_analytics", 4),
    ("quality_gates", 3),
    ("quality_tab", 4),
    ("raci_matrix", 5),
    ("red_flags", 4),
    ("reload_compare", 3),
    ("results_aggregation", 4),
    ("results_filtering", 6),
    ("results_filtering_hv", 5),
    ("review", 10),
    ("review_edit", 4),
    ("review_options", 4),
    ("review_presets", 5),
    ("review_progress", 5),
    ("role_doc_matrix", 4),
    ("roles", 10),
    ("roles_analytics", 4),
    ("score_breakdown", 4),
    ("search_filtering", 4),
    ("selection_tools", 4),
    ("settings", 8),
    ("sharing_settings", 3),
    ("sorting_filtering", 3),
    ("sow", 5),
    ("statement_integration", 4),
    ("statements_tab", 3),
    ("template_upload", 3),
    ("triage_mode", 5),
    ("updates_tab", 3),
    ("upload_extract", 4),
    ("upload_paste", 4),
    ("validator", 7),
    ("vendor_scores", 4),
]

# Generate demo audio file list programmatically
DEMO_AUDIO_FILES = []
for _section, _count in DEMO_AUDIO_SECTIONS:
    for _i in range(_count):
        DEMO_AUDIO_FILES.append(f"static/audio/demo/{_section}__step{_i}.mp3")


def get_ssl_context():
    """Get SSL context with aggressive fallback for embedded Python."""
    # Try 1: certifi
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using certifi certificates")
        return ctx
    except Exception:
        pass

    # Try 2: system certs
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(
            urllib.request.Request("https://github.com"),
            context=ctx, timeout=5
        )
        print("  SSL: Using system certificates")
        return ctx
    except Exception:
        pass

    # Try 3: unverified (SSLContext directly, not create_default_context)
    print("  [WARN] SSL certificates not available - using unverified HTTPS")
    print("         (This is safe for downloading from GitHub)")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(filepath, ssl_ctx, timeout=30):
    """Download a single file from GitHub raw content. Returns bytes or None."""
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{filepath}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  FAIL  {filepath} -- {e}")
        return None


def main():
    # Detect install directory (where this script is running)
    install_dir = os.path.dirname(os.path.abspath(__file__))

    # Verify we're in the right place
    has_app = os.path.exists(os.path.join(install_dir, "app.py"))
    has_static = os.path.isdir(os.path.join(install_dir, "static"))
    if not has_app and not has_static:
        print("=" * 60)
        print("  WARNING: This doesn't look like an AEGIS directory!")
        print(f"  Current location: {install_dir}")
        print()
        print("  Expected to find app.py and static/ folder here.")
        print("  Place this script in your AEGIS installation directory.")
        print("=" * 60)
        print()
        resp = input("  Continue anyway? (y/n): ").strip().lower()
        if resp != 'y':
            print("  Cancelled.")
            return 1

    total_audio = len(DEMO_AUDIO_FILES) + len(CINEMA_AUDIO_FILES)

    print()
    print("  " + "=" * 58)
    print("    AEGIS v6.0.2 Comprehensive Update")
    print("    Includes all changes from v6.0.0, v6.0.1, and v6.0.2")
    print("  " + "=" * 58)
    print()
    print("  v6.0.2 - Fix Assistant Reviewer Mode + Audio Fix:")
    print("    - Reviewer / Document Owner mode toggle in Fix Assistant")
    print("    - Demo audio voice changed to en-US-AvaNeural")
    print("    - US English spelling dictionary updates")
    print()
    print("  v6.0.1 - Proposal Compare Enhancements:")
    print("    - Company name tiles (2-line clamp, word-break)")
    print("    - Re-Analyze from Project Detail view")
    print("    - Contract term badges on proposal cards")
    print()
    print("  v6.0.0 - Cinematic Technology Showcase:")
    print("    - Full-screen Canvas-animated cinematic video")
    print("    - 18 narrated cinema audio clips")
    print("    - Behind the Scenes landing page tile")
    print()
    print(f"  Install dir:  {install_dir}")
    print(f"  Code files:   {len(CODE_FILES)}")
    print(f"  Audio files:  {total_audio} ({len(DEMO_AUDIO_FILES)} demo + {len(CINEMA_AUDIO_FILES)} cinema)")
    print(f"  Total files:  {len(CODE_FILES) + total_audio}")
    print()

    # Set up SSL
    print("  Setting up SSL...")
    ssl_ctx = get_ssl_context()
    print()

    # Create backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(install_dir, "backups", f"pre_v6.0.2_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"  Backup dir: {backup_dir}")
    print()

    # ========================================================
    # PHASE 1: Download and apply code files
    # ========================================================
    print("  PHASE 1: Downloading and applying code files...")
    print("  " + "-" * 54)
    code_success = 0
    code_failed = 0
    code_backed_up = 0

    for filepath in CODE_FILES:
        # Download from GitHub
        data = download_file(filepath, ssl_ctx)
        if data is None:
            code_failed += 1
            continue

        dest = os.path.join(install_dir, filepath)

        # Backup existing file
        if os.path.exists(dest):
            backup_dest = os.path.join(backup_dir, filepath)
            backup_dest_dir = os.path.dirname(backup_dest)
            if backup_dest_dir:
                os.makedirs(backup_dest_dir, exist_ok=True)
            try:
                shutil.copy2(dest, backup_dest)
                code_backed_up += 1
            except Exception as e:
                print(f"  [WARN] Could not backup {filepath}: {e}")

        # Create directory structure if needed
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Write the new file (binary safe)
        try:
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  OK    {filepath} ({size_kb:.1f} KB)")
            code_success += 1
        except Exception as e:
            print(f"  FAIL  {filepath} -- write error: {e}")
            code_failed += 1

    print()
    print(f"  Code phase complete: {code_success} applied, {code_failed} failed, {code_backed_up} backed up")
    print()

    # ========================================================
    # PHASE 2: Download audio files (no backups needed)
    # ========================================================
    all_audio = DEMO_AUDIO_FILES + CINEMA_AUDIO_FILES
    total_audio_count = len(all_audio)

    print(f"  PHASE 2: Downloading audio files ({len(DEMO_AUDIO_FILES)} demo + {len(CINEMA_AUDIO_FILES)} cinema)...")
    print("  " + "-" * 54)
    print()

    # Ensure audio directories exist
    os.makedirs(os.path.join(install_dir, "static", "audio", "demo"), exist_ok=True)
    os.makedirs(os.path.join(install_dir, "static", "audio", "cinema"), exist_ok=True)

    audio_success = 0
    audio_failed = 0

    for idx, filepath in enumerate(all_audio, 1):
        # Progress indicator
        filename = os.path.basename(filepath)
        progress = f"[{idx:3d}/{total_audio_count}]"
        sys.stdout.write(f"\r  {progress} {filename:<55s}")
        sys.stdout.flush()

        # Download from GitHub
        data = download_file(filepath, ssl_ctx, timeout=15)
        if data is None:
            audio_failed += 1
            # download_file already printed FAIL, add newline
            continue

        dest = os.path.join(install_dir, filepath)

        # Write the audio file (binary)
        try:
            with open(dest, "wb") as f:
                f.write(data)
            audio_success += 1
        except Exception as e:
            print(f"\n  FAIL  {filepath} -- write error: {e}")
            audio_failed += 1

    # Clear the progress line and print summary
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()
    print(f"  Audio phase complete: {audio_success} applied, {audio_failed} failed")
    print()

    # ========================================================
    # SUMMARY
    # ========================================================
    total_success = code_success + audio_success
    total_failed = code_failed + audio_failed
    total_files = len(CODE_FILES) + total_audio_count

    print("  " + "=" * 58)
    print("  SUMMARY")
    print("  " + "=" * 58)
    print(f"  Code files:  {code_success} applied, {code_failed} failed, {code_backed_up} backed up")
    print(f"  Audio files: {audio_success} applied, {audio_failed} failed")
    print(f"  Total:       {total_success}/{total_files} files")
    print()

    if total_failed == 0:
        print("  All files applied successfully!")
        print()
        print("  IMPORTANT: This update changes Python backend code.")
        print("  You MUST restart AEGIS for changes to take effect.")
        print()
        print("  NEXT STEPS:")
        print("    1. Close this window")
        print("    2. Restart AEGIS with Start_AEGIS.bat or restart_aegis.sh")
        print("    3. Open AEGIS in your browser")
        print("    4. Verify version shows 6.0.2 in the footer")
        print()
        print(f"  If something went wrong, your old files are in:")
        print(f"    {backup_dir}")
    else:
        print(f"  WARNING: {total_failed} file(s) failed to download/apply.")
        print("  Check your internet connection and try again.")
        print()
        print(f"  Successfully applied files are already in place.")
        print(f"  Old code files backed up to: {backup_dir}")

    print()
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
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
