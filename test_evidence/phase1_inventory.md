# AEGIS Project Inventory

**Version**: 4.6.2
**Generated**: 2026-02-13
**Root**: `/Users/nick/Desktop/Work_Tools/TechWriterReview/`

---

## 1. Directory Tree

### Top-Level (2 levels deep)

```
TechWriterReview/
|-- app.py                          # Flask main app (10,320 lines)
|-- core.py                         # AEGISEngine + extractors (2,708 lines)
|-- __main__.py                     # CLI entry point
|-- config.json                     # Runtime configuration
|-- version.json                    # Version metadata + changelog
|-- requirements.txt                # Python dependencies
|-- requirements-nlp.txt            # NLP-specific dependencies
|-- scan_history.db                 # Primary SQLite database (226 MB)
|
|-- data/
|   |-- scan_history.db             # Empty (unused copy)
|   |-- techwriter.db               # Legacy/secondary database (220 KB)
|   |-- decision_patterns.db        # Fix Assistant decision patterns
|   |-- adaptive_learning.db        # Adaptive learner patterns
|   |-- aerospace_patterns.json     # Aerospace-specific patterns
|   |-- as9100_doc_requirements.json
|   |-- dale_chall_3000.json        # Readability word list
|   |-- mil_std_40051_patterns.json
|   |-- product_names.json
|   |-- s1000d_basic_rules.json
|   |-- spache_easy_words.json      # Readability word list
|   |-- ste100_approved_words.json  # Simplified Technical English
|   |-- universal_acronyms.json
|   |-- dictionaries/               # Custom spell-check dictionaries
|   |-- external_databases/         # External reference data
|
|-- document_compare/               # Document Comparison package
|   |-- __init__.py
|   |-- differ.py
|   |-- models.py
|   |-- routes.py
|
|-- hyperlink_validator/            # Hyperlink Validator package
|   |-- __init__.py
|   |-- docx_extractor.py
|   |-- excel_extractor.py
|   |-- export.py
|   |-- headless_validator.py
|   |-- models.py
|   |-- routes.py
|   |-- storage.py
|   |-- validator.py
|
|-- statement_forge/                # Statement Forge package
|   |-- __init__.py
|   |-- export.py
|   |-- extractor.py
|   |-- models.py
|   |-- routes.py
|
|-- portfolio/                      # Portfolio batch review package
|   |-- __init__.py
|   |-- routes.py
|
|-- nlp/                            # NLP subsystem (see Section 2c)
|   |-- __init__.py
|   |-- base.py
|   |-- config.py
|   |-- languagetool/
|   |-- readability/
|   |-- semantics/
|   |-- spacy/
|   |-- spelling/
|   |-- style/
|   |-- verbs/
|
|-- static/                         # Frontend assets (see below)
|-- templates/                      # Jinja2 templates
|   |-- index.html                  # Single Page Application
|   |-- loader-demo.html            # Loader animation demo
|
|-- tests/                          # Test suite
|-- test_documents/                 # Sample documents for testing
|-- test_evidence/                  # Test evidence artifacts
|-- logs/                           # Application logs
|-- temp/                           # Temporary file storage
|-- updates/                        # Update packages drop zone
|-- deployment/                     # Distribution packaging scripts
|-- docs/                           # Project documentation
|-- dictionaries/                   # Custom dictionary text files
|-- tools/                          # Standalone utility scripts
|-- images/                         # App icon (twr_icon.ico)
|-- nlp_offline/                    # Offline NLP package bundle
|-- tesseract_package/              # OCR engine distribution
```

### static/ (3 levels deep)

```
static/
|-- css/
|   |-- style.css                   # Root stylesheet (all @imports)
|   |-- base.css                    # Base typography, variables
|   |-- layout.css                  # Grid, flex layouts
|   |-- components.css              # Reusable UI components
|   |-- modals.css                  # Modal dialogs
|   |-- charts.css                  # Chart.js / D3 chart styles
|   |-- dark-mode.css               # Dark mode variable overrides
|   |-- features/
|       |-- cinematic-loader.css
|       |-- cinematic-progress.css
|       |-- data-explorer.css
|       |-- doc-compare.css
|       |-- fix-assistant.css
|       |-- hv-cinematic-progress.css
|       |-- hyperlink-enhanced.css
|       |-- hyperlink-validator.css
|       |-- landing-dashboard.css   # (dead code)
|       |-- landing-page.css
|       |-- link-history.css
|       |-- metrics-analytics.css
|       |-- molten-progress.css
|       |-- portfolio.css
|       |-- roles-studio.css
|       |-- scan-history.css
|       |-- scan-progress-dashboard.css
|       |-- sow-generator.css
|       |-- statement-forge.css
|       |-- statement-history.css
|
|-- js/
|   |-- app.js                      # Main application controller
|   |-- adjudication-lookup.js      # Global adjudication badge utility
|   |-- button-fixes.js             # Button behavior patches
|   |-- function-tags.js            # Function tag management UI
|   |-- help-content.js             # Help panel content (legacy)
|   |-- help-docs.js                # Help documentation (65 sections)
|   |-- history-fixes.js            # Scan history UI patches
|   |-- presets_visualizations.js   # Style preset charts
|   |-- roles-dictionary-fix.js     # Dictionary tab IIFE rewrite
|   |-- roles-export-fix.js         # Export/share dropdown handlers
|   |-- roles-tabs-fix.js           # Roles Studio tab rendering
|   |-- run-state-fixes.js          # Review run state management
|   |-- statement-review-lookup.js  # Statement review badge utility
|   |-- twr-loader.js               # App initialization loader
|   |-- update-functions.js         # Update manager frontend
|   |-- api/
|   |   |-- client.js               # API client wrapper
|   |-- features/
|   |   |-- a11y-manager.js
|   |   |-- cinematic-loader.js
|   |   |-- cinematic-progress.js
|   |   |-- console-capture.js
|   |   |-- data-explorer.js
|   |   |-- doc-compare.js
|   |   |-- doc-compare-state.js
|   |   |-- document-viewer.js
|   |   |-- families.js
|   |   |-- fix-assistant-state.js
|   |   |-- frontend-logger.js
|   |   |-- graph-export.js
|   |   |-- hv-cinematic-progress.js
|   |   |-- hyperlink-validator.js
|   |   |-- hyperlink-validator-state.js
|   |   |-- hyperlink-visualizations.js
|   |   |-- landing-dashboard.js    # (dead code)
|   |   |-- landing-page.js
|   |   |-- learner-client.js
|   |   |-- link-history.js
|   |   |-- metrics-analytics.js
|   |   |-- minimap.js
|   |   |-- molten-progress.js
|   |   |-- pdf-viewer.js
|   |   |-- portfolio.js
|   |   |-- preview-modes.js
|   |   |-- report-client.js
|   |   |-- role-source-viewer.js
|   |   |-- roles.js
|   |   |-- scan-progress-dashboard.js
|   |   |-- sound-effects.js
|   |   |-- sow-generator.js
|   |   |-- statement-history.js
|   |   |-- statement-review-mode.js
|   |   |-- style-presets.js
|   |   |-- triage.js
|   |-- ui/
|   |   |-- events.js
|   |   |-- modals.js
|   |   |-- renderers.js
|   |   |-- state.js
|   |   |-- storage.js
|   |-- utils/
|   |   |-- dom.js
|   |-- vendor/
|       |-- chart.min.js            # Chart.js
|       |-- d3.v7.min.js            # D3.js v7
|       |-- gsap.min.js             # GSAP animation
|       |-- lottie.min.js           # Lottie animation
|       |-- lucide.min.js           # Lucide icons
|       |-- Sortable.min.js         # Sortable.js drag-drop
|       |-- pdfjs/                  # PDF.js v4.2.67
|
|-- images/
|   |-- logo.svg
|   |-- aegis_loader_28px.svg
|   |-- branding/
|
|-- animations/                     # Lottie animation files
|-- test_files/                     # Test Excel/DOCX files
```

