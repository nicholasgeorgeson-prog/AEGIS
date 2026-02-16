# AEGIS - Bug & Issue Tracker

**Version:** 4.0.0
**Last Updated:** 2026-02-04
**Status Legend:** 🔴 Critical | 🟡 Medium | 🟢 Low | ⚪ Info | ✅ Fixed

---

## Summary Dashboard

| Priority | Open | Fixed | Total |
|----------|------|-------|-------|
| 🔴 Critical | 0 | 10 | 10 |
| 🟡 Medium | 0 | 36 | 36 |
| 🟢 Low | 1 | 9 | 10 |
| ⚪ Info/Enhancement | 4 | 5 | 9 |

**Overall Status:** Production Ready - v4.0.0 AEGIS Rebrand Release (2026-02-04)

### E2E Test Results (2026-02-04)
```
433+ tests passing (v4.0.0)
84 checkers verified
```
All critical functionality verified:
- ✅ Passive voice checker with 300+ false positives exclusion
- ✅ Role consolidation engine (ENH-001)
- ✅ Graph export module (ENH-003)
- ✅ Role comparison module (ENH-004)
- ✅ Universal Role Source Viewer (ENH-005)
- ✅ Statement Forge Review Mode (ENH-006)
- ✅ NLP integration with spaCy (ENH-008)
- ✅ Comprehensive logging/diagnostics system (ENH-009)
- ✅ Clean upgrade path with backup/restore (ENH-010)
- ✅ Dark mode styling (carousel, heatmap)
- ✅ API endpoints (version, docling, document-compare)
- ✅ Passive event listeners performance fix
- ✅ Poll frequency optimization (500ms → 2000ms)
- ✅ SortableJS local installation
- ✅ AbortController timeout for Docling status

---

## Open Issues

### 🔴 CRITICAL Priority

#### BUG-C01: Excessive false positives - 1400+ errors flagged on 10K word document
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🔴 Critical
**Version:** 3.1.0
**Location:** `grammar_checker.py` - PassiveVoiceChecker
**Fix Applied:** Expanded FALSE_POSITIVES set from ~38 words to 300+ words including technical/systems engineering terms, emotional states, physical states, and irregular past participles. This dramatically reduces false positives from passive voice detection matching adjectives that end in -ed/-en.
**Reported:** February 1, 2026
**Platform:** All

**Symptoms:**
1. Document with ~10,317 words scanned
2. Tool flagged 1,400+ errors
3. This is ~13.5% error rate - WAY too high for a normal document
4. Strongly suggests regex patterns are over-matching

**Expected Behavior:**
- A well-written technical document should have <5% flagged items
- Most flags should be legitimate issues worth reviewing
- False positive rate should be <10%

**Actual Behavior:**
- Massive over-flagging making tool unusable
- Users cannot identify real issues in sea of false positives
- Likely regex patterns matching too broadly

**Probable Root Causes:**

1. **Overly broad regex patterns** - Patterns matching common words/phrases
2. **Missing word boundaries** - `\b` not used, matching partial words
3. **Case sensitivity issues** - Patterns matching where they shouldn't
4. **Overlapping rules** - Same text flagged by multiple checkers
5. **Context-ignorant matching** - Not considering surrounding text

**High-Suspicion Checkers to Audit:**
- Passive voice detector (likely over-matching "is", "are", "was", "were")
- Weak word checker (common words being flagged)
- Acronym checker (flagging normal capitalized words)
- Style checker patterns
- Grammar patterns

**Debug Steps:**
1. Get breakdown of flags BY CATEGORY - which checker is producing most?
2. Export the flagged items to see what's being caught
3. Identify top 10 most frequent flag types
4. Review those specific regex patterns
5. Test patterns against known good/bad text samples

