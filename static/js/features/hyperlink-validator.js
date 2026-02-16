/**
 * Hyperlink Validator UI Module
 * =============================
 * UI module for the standalone hyperlink validator feature.
 * Handles modal rendering, user interactions, and result display.
 *
 * @version 1.0.0
 */

window.HyperlinkValidator = (function() {
    'use strict';

    // ==========================================================================
    // STATE
    // ==========================================================================

    let initialized = false;
    let isOpen = false;

    // DOM element cache
    const el = {
        modal: null,
        closeBtn: null,
        urlInput: null,
        urlCount: null,
        modeSelect: null,
        scanDepthSelect: null,
        validateBtn: null,
        clearBtn: null,
        progressSection: null,
        progressFill: null,
        progressText: null,
        progressStats: null,
        progressEta: null,
        cancelBtn: null,
        resultsSection: null,
        summarySection: null,
        resultsBody: null,
        filterStatus: null,
        filterSearch: null,
        exportCsv: null,
        exportJson: null,
        exportHtml: null,
        exportHighlighted: null, // v3.0.110: Export with broken links highlighted
        historyList: null,
        settingsToggle: null,
        settingsContent: null,
        tabPaste: null,
        tabUpload: null,
        tabContentPaste: null,
        tabContentUpload: null,
        dropzone: null,
        fileInput: null,
        // Exclusions
        exclusionsList: null,
        exclusionPattern: null,
        exclusionMatchType: null,
        exclusionReason: null,
        exclusionTreatAsValid: null,
        addExclusionBtn: null,
        // Extended metrics
        extendedMetrics: null,
        sslWarningsCount: null,
        soft404Count: null,
        suspiciousCount: null,
        avgResponseTime: null,
        minResponseTime: null,
        maxResponseTime: null
    };

    // v3.0.110: Track the source file for highlighted export
    let sourceFile = null;
    let sourceFileType = null; // 'docx' or 'excel'
    let sourceFileBuffer = null; // ArrayBuffer backup of the file
    let sourceFileName = null;   // Original filename

    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================

    async function init() {
        if (initialized) return true;

        console.log('[TWR HyperlinkValidator] Initializing...');

        // Cache DOM elements
        cacheElements();

        if (!el.modal) {
            console.error('[TWR HyperlinkValidator] Modal element not found');
            return false;
        }

        // Initialize state module
        const stateReady = await HyperlinkValidatorState.init();
        if (!stateReady) {
            console.warn('[TWR HyperlinkValidator] State initialization failed, some features may be limited');
        }

        // Bind events
        bindEvents();

        // Subscribe to state changes
        HyperlinkValidatorState.onChange(handleStateChange);
        HyperlinkValidatorState.onProgress(handleProgress);
        HyperlinkValidatorState.onComplete(handleComplete);
        HyperlinkValidatorState.onError(handleError);

        // v4.3.0: Initialize smart search autocomplete
        initHvSmartSearch();

        initialized = true;
        console.log('[TWR HyperlinkValidator] Initialized');

        return true;
    }

    /**
     * v4.3.0: Initialize SmartSearch autocomplete for hyperlink validator search
     */
    function initHvSmartSearch() {
        // Check if SmartSearch is available from roles module
        if (!window.TWR?.Roles?.SmartSearch) {
            console.log('[TWR HyperlinkValidator] SmartSearch not available, skipping autocomplete');
            return;
        }

        const SmartSearch = window.TWR.Roles.SmartSearch;

        SmartSearch.init('hv-filter-search', {
            itemType: 'link',
            getItems: () => {
                const results = HyperlinkValidatorState?.getResults?.() || [];
                // Get unique URLs and domains
                const uniqueUrls = new Map();
                const domains = new Map();

                results.forEach(r => {
                    const url = r.url || r.link || '';
                    if (url && !uniqueUrls.has(url)) {
                        uniqueUrls.set(url, {
                            label: url,
                            type: 'link',
                            meta: r.status || r.result || 'unknown',
                            status: r.status || r.result
                        });
                    }

                    // Extract domain
                    try {
                        const domain = new URL(url).hostname;
                        if (domain && !domains.has(domain)) {
                            const domainResults = results.filter(res => {
                                try { return new URL(res.url || res.link || '').hostname === domain; }
                                catch { return false; }
                            });
                            domains.set(domain, {
                                label: domain,
                                type: 'link',
                                meta: `${domainResults.length} links`,
                                badge: domainResults.length
                            });
                        }
                    } catch (e) {}
                });

                // Return domains first, then individual URLs (limited)
                return [
                    ...Array.from(domains.values()),
                    ...Array.from(uniqueUrls.values()).slice(0, 20)
                ];
            },
            onSelect: (item, input) => {
                HyperlinkValidatorState.setFilter('search', item.label);
                renderResults(HyperlinkValidatorState.getFilteredResults());
            },
            maxResults: 12
        });
    }

    function cacheElements() {
        el.modal = document.getElementById('modal-hyperlink-validator');
        el.closeBtn = document.getElementById('hv-btn-close');
        el.urlInput = document.getElementById('hv-url-input');
        el.urlCount = document.querySelector('.hv-url-count');
        el.modeSelect = document.getElementById('hv-mode');
        el.validateBtn = document.getElementById('hv-btn-validate');
        el.clearBtn = document.getElementById('hv-btn-clear');
        el.progressSection = document.getElementById('hv-progress');
        el.progressFill = document.getElementById('hv-progress-fill');
        el.progressText = document.getElementById('hv-progress-text');
        el.progressStats = document.getElementById('hv-progress-stats');
        el.progressEta = document.getElementById('hv-progress-eta');
        el.cancelBtn = document.getElementById('hv-btn-cancel');
        el.resultsSection = document.getElementById('hv-results');
        el.summarySection = document.getElementById('hv-summary');
        el.resultsBody = document.getElementById('hv-results-body');
        el.filterStatus = document.getElementById('hv-filter-status');
        el.filterDomain = document.getElementById('hv-filter-domain');
        el.filterSearch = document.getElementById('hv-filter-search');
        el.statsGrid = document.getElementById('hv-stats-grid');
        el.exportCsv = document.getElementById('hv-btn-export-csv');
        el.exportJson = document.getElementById('hv-btn-export-json');
        el.exportHtml = document.getElementById('hv-btn-export-html');
        el.exportHighlighted = document.getElementById('hv-btn-export-highlighted'); // v3.0.110
        el.historyList = document.getElementById('hv-history-list');
        el.historyPanel = document.getElementById('hv-history-panel');
        el.historyToggle = document.getElementById('hv-btn-toggle-history');
        el.settingsToggle = document.getElementById('hv-settings-toggle');
        el.settingsContent = document.querySelector('.hv-settings-content');
        el.tabPaste = document.querySelector('[data-tab="paste"]');
        el.tabUpload = document.querySelector('[data-tab="upload"]');
        el.tabContentPaste = document.getElementById('hv-tab-paste');
        el.tabContentUpload = document.getElementById('hv-tab-upload');
        el.dropzone = document.getElementById('hv-dropzone');
        el.fileInput = document.getElementById('hv-file-input');

        // Scan depth
        el.scanDepthSelect = document.getElementById('hv-scan-depth');

        // Exclusions
        el.exclusionsList = document.getElementById('hv-exclusions-list');
        el.exclusionPattern = document.getElementById('hv-exclusion-pattern');
        el.exclusionMatchType = document.getElementById('hv-exclusion-type');
        el.exclusionReason = document.getElementById('hv-exclusion-reason');
        el.exclusionTreatAsValid = document.getElementById('hv-exclusion-valid');
        el.addExclusionBtn = document.getElementById('hv-btn-add-exclusion');
        el.exclusionForm = document.getElementById('hv-exclusion-form');

        // v4.6.1: Link History button
        el.linkHistoryBtn = document.getElementById('hv-btn-link-history');

        // Extended metrics
        el.extendedMetrics = document.getElementById('hv-extended-metrics');
        el.sslWarningsCount = document.getElementById('hv-count-ssl-warnings');
        el.soft404Count = document.getElementById('hv-count-soft-404');
        el.suspiciousCount = document.getElementById('hv-count-suspicious');
        el.avgResponseTime = document.getElementById('hv-avg-response');
        el.minResponseTime = document.getElementById('hv-min-response');
        el.maxResponseTime = document.getElementById('hv-max-response');
    }

    function bindEvents() {
        // Close button
        el.closeBtn?.addEventListener('click', close);

        // URL input
        el.urlInput?.addEventListener('input', handleUrlInputChange);

        // Validate button
        el.validateBtn?.addEventListener('click', handleValidate);

        // Clear button
        el.clearBtn?.addEventListener('click', handleClear);

        // Cancel button
        el.cancelBtn?.addEventListener('click', handleCancel);

        // Filter events
        el.filterStatus?.addEventListener('change', handleFilterChange);
        el.filterDomain?.addEventListener('change', handleDomainFilterChange);
        el.filterSearch?.addEventListener('input', debounce(handleSearchChange, 300));

        // v4.6.2: Stat card click-to-filter
        el.statsGrid?.addEventListener('click', handleStatCardClick);

        // Export buttons
        el.exportCsv?.addEventListener('click', () => handleExport('csv'));
        el.exportJson?.addEventListener('click', () => handleExport('json'));
        el.exportHtml?.addEventListener('click', () => handleExport('html'));
        el.exportHighlighted?.addEventListener('click', handleExportHighlighted); // v3.0.110

        // Settings toggle
        el.settingsToggle?.addEventListener('click', toggleSettings);

        // Tab switching
        el.tabPaste?.addEventListener('click', () => switchTab('paste'));
        el.tabUpload?.addEventListener('click', () => switchTab('upload'));

        // File upload
        el.dropzone?.addEventListener('click', () => el.fileInput?.click());
        el.fileInput?.addEventListener('change', handleFileSelect);
        el.dropzone?.addEventListener('dragover', handleDragOver);
        el.dropzone?.addEventListener('drop', handleFileDrop);

        // Table header sorting
        document.querySelectorAll('.hv-table th[data-sort]').forEach(th => {
            th.addEventListener('click', () => handleSort(th.dataset.sort));
        });

        // Modal close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                close();
            }
        });

        // Modal close on backdrop click
        el.modal?.addEventListener('click', (e) => {
            if (e.target === el.modal) {
                close();
            }
        });

        // Exclusions
        el.addExclusionBtn?.addEventListener('click', showExclusionForm);
        document.getElementById('hv-btn-save-exclusion')?.addEventListener('click', handleSaveExclusion);
        document.getElementById('hv-btn-cancel-exclusion')?.addEventListener('click', hideExclusionForm);
        el.exclusionsList?.addEventListener('click', handleExclusionAction);

        // v4.6.1: Link History button — opens Link History modal
        el.linkHistoryBtn?.addEventListener('click', () => {
            if (window.LinkHistory && typeof window.LinkHistory.open === 'function') {
                window.LinkHistory.open();
            } else {
                if (typeof showToast === 'function') showToast('error', 'Link History module not available');
            }
        });

        // v3.0.125: History panel toggle
        el.historyToggle?.addEventListener('click', toggleHistoryPanel);

        // v3.0.125: Show history button (when panel is closed)
        document.getElementById('hv-btn-show-history')?.addEventListener('click', showHistoryPanel);
    }

    // ==========================================================================
    // HISTORY PANEL TOGGLE (v3.0.125)
    // ==========================================================================

    function toggleHistoryPanel() {
        if (!el.historyPanel) return;

        const isOpen = el.historyPanel.classList.contains('open');

        if (isOpen) {
            el.historyPanel.classList.remove('open');
            // Update icon
            const icon = el.historyToggle?.querySelector('i, svg');
            if (icon) {
                icon.setAttribute('data-lucide', 'panel-right-open');
                lucide?.createIcons({ nodes: [icon] });
            }
        } else {
            showHistoryPanel();
        }
    }

    function showHistoryPanel() {
        if (!el.historyPanel) return;

        el.historyPanel.classList.add('open');
        // Update icon
        const icon = el.historyToggle?.querySelector('i, svg');
        if (icon) {
            icon.setAttribute('data-lucide', 'panel-right-close');
            lucide?.createIcons({ nodes: [icon] });
        }
    }

    // ==========================================================================
    // MODAL MANAGEMENT
    // ==========================================================================

    function open() {
        if (!initialized) {
            init().then(() => open());
            return;
        }

        console.log('[TWR HyperlinkValidator] Opening modal');

        el.modal?.classList.add('active');
        document.body.classList.add('modal-open');
        isOpen = true;

        // Focus URL input
        setTimeout(() => el.urlInput?.focus(), 100);

        // Refresh history
        HyperlinkValidatorState.loadHistory();

        // Update capabilities display
        updateCapabilitiesDisplay();
    }

    function close() {
        console.log('[TWR HyperlinkValidator] Closing modal');

        el.modal?.classList.remove('active');
        document.body.classList.remove('modal-open');
        isOpen = false;

        // v4.6.1: Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage) {
            TWR.LandingPage.show();
        }
    }

    // ==========================================================================
    // EVENT HANDLERS
    // ==========================================================================

    function handleUrlInputChange() {
        const urls = parseUrls(el.urlInput.value);
        if (el.urlCount) {
            el.urlCount.textContent = `${urls.length} URL${urls.length !== 1 ? 's' : ''} detected`;
        }
    }

    async function handleValidate() {
        const urls = parseUrls(el.urlInput.value);

        if (urls.length === 0) {
            showToast('error', 'Please enter at least one URL');
            return;
        }

        const mode = el.modeSelect?.value || 'validator';
        const options = getValidationOptions();

        // Show progress section
        showProgress();

        // v4.6.2: Show cinematic progress for larger URL sets (10+ URLs)
        if (typeof HVCinematicProgress !== 'undefined' && urls.length >= 10) {
            HVCinematicProgress.show('Pasted URLs', urls.length, urls.length);
            HVCinematicProgress.setPhaseValidating(urls.length, urls.length);
        }

        try {
            await HyperlinkValidatorState.startValidation(urls, mode, options);
        } catch (e) {
            showToast('error', `Validation failed: ${e.message}`);
            hideProgress();
            if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
                HVCinematicProgress.destroy();
            }
        }
    }

    function handleClear() {
        if (el.urlInput) {
            el.urlInput.value = '';
            handleUrlInputChange();
        }
        HyperlinkValidatorState.reset();
        hideProgress();
        hideResults();
    }

    async function handleCancel() {
        await HyperlinkValidatorState.cancelValidation();
        hideProgress();
        // v4.6.2: Destroy cinematic progress on cancel
        if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
            HVCinematicProgress.destroy();
        }
        showToast('info', 'Validation cancelled');
    }

    function handleFilterChange() {
        const value = el.filterStatus?.value || 'all';
        HyperlinkValidatorState.setFilter('status', value);
        renderResults(HyperlinkValidatorState.getFilteredResults());
    }

    function handleSearchChange() {
        const value = el.filterSearch?.value || '';
        HyperlinkValidatorState.setFilter('search', value);
        renderResults(HyperlinkValidatorState.getFilteredResults());
    }

    /**
     * v4.6.2: Handle domain filter dropdown change.
     */
    function handleDomainFilterChange() {
        const value = el.filterDomain?.value || 'all';
        HyperlinkValidatorState.setFilter('domain', value);
        renderResults(HyperlinkValidatorState.getFilteredResults());
    }

    /**
     * v4.6.2: Handle stat card click to filter results by that status.
     * Click toggles filter (click active filter to clear it).
     */
    function handleStatCardClick(e) {
        const card = e.target.closest('.hv-stat-card[data-filter]');
        if (!card) return;

        const filterValue = card.dataset.filter;
        const currentValue = el.filterStatus?.value || 'all';

        // Toggle: if clicking the already-active filter, reset to 'all'
        const newValue = currentValue === filterValue ? 'all' : filterValue;

        if (el.filterStatus) {
            el.filterStatus.value = newValue;
        }

        // Update active card styling
        document.querySelectorAll('.hv-stat-card[data-filter]').forEach(c => {
            c.classList.toggle('hv-stat-active', c.dataset.filter === newValue);
        });

        HyperlinkValidatorState.setFilter('status', newValue);
        renderResults(HyperlinkValidatorState.getFilteredResults());
    }

    /**
     * v4.6.2: Populate the domain filter dropdown from current results.
     */
    function populateDomainFilter(results) {
        if (!el.filterDomain) return;

        // Extract unique domains sorted by count
        const domainCounts = {};
        for (const r of results) {
            try {
                const domain = new URL(r.url).hostname.toLowerCase();
                domainCounts[domain] = (domainCounts[domain] || 0) + 1;
            } catch {
                // skip non-URL entries (mailto, etc.)
            }
        }

        const sortedDomains = Object.entries(domainCounts)
            .sort((a, b) => b[1] - a[1]);

        // Save current selection
        const currentDomain = el.filterDomain.value;

        // Rebuild options
        el.filterDomain.innerHTML = '<option value="all">All Domains (' + sortedDomains.length + ')</option>';
        for (const [domain, count] of sortedDomains) {
            const opt = document.createElement('option');
            opt.value = domain;
            opt.textContent = `${domain} (${count})`;
            el.filterDomain.appendChild(opt);
        }

        // Restore selection if still valid
        if (currentDomain && currentDomain !== 'all') {
            const exists = sortedDomains.some(([d]) => d === currentDomain);
            el.filterDomain.value = exists ? currentDomain : 'all';
        }
    }

    function handleSort(column) {
        const current = HyperlinkValidatorState.getFilters();
        // Toggle direction if same column
        const newDir = current.sort?.column === column && current.sort?.direction === 'asc' ? 'desc' : 'asc';
        HyperlinkValidatorState.setSortColumn(column, newDir);
        renderResults(HyperlinkValidatorState.getFilteredResults());
    }

    function handleExport(format) {
        // First try server-side export (for job-based results)
        const url = HyperlinkValidatorState.getExportUrl(format);
        if (url) {
            window.location.href = url;
            return;
        }

        // Fall back to client-side export (for Excel/DOCX results)
        const exportData = HyperlinkValidatorState.exportLocalResults(format);
        if (exportData) {
            const { blob, filename } = exportData;
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);
            showToast('success', `Exported to ${filename}`);
        } else {
            showToast('error', 'No results to export');
        }
    }

    function handleFileSelect(e) {
        const file = e.target.files?.[0];
        if (file) {
            loadUrlsFromFile(file);
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        el.dropzone?.classList.add('dragover');
    }

    function handleFileDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        el.dropzone?.classList.remove('dragover');

        const file = e.dataTransfer?.files?.[0];
        if (file) {
            loadUrlsFromFile(file);
        }
    }

    async function loadUrlsFromFile(file) {
        const filename = file.name.toLowerCase();

        // Check if it's a DOCX file - handle differently
        if (filename.endsWith('.docx')) {
            await handleDocxFile(file);
            return;
        }

        // Check if it's an Excel file - handle differently
        if (filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
            await handleExcelFile(file);
            return;
        }

        const text = await file.text();
        const urls = parseUrls(text);

        if (el.urlInput) {
            el.urlInput.value = urls.join('\n');
            handleUrlInputChange();
        }

        // Switch to paste tab to show the URLs
        switchTab('paste');

        showToast('success', `Loaded ${urls.length} URLs from file`);
    }

    async function handleDocxFile(file) {
        showToast('info', 'Extracting links from DOCX file...');
        showProgress();

        // v3.0.110: Store the source file for highlighted export
        sourceFile = file;
        sourceFileType = 'docx';
        sourceFileName = file.name;
        // v4.6.2: Store ArrayBuffer backup in case File object becomes stale
        try {
            sourceFileBuffer = await file.arrayBuffer();
        } catch (e) {
            console.warn('[HyperlinkValidator] Could not read file buffer:', e);
            sourceFileBuffer = null;
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('validate_web_urls', 'true');
            formData.append('check_bookmarks', 'true');
            formData.append('check_cross_refs', 'true');

            // Get CSRF token
            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;

            const response = await fetch('/api/hyperlink-validator/validate-docx', {
                method: 'POST',
                body: formData,
                headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error?.message || 'Failed to process DOCX file');
            }

            // Display results
            hideProgress();
            showResults();

            // Render DOCX-specific summary
            renderDocxSummary(data);

            // Convert validation results to standard format for rendering
            const results = data.validation_results.map(vr => ({
                url: vr.link?.url || vr.validation.link,
                status: vr.validation.is_valid ? 'WORKING' : 'INVALID',
                message: vr.validation.message,
                link_type: vr.validation.link_type || vr.link?.link_type,
                display_text: vr.link?.display_text,
                location: vr.link?.location || '',
                warnings: vr.validation.warnings || []
            }));

            // Store results in state for export functionality
            HyperlinkValidatorState.setLocalResults(results, data.summary);

            renderDocxResults(results);

            // v3.0.110: Enable highlighted export if there are broken links
            updateHighlightedExportButton(results);
            populateDomainFilter(results);  // v4.6.2

            showToast('success', `Validated ${data.links.length} links from ${file.name}`);

        } catch (e) {
            hideProgress();
            showToast('error', `DOCX processing failed: ${e.message}`);
        }
    }

    async function handleExcelFile(file) {
        showToast('info', 'Extracting links from Excel file...');
        showProgress();
        showExcelExtractionProgress(file.name);

        // v4.6.2: Launch cinematic progress overlay
        if (typeof HVCinematicProgress !== 'undefined') {
            HVCinematicProgress.show(file.name, 0, 0);
        }

        // v3.0.110: Store the source file for highlighted export
        sourceFile = file;
        sourceFileType = 'excel';
        sourceFileName = file.name;
        // v4.6.2: Store ArrayBuffer backup in case File object becomes stale
        try {
            sourceFileBuffer = await file.arrayBuffer();
        } catch (e) {
            console.warn('[HyperlinkValidator] Could not read file buffer:', e);
            sourceFileBuffer = null;
        }

        // Store extracted links for rendering after validation
        let extractedLinks = [];
        let extractionData = null;

        try {
            // Phase 1: Extract links only (fast, no HTTP validation)
            const formData = new FormData();
            formData.append('file', file);
            formData.append('extract_from_values', 'true');
            formData.append('extract_from_formulas', 'true');

            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;

            const extractResponse = await fetch('/api/hyperlink-validator/extract-excel', {
                method: 'POST',
                body: formData,
                headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
            });

            extractionData = await extractResponse.json();

            if (!extractionData.success) {
                throw new Error(extractionData.error?.message || 'Failed to extract links from Excel file');
            }

            extractedLinks = extractionData.links || [];
            const totalLinks = extractionData.total_links || 0;

            showToast('success', `Extracted ${totalLinks} links from ${file.name}`);

            // Collect unique web URLs for validation
            const webUrls = [];
            const seenUrls = new Set();
            for (const link of extractedLinks) {
                const url = link.url;
                if ((url.startsWith('http://') || url.startsWith('https://')) && !seenUrls.has(url)) {
                    seenUrls.add(url);
                    webUrls.push(url);
                }
            }

            if (webUrls.length === 0) {
                // No web URLs to validate -- show extraction results directly
                hideExcelExtractionProgress();
                hideProgress();
                showResults();
                _renderExcelExtractedResults(extractedLinks, extractionData, null);
                return;
            }

            // Update progress stats with extraction summary before starting validation
            if (el.progressStats) {
                el.progressStats.textContent = `Found ${totalLinks} links (${webUrls.length} unique web URLs to validate)`;
            }

            // Phase 2: Validate web URLs asynchronously using the job system
            showToast('info', `Validating ${webUrls.length} web URLs...`);
            hideExcelExtractionProgress();

            // v4.6.2: Transition cinematic progress to validation phase
            if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
                HVCinematicProgress.setPhaseValidating(totalLinks, webUrls.length);
            }

            // Use the existing async validation flow
            const mode = el.modeSelect?.value || 'validator';
            const options = getValidationOptions();

            // Store Excel extraction data for when validation completes
            _pendingExcelData = { extractedLinks, extractionData };

            // Start async validation -- the onComplete handler will merge results
            await HyperlinkValidatorState.startValidation(webUrls, mode, options);

        } catch (e) {
            console.error('[HyperlinkValidator] Excel processing failed:', e);
            hideExcelExtractionProgress();
            hideProgress();
            // v4.6.2: Destroy cinematic progress on Excel error
            if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
                HVCinematicProgress.destroy();
            }
            showToast('error', `Excel processing failed: ${e.message}`);
        }
    }

    // Pending Excel data for merging after async validation completes
    let _pendingExcelData = null;

    /**
     * Render Excel results with optional validation data merged in.
     */
    function _renderExcelExtractedResults(extractedLinks, extractionData, validationResults) {
        // Build a URL->validation map
        const urlResults = {};
        if (validationResults) {
            for (const vr of validationResults) {
                urlResults[vr.url] = vr;
            }
        }

        // Convert links to standard format for rendering
        const results = extractedLinks.map(link => {
            const vr = urlResults[link.url];
            return {
                url: link.url,
                status: vr?.status || (link.url.startsWith('mailto:') ? 'MAILTO' : 'EXTRACTED'),
                message: vr?.message || `Found in ${link.sheet_name} (${link.cell_address})`,
                status_code: vr?.status_code,
                response_time_ms: vr?.response_time_ms,
                link_source: link.source,
                sheet_name: link.sheet_name,
                cell_address: link.cell_address,
                display_text: link.display_text,
                context: link.context,
                validation: vr ? {
                    status: vr.status,
                    message: vr.message,
                    status_code: vr.status_code
                } : null
            };
        });

        // Build summary that matches renderExcelSummary expectations
        const summaryData = {
            links: results.map(r => ({
                url: r.url,
                validation: r.validation
            })),
            sheet_summaries: extractionData?.sheet_summaries || [],
            total_links: extractionData?.total_links || results.length,
            validation_summary: validationResults ? _buildValidationSummary(validationResults) : null
        };

        showResults();
        renderExcelSummary(summaryData);
        HyperlinkValidatorState.setLocalResults(results, summaryData.validation_summary);
        renderExcelResults(results);
        updateHighlightedExportButton(results);
        populateDomainFilter(results);  // v4.6.2
    }

    function _buildValidationSummary(results) {
        const summary = { working: 0, broken: 0, redirect: 0, timeout: 0, blocked: 0, unknown: 0 };
        for (const r of results) {
            const s = (r.status || '').toUpperCase();
            if (s === 'WORKING') summary.working++;
            else if (s === 'BROKEN' || s === 'INVALID' || s === 'DNSFAILED' || s === 'SSLERROR') summary.broken++;
            else if (s === 'REDIRECT') summary.redirect++;
            else if (s === 'TIMEOUT') summary.timeout++;
            else if (s === 'BLOCKED') summary.blocked++;
            else if (s === 'MAILTO' || s === 'EXTRACTED') { /* skip non-validated */ }
            else summary.unknown++;
        }
        return summary;
    }

    /**
     * Show a modern indeterminate progress indicator for Excel extraction phase.
     */
    function showExcelExtractionProgress(filename) {
        if (el.progressFill) {
            el.progressFill.classList.add('hv-indeterminate');
            el.progressFill.style.width = '100%';
        }
        if (el.progressText) {
            const displayName = filename.length > 40 ? filename.substring(0, 37) + '...' : filename;
            el.progressText.innerHTML = `<span class="hv-extract-phase"><i data-lucide="file-spreadsheet" style="width:16px;height:16px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> Extracting links from <strong>${escapeHtml(displayName)}</strong></span>`;
            if (typeof refreshIcons === 'function') refreshIcons();
        }
        if (el.progressStats) {
            el.progressStats.textContent = 'Scanning worksheets for hyperlinks, formulas, and URLs...';
        }
        if (el.progressEta) {
            el.progressEta.textContent = '';
        }
        // Show cancel button during extraction
        if (el.cancelBtn) {
            el.cancelBtn.style.display = 'inline-flex';
        }
    }

    function hideExcelExtractionProgress() {
        if (el.progressFill) {
            el.progressFill.classList.remove('hv-indeterminate');
        }
    }

    // =========================================================================
    // v3.0.110: HIGHLIGHTED EXPORT FUNCTIONS
    // =========================================================================

    /**
     * Check if there are broken links and enable/disable the highlighted export button.
     * v4.6.2: Also checks ArrayBuffer backup for file availability.
     */
    function updateHighlightedExportButton(results) {
        if (!el.exportHighlighted) return;

        const brokenStatuses = ['BROKEN', 'INVALID', 'TIMEOUT', 'DNSFAILED', 'SSLERROR', 'BLOCKED'];
        const brokenCount = results.filter(r =>
            brokenStatuses.includes(r.status?.toUpperCase())
        ).length;
        const hasBrokenLinks = brokenCount > 0;

        const hasSourceFile = sourceFile !== null || sourceFileBuffer !== null;

        if (hasSourceFile && hasBrokenLinks) {
            el.exportHighlighted.disabled = false;
            el.exportHighlighted.title = `Export ${sourceFileType === 'docx' ? 'DOCX' : 'Excel'} with ${brokenCount} broken link${brokenCount !== 1 ? 's' : ''} highlighted in red`;
            console.log(`[HyperlinkValidator] Export Highlighted button enabled (${brokenCount} broken links)`);
        } else if (hasSourceFile && !hasBrokenLinks) {
            el.exportHighlighted.disabled = true;
            el.exportHighlighted.title = 'No broken links to highlight';
        } else {
            el.exportHighlighted.disabled = true;
            el.exportHighlighted.title = 'Upload a DOCX or Excel file first';
        }
    }

    /**
     * Handle the Export Highlighted button click.
     * Sends the source file and validation results to the server for highlighting.
     * v4.6.2: Uses ArrayBuffer backup if File object is stale, improved logging.
     */
    async function handleExportHighlighted() {
        console.log('[HyperlinkValidator] Export Highlighted clicked', {
            hasSourceFile: !!sourceFile,
            hasSourceBuffer: !!sourceFileBuffer,
            sourceFileType,
            sourceFileName
        });

        if ((!sourceFile && !sourceFileBuffer) || !sourceFileType) {
            showToast('error', 'No source file available. Upload a DOCX or Excel file first.');
            return;
        }

        const results = HyperlinkValidatorState.getResults();
        if (!results || results.length === 0) {
            showToast('error', 'No validation results available.');
            return;
        }

        // Count broken links being sent
        const brokenStatuses = ['BROKEN', 'INVALID', 'TIMEOUT', 'DNSFAILED', 'SSLERROR', 'BLOCKED'];
        const brokenCount = results.filter(r => brokenStatuses.includes(r.status?.toUpperCase())).length;
        console.log(`[HyperlinkValidator] Sending ${results.length} results (${brokenCount} broken) for highlighting`);

        if (brokenCount === 0) {
            showToast('info', 'No broken links found to highlight.');
            return;
        }

        showToast('info', `Creating highlighted ${sourceFileType.toUpperCase()} file with ${brokenCount} broken links...`);

        try {
            const formData = new FormData();

            // v4.6.2: Use File object if available, fall back to ArrayBuffer backup
            let fileToSend = sourceFile;
            try {
                // Test if File object is still readable
                if (sourceFile) {
                    await sourceFile.slice(0, 1).arrayBuffer();
                }
            } catch (fileErr) {
                console.warn('[HyperlinkValidator] File object stale, using buffer backup:', fileErr);
                fileToSend = null;
            }

            if (fileToSend) {
                formData.append('file', fileToSend);
            } else if (sourceFileBuffer) {
                // Reconstruct File from ArrayBuffer
                const mimeType = sourceFileType === 'docx'
                    ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
                const reconstructedFile = new File(
                    [sourceFileBuffer],
                    sourceFileName || `document.${sourceFileType === 'docx' ? 'docx' : 'xlsx'}`,
                    { type: mimeType }
                );
                formData.append('file', reconstructedFile);
                console.log('[HyperlinkValidator] Using reconstructed file from buffer');
            } else {
                showToast('error', 'Source file is no longer available. Please re-upload the file.');
                return;
            }

            formData.append('results', JSON.stringify(results));

            // Get CSRF token
            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;

            const endpoint = sourceFileType === 'docx'
                ? '/api/hyperlink-validator/export-highlighted/docx'
                : '/api/hyperlink-validator/export-highlighted/excel';

            console.log(`[HyperlinkValidator] POST ${endpoint}`);

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
            });

            console.log(`[HyperlinkValidator] Response: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `Server error: ${response.status}`);
            }

            // Get the filename from the Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `highlighted_${sourceFileName || 'document'}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match) filename = match[1];
            }

            // Download the file
            const blob = await response.blob();
            console.log(`[HyperlinkValidator] Downloaded blob: ${blob.size} bytes`);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            // Delay revoke to allow download to start
            setTimeout(() => URL.revokeObjectURL(url), 5000);

            // Get highlight count from header if available
            const highlightCount = response.headers.get('X-Highlight-Count') || '';
            showToast('success', highlightCount || `Exported highlighted ${sourceFileType.toUpperCase()} file`);

        } catch (e) {
            console.error('[HyperlinkValidator] Export Highlighted failed:', e);
            showToast('error', `Highlighted export failed: ${e.message}`);
        }
    }

    function renderExcelSummary(data) {
        // v4.6.2: Count by detailed validation status (matching renderSummary breakdown)
        const counts = { working: 0, broken: 0, redirect: 0, timeout: 0, blocked: 0, unknown: 0 };
        let mailto = 0;

        data.links.forEach(link => {
            if (link.url.startsWith('mailto:')) {
                mailto++;
                return;
            }
            if (!link.validation) return;

            const s = (link.validation.status || '').toUpperCase();
            if (s === 'WORKING') counts.working++;
            else if (s === 'BROKEN' || s === 'INVALID' || s === 'DNSFAILED' || s === 'SSLERROR') counts.broken++;
            else if (s === 'REDIRECT') counts.redirect++;
            else if (s === 'TIMEOUT') counts.timeout++;
            else if (s === 'BLOCKED') counts.blocked++;
            else counts.unknown++;
        });

        // Update all stat cards with proper counts
        const statIds = {
            'hv-count-working': counts.working,
            'hv-count-broken': counts.broken,
            'hv-count-redirect': counts.redirect,
            'hv-count-timeout': counts.timeout,
            'hv-count-blocked': counts.blocked,
            'hv-count-unknown': counts.unknown
        };

        Object.entries(statIds).forEach(([id, count]) => {
            const elem = document.getElementById(id);
            if (elem) animateCount(elem, count);
        });

        // Show sheet breakdown
        if (data.sheet_summaries && data.sheet_summaries.length > 0) {
            const summaryHtml = data.sheet_summaries.map(s =>
                `<span class="hv-sheet-stat">${escapeHtml(s.name)}: ${s.total_links}</span>`
            ).join('');

            // Add sheet breakdown to summary if element exists
            const sheetBreakdown = document.getElementById('hv-sheet-breakdown');
            if (sheetBreakdown) {
                sheetBreakdown.innerHTML = summaryHtml;
            }
        }

        // Hide other counts that don't apply
        ['hv-count-timeout', 'hv-count-blocked', 'hv-count-unknown'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
    }

    function renderExcelResults(results) {
        if (!el.resultsBody) return;

        el.resultsBody.innerHTML = '';

        results.forEach((result, index) => {
            const row = document.createElement('tr');
            const statusClass = getExcelStatusClass(result.status);
            const sourceLabel = formatLinkSource(result.link_source);
            const isExcluded = isUrlExcluded(result.url);

            if (isExcluded) {
                row.classList.add('hv-row-excluded');
            }

            row.innerHTML = `
                <td>
                    <span class="hv-status-badge hv-status-${statusClass}">${isExcluded ? 'EXCLUDED' : result.status}</span>
                    <span class="hv-link-source-badge">${sourceLabel}</span>
                </td>
                <td class="hv-url-cell">
                    ${result.display_text && result.display_text !== result.url ?
                        `<span class="hv-display-text">${escapeHtml(result.display_text)}</span><br>` : ''}
                    <a href="${escapeHtml(result.url)}" target="_blank" rel="noopener">${escapeHtml(result.url)}</a>
                    <div class="hv-cell-location">
                        <span class="hv-sheet-name">${escapeHtml(result.sheet_name || '')}</span>
                        <span class="hv-cell-address">${escapeHtml(result.cell_address || '')}</span>
                        ${result.context ? `<span class="hv-cell-context">${escapeHtml(result.context)}</span>` : ''}
                    </div>
                </td>
                <td>${result.status_code || '-'}</td>
                <td>${escapeHtml(result.message || '')}</td>
                <td>${result.response_time_ms ? Math.round(result.response_time_ms) + 'ms' : '-'}</td>
                <td class="hv-col-actions">
                    ${isExcluded ?
                        `<button class="hv-btn-include" data-url="${escapeHtml(result.url)}" title="Remove from exclusions">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>` :
                        `<button class="hv-btn-exclude" data-url="${escapeHtml(result.url)}" title="Exclude this URL">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                        </button>`
                    }
                </td>
            `;
            el.resultsBody.appendChild(row);
        });

        if (results.length === 0) {
            el.resultsBody.innerHTML = `
                <tr><td colspan="6" class="hv-no-results">No links found in Excel file</td></tr>
            `;
        }

        // Bind action buttons
        bindResultActionButtons();
    }

    function getExcelStatusClass(status) {
        const statusMap = {
            'WORKING': 'working',
            'BROKEN': 'broken',
            'MAILTO': 'mailto',
            'EXTRACTED': 'unknown',
            'TIMEOUT': 'timeout',
            'REDIRECT': 'redirect'
        };
        return statusMap[status] || 'unknown';
    }

    function formatLinkSource(source) {
        const labels = {
            'hyperlink': 'Link',
            'formula': 'Formula',
            'cell_value': 'Cell Text',
            'comment': 'Comment'
        };
        return labels[source] || source || '';
    }

    function renderDocxSummary(data) {
        // Count by type
        const byType = {};
        data.links.forEach(link => {
            const type = link.link_type || 'unknown';
            byType[type] = (byType[type] || 0) + 1;
        });

        // Count valid/invalid
        const valid = data.validation_results.filter(r => r.validation.is_valid).length;
        const invalid = data.validation_results.length - valid;

        // Update summary counts (reuse existing elements)
        const workingEl = document.getElementById('hv-count-working');
        const brokenEl = document.getElementById('hv-count-broken');
        if (workingEl) workingEl.textContent = valid;
        if (brokenEl) brokenEl.textContent = invalid;

        // Hide other counts that don't apply
        ['hv-count-redirect', 'hv-count-timeout', 'hv-count-blocked', 'hv-count-unknown'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
    }

    function renderDocxResults(results) {
        if (!el.resultsBody) return;

        el.resultsBody.innerHTML = '';

        results.forEach((result, index) => {
            const row = document.createElement('tr');
            const isExcluded = isUrlExcluded(result.url);
            const statusClass = isExcluded ? 'excluded' : (result.status === 'WORKING' ? 'working' : 'broken');
            const linkTypeLabel = formatLinkType(result.link_type);

            if (isExcluded) {
                row.classList.add('hv-row-excluded');
            }

            row.innerHTML = `
                <td>
                    <span class="hv-status-badge hv-status-${statusClass}">${isExcluded ? 'EXCLUDED' : result.status}</span>
                    <span class="hv-link-type-badge">${linkTypeLabel}</span>
                </td>
                <td class="hv-url-cell">
                    ${result.display_text ? `<span class="hv-display-text">${escapeHtml(result.display_text)}</span><br>` : ''}
                    <a href="${escapeHtml(result.url)}" target="_blank" rel="noopener">${escapeHtml(result.url)}</a>
                    ${result.warnings?.length ? `<div class="hv-warnings">${result.warnings.map(w => `<span class="hv-warning">\u26A0 ${escapeHtml(w)}</span>`).join('')}</div>` : ''}
                </td>
                <td>-</td>
                <td>${escapeHtml(result.message || '')}</td>
                <td>-</td>
                <td class="hv-col-actions">
                    ${isExcluded ?
                        `<button class="hv-btn-include" data-url="${escapeHtml(result.url)}" title="Remove from exclusions">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>` :
                        `<button class="hv-btn-exclude" data-url="${escapeHtml(result.url)}" title="Exclude this URL">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                        </button>`
                    }
                </td>
            `;
            el.resultsBody.appendChild(row);
        });

        // Bind action buttons
        bindResultActionButtons();

        if (results.length === 0) {
            el.resultsBody.innerHTML = `
                <tr><td colspan="5" class="hv-no-results">No links found in document</td></tr>
            `;
        }
    }

    function formatLinkType(type) {
        const labels = {
            'web_url': 'Web',
            'mailto': 'Email',
            'file_path': 'File',
            'network_path': 'UNC',
            'bookmark': 'Bookmark',
            'cross_ref': 'Reference',
            'ftp': 'FTP',
            'unknown': '?'
        };
        return labels[type] || type;
    }

    function showExclusionForm() {
        if (el.exclusionForm) {
            el.exclusionForm.style.display = 'flex';
        }
        if (el.exclusionPattern) {
            el.exclusionPattern.focus();
        }
    }

    function hideExclusionForm() {
        if (el.exclusionForm) {
            el.exclusionForm.style.display = 'none';
        }
        // Clear form
        if (el.exclusionPattern) el.exclusionPattern.value = '';
        if (el.exclusionReason) el.exclusionReason.value = '';
        if (el.exclusionMatchType) el.exclusionMatchType.value = 'contains';
        if (el.exclusionTreatAsValid) el.exclusionTreatAsValid.checked = true;
    }

    function handleSaveExclusion() {
        const pattern = el.exclusionPattern?.value?.trim();
        if (!pattern) {
            showToast('error', 'Please enter a pattern');
            return;
        }

        const exclusion = {
            pattern: pattern,
            match_type: el.exclusionMatchType?.value || 'contains',
            reason: el.exclusionReason?.value || '',
            treat_as_valid: el.exclusionTreatAsValid?.checked ?? true
        };

        HyperlinkValidatorState.addExclusion(exclusion);

        // Hide and clear form
        hideExclusionForm();

        // Update exclusion count
        updateExclusionCount();

        renderExclusions(HyperlinkValidatorState.getExclusions());
        showToast('success', 'Exclusion added');
    }

    function updateExclusionCount() {
        const countEl = document.querySelector('.hv-exclusion-count');
        if (countEl) {
            const count = HyperlinkValidatorState.getExclusions().length;
            countEl.textContent = `(${count})`;
        }
    }

    function handleExclusionAction(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        const index = parseInt(target.dataset.index, 10);

        if (action === 'delete') {
            HyperlinkValidatorState.removeExclusion(index);
            renderExclusions(HyperlinkValidatorState.getExclusions());
            showToast('info', 'Exclusion removed');
        }
    }

    // ==========================================================================
    // STATE CHANGE HANDLERS
    // ==========================================================================

    function handleStateChange(state) {
        // Update history
        renderHistory(state.history);
    }

    function handleProgress(progress) {
        updateProgress(progress);

        // v4.6.2: Feed live_stats to cinematic progress overlay
        if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
            HVCinematicProgress.onProgress(progress, progress.liveStats || null);
        }
    }

    function handleComplete(data) {
        hideProgress();

        // v4.6.2: Complete cinematic progress with final summary
        if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
            HVCinematicProgress.complete(data.summary);
        }

        // Check if this validation was triggered by an Excel file upload
        if (_pendingExcelData) {
            const { extractedLinks, extractionData } = _pendingExcelData;
            _pendingExcelData = null;
            _renderExcelExtractedResults(extractedLinks, extractionData, data.results);
            showToast('success', `Validated ${data.results.length} URLs from Excel file`);
            return;
        }

        showResults();
        renderSummary(data.summary);
        renderResults(HyperlinkValidatorState.getFilteredResults());
        populateDomainFilter(data.results);  // v4.6.2
        showToast('success', `Validation complete: ${data.results.length} URLs checked`);
    }

    function handleError(error) {
        hideProgress();
        _pendingExcelData = null; // Clear pending Excel data on error

        // v4.6.2: Destroy cinematic progress on error
        if (typeof HVCinematicProgress !== 'undefined' && HVCinematicProgress.isActive()) {
            HVCinematicProgress.destroy();
        }
        showToast('error', error.message || 'An error occurred');
    }

    // ==========================================================================
    // UI UPDATES
    // ==========================================================================

    function showProgress() {
        if (el.progressSection) {
            el.progressSection.style.display = 'flex';
        }
        if (el.validateBtn) {
            el.validateBtn.disabled = true;
        }
    }

    function hideProgress() {
        if (el.progressSection) {
            el.progressSection.style.display = 'none';
        }
        if (el.validateBtn) {
            el.validateBtn.disabled = false;
        }
    }

    function updateProgress(progress) {
        if (el.progressFill) {
            el.progressFill.style.width = `${progress.overallProgress}%`;
        }
        if (el.progressText) {
            el.progressText.textContent = progress.phase || 'Validating...';
        }
        if (el.progressStats) {
            el.progressStats.textContent = `${progress.urlsCompleted} / ${progress.urlsTotal} URLs`;
        }
        if (el.progressEta && progress.eta) {
            el.progressEta.textContent = progress.eta;
        }
    }

    function showResults() {
        if (el.resultsSection) {
            el.resultsSection.style.display = 'block';
        }
    }

    function hideResults() {
        if (el.resultsSection) {
            el.resultsSection.style.display = 'none';
        }
    }

    function renderSummary(summary) {
        if (!summary) return;

        // Update summary counts
        const counts = {
            'hv-count-working': summary.working,
            'hv-count-broken': summary.broken,
            'hv-count-redirect': summary.redirect,
            'hv-count-timeout': summary.timeout,
            'hv-count-blocked': summary.blocked,
            'hv-count-unknown': (summary.unknown || 0) + (summary.dns_failed || 0) + (summary.ssl_error || 0) + (summary.invalid || 0)
        };

        Object.entries(counts).forEach(([id, count]) => {
            const elem = document.getElementById(id);
            if (elem) {
                // Animate the count
                animateCount(elem, count || 0);
            }
        });

        // Update extended metrics (for thorough mode)
        const scanDepth = el.scanDepthSelect?.value || 'standard';
        if (scanDepth === 'thorough' && el.extendedMetrics) {
            el.extendedMetrics.style.display = 'block';

            if (el.sslWarningsCount) el.sslWarningsCount.textContent = summary.ssl_warnings || 0;
            if (el.soft404Count) el.soft404Count.textContent = summary.soft_404_count || 0;
            if (el.suspiciousCount) el.suspiciousCount.textContent = summary.suspicious_count || 0;
            if (el.avgResponseTime) el.avgResponseTime.textContent = `${Math.round(summary.average_response_ms || 0)}ms`;
            if (el.minResponseTime) el.minResponseTime.textContent = `${Math.round(summary.min_response_ms || 0)}ms`;
            if (el.maxResponseTime) el.maxResponseTime.textContent = `${Math.round(summary.max_response_ms || 0)}ms`;
        } else if (el.extendedMetrics) {
            el.extendedMetrics.style.display = 'none';
        }

        // Render enhanced visualizations if available
        renderVisualizations(summary);

        // Show/hide rescan section based on rescan-eligible URL count
        const allResults = HyperlinkValidatorState.getResults() || [];
        _updateRescanSection(summary, allResults);

        // Bind rescan button if not already bound
        const rescanBtn = document.getElementById('hv-btn-rescan');
        if (rescanBtn && !rescanBtn.dataset.bound) {
            rescanBtn.dataset.bound = 'true';
            rescanBtn.addEventListener('click', handleRescan);
        }
    }

    /**
     * Animate a number counting up.
     */
    function animateCount(element, target) {
        const duration = 600;
        const start = parseInt(element.textContent) || 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (target - start) * easeOut);

            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    /**
     * Render enhanced visualizations (donut chart, histogram, heatmap).
     */
    function renderVisualizations(summary) {
        // Check if visualization module is loaded
        if (typeof HyperlinkVisualization === 'undefined') return;

        const results = HyperlinkValidatorState.getResults() || [];
        const total = Object.values(summary).reduce((sum, val) => typeof val === 'number' ? sum + val : sum, 0);

        // Only show visualizations if we have enough data
        if (total < 5) return;

        // Show chart section
        const chartSection = document.getElementById('hv-chart-section');
        if (chartSection) {
            chartSection.style.display = 'grid';

            // Donut chart
            const donutContainer = document.getElementById('hv-donut-chart');
            if (donutContainer) {
                HyperlinkVisualization.createDonutChart(donutContainer, {
                    working: summary.working || 0,
                    broken: summary.broken || 0,
                    redirect: summary.redirect || 0,
                    timeout: summary.timeout || 0,
                    blocked: summary.blocked || 0,
                    unknown: (summary.unknown || 0) + (summary.dns_failed || 0) + (summary.ssl_error || 0)
                });
            }

            // Response time histogram
            const histogramContainer = document.getElementById('hv-response-histogram');
            if (histogramContainer && results.length > 0) {
                HyperlinkVisualization.createResponseHistogram(histogramContainer, results);
            }
        }

        // Domain health visualization (only if >= 3 domains)
        const domains = new Set();
        results.forEach(r => {
            try { domains.add(new URL(r.url).hostname); } catch {}
        });

        if (domains.size >= 3) {
            // v3.0.125: Show 3D carousel for domain health (more impressive!)
            const carouselSection = document.getElementById('hv-domain-carousel-section');
            const carouselContainer = document.getElementById('hv-domain-carousel');
            if (carouselSection && carouselContainer) {
                carouselSection.style.display = 'block';
                HyperlinkVisualization.createDomainHealthCarousel(carouselContainer, results);
            }

            // Also show heatmap as an alternate compact view (for large datasets)
            if (domains.size > 10) {
                const heatmapSection = document.getElementById('hv-domain-heatmap-section');
                const heatmapContainer = document.getElementById('hv-domain-heatmap');
                if (heatmapSection && heatmapContainer) {
                    heatmapSection.style.display = 'block';
                    HyperlinkVisualization.createDomainHeatmap(heatmapContainer, results);
                }
            }
        }

        // Show rescan button if there are rescan-eligible URLs (blocked, timeout, auth, DNS, SSL)
        const allResults = HyperlinkValidatorState.getResults() || [];
        _updateRescanSection(summary, allResults);

        // Bind rescan button if not already bound
        const rescanBtn = document.getElementById('hv-btn-rescan');
        if (rescanBtn && !rescanBtn.dataset.bound) {
            rescanBtn.dataset.bound = 'true';
            rescanBtn.addEventListener('click', handleRescan);
        }
    }

    /**
     * Statuses eligible for headless browser rescan.
     */
    const RESCAN_ELIGIBLE_STATUSES = ['BLOCKED', 'TIMEOUT', 'DNSFAILED', 'AUTH_REQUIRED', 'SSLERROR'];

    /**
     * Handle rescan button click for bot-protected sites.
     * Uses Playwright headless browser to re-validate URLs that failed
     * due to bot protection, WAF, or auth-wall redirects.
     */
    async function handleRescan() {
        const rescanBtn = document.getElementById('hv-btn-rescan');
        if (!rescanBtn) return;

        // Get rescan-eligible URLs
        const currentResults = HyperlinkValidatorState.getResults() || [];
        const failedUrls = currentResults
            .filter(r => RESCAN_ELIGIBLE_STATUSES.includes((r.status || '').toUpperCase()))
            .map(r => r.url);

        if (failedUrls.length === 0) {
            showToast('info', 'No URLs eligible for headless rescan');
            return;
        }

        const urlCount = Math.min(failedUrls.length, 50);
        console.log(`[HV Rescan] Starting headless rescan for ${urlCount} of ${failedUrls.length} URLs`);

        // Show loading state with count
        rescanBtn.disabled = true;
        rescanBtn.classList.add('loading');
        const originalText = rescanBtn.innerHTML;
        rescanBtn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Rescanning ${urlCount} URLs...`;
        if (typeof lucide !== 'undefined') lucide.createIcons();

        try {
            const csrfToken = window.State?.csrfToken ||
                document.querySelector('meta[name="csrf-token"]')?.content;

            const response = await fetch('/api/hyperlink-validator/rescan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {})
                },
                body: JSON.stringify({ urls: failedUrls.slice(0, 50), timeout: 30 })
            });

            const data = await response.json();

            if (data.success && data.results && data.results.length > 0) {
                // Build a map of rescan results keyed by URL
                const rescanMap = {};
                for (const rr of data.results) {
                    rescanMap[rr.url] = rr;
                }

                // Merge rescan results back into the current results
                const updatedResults = currentResults.map(r => {
                    const rescanResult = rescanMap[r.url];
                    if (!rescanResult) return r;

                    // Only update if the rescan produced a different (better) result
                    const oldStatus = (r.status || '').toUpperCase();
                    const newStatus = (rescanResult.status || '').toUpperCase();

                    // If rescan recovered the URL (WORKING or REDIRECT), update it
                    if (newStatus === 'WORKING' || newStatus === 'REDIRECT') {
                        console.log(`[HV Rescan] Recovered: ${r.url} (${oldStatus} → ${newStatus})`);
                        return {
                            ...r,
                            status: rescanResult.status,
                            message: rescanResult.message || `Recovered via headless browser`,
                            status_code: rescanResult.status_code,
                            response_time_ms: rescanResult.response_time_ms,
                            final_url: rescanResult.final_url,
                            validation_method: 'headless_browser',
                            // Preserve Excel-specific fields
                            ...(r.sheet_name ? { sheet_name: r.sheet_name } : {}),
                            ...(r.cell_address ? { cell_address: r.cell_address } : {}),
                            ...(r.display_text ? { display_text: r.display_text } : {}),
                            ...(r.link_source ? { link_source: r.link_source } : {}),
                            ...(r.context ? { context: r.context } : {})
                        };
                    }

                    // If rescan found AUTH_REQUIRED where we had BLOCKED, update the status
                    if (newStatus === 'AUTH_REQUIRED' && oldStatus === 'BLOCKED') {
                        console.log(`[HV Rescan] Reclassified: ${r.url} (${oldStatus} → ${newStatus})`);
                        return {
                            ...r,
                            status: rescanResult.status,
                            message: rescanResult.message || 'Authentication required',
                            status_code: rescanResult.status_code,
                            validation_method: 'headless_browser'
                        };
                    }

                    // Otherwise keep original (rescan didn't improve)
                    return r;
                });

                // Update state with merged results (generates new summary automatically)
                HyperlinkValidatorState.setLocalResults(updatedResults);
                const newSummary = HyperlinkValidatorState.getSummary();

                // Re-render everything
                renderSummary(newSummary);
                renderResults(HyperlinkValidatorState.getFilteredResults());
                populateDomainFilter(updatedResults);

                // Update rescan section visibility (some URLs may no longer need rescan)
                _updateRescanSection(newSummary, updatedResults);

                // Report results
                const recovered = data.summary?.recovered || 0;
                const total = data.summary?.total || data.results.length;
                showToast('success',
                    `Headless rescan complete: ${recovered} of ${total} URLs recovered`
                );
                console.log(`[HV Rescan] Complete. Recovered: ${recovered}/${total}`, data.summary);
            } else if (data.success) {
                showToast('info', 'Rescan complete — no URLs were recovered');
            } else {
                throw new Error(data.error?.message || 'Rescan failed');
            }
        } catch (e) {
            console.error('[HV Rescan] Error:', e);
            if (e.message && e.message.includes('HEADLESS_UNAVAILABLE')) {
                showToast('error', 'Headless browser not available. Install: pip install playwright && playwright install chromium');
            } else {
                showToast('error', `Rescan failed: ${e.message}`);
            }
        } finally {
            rescanBtn.disabled = false;
            rescanBtn.classList.remove('loading');
            rescanBtn.innerHTML = originalText;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    /**
     * Update the rescan section visibility and count after a rescan.
     */
    function _updateRescanSection(summary, results) {
        const rescanSection = document.getElementById('hv-rescan-section');
        if (!rescanSection) return;

        // Count all rescan-eligible URLs
        const eligibleCount = results
            ? results.filter(r => RESCAN_ELIGIBLE_STATUSES.includes((r.status || '').toUpperCase())).length
            : (summary.blocked || 0) + (summary.timeout || 0);

        if (eligibleCount > 0) {
            rescanSection.style.display = 'block';
            const blockedCountEl = document.getElementById('hv-blocked-count');
            if (blockedCountEl) blockedCountEl.textContent = eligibleCount;
        } else {
            rescanSection.style.display = 'none';
        }
    }

    function renderExclusions(exclusions) {
        if (!el.exclusionsList) return;

        el.exclusionsList.innerHTML = '';

        if (!exclusions || exclusions.length === 0) {
            el.exclusionsList.innerHTML = '<div class="hv-exclusion-empty">No exclusions defined</div>';
            return;
        }

        exclusions.forEach((exc, index) => {
            const item = document.createElement('div');
            item.className = 'hv-exclusion-item';
            item.innerHTML = `
                <div class="hv-exclusion-info">
                    <span class="hv-exclusion-pattern">${escapeHtml(exc.pattern)}</span>
                    <span class="hv-exclusion-type">${exc.match_type}</span>
                    ${exc.treat_as_valid ? '<span class="hv-exclusion-valid">Show as OK</span>' : '<span class="hv-exclusion-skip">Skip</span>'}
                    ${exc.reason ? `<span class="hv-exclusion-reason">${escapeHtml(exc.reason)}</span>` : ''}
                </div>
                <button class="hv-exclusion-delete" data-action="delete" data-index="${index}" title="Remove">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            `;
            el.exclusionsList.appendChild(item);
        });
    }

    function renderResults(results) {
        if (!el.resultsBody) return;

        el.resultsBody.innerHTML = '';

        results.forEach((result, index) => {
            const row = document.createElement('tr');
            const isExcluded = isUrlExcluded(result.url);
            const statusClass = isExcluded ? 'excluded' : result.status.toLowerCase();

            if (isExcluded) {
                row.classList.add('hv-row-excluded');
            }

            row.innerHTML = `
                <td><span class="hv-status-badge hv-status-${statusClass}">${isExcluded ? 'EXCLUDED' : result.status}</span></td>
                <td class="hv-url-cell">
                    <a href="${escapeHtml(result.url)}" target="_blank" rel="noopener">${escapeHtml(result.url)}</a>
                </td>
                <td>${result.status_code || '-'}</td>
                <td>${escapeHtml(result.message || '')}</td>
                <td>${result.response_time_ms ? Math.round(result.response_time_ms) + 'ms' : '-'}</td>
                <td class="hv-col-actions">
                    ${isExcluded ?
                        `<button class="hv-btn-include" data-url="${escapeHtml(result.url)}" title="Remove from exclusions">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>` :
                        `<button class="hv-btn-exclude" data-url="${escapeHtml(result.url)}" title="Exclude this URL">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                        </button>`
                    }
                </td>
            `;
            el.resultsBody.appendChild(row);
        });

        // Show message if no results
        if (results.length === 0) {
            el.resultsBody.innerHTML = `
                <tr><td colspan="6" class="hv-no-results">No results match the current filters</td></tr>
            `;
        }

        // Bind action buttons
        bindResultActionButtons();
    }

    function renderHistory(history) {
        if (!el.historyList) return;

        el.historyList.innerHTML = '';

        if (!history || history.length === 0) {
            el.historyList.innerHTML = '<div class="hv-history-empty">No validation history</div>';
            return;
        }

        history.forEach(run => {
            const item = document.createElement('div');
            item.className = 'hv-history-item';
            item.innerHTML = `
                <div class="hv-history-info">
                    <span class="hv-history-date">${formatDate(run.created_at)}</span>
                    <span class="hv-history-count">${run.url_count || 0} URLs</span>
                </div>
                <div class="hv-history-summary">
                    ${run.summary ? `
                        <span class="hv-mini-stat working">${run.summary.working}</span>
                        <span class="hv-mini-stat broken">${run.summary.broken}</span>
                    ` : ''}
                </div>
            `;
            item.addEventListener('click', () => loadHistoricalRun(run.job_id));
            el.historyList.appendChild(item);
        });
    }

    async function loadHistoricalRun(jobId) {
        const success = await HyperlinkValidatorState.loadHistoricalRun(jobId);
        if (success) {
            showResults();
            renderSummary(HyperlinkValidatorState.getSummary());
            renderResults(HyperlinkValidatorState.getFilteredResults());
        }
    }

    function updateCapabilitiesDisplay() {
        const caps = HyperlinkValidatorState.getCapabilities();
        if (!caps) return;

        // Disable unavailable modes in select
        if (el.modeSelect) {
            Array.from(el.modeSelect.options).forEach(opt => {
                const mode = caps.modes[opt.value];
                if (mode && !mode.available) {
                    opt.disabled = true;
                    opt.textContent += ' (unavailable)';
                }
            });
        }
    }

    function toggleSettings() {
        const settings = document.getElementById('hv-settings');
        settings?.classList.toggle('collapsed');
    }

    function switchTab(tab) {
        // Update tab buttons
        el.tabPaste?.classList.toggle('active', tab === 'paste');
        el.tabUpload?.classList.toggle('active', tab === 'upload');

        // Update tab content
        if (el.tabContentPaste) {
            el.tabContentPaste.style.display = tab === 'paste' ? 'block' : 'none';
        }
        if (el.tabContentUpload) {
            el.tabContentUpload.style.display = tab === 'upload' ? 'block' : 'none';
        }
    }

    // ==========================================================================
    // UTILITIES
    // ==========================================================================

    function parseUrls(text) {
        if (!text) return [];

        const lines = text.replace(/,/g, '\n').replace(/;/g, '\n').split('\n');
        const urls = [];

        lines.forEach(line => {
            line = line.trim();
            if (!line || line.startsWith('#')) return;

            // Add https:// if missing scheme
            if (line.match(/^[a-zA-Z0-9]/) && line.includes('.') && !line.includes('://')) {
                line = 'https://' + line;
            }

            if (line.startsWith('http://') || line.startsWith('https://') || line.startsWith('ftp://')) {
                urls.push(line);
            }
        });

        // Remove duplicates
        return [...new Set(urls)];
    }

    function getValidationOptions() {
        return {
            timeout: parseInt(document.getElementById('hv-timeout')?.value) || 10,
            retries: parseInt(document.getElementById('hv-retries')?.value) || 3,
            use_windows_auth: document.getElementById('hv-windows-auth')?.checked ?? true,
            follow_redirects: document.getElementById('hv-follow-redirects')?.checked ?? true,
            scan_depth: el.scanDepthSelect?.value || 'standard',
            exclusions: HyperlinkValidatorState.getExclusions()
        };
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function debounce(fn, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function showToast(type, message) {
        // Use TWR.Modals if available
        if (typeof TWR !== 'undefined' && TWR.Modals?.toast) {
            TWR.Modals.toast(type, message);
        } else {
            console.log(`[TWR HyperlinkValidator] ${type}: ${message}`);
        }
    }

    // ==========================================================================
    // EXCLUSION HELPERS
    // ==========================================================================

    /**
     * Check if a URL matches any exclusion rule.
     */
    function isUrlExcluded(url) {
        const exclusions = HyperlinkValidatorState.getExclusions();
        if (!exclusions || exclusions.length === 0) return false;

        for (const exc of exclusions) {
            if (matchesExclusion(url, exc)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Check if a URL matches a specific exclusion rule.
     */
    function matchesExclusion(url, exclusion) {
        const pattern = exclusion.pattern;
        const matchType = exclusion.match_type || 'contains';

        switch (matchType) {
            case 'exact':
                return url === pattern;
            case 'prefix':
                return url.startsWith(pattern);
            case 'suffix':
                return url.endsWith(pattern);
            case 'contains':
                return url.includes(pattern);
            case 'regex':
                try {
                    const regex = new RegExp(pattern, 'i');
                    return regex.test(url);
                } catch {
                    return false;
                }
            default:
                return url.includes(pattern);
        }
    }

    /**
     * Bind click handlers for exclude/include buttons in results table.
     */
    function bindResultActionButtons() {
        // Exclude buttons - show menu on click
        el.resultsBody?.querySelectorAll('.hv-btn-exclude').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const url = btn.dataset.url;
                if (url) {
                    showExcludeMenu(btn, url);
                }
            });
        });

        // Include buttons (remove exclusion)
        el.resultsBody?.querySelectorAll('.hv-btn-include').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const url = btn.dataset.url;
                if (url) {
                    removeExclusionByUrl(url);
                }
            });
        });
    }

    /**
     * Show exclude menu with options for URL vs domain exclusion.
     */
    function showExcludeMenu(btn, url) {
        // Remove any existing menu
        document.querySelectorAll('.hv-exclude-menu').forEach(m => m.remove());

        // Extract domain info
        let hostname = null;
        let baseDomain = null;
        try {
            const parsed = new URL(url);
            hostname = parsed.hostname;
            // Get base domain (e.g., example.com from sub.example.com)
            const parts = hostname.split('.');
            if (parts.length >= 2) {
                baseDomain = parts.slice(-2).join('.');
            }
        } catch {
            // Non-URL, just offer exact match
        }

        // Count how many results would be affected by domain exclusion
        const results = HyperlinkValidatorState.getResults() || [];
        let domainCount = 0;
        if (hostname) {
            domainCount = results.filter(r => {
                try {
                    return new URL(r.url).hostname === hostname;
                } catch { return false; }
            }).length;
        }

        // Build menu
        const menu = document.createElement('div');
        menu.className = 'hv-exclude-menu';

        let menuHtml = `
            <div class="hv-exclude-menu-item" data-action="url" data-url="${escapeHtml(url)}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                <span>Exclude this URL only</span>
            </div>
        `;

        if (hostname) {
            menuHtml += `
                <div class="hv-exclude-menu-item" data-action="domain" data-pattern="${escapeHtml(hostname)}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>Exclude all from <strong>${escapeHtml(hostname)}</strong></span>
                    ${domainCount > 1 ? `<span class="hv-menu-count">${domainCount} URLs</span>` : ''}
                </div>
            `;

            // If there's a subdomain, offer base domain option
            if (baseDomain && baseDomain !== hostname) {
                const baseDomainCount = results.filter(r => {
                    try {
                        return new URL(r.url).hostname.endsWith(baseDomain);
                    } catch { return false; }
                }).length;

                menuHtml += `
                    <div class="hv-exclude-menu-item" data-action="basedomain" data-pattern="${escapeHtml(baseDomain)}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                        <span>Exclude all *.${escapeHtml(baseDomain)}</span>
                        ${baseDomainCount > 1 ? `<span class="hv-menu-count">${baseDomainCount} URLs</span>` : ''}
                    </div>
                `;
            }
        }

        menu.innerHTML = menuHtml;

        // Add to body first so we can measure it
        document.body.appendChild(menu);

        // Position menu below button using fixed positioning
        const rect = btn.getBoundingClientRect();
        const menuWidth = 280; // Use min-width from CSS
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        // Calculate left position - align right edge of menu with right edge of button
        let leftPos = rect.right - menuWidth;

        // Keep within viewport bounds
        if (leftPos < 10) {
            leftPos = 10;
        } else if (leftPos + menuWidth > viewportWidth - 10) {
            leftPos = viewportWidth - menuWidth - 10;
        }

        // Calculate top position - below button, or above if not enough space below
        let topPos = rect.bottom + 4;
        if (topPos + 200 > viewportHeight) {
            // Not enough space below, show above
            topPos = rect.top - 200;
            if (topPos < 10) topPos = 10;
        }

        menu.style.top = `${topPos}px`;
        menu.style.left = `${leftPos}px`;

        // Handle menu item clicks
        menu.querySelectorAll('.hv-exclude-menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;

                if (action === 'url') {
                    excludeExactUrl(item.dataset.url);
                } else if (action === 'domain') {
                    excludeDomain(item.dataset.pattern, 'exact');
                } else if (action === 'basedomain') {
                    excludeDomain(item.dataset.pattern, 'suffix');
                }

                menu.remove();
            });
        });

        // Close menu on outside click
        const closeMenu = (e) => {
            if (!menu.contains(e.target) && e.target !== btn) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    }

    /**
     * Exclude a single exact URL.
     */
    function excludeExactUrl(url) {
        HyperlinkValidatorState.addExclusion({
            pattern: url,
            match_type: 'exact',
            reason: 'Excluded URL',
            treat_as_valid: true
        });

        updateExclusionCount();
        renderExclusions(HyperlinkValidatorState.getExclusions());
        refreshCurrentResults();
        showToast('success', `Excluded URL`);
    }

    /**
     * Exclude by domain pattern.
     */
    function excludeDomain(domain, matchType = 'exact') {
        // For suffix matching on base domain, we match the hostname ending
        const pattern = matchType === 'suffix' ? `.${domain}` : domain;

        HyperlinkValidatorState.addExclusion({
            pattern: matchType === 'suffix' ? domain : domain,
            match_type: matchType === 'suffix' ? 'suffix' : 'contains',
            reason: `Excluded domain: ${domain}`,
            treat_as_valid: true
        });

        updateExclusionCount();
        renderExclusions(HyperlinkValidatorState.getExclusions());
        refreshCurrentResults();

        const count = countExcludedUrls();
        showToast('success', `Excluded ${domain} (${count} URLs affected)`);
    }

    /**
     * Count how many URLs are now excluded.
     */
    function countExcludedUrls() {
        const results = HyperlinkValidatorState.getResults() || [];
        return results.filter(r => isUrlExcluded(r.url)).length;
    }

    /**
     * Legacy function - now shows menu instead.
     */
    function quickExcludeUrl(url) {
        // Default to domain exclusion for backwards compatibility
        let pattern = url;
        try {
            const parsed = new URL(url);
            pattern = parsed.hostname;
        } catch {
            // Use full URL if parsing fails
        }

        HyperlinkValidatorState.addExclusion({
            pattern: pattern,
            match_type: 'contains',
            reason: 'Excluded from results',
            treat_as_valid: true
        });

        updateExclusionCount();
        renderExclusions(HyperlinkValidatorState.getExclusions());

        // Re-render current results to reflect exclusion
        refreshCurrentResults();

        showToast('success', `Excluded: ${pattern}`);
    }

    /**
     * Remove exclusion that matches a URL.
     */
    function removeExclusionByUrl(url) {
        const exclusions = HyperlinkValidatorState.getExclusions();
        const index = exclusions.findIndex(exc => matchesExclusion(url, exc));

        if (index >= 0) {
            HyperlinkValidatorState.removeExclusion(index);
            updateExclusionCount();
            renderExclusions(HyperlinkValidatorState.getExclusions());
            refreshCurrentResults();
            showToast('info', 'Exclusion removed');
        }
    }

    /**
     * Refresh the current results display.
     */
    function refreshCurrentResults() {
        const results = HyperlinkValidatorState.getResults();
        if (results && results.length > 0) {
            // Check if these are Excel/DOCX results (have sheet_name or link_type)
            if (results[0].sheet_name) {
                renderExcelResults(results);
            } else if (results[0].link_type) {
                renderDocxResults(results);
            } else {
                renderResults(HyperlinkValidatorState.getFilteredResults());
            }
        }
    }

    // ==========================================================================
    // PUBLIC API
    // ==========================================================================

    return {
        init,
        open,
        close,
        _parseUrls: parseUrls,
        _renderResults: renderResults,
        _updateProgress: updateProgress
    };

})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Don't auto-init, wait for first open
});