---

## 2. Python Files Inventory

### 2a. Core Application (6 files)

| File | Lines | Purpose |
|------|------:|---------|
| `app.py` | 10,320 | Flask main app: all `/api/*` routes, CSRF, session management, blueprint registration |
| `core.py` | 2,708 | AEGISEngine: MammothDocumentExtractor, Pymupdf4llmExtractor, checker orchestration |
| `__main__.py` | 579 | CLI entry point (`python -m AEGIS`) for batch/single-file analysis |
| `config_logging.py` | 761 | Centralized logging configuration, log rotation, formatters |
| `database.py` | 663 | Legacy database abstraction layer (techwriter.db) |
| `scan_history.py` | 5,686 | Primary database operations: scan CRUD, role dictionary, statements, export/import |

### 2b. Checkers and Analyzers (30 files)

| File | Lines | Purpose |
|------|------:|---------|
| `acronym_checker.py` | 1,461 | Detects undefined/inconsistent acronyms in documents |
| `acronym_enhanced_checkers.py` | 355 | Extended acronym detection (first-use, expansion consistency) |
| `base_checker.py` | 390 | Abstract base class for all checkers |
| `clarity_checkers.py` | 514 | Readability and clarity issue detection (long sentences, jargon) |
| `compliance_checkers.py` | 623 | AS9100/S1000D/MIL-STD compliance verification |
| `comprehensive_hyperlink_checker.py` | 1,948 | HTTP link validation with HEAD/GET fallback and auth support |
| `cross_reference_validator.py` | 532 | Validates internal document cross-references |
| `document_checker.py` | 604 | Structure and formatting checks (headings, numbering) |
| `document_comparison_checker.py` | 437 | Cross-document consistency checking |
| `document_quality_checkers.py` | 612 | Overall document quality metrics and scoring |
| `enhanced_analyzers.py` | 762 | Advanced analysis passes (ambiguity, completeness) |
| `enhanced_grammar_checker.py` | 330 | Extended grammar rules beyond basic checks |
| `enhanced_passive_checker.py` | 532 | Passive voice detection with context-aware exceptions |
| `extended_checkers.py` | 1,288 | Additional checker collection (tense, voice, style) |
| `fragment_checker.py` | 547 | Sentence fragment detection |
| `grammar_checker.py` | 375 | Core grammar checking (subject-verb agreement, tense) |
| `hyperlink_checker.py` | 771 | Basic URL format and link text quality checks |
| `image_figure_checker.py` | 462 | Figure/image reference and caption validation |
| `passivepy_checker.py` | 423 | PassivePy-based passive voice detection |
| `procedural_writing_checkers.py` | 371 | Step/instruction format verification |
| `punctuation_checker.py` | 308 | Punctuation consistency and correctness |
| `readability_enhanced.py` | 551 | Comprehensive readability metrics (Flesch, Dale-Chall, SMOG) |
| `requirements_checker.py` | 280 | Requirements statement quality (shall/will/must validation) |
| `sentence_checker.py` | 302 | Sentence structure analysis (length, complexity) |
| `spell_checker.py` | 613 | Spell checking with technical dictionary support |
| `ste100_checker.py` | 577 | Simplified Technical English (ASD-STE100) compliance |
| `structure_analyzer.py` | 853 | Document structure analysis (heading hierarchy, sections) |
| `style_consistency_checkers.py` | 906 | Style guide compliance (Microsoft, Chicago, etc.) |
| `terminology_checker.py` | 612 | Term consistency and preferred terminology |
| `writing_quality_checker.py` | 671 | Overall writing quality metrics and scoring |

### 2c. NLP Modules (24 files across nlp/ package)

| File | Lines | Purpose |
|------|------:|---------|
| `nlp/__init__.py` | 158 | NLP subsystem initialization, feature detection |
| `nlp/base.py` | 265 | Base NLP checker class, common utilities |
| `nlp/config.py` | 304 | NLP configuration and capability management |
| `nlp/languagetool/__init__.py` | 67 | LanguageTool integration init |
| `nlp/languagetool/checker.py` | 183 | LanguageTool grammar/style checker adapter |
| `nlp/languagetool/client.py` | 279 | LanguageTool Python library client |
| `nlp/readability/__init__.py` | 87 | Readability module init |
| `nlp/readability/enhanced.py` | 356 | Enhanced readability scoring (7+ metrics) |
| `nlp/semantics/__init__.py` | 91 | Semantics module init |
| `nlp/semantics/checker.py` | 271 | Semantic analysis checker (word choice, redundancy) |
| `nlp/semantics/wordnet.py` | 326 | WordNet integration for synonym/hypernym analysis |
| `nlp/spacy/__init__.py` | 65 | spaCy module init |
| `nlp/spacy/analyzer.py` | 501 | spaCy NLP pipeline (POS tagging, NER, dependency parsing) |
| `nlp/spacy/checkers.py` | 353 | spaCy-powered grammar and style checkers |
| `nlp/spelling/__init__.py` | 77 | Spelling module init |
| `nlp/spelling/checker.py` | 223 | Unified spelling checker coordinator |
| `nlp/spelling/enchant.py` | 291 | PyEnchant spell checker adapter |
| `nlp/spelling/symspell.py` | 282 | SymSpell fast spell checker adapter |
| `nlp/style/__init__.py` | 78 | Style module init |
| `nlp/style/checker.py` | 174 | Style checker coordinator |
| `nlp/style/proselint.py` | 255 | Proselint integration for prose quality |
| `nlp/verbs/__init__.py` | 76 | Verb analysis module init |
| `nlp/verbs/checker.py` | 192 | Verb tense and form checker |
| `nlp/verbs/pattern_en.py` | 357 | English verb conjugation patterns |

**Top-level NLP integration files:**

| File | Lines | Purpose |
|------|------:|---------|
| `nlp_enhanced.py` | 1,207 | Enhanced NLP orchestrator (spaCy + LanguageTool combined) |
| `nlp_enhancer.py` | 517 | NLP enhancement wrapper for base checkers |
| `nlp_integration.py` | 799 | NLP system integration and initialization |
| `nlp_utils.py` | 1,119 | NLP utility functions (tokenization, normalization) |
| `text_statistics.py` | 1,045 | Text statistical analysis (word freq, complexity metrics) |
| `semantic_analyzer.py` | 602 | Standalone semantic similarity and coherence analyzer |
| `prose_linter.py` | 1,174 | Advanced prose quality linting |

