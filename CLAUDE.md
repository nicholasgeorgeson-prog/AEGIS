# AEGIS - Claude Session Notes

## Project Overview
**AEGIS** (Aerospace Engineering Governance & Inspection System) is a Flask-based document review/QA application for technical writing. Created by Nicholas Georgeson. Runs on localhost:5050 on the user's Mac.

## Architecture
- **Backend**: Flask (Python 3), SQLite databases
- **Frontend**: Vanilla JS, CSS, HTML (no framework)
- **Entry point**: `app.py` → calls `main()` which starts Flask server
- **Routes**: Modular blueprints in `routes/` package
- **Static files**: `static/js/`, `static/css/`, `templates/`
- **Database**: `scan_history.db` (SQLite) - roles, documents, scans, etc.
- **Quality Checkers**: 100+ document review checkers with UI toggle controls (98 UI + 7 always-on)
- **Guided Tour System**: Interactive help panels, spotlight tours, and voice narration via `guide-system.js`
- **Print Support**: Print-optimized stylesheet with URL display and page break controls

## Server Management - CRITICAL
- **The user does NOT manage the server.** Everything is done through Claude sessions.
- **Flask runs on the user's Mac** at `localhost:5050`. The Cowork VM can edit files (mounted at `/mnt/TechWriterReview`) but CANNOT restart processes on the host Mac.
- **Static files (JS, CSS, HTML)** are served fresh from disk — changes take effect on browser refresh WITHOUT server restart.
- **Python file changes REQUIRE a server restart.** The app runs with `debug=False` by default.
- **Debug mode**: Pass `--debug` flag to `app.py` to enable auto-reload for Python changes: `python3 app.py --debug`
- **Restart script**: `restart_aegis.sh` exists in the project root — kills port 5050 process and starts fresh.
- **Project path on Mac**: `~/Desktop/Work_Tools/TechWriterReview`
- **To restart**: The user must either:
  1. Double-click `restart_aegis.sh` in Finder
  2. Or in Terminal: `cd ~/Desktop/Work_Tools/TechWriterReview && lsof -ti :5050 | xargs kill -9 && sleep 2 && python3 app.py --debug`
  3. Or: Ctrl+C the running server, then `python3 app.py --debug`
- **Recommendation**: Run with `python3 app.py --debug` during development sessions so Python changes auto-reload.

## Database Schema (scan_history.db)
- **roles**: `id, role_name, normalized_name, first_seen, document_count, total_mentions, description, is_deliverable, category, role_source`
  - Does NOT have: `document_id`, `occurrence_count`, `responsibilities`
- **document_roles** (join table): `id, document_id, role_id, mention_count, responsibilities_json, last_updated`
- **documents**: `id, filename, filepath, file_hash, first_scan, last_scan, scan_count, word_count, paragraph_count`
- **function_categories**: 112 rows
- **role_function_tags**: 1126 rows
- **document_categories**: 12 rows

## Key Files
| File | Purpose |
|------|---------|
| `app.py` | Flask entry point, middleware, server startup |
| `routes/data_routes.py` | API routes for roles reports, data endpoints |
| `routes/roles_routes.py` | Roles API endpoints |
| `routes/scan_history.py` | Scan history API |
| `static/js/roles-tabs-fix.js` | Roles Studio tab management (very large file, ~4500 lines) |
| `static/js/features/landing-page.js` | Dashboard landing page tile click handlers |
| `static/js/function-tags.js` | Function tags, report generation, tag management |
| `static/js/features/guide-system.js` | Guided tour & contextual help system |
| `static/css/features/roles-studio.css` | Roles Studio styling |
| `static/css/features/guide-system.css` | Guide system styling (beacon, panel, spotlight) |
| `static/css/print.css` | Print-optimized stylesheet |
| `config.json` | App configuration |
| `review_report.py` | PDF review report generator (reportlab, AEGIS branding) |
| `export_module.py` | Excel/CSV/PDF/JSON exporters |
| `markup_engine.py` | DOCX comment insertion (COM→lxml fallback) |
| `download_win_wheels.py` | Downloads Windows x64 wheels on connected machine |
| `demo_audio_generator.py` | TTS audio generation for demo narration (edge-tts/pyttsx3) |
| `static/js/features/demo-simulator.js` | Demo mock data injection IIFE (progress, results, SOW preview) |
| `graph_export_html.py` | Interactive HTML graph export generator (D3.js, filters, search) |
| `install_offline.bat` | Offline wheel installer for air-gapped Windows |

## CSS Patterns
- Roles sections use class-based visibility: `.roles-section { display: none !important }` / `.roles-section.active { display: flex !important }`
- NEVER set inline `style.display` on role sections — it conflicts with `!important` CSS rules. Use `classList.add/remove('active')` and `style.removeProperty('display')`.

## Navigation Patterns
- **Landing page tiles** (in `landing-page.js`) use their OWN modal-opening code, separate from sidebar nav
- **Sidebar nav** buttons call the proper override functions (e.g., `showRolesModalOverride()`)
- When adding new modal-opening logic, ensure BOTH landing page tiles AND sidebar buttons call the same override functions

## Lessons Learned

### 1. Landing Page vs Sidebar Entry Points (Roles Studio Overview Bug)
**Problem**: Roles Studio Overview tab loaded fine from sidebar but was empty when opened from dashboard tile.
**Root Cause**: `landing-page.js` called generic `showModal('modal-roles')` which only toggles visibility without loading data. The sidebar called `window.showRolesModal()` which is the proper override that loads data and renders the overview.
**Fix**: Changed `landing-page.js` to call `window.showRolesModal()` instead of `showModal('modal-roles')`.
**Lesson**: Always check ALL entry points to a feature. Dashboard tiles and sidebar nav may have completely separate code paths.

### 2. Inline Styles vs CSS !important (Display Conflicts)
**Problem**: Sections not showing even with `.active` class added.
**Root Cause**: JavaScript was setting `section.style.display = 'none'` inline, which competed with CSS `.roles-section.active { display: flex !important }`. While `!important` should win, some browsers/timing issues caused conflicts.
**Fix**: Replace `section.style.display = 'none'` with `section.style.removeProperty('display')` and rely solely on CSS class toggling.
**Lesson**: Never set inline display styles when CSS uses `!important` class-based visibility. Use `classList` and `removeProperty('display')`.

### 3. SQL Queries Must Match Actual Schema (Generate Reports 500)
**Problem**: Report API endpoints returned 500 Internal Server Error.
**Root Cause**: SQL queries in `data_routes.py` referenced `roles.document_id` which doesn't exist. The role-document relationship goes through the `document_roles` join table.
**Fix**: Updated queries to JOIN through `document_roles` table.
**Lesson**: Always verify column names against actual database schema. The `roles` table has no foreign keys — all relationships go through join tables.

### 4. Python Changes Need Server Restart
**Problem**: After fixing Python files, changes don't take effect.
**Root Cause**: Flask runs with `debug=False`, no auto-reload.
**Fix**: User must restart server. Recommend using `--debug` flag during development.
**Lesson**: For Python backend changes, always remind about server restart. JS/CSS/HTML changes are picked up on browser refresh.

### 5. Console Logging is Your Best Friend
**Pattern**: All major functions in roles-tabs-fix.js log with `[TWR RolesTabs]` prefix. When debugging, check console for these markers to confirm which code paths are actually executing.
**Example**: When the override wasn't being called, console showed `[TWR RolesExport]` messages but NO `[TWR RolesTabs]` messages — proving the override function wasn't being triggered.

### 6. Dark Mode Considerations
**Pattern**: When fixing UI components, always check both light and dark mode. Text colors that work in light mode (black text) become invisible in dark mode.
**Key CSS**: Dark mode uses `[data-theme="dark"]` selector. Text in modals/selects needs explicit white color in dark mode.

### 7. Document Compare Auto-Load Pattern
**Pattern**: When user clicks Document Compare, it should auto-select oldest doc on left, newest on right, and immediately run comparison without requiring a manual "Compare" button click.

### 8. Flask Import Scope in Blueprints (app vs current_app)
**Problem**: `data_routes.py` used `app.logger` but `app` was never imported — only Blueprint-related imports existed.
**Root Cause**: In Flask blueprints, the `app` object isn't directly available. You must use `current_app` from flask, which is a proxy to the active application.
**Fix**: Added `current_app` to the flask import and replaced `app.logger` with `current_app.logger`.
**Lesson**: In any blueprint file, NEVER use bare `app.` — always use `current_app.` and ensure it's imported.

### 9. Popup Blockers Kill window.open() After Async Operations
**Problem**: `downloadReport()` in `function-tags.js` used `window.open()` to open the report in a new tab, but Chrome's popup blocker silently killed it because the call happened after an `await fetch()`.
**Root Cause**: User gesture context expires after async operations. `window.open()` must be called synchronously within a click handler to avoid popup blocking.
**Fix**: Replaced `window.open()` with a hidden `<iframe>` approach that loads the URL. Since the server returns `Content-Disposition: attachment`, the iframe triggers a download without navigating away.
**Lesson**: Never use `window.open()` after `await`. Use iframe downloads or blob+link patterns instead.

### 10. Error Handling: Catch Exception, Not Just ImportError
**Problem**: Report endpoints in `data_routes.py` caught only `ImportError` in the except clause, so any other exception (TypeError, KeyError, etc.) from the HTML generator would escape to the generic error handler.
**Fix**: Changed `except ImportError:` to `except Exception as e:` with proper logging for all three report endpoints.
**Lesson**: When providing a fallback for external module calls, catch broad `Exception`, not just `ImportError`. The module may import fine but fail during execution.

### 11. Toast Z-Index Must Be Higher Than All Modals
**Problem**: Toast notifications were hidden behind modals (reports modal z-index: 10000, toast: 2500).
**Fix**: Changed toast container z-index to 200000 in `components.css`, `dark-mode.css`, and `base.css` (`--z-toast` variable).
**Lesson**: The toast system must be the highest z-index in the app. When adding new modals, never exceed the toast z-index.