**Fix Approach:**
1. Identify which checker(s) are over-firing
2. Tighten regex patterns with word boundaries
3. Add exclusion lists for common false positives
4. Add context awareness (don't flag in certain contexts)
5. Consider confidence scoring - only show high-confidence flags

**Related:**
- ENH-008 (NLP integration) would help significantly here
- BUG-M11, M12, M13 (role/deliverable/acronym issues)

**Effort:** High (4-8 hours to audit and fix patterns)

---

#### BUG-C02: Diagnostic Export Timeout - 30 second timeout causing 504 error
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🔴 Critical
**Version:** 3.0.114+
**Location:** `diagnostic_export.py`
**Fix Applied:**
1. Increased timeout from 30s to 60s
2. Limited error export to last 500 errors to prevent huge exports
3. Inline export logic to avoid double function call overhead

**Related Issues:**
- BUG-M25 (Export buttons show "Exporting" but nothing happens)
- BUG-M26 (Error count mismatch)

---

### 🟡 MEDIUM Priority

#### BUG-M06: Document scan progress bar not showing
**Status:** ✅ Fixed (v3.1.5 - v3.1.9)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/js/features/cinematic-progress.js`, `static/js/features/molten-progress.js`
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 2, 2026

**Fix Applied:**
1. v3.1.5: Added Circuit board themed batch progress with elapsed time counter
2. v3.1.6: Implemented Cinematic Progress Animation System with 5 themes (Circuit, Cosmic, Matrix, Energy, Fire)
3. v3.1.9: Added Molten Progress Bar system with scalable sizes (4px-28px)
4. Multiple progress bar integrations: batch rows, loading overlay, hyperlink validator, cinematic modal

**Files Added:**
- `static/js/features/cinematic-progress.js` (825 lines)
- `static/js/features/molten-progress.js`
- `static/css/features/cinematic-progress.css` (782 lines)
- `static/css/features/molten-progress.css`

**Effort:** Completed

---

#### BUG-M27: Print Section null reference error - Cannot read 'document' property
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🟡 Medium
**Version:** 3.0.114+
**Location:** `static/js/help-content.js`
**Fix Applied:** Added null check for `printWindow` and `printWindow.document` before accessing. Shows alert if popup is blocked.

**Effort:** Low (15 min)

---

#### BUG-M28: Scan Profiles load failure - querySelector on null element
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🟡 Medium
**Version:** 3.0.114+
**Location:** `static/js/app.js` - `renderProfileList` function
**Fix Applied:** Added null check for container element before calling `querySelector`. Added null check for `emptyMsg` element before accessing style property.

**Effort:** Low (15 min)

---

#### BUG-M29: SortableJS blocked by CSP - drag-drop disabled in Statement Forge
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🟡 Medium
**Version:** 3.0.114+
**Location:** `templates/index.html`, `static/js/vendor/`
**Fix Applied:**
1. Downloaded SortableJS v1.15.0 to `static/js/vendor/Sortable.min.js`
2. Updated `templates/index.html` to load from local path
3. Added CDN fallback in case local file fails

**Effort:** Low (15 min)

---

#### BUG-M30: HelpContent click handler extremely slow - 19+ seconds
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🟡 Medium
**Version:** 3.0.114+
**Location:** `static/js/help-content.js`
**Fix Applied:** Wrapped `lucide.createIcons()` calls in `requestAnimationFrame()` to avoid blocking the main thread. Added error handling for icon initialization.

**Symptoms (before fix):**
1. Click in Help & Documentation section
2. UI freezes/hangs
3. Browser reports violation: click handler took 19873ms (~20 seconds)

**Error from Logs:**
```
help-content.js:231 [Violation] 'click' handler took 19873ms
```

**Root Cause:**
A click handler in help-content.js is performing an extremely expensive operation synchronously, blocking the main thread for ~20 seconds.

**Possible Causes:**
1. Large DOM manipulation without batching
2. Expensive regex operations on large content
3. Synchronous file I/O or network request
4. Infinite/large loop
5. Building search index on every click

**Debug Steps:**
1. Profile the click handler at line 231
2. Identify what operation is taking so long
3. Check if it's related to help content size (59 sections)

**Fix Options:**
1. **Async/defer heavy work** - Move expensive operations to Web Worker or requestIdleCallback
2. **Batch DOM updates** - Use DocumentFragment for multiple insertions
3. **Lazy loading** - Don't process all sections upfront
4. **Memoization** - Cache expensive computation results

**Effort:** Medium (1-2 hours to profile and fix)

---

#### BUG-M07: Hyperlink validator false positives on valid URLs
**Status:** ✅ Fixed (v3.0.122 - v3.0.124)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `hyperlink_validator/validator.py`
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 1-2, 2026

**Fix Applied:**
1. **v3.0.122**: Added persistent link exclusions stored in SQLite database
2. **v3.0.123**: Added CAC/PIV client certificate authentication, custom CA bundle support, proxy server support
3. **v3.0.124**: Added headless browser rescan (Playwright) for bot-protected sites
4. **Soft-404 detection**: Made more specific to avoid false positives (removed generic "error" from title check)
5. **Windows SSO**: Auto-configured via requests-negotiate-sspi or requests-ntlm
6. **Extended timeouts**: Government sites get longer connect/read timeouts
7. **HEAD/GET fallback**: Automatically retries with GET when HEAD returns 404/405/403
8. **Realistic User-Agent**: Browser-like headers to avoid bot blocking

**User Workarounds for Persistent Bot-Blocking Sites:**
- Use "Add Exclusion" feature to mark sites as valid
- Use "Rescan with Browser" button for sites like YouTube, defense.gov

**Effort:** Completed

---

#### BUG-M08: Excel file not loading in hyperlink validator
**Status:** ✅ Fixed (v4.0.0)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `hyperlink_validator/excel_extractor.py`, `requirements.txt`
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 4, 2026

**Fix Applied:**
1. **openpyxl** is in requirements.txt (line 21): `openpyxl>=3.0.0,<4.0.0`
2. Full Excel extraction implemented in `excel_extractor.py`:
   - Cell hyperlinks (explicit hyperlink objects)
   - HYPERLINK() formula-based links
   - Email addresses and URLs in cell values
3. Supports both .xlsx (openpyxl) and .xls (xlrd, optional)

**Verification:**
```bash
python -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
```

**Note:** If "No Windows authentication set" error appears, it's informational - validation still works without Windows SSO for external URLs.

**Debug Steps:**
1. Check if openpyxl is installed: `python -c "import openpyxl; print(openpyxl.__version__)"`
2. Check browser console for JavaScript errors
3. Check Flask logs for Python errors during file upload

**Fix Options:**
1. Add missing packages to offline bundle
2. Add better error messages when extraction fails
3. Show clear UI feedback when file can't be processed

**Effort:** Medium (1-2 hours)

---

#### BUG-M09: Hyperlink validator HTML export shows "undefined" and empty columns
**Status:** ✅ Fixed (v3.4.5)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `hyperlink_validator/export.py`, `static/js/features/hyperlink-validator-state.js`
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 4, 2026

**Symptoms:**
HTML export of hyperlink validation results shows:
- Total links: **undefined**
- Working/Broken/Redirects/Timeouts: **0**
- Code column: **empty**
- Time column: **empty**
- Location column: **empty** (not in current template)

**Root Cause:**
Client-side HTML export template was not using nullish coalescing for summary fields, causing "undefined" to display when summary object was incomplete.

**Fix Applied:**
1. Updated `generateHtmlReport()` in `hyperlink-validator-state.js` to use `??` operator for summary fields
2. Server-side `export.py` already had fallback for missing summary (lines 471-507) - verified correct

**Effort:** Low (15 min)

---

#### BUG-M10: Hyperlink flags in main scan don't show the actual broken URL
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `comprehensive_hyperlink_checker.py`
**Fix Applied:** Updated hyperlink issue messages to include the full URL (truncated to 80 chars if needed) and error details. Now shows: "Broken hyperlink (HTTP 404): https://example.com/page"

**Effort:** Low (15 min)

---

#### BUG-M11: Role identification needs improvement
**Status:** ✅ Fixed (v3.2.4 - v3.3.0)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `role_extractor_v3.py`, `nlp_utils.py`, `nlp_enhanced.py`
**Reported:** February 1, 2026
**Platform:** All
**Fixed:** February 3, 2026

**Fix Applied:**
1. **v3.2.4**: Enhanced spaCy integration with noun chunk analysis, compound noun detection, role-verb associations
2. **v3.2.5**: Phone/numeric filtering, ZIP code filtering, run-together word filtering, 50+ FAA/OSHA roles
3. **v3.3.0**: Maximum Accuracy NLP Enhancement Suite:
   - Transformer NER with EntityRuler (100+ aerospace/defense patterns)
   - PhraseMatcher for fast gazetteer lookups (150+ role phrases)
   - Adaptive learning from user adjudication decisions
   - Context-aware confidence boosting
   - **Target accuracy: 95%+** (up from 56.7%)

**Files Added:**
- `nlp_enhanced.py` - Enhanced NLP processor
- `adaptive_learner.py` - Learning system with SQLite persistence
- `data/aerospace_patterns.json` - 80+ EntityRuler patterns

**Effort:** Completed (v3.3.0 includes 167 new tests, all passing)

---

#### BUG-M12: Deliverables identification needs improvement
**Status:** ✅ Fixed (v3.1.2 - v3.2.4)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `role_extractor_v3.py`, `nlp_utils.py`
**Reported:** February 1, 2026
**Platform:** All
**Fixed:** February 2, 2026

**Fix Applied:**
1. **role_extractor_v3.py**: Added `extract_deliverables()` method (line 2250+)
   - Pattern-based extraction: "shall deliver/provide/submit [deliverable]"
   - CDRL/DID reference detection
   - Deliverable type classification (document, report, plan, specification, etc.)
2. **nlp_utils.py**: Full NLP-based `NLPProcessor.extract_deliverables()` (line 832+)
   - spaCy noun phrase extraction
   - Delivery verb object detection (deliver, provide, submit, prepare, develop, create, produce, generate)
   - Confidence scoring and deduplication
3. **EntityKind enum**: Added DELIVERABLE type for classification
4. **DELIVERABLE_PATTERNS**: Regex patterns for documents, reports, plans, specifications, manuals, schedules, budgets, contracts, test outputs

**Effort:** Completed

---

#### BUG-M13: Acronym detection needs improvement
**Status:** ✅ Fixed (v4.3.3 - v4.6.0)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `acronym_checker.py`, `acronym_extractor.py`
**Reported:** February 1, 2026
**Platform:** All
**Fixed:** February 3, 2026

**Fix Applied:**
1. **v4.3.3**: ALL CAPS detection improvements, 40%+ false positive reduction
2. **v4.4.4**: External acronym database with 1,767 well-known acronyms (DOD, FDA, IEEE, ISO)
3. **v4.5.1**: Section reference code filtering, 80+ domain-specific skip words
4. **v4.6.0**: Complete rewrite with comprehensive pattern matching
5. **acronym_extractor.py** (v3.2.4): Schwartz-Hearst algorithm for definition extraction
   - Consistency checking across document
   - Undefined acronym detection
   - 100+ standard aerospace/defense acronyms

**Features:**
- External database lookup (aerospace, defense, government)
- Pattern matching for "ACRONYM (definition)" and "(ACRONYM) Definition" formats
- Section reference filtering (prevents false positives on "Section 3.2", "Figure A-1")
- Domain-specific terminology awareness

**Effort:** Completed

---

#### BUG-M14: Document comparison - no documents available in dropdown
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `document_compare/routes.py`
**Fix Applied:** Added helpful message when no documents are available in the comparison dropdown. The route now returns a success response with an empty list and a user-friendly message explaining that documents need to be scanned first before comparison is available.

**Effort:** Low (15 min)

---

#### BUG-M15: Portfolio - documents incorrectly categorized as batch instead of individual
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `portfolio/routes.py`
**Fix Applied:** Reduced batch detection time window from 5 minutes to 30 seconds. The previous logic grouped any documents scanned within 5 minutes as a "batch". With 30 seconds, only true batch uploads (multiple files uploaded simultaneously) will be grouped together. Individual scans done minutes apart will now correctly appear in the Individual section.

**Effort:** Low (15 min)

---

#### BUG-M16: Batch loading fails - "Too many requests" rate limiting
**Status:** ✅ Fixed (v3.1.1)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/js/ui/state.js`
**Fix Applied:** Changed `pollFrequency` from 500ms to 2000ms in `LoadingTracker` to avoid rate limiting.

**Effort:** Low (5 min)

---

#### BUG-M17: Statement Forge logic changed - must match original exactly
**Status:** ✅ Verified (v2.9.3 - v3.1.3)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `statement_forge/extractor.py`
**Reported:** February 1, 2026
**Platform:** All
**Verified:** February 4, 2026

**Verification Result:**
Code audit found NO breaking changes to core Statement Forge logic. All changes are **additive enhancements**:

1. **v2.9.3**: Extended action verb list from 505 to 1,000+ verbs (enhancement only)
2. **v3.1.3**: Added Statement Forge Review Mode (ENH-006) - new feature, does not modify extraction logic
3. Core statement extraction patterns remain unchanged
4. No TODO/FIXME comments indicating deviation from original logic

**Conclusion:** Statement Forge maintains original logic with expanded verb coverage. No fix needed.

**Effort:** Completed (audit only)

---

#### BUG-M18: Left panel/console in Review doesn't collapse fully when minimized
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/css/layout.css`
**Fix Applied:** Reduced sidebar collapsed width from 56px to 44px for tighter collapse. Added new `.fully-collapsed` CSS class that reduces to 24px with only expand button visible. This provides maximum document viewing area when panel is minimized.

**Effort:** Low (15 min)

---

#### BUG-M19: Hyperlink validator history not logging successful runs
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `hyperlink_validator/routes.py`, `hyperlink_validator/storage.py`
**Fix Applied:** Enhanced hyperlink validator history storage to include:
1. Added `excluded` field to track excluded URLs
2. Added `duration_ms` field to record validation duration
3. Updated database schema with new columns
4. Fixed history record creation to include all validation metadata
5. History now properly logs successful runs with complete statistics

**Effort:** Medium (1 hour)

---

#### BUG-M20: Review page carousel missing night/dark mode styling
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/css/dark-mode.css`
**Fix Applied:** Added comprehensive dark mode CSS rules for carousel component including background, text, navigation arrows, and hover states. All carousel elements now properly adapt to dark theme.

**Effort:** Low (20 min)

---

#### BUG-M21: Heatmap colors unreadable in night mode (Help & Documentation cross-reference)
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/css/dark-mode.css`
**Fix Applied:** Added dark mode CSS rules for heatmap swatches with white text, text-shadow for contrast, and borders. Light blue and medium blue color swatches now have proper text contrast in dark mode.

---

#### BUG-M22: Docling status stuck on "Checking Docling status" in Help & Documentation
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/js/help-docs.js`
**Fix Applied:** Added AbortController with 5-second timeout to the fetch request. Now displays helpful timeout message instead of hanging indefinitely. Also improved error handling to show specific messages for different failure modes.

**Effort:** Low (15 min)

---

#### BUG-M23: Version numbers inconsistent across different windows/pages
**Status:** ✅ Fixed (v3.2.3)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `app.js`, `templates/index.html`, `/api/version` endpoint
**Reported:** February 1, 2026
**Platform:** All
**Fixed:** February 2, 2026

**Fix Applied:**
1. All UI components now load version dynamically from `/api/version` endpoint
2. `app.js` `loadVersionLabel()` function (lines 679-690) fetches and updates:
   - `#version-label`
   - `#footer-version`
   - `#help-version`
3. Templates use dynamic loading instead of hardcoded values
4. Single source of truth: `version.json`

**Effort:** Completed

---

#### BUG-M25: Troubleshooting window export buttons (JSON & Text) show "Exporting" but nothing happens
**Status:** ✅ Fixed (v3.2.3)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `diagnostic_export.py`, troubleshooting JS
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 2, 2026

**Fix Applied:**
1. Fixed element selection - buttons now properly find their target elements
2. Increased timeout from 30s to 60s (related to BUG-C02)
3. Limited error export to last 500 errors to prevent huge exports
4. Added proper error handling with user-visible messages

**v3.2.3 Changelog Entry:**
> FIX: BUG-M25 - Troubleshooting export buttons now properly find their elements

**Effort:** Completed

---

#### BUG-M26: Troubleshooting window error count mismatch - UI shows 1 error, console shows 215
**Status:** ✅ Fixed (v3.1.2 - v3.2.3)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `static/js/ui/state.js`, troubleshooting panel
**Reported:** February 1, 2026
**Platform:** Windows 10/11
**Fixed:** February 2, 2026

**Fix Applied:**
1. **Root cause**: Poll frequency at 500ms caused 429 rate limit errors (BUG-M16)
2. **v3.1.1**: Changed `pollFrequency` from 500ms to 2000ms - eliminated rate limiting
3. **v3.1.2**: Limited error export to last 500 errors
4. **v3.2.3**: Renamed duplicate element IDs in troubleshooting panel to prevent counting conflicts

**v3.2.3 Changelog Entry:**
> FIX: BUG-M26 - Duplicate element IDs in troubleshooting panel renamed to prevent conflicts

**Effort:** Completed

---

#### BUG-M24: Changelog not up to date
**Status:** ✅ Fixed (v4.0.0)
**Priority:** 🟡 Medium
**Version:** 3.1.0
**Location:** `CHANGELOG.md`
**Reported:** February 1, 2026
**Platform:** All
**Fixed:** February 4, 2026

**Fix Applied:**
`CHANGELOG.md` is now comprehensive and current through v4.0.0 (2026-02-04), including:
- All versions from v3.0.92 through v4.0.0
- Detailed entries for each release with features, fixes, and test results
- v4.0.0 AEGIS rebrand with 163+ files documented
- All bug fix references (BUG-xxx) included
- All enhancement references (ENH-xxx) included

**Effort:** Completed

---

**Expected Behavior:**
- All heatmap color swatches should have readable text in both light and dark modes
- Text should have sufficient contrast against background colors

**Actual Behavior:**
- Medium and light blue heatmap colors blend into dark mode background
- Text on these swatches lacks contrast and is difficult/impossible to read

**Root Cause:**
Heatmap color swatches likely use fixed colors that work in light mode but don't have dark mode variants or contrast adjustments.

**Fix Options:**
1. Add dark mode CSS to increase text contrast on light-colored swatches (white or very light text)
2. Add borders/outlines to color swatches in dark mode so they stand out
3. Adjust the heatmap colors themselves for dark mode (darker variants)
4. Add text shadow or background to improve readability

**CSS Fix Example:**
```css
.dark-mode .heatmap-swatch.light-blue,
.dark-mode .heatmap-swatch.medium-blue {
    color: #ffffff;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    border: 1px solid rgba(255,255,255,0.3);
}
```

**Files to Check:**
- `static/css/help.css` or similar
- `static/css/dark-mode.css`
- `templates/help.html` or help documentation template

**Effort:** Low (30 min)

---

---

### 🟢 LOW Priority

#### BUG-L09: Missing logo.svg asset - 404 error
**Status:** ✅ Fixed (v4.0.0)
**Priority:** 🟢 Low
**Version:** 3.0.114+
**Location:** `static/images/logo.svg`
**Reported:** February 2, 2026
**Platform:** All
**Fixed:** February 4, 2026

**Fix Applied:**
1. Created AEGIS shield logo at `static/images/logo.svg` (1,728 bytes)
2. Gold/bronze color scheme matching rebrand
3. Fallback div in `templates/index.html` for graceful degradation

**Effort:** Completed

---

#### BUG-L10: Passive event listener violations - 9 scroll-blocking events
**Status:** ✅ Fixed (v3.1.2)
**Priority:** 🟢 Low
**Version:** 3.0.114+
**Location:** Various event handlers
**Fix Applied:** Added `{ passive: true }` to touch and scroll event listeners in:
- `static/js/ui/renderers.js` (carousel touchstart/touchmove)
- `static/js/features/preview-modes.js` (scroll sync handlers)
- `static/js/features/hyperlink-visualizations.js` (carousel touch events)

**Effort:** Low (20 min)

---

#### BUG-L01: Version comments outdated in file headers
**Status:** ✅ Fixed (v3.0.116)
**Location:** Multiple Python files
**Impact:** Confusing for developers
**Fix:** Updated 13 Python files to use "reads from version.json (module vX.X)" format
**Effort:** Low (30 minutes)

#### BUG-L02: Missing type hints in some functions
**Status:** Open  
**Location:** Various Python modules  
**Impact:** IDE support, code documentation  
**Fix:** Add type hints gradually  
**Effort:** Medium (ongoing)

#### BUG-L03: Console log prefixes inconsistent
**Status:** ✅ Fixed (v3.0.116)
**Location:** JavaScript files
**Impact:** Harder to filter logs
**Fix:** Standardized log prefixes to `[TWR Module]` format across 8 feature modules
**Effort:** Low (1 hour)

#### BUG-L04: Magic numbers in statistics calculation
**Status:** ✅ Fixed (v3.0.116)
**Location:** `config_logging.py`
**Impact:** Code clarity
**Fix:** Extracted magic numbers to named constants (DEFAULT_MAX_UPLOAD_MB, MAX_SAFE_UPLOAD_MB, LOG_FILE_MAX_BYTES, etc.)
**Effort:** Low (30 minutes)

#### BUG-L05: Learner export endpoint lacks CSRF
**Status:** ✅ Fixed (v3.0.116)
**Location:** `app.py` learner export
**Impact:** Very low - read-only endpoint
**Fix:** Added `@require_csrf` decorator for consistency
**Effort:** Low (15 minutes)

#### BUG-L06: Minor unused imports
**Status:** ✅ Fixed (v3.0.116)
**Location:** Various Python files
**Impact:** Code cleanliness
**Fix:** Removed unused imports from job_manager.py, diagnostic_export.py, core.py
**Effort:** Low (30 minutes)

#### BUG-L07: Batch limit constants not defined
**Status:** ✅ Fixed (v3.0.116)
**Location:** `app.py`
**Impact:** Test skipped; batch limits not enforced
**Evidence:** Test `test_batch_constants_defined` skipped
**Fix:** Defined `MAX_BATCH_SIZE` (10) and `MAX_BATCH_TOTAL_SIZE` (100MB) constants
**Effort:** Low (30 minutes)

#### BUG-L08: Sound effects not discoverable
**Status:** ✅ Fixed (v3.0.116)
**Location:** `static/js/app.js`
**Impact:** Users don't know sounds exist (disabled by default)
**Fix:** Added `showSoundDiscoveryTip()` - one-time tooltip that appears on first Fix Assistant open
**Effort:** Low (1 hour)

---

### ⚪ INFO / Enhancements (1 open)

#### ENH-001: Role consolidation engine
**Status:** ✅ Implemented (v3.1.2)
**Description:** Merge similar roles (Engineer/Engineers)
**Implementation:** Created `/role_consolidation.py` with:
- Comprehensive built-in rules for 25+ engineering/defense roles
- Fuzzy matching for similar names
- Abbreviation recognition (PM, SE, QA, etc.)
- Confidence-based merge suggestions (0.0-1.0 scoring)
- Custom rule support and export/import

#### ENH-002: Dictionary sharing
**Status:** ✅ Implemented (v3.1.2)
**Description:** Export/import role dictionaries for teams
**Implementation:** Built into role_consolidation.py:
- `export_rules()` - Serialize rules to JSON
- `import_rules()` - Import custom rules from JSON
- Supports both built-in and custom rules

#### ENH-003: Graph export
**Status:** ✅ Implemented (v3.1.2)
**Description:** PNG/SVG download option for role graphs
**Implementation:** Created `/static/js/features/graph-export.js` with:
- Chart.js export to PNG (high-res with scale factor)
- D3.js/SVG export to both SVG and PNG
- Canvas export support
- Automatic style inlining for portable SVGs
- `addExportButton()` helper for easy integration

#### ENH-004: Multi-document comparison
**Status:** ✅ Implemented (v3.1.2)
**Description:** Side-by-side role analysis
**Implementation:** Created `/role_comparison.py` with:
- RoleComparator class for comparing roles across documents
- Common/partial/unique role identification
- Responsibility diff analysis
- Text, Markdown, and HTML report generation
- Consistency scoring

**Effort:** Medium (completed)

#### ENH-008: Integrate NLP models (spaCy, etc.) to improve Review and Role Extraction
**Status:** ✅ Implemented (v3.1.2)
**Priority:** 🔴 CRITICAL Enhancement - PRIMARY FOCUS
**Version:** 3.1.2
**Reported:** February 1, 2026

**Description:**
The NLP dependencies have been installed (spaCy, LanguageTool, SymSpellPy, etc.) but need to be fully integrated to significantly improve:
1. **Role Extraction** accuracy and coverage
2. **Document Review** quality and detection
3. **Deliverables** identification
4. **Acronym** detection

**Current State:**
- NLP packages installed in offline bundle
- spaCy model (`en_core_web_md`) available
- Basic pattern matching currently in use
- Results are inconsistent (see BUG-M11, M12, M13)

**Target State:**
- spaCy NER (Named Entity Recognition) for role detection
- spaCy dependency parsing for context understanding
- LanguageTool for grammar/style checking in Review
- SymSpellPy for improved spelling suggestions
- Better sentence boundary detection
- Improved noun phrase extraction for deliverables

**Integration Points:**

1. **Role Extraction (`role_extractor_v3.py`)**
   - Use spaCy NER to identify PERSON, ORG, TITLE entities
   - Use dependency parsing to find role-action relationships
   - Extract roles from "shall" statements with better accuracy
   - Identify role modifiers (Lead, Senior, Chief, etc.)
   - Context-aware role classification

2. **Deliverables Detection**
   - Use noun phrase extraction (NP chunks)
   - Identify document/artifact references
   - Pattern: "shall deliver/provide/submit [NP]"
   - Detect CDRLs, DIDs, and standard deliverable types

3. **Acronym Checker (`acronym_checker.py`)**
   - Use spaCy tokenization for better boundary detection
   - Improve definition detection with dependency parsing
   - Handle complex acronym patterns (e.g., "C2" for Command and Control)

4. **Review/Grammar Checking**
   - Integrate LanguageTool for 3000+ grammar rules
   - Add style checking (passive voice, wordiness)
   - Improve readability scoring with textstat
   - Better sentence structure analysis

**Technical Implementation:**

```python
# Example: Enhanced role extraction with spaCy
import spacy
nlp = spacy.load("en_core_web_md")

def extract_roles_nlp(text):
    doc = nlp(text)
    roles = []

    # NER-based extraction
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "NORP"]:
            # Check if it's a role vs named person
            if is_role_pattern(ent.text):
                roles.append(ent.text)

    # Dependency-based extraction
    for token in doc:
        if token.dep_ == "nsubj" and token.head.lemma_ == "shall":
            roles.append(get_full_noun_phrase(token))

    return roles
```

**Files to Modify:**
- `role_extractor_v3.py` - Add spaCy NER integration
- `role_integration.py` - Update extraction pipeline
- `acronym_checker.py` - Improve with NLP
- `document_checker.py` - Add LanguageTool integration
- `core.py` - Initialize NLP models efficiently
- `nlp_utils.py` (new) - Shared NLP utilities

**Performance Considerations:**
- Load spaCy model ONCE at startup (not per-document)
- Use `nlp.pipe()` for batch processing
- Disable unused pipeline components for speed
- Consider `en_core_web_sm` for faster processing if accuracy acceptable

**Success Metrics:**
- Role extraction accuracy > 90%
- False positive rate < 10%
- Deliverables detection accuracy > 85%
- Acronym detection accuracy > 95%
- Processing time < 2x current baseline

**Effort:** High (12-20 hours)
- spaCy integration for roles: 4-6 hours
- Deliverables NLP: 3-4 hours
- Acronym improvement: 2-3 hours
- LanguageTool integration: 3-4 hours
- Testing and tuning: 2-3 hours

---

#### ENH-005: Universal Role Source Viewer - accessible from ANY role display location
**Status:** ✅ Implemented (v3.1.3)
**Priority:** ⚪ Enhancement (HIGH priority)
**Version:** 3.1.0
**Reported:** February 1, 2026
**Updated:** February 1, 2026

**Description:**
Add a universal "view in document" feature that is accessible from ANY location in the Roles & Responsibilities Studio where a role is displayed. When a role appears in multiple documents, users must be able to toggle through ALL occurrences across all documents.

**Core Requirements:**

1. **Universal Access** - The review/source viewer must be accessible from:
   - Role list panel
   - Role details view
   - Role-Document matrix
   - Role graph nodes
   - Any other location where a role name appears
   - Essentially: click ANY role → see where it came from

2. **Multi-Document Support** - When a role is found in multiple documents:
   - Show ALL documents where the role appears
   - Toggle/navigate between documents (Previous/Next or dropdown)
   - Show count: "Found in 3 documents (1 of 3)"
   - Each document shows its specific location(s)

3. **Multi-Location Support** - When a role appears multiple times in ONE document:
   - Show ALL occurrences within that document
   - Toggle between occurrences: "Location 2 of 5"
   - Navigate: Previous/Next occurrence buttons

**User Story:**
As a user reviewing roles, I want to:
1. Click on ANY role displayed anywhere in the R&R Studio
2. Instantly see the exact document context where it was found
3. If found in multiple documents, toggle through each document
4. If found multiple times in a document, toggle through each occurrence
5. See the role highlighted in its surrounding paragraph/section

**UI Concept:**
```
┌─────────────────────────────────────────────────────────┐
│  Role: "Systems Engineer"                          [X]  │
├─────────────────────────────────────────────────────────┤
│  Found in: 3 documents                                  │
│  ◀ Previous │ Document 2 of 3 ▼ │ Next ▶              │
│                                                         │
│  📄 Requirements_Spec_v2.docx                          │
│  ─────────────────────────────────────                  │
│  Location: 2 of 4 occurrences    ◀ Prev │ Next ▶      │
│  Section: 3.2.1 - Staffing Requirements                │
│  Page: 12                                               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ...project team shall include a **Systems       │   │
│  │ Engineer** responsible for the integration of   │   │
│  │ all subsystems. The Systems Engineer shall...   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [View Full Document]  [Jump to Next Occurrence]        │
└─────────────────────────────────────────────────────────┘
```

**Technical Requirements:**

1. **Data Storage During Extraction:**
   - Store document ID/name for each role occurrence
   - Store character offset/position in document
   - Store surrounding context (100-200 chars before/after)
   - Store section/heading name if available
   - Store page number if available

2. **Backend API:**
   - `GET /api/roles/{role_name}/occurrences` - Returns all occurrences across all documents
   - Response includes: document list, locations per document, context snippets

3. **Frontend Components:**
   - Role context viewer modal/panel
   - Document selector (dropdown or navigation)
   - Occurrence navigator (prev/next within document)
   - Context display with highlighting
   - Integration points at every role display location

4. **Click Handlers:**
   - Add click handler to all role display elements
   - Consistent behavior regardless of where role is clicked
   - Visual indicator that roles are clickable (cursor, underline, icon)

**Benefits:**
- Complete traceability from role to source
- Verify extraction accuracy across entire corpus
- Understand context differences across documents
- Build user confidence in extraction quality
- Debug false positives/negatives easily

**Effort:** High (8-12 hours)
- Backend: Store occurrence data during extraction (3-4 hrs)
- API: Create occurrence retrieval endpoint (1-2 hrs)
- Frontend: Build viewer component (3-4 hrs)
- Integration: Add click handlers everywhere (2-3 hrs)

#### ENH-006: Statement Forge - Review mode with source context and statement creation
**Status:** ✅ Implemented (v3.1.3)
**Priority:** ⚪ Enhancement
**Version:** 3.1.0
**Reported:** February 1, 2026

**Description:**
Add a review/creation interface to Statement Forge that allows users to:
1. See WHERE each statement was extracted from in the document
2. Highlight text and create new statements manually
3. Full editing capabilities with all Statement Forge features

**User Story:**
As a user working with Statement Forge, I want to:
1. Click on an extracted statement → See the source context in the document
2. Highlight any text in the document → Create a new statement from selection
3. Edit/refine statements with all formatting and metadata options

**Features Needed:**
1. **Source Viewer** - Show document context where statement was found
   - Highlight the matched text
   - Show surrounding paragraphs
   - Display section/page reference

2. **Statement Creator** - Select text and create new statements
   - Highlight text in document preview
   - Click "Create Statement" button
   - Opens statement editor with pre-filled text
   - All Statement Forge bells and whistles available

3. **Review Mode** - Iterate through extracted statements
   - Navigate between statements
   - Approve/reject/edit each one
   - See source context for verification

**UI Concept:**
- Split view: Document on left, Statement editor on right
- Click statement → Scrolls document to source
- Highlight in document → "Create Statement" button appears
- Similar to Fix Assistant but for statement creation

**Benefits:**
- Verify statement extraction accuracy
- Create custom statements from any document text
- Full control over statement content
- Build comprehensive statement library

**Technical Approach:**
1. Store character offsets during extraction
2. Create document preview component with highlighting
3. Add selection handler for manual statement creation
4. Integrate with existing Statement Forge editor

**Effort:** High (6-10 hours)

#### ENH-009: Comprehensive logging for detailed bug reports (without performance degradation)
**Status:** ✅ Implemented (v3.1.3)
**Priority:** ⚪ Enhancement (HIGH priority)
**Version:** 3.1.0 (AEGIS)
**Reported:** February 1, 2026

**Description:**
Implement comprehensive logging throughout the application so that bug reports contain all necessary diagnostic information. Logs must be detailed enough to diagnose issues without requiring reproduction, but must NOT degrade performance.

**Current State:**
- Logging exists but is inconsistent across modules
- Some operations don't log at all
- Error details often missing context
- Hard to diagnose issues without reproduction
- Troubleshooting window shows incomplete data (BUG-M26)

**Target State:**
- Every significant operation is logged
- Errors include full context (inputs, state, stack traces)
- Performance-critical paths use lazy/conditional logging
- Log levels properly configured (DEBUG, INFO, WARNING, ERROR)
- Logs exportable for bug reports

**Logging Requirements:**

1. **Backend (Python/Flask):**
   - Log all API endpoint calls with timing
   - Log document processing stages with progress
   - Log all errors with full tracebacks
   - Log configuration state at startup
   - Log session creation/cleanup
   - Log NLP model loading and usage
   - Log file operations (upload, save, export)

2. **Frontend (JavaScript):**
   - Log all API calls with request/response summary
   - Log user actions (button clicks, navigation)
   - Log state changes in major components
   - Log errors with stack traces
   - Log performance metrics (load times, render times)
   - Capture console errors automatically

3. **Troubleshooting Window Integration:**
   - Show real-time log stream
   - Filter by log level (DEBUG/INFO/WARN/ERROR)
   - Filter by module/component
   - Search logs
   - Export complete logs for bug reports
   - Show accurate error counts (fix BUG-M26)

**Performance Safeguards:**

1. **Lazy Evaluation:**
   ```python
   # Bad - always evaluates expensive_operation()
   logger.debug(f"Result: {expensive_operation()}")

   # Good - only evaluates if DEBUG enabled
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug(f"Result: {expensive_operation()}")
   ```

2. **Async Logging:**
   - Use queue-based logging for high-frequency events
   - Don't block main thread for log writes
   - Batch writes to disk

3. **Log Levels:**
   - DEBUG: Verbose, only in development
   - INFO: Normal operations (default for production)
   - WARNING: Potential issues
   - ERROR: Failures requiring attention

4. **Sampling:**
   - For very high-frequency events, log only every Nth occurrence
   - Include count of skipped events

5. **Circular Buffer:**
   - Keep last N log entries in memory
   - Only write to disk on error or export
   - Prevents disk I/O overhead

**Log Format:**
```
[2026-02-01 14:32:15.123] [INFO] [role_extractor] Processing document: spec.docx (10,317 words)
[2026-02-01 14:32:15.456] [DEBUG] [role_extractor] Found 23 potential roles in 0.33s
[2026-02-01 14:32:15.789] [ERROR] [api] POST /api/scan failed: ValueError - Invalid document format
  Traceback (most recent call last):
    File "app.py", line 234, in scan_document
    ...
  Context: {filename: "test.xyz", size: 1234, user_session: "abc123"}
```

**Files to Modify:**
- `config_logging.py` - Enhance logging configuration
- `app.py` - Add API logging middleware
- `core.py` - Add processing stage logging
- `static/js/` - Add frontend logging utility
- `diagnostic_export.py` - Enhance export with full logs

**Benefits:**
- Diagnose bugs without reproduction
- Faster bug resolution
- Better understanding of user workflows
- Performance monitoring built-in
- Professional-grade observability

**Effort:** Medium-High (6-10 hours)
- Backend logging enhancement: 3-4 hours
- Frontend logging utility: 2-3 hours
- Troubleshooting window integration: 2-3 hours
- Performance testing: 1 hour

---

#### ENH-010: Clean upgrade path - installer should handle updates without full reinstall
**Status:** ✅ Implemented (v3.1.4)
**Priority:** ⚪ Enhancement (HIGH priority)
**Version:** 3.1.0 (AEGIS)
**Reported:** February 1, 2026

**Description:**
Many bug fixes and enhancements require changes to both Python backend and JavaScript frontend. Currently, users need to do a fresh install to get updates. Need a cleaner upgrade mechanism.

**Current State:**
- Updates require fresh install
- User settings/data may be lost during reinstall
- No migration path for configuration
- Offline bundle needs manual rebuilding

**Target State:**
- One-click update mechanism
- Preserves user settings and data
- Handles Python package updates
- Handles JavaScript/static file updates
- Version migration scripts if needed

**Changes Requiring Fresh Install (Current Bugs):**

| Change Type | Examples | Why Fresh Install Needed |
|-------------|----------|--------------------------|
| **Python packages** | openpyxl, requests-negotiate-sspi | Not in current offline bundle |
| **JavaScript changes** | Rate limiting fix (500ms→2000ms) | Browser may cache old JS |
| **NLP models** | spaCy en_core_web_md | ~100MB model not included |
| **New Python modules** | nlp_utils.py | New files needed |
| **Config changes** | Logging configuration | New config structure |

**Upgrade Mechanism Options:**

1. **In-App Updater:**
   - Check for updates on startup
   - Download delta/patch files
   - Apply updates and restart
   - Complexity: High

2. **Versioned Installer with Upgrade Mode:**
   - Installer detects existing installation
   - Offers "Upgrade" vs "Fresh Install"
   - Preserves user data during upgrade
   - Complexity: Medium

3. **Portable Update Package:**
   - Separate "update.zip" with changed files only
   - User extracts over existing installation
   - Include migration script if needed
   - Complexity: Low

4. **Git-Based Updates (for dev users):**
   - `git pull` for code updates
   - `pip install -r requirements.txt` for packages
   - Complexity: Low (but requires git)

**Recommended Approach:**
Start with Option 3 (Portable Update Package) for simplicity:
1. Create `AEGIS_Update_vX.X.X.zip`
2. Include only changed files
3. Include `update.bat` / `update.sh` script
4. Script backs up user data, applies update, restores data
5. Later: Build full in-app updater

**User Data to Preserve:**
- `scan_history.db` - Scan history
- `user_settings.json` - Preferences
- `custom_dictionaries/` - User word lists
- `learner_data/` - ML training data
- Session data (if applicable)

**Effort:** Medium-High (4-8 hours for update package system)
- Update package creation script: 2-3 hours
- Migration/preservation logic: 2-3 hours
- Testing upgrade scenarios: 2 hours

**Note:** For v3.1.0 (AEGIS) release, fresh install will likely be required due to scope of changes. Future minor versions should support upgrade packages.

---

#### ENH-007: Replace ASCII/text diagrams with professional HD graphics
**Status:** Requested
**Priority:** ⚪ Enhancement (HIGH priority)
**Version:** 3.1.0 (AEGIS rebrand)
**Reported:** February 1, 2026

**Description:**
Replace all ASCII/text-style diagrams and visuals with professional, high-definition images or SVG graphics for a more polished, enterprise-ready appearance.

**Current State:**
- Extraction pipeline diagram uses ASCII art / text boxes
- Help documentation uses text-based flow diagrams
- Architecture visuals are low-fidelity

**Target State:**
- Professional HD images (PNG/SVG) for all diagrams
- Consistent visual style matching AEGIS branding
- Clean, modern look appropriate for enterprise/defense customers
- Responsive images that scale well on all screen sizes

**Diagrams to Replace:**

1. **Extraction Pipeline Visual**
   - Current: Text/ASCII flow diagram
   - Replace with: Professional flowchart showing document → extraction → analysis stages
   - Include: Icons for each stage, arrows showing data flow, color coding

2. **Architecture Overview**
   - System components diagram
   - Module interconnections
   - Data flow visualization

3. **Help & Documentation Diagrams**
   - Cross-reference heatmap legend
   - Feature workflow diagrams
   - UI navigation guides

4. **Statement Forge Pipeline**
   - Statement extraction flow
   - Classification stages

5. **Role Extraction Pipeline**
   - NLP processing stages
   - Classification decision tree

**Design Requirements:**
- **Style:** Clean, modern, professional (enterprise-appropriate)
- **Colors:** Match AEGIS branding (navy blue, gold accents)
- **Format:** SVG preferred (scalable), PNG fallback (2x resolution for retina)
- **Accessibility:** Include alt text for all images
- **Dark Mode:** Provide dark mode variants OR use colors that work in both modes

**Technical Approach:**
1. Create designs in Figma, Adobe Illustrator, or similar
2. Export as SVG (primary) and PNG @2x (fallback)
3. Store in `static/images/diagrams/`
4. Update HTML templates to reference new images
5. Add CSS for responsive sizing and dark mode support

**File Locations to Update:**
- `templates/help.html` - Help documentation
- `templates/index.html` - Main dashboard
- `static/css/` - Image styling
- `static/images/` - New image assets

**Benefits:**
- Professional appearance for enterprise customers
- Aligns with AEGIS rebrand
- Better user experience and comprehension
- Consistent visual identity

**Effort:** Medium-High (4-8 hours)
- Design creation: 2-4 hours
- Image export and optimization: 1 hour
- Template updates: 1-2 hours
- Dark mode variants: 1 hour

---

## Competitive Analysis - Missing Features (Researched 2026-02-02)

Based on analysis of competing tools (DOORS, Jama, Polarion, Helix RM, ReqView, Cradle, Modern Requirements, Visure, RequisitePro, Integrity), the following high-impact features would significantly differentiate AEGIS:

### ENH-011: Intelligent Requirements Traceability Engine
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact)
**Competitive Gap:** DOORS, Jama, Polarion all have this

