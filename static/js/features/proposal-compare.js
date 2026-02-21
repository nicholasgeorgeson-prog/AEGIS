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
        switch (level) {
            case 'very_low': return '#2d6a2d';
            case 'low': return '#4caf50';
            case 'neutral': return '#f5f5f5';
            case 'high': return '#ff9800';
            case 'very_high': return '#f44336';
            case 'missing': return '#e0e0e0';
            default: return '#f5f5f5';
        }
    }

    function heatmapTextColor(level) {
        switch (level) {
            case 'very_low': return '#fff';
            case 'low': return '#fff';
            case 'neutral': return '#333';
            case 'high': return '#fff';
            case 'very_high': return '#fff';
            case 'missing': return '#999';
            default: return '#333';
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
                '<div class="pc-dropzone" id="pc-dropzone">' +
                    '<input type="file" class="pc-file-input" id="pc-file-input"' +
                    '       multiple accept=".xlsx,.xls,.docx,.pdf">' +
                    '<div class="pc-dropzone-icon">' +
                        '<i data-lucide="upload-cloud"></i>' +
                    '</div>' +
                    '<h3>Drop proposal files here</h3>' +
                    '<p>Supports DOCX, PDF, and Excel files \u2022 2\u201310 files</p>' +
                '</div>' +
                '<div class="pc-file-list" id="pc-file-list"></div>' +
                '<div class="pc-upload-actions">' +
                    '<button class="pc-btn pc-btn-primary" id="pc-btn-extract" disabled>' +
                        '<i data-lucide="scan-search"></i> Extract Financial Data' +
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

        var html = '<div class="pc-li-editor" id="pc-li-editor">' +
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
            document.getElementById('pc-add-line-item')?.addEventListener('click', function() {
                var tbody = document.getElementById('pc-line-item-tbody');
                if (!tbody) return;
                var cats = ['Labor', 'Material', 'Software', 'License', 'Travel', 'Training', 'ODC', 'Subcontract', 'Overhead', 'Fee', 'Other'];
                var newRow = _renderLineItemRow({ description: '', category: 'Other', amount: null, amount_raw: '', quantity: null, unit_price: null }, tbody.children.length, cats);
                tbody.insertAdjacentHTML('beforeend', newRow);
            });

            document.getElementById('pc-li-editor')?.addEventListener('click', function(e) {
                if (e.target.classList.contains('pc-li-del-btn')) {
                    e.target.closest('.pc-li-row')?.remove();
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

        body.innerHTML =
            renderPhaseIndicator(3) +
            projectBar +
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
                    '<i data-lucide="git-compare-arrows"></i> Compare All ' + total + ' Proposals' +
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
        document.getElementById('pc-btn-compare')?.addEventListener('click', startComparison);

        // Bind review-phase project selector
        var reviewProjSelect = document.getElementById('pc-review-project-select');
        if (reviewProjSelect) {
            reviewProjSelect.addEventListener('change', function() {
                var val = this.value;
                State.selectedProjectId = val ? parseInt(val) : null;
                if (State.selectedProjectId) {
                    var proj = State.projects.find(function(p) { return p.id === State.selectedProjectId; });
                    State.projectName = proj ? proj.name : '';
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
    // Phase: Comparison
    // ──────────────────────────────────────────

    async function startComparison() {
        // Capture edits for current review proposal
        _captureReviewEdits(State._reviewIdx);
        _cleanupBlobUrls();

        State.phase = 'comparing';
        const body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML =
            '<div class="pc-loading">' +
                '<div class="pc-spinner"></div>' +
                '<div class="pc-loading-text">Aligning and comparing ' + State.proposals.length + ' proposals...</div>' +
            '</div>';

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

        body.innerHTML =
            '<div class="pc-results">' +
                '<div class="pc-results-header">' +
                    '<h3>Proposal Comparison \u2014 ' + cmp.proposals.length + ' Proposals</h3>' +
                    '<div style="display:flex;gap:8px">' +
                        '<button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">' +
                            '<i data-lucide="arrow-left"></i> New Compare' +
                        '</button>' +
                        (State.proposals.length > 0
                            ? '<button class="pc-btn pc-btn-ghost" onclick="ProposalCompare._backToReview()">' +
                                '<i data-lucide="pencil"></i> Back to Review' +
                              '</button>'
                            : '') +
                        '<button class="pc-btn pc-btn-primary" onclick="ProposalCompare._export()">' +
                            '<i data-lucide="download"></i> Export XLSX' +
                        '</button>' +
                        '<button class="pc-btn pc-btn-gold" onclick="ProposalCompare._exportHTML()">' +
                            '<i data-lucide="globe"></i> Export Interactive HTML' +
                        '</button>' +
                    '</div>' +
                '</div>' +
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

        html += '<div class="pc-exec-heroes">';
        html += renderHeroCard('layers', lineItemCount, 'Line Items Compared', '#2196f3');
        html += renderHeroCard('users', propIds.length, 'Vendors', '#D6A84A');
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
            canvas.parentElement.style.display = 'none';
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
                            if (it.variance_pct > 50) return 'rgba(244,67,54,0.75)';
                            if (it.variance_pct > 25) return 'rgba(255,152,0,0.75)';
                            return 'rgba(214,168,74,0.75)';
                        }),
                        borderWidth: 0,
                        borderRadius: 3,
                        borderSkipped: false,
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
                            grid: { color: 'rgba(128,128,128,0.1)' },
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
                            stacked: true,
                            beginAtZero: true,
                            ticks: {
                                callback: function(v) { return formatMoneyShort(v); },
                                color: secondaryColor,
                                font: { size: 11 },
                            },
                            grid: { color: 'rgba(128,128,128,0.1)' },
                        },
                        x: {
                            stacked: true,
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

        // Legend
        var html = '<div class="pc-hm-legend">' +
            '<span class="pc-hm-legend-label">Deviation from average:</span>' +
            '<span class="pc-hm-swatch" style="background:#2d6a2d;color:#fff">&lt; -15%</span>' +
            '<span class="pc-hm-swatch" style="background:#4caf50;color:#fff">-5% to -15%</span>' +
            '<span class="pc-hm-swatch" style="background:#f5f5f5;color:#333">\u00b15%</span>' +
            '<span class="pc-hm-swatch" style="background:#ff9800;color:#fff">+5% to +15%</span>' +
            '<span class="pc-hm-swatch" style="background:#f44336;color:#fff">&gt; +15%</span>' +
            '<span class="pc-hm-swatch" style="background:#e0e0e0;color:#999">Missing</span>' +
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
                    cellContent = formatMoney(cell.amount) +
                        '<div class="pc-hm-dev">' +
                        (cell.deviation_pct > 0 ? '+' : '') + (cell.deviation_pct != null ? cell.deviation_pct.toFixed(1) + '%' : '') +
                        '</div>';
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
                '<canvas id="pc-chart-radar" height="300"></canvas>' +
            '</div>' +
            '<div class="pc-chart-container" id="pc-chart-scores-wrap">' +
                '<canvas id="pc-chart-scores" height="250"></canvas>' +
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
                            max: 100,
                            ticks: {
                                stepSize: 20,
                                display: true,
                                color: radarSecondary,
                                font: { size: 10 },
                                backdropColor: 'transparent',
                            },
                            grid: { color: radarGrid },
                            pointLabels: {
                                color: radarTextColor,
                                font: { size: 12, weight: '600' },
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

        _applyChartDefaults();
        var scTextColor = _getChartTextColor();
        var scSecondary = _getChartSecondaryColor();

        try {
            var chart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: propIds,
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
            a.download = 'AEGIS_Proposal_Comparison.xlsx';
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            if (window.showToast) {
                window.showToast('Comparison exported to XLSX', 'success');
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Export error:', err);
            if (window.showToast) {
                window.showToast('Export failed: ' + err.message, 'error');
            }
        }
    }

    async function exportHTML() {
        if (!State.comparison) return;

        try {
            if (window.showToast) {
                window.showToast('Generating interactive HTML report...', 'info');
            }

            var exportData = Object.assign({}, State.comparison, {
                metadata: Object.assign({}, State.comparison.metadata || {}, {
                    project_name: State.projectId ? (State.projectName || 'Comparison') : 'Comparison',
                    compared_at: new Date().toISOString(),
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
            a.download = fname;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            if (window.showToast) {
                window.showToast('Interactive HTML report exported!', 'success');
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

        } catch(err) {
            console.error('[PC Dashboard] Detail fetch error:', err);
            if (window.showToast) window.showToast('Failed to load project: ' + err.message, 'error');
        }
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
        close: close,
        // Internal callbacks (used by onclick in HTML)
        _removeFile: removeFile,
        _restart: function() { _cleanupBlobUrls(); State._reviewIdx = 0; State._lineItemEditorOpen = []; renderUploadPhase(); },
        _backToReview: function() { renderReviewPhase(); },
        _export: exportXLSX,
        _exportHTML: exportHTML,
        _loadHistory: renderHistoryView,
        // Project dashboard (Part B)
        _openDashboard: renderProjectDashboard,
        _openProjectDetail: renderProjectDetail,
        _tagToProject: _showTagToProjectMenu,
    };
})();
