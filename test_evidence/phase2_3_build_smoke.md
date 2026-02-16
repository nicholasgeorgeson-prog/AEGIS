# Phase 2 — Clean Build/Run + Phase 3 — Smoke Tests

## AEGIS v4.6.2 Audit — 2026-02-13

## Phase 2: Build/Run

| Check | Status | Evidence |
|-------|--------|----------|
| Python 3.10.9 | PASS | `python3 --version` |
| 200 packages installed | PASS | `pip3 list \| wc -l` |
| 21/25 key imports OK | PASS (with notes) | 4 missing: pdfplumber (import error), rapidfuzz, passivepy, bokeh |
| Missing deps guarded | PASS | All 4 have try/except in source — non-fatal |
| Server starts | PASS | `python3 app.py` → HTTP 200 in <4ms |
| No startup errors | PASS | Zero error/exception/traceback in startup log |
| Baseline memory | INFO | ~490MB RSS at startup |

### Missing Dependencies Detail
- `pdfplumber`: Import error (`cannot import name 'Matrix' from pdfminer.utils`) — version incompatibility. Guarded in app.py:3662.
- `rapidfuzz`: Not installed, not imported by any core runtime file.
- `passivepy`: Not installed, only used in test/analysis scripts.
- `bokeh`: Not installed, not imported by any core runtime file.

**Verdict: Non-blocking. Core functionality unaffected.**

## Phase 3: Smoke Tests (3 Start/Stop Cycles)

| Cycle | Startup Time | HTTP Status | Log Errors | Memory |
|-------|-------------|-------------|------------|--------|
| 1 | 0.55s | 200 | 0 real | ~490MB |
| 2 | 0.54s | 200 | 0 real | ~490MB |
| 3 | 0.54s | 200 | 0 real | ~490MB |

- Port cleanup: Clean between cycles, no orphan processes
- All cycles: clean start, clean response, no state corruption

**Phase 3: PASS**

## Early Defects Found

### DEFECT-001 (HIGH — Data Integrity)
**Landing page metrics are wrong due to API pagination limit**
- `/api/scan-history` defaults to `limit=50` (app.py:4429)
- Landing page calls API without `?limit=` parameter (landing-page.js:187)
- UI shows 50 scans (correct: 71), 37 documents (correct: 45), 23 avg score (correct: 35)
- Roles (1056) and Statements (1404) are correct (different API sources)
- **Root cause**: app.py line 4429: `limit = int(request.args.get('limit', 50))`
- **Fix**: Landing page should call `/api/scan-history?limit=9999` or API should have a separate stats endpoint

### DEFECT-002 (LOW — Version Display)
**Help panel has hardcoded version v3.2.4**
- templates/index.html:2585: `<span class="help-version" id="help-version">v3.2.4</span>`
- Should read from version.json or meta tag like other version displays
