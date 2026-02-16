/**
 * AEGIS History Tab Fix + Scan Recall
 * ===============================================
 * Fixes the History tab and adds scan recall + management features.
 * 
 * Version: 3.0.54b
 * 
 * Features:
 * 1. Loads history data when History tab is clicked
 * 2. Adds "Load" button to recall previous scans
 * 3. Adds "Clear" buttons for storage management
 * 4. Shows storage statistics
 * 5. Displays recalled scans with visual indicator
 */

(function() {
    'use strict';

    // v4.7.0-fix: Prevent duplicate initialization on SPA navigation
    if (window.__TWR_historyFixesLoaded) return;
    window.__TWR_historyFixesLoaded = true;

    console.log('[TWR] Loading history-fixes v3.0.111...');

    let initAttempts = 0;
    const maxAttempts = 50;
    
    // Track if we're viewing a recalled scan
    let isViewingRecalledScan = false;
    let recalledScanInfo = null;
    
    function initHistoryFixes() {
        initAttempts++;
        
        const navHistory = document.getElementById('nav-history');
        
        if (!navHistory) {
            if (initAttempts < maxAttempts) {
                setTimeout(initHistoryFixes, 100);
                return;
            }
            console.warn('[TWR] History fixes: nav-history button not found');
            return;
        }
        
        // Override the renderScanHistory function to add our buttons
        overrideRenderFunction();
        
        // Add capturing phase listener for loading data
        navHistory.addEventListener('click', async function(e) {
            console.log('[TWR] History tab clicked - loading data...');
            try {
                await loadHistoryData();
            } catch (err) {
                console.error('[TWR] Error loading history:', err);
            }
        }, true);
        
        // Fix the refresh button
        const refreshBtn = document.getElementById('btn-refresh-history');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async function() {
                try {
                    await loadHistoryData();
                } catch (err) {
                    console.error('[TWR] Error refreshing history:', err);
                }
            });
        }
        
        // Fix the top nav Roles button (events.js uses wrong modal ID 'modal-roles-report')
        const navRoles = document.getElementById('nav-roles');
        if (navRoles) {
            navRoles.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent the broken handler
                console.log('[TWR] Roles nav clicked - calling showRolesModal');
                if (typeof window.showRolesModal === 'function') {
                    window.showRolesModal();
                } else if (window.TWR?.Roles?.showRolesModal) {
                    window.TWR.Roles.showRolesModal();
                } else if (typeof window.showModal === 'function') {
                    window.showModal('modal-roles'); // Correct modal ID
                }
            }, true); // Capturing phase to run before the broken handler
        }

        // Add Compare nav button handler (v3.0.110)
        const navCompare = document.getElementById('nav-compare');
        if (navCompare) {
            navCompare.addEventListener('click', function(e) {
                e.preventDefault();
                openCompareFromNav();
            });
        }

        // Add Portfolio nav button handler (v3.0.114)
        const navPortfolio = document.getElementById('nav-portfolio');
        if (navPortfolio) {
            navPortfolio.addEventListener('click', function(e) {
                e.preventDefault();
                if (window.Portfolio && typeof window.Portfolio.open === 'function') {
                    window.Portfolio.open();
                } else {
                    console.error('[Portfolio] Module not loaded');
                }
            });
        }

        // Add Hyperlink Validator nav button handler (v1.0.0)
        const navHyperlinkValidator = document.getElementById('nav-hyperlink-validator');
        if (navHyperlinkValidator) {
            navHyperlinkValidator.addEventListener('click', function(e) {
                e.preventDefault();
                if (window.HyperlinkValidator && typeof window.HyperlinkValidator.open === 'function') {
                    window.HyperlinkValidator.open();
                } else {
                    console.error('[HyperlinkValidator] Module not loaded');
                }
            });
        }

        // Add Link History nav button handler (v1.0.0)
        const navLinkHistory = document.getElementById('nav-link-history');
        if (navLinkHistory) {
            navLinkHistory.addEventListener('click', function(e) {
                e.preventDefault();
                if (window.LinkHistory && typeof window.LinkHistory.open === 'function') {
                    window.LinkHistory.open();
                } else {
                    console.error('[LinkHistory] Module not loaded');
                }
            });
        }

        // Add event delegation for all history modal buttons
        const historyModal = document.getElementById('modal-scan-history');
        if (historyModal) {
            historyModal.addEventListener('click', async function(e) {
                // Load scan button
                const loadBtn = e.target.closest('[data-action="load-scan"]');
                if (loadBtn) {
                    const scanId = parseInt(loadBtn.dataset.scanId, 10);
                    const filename = loadBtn.dataset.filename;
                    if (scanId) {
                        await recallScan(scanId, filename);
                    }
                    return;
                }
                
                // Clear all button
                if (e.target.closest('#btn-clear-all-history')) {
                    await clearAllHistory();
                    return;
                }
                
                // Clear old button
                if (e.target.closest('#btn-clear-old-history')) {
                    await clearOldHistory();
                    return;
                }

                // View statements button (v4.1.0)
                const stmtBtn = e.target.closest('[data-action="view-statements"]');
                if (stmtBtn) {
                    const scanId = parseInt(stmtBtn.dataset.scanId, 10);
                    const documentId = parseInt(stmtBtn.dataset.documentId, 10);
                    const filename = stmtBtn.dataset.filename || '';
                    if (documentId && typeof TWR !== 'undefined' && TWR.StatementHistory) {
                        // Close history modal
                        if (typeof window.hideModal === 'function') {
                            window.hideModal('modal-scan-history');
                        } else {
                            const modal = document.getElementById('modal-scan-history');
                            if (modal) modal.classList.remove('active');
                        }
                        TWR.StatementHistory.open(documentId, scanId, filename);
                    } else if (!TWR?.StatementHistory) {
                        console.warn('[TWR] StatementHistory module not available');
                        if (typeof showToast === 'function') showToast('error', 'Statement History module not loaded');
                    }
                    return;
                }

                // Compare scan button (v3.0.110)
                const compareBtn = e.target.closest('[data-action="compare-scan"]');
                if (compareBtn) {
                    const documentId = parseInt(compareBtn.dataset.documentId, 10);
                    const scanId = parseInt(compareBtn.dataset.scanId, 10);
                    if (documentId && typeof DocCompare !== 'undefined') {
                        // Close history modal
                        if (typeof window.hideModal === 'function') {
                            window.hideModal('modal-scan-history');
                        } else {
                            const modal = document.getElementById('modal-scan-history');
                            if (modal) modal.classList.remove('active');
                        }
                        // Open comparison modal
                        DocCompare.open(documentId, null, scanId);
                    } else if (!documentId) {
                        console.warn('[TWR] No document ID for comparison');
                    } else {
                        console.warn('[TWR] DocCompare module not available');
                    }
                    return;
                }
            });
        }
        
        // Expose functions globally
        window.recallScan = recallScan;
        window.clearRecalledScanBanner = clearRecalledScanBanner;
        window.loadHistoryData = loadHistoryData;
        
        console.log('[TWR] History fixes applied successfully');
    }
    
    /**
     * Override the original renderScanHistory to add Load buttons
     */
    function overrideRenderFunction() {
        // Store original if it exists
        const originalRender = window.renderScanHistory;
        
        // Replace with our enhanced version
        window.renderScanHistory = function(history) {
            console.log('[TWR] Enhanced renderScanHistory called');
            renderHistoryTableEnhanced(history);
        };
        
        console.log('[TWR] renderScanHistory overridden');
    }
    
    /**
     * Load history data using the API
     */
    async function loadHistoryData() {
        try {
            let response;
            if (typeof window.api === 'function') {
                response = await window.api('/scan-history', 'GET');
            } else {
                const res = await fetch('/api/scan-history');
                response = await res.json();
            }
            
            if (response && response.success && response.data) {
                renderHistoryTableEnhanced(response.data);
                await loadStorageStats();
            } else {
                showEmptyState();
            }
        } catch (err) {
            console.error('[TWR] Failed to fetch history:', err);
            showEmptyState();
        }
    }
    
    /**
     * Load and display storage statistics
     */
    async function loadStorageStats() {
        try {
            let response;
            if (typeof window.api === 'function') {
                response = await window.api('/scan-history/stats', 'GET');
            } else {
                const res = await fetch('/api/scan-history/stats');
                response = await res.json();
            }
            
            if (response && response.success && response.data) {
                updateStatsDisplay(response.data);
            }
        } catch (err) {
            // Stats endpoint may not exist yet - that's okay
            console.log('[TWR] Stats endpoint not available (optional)');
        }
    }
    
    /**
     * Update the stats display in the modal
     */
    function updateStatsDisplay(stats) {
        let statsContainer = document.getElementById('history-stats-container');
        
        if (!statsContainer) {
            // Create stats container if it doesn't exist
            const modalBody = document.querySelector('#modal-scan-history .modal-body');
            if (modalBody) {
                statsContainer = document.createElement('div');
                statsContainer.id = 'history-stats-container';
                statsContainer.className = 'history-stats';
                modalBody.insertBefore(statsContainer, modalBody.firstChild);
            }
        }
        
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stats-bar">
                    <div class="stats-info">
                        <span><strong>${stats.document_count || 0}</strong> documents</span>
                        <span><strong>${stats.scan_count || 0}</strong> scans</span>
                        <span><strong>${stats.database_size_mb || '0.0'}</strong> MB used</span>
                    </div>
                    <div class="stats-actions">
                        <button class="btn btn-sm btn-ghost" id="btn-clear-old-history" title="Clear scans older than 30 days">
                            <i data-lucide="calendar-minus"></i> Clear Old
                        </button>
                        <button class="btn btn-sm btn-ghost btn-danger" id="btn-clear-all-history" title="Clear all scan history">
                            <i data-lucide="trash-2"></i> Clear All
                        </button>
                    </div>
                </div>
            `;
            
            // Add styles if not present
            addStatsStyles();
            
            // Refresh icons
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch(e) {}
            }
        }
    }
    
    /**
     * Add CSS styles for stats bar
     */
    function addStatsStyles() {
        if (document.getElementById('history-fixes-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'history-fixes-styles';
        styles.textContent = `
            .history-stats {
                margin-bottom: 16px;
                padding: 12px 16px;
                background: var(--bg-secondary, #f5f5f5);
                border-radius: var(--radius-md, 8px);
            }
            .stats-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }
            .stats-info {
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
            }
            .stats-info span {
                font-size: 13px;
                color: var(--text-muted, #666);
            }
            .stats-actions {
                display: flex;
                gap: 8px;
            }
            .btn-danger {
                color: var(--error, #dc2626) !important;
            }
            .btn-danger:hover {
                background: rgba(220, 38, 38, 0.1) !important;
            }
            .recalled-scan-banner {
                background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
                color: white;
                padding: 8px 16px;
                position: sticky;
                top: 0;
                z-index: 100;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            .recalled-scan-content {
                display: flex;
                align-items: center;
                gap: 8px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .recalled-scan-content .btn-ghost {
                color: white;
                margin-left: auto;
            }
            .recalled-scan-content .btn-ghost:hover {
                background: rgba(255,255,255,0.1);
            }
            .load-btn {
                color: var(--primary, #2563eb) !important;
            }
            .load-btn:hover {
                background: rgba(37, 99, 235, 0.1) !important;
            }
        `;
        document.head.appendChild(styles);
    }
    
    /**
     * Show empty state
     */
    function showEmptyState() {
        const emptyMsg = document.getElementById('scan-history-empty');
        const table = document.querySelector('.scan-history-table');
        if (emptyMsg) emptyMsg.style.display = 'block';
        if (table) table.style.display = 'none';
    }
    
    /**
     * Enhanced history table renderer with Load buttons
     */
    function renderHistoryTableEnhanced(history) {
        const tbody = document.getElementById('scan-history-body');
        const emptyMsg = document.getElementById('scan-history-empty');
        const table = document.querySelector('.scan-history-table');
        
        if (!history || history.length === 0) {
            showEmptyState();
            return;
        }
        
        if (emptyMsg) emptyMsg.style.display = 'none';
        if (table) table.style.display = 'block';
        
        if (!tbody) {
            console.error('[TWR] scan-history-body not found');
            return;
        }
        
        tbody.innerHTML = history.map(scan => {
            const scanDate = new Date(scan.scan_time);
            const dateStr = scanDate.toLocaleDateString() + ' ' + 
                           scanDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            let changeHtml = '<span class="change-indicator unchanged">First scan</span>';
            if (scan.issues_added > 0 || scan.issues_removed > 0) {
                changeHtml = `
                    <span class="change-indicator added">+${scan.issues_added}</span>
                    <span class="change-indicator removed">-${scan.issues_removed}</span>
                `;
            }
            
            const filename = escapeHtml(scan.filename || '');
            const scanId = scan.scan_id || scan.id;
            const docId = scan.document_id || 0;

            // Only show compare button if document has multiple scans
            const showCompare = docId > 0;

            const stmtCount = scan.statement_count || 0;
            const stmtBtn = stmtCount > 0 ? `
                            <button class="btn btn-ghost btn-sm stmt-history-btn"
                                    data-action="view-statements"
                                    data-scan-id="${scanId}"
                                    data-document-id="${docId}"
                                    data-filename="${filename}"
                                    title="View extracted statements (${stmtCount})">
                                <i data-lucide="file-text"></i>
                            </button>` : '';

            return `
                <tr data-scan-id="${scanId}" data-document-id="${docId}">
                    <td><strong>${filename}</strong></td>
                    <td>${dateStr}</td>
                    <td>${scan.issue_count}</td>
                    <td>${scan.score}</td>
                    <td><span class="grade-badge grade-${scan.grade}">${scan.grade}</span></td>
                    <td>${stmtCount > 0 ? `<span class="stmt-count-badge" data-action="view-statements" data-scan-id="${scanId}" data-document-id="${docId}" data-filename="${filename}" style="cursor:pointer;color:var(--accent-blue);font-weight:600;" title="Click to view statements">${stmtCount}</span>` : '0'}</td>
                    <td>${changeHtml}</td>
                    <td>
                        <div style="display: flex; gap: 4px;">
                            <button class="btn btn-ghost btn-sm load-btn"
                                    data-action="load-scan"
                                    data-scan-id="${scanId}"
                                    data-filename="${filename}"
                                    title="Load this scan's results">
                                <i data-lucide="upload"></i>
                            </button>
                            ${stmtBtn}
                            ${showCompare ? `
                            <button class="btn btn-ghost btn-sm compare-btn"
                                    data-action="compare-scan"
                                    data-scan-id="${scanId}"
                                    data-document-id="${docId}"
                                    data-filename="${filename}"
                                    title="Compare with other scans">
                                <i data-lucide="git-compare"></i>
                            </button>
                            ` : ''}
                            <button class="btn btn-ghost btn-sm btn-delete-scan"
                                    data-action="delete-scan"
                                    data-scan-id="${scanId}"
                                    data-filename="${filename}"
                                    title="Delete this scan">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
        
        // Add styles
        addStatsStyles();
    }
    
    /**
     * Clear all history
     */
    async function clearAllHistory() {
        if (!confirm('Are you sure you want to delete ALL scan history?\n\nThis cannot be undone.')) {
            return;
        }
        
        try {
            let response;
            if (typeof window.api === 'function') {
                response = await window.api('/scan-history/clear', 'POST', { clear_all: true });
            } else {
                const res = await fetch('/api/scan-history/clear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ clear_all: true })
                });
                response = await res.json();
            }
            
            if (response && response.success) {
                if (typeof window.toast === 'function') {
                    window.toast('success', `Cleared ${response.deleted || 'all'} scans`);
                }
                await loadHistoryData();
            } else {
                throw new Error(response?.error || 'Failed to clear history');
            }
        } catch (err) {
            console.error('[TWR] Error clearing history:', err);
            if (typeof window.toast === 'function') {
                window.toast('error', 'Clear feature not available. Delete scans individually or update to latest version.');
            } else {
                alert('Clear feature not available yet. Please delete scans individually using the trash icon.');
            }
        }
    }
    
    /**
     * Clear old history (older than 30 days)
     */
    async function clearOldHistory() {
        if (!confirm('Delete all scans older than 30 days?\n\nThis cannot be undone.')) {
            return;
        }
        
        try {
            let response;
            if (typeof window.api === 'function') {
                response = await window.api('/scan-history/clear', 'POST', { older_than_days: 30 });
            } else {
                const res = await fetch('/api/scan-history/clear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ older_than_days: 30 })
                });
                response = await res.json();
            }
            
            if (response && response.success) {
                if (typeof window.toast === 'function') {
                    window.toast('success', `Cleared ${response.deleted || 0} old scans`);
                }
                await loadHistoryData();
            } else {
                throw new Error(response?.error || 'Failed to clear old history');
            }
        } catch (err) {
            console.error('[TWR] Error clearing old history:', err);
            if (typeof window.toast === 'function') {
                window.toast('error', 'Clear feature not available. Delete scans individually or update to latest version.');
            } else {
                alert('Clear feature not available yet. Please delete scans individually using the trash icon.');
            }
        }
    }
    
    /**
     * Recall a scan from history
     */
    async function recallScan(scanId, filename) {
        console.log(`[TWR] Recalling scan ${scanId}: ${filename}`);
        
        // Show loading indicator
        if (typeof window.setLoading === 'function') {
            window.setLoading(true, 'Loading scan...');
        }
        
        try {
            let response;
            if (typeof window.api === 'function') {
                response = await window.api(`/scan-history/${scanId}/recall`, 'GET');
            } else {
                const res = await fetch(`/api/scan-history/${scanId}/recall`);
                response = await res.json();
            }
            
            if (response && response.success && response.data) {
                const scanData = response.data;
                
                // Close the history modal
                if (typeof window.hideModal === 'function') {
                    window.hideModal('modal-scan-history');
                } else {
                    const modal = document.getElementById('modal-scan-history');
                    if (modal) modal.classList.remove('show');
                }
                
                // Populate the UI with recalled results
                await populateRecalledScan(scanData);
                
                // Show success message
                if (typeof window.toast === 'function') {
                    window.toast('success', `Loaded scan from ${new Date(scanData.scan_time).toLocaleDateString()}`);
                }
                
            } else {
                const errorMsg = response?.error || 'Failed to recall scan';
                console.error('[TWR] Recall failed:', errorMsg);
                if (typeof window.toast === 'function') {
                    window.toast('error', errorMsg);
                } else {
                    alert(errorMsg);
                }
            }
        } catch (err) {
            console.error('[TWR] Error recalling scan:', err);
            if (typeof window.toast === 'function') {
                window.toast('error', 'Recall feature not available. Please ensure you have the latest backend update.');
            } else {
                alert('Recall feature not available. Please ensure you have applied the full v3.0.54 update including scan_recall.py.');
            }
        } finally {
            if (typeof window.setLoading === 'function') {
                window.setLoading(false);
            }
        }
    }
    
    /**
     * Populate the UI with recalled scan data
     */
    async function populateRecalledScan(scanData) {
        console.log('[TWR] Populating recalled scan:', scanData.filename);
        
        const results = scanData.results;
        if (!results) {
            console.error('[TWR] No results in scan data');
            return;
        }
        
        // Store recalled scan info
        isViewingRecalledScan = true;
        recalledScanInfo = {
            scanId: scanData.scan_id,
            filename: scanData.filename,
            scanTime: scanData.scan_time,
            documentId: scanData.document_id || 0
        };

        // v4.2.0: Set globals for Statement History sidebar button in Forge
        if (scanData.document_id) {
            window._sfCurrentDocumentId = scanData.document_id;
            window._sfCurrentScanId = scanData.scan_id;
        }
        
        // Get the global State object
        const State = window.State || window.TWR?.State?.State;
        if (!State) {
            console.error('[TWR] State object not found');
            renderIssuesFallback(results.issues);
            return;
        }
        
        // Populate State with recalled data (mimics processReviewResults)
        State.reviewResults = results;
        State.issues = results.issues || [];
        State.filteredIssues = [...State.issues];
        State.filename = scanData.filename;
        State.currentFilename = scanData.filename;
        if (State.selectedIssues && typeof State.selectedIssues.clear === 'function') {
            State.selectedIssues.clear();
        }
        
        // Handle roles if present
        if (results.roles) {
            State.roles = results.roles.roles || results.roles;
        } else {
            State.roles = {};
        }
        
        // Update filename display
        const filenameEl = document.getElementById('current-filename');
        if (filenameEl) {
            filenameEl.textContent = scanData.filename;
        }

        // v4.5.3: Update document title in header (doc-title is the actual visible element)
        if (typeof window.updateDocumentInfo === 'function') {
            const ext = scanData.filename?.split('.').pop()?.toLowerCase() || '';
            window.updateDocumentInfo({
                filename: scanData.filename,
                file_type: ext,
                word_count: results.word_count || 0,
                paragraph_count: results.paragraph_count || 0,
                table_count: results.table_count || 0,
                heading_count: results.heading_count || 0
            });
        }

        // Show the recalled scan banner
        showRecalledScanBanner(scanData);

        // Call the app's UI update functions
        if (typeof window.updateResultsUI === 'function') {
            window.updateResultsUI(results);
        }
        
        if (typeof window.updateSeverityCounts === 'function') {
            window.updateSeverityCounts(results.by_severity || {});
        }
        
        if (typeof window.updateCategoryFilters === 'function') {
            window.updateCategoryFilters(results.by_category || {});
        }
        
        // Render the issues list
        if (typeof window.renderIssuesList === 'function') {
            window.renderIssuesList();
        } else if (window.TWR?.Renderers?.renderIssuesList) {
            window.TWR.Renderers.renderIssuesList();
        } else {
            renderIssuesFallback(results.issues);
        }
        
        // Show the issues container
        const issuesContainer = document.getElementById('issues-container');
        if (issuesContainer) {
            issuesContainer.style.display = '';
        }

        // v4.0.2: Show stats bar and hide empty state when loading from history
        const statsBar = document.getElementById('stats-bar');
        const emptyState = document.getElementById('empty-state');
        if (statsBar) statsBar.style.display = 'flex';
        if (emptyState) emptyState.style.display = 'none';

        // Show analytics if available
        if (typeof window.showAnalyticsAccordion === 'function') {
            window.showAnalyticsAccordion(results);
        }
        
        // Enable export button
        const exportBtn = document.getElementById('btn-export');
        if (exportBtn) exportBtn.disabled = false;
        
        // Switch to review view
        const navReview = document.getElementById('nav-review');
        if (navReview) {
            navReview.click();
        }
        
        console.log(`[TWR] Recalled scan populated: ${State.issues.length} issues`);
    }
    
    /**
     * Show banner indicating we're viewing a historical scan
     */
    function showRecalledScanBanner(scanData) {
        clearRecalledScanBanner();
        
        const scanDate = new Date(scanData.scan_time);
        const dateStr = scanDate.toLocaleDateString() + ' ' + 
                       scanDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        const banner = document.createElement('div');
        banner.id = 'recalled-scan-banner';
        banner.className = 'recalled-scan-banner';
        banner.innerHTML = `
            <div class="recalled-scan-content">
                <i data-lucide="history" style="width:16px;height:16px;"></i>
                <span>Viewing historical scan from <strong>${dateStr}</strong></span>
                <button class="btn btn-sm btn-ghost" onclick="window.clearRecalledScanBanner()" title="Dismiss">
                    <i data-lucide="x" style="width:14px;height:14px;"></i>
                </button>
            </div>
        `;
        
        addStatsStyles(); // Includes banner styles
        
        const mainContent = document.querySelector('.main-content') || 
                           document.querySelector('.app-container') ||
                           document.body;
        mainContent.insertBefore(banner, mainContent.firstChild);
        
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }
    
    /**
     * Clear the recalled scan banner
     */
    function clearRecalledScanBanner() {
        const banner = document.getElementById('recalled-scan-banner');
        if (banner) {
            banner.remove();
        }
        isViewingRecalledScan = false;
        recalledScanInfo = null;
    }
    
    /**
     * Update summary statistics
     */
    function updateSummaryStats(results) {
        const issueCountEl = document.getElementById('issue-count');
        if (issueCountEl) {
            issueCountEl.textContent = results.issue_count || (results.issues?.length || 0);
        }
        
        const wordCountEl = document.getElementById('word-count');
        if (wordCountEl && results.word_count) {
            wordCountEl.textContent = results.word_count.toLocaleString();
        }
        
        const paraCountEl = document.getElementById('paragraph-count');
        if (paraCountEl && results.paragraph_count) {
            paraCountEl.textContent = results.paragraph_count;
        }
    }
    
    /**
     * Fallback issue renderer
     */
    function renderIssuesFallback(issues) {
        const container = document.getElementById('issues-container') || 
                         document.getElementById('issues-list');
        if (!container) {
            console.warn('[TWR] Issues container not found');
            return;
        }
        
        if (!issues || issues.length === 0) {
            container.innerHTML = '<div class="empty-state">No issues found</div>';
            return;
        }
        
        container.innerHTML = issues.map((issue, idx) => `
            <div class="issue-card" data-index="${idx}">
                <div class="issue-header">
                    <span class="issue-type">${escapeHtml(issue.check_type || issue.type || 'Issue')}</span>
                    <span class="issue-severity severity-${(issue.severity || 'info').toLowerCase()}">${issue.severity || 'Info'}</span>
                </div>
                <div class="issue-message">${escapeHtml(issue.message || '')}</div>
                ${issue.context ? `<div class="issue-context">${escapeHtml(issue.context)}</div>` : ''}
            </div>
        `).join('');
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"']/g, c => 
            ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
    }
    
    // Start initialization
    /**
     * Open Document Comparison from nav button (v3.0.112)
     * Shows a document selector if no document is loaded, or opens comparison for current doc
     */
    async function openCompareFromNav() {
        const currentFilename = window.State?.filename || window.State?.currentFilename;

        if (currentFilename) {
            // Document is loaded - open comparison for this document
            const modal = document.getElementById('modal-doc-compare');
            if (modal && typeof window.DocCompare?.open === 'function') {
                // Always look up the numeric document_id from scan history
                // (State.documentId is a string hash, not the database ID)
                try {
                    const response = await fetch(`/api/scan-history?filename=${encodeURIComponent(currentFilename)}&limit=1`);
                    const data = await response.json();
                    const scans = data.data || data.scans || [];
                    if (data.success && scans.length > 0) {
                        const docId = scans[0].document_id;
                        console.log('[TWR] Opening DocCompare with document_id:', docId, 'for filename:', currentFilename);
                        window.DocCompare.open(docId);
                    } else {
                        console.warn('[TWR] No scan history found for:', currentFilename);
                        showCompareDocumentPicker();
                    }
                } catch (err) {
                    console.error('[TWR] Error getting document ID:', err);
                    showCompareDocumentPicker();
                }
            } else {
                showCompareDocumentPicker();
            }
        } else {
            // No document loaded - show document picker
            showCompareDocumentPicker();
        }
    }

    /**
     * Show a picker to select which document to compare (v3.0.110)
     */
    async function showCompareDocumentPicker() {
        try {
            // Load documents with multiple scans
            const response = await fetch('/api/scan-history?limit=100');
            const data = await response.json();

            // API returns { success, data: [...] } where data is the array of scans
            const scans = data.data || data.scans || [];

            if (!data.success || !scans.length) {
                if (typeof window.toast === 'function') {
                    window.toast('info', 'No scan history available. Scan some documents first.');
                } else {
                    alert('No scan history available. Scan some documents first to enable comparison.');
                }
                return;
            }

            // Group by document and find those with 2+ scans
            const docScans = {};
            scans.forEach(scan => {
                const key = scan.document_id || scan.filename;
                if (!docScans[key]) {
                    docScans[key] = {
                        filename: scan.filename,
                        document_id: scan.document_id,
                        count: 0
                    };
                }
                docScans[key].count++;
            });

            const comparableDocs = Object.values(docScans).filter(d => d.count >= 2 && d.document_id);

            if (comparableDocs.length === 0) {
                if (typeof window.toast === 'function') {
                    window.toast('info', 'No documents with multiple scans found. Re-scan a document to enable comparison.');
                } else {
                    alert('No documents with multiple scans available for comparison. Re-scan a document to enable comparison.');
                }
                return;
            }

            // If only one document has multiple scans, open it directly
            if (comparableDocs.length === 1) {
                const doc = comparableDocs[0];
                if (typeof window.DocCompare?.open === 'function') {
                    window.DocCompare.open(doc.document_id);
                }
                return;
            }

            // Multiple documents - show picker dialog
            const pickerHtml = `
                <div class="compare-picker-overlay" id="compare-picker-overlay">
                    <div class="compare-picker-dialog">
                        <div class="compare-picker-header">
                            <h3><i data-lucide="git-compare"></i> Select Document to Compare</h3>
                            <button class="btn btn-ghost btn-icon" id="compare-picker-close">
                                <i data-lucide="x"></i>
                            </button>
                        </div>
                        <div class="compare-picker-body">
                            <p class="compare-picker-hint">Select a document with multiple scans to compare versions:</p>
                            <div class="compare-picker-list">
                                ${comparableDocs.map(doc => `
                                    <button class="compare-picker-item" data-document-id="${doc.document_id}" data-filename="${doc.filename}">
                                        <i data-lucide="file-text"></i>
                                        <span class="compare-picker-filename">${doc.filename}</span>
                                        <span class="compare-picker-count">${doc.count} scans</span>
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Add picker to DOM
            document.body.insertAdjacentHTML('beforeend', pickerHtml);

            // Initialize icons
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch(e) {}
            }

            const overlay = document.getElementById('compare-picker-overlay');

            // Close handler
            const closePickerHandler = () => {
                overlay?.remove();
            };

            document.getElementById('compare-picker-close')?.addEventListener('click', closePickerHandler);
            overlay?.addEventListener('click', (e) => {
                if (e.target === overlay) closePickerHandler();
            });

            // Document selection handler
            overlay?.querySelectorAll('.compare-picker-item').forEach(item => {
                item.addEventListener('click', () => {
                    const docId = parseInt(item.dataset.documentId, 10);
                    closePickerHandler();
                    if (typeof window.DocCompare?.open === 'function') {
                        window.DocCompare.open(docId);
                    }
                });
            });

        } catch (err) {
            console.error('[TWR] Error showing compare picker:', err);
            if (typeof window.toast === 'function') {
                window.toast('error', 'Failed to load documents for comparison');
            }
        }
    }

    /**
     * Show comparison prompt after re-scanning a document (v3.0.110)
     * Called from scan completion handler
     */
    function showComparePromptAfterScan(documentId, filename, scanCount) {
        if (scanCount < 2) return; // Need at least 2 scans to compare

        // Create a toast-like prompt
        const promptHtml = `
            <div class="compare-prompt" id="compare-prompt">
                <div class="compare-prompt-content">
                    <i data-lucide="git-compare"></i>
                    <div class="compare-prompt-text">
                        <strong>Compare versions?</strong>
                        <span>This document has ${scanCount} scans. Would you like to compare changes?</span>
                    </div>
                    <div class="compare-prompt-actions">
                        <button class="btn btn-primary btn-sm" id="compare-prompt-yes">Compare</button>
                        <button class="btn btn-ghost btn-sm" id="compare-prompt-no">Dismiss</button>
                    </div>
                </div>
            </div>
        `;

        // Remove any existing prompt
        document.getElementById('compare-prompt')?.remove();

        // Add prompt to DOM
        document.body.insertAdjacentHTML('beforeend', promptHtml);

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }

        const prompt = document.getElementById('compare-prompt');

        // Auto-dismiss after 15 seconds
        const autoDismiss = setTimeout(() => {
            prompt?.classList.add('compare-prompt-exit');
            setTimeout(() => prompt?.remove(), 300);
        }, 15000);

        // Yes handler
        document.getElementById('compare-prompt-yes')?.addEventListener('click', () => {
            clearTimeout(autoDismiss);
            prompt?.remove();
            if (typeof window.DocCompare?.open === 'function') {
                // DocCompare.open takes (docId, oldScanId?, newScanId?)
                // Pass only docId to open with latest two scans
                window.DocCompare.open(documentId);
            }
        });

        // No handler
        document.getElementById('compare-prompt-no')?.addEventListener('click', () => {
            clearTimeout(autoDismiss);
            prompt?.classList.add('compare-prompt-exit');
            setTimeout(() => prompt?.remove(), 300);
        });
    }

    // Expose functions globally for use by other modules
    window.showComparePromptAfterScan = showComparePromptAfterScan;
    window.openCompareFromNav = openCompareFromNav;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initHistoryFixes, 200);
        });
    } else {
        setTimeout(initHistoryFixes, 200);
    }

})();

console.log('[TWR] History fixes module loaded v3.0.111');
