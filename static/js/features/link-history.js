/**
 * Link History Module
 * ===================
 * Manages persistent exclusions and scan history for the Hyperlink Validator.
 * Integrates with Portfolio as a separate tab.
 *
 * @version 1.0.0
 */

window.LinkHistory = (function() {
    'use strict';

    // =========================================================================
    // STATE
    // =========================================================================

    const state = {
        initialized: false,
        isOpen: false,
        activeTab: 'exclusions', // 'exclusions' or 'scans'
        exclusions: [],
        scans: [],
        exclusionStats: null,
        scanStats: null,
        isLoading: false,
        error: null
    };

    // DOM element cache
    let el = {
        modal: null,
        tabExclusions: null,
        tabScans: null,
        contentExclusions: null,
        contentScans: null,
        exclusionsList: null,
        scansList: null,
        addExclusionForm: null,
        statsExclusions: null,
        statsScans: null
    };

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    async function init() {
        if (state.initialized) return true;

        console.log('[TWR LinkHistory] Initializing...');

        createModal();
        cacheElements();
        bindEvents();

        state.initialized = true;
        console.log('[TWR LinkHistory] Module ready');

        return true;
    }

    function createModal() {
        // Check if modal already exists
        if (document.getElementById('link-history-modal')) {
            el.modal = document.getElementById('link-history-modal');
            return;
        }

        const modal = document.createElement('div');
        modal.id = 'link-history-modal';
        modal.className = 'lh-modal';
        modal.innerHTML = `
            <div class="lh-modal-content">
                <!-- Header -->
                <div class="lh-header">
                    <div class="lh-header-left">
                        <div class="lh-logo">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                                <line x1="4" y1="4" x2="20" y2="20" stroke-dasharray="2 2"/>
                            </svg>
                            <span class="lh-title">Link History</span>
                        </div>
                        <div class="lh-subtitle">Exclusions & Scan History</div>
                    </div>
                    <div class="lh-header-center">
                        <div class="lh-tabs">
                            <button class="lh-tab lh-tab-active" data-tab="exclusions">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                                </svg>
                                <span>Exclusions</span>
                                <span class="lh-tab-count" id="lh-exclusion-count">0</span>
                            </button>
                            <button class="lh-tab" data-tab="scans">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                                </svg>
                                <span>Scan History</span>
                                <span class="lh-tab-count" id="lh-scan-count">0</span>
                            </button>
                        </div>
                    </div>
                    <div class="lh-header-right">
                        <button class="lh-close-btn" id="lh-close-btn" title="Close">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="lh-body">
                    <!-- Exclusions Tab -->
                    <div class="lh-content lh-content-active" id="lh-content-exclusions">
                        <!-- Add Exclusion Form -->
                        <div class="lh-add-form" id="lh-add-exclusion-form">
                            <div class="lh-form-row">
                                <input type="text" id="lh-new-pattern" placeholder="Enter URL pattern (domain, URL, or regex)" class="lh-input">
                                <select id="lh-new-match-type" class="lh-select">
                                    <option value="contains">Contains</option>
                                    <option value="exact">Exact Match</option>
                                    <option value="prefix">Starts With</option>
                                    <option value="suffix">Ends With</option>
                                    <option value="regex">Regex</option>
                                </select>
                                <button id="lh-btn-add-exclusion" class="lh-btn lh-btn-primary">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="12" y1="5" x2="12" y2="19"/>
                                        <line x1="5" y1="12" x2="19" y2="12"/>
                                    </svg>
                                    Add Exclusion
                                </button>
                            </div>
                            <div class="lh-form-row lh-form-row-secondary">
                                <input type="text" id="lh-new-reason" placeholder="Reason (optional)" class="lh-input lh-input-small">
                                <label class="lh-checkbox-label">
                                    <input type="checkbox" id="lh-new-treat-valid" checked>
                                    <span>Treat as valid</span>
                                </label>
                            </div>
                        </div>

                        <!-- Stats Bar -->
                        <div class="lh-stats-bar" id="lh-stats-exclusions">
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-total-exclusions">0</span>
                                <span class="lh-stat-label">Total</span>
                            </div>
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-active-exclusions">0</span>
                                <span class="lh-stat-label">Active</span>
                            </div>
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-total-hits">0</span>
                                <span class="lh-stat-label">Total Hits</span>
                            </div>
                        </div>

                        <!-- Exclusions List -->
                        <div class="lh-list-container">
                            <table class="lh-table">
                                <thead>
                                    <tr>
                                        <th>Pattern</th>
                                        <th>Match Type</th>
                                        <th>Reason</th>
                                        <th>Hits</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="lh-exclusions-list">
                                    <tr class="lh-loading-row">
                                        <td colspan="6">Loading exclusions...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Scans Tab -->
                    <div class="lh-content" id="lh-content-scans">
                        <!-- Stats Bar -->
                        <div class="lh-stats-bar" id="lh-stats-scans">
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-total-scans">0</span>
                                <span class="lh-stat-label">Total Scans</span>
                            </div>
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-urls-scanned">0</span>
                                <span class="lh-stat-label">URLs Scanned</span>
                            </div>
                            <div class="lh-stat">
                                <span class="lh-stat-value" id="lh-stat-success-rate">0%</span>
                                <span class="lh-stat-label">Avg Success</span>
                            </div>
                            <div class="lh-stat-action">
                                <button id="lh-btn-clear-history" class="lh-btn lh-btn-danger-subtle">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                    </svg>
                                    Clear Old
                                </button>
                            </div>
                        </div>

                        <!-- Scans List -->
                        <div class="lh-list-container">
                            <table class="lh-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Source</th>
                                        <th>URLs</th>
                                        <th>Working</th>
                                        <th>Broken</th>
                                        <th>Mode</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="lh-scans-list">
                                    <tr class="lh-loading-row">
                                        <td colspan="7">Loading scan history...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        el.modal = modal;

        // Initialize Lucide icons if available
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    function cacheElements() {
        el.modal = document.getElementById('link-history-modal');
        el.tabExclusions = el.modal?.querySelector('[data-tab="exclusions"]');
        el.tabScans = el.modal?.querySelector('[data-tab="scans"]');
        el.contentExclusions = document.getElementById('lh-content-exclusions');
        el.contentScans = document.getElementById('lh-content-scans');
        el.exclusionsList = document.getElementById('lh-exclusions-list');
        el.scansList = document.getElementById('lh-scans-list');
        el.addExclusionForm = document.getElementById('lh-add-exclusion-form');
        el.statsExclusions = document.getElementById('lh-stats-exclusions');
        el.statsScans = document.getElementById('lh-stats-scans');
    }

    function bindEvents() {
        // Close button
        document.getElementById('lh-close-btn')?.addEventListener('click', close);

        // Tab switching
        el.modal?.querySelectorAll('.lh-tab').forEach(tab => {
            tab.addEventListener('click', () => switchTab(tab.dataset.tab));
        });

        // Add exclusion
        document.getElementById('lh-btn-add-exclusion')?.addEventListener('click', handleAddExclusion);
        document.getElementById('lh-new-pattern')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleAddExclusion();
        });

        // Clear history
        document.getElementById('lh-btn-clear-history')?.addEventListener('click', handleClearHistory);

        // Close on outside click
        el.modal?.addEventListener('click', (e) => {
            if (e.target === el.modal) close();
        });

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isOpen) close();
        });
    }

    // =========================================================================
    // MODAL CONTROL
    // =========================================================================

    async function open() {
        await init();

        state.isOpen = true;
        el.modal?.classList.add('lh-active');
        document.body.classList.add('lh-modal-open');

        // Load data
        await loadData();
    }

    function close() {
        state.isOpen = false;
        el.modal?.classList.remove('lh-active');
        document.body.classList.remove('lh-modal-open');

        // v4.6.1: Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage) {
            TWR.LandingPage.show();
        }
    }

    function switchTab(tabName) {
        state.activeTab = tabName;

        // Update tab buttons
        el.modal?.querySelectorAll('.lh-tab').forEach(tab => {
            tab.classList.toggle('lh-tab-active', tab.dataset.tab === tabName);
        });

        // Update content panels
        el.contentExclusions?.classList.toggle('lh-content-active', tabName === 'exclusions');
        el.contentScans?.classList.toggle('lh-content-active', tabName === 'scans');

        // Load tab-specific data if needed
        if (tabName === 'exclusions' && state.exclusions.length === 0) {
            loadExclusions();
        } else if (tabName === 'scans' && state.scans.length === 0) {
            loadScans();
        }
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async function loadData() {
        state.isLoading = true;

        try {
            await Promise.all([
                loadExclusions(),
                loadScans(),
                loadExclusionStats(),
                loadScanStats()
            ]);
        } catch (e) {
            console.error('[TWR LinkHistory] Error loading data:', e);
            state.error = e.message;
        } finally {
            state.isLoading = false;
        }
    }

    async function loadExclusions() {
        try {
            const response = await fetch('/api/hyperlink-validator/exclusions');
            const data = await response.json();

            if (data.success) {
                state.exclusions = data.exclusions || [];
                renderExclusions();
                updateExclusionCount();
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to load exclusions:', e);
        }
    }

    async function loadScans() {
        try {
            const response = await fetch('/api/hyperlink-validator/history?limit=50');
            const data = await response.json();

            if (data.success) {
                state.scans = data.scans || [];
                renderScans();
                updateScanCount();
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to load scans:', e);
        }
    }

    async function loadExclusionStats() {
        try {
            const response = await fetch('/api/hyperlink-validator/exclusions/stats');
            const data = await response.json();

            if (data.success) {
                state.exclusionStats = data.stats;
                renderExclusionStats();
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to load exclusion stats:', e);
        }
    }

    async function loadScanStats() {
        try {
            const response = await fetch('/api/hyperlink-validator/history/stats');
            const data = await response.json();

            if (data.success) {
                state.scanStats = data.stats;
                renderScanStats();
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to load scan stats:', e);
        }
    }

    // =========================================================================
    // RENDERING
    // =========================================================================

    function renderExclusions() {
        if (!el.exclusionsList) return;

        if (state.exclusions.length === 0) {
            el.exclusionsList.innerHTML = `
                <tr class="lh-empty-row">
                    <td colspan="6">
                        <div class="lh-empty-state">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                            </svg>
                            <p>No exclusions yet</p>
                            <span>Add patterns above to exclude URLs from validation</span>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        el.exclusionsList.innerHTML = state.exclusions.map(exc => `
            <tr class="${exc.is_active ? '' : 'lh-row-inactive'}">
                <td class="lh-col-pattern">
                    <code>${escapeHtml(exc.pattern)}</code>
                </td>
                <td class="lh-col-type">
                    <span class="lh-badge lh-badge-${exc.match_type}">${exc.match_type}</span>
                </td>
                <td class="lh-col-reason">${escapeHtml(exc.reason || '-')}</td>
                <td class="lh-col-hits">${exc.hit_count || 0}</td>
                <td class="lh-col-date">${formatDate(exc.created_at)}</td>
                <td class="lh-col-actions">
                    <button class="lh-btn-icon lh-btn-toggle" data-id="${exc.id}" data-active="${exc.is_active}" title="${exc.is_active ? 'Disable' : 'Enable'}">
                        ${exc.is_active ?
                            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>' :
                            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
                        }
                    </button>
                    <button class="lh-btn-icon lh-btn-delete" data-id="${exc.id}" title="Delete">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');

        // Bind action buttons
        el.exclusionsList.querySelectorAll('.lh-btn-toggle').forEach(btn => {
            btn.addEventListener('click', () => handleToggleExclusion(btn.dataset.id, btn.dataset.active === 'true'));
        });
        el.exclusionsList.querySelectorAll('.lh-btn-delete').forEach(btn => {
            btn.addEventListener('click', () => handleDeleteExclusion(btn.dataset.id));
        });
    }

    function renderScans() {
        if (!el.scansList) return;

        if (state.scans.length === 0) {
            el.scansList.innerHTML = `
                <tr class="lh-empty-row">
                    <td colspan="7">
                        <div class="lh-empty-state">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                            </svg>
                            <p>No scan history</p>
                            <span>Completed validations will appear here</span>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        el.scansList.innerHTML = state.scans.map(scan => {
            const successRate = scan.total_urls > 0
                ? Math.round((scan.working / scan.total_urls) * 100)
                : 0;
            const successClass = successRate >= 90 ? 'success' : successRate >= 70 ? 'warning' : 'error';

            return `
                <tr>
                    <td class="lh-col-date">${formatDateTime(scan.scan_time)}</td>
                    <td class="lh-col-source">
                        <span class="lh-source-badge lh-source-${scan.source_type}">${scan.source_type}</span>
                        ${scan.source_name ? `<span class="lh-source-name">${escapeHtml(scan.source_name)}</span>` : ''}
                    </td>
                    <td class="lh-col-urls">${scan.total_urls}</td>
                    <td class="lh-col-working">
                        <span class="lh-status-badge lh-status-working">${scan.working}</span>
                    </td>
                    <td class="lh-col-broken">
                        <span class="lh-status-badge lh-status-broken">${scan.broken}</span>
                    </td>
                    <td class="lh-col-mode">${scan.validation_mode}</td>
                    <td class="lh-col-actions">
                        <button class="lh-btn-icon lh-btn-view" data-id="${scan.id}" title="View Details">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                        </button>
                        <button class="lh-btn-icon lh-btn-delete" data-id="${scan.id}" title="Delete">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // Bind action buttons
        el.scansList.querySelectorAll('.lh-btn-view').forEach(btn => {
            btn.addEventListener('click', () => handleViewScan(btn.dataset.id));
        });
        el.scansList.querySelectorAll('.lh-btn-delete').forEach(btn => {
            btn.addEventListener('click', () => handleDeleteScan(btn.dataset.id));
        });
    }

    function renderExclusionStats() {
        if (!state.exclusionStats) return;

        const stats = state.exclusionStats;
        document.getElementById('lh-stat-total-exclusions').textContent = stats.total_exclusions || 0;
        document.getElementById('lh-stat-active-exclusions').textContent = stats.active_exclusions || 0;
        document.getElementById('lh-stat-total-hits').textContent = stats.total_hits || 0;
    }

    function renderScanStats() {
        if (!state.scanStats) return;

        const stats = state.scanStats;
        // v4.6.2-fix: Guard against null DOM elements (these only exist when Link History panel is open)
        const totalEl = document.getElementById('lh-stat-total-scans');
        const urlsEl = document.getElementById('lh-stat-urls-scanned');
        const rateEl = document.getElementById('lh-stat-success-rate');
        if (totalEl) totalEl.textContent = stats.total_scans || 0;
        if (urlsEl) urlsEl.textContent = formatNumber(stats.total_urls_scanned || 0);
        if (rateEl) rateEl.textContent = `${stats.avg_success_rate || 0}%`;
    }

    function updateExclusionCount() {
        const countEl = document.getElementById('lh-exclusion-count');
        if (countEl) {
            countEl.textContent = state.exclusions.length;
        }
    }

    function updateScanCount() {
        const countEl = document.getElementById('lh-scan-count');
        if (countEl) {
            countEl.textContent = state.scans.length;
        }
    }

    // =========================================================================
    // EVENT HANDLERS
    // =========================================================================

    async function handleAddExclusion() {
        const patternInput = document.getElementById('lh-new-pattern');
        const matchTypeSelect = document.getElementById('lh-new-match-type');
        const reasonInput = document.getElementById('lh-new-reason');
        const treatValidCheckbox = document.getElementById('lh-new-treat-valid');

        const pattern = patternInput?.value.trim();
        if (!pattern) {
            showToast('error', 'Please enter a pattern');
            return;
        }

        const matchType = matchTypeSelect?.value || 'contains';
        const reason = reasonInput?.value.trim() || '';
        const treatAsValid = treatValidCheckbox?.checked ?? true;

        try {
            const response = await fetch('/api/hyperlink-validator/exclusions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pattern,
                    match_type: matchType,
                    reason,
                    treat_as_valid: treatAsValid
                })
            });

            const data = await response.json();

            if (data.success) {
                // Clear form
                patternInput.value = '';
                reasonInput.value = '';

                // Reload exclusions
                await loadExclusions();
                await loadExclusionStats();

                showToast('success', 'Exclusion added');

                // Sync with validator if open
                syncWithValidator();
            } else {
                showToast('error', data.error?.message || 'Failed to add exclusion');
            }
        } catch (e) {
            showToast('error', 'Failed to add exclusion');
        }
    }

    async function handleToggleExclusion(id, currentlyActive) {
        try {
            const response = await fetch(`/api/hyperlink-validator/exclusions/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !currentlyActive })
            });

            const data = await response.json();

            if (data.success) {
                await loadExclusions();
                await loadExclusionStats();
                syncWithValidator();
            }
        } catch (e) {
            showToast('error', 'Failed to update exclusion');
        }
    }

    async function handleDeleteExclusion(id) {
        if (!confirm('Delete this exclusion?')) return;

        try {
            const response = await fetch(`/api/hyperlink-validator/exclusions/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                await loadExclusions();
                await loadExclusionStats();
                showToast('success', 'Exclusion deleted');
                syncWithValidator();
            }
        } catch (e) {
            showToast('error', 'Failed to delete exclusion');
        }
    }

    async function handleViewScan(id) {
        try {
            const response = await fetch(`/api/hyperlink-validator/history/${id}`);
            const data = await response.json();

            if (data.success && data.results) {
                // Open in validator with these results
                if (window.HyperlinkValidator) {
                    window.HyperlinkValidator.open();
                    // Could expand to load historical results
                }
                showToast('info', `Scan had ${data.scan.total_urls} URLs`);
            }
        } catch (e) {
            showToast('error', 'Failed to load scan details');
        }
    }

    async function handleDeleteScan(id) {
        if (!confirm('Delete this scan record?')) return;

        try {
            const response = await fetch(`/api/hyperlink-validator/history/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                await loadScans();
                await loadScanStats();
                showToast('success', 'Scan deleted');
            }
        } catch (e) {
            showToast('error', 'Failed to delete scan');
        }
    }

    async function handleClearHistory() {
        const days = prompt('Keep scans from the last N days:', '90');
        if (days === null) return;

        const daysNum = parseInt(days, 10);
        if (isNaN(daysNum) || daysNum < 1) {
            showToast('error', 'Please enter a valid number of days');
            return;
        }

        try {
            const response = await fetch('/api/hyperlink-validator/history/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days_to_keep: daysNum })
            });

            const data = await response.json();

            if (data.success) {
                await loadScans();
                await loadScanStats();
                showToast('success', `Deleted ${data.deleted} old scan records`);
            }
        } catch (e) {
            showToast('error', 'Failed to clear history');
        }
    }

    // =========================================================================
    // SYNC WITH VALIDATOR
    // =========================================================================

    function syncWithValidator() {
        // Sync exclusions with the HyperlinkValidatorState
        if (window.HyperlinkValidatorState) {
            // Convert to the format expected by the validator
            const exclusions = state.exclusions
                .filter(e => e.is_active)
                .map(e => ({
                    pattern: e.pattern,
                    match_type: e.match_type,
                    reason: e.reason,
                    treat_as_valid: e.treat_as_valid
                }));

            window.HyperlinkValidatorState.setExclusions(exclusions);
        }
    }

    /**
     * Load exclusions from storage and sync with validator state.
     * Called when validator opens to get persistent exclusions.
     */
    async function loadAndSyncExclusions() {
        try {
            const response = await fetch('/api/hyperlink-validator/exclusions?active_only=true');
            const data = await response.json();

            if (data.success) {
                state.exclusions = data.exclusions || [];
                syncWithValidator();
                return state.exclusions;
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to load exclusions:', e);
        }
        return [];
    }

    /**
     * Save a scan to history.
     * Called after validation completes.
     */
    async function recordScan(scanData) {
        try {
            const response = await fetch('/api/hyperlink-validator/history/record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scanData)
            });

            const data = await response.json();

            if (data.success) {
                // Refresh if history panel is open
                if (state.isOpen && state.activeTab === 'scans') {
                    await loadScans();
                    await loadScanStats();
                }
            }
        } catch (e) {
            console.error('[TWR LinkHistory] Failed to record scan:', e);
        }
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    function formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString();
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    function showToast(type, message) {
        if (typeof TWR !== 'undefined' && TWR.Modals?.toast) {
            TWR.Modals.toast(type, message);
        } else {
            console.log(`[TWR LinkHistory] ${type}: ${message}`);
        }
    }

    /**
     * Refresh the scans list (called from external modules).
     */
    async function refreshScans() {
        await loadScans();
        await loadScanStats();
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        init,
        open,
        close,
        loadAndSyncExclusions,
        recordScan,
        refreshScans,
        getExclusions: () => state.exclusions,
        isOpen: () => state.isOpen
    };

})();
