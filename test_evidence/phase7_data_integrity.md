# Phase 7: Deep Data Integrity Verification

**Date:** 2026-02-13
**AEGIS Version:** 4.6.2
**Database:** scan_history.db
**Server:** localhost:5050
**Tester:** Claude Opus 4.6 (automated)

---

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Scan count | BUG FOUND | Landing page shows 50/71 due to default API limit |
| Document count | BUG FOUND | Landing page shows 37/45 (same root cause) |
| Role dictionary count | PASS | DB=1056, API=1056, all screens agree |
| Statement count | PASS | DB=1404, API=1404, consistent everywhere |
| Average score | BUG FOUND | Landing page shows 23, actual is 35.5 |
| Checker count (84) | INACCURATE | Hardcoded 84, actual is 40 base + 8 NLP = 48 |
| Metrics Dashboard API | PASS (minor) | All values match DB except avg_word_count (documented difference) |
| Scan History Stats API | BUG FOUND | `last_scan` always null (wrong field name) |
| Cross-screen consistency | BUG FOUND | 3 metrics differ between Landing Page and Metrics Dashboard |
| Database integrity | DATA ISSUE | 4 orphaned NULL role_id entries in role_function_tags |

**Bugs Found: 5** | **Data Issues: 2** | **Passing Checks: 4**

---

## 1. Scan Count Verification

### Database (Ground Truth)
```sql
SELECT COUNT(*) FROM scans;
-- Result: 71
```

### API: `/api/scan-history` (default, no limit param)
- Returns: **50 scans** (default limit=50 in `scan_history.py:get_scan_history()`)
- The API route at `app.py:4429` defaults: `limit = int(request.args.get('limit', 50))`

### API: `/api/scan-history?limit=9999`
- Returns: **71 scans** -- matches DB

### API: `/api/scan-history/stats`
- Returns: `total_scans: 71` -- matches DB (uses `limit=1000` internally)

### API: `/api/metrics/dashboard` overview
- Returns: `total_scans: 71` -- matches DB

### Landing Page (computed client-side)
- Calls `/api/scan-history` WITHOUT a limit parameter
- Receives only 50 of 71 scans
- **Displays: 50** (should be 71)

### BUG: Landing page undercounts scans
- **Root cause:** `landing-page.js:187` calls `fetch('/api/scan-history')` without `?limit=9999`
- **Impact:** Landing page "Total Scans" metric card shows 50 instead of 71
- **Fix:** Add `?limit=9999` to the fetch URL, or use `/api/scan-history/stats` for totals

---

## 2. Document Count Verification

### Database (Ground Truth)
```sql
SELECT COUNT(*) FROM documents;
-- Result: 45

SELECT COUNT(DISTINCT filename) FROM documents;
-- Result: 45
```

### API: `/api/scan-history?limit=9999` unique filenames
- Result: **45** -- matches DB

### API: `/api/scan-history/stats`
- Returns: `unique_documents: 45` -- matches DB

### API: `/api/metrics/dashboard` overview
- Returns: `total_documents: 45` -- matches DB

### Landing Page (computed client-side)
- Computes `new Set(scans.map(s => s.filename)).size` from default 50-record response
- **Displays: 37** (should be 45)

### BUG: Landing page undercounts documents
- **Root cause:** Same as scan count -- only 50 scans returned, covering only 37 unique filenames
- **Impact:** Landing page "Total Documents" metric card shows 37 instead of 45

---

## 3. Role Dictionary Count Verification

### Database (Ground Truth)
```sql
SELECT COUNT(*) FROM role_dictionary;
-- Result: 1056

SELECT COUNT(*) FROM role_dictionary WHERE is_active=1;
-- Result: 1056 (all active)

SELECT COUNT(*) FROM role_dictionary WHERE is_active=0;
-- Result: 0

SELECT COUNT(*) FROM role_dictionary WHERE is_deliverable=1;
-- Result: 1
```

### API: `/api/roles/dictionary`
```json
{
  "success": true,
  "data": {
    "roles": [...],  // 1056 items
    "total": 1056
  }
}
```
- `roles` array length: **1056** -- matches DB
- `total` field: **1056** -- matches DB
- Active count from API: **1056** -- matches DB
- Deliverable count from API: **1** -- matches DB

### API: `/api/metrics/dashboard` overview
- Returns: `total_roles: 1056` -- matches DB

