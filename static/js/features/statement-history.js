/**
 * Statement History Viewer
 * ========================
 * v4.2.0: Full-featured Statement Forge history viewer with:
 * - Statement extraction history across scans
 * - Document viewer with statement highlighting
 * - Side-by-side scan comparison with diff highlighting
 * - Highlight-to-create statement functionality
 * - Directive trend charts
 * - Role coverage analysis
 *
 * Module Pattern: IIFE exposed via TWR.StatementHistory
 */

window.TWR = window.TWR || {};

TWR.StatementHistory = (function() {
    'use strict';

    const VERSION = '4.3.0';
    const LOG_PREFIX = '[SF History]';

    // =========================================================================
    // STATE
    // =========================================================================

    const State = {
        isOpen: false,
        modal: null,
        documentId: null,
        scanId: null,
        documentName: '',
        documentText: '',
        htmlPreview: '',       // v4.3.0: HTML preview from mammoth/pymupdf4llm
        docFormat: 'text',     // v4.3.0: 'html' | 'text' — determined by API response
        history: [],           // Array of scan summaries
        currentStatements: [], // Statements for current scan
        currentView: 'overview', // overview | viewer | compare | create
        compareScans: { left: null, right: null },
        charts: {},
        isLightMode: false,
        navStack: [],
        selection: null,       // Text selection for highlight-to-create
        currentStmtIndex: -1,  // Index in filtered statement list
        filteredStatements: [], // Current filter subset (non-header)
        activeFilter: 'all',   // Active directive filter
        editMode: false,        // Detail panel edit mode
        compareMode: false,           // In compare viewer?
        compareDiff: null,            // Raw diff from API
        compareScanInfo: { newer: null, older: null },
        mergedStatements: [],         // Unified list with _diff_status
        activeDiffFilter: 'all',      // 'all'|'added'|'removed'|'modified'|'unchanged'
        // v4.4.0: Bulk editing
        selectedStatements: new Set(), // Selected statement IDs for bulk ops
        bulkMode: false,               // Bulk edit mode active
        // v4.6.0: Review status filtering
        activeReviewFilter: 'all'      // 'all'|'pending'|'reviewed'|'rejected'|'unchanged'
    };

    // =========================================================================
    // UTILITIES
    // =========================================================================

    function log(msg, level = 'log') {
        console[level](LOG_PREFIX, msg);
    }

    // v4.5.1: String-based escapeHtml — avoids DOM allocation on every call
    const _escapeMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    const _escapeRe = /[&<>"']/g;
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(_escapeRe, ch => _escapeMap[ch]);
    }

    function detectTheme() {
        State.isLightMode = !document.body.classList.contains('dark-mode');
    }

    function getCSRF() {
        return window.CSRF_TOKEN ||
               document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    async function apiFetch(url, options = {}) {
        const defaults = {
            headers: { 'Content-Type': 'application/json' }
        };
        if (options.method && options.method !== 'GET') {
            defaults.headers['X-CSRF-Token'] = getCSRF();
        }
        const res = await fetch(url, { ...defaults, ...options });
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return res.json();
    }

    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        const d = new Date(dateStr);
        return d.toLocaleDateString() + ' ' +
               d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function formatDateShort(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return (d.getMonth() + 1) + '/' + d.getDate();
    }

    // Throttle: prevents rapid-fire calls from freezing the UI
    let _navThrottleTimer = null;
    const NAV_THROTTLE_MS = 80; // Min interval between statement navigations
    let _lastNavTime = 0; // Track rapid scroll to switch to instant behavior

    // v4.5.1: Scoped icon refresh — pass a container node to avoid scanning entire DOM
    function refreshIcons(scopeNode) {
        if (typeof lucide !== 'undefined') {
            try {
                if (scopeNode) {
                    lucide.createIcons({ nodes: [scopeNode] });
                } else {
                    lucide.createIcons();
                }
            } catch (e) { /* ok */ }
        }
    }

    function updateFooterShortcuts() {
        const shortcuts = State.modal?.querySelector('.sfh-shortcuts');
        if (!shortcuts) return;
        const base = '<span><kbd>Esc</kbd> Close</span><span><kbd>←</kbd> Back</span>';
        if (State.currentView === 'compare') {
            shortcuts.innerHTML = base +
                '<span><kbd>↑↓</kbd> Nav</span>' +
                '<span><kbd>e</kbd> Edit</span>' +
                '<span><kbd>a</kbd> Added</span>' +
                '<span><kbd>r</kbd> Removed</span>' +
                '<span><kbd>m</kbd> Modified</span>';
        } else if (State.currentView === 'viewer') {
            shortcuts.innerHTML = base +
                '<span><kbd>↑↓</kbd> Nav</span>' +
                '<span><kbd>e</kbd> Edit</span>';
        } else {
            shortcuts.innerHTML = base;
        }
    }

    function destroyCharts() {
        Object.values(State.charts).forEach(c => {
            try { c.destroy(); } catch (e) { /* ok */ }
        });
        State.charts = {};
    }

    // =========================================================================
    // MODAL CREATION
    // =========================================================================

    function createModal() {
        if (State.modal) return State.modal;

        detectTheme();

        const modal = document.createElement('div');
        modal.id = 'sfh-modal-overlay';
        modal.className = 'sfh-overlay' + (State.isLightMode ? ' sfh-light' : '');
        modal.innerHTML = `
            <div class="sfh-modal">
                <div class="sfh-header">
                    <div class="sfh-nav-controls">
                        <button class="sfh-nav-btn sfh-back" title="Go Back">
                            <i data-lucide="arrow-left" style="width:16px;height:16px"></i>
                        </button>
                        <button class="sfh-nav-btn sfh-home" title="Overview">
                            <i data-lucide="home" style="width:16px;height:16px"></i>
                        </button>
                    </div>
                    <div class="sfh-breadcrumbs">
                        <span class="sfh-breadcrumb sfh-current">Statement History</span>
                    </div>
                    <div class="sfh-header-actions">
                        <button class="sfh-close-btn" title="Close (Esc)">&times;</button>
                    </div>
                </div>
                <div class="sfh-body">
                    <div class="sfh-content">
                        <div class="sfh-loading">
                            <div class="sfh-spinner"></div>
                            <p>Loading statement history...</p>
                        </div>
                    </div>
                </div>
                <div class="sfh-footer">
                    <div class="sfh-shortcuts">
                        <span><kbd>Esc</kbd> Close</span>
                        <span><kbd>←</kbd> Back</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;

        // Event listeners
        modal.querySelector('.sfh-close-btn').addEventListener('click', close);
        modal.querySelector('.sfh-back').addEventListener('click', goBack);
        modal.querySelector('.sfh-home').addEventListener('click', () => showOverview());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close();
        });

        const keyHandler = (e) => {
            if (!State.isOpen) return;
            const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);

            if (e.key === 'Escape') {
                if (State.editMode) {
                    // Exit edit mode instead of closing modal
                    const stmt = State.filteredStatements[State.currentStmtIndex];
                    if (stmt) {
                        const origIdx = State.currentStatements.indexOf(stmt);
                        exitEditMode(stmt, origIdx);
                    }
                    return;
                }
                close();
            }
            if (e.key === 'ArrowLeft' && !isTyping) goBack();

            // Statement navigation in viewer and compare (↑/↓ arrows)
            if ((State.currentView === 'viewer' || State.currentView === 'compare') && !isTyping && !State.editMode) {
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    navigateToStatement('prev');
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    navigateToStatement('next');
                } else if (e.key === 'e' && State.currentStmtIndex >= 0) {
                    // 'e' to edit current statement (only non-removed in compare)
                    const stmt = State.filteredStatements[State.currentStmtIndex];
                    if (stmt && !(State.compareMode && stmt._diff_status === 'removed')) {
                        const origIdx = State.currentStatements.indexOf(stmt);
                        enterEditMode(stmt, origIdx);
                    }
                } else if (State.compareMode) {
                    // Compare-only shortcuts: a/r/m jump to next added/removed/modified
                    if (e.key === 'a') navigateToNextDiffStatus('added');
                    else if (e.key === 'r') navigateToNextDiffStatus('removed');
                    else if (e.key === 'm') navigateToNextDiffStatus('modified');
                }
            }
        };
        document.addEventListener('keydown', keyHandler);

        refreshIcons(modal);
        return modal;
    }

    // =========================================================================
    // OPEN / CLOSE / NAVIGATE
    // =========================================================================

    async function open(documentId, scanId, documentName) {
        if (State.isOpen) return;
        log(`Opening for document ${documentId}, scan ${scanId}`);

        State.isOpen = true;
        State.documentId = documentId;
        State.scanId = scanId;
        State.documentName = documentName || '';
        State.documentText = '';
        State.htmlPreview = '';
        State.docFormat = 'text';
        State.navStack = [];
        State.currentView = 'overview';

        if (!State.modal) createModal();
        detectTheme();
        if (State.isLightMode) {
            State.modal.classList.add('sfh-light');
        } else {
            State.modal.classList.remove('sfh-light');
        }

        State.modal.style.display = '';  // Restore display in case close() hid it
        State.modal.classList.add('sfh-visible');
        document.body.style.overflow = 'hidden';

        await loadHistoryData();
    }

    function close() {
        if (!State.isOpen) return;
        log('Closing');
        State.isOpen = false;
        if (State.modal) {
            State.modal.classList.remove('sfh-visible');
            // Ensure modal is fully hidden after CSS transition
            setTimeout(() => {
                if (!State.isOpen && State.modal) {
                    State.modal.style.display = 'none';
                }
            }, 350);
        }
        document.body.style.overflow = '';
        destroyCharts();
        State.selection = null;
    }

    function goBack() {
        if (State.navStack.length > 0) {
            const prev = State.navStack.pop();
            State.currentView = prev.view;
            if (prev.view === 'overview') showOverview(true);
            else if (prev.view === 'viewer') showDocumentViewer(prev.scanId, true);
            else if (prev.view === 'compare') showCompareViewer(prev.leftId, prev.rightId, true);
        }
    }

    function pushNav(view, extra = {}) {
        State.navStack.push({ view: State.currentView, scanId: State.scanId, ...extra });
        State.currentView = view;
    }

    function updateBreadcrumb(text) {
        const bc = State.modal?.querySelector('.sfh-breadcrumbs');
        if (bc) bc.innerHTML = `<span class="sfh-breadcrumb sfh-current">${escapeHtml(text)}</span>`;
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async function loadHistoryData() {
        const content = State.modal.querySelector('.sfh-content');
        content.innerHTML = '<div class="sfh-loading"><div class="sfh-spinner"></div><p>Loading history...</p></div>';

        try {
            const data = await apiFetch(`/api/statement-forge/history/${State.documentId}`);
            if (data.success) {
                State.history = data.data || [];
                showOverview();
            } else {
                content.innerHTML = `<div class="sfh-empty"><p>No statement history available for this document.</p></div>`;
            }
        } catch (err) {
            log('Error loading history: ' + err, 'error');
            content.innerHTML = `<div class="sfh-error"><p>Failed to load history. ${escapeHtml(err.message)}</p></div>`;
        }
    }

    async function loadScanStatements(scanId) {
        try {
            const data = await apiFetchWithTimeout(`/api/statement-forge/scan/${scanId}`, {}, 15000);
            if (data.success) return data.data || [];
        } catch (e) {
            log('Error loading statements: ' + e, 'error');
        }
        return [];
    }

    async function loadDocumentText(scanId) {
        if (State.documentText) return State.documentText;
        try {
            const params = new URLSearchParams();
            if (scanId) params.set('scan_id', scanId);
            else if (State.documentName) params.set('filename', State.documentName);
            else if (State.documentId) params.set('doc_id', State.documentId);
            const data = await apiFetchWithTimeout(`/api/scan-history/document-text?${params}`, {}, 15000);
            if (data.success && data.text) {
                State.documentText = data.text;
                // v4.3.0: Capture HTML preview if available
                State.htmlPreview = data.html_preview || '';
                State.docFormat = data.format || (data.html_preview ? 'html' : 'text');
                return data.text;
            }
        } catch (e) {
            log('Error loading document text: ' + e, 'error');
        }
        return '';
    }

    async function apiFetchWithTimeout(url, options = {}, timeoutMs = 15000) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
            return await apiFetch(url, { ...options, signal: controller.signal });
        } finally {
            clearTimeout(timer);
        }
    }

    async function loadTrends() {
        try {
            const data = await apiFetch(`/api/statement-forge/trends/${State.documentId}`);
            if (data.success) return data.data;
        } catch (e) { log('Trends error: ' + e, 'error'); }
        return { timeline: [], role_frequency: [], data_points: 0 };
    }

    async function loadComparison(scanId1, scanId2) {
        try {
            const data = await apiFetch(`/api/statement-forge/compare/${scanId1}/${scanId2}`);
            if (data.success) return data.data;
        } catch (e) { log('Comparison error: ' + e, 'error'); }
        return null;
    }

    // =========================================================================
    // VIEW: OVERVIEW
    // =========================================================================

    async function showOverview(isBack = false) {
        if (!isBack) State.navStack = [];
        State.currentView = 'overview';
        State.compareMode = false;
        updateBreadcrumb('Statement History');

        const content = State.modal.querySelector('.sfh-content');
        const history = State.history;

        if (!history.length) {
            content.innerHTML = `
                <div class="sfh-empty">
                    <i data-lucide="file-search" style="width:48px;height:48px;opacity:0.4"></i>
                    <h3>No Statement History</h3>
                    <p>Run a document scan to start tracking statement extraction history.</p>
                </div>`;
            refreshIcons(content);
            return;
        }

        const latest = history[0];
        const totalScans = history.length;
        const totalStmts = latest.statement_count;
        const totalDirectives = Object.values(latest.directive_counts || {}).reduce((a, b) => a + b, 0);

        // Calculate trend
        let trendHtml = '';
        if (history.length >= 2) {
            const prev = history[1];
            const diff = latest.statement_count - prev.statement_count;
            if (diff > 0) trendHtml = `<span class="sfh-trend sfh-trend-up">+${diff}</span>`;
            else if (diff < 0) trendHtml = `<span class="sfh-trend sfh-trend-down">${diff}</span>`;
            else trendHtml = `<span class="sfh-trend sfh-trend-flat">±0</span>`;
        }

        content.innerHTML = `
            <div class="sfh-overview">
                <!-- Hero Stats -->
                <div class="sfh-hero">
                    <div class="sfh-hero-stat sfh-clickable" data-action="view-latest">
                        <div class="sfh-hero-icon"><i data-lucide="file-text" style="width:24px;height:24px"></i></div>
                        <div class="sfh-hero-value">${totalStmts} ${trendHtml}</div>
                        <div class="sfh-hero-label">Statements (Latest)</div>
                    </div>
                    <div class="sfh-hero-stat">
                        <div class="sfh-hero-icon"><i data-lucide="history" style="width:24px;height:24px"></i></div>
                        <div class="sfh-hero-value">${totalScans}</div>
                        <div class="sfh-hero-label">Scans Recorded</div>
                    </div>
                    <div class="sfh-hero-stat">
                        <div class="sfh-hero-icon"><i data-lucide="shield-check" style="width:24px;height:24px"></i></div>
                        <div class="sfh-hero-value">${totalDirectives}</div>
                        <div class="sfh-hero-label">Directive Statements</div>
                    </div>
                    <div class="sfh-hero-stat">
                        <div class="sfh-hero-icon"><i data-lucide="users" style="width:24px;height:24px"></i></div>
                        <div class="sfh-hero-value">${latest.unique_roles}</div>
                        <div class="sfh-hero-label">Unique Roles</div>
                    </div>
                </div>

                <!-- v4.4.0: Global Statement Search -->
                <div class="sfh-search-bar">
                    <div class="sfh-search-input-wrap">
                        <i data-lucide="search" style="width:16px;height:16px"></i>
                        <input type="text" class="sfh-search-input" placeholder="Search statements across all scans..." id="sfh-global-search">
                    </div>
                    <div class="sfh-search-results" id="sfh-search-results" style="display:none;"></div>
                </div>

                <!-- v4.6.0: Review Status & Data Management -->
                <div class="sfh-review-panel" id="sfh-review-panel" style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
                    <div class="sfh-review-stat" style="flex:1;min-width:140px;padding:12px 16px;background:var(--bg-surface);border-radius:var(--radius-md);border:1px solid var(--border-default);">
                        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">Review Progress</div>
                        <div id="sfh-review-progress" style="font-size:13px;color:var(--text-primary);">Loading...</div>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <button class="sfh-btn sfh-btn-sm sfh-btn-outline" id="sfh-btn-find-dupes" title="Find and clean up duplicate statements">
                            <i data-lucide="copy-minus" style="width:14px;height:14px"></i> Duplicates
                        </button>
                        <button class="sfh-btn sfh-btn-sm sfh-btn-outline" id="sfh-btn-bulk-review" title="Review all pending statements">
                            <i data-lucide="check-check" style="width:14px;height:14px"></i> Bulk Review
                        </button>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="sfh-charts-row">
                    <div class="sfh-chart-card">
                        <h4>Statement Trend</h4>
                        <div class="sfh-chart-wrap">
                            <canvas id="sfh-trend-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                    <div class="sfh-chart-card">
                        <h4>Directive Distribution</h4>
                        <div class="sfh-chart-wrap">
                            <canvas id="sfh-directive-chart" width="300" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Scan Timeline -->
                <div class="sfh-section">
                    <div class="sfh-section-header">
                        <h4>Scan Timeline</h4>
                        <span class="sfh-section-badge">${totalScans} scans</span>
                    </div>
                    <div class="sfh-timeline">
                        ${history.map((scan, idx) => {
                            const dc = scan.directive_counts || {};
                            const prevScan = history[idx + 1];
                            let diffBadge = '';
                            if (prevScan) {
                                const d = scan.statement_count - prevScan.statement_count;
                                if (d > 0) diffBadge = `<span class="sfh-diff-badge sfh-diff-added">+${d}</span>`;
                                else if (d < 0) diffBadge = `<span class="sfh-diff-badge sfh-diff-removed">${d}</span>`;
                            }
                            return `
                            <div class="sfh-timeline-item" data-scan-id="${scan.scan_id}">
                                <div class="sfh-timeline-dot"></div>
                                <div class="sfh-timeline-content">
                                    <div class="sfh-timeline-header">
                                        <span class="sfh-timeline-date">${formatDate(scan.scan_time)}</span>
                                        <span class="sfh-timeline-count">${scan.statement_count} statements ${diffBadge}</span>
                                    </div>
                                    <div class="sfh-timeline-meta">
                                        <span class="sfh-directive-pill sfh-shall">Shall: ${dc.shall || 0}</span>
                                        <span class="sfh-directive-pill sfh-must">Must: ${dc.must || 0}</span>
                                        <span class="sfh-directive-pill sfh-will">Will: ${dc.will || 0}</span>
                                        <span class="sfh-directive-pill sfh-should">Should: ${dc.should || 0}</span>
                                        <span class="sfh-meta-sep">|</span>
                                        <span>${scan.unique_roles} roles</span>
                                        <span>${scan.section_count} sections</span>
                                    </div>
                                    <div class="sfh-timeline-actions">
                                        <button class="sfh-btn sfh-btn-sm" data-action="view-scan" data-scan-id="${scan.scan_id}" title="View statements in document">
                                            <i data-lucide="eye" style="width:14px;height:14px"></i> View
                                        </button>
                                        ${idx < history.length - 1 ? `
                                        <button class="sfh-btn sfh-btn-sm sfh-btn-outline" data-action="compare-scan"
                                                data-scan-left="${scan.scan_id}" data-scan-right="${history[idx + 1].scan_id}"
                                                title="Compare with previous scan">
                                            <i data-lucide="git-compare" style="width:14px;height:14px"></i> Compare
                                        </button>` : ''}
                                    </div>
                                </div>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;

        // Event delegation
        content.addEventListener('click', handleOverviewClick);

        // v4.4.0: Wire global search
        const searchInput = document.getElementById('sfh-global-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                handleGlobalSearch(e.target.value.trim());
            });
        }

        refreshIcons(content);
        updateFooterShortcuts();
        await renderCharts();

        // v4.6.0: Load review stats
        loadReviewStats();

        // v4.6.0: Wire duplicate cleanup button
        const dupesBtn = document.getElementById('sfh-btn-find-dupes');
        if (dupesBtn) {
            dupesBtn.addEventListener('click', showDuplicateCleanup);
        }
        // v4.6.0: Wire bulk review button
        const bulkRevBtn = document.getElementById('sfh-btn-bulk-review');
        if (bulkRevBtn) {
            bulkRevBtn.addEventListener('click', showBulkReviewDialog);
        }
    }

    // v4.6.0: Load and display review statistics
    async function loadReviewStats() {
        const el = document.getElementById('sfh-review-progress');
        if (!el) return;
        try {
            const data = await apiFetch('/api/scan-history/statements/review-stats');
            if (data.success && data.data) {
                const s = data.data;
                const reviewedPct = s.total > 0 ? Math.round((s.reviewed / s.total) * 100) : 0;
                el.innerHTML = AEGIS.StatementReviewLookup
                    ? AEGIS.StatementReviewLookup.getSummary(s) || `${s.total} total`
                    : `${s.reviewed}/${s.total} reviewed (${reviewedPct}%)`;
            } else {
                el.textContent = 'No data';
            }
        } catch (e) {
            el.textContent = 'Error loading stats';
            log('Review stats error: ' + e, 'error');
        }
    }

    // v4.6.0: Show duplicate cleanup dialog
    async function showDuplicateCleanup() {
        try {
            const data = await apiFetch('/api/scan-history/statements/duplicates');
            if (!data.success) {
                showToast('error', data.error || 'Failed to find duplicates');
                return;
            }
            if (!data.groups || data.groups.length === 0) {
                showToast('info', 'No duplicate statements found');
                return;
            }

            const msg = `Found ${data.total_groups} duplicate groups (${data.total_duplicates} extra copies).\n\n` +
                `Top duplicates:\n` +
                data.groups.slice(0, 5).map(g =>
                    `  ${g.count}x: "${(g.sample_desc || '').substring(0, 60)}..."`
                ).join('\n') +
                `\n\nClean up duplicates? (Keeps the latest copy of each statement)`;

            if (!confirm(msg)) return;

            const csrfToken = window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
            const resp = await fetch('/api/scan-history/statements/deduplicate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ keep: 'latest' })
            });
            const result = await resp.json();
            if (result.success) {
                showToast('success', `Removed ${result.deleted} duplicate statements`);
                if (AEGIS.StatementReviewLookup) AEGIS.StatementReviewLookup.invalidate();
                loadReviewStats();
            } else {
                showToast('error', result.error || 'Deduplication failed');
            }
        } catch (e) {
            showToast('error', 'Error: ' + e.message);
        }
    }

    // v4.6.0: Show bulk review dialog
    async function showBulkReviewDialog() {
        try {
            const data = await apiFetch('/api/scan-history/statements/review-stats');
            if (!data.success || !data.data) {
                showToast('error', 'Failed to load review stats');
                return;
            }
            const s = data.data;
            if (s.pending === 0) {
                showToast('info', 'All statements have been reviewed');
                return;
            }

            const action = prompt(
                `${s.pending} statements are pending review.\n\n` +
                `Enter action:\n` +
                `  "approve" - Mark all pending as reviewed\n` +
                `  "reject"  - Mark all pending as rejected\n` +
                `  (Cancel to abort)`
            );
            if (!action) return;

            const review_status = action.toLowerCase().startsWith('reject') ? 'rejected' : 'reviewed';
            const csrfToken = window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';

            // We need to get all pending statement IDs — use a search query
            const searchData = await apiFetch('/api/scan-history/statements/search?limit=500');
            if (!searchData.success || !searchData.data) {
                showToast('error', 'Failed to load statements');
                return;
            }

            // Filter to pending
            const pendingIds = searchData.data
                .filter(s => !s.review_status || s.review_status === 'pending')
                .map(s => ({ id: s.id, review_status }));

            if (pendingIds.length === 0) {
                showToast('info', 'No pending statements found in results');
                return;
            }

            const resp = await fetch('/api/scan-history/statements/batch-review', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ updates: pendingIds })
            });
            const result = await resp.json();
            if (result.success) {
                showToast('success', `${result.updated} statements marked as ${review_status}`);
                if (AEGIS.StatementReviewLookup) AEGIS.StatementReviewLookup.invalidate();
                loadReviewStats();
            } else {
                showToast('error', result.error || 'Batch review failed');
            }
        } catch (e) {
            showToast('error', 'Error: ' + e.message);
        }
    }

    // v4.6.0: Handle single statement review action
    async function handleReviewAction(stmtId, newStatus, stmt, idx) {
        try {
            const csrfToken = window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
            const resp = await fetch(`/api/scan-history/statements/${stmtId}/review`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ review_status: newStatus })
            });
            const result = await resp.json();
            if (result.success) {
                // Update local state
                stmt.review_status = newStatus;
                if (AEGIS.StatementReviewLookup) AEGIS.StatementReviewLookup.invalidate();
                showToast('success', `Statement marked as ${newStatus}`);
                // Re-render detail panel to show updated badge
                State.filteredStatements = getFilteredStatements();
                showStatementDetail(stmt, idx);
            } else {
                showToast('error', result.error || 'Review update failed');
            }
        } catch (e) {
            showToast('error', 'Error: ' + e.message);
        }
    }

    // v4.4.0: Global statement search with debounce
    let _searchTimer = null;
    function handleGlobalSearch(query) {
        if (_searchTimer) clearTimeout(_searchTimer);
        const resultsDiv = document.getElementById('sfh-search-results');
        if (!resultsDiv) return;

        if (!query || query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        _searchTimer = setTimeout(async () => {
            try {
                const data = await apiFetch(`/api/scan-history/statements/search?q=${encodeURIComponent(query)}&limit=20`);
                if (!data.success || !data.data || !data.data.length) {
                    resultsDiv.innerHTML = '<div class="sfh-no-results">No statements found.</div>';
                    resultsDiv.style.display = 'block';
                    return;
                }
                resultsDiv.innerHTML = data.data.map(s => `
                    <div class="sfh-search-result" data-scan-id="${s.scan_id}" data-doc-id="${s.document_id}">
                        <div class="sfh-search-result-header">
                            <span class="sfh-search-directive sfh-d-${s.directive || 'none'}">${s.directive || '-'}</span>
                            <span class="sfh-search-doc">${escapeHtml(s.document_name)}</span>
                            <span class="sfh-search-date">${formatDate(s.scan_time)}</span>
                        </div>
                        <div class="sfh-search-result-desc">${escapeHtml((s.description || '').substring(0, 150))}</div>
                    </div>
                `).join('');
                resultsDiv.style.display = 'block';

                // Wire click handlers
                resultsDiv.querySelectorAll('.sfh-search-result').forEach(el => {
                    el.addEventListener('click', () => {
                        const scanId = parseInt(el.dataset.scanId);
                        if (scanId) {
                            pushNav('viewer');
                            showDocumentViewer(scanId);
                        }
                    });
                });
            } catch (e) {
                log('Search error: ' + e, 'error');
            }
        }, 300);
    }

    function handleOverviewClick(e) {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;

        const action = btn.dataset.action;
        if (action === 'view-scan' || action === 'view-latest') {
            const scanId = btn.dataset.scanId || (State.history[0]?.scan_id);
            if (scanId) {
                pushNav('viewer');
                showDocumentViewer(parseInt(scanId));
            }
        } else if (action === 'compare-scan') {
            const left = parseInt(btn.dataset.scanLeft);
            const right = parseInt(btn.dataset.scanRight);
            if (left && right) {
                pushNav('compare', { leftId: left, rightId: right });
                showCompareViewer(left, right);
            }
        }
    }

    // =========================================================================
    // CHARTS
    // =========================================================================

    async function renderCharts() {
        if (typeof Chart === 'undefined') return;
        destroyCharts();

        const trends = await loadTrends();

        // Trend line chart
        const trendCanvas = document.getElementById('sfh-trend-chart');
        if (trendCanvas && trends.timeline.length > 0) {
            const labels = trends.timeline.map(t => formatDateShort(t.scan_time));
            const isDark = !State.isLightMode;
            const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
            const textColor = isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)';

            State.charts.trend = new Chart(trendCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'Total',
                            data: trends.timeline.map(t => t.total),
                            borderColor: '#D6A84A',
                            backgroundColor: 'rgba(214, 168, 74, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4
                        },
                        {
                            label: 'Shall',
                            data: trends.timeline.map(t => t.shall),
                            borderColor: '#3b82f6',
                            borderWidth: 1.5,
                            tension: 0.3,
                            pointRadius: 3,
                            borderDash: [4, 2]
                        },
                        {
                            label: 'Must',
                            data: trends.timeline.map(t => t.must),
                            borderColor: '#ef4444',
                            borderWidth: 1.5,
                            tension: 0.3,
                            pointRadius: 3,
                            borderDash: [4, 2]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: textColor, boxWidth: 12 } }
                    },
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor }, beginAtZero: true }
                    }
                }
            });
        }

        // Directive donut
        const directiveCanvas = document.getElementById('sfh-directive-chart');
        const latest = State.history[0];
        if (directiveCanvas && latest) {
            const dc = latest.directive_counts || {};
            State.charts.directive = new Chart(directiveCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Shall', 'Must', 'Will', 'Should', 'May'],
                    datasets: [{
                        data: [dc.shall || 0, dc.must || 0, dc.will || 0, dc.should || 0, dc.may || 0],
                        backgroundColor: ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: State.isLightMode ? '#333' : '#ccc',
                                boxWidth: 12,
                                padding: 8
                            }
                        }
                    }
                }
            });
        }
    }

    // =========================================================================
    // VIEW: DOCUMENT VIEWER WITH STATEMENT HIGHLIGHTING
    // =========================================================================

    async function showDocumentViewer(scanId, isBack = false) {
        State.currentView = 'viewer';
        State.compareMode = false;
        const scanInfo = State.history.find(h => h.scan_id === scanId);
        updateBreadcrumb(`Scan ${formatDate(scanInfo?.scan_time || '')}`);

        const content = State.modal.querySelector('.sfh-content');
        content.innerHTML = '<div class="sfh-loading"><div class="sfh-spinner"></div><p>Loading document viewer...</p></div>';

        const [statements, docText] = await Promise.all([
            loadScanStatements(scanId),
            loadDocumentText(scanId)
        ]);

        State.currentStatements = statements;
        State.activeFilter = 'all';
        State.activeReviewFilter = 'all';
        State.filteredStatements = getFilteredStatements();
        State.currentStmtIndex = -1;
        State.editMode = false;

        if (!docText) {
            content.innerHTML = `
                <div class="sfh-viewer-no-text">
                    <p>Document text not available in scan history.</p>
                    <p>Showing extracted statements only.</p>
                    ${renderStatementsTable(statements)}
                </div>`;
            refreshIcons(content);
            return;
        }

        // Filter: show all or by directive
        const directives = ['all', 'shall', 'must', 'will', 'should', 'may'];

        content.innerHTML = `
            <div class="sfh-viewer">
                <div class="sfh-viewer-toolbar">
                    <div class="sfh-filter-chips">
                        ${directives.map(d => `
                            <button class="sfh-chip ${d === 'all' ? 'sfh-chip-active' : ''}"
                                    data-filter="${d}">${d === 'all' ? 'All' : d.charAt(0).toUpperCase() + d.slice(1)}
                                <span class="sfh-chip-count">${d === 'all' ? statements.length :
                                    statements.filter(s => s.directive === d).length}</span>
                            </button>
                        `).join('')}
                    </div>
                    <div class="sfh-viewer-stats">
                        <span>${statements.length} statements</span>
                        <span class="sfh-meta-sep">|</span>
                        <span>${statements.filter(s => s.role).length} with roles</span>
                        <button class="sfh-btn sfh-btn-sm sfh-bulk-toggle" title="Toggle bulk edit mode">
                            <i data-lucide="check-square" style="width:14px;height:14px"></i> Bulk Edit
                        </button>
                    </div>
                </div>
                <div class="sfh-bulk-bar" id="sfh-bulk-bar" style="display:none;">
                    <span class="sfh-bulk-count">0 selected</span>
                    <select class="sfh-bulk-directive" title="Set directive for selected">
                        <option value="">Set Directive...</option>
                        <option value="shall">Shall</option>
                        <option value="must">Must</option>
                        <option value="will">Will</option>
                        <option value="should">Should</option>
                        <option value="may">May</option>
                    </select>
                    <input class="sfh-bulk-role" placeholder="Set role..." title="Set role for selected">
                    <button class="sfh-btn sfh-btn-sm sfh-btn-primary sfh-bulk-apply" title="Apply changes">Apply</button>
                    <button class="sfh-btn sfh-btn-sm sfh-btn-ghost sfh-bulk-clear" title="Clear selection">Clear</button>
                </div>
                <div class="sfh-viewer-split">
                    <div class="sfh-viewer-doc-panel">
                        <div class="sfh-viewer-doc-header">
                            <h4><i data-lucide="file-text" style="width:16px;height:16px"></i> ${escapeHtml(State.documentName)}</h4>
                            <div class="sfh-view-toggle" id="sfh-view-toggle">
                                ${State.htmlPreview ? `
                                <button class="sfh-toggle-btn sfh-toggle-active" data-view="preview">
                                    <i data-lucide="eye" style="width:14px;height:14px"></i> Preview
                                </button>
                                <button class="sfh-toggle-btn" data-view="text">
                                    <i data-lucide="align-left" style="width:14px;height:14px"></i> Text
                                </button>` : ''}
                                ${(State.documentName || '').toLowerCase().endsWith('.pdf') ? `
                                <button class="sfh-toggle-btn" data-view="pdf">
                                    <i data-lucide="file" style="width:14px;height:14px"></i> PDF
                                </button>` : ''}
                            </div>
                            <span class="sfh-viewer-hint">Click a highlight to see statement details. Select text to create a new statement.</span>
                        </div>
                        <div class="sfh-viewer-doc-content" id="sfh-doc-content">
                            ${renderDocument(docText, statements)}
                        </div>
                    </div>
                    <div class="sfh-viewer-detail-panel" id="sfh-detail-panel">
                    </div>
                </div>
            </div>
        `;

        // Populate detail panel empty state (with jump button if statements exist)
        resetDetailPanel();

        // Wire events
        const docContent = content.querySelector('#sfh-doc-content');

        // v4.5.1: Build mark index cache for O(1) lookups during navigation
        buildMarkIndexMap(docContent);
        _activeMarkEl = null;

        // Highlight click → show detail + update navigation state (throttled)
        docContent.addEventListener('click', (e) => {
            const mark = e.target.closest('.sfh-stmt-highlight');
            if (mark) {
                if (_navThrottleTimer) return; // Prevent rapid-fire clicks
                _navThrottleTimer = setTimeout(() => { _navThrottleTimer = null; }, NAV_THROTTLE_MS);

                const idx = parseInt(mark.dataset.stmtIndex);
                const stmt = State.currentStatements[idx];
                if (!stmt) return;
                // Update navigation index in filtered list
                State.currentStmtIndex = State.filteredStatements.findIndex(s => s === stmt || s.id === stmt.id);
                State.editMode = false;
                showStatementDetail(stmt, idx);
                updateActiveHighlight(idx);
            }
        });

        // Text selection → highlight-to-create
        docContent.addEventListener('mouseup', handleTextSelection);

        // Filter chips
        content.querySelectorAll('.sfh-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                content.querySelectorAll('.sfh-chip').forEach(c => c.classList.remove('sfh-chip-active'));
                chip.classList.add('sfh-chip-active');

                State.activeFilter = chip.dataset.filter;
                State.filteredStatements = getFilteredStatements();
                State.currentStmtIndex = -1;
                State.editMode = false;

                const filter = chip.dataset.filter;
                const filtered = filter === 'all' ? statements :
                    statements.filter(s => s.directive === filter);
                docContent.innerHTML = renderDocument(docText, filtered);
                buildMarkIndexMap(docContent); // v4.5.1: Rebuild mark cache after filter
                _activeMarkEl = null;

                // Reset detail panel
                resetDetailPanel();
            });
        });

        // v5.9.35: Document view toggle — Preview (HTML) / Text / PDF
        const toggle = content.querySelector('#sfh-view-toggle');
        if (toggle) {
            toggle.querySelectorAll('.sfh-toggle-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    toggle.querySelectorAll('.sfh-toggle-btn').forEach(b => b.classList.remove('sfh-toggle-active'));
                    btn.classList.add('sfh-toggle-active');

                    const docContent = content.querySelector('#sfh-doc-content');
                    const filter = State.activeFilter;
                    const filtered = filter === 'all' ? statements :
                        statements.filter(s => s.directive === filter);

                    if (btn.dataset.view === 'pdf') {
                        if (typeof TWR !== 'undefined' && TWR.PDFViewer) {
                            try {
                                await TWR.PDFViewer.render(
                                    docContent,
                                    `/api/scan-history/document-file?scan_id=${scanId}`
                                );
                            } catch (pdfErr) {
                                console.warn('[SFH] PDF render failed, falling back to text:', pdfErr);
                                docContent.innerHTML = renderDocument(docText, filtered, { forceText: true });
                                buildMarkIndexMap(docContent);
                                _activeMarkEl = null;
                            }
                        } else {
                            docContent.innerHTML = '<div class="pdfv-error">PDF viewer not available.</div>';
                        }
                    } else if (btn.dataset.view === 'text') {
                        // v5.9.35: Force plain text rendering (no HTML preview)
                        docContent.innerHTML = renderDocument(docText, filtered, { forceText: true });
                        buildMarkIndexMap(docContent);
                        _activeMarkEl = null;
                    } else {
                        // preview or html — use normal rendering (HTML preview if available)
                        docContent.innerHTML = renderDocument(docText, filtered);
                        buildMarkIndexMap(docContent);
                        _activeMarkEl = null;
                    }

                    // Refresh Lucide icons in new content
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                });
            });
        }

        // v4.4.0: Bulk edit mode
        State.selectedStatements.clear();
        State.bulkMode = false;
        content.querySelector('.sfh-bulk-toggle')?.addEventListener('click', () => {
            State.bulkMode = !State.bulkMode;
            const bar = document.getElementById('sfh-bulk-bar');
            if (bar) bar.style.display = State.bulkMode ? 'flex' : 'none';
            content.querySelector('.sfh-bulk-toggle')?.classList.toggle('sfh-chip-active', State.bulkMode);
            if (!State.bulkMode) {
                State.selectedStatements.clear();
                updateBulkCount();
            }
        });
        content.querySelector('.sfh-bulk-apply')?.addEventListener('click', () => applyBulkUpdate(scanId));
        content.querySelector('.sfh-bulk-clear')?.addEventListener('click', () => {
            State.selectedStatements.clear();
            updateBulkCount();
        });

        refreshIcons(content);
        updateFooterShortcuts();
    }

    // =========================================================================
    // v4.4.0: BULK EDIT HELPERS
    // =========================================================================

    function updateBulkCount() {
        const countEl = document.querySelector('.sfh-bulk-count');
        if (countEl) countEl.textContent = `${State.selectedStatements.size} selected`;
    }

    function toggleStatementSelection(stmtId) {
        if (State.selectedStatements.has(stmtId)) {
            State.selectedStatements.delete(stmtId);
        } else {
            State.selectedStatements.add(stmtId);
        }
        updateBulkCount();
    }

    async function applyBulkUpdate(scanId) {
        const directive = document.querySelector('.sfh-bulk-directive')?.value;
        const role = document.querySelector('.sfh-bulk-role')?.value?.trim();

        if (!directive && !role) {
            showToast('info', 'Select a directive or enter a role');
            return;
        }

        if (State.selectedStatements.size === 0) {
            showToast('info', 'No statements selected');
            return;
        }

        const updates = Array.from(State.selectedStatements).map(id => ({
            id,
            updates: {
                ...(directive ? { directive } : {}),
                ...(role ? { role } : {})
            }
        }));

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
            const data = await apiFetch('/api/scan-history/statements/batch', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ updates })
            });

            if (data.success) {
                showToast('success', `Updated ${data.updated} statements`);
                State.selectedStatements.clear();
                State.bulkMode = false;
                // v4.5.1: Don't clear documentText/htmlPreview — only statement metadata changed.
                // The document content itself hasn't changed, so avoid redundant API re-fetch.
                showDocumentViewer(scanId);
            } else {
                showToast('error', 'Bulk update failed: ' + (data.error || 'Unknown'));
            }
        } catch (e) {
            showToast('error', 'Bulk update error: ' + e.message);
        }
    }

    // v4.5.1: Cache for normalized document text (avoids recomputing on every filter change)
    let _normDocCache = { docText: null, normDocStr: null, normToOrig: null };

    // Shared helper: find highlight positions for statements in document text
    // Returns sorted, non-overlapping array of {start, end, stmt, idx, directive, role}
    function findHighlightPositions(docText, statements) {
        // Normalize whitespace: collapse runs of whitespace/pipes into single space
        function normalizeWS(text) {
            return text.replace(/[\s|]+/g, ' ').trim();
        }

        // v4.5.1: Use cached normalization if docText hasn't changed
        let normDocStr, normToOrig;
        if (_normDocCache.docText === docText) {
            normDocStr = _normDocCache.normDocStr;
            normToOrig = _normDocCache.normToOrig;
        } else {
            const normDoc = [];
            normToOrig = [];
            let inWS = false;
            for (let i = 0; i < docText.length; i++) {
                const ch = docText[i];
                if (ch === ' ' || ch === '|' || ch === '\t' || ch === '\n' || ch === '\r') {
                    if (!inWS) { normDoc.push(' '); normToOrig.push(i); inWS = true; }
                } else {
                    normDoc.push(ch); normToOrig.push(i); inWS = false;
                }
            }
            normDocStr = normDoc.join('');
            _normDocCache = { docText, normDocStr, normToOrig };
        }

        const highlights = [];
        statements.forEach((stmt, idx) => {
            if (stmt.is_header || !stmt.description) return;
            const desc = stmt.description.trim();
            if (desc.length < 10) return;

            // Strategy 1: Direct match (fast path)
            const searchText = desc.substring(0, Math.min(80, desc.length));
            let pos = docText.indexOf(searchText);
            if (pos >= 0) {
                highlights.push({ start: pos, end: pos + desc.length, stmt, idx,
                    directive: stmt.directive || '', role: stmt.role || '' });
                return;
            }

            // Strategy 2: Directive keyword phrase search in original text
            const normDesc = normalizeWS(desc);
            const directiveKw = (stmt.directive || '').toLowerCase();
            let matched = false;

            if (directiveKw) {
                const normLower = normDesc.toLowerCase();
                const dIdx = normLower.indexOf(directiveKw);
                if (dIdx >= 0) {
                    const phraseStart = Math.max(0, dIdx - 20);
                    const phraseEnd = Math.min(normDesc.length, dIdx + directiveKw.length + 40);
                    const phrase = normDesc.substring(phraseStart, phraseEnd);
                    const words = phrase.split(/\s+/).filter(w => w.length > 2);
                    const kwIdx = words.findIndex(w => w.toLowerCase().includes(directiveKw));
                    if (kwIdx >= 0) {
                        const startW = Math.max(0, kwIdx - 1);
                        const endW = Math.min(words.length, kwIdx + 3);
                        const searchWords = words.slice(startW, endW);
                        const pattern = searchWords.map(w =>
                            w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
                        ).join('[\\s|]+');
                        try {
                            const regex = new RegExp(pattern, 'i');
                            const match = regex.exec(docText);
                            if (match) {
                                let hStart = match.index;
                                const lookBack = Math.max(0, hStart - 200);
                                for (let j = hStart - 1; j >= lookBack; j--) {
                                    const c = docText[j];
                                    if (c === '\n' || c === '*') { hStart = j + 1; break; }
                                    if (j === lookBack) hStart = j;
                                }
                                let hEnd = match.index + match[0].length;
                                const lookFwd = Math.min(docText.length, hEnd + 200);
                                for (let j = hEnd; j < lookFwd; j++) {
                                    const c = docText[j];
                                    if (c === '\n' || (c === '.' && docText[j+1] === '*') || (c === '.' && docText[j+1] === ' ')) {
                                        hEnd = j + 1; break;
                                    }
                                    if (j === lookFwd - 1) hEnd = j;
                                }
                                highlights.push({ start: hStart, end: Math.min(hEnd, docText.length),
                                    stmt, idx, directive: stmt.directive || '', role: stmt.role || '' });
                                matched = true;
                            }
                        } catch(e) { /* regex error, fall through */ }
                    }
                }
            }

            // Strategy 3: Fallback — normalized first 80 chars, fixed 400-char window
            if (!matched) {
                const normSearch = normDesc.substring(0, Math.min(80, normDesc.length));
                const normPos = normDocStr.indexOf(normSearch);
                if (normPos >= 0) {
                    const origStart = normToOrig[normPos] || 0;
                    const origEnd = Math.min(origStart + 400, docText.length);
                    highlights.push({ start: origStart, end: origEnd, stmt, idx,
                        directive: stmt.directive || '', role: stmt.role || '' });
                }
            }
        });

        // Sort by position and remove overlaps (keep first, merge indices)
        highlights.sort((a, b) => a.start - b.start);
        const clean = [];
        let lastEnd = -1;
        for (const h of highlights) {
            if (h.start >= lastEnd) {
                h.allIndices = [h.idx]; // Track all statement indices sharing this mark
                clean.push(h);
                lastEnd = h.end;
            } else if (clean.length > 0) {
                // Overlapping — merge this statement's index into the surviving mark
                clean[clean.length - 1].allIndices.push(h.idx);
            }
        }
        return clean;
    }

    function renderHighlightedDocument(docText, statements) {
        if (!docText) return '<p class="sfh-no-doc">No document text available.</p>';

        const clean = findHighlightPositions(docText, statements);

        // v4.5.1: Build O(1) lookup map for currentStatements indices
        const csMap = new Map();
        State.currentStatements.forEach((s, i) => { if (!csMap.has(s)) csMap.set(s, i); });

        // Remap idx and allIndices to State.currentStatements indices
        for (const h of clean) {
            const csIdx = csMap.get(h.stmt);
            if (csIdx !== undefined) h.idx = csIdx;
            // Remap allIndices: find each overlapping stmt in currentStatements
            if (h.allIndices) {
                h.allIndices = h.allIndices.map(origIdx => {
                    const s = statements[origIdx];
                    if (!s) return origIdx;
                    const ci = csMap.get(s);
                    return ci !== undefined ? ci : origIdx;
                });
            }
        }

        // Build HTML
        let html = '';
        let cursor = 0;
        for (const h of clean) {
            if (h.start > cursor) html += escapeHtml(docText.substring(cursor, h.start));
            const directiveClass = h.directive ? `sfh-d-${h.directive}` : '';
            const matchedText = docText.substring(h.start, Math.min(h.end, docText.length));
            const allIdx = (h.allIndices || [h.idx]).join(',');
            html += `<mark class="sfh-stmt-highlight ${directiveClass}" data-stmt-index="${h.idx}" data-stmt-indices="${allIdx}" title="${escapeHtml(h.role || h.directive || 'Statement')}">${escapeHtml(matchedText)}</mark>`;
            cursor = Math.min(h.end, docText.length);
        }
        if (cursor < docText.length) html += escapeHtml(docText.substring(cursor));

        return html.replace(/\n/g, '<br>');
    }

    // =========================================================================
    // v4.3.0: HTML-based document rendering with DOM text node highlighting
    // =========================================================================

    /**
     * Render HTML preview with statement highlights using DOM text node walking.
     * This replaces the fragile string-index matching with direct DOM manipulation.
     * Falls back to renderHighlightedDocument() when no HTML preview is available.
     *
     * @param {string} htmlContent - Raw HTML from mammoth/pymupdf4llm
     * @param {Array} statements - Statement objects to highlight
     * @param {Object} options - { isCompare: false, mergedStatements: null }
     * @returns {string} HTML string with statement highlights injected
     */
    function renderHTMLDocument(htmlContent, statements, options = {}) {
        if (!htmlContent) return renderHighlightedDocument(State.documentText, statements);

        // Sanitize HTML: strip scripts, styles, event handlers
        const sanitized = sanitizeHTML(htmlContent);

        // Create a temporary container to build the DOM
        const container = document.createElement('div');
        container.className = 'sfh-html-content';
        container.innerHTML = sanitized;

        // Walk text nodes and find statement positions using DOM Range API
        const statementsToHighlight = statements.filter(s => !s.is_header && s.description && s.description.trim().length >= 10);

        // Collect all text nodes
        const textNodes = [];
        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim().length > 0) {
                textNodes.push(node);
            }
        }

        // Build concatenated text for searching
        const nodeMap = []; // [{node, startOffset (in concat text), text}]
        let totalOffset = 0;
        for (const tn of textNodes) {
            const text = tn.textContent;
            nodeMap.push({ node: tn, startOffset: totalOffset, text });
            totalOffset += text.length;
        }
        const concatText = nodeMap.map(n => n.text).join('');

        // v4.3.0: Aggressive normalization for cross-extractor matching
        // Statement descriptions may come from Docling/legacy (with | and ** artifacts)
        // while HTML text comes from mammoth (clean). Strip all formatting noise.
        function normalizeForMatch(text) {
            return text
                .replace(/\*+/g, '')           // Strip markdown bold/italic markers
                .replace(/[|]+/g, ' ')          // Strip pipe characters (table formatting)
                .replace(/[-]{3,}/g, ' ')       // Strip horizontal rules (---)
                .replace(/#+\s*/g, '')           // Strip markdown headers
                .replace(/\s+/g, ' ')            // Collapse whitespace
                .trim();
        }

        // Build normalized version of concatenated text for fuzzy matching
        // Also build a position map: normIdx -> origIdx (O(n) algorithm)
        const normConcat = normalizeForMatch(concatText);
        const normToOrigMap = []; // normToOrigMap[normIdx] = origIdx
        {
            // Walk both strings in parallel to build the mapping efficiently
            // Instead of O(n^2) substring calls, we track what normalizeForMatch does:
            // - strips *+, converts | to space, strips ---+, strips #+, collapses whitespace
            let normI = 0;
            let prevWasSpace = false;
            // Skip leading whitespace (normalize trims)
            let startOrig = 0;
            while (startOrig < concatText.length && /\s/.test(concatText[startOrig])) startOrig++;

            for (let i = startOrig; i < concatText.length && normI < normConcat.length; i++) {
                const ch = concatText[i];
                // Characters that get stripped entirely by normalizeForMatch
                if (ch === '*') continue;
                if (ch === '#') {
                    // Skip # and any following whitespace
                    while (i + 1 < concatText.length && /\s/.test(concatText[i + 1])) i++;
                    continue;
                }
                // Check for --- (3+ dashes become space)
                if (ch === '-' && i + 2 < concatText.length && concatText[i + 1] === '-' && concatText[i + 2] === '-') {
                    while (i + 1 < concatText.length && concatText[i + 1] === '-') i++;
                    if (!prevWasSpace && normI < normConcat.length && normConcat[normI] === ' ') {
                        normToOrigMap[normI] = i;
                        normI++;
                        prevWasSpace = true;
                    }
                    continue;
                }
                // Pipe characters become space
                if (ch === '|') {
                    if (!prevWasSpace && normI < normConcat.length && normConcat[normI] === ' ') {
                        normToOrigMap[normI] = i;
                        normI++;
                        prevWasSpace = true;
                    }
                    continue;
                }
                // Whitespace: collapse to single space
                if (/\s/.test(ch)) {
                    if (!prevWasSpace && normI < normConcat.length && normConcat[normI] === ' ') {
                        normToOrigMap[normI] = i;
                        normI++;
                        prevWasSpace = true;
                    }
                    continue;
                }
                // Regular character
                if (normI < normConcat.length) {
                    normToOrigMap[normI] = i;
                    normI++;
                    prevWasSpace = false;
                }
            }
        }

        // v4.5.1: Build O(1) lookup map + hoist Strategy 3 split outside loop
        const csMap = new Map();
        State.currentStatements.forEach((s, i) => { if (!csMap.has(s)) csMap.set(s, i); });
        const concatWordsLower = normConcat.split(/\s+/).map(w => w.toLowerCase()); // Hoisted + pre-lowered

        // Find positions of each statement in the concatenated text
        const highlights = [];
        statementsToHighlight.forEach((stmt, filterIdx) => {
            const desc = stmt.description.trim();
            const searchText = desc.substring(0, Math.min(80, desc.length));
            const csIdx = csMap.has(stmt) ? csMap.get(stmt) : filterIdx; // v4.5.1: O(1) lookup

            // Strategy 1: Direct match (exact substring)
            let pos = concatText.indexOf(searchText);
            if (pos >= 0) {
                highlights.push({
                    start: pos,
                    end: pos + Math.min(desc.length, concatText.length - pos),
                    stmt, csIdx,
                    directive: stmt.directive || '',
                    role: stmt.role || ''
                });
                return;
            }

            // Strategy 2: Normalized match (strips pipes, bold markers, excess whitespace)
            const normDesc = normalizeForMatch(desc);
            const normSearch = normDesc.substring(0, Math.min(60, normDesc.length));
            if (normSearch.length < 10) return;

            const normPos = normConcat.indexOf(normSearch);
            if (normPos >= 0) {
                const origStart = normToOrigMap[normPos] || 0;
                const normEndPos = Math.min(normPos + normDesc.length, normConcat.length - 1);
                const origEnd = normToOrigMap[normEndPos] || Math.min(origStart + desc.length, concatText.length);
                highlights.push({
                    start: origStart, end: origEnd, stmt, csIdx,
                    directive: stmt.directive || '',
                    role: stmt.role || ''
                });
                return;
            }

            // Strategy 3: Find longest matching word sequence (fuzzy)
            const descWords = normDesc.split(/\s+/).filter(w => w.length > 3);
            if (descWords.length >= 3) {
                const descWordsLower = descWords.map(w => w.toLowerCase());
                for (let cw = 0; cw < concatWordsLower.length - 2; cw++) {
                    let matchLen = 0;
                    for (let dw = 0; dw < descWordsLower.length && (cw + matchLen) < concatWordsLower.length; dw++) {
                        if (concatWordsLower[cw + matchLen] === descWordsLower[dw]) {
                            matchLen++;
                        }
                    }
                    if (matchLen >= 3) {
                        const matchPhrase = concatWordsLower.slice(cw, cw + matchLen).join(' ');
                        const phrasePos = normConcat.toLowerCase().indexOf(matchPhrase);
                        if (phrasePos >= 0) {
                            const origStart = normToOrigMap[phrasePos] || 0;
                            const phraseEndPos = Math.min(phrasePos + matchPhrase.length, normConcat.length - 1);
                            const origEnd = normToOrigMap[phraseEndPos] || Math.min(origStart + matchPhrase.length, concatText.length);
                            highlights.push({
                                start: origStart, end: origEnd, stmt, csIdx,
                                directive: stmt.directive || '',
                                role: stmt.role || ''
                            });
                            break;
                        }
                    }
                }
            }
        });

        // Sort by position and remove overlaps
        highlights.sort((a, b) => a.start - b.start);
        const clean = [];
        let lastEnd = -1;
        for (const h of highlights) {
            if (h.start >= lastEnd) {
                h.allIndices = [h.csIdx];
                clean.push(h);
                lastEnd = h.end;
            } else if (clean.length > 0) {
                clean[clean.length - 1].allIndices.push(h.csIdx);
            }
        }

        // Apply highlights using DOM Range API (process in reverse to preserve positions)
        for (let i = clean.length - 1; i >= 0; i--) {
            const h = clean[i];
            try {
                // Find start and end nodes
                const startInfo = findNodeAtOffset(nodeMap, h.start);
                const endInfo = findNodeAtOffset(nodeMap, h.end);
                if (!startInfo || !endInfo) continue;

                const range = document.createRange();
                range.setStart(startInfo.node, startInfo.offset);
                range.setEnd(endInfo.node, endInfo.offset);

                // Create mark element
                const mark = document.createElement('mark');
                const directiveClass = h.directive ? `sfh-d-${h.directive}` : '';

                // Handle diff mode
                let diffClass = '', diffLabel = '';
                if (options.isCompare && h.stmt._diff_status) {
                    const ds = h.stmt._diff_status;
                    const diffClasses = { added: 'sfh-diff-added', removed: 'sfh-diff-removed', modified_new: 'sfh-diff-modified', modified: 'sfh-diff-modified' };
                    const diffLabels = { added: 'NEW', removed: 'REMOVED', modified_new: 'CHANGED', modified: 'CHANGED' };
                    diffClass = diffClasses[ds] || '';
                    if (diffLabels[ds]) {
                        const labelCls = { added: 'sfh-diff-new', removed: 'sfh-diff-del', modified_new: 'sfh-diff-mod', modified: 'sfh-diff-mod' };
                        diffLabel = ` <span class="sfh-diff-indicator ${labelCls[ds] || ''}">${diffLabels[ds]}</span>`;
                    }
                }

                mark.className = `sfh-stmt-highlight ${directiveClass} ${diffClass}`.trim();
                mark.dataset.stmtIndex = String(h.csIdx);
                mark.dataset.stmtIndices = (h.allIndices || [h.csIdx]).join(',');
                mark.title = h.role || h.directive || 'Statement';

                if (options.isCompare && h.stmt._diff_status) {
                    mark.dataset.diffStatus = h.stmt._diff_status;
                    mark.dataset.source = h.stmt._source || 'newer';
                }

                // Wrap range contents
                try {
                    range.surroundContents(mark);
                } catch (surErr) {
                    // surroundContents fails if range spans partial elements
                    // Fallback: extract and re-insert
                    const fragment = range.extractContents();
                    mark.appendChild(fragment);
                    range.insertNode(mark);
                }

                // Add diff label after the mark content
                if (diffLabel) {
                    mark.insertAdjacentHTML('beforeend', diffLabel);
                }
            } catch (e) {
                // Skip this highlight if DOM manipulation fails
                log('HTML highlight error for stmt ' + h.csIdx + ': ' + e.message, 'debug');
            }
        }

        return container.innerHTML;
    }

    /**
     * Find the text node and offset for a given position in concatenated text.
     */
    function findNodeAtOffset(nodeMap, targetOffset) {
        for (const entry of nodeMap) {
            const endOffset = entry.startOffset + entry.text.length;
            if (targetOffset >= entry.startOffset && targetOffset <= endOffset) {
                return {
                    node: entry.node,
                    offset: targetOffset - entry.startOffset
                };
            }
        }
        // If past end, return last node's end
        if (nodeMap.length > 0) {
            const last = nodeMap[nodeMap.length - 1];
            return { node: last.node, offset: last.text.length };
        }
        return null;
    }

    /**
     * Sanitize HTML: remove scripts, styles, event handlers.
     */
    function sanitizeHTML(html) {
        // Remove script tags and their content
        let clean = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        // Remove style tags and their content
        clean = clean.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
        // Remove event handlers (on*)
        clean = clean.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]*)/gi, '');
        // Remove javascript: URLs
        clean = clean.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"');
        return clean;
    }

    /**
     * Choose the best rendering method for document content.
     * Uses HTML preview when available, falls back to plain text highlighting.
     */
    function renderDocument(docText, statements, options = {}) {
        // v5.9.35: forceText option bypasses HTML preview for text toggle
        if (options.forceText) {
            if (options.isCompare) {
                return renderCompareHighlightedDocument(docText, statements);
            }
            return renderHighlightedDocument(docText, statements);
        }
        if (State.htmlPreview && State.docFormat === 'html') {
            return renderHTMLDocument(State.htmlPreview, statements, options);
        }
        if (options.isCompare) {
            return renderCompareHighlightedDocument(docText, statements);
        }
        return renderHighlightedDocument(docText, statements);
    }

    // Diff-aware highlight renderer for compare viewer
    function renderCompareHighlightedDocument(docText, mergedStatements) {
        if (!docText) return '<p class="sfh-no-doc">No document text available.</p>';

        const clean = findHighlightPositions(docText, mergedStatements);

        // Remap idx and allIndices to State.currentStatements indices
        for (const h of clean) {
            const csIdx = State.currentStatements.indexOf(h.stmt);
            if (csIdx >= 0) h.idx = csIdx;
            if (h.allIndices) {
                h.allIndices = h.allIndices.map(origIdx => {
                    const s = mergedStatements[origIdx];
                    if (!s) return origIdx;
                    const ci = State.currentStatements.indexOf(s);
                    return ci >= 0 ? ci : origIdx;
                });
            }
        }

        const diffLabels = {
            added: '<span class="sfh-diff-indicator sfh-diff-new">NEW</span>',
            removed: '<span class="sfh-diff-indicator sfh-diff-del">REMOVED</span>',
            modified_new: '<span class="sfh-diff-indicator sfh-diff-mod">CHANGED</span>',
            modified: '<span class="sfh-diff-indicator sfh-diff-mod">CHANGED</span>'
        };

        const diffClasses = {
            added: 'sfh-diff-added',
            removed: 'sfh-diff-removed',
            modified_new: 'sfh-diff-modified',
            modified: 'sfh-diff-modified'
        };

        let html = '';
        let cursor = 0;
        for (const h of clean) {
            if (h.start > cursor) html += escapeHtml(docText.substring(cursor, h.start));

            const stmt = h.stmt;
            const diffStatus = stmt._diff_status || 'unchanged';
            const source = stmt._source || 'newer';
            const directiveClass = (diffStatus === 'removed') ? '' : (h.directive ? `sfh-d-${h.directive}` : '');
            const diffClass = diffClasses[diffStatus] || '';
            const label = diffLabels[diffStatus] || '';

            const matchedText = docText.substring(h.start, Math.min(h.end, docText.length));
            const allIdx = (h.allIndices || [h.idx]).join(',');
            html += `<mark class="sfh-stmt-highlight ${directiveClass} ${diffClass}" data-stmt-index="${h.idx}" data-stmt-indices="${allIdx}" data-diff-status="${diffStatus}" data-source="${source}" title="${escapeHtml(h.role || h.directive || 'Statement')}">${escapeHtml(matchedText)}${label}</mark>`;
            cursor = Math.min(h.end, docText.length);
        }
        if (cursor < docText.length) html += escapeHtml(docText.substring(cursor));

        return html.replace(/\n/g, '<br>');
    }

    function showStatementDetail(stmt, idx) {
        const panel = document.getElementById('sfh-detail-panel');
        if (!panel || !stmt) return;

        const directiveColor = {
            shall: '#3b82f6', must: '#ef4444', will: '#f59e0b',
            should: '#22c55e', may: '#8b5cf6'
        };
        const color = directiveColor[stmt.directive] || '#666';
        const isCompare = State.compareMode;
        const diffStatus = stmt._diff_status || 'unchanged';
        const isRemoved = diffStatus === 'removed';
        const canEdit = !isRemoved; // Can't edit removed (older scan) statements

        // Navigation bar (only if >1 statement in filtered set)
        const filtered = State.filteredStatements;
        const navHtml = filtered.length > 1 ? `
            <div class="sfh-detail-nav">
                <button class="sfh-detail-nav-btn" data-action="prev-stmt" title="Previous statement (↑)">
                    <i data-lucide="chevron-up" style="width:16px;height:16px"></i>
                </button>
                <span class="sfh-detail-nav-position">${State.currentStmtIndex + 1} of ${filtered.length}</span>
                <button class="sfh-detail-nav-btn" data-action="next-stmt" title="Next statement (↓)">
                    <i data-lucide="chevron-down" style="width:16px;height:16px"></i>
                </button>
            </div>
        ` : '';

        // Compare mode: diff status badge
        const diffBadgeMap = {
            added: '<span class="sfh-diff-badge-detail sfh-badge-added">NEW IN THIS SCAN</span>',
            removed: '<span class="sfh-diff-badge-detail sfh-badge-removed">REMOVED</span>',
            modified_new: '<span class="sfh-diff-badge-detail sfh-badge-modified">CHANGED</span>',
            unchanged: '<span class="sfh-diff-badge-detail sfh-badge-unchanged">UNCHANGED</span>'
        };
        const diffBadgeHtml = isCompare ? (diffBadgeMap[diffStatus] || '') : '';

        // Compare mode: source scan indicator
        const sourceHtml = isCompare ? `
            <div class="sfh-detail-source">
                <i data-lucide="${stmt._source === 'newer' ? 'arrow-up-circle' : 'arrow-down-circle'}" style="width:12px;height:12px"></i>
                ${stmt._source === 'newer' ? 'Newer' : 'Older'} Scan
                (${formatDate(State.compareScanInfo?.[stmt._source]?.scan_time || '')})
            </div>` : '';

        // Compare mode: field-level diff for modified statements
        let fieldDiffHtml = '';
        if (isCompare && (diffStatus === 'modified_new' || diffStatus === 'modified') && stmt._modified_from) {
            const old = stmt._modified_from;
            const diffs = [];
            if ((old.directive || '') !== (stmt.directive || ''))
                diffs.push(`<div class="sfh-diff-row"><label>Directive</label><span class="sfh-diff-old">${escapeHtml(old.directive || 'none')}</span><span class="sfh-diff-arrow">→</span><span class="sfh-diff-new">${escapeHtml(stmt.directive || 'none')}</span></div>`);
            if ((old.role || '') !== (stmt.role || ''))
                diffs.push(`<div class="sfh-diff-row"><label>Role</label><span class="sfh-diff-old">${escapeHtml(old.role || 'none')}</span><span class="sfh-diff-arrow">→</span><span class="sfh-diff-new">${escapeHtml(stmt.role || 'none')}</span></div>`);
            if ((old.level || 0) !== (stmt.level || 0))
                diffs.push(`<div class="sfh-diff-row"><label>Level</label><span class="sfh-diff-old">${old.level || 0}</span><span class="sfh-diff-arrow">→</span><span class="sfh-diff-new">${stmt.level || 0}</span></div>`);
            if ((old.title || '') !== (stmt.title || ''))
                diffs.push(`<div class="sfh-diff-row"><label>Title</label><span class="sfh-diff-old">${escapeHtml(old.title || 'none')}</span><span class="sfh-diff-arrow">→</span><span class="sfh-diff-new">${escapeHtml(stmt.title || 'none')}</span></div>`);
            if (diffs.length > 0) {
                fieldDiffHtml = `
                    <div class="sfh-detail-diff">
                        <div class="sfh-detail-diff-title"><i data-lucide="arrow-right-left" style="width:12px;height:12px"></i> Changes from previous scan</div>
                        ${diffs.join('')}
                    </div>`;
            }
        }

        // Removed statement note
        const removedNote = isCompare && isRemoved ? `
            <div class="sfh-detail-removed-note">
                <i data-lucide="info" style="width:14px;height:14px"></i>
                This statement was removed in the newer scan.
            </div>` : '';

        if (!State.editMode) {
            // READ MODE
            const isSelected = State.selectedStatements.has(stmt.id);
            const bulkCheckbox = State.bulkMode && canEdit ? `
                <label class="sfh-bulk-checkbox" title="Select for bulk edit">
                    <input type="checkbox" ${isSelected ? 'checked' : ''} data-action="bulk-select" data-stmt-id="${stmt.id}">
                </label>` : '';
            panel.innerHTML = `
                ${navHtml}
                <div class="sfh-detail-card">
                    <div class="sfh-detail-header-row">
                        ${bulkCheckbox}
                        <div class="sfh-detail-number">${escapeHtml(stmt.number || `#${idx + 1}`)}</div>
                        ${diffBadgeHtml}
                        ${canEdit ? `<button class="sfh-detail-edit-btn" data-action="edit-stmt" title="Edit Statement (e)">
                            <i data-lucide="pencil" style="width:14px;height:14px"></i> Edit
                        </button>` : ''}
                    </div>
                    ${sourceHtml}
                    ${stmt.directive ? `<div class="sfh-detail-directive" style="color:${color}; border-color:${color}">
                        ${stmt.directive.toUpperCase()}</div>` : ''}
                    <div class="sfh-detail-title">${escapeHtml(stmt.title || '')}</div>
                    <div class="sfh-detail-description">${escapeHtml(stmt.description || '')}</div>
                    ${fieldDiffHtml}
                    ${removedNote}
                    ${stmt.role ? `<div class="sfh-detail-field"><label>Role</label><span>${escapeHtml(stmt.role)}</span></div>` : ''}
                    ${stmt.section ? `<div class="sfh-detail-field"><label>Section</label><span>${escapeHtml(stmt.section)}</span></div>` : ''}
                    <div class="sfh-detail-field"><label>Level</label><span>${stmt.level}</span></div>
                    <div class="sfh-detail-field"><label>Review</label><span>${
                        AEGIS.StatementReviewLookup
                            ? AEGIS.StatementReviewLookup.getBadge(stmt.confirmed ? 'confirmed' : (stmt.review_status || 'pending'))
                            : (stmt.review_status || 'pending')
                    }</span></div>
                    ${stmt.notes && stmt.notes.length ? `
                        <div class="sfh-detail-notes">
                            <label>Notes</label>
                            ${stmt.notes.map(n => `<div class="sfh-note">${escapeHtml(n)}</div>`).join('')}
                        </div>` : ''}
                    ${canEdit ? `<div class="sfh-review-actions" style="display:flex;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid var(--border-default);">
                        <button class="sfh-btn sfh-btn-sm" data-action="review-approve" data-stmt-id="${stmt.id}" style="background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3);">
                            <i data-lucide="check" style="width:12px;height:12px"></i> Approve
                        </button>
                        <button class="sfh-btn sfh-btn-sm" data-action="review-reject" data-stmt-id="${stmt.id}" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);">
                            <i data-lucide="x" style="width:12px;height:12px"></i> Reject
                        </button>
                    </div>` : ''}
                </div>
            `;
        } else {
            // EDIT MODE
            panel.innerHTML = `
                ${navHtml}
                <div class="sfh-detail-card sfh-edit-mode">
                    <div class="sfh-detail-header-row">
                        <div class="sfh-detail-number">${escapeHtml(stmt.number || `#${idx + 1}`)}</div>
                        <span class="sfh-edit-badge">Editing</span>
                    </div>
                    ${sourceHtml}
                    <div class="sfh-edit-field">
                        <label>Title</label>
                        <input type="text" class="sfh-edit-input" id="sfh-edit-title"
                            value="${escapeHtml(stmt.title || '')}" maxlength="200">
                    </div>
                    <div class="sfh-edit-field">
                        <label>Description</label>
                        <textarea class="sfh-edit-textarea" id="sfh-edit-description" rows="6">${escapeHtml(stmt.description || '')}</textarea>
                    </div>
                    <div class="sfh-edit-field">
                        <label>Directive</label>
                        <select class="sfh-edit-select" id="sfh-edit-directive">
                            <option value="">None</option>
                            <option value="shall" ${stmt.directive === 'shall' ? 'selected' : ''}>Shall</option>
                            <option value="must" ${stmt.directive === 'must' ? 'selected' : ''}>Must</option>
                            <option value="will" ${stmt.directive === 'will' ? 'selected' : ''}>Will</option>
                            <option value="should" ${stmt.directive === 'should' ? 'selected' : ''}>Should</option>
                            <option value="may" ${stmt.directive === 'may' ? 'selected' : ''}>May</option>
                        </select>
                    </div>
                    <div class="sfh-edit-field">
                        <label>Role</label>
                        <input type="text" class="sfh-edit-input" id="sfh-edit-role" list="sfh-role-suggestions"
                            value="${escapeHtml(stmt.role || '')}" maxlength="100" placeholder="Type to search roles...">
                        <datalist id="sfh-role-suggestions"></datalist>
                    </div>
                    <div class="sfh-edit-field">
                        <label>Level</label>
                        <input type="number" class="sfh-edit-input sfh-edit-level" id="sfh-edit-level"
                            value="${stmt.level || 1}" min="1" max="5">
                    </div>
                    <div class="sfh-edit-actions">
                        <button class="sfh-btn sfh-btn-sm" data-action="save-stmt">
                            <i data-lucide="save" style="width:14px;height:14px"></i> Save
                        </button>
                        <button class="sfh-btn sfh-btn-sm sfh-btn-outline" data-action="cancel-edit">Cancel</button>
                    </div>
                </div>
            `;
        }

        // Scoped icon refresh — only process icons inside the detail panel
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [panel] }); } catch (_) {
                // Fallback for older lucide versions without nodes option
                refreshIcons();
            }
        }

        // Wire detail panel event delegation — remove previous handler first to prevent leak
        if (panel._sfhHandler) {
            panel.removeEventListener('click', panel._sfhHandler);
        }
        const handler = (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const action = btn.dataset.action;
            if (action === 'prev-stmt') navigateToStatement('prev');
            else if (action === 'next-stmt') navigateToStatement('next');
            else if (action === 'edit-stmt') enterEditMode(stmt, idx);
            else if (action === 'cancel-edit') exitEditMode(stmt, idx);
            else if (action === 'save-stmt') saveStatementEdit(stmt, idx);
            else if (action === 'bulk-select') {
                toggleStatementSelection(btn.dataset.stmtId || stmt.id);
            }
            // v4.6.0: Review actions
            else if (action === 'review-approve' || action === 'review-reject') {
                const stmtId = parseInt(btn.dataset.stmtId || stmt.id);
                const newStatus = action === 'review-approve' ? 'reviewed' : 'rejected';
                handleReviewAction(stmtId, newStatus, stmt, idx);
            }
        };
        panel._sfhHandler = handler;
        panel.addEventListener('click', handler);
    }

    // =========================================================================
    // STATEMENT NAVIGATION
    // =========================================================================

    function getFilteredStatements() {
        let stmts = State.compareMode ? State.mergedStatements : State.currentStatements;
        stmts = stmts.filter(s => !s.is_header && s.description);
        if (State.activeFilter !== 'all') stmts = stmts.filter(s => s.directive === State.activeFilter);
        if (State.compareMode && State.activeDiffFilter !== 'all')
            stmts = stmts.filter(s => s._diff_status === State.activeDiffFilter);
        // v4.6.0: Review status filter
        if (State.activeReviewFilter !== 'all') {
            stmts = stmts.filter(s => (s.review_status || 'pending') === State.activeReviewFilter);
        }
        return stmts;
    }

    function navigateToStatement(direction) {
        // Throttle rapid navigation to prevent UI freeze
        if (_navThrottleTimer) return;
        _navThrottleTimer = setTimeout(() => { _navThrottleTimer = null; }, NAV_THROTTLE_MS);

        const filtered = State.filteredStatements;
        if (filtered.length === 0) return;

        let newIdx;
        if (State.currentStmtIndex < 0) {
            newIdx = direction === 'next' ? 0 : filtered.length - 1;
        } else if (direction === 'prev') {
            newIdx = State.currentStmtIndex > 0 ? State.currentStmtIndex - 1 : filtered.length - 1;
        } else {
            newIdx = State.currentStmtIndex < filtered.length - 1 ? State.currentStmtIndex + 1 : 0;
        }

        State.currentStmtIndex = newIdx;
        State.editMode = false; // exit edit mode on navigation
        const stmt = filtered[newIdx];

        // Find index in full statements array for highlight matching
        const origIdx = State.currentStatements.indexOf(stmt);

        showStatementDetail(stmt, origIdx);
        updateActiveHighlight(origIdx);
        scrollToStatement(origIdx);
    }

    // v4.5.1: Mark index cache for O(1) lookups instead of querySelectorAll on every navigation
    let _markIndexMap = null; // Map<stmtIndex string, mark element>
    let _activeMarkEl = null; // Currently active mark element (avoid full DOM scan to remove class)

    function buildMarkIndexMap(container) {
        const root = container || document.getElementById('sfh-doc-content');
        _markIndexMap = new Map();
        if (!root) return;
        const marks = root.querySelectorAll('.sfh-stmt-highlight');
        for (const m of marks) {
            const indices = m.dataset.stmtIndices;
            if (indices) {
                for (const idx of indices.split(',')) {
                    if (!_markIndexMap.has(idx)) _markIndexMap.set(idx, m);
                }
            }
            // Also index by primary data-stmt-index
            const primary = m.dataset.stmtIndex;
            if (primary && !_markIndexMap.has(primary)) _markIndexMap.set(primary, m);
        }
    }

    function findMarkForIndex(stmtIndex, container) {
        if (_markIndexMap && !container) {
            return _markIndexMap.get(String(stmtIndex)) || null;
        }
        // Fallback: direct DOM query (used when container is explicitly passed or cache not built)
        const root = container || document.getElementById('sfh-doc-content');
        if (!root) return null;
        const idxStr = String(stmtIndex);
        const marks = root.querySelectorAll('.sfh-stmt-highlight');
        for (const m of marks) {
            const indices = m.dataset.stmtIndices;
            if (indices) {
                const arr = indices.split(',');
                if (arr.includes(idxStr)) return m;
            }
        }
        return root.querySelector(`.sfh-stmt-highlight[data-stmt-index="${stmtIndex}"]`);
    }

    function updateActiveHighlight(stmtIndex) {
        // v4.5.1: O(1) — remove class from cached previous, add to new
        if (_activeMarkEl) {
            _activeMarkEl.classList.remove('sfh-active');
            _activeMarkEl = null;
        }
        const mark = findMarkForIndex(stmtIndex);
        if (mark) {
            mark.classList.add('sfh-active');
            _activeMarkEl = mark;
        }
    }

    function scrollToStatement(stmtIndex) {
        const mark = findMarkForIndex(stmtIndex);
        if (!mark) return;
        const docContent = document.getElementById('sfh-doc-content');
        if (!docContent) return;

        // Use instant scroll when navigating rapidly (< 300ms between clicks)
        const now = Date.now();
        const isRapid = (now - _lastNavTime) < 300;
        _lastNavTime = now;
        const scrollBehavior = isRapid ? 'auto' : 'smooth';

        try {
            const prevOverflow = document.body.style.overflow;
            document.body.style.overflow = 'hidden'; // Prevent page scroll
            mark.scrollIntoView({ behavior: scrollBehavior, block: 'center' });
            requestAnimationFrame(() => { document.body.style.overflow = prevOverflow; });
        } catch (_) {
            // Fallback: manual calculation
            const markRect = mark.getBoundingClientRect();
            const docRect = docContent.getBoundingClientRect();
            const markTopInDoc = markRect.top - docRect.top + docContent.scrollTop;
            const scrollTarget = markTopInDoc - (docContent.clientHeight / 3);
            docContent.scrollTo({ top: Math.max(0, scrollTarget), behavior: scrollBehavior });
        }
    }

    // =========================================================================
    // STATEMENT EDITING
    // =========================================================================

    function enterEditMode(stmt, idx) {
        State.editMode = true;
        showStatementDetail(stmt, idx);
        // v4.6.0: Populate role suggestions from adjudication cache
        populateRoleSuggestions();
    }

    // v4.6.0: Populate datalist with role names from adjudication cache
    async function populateRoleSuggestions() {
        const datalist = document.getElementById('sfh-role-suggestions');
        if (!datalist) return;
        try {
            if (AEGIS.AdjudicationLookup) {
                const data = await AEGIS.AdjudicationLookup.ensureLoaded();
                if (data && typeof data === 'object') {
                    datalist.innerHTML = Object.keys(data)
                        .sort()
                        .map(name => `<option value="${escapeHtml(name)}">`)
                        .join('');
                }
            }
        } catch (e) {
            log('Failed to populate role suggestions: ' + e, 'warn');
        }
    }

    function exitEditMode(stmt, idx) {
        State.editMode = false;
        showStatementDetail(stmt, idx);
    }

    async function saveStatementEdit(stmt, idx) {
        const panel = document.getElementById('sfh-detail-panel');
        if (!panel) return;

        const updates = {
            title: (panel.querySelector('#sfh-edit-title')?.value || '').trim(),
            description: (panel.querySelector('#sfh-edit-description')?.value || '').trim(),
            directive: panel.querySelector('#sfh-edit-directive')?.value || '',
            role: (panel.querySelector('#sfh-edit-role')?.value || '').trim(),
            level: parseInt(panel.querySelector('#sfh-edit-level')?.value) || 1
        };

        if (!updates.description) {
            if (typeof showToast === 'function') showToast('error', 'Description is required');
            return;
        }

        try {
            const data = await apiFetch(`/api/statement-forge/scan/statements/${stmt.id}`, {
                method: 'PUT',
                body: JSON.stringify(updates)
            });

            if (data.success) {
                // Update local state
                const oldDirective = stmt.directive;
                Object.assign(stmt, updates);

                // Update highlight color if directive changed
                if (oldDirective !== updates.directive) {
                    updateHighlightDirective(idx, updates.directive);
                }

                // Refresh filter counts
                State.filteredStatements = getFilteredStatements();
                updateFilterCounts();

                State.editMode = false;
                showStatementDetail(stmt, idx);

                if (typeof showToast === 'function') showToast('success', 'Statement updated');
            } else {
                // v5.9.2: Always exit edit mode on failure (prevents stuck state)
                State.editMode = false;
                showStatementDetail(stmt, idx);
                if (typeof showToast === 'function') showToast('error', data.error || 'Failed to update');
            }
        } catch (err) {
            log('Save statement error: ' + err, 'error');
            // v5.9.2: Always exit edit mode on exception (prevents stuck state)
            State.editMode = false;
            showStatementDetail(stmt, idx);
            if (typeof showToast === 'function') showToast('error', 'Failed to save changes');
        }
    }

    function updateHighlightDirective(stmtIndex, newDirective) {
        const mark = findMarkForIndex(stmtIndex);
        if (!mark) return;
        ['sfh-d-shall', 'sfh-d-must', 'sfh-d-will', 'sfh-d-should', 'sfh-d-may'].forEach(cls =>
            mark.classList.remove(cls)
        );
        if (newDirective) mark.classList.add(`sfh-d-${newDirective}`);
    }

    function updateFilterCounts() {
        // v4.5.1: Single pass to count all directives instead of N filter passes
        const counts = { all: 0 };
        for (const s of State.currentStatements) {
            if (s.is_header) continue;
            counts.all++;
            if (s.directive) counts[s.directive] = (counts[s.directive] || 0) + 1;
        }
        const chips = document.querySelectorAll('.sfh-chip');
        chips.forEach(chip => {
            const filter = chip.dataset.filter;
            const countSpan = chip.querySelector('.sfh-chip-count');
            if (countSpan) countSpan.textContent = counts[filter] || 0;
        });
    }

    function renderStatementsTable(statements) {
        if (!statements.length) return '<p>No statements found.</p>';
        return `
            <div class="sfh-stmts-table-wrap">
                <table class="sfh-stmts-table">
                    <thead>
                        <tr><th>#</th><th>Directive</th><th>Role</th><th>Description</th></tr>
                    </thead>
                    <tbody>
                        ${statements.filter(s => !s.is_header).map((s, i) => `
                            <tr>
                                <td>${escapeHtml(s.number || String(i + 1))}</td>
                                <td><span class="sfh-directive-pill sfh-${s.directive || 'none'}">${escapeHtml(s.directive || '-')}</span></td>
                                <td>${escapeHtml(s.role || '-')}</td>
                                <td>${escapeHtml((s.description || '').substring(0, 120))}${(s.description || '').length > 120 ? '...' : ''}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // =========================================================================
    // VIEW: UNIFIED COMPARE VIEWER
    // =========================================================================

    function buildMergedStatements(diff) {
        const modifiedMap = new Map();
        if (diff.modified) {
            diff.modified.forEach(m => {
                if (m.new && m.new.id) modifiedMap.set(m.new.id, m.old);
            });
        }
        const addedIds = new Set((diff.added || []).map(s => s.id));
        const removedIds = new Set((diff.removed || []).map(s => s.id));

        // Start with newer scan statements
        const merged = [];
        for (const stmt of (diff.statements_1 || [])) {
            const s = { ...stmt };
            if (addedIds.has(s.id)) {
                s._diff_status = 'added';
            } else if (modifiedMap.has(s.id)) {
                s._diff_status = 'modified_new';
                s._modified_from = modifiedMap.get(s.id);
            } else if (!s._diff_status || s._diff_status === 'unchanged') {
                s._diff_status = 'unchanged';
            }
            s._source = 'newer';
            merged.push(s);
        }

        // Insert removed statements from older scan at approximate positions
        const removedStmts = (diff.statements_2 || [])
            .filter(s => removedIds.has(s.id))
            .map(s => ({ ...s, _diff_status: 'removed', _source: 'older' }));

        for (const removed of removedStmts) {
            const rIdx = removed.position_index || 0;
            let insertAt = merged.findIndex(m => (m.position_index || 0) >= rIdx);
            if (insertAt === -1) insertAt = merged.length;
            merged.splice(insertAt, 0, removed);
        }

        return merged;
    }

    async function showCompareViewer(scanId1, scanId2, isBack = false) {
        State.currentView = 'compare';
        State.compareMode = true;
        State.compareScans = { left: scanId1, right: scanId2 };
        // v4.4.0: Force fresh document load for the compare scan
        State.documentText = '';
        State.htmlPreview = '';
        State.docFormat = 'text';

        const scan1Info = State.history.find(h => h.scan_id === scanId1);
        const scan2Info = State.history.find(h => h.scan_id === scanId2);
        State.compareScanInfo = { newer: scan1Info, older: scan2Info };
        updateBreadcrumb(`Compare: ${formatDate(scan1Info?.scan_time)} vs ${formatDate(scan2Info?.scan_time)}`);

        const content = State.modal.querySelector('.sfh-content');
        content.innerHTML = '<div class="sfh-loading"><div class="sfh-spinner"></div><p>Loading comparison...</p></div>';

        const [diff, docText] = await Promise.all([
            loadComparison(scanId1, scanId2),
            loadDocumentText(scanId1)
        ]);

        if (!diff) {
            content.innerHTML = '<div class="sfh-error"><p>Failed to load comparison data.</p></div>';
            return;
        }

        State.compareDiff = diff;
        const merged = buildMergedStatements(diff);
        State.mergedStatements = merged;
        State.currentStatements = merged;
        State.activeFilter = 'all';
        State.activeDiffFilter = 'all';
        State.filteredStatements = getFilteredStatements();
        State.currentStmtIndex = -1;
        State.editMode = false;

        const modCount = diff.modified_count || 0;

        // Count directives from merged (non-header)
        const nonHeader = merged.filter(s => !s.is_header && s.description);
        const directives = ['all', 'shall', 'must', 'will', 'should', 'may'];
        const diffStatuses = [
            { key: 'all', label: 'All', icon: 'layers' },
            { key: 'added', label: 'Added', icon: 'plus-circle', count: diff.added_count || 0 },
            { key: 'removed', label: 'Removed', icon: 'minus-circle', count: diff.removed_count || 0 },
            { key: 'modified_new', label: 'Changed', icon: 'refresh-cw', count: modCount },
            { key: 'unchanged', label: 'Unchanged', icon: 'check-circle', count: diff.unchanged_count || 0 }
        ];

        if (!docText) {
            content.innerHTML = `
                <div class="sfh-viewer-no-text">
                    <p>Document text not available. Showing diff summary only.</p>
                </div>`;
            refreshIcons(content);
            return;
        }

        content.innerHTML = `
            <div class="sfh-viewer sfh-compare-viewer">
                <!-- Diff Summary Bar -->
                <div class="sfh-diff-summary-bar">
                    <div class="sfh-diff-summary-item sfh-diff-sum-unchanged">
                        <i data-lucide="check-circle" style="width:14px;height:14px"></i>
                        <span>${diff.unchanged_count} unchanged</span>
                    </div>
                    <div class="sfh-diff-summary-item sfh-diff-sum-added">
                        <i data-lucide="plus-circle" style="width:14px;height:14px"></i>
                        <span>+${diff.added_count} added</span>
                    </div>
                    <div class="sfh-diff-summary-item sfh-diff-sum-removed">
                        <i data-lucide="minus-circle" style="width:14px;height:14px"></i>
                        <span>-${diff.removed_count} removed</span>
                    </div>
                    ${modCount > 0 ? `
                    <div class="sfh-diff-summary-item sfh-diff-sum-modified">
                        <i data-lucide="refresh-cw" style="width:14px;height:14px"></i>
                        <span>~${modCount} changed</span>
                    </div>` : ''}
                    <div class="sfh-diff-summary-item sfh-diff-sum-total">
                        <span>${diff.total_scan_1} → ${diff.total_scan_2} total</span>
                    </div>
                    <div class="sfh-compare-export-btns">
                        <button class="sfh-btn sfh-btn-sm sfh-export-csv" title="Export diff as CSV">
                            <i data-lucide="download" style="width:14px;height:14px"></i> CSV
                        </button>
                        <button class="sfh-btn sfh-btn-sm sfh-export-pdf" title="Export diff as PDF">
                            <i data-lucide="file-text" style="width:14px;height:14px"></i> PDF
                        </button>
                    </div>
                </div>

                <div class="sfh-viewer-toolbar">
                    <div class="sfh-filter-chips">
                        ${directives.map(d => `
                            <button class="sfh-chip ${d === 'all' ? 'sfh-chip-active' : ''}"
                                    data-filter="${d}">${d === 'all' ? 'All' : d.charAt(0).toUpperCase() + d.slice(1)}
                                <span class="sfh-chip-count">${d === 'all' ? nonHeader.length :
                                    nonHeader.filter(s => s.directive === d).length}</span>
                            </button>
                        `).join('')}
                    </div>
                    <div class="sfh-diff-chips">
                        ${diffStatuses.map(ds => `
                            <button class="sfh-chip sfh-chip-diff sfh-chip-diff-${ds.key} ${ds.key === 'all' ? 'sfh-chip-active' : ''}"
                                    data-diff-filter="${ds.key}">
                                ${ds.label}
                                ${ds.count !== undefined ? `<span class="sfh-chip-count">${ds.key === 'all' ? nonHeader.length : ds.count}</span>` : `<span class="sfh-chip-count">${nonHeader.length}</span>`}
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="sfh-viewer-split">
                    <div class="sfh-viewer-doc-panel">
                        <div class="sfh-viewer-doc-header">
                            <h4><i data-lucide="git-compare" style="width:16px;height:16px"></i> ${escapeHtml(State.documentName)}</h4>
                            <span class="sfh-viewer-hint">Click a highlight to see diff details. Select text to create a new statement.</span>
                        </div>
                        <div class="sfh-viewer-doc-content" id="sfh-doc-content">
                            ${renderDocument(docText, merged, { isCompare: true })}
                        </div>
                    </div>
                    <div class="sfh-viewer-detail-panel" id="sfh-detail-panel">
                    </div>
                </div>
            </div>
        `;

        // Populate detail panel empty state (with jump button if statements exist)
        resetDetailPanel();

        // Wire events
        const docContent = content.querySelector('#sfh-doc-content');

        // v4.5.1: Build mark index cache for O(1) lookups during navigation
        buildMarkIndexMap(docContent);
        _activeMarkEl = null;

        // Highlight click → show detail + update navigation state
        docContent.addEventListener('click', (e) => {
            const mark = e.target.closest('.sfh-stmt-highlight');
            if (mark) {
                const idx = parseInt(mark.dataset.stmtIndex);
                const stmt = State.currentStatements[idx];
                if (!stmt) return;
                State.currentStmtIndex = State.filteredStatements.findIndex(s => s === stmt || s.id === stmt.id);
                State.editMode = false;
                showStatementDetail(stmt, idx);
                updateActiveHighlight(idx);
            }
        });

        // Text selection → highlight-to-create
        docContent.addEventListener('mouseup', handleTextSelection);

        // v4.5.1: Shared re-render helper for compare filter chips (deduplicates code)
        function reRenderCompareDoc() {
            const filteredForRender = State.activeFilter === 'all' ? merged :
                merged.filter(s => s.directive === State.activeFilter);
            const furtherFiltered = State.activeDiffFilter === 'all' ? filteredForRender :
                filteredForRender.filter(s => s._diff_status === State.activeDiffFilter);
            docContent.innerHTML = renderDocument(docText, furtherFiltered, { isCompare: true });
            buildMarkIndexMap(docContent);
            _activeMarkEl = null;
            resetDetailPanel();
        }

        // Directive filter chips
        content.querySelectorAll('.sfh-chip:not(.sfh-chip-diff)').forEach(chip => {
            chip.addEventListener('click', () => {
                content.querySelectorAll('.sfh-chip:not(.sfh-chip-diff)').forEach(c => c.classList.remove('sfh-chip-active'));
                chip.classList.add('sfh-chip-active');

                State.activeFilter = chip.dataset.filter;
                State.filteredStatements = getFilteredStatements();
                State.currentStmtIndex = -1;
                State.editMode = false;
                reRenderCompareDoc();
            });
        });

        // Diff status filter chips
        content.querySelectorAll('.sfh-chip-diff').forEach(chip => {
            chip.addEventListener('click', () => {
                content.querySelectorAll('.sfh-chip-diff').forEach(c => c.classList.remove('sfh-chip-active'));
                chip.classList.add('sfh-chip-active');

                State.activeDiffFilter = chip.dataset.diffFilter;
                State.filteredStatements = getFilteredStatements();
                State.currentStmtIndex = -1;
                State.editMode = false;
                reRenderCompareDoc();
            });
        });

        // v4.4.0: Export buttons (use iframe to avoid popup blocker issues after async operations)
        content.querySelector('.sfh-export-csv')?.addEventListener('click', () => {
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = `/api/statement-forge/compare/${scanId1}/${scanId2}/export-csv`;
            document.body.appendChild(iframe);
            setTimeout(() => document.body.removeChild(iframe), 30000);
        });
        content.querySelector('.sfh-export-pdf')?.addEventListener('click', () => {
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = `/api/statement-forge/compare/${scanId1}/${scanId2}/export-pdf`;
            document.body.appendChild(iframe);
            setTimeout(() => document.body.removeChild(iframe), 30000);
        });

        refreshIcons(content);
        updateFooterShortcuts();
    }

    function resetDetailPanel() {
        const detailPanel = document.getElementById('sfh-detail-panel');
        if (!detailPanel) return;
        const hasStmts = State.filteredStatements && State.filteredStatements.length > 0;
        const icon = State.compareMode ? 'git-compare' : 'mouse-pointer-click';
        const msg = State.compareMode ? 'diff details' : 'details';
        detailPanel.innerHTML = `
            <div class="sfh-detail-empty">
                <i data-lucide="${icon}" style="width:32px;height:32px;opacity:0.3"></i>
                <p>Click a highlighted statement to see ${msg}</p>
                ${hasStmts ? `<button class="sfh-btn-jump-first">
                    <i data-lucide="arrow-down-to-line" style="width:14px;height:14px"></i>
                    Jump to first statement
                </button>` : ''}
            </div>`;
        refreshIcons(detailPanel);

        // Wire jump button
        const jumpBtn = detailPanel.querySelector('.sfh-btn-jump-first');
        if (jumpBtn) {
            jumpBtn.addEventListener('click', () => navigateToStatement('next'));
        }
    }

    function fingerprint(stmt) {
        const desc = (stmt.description || '').substring(0, 100).trim().toLowerCase();
        const directive = (stmt.directive || '').toLowerCase();
        const role = (stmt.role || '').toLowerCase();
        return `${desc}|${directive}|${role}`;
    }

    function navigateToNextDiffStatus(status) {
        const filtered = State.filteredStatements;
        if (filtered.length === 0) return;
        const startIdx = State.currentStmtIndex >= 0 ? State.currentStmtIndex + 1 : 0;
        // Search forward from current, wrapping around
        for (let i = 0; i < filtered.length; i++) {
            const idx = (startIdx + i) % filtered.length;
            if (filtered[idx]._diff_status === status || filtered[idx]._diff_status === status + '_new') {
                State.currentStmtIndex = idx;
                State.editMode = false;
                const stmt = filtered[idx];
                const origIdx = State.currentStatements.indexOf(stmt);
                showStatementDetail(stmt, origIdx);
                updateActiveHighlight(origIdx);
                scrollToStatement(origIdx);
                return;
            }
        }
    }

    // =========================================================================
    // HIGHLIGHT-TO-CREATE STATEMENT
    // =========================================================================

    function handleTextSelection(e) {
        const selection = window.getSelection();
        const text = selection.toString().trim();

        // Remove existing create popup
        const existing = document.querySelector('.sfh-create-popup');
        if (existing) existing.remove();

        if (!text || text.length < 10) return;

        State.selection = text;

        // Create popup near selection
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        const docPanel = document.querySelector('.sfh-viewer-doc-panel');
        const panelRect = docPanel?.getBoundingClientRect() || { left: 0, top: 0 };

        const popup = document.createElement('div');
        popup.className = 'sfh-create-popup';
        popup.innerHTML = `
            <div class="sfh-create-popup-content">
                <div class="sfh-create-popup-header">Create Statement from Selection</div>
                <div class="sfh-create-preview">"${escapeHtml(text.substring(0, 100))}${text.length > 100 ? '...' : ''}"</div>
                <div class="sfh-create-fields">
                    <select class="sfh-create-directive" title="Directive">
                        <option value="">No directive</option>
                        <option value="shall">Shall</option>
                        <option value="must">Must</option>
                        <option value="will">Will</option>
                        <option value="should">Should</option>
                        <option value="may">May</option>
                    </select>
                    <input class="sfh-create-role" placeholder="Role (optional)" title="Role">
                </div>
                <div class="sfh-create-actions">
                    <button class="sfh-btn sfh-btn-primary sfh-create-confirm">
                        <i data-lucide="plus" style="width:14px;height:14px"></i> Create Statement
                    </button>
                    <button class="sfh-btn sfh-btn-ghost sfh-create-cancel">Cancel</button>
                </div>
            </div>
        `;

        // Position popup
        popup.style.position = 'fixed';
        popup.style.left = Math.min(rect.left, window.innerWidth - 340) + 'px';
        popup.style.top = (rect.bottom + 8) + 'px';
        popup.style.zIndex = '10010';

        document.body.appendChild(popup);
        refreshIcons(popup);

        // Auto-detect directive
        const directiveSelect = popup.querySelector('.sfh-create-directive');
        const textLower = text.toLowerCase();
        if (textLower.includes(' shall ')) directiveSelect.value = 'shall';
        else if (textLower.includes(' must ')) directiveSelect.value = 'must';
        else if (textLower.includes(' will ')) directiveSelect.value = 'will';
        else if (textLower.includes(' should ')) directiveSelect.value = 'should';
        else if (textLower.includes(' may ')) directiveSelect.value = 'may';

        // Events
        popup.querySelector('.sfh-create-confirm').addEventListener('click', () => {
            const directive = directiveSelect.value;
            const role = popup.querySelector('.sfh-create-role').value.trim();
            createStatementFromSelection(text, directive, role);
            popup.remove();
        });

        popup.querySelector('.sfh-create-cancel').addEventListener('click', () => {
            popup.remove();
            State.selection = null;
        });

        // Close on click outside
        setTimeout(() => {
            document.addEventListener('mousedown', function handler(ev) {
                if (!popup.contains(ev.target)) {
                    popup.remove();
                    document.removeEventListener('mousedown', handler);
                }
            });
        }, 100);
    }

    async function createStatementFromSelection(text, directive, role) {
        try {
            const data = await apiFetch('/api/statement-forge/statements/add', {
                method: 'POST',
                body: JSON.stringify({
                    title: text.substring(0, 60).trim(),
                    description: text,
                    directive: directive,
                    role: role,
                    level: 2
                })
            });

            if (data.success) {
                if (typeof showToast === 'function') {
                    showToast('success', 'Statement created from selection');
                }
            } else {
                if (typeof showToast === 'function') {
                    showToast('error', 'Failed to create statement: ' + (data.error || 'Unknown error'));
                }
            }
        } catch (err) {
            log('Create statement error: ' + err, 'error');
            if (typeof showToast === 'function') {
                showToast('error', 'Failed to create statement');
            }
        }

        State.selection = null;
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        VERSION,
        open,
        close,
        isOpen: () => State.isOpen,
        showOverview,
        showDocumentViewer,
        showCompareViewer,
        getState: () => ({ ...State })
    };

})();
