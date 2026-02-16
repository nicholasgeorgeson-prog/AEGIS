# Phase 1: AEGIS Metrics Inventory

> Comprehensive mapping of all user-facing numeric values across the AEGIS application.
> Generated: 2026-02-13

---

## 1. Landing Page (`static/js/features/landing-page.js`)

### 1.1 Metric Cards (top 6 stat cards with animated count-up)

| Metric Name | DOM Element | Source | Computation | Format |
|---|---|---|---|---|
| Total Scans | `.lp-metric-value[data-target]` (id=scans) | `GET /api/scan-history` | `scanResult.data.length` (count of all scan records) | Integer |
| Documents | `.lp-metric-value[data-target]` (id=docs) | `GET /api/scan-history` | `new Set(scans.map(s => s.filename)).size` (unique filenames) | Integer |
| Roles Found | `.lp-metric-value[data-target]` (id=roles) | `GET /api/roles/dictionary` | `rolesResult.data.roles.length` (count of dictionary roles) | Integer |
| Statements | `.lp-metric-value[data-target]` (id=stmts) | `GET /api/scan-history` | `scans.reduce(sum + (s.statement_count \|\| s.stmt_count \|\| 0))` (sum across ALL scans, not latest-per-doc) | Integer |
| Avg Score | `.lp-metric-value[data-target]` (id=score) | `GET /api/scan-history` | `Math.round(scores.reduce(a+b) / scores.length)` where scores = `scans.filter(s.score != null).map(parseFloat(s.score))` | Integer (0-100) |
| Checkers | `.lp-metric-value[data-target]` (id=checkers) | Client-side constant | Hardcoded `data.checkerCount = 84` (line 124) | Integer |

### 1.2 Tool Tile Badges (badge counts on the 9 tool cards)

| Tile | Badge Text | Source | Key |
|---|---|---|---|
| Document Review | `{N} scans` | `data.totalScans` | Same as Total Scans above |
| Statement Forge | `{N} statements` | `data.totalStatements` | Same as Statements above |
| Roles Studio | `{N} roles` | `data.totalRoles` | Same as Roles Found above |
| Metrics & Analytics | `{N} avg score` | `data.avgScore` | Same as Avg Score above |
| Scan History | `{N} scans` | `data.totalScans` | Same as Total Scans above |
| Document Compare | (none) | null | No badge |
| Link Validator | (none) | null | No badge |
| Portfolio | `{N} documents` | `data.totalDocs` | Same as Documents above |
| SOW Generator | (none) | null | No badge |

### 1.3 Footer

| Metric | Source | Computation |
|---|---|---|
| Checker count text | Client constant | `${data.checkerCount} quality checkers` (hardcoded 84) |

### 1.4 NLP/Extractor Data (from capabilities)

| Metric | Source | Computation |
|---|---|---|
| NLP Engines list | `GET /api/extraction/capabilities` | `Object.entries(capsResult.nlp).filter(v===true).map(k)` |
| PDF Extractors list | `GET /api/extraction/capabilities` | `Object.entries(capsResult.pdf).filter(v===true).map(k)` |

---

## 2. Metrics & Analytics (`static/js/features/metrics-analytics.js`)

**API Endpoint:** `GET /api/metrics/dashboard` (single endpoint, response shape below in Section 7)

### 2.1 Overview Tab Hero Stats

| Metric Name | Source Field | Computation | Format |
|---|---|---|---|
| Documents | `data.overview.total_documents` | Server-side: `COUNT(*) FROM documents` | Integer |
| Statements | `data.overview.total_statements` | Server-side: `COUNT(*) FROM scan_statements` (latest scan per doc only) | Integer |
| Roles | `data.overview.total_roles` | Server-side: `COUNT(*) FROM role_dictionary WHERE is_active=1` | Integer |
| Avg Score | `data.overview.avg_score` | Server-side: `AVG(score) FROM scans`, rounded to 1 decimal | Float (0-100) |