### 12. Async Init Race Condition (Landing Page Empty Tiles)
**Problem**: Landing page tiles/metrics rendered empty on page load, especially after server restart or when session-restore was active.
**Root Cause**: Two issues combined: (1) `show()` called `init()` without `await`, so the async `fetchData()`→`render()` chain hadn't completed when the page became visible. (2) `app.js` called `init()` then immediately `show()` — but `init()` sets `initialized = true` synchronously before `fetchData()` resolves, so `show()` saw `initialized === true` and skipped the full render path. (3) When `sessionRestored` was true, `init()` was never called at all, leaving the landing page module uninitialized for later navigation.
**Fix**: Made `show()` async with `await init()`. Removed redundant `init()` call in `app.js` (let `show()` handle it). Added `init()` pre-load even on session-restore path so tiles are ready when user navigates back to landing.
**Lesson**: When an async `init()` sets a guard flag (`initialized = true`) synchronously, any caller must `await` it or the dependent render won't have completed. Always audit all code paths that skip initialization (like session restore) to ensure deferred initialization still happens.

### 13. Structured Error Objects in handle_api_errors (Missing Message Extraction)
**Problem**: Error toast notifications showed "[object Object]" instead of meaningful error messages after API failures with structured error handling.
**Root Cause**: `handle_api_errors()` in `api-utils.js` returns a structured error object `{success: false, error: {...}}`, but callers were logging/displaying the entire object instead of extracting the `.message` property. Template files and some JS modules forgot to extract `.error.message` from the response.
**Fix**: Always extract the message field when handling errors: `const msg = error.error?.message || 'Unknown error'; showToast(msg, 'error');`
**Lesson**: Structured error responses require message extraction at every call site. Consider adding a wrapper function like `getErrorMessage(errorObj)` that safely extracts the message, or return plain strings from error handlers. If returning objects, always document the expected extraction pattern.

### 14. Document Compare Auto-Picker (No Document Selected on Open)
**Problem**: Document Compare modal opened but showed empty state even when documents existed, requiring user to manually select documents from dropdown.
**Root Cause**: Compare modal opened without checking if a document was pre-selected or if this was the first-time open. The modal should auto-select oldest doc on left, newest on right when opened without a docId parameter, then immediately run comparison.
**Fix**: Added fallback auto-picker in Document Compare open handler: if no docId in URL, query available docs and auto-select oldest/newest pair, then call `runComparison()` without waiting for user interaction.
**Lesson**: Modal features that depend on data selection should auto-load sensible defaults (oldest/newest, first/last, etc.) when opened without explicit parameters. Test all entry points (sidebar, landing tile, URL hash) to ensure consistent behavior.

### 15. Missing Timezone Import in datetime Operations (SOW Generation 500 Error)
**Problem**: Statement of Work generation endpoint returned 500 Internal Server Error when generating templates with dates.
**Root Cause**: Python code used `datetime.now(timezone.utc)` to get current time, but `timezone` was never imported from the `datetime` module. Python 3.9+ removed implicit timezone support; explicit import required.
**Fix**: Added `from datetime import datetime, timezone` to import statements. Verified all datetime operations include explicit timezone parameter when creating UTC timestamps.
**Lesson**: Python 3.9+ requires explicit `from datetime import timezone` for `timezone.utc`. When refactoring legacy datetime code that used deprecated `utcnow()`, always include timezone imports. Test date/time operations on startup to catch import errors early.

### 16. Version Display Stale After Update (Import-Time Caching)
**Problem**: After updating `version.json` to 4.9.9, the UI still displayed "4.7" even after server restart and hard refresh.
**Root Cause**: Three issues compounded: (1) `config_logging.py` read `version.json` at **import time** and stored it as `VERSION = _load_version()`. Python bytecode cache (`.pyc`) could serve stale values. (2) The `index()` middleware used the import-time `VERSION` constant, not a fresh read. (3) `index.html` had hardcoded `?v=4.8.3` etc. on script tags, and the middleware's `.js"` replacement couldn't match `.js?v=4.8.3"`, so cache-busting was inconsistent.
**Fix**: (1) Added `get_version()` function to `config_logging.py` that reads `version.json` fresh on every call. (2) Changed `index()` route and `/api/version` to call `get_version()` instead of using the stale `VERSION` constant. (3) Stripped all hardcoded `?v=` from `index.html` — the middleware now uses regex to replace/add version params uniformly. (4) The regex first replaces existing `?v=` params, then adds them to any files that don't have one yet.
**Lesson**: Never cache version strings at import time. Use a function (`get_version()`) that reads from disk on each call. For cache-busting, let the server middleware handle all `?v=` injection — never hardcode version params in HTML templates. The single source of truth is `version.json`, and `get_version()` is the single access point.

### 17. Duplicate version.json Files (Static vs Root)
**Problem**: After all the import-time caching fixes (Lesson 16), version STILL showed 4.7.0 in the browser UI.
**Root Cause**: There are TWO copies of `version.json` — one in the project root (read by Python `get_version()` and `/api/version`) and one in `static/` (served to the browser JS). The root copy was updated to 4.9.9 but `static/version.json` was still 4.7.0. Both `app.js` and `landing-page.js` fetched from `/static/version.json` as their primary source.
**Fix**: (1) Copied root `version.json` to `static/version.json`. (2) Changed `app.js` and `landing-page.js` to use `/api/version` as primary source (which reads fresh from root via `get_version()`) with `/static/version.json` as fallback only.
**Lesson**: When debugging "version not updating," check ALL copies of the version file. The browser JS and Python backend may read from different files. Always verify what the browser actually receives (use browser dev tools or MCP inspection), not just what's on disk.

## Version Management
- **Current version**: 5.9.21
- **Single source of truth**: `version.json` in project root
- **Access function**: `from config_logging import get_version` — reads fresh from disk every call
- **Legacy constant**: `VERSION` from `config_logging` is set at import time — use `get_version()` for anything user-facing
- **Server-side injection**: `core_routes.py index()` reads `get_version()` each request and injects into HTML elements + cache-bust params
- **Client-side**: `app.js loadVersionLabel()` and `landing-page.js` both fetch `/api/version` as primary source (reads fresh from root `version.json` via `get_version()`), with `/static/version.json` as fallback
- **IMPORTANT**: There are TWO copies of `version.json` — root and `static/`. Always update BOTH when changing version, or better yet just update root and copy: `cp version.json static/version.json`
- **To update version**: Edit `version.json` in project root, then `cp version.json static/version.json` to sync the static copy.

## GitHub Workflow
- **PAT**: Stored in session context (not committed to repo for security)
- **Git config**: email=`nicholas.georgeson@gmail.com`, name=`Nicholas Georgeson`
- **gh CLI path**: `/sessions/fervent-ecstatic-faraday/gh`
- **Index lock status**: Git index is stuck in Cowork VM — all pushes use GitHub REST API (no `git push`)
- **REST API workflow**: Create blobs (base64) → create tree (with base_tree) → create commit → PATCH refs/heads/main
- **Batch size**: Group files in batches of 30 per commit to avoid timeout errors
- **Large files (>100MB)**: Must use GitHub Releases, not regular commits
- **Release for wheels**: `v5.1.0-wheels` contains torch (139MB) and other large binaries

## Wheels & Dependencies
- **Total wheels**: 195 wheel files in `wheels/` directory
- **Platforms**: Both Linux ARM64 (`manylinux_2_17_aarch64`) and Windows x64 (`win_amd64`) wheels present
- **torch wheel**: 139MB uploaded to GitHub Release v5.1.0-wheels (exceeds 100MB commit limit)
- **Installation script**: `install_offline.bat` handles installation on air-gapped Windows systems
- **Download script**: `download_win_wheels.py` downloads Windows x64 wheels on connected machines
- **Key packages**: spaCy (en_core_web_sm), numpy, pandas, scipy, scikit-learn, docling, opencv, transformers
- **NLP model sharing**: Use `get_spacy_model()` from `nlp_utils.py` for singleton caching across checkers

### 18. CSRF Token Mismatch When Using MCP Browser / Programmatic fetch()
**Problem**: Programmatic `fetch('/api/upload', ...)` from MCP browser JavaScript fails with `CSRF_ERROR` even after page refresh and cookie clearing.
**Root Cause**: Flask debug auto-reload creates a new server process with a new secret key, invalidating all existing sessions. The page's `<meta name="csrf-token">` stores the token from when the HTML was rendered (old session), but `fetch()` uses the cookie from the current session (new, different token). The meta CSRF and session CSRF are out of sync.
**Fix (for MCP programmatic uploads)**: Two-step approach:
1. First make a GET request to get the fresh CSRF from the **response header**: `const resp = await fetch('/api/version', {credentials: 'same-origin'}); const freshCsrf = resp.headers.get('X-CSRF-Token');`
2. Use that fresh token in subsequent POST requests: `headers: {'X-CSRF-Token': freshCsrf}`
The response header CSRF (set by `app.py` after_request at line 382) always matches the current session because it's set in the same request cycle.
**Key Insight**: `meta[name="csrf-token"]` ≠ `response.headers['X-CSRF-Token']` after debug reloads. Always use the response header for programmatic API calls.
**Lesson**: When doing programmatic uploads via MCP browser, never trust the meta tag CSRF. Always fetch a fresh token from any API response header first. This is a recurring issue during development sessions with `--debug` mode.

### 19. New Checkers Must Be Added to `additional_checkers` List (core.py)
**Problem**: New checkers registered in `_init_checkers()` and loaded into `self.checkers` were NOT being run during reviews. Checker count showed 88 but issues from new checkers were missing.
**Root Cause**: `review_document()` in `core.py` builds `enabled_checkers` from two sources: (1) `option_mapping` dict (lines 1960-2033) mapping UI checkbox names to checker names, and (2) `additional_checkers` list (lines 2046-2052) for checkers without UI toggles. New checkers were in `self.checkers` but not in either list, so they were never added to `enabled_checkers`.
**Fix**: Added new checker names to the `additional_checkers` list:
```python
additional_checkers = [
    ...,
    'requirement_traceability', 'vague_quantifier',
    'verification_method', 'ambiguous_scope'
]
```
**Lesson**: Registering a checker in `_init_checkers()` is NOT enough. The checker name must ALSO appear in either `option_mapping` (if it needs a UI toggle) or `additional_checkers` (if it should always run). Three places to touch: (1) checker file with factory function, (2) `_init_checkers()` import block, (3) `additional_checkers` list or `option_mapping` dict.

