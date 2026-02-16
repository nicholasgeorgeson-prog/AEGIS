# AEGIS Changelog

All notable changes to AEGIS (Aerospace Engineering Governance & Inspection System) are documented in this file.

---

## [5.1.0] - 2026-02-16 - Security Hardening + Accessibility + Print Support

### Security & CSRF Protection
- **@require_csrf decorator** added to 9 unprotected POST routes (SOW generation, presets, analyzers, diagnostics email)
- **Fresh CSRF token pattern** implemented in 18+ JavaScript functions using `_getFreshCsrf()` helper
- **Data management handlers** fixed to use fresh tokens for clear operations (statements, roles, learning, factory reset)
- **Popup blocker vulnerability** fixed in statement history exports (replaced window.open after await with iframe pattern)

### Review Engine Quality Improvements
- **spaCy singleton pattern** fixed for shared model instances (performance improvement, prevents multiple model loads)
- **Issue deduplication key** improved from 50 to 80 characters (includes rule_id for better uniqueness)
- **18 aerospace adjectival participles** added to passive voice whitelist (improved accuracy for technical docs)
- **All 83 checkers verified** with 14 new UI toggles in Settings → Document Profiles

### Accessibility (WCAG 2.1 Level A)
- **134 aria-label attributes** added across all UI elements
- **28 modals** updated with `role="dialog"` and `aria-modal="true"`
- **Tab navigation systems** enhanced with `role="tablist"`, `role="tab"`, `role="tabpanel"`
- **116 decorative icons** marked with `aria-hidden="true"`

### Print Support
- **New print.css stylesheet** for optimized document printing
- **Non-printable elements** hidden (sidebar, toolbar, toasts, modals)
- **Tables and typography** optimized for print with proper spacing and page breaks
- **Link URLs displayed** after links for reference in printed documents

### UI/UX Improvements
- **Folder browse button** now opens native OS folder picker via backend API (instead of file upload dialog)
- **Dropdown z-index conflict** fixed with toast notifications (raised dropdowns appropriately)
- **Dark mode overrides** added for modal radio card components
- **Statement history exports** use fresh CSRF to avoid popup blocker

### Windows Offline Installation
- **195 Windows x64 wheel files** bundled for air-gapped installation
- **Dependencies included**: numpy, pandas, scipy, scikit-learn, spaCy, docling, openpyxl, flask, etc.
- **torch (139MB)** available via GitHub Release download link
- **download_win_wheels.py** script for connected Windows environments (auto-downloads all wheels)
- **install_offline.bat** updated to support both wheel directories and verify installation

### Critical Bug Fixes
- **Landing page 0 roles** fixed with fallback from role_dictionary to roles table
- **Source document not loading** when clicking roles in Adjudication view
- **Updater spinning forever** fixed with 15s timeout and AbortController
- **Diagnostic email export** fixed (changed from GET to POST with fresh CSRF)
- **Version display stale** after update fixed (removed import-time caching)

---

## [5.0.0] - 2026-02-15 - Multiprocessing Architecture + Role Extraction Overhaul

### Multiprocessing Architecture
- **ARCHITECTURE**: Review jobs now run in separate PROCESS (multiprocessing.Process) instead of threading.Thread
- **ARCHITECTURE**: Flask server stays fully responsive during large document analysis (separate GIL)
- **ARCHITECTURE**: Worker process crash isolation — if review crashes, Flask keeps running
- **ARCHITECTURE**: Per-document timeout (600s default) with graceful process termination
- **ARCHITECTURE**: Progress updates via multiprocessing.Queue with monitor thread bridge pattern
- **ARCHITECTURE**: Results written to temp JSON file (handles large documents without queue limits)
- **ARCHITECTURE**: Legacy threading fallback if multiprocessing unavailable

### Role Extraction v3.5.0
- **FIX**: Role extraction 'Validation' false positive — single-word variants no longer verify compound roles
- **FIX**: Removed 'nasa' and 'government' from KNOWN_ROLES (moved to ORGANIZATION_ENTITIES filter)
- **FIX**: Removed duplicate role entries (contracting officer, contractor, technical authority, government)
- **FIX**: Discovery mode now filters organization entities, low-confidence roles, and stopword roles
- **FIX**: PDF multi-column layout detection with extraction quality warning
- **NEW**: ORGANIZATION_ENTITIES filter set — prevents organizations from being extracted as roles
- **NEW**: 30+ missing aerospace roles added (technical fellow, mission systems engineer, failure review board, etc.)
- **NEW**: 50+ expanded SINGLE_WORD_EXCLUSIONS preventing common English words from extraction
- **NEW**: Confidence threshold filter (< 0.4) removes low-quality role extractions

### Statement Forge Enhancements
- **NEW**: Document type classification in Statement Forge export (requirements/guidance/descriptive/informational)
- **NEW**: Document classification detail text explaining directive distribution
- **NEW**: Column layout detection in PDF extraction with quality warnings

### Quality Improvements
- **IMPROVED**: Role extractor v3.5.0 with 3-layer post-verification filtering
- **IMPROVED**: STRICT mode also skips organization entities
- **IMPROVED**: pymupdf4llm extraction uses write_images=False for faster processing
- **TESTED**: Full NASA SE Handbook (297 pages) — role false positives reduced from 44% to <5%

### Windows Packaging & Distribution
- **NEW**: Complete Windows installer package with embedded Python 3.10.11
- **NEW**: 126 pre-built Windows AMD64 wheel files for offline installation
- **NEW**: install_aegis.bat — 8-step installation wizard with folder picker
- **NEW**: Start_AEGIS.bat and Stop_AEGIS.bat launcher scripts
- **NEW**: restart_aegis.bat for quick server restart on Windows
- **NEW**: GitHub Release-based distribution with download scripts
- **NEW**: Comprehensive user guides (interactive HTML + DOCX)

---

## [4.9.9] - 2026-02-15 - Statement Source Viewer + SOW & Error Handling Improvements

### Statement Source Viewer with Highlight-to-Select
- **FEATURE**: New Statement Source Viewer modal with two-panel layout (document text + details)
- **FEATURE**: Click any text in document to create inline statement without leaving viewer
- **FEATURE**: Highlight-to-select editing — select text range and inline save as new statement
- **NEW**: Source viewer integrates Statement Forge history context
- **NEW**: Keyboard shortcuts for navigation (J/K or arrows for statements)
- **IMPROVED**: Statement editing now preserves document context and character offsets

### SOW Generator Error Handling
- **FIX**: SOW generation 500 error — missing `timezone` import in datetime operations
- **FIX**: Added `from datetime import datetime, timezone` to all modules using `timezone.utc`
- **FIX**: SOW template generation now properly handles current date/time with UTC timezone
- **NEW**: `/api/sow/generate` endpoint error response now returns structured `{success, error}` format
- **IMPROVED**: Better validation of template parameters before SOW generation

### Document Compare Auto-Picker
- **FIX**: Document Compare modal now auto-selects oldest doc on left, newest on right when opened
- **FIX**: Auto-picker triggers immediate comparison without requiring manual selection
- **FIX**: Falls back to oldest/newest pair when opened without explicit docId parameter
- **NEW**: Auto-comparison initialization in compare-viewer.js `initializeComparison()`
- **IMPROVED**: Consistent behavior across all entry points (sidebar, landing tile, URL)

### Error Handling Improvements Across All Modules
- **FIX**: `api-utils.js` error responses now include proper message extraction
- **FIX**: Template files now correctly extract `.error.message` from structured error objects
- **FIX**: Toast notifications show meaningful error text instead of "[object Object]"
- **NEW**: `getErrorMessage(errorObj)` utility function for safe message extraction
- **IMPROVED**: All API error handlers follow consistent response format: `{success: false, error: {message, code, details}}`

### Production Logging & Stability
- **IMPROVED**: Session logging now tracks user interactions with correlation IDs
- **IMPROVED**: API response logging includes timing metadata
- **NEW**: Frontend error tracking with automatic backend sync via `/api/diagnostics/log`

### Settings Persistence
- **IMPROVED**: Document profile settings now persist across server restarts
- **IMPROVED**: User preferences cached in localStorage with server-side backup
- **FIX**: Settings save operation now includes dirty-state tracking with visual feedback

### Windows Compatibility Fixes
- **FIX**: File permission operations (chmod) now skipped on Windows platforms
- **FIX**: Platform detection using `os.name == 'nt'` for Windows-specific code paths
- **NEW**: Windows-specific environment variable handling in config loader
- **IMPROVED**: Cross-platform path handling with `pathlib.Path` throughout codebase

### Mass Statement Review Enhancements
- **IMPROVED**: Particle effects transparency adjusted for better visibility over dark backgrounds
- **IMPROVED**: Review list rendering performance for 100+ statements
- **NEW**: Batch review progress indicator showing processed/total count

---

## [4.7.0] - 2026-02-14 - Database Access Layer Refactoring + Bug Fixes

### Database Access Layer Refactoring
- **REFACTOR**: Replaced **99 scattered `sqlite3.connect()` calls** across 7 files with a unified `db_connection()` context manager pattern — the #1 reliability risk identified in the 13-phase enterprise audit
- **NEW**: `db_connection(db_path)` context manager in `scan_history.py` — auto-commits on success, rolls back on exception, always closes connection, sets `row_factory=sqlite3.Row` and `PRAGMA journal_mode=WAL`
- **NEW**: `ScanHistoryDB.connection()` convenience method wrapping `db_connection(self.db_path)`
- **NEW**: `HyperlinkValidatorStorage.connection()` method with its own local `db_connection` context manager (avoids circular import)

### Files Migrated
- **`scan_history.py`** — 23 calls migrated to `self.connection()`
- **`app.py`** — 49 calls migrated to `db.connection()` or standalone `db_connection(path)`
- **`hyperlink_validator/storage.py`** — 17 calls migrated to `self.connection()`
- **`document_compare/routes.py`** — 6 calls migrated with `try/except ImportError` fallback pattern
- **`role_extractor_v3.py`** — 2 calls migrated with local `_db_conn` context manager
- **`update_manager.py`** — 1 call migrated via imported `db_connection`
- **`diagnostic_export.py`** — 1 call migrated with local `_db_conn` context manager

### Reliability Improvements
- **FIX**: ~60% of DB calls lacked proper exception handling — now all use try/except with automatic rollback
- **FIX**: ~65% of DB calls risked connection leaks (no `finally: conn.close()`) — context manager guarantees cleanup
- **FIX**: Removed decompiler artifact `__import__('sqlite3').connect()` pattern discovered in app.py
- **IMPROVED**: WAL journal mode now applied uniformly via context manager (was inconsistent across files)
- **IMPROVED**: All database operations have consistent error handling and automatic cleanup

### Bug Fixes (10 decompiler recovery fixes)
- **FIX**: Scan history missing `statement_count` field in `get_scan_history()` response
- **FIX**: Document compare missing `compare_scan_statements()` method (lost in decompiler recovery)
- **FIX**: Heatmap flickering — switched from `display:none` to `visibility:hidden` for smooth transitions
- **FIX**: Graph layout buttons missing event listeners after bytecode recovery
- **FIX**: Generate reports buttons not working after bytecode recovery
- **FIX**: RACI matrix and module hover flickering caused by `transition:all` on cards
- **FIX**: Role-Doc Matrix Excel export was producing CSV instead of XLSX
- **FIX**: CSRF header typo in `roles.js` and `role-source-viewer.js` — `X-CSRFToken` corrected to `X-CSRF-Token` (3 occurrences)

---

## [4.6.2] - 2026-02-13 - Hyperlink Validator Enhancements

### Deep Validate (Headless Browser Rescan)
- **FEATURE**: Deep Validate now fully functional — headless browser rescan results merge back into the UI, updating stat tiles, domain filter, visualizations, and result table in real time
- **FIX**: Rescan results were never merged back into state — `handleRescan()` had a `// TODO: Merge results` placeholder since v3.0.124 that was never implemented
- **FIX**: Rescan eligibility expanded from 3 statuses (BLOCKED, TIMEOUT, DNSFAILED) to 5 (adds AUTH_REQUIRED, SSLERROR)
- **FIX**: Rescan section was missing from non-Excel validation flow — `renderSummary()` now also shows/hides the Deep Validate button
- **NEW**: `RESCAN_ELIGIBLE_STATUSES` constant and `_updateRescanSection()` helper for dynamic button visibility
- **IMPROVED**: Renamed from "Rescan Blocked" to "Deep Validate" with `scan-search` icon and purple accent styling
- **IMPROVED**: Recovered URLs preserve all Excel-specific fields (sheet_name, cell_address, display_text, link_source, context)
- **IMPROVED**: Domain filter repopulates after rescan to reflect recovered URL domain changes

### Domain Filter & Clickable Stats
- **FEATURE**: Domain Filter Dropdown — searchable dropdown filters results by specific domain with clear button
- **FEATURE**: Clickable Stat Tiles — click any summary stat card (Excellent, Broken, Blocked, Timeout, etc.) to filter results to that status category with gold active indicator

### Export & Exclusion Fixes
- **FIX**: Export Highlighted button — ArrayBuffer backup ensures DOCX export works even when original file blob is unavailable
- **FIX**: Exclusion persistence — exclusions created from result row context menus now save to the database via API, surviving sessions
- **FIX**: Stat count accuracy — summary counts correctly reflect merged rescan results after deep validation

### History Panel Layout Fix
- **FIX**: History panel compressing HV layout on wide displays (2500px+ viewports) — `translateX(100%)` was insufficient to push the 280px panel outside the parent boundary. Fixed by using `display: none` / `visibility: hidden` when closed, `display: flex` / `visibility: visible` when open

### Status Filtering
- **NEW**: Status filter pills — click status badges in result rows to filter by that status type
- **IMPROVED**: Active stat tile shows gold border + checkmark indicator, deselects on second click

---

## [4.6.1] - 2026-02-13 - Metrics & Analytics Command Center + Critical Bug Fixes

### Metrics & Analytics Command Center
- **FEATURE**: Standalone modal with 4-tab layout (Overview, Quality, Roles, Documents) accessible from Landing Page and nav bar
- **NEW**: Overview tab — hero stat cards, quality trend line chart, score distribution, severity breakdown doughnut, scan activity heatmap
- **NEW**: Quality tab — score distribution bar chart, issue category radar, top issues table
- **NEW**: Roles tab — role frequency chart, deliverables vs non-deliverables comparison
- **NEW**: Documents tab — per-document score history, detail drill-down panels
- **NEW**: Scan activity heatmap — GitHub-style SVG grid with custom HTML tooltip, hover overlay rect
- **NEW**: Drill-down panels on hero stats and document cards for detailed breakdowns
- **NEW**: Dark mode support across all charts (Chart.js + D3.js), tooltip styling