### 2.2 Overview Tab Mini Stats

| Metric Name | DOM ID | Source Field | Format |
|---|---|---|---|
| Total Words | `ma-mini-words` | `data.overview.total_word_count` | Integer |
| Avg Words/Doc | `ma-mini-avgwords` | `Math.round(data.overview.avg_word_count)` | Integer |
| Total Issues | `ma-mini-issues` | `data.overview.total_issues` | Integer |
| Adjudicated | `ma-mini-adjudicated` | `data.roles.total_confirmed \|\| data.roles.total_adjudicated` | Integer |
| Deliverables | `ma-mini-deliverables` | `data.roles.total_deliverable` | Integer |
| Total Scans | `ma-mini-scans` | `data.overview.total_scans` | Integer |

### 2.3 Overview Tab Charts

| Chart | Type | Data Source | Labels |
|---|---|---|---|
| Score Trend | Line (Chart.js) | `data.quality.score_trend[].score` | Truncated filenames |
| Grade Distribution | Doughnut (Chart.js) | `data.quality.grade_distribution` (A/B/C/D/F counts) | A, B, C, D, F |
| Activity Heatmap | SVG (D3.js) | `data.scans[]` grouped by day | Calendar day cells (52 weeks) |
| Heatmap center text | Doughnut center | `gradeTotal` (sum of A+B+C+D+F counts) | `{N} scans` |

### 2.4 Quality Tab Hero Stats

| Metric Name | Source Field | Format |
|---|---|---|
| Avg Score | `data.overview.avg_score` | Float |
| Best Score | Client: `Math.max(...docs.map(d.latest_score))` | Float |
| Worst Score | Client: `Math.min(...docs.map(d.latest_score))` | Float |
| Total Issues | `data.overview.total_issues` | Integer |

### 2.5 Quality Tab Charts/Tables

| Chart | Type | Data Source |
|---|---|---|
| Score Distribution | Bar (Chart.js) | `data.quality.score_distribution[].{range,count}` (10-pt buckets) |
| Issue Categories | Horizontal Bar (Chart.js) | `data.quality.issue_categories[].{category,count}` (top 10) |
| Top Issues table | HTML table | `data.quality.top_issues[].{message,category,count}` (top 10) |
| Document Scores table | HTML table | `data.documents[].{filename,latest_score,latest_grade,issue_count,scan_count}` |

### 2.6 Statements Tab Hero Stats

| Metric Name | Source Field | Format |
|---|---|---|
| Total Statements | `data.statements.total` | Integer |
| Shall | `data.statements.by_directive.shall` | Integer |
| Must | `data.statements.by_directive.must` | Integer |
| Unique Roles | `data.statements.by_role.length` (client array length) | Integer |

### 2.7 Statements Tab Charts/Tables

| Chart | Type | Data Source |
|---|---|---|
| Directive Doughnut | Doughnut | `data.statements.by_directive` (shall/must/will/should/other) |
| Statements by Document | Horizontal Bar | `data.statements.by_document[].{filename,count}` (top 20) |
| Top Roles table | HTML table | `data.statements.by_role[].{role,count}` (top 20) |

### 2.8 Roles Tab Hero Stats

| Metric Name | Source Field | Format |
|---|---|---|
| Total Roles | `data.roles.total_extracted` | Integer |
| Confirmed | `data.roles.total_confirmed` | Integer |
| Deliverable | `data.roles.total_deliverable` | Integer |
| Rejected | `data.roles.total_rejected` | Integer |

### 2.9 Roles Tab Charts/Tables

| Chart | Type | Data Source |
|---|---|---|
| Adjudication Status | Doughnut | Confirmed / Deliverable / Rejected / Pending (derived: extracted - adjudicated) |
| Roles by Category | Horizontal Bar | `data.roles.by_category[].{category,count}` (top 12) |
| Function Coverage | Bubble (D3) | `data.roles.function_coverage[].{code,name,color,role_count}` |
| Top Roles table | HTML table | `data.roles.top_by_documents[].{role,document_count,mention_count}` (top 20) |
| Relationship Types | Bar | `data.relationships.by_type[].{type,count}` |
| Adj center text | Doughnut center | `data.roles.total_extracted` as `{N} total` |