### 2d. Utilities and Infrastructure (23 files)

| File | Lines | Purpose |
|------|------:|---------|
| `api_extensions.py` | 914 | Additional API blueprint: export, history, baseline, analytics |
| `adaptive_learner.py` | 1,408 | Machine learning-free adaptive pattern learner |
| `acronym_database.py` | 451 | Acronym database management and lookup |
| `acronym_extractor.py` | 661 | Automatic acronym extraction from documents |
| `auto_fixer.py` | 759 | Automatic issue correction engine |
| `comment_inserter.py` | 1,289 | Word document comment insertion |
| `config.json` | -- | Runtime configuration (JSON) |
| `context_utils.py` | 425 | Rich context generation for review issues |
| `decision_learner.py` | 532 | Rule-based user decision tracking and prediction |
| `diagnostics.py` | 557 | Comprehensive diagnostics and logging module |
| `diagnostic_export.py` | 2,035 | Diagnostic report HTML generator |
| `docling_extractor.py` | 1,425 | Docling document extraction (subprocess with timeout) |
| `export_module.py` | 936 | Document export (DOCX/CSV/XLSX) |
| `fix_assistant_api.py` | 857 | Fix Assistant v2 API layer |
| `hyperlink_health.py` | 1,382 | Hyperlink health monitoring and reporting |
| `job_manager.py` | 582 | Background job queue manager |
| `markup_engine.py` | 1,220 | Word document markup with tracked changes (COM-based) |
| `ocr_extractor.py` | 355 | Tesseract OCR text extraction |
| `pdf_extractor.py` | 571 | Legacy PDF extraction |
| `pdf_extractor_v2.py` | 1,026 | Enhanced PDF extraction (pymupdf) |
| `pdf_extractor_enhanced.py` | 501 | PDF extraction with pymupdf4llm Markdown output |
| `style_presets.py` | 678 | Style guide presets (Microsoft, Chicago, APA, etc.) |
| `update_manager.py` | 1,778 | FileRouter: .aegis-roles auto-import, updates detection |
| `technical_dictionary.py` | 1,374 | Technical term dictionary management |

### 2e. Role Analysis and Export (14 files)

| File | Lines | Purpose |
|------|------:|---------|
| `role_extractor_v3.py` | 3,070 | Primary role extraction engine v3 |
| `role_integration.py` | 1,059 | Role integration and aggregation across documents |
| `role_analyzer.py` | 445 | Role analysis and metrics |
| `role_management_studio_v3.py` | 1,740 | Role Management Studio backend logic |
| `role_consolidation_engine.py` | 1,228 | Intelligent role merging (fuzzy match, normalization) |
| `role_consolidation.py` | 582 | Role consolidation orchestrator |
| `role_comparison.py` | 577 | Multi-document role comparison |
| `requirements_analyzer.py` | 662 | Requirements analysis and quality scoring |
| `adjudication_export.py` | 1,266 | Standalone HTML kanban board generator |
| `adjudication_report.py` | 371 | PDF adjudication report (reportlab) |
| `hierarchy_export.py` | 3,263 | Role Inheritance Map HTML generator (4 views) |
| `role_template_export.py` | 2,039 | Role import template HTML generator |
| `sipoc_parser.py` | 764 | SIPOC Excel parser (dual-mode: hierarchy vs process) |
| `sow_generator.py` | 1,130 | Statement of Work HTML generator |

### 2f. Subpackage Route Files (4 packages)

| Package | File | Lines | Purpose |
|---------|------|------:|---------|
| `document_compare/` | `routes.py` | -- | Compare API: documents, scans, diff, issues |
| `document_compare/` | `differ.py` | -- | Document diffing engine |
| `document_compare/` | `models.py` | -- | Comparison data models |
| `hyperlink_validator/` | `routes.py` | 1,927 | HV API: validate, rescan, exclusions, history, export |
| `hyperlink_validator/` | `validator.py` | 1,820 | URL validation engine (requests + session pooling) |
| `hyperlink_validator/` | `headless_validator.py` | 482 | Playwright headless browser validator |
| `hyperlink_validator/` | `models.py` | 1,281 | HV data models and URL classification |
| `hyperlink_validator/` | `export.py` | 966 | HV result export (highlighted DOCX/Excel) |
| `hyperlink_validator/` | `storage.py` | 651 | HV SQLite storage layer |
| `hyperlink_validator/` | `docx_extractor.py` | 509 | DOCX hyperlink extraction |
| `hyperlink_validator/` | `excel_extractor.py` | 490 | Excel hyperlink extraction |
| `statement_forge/` | `routes.py` | -- | Statement Forge API: extract, CRUD, export, compare |
| `statement_forge/` | `extractor.py` | -- | Statement extraction pipeline |
| `statement_forge/` | `export.py` | -- | Statement export (DOCX/CSV) |
| `statement_forge/` | `models.py` | -- | Statement data models |
| `portfolio/` | `routes.py` | -- | Portfolio API: batches, documents, stats |

### 2g. Reports and HTML Generators (3 files)

| File | Lines | Purpose |
|------|------:|---------|
| `report_generator.py` | 331 | Core PDF report generator |
| `report_html_generator.py` | 3,111 | Rich interactive HTML report with charts and Sankey diagrams |
| `diagnostic_export.py` | 2,035 | Diagnostic report HTML export |

### 2h. Tests (11 files)

| File | Lines | Purpose |
|------|------:|---------|
| `tests.py` | 3,220 | Main test suite (top-level) |
| `test_enhancements.py` | 332 | Enhancement feature tests |
| `test_scan_analysis.py` | 323 | Scan analysis integration tests |
| `tests/test_adaptive_learner.py` | -- | Adaptive learner unit tests |
| `tests/test_advanced_checkers.py` | -- | Advanced checker unit tests |
| `tests/test_checker_performance.py` | -- | Checker performance benchmarks |
| `tests/test_e2e_comprehensive.py` | -- | End-to-end comprehensive tests |
| `tests/test_nlp_enhanced.py` | -- | NLP enhanced checker tests |
| `tests/test_nlp_integration.py` | -- | NLP integration tests |
| `tests/test_technical_dictionary.py` | -- | Technical dictionary tests |
| `tests/test_terminology_validation.py` | -- | Terminology validation tests |
| `tests/test_v340_checkers.py` | -- | v3.4.0 checker tests |

### 2i. Scripts and Utilities (16 files)