### Critical Bug Fixes
- **FIX**: Scan cancel button not working — `window.cancelCurrentJob` was never exposed as a global function, so the Scan Progress Dashboard's cancel button did nothing and the scan continued running in the background
- **FIX**: Scan Progress Dashboard cancel leaves UI hung — loading overlay and progress dashboard now properly cleaned up on cancel (both overlay and polling loop terminate)
- **FIX**: Scan History and Roles Studio showing doc review background instead of dashboard — modals now keep the landing page dashboard visible behind their backdrop
- **FIX**: Landing page tiles hiding dashboard when opening modals — stopped calling `hide()` for forge/roles/history tiles; they now just stop the particle loop and open the modal on top
- **FIX**: Nav bar module buttons not restoring dashboard background — history/roles/forge nav buttons now show the landing page when not already active
- **FIX**: Heatmap hover flicker — SVG overlay rect was appended before cells (rendered behind them); moved to after cells so it renders on top. Removed CSS `opacity transition` on tooltip that caused rapid show/hide flicker on 12px cells

### Improvements
- **IMPROVED**: Heatmap tooltip shows instantly (direct opacity manipulation, no CSS transition)
- **IMPROVED**: Scan cancel cleanup is comprehensive — destroys progress dashboard, resets loading tracker, clears job state and global cancel hook
- **IMPROVED**: Cancel handler works from both the Scan Progress Dashboard cancel button and the loading overlay cancel button

### Backend
- **NEW**: `GET /api/metrics/analytics` — aggregated analytics data from scan history for the Metrics & Analytics Command Center

---

## [4.6.0] - 2026-02-12 - Statement Lifecycle, Bug Fixes & Settings Overhaul

### Statement Lifecycle Management
- **FEATURE**: Statement fingerprinting and deduplication on rescan — unchanged statements tagged, new ones flagged as pending
- **FEATURE**: Statement review workflow — approve/reject individual or bulk statements with status badges (Pending/Reviewed/Rejected/Unchanged)
- **FEATURE**: Statement duplicate cleanup — find duplicate groups and remove redundant copies
- **FEATURE**: `AEGIS.StatementReviewLookup` global utility — badge rendering with 15s TTL cache
- **NEW**: Review status filter chips in Statement History overview alongside directive filters
- **NEW**: Review stats panel showing total/pending/reviewed/rejected counts
- **NEW**: Clear Statement Data button in Settings → Data Management

### Role-Statement Responsibility Interface
- **FEATURE**: Role Statements panel (S key / button) — view all statements assigned to a role, grouped by document
- **FEATURE**: Bulk reassign — select statements and reassign to a different role via dropdown
- **FEATURE**: Bulk remove — unassign statements from a role
- **NEW**: Generic role warning banner for names like "Personnel", "Staff" that typically have misassigned statements
- **NEW**: Statement-to-role tagging with autocomplete datalist during statement edit in Document Viewer

### Bug Fixes
- **FIX**: Impact Analyzer readability — increased font sizes and padding for "path to 100" bars
- **FIX**: Factory reset now clears ALL tables including `role_function_tags`, `role_relationships`, `function_categories`, `role_required_actions`
- **FIX**: Compare feature CSRF failures — added `/api/compare/status` endpoint + retry-after-token-refresh logic
- **FIX**: Settings save UX — dirty tracking with pulse animation on Save button, unsaved changes warning on close

### Settings Enhancements
- **NEW**: Clear Role Dictionary button handler wired up in Settings → Data Management
- **NEW**: Clear Learning Data button handler wired up with new `/api/data/clear-learning` endpoint
- **NEW**: Data counts displayed in Data Management tab (statement count + review stats, role count)

### Backend
- **SCHEMA**: `scan_statements` table gains `review_status`, `confirmed`, `reviewed_by`, `reviewed_at`, `fingerprint` columns
- **MIGRATION**: Automatic backfill computes fingerprints for existing statements on first run
- **NEW**: 12 API endpoints: statement review (3), dedup (2), role statements (2), data management (1), compare status (1), clear learning (1), review stats (1), bulk reassign (1)
- **NEW**: `ScanHistoryDB` methods: `update_statement_review()`, `batch_update_statement_review()`, `get_statement_review_stats()`, `clear_statement_data()`, `find_duplicate_statements()`, `deduplicate_statements()`

---

## [4.5.2] - 2026-02-10 - Known Issues Cleanup + Scanning Pipeline Audit

### Critical Fixes (Crash Prevention)
- **FIX**: Infinite recursion in `_log()` fallback — when `config_logging` import fails, warning/error calls recursed infinitely. Now falls back to `print()`
- **FIX**: `SessionManager.set()` AttributeError — method didn't exist. Replaced with `SessionManager.update()` in `/api/review/single` endpoint
- **FIX**: `DoclingAdapter` crash when Docling returns tables with `None` headers — added null-safe guards on `t.headers`, `t.rows`, `t.caption`

### Bug Fixes
- **FIX**: Quality score always showing N/A — frontend used `quality_score` field but backend returns `score` (2 occurrences in app.js)
- **FIX**: `.doc` files now return a clear user-facing error message ("Please save as .docx") instead of silently failing when LibreOffice is unavailable
- **FIX**: Missing `@app.route('/api/filter')` decorator on `filter_issues()` — function was defined but unreachable (dead endpoint)
- **FIX**: File handle leaks in html_preview ZIP detection — bare `open().read(2)` replaced with context-managed `_is_zip_file()` helper
- **FIX**: Docling subprocess queue race condition — `empty()` + `get_nowait()` could miss data in transit. Now uses `get(timeout=2)`
- **FIX**: `fitz.Document` handle leak in `Pymupdf4llmExtractor` — `doc.close()` skipped on corrupt PDFs. Now uses `with` context manager
- **FIX**: Help docs JSON example used incorrect `quality_score` field — corrected to `score` + `grade`

### Improvements
- **NEW**: Empty/unreadable document detection — documents with no extractable text now return a clear warning with `score: 0, grade: N/A` instead of a misleading `score: 100, 0 issues`
- **IMPROVED**: DOCX Docling timeout reduced from 120s to 60s — DOCX files extract much faster than PDFs, so hanging DOCX files (e.g. USC_SOP_Template.docx) fail faster
- **IMPROVED**: `run_with_timeout()` in app.py documented with thread-leak warning (used only by export endpoint)
- **REMOVED**: Deprecated `_run_with_timeout()` function and `ThreadPoolExecutor` import from core.py — dead code from v4.5.0 revert
- **REMOVED**: `concurrent.futures` import that caused confusion about parallel checker support

### Known Issues Resolved
| Issue | Status | Resolution |
|-------|--------|-----------|
| Docling hangs on large PDFs | Fixed in v4.5.1 | Subprocess + 120s timeout + >2MB skip |
| Parallel checker deadlocks | Fixed in v4.5.0 | Reverted to sequential; dead code now removed |
| USC_SOP_Template.docx hangs | Mitigated | 60s DOCX timeout (was 120s); falls back to mammoth |
| .doc format not supported | Improved | Clear error message; works with LibreOffice installed |
| quality_score always N/A | Fixed | Corrected field name to `score` |

### Pipeline Audit Summary (8 fixes from deep audit)
- 3 crash-level bugs fixed (infinite recursion, missing method, null dereference)
- 3 resource leaks fixed (2 file handles, 1 fitz document)
- 1 race condition fixed (multiprocessing queue)
- 1 edge case handled (empty documents)

---

## [4.5.1] - 2026-02-10 - Relationship Graph Redesign: Edge Bundling + Semantic Zoom

### Hierarchical Edge Bundling (HEB) — New Default Graph Layout
- **NEW**: Roles arranged in a circle grouped by source document, with bundled bezier edge paths
- **NEW**: Document group arcs — colored arc segments on the outer ring showing document clusters
- **NEW**: Bridge role visualization — cross-document edges span the circle as long bundled curves
- **NEW**: Bundling Tension slider (0-1) — adjusts edge bundling from straight lines to maximum bundling
- **NEW**: HEB-specific legend with arc sample, bundled curve sample, and brightness indicators
- **NEW**: HEB circular minimap with colored document group arcs and node dots

### Semantic Zoom (Level-of-Detail)
- **NEW**: Toggle option alongside HEB for zoom-based progressive disclosure
- **NEW**: LOD 1 (zoomed out): Document clusters as labeled circles with galaxy dots
- **NEW**: LOD 2 (medium zoom): Individual nodes appear with bundled inter-group edges
- **NEW**: LOD 3 (zoomed in): Full labels, individual edges, complete detail

### Preserved Interactions
- **PRESERVED**: All 15 existing graph interactions work in HEB and Semantic Zoom
- **PRESERVED**: Node click → details panel, hover → tooltips, drill-down filtering, breadcrumbs
- **PRESERVED**: Weight slider, search, label visibility modes, zoom/pan, keyboard navigation
- **PRESERVED**: Minimap, adjudication badges, performance mode, dark mode

### Layout Controls
- **UPDATED**: Layout dropdown — Edge Bundling (default), Semantic Zoom, Force-Directed (Classic), Bipartite
- **UPDATED**: Legend auto-switches between force and HEB variants based on selected layout
- **UPDATED**: Bundling slider visibility toggles based on layout selection

### Performance
- **IMPROVED**: HEB is inherently faster than force-directed (no physics simulation)
- **IMPROVED**: Performance thresholds raised for HEB: 300 nodes / 600 links (vs 150/300 for force)
- **IMPROVED**: Dark mode `mix-blend-mode: screen` for edge visibility on dark backgrounds

---

## [4.5.0] - 2026-02-09 - Scan Progress Dashboard, Landing Page & Performance

### Scan Progress Dashboard
- **NEW**: Step-by-step checklist overlay replacing simple loading spinner during document review
- **NEW**: 7 weighted steps: Upload (5%), Extract (15%), Parse (10%), Quality Checks (35%), NLP (10%), Roles (15%), Finalize (10%)
- **NEW**: Real-time ETA calculation based on elapsed time and weighted progress
- **NEW**: Historical step duration averaging saved to localStorage for improved ETA accuracy
- **NEW**: Sub-progress bars per step with detail messages from backend phases
- **NEW**: Animated step transitions with spinner → checkmark on completion
- **NEW**: Cancel button wired to job cancellation system

### Landing Page Dashboard
- **NEW**: Tool launcher dashboard replaces empty drop zone on app load
- **NEW**: 6 tool cards: Review, Statement Forge, Roles Studio, Scan History, Compare, Link Validator
- **NEW**: Each card shows description and icon, navigates to the corresponding tool on click
- **NEW**: Recent Documents section showing last 5 scans with quick view/delete actions
- **NEW**: System stats bar (total scans, documents processed, roles discovered)
- **NEW**: Hero drop zone preserved — drag and drop still works for document review
- **NEW**: Responsive grid: 3-col → 2-col → 1-col with staggered card entrance animations

### Progress Reporting & Stability
- **IMPROVED**: Granular progress reporting during checker execution phase
- **IMPROVED**: Better cancellation checks between extraction, checking, and role phases
- **IMPROVED**: Sequential checker execution with per-checker progress updates

### Bug Fixes
- **FIX**: Statement extraction `||||||` regression — added `_sanitize_for_statements()` for Docling PDF text
- **FIX**: Compare Viewer dark mode — all `[data-theme="dark"]` selectors replaced with `body.dark-mode`
- **FIX**: Compare Viewer CSRF 403 errors — `window.CSRF_TOKEN || meta tag` pattern with sync from GET responses
- **FIX**: Document Viewer highlight alignment — replaced getBoundingClientRect with `scrollIntoView({block:'center'})`
- **FIX**: PDF.js toggle "not available" — added `.mjs` to allowed vendor file extensions in app.py
- **FIX**: PDF.js HEAD pre-check before ESM import with descriptive error messages
- **FIX**: Role Interactions empty page on drill — shows "No Detailed Data" empty state
- **FIX**: History tab action column cutoff — `table-layout: fixed` with explicit column widths
- **FIX**: Scan processing hanging — extraction timeouts (120s Docling, 90s pymupdf4llm, 60s mammoth, 90s roles)
- **FIX**: Added cancellation check before role extraction phase

### Quick Fixes
- **IMPROVED**: Matrix animation is now the default for batch processing (was circuit)
- **IMPROVED**: Matrix animation drop speed halved for more cinematic effect
- **IMPROVED**: Batch processing dark mode text visibility (`color: #fff; color-scheme: dark`)
- **REMOVED**: `.txt extension bypass` removed from help documentation and UPDATE_README

---

## [4.4.0] - 2026-02-09 - Statement Search, Bulk Edit, PDF Viewer & Diff Export

### Statement Quality Improvement
- **IMPROVED**: Statement Forge now uses mammoth's clean text when Docling is the primary extractor
- **IMPROVED**: Eliminates `|` and `**` table artifacts from statement descriptions
- **IMPROVED**: `clean_full_text` generated via `mammoth.extract_raw_text()` and stored in scan results

### Compare Viewer HTML Fixes
- **FIX**: Compare viewer resets document state on entry, preventing stale cache from previous viewer sessions
- **FIX**: Diff indicator badges inside removed highlights no longer inherit strikethrough text decoration

### Statement Diff Export
- **NEW**: CSV export from Compare Viewer with columns: Number, Title, Description, Directive, Role, Level, Diff Status, Changed Fields
- **NEW**: PDF export from Compare Viewer with AEGIS-branded report, summary statistics, and color-coded statement table
- **NEW**: Export buttons (CSV, PDF) in the compare diff summary bar

### Statement Search Across Scans
- **NEW**: Full-text search bar in Statement History overview dashboard
- **NEW**: Search across all statement descriptions and titles with debounced input (300ms)
- **NEW**: Results show directive badge, document name, scan date, and description excerpt
- **NEW**: Click search result to navigate directly to that scan's Document Viewer
- **NEW**: Optional directive filter on search results

### Bulk Statement Editing
- **NEW**: Bulk edit mode toggle in Document Viewer toolbar
- **NEW**: Checkbox selection on individual statements with select count display
- **NEW**: Batch update directive and role fields for all selected statements
- **NEW**: Apply and Clear Selection controls in bulk action bar

### PDF.js Viewer Integration
- **NEW**: PDF.js v4.2.67 integrated for pixel-perfect PDF rendering
- **NEW**: HTML/PDF view toggle button in Document Viewer header for PDF documents
- **NEW**: Each PDF page rendered to canvas with page number labels
- **NEW**: Dynamic ESM import with graceful fallback when PDF.js unavailable

### Backend Changes
- **NEW**: `GET /api/scan-history/statements/search` — full-text LIKE search on description/title across all scans
- **NEW**: `PUT /api/scan-history/statements/batch` — batch update for statement fields (directive, role, level, title, description)
- **NEW**: `GET /api/scan-history/document-file` — serves original document file from scan filepath for PDF.js rendering
- **NEW**: `GET /api/statement-forge/compare/<id1>/<id2>/export-csv` — CSV diff export with UTF-8 BOM
- **NEW**: `GET /api/statement-forge/compare/<id1>/<id2>/export-pdf` — PDF diff export with reportlab (AEGIS branding, color-coded rows)
- **NEW**: `search_statements()` and `batch_update_statements()` methods in scan_history.py

---

## [4.3.0] - 2026-02-09 - Document Extraction Overhaul & AEGIS Installer

