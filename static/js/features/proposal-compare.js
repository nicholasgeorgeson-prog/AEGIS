/**
 * AEGIS Proposal Compare Module
 * Upload 2+ proposal docs (DOCX/PDF/XLSX), extract financial data,
 * and display side-by-side comparison matrix.
 *
 * Pure extraction — NO AI/LLM. Displays only what's found in documents.
 *
 * @version 1.0.0
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
        activeTab: 'comparison', // 'comparison' | 'categories' | 'details' | 'tables'
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
        document.body.classList.add('modal-open');
        reset();
        renderUploadPhase();
        if (window.lucide) window.lucide.createIcons();
    }

    function close() {
        const modal = document.getElementById('pc-modal');
        if (modal) modal.classList.remove('active');
        document.body.classList.remove('modal-open');
    }

    function reset() {
        State.phase = 'upload';
        State.files = [];
        State.proposals = [];
        State.comparison = null;
        State.activeTab = 'comparison';
    }

    // ──────────────────────────────────────────
    // Format helpers
    // ──────────────────────────────────────────

    function formatMoney(amount) {
        if (amount == null) return '—';
        return '$' + amount.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function formatVariance(pct) {
        if (pct == null) return '—';
        const cls = pct < 10 ? 'pc-variance-low' : pct < 30 ? 'pc-variance-mid' : 'pc-variance-high';
        return `<span class="${cls}">${pct.toFixed(1)}%</span>`;
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

    // ──────────────────────────────────────────
    // Phase: Upload
    // ──────────────────────────────────────────

    function renderUploadPhase() {
        const body = document.getElementById('pc-body');
        if (!body) return;

        State.phase = 'upload';

        body.innerHTML = `
            <div class="pc-phase-indicator">
                <div class="pc-phase-step active">
                    <span class="pc-step-num">1</span> Upload
                </div>
                <div class="pc-phase-connector"></div>
                <div class="pc-phase-step">
                    <span class="pc-step-num">2</span> Extract
                </div>
                <div class="pc-phase-connector"></div>
                <div class="pc-phase-step">
                    <span class="pc-step-num">3</span> Compare
                </div>
            </div>

            <div class="pc-upload-area">
                <div class="pc-dropzone" id="pc-dropzone">
                    <input type="file" class="pc-file-input" id="pc-file-input"
                           multiple accept=".xlsx,.xls,.docx,.pdf">
                    <div class="pc-dropzone-icon">
                        <i data-lucide="upload-cloud"></i>
                    </div>
                    <h3>Drop proposal files here</h3>
                    <p>Supports DOCX, PDF, and Excel files • 2-10 files</p>
                </div>

                <div class="pc-file-list" id="pc-file-list"></div>

                <div class="pc-upload-actions">
                    <button class="pc-btn pc-btn-primary" id="pc-btn-extract" disabled>
                        <i data-lucide="scan-search"></i> Extract Financial Data
                    </button>
                </div>
            </div>
        `;

        // Wire up events
        const dropzone = document.getElementById('pc-dropzone');
        const fileInput = document.getElementById('pc-file-input');
        const extractBtn = document.getElementById('pc-btn-extract');

        dropzone.addEventListener('click', () => fileInput.click());
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files).filter(f => {
                const ext = '.' + f.name.split('.').pop().toLowerCase();
                return ['.xlsx', '.xls', '.docx', '.pdf'].includes(ext);
            });
            addFiles(files);
        });

        fileInput.addEventListener('change', () => {
            addFiles(Array.from(fileInput.files));
            fileInput.value = '';
        });

        extractBtn.addEventListener('click', startExtraction);

        if (window.lucide) window.lucide.createIcons();
    }

    function addFiles(newFiles) {
        for (const f of newFiles) {
            // Don't add duplicates
            if (State.files.some(sf => sf.name === f.name && sf.size === f.size)) continue;
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

        list.innerHTML = State.files.map((f, idx) => {
            const ext = '.' + f.name.split('.').pop().toLowerCase();
            return `
                <div class="pc-file-item">
                    <div class="pc-file-icon ${fileIconClass(ext)}">
                        <i data-lucide="${fileIcon(ext)}"></i>
                    </div>
                    <div class="pc-file-info">
                        <div class="pc-file-name">${f.name}</div>
                        <div class="pc-file-meta">${formatBytes(f.size)}</div>
                    </div>
                    <button class="pc-file-remove" onclick="ProposalCompare._removeFile(${idx})" title="Remove">
                        <i data-lucide="x" style="width:16px;height:16px"></i>
                    </button>
                </div>
            `;
        }).join('');

        if (window.lucide) window.lucide.createIcons();
    }

    function updateExtractButton() {
        const btn = document.getElementById('pc-btn-extract');
        if (btn) {
            btn.disabled = State.files.length < 2;
        }
    }

    // ──────────────────────────────────────────
    // Phase: Extraction
    // ──────────────────────────────────────────

    async function startExtraction() {
        State.phase = 'extracting';
        const body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML = `
            <div class="pc-phase-indicator">
                <div class="pc-phase-step done">
                    <span class="pc-step-num">✓</span> Upload
                </div>
                <div class="pc-phase-connector done"></div>
                <div class="pc-phase-step active">
                    <span class="pc-step-num">2</span> Extract
                </div>
                <div class="pc-phase-connector"></div>
                <div class="pc-phase-step">
                    <span class="pc-step-num">3</span> Compare
                </div>
            </div>
            <div class="pc-loading">
                <div class="pc-spinner"></div>
                <div class="pc-loading-text">Extracting financial data from ${State.files.length} files...</div>
            </div>
            <div class="pc-file-list" id="pc-extract-list"></div>
        `;

        // Show file extraction progress
        const extractList = document.getElementById('pc-extract-list');
        if (extractList) {
            extractList.innerHTML = State.files.map((f, idx) => {
                const ext = '.' + f.name.split('.').pop().toLowerCase();
                return `
                    <div class="pc-file-item" id="pc-extract-item-${idx}">
                        <div class="pc-file-icon ${fileIconClass(ext)}">
                            <i data-lucide="${fileIcon(ext)}"></i>
                        </div>
                        <div class="pc-file-info">
                            <div class="pc-file-name">${f.name}</div>
                            <div class="pc-file-meta" id="pc-extract-meta-${idx}">Waiting...</div>
                        </div>
                        <div class="pc-file-status extracting" id="pc-extract-status-${idx}">Extracting</div>
                    </div>
                `;
            }).join('');
        }

        if (window.lucide) window.lucide.createIcons();

        // Upload and extract
        const formData = new FormData();
        State.files.forEach(f => formData.append('files[]', f));

        try {
            const resp = await fetch('/api/proposal-compare/upload', {
                method: 'POST',
                headers: { 'X-CSRF-Token': getCSRF() },
                body: formData,
            });

            const result = await resp.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Upload failed');
            }

            // Process results
            State.proposals = [];
            const results = result.data?.results || [];

            results.forEach((r, idx) => {
                const metaEl = document.getElementById(`pc-extract-meta-${idx}`);
                const statusEl = document.getElementById(`pc-extract-status-${idx}`);

                if (r.success && r.data) {
                    State.proposals.push(r.data);
                    const items = r.data.line_items?.length || 0;
                    const tables = r.data.tables?.length || 0;
                    const total = r.data.total_raw || 'N/A';
                    if (metaEl) metaEl.textContent = `${items} line items • ${tables} tables • Total: ${total}`;
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

            // Auto-advance to review if we got at least 2 proposals
            if (State.proposals.length >= 2) {
                setTimeout(() => renderReviewPhase(), 1200);
            } else {
                // Show error state
                const loadingEl = body.querySelector('.pc-loading');
                if (loadingEl) {
                    loadingEl.innerHTML = `
                        <div class="pc-empty">
                            <i data-lucide="alert-circle"></i>
                            <h4>Insufficient Data</h4>
                            <p>Need at least 2 successfully extracted proposals. Got ${State.proposals.length}.</p>
                            <button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">
                                <i data-lucide="arrow-left"></i> Back to Upload
                            </button>
                        </div>
                    `;
                    if (window.lucide) window.lucide.createIcons();
                }
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Extraction error:', err);
            const loadingEl = body.querySelector('.pc-loading');
            if (loadingEl) {
                loadingEl.innerHTML = `
                    <div class="pc-empty">
                        <i data-lucide="alert-triangle"></i>
                        <h4>Extraction Failed</h4>
                        <p>${err.message}</p>
                        <button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">
                            <i data-lucide="arrow-left"></i> Try Again
                        </button>
                    </div>
                `;
                if (window.lucide) window.lucide.createIcons();
            }
        }
    }

    // ──────────────────────────────────────────
    // Phase: Review (edit company names, verify extraction)
    // ──────────────────────────────────────────

    function renderReviewPhase() {
        State.phase = 'review';
        const body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML = `
            <div class="pc-phase-indicator">
                <div class="pc-phase-step done">
                    <span class="pc-step-num">✓</span> Upload
                </div>
                <div class="pc-phase-connector done"></div>
                <div class="pc-phase-step done">
                    <span class="pc-step-num">✓</span> Extract
                </div>
                <div class="pc-phase-connector done"></div>
                <div class="pc-phase-step active">
                    <span class="pc-step-num">3</span> Compare
                </div>
            </div>

            <div class="pc-extraction-summary" id="pc-proposal-cards"></div>

            <div class="pc-upload-actions">
                <button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">
                    <i data-lucide="arrow-left"></i> Start Over
                </button>
                <button class="pc-btn pc-btn-primary" id="pc-btn-compare">
                    <i data-lucide="git-compare-arrows"></i> Compare Proposals
                </button>
            </div>
        `;

        // Render proposal cards
        const cardsEl = document.getElementById('pc-proposal-cards');
        if (cardsEl) {
            cardsEl.innerHTML = State.proposals.map((p, idx) => {
                const company = p.company_name || p.filename;
                const items = p.line_items?.length || 0;
                const tables = p.tables?.length || 0;
                const total = p.total_raw || 'N/A';
                const ext = '.' + (p.file_type || '').toLowerCase();

                return `
                    <div class="pc-proposal-card">
                        <div class="pc-proposal-card-header">
                            <div class="pc-card-icon">
                                <i data-lucide="${fileIcon(ext)}"></i>
                            </div>
                            <h4 title="${p.filename}">${p.filename}</h4>
                        </div>
                        <div class="pc-company-name">
                            <span contenteditable="true" class="pc-editable" id="pc-company-${idx}"
                                  title="Click to edit company name">${company}</span>
                        </div>
                        <div class="pc-card-stats">
                            <div class="pc-card-stat">
                                <div class="pc-card-stat-value">${items}</div>
                                <div class="pc-card-stat-label">Line Items</div>
                            </div>
                            <div class="pc-card-stat">
                                <div class="pc-card-stat-value">${tables}</div>
                                <div class="pc-card-stat-label">Tables</div>
                            </div>
                            <div class="pc-card-stat">
                                <div class="pc-card-stat-value">${total}</div>
                                <div class="pc-card-stat-label">Total</div>
                            </div>
                            <div class="pc-card-stat">
                                <div class="pc-card-stat-value">${p.date || '—'}</div>
                                <div class="pc-card-stat-label">Date</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        document.getElementById('pc-btn-compare')?.addEventListener('click', startComparison);
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Phase: Comparison
    // ──────────────────────────────────────────

    async function startComparison() {
        // Capture any edited company names
        State.proposals.forEach((p, idx) => {
            const nameEl = document.getElementById(`pc-company-${idx}`);
            if (nameEl) {
                p.company_name = nameEl.textContent.trim() || p.filename;
            }
        });

        State.phase = 'comparing';
        const body = document.getElementById('pc-body');
        if (!body) return;

        body.innerHTML = `
            <div class="pc-loading">
                <div class="pc-spinner"></div>
                <div class="pc-loading-text">Aligning and comparing ${State.proposals.length} proposals...</div>
            </div>
        `;

        try {
            const resp = await fetch('/api/proposal-compare/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify({ proposals: State.proposals }),
            });

            const result = await resp.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Comparison failed');
            }

            State.comparison = result.data;
            renderResults();

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Comparison error:', err);
            body.innerHTML = `
                <div class="pc-empty">
                    <i data-lucide="alert-triangle"></i>
                    <h4>Comparison Failed</h4>
                    <p>${err.message}</p>
                    <button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()" style="margin-top:16px">
                        <i data-lucide="arrow-left"></i> Try Again
                    </button>
                </div>
            `;
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

        const cmp = State.comparison;
        if (!cmp) return;

        const propIds = cmp.proposals.map(p => p.id);

        body.innerHTML = `
            <div class="pc-results">
                <div class="pc-results-header">
                    <h3>Proposal Comparison — ${cmp.proposals.length} Proposals</h3>
                    <div style="display:flex;gap:8px">
                        <button class="pc-btn pc-btn-secondary" onclick="ProposalCompare._restart()">
                            <i data-lucide="arrow-left"></i> New Compare
                        </button>
                        <button class="pc-btn pc-btn-primary" onclick="ProposalCompare._export()">
                            <i data-lucide="download"></i> Export XLSX
                        </button>
                    </div>
                </div>

                <!-- Tabs -->
                <div class="pc-tabs">
                    <button class="pc-tab active" data-tab="comparison">
                        <i data-lucide="table-2" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>
                        Comparison
                    </button>
                    <button class="pc-tab" data-tab="categories">
                        <i data-lucide="pie-chart" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>
                        Categories
                    </button>
                    <button class="pc-tab" data-tab="details">
                        <i data-lucide="info" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>
                        Details
                    </button>
                    <button class="pc-tab" data-tab="tables">
                        <i data-lucide="grid-3x3" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>
                        Raw Tables
                    </button>
                </div>

                <!-- Tab panels -->
                <div class="pc-tab-panel active" id="pc-panel-comparison"></div>
                <div class="pc-tab-panel" id="pc-panel-categories"></div>
                <div class="pc-tab-panel" id="pc-panel-details"></div>
                <div class="pc-tab-panel" id="pc-panel-tables"></div>
            </div>
        `;

        // Wire tabs
        body.querySelectorAll('.pc-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                body.querySelectorAll('.pc-tab').forEach(t => t.classList.remove('active'));
                body.querySelectorAll('.pc-tab-panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                const panel = document.getElementById(`pc-panel-${tab.dataset.tab}`);
                if (panel) panel.classList.add('active');
                State.activeTab = tab.dataset.tab;
            });
        });

        // Render each tab
        renderComparisonTable(propIds, cmp);
        renderCategoriesTab(propIds, cmp);
        renderDetailsTab(cmp);
        renderTablesTab(cmp);

        if (window.lucide) window.lucide.createIcons();
    }

    function renderComparisonTable(propIds, cmp) {
        const panel = document.getElementById('pc-panel-comparison');
        if (!panel) return;

        const items = cmp.aligned_items || [];
        if (items.length === 0) {
            panel.innerHTML = `
                <div class="pc-empty">
                    <i data-lucide="search-x"></i>
                    <h4>No Financial Line Items Found</h4>
                    <p>No extractable financial data was found in the uploaded proposals.</p>
                </div>
            `;
            return;
        }

        // Sort by category then description
        const sorted = [...items].sort((a, b) => {
            const catCmp = (a.category || 'zzz').localeCompare(b.category || 'zzz');
            if (catCmp !== 0) return catCmp;
            return (a.description || '').localeCompare(b.description || '');
        });

        // Build table
        let html = `<div class="pc-table-wrap"><table class="pc-table">
            <thead><tr>
                <th style="min-width:200px">Line Item</th>
                <th>Category</th>
                ${propIds.map(id => `<th style="min-width:130px">${id}</th>`).join('')}
                <th>Variance</th>
            </tr></thead>
            <tbody>`;

        let currentCategory = null;
        for (const item of sorted) {
            // Category header
            if (item.category !== currentCategory) {
                currentCategory = item.category;
                html += `<tr class="pc-category-header">
                    <td colspan="${propIds.length + 3}">${currentCategory || 'Uncategorized'}</td>
                </tr>`;
            }

            const amounts = item.amounts || {};
            const valid = Object.values(amounts).filter(a => a != null && a > 0);
            const minAmt = valid.length ? Math.min(...valid) : null;
            const maxAmt = valid.length > 1 ? Math.max(...valid) : null;

            html += `<tr>
                <td title="${item.description}">${truncate(item.description, 60)}</td>
                <td>${item.category || ''}</td>`;

            for (const pid of propIds) {
                const amt = amounts[pid];
                if (amt != null) {
                    let cls = 'pc-amount';
                    if (valid.length > 1) {
                        if (amt === minAmt) cls += ' pc-amount-lowest';
                        else if (amt === maxAmt) cls += ' pc-amount-highest';
                    }
                    html += `<td class="${cls}">${formatMoney(amt)}</td>`;
                } else {
                    html += `<td class="pc-amount pc-amount-missing">—</td>`;
                }
            }

            html += `<td class="pc-variance">${formatVariance(item.variance_pct)}</td>`;
            html += `</tr>`;
        }

        // Grand total row
        html += `<tr class="pc-total-row">
            <td>GRAND TOTAL</td>
            <td></td>`;
        for (const pid of propIds) {
            const total = cmp.totals?.[pid];
            html += `<td class="pc-amount">${formatMoney(total)}</td>`;
        }
        html += `<td class="pc-variance">${formatVariance(cmp.total_variance_pct)}</td>`;
        html += `</tr>`;

        html += `</tbody></table></div>`;

        // Summary notes
        if (cmp.notes && cmp.notes.length) {
            html += `<div style="margin-top:12px;font-size:12px;color:var(--text-secondary,#666)">
                ${cmp.notes.map(n => `<div>• ${n}</div>`).join('')}
            </div>`;
        }

        panel.innerHTML = html;
    }

    function renderCategoriesTab(propIds, cmp) {
        const panel = document.getElementById('pc-panel-categories');
        if (!panel) return;

        const cats = cmp.category_summaries || [];
        if (cats.length === 0) {
            panel.innerHTML = '<div class="pc-empty"><h4>No category data</h4></div>';
            return;
        }

        let html = `<div class="pc-table-wrap"><table class="pc-table">
            <thead><tr>
                <th>Category</th>
                <th>Items</th>
                ${propIds.map(id => `<th>${id}</th>`).join('')}
            </tr></thead>
            <tbody>`;

        for (const cat of cats) {
            html += `<tr>
                <td><strong>${cat.category}</strong></td>
                <td>${cat.item_count}</td>`;

            const totals = cat.totals || {};
            const valid = Object.values(totals).filter(t => t > 0);
            const minT = valid.length ? Math.min(...valid) : null;
            const maxT = valid.length > 1 ? Math.max(...valid) : null;

            for (const pid of propIds) {
                const t = totals[pid];
                let cls = 'pc-amount';
                if (t && valid.length > 1) {
                    if (t === minT) cls += ' pc-amount-lowest';
                    else if (t === maxT) cls += ' pc-amount-highest';
                }
                html += `<td class="${cls}">${t ? formatMoney(t) : '—'}</td>`;
            }
            html += `</tr>`;
        }

        html += `</tbody></table></div>`;
        panel.innerHTML = html;
    }

    function renderDetailsTab(cmp) {
        const panel = document.getElementById('pc-panel-details');
        if (!panel) return;

        const proposals = cmp.proposals || [];
        let html = '<div class="pc-extraction-summary">';

        for (const p of proposals) {
            html += `
                <div class="pc-proposal-card">
                    <div class="pc-proposal-card-header">
                        <div class="pc-card-icon">
                            <i data-lucide="building-2"></i>
                        </div>
                        <h4>${p.company_name || p.filename}</h4>
                    </div>
                    <div class="pc-card-stats">
                        <div class="pc-card-stat">
                            <div class="pc-card-stat-value">${p.total_raw || '—'}</div>
                            <div class="pc-card-stat-label">Total Amount</div>
                        </div>
                        <div class="pc-card-stat">
                            <div class="pc-card-stat-value">${p.line_item_count || 0}</div>
                            <div class="pc-card-stat-label">Line Items</div>
                        </div>
                        <div class="pc-card-stat">
                            <div class="pc-card-stat-value">${p.table_count || 0}</div>
                            <div class="pc-card-stat-label">Tables</div>
                        </div>
                        <div class="pc-card-stat">
                            <div class="pc-card-stat-value">${p.file_type?.toUpperCase() || '—'}</div>
                            <div class="pc-card-stat-label">File Type</div>
                        </div>
                    </div>
                    ${p.extraction_notes?.length ? `
                        <div style="margin-top:10px;font-size:12px;color:var(--text-secondary,#666)">
                            ${p.extraction_notes.map(n => `<div>• ${n}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        html += '</div>';
        panel.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }

    function renderTablesTab(cmp) {
        const panel = document.getElementById('pc-panel-tables');
        if (!panel) return;

        const proposals = cmp.proposals || [];
        let html = '';

        for (const p of proposals) {
            const propData = State.proposals.find(sp => sp.filename === p.filename);
            if (!propData || !propData.tables?.length) continue;

            html += `<h4 style="margin:16px 0 8px;color:var(--text-primary)">${p.company_name || p.filename}</h4>`;

            for (const table of propData.tables) {
                if (!table.rows?.length) continue;

                const finBadge = table.has_financial_data
                    ? '<span style="background:rgba(214,168,74,0.15);color:#D6A84A;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;margin-left:8px">Financial</span>'
                    : '';

                html += `<div style="margin-bottom:16px">
                    <div style="font-size:13px;font-weight:600;color:var(--text-secondary,#666);margin-bottom:6px">
                        ${table.source} — ${table.rows.length} rows ${finBadge}
                    </div>
                    <div class="pc-table-wrap">
                        <table class="pc-table">
                            <thead><tr>
                                ${table.headers.map(h => `<th>${h || ''}</th>`).join('')}
                            </tr></thead>
                            <tbody>
                                ${table.rows.slice(0, 50).map(row => `<tr>
                                    ${row.map(cell => `<td>${cell || ''}</td>`).join('')}
                                </tr>`).join('')}
                                ${table.rows.length > 50 ? `<tr><td colspan="${table.headers.length}" style="text-align:center;color:var(--text-secondary)">... ${table.rows.length - 50} more rows</td></tr>` : ''}
                            </tbody>
                        </table>
                    </div>
                </div>`;
            }
        }

        if (!html) {
            html = '<div class="pc-empty"><h4>No tables extracted</h4></div>';
        }

        panel.innerHTML = html;
    }

    // ──────────────────────────────────────────
    // Export
    // ──────────────────────────────────────────

    async function exportXLSX() {
        if (!State.comparison) return;

        try {
            const resp = await fetch('/api/proposal-compare/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRF(),
                },
                body: JSON.stringify(State.comparison),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.error?.message || `Export failed (${resp.status})`);
            }

            // Download the file
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'AEGIS_Proposal_Comparison.xlsx';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            if (window.showToast) {
                window.showToast('Comparison exported to XLSX', 'success');
            }

        } catch (err) {
            console.error('[AEGIS ProposalCompare] Export error:', err);
            if (window.showToast) {
                window.showToast(`Export failed: ${err.message}`, 'error');
            }
        }
    }

    // ──────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────

    function truncate(str, max) {
        if (!str) return '';
        return str.length > max ? str.substring(0, max) + '...' : str;
    }

    // ──────────────────────────────────────────
    // Public API
    // ──────────────────────────────────────────

    return {
        open,
        close,
        // Internal callbacks (used by onclick in HTML)
        _removeFile: removeFile,
        _restart: function() { renderUploadPhase(); },
        _export: exportXLSX,
    };
})();
