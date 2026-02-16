# AEGIS - Session Change Log

This document tracks changes made across development sessions. Add new sessions at the top.

---

## Session: 2026-02-07 - Roles Studio UI Enhancements (v4.0.1 → v4.0.2)

### Version: v4.0.2

### Summary
Fixed dark mode readability in Role Source Viewer, aligned RACI Matrix counts with Overview's deduplicated responsibility count, and added explore buttons to Role Details cards.

### Changes Made

#### 1. Role Source Viewer Dark Mode Fix
**File:** `static/js/features/role-source-viewer.js`

Added ~250 lines of comprehensive dark mode CSS:
- Document text area: `#e0e0e0` text on `#1e1e1e` background
- Headers, footers, panels: `#252525` with `#3a3a3a` borders
- Role highlights: amber gradient overlays visible in dark mode
- Form controls (buttons, selects, inputs): proper dark mode styling
- Footer shortcuts and keyboard hints: styled for readability

#### 2. RACI Matrix Deduplication Fix
**File:** `scan_history.py` - `get_raci_matrix()` method

```python
# v3.4.1: Track seen responsibilities per role for deduplication
seen_responsibilities_per_role = {}  # role_name -> set of normalized text

# When processing responsibilities:
normalized_text = text.strip().lower()[:100]
if normalized_text in seen_responsibilities_per_role[role_name]:
    continue  # Skip duplicate
seen_responsibilities_per_role[role_name].add(normalized_text)
```