| File | Lines | Purpose |
|------|------:|---------|
| `batch_test_enhancements.py` | 247 | Batch test runner for enhancements |
| `check_pdf_capabilities.py` | 652 | PDF library capability checker |
| `enhanced_table_extractor.py` | 508 | Enhanced table extraction from documents |
| `table_processor.py` | 433 | Table detection and processing |
| `install_nlp.py` | 223 | NLP dependency installer (online) |
| `install_nlp_offline.py` | 274 | NLP dependency installer (air-gapped) |
| `load_test_docs.py` | 138 | Test document loader (HTTP client to local server) |
| `migrate_function_tags.py` | 309 | Database migration: adds function tag tables |
| `setup_tesseract.py` | 431 | Tesseract OCR setup utility |
| `word_language_checker.py` | 496 | Word-level language analysis |
| `aerospace_role_analysis.py` | 282 | Aerospace-specific role analysis script |
| `defense_role_analysis.py` | 392 | Defense industry role analysis script |
| `defense_role_analysis_expanded.py` | 255 | Expanded defense role analysis |
| `faa_exhaustive_analysis.py` | 417 | FAA document exhaustive analysis |
| `manual_analysis_comparison.py` | 376 | Manual vs automated analysis comparison |
| `manual_osha_analysis.py` | 283 | Manual OSHA document analysis |
| `manual_role_analysis.py` | 596 | Manual role extraction analysis |
| `manual_stanford_analysis.py` | 258 | Manual Stanford SOP analysis |
| `run_enhancement_analysis.py` | 406 | Enhancement analysis runner |

---

## 3. JavaScript Files

### Application JS (non-vendor)

| File | Size (bytes) | Purpose |
|------|-------------:|---------|
| `app.js` | 614,556 | Main application controller, event handling, UI orchestration |
| `features/roles.js` | 455,373 | Roles module IIFE: detectDeliverable, suggestRoleType, role management |
| `help-docs.js` | 434,105 | Help documentation content (65 sections of inline HTML) |
| `roles-tabs-fix.js` | 215,508 | Roles Studio tab rendering, export/share/import handlers |
| `features/data-explorer.js` | 165,709 | Data Explorer drill-down modal with multi-view analysis |
| `roles-dictionary-fix.js` | 139,376 | Dictionary tab complete IIFE rewrite, DictState, card/table views |
| `features/statement-history.js` | 123,297 | Statement History: overview, document viewer, compare viewer |
| `features/role-source-viewer.js` | 103,122 | Source viewer modal with function tags |
| `function-tags.js` | 98,050 | Function tag management UI (categories, assignment, charts) |
| `features/hyperlink-validator.js` | 92,564 | HV frontend: handleRescan, domain filter, stat tiles, status filters |
| `ui/renderers.js` | 67,813 | UI rendering functions (results, tables, cards) |
| `features/hyperlink-validator-state.js` | 65,488 | HV state IIFE: setLocalResults, generateLocalSummary, filters |
| `features/metrics-analytics.js` | 63,280 | Metrics Command Center: 4-tab modal with charts and heatmap |
| `features/hyperlink-visualizations.js` | 61,545 | HV D3.js visualizations (treemap, sunburst, network) |
| `ui/events.js` | 55,674 | UI event handlers and delegation |
| `features/cinematic-progress.js` | 55,253 | Cinematic scan progress animations |
| `features/fix-assistant-state.js` | 49,075 | Fix Assistant state management |
| `features/landing-page.js` | 48,544 | Landing page: 3x3 tool grid, particle canvas, metric cards |
| `features/doc-compare.js` | 47,659 | Document comparison UI |
| `history-fixes.js` | 44,965 | Scan history UI patches and nav handlers |
| `features/hv-cinematic-progress.js` | 39,137 | HV-specific cinematic progress overlay |
| `features/portfolio.js` | 38,602 | Portfolio batch review UI |
| `features/link-history.js` | 35,078 | Link validation history panel |
| `presets_visualizations.js` | 34,428 | Style preset radar/comparison charts |
| `features/statement-review-mode.js` | 32,341 | Statement review mode with adjudication |
| `features/document-viewer.js` | 26,644 | Document viewer (split-panel, highlight-to-create) |
| `features/families.js` | 26,385 | Role families/groups management |
| `ui/modals.js` | 25,549 | Modal dialog management |
| `features/doc-compare-state.js` | 24,064 | Document comparison state management |
| `features/cinematic-loader.js` | 21,600 | Cinematic loader animation controller |
| `ui/state.js` | 19,419 | Global UI state management |
| `features/preview-modes.js` | 18,716 | Document preview modes (annotated, clean, tracked) |
| `features/sow-generator.js` | 17,237 | SOW generator frontend |
| `ui/storage.js` | 17,043 | Local storage management |
| `features/minimap.js` | 15,711 | Document minimap navigation |
| `help-content.js` | 15,583 | Help panel content (legacy) |
| `update-functions.js` | 15,453 | Update manager frontend |
| `api/client.js` | 14,781 | API client wrapper with CSRF, error handling |
| `features/scan-progress-dashboard.js` | 14,382 | Step-by-step scan progress checklist overlay |
| `features/triage.js` | 14,352 | Issue triage and prioritization UI |
| `features/style-presets.js` | 14,116 | Style guide preset selection UI |
| `utils/dom.js` | 12,565 | DOM utility functions |
| `features/frontend-logger.js` | 12,446 | Frontend logging and diagnostics capture |
| `features/graph-export.js` | 12,238 | Role graph SVG/PNG export |
| `features/console-capture.js` | 11,022 | Browser console capture for diagnostics |
| `run-state-fixes.js` | 9,633 | Review run state management patches |
| `button-fixes.js` | 9,290 | Button behavior fixes and patches |
| `features/landing-dashboard.js` | 9,178 | Landing dashboard (dead code, replaced by landing-page.js) |
| `roles-export-fix.js` | 8,971 | Roles export dropdown handler fixes |
| `features/molten-progress.js` | 8,554 | Molten-style progress animation |
| `features/a11y-manager.js` | 8,192 | Accessibility manager (ARIA, focus trapping, keyboard nav) |
| `features/learner-client.js` | 7,898 | Adaptive learner frontend client |
| `features/sound-effects.js` | 7,261 | UI sound effects (optional) |
| `features/report-client.js` | 6,463 | PDF report generation frontend client |
| `adjudication-lookup.js` | 5,995 | Global adjudication badge utility (AEGIS.AdjudicationLookup) |
| `twr-loader.js` | 5,043 | App initialization and dependency loader |
| `statement-review-lookup.js` | 4,353 | Statement review badge utility |
| `features/pdf-viewer.js` | 3,567 | PDF.js viewer IIFE (canvas rendering at 1.5x) |

### Vendor Libraries

| File | Size (bytes) | Library |
|------|-------------:|---------|
| `vendor/lucide.min.js` | 329,951 | Lucide Icons |
| `vendor/lottie.min.js` | 305,543 | Lottie Animation |
| `vendor/d3.v7.min.js` | 279,706 | D3.js v7 |
| `vendor/chart.min.js` | 205,399 | Chart.js |
| `vendor/gsap.min.js` | 72,214 | GSAP Animation |
| `vendor/Sortable.min.js` | 44,136 | Sortable.js Drag & Drop |
| `vendor/pdfjs/` | -- | PDF.js v4.2.67 ESM |

---

## 4. CSS Files

