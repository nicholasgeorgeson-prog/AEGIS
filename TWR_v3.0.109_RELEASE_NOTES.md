# AEGIS v3.0.109 Release Notes

**Release Date:** January 28, 2026  
**Codename:** Bug Squash Complete

## Overview

Version 3.0.109 is a comprehensive bug fix release that addresses **all 14 issues** identified during v3.0.108 testing. This release merges fixes from multiple parallel development chats into a single, consistent codebase.

## All Issues Fixed ✅

| Issue | Description | Status |
|-------|-------------|--------|
| #2 | Hyperlinks not extracted from DOCX field codes | ✅ Fixed |
| #3 | Acronym highlighting false positives | ✅ Fixed |
| #4 | Fix Assistant Premium not working | ✅ Fixed |
| #5 | Statement Forge "No document loaded" | ✅ Fixed |
| #6 | Scan history missing API endpoints | ✅ Fixed |
| #7 | Triage mode documentId error | ✅ Fixed |
| #8 | Document filter not populating | ✅ Fixed |
| #9 | Role-Document Matrix stuck loading | ✅ Fixed |
| #10 | Export modal badge overflow | ✅ Fixed |
| #11 | Comment placement text matching | ✅ Fixed |
| #12 | Version history incomplete | ✅ Fixed |
| #13 | Updater rollback not working | ✅ Fixed |
| #14 | "No updates" empty state styling | ✅ Fixed |
| #1, #15 | Batch modal & logo (in base) | ✅ Fixed |

## Detailed Fixes

### Issue #2: Hyperlinks Not Extracted
**Problem:** DOCX hyperlinks stored as field codes weren't being detected.  
**Fix:** Added extraction for `<w:fldSimple>` and `<w:instrText>` HYPERLINK patterns.

### Issue #3: Acronym False Positives
**Problem:** "NDA" was highlighted inside "staNDArds".  
**Fix:** Uses word boundary regex (`\b`) for exact word matching only.

### Issue #4: Fix Assistant Premium
**Problem:** Close button, navigation, and action buttons weren't working.  
**Fix:** Complete reimplementation with proper event binding, keyboard shortcuts (A/R/S/arrows/Escape), progress tracking, and visual feedback.

### Issue #5: Statement Forge "No document loaded"
**Problem:** Modal showed "No document loaded" even when document was present.  
**Fix:** `updateDocumentStatus()` now uses same state checks as `extractStatements()`.

### Issue #6: Scan History Endpoints
**Problem:** `/stats`, `/clear`, `/recall` endpoints missing.  
**Fix:** Added all three endpoints to app.py.

### Issue #7: Triage Mode Error
**Problem:** "Document must be saved to history" error on fresh reviews.  
**Fix:** `State.documentId` now generated after fresh review, not just history restore.

### Issue #8: Document Filter Empty
**Problem:** Document filter dropdown wasn't populating.  
**Fix:** Now loads from scan history correctly.

### Issue #9: Role-Document Matrix
**Problem:** Matrix stuck on "Loading..." indefinitely.  
**Fix:** Improved response validation with null/undefined handling and retry button.

### Issue #10: Export Modal Badges
**Problem:** Status badges overflowed their containers.  
**Fix:** Added flex-wrap, max-width, and text-overflow: ellipsis.

### Issue #11: Comment Placement
**Problem:** Comments attached to wrong text due to quote/whitespace mismatches.  
**Fix:** Multi-strategy matching: exact → normalized (smart quotes → straight) → fuzzy.

### Issue #12: Version History
**Problem:** Missing versions in Help changelog.  
**Fix:** Added v3.0.103-v3.0.109 entries to help-docs.js.

### Issue #13: Updater Rollback
**Problem:** Wrong endpoint (`/restore` vs `/rollback`), button state not updating.  
**Fix:** Corrected endpoint, added button enable/disable based on backup availability.

### Issue #14: "No Updates" Styling
**Problem:** Empty state had no styling.  
**Fix:** Centered layout with checkmark icon and proper colors.

## Files Modified

| File | Issues |
|------|--------|
| `app.py` | #6 |
| `static/js/app.js` | #4, #5, #7, #8, #13 |
| `static/js/ui/renderers.js` | #3 |
| `static/js/features/document-viewer.js` | #3 |
| `static/js/features/roles.js` | #9 |
| `static/js/help-docs.js` | #12 |
| `static/css/features/fix-assistant.css` | #4 |
| `static/css/modals.css` | #10 |
| `static/css/components.css` | #14 |
| `comprehensive_hyperlink_checker.py` | #2 |
| `statement_forge/extractor.py` | #5 |
| `comment_inserter.py` | #11 |
| `templates/index.html` | #1, #15 |

## Upgrade Notes

This is a drop-in replacement for v3.0.108. No database migrations or configuration changes required.

---

*AEGIS v3.0.109 - All Issues Resolved*
