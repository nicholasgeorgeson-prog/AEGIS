/**
 * AEGIS Proposal Compare Module
 * Upload 2+ proposal docs (DOCX/PDF/XLSX), extract financial data,
 * and display side-by-side comparison matrix with advanced analytics.
 *
 * Pure extraction — NO AI/LLM. Displays only what's found in documents.
 *
 * Features:
 *   - Project management (create/select/add proposals)
 *   - Upload, extract, review, compare workflow
 *   - 8 result tabs: Executive Summary, Comparison, Categories, Red Flags,
 *     Heatmap, Vendor Scores, Details, Raw Tables
 *   - Chart.js integration (optional, degrades gracefully)
 *   - Export to XLSX
 *
 * @version 2.0.0
 */

window.ProposalCompare = (function() {
    'use strict';

    // ──────────────────────────────────────────
    // State
    // ──────────────────────────────────────────

    const State = {
        phase: 'upload',       // 'upload' | 'extracting' | 'review' | 'comparing' | 'results'
        files: [],             // File objects
        proposals: [],         // Extracted ProposalData objects (from server)
        comparison: null,      // ComparisonResult from server
        comparisonId: null,    // DB id of saved comparison (for history)
        activeTab: 'executive', // active tab id
        // Project management
        projects: [],          // cached project list
        selectedProjectId: null,
        projectProposals: [],  // proposals already in selected project
        // Review phase navigation
        _reviewIdx: 0,         // current proposal index in review split-pane
        _blobUrls: [],         // blob URLs for document viewer (cleaned up on phase exit)
        _lineItemEditorOpen: [], // track which proposals have line item editor open
        // Chart instances (for cleanup)
        _charts: [],
        // Click-to-populate: last focused form field
        _lastFocusedField: null,
        // Dashboard state
        dashboardProject: null,
        dashboardComparisons: [],
        // Multi-term comparison (v5.9.46)
        multiTermMode: false,              // true when comparing proposals grouped by contract term
        multiTermResults: [],              // [{termLabel, comparison, comparisonId, proposals}, ...]
        multiTermActiveIdx: 0,             // index of currently displayed term group
        multiTermExcluded: [],             // proposals excluded (single vendor in a term group)
        // v5.9.53: Proposal selection for targeted comparison
        _selectedForCompare: new Set(),    // indices of proposals selected for comparison
        _selectMode: false,                // true when user is picking proposals to compare
        // v5.9.53: Line item undo stack (per-proposal)
        _undoStacks: {},                   // { proposalIdx: [{action, data, rowIdx}] }
        _redoStacks: {},                   // { proposalIdx: [{action, data, rowIdx}] }
        // v5.9.53: Expanded description tracking
        _expandedDescs: new Set(),         // set of "proposalIdx-liIdx" keys for expanded descriptions
    };

    // CSRF token
    function getCSRF() {
        return document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
    }

    // ──────────────────────────────────────────
    // Modal management
    // ──────────────────────────────────────────

    function open() {
        const modal = document.getElementById('pc-modal');
        if (!modal) {
            console.error('[AEGIS ProposalCompare] Modal #pc-modal not found');
            return;
        }
        modal.classList.add('active');
        // v5.9.40: Force z-index above landing page tiles (belt-and-suspenders with CSS)
        modal.style.zIndex = '15000';
        document.body.classList.add('modal-open');
        reset();
        renderUploadPhase();
        if (window.lucide) window.lucide.createIcons();
    }

    // v5.9.53: Open directly to a project's detail view (called from landing page)
    function openProject(projectId) {
        const modal = document.getElementById('pc-modal');
        if (!modal) return;
        modal.classList.add('active');
        modal.style.zIndex = '15000';
        document.body.classList.add('modal-open');
        State.selectedProjectId = projectId;
        State.dashboardProject = projectId;
        renderProjectDetail(projectId);
        if (window.lucide) window.lucide.createIcons();
    }

    // v5.9.53: Open project and auto-load latest comparison results
    async function openProjectWithResults(projectId) {
        const modal = document.getElementById('pc-modal');
        if (!modal) return;
        modal.classList.add('active');
        modal.style.zIndex = '15000';
        document.body.classList.add('modal-open');
        State.selectedProjectId = projectId;
        State.dashboardProject = projectId;

        // Show loading in body
        var body = document.getElementById('pc-body');
        if (body) {
            body.innerHTML = '<div class="pc-loading" style="padding:60px 0;text-align:center">' +
                '<div class="pc-spinner"></div> Loading project financial analysis...' +
                '</div>';
        }

        // Fetch latest comparison for this project
        try {
            var compsResp = await fetch('/api/proposal-compare/projects/' + projectId + '/comparisons', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var compsData = await compsResp.json();
            var comps = (compsData.success && compsData.data) ? compsData.data : [];

            if (comps.length > 0) {
                // Load the most recent comparison
                await _loadHistoryItem(comps[0].id);
            } else {
                // No comparisons yet — fall back to project detail view
                renderProjectDetail(projectId);
            }
        } catch (e) {
            console.error('[AEGIS ProposalCompare] openProjectWithResults error:', e);
            renderProjectDetail(projectId);
        }
        if (window.lucide) window.lucide.createIcons();
    }

    function close() {
        const modal = document.getElementById('pc-modal');
        if (modal) modal.classList.remove('active');
        document.body.classList.remove('modal-open');
        destroyCharts();
    }

    function reset() {
        State.phase = 'upload';
        State.files = [];
        State.proposals = [];
        State.comparison = null;
        State.activeTab = 'executive';
        State.selectedProjectId = null;
        State.projectProposals = [];
        destroyCharts();
    }

    function destroyCharts() {
        if (State._charts) {
            State._charts.forEach(c => { try { c.destroy(); } catch(e) {} });
        }
        State._charts = [];
    }

    // ──────────────────────────────────────────
    // Format helpers
    // ──────────────────────────────────────────

    // ── Vendor color palette (deterministic by index) ──
    var VENDOR_COLORS = [
        '#D6A84A', '#2196f3', '#219653', '#f44336', '#9b59b6',
        '#e67e22', '#1abc9c', '#34495e', '#e74c3c', '#2ecc71',
    ];

    function vendorColor(idx) {
        return VENDOR_COLORS[idx % VENDOR_COLORS.length];
    }

    function vendorBadge(propId, idx) {
        var color = vendorColor(idx);
        return '<span class="pc-vendor-badge" style="border-color:' + color + '">' +
            '<span class="pc-vendor-dot" style="background:' + color + '"></span>' +
            escHtml(propId) + '</span>';
    }

    function formatMoney(amount) {
        if (amount == null) return '\u2014';
        return '$' + amount.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function formatMoneyShort(amount) {
        if (amount == null) return '\u2014';
        if (amount >= 1000000) return '$' + (amount / 1000000).toFixed(1) + 'M';
        if (amount >= 1000) return '$' + (amount / 1000).toFixed(0) + 'K';
        return '$' + amount.toFixed(0);
    }

    function formatVariance(pct) {
        if (pct == null) return '\u2014';
        const cls = pct < 10 ? 'pc-variance-low' : pct < 30 ? 'pc-variance-mid' : 'pc-variance-high';
        return '<span class="' + cls + '">' + pct.toFixed(1) + '%</span>';
    }

    function formatPct(val) {
        if (val == null) return '\u2014';
        return val.toFixed(1) + '%';
    }

    // ── Chart dark mode helper ──
    function _getChartTextColor() {
        return getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim() || '#e6edf3';
    }
    function _getChartSecondaryColor() {
        return getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || '#8b949e';
    }
    function _getChartGridColor() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    }
    function _applyChartDefaults() {
        if (window.Chart) {
            Chart.defaults.color = _getChartTextColor();
            Chart.defaults.borderColor = _getChartGridColor();
        }
    }

    function fileIcon(ext) {
        if (ext === '.xlsx' || ext === '.xls') return 'file-spreadsheet';
        if (ext === '.docx') return 'file-text';
        if (ext === '.pdf') return 'file';
        return 'file';
    }

    function fileIconClass(ext) {
        if (ext === '.xlsx' || ext === '.xls') return 'xlsx';
        if (ext === '.docx') return 'docx';
        if (ext === '.pdf') return 'pdf';
        return '';
    }

    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function truncate(str, max) {
        if (!str) return '';
        return str.length > max ? str.substring(0, max) + '...' : str;
    }

    function escHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function severityColor(severity) {
        switch (severity) {
            case 'critical': return '#f44336';
            case 'warning': return '#ff9800';
            case 'info': return '#2196f3';
            default: return '#9e9e9e';
        }
    }

    function severityBg(severity) {
        switch (severity) {
            case 'critical': return 'rgba(244,67,54,0.1)';
            case 'warning': return 'rgba(255,152,0,0.1)';
            case 'info': return 'rgba(33,150,243,0.1)';
            default: return 'rgba(158,158,158,0.08)';
        }
    }

    function heatmapColor(level) {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        switch (level) {
            case 'very_low': return '#2d6a2d';
            case 'low': return '#4caf50';
            case 'neutral': return isDark ? '#2d333b' : '#f5f5f5';
            case 'high': return '#ff9800';
            case 'very_high': return '#f44336';
            case 'single_vendor': return isDark ? '#1c2128' : '#f9f9f9';
            case 'missing': return isDark ? '#161b22' : '#e0e0e0';
            default: return isDark ? '#2d333b' : '#f5f5f5';
        }
    }

    function heatmapTextColor(level) {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        switch (level) {
            case 'very_low': return '#fff';
            case 'low': return '#fff';
            case 'neutral': return isDark ? '#adbac7' : '#333';
            case 'high': return '#fff';
            case 'very_high': return '#fff';
            case 'single_vendor': return isDark ? '#768390' : '#888';
            case 'missing': return isDark ? '#545d68' : '#999';
            default: return isDark ? '#adbac7' : '#333';
        }
    }

    function gradeColor(grade) {
        switch (grade) {
            case 'A': return '#219653';
            case 'B': return '#4caf50';
            case 'C': return '#ff9800';
            case 'D': return '#f44336';
            case 'F': return '#b71c1c';
            default: return '#9e9e9e';
        }
    }

    // ──────────────────────────────────────────
    // Phase indicator helper
    // ──────────────────────────────────────────

    function renderPhaseIndicator(activeStep) {
        // activeStep: 1=Upload, 2=Extract, 3=Review, 4=Compare
        const steps = [
            { num: 1, label: 'Upload' },
            { num: 2, label: 'Extract' },
            { num: 3, label: 'Review' },
            { num: 4, label: 'Compare' },
        ];
        return '<div class="pc-phase-indicator">' + steps.map((s, i) => {
            let cls = 'pc-phase-step';
            let numContent = String(s.num);
            if (s.num < activeStep) {
                cls += ' done';
                numContent = '\u2713';
            } else if (s.num === activeStep) {
                cls += ' active';
            }
            let connector = '';
            if (i < steps.length - 1) {
                connector = '<div class="pc-phase-connector' + (s.num < activeStep ? ' done' : '') + '"></div>';
            }
            return '<div class="' + cls + '">' +
                '<span class="pc-step-num">' + numContent + '</span> ' + s.label +
                '</div>' + connector;
        }).join('') + '</div>';
    }

    // ──────────────────────────────────────────
    // Project Management
    // ──────────────────────────────────────────

    async function fetchProjects() {
        try {
            const resp = await fetch('/api/proposal-compare/projects', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            const result = await resp.json();
            if (result.success) {
                State.projects = result.data || [];
            }
        } catch (err) {
            console.warn('[AEGIS ProposalCompare] Failed to fetch projects:', err);
            State.projects = [];
        }
    }

    async function fetchProjectProposals(projectId) {
        try {
            const resp = await fetch('/api/proposal-compare/projects/' + projectId + '/proposals', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            const result = await resp.json();
            if (result.success) {
                State.projectProposals = result.data || [];
            }
        } catch (err) {
            console.warn('[AEGIS ProposalCompare] Failed to fetch project proposals:', err);
            State.projectProposals = [];
        }
    }

    async function createProject(name, description) {
        try {
            const resp = await fetch('/api/proposal-compare/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify({ name: name, description: description || '' }),
            });
            const result = await resp.json();
            if (result.success && result.data) {
                State.projects.unshift(result.data);
                State.selectedProjectId = result.data.id;
                if (window.showToast) window.showToast('Project created: ' + name, 'success');
                return result.data;
            } else {
                throw new Error(result.error?.message || 'Failed to create project');
            }
        } catch (err) {
            console.error('[AEGIS ProposalCompare] Create project error:', err);
            if (window.showToast) window.showToast('Failed to create project: ' + err.message, 'error');
            return null;
        }
    }

    function renderProjectSelector() {
        const container = document.getElementById('pc-project-selector');
        if (!container) return;

        let options = '<option value="">No project (ad-hoc comparison)</option>';
        for (const p of State.projects) {
            const sel = State.selectedProjectId === p.id ? ' selected' : '';
            options += '<option value="' + p.id + '"' + sel + '>' + escHtml(p.name) + '</option>';
        }

        container.innerHTML =
            '<div class="pc-project-bar">' +
                '<div class="pc-project-bar-left">' +
                    '<i data-lucide="folder-open" style="width:16px;height:16px;color:#D6A84A"></i>' +
                    '<select id="pc-project-dropdown" class="pc-project-select">' + options + '</select>' +
                '</div>' +
                '<button class="pc-btn-icon" id="pc-btn-new-project" title="New Project">' +
                    '<i data-lucide="folder-plus" style="width:16px;height:16px"></i>' +
                '</button>' +
            '</div>' +
            '<div class="pc-new-project-form" id="pc-new-project-form" style="display:none">' +
                '<input type="text" id="pc-project-name" class="pc-input" placeholder="Project name" maxlength="100">' +
                '<input type="text" id="pc-project-desc" class="pc-input" placeholder="Description (optional)" maxlength="250">' +
                '<div class="pc-new-project-actions">' +
                    '<button class="pc-btn pc-btn-primary pc-btn-sm" id="pc-btn-save-project">' +
                        '<i data-lucide="check" style="width:14px;height:14px"></i> Create' +
                    '</button>' +
                    '<button class="pc-btn pc-btn-secondary pc-btn-sm" id="pc-btn-cancel-project">' +
                        'Cancel' +
                    '</button>' +
                '</div>' +
            '</div>' +
            '<div id="pc-project-proposals-list"></div>';

        // Wire events
        const dropdown = document.getElementById('pc-project-dropdown');
        if (dropdown) {
            dropdown.addEventListener('change', async function() {
                const val = this.value;
                State.selectedProjectId = val ? parseInt(val) : null;
                State.projectProposals = [];
                if (State.selectedProjectId) {
                    await fetchProjectProposals(State.selectedProjectId);
                }
                renderProjectProposalsList();
            });
        }

        const newBtn = document.getElementById('pc-btn-new-project');
        if (newBtn) {
            newBtn.addEventListener('click', function() {
                const form = document.getElementById('pc-new-project-form');
                if (form) form.style.display = form.style.display === 'none' ? 'flex' : 'none';
            });
        }

        const saveBtn = document.getElementById('pc-btn-save-project');
        if (saveBtn) {
            saveBtn.addEventListener('click', async function() {
                const nameInput = document.getElementById('pc-project-name');
                const descInput = document.getElementById('pc-project-desc');
                const name = nameInput?.value?.trim();
                if (!name) {
                    if (window.showToast) window.showToast('Project name is required', 'error');
                    return;
                }
                const proj = await createProject(name, descInput?.value?.trim());
                if (proj) {
                    const form = document.getElementById('pc-new-project-form');
                    if (form) form.style.display = 'none';
                    renderProjectSelector();
                    if (window.lucide) window.lucide.createIcons();
                }
            });
        }

        const cancelBtn = document.getElementById('pc-btn-cancel-project');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                const form = document.getElementById('pc-new-project-form');
                if (form) form.style.display = 'none';
            });
        }

        if (window.lucide) window.lucide.createIcons();

        // If a project is selected, show its proposals
        if (State.selectedProjectId) {
            renderProjectProposalsList();
        }
    }

    function renderProjectProposalsList() {
        const listEl = document.getElementById('pc-project-proposals-list');
        if (!listEl) return;

        if (!State.selectedProjectId || State.projectProposals.length === 0) {
            listEl.innerHTML = '';
            return;
        }

        let html = '<div class="pc-project-existing">' +
            '<div class="pc-project-existing-label">' +
            '<i data-lucide="file-check" style="width:14px;height:14px;color:#219653"></i> ' +
            State.projectProposals.length + ' proposal' +
            (State.projectProposals.length !== 1 ? 's' : '') +
            ' already in project</div>';

        for (const p of State.projectProposals) {
            html += '<div class="pc-project-prop-item" data-proposal-id="' + (p.id || '') + '">' +
                '<span class="pc-project-prop-name">' + escHtml(p.company_name || p.filename) + '</span>' +
                '<span class="pc-project-prop-total">' + (p.total_raw || '\u2014') + '</span>' +
                (p.id ? '<button class="pc-prop-delete-btn" data-pid="' + p.id + '" title="Remove from project">' +
                    '<i data-lucide="trash-2" style="width:14px;height:14px"></i></button>' : '') +
            '</div>';
        }
        html += '</div>';

        listEl.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();

        // Wire delete buttons
        listEl.querySelectorAll('.pc-prop-delete-btn').forEach(function(btn) {
            btn.addEventListener('click', async function(e) {
                e.stopPropagation();
                var pid = parseInt(this.getAttribute('data-pid'));
                if (!pid) return;

                var propName = this.closest('.pc-project-prop-item')
                    ?.querySelector('.pc-project-prop-name')?.textContent || 'this proposal';

                if (!confirm('Remove "' + propName + '" from this project?')) return;

                try {
                    var resp = await fetch('/api/proposal-compare/proposals/' + pid, {
                        method: 'DELETE',
                        headers: { 'X-CSRF-Token': getCSRF() },
                    });
                    var result = await resp.json();
                    if (result.success) {
                        if (window.showToast) window.showToast('Proposal removed', 'success');
                        // Refresh the list
                        await fetchProjectProposals(State.selectedProjectId);
                        renderProjectProposalsList();
                    } else {
                        if (window.showToast) window.showToast(result.error?.message || 'Failed to remove', 'error');
                    }
                } catch (err) {
                    console.error('[AEGIS ProposalCompare] Delete proposal error:', err);
                    if (window.showToast) window.showToast('Failed to remove proposal', 'error');
                }
            });
        });
    }

    // ──────────────────────────────────────────
    // Phase: Upload
    // ──────────────────────────────────────────

    async function renderUploadPhase() {
        const body = document.getElementById('pc-body');
        if (!body) return;

        State.phase = 'upload';

        // Fetch projects in background
        await fetchProjects();

        body.innerHTML =
            renderPhaseIndicator(1) +
            '<div class="pc-upload-area">' +
                '<div class="pc-upload-header">' +
                    '<div id="pc-project-selector"></div>' +
                    '<button class="pc-btn pc-btn-ghost pc-btn-sm" id="pc-btn-projects">' +
                        '<i data-lucide="layout-dashboard"></i> Projects' +
                    '</button>' +
                    '<button class="pc-btn pc-btn-ghost pc-btn-sm" id="pc-btn-history">' +
                        '<i data-lucide="history"></i> History' +
                    '</button>' +
                '</div>' +
                // v5.9.53: Show existing proposals when returning via "Add Proposal"
                (State.proposals.length > 0
                    ? '<div class="pc-existing-proposals">' +
                        '<div class="pc-existing-header">' +
                            '<i data-lucide="check-circle" style="width:16px;height:16px;color:#4CAF50;vertical-align:-3px"></i> ' +
                            '<strong>' + State.proposals.length + ' proposal' + (State.proposals.length > 1 ? 's' : '') + ' already loaded</strong>' +
                            '<span style="color:var(--text-secondary,#888);font-size:12px;margin-left:8px">Add more files below, then click Extract</span>' +
                        '</div>' +
                        '<div class="pc-existing-list">' +
                            State.proposals.map(function(ep, epi) {
                                return '<span class="pc-existing-chip">' +
                                    '<i data-lucide="file-text" style="width:12px;height:12px;vertical-align:-2px;margin-right:4px"></i>' +
                                    escHtml(ep.company_name || ep.filename || ('Proposal ' + (epi + 1))) +
                                    (ep.contract_term ? ' <span class="pc-chip-term">' + escHtml(ep.contract_term) + '</span>' : '') +
                                    (ep.total_amount != null ? ' <span class="pc-chip-total">' + formatMoneyShort(ep.total_amount) + '</span>' : '') +
                                '</span>';
                            }).join('') +
                        '</div>' +
                      '</div>'
                    : '') +
                '<div class="pc-dropzone" id="pc-dropzone">' +
                    '<input type="file" class="pc-file-input" id="pc-file-input"' +
                    '       multiple accept=".xlsx,.xls,.docx,.pdf">' +
                    '<div class="pc-dropzone-icon">' +
                        '<i data-lucide="upload-cloud"></i>' +
                    '</div>' +
                    '<h3>' + (State.proposals.length > 0 ? 'Add more proposal files' : 'Drop proposal files here') + '</h3>' +
                    '<p>Supports DOCX, PDF, and Excel files \u2022 2\u201310 files</p>' +
                '</div>' +
                '<div class="pc-file-list" id="pc-file-list"></div>' +
                '<div class="pc-upload-actions">' +
                    '<button class="pc-btn pc-btn-primary" id="pc-btn-extract" disabled>' +
                        '<i data-lucide="scan-search"></i> Extract Financial Data' +
                    '</button>' +
                    '<button class="pc-btn pc-btn-ghost pc-btn-sm" id="pc-btn-structure" disabled' +
                    '        title="Download a privacy-safe structural analysis of all selected files — safe for sharing with developers">' +
                        '<i data-lucide="file-search"></i> Analyze Structure' +
                    '</button>' +
                '</div>' +
            '</div>';

        // Render the project selector
        renderProjectSelector();

        // Wire up events
        const dropzone = document.getElementById('pc-dropzone');
        const fileInput = document.getElementById('pc-file-input');
        const extractBtn = document.getElementById('pc-btn-extract');

        dropzone.addEventListener('click', function() { fileInput.click(); });
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
        dropzone.addEventListener('dragleave', function() {
            dropzone.classList.remove('dragover');
        });
        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            var files = Array.from(e.dataTransfer.files).filter(function(f) {
                var ext = '.' + f.name.split('.').pop().toLowerCase();
                return ['.xlsx', '.xls', '.docx', '.pdf'].indexOf(ext) >= 0;
            });
            addFiles(files);
        });

        fileInput.addEventListener('change', function() {
            addFiles(Array.from(fileInput.files));
            fileInput.value = '';
        });

        extractBtn.addEventListener('click', startExtraction);

        var structBtn = document.getElementById('pc-btn-structure');
        if (structBtn) {
            structBtn.addEventListener('click', analyzeStructure);
        }

        var projectsBtn = document.getElementById('pc-btn-projects');
        if (projectsBtn) {
            projectsBtn.addEventListener('click', renderProjectDashboard);
        }

        var historyBtn = document.getElementById('pc-btn-history');
        if (historyBtn) {
            historyBtn.addEventListener('click', renderHistoryView);
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function addFiles(newFiles) {
        for (const f of newFiles) {
            // Don't add duplicates
            if (State.files.some(function(sf) { return sf.name === f.name && sf.size === f.size; })) continue;
            if (State.files.length >= 10) break;
            State.files.push(f);
        }
        renderFileList();
        updateExtractButton();
    }

    function removeFile(index) {
        State.files.splice(index, 1);
        renderFileList();
        updateExtractButton();
    }

    function renderFileList() {
        const list = document.getElementById('pc-file-list');
        if (!list) return;

        if (State.files.length === 0) {
            list.innerHTML = '';
            return;
        }

        list.innerHTML = State.files.map(function(f, idx) {
            var ext = '.' + f.name.split('.').pop().toLowerCase();
            return '<div class="pc-file-item">' +
                '<div class="pc-file-icon ' + fileIconClass(ext) + '">' +
                    '<i data-lucide="' + fileIcon(ext) + '"></i>' +
                '</div>' +
                '<div class="pc-file-info">' +
                    '<div class="pc-file-name">' + escHtml(f.name) + '</div>' +
                    '<div class="pc-file-meta">' + formatBytes(f.size) + '</div>' +
                '</div>' +
                '<button class="pc-file-remove" onclick="ProposalCompare._removeFile(' + idx + ')" title="Remove">' +
                    '<i data-lucide="x" style="width:16px;height:16px"></i>' +
                '</button>' +
            '</div>';
        }).join('');

        if (window.lucide) window.lucide.createIcons();
    }

    function updateExtractButton() {
        const btn = document.getElementById('pc-btn-extract');
        if (btn) {
            // If project has existing proposals, fewer new files needed
            var existingCount = State.projectProposals.length || 0;
            var minFiles = Math.max(0, 2 - existingCount);
            btn.disabled = State.files.length < Math.max(1, minFiles);
        }
        // Structure analysis — works on all selected files
        var structBtn = document.getElementById('pc-btn-structure');
        if (structBtn) {
            structBtn.disabled = State.files.length < 1;
            var structLabel = 'Analyze Structure';
            if (State.files.length > 1) {
                structLabel = 'Analyze Structure (' + State.files.length + ' files)';
            }
            structBtn.innerHTML = '<i data-lucide="file-search"></i> ' + structLabel;
            if (window.lucide) window.lucide.createIcons();
        }
    }

    // ──────────────────────────────────────────
    // Structure Analysis (privacy-safe)
    // ──────────────────────────────────────────

    async function analyzeStructure() {
        if (State.files.length < 1) return;

        var fileCount = State.files.length;
        var btn = document.getElementById('pc-btn-structure');
        if (btn) {
            btn.disabled = true;
            var loadLabel = fileCount > 1
                ? 'Analyzing ' + fileCount + ' files...'
                : 'Analyzing...';
            btn.innerHTML = '<i data-lucide="loader-2" class="pc-spin"></i> ' + loadLabel;
            if (window.lucide) window.lucide.createIcons();
        }

        try {
            // Get CSRF token
            var csrfMeta = document.querySelector('meta[name="csrf-token"]');
            var csrfToken = csrfMeta ? csrfMeta.content : '';

            var formData = new FormData();
            State.files.forEach(function(f) {
                formData.append('files[]', f);
            });

            var resp = await fetch('/api/proposal-compare/analyze-batch-structure', {
                method: 'POST',
                headers: { 'X-CSRF-Token': csrfToken },
                body: formData,
            });

            if (!resp.ok) {
                var errData = null;
                try { errData = await resp.json(); } catch(e) {}
                var msg = errData && errData.error ? errData.error.message : ('Server error ' + resp.status);
                throw new Error(msg);
            }

            // Download the JSON file
            var blob = await resp.blob();
            var downloadName = fileCount > 1
                ? 'batch_structure_analysis.json'
                : State.files[0].name.replace(/\.[^.]+$/, '') + '_structure_analysis.json';

            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = downloadName;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                URL.revokeObjectURL(a.href);
                document.body.removeChild(a);
            }, 200);

            if (typeof showToast === 'function') {
                var toastMsg = 'Structure analysis downloaded';
                if (fileCount > 1) toastMsg += ' (' + fileCount + ' files)';
                showToast(toastMsg, 'success');
            }

        } catch(err) {
            console.error('[ProposalCompare] Structure analysis error:', err);
            if (typeof showToast === 'function') {
                showToast('Structure analysis failed: ' + err.message, 'error');
            }
        } finally {
            if (btn) {
                btn.disabled = State.files.length < 1;
                var restoreLabel = 'Analyze Structure';
                if (State.files.length > 1) {
                    restoreLabel = 'Analyze Structure (' + State.files.length + ' files)';
                }
                btn.innerHTML = '<i data-lucide="file-search"></i> ' + restoreLabel;
                if (window.lucide) window.lucide.createIcons();
            }
        }
    }


    // ──────────────────────────────────────────
    // Phase: Extraction
    // ──────────────────────────────────────────

    async function startExtraction() {
        State.phase = 'extracting';
        const body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML =
            renderPhaseIndicator(2) +
            '<div class="pc-loading">' +
                '<div class="pc-spinner"></div>' +
                '<div class="pc-loading-text">Extracting financial data from ' + State.files.length + ' files...</div>' +
            '</div>' +
            '<div class="pc-file-list" id="pc-extract-list"></div>';

        // Show file extraction progress
        var extractList = document.getElementById('pc-extract-list');
        if (extractList) {
            extractList.innerHTML = State.files.map(function(f, idx) {
                var ext = '.' + f.name.split('.').pop().toLowerCase();
                return '<div class="pc-file-item" id="pc-extract-item-' + idx + '">' +
                    '<div class="pc-file-icon ' + fileIconClass(ext) + '">' +
                        '<i data-lucide="' + fileIcon(ext) + '"></i>' +
                    '</div>' +
                    '<div class="pc-file-info">' +
                        '<div class="pc-file-name">' + escHtml(f.name) + '</div>' +
                        '<div class="pc-file-meta" id="pc-extract-meta-' + idx + '">Waiting...</div>' +
                    '</div>' +
                    '<div class="pc-file-status extracting" id="pc-extract-status-' + idx + '">Extracting</div>' +
                '</div>';
            }).join('');
        }

        if (window.lucide) window.lucide.createIcons();

        // Upload and extract
        var formData = new FormData();
        State.files.forEach(function(f) { formData.append('files[]', f); });
        if (State.selectedProjectId) {
            formData.append('project_id', String(State.selectedProjectId));
        }

        try {
            var resp = await fetch('/api/proposal-compare/upload', {
                method: 'POST',
                headers: { 'X-CSRF-Token': getCSRF() },
                body: formData,
            });

            var result = await resp.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Upload failed');
            }

            // Process results
            State.proposals = [];
            var results = result.data?.results || [];

            results.forEach(function(r, idx) {
                var metaEl = document.getElementById('pc-extract-meta-' + idx);
                var statusEl = document.getElementById('pc-extract-status-' + idx);

                if (r.success && r.data) {
                    // Track db_id for edit persistence (Part A)
                    if (r.db_id) r.data._db_id = r.db_id;

                    // Snapshot original extraction for learning system (v5.9.49)
                    // Deep copy parser output before user can edit — sent with compare
                    // request so backend can compute diffs and learn from corrections.
                    // All learned data stays local in parser_patterns.json, never uploaded.
                    r.data._original_extraction = JSON.parse(JSON.stringify({
                        company_name: r.data.company_name || '',
                        contract_term: r.data.contract_term || '',
                        line_items: (r.data.line_items || []).map(function(li) {
                            return {
                                description: li.description || '',
                                category: li.category || '',
                                amount: li.amount,
                                quantity: li.quantity,
                                unit_price: li.unit_price
                            };
                        })
                    }));

                    State.proposals.push(r.data);
                    var items = r.data.line_items?.length || 0;
                    var tables = r.data.tables?.length || 0;
                    var total = r.data.total_raw || 'N/A';
                    if (metaEl) metaEl.textContent = items + ' line items \u2022 ' + tables + ' tables \u2022 Total: ' + total;
                    if (statusEl) {
                        statusEl.className = 'pc-file-status ready';
                        statusEl.textContent = 'Ready';
                    }
                } else {
                    if (metaEl) metaEl.textContent = r.error || 'Extraction failed';
                    if (statusEl) {
                        statusEl.className = 'pc-file-status error';
                        statusEl.textContent = 'Error';
                    }
                }
            });

            // Auto-advance to review if we got at least 2 proposals (counting project proposals too)
            var totalAvailable = State.proposals.length + (State.projectProposals?.length || 0);
            if (totalAvailable >= 2 && State.proposals.length >= 1) {
                setTimeout(function() { renderReviewPhase(); }, 1200);
            } else if (State.proposals.length >= 2) {
                setTimeout(function() { renderReviewPhase(); }, 1200);
            } else {
                // Show error state
                var loadingEl = body.querySelector('.pc-loading');
                if (loadingEl) {
                    loadingEl.innerHTML =
                        '<div class="pc-empty">' +
                            '<i data-lucide="alert-circle"></i>' +
                            '<h4>Insufficient Data</h4>' +
                            '<p>Need at least 2 successfully extracted proposals. Got ' + State.proposals.length + '.</p>' +
                            '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">' +
                                '<i data-lucide="arrow-left"></i> Back to Upload' +
                            '</button>' +
                        '</div>';
                    if (window.lucide) window.lucide.createIcons();
                }
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Extraction error:', err);
            var loadingEl = body.querySelector('.pc-loading');
            if (loadingEl) {
                loadingEl.innerHTML =
                    '<div class="pc-empty">' +
                        '<i data-lucide="alert-triangle"></i>' +
                        '<h4>Extraction Failed</h4>' +
                        '<p>' + escHtml(err.message) + '</p>' +
                        '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">' +
                            '<i data-lucide="arrow-left"></i> Try Again' +
                        '</button>' +
                    '</div>';
                if (window.lucide) window.lucide.createIcons();
            }
        }
    }

    // ──────────────────────────────────────────
    // Phase: Review (split-pane: doc viewer + metadata editor)
    // ──────────────────────────────────────────

    function _formatCurrency(val) {
        if (val == null || val === '' || isNaN(val)) return '';
        return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function _parseCurrency(str) {
        if (str == null || str === '') return null;
        var cleaned = String(str).replace(/[^0-9.\-]/g, '');
        var num = parseFloat(cleaned);
        return isNaN(num) ? null : num;
    }

    /** Save current review form fields into State.proposals[idx] */
    function _captureReviewEdits(idx) {
        var p = State.proposals[idx];
        if (!p) return;

        var companyEl = document.getElementById('pc-edit-company');
        var dateEl = document.getElementById('pc-edit-date');
        var termEl = document.getElementById('pc-edit-term');
        var totalEl = document.getElementById('pc-edit-total');

        if (companyEl) p.company_name = companyEl.value.trim() || p.filename;
        if (dateEl) p.date = dateEl.value.trim();
        if (termEl) p.contract_term = termEl.value.trim();
        if (totalEl) {
            var parsed = _parseCurrency(totalEl.value);
            if (parsed !== null) {
                p.total_amount = parsed;
                p.total_raw = totalEl.value.trim();
            }
        }

        // Capture line item edits if editor is open
        var editorBody = document.getElementById('pc-line-item-tbody');
        if (editorBody && State._lineItemEditorOpen[idx]) {
            var rows = editorBody.querySelectorAll('.pc-li-row');
            var items = [];
            rows.forEach(function(row) {
                var desc = row.querySelector('.pc-li-desc')?.value?.trim() || '';
                if (!desc) return; // skip empty rows
                items.push({
                    description: desc,
                    category: row.querySelector('.pc-li-cat')?.value || 'Other',
                    amount: _parseCurrency(row.querySelector('.pc-li-amount')?.value),
                    amount_raw: row.querySelector('.pc-li-amount')?.value || '',
                    quantity: parseFloat(row.querySelector('.pc-li-qty')?.value) || null,
                    unit_price: _parseCurrency(row.querySelector('.pc-li-unit')?.value),
                    unit: '',
                    row_index: 0,
                    table_index: 0,
                    source_sheet: '',
                    confidence: 1.0,
                });
            });
            p.line_items = items;
        }

        // v5.9.42: Auto-persist edits to DB if proposal has _db_id
        if (p._db_id) {
            fetch('/api/proposal-compare/proposals/' + p._db_id, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify(p),
            }).then(function(r) {
                if (!r.ok) console.warn('[PC] Edit persist failed for proposal', p._db_id);
                else console.log('[PC] Edits persisted for proposal', p._db_id);
            }).catch(function(e) {
                console.warn('[PC] Edit persist error:', e);
            });
        }
    }

    // ──────────────────────────────────────────
    // v5.9.53: Line Item Undo/Redo
    // ──────────────────────────────────────────

    function _pushUndo(idx, action, data, rowIdx) {
        if (!State._undoStacks[idx]) State._undoStacks[idx] = [];
        State._undoStacks[idx].push({ action: action, data: data, rowIdx: rowIdx, timestamp: Date.now() });
        // Clear redo stack on new action
        State._redoStacks[idx] = [];
        _updateUndoRedoButtons(idx);
    }

    function _undoLineItem(idx) {
        var stack = State._undoStacks[idx];
        if (!stack || stack.length === 0) return;
        var entry = stack.pop();
        if (!State._redoStacks[idx]) State._redoStacks[idx] = [];
        State._redoStacks[idx].push(entry);

        if (entry.action === 'delete') {
            // Re-insert the deleted row
            var tbody = document.getElementById('pc-line-item-tbody');
            if (tbody) {
                var cats = ['Labor', 'Material', 'Software', 'License', 'Travel', 'Training', 'ODC', 'Subcontract', 'Overhead', 'Fee', 'Other'];
                var rowHtml = _renderLineItemRow(entry.data, entry.rowIdx, cats);
                var rows = tbody.querySelectorAll('.pc-li-row');
                if (entry.rowIdx >= rows.length) {
                    tbody.insertAdjacentHTML('beforeend', rowHtml);
                } else {
                    rows[entry.rowIdx].insertAdjacentHTML('beforebegin', rowHtml);
                }
                _wireLineItemRowEvents(tbody);
            }
        } else if (entry.action === 'add') {
            // Remove the added row
            var tbody = document.getElementById('pc-line-item-tbody');
            if (tbody) {
                var lastRow = tbody.querySelector('.pc-li-row:last-child');
                if (lastRow) lastRow.remove();
            }
        }
        _updateUndoRedoButtons(idx);
    }

    function _redoLineItem(idx) {
        var stack = State._redoStacks[idx];
        if (!stack || stack.length === 0) return;
        var entry = stack.pop();
        if (!State._undoStacks[idx]) State._undoStacks[idx] = [];
        State._undoStacks[idx].push(entry);

        if (entry.action === 'delete') {
            // Re-delete the row
            var tbody = document.getElementById('pc-line-item-tbody');
            if (tbody) {
                var rows = tbody.querySelectorAll('.pc-li-row');
                if (rows[entry.rowIdx]) rows[entry.rowIdx].remove();
            }
        } else if (entry.action === 'add') {
            // Re-add the row
            var tbody = document.getElementById('pc-line-item-tbody');
            if (tbody) {
                var cats = ['Labor', 'Material', 'Software', 'License', 'Travel', 'Training', 'ODC', 'Subcontract', 'Overhead', 'Fee', 'Other'];
                var rowHtml = _renderLineItemRow(entry.data, tbody.children.length, cats);
                tbody.insertAdjacentHTML('beforeend', rowHtml);
                _wireLineItemRowEvents(tbody);
            }
        }
        _updateUndoRedoButtons(idx);
    }

    function _updateUndoRedoButtons(idx) {
        var undoBtn = document.getElementById('pc-li-undo');
        var redoBtn = document.getElementById('pc-li-redo');
        if (undoBtn) {
            var hasUndo = State._undoStacks[idx] && State._undoStacks[idx].length > 0;
            undoBtn.disabled = !hasUndo;
            undoBtn.title = hasUndo ? 'Undo: ' + State._undoStacks[idx][State._undoStacks[idx].length - 1].action : 'Nothing to undo';
        }
        if (redoBtn) {
            var hasRedo = State._redoStacks[idx] && State._redoStacks[idx].length > 0;
            redoBtn.disabled = !hasRedo;
            redoBtn.title = hasRedo ? 'Redo: ' + State._redoStacks[idx][State._redoStacks[idx].length - 1].action : 'Nothing to redo';
        }
    }

    // ──────────────────────────────────────────
    // v5.9.53: Auto-recalculate helper
    // ──────────────────────────────────────────

    function _autoRecalcRow(row) {
        var amtEl = row.querySelector('.pc-li-amount');
        var qtyEl = row.querySelector('.pc-li-qty');
        var unitEl = row.querySelector('.pc-li-unit');
        if (!amtEl || !qtyEl || !unitEl) return;

        var amt = _parseCurrency(amtEl.value);
        var qty = parseFloat(qtyEl.value) || null;
        var unit = _parseCurrency(unitEl.value);

        // Count how many fields have values
        var filled = (amt !== null ? 1 : 0) + (qty !== null ? 1 : 0) + (unit !== null ? 1 : 0);
        if (filled < 2) return; // Need at least 2 to compute 3rd

        if (amt === null && qty !== null && unit !== null) {
            amtEl.value = _formatCurrency(qty * unit);
            amtEl.classList.add('pc-auto-calc');
        } else if (qty === null && amt !== null && unit !== null && unit > 0) {
            qtyEl.value = Math.round((amt / unit) * 100) / 100;
            qtyEl.classList.add('pc-auto-calc');
        } else if (unit === null && amt !== null && qty !== null && qty > 0) {
            unitEl.value = _formatCurrency(amt / qty);
            unitEl.classList.add('pc-auto-calc');
        }
    }

    function _wireLineItemRowEvents(tbody) {
        // Wire auto-recalculate on input for amount/qty/unit fields
        tbody.querySelectorAll('.pc-li-amount, .pc-li-qty, .pc-li-unit').forEach(function(input) {
            if (input._pcWired) return;
            input._pcWired = true;
            input.addEventListener('blur', function() {
                this.classList.remove('pc-auto-calc');
                _autoRecalcRow(this.closest('.pc-li-row'));
            });
        });
        // Wire expandable descriptions
        tbody.querySelectorAll('.pc-li-desc').forEach(function(input) {
            if (input._pcExpandWired) return;
            input._pcExpandWired = true;
            input.addEventListener('focus', function() {
                this.closest('.pc-li-row')?.classList.add('pc-li-expanded');
            });
            input.addEventListener('blur', function() {
                this.closest('.pc-li-row')?.classList.remove('pc-li-expanded');
            });
        });
    }

    // ──────────────────────────────────────────
    // v5.9.53: Selective comparison helpers
    // ──────────────────────────────────────────

    function _startSelectiveComparison(proposalIndices) {
        // Filter proposals to only those selected
        var selected = proposalIndices.map(function(i) { return State.proposals[i]; }).filter(Boolean);
        if (selected.length < 2) {
            if (window.showToast) window.showToast('Select at least 2 proposals to compare', 'error');
            return;
        }
        // Store original proposals list and swap in selected subset
        State._allProposals = State.proposals;
        State.proposals = selected;
        startComparison();
    }

    function _restoreAllProposals() {
        if (State._allProposals) {
            State.proposals = State._allProposals;
            State._allProposals = null;
        }
    }

    /**
     * v5.9.53: Apply vendor filter on results view — re-renders tab content
     * with only the checked vendor chips included.
     */
    function _applyVendorFilter() {
        var activeChips = document.querySelectorAll('.pc-vendor-chip.pc-vendor-chip-on');
        var activeIds = [];
        activeChips.forEach(function(c) { activeIds.push(c.dataset.vendorId); });

        if (activeIds.length < 2) {
            if (window.showToast) window.showToast('Need at least 2 vendors for comparison', 'error');
            return;
        }

        // Filter comparison data to only active vendors
        var cmp = State.comparison;
        if (!cmp) return;

        var propIds = activeIds;
        destroyCharts();

        // Re-render all tabs with filtered vendor list
        renderExecutiveSummary(propIds, cmp);
        renderComparisonTable(propIds, cmp);
        renderCategoriesTab(propIds, cmp);
        renderRedFlagsTab(propIds, cmp);
        renderHeatmapTab(propIds, cmp);
        renderVendorScoresTab(propIds, cmp);
        renderDetailsTab(cmp);
        renderTablesTab(cmp);

        if (window.lucide) window.lucide.createIcons();
    }

    function _renderDocViewer(idx) {
        var p = State.proposals[idx];
        var fileType = (p.file_type || '').toLowerCase();
        var container = document.getElementById('pc-doc-viewer');
        if (!container) return;

        console.log('[PC DocViewer] Rendering idx=' + idx + ' fileType=' + fileType +
            ' hasFile=' + !!State.files[idx] + ' hasText=' + !!(p.full_text || p.extraction_text));

        container.innerHTML = '<div class="pc-doc-loading"><div class="pc-spinner"></div> Loading document...</div>';

        // PDF: serve from backend via /api/proposal-compare/file/<name>
        // Same pattern as /api/scan-history/document-file for the main review tool
        if (fileType === 'pdf') {
            var textContent = p.extraction_text || '';
            var serverFile = p._server_file;

            if (serverFile && window.TWR && window.TWR.PDFViewer) {
                var fileUrl = '/api/proposal-compare/file/' + encodeURIComponent(serverFile);
                console.log('[PC DocViewer] Rendering PDF from server: ' + fileUrl);
                TWR.PDFViewer.render(container, fileUrl, { scale: 2.0, showZoomBar: true, showMagnifier: true }).catch(function(err) {
                    console.warn('[PC DocViewer] PDF.js render failed:', err);
                    if (textContent) {
                        container.innerHTML = '<div class="pc-doc-notice"><i data-lucide="info"></i> ' +
                            'PDF canvas render failed — showing extracted text</div>' +
                            '<pre class="pc-doc-text">' + escHtml(textContent) + '</pre>';
                        if (window.lucide) window.lucide.createIcons();
                    }
                });
            } else if (textContent) {
                // No PDF.js or no server file — show extracted text
                console.log('[PC DocViewer] Showing extracted text (serverFile=' + !!serverFile +
                    ', PDFViewer=' + !!(window.TWR && window.TWR.PDFViewer) + ')');
                container.innerHTML = '<div class="pc-doc-notice"><i data-lucide="info"></i> ' +
                    'Showing extracted text</div>' +
                    '<pre class="pc-doc-text">' + escHtml(textContent) + '</pre>';
                if (window.lucide) window.lucide.createIcons();
            } else {
                container.innerHTML = '<div class="pc-doc-fallback"><i data-lucide="file-text"></i>' +
                    '<p>PDF preview not available.</p>' +
                    '<p class="pc-doc-hint">Extracted data shown in the editor panel.</p></div>';
                if (window.lucide) window.lucide.createIcons();
            }
            return;
        }

        // XLSX: render tables
        if (fileType === 'xlsx' && p.tables && p.tables.length > 0) {
            var html = '';
            p.tables.forEach(function(t, ti) {
                html += '<div class="pc-doc-table-section"><h5>Table ' + (ti + 1) + '</h5>';
                html += '<table class="pc-doc-table"><thead><tr>';
                (t.headers || []).forEach(function(h) { html += '<th>' + escHtml(h) + '</th>'; });
                html += '</tr></thead><tbody>';
                (t.rows || []).forEach(function(r) {
                    html += '<tr>';
                    r.forEach(function(c) { html += '<td>' + escHtml(String(c ?? '')) + '</td>'; });
                    html += '</tr>';
                });
                html += '</tbody></table></div>';
            });
            container.innerHTML = html || '<p class="pc-doc-fallback">No table data extracted.</p>';
            return;
        }

        // DOCX / text fallback: show extraction text
        var textContent = p.full_text || p.extraction_text || '';
        if (textContent) {
            container.innerHTML = '<pre class="pc-doc-text">' + escHtml(textContent) + '</pre>';
        } else if (State.files[idx] && fileType === 'docx') {
            // For DOCX, try to show a basic message since we can't render it natively
            container.innerHTML = '<div class="pc-doc-fallback"><i data-lucide="file-text"></i>' +
                '<p>DOCX preview not available.</p><p class="pc-doc-hint">Extracted data shown in the editor panel.</p></div>';
            if (window.lucide) window.lucide.createIcons();
        } else {
            container.innerHTML = '<div class="pc-doc-fallback"><i data-lucide="file-question"></i>' +
                '<p>No document preview available.</p></div>';
            if (window.lucide) window.lucide.createIcons();
        }
    }

    function _renderLineItemEditor(idx) {
        var p = State.proposals[idx];
        var items = p.line_items || [];
        var cats = ['Labor', 'Material', 'Software', 'License', 'Travel', 'Training', 'ODC', 'Subcontract', 'Overhead', 'Fee', 'Other'];

        var hasUndo = State._undoStacks[idx] && State._undoStacks[idx].length > 0;
        var hasRedo = State._redoStacks[idx] && State._redoStacks[idx].length > 0;

        var html = '<div class="pc-li-editor" id="pc-li-editor">' +
            '<div class="pc-li-toolbar">' +
                '<button class="pc-btn pc-btn-xs pc-btn-ghost" id="pc-li-undo" title="Undo"' + (hasUndo ? '' : ' disabled') + '>' +
                    '<i data-lucide="undo-2"></i> Undo' +
                '</button>' +
                '<button class="pc-btn pc-btn-xs pc-btn-ghost" id="pc-li-redo" title="Redo"' + (hasRedo ? '' : ' disabled') + '>' +
                    '<i data-lucide="redo-2"></i> Redo' +
                '</button>' +
                '<span class="pc-li-toolbar-divider"></span>' +
                '<button class="pc-btn pc-btn-xs pc-btn-ghost" id="pc-li-recalc" title="Auto-calculate missing values from available fields">' +
                    '<i data-lucide="calculator"></i> Recalculate' +
                '</button>' +
                '<span class="pc-li-item-count">' + items.length + ' items</span>' +
            '</div>' +
            '<div class="pc-li-table-wrap"><table class="pc-li-table">' +
            '<thead><tr>' +
                '<th class="pc-li-th-desc">Description</th>' +
                '<th class="pc-li-th-cat">Category</th>' +
                '<th class="pc-li-th-amt">Amount</th>' +
                '<th class="pc-li-th-qty">Qty</th>' +
                '<th class="pc-li-th-unit">Unit Price</th>' +
                '<th class="pc-li-th-del"></th>' +
            '</tr></thead>' +
            '<tbody id="pc-line-item-tbody">';

        items.forEach(function(li, liIdx) {
            html += _renderLineItemRow(li, liIdx, cats);
        });

        html += '</tbody></table></div>' +
            '<button class="pc-btn pc-btn-sm pc-btn-ghost" id="pc-add-line-item">' +
                '<i data-lucide="plus"></i> Add Line Item' +
            '</button></div>';

        return html;
    }

    function _renderLineItemRow(li, liIdx, cats) {
        var catOptions = cats.map(function(c) {
            var sel = (li.category || 'Other') === c ? ' selected' : '';
            return '<option value="' + c + '"' + sel + '>' + c + '</option>';
        }).join('');

        return '<tr class="pc-li-row" data-li-idx="' + liIdx + '">' +
            '<td><input type="text" class="pc-li-desc pc-li-input" value="' + escHtml(li.description || '') + '" placeholder="Description"></td>' +
            '<td><select class="pc-li-cat pc-li-input">' + catOptions + '</select></td>' +
            '<td><input type="text" class="pc-li-amount pc-li-input" value="' + escHtml(li.amount_raw || (li.amount != null ? _formatCurrency(li.amount) : '')) + '" placeholder="$0.00"></td>' +
            '<td><input type="text" class="pc-li-qty pc-li-input" value="' + (li.quantity || '') + '" placeholder="-"></td>' +
            '<td><input type="text" class="pc-li-unit pc-li-input" value="' + escHtml(li.unit_price != null ? _formatCurrency(li.unit_price) : '') + '" placeholder="-"></td>' +
            '<td><button class="pc-li-del-btn" title="Remove">&times;</button></td>' +
        '</tr>';
    }

    function _renderReviewProposal(idx) {
        var p = State.proposals[idx];
        if (!p) return;

        var ext = '.' + (p.file_type || '').toLowerCase();
        var items = p.line_items?.length || 0;
        var tables = p.tables?.length || 0;
        var totalDisplay = p.total_raw || (p.total_amount != null ? _formatCurrency(p.total_amount) : '');
        var editorOpen = State._lineItemEditorOpen[idx];

        var container = document.getElementById('pc-review-content');
        if (!container) return;

        container.innerHTML =
            '<div class="pc-review-split">' +
                // Left: Document viewer
                '<div class="pc-review-doc-panel">' +
                    '<div class="pc-review-doc-header">' +
                        '<i data-lucide="' + fileIcon(ext) + '"></i> ' +
                        '<span>' + escHtml(p.filename) + '</span>' +
                    '</div>' +
                    '<div class="pc-review-doc-viewer" id="pc-doc-viewer"></div>' +
                '</div>' +
                // Right: Metadata editor
                '<div class="pc-review-edit-panel">' +
                    '<div class="pc-review-edit-form">' +
                        '<div class="pc-edit-field">' +
                            '<label>Company / Vendor Name</label>' +
                            '<input type="text" id="pc-edit-company" class="pc-edit-input" value="' + escHtml(p.company_name || '') + '" placeholder="Enter company name">' +
                        '</div>' +
                        '<div class="pc-edit-field">' +
                            '<label>Date</label>' +
                            '<input type="text" id="pc-edit-date" class="pc-edit-input" value="' + escHtml(p.date || '') + '" placeholder="e.g. February 15, 2026">' +
                        '</div>' +
                        '<div class="pc-edit-field">' +
                            '<label>Contract Term</label>' +
                            '<input type="text" id="pc-edit-term" class="pc-edit-input" value="' + escHtml(p.contract_term || '') + '" placeholder="e.g. 3 Year, Base + 4 Options">' +
                        '</div>' +
                        '<div class="pc-edit-field">' +
                            '<label>Total Amount</label>' +
                            '<input type="text" id="pc-edit-total" class="pc-edit-input" value="' + escHtml(totalDisplay) + '" placeholder="$0.00">' +
                        '</div>' +
                        '<div class="pc-quality-badges">' +
                            (p.company_name
                                ? '<span class="pc-qb pc-qb-ok"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Company detected</span>'
                                : '<span class="pc-qb pc-qb-warn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> No company name</span>') +
                            (items > 0
                                ? '<span class="pc-qb pc-qb-ok"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> ' + items + ' line items</span>'
                                : '<span class="pc-qb pc-qb-warn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> No line items detected</span>') +
                            (p.total_amount != null
                                ? '<span class="pc-qb pc-qb-ok"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Total: ' + formatMoney(p.total_amount) + '</span>'
                                : '<span class="pc-qb pc-qb-warn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> No total found</span>') +
                            (p.contract_term
                                ? '<span class="pc-qb pc-qb-ok"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> ' + escHtml(p.contract_term) + '</span>'
                                : '<span class="pc-qb pc-qb-info"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> No term detected</span>') +
                        '</div>' +
                        '<button class="pc-btn pc-btn-sm pc-btn-ghost pc-li-toggle" id="pc-toggle-line-items">' +
                            '<i data-lucide="' + (editorOpen ? 'chevron-down' : 'chevron-right') + '"></i> ' +
                            (editorOpen ? 'Hide' : 'Edit') + ' Line Items' +
                        '</button>' +
                    '</div>' +
                    '<div id="pc-li-editor-wrap" class="' + (editorOpen ? '' : 'pc-hidden') + '">' +
                        (editorOpen ? _renderLineItemEditor(idx) : '') +
                    '</div>' +
                '</div>' +
            '</div>';

        // Render document viewer async
        _renderDocViewer(idx);

        // Bind events
        document.getElementById('pc-toggle-line-items')?.addEventListener('click', function() {
            _captureReviewEdits(idx); // save any in-progress edits
            State._lineItemEditorOpen[idx] = !State._lineItemEditorOpen[idx];
            _renderReviewProposal(idx); // re-render with toggled state
        });

        // Line item editor events (if open)
        if (editorOpen) {
            var _editorTbody = document.getElementById('pc-line-item-tbody');

            // Wire auto-recalc and expandable descriptions on existing rows
            if (_editorTbody) _wireLineItemRowEvents(_editorTbody);

            document.getElementById('pc-add-line-item')?.addEventListener('click', function() {
                var tbody = document.getElementById('pc-line-item-tbody');
                if (!tbody) return;
                var cats = ['Labor', 'Material', 'Software', 'License', 'Travel', 'Training', 'ODC', 'Subcontract', 'Overhead', 'Fee', 'Other'];
                var newItem = { description: '', category: 'Other', amount: null, amount_raw: '', quantity: null, unit_price: null };
                var newRow = _renderLineItemRow(newItem, tbody.children.length, cats);
                tbody.insertAdjacentHTML('beforeend', newRow);
                _wireLineItemRowEvents(tbody);
                _pushUndo(idx, 'add', newItem, tbody.children.length - 1);
                // Focus the new description field
                var lastRow = tbody.querySelector('.pc-li-row:last-child .pc-li-desc');
                if (lastRow) lastRow.focus();
            });

            document.getElementById('pc-li-editor')?.addEventListener('click', function(e) {
                if (e.target.classList.contains('pc-li-del-btn')) {
                    var row = e.target.closest('.pc-li-row');
                    if (!row) return;
                    // Capture row data before deletion for undo
                    var rowData = {
                        description: row.querySelector('.pc-li-desc')?.value || '',
                        category: row.querySelector('.pc-li-cat')?.value || 'Other',
                        amount: _parseCurrency(row.querySelector('.pc-li-amount')?.value),
                        amount_raw: row.querySelector('.pc-li-amount')?.value || '',
                        quantity: parseFloat(row.querySelector('.pc-li-qty')?.value) || null,
                        unit_price: _parseCurrency(row.querySelector('.pc-li-unit')?.value),
                    };
                    var rowIdx = Array.from(row.parentNode.children).indexOf(row);
                    _pushUndo(idx, 'delete', rowData, rowIdx);
                    row.remove();
                    // Update item count
                    var countEl = document.querySelector('.pc-li-item-count');
                    var tbody = document.getElementById('pc-line-item-tbody');
                    if (countEl && tbody) countEl.textContent = tbody.children.length + ' items';
                }
            });

            // Undo/Redo buttons
            document.getElementById('pc-li-undo')?.addEventListener('click', function() { _undoLineItem(idx); });
            document.getElementById('pc-li-redo')?.addEventListener('click', function() { _redoLineItem(idx); });

            // Recalculate all rows
            document.getElementById('pc-li-recalc')?.addEventListener('click', function() {
                var tbody = document.getElementById('pc-line-item-tbody');
                if (!tbody) return;
                var count = 0;
                tbody.querySelectorAll('.pc-li-row').forEach(function(row) {
                    var before = {
                        amt: row.querySelector('.pc-li-amount')?.value,
                        qty: row.querySelector('.pc-li-qty')?.value,
                        unit: row.querySelector('.pc-li-unit')?.value
                    };
                    _autoRecalcRow(row);
                    var after = {
                        amt: row.querySelector('.pc-li-amount')?.value,
                        qty: row.querySelector('.pc-li-qty')?.value,
                        unit: row.querySelector('.pc-li-unit')?.value
                    };
                    if (before.amt !== after.amt || before.qty !== after.qty || before.unit !== after.unit) count++;
                });
                if (window.showToast) {
                    window.showToast(count > 0 ? count + ' row' + (count > 1 ? 's' : '') + ' recalculated' : 'All rows already complete', count > 0 ? 'success' : 'info');
                }
            });
        }

        // Currency auto-format on blur for total field
        var totalInput = document.getElementById('pc-edit-total');
        if (totalInput) {
            totalInput.addEventListener('blur', function() {
                var val = _parseCurrency(this.value);
                if (val !== null) this.value = _formatCurrency(val);
            });
        }

        // Currency auto-format + auto-calc on blur for line item fields (event delegation)
        var liEditor = document.getElementById('pc-li-editor');
        if (liEditor) {
            liEditor.addEventListener('blur', function(e) {
                var el = e.target;
                // Auto-format currency fields on blur
                if (el.classList.contains('pc-li-amount') || el.classList.contains('pc-li-unit')) {
                    var val = _parseCurrency(el.value);
                    if (val !== null) el.value = _formatCurrency(val);
                }
            }, true); // capture phase for blur

            liEditor.addEventListener('input', function(e) {
                var el = e.target;
                if (!el.classList.contains('pc-li-amount') && !el.classList.contains('pc-li-qty') && !el.classList.contains('pc-li-unit')) return;
                var row = el.closest('.pc-li-row');
                if (!row) return;

                var amtEl = row.querySelector('.pc-li-amount');
                var qtyEl = row.querySelector('.pc-li-qty');
                var unitEl = row.querySelector('.pc-li-unit');

                var amt = _parseCurrency(amtEl?.value);
                var qty = parseFloat(qtyEl?.value) || null;
                var unit = _parseCurrency(unitEl?.value);

                // Auto-calc missing third field when 2 of 3 are present
                if (qty && unit && amt === null && amtEl) {
                    amtEl.value = _formatCurrency(qty * unit);
                    amtEl.classList.add('pc-auto-calc');
                } else if (amtEl) {
                    amtEl.classList.remove('pc-auto-calc');
                }

                if (amt && qty && unit === null && unitEl) {
                    unitEl.value = _formatCurrency(amt / qty);
                    unitEl.classList.add('pc-auto-calc');
                } else if (unitEl && el !== unitEl) {
                    unitEl.classList.remove('pc-auto-calc');
                }

                if (amt && unit && qty === null && qtyEl) {
                    qtyEl.value = (amt / unit).toFixed(1);
                    qtyEl.classList.add('pc-auto-calc');
                } else if (qtyEl && el !== qtyEl) {
                    qtyEl.classList.remove('pc-auto-calc');
                }
            });
        }

        // Click-to-populate: track last focused input in the edit panel
        var editPanel = container.querySelector('.pc-review-edit-panel');
        if (editPanel) {
            editPanel.addEventListener('focusin', function(e) {
                if (e.target.matches('input.pc-edit-input, input.pc-li-input')) {
                    State._lastFocusedField = e.target;
                }
            });
        }

        // Click-to-populate: mouseup on doc viewer shows "Use" popover when text selected
        var docViewer = document.getElementById('pc-doc-viewer');
        if (docViewer) {
            docViewer.addEventListener('mouseup', function(e) {
                // Remove any existing popover
                var old = document.getElementById('pc-use-popover');
                if (old) old.remove();

                var sel = window.getSelection();
                var text = (sel ? sel.toString() : '').trim();
                if (!text || !State._lastFocusedField) return;

                // Create the micro "Use" button
                var btn = document.createElement('button');
                btn.id = 'pc-use-popover';
                btn.className = 'pc-use-popover-btn';
                btn.textContent = 'Use';
                btn.style.left = e.clientX + 'px';
                btn.style.top = (e.clientY - 36) + 'px';
                document.body.appendChild(btn);

                btn.addEventListener('click', function(ev) {
                    ev.stopPropagation();
                    var field = State._lastFocusedField;
                    if (field) {
                        // Apply currency formatting if it's a currency field
                        if (field.id === 'pc-edit-total' || field.classList.contains('pc-li-amount') || field.classList.contains('pc-li-unit')) {
                            var parsed = _parseCurrency(text);
                            field.value = parsed !== null ? _formatCurrency(parsed) : text;
                        } else {
                            field.value = text;
                        }
                        field.focus();
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    btn.remove();
                });

                // Auto-remove after 3 seconds
                setTimeout(function() { if (btn.parentNode) btn.remove(); }, 3000);
            });

            // Remove popover on scroll or click elsewhere
            docViewer.addEventListener('scroll', function() {
                var old = document.getElementById('pc-use-popover');
                if (old) old.remove();
            });
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function _buildComparePreview() {
        var totalProps = State.proposals.length;
        var companies = State.proposals.filter(function(p) { return p.company_name; });
        var totalItems = State.proposals.reduce(function(sum, p) { return sum + (p.line_items?.length || 0); }, 0);
        var emptyProps = State.proposals.filter(function(p) { return !p.line_items || p.line_items.length === 0; });
        var allReady = companies.length === totalProps && emptyProps.length === 0 && totalItems > 0;

        var html = '<div class="pc-compare-preview">';

        // Proposals ready
        html += '<span class="pc-cp-stat">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ' +
            '<strong>' + totalProps + '</strong> proposals' +
        '</span>';
        html += '<span class="pc-cp-divider"></span>';

        // Companies detected
        html += '<span class="pc-cp-stat">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg> ' +
            '<strong>' + companies.length + '</strong> vendors identified' +
        '</span>';
        html += '<span class="pc-cp-divider"></span>';

        // Total line items
        html += '<span class="pc-cp-stat">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg> ' +
            '<strong>' + totalItems + '</strong> total line items' +
        '</span>';

        // Warning or ready indicator
        if (emptyProps.length > 0) {
            html += '<span class="pc-cp-divider"></span>';
            html += '<span class="pc-cp-stat pc-cp-warn">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> ' +
                emptyProps.length + ' proposal' + (emptyProps.length > 1 ? 's' : '') + ' with no line items' +
            '</span>';
        } else if (allReady) {
            html += '<span class="pc-cp-divider"></span>';
            html += '<span class="pc-cp-stat pc-cp-ready">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> ' +
                'Ready to compare' +
            '</span>';
        }

        // ── Multi-term indicator (v5.9.46) ──
        var termCounts = _getTermGroupSummary(State.proposals);
        var termKeys = Object.keys(termCounts);
        var nonEmptyTerms = termKeys.filter(function(k) { return k !== '(none)'; });

        if (nonEmptyTerms.length >= 2) {
            html += '</div>';  // Close current preview row
            html += '<div class="pc-compare-preview pc-term-preview">';
            html += '<span class="pc-cp-stat" style="color:#D6A84A">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D6A84A" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> ' +
                '<strong>Multi-term detected</strong> \u2014 ' + nonEmptyTerms.length + ' term groups will be compared separately' +
            '</span>';
            html += '<span class="pc-cp-divider"></span>';
            nonEmptyTerms.forEach(function(t) {
                html += '<span class="pc-term-badge">' + escHtml(t) + ' (' + termCounts[t] + ')</span> ';
            });
            if (termCounts['(none)']) {
                html += '<span class="pc-term-badge pc-term-badge-none">No term (' + termCounts['(none)'] + ')</span> ';
            }
        }

        html += '</div>';
        return html;
    }

    function renderReviewPhase() {
        State.phase = 'review';
        State._reviewIdx = State._reviewIdx || 0;
        State._lineItemEditorOpen = State._lineItemEditorOpen.length === State.proposals.length
            ? State._lineItemEditorOpen
            : State.proposals.map(function() { return false; });

        const body = document.getElementById('pc-body');
        if (!body) return;

        // Clean up previous blob URLs
        _cleanupBlobUrls();

        var total = State.proposals.length;
        var idx = State._reviewIdx;

        // Build compact project selector for review phase
        var projectBar = '';
        if (State.projects && State.projects.length > 0) {
            var projOpts = '<option value="">No project (ad-hoc)</option>';
            for (var pi = 0; pi < State.projects.length; pi++) {
                var proj = State.projects[pi];
                var psel = State.selectedProjectId === proj.id ? ' selected' : '';
                projOpts += '<option value="' + proj.id + '"' + psel + '>' + escHtml(proj.name) + '</option>';
            }
            projectBar = '<div class="pc-review-project-bar">' +
                '<i data-lucide="folder-open" style="width:14px;height:14px;color:#D6A84A"></i> ' +
                '<span style="font-size:12px;color:var(--text-secondary,#888)">Project:</span> ' +
                '<select id="pc-review-project-select" class="pc-project-select-sm">' + projOpts + '</select>' +
            '</div>';
        }

        // ── v5.9.53: Proposal selection chip bar ──
        var chipBarHtml = '<div class="pc-proposal-chips">';
        chipBarHtml += '<span class="pc-chip-label"><i data-lucide="list-checks" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Proposals:</span>';
        State.proposals.forEach(function(p, pIdx) {
            var name = p.company_name || p.filename || ('Proposal ' + (pIdx + 1));
            var term = p.contract_term ? ' <span class="pc-chip-term">' + escHtml(p.contract_term) + '</span>' : '';
            var total = p.total_amount != null ? ' <span class="pc-chip-total">' + formatMoneyShort(p.total_amount) + '</span>' : '';
            var isSelected = !State._selectMode || State._selectedForCompare.has(pIdx);
            var activeClass = pIdx === idx ? ' pc-chip-viewing' : '';
            var selectedClass = isSelected ? ' pc-chip-selected' : ' pc-chip-excluded';
            var items = (p.line_items?.length || 0) + ' items';
            chipBarHtml += '<button class="pc-proposal-chip' + activeClass + selectedClass + '" data-chip-idx="' + pIdx + '" title="' + escHtml(name) + ' — ' + items + '">' +
                '<span class="pc-chip-check"><input type="checkbox"' + (isSelected ? ' checked' : '') + ' class="pc-chip-cb"></span>' +
                '<span class="pc-chip-name">' + escHtml(truncate(name, 20)) + '</span>' +
                term + total +
            '</button>';
        });
        // Selection action buttons
        var selCount = State._selectMode ? State._selectedForCompare.size : total;
        chipBarHtml += '<span class="pc-chip-divider"></span>';
        chipBarHtml += '<span class="pc-chip-status">' + selCount + ' of ' + total + ' selected</span>';
        chipBarHtml += '</div>';

        body.innerHTML =
            renderPhaseIndicator(3) +
            projectBar +
            chipBarHtml +
            '<div class="pc-review-nav">' +
                '<button class="pc-btn pc-btn-sm pc-btn-ghost" id="pc-review-prev"' +
                    (idx <= 0 ? ' disabled' : '') + '>' +
                    '<i data-lucide="chevron-left"></i> Previous' +
                '</button>' +
                '<span class="pc-review-counter">Proposal ' + (idx + 1) + ' of ' + total + '</span>' +
                '<button class="pc-btn pc-btn-sm pc-btn-ghost" id="pc-review-next"' +
                    (idx >= total - 1 ? ' disabled' : '') + '>' +
                    'Next <i data-lucide="chevron-right"></i>' +
                '</button>' +
            '</div>' +
            '<div id="pc-review-content"></div>' +
            _buildComparePreview() +
            '<div class="pc-upload-actions">' +
                '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">' +
                    '<i data-lucide="arrow-left"></i> Start Over' +
                '</button>' +
                '<button class="pc-btn pc-btn-primary" id="pc-btn-compare">' +
                    '<i data-lucide="git-compare-arrows"></i> ' +
                    (function() {
                        if (State._selectMode && State._selectedForCompare.size < total) {
                            return 'Compare Selected (' + State._selectedForCompare.size + ')';
                        }
                        var tg = _groupByContractTerm(State.proposals);
                        if (tg.isMultiTerm) {
                            var groupCount = Object.keys(tg.groups).length;
                            return 'Compare by Term (' + groupCount + ' groups)';
                        }
                        return 'Compare All ' + total + ' Proposals';
                    })() +
                '</button>' +
            '</div>';

        // Render current proposal split-pane
        _renderReviewProposal(idx);

        // Bind nav
        document.getElementById('pc-review-prev')?.addEventListener('click', function() {
            if (State._reviewIdx > 0) {
                _captureReviewEdits(State._reviewIdx);
                State._reviewIdx--;
                renderReviewPhase();
            }
        });
        document.getElementById('pc-review-next')?.addEventListener('click', function() {
            if (State._reviewIdx < State.proposals.length - 1) {
                _captureReviewEdits(State._reviewIdx);
                State._reviewIdx++;
                renderReviewPhase();
            }
        });
        document.getElementById('pc-btn-compare')?.addEventListener('click', function() {
            // If in select mode and not all selected, run selective comparison
            if (State._selectMode && State._selectedForCompare.size < State.proposals.length && State._selectedForCompare.size >= 2) {
                _startSelectiveComparison(Array.from(State._selectedForCompare));
            } else {
                startComparison();
            }
        });

        // ── Wire proposal chip bar clicks ──
        body.querySelectorAll('.pc-proposal-chip').forEach(function(chip) {
            chip.addEventListener('click', function(e) {
                // If checkbox was clicked, toggle selection
                if (e.target.classList.contains('pc-chip-cb')) {
                    e.stopPropagation();
                    var chipIdx = parseInt(chip.dataset.chipIdx, 10);
                    if (!State._selectMode) {
                        // First checkbox interaction — initialize select mode with all selected
                        State._selectMode = true;
                        State._selectedForCompare = new Set();
                        for (var si = 0; si < State.proposals.length; si++) State._selectedForCompare.add(si);
                    }
                    if (State._selectedForCompare.has(chipIdx)) {
                        State._selectedForCompare.delete(chipIdx);
                    } else {
                        State._selectedForCompare.add(chipIdx);
                    }
                    _captureReviewEdits(State._reviewIdx);
                    renderReviewPhase();
                    return;
                }
                // Otherwise, navigate to that proposal
                var chipIdx = parseInt(chip.dataset.chipIdx, 10);
                if (chipIdx >= 0 && chipIdx < State.proposals.length) {
                    _captureReviewEdits(State._reviewIdx);
                    State._reviewIdx = chipIdx;
                    renderReviewPhase();
                }
            });
        });

        // Bind review-phase project selector
        var reviewProjSelect = document.getElementById('pc-review-project-select');
        if (reviewProjSelect) {
            reviewProjSelect.addEventListener('change', function() {
                var val = this.value;
                State.selectedProjectId = val ? parseInt(val) : null;
                if (State.selectedProjectId) {
                    var proj = State.projects.find(function(p) { return p.id === State.selectedProjectId; });
                    State.projectName = proj ? proj.name : '';
                    // Immediately tag all in-memory proposals to this project
                    _tagAllProposalsToProject(State.selectedProjectId);
                }
                if (window.showToast) {
                    window.showToast(
                        State.selectedProjectId
                            ? 'Proposals will be saved to project: ' + (State.projectName || 'Selected')
                            : 'No project selected — ad-hoc comparison',
                        'info'
                    );
                }
            });
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function _cleanupBlobUrls() {
        State._blobUrls.forEach(function(url) {
            try { URL.revokeObjectURL(url); } catch(e) {}
        });
        State._blobUrls = [];
    }

    // ──────────────────────────────────────────
    // Pre-comparison Validation
    // ──────────────────────────────────────────

    function _validateBeforeCompare() {
        var warnings = [];
        var proposals = State.proposals || [];
        if (proposals.length < 2) {
            warnings.push('Only ' + proposals.length + ' proposal loaded — comparison requires at least 2.');
            return warnings;
        }

        // Check for proposals with no line items
        var emptyProposals = proposals.filter(function(p) {
            return !p.line_items || p.line_items.length === 0;
        });
        if (emptyProposals.length > 0) {
            warnings.push(emptyProposals.length + ' proposal(s) have no line items: ' +
                emptyProposals.map(function(p) { return p.company_name || p.filename; }).join(', '));
        }

        // Check for missing company names
        var noName = proposals.filter(function(p) { return !p.company_name; });
        if (noName.length > 0) {
            warnings.push(noName.length + ' proposal(s) have no company name — vendors will use filenames.');
        }

        // Check for duplicate company names (same vendor, possibly different terms)
        var nameMap = {};
        proposals.forEach(function(p) {
            var key = (p.company_name || '').trim().toLowerCase();
            if (key) {
                nameMap[key] = (nameMap[key] || 0) + 1;
            }
        });
        for (var name in nameMap) {
            if (nameMap[name] > 1) {
                warnings.push('Multiple proposals from "' + name + '" (' + nameMap[name] + ') — ensure contract terms differ for proper distinction.');
            }
        }

        // Check for very low item counts (likely extraction issues)
        proposals.forEach(function(p) {
            if (p.line_items && p.line_items.length > 0 && p.line_items.length < 3) {
                warnings.push((p.company_name || p.filename) + ' has only ' + p.line_items.length + ' line item(s) — check if extraction captured all items.');
            }
        });

        return warnings;
    }

    // ──────────────────────────────────────────
    // Multi-term grouping (v5.9.46)
    // ──────────────────────────────────────────

    /**
     * Group proposals by contract_term.
     * Returns { groups: {termLabel → [proposals]}, excluded: [proposals], isMultiTerm: bool }
     *
     * Multi-term mode activates only when:
     * - 2+ distinct non-empty term values exist
     * - Each term group has 2+ proposals
     * Single-vendor term groups are excluded with a notice.
     */
    function _groupByContractTerm(proposals) {
        var termMap = {};
        proposals.forEach(function(p) {
            var term = (p.contract_term || '').trim();
            if (!term) term = '';
            if (!termMap[term]) termMap[term] = [];
            termMap[term].push(p);
        });

        var termKeys = Object.keys(termMap);

        // Count how many DISTINCT non-empty terms exist
        var nonEmptyTerms = termKeys.filter(function(k) { return k !== ''; });

        // If 0 or 1 distinct terms → single comparison mode
        if (nonEmptyTerms.length < 2) {
            return { groups: null, excluded: [], isMultiTerm: false };
        }

        // Multi-term mode: separate groups, handle excluded
        var groups = {};
        var excluded = [];

        termKeys.forEach(function(term) {
            var termProposals = termMap[term];
            var label = term || 'Unspecified Term';

            if (termProposals.length < 2) {
                // Single vendor in this term — exclude from comparison
                termProposals.forEach(function(p) {
                    excluded.push({ proposal: p, term: label, reason: 'Only one vendor for this term' });
                });
            } else {
                groups[label] = termProposals;
            }
        });

        // If after filtering we only have 0 or 1 group with 2+ proposals, fall back to single mode
        var validGroups = Object.keys(groups);
        if (validGroups.length < 2) {
            return { groups: null, excluded: [], isMultiTerm: false };
        }

        return { groups: groups, excluded: excluded, isMultiTerm: true };
    }

    /**
     * Get a short summary of detected term groups for the review phase.
     */
    function _getTermGroupSummary(proposals) {
        var termCounts = {};
        proposals.forEach(function(p) {
            var term = (p.contract_term || '').trim() || '(none)';
            termCounts[term] = (termCounts[term] || 0) + 1;
        });
        return termCounts;
    }

    // ──────────────────────────────────────────
    // Phase: Comparison
    // ──────────────────────────────────────────

    async function startComparison() {
        // Capture edits for current review proposal
        _captureReviewEdits(State._reviewIdx);

        // ── Pre-comparison validation warnings ──
        var warnings = _validateBeforeCompare();
        if (warnings.length > 0) {
            var proceed = confirm(
                'Pre-Comparison Warnings:\n\n' +
                warnings.map(function(w, i) { return (i + 1) + '. ' + w; }).join('\n') +
                '\n\nProceed with comparison anyway?'
            );
            if (!proceed) return;
        }

        _cleanupBlobUrls();
        State.phase = 'comparing';
        const body = document.getElementById('pc-body');
        if (!body) return;

        // ── Check for multi-term grouping ──
        var termGrouping = _groupByContractTerm(State.proposals);

        if (termGrouping.isMultiTerm) {
            // Multi-term mode: run separate comparisons per term group
            await _startMultiTermComparison(termGrouping, body);
            return;
        }

        // ── Single comparison mode (existing behavior) ──
        body.innerHTML =
            '<div class="pc-loading">' +
                '<div class="pc-spinner"></div>' +
                '<div class="pc-loading-text">Aligning and comparing ' + State.proposals.length + ' proposals...</div>' +
            '</div>';

        State.multiTermMode = false;
        State.multiTermResults = [];

        try {
            var payload = { proposals: State.proposals };
            if (State.selectedProjectId) {
                payload.project_id = State.selectedProjectId;
            }

            var resp = await fetch('/api/proposal-compare/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify(payload),
            });

            var result = await resp.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Comparison failed');
            }

            State.comparison = result.data;
            State.comparisonId = result.data?.comparison_id || null;
            renderResults();

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Comparison error:', err);
            body.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="alert-triangle"></i>' +
                    '<h4>Comparison Failed</h4>' +
                    '<p>' + escHtml(err.message) + '</p>' +
                    '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">' +
                        '<i data-lucide="arrow-left"></i> Try Again' +
                    '</button>' +
                '</div>';
            if (window.lucide) window.lucide.createIcons();
        }
    }

    // ──────────────────────────────────────────
    // Multi-term comparison orchestration (v5.9.46)
    // ──────────────────────────────────────────

    async function _startMultiTermComparison(termGrouping, body) {
        var groups = termGrouping.groups;
        var excluded = termGrouping.excluded;
        var termLabels = Object.keys(groups);

        console.log('[AEGIS ProposalCompare] Multi-term mode: ' + termLabels.length + ' term groups detected: ' + termLabels.join(', '));

        State.multiTermMode = true;
        State.multiTermResults = [];
        State.multiTermActiveIdx = 0;
        State.multiTermExcluded = excluded;

        body.innerHTML =
            '<div class="pc-loading">' +
                '<div class="pc-spinner"></div>' +
                '<div class="pc-loading-text" id="pc-multiterm-progress">' +
                    'Multi-term comparison: Preparing ' + termLabels.length + ' term groups...' +
                '</div>' +
            '</div>';

        try {
            for (var gi = 0; gi < termLabels.length; gi++) {
                var termLabel = termLabels[gi];
                var termProposals = groups[termLabel];

                // Update progress
                var progressEl = document.getElementById('pc-multiterm-progress');
                if (progressEl) {
                    progressEl.textContent = 'Comparing "' + termLabel + '" (' + (gi + 1) + ' of ' + termLabels.length + ') — ' + termProposals.length + ' vendors...';
                }

                var payload = {
                    proposals: termProposals,
                    term_label: termLabel,
                };
                if (State.selectedProjectId) {
                    payload.project_id = State.selectedProjectId;
                }

                var resp = await fetch('/api/proposal-compare/compare', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': getCSRF(),
                    },
                    body: JSON.stringify(payload),
                });

                var result = await resp.json();

                if (!result.success) {
                    console.warn('[AEGIS ProposalCompare] Term "' + termLabel + '" comparison failed:', result.error);
                    State.multiTermResults.push({
                        termLabel: termLabel,
                        comparison: null,
                        comparisonId: null,
                        proposals: termProposals,
                        error: result.error?.message || 'Comparison failed',
                    });
                    continue;
                }

                State.multiTermResults.push({
                    termLabel: termLabel,
                    comparison: result.data,
                    comparisonId: result.data?.comparison_id || null,
                    proposals: termProposals,
                    error: null,
                });
            }

            // Set the first successful result as the active comparison
            var firstValid = State.multiTermResults.find(function(r) { return r.comparison; });
            if (firstValid) {
                State.comparison = firstValid.comparison;
                State.comparisonId = firstValid.comparisonId;
                State.multiTermActiveIdx = State.multiTermResults.indexOf(firstValid);
            }

            renderMultiTermResults();

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Multi-term comparison error:', err);
            body.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="alert-triangle"></i>' +
                    '<h4>Multi-Term Comparison Failed</h4>' +
                    '<p>' + escHtml(err.message) + '</p>' +
                    '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">' +
                        '<i data-lucide="arrow-left"></i> Try Again' +
                    '</button>' +
                '</div>';
            if (window.lucide) window.lucide.createIcons();
        }
    }


    // ──────────────────────────────────────────
    // Multi-term results rendering (v5.9.46)
    // ──────────────────────────────────────────

    function renderMultiTermResults() {
        State.phase = 'results';
        const body = document.getElementById('pc-body');
        if (!body) return;

        destroyCharts();

        var results = State.multiTermResults;
        var excluded = State.multiTermExcluded;
        var activeIdx = State.multiTermActiveIdx;

        // ── Build term selector pills ──
        var termPillsHtml = '<div class="pc-term-selector">';
        termPillsHtml += '<span class="pc-term-selector-label">' +
            '<i data-lucide="calendar-range" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Contract Terms:</span>';

        results.forEach(function(r, idx) {
            var active = idx === activeIdx ? ' active' : '';
            var errorClass = r.error ? ' pc-term-pill-error' : '';
            var vendorCount = r.comparison ? r.comparison.proposals.length : 0;
            termPillsHtml += '<button class="pc-term-pill' + active + errorClass + '" data-term-idx="' + idx + '">' +
                escHtml(r.termLabel) +
                (vendorCount > 0 ? ' <span class="pc-term-pill-count">' + vendorCount + '</span>' : '') +
            '</button>';
        });

        // "All Terms Summary" pill
        termPillsHtml += '<button class="pc-term-pill pc-term-pill-summary' +
            (activeIdx === -1 ? ' active' : '') + '" data-term-idx="-1">' +
            '<i data-lucide="layout-grid" style="width:12px;height:12px;vertical-align:-1px;margin-right:3px"></i>' +
            'All Terms Summary</button>';

        termPillsHtml += '</div>';

        // ── Excluded proposals notice ──
        var excludedHtml = '';
        if (excluded.length > 0) {
            excludedHtml = '<div class="pc-term-excluded-notice">' +
                '<i data-lucide="info" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>' +
                '<strong>' + excluded.length + ' proposal' + (excluded.length > 1 ? 's' : '') + ' excluded</strong> (single vendor in term group): ';
            excludedHtml += excluded.map(function(e) {
                return escHtml((e.proposal.company_name || e.proposal.filename) + ' — ' + e.term);
            }).join(', ');
            excludedHtml += '</div>';
        }

        // ── Results container (reuses standard tab structure) ──
        body.innerHTML =
            '<div class="pc-results">' +
                '<div class="pc-results-header">' +
                    '<h3>Multi-Term Proposal Comparison</h3>' +
                    '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
                        '<button class="pc-btn pc-btn-gold" id="pc-btn-reanalyze">' +
                            '<i data-lucide="refresh-cw"></i> Re-Analyze' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">' +
                            '<i data-lucide="arrow-left"></i> New Compare' +
                        '</button>' +
                        (State.proposals.length > 0
                            ? '<button class="pc-btn pc-btn-ghost" onclick="ProposalCompare._backToReview()">' +
                                '<i data-lucide="pencil"></i> Back to Review' +
                              '</button>'
                            : '') +
                        '<button class="pc-btn pc-btn-ghost" id="pc-btn-add-proposal">' +
                            '<i data-lucide="plus-circle"></i> Add Proposal' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-primary" onclick="ProposalCompare._export()">' +
                            '<i data-lucide="download"></i> Export XLSX' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-gold" onclick="ProposalCompare._exportHTML()">' +
                            '<i data-lucide="globe"></i> Export HTML' +
                        '</button>' +
                    '</div>' +
                '</div>' +
                termPillsHtml +
                excludedHtml +
                '<div id="pc-multiterm-content"></div>' +
            '</div>';

        // Wire term pill clicks
        body.querySelectorAll('.pc-term-pill').forEach(function(pill) {
            pill.addEventListener('click', function() {
                var idx = parseInt(pill.dataset.termIdx, 10);
                _switchMultiTermTab(idx);
            });
        });

        // v5.9.53: Wire Re-Analyze button (multi-term)
        document.getElementById('pc-btn-reanalyze')?.addEventListener('click', function() {
            _restoreAllProposals();
            startComparison();
        });

        // v5.9.53: Wire Add Proposal button (multi-term)
        document.getElementById('pc-btn-add-proposal')?.addEventListener('click', function() {
            _restoreAllProposals();
            State.phase = 'upload';
            State.comparison = null;
            State.comparisonId = null;
            State.multiTermMode = false;
            State.multiTermResults = [];
            renderUploadPhase();
        });

        // Render active term's results
        _renderMultiTermContent(activeIdx);

        if (window.lucide) window.lucide.createIcons();
    }

    function _switchMultiTermTab(idx) {
        State.multiTermActiveIdx = idx;

        // Update pill active states
        document.querySelectorAll('.pc-term-pill').forEach(function(pill) {
            var pillIdx = parseInt(pill.dataset.termIdx, 10);
            pill.classList.toggle('active', pillIdx === idx);
        });

        if (idx >= 0 && State.multiTermResults[idx]) {
            State.comparison = State.multiTermResults[idx].comparison;
            State.comparisonId = State.multiTermResults[idx].comparisonId;
        }

        destroyCharts();
        _renderMultiTermContent(idx);
    }

    function _renderMultiTermContent(idx) {
        var container = document.getElementById('pc-multiterm-content');
        if (!container) return;

        if (idx === -1) {
            // All Terms Summary view
            _renderAllTermsSummary(container);
            return;
        }

        var termResult = State.multiTermResults[idx];
        if (!termResult) return;

        if (termResult.error) {
            container.innerHTML =
                '<div class="pc-empty" style="padding:40px 20px">' +
                    '<i data-lucide="alert-triangle"></i>' +
                    '<h4>Comparison failed for "' + escHtml(termResult.termLabel) + '"</h4>' +
                    '<p>' + escHtml(termResult.error) + '</p>' +
                '</div>';
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        var cmp = termResult.comparison;
        if (!cmp) return;

        var propIds = cmp.proposals.map(function(p) { return p.id || p.company_name || p.filename || 'Unknown'; });

        // Build standard 8-tab structure inside the container
        var tabs = [
            { id: 'executive',  icon: 'trophy',          label: 'Executive Summary' },
            { id: 'comparison', icon: 'table-2',         label: 'Comparison' },
            { id: 'categories', icon: 'pie-chart',       label: 'Categories' },
            { id: 'redflags',   icon: 'shield-alert',    label: 'Red Flags' },
            { id: 'heatmap',    icon: 'grid-3x3',        label: 'Heatmap' },
            { id: 'scores',     icon: 'bar-chart-3',     label: 'Vendor Scores' },
            { id: 'details',    icon: 'info',            label: 'Details' },
            { id: 'tables',     icon: 'table',           label: 'Raw Tables' },
        ];

        var tabsHtml = tabs.map(function(t) {
            var active = t.id === State.activeTab ? ' active' : '';
            return '<button class="pc-tab" data-tab="' + t.id + '"' + active + '>' +
                '<i data-lucide="' + t.icon + '" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>' +
                t.label +
            '</button>';
        }).join('');

        var panelsHtml = tabs.map(function(t) {
            var active = t.id === State.activeTab ? ' active' : '';
            return '<div class="pc-tab-panel' + active + '" id="pc-panel-' + t.id + '"></div>';
        }).join('');

        container.innerHTML =
            '<div class="pc-multiterm-term-header">' +
                '<i data-lucide="calendar" style="width:16px;height:16px;color:#D6A84A;vertical-align:-3px;margin-right:6px"></i>' +
                '<strong>' + escHtml(termResult.termLabel) + '</strong>' +
                ' \u2014 ' + cmp.proposals.length + ' vendors compared' +
            '</div>' +
            '<div class="pc-tabs" id="pc-tabs-bar">' + tabsHtml + '</div>' +
            panelsHtml;

        // Wire tabs
        container.querySelectorAll('.pc-tab').forEach(function(tab) {
            tab.addEventListener('click', function() {
                container.querySelectorAll('.pc-tab').forEach(function(t) { t.classList.remove('active'); });
                container.querySelectorAll('.pc-tab-panel').forEach(function(p) { p.classList.remove('active'); });
                tab.classList.add('active');
                var panel = document.getElementById('pc-panel-' + tab.dataset.tab);
                if (panel) panel.classList.add('active');
                State.activeTab = tab.dataset.tab;
            });
        });

        // Render each tab (reuses exact same functions as single-term mode)
        renderExecutiveSummary(propIds, cmp);
        renderComparisonTable(propIds, cmp);
        renderCategoriesTab(propIds, cmp);
        renderRedFlagsTab(propIds, cmp);
        renderHeatmapTab(propIds, cmp);
        renderVendorScoresTab(propIds, cmp);
        renderDetailsTab(cmp);
        renderTablesTab(cmp);

        if (window.lucide) window.lucide.createIcons();
    }


    /**
     * All Terms Summary — cross-term overview showing vendors across all terms.
     */
    function _renderAllTermsSummary(container) {
        var results = State.multiTermResults.filter(function(r) { return r.comparison; });

        if (results.length === 0) {
            container.innerHTML = '<div class="pc-empty"><h4>No completed comparisons</h4></div>';
            return;
        }

        // Collect all unique vendors (case-insensitive) and all terms
        var allVendors = {};
        var allTerms = [];

        results.forEach(function(r) {
            allTerms.push(r.termLabel);
            (r.comparison.proposals || []).forEach(function(p) {
                var vendorKey = (p.company_name || p.filename || 'Unknown').trim().toLowerCase();
                if (!allVendors[vendorKey]) {
                    allVendors[vendorKey] = { name: p.company_name || p.filename || 'Unknown', terms: {} };
                }
                // Store total for this vendor in this term
                var pid = p.id || p.company_name || p.filename;
                var total = r.comparison.totals ? r.comparison.totals[pid] : null;
                allVendors[vendorKey].terms[r.termLabel] = {
                    total: total,
                    totalFormatted: total ? '$' + total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '\u2014',
                    proposalId: pid,
                    lineItems: (r.comparison.proposals.find(function(pp) { return (pp.id || pp.company_name) === pid; }) || {}).line_item_count || 0,
                };
            });
        });

        var vendorKeys = Object.keys(allVendors).sort();

        // ── Hero stats ──
        var html = '<div class="pc-multiterm-term-header">' +
            '<i data-lucide="layout-grid" style="width:16px;height:16px;color:#D6A84A;vertical-align:-3px;margin-right:6px"></i>' +
            '<strong>All Terms Summary</strong>' +
            ' \u2014 ' + allTerms.length + ' terms, ' + vendorKeys.length + ' unique vendors' +
        '</div>';

        html += '<div class="pc-exec-heroes" style="margin-bottom:20px">';
        html += renderHeroCard('calendar-range', allTerms.length, 'Contract Terms', '#2196f3');
        html += renderHeroCard('users', vendorKeys.length, 'Unique Vendors', '#D6A84A');
        html += renderHeroCard('file-text', State.multiTermResults.reduce(function(sum, r) {
            return sum + (r.comparison ? r.comparison.proposals.length : 0);
        }, 0), 'Total Proposals', '#8b949e');

        // Total line items across all terms
        var totalItems = results.reduce(function(sum, r) {
            return sum + (r.comparison.aligned_items || []).length;
        }, 0);
        html += renderHeroCard('layers', totalItems, 'Total Line Items', '#4CAF50');
        html += '</div>';

        // ── Cross-term comparison table ──
        html += '<div style="overflow-x:auto">';
        html += '<table class="pc-comparison-table">';
        html += '<thead><tr><th>Vendor</th>';
        allTerms.forEach(function(t) {
            html += '<th>' + escHtml(t) + '</th>';
        });
        html += '<th>Lowest Term</th>';
        html += '</tr></thead><tbody>';

        vendorKeys.forEach(function(vk) {
            var vendor = allVendors[vk];
            var lowestTerm = null;
            var lowestTotal = Infinity;

            html += '<tr>';
            html += '<td><strong>' + escHtml(vendor.name) + '</strong></td>';

            allTerms.forEach(function(t) {
                var data = vendor.terms[t];
                if (data && data.total != null) {
                    html += '<td class="pc-amount">' + data.totalFormatted +
                        '<br><small style="color:var(--text-secondary,#888)">' + data.lineItems + ' items</small></td>';
                    if (data.total < lowestTotal) {
                        lowestTotal = data.total;
                        lowestTerm = t;
                    }
                } else {
                    html += '<td style="color:var(--text-secondary,#888);text-align:center">\u2014</td>';
                }
            });

            // Lowest term for this vendor
            html += '<td>';
            if (lowestTerm) {
                html += '<span class="pc-term-badge pc-term-badge-best">' + escHtml(lowestTerm) + '</span>';
            } else {
                html += '\u2014';
            }
            html += '</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';

        // ── v5.9.53: Year-over-Year % Change by Line Item ──
        // Only if 2+ terms have successful comparisons
        if (results.length >= 2) {
            // Build line-item-level data per vendor per term
            // { vendorKey: { lineItemDesc: { termLabel: amount } } }
            var yoyData = {};
            results.forEach(function(r) {
                if (!r.comparison) return;
                var items = r.comparison.aligned_items || [];
                items.forEach(function(item) {
                    var amounts = item.amounts || {};
                    for (var pid in amounts) {
                        if (amounts[pid] == null || amounts[pid] <= 0) continue;
                        // Find vendor name for this pid
                        var prop = (r.comparison.proposals || []).find(function(p) {
                            return (p.id || p.company_name || p.filename) === pid;
                        });
                        var vendorName = prop ? (prop.company_name || prop.filename || 'Unknown') : pid;
                        var vendorKey = vendorName.trim().toLowerCase();
                        if (!yoyData[vendorKey]) yoyData[vendorKey] = { name: vendorName, items: {} };
                        var desc = (item.description || 'Unnamed item').trim();
                        if (!yoyData[vendorKey].items[desc]) yoyData[vendorKey].items[desc] = {};
                        yoyData[vendorKey].items[desc][r.termLabel] = amounts[pid];
                    }
                });
            });

            // Check if any vendor has data across multiple terms
            var hasYoY = false;
            for (var vk in yoyData) {
                for (var desc in yoyData[vk].items) {
                    var termCount = Object.keys(yoyData[vk].items[desc]).length;
                    if (termCount >= 2) { hasYoY = true; break; }
                }
                if (hasYoY) break;
            }

            if (hasYoY) {
                html += '<h4 style="margin-top:24px;margin-bottom:12px">' +
                    '<i data-lucide="trending-up" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px"></i>' +
                    'Year-over-Year % Change by Line Item</h4>';

                var yoyVendorKeys = Object.keys(yoyData).sort();
                yoyVendorKeys.forEach(function(vk) {
                    var vendor = yoyData[vk];
                    var itemDescs = Object.keys(vendor.items).sort();

                    // Filter to items with data in 2+ terms
                    var multiTermItems = itemDescs.filter(function(d) {
                        return Object.keys(vendor.items[d]).length >= 2;
                    });
                    if (multiTermItems.length === 0) return;

                    html += '<div style="margin-bottom:16px">' +
                        '<h5 style="margin:0 0 8px;font-size:13px;color:var(--text-primary,#333)">' +
                            '<i data-lucide="building-2" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;color:#D6A84A"></i>' +
                            escHtml(vendor.name) +
                            ' <span style="font-weight:400;color:var(--text-secondary,#888)">(' + multiTermItems.length + ' comparable items)</span>' +
                        '</h5>';

                    html += '<div class="pc-table-wrap"><table class="pc-table">';
                    html += '<thead><tr><th style="min-width:200px">Line Item</th>';
                    allTerms.forEach(function(t) {
                        html += '<th>' + escHtml(t) + '</th>';
                    });
                    // Add YoY % columns between consecutive terms
                    for (var ti = 1; ti < allTerms.length; ti++) {
                        html += '<th style="color:#D6A84A">\u0394 ' + escHtml(allTerms[ti - 1]) + ' \u2192 ' + escHtml(allTerms[ti]) + '</th>';
                    }
                    html += '</tr></thead><tbody>';

                    multiTermItems.forEach(function(desc) {
                        var termData = vendor.items[desc];
                        html += '<tr>';
                        html += '<td title="' + escHtml(desc) + '">' + truncate(desc, 50) + '</td>';

                        allTerms.forEach(function(t) {
                            var amt = termData[t];
                            if (amt != null) {
                                html += '<td class="pc-amount">$' + amt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '</td>';
                            } else {
                                html += '<td class="pc-amount-missing">\u2014</td>';
                            }
                        });

                        // Compute % change between consecutive terms
                        for (var ti = 1; ti < allTerms.length; ti++) {
                            var prev = termData[allTerms[ti - 1]];
                            var curr = termData[allTerms[ti]];
                            if (prev != null && prev > 0 && curr != null) {
                                var pctChange = ((curr - prev) / prev) * 100;
                                var sign = pctChange >= 0 ? '+' : '';
                                var colorClass = pctChange > 10 ? 'pc-variance-high'
                                    : pctChange > 0 ? 'pc-variance-mid'
                                    : pctChange < -10 ? 'pc-variance-low'
                                    : 'pc-variance-low';
                                html += '<td class="pc-variance ' + colorClass + '">' + sign + pctChange.toFixed(1) + '%</td>';
                            } else {
                                html += '<td class="pc-amount-missing">\u2014</td>';
                            }
                        }

                        html += '</tr>';
                    });

                    // Summary row — total across terms
                    html += '<tr class="pc-total-row"><td><strong>Total</strong></td>';
                    var termTotals = {};
                    allTerms.forEach(function(t) {
                        var sum = 0;
                        multiTermItems.forEach(function(desc) {
                            if (vendor.items[desc][t] != null) sum += vendor.items[desc][t];
                        });
                        termTotals[t] = sum;
                        html += '<td class="pc-amount"><strong>$' + sum.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '</strong></td>';
                    });
                    // Total YoY %
                    for (var ti = 1; ti < allTerms.length; ti++) {
                        var prevTotal = termTotals[allTerms[ti - 1]];
                        var currTotal = termTotals[allTerms[ti]];
                        if (prevTotal > 0 && currTotal > 0) {
                            var pctChange = ((currTotal - prevTotal) / prevTotal) * 100;
                            var sign = pctChange >= 0 ? '+' : '';
                            var colorClass = pctChange > 10 ? 'pc-variance-high'
                                : pctChange > 0 ? 'pc-variance-mid'
                                : 'pc-variance-low';
                            html += '<td class="pc-variance ' + colorClass + '"><strong>' + sign + pctChange.toFixed(1) + '%</strong></td>';
                        } else {
                            html += '<td class="pc-amount-missing">\u2014</td>';
                        }
                    }
                    html += '</tr>';

                    html += '</tbody></table></div></div>';
                });
            }
        }

        // ── Vendor presence matrix ──
        html += '<h4 style="margin-top:24px;margin-bottom:12px">' +
            '<i data-lucide="check-square" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px"></i>' +
            'Vendor Presence by Term</h4>';
        html += '<div style="overflow-x:auto">';
        html += '<table class="pc-comparison-table">';
        html += '<thead><tr><th>Vendor</th>';
        allTerms.forEach(function(t) {
            html += '<th>' + escHtml(t) + '</th>';
        });
        html += '<th>Coverage</th></tr></thead><tbody>';

        vendorKeys.forEach(function(vk) {
            var vendor = allVendors[vk];
            var present = 0;
            html += '<tr>';
            html += '<td><strong>' + escHtml(vendor.name) + '</strong></td>';
            allTerms.forEach(function(t) {
                if (vendor.terms[t]) {
                    html += '<td style="text-align:center;color:#4CAF50"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></td>';
                    present++;
                } else {
                    html += '<td style="text-align:center;color:var(--text-secondary,#666)">\u2014</td>';
                }
            });
            var pct = Math.round((present / allTerms.length) * 100);
            html += '<td style="text-align:center"><strong>' + pct + '%</strong> (' + present + '/' + allTerms.length + ')</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';

        // Excluded notice
        if (State.multiTermExcluded.length > 0) {
            html += '<div class="pc-term-excluded-notice" style="margin-top:20px">' +
                '<i data-lucide="info" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>' +
                '<strong>Excluded from comparison:</strong> ';
            html += State.multiTermExcluded.map(function(e) {
                return escHtml((e.proposal.company_name || e.proposal.filename) + ' (' + e.term + ')');
            }).join(', ');
            html += '</div>';
        }

        container.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }


    // ──────────────────────────────────────────
    // Phase: Results
    // ──────────────────────────────────────────

    function renderResults() {
        State.phase = 'results';
        const body = document.getElementById('pc-body');
        if (!body) return;

        destroyCharts();

        var cmp = State.comparison;
        if (!cmp) return;

        var propIds = cmp.proposals.map(function(p) { return p.id || p.company_name || p.filename || 'Unknown'; });

        // Determine available tabs based on data
        var tabs = [
            { id: 'executive',  icon: 'trophy',          label: 'Executive Summary', always: true },
            { id: 'comparison', icon: 'table-2',         label: 'Comparison',        always: true },
            { id: 'categories', icon: 'pie-chart',       label: 'Categories',        always: true },
            { id: 'redflags',   icon: 'shield-alert',    label: 'Red Flags',         always: true },
            { id: 'heatmap',    icon: 'grid-3x3',        label: 'Heatmap',           always: true },
            { id: 'scores',     icon: 'bar-chart-3',     label: 'Vendor Scores',     always: true },
            { id: 'details',    icon: 'info',            label: 'Details',           always: true },
            { id: 'tables',     icon: 'table',           label: 'Raw Tables',        always: true },
        ];

        var tabsHtml = tabs.map(function(t) {
            var active = t.id === State.activeTab ? ' active' : '';
            return '<button class="pc-tab' + active + '" data-tab="' + t.id + '">' +
                '<i data-lucide="' + t.icon + '" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>' +
                t.label +
            '</button>';
        }).join('');

        var panelsHtml = tabs.map(function(t) {
            var active = t.id === State.activeTab ? ' active' : '';
            return '<div class="pc-tab-panel' + active + '" id="pc-panel-' + t.id + '"></div>';
        }).join('');

        // v5.9.53: Vendor filter chips for results (toggle vendors in/out with live recalculation)
        var vendorChipsHtml = '';
        if (cmp.proposals.length > 2) {
            vendorChipsHtml = '<div class="pc-results-vendor-filter">' +
                '<span class="pc-chip-label"><i data-lucide="filter" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Filter Vendors:</span>';
            cmp.proposals.forEach(function(vp, vpIdx) {
                var name = vp.id || vp.company_name || vp.filename || ('Vendor ' + (vpIdx + 1));
                vendorChipsHtml += '<button class="pc-vendor-chip pc-vendor-chip-on" data-vendor-idx="' + vpIdx + '" data-vendor-id="' + escHtml(name) + '">' +
                    '<span class="pc-vchip-check">\u2713</span> ' + escHtml(truncate(name, 18)) +
                '</button>';
            });
            vendorChipsHtml += '<button class="pc-btn pc-btn-xs pc-btn-ghost" id="pc-vendor-reset" style="margin-left:8px">' +
                '<i data-lucide="rotate-ccw" style="width:12px;height:12px"></i> Reset</button>';
            vendorChipsHtml += '</div>';
        }

        body.innerHTML =
            '<div class="pc-results">' +
                '<div class="pc-results-header">' +
                    '<h3>Proposal Comparison \u2014 ' + cmp.proposals.length + ' Proposals</h3>' +
                    '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
                        '<button class="pc-btn pc-btn-gold" id="pc-btn-reanalyze">' +
                            '<i data-lucide="refresh-cw"></i> Re-Analyze' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">' +
                            '<i data-lucide="arrow-left"></i> New Compare' +
                        '</button>' +
                        (State.proposals.length > 0
                            ? '<button class="pc-btn pc-btn-ghost" onclick="ProposalCompare._backToReview()">' +
                                '<i data-lucide="pencil"></i> Back to Review' +
                              '</button>'
                            : '') +
                        '<button class="pc-btn pc-btn-ghost" id="pc-btn-add-proposal">' +
                            '<i data-lucide="plus-circle"></i> Add Proposal' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-ghost" id="pc-results-tag-project">' +
                            '<i data-lucide="folder-plus"></i> Tag to Project' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-primary" onclick="ProposalCompare._export()">' +
                            '<i data-lucide="download"></i> Export XLSX' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-gold" onclick="ProposalCompare._exportHTML()">' +
                            '<i data-lucide="globe"></i> Export Interactive HTML' +
                        '</button>' +
                    '</div>' +
                '</div>' +
                vendorChipsHtml +
                '<div class="pc-tabs" id="pc-tabs-bar">' + tabsHtml + '</div>' +
                panelsHtml +
            '</div>';

        // Wire tabs
        body.querySelectorAll('.pc-tab').forEach(function(tab) {
            tab.addEventListener('click', function() {
                body.querySelectorAll('.pc-tab').forEach(function(t) { t.classList.remove('active'); });
                body.querySelectorAll('.pc-tab-panel').forEach(function(p) { p.classList.remove('active'); });
                tab.classList.add('active');
                var panel = document.getElementById('pc-panel-' + tab.dataset.tab);
                if (panel) panel.classList.add('active');
                State.activeTab = tab.dataset.tab;
            });
        });

        // Wire "Tag to Project" button in results header
        var tagProjBtn = document.getElementById('pc-results-tag-project');
        if (tagProjBtn) {
            tagProjBtn.addEventListener('click', function(e) {
                // Show project dropdown with all proposals from this comparison
                _showResultsTagToProjectMenu(e.target.closest('#pc-results-tag-project') || tagProjBtn);
            });
        }

        // v5.9.53: Wire Re-Analyze button
        document.getElementById('pc-btn-reanalyze')?.addEventListener('click', function() {
            _restoreAllProposals(); // restore full set if was selective
            startComparison();
        });

        // v5.9.53: Wire Add Proposal button — return to upload preserving existing proposals
        document.getElementById('pc-btn-add-proposal')?.addEventListener('click', function() {
            _restoreAllProposals();
            State.phase = 'upload';
            State.comparison = null;
            State.comparisonId = null;
            State.multiTermMode = false;
            State.multiTermResults = [];
            // Keep State.proposals intact — renderUploadPhase will show them as "already loaded"
            renderUploadPhase();
        });

        // v5.9.53: Wire vendor filter chips (toggle vendors in/out of results view)
        body.querySelectorAll('.pc-vendor-chip').forEach(function(vChip) {
            vChip.addEventListener('click', function() {
                vChip.classList.toggle('pc-vendor-chip-on');
                vChip.classList.toggle('pc-vendor-chip-off');
                var checkSpan = vChip.querySelector('.pc-vchip-check');
                if (checkSpan) checkSpan.textContent = vChip.classList.contains('pc-vendor-chip-on') ? '\u2713' : '';
                // Rebuild comparison data with filtered vendors
                _applyVendorFilter();
            });
        });
        document.getElementById('pc-vendor-reset')?.addEventListener('click', function() {
            body.querySelectorAll('.pc-vendor-chip').forEach(function(vc) {
                vc.classList.add('pc-vendor-chip-on');
                vc.classList.remove('pc-vendor-chip-off');
                var cs = vc.querySelector('.pc-vchip-check');
                if (cs) cs.textContent = '\u2713';
            });
            _applyVendorFilter();
        });

        // Render each tab
        renderExecutiveSummary(propIds, cmp);
        renderComparisonTable(propIds, cmp);
        renderCategoriesTab(propIds, cmp);
        renderRedFlagsTab(propIds, cmp);
        renderHeatmapTab(propIds, cmp);
        renderVendorScoresTab(propIds, cmp);
        renderDetailsTab(cmp);
        renderTablesTab(cmp);

        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Tab: Executive Summary
    // ──────────────────────────────────────────

    function renderExecutiveSummary(propIds, cmp) {
        var panel = document.getElementById('pc-panel-executive');
        if (!panel) return;

        var exec = cmp.executive_summary || {};
        var scores = cmp.vendor_scores || {};
        var html = '';

        // ── Hero stats row ──
        var totalFlags = 0;
        var redFlags = cmp.red_flags || {};
        for (var pid in redFlags) {
            totalFlags += (redFlags[pid] || []).length;
        }
        var totalSavings = exec.total_potential_savings_formatted || '\u2014';
        var lineItemCount = exec.total_line_items || (cmp.aligned_items || []).length;

        // v5.9.43: Compute unique vendor count (by company name, case-insensitive)
        var uniqueVendors = {};
        (cmp.proposals || []).forEach(function(pr) {
            var base = (pr.company_name || pr.filename || '').trim().toLowerCase();
            if (base) uniqueVendors[base] = true;
        });
        var vendorCount = Object.keys(uniqueVendors).length;

        html += '<div class="pc-exec-heroes">';
        html += renderHeroCard('layers', lineItemCount, 'Line Items Compared', '#2196f3');
        html += renderHeroCard('users', vendorCount, 'Unique Vendors', '#D6A84A');
        if (propIds.length > vendorCount) {
            html += renderHeroCard('file-text', propIds.length, 'Proposals', '#8b949e');
        }
        html += renderHeroCard('shield-alert', totalFlags, 'Red Flags', totalFlags > 0 ? '#f44336' : '#219653');
        html += renderHeroCard('piggy-bank', totalSavings, 'Potential Savings', '#219653');
        html += '</div>';

        // ── Price Ranking ──
        var priceRanking = exec.price_ranking || [];
        if (priceRanking.length > 0) {
            html += '<div class="pc-exec-section">';
            html += '<h4 class="pc-exec-section-title"><i data-lucide="trophy" style="width:16px;height:16px;color:#D6A84A"></i> Price Ranking</h4>';
            html += '<div class="pc-exec-ranking">';
            priceRanking.forEach(function(pr) {
                var medalClass = pr.rank === 1 ? 'pc-rank-gold' : pr.rank === 2 ? 'pc-rank-silver' : 'pc-rank-bronze';
                var deltaStr = pr.delta_pct > 0 ? '+' + pr.delta_pct.toFixed(1) + '%' : '\u2014';
                var vidx = propIds.indexOf(pr.vendor);
                html += '<div class="pc-rank-card ' + medalClass + '">' +
                    '<div class="pc-rank-num">#' + pr.rank + '</div>' +
                    '<div class="pc-rank-vendor">' + vendorBadge(pr.vendor, vidx >= 0 ? vidx : pr.rank - 1) + '</div>' +
                    '<div class="pc-rank-total">' + (pr.total_formatted || formatMoney(pr.total)) + '</div>' +
                    '<div class="pc-rank-delta">' + deltaStr + '</div>' +
                '</div>';
            });
            html += '</div></div>';
        }

        // ── Score Ranking ──
        var scoreRanking = exec.score_ranking || [];
        if (scoreRanking.length > 0) {
            html += '<div class="pc-exec-section">';
            html += '<h4 class="pc-exec-section-title"><i data-lucide="bar-chart-3" style="width:16px;height:16px;color:#D6A84A"></i> Score Ranking</h4>';
            html += '<div class="pc-exec-ranking">';
            scoreRanking.forEach(function(sr) {
                var gc = gradeColor(sr.grade);
                var vidx = propIds.indexOf(sr.vendor);
                html += '<div class="pc-rank-card">' +
                    '<div class="pc-rank-num" style="color:' + gc + '">#' + sr.rank + '</div>' +
                    '<div class="pc-rank-vendor">' + vendorBadge(sr.vendor, vidx >= 0 ? vidx : sr.rank - 1) + '</div>' +
                    '<div class="pc-score-badge" style="background:' + gc + '">' + sr.grade + '</div>' +
                    '<div class="pc-rank-delta">' + sr.overall_score + '/100</div>' +
                '</div>';
            });
            html += '</div></div>';
        }

        // ── Key Findings ──
        var findings = exec.key_findings || [];
        if (findings.length > 0) {
            html += '<div class="pc-exec-section">';
            html += '<h4 class="pc-exec-section-title"><i data-lucide="lightbulb" style="width:16px;height:16px;color:#D6A84A"></i> Key Findings</h4>';
            html += '<div class="pc-findings-list">';
            findings.forEach(function(f) {
                var sc = severityColor(f.severity);
                var sb = severityBg(f.severity);
                html += '<div class="pc-finding-card" style="border-left:3px solid ' + sc + ';background:' + sb + '">' +
                    '<span class="pc-finding-badge" style="background:' + sc + ';color:#fff">' + (f.severity || 'info').toUpperCase() + '</span>' +
                    '<span class="pc-finding-text">' + escHtml(f.text) + '</span>' +
                '</div>';
            });
            html += '</div></div>';
        }

        // ── Negotiation Opportunities ──
        var negot = exec.negotiation_opportunities || [];
        if (negot.length > 0) {
            html += '<div class="pc-exec-section">';
            html += '<h4 class="pc-exec-section-title"><i data-lucide="handshake" style="width:16px;height:16px;color:#D6A84A"></i> Top Negotiation Opportunities</h4>';

            // Tornado chart — shows line items with largest price spread
            html += '<div class="pc-chart-container" id="pc-chart-tornado-wrap">' +
                '<canvas id="pc-chart-tornado" height="280"></canvas>' +
            '</div>';

            html += '<div class="pc-table-wrap"><table class="pc-table">';
            html += '<thead><tr>' +
                '<th>Vendor</th><th>Line Item</th><th>Current</th><th>Average</th><th>Potential Savings</th><th>Variance</th>' +
            '</tr></thead><tbody>';
            negot.forEach(function(n) {
                html += '<tr>' +
                    '<td>' + escHtml(n.vendor) + '</td>' +
                    '<td title="' + escHtml(n.line_item) + '">' + truncate(n.line_item, 40) + '</td>' +
                    '<td class="pc-amount">' + formatMoney(n.current_amount) + '</td>' +
                    '<td class="pc-amount">' + formatMoney(n.avg_amount) + '</td>' +
                    '<td class="pc-amount pc-amount-lowest">' + (n.savings_formatted || formatMoney(n.potential_savings)) + '</td>' +
                    '<td class="pc-variance">' + formatVariance(n.variance_pct) + '</td>' +
                '</tr>';
            });
            html += '</tbody></table></div>';
            html += '</div>';
        }

        // ── Price Spread / Tornado Chart (from aligned items) ──
        var aligned = cmp.aligned_items || [];
        if (aligned.length > 0 && negot.length === 0) {
            // If no negotiation opportunities computed, show tornado from aligned items
            html += '<div class="pc-exec-section">';
            html += '<h4 class="pc-exec-section-title"><i data-lucide="bar-chart-horizontal" style="width:16px;height:16px;color:#D6A84A"></i> Price Spread Analysis</h4>';
            html += '<div class="pc-chart-container" id="pc-chart-tornado-wrap">' +
                '<canvas id="pc-chart-tornado" height="280"></canvas>' +
            '</div>';
            html += '</div>';
        }

        panel.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();

        // Render tornado chart
        renderTornadoChart(cmp);
    }

    function renderHeroCard(icon, value, label, color) {
        return '<div class="pc-exec-hero">' +
            '<div class="pc-exec-hero-icon" style="background:' + color + '20;color:' + color + '">' +
                '<i data-lucide="' + icon + '" style="width:20px;height:20px"></i>' +
            '</div>' +
            '<div class="pc-exec-hero-value">' + value + '</div>' +
            '<div class="pc-exec-hero-label">' + label + '</div>' +
        '</div>';
    }

    // ──────────────────────────────────────────
    // Weight Sliders (Phase 3.1)
    // ──────────────────────────────────────────

    function renderWeightSlider(key, label, value, color) {
        return '<div class="pc-weight-row">' +
            '<label class="pc-weight-label">' + label + '</label>' +
            '<input type="range" class="pc-weight-slider" id="pc-wt-' + key + '" ' +
                'min="0" max="100" step="5" value="' + value + '" ' +
                'style="accent-color:' + color + '">' +
            '<span class="pc-weight-value" id="pc-wt-val-' + key + '">' + value + '%</span>' +
        '</div>';
    }

    function wireWeightSliders(propIds, cmp, scores) {
        var defaults = { price: 40, completeness: 25, risk: 25, data_quality: 10 };
        if (!State._weights) State._weights = Object.assign({}, defaults);

        var keys = ['price', 'completeness', 'risk', 'data_quality'];
        var scoreKeys = ['price_score', 'completeness_score', 'risk_score', 'data_quality_score'];
        var _debounceTimer = null;

        function updateTotal() {
            var total = 0;
            keys.forEach(function(k) { total += State._weights[k]; });
            var el = document.getElementById('pc-weight-total');
            if (el) {
                el.textContent = total + '%';
                el.style.color = total === 100 ? 'var(--success, #219653)' : '#f44336';
            }
        }

        function recalcScores() {
            var w = State._weights;
            var totalW = w.price + w.completeness + w.risk + w.data_quality;
            if (totalW <= 0) return;

            // Recalculate overall scores with new weights
            for (var i = 0; i < propIds.length; i++) {
                var pid = propIds[i];
                var vs = scores[pid];
                if (!vs) continue;

                vs.overall = Math.round(
                    (vs.price_score * w.price +
                     vs.completeness_score * w.completeness +
                     vs.risk_score * w.risk +
                     vs.data_quality_score * w.data_quality) / totalW
                );

                // Recalc grade
                if (vs.overall >= 90) vs.grade = 'A';
                else if (vs.overall >= 80) vs.grade = 'B';
                else if (vs.overall >= 70) vs.grade = 'C';
                else if (vs.overall >= 60) vs.grade = 'D';
                else vs.grade = 'F';
            }

            // Update score cards in-place (don't re-render entire tab)
            propIds.forEach(function(pid) {
                var vs = scores[pid];
                if (!vs) return;
                var gc = gradeColor(vs.grade);

                // Update overall number
                var panel = document.getElementById('pc-panel-scores');
                if (!panel) return;
                var cards = panel.querySelectorAll('.pc-score-card');
                cards.forEach(function(card) {
                    var vendorEl = card.querySelector('.pc-score-vendor');
                    if (!vendorEl || vendorEl.textContent !== pid) return;
                    var numEl = card.querySelector('.pc-score-num');
                    if (numEl) numEl.textContent = vs.overall;
                    var gradeEl = card.querySelector('.pc-score-grade');
                    if (gradeEl) {
                        gradeEl.textContent = vs.grade;
                        gradeEl.style.background = gc;
                    }
                    var circleEl = card.querySelector('.pc-score-circle');
                    if (circleEl) circleEl.style.borderColor = gc;
                });
            });

            // Rebuild charts with new scores
            destroyChartById('pc-chart-radar');
            destroyChartById('pc-chart-scores');
            renderRadarChart(propIds, scores);
            renderScoresChart(propIds, scores);
        }

        function destroyChartById(canvasId) {
            var canvas = document.getElementById(canvasId);
            if (!canvas) return;
            var chartInstance = Chart.getChart(canvas);
            if (chartInstance) {
                chartInstance.destroy();
                var idx = State._charts.indexOf(chartInstance);
                if (idx >= 0) State._charts.splice(idx, 1);
            }
        }

        keys.forEach(function(key) {
            var slider = document.getElementById('pc-wt-' + key);
            if (!slider) return;

            slider.addEventListener('input', function() {
                var val = parseInt(this.value, 10);
                State._weights[key] = val;
                var valEl = document.getElementById('pc-wt-val-' + key);
                if (valEl) valEl.textContent = val + '%';
                updateTotal();

                // Debounce recalc
                clearTimeout(_debounceTimer);
                _debounceTimer = setTimeout(recalcScores, 200);
            });
        });

        var resetBtn = document.getElementById('pc-weight-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                State._weights = Object.assign({}, defaults);
                keys.forEach(function(key) {
                    var slider = document.getElementById('pc-wt-' + key);
                    if (slider) slider.value = defaults[key];
                    var valEl = document.getElementById('pc-wt-val-' + key);
                    if (valEl) valEl.textContent = defaults[key] + '%';
                });
                updateTotal();
                recalcScores();
            });
        }

        updateTotal();
    }

    // ──────────────────────────────────────────
    // Chart: Tornado (Negotiation Impact)
    // ──────────────────────────────────────────

    function renderTornadoChart(cmp) {
        if (!window.Chart) return;
        var canvas = document.getElementById('pc-chart-tornado');
        if (!canvas) return;

        // Build spread data from aligned items or negotiation opportunities
        var items = [];
        var aligned = cmp.aligned_items || [];
        for (var i = 0; i < aligned.length; i++) {
            var item = aligned[i];
            var amounts = item.amounts || {};
            var valid = [];
            for (var k in amounts) {
                if (amounts[k] != null && amounts[k] > 0) valid.push(amounts[k]);
            }
            if (valid.length < 2) continue;
            var minAmt = Math.min.apply(null, valid);
            var maxAmt = Math.max.apply(null, valid);
            var spread = maxAmt - minAmt;
            if (spread <= 0) continue;
            items.push({
                description: item.description || 'Unknown',
                spread: spread,
                min: minAmt,
                max: maxAmt,
                avg: valid.reduce(function(a, b) { return a + b; }, 0) / valid.length,
                variance_pct: minAmt > 0 ? ((maxAmt - minAmt) / minAmt * 100) : 0,
            });
        }

        // Sort by spread descending, take top 12
        items.sort(function(a, b) { return b.spread - a.spread; });
        items = items.slice(0, 12);

        if (items.length === 0) {
            // Show helpful message instead of just hiding
            canvas.parentElement.innerHTML =
                '<div class="pc-chart-empty">' +
                    '<i data-lucide="git-compare" style="width:24px;height:24px;color:#8b949e"></i>' +
                    '<p>No price spreads to display — items need 2+ vendor prices for comparison.</p>' +
                '</div>';
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        // Adjust canvas height based on item count
        var barHeight = items.length > 8 ? 30 : 36;
        canvas.height = Math.max(200, items.length * barHeight + 80);

        _applyChartDefaults();
        var textColor = _getChartTextColor();
        var secondaryColor = _getChartSecondaryColor();

        try {
            var chart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: items.map(function(it) {
                        return it.description.length > 35 ? it.description.substring(0, 32) + '...' : it.description;
                    }),
                    datasets: [{
                        label: 'Price Spread (Max - Min)',
                        data: items.map(function(it) { return it.spread; }),
                        backgroundColor: items.map(function(it) {
                            // Color by variance intensity
                            if (it.variance_pct > 50) return 'rgba(244,67,54,0.8)';
                            if (it.variance_pct > 25) return 'rgba(255,152,0,0.8)';
                            return 'rgba(214,168,74,0.8)';
                        }),
                        borderWidth: 0,
                        borderRadius: 4,
                        borderSkipped: false,
                        barPercentage: 0.85,
                        categoryPercentage: 0.9,
                    }],
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        title: {
                            display: true,
                            text: 'Biggest Price Spreads — Where to Focus Negotiations',
                            color: textColor,
                            font: { size: 13, weight: '600' },
                            padding: { bottom: 12 },
                        },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    var it = items[ctx.dataIndex];
                                    return [
                                        'Spread: ' + formatMoney(it.spread),
                                        'Range: ' + formatMoney(it.min) + ' – ' + formatMoney(it.max),
                                        'Variance: ' + it.variance_pct.toFixed(1) + '%',
                                    ];
                                },
                            },
                        },
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(v) { return formatMoneyShort(v); },
                                color: secondaryColor,
                                font: { size: 11 },
                            },
                            grid: { color: _getChartGridColor() },
                        },
                        y: {
                            ticks: {
                                color: textColor,
                                font: { size: 11 },
                            },
                            grid: { display: false },
                        },
                    },
                },
            });
            State._charts.push(chart);
        } catch (e) {
            console.warn('[AEGIS ProposalCompare] Tornado chart error:', e);
        }
    }

    // ──────────────────────────────────────────
    // Tab: Comparison (existing, preserved)
    // ──────────────────────────────────────────

    function renderComparisonTable(propIds, cmp) {
        var panel = document.getElementById('pc-panel-comparison');
        if (!panel) return;

        var items = cmp.aligned_items || [];
        if (items.length === 0) {
            panel.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="search-x"></i>' +
                    '<h4>No Financial Line Items Found</h4>' +
                    '<p>No extractable financial data was found in the uploaded proposals.</p>' +
                '</div>';
            return;
        }

        // Store for interactive re-rendering
        State._compItems = items;
        State._compPropIds = propIds;
        State._compCmp = cmp;
        State._compSort = State._compSort || { col: 'category', dir: 'asc' };
        State._compFilter = State._compFilter || { minVariance: 0, category: null };

        _renderComparisonInner(panel, propIds, cmp);
    }

    function _renderComparisonInner(panel, propIds, cmp) {
        var items = State._compItems || cmp.aligned_items || [];
        var sort = State._compSort;
        var filter = State._compFilter;

        // Apply filters
        var filtered = items.filter(function(item) {
            if (filter.minVariance > 0 && (item.variance_pct || 0) < filter.minVariance) return false;
            if (filter.category && item.category !== filter.category) return false;
            return true;
        });

        // Sort
        var sorted = filtered.slice().sort(function(a, b) {
            var dir = sort.dir === 'asc' ? 1 : -1;
            if (sort.col === 'category') {
                var catCmp = (a.category || 'zzz').localeCompare(b.category || 'zzz');
                if (catCmp !== 0) return catCmp * dir;
                return (a.description || '').localeCompare(b.description || '') * dir;
            } else if (sort.col === 'description') {
                return (a.description || '').localeCompare(b.description || '') * dir;
            } else if (sort.col === 'variance') {
                return ((a.variance_pct || 0) - (b.variance_pct || 0)) * dir;
            } else {
                // Sort by vendor amount
                var aAmt = a.amounts?.[sort.col] || 0;
                var bAmt = b.amounts?.[sort.col] || 0;
                return (aAmt - bAmt) * dir;
            }
        });

        // ── Filter bar ──
        var categories = {};
        items.forEach(function(it) {
            var c = it.category || 'Uncategorized';
            categories[c] = (categories[c] || 0) + 1;
        });

        var html = '<div class="pc-comp-filters">' +
            '<div class="pc-comp-filter-row">' +
                '<span class="pc-comp-filter-label">Filter:</span>' +
                '<select class="pc-comp-filter-cat" id="pc-comp-filter-cat">' +
                    '<option value="">All Categories</option>';
        Object.keys(categories).sort().forEach(function(cat) {
            var sel = filter.category === cat ? ' selected' : '';
            html += '<option value="' + escHtml(cat) + '"' + sel + '>' + escHtml(cat) + ' (' + categories[cat] + ')</option>';
        });
        html += '</select>' +
                '<select class="pc-comp-filter-var" id="pc-comp-filter-var">' +
                    '<option value="0"' + (filter.minVariance === 0 ? ' selected' : '') + '>All Variance</option>' +
                    '<option value="10"' + (filter.minVariance === 10 ? ' selected' : '') + '>&gt; 10% spread</option>' +
                    '<option value="20"' + (filter.minVariance === 20 ? ' selected' : '') + '>&gt; 20% spread</option>' +
                    '<option value="50"' + (filter.minVariance === 50 ? ' selected' : '') + '>&gt; 50% spread</option>' +
                '</select>' +
                '<span class="pc-comp-count">' + filtered.length + ' of ' + items.length + ' items</span>' +
            '</div>' +
        '</div>';

        // ── Sortable header icons ──
        function sortIcon(col) {
            if (sort.col !== col) return ' <span class="pc-sort-icon">\u2195</span>';
            return sort.dir === 'asc'
                ? ' <span class="pc-sort-icon pc-sort-active">\u2191</span>'
                : ' <span class="pc-sort-icon pc-sort-active">\u2193</span>';
        }

        // Build table
        html += '<div class="pc-table-wrap"><table class="pc-table pc-comp-table">' +
            '<thead><tr>' +
                '<th class="pc-sortable" data-sort="description" style="min-width:200px">Line Item' + sortIcon('description') + '</th>' +
                '<th class="pc-sortable" data-sort="category">Category' + sortIcon('category') + '</th>' +
                propIds.map(function(id, idx) {
                    return '<th class="pc-sortable" data-sort="' + escHtml(id) + '" style="min-width:150px">' + vendorBadge(id, idx) + sortIcon(id) + '</th>';
                }).join('') +
                '<th class="pc-sortable" data-sort="variance">Variance' + sortIcon('variance') + '</th>' +
            '</tr></thead>' +
            '<tbody>';

        var currentCategory = null;
        for (var i = 0; i < sorted.length; i++) {
            var item = sorted[i];
            // Category header (only when sorted by category)
            if (sort.col === 'category' && item.category !== currentCategory) {
                currentCategory = item.category;
                html += '<tr class="pc-category-header">' +
                    '<td colspan="' + (propIds.length + 3) + '">' + escHtml(currentCategory || 'Uncategorized') + '</td>' +
                '</tr>';
            }

            var amounts = item.amounts || {};
            var valid = [];
            for (var k in amounts) {
                if (amounts[k] != null && amounts[k] > 0) valid.push(amounts[k]);
            }
            var minAmt = valid.length ? Math.min.apply(null, valid) : null;
            var maxAmt = valid.length > 1 ? Math.max.apply(null, valid) : null;

            html += '<tr>' +
                '<td title="' + escHtml(item.description) + '">' + truncate(item.description, 60) + '</td>' +
                '<td>' + escHtml(item.category || '') + '</td>';

            for (var j = 0; j < propIds.length; j++) {
                var pid = propIds[j];
                var amt = amounts[pid];
                if (amt != null) {
                    var cls = 'pc-amount';
                    if (valid.length > 1) {
                        if (amt === minAmt) cls += ' pc-amount-lowest';
                        else if (amt === maxAmt) cls += ' pc-amount-highest';
                    }
                    html += '<td class="' + cls + '">' + formatMoney(amt) + '</td>';
                } else {
                    html += '<td class="pc-amount pc-amount-missing">\u2014</td>';
                }
            }

            html += '<td class="pc-variance">' + formatVariance(item.variance_pct) + '</td>';
            html += '</tr>';
        }

        // Grand total row
        html += '<tr class="pc-total-row">' +
            '<td>GRAND TOTAL</td>' +
            '<td></td>';
        for (var j = 0; j < propIds.length; j++) {
            var total = cmp.totals?.[propIds[j]];
            html += '<td class="pc-amount">' + formatMoney(total) + '</td>';
        }
        html += '<td class="pc-variance">' + formatVariance(cmp.total_variance_pct) + '</td>';
        html += '</tr>';

        html += '</tbody></table></div>';

        // Summary notes
        if (cmp.notes && cmp.notes.length) {
            html += '<div class="pc-notes">' +
                cmp.notes.map(function(n) { return '<div>\u2022 ' + escHtml(n) + '</div>'; }).join('') +
            '</div>';
        }

        panel.innerHTML = html;

        // Wire sort/filter events
        panel.querySelectorAll('.pc-sortable').forEach(function(th) {
            th.addEventListener('click', function() {
                var col = this.getAttribute('data-sort');
                if (State._compSort.col === col) {
                    State._compSort.dir = State._compSort.dir === 'asc' ? 'desc' : 'asc';
                } else {
                    State._compSort = { col: col, dir: 'asc' };
                }
                _renderComparisonInner(panel, propIds, cmp);
            });
        });

        var catFilter = document.getElementById('pc-comp-filter-cat');
        if (catFilter) {
            catFilter.addEventListener('change', function() {
                State._compFilter.category = this.value || null;
                _renderComparisonInner(panel, propIds, cmp);
            });
        }

        var varFilter = document.getElementById('pc-comp-filter-var');
        if (varFilter) {
            varFilter.addEventListener('change', function() {
                State._compFilter.minVariance = parseInt(this.value, 10) || 0;
                _renderComparisonInner(panel, propIds, cmp);
            });
        }
    }

    // ──────────────────────────────────────────
    // Tab: Categories (existing, enhanced with chart)
    // ──────────────────────────────────────────

    function renderCategoriesTab(propIds, cmp) {
        var panel = document.getElementById('pc-panel-categories');
        if (!panel) return;

        var cats = cmp.category_summaries || [];
        if (cats.length === 0) {
            panel.innerHTML = '<div class="pc-empty"><h4>No category data</h4></div>';
            return;
        }

        // Chart canvas (optional — rendered if Chart.js available)
        var html = '<div class="pc-chart-container" id="pc-chart-categories-wrap">' +
            '<canvas id="pc-chart-categories" height="280"></canvas>' +
        '</div>';

        html += '<div class="pc-table-wrap"><table class="pc-table">' +
            '<thead><tr>' +
                '<th>Category</th>' +
                '<th>Items</th>' +
                propIds.map(function(id) { return '<th>' + escHtml(id) + '</th>'; }).join('') +
            '</tr></thead>' +
            '<tbody>';

        for (var i = 0; i < cats.length; i++) {
            var cat = cats[i];
            html += '<tr>' +
                '<td><strong>' + escHtml(cat.category) + '</strong></td>' +
                '<td>' + cat.item_count + '</td>';

            var totals = cat.totals || {};
            var validTotals = [];
            for (var k in totals) {
                if (totals[k] > 0) validTotals.push(totals[k]);
            }
            var minT = validTotals.length ? Math.min.apply(null, validTotals) : null;
            var maxT = validTotals.length > 1 ? Math.max.apply(null, validTotals) : null;

            for (var j = 0; j < propIds.length; j++) {
                var t = totals[propIds[j]];
                var cls = 'pc-amount';
                if (t && validTotals.length > 1) {
                    if (t === minT) cls += ' pc-amount-lowest';
                    else if (t === maxT) cls += ' pc-amount-highest';
                }
                html += '<td class="' + cls + '">' + (t ? formatMoney(t) : '\u2014') + '</td>';
            }
            html += '</tr>';
        }

        html += '</tbody></table></div>';
        panel.innerHTML = html;

        // Render chart if Chart.js is available
        renderCategoriesChart(propIds, cats);
    }

    function renderCategoriesChart(propIds, cats) {
        if (!window.Chart) return;
        var canvas = document.getElementById('pc-chart-categories');
        if (!canvas) return;

        var chartColors = [
            'rgba(214,168,74,0.8)', 'rgba(33,150,83,0.8)', 'rgba(47,128,237,0.8)',
            'rgba(235,87,87,0.8)', 'rgba(155,89,182,0.8)', 'rgba(241,196,15,0.8)',
            'rgba(26,188,156,0.8)', 'rgba(230,126,34,0.8)', 'rgba(52,73,94,0.8)',
            'rgba(149,165,166,0.8)',
        ];

        var datasets = propIds.map(function(pid, idx) {
            return {
                label: pid,
                data: cats.map(function(c) { return c.totals?.[pid] || 0; }),
                backgroundColor: chartColors[idx % chartColors.length],
                borderWidth: 0,
                borderRadius: 3,
            };
        });

        _applyChartDefaults();
        var textColor = _getChartTextColor();
        var secondaryColor = _getChartSecondaryColor();

        try {
            var chart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: cats.map(function(c) { return c.category; }),
                    datasets: datasets,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: textColor,
                                usePointStyle: true,
                                pointStyleWidth: 12,
                                padding: 16,
                                font: { size: 11 },
                            },
                        },
                        title: {
                            display: true,
                            text: 'Cost Breakdown by Category',
                            color: textColor,
                            font: { size: 14, weight: '600' },
                            padding: { bottom: 12 },
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': ' + formatMoney(ctx.raw);
                                },
                                footer: function(tooltipItems) {
                                    var sum = 0;
                                    tooltipItems.forEach(function(ti) { sum += ti.raw; });
                                    return 'Total: ' + formatMoney(sum);
                                },
                            },
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(v) { return formatMoneyShort(v); },
                                color: secondaryColor,
                                font: { size: 11 },
                            },
                            grid: { color: _getChartGridColor() },
                        },
                        x: {
                            ticks: {
                                color: secondaryColor,
                                font: { size: 11 },
                                maxRotation: 45,
                            },
                            grid: { display: false },
                        },
                    },
                },
            });
            State._charts.push(chart);
        } catch(e) {
            console.warn('[AEGIS ProposalCompare] Chart render error:', e);
        }
    }

    // ──────────────────────────────────────────
    // Tab: Red Flags
    // ──────────────────────────────────────────

    function renderRedFlagsTab(propIds, cmp) {
        var panel = document.getElementById('pc-panel-redflags');
        if (!panel) return;

        var redFlags = cmp.red_flags || {};
        var totalFlags = 0;
        for (var pid in redFlags) {
            totalFlags += (redFlags[pid] || []).length;
        }

        if (totalFlags === 0) {
            panel.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="shield-check"></i>' +
                    '<h4>No Red Flags Detected</h4>' +
                    '<p>All proposals passed automated risk checks.</p>' +
                '</div>';
            return;
        }

        var html = '<div class="pc-rf-summary">' +
            '<div class="pc-rf-summary-stat">' +
                '<span class="pc-rf-count">' + totalFlags + '</span>' +
                '<span class="pc-rf-label">Total Red Flags</span>' +
            '</div>';

        // Count by severity
        var sevCounts = { critical: 0, warning: 0, info: 0 };
        for (var pid in redFlags) {
            (redFlags[pid] || []).forEach(function(f) {
                sevCounts[f.severity || 'info'] = (sevCounts[f.severity || 'info'] || 0) + 1;
            });
        }
        if (sevCounts.critical > 0) {
            html += '<div class="pc-rf-summary-stat">' +
                '<span class="pc-rf-count" style="color:#f44336">' + sevCounts.critical + '</span>' +
                '<span class="pc-rf-label">Critical</span>' +
            '</div>';
        }
        if (sevCounts.warning > 0) {
            html += '<div class="pc-rf-summary-stat">' +
                '<span class="pc-rf-count" style="color:#ff9800">' + sevCounts.warning + '</span>' +
                '<span class="pc-rf-label">Warning</span>' +
            '</div>';
        }
        if (sevCounts.info > 0) {
            html += '<div class="pc-rf-summary-stat">' +
                '<span class="pc-rf-count" style="color:#2196f3">' + sevCounts.info + '</span>' +
                '<span class="pc-rf-label">Info</span>' +
            '</div>';
        }
        html += '</div>';

        // Cards by vendor
        for (var i = 0; i < propIds.length; i++) {
            var pid = propIds[i];
            var flags = redFlags[pid] || [];
            if (flags.length === 0) continue;

            // Sort: critical first, then warning, then info
            flags.sort(function(a, b) {
                var sevOrder = { critical: 0, warning: 1, info: 2 };
                return (sevOrder[a.severity] || 3) - (sevOrder[b.severity] || 3);
            });

            html += '<div class="pc-rf-vendor">';
            html += '<h4 class="pc-rf-vendor-title">' +
                '<i data-lucide="building-2" style="width:16px;height:16px;color:#D6A84A"></i> ' +
                escHtml(pid) +
                ' <span class="pc-rf-vendor-count">(' + flags.length + ' flag' + (flags.length !== 1 ? 's' : '') + ')</span>' +
            '</h4>';

            flags.forEach(function(flag) {
                var sc = severityColor(flag.severity);
                var sb = severityBg(flag.severity);
                html += '<div class="pc-rf-card" style="border-left:4px solid ' + sc + ';background:' + sb + '">' +
                    '<div class="pc-rf-card-header">' +
                        '<span class="pc-rf-badge" style="background:' + sc + '">' + (flag.severity || '').toUpperCase() + '</span>' +
                        '<span class="pc-rf-type">' + escHtml(flag.type || '').replace(/_/g, ' ') + '</span>' +
                    '</div>' +
                    '<div class="pc-rf-card-title">' + escHtml(flag.title || '') + '</div>' +
                    '<div class="pc-rf-card-detail">' + escHtml(flag.detail || '') + '</div>' +
                '</div>';
            });

            html += '</div>';
        }

        panel.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Tab: Heatmap
    // ──────────────────────────────────────────

    function renderHeatmapTab(propIds, cmp) {
        var panel = document.getElementById('pc-panel-heatmap');
        if (!panel) return;

        var heatmap = cmp.heatmap || {};
        var rows = heatmap.rows || [];

        if (rows.length === 0) {
            panel.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="grid-3x3"></i>' +
                    '<h4>No Heatmap Data</h4>' +
                    '<p>Not enough comparable data to build a heatmap.</p>' +
                '</div>';
            return;
        }

        var hmPropIds = heatmap.prop_ids || propIds;

        // Legend (use runtime colors for dark mode consistency)
        var html = '<div class="pc-hm-legend">' +
            '<span class="pc-hm-legend-label">Deviation from average:</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('very_low') + ';color:' + heatmapTextColor('very_low') + '">&lt; -15%</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('low') + ';color:' + heatmapTextColor('low') + '">-5% to -15%</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('neutral') + ';color:' + heatmapTextColor('neutral') + '">\u00b15%</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('high') + ';color:' + heatmapTextColor('high') + '">+5% to +15%</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('very_high') + ';color:' + heatmapTextColor('very_high') + '">&gt; +15%</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('single_vendor') + ';color:' + heatmapTextColor('single_vendor') + '">Only Vendor</span>' +
            '<span class="pc-hm-swatch" style="background:' + heatmapColor('missing') + ';color:' + heatmapTextColor('missing') + '">Missing</span>' +
        '</div>';

        // Table
        html += '<div class="pc-table-wrap"><table class="pc-table pc-hm-table">';
        html += '<thead><tr>' +
            '<th style="min-width:200px">Line Item</th>' +
            '<th>Category</th>' +
            '<th>Average</th>' +
            hmPropIds.map(function(id) { return '<th>' + escHtml(id) + '</th>'; }).join('') +
        '</tr></thead><tbody>';

        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var cells = row.cells || {};

            html += '<tr>' +
                '<td title="' + escHtml(row.description) + '">' + truncate(row.description, 50) + '</td>' +
                '<td>' + escHtml(row.category || '') + '</td>' +
                '<td class="pc-amount">' + formatMoney(row.avg) + '</td>';

            for (var j = 0; j < hmPropIds.length; j++) {
                var pid = hmPropIds[j];
                var cell = cells[pid] || { level: 'missing', amount: null, deviation_pct: null };
                var bg = heatmapColor(cell.level);
                var fg = heatmapTextColor(cell.level);

                var cellContent = '';
                if (cell.amount != null) {
                    var devText = '';
                    if (cell.level === 'single_vendor') {
                        devText = '<span style="opacity:0.6;font-style:italic">only vendor</span>';
                    } else if (cell.deviation_pct != null) {
                        devText = (cell.deviation_pct > 0 ? '+' : '') + cell.deviation_pct.toFixed(1) + '%';
                    }
                    cellContent = formatMoney(cell.amount) +
                        '<div class="pc-hm-dev">' + devText + '</div>';
                } else {
                    cellContent = '\u2014';
                }

                html += '<td class="pc-hm-cell" style="background:' + bg + ';color:' + fg + '">' + cellContent + '</td>';
            }

            html += '</tr>';
        }

        html += '</tbody></table></div>';

        panel.innerHTML = html;
    }

    // ──────────────────────────────────────────
    // Tab: Vendor Scores
    // ──────────────────────────────────────────

    function renderVendorScoresTab(propIds, cmp) {
        var panel = document.getElementById('pc-panel-scores');
        if (!panel) return;

        var scores = cmp.vendor_scores || {};
        if (Object.keys(scores).length === 0) {
            panel.innerHTML =
                '<div class="pc-empty">' +
                    '<i data-lucide="bar-chart-3"></i>' +
                    '<h4>No Vendor Scores Available</h4>' +
                    '<p>Insufficient data to compute vendor scores.</p>' +
                '</div>';
            return;
        }

        // ── Weight Sliders ──
        var weights = State._weights || { price: 40, completeness: 25, risk: 25, data_quality: 10 };
        var html = '<div class="pc-weight-panel">' +
            '<div class="pc-weight-header">' +
                '<i data-lucide="sliders-horizontal" style="width:16px;height:16px;color:#D6A84A"></i>' +
                '<span>Evaluation Weights</span>' +
                '<span class="pc-weight-total" id="pc-weight-total">' + (weights.price + weights.completeness + weights.risk + weights.data_quality) + '%</span>' +
                '<button class="pc-weight-reset" id="pc-weight-reset" title="Reset to defaults">Reset</button>' +
            '</div>' +
            '<div class="pc-weight-sliders">' +
                renderWeightSlider('price', 'Price', weights.price, '#D6A84A') +
                renderWeightSlider('completeness', 'Completeness', weights.completeness, '#2196f3') +
                renderWeightSlider('risk', 'Risk', weights.risk, '#219653') +
                renderWeightSlider('data_quality', 'Data Quality', weights.data_quality, '#9c27b0') +
            '</div>' +
        '</div>';

        // Chart containers — radar (primary) + bar (secondary)
        html += '<div class="pc-scores-charts">' +
            '<div class="pc-chart-container" id="pc-chart-radar-wrap">' +
                '<canvas id="pc-chart-radar" height="380"></canvas>' +
            '</div>' +
            '<div class="pc-chart-container" id="pc-chart-scores-wrap">' +
                '<canvas id="pc-chart-scores" height="280"></canvas>' +
            '</div>' +
        '</div>';

        // Score cards
        html += '<div class="pc-scores-grid">';

        for (var i = 0; i < propIds.length; i++) {
            var pid = propIds[i];
            var vs = scores[pid];
            if (!vs) continue;

            var gc = gradeColor(vs.grade);

            html += '<div class="pc-score-card">' +
                '<div class="pc-score-card-header">' +
                    '<div class="pc-score-vendor">' + escHtml(pid) + '</div>' +
                    '<div class="pc-score-grade" style="background:' + gc + '">' + vs.grade + '</div>' +
                '</div>' +
                '<div class="pc-score-overall">' +
                    '<div class="pc-score-circle" style="border-color:' + gc + '">' +
                        '<span class="pc-score-num">' + vs.overall + '</span>' +
                    '</div>' +
                    '<div class="pc-score-label">Overall Score</div>' +
                '</div>' +
                '<div class="pc-score-bars">' +
                    renderScoreBar('Price', vs.price_score, '#D6A84A') +
                    renderScoreBar('Completeness', vs.completeness_score, '#2196f3') +
                    renderScoreBar('Risk', vs.risk_score, vs.risk_score >= 70 ? '#219653' : '#f44336') +
                    renderScoreBar('Data Quality', vs.data_quality_score, '#9c27b0') +
                '</div>' +
                '<div class="pc-score-footer">' +
                    '<span><i data-lucide="shield-alert" style="width:12px;height:12px;color:#f44336"></i> ' +
                        vs.red_flag_count + ' flag' + (vs.red_flag_count !== 1 ? 's' : '') +
                        (vs.critical_flags > 0 ? ' (' + vs.critical_flags + ' critical)' : '') +
                    '</span>' +
                '</div>' +
            '</div>';
        }

        html += '</div>';
        panel.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();

        // Render charts
        renderRadarChart(propIds, scores);
        renderScoresChart(propIds, scores);

        // Wire up weight sliders
        wireWeightSliders(propIds, cmp, scores);
    }

    function renderScoreBar(label, value, color) {
        var pct = Math.min(100, Math.max(0, value || 0));
        if (pct === 0) {
            return '<div class="pc-score-bar-row">' +
                '<div class="pc-score-bar-label">' + label + '</div>' +
                '<div class="pc-score-bar-track">' +
                    '<div class="pc-score-bar-fill pc-score-bar-empty" style="width:100%;background:' + _getChartGridColor() + '"></div>' +
                '</div>' +
                '<div class="pc-score-bar-value" style="opacity:0.5;font-style:italic">N/A</div>' +
            '</div>';
        }
        return '<div class="pc-score-bar-row">' +
            '<div class="pc-score-bar-label">' + label + '</div>' +
            '<div class="pc-score-bar-track">' +
                '<div class="pc-score-bar-fill" style="width:' + pct + '%;background:' + color + '"></div>' +
            '</div>' +
            '<div class="pc-score-bar-value">' + pct + '</div>' +
        '</div>';
    }

    function renderRadarChart(propIds, scores) {
        if (!window.Chart) return;
        var canvas = document.getElementById('pc-chart-radar');
        if (!canvas) return;

        var radarColors = [
            { bg: 'rgba(214,168,74,0.2)', border: 'rgba(214,168,74,0.9)' },
            { bg: 'rgba(33,150,83,0.2)', border: 'rgba(33,150,83,0.9)' },
            { bg: 'rgba(47,128,237,0.2)', border: 'rgba(47,128,237,0.9)' },
            { bg: 'rgba(235,87,87,0.2)', border: 'rgba(235,87,87,0.9)' },
            { bg: 'rgba(155,89,182,0.2)', border: 'rgba(155,89,182,0.9)' },
            { bg: 'rgba(241,196,15,0.2)', border: 'rgba(241,196,15,0.9)' },
            { bg: 'rgba(26,188,156,0.2)', border: 'rgba(26,188,156,0.9)' },
            { bg: 'rgba(230,126,34,0.2)', border: 'rgba(230,126,34,0.9)' },
        ];

        var axes = ['Price', 'Completeness', 'Risk', 'Data Quality'];
        var axisKeys = ['price_score', 'completeness_score', 'risk_score', 'data_quality_score'];

        var datasets = [];
        for (var i = 0; i < propIds.length; i++) {
            var pid = propIds[i];
            var vs = scores[pid];
            if (!vs) continue;
            var ci = i % radarColors.length;
            datasets.push({
                label: pid,
                data: axisKeys.map(function(k) { return vs[k] || 0; }),
                backgroundColor: radarColors[ci].bg,
                borderColor: radarColors[ci].border,
                borderWidth: 2,
                pointBackgroundColor: radarColors[ci].border,
                pointBorderColor: '#fff',
                pointRadius: 4,
                pointHoverRadius: 6,
            });
        }

        _applyChartDefaults();
        var radarTextColor = _getChartTextColor();
        var radarSecondary = _getChartSecondaryColor();
        var radarGrid = _getChartGridColor();

        try {
            var chart = new Chart(canvas.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: axes,
                    datasets: datasets,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: radarTextColor,
                                usePointStyle: true,
                                padding: 16,
                                font: { size: 11 },
                            },
                        },
                        title: {
                            display: true,
                            text: 'Vendor Comparison Radar',
                            color: radarTextColor,
                            font: { size: 14, weight: '600' },
                            padding: { bottom: 12 },
                        },
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            suggestedMax: 100,
                            ticks: {
                                stepSize: 25,
                                display: true,
                                color: radarSecondary,
                                font: { size: 10 },
                                backdropColor: 'transparent',
                                showLabelBackdrop: false,
                            },
                            grid: { color: radarGrid },
                            pointLabels: {
                                color: radarTextColor,
                                font: { size: 13, weight: '600' },
                                padding: 8,
                            },
                            angleLines: { color: radarGrid },
                        },
                    },
                },
            });
            State._charts.push(chart);
        } catch (e) {
            console.warn('[AEGIS ProposalCompare] Radar chart error:', e);
        }
    }

    function renderScoresChart(propIds, scores) {
        if (!window.Chart) return;
        var canvas = document.getElementById('pc-chart-scores');
        if (!canvas) return;

        var chartColors = [
            'rgba(214,168,74,0.8)', 'rgba(33,150,83,0.8)', 'rgba(47,128,237,0.8)',
            'rgba(235,87,87,0.8)', 'rgba(155,89,182,0.8)',
        ];

        var components = ['price_score', 'completeness_score', 'risk_score', 'data_quality_score'];
        var componentLabels = ['Price (40%)', 'Completeness (25%)', 'Risk (25%)', 'Data Quality (10%)'];

        var datasets = components.map(function(comp, idx) {
            return {
                label: componentLabels[idx],
                data: propIds.map(function(pid) { return scores[pid]?.[comp] || 0; }),
                backgroundColor: chartColors[idx % chartColors.length],
                borderWidth: 0,
                borderRadius: 3,
            };
        });

        // Truncate long vendor names for x-axis labels
        var xLabels = propIds.map(function(pid) {
            return pid.length > 25 ? pid.substring(0, 22) + '...' : pid;
        });

        _applyChartDefaults();
        var scTextColor = _getChartTextColor();
        var scSecondary = _getChartSecondaryColor();

        try {
            var chart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: xLabels,
                    datasets: datasets,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: scTextColor,
                                usePointStyle: true,
                                pointStyleWidth: 12,
                                padding: 16,
                                font: { size: 11 },
                            },
                        },
                        title: {
                            display: true,
                            text: 'Vendor Score Components',
                            color: scTextColor,
                            font: { size: 14, weight: '600' },
                            padding: { bottom: 16 },
                        },
                        tooltip: {
                            callbacks: {
                                title: function(ctx) {
                                    // Show full vendor name in tooltip
                                    return propIds[ctx[0].dataIndex] || ctx[0].label;
                                },
                            },
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                color: scSecondary,
                                font: { size: 11 },
                            },
                            grid: { color: _getChartGridColor() },
                        },
                        x: {
                            ticks: {
                                color: scSecondary,
                                font: { size: 11 },
                                maxRotation: 35,
                                minRotation: 0,
                            },
                            grid: { display: false },
                        },
                    },
                },
            });
            State._charts.push(chart);
        } catch(e) {
            console.warn('[AEGIS ProposalCompare] Scores chart error:', e);
        }
    }

    // ──────────────────────────────────────────
    // Tab: Details (existing, preserved)
    // ──────────────────────────────────────────

    function renderDetailsTab(cmp) {
        var panel = document.getElementById('pc-panel-details');
        if (!panel) return;

        var proposals = cmp.proposals || [];
        var html = '<div class="pc-extraction-summary">';

        for (var i = 0; i < proposals.length; i++) {
            var p = proposals[i];
            html += '<div class="pc-proposal-card">' +
                '<div class="pc-proposal-card-header">' +
                    '<div class="pc-card-icon">' +
                        '<i data-lucide="building-2"></i>' +
                    '</div>' +
                    '<h4>' + escHtml(p.company_name || p.filename) + '</h4>' +
                '</div>' +
                '<div class="pc-card-stats">' +
                    '<div class="pc-card-stat">' +
                        '<div class="pc-card-stat-value">' + escHtml(p.total_raw || '\u2014') + '</div>' +
                        '<div class="pc-card-stat-label">Total Amount</div>' +
                    '</div>' +
                    '<div class="pc-card-stat">' +
                        '<div class="pc-card-stat-value">' + (p.line_item_count || 0) + '</div>' +
                        '<div class="pc-card-stat-label">Line Items</div>' +
                    '</div>' +
                    '<div class="pc-card-stat">' +
                        '<div class="pc-card-stat-value">' + (p.table_count || 0) + '</div>' +
                        '<div class="pc-card-stat-label">Tables</div>' +
                    '</div>' +
                    '<div class="pc-card-stat">' +
                        '<div class="pc-card-stat-value">' + escHtml((p.file_type || '').toUpperCase() || '\u2014') + '</div>' +
                        '<div class="pc-card-stat-label">File Type</div>' +
                    '</div>' +
                '</div>';

            if (p.extraction_notes && p.extraction_notes.length) {
                html += '<div class="pc-notes">' +
                    p.extraction_notes.map(function(n) { return '<div>\u2022 ' + escHtml(n) + '</div>'; }).join('') +
                '</div>';
            }
            html += '</div>';
        }

        html += '</div>';
        panel.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Tab: Raw Tables (existing, preserved)
    // ──────────────────────────────────────────

    function renderTablesTab(cmp) {
        var panel = document.getElementById('pc-panel-tables');
        if (!panel) return;

        var proposals = cmp.proposals || [];
        var html = '';

        for (var i = 0; i < proposals.length; i++) {
            var p = proposals[i];
            var propData = null;
            for (var k = 0; k < State.proposals.length; k++) {
                if (State.proposals[k].filename === p.filename) {
                    propData = State.proposals[k];
                    break;
                }
            }
            if (!propData || !propData.tables || !propData.tables.length) continue;

            html += '<h4 class="pc-raw-table-title">' + escHtml(p.company_name || p.filename) + '</h4>';

            for (var t = 0; t < propData.tables.length; t++) {
                var table = propData.tables[t];
                if (!table.rows || !table.rows.length) continue;

                var finBadge = table.has_financial_data
                    ? '<span class="pc-fin-badge">Financial</span>'
                    : '';

                html += '<div class="pc-raw-table-block">' +
                    '<div class="pc-raw-table-label">' +
                        escHtml(table.source) + ' \u2014 ' + table.rows.length + ' rows ' + finBadge +
                    '</div>' +
                    '<div class="pc-table-wrap">' +
                        '<table class="pc-table">' +
                            '<thead><tr>' +
                                table.headers.map(function(h) { return '<th>' + escHtml(h || '') + '</th>'; }).join('') +
                            '</tr></thead>' +
                            '<tbody>' +
                                table.rows.slice(0, 50).map(function(row) {
                                    return '<tr>' + row.map(function(cell) {
                                        return '<td>' + escHtml(String(cell || '')) + '</td>';
                                    }).join('') + '</tr>';
                                }).join('') +
                                (table.rows.length > 50
                                    ? '<tr><td colspan="' + table.headers.length + '" class="pc-truncation-notice">... ' +
                                      (table.rows.length - 50) + ' more rows</td></tr>'
                                    : '') +
                            '</tbody>' +
                        '</table>' +
                    '</div>' +
                '</div>';
            }
        }

        if (!html) {
            html = '<div class="pc-empty"><h4>No tables extracted</h4></div>';
        }

        panel.innerHTML = html;
    }

    // ──────────────────────────────────────────
    // Comparison History
    // ──────────────────────────────────────────

    async function renderHistoryView() {
        var body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML =
            '<div class="pc-history-view">' +
                '<div class="pc-history-header">' +
                    '<h3><i data-lucide="history" style="width:20px;height:20px;vertical-align:-3px;margin-right:6px"></i>Comparison History</h3>' +
                    '<button class="pc-btn pc-btn-ghost pc-btn-sm" onclick="ProposalCompare._restart()">' +
                        '<i data-lucide="arrow-left"></i> Back to Upload' +
                    '</button>' +
                '</div>' +
                '<div class="pc-history-list" id="pc-history-list">' +
                    '<div class="pc-loading"><i data-lucide="loader" class="spin"></i> Loading history...</div>' +
                '</div>' +
            '</div>';

        if (window.lucide) window.lucide.createIcons();

        // Fetch history
        try {
            var resp = await fetch('/api/proposal-compare/history', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            if (!json.success || !json.data || json.data.length === 0) {
                document.getElementById('pc-history-list').innerHTML =
                    '<div class="pc-empty">' +
                        '<i data-lucide="inbox" style="width:48px;height:48px;opacity:0.3"></i>' +
                        '<h4>No comparisons yet</h4>' +
                        '<p>Run a proposal comparison and it will be automatically saved here.</p>' +
                    '</div>';
                if (window.lucide) window.lucide.createIcons();
                return;
            }

            var items = json.data;
            var html = items.map(function(item) {
                var vendors = (item.vendor_names || []).map(function(v) {
                    return '<span class="pc-history-vendor">' + escHtml(v) + '</span>';
                }).join('');

                var spread = item.total_spread
                    ? _formatCurrency(item.total_spread) + ' spread'
                    : '';

                var date = '';
                if (item.created_at) {
                    try {
                        var d = new Date(item.created_at);
                        date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
                            ' at ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                    } catch(e) { date = item.created_at; }
                }

                return '<div class="pc-history-card" data-id="' + item.id + '">' +
                    '<div class="pc-history-card-main">' +
                        '<div class="pc-history-card-info">' +
                            '<div class="pc-history-card-title">' +
                                escHtml(item.project_name || 'Ad-hoc Comparison') +
                            '</div>' +
                            '<div class="pc-history-card-vendors">' + vendors + '</div>' +
                            '<div class="pc-history-card-meta">' +
                                '<span>' + (item.vendor_count || 0) + ' proposals</span>' +
                                (spread ? ' \u2022 <span>' + spread + '</span>' : '') +
                                ' \u2022 <span>' + date + '</span>' +
                            '</div>' +
                        '</div>' +
                        '<div class="pc-history-card-actions">' +
                            '<button class="pc-btn pc-btn-primary pc-btn-sm pc-history-load" title="View results">' +
                                '<i data-lucide="eye"></i> View' +
                            '</button>' +
                            '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-history-delete" title="Delete">' +
                                '<i data-lucide="trash-2"></i>' +
                            '</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
            }).join('');

            document.getElementById('pc-history-list').innerHTML = html;
            if (window.lucide) window.lucide.createIcons();

            // Wire up events via delegation
            document.getElementById('pc-history-list').addEventListener('click', function(e) {
                var loadBtn = e.target.closest('.pc-history-load');
                var delBtn = e.target.closest('.pc-history-delete');
                var card = e.target.closest('.pc-history-card');
                if (!card) return;
                var id = card.dataset.id;

                if (delBtn) {
                    e.stopPropagation();
                    _deleteHistoryItem(id, card);
                } else if (loadBtn || (!delBtn && card)) {
                    _loadHistoryItem(id);
                }
            });

        } catch (err) {
            console.error('[AEGIS ProposalCompare] History fetch error:', err);
            document.getElementById('pc-history-list').innerHTML =
                '<div class="pc-empty"><h4>Failed to load history</h4><p>' + escHtml(err.message) + '</p></div>';
        }
    }

    async function _loadHistoryItem(id) {
        try {
            var list = document.getElementById('pc-history-list');
            if (list) {
                list.innerHTML = '<div class="pc-loading"><i data-lucide="loader" class="spin"></i> Loading comparison...</div>';
                if (window.lucide) window.lucide.createIcons();
            }

            var resp = await fetch('/api/proposal-compare/history/' + id, {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            if (!json.success || !json.data) {
                throw new Error(json.error?.message || 'Failed to load comparison');
            }

            var result = json.data;

            // v5.9.41: Backend wraps comparison data in a .result key
            // (get_comparison returns {id, project_id, created_at, notes, result: {...}})
            // Unwrap to get the actual comparison data
            if (result && result.result && typeof result.result === 'object') {
                var compMeta = { id: result.id, project_id: result.project_id, created_at: result.created_at, notes: result.notes };
                result = result.result;
                result._comparisonMeta = compMeta;
            }

            // If the result has _proposals_input, restore State.proposals for Back to Review
            if (result._proposals_input && Array.isArray(result._proposals_input)) {
                State.proposals = result._proposals_input;
            } else {
                State.proposals = [];
            }
            // Remove internal field before rendering
            delete result._proposals_input;

            State.comparison = result;
            State.comparisonId = parseInt(id, 10);
            State.activeTab = 'executive';
            renderResults();

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Load history item error:', err);
            if (window.showToast) {
                window.showToast('Failed to load comparison: ' + err.message, 'error');
            }
        }
    }

    async function _deleteHistoryItem(id, cardEl) {
        if (!confirm('Delete this comparison? This cannot be undone.')) return;

        try {
            var resp = await fetch('/api/proposal-compare/history/' + id, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            if (!json.success) {
                throw new Error(json.error?.message || 'Delete failed');
            }

            // Animate removal
            cardEl.style.transition = 'opacity 0.3s, transform 0.3s';
            cardEl.style.opacity = '0';
            cardEl.style.transform = 'translateX(20px)';
            setTimeout(function() {
                cardEl.remove();
                // Check if list is now empty
                var list = document.getElementById('pc-history-list');
                if (list && !list.querySelector('.pc-history-card')) {
                    list.innerHTML =
                        '<div class="pc-empty">' +
                            '<i data-lucide="inbox" style="width:48px;height:48px;opacity:0.3"></i>' +
                            '<h4>No comparisons yet</h4>' +
                            '<p>Run a proposal comparison and it will be automatically saved here.</p>' +
                        '</div>';
                    if (window.lucide) window.lucide.createIcons();
                }
            }, 300);

            if (window.showToast) {
                window.showToast('Comparison deleted', 'success');
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Delete error:', err);
            if (window.showToast) {
                window.showToast('Delete failed: ' + err.message, 'error');
            }
        }
    }

    // ──────────────────────────────────────────
    // Export
    // ──────────────────────────────────────────

    async function exportXLSX() {
        // In multi-term mode, export the currently active term's comparison
        // (or if on "All Terms Summary", export all terms sequentially)
        if (State.multiTermMode && State.multiTermActiveIdx === -1) {
            // Export all terms — one XLSX per term (zip not supported, export current selection)
            if (window.showToast) {
                window.showToast('Switch to a specific term tab to export its XLSX, or each term can be exported individually.', 'info');
            }
            return;
        }

        if (!State.comparison) return;

        try {
            var resp = await fetch('/api/proposal-compare/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify(State.comparison),
            });

            if (!resp.ok) {
                var err = {};
                try { err = await resp.json(); } catch(e) {}
                throw new Error(err.error?.message || 'Export failed (' + resp.status + ')');
            }

            // Download the file
            var blob = await resp.blob();
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            var termSuffix = '';
            if (State.multiTermMode && State.multiTermResults[State.multiTermActiveIdx]) {
                termSuffix = '_' + State.multiTermResults[State.multiTermActiveIdx].termLabel.replace(/\s+/g, '_');
            }
            a.download = 'AEGIS_Proposal_Comparison' + termSuffix + '.xlsx';
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            if (window.showToast) {
                var msg = 'Comparison exported to XLSX';
                if (termSuffix) msg += ' (' + State.multiTermResults[State.multiTermActiveIdx].termLabel + ')';
                window.showToast(msg, 'success');
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Export error:', err);
            if (window.showToast) {
                window.showToast('Export failed: ' + err.message, 'error');
            }
        }
    }

    async function exportHTML() {
        // In multi-term mode on "All Terms Summary", export all terms
        if (State.multiTermMode && State.multiTermActiveIdx === -1) {
            if (window.showToast) {
                window.showToast('Switch to a specific term tab to export its HTML, or each term can be exported individually.', 'info');
            }
            return;
        }

        if (!State.comparison) return;

        try {
            if (window.showToast) {
                window.showToast('Generating interactive HTML report...', 'info');
            }

            var termLabel = '';
            if (State.multiTermMode && State.multiTermResults[State.multiTermActiveIdx]) {
                termLabel = State.multiTermResults[State.multiTermActiveIdx].termLabel;
            }

            var exportData = Object.assign({}, State.comparison, {
                metadata: Object.assign({}, State.comparison.metadata || {}, {
                    project_name: State.projectId ? (State.projectName || 'Comparison') : 'Comparison',
                    compared_at: new Date().toISOString(),
                    term_label: termLabel,
                }),
            });

            var resp = await fetch('/api/proposal-compare/export-html', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify(exportData),
            });

            if (!resp.ok) {
                var err = {};
                try { err = await resp.json(); } catch(e) {}
                throw new Error(err.error?.message || 'HTML export failed (' + resp.status + ')');
            }

            var blob = await resp.blob();
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            var cd = resp.headers.get('content-disposition') || '';
            var fname = 'AEGIS_Proposal_Comparison.html';
            var match = cd.match(/filename="?([^"]+)"?/);
            if (match) fname = match[1];
            if (termLabel && !fname.includes(termLabel)) {
                fname = fname.replace('.html', '_' + termLabel.replace(/\s+/g, '_') + '.html');
            }
            a.download = fname;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            if (window.showToast) {
                var msg = 'Interactive HTML report exported!';
                if (termLabel) msg += ' (' + termLabel + ')';
                window.showToast(msg, 'success');
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] HTML export error:', err);
            if (window.showToast) {
                window.showToast('HTML export failed: ' + err.message, 'error');
            }
        }
    }

    // ──────────────────────────────────────────
    // Project Dashboard
    // ──────────────────────────────────────────

    async function renderProjectDashboard() {
        var body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML =
            '<div class="pc-dashboard">' +
                '<div class="pc-dashboard-header">' +
                    '<h3><i data-lucide="layout-dashboard" style="width:20px;height:20px;vertical-align:-3px;margin-right:6px"></i>Project Dashboard</h3>' +
                    '<div class="pc-dashboard-actions">' +
                        '<button class="pc-btn pc-btn-ghost pc-btn-sm" onclick="ProposalCompare._restart()">' +
                            '<i data-lucide="arrow-left"></i> Back' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-primary pc-btn-sm" id="pc-dash-new-project">' +
                            '<i data-lucide="plus"></i> New Project' +
                        '</button>' +
                    '</div>' +
                '</div>' +
                '<div class="pc-project-grid" id="pc-project-grid">' +
                    '<div class="pc-loading"><div class="pc-spinner"></div> Loading projects...</div>' +
                '</div>' +
            '</div>';
        if (window.lucide) window.lucide.createIcons();

        // Wire new project button
        var newBtn = document.getElementById('pc-dash-new-project');
        if (newBtn) {
            newBtn.addEventListener('click', async function() {
                var name = prompt('Enter project name:');
                if (!name || !name.trim()) return;
                try {
                    var resp = await fetch('/api/proposal-compare/projects', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                        body: JSON.stringify({ name: name.trim() }),
                    });
                    var json = await resp.json();
                    if (json.success) {
                        if (window.showToast) window.showToast('Project created', 'success');
                        renderProjectDashboard(); // refresh
                    }
                } catch(e) {
                    console.error('[PC Dashboard] Create project error:', e);
                }
            });
        }

        // Fetch projects
        try {
            var resp = await fetch('/api/proposal-compare/projects?status=all', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            var grid = document.getElementById('pc-project-grid');
            if (!grid) return;

            if (!json.success || !json.data || json.data.length === 0) {
                grid.innerHTML =
                    '<div class="pc-empty" style="grid-column:1/-1">' +
                        '<i data-lucide="folder-plus" style="width:48px;height:48px;opacity:0.3"></i>' +
                        '<h4>No projects yet</h4>' +
                        '<p>Create a project to organize and track your proposal comparisons.</p>' +
                    '</div>';
                if (window.lucide) window.lucide.createIcons();
                return;
            }

            var projects = json.data;
            grid.innerHTML = projects.map(function(proj) {
                var dateStr = '';
                try {
                    var d = new Date(proj.updated_at);
                    dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                } catch(e) { dateStr = proj.updated_at || ''; }

                var totalValueStr = proj.total_value ? formatMoneyShort(proj.total_value) : '\u2014';

                return '<div class="pc-project-card" data-project-id="' + proj.id + '">' +
                    '<div class="pc-project-card-header">' +
                        '<div class="pc-project-card-icon"><i data-lucide="folder-open"></i></div>' +
                        '<div class="pc-project-card-title">' + escHtml(proj.name) + '</div>' +
                        '<div class="pc-project-card-status ' + (proj.status === 'active' ? 'active' : 'archived') + '">' +
                            proj.status +
                        '</div>' +
                    '</div>' +
                    (proj.description ? '<div class="pc-project-card-desc">' + escHtml(proj.description) + '</div>' : '') +
                    '<div class="pc-project-card-stats">' +
                        '<div class="pc-project-stat">' +
                            '<span class="pc-project-stat-value">' + (proj.proposal_count || 0) + '</span>' +
                            '<span class="pc-project-stat-label">Proposals</span>' +
                        '</div>' +
                        '<div class="pc-project-stat">' +
                            '<span class="pc-project-stat-value">' + (proj.total_line_items || 0) + '</span>' +
                            '<span class="pc-project-stat-label">Line Items</span>' +
                        '</div>' +
                        '<div class="pc-project-stat">' +
                            '<span class="pc-project-stat-value">' + totalValueStr + '</span>' +
                            '<span class="pc-project-stat-label">Total Value</span>' +
                        '</div>' +
                        '<div class="pc-project-stat">' +
                            '<span class="pc-project-stat-value">' + dateStr + '</span>' +
                            '<span class="pc-project-stat-label">Last Updated</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="pc-project-card-actions">' +
                        '<button class="pc-btn pc-btn-primary pc-btn-sm pc-proj-open">' +
                            '<i data-lucide="external-link"></i> Open' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-proj-delete" title="Delete project">' +
                            '<i data-lucide="trash-2"></i>' +
                        '</button>' +
                    '</div>' +
                '</div>';
            }).join('');
            if (window.lucide) window.lucide.createIcons();

            // Event delegation
            grid.addEventListener('click', function(e) {
                var card = e.target.closest('.pc-project-card');
                if (!card) return;
                var projId = parseInt(card.dataset.projectId, 10);

                if (e.target.closest('.pc-proj-delete')) {
                    e.stopPropagation();
                    if (confirm('Delete this project and all its proposals?')) {
                        fetch('/api/proposal-compare/projects/' + projId, {
                            method: 'DELETE',
                            headers: { 'X-CSRF-Token': getCSRF() },
                        }).then(function() {
                            card.style.transition = 'opacity 0.3s, transform 0.3s';
                            card.style.opacity = '0';
                            card.style.transform = 'scale(0.95)';
                            setTimeout(function() { card.remove(); }, 300);
                            if (window.showToast) window.showToast('Project deleted', 'success');
                        });
                    }
                    return;
                }

                if (e.target.closest('.pc-proj-open') || e.target.closest('.pc-project-card-header')) {
                    renderProjectDetail(projId);
                }
            });

        } catch (err) {
            console.error('[PC Dashboard] Fetch projects error:', err);
            var grid = document.getElementById('pc-project-grid');
            if (grid) grid.innerHTML = '<div class="pc-empty"><h4>Failed to load projects</h4><p>' + escHtml(err.message) + '</p></div>';
        }
    }

    async function renderProjectDetail(projectId) {
        var body = document.getElementById('pc-body');
        if (!body) return;

        State.dashboardProject = projectId;

        body.innerHTML =
            '<div class="pc-dashboard">' +
                '<div class="pc-dashboard-header">' +
                    '<h3 id="pc-detail-title"><i data-lucide="folder-open" style="width:20px;height:20px;vertical-align:-3px;margin-right:6px"></i>Loading...</h3>' +
                    '<div class="pc-dashboard-actions">' +
                        '<button class="pc-btn pc-btn-ghost pc-btn-sm" onclick="ProposalCompare._openDashboard()">' +
                            '<i data-lucide="arrow-left"></i> Dashboard' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-secondary pc-btn-sm" id="pc-detail-add">' +
                            '<i data-lucide="upload"></i> Add Proposals' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-primary pc-btn-sm" id="pc-detail-compare">' +
                            '<i data-lucide="git-compare-arrows"></i> Compare All' +
                        '</button>' +
                    '</div>' +
                '</div>' +
                '<!-- v5.9.53: Financial summary dashboard -->' +
                '<div class="pc-detail-section" id="pc-detail-financial">' +
                    '<div id="pc-fin-summary"><div class="pc-loading"><div class="pc-spinner"></div> Loading financial summary...</div></div>' +
                '</div>' +
                '<div class="pc-detail-section" id="pc-detail-proposals">' +
                    '<h4><i data-lucide="file-text" style="width:16px;height:16px;vertical-align:-2px;margin-right:4px"></i>Proposals</h4>' +
                    '<div class="pc-detail-list" id="pc-prop-list"><div class="pc-loading"><div class="pc-spinner"></div> Loading...</div></div>' +
                '</div>' +
                '<div class="pc-detail-section" id="pc-detail-comparisons">' +
                    '<h4><i data-lucide="history" style="width:16px;height:16px;vertical-align:-2px;margin-right:4px"></i>Comparison History</h4>' +
                    '<div class="pc-detail-list" id="pc-comp-list"><div class="pc-loading"><div class="pc-spinner"></div> Loading...</div></div>' +
                '</div>' +
            '</div>';
        if (window.lucide) window.lucide.createIcons();

        // Wire Add Proposals button — switch to upload phase with project pre-selected
        var addBtn = document.getElementById('pc-detail-add');
        if (addBtn) {
            addBtn.addEventListener('click', function() {
                State.selectedProjectId = projectId;
                renderUploadPhase();
            });
        }

        // Wire Compare All button
        var compareBtn = document.getElementById('pc-detail-compare');
        if (compareBtn) {
            compareBtn.addEventListener('click', async function() {
                compareBtn.disabled = true;
                compareBtn.innerHTML = '<div class="pc-spinner" style="width:14px;height:14px"></div> Comparing...';
                try {
                    var resp = await fetch('/api/proposal-compare/projects/' + projectId + '/compare', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                        body: JSON.stringify({}),
                    });
                    var json = await resp.json();
                    if (!json.success) throw new Error(json.error?.message || 'Compare failed');
                    State.comparison = json.data;
                    State.activeTab = 'executive';
                    renderResults();
                } catch(e) {
                    if (window.showToast) window.showToast('Compare failed: ' + e.message, 'error');
                    compareBtn.disabled = false;
                    compareBtn.innerHTML = '<i data-lucide="git-compare-arrows"></i> Compare All';
                    if (window.lucide) window.lucide.createIcons();
                }
            });
        }

        // Fetch project info + proposals + comparisons in parallel
        try {
            var [projResp, propsResp, compsResp] = await Promise.all([
                fetch('/api/proposal-compare/projects/' + projectId, { headers: { 'X-CSRF-Token': getCSRF() } }),
                fetch('/api/proposal-compare/projects/' + projectId + '/proposals', { headers: { 'X-CSRF-Token': getCSRF() } }),
                fetch('/api/proposal-compare/projects/' + projectId + '/comparisons', { headers: { 'X-CSRF-Token': getCSRF() } }),
            ]);

            var projData = await projResp.json();
            var propsData = await propsResp.json();
            var compsData = await compsResp.json();

            // Update title
            var titleEl = document.getElementById('pc-detail-title');
            if (titleEl && projData.success && projData.data) {
                titleEl.innerHTML = '<i data-lucide="folder-open" style="width:20px;height:20px;vertical-align:-3px;margin-right:6px"></i>' +
                    escHtml(projData.data.name);
                if (window.lucide) window.lucide.createIcons();
            }

            // Render proposals
            var propList = document.getElementById('pc-prop-list');
            if (propList) {
                var props = (propsData.success && propsData.data) ? propsData.data : [];
                if (props.length === 0) {
                    propList.innerHTML = '<div class="pc-empty-sm">No proposals yet. Click "Add Proposals" to get started.</div>';
                } else {
                    propList.innerHTML = props.map(function(prop) {
                        return '<div class="pc-prop-card" data-prop-id="' + prop.id + '">' +
                            '<div class="pc-prop-card-main">' +
                                '<div class="pc-prop-card-icon"><i data-lucide="building-2"></i></div>' +
                                '<div class="pc-prop-card-info">' +
                                    '<div class="pc-prop-card-name">' + escHtml(prop.company_name || prop.filename) + '</div>' +
                                    '<div class="pc-prop-card-meta">' +
                                        escHtml(prop.filename) + ' \u2022 ' +
                                        (prop.line_item_count || 0) + ' items' +
                                        (prop.total_amount ? ' \u2022 ' + formatMoney(prop.total_amount) : '') +
                                    '</div>' +
                                '</div>' +
                            '</div>' +
                            '<div class="pc-prop-card-actions">' +
                                '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-prop-edit" title="Edit">' +
                                    '<i data-lucide="pencil"></i>' +
                                '</button>' +
                                '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-prop-move" title="Move to another project">' +
                                    '<i data-lucide="move"></i>' +
                                '</button>' +
                                '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-prop-remove" title="Remove">' +
                                    '<i data-lucide="x"></i>' +
                                '</button>' +
                            '</div>' +
                        '</div>';
                    }).join('');
                    if (window.lucide) window.lucide.createIcons();

                    // Event delegation for proposal actions
                    propList.addEventListener('click', function(e) {
                        var card = e.target.closest('.pc-prop-card');
                        if (!card) return;
                        var propId = parseInt(card.dataset.propId, 10);

                        if (e.target.closest('.pc-prop-edit')) {
                            e.stopPropagation();
                            _editProposalFromDashboard(propId, projectId);
                        } else if (e.target.closest('.pc-prop-move')) {
                            e.stopPropagation();
                            _showTagToProjectMenu(e.target.closest('.pc-prop-move'), null, propId);
                        } else if (e.target.closest('.pc-prop-remove')) {
                            e.stopPropagation();
                            if (confirm('Remove this proposal from the project?')) {
                                fetch('/api/proposal-compare/proposals/' + propId, {
                                    method: 'DELETE',
                                    headers: { 'X-CSRF-Token': getCSRF() },
                                }).then(function() {
                                    card.style.transition = 'opacity 0.3s';
                                    card.style.opacity = '0';
                                    setTimeout(function() { card.remove(); }, 300);
                                    if (window.showToast) window.showToast('Proposal removed', 'success');
                                });
                            }
                        }
                    });
                }
            }

            // Render comparisons
            var compList = document.getElementById('pc-comp-list');
            if (compList) {
                var comps = (compsData.success && compsData.data) ? compsData.data : [];
                if (comps.length === 0) {
                    compList.innerHTML = '<div class="pc-empty-sm">No comparisons yet. Add 2+ proposals and click "Compare All".</div>';
                } else {
                    compList.innerHTML = comps.map(function(comp) {
                        var vendors = (comp.vendor_names || []).map(function(v) {
                            return '<span class="pc-history-vendor">' + escHtml(v) + '</span>';
                        }).join('');
                        var dateStr = '';
                        try {
                            var d = new Date(comp.created_at);
                            dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
                                ' at ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                        } catch(e) { dateStr = comp.created_at; }

                        return '<div class="pc-comp-card" data-comp-id="' + comp.id + '">' +
                            '<div class="pc-comp-card-main">' +
                                '<div class="pc-comp-card-info">' +
                                    '<div class="pc-comp-card-vendors">' + vendors + '</div>' +
                                    '<div class="pc-comp-card-meta">' +
                                        (comp.vendor_count || 0) + ' proposals' +
                                        (comp.total_spread !== 'N/A' ? ' \u2022 ' + comp.total_spread : '') +
                                        ' \u2022 ' + dateStr +
                                    '</div>' +
                                '</div>' +
                                '<div class="pc-comp-card-actions">' +
                                    '<button class="pc-btn pc-btn-primary pc-btn-sm pc-comp-view">' +
                                        '<i data-lucide="eye"></i> View' +
                                    '</button>' +
                                    '<button class="pc-btn pc-btn-ghost pc-btn-sm pc-comp-delete">' +
                                        '<i data-lucide="trash-2"></i>' +
                                    '</button>' +
                                '</div>' +
                            '</div>' +
                        '</div>';
                    }).join('');
                    if (window.lucide) window.lucide.createIcons();

                    compList.addEventListener('click', function(e) {
                        var card = e.target.closest('.pc-comp-card');
                        if (!card) return;
                        var compId = card.dataset.compId;

                        if (e.target.closest('.pc-comp-delete')) {
                            e.stopPropagation();
                            _deleteHistoryItem(compId, card);
                        } else if (e.target.closest('.pc-comp-view')) {
                            _loadHistoryItem(compId);
                        }
                    });
                }
            }

            // ── v5.9.53: Fetch + render financial summary dashboard ──
            _renderFinancialSummary(projectId, compsData);

        } catch(err) {
            console.error('[PC Dashboard] Detail fetch error:', err);
            if (window.showToast) window.showToast('Failed to load project: ' + err.message, 'error');
        }
    }

    /**
     * v5.9.53: Fetch financial summary from latest comparison and render
     * a rich dashboard inside the project detail view.
     */
    async function _renderFinancialSummary(projectId, compsData) {
        var container = document.getElementById('pc-fin-summary');
        if (!container) return;

        var comps = (compsData && compsData.success && compsData.data) ? compsData.data : [];
        if (comps.length === 0) {
            container.innerHTML =
                '<div class="pc-fin-empty">' +
                    '<i data-lucide="bar-chart-3" style="width:32px;height:32px;opacity:0.3"></i>' +
                    '<p>No comparisons yet. Add 2+ proposals and click <strong>Compare All</strong> to see financial analysis.</p>' +
                '</div>';
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        try {
            var resp = await fetch('/api/proposal-compare/projects/' + projectId + '/financial-summary', {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            if (!json.success || !json.data || !json.data.has_comparison) {
                container.innerHTML = '<div class="pc-fin-empty"><p>Financial data unavailable.</p></div>';
                return;
            }

            var d = json.data;
            var html = '';

            // ── Hero stat cards ──
            var vendorCount = (d.vendors || []).length;
            var totalLineItems = 0;
            var totalFlags = (d.red_flags ? (d.red_flags.critical || 0) + (d.red_flags.warning || 0) + (d.red_flags.info || 0) : 0);
            (d.vendors || []).forEach(function(v) { totalLineItems += (v.line_item_count || 0); });

            html += '<div class="pc-fin-heroes">';
            html += _finHero('users', vendorCount, 'Vendors', '#D6A84A');
            html += _finHero('layers', totalLineItems, 'Line Items', '#2196f3');
            if (d.price_range) {
                html += _finHero('dollar-sign', formatMoneyShort(d.price_range.avg), 'Average Total', '#219653');
                html += _finHero('trending-up', formatMoneyShort(d.price_range.spread), 'Price Spread', d.price_range.spread > d.price_range.avg * 0.3 ? '#f44336' : '#D6A84A');
            }
            html += _finHero('shield-alert', totalFlags, 'Risk Flags', totalFlags > 5 ? '#f44336' : totalFlags > 0 ? '#D6A84A' : '#219653');
            html += '</div>';

            // ── Vendor comparison table ──
            if (d.vendors && d.vendors.length > 0) {
                html += '<div class="pc-fin-section">';
                html += '<h5 class="pc-fin-section-title"><i data-lucide="building-2" style="width:15px;height:15px;color:#D6A84A"></i> Vendor Overview</h5>';
                html += '<div class="pc-fin-vendor-grid">';
                d.vendors.sort(function(a, b) { return (a.total || 0) - (b.total || 0); });
                d.vendors.forEach(function(v, idx) {
                    var gc = gradeColor(v.grade || 'C');
                    var isLowest = idx === 0 && d.vendors.length > 1;
                    html += '<div class="pc-fin-vendor-card' + (isLowest ? ' pc-fin-lowest' : '') + '">' +
                        (isLowest ? '<div class="pc-fin-lowest-badge"><i data-lucide="trophy" style="width:11px;height:11px"></i> Lowest</div>' : '') +
                        '<div class="pc-fin-vendor-name">' + escHtml(v.company_name || 'Vendor ' + (idx + 1)) + '</div>' +
                        '<div class="pc-fin-vendor-total">' + formatMoney(v.total) + '</div>' +
                        '<div class="pc-fin-vendor-meta">' +
                            (v.line_item_count || 0) + ' items' +
                            (v.contract_term ? ' &bull; ' + escHtml(v.contract_term) : '') +
                        '</div>' +
                        '<div class="pc-fin-vendor-footer">' +
                            '<span class="pc-fin-grade" style="background:' + gc + '">' + (v.grade || '\u2014') + '</span>' +
                            '<span class="pc-fin-score">' + (v.overall_score != null ? v.overall_score + '/100' : '') + '</span>' +
                        '</div>' +
                    '</div>';
                });
                html += '</div></div>';
            }

            // ── Price range bar ──
            if (d.price_range && d.price_range.min != null) {
                var pr = d.price_range;
                var range = pr.max - pr.min;
                var avgPct = range > 0 ? ((pr.avg - pr.min) / range * 100) : 50;
                html += '<div class="pc-fin-section">';
                html += '<h5 class="pc-fin-section-title"><i data-lucide="ruler" style="width:15px;height:15px;color:#D6A84A"></i> Price Range</h5>';
                html += '<div class="pc-fin-price-range">' +
                    '<div class="pc-fin-range-labels">' +
                        '<span class="pc-fin-range-min">' + formatMoney(pr.min) + '</span>' +
                        '<span class="pc-fin-range-max">' + formatMoney(pr.max) + '</span>' +
                    '</div>' +
                    '<div class="pc-fin-range-bar">' +
                        '<div class="pc-fin-range-fill"></div>' +
                        '<div class="pc-fin-range-avg" style="left:' + avgPct.toFixed(1) + '%">' +
                            '<div class="pc-fin-range-avg-label">AVG ' + formatMoneyShort(pr.avg) + '</div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="pc-fin-range-spread">Spread: ' + formatMoney(pr.spread) + '</div>' +
                '</div></div>';
            }

            // ── Category breakdown ──
            if (d.categories && Object.keys(d.categories).length > 0) {
                html += '<div class="pc-fin-section">';
                html += '<h5 class="pc-fin-section-title"><i data-lucide="pie-chart" style="width:15px;height:15px;color:#D6A84A"></i> Category Breakdown</h5>';
                html += '<div class="pc-fin-cat-table"><table class="pc-table pc-table-compact">';
                html += '<thead><tr><th>Category</th>';
                (d.vendors || []).forEach(function(v) {
                    html += '<th>' + escHtml((v.company_name || '').split(' ')[0]) + '</th>';
                });
                html += '</tr></thead><tbody>';
                for (var catName in d.categories) {
                    var catRow = d.categories[catName];
                    html += '<tr><td class="pc-fin-cat-name">' + escHtml(catName) + '</td>';
                    (d.vendors || []).forEach(function(v) {
                        var vid = v.vendor_id || v.company_name;
                        var catVendors = catRow.vendors || {};
                        var amt = catVendors[vid];
                        html += '<td class="pc-amount">' + (amt != null ? formatMoney(amt) : '\u2014') + '</td>';
                    });
                    html += '</tr>';
                }
                html += '</tbody></table></div></div>';
            }

            // ── Red flags summary ──
            if (d.red_flags && totalFlags > 0) {
                html += '<div class="pc-fin-section">';
                html += '<h5 class="pc-fin-section-title"><i data-lucide="shield-alert" style="width:15px;height:15px;color:#f44336"></i> Risk Summary</h5>';
                html += '<div class="pc-fin-flags">';
                if (d.red_flags.critical > 0) {
                    html += '<div class="pc-fin-flag-pill pc-fin-flag-critical">' +
                        '<i data-lucide="alert-circle" style="width:13px;height:13px"></i> ' +
                        d.red_flags.critical + ' Critical</div>';
                }
                if (d.red_flags.warning > 0) {
                    html += '<div class="pc-fin-flag-pill pc-fin-flag-warning">' +
                        '<i data-lucide="alert-triangle" style="width:13px;height:13px"></i> ' +
                        d.red_flags.warning + ' Warning</div>';
                }
                if (d.red_flags.info > 0) {
                    html += '<div class="pc-fin-flag-pill pc-fin-flag-info">' +
                        '<i data-lucide="info" style="width:13px;height:13px"></i> ' +
                        d.red_flags.info + ' Info</div>';
                }
                html += '</div></div>';
            }

            // ── Contract terms ──
            if (d.contract_terms && d.contract_terms.length > 1) {
                html += '<div class="pc-fin-section">';
                html += '<h5 class="pc-fin-section-title"><i data-lucide="calendar" style="width:15px;height:15px;color:#D6A84A"></i> Contract Terms</h5>';
                html += '<div class="pc-fin-terms">';
                d.contract_terms.forEach(function(term) {
                    html += '<span class="pc-fin-term-badge">' + escHtml(term) + '</span>';
                });
                html += '</div></div>';
            }

            // ── View Full Results button ──
            html += '<div class="pc-fin-actions">' +
                '<button class="pc-btn pc-btn-primary" id="pc-fin-view-full">' +
                    '<i data-lucide="maximize-2"></i> View Full Analysis' +
                '</button>' +
                '<button class="pc-btn pc-btn-secondary" id="pc-fin-export-html">' +
                    '<i data-lucide="download"></i> Export Report' +
                '</button>' +
            '</div>';

            container.innerHTML = html;
            if (window.lucide) window.lucide.createIcons();

            // Wire buttons
            var viewFullBtn = document.getElementById('pc-fin-view-full');
            if (viewFullBtn) {
                viewFullBtn.addEventListener('click', function() {
                    _loadHistoryItem(d.comparison_id);
                });
            }
            var exportBtn = document.getElementById('pc-fin-export-html');
            if (exportBtn) {
                exportBtn.addEventListener('click', async function() {
                    try {
                        var compResp = await fetch('/api/proposal-compare/comparisons/' + d.comparison_id, {
                            headers: { 'X-CSRF-Token': getCSRF() },
                        });
                        var compJson = await compResp.json();
                        if (compJson.success && compJson.data && compJson.data.result_json) {
                            State.comparison = JSON.parse(compJson.data.result_json);
                            exportHTML();
                        } else {
                            if (window.showToast) window.showToast('Could not load comparison data for export', 'error');
                        }
                    } catch(e) {
                        if (window.showToast) window.showToast('Export error: ' + e.message, 'error');
                    }
                });
            }

        } catch(err) {
            console.error('[PC Dashboard] Financial summary error:', err);
            container.innerHTML = '<div class="pc-fin-empty"><p>Failed to load financial summary.</p></div>';
        }
    }

    function _finHero(icon, value, label, color) {
        return '<div class="pc-fin-hero-card">' +
            '<div class="pc-fin-hero-icon" style="background:' + color + '18;color:' + color + '">' +
                '<i data-lucide="' + icon + '" style="width:18px;height:18px"></i>' +
            '</div>' +
            '<div class="pc-fin-hero-value">' + value + '</div>' +
            '<div class="pc-fin-hero-label">' + label + '</div>' +
        '</div>';
    }

    async function _editProposalFromDashboard(proposalId, projectId) {
        try {
            var resp = await fetch('/api/proposal-compare/proposals/' + proposalId, {
                headers: { 'X-CSRF-Token': getCSRF() },
            });
            var json = await resp.json();
            if (!json.success || !json.data) throw new Error(json.error?.message || 'Not found');

            var fullData = json.data;
            fullData._db_id = proposalId;
            fullData._dashboardProjectId = projectId;
            State.proposals = [fullData];
            State.files = []; // no files for dashboard edit
            State._reviewIdx = 0;
            State._lineItemEditorOpen = [];
            State.selectedProjectId = projectId;
            renderReviewPhase();
        } catch(e) {
            console.error('[PC Dashboard] Edit proposal error:', e);
            if (window.showToast) window.showToast('Failed to load proposal: ' + e.message, 'error');
        }
    }

    /**
     * Tag all in-memory proposals to a project. Used when user selects a project
     * from the review-phase dropdown — immediately persists each proposal.
     */
    function _tagAllProposalsToProject(projectId) {
        if (!projectId || !State.proposals || State.proposals.length === 0) return;

        var tagged = 0;
        State.proposals.forEach(function(p, idx) {
            if (p._db_id) {
                // Already in DB — move to new project
                fetch('/api/proposal-compare/proposals/' + p._db_id + '/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                    body: JSON.stringify({ project_id: projectId }),
                }).then(function(r) { return r.json(); }).then(function(json) {
                    if (json.success) tagged++;
                    console.log('[PC] Moved proposal', p._db_id, 'to project', projectId, json.success ? 'OK' : 'FAIL');
                }).catch(function(e) {
                    console.warn('[PC] Move proposal error:', e);
                });
            } else {
                // Not yet in DB — add to project
                fetch('/api/proposal-compare/projects/' + projectId + '/proposals', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                    body: JSON.stringify(p),
                }).then(function(r) { return r.json(); }).then(function(json) {
                    if (json.success && json.data && json.data.id) {
                        p._db_id = json.data.id;
                        tagged++;
                    }
                    console.log('[PC] Added proposal', (p.company_name || p.filename), 'to project', projectId, json.success ? 'OK' : 'FAIL');
                }).catch(function(e) {
                    console.warn('[PC] Add proposal error:', e);
                });
            }
        });
    }

    /**
     * Show project picker from the Results header. Tags ALL proposals
     * from the current comparison to the selected project.
     */
    function _showResultsTagToProjectMenu(anchorEl) {
        var existing = document.querySelector('.pc-tag-dropdown');
        if (existing) existing.remove();

        var dropdown = document.createElement('div');
        dropdown.className = 'pc-tag-dropdown';
        dropdown.innerHTML = '<div class="pc-tag-dropdown-loading"><div class="pc-spinner" style="width:16px;height:16px"></div> Loading projects...</div>';

        var rect = anchorEl.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 4) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.zIndex = '16000';
        document.body.appendChild(dropdown);

        function closeDropdown(e) {
            if (!dropdown.contains(e.target) && e.target !== anchorEl) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        }
        setTimeout(function() { document.addEventListener('click', closeDropdown); }, 50);

        fetch('/api/proposal-compare/projects?status=active', {
            headers: { 'X-CSRF-Token': getCSRF() },
        }).then(function(r) { return r.json(); }).then(function(json) {
            var projects = (json.success && json.data) ? json.data : [];

            var propCount = State.proposals ? State.proposals.length : 0;
            var html = '<div class="pc-tag-dropdown-header">Tag ' + propCount + ' proposal' + (propCount !== 1 ? 's' : '') + ' to project</div>';
            html += '<div class="pc-tag-dropdown-list">';

            projects.forEach(function(proj) {
                html += '<div class="pc-tag-dropdown-item" data-project-id="' + proj.id + '">' +
                    '<i data-lucide="folder" style="width:14px;height:14px;margin-right:8px;opacity:0.5"></i>' +
                    escHtml(proj.name) +
                    '<span class="pc-tag-dropdown-count">' + (proj.proposal_count || 0) + '</span>' +
                '</div>';
            });

            html += '<div class="pc-tag-dropdown-item pc-tag-new-project">' +
                '<i data-lucide="plus" style="width:14px;height:14px;margin-right:8px;opacity:0.5"></i>' +
                '+ New Project' +
            '</div>';
            html += '</div>';
            dropdown.innerHTML = html;
            if (window.lucide) window.lucide.createIcons();

            dropdown.addEventListener('click', function(e) {
                var item = e.target.closest('.pc-tag-dropdown-item');
                if (!item) return;

                var doTag = function(targetProjId) {
                    _tagAllProposalsToProject(targetProjId);
                    State.selectedProjectId = targetProjId;
                    if (window.showToast) {
                        var projName = '';
                        try { projName = projects.find(function(p) { return p.id === targetProjId; }).name; } catch(e) {}
                        window.showToast('Tagged ' + propCount + ' proposal' + (propCount !== 1 ? 's' : '') + ' to project' + (projName ? ': ' + projName : ''), 'success');
                    }
                };

                if (item.classList.contains('pc-tag-new-project')) {
                    var name = prompt('Enter new project name:');
                    if (!name || !name.trim()) return;
                    fetch('/api/proposal-compare/projects', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                        body: JSON.stringify({ name: name.trim() }),
                    }).then(function(r) { return r.json(); }).then(function(result) {
                        if (result.success && result.data) {
                            doTag(result.data.id);
                        }
                    });
                } else {
                    var targetId = parseInt(item.dataset.projectId, 10);
                    doTag(targetId);
                }

                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            });
        });
    }

    function _showTagToProjectMenu(anchorEl, proposalIdx, dbId) {
        // Remove any existing dropdown
        var existing = document.querySelector('.pc-tag-dropdown');
        if (existing) existing.remove();

        var dropdown = document.createElement('div');
        dropdown.className = 'pc-tag-dropdown';
        dropdown.innerHTML = '<div class="pc-tag-dropdown-loading"><div class="pc-spinner" style="width:16px;height:16px"></div> Loading projects...</div>';

        // Position near anchor
        var rect = anchorEl.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 4) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.zIndex = '16000';
        document.body.appendChild(dropdown);

        // Close on outside click
        function closeDropdown(e) {
            if (!dropdown.contains(e.target) && e.target !== anchorEl) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        }
        setTimeout(function() { document.addEventListener('click', closeDropdown); }, 50);

        // Fetch projects
        fetch('/api/proposal-compare/projects?status=active', {
            headers: { 'X-CSRF-Token': getCSRF() },
        }).then(function(r) { return r.json(); }).then(function(json) {
            var projects = (json.success && json.data) ? json.data : [];

            var html = '<div class="pc-tag-dropdown-header">Move to Project</div>';
            html += '<div class="pc-tag-dropdown-list">';

            projects.forEach(function(proj) {
                html += '<div class="pc-tag-dropdown-item" data-project-id="' + proj.id + '">' +
                    '<i data-lucide="folder" style="width:14px;height:14px;margin-right:8px;opacity:0.5"></i>' +
                    escHtml(proj.name) +
                    '<span class="pc-tag-dropdown-count">' + (proj.proposal_count || 0) + '</span>' +
                '</div>';
            });

            html += '<div class="pc-tag-dropdown-item pc-tag-new-project">' +
                '<i data-lucide="plus" style="width:14px;height:14px;margin-right:8px;opacity:0.5"></i>' +
                '+ New Project' +
            '</div>';
            html += '</div>';
            dropdown.innerHTML = html;
            if (window.lucide) window.lucide.createIcons();

            // Handle clicks
            dropdown.addEventListener('click', function(e) {
                var item = e.target.closest('.pc-tag-dropdown-item');
                if (!item) return;

                if (item.classList.contains('pc-tag-new-project')) {
                    var name = prompt('Enter new project name:');
                    if (!name || !name.trim()) return;
                    fetch('/api/proposal-compare/projects', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                        body: JSON.stringify({ name: name.trim() }),
                    }).then(function(r) { return r.json(); }).then(function(result) {
                        if (result.success && result.data) {
                            _doMoveOrTag(proposalIdx, dbId, result.data.id);
                        }
                    });
                } else {
                    var targetId = parseInt(item.dataset.projectId, 10);
                    _doMoveOrTag(proposalIdx, dbId, targetId);
                }

                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            });
        });
    }

    function _doMoveOrTag(proposalIdx, dbId, targetProjectId) {
        if (dbId) {
            // Proposal already in DB — use move endpoint
            fetch('/api/proposal-compare/proposals/' + dbId + '/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                body: JSON.stringify({ project_id: targetProjectId }),
            }).then(function(r) { return r.json(); }).then(function(json) {
                if (json.success) {
                    if (window.showToast) window.showToast('Proposal moved', 'success');
                    // Refresh dashboard if we're on it
                    if (State.dashboardProject) renderProjectDetail(State.dashboardProject);
                } else {
                    if (window.showToast) window.showToast('Move failed: ' + (json.error?.message || 'Unknown'), 'error');
                }
            });
        } else if (proposalIdx !== null && State.proposals[proposalIdx]) {
            // In-memory proposal — add to project
            var p = State.proposals[proposalIdx];
            fetch('/api/proposal-compare/projects/' + targetProjectId + '/proposals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRF() },
                body: JSON.stringify(p),
            }).then(function(r) { return r.json(); }).then(function(json) {
                if (json.success) {
                    // Track the db_id for future edits
                    if (json.data && json.data.id) p._db_id = json.data.id;
                    if (window.showToast) window.showToast('Proposal tagged to project', 'success');
                } else {
                    if (window.showToast) window.showToast('Tag failed: ' + (json.error?.message || 'Unknown'), 'error');
                }
            });
        }
    }

    // ──────────────────────────────────────────
    // Public API
    // ──────────────────────────────────────────

    return {
        open: open,
        openProject: openProject,
        openProjectWithResults: openProjectWithResults,
        close: close,
        // Internal callbacks (used by onclick in HTML)
        _removeFile: removeFile,
        _restart: function() {
            _cleanupBlobUrls(); _restoreAllProposals();
            State._reviewIdx = 0; State._lineItemEditorOpen = [];
            State.multiTermMode = false; State.multiTermResults = [];
            State.multiTermActiveIdx = 0; State.multiTermExcluded = [];
            State._selectedForCompare = new Set(); State._selectMode = false;
            State._undoStacks = {}; State._redoStacks = {};
            State._expandedDescs = new Set(); State.proposals = []; State.files = [];
            renderUploadPhase();
        },
        _backToReview: function() { _restoreAllProposals(); renderReviewPhase(); },
        _reanalyze: function() { _restoreAllProposals(); startComparison(); },
        _export: exportXLSX,
        _exportHTML: exportHTML,
        _loadHistory: renderHistoryView,
        // Project dashboard (Part B)
        _openDashboard: renderProjectDashboard,
        _openProjectDetail: renderProjectDetail,
        _tagToProject: _showTagToProjectMenu,
    };
})();