**Description:**
Automatic bi-directional traceability matrix generation with gap analysis.

**Features:**
- Auto-link requirements to design elements, test cases, code
- Visual traceability graphs showing parent-child relationships
- Gap detection: "Requirement X has no linked test case"
- Impact analysis: "If Requirement Y changes, these 5 items affected"
- Configurable link types (satisfies, derives, verifies, etc.)

**Why Important:**
This is the #1 differentiator for enterprise requirements tools. Currently AEGIS has no traceability beyond document-level analysis.

**Effort:** High (20-40 hours)

---

### ENH-012: Enterprise Terminology Management System
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact)
**Competitive Gap:** Helix RM, Visure have glossary management

**Description:**
Project-wide glossary with automatic term consistency checking.

**Features:**
- Create/manage project glossaries with definitions
- Auto-detect undefined terms in documents
- Flag inconsistent term usage (e.g., "UAV" vs "drone" vs "unmanned aircraft")
- Suggest standardized terms during editing
- Import/export glossaries (CSV, XML)
- Term usage reports across document corpus

**Why Important:**
Defense/aerospace contracts require strict terminology consistency. This directly addresses real customer pain.

**Effort:** Medium-High (15-25 hours)

---

### ENH-013: EARS/INCOSE Requirement Quality Analyzer
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact)
**Competitive Gap:** ReqView, Modern Requirements have quality scoring

