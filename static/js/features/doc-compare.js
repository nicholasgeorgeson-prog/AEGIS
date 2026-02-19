/**
 * Document Comparison UI Module
 * ==============================
 * Main UI module for document comparison feature.
 * Renders side-by-side diff view with synchronized scrolling
 * and change navigation.
 *
 * @version 1.0.0
 * @requires DocCompareState
 */

window.DocCompare = (function() {
    'use strict';

    // =========================================================================
    // DOM REFERENCES
    // =========================================================================

    let modal = null;
    let oldScanSelect = null;
    let newScanSelect = null;
    let compareBtn = null;
    let closeBtn = null;
    let prevBtn = null;
    let nextBtn = null;
    let firstBtn = null;
    let lastBtn = null;
    let filterSelect = null;
    let oldPanel = null;
    let newPanel = null;
    let minimapEl = null;
    let issuesPanel = null;

    // Stat elements
    let changeCurrentEl = null;
    let changeTotalEl = null;
    let statAddedEl = null;
    let statDeletedEl = null;
    let statModifiedEl = null;
    let statMovedEl = null;

    // v4.6.1: View controls
    let changeIndexPanel = null;
    let changeIndexList = null;
    let changeIndexCount = null;
    let unifiedPanel = null;
    let unifiedContent = null;
    let viewMode = 'side-by-side'; // 'side-by-side' or 'unified'
    let changeIndexVisible = false;

    // Issue elements
    let scoreOldEl = null;
    let scoreNewEl = null;
    let scoreChangeEl = null;
    let issuesFixedEl = null;
    let issuesNewEl = null;

    // v5.8.1: Document selector
    let docSelect = null;
    let _allComparableDocs = [];

    // =========================================================================
    // UI STATE
    // =========================================================================

    let syncScrollEnabled = true;

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    /**
     * Initialize the module.
     */
    function init() {
        modal = document.getElementById('modal-doc-compare');
        if (!modal) {
            console.warn('[DocCompare] Modal not found, skipping initialization');
            return;
        }

        // Cache DOM elements
        cacheDOMElements();

        // Setup event listeners
        setupEventListeners();
        setupKeyboardShortcuts();

        // Subscribe to state changes
        DocCompareState.onChange(handleStateChange);
        DocCompareState.onNavigate(handleNavigate);
        DocCompareState.onLoad(handleLoad);
        DocCompareState.onError(handleError);

        console.log('[DocCompare] Module initialized');
    }

    /**
     * Cache DOM element references.
     */
    function cacheDOMElements() {
        oldScanSelect = document.getElementById('dc-old-scan');
        newScanSelect = document.getElementById('dc-new-scan');
        compareBtn = document.getElementById('dc-btn-compare');
        closeBtn = document.getElementById('dc-btn-close');
        prevBtn = document.getElementById('dc-btn-prev');
        nextBtn = document.getElementById('dc-btn-next');
        firstBtn = document.getElementById('dc-btn-first');
        lastBtn = document.getElementById('dc-btn-last');
        filterSelect = document.getElementById('dc-filter');
        oldPanel = document.getElementById('dc-content-old');
        newPanel = document.getElementById('dc-content-new');
        minimapEl = document.getElementById('dc-minimap');
        issuesPanel = document.getElementById('dc-issues-panel');

        // Stats
        changeCurrentEl = document.getElementById('dc-change-current');
        changeTotalEl = document.getElementById('dc-change-total');
        statAddedEl = document.getElementById('dc-stat-added');
        statDeletedEl = document.getElementById('dc-stat-deleted');
        statModifiedEl = document.getElementById('dc-stat-modified');
        statMovedEl = document.getElementById('dc-stat-moved');

        // v4.6.1: View controls
        changeIndexPanel = document.getElementById('dc-change-index');
        changeIndexList = document.getElementById('dc-ci-list');
        changeIndexCount = document.getElementById('dc-ci-count');
        unifiedPanel = document.getElementById('dc-unified-panel');
        unifiedContent = document.getElementById('dc-content-unified');

        // Issues
        scoreOldEl = document.getElementById('dc-score-old');
        scoreNewEl = document.getElementById('dc-score-new');
        scoreChangeEl = document.getElementById('dc-score-change');
        issuesFixedEl = document.getElementById('dc-issues-fixed');
        issuesNewEl = document.getElementById('dc-issues-new');

        // v5.8.1: Document selector
        docSelect = document.getElementById('dc-doc-select');
    }

    // =========================================================================
    // EVENT LISTENERS
    // =========================================================================

    /**
     * Setup DOM event listeners.
     */
    function setupEventListeners() {
        // Close button
        if (closeBtn) {
            closeBtn.addEventListener('click', close);
        }

        // Also close on modal backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                close();
            }
        });

        // Scan selection
        if (oldScanSelect) {
            oldScanSelect.addEventListener('change', () => {
                const scanId = parseInt(oldScanSelect.value, 10);
                if (scanId) {
                    DocCompareState.setOldScan(scanId);
                }
            });
        }

        if (newScanSelect) {
            newScanSelect.addEventListener('change', () => {
                const scanId = parseInt(newScanSelect.value, 10);
                if (scanId) {
                    DocCompareState.setNewScan(scanId);
                }
            });
        }

        // v5.8.1: Document selector — switch to a different document
        if (docSelect) {
            docSelect.addEventListener('change', async () => {
                const newDocId = parseInt(docSelect.value, 10);
                if (!newDocId) return;
                console.log('[DocCompare] Document changed to:', newDocId);

                // Reset diff panels
                if (oldPanel) oldPanel.innerHTML = '';
                if (newPanel) newPanel.innerHTML = '';
                if (unifiedContent) unifiedContent.innerHTML = '';
                resetStats();

                // Re-initialize state for new document
                DocCompareState.init(newDocId);

                try {
                    const scans = await DocCompareState.loadScans(newDocId);

                    if (scans.length >= 2) {
                        const previousScan = scans[1];
                        const latestScan = scans[0];

                        DocCompareState.setOldScan(previousScan.id);
                        DocCompareState.setNewScan(latestScan.id);

                        if (oldScanSelect) oldScanSelect.value = previousScan.id;
                        if (newScanSelect) newScanSelect.value = latestScan.id;

                        await loadComparison();
                    }
                } catch (error) {
                    showToast('Failed to load scans for selected document: ' + error.message, 'error');
                }
            });
        }

        // Compare button
        if (compareBtn) {
            compareBtn.addEventListener('click', loadComparison);
        }

        // Navigation
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                DocCompareState.goToPreviousChange();
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                DocCompareState.goToNextChange();
            });
        }

        if (firstBtn) {
            firstBtn.addEventListener('click', () => {
                DocCompareState.goToFirstChange();
            });
        }

        if (lastBtn) {
            lastBtn.addEventListener('click', () => {
                DocCompareState.goToLastChange();
            });
        }

        // Filter
        if (filterSelect) {
            filterSelect.addEventListener('change', handleFilterChange);
        }

        // Issues panel toggle
        const toggleIssuesBtn = document.getElementById('dc-btn-toggle-issues');
        if (toggleIssuesBtn) {
            toggleIssuesBtn.addEventListener('click', () => {
                DocCompareState.toggleIssuesPanel();
            });
        }

        // Synchronized scrolling
        if (oldPanel && newPanel) {
            setupSyncScroll();
        }

        // v4.6.1: View mode controls
        const sideBySideBtn = document.getElementById('dc-btn-side-by-side');
        const unifiedBtn = document.getElementById('dc-btn-unified');
        const changeIndexBtn = document.getElementById('dc-btn-change-index');
        const exportBtn = document.getElementById('dc-btn-export');

        if (sideBySideBtn) {
            sideBySideBtn.addEventListener('click', () => setViewMode('side-by-side'));
        }
        if (unifiedBtn) {
            unifiedBtn.addEventListener('click', () => setViewMode('unified'));
        }
        if (changeIndexBtn) {
            changeIndexBtn.addEventListener('click', toggleChangeIndex);
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', exportComparison);
        }
    }

    /**
     * Setup keyboard shortcuts.
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!modal || !modal.classList.contains('active')) return;

            // Don't trigger if typing in input
            const tag = e.target.tagName;
            if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
                if (e.key === 'Escape') {
                    close();
                }
                return;
            }

            switch (e.key.toLowerCase()) {
                case 'j':
                case 'arrowdown':
                    e.preventDefault();
                    DocCompareState.goToNextChange();
                    break;

                case 'k':
                case 'arrowup':
                    e.preventDefault();
                    DocCompareState.goToPreviousChange();
                    break;

                case 'home':
                    e.preventDefault();
                    DocCompareState.goToFirstChange();
                    break;

                case 'end':
                    e.preventDefault();
                    DocCompareState.goToLastChange();
                    break;

                case 'escape':
                    close();
                    break;

                case 'f':
                    e.preventDefault();
                    if (filterSelect) {
                        filterSelect.focus();
                    }
                    break;

                case 'i':
                    e.preventDefault();
                    DocCompareState.toggleIssuesPanel();
                    break;

                case 'c':
                    e.preventDefault();
                    toggleChangeIndex();
                    break;

                case 'u':
                    e.preventDefault();
                    setViewMode(viewMode === 'unified' ? 'side-by-side' : 'unified');
                    break;

                case 'e':
                    e.preventDefault();
                    exportComparison();
                    break;

                default:
                    // Number keys 1-9 for quick jump
                    if (e.key >= '1' && e.key <= '9') {
                        const idx = parseInt(e.key, 10) - 1;
                        DocCompareState.goToChange(idx);
                    }
            }
        });
    }

    // =========================================================================
    // SYNCHRONIZED SCROLLING
    // =========================================================================

    /**
     * Setup synchronized scrolling between panels.
     * Uses a "scroll initiator" pattern to prevent feedback loops.
     */
    function setupSyncScroll() {
        let scrollInitiator = null;  // Track which panel started the scroll
        let scrollTimeout = null;

        function handleScroll(source, target, sourceName) {
            if (!syncScrollEnabled) return;

            // If another panel initiated the scroll, ignore this event
            if (scrollInitiator && scrollInitiator !== sourceName) {
                return;
            }

            // Mark this panel as the initiator
            scrollInitiator = sourceName;

            // Clear any pending timeout
            if (scrollTimeout) {
                clearTimeout(scrollTimeout);
            }

            // Sync the target panel to match source
            const sourceMax = source.scrollHeight - source.clientHeight;
            const scrollPercent = sourceMax > 0 ? source.scrollTop / sourceMax : 0;

            const targetMax = target.scrollHeight - target.clientHeight;
            const targetScrollTop = Math.round(scrollPercent * targetMax);

            // Only update if there's a meaningful difference
            if (Math.abs(target.scrollTop - targetScrollTop) > 1) {
                target.scrollTop = targetScrollTop;
            }

            // Update minimap viewport
            updateMinimapViewport(scrollPercent);

            // Reset initiator after scrolling stops (150ms debounce)
            scrollTimeout = setTimeout(() => {
                scrollInitiator = null;
            }, 150);
        }

        oldPanel.addEventListener('scroll', () => handleScroll(oldPanel, newPanel, 'old'), { passive: true });
        newPanel.addEventListener('scroll', () => handleScroll(newPanel, oldPanel, 'new'), { passive: true });
    }

    // =========================================================================
    // STATE HANDLERS
    // =========================================================================

    /**
     * Handle state change events.
     */
    function handleStateChange(event) {
        switch (event.type) {
            case 'loading':
                setLoadingState(event.isLoading);
                break;

            case 'issuesPanel':
                updateIssuesPanelState(event.collapsed);
                break;

            case 'filter':
                updateNavigationUI();
                break;
        }
    }

    /**
     * Handle navigation events.
     */
    function handleNavigate(event) {
        updateNavigationUI();
        scrollToChange(event.rowIndex);
        highlightCurrentChange(event.rowIndex);
    }

    /**
     * Handle load events.
     */
    function handleLoad(event) {
        switch (event.type) {
            case 'scans':
                populateScanSelectors(event.scans, event.document);
                break;

            case 'diff':
                renderDiff(event.diff);
                renderChangeIndex(event.diff);
                renderUnifiedView(event.diff);
                updateStatsUI(event.diff.stats);
                updateNavigationUI();
                break;

            case 'issues':
                renderIssueComparison(event.comparison);
                break;
        }
    }

    /**
     * Handle error events.
     */
    function handleError(event) {
        console.error('[DocCompare] Error:', event.type, event.error);
        showToast(event.error, 'error');
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    /**
     * Open the comparison modal.
     * @param {number} docId - Document ID
     * @param {number} [initialOldScanId] - Initial old scan ID
     * @param {number} [initialNewScanId] - Initial new scan ID
     */
    async function open(docId, initialOldScanId = null, initialNewScanId = null) {
        if (!modal) {
            console.error('[DocCompare] Modal not initialized');
            return;
        }

        // Validate docId - if not provided, use document picker
        if (!docId) {
            console.log('[DocCompare] No document ID provided, opening document picker');
            if (typeof window.openCompareFromNav === 'function') {
                window.openCompareFromNav();
            } else if (typeof showCompareDocumentPicker === 'function') {
                showCompareDocumentPicker();
            } else {
                showToast('No document selected for comparison. Please select a document first.', 'error');
            }
            return;
        }

        console.log('[DocCompare] Opening comparison for document:', docId);

        // Show modal
        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // v5.8.1: Populate master document selector (non-blocking)
        populateDocumentSelector(docId);

        // Initialize state
        DocCompareState.init(docId);

        try {
            // Load scans for document
            const scans = await DocCompareState.loadScans(docId);

            // Auto-select scans
            if (initialOldScanId && initialNewScanId) {
                DocCompareState.setOldScan(initialOldScanId);
                DocCompareState.setNewScan(initialNewScanId);

                // Update selectors
                if (oldScanSelect) oldScanSelect.value = initialOldScanId;
                if (newScanSelect) newScanSelect.value = initialNewScanId;

                // Auto-load comparison
                await loadComparison();

            } else if (scans.length >= 2) {
                // v4.7.0-fix: Default to second-newest (left) vs newest (right), auto-compare
                const previousScan = scans[1];  // second most recent
                const latestScan = scans[0];    // most recent

                DocCompareState.setOldScan(previousScan.id);
                DocCompareState.setNewScan(latestScan.id);

                if (oldScanSelect) oldScanSelect.value = previousScan.id;
                if (newScanSelect) newScanSelect.value = latestScan.id;

                // Auto-load comparison immediately
                await loadComparison();
            }

        } catch (error) {
            showToast('Failed to load document scans: ' + error.message, 'error');
        }
    }

    /**
     * Close the comparison modal.
     */
    function close() {
        if (modal) {
            modal.classList.remove('active');
            document.body.classList.remove('modal-open');
        }

        // Clear panels
        if (oldPanel) oldPanel.innerHTML = '';
        if (newPanel) newPanel.innerHTML = '';
        if (minimapEl) minimapEl.innerHTML = '';
        if (unifiedContent) unifiedContent.innerHTML = '';
        if (changeIndexList) changeIndexList.innerHTML = '';

        // Reset view mode
        viewMode = 'side-by-side';
        changeIndexVisible = false;
        setViewMode('side-by-side');
        if (changeIndexPanel) changeIndexPanel.classList.add('collapsed');

        // Reset state
        DocCompareState.cleanup();

        // v4.6.1: Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage) {
            TWR.LandingPage.show();
        }
    }

    /**
     * Load and display comparison.
     * Guarded against concurrent calls and non-retryable validation errors.
     */
    let _comparisonInFlight = false;
    async function loadComparison() {
        // v4.7.0-fix: Prevent concurrent comparison requests
        if (_comparisonInFlight) {
            console.warn('[DocCompare] loadComparison already in flight — skipping duplicate call');
            return;
        }

        console.log('[DocCompare] loadComparison called');

        // Check if scans are selected
        const { oldScanId, newScanId } = DocCompareState.getSelectedScans();
        console.log('[DocCompare] Selected scans:', { oldScanId, newScanId });

        if (!oldScanId || !newScanId) {
            showToast('Please select both an old and new scan to compare', 'error');
            return;
        }

        _comparisonInFlight = true;
        try {
            setLoadingState(true);

            // Load diff
            console.log('[DocCompare] Loading diff...');
            await DocCompareState.loadDiff();
            console.log('[DocCompare] Diff loaded successfully');

            // Load issue comparison
            console.log('[DocCompare] Loading issue comparison...');
            await DocCompareState.loadIssueComparison();
            console.log('[DocCompare] Issue comparison loaded successfully');

            // Navigate to first change
            const changeCount = DocCompareState.getFilteredChangeCount();
            console.log('[DocCompare] Change count:', changeCount);
            if (changeCount > 0) {
                DocCompareState.goToChange(0);
            }

        } catch (error) {
            console.error('[DocCompare] loadComparison error:', error);
            // v4.7.0-fix: Show user-friendly message for validation errors (missing text)
            const msg = error.message || '';
            if (msg.includes('does not contain document text')) {
                showToast('One or both scans are missing document text. Re-scan the document to enable comparison.', 'error');
            } else {
                showToast('Failed to load comparison: ' + msg, 'error');
            }
        } finally {
            _comparisonInFlight = false;
            setLoadingState(false);
        }
    }

    // =========================================================================
    // RENDERING
    // =========================================================================

    /**
     * v5.8.1: Reset stats display.
     */
    function resetStats() {
        if (statAddedEl) statAddedEl.textContent = '0';
        if (statDeletedEl) statDeletedEl.textContent = '0';
        if (statModifiedEl) statModifiedEl.textContent = '0';
        if (statMovedEl) statMovedEl.textContent = '0';
        if (changeCurrentEl) changeCurrentEl.textContent = '0';
        if (changeTotalEl) changeTotalEl.textContent = '0';
    }

    /**
     * v5.8.1: Populate the master document selector dropdown.
     * @param {number} [selectedDocId] - Document ID to pre-select
     */
    async function populateDocumentSelector(selectedDocId) {
        if (!docSelect) return;

        try {
            const response = await fetch('/api/compare/documents');
            const data = await response.json();

            if (!data.success || !data.documents) {
                console.warn('[DocCompare] No comparable documents found');
                return;
            }

            _allComparableDocs = data.documents;

            // Rebuild options
            docSelect.innerHTML = '';

            _allComparableDocs.forEach(doc => {
                const opt = document.createElement('option');
                opt.value = doc.id;
                opt.textContent = `${doc.filename} (${doc.scan_count} scans)`;
                if (doc.id === selectedDocId) {
                    opt.selected = true;
                }
                docSelect.appendChild(opt);
            });

            console.log(`[DocCompare] Populated document selector with ${_allComparableDocs.length} documents, selected: ${selectedDocId}`);
        } catch (err) {
            console.error('[DocCompare] Failed to load comparable documents:', err);
        }
    }

    /**
     * Populate scan selector dropdowns.
     */
    function populateScanSelectors(scans, docInfo) {
        console.log('[DocCompare] populateScanSelectors called:', {
            scanCount: scans?.length || 0,
            docInfo: docInfo,
            hasOldSelect: !!oldScanSelect,
            hasNewSelect: !!newScanSelect
        });

        if (!oldScanSelect || !newScanSelect) {
            console.error('[DocCompare] Scan selectors not found in DOM');
            return;
        }

        // Clear existing options
        oldScanSelect.innerHTML = '<option value="">Select older scan...</option>';
        newScanSelect.innerHTML = '<option value="">Select newer scan...</option>';

        if (!scans || scans.length === 0) {
            console.warn('[DocCompare] No scans available for dropdown population');
            return;
        }

        // Add scan options
        scans.forEach((scan, index) => {
            const dateStr = formatDate(scan.scan_time);
            const label = `${dateStr} (Score: ${scan.score}, Issues: ${scan.issue_count})`;

            const opt1 = document.createElement('option');
            opt1.value = scan.id;
            opt1.textContent = label;
            oldScanSelect.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = scan.id;
            opt2.textContent = label;
            newScanSelect.appendChild(opt2);

            if (index === 0) {
                console.log('[DocCompare] First scan option:', { id: scan.id, label });
            }
        });

        console.log(`[DocCompare] Populated ${scans.length} scan options`);

        // v5.8.1: Update document selector to match current document
        if (docSelect && docInfo && docInfo.id) {
            docSelect.value = docInfo.id;
        }
    }

    /**
     * Render the diff in both panels.
     */
    function renderDiff(diff) {
        // v4.0.2: Re-fetch panel elements if not cached (fixes modal timing issue)
        if (!oldPanel) oldPanel = document.getElementById('dc-content-old');
        if (!newPanel) newPanel = document.getElementById('dc-content-new');

        if (!oldPanel || !newPanel || !diff) {
            console.warn('[DocCompare] renderDiff: Missing panels or diff', { oldPanel: !!oldPanel, newPanel: !!newPanel, diff: !!diff });
            return;
        }

        // Clear panels
        oldPanel.innerHTML = '';
        newPanel.innerHTML = '';

        // Render each row
        diff.rows.forEach((row, index) => {
            const oldRow = renderRow(row, 'old', index);
            const newRow = renderRow(row, 'new', index);

            oldPanel.appendChild(oldRow);
            newPanel.appendChild(newRow);
        });

        // Render minimap
        renderMinimap(diff);

        // Update panel headers
        updatePanelHeaders(diff);
    }

    /**
     * Render a single row for one panel.
     */
    function renderRow(row, side, index) {
        const div = document.createElement('div');
        // Map moved statuses to CSS class variants
        const cssStatus = row.status === 'moved_from' ? 'moved' :
                          row.status === 'moved_to' ? 'moved' : row.status;
        div.className = `dc-row dc-row-${cssStatus}`;
        if (row.status === 'moved_from') div.classList.add('dc-row-moved-from');
        if (row.status === 'moved_to') div.classList.add('dc-row-moved-to');
        div.dataset.rowIndex = index;
        div.dataset.status = row.status;

        if (side === 'old') {
            if (row.status === 'added' || row.status === 'moved_to') {
                // Placeholder on old side for added/moved-to content
                div.classList.add('dc-placeholder');
                div.innerHTML = '&nbsp;';
            } else if (row.status === 'moved_from') {
                div.innerHTML = `<span class="dc-move-indicator">↗ Moved</span> ${escapeHtml(row.old_line)}`;
            } else {
                // Use pre-rendered HTML from backend
                div.innerHTML = row.old_html || escapeHtml(row.old_line);
            }
        } else {
            if (row.status === 'deleted' || row.status === 'moved_from') {
                // Placeholder on new side for deleted/moved-from content
                div.classList.add('dc-placeholder');
                div.innerHTML = '&nbsp;';
            } else if (row.status === 'moved_to') {
                div.innerHTML = `<span class="dc-move-indicator">↙ Moved here</span> ${escapeHtml(row.new_line)}`;
            } else {
                div.innerHTML = row.new_html || escapeHtml(row.new_line);
            }
        }

        // Add click handler for navigation
        if (row.is_change) {
            div.style.cursor = 'pointer';
            div.addEventListener('click', () => {
                DocCompareState.goToRow(index);
            });
        }

        return div;
    }

    /**
     * Render the minimap.
     */
    function renderMinimap(diff) {
        if (!minimapEl || !diff) return;

        minimapEl.innerHTML = '';

        const totalRows = diff.rows.length;
        if (totalRows === 0) return;

        // Create markers for changes
        diff.rows.forEach((row, index) => {
            if (!row.is_change) return;

            const marker = document.createElement('div');
            marker.className = `dc-minimap-marker dc-marker-${row.status}`;
            marker.dataset.rowIndex = index;

            // Calculate position
            const topPercent = (index / totalRows) * 100;
            marker.style.top = `${topPercent}%`;

            // Click to navigate
            marker.addEventListener('click', () => {
                DocCompareState.goToRow(index);
            });

            // Tooltip
            marker.title = `${row.status}: Line ${index + 1}`;

            minimapEl.appendChild(marker);
        });

        // Create viewport indicator
        const viewport = document.createElement('div');
        viewport.className = 'dc-minimap-viewport';
        viewport.id = 'dc-minimap-viewport';
        minimapEl.appendChild(viewport);
    }

    /**
     * Update minimap viewport position.
     */
    function updateMinimapViewport(scrollPercent) {
        const viewport = document.getElementById('dc-minimap-viewport');
        if (!viewport || !minimapEl) return;

        const containerHeight = minimapEl.clientHeight;
        const viewportHeight = Math.max(20, containerHeight * 0.1);

        viewport.style.height = `${viewportHeight}px`;
        viewport.style.top = `${scrollPercent * (containerHeight - viewportHeight)}px`;
    }

    /**
     * Render issue comparison panel.
     */
    function renderIssueComparison(comparison) {
        if (!comparison) return;

        // Update scores
        if (scoreOldEl) scoreOldEl.textContent = comparison.old_score + '%';
        if (scoreNewEl) scoreNewEl.textContent = comparison.new_score + '%';

        // v4.0.2: Enhanced change display with descriptive label
        const changeLabelEl = document.getElementById('dc-score-change-label');

        if (scoreChangeEl) {
            const change = comparison.score_change;
            if (change > 0) {
                scoreChangeEl.textContent = `+${change}%`;
                scoreChangeEl.className = 'dc-score-change positive';
                if (changeLabelEl) changeLabelEl.textContent = 'Improved';
            } else if (change < 0) {
                scoreChangeEl.textContent = `${change}%`;
                scoreChangeEl.className = 'dc-score-change negative';
                if (changeLabelEl) changeLabelEl.textContent = 'Declined';
            } else {
                scoreChangeEl.textContent = '—';
                scoreChangeEl.className = 'dc-score-change neutral';
                if (changeLabelEl) changeLabelEl.textContent = 'No Change';
            }
        }

        // Update issue counts
        if (issuesFixedEl) issuesFixedEl.textContent = comparison.fixed_count;
        if (issuesNewEl) issuesNewEl.textContent = comparison.new_count;
    }

    /**
     * Update panel headers with scan dates.
     */
    function updatePanelHeaders(diff) {
        const oldLabel = document.getElementById('dc-old-label');
        const newLabel = document.getElementById('dc-new-label');

        if (oldLabel && diff.old_scan_time) {
            oldLabel.textContent = `Original (${formatDate(diff.old_scan_time)})`;
        }

        if (newLabel && diff.new_scan_time) {
            newLabel.textContent = `Current (${formatDate(diff.new_scan_time)})`;
        }
    }

    // =========================================================================
    // UI UPDATES
    // =========================================================================

    /**
     * Update statistics UI.
     */
    function updateStatsUI(stats) {
        if (!stats) return;

        if (statAddedEl) statAddedEl.textContent = stats.added;
        if (statDeletedEl) statDeletedEl.textContent = stats.deleted;
        if (statModifiedEl) statModifiedEl.textContent = stats.modified;
        if (statMovedEl) statMovedEl.textContent = stats.moved || 0;
    }

    /**
     * Update navigation UI.
     */
    function updateNavigationUI() {
        const current = DocCompareState.getCurrentChangeIndex() + 1;
        const total = DocCompareState.getFilteredChangeCount();

        if (changeCurrentEl) changeCurrentEl.textContent = total > 0 ? current : 0;
        if (changeTotalEl) changeTotalEl.textContent = total;

        // Update button states
        const atFirst = current <= 1;
        const atLast = current >= total;

        if (prevBtn) prevBtn.disabled = atFirst;
        if (nextBtn) nextBtn.disabled = atLast;
        if (firstBtn) firstBtn.disabled = atFirst;
        if (lastBtn) lastBtn.disabled = atLast;
    }

    /**
     * Set loading state.
     */
    function setLoadingState(loading) {
        if (compareBtn) {
            compareBtn.disabled = loading;
            compareBtn.textContent = loading ? 'Loading...' : 'Compare';
        }

        if (loading) {
            modal.classList.add('dc-loading');
        } else {
            modal.classList.remove('dc-loading');
        }
    }

    /**
     * Update issues panel collapsed state.
     */
    function updateIssuesPanelState(collapsed) {
        if (issuesPanel) {
            issuesPanel.classList.toggle('collapsed', collapsed);
        }

        const toggleBtn = document.getElementById('dc-btn-toggle-issues');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (icon) {
                icon.setAttribute('data-lucide', collapsed ? 'panel-right-open' : 'panel-right-close');
                // Re-render Lucide icons if available
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
    }

    /**
     * Scroll to a specific change row.
     */
    function scrollToChange(rowIndex) {
        if (rowIndex < 0) return;

        // Find rows in both panels
        const oldRow = oldPanel?.querySelector(`[data-row-index="${rowIndex}"]`);
        const newRow = newPanel?.querySelector(`[data-row-index="${rowIndex}"]`);

        if (oldRow) {
            oldRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else if (newRow) {
            newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Highlight the current change row.
     */
    function highlightCurrentChange(rowIndex) {
        // Remove existing highlights
        document.querySelectorAll('.dc-row-current').forEach(el => {
            el.classList.remove('dc-row-current');
        });

        // Add highlight to current row
        const oldRow = oldPanel?.querySelector(`[data-row-index="${rowIndex}"]`);
        const newRow = newPanel?.querySelector(`[data-row-index="${rowIndex}"]`);

        if (oldRow) oldRow.classList.add('dc-row-current');
        if (newRow) newRow.classList.add('dc-row-current');

        // Update minimap
        document.querySelectorAll('.dc-minimap-marker.dc-marker-active').forEach(el => {
            el.classList.remove('dc-marker-active');
        });

        const marker = minimapEl?.querySelector(`[data-row-index="${rowIndex}"]`);
        if (marker) {
            marker.classList.add('dc-marker-active');
        }
    }

    /**
     * Handle filter change.
     */
    function handleFilterChange() {
        const value = filterSelect.value;

        switch (value) {
            case 'all':
                DocCompareState.setFilters({
                    showAdded: true,
                    showDeleted: true,
                    showModified: true,
                    showMoved: true
                });
                break;
            case 'additions':
                DocCompareState.setFilters({
                    showAdded: true,
                    showDeleted: false,
                    showModified: false,
                    showMoved: false
                });
                break;
            case 'deletions':
                DocCompareState.setFilters({
                    showAdded: false,
                    showDeleted: true,
                    showModified: false,
                    showMoved: false
                });
                break;
            case 'modifications':
                DocCompareState.setFilters({
                    showAdded: false,
                    showDeleted: false,
                    showModified: true,
                    showMoved: false
                });
                break;
            case 'moves':
                DocCompareState.setFilters({
                    showAdded: false,
                    showDeleted: false,
                    showModified: false,
                    showMoved: true
                });
                break;
        }
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

    /**
     * Escape HTML entities.
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format date string.
     */
    function formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    }

    /**
     * Show toast notification.
     */
    function showToast(message, type = 'info') {
        // Use existing TWR toast if available
        // Note: TWR.Modals.toast signature is (type, message) — reversed from this function
        if (typeof TWR !== 'undefined' && TWR.Modals && TWR.Modals.toast) {
            TWR.Modals.toast(type, message);
        } else if (typeof showToastNotification === 'function') {
            showToastNotification(type, message);
        } else {
            console.log(`[DocCompare] ${type}: ${message}`);
        }
    }

    // =========================================================================
    // VIEW MODE & CHANGE INDEX (v4.6.1)
    // =========================================================================

    /**
     * Switch between side-by-side and unified view modes.
     * @param {string} mode - 'side-by-side' or 'unified'
     */
    function setViewMode(mode) {
        viewMode = mode;

        const sideBySideBtn = document.getElementById('dc-btn-side-by-side');
        const unifiedBtn = document.getElementById('dc-btn-unified');
        const oldPanelEl = oldPanel?.closest('.dc-panel-old');
        const newPanelEl = newPanel?.closest('.dc-panel-new');

        if (mode === 'unified') {
            // Show unified panel, hide side-by-side panels
            if (unifiedPanel) unifiedPanel.style.display = '';
            if (oldPanelEl) oldPanelEl.style.display = 'none';
            if (newPanelEl) newPanelEl.style.display = 'none';
            if (sideBySideBtn) sideBySideBtn.classList.remove('active');
            if (unifiedBtn) unifiedBtn.classList.add('active');
        } else {
            // Show side-by-side panels, hide unified
            if (unifiedPanel) unifiedPanel.style.display = 'none';
            if (oldPanelEl) oldPanelEl.style.display = '';
            if (newPanelEl) newPanelEl.style.display = '';
            if (sideBySideBtn) sideBySideBtn.classList.add('active');
            if (unifiedBtn) unifiedBtn.classList.remove('active');
        }
    }

    /**
     * Toggle the change index sidebar visibility.
     */
    function toggleChangeIndex() {
        changeIndexVisible = !changeIndexVisible;

        const changeIndexBtn = document.getElementById('dc-btn-change-index');
        if (changeIndexPanel) {
            changeIndexPanel.classList.toggle('collapsed', !changeIndexVisible);
        }
        if (changeIndexBtn) {
            changeIndexBtn.classList.toggle('active', changeIndexVisible);
        }
    }

    /**
     * Render the change index sidebar with clickable grouped entries.
     * @param {Object} diff - Diff result from backend
     */
    function renderChangeIndex(diff) {
        if (!changeIndexList || !diff) return;

        changeIndexList.innerHTML = '';

        // Use change_index from backend if available, else build from rows
        const entries = diff.change_index || [];

        if (entries.length > 0) {
            // Backend-provided change index (grouped by section)
            let currentSection = '';
            entries.forEach((entry, i) => {
                // Section header
                if (entry.section && entry.section !== currentSection) {
                    currentSection = entry.section;
                    const sectionEl = document.createElement('div');
                    sectionEl.className = 'dc-ci-section';
                    sectionEl.textContent = currentSection;
                    changeIndexList.appendChild(sectionEl);
                }

                const item = document.createElement('div');
                item.className = `dc-ci-item dc-ci-${entry.type || entry.status || 'modified'}`;
                item.dataset.rowIndex = entry.row_index;

                const icon = entry.type === 'added' || entry.status === 'added' ? '+' :
                             entry.type === 'deleted' || entry.status === 'deleted' ? '−' :
                             entry.type === 'moved' || entry.status === 'moved_from' || entry.status === 'moved_to' ? '↔' : '~';

                const preview = (entry.preview || entry.context || entry.text || '').substring(0, 60);
                item.innerHTML = `<span class="dc-ci-icon">${icon}</span>` +
                                 `<span class="dc-ci-text">${escapeHtml(preview)}</span>`;

                item.addEventListener('click', () => {
                    DocCompareState.goToRow(entry.row_index);
                });

                changeIndexList.appendChild(item);
            });
        } else {
            // Fallback: build from rows
            let currentSection = '';
            diff.rows.forEach((row, index) => {
                if (!row.is_change) return;

                // Section header
                if (row.section && row.section !== currentSection) {
                    currentSection = row.section;
                    const sectionEl = document.createElement('div');
                    sectionEl.className = 'dc-ci-section';
                    sectionEl.textContent = currentSection;
                    changeIndexList.appendChild(sectionEl);
                }

                const item = document.createElement('div');
                const cssType = row.status === 'moved_from' || row.status === 'moved_to' ? 'moved' : row.status;
                item.className = `dc-ci-item dc-ci-${cssType}`;
                item.dataset.rowIndex = index;

                const icon = row.status === 'added' ? '+' :
                             row.status === 'deleted' ? '−' :
                             row.status === 'moved_from' || row.status === 'moved_to' ? '↔' : '~';

                const text = row.new_line || row.old_line || '';
                const preview = text.substring(0, 60);
                item.innerHTML = `<span class="dc-ci-icon">${icon}</span>` +
                                 `<span class="dc-ci-text">${escapeHtml(preview)}</span>`;

                item.addEventListener('click', () => {
                    DocCompareState.goToRow(index);
                });

                changeIndexList.appendChild(item);
            });
        }

        // Update count
        const changeCount = diff.stats?.total_changes || diff.changes?.length || 0;
        if (changeIndexCount) changeIndexCount.textContent = changeCount;
    }

    /**
     * Render the unified/redline view showing all changes inline.
     * @param {Object} diff - Diff result from backend
     */
    function renderUnifiedView(diff) {
        if (!unifiedContent || !diff) return;

        unifiedContent.innerHTML = '';

        let currentSection = '';

        diff.rows.forEach((row, index) => {
            // Section divider
            if (row.section && row.section !== currentSection) {
                currentSection = row.section;
                const sectionDiv = document.createElement('div');
                sectionDiv.className = 'dc-unified-section';
                sectionDiv.textContent = currentSection;
                unifiedContent.appendChild(sectionDiv);
            }

            if (row.status === 'unchanged') {
                // Unchanged line — show as-is
                const line = document.createElement('div');
                line.className = 'dc-unified-line dc-unified-unchanged';
                line.dataset.rowIndex = index;
                line.textContent = row.old_line || row.new_line || '';
                unifiedContent.appendChild(line);
            } else if (row.status === 'added') {
                // Added line — green with + prefix
                const line = document.createElement('div');
                line.className = 'dc-unified-line dc-unified-added';
                line.dataset.rowIndex = index;
                line.innerHTML = `<span class="dc-unified-prefix">+</span>${escapeHtml(row.new_line)}`;
                line.style.cursor = 'pointer';
                line.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(line);
            } else if (row.status === 'deleted') {
                // Deleted line — red with - prefix, strikethrough
                const line = document.createElement('div');
                line.className = 'dc-unified-line dc-unified-deleted';
                line.dataset.rowIndex = index;
                line.innerHTML = `<span class="dc-unified-prefix">−</span>${escapeHtml(row.old_line)}`;
                line.style.cursor = 'pointer';
                line.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(line);
            } else if (row.status === 'modified') {
                // Modified — show old (red strikethrough) then new (green)
                const oldLine = document.createElement('div');
                oldLine.className = 'dc-unified-line dc-unified-deleted';
                oldLine.dataset.rowIndex = index;
                oldLine.innerHTML = `<span class="dc-unified-prefix">−</span>${row.old_html || escapeHtml(row.old_line)}`;
                oldLine.style.cursor = 'pointer';
                oldLine.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(oldLine);

                const newLine = document.createElement('div');
                newLine.className = 'dc-unified-line dc-unified-added';
                newLine.dataset.rowIndex = index;
                newLine.innerHTML = `<span class="dc-unified-prefix">+</span>${row.new_html || escapeHtml(row.new_line)}`;
                newLine.style.cursor = 'pointer';
                newLine.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(newLine);
            } else if (row.status === 'moved_from') {
                const line = document.createElement('div');
                line.className = 'dc-unified-line dc-unified-moved';
                line.dataset.rowIndex = index;
                line.innerHTML = `<span class="dc-unified-prefix">↗</span><span class="dc-move-label">Moved away:</span> ${escapeHtml(row.old_line)}`;
                line.style.cursor = 'pointer';
                line.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(line);
            } else if (row.status === 'moved_to') {
                const line = document.createElement('div');
                line.className = 'dc-unified-line dc-unified-moved';
                line.dataset.rowIndex = index;
                line.innerHTML = `<span class="dc-unified-prefix">↙</span><span class="dc-move-label">Moved here:</span> ${escapeHtml(row.new_line)}`;
                line.style.cursor = 'pointer';
                line.addEventListener('click', () => DocCompareState.goToRow(index));
                unifiedContent.appendChild(line);
            }
        });
    }

    /**
     * Export the comparison — shows format picker (CSV or HTML).
     */
    function exportComparison() {
        const diff = DocCompareState.getDiff();
        if (!diff || !diff.rows) {
            showToast('No comparison data to export', 'error');
            return;
        }

        // Show format picker dropdown near button
        const exportBtn = document.getElementById('dc-btn-export');
        let picker = document.getElementById('dc-export-picker');

        if (picker) {
            // Toggle visibility
            picker.style.display = picker.style.display === 'none' ? 'flex' : 'none';
            return;
        }

        // Create format picker
        picker = document.createElement('div');
        picker.id = 'dc-export-picker';
        picker.style.cssText = 'position:absolute;right:8px;top:100%;display:flex;flex-direction:column;gap:4px;padding:8px;background:var(--bg-surface,#1e1e2e);border:1px solid var(--border-color,#333);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.3);z-index:10000;min-width:160px;';
        picker.innerHTML = `
            <button class="dc-export-opt" data-format="csv" style="padding:8px 12px;border:none;border-radius:6px;background:transparent;color:var(--text-primary,#fff);cursor:pointer;text-align:left;font-size:13px;display:flex;align-items:center;gap:8px;transition:background 0.15s;">
                <i data-lucide="file-spreadsheet" style="width:16px;height:16px;"></i> Export CSV
            </button>
            <button class="dc-export-opt" data-format="html" style="padding:8px 12px;border:none;border-radius:6px;background:transparent;color:var(--text-primary,#fff);cursor:pointer;text-align:left;font-size:13px;display:flex;align-items:center;gap:8px;transition:background 0.15s;">
                <i data-lucide="file-code" style="width:16px;height:16px;"></i> Export HTML Report
            </button>
        `;

        // Position relative to export button
        if (exportBtn && exportBtn.parentElement) {
            exportBtn.parentElement.style.position = 'relative';
            exportBtn.parentElement.appendChild(picker);
        } else {
            document.body.appendChild(picker);
        }

        // Hover styles
        picker.querySelectorAll('.dc-export-opt').forEach(btn => {
            btn.addEventListener('mouseenter', () => btn.style.background = 'var(--bg-hover,rgba(255,255,255,0.1))');
            btn.addEventListener('mouseleave', () => btn.style.background = 'transparent');
        });

        // Click handlers
        picker.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-format]');
            if (!btn) return;
            const format = btn.dataset.format;
            picker.style.display = 'none';
            if (format === 'csv') exportComparisonCSV();
            else if (format === 'html') exportComparisonHTML();
        });

        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', function _closePicker(e) {
                if (!picker.contains(e.target) && e.target !== exportBtn) {
                    picker.style.display = 'none';
                    document.removeEventListener('click', _closePicker);
                }
            });
        }, 100);

        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ attrs: { class: '' } }); } catch(_) {}
        }
    }

    /**
     * Export comparison as CSV file.
     */
    function exportComparisonCSV() {
        const diff = DocCompareState.getDiff();
        if (!diff || !diff.rows) return;

        const stats = diff.stats || {};
        const docInfo = DocCompareState.getDocument();
        const filename = docInfo?.filename || 'document';
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

        const csvRows = [
            ['Row', 'Status', 'Section', 'Old Text', 'New Text'].join(',')
        ];

        diff.rows.forEach((row, i) => {
            if (row.status === 'unchanged') return;
            const escapeCsv = (s) => {
                if (!s) return '""';
                return '"' + s.replace(/"/g, '""') + '"';
            };
            csvRows.push([
                i + 1,
                row.status,
                escapeCsv(row.section || ''),
                escapeCsv(row.old_line || ''),
                escapeCsv(row.new_line || '')
            ].join(','));
        });

        const header = [
            `# Document Comparison Export`,
            `# File: ${filename}`,
            `# Old Scan: ${diff.old_scan_time || 'N/A'}`,
            `# New Scan: ${diff.new_scan_time || 'N/A'}`,
            `# Added: ${stats.added || 0}, Deleted: ${stats.deleted || 0}, Modified: ${stats.modified || 0}, Moved: ${stats.moved || 0}`,
            `# Exported: ${new Date().toLocaleString()}`,
            ``
        ].join('\n');

        downloadCSV(header + csvRows.join('\n'), `comparison_${filename}_${timestamp}.csv`);
        showToast(`Exported ${csvRows.length - 1} changes to CSV`, 'success');
    }

    /**
     * v5.9.26: Export comparison as standalone HTML report.
     */
    function exportComparisonHTML() {
        const diff = DocCompareState.getDiff();
        if (!diff || !diff.rows) return;

        const stats = diff.stats || {};
        const docInfo = DocCompareState.getDocument();
        const filename = docInfo?.filename || 'document';
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const exportDate = new Date().toLocaleString();

        const escHtml = (s) => {
            if (!s) return '';
            return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        };

        // Count changes
        let addedCount = 0, deletedCount = 0, modifiedCount = 0, unchangedCount = 0;
        diff.rows.forEach(r => {
            if (r.status === 'added') addedCount++;
            else if (r.status === 'deleted') deletedCount++;
            else if (r.status === 'modified') modifiedCount++;
            else unchangedCount++;
        });

        // Build table rows
        const tableRows = diff.rows.map((row, i) => {
            const statusClass = row.status || 'unchanged';
            const statusLabel = (row.status || 'unchanged').charAt(0).toUpperCase() + (row.status || 'unchanged').slice(1);
            const oldText = escHtml(row.old_line || '');
            const newText = escHtml(row.new_line || '');

            return `<tr class="row-${statusClass}">
                <td class="col-num">${i + 1}</td>
                <td class="col-status"><span class="badge badge-${statusClass}">${statusLabel}</span></td>
                <td class="col-old">${oldText}</td>
                <td class="col-new">${newText}</td>
            </tr>`;
        }).join('\n');

        const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AEGIS Document Comparison — ${escHtml(filename)}</title>
<style>
:root {
    --aegis-gold: #D6A84A;
    --aegis-bronze: #B8743A;
    --bg: #0d1117;
    --bg-card: #161b22;
    --bg-surface: #1e2530;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --border: #30363d;
    --added-bg: rgba(46,160,67,0.15);
    --added-text: #3fb950;
    --added-border: rgba(46,160,67,0.4);
    --deleted-bg: rgba(248,81,73,0.15);
    --deleted-text: #f85149;
    --deleted-border: rgba(248,81,73,0.4);
    --modified-bg: rgba(210,153,34,0.15);
    --modified-text: #d29922;
    --modified-border: rgba(210,153,34,0.4);
    --unchanged-bg: transparent;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }
.header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid var(--aegis-gold); }
.header h1 { font-size: 24px; font-weight: 600; }
.header .aegis-badge { background: linear-gradient(135deg, var(--aegis-gold), var(--aegis-bronze)); color: #000; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }
.meta-item { background: var(--bg-card); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border); }
.meta-label { font-size: 11px; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.5px; }
.meta-value { font-size: 14px; font-weight: 500; margin-top: 4px; }
.stats { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 20px; text-align: center; min-width: 100px; }
.stat-card.added { border-color: var(--added-border); }
.stat-card.deleted { border-color: var(--deleted-border); }
.stat-card.modified { border-color: var(--modified-border); }
.stat-num { font-size: 28px; font-weight: 700; }
.stat-card.added .stat-num { color: var(--added-text); }
.stat-card.deleted .stat-num { color: var(--deleted-text); }
.stat-card.modified .stat-num { color: var(--modified-text); }
.stat-label { font-size: 11px; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.5px; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 20px; background: transparent; color: var(--text-dim); cursor: pointer; font-size: 12px; transition: all 0.2s; }
.filter-btn:hover, .filter-btn.active { color: var(--text); border-color: var(--aegis-gold); background: rgba(214,168,74,0.1); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th { background: var(--bg-surface); padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.5px; border-bottom: 2px solid var(--border); position: sticky; top: 0; z-index: 1; }
td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; word-break: break-word; }
.col-num { width: 50px; text-align: center; color: var(--text-dim); }
.col-status { width: 90px; }
.col-old, .col-new { width: 42%; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.badge-added { background: var(--added-bg); color: var(--added-text); border: 1px solid var(--added-border); }
.badge-deleted { background: var(--deleted-bg); color: var(--deleted-text); border: 1px solid var(--deleted-border); }
.badge-modified { background: var(--modified-bg); color: var(--modified-text); border: 1px solid var(--modified-border); }
.badge-unchanged { background: transparent; color: var(--text-dim); border: 1px solid var(--border); }
.row-added { background: var(--added-bg); }
.row-deleted { background: var(--deleted-bg); }
.row-deleted .col-old { text-decoration: line-through; opacity: 0.8; }
.row-modified { background: var(--modified-bg); }
.row-unchanged { opacity: 0.6; }
.footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--text-dim); }