### 2.10 Roles Tab Drill-Down (on row click)

| Metric Name | Computation | Format |
|---|---|---|
| Documents | `row.document_count` | Integer |
| Total Mentions | `row.mention_count` | Integer |
| Avg per Doc | `(row.mention_count / row.document_count).toFixed(1)` | Float (1 decimal) |

### 2.11 Documents Tab Hero Stats

| Metric Name | Source | Format |
|---|---|---|
| Documents | `data.documents.length` (client array length) | Integer |
| Total Words | `data.overview.total_word_count` | Integer |
| Avg Words | `Math.round(data.overview.avg_word_count)` | Integer |
| Multi-Scan | Client: `Math.round((multiScanDocs / docs.length) * 100)` | Percentage |

### 2.12 Documents Tab Charts/Tables

| Chart | Type | Data Source |
|---|---|---|
| Word Count Distribution | Bar | `data.documents_meta.word_count_distribution[].{range,count}` (< 1K / 1K-5K / 5K-10K / 10K-25K / 25K+) |
| Documents by Category | Doughnut | `data.documents_meta.by_category_type[].{type,count}` |
| Document List table | HTML table | `data.documents[].{filename,word_count,scan_count,latest_score,latest_grade,role_count,statement_count}` |

---

## 3. Roles Studio

### 3.1 Overview Tab Stat Cards (`roles-tabs-fix.js`, lines 444-489)

| Metric Name | DOM ID | Source | Computation | Format |
|---|---|---|---|---|
| Unique Roles | `total-roles-count` | `GET /api/roles/aggregated?include_deliverables=true` | `filteredRoles.length` (filtered by document selector) | Integer |
| Responsibilities | `total-responsibilities-count` | Same | `filteredRoles.reduce(sum + r.responsibility_count)` | Integer |
| Documents | `total-documents-count` | `GET /api/scan-history` | `new Set(filteredHistory.map(h.filename)).size` | Integer |
| Categories | `total-interactions-count` | Same as roles | `new Set(filteredRoles.map(r.category).filter(Boolean)).size` | Integer |
| Adjudicated subtitle | `adjudicated-subtitle-text` | `AEGIS.AdjudicationLookup.getStats()` | `"{confirmed+deliverable} adjudicated"` + optionally `"{deliverable} deliverable"` | Text |

### 3.2 Overview Tab - Top Roles List

| Metric | Source | Computation | Format |
|---|---|---|---|
| Role count badge | inline | `count` (per category from role distribution) | Integer |
| Document count per role | inline | `role.unique_document_count \|\| role.documents?.length \|\| 0` | `{N} docs` |
| Filter count | inline | `filteredRoles.length of roles.length` | `{N} of {M} roles` |

### 3.3 Adjudication Tab Stats (`roles-tabs-fix.js`, lines 1544-1577)

| Metric Name | DOM ID | Source | Computation | Format |
|---|---|---|---|---|
| Pending | `adj-pending-count` | Client state | Count of roles where `getRoleStatus(r) === 'pending'` | Integer |
| Confirmed | `adj-confirmed-count` | Client state | Count of roles where status === 'confirmed' | Integer |
| Deliverable | `adj-deliverable-count` | Client state | Count of roles where status === 'deliverable' | Integer |
| Rejected | `adj-rejected-count` | Client state | Count of roles where status === 'rejected' | Integer |
| Progress Ring | `adj-progress-ring` | Client state | `Math.round((adjudicated / total) * 100)` where adjudicated = confirmed + deliverable + rejected | Percentage (SVG ring) |

### 3.4 Adjudication Kanban Counts

