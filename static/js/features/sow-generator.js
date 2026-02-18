/**
 * SOW Generator Module
 * ====================
 * IIFE module for Statement of Work generation.
 * Loads data from AEGIS, configures SOW sections, and generates
 * standalone HTML SOW documents via the backend API.
 *
 * v4.6.1: Added document selection — users can pick which documents
 *         to include in the SOW. Stats and directive chart update
 *         dynamically based on selection.
 *
 * @version 1.1.0 (v4.6.1)
 */

window.SowGenerator = (function() {
    'use strict';

    // =========================================================================
    // STATE
    // =========================================================================

    let modal = null;
    let initialized = false;
    let sowData = null; // Cached data from /api/sow/data
    let isLoading = false;
    let selectedDocIds = new Set(); // v4.6.1: Track selected document IDs
    let templateFile = null; // v5.9.16: User-uploaded DOCX template

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    function init() {
        modal = document.getElementById('modal-sow-generator');
        if (!modal) {
            console.warn('[SowGenerator] Modal not found');
            return;
        }

        if (initialized) return;
        initialized = true;

        // Close button
        const closeBtn = document.getElementById('sow-btn-close');
        const cancelBtn = document.getElementById('sow-btn-cancel');
        if (closeBtn) closeBtn.addEventListener('click', close);
        if (cancelBtn) cancelBtn.addEventListener('click', close);

        // Backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close();
        });

        // Generate button
        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn) genBtn.addEventListener('click', generate);

        // Set default date
        const dateInput = document.getElementById('sow-date');
        if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];

        // ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
                close();
            }
        });

        // v4.6.1: Select All / None buttons
        const selectAllBtn = document.getElementById('sow-select-all');
        const selectNoneBtn = document.getElementById('sow-select-none');
        if (selectAllBtn) selectAllBtn.addEventListener('click', selectAllDocs);
        if (selectNoneBtn) selectNoneBtn.addEventListener('click', selectNoDocs);

        // v5.9.16: Template upload handlers
        initTemplateUpload();

        console.log('[SowGenerator] Initialized');
    }

    // =========================================================================
    // OPEN / CLOSE
    // =========================================================================

    async function open() {
        if (!modal) init();
        if (!modal) return;

        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch (_) {}
        }

        // Load data
        await loadData();
    }

    function close() {
        if (modal) {
            modal.classList.remove('active');
            document.body.classList.remove('modal-open');
        }

        // v4.6.1: Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage) {
            TWR.LandingPage.show();
        }
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async function loadData() {
        if (isLoading) return;
        isLoading = true;

        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn) {
            genBtn.disabled = true;
            genBtn.innerHTML = '<i data-lucide="loader"></i> Loading...';
        }

        try {
            const csrfToken = window.CSRF_TOKEN
                || document.querySelector('meta[name="csrf-token"]')?.content
                || '';

            const resp = await fetch('/api/sow/data', {
                headers: { 'X-CSRF-Token': csrfToken }
            });

            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

            const result = await resp.json();
            if (!result.success) throw new Error(result.error || 'Failed to load data');

            sowData = result.data;

            // v4.6.1: Default — select ALL documents
            selectedDocIds = new Set(
                (sowData.documents || []).map(d => d.id)
            );

            renderDataSummary();

            if (genBtn) {
                genBtn.disabled = false;
                genBtn.innerHTML = '<i data-lucide="file-output"></i> Generate SOW';
            }
        } catch (err) {
            console.error('[SowGenerator] Failed to load data:', err);
            if (typeof showToast === 'function') {
                showToast('error', 'Failed to load SOW data: ' + err.message);
            }
            if (genBtn) {
                genBtn.disabled = true;
                genBtn.innerHTML = '<i data-lucide="alert-circle"></i> Load Failed';
            }
        } finally {
            isLoading = false;
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch (_) {}
            }
        }
    }

    // =========================================================================
    // RENDER DATA SUMMARY
    // =========================================================================

    function renderDataSummary() {
        if (!sowData) return;

        // Render document list (with checkboxes)
        renderDocList();

        // Update stats and chart based on current selection
        updateSelectedStats();
    }

    /**
     * v4.6.1: Recalculate and display stats based on selected documents.
     * Called whenever the selection changes.
     */
    function updateSelectedStats() {
        if (!sowData) return;

        const allDocs = sowData.documents || [];
        const allStmts = sowData.statements || [];

        // Filter to selected documents
        const selDocs = allDocs.filter(d => selectedDocIds.has(d.id));
        const selStmts = allStmts.filter(s => selectedDocIds.has(s.document_id));

        // Collect unique roles mentioned in selected statements
        const selRoleNames = new Set();
        selStmts.forEach(s => {
            if (s.role) selRoleNames.add(s.role.toLowerCase().trim());
        });

        // Update stat numbers
        const el = (id, val) => {
            const e = document.getElementById(id);
            if (e) e.textContent = val;
        };

        el('sow-count-docs', selDocs.length);
        el('sow-count-stmts', selStmts.length);
        // Roles count: show total roles (not document-filtered) but if nothing selected, 0
        el('sow-count-roles', selDocs.length > 0 ? (sowData.counts?.roles || 0) : 0);
        el('sow-count-cats', selDocs.length > 0 ? (sowData.counts?.categories || 0) : 0);

        // Update selected count label
        const countLabel = document.getElementById('sow-selected-count');
        if (countLabel) {
            const total = allDocs.length;
            const selected = selectedDocIds.size;
            countLabel.textContent = selected === total
                ? `All ${total} selected`
                : `${selected} of ${total} selected`;
        }

        // Render directive breakdown based on selected docs
        renderDirectiveChart(selStmts);

        // Disable generate if no docs selected
        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn && !isLoading) {
            genBtn.disabled = selectedDocIds.size === 0;
        }
    }

    // =========================================================================
    // DOCUMENT LIST WITH CHECKBOXES
    // =========================================================================

    function renderDocList() {
        const container = document.getElementById('sow-doc-list');
        const controls = document.getElementById('sow-doc-controls');
        if (!container || !sowData?.documents) return;

        if (sowData.documents.length === 0) {
            container.innerHTML = '<p class="sow-placeholder">No documents scanned yet. Scan documents first to generate a SOW.</p>';
            if (controls) controls.style.display = 'none';
            return;
        }

        // Show select controls
        if (controls) controls.style.display = 'flex';

        container.innerHTML = sowData.documents.map(doc => {
            const fname = escapeHtml(doc.filename || 'Unknown');
            const words = (doc.word_count || 0).toLocaleString();
            const score = doc.latest_score || '\u2014';
            const isChecked = selectedDocIds.has(doc.id) ? 'checked' : '';
            return `<label class="sow-doc-item sow-doc-selectable" data-doc-id="${doc.id}">
                <input type="checkbox" class="sow-doc-checkbox" value="${doc.id}" ${isChecked}>
                <i data-lucide="file-text"></i>
                <span class="sow-doc-name" title="${fname}">${fname}</span>
                <span class="sow-doc-meta">${words} words</span>
            </label>`;
        }).join('');

        // Attach change handlers via delegation
        container.addEventListener('change', handleDocCheckChange);

        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ attrs: { class: '' } }); } catch (_) {}
        }
    }

    /**
     * Handle checkbox change in document list
     */
    function handleDocCheckChange(e) {
        const cb = e.target.closest('.sow-doc-checkbox');
        if (!cb) return;

        const docId = parseInt(cb.value, 10);
        if (isNaN(docId)) return;

        if (cb.checked) {
            selectedDocIds.add(docId);
        } else {
            selectedDocIds.delete(docId);
        }

        updateSelectedStats();
    }

    /**
     * v4.6.1: Select all documents
     */
    function selectAllDocs() {
        if (!sowData?.documents) return;
        selectedDocIds = new Set(sowData.documents.map(d => d.id));

        // Update all checkboxes
        const container = document.getElementById('sow-doc-list');
        if (container) {
            container.querySelectorAll('.sow-doc-checkbox').forEach(cb => {
                cb.checked = true;
            });
        }
        updateSelectedStats();
    }

    /**
     * v4.6.1: Deselect all documents
     */
    function selectNoDocs() {
        selectedDocIds.clear();

        const container = document.getElementById('sow-doc-list');
        if (container) {
            container.querySelectorAll('.sow-doc-checkbox').forEach(cb => {
                cb.checked = false;
            });
        }
        updateSelectedStats();
    }

    // =========================================================================
    // DIRECTIVE CHART
    // =========================================================================

    function renderDirectiveChart(statements) {
        const stmts = statements || sowData?.statements || [];

        // Count directives
        const counts = { shall: 0, must: 0, will: 0, should: 0, may: 0 };
        stmts.forEach(s => {
            const d = (s.directive || '').toLowerCase().trim();
            if (d in counts) counts[d]++;
        });

        const max = Math.max(1, ...Object.values(counts));

        Object.entries(counts).forEach(([directive, count]) => {
            const bar = document.querySelector(`.sow-dir-bar[data-directive="${directive}"]`);
            if (!bar) return;

            const fill = bar.querySelector('.sow-dir-fill');
            const countEl = bar.querySelector('.sow-dir-count');

            if (fill) fill.style.width = `${(count / max) * 100}%`;
            if (countEl) countEl.textContent = count;
        });
    }

    // =========================================================================
    // TEMPLATE UPLOAD (v5.9.16)
    // =========================================================================

    function initTemplateUpload() {
        const fileInput = document.getElementById('sow-template-file');
        const dropzone = document.getElementById('sow-template-dropzone');
        const browseLink = document.getElementById('sow-template-browse');
        const removeBtn = document.getElementById('sow-template-remove');

        if (browseLink) {
            browseLink.addEventListener('click', (e) => {
                e.preventDefault();
                fileInput?.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files?.[0];
                if (file) setTemplateFile(file);
            });
        }

        if (dropzone) {
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('sow-template-dragover');
            });
            dropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('sow-template-dragover');
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('sow-template-dragover');
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    if (!file.name.toLowerCase().endsWith('.docx')) {
                        if (typeof showToast === 'function') showToast('error', 'Template must be a .docx file');
                        return;
                    }
                    setTemplateFile(file);
                }
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', clearTemplateFile);
        }
    }

    function setTemplateFile(file) {
        if (!file.name.toLowerCase().endsWith('.docx')) {
            if (typeof showToast === 'function') showToast('error', 'Template must be a .docx file');
            return;
        }

        templateFile = file;

        // Update UI — hide dropzone, show loaded state
        const dropzone = document.getElementById('sow-template-dropzone');
        const loaded = document.getElementById('sow-template-loaded');
        const nameEl = document.getElementById('sow-template-name');

        if (dropzone) dropzone.style.display = 'none';
        if (loaded) loaded.style.display = 'flex';
        if (nameEl) nameEl.textContent = file.name;

        // Update generate button label
        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn && !isLoading) {
            genBtn.innerHTML = '<i data-lucide="file-output"></i> Generate from Template';
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch (_) {}
            }
        }

        console.log('[SowGenerator] Template set:', file.name, `(${(file.size / 1024).toFixed(1)} KB)`);
    }

    function clearTemplateFile() {
        templateFile = null;

        // Reset file input
        const fileInput = document.getElementById('sow-template-file');
        if (fileInput) fileInput.value = '';

        // Update UI — show dropzone, hide loaded state
        const dropzone = document.getElementById('sow-template-dropzone');
        const loaded = document.getElementById('sow-template-loaded');

        if (dropzone) dropzone.style.display = '';
        if (loaded) loaded.style.display = 'none';

        // Restore generate button label
        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn && !isLoading) {
            genBtn.innerHTML = '<i data-lucide="file-output"></i> Generate SOW';
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch (_) {}
            }
        }

        console.log('[SowGenerator] Template cleared');
    }

    // =========================================================================
    // GENERATE SOW
    // =========================================================================

    async function generate() {
        if (!sowData) {
            if (typeof showToast === 'function') showToast('error', 'No data loaded. Please wait for data to load.');
            return;
        }

        if (selectedDocIds.size === 0) {
            if (typeof showToast === 'function') showToast('error', 'Please select at least one document.');
            return;
        }

        const genBtn = document.getElementById('sow-btn-generate');
        if (genBtn) {
            genBtn.disabled = true;
            genBtn.innerHTML = '<i data-lucide="loader"></i> Generating...';
        }

        try {
            const config = buildConfig();

            const csrfToken = window.CSRF_TOKEN
                || document.querySelector('meta[name="csrf-token"]')?.content
                || '';

            let resp;

            if (templateFile) {
                // v5.9.16: Use FormData when a template is uploaded
                const formData = new FormData();
                formData.append('config', JSON.stringify(config));
                formData.append('template', templateFile);

                resp = await fetch('/api/sow/generate', {
                    method: 'POST',
                    headers: { 'X-CSRF-Token': csrfToken },
                    body: formData
                });
            } else {
                // Standard JSON request (no template)
                resp = await fetch('/api/sow/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ config })
                });
            }

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                // Handle structured error objects from handle_api_errors decorator
                const errMsg = typeof err.error === 'string'
                    ? err.error
                    : err.error?.message || err.message || `HTTP ${resp.status}`;
                throw new Error(errMsg);
            }

            // Download the file (HTML or DOCX depending on template mode)
            const blob = await resp.blob();
            const disposition = resp.headers.get('Content-Disposition') || '';
            const match = disposition.match(/filename=([^;]+)/);
            const defaultExt = templateFile ? 'docx' : 'html';
            const filename = match
                ? match[1].trim()
                : `AEGIS_SOW_${new Date().toISOString().split('T')[0]}.${defaultExt}`;

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            if (typeof showToast === 'function') {
                showToast('success', 'SOW generated and downloaded successfully');
            }

            close();

        } catch (err) {
            console.error('[SowGenerator] Generation failed:', err);
            if (typeof showToast === 'function') {
                showToast('error', 'SOW generation failed: ' + err.message);
            }
        } finally {
            if (genBtn) {
                genBtn.disabled = false;
                genBtn.innerHTML = '<i data-lucide="file-output"></i> Generate SOW';
            }
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch (_) {}
            }
        }
    }

    function buildConfig() {
        const val = (id) => (document.getElementById(id)?.value || '').trim();
        const checked = (id) => document.getElementById(id)?.checked ?? true;

        return {
            title: val('sow-title') || 'Statement of Work',
            doc_number: val('sow-doc-number'),
            version: val('sow-version') || '1.0',
            date: val('sow-date') || new Date().toISOString().split('T')[0],
            prepared_by: val('sow-prepared-by'),
            organization: val('sow-organization'),
            intro_text: val('sow-intro-text'),
            scope_text: val('sow-scope-text'),
            // v4.6.1: Pass selected document IDs for backend filtering
            document_ids: Array.from(selectedDocIds),
            sections: {
                intro: checked('sow-sec-intro'),
                scope: checked('sow-sec-scope'),
                documents: checked('sow-sec-documents'),
                requirements: checked('sow-sec-requirements'),
                wbs: checked('sow-sec-wbs'),
                roles: checked('sow-sec-roles'),
                acceptance: checked('sow-sec-acceptance'),
                standards: checked('sow-sec-standards'),
                assumptions: checked('sow-sec-assumptions')
            }
        };
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

    // =========================================================================
    // AUTO-INIT
    // =========================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return { init, open, close };
})();

console.log('[SowGenerator] Module loaded');
