# AEGIS v5.8.2 — Manual QA Checklist

**Date:** February 17, 2026
**Purpose:** Step-by-step visual verification for the morning review

---

## Pre-Requisites
- [ ] Server restarted with: `python3 app.py --debug`
- [ ] Browser open at `http://localhost:5050`
- [ ] Both dark mode and light mode will be tested

---

## Critical Fixes (MUST VERIFY)

### 1. PDF Export — ReportLab Sanitization
- [ ] Open Roles Studio (sidebar or landing tile)
- [ ] Click Export dropdown > PDF Report
- [ ] PDF downloads without server error
- [ ] Open PDF — all role names render correctly
- [ ] No `&lt;` or `&amp;` showing as raw text in the PDF

### 2. Mass Statement Review — CSRF Fix
- [ ] Open Roles Studio > select a role with statements
- [ ] Open Mass Statement Review
- [ ] Select one or more statements
- [ ] Click bulk update > change a directive > save
- [ ] Toast shows success (NOT "CSRF validation failed")

### 3. Accessibility — Reduced Motion
- [ ] macOS: System Preferences > Accessibility > Display > Reduce Motion ON
- [ ] Reload the page
- [ ] Landing page: no particle animation, no card hover transitions
- [ ] Roles Studio: no animation on tab switches
- [ ] Hyperlink Validator: no progress animations
- [ ] Re-enable Reduce Motion after testing

---

## General Verification

### 4. Landing Page
- [ ] 9 tool tiles visible with correct icons and colors
- [ ] Metric badges show real counts (not "0" for everything)
- [ ] Clicking each tile opens the correct module
- [ ] AEGIS logo in nav bar returns to landing page
- [ ] Dark mode: particle background visible, text readable

### 5. Document Review
- [ ] Upload a test document (.docx or .pdf)
- [ ] Scan progress dashboard appears with step-by-step progress
- [ ] Results page shows issues with severity badges
- [ ] Score/grade display at top
- [ ] Export buttons (DOCX, XLSX, CSV) visible and functional

### 6. Roles Studio
- [ ] Overview tab: stats and chart load
- [ ] Dictionary tab: role cards display
- [ ] Adjudication tab: kanban columns visible
- [ ] Export dropdown: all options present
- [ ] Dark mode: all text readable

### 7. Statement History
- [ ] Overview dashboard: document list loads
- [ ] Click a document: viewer opens with highlighted statements
- [ ] Compare: select two scans, diff highlights show

### 8. Hyperlink Validator
- [ ] Open from landing page or nav
- [ ] Previous results load (if any)
- [ ] Domain filter dropdown works
- [ ] Stat tile clicking filters results

### 9. Zoom Testing
- [ ] 100% zoom: layout centered and clean
- [ ] 125% zoom: no content clipping
- [ ] 150% zoom: modals fit on screen
- [ ] No horizontal scrollbars at any level

---

## Sign-Off

| Area | Pass/Fail | Notes |
|------|-----------|-------|
| PDF Export | | |
| CSRF Fix | | |
| Reduced Motion | | |
| Landing Page | | |
| Document Review | | |
| Roles Studio | | |
| Statement History | | |
| Hyperlink Validator | | |
| Zoom Testing | | |
| Dark Mode | | |

**Tester:** _______________
**Date:** _______________
**Verdict:** PASS / FAIL / CONDITIONAL
