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
- **Guided Tour System**: Interactive help panels and spotlight tours via `guide-system.js`
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
| `download_win_wheels.py` | Downloads Windows x64 wheels on connected machine |
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
- **Current version**: 5.7.0
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

### 25. Guided Tour System Architecture
**Pattern**: The AEGIS Guide system (`guide-system.js` + `guide-system.css`) uses:
- SVG mask for spotlight cutouts (not box-shadow hack)
- `getBoundingClientRect()` + `scrollIntoView()` for element targeting
- Section registry pattern — each section defines: whatIsThis, keyActions, proTips, tourSteps
- Tour steps reference CSS selectors that must exist in index.html
**Files**: `static/js/features/guide-system.js`, `static/css/features/guide-system.css`
**API**: `AEGISGuide.startFullTour()`, `AEGISGuide.openPanel('sectionId')`, `AEGISGuide.addHelpButton(modal, sectionId)`

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

### 35. Animated Demo Player Architecture (v5.6.0)
**Problem**: Users wanted "live video" walkthroughs of every AEGIS feature, but actual screen-recorded video files would be massive and stale after any UI change.
**Solution**: Built an animated demo player system in pure HTML/CSS/JS that runs on the live UI. Each section defines `demoScenes` — arrays of steps with `target` (CSS selector), `narration` (text), and optional `navigate` (function to open the correct modal first).
**Architecture**:
- Demo bar: Fixed-bottom glass-morphism UI with typewriter narration, controls (play/pause/prev/next/stop), speed selector, progress bar
- SVG mask spotlight: Creates SVG with white fill + black cutout rect for target element, applied as CSS mask to semi-transparent overlay
- Section navigation: `_navigateToSection(sectionId)` opens the correct modal/view, waits 600ms for DOM to settle, then spotlights elements within it
- Typewriter effect: Characters typed one at a time at configurable speed (adjusted by playback speed multiplier)
- Auto-advance: Each step displays for `demoStepDuration / speed` milliseconds before advancing
- Full Demo mode: Iterates through all 11 sections sequentially, navigating between modals automatically
**Key files**: `guide-system.js` (logic), `guide-system.css` (styles)
**Z-index hierarchy**: beacon=150000, demoBar=149800, panel=149500, spotlight=149000
**Settings**: localStorage key `aegis-guide-enabled`, toggle in Settings > General, synced via `saveSettings()` in app.js
**Lesson**: For feature walkthrough "videos," an animated demo player on the live UI is better than pre-recorded videos — it stays current with UI changes, requires no video hosting, and can be interactive. The key design pattern is: define scenes declaratively (selector + narration + navigation), then a generic player engine handles spotlight, narration, timing, and controls.

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

## MANDATORY: Documentation with Every Deliverable
**RULE**: Every code change delivered to the user MUST include:
1. **Changelog update** in `version.json` (and copy to `static/version.json`)
2. **Version bump** if warranted
3. **Help docs update** in `static/js/help-docs.js` if user-facing changes
4. **CLAUDE.md update** if new patterns, lessons, or architecture changes
This is a mandatory step, not optional. The user has explicitly requested this be committed to memory.