| File | Size (bytes) |
|------|-------------:|
| `features/roles-studio.css` | 273,745 |
| `components.css` | 169,116 |
| `features/fix-assistant.css` | 115,051 |
| `layout.css` | 68,255 |
| `features/data-explorer.css` | 64,356 |
| `features/hyperlink-validator.css` | 62,270 |
| `features/hyperlink-enhanced.css` | 53,338 |
| `features/statement-history.css` | 46,619 |
| `charts.css` | 38,857 |
| `features/statement-forge.css` | 31,928 |
| `features/doc-compare.css` | 30,884 |
| `features/portfolio.css` | 27,263 |
| `dark-mode.css` | 25,248 |
| `features/metrics-analytics.css` | 23,067 |
| `modals.css` | 22,401 |
| `features/hv-cinematic-progress.css` | 19,834 |
| `base.css` | 19,252 |
| `features/landing-page.css` | 18,786 |
| `features/cinematic-progress.css` | 17,630 |
| `features/cinematic-loader.css` | 15,380 |
| `features/link-history.css` | 13,831 |
| `features/molten-progress.css` | 11,869 |
| `features/sow-generator.css` | 11,574 |
| `features/landing-dashboard.css` | 6,460 |
| `features/scan-progress-dashboard.css` | 6,225 |
| `style.css` | 5,947 |
| `features/scan-history.css` | 3,558 |
| **Total** | **~1,182,734** |

---

## 5. API Endpoints

### 5a. app.py Routes (164 routes)

#### Core / System

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve SPA (index.html) |
| GET | `/loader-demo` | Loader animation demo page |
| GET | `/favicon.ico` | Favicon |
| GET | `/static/css/<path>` | CSS asset serving |
| GET | `/static/js/<path>` | JS asset serving |
| GET | `/static/js/vendor/<path>` | Vendor JS serving |
| GET | `/static/images/<path>` | Image asset serving |
| GET | `/api/csrf-token` | Get CSRF token |
| GET | `/api/version` | Version info |
| GET | `/api/health` | Health check |
| GET | `/api/ready` | Readiness check |
| GET | `/api/health/assets` | Asset health check |
| POST | `/api/clear-session` | Clear session data |

#### Document Upload & Review

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/upload` | Upload single document |
| POST | `/api/upload/batch` | Upload batch of documents |
| GET | `/api/dev/load-test-file` | Dev: load test file |
| GET | `/api/dev/temp/<filename>` | Dev: serve temp file |
| POST | `/api/review` | Run document review (synchronous) |
| POST | `/api/review/single` | Single-file review |
| POST | `/api/review/batch` | Batch review |
| POST | `/api/review/start` | Start async review job |
| GET | `/api/review/result/<job_id>` | Get async review result |

#### Results & Filtering

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/filter` | Filter review results |
| POST | `/api/select` | Select specific results |
| POST | `/api/export` | Export results (DOCX) |
| POST | `/api/export/csv` | Export results (CSV) |
| POST | `/api/export/xlsx` | Export results (XLSX) |

#### Configuration

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/api/config` | Get/set configuration |
| GET | `/api/presets` | List style presets |
| GET | `/api/presets/<name>` | Get preset details |
| POST | `/api/presets/<name>/apply` | Apply preset |
| POST | `/api/auto-fix/preview` | Preview auto-fix results |
| GET/POST | `/api/config/acronyms` | Get/set acronym config |
| GET/POST | `/api/config/hyperlinks` | Get/set hyperlink config |
| GET/POST | `/api/config/sharing` | Get/set sharing config |
| POST | `/api/config/sharing/test` | Test sharing config |

#### NLP

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/nlp/status` | NLP system status |
| GET | `/api/nlp/checkers` | List available NLP checkers |
| GET/POST | `/api/nlp/config` | Get/set NLP configuration |

#### Analyzers

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/analyzers/status` | Analyzer status |
| POST | `/api/analyzers/semantic/similar` | Find similar text |
| POST | `/api/analyzers/acronyms/extract` | Extract acronyms |
| POST | `/api/analyzers/statistics` | Text statistics |
| POST | `/api/analyzers/lint` | Prose lint |

#### Extraction & Docling

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/docling/status` | Docling availability status |
| GET | `/api/extraction/capabilities` | Extraction capabilities |

#### Hyperlink Health (legacy)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hyperlink-health/status` | HH status |
| POST | `/api/hyperlink-health/validate` | Validate hyperlinks |
| GET | `/api/hyperlink-health/export/<format>` | Export results |
| POST | `/api/hyperlink-health/comments` | Add comments |
| GET | `/api/hyperlink-health/comments/download` | Download comments |

#### Jobs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/job/status` | Current job status |
| GET | `/api/job/<job_id>` | Get job by ID |
| POST | `/api/job/<job_id>/cancel` | Cancel job |
| GET | `/api/job/list` | List all jobs |

#### Scan History

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/scan-history` | List scans |
| DELETE | `/api/scan-history/<scan_id>` | Delete scan |
| GET | `/api/scan-history/document/<doc_id>/roles` | Roles for document |
| GET | `/api/scan-history/stats` | Scan statistics |
| POST | `/api/scan-history/clear` | Clear history |
| GET | `/api/scan-history/document-text` | Get document text |
| GET | `/api/scan-history/document-file` | Get document file |
| POST | `/api/scan-history/<scan_id>/recall` | Recall scan results |

#### Statements

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/scan-history/statements/search` | Cross-scan search |
| PUT | `/api/scan-history/statements/batch` | Batch update |
| PUT | `/api/scan-history/statements/<id>/review` | Review single statement |
| PUT | `/api/scan-history/statements/batch-review` | Batch review statements |
| GET | `/api/scan-history/statements/review-stats` | Review statistics |
| GET | `/api/scan-history/statements/duplicates` | Find duplicates |
| POST | `/api/scan-history/statements/deduplicate` | Remove duplicates |

#### Roles

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/roles/extract` | Extract roles from document |
| GET | `/api/roles/export` | Export roles |
| GET | `/api/documents` | List documents |
| GET | `/api/roles/aggregated` | Aggregated roles across docs |
| GET | `/api/roles/context` | Role context data |
| GET | `/api/roles/matrix` | Role responsibility matrix |
| GET | `/api/roles/raci` | RACI matrix |
| POST | `/api/roles/verify` | Verify role |
| GET/POST | `/api/roles/extraction-mode` | Get/set extraction mode |
| GET | `/api/roles/graph` | Role relationship graph |
| GET | `/api/roles/<name>/statements` | Statements for role |
| PUT | `/api/roles/<name>/statements/bulk-reassign` | Bulk reassign role statements |

#### Adjudication

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/roles/adjudicate` | Adjudicate single role |
| POST | `/api/roles/rename` | Rename role |
| GET | `/api/roles/adjudication-status` | Adjudication status |
| POST | `/api/roles/auto-adjudicate` | Auto-classify roles |
| POST | `/api/roles/adjudicate/batch` | Batch adjudicate |
| GET | `/api/roles/adjudication-summary` | Summary stats |
| POST | `/api/roles/update-category` | Update role category |