| Metric Name | DOM ID | Format |
|---|---|---|
| Kanban Pending | `adj-kanban-pending` | Integer |
| Kanban Confirmed | `adj-kanban-confirmed` | Integer |
| Kanban Deliverable | `adj-kanban-deliverable` | Integer |
| Kanban Rejected | `adj-kanban-rejected` | Integer |
| Filter count | inline text | `Showing {N} of {M} roles` |

### 3.5 Cross-Reference Tab

| Metric | Source | Computation | Format |
|---|---|---|---|
| Role count x Doc count | Client state | `roleList.length` x `docList.length` | `{N} roles x {M} documents` |
| Cell connection count | Client state | Sum of `connections[roleId]` values | Integer per cell |

### 3.6 RACI Tab

| Metric | Source | Format |
|---|---|---|
| Known Roles count | Client state | `roles.length` |
| Roles by category | Client state | `catRoles.length` per category (top 10) |

### 3.7 Auto-Classify Modal

| Metric | Source | Computation | Format |
|---|---|---|---|
| Suggestions count | `POST /api/roles/dictionary/auto-classify` | `result.suggestions.filter(s => !s.already_adjudicated).length` | Integer |
| Filter pills | Client state | `All ({N})`, `Confirmed ({N})`, `Deliverable ({N})`, `Rejected ({N})` | Integer per status |
| Page info | Client state | `{start}-{end} of {filtered}({total} total)` | Range |
| Apply button | Client state | `Apply {N} Selected` | Integer |

### 3.8 Role Statement Viewer (inline in adjudication)

| Metric | Source | Format |
|---|---|---|
| Statement count | Client state | `{N} statements` |
| Document count | Client state | `{N} documents` |
| Per-doc statement count | Client state | Count per group | Integer badge |

---

## 4. Roles Dictionary (`static/js/roles-dictionary-fix.js`)

### 4.1 Dashboard Tiles (lines 262-326)

| Metric Name | Source | Computation | Format |
|---|---|---|---|
| Total Roles | `DictState.roles` | `roles.length` | Integer |
| Active / Inactive subtitle | Same | `{active} active . {inactive} inactive` | Integer pair |
| Deliverables | Same | `roles.filter(r.is_deliverable).length` | Integer |
| Deliverable % subtitle | Same | `Math.round(deliverable/total*100)` | `{N}% of dictionary` |
| Adjudicated | Same | `adjStats.confirmed + adjStats.deliverable` | Integer |
| Adj breakdown subtitle | Same | Confirmed / Deliverable / Rejected / Pending counts | 4 integers |
| Health Score | Same | `Math.round(((withDesc + withTags) / (total * 2)) * 100)` | Percentage + bar |
| Health subtitle | Same | `{withDesc} described . {withTags} tagged` | Integer pair |

### 4.2 Dashboard Charts

| Chart | Type | Data Source |
|---|---|---|
| Category Distribution | Doughnut (Chart.js) | `catEntries` from `DictState.roles` grouped by category |
| Source Breakdown | Horizontal bars (HTML) | `srcCounts` from `DictState.roles` grouped by source, with % width |
| Top Categories | Horizontal bars (HTML) | `catEntries.slice(0,8)` with count and % bar |

### 4.3 Filter Count Badge

| Metric | DOM ID | Computation | Format |
|---|---|---|---|
| Filter count | `dict-filter-count` | `filtered === total ? "{total} roles" : "{filtered} of {total} roles"` | Text |

### 4.4 Bulk Selection Count

| Metric | Source | Format |
|---|---|---|
| Selected count | `DictState.selectedRoles.size` | Integer (shown in toolbar) |

### 4.5 SIPOC Import Summary Stats