**Description:**
Analyze requirements against EARS (Easy Approach to Requirements Syntax) templates and INCOSE quality guidelines.

**Features:**
- Classify requirement type (Ubiquitous, Event-Driven, State-Driven, etc.)
- Check against EARS templates with specific feedback
- INCOSE quality attributes scoring:
  - Atomic (single requirement)
  - Complete (no TBDs, TBRs)
  - Consistent (no conflicts)
  - Feasible (achievable)
  - Verifiable (testable)
  - Unambiguous (clear language)
- Quality dashboard with trends over time
- Rewrite suggestions for non-compliant requirements

**Why Important:**
Standards compliance is critical for defense contracts. EARS is becoming industry standard.

**Effort:** High (25-40 hours)

---

### ENH-014: Real-time Quality Score Dashboard
**Status:** Proposed
**Priority:** ⚪ Enhancement (MEDIUM impact)
**Competitive Gap:** All major tools have dashboards

**Description:**
Live metrics dashboard showing document quality over time.

**Features:**
- Overall quality score (0-100) with breakdown
- Trend charts: quality improving/declining
- Category breakdown (grammar, style, requirements, structure)
- Comparison across documents in portfolio
- Export metrics for reporting
- Configurable thresholds and alerts

**Why Important:**
Managers need visibility into document quality across projects. Currently AEGIS only shows point-in-time results.

