/**
 * AEGIS Standalone Landing Page
 * v4.5.1: Premium full-page landing with animated particle background,
 * dynamic metric tiles, tool grid with drill-downs, and glass-morphism design.
 */
window.TWR = window.TWR || {};
TWR.LandingPage = (function() {
    'use strict';

    // ── Tool definitions ────────────────────────────────────
    const TOOLS = [
        {
            id: 'review',
            name: 'Document Review',
            desc: 'Analyze documents for quality, grammar, compliance, and technical writing standards',
            icon: 'file-search',
            iconClass: 'lp-ic-review',
            color: '#3b82f6',
            navId: null, // special: opens file dialog
            metricKey: 'totalScans',
            metricLabel: 'scans'
        },
        {
            id: 'forge',
            name: 'Statement Forge',
            desc: 'Extract, categorize, and manage requirement statements from technical documents',
            icon: 'hammer',
            iconClass: 'lp-ic-forge',
            color: '#a855f7',
            navId: 'forge',
            metricKey: 'totalStatements',
            metricLabel: 'statements'
        },
        {
            id: 'roles',
            name: 'Roles Studio',
            desc: 'Manage role dictionaries, adjudication workflows, and inheritance maps',
            icon: 'users',
            iconClass: 'lp-ic-roles',
            color: '#D6A84A',
            navId: 'roles',
            metricKey: 'totalRoles',
            metricLabel: 'roles'
        },
        {
            id: 'metrics',
            name: 'Metrics & Analytics',
            desc: 'View quality scores, grade distributions, issue breakdowns, and trend analysis',
            icon: 'bar-chart-2',
            iconClass: 'lp-ic-metrics',
            color: '#10b981',
            navId: 'metrics',
            metricKey: 'avgScore',
            metricLabel: 'avg score'
        },
        {
            id: 'history',
            name: 'Scan History',
            desc: 'Browse past document scans, compare results, and track quality trends over time',
            icon: 'history',
            iconClass: 'lp-ic-history',
            color: '#22c55e',
            navId: 'history',
            metricKey: 'totalScans',
            metricLabel: 'scans'
        },
        {
            id: 'compare',
            name: 'Document Compare',
            desc: 'Compare two document versions side by side with diff highlighting and change tracking',
            icon: 'git-compare',
            iconClass: 'lp-ic-compare',
            color: '#ec4899',
            navId: 'compare',
            metricKey: null,
            metricLabel: null
        },
        {
            id: 'links',
            name: 'Link Validator',
            desc: 'Validate hyperlinks across documents with batch checking and health reports',
            icon: 'link-2',
            iconClass: 'lp-ic-links',
            color: '#14b8a6',
            navId: 'hyperlink-validator',
            metricKey: null,
            metricLabel: null
        },
        {
            id: 'portfolio',
            name: 'Portfolio',
            desc: 'Tile-based overview of all scanned documents with quick filters and sorting',
            icon: 'layout-grid',
            iconClass: 'lp-ic-portfolio',
            color: '#06b6d4',
            navId: 'portfolio',
            metricKey: 'totalDocs',
            metricLabel: 'documents'
        },
        {
            id: 'mass-review',
            name: 'Statement Review',
            desc: 'Review all role statements in one place — filter, flag, bulk approve or reject across all roles',
            icon: 'list-checks',
            iconClass: 'lp-ic-mass-review',
            color: '#f97316',
            navId: 'mass-review',
            metricKey: null,
            metricLabel: null
        },
        {
            id: 'sow',
            name: 'SOW Generator',
            desc: 'Generate Statement of Work documents from extracted requirements, roles, and compliance data',
            icon: 'scroll-text',
            iconClass: 'lp-ic-sow',
            color: '#D6A84A',
            navId: null, // special: opens SOW modal
            metricKey: null,
            metricLabel: null
        }
    ];

    // ── State ───────────────────────────────────────────────
    let animFrameId = null;
    let particles = [];
    let canvas = null;
    let ctx = null;
    let data = {
        totalScans: 0,
        totalDocs: 0,
        totalRoles: 0,
        totalStatements: 0,
        avgScore: 0,
        checkerCount: 84,  // v4.7.0: default to known count, updated from /api/version if available
        recentScans: [],
        adjudicated: 0,
        deliverable: 0,
        nlpEngines: [],
        extractors: []
    };
    let initialized = false;
    let openDrillDown = null;

    // ── Public API ──────────────────────────────────────────

    async function init() {
        if (initialized) return;
        initialized = true;

        await fetchData();
        render();
        wireEvents();
        initParticles();
    }

    async function show() {
        document.body.classList.add('landing-active');
        const page = document.getElementById('aegis-landing-page');
        if (page) page.classList.remove('lp-exiting');
        if (!initialized) {
            await init();
        } else {
            // Refresh data on re-show
            fetchData().then(() => updateMetrics());
        }
        // Canvas may have 0 dimensions from when page was display:none — resize first
        resizeCanvas();
        if (!animFrameId) startParticleLoop();
    }

    function hide(callback) {
        const page = document.getElementById('aegis-landing-page');
        if (page) {
            page.classList.add('lp-exiting');
            setTimeout(() => {
                document.body.classList.remove('landing-active');
                page.classList.remove('lp-exiting');
                // v4.7.1: Particles now run globally — don't stop on hide
                if (callback) callback();
            }, 280);
        } else {
            document.body.classList.remove('landing-active');
            if (callback) callback();
        }
    }

    function destroy() {
        stopParticleLoop();
        initialized = false;
    }

    // ── Data Fetching ───────────────────────────────────────

    async function fetchData() {
        try {
            // v4.8.3: Single endpoint replaces 4 separate API calls
            // All landing page metrics now come from /api/metrics/landing (one DB round-trip)
            const results = await Promise.allSettled([
                fetch('/api/metrics/landing').then(r => r.json()),
                fetch('/api/extraction/capabilities').then(r => r.json())  // NLP/PDF engines (not in metrics DB)
            ]);

            const metricsResult = results[0].status === 'fulfilled' ? results[0].value : null;
            if (metricsResult?.success && metricsResult?.data) {
                const m = metricsResult.data;
                data.totalScans = m.total_scans || 0;
                data.totalDocs = m.total_docs || 0;
                data.totalRoles = m.total_roles || 0;
                data.avgScore = m.avg_score || 0;
                data.totalStatements = m.total_statements || 0;
                data.adjudicated = m.adjudicated || 0;
                data.deliverable = m.deliverable || 0;
                data.checkerCount = m.checker_count || 84;
                data.recentScans = m.recent_scans || [];
            }

            // Extraction capabilities (NLP engines + PDF extractors) — not in scan_history.db
            const capsResult = results[1].status === 'fulfilled' ? results[1].value : null;
            if (capsResult) {
                if (capsResult.nlp) {
                    data.nlpEngines = Object.entries(capsResult.nlp)
                        .filter(([, v]) => v === true)
                        .map(([k]) => k);
                }
                if (capsResult.pdf) {
                    data.extractors = Object.entries(capsResult.pdf)
                        .filter(([, v]) => v === true)
                        .map(([k]) => k);
                }
            }

            // v4.9.9: Read version from /api/version (reads fresh from root version.json)
            try {
                const vr = await fetch('/api/version');
                if (vr.ok) {
                    const vd = await vr.json();
                    if (vd.app_version) data._appVersion = vd.app_version;
                }
            } catch (_) {}
        } catch (_) {
            // Offline / no data — show zeros
        }
    }

    // ── Rendering ───────────────────────────────────────────

    function render() {
        const metricsEl = document.getElementById('lp-metrics');
        const tilesEl = document.getElementById('lp-tiles');
        const recentEl = document.getElementById('lp-recent');
        const footerEl = document.getElementById('lp-footer');
        const versionEl = document.getElementById('lp-version');

        if (metricsEl) metricsEl.innerHTML = buildMetricsHTML();
        if (tilesEl) tilesEl.innerHTML = buildTilesHTML();
        if (recentEl) recentEl.innerHTML = buildRecentHTML();
        if (footerEl) footerEl.innerHTML = buildFooterHTML();
        if (versionEl && data._appVersion) {
            // v4.7.0: All version displays pull from /api/version (single source: version.json)
            versionEl.textContent = `v${data._appVersion}`;
        }

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Animate count-up for metrics
        requestAnimationFrame(() => animateCountUp());
    }

    function buildMetricsHTML() {
        const metrics = [
            { id: 'scans', icon: 'scan-line', value: data.totalScans, label: 'Total Scans' },
            { id: 'docs', icon: 'file-stack', value: data.totalDocs, label: 'Documents' },
            { id: 'roles', icon: 'users', value: data.totalRoles, label: 'Roles Found' },
            { id: 'stmts', icon: 'list-checks', value: data.totalStatements, label: 'Statements' },
            { id: 'score', icon: 'gauge', value: data.avgScore, label: 'Avg Score' },
            { id: 'checkers', icon: 'shield-check', value: data.checkerCount, label: 'Checkers' }
        ];

        return metrics.map(m => `
            <div class="lp-metric-card" data-metric="${m.id}">
                <div class="lp-metric-icon"><i data-lucide="${m.icon}"></i></div>
                <div class="lp-metric-value" data-target="${m.value}">0</div>
                <div class="lp-metric-label">${m.label}</div>
                <div class="lp-metric-expand" id="lp-mexp-${m.id}"></div>
            </div>
        `).join('');
    }

    function buildTilesHTML() {
        return TOOLS.map(tool => {
            const metricVal = tool.metricKey ? data[tool.metricKey] : null;
            const badgeHTML = metricVal != null && tool.metricLabel
                ? `<span class="lp-tile-badge" data-drill="${tool.id}"><i data-lucide="chevron-down"></i> ${metricVal} ${tool.metricLabel}</span>`
                : '';

            return `
                <div class="lp-tile" data-tool="${tool.id}">
                    <div class="lp-tile-header">
                        <div class="lp-tile-icon ${tool.iconClass}">
                            <i data-lucide="${tool.icon}"></i>
                        </div>
                        <div class="lp-tile-info">
                            <div class="lp-tile-name">${tool.name}</div>
                        </div>
                    </div>
                    <div class="lp-tile-desc">${tool.desc}</div>
                    ${badgeHTML}
                    <div class="lp-tile-detail" id="lp-detail-${tool.id}"></div>
                </div>
            `;
        }).join('');
    }

    function buildRecentHTML() {
        if (data.recentScans.length === 0) {
            return `
                <h3 class="lp-section-title">Recent Documents</h3>
                <div class="lp-recent-empty">No documents scanned yet. Drop a file above to get started.</div>
            `;
        }

        const items = data.recentScans.map(scan => {
            const name = cleanFilename(scan.filename || '');
            const ext = name.split('.').pop().toLowerCase();
            const gradeClass = `lp-grade-${(scan.grade || 'f').toLowerCase()}`;
            const date = scan.scan_time ? formatRelativeTime(scan.scan_time) : '';
            const issues = scan.issue_count || 0;
            return `
                <div class="lp-recent-item" data-scan-id="${scan.scan_id}">
                    <div class="lp-recent-icon lp-ext-${ext}">
                        <i data-lucide="${ext === 'pdf' ? 'file-text' : 'file'}"></i>
                    </div>
                    <div class="lp-recent-info">
                        <div class="lp-recent-name">${escapeHtml(name)}</div>
                        <div class="lp-recent-meta">${date} &middot; ${issues} issues</div>
                    </div>
                    <div class="lp-recent-grade ${gradeClass}">${scan.grade || '-'}</div>
                </div>
            `;
        }).join('');

        return `
            <h3 class="lp-section-title">Recent Documents</h3>
            <div class="lp-recent-list">${items}</div>
        `;
    }

    function buildFooterHTML() {
        const extractorNames = data.extractors.length > 0
            ? data.extractors.join(', ')
            : 'Docling, mammoth, pymupdf4llm';
        const nlpCount = data.nlpEngines.length;

        return `
            <div class="lp-footer-item">
                <div class="lp-footer-dot${nlpCount > 0 ? '' : ' lp-dot-off'}"></div>
                ${nlpCount} NLP engine${nlpCount !== 1 ? 's' : ''} active
            </div>
            <div class="lp-footer-item">
                <i data-lucide="shield-check"></i>
                ${data.checkerCount} quality checkers
            </div>
            <div class="lp-footer-item">
                <i data-lucide="cpu"></i>
                Extractors: ${extractorNames}
            </div>
        `;
    }

    function updateMetrics() {
        const metricsEl = document.getElementById('lp-metrics');
        if (metricsEl) {
            metricsEl.innerHTML = buildMetricsHTML();
            if (typeof lucide !== 'undefined') lucide.createIcons();
            animateCountUp();
        }
        // Also update recent
        const recentEl = document.getElementById('lp-recent');
        if (recentEl) {
            recentEl.innerHTML = buildRecentHTML();
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    // ── Count-Up Animation ──────────────────────────────────

    function animateCountUp() {
        const cards = document.querySelectorAll('.lp-metric-value[data-target]');
        cards.forEach(el => {
            const target = parseInt(el.dataset.target, 10) || 0;
            if (target === 0) { el.textContent = '0'; return; }

            const duration = 800;
            const start = performance.now();

            function tick(now) {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                // easeOutCubic
                const eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(target * eased);
                if (progress < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        });
    }

    // ── Module Launcher (v4.6.1) ───────────────────────────

    /**
     * Open a module directly from a dashboard tile.
     *
     * v4.6.1: Windowed modules (those with their own fixed overlay modal)
     * are opened ON TOP of the dashboard — the landing page stays visible
     * behind them. Only app-embedded views (review, metrics) actually
     * hide the landing page. This ensures the user never sees the old
     * review results behind a windowed module.
     */
    function openModule(tool) {
        if (!tool) return;
        // v4.6.1: Close any open drill-down panels when opening a module
        closeAllDrillDowns();
        // v4.7.1: Particles now run globally — no stopParticleLoop() needed on module open

        // Special cases
        if (tool.id === 'sow') {
            // SOW Generator is a windowed modal — keep dashboard visible
            if (window.SowGenerator) SowGenerator.open();
            return;
        }

        if (tool.navId === null) {
            // Document Review — open file dialog (needs app visible)
            hide(() => {
                document.getElementById('file-input')?.click();
            });
            return;
        }

        // Map navId to direct module open actions
        switch (tool.navId) {
            // v4.6.1: Windowed modules — keep dashboard visible behind modal overlay
            case 'forge':
                if (typeof showModal === 'function') showModal('modal-statement-forge');
                if (window.StatementForge) {
                    setTimeout(() => {
                        window.StatementForge.updateDocumentStatus();
                        window.StatementForge.loadFromSession();
                    }, 100);
                }
                break;
            case 'roles':
                // v4.7.0-fix: Use showRolesModal override which handles modal display + data loading + overview render
                if (typeof window.showRolesModal === 'function') {
                    window.showRolesModal();
                } else if (typeof showModal === 'function') {
                    showModal('modal-roles');
                }
                break;
            case 'metrics':
                if (window.MetricsAnalytics && typeof window.MetricsAnalytics.open === 'function') {
                    window.MetricsAnalytics.open();
                } else {
                    if (typeof showToast === 'function') showToast('error', 'Metrics module not available');
                }
                break;
            case 'history':
                if (typeof showModal === 'function') showModal('modal-scan-history');
                // v4.6.2-fix: Trigger data load so Scan History table isn't empty
                if (typeof loadHistoryData === 'function') {
                    setTimeout(() => loadHistoryData(), 100);
                }
                break;

            // ── Windowed modules: keep dashboard visible, open on top ──
            case 'compare':
                if (typeof openCompareFromNav === 'function') {
                    openCompareFromNav();
                } else if (window.DocCompare && typeof window.DocCompare.open === 'function') {
                    window.DocCompare.open();
                }
                break;
            case 'hyperlink-validator':
                if (window.HyperlinkValidator && typeof window.HyperlinkValidator.open === 'function') {
                    window.HyperlinkValidator.open();
                }
                break;
            // v4.6.1: link-history removed — now accessed via button in Hyperlink Validator
            case 'portfolio':
                if (window.Portfolio && typeof window.Portfolio.open === 'function') {
                    window.Portfolio.open();
                }
                break;
            case 'mass-review':
                if (window.TWR?.MassStatementReview?.open) {
                    window.TWR.MassStatementReview.open();
                } else {
                    if (typeof showToast === 'function') showToast('error', 'Mass Statement Review module not available');
                }
                break;

            default:
                // Fallback: try clicking the hidden nav button
                hide(() => {
                    const tab = document.getElementById(`nav-${tool.navId}`);
                    if (tab) tab.click();
                });
                break;
        }
    }

    // ── Events ──────────────────────────────────────────────

    function wireEvents() {
        const page = document.getElementById('aegis-landing-page');
        if (!page) return;

        // Hero drop zone
        const hero = page.querySelector('.lp-hero');
        if (hero) {
            hero.addEventListener('click', (e) => {
                e.stopPropagation();
                hide(() => {
                    document.getElementById('file-input')?.click();
                });
            });
            hero.addEventListener('dragover', (e) => {
                e.preventDefault();
                hero.classList.add('lp-drag-over');
            });
            hero.addEventListener('dragleave', () => {
                hero.classList.remove('lp-drag-over');
            });
            hero.addEventListener('drop', (e) => {
                e.preventDefault();
                hero.classList.remove('lp-drag-over');
                if (e.dataTransfer?.files?.length) {
                    const file = e.dataTransfer.files[0];
                    hide(() => {
                        if (typeof window.handleFileSelection === 'function') {
                            window.handleFileSelection(file);
                        }
                    });
                }
            });
        }

        // Metric card clicks (expand drill-down)
        const metricsEl = page.querySelector('.lp-metrics');
        if (metricsEl) {
            metricsEl.addEventListener('click', (e) => {
                const card = e.target.closest('.lp-metric-card');
                if (!card) return;
                e.stopPropagation();
                toggleMetricExpand(card.dataset.metric);
            });
        }

        // Tile clicks (use event delegation on the tiles container)
        const tilesEl = page.querySelector('.lp-tiles');
        if (tilesEl) {
            tilesEl.addEventListener('click', (e) => {
                // Check if clicking a drill-down badge
                const badge = e.target.closest('.lp-tile-badge');
                if (badge) {
                    e.stopPropagation();
                    toggleDrillDown(badge.dataset.drill);
                    return;
                }

                const tile = e.target.closest('.lp-tile');
                if (!tile) return;
                e.stopPropagation();

                const toolId = tile.dataset.tool;
                const tool = TOOLS.find(t => t.id === toolId);
                if (!tool) return;

                // v4.6.1: Open modules directly from dashboard tiles
                openModule(tool);
            });
        }

        // Recent item clicks — open scan history directly
        const recentEl = page.querySelector('.lp-recent');
        if (recentEl) {
            recentEl.addEventListener('click', (e) => {
                const item = e.target.closest('.lp-recent-item');
                if (!item) return;
                e.stopPropagation();
                // v4.6.1: Keep dashboard visible behind modal
                if (typeof showModal === 'function') showModal('modal-scan-history');
            });
        }

        // v4.6.2-fix: Theme toggle button on landing page
        const themeBtn = document.getElementById('lp-btn-theme');
        if (themeBtn) {
            themeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof toggleTheme === 'function') {
                    toggleTheme();
                } else {
                    document.body.classList.toggle('dark-mode');
                    const isDark = document.body.classList.contains('dark-mode');
                    localStorage.setItem('twr-theme', isDark ? 'dark' : 'light');
                }
                // Re-pick particle colors for the new theme
                particles.forEach(p => { p.color = pickParticleColor(); });
            });
        }

        // v4.6.1: Header action buttons (Help & Settings)
        const helpBtn = document.getElementById('lp-btn-help');
        if (helpBtn) {
            helpBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (window.showModal) {
                    window.showModal('modal-help');
                } else if (window.TWR?.Modals?.showModal) {
                    TWR.Modals.showModal('modal-help');
                }
            });
        }
        const settingsBtn = document.getElementById('lp-btn-settings');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (window.showModal) {
                    window.showModal('modal-settings');
                } else if (window.TWR?.Modals?.showModal) {
                    TWR.Modals.showModal('modal-settings');
                }
            });
        }

        // v4.6.1: Click anywhere on the landing page (outside tiles/badges) to close open drill-downs
        page.addEventListener('click', (e) => {
            // Don't close if clicking inside a tile or badge (those have their own handlers with stopPropagation)
            if (e.target.closest('.lp-tile') || e.target.closest('.lp-tile-badge') || e.target.closest('.lp-metric-card')) return;
            closeAllDrillDowns();
        });
    }

    // ── Drill-Down ──────────────────────────────────────────

    function closeAllDrillDowns() {
        if (openDrillDown) {
            const prev = document.getElementById(`lp-detail-${openDrillDown}`);
            if (prev) prev.classList.remove('lp-detail-open');
            openDrillDown = null;
        }
        if (openMetricId) {
            const prev = document.getElementById(`lp-mexp-${openMetricId}`);
            if (prev) {
                prev.classList.remove('lp-mexp-open');
                const card = prev.closest('.lp-metric-card');
                if (card) card.style.gridColumn = '';
            }
            openMetricId = null;
        }
    }

    function toggleDrillDown(toolId) {
        const detailEl = document.getElementById(`lp-detail-${toolId}`);
        if (!detailEl) return;

        if (openDrillDown && openDrillDown !== toolId) {
            // Close previously open drill-down
            const prev = document.getElementById(`lp-detail-${openDrillDown}`);
            if (prev) prev.classList.remove('lp-detail-open');
        }

        const isOpen = detailEl.classList.contains('lp-detail-open');
        if (isOpen) {
            detailEl.classList.remove('lp-detail-open');
            openDrillDown = null;
        } else {
            detailEl.innerHTML = buildDrillDownContent(toolId);
            detailEl.classList.add('lp-detail-open');
            openDrillDown = toolId;
        }
    }

    function buildDrillDownContent(toolId) {
        switch (toolId) {
            case 'review': {
                const grades = {};
                data.recentScans.forEach(s => {
                    const g = (s.grade || 'F').toUpperCase();
                    grades[g] = (grades[g] || 0) + 1;
                });
                const gradeRows = Object.entries(grades).map(([g, c]) =>
                    `<div class="lp-detail-row"><span class="lp-detail-label">Grade ${g}</span><span class="lp-detail-value">${c}</span></div>`
                ).join('') || '<div class="lp-detail-row"><span class="lp-detail-label">No scans yet</span></div>';
                return `<div class="lp-detail-row"><span class="lp-detail-label">Total Scans</span><span class="lp-detail-value">${data.totalScans}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Avg Score</span><span class="lp-detail-value">${data.avgScore}</span></div>
                    ${gradeRows}`;
            }
            case 'forge':
                return `<div class="lp-detail-row"><span class="lp-detail-label">Total Statements</span><span class="lp-detail-value">${data.totalStatements}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Documents with Statements</span><span class="lp-detail-value">${data.totalDocs}</span></div>`;
            case 'roles':
                return `<div class="lp-detail-row"><span class="lp-detail-label">Total Roles</span><span class="lp-detail-value">${data.totalRoles}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Adjudicated</span><span class="lp-detail-value">${data.adjudicated}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Deliverable</span><span class="lp-detail-value">${data.deliverable}</span></div>`;
            case 'metrics':
                return `<div class="lp-detail-row"><span class="lp-detail-label">Average Score</span><span class="lp-detail-value">${data.avgScore}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Documents Scored</span><span class="lp-detail-value">${data.totalDocs}</span></div>`;
            case 'history':
                return `<div class="lp-detail-row"><span class="lp-detail-label">Total Scans</span><span class="lp-detail-value">${data.totalScans}</span></div>
                    <div class="lp-detail-row"><span class="lp-detail-label">Unique Documents</span><span class="lp-detail-value">${data.totalDocs}</span></div>`;
            case 'portfolio':
                return `<div class="lp-detail-row"><span class="lp-detail-label">Documents in Portfolio</span><span class="lp-detail-value">${data.totalDocs}</span></div>`;
            default:
                return '<div class="lp-detail-row"><span class="lp-detail-label">Navigate to explore</span></div>';
        }
    }

    // ── Metric Card Drill-Down ─────────────────────────────

    let openMetricId = null;

    function toggleMetricExpand(metricId) {
        // Close any previously open metric expand
        if (openMetricId && openMetricId !== metricId) {
            const prev = document.getElementById(`lp-mexp-${openMetricId}`);
            if (prev) {
                prev.classList.remove('lp-mexp-open');
                const prevCard = prev.closest('.lp-metric-card');
                if (prevCard) prevCard.classList.remove('lp-metric-expanded');
            }
        }

        const expandEl = document.getElementById(`lp-mexp-${metricId}`);
        if (!expandEl) return;
        const card = expandEl.closest('.lp-metric-card');

        if (expandEl.classList.contains('lp-mexp-open')) {
            expandEl.classList.remove('lp-mexp-open');
            if (card) card.classList.remove('lp-metric-expanded');
            openMetricId = null;
        } else {
            expandEl.innerHTML = buildMetricExpandContent(metricId);
            expandEl.classList.add('lp-mexp-open');
            if (card) card.classList.add('lp-metric-expanded');
            openMetricId = metricId;
            // Draw any canvas visualizations after DOM update
            requestAnimationFrame(() => drawMetricViz(metricId, expandEl));
        }
    }

    function buildMetricExpandContent(id) {
        switch (id) {
            case 'scans': return buildScansExpand();
            case 'docs': return buildDocsExpand();
            case 'roles': return buildRolesExpand();
            case 'stmts': return buildStmtsExpand();
            case 'score': return buildScoreExpand();
            case 'checkers': return buildCheckersExpand();
            default: return '';
        }
    }

    function buildScansExpand() {
        // Grade distribution + recent activity sparkline
        const grades = { A: 0, B: 0, C: 0, D: 0, F: 0 };
        const allScans = data.recentScans.length > 0 ? data.recentScans : [];
        // Use all scans data for grade counts (we have totalScans but only 5 recents)
        allScans.forEach(s => {
            const g = (s.grade || 'F').toUpperCase();
            if (grades[g] !== undefined) grades[g]++;
        });

        const gradeColors = { A: '#22c55e', B: '#84cc16', C: '#eab308', D: '#f97316', F: '#ef4444' };
        const gradeBars = Object.entries(grades).map(([g, count]) =>
            `<div class="lp-mexp-bar-row">
                <span class="lp-mexp-bar-label">${g}</span>
                <div class="lp-mexp-bar-track">
                    <div class="lp-mexp-bar-fill" style="width:${data.totalScans > 0 ? Math.round((count / Math.max(data.totalScans, 1)) * 100) : 0}%;background:${gradeColors[g]}"></div>
                </div>
                <span class="lp-mexp-bar-count">${count}</span>
            </div>`
        ).join('');

        return `
            <div class="lp-mexp-title">Grade Distribution (Recent)</div>
            ${gradeBars}
            <canvas id="lp-viz-scans" class="lp-mexp-canvas" width="200" height="48"></canvas>
        `;
    }

    function buildDocsExpand() {
        // File type breakdown + most-scanned docs
        const types = {};
        const fileCounts = {};
        data.recentScans.forEach(s => {
            const name = cleanFilename(s.filename || '');
            const ext = name.split('.').pop().toLowerCase();
            types[ext] = (types[ext] || 0) + 1;
            fileCounts[name] = (fileCounts[name] || 0) + 1;
        });

        const typeHTML = Object.entries(types)
            .sort((a, b) => b[1] - a[1])
            .map(([ext, n]) =>
                `<span class="lp-mexp-chip lp-mexp-chip-${ext}">.${ext} <b>${n}</b></span>`
            ).join('');

        const topDocs = Object.entries(fileCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([name, n]) =>
                `<div class="lp-mexp-doc-row"><span class="lp-mexp-doc-name">${escapeHtml(name.length > 28 ? name.slice(0, 28) + '...' : name)}</span><span class="lp-mexp-bar-count">${n}x</span></div>`
            ).join('');

        return `
            <div class="lp-mexp-title">File Types</div>
            <div class="lp-mexp-chips">${typeHTML || '<span class="lp-mexp-none">No data</span>'}</div>
            ${topDocs ? `<div class="lp-mexp-title" style="margin-top:8px">Most Scanned</div>${topDocs}` : ''}
        `;
    }

    function buildRolesExpand() {
        // Adjudication ring + stats
        const pending = data.totalRoles - data.adjudicated;
        return `
            <div class="lp-mexp-ring-row">
                <canvas id="lp-viz-roles" class="lp-mexp-ring" width="56" height="56"></canvas>
                <div class="lp-mexp-ring-stats">
                    <div class="lp-mexp-ring-stat"><span style="color:#22c55e">${data.adjudicated}</span> adjudicated</div>
                    <div class="lp-mexp-ring-stat"><span style="color:#eab308">${pending}</span> pending</div>
                    <div class="lp-mexp-ring-stat"><span style="color:#D6A84A">${data.deliverable}</span> deliverable</div>
                </div>
            </div>
        `;
    }

    function buildStmtsExpand() {
        // Avg per doc + directive hints
        const avgPerDoc = data.totalDocs > 0 ? Math.round(data.totalStatements / data.totalDocs) : 0;
        return `
            <div class="lp-mexp-stat-grid">
                <div class="lp-mexp-stat-cell">
                    <div class="lp-mexp-stat-val">${avgPerDoc}</div>
                    <div class="lp-mexp-stat-lbl">Avg / Doc</div>
                </div>
                <div class="lp-mexp-stat-cell">
                    <div class="lp-mexp-stat-val">${data.totalDocs}</div>
                    <div class="lp-mexp-stat-lbl">Documents</div>
                </div>
            </div>
            <canvas id="lp-viz-stmts" class="lp-mexp-canvas" width="200" height="48"></canvas>
        `;
    }

    function buildScoreExpand() {
        // Score histogram + best/worst
        const scores = data.recentScans
            .filter(s => s.score != null && s.score !== 'N/A')
            .map(s => ({ score: parseFloat(s.score), name: cleanFilename(s.filename || '') }));

        const best = scores.length > 0 ? scores.reduce((a, b) => a.score > b.score ? a : b) : null;
        const worst = scores.length > 0 ? scores.reduce((a, b) => a.score < b.score ? a : b) : null;

        let bwHTML = '';
        if (best && worst && best.name !== worst.name) {
            bwHTML = `
                <div class="lp-mexp-bw-row"><span class="lp-mexp-bw-label" style="color:#22c55e">Best</span><span class="lp-mexp-bw-name">${escapeHtml(best.name.length > 20 ? best.name.slice(0, 20) + '...' : best.name)}</span><span class="lp-mexp-bw-val">${best.score}</span></div>
                <div class="lp-mexp-bw-row"><span class="lp-mexp-bw-label" style="color:#ef4444">Worst</span><span class="lp-mexp-bw-name">${escapeHtml(worst.name.length > 20 ? worst.name.slice(0, 20) + '...' : worst.name)}</span><span class="lp-mexp-bw-val">${worst.score}</span></div>
            `;
        }
        return `
            <canvas id="lp-viz-score" class="lp-mexp-canvas" width="200" height="48"></canvas>
            ${bwHTML}
        `;
    }

    function buildCheckersExpand() {
        // Checker categories
        const categories = [
            { name: 'Grammar & Style', count: 18, color: '#3b82f6' },
            { name: 'Technical Writing', count: 14, color: '#a855f7' },
            { name: 'Compliance', count: 12, color: '#D6A84A' },
            { name: 'Requirements', count: 10, color: '#22c55e' },
            { name: 'Spelling & Language', count: 8, color: '#14b8a6' },
            { name: 'Structure & Format', count: 12, color: '#ec4899' },
            { name: 'NLP-Enhanced', count: 10, color: '#f97316' }
        ];

        return categories.map(c =>
            `<div class="lp-mexp-bar-row">
                <span class="lp-mexp-bar-label" style="flex:1">${c.name}</span>
                <div class="lp-mexp-bar-track" style="flex:1">
                    <div class="lp-mexp-bar-fill" style="width:${Math.round(c.count / 20 * 100)}%;background:${c.color}"></div>
                </div>
                <span class="lp-mexp-bar-count">${c.count}</span>
            </div>`
        ).join('');
    }

    // ── Metric Visualizations (Canvas) ──────────────────────

    function drawMetricViz(metricId, container) {
        switch (metricId) {
            case 'scans': drawScansSparkline(); break;
            case 'roles': drawRolesRing(); break;
            case 'stmts': drawStmtsSparkline(); break;
            case 'score': drawScoreHistogram(); break;
        }
    }

    function drawScansSparkline() {
        const c = document.getElementById('lp-viz-scans');
        if (!c) return;
        const ctx2 = c.getContext('2d');
        const w = c.width, h = c.height;

        // Build a simple activity sparkline from recent scan dates
        const now = Date.now();
        const weekMs = 7 * 24 * 60 * 60 * 1000;
        const weeks = 8;
        const bins = new Array(weeks).fill(0);
        data.recentScans.forEach(s => {
            if (!s.scan_time) return;
            const age = now - new Date(s.scan_time).getTime();
            const weekIdx = Math.min(Math.floor(age / weekMs), weeks - 1);
            bins[weeks - 1 - weekIdx]++;
        });

        const maxBin = Math.max(...bins, 1);
        const barW = (w - 4) / weeks;
        const gold = '#D6A84A';

        ctx2.clearRect(0, 0, w, h);
        for (let i = 0; i < weeks; i++) {
            const barH = (bins[i] / maxBin) * (h - 8);
            const x = 2 + i * barW + 2;
            const y = h - 4 - barH;
            ctx2.fillStyle = i === weeks - 1 ? gold : 'rgba(214, 168, 74, 0.3)';
            ctx2.beginPath();
            ctx2.roundRect(x, y, barW - 4, barH, 2);
            ctx2.fill();
        }
    }

    function drawRolesRing() {
        const c = document.getElementById('lp-viz-roles');
        if (!c) return;
        const ctx2 = c.getContext('2d');
        const cx = 28, cy = 28, r = 22, lw = 5;

        ctx2.clearRect(0, 0, c.width, c.height);
        const total = data.totalRoles || 1;
        const adj = data.adjudicated || 0;
        const pending = total - adj;

        // Background ring
        ctx2.beginPath();
        ctx2.arc(cx, cy, r, 0, Math.PI * 2);
        ctx2.strokeStyle = 'rgba(255,255,255,0.06)';
        ctx2.lineWidth = lw;
        ctx2.stroke();

        // Adjudicated arc (green)
        if (adj > 0) {
            const adjAngle = (adj / total) * Math.PI * 2;
            ctx2.beginPath();
            ctx2.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + adjAngle);
            ctx2.strokeStyle = '#22c55e';
            ctx2.lineWidth = lw;
            ctx2.lineCap = 'round';
            ctx2.stroke();
        }

        // Center text
        ctx2.fillStyle = '#e6edf3';
        ctx2.font = 'bold 12px -apple-system, sans-serif';
        ctx2.textAlign = 'center';
        ctx2.textBaseline = 'middle';
        ctx2.fillText(`${Math.round((adj / total) * 100)}%`, cx, cy);
    }

    function drawStmtsSparkline() {
        const c = document.getElementById('lp-viz-stmts');
        if (!c) return;
        const ctx2 = c.getContext('2d');
        const w = c.width, h = c.height;

        // Statement counts per recent scan
        const counts = data.recentScans.map(s => s.statement_count || s.stmt_count || 0).reverse();
        if (counts.length === 0) return;

        const maxCount = Math.max(...counts, 1);
        ctx2.clearRect(0, 0, w, h);

        // Draw filled area sparkline
        const stepX = counts.length > 1 ? (w - 8) / (counts.length - 1) : w / 2;
        ctx2.beginPath();
        ctx2.moveTo(4, h - 4);
        counts.forEach((v, i) => {
            const x = 4 + i * stepX;
            const y = h - 4 - (v / maxCount) * (h - 12);
            if (i === 0) ctx2.lineTo(x, y);
            else ctx2.lineTo(x, y);
        });
        ctx2.lineTo(4 + (counts.length - 1) * stepX, h - 4);
        ctx2.closePath();
        ctx2.fillStyle = 'rgba(168, 85, 247, 0.15)';
        ctx2.fill();

        // Draw line
        ctx2.beginPath();
        counts.forEach((v, i) => {
            const x = 4 + i * stepX;
            const y = h - 4 - (v / maxCount) * (h - 12);
            if (i === 0) ctx2.moveTo(x, y);
            else ctx2.lineTo(x, y);
        });
        ctx2.strokeStyle = '#a855f7';
        ctx2.lineWidth = 1.5;
        ctx2.stroke();

        // Draw dots
        counts.forEach((v, i) => {
            const x = 4 + i * stepX;
            const y = h - 4 - (v / maxCount) * (h - 12);
            ctx2.beginPath();
            ctx2.arc(x, y, 2.5, 0, Math.PI * 2);
            ctx2.fillStyle = i === counts.length - 1 ? '#a855f7' : 'rgba(168, 85, 247, 0.4)';
            ctx2.fill();
        });
    }

    function drawScoreHistogram() {
        const c = document.getElementById('lp-viz-score');
        if (!c) return;
        const ctx2 = c.getContext('2d');
        const w = c.width, h = c.height;

        const scores = data.recentScans
            .filter(s => s.score != null && s.score !== 'N/A')
            .map(s => parseFloat(s.score));

        if (scores.length === 0) return;

        // Bucket into 5 bins: 0-20, 20-40, 40-60, 60-80, 80-100
        const bins = [0, 0, 0, 0, 0];
        const binColors = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e'];
        scores.forEach(s => {
            const idx = Math.min(Math.floor(s / 20), 4);
            bins[idx]++;
        });

        const maxBin = Math.max(...bins, 1);
        const barW = (w - 4) / 5;

        ctx2.clearRect(0, 0, w, h);
        for (let i = 0; i < 5; i++) {
            const barH = (bins[i] / maxBin) * (h - 8);
            const x = 2 + i * barW + 2;
            const y = h - 4 - barH;
            ctx2.fillStyle = bins[i] > 0 ? binColors[i] : 'rgba(255,255,255,0.04)';
            ctx2.beginPath();
            ctx2.roundRect(x, y, barW - 4, Math.max(barH, 2), 2);
            ctx2.fill();
        }
    }

    // ── Particle Animation ──────────────────────────────────

    function initParticles() {
        canvas = document.getElementById('lp-bg-canvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d');

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Create particles — v4.7.0: more particles, faster movement
        const count = Math.min(120, Math.floor((canvas.width * canvas.height) / 10000));
        particles = [];
        const isDark = document.body.classList.contains('dark-mode');
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.7,
                vy: (Math.random() - 0.5) * 0.7,
                r: isDark ? 1 + Math.random() * 1.5 : 1.5 + Math.random() * 2,
                alpha: isDark ? 0.2 + Math.random() * 0.4 : 0.4 + Math.random() * 0.4,
                // Gold/amber palette — stronger in light mode
                color: pickParticleColor()
            });
        }

        startParticleLoop();
    }

    function pickParticleColor() {
        // v4.7.0: Visible particles in both modes — gold/amber palette
        const isDark = document.body.classList.contains('dark-mode');
        const colors = isDark ? [
            'rgba(214, 168, 74,',   // Gold
            'rgba(184, 116, 58,',   // Amber
            'rgba(230, 237, 243,',  // White-ish
            'rgba(214, 168, 74,',   // Gold (weighted)
        ] : [
            'rgba(184, 130, 30,',   // Rich gold
            'rgba(160, 100, 20,',   // Deep amber
            'rgba(140, 90, 30,',    // Bronze
            'rgba(200, 155, 50,',   // Bright gold
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    function resizeCanvas() {
        if (!canvas) return;
        // v4.7.1: Canvas is now a direct child of body — size to viewport
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function startParticleLoop() {
        if (animFrameId) return;
        function loop() {
            drawParticles();
            animFrameId = requestAnimationFrame(loop);
        }
        animFrameId = requestAnimationFrame(loop);
    }

    function stopParticleLoop() {
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
        }
    }

    function drawParticles() {
        if (!ctx || !canvas) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const w = canvas.width;
        const h = canvas.height;
        const maxDist = 120;

        // Move and draw particles
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            // Wrap around edges
            if (p.x < -10) p.x = w + 10;
            if (p.x > w + 10) p.x = -10;
            if (p.y < -10) p.y = h + 10;
            if (p.y > h + 10) p.y = -10;

            // Draw dot
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ')';
            ctx.fill();
        }

        // Draw connecting lines between nearby particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < maxDist) {
                    const opacity = (1 - dist / maxDist) * 0.12;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    // v4.7.0: Visible connecting lines in both modes
                    const isDark = document.body.classList.contains('dark-mode');
                    ctx.strokeStyle = isDark
                        ? `rgba(214, 168, 74, ${opacity})`
                        : `rgba(160, 120, 40, ${opacity * 3.5})`;
                    ctx.lineWidth = isDark ? 0.5 : 0.8;
                    ctx.stroke();
                }
            }
        }
    }

    // ── Helpers ──────────────────────────────────────────────

    function cleanFilename(name) {
        return name.replace(/^[0-9a-f]{8}_/, '').replace(/^test_documents/, '');
    }

    function formatRelativeTime(dateStr) {
        try {
            const date = new Date(dateStr);
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);
            if (diff < 60) return 'just now';
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
            return date.toLocaleDateString();
        } catch (_) { return ''; }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Public Interface ────────────────────────────────────

    return { init, show, hide, destroy };
})();