| Metric Name | Source | Format |
|---|---|---|
| Roles | `stats.unique_roles` | Integer |
| Tools | `stats.unique_tools` | Integer |
| Relationships | `stats.total_relationships` | Integer |
| Tagged Roles | `stats.roles_with_tags` | Integer |
| Roles Added | `data.roles_added` | Integer |
| Roles Updated | `data.roles_updated` | Integer |
| Relationships Created | `data.relationships_created` | Integer |
| Tags Assigned | `data.tags_assigned` | Integer |
| Auto-Adjudicated | `adjudicatedCount` | Integer (conditional) |
| Stale Roles Removed | `removed` | Integer (conditional) |

### 4.6 Import Diff Preview

| Metric | Source | Format |
|---|---|---|
| New Roles | `diff.new_roles.length` | `+{N}` badge (green) |
| Changed Roles | `diff.changed.length` | `~{N}` badge (amber) |
| Unchanged Roles | `diff.unchanged.length` | `={N}` badge (gray) |

---

## 5. Statement History (`static/js/features/statement-history.js`)

### 5.1 Overview Hero Stats (lines 449-471)

| Metric Name | Source | Computation | Format |
|---|---|---|---|
| Statements (Latest) | `GET /api/statement-forge/history/{docId}` | `latest.statement_count` | Integer + trend badge |
| Trend badge | Same | `latest.statement_count - prev.statement_count` | `+{N}` / `-{N}` / `+-0` |
| Scans Recorded | Same | `history.length` | Integer |
| Directive Statements | Same | `Object.values(latest.directive_counts).reduce(a+b)` | Integer |
| Unique Roles | Same | `latest.unique_roles` | Integer |

### 5.2 Scan Timeline (per scan row)

| Metric | Source | Format |
|---|---|---|
| Statement count | `scan.statement_count` | `{N} statements` |
| Diff badge | Client | `+{N}` / `-{N}` (vs previous scan) |
| Shall count | `scan.directive_counts.shall` | `Shall: {N}` |
| Must count | `scan.directive_counts.must` | `Must: {N}` |
| Will count | `scan.directive_counts.will` | `Will: {N}` |
| Should count | `scan.directive_counts.should` | `Should: {N}` |
| Roles count | `scan.unique_roles` | `{N} roles` |
| Sections count | `scan.section_count` | `{N} sections` |
| Timeline badge | Same | `{totalScans} scans` |

### 5.3 Review Progress Panel (v4.6.0)

| Metric | Source | Computation | Format |
|---|---|---|---|
| Review Progress | `GET /api/scan-history/statements/review-stats` | `{reviewed}/{total} reviewed ({pct}%)` where pct = `Math.round((reviewed/total)*100)` | Text fraction + percentage |

### 5.4 Duplicate Cleanup Dialog

| Metric | Source | Format |
|---|---|---|
| Duplicate groups | `GET /api/scan-history/statements/duplicates` | `Found {total_groups} duplicate groups ({total_duplicates} extra copies)` |

### 5.5 Document Viewer (per statement)

| Metric | Source | Format |
|---|---|---|
| Statement index | Client state | `{N} of {total}` in statement detail panel |

### 5.6 Compare Viewer

| Metric | Source | Format |
|---|---|---|
| Added count | Client diff | Count of statements with `_diff_status === 'added'` |
| Removed count | Client diff | Count with `_diff_status === 'removed'` |
| Modified count | Client diff | Count with `_diff_status === 'modified_new'` |
| Unchanged count | Client diff | Count with `_diff_status === 'unchanged'` |

---

## 6. Hyperlink Validator

### 6.1 Summary Stat Cards (`hyperlink-validator.js`, lines 1475-1524)

| Metric Name | DOM ID | Source | Computation | Format |
|---|---|---|---|---|
| Excellent (Working) | `hv-count-working` | `summary.working` | Count of results where status === 'WORKING' | Integer (animated) |
| Broken | `hv-count-broken` | `summary.broken` | Count where status in (BROKEN, INVALID, DNSFAILED, SSLERROR) | Integer (animated) |
| Redirect | `hv-count-redirect` | `summary.redirect` | Count where status === 'REDIRECT' | Integer (animated) |
| Timeout | `hv-count-timeout` | `summary.timeout` | Count where status === 'TIMEOUT' | Integer (animated) |
| Blocked | `hv-count-blocked` | `summary.blocked` | Count where status === 'BLOCKED' | Integer (animated) |
| Unknown | `hv-count-unknown` | `(summary.unknown \|\| 0) + (summary.dns_failed \|\| 0) + (summary.ssl_error \|\| 0) + (summary.invalid \|\| 0)` | Composite count | Integer (animated) |