**Effort:** Medium (12-20 hours)

---

### ENH-015: LLM-Powered Semantic Analysis Module
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact - DIFFERENTIATOR)
**Competitive Gap:** None have this - would be unique to AEGIS

**Description:**
Use large language models for deep semantic understanding beyond regex/NLP.

**Features:**
- Requirement conflict detection using semantic similarity
- Auto-categorization of requirements by type
- Ambiguity detection with rewrite suggestions
- Cross-document semantic search
- "Ask questions about your documents" interface
- Intelligent requirement decomposition suggestions

**Why Important:**
This would be a MAJOR differentiator. No competing tool has LLM integration for semantic analysis.

**Technical Approach:**
- Local LLM (Ollama) for offline/air-gapped environments
- OpenAI/Anthropic API for cloud deployments
- Configurable: users choose local vs cloud

**Effort:** Very High (40-80 hours)

---

### ENH-016: Compliance Artifact Generator
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact)
**Competitive Gap:** Visure, Integrity have compliance reporting

**Description:**
Auto-generate compliance matrices and audit artifacts for standards.

**Features:**
- Templates for common standards (DO-178C, ISO 26262, MIL-STD-498, etc.)
- Map document content to standard sections
- Generate compliance matrices showing coverage
- Export audit-ready reports (Word, Excel, PDF)
- Gap analysis: "Standard requires X, document doesn't address"
- Evidence linking: attach artifacts to compliance claims