**Result:**
- Before: RACI showed 406 total (counting duplicates across documents)
- After: RACI shows ~297 total (matching Overview's 298 unique responsibilities)

#### 3. Role Details Explore Button
**File:** `static/js/roles-tabs-fix.js`

Added explore button to each role card header:
```javascript
<button class="rd-explore-btn" data-role="${escapeHtml(role.role_name)}"
        title="Explore in Data Explorer" ...>
    <svg><!-- magnifying glass + plus icon --></svg>
</button>
```

Click handler opens Data Explorer and drills into the selected role:
```javascript
btn.addEventListener('click', (e) => {
    e.stopPropagation();
    window.TWR.DataExplorer.open();
    setTimeout(() => {
        window.TWR.DataExplorer.drillInto('role', roleName, { name: roleName });
    }, 600);
});
```

### Files Modified
| File | Changes |
|------|---------|
| `static/js/features/role-source-viewer.js` | ~250 lines dark mode CSS |
| `scan_history.py` | RACI deduplication logic |
| `static/js/roles-tabs-fix.js` | Explore button on role cards |
| `CHANGELOG.md` | Added v4.0.2 entry |
| `static/js/help-docs.js` | Added v4.0.2 changelog |
| `docs/NEXT_SESSION_PROMPT.md` | Updated for next session |
| `docs/TWR_PROJECT_STATE.md` | Updated version and changes |

### Testing
- Verified Role Source Viewer readable in dark mode
- Verified RACI totals: 285 R + 1 A + 11 C + 0 I = 297 (vs 298 in Overview)
- Verified explore buttons open Data Explorer for correct role

### Known Issues
- 1-responsibility difference between RACI (297) and Overview (298) - minor edge case

---

## Session: 2026-02-03 - Role Extraction Accuracy Overhaul (v3.2.4 → v3.2.5)

### Version: v3.2.5

### Summary
Major improvements to role extraction accuracy. Tested on OSHA, FAA, and NASA documents. Reduced false positives by 78% and improved accuracy from 36.7% to 56.7%.

### Problem Statement
Role extraction was producing too many false positives:
- Phone numbers being extracted as roles (e.g., "542-5795 Director California Department")
- Run-together PDF text (e.g., "Byasafetydepartment", "Thepersonnel")
- Location/address patterns (e.g., "Atlanta Federal Center", "Suite 670")
- Section headers (e.g., "C. Scalability")
- Single words that aren't roles (e.g., "User", "Owner", "Team")

### Changes Made

#### 1. Phone Number and Numeric Filtering
**File:** `role_extractor_v3.py` - `_clean_candidate()` method

```python
# v3.2.5: PHONE NUMBER AND NUMERIC FILTERING
if re.match(r'^\d', candidate):
    return ""  # Reject candidates starting with digits

phone_patterns = [
    r'\d{3}[-.\s]?\d{4}',  # ###-#### or ### ####
    r'\(\d{3}\)',          # (###)
    r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # ###-###-####
]

# Reject if >30% numeric
digit_count = sum(1 for c in candidate if c.isdigit())
if len(candidate) > 0 and digit_count / len(candidate) > 0.3:
    return ""
```

#### 2. Run-Together Word Filtering
**Files:** `role_extractor_v3.py`, `nlp_utils.py`

```python
# v3.2.5: Reject run-together words (PDF extraction artifacts)
if len(candidate) > 10 and ' ' not in candidate:
    if re.search(r'[a-z][A-Z]', candidate):  # camelCase
        return ""
    run_together_prefixes = ['bythe', 'bya', 'tothe', 'thepersonnel', ...]
    if any(candidate.lower().startswith(p) for p in run_together_prefixes):
        return ""
```

#### 3. Location/Address Pattern Filtering
**File:** `role_extractor_v3.py` - `_is_valid_role()` method

```python
# v3.2.5: Reject location/address patterns
location_words = {'center', 'building', 'suite', 'atlanta', 'california', ...}
if len(words) >= 2:
    location_count = sum(1 for w in words if w in location_words)
    has_number = any(w.isdigit() for w in words)
    if location_count >= 2 or (location_count >= 1 and has_number):
        if not any(w in ['administrator', 'director', 'manager'] for w in words):
            return False, 0.0
```

#### 4. Acronym Extraction Enhancement
**File:** `role_extractor_v3.py`

```python
# v3.2.5: Extended acronym pattern (6 words, supports &)
self.pattern_acronym = re.compile(
    r'([A-Z][a-zA-Z]+(?:[\s&]+[A-Z]?[a-zA-Z]+){0,5}?)\s*\(([A-Z][A-Z&/]{1,7})\)',
    re.MULTILINE
)

# v3.2.5: Extract acronym from NLP context
if nlp_role.context:
    acronym_match = re.search(
        re.escape(nlp_role.name) + r'\s*\(([A-Z][A-Z&/]{1,7})\)',
        nlp_role.context, re.IGNORECASE
    )
    if acronym_match:
        role_entry.variants.add(acronym_match.group(1).upper())
```

#### 5. Conservative NLP Override
**File:** `role_extractor_v3.py` - `_apply_nlp_enhancement()` method

```python
# v3.2.5: Only trust high-confidence NLP if it has role indicators
if not is_valid and nlp_role.confidence >= 0.85:
    role_indicators = ['manager', 'engineer', 'director', 'officer', ...]
    has_role_indicator = any(ind in name_lower for ind in role_indicators)
    if has_role_indicator:  # Only then trust NLP
        is_valid = True
```

#### 6. Expanded Single-Word Exclusions
**File:** `role_extractor_v3.py` - `SINGLE_WORD_EXCLUSIONS`

Added: user, users, owner, owners, chief, team, teams, group, groups, labor, section, sections, suite, center, division, office, department, authority, authorities, contractor, contractors, vendor, vendors, stakeholder, stakeholders, evaluator, evaluators, operator, operators, objectives, scalability

#### 7. New Role Definitions
**File:** `role_extractor_v3.py` - `KNOWN_ROLES`

*FAA/Aviation (25+):*
accountable executive, accountable manager, safety manager, certificate holder, certificate management team, flight crew, pilot in command, second in command, flight engineer, cabin crew, dispatcher, flight dispatcher, load master, maintenance controller, director of safety, director of operations, director of maintenance, chief pilot, check airman, training captain, standards captain, designated examiner, aviation safety inspector, principal operations inspector, principal maintenance inspector

*OSHA/Safety (25+):*
safety committee, process safety coordinator, process owner, area manager, plant manager, facility manager, operations manager, shift supervisor, unit supervisor, emergency coordinator, emergency response team, fire brigade, hazmat team, rescue team, first responder, safety officer, industrial hygienist, environmental health specialist, compliance officer, safety inspector, loss prevention specialist

### Test Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total roles extracted | 134 | 69 | -49% (noise removed) |
| Good roles | 40 | 38 | -5% (minor) |
| False positives | 9 | 2 | **-78%** |
| Accuracy estimate | 36.7% | 56.7% | **+54%** |

### Files Modified
- `role_extractor_v3.py` - All filtering and validation improvements
- `nlp_utils.py` (v1.1.2) - NLP-side filtering
- `version.json` - Updated to 3.2.5
- `CHANGELOG.md` - Added v3.2.5 section
- `docs/TWR_SESSION_HANDOFF.md` - Updated documentation

### Testing Commands
```bash
# Start server
TWR_CSRF=false python3 app.py

# Run accuracy analysis
python3 /tmp/analyze_role_accuracy.py

# Test acronym extraction
python3 /tmp/test_acronym_roles.py
```

### Known Limitations
- Large PDFs (>3MB) may timeout during processing due to Docling model loading
- NASA documents require HF_HUB_OFFLINE=0 for model downloads

---

## Session: 2026-02-03 - Enhanced Analyzers Integration (v3.2.3 → v3.2.4)

### Version: v3.2.4

### Summary
Integrated 5 new NLP-based analysis modules into the core review engine and enhanced role extraction with improved spaCy integration.

### New Modules Created
1. `semantic_analyzer.py` - Sentence-Transformers semantic similarity
2. `acronym_extractor.py` - Schwartz-Hearst acronym extraction
3. `prose_linter.py` - Vale-style technical writing rules
4. `structure_analyzer.py` - Document structure analysis
5. `text_statistics.py` - Readability and text metrics

### Integration
- Created `enhanced_analyzers.py` wrapper for BaseChecker compatibility
- Added option mappings in `core.py` for UI checkbox control
- Added 5 new API endpoints in `app.py`

---

## Session: 2026-02-03 - Role Dictionary Integration Fixes (v3.2.0 → v3.2.2)

### Version: v3.2.2

### Summary
Fixed critical issues with role adjudication not persisting to the role dictionary database. Added backup save mechanism, fixed UI styling in the dictionary table, and confirmed the role extraction engine integration is working correctly.

### Changes Made

#### 1. Adjudication Dictionary Save Fix
**Files Modified:**
- `static/js/features/role-source-viewer.js` (v3.2.0 → v3.2.2)

**Functionality:**
- Enhanced `handleAdjudication()` with proper error handling
- Added `addRoleToDictionaryBackup()` as fallback save method
- Enhanced `syncWithRolesAdjudication()` with complete field mapping
- Added comprehensive logging for debugging

**Key Code:**
```javascript
// Primary save via /api/roles/adjudicate
// If fails, backup via /api/roles/dictionary
await addRoleToDictionaryBackup(roleName, action, category, notes);
```

#### 2. Role Dictionary UI Fixes
**Files Modified:**
- `static/css/features/roles-studio.css`

**Fixes:**
- Delete button now shows trash icon instead of red box
- Ghost danger button styling: transparent bg, red on hover
- Dictionary table action buttons properly sized
- Status badges (status-active/status-inactive) styled correctly

**CSS Added:**
```css
.btn-ghost.btn-danger {
    background: transparent !important;
    color: var(--text-muted, #9ca3af);
}
.btn-ghost.btn-danger:hover {
    background: rgba(239, 68, 68, 0.1) !important;
    color: var(--error, #ef4444) !important;
}
```

#### 3. Role Extraction Engine Integration (Confirmed Working)
**Files Verified:**
- `role_extractor_v3.py`

**Integration Points:**
- `_load_dictionary_roles()` - Loads confirmed roles into `known_roles` (0.95 confidence)
- `_load_rejected_roles()` - Loads rejected roles into `false_positives` (excluded)

**Database Queries:**
```sql
-- Confirmed roles
SELECT role_name, aliases FROM role_dictionary
WHERE is_active = 1 AND is_deliverable = 0

-- Rejected roles
SELECT role_name, aliases FROM role_dictionary
WHERE is_active = 0 AND source = 'adjudication'
```

### Testing Notes
- Adjudicate a role → verify in DB: `sqlite3 scan_history.db "SELECT * FROM role_dictionary WHERE source='adjudication'"`
- Role should disappear from pending list (filter shows pending only by default)
- Delete button should show trash icon, turn red on hover
- Status badges should be green (Active) or gray (Inactive)

### Version Progression
- v3.2.0: Initial Role Source Viewer with adjudication UI
- v3.2.1: Added adjudication API endpoints
- v3.2.2: Fixed dictionary save issues and UI styling

---

## Session: 2026-02-03 - Role Source Viewer with Adjudication Controls (v3.1.9 → v3.2.0)

### Version: v3.2.0

### Summary
Implemented a comprehensive Role Source Viewer with full adjudication controls, transforming it into the primary role review interface. Users can now view actual document text with highlighted role mentions from historical scans and make informed adjudication decisions with Confirm, Mark Deliverable, and Reject actions.

### Changes Made

#### 1. Role Source Viewer Adjudication Panel
**Files Modified:**
- `static/js/features/role-source-viewer.js` (v3.0.0 → v3.1.0)

**Functionality:**
- Added adjudication section to right panel with:
  - Status indicator badge (Pending Review, Confirmed, Deliverable, Rejected)
  - Three action buttons: Confirm Role (green), Mark Deliverable (blue), Reject (red)
  - Category dropdown (Role, Management, Technical, Organization, Custom)
  - Notes textarea for adjudication comments
- Added event handlers for adjudication actions
- Added `handleAdjudication(action)` async function with API integration
- Added `handleCategoryChange(category)` for category updates
- Added `updateStatusBadge(status)` and `updateAdjudicationButtons(action)` functions
- Added `showToast(message, type)` with fallback notification system
- Added `getCSRFToken()` helper for secure API calls

**HTML Added:**
```html
<!-- Adjudication Section -->
<div class="rsv-adjudication-section">
    <label>Adjudication</label>
    <div class="rsv-status-indicator">
        <span class="rsv-status-badge" data-status="pending">Pending Review</span>
    </div>
    <div class="rsv-adjudication-actions">
        <button class="rsv-adj-btn rsv-adj-confirm">Confirm Role</button>
        <button class="rsv-adj-btn rsv-adj-deliverable">Mark Deliverable</button>
        <button class="rsv-adj-btn rsv-adj-reject">Reject</button>
    </div>
    <div class="rsv-category-section">...</div>
    <div class="rsv-notes-section">...</div>
</div>
```

**CSS Added:**
- `.rsv-adjudication-section` - Background panel styling
- `.rsv-status-badge[data-status="pending|confirmed|deliverable|rejected"]` - Color-coded badges
- `.rsv-adj-btn`, `.rsv-adj-confirm`, `.rsv-adj-deliverable`, `.rsv-adj-reject` - Button styling
- `.rsv-adj-active` - Active state highlighting
- `.rsv-category-select`, `.rsv-notes-input` - Form element styling
- `.rsv-divider` - Visual separator
- `.rsv-toast`, `.rsv-toast-success`, `.rsv-toast-error` - Notification styling

#### 2. Document Text Retrieval for Historical Scans
**Files Modified:**
- `app.py` - Added `/api/scan-history/document-text` endpoint

**Functionality:**
- Retrieves `full_text` from `results_json` column in scans table
- Returns document text for historical scans (no need to re-extract from file)
- Handles missing documents gracefully

**API Endpoint:**
```
GET /api/scan-history/document-text?filename=<document_name>

Response:
{
    "success": true,
    "text": "Full document text...",
    "filename": "document.docx"
}
```

#### 3. Document Compare Modal Sizing Fix
**Files Modified:**
- `static/css/features/doc-compare.css`

**Problem:**
- Document Compare modal appeared compacted/too small

**Fix Applied:**
```css
#modal-doc-compare .modal-content,
#modal-doc-compare.modal-fullscreen .modal-content,
#modal-doc-compare .dc-modal-content,
.dc-modal-content {
    width: 95vw !important;
    height: 90vh !important;
    max-width: 1800px !important;
    min-width: 900px;
}
```

#### 4. Browser Cache-Busting
**Files Modified:**
- `templates/index.html`

**Change:**
- Added version query strings to script tags for cache-busting
- `<script src="/static/js/features/role-source-viewer.js?v=3.1.0"></script>`

### Data Flow

```
User clicks role name in Roles tab
    → TWR.RoleSourceViewer.open(roleName) called
    → Modal displays with left panel (document text) and right panel (details + adjudication)
    → If no text in State.currentText, fetches from /api/scan-history/document-text
    → Document text displayed with all role mentions highlighted
    → User can navigate between mentions with Prev/Next or click highlights

User clicks adjudication button (e.g., "Confirm Role")
    → handleAdjudication('confirmed') called
    → UI updates immediately (status badge, button highlight)
    → POST to /api/roles/adjudicate with role_name, action, category, notes
    → Toast notification shows success/error
    → If API unavailable, UI still updates locally
```

### Testing Notes
- Verified Role Source Viewer opens with document text from historical scans
- Verified adjudication buttons update status badge correctly
- Verified notes and category fields are captured
- Verified toast notifications display on action
- Verified modal sizing fix displays properly

### Files Summary

| File | Action | Description |
|------|--------|-------------|
| `static/js/features/role-source-viewer.js` | Modified | Added adjudication section (v3.1.0) |
| `static/css/features/doc-compare.css` | Modified | Fixed modal sizing with !important |
| `app.py` | Modified | Added /api/scan-history/document-text endpoint |
| `templates/index.html` | Modified | Cache-busting version strings |
| `version.json` | Modified | Updated to v3.2.0 |
| `CHANGELOG.md` | Modified | Added v3.2.0 entry |

### Follow-up Changes (Same Session)

#### 5. Per-Role Adjudication Persistence
**Problem:**
- Adjudication state was persisting across all roles, not tracking per-role
- Adjudicated roles were not being saved to the dictionary
- Rejected roles were not being used to improve future extractions

**Solution:**
Added three new API endpoints and integrated with the Role Dictionary:

**New API Endpoints in `app.py`:**
- `POST /api/roles/adjudicate` - Saves adjudication to role_dictionary table
- `GET /api/roles/adjudication-status?role_name=<name>` - Returns current status
- `POST /api/roles/update-category` - Updates category classification

**New Method in `scan_history.py`:**
- `get_role_by_name(role_name)` - Lookup role by name (case-insensitive)

**Role Source Viewer Updates (`role-source-viewer.js` v3.2.1):**
- Added `resetAdjudicationPanel()` - Resets UI when opening new role
- Added `loadAdjudicationStatus()` - Loads saved status from API
- Each role now shows its own adjudication state

**Role Extractor Enhancement (`role_extractor_v3.py`):**
- Added `_load_rejected_roles()` method
- Rejected roles are automatically added to `false_positives`
- Makes extractor smarter over time as users adjudicate

### Adjudication Learning Flow

```
User adjudicates role as "Rejected"
    → POST /api/roles/adjudicate with action='rejected'
    → Role added to role_dictionary with is_active=0
    → Next extraction: rejected role in false_positives → not detected

User adjudicates role as "Confirmed"
    → Role added to role_dictionary with is_active=1
    → Next extraction: confirmed role in known_roles → higher confidence
```

### Known Issues / Future Improvements
- Could add bulk adjudication across multiple roles
- Could add undo/revert functionality for adjudications
- Could show adjudication history/audit trail

---

## Session: 2026-02-02 - Molten Progress Integration & Loader Fix (v3.1.8 → v3.1.9)

### Version: v3.1.9

### Summary
This session continued the Rive-inspired visual enhancements, creating a scalable molten progress bar system and integrating it throughout the application. Also fixed a critical bug where the AEGIS loader was blocking all UI clicks after fade-out, and removed the initial startup loader since the app loads fast enough without it.

### Changes Made

#### 1. Molten Progress Bar System (NEW)
**Files Created:**
- `static/css/features/molten-progress.css` - Scalable molten progress bar component (457 lines)
- `static/js/features/molten-progress.js` - JavaScript API for dynamic progress bars

**Features:**
- 4 size variants: mini (4px), small (8px), medium (16px), large (28px)
- 3 color themes: orange (default), blue, green
- Rive-inspired molten gradient: deep orange → amber → yellow → white-hot
- Glowing orb at leading edge with pulse animation
- Optional reflection glow below bar
- Optional trailing effect
- Indeterminate loading state (contained within bar bounds)
- Accessibility support (reduced motion)
- Light/dark mode compatibility

#### 2. Molten Progress Integration
**Files Modified:**
- `static/js/app.js` - Batch document row progress bars (molten-mini)
- `templates/index.html` - Loading overlay progress bar (molten-medium with reflection)
- `static/js/features/hyperlink-visualizations.js` - HV progress bar (molten-small with reflection)
- `static/js/features/cinematic-progress.js` - Batch modal progress (molten-small with reflection)

#### 3. AEGIS Loader Enhancement (v2.4)
**Files Modified:**
- `static/css/features/cinematic-loader.css` - Molten theme colors and enhanced glow effects
- `static/js/features/cinematic-loader.js` - Molten particle colors and critical bug fix

**Visual Changes:**
- Molten color palette throughout (orange/amber/yellow/white-hot)
- Enhanced orb with white-hot core
- Rive-style reflection glow below progress bar
- Orange-dominated particle effects

**Bug Fix:**
- **Issue**: After fade-out animation, loader had `opacity: 0` but still `pointer-events: auto` and `z-index: 99999`, blocking ALL clicks on the page
- **Fix**: Added `onComplete` callback to GSAP timeline that sets `pointer-events: none`, `display: none`, and `running = false`

#### 4. Removed Initial Startup Loader
**Files Modified:**
- `templates/index.html` - Removed AEGIS loader HTML and init script (kept hidden stub for compatibility)
- `static/js/app.js` - Removed `updateLoaderProgress()` and `completeLoader()` functions, simplified DOMContentLoaded handler

**Rationale:**
- App initializes in <500ms on typical hardware
- Loading screen was barely visible before fade-out
- Reduces unnecessary visual overhead
- CinematicLoader still available for batch processing where it's actually useful

### Files Summary
| File | Action | Description |
|------|--------|-------------|
| `static/css/features/molten-progress.css` | Created | Scalable molten progress bar styles |
| `static/js/features/molten-progress.js` | Created | MoltenProgress JavaScript API |
| `static/css/features/cinematic-loader.css` | Modified | Molten theme colors, enhanced glow |
| `static/js/features/cinematic-loader.js` | Modified | Molten colors, pointer-events fix |
| `static/js/app.js` | Modified | Molten progress in batch rows, removed loader code |
| `templates/index.html` | Modified | Molten progress in overlay, removed AEGIS loader |
| `static/js/features/hyperlink-visualizations.js` | Modified | Molten progress bar |
| `static/js/features/cinematic-progress.js` | Modified | Molten progress bar |

### Testing
- Verified all buttons clickable after removing loader
- Verified molten progress bars render correctly
- Verified no console errors on page load
- Tested profile selection buttons (Grammar, Requirements, etc.)

---

## Session: 2026-02-02 - Comprehensive Enhancement Implementation (v3.1.2 → v3.1.4)

### Versions: v3.1.2 → v3.1.3 → v3.1.4

### Summary
Implemented all remaining enhancements from the TWR_BUG_TRACKER.md, bringing the application from v3.1.2 to v3.1.4. This session implemented 7 major enhancements covering NLP integration, role comparison, universal role viewers, statement forge review mode, comprehensive logging/diagnostics, and clean upgrade paths. All 75 E2E tests pass.

### Changes Made

#### 1. ENH-008: NLP Integration with spaCy
**Files Created:**
- `nlp_utils.py` - NLP processor with spaCy integration

**Functionality:**
- NLPProcessor class with spaCy integration for enhanced extraction
- Named Entity Recognition (NER) for role extraction
- Noun phrase chunking for deliverable extraction
- Acronym detection with definition parsing
- Pattern-based fallback when spaCy unavailable

#### 2. ENH-004: Multi-document Role Comparison
**Files Created:**
- `role_comparison.py` - Role comparison module

**Functionality:**
- RoleComparator class for multi-document analysis
- Identifies common, partial, and unique roles
- Generates reports in text, Markdown, and HTML formats
- Includes consistency scoring across documents

#### 3. ENH-005: Universal Role Source Viewer
**Files Created:**
- `static/js/features/role-source-viewer.js`

**Functionality:**
- Modal-based viewer accessible from any role display
- Multi-document navigation (Previous/Next)
- Multi-occurrence support within documents
- Context highlighting with surrounding text
- Auto-initialization with CSS injection

#### 4. ENH-006: Statement Forge Review Mode
**Files Created:**
- `static/js/features/statement-review-mode.js`

**Files Modified:**
- `statement_forge/models.py` - Added source context fields

**Functionality:**
- Review mode with source document context
- Navigate between statements (Previous/Next)
- Approve/Reject/Save actions
- Create statements from text selection
- Keyboard shortcuts: ←→ nav, S=save, A=approve, R=reject, Esc=close
- Dark mode support

**New Statement Model Fields:**
- source_document: Name of the source document
- source_char_start/end: Character offsets
- source_context_before/after: Surrounding text
- source_page: Page number if available
- source_section_title: Section heading where found

#### 5. ENH-009: Comprehensive Logging System
**Files Created:**
- `diagnostics.py` - Backend diagnostics module
- `static/js/features/frontend-logger.js` - Frontend logger

**Backend Features:**
- CircularLogBuffer for memory-efficient log storage (configurable max size)
- AsyncLogQueue for non-blocking log writes with batching
- SamplingLogger for high-frequency events (configurable threshold)
- PerformanceTimer context manager
- @timed decorator for function timing
- Flask blueprint for diagnostics API endpoints
- Full export_diagnostics() for troubleshooting

**Frontend Features:**
- Circular buffer for recent logs
- API call timing with response logger pattern
- User action tracking
- Performance measurement with startTimer/logPerformance
- Backend sync support via /api/diagnostics/frontend

#### 6. ENH-010: Clean Upgrade Path
**Files Modified:**
- `update_manager.py` - Enhanced from v1.4 to v1.5

**New UpdateManager Methods:**
- get_current_version() - Read version from version.json
- compare_versions(v1, v2) - Semantic version comparison
- check_update_package_version(path) - Check .zip package version
- backup_user_data() - Backup user data before upgrade
- restore_user_data(path) - Restore user data after upgrade
- apply_update_package(path, preserve_user_data) - Full upgrade workflow

**New API Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/updates/version` | GET | Get current installed version |
| `/api/updates/check-package` | POST | Check update package version |
| `/api/updates/backup-userdata` | POST | Backup user data |
| `/api/updates/restore-userdata` | POST | Restore user data |
| `/api/updates/apply-package` | POST | Apply update with preservation |

**User Data Preserved:**
- scan_history.db - Scan history database
- user_settings.json - User preferences
- custom_dictionaries/ - User word lists
- learner_data/ - ML training data
- hyperlink_exclusions.db - Link exclusion rules
- logs/ - Recent logs for debugging

#### 7. Test Suite Expansion
**Files Modified:**
- `tests/test_e2e_comprehensive.py`

**New Test Classes:**
- TestNLPIntegration (8 tests)
- TestRoleComparison (4 tests)
- TestDiagnostics (8 tests)
- TestRoleSourceViewer (3 tests)
- TestFrontendLogger (3 tests)
- TestStatementReviewMode (6 tests)
- TestUpgradeManager (7 tests)

**Test Results:**
```
75 passed in 6.51s
```

#### 8. Documentation Updates
**Files Modified:**
- `CHANGELOG.md` - Added v3.1.2, v3.1.3, v3.1.4 entries
- `CHANGELOG_SESSION.md` - This session log
- `static/js/help-docs.js` - Version history section
- `version.json` - Updated to v3.1.4
- `TWR_BUG_TRACKER.md` - Marked ENH-005, 006, 009, 010 as implemented

### Data Flow

**Upgrade Flow (ENH-010):**
```
User initiates upgrade via API or UI
    → check_update_package_version() verifies package is newer
    → backup_user_data() saves USER_DATA_PATHS to backups/userdata_X/
    → create_backup() saves current code files
    → Extract .zip to temp, copy files (excluding user data)
    → restore_user_data() puts user data back
    → If failure at any step, rollback() restores from backup
```

**Logging Flow (ENH-009):**
```
Application code calls logger.info('message', **kwargs)
    → AsyncLogQueue batches log entries
    → Worker thread processes batch
    → CircularLogBuffer stores (max 10000 entries)
    → SamplingLogger filters high-frequency events
    → /api/diagnostics/export returns full state
```

### Testing Notes
- All 75 tests pass with pytest
- NLP tests skip gracefully if spaCy not installed
- Diagnostics tests handle async queue timing
- Statement model tests verify new fields are serialized

### Files Summary

| Category | Files Created | Files Modified |
|----------|--------------|----------------|
| Python Modules | nlp_utils.py, role_comparison.py, diagnostics.py | update_manager.py, statement_forge/models.py |
| JavaScript | role-source-viewer.js, frontend-logger.js, statement-review-mode.js | help-docs.js |
| Tests | - | test_e2e_comprehensive.py |
| Documentation | - | CHANGELOG.md, CHANGELOG_SESSION.md, TWR_BUG_TRACKER.md |
| Config | - | version.json, templates/index.html |

### Known Issues / Future Improvements
- ENH-007 (HD Graphics) still pending - requires SVG assets from user
- spaCy models require separate installation (~500MB)
- Frontend logger backend sync not yet integrated into UI

---

## Session: 2026-02-01 - Hyperlink Validator Visual Overhaul

### Version: v3.0.125

### Summary
Comprehensive visual enhancement of the Hyperlink Validator with modern glassmorphism design, animated stat cards, interactive data visualizations (donut chart, response time histogram, domain health heatmap), and enhanced progress indicators. Also conducted a full code review for Windows compatibility and robustness.

### Changes Made

#### 1. Enhanced CSS Stylesheet
**Files Created:**
- `static/css/features/hyperlink-enhanced.css` (600+ lines)

**Visual Features:**
- Glassmorphism stat cards with backdrop blur and gradient accents
- Animated counter values with ease-out cubic-bezier timing
- Color-coded status indicators (working=green, broken=red, timeout=yellow, etc.)
- Hover effects with transform and shadow transitions
- Dark mode support via CSS variables
- Shimmer animation on progress bar fill
- Skeleton loading states for better perceived performance

**CSS Classes Added:**
- `.hv-stat-card`, `.hv-stat-card-icon`, `.hv-stat-card-value`
- `.hv-donut-container`, `.hv-donut-segment`, `.hv-donut-center`
- `.hv-histogram-container`, `.hv-histogram-bar`
- `.hv-heatmap-container`, `.hv-heatmap-cell`, `.health-*` variants
- `.hv-streaming-indicator`, `.hv-streaming-dot`
- `.hv-progress-enhanced`, `.hv-progress-bar-fill`
- `.hv-rescan-btn` with gradient and shimmer animation
- `.hv-result-details`, `.hv-redirect-chain`

#### 2. Visualization JavaScript Module
**Files Created:**
- `static/js/features/hyperlink-visualizations.js`

**Functions:**
- `createDonutChart(container, data)` - SVG donut chart with animated segments
- `createResponseHistogram(container, results)` - Color-coded speed histogram
- `createDomainHeatmap(container, results)` - Clickable domain health tiles
- `createStatCards(container, summary)` - Animated stat card grid
- `createStreamingIndicator(container)` - Real-time validation indicator
- `createEnhancedProgress(container, progress)` - Progress with ETA and speed
- `createErrorDetails(result)` - Expandable error detail panels
- `createSkeleton(container, type)` - Loading placeholders

**Design Patterns:**
- Modular IIFE pattern with public API
- Configurable color palette and animation timing
- SVG-based charts for crisp rendering at any resolution
- Event delegation for dynamic content

#### 3. HTML Template Updates
**Files Modified:**
- `templates/index.html`

**New Elements:**
- Enhanced stat cards grid (`#hv-stats-grid`)
- Chart section with donut and histogram (`#hv-chart-section`)
- Domain health heatmap section (`#hv-domain-heatmap-section`)
- Rescan button for bot-protected sites (`#hv-rescan-section`)
- Updated mode dropdown (removed ps1_validator option)

#### 4. Validator UI Integration
**Files Modified:**
- `static/js/features/hyperlink-validator.js`

**New Functions:**
- `animateCount(element, target)` - Smooth number animation
- `renderVisualizations(summary)` - Orchestrates all chart rendering
- `handleRescan()` - Headless browser rescan for blocked URLs

**Integration Points:**
- `renderSummary()` now calls `renderVisualizations()`
- Rescan button bound dynamically when blocked URLs detected
- Domain heatmap cells filter results on click

#### 5. Code Review & Windows Compatibility
**Analysis Completed:**
- Full review of `hyperlink_validator/` directory (6 files, ~5000+ lines)
- Full review of frontend modules (4 files, ~3000+ lines)

**Findings:**
- SQL in storage.py is safe (column names hardcoded, values parameterized)
- Windows path handling adequate for current use cases
- Temporary file cleanup uses platform-agnostic methods
- Chrome channel detection works on Windows when Chrome is installed

**Recommendations Documented:**
- Add rate limiting for production deployments
- Consider connection pooling for high-volume validation
- Add database migrations for schema versioning

### Visual Design System

**Color Palette:**
```css
--hv-chart-green: #22c55e;  /* Working */
--hv-chart-red: #ef4444;    /* Broken */
--hv-chart-yellow: #f59e0b; /* Timeout */
--hv-chart-blue: #3b82f6;   /* Redirect */
--hv-chart-purple: #8b5cf6; /* Blocked */
--hv-chart-cyan: #06b6d4;   /* Info */
```

**Animation Timing:**
- Duration: 600ms
- Easing: `cubic-bezier(0.4, 0, 0.2, 1)` (smooth deceleration)
- Stagger: 100ms between elements

### Testing Notes
- All JavaScript files syntax-checked
- CSS validated for dark mode compatibility
- Lucide icons render correctly after dynamic content insertion

### Known Issues / Future Improvements
- Rescan results not yet merged back into main results state
- Could add PDF export of visualizations
- Could add comparison view between two validation runs

---

## Session: 2026-02-01 - Hyperlink Validator Simplification & Headless Browser Rescan

### Version: v3.0.124

### Summary
Simplified the Hyperlink Validator from 3 modes to 2 modes (Offline and Validator), enhanced government site validation with robust HEAD/GET fallback, and implemented headless browser rescan for bot-protected sites like .mil and .gov domains. Added Playwright installation to setup.bat.

### Changes Made

#### 1. Validator Mode Simplification
**Files Modified:**
- `hyperlink_validator/validator.py`

**Functionality:**
- Removed `ps1_validator` mode - now only 2 modes: `offline` and `validator`
- `offline` mode: Format validation only (no HTTP requests)
- `validator` mode: Full HTTP validation with Windows integrated auth (NTLM/Negotiate SSO)
- Added parameters: `client_cert`, `ca_bundle`, `proxy`, `verify_ssl`
- Government sites (.mil, .gov) use Windows auth automatically

#### 2. HEAD/GET Fallback for Government Sites
**Files Modified:**
- `hyperlink_validator/validator.py` (validate_url function)

**Problem:**
- Many government sites (e.g., quicksearch.dla.mil) block HEAD requests, returning 404/403/405 even when the page is accessible via GET

**Fix Applied:**
```python
# Check if HEAD returned an error - many gov sites block HEAD
if response.status_code in [404, 405, 403, 501]:
    head_failed = True
    continue  # Retry with GET
```

**Result:**
- First attempts HEAD request for efficiency
- If HEAD fails with 404/405/403/501, automatically retries with GET
- Successfully validates government sites that block HEAD

#### 3. Headless Browser Rescan Feature
**Files Created:**
- `hyperlink_validator/headless_validator.py`

**Functionality:**
- Playwright-based headless browser validation for bot-protected sites
- Uses real Chrome channel (not Chromium) to bypass bot detection
- Stealth scripts remove `navigator.webdriver` detection
- Configurable timeout, headless mode, user agent
- Batch validation with concurrency control

**Key Implementation:**
```python
self._browser = self._playwright.chromium.launch(
    headless=self.headless,
    channel="chrome",  # Use real Chrome if available
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
    ]
)
```

#### 4. Rescan API Endpoints
**Files Modified:**
- `hyperlink_validator/routes.py`

**New Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rescan/capabilities` | GET | Check if headless rescan is available |
| `/rescan` | POST | Start headless rescan of failed URLs |
| `/rescan/job/<job_id>` | GET | Get rescan job status/results |

**Features:**
- Maximum 50 URLs per rescan (headless is slower)
- Returns job_id for async status polling
- Reports recovered URLs vs still-failed

#### 5. Authentication Settings UI
**Files Modified:**
- `templates/index.html`
- `config.json`

**New UI Elements:**
- "Advanced Authentication Settings" collapsible panel in Hyperlink Validator
- Inputs for:
  - Client Certificate Path (CAC/PIV)
  - Client Key Path
  - CA Bundle Path
  - Proxy URL
  - Verify SSL toggle

**Config Keys Added:**
```json
{
    "client_cert_path": "",
    "client_key_path": "",
    "ca_bundle_path": "",
    "proxy_url": "",
    "verify_ssl": true
}
```

#### 6. Help Documentation Update
**Files Modified:**
- `static/js/help-docs.js`

**Updates:**
- Added "Headless Browser Rescan" section explaining the feature
- Added "Authentication Options" table documenting all auth settings
- Updated version to 3.0.124

#### 7. Setup Script Update
**Files Modified:**
- `setup.bat`

**Changes:**
- Updated version from 3.0.97 to 3.0.124
- Added Step 8/8: Headless Browser (Playwright) installation
- Installs `playwright` via pip
- Downloads Chromium via `playwright install chromium`
- Added verification check for Playwright import
- Updated disk space estimate from ~600MB to ~800MB

### Testing Results

**Government Sites Tested:**
| Site | Standard Validator | Headless Rescan |
|------|-------------------|-----------------|
| quicksearch.dla.mil | ✅ (after GET fallback) | ✅ |
| dla.mil | ❌ 403 (bot blocked) | ✅ Recovered |
| defense.gov | ❌ 403 (bot blocked) | ✅ Recovered |
| navy.mil | ❌ 403 | ❌ (aggressive protection) |
| af.mil | ❌ 403 | ❌ (aggressive protection) |

**Key Finding:**
- Using `channel="chrome"` (real Chrome) bypasses most bot detection
- Plain Chromium gets blocked by Akamai/Cloudflare protection
- Some .mil sites (navy.mil, af.mil) have extremely aggressive protection that even real Chrome can't bypass

### Data Flow

```
User initiates validation
    → Standard validator runs (HEAD/GET with Windows auth)
    → Some URLs fail with 403 (bot blocked)
    → User clicks "Rescan with Browser"
    → POST /rescan with failed URLs
    → Headless Chrome validates each URL
    → Results show recovered vs still-failed
    → User can update results with recovered URLs
```

### Key Code Patterns

**Stealth Script for Bot Bypass:**
```javascript
// Injected into every page
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
```

**Chrome Channel vs Chromium:**
```python
# This gets blocked by most bot protection:
browser = playwright.chromium.launch(headless=True)

# This bypasses most bot protection:
browser = playwright.chromium.launch(
    headless=True,
    channel="chrome"  # Uses installed Chrome
)
```

### Known Issues / Future Improvements
- navy.mil and af.mil remain blocked even with headless Chrome
- Could add proxy rotation for additional bypass capability
- Could add CAPTCHA detection and user notification

---

## Session: 2026-02-01 - Low Priority Bug Fixes (Continued)

### Version: v3.0.116

### Summary
Completed all remaining low-priority bug fixes from the bug tracker. This session fixed 6 low-priority issues: version comments in file headers, console log prefix standardization, magic number extraction, unused import cleanup, CSRF on learner export, and verified sound effects discoverability was already implemented.

### Changes Made

#### 1. BUG-L05: CSRF on Learner Export Endpoint
**Files Modified:**
- `app.py` (learner_export function)

**Functionality:**
- Added `@require_csrf` decorator to `/api/learner/export` endpoint for consistency
- Endpoint was previously unprotected (read-only, low risk) but now follows same pattern as other endpoints

#### 2. BUG-L08: Sound Effects Discoverability
**Status:** Already implemented - verified existing code

**Files Verified:**
- `static/js/app.js` (lines ~4840-4892)

**Existing Implementation:**
- `showSoundDiscoveryTip()` function shows one-time tooltip on first Fix Assistant open
- Uses localStorage key `twr_sound_tip_shown` to track if user has seen it
- Tooltip auto-dismisses after 8 seconds or can be manually closed
- Only shows if sounds are disabled (default state)

#### 3. BUG-L01: Version Comments in File Headers
**Files Modified:**
- `config_logging.py`
- `comment_inserter.py`
- `nlp_enhancer.py`
- `image_figure_checker.py`
- `word_language_checker.py`
- `enhanced_table_extractor.py`

**Change Pattern:**
- Changed `Version: X.X.X` to `Version: reads from version.json (module vX.X)`
- Follows pattern already used in `api_extensions.py`
- Clarifies that main app version comes from version.json while noting module-specific version

#### 4. BUG-L03: Console Log Prefix Standardization
**Files Modified:**
- `static/js/features/hyperlink-validator.js` - `[HV UI]` → `[TWR HyperlinkValidator]`
- `static/js/features/hyperlink-validator-state.js` - `[HV State]` → `[TWR HVState]`
- `static/js/features/link-history.js` - `[LinkHistory]` → `[TWR LinkHistory]`
- `static/js/features/console-capture.js` - `[ConsoleCapture]` → `[TWR ConsoleCapture]`
- `static/js/features/portfolio.js` - `[Portfolio]` → `[TWR Portfolio]`
- `static/js/features/fix-assistant-state.js` - `[FixAssistantState]` → `[TWR FAState]`
- `static/js/features/doc-compare-state.js` - `[DocCompareState]` → `[TWR DocCompare]`
- `static/js/features/roles.js` - `[Adjudication]` → `[TWR Roles]`, `[Graph]` → `[TWR Graph]`

**Standard Format:**
- All console logs now use `[TWR ModuleName]` prefix
- Enables easy filtering in browser console with `[TWR` pattern

#### 5. BUG-L04: Magic Numbers Extraction
**Files Modified:**
- `config_logging.py` (lines ~24-35)

**Constants Added:**
```python
DEFAULT_MAX_UPLOAD_MB = 50          # Default max upload size in megabytes
MAX_SAFE_UPLOAD_MB = 500            # Maximum safe upload limit in megabytes
DEFAULT_RATE_LIMIT_REQUESTS = 100   # Default requests per window
DEFAULT_RATE_LIMIT_WINDOW = 60      # Default window in seconds
MIN_SECRET_KEY_LENGTH = 32          # Minimum secret key length
LOG_FILE_MAX_BYTES = 5 * 1024 * 1024  # 5MB max per log file
LOG_BACKUP_COUNT = 5                # Number of log backup files to keep

# Derived constants
DEFAULT_MAX_UPLOAD_BYTES = DEFAULT_MAX_UPLOAD_MB * 1024 * 1024
MAX_SAFE_UPLOAD_BYTES = MAX_SAFE_UPLOAD_MB * 1024 * 1024
```

**References Updated:**
- `AppConfig.max_content_length` default
- `AppConfig.rate_limit_requests` default
- `AppConfig.rate_limit_window` default
- `AppConfig.from_env()` environment fallbacks
- `AppConfig.validate()` validation checks
- `RotatingFileHandler` configuration

#### 6. BUG-L06: Unused Import Cleanup
**Files Modified:**
- `job_manager.py` - Removed unused `json` import and `Callable` from typing
- `diagnostic_export.py` - Removed unused `timedelta`, `Pattern`, `Callable` imports
- `core.py` - Removed unused `os`, `Set`, `Any` imports

### Bug Tracker Updates

| Priority | Open | Fixed | Total |
|----------|------|-------|-------|
| 🔴 Critical | 0 | 7 | 7 |
| 🟡 Medium | 0 | 11 | 11 |
| 🟢 Low | 1 | 7 | 8 |

**Remaining Open:** BUG-L02 (Missing type hints) - marked as ongoing/gradual improvement

### Testing Notes
- All Python files verified for syntax after import removal
- Console log prefixes verified with grep
- Constants verified to reference correctly in code

### Key Code Patterns

**Named Constants Pattern:**
```python
# Before (magic numbers)
max_content_length: int = 50 * 1024 * 1024
if self.max_content_length > 500 * 1024 * 1024:

# After (named constants)
max_content_length: int = DEFAULT_MAX_UPLOAD_BYTES
if self.max_content_length > MAX_SAFE_UPLOAD_BYTES:
```

**Console Log Prefix Pattern:**
```javascript
// Before (inconsistent)
console.log('[HV UI] Initializing...');
console.log('[Portfolio] Opening...');

// After (standardized)
console.log('[TWR HyperlinkValidator] Initializing...');
console.log('[TWR Portfolio] Opening...');
```

---

## Session: 2026-02-01 - Document Type Profiles & First-Time Setup

### Version: v3.0.115 → v3.0.116

### Summary
Implemented customizable Document Type Profiles allowing users to configure which quality checks are performed for each document type (PrOP, PAL, FGOST, SOW). Added a first-time user prompt that guides new users to configure their profiles on initial app launch. Custom profiles persist in localStorage across sessions.

### Changes Made

#### 1. Document Profiles Settings Tab
**Files Modified:**
- `templates/index.html` (lines ~1639, 1712-1850)
- `static/js/app.js` (lines ~7590-7930)
- `static/css/features/roles-studio.css` (lines ~3140-3290)

**Functionality:**
- New "Document Profiles" tab in Settings modal
- Profile selector buttons: PrOP, PAL, FGOST, SOW
- Profile description showing purpose of each document type
- Checker grid with 6 categories (~35 checkboxes):
  - Writing Quality (Passive Voice, Weak Language, Wordy Phrases, etc.)
  - Grammar & Spelling (Spelling, Grammar, Punctuation, etc.)
  - Technical Writing (Acronyms, Requirements Language, TBD/TBR, etc.)
  - Clarity (Ambiguous Pronouns, Hedging, Weasel Words, etc.)
  - Document Structure (Document Structure, References, Hyperlinks, etc.)
  - Standards & Other (MIL-STD, DO-178, Accessibility, Roles, etc.)
- Action buttons: Select All, Clear All, Reset to Default
- Auto-save on checkbox change

**Default Profiles:**
| Profile | Focus | Key Checks |
|---------|-------|------------|
| PrOP | Process clarity & step-by-step instructions | Passive Voice, Weak Language, Requirements, Roles, Structure, Lists |
| PAL | Templates & assets - grammar focus | Spelling, Grammar, Punctuation, Structure, References, Hyperlinks |
| FGOST | Decision gates - requirements & completeness | Requirements, TBD, Roles, Testability, Escape Clauses |
| SOW | Contract-focused legal/technical clarity | Requirements, Passive Voice, Escape Clauses, Acronyms, Units |

#### 2. localStorage Persistence
**Files Modified:**
- `static/js/app.js` (lines ~7630-7680)

**Storage Keys:**
- `twr_document_profiles` - Stores customized profile configurations
- `twr_profiles_setup_seen` - Tracks if first-time prompt was shown

**Functions Added:**
- `getCustomProfiles()` - Retrieves custom profiles merged with defaults
- `saveCustomProfile(profileId, checks)` - Saves profile to localStorage
- `resetProfileToDefault(profileId)` - Resets single profile to default

#### 3. applyPreset Integration
**Files Modified:**
- `static/js/app.js` (lines ~3213-3295)

**Functionality:**
- `applyPreset()` now checks for custom profiles before using defaults
- When clicking PrOP, PAL, FGOST, or SOW buttons in sidebar, custom profiles are applied
- Falls back to hardcoded defaults if no custom profile exists
- Console logging: `[TWR] Applied custom profile: pal (10 checks)`

#### 4. First-Time User Prompt
**Files Modified:**
- `static/js/app.js` (lines ~7825-7930)

**Functionality:**
- `checkFirstTimeProfileSetup()` - Called on DOMContentLoaded
- Shows welcome modal if:
  - User has NOT seen prompt before (`twr_profiles_setup_seen` not set)
  - User has NOT already configured profiles (`twr_document_profiles` not set)
- Modal appears 1.5 seconds after page load

**Modal Contents:**
- Header: "Configure Document Profiles" with settings icon
- File-check icon visual
- Welcome text explaining customization options
- Document type badges: PrOP, PAL, FGOST, SOW
- Note about persistence across sessions
- Two buttons:
  - "Maybe Later" - Dismisses, sets flag, won't show again
  - "Configure Now" - Opens Settings → Document Profiles tab

**Functions Added:**
- `showProfileSetupPrompt()` - Creates and displays the modal
- `closeProfileSetupModal()` - Closes the modal
- `openSettingsToProfilesTab()` - Opens Settings and switches to Profiles tab

#### 5. CSS Styling
**Files Modified:**
- `static/css/features/roles-studio.css` (lines ~3140-3290)

**Classes Added:**
```css
.profiles-header
.profile-selector-settings
.profile-btn-settings, .profile-btn-settings.active
.profile-description
.checker-grid-container
.checker-grid-header, .checker-grid-actions
.checker-grid
.checker-category, .checker-category-header
.checker-option
.profile-save-status
```

**Design:**
- Consistent with existing Settings styling
- Profile buttons with accent highlight when active
- Description box with left border accent
- Grid layout for checker categories (auto-fit, minmax 200px)
- Dark mode support via CSS variables

### Data Flow

```
First-time user opens app
    → checkFirstTimeProfileSetup() called after 1.5s delay
    → No twr_profiles_setup_seen or twr_document_profiles in localStorage
    → showProfileSetupPrompt() displays welcome modal

User clicks "Configure Now"
    → localStorage.setItem('twr_profiles_setup_seen', 'true')
    → closeProfileSetupModal()
    → openSettingsToProfilesTab()
    → Settings modal opens to Document Profiles tab

User modifies checkbox in profile grid
    → change event fires on #profile-checker-grid
    → getChecksFromGrid() collects all checked items
    → saveCustomProfile(currentSettingsProfile, checks)
    → localStorage.setItem('twr_document_profiles', JSON.stringify(profiles))

User clicks PAL button in sidebar
    → applyPreset('pal') called
    → getCustomProfiles() checks localStorage
    → Custom PAL checks array found
    → Checkboxes updated to match custom profile
```

### Testing Notes
- Verified first-time prompt appears on fresh localStorage
- Verified "Configure Now" opens Settings → Document Profiles tab
- Verified "Maybe Later" dismisses and sets flag
- Verified prompt doesn't reappear after dismissal
- Verified custom profile saves to localStorage on checkbox change
- Verified PAL button uses custom profile (added passive_voice, verified it appears)
- Verified persistence across page reloads

### Key Code Patterns

**First-Time Detection:**
```javascript
function checkFirstTimeProfileSetup() {
    const hasSeenPrompt = localStorage.getItem(PROFILES_SETUP_SEEN_KEY);
    const hasCustomProfiles = localStorage.getItem(PROFILES_STORAGE_KEY);

    if (hasSeenPrompt || hasCustomProfiles) {
        return; // Skip if already seen or configured
    }

    setTimeout(() => showProfileSetupPrompt(), 1500);
}
```

**Custom Profile Application:**
```javascript
// In applyPreset()
const customizablePresets = ['prop', 'pal', 'fgost', 'sow'];
if (customizablePresets.includes(preset) && typeof window.getCustomProfiles === 'function') {
    const profiles = window.getCustomProfiles();
    if (profiles[preset]?.checks) {
        checkboxes.forEach(cb => cb.checked = false);
        profiles[preset].checks.forEach(c => {
            document.querySelector(`[data-checker="${c}"]`)?.checked = true;
        });
        return; // Skip default preset
    }
}
```

### Known Issues / Future Improvements
- Could add profile import/export functionality
- Could add profile sharing between users
- Could add profile templates beyond the 4 document types

---

## Session: 2026-02-01 - Persistent Link Exclusions & Scan History

### Version: v3.0.122

### Summary
Added persistent storage for URL exclusions and scan history in the Hyperlink Validator. Exclusions now persist between sessions via SQLite database, and historical scans are recorded with summary statistics. Created a new "Link History" modal accessible from the top navigation.

### Changes Made

#### 1. New Backend Storage Module
**Files Created:**
- `hyperlink_validator/storage.py`

**Functionality:**
- SQLite-backed persistent storage using existing `scan_history.db`
- `StoredExclusion` dataclass for exclusion rules
- `LinkScanRecord` dataclass for scan history entries
- `HyperlinkValidatorStorage` class with full CRUD operations:
  - `add_exclusion()`, `get_all_exclusions()`, `update_exclusion()`, `delete_exclusion()`
  - `record_scan()`, `get_recent_scans()`, `get_scan_by_id()`, `delete_scan()`
  - `get_exclusion_stats()`, `get_scan_stats()`, `clear_old_scans()`
- Database tables: `hyperlink_exclusions`, `link_scan_history`

#### 2. API Endpoints for Exclusions & History
**Files Modified:**
- `hyperlink_validator/routes.py` (~300 lines added)

**New Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/exclusions` | GET | List all exclusions |
| `/exclusions` | POST | Create new exclusion |
| `/exclusions/<id>` | GET | Get single exclusion |
| `/exclusions/<id>` | PATCH | Update exclusion |
| `/exclusions/<id>` | DELETE | Delete exclusion |
| `/exclusions/stats` | GET | Exclusion statistics |
| `/history` | GET | List scan history |
| `/history/<id>` | GET | Get single scan with results |
| `/history/<id>` | DELETE | Delete scan record |
| `/history/stats` | GET | Scan statistics |
| `/history/record` | POST | Record new scan |
| `/history/clear` | POST | Clear old records |

#### 3. Link History UI Module
**Files Created:**
- `static/js/features/link-history.js`
- `static/css/features/link-history.css`

**Functionality:**
- Full-screen modal with two tabs: Exclusions and Scan History
- **Exclusions Tab:**
  - Add new exclusion form (pattern, match type, reason, treat as valid)
  - Match types: contains, exact, prefix, suffix, regex
  - Table showing all exclusions with enable/disable toggle and delete
  - Statistics bar (total, active, hit count)
- **Scans Tab:**
  - Table showing recent scans with date, source, URL count, working/broken stats
  - View details and delete actions
  - Clear old history (with days-to-keep prompt)
  - Statistics bar (total scans, URLs scanned, avg success rate)

**CSS Design:**
- Consistent with Portfolio modal styling
- Dark mode support via CSS variables
- Responsive table layouts
- Badge styling for match types and status indicators

#### 4. State Management Integration
**Files Modified:**
- `static/js/features/hyperlink-validator-state.js`

**New Methods Added:**
- `loadExclusionsFromDatabase()` - Loads exclusions from API on init, falls back to localStorage
- `setExclusions(exclusions)` - Syncs exclusions from LinkHistory module
- `recordScanToHistory(sourceType, sourceName, results, summary)` - Records completed scans to persistent storage

**Changes:**
- `init()` now calls `loadExclusionsFromDatabase()` instead of just localStorage
- After validation completes, automatically calls `recordScanToHistory()`
- Added both new methods to public API

#### 5. Navigation Integration
**Files Modified:**
- `templates/index.html` - Added "Links" nav button, CSS/JS loading
- `static/js/history-fixes.js` - Added click handler for nav button

**Navigation Button:**
```html
<button class="top-nav-link" id="nav-link-history" title="Link exclusions & scan history">
    <i data-lucide="link-2-off"></i>
    <span>Links</span>
</button>
```

### Data Flow

```
User adds exclusion in Link History modal
    → POST /api/hyperlink-validator/exclusions
    → Stored in SQLite (hyperlink_exclusions table)
    → syncWithValidator() updates HyperlinkValidatorState

Validator initializes
    → HyperlinkValidatorState.init()
    → loadExclusionsFromDatabase()
    → Fetch from /api/hyperlink-validator/exclusions
    → Exclusions applied to validation

Validation completes
    → recordScanToHistory() called
    → POST /api/hyperlink-validator/history/record
    → Stored in SQLite (link_scan_history table)
    → LinkHistory.refreshScans() updates modal if open
```

### Database Schema

**hyperlink_exclusions:**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| pattern | TEXT | URL pattern to match |
| match_type | TEXT | contains/exact/prefix/suffix/regex |
| reason | TEXT | Why excluded |
| treat_as_valid | INTEGER | 1=show as valid, 0=skip |
| is_active | INTEGER | 1=active, 0=disabled |
| created_at | TEXT | ISO timestamp |
| created_by | TEXT | Optional user identifier |
| hit_count | INTEGER | Times matched |

**link_scan_history:**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| scan_time | TEXT | ISO timestamp |
| source_type | TEXT | paste/file/excel/docx |
| source_name | TEXT | Filename if applicable |
| total_urls | INTEGER | URLs scanned |
| working | INTEGER | Working count |
| broken | INTEGER | Broken count |
| redirect | INTEGER | Redirect count |
| timeout | INTEGER | Timeout count |
| blocked | INTEGER | Blocked count |
| unknown | INTEGER | Unknown count |
| validation_mode | TEXT | Mode used |
| results_json | TEXT | Full results (JSON blob) |

### Testing Notes
- Storage module tested with Python syntax validation
- Flask app loads successfully with blueprint registered
- All JavaScript files have valid syntax
- Full integration verified: nav button → modal → API → database

### Known Issues / Future Improvements
- Could add export of exclusion rules
- Could add import from JSON/CSV
- Could add bulk exclusion management

---

## Session: 2026-02-01 - Portfolio "Open in Review" Fix & Hyperlinks Enhancements

### Version: v3.0.121

### Summary
Fixed the Portfolio module's "Open in Review" button which wasn't properly loading documents into the Review view, and enhanced the Hyperlinks panel to be responsive and clickable for manual verification.

### Changes Made

#### 1. Portfolio "Open in Review" Button Fix
**Files Modified:**
- `static/js/features/portfolio.js` (lines ~855-875)

**Problem:**
- Clicking "Open in Review" in the Portfolio's document preview panel would close the modal and show the issues table, but the main content area still displayed "Drop a document to begin" placeholder instead of the document content.

**Root Cause:**
- The `openDocument()` function was missing critical calls to hide the empty state and show the stats bar.

**Fix Applied:**
```javascript
// Hide empty state and show stats bar (critical for document display)
const emptyState = document.getElementById('empty-state');
if (emptyState) {
    emptyState.style.display = 'none';
}
const statsBar = document.getElementById('stats-bar');
if (statsBar) {
    statsBar.style.display = '';
}
```

**Result:**
- Document now fully loads with stats bar, analytics, severity counts, and issues table all displaying correctly.

#### 2. Responsive Hyperlinks Panel
**Files Modified:**
- `static/css/components.css` (lines ~4907-5003)

**Changes:**
- Changed `.hyperlink-list` max-height from fixed `300px` to responsive `50vh` (50% viewport height)
- Changed collapsed state max-height from `150px` to `25vh`
- Removed fixed `max-width: 200px` from `.hyperlink-text`, added `min-width: 0` for flex shrinking
- Changed `.hyperlink-error` from `flex-shrink: 0` with `max-width: 150px` to `flex: 1` with `min-width: 0`
- Added `min-width: 0` to `.hyperlink-item` for proper flex child shrinking

**Result:**
- Hyperlinks panel now expands/contracts with window size instead of being fixed.

#### 3. Clickable Hyperlinks for Manual Verification
**Files Modified:**
- `static/js/app.js` (lines ~1925-1950)
- `static/css/components.css` (lines ~5005-5060)

**JavaScript Changes:**
- Added `clickable` class and `data-url` attribute to hyperlink rows
- Added external-link icon (`<i data-lucide="external-link">`) to each row
- Added click event handlers that open URLs in new tabs with `window.open(url, '_blank', 'noopener,noreferrer')`

**CSS Classes Added:**
```css
/* Clickable hyperlink rows */
.hyperlink-row.clickable {
    cursor: pointer;
    transition: background var(--duration-fast), transform var(--duration-fast);
}

.hyperlink-row.clickable:hover {
    background: var(--bg-hover);
    transform: translateX(2px);
}

.hyperlink-row .open-link-icon {
    opacity: 0;
    transition: opacity var(--duration-fast);
    margin-left: auto;
}

.hyperlink-row.clickable:hover .open-link-icon {
    opacity: 1;
    color: var(--accent);
}
```

**Result:**
- Users can now click any hyperlink in the panel to open it in a new tab
- Visual feedback: row highlights and shifts on hover, external link icon appears
- Enables manual verification of link status

#### 4. Test Document Created
**Files Created:**
- `hyperlink_test.docx`

**Contents:**
- Working links: Google, GitHub, Anthropic, Python Documentation
- Test/broken links: non-existent domain, httpstat.us/404, httpstat.us/500
- Sample text for document structure testing

### Testing Notes
- Tested Portfolio "Open in Review" flow end-to-end
- Verified stats bar displays after loading from Portfolio
- Verified empty state is hidden
- Verified issues table shows correctly
- CSS changes verified for responsive behavior

### Key Code Patterns

**Portfolio Document Loading Pattern:**
```javascript
// After API call succeeds and state is updated:
// 1. Update UI components
updateResultsUI(results);
updateSeverityCounts(results.by_severity || {});
updateCategoryFilters(results.by_category || {});

// 2. Enable filters
document.querySelectorAll('.sev-toggle').forEach(btn => btn.classList.add('active'));
applyUnifiedFilters();

// 3. Render issues
renderIssuesList();

// 4. Critical: Toggle visibility
document.getElementById('empty-state').style.display = 'none';
document.getElementById('stats-bar').style.display = '';

// 5. Show analytics
showAnalyticsAccordion(results);
```

### Known Issues / Future Improvements
- None currently identified

---

## Session: 2026-02-01 - Document Filter & Help Documentation Overhaul

### Version: v3.0.119

### Summary
Fixed the document filter dropdown in Roles Studio to properly filter roles by document, and comprehensively updated the Help & Documentation system with detailed coverage of all features including Fix Assistant v2, Hyperlink Health, Batch Processing, and expanded technical documentation.

### Changes Made

#### 1. Document Filter Dropdown Fix
**Files Modified:**
- `static/js/roles-tabs-fix.js` (lines ~102, 305-327, 333-370, 400-402, 619-620)

**Functionality:**
- Fixed dropdown population from scan history
- Added `filterRolesByDocument()` function to filter roles by source document
- Added `filterHistoryByDocument()` function for scan history filtering
- Fixed CSS selector bug: changed `.roles-nav-btn.active` to `.roles-nav-item.active`
- Filter now updates Overview stats, Responsibility Distribution chart, and Top Roles list
- Filter indicator shows "Filtered by: [document]" when active
- Restores previous filter selection when re-opening modal

**Bug Fixed:**
- Dropdown change event wasn't triggering re-render due to wrong CSS selector

#### 2. Help Modal Styling (3/4 Screen with Opaque Backdrop)
**Files Modified:**
- `static/css/modals.css` (lines ~832-880)
- `static/css/features/statement-forge.css` (lines ~1494-1555)

**Functionality:**
- Added semi-transparent backdrop (`rgba(0, 0, 0, 0.7)`) to main Help modal
- Set Help modal to 85vw width, 80vh height (3/4 screen)
- Added same styling to Statement Forge Help modal (80vw, 75vh)
- Added responsive breakpoints for tablet/mobile
- Matches Roles Studio modal styling pattern

#### 3. Comprehensive Help Documentation Update
**Files Modified:**
- `static/js/help-docs.js` (major updates throughout, version bumped to 3.0.119)

**New Navigation Sections Added:**
- Fix Assistant (fix-overview, fix-workflow, fix-learning, fix-export)
- Hyperlink Health (hyperlink-overview, hyperlink-validation, hyperlink-status)
- Batch Processing (batch-overview, batch-queue, batch-results)

**Sections Significantly Updated:**

1. **Welcome Section** - Complete overhaul:
   - "Enterprise-Grade Capabilities" callout with 94.7% precision stats
   - 8 Core Capabilities feature cards
   - Supported file formats section
   - 6 "Where to Start" navigation cards
   - Pro Tips with keyboard shortcuts

2. **Roles & Responsibilities Studio** - Expanded with:
   - Performance validation stats (94.7% precision, 92.3% F1)
   - 8 Key Features cards (Overview Dashboard, Relationship Graph, RACI Matrix, Role-Doc Matrix, Adjudication Workflow, Document Filtering, Role Dictionary, Export Options)
   - Studio Tabs table (Analysis/Workflow/Management sections)
   - Typical Workflow guide (7 steps)
   - "Why Role Extraction Matters" benefits list
   - Navigation to all sub-sections

3. **Statement Forge** - Comprehensive documentation:
   - 8 Key Features cards (Smart Extraction, Actor Detection, Object Extraction, Statement Types, Inline Editing, Merge & Split, Auto-Numbering, Multiple Exports)
   - Workflow guide (7 steps)
   - Keyboard shortcuts table
   - Session-based warning callout

4. **Fix Assistant v2** - New complete section:
   - Overview with confidence scoring explanation
   - 8 Key Features cards
   - Keyboard shortcuts table
   - Review Workflow guide with confidence levels table
   - Bulk Actions documentation
   - Pattern Learning explanation
   - Export Options (Word with tracked changes, PDF report, JSON)

5. **Hyperlink Health** - New complete section:
   - What Gets Checked list
   - Validation Results status table (Valid/Redirect/Broken/SSL Error/Timeout/Skipped)
   - URL Validation process
   - Validation Settings
   - HTTP Status Codes reference (2xx, 3xx, 4xx, 5xx)

6. **Batch Processing** - New complete section:
   - Adding Documents workflow
   - Queue Management features
   - Queue States table
   - Results View documentation
   - Export Options
   - Cross-Document Analysis tips

7. **Quality Checkers Overview** - Expanded with:
   - Complete Checker List table (13 modules)
   - How Checkers Work process (6 steps)
   - Severity Levels table with color coding
   - Configuring Checkers guide
   - Philosophy section

### CSS Classes Added
```css
/* Help Modal Styling */
#modal-help.active { background: rgba(0, 0, 0, 0.7) !important; }
#modal-help .modal-content { width: 85vw; max-width: 1400px; height: 80vh; }

/* Statement Forge Help Modal */
#modal-sf-help.active { background: rgba(0, 0, 0, 0.7) !important; }
#modal-sf-help .modal-content { width: 80vw; max-width: 1200px; height: 75vh; }
```

### Testing Notes
- Tested document filter with nasa_test.docx - correctly filters 16 roles to 8
- Verified filter resets properly when selecting "All Documents"
- Confirmed Help modal renders at 3/4 screen size
- Verified all new documentation sections render correctly
- No JavaScript console errors

### Key Code Patterns

**Document Filter Implementation:**
```javascript
// Filter roles by document filename
function filterRolesByDocument(roles, documentFilter) {
    if (!documentFilter || documentFilter === 'all') return roles;
    return roles.filter(role => {
        if (role.documents && Array.isArray(role.documents)) {
            return role.documents.includes(documentFilter);
        }
        return false;
    });
}

// Change event triggers re-render
filterSelect.addEventListener('change', (e) => {
    currentDocumentFilter = e.target.value;
    const activeTab = document.querySelector('.roles-nav-item.active');
    if (activeTab) switchToTab(activeTab.dataset.tab);
});
```

### Known Issues / Future Improvements
- None currently identified

---

## Session: 2026-02-01 - Issues by Section 3D Carousel

### Version: v3.0.120

### Summary
Implemented a 3D rotating carousel for the "Issues by Section" panel in Document Analytics, replacing the previous flat/scattered layouts.

### Changes Made

#### New Feature: 3D Carousel for Issues by Section
**Files Modified:**
- `static/css/charts.css` (lines ~975-1165)
- `static/js/ui/renderers.js` (lines ~1000-1140)

**Functionality:**
- Boxes arranged in a horizontal arc with 3D perspective
- Center box is largest, side boxes scale down and recede
- Supports drag-to-spin (continuous rotation while dragging)
- Slider control for navigation
- Touch support for mobile devices
- Click on a box to filter issues to that section

**Visual Design:**
- White/light background with subtle border
- Box size: 75x80px
- Color-coded borders based on issue density:
  - Gray (`#d1d5db`) - No issues
  - Green (`#10b981`) - Low density
  - Yellow/Orange (`#f59e0b`) - Medium density
  - Red (`#ef4444`) - High density
- Section labels (§1, §2, etc.) at top of each box
- Issue count prominently displayed (26px font)
- Paragraph range at bottom (e.g., ¶1-32)

**CSS Classes Added:**
- `.section-carousel-wrapper` - Main container with perspective
- `.section-carousel` - Carousel viewport
- `.carousel-track` - 3D transform container
- `.carousel-block` - Individual section boxes
- `.block-cube`, `.cube-front` - Box styling
- `.carousel-controls`, `.carousel-slider` - Navigation slider
- `.density-none`, `.density-low`, `.density-medium`, `.density-high` - Color variants

### Iterations & Lessons Learned

1. **Started with dark theme** - Initially implemented with dark background and glowing borders (like reference image), but switched to white background to match app aesthetic.

2. **Scattered polaroid look rejected** - User feedback: "this just looks like a mess" - clean rotating boxes preferred over scattered photo gallery style.

3. **Continuous spin implementation** - Changed from discrete drag (move X pixels = change 1 section) to continuous spin (hold and drag to keep spinning). Key code pattern:
   ```javascript
   function startSpin(direction) {
       spinInterval = setInterval(() => {
           currentIndex = (currentIndex + direction + numBlocks) % numBlocks;
           positionBlocks(currentIndex);
       }, 150); // Spin speed
   }
   ```

4. **Vertical centering** - Added `justify-content: center` to parent containers and `flex: 1` to carousel wrapper to dynamically center between header and legend.

5. **Size adjustments** - Increased box size from 60x65px to 75x80px based on user feedback for better readability.

### Testing Notes
- Tested with NASA document (161 paragraphs, 718 issues)
- Carousel correctly divides into 5 sections (~32 paragraphs each)
- Issue distribution displayed: §1: 16, §2: 14, §3: 55, §4: 122, §5: 154

### Known Issues / Future Improvements
- None currently identified

---

## Template for New Sessions

```markdown
## Session: YYYY-MM-DD - Brief Description

### Version: v3.0.XXX

### Summary
One paragraph describing what was accomplished.

### Changes Made

#### Feature/Fix Name
**Files Modified:**
- `path/to/file.py` (lines X-Y)

**Functionality:**
- Bullet points describing what it does

**Visual Design:** (if applicable)
- Design specifications

### Iterations & Lessons Learned
1. What approaches were tried
2. What worked/didn't work
3. Key code patterns discovered

### Testing Notes
- How it was tested
- Edge cases considered

### Known Issues / Future Improvements
- Any remaining work
```

---

## Quick Reference: Key Files

| Feature | Primary Files |
|---------|--------------|
| Link History Storage | `hyperlink_validator/storage.py` |
| Link History UI | `static/js/features/link-history.js`, `static/css/features/link-history.css` |
| Hyperlink Validator State | `static/js/features/hyperlink-validator-state.js` |
| Hyperlink Validator Routes | `hyperlink_validator/routes.py` |
| Carousel CSS | `static/css/charts.css` (~975-1165) |
| Carousel JS | `static/js/ui/renderers.js` (~1000-1140) |
| Analytics Panel HTML | `templates/index.html` (~622-676) |
| App Config | `config.json` |
| Main Flask App | `app.py` |
| Document Parsing | `core.py` |

---

## Version History Quick Reference

| Version | Date | Key Changes |
|---------|------|-------------|
| v3.0.124 | 2026-02-01 | Hyperlink Validator 2-mode simplification, HEAD/GET fallback, Headless browser rescan |
| v3.0.122 | 2026-02-01 | Persistent Link Exclusions & Scan History |
| v3.0.121 | 2026-02-01 | Portfolio "Open in Review" fix, Responsive/Clickable Hyperlinks |
| v3.0.120 | 2026-02-01 | 3D Carousel for Issues by Section |
| v3.0.119 | 2026-02-01 | Document Filter fix, Help Documentation overhaul |
| v3.0.118 | 2026-01-29 | Document filter with filtering (selector bug) |
| v3.0.117 | 2026-01-29 | Document filter dropdown population |
| v3.0.116 | 2026-02-01 | Memory fixes, session cleanup, localStorage collision fix |
| v3.0.115 | 2026-02-01 | Document Type Profiles, First-time setup prompt |
| v3.0.114 | 2026-01-28 | Combined Analytics Panel (3 columns) |
| v3.0.113 | 2026-01-28 | Fix Assistant tables/headings bug fix |