**Summary computed by:** `HyperlinkValidatorState.generateLocalSummary(results)` or server response `validation_summary`.

### 6.2 Extended Metrics (Thorough Mode Only)

| Metric Name | DOM ID | Source | Format |
|---|---|---|---|
| SSL Warnings | `hv-count-ssl-warnings` | `summary.ssl_warnings` | Integer |
| Soft 404s | `hv-count-soft-404` | `summary.soft_404_count` | Integer |
| Suspicious | `hv-count-suspicious` | `summary.suspicious_count` | Integer |
| Avg Response Time | `hv-avg-response-time` | `summary.average_response_ms` | `{N}ms` |
| Min Response Time | `hv-min-response-time` | `summary.min_response_ms` | `{N}ms` |
| Max Response Time | `hv-max-response-time` | `summary.max_response_ms` | `{N}ms` |

### 6.3 Deep Validate (Rescan) Section

| Metric | DOM ID | Source | Computation | Format |
|---|---|---|---|---|
| Rescan-Eligible Count | `hv-blocked-count` | Client state | `results.filter(r => RESCAN_ELIGIBLE_STATUSES.includes(r.status)).length` | Integer |
| Rescan button text | inline | Client state | `Rescanning {N} URLs...` (min(eligible, 50)) | Integer |

**RESCAN_ELIGIBLE_STATUSES:** `['BLOCKED', 'TIMEOUT', 'DNSFAILED', 'AUTH_REQUIRED', 'SSLERROR']`

### 6.4 Visualizations (Chart Section)

| Chart | Type | Data Source |
|---|---|---|
| Status Donut | D3/SVG | summary.{working, broken, redirect, timeout, blocked, unknown} |
| Response Time Histogram | D3/SVG | `results[].response_time` |
| Domain Health Heatmap | D3/SVG | Per-domain breakdown (requires >= 3 domains) |

### 6.5 Excel Mode Summary

| Metric | Source | Computation | Format |
|---|---|---|---|
| Sheet breakdown | `data.sheet_summaries[].{name, total_links}` | Per-sheet link counts | `{sheet}: {N}` |
| Total links | `data.total_links \|\| results.length` | Total across all sheets | Integer |

### 6.6 History Panel

| Metric | Source | Format |
|---|---|---|
| URL count per run | `run.url_count` | `{N} URLs` |
| Working per run | `run.summary.working` | Integer (green) |
| Broken per run | `run.summary.broken` | Integer (red) |

### 6.7 HV State Summary Shape (`hyperlink-validator-state.js`, lines 595-618)

```
{
    total: results.length,
    working: N,
    broken: N,    // includes BROKEN, INVALID, DNSFAILED, SSLERROR
    redirect: N,
    timeout: N,
    blocked: N,
    unknown: N,
    mailto: N     // includes MAILTO, EXTRACTED
}
```

---

## 7. Scan History (`static/js/history-fixes.js`)

### 7.1 Stats Bar (lines 279-310)

| Metric Name | Source | Computation | Format |
|---|---|---|---|
| Documents | `GET /api/scan-history/stats` | `stats.document_count` (server: `len(unique_docs)`) | Integer |
| Scans | Same | `stats.scan_count` (server: `len(history)`) | Integer |
| Database Size | Same | `stats.database_size_mb` | `{N} MB` |

### 7.2 Scan History Table (per row, lines 427-489)