### Document Extraction — mammoth for DOCX, pymupdf4llm for PDF
- **NEW**: MammothDocumentExtractor class — converts .docx to clean semantic HTML via mammoth library
- **NEW**: Pymupdf4llmExtractor class — converts PDF to structured Markdown via pymupdf4llm
- **NEW**: html_preview field stored with scan results for rich document rendering in Statement History
- **NEW**: Automatic html_preview generation for all extraction paths (Docling, mammoth, pymupdf4llm, legacy)
- **IMPROVED**: DOCX text extraction no longer produces table artifacts (pipe `|` and `---` characters eliminated)
- **IMPROVED**: Statement Forge receives cleaner text input, improving extraction accuracy
- **IMPROVED**: All 60+ checkers continue to receive full_text with zero modifications needed

### HTML-Based Document Viewer in Statement History
- **NEW**: renderHTMLDocument() renders mammoth HTML output with proper tables, headings, bold/italic formatting
- **NEW**: DOM-based text node walking replaces fragile string-index highlighting for HTML content
- **NEW**: Cross-extractor normalized matching strips markdown artifacts (`**`, `|`, `---`, `#`) for reliable highlight positioning
- **NEW**: 3-strategy matching: exact substring, normalized match with position mapping, word-sequence fuzzy match
- **NEW**: HTML content CSS styles for tables (AEGIS gold header tint), headings, lists, paragraphs in document panel
- **NEW**: Dark mode and light mode support for rendered HTML content
- **IMPROVED**: Old scans without html_preview gracefully fall back to plain-text highlighting (backward compatible)

### AEGIS Installer
- **NEW**: Install_AEGIS.bat — 7-step Windows installer with user-selectable install location
- **NEW**: Default install to C:\AEGIS with clean folder structure (Start/Stop scripts at top, app code in subfolder)
- **NEW**: Offline dependency installation from bundled wheel packages
- **NEW**: NLTK data setup and spaCy model installation from offline bundles
- **NEW**: Start_AEGIS.bat and Stop_AEGIS.bat launcher scripts created automatically
- **NEW**: Updates folder with README for the update workflow

### Distribution Packaging
- **IMPROVED**: package_for_distribution.bat renamed to AEGIS_Distribution with mammoth wheel download
- **IMPROVED**: 8 download steps covering all dependencies including mammoth and pymupdf4llm
- **IMPROVED**: Wheels stored in deployment/wheels/ subdirectory for clean organization

### Backend Changes
- **NEW**: mammoth>=1.6.0 added to requirements.txt
- **NEW**: MAMMOTH_AVAILABLE and PYMUPDF4LLM_AVAILABLE import flags with graceful fallback
- **NEW**: /api/scan-history/document-text endpoint returns html_preview and format fields
- **IMPROVED**: Extraction fallback chain: Docling → mammoth/pymupdf4llm → legacy extractors
- **IMPROVED**: html_preview stored in results_json for scan history (no schema changes needed)

---

## [4.2.0] - 2026-02-09 - Statement Forge History & Compare Viewer

### Statement Forge History — Complete Feature
- **NEW**: Statement History modal accessible from Scan History (statement count click) and Statement Forge (clock icon)
- **NEW**: Overview dashboard with 4 stat tiles (Total Scans, Latest Count, Unique Roles, Top Directive)
- **NEW**: Trend line chart plotting statement counts across scans over time
- **NEW**: Directive breakdown donut chart showing shall/must/will/should/may distribution
- **NEW**: Scrollable scan timeline with View and Compare action buttons per scan

### Document Viewer — Full-Text with Highlighted Statements
- **NEW**: Split-panel document viewer: source document (left) with statement detail (right)
- **NEW**: Statements highlighted in document text using directive-specific colors (blue=shall, red=must, amber=will, green=should, purple=may)
- **NEW**: Click any highlight to jump to that statement's detail panel
- **NEW**: Click any statement in detail panel to scroll document to its location
- **NEW**: Directive filter chips to focus on specific statement types
- **NEW**: Highlight-to-create: select text in document to create new statements with auto-detected directive
- **NEW**: Statement editing via inline form (directive, role, description) with PUT API save
- **NEW**: Keyboard navigation: ↑/↓ arrows, e=edit, Esc=close, ←=back

### Unified Compare Viewer — Document Diff with Full Features
- **NEW**: Unified document viewer showing single document text with diff-aware highlights
- **NEW**: Four diff categories: unchanged (normal), added (green + NEW badge), removed (red + strikethrough + REMOVED badge), modified (amber + CHANGED badge)
- **NEW**: Diff summary bar with counts for each category
- **NEW**: Dual filter system: directive chips (row 1) + diff status chips (row 2)
- **NEW**: Field-level diff display for modified statements (shows old → new for directive, role, level changes)
- **NEW**: Keyboard shortcuts: a=jump to next added, r=next removed, m=next modified
- **NEW**: Edit button on newer-scan statements only; removed statements show read-only note
- **NEW**: Backend enhanced `compare_scan_statements()` with modified detection using two-tier fingerprinting

### Overlapping Statement Highlight Fix
- **FIX**: Statements sharing the same document text now correctly share a single `<mark>` element via `data-stmt-indices` attribute
- **FIX**: New `findMarkForIndex()` helper searches marks by comma-separated index list instead of exact match
- **FIX**: `updateActiveHighlight()`, `scrollToStatement()`, and `updateHighlightDirective()` all use the new helper

### Document Scroll Positioning Fix
- **FIX**: Document viewer now scrolls to correct position when navigating between statements
- **FIX**: Root cause: `mark.offsetTop` was relative to `sfh-modal-overlay` (wrong offsetParent) instead of `sfh-doc-content`
- **FIX**: Replaced `offsetTop` approach with `getBoundingClientRect()` math for reliable cross-container positioning
- **FIX**: Highlighted statement now appears in the upper third of the visible document area

### Additional Fixes
- **FIX**: Forge History button in Statement Forge sidebar now correctly opens history for current document
- **FIX**: Dark mode statement highlights use proper opacity for readability
- **FIX**: Navigation buttons (View, Compare) render correctly in scan timeline
- **FIX**: X close button properly closes Statement History modal
- **FIX**: Escape key closes Statement History without propagating to Statement Forge modal

### CSS — Statement History Styles
- **NEW**: ~400 lines of CSS for Statement History modal, overview dashboard, document viewer, compare viewer
- **NEW**: Directive-specific highlight colors with dark mode support
- **NEW**: Diff highlight styles: `.sfh-diff-added`, `.sfh-diff-removed`, `.sfh-diff-modified` with inline badges
- **NEW**: Diff summary bar, diff filter chips, detail panel diff display
- **NEW**: Light mode overrides for all diff colors

### Backend
- **NEW**: `compare_scan_statements()` enhanced with modified detection using `desc_fp` + `full_fp` two-tier matching
- **NEW**: `_diff_status` injected on each statement: 'unchanged', 'added', 'removed', 'modified_new', 'modified_old'
- **NEW**: Modified statements include `_modified_from` reference for field-level comparison

### Files Modified
- `static/js/features/statement-history.js` — New module (~1600 lines): overview, document viewer, compare viewer, highlight rendering, keyboard nav, text selection creation
- `static/css/features/statement-history.css` — New stylesheet (~400 lines): all Statement History styling with dark/light mode
- `scan_history.py` — Enhanced `compare_scan_statements()` with modified detection + `_diff_status` injection
- `app.py` — Statement History API endpoints (document-text, compare)
- `templates/index.html` — Script/CSS includes for statement-history module

### Technical Notes
- `findHighlightPositions()` extracted as shared helper for both renderers
- Overlap removal merges `allIndices` when multiple statements share the same text region
- Both `renderHighlightedDocument()` and `renderCompareHighlightedDocument()` emit `data-stmt-indices`
- `scrollToStatement()` uses `getBoundingClientRect()` for reliable cross-container scroll positioning
- Statement extraction logic (`statement_forge/extractor.py`) confirmed intact and unmodified

---

## [4.1.0] - 2026-02-08 - Nimbus SIPOC Import, Role Inheritance & Template

### Nimbus SIPOC Import
- **NEW**: Import roles from Nimbus process model SIPOC Excel exports
- **NEW**: 5-step import wizard: Upload → Preview → Options → Import → Complete
- **NEW**: Import dropdown menu with "Import CSV/Excel" and "Nimbus SIPOC Import" options
- **NEW**: Context-dependent dual-mode parsing (hierarchy mode vs. process mode)
- **NEW**: Handles tools/systems (prefixed with `[S]`) as separate category
- **NEW**: Merges metadata across all rows where a role appears (description, org tags, disposition)
- **NEW**: Auto-creates function tags for organizational groupings and baselined status
- **NEW**: Clear previous SIPOC import option for clean reimport
- **NEW**: `sipoc_parser.py` standalone module for SIPOC Excel parsing

### Role Inheritance (Hierarchy Mode)
- **NEW**: Resource-based inheritance — primary role (pos 1) inherits from secondary roles (pos 2+)
- **NEW**: `inherits-from` relationship type replaces `supervises` for Roles Hierarchy map
- **NEW**: Suppliers/Customers columns ignored in hierarchy mode (false positives)
- **NEW**: Inheritance terminology throughout: "Inherits From" / "Inherited By" labels
- **NEW**: Inheritance chains: trace where secondary roles appear as primary in other rows

### Process Mode (Auto-Fallback)
- **NEW**: Auto-fallback when "Roles Hierarchy" map path not found in SIPOC file
- **NEW**: Processes ALL rows instead of returning 0 results
- **NEW**: `co-performs` relationship type for multiple roles on same activity
- **NEW**: `supplies-to` relationship type for upstream supplier roles
- **NEW**: `receives-from` relationship type for downstream customer roles
- **NEW**: Yellow/green info boxes showing parsing mode in SIPOC preview

### Interactive HTML Role Import Template
- **NEW**: Downloadable standalone HTML form for manual role population
- **NEW**: Single role entry form with all fields (name, category, type, disposition, etc.)
- **NEW**: Bulk paste modal with auto-format detection (Excel/TSV, CSV, semicolons, one-per-line)
- **NEW**: Bulk preview with column mapping and import confirmation
- **NEW**: Sortable role table with inline edit/delete
- **NEW**: JSON export compatible with AEGIS import (role_dictionary_import format)
- **NEW**: Function tag picker with embedded categories from database
- **NEW**: Dark/light mode toggle with localStorage persistence
- **NEW**: AEGIS-branded header with shield logo and version info
- **NEW**: Auto-updating stat cards (Total Roles, Deliverables, With Tags, With Description)
- **NEW**: `role_template_export.py` standalone HTML generator (2039 lines)
- **NEW**: "Template" download button in dictionary toolbar

### Role Hierarchy & Relationships
- **NEW**: `role_relationships` database table with inherits-from, uses-tool, co-performs, supplies-to, receives-from types
- **NEW**: Hierarchy view mode in dictionary tab (Table | Card | Hierarchy toggle)
- **NEW**: Collapsible tree visualization of role inheritance
- **NEW**: Tree search with auto-expand to matching nodes
- **NEW**: Expand All / Collapse All controls
- **NEW**: Role Disposition tracking: Sanctioned (✓), To Be Retired (⚠), TBD (?)
- **NEW**: Baselined status tracking with green checkmark badge
- **NEW**: Role Type classification (Singular-Specific, Singular-Aggregate, Group-Specific, Group-Aggregate)
- **NEW**: 5 new database columns on role_dictionary: tracings, role_type, role_disposition, org_group, hierarchy_level, baselined

### Interactive HTML Role Inheritance Map (formerly Hierarchy Export)
- **NEW**: Standalone interactive HTML file for offline role inheritance visualization
- **NEW**: Renamed from "Role Hierarchy" to "Role Inheritance Map" (this is inheritance, not organizational hierarchy)
- **NEW**: 4 views: Dashboard, Tree, Graph, Table
- **NEW**: Pre-export filter modal: filter by org group, disposition, baselined status, include/exclude tools
- **NEW**: SVG-based donut charts and cluster-based graph (no external dependencies)
- **NEW**: Role detail panel with disposition badges, inherits-from/inherited-by navigation
- **NEW**: Dark/light mode toggle with localStorage persistence
- **NEW**: Filtering and search across all views (function tag, disposition, role type, baselined filters)
- **NEW**: CSV export from table view
- **NEW**: Print-friendly mode via CSS media queries
- **NEW**: Function Tag Distribution donut chart — accurate counts from role_function_tags join table
- **NEW**: Dashboard stat cards: Total Roles, Tools, Function Tags, Relationships with animated counters
- **NEW**: Health Metrics panel: Descriptions % and Baselined % with color-coded progress bars
- **NEW**: Role Types horizontal bar chart breakdown (Singular-Specific, Singular-Aggregate, Group-Specific, Group-Aggregate, Unknown)

### Inline Editing & Export-Back (Inheritance Map)
- **NEW**: Click Edit button on any role in Tree/Graph/Table views to edit all fields inline
- **NEW**: Editable fields: role name, role type, disposition, org group, hierarchy level, baselined, aliases, category, description, notes, status (Sanctioned/To Be Retired/Deliverable/Rejected)
- **NEW**: Edit form organized into 3 sections: Identity, Classification, Details
- **NEW**: Change tracking with "Modified" badge on edited roles and amber dot indicators in tree view
- **NEW**: Export Changes modal — shows field-level diffs for every modified role
- **NEW**: Download changes as JSON compatible with AEGIS adjudication import endpoint
- **NEW**: Undo/redo support for edit history within the export session
- **NEW**: Import instructions in Export Changes modal: Option A (drop in updates/ folder → Settings → Check for Updates → Update) and Option B (manual import in Adjudication tab)

### Auto-Import Support for Edited Export JSON
- **NEW**: `update_manager.py` auto-detects adjudication JSON files in updates/ folder
- **NEW**: Files with `export_type: "adjudication_decisions"` are automatically routed to `batch_adjudicate()`
- **NEW**: Extended field support in `batch_adjudicate()`: role_type, role_disposition, org_group, hierarchy_level, baselined, aliases, new_role_name (for renames)
- **NEW**: `_import_adjudication_json()` method in FileRouter for seamless update pipeline

### SIPOC Re-Import with Diff-Based Cleanup
- **IMPROVED**: Re-importing a SIPOC file now automatically removes stale roles that were previously imported but are no longer present in the new SIPOC file
- **NEW**: Diff-based cleanup: compares new SIPOC role names against existing `source='sipoc'` roles, deletes those not in the new file
- **NEW**: Stale role cleanup also removes associated relationships (`import_source='sipoc'`) and function tags (`assigned_by='sipoc_import'`)
- **NEW**: Import results now show removal counts: "Stale Roles Removed" with explanation
- **IMPORTANT**: Only roles with `source='sipoc'` are affected — manually added or adjudicated roles are never removed
- **IMPORTANT**: The import is upsert-based: existing roles are updated, new roles are added, missing roles are removed

### Dictionary Keyboard Hints Bar Fix
- **FIX**: Keyboard hints bar (j/k Navigate, Space Select, etc.) no longer overlaps table rows
- **FIX**: Table container now uses flexbox sizing instead of fixed 500px max-height
- **FIX**: Dictionary layout uses proper flex hierarchy so content fills available space without overflow