**Why Important:**
Defense/aerospace audits require extensive compliance documentation. This saves weeks of manual work.

**Effort:** High (30-50 hours)

---

### ENH-017: Visual Document Quality Map (Heatmap)
**Status:** Proposed
**Priority:** ⚪ Enhancement (MEDIUM impact)
**Competitive Gap:** Some tools have basic highlighting

**Description:**
Visual representation of document quality showing problem areas at a glance.

**Features:**
- Color-coded document view (green=good, yellow=minor, red=critical)
- Section-level quality scoring
- Zoom from document overview to specific issues
- Exportable quality map for reviews
- Side-by-side comparison of quality maps over time

**Why Important:**
Visual representation helps reviewers quickly focus on problem areas. Current AEGIS only has list-based issue view.

**Effort:** Medium (10-15 hours)

---

### ENH-018: ReqIF Import/Export Module
**Status:** Proposed
**Priority:** ⚪ Enhancement (HIGH impact for enterprise)
**Competitive Gap:** DOORS, Jama, Polarion all support ReqIF

**Description:**
Support Requirements Interchange Format (ReqIF) for tool interoperability.

**Features:**
- Import ReqIF files from DOORS, Polarion, etc.
- Export AEGIS analysis results as ReqIF
- Preserve attributes, relationships, metadata
- Round-trip support (import → modify → export)
- Mapping configuration for custom attributes