| Column | Source Field | Format |
|---|---|---|
| Filename | `scan.filename` | Text |
| Date | `scan.scan_time` | `MM/DD/YYYY HH:MM` |
| Issues | `scan.issue_count` | Integer |
| Score | `scan.score` | Integer (0-100) |
| Grade | `scan.grade` | Letter badge (A-F) |
| Statements | `scan.statement_count` | Integer (clickable if > 0) |
| Changes | `scan.issues_added` / `scan.issues_removed` | `+{N} -{M}` or "First scan" |

---

## 8. API Endpoint Response Shapes

### 8.1 `GET /api/scan-history` (app.py line 4421)

```json
{
    "success": true,
    "data": [
        {
            "scan_id": int,
            "filename": str,
            "scan_time": str,
            "issue_count": int,
            "score": float,
            "grade": str,
            "word_count": int,
            "issues_added": int,
            "issues_removed": int,
            "role_count": int,
            "document_id": int,
            "statement_count": int
        }
    ]
}
```

### 8.2 `GET /api/scan-history/stats` (app.py line 4478)

```json
{
    "success": true,
    "total_scans": int,
    "unique_documents": int,
    "last_scan": str|null
}
```

**Note:** Response has `total_scans` and `unique_documents` at top level, but `history-fixes.js` reads `stats.document_count` and `stats.scan_count`. This is a mismatch -- the JS expects `data.document_count` / `data.scan_count` / `data.database_size_mb` but the API returns `total_scans` / `unique_documents` / `last_scan` without `data` wrapper. The JS accesses `response.data` so these fields may not render correctly.

### 8.3 `GET /api/roles/dictionary` (app.py line 5872)

```json
{
    "success": true,
    "data": {
        "roles": [
            {
                "id": int,
                "role_name": str,
                "source": str,
                "category": str,
                "is_active": int,
                "is_deliverable": int,
                "description": str|null,
                "aliases": list|null,
                "function_tags": list|null
            }
        ],
        "total": int
    }
}
```

### 8.4 `GET /api/roles/aggregated` (app.py line 5120)

Returns roles aggregated across all scans with:
- `role_name`, `category`, `document_count`, `unique_document_count`, `total_mentions`
- `responsibility_count`, `documents[]`, `sample_contexts[]`

### 8.5 `GET /api/metrics/dashboard` (app.py line 7667)

```json
{
    "success": true,
    "data": {
        "overview": {
            "total_documents": int,
            "total_scans": int,
            "total_statements": int,
            "total_roles": int,
            "total_issues": int,
            "avg_score": float,
            "avg_word_count": int,
            "total_word_count": int,
            "last_scan_time": str|null
        },
        "documents": [
            {
                "id": int, "filename": str, "word_count": int,
                "scan_count": int, "first_scan": str, "last_scan": str,
                "latest_score": float, "latest_grade": str,
                "issue_count": int, "role_count": int,
                "statement_count": int, "category_type": str|null,
                "function_code": str|null
            }
        ],
        "scans": [
            {
                "id": int, "document_id": int, "filename": str,
                "scan_time": str, "score": float, "grade": str,
                "issue_count": int, "word_count": int
            }
        ],
        "statements": {
            "total": int,
            "by_directive": {"shall": int, "must": int, "will": int, ...},
            "by_role": [{"role": str, "count": int}],
            "by_document": [{"doc_id": int, "filename": str, "count": int}],
            "by_level": {"1": int, "2": int, ...}
        },
        "roles": {
            "total_extracted": int,
            "total_adjudicated": int,
            "total_deliverable": int,
            "total_rejected": int,
            "total_confirmed": int,
            "by_category": [{"category": str, "count": int}],
            "by_source": [{"source": str, "count": int}],
            "top_by_documents": [{"role": str, "document_count": int, "mention_count": int}],
            "function_coverage": [{"code": str, "name": str, "color": str, "role_count": int}]
        },
        "quality": {
            "score_distribution": [{"range": str, "count": int}],
            "grade_distribution": {"A": int, "B": int, "C": int, "D": int, "F": int},
            "score_trend": [{"scan_time": str, "score": float, "filename": str}],
            "issue_categories": [{"category": str, "count": int}],
            "top_issues": [{"message": str, "category": str, "count": int}]
        },
        "documents_meta": {
            "by_category_type": [{"type": str, "count": int}],
            "by_function": [{"code": str, "name": str, "color": str, "count": int}],
            "word_count_distribution": [{"range": str, "count": int}]
        },
        "relationships": {
            "total": int,
            "by_type": [{"type": str, "count": int}]
        }
    }
}
```

