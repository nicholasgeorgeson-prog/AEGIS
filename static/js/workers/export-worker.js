/**
 * AEGIS Export Worker — Off-main-thread CSV/JSON generation
 * v6.5.0: Moves heavy string formatting to Web Worker for responsive UI
 *
 * Message protocol:
 *   Request:  { type: 'generateJSON'|'generateCSV'|'generateReviewLogCSV'|'generateBatchJSON', data: {...} }
 *   Response: { success: true, content: "string", type: "...", filename: "..." }
 *   Error:    { success: false, error: "message", type: "..." }
 */

'use strict';

/* ---- CSV helpers ---- */

function escapeCSV(val) {
    if (val == null) return '';
    var s = String(val);
    if (s.indexOf(',') !== -1 || s.indexOf('"') !== -1 || s.indexOf('\n') !== -1) {
        return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
}

function addBOMandCRLF(csv) {
    // UTF-8 BOM for Excel compatibility + CRLF line endings
    return '\uFEFF' + csv.replace(/\n/g, '\r\n');
}

/* ---- Generators ---- */

/**
 * Generate review JSON export string
 * @param {Object} data — { issues, filename, score, grade, documentInfo, filtersApplied }
 */
function generateJSON(data) {
    var exportObj = {
        filename: data.filename || 'Unknown',
        exported: new Date().toISOString(),
        score: data.score != null ? data.score : null,
        grade: data.grade || null,
        issue_count: data.issues ? data.issues.length : 0,
        document_info: data.documentInfo || null,
        issues: data.issues || [],
        filters_applied: data.filtersApplied || null
    };
    return JSON.stringify(exportObj, null, 2);
}

/**
 * Generate generic CSV from an array of issues
 * @param {Object} data — { issues, headers, fieldMap }
 *   headers: ['Severity', 'Category', ...]
 *   fieldMap: ['severity', 'category', ...] — property names matching headers
 */
function generateCSV(data) {
    var headers = data.headers || ['Severity', 'Category', 'Message', 'Flagged Text', 'Suggestion', 'Rule ID'];
    var fields = data.fieldMap || ['severity', 'category', 'message', 'flagged_text', 'suggestion', 'rule_id'];
    var issues = data.issues || [];

    var rows = [headers.join(',')];
    for (var i = 0; i < issues.length; i++) {
        var issue = issues[i];
        var cells = [];
        for (var f = 0; f < fields.length; f++) {
            cells.push(escapeCSV(issue[fields[f]]));
        }
        rows.push(cells.join(','));
    }
    return addBOMandCRLF(rows.join('\n'));
}

/**
 * Generate review log CSV
 * @param {Object} data — { logEntries }
 */
function generateReviewLogCSV(data) {
    var entries = data.logEntries || [];
    var headers = ['Timestamp', 'Issue ID', 'Action', 'Message', 'Category', 'Severity', 'Note', 'Reviewer'];
    var rows = [headers.join(',')];

    for (var i = 0; i < entries.length; i++) {
        var e = entries[i];
        var row = [
            escapeCSV(e.timestamp || ''),
            escapeCSV(e.issueId || ''),
            escapeCSV(e.action || ''),
            escapeCSV(e.message || ''),
            escapeCSV(e.category || ''),
            escapeCSV(e.severity || ''),
            escapeCSV(e.note || ''),
            escapeCSV(e.reviewer || '')
        ];
        rows.push(row.join(','));
    }
    return addBOMandCRLF(rows.join('\n'));
}

/**
 * Generate batch results JSON export
 * @param {Object} data — { issues, documentCount, exportDate }
 */
function generateBatchJSON(data) {
    var issues = data.issues || [];
    var categories = {};
    var severityBreakdown = {};

    for (var i = 0; i < issues.length; i++) {
        var cat = issues[i].category || 'Uncategorized';
        var sev = issues[i].severity || 'Info';
        categories[cat] = true;
        severityBreakdown[sev] = (severityBreakdown[sev] || 0) + 1;
    }

    var exportObj = {
        export_date: data.exportDate || new Date().toISOString(),
        total_issues: issues.length,
        document_count: data.documentCount || 0,
        unique_categories: Object.keys(categories).length,
        severity_breakdown: severityBreakdown,
        issues: issues
    };
    return JSON.stringify(exportObj, null, 2);
}

/* ---- Message handler ---- */

self.onmessage = function(e) {
    var msg = e.data;
    try {
        var content;
        switch (msg.type) {
            case 'generateJSON':
                content = generateJSON(msg.data);
                break;
            case 'generateCSV':
                content = generateCSV(msg.data);
                break;
            case 'generateReviewLogCSV':
                content = generateReviewLogCSV(msg.data);
                break;
            case 'generateBatchJSON':
                content = generateBatchJSON(msg.data);
                break;
            default:
                self.postMessage({ success: false, error: 'Unknown type: ' + msg.type, type: msg.type });
                return;
        }
        self.postMessage({
            success: true,
            content: content,
            type: msg.type,
            filename: msg.filename || null
        });
    } catch (err) {
        self.postMessage({
            success: false,
            error: err.message || String(err),
            type: msg.type
        });
    }
};