#### Role Dictionary

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/roles/dictionary` | List dictionary roles |
| POST | `/api/roles/dictionary` | Add role to dictionary |
| PUT | `/api/roles/dictionary/<id>` | Update dictionary role |
| DELETE | `/api/roles/dictionary/<id>` | Delete dictionary role |
| POST | `/api/roles/dictionary/import` | Import roles |
| POST | `/api/roles/dictionary/seed` | Seed dictionary |
| POST | `/api/roles/dictionary/import-excel` | Import from Excel |
| GET | `/api/roles/dictionary/export` | Export dictionary |
| POST | `/api/roles/dictionary/import-sipoc` | Import SIPOC |
| GET | `/api/roles/dictionary/export-template` | Export import template |
| POST | `/api/roles/dictionary/clear-sipoc` | Clear SIPOC imports |
| GET | `/api/roles/dictionary/status` | Dictionary status |
| POST | `/api/roles/dictionary/export-master` | Export master JSON |
| POST | `/api/roles/dictionary/create-master` | Create master JSON |
| POST | `/api/roles/dictionary/sync` | Sync dictionary |
| GET | `/api/roles/dictionary/download-master` | Download master JSON |

#### Role Relationships & Hierarchy

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/roles/relationships` | List relationships |
| POST | `/api/roles/relationships` | Create relationship |
| POST | `/api/roles/relationships/delete` | Delete relationship |
| GET | `/api/roles/hierarchy` | Get hierarchy data |
| GET | `/api/roles/hierarchy/export-html` | Export hierarchy as HTML |

#### Role Sharing & Export

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/roles/adjudication/export-html` | Export kanban HTML |
| GET | `/api/roles/adjudication/export-pdf` | Export adjudication PDF |
| POST | `/api/roles/adjudication/import-preview` | Preview import |
| POST | `/api/roles/adjudication/import` | Import decisions |
| POST | `/api/roles/share/package` | Create .aegis-roles package |
| POST | `/api/roles/share/import-package` | Import package |

#### Function Categories & Tags

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/function-categories` | List categories |
| POST | `/api/function-categories` | Create category |
| PUT | `/api/function-categories/<code>` | Update category |
| DELETE | `/api/function-categories/<code>` | Delete category |
| GET | `/api/role-function-tags` | List tags |
| POST | `/api/role-function-tags` | Assign tag |
| DELETE | `/api/role-function-tags/<id>` | Remove tag |

#### Document Categories

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/document-category-types` | List category types |
| GET | `/api/document-categories` | List document categories |
| POST | `/api/document-categories` | Assign category |
| DELETE | `/api/document-categories/<id>` | Remove category |
| DELETE | `/api/document-categories/by-document/<name>` | Remove by document |
| POST | `/api/document-categories/auto-detect` | Auto-detect categories |

#### Role Required Actions

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/role-required-actions` | List required actions |
| POST | `/api/role-required-actions` | Create action |
| POST | `/api/role-required-actions/<id>/verify` | Verify action |
| DELETE | `/api/role-required-actions/<id>` | Delete action |
| POST | `/api/role-required-actions/extract` | Auto-extract actions |

#### Reports

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/roles/reports/by-function` | Report grouped by function |
| GET | `/api/roles/reports/by-document` | Report grouped by document |
| GET | `/api/roles/reports/by-owner` | Report grouped by owner |

#### SOW & Metrics

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/sow/data` | Get SOW data |
| POST | `/api/sow/generate` | Generate SOW HTML |
| GET | `/api/metrics/dashboard` | Metrics analytics data |

#### Adaptive Learner

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/learner/record` | Record decision |
| POST | `/api/learner/predict` | Predict action |
| GET | `/api/learner/patterns` | List patterns |
| POST | `/api/learner/patterns/clear` | Clear patterns |
| GET/POST/DELETE | `/api/learner/dictionary` | Custom dictionary CRUD |
| GET | `/api/learner/statistics` | Learner statistics |
| GET | `/api/learner/export` | Export learner data |
| POST | `/api/learner/import` | Import learner data |

#### Data Management

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/data/clear-roles` | Clear all roles |
| POST | `/api/data/clear-statements` | Clear all statements |
| POST | `/api/data/clear-learning` | Clear learning data |
| POST | `/api/data/recalculate-role-counts` | Recalculate counts |
| POST | `/api/data/cleanup-false-positives` | Remove false positives |
| POST | `/api/data/factory-reset` | Factory reset |
| GET | `/api/data/stats` | Database statistics |

#### Reports & Diagnostics

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/report/generate` | Generate PDF report |
| GET | `/api/diagnostics/logs` | Get diagnostic logs |
| GET | `/api/diagnostics/logs/<error_id>` | Get specific error log |

#### Scan Profiles

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/scan-profiles` | List profiles |
| POST | `/api/scan-profiles` | Create profile |
| DELETE | `/api/scan-profiles/<id>` | Delete profile |
| GET | `/api/scan-profiles/default` | Get default profile |

#### Score Trend

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/score-trend` | Score trend data |

### 5b. Blueprint Routes

#### api_extensions.py (prefix: `/api`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/capabilities` | System capabilities |
| POST | `/api/export/excel` | Export to Excel |
| POST | `/api/export/csv` | Export to CSV |
| POST | `/api/export/pdf` | Export to PDF |
| POST | `/api/export/json` | Export to JSON |
| POST | `/api/export/compliance-matrix` | Compliance matrix export |
| POST | `/api/roles/analyze` | Analyze roles |
| POST | `/api/roles/network` | Role network data |
| POST | `/api/roles/summary` | Role summary |
| GET | `/api/history/documents` | Document history |
| GET | `/api/history/document/<doc_id>` | Document detail |
| GET | `/api/history/trends/<doc_id>` | Document trends |
| POST | `/api/history/compare` | Compare history |
| POST | `/api/history/save` | Save history |
| POST | `/api/baseline/add` | Add baseline |
| POST | `/api/baseline/remove` | Remove baseline |
| GET | `/api/baseline/list/<doc_id>` | List baselines |
| POST | `/api/baseline/filter` | Filter baselines |
| GET | `/api/userconfig` | Get user config |
| GET | `/api/userconfig/<key>` | Get config key |
| POST | `/api/userconfig` | Set user config |
| GET | `/api/words/<list_type>` | Get word list |
| POST | `/api/words/<list_type>` | Add to word list |
| DELETE | `/api/words/<list_type>/<word>` | Remove from word list |
| POST | `/api/analytics/summary` | Analytics summary |
| POST | `/api/analytics/trends` | Analytics trends |
| GET | `/api/batch/status` | Batch job status |

#### document_compare/routes.py (prefix: `/api/compare`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/compare/documents` | List comparable documents |
| GET | `/api/compare/scans/<doc_id>` | List scans for document |
| POST | `/api/compare/diff` | Generate diff |
| GET | `/api/compare/issues/<old_id>/<new_id>` | Issue changes |
| GET | `/api/compare/status` | Compare module status |
| GET | `/api/compare/health` | Health check |

