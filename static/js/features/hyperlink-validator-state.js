/**
 * Hyperlink Validator State Management
 * ====================================
 * State management module for the standalone hyperlink validator feature.
 * Handles API communication, job polling, and result caching.
 *
 * @version 1.0.0
 */

window.HyperlinkValidatorState = (function() {
    'use strict';

    // ==========================================================================
    // STATE
    // ==========================================================================

    let state = {
        // Current job
        jobId: null,
        runId: null,
        status: 'idle', // idle, running, complete, failed, cancelled

        // Progress tracking
        progress: {
            phase: '',
            overallProgress: 0,
            urlsCompleted: 0,
            urlsTotal: 0,
            currentUrl: '',
            eta: null
        },

        // Results
        results: [],
        summary: null,

        // Filtering
        filters: {
            status: 'all',
            search: ''
        },

        // Sorting
        sort: {
            column: 'status',
            direction: 'asc'
        },

        // History
        history: [],

        // Capabilities
        capabilities: null,

        // Polling
        pollInterval: null,
        pollIntervalMs: 1000,

        // Exclusions
        exclusions: []
    };

    // Event callbacks
    const callbacks = {
        onChange: [],
        onProgress: [],
        onComplete: [],
        onError: []
    };

    // ==========================================================================
    // HELPERS
    // ==========================================================================

    function getCSRFToken() {
        // Try to get from global State first
        if (window.State && window.State.csrfToken) {
            return window.State.csrfToken;
        }
        // Fallback to meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.content : null;
    }

    async function apiRequest(endpoint, options = {}) {
        const csrfToken = getCSRFToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
            ...(options.headers || {})
        };

        const response = await fetch(`/api/hyperlink-validator${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            const error = data.error || { message: 'Unknown error' };
            throw new Error(error.message || 'Request failed');
        }

        return data;
    }

    function emit(event, data) {
        const eventCallbacks = callbacks[event] || [];
        eventCallbacks.forEach(cb => {
            try {
                cb(data);
            } catch (e) {
                console.error(`[TWR HVState] Error in ${event} callback:`, e);
            }
        });
    }

    function setState(updates) {
        Object.assign(state, updates);
        emit('onChange', { ...state });
    }

    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================

    async function init() {
        console.log('[TWR HVState] Initializing...');

        try {
            // Load exclusions from persistent storage first, then localStorage as fallback
            await loadExclusionsFromDatabase();

            // Load capabilities
            const capsData = await apiRequest('/capabilities');
            state.capabilities = capsData.capabilities;

            // Load history
            await loadHistory();

            console.log('[TWR HVState] Initialized', state.capabilities);
            emit('onChange', { ...state });
            return true;
        } catch (e) {
            console.error('[TWR HVState] Initialization failed:', e);
            // Fallback to localStorage exclusions
            loadExclusionsFromStorage();
            return false;
        }
    }

    /**
     * Load exclusions from the persistent database via LinkHistory module.
     */
    async function loadExclusionsFromDatabase() {
        try {
            // Try using LinkHistory module if available
            if (window.LinkHistory && typeof window.LinkHistory.loadAndSyncExclusions === 'function') {
                const exclusions = await window.LinkHistory.loadAndSyncExclusions();
                if (exclusions && exclusions.length > 0) {
                    state.exclusions = exclusions.map(e => ({
                        pattern: e.pattern,
                        match_type: e.match_type,
                        reason: e.reason,
                        treat_as_valid: e.treat_as_valid
                    }));
                    console.log('[TWR HVState] Loaded', state.exclusions.length, 'exclusions from database');
                    return;
                }
            }

            // Direct API call fallback
            const response = await fetch('/api/hyperlink-validator/exclusions?active_only=true');
            const data = await response.json();

            if (data.success && data.exclusions) {
                state.exclusions = data.exclusions.map(e => ({
                    pattern: e.pattern,
                    match_type: e.match_type,
                    reason: e.reason,
                    treat_as_valid: e.treat_as_valid
                }));
                console.log('[TWR HVState] Loaded', state.exclusions.length, 'exclusions from API');
            }
        } catch (e) {
            console.warn('[TWR HVState] Failed to load exclusions from database, using localStorage:', e);
            loadExclusionsFromStorage();
        }
    }

    function reset() {
        // Stop any polling
        stopPolling();

        // Reset state
        state.jobId = null;
        state.runId = null;
        state.status = 'idle';
        state.progress = {
            phase: '',
            overallProgress: 0,
            urlsCompleted: 0,
            urlsTotal: 0,
            currentUrl: '',
            eta: null
        };
        state.results = [];
        state.summary = null;
        state.filters = { status: 'all', search: '' };
        state.sort = { column: 'status', direction: 'asc' };

        emit('onChange', { ...state });
    }

    function isInitialized() {
        return state.capabilities !== null;
    }

    // ==========================================================================
    // VALIDATION
    // ==========================================================================

    async function startValidation(urls, mode = 'validator', options = {}) {
        console.log(`[TWR HVState] Starting validation: ${urls.length} URLs, mode=${mode}`);

        // Reset previous results
        state.results = [];
        state.summary = null;
        state.status = 'running';
        state.progress = {
            phase: 'starting',
            overallProgress: 0,
            urlsCompleted: 0,
            urlsTotal: urls.length,
            currentUrl: '',
            eta: null
        };

        emit('onChange', { ...state });

        try {
            const data = await apiRequest('/validate', {
                method: 'POST',
                body: JSON.stringify({
                    urls: urls,
                    mode: mode,
                    options: options,
                    async: true
                })
            });

            state.jobId = data.job_id;
            emit('onChange', { ...state });

            // Start polling
            startPolling();

            return data.job_id;
        } catch (e) {
            state.status = 'failed';
            emit('onError', { message: e.message });
            emit('onChange', { ...state });
            throw e;
        }
    }

    async function cancelValidation() {
        if (!state.jobId) {
            console.warn('[TWR HVState] No job to cancel');
            return false;
        }

        console.log(`[TWR HVState] Cancelling job ${state.jobId}`);

        try {
            await apiRequest(`/cancel/${state.jobId}`, { method: 'POST' });

            stopPolling();
            state.status = 'cancelled';
            emit('onChange', { ...state });

            return true;
        } catch (e) {
            console.error('[TWR HVState] Cancel failed:', e);
            return false;
        }
    }

    // ==========================================================================
    // POLLING
    // ==========================================================================

    function startPolling() {
        if (state.pollInterval) {
            clearInterval(state.pollInterval);
        }

        state.pollInterval = setInterval(pollJobStatus, state.pollIntervalMs);
        // Also poll immediately
        pollJobStatus();
    }

    function stopPolling() {
        if (state.pollInterval) {
            clearInterval(state.pollInterval);
            state.pollInterval = null;
        }
    }

    async function pollJobStatus() {
        if (!state.jobId) {
            stopPolling();
            return;
        }

        try {
            // Include results if complete
            const includeResults = state.status !== 'running';
            const data = await apiRequest(`/job/${state.jobId}?include_results=${includeResults}`);

            const job = data.job;

            // Update progress
            if (job.progress) {
                state.progress = {
                    phase: job.progress.phase || '',
                    overallProgress: job.progress.overall_progress || 0,
                    urlsCompleted: job.progress.checkers_completed || 0,
                    urlsTotal: state.progress.urlsTotal,
                    currentUrl: job.progress.last_log || '',
                    eta: job.eta
                };
            }

            // v4.6.2: Pass live_stats from backend to cinematic progress
            const liveStats = job.live_stats || null;

            // v4.6.2: Use live_stats.completed for more accurate completion count
            if (liveStats && liveStats.completed > 0) {
                state.progress.urlsCompleted = liveStats.completed;
            }

            emit('onProgress', { ...state.progress, liveStats });

            // Check status
            if (job.status === 'complete') {
                stopPolling();

                state.status = 'complete';
                state.runId = job.run_id;
                state.summary = job.summary;

                // Fetch full results
                if (job.results) {
                    state.results = job.results;
                } else {
                    // Need to fetch results separately
                    const resultsData = await apiRequest(`/job/${state.jobId}?include_results=true`);
                    state.results = resultsData.job.results || [];
                }

                emit('onComplete', {
                    results: state.results,
                    summary: state.summary
                });

                // Record scan to persistent history
                recordScanToHistory('paste', '', state.results, state.summary);

                // Refresh history
                await loadHistory();

            } else if (job.status === 'failed') {
                stopPolling();
                state.status = 'failed';
                emit('onError', { message: job.error || 'Validation failed' });

            } else if (job.status === 'cancelled') {
                stopPolling();
                state.status = 'cancelled';
            }

            emit('onChange', { ...state });

        } catch (e) {
            console.error('[TWR HVState] Poll error:', e);
            // Don't stop polling on transient errors
        }
    }

    // ==========================================================================
    // FILTERING & SORTING
    // ==========================================================================

    function setFilter(type, value) {
        state.filters[type] = value;
        emit('onChange', { ...state });
    }

    function getFilters() {
        return { ...state.filters };
    }

    function setSortColumn(column, direction = 'asc') {
        state.sort = { column, direction };
        emit('onChange', { ...state });
    }

    function getFilteredResults() {
        let filtered = [...state.results];

        // Filter by status
        if (state.filters.status && state.filters.status !== 'all') {
            const filterVal = state.filters.status.toLowerCase();
            if (filterVal === 'issues') {
                // All non-working statuses
                filtered = filtered.filter(r =>
                    !['WORKING', 'REDIRECT'].includes(r.status.toUpperCase())
                );
            } else if (filterVal === 'broken') {
                // v4.6.2: Broken includes all error statuses
                filtered = filtered.filter(r =>
                    ['BROKEN', 'INVALID', 'DNSFAILED', 'SSLERROR'].includes(r.status.toUpperCase())
                );
            } else {
                filtered = filtered.filter(r =>
                    r.status.toUpperCase() === filterVal.toUpperCase()
                );
            }
        }

        // v4.6.2: Filter by domain
        if (state.filters.domain && state.filters.domain !== 'all') {
            const domainFilter = state.filters.domain.toLowerCase();
            filtered = filtered.filter(r => {
                try {
                    const urlDomain = new URL(r.url).hostname.toLowerCase();
                    return urlDomain === domainFilter || urlDomain.endsWith('.' + domainFilter);
                } catch {
                    return false;
                }
            });
        }

        // Filter by search
        if (state.filters.search) {
            const search = state.filters.search.toLowerCase();
            filtered = filtered.filter(r =>
                r.url.toLowerCase().includes(search) ||
                (r.message && r.message.toLowerCase().includes(search))
            );
        }

        // Sort
        const { column, direction } = state.sort;
        filtered.sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];

            // Handle null/undefined
            if (aVal === null || aVal === undefined) aVal = '';
            if (bVal === null || bVal === undefined) bVal = '';

            // Handle numbers
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return direction === 'asc' ? aVal - bVal : bVal - aVal;
            }

            // Handle strings
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();

            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        return filtered;
    }

    // ==========================================================================
    // HISTORY
    // ==========================================================================

    async function loadHistory() {
        try {
            const data = await apiRequest('/history?limit=20');
            state.history = data.scans || data.history || [];
            emit('onChange', { ...state });
        } catch (e) {
            console.error('[TWR HVState] Failed to load history:', e);
        }
    }

    async function loadHistoricalRun(jobId) {
        console.log(`[TWR HVState] Loading historical run: ${jobId}`);

        try {
            const data = await apiRequest(`/job/${jobId}?include_results=true`);
            const job = data.job;

            state.jobId = jobId;
            state.runId = job.run_id;
            state.status = job.status;
            state.results = job.results || [];
            state.summary = job.summary;
            state.progress = {
                phase: 'complete',
                overallProgress: 100,
                urlsCompleted: state.results.length,
                urlsTotal: state.results.length,
                currentUrl: '',
                eta: null
            };

            emit('onChange', { ...state });

            return true;
        } catch (e) {
            console.error('[TWR HVState] Failed to load historical run:', e);
            emit('onError', { message: `Failed to load run: ${e.message}` });
            return false;
        }
    }

    // ==========================================================================
    // EXPORT
    // ==========================================================================

    function getExportUrl(format = 'csv') {
        if (!state.jobId) return null;
        return `/api/hyperlink-validator/export/${state.jobId}?format=${format}`;
    }

    /**
     * Generate client-side export for local results (Excel/DOCX).
     * @param {string} format - csv, json, or html
     * @returns {Blob|null} - Downloadable blob or null if no results
     */
    function exportLocalResults(format = 'csv') {
        if (!state.results || state.results.length === 0) return null;

        const results = state.results;
        const summary = state.summary || generateLocalSummary(results);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        let content = '';
        let mimeType = '';
        let filename = '';

        if (format === 'csv') {
            // CSV export
            const headers = ['URL', 'Status', 'Status Code', 'Message', 'Response Time (ms)', 'Link Type', 'Location'];
            const rows = results.map(r => [
                r.url || '',
                r.status || '',
                r.status_code || '',
                (r.message || '').replace(/"/g, '""'),
                r.response_time_ms || '',
                r.link_type || r.link_source || '',
                r.sheet_name ? `${r.sheet_name}:${r.cell_address}` : (r.location || '')
            ]);

            content = [headers.join(','), ...rows.map(row =>
                row.map(cell => `"${cell}"`).join(',')
            )].join('\n');

            mimeType = 'text/csv';
            filename = `hyperlink_validation_${timestamp}.csv`;

        } else if (format === 'json') {
            // JSON export
            content = JSON.stringify({
                exported_at: new Date().toISOString(),
                summary: summary,
                results: results
            }, null, 2);

            mimeType = 'application/json';
            filename = `hyperlink_validation_${timestamp}.json`;

        } else if (format === 'html') {
            // HTML report export
            content = generateHtmlReport(results, summary, timestamp);
            mimeType = 'text/html';
            filename = `hyperlink_validation_${timestamp}.html`;
        }

        if (!content) return null;

        // For CSV: add UTF-8 BOM and normalize to CRLF for Windows Excel compatibility
        if (format === 'csv') {
            const bom = '\uFEFF';
            const crlf = content.replace(/\r?\n/g, '\r\n');
            const blob = new Blob([bom + crlf], { type: 'text/csv;charset=utf-8;' });
            return { blob, filename, mimeType: 'text/csv;charset=utf-8;' };
        }

        const blob = new Blob([content], { type: mimeType });
        return { blob, filename, mimeType };
    }

    function generateLocalSummary(results) {
        const summary = {
            total: results.length,
            working: 0,
            broken: 0,
            redirect: 0,
            timeout: 0,
            blocked: 0,
            auth_required: 0,
            unknown: 0,
            mailto: 0
        };

        results.forEach(r => {
            const status = (r.status || '').toUpperCase();
            if (status === 'WORKING') summary.working++;
            else if (status === 'BROKEN' || status === 'INVALID' || status === 'DNSFAILED' || status === 'SSLERROR') summary.broken++;
            else if (status === 'REDIRECT') summary.redirect++;
            else if (status === 'TIMEOUT') summary.timeout++;
            else if (status === 'BLOCKED') summary.blocked++;
            else if (status === 'AUTH_REQUIRED') summary.auth_required++;
            else if (status === 'MAILTO' || status === 'EXTRACTED') summary.mailto++;
            else summary.unknown++;
        });

        return summary;
    }

    function generateHtmlReport(results, summary, timestamp) {
        // ── Aggregate analytics data ──────────────────────────────────
        const statusColors = {
            WORKING: '#22c55e', BROKEN: '#ef4444', INVALID: '#ef4444',
            REDIRECT: '#3b82f6', TIMEOUT: '#f59e0b', BLOCKED: '#8b5cf6',
            MAILTO: '#64748b', EXTRACTED: '#6b7280', UNKNOWN: '#6b7280'
        };

        // Domain breakdown
        const domainMap = {};
        results.forEach(r => {
            try {
                const d = new URL(r.url).hostname;
                if (!domainMap[d]) domainMap[d] = { working: 0, broken: 0, redirect: 0, timeout: 0, blocked: 0, other: 0, total: 0, avgTime: 0, times: [] };
                const dm = domainMap[d];
                dm.total++;
                const s = (r.status || '').toUpperCase();
                if (s === 'WORKING') dm.working++;
                else if (s === 'BROKEN' || s === 'INVALID') dm.broken++;
                else if (s === 'REDIRECT') dm.redirect++;
                else if (s === 'TIMEOUT') dm.timeout++;
                else if (s === 'BLOCKED') dm.blocked++;
                else dm.other++;
                if (r.response_time_ms) dm.times.push(r.response_time_ms);
            } catch (e) {}
        });
        Object.values(domainMap).forEach(dm => {
            dm.avgTime = dm.times.length ? Math.round(dm.times.reduce((a, b) => a + b, 0) / dm.times.length) : 0;
        });
        const domainsSorted = Object.entries(domainMap).sort((a, b) => b[1].total - a[1].total);

        // Sheet breakdown (for Excel sources)
        const sheetMap = {};
        results.forEach(r => {
            if (!r.sheet_name) return;
            if (!sheetMap[r.sheet_name]) sheetMap[r.sheet_name] = { working: 0, broken: 0, total: 0 };
            const sm = sheetMap[r.sheet_name];
            sm.total++;
            const s = (r.status || '').toUpperCase();
            if (s === 'WORKING') sm.working++;
            else if (s === 'BROKEN' || s === 'INVALID') sm.broken++;
        });
        const hasSheets = Object.keys(sheetMap).length > 0;

        // File type breakdown from URLs
        const typeMap = {};
        results.forEach(r => {
            try {
                const path = new URL(r.url).pathname;
                const ext = path.includes('.') ? path.split('.').pop().toLowerCase().substring(0, 10) : 'unknown';
                if (!typeMap[ext]) typeMap[ext] = 0;
                typeMap[ext]++;
            } catch (e) {}
        });
        const typesSorted = Object.entries(typeMap).sort((a, b) => b[1] - a[1]).slice(0, 15);

        // Response time stats
        const times = results.filter(r => r.response_time_ms > 0).map(r => r.response_time_ms);
        const avgTime = times.length ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : 0;
        const minTime = times.length ? Math.round(Math.min(...times)) : 0;
        const maxTime = times.length ? Math.round(Math.max(...times)) : 0;
        const medianTime = times.length ? Math.round(times.sort((a, b) => a - b)[Math.floor(times.length / 2)]) : 0;

        // Error message frequency
        const errorMap = {};
        results.filter(r => (r.status || '').toUpperCase() !== 'WORKING').forEach(r => {
            const msg = (r.message || 'Unknown error').substring(0, 80);
            if (!errorMap[msg]) errorMap[msg] = 0;
            errorMap[msg]++;
        });
        const topErrors = Object.entries(errorMap).sort((a, b) => b[1] - a[1]).slice(0, 10);

        // Health score
        const total = summary?.total || results.length;
        const healthPct = total > 0 ? Math.round(((summary?.working || 0) / total) * 100) : 0;

        // ── Build table rows JSON for interactive filtering ───────────
        const rowsData = JSON.stringify(results.map((r, i) => ({
            i,
            url: r.url || '',
            status: (r.status || 'UNKNOWN').toUpperCase(),
            code: r.status_code || '',
            message: r.message || '',
            time: r.response_time_ms ? Math.round(r.response_time_ms) : '',
            location: r.sheet_name ? r.sheet_name + ':' + (r.cell_address || '') : (r.location || ''),
            context: r.context || '',
            sheet: r.sheet_name || '',
            domain: (() => { try { return new URL(r.url).hostname; } catch(e) { return ''; } })()
        })));

        // ── Build HTML ────────────────────────────────────────────────
        const esc = (s) => escapeHtmlContent(s);
        const escA = (s) => escapeHtmlAttr(s);

        // Domain rows HTML
        const domainRowsHtml = domainsSorted.map(([domain, dm]) => {
            const healthPct = dm.total > 0 ? Math.round((dm.working / dm.total) * 100) : 0;
            const barColor = healthPct >= 80 ? '#22c55e' : healthPct >= 50 ? '#f59e0b' : '#ef4444';
            return `<tr>
                <td class="domain-name">${esc(domain)}</td>
                <td class="num">${dm.total}</td>
                <td class="num c-working">${dm.working}</td>
                <td class="num c-broken">${dm.broken}</td>
                <td class="num">${dm.blocked + dm.timeout + dm.redirect + dm.other}</td>
                <td class="num">${dm.avgTime ? dm.avgTime + 'ms' : '-'}</td>
                <td>
                    <div class="health-bar-wrap"><div class="health-bar" style="width:${healthPct}%;background:${barColor}"></div></div>
                    <span class="health-pct" style="color:${barColor}">${healthPct}%</span>
                </td>
            </tr>`;
        }).join('\n');

        // Sheet rows HTML
        const sheetRowsHtml = hasSheets ? Object.entries(sheetMap).map(([sheet, sm]) => {
            const pct = sm.total > 0 ? Math.round((sm.working / sm.total) * 100) : 0;
            const barColor = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
            return `<tr>
                <td>${esc(sheet)}</td>
                <td class="num">${sm.total}</td>
                <td class="num c-working">${sm.working}</td>
                <td class="num c-broken">${sm.broken}</td>
                <td>
                    <div class="health-bar-wrap"><div class="health-bar" style="width:${pct}%;background:${barColor}"></div></div>
                    <span class="health-pct" style="color:${barColor}">${pct}%</span>
                </td>
            </tr>`;
        }).join('\n') : '';

        // Error pattern rows
        const errorRowsHtml = topErrors.map(([msg, count]) =>
            `<tr><td class="err-msg">${esc(msg)}</td><td class="num">${count}</td></tr>`
        ).join('\n');

        // File type chart bars
        const maxTypeCount = typesSorted.length ? typesSorted[0][1] : 1;
        const typeChartHtml = typesSorted.map(([ext, count]) => {
            const pct = Math.round((count / maxTypeCount) * 100);
            return `<div class="type-row">
                <span class="type-label">.${esc(ext)}</span>
                <div class="type-bar-wrap"><div class="type-bar" style="width:${pct}%"></div></div>
                <span class="type-count">${count}</span>
            </div>`;
        }).join('\n');

        return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AEGIS Hyperlink Validation Report</title>
<style>
:root {
    --bg: #0d1117; --bg-card: #161b22; --bg-card-alt: #1c2333; --bg-hover: #1f2937;
    --border: #30363d; --border-light: #21262d;
    --text: #e6edf3; --text-dim: #8b949e; --text-muted: #484f58;
    --gold: #D6A84A; --gold-dim: rgba(214,168,74,0.15);
    --green: #22c55e; --red: #ef4444; --blue: #3b82f6; --orange: #f59e0b; --purple: #8b5cf6;
    --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.5; }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ─────────────────────────────────────────── */
.report-header {
    background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 50%, #0d1117 100%);
    border-bottom: 1px solid var(--border);
    padding: 2rem 2.5rem;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
}
.header-left { display: flex; align-items: center; gap: 1rem; }
.aegis-logo {
    width: 44px; height: 44px; border-radius: 10px;
    background: var(--gold-dim); border: 1px solid rgba(214,168,74,0.3);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 16px; color: var(--gold);
}
.header-title { font-size: 1.25rem; font-weight: 700; color: var(--text); }
.header-sub { font-size: 0.8125rem; color: var(--text-dim); margin-top: 2px; }
.header-right { text-align: right; }
.header-right .date { font-size: 0.8125rem; color: var(--text-dim); }
.header-right .health-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.875rem; margin-top: 6px;
}

/* ── Content wrapper ────────────────────────────────── */
.content { max-width: 1400px; margin: 0 auto; padding: 1.5rem 2rem 3rem; }

/* ── Stat cards ─────────────────────────────────────── */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 1.5rem; }
.stat-card {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; position: relative; overflow: hidden;
}
.stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.stat-card.s-total::before { background: var(--gold); }
.stat-card.s-working::before { background: var(--green); }
.stat-card.s-broken::before { background: var(--red); }
.stat-card.s-redirect::before { background: var(--blue); }
.stat-card.s-timeout::before { background: var(--orange); }
.stat-card.s-blocked::before { background: var(--purple); }
.stat-value { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; }
.stat-label { font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); margin-top: 2px; }
.s-total .stat-value { color: var(--gold); }
.s-working .stat-value { color: var(--green); }
.s-broken .stat-value { color: var(--red); }
.s-redirect .stat-value { color: var(--blue); }
.s-timeout .stat-value { color: var(--orange); }
.s-blocked .stat-value { color: var(--purple); }

/* ── Section panels ─────────────────────────────────── */
.section { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 1.25rem; overflow: hidden; }
.section-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.875rem 1.25rem; border-bottom: 1px solid var(--border);
    cursor: pointer; user-select: none;
}
.section-header:hover { background: var(--bg-hover); }
.section-title { font-size: 0.9375rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.section-badge { background: var(--gold-dim); color: var(--gold); padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.section-toggle { color: var(--text-dim); font-size: 1.25rem; transition: transform 0.2s; }
.section.collapsed .section-body { display: none; }
.section.collapsed .section-toggle { transform: rotate(-90deg); }
.section-body { padding: 1rem 1.25rem; }

/* ── Tables ─────────────────────────────────────────── */
table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
th { text-align: left; padding: 8px 10px; color: var(--text-dim); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--border); background: var(--bg-card-alt); position: sticky; top: 0; z-index: 1; }
td { padding: 8px 10px; border-bottom: 1px solid var(--border-light); vertical-align: top; }
tr:hover td { background: rgba(255,255,255,0.02); }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.c-working { color: var(--green); }
.c-broken { color: var(--red); }
.domain-name { font-weight: 600; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.err-msg { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.75rem; color: var(--text-dim); max-width: 600px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Health bars ────────────────────────────────────── */
.health-bar-wrap { display: inline-block; width: 60px; height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden; vertical-align: middle; }
.health-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
.health-pct { font-size: 0.75rem; font-weight: 700; margin-left: 6px; }

/* ── File type chart ────────────────────────────────── */
.type-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.type-label { width: 80px; font-size: 0.8125rem; font-weight: 600; color: var(--text-dim); text-align: right; font-family: 'SF Mono', 'Fira Code', monospace; }
.type-bar-wrap { flex: 1; height: 20px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.type-bar { height: 100%; background: linear-gradient(90deg, var(--gold), rgba(214,168,74,0.6)); border-radius: 4px; }
.type-count { width: 50px; text-align: right; font-size: 0.8125rem; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ── Timing stats ───────────────────────────────────── */
.timing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
.timing-stat { text-align: center; padding: 0.75rem; background: var(--bg); border-radius: 8px; }
.timing-stat .tv { font-size: 1.5rem; font-weight: 800; color: var(--gold); }
.timing-stat .tl { font-size: 0.6875rem; text-transform: uppercase; color: var(--text-dim); margin-top: 2px; }

/* ── Interactive toolbar ────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.toolbar input, .toolbar select {
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    padding: 7px 12px; border-radius: 6px; font-size: 0.8125rem; font-family: var(--font);
}
.toolbar input:focus, .toolbar select:focus { border-color: var(--gold); outline: none; }
.toolbar input[type="text"] { min-width: 240px; }
.result-count { font-size: 0.8125rem; color: var(--text-dim); margin-left: auto; }
.url-cell { word-break: break-all; max-width: 420px; }
.status-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-weight: 700; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.03em; white-space: nowrap;
}
.ctx-info { font-size: 0.6875rem; color: var(--text-muted); margin-top: 2px; }
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--gold); }
.sort-arrow { font-size: 0.625rem; margin-left: 3px; }

/* ── Results table scroll ───────────────────────────── */
.table-scroll { max-height: 70vh; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; }
.table-scroll::-webkit-scrollbar { width: 6px; }
.table-scroll::-webkit-scrollbar-track { background: var(--bg-card); }
.table-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Footer ─────────────────────────────────────────── */
.report-footer {
    text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.75rem;
    border-top: 1px solid var(--border); margin-top: 2rem;
}
.report-footer strong { color: var(--gold); }

/* ── Donut chart ────────────────────────────────────── */
.donut-section { display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; justify-content: center; padding: 1rem 0; }
.donut-wrap { position: relative; width: 180px; height: 180px; }
.donut-wrap svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.donut-wrap circle { fill: none; stroke-width: 28; }
.donut-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); text-align: center; }
.donut-center .dc-val { font-size: 2rem; font-weight: 800; }
.donut-center .dc-label { font-size: 0.6875rem; color: var(--text-dim); text-transform: uppercase; }
.donut-legend { display: flex; flex-direction: column; gap: 8px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-count { font-weight: 700; min-width: 40px; text-align: right; font-variant-numeric: tabular-nums; }

/* ── Two-column layout ──────────────────────────────── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

/* ── Print styles ───────────────────────────────────── */
@media print {
    body { background: #fff; color: #111; }
    .report-header { background: #fff; border-bottom: 2px solid #111; }
    .header-title, .section-title { color: #111; }
    .stat-card, .section { border-color: #ccc; background: #f9f9f9; }
    .section-header { background: #eee; }
    th { background: #eee; color: #333; }
    td { border-color: #ddd; }
    .toolbar { display: none; }
    .table-scroll { max-height: none; overflow: visible; }
    .no-print { display: none !important; }
}

/* ── Light mode toggle ──────────────────────────────── */
body.light {
    --bg: #f8fafc; --bg-card: #ffffff; --bg-card-alt: #f1f5f9; --bg-hover: #e2e8f0;
    --border: #e2e8f0; --border-light: #f1f5f9;
    --text: #1e293b; --text-dim: #64748b; --text-muted: #94a3b8;
}
body.light a { color: #2563eb; }
body.light .toolbar input, body.light .toolbar select { background: #fff; color: #1e293b; border-color: #cbd5e1; }
body.light .type-bar { background: linear-gradient(90deg, #D6A84A, #e8c473); }
body.light .timing-stat { background: #f1f5f9; }
body.light .timing-stat .tv { color: #b8743a; }
.theme-toggle {
    position: fixed; bottom: 1rem; right: 1rem; z-index: 100;
    width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--border);
    background: var(--bg-card); color: var(--text); cursor: pointer;
    display: flex; align-items: center; justify-content: center; font-size: 1.125rem;
    transition: all 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.theme-toggle:hover { border-color: var(--gold); color: var(--gold); transform: scale(1.1); }
</style>
</head>
<body>
<!-- ── Header ─────────────────────────────────────── -->
<div class="report-header">
    <div class="header-left">
        <div class="aegis-logo">A</div>
        <div>
            <div class="header-title">AEGIS Hyperlink Validation Report</div>
            <div class="header-sub">Generated ${new Date().toLocaleString()} &middot; ${total.toLocaleString()} links analyzed</div>
        </div>
    </div>
    <div class="header-right">
        <div class="health-badge" style="background:${healthPct >= 80 ? 'rgba(34,197,94,0.15);color:#22c55e' : healthPct >= 50 ? 'rgba(245,158,11,0.15);color:#f59e0b' : 'rgba(239,68,68,0.15);color:#ef4444'}">
            ${healthPct >= 80 ? '&#9679;' : healthPct >= 50 ? '&#9888;' : '&#10005;'}
            &nbsp;${healthPct}% Health Score
        </div>
    </div>
</div>

<div class="content">
<!-- ── Summary Stats ──────────────────────────────── -->
<div class="stats-row">
    <div class="stat-card s-total"><div class="stat-value">${(summary?.total || total).toLocaleString()}</div><div class="stat-label">Total Links</div></div>
    <div class="stat-card s-working"><div class="stat-value">${(summary?.working || 0).toLocaleString()}</div><div class="stat-label">Working</div></div>
    <div class="stat-card s-broken"><div class="stat-value">${(summary?.broken || 0).toLocaleString()}</div><div class="stat-label">Broken</div></div>
    <div class="stat-card s-redirect"><div class="stat-value">${(summary?.redirect || 0).toLocaleString()}</div><div class="stat-label">Redirects</div></div>
    <div class="stat-card s-timeout"><div class="stat-value">${(summary?.timeout || 0).toLocaleString()}</div><div class="stat-label">Timeouts</div></div>
    <div class="stat-card s-blocked"><div class="stat-value">${(summary?.blocked || 0).toLocaleString()}</div><div class="stat-label">Blocked</div></div>
    <div class="stat-card s-auth"><div class="stat-value">${(summary?.auth_required || 0).toLocaleString()}</div><div class="stat-label">Auth Required</div></div>
</div>

<!-- ── Status Distribution Donut + Timing ─────────── -->
<div class="two-col">
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#128202;</span> Status Distribution</div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body">
        <div class="donut-section">
            <div class="donut-wrap">
                ${buildDonutSVG(summary, total)}
                <div class="donut-center">
                    <div class="dc-val" style="color:${healthPct >= 80 ? 'var(--green)' : healthPct >= 50 ? 'var(--orange)' : 'var(--red)'}">${healthPct}%</div>
                    <div class="dc-label">Health</div>
                </div>
            </div>
            <div class="donut-legend">
                <div class="legend-item"><span class="legend-dot" style="background:var(--green)"></span><span class="legend-count">${(summary?.working||0).toLocaleString()}</span> Working</div>
                <div class="legend-item"><span class="legend-dot" style="background:var(--red)"></span><span class="legend-count">${(summary?.broken||0).toLocaleString()}</span> Broken</div>
                <div class="legend-item"><span class="legend-dot" style="background:var(--blue)"></span><span class="legend-count">${(summary?.redirect||0).toLocaleString()}</span> Redirects</div>
                <div class="legend-item"><span class="legend-dot" style="background:var(--orange)"></span><span class="legend-count">${(summary?.timeout||0).toLocaleString()}</span> Timeouts</div>
                <div class="legend-item"><span class="legend-dot" style="background:var(--purple)"></span><span class="legend-count">${(summary?.blocked||0).toLocaleString()}</span> Blocked</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f97316"></span><span class="legend-count">${(summary?.auth_required||0).toLocaleString()}</span> Auth Required</div>
            </div>
        </div>
    </div>
</div>

<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#9201;</span> Response Time Analysis</div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body">
        <div class="timing-grid">
            <div class="timing-stat"><div class="tv">${avgTime.toLocaleString()}<span style="font-size:0.75rem;font-weight:400">ms</span></div><div class="tl">Average</div></div>
            <div class="timing-stat"><div class="tv">${medianTime.toLocaleString()}<span style="font-size:0.75rem;font-weight:400">ms</span></div><div class="tl">Median</div></div>
            <div class="timing-stat"><div class="tv">${minTime.toLocaleString()}<span style="font-size:0.75rem;font-weight:400">ms</span></div><div class="tl">Fastest</div></div>
            <div class="timing-stat"><div class="tv">${maxTime.toLocaleString()}<span style="font-size:0.75rem;font-weight:400">ms</span></div><div class="tl">Slowest</div></div>
        </div>
    </div>
</div>
</div>

<!-- ── Domain Health ──────────────────────────────── -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#127760;</span> Domain Health Breakdown <span class="section-badge">${domainsSorted.length} domains</span></div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body" style="padding:0;">
        <div class="table-scroll" style="max-height:400px">
        <table>
            <thead><tr><th>Domain</th><th class="num">Total</th><th class="num">Working</th><th class="num">Broken</th><th class="num">Other</th><th class="num">Avg Time</th><th>Health</th></tr></thead>
            <tbody>${domainRowsHtml}</tbody>
        </table>
        </div>
    </div>
</div>

<!-- ── File Type + Error Patterns ─────────────────── -->
<div class="two-col">
${typesSorted.length > 0 ? `
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#128196;</span> File Type Distribution <span class="section-badge">${typesSorted.length} types</span></div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body">${typeChartHtml}</div>
</div>
` : ''}
${topErrors.length > 0 ? `
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#9888;</span> Top Error Patterns <span class="section-badge">${topErrors.length}</span></div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body" style="padding:0;">
        <table><thead><tr><th>Error Message</th><th class="num">Count</th></tr></thead><tbody>${errorRowsHtml}</tbody></table>
    </div>
</div>
` : ''}
</div>

${hasSheets ? `
<!-- ── Sheet Breakdown ────────────────────────────── -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#128203;</span> Sheet Breakdown <span class="section-badge">${Object.keys(sheetMap).length} sheets</span></div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body" style="padding:0;">
        <table>
            <thead><tr><th>Sheet</th><th class="num">Total</th><th class="num">Working</th><th class="num">Broken</th><th>Health</th></tr></thead>
            <tbody>${sheetRowsHtml}</tbody>
        </table>
    </div>
</div>
` : ''}

<!-- ── Full Results Table ─────────────────────────── -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <div class="section-title"><span>&#128279;</span> All Results <span class="section-badge">${total.toLocaleString()} links</span></div>
        <span class="section-toggle">&#9660;</span>
    </div>
    <div class="section-body">
        <div class="toolbar no-print">
            <input type="text" id="search-input" placeholder="Search URLs, messages, domains..." oninput="filterTable()">
            <select id="status-filter" onchange="filterTable()">
                <option value="">All Statuses</option>
                <option value="WORKING">Working</option>
                <option value="BROKEN">Broken / Invalid</option>
                <option value="REDIRECT">Redirect</option>
                <option value="TIMEOUT">Timeout</option>
                <option value="BLOCKED">Blocked</option>
            </select>
            <select id="domain-filter" onchange="filterTable()">
                <option value="">All Domains</option>
                ${domainsSorted.slice(0, 50).map(([d]) => `<option value="${escA(d)}">${esc(d)}</option>`).join('')}
            </select>
            <span class="result-count" id="result-count">${total.toLocaleString()} results</span>
        </div>
        <div class="table-scroll">
        <table id="results-table">
            <thead><tr>
                <th class="sortable" onclick="sortTable('status')">Status <span class="sort-arrow" id="sort-status"></span></th>
                <th class="sortable" onclick="sortTable('url')">URL <span class="sort-arrow" id="sort-url"></span></th>
                <th class="sortable num" onclick="sortTable('code')">Code <span class="sort-arrow" id="sort-code"></span></th>
                <th>Message</th>
                <th class="sortable num" onclick="sortTable('time')">Time <span class="sort-arrow" id="sort-time"></span></th>
                <th>Location</th>
            </tr></thead>
            <tbody id="results-body"></tbody>
        </table>
        </div>
    </div>
</div>
</div>

<div class="report-footer">
    <strong>AEGIS</strong> &mdash; Aerospace Engineering Governance &amp; Inspection System<br>
    Hyperlink Validation Report &middot; Generated ${new Date().toISOString()}
</div>

<button class="theme-toggle no-print" onclick="toggleTheme()" title="Toggle light/dark mode">&#9788;</button>

<script>
// ── Data ──────────────────────────────────────────
var DATA = ${rowsData};
var currentSort = { col: '', dir: 'asc' };
var SC = {WORKING:'${statusColors.WORKING}',BROKEN:'${statusColors.BROKEN}',INVALID:'${statusColors.INVALID}',REDIRECT:'${statusColors.REDIRECT}',TIMEOUT:'${statusColors.TIMEOUT}',BLOCKED:'${statusColors.BLOCKED}',MAILTO:'${statusColors.MAILTO}',EXTRACTED:'${statusColors.EXTRACTED}',UNKNOWN:'${statusColors.UNKNOWN}'};

function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function toggleSection(hdr) {
    hdr.parentElement.classList.toggle('collapsed');
}

function toggleTheme() {
    document.body.classList.toggle('light');
}

function filterTable() {
    var search = (document.getElementById('search-input').value || '').toLowerCase();
    var status = document.getElementById('status-filter').value;
    var domain = document.getElementById('domain-filter').value;
    var filtered = DATA.filter(function(r) {
        if (status) {
            if (status === 'BROKEN') { if (r.status !== 'BROKEN' && r.status !== 'INVALID') return false; }
            else if (r.status !== status) return false;
        }
        if (domain && r.domain !== domain) return false;
        if (search && r.url.toLowerCase().indexOf(search) === -1 && r.message.toLowerCase().indexOf(search) === -1 && r.domain.toLowerCase().indexOf(search) === -1 && (r.context||'').toLowerCase().indexOf(search) === -1) return false;
        return true;
    });
    if (currentSort.col) filtered = doSort(filtered, currentSort.col, currentSort.dir);
    renderRows(filtered);
    document.getElementById('result-count').textContent = filtered.length.toLocaleString() + ' results';
}

function sortTable(col) {
    if (currentSort.col === col) {
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.col = col;
        currentSort.dir = 'asc';
    }
    document.querySelectorAll('.sort-arrow').forEach(function(el) { el.textContent = ''; });
    var arrow = document.getElementById('sort-' + col);
    if (arrow) arrow.textContent = currentSort.dir === 'asc' ? ' \\u25B2' : ' \\u25BC';
    filterTable();
}

function doSort(arr, col, dir) {
    return arr.slice().sort(function(a, b) {
        var va = a[col] || '', vb = b[col] || '';
        if (col === 'time' || col === 'code') {
            va = Number(va) || 0; vb = Number(vb) || 0;
        }
        if (va < vb) return dir === 'asc' ? -1 : 1;
        if (va > vb) return dir === 'asc' ? 1 : -1;
        return 0;
    });
}

function renderRows(rows) {
    var tbody = document.getElementById('results-body');
    // Batch render for performance with large datasets
    var limit = Math.min(rows.length, 500);
    var html = '';
    for (var i = 0; i < limit; i++) {
        var r = rows[i];
        var s = r.status;
        var c = SC[s] || '#6b7280';
        html += '<tr>'
            + '<td><span class="status-badge" style="background:' + c + '20;color:' + c + '">' + s + '</span></td>'
            + '<td class="url-cell"><a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.url) + '</a>'
            + (r.context ? '<div class="ctx-info">' + esc(r.context) + '</div>' : '')
            + '</td>'
            + '<td class="num">' + (r.code || '-') + '</td>'
            + '<td>' + esc(r.message) + '</td>'
            + '<td class="num">' + (r.time ? r.time + 'ms' : '-') + '</td>'
            + '<td>' + esc(r.location) + '</td>'
            + '</tr>';
    }
    if (rows.length > limit) {
        html += '<tr><td colspan="6" style="text-align:center;padding:1rem;color:var(--text-dim);font-style:italic">Showing ' + limit + ' of ' + rows.length.toLocaleString() + ' results. Use filters to narrow down.</td></tr>';
    }
    tbody.innerHTML = html;
}

// Initial render
filterTable();
</script>
</body>
</html>`;
    }

    /**
     * Build SVG donut chart for status distribution.
     */
    function buildDonutSVG(summary, total) {
        if (!total || total === 0) return '<svg viewBox="0 0 200 200"><circle cx="100" cy="100" r="86" stroke="#30363d" /></svg>';

        const slices = [
            { count: summary?.working || 0, color: '#22c55e' },
            { count: summary?.broken || 0, color: '#ef4444' },
            { count: summary?.redirect || 0, color: '#3b82f6' },
            { count: summary?.timeout || 0, color: '#f59e0b' },
            { count: summary?.blocked || 0, color: '#8b5cf6' },
            { count: summary?.auth_required || 0, color: '#f97316' }
        ].filter(s => s.count > 0);

        const circumference = 2 * Math.PI * 86; // radius=86
        let offset = 0;
        const circles = slices.map(s => {
            const pct = s.count / total;
            const dash = pct * circumference;
            const circle = `<circle cx="100" cy="100" r="86" stroke="${s.color}" stroke-dasharray="${dash} ${circumference - dash}" stroke-dashoffset="${-offset}" />`;
            offset += dash;
            return circle;
        }).join('');

        return `<svg viewBox="0 0 200 200">${circles}</svg>`;
    }

    function escapeHtmlContent(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function escapeHtmlAttr(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    /**
     * Set results directly (for Excel/DOCX local processing).
     * @param {Array} results - Array of result objects
     * @param {Object} summary - Optional summary object
     */
    function setLocalResults(results, summary = null) {
        state.results = results;
        state.summary = summary || generateLocalSummary(results);
        state.status = 'complete';
        state.jobId = null; // No server job for local results
        emit('onChange', { ...state });
    }

    // ==========================================================================
    // GETTERS
    // ==========================================================================

    function getJobId() { return state.jobId; }
    function getStatus() { return state.status; }
    function getProgress() { return { ...state.progress }; }
    function getResults() { return [...state.results]; }
    function getSummary() { return state.summary ? { ...state.summary } : null; }
    function getHistory() { return [...state.history]; }
    function getCapabilities() { return state.capabilities; }

    // ==========================================================================
    // EVENTS
    // ==========================================================================

    function onChange(callback) {
        callbacks.onChange.push(callback);
        return () => {
            const idx = callbacks.onChange.indexOf(callback);
            if (idx > -1) callbacks.onChange.splice(idx, 1);
        };
    }

    function onProgress(callback) {
        callbacks.onProgress.push(callback);
        return () => {
            const idx = callbacks.onProgress.indexOf(callback);
            if (idx > -1) callbacks.onProgress.splice(idx, 1);
        };
    }

    function onComplete(callback) {
        callbacks.onComplete.push(callback);
        return () => {
            const idx = callbacks.onComplete.indexOf(callback);
            if (idx > -1) callbacks.onComplete.splice(idx, 1);
        };
    }

    function onError(callback) {
        callbacks.onError.push(callback);
        return () => {
            const idx = callbacks.onError.indexOf(callback);
            if (idx > -1) callbacks.onError.splice(idx, 1);
        };
    }

    // ==========================================================================
    // EXCLUSIONS
    // ==========================================================================

    function getExclusions() {
        return [...state.exclusions];
    }

    function addExclusion(exclusion) {
        const exc = {
            pattern: exclusion.pattern,
            match_type: exclusion.match_type || 'contains',
            reason: exclusion.reason || '',
            treat_as_valid: exclusion.treat_as_valid !== false,
            created_at: new Date().toISOString()
        };
        state.exclusions.push(exc);
        saveExclusionsToStorage();
        emit('onChange', { ...state });

        // v4.6.2: Also persist to server database for cross-session persistence
        persistExclusionToServer(exc);
    }

    /**
     * v4.6.2: Persist exclusion to server database.
     * Fire-and-forget — localStorage is the primary store, server is backup.
     */
    async function persistExclusionToServer(exclusion) {
        try {
            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;
            await fetch('/api/hyperlink-validator/exclusions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {})
                },
                body: JSON.stringify({
                    pattern: exclusion.pattern,
                    match_type: exclusion.match_type,
                    reason: exclusion.reason,
                    treat_as_valid: exclusion.treat_as_valid
                })
            });
            console.log('[TWR HVState] Exclusion persisted to server:', exclusion.pattern);
        } catch (e) {
            console.warn('[TWR HVState] Failed to persist exclusion to server:', e);
        }
    }

    function removeExclusion(index) {
        if (index >= 0 && index < state.exclusions.length) {
            const removed = state.exclusions[index];
            state.exclusions.splice(index, 1);
            saveExclusionsToStorage();
            emit('onChange', { ...state });

            // v5.9.35: Also delete from server database (Bug fix: was localStorage-only)
            if (removed && removed.pattern) {
                deleteExclusionFromServer(removed);
            }
        }
    }

    /**
     * v5.9.35: Delete exclusion from server database.
     * Fire-and-forget — localStorage is the primary store.
     */
    async function deleteExclusionFromServer(exclusion) {
        try {
            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;

            // Find the exclusion by pattern to get its server ID
            const response = await fetch('/api/hyperlink-validator/exclusions?active_only=false', {
                credentials: 'same-origin'
            });
            const data = await response.json();

            if (data.success && data.exclusions) {
                const match = data.exclusions.find(e =>
                    e.pattern === exclusion.pattern && e.match_type === exclusion.match_type
                );
                if (match && match.id) {
                    await fetch(`/api/hyperlink-validator/exclusions/${match.id}`, {
                        method: 'DELETE',
                        headers: {
                            ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {})
                        },
                        credentials: 'same-origin'
                    });
                    console.log('[TWR HVState] Exclusion deleted from server:', exclusion.pattern);
                }
            }
        } catch (e) {
            console.warn('[TWR HVState] Failed to delete exclusion from server:', e);
        }
    }

    function clearExclusions() {
        state.exclusions = [];
        saveExclusionsToStorage();
        emit('onChange', { ...state });
    }

    function saveExclusionsToStorage() {
        try {
            localStorage.setItem('hv_exclusions', JSON.stringify(state.exclusions));
        } catch (e) {
            console.warn('[TWR HVState] Failed to save exclusions to localStorage:', e);
        }
    }

    function loadExclusionsFromStorage() {
        try {
            const saved = localStorage.getItem('hv_exclusions');
            if (saved) {
                state.exclusions = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('[TWR HVState] Failed to load exclusions from localStorage:', e);
        }
    }

    /**
     * Set exclusions from external source (e.g., LinkHistory module sync).
     * @param {Array} exclusions - Array of exclusion objects
     */
    function setExclusions(exclusions) {
        if (!Array.isArray(exclusions)) return;

        state.exclusions = exclusions.map(e => ({
            pattern: e.pattern,
            match_type: e.match_type || 'contains',
            reason: e.reason || '',
            treat_as_valid: e.treat_as_valid !== false
        }));

        // Also save to localStorage as backup
        saveExclusionsToStorage();
        emit('onChange', { ...state });
        console.log('[TWR HVState] Exclusions synced:', state.exclusions.length, 'rules');
    }

    /**
     * Record a completed scan to persistent history via the API.
     * @param {string} sourceType - 'paste', 'file', 'excel', 'docx'
     * @param {string} sourceName - Optional filename or description
     * @param {Array} results - Array of result objects
     * @param {Object} summary - Summary statistics
     */
    async function recordScanToHistory(sourceType, sourceName, results, summary) {
        if (!results || results.length === 0) return;

        try {
            const scanSummary = summary || generateLocalSummary(results);

            // Prepare result URLs for storage (just the essential data)
            const resultUrls = results.map(r => ({
                url: r.url,
                status: r.status,
                status_code: r.status_code,
                message: r.message,
                response_time_ms: r.response_time_ms
            }));

            // BUG-M19 FIX: Include all summary fields including excluded and duration
            await apiRequest('/history/record', {
                method: 'POST',
                body: JSON.stringify({
                    source_type: sourceType || 'paste',
                    source_name: sourceName || '',
                    total_urls: results.length,
                    summary: {
                        working: scanSummary.working || 0,
                        broken: scanSummary.broken || 0,
                        redirect: scanSummary.redirect || 0,
                        timeout: scanSummary.timeout || 0,
                        blocked: scanSummary.blocked || 0,
                        unknown: scanSummary.unknown || 0,
                        excluded: scanSummary.excluded || 0
                    },
                    validation_mode: state.mode || 'validator',
                    scan_depth: state.depth || 'standard',
                    duration_ms: state.duration || 0,
                    results: resultUrls
                })
            });

            console.log('[TWR HVState] Scan recorded to history');

            // Notify LinkHistory if available to refresh its display
            if (window.LinkHistory && typeof window.LinkHistory.refreshScans === 'function') {
                window.LinkHistory.refreshScans();
            }
        } catch (e) {
            console.warn('[TWR HVState] Failed to record scan to history:', e);
            // Non-critical failure, don't throw
        }
    }

    // ==========================================================================
    // CLEANUP
    // ==========================================================================

    function cleanup() {
        stopPolling();
        callbacks.onChange = [];
        callbacks.onProgress = [];
        callbacks.onComplete = [];
        callbacks.onError = [];
    }

    // ==========================================================================
    // PUBLIC API
    // ==========================================================================

    return {
        // Initialization
        init,
        reset,
        isInitialized,

        // Validation
        startValidation,
        cancelValidation,
        pollJobStatus,

        // Getters
        getJobId,
        getStatus,
        getProgress,
        getResults,
        getSummary,
        getFilteredResults,
        getHistory,
        getCapabilities,
        getExportUrl,
        exportLocalResults,
        setLocalResults,

        // Filtering & Sorting
        setFilter,
        getFilters,
        setSortColumn,

        // History
        loadHistory,
        loadHistoricalRun,

        // Exclusions
        getExclusions,
        addExclusion,
        removeExclusion,
        clearExclusions,
        setExclusions,

        // Scan History
        recordScanToHistory,

        // Events
        onChange,
        onProgress,
        onComplete,
        onError,

        // Cleanup
        cleanup
    };

})();