@media print {
    body { background: #fff; color: #000; }
    .container { max-width: 100%; padding: 12px; }
    .header { border-bottom-color: #000; }
    .header .aegis-badge { background: #D6A84A; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .meta-item, .stat-card { border-color: #ccc; background: #f9f9f9; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .stat-card.added .stat-num { color: #1a7f37; }
    .stat-card.deleted .stat-num { color: #cf222e; }
    .stat-card.modified .stat-num { color: #9a6700; }
    thead th { background: #f0f0f0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .row-added { background: #dafbe1; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .row-deleted { background: #ffebe9; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .row-modified { background: #fff8c5; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .badge-added { background: #dafbe1; color: #1a7f37; border-color: #1a7f37; }
    .badge-deleted { background: #ffebe9; color: #cf222e; border-color: #cf222e; }
    .badge-modified { background: #fff8c5; color: #9a6700; border-color: #9a6700; }
    .filter-bar, .filter-btn { display: none; }
}
</style>
<script>
function filterRows(status) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.status === status || status === 'all'));
    document.querySelectorAll('tbody tr').forEach(tr => {
        if (status === 'all') { tr.style.display = ''; return; }
        const isMatch = tr.classList.contains('row-' + status);
        tr.style.display = isMatch ? '' : 'none';
    });
}
</script>
</head>
<body>
<div class="container">
    <div class="header">
        <span class="aegis-badge">AEGIS</span>
        <h1>Document Comparison Report</h1>
    </div>

    <div class="meta">
        <div class="meta-item">
            <div class="meta-label">Document</div>
            <div class="meta-value">${escHtml(filename)}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Previous Scan</div>
            <div class="meta-value">${escHtml(diff.old_scan_time || 'N/A')}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Current Scan</div>
            <div class="meta-value">${escHtml(diff.new_scan_time || 'N/A')}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Exported</div>
            <div class="meta-value">${exportDate}</div>
        </div>
    </div>

    <div class="stats">
        <div class="stat-card added">
            <div class="stat-num">${addedCount}</div>
            <div class="stat-label">Added</div>
        </div>
        <div class="stat-card deleted">
            <div class="stat-num">${deletedCount}</div>
            <div class="stat-label">Deleted</div>
        </div>
        <div class="stat-card modified">
            <div class="stat-num">${modifiedCount}</div>
            <div class="stat-label">Modified</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">${unchangedCount}</div>
            <div class="stat-label">Unchanged</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">${diff.rows.length}</div>
            <div class="stat-label">Total Rows</div>
        </div>
    </div>

    <div class="filter-bar">
        <button class="filter-btn active" data-status="all" onclick="filterRows('all')">All</button>
        <button class="filter-btn" data-status="added" onclick="filterRows('added')">Added (${addedCount})</button>
        <button class="filter-btn" data-status="deleted" onclick="filterRows('deleted')">Deleted (${deletedCount})</button>
        <button class="filter-btn" data-status="modified" onclick="filterRows('modified')">Modified (${modifiedCount})</button>
        <button class="filter-btn" data-status="unchanged" onclick="filterRows('unchanged')">Unchanged (${unchangedCount})</button>
    </div>

    <table>
        <thead>
            <tr>
                <th class="col-num">#</th>
                <th class="col-status">Status</th>
                <th class="col-old">Previous Version</th>
                <th class="col-new">Current Version</th>
            </tr>
        </thead>
        <tbody>
            ${tableRows}
        </tbody>
    </table>

    <div class="footer">
        <span>Generated by AEGIS v${escHtml(window.AEGIS_VERSION || '5.9')}</span>
        <span>${escHtml(filename)} — ${exportDate}</span>
    </div>
</div>
</body>
</html>`;

        // Download HTML file
        const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comparison_${filename.replace(/[^a-zA-Z0-9_.-]/g, '_')}_${timestamp}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        const changeCount = addedCount + deletedCount + modifiedCount;
        showToast(`Exported ${changeCount} changes to HTML report`, 'success');
    }

    // =========================================================================
    // AUTO-INITIALIZATION
    // =========================================================================

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // =========================================================================
    // PUBLIC INTERFACE
    // =========================================================================

    return {
        init,
        open,
        close
    };
})();

// Log module load
console.log('[DocCompare] Module loaded');