**Why Important:**
ReqIF is the industry standard for requirements exchange. Without it, AEGIS can't integrate into enterprise toolchains.

**Effort:** High (25-35 hours)

---

### ENH-019: Collaborative Review Workflow
**Status:** Proposed
**Priority:** ⚪ Enhancement (MEDIUM impact)
**Competitive Gap:** All enterprise tools have this

**Description:**
Multi-user review and approval workflow.

**Features:**
- Assign reviewers to documents/sections
- Comment and discussion threads on issues
- Approval workflow (draft → review → approved)
- Email notifications for assignments
- Review status dashboard
- Audit trail of all review actions

**Why Important:**
Enterprise customers need multi-user collaboration. Currently AEGIS is single-user focused.

**Effort:** Very High (50-80 hours) - requires backend changes

---

### ENH-020: Vale/textlint Rule Compatibility Layer
**Status:** Proposed
**Priority:** ⚪ Enhancement (MEDIUM impact)
**Competitive Gap:** Technical writing tools use Vale

**Description:**
Support Vale and textlint style rules for compatibility with existing corporate style guides.

**Features:**
- Import Vale rule packages (.yml)
- Import textlint rules
- Convert to AEGIS internal format
- Support for major style guides (Microsoft, Google, Apple)
- Custom rule creation wizard

**Why Important:**
Many organizations already have Vale/textlint rules. Supporting these reduces adoption friction.

**Effort:** Medium (15-25 hours)

---

### Competitive Feature Priority Matrix

| Feature | Impact | Effort | Priority Score | Recommendation |
|---------|--------|--------|----------------|----------------|
| ENH-015: LLM Semantic Analysis | Very High | Very High | ⭐⭐⭐⭐⭐ | **#1 - Unique differentiator** |
| ENH-013: EARS/INCOSE Analyzer | High | High | ⭐⭐⭐⭐ | **#2 - Standards compliance** |
| ENH-011: Traceability Engine | High | High | ⭐⭐⭐⭐ | **#3 - Enterprise must-have** |
| ENH-012: Terminology Management | High | Medium-High | ⭐⭐⭐⭐ | **#4 - Customer pain point** |
| ENH-016: Compliance Generator | High | High | ⭐⭐⭐ | #5 - Audit support |
| ENH-018: ReqIF Support | High | High | ⭐⭐⭐ | #6 - Enterprise integration |
| ENH-014: Quality Dashboard | Medium | Medium | ⭐⭐⭐ | #7 - Manager visibility |
| ENH-017: Visual Quality Map | Medium | Medium | ⭐⭐ | #8 - Nice to have |
| ENH-020: Vale Compatibility | Medium | Medium | ⭐⭐ | #9 - Adoption ease |
| ENH-019: Collaborative Review | Medium | Very High | ⭐ | #10 - Major undertaking |

---

