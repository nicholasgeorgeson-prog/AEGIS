/**
 * Portfolio Module - Visual Tile Dashboard
 * =========================================
 * v3.0.114 - Stunning tile-based view for batch results and document history
 *
 * Features:
 * - Animated batch cards with cascade expansion
 * - Document tiles with quick preview
 * - Visual health indicators and gradients
 * - Smooth transitions and micro-interactions
 * - Activity feed sidebar
 */

window.Portfolio = (function() {
    'use strict';

    // =========================================================================
    // STATE
    // =========================================================================

    const state = {
        isOpen: false,
        batches: [],
        singles: [],
        stats: null,
        expandedBatch: null,
        selectedDocument: null,
        viewMode: 'grid', // 'grid' or 'list'
        isLoading: false,
        error: null
    };

    // =========================================================================
    // DOM REFERENCES
    // =========================================================================

    let elements = {
        modal: null,
        container: null,
        batchGrid: null,
        singlesGrid: null,
        statsBar: null,
        activityFeed: null,
        previewPanel: null
    };

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    function init() {
        console.log('[TWR Portfolio] Initializing...');
        createModal();
        setupEventListeners();
        console.log('[TWR Portfolio] Module ready');
    }

    function createModal() {
        // Check if modal already exists
        if (document.getElementById('portfolio-modal')) {
            elements.modal = document.getElementById('portfolio-modal');
            return;
        }

        const modal = document.createElement('div');
        modal.id = 'portfolio-modal';
        modal.className = 'pf-modal';
        modal.innerHTML = `
            <div class="pf-modal-content">
                <!-- Header -->
                <div class="pf-header">
                    <div class="pf-header-left">
                        <div class="pf-logo">
                            <i data-lucide="layout-grid" class="pf-logo-icon"></i>
                            <span class="pf-title">Portfolio</span>
                        </div>
                        <div class="pf-subtitle">Document Analysis Dashboard</div>
                    </div>
                    <div class="pf-header-center">
                        <div class="pf-stats-mini" id="pf-stats-mini">
                            <div class="pf-stat-chip">
                                <span class="pf-stat-value" id="pf-stat-docs">--</span>
                                <span class="pf-stat-label">Documents</span>
                            </div>
                            <div class="pf-stat-chip">
                                <span class="pf-stat-value" id="pf-stat-batches">--</span>
                                <span class="pf-stat-label">Batches</span>
                            </div>
                            <div class="pf-stat-chip pf-stat-score">
                                <span class="pf-stat-value" id="pf-stat-avg">--</span>
                                <span class="pf-stat-label">Avg Score</span>
                            </div>
                        </div>
                    </div>
                    <div class="pf-header-right">
                        <button class="pf-view-toggle" id="pf-view-toggle" title="Toggle view">
                            <i data-lucide="grid-3x3"></i>
                        </button>
                        <button class="pf-close-btn" id="pf-close-btn" title="Close Portfolio">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="pf-body">
                    <!-- Sidebar - Activity Feed -->
                    <div class="pf-sidebar" id="pf-sidebar">
                        <div class="pf-sidebar-header">
                            <i data-lucide="activity"></i>
                            <span>Recent Activity</span>
                        </div>
                        <div class="pf-activity-feed" id="pf-activity-feed">
                            <!-- Activity items rendered here -->
                        </div>
                    </div>

                    <!-- Main Grid Area -->
                    <div class="pf-main">
                        <!-- Loading State -->
                        <div class="pf-loading" id="pf-loading" style="display: none;">
                            <div class="pf-spinner"></div>
                            <span>Loading your portfolio...</span>
                        </div>

                        <!-- Empty State -->
                        <div class="pf-empty" id="pf-empty" style="display: none;">
                            <i data-lucide="folder-open"></i>
                            <h3>No Documents Yet</h3>
                            <p>Upload documents using the Batch feature to see them here</p>
                            <button class="pf-empty-btn" onclick="Portfolio.close(); document.getElementById('btn-batch-load')?.click();">
                                <i data-lucide="upload"></i>
                                Start Batch Upload
                            </button>
                        </div>

                        <!-- Batches Section -->
                        <div class="pf-section" id="pf-batches-section">
                            <div class="pf-section-header">
                                <h3><i data-lucide="layers"></i> Batch Sessions</h3>
                                <span class="pf-section-count" id="pf-batch-count">0 batches</span>
                            </div>
                            <div class="pf-batch-grid" id="pf-batch-grid">
                                <!-- Batch cards rendered here -->
                            </div>
                        </div>

                        <!-- Singles Section -->
                        <div class="pf-section" id="pf-singles-section">
                            <div class="pf-section-header">
                                <h3><i data-lucide="file-text"></i> Individual Documents</h3>
                                <span class="pf-section-count" id="pf-singles-count">0 documents</span>
                            </div>
                            <div class="pf-doc-grid" id="pf-singles-grid">
                                <!-- Document tiles rendered here -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Expanded Batch Overlay -->
                <div class="pf-batch-overlay" id="pf-batch-overlay" style="display: none;">
                    <div class="pf-batch-expanded">
                        <div class="pf-batch-expanded-header">
                            <button class="pf-back-btn" onclick="Portfolio.closeBatchExpand()">
                                <i data-lucide="arrow-left"></i>
                                Back to Portfolio
                            </button>
                            <div class="pf-batch-title" id="pf-batch-title">Batch Details</div>
                            <div class="pf-batch-meta" id="pf-batch-meta"></div>
                        </div>
                        <div class="pf-batch-expanded-grid" id="pf-batch-expanded-grid">
                            <!-- Expanded batch documents -->
                        </div>
                    </div>
                </div>

                <!-- Document Preview Panel (outside pf-body for proper z-index stacking) -->
                <div class="pf-preview-panel" id="pf-preview-panel" style="display: none;">
                    <div class="pf-preview-header">
                        <span>Document Preview</span>
                        <button class="pf-preview-close" onclick="Portfolio.closePreview()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="pf-preview-content" id="pf-preview-content">
                        <!-- Preview content rendered here -->
                    </div>
                    <div class="pf-preview-actions">
                        <button class="pf-btn pf-btn-primary" id="pf-open-doc-btn">
                            <i data-lucide="external-link"></i>
                            Open in Review
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        elements.modal = modal;

        // Cache other elements
        elements.batchGrid = document.getElementById('pf-batch-grid');
        elements.singlesGrid = document.getElementById('pf-singles-grid');
        elements.activityFeed = document.getElementById('pf-activity-feed');
        elements.previewPanel = document.getElementById('pf-preview-panel');

        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons({ attrs: { class: 'lucide-icon' } });
        }
    }

    function setupEventListeners() {
        // Close button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#pf-close-btn')) {
                close();
            }
        });

        // View toggle
        document.addEventListener('click', (e) => {
            if (e.target.closest('#pf-view-toggle')) {
                toggleViewMode();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isOpen) {
                if (state.expandedBatch) {
                    closeBatchExpand();
                } else if (state.selectedDocument) {
                    closePreview();
                } else {
                    close();
                }
            }
        });

        // Click outside to close preview
        document.addEventListener('click', (e) => {
            if (state.isOpen && state.selectedDocument &&
                !e.target.closest('.pf-preview-panel') &&
                !e.target.closest('.pf-doc-tile')) {
                closePreview();
            }
        });

        // Handle Open in Review button via delegation
        document.addEventListener('click', (e) => {
            const openBtn = e.target.closest('#pf-open-doc-btn');
            if (openBtn && state.selectedDocument) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[TWR Portfolio] Open button clicked via delegation!');
                // Get filepath/filename from the preview panel content
                const panel = document.getElementById('pf-preview-panel');
                if (panel && panel._previewData) {
                    openDocument(panel._previewData.filepath, panel._previewData.filename);
                }
            }
        });
    }

    // =========================================================================
    // MODAL CONTROL
    // =========================================================================

    async function open() {
        console.log('[TWR Portfolio] Opening...');
        state.isOpen = true;

        if (!elements.modal) {
            createModal();
        }

        elements.modal.classList.add('pf-active');
        document.body.style.overflow = 'hidden';

        // Load data
        await loadPortfolioData();

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons(), 100);
        }
    }

    function close() {
        console.log('[TWR Portfolio] Closing...');
        state.isOpen = false;
        state.expandedBatch = null;
        state.selectedDocument = null;

        if (elements.modal) {
            elements.modal.classList.remove('pf-active');
        }
        document.body.style.overflow = '';

        // v4.6.1: Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage) {
            TWR.LandingPage.show();
        }
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async function loadPortfolioData() {
        showLoading(true);

        try {
            // Load batches and stats in parallel
            const [batchesRes, statsRes, activityRes] = await Promise.all([
                fetch('/api/portfolio/batches'),
                fetch('/api/portfolio/stats'),
                fetch('/api/portfolio/recent?limit=10')
            ]);

            const batchesData = await batchesRes.json();
            const statsData = await statsRes.json();
            const activityData = await activityRes.json();

            if (batchesData.success) {
                state.batches = batchesData.batches || [];
                state.singles = batchesData.singles || [];
            }

            if (statsData.success) {
                state.stats = statsData.stats;
                renderStats(state.stats);
            }

            if (activityData.success) {
                renderActivityFeed(activityData.activity || []);
            }

            renderPortfolio();
            showLoading(false);

        } catch (error) {
            console.error('[TWR Portfolio] Error loading data:', error);
            state.error = error.message;
            showLoading(false);
            showError('Failed to load portfolio data');
        }
    }

    // =========================================================================
    // RENDERING
    // =========================================================================

    function showLoading(show) {
        const loadingEl = document.getElementById('pf-loading');
        const batchSection = document.getElementById('pf-batches-section');
        const singlesSection = document.getElementById('pf-singles-section');

        if (loadingEl) {
            loadingEl.style.display = show ? 'flex' : 'none';
        }
        if (batchSection) {
            batchSection.style.display = show ? 'none' : 'block';
        }
        if (singlesSection) {
            singlesSection.style.display = show ? 'none' : 'block';
        }
    }

    function showError(message) {
        // Could show a toast or inline error
        console.error('[TWR Portfolio]', message);
    }

    function renderStats(stats) {
        if (!stats) return;

        const docsEl = document.getElementById('pf-stat-docs');
        const batchesEl = document.getElementById('pf-stat-batches');
        const avgEl = document.getElementById('pf-stat-avg');

        if (docsEl) docsEl.textContent = stats.total_documents || 0;
        if (batchesEl) batchesEl.textContent = state.batches.length || 0;
        if (avgEl) avgEl.textContent = (stats.avg_score || 0) + '%';
    }

    function renderPortfolio() {
        const emptyEl = document.getElementById('pf-empty');
        const batchSection = document.getElementById('pf-batches-section');
        const singlesSection = document.getElementById('pf-singles-section');

        // Check if empty
        if (state.batches.length === 0 && state.singles.length === 0) {
            emptyEl.style.display = 'flex';
            batchSection.style.display = 'none';
            singlesSection.style.display = 'none';
            return;
        }

        emptyEl.style.display = 'none';

        // Render batches
        if (state.batches.length > 0) {
            batchSection.style.display = 'block';
            document.getElementById('pf-batch-count').textContent =
                `${state.batches.length} batch${state.batches.length !== 1 ? 'es' : ''}`;
            renderBatches();
        } else {
            batchSection.style.display = 'none';
        }

        // Render singles
        if (state.singles.length > 0) {
            singlesSection.style.display = 'block';
            document.getElementById('pf-singles-count').textContent =
                `${state.singles.length} document${state.singles.length !== 1 ? 's' : ''}`;
            renderSingles();
        } else {
            singlesSection.style.display = 'none';
        }

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons(), 50);
        }
    }

    function renderBatches() {
        if (!elements.batchGrid) return;

        elements.batchGrid.innerHTML = state.batches.map((batch, index) => `
            <div class="pf-batch-card" data-batch-id="${batch.id}" style="--delay: ${index * 50}ms">
                <div class="pf-batch-card-header">
                    <div class="pf-batch-icon pf-grade-${batch.grade_color}">
                        <i data-lucide="folder"></i>
                    </div>
                    <div class="pf-batch-info">
                        <div class="pf-batch-name">${escapeHtml(batch.name)}</div>
                        <div class="pf-batch-time">${batch.formatted_time}</div>
                    </div>
                    <div class="pf-batch-score pf-grade-bg-${batch.grade_color}">
                        ${batch.avg_score}%
                    </div>
                </div>
                <div class="pf-batch-stats">
                    <div class="pf-batch-stat">
                        <span class="pf-batch-stat-value">${batch.document_count}</span>
                        <span class="pf-batch-stat-label">Docs</span>
                    </div>
                    <div class="pf-batch-stat">
                        <span class="pf-batch-stat-value">${batch.total_issues}</span>
                        <span class="pf-batch-stat-label">Issues</span>
                    </div>
                    <div class="pf-batch-stat">
                        <span class="pf-batch-stat-value">${batch.dominant_grade}</span>
                        <span class="pf-batch-stat-label">Grade</span>
                    </div>
                </div>
                <div class="pf-batch-preview">
                    ${renderBatchPreviewTiles(batch.documents)}
                </div>
                <div class="pf-batch-footer">
                    <button class="pf-expand-btn" onclick="Portfolio.expandBatch('${batch.id}')">
                        <i data-lucide="maximize-2"></i>
                        View All Documents
                    </button>
                </div>
            </div>
        `).join('');

        // Add click handlers
        elements.batchGrid.querySelectorAll('.pf-batch-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.pf-expand-btn')) {
                    expandBatch(card.dataset.batchId);
                }
            });
        });
    }

    function renderBatchPreviewTiles(documents) {
        if (!documents || documents.length === 0) return '';

        const tiles = documents.slice(0, 4).map(doc => `
            <div class="pf-mini-tile pf-grade-border-${doc.grade_color}" title="${escapeHtml(doc.filename)}">
                <span class="pf-mini-grade">${doc.grade}</span>
            </div>
        `).join('');

        const extra = documents.length > 4 ?
            `<div class="pf-mini-tile pf-mini-more">+${documents.length - 4}</div>` : '';

        return tiles + extra;
    }

    function renderSingles() {
        if (!elements.singlesGrid) return;

        elements.singlesGrid.innerHTML = state.singles.map((doc, index) =>
            renderDocumentTile(doc, index)
        ).join('');

        // Add click handlers
        elements.singlesGrid.querySelectorAll('.pf-doc-tile').forEach(tile => {
            tile.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('[TWR Portfolio] Singles tile clicked, scanId:', tile.dataset.scanId);
                selectDocument(parseInt(tile.dataset.scanId));
            });
        });
    }

    function renderDocumentTile(doc, index = 0) {
        const truncatedName = doc.filename.length > 25 ?
            doc.filename.substring(0, 22) + '...' : doc.filename;

        return `
            <div class="pf-doc-tile" data-scan-id="${doc.id}" style="--delay: ${index * 30}ms">
                <div class="pf-doc-tile-glow pf-grade-glow-${doc.grade_color}"></div>
                <div class="pf-doc-header">
                    <div class="pf-doc-icon">
                        <i data-lucide="${doc.filename.endsWith('.pdf') ? 'file-text' : 'file'}"></i>
                    </div>
                    <div class="pf-doc-score pf-grade-bg-${doc.grade_color}">
                        ${doc.score}%
                    </div>
                </div>
                <div class="pf-doc-body">
                    <div class="pf-doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(truncatedName)}</div>
                    <div class="pf-doc-meta">
                        <span><i data-lucide="alert-circle"></i> ${doc.issue_count}</span>
                        <span><i data-lucide="type"></i> ${formatWordCount(doc.word_count)}</span>
                    </div>
                </div>
                <div class="pf-doc-footer">
                    <span class="pf-doc-time">${doc.formatted_time}</span>
                    <span class="pf-doc-grade pf-grade-text-${doc.grade_color}">${doc.grade}</span>
                </div>
            </div>
        `;
    }

    function renderActivityFeed(activity) {
        if (!elements.activityFeed) return;

        if (!activity || activity.length === 0) {
            elements.activityFeed.innerHTML = `
                <div class="pf-activity-empty">
                    <i data-lucide="inbox"></i>
                    <span>No recent activity</span>
                </div>
            `;
            return;
        }

        elements.activityFeed.innerHTML = activity.map(item => `
            <div class="pf-activity-item" data-scan-id="${item.id}">
                <div class="pf-activity-dot pf-grade-bg-${item.grade_color}"></div>
                <div class="pf-activity-content">
                    <div class="pf-activity-name">${escapeHtml(item.filename)}</div>
                    <div class="pf-activity-meta">
                        <span class="pf-activity-score">${item.score}%</span>
                        <span class="pf-activity-time">${item.formatted_time}</span>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers
        elements.activityFeed.querySelectorAll('.pf-activity-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('[TWR Portfolio] Activity item clicked, scanId:', item.dataset.scanId);
                selectDocument(parseInt(item.dataset.scanId));
            });
        });
    }

    // =========================================================================
    // BATCH EXPANSION
    // =========================================================================

    async function expandBatch(batchId) {
        console.log('[TWR Portfolio] Expanding batch:', batchId);
        state.expandedBatch = batchId;

        const overlay = document.getElementById('pf-batch-overlay');
        const grid = document.getElementById('pf-batch-expanded-grid');
        const title = document.getElementById('pf-batch-title');
        const meta = document.getElementById('pf-batch-meta');

        if (!overlay || !grid) return;

        // Show overlay with loading
        overlay.style.display = 'flex';
        grid.innerHTML = '<div class="pf-loading"><div class="pf-spinner"></div></div>';

        try {
            const response = await fetch(`/api/portfolio/batch/${batchId}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load batch');
            }

            const batch = data.batch;
            const documents = data.documents;

            // Update header
            title.textContent = batch.name;
            meta.innerHTML = `
                <span><i data-lucide="file"></i> ${batch.document_count} documents</span>
                <span><i data-lucide="alert-triangle"></i> ${batch.total_issues} issues</span>
                <span><i data-lucide="bar-chart-2"></i> ${batch.avg_score}% avg</span>
            `;

            // Render documents
            grid.innerHTML = documents.map((doc, index) => renderDocumentTile(doc, index)).join('');

            // Add click handlers
            grid.querySelectorAll('.pf-doc-tile').forEach(tile => {
                tile.addEventListener('click', (e) => {
                    e.stopPropagation();
                    console.log('[TWR Portfolio] Tile clicked, scanId:', tile.dataset.scanId);
                    selectDocument(parseInt(tile.dataset.scanId));
                });
            });

            // Refresh icons
            if (typeof lucide !== 'undefined') {
                setTimeout(() => lucide.createIcons(), 50);
            }

        } catch (error) {
            console.error('[TWR Portfolio] Error loading batch:', error);
            grid.innerHTML = `<div class="pf-error">Failed to load batch: ${error.message}</div>`;
        }
    }

    function closeBatchExpand() {
        state.expandedBatch = null;
        const overlay = document.getElementById('pf-batch-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // =========================================================================
    // DOCUMENT PREVIEW & SELECTION
    // =========================================================================

    async function selectDocument(scanId) {
        console.log('[TWR Portfolio] selectDocument called with scanId:', scanId);
        state.selectedDocument = scanId;

        const panel = document.getElementById('pf-preview-panel');
        const content = document.getElementById('pf-preview-content');

        console.log('[TWR Portfolio] Preview panel found:', !!panel, 'Content found:', !!content);

        if (!panel || !content) {
            console.error('[TWR Portfolio] Preview panel or content not found!');
            return;
        }

        // Show panel with loading
        panel.style.display = 'flex';
        content.innerHTML = '<div class="pf-loading"><div class="pf-spinner"></div></div>';

        try {
            const response = await fetch(`/api/portfolio/document/${scanId}/preview`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load preview');
            }

            const preview = data.preview;
            renderPreview(preview);

            // Store preview data on panel for event delegation
            panel._previewData = {
                filepath: preview.filepath,
                filename: preview.filename
            };

            // Set up open button
            const openBtn = document.getElementById('pf-open-doc-btn');
            console.log('[TWR Portfolio] Open button found:', !!openBtn, 'filepath:', preview.filepath);
            if (openBtn) {
                // Remove any existing handlers first
                openBtn.onclick = null;
                openBtn.onclick = () => {
                    console.log('[TWR Portfolio] Open button clicked!');
                    openDocument(preview.filepath, preview.filename);
                };
            }

        } catch (error) {
            console.error('[TWR Portfolio] Error loading preview:', error);
            content.innerHTML = `<div class="pf-error">Failed to load preview: ${error.message}</div>`;
        }
    }

    function renderPreview(preview) {
        const content = document.getElementById('pf-preview-content');
        if (!content) return;

        const severityBars = Object.entries(preview.by_severity || {}).map(([sev, count]) => `
            <div class="pf-preview-bar">
                <span class="pf-preview-bar-label">${sev}</span>
                <div class="pf-preview-bar-track">
                    <div class="pf-preview-bar-fill pf-severity-${sev.toLowerCase()}" style="width: ${Math.min(count * 20, 100)}%"></div>
                </div>
                <span class="pf-preview-bar-value">${count}</span>
            </div>
        `).join('');

        content.innerHTML = `
            <div class="pf-preview-doc">
                <div class="pf-preview-score pf-grade-bg-${preview.grade_color}">
                    <span class="pf-preview-score-value">${preview.score}%</span>
                    <span class="pf-preview-score-grade">${preview.grade}</span>
                </div>
                <h3 class="pf-preview-title">${escapeHtml(preview.filename)}</h3>
                <div class="pf-preview-stats">
                    <div class="pf-preview-stat">
                        <i data-lucide="alert-circle"></i>
                        <span>${preview.issue_count} issues</span>
                    </div>
                    <div class="pf-preview-stat">
                        <i data-lucide="type"></i>
                        <span>${formatWordCount(preview.word_count)} words</span>
                    </div>
                </div>
            </div>
            <div class="pf-preview-section">
                <h4>Issues by Severity</h4>
                <div class="pf-preview-bars">
                    ${severityBars || '<span class="pf-preview-empty">No issues found</span>'}
                </div>
            </div>
            <div class="pf-preview-section">
                <h4>Top Issues</h4>
                <div class="pf-preview-issues">
                    ${(preview.top_issues || []).map(issue => `
                        <div class="pf-preview-issue">
                            <span class="pf-issue-severity pf-severity-${issue.severity.toLowerCase()}">${issue.severity}</span>
                            <span class="pf-issue-text">${escapeHtml(issue.message)}</span>
                        </div>
                    `).join('') || '<span class="pf-preview-empty">No issues to show</span>'}
                </div>
            </div>
            <div class="pf-preview-section">
                <h4>Text Preview</h4>
                <div class="pf-preview-text">${escapeHtml(preview.full_text_preview || 'No preview available')}</div>
            </div>
        `;

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons(), 50);
        }
    }

    function closePreview() {
        state.selectedDocument = null;
        const panel = document.getElementById('pf-preview-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    async function openDocument(filepath, filename) {
        console.log('[TWR Portfolio] openDocument called:', { filepath, filename });

        // Close portfolio
        close();

        // Show loading toast
        if (window.showToast) {
            window.showToast('Loading document...', 'info');
        }

        try {
            // Get CSRF token from various sources
            const csrfToken = window.CSRF_TOKEN ||
                              (window.State && window.State.csrfToken) ||
                              document.querySelector('meta[name="csrf-token"]')?.content ||
                              '';

            console.log('[TWR Portfolio] Fetching /api/review/single with:', { filepath, filename, hasToken: !!csrfToken });
            const response = await fetch('/api/review/single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ filepath, filename })
            });

            console.log('[TWR Portfolio] Response status:', response.status);
            const result = await response.json();
            console.log('[TWR Portfolio] Response result:', result);

            if (!result.success) {
                throw new Error(result.error?.message || result.error || 'Failed to load document');
            }

            // Update state with results
            const results = result.data;
            if (window.State) {
                window.State.currentFile = filepath;
                window.State.originalFilename = filename;
                window.State.filename = filename;
                window.State.fileType = filename?.split('.').pop()?.toLowerCase() || '';
                window.State.reviewResults = results;
                window.State.issues = results.issues || [];
                window.State.fullText = results.full_text || '';
            }

            // Update UI using the correct rendering functions
            console.log('[TWR Portfolio] Rendering results with', results.issues?.length || 0, 'issues');

            // Update document title and info in header
            if (typeof window.updateDocumentInfo === 'function') {
                window.updateDocumentInfo({
                    filename: filename,
                    file_type: filename?.split('.').pop()?.toLowerCase() || '',
                    word_count: results.word_count || 0,
                    paragraph_count: results.paragraph_count || 0,
                    table_count: results.table_count || 0,
                    heading_count: results.heading_count || 0
                });
            }

            // Update results UI (score, grade, stats)
            if (typeof window.updateResultsUI === 'function') {
                window.updateResultsUI(results);
            }

            // Update severity counts in sidebar
            if (typeof window.updateSeverityCounts === 'function') {
                window.updateSeverityCounts(results.by_severity || {});
            }

            // Update category filters
            if (typeof window.updateCategoryFilters === 'function') {
                window.updateCategoryFilters(results.by_category || {});
            }

            // Enable all severity filters so issues are visible
            document.querySelectorAll('#unified-severity-toggles .sev-toggle').forEach(btn => {
                btn.classList.add('active');
            });
            // Also enable sidebar severity filters
            document.querySelectorAll('.sidebar .sev-toggle, .severity-filter-btn').forEach(btn => {
                btn.classList.add('active');
            });
            // Apply the filter changes
            if (typeof window.applyUnifiedFilters === 'function') {
                window.applyUnifiedFilters();
            }

            // Render the issues list
            if (typeof window.renderIssuesList === 'function') {
                window.renderIssuesList();
            } else if (window.TWR?.Renderers?.renderIssuesList) {
                window.TWR.Renderers.renderIssuesList();
            }

            // Show the issues container
            const issuesContainer = document.getElementById('issues-container');
            if (issuesContainer) {
                issuesContainer.style.display = '';
            }

            // Hide empty state and show stats bar (critical for document display)
            const emptyState = document.getElementById('empty-state');
            if (emptyState) {
                emptyState.style.display = 'none';
            }
            const statsBar = document.getElementById('stats-bar');
            if (statsBar) {
                statsBar.style.display = '';
            }

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

            if (window.showToast) {
                window.showToast(`Loaded: ${filename}`, 'success');
            }

            console.log('[TWR Portfolio] Document loaded successfully');

        } catch (error) {
            console.error('[TWR Portfolio] Error opening document:', error);
            if (window.showToast) {
                window.showToast('Failed to load document: ' + error.message, 'error');
            }
        }
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

    function toggleViewMode() {
        state.viewMode = state.viewMode === 'grid' ? 'list' : 'grid';
        const mainEl = document.querySelector('.pf-main');
        if (mainEl) {
            mainEl.classList.toggle('pf-list-view', state.viewMode === 'list');
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;');
    }

    function formatWordCount(count) {
        if (!count) return '0';
        if (count >= 1000) {
            return (count / 1000).toFixed(1) + 'k';
        }
        return count.toString();
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        init,
        open,
        close,
        expandBatch,
        closeBatchExpand,
        selectDocument,
        closePreview
    };

})();

// Initialize when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', Portfolio.init);
} else {
    Portfolio.init();
}

console.log('[TWR Portfolio] Module loaded v3.0.114');