### Category Breakdown
| Category | DB | API | Match |
|----------|-----|-----|-------|
| Role | 1047 | 1047 | PASS |
| Tools & Systems | 8 | 8 | PASS |
| Technical | 1 | 1 | PASS |

### Source Breakdown
| Source | DB | API | Match |
|--------|-----|-----|-------|
| sipoc | 1046 | 1046 | PASS |
| adjudication | 7 | 7 | PASS |
| rename | 3 | 3 | PASS |

### PASS: All role dictionary counts are consistent across DB, API, and all screens.

---

## 4. Statement Count Verification

### Database (Ground Truth)
```sql
SELECT COUNT(*) FROM scan_statements;
-- Result: 1404

SELECT COUNT(DISTINCT scan_id) FROM scan_statements;
-- Result: 3 (only 3 scans have statements)
```

### Statement Breakdown by Scan
| Scan ID | Document | Statements |
|---------|----------|------------|
| 156 | NASA_Systems_Engineering_Handbook.pdf | 1350 |
| 154 | PMBOK_Guide_Summary.pdf | 32 |
| 155 | Stanford_Engineering_Robotics_SOP.docx | 22 |

### API: `/api/metrics/dashboard` overview
- Returns: `total_statements: 1404` -- matches DB

### Landing Page (computed client-side)
- Sums `statement_count` from scan history records
- All 3 statement-bearing scans are within the default 50-record window
- **Displays: 1404** -- matches DB

### PASS: Statement counts are consistent.

---

## 5. Average Score Verification

### Database (Ground Truth)
```sql
SELECT AVG(score) FROM scans WHERE score IS NOT NULL;
-- Result: 35.4929577464789

SELECT ROUND(AVG(score), 1) FROM scans WHERE score IS NOT NULL;
-- Result: 35.5

SELECT COUNT(*) FROM scans WHERE score IS NOT NULL;
-- Result: 71 (all scans have scores)
```

### Score Distribution
| Range | Count |
|-------|-------|
| 0-59 (F) | 57 |
| 80-89 (B) | 5 |
| 90-100 (A) | 9 |

### Grade Distribution
| Grade | Count |
|-------|-------|
| F | 57 |
| A | 9 |
| B | 5 |

### API: `/api/metrics/dashboard` overview
- Returns: `avg_score: 35.5` -- matches DB

### Landing Page (computed client-side)
- Computes average from the 50 scans returned by default API call
- Average of those 50 scores: **23** (heavily skewed by the subset)
- **Should be: 36** (rounded from 35.5)

### BUG: Landing page shows wrong average score
- **Root cause:** Average computed from 50 of 71 scans (same pagination bug)
- **Impact:** Shows score of 23 instead of the true average of 35.5 (36 rounded)
- **Note:** The 21 missing scans likely include higher-scoring documents, pulling the truncated average down significantly

---

## 6. Checker Count Verification

### Landing Page Display
- `landing-page.js:124`: `checkerCount: 84` (hardcoded default)
- This value is NEVER updated by `fetchData()` -- it remains 84 always

### Actual Checker Inventory

**Base Checkers (registered in core.py `__init__`):**
1. document_structure
2. heading_consistency
3. numbering
4. passive_voice
5. references
6. table_formatting
7. lists
8. acronyms
9. sentence_length
10. punctuation
11. hyperlinks (ComprehensiveHyperlinkChecker)
12. language (WordLanguageChecker)
13. comparison (DocumentComparisonChecker)
14. images (ImageFigureChecker)
15. roles (RoleChecker)

**Extended v2.2 Checkers (from `extended_checkers.py:get_all_v22_checkers()`):**
16. spelling
17. grammar
18. units
19. number_format
20. terminology
21. tbd
22. redundancy
23. testability
24. atomicity
25. escape_clauses
26. hyphenation
27. serial_comma
28. enhanced_references
29. hedging
30. weasel_words
31. cliches
32. dangling_modifiers
33. run_on_sentences
34. sentence_fragments
35. parallel_structure
36. mil_std
37. do178
38. orphan_headings
39. empty_sections
40. accessibility

**Note:** Extended checkers override base `spelling`, `grammar`, and `hyperlinks` keys, so unique total = **40** (not 41).