### 8.6 `GET /api/scan-history/statements/review-stats` (app.py line 4773)

```json
{
    "success": true,
    "data": {
        "total": int,
        "reviewed": int
    }
}
```

### 8.7 `GET /api/extraction/capabilities` (app.py line 3597)

```json
{
    "version": "3.0.91",
    "pdf": {"docling": bool, "camelot": bool, "tabula": bool, "pdfplumber": bool, "pymupdf": bool},
    "ocr": {"tesseract": bool, "pdf2image": bool},
    "nlp": {"spacy": bool, "sklearn": bool, "nltk": bool, "textstat": bool},
    "estimated_accuracy": {"table_extraction": 0.70, "role_detection": 0.75, "text_extraction": 0.80},
    "recommended_setup": []
}
```

---

## 9. Potential Data Discrepancies

| Issue | Location | Detail |
|---|---|---|
| Landing Page Statements = sum of ALL scans | `landing-page.js:200-203` | Sums `statement_count` across every scan record, including multiple scans of the same document. Metrics Dashboard uses latest-per-doc only. These will differ. |
| Landing Page Avg Score = avg of ALL scans | `landing-page.js:205-206` | Averages scores across all scans. Metrics Dashboard also uses `AVG(score) FROM scans` (all scans), so these should match. |
| Scan History Stats API mismatch | `app.py:4498-4503` vs `history-fixes.js:279-310` | API returns `total_scans`/`unique_documents` without `data` wrapper, but JS reads `response.data.document_count`/`scan_count`/`database_size_mb`. Field names don't align. |
| Checker count hardcoded | `landing-page.js:124` | `data.checkerCount = 84` is a static constant, not queried from server. If checkers change, this won't update. |
| Roles total: active-only vs all | Metrics Dashboard vs Dictionary | Dashboard counts `WHERE is_active=1`, Dictionary counts all roles including inactive. |
| HV summary.broken aggregation | `hyperlink-validator.js:1485` vs `state.js:610` | Main renderSummary combines `unknown + dns_failed + ssl_error + invalid` into the "Unknown" card. But `generateLocalSummary` puts DNSFAILED and SSLERROR into `broken`. The Unknown card in renderSummary may double-count. |

---

## 10. Summary Statistics

| Screen | Total Distinct Metrics | API Endpoints Used |
|---|---|---|
| Landing Page | 6 metric cards + 5 tile badges | `/api/scan-history`, `/api/roles/dictionary`, `/api/extraction/capabilities` |
| Metrics Analytics | 20 hero stats + 6 mini stats + 12 charts | `/api/metrics/dashboard` |
| Roles Studio (Overview) | 5 stat cards + role counts | `/api/roles/aggregated`, `/api/scan-history` |
| Roles Studio (Adjudication) | 4 status counts + progress ring + kanban counts | `/api/roles/aggregated`, `/api/roles/dictionary` |
| Roles Dictionary | 4 dashboard tiles + 3 charts + filter count | `/api/roles/dictionary` |
| Statement History | 4 hero stats + per-scan timeline metrics + review progress | `/api/statement-forge/history/{id}`, `/api/scan-history/statements/review-stats` |
| Hyperlink Validator | 6 stat cards + 6 extended metrics + rescan count | `/api/hyperlink-validator/validate` (POST), client state |
| Scan History | 3 stats-bar values + 7 table columns per row | `/api/scan-history`, `/api/scan-history/stats` |