### 20. Duplicate Responsibility Statements from Repeated Document Scans
**Problem**: RACI numbers and responsibility counts were inflated (2713 vs 1993 actual unique statements). Distribution was wrong.
**Root Cause**: When a document is scanned multiple times, `document_roles.responsibilities_json` accumulates duplicate entries within the same JSON blob. Each scan appends statements without checking for existing ones. Methods like `get_all_roles()`, `get_role_context()`, and `get_raci_matrix()` counted every entry without deduplication.
**Fix**: Added `seen_texts` set-based deduplication in three methods in `scan_history.py`:
1. `get_all_roles()` — powers Roles Studio Overview "Responsibilities" count
2. `get_role_context()` — powers the RACI detail popup statements list
3. `get_raci_matrix()` — powers RACI matrix verb classification counts
**Lesson**: Any method that reads from `responsibilities_json` MUST deduplicate by statement text. Multiple scans of the same document create duplicates within the JSON array. Always use a `seen_texts = set()` pattern when iterating over responsibility entries. The two separate counting systems (scan_statements table vs responsibilities_json) may produce different totals — this is expected since they count different things (extracted requirements vs role-linked responsibilities).

### 21. GitHub Release for Large Files (torch wheel)
**Problem**: torch-2.10.0 wheel (139MB) exceeds GitHub's 100MB per-file commit limit.
**Root Cause**: GitHub REST API and git both reject files >100MB in regular commits.
**Fix**: Created a GitHub Release (`v5.1.0-wheels`) and uploaded torch as a release asset. Releases support up to 2GB per file.
**Lesson**: Any wheel or binary >100MB must go into a GitHub Release, not a regular commit. Use `gh api repos/{owner}/{repo}/releases` to create, then upload assets to the upload_url.

### 22. Git Index Lock — Use GitHub REST API for All Pushes
**Problem**: Git index.lock file is stuck/corrupted in the Cowork VM, preventing all normal git operations (add, commit, push).
**Fix**: ALL pushes done via GitHub REST API: create blobs (base64) → create tree (with base_tree) → create commit → PATCH refs/heads/main.
**Lesson**: When git is broken in the VM, the full GitHub REST API workflow is: (1) GET refs/heads/main for HEAD SHA, (2) GET commits/{sha} for tree SHA, (3) POST git/blobs for each file, (4) POST git/trees with base_tree + new blob SHAs, (5) POST git/commits with tree + parent, (6) PATCH git/refs/heads/main with new SHA. Batch files in groups of 30 per commit to avoid timeouts.

### 23. Platform-Specific Wheels Must Match Production OS
**Problem**: All 33 platform-specific wheels were Linux ARM64 (`manylinux_2_17_aarch64`). Production is Windows x86_64.
**Root Cause**: Wheels were downloaded on the Cowork VM (Linux ARM64). pip silently skips incompatible platform wheels — no error, just doesn't install.
**Fix**: Downloaded Windows x64 (`win_amd64`) versions of all packages. Both platforms' wheels coexist in `wheels/` — pip auto-selects the correct one.
**Lesson**: Always verify wheel platform tags match the target OS. pip gives NO warning when it skips incompatible wheels. Use `pip debug --verbose` to see which platforms pip expects.

### 24. spaCy Model Singleton Pattern (Performance)
**Problem**: Multiple checkers each loading their own spaCy model instance, wasting memory and startup time.
**Fix**: Added `get_spacy_model()` function in `nlp_utils.py` that caches the model globally. All checkers share one instance.
**Lesson**: Heavy NLP models (spaCy, transformers) should be loaded ONCE and shared via a module-level cache function. Never load in a checker's `__init__` if multiple checkers need the same model.