#### hyperlink_validator/routes.py (prefix: `/api/hyperlink-validator`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hyperlink-validator/health` | Health check |
| GET | `/api/hyperlink-validator/capabilities` | HV capabilities |
| POST | `/api/hyperlink-validator/validate` | Validate URLs |
| GET | `/api/hyperlink-validator/job/<job_id>` | Job status |
| POST | `/api/hyperlink-validator/cancel/<job_id>` | Cancel job |
| GET | `/api/hyperlink-validator/history` | Validation history |
| GET | `/api/hyperlink-validator/export/<job_id>` | Export results |
| POST | `/api/hyperlink-validator/clear-history` | Clear history |
| POST | `/api/hyperlink-validator/validate-link` | Validate single link |
| POST | `/api/hyperlink-validator/classify-link` | Classify link |
| POST | `/api/hyperlink-validator/check-typos` | Check URL typos |
| POST | `/api/hyperlink-validator/validate-docx` | Validate DOCX links |
| POST | `/api/hyperlink-validator/extract-docx` | Extract DOCX links |
| POST | `/api/hyperlink-validator/validate-excel` | Validate Excel links |
| POST | `/api/hyperlink-validator/extract-excel` | Extract Excel links |
| GET | `/api/hyperlink-validator/excel-capabilities` | Excel capabilities |
| GET | `/api/hyperlink-validator/exclusions` | List exclusions |
| POST | `/api/hyperlink-validator/exclusions` | Add exclusion |
| GET | `/api/hyperlink-validator/exclusions/<id>` | Get exclusion |
| PUT/PATCH | `/api/hyperlink-validator/exclusions/<id>` | Update exclusion |
| DELETE | `/api/hyperlink-validator/exclusions/<id>` | Delete exclusion |
| GET | `/api/hyperlink-validator/exclusions/stats` | Exclusion stats |
| GET | `/api/hyperlink-validator/history` | Link scan history |
| GET | `/api/hyperlink-validator/history/<scan_id>` | Scan detail |
| DELETE | `/api/hyperlink-validator/history/<scan_id>` | Delete scan |
| GET | `/api/hyperlink-validator/history/stats` | History stats |
| POST | `/api/hyperlink-validator/history/record` | Record scan |
| POST | `/api/hyperlink-validator/history/clear` | Clear history |
| GET | `/api/hyperlink-validator/rescan/capabilities` | Rescan (headless) capabilities |
| POST | `/api/hyperlink-validator/rescan` | Start headless rescan |
| POST | `/api/hyperlink-validator/rescan/job/<job_id>` | Rescan job status |
| GET | `/api/hyperlink-validator/export-highlighted/capabilities` | Highlight export capabilities |
| POST | `/api/hyperlink-validator/export-highlighted/docx` | Export highlighted DOCX |
| POST | `/api/hyperlink-validator/export-highlighted/excel` | Export highlighted Excel |

#### statement_forge/routes.py (prefix: `/api/statement-forge`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/statement-forge/extract-from-session` | Extract from active session |
| POST | `/api/statement-forge/extract` | Extract from document |
| GET | `/api/statement-forge/statements` | List statements |
| POST | `/api/statement-forge/statements` | Create statement |
| PUT | `/api/statement-forge/statements/<id>` | Update statement |
| DELETE | `/api/statement-forge/statements/<id>` | Delete statement |
| POST | `/api/statement-forge/statements/merge` | Merge statements |
| POST | `/api/statement-forge/statements/split` | Split statement |
| POST | `/api/statement-forge/statements/add` | Add statement |
| POST | `/api/statement-forge/statements/reorder` | Reorder statements |
| POST | `/api/statement-forge/export` | Export statements |
| POST | `/api/statement-forge/export/preview` | Preview export |
| GET | `/api/statement-forge/verbs` | List directive verbs |
| POST | `/api/statement-forge/detect-directive` | Detect directive |
| POST | `/api/statement-forge/clear` | Clear session |
| GET | `/api/statement-forge/health` | Health check |
| GET | `/api/statement-forge/availability` | Availability check |
| POST | `/api/statement-forge/map-to-roles` | Map statements to roles |
| GET | `/api/statement-forge/role-mapping-status` | Mapping status |
| GET | `/api/statement-forge/history/<doc_id>` | Statement history |
| GET | `/api/statement-forge/scan/<scan_id>` | Statements for scan |
| GET | `/api/statement-forge/trends/<doc_id>` | Statement trends |
| GET | `/api/statement-forge/compare/<id1>/<id2>` | Compare scans |
| PUT | `/api/statement-forge/scan/statements/<id>` | Update scan statement |
| GET | `/api/statement-forge/compare/<id1>/<id2>/export-csv` | Export diff CSV |
| GET | `/api/statement-forge/compare/<id1>/<id2>/export-pdf` | Export diff PDF |

#### portfolio/routes.py (prefix: `/api/portfolio`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/portfolio/batches` | List batches |
| GET | `/api/portfolio/batch/<batch_id>` | Batch detail |
| GET | `/api/portfolio/document/<scan_id>/preview` | Document preview |
| GET | `/api/portfolio/recent` | Recent documents |
| GET | `/api/portfolio/stats` | Portfolio stats |

**Total API endpoints: ~250+**

---

## 6. Database Schema

### 6a. scan_history.db (Primary - 226 MB)

17 tables total:

#### Core Tables

**scans** - Document scan records

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| document_id | INTEGER | FK |
| scan_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| options_json | TEXT | |
| issue_count | INTEGER | |
| score | INTEGER | |
| grade | TEXT | |
| word_count | INTEGER | |
| paragraph_count | INTEGER | |
| results_json | TEXT | (stores full results + html_preview) |

**documents** - Document metadata

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| filename | TEXT | NOT NULL |
| filepath | TEXT | |
| file_hash | TEXT | |
| first_scan | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| last_scan | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| scan_count | INTEGER | DEFAULT 1 |
| word_count | INTEGER | |
| paragraph_count | INTEGER | |

**scan_statements** - Extracted statements

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| scan_id | INTEGER | NOT NULL |
| document_id | INTEGER | NOT NULL |
| statement_number | TEXT | |
| title | TEXT | |
| description | TEXT | NOT NULL DEFAULT '' |
| level | INTEGER | DEFAULT 1 |
| role | TEXT | DEFAULT '' |
| directive | TEXT | DEFAULT '' |
| section | TEXT | DEFAULT '' |
| is_header | INTEGER | DEFAULT 0 |
| notes_json | TEXT | |
| position_index | INTEGER | DEFAULT 0 |
| review_status | TEXT | DEFAULT 'pending' |
| confirmed | INTEGER | DEFAULT 0 |
| reviewed_by | TEXT | |
| reviewed_at | TIMESTAMP | |
| fingerprint | TEXT | |

#### Role Tables

**role_dictionary** - Adjudicated roles (master list)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| role_name | TEXT | NOT NULL |
| normalized_name | TEXT | NOT NULL |
| aliases | TEXT | |
| category | TEXT | DEFAULT 'Custom' |
| source | TEXT | NOT NULL |
| source_document | TEXT | |
| description | TEXT | |
| is_active | INTEGER | DEFAULT 1 |
| is_deliverable | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| created_by | TEXT | DEFAULT 'user' |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_by | TEXT | |
| notes | TEXT | |
| tracings | TEXT | |
| role_type | TEXT | |
| role_disposition | TEXT | |
| org_group | TEXT | |
| hierarchy_level | TEXT | |
| baselined | INTEGER | DEFAULT 0 |