### Roles Studio Click Handling Fixes (End-to-End Review)
- **FIX**: RACI Matrix row click now opens drilldown modal — was silently failing due to `showModal()` signature mismatch (passed title string instead of element ID)
- **FIX**: RACI cell click (R/A/C/I values) now opens responsibilities modal — same root cause as drilldown
- **NEW**: `showContentModal(title, htmlContent, options)` function in modals.js — creates dynamic modal overlays for content that doesn't have a pre-existing DOM element
- **FIX**: Adjudication card body click now opens Role Source Viewer — previously only the role name and view button worked, clicking card body/meta/doc chips did nothing
- **FIX**: Adjudication kanban card click now opens Role Source Viewer — kanban cards had zero click handlers (only drag-and-drop)
- **FIX**: Adjudication context toggle ("Show more") now works — class name mismatch between rendered HTML (`.adj-card-context-toggle`) and event handler (`.adj-context-toggle`)
- **FIX**: Escape key on RACI/content modals no longer also closes parent Roles Studio modal — added `stopPropagation()` to content modal Escape handler
- **FIX**: Data Explorer `getBoundingClientRect` error when switching tabs — added null check for `chart.canvas` before accessing rect in setTimeout callback
- **VERIFIED**: All 8 Roles Studio tabs tested end-to-end with zero console errors: Overview, Relationship Graph, Role Details, RACI Matrix, Role-Doc Matrix, Adjudication, Role Dictionary, Document Log

### Graph View Animations
- **NEW**: Staggered card entrance animations on cluster overview (Layer 0) and root roles (Layer 1)
- **NEW**: SVG node pop-in animation with bounce effect on node neighborhood view (Layer 2)
- **NEW**: Center node pulse animation on focus
- **NEW**: Arrow line draw-in animation from center to connected nodes
- **NEW**: Mini progress bar grow animation on cluster cards
- **NEW**: Enhanced hover effects: card lift with shadow on cluster/root cards
- **NEW**: Consistent inheritance terminology: "INHERITS FROM" and "INHERITED BY" section labels (no "reports to")

### Visual Differentiation
- **NEW**: Sanctioned roles: green border, shield icon, "Owner Approved" styling
- **NEW**: To Be Retired roles: strikethrough name, faded/muted, amber warning border, 65% opacity
- **NEW**: TBD roles: dotted gray border, italic text, question mark icon
- **NEW**: Baselined badge: green checkmark pill on card headers and table rows
- **NEW**: Role Type badge: purple pill showing classification
- **NEW**: All disposition treatments applied in both in-app views and HTML export

### Backend & API
- **NEW**: `POST /api/roles/dictionary/import-sipoc` - SIPOC file upload with preview/confirm modes
- **NEW**: `GET /api/roles/relationships` - Query role relationships with filters
- **NEW**: `GET /api/roles/hierarchy` - Full inheritance tree structure for visualization
- **NEW**: `GET /api/roles/hierarchy/export-html` - Generate filtered interactive HTML export
- **NEW**: `POST /api/roles/dictionary/clear-sipoc` - Clear all SIPOC-imported data
- **NEW**: `GET /api/roles/dictionary/export-template` - Download interactive role import template
- **NEW**: 6 new database methods in scan_history.py
- **IMPROVED**: `import_roles_to_dictionary()` supports extended fields (role_type, role_disposition, org_group, baselined)

### Technical
- `roles-dictionary-fix.js`: Added SIPOC wizard, hierarchy view, export filter, template button (~600 lines added)
- `roles-studio.css`: Added SIPOC, hierarchy, disposition, fallback notice CSS with dark mode support
- `sipoc_parser.py`: New standalone parser module with dual-mode logic
- `hierarchy_export.py`: New standalone HTML generator with inheritance terminology
- `role_template_export.py`: New standalone HTML template generator (2039 lines)
- `scan_history.py`: Extended with inheritance types, extended field import support

---

## [4.0.5] - 2026-02-08 - Role Dictionary Complete Overhaul

### Dictionary Dashboard
- **NEW**: Live dashboard with 4 stat tiles: Total Roles, Deliverables, Adjudicated, Health Score
- **NEW**: Category distribution donut chart (Chart.js) with center text overlay
- **NEW**: Source breakdown horizontal bar chart showing builtin/manual/adjudication/upload distribution
- **NEW**: Top categories list with proportional bars and counts
- **NEW**: Health Score metric calculated from description and tag completeness (0-100%)

### Card View
- **NEW**: Toggle between table and card view (T key or toolbar buttons)
- **NEW**: Rich role cards with color-coded left border by adjudication status
- **NEW**: Cards show description excerpt, aliases, function tags, notes, and metadata
- **NEW**: Inline actions (edit, clone, delete) appear on card hover
- **NEW**: Deliverable star toggle and status toggle on each card

### Bulk Operations
- **NEW**: Checkbox selection on every row and card for multi-select
- **NEW**: Select All checkbox in table header
- **NEW**: Bulk action bar with: Activate, Deactivate, Set Category, Mark/Unmark Deliverable, Delete
- **NEW**: Gold-tinted action bar with count badge and clear button

### Inline Quick Actions
- **NEW**: Click category badge to change category inline (dropdown replaces badge)
- **NEW**: Star toggle (★/☆) for deliverable status on each row
- **NEW**: Click role name to copy to clipboard
- **NEW**: Clone button creates duplicate role with "(Copy)" suffix

### Duplicate Detection
- **NEW**: Warns on save when similar role names or matching aliases already exist
- **NEW**: Fuzzy matching (containment check for names > 4 chars)
- **NEW**: User can confirm to save anyway if intentional

### Keyboard Navigation
- **NEW**: `↑`/`↓` or `j`/`k` to navigate rows
- **NEW**: `Enter` or `e` to edit focused role
- **NEW**: `Space` to toggle selection on focused role
- **NEW**: `T` to toggle between table and card view
- **NEW**: `/` to focus search input
- **NEW**: `Escape` to clear selection and focus
- **NEW**: `Delete`/`Backspace` to delete focused role
- **NEW**: Keyboard hint bar at bottom of dictionary tab

### Enhanced Filtering
- **NEW**: Filter by adjudication status (Confirmed, Deliverable, Rejected, Pending)
- **NEW**: Filter by has/no description
- **NEW**: Filter by has/no function tags
- **NEW**: Filter count badge showing "X of Y roles"

### Audit Trail & Metadata
- **NEW**: Time ago display (just now, 5m ago, 2h ago, 3d ago) with full date tooltip
- **NEW**: "by [username]" attribution on modified dates
- **IMPROVED**: Adjudication badge on every row (✓ Confirmed, ★ Deliverable, ✗ Rejected, ○ Pending)
- **IMPROVED**: Sortable columns with visual sort direction arrows

### Files Modified
- `static/js/roles-dictionary-fix.js` - Complete rewrite (854 → 1555 lines)
- `templates/index.html` - New dictionary layout with dashboard, bulk bar, view toggle, keyboard hints
- `static/css/features/roles-studio.css` - 500+ lines of new dictionary CSS with dark mode

---

## [4.0.4] - 2026-02-08 - Import Enhancements & PDF Export

### Dictionary Diff Preview
- **NEW**: Preview modal shows what will change before importing adjudication decisions
- Shows new roles (green), changed roles (amber), and unchanged roles (gray)
- Changed roles display specific field differences (status, category, notes)
- "Import" button only after reviewing the diff

### Package Versioning
- **NEW**: Version compatibility check when importing packages or decisions
- Warns if the package was created with a newer version of AEGIS
- Warning is informational (import still allowed) to avoid blocking workflows

### PDF Adjudication Report
- **NEW**: Export → PDF Report generates a formatted adjudication report
- Sections: Summary statistics, roles grouped by status, function tag distribution
- Uses AEGIS gold branding, professional layout with reportlab

### Import Progress Indicators
- **IMPROVED**: Visual progress overlay during adjudication decision imports
- Spinner + status text replaces previous toast-only feedback pattern

### New API Endpoints
- `POST /api/roles/adjudication/import-preview` - Diff preview before import
- `GET /api/roles/adjudication/export-pdf` - PDF report download

### Files Modified
- `app.py` - Version meta tag injection, 2 new API endpoints
- `adjudication_report.py` - NEW: PDF report generator using reportlab
- `static/js/roles-tabs-fix.js` - Version check, diff modal, progress overlay, PDF export
- `static/css/features/roles-studio.css` - Diff modal styles with dark mode support
- `templates/index.html` - PDF export dropdown item

---

## [4.0.3] - 2026-02-08 - Adjudication Tab Complete Overhaul

### Global Adjudication Badges
- **NEW**: Tool-wide adjudication status badges on all role displays (✓ Adjudicated, ★ Deliverable, ✗ Rejected)
- **NEW**: `AEGIS.AdjudicationLookup` global utility - fetches role dictionary, caches with 30s TTL, provides badge HTML
- **NEW**: `adjudication-lookup.js` - standalone utility for any JS file to display adjudication status
- **NEW**: Adjudication badge CSS in `style.css` with light/dark mode support
- Badges appear in: Roles Studio Overview, Role Details, Data Explorer (all views), Role-Doc Matrix, RACI Matrix
- Relationship Graph uses D3.js node coloring instead of HTML badges (appropriate for SVG graph)

