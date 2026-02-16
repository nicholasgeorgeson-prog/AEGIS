/**
 * AEGIS Landing Dashboard
 * v4.5.0: Tool launcher cards, recent documents, system stats.
 * Renders inside the empty-state container when no document is loaded.
 */
window.TWR = window.TWR || {};
TWR.LandingDashboard = (function() {
    'use strict';

    const TOOLS = [
        {
            id: 'review',
            name: 'Document Review',
            desc: 'Analyze documents for quality, grammar, and compliance',
            icon: 'file-search',
            iconClass: 'ld-icon-review',
            action: () => document.getElementById('file-input')?.click()
        },
        {
            id: 'forge',
            name: 'Statement Forge',
            desc: 'Extract and manage requirement statements',
            icon: 'hammer',
            iconClass: 'ld-icon-forge',
            action: () => clickTab('forge')
        },
        {
            id: 'roles',
            name: 'Roles Studio',
            desc: 'Manage role dictionaries and adjudication',
            icon: 'users',
            iconClass: 'ld-icon-roles',
            action: () => clickTab('roles')
        },
        {
            id: 'history',
            name: 'Scan History',
            desc: 'Review past document scans and trends',
            icon: 'clock',
            iconClass: 'ld-icon-history',
            action: () => clickTab('history')
        },
        {
            id: 'compare',
            name: 'Document Compare',
            desc: 'Compare two document versions side by side',
            icon: 'git-compare',
            iconClass: 'ld-icon-compare',
            action: () => clickTab('compare')
        },
        {
            id: 'links',
            name: 'Link Validator',
            desc: 'Validate hyperlinks across documents',
            icon: 'link',
            iconClass: 'ld-icon-links',
            action: () => clickTab('hyperlink-validator')
        }
    ];

    let rendered = false;

    function clickTab(navId) {
        // Main nav tabs use id="nav-forge", id="nav-roles", etc.
        const tab = document.getElementById(`nav-${navId}`);
        if (tab) tab.click();
    }

    async function render(container) {
        if (!container) return;
        rendered = true;

        // Fetch recent scans and stats
        let recentScans = [];
        let stats = { totalScans: 0, totalDocs: 0, totalRoles: 0 };

        try {
            const resp = await fetch('/api/scan-history');
            const data = await resp.json();
            if (data.success && Array.isArray(data.data)) {
                recentScans = data.data.slice(0, 5);
                stats.totalScans = data.data.length;
                stats.totalDocs = new Set(data.data.map(s => s.filename)).size;
                stats.totalRoles = data.data.reduce((sum, s) => sum + (s.role_count || 0), 0);
            }
        } catch (_) { /* offline / no history */ }

        container.innerHTML = buildDashboardHTML(recentScans, stats);

        // Wire tool card clicks
        container.querySelectorAll('.ld-tool-card').forEach(card => {
            card.addEventListener('click', (e) => {
                e.stopPropagation();
                const toolId = card.dataset.tool;
                const tool = TOOLS.find(t => t.id === toolId);
                if (tool?.action) tool.action();
            });
        });

        // Wire drop zone
        const hero = container.querySelector('.ld-hero');
        if (hero) {
            hero.addEventListener('click', (e) => {
                if (e.target.closest('.ld-hero')) {
                    document.getElementById('file-input')?.click();
                }
            });
            hero.addEventListener('dragover', (e) => { e.preventDefault(); hero.classList.add('ld-drag-over'); });
            hero.addEventListener('dragleave', () => hero.classList.remove('ld-drag-over'));
            hero.addEventListener('drop', (e) => {
                e.preventDefault();
                hero.classList.remove('ld-drag-over');
                // Pass to the existing file handler
                if (e.dataTransfer?.files?.length && typeof window.handleFileSelection === 'function') {
                    window.handleFileSelection(e.dataTransfer.files[0]);
                }
            });
        }

        // Wire recent item clicks
        container.querySelectorAll('.ld-recent-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const scanId = item.dataset.scanId;
                if (scanId) {
                    // Navigate to history tab and load scan
                    clickTab('history');
                }
            });
        });

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function buildDashboardHTML(recentScans, stats) {
        const toolCards = TOOLS.map(tool => `
            <div class="ld-tool-card" data-tool="${tool.id}">
                <div class="ld-tool-icon ${tool.iconClass}">
                    <i data-lucide="${tool.icon}"></i>
                </div>
                <div class="ld-tool-info">
                    <div class="ld-tool-name">${tool.name}</div>
                    <div class="ld-tool-desc">${tool.desc}</div>
                </div>
            </div>
        `).join('');

        const recentHTML = recentScans.length > 0
            ? recentScans.map(scan => {
                const name = cleanFilename(scan.filename);
                const ext = name.split('.').pop().toLowerCase();
                const gradeClass = `ld-grade-${(scan.grade || 'f').toLowerCase()}`;
                const date = scan.scan_time ? formatRelativeTime(scan.scan_time) : '';
                const issues = scan.issue_count || 0;
                return `
                    <div class="ld-recent-item" data-scan-id="${scan.scan_id}">
                        <div class="ld-recent-icon ld-ext-${ext}">
                            <i data-lucide="${ext === 'pdf' ? 'file-text' : 'file'}"></i>
                        </div>
                        <div class="ld-recent-info">
                            <div class="ld-recent-name">${escapeHtml(name)}</div>
                            <div class="ld-recent-meta">${date} &middot; ${issues} issues</div>
                        </div>
                        <div class="ld-recent-grade ${gradeClass}">${scan.grade || '-'}</div>
                    </div>
                `;
            }).join('')
            : '<div class="ld-recent-empty">No documents scanned yet. Drop a file above to get started.</div>';

        return `
            <div class="ld-dashboard">
                <div class="ld-hero">
                    <div class="ld-hero-icon">
                        <i data-lucide="upload"></i>
                    </div>
                    <h2>Drop a document to begin</h2>
                    <p>Drag & drop a .docx, .doc, or .pdf file, or use <kbd>Ctrl</kbd>+<kbd>O</kbd> to open</p>
                </div>

                <h3 class="ld-section-title">Tools</h3>
                <div class="ld-tools">
                    ${toolCards}
                </div>

                <h3 class="ld-section-title">Recent Documents</h3>
                <div class="ld-recent">
                    <div class="ld-recent-list">
                        ${recentHTML}
                    </div>
                </div>

                <div class="ld-stats">
                    <div class="ld-stat">
                        <div class="ld-stat-value">${stats.totalScans}</div>
                        <div class="ld-stat-label">Total Scans</div>
                    </div>
                    <div class="ld-stat">
                        <div class="ld-stat-value">${stats.totalDocs}</div>
                        <div class="ld-stat-label">Documents</div>
                    </div>
                    <div class="ld-stat">
                        <div class="ld-stat-value">${stats.totalRoles}</div>
                        <div class="ld-stat-label">Roles Found</div>
                    </div>
                </div>
            </div>
        `;
    }

    function cleanFilename(name) {
        // Remove temp prefixes like "175afe87_"
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

    function isRendered() { return rendered; }

    function destroy() {
        rendered = false;
    }

    return { render, destroy, isRendered };
})();
