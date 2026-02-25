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
| `proposal_compare/projects.py` | SQLite project management + comparison history + proposal CRUD |
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
- **Current version**: 6.1.11
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

### 71. sspilib — Another Windows-Only Transitive Dependency (pyspnego/requests-ntlm)
**Problem**: `requests-ntlm` import failed with `No module named 'sspilib'` on the Windows machine. The repair tool showed `[FAIL]` for Windows Domain Auth.
**Root Cause**: `requests-ntlm` → `pyspnego>=0.12.0` → `sspilib>=0.3.0` (conditional: `sys_platform == "win32"`). Same pattern as colorama (Lesson 61) and typer (Lesson 68) — a Windows-only transitive dependency that's invisible on Mac development because the platform condition excludes it.
**Fix**: (1) Downloaded `sspilib-0.4.0-cp310-cp310-win_amd64.whl` to `wheels/`. (2) Added `sspilib>=0.3.0` to `requirements.txt` and `packaging/requirements-windows.txt`. (3) Updated OneClick installer to install `sspilib` alongside `colorama` and `typer` as priority Windows deps. (4) Repair tool Step 3f installs `sspilib` before attempting `requests-ntlm` or `requests-negotiate-sspi`.
**Lesson**: The complete list of Windows-only transitive dependencies discovered so far: **colorama** (click/wasabi), **typer** (spaCy CLI), **sspilib** (pyspnego/requests-ntlm). When adding any new package that touches authentication or SSPI on Windows, always check for platform-conditional deps with `pip show <pkg>` on the TARGET platform.