### Adjudication Stat Subtitles
- **IMPROVED**: Adjudication stats shown as green subtitle under Unique Roles tile (not a separate tile)
- Clean 3-column/4-column grid aesthetic preserved across all stat displays
- Subtitle format: "✓ X adjudicated · Y deliverable" in green (#22c55e)
- Applied in: Roles Studio Overview, Role Details, Data Explorer Overview, index.html

### Dark Mode / Light Mode Fix
- **FIX**: Critical bug - `dark-mode.css` was not loading at all due to CSS @import ordering violation
- Root cause: adj-badge CSS rules were placed before `@import url('dark-mode.css')` in `style.css`
- Per CSS spec, `@import` must precede all rules or browser silently ignores them
- **FIX**: Restructured `style.css` - all @import statements first, then CSS rules
- Verified dark/light mode works correctly across main app, Roles Studio, and Data Explorer

### Data Explorer Donut Chart Centering
- **FIX**: "3 CATEGORIES" center text in donut chart now properly centered within the donut ring
- Chart.js legend (position: right) shifts the donut left; `centerDonutText()` recalculates position
- Fixed timing: use `setTimeout(50)` + animation `onComplete` callback instead of single `requestAnimationFrame`

### Files Modified (Badges & Theme Session)
- `static/js/adjudication-lookup.js` - **NEW**: Global adjudication badge utility
- `static/css/style.css` - **FIX**: @import ordering + adjudication badge CSS
- `templates/index.html` - Adjudication subtitle under Unique Roles, script include for adjudication-lookup.js
- `static/js/roles-tabs-fix.js` - Adjudication subtitle population, badge integration in Role-Doc Matrix
- `static/js/features/roles.js` - Badges in Overview/Details stats, 3-column grid restored
- `static/js/features/data-explorer.js` - Badges in all drill views, subtitle in Overview, donut centering fix
- `static/css/features/data-explorer.css` - Light mode overrides for adjudication badges

### Adjudication System Rewrite
- **OVERHAUL**: Complete rewrite of the Adjudication tab in Roles & Responsibilities Studio
- Dashboard with animated stat cards (Pending/Confirmed/Deliverable/Rejected) and SVG progress ring
- Click any stat card to filter roles to that status
- Enhanced role cards with confidence gauge, function tag pills, document chips, and context preview

### Auto-Classify & Batch Operations
- **NEW**: Auto-Classify button runs AI-assisted pattern matching on all pending roles
- Modal preview of suggestions before applying, with per-role accept/reject
- Batch adjudication API endpoint processes multiple roles in single transaction
- Bulk select with select-all checkbox and batch confirm/reject/deliverable buttons

### Kanban Board View
- **NEW**: Toggle between list view and kanban board view
- 4-column board: Pending | Confirmed | Deliverables | Rejected
- Native HTML5 drag-and-drop between columns
- View preference persisted in localStorage

### Function Tags & Enhanced Cards
- **NEW**: Function tag pills displayed on each role card
- Add/remove tags directly from cards via hierarchical dropdown
- Confidence ring (SVG) showing classification confidence per role
- Document chips showing which scanned documents contain each role
- Expandable context preview with full text toggle

### Keyboard Navigation & Undo/Redo
- **NEW**: Full keyboard navigation (Arrow keys to move, C/D/R to classify, V for Source Viewer)
- **NEW**: Undo/Redo system for all adjudication actions (Ctrl+Z / Ctrl+Y)
- Space bar toggles selection, Ctrl+A selects all visible

### Backend Enhancements
- `POST /api/roles/auto-adjudicate` - Pattern-based auto-classification with confidence scoring
- `POST /api/roles/adjudicate/batch` - Batch adjudication in single transaction
- `GET /api/roles/adjudication-summary` - Dashboard statistics endpoint
- Enhanced `POST /api/roles/adjudicate` with optional `function_tags` parameter
- `batch_adjudicate()` and `get_adjudication_summary()` methods in `scan_history.py`

### Role Source Viewer Integration
- **NEW**: Function tag section in Role Source Viewer with Add/Remove tags
- **NEW**: Custom tag creation dialog within Source Viewer
- Adjudication status syncs between Adjudication tab and Source Viewer

### Infrastructure & Session Fixes
- **FIX**: CSRF token sync between page load and fetch sessions
- **FIX**: Persistent secret key survives server restarts (`.secret_key` file)
- **FIX**: Switched localhost from Waitress to Flask threaded server (Waitress added Secure flag to cookies)
- **FIX**: Kanban view toggle now properly shows/hides list and board containers
- Added `syncCSRFFromResponse()` helper and `getCSRFToken()` in roles-tabs-fix.js
- CSRF token meta tag kept in sync across all API response paths

### Interactive HTML Export/Import
- **NEW**: Export adjudication as standalone interactive HTML kanban board
- HTML file works offline with drag-and-drop, function tag assignment, category editing, notes
- Dark/light mode toggle, search/filter, real-time stat counters
- "Generate Import File" button creates JSON with all decisions
- Import decisions JSON back into AEGIS to apply changes
- Export dropdown menu with CSV, Interactive HTML Board, and Import Decisions options

### Roles Sharing System
- **NEW**: Share button in Adjudication toolbar with dropdown
- "Export to Shared Folder" exports master dictionary with function tags to configured path
- "Email Package" creates `.aegis-roles` package and opens mailto: with import instructions
- Import Package button in Settings > Sharing tab for `.aegis-roles` file upload
- FileRouter recognizes `.aegis-roles` files in updates/ folder for auto-import
- Enhanced master file format now includes function_tags per role
- Enhanced sync_from_master_file() imports function_tags during sync

### New API Endpoints
- `GET /api/roles/adjudication/export-html` - Generate interactive HTML board download
- `POST /api/roles/adjudication/import` - Import adjudication decisions from JSON
- `POST /api/roles/share/package` - Create downloadable .aegis-roles package
- `POST /api/roles/share/import-package` - Import .aegis-roles package (file upload or JSON)

### Files Modified
- `adjudication_export.py` - **NEW**: Standalone interactive HTML generator (~500 lines)
- `scan_history.py` - Enhanced export/import with function_tags, batch_adjudicate, summary methods
- `app.py` - 4 new export/import/share endpoints; auto-adjudicate, batch, summary endpoints
- `config_logging.py` - Persistent secret key generation
- `templates/index.html` - Export dropdown, Share button, Settings import package UI
- `static/css/features/roles-studio.css` - Export/share dropdown styles, adjudication CSS
- `static/js/roles-tabs-fix.js` - Export/share/import handlers, rendering rewrite, CSRF sync
- `static/js/features/roles.js` - Exported detectDeliverable and suggestRoleType helpers
- `static/js/features/role-source-viewer.js` - Function tag section, custom tag creation
- `static/js/api/client.js` - CSRF meta tag sync on token refresh
- `update_manager.py` - .aegis-roles file routing and auto-import support

---

## [4.0.2] - 2026-02-07 - Roles Studio UI Enhancements & RACI Fix

### Role Source Viewer Dark Mode
- **FIX**: Complete dark mode support for Role Source Viewer modal
- Document text area now fully readable in dark mode (#e0e0e0 text on dark background)
- All panel sections, buttons, labels, and inputs have proper dark mode styling
- Role highlights visible with amber gradient overlays in dark mode
- Footer shortcuts and keyboard hints styled for dark mode

### RACI Matrix Deduplication Fix
- **FIX**: RACI totals now match Overview's deduplicated responsibility count
- Previously: RACI showed 406 total (counting duplicates across documents)
- Now: RACI shows ~297 total (matching Overview's 298 unique responsibilities)
- Added deduplication logic to `get_raci_matrix()` in `scan_history.py`
- Uses same normalization (first 100 chars, lowercase) as `get_all_roles()`

### Role Details Tab Enhancements
- **NEW**: "Explore in Data Explorer" icon button on each role card
- Magnifying glass + plus icon links directly to role's Data Explorer view
- Replaces double-click behavior with visible, clickable icon
- Hover effects and smooth transitions on explore button

### Files Modified
- `static/js/features/role-source-viewer.js` - Comprehensive dark mode CSS (~250 lines added)
- `scan_history.py` - RACI deduplication in `get_raci_matrix()` method
- `static/js/roles-tabs-fix.js` - Explore button on role cards

---

## [4.0.1] - 2026-02-04 - Role Extraction Accuracy Enhancement

### Role Extractor v3.3.x - Comprehensive Accuracy Improvements

Major improvements to `role_extractor_v3.py` achieving **99%+ recall** across defense, aerospace, government, and academic technical documents.

#### Performance Results

| Category | Documents Tested | Average Recall |
|----------|-----------------|----------------|
| Original (FAA, OSHA, Stanford) | 3 | **103%** |
| Defense/Government (MIL-STD, NIST, NASA) | 8 | **99.5%** |
| Aerospace (NASA, FAA, KSC) | 7 | **99.0%** |

#### v3.3.0 - OSHA and Academic Roles
- Added ~40 new roles to KNOWN_ROLES (worker terms, academic roles)
- Added worker_terms and academic_terms early validation in `_is_valid_role()`
- Generic worker terms: employer, employees, personnel, staff, workers
- Academic roles: graduate student, postdoctoral researcher, lab supervisor

#### v3.3.1 - False Positives Cleanup
- Added ~25 entries to FALSE_POSITIVES
- Safety management concepts: safety management, safety policy, safety assurance
- Document references: advisory circular, federal register
- Department names: environmental health and safety

#### v3.3.2 - Defense/MIL-STD Roles
- **Key Fix**: Removed `contractor`, `government`, `quality control` from FALSE_POSITIVES
- Added ~30 defense-specific roles to KNOWN_ROLES
- Government acquisition: contracting officer, procuring activity, technical authority
- Contractor roles: prime contractor, subcontractor, vendor, supplier
- Technical manual: technical writer, illustrator, custodian

#### v3.3.3 - Aerospace Roles
- Added aerospace/aviation terms to defense_terms validation
- Added: lead, leads, pilot, pilots, engineer, engineers

#### Test Scripts Created
- `manual_role_analysis.py` - Original 3-document test
- `defense_role_analysis.py` - MIL-STD specific testing
- `defense_role_analysis_expanded.py` - 8-document government/defense test
- `aerospace_role_analysis.py` - 7-document aerospace test

#### Documentation Updated
- `ROLE_EXTRACTION_IMPROVEMENTS.md` - Complete implementation guide
- `ROLE_EXTRACTION_TEST_RESULTS.md` - Updated with new test results

---

## [4.0.0] - 2026-02-04 - AEGIS Rebrand Release

### Major Rebrand
Complete rebrand from TechWriterReview to **AEGIS** (Aerospace Engineering Governance & Inspection System).

#### Branding Updates
- **Name**: TechWriterReview → AEGIS
- **Full Name**: Aerospace Engineering Governance & Inspection System
- **Logo**: New AEGIS shield logo with gold/bronze gradient (#D6A84A, #B8743A)
- **Color Scheme**: Updated to gold accent palette throughout UI
- **163+ files** updated across codebase with new branding

#### UI Improvements
- **Document Text Readability**: Enhanced font sizing (15px), line-height (1.75), and letter spacing for easier reading
- **Navigation Tab Order**: Validate and Links tabs now adjacent (Portfolio moved to end)
- **Active Tab Styling**: Gold accent underline for active navigation tabs
- **Context Text Styling**: Improved mark highlights with gradient backgrounds

#### Checker Accuracy Improvements
- **GRM002 (Capitalize I)**: Fixed critical false positives matching 'i' inside words like "which" or "verify"
- **Grammar Checker v2.6.0**: Case-sensitive lowercase 'i' detection pattern
- **Punctuation Checker v2.7.0**: Filters TOC/table of contents entries to reduce false positives
- **Prose Linter v1.1.0**: Nominalization exceptions for 40+ technical terms (documentation, verification, etc.)
- **Enhanced Passive Checker**: Added 60+ adjectival participles (prohibited, permitted, mandated, etc.)
- **Fragment Checker**: Added 100+ imperative verb indicators for technical documentation
- **Base Checker v2.5.0**: Word boundary validation for single-character matches

#### Data Management (Settings)
- **New Data Management Tab**: Clear Scan History, Clear Role Dictionary, Clear Learning Data
- **Factory Reset**: Complete reset option to restore tool to defaults
- **API Endpoints**: `/api/data/clear-roles`, `/api/data/factory-reset`, `/api/data/stats`

#### Test Suite Updates
- Version expectations updated from 3.3.0 to 4.0.0
- All 325+ tests passing

---

## [3.4.0] - 2026-02-03

### Added - Maximum Coverage Suite
Comprehensive expansion adding 23 new offline-only checkers for style consistency, clarity, procedural writing, document quality, and compliance validation. **All solutions are 100% offline-capable for air-gapped network deployment.**

#### Style Consistency Checkers (6 new)
- **`style_consistency_checkers.py`** - Style guide compliance validation
  - `HeadingCaseConsistencyChecker` - Validates consistent heading capitalization (title case, sentence case, all caps)
  - `ContractionConsistencyChecker` - Detects mixed contraction usage ("don't" vs "do not")
  - `OxfordCommaConsistencyChecker` - Validates serial/Oxford comma consistency
  - `ARIProminenceChecker` - Automated Readability Index assessment
  - `SpacheReadabilityChecker` - Spache formula for basic audience readability
  - `DaleChallEnhancedChecker` - Enhanced Dale-Chall with full 3000-word list

#### Clarity Checkers (5 new)
- **`clarity_checkers.py`** - Writing clarity improvements
  - `FutureTenseChecker` - Flags "will display" patterns (prefer present tense)
  - `LatinAbbreviationChecker` - Warns about i.e., e.g., etc., et al.
  - `SentenceInitialConjunctionChecker` - Flags And, But, So at sentence start
  - `DirectionalLanguageChecker` - Flags "above", "below", "left", "right" (content may move)
  - `TimeSensitiveLanguageChecker` - Flags "currently", "now", "recently" (content ages)

#### Enhanced Acronym Checkers (2 new)
- **`acronym_enhanced_checkers.py`** - Advanced acronym validation
  - `AcronymFirstUseChecker` - Enforces acronym definition on first use
  - `AcronymMultipleDefinitionChecker` - Flags acronyms defined multiple times

#### Procedural Writing Checkers (3 new)
- **`procedural_writing_checkers.py`** - Procedural/instructional writing quality
  - `ImperativeMoodChecker` - Validates procedural steps use imperative mood
  - `SecondPersonChecker` - Prefers "you" over "the user" for direct address
  - `LinkTextQualityChecker` - Flags "click here" and vague link text

#### Document Quality Checkers (4 new)
- **`document_quality_checkers.py`** - Document structure validation
  - `NumberedListSequenceChecker` - Validates numbered lists are sequential (1, 2, 3 not 1, 2, 4)
  - `ProductNameConsistencyChecker` - Validates product name capitalization (JavaScript not Javascript)
  - `CrossReferenceTargetChecker` - Validates Table 5, Figure 3 references point to existing targets
  - `CodeFormattingConsistencyChecker` - Flags unformatted code elements and commands

#### Compliance Checkers (3 new)
- **`compliance_checkers.py`** - Aerospace/defense compliance validation
  - `MILStd40051Checker` - MIL-STD-40051-2 technical manual compliance
  - `S1000DBasicChecker` - S1000D/IETM structural validation
  - `AS9100DocChecker` - AS9100D documentation requirements

#### Data Files (6 new)
- **`data/dale_chall_3000.json`** - Full 2949-word Dale-Chall easy word list
- **`data/spache_easy_words.json`** - 773-word Spache formula word list
- **`data/product_names.json`** - 250+ product/technology name capitalizations
- **`data/mil_std_40051_patterns.json`** - MIL-STD-40051-2 compliance patterns and rules
- **`data/s1000d_basic_rules.json`** - S1000D Issue 5.0 structural requirements
- **`data/as9100_doc_requirements.json`** - AS9100D documentation requirements

#### Integration
- All 23 checkers integrated into `core.py` with option mappings for UI checkbox control
- Factory functions for bulk checker registration
- Graceful fallback when data files not found

#### Testing
- **`tests/test_v340_checkers.py`** - 42 unit tests for all new checkers
- Integration tests verifying checkers load in core.py
- Data file validation tests

### Changed
- Total checker count: 84 (61 existing + 23 new)
- Version updated to 3.4.0

---

## [3.3.0] - 2026-02-03

### Added - Maximum Accuracy NLP Enhancement Suite
Comprehensive enhancement to achieve near-100% accuracy for role extraction, acronym detection, grammar checking, and all document analysis capabilities. **All solutions are 100% offline-capable for air-gapped network deployment.**

#### Phase 1: Technical Dictionary System
- **`technical_dictionary.py`** - Master dictionary with 10,000+ embedded terms
  - Aerospace/defense terminology (1,200+ terms)
  - Government contracting vocabulary
  - Software/IT terminology
  - Technical corrections (500+ misspelling → correction mappings)
  - Standard acronyms with expansions (300+ aerospace/defense acronyms)
  - Proper nouns (companies, programs, standards)
- **Features:**
  - `is_valid_term()` - Case-insensitive term validation
  - `get_correction()` - Spelling correction lookup
  - `get_acronym_expansion()` - Acronym expansion with domain tagging
  - `add_custom_term()` / `remove_custom_term()` - Custom term management
  - `suggest_similar()` - Levenshtein distance-based suggestions
  - `search_terms()` - Regex/substring search
  - Singleton pattern with `get_technical_dictionary()`

#### Phase 2: Adaptive Learning System
- **`adaptive_learner.py`** - Unified learning system with SQLite persistence
  - Role adjudication tracking (confirm/reject/deliverable)
  - Acronym decision tracking (accept/expand/ignore)
  - Grammar/style pattern learning
  - Spelling decision tracking
  - Context-aware confidence adjustment
  - Export/import JSON for team sharing
- **Database Schema:**
  - `decisions` table - Individual user decisions with timestamps
  - `patterns` table - Aggregated statistics per pattern
  - Pattern key generators for roles, acronyms, grammar, spelling
- **Integration:**
  - Confidence boosting based on historical decisions
  - Decay function for older decisions (half-life: 30 days)
  - Context similarity matching

#### Phase 3: Enhanced spaCy Pipeline
- **`nlp_enhanced.py`** - Enhanced NLP processor with multiple extraction methods
  - Supports transformer models (`en_core_web_trf` for best accuracy)
  - Supports large models (`en_core_web_lg` as fallback)
  - **EntityRuler** with 100+ aerospace/defense patterns
  - **PhraseMatcher** for fast gazetteer lookups (150+ role phrases)
  - Ensemble extraction combining NER, patterns, and dependency parsing
  - Coreference resolution support (via `coreferee`)
- **`data/aerospace_patterns.json`** - 80+ EntityRuler patterns
  - Aerospace roles (Program Manager, Systems Engineer, etc.)
  - Defense roles (Contracting Officer, COTR, etc.)
  - Deliverable artifacts (CDR, PDR, SRR, etc.)
- **Features:**
  - `ExtractedRole` dataclass with confidence, source, context, modifiers
  - `ExtractedAcronym` dataclass with expansion, definition location, usage count
  - `DocumentAnalysis` with roles, acronyms, requirements, passive voice, ambiguous terms
  - Integration with AdaptiveLearner for confidence boosting
  - Integration with TechnicalDictionary for validation

#### Phase 4: Advanced Checkers
- **`enhanced_passive_checker.py`** - Dependency parsing-based passive voice detection
  - Uses spaCy dependency parsing (not regex)
  - 300+ adjectival participles whitelist (established, required, etc.)
  - Distinguishes true passives from adjectival uses
  - Acceptable context patterns (headings, definitions)
  - Active voice suggestions when possible
- **`fragment_checker.py`** - Syntactic parsing for sentence fragment detection
  - Full subject and finite verb detection via spaCy
  - Handles imperatives, headings, list items
  - Subordinate clause identification
  - Question detection
- **`requirements_analyzer.py`** - Technical document requirements analysis
  - Atomicity checking (one shall per requirement)
  - Testability validation (measurable criteria detection)
  - Escape clause detection (TBD, TBR, TBS, etc.)
  - Ambiguous term flagging (60+ terms: appropriate, adequate, etc.)
  - Modal verb consistency (shall/will/must analysis)
  - Requirement structure validation

#### Phase 5: Terminology & Cross-Reference Validation
- **`terminology_checker.py`** - Terminology consistency checking
  - Spelling variant detection (backend/back-end/back end)
  - British/American English consistency (100+ word pairs)
  - Abbreviation consistency (config/configuration)
  - Capitalization consistency
  - Hyphenation consistency
- **`cross_reference_validator.py`** - Document cross-reference validation
  - Section reference validation (Section 1.1, etc.)
  - Table/Figure reference validation
  - Requirement ID validation (REQ-001, SYS-123, etc.)
  - Broken reference detection
  - Unreferenced item detection
  - Reference format consistency checking

#### Phase 6: Integration, Testing & Documentation
- **`nlp_integration.py`** - Integration module for core.py and role_extractor_v3.py
  - Wrapper classes for all v3.3.0 checkers
  - Factory functions for easy module access
  - Status reporting for component availability
  - Integration with adaptive learning for confidence boosting
- **Core.py integration** - v3.3.0 checkers loaded into main review engine
  - 6 new checker options in option_mapping
  - Automatic initialization via nlp_integration module
- **Role Extractor integration** - Enhanced NLP and adaptive learning
  - New `_apply_v330_enhancement()` method for maximum accuracy
  - Confidence boosting from user decisions
  - EntityRuler/PhraseMatcher/transformer support
- **202 new unit tests** across 6 test files:
  - `tests/test_technical_dictionary.py` - 40 tests
  - `tests/test_adaptive_learner.py` - 34 tests
  - `tests/test_nlp_enhanced.py` - 30 tests
  - `tests/test_advanced_checkers.py` - 35 tests
  - `tests/test_terminology_validation.py` - 28 tests
  - `tests/test_nlp_integration.py` - 35 tests
- **All 394 tests passing** (existing 189 + new 202 + 3 e2e fixed)

#### Target Accuracy Improvements
| Category | Previous | Target | Method |
|----------|----------|--------|--------|
| Role Extraction | 56.7% | 95%+ | Transformer NER + EntityRuler + Learning |
| Acronym Detection | 75% | 95%+ | Domain dictionaries + Context analysis |
| Passive Voice | 70% | 88%+ | Dependency parsing (not regex) |
| Grammar (general) | 75% | 92%+ | Full spaCy + Technical dictionary |
| Spelling | 85% | 98%+ | SymSpell + Technical dictionary |
| Requirements Language | 80% | 95%+ | Pattern expansion + Atomicity |
| Terminology Consistency | 70% | 92%+ | Variant detection + Semantic |

#### Offline Package Requirements (Optional)
For maximum accuracy with transformer models:
- spacy 3.7.4 (~10MB)
- en_core_web_trf 3.7.x (~460MB) - Best accuracy
- en_core_web_lg 3.7.x (~746MB) - Fallback
- coreferee 2.4.x (~20MB) - Coreference resolution
- **Total offline package: ~1.2GB additional**

#### Files Added
- `technical_dictionary.py` (~1,200 lines)
- `adaptive_learner.py` (~900 lines)
- `nlp_enhanced.py` (~1,100 lines)
- `enhanced_passive_checker.py` (~450 lines)
- `fragment_checker.py` (~450 lines)
- `requirements_analyzer.py` (~650 lines)
- `terminology_checker.py` (~550 lines)
- `cross_reference_validator.py` (~500 lines)
- `nlp_integration.py` (~800 lines) - Integration module
- `data/aerospace_patterns.json` (80+ patterns)
- `dictionaries/README.md`
- `tests/test_technical_dictionary.py`
- `tests/test_adaptive_learner.py`
- `tests/test_nlp_enhanced.py`
- `tests/test_advanced_checkers.py`
- `tests/test_terminology_validation.py`
- `tests/test_nlp_integration.py` - 35 integration tests

#### Files Modified
- `core.py` - Added v3.3.0 checker loading and option mapping
- `role_extractor_v3.py` - Added `_apply_v330_enhancement()` method
- `tests/test_e2e_comprehensive.py` - Updated version expectations

---

## [3.2.5] - 2026-02-03

### Improved - Role Extraction Accuracy Overhaul
Major improvements to role extraction accuracy, reducing false positives by 78% and improving overall accuracy from 36.7% to 56.7%.

#### Phone Number & Numeric Filtering
- Filter phone patterns (###-####, (###), ###.###.####)
- Reject candidates starting with digits
- Reject candidates with >30% numeric characters
- Filter ZIP code patterns (#####, #####-####)

#### Acronym Extraction Enhancement
- Acronyms in parentheses now extracted with roles (e.g., "Project Manager (PM)" extracts PM as variant)
- Extended pattern to support 6-word role names and & in acronyms (e.g., "IV&V")
- NLP extraction captures acronyms from context
- Automatic acronym map population for discovered acronyms

#### False Positive Filtering
- Filter run-together words from PDF extraction (e.g., "Byasafetydepartment")
- Filter slash-separated alternatives (e.g., "Owner/Manager")
- Filter section headers (e.g., "C. Scalability", "1.2 Overview")
- Filter address/location patterns (e.g., "Suite 670", "Atlanta Federal Center")
- Filter "Other X" and "Own X" patterns
- More conservative NLP override - requires role indicators to trust high-confidence NLP

#### New Role Definitions
- 25+ FAA/Aviation-specific roles (accountable executive, certificate holder, flight crew, pilot in command, etc.)
- 25+ OSHA/Safety-specific roles (process safety coordinator, plant manager, shift supervisor, emergency coordinator, etc.)

#### Single-Word Exclusions Expanded
- Added 20+ exclusions: user, owner, chief, team, group, labor, section, center, division, office, department, authority, contractor, vendor, stakeholder, evaluator, operator, objectives, scalability

#### Validation Improvements
- Maximum length validation (>60 chars rejected)
- Location/address pattern detection and rejection
- Role indicator requirement for NLP confidence override

#### Test Results
- Total roles extracted: 134 → 69 (removed noise)
- False positives: 9 → 2 (78% reduction)
- Accuracy: 36.7% → 56.7% (54% improvement)

#### Files Modified
- `role_extractor_v3.py` (v3.2.5) - All filtering and validation improvements
- `nlp_utils.py` (v1.1.2) - NLP-side filtering for run-together words, section headers
- `version.json` - Updated changelog
- `docs/TWR_SESSION_HANDOFF.md` - Updated documentation

---

## [3.2.4] - 2026-02-03

### Added - Enhanced Analyzers Integration
Five new NLP-based analysis modules integrated into the core review engine.

#### New Modules
- `semantic_analyzer.py` - Sentence-Transformers for semantic similarity
- `acronym_extractor.py` - Schwartz-Hearst algorithm for acronym extraction
- `prose_linter.py` - Vale-style rules for technical writing
- `structure_analyzer.py` - Document structure and cross-reference analysis
- `text_statistics.py` - Comprehensive readability and text metrics

#### Integration Wrapper
- `enhanced_analyzers.py` - BaseChecker-compatible wrapper for all 5 modules
- Option mappings for UI checkbox control in `core.py`
- Metrics capture in post-processing section

#### New API Endpoints
- `/api/analyzers/status` - Get availability of all enhanced analyzers
- `/api/analyzers/semantic/similar` - Find similar sentences
- `/api/analyzers/acronyms/extract` - Extract acronyms
- `/api/analyzers/statistics` - Get text statistics
- `/api/analyzers/lint` - Prose quality checking

#### NLP Processor Improvements (v1.1.0)
- Better noun chunk analysis using spaCy's linguistic features
- Compound noun detection for multi-word roles
- Passive voice subject detection for roles
- Role-verb association detection (approve, review, coordinate, etc.)
- Enhanced confidence scoring based on POS tags
- Sentence-based context extraction
- 45+ new role suffixes and modifiers for aerospace/defense
- Org unit indicators (directorate, center, facility, etc.)
- Fuzzy matching to boost existing roles found by NLP

---

## [3.2.3] - 2026-02-03

### Fixed - Multiple Bug Fixes
- BUG-M09: HTML export properly escapes URLs and handles None values
- BUG-M07: Soft 404 detection less aggressive
- BUG-M23: Version numbers synchronized across all UI components
- BUG-M26: Duplicate element IDs in troubleshooting panel renamed
- BUG-M25: Troubleshooting export buttons now properly find their elements

---

## [3.2.2] - 2026-02-03

### Fixed - Role Dictionary Integration
Adjudicated roles now properly persist to the role dictionary database and feed back into the extraction engine.

#### Bug Fixes
- **Dictionary Save**: Adjudicated roles now saved via both primary `/api/roles/adjudicate` and backup `/api/roles/dictionary` endpoints
- **List Refresh**: Adjudicated roles properly removed from pending list - the adjudication list refreshes correctly after each action
- **State Sync**: `AdjudicationState.decisions` Map now updated with all required fields (confidence, notes, suggestedType)
- **Graph Sync**: `State.adjudicatedRoles` properly updated for graph visualization consistency
- **Delete Icon**: Role Dictionary delete button now shows proper trash icon instead of red box
- **Action Buttons**: Dictionary table action buttons (edit, toggle, delete) styled correctly
- **Status Badges**: Active/inactive status badges now display properly in dictionary table

#### Role Extraction Engine Integration
The role dictionary now feeds back into the extraction engine for continuous improvement:
- **Confirmed Roles** (`is_active=1, is_deliverable=0`): Added to `known_roles` → 0.95 confidence boost
- **Rejected Roles** (`is_active=0, source='adjudication'`): Added to `false_positives` → Excluded from future extraction
- **Loading Methods**: `_load_dictionary_roles()` and `_load_rejected_roles()` in `role_extractor_v3.py`

#### Technical Details
- Added `addRoleToDictionaryBackup()` function as fallback if primary API fails
- Enhanced `syncWithRolesAdjudication()` with complete field mapping
- Added comprehensive logging for debugging adjudication flow
- Both confirmed and rejected roles now tracked in dictionary (rejected with `is_active=false`)

#### Files Modified
- `static/js/features/role-source-viewer.js` (v3.2.2) - Enhanced adjudication handlers with backup save
- `static/css/features/roles-studio.css` - Fixed button and badge styling in dictionary table

---

## [3.2.1] - 2026-02-03

### Fixed - Per-Role Adjudication Persistence
Each role now tracks its own adjudication state independently.

#### New API Endpoints
- `POST /api/roles/adjudicate` - Saves adjudication decision to role dictionary
- `GET /api/roles/adjudication-status` - Retrieves saved adjudication state for a role
- `POST /api/roles/update-category` - Updates role category classification

#### Role Extractor Learning
- Rejected roles automatically added to `false_positives` for future extraction runs
- Confirmed roles added to `known_roles` for higher confidence matching
- Role extraction becomes smarter over time through adjudication feedback

#### Files Modified
- `app.py` - Added adjudication API endpoints
- `scan_history.py` - Added `get_role_by_name()` method
- `role_extractor_v3.py` - Added `_load_rejected_roles()` method and learning integration

---

## [3.2.0] - 2026-02-03

### Added - Role Source Viewer with Adjudication Controls
Unified role review interface that displays actual document text with highlighted role mentions, enabling informed adjudication decisions.

#### Role Source Viewer Enhancements (ENH-005)
- **Full Document Text Display**: View complete document text with all role mentions highlighted in orange
- **Multi-Document Navigation**: Navigate between documents where the role appears
- **Occurrence Navigation**: Step through each mention with Prev/Next buttons and click-to-jump
- **Historical Document Support**: Retrieves document text from `results_json.full_text` in scan history
- **New API Endpoint**: `GET /api/scan-history/document-text?filename=<name>` for historical text retrieval

#### Adjudication Panel
- **Status Indicator**: Shows current adjudication state (Pending Review, Confirmed, Deliverable, Rejected)
- **Three Action Buttons**:
  - ✓ **Confirm Role** (green) - Mark as a valid role
  - ★ **Mark Deliverable** (blue) - Flag as deliverable/artifact for export
  - ✗ **Reject** (red) - Mark as not a valid role
- **Category Dropdown**: Classify role type (Role, Management, Technical, Organization, Custom)
- **Notes Textarea**: Add notes about adjudication decisions
- **Visual Feedback**: Button highlights and status badge updates on action

#### Files Modified
- `static/js/features/role-source-viewer.js` (v3.1.0) - Added adjudication section with handlers
- `static/css/features/doc-compare.css` - Fixed modal sizing constraints
- `app.py` - Added `/api/scan-history/document-text` endpoint
- `templates/index.html` - Cache-busting version updates

### Fixed - Document Compare Modal Sizing
- Modal now properly displays at 95vw × 90vh with max-width 1800px
- Added `!important` overrides to ensure modal-content constraints are respected
- Fixed compacted modal display issue

### Changed - Browser Cache Management
- Script loading now includes version query strings (`?v=3.1.0`) for cache-busting
- Ensures users see latest code updates without manual cache clearing

---

## [3.1.9] - 2026-02-02

### Added - Clickable Role Names with Source Viewer
Role names throughout the Roles & Responsibilities Studio are now clickable to view source context.

#### Integration Points
- **Overview Tab**: Top roles list - click role name to view source documents
- **Details Tab**: Role cards - click role name in header to view source context
- **Cross-Reference Tab**: Role rows in matrix - click to see document occurrences
- **RACI Matrix Tab**: Role chips in fallback view - click to view source context
- **Adjudication Tab**: Role names in review list - click to see where role was extracted

#### How It Works
- Clicking a role name opens the Role Source Viewer modal
- Shows all document occurrences with highlighted context
- Allows navigation between occurrences with prev/next buttons
- Leverages existing `TWR.RoleSourceViewer` module via `data-role-source` attribute

#### Backend Support
- **New API Endpoint**: `GET /api/roles/context?role=<name>` - Returns role context with all occurrences
- **New DB Method**: `ScanHistoryDB.get_role_context()` - Fetches role details from scan history
- **Enhanced RoleSourceViewer**: Now fetches from API when State.roles is empty
- **Graceful Fallback**: Shows helpful message when no context is available

#### Files Modified
- `static/js/roles-tabs-fix.js` - Added `data-role-source` attributes to role names
- `static/js/features/role-source-viewer.js` - Added async API fetch support
- `scan_history.py` - Added `get_role_context()` method
- `app.py` - Added `/api/roles/context` endpoint

### Added - Molten Progress Bar System
Scalable Rive-inspired molten orange progress bars integrated throughout the application.

#### Molten Progress Component
- **4 Size Variants**: mini (4px), small (8px), medium (16px), large (28px)
- **3 Color Themes**: orange (default), blue, green
- **Optional Features**: reflection glow, trailing effect
- **Molten Gradient**: Deep orange → amber → yellow → white-hot leading edge
- **Glowing Orb**: White-hot center with pulsing animation at progress edge
- **Indeterminate Mode**: Contained animation for unknown-duration operations

#### Integration Points
- **Batch Document Rows** (`app.js`) → `molten-mini` (4px) for individual file progress
- **Loading Overlay** (`index.html`) → `molten-medium` with reflection (16px)
- **Hyperlink Validator** (`hyperlink-visualizations.js`) → `molten-small` with reflection (8px)
- **Cinematic Progress Modal** (`cinematic-progress.js`) → `molten-small` with reflection (8px)

#### Files Added
- `static/css/features/molten-progress.css` - Scalable progress bar styles (457 lines)
- `static/js/features/molten-progress.js` - JavaScript API for dynamic progress bars

#### API
```javascript
// Create progress bar
const progress = MoltenProgress.create('#container', {
  size: 'medium',      // mini | small | medium | large
  color: 'orange',     // orange | blue | green
  withReflection: true,
  withTrail: false,
  indeterminate: false,
  initialProgress: 0
});

// Update progress (0-1)
progress.setProgress(0.5);

// Mark complete (brightens bar)
progress.complete();

// Reset to 0
progress.reset();

// Remove from DOM
progress.destroy();
```

### Changed - AEGIS Cinematic Loader
Enhanced the cinematic loader with Rive-inspired molten theme and critical bug fix.

#### Visual Enhancements (v2.4)
- **Molten Color Palette**: Deep orange → amber → yellow → white-hot gradient
- **Enhanced Orb**: White-hot core with intense orange/amber bloom
- **Reflection Glow**: Rive-style glow below the progress bar
- **Particle Theme**: Orange/amber dominated colors for particles and sparks

#### Bug Fix - Click Blocking
- **Issue**: After fade-out, loader remained at z-index 99999 with pointer-events enabled, blocking all UI clicks
- **Fix**: Added `onComplete` callback to set `pointer-events: none` and `display: none` after fade animation

### Removed - Initial Startup Loader
Removed the full-screen AEGIS loader from initial app startup since the app loads fast enough without it.

#### Rationale
- App initialization completes in <500ms on typical hardware
- Loading screen was barely visible before fade-out
- Removed unnecessary visual overhead for fast-loading app

#### Changes
- Removed AEGIS loader HTML from `index.html` (kept hidden stub for compatibility)
- Removed `updateLoaderProgress()` and `completeLoader()` functions from `app.js`
- Simplified `DOMContentLoaded` handler

#### Note
The cinematic loader system (`CinematicLoader`) is still available for use in batch processing and other long-running operations where visual feedback is valuable.

---

## [3.1.8] - 2026-02-02

### Added - AEGIS Cinematic Loader
Full-screen startup animation that displays during initial app load, providing a premium experience while modules initialize.

#### Visual Elements
- **Particle Background** - Canvas with 170 animated particles (blue + gold warm mix)
- **Grid Overlay** - Subtle tech grid pattern at 16% opacity
- **28px Progress Bar** - Thick cinematic bar with multi-color gradient fill
- **Sheen Sweep** - Continuous diagonal shine animation across the bar
- **Progress Orb** - Glowing sphere that tracks progress edge position
- **Trailing Glow** - Fading tail behind the orb (90-240px adaptive length)
- **Vignette** - Cinematic edge darkening for focus
- **Film Grain** - Subtle animated noise overlay for cinematic texture

#### Integration
- Progress updates at key initialization stages:
  - 10% - Initializing security (CSRF)
  - 20% - Checking capabilities
  - 30% - Loading version info
  - 40% - Building interface
  - 55% - Binding events
  - 70% - Configuring shortcuts
  - 85% - Loading settings
  - 95% - Restoring session
  - 100% - Complete (fade out)
- Smooth fade-out after completion
- Reduced motion support for accessibility
- Graceful fallback if GSAP unavailable

#### Files Added
- `static/js/features/cinematic-loader.js` - Loader module (258 lines)
- `static/css/features/cinematic-loader.css` - Loader styles (217 lines)
- `static/images/aegis_loader_28px.svg` - Rive-ready SVG asset

#### API
```javascript
// Mount loader
const loader = CinematicLoader.mount('#aegisLoader', { fps: 30, maxDpr: 1.5 });

// Update progress (0-1)
loader.setProgress(0.5);

// Update status text
loader.setStatus('Loading modules');

// Complete with cinematic flash + fade
loader.complete();

// Error shake animation
loader.error();

// Cleanup
loader.destroy();
```

## [3.1.7] - 2026-02-02

### Enhanced - Cinematic Progress Animation Boost
Major visual upgrade to the cinematic progress animation system with theme-specific effects and milestone celebrations.

#### New Effects
- **Particle Trails** - 30% of particles now leave fading motion trails as they move
- **Particle Connections** - Web-like lines connect nearby particles (configurable distance: 80px)
- **Milestone Celebrations** - Burst effects at 25%, 50%, 75%, and 100% progress
  - Expanding rings with theme-colored glow
  - 40 burst particles (100 at completion)
  - "COMPLETE!" text animation at 100%
- **Grand Finale** - 80 burst particles + container scale pulse at completion

#### Theme-Specific Effects
- **Circuit Theme**:
  - Lightning bolts randomly strike toward progress position
  - White electrical arcs with orange glow
  - ~2% chance per frame when progress > 5%
- **Cosmic Theme**:
  - 50 twinkling stars with varying brightness
  - Larger stars have cross-shine effect
  - Stars drift slowly toward progress
- **Fire Theme**:
  - 30 rising ember particles
  - Wobble animation with gravity
  - Gradient from white core to flame color
- **Matrix Theme**:
  - 25 data streams (up from 20)
  - Depth effect - streams vary in size/brightness
  - 6-character trailing effect per stream
  - Full katakana character set (46 chars)
  - Speed boost near progress line

#### Enhanced Trail System
- Energy trail now spawns 8 sparks continuously
- Sparks have gravity and fade out
- Ripple effect around leading orb (3 rings)
- Larger orb (18px) with multi-color gradient
- Inner white-hot trail overlay

#### Technical Changes
- Extended CONFIG with: `particleTrailLength`, `connectionDistance`, `milestones`, `sparkCount`, `lightningFrequency`, `starCount`, `emberCount`, `matrixStreamCount`
- New classes: `Spark`, `LightningBolt`, `Star`, `Ember`, `MilestoneCelebration`
- Added `onMilestone` callback option
- Theme switching now reinitializes theme-specific effects
- `cinematic-progress.js` expanded to 1545 lines

## [3.1.6] - 2026-02-02

### Added - Cinematic Progress Animation System
- **Lottie + GSAP + Rive + Canvas Integration** - Multi-library cinematic animation stack for batch progress:
  - **Layer 1: GSAP (72KB)** - Timeline orchestration and smooth tweening engine
  - **Layer 2: Lottie (305KB)** - After Effects JSON animations with frame scrubbing
  - **Layer 3: Rive (164KB)** - State machine animations with progress input binding
  - **Layer 4: Canvas 2D** - Custom particle systems, energy trails, data streams
  - **Layer 5: CSS Effects** - Glow, blur, gradients as enhancement layer
- **5 Cinematic Themes** with distinct visual styles:
  - **Circuit** (default) - Orange/gold tech aesthetic with circuit-inspired particles
  - **Cosmic** - Purple/cyan space theme with ethereal glow effects
  - **Matrix** - Green terminal aesthetic with falling data stream effect
  - **Energy** - Teal power theme with electric trail effects
  - **Fire** - Red/orange flame theme with ember particles
- **Theme Selector** - Clickable theme buttons with localStorage persistence
- **Particle System** - 150+ animated particles with theme-specific colors and behaviors
- **Energy Trail** - Glowing path that follows progress bar tip with 15-point history
- **Data Stream Effect** - Matrix-style falling characters (configurable per theme)
- **CDN Fallbacks** - Local-first with automatic CDN fallback for air-gapped compatibility

### Technical
- Created `static/js/features/cinematic-progress.js` (825 lines) - Main animation module
- Created `static/css/features/cinematic-progress.css` (782 lines) - Theme styles and backward-compatible aliases
- Downloaded `static/js/vendor/gsap.min.js` (72KB) - GSAP animation library
- Downloaded `static/js/vendor/rive.min.js` (164KB) - Rive runtime
- Updated `templates/index.html` - Added script includes with CDN fallbacks, replaced circuit-progress with cinematic-batch-progress
- Updated `static/js/app.js` - Integrated CinematicProgress into batch processing, added theme switching

### Architecture
```
Animation Stack Data Flow:
┌─────────────────────────────────────────────────────────────┐
│  User Progress Update (0-100%)                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  CinematicProgressBar.setProgress(value)                     │
│    ├── Lottie: animationInstance.goToAndStop(frame)          │
│    ├── Rive: stateMachine.input('progress').value = value    │
│    ├── GSAP: timeline.progress(value) + glow tween           │
│    ├── Canvas: particle positions + trail update             │
│    └── CSS: --progress custom property update                │
└─────────────────────────────────────────────────────────────┘
```

## [3.1.5] - 2026-02-02

### Added - Circuit Board Progress UI Enhancements
- **Enhanced Batch Progress Display** - Complete visual overhaul of batch processing UI:
  - Dark navy/black background for dramatic contrast
  - Orange/gold glowing progress bar with intense glow effects
  - Animated corner decorations with gold accents
  - Subtle red accent dots in corners
  - Smooth scanning line animation
- **Time Tracking Features**:
  - Elapsed time counter (MM:SS format)
  - Estimated time remaining calculation
  - Processing speed display (docs/min)
- **Animated Percentage Counter** - Smooth counting animation with pulse effect
- **Real-time Status Labels** - Per-document status: QUEUED → UPLOADING → ANALYZING → DONE
- **Sound Notification** - Optional completion sound (toggleable via speaker icon)
- **Sound Toggle Button** - Persistent preference saved to localStorage

### Fixed
- **Dual File Dialog Bug** - Fixed issue where clicking "Select Files" or "Select Folder" would trigger both file dialogs
  - Moved hidden file inputs outside the dropzone to prevent event bubbling
  - Added `e.preventDefault()` to button click handlers

### Changed
- Simplified circuit board visual effects (removed overly complex animated traces and bokeh particles)
- Progress bar now uses intense orange (#ff6600 to #ffb347) gradient with multi-layer glow
- Scan line simplified to subtle gold sweep effect

### Technical
- Updated `templates/index.html` - Reorganized batch modal structure, moved file inputs outside dropzone
- Updated `static/css/components.css` - New circuit board CSS variables, enhanced progress fill styling
- Updated `static/js/app.js` - Added time tracking, animated percentage, sound notification functions

## [3.1.4] - 2026-02-02

### Added - ENH-010: Clean Upgrade Path
- **User Data Preservation** - Automatic backup/restore of user data during upgrades
- **Version Comparison** - Compare installed version with update packages (.zip)
- **Update Package Support** - Apply full version updates from .zip files
- **New API Endpoints** - `/api/updates/version`, `/check-package`, `/backup-userdata`, `/restore-userdata`, `/apply-package`
- **USER_DATA_PATHS** - Configurable list of files/directories to preserve (scan_history.db, settings, dictionaries)
- **Rollback on Failure** - Automatic rollback if upgrade fails

### Changed
- Updated `update_manager.py` from v1.4 to v1.5 with ENH-010 features
- Test suite expanded to 75 tests (all passing)

## [3.1.3] - 2026-02-02

### Added - ENH-005, ENH-006, ENH-009
- **Universal Role Source Viewer (ENH-005)** - View role context in source documents from any location
  - Modal-based viewer with multi-document navigation
  - Multi-occurrence support within documents
  - Context highlighting with surrounding text
- **Statement Forge Review Mode (ENH-006)** - Review statements with source context
  - Navigate between statements (Previous/Next)
  - Approve/Reject/Save actions
  - Create statements from text selection
  - Keyboard shortcuts (←→ nav, S=save, A=approve, R=reject, Esc=close)
- **Comprehensive Logging System (ENH-009)**
  - Backend: `diagnostics.py` with CircularLogBuffer, AsyncLogQueue, SamplingLogger
  - Frontend: `frontend-logger.js` with API call timing, action tracking
  - Performance timer decorator and sampling for high-frequency events
- **Statement Model Extended** - Source context fields (source_document, char offsets, context, page, section)

### Changed
- Test suite expanded from 48 to 68 tests

## [3.1.2] - 2026-02-02

### Fixed - Bug Fixes
- **BUG-C01**: Expanded passive voice FALSE_POSITIVES from ~38 to 300+ words
- **BUG-C02**: Diagnostic export timeout increased to 60s, errors limited to 500
- **BUG-M10**: Hyperlink flags now include the actual broken URL in error messages
- **BUG-M14**: Document comparison shows helpful message when no documents available
- **BUG-M15**: Portfolio batch categorization time window reduced from 5min to 30sec
- **BUG-M16**: Poll frequency increased from 500ms to 2000ms to prevent rate limiting
- **BUG-M18**: Sidebar collapsed width reduced from 56px to 44px
- **BUG-M19**: Hyperlink validator history now properly logs with excluded/duration_ms fields
- **BUG-M20**: Carousel dark mode styling added
- **BUG-M21**: Heatmap dark mode contrast improvements
- **BUG-M22**: Docling status check uses AbortController with 5-second timeout
- **BUG-M27**: Print section null reference check added
- **BUG-M28**: Scan profiles load failure null check added
- **BUG-M29**: SortableJS now loaded locally to avoid CSP blocking
- **BUG-M30**: HelpContent click handler uses requestAnimationFrame for performance
- **BUG-L10**: Passive event listeners added to touch/scroll handlers

### Added - Enhancements
- **ENH-001**: Role consolidation engine with 25+ built-in rules, fuzzy matching
- **ENH-003**: Graph export module for PNG/SVG export of Chart.js and D3.js
- **ENH-004**: Role comparison module for multi-document side-by-side analysis
- **ENH-008**: NLP integration (spaCy) for improved role/deliverable/acronym detection

### Changed
- Test suite expanded from existing to 48 tests

## [3.0.126] - 2026-02-01

### Added
- **3D Animated Progress Bar** - Stunning new progress bar for Hyperlink Validator with:
  - Dark cosmic purple/blue gradient background with animated starfield
  - Flowing purple-blue animated gradient fill with glow effects
  - Floating particle system (orbs and sparkles) with smooth animations
  - Glowing edge effect at progress bar tip
  - Pulsing green status indicator
  - 3D depth with shadows and layered effects
- **3D Animated Loading Overlay** - Matching visual treatment for main review page loading:
  - Glass-effect card with blur backdrop
  - Same animated starfield background
  - 3D progress bar with particles
  - Glowing orb accents creating depth
- **Domain Health Carousel in Review Tab** - The 3D domain carousel now also appears in the review tab's hyperlinks panel when documents contain validated links
- **Light/Dark Mode Support** - Both progress bars fully adapt to selected theme:
  - Light mode: Clean white/blue theme with subtle particles
  - Dark mode: Cosmic purple/blue theme with intense glows

### Changed
- **Upload File Now Default Tab** - Hyperlink Validator now opens with "Upload File" as the default tab, with "Paste URLs" as secondary option
- Reorganized tab order in Hyperlink Validator input section

### Improved
- **Windows Compatibility** - File upload handling uses standard Web APIs (FileReader, FormData) with no platform-specific path manipulations
- Progress bar height fixed to 28px with proper min-height to prevent CSS flex shrinking issues
- Enhanced particle animations with varied delays for more organic movement

### Technical
- Updated `templates/index.html` - New 3D progress bar HTML structure with particles, orbs, and streaks
- Updated `static/css/features/hyperlink-validator.css` - Complete progress section rewrite with 3D effects and theme support
- Updated `static/css/components.css` - New 3D loading overlay styles with light/dark mode variants
- Updated `static/js/app.js` - Domain health carousel rendering in review tab hyperlinks panel

## [3.0.122] - 2026-02-01

### Added
- **Persistent Link Exclusions** - URL exclusion rules now stored in SQLite database (survive sessions)
- **Scan History Storage** - Historical hyperlink scans recorded with summary statistics
- **Link History Modal** - New "Links" button in top navigation opens history modal with two tabs:
  - **Exclusions Tab** - Add, edit, enable/disable, delete URL exclusion patterns
  - **Scans Tab** - View historical scans, see details, clear old records
- New API endpoints: `/api/hyperlink-validator/exclusions/*` and `/history/*`
- `HyperlinkValidatorStorage` class for database operations
- `LinkHistory` JavaScript module for UI management
- Match types: contains, exact, prefix, suffix, regex

### Changed
- `HyperlinkValidatorState` now loads exclusions from database on init (falls back to localStorage)
- Completed scans automatically recorded to database via `recordScanToHistory()`

## [3.0.121] - 2026-02-01

### Fixed
- **Portfolio "Open in Review"** - Button now correctly loads documents with stats bar, analytics, and issues table displaying properly (was showing empty state placeholder)
- Added missing calls to hide empty-state and show stats-bar in `openDocument()` function

### Improved
- **Responsive Hyperlinks Panel** - Changed from fixed heights (300px/150px) to viewport-relative (50vh/25vh)
- **Clickable Hyperlinks** - Users can now click any hyperlink row to open URL in new tab for manual verification
- Added visual hover feedback with external-link icon appearing on hover
- Hyperlink text and error columns now properly flex and shrink

### Added
- Test document `hyperlink_test.docx` with working and broken link examples

## [3.0.120] - 2026-02-01

### Added
- **3D Carousel for Issues by Section** - New rotating carousel view in Document Analytics
- Boxes arranged in horizontal arc with 3D perspective
- Drag-to-spin (continuous rotation while dragging) and slider navigation
- Click on box to filter issues to that section
- Color-coded borders based on issue density (none/low/medium/high)

### Improved
- Visual design: white background, 75x80px boxes, section labels, issue counts
- Touch support for mobile devices
- Dark mode compatibility

## [3.0.119] - 2026-02-01

### Fixed
- **Document Filter Dropdown** - Now correctly filters roles by document in Roles Studio
- Fixed CSS selector bug: `.roles-nav-btn.active` → `.roles-nav-item.active`
- Filter updates Overview stats, Responsibility Distribution chart, and Top Roles list

### Added
- Filter indicator shows "Filtered by: [document]" when active
- Restores previous filter selection when re-opening modal

### Improved
- **Help Modal Sizing** - Now 85vw × 80vh (3/4 screen) with opaque backdrop
- **Statement Forge Help Modal** - Now 80vw × 75vh with matching styling

### Documentation
- **Comprehensive Help Documentation Overhaul** - Major content updates:
  - **Welcome Section** - Enterprise-grade capabilities callout, 8 Core Capabilities cards, file formats, 6 "Where to Start" navigation cards
  - **Roles Studio** - Performance stats (94.7% precision), 8 Key Features cards, Studio Tabs table, Workflow guide
  - **Statement Forge** - 8 Key Features, Workflow guide, Keyboard shortcuts table
  - **Fix Assistant v2** (NEW) - Complete section with Overview, 8 Key Features, Shortcuts, Workflow, Bulk Actions, Pattern Learning, Export Options
  - **Hyperlink Health** (NEW) - What Gets Checked, Validation Results table, HTTP Status Codes reference
  - **Batch Processing** (NEW) - Queue Management, Queue States table, Results View, Export Options
  - **Quality Checkers** - Complete Checker List table (13 modules), Severity Levels, Configuration guide

## [3.0.116] - 2026-02-01

### Fixed
- **BUG-M02**: Batch memory - Files now stream to disk in 8KB chunks instead of loading entirely into memory
- **BUG-M03**: SessionManager growth - Added automatic cleanup thread that runs hourly to remove sessions older than 24 hours
- **BUG-M04**: Batch error context - Full tracebacks now logged for batch processing errors (debug mode shows in response)
- **BUG-M05**: localStorage key collision - Fix Assistant progress now uses unique document IDs via hash of filename + size + timestamp
- **BUG-L07**: Batch limit constants - Defined `MAX_BATCH_SIZE` (10) and `MAX_BATCH_TOTAL_SIZE` (100MB) constants

### Added
- `SessionManager.start_auto_cleanup()` method for configurable automatic session cleanup
- `SessionManager.stop_auto_cleanup()` method to halt the cleanup thread
- `SessionManager.get_session_count()` method to check active session count
- `FixAssistantState.generateDocumentId()` function to create collision-free storage keys

### Changed
- Batch upload endpoint now enforces file count and total size limits
- Batch upload/review errors now include full traceback in debug mode

## [3.0.115] - 2026-02-01

### Added
- **Document Type Profiles** - Customize which quality checks are performed for PrOP, PAL, FGOST, SOW, and other document types
- Settings > Document Profiles tab with visual checker grid for each document type
- Custom profiles persist in localStorage (user-specific)
- Select All, Clear All, Reset to Default buttons for profile management
- First-time user prompt to configure document profiles on initial app launch

### Changed
- `applyPreset()` now uses custom profiles when available for document type presets

## [3.0.110] - 2026-02-01

### Added
- **Hyperlink Validator Export** - Export highlighted DOCX with broken links marked in red/yellow/strikethrough
- **Hyperlink Validator Export** - Export highlighted Excel with broken link rows in red background
- API endpoint `/api/hyperlink-validator/export-highlighted/docx`
- API endpoint `/api/hyperlink-validator/export-highlighted/excel`
- "Export Highlighted" button in Hyperlink Validator modal (enabled after file validation)

## [3.0.109] - 2026-01-28

### Fixed
- **Issue #1**: Batch Modal - Now opens correctly (removed inline style override from template)
- **Issue #2**: Hyperlinks - Now extracts HYPERLINK field codes (`<w:fldSimple>`, `<w:instrText>`) in addition to standard `<w:hyperlink>` elements from DOCX files
- **Issue #3**: Acronym Highlighting - Uses word boundary regex (`\b`) to prevent false positives like "NDA" inside "staNDArds"
- **Issue #4**: Fix Assistant Premium - Complete implementation with close button, navigation, keyboard shortcuts, progress tracking, and all action buttons working
- **Issue #5**: Statement Forge - "No document loaded" error fixed with consistent state checks matching `extractStatements()` logic
- **Issue #6**: Scan History - Added missing `/api/scan-history/stats`, `/clear`, `/recall` endpoints
- **Issue #7**: Triage Mode - `State.documentId` now set after fresh review, fixing "Document must be saved to history" error
- **Issue #8**: Document Filter - Now properly populates from scan history
- **Issue #9**: Role-Document Matrix - Improved response validation, handles null/undefined data gracefully
- **Issue #10**: Export Modal Badge Overflow - Badges now wrap and truncate with ellipsis when too long
- **Issue #11**: Comment Placement - Smart quote normalization and multi-strategy text matching (exact → normalized → fuzzy)
- **Issue #12**: Version History - Added missing version entries to help documentation
- **Issue #13**: Updater Rollback - `restoreBackup()` now uses correct `/api/updates/rollback` endpoint, button enable/disable based on backup availability
- **Issue #14**: "No Updates Available" - Proper empty state styling with centered text and checkmark icon
- **Issue #15**: Logo 404 - Fixed missing logo reference (changed from .png to .svg)

### Improved
- Statement extraction patterns expanded with responsibility/accountability/required-to phrases
- Fallback extraction for documents without clear section structure (scans all paragraphs)
- Role-Document Matrix error display with retry button
- Statement Forge modal opens with pre-extracted statements if available
- Fix Assistant keyboard shortcuts with visual feedback (A=accept, R=reject, S=skip, arrows, Escape)

### Added
- `generateGlobalDocumentId()` function for consistent document ID generation
- `/api/scan-history/stats` endpoint for scan history panel
- `/api/scan-history/clear` endpoint for clearing scan history  
- `/api/scan-history/<id>/recall` endpoint for restoring previous scans
- `_parse_field_code_hyperlink()` method for parsing HYPERLINK field codes
- `normalize_quotes()` and `normalize_whitespace()` functions in comment_inserter.py
- `escapeRegex()` helper in renderers.js for safe regex construction
- Fix Assistant Premium CSS enhancements for modal, buttons, progress bar

## [3.0.108] - 2026-01-28

### Fixed
- **BUG-009**: Document filter dropdown now populates with scanned document names
- Added `source_documents` field to role extraction data for proper filtering

## [3.0.107] - 2026-01-28

### Fixed
- **BUG-007**: Role Details tab now shows `sample_contexts` from documents
- **BUG-008**: Role-Doc Matrix shows helpful guidance when empty instead of stuck on "Loading"

### Improved
- Matrix tab explains how to populate cross-document data
- Better empty state messaging throughout Role Studio

## [3.0.106] - 2026-01-28

### Fixed
- **BUG-006**: Fix Assistant v2 Document Viewer was empty (0 paragraphs) - `paragraphs`, `page_map`, and `headings` now returned from `core.py` review results
- **BUG-M01**: Remaining deprecated `datetime.utcnow()` calls in `config_logging.py` replaced with `datetime.now(timezone.utc)`

## [3.0.105] - 2026-01-28

### Fixed
- **BUG-001**: Report generator API signature mismatch - `generate()` now returns bytes when `output_path` not provided
- **BUG-002**: Learner stats endpoint now uses standard `{success, data}` response envelope
- **BUG-003**: Acronym checker mode handling - strict mode now properly flags common acronyms
- **BUG-004**: Role classification tiebreak - "Report Engineer" now correctly classified as role
- **BUG-005**: Comment pack now includes location hints from `hyperlink_info`

### Maintenance
- Updated deprecated `datetime.utcnow()` calls to `datetime.now(timezone.utc)` (partial - completed in 3.0.106)

## [3.0.104] - 2026-01-28

### Fixed
- Fix Assistant v2 load failure - BodyText style conflict resolved
- Logger reserved keyword conflict in static file security endpoint

### Tests
- Updated test expectations for static file security responses
- Fixed CSS test locations for modularized stylesheets

## [3.0.103] - 2026-01-28

### Security
- innerHTML safety audit - all 143 usages documented and verified (Task A)

### Refactored
- CSS modularized into 10 logical files for maintainability (Task B)

### Quality
- Test suite modernized with docstrings (Task C)
- Exception handling refined with specific catches (Task D)
- Added comprehensive code comments throughout JavaScript

### Tests
- Added `TestFixAssistantV2API` class
- Added `TestBatchLimits` class  
- Added `TestSessionCleanup` class

## [3.0.102] - 2026-01-28 *(reconstructed)*

### Added
- Intermediate stabilization release between 3.0.101 and 3.0.103

## [3.0.101] - 2026-01-28

### Refactored
- Standardized API error responses with correlation IDs (ISSUE-004)
- Centralized document type detection into `get_document_extractor()` helper (ISSUE-008)
- Centralized user-facing strings into `STRINGS` constant (ISSUE-009)

### Documentation
- Added comprehensive JSDoc comments to feature modules (ISSUE-010)
- Completed remaining 4 of 12 issues from comprehensive code review audit

## [3.0.100] - 2026-01-28

### Security
- Added ReDoS protection with safe regex wrappers (ISSUE-001)
- Enhanced input validation on learner dictionary API (ISSUE-005)

### Performance
- Enabled WAL mode for SQLite with `busy_timeout` for concurrent access (ISSUE-002)
- Added file size validation for large document protection (ISSUE-003)

### Fixed
- `State.entities` now properly reset on new document load (ISSUE-006)
- Added `cleanup()` function to `FixAssistantState` to prevent memory leaks (ISSUE-007)
- Addressed 7 of 12 issues from comprehensive code review audit

## [3.0.99] - 2026-01-28 *(reconstructed)*

### Added
- Intermediate release with bug fixes between 3.0.98 and 3.0.100

## [3.0.98] - 2026-01-28

### Fixed
- **BUG-001**: Double browser tab on startup
- **BUG-002**: Export modal crash
- **BUG-003**: Context highlighting showing wrong text
- **BUG-004**: Restored hyperlink status panel
- **BUG-005**: Version history gaps in Help modal
- **BUG-009**: Restored Role-Document matrix tab

### Improved
- **BUG-006**: Comprehensive `TWR_LESSONS_LEARNED.md` updates
- **BUG-007**: Role Details tab with context preview
- **BUG-008**: Document filter dropdown in Role Studio

## [3.0.97] - 2026-01-28

### Added - Fix Assistant v2 (Major Feature)
- Two-panel document viewer with page navigation and highlighting
- Mini-map showing document overview with fix position markers
- Undo/redo capability for all review decisions
- Search and filter fixes by text, category, or confidence
- Save progress and continue later (localStorage persistence)
- Learning from user decisions (pattern tracking, no AI)
- Custom dictionary for terms to always skip
- Live preview mode showing changes inline
- Split-screen view (original vs fixed document)
- PDF summary report generation
- Accessibility features (high contrast, screen reader support)
- Enhanced keyboard shortcuts (A=accept, R=reject, S=skip, U=undo)
- Optional sound effects for actions (Web Audio API)
- Rejected fixes exported as document comments with reviewer notes

### Improved
- Export now handles both accepted fixes (track changes) and rejected fixes (comments)

### API
- Added `/api/learner/*` endpoints for pattern learning
- Added `/api/report/generate` endpoint for PDF reports

## [3.0.96] - 2026-01-27

### Added - Fix Assistant v1
- Premium triage-style interface for reviewing automatic fixes
- Keyboard shortcuts (A=accept, R=reject, S=skip, arrows=nav)
- Confidence tiers (Safe/Review/Caution) for each proposed fix
- Context display showing surrounding text with highlighted change
- Before/After comparison with clear visual distinction
- Bulk actions (Accept All Safe, Accept All, Reject All)

### Improved
- Export now uses Fix Assistant selections instead of all fixes
- Progress tracking shows reviewed/total count

### UI
- Premium styling with confidence badges, progress bar, keyboard hints

## [3.0.95] - 2026-01-27

### Fixed
- Version display consistency - all UI components now show same version
- About section simplified - shows only author name
- Heatmap clicking - Category × Severity heatmap now filters issues on click

### Added
- Hyperlink status panel - visual display of checked hyperlinks and validation status

### Improved
- Section heatmap click feedback with toast messages

## [3.0.94] - 2026-01-27 *(reconstructed)*

### Added
- Intermediate release with improvements between 3.0.93 and 3.0.95

## [3.0.93] - 2026-01-27

### Improved - Acronym Detection
- Added 100+ common ALL CAPS words to `COMMON_CAPS_SKIP`
- Added PDF word fragment detection

### Testing
- Reduced false positive acronym flagging by ~55%

## [3.0.92] - 2026-01-27

### Fixed
- PDF punctuation false positives
- Acronym false positives

### Added
- PDF hyperlink extraction via PyMuPDF

---

## Version Numbering

AEGIS uses semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** (3): Major architectural changes
- **MINOR** (0): Feature additions
- **PATCH** (92-108): Bug fixes and improvements

---

## Links

- [Bug Tracker](TWR_BUG_TRACKER.md)
- [Project State](docs/TWR_PROJECT_STATE.md)
- [Lessons Learned](TWR_LESSONS_LEARNED.md)