### 25. Guided Tour System Architecture (v2.3.0)
**Pattern**: The AEGIS Guide system (`guide-system.js` v2.3.0 + `guide-system.css`) uses:
- SVG mask for spotlight cutouts (not box-shadow hack)
- `getBoundingClientRect()` + `scrollIntoView()` for element targeting (fixed `offsetParent` check → `getBoundingClientRect().width > 0` for modal elements)
- Section registry pattern — each section defines: whatIsThis, keyActions, proTips, tourSteps, demoScenes, **subDemos**
- Tour steps reference CSS selectors that must exist in index.html
- **79 overview demo scenes** across 11 sections (~10 min full demo with voice narration)
- **93 sub-demos with ~471 deep-dive scenes** covering every sub-function, tab, workflow, export, import, and feature
- **Demo picker UI** in help panel: overview card + 2-column sub-demo card grid
- **preAction pattern**: each sub-demo has an async preAction() that clicks the correct tab before scenes play
- **Breadcrumb display**: demo bar shows "Section › Sub-demo" during sub-demo playback
- Voice narration provider chain: pre-generated MP3 → Web Speech API → silent timer fallback
- Demo bar: fixed-bottom glassmorphism UI with typewriter narration, controls (play/pause/prev/next/stop), speed selector, progress bar
- Double-start guard prevents rapid-click demo restarts
- Tooltip suppression during demo mode (400ms setTimeout after showSpotlight's 350ms)
**Files**: `static/js/features/guide-system.js`, `static/css/features/guide-system.css`, `demo_audio_generator.py`
**API**: `AEGISGuide.startFullTour()`, `AEGISGuide.startFullDemo()`, `AEGISGuide.startDemo(sectionId)`, `AEGISGuide.startSubDemo(sectionId, subDemoId)`, `AEGISGuide.openPanel('sectionId')`, `AEGISGuide.addHelpButton(modal, sectionId)`
**Z-index hierarchy**: beacon=150000, demoBar=149800, panel=149500, spotlight=149000
**Settings**: localStorage key `aegis-guide-enabled`, toggle in Settings > General

### 26. Print Stylesheet Approach
**Pattern**: `static/css/print.css` loaded with `media="print"` — only activates during Ctrl+P.
**Key rules**: Hide sidebar, toolbar, toasts, floating buttons. Show table borders. Display URLs after links via `a[href]::after { content: " (" attr(href) ")"; }`. Force white background. Control page breaks with `break-inside: avoid` on cards/tables.

### 27. Accessibility Retrofit Pattern
**Pattern**: When adding aria-labels to an existing app:
1. All icon-only buttons need `aria-label` describing the action
2. All modals need `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
3. All tab systems need `role="tablist"` on container, `role="tab"` on buttons, `role="tabpanel"` on panels
4. Decorative icons (next to text labels) get `aria-hidden="true"`
5. Live regions (toasts, loading) get `role="alert"` or `aria-live="polite"`
**Lesson**: Don't add `aria-label` to elements that already have visible text — screen readers read both, causing duplication.

### 28. Checker UI Toggle Wiring (Three Places to Touch)
**Problem**: 14 checkers had no UI checkboxes — they ran via `additional_checkers` but users couldn't see/control them.
**Fix**: Added checkbox HTML in index.html → mapped names in `option_mapping` in core.py → removed from `additional_checkers`.
**Lesson**: To add a checker toggle: (1) Add `<input type="checkbox" data-checker="name">` in index.html settings panel, (2) Add `'check_name': 'checker_name'` to `option_mapping` in core.py `review_document()`, (3) Remove from `additional_checkers` if it was there. Three files, three changes, all required.

### 29. Checker Naming Conflicts (Duplicate Factory Keys)
**Problem**: v3.3.0 `terminology_checker.py` and v5.3.0 `terminology_consistency_checker.py` both produced a checker with key `terminology_consistency`. The second one overwrote the first in `self.checkers`.
**Fix**: Renamed v5.3.0 factory output from `terminology_consistency` to `wordnet_terminology`. Updated `option_mapping` in core.py (`check_term_consistency` → `wordnet_terminology`) and verified index.html checkbox uses matching `data-checker` attribute.
**Lesson**: Every checker factory function must produce UNIQUE keys. Before creating a new checker, search `core.py` for existing keys with the same name. Use `grep -r "terminology_consistency" *.py` to find all references.

### 30. Dark Mode FOUC (Flash of Unstyled Content)
**Problem**: User reported "opens in light mode then switches to dark" despite inline script setting `.dark-mode` class before CSS loads.
**Root Cause**: The inline script only set the CSS class on `<html>`, but CSS variable defaults in `:root` were light values. The dark overrides via `.dark-mode` selector hadn't cascaded yet during first paint.
**Fix**: Three-part fix: (1) Set `data-theme="dark"` attribute in addition to class (for selectors using `[data-theme="dark"]`). (2) Set critical CSS variables inline (`--bg-deep`, `--bg-primary`, `--text-primary`). (3) Add inline `<style>` block with `html.dark-mode { background-color: #0d1117; color: #e6edf3; }` before any stylesheet link.
**Lesson**: For FOUC prevention, CSS classes alone aren't enough — you need to set the actual CSS variable VALUES inline before any stylesheet loads. The class needs the stylesheet to define what it means; inline variables are self-contained.

### 31. Script Defer for Faster Initial Paint
**Problem**: 40+ synchronous `<script>` tags blocked HTML parsing, delaying first meaningful paint by 200-500ms.
**Fix**: Added `defer` attribute to 30+ feature module scripts that aren't needed for initial landing page. Kept core modules (storage, state, api, modals, app.js, landing-page.js) synchronous since they're needed immediately.
**Lesson**: `defer` downloads scripts in parallel and executes in order after HTML parsing. Safe for any script that uses `DOMContentLoaded`. NOT safe for scripts that write to DOM during load or that other sync scripts depend on immediately. Test all entry points after adding defer.

### 32. Async CSS Loading Pattern
**Pattern**: Use `media="print" onload="this.media='all'"` to load non-critical CSS asynchronously. The browser downloads the file immediately (for "print") but doesn't block render. On load, switching to `media="all"` applies the styles.
**Lesson**: Only the main `style.css` and `landing-page.css` need to be render-blocking. All feature CSS (portfolio, hyperlink-validator, data-explorer, etc.) can load async since those features aren't visible on initial page load.

### 33. Batch Scan Multi-Threading (ThreadPoolExecutor)
**Problem**: Batch scan processed documents sequentially — 10 documents took 10x the time of one.
**Fix**: Wrapped each document review in a separate thread via `ThreadPoolExecutor(max_workers=3)`. Each thread creates its own `AEGISEngine()` instance to avoid shared state.
**Why max_workers=3**: Higher values cause memory pressure from NLP models (spaCy, sentence-transformers). 3 is a safe balance.
**Why ThreadPoolExecutor not ProcessPoolExecutor**: The individual `review_document()` already spawns a subprocess (multiprocessing.Process). Threading at the batch level + subprocess per review gives us parallelism without the complexity of nested multiprocessing.
**Lesson**: For batch operations where each item is independent, ThreadPoolExecutor with per-thread engine instances is safe. The key is NO shared mutable state between threads.

### 34. Server-Side Folder Scan Architecture (v5.5.0)
**Problem**: Users need to scan entire document repositories with hundreds of files across nested subdirectories. The existing browser-based batch upload requires manually selecting files and is limited by browser memory.
**Solution**: New `/api/review/folder-scan` endpoint accepts a server filesystem path, recursively discovers all supported documents, then processes them in memory-safe chunks.
**Architecture**:
- Phase 1 (Discovery): Recursive `Path.iterdir()` with depth limit, skipping hidden dirs, empty files, files >100MB, and common non-doc dirs (`.git`, `node_modules`, `__pycache__`).
- Phase 2 (Review): Documents split into chunks of `FOLDER_SCAN_CHUNK_SIZE` (5). Each chunk processed via `ThreadPoolExecutor(max_workers=3)`. `gc.collect()` runs between chunks.
- Per-file error isolation: one bad file doesn't stop the scan. Errors logged and reported in results.
- Results aggregated: grade distribution, severity breakdown, category analysis, role discovery across all documents.
**Constants** (in `_shared.py`): `MAX_FOLDER_SCAN_FILES=500`, `FOLDER_SCAN_CHUNK_SIZE=5`, `FOLDER_SCAN_MAX_WORKERS=3`.
**Batch limits increased**: `MAX_BATCH_SIZE=50` (was 10), `MAX_BATCH_TOTAL_SIZE=500MB` (was 100MB).
**Frontend**: Folder path input in batch upload modal with "Preview" (discovery only) and "Scan All" buttons.
**Lesson**: For large batch operations, chunk processing with inter-chunk GC is essential. Don't try to hold all engine instances in memory simultaneously. The discovery/review two-phase approach lets users preview before committing. Always provide a dry-run option for potentially long operations.

### 35. Animated Demo Player Architecture (v5.6.0 → v5.9.9)
**Problem**: Users wanted "live video" walkthroughs of every AEGIS feature, but actual screen-recorded video files would be massive and stale after any UI change.
**Solution**: Built an animated demo player system in pure HTML/CSS/JS that runs on the live UI. Each section defines `demoScenes` (overview) + `subDemos` (deep-dive) — arrays of steps with `target` (CSS selector), `narration` (text), `duration` (ms), and optional `navigate` (function to open the correct modal first).
**Architecture**:
- Demo bar: Fixed-bottom glass-morphism UI with typewriter narration, controls (play/pause/prev/next/stop), speed selector, progress bar
- SVG mask spotlight: Creates SVG with white fill + black cutout rect for target element, applied as CSS mask to semi-transparent overlay
- Section navigation: `_navigateToSection(sectionId)` opens the correct modal/view, waits 600ms for DOM to settle, then spotlights elements within it
- Typewriter effect: Characters typed one at a time at configurable speed (adjusted by playback speed multiplier)
- Auto-advance: Each step displays for `duration / speed` milliseconds before advancing
- Full Demo mode: Iterates through all 11 sections sequentially, navigating between modals automatically
- Voice narration: Web Speech API with `SpeechSynthesisUtterance`, provider chain (MP3 → WebSpeech → silent timer)
- **79 overview scenes** across 11 sections — full demo ~10 min with narration at 1x speed
- **93 sub-demos with ~471 deep-dive scenes** — hierarchical drill-down covering every sub-function, export, import, and workflow
- **Demo picker**: Help panel transitions to show overview card + 2-column sub-demo card grid when "Watch Demo" is clicked
- **preAction pattern**: Each sub-demo has `preAction: async () => { ... }` that clicks the correct tab, waits for render
- **startSubDemo(sectionId, subDemoId)**: Navigates to section → runs preAction → plays scenes with breadcrumb title
- Content guidelines: 150-300 char narration, 7000-10000ms duration, one teaching point per scene, workflow order
**Key files**: `guide-system.js` (logic, v2.3.0), `guide-system.css` (styles), `demo_audio_generator.py` (pre-gen TTS)
**Z-index hierarchy**: beacon=150000, demoBar=149800, panel=149500, spotlight=149000
**Settings**: localStorage key `aegis-guide-enabled`, toggle in Settings > General, synced via `saveSettings()` in app.js
**Lesson**: For feature walkthrough "videos," an animated demo player on the live UI is better than pre-recorded videos — it stays current with UI changes, requires no video hosting, and can be interactive. The key design pattern is: define scenes declaratively (selector + narration + navigation), then a generic player engine handles spotlight, narration, timing, and controls. For sub-function drill-down, the `subDemos` object alongside `demoScenes` provides hierarchical depth without restructuring existing overview demos.

### 36. ReviewIssue Object vs Dict in Folder Scan (v5.6.1)
**Problem**: Folder scan returned `errors: 5` for all documents. Error message: `'ReviewIssue' object has no attribute 'get'`.
**Root Cause**: `review_document()` returns `self.issues` which is a mixed list — non-NLP checkers add `ReviewIssue` dataclass instances, NLP checkers add converted dicts via `convert_to_legacy_issue()`. The folder scan's `_review_single()` passed these raw objects to aggregation code that called `.get('severity')` and `.get('category')`, and to `json.dumps()` for scan history recording — both fail on dataclass instances.
**Fix**: Added conversion step at the top of `_review_single()` that normalizes all issues to dicts: `issue.to_dict()` for ReviewIssue objects, passthrough for dicts, fallback `getattr()` extraction for anything else. This ensures all downstream code (aggregation, JSON serialization, fingerprinting) receives dicts.
**Lesson**: When consuming output from `review_document()`, always convert issues to dicts first. The `issues` list contains a mix of `ReviewIssue` objects and plain dicts. Use `issue.to_dict() if hasattr(issue, 'to_dict') else issue` pattern. This affects any code path that processes review results outside the normal `/api/review` → `jsonify()` flow (folder scan, batch scan, programmatic access).

### 37. Flask Debug Threading Fix (v5.7.0)
**Problem**: Flask debug mode (`--debug`) runs single-threaded by default. A long folder scan (31 files, 15+ minutes) blocks ALL other requests — even `/api/version` hangs. Users see a completely frozen UI.
**Root Cause**: `app.run(debug=True)` without `threaded=True` starts a single-threaded WSGI server. Long-running endpoints (folder scan, batch review) block the entire server.
**Fix**: Added `threaded=True` to the debug mode `app.run()` call in `app.py` line 580. Non-debug localhost mode and production (Waitress) already had threading enabled.
**Lesson**: Always pass `threaded=True` when using Flask's development server for applications that have long-running endpoints. The production Waitress setup with 4 threads was already fine — this only affected `--debug` mode during development.

### 38. Async Folder Scan with Progress Polling (v5.7.0)
**Problem**: Folder scan returned everything at once after completion — user stared at a static "Discovering and reviewing documents..." message for 15+ minutes with zero visibility into progress.
**Solution**: Two-step async pattern:
1. `POST /api/review/folder-scan-start` — Runs discovery synchronously (fast, <1s), returns `scan_id` + discovery results immediately, spawns a background thread for the review phase.
2. `GET /api/review/folder-scan-progress/<scan_id>` — Returns current state from module-level `_folder_scan_state` dict. Supports `?since=N` for incremental document fetching (only new docs since last poll).
**Architecture**: Module-level `_folder_scan_state` dict protected by `threading.Lock`. Background thread calls `_process_folder_scan_async()` which updates state after each file completes. State includes: phase, total/processed/errors, current_file, current_chunk/total_chunks, documents[], elapsed_seconds, estimated_remaining. States auto-cleanup after 30 minutes of completion.
**Frontend**: Polls every 1.5s, builds `bpd-doc-row` elements (reusing batch dashboard CSS), shows per-file status transitions (queued → processing → complete/error), progress bar, elapsed/remaining time, speed, chunk tracking.
**Lesson**: For long-running operations, always use a background thread + polling pattern instead of blocking the HTTP response. The existing synchronous `/folder-scan` endpoint is preserved as fallback for backward compatibility.

### 39. Deduplication Key Should Not Include rule_id (v5.7.0)
**Problem**: Two separate acronym checker systems (`acronym_checker.py` + `acronym_enhanced_checkers.py`) flagged the same undefined acronyms. The deduplication key `(paragraph_index, category, flagged_text[:80], message[:80], rule_id)` included `rule_id` and `message`, so cross-checker duplicates (same text, different checker → different rule_id and message wording) bypassed dedup. This inflated issue counts by ~20-30%.
**Fix**: Simplified dedup key in `_deduplicate_issues()` to `(paragraph_index, category, flagged_text[:80])` — removes `rule_id` and `message`. Different checkers flagging the same text at the same location are now properly caught as duplicates.
**Also fixed**: Broken `option_mapping` entry `'check_enhanced_acronyms': 'enhanced_acronyms'` — the key `'enhanced_acronyms'` doesn't exist as a checker. The enhanced checkers register as `'acronym_first_use'` and `'acronym_multiple_definition'` (which already had proper mappings).
**Lesson**: Dedup keys should be based on WHAT was flagged and WHERE, not WHO flagged it. Including the checker's rule_id or message text in a dedup key defeats the purpose when multiple checkers cover overlapping territory.

### 40. Background Thread Robustness for Async Scans (v5.7.1)
**Problem**: Async folder scan background thread stalled after processing 2 of 31 files. `elapsed_seconds` froze at 29.4s despite 90+ real seconds passing. The entire scan appeared dead with no recovery.
**Root Cause**: Multiple issues: (1) `future.result()` had no timeout — if a worker hung on a file (e.g., large PDF, corrupt .doc), it blocked forever. (2) `elapsed_seconds` was only updated inside the `as_completed` loop — if no futures completed, the timer froze. (3) No try/except around `future.result()`, so unexpected exceptions crashed the entire background thread silently. (4) `current_file` only showed the last-completed file, not what was actively being processed.
**Fix**: (1) Added per-file timeout (5 min) via `future.result(timeout=30)` and chunk-level timeout via `as_completed(timeout=PER_FILE_TIMEOUT * len(chunk))`. (2) Compute `elapsed_seconds` LIVE in the progress endpoint from `started_at` instead of using the stored value. (3) Wrapped `future.result()` in try/except with error result fallback. (4) Set `current_file` to show chunk contents (up to 3 filenames) at chunk start. (5) Extracted `_update_scan_state_with_result()` helper to clean up deep indentation. (6) Chunk timeout gracefully marks remaining files as errors and continues to next chunk.
**Lesson**: For background threads with ThreadPoolExecutor: ALWAYS use timeouts on `future.result()` and `as_completed()`. Never store elapsed time statically — compute it live from `started_at`. Wrap all future operations in try/except. Show what's being processed, not just what's done.

### 41. detectCurrentSection() and Landing Page Overlay (v5.7.2)
**Problem**: Help panel showed "Statement Forge" content when opened from the landing page. Additionally, clicking section nav buttons for modals (e.g., Batch Scan) opened the modal BEHIND the landing page overlay — invisible to the user.
**Root Cause**: Three issues: (1) Statement Forge check in `detectCurrentSection()` used `el.style.display !== 'none'` which returns true when display is empty string (no inline style). (2) Landing page check used `el.offsetParent !== null`, but landing page has `position: fixed` which always returns null for offsetParent. (3) `_navigateToSection()` called `closeModals()` but never dismissed the landing page overlay, so modals opened behind it.
**Fix**: (1) Changed Statement Forge check to only use `.active` class like all other modals. (2) Changed landing page check to `document.body.classList.contains('landing-active')`. (3) Added landing page dismissal at the top of `_navigateToSection()` for all non-landing sections. (4) Added missing `batch` and `portfolio` entries to the detection array.
**Lesson**: `offsetParent` is null for `position: fixed` elements — don't use it for visibility detection. Use class-based checks consistently. When navigating between sections, always dismiss ALL overlays (including landing page), not just modals.

### 42. Cross-Checker Dedup and Document-Type-Aware Review (v5.8.0)
**Problem**: AEGIS flagged 71 issues on a 10-sentence test document. Manual review found ~40 were true positives, ~20 were cross-checker duplicates (same issue, different category names), and ~11 were false positives (noise for requirements docs). The automated score was close but inflated by duplicate/noise issues.
**Root Cause**: (1) `_deduplicate_issues()` keyed on `(para_idx, category, flagged_text)` — but different checkers use different category names for the same finding (e.g., "Requirement Traceability" vs "INCOSE Compliance" both flag missing IDs). (2) Checkers like Noun Phrase Density and Dale-Chall Readability aren't calibrated for requirements documents where high noun density and technical vocabulary are expected. (3) No checker detected mixed directive verbs (shall/should/must) or dangling cross-references.
**Fix**: (1) Added `_CATEGORY_NORM` normalization map in `_deduplicate_issues()` that maps semantically equivalent categories to a common key before dedup. (2) Added `_suppress_for_requirements_doc()` that downgrades noise categories to Info for auto-detected requirements documents. (3) Created `DirectiveVerbConsistencyChecker` and `UnresolvedCrossReferenceChecker` in `requirement_quality_checkers.py`. (4) Expanded spelling dictionary with aerospace/PM terms.
**Lesson**: Cross-checker dedup must normalize category names, not just compare them literally. Document-type detection (already present in `_detect_document_type()`) should feed back into issue suppression/downgrading. When comparing automated results to human expert review, the biggest gap is usually noise (false positives from domain-inappropriate thresholds), not missed issues.

### 43. Document Compare Needs a Master Document Selector (v5.8.1)
**Problem**: Document Compare modal opened with a pre-selected document (auto-detected from current file or picker) and provided no way to switch to a different document. Users were locked into comparing scans of one document — to compare a different document, they had to close and reopen the modal.
**Root Cause**: The modal header had a static `.dc-doc-title` span showing the filename as plain text. Only scan-level `<select>` dropdowns existed (`#dc-old-scan`, `#dc-new-scan`) for choosing which scans to compare. No document-level selector was ever built — the original design assumed users would always enter via the document picker or current-document path.
**Fix**: (1) Replaced `.dc-doc-title` span with a `<select id="dc-doc-select">` dropdown in `index.html`. (2) Added `populateDocumentSelector()` in `doc-compare.js` that fetches all comparable documents from `/api/compare/documents` and populates the dropdown on modal open. (3) Added change event listener that re-initializes state, reloads scans, and auto-compares when user switches documents. (4) Styled for both light and dark mode in `doc-compare.css`.
**Lesson**: Any modal that operates on a specific entity (document, role, scan) should always provide a way to switch that entity from within the modal. Don't assume users will always enter via the "correct" path. The `/api/compare/documents` endpoint already existed but was only used by the picker dialog — reusing it in the modal header was trivial.

### 44. Export Suite Architecture — Filter + Format + Progress Pattern (v5.9.4)
**Problem**: Export system had only 3 formats (DOCX, CSV, JSON), no server-side PDF, no pre-export filtering, and the PDF "export" was just a client-side print dialog (`window.open()` → `print()`). No way to filter by severity or category before exporting. No progress feedback during export.
**Solution**: Complete export suite rebuild:
1. **5 format cards**: DOCX (comments), PDF Report (reportlab), XLSX (openpyxl), CSV, JSON
2. **Pre-export filter panel**: Collapsible panel with severity and category chip-based multi-select. Live preview count updates as filters are toggled. Filters stack on top of export mode (All/Filtered/Selected).
3. **Server-side PDF**: New `review_report.py` with `ReviewReportGenerator` class using reportlab. Cover page, executive summary, severity/category breakdown tables, issue details grouped by category. AEGIS gold/bronze branding. Filter notice banner when filters are active.
4. **Export progress overlay**: Glassmorphism card with animated progress bar, format-specific title, and issue count detail. Shown during export, hidden on completion.
5. **Backend endpoint**: `POST /api/export/pdf` with filter support. Issues can come from request body or session. Filters applied server-side as well.
**Files**: `review_report.py` (NEW), `static/css/features/export-suite.css` (NEW), `templates/index.html` (modal update), `static/js/app.js` (export logic), `routes/review_routes.py` (PDF endpoint)
**Key patterns**:
- Export filters are applied CLIENT-SIDE before sending to backend (reduces payload, works for all formats including client-side JSON)
- `_populateExportFilterChips()` builds chips from `State.issues` on modal open
- `_getExportFilters()` reads active chips and returns `{severities: [], categories: []}`
- `_updateExportFilterPreview()` counts matching issues and updates the preview bar
- `_showExportProgress()` / `_hideExportProgress()` manage the overlay
- PDF report uses same branding patterns as `adjudication_report.py` (AEGIS_GOLD, AEGIS_BRONZE, letter size, Helvetica fonts)
**Lesson**: For export features, always (1) provide format-specific progress feedback (users hate staring at "Exporting..."), (2) allow pre-export filtering so users can create focused deliverables, and (3) do server-side generation for complex formats (PDF) while keeping simple formats (JSON) client-side.

### 45. Fix Assistant ↔ Export Modal Integration (v5.9.4)
**Problem**: Fix Assistant v2 opened on top of the export modal, but when it closed, the export modal was gone (FA's `showModal()` closes all other `.modal.active`). Additionally, the launcher stats ("X selected") never updated after review because the `fixAssistantDone` event had no listener. And `handleFinishReview()` populated `State.selectedFixes` using array indices instead of actual fix indices.
**Root Causes**: (1) Fix Assistant's `showModal()` at line 7432 calls `otherModal.classList.remove('active')` on all modals except `fav2-modal` — this closes the export modal. (2) `fixAssistantDone` custom event was dispatched but never listened for. (3) `FixAssistantState.getSelectedFixes()` returns an array of objects, not a Map — so `.forEach((_, idx)` gives sequential array indices, not the original fix indices from the decisions Map.
**Fix**: (1) Added `fixAssistantDone` event listener in `initNewFeatureListeners()` that re-shows the export modal, updates launcher stats, and auto-checks the "Apply selected fixes" checkbox. (2) Added `close()` re-show logic with `setTimeout(100ms)` for the cancel/X path. (3) Added `_closingForFinish` flag to prevent double-modal-open when `handleFinishReview()` calls `close()` then dispatches `fixAssistantDone`. (4) Fixed `State.selectedFixes` population to use `FixAssistantState.getDecision(originalIdx)` iteration over all fixes. (5) Added stats restoration in `showExportModal()` when returning after previous FA review.
**Data format gotcha**: `FixAssistantState.getSelectedFixes()` returns `{original_text, replacement_text, ...}` (mapped from raw fix's `flagged_text`/`suggestion`). Legacy `FixAssistant.getSelectedFixes()` fallback returns `{flagged_text, suggestion, ...}` directly from `State.fixes[idx]`. Always use `||` fallbacks: `f.original_text || f.flagged_text || ''`.
**Lesson**: When a full-screen modal (like Fix Assistant) closes all other modals on open, it MUST re-show the originating modal on close. Use a flag (`_closingForFinish`) to distinguish between user-cancelled close (re-show with current state) and finish-review close (re-show with updated stats via custom event). Always check what data format `.getSelectedFixes()` actually returns — the same method name can return different shapes depending on the initialization state.

### 46. FOUC Script Sets data-theme on Body — Must Sync on Toggle (v5.9.5)
**Problem**: "New to AEGIS?" banner text invisible in light mode. `.gs-card-title` had `color: var(--text-primary)` but `--text-primary` resolved to `#e6edf3` (white) on the body element despite being in light mode.
**Root Cause**: Three-layer FOUC (Flash of Unstyled Content) prevention system was out of sync:
1. `<head>` script sets `data-theme="dark"` and inline styles on `<html>` element
2. `<body>` inline script (line 131 of index.html) sets `data-theme="dark"` on `<body>` element
3. `toggleTheme()` and `initThemeToggle()` in app.js only synced `data-theme` on `<html>`, never on `<body>`

When user toggled to light: `<html data-theme="light">` but `<body data-theme="dark">` — the CSS selector `[data-theme="dark"]` matched `<body>`, applying dark mode variables to all body descendants.
**Fix**:
1. Added `document.body.setAttribute('data-theme', isDark ? 'dark' : 'light')` in BOTH `toggleTheme()` and `initThemeToggle()`
2. Previous session's fix already cleared inline CSS variable overrides from both `<html>` and `<body>`
**Lesson**: When FOUC prevention scripts set `data-theme` on MULTIPLE elements (html AND body), ALL theme-switching code must update ALL elements. Check every `setAttribute('data-theme', ...)` call and ensure it covers both `document.documentElement` and `document.body`. Use `getComputedStyle(document.body).getPropertyValue('--text-primary')` to debug — if body's variable differs from html's, they're out of sync.

### 47. Help Docs Print Uses window.open() — Popup Blocker (v5.9.5)
**Problem**: Clicking the print button in Help & Documentation showed "Unable to open print window" alert.
**Root Cause**: `HelpContent.printSection()` used `window.open('', '_blank')` to create a new window for printing. Chrome's popup blocker blocks `window.open()` even when called from a click handler if there's any asynchronous code path involved. This is the same pattern as Lesson 9.
**Fix**: Replaced `window.open()` with hidden `<iframe>` approach — creates an off-screen iframe, writes the help content HTML into it, then calls `iframe.contentWindow.print()`. The iframe is cleaned up after the print dialog closes.
**Lesson**: NEVER use `window.open()` for printing. Always use the hidden iframe pattern: create iframe → write content → `contentWindow.focus()` → `contentWindow.print()` → cleanup. This avoids popup blockers entirely.

### 48. Voice Narration System Architecture (v5.9.7)
**Feature**: Added voice narration to the existing Live Demo player system in guide-system.js.
**Architecture**: Three-tier provider chain — (1) Pre-generated MP3 clips from `static/audio/demo/` with manifest.json, (2) Web Speech API (`speechSynthesis`) with automatic sentence chunking to avoid Chrome's 15-second timeout bug, (3) Silent timer fallback (existing behavior).
**Key Design Decisions**:
- Progressive enhancement: demo works identically with or without audio — narration is a pure overlay
- Audio timing overrides step timer: when narration is enabled and audio plays, the step advances when audio finishes + 800ms pause (not on a fixed timer)
- `_showDemoStep()` fires `_playNarration()` as a Promise alongside the typewriter effect — they run in parallel
- Volume control persists via localStorage (`aegis-narration-volume`)
- Voice preference persists via localStorage (`aegis-narration-voice`)
- Chrome 15-sec bug: `_speakText()` splits text into sentences and chains them via `onend` callbacks
- Speed sync: `audio.playbackRate` and `utterance.rate` both sync with `demo.speed` selector
**Server-side**: `demo_audio_generator.py` provides `generate_demo_audio()` that extracts narration text from guide-system.js and generates MP3s via edge-tts (neural, requires internet) or pyttsx3 (system voices, offline). API endpoints at `/api/demo/audio/*`.
**Files**: `guide-system.js` (narration state + provider chain), `guide-system.css` (narration controls styling), `demo_audio_generator.py` (TTS generation), `routes/config_routes.py` (API endpoints), `static/audio/demo/` (audio files + manifest).
**Lesson**: When adding audio to an existing visual system, use a provider chain with automatic fallback. The frontend should never fail because audio is unavailable — it should gracefully degrade. The `_playNarration()` → `true`/`false` return pattern lets the step timer know whether to wait for audio or use its own timing.

### 49. Demo Tooltip Suppression and Double-Start Guard (v5.9.8)
**Problem**: During demo playback, the spotlight tooltip ("STEP 1 OF 1" with Skip/Back/Next buttons) appeared on top of the spotlighted element, obscuring the view. Also, clicking "Watch Demo" rapidly could start multiple demos simultaneously.
**Root Cause**: `showSpotlight()` internally calls `positionTooltip()` which sets `tooltip.style.display = 'block'` and `tooltip.style.visibility = 'visible'` inside a 350ms `setTimeout`. The `_showDemoStep()` code set `tooltip.style.display = 'none'` BEFORE calling `showSpotlight()`, but the 350ms async delay in `showSpotlight` re-showed it.
**Fix**: (1) Moved tooltip hiding to AFTER `showSpotlight()` with a 400ms `setTimeout` (longer than the 350ms in `showSpotlight`), setting both `display: none` and `visibility: hidden`. (2) Added `if (this.demo.isPlaying) return;` guard at top of `startDemo()` and `startFullDemo()` to prevent double-starts from rapid clicks.
**Lesson**: When hiding UI elements that are manipulated by async/setTimeout code, your hiding code must run AFTER the async code completes. Use a longer timeout or a callback/flag to ensure ordering. For user-triggered actions (button clicks), always add idempotency guards (`if (already_running) return`) to prevent duplicate invocations.

### 50. Super-Detailed Demo Scenes — Content Architecture (v5.9.8)
**Enhancement**: Expanded demo scene count from 31 to 79 across all 11 AEGIS modules. Every section now has 5-10 detailed narration scenes covering individual UI elements, sub-features, workflows, and tips.
**Content guidelines for narrated demo scenes**:
- Each narration should be 150-300 characters (2-4 sentences) — enough for 8-10 seconds of speech
- Duration should be 7000-10000ms to allow narration to complete with natural pacing
- Every scene should teach something specific, not repeat general statements
- Scenes should follow the user's workflow order (open → configure → execute → review results → export)
- Sections with tabs (Roles Studio, Metrics) should have one scene per tab
- Scenes can reference features that other sections cover (cross-references build understanding)
- Narration text should use full words ("one hundred" not "100") since it's read aloud by TTS
**Full demo timing**: 79 content scenes + 11 section transition scenes = 90 total scenes. At 1x speed with narration, the full demo runs approximately 10 minutes.

### 51. Missing CSS .hidden Rules for Demo Picker Toggle (v5.9.12)
**Problem**: Demo picker sub-demo cards were invisible when user clicked "Watch Demo" in the guide panel. All 11 sections affected — cards existed in DOM but were pushed below the visible scroll area.
**Root Cause**: The JS code in `_showDemoPicker()` used `helpContent.classList.add('hidden')` and `footer.classList.add('hidden')` to hide help content before showing the picker. But no CSS rules existed for `.panel-help-content.hidden` or `.panel-footer.hidden`. The project had only component-specific `.hidden` selectors (e.g., `.demo-picker.hidden`, `.tips-list.hidden`), not a generic `.hidden { display: none; }`. So the help content stayed visible (512px tall) and pushed the picker to offsetTop 636, below the 774px panel body viewport.
**Fix**: Added two CSS rules in `guide-system.css`: `.panel-help-content.hidden { display: none !important; }` and `.panel-footer.hidden { display: none !important; }`.
**Lesson**: Never assume `.hidden` class works generically. This project uses component-specific `.hidden` selectors — every element that uses `classList.add('hidden')` needs a matching CSS rule. When adding new toggle logic, always verify the CSS selector exists. Use `getComputedStyle(el).display` to confirm elements are actually hidden, not just that the class was added.

### 52. IIFE Public API Must Expose Functions Used by Other Modules (v5.9.14)
**Problem**: Metrics sub-demo preActions used `.click()` on tab buttons (`#ma-tab-btn-quality`, etc.) to switch tabs before playing scenes. But the clicks did nothing — the tab didn't switch.
**Root Cause**: MetricsAnalytics is an IIFE that uses event delegation on `#modal-metrics-analytics` with `e.target.closest('.ma-tab')`. The `switchTab()` function is defined inside the IIFE closure and only exposed `{ init, open, close }` in its public API (line 1492). Despite `.click()` dispatching a real click event that bubbles, the event delegation wasn't triggering. Additionally, `_navigateToSection('metrics')` used `showModal('modal-metrics-analytics')` instead of `MetricsAnalytics.open()`, so data wasn't loaded, making tab rendering impossible even if the click had worked.
**Fix**: (1) Added `switchTab` to the IIFE's public return: `return { init, open, close, switchTab }`. (2) Changed `_navigateToSection('metrics')` to use `MetricsAnalytics.open()`. (3) Updated all 5 metrics preActions to call `window.MetricsAnalytics.switchTab('quality')` directly instead of `.click()`. (4) Fixed namespace from `TWR.MetricsAnalytics` to `window.MetricsAnalytics` (the IIFE assigns to `window.MetricsAnalytics`, not `window.TWR.MetricsAnalytics`).
**Lesson**: When module A (guide-system) needs to control module B (MetricsAnalytics), module B MUST expose that function in its public API. `.click()` on elements controlled by IIFE event delegation is unreliable for programmatic control. Always check the IIFE's `return` statement to see what's actually exposed, and verify the correct namespace (`window.X` vs `window.TWR.X`).

### 53. Sub-Demo Target Selector Audit Checklist (v5.9.13-14)
**Problem**: Of 168 unique selectors used as `target:` in sub-demo scenes, 3 referenced non-existent elements: `#btn-fix-assistant` (actual: `#btn-open-fix-assistant`), `#format-csv-card` and `#format-json-card` (no IDs on those `<label>` elements). Additionally, `#sf-btn-sow` was used in a preAction but doesn't exist — SOW generator is opened via `SowGenerator.open()` API.
**Fix**: Corrected the Fix Assistant target, added IDs to CSV/JSON export cards in index.html, and changed SOW preAction to call the module API.
**Lesson**: When creating sub-demo targets: (1) ALWAYS verify the exact `id` attribute in index.html — don't guess based on naming conventions. (2) For IIFE modules (MetricsAnalytics, SowGenerator, etc.), use their public API methods in preActions, not `.click()` on buttons that trigger internal event delegation. (3) Run a programmatic audit: extract all `target:` selectors from guide-system.js and cross-reference against index.html to catch mismatches before shipping. (4) Elements in modals/dropdowns that only render after user interaction need preActions that open the containing modal first.

### 54. Sub-Demo Modal Force-Show Pattern (v5.9.15)
**Problem**: 9 sub-demos were rated BAD because their preActions didn't open the target modal, so all scenes spotlighted the trigger button instead of actual content. 18 more were PARTIAL — preActions opened the right section but every scene targeted the same element.
**Root Cause**: Sub-demos for modals that aren't normally visible (export, triage, score breakdown, function tags, help) need their preAction to force-show the modal before scenes can target elements inside it. Portfolio sub-demos called `#nav-portfolio` click but needed to use the `Portfolio.open()` API. Several targets used IDs that don't exist (`#sf-sidebar` → `.sf-sidebar`, `#advanced-settings-panel` → `#advanced-panel`, `#file-dropzone` → `#dropzone`, `#results-table` → `#issues-container`).
**Fix pattern for force-shown modals**:
```javascript
preAction: async () => {
    try {
        const modal = document.getElementById('modal-xxx');
        if (modal) {
            modal.classList.add('active');
            modal.style.display = 'flex';
            modal.style.zIndex = '148000';
            AEGISGuide._xxxCleanup = () => {
                modal.classList.remove('active');
                modal.style.display = '';
                modal.style.zIndex = '';
            };
        }
        await AEGISGuide._wait(300);
    } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
},
```
**Cleanup**: Each force-shown modal stores a cleanup function on `AEGISGuide._xxxCleanup`. These are called in both `stopDemo()` and `_navigateToSection()`. Currently 5 cleanups: `_exportCleanup`, `_triageCleanup`, `_scoreCleanup`, `_funcTagsCleanup`, `_helpCleanup`.
**For IIFE modules**: Use the module's public API (e.g., `Portfolio.open()`, `TWR.FunctionTags.showModal()`, `MetricsAnalytics.open()`) instead of `.click()` on nav buttons.
**Lesson**: Every sub-demo that targets elements inside a modal/overlay MUST: (1) force-show the modal in preAction with `display:flex` + `zIndex:148000`, (2) store a cleanup function, (3) have cleanup called on stop AND section navigation. Always verify target selectors exist in the DOM — use `.class-name` for elements without IDs. Run programmatic verification of all targets after changes.

### 55. Help Beacon Must Hide During Demo Playback (v5.9.18)
**Problem**: The ? help beacon (`z-index:150000`) overlaid the demo bar's X stop button (`z-index:149800`) in the bottom-right corner, making it very difficult to click stop during demos.
**Root Cause**: The beacon is `position: fixed; bottom: 32px; right: 32px` and sits at the highest z-index in the app (150000). The demo bar is `position: fixed; bottom: 0` at z-index 149800. The beacon's position directly overlaps the demo bar's control area.
**Fix**: Added `this.refs.beacon.style.display = 'none'` in all 3 demo start locations (`startDemo()`, `startFullDemo()`, `startSubDemo()`) right after `this.demo.isPlaying = true`. Added `this.refs.beacon.style.display = ''` in `stopDemo()` to restore it when demo ends.
**Lesson**: Any persistent floating UI element (beacons, FABs, chat widgets) must be hidden when a full-screen overlay or bottom-bar UI is active. Check all fixed-position elements' z-indices when adding new fixed-position features. The beacon's z-index (150000) was intentionally highest for normal use, but that same priority made it block demo controls.

### 56. `--no-deps` Flag Prevents Dependency Resolution for spaCy
**Problem**: spaCy showed as installed (`pip list` confirmed `spacy 3.8.11`) but `import spacy` failed at runtime.
**Root Cause**: The OneClick installer (line 317) originally installed spaCy with `--no-deps --no-index`:
```bat
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location spacy ...
```
The `--no-deps` flag means pip installs the spaCy wheel itself but does NOT install its 15+ dependencies (thinc, cymem, preshed, blis, murmurhash, srsly, wasabi, weasel, catalogue, confection, etc.). The wheel file gets placed in site-packages, but `import spacy` fails because it can't import thinc, which can't import cymem, etc.
**Fix**: Removed `--no-deps` from lines 316-317. Changed to `--no-index --find-links="%WHEELS%"` only, which lets pip resolve dependencies from the local wheels directory.
**Lesson**: NEVER use `--no-deps` when installing packages that have compiled C extension dependencies (spaCy, numpy, scipy, torch, etc.). The `--no-deps` flag is only safe for the stragglers loop where packages are already installed and you just want to ensure the wheel itself is present. For primary installs, use `--no-index --find-links` without `--no-deps` so pip can resolve the dependency tree from available wheels.

### 57. `replace_all` on Version Strings Can Accidentally Change URLs
**Problem**: When updating installer branding from v5.9.25 to v5.9.26, `replace_all` changed ALL occurrences including the GitHub release download URLs where binary assets are hosted (on the v5.9.21 release).
**Root Cause**: The installer had `v5.9.25` in two contexts: (1) branding/display strings, and (2) release download URLs pointing to where binary assets live. A blanket `replace_all` of `v5.9.25` → `v5.9.26` changed the download URLs from `releases/download/v5.9.25` to `releases/download/v5.9.26` — but there IS no v5.9.26 release with binary assets.
**Fix**: Manually changed the 3 release download URLs back to v5.9.21 (where Python, torch, pip, and models are hosted).
**Lesson**: When using `replace_all` on version strings, ALWAYS check that the replacement doesn't affect URLs, paths, or identifiers that should remain at a different version. Release download URLs and branding strings can contain the same version number for different reasons. Do a preview/diff after `replace_all` to catch unintended changes.

### 58. lxml Version Constraint Rejected Bundled Wheel
**Problem**: lxml failed to install from the wheels directory despite having a wheel file present.
**Root Cause**: `requirements.txt` had `lxml>=4.9.0,<5.0.0` but the bundled wheel was `lxml-5.4.0-cp310-cp310-win_amd64.whl`. The upper bound constraint `<5.0.0` caused pip to reject the v5.4.0 wheel.
**Fix**: Changed `requirements.txt` from `lxml>=4.9.0,<5.0.0` to `lxml>=4.9.0` (removed upper bound).
**Lesson**: When bundling wheels for offline install, verify that version constraints in requirements files don't reject the bundled wheel versions. Run `pip install --dry-run --no-index --find-links=wheels/ -r requirements.txt` to catch constraint conflicts before shipping.

### 59. Offline-First Install Pattern for Optional Packages
**Problem**: `symspellpy`, `proselint`, and `textstat` had wheels in the wheels directory but the installer tried to install them from the internet first (or only from internet), which fails on air-gapped machines.
**Root Cause**: These packages were added to the installer after the initial offline design. The install commands used `pip install <package>` (online) instead of `pip install --no-index --find-links="%WHEELS%" <package>` (offline).
**Fix**: Changed to offline-first pattern with online fallback:
```bat
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location symspellpy 2>nul
if errorlevel 1 (
    echo  [WARN] symspellpy offline install failed, trying online...
    "%PYTHON_DIR%\python.exe" -m pip install --no-warn-script-location symspellpy 2>nul
)
```
**Lesson**: Every package in the OneClick installer MUST use offline-first (`--no-index --find-links`) with online fallback. The target environment is NGC (Northrop Grumman) air-gapped Windows machines. Never assume internet access. The pattern is: try offline → if fail → try online → if fail → warn and continue.

### 60. `requirements-windows.txt` Contains Direct URLs That Fail Offline
**Pattern**: `packaging/requirements-windows.txt` line 44 contains:
```
en_core_web_md @ https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
```
This direct URL download works online but fails silently on air-gapped machines when installed via `pip install --no-index --find-links`. The `--no-index` flag prevents URL resolution, so this line is skipped. The `en_core_web_sm` model is bundled as a wheel in the wheels directory and installed separately — that's the model AEGIS actually uses.
**Lesson**: Direct URL dependencies in requirements files (`package @ https://...`) are incompatible with `--no-index` offline installs. For offline deployments, download the wheel file and include it in the wheels directory instead. The `en_core_web_md` line in requirements-windows.txt is effectively a no-op on air-gapped machines but doesn't cause errors because `--no-index` just skips it.

### 61. Windows-Only Transitive Dependencies Not in Wheels (colorama)
**Problem**: spaCy, Flask, and click all showed `[SKIP]` / `[WARN]` during OneClick installer verification despite pip confirming they were installed in site-packages. The `2>nul` error suppression hid the actual error.
**Root Cause**: `colorama>=0.4.6` is a **Windows-only** transitive dependency required by:
- spaCy → wasabi → colorama (conditional: `sys_platform == "win32"`)
- Flask → click → colorama (conditional: `platform_system == "Windows"`)
Since development is on Mac, colorama never appeared as a dependency. The offline install with `--no-index` couldn't download it, so pip failed silently. The packages installed but their import chains broke at runtime because wasabi/click couldn't import colorama.
**Fix**: (1) Downloaded `colorama-0.4.6-py2.py3-none-any.whl` to `wheels/`. (2) Added `colorama>=0.4.6` to `requirements.txt` and `packaging/requirements-windows.txt`. (3) Install colorama FIRST in OneClick installer (line 315) before Flask/spaCy. (4) Repair script installs colorama as priority before attempting spaCy chain reinstall.
**Lesson**: Always check platform-conditional dependencies when building offline installers on a different OS than the target. Use `pip install --dry-run --report` or `pipdeptree` on the TARGET platform to find all transitive deps. On Windows, `colorama` is required by: click, wasabi, tqdm, pytest, and many others. It should ALWAYS be in the wheels directory for any Windows offline installer.

### 62. Batch Script `errorlevel` Unreliable Across Subroutines
**Problem**: Repair_AEGIS.bat showed false failures — packages that imported successfully were reported as `[FAIL]` with "Error details:" messages.
**Root Cause**: In Windows batch, `errorlevel` is **sticky** — it persists from previous commands and doesn't reset to 0 on success in all contexts. When using `call :subroutine` with `if errorlevel 1` after a Python command, the errorlevel from a PREVIOUS subroutine call could bleed through, causing false positives.
**Attempted fixes that also failed**:
1. **Temp file markers**: `open(r'%TEMPMARK%','w').write('ok')` inside Python `-c` strings crashed because `%TEMP%` path expansion produces backslashes that conflict with Python string parsing, and paths with spaces (OneDrive) break the command.
2. **`&&` / `||` pattern**: `python.exe -c "..." 2>&1 && (success) || (failure)` — also crashes inside `call :subroutine` blocks on some Windows versions.
**Lesson**: Batch scripting for reliable error detection is extremely fragile. For complex diagnostic tools, consider writing the logic in Python instead of batch — a Python script called by a simple 5-line `.bat` wrapper would be far more reliable. The `.bat` file just needs to find python.exe and call the Python script. All the import testing, error capturing, and repair logic belongs in Python where error handling actually works.

### 63. Installer `2>nul` Hides Critical Errors — Use Repair Tool for Diagnosis
**Problem**: The OneClick installer uses `2>nul` on ALL verification commands (lines 589-604), so when `import spacy` fails, the user sees `[SKIP] spaCy (optional)` with zero information about WHY. Multiple sessions were spent guessing at root causes (--no-deps, ._pth file, path spaces) when the actual error was a missing colorama wheel.
**Root Cause**: The `2>nul` pattern was designed to keep output clean for non-technical users. But it also hides the exact Python traceback that would immediately reveal the root cause.
**Fix**: Created `Repair_AEGIS.bat` that runs the same import checks with `2>&1` (errors shown) instead of `2>nul` (errors hidden). This immediately revealed `ERROR: Could not find a version that satisfies the requirement colorama>=0.4.6`.
**Lesson**: NEVER use `2>nul` on diagnostic/verification commands without also providing a way to see the errors. The installer should either: (1) log errors to a file even when suppressing console output, or (2) have a `--verbose` flag, or (3) ship with a separate diagnostic tool. The Repair_AEGIS.bat serves as that diagnostic tool.

### 64. Stragglers Loop Creates Version Churn (Duplicate Wheels)
**Problem**: The OneClick installer's "stragglers" loop (line 348) installs ALL `.whl` files individually with `--no-deps`. When the wheels directory contains multiple versions of the same package (e.g., `filelock-3.24.0` AND `filelock-3.24.2`), this causes packages to be installed, uninstalled, and reinstalled as each version is processed alphabetically. The installer log showed packages like huggingface_hub flip from 1.4.1 → 0.36.2 → 1.4.1.
**Root Cause**: The `wheels/` directory accumulated duplicate versions over time. The `for %%f in (*.whl)` loop processes them alphabetically, and `--no-deps` means pip doesn't check version compatibility — it just force-installs whatever wheel it's given.
**Impact**: Not breaking (final version is usually correct since alphabetically-last wins), but wastes time and produces confusing installer output. Can occasionally leave a WRONG version if the alphabetically-last wheel is an older version.
**Lesson**: Before releasing, deduplicate the wheels directory — keep only the latest version of each package. Use: `pip download -r requirements.txt --dest wheels/ --only-binary=:all:` which always gets latest compatible versions. The stragglers loop should be a safety net, not the primary install mechanism.

### 65. GitHub Release Assets for Installer Updates
**Pattern**: When updating installer `.bat` files, THREE places must be updated:
1. **Main branch** — `Install_AEGIS_OneClick.bat` (root) via GitHub REST API commit
2. **Packaging copy** — `packaging/Install_AEGIS_OneClick.bat` (keep in sync with root)
3. **Release asset** — DELETE old asset + POST new asset on v5.9.21 release
The v5.9.21 release hosts all binary assets (Python, torch, pip, wheels, models). The installer `.bat` files download from this release. When updating the installer, always update the release asset too, or users downloading from the release page get the old version.
**API workflow**: `GET /releases` → find release by tag → `GET release.assets` → find asset by name → `DELETE /releases/assets/{id}` → `POST` to `upload_url` with `?name=filename`.

### 66. OneDrive Paths with Spaces Break Batch Python Commands
**Problem**: Repair_AEGIS.bat crashed when trying to write temp files or execute Python commands with file path arguments on the target machine.
**Root Cause**: The AEGIS install path is `C:\Users\M26402\OneDrive - NGC\Desktop\Doc Review\AEGIS`. The `OneDrive - NGC` segment contains spaces AND a dash. When batch variables expand inside Python `-c` strings (e.g., `open(r'%TEMPMARK%','w')`), the spaces in `%TEMP%` or `%INSTALL_DIR%` paths break the Python command parsing. Quoting helps for batch commands (`"%PYTHON_DIR%\python.exe"`) but not for Python code embedded in `-c` strings that reference batch-expanded paths.
**Lesson**: When writing batch scripts that target machines with OneDrive or paths containing spaces: (1) NEVER embed batch variable paths inside Python `-c` code strings. (2) Keep Python `-c` commands self-contained — no file I/O referencing batch paths. (3) If you need Python to write/read files, pass the path as a command-line argument and use `sys.argv[1]` in the Python code, with proper quoting. (4) Better yet, write a `.py` script file and call it from batch.

### 67. Installer File Inventory — Three .bat Files Must Stay in Sync
**Pattern**: The project has THREE installer-related .bat files that must be kept consistent:
1. `Install_AEGIS_OneClick.bat` (project root) — the "source of truth"
2. `packaging/Install_AEGIS_OneClick.bat` — copy for packaging, must mirror root
3. `Install_AEGIS.bat` (project root) — the manual/legacy installer
After editing the OneClick installer, ALWAYS run: `cp Install_AEGIS_OneClick.bat packaging/Install_AEGIS_OneClick.bat`
Additionally, version branding updates should be applied to ALL three files. Use `replace_all` but then verify URLs weren't accidentally changed (see Lesson 57).
**Also exists**: `install_offline.bat` — simpler offline installer for air-gapped environments. Has its own version reference that needs updating.
**Lesson**: When the project has multiple copies of the same file, document which is the source of truth and always sync after editing. A future improvement would be to have the packaging copy be a symlink or generated from the root copy.

### 68. typer Is Another Windows-Only Transitive Dependency for spaCy
**Problem**: After fixing the `colorama` missing wheel issue, spaCy still failed with `No module named 'typer'`.
**Root Cause**: spaCy (v3.8+) depends on `typer` for its CLI. Like colorama, typer is a pure-Python package that pip normally auto-resolves — but with `--no-index --find-links` offline installs, it was never pulled in because it wasn't explicitly listed in the install command or requirements.
**Fix**: (1) Downloaded `typer-0.24.0-py3-none-any.whl` to `wheels/`. (2) Added `typer>=0.9.0` to `requirements.txt` and `typer==0.24.0` to `packaging/requirements-windows.txt`. (3) Updated OneClick installer to install `colorama typer` together as the first priority install. (4) Updated `repair_aegis.py` to include `typer` in `SPACY_CHAIN`, `CRITICAL_PACKAGES`, the diagnostic groups, and the skip set.
**typer's dependencies**: click, shellingham, rich, annotated-doc — all already present in `wheels/` directory.
**Lesson**: When debugging "module not found" errors for a large package like spaCy, there may be MULTIPLE missing transitive dependencies. Fix one, run again, find the next. The repair tool's visible error messages (no `2>nul`) are essential for this iterative process. Always add newly discovered deps to ALL three places: (1) wheels directory, (2) requirements files, (3) installer install commands.

### 69. Python-Based Repair Tool Replaces Crashing Batch Scripts
**Pattern**: After three failed attempts at writing a batch-only repair tool (Lesson 62: errorlevel unreliable, Lesson 66: OneDrive paths break), the solution is a thin `Repair_AEGIS.bat` wrapper (~75 lines) that:
1. Finds `python.exe` in the AEGIS directory (checks current dir, common locations, prompts user)
2. Finds `repair_aegis.py` in the same directory
3. Calls `"%PYTHON_EXE%" "%REPAIR_PY%"` — proper quoting handles spaces in OneDrive paths
The actual logic lives in `repair_aegis.py` (500 lines) where Python's error handling, string processing, and subprocess management work reliably regardless of path names.
**Files**: `Repair_AEGIS.bat` (thin wrapper), `repair_aegis.py` (all logic)
**Both files** must be in the AEGIS install directory and uploaded as release assets on v5.9.21.
**Lesson**: For any non-trivial Windows tooling, write the logic in Python and use batch only as a 10-line launcher. Batch scripting is fundamentally broken for: error handling (`errorlevel` sticky), string processing (paths with spaces), and control flow (`call :subroutine` + `&&/||`).

### 70. setuptools v82+ Removed pkg_resources (Feb 2026 Breaking Change)
**Problem**: `import pkg_resources` fails with `No module named 'pkg_resources'` even though `pip list` shows setuptools 82.0.0 installed. spaCy's `en_core_web_sm` model requires `pkg_resources` to load.
**Root Cause**: setuptools v82.0 (released ~8 Feb 2026) **completely removed** the `pkg_resources` module. This is a massive breaking change affecting thousands of packages. pip reports "Requirement already satisfied: setuptools (82.0.0)" but the installed version doesn't have the module that everything expects.
**Fix**: (1) Replaced `setuptools-82.0.0-py3-none-any.whl` with `setuptools-80.10.2-py3-none-any.whl` in wheels directory. (2) Pinned `setuptools>=60.0,<81` in `requirements.txt`. (3) Repair tool uses `pip_install(['setuptools<81'], wheels_dir, force=True)` — the `--force-reinstall` is critical because pip sees v82 as "already satisfied" and won't downgrade without it. (4) Batch wrapper pre-flight also uses `--force-reinstall` with `"setuptools<81"` version pin. (5) OneClick installer pins `"setuptools<81"` with `--force-reinstall`.
**Why force-reinstall is required**: pip's default behavior is to skip packages that are already installed. When v82 is installed, `pip install setuptools` returns "already satisfied" even though v82 doesn't have `pkg_resources`. Only `--force-reinstall` combined with `<81` version pin forces pip to actually downgrade.
**Lesson**: Always check the actual version of critical infrastructure packages in the wheels directory. When a package has a major version change that removes functionality (like setuptools dropping pkg_resources), version pinning is essential. The `--force-reinstall` flag is needed when the installed version must be DOWNGRADED, not just installed.

## MANDATORY: Documentation with Every Deliverable
**RULE**: Every code change delivered to the user MUST include:
1. **Changelog update** in `version.json` (and copy to `static/version.json`)
2. **Version bump** if warranted
3. **Help docs update** in `static/js/help-docs.js` if user-facing changes
4. **CLAUDE.md update** if new patterns, lessons, or architecture changes
This is a mandatory step, not optional. The user has explicitly requested this be committed to memory.