### 72. Repair Tool Import Testing — Subprocess for Reimport-Unsafe Packages
**Problem**: Repair tool's `check_import()` showed false failures for `torch` ("TORCH_LIBRARY can only be registered once") and `requests-negotiate-sspi` ("module 'requests' has no attribute 'adapters'"). Both packages were actually installed and working fine.
**Root Cause**: `check_import()` was deleting modules from `sys.modules` and reimporting them with `importlib.import_module()`. This breaks packages with C extensions that register global state (torch's TORCH_LIBRARY) and packages that depend on submodules of already-imported packages (requests.adapters gets orphaned when requests is removed from sys.modules).
**Fix**: Added `SUBPROCESS_CHECK` set in `check_import()`. Packages in this set are tested via `subprocess.run([sys.executable, '-c', f'import {module_name}'])` instead of in-process reimport. Each subprocess gets a clean Python interpreter state, so no reimport conflicts.
**Packages in SUBPROCESS_CHECK**: `torch`, `requests_negotiate_sspi`
**Lesson**: Never `del sys.modules[x]` + reimport for packages with C extensions, global state registration, or complex submodule dependencies. Use subprocess-based import testing for a clean slate. The subprocess approach is slightly slower but gives accurate results. Also applicable to any diagnostic tool that tests imports in a loop.

### 73. Repair Tool Must Search ALL Wheel Directories (Not Just First)
**Problem**: `find_wheels_dir()` returned the FIRST wheel directory found. `torch` lives in `packaging/wheels/` but `wheels/` was found first, so torch's wheel was never discovered by `pip install --find-links`.
**Root Cause**: The original function returned a single path. When `wheels/` existed, it returned immediately without checking `packaging/wheels/`. pip only searches directories explicitly passed via `--find-links`.
**Fix**: Renamed to `find_wheels_dirs()` (plural). Returns a LIST of all found directories. `pip_install()` now accepts a list and passes multiple `--find-links` flags: `--find-links wheels/ --find-links packaging/wheels/`. All callers updated: `preflight_setuptools()`, Phase 3 repair steps, en_core_web_sm wheel search.
**Lesson**: When an offline installer has wheels split across multiple directories (e.g., `wheels/` for pure-Python, `packaging/wheels/` for large platform-specific binaries), the install tool must search ALL of them. Always pass multiple `--find-links` flags to pip rather than consolidating into one directory.

### 74. coreferee Incompatible with spaCy 3.6+ (Abandoned Library)
**Problem**: During AEGIS startup/document scan, a warning prints: "en_core_web_sm version 3.8.0 is not supported by coreferee please examine coreferee/lang/en/config to see supported models/versions".
**Root Cause**: `coreferee` 1.4.1 (last release June 2023) requires `spaCy <3.6.0`. AEGIS uses spaCy 3.8.x with en_core_web_sm 3.8.0. The library is fundamentally incompatible and hasn't been maintained for 2+ years. The warning is printed by coreferee's internal version check during `nlp.add_pipe('coreferee')` before it raises an exception.
**Fix**: (1) Added model version guard in both `coreference_checker.py` (`_init_nlp()`) and `nlp_enhanced.py` (`_setup_coreference()`): if model version >= 3.6, skip coreferee import entirely and use fallback. (2) Commented out `coreferee>=1.4.0` in `requirements.txt` with explanation. (3) Deleted `coreferee-1.4.1-py3-none-any.whl` from `wheels/`. (4) The coreference checker's `_fallback_check()` method (pattern-matching for paragraph-initial pronouns) works without coreferee.
**Lesson**: Before bundling NLP pipeline components (coreferee, negspacy, etc.), always check their spaCy version constraints on PyPI. Libraries that haven't been updated in 1+ years are likely incompatible with the latest spaCy. The safe pattern is: version-guard before import, graceful fallback, never let an incompatible library print warnings to stdout during startup.

### 75. NTLM/Negotiate Fresh Session Pattern (v5.9.29)
**Problem**: Internal links with 401/403 responses were immediately marked AUTH_REQUIRED without trying Windows SSO authentication. But Chrome authenticates these same links automatically.
**Root Cause**: NTLM/Negotiate authentication is *connection-specific* — the challenge→response handshake happens on a single TCP connection. The validator's shared `requests.Session` across ThreadPoolExecutor threads corrupted the multi-step NTLM handshake state because different threads' auth challenges interfered with each other.
**Fix**: Created `_retry_with_fresh_auth()` method that spins up a brand-new `requests.Session()` with `HttpNegotiateAuth()` for each auth retry. Key settings: `GET` (not HEAD — NTLM needs full HTTP exchange), `stream=True` (don't download file bodies), `allow_redirects=True` (follow auth redirect chain). Also added `_probe_windows_auth()` pre-validation probe and `_is_login_page_redirect()` detection.
**Lesson**: For NTLM/Negotiate auth in multi-threaded code, NEVER share a session across threads. Create a fresh session per auth attempt. The per-URL overhead is negligible compared to the correctness guarantee. This is the same pattern Chrome uses — each tab gets its own connection pool with independent auth state.

### 76. Blanket Domain Downgrades Mask Real Broken Links (v5.9.29)
**Problem**: The validator had two blanket downgrade rules (v5.0.5 and v5.9.1) that converted BROKEN/TIMEOUT/BLOCKED to AUTH_REQUIRED for: (1) any URL on a corporate domain (`.myngc.com`, `.northgrum.com`, etc.), and (2) any URL pointing to a document file extension (`.pdf`, `.docx`, etc.) on enterprise networks. This masked genuinely broken links — if a corporate intranet page was deleted, it would still show as AUTH_REQUIRED instead of BROKEN.
**Fix**: Replaced both blanket rules with a single DNS-only downgrade: only `DNSFAILED` on corporate domains gets downgraded to AUTH_REQUIRED (because internal DNS doesn't resolve from outside VPN). HTTP errors (BROKEN/TIMEOUT/BLOCKED) are now genuine — after the Tier 2 fresh auth retry has already tested them.
**Lesson**: Never auto-convert HTTP errors to AUTH_REQUIRED based solely on domain or file extension. If the server responded with an error (404, 500, timeout after response started), the link is genuinely problematic. Only DNS failures on known-internal domains should be downgraded, because DNS resolution is a network-layer issue (VPN needed), not an application-layer issue.

### 77. SharePoint REST API with Windows SSO (v5.9.29)
**Pattern**: SharePoint Online can be accessed via REST API (`/_api/web/...`) using the same `HttpNegotiateAuth()` from `requests-negotiate-sspi` that the hyperlink validator uses. Zero new dependencies needed.
**Key endpoints**:
- `/_api/web` — Site info (auth probe, returns title/URL)
- `/_api/web/GetFolderByServerRelativeUrl('{path}')/Files` — List files in folder
- `/_api/web/GetFolderByServerRelativeUrl('{path}')/Folders` — List subfolders (for recursion)
- `/_api/web/GetFileByServerRelativeUrl('{path}')/$value` — Download file binary content
**Headers**: `Accept: application/json;odata=verbose`, `Content-Type: application/json;odata=verbose`
**Response format**: OData verbose — data is nested under `d` key, lists under `d.results[]`
**Throttling**: SharePoint returns HTTP 429 with `Retry-After` header. Always respect it.
**Files**: `sharepoint_connector.py` (connector class), `routes/review_routes.py` (endpoints)
**Lesson**: When the target Windows machine already has `requests-negotiate-sspi` installed for one feature (HV auth), you can reuse it for any other corporate system that accepts Windows SSO. SharePoint, JIRA, Confluence, ServiceNow on corporate networks all support Negotiate/NTLM auth.

### 78. Werkzeug 413 — request.max_content_length vs app.config['MAX_CONTENT_LENGTH'] (v5.9.30)
**Problem**: `export_highlighted_excel_endpoint` crashed with `413 Request Entity Too Large` even though the `before_request` handler set `request.max_content_length = 200MB`.
**Root Cause**: Werkzeug's multipart form parser (`formparser.py:389`) reads the content length limit from the Flask app's `MAX_CONTENT_LENGTH` config, not from `request.max_content_length`. The `before_request` hook runs before the view function, but when `request.files` is accessed (lazy property), Werkzeug's `_load_form_data()` calls the multipart parser which checks `app.config['MAX_CONTENT_LENGTH']` — the app-level value the before_request didn't modify.
**Fix**: Three-part approach: (1) Set `request.max_content_length = None` (request-level, unlimited). (2) Set `current_app.config['MAX_CONTENT_LENGTH'] = None` (app-level, unlimited). (3) Save original value on `g._hv_original_max_content` and restore it in `@hv_blueprint.after_request`.
**Lesson**: When overriding Flask's upload size limit for specific routes, you must modify BOTH `request.max_content_length` AND `current_app.config['MAX_CONTENT_LENGTH']`. The request-level only affects direct size checks; the multipart parser reads from the app config. Always restore the app config in an `after_request` handler to prevent the override from leaking to other requests.

### 79. GET Fallback for HEAD-Rejected File Download Links (v5.9.30)
**Problem**: Corporate file servers and document management systems return 401/403 on HEAD requests but serve files correctly on GET. Over 1000 links were falsely flagged as BROKEN.
**Root Cause**: The validator used HEAD requests for speed. Many servers (SharePoint, ADFS-protected doc servers, government file portals) reject HEAD but allow GET. The GET response includes `Content-Disposition: attachment` and document MIME types proving the file is accessible.
**Fix**: Added GET fallback in the 4xx handler: when HEAD returns 401/403, retry with `session.get(url, stream=True)`. Check response for (a) 200-399 status code, (b) Content-Disposition containing 'attachment', (c) Content-Type matching document MIME types (pdf, msword, openxmlformats, excel, powerpoint, octet-stream, zip, opendocument). If GET serves a file → WORKING with "File download link (valid)" message. If GET returns a page → WORKING with "GET fallback" message.
**Key requirement from user**: "I need the link tested to see if it broken or it will open the file" — explicitly rejected URL-pattern guessing and blanket pass approaches. The GET fallback actually tests the link.
**Lesson**: HEAD and GET can return completely different responses on enterprise file servers. Always have a GET fallback for auth-related errors (401/403). Use `stream=True` to avoid downloading file bodies.

### 80. TTS Voice Selection — Prioritize Female Neural Voices (v5.9.30)
**Problem**: Demo narration used a robotic-sounding male voice on Windows.
**Root Cause**: Three places configured TTS voices: (1) `demo_audio_generator.py` — `DEFAULT_VOICE = 'en-US-GuyNeural'` (male). (2) `guide-system.js` Web Speech API — priority list started with "Google US English" (often male/robotic on Windows). (3) `pyttsx3` fallback — picked first English voice found (often male).
**Fix**: (1) Changed edge-tts default to `'en-US-JennyNeural'` (female, natural-sounding neural voice). (2) Rewrote `_selectPreferredVoice()` priority: Microsoft Online neural female (Aria/Jenny/Sonia/Libby) → Microsoft Zira → macOS Samantha/Karen/Moira → Google voices → any en-US. (3) pyttsx3 fallback now searches for female voice patterns (zira, jenny, samantha, etc.) before falling back to any English voice. (4) Set `utterance.pitch = 1.05` for slightly more natural female tone.
**Lesson**: When shipping TTS features, specify the EXACT voice you want as default — don't rely on system defaults which vary wildly by OS. On Windows, Microsoft neural "Online" voices (Aria, Jenny) are dramatically better than standard voices (David, Zira). On macOS, Samantha is the best built-in English voice. Always provide voice selection UI so users can choose.

### 81. Multi-Strategy SSL Fallback for Corporate CA Certificates (v5.9.31)
**Problem**: Corporate internal links (`.northgrum.com`, `.myngc.com`, `ngc.sharepoint.us`) were flagged SSLERROR when they worked fine in Chrome. Hundreds of working links showed as broken.
**Root Cause**: Three compounding issues: (1) Python's `requests` library uses `certifi` (Mozilla CA bundle), NOT the Windows certificate store. Corporate sites use internal CA certificates that certifi doesn't trust → SSL handshake fails. (2) The existing SSL fallback tried `session.head(url, verify=False)` but many corporate servers reject HEAD requests entirely. (3) No attempt at combining SSL bypass with Windows SSO auth — corporate links often need BOTH.
**Fix**: Replaced single HEAD-with-verify=False fallback with a multi-strategy cascade:
- **Strategy 1**: `session.get(url, verify=False, stream=True)` — bypasses cert check with GET (not HEAD), detects file downloads via Content-Type/Content-Disposition, marks as SSL_WARNING if link works.
- **Strategy 2**: Fresh SSO session (`requests.Session()` + `HttpNegotiateAuth()`) with `verify=False` — for corporate domains that need both SSL bypass AND Windows authentication. Creates a brand-new session (no shared state corruption).
- **Retest Strategy 2b**: `get_no_ssl_fresh_auth` — combined `verify=False` + fresh Windows SSO in the retest phase for SSLERROR links on corporate domains.
- **Headless fallback**: Expanded priority URL list to include NGC corporate domains (`.myngc.com`, `.northgrum.com`, `ngc.sharepoint.us`) so headless Chromium (which trusts the OS cert store) catches any remaining SSLERROR links.
- **urllib3 warning suppression**: `urllib3.disable_warnings(InsecureRequestWarning)` since `verify=False` is deliberate for corporate CA bypass.
**Why headless Chromium is the ultimate fallback**: Playwright's Chromium uses the Windows certificate store — same as Chrome. So it trusts the same corporate CA certs that Python's certifi doesn't. Links that fail all `requests`-based strategies will typically succeed with headless because it handles SSL, auth, and JavaScript in one shot.
**Lesson**: When Python's `requests` fails SSL on corporate networks, the root cause is ALWAYS the CA cert bundle mismatch. The fix has 3 layers: (1) `verify=False` with GET (not HEAD) for servers that respond to GET differently, (2) fresh SSO session + verify=False for internal links needing auth, (3) headless Chromium as nuclear option (uses OS cert store). Chrome works because it uses the OS cert store + SPNEGO auth automatically — replicate both in Python fallbacks.

### 82. .mil/.gov Bot Protection Returns 403 — Mark BLOCKED Not BROKEN (v5.9.32)
**Problem**: 12 `public.cyber.mil/stigs/stig-viewing-tools/` links were showing as BROKEN despite working in Chrome.
**Root Cause**: DoD websites use aggressive bot protection (Cloudflare, Akamai, DoD WAF) that returns 403 Forbidden to all non-browser HTTP requests regardless of User-Agent or headers. The TLS fingerprint of Python's `requests` library doesn't match a real browser, so these WAFs block it immediately. The 403 handler at line 1351 tries auth retries and no-auth fallback, but for bot-blocked sites all attempts return 403. The code then falls through to the generic 4xx handler which marks as BROKEN.
**Fix**: Added `.mil`/`.gov` domain detection in the 4xx catchall handler. When a `.mil`/`.gov` domain returns 403/406/418/451, mark as `BLOCKED` instead of `BROKEN`. BLOCKED status is eligible for headless browser retest, and headless Chromium (Playwright) has a genuine browser TLS fingerprint that passes bot protection.
**Lesson**: `.mil`/`.gov` 403 responses are almost never "broken links" — they're bot protection. Always mark as BLOCKED so the headless browser fallback can try them. The headless browser succeeds because it has: (1) genuine Chromium TLS fingerprint, (2) JavaScript execution capability, (3) cookie handling, (4) OS certificate store. For validation pipelines targeting government sites, headless Chromium should be considered a primary validation method, not just a fallback.

### 83. Clean SSL Error Messages — Extract Reason from Verbose Exception (v5.9.32)
**Problem**: SSL_WARNING message showed `"Link works but SSL certificate untrusted by Python: HTTPSConnectionPool(host='x.northgrum.com', port=443): Max retries exceeded..."` — confusing and ugly for users.
**Root Cause**: The SSL fallback code used `str(e)[:80]` from the SSLError exception, which includes the verbose `requests` wrapper: `HTTPSConnectionPool(...): Max retries exceeded with url: ... (Caused by SSLError(SSLCertVerificationError(...)))`. The actual useful information is buried inside nested parentheses.
**Fix**: Added SSL error reason extraction at the SSLError handler that checks for common patterns: `CERTIFICATE_VERIFY_FAILED` → "certificate not trusted (corporate/internal CA)", `HANDSHAKE_FAILURE` → "SSL handshake failed", `certificate has expired` → "certificate expired", `self signed` → "self-signed certificate", `unable to get local issuer` → "certificate issuer not trusted". Falls back to regex extraction of the inner reason string, then to a generic "SSL certificate verification failed".
**Lesson**: Python's `requests` library wraps all SSL errors in verbose `HTTPSConnectionPool` messages. When displaying SSL errors to users, always parse the exception string to extract the meaningful certificate reason. The pattern `re.search(r"Caused by SSLError\([^)]*?'([^']{10,80})'", str(e))` extracts the inner reason from most requests SSLError exceptions.

### 84. Multi-Color Excel Export — Send ALL Results, Not Just Broken (v5.9.33)
**Problem**: Export Highlighted only colored broken links red. User needed ALL rows colored by status (green/yellow/orange/red) to quickly scan a 6,000-row document registry.
**Root Cause**: (1) Frontend only sent broken/issue results (filtered by `brokenStatuses2` array) to reduce payload — but multicolor mode needs ALL results including WORKING. (2) Backend `export_highlighted_excel()` only called `_get_broken_urls()` and aborted if empty — no support for coloring non-broken rows. (3) Export function only had red fill for broken links.
**Fix**: (1) New `export_highlighted_excel_multicolor()` function in `export.py` with `_STATUS_COLORS` dict mapping each status to fill/font colors. (2) Adds "Link Status" and "Link Details" columns to the sheet. (3) Adds "Link Validation Summary" sheet with category counts, detailed breakdown, and color legend. (4) Frontend now sends ALL results (slimmed to essential fields: url, status, status_code, message) with `mode=multicolor` form field. (5) Route selects between multicolor and legacy broken_only mode based on `mode` parameter.
**Color scheme**: Green (`C6EFCE`) = WORKING/OK/REDIRECT. Yellow (`FFF2CC`) = SSL_WARNING/REDIRECT_LOOP. Orange (`FCE4D6`) = AUTH_REQUIRED/BLOCKED. Red (`FFC7CE`) = BROKEN/INVALID/TIMEOUT/DNSFAILED/SSLERROR. Grey (`F2F2F2`) = no URL in row.
**Lesson**: For export features that color-code data, send ALL data points (not just problems). Users want at-a-glance status of everything, not just what's broken. Slim the payload by sending only the fields needed for highlighting (url, status, status_code, message) rather than the full validation result objects. The `_build_url_status_map()` helper creates a URL→result lookup dict with normalized variants for fast per-row matching.

### 85. Werkzeug 413 — request.max_content_length vs app.config['MAX_CONTENT_LENGTH'] (v5.9.34)
**Problem**: `export_highlighted_excel_endpoint` crashed with `413 Request Entity Too Large` on Windows despite `before_request` hook setting `MAX_CONTENT_LENGTH = None`. Error persisted across v5.9.30-v5.9.33. Payload was only ~1.1MB (856KB file + 250KB JSON) — well under the 200MB limit.
**Root Cause**: Werkzeug's `MultiPartParser` in `formparser.py` reads `max_content_length` at the moment `request.files` is first accessed (lazy `_load_form_data()` call). On the Windows embedded Python's Werkzeug version, the blueprint `before_request` hook either didn't execute reliably before the form parser initialization, or the parser cached the limit from a source other than `current_app.config`. The result: despite setting `current_app.config['MAX_CONTENT_LENGTH'] = None` in `before_request`, Werkzeug still raised 413 at line 389 of `formparser.py` during multipart parsing.
**Fix**: Three-layer approach: (1) Set `app.config['MAX_CONTENT_LENGTH'] = None` globally in `app.py` — AEGIS is a local-only tool (localhost:5050), no security reason for an upload limit. (2) Keep blueprint `before_request` hook as safety net. (3) Added inline `request.max_content_length = None` + `current_app.config['MAX_CONTENT_LENGTH'] = None` + `request.environ.pop('MAX_CONTENT_LENGTH', None)` RIGHT BEFORE the first `request.files` access in each export endpoint, plus `try/except RequestEntityTooLarge` wrapper with diagnostic logging.
**Lesson**: When overriding Flask/Werkzeug upload size limits for specific routes, `before_request` hooks are NOT reliable across all Werkzeug versions. The safest approach for local-only tools is to remove `MAX_CONTENT_LENGTH` entirely at the app level (`app.config['MAX_CONTENT_LENGTH'] = None`). If you must keep a global limit, override it at three levels immediately before `request.files` access: `request.max_content_length`, `current_app.config['MAX_CONTENT_LENGTH']`, and `request.environ`. Always wrap `request.files` access in `try/except RequestEntityTooLarge` for defense in depth.

### 86. Persistent Docling Worker Pool for Batch Performance (v5.9.37)
**Problem**: Batch scans processed at 0.3 docs/min. Users reported documents timing out at 1500s (the chunk timeout: 300s × 5 files).
**Root Cause**: `_extract_with_docling_subprocess()` used `multiprocessing.get_context('spawn')` which creates a brand new Python interpreter for EVERY document. Each subprocess must: (1) Start fresh Python, (2) Import docling, torch, transformers, (3) Create DocumentConverter with PDF pipeline, (4) Process one document, (5) Serialize via Queue, (6) Shut down. The import/init overhead was 15-30s per document BEFORE Docling even read the file.
**Fix**: Five-part optimization:
1. **Persistent Docling worker** (`_PersistentDoclingPool`): Module-level singleton that spawns ONE long-lived subprocess. Worker initializes Docling ONCE, then processes documents via request/response queues. Auto-restarts on death. Falls back to legacy per-doc subprocess if persistent worker fails.
2. **batch_mode option**: `review_document()` accepts `options['batch_mode'] = True` which skips `html_preview` generation (mammoth/pymupdf4llm) and `clean_full_text` generation during batch scans. These are only needed for Statement History viewer, not batch results.
3. **Increased workers**: `FOLDER_SCAN_MAX_WORKERS` 3→4, `FOLDER_SCAN_CHUNK_SIZE` 5→8. Safe because persistent worker eliminates per-thread memory pressure from subprocess spawning.
4. **Increased timeout**: `PER_FILE_TIMEOUT` 300s→480s to prevent false timeouts on complex PDFs.
5. **Thread-safe**: `_PersistentDoclingPool` uses a lock for submission but releases it during wait, so multiple batch threads can queue work.
**Architecture**: `_docling_persistent_worker()` runs in spawned subprocess, loops on `request_queue.get()`, sends results on `response_queue`. Sentinel `None` triggers clean shutdown. 600s idle timeout auto-exits unused workers. Parent-side `_PersistentDoclingPool.extract()` submits work under lock, waits outside lock with polling for worker death detection.
**Expected improvement**: From ~0.3 docs/min to ~1-2 docs/min (3-6x faster) — the exact improvement depends on document complexity, but eliminating 15-30s of overhead per document on a 3-4 minute total cycle is significant.
**Key constraint**: ZERO accuracy loss. Docling extraction quality is identical — only the process management changed. User explicitly stated: "I am not looking at losing any accuracy."
**Lesson**: When a subprocess is spawned repeatedly with heavy initialization, convert to a persistent worker pattern. The `spawn` context is still necessary (fork crashes on macOS), but the subprocess stays alive across documents. The Queue-based request/response pattern gives clean process isolation while amortizing initialization cost across the entire batch.

### 87. SharePoint Connect & Scan — One-Click Flow and Connection Diagnostics (v5.9.38)
**Problem**: SharePoint batch scan required 4 clicks (paste URL → Test → Preview → Scan All) and showed generic "Cannot reach SharePoint server" errors with no diagnostic detail. Library path required manual entry even though it could be auto-detected.
**Root Cause**: (1) The `test_connection()` error handler at line 392 was a catch-all `ConnectionError` handler that swallowed the actual error details (SSL cert, DNS failure, proxy, timeout) into a generic message. (2) The connector's default timeout was 30s — too short for some corporate networks with proxy inspection. (3) The multi-step UX required the user to click Test (waits for connection), then Preview (waits for discovery), then Scan All (starts polling). (4) Library path auto-detection happened only after Test succeeded, not during the scan flow.
**Fix**: Four-part improvement:
1. **Enhanced error diagnostics**: `test_connection()` now categorizes ConnectionError into specific types: SSL/certificate, DNS/getaddrinfo, connection refused, timeout, proxy, reset by peer, and max retries (with inner reason extraction via regex). Includes auth method in error message for diagnostics.
2. **Connection resilience**: Default timeout increased 30s→45s. All ConnectionErrors now trigger SSL bypass (not just SSL-specific ones) because corporate proxies can wrap SSL issues in generic ConnectionError. On retry, creates fresh session with SSO auth.
3. **One-click "Connect & Scan"**: New `connect_and_discover()` method combines test + auto-detect library + list files. New `/api/review/sharepoint-connect-and-scan` endpoint does test+discover+start-scan in one call. Frontend "Connect & Scan" button replaces the 3-button flow.
4. **Auto-populate library path**: URL paste auto-parses library path client-side. Server-side auto-detection fills it if not found in URL. Library path field placeholder changed to "(auto-detected)".
**Files**: `sharepoint_connector.py`, `routes/review_routes.py`, `templates/index.html`, `static/js/app.js`
**Lesson**: Multi-step connection flows are UX friction — combine them into one-click operations. For corporate network debugging, always log the full error and categorize ConnectionError subtypes (SSL vs DNS vs proxy vs timeout) rather than using a catch-all message. Users can't fix "Cannot reach server" but CAN fix "DNS resolution failed — check VPN".

### 88. Batch Scan Minimize/Restore and Portfolio Batch Count Mismatch (v5.9.39)
**Problem**: (1) Clicking outside the batch scan modal during an active scan closed it with no way to get back. (2) Portfolio batch detail view showed different document counts (e.g., "2 docs" on card, "16 docs" inside detail).
**Root Cause**: (1) `closeBatchModal()` did `modal.style.display = 'none'` unconditionally with no "minimize to badge" option. (2) Portfolio `/api/portfolio/batches` (card view) groups scans within a 30-second window, but `/api/portfolio/batch/<id>` (detail view) queried with `BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')` — a 10-minute window that pulls in scans from separate batches.
**Fix**: (1) Implemented minimize/restore pattern matching HV cinematic progress: `minimizeBatchModal()` hides modal, creates `.batch-mini-badge` with SVG progress ring and percentage. `restoreBatchModal()` shows modal and removes badge. `closeBatchModal()` now checks `_isBatchScanStillRunning()` and calls `minimizeBatchModal()` if any scan is active. Minimize button shown in modal header during active scans. Badge loop reads percentage from whichever dashboard is active (batch/folder/SP). (2) Changed detail query from `±5 minutes` to `±30 seconds` to match the card view's `BATCH_TIME_WINDOW_SECONDS = 30`.
**Files**: `static/js/app.js` (minimize/restore functions), `static/css/features/batch-progress-dashboard.css` (mini badge styling), `templates/index.html` (minimize button), `portfolio/routes.py` (detail query window fix)
**Lesson**: When a modal hosts a long-running operation, NEVER close it on outside-click — minimize to a floating indicator instead. For batch grouping, use the SAME time window constant in both the list view and detail view queries. Two different window sizes cause visible count mismatches that confuse users.

### 89. Metrics & Analytics Cross-Module Tab Pattern (v5.9.40)
**Feature**: Added a "Proposals" tab to the Metrics & Analytics dashboard that fetches data from a SEPARATE API endpoint (`/api/proposal-compare/metrics`) rather than the main `/api/metrics/dashboard` endpoint.
**Architecture**: The existing 5 M&A tabs (Overview, Quality, Statements, Roles, Documents) all render from the same `data` object fetched once from `/api/metrics/dashboard`. The Proposals tab uses a separate `proposalData` cache with its own timestamp, fetched lazily only when the user clicks the Proposals tab. This avoids bloating the main dashboard endpoint and gracefully degrades when the proposal compare module isn't configured.
**Key pattern**: `renderProposalsTab()` checks `proposalData` cache first (5-min TTL, same as main data), fetches from `/api/proposal-compare/metrics` if stale, and renders 4 hero stats + 4 charts + activity table with drill-down. If the fetch fails (module not installed, no data, etc.), shows a friendly empty state instead of breaking the dashboard.
**Files**: `metrics-analytics.js` (new renderProposalsTab + helpers), `metrics-analytics.css` (ma-grid-2col responsive), `templates/index.html` (tab button + panel), `guide-system.js` (demo scene + sub-demo)
**Lesson**: When integrating cross-module data into a shared dashboard, use lazy loading with a separate cache rather than bundling into the main data fetch. This keeps the primary endpoint fast and prevents failures in optional modules from blocking the core dashboard. The tab pattern (fetch on first visit, cache for N minutes, show empty state on error) works well for any cross-module integration.

### 90. Docling Daemon Process Restriction on Windows (v5.9.40)
**Problem**: Batch scan processing 63 documents took 70+ minutes at 0.2 docs/min. Docling timed out on every single file with "subprocess timed out after 60s" errors.
**Root Cause**: Three compounding issues:
1. **daemon=True restriction**: The persistent Docling worker (`_PersistentDoclingPool`) was spawned with `daemon=True`. On Windows, daemon processes cannot spawn child processes — and Docling uses `multiprocessing` internally. So the persistent worker always failed silently, falling back to per-document subprocess spawning.
2. **Invalid DOCLING_ARTIFACTS_PATH**: The environment variable pointed to `C:/Users/M26402/OneDrive - NGC/Desktop/doclingtest/TechWriterReview/docling_models` — an old test folder. Every subprocess failed the artifacts_path validation.
3. **No session-broken flag**: After the first Docling failure, every subsequent file in the batch still attempted Docling, waited 60s for timeout, then fell back. 63 files × 60s = 63 minutes wasted.
**Fix**: (1) Changed `daemon=False` with `atexit` cleanup handler for the non-daemon process. (2) Added artifacts_path validation + auto-detection relative to `docling_extractor.py`'s own directory. (3) Added `_docling_session_broken` module-level flag — first failure marks it True, all subsequent files skip Docling instantly. (4) Reduced chunk size 8→5 and workers 4→3 for stability.
**Lesson**: On Windows, NEVER use `daemon=True` for processes that need to spawn their own children (Docling, torch, any ML framework with multiprocessing). Use `daemon=False` + `atexit` cleanup instead. Always validate env var paths on startup and have auto-detection fallbacks. For batch operations, a "session broken" flag prevents repeating expensive failures across hundreds of files.

### 91. request.max_content_length Read-Only on Windows Werkzeug (v5.9.40)
**Problem**: Export Highlighted crashed with `AttributeError: can't set attribute 'max_content_length'` on the Windows machine. The error occurred in the `before_request` hook, preventing ALL export-highlighted requests from even reaching the endpoint.
**Root Cause**: The Windows embedded Python ships with a Werkzeug version where `request.max_content_length` is implemented as a **read-only property** (getter only, no setter). The Mac development Werkzeug has a settable property. The `before_request` hook and the endpoint body both did `request.max_content_length = None` which crashed with `AttributeError`.
**Fix**: Wrapped all 3 locations that set `request.max_content_length` in `try/except (AttributeError, TypeError): pass`. The `current_app.config['MAX_CONTENT_LENGTH'] = None` line (which IS settable on all versions) does the actual heavy lifting. The `request.max_content_length` was just belt-and-suspenders.
**Files**: `hyperlink_validator/routes.py` — `_hv_increase_upload_limit()` before_request hook, DOCX export endpoint (~line 1785), Excel export endpoint (~line 1916)
**Lesson**: Never assume Flask/Werkzeug properties are settable across versions. Always wrap property assignments in `try/except AttributeError` when the code must work on multiple Werkzeug versions. The Mac development environment and Windows production can have different Werkzeug behaviors. Use `current_app.config` as the primary mechanism since it's always a regular dict.

### 92. Missing /api/capabilities Endpoint Caused Boot Error (v5.9.40)
**Problem**: `checkCapabilities()` in app.js called `fetch('/api/capabilities')` during boot, but no such endpoint existed. The call silently failed (wrapped in try-catch), but `State.capabilities` stayed undefined, causing export buttons (Excel, PDF) to show as disabled with "install openpyxl"/"install reportlab" tooltips even when those packages were installed.
**Root Cause**: The endpoint was referenced in app.js (line 773) and tests.py (lines 956, 971) but never implemented. Only `/api/extraction/capabilities` existed (different endpoint, different response format).
**Fix**: Added `/api/capabilities` endpoint in `config_routes.py` that returns `{success: true, data: {version, capabilities: {excel_export, pdf_export, docling, mammoth, spacy, proposal_compare, sharepoint}}}`. Each capability is detected via try/except import.
**Lesson**: When adding `fetch()` calls to the boot sequence, always implement the corresponding endpoint first. Silent failures in capability checks cascade to broken UI states (disabled buttons, missing features) that are hard to diagnose because there's no visible error. Always search for endpoint usage across frontend AND test files before shipping.

### 93. Proposal Compare z-index Behind Landing Page Tiles on Windows Chrome (v5.9.40)
**Problem**: Clicking the Proposal Compare tile on the landing page opened the modal BEHIND the dashboard tiles — the user could see it was loading but couldn't interact with it.
**Root Cause**: The `.pc-modal` CSS had `z-index: 10001` and the `.lp-page` (landing page) had `z-index: 9999`. Theoretically 10001 > 9999 should work since both are `position: fixed` at the root level. BUT — on Windows Chrome, the `backdrop-filter: blur(8px)` on `.lp-tile` elements creates an implicit stacking context that can elevate tiles above their parent's z-index in certain compositing scenarios.
**Fix**: Bumped `.pc-modal` z-index from 10001 to 15000 in both CSS (`proposal-compare.css`) and JavaScript (`ProposalCompare.open()` sets `modal.style.zIndex = '15000'`). Updated `landing-page.css` override rule to match. The belt-and-suspenders approach (CSS + JS) ensures it works regardless of CSS loading order.
**Lesson**: `backdrop-filter` creates a new stacking context (per CSS spec). When any descendant element has `backdrop-filter`, that element and its children form an independent layer. On some browsers/platforms (notably Windows Chrome), this can cause unexpected stacking behavior where the backdrop-filter element appears above siblings that have lower or equal z-index to the parent. Solution: use a significantly higher z-index (15000 vs 10001) to guarantee visibility, not just barely-above.

### 94. apply_v5.x.xx.py Update Script Pattern (v5.9.40)
**Pattern**: When delivering updates to the user, create an `apply_v{VERSION}.py` script that:
1. Downloads all changed files from GitHub (`raw.githubusercontent.com`)
2. Creates timestamped backup of each file before overwriting
3. Places files directly into the AEGIS install directory (no intermediary)
4. Verifies it's running from the correct directory (checks for `app.py` and `static/`)
5. Creates necessary directories (e.g., `proposal_compare/` with `__init__.py`)
6. Uses the same SSL fallback pattern as all other download scripts
7. No external dependencies — Python standard library only
8. Prints summary of changes, next steps, and backup location
**Files**: `apply_v5.9.40.py` (this version), prior examples: `apply_v5.9.33.py` through `apply_v5.9.38.py`
**Lesson**: Always provide BOTH `pull_updates.py` (for AEGIS built-in updater) AND `apply_v{VERSION}.py` (direct updater) for each release. The `apply_v{VERSION}.py` script is more reliable because it places files directly without requiring the AEGIS app to be running.

### 95. Update Button Never Shown — display:none Without Toggle (v5.9.40)
**Problem**: In Settings > Updates, clicking "Check for Updates" found updates and showed the list, but the "Apply Updates" button never appeared. Users could see updates were available but had no way to apply them from the UI.
**Root Cause**: `#btn-apply-updates` in index.html starts with `style="display:none;"`. The `checkForUpdates()` function in `update-functions.js` showed the `#updates-available` div and populated the file list, but **never toggled the button visible**. The button's display was never changed from `none` to anything visible.
**Fix**: Added `document.getElementById('btn-apply-updates').style.display = 'inline-flex'` when updates are found (line 63), and `display = 'none'` when no updates found (line 102).
**Files**: `static/js/update-functions.js`
**Lesson**: When an HTML element starts with `display:none`, EVERY code path that should show it must explicitly set display. Search for ALL references to the element ID to confirm at least one code path makes it visible. A hidden button that's never shown is invisible to the user but invisible to code reviewers too — always test the full UI flow (check → show list → show button → click apply).

### 96. Proposal Compare Module Architecture (v5.9.41 / v2.1)
**Pattern**: The Proposal Compare module is a multi-file feature:
**Backend** (`proposal_compare/`):
- `parser.py` — `ProposalParser` class extracts financial data from DOCX/PDF/XLSX. Text extraction before tables, 5-strategy company name detection with filename fallback. Regex-based dollar amount detection.
- `analyzer.py` — Centralized `_generate_proposal_ids()` helper ensures consistent IDs. Totals computed from aligned items (not raw extraction). Executive summary, red flags (FAR 15.404), heatmap, vendor scores (A-F).
- `routes.py` — 16 API endpoints under `/api/proposal-compare/*` including upload, extract, compare, projects CRUD, metrics, history (list/get/delete).
- `projects.py` — SQLite-based project management + comparison history. `save_comparison()` stores proposals_json for history re-editing. `list_comparisons()`, `get_comparison()`, `delete_comparison()`.
**Frontend**:
- `static/js/features/proposal-compare.js` (~2700 lines) — `window.ProposalCompare` IIFE with 4-phase workflow (upload→extract→review→results), split-pane review phase, comparison history, 8-tab results.
- `static/css/features/proposal-compare.css` (~900 lines) — Styling for all phases including review split-pane, doc viewer, line item editor, history cards, dark mode.
**Review phase**: Split-pane with document viewer (left) + metadata editor (right). One proposal at a time with prev/next nav. Doc viewer: PDF.js for PDFs, extracted text for DOCX, HTML tables for XLSX. Uses blob URLs from `State.files[]`, cleaned up on phase exit.
**Line item editor**: Accordion toggle, scrollable table with description/category/amount/qty/unit_price columns, add/delete rows. Categories: Labor, Material, Software, Travel, ODC, Subcontract, Other.
**Comparison history**: Auto-saved via routes.py compare endpoint. Frontend: History button in upload phase, card list with vendor badges, View/Delete actions. Loaded comparisons restore `State.proposals` from `_proposals_input` for Back to Review.
**8 Result Tabs**: executive (summary + tornado chart), comparison (sortable/filterable matrix), categories (stacked bar), red_flags (risk), heatmap (deviation grid), vendor_scores (letter grades + radar chart + weight sliders), details (per-vendor), raw_tables.
**Modal**: Uses custom `.pc-modal` class (not standard `.modal`), z-index 15000 to clear landing page stacking contexts.
**Key pattern**: Pure extraction, NO AI/LLM — displays only what's found in documents. Prevents hallucination.
**Public API**: `{ open, close, _removeFile, _restart, _backToReview, _export, _loadHistory }`

### 97. Metrics & Analytics Cross-Module Integration Pattern (v5.9.40)
**Pattern**: When adding a new tool/module to AEGIS, it must be reflected in the Metrics & Analytics dashboard:
1. Add a new tab to the M&A IIFE (`metrics-analytics.js`) with `renderXxxTab()` function
2. Use lazy loading — fetch data from the module's own metrics endpoint only when tab is clicked
3. Cache with separate timestamp (e.g., `proposalData`, `proposalDataTimestamp`) independent of main metrics
4. Provide graceful empty state when module has no data or isn't installed
5. Add tab button in `index.html` M&A modal, tab panel with chart canvases
6. Add CSS for any new grid layouts (e.g., `.ma-grid-2col`)
**API pattern**: Module provides `/api/{module}/metrics` endpoint returning aggregated stats. M&A fetches from it, not from the module's regular data endpoints.
**Lesson**: Keep M&A in lockstep with feature additions. When adding a new feature, always add a corresponding M&A tab. The user has explicitly requested this pattern be maintained.

### 98. PDF.js Vendor Files Not Deployed — Must Include in Updater or Provide Fallback (v5.9.41)
**Problem**: "Failed to render PDF" error in Proposal Compare's document viewer on Windows. Users saw a dead-end error with no way to view the document content.
**Root Cause**: Three compounding issues: (1) PDF.js vendor files (`static/js/vendor/pdfjs/pdf.min.mjs` and `pdf.worker.min.mjs`) exist on the dev Mac but were **never included in any installer or updater script** (`Install_AEGIS_OneClick.bat`, `apply_v5.9.*.py`). (2) `_renderDocViewer()` in `proposal-compare.js` had no text fallback for PDFs — when PDF.js failed, it showed a static error message with no alternative content. (3) `ProposalData` dataclass in `parser.py` never stored the extracted text — the `full_text` variable was local to each parse function and discarded after company name/date extraction.
**Fix**: (1) Added `extraction_text` field to `ProposalData` dataclass and `to_dict()`. All 3 parsers (Excel, DOCX, PDF) now store extracted text. (2) Rewrote `_renderDocViewer()` PDF path: tries PDF.js first, catches failure, falls back to showing extracted text with an info notice. (3) Modified `pdf-viewer.js` `render()` to re-throw errors so callers can catch and provide fallback content. (4) Wrapped Statement History's `PDFViewer.render()` call in try/catch with text fallback. (5) Added `console.log`/`console.error` throughout for F12 debugging.
**Key insight**: The error was entirely client-side — backend logging captured nothing because PDF parsing succeeded fine. The render failure happened when the browser tried to load PDF.js ESM modules that didn't exist on disk.
**Lesson**: When a feature depends on vendor libraries (PDF.js, D3.js, Chart.js, etc.), ALWAYS verify those vendor files are included in the deployment/update mechanism. Dev machine having the files doesn't mean production has them. Every viewer/renderer should have a graceful text-based fallback — never show a dead-end error when you have the data to display in a simpler format. Store extracted text in the response even if a rich renderer is the primary display path.

### 99. PDFViewer.render() Error Propagation — Re-throw for Caller Fallback (v5.9.41)
**Problem**: `TWR.PDFViewer.render()` swallowed all errors internally (try/catch at line 85 set `container.innerHTML` to error message but didn't re-throw). Callers had no way to detect failure and provide alternative content.
**Fix**: Added `throw e` after setting the error innerHTML in the catch block, and `throw new Error(...)` after the init failure path. All existing callers updated with try/catch: `proposal-compare.js` uses `.catch()` on the Promise, `statement-history.js` uses `try/await/catch` with fallback to text rendering.
**Lesson**: Shared rendering utilities should re-throw errors after displaying their own error state, so callers can choose to replace the error with fallback content. The pattern is: (1) render utility shows its own error message, (2) re-throws, (3) caller catches and optionally replaces with richer fallback. Without re-throw, every caller is stuck with the utility's generic error message.

### 100. Server-Side File Serving vs Blob URLs for PDF.js (v5.9.41)
**Problem**: PDF.js `render()` failed with `"unexpected server response (0)"` when given a blob URL (`blob:http://localhost:5050/...`). The File object backing the blob was garbage collected or the blob was revoked before PDF.js could fetch it.
**Root Cause**: `URL.createObjectURL(file)` creates a temporary URL that references the in-memory File object. PDF.js uses `fetch()` internally to retrieve the PDF data from that URL. If the File object is GC'd, the browser context changes, or the blob is revoked, the fetch returns status 0 (network-level failure). This is especially unreliable across async operations and module boundaries.
**Fix**: Switched to server-side file serving — the same pattern used by Statement History (`/api/scan-history/document-file`):
1. Upload endpoint saves files to `temp/proposals/` with timestamp prefix (instead of deleting after parse)
2. New `GET /api/proposal-compare/file/<filename>` endpoint serves files via Flask's `send_file()`
3. Frontend uses `'/api/proposal-compare/file/' + encodeURIComponent(p._server_file)` instead of blob URL
4. `_cleanup_old_proposal_files()` helper removes files older than 1 hour to prevent disk bloat
**Key insight**: Blob URLs are unreliable for libraries that `fetch()` from them asynchronously (PDF.js, video players, etc.). Server URLs via `send_file()` are always available as long as the file exists on disk.
**Lesson**: When a module needs to display uploaded files (PDF, images, etc.), ALWAYS use server-side file serving with `send_file()` — never blob URLs. The pattern is: (1) save uploaded file to a temp directory with timestamp prefix, (2) add a GET endpoint that serves the file, (3) add periodic cleanup of old files, (4) frontend constructs server URL from filename returned in upload response. This is the standard AEGIS pattern and should be used for any future file viewer features.

### 101. Contract Term Detection — Regex Patterns for Government Proposals (v5.9.41)
**Feature**: `extract_contract_term(text)` in `proposal_compare/parser.py` detects contract period/term from proposal text.
**Regex priority**: (1) "X-year contract/period/term", (2) "base year plus N option(s)", (3) "period of performance: N months", (4) "BY / OY1 / OY2" abbreviation patterns, (5) XLSX sheet tab names ("Year 1", "BY", "OY1").
**Output**: `contract_term` string on `ProposalData` (e.g., "3 Year", "Base + 4 Options", "36 Months") and `contract_periods` list of dicts.
**Used for**: Multi-term vendor disambiguation in `analyzer.py` — when two proposals share `company_name`, appends `contract_term` for unique IDs (e.g., "Acme Corp (3 Year)" vs "Acme Corp (5 Year)").
**Lesson**: Government proposals use highly varied terminology for contract periods. The regex chain must try the most specific patterns first (exact "X-year" matches) before falling back to abbreviation patterns (BY/OY) which have more false positives.

### 102. Indirect Rate Detection — Overhead, G&A, Fringe, Fee Patterns (v5.9.41)
**Feature**: `detect_indirect_rates()` in `proposal_compare/analyzer.py` identifies overhead, G&A, fringe, and fee/profit line items from proposal data.
**Pattern matching**: Checks line item descriptions for keywords: "overhead"/"OH"/"indirect", "G&A"/"general and administrative", "fringe"/"benefits", "fee"/"profit"/"margin". Calculates implied rates when dollar amounts are given (e.g., `fringe_rate = fringe$ / labor$`).
**Flag thresholds**: Fringe 25-45%, OH 40-120%, G&A 10-25%, fee 8-15%. Rates outside these ranges generate red flag warnings.
**Lesson**: Indirect rate analysis requires careful base-cost identification — the denominator matters. Fringe is typically against direct labor only, while G&A is against total direct + OH costs. Always flag rates outside typical ranges but never auto-reject — government contracts can have legitimate outlier rates.

### 103. Auto-Calculation of Missing Financial Fields (v5.9.41)
**Feature**: `_auto_calculate_line_items(items)` in `proposal_compare/parser.py` fills missing financial fields:
- qty + unit_price → amount = qty * unit_price
- amount + qty → unit_price = amount / qty
- amount + unit_price → qty = amount / unit_price
**Called at**: End of each parser (XLSX ~line 935, DOCX ~line 1044, PDF ~line 1314).
**Frontend mirror**: `proposal-compare.js` has matching `input` event delegation on `.pc-li-amount`, `.pc-li-qty`, `.pc-li-unit` fields. When 2 of 3 are filled, auto-computes the third with `.pc-auto-calc` CSS class (italic, info color).
**Lesson**: Financial auto-calc should happen in BOTH backend (parser) and frontend (live editing). Backend handles extraction gaps; frontend handles user edits. Always mark auto-calculated values distinctly (CSS class, confidence field) so users know which values are computed vs extracted.

### 104. Click-to-Populate from Document Viewer (v5.9.41)
**Pattern**: In Proposal Compare's Review phase, users can select text in the document viewer and populate form fields.
**Architecture**: Three event listeners on the review container:
1. `focusin` on `.pc-review-edit-panel` tracks `State._lastFocusedField` (last focused input)
2. `mouseup` on `#pc-doc-viewer` checks `window.getSelection()`, shows positioned "Use" popover button
3. `scroll` on `#pc-doc-viewer` removes popover on scroll
**Popover**: Fixed-position button at click coordinates (`e.clientX`, `e.clientY - 36`), auto-removes after 3 seconds. On click, populates field with optional currency formatting for amount/unit fields.
**Lesson**: Click-to-populate UX requires tracking TWO things independently: which field the user wants to fill (via focus tracking) and what text they want to use (via selection detection). The popover must be `position: fixed` (not absolute) because the click coordinates are viewport-relative. Always auto-remove the popover after a short timeout to prevent stale popovers.

### 105. HV Auth Diagnostic Endpoint and Badge Pattern (v5.9.41)
**Feature**: `POST /api/hyperlink-validator/diagnose-auth` returns Windows SSO auth status: `windows_auth_available`, `auth_method`, `auth_init_error`, `platform`. Optional `test_url` in body probes a URL with fresh SSO session.
**Frontend badge**: `_fetchAuthBadge()` called on HV modal open. Shows green "Shield-check: Windows SSO" or red "Shield-off: Anonymous" badge in modal header. Uses Lucide icons.
**Module variables**: `_auth_method` (string: 'negotiate-sspi', 'ntlm', 'none'), `_auth_init_error` (string or None) added to `validator.py` for diagnostic reporting.
**Lesson**: Auth diagnostic endpoints are essential for corporate environments where SSO can fail silently. The badge gives users immediate visual feedback about their auth state before they run a validation. Always expose the `init_error` so the user can report it to IT.

### 106. Headless-First Routing for .mil/.gov Domains (v5.9.41)
**Pattern**: In `hyperlink_validator/validator.py`, before the standard retry loop, check if the domain is `.mil` or `.gov`. If yes AND headless validator is available, immediately mark as `BLOCKED` with message "Government site — routed to headless browser validation" and return. This skips the 10-30s timeout from HEAD/GET requests that always fail on DoD WAFs.
**Why**: Government sites use aggressive bot protection (Cloudflare, Akamai, DoD WAF) that rejects ALL Python `requests` attempts regardless of headers/auth. Only a real browser TLS fingerprint (headless Chromium) passes.
**Performance impact**: Saves 10-30s per .mil/.gov URL by skipping doomed HTTP attempts. For documents with 50+ .mil links, this saves 8-25 minutes of validation time.
**Lesson**: When a class of URLs is KNOWN to always fail with standard HTTP clients, short-circuit before the retry loop. Don't waste time on strategies that can't work. The BLOCKED status feeds into the headless retest phase which handles them correctly.

### 107. SharePoint Corporate Domain Auto-Detection Pattern (v5.9.41)
**Pattern**: In `sharepoint_connector.py __init__()`, auto-detect corporate domains:
```python
_corp_patterns = ('sharepoint.us', 'sharepoint.com', '.ngc.', '.myngc.', '.northgrum.', '.northropgrumman.')
_is_corp = any(p in site_url.lower() for p in _corp_patterns)
self.ssl_verify = not _is_corp
```
Auto-disables SSL verification for corporate SharePoint because Python's `certifi` bundle doesn't trust internal CA certificates.
**404 retry**: `download_file()` on 404 → creates fresh `requests.Session()` with `HttpNegotiateAuth()` → retries once. SharePoint returns transient 404s especially under load or after session timeout.
**Lesson**: For corporate SharePoint connectors, assume SSL will fail and default to `verify=False` for known corporate domains. Transient 404s are common on SharePoint — always retry file downloads once with a fresh session before reporting failure.

### 108. HV Blueprint Import — except ImportError Too Narrow (v5.9.42)
**Problem**: Hyperlink Validator returned "resource not found" (404) for all API endpoints on Windows machine.
**Root Cause**: `routes.py` lines 28-33 caught only `ImportError` when importing `config_logging`. On the Windows machine, `config_logging.get_logger()` → `StructuredLogger._setup_logger()` → `RotatingFileHandler()` failed with a non-ImportError exception (likely `PermissionError` or `OSError` from OneDrive path). Since the except clause only caught `ImportError`, `logger` was never assigned, causing `NameError: name 'logger' is not defined` when any module-level code tried to use it. This prevented the entire HV blueprint from registering.
**Fix**: Changed `except ImportError:` to `except Exception:` in the config_logging import block. This ensures `logger` always gets assigned via the fallback `logging.getLogger()` path.
**Lesson**: When importing optional modules with initialization side effects (creating file handlers, connecting to services, etc.), ALWAYS use `except Exception`, not just `except ImportError`. The module may import fine but fail during initialization with `OSError`, `PermissionError`, `TypeError`, etc. Especially critical on Windows where OneDrive path locking and permission issues are common.

### 109. Edit Persistence — Fire-and-Forget DB Writes (v5.9.42)
**Pattern**: When users edit proposal data in the review phase (`_captureReviewEdits()`), edits are persisted to the database via a fire-and-forget `fetch()` PUT call. The edits travel in-memory to the comparison regardless of DB write success. The `_db_id` is tracked from the upload response and attached to the proposal data object.
**Lesson**: For real-time editing UX, always persist edits asynchronously (fire-and-forget) so the UI doesn't block. Track the database ID from the initial save so subsequent edits can be persisted. The in-memory state is always the source of truth for the current session; the DB is the persistence layer for cross-session survival.

### 110. Project Dashboard Architecture (v5.9.42)
**Pattern**: The Project Dashboard is a new "phase" within the Proposal Compare IIFE, accessible via a "Projects" button in the upload phase header. It has two views:
1. **Grid View** (`renderProjectDashboard()`) — 2-column CSS grid of project cards
2. **Detail View** (`renderProjectDetail(projectId)`) — proposals list + comparisons list for a specific project
**Tag-to-Project** uses a fixed-position dropdown (`_showTagToProjectMenu()`) that supports both in-memory proposals (add to project) and DB-backed proposals (move between projects).
**Edit from Dashboard** fetches full proposal data via GET, enters review phase with a "Save & Back" button, and auto-persists changes on save.

### 111. openpyxl ws.hyperlinks vs cell.hyperlink Discrepancy (v5.9.43)
**Problem**: HV export showed 3,742 "No URL" rows despite the dashboard showing all URLs were validated. Export only highlighted 17 of 106 broken links.
**Root Cause**: openpyxl has TWO different hyperlink access methods: (1) `ws.hyperlinks` (sheet-level collection used by extraction/validation) and (2) `cell.hyperlink` (per-cell property used by export highlighting). These are NOT equivalent — `ws.hyperlinks` has entries that `cell.hyperlink` misses, and vice versa. The extraction code in `excel_extractor.py` reads from `ws.hyperlinks` which returns the full list, but the export code in `export.py` iterated cells and checked `cell.hyperlink` which returned `None` for many cells.
**Fix**: 3-strategy URL matching in export: (1) Row-level map from `(sheet_name, row_num)` → ValidationResult using source location metadata added to the result objects (sheet_name, cell_address fields). (2) Sheet-level hyperlink map built from `ws.hyperlinks` (same source as extraction). (3) Original cell text + `cell.hyperlink` fallback. Strategy 1 handles 90%+ of cases because the frontend now sends source location data with each result.
**Lesson**: When one part of the system reads URLs via `ws.hyperlinks` (sheet-level) and another reads via `cell.hyperlink` (cell-level), they WILL disagree. Always use the same access method, or better yet, carry the source location metadata through the entire pipeline so matching doesn't depend on re-extracting URLs from cells.

### 112. Multi-Term Comparison Awareness — Same Company, Different Periods (v5.9.43)
**Problem**: When the same company submits 3-year and 5-year proposals, items unique to the 5-year option were flagged as "missing" from the 3-year proposal (critical/warning severity). This created false red flags.
**Root Cause**: The missing items detection in `analyzer.py` compared each vendor's line items against ALL other vendors. It didn't understand that two proposals from the same company represent different contract configurations, not competing bids with missing items.
**Fix**: Added multi-term detection: (1) Identify same-company proposals by comparing `company_name` case-insensitively. (2) When same-company proposals exist, count how many "missing" items are only priced by other proposals from the same company (term-specific items). (3) Subtract term-specific count from missing count. (4) Add info-level "Term-Specific Items" flag instead of false critical/warning. (5) Falls through to original logic for genuinely different vendors.
**Lesson**: Financial comparison tools must understand that proposals from the same company with different terms are NOT competing bids — they're options. "Missing" items between same-company variants are expected (term-specific) and should be info-level, not critical. Always check `company_name` equality (case-insensitive) before flagging missing items.

### 113. ProposalData Reconstruction Must Include ALL Fields (v5.9.43)
**Problem**: Contract term was filled in by the user during review, but after comparison the results showed no contract term distinction. Vendor IDs fell back to numeric suffixes instead of "(3 Year)" / "(5 Year)".
**Root Cause**: `routes.py` line 296 reconstructs `ProposalData` from the JSON payload, but the reconstruction didn't include `contract_term` or `extraction_text`. These fields were silently dropped, so the analyzer never saw the user's edits.
**Fix**: Added `contract_term=rp.get('contract_term', '')` and `extraction_text=rp.get('extraction_text', '')` to the ProposalData reconstruction.
**Lesson**: When a dataclass is reconstructed from dict/JSON in a route handler, EVERY field must be explicitly mapped. Use `ProposalData(**{k: rp.get(k, default) for k in ProposalData.__dataclass_fields__})` pattern or at minimum manually verify all fields are present when adding new ones.

### 114. Vendor Count Deduplication Pattern (v5.9.43)
**Pattern**: Unique vendor count is computed by deduplicating company names case-insensitively:
```javascript
var uniqueVendors = {};
proposals.forEach(function(p) {
    var base = (p.company_name || p.filename || '').trim().toLowerCase();
    if (base) uniqueVendors[base] = true;
});
var vendorCount = Object.keys(uniqueVendors).length;
```
Display "Unique Vendors" when vendorCount < proposals.length, with a separate "Proposals" card showing total count. In HTML export, show "X proposals total" as subtitle under unique vendor count.
**Lesson**: Never use `proposals.length` as vendor count. Same company can submit multiple proposals (different terms, options, scenarios). Always deduplicate by company name.

### 115. HV Headless Browser Rewrite — Resource Blocking + Parallel Validation (v5.9.44)
**Problem**: Headless browser validation was slow (1 URL at a time) and downloaded full page resources (images, CSS, fonts), wasting bandwidth and time. Government sites and corporate intranets needed Windows SSO passthrough.
**Fix**: Complete rewrite of `headless_validator.py`:
1. **Resource blocking**: Intercept requests via `page.route()`, block images/CSS/fonts/media. Only allow HTML/document/XHR/fetch. Saves 60-80% bandwidth.
2. **Parallel validation**: Process 5 URLs concurrently via `asyncio.gather()` with semaphore control. 5× throughput improvement.
3. **Windows SSO passthrough**: Chromium launch args `--auth-server-allowlist=*.myngc.com,*.northgrum.com` + `--auth-negotiate-delegate-allowlist` pass NTLM/Negotiate auth through to headless browser.
4. **Login page detection**: After navigation, check final URL for ADFS/Azure AD/SAML patterns (e.g., `/adfs/ls/`, `login.microsoftonline.com`, `/saml2/`). Mark as AUTH_REQUIRED not WORKING.
5. **Soft 404 detection**: Check page title/body for "not found", "404", "page doesn't exist" patterns when server returns 200.
**Lesson**: Headless browser validation should ALWAYS block non-essential resources and run in parallel. The biggest performance win comes from resource blocking (fewer network requests), not from parallelism alone. For corporate environments, SSO passthrough via Chromium's `--auth-server-allowlist` flag is essential — without it, headless visits the same login redirect that Python requests sees.

### 116. Per-Domain Rate Limiting with Thread-Safe Semaphores (v5.9.44)
**Problem**: Large batch validation (6000+ URLs) triggered HTTP 429 (Too Many Requests) and IP blocks from aggressive servers. All requests to the same domain were fired simultaneously across ThreadPoolExecutor workers.
**Fix**: Added `_DomainRateLimiter` class in `validator.py`:
- `defaultdict(lambda: threading.Semaphore(3))` — max 3 concurrent requests per domain
- `defaultdict(float)` — tracks last request time per domain
- `acquire(domain)` method: acquires semaphore, then sleeps if < 0.2s since last request to that domain
- `release(domain)` method: releases semaphore
- Used as context manager around every HTTP request in the validation loop
**Lesson**: For batch URL validation, per-domain rate limiting is essential. A global rate limit (e.g., 10 req/s total) is too conservative for 500+ unique domains but too aggressive for a single domain with 100 URLs. The per-domain semaphore + minimum delay pattern gives optimal throughput: fast for diverse URL sets, polite for single-domain concentrations. Always make it thread-safe (`threading.Semaphore`, not a plain counter).

### 117. Content-Type Mismatch Detection for Silent Login Redirects (v5.9.44)
**Problem**: Corporate URLs to `.pdf` and `.docx` files returned HTTP 200 with `Content-Type: text/html` — the server silently redirected to a login page instead of returning the document. These were marked as WORKING because the status code was 200.
**Fix**: Added content-type mismatch check after successful HEAD/GET responses:
1. Build expected content-type from URL extension (`.pdf` → `application/pdf`, `.docx` → `application/vnd.openxmlformats`, etc.)
2. Compare actual `Content-Type` header against expected
3. If URL has document extension but response is `text/html`, mark as `AUTH_REQUIRED` with message "Document URL returned HTML (likely login redirect)"
4. Also check for login-related URL patterns in the final URL after redirects
**Lesson**: HTTP 200 does NOT mean the link works correctly. When validating document links, always check that the Content-Type matches what the URL extension implies. A `.pdf` URL returning `text/html` is almost always a silent SSO redirect to a login page. This is a common pattern on SharePoint, ADFS-protected file servers, and corporate intranets.

### 118. OS Truststore Integration for Corporate SSL (v5.9.44)
**Problem**: Python's `requests` library uses `certifi` (Mozilla CA bundle) which doesn't trust corporate internal CA certificates. Hundreds of internal links flagged as SSLERROR.
**Fix**: Added `truststore` module integration:
```python
try:
    import truststore
    truststore.inject_into_ssl()  # Monkey-patches ssl to use OS cert store
    _using_truststore = True
except ImportError:
    _using_truststore = False
```
When `truststore` is available, Python's `ssl` module uses the OS certificate store (same as Chrome), eliminating most corporate SSL errors. Falls back to existing `verify=False` cascade when `truststore` is not installed.
**Lesson**: The `truststore` module (pip install truststore) is the cleanest solution for corporate SSL issues. It monkey-patches Python's `ssl` module to use the OS certificate store instead of certifi. No code changes needed — all `requests` calls automatically trust the same CAs as Chrome. Always try `truststore.inject_into_ssl()` at module load with ImportError fallback. Include `truststore>=0.9.0` in requirements.txt.

### 119. Python 3.14 SSL Certificate Issue — Use curl for GitHub API (v5.9.44)
**Problem**: GitHub REST API push script using `urllib.request` failed with `ssl.SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate` on Python 3.14.
**Root Cause**: Python 3.14 on macOS doesn't automatically trust the system certificate store. The `Install Certificates.command` script needs to be run after Python installation to install certifi certs, but this wasn't done for the 3.14 installation.
**Fix**: Replaced `urllib.request` with `subprocess.run(["curl", ...])` for all GitHub API calls. curl uses the macOS system certificate store and handles SSL correctly. For POST requests with large payloads, write JSON to a temp file and use `curl -d @tempfile` to avoid shell argument length limits.
**Lesson**: When Python's urllib/requests has SSL issues on macOS, use `subprocess.run(["curl", ...])` as a reliable fallback. curl always uses the OS certificate store. For large payloads (base64-encoded files), always write to a temp file and use `@filename` syntax — don't pass base64 data as shell arguments. Clean up temp files after each call.

### 120. GitHub REST API Batch Push Pattern — 25 Files Per Commit (v5.9.44)
**Problem**: Pushing 90+ source files + 500+ audio files (626 total) to GitHub via REST API in a single commit would create a massive tree operation that could timeout.
**Fix**: Batch files in groups of 25 per commit. Each batch:
1. Create blobs (base64 encode each file → POST /git/blobs)
2. Create tree (POST /git/trees with `base_tree` from previous commit)
3. Create commit (POST /git/commits with parent = previous commit SHA)
4. Update ref (PATCH /git/refs/heads/main)
5. Sleep 1s between batches to avoid rate limiting
Chain batches sequentially: each batch's commit becomes the next batch's parent, each batch's tree becomes the next batch's base_tree.
**Lesson**: For large pushes via GitHub REST API (>30 files), batch into groups of 25 with sequential commit chaining. The `base_tree` parameter is critical — it tells GitHub to keep all existing files and only add/modify the ones in the current tree. Without `base_tree`, the tree would only contain the files in the current batch (deleting everything else). Add 0.05s sleep between blob creations and 1-2s between batches to avoid GitHub's secondary rate limits.

### 121. Demo Audio Manifest System (v5.9.44)
**Feature**: Pre-generated MP3 audio clips for all demo narration scenes, stored in `static/audio/demo/` with `manifest.json` tracking metadata.
**Architecture**: `demo_audio_generator.py` extracts narration text from `guide-system.js` section registry, generates MP3s via edge-tts (neural voice, requires internet) or pyttsx3 (system voices, offline fallback).
**Manifest format**:
```json
{
  "version": "1.0",
  "voice": "en-US-JennyNeural",
  "provider": "edge-tts",
  "sections": {
    "section_id": {
      "steps": [
        { "file": "section_id__step0.mp3", "text": "...", "hash": "c3c1ae4d", "size": 85536 }
      ]
    }
  }
}
```
**Lookup in guide-system.js**: `_getPregenAudioFile(sectionId, stepIndex, subDemoId)` checks `_audioManifest` for matching section/step, returns `{url, text}` or null (falls back to Web Speech API).
**Cache invalidation**: Each step has a text hash. If narration text changes in guide-system.js, the hash won't match, and `demo_audio_generator.py` regenerates only changed clips.
**Lesson**: For TTS-narrated demos, pre-generate audio clips and serve as static MP3s — this gives the best voice quality (neural TTS) and eliminates browser TTS inconsistencies. Use a manifest with text hashes for efficient cache invalidation. The three-tier provider chain (MP3 → Web Speech → silent timer) ensures demos always work even without audio files.

### 122. Interactive HTML Export — Self-Contained Report Pattern (v5.9.42)
**Pattern**: `proposal_compare_export.py` generates a standalone HTML file with ALL content inline — no external dependencies, no CDN links, no internet required.
**Architecture**:
- SVG charts generated server-side as inline `<svg>` elements (tornado chart, stacked bars, horizontal bars, radar chart) — no Chart.js or D3.js dependency
- CSS embedded in `<style>` tags with dark/light mode toggle via `data-theme` attribute
- JavaScript embedded for interactivity: tab switching, column sorting, category filtering, animated count-up stats, theme toggle with localStorage persistence
- Print-optimized `@media print` rules hide navigation and show all sections linearly
- AEGIS gold (#D6A84A) and dark navy (#1B2838) branding throughout
- File size typically 150-400 KB depending on line item count — small enough to email
**Key design decisions**: (1) SVG over Canvas for charts — SVG scales to any resolution and prints cleanly. (2) No framework — vanilla JS keeps the file self-contained. (3) Dark mode default with light toggle — matches AEGIS desktop theme. (4) Sortable tables via vanilla JS `Array.sort()` + DOM reflow — no library needed.
**Lesson**: For exportable HTML reports, generate ALL content server-side as inline SVG/CSS/JS. Never reference external CDNs — the file must work offline and behind corporate firewalls. SVG charts are preferred over Canvas because they scale, print cleanly, and can be styled with CSS. Keep total file size under 500KB for email-friendly distribution.

### 123. PDF Viewer HiDPI Rendering + Zoom + Magnifier (v5.9.42)
**Feature**: Enhanced PDF.js viewer in Proposal Compare's review phase with zoom controls and magnifier loupe.
**Architecture** (in `pdf-viewer.js` and `proposal-compare.js`):
- Canvas rendering at `window.devicePixelRatio` × scale (e.g., 2× on Retina) for crisp text
- Zoom controls: +/− buttons (25% increments, range 50%–300%), fit-width button
- Magnifier loupe: 150px circle following cursor at 3× zoom, rendered by redrawing a zoomed region of the PDF page onto a small canvas overlay
- Canvas CSS sizing: `canvas.width = viewport.width * dpr`, `canvas.style.width = viewport.width + 'px'` — physical pixels vs CSS pixels
**Lesson**: For HiDPI PDF rendering, always multiply canvas dimensions by `devicePixelRatio` and set CSS dimensions to the logical size. Without this, text appears blurry on Retina/4K displays. The magnifier loupe pattern uses a second canvas positioned at cursor coordinates, drawing a zoomed region from the main canvas via `drawImage(mainCanvas, sx, sy, sw, sh, 0, 0, dw, dh)`.

### 124. Multi-Term Comparison — Frontend Orchestration Pattern (v5.9.46)
**Feature**: When proposals have different `contract_term` values (e.g., "3 Year", "5 Year"), AEGIS automatically groups them by term and runs separate comparisons for each group.
**Architecture**: Frontend orchestration with multiple backend calls. `_groupByContractTerm(proposals)` detects distinct terms, `_startMultiTermComparison()` loops through groups sending POST `/api/proposal-compare/compare` for each. Results stored in `State.multiTermResults[]` array. `renderMultiTermResults()` renders a term selector bar above the existing 8-tab UI — clicking a term pill switches which `ComparisonResult` is displayed. "All Terms Summary" pill shows cross-term vendor comparison table.
**Key design decisions**:
- Zero changes to `analyzer.py` — each term group uses the exact same `compare_proposals()` engine
- Each term comparison saves independently to history with `notes = "Term: X"` using existing `notes` field (no schema changes)
- Single-term/no-term workflows are completely unaffected — `_groupByContractTerm()` returns `{isMultiTerm: false}` and existing code path runs
- Term groups with only 1 vendor are excluded (need 2+ to compare) with visible notice
- State fields: `multiTermMode`, `multiTermResults[]`, `multiTermActiveIdx`, `multiTermExcluded[]`
**Files**: `proposal-compare.js` (grouping, orchestration, rendering), `proposal-compare.css` (term selector, badges, summary), `routes.py` (accepts `term_label` in compare payload)
**Lesson**: When adding multi-dimensional comparison features, keep the comparison engine unchanged and orchestrate from the frontend. This avoids breaking existing single-dimension workflows and makes each dimension's results independently accessible (history, export, etc.). The frontend-orchestration pattern works well when the backend API already handles a subset of items — just call it multiple times with different subsets.

### 125. Proposal Structure Analyzer — Privacy-Safe Parser Diagnostics (v5.9.47)
**Feature**: `proposal_compare/structure_analyzer.py` — runs the existing parser on a proposal, then produces a REDACTED structural report that reveals table shapes, column patterns, category distribution, and extraction diagnostics WITHOUT exposing dollar amounts, company names, or proprietary descriptions.
**Redaction strategy**: Dollar amounts → bucket labels ($1K-$9.9K, $100K-$999K, etc.). Company names → stripped (only "detected: yes/no"). Descriptions → pattern analysis (length, word count, structural type). File paths → removed from error messages. Headers → classified into safe roles or redacted to "custom_header (N words, N chars)".
**Key functions**: `analyze_proposal_structure(filepath)` → dict, `_bucket_amount(amount)` → bucket label, `_classify_header(header)` → safe role name, `_analyze_cell_patterns(rows)` → per-column type/fill stats, `_compute_completeness_score(proposal)` → extraction quality metrics, `_generate_suggestions(proposal, analysis)` → parser improvement recommendations.
**API**: `POST /api/proposal-compare/analyze-structure` accepts single file as `file` field in multipart form. Returns JSON with `?download=1` returning downloadable file. Temp file cleaned up immediately after analysis.
**Frontend**: "Analyze Structure" button in upload phase (enabled when 1+ files selected), sends first file to API with `?download=1`, creates blob URL + `<a>` click for download.
**Files**: `proposal_compare/structure_analyzer.py` (NEW), `proposal_compare/routes.py` (new endpoint), `proposal-compare.js` (button + handler), `help-docs.js` (pc-structure section)
**Lesson**: When users need to share parser diagnostic data without revealing proprietary content, bucket financial values into ranges, replace text with structural metrics (length, word count, pattern type), and classify headers into standard financial roles. The structure report tells you EVERYTHING about how the parser interpreted the document without revealing ANYTHING about what the document contains.

### 126. Local Pattern Learning System — Learn from User Corrections (v5.9.49)
**Feature**: `proposal_compare/pattern_learner.py` — computes diffs between the parser's original extraction and the user's edits, stores learned patterns in `parser_patterns.json`. All data stays on disk, never uploaded.
**Architecture**: Frontend snapshots `_original_extraction` (deep copy of parser output) on upload before user can edit. When Compare is clicked, the snapshot travels with the proposal JSON. Backend `learn_from_corrections()` in routes.py compares original vs edited data, calls `_learn_categories()`, `_learn_company()`, `_learn_table_signatures()`. Patterns stored in `parser_patterns.json` in the `proposal_compare/` directory.
**Pattern types**: (1) `category_overrides` — keyword→category mappings from user category corrections, (2) `company_patterns` — filename_hint→company_name from company name corrections, (3) `financial_table_headers` — header signatures from tables with verified financial data, (4) `column_mappings` — (reserved for future) header signatures linked to known column indices.
**Safety threshold**: Learned patterns only activate after `count >= 2` — prevents learning from one-off mistakes. Uses case-insensitive matching throughout.
**Application points in parser.py**: `classify_line_item()` checks learned category overrides before hardcoded CATEGORY_PATTERNS. `extract_company_from_text()` checks learned company patterns as Strategy 0 (before all other strategies). `is_financial_table()` checks learned header signatures before keyword/cell-ratio checks.
**Atomic writes**: `save_patterns()` writes to `.tmp` file then `os.replace()` for crash safety.
**Cache**: `_learned_patterns` module-level global in parser.py, loaded once on first use. `reload_learned_patterns()` clears cache after new patterns are learned (called from routes.py after `learn_from_corrections()`).
**Files**: `proposal_compare/pattern_learner.py` (NEW), `proposal_compare/parser.py` (5 fixes + learned pattern integration), `proposal_compare/routes.py` (learning trigger), `static/js/features/proposal-compare.js` (_original_extraction snapshot), `static/js/help-docs.js` (learning docs)
**5 immediate parser fixes also in this version**: (1) Expanded CATEGORY_PATTERNS for Software/License with 20+ product keywords, (2) Filename-based contract term detection, (3) Column-focused financial table detection, (4) Dynamic confidence scoring based on columns inferred, (5) Relaxed column inference thresholds for sparse tables.
**Lesson**: For local learning systems: (1) Always snapshot the original output before user edits — you can't compute diffs without a baseline. (2) Use a count threshold (≥2) to prevent learning from mistakes. (3) Check learned patterns BEFORE hardcoded defaults — user corrections should override the code. (4) Atomic file writes prevent corruption if the app crashes mid-save. (5) Module-level cache with explicit reload keeps parser fast while allowing hot-reload after learning.

### 127. Universal Learning System — Per-Module Pattern Files (v5.9.50)
**Feature**: Extended the Proposal Compare pattern learning system (Lesson 126) to ALL AEGIS modules. Each module now has its own learner file and JSON pattern store.
**Architecture**: 5 independent learner modules, each following the same pattern:
| Module | Learner File | Pattern File | Sections |
|--------|-------------|--------------|----------|
| Proposal Compare | `proposal_compare/pattern_learner.py` | `proposal_compare/parser_patterns.json` | category_overrides, company_patterns, column_mappings, financial_table_headers |
| Document Review | `review_learner.py` | `review_patterns.json` | dismissed_categories, fix_patterns, severity_overrides |
| Statement Forge | `statement_forge/statement_learner.py` | `statement_forge/statement_patterns.json` | directive_corrections, role_assignments, deletion_patterns, batch_preferences |
| Roles Adjudication | `roles_learner.py` | `roles_patterns.json` | category_patterns, deliverable_patterns, disposition_patterns, role_type_patterns |
| Hyperlink Validator | `hyperlink_validator/hv_learner.py` | `hyperlink_validator/hv_patterns.json` | status_overrides, trusted_domains, exclusion_domains, headless_required_domains |
**Integration points**: (1) `core.py` — after `_suppress_for_requirements_doc()`, checks learned dismissed categories and severity overrides. (2) `statement_forge/routes.py` — PUT update_statement triggers `learn_from_statement_edits()`. (3) `scan_history.py` — `batch_adjudicate()` triggers `learn_from_adjudication()`. (4) `hyperlink_validator/routes.py` — exclusion and rescan endpoints trigger learning. (5) `routes/review_routes.py` — Fix Assistant corrections trigger `learn_fix_patterns()`.
**Aggregation endpoint**: `GET /api/learning/stats` in `config_routes.py` returns stats from all 5 modules.
**Safety thresholds**: Standard patterns require count >= 2. Destructive patterns (deletion_patterns) require count >= 3. Auto-exclusion suggestions require count >= 3.
**Non-blocking guarantee**: ALL learning triggers are wrapped in `try/except Exception: pass` — a failure in any learner NEVER blocks core functionality.
**Lesson**: When extending a learning system across multiple modules: (1) Each module gets its OWN pattern file — never share a single JSON across modules. (2) Integration points should be at the END of successful operations (after adjudication, after save, after export), not in the middle of workflows. (3) All triggers must be non-blocking (`try/except: pass`) because learning is enhancement, not core. (4) Higher safety thresholds for destructive actions (delete, suppress) than for constructive actions (suggest, override). (5) A central `/api/learning/stats` endpoint lets the UI show learning status across all modules.

### 128. Settings UI for Learning System — Management Dashboard (v5.9.52)
**Feature**: New "Learning" tab in Settings modal providing full user control over the pattern learning system.
**Architecture**: Settings modal gains a 6th tab ("Learning") with brain icon. Tab content is dynamically rendered from `/api/learning/stats` on each open.
**UI Components**:
- **Global toggle**: "Learning Enabled" checkbox — dual-persisted to `localStorage('aegis-learning-enabled')` AND backend `config.json` via `POST /api/config { learningEnabled: bool }`. Each Python learner module reads `config.json` via `_is_learning_enabled()` guard function.
- **Summary bar**: Gold-bordered stats showing total patterns + last updated across all modules.
- **Module cards**: 2-column grid of 5 cards (Document Review, Statement Forge, Roles, HV, Proposal Compare). Each shows icon, description, pattern count, last updated, file size. Color-coded by module (blue/yellow/purple/green/rose).
- **Per-module actions**: View (read-only JSON viewer modal), Export (download JSON), Clear (with confirmation).
- **Global actions**: Export All (combined JSON with `_export_meta`), Clear All (double confirmation).
- **Pattern Viewer modal**: `#modal-learning-viewer` at z-index 10200, monospace `<pre>` with syntax-friendly dark bg.
**Backend endpoints** (7 new in `config_routes.py`):
1. `GET /api/learning/patterns/<module>` — returns full pattern JSON
2. `DELETE /api/learning/patterns/<module>` — clears one module's patterns + reloads cache
3. `DELETE /api/learning/patterns` — clears ALL module patterns
4. `GET /api/learning/export/<module>` — downloads pattern file as JSON attachment
5. `GET /api/learning/export` — downloads combined JSON of all modules
6. Existing `GET /api/learning/stats` — aggregates stats from all 5 modules
7. Existing `POST /api/config` — now handles `learningEnabled` key (camelCase→snake_case)
**Module registry**: `_LEARNER_MODULES` dict in config_routes.py maps module IDs to import paths, labels, and descriptions. `_get_learner_module()` helper uses lazy import with try/except.
**Toggle implementation**: Frontend reads `localStorage` for instant UI state. Backend reads `config.json` for Python-side gating. Toggle change handler writes to both stores. Each learner's `_is_learning_enabled()` checks `config.json` at call time (not cached).
**Files**: `routes/config_routes.py` (endpoints), `templates/index.html` (tab + panel + viewer modal), `static/js/app.js` (Learning tab IIFE ~200 lines), `static/css/features/settings.css` (~170 lines), all 5 learner modules (guard functions).
**Lesson**: For feature toggle systems that span frontend + backend: (1) Dual-persist the toggle (localStorage for instant UI, config.json for Python). (2) Backend modules should read config.json at call time, not cache it — the user may toggle mid-session. (3) The Settings UI should lazy-load stats on tab open (not on Settings modal open) to avoid unnecessary API calls. (4) Per-module actions (view/export/clear) should use a registry pattern (`_LEARNER_MODULES`) rather than hardcoded routes for each module. (5) Clear operations need confirmation dialogs — use double confirmation for "Clear All" (first confirm, then type-to-confirm would be ideal but simple confirm is acceptable for local-only tools).

### 129. Cinematic Technology Showcase — Canvas Animation Engine (v5.9.54)
**Feature**: Full-screen Canvas-animated cinematic video showcasing AEGIS capabilities. Cyberpunk HUD aesthetic (Iron Man's JARVIS meets Tron). Launched from "Behind the Scenes" tile on landing page.
**Architecture**: `window.CinematicVideo` IIFE with Engine object, easing library, particle systems, camera system, scene sequencer, and control bar.
**Story Structure**: 6 acts, 18 scenes, ~6-8 minutes:
- Act 1 (The Problem): doc_chaos, standards_wall, breaking_point
- Act 2 (The Solution): aegis_boot, hud_activates, document_scan
- Act 3 (Deep Dive): review_engine, statement_forge, roles_studio, proposal_compare, hyperlink_validator, learning_system
- Act 4 (The Numbers): stat_cascade, architecture_overview
- Act 5 (Air-Gapped): fortress, classified_ready
- Act 6 (Finale): convergence, logo_reveal
**Canvas techniques**: HiDPI (`dpr` scaling), glow/bloom (`shadowBlur`), scanlines (offscreen `createPattern()`), vignette (`createRadialGradient()`), data rain (gold Matrix-style columns), particle systems (ambient + burst), circuit board patterns (offscreen caching), camera lerp.
**Narration**: 18 pre-generated MP3 clips via edge-tts JennyNeural in `static/audio/cinema/manifest.json`. Provider chain: MP3 → Web Speech API → silent timer.
**Controls**: Glassmorphism bar (opacity 0→1 on hover/pause), play/pause, progress scrub, volume, fullscreen, close. Space/Escape keyboard.
**z-index**: 155000 (overlay), 155002 (subtitle), 155003 (controls).
**Files**: `static/js/features/technology-showcase.js` (IIFE, ~1500 lines), `static/css/features/technology-showcase.css` (~250 lines), `static/audio/cinema/` (18 MP3s + manifest.json), `demo_audio_generator.py` (`generate_cinema_audio()` + `get_cinema_scenes()`)
**Modified**: `templates/index.html` (cinema modal + CSS/script tags), `static/js/features/landing-page.js` (tile + dispatch)
**Public API**: `CinematicVideo.play()`, `.pause()`, `.resume()`, `.stop()`, `.seek(fraction)`
**Lesson**: For cinematic Canvas animations, use offscreen canvas caching for static elements (scanlines, circuit board), a central Engine object with RAF loop, and scene functions with setup/render/teardown lifecycle. Beat arrays sync visual callbacks to narration timestamps. Camera lerp with `targetX/targetY/targetZoom` gives smooth transitions between scenes.

### 130. Re-Analyze from Project Detail — Reusing Multi-Term Pipeline (v6.0.1)
**Problem**: Project detail view had a "Compare All" button that sent proposals to the server for a flat comparison, ignoring contract terms. No way to get togglable term-grouped views from the project dashboard.
**Root Cause**: The multi-term pipeline (`_groupByContractTerm` → `_startMultiTermComparison` → `renderMultiTermResults`) was only triggered from the upload→review→compare flow, never from project detail.
**Fix**: Created `_reanalyzeFromProject(projectId, proposalSummaries)` which: (1) shows loading spinner, (2) fetches full proposal data for all proposals via individual GET requests in parallel, (3) sets `State.proposals` with full data, (4) calls `startComparison()` which auto-routes to multi-term or single comparison via existing pipeline.
**Button wiring**: Both "Compare All" and "Re-Analyze" now call `_reanalyzeFromProject()`. Buttons are wired AFTER proposals are fetched (inside the try block) because the proposal list is needed as a parameter. Buttons are disabled with tooltip if < 2 proposals.
**Backend**: Added `contract_term` to `_row_to_proposal_summary()` by including `proposal_data_json` in the SELECT and extracting from the JSON blob. No schema migration needed.
**CSS**: Company name tiles changed from single-line ellipsis to 2-line `-webkit-line-clamp` with `word-break: break-word`. Title tooltip added for full name on hover. Term badges (`.pc-term-badge`) show contract term on proposal cards.
**Key insight**: `startComparison()` already calls `_captureReviewEdits()` and `_cleanupBlobUrls()` at the top — these are harmless no-ops when coming from project detail (no DOM elements to capture from, no blobs to clean).
**Files**: `proposal-compare.js`, `proposal-compare.css`, `proposal_compare/projects.py`
**Lesson**: When an existing pipeline does exactly what's needed but is only triggered from one flow, create a thin bridge function that prepares the state and calls the pipeline entry point. Zero duplication of comparison logic.

### 131. Fix Assistant Reviewer/Owner Mode Toggle (v6.0.2)
**Feature**: Added a review role toggle to Fix Assistant — users choose between "Doc Owner" and "Reviewer" modes that change how accepted and rejected fixes are applied during DOCX export.
**Owner mode** (default, existing behavior): Accepted fixes → Track Changes text replacements. Rejected fixes → margin comments noting the rejection with reviewer notes.
**Reviewer mode**: Accepted fixes → recommendation comments only (no text changes). Rejected fixes → skipped entirely (no action). This lets reviewers mark suggestions without modifying the document author's text.
**Architecture**: Frontend-controlled routing — the toggle changes what goes into `selected_fixes` (Track Changes) vs `comment_only_issues` (comments) before sending to the backend. Zero backend logic changes needed since `apply_fixes_with_track_changes()` and `add_review_comments()` already handle both modes.
**State persistence**: `reviewRole` stored in `FixAssistantState` IIFE with `localStorage('aegis-fa-review-role')`. Getter/setter exposed in public API.
**UI**: `<select id="fav2-role-mode">` in FA header left section, styled to match existing `.fav2-nav-mode` dropdown. "Role:" prefix label via CSS `::before`. Tooltips on Accept/Reject buttons update contextually.
**Export modal**: "Apply selected fixes" label changes to "Add accepted fixes as recommendation comments" when in Reviewer mode.
**Files**: `index.html`, `fix-assistant-state.js`, `app.js`, `fix-assistant.css`, `review_routes.py` (logging only)
**Lesson**: When the backend already supports both export modes (Track Changes vs comments-only), new workflow modes can be implemented entirely in the frontend by controlling which data goes to which API field. The `selected_fixes` → `comment_only_issues` rerouting pattern avoids backend changes.

### 132. US English Dictionary for Spelling Checker (v6.0.2)
**Feature**: Switched spell checker from accepting both British and American spellings to US-only dictionary.
**Changes**: (1) Removed British `'learnt'` from COMMON_WORDS in `spell_checker.py`. (2) Added 200+ British→American corrections to COMMON_MISSPELLINGS dict: -ise→-ize, -ised→-ized, -ising→-izing, -isation→-ization, -our→-or, -re→-er, -t→-ed past tense, defence→defense, programme→program, grey→gray, etc.
**Pre-existing**: `terminology_checker.py` already has `prefer_american=True` default. `nlp/spelling/enchant.py` already defaults to `language='en_US'`.
**Files**: `spell_checker.py`
**Lesson**: When switching to a US-only dictionary, the COMMON_MISSPELLINGS dict is the right place for British→American corrections — it flags the British spelling as incorrect and suggests the American form. COMMON_WORDS should only contain the American form. Always check all spelling-related modules (spell_checker, terminology_checker, nlp/spelling/*) to ensure consistency.

### 133. Proposal Compare "Add Proposal" Erased Previous Batch (v6.0.2)
**Problem**: User uploaded 6 proposals (3 vendors × 2 terms) but only 2 were compared.
**Root Cause**: `startExtraction()` at line 886 in `proposal-compare.js` did `State.proposals = []` which erased ALL previously loaded proposals when the user uploaded files in multiple batches via the "Add Proposal" flow. The upload phase correctly showed existing proposals as "already loaded" (line 589), but the extraction reset wiped them.
**Fix**: Changed `State.proposals = []` to `State.proposals = State.proposals.slice()` (preserve existing array). New extractions are still pushed via `State.proposals.push(r.data)`, so they append to existing proposals instead of replacing them.
**Also fixed**: `_groupByContractTerm()` now normalizes contract terms before grouping — case-insensitive, strips hyphens/dashes, collapses whitespace. "3 Year", "3-year", "3 year" all group together. Normalized keys map back to display labels (first seen original used as label).
**Diagnostic logging**: Added `console.log` at 3 points: extraction (existing + new counts), term grouping (groups with counts), comparison start (proposals with term values, mode selected).
**Lesson**: Any multi-batch upload flow must preserve state from previous batches. When `startExtraction()` resets `State.proposals`, all prior work is lost. The "Add Proposal" button correctly preserved proposals in the upload phase UI, but the extraction function undid it. Always test the full "upload → add more → extract" flow end to end.

### 134. SharePoint Batch Scan 401 — Thread-Unsafe Shared Session (v6.0.3)
**Problem**: SharePoint batch document scan returned 401 auth errors for every file despite successful connection test.
**Root Cause**: `sharepoint_connector.py` created a single `requests.Session()` at init (line 231) shared across ALL worker threads during batch scans. `_process_sharepoint_scan_async()` in `review_routes.py` passes the single connector to `ThreadPoolExecutor(max_workers=3)`, and each worker calls `connector.download_file()` which used `self._api_get()` on the shared session. NTLM/Negotiate authentication is connection-specific — the multi-step challenge→response handshake requires the same TCP connection throughout. When 3 concurrent threads hit the shared session, their NTLM handshake states corrupt each other → 401 on every download.
**Fix**: (1) Added `_create_download_session()` method that creates a fresh `requests.Session()` with SSO auth for each download — each thread gets its own clean NTLM handshake. (2) Added `_download_with_session()` helper that executes the actual GET + file write. (3) `download_file()` now creates a per-call session, tries download, and on 401/403 retries once with a second fresh session (matching the existing 404 retry pattern and HV's `_retry_with_fresh_auth` pattern from Lesson 75). (4) Session is always closed in a `finally` block.
**Key insight**: The 404 handler (lines 925-959) already had the correct fresh-session retry pattern, but the 401 handler at lines 918-924 returned immediate failure with no retry. The fix extends the same retry pattern to 401/403.
**Files**: `sharepoint_connector.py`
**Lesson**: NTLM/Negotiate auth is inherently connection-specific — NEVER share a `requests.Session()` across threads for NTLM-authenticated endpoints. Create a fresh session per request (per thread). This is the same pattern as the hyperlink validator's `_retry_with_fresh_auth` (Lesson 75). For batch operations with `ThreadPoolExecutor`, the shared connector object is fine for configuration (site_url, ssl_verify, timeout), but the actual HTTP session must be per-call, not per-connector.

### 135. SharePoint Folder Names with Ampersand — ResourcePath API (v6.0.3)
**Problem**: SharePoint batch scan returned 400 "Folder not found" for library path `/sites/AS-ENG/PAL/yyRelease/T&E`. Connection test passed but file discovery failed.
**Root Cause**: The legacy `GetFolderByServerRelativeUrl('...')` API has known issues with special characters (`&`, `#`, `%`) in folder/file names. The `&` character inside the OData function parameter is ambiguous — the HTTP transport layer (requests library, proxies, corporate WAFs) may interpret it as an HTTP query string separator before SharePoint's OData parser processes it. Keeping `&` literal (`safe='/:&'`) was unreliable; encoding as `%26` was also wrong because the legacy API treats `%26` as literal `%26`, not decoded `&`.
**Fix**: Switched from legacy `GetFolderByServerRelativeUrl` / `GetFileByServerRelativeUrl` to Microsoft's recommended **ResourcePath API**:
- `GetFolderByServerRelativePath(decodedUrl='...')` for folder operations
- `GetFileByServerRelativePath(decodedUrl='...')` for file downloads
The `decodedUrl` parameter **auto-decodes** percent-encoded values before using them as paths (`%26`→`&`, `%23`→`#`, `%25`→`%`). This eliminates the ambiguity — `&` is percent-encoded as `%26` for safe HTTP transport, then SharePoint decodes it back to `&` for the actual path lookup.
**Encoding**: `_encode_sp_path()` uses `quote(path, safe='/')` — encode everything except path separators. Additionally, OData single quotes are escaped: `'` → `''`.
**Fallback**: `validate_folder_path()` retains a Strategy 2 fallback using the legacy `GetFolderByServerRelativeUrl` API for older SharePoint versions that don't support the ResourcePath API.
**Reference**: https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/supporting-and-in-file-and-folder-with-the-resourcepath-api
**Files**: `sharepoint_connector.py`
**Lesson**: NEVER use the legacy `GetFolderByServerRelativeUrl` / `GetFileByServerRelativeUrl` APIs for paths that may contain special characters. Always use Microsoft's ResourcePath API (`GetFolderByServerRelativePath(decodedUrl=...)`, `GetFileByServerRelativePath(decodedUrl=...)`). The `decodedUrl` parameter handles all special character decoding. Use `quote(path, safe='/')` for encoding and `'` → `''` for OData single-quote escaping. Common folder names with special chars: T&E, R&D, P&ID, M&A, I&T.

### 136. PDF Viewer Zoom/Pan — CSS Override, Wrong Scroll Target, No Position Preservation (v6.0.4)
**Problem**: PDF zoom only zoomed into one location and there was no way to pan/scroll after zooming. Click-and-drag appeared broken.
**Root Cause**: Three compounding issues: (1) CSS rule `.pc-review-doc-viewer .pdfv-page canvas { width: 100%; height: auto; }` overrode the explicit pixel dimensions set by `_renderPages()` when zooming — the canvas always stretched to 100% of container width regardless of zoom level. (2) `_initPanDrag()` scrolled `wrapper.parentElement` (the container) but `.pdfv-wrapper` itself had `overflow: auto` and was the actual scroll container. (3) `_setZoom()` called `_renderPages()` which re-rendered all canvases from scratch, losing the current scroll position — so zoom always jumped to top-left.
**Fix**: (1) Removed `width: 100%` CSS override from `.pc-review-doc-viewer .pdfv-page canvas` — canvas dimensions are now controlled by pdf-viewer.js based on zoom level. (2) Changed `_initPanDrag()` to scroll `wrapper` directly (not `wrapper.parentElement`). (3) Added viewport center preservation to `_setZoom()` — tracks `centerFractionX/Y` before re-render and restores scroll position after. (4) Added auto-fit-width on initial render — computes fit scale from container width and first page dimensions.
**Files**: `static/js/features/pdf-viewer.js`, `static/css/features/proposal-compare.css`
**Lesson**: When a CSS rule and JavaScript both set element dimensions, CSS `width: 100%` wins over JavaScript `style.width = '500px'` if the CSS is more specific. For zoom to work, the CSS must NOT override JS-set dimensions. Also, when re-rendering content that has scroll position, always capture the viewport center as a fraction of total scroll content, re-render, then restore the scroll position using the same fraction against the new dimensions.

### 137. Proposal Compare Duplicate Detection on Re-Upload (v6.0.4)
**Problem**: Users could upload the same proposal file multiple times to the same project with no warning, creating duplicate entries that skewed comparison results.
**Fix**: Two-stage duplicate detection:
1. **File-level (in `addFiles()`)**: When adding files to the upload queue, check against `State.proposals` (already-extracted proposals) by filename (case-insensitive). Duplicate files trigger a `confirm()` prompt: user can replace existing or keep existing. Replace removes the old proposal from `State.proposals` and adds the new file; keep skips the file.
2. **Post-extraction (in `_checkProjectDuplicates()`)**: After extraction, check new proposals against `State.projectProposals` (proposals already in the selected project) by company_name OR filename (case-insensitive). Duplicate triggers prompt with total amounts for comparison. Replace DELETEs old from DB via API and removes from `projectProposals` array; keep discards the new extraction.
**Key pattern**: Company name matching is case-insensitive and trimmed. Both stages use `confirm()` for simplicity and reliability (no custom modal needed for a rare operation). DELETE is fire-and-forget with `.catch()` logging.
**Files**: `static/js/features/proposal-compare.js`
**Lesson**: Duplicate detection for multi-batch uploads needs to check at two levels: (1) against in-memory state (already loaded/extracted proposals) during file selection, and (2) against database state (project proposals) after extraction when server data is available. Always match by multiple fields (filename AND company_name) with case-insensitive comparison to catch renamed files with the same content.

### 138. Discovery-First Development Process (Mandatory)
**Problem**: Shotgun approach of guessing at fixes without understanding the root cause caused repeated rework and wasted effort. Fixes that seemed logical based on API docs or code patterns turned out to be wrong because the actual runtime behavior differed from assumptions.
**Root Cause**: Jumping to implementation before thoroughly understanding the problem domain, reading relevant logs, testing hypotheses, and researching what others have found with similar configurations.
**Mandatory Process**: Before implementing ANY fix, ALWAYS follow this discovery-first workflow:
1. **Collect evidence**: Read ALL available logs, error messages, and stack traces from the actual failing environment (not assumptions)
2. **Research**: Search for the specific error/behavior others have encountered with the same technology stack (e.g., requests-negotiate-sspi + SharePoint + ThreadPoolExecutor)
3. **Understand the system**: Read the relevant source code, API docs, and configuration to understand what's actually happening at runtime — not what should happen in theory
4. **Form a hypothesis**: Based on evidence and research, propose a specific root cause with a clear explanation of WHY the current code fails
5. **Validate before coding**: If possible, add diagnostic logging or a minimal test to confirm the hypothesis before writing the fix
6. **Implement with confidence**: Only then write the fix, targeting the confirmed root cause
**Anti-patterns to avoid**: (1) Changing API endpoints without evidence that the endpoint is the problem. (2) Adding retry logic without understanding why the initial request fails. (3) Switching library versions without confirming version-specific bugs. (4) Applying fixes from StackOverflow without verifying they match our exact configuration.
**Lesson**: "This shotgun approach of just guessing is not working and is causing more re-work than progress." — Every fix must be preceded by a thorough discovery phase. Research first, implement second. When a fix doesn't work, go back to discovery rather than trying another guess.

### 139. SharePoint Online Legacy Auth Disabled — Preemptive SSPI + MSAL OAuth (v6.0.5)
**Problem**: SharePoint batch scan returned 401 for every API call despite successful Windows SSO on other corporate sites. The 401 response had an **empty WWW-Authenticate header**.
**Root Cause**: `ngc.sharepoint.us` is SharePoint Online GCC High (US Government cloud). Microsoft disabled legacy authentication (NTLM/Negotiate) on SharePoint Online as of February 2026. The server returns `401` with an empty `WWW-Authenticate` header. `requests-negotiate-sspi`'s response hook only triggers when `WWW-Authenticate` contains "Negotiate" or "NTLM" — with an empty header, the auth library never fires, so no credentials are ever sent. Standard NTLM/Negotiate CANNOT work for SharePoint Online — it requires OAuth 2.0 via Azure AD/Entra.
**Fix**: Three-strategy auth cascade in `sharepoint_connector.py`:
1. **Preemptive SSPI Negotiate token**: `_generate_preemptive_negotiate_token()` uses Windows SSPI (`sspi.ClientAuth('Negotiate', targetspn=f'HTTP/{host}')`) to generate a Negotiate token BEFORE the first request. Token is attached as `Authorization: Negotiate <base64>` header, bypassing the need for the server to advertise auth schemes. This may work for on-premises SharePoint that still supports Negotiate but doesn't advertise it.
2. **MSAL OAuth 2.0**: `_acquire_oauth_token()` uses Microsoft Authentication Library (MSAL) for modern auth. Tries client credentials flow first (requires `sharepoint_oauth` config in `config.json` with `client_id`, `tenant_id`, `client_secret`), then falls back to Integrated Windows Auth (IWA). GCC High uses `login.microsoftonline.us` authority. Token attached as `Authorization: Bearer <token>`.
3. **Standard Negotiate (fallback)**: `HttpNegotiateAuth()` for on-premises SharePoint that properly advertises NTLM/Negotiate in WWW-Authenticate.
**Auto-detection**: `self._is_sharepoint_online` flag set when site URL contains `sharepoint.com` or `sharepoint.us`. Controls auth strategy priority and diagnostic messaging.
**On 401 cascade in `_api_get()`**: If initial auth fails with 401, tries preemptive SSPI (if not yet tried), then OAuth (if not yet tried), then returns failure with diagnostics.
**Dependencies**: `msal>=1.20.0` (pure Python), `PyJWT>=2.0.0` (required by MSAL). Both are `py3-none-any` wheels — platform-independent. Pre-existing deps (cffi, cryptography) already in wheels for Windows.
**Files**: `sharepoint_connector.py`, `requirements.txt`
**Lesson**: When a server returns 401 with an empty `WWW-Authenticate` header, `requests-negotiate-sspi` will NEVER attempt authentication — it requires the header to contain "Negotiate" or "NTLM". This is the signature of SharePoint Online's legacy auth deprecation. The fix requires either: (1) preemptive token generation via SSPI (bypasses the response-hook mechanism entirely), or (2) OAuth 2.0 via MSAL (the Microsoft-recommended path for SharePoint Online). Always auto-detect `.sharepoint.com` / `.sharepoint.us` domains and route to modern auth. For GCC High, use `login.microsoftonline.us` authority, NOT `login.microsoftonline.com`.

### 140. Preemptive SSPI Requires pywin32 — Not Installed by Default (v6.0.7)
**Problem**: SharePoint auth still returned 401 after v6.0.5/v6.0.6 fixes. The "MSAL not installed" diagnostic message distracted from the real issue.
**Root Cause**: THREE compounding issues:
1. **pywin32 never explicitly installed**: The preemptive SSPI strategy (Strategy 1) imports `sspi` and `win32security` from pywin32. The wheel existed in `wheels/pywin32-311-cp310-cp310-win_amd64.whl` but was NEVER explicitly installed — it only got installed if the "stragglers loop" happened to pick it up. Without pywin32, `SSPI_PREEMPTIVE_AVAILABLE = False` and the primary auth strategy silently did nothing.
2. **Apply script installed to wrong Python**: `sys.executable` in the apply script pointed to the system Python (whatever `python` resolves to on PATH), but AEGIS runs on the embedded Python in `python/python.exe` (OneClick installer layout). Packages were installed to system Python's site-packages, invisible to AEGIS's embedded Python.
3. **MSAL also not installed (same wrong-Python issue)**: Same root cause — msal was installed to system Python, not embedded Python.
**Result**: All three auth strategies failed: (1) Preemptive SSPI — pywin32 not installed → `SSPI_PREEMPTIVE_AVAILABLE = False`. (2) Standard Negotiate — `requests-negotiate-sspi` IS installed but SharePoint Online returns empty `WWW-Authenticate`, so it never fires. (3) MSAL OAuth — msal not installed (wrong Python) → `MSAL_AVAILABLE = False`.
**Fix**: (1) Apply script now auto-detects embedded Python at `python/python.exe` (searched before falling back to `sys.executable`). (2) Apply script installs `pywin32` explicitly (needed for `sspi` + `win32security`). (3) Runs pywin32 post-install script if present. (4) All installs are offline-only (`--no-index --find-links=wheels/`), no internet fallback. (5) Step 5 shows auth strategy availability summary. (6) Added `pywin32>=300; sys_platform == "win32"` to `requirements.txt`.
**Lesson**: When developing on Mac but deploying to Windows embedded Python: (1) **ALWAYS check which Python pip installs to** — `sys.executable` in an apply script may not be the same Python that runs the app. Look for `python/python.exe` in the install directory. (2) **Every import in the app must have a corresponding explicit install** — don't rely on the stragglers loop or transitive deps. The wheel existing in `wheels/` is NOT enough; it must be explicitly installed. (3) **Auth cascade failures are silent** — each strategy sets a flag (`SSPI_PREEMPTIVE_AVAILABLE`, `MSAL_AVAILABLE`) at import time. If all flags are False, the connector falls through to standard `session.get()` with no auth, which gets 401. Add diagnostic logging that shows which strategies are available at connector init time.

### 140. Zero-Config OAuth for Enterprise Rollout — Auto-Detect Tenant + Well-Known Client ID (v6.0.8)
**Problem**: SharePoint MSAL OAuth required users to edit `config.json` with Azure AD `client_id` and `tenant_id`. User explicitly stated: "nothing in the config file can or needs to be edited by the user — that will be too much for enterprise roll out."
**Root Cause**: `_acquire_oauth_token()` only checked `_get_oauth_config()` which reads `sharepoint_oauth` from `config.json`. If that section was absent, OAuth was marked "not configured" — even though the tenant can be auto-detected from the SharePoint URL and Microsoft has pre-registered well-known client IDs that work in all tenants.
**Fix**: (1) Added `_auto_detect_oauth_config(site_url)` that extracts tenant name from SharePoint URL domain (`ngc.sharepoint.us` → tenant `ngc`), uses Microsoft's well-known Office client ID (`d3590ed6-52b3-4102-aeff-aad2292ab01c`), and determines authority URL from domain pattern (`.us` → `login.microsoftonline.us`, `.com` → `login.microsoftonline.com`). (2) Rewrote `_acquire_oauth_token()` to try explicit config first, then auto-detect, then attempt token acquisition via: client credentials (explicit secret only) → IWA (Integrated Windows Auth for seamless SSO) → device code flow (interactive fallback). (3) Removed all user-facing references to "add sharepoint_oauth to config.json". (4) Fixed `msal_note` diagnostic message to reflect auto-detection.
**Well-known client ID**: `d3590ed6-52b3-4102-aeff-aad2292ab01c` is Microsoft's pre-registered "Microsoft Office" application. It exists in ALL Azure AD/Entra tenants, supports delegated permissions (Files.Read.All, Sites.Read.All), and does NOT require admin app registration. This is the same client ID used by Office desktop apps for SharePoint access.
**IWA (Integrated Windows Auth)**: `msal.PublicClientApplication.acquire_token_by_integrated_windows_auth()` uses the current Windows login session's Kerberos ticket for SSO — no password prompt, no browser popup. Requires the user's UPN (email/domain username), which `_get_windows_upn()` extracts via `os.environ.get('USERNAME')` + `os.environ.get('USERDNSDOMAIN')`.
**Files**: `sharepoint_connector.py`
**Lesson**: For enterprise rollout, ZERO user configuration is mandatory. Auto-detect everything possible: tenant from URL, client ID from Microsoft's well-known registry, authority from domain pattern, UPN from Windows environment. Config.json should be for OPTIONAL overrides only, never a requirement. The well-known Office client ID is the key enabler — it eliminates the need for IT admin to register an Azure AD app.

### 141. UI Freeze After SharePoint Connection Failure — Button Re-Enable Gap (v6.0.8)
**Problem**: After a failed SharePoint Connect & Scan (401 error), the rest of the tool was unresponsive. User reported: "the tool wont respond. It has not frozen but has none of the functionality."
**Root Cause**: The Connect & Scan handler (line 11801) disables ALL 4 SP buttons at start: `[btnSpConnectScan, btnSpTest, btnSpDiscover, btnSpScan].forEach(b => b.disabled = true)`. The `finally` block (line 11909) only re-enables 3 of 4 buttons (`btnSpConnectScan`, `btnSpTest`, `btnSpDiscover`) — `btnSpScan` was left disabled. More critically, the batch upload modal is displayed with `style.display = 'flex'` which creates a full-screen overlay with `.modal-overlay` that blocks ALL clicks to elements behind it. The user couldn't access any other part of the tool without first closing the modal.
**Fix**: (1) Added `btnSpScan` re-enable in the `finally` block: `if (btnSpScan && !btnSpScan.dataset.scanId) btnSpScan.disabled = false` — only leaves it disabled if a scan was actually started. (2) The modal close button (X) already worked, but the user may not have realized they needed to close the modal first.
**Files**: `static/js/app.js`
**Lesson**: When a modal disables buttons during an async operation, the `finally` block MUST re-enable ALL buttons, not just some. Any modal with a `.modal-overlay` creates a full-screen click blocker — if users can't close it, the entire app appears frozen. Always test the "operation failed immediately" path, not just the success path. The gap between "3 of 4 buttons re-enabled" was invisible during development because the 4th button (Scan All) was rarely used directly.

### 142. Apply Script --no-index Silently Fails When Wheels Missing (v6.0.9)
**Problem**: Apply scripts v6.0.7 and v6.0.8 both failed to install msal, PyJWT, and pywin32 on the Windows machine. The terminal showed `[FAIL]` but the user may not have noticed. AEGIS started without MSAL or pywin32, so all SharePoint Online auth strategies except the basic Negotiate (which can't work with empty WWW-Authenticate) were disabled.
**Root Cause**: `pip_install()` in apply scripts used `--no-index --find-links=wheels/` (offline-only). The wheel files (`msal-1.35.0-py3-none-any.whl`, `pywin32-311-cp310-cp310-win_amd64.whl`, etc.) exist on the Mac dev machine but were NEVER included in the GitHub file downloads or the apply script's FILES dict. The `wheels/` directory on the Windows machine doesn't contain these wheels. pip with `--no-index` silently fails when no matching wheel is found — it prints an error but returns non-zero, which the script caught and printed `[FAIL]` but continued. The user had internet access (the machine can reach `ngc.sharepoint.us`), so online pip install would have worked.
**Fix**: New `pip_install()` with two-strategy approach: (1) Try offline first (`--no-index --find-links=wheels/`), (2) If offline fails, try online (`pip install` without `--no-index`). Also: verify imports after install with clear `✓ INSTALLED` / `✗ NOT INSTALLED` summary. Also: check pip availability before attempting installs.
**Key log evidence**: Terminal log showed `"Windows SSO (Negotiate) configured"` (Strategy 3 only) with NO "Preemptive SSPI" or "MSAL available" messages — confirming pywin32 and MSAL were both absent.
**Files**: `apply_v6.0.9.py`
**Lesson**: NEVER assume wheel files exist in the `wheels/` directory on the target machine when using apply scripts that download source files from GitHub. The apply script downloads `.py` and `.js` files — NOT `.whl` files. For packages that need to be installed, always try online pip as fallback after offline. The offline-first strategy is still preferred for air-gapped environments, but the fallback prevents silent failure on internet-connected machines. Additionally, the apply script should print a CLEAR summary of which packages were successfully installed vs failed, not just per-package `[OK]`/`[FAIL]` messages that scroll by.

### 143. MSAL Authority Requires Full Tenant Identifier — Not Bare Subdomain (v6.1.0)
**Problem**: After v6.0.9 successfully installed MSAL and pywin32, SharePoint OAuth still failed: `Unable to get authority configuration for https://login.microsoftonline.us/ngc`. MSAL couldn't discover the Azure AD tenant configuration.
**Root Cause**: `_auto_detect_oauth_config()` extracted the tenant name from the SharePoint URL — `ngc.sharepoint.us` → `ngc` — and used it directly in the MSAL authority URL as `https://login.microsoftonline.us/ngc`. But the bare subdomain `ngc` is NOT a valid Azure AD tenant identifier. MSAL validates the authority by querying `https://login.microsoftonline.us/ngc/.well-known/openid-configuration`, which returns an error because Azure AD doesn't recognize `ngc` alone. Valid tenant identifiers are: (1) the tenant GUID (e.g., `aaaabbbb-0000-cccc-1111-dddd2222eeee`), (2) the full `.onmicrosoft` domain (e.g., `ngc.onmicrosoft.us` for GCC High or `contoso.onmicrosoft.com` for commercial), or (3) a verified custom domain.
**Fix**: Three-part approach: (1) New `_discover_tenant_guid()` function queries Microsoft's public OIDC discovery endpoint at `https://login.microsoftonline.us/{tenant}.onmicrosoft.us/.well-known/openid-configuration` to resolve the actual tenant GUID. This endpoint is unauthenticated and returns the GUID in the `issuer` field. (2) Fallback: if OIDC fails, tries extracting GUID from the SharePoint 401 `WWW-Authenticate: Bearer realm="{guid}"` header. (3) If no GUID discovered, uses `{tenant}.onmicrosoft.us` domain format (valid for MSAL). Also added authority fallback cascade in `_acquire_oauth_token()` — if MSAL app creation fails with one authority, tries domain format, then `organizations` multi-tenant endpoint.
**GCC High vs Commercial**: GCC High uses `login.microsoftonline.us` + `onmicrosoft.us`. Commercial uses `login.microsoftonline.com` + `onmicrosoft.com`. The code auto-detects from the SharePoint URL domain.
**Files**: `sharepoint_connector.py`
**Lesson**: When auto-detecting Azure AD tenant from a SharePoint URL, the subdomain (e.g., `ngc` from `ngc.sharepoint.us`) is the tenant NAME but not a valid tenant IDENTIFIER for MSAL. Always convert to either: (1) `{name}.onmicrosoft.us` (GCC High) / `{name}.onmicrosoft.com` (commercial) for domain-based authority, or (2) the actual tenant GUID discovered via the public OIDC endpoint. The OIDC endpoint `https://login.microsoftonline.{us|com}/{tenant}.onmicrosoft.{us|com}/.well-known/openid-configuration` is publicly accessible, requires no authentication, and is the recommended discovery method per Microsoft documentation.

### 144. MSAL instance_discovery=False + verify=False for GCC High (v6.1.1)
**Problem**: After v6.1.0 fixed the tenant identifier format (ngc → ngc.onmicrosoft.us / GUID), MSAL still failed with the same "Unable to get authority configuration" error. The correct authority URL was being used, but MSAL's constructor still couldn't create the app.
**Root Cause**: THREE compounding issues:
1. **`instance_discovery=False` missing**: MSAL's `PublicClientApplication` constructor by default contacts the COMMERCIAL cloud's instance discovery endpoint (`login.microsoftonline.com/common/discovery/instance`) to validate the authority. For GCC High authorities (`login.microsoftonline.us`), this validation FAILS because the commercial endpoint doesn't know about US Government cloud authorities. The fix is `instance_discovery=False`, which tells MSAL to skip this validation and trust the authority URL directly.
2. **`verify=False` missing in MSAL**: Corporate SSL inspection (proxy/WAF) replaces TLS certificates with internal CA certs that Python's certifi bundle doesn't trust. The SharePoint connector already set `self.ssl_verify = False` for its own `requests.Session`, but MSAL creates its OWN internal `requests.Session` for token acquisition. Without passing `verify=False` to the MSAL constructor, MSAL's internal HTTPS calls to `login.microsoftonline.us` fail with SSL certificate errors.
3. **IWA is dead code**: `acquire_token_by_integrated_windows_auth()` does NOT exist in MSAL Python — it only exists in MSAL.NET. The `hasattr(app, 'acquire_token_by_integrated_windows_auth')` check always returned False, so Strategy 2 (IWA) was completely dead code since v6.0.5.
**Fix**: (1) Added `instance_discovery=False` and `verify=False` to `_try_msal_app_creation()` via kwargs dict. (2) Added TypeError fallback for older MSAL versions that don't support these kwargs. (3) Same params added to `ConfidentialClientApplication` for client credentials flow. (4) OIDC discovery request changed from `verify=True` to `verify=False`. (5) Removed dead IWA code, replaced with informational logging about device code flow availability.
**Confirmed NGC tenant GUID**: `83116fc8-b4d8-4b27-8ddf-e8f32e080b8e` (discovered via OIDC endpoint).
**Files**: `sharepoint_connector.py`
**Lesson**: For GCC High (US Government cloud), MSAL Python REQUIRES `instance_discovery=False` in the constructor. Without it, MSAL contacts the commercial cloud to validate the authority, which fails for all government endpoints. Additionally, on corporate networks with SSL inspection, `verify=False` must be passed to MSAL because it uses its own internal requests session (separate from the caller's session). These are constructor-time parameters — they cannot be set after app creation. Always test MSAL integration on the actual corporate network, not just from a dev machine where SSL inspection isn't present.

### 145. SharePoint URL Misrouted to Local Folder Scan + Device Code Flow Invisible (v6.1.2)
**Problem**: User pasted SharePoint URL (`https://ngc.sharepoint.us/sites/AS-ENG/PAL/yyRelease/Forms/Default.aspx?id=...`) into the tool and got "Folder not found" error. Additionally, when Connect & Scan did work, the device code flow was initiated but the user never saw the code.
**Root Cause**: TWO separate issues:
1. **URL misrouted to wrong endpoint**: The aegis.log showed the error came from `folder_scan_start` (line 891), NOT `sharepoint-connect-and-scan`. The local folder scan handler called `Path(folder_path_str).exists()` on a URL string, which always fails. The UI has two input fields — "Enter folder path" (top) and "Paste SharePoint link" (bottom) — but the error messaging didn't explain the distinction.
2. **Device code flow invisible**: `_acquire_oauth_token()` at line 588 initiates a device code flow and stores the flow info in `_device_code_flows` dict, but `_acquire_oauth_token()` immediately returns `None` after `initiate_device_code_flow()`. The device code message, verification URL, and user code were stored server-side but NEVER communicated to the frontend. The user had no idea they needed to go to `microsoft.com/devicelogin` and enter a code.
**Fix**: (1) Added URL detection guard in `folder_scan_start` — checks for `http://`, `https://`, or `sharepoint` in the folder_path and raises a clear `ValidationError` directing users to the SharePoint Connect & Scan input. (2) Added `get_pending_device_flow()` and `complete_device_flow()` module-level functions in `sharepoint_connector.py`. (3) Modified `sharepoint-connect-and-scan` error response to check for pending device code flows and include `device_code` info (user_code, verification_uri) in the response. (4) Added new `/api/review/sharepoint-device-code-complete` endpoint that blocks up to 120s waiting for user auth. (5) Frontend now shows styled "Authentication Required" panel with the verification URL (clickable), the device code (large/selectable), and "I've Completed Authentication" button.
**Files**: `sharepoint_connector.py`, `routes/review_routes.py`, `static/js/app.js`
**Lesson**: When an OAuth device code flow is the expected auth path (no SSO, no password, just a code), the application MUST surface the code to the user in the UI. Storing it server-side and returning None is invisible to the user. The pattern is: (1) initiate flow → store flow state, (2) return device code info in the API error response, (3) frontend shows the code and a completion button, (4) completion endpoint calls `acquire_token_by_device_flow()` which blocks until the user enters the code. For multi-input forms, always validate that the input matches the expected format — a URL is not a filesystem path, and the error message should guide the user to the correct field.

### 146. Headless Browser SharePoint Connector — Bypassing OAuth Entirely (v6.1.3)
**Problem**: SharePoint Online GCC High (`ngc.sharepoint.us`) blocked ALL first-party OAuth client IDs with error `AADSTS65002`. The well-known Office client ID (`d3590ed6`) and every other first-party app are not pre-authorized in GCC High. Custom Azure AD app registration requires IT approval — a long process at NGC. v6.0.5–v6.1.2 tried every OAuth approach: preemptive SSPI, standard Negotiate, MSAL device code flow — all blocked by the server.
**Root Cause**: Microsoft disabled legacy auth (NTLM/Negotiate) on SharePoint Online. The 401 response has an empty `WWW-Authenticate` header so `requests-negotiate-sspi` never fires. MSAL OAuth works mechanically (device code flow reaches the login page) but token acquisition is rejected with AADSTS65002 because first-party app preauthorization is not configured in GCC High.
**Solution**: `HeadlessSPConnector` class in `sharepoint_connector.py` — uses Playwright headless browser with `--auth-server-allowlist=*.ngc.sharepoint.us` to automatically pass Windows SSO credentials (the same ones Chrome uses). Once the browser is authenticated, `page.evaluate(fetch('/_api/web/...'))` calls the SharePoint REST API from within the browser's authenticated JavaScript context, returning identical JSON responses to the REST-based connector. Zero OAuth, zero config.json editing, zero IT admin involvement.
**Architecture**: Auto-fallback in `sharepoint_connect_and_scan()` — when `SharePointConnector.connect_and_discover()` fails, the route handler tries `HeadlessSPConnector.connect_and_discover()`. If headless succeeds, it replaces the connector object and falls through to the success path. The frontend is completely unchanged — polymorphism handles it.
**Key design decisions**: (1) ONE browser context for entire session (SSO session must persist across API calls). (2) `page.evaluate(fetch())` for API calls (executes in browser's auth context). (3) Three-strategy file download: fetch-as-base64, Playwright download API, response.body(). (4) `max_workers=1` for batch scans (Playwright sync API is single-threaded). (5) `HEADLESS_SP_AVAILABLE` flag wraps import in try/except — fallback silently skipped if Playwright not installed.
**Files**: `sharepoint_connector.py` (HeadlessSPConnector class + HEADLESS_SP_AVAILABLE flag), `routes/review_routes.py` (auto-fallback + max_workers=1).
**Lesson**: When all Python-based auth strategies fail for a corporate SSO-protected service, the headless browser is the ultimate fallback — it uses the OS credential store and TLS stack exactly like Chrome. The `--auth-server-allowlist` flag + `page.evaluate(fetch())` pattern lets you call any REST API through the browser's authenticated session without any auth library. This approach works for ANY corporate service that Chrome can access — SharePoint, JIRA, Confluence, ServiceNow, etc.

### 148. Federated SSO Authentication — Navigate to Homepage, Not API (v6.1.4)
**Problem**: HeadlessSPConnector v6.1.3 FAILED on the Windows machine. Log analysis showed headless fallback was being attempted (response times jumped from ~1.5s to ~5-7s) but authentication always failed. No diagnostic messages in any log file.
**Root Cause**: TWO compounding issues:
1. **Premature login detection**: `_authenticate()` navigated to `/_api/web`, which immediately redirected to `login.microsoftonline.us`. The login URL detection code at line 2132 checked `if any(p in current_url for p in login_patterns)` — it matched `'login.microsoftonline'` in the redirect URL and returned failure BEFORE the federated SSO redirect chain could complete. The SSO flow is: SharePoint → Azure AD (`login.microsoftonline.us`) → Org ADFS → Kerberos/Negotiate via `--auth-server-allowlist` → SAML token → Azure AD → SharePoint cookie. The code was checking the URL MID-CHAIN, not after completion.
2. **Missing identity provider domains in auth allowlist**: `--auth-server-allowlist` only included SharePoint and corporate domains (`*.ngc.sharepoint.us`, `*.myngc.com`, etc.) but NOT the identity provider domains (`*.microsoftonline.us`, `*.windows.net`, `*.adfs.*`) where the actual Kerberos/Negotiate challenge happens. Without these domains in the allowlist, Chromium wouldn't pass Windows SSO credentials to Azure AD or ADFS.
3. **No file-based logging**: `logging.getLogger('aegis.sharepoint')` had no `FileHandler` — all connector diagnostics went to stdout only, invisible in exported log files. The user exported `app.log` which showed request/response codes but zero HeadlessSP messages.
**Fix**: Three-part:
1. **3-phase authentication**: Phase 1: Navigate to site homepage (NOT `/_api/web`). Phase 2: If on login page, wait up to 30s for SSO redirect chain to complete via `page.wait_for_url(f'**{sp_host}**')`. Phase 3: Verify auth by calling `page.evaluate(fetch('/_api/web'))` from within the browser's JavaScript context.
2. **Expanded auth allowlist**: Added `*.microsoftonline.com`, `*.microsoftonline.us`, `*.windows.net`, `*.login.windows.net`, `*.adfs.*` to both HeadlessSPConnector AND HeadlessValidator allowlists.
3. **File-based logging**: Added `RotatingFileHandler` writing to `logs/sharepoint.log` (5MB, 2 backups).
**Key insight from HV comparison**: The HeadlessValidator's `validate_url()` uses `wait_until='domcontentloaded'` and checks the final URL AFTER navigation completes. The SP connector was checking the URL DURING the redirect chain and bailing out early.
**Also applied to HV**: Same expanded auth allowlist domains added to `headless_validator.py`'s `CORP_AUTH_DOMAINS` and `LOGIN_PAGE_INDICATORS['url_patterns']` updated with `login.microsoftonline.us` (GCC High variant).
**Files**: `sharepoint_connector.py` (3 edits), `routes/review_routes.py` (error msg), `hyperlink_validator/headless_validator.py` (auth domains), `version.json`, `static/version.json`, `static/js/help-docs.js`, `apply_v6.1.4.py`
**Lesson**: When implementing headless browser SSO authentication: (1) Navigate to the site HOMEPAGE, not an API endpoint — API endpoints trigger immediate redirects that look like "login pages" mid-chain. (2) The `--auth-server-allowlist` must include ALL domains in the SSO chain: the target site domains AND the identity provider domains (Azure AD, ADFS, etc.). (3) After navigation, WAIT for the SSO chain to complete before checking the URL — use `page.wait_for_url()` to wait for the browser to return to the target domain. (4) Verify auth separately via `page.evaluate(fetch())` — don't trust the URL alone. (5) Always add file-based logging for headless browser operations — stdout is invisible in production log exports.

### 149. Playwright Browser Binary Must Be Installed Separately from Package (v6.1.5)
**Problem**: HeadlessSPConnector failed with `BrowserType.launch: Executable doesn't exist at C:\Users\M26402\AppData\Local\ms-playwright\chromium_headless_shell-1208\chrome-headless-shell-win64\chrome-headless-shell.exe`. Playwright Python package was installed but the actual Chromium browser binary was never downloaded.
**Root Cause**: `pip install playwright` installs the Python API package only. The actual browser binaries (Chromium, Firefox, WebKit) are separate ~100MB downloads that must be installed via `python -m playwright install chromium`. The v6.1.4 apply script had this command in Step 2, but it apparently failed on the Windows machine (possibly due to network issues, permissions, or the command not completing in the timeout window).
**Fix**: Created `apply_v6.1.5.py` that focuses specifically on ensuring the Playwright browser binary is installed:
1. Runs `python -m playwright install chromium` with extended timeout (600s)
2. Verifies the binary exists by checking the expected path via `python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium; print(b.executable_path)"`
3. If automated install fails, provides clear manual instructions with the exact Python path
4. Also fixed duplicate auth-server-allowlist entries (IdP domains appeared twice — once from CORP_AUTH_DOMAINS import, once from extras list)
**Also fixed**: Duplicate auth allowlist entries in `_ensure_browser()`. The v6.1.4 update added identity provider domains to both `CORP_AUTH_DOMAINS` in headless_validator.py and the `_idp_extras` list in sharepoint_connector.py. Since HeadlessSPConnector imports `CORP_AUTH_DOMAINS`, every IdP domain appeared twice in the `--auth-server-allowlist` argument. Added set-based deduplication.
**Lesson**: `pip install playwright` and `playwright install chromium` are TWO SEPARATE steps. The first installs the Python API, the second downloads the ~100MB browser binary. Without the binary, `BrowserType.launch()` fails immediately. Apply scripts must: (1) verify the package is installed, (2) run `playwright install chromium`, (3) VERIFY the binary exists at the expected path, (4) provide clear manual fallback instructions. The browser binary path is platform-specific and version-specific — don't hardcode it; use `browser.executable_path` from the Playwright API to check.

### 150. Headless Browser SSO — Three Compounding Root Causes (v6.1.6)
**Problem**: HeadlessSPConnector v6.1.3-v6.1.5 FAILED on Windows. SSO redirect chain timed out after 30 seconds — browser reached Azure AD login page but Windows credentials were never passed.
**Root Cause**: THREE compounding issues, all must be fixed together:
1. **chrome-headless-shell lacks full SSPI/Negotiate**: The bundled Playwright binary is `chrome-headless-shell`, a "lightweight wrapper around Chromium's //content module" designed for scraping/screenshots. Chromium bug #741872 (Windows Auth in headless) was fixed in the NEW headless mode (full Chrome binary), not in headless-shell. The log showed "Browser started (Chromium fallback)" — confirming `channel='chrome'` failed and fell back to the stripped-down binary.
2. **`new_context()` creates incognito-like profiles where ambient auth is disabled**: Chrome 81+ disabled NTLM/Negotiate ambient authentication in incognito/private profiles (Chromium issue #458369). Playwright's `browser.new_context()` creates ephemeral contexts that behave like incognito — the browser never passes Windows credentials to the server. Confirmed by Playwright issue #1707 where `launchPersistentContext()` fixed SSO.
3. **No explicit ambient auth enablement**: Even with persistent context, the `--enable-features=EnableAmbientAuthenticationInIncognito` Chromium flag provides belt-and-suspenders safety.
**Fix**: Three-part rewrite of `_ensure_browser()`:
1. Use `launchPersistentContext()` with a temp `user_data_dir` instead of `launch()` + `new_context()` — creates a "regular" profile where ambient auth IS enabled.
2. Try `channel='msedge'` first (always on Win10/11), then `chrome`, then bundled — branded browsers use the new headless mode with full SSPI.
3. Add `--enable-features=EnableAmbientAuthenticationInIncognito` to launch args.
4. Update User-Agent to include `Edg/131.0.0.0` for AD FS `WiaSupportedUserAgents` matching.
5. Clean up temp `user_data_dir` in `close()` via `shutil.rmtree()`.
**Research sources**: Playwright issues #1707, #33566, #33850, #32324. Chromium bugs #741872 (issues.chromium.org/40529746), #458369. Chrome headless-shell docs.
**Lesson**: For headless browser Windows SSO authentication, ALL THREE conditions must be met: (1) Use a full browser binary (Edge/Chrome new headless mode), NOT chrome-headless-shell. (2) Use `launchPersistentContext()` with a `user_data_dir`, NOT `launch()` + `new_context()` — the latter creates incognito-like contexts where ambient auth is disabled. (3) Include `--enable-features=EnableAmbientAuthenticationInIncognito` for safety. Also include identity provider domains (`*.microsoftonline.com`, `*.microsoftonline.us`, `*.windows.net`, `*.adfs.*`) in `--auth-server-allowlist` — the Kerberos challenge happens on the IdP, not the target site.

### 151. Version Management Update
- **Current version**: 6.1.11

### 152. Diagnostic-First Approach for Remote Environment Debugging (v6.1.7)
**Problem**: HeadlessSPConnector v6.1.6 authenticated successfully (SSO works) but returned zero documents from the `T&E` library path. Without logs from the Windows machine, the exact failure point was unknown.
**Root Cause**: Unknown — investigation confirmed that URL parsing (`parse_sharepoint_url` correctly extracts `/sites/AS-ENG/PAL/yyRelease/T&E`), path encoding (`_encode_sp_path` correctly produces `T%26E`), and ResourcePath API (`decodedUrl` auto-decodes `%26`→`&`) are all theoretically correct. The failure could be: (1) `validate_folder_path()` fails → truncation finds parent → parent is empty, (2) validation succeeds but `list_files()` returns nothing, (3) an API error in `_api_get()` that's swallowed, or (4) the library_path arriving URL-encoded (`%26` instead of `&`) causing double-encoding.
**Fix**: Added comprehensive diagnostic logging at every step of the discovery chain: `validate_folder_path()` logs input/encoded path and result (Name, ItemCount), `_list_files_recursive()` logs file counts/names/subfolders at each depth, `connect_and_discover()` logs the full validation→truncation→auto-detect chain, `_api_get()` logs the full URL. Added defensive URL-decode check — if `library_path` contains `%`, auto-decode it before use. Added route-level logging of parsed `site_url` and `library_path`.
**Key insight**: Rather than guessing at fixes (anti-pattern from Lesson 138), the diagnostic approach generates definitive evidence on next deployment. The `logs/sharepoint.log` file will show exactly which API call fails and why.
**Lesson**: When debugging issues on a remote machine you can't access directly, add comprehensive logging at every decision point in the chain, deploy the diagnostic build, and have the user share the logs. This is faster than iterating through guesses. Always log: (1) inputs to each function, (2) encoded/transformed values, (3) API responses (success/fail + key fields), (4) which branch of conditional logic was taken.

### 153. SharePoint Subsite (Sub-Web) Detection — API Calls Target Wrong Web (v6.1.9)
**Problem**: HeadlessSP connector authenticated successfully and `validate_folder_path()` confirmed ItemCount=69, but `/Files` returned 0 items and all 3 List Items API fallback strategies (v6.1.8) returned HTTP 500 "Incorrect function (0x80070001)".
**Root Cause**: `PAL` in the path `/sites/AS-ENG/PAL/SITE` is a SharePoint **subsite (sub-web)**, NOT a regular folder. `self.site_url` was set to `https://ngc.sharepoint.us/sites/AS-ENG`, so all API calls went to `/sites/AS-ENG/_api/web/...`. But the document library `SITE` belongs to the subsite at `/sites/AS-ENG/PAL`. SharePoint's `GetFolderByServerRelativePath` resolves folder metadata globally from ANY web context (which is why `validate_folder_path` succeeded), but `/Files`, `/Folders`, and `GetList()` are **web-scoped** — they only return data owned by the current web.
**Fix**: Added `_detect_subweb(library_path)` method to BOTH `HeadlessSPConnector` and `SharePointConnector`. The method probes intermediate path segments between `site_url` and `library_path` by calling `{candidate_path}/_api/web?$select=Title,Url`. HTTP 200 = subsite found. Probes deepest-to-shallowest (finds closest subweb to library). Integrated as "Step 2b" in `connect_and_discover()` between folder validation and file listing. When a subweb is detected, `self.site_url` is re-routed to the subweb URL.
**Example**: site_url=`/sites/AS-ENG`, library=`/sites/AS-ENG/PAL/SITE` → probes `/sites/AS-ENG/PAL/_api/web` → 200 OK (Title="PAL") → re-routes site_url to `/sites/AS-ENG/PAL` → all subsequent API calls target the correct web.
**Lesson**: When SharePoint REST API calls return empty results or 500 errors despite valid folder metadata, check if any intermediate path segment is a subsite. `GetFolderByServerRelativePath` is globally resolvable (misleadingly succeeds), but collection endpoints (`/Files`, `/Folders`, `GetList`) are web-scoped. Always probe intermediate paths with `/_api/web` to detect subsites before making collection queries. This applies to ANY SharePoint deployment with subsites — not just NGC.

### 154. NLTK Data Packages Bundled Offline in nltk_data/ Directory (v6.1.9)
**Problem**: Health check showed `averaged_perceptron_tagger` missing. Previous approach relied on `nltk.download()` at runtime, which fails on air-gapped machines.
**Root Cause**: The NLTK data packages were never bundled with the project. The installer/repair scripts tried to download them at install time via `nltk.download()`, but on air-gapped corporate networks this always fails silently. The `nlp_offline/nltk_data/` directory only had 3 of 8 required packages.
**Fix**: Created `nltk_data/` directory in project root with all 8 required NLTK data packages as ZIP files organized by category (`tokenizers/`, `taggers/`, `corpora/`). Total ~57MB ZIPs. `app.py` already sets `NLTK_DATA` env var to this directory on startup (lines 59-62). Updated 6 files: `apply_v6.1.9.py` (downloads ZIPs from GitHub and extracts), `requirements.txt` (documents offline data approach), `install_nlp.py` (checks bundled dir first), `repair_aegis.py` (extracts bundled ZIPs before downloading), `Install_AEGIS_OneClick.bat` (checks project-root `nltk_data/` before `models/nltk_data`), `packaging/prepare_offline_data.py` (notes bundled data).
**8 packages**: punkt, punkt_tab (tokenizers); averaged_perceptron_tagger, averaged_perceptron_tagger_eng (taggers); stopwords, wordnet, omw-1.4, cmudict (corpora).
**Lesson**: NLTK data packages are NOT Python wheels — they're ZIP files containing language models/corpora. They can't be installed via pip. For air-gap deployments, bundle the ZIPs in the repo and extract on the target machine. The apply script downloads ZIPs from GitHub raw content and extracts to `nltk_data/{category}/{package_name}/`. All 6 NLTK-touching files (app.py, install_nlp.py, repair_aegis.py, OneClick installer, prepare_offline_data.py, apply scripts) must agree on the directory structure: `nltk_data/{category}/{package}/`.

### 155. SharePoint Connect & Scan Progress Indicator (v6.1.10)
**Problem**: SharePoint Connect & Scan button showed static "Connecting..." text with a spinning icon during the 15-45 second SSO authentication and file discovery process. No progress bar, no phase updates, no elapsed time — the tool appeared frozen.
**Root Cause**: The backend `/api/review/sharepoint-connect-and-scan` is a single blocking HTTP request that handles authentication (SSO redirect chain), subweb detection, and file listing all at once. The frontend `fetch()` call blocks until the entire process completes, with no intermediate progress events.
**Fix**: Added time-based phase animation in the frontend that cycles through 7 expected phases during the blocking request: (1) Initializing connection (0s), (2) Authenticating via Windows SSO (3s), (3) SSO redirect chain in progress (8s), (4) Verifying authentication (15s), (5) Detecting library structure (20s), (6) Listing documents (25s), (7) Processing results (35s). Each phase updates: a status label with Lucide icon, a gold progress bar (5% → 90%), the button text with a short label, and a live elapsed time counter. An informational subtitle sets expectations ("15-45 seconds"). All timers are cleaned up in success, error, and finally paths.
**Key pattern**: When a backend request is blocking and can't emit intermediate progress, use client-side time-based phase simulation. The phases should match the known server-side steps with realistic timing. Always include: (1) elapsed time counter (proves the tool isn't frozen), (2) phase description (tells user what's happening), (3) progress bar (visual motion catches the eye), (4) expectation-setting text (prevents premature abandonment).
**Files**: `static/js/app.js` (Connect & Scan button handler)
**Lesson**: Any operation that takes >5 seconds should have visible progress indication. For blocking requests where server-sent events aren't practical, client-side phase animation with realistic timing is effective. The key elements are: elapsed time (proves activity), phase text (explains what's happening), progress bar (visual motion), and expectation text (tells user how long to wait). Always clean up timers in try/catch/finally to prevent memory leaks.

### 156. SharePoint File Selection + SP Link Validation Parity (v6.1.11)
**Feature 1: File Selection After Discovery**: Instead of auto-scanning all discovered SharePoint files, Connect & Scan now uses `discover_only: true` to return the file list without starting a scan. A file picker UI (`#sp-file-selector`) renders with checkboxes, extension filter chips, Select All/Deselect All, and a "Scan Selected (N)" button. Selected files are sent to the new `POST /api/review/sharepoint-scan-selected` endpoint which re-creates the connector and starts an async scan with only those files. The existing progress polling dashboard is reused via `btnSpScan.click()` auto-trigger.
**Feature 2: SP Link Validation Parity**: New `sharepoint_link_validator.py` shared utility provides `validate_sharepoint_url()` and `is_sharepoint_url()` — full auth cascade: HEAD with fresh SSO + SSL bypass → GET fallback → SharePoint REST API probe → Content-Type mismatch detection (document URL returning HTML = login redirect). Thread-safe (fresh session per call). Integrated into: (1) `comprehensive_hyperlink_checker.py` — SP URLs routed through shared validator before generic `request_with_retry()`, with rule IDs HL080/HL081/HL082, (2) `hyperlink_validator/validator.py` — Strategy 3c renamed `sharepoint_full`, uses shared validator first with legacy REST-only fallback.
**Key files**: `sharepoint_link_validator.py` (NEW), `comprehensive_hyperlink_checker.py` (modified), `hyperlink_validator/validator.py` (modified), `routes/review_routes.py` (modified + new endpoint), `static/js/app.js` (file picker helpers + discover_only), `templates/index.html` (`#sp-file-selector`), `static/css/features/batch-progress-dashboard.css` (file selector styles)
**API contracts**: `POST /api/review/sharepoint-connect-and-scan` now accepts `discover_only: true` and returns `{files, site_url, library_path, connector_type}` without starting scan. `POST /api/review/sharepoint-scan-selected` accepts `{site_url, library_path, files, connector_type}` and returns `{scan_id, total_files}`.
**Frontend helpers**: `_renderSpFileSelector(files, discoveryCtx)` builds UI, stores context on `data-discoveryCtx`. `_updateSpSelectionCount()` updates count/button. `_applySpExtensionFilter()` toggles row visibility. `_startSPSelectedScan()` sends selected files to new endpoint.
**Lesson**: When refactoring a one-click auto-scan into a user-selection flow, the key design is: (1) backend returns discovery without starting scan (`discover_only`), (2) frontend renders selection UI with context stored as dataset, (3) new endpoint accepts the selection and starts the scan, (4) existing progress polling is reused by setting `btnSpScan.dataset.scanId` and triggering the existing click handler.

## MANDATORY: Documentation with Every Deliverable
**RULE**: Every code change delivered to the user MUST include:
1. **Changelog update** in `version.json` (and copy to `static/version.json`)
2. **Version bump** if warranted
3. **Help docs update** in `static/js/help-docs.js` if user-facing changes
4. **CLAUDE.md update** if new patterns, lessons, or architecture changes
This is a mandatory step, not optional. The user has explicitly requested this be committed to memory.