## Files to Exclude from Distribution Package

Based on analysis, these files/folders should NOT be included in the production package:

| Path | Size | Reason |
|------|------|--------|
| `.git/` | ~9.1 MB | Version control, not needed for deployment |
| `__pycache__/` | ~1.5 MB | Python bytecode, regenerates automatically |
| `logs/` | ~6.9 MB | Runtime logs, should start fresh |
| `*.pyc` | varies | Compiled Python, not needed |
| `test_*.py` | varies | Test files, not needed in production |
| `tests/` | varies | Test directory |
| `.pytest_cache/` | varies | Test cache |
| `*.md` (most) | varies | Dev documentation (keep README) |
| `.env` | varies | Local environment config |
| `nlp_offline/` | ~124 MB | CONDITIONAL - only exclude if NLP models installed system-wide |

**Estimated savings:** ~18 MB (without nlp_offline) or ~142 MB (with nlp_offline)

---

## Fixed Issues (Recent)

### ✅ v3.0.116 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| BUG-M02 | Batch Memory - Streaming file uploads, batch limits enforced | app.py |
| BUG-M03 | SessionManager Growth - Automatic cleanup thread (hourly, 24h TTL) | app.py |
| BUG-M04 | Batch Error Context - Full tracebacks now logged | app.py |
| BUG-M05 | Progress Persistence Key Collision - Unique doc IDs via hash | fix-assistant-state.js |
| BUG-L05 | Learner export endpoint CSRF - Added @require_csrf decorator | app.py |
| BUG-L07 | Batch limit constants defined (MAX_BATCH_SIZE=10, MAX_BATCH_TOTAL_SIZE=100MB) | app.py |
| BUG-L08 | Sound effects discoverable - One-time tooltip on first Fix Assistant open | app.js |
| BUG-L01 | Version comments - Updated to reference version.json | Multiple Python files |
| BUG-L03 | Console log prefixes - Standardized to `[TWR Module]` format | 8 JS feature modules |
| BUG-L04 | Magic numbers - Extracted to named constants | config_logging.py |

### ✅ v3.0.108 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| BUG-009 | Document filter dropdown not populated | role_integration.py, roles.js |

### ✅ v3.0.107 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| BUG-007 | Role Details missing sample_contexts | roles.js |
| BUG-008 | Role-Doc Matrix stuck on "Loading" | roles.js |

### ✅ v3.0.106 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| BUG-006 | Fix Assistant v2 Document Viewer empty (0 paragraphs) | core.py |
| BUG-M01 | Remaining deprecated datetime.utcnow() calls | config_logging.py |

### ✅ v3.0.105 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| BUG-001 | Report generator API signature mismatch | report_generator.py |
| BUG-002 | Learner stats missing success wrapper | app.py |
| BUG-003 | Acronym checker mode handling | acronym_checker.py |
| BUG-004 | Role classification tiebreak logic | role_extractor_v3.py |
| BUG-005 | Comment pack missing location hints | comment_inserter.py |
| WARN-001 | Deprecated datetime.utcnow() (partial) | app.py |

### ✅ v3.0.104 Fixes

| Bug ID | Description | File |
|--------|-------------|------|
| #1 | BodyText style conflict blocking FAv2 | report_generator.py |
| #2 | Logger reserved keyword conflict | app.py |
| #3 | Static file security test expectations | tests.py |
| #4 | CSS test location mismatches | tests.py |

### ✅ v3.0.98 Fixes

| Bug ID | Description |
|--------|-------------|
| BUG-001 | Double browser tab on startup |
| BUG-002 | Export modal crash |
| BUG-003 | Context highlighting showing wrong text |
| BUG-004 | Hyperlink status panel missing |
| BUG-005 | Version history gaps |
| BUG-007 | Role Details tab context preview |
| BUG-008 | Document filter dropdown |
| BUG-009 | Role-Document matrix tab missing |

### ✅ v3.0.97 Fixes (Fix Assistant v2 Integration)

| Issue | Description |
|-------|-------------|
| 1.1 | State.fixes never set |
| 1.2 | Backend missing FAV2 data fields |
| 2.1 | Job result endpoint missing FAV2 fields |
| 2.2 | Missing method stubs in FixAssistant API |
| 3.1 | Help documentation not updated |

---

## Testing Status

**Latest Test Run:** 2026-02-02
**Result:** 36/36 E2E tests passing
**Test File:** `tests/test_e2e_comprehensive.py`

### E2E Test Suite Coverage (v3.1.2)

| Test Class | Tests | Status |
|------------|-------|--------|
| TestEnvironment | 3 | ✅ Pass |
| TestPassiveVoiceChecker | 4 | ✅ Pass |
| TestRoleConsolidation | 7 | ✅ Pass |
| TestHyperlinkChecker | 3 | ✅ Pass |
| TestDarkModeCSS | 3 | ✅ Pass |
| TestGraphExport | 2 | ✅ Pass |
| TestDatabaseOperations | 1 | ✅ Pass |
| TestAPIEndpoints | 3 | ✅ Pass |
| TestPortfolioBatchCategorization | 1 | ✅ Pass |
| TestPassiveEventListeners | 2 | ✅ Pass |
| TestSidebarCollapse | 1 | ✅ Pass |
| TestHelpContentPerformance | 1 | ✅ Pass |
| TestDoclingStatusTimeout | 1 | ✅ Pass |
| TestPollFrequency | 1 | ✅ Pass |
| TestSortableJSLocal | 2 | ✅ Pass |
| TestIntegration | 1 | ✅ Pass |

### Legacy Test Coverage by Feature

| Feature | Tests | Status |
|---------|-------|--------|
| API Endpoints | 5 | ✅ Pass |
| Authentication | 4 | ✅ Pass |
| Acronym Checker | 6 | ✅ Pass |
| Analytics | 3 | ✅ Pass |
| Batch Limits | 2 | ⚠️ 1 Skip |
| Comment Inserter | 11 | ✅ Pass |
| Config | 4 | ✅ Pass |
| Error Handling | 2 | ✅ Pass |
| Export | 3 | ✅ Pass |
| File Validation | 4 | ✅ Pass |
| Fix Assistant v2 | 5 | ✅ Pass |
| Hyperlink Health | 6 | ✅ Pass |
| Role Extraction | 9 | ✅ Pass |
| Statement Forge | 4 | ✅ Pass |
| Static Security | 5 | ✅ Pass |
| UI Polish | 6 | ✅ Pass |
| Version | 3 | ✅ Pass |

---

## Prioritization Strategy

### Immediate (This Sprint)
All medium-priority bugs have been resolved in v3.0.116.

### Short-term (Next Sprint)
1. **BUG-L03** - Standardize console prefixes (1 hr, maintainability)
2. **BUG-L01** - Update file header versions (30 min)
3. **BUG-L08** - Sound effects discoverability (1 hr)

### Low Priority (Tech Debt)
4. **BUG-L02** - Type hints (ongoing)
5. **BUG-L04** - Extract magic numbers (30 min)
6. **BUG-L05** - CSRF on learner export (15 min)
7. **BUG-L06** - Remove unused imports (30 min)

---

## Bug Reporting Template

When finding new bugs, add them with this format:

```markdown
#### BUG-XXX: [Brief Title]
**Status:** Open  
**Priority:** 🔴/🟡/🟢  
**Location:** `file.py` line XXX  
**Impact:** [What breaks or degrades]  
**Evidence:** [How you found it - test failure, user report, code review]  
**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Expected: X, Actual: Y

**Fix:** [Proposed solution]  
**Effort:** Low/Medium/High (time estimate)
```

---

## Notes

- All 🔴 Critical bugs were fixed in v3.0.97-v3.0.105
- All 🟡 Medium bugs were fixed in v3.0.116
- The batch constants test should now pass (BUG-L07 fixed)
- SessionManager now auto-cleans every hour, removing sessions older than 24 hours
- Batch uploads now use streaming (8KB chunks) to reduce memory usage