**NLP Enhanced Checkers (from `nlp` module, run separately):**
41. Subject-Verb Agreement (Enhanced)
42. Dangling Modifier (Enhanced)
43. Sentence Complexity
44. Grammar (Comprehensive)
45. Spelling (Enhanced)
46. Style (Professional)
47. Tense Consistency
48. Terminology Consistency

### Total: 40 base/extended + 8 NLP = **48 checkers**

### INACCURATE: Hardcoded 84 does not match reality (48)
- **Root cause:** `checkerCount: 84` is a hardcoded constant in `landing-page.js`, never computed from the actual engine
- **Impact:** Landing page footer and metric card both show "84 quality checkers" when only 48 exist
- **Note:** The 84 number may have been an aspirational count or included sub-rules within checkers, but no code path produces this number

---

## 7. Metrics Dashboard API Verification

### Endpoint: `GET /api/metrics/dashboard`

**Note:** The endpoint `/api/metrics/analytics` returns 404. The correct endpoint is `/api/metrics/dashboard`.

### Response Shape
```json
{
  "success": true,
  "data": {
    "overview": { ... },
    "scans": [...],
    "documents": [...],
    "documents_meta": { ... },
    "roles": { ... },
    "statements": { ... },
    "quality": { ... },
    "relationships": { ... },
    "hyperlinks": { ... }
  }
}
```

### Overview Section Verification

| Field | DB Value | API Value | Match |
|-------|----------|-----------|-------|
| total_scans | 71 | 71 | PASS |
| total_documents | 45 | 45 | PASS |
| avg_score | 35.5 | 35.5 | PASS |
| total_roles | 1056 | 1056 | PASS |
| total_statements | 1404 | 1404 | PASS |
| total_issues | 211667 | 211667 | PASS |
| total_word_count | 1494223 | 1494223 | PASS |
| avg_word_count | 21045 (per scan) | 26050 (per document) | DOCUMENTED DIFFERENCE |

### avg_word_count Explanation
- The API computes `AVG(word_count) FROM documents WHERE word_count > 0` = **26050**
- A per-scan average would be `AVG(word_count) FROM scans` = **21045**
- The per-document average is the correct metric (documents can have multiple scans)
- **Status:** Not a bug -- intentional per-document calculation

### Relationships Section
| Field | DB Value | API Value | Match |
|-------|----------|-----------|-------|
| total | 403 | 403 | PASS |
| inherits-from | 396 | 396 | PASS |
| uses-tool | 7 | 7 | PASS |

### PASS (with minor note): Metrics Dashboard API is accurate for all verifiable fields.

---

## 8. Scan History Stats API Verification

### Endpoint: `GET /api/scan-history/stats`

### Response
```json
{
  "success": true,
  "total_scans": 71,
  "unique_documents": 45,
  "last_scan": null
}
```

| Field | DB Value | API Value | Match |
|-------|----------|-----------|-------|
| total_scans | 71 | 71 | PASS |
| unique_documents | 45 | 45 | PASS |
| last_scan | 2026-02-13 02:58:49 | null | BUG |

### BUG: `last_scan` is always null
- **Location:** `app.py:4496`
- **Code:** `last_scan = history[0].get('timestamp') if history else None`
- **Problem:** The scan history records use the key `scan_time`, not `timestamp`
- **Fix:** Change to `history[0].get('scan_time')`
- **Impact:** Any consumer of this API that needs the last scan timestamp gets null

---

## 9. Cross-Screen Consistency

### Comparison Matrix

| Metric | DB (Truth) | Metrics Dashboard | Scan History Stats | Landing Page | Roles Studio |
|--------|------------|-------------------|-------------------|--------------|--------------|
| Total Scans | 71 | 71 | 71 | **50** | N/A |
| Total Documents | 45 | 45 | 45 | **37** | N/A |
| Total Roles | 1056 | 1056 | N/A | 1056 | 1056 |
| Total Statements | 1404 | 1404 | N/A | 1404 | N/A |
| Avg Score | 35.5 | 35.5 | N/A | **23** | N/A |
| Checkers | 48 (actual) | N/A | N/A | **84** (hardcoded) | N/A |
| Last Scan | 2026-02-13 02:58:49 | 2026-02-13 02:58:49 | **null** | N/A | N/A |
| Adjudicated Roles | 0 (no column) | 0 | N/A | **0** (correct but wrong reason) | N/A |
| Deliverable Roles | 1 | 1 | N/A | 1 | N/A |