**roles** - Discovered roles (aggregated)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| role_name | TEXT | |
| normalized_name | TEXT | |
| first_seen | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| document_count | INTEGER | DEFAULT 1 |
| total_mentions | INTEGER | DEFAULT 1 |
| description | TEXT | |
| is_deliverable | INTEGER | DEFAULT 0 |
| category | TEXT | |
| role_source | TEXT | DEFAULT 'discovered' |

**function_categories** - Hierarchical function codes

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| code | TEXT | NOT NULL |
| name | TEXT | NOT NULL |
| description | TEXT | |
| parent_code | TEXT | |
| sort_order | INTEGER | DEFAULT 0 |
| is_active | INTEGER | DEFAULT 1 |
| color | TEXT | DEFAULT '#3b82f6' |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**role_function_tags** - M:N role-to-function mapping

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| role_id | INTEGER | |
| role_name | TEXT | |
| function_code | TEXT | NOT NULL |
| assigned_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| assigned_by | TEXT | DEFAULT 'system' |

**role_relationships** - Role inheritance/relationship edges

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| source_role_id | INTEGER | |
| source_role_name | TEXT | NOT NULL |
| target_role_id | INTEGER | |
| target_role_name | TEXT | NOT NULL |
| relationship_type | TEXT | DEFAULT 'supervises' |
| source_context | TEXT | |
| import_source | TEXT | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**document_roles** - Document-to-role mapping

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| document_id | INTEGER | |
| role_id | INTEGER | |
| mention_count | INTEGER | DEFAULT 1 |
| responsibilities_json | TEXT | |
| last_updated | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

#### Supporting Tables

**role_required_actions** - Actions required by roles

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| role_id | INTEGER | |
| role_name | TEXT | NOT NULL |
| statement_text | TEXT | NOT NULL |
| statement_type | TEXT | DEFAULT 'requirement' |
| source_document_id | INTEGER | |
| source_document_name | TEXT | |
| source_location | TEXT | |
| confidence_score | REAL | DEFAULT 1.0 |
| is_verified | INTEGER | DEFAULT 0 |
| verified_by | TEXT | |
| verified_at | TIMESTAMP | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**document_categories** - Document classification

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| document_id | INTEGER | |
| document_name | TEXT | |
| category_type | TEXT | NOT NULL |
| function_code | TEXT | |
| doc_number | TEXT | |
| document_owner | TEXT | |
| auto_detected | INTEGER | DEFAULT 0 |
| assigned_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| assigned_by | TEXT | DEFAULT 'system' |

**document_category_types** - Category type definitions

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| name | TEXT | NOT NULL |
| description | TEXT | |
| doc_number_patterns | TEXT | |
| is_active | INTEGER | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**issue_changes** - Scan-to-scan issue tracking

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| document_id | INTEGER | |
| scan_id | INTEGER | |
| previous_scan_id | INTEGER | |
| issues_added | INTEGER | DEFAULT 0 |
| issues_removed | INTEGER | DEFAULT 0 |
| issues_unchanged | INTEGER | DEFAULT 0 |
| change_summary_json | TEXT | |

**link_scan_history** - Hyperlink validation history

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| scan_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| source_type | TEXT | DEFAULT 'paste' |
| source_name | TEXT | |
| total_urls | INTEGER | DEFAULT 0 |
| working / broken / redirect / timeout / blocked / unknown / excluded | INTEGER | DEFAULT 0 |
| validation_mode | TEXT | DEFAULT 'validator' |
| scan_depth | TEXT | DEFAULT 'standard' |
| duration_ms | INTEGER | DEFAULT 0 |
| results_json | TEXT | |

**hyperlink_exclusions** - URL exclusion rules

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| pattern | TEXT | NOT NULL |
| match_type | TEXT | DEFAULT 'contains' |
| reason | TEXT | |
| treat_as_valid | INTEGER | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| created_by | TEXT | DEFAULT 'user' |
| is_active | INTEGER | DEFAULT 1 |
| hit_count | INTEGER | DEFAULT 0 |
| last_hit | TIMESTAMP | |

**scan_profiles** - Saved scan configurations

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| name | TEXT | NOT NULL |
| description | TEXT | |
| options_json | TEXT | NOT NULL |
| is_default | INTEGER | DEFAULT 0 |
| created | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| last_used | TIMESTAMP | |

### 6b. data/techwriter.db (Legacy - 220 KB)

8 tables: `documents`, `analysis_history`, `issues`, `roles`, `role_relationships`, `configurations`, `custom_words`, `issue_baselines`

### 6c. data/decision_patterns.db

3 tables: `decisions`, `patterns`, `user_dictionary`

### 6d. data/adaptive_learning.db

7 tables: `decisions`, `patterns`, `custom_dictionary`, `acronym_patterns`, `context_patterns`, `role_patterns`, `user_preferences`

---

## 7. External Service Calls

### Outbound HTTP Requests

| File | Library | Target | Purpose |
|------|---------|--------|---------|
| `comprehensive_hyperlink_checker.py` | `requests` | User-provided URLs | HEAD/GET validation of document hyperlinks |
| `hyperlink_health.py` | `requests` | User-provided URLs | HEAD request for hyperlink health monitoring |
| `hyperlink_validator/validator.py` | `requests` (via session) | User-provided URLs | Session-based GET validation with connection pooling |
| `hyperlink_validator/headless_validator.py` | `playwright` | User-provided URLs | Chromium headless browser for bot-blocked URLs |
| `setup_tesseract.py` | `urllib.request` | Tesseract download URL | Download Tesseract OCR installer |
| `load_test_docs.py` | `requests` | `localhost:5050` | Test utility: upload/review against local server |
| `test_scan_analysis.py` | `requests` | `localhost:5050` | Test utility: scan analysis against local server |

### Key Notes on External Calls

- **No cloud AI/ML calls**: All analysis runs locally (no OpenAI, no external NLP APIs)
- **No telemetry or analytics**: No usage data sent externally
- **LanguageTool**: Uses `language_tool_python` library which runs a local JVM instance (not an external API)
- **spaCy**: Local model (`en_core_web_sm` or larger), no external calls
- **Docling**: Runs as local subprocess, no external service
- **All outbound HTTP**: Limited to validating user-provided URLs (hyperlink checking) and one-time Tesseract download

---

## Summary Statistics

| Category | Count |
|----------|------:|
| Python files (top-level) | 87 |
| Python files (packages) | 42 |
| JavaScript files (app) | 57 |
| JavaScript files (vendor) | 7 |
| CSS files | 27 |
| API endpoints (total) | ~250+ |
| Database tables (scan_history.db) | 17 |
| Database tables (all DBs) | 35 |
| Total Python LOC (top-level, estimated) | ~78,000 |
| Total JS size (non-vendor) | ~3.6 MB |
| Total CSS size | ~1.2 MB |
| Primary DB size | 226 MB |