### Discrepancies Explained

1. **Scan count (50 vs 71):** Landing page calls `/api/scan-history` without limit, gets default 50
2. **Document count (37 vs 45):** Derived from the truncated 50-scan result set
3. **Avg score (23 vs 35.5):** Computed from the biased 50-scan subset
4. **Checker count (84 vs 48):** Hardcoded, never dynamically computed
5. **Last scan (null):** Wrong dictionary key in stats API

### Adjudication Count Note
The landing page counts `adjudication_status === 'adjudicated'` from `/api/roles/dictionary`, but this field does not exist in the API response (the `role_dictionary` table has no `adjudication_status` column). The count is always 0, which happens to match the database (no column = no adjudicated roles), but for the wrong reason. If adjudication tracking is intended, the column and API field need to be added.

---

## 10. Database Integrity Issues

### NULL role_id entries in role_function_tags

```sql
SELECT function_code, COUNT(*) FROM role_function_tags
WHERE role_id IS NULL GROUP BY function_code;
```

| Function Code | NULL Entries |
|---------------|-------------|
| BASELINED | 1 |
| PM | 3 |
| **Total** | **4** |

These 4 orphaned entries have `role_id IS NULL`, meaning they are not associated with any role. This causes the BASELINED function coverage count in the Metrics Dashboard to show 277 instead of the actual 276 roles with BASELINED tags.

### No other orphan issues found
- No orphaned `role_function_tags` entries (tag for deleted role): 0
- No orphaned `role_relationships` entries: 0

---

## Bug Summary

### BUG-1: Landing Page Pagination (MEDIUM severity)
- **Symptom:** Scan count, document count, and average score are wrong on landing page
- **Root cause:** `landing-page.js:187` calls `/api/scan-history` without `?limit=9999`
- **Affected metrics:** Total Scans (50 vs 71), Total Docs (37 vs 45), Avg Score (23 vs 36)
- **Fix:** Either pass `?limit=9999` or use `/api/scan-history/stats` + `/api/metrics/dashboard` for totals

### BUG-2: Hardcoded Checker Count (LOW severity)
- **Symptom:** Landing page shows "84 quality checkers"
- **Root cause:** `landing-page.js:124` hardcodes `checkerCount: 84`, never updated dynamically
- **Actual count:** 48 (40 base/extended + 8 NLP)
- **Fix:** Compute from engine or expose via API endpoint

### BUG-3: Scan History Stats last_scan Always Null (LOW severity)
- **Symptom:** `/api/scan-history/stats` returns `last_scan: null`
- **Root cause:** `app.py:4496` reads `history[0].get('timestamp')` but field is `scan_time`
- **Fix:** Change `'timestamp'` to `'scan_time'`

### BUG-4: Adjudication Status Field Missing (LOW severity)
- **Symptom:** Landing page adjudicated count is always 0
- **Root cause:** `adjudication_status` field does not exist in DB schema or API response
- **Note:** Landing page code at `line 216` filters on `r.adjudication_status === 'adjudicated'`

### BUG-5: NULL role_id in role_function_tags (LOW severity)
- **Symptom:** BASELINED function coverage shows 277 instead of 276
- **Root cause:** 4 rows in `role_function_tags` have `role_id IS NULL`
- **Fix:** `DELETE FROM role_function_tags WHERE role_id IS NULL;`

---

## Complete Database Statistics (Reference)

| Table | Row Count |
|-------|-----------|
| scans | 71 |
| documents | 45 |
| role_dictionary | 1056 |
| scan_statements | 1404 |
| function_categories | 112 |
| role_function_tags | 1130 |
| role_relationships | 403 |
| hyperlink_exclusions | 0 |

| Metric | Value |
|--------|-------|
| Score range | 20 - 98 |
| Average score | 35.5 |
| Total issues | 211,667 |
| Total word count | 1,494,223 |
| Avg word count (per document) | 26,050 |
| Avg word count (per scan) | 21,045 |
| Baselined roles | 276 |
| Deliverable roles | 1 |
| NLP checkers available | 8 |
| NLP modules active | 7 (spacy, spelling, style, verbs, semantics, readability, languagetool) |

---

*Generated by automated data integrity verification. All values verified via direct sqlite3 queries and curl API calls against running AEGIS v4.6.2 server.*
