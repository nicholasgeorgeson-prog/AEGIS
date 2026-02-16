/**
 * AEGIS - Mass Statement Review
 * ==============================
 * v4.9.5: Mass review of ALL responsibility statements across ALL roles.
 *
 * Features:
 * - Table view with Role, Statement, Document, Action Type, Status columns
 * - Sortable columns
 * - Filter by status, document, role, flagged
 * - Smart adjudication flags (fragment, wrong, too long, etc.)
 * - Bulk selection with shift-click
 * - Bulk actions: approve, reject, delete
 * - Inline statement editing
 * - View in Document integration
 * - Search across all statements
 */

'use strict';

window.TWR = window.TWR || {};

TWR.MassStatementReview = (function() {
    const VERSION = '1.0.0';
    const LOG_PREFIX = '[MassStmtReview]';

    const State = {
        isOpen: false,
        modal: null,
        statements: [],
        filteredStatements: [],
        summary: {},
        selected: new Set(),  // Set of "role_name|document|statement_index" keys
        lastSelectedIndex: -1,
        sortColumn: 'role_name',
        sortDirection: 'asc',
        filters: {
            status: '',
            document: '',
            role: '',
            search: '',
            flagged_only: false
        },
        editingKey: null,  // Key of statement being edited
        isLightMode: false,
        loading: false
    };

    function log(msg, level = 'log') {
        console[level](`${LOG_PREFIX} ${msg}`);
    }

    function stmtKey(s) {
        return `${s.role_name}|${s.document}|${s.statement_index}`;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function detectThemeMode() {
        const dataTheme = document.body.dataset.theme || document.documentElement.dataset.theme;
        if (dataTheme === 'light') return true;
        if (dataTheme === 'dark') return false;
        const stored = localStorage.getItem('theme') || localStorage.getItem('twr-theme');
        if (stored === 'light') return true;
        if (stored === 'dark') return false;
        return false;
    }

    // ============================================================
    // API CALLS
    // ============================================================

    async function fetchStatements(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.set('review_status', filters.status);
        if (filters.document) params.set('document', filters.document);
        if (filters.role) params.set('role', filters.role);
        if (filters.search) params.set('search', filters.search);
        if (filters.flagged_only) params.set('flagged_only', 'true');

        const url = '/api/roles/all-statements' + (params.toString() ? '?' + params : '');
        const resp = await fetch(url);
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'Failed to fetch statements');
        return data;
    }

    async function bulkUpdateStatements(stmtList, updates) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const headers = { 'Content-Type': 'application/json' };
        if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.content;

        const resp = await fetch('/api/roles/bulk-update-statements', {
            method: 'PUT',
            headers,
            body: JSON.stringify({ statements: stmtList, updates })
        });
        return await resp.json();
    }

    async function bulkDeleteStatements(deletionList) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const headers = { 'Content-Type': 'application/json' };
        if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.content;

        const resp = await fetch('/api/roles/bulk-delete-statements', {
            method: 'POST',
            headers,
            body: JSON.stringify({ deletions: deletionList })
        });
        return await resp.json();
    }

    async function updateSingleStatement(roleName, document, stmtIndex, updates) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const headers = { 'Content-Type': 'application/json' };
        if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.content;

        const resp = await fetch('/api/roles/responsibility', {
            method: 'PUT',
            headers,
            body: JSON.stringify({
                role_name: roleName,
                document: document,
                statement_index: stmtIndex,
                updates
            })
        });
        return await resp.json();
    }

    // ============================================================
    // SORTING & FILTERING
    // ============================================================

    function applySort(statements) {
        const col = State.sortColumn;
        const dir = State.sortDirection === 'asc' ? 1 : -1;

        return [...statements].sort((a, b) => {
            let va = a[col] || '';
            let vb = b[col] || '';

            if (col === 'word_count' || col === 'confidence' || col === 'mention_count') {
                return (Number(va) - Number(vb)) * dir;
            }
            if (col === 'flags') {
                return (a.flags.length - b.flags.length) * dir;
            }
            if (typeof va === 'string') va = va.toLowerCase();
            if (typeof vb === 'string') vb = vb.toLowerCase();
            if (va < vb) return -1 * dir;
            if (va > vb) return 1 * dir;
            return 0;
        });
    }

    function getFilteredStatements() {
        // Server-side filtering already applied, but we can also sort
        State.filteredStatements = applySort(State.statements);
        return State.filteredStatements;
    }

    // ============================================================
    // RENDERING
    // ============================================================

    function flagBadge(flag) {
        const labels = {
            'fragment_short': '⚠️ Too Short',
            'fragment_no_verb': '⚠️ No Verb',
            'wrong_header': '🚫 Header',
            'wrong_number': '🚫 Numbers Only',
            'wrong_too_long': '⚠️ Too Long',
            'wrong_reference': '🚫 Reference',
            'low_confidence': '⚠️ Low Conf'
        };
        const colors = {
            'fragment_short': '#f59e0b',
            'fragment_no_verb': '#f59e0b',
            'wrong_header': '#ef4444',
            'wrong_number': '#ef4444',
            'wrong_too_long': '#f97316',
            'wrong_reference': '#ef4444',
            'low_confidence': '#8b5cf6'
        };
        return `<span class="msr-flag" style="background:${colors[flag] || '#666'};color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;white-space:nowrap">${labels[flag] || flag}</span>`;
    }

    function statusBadge(status) {
        if (status === 'reviewed') return '<span class="msr-status-badge msr-status-reviewed">Reviewed</span>';
        if (status === 'rejected') return '<span class="msr-status-badge msr-status-rejected">Rejected</span>';
        if (status === 'pending') return '<span class="msr-status-badge msr-status-pending">Pending</span>';
        return '<span class="msr-status-badge msr-status-unreviewed">Unreviewed</span>';
    }

    function renderSummaryBar() {
        const s = State.summary;
        const bar = State.modal.querySelector('.msr-summary-bar');
        if (!bar) return;

        bar.innerHTML = `
            <div class="msr-stat msr-stat-total">
                <span class="msr-stat-num">${s.total || 0}</span>
                <span class="msr-stat-label">Total</span>
            </div>
            <div class="msr-stat msr-stat-reviewed">
                <span class="msr-stat-num">${s.reviewed || 0}</span>
                <span class="msr-stat-label">Reviewed</span>
            </div>
            <div class="msr-stat msr-stat-rejected">
                <span class="msr-stat-num">${s.rejected || 0}</span>
                <span class="msr-stat-label">Rejected</span>
            </div>
            <div class="msr-stat msr-stat-unreviewed">
                <span class="msr-stat-num">${s.unreviewed || 0}</span>
                <span class="msr-stat-label">Unreviewed</span>
            </div>
            <div class="msr-stat msr-stat-flagged" title="Statements flagged as potentially problematic">
                <span class="msr-stat-num">${(s.flagged_fragment || 0) + (s.flagged_wrong || 0)}</span>
                <span class="msr-stat-label">Flagged</span>
            </div>
            <div class="msr-stat">
                <span class="msr-stat-num">${s.roles_count || 0}</span>
                <span class="msr-stat-label">Roles</span>
            </div>
            <div class="msr-stat">
                <span class="msr-stat-num">${s.documents_count || 0}</span>
                <span class="msr-stat-label">Documents</span>
            </div>
        `;
    }

    function renderTable() {
        const tbody = State.modal.querySelector('.msr-table-body');
        if (!tbody) return;

        const stmts = getFilteredStatements();

        if (stmts.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="msr-empty">No statements found matching current filters.</td></tr>`;
            return;
        }

        // Virtual rendering for large lists — show max 500
        const displayLimit = 500;
        const display = stmts.slice(0, displayLimit);

        let html = '';
        for (let i = 0; i < display.length; i++) {
            const s = display[i];
            const key = stmtKey(s);
            const isSelected = State.selected.has(key);
            const isEditing = State.editingKey === key;
            const truncText = s.text.length > 200 ? s.text.substring(0, 200) + '...' : s.text;

            html += `<tr class="msr-row ${isSelected ? 'msr-row-selected' : ''} ${s.flags.length ? 'msr-row-flagged' : ''}"
                         data-idx="${i}" data-key="${escapeHtml(key)}">
                <td class="msr-col-check">
                    <input type="checkbox" class="msr-checkbox" ${isSelected ? 'checked' : ''} />
                </td>
                <td class="msr-col-role" title="${escapeHtml(s.role_name)}">
                    <span class="msr-role-name">${escapeHtml(s.role_name)}</span>
                    ${s.category !== 'Role' ? `<span class="msr-role-cat">${escapeHtml(s.category)}</span>` : ''}
                </td>
                <td class="msr-col-statement">
                    ${isEditing ?
                        `<textarea class="msr-edit-textarea" data-key="${escapeHtml(key)}">${escapeHtml(s.text)}</textarea>
                         <div class="msr-edit-actions">
                            <button class="msr-btn msr-btn-sm msr-btn-save" data-key="${escapeHtml(key)}">Save</button>
                            <button class="msr-btn msr-btn-sm msr-btn-cancel" data-key="${escapeHtml(key)}">Cancel</button>
                         </div>` :
                        `<span class="msr-stmt-text" title="${escapeHtml(s.text)}">${escapeHtml(truncText)}</span>`
                    }
                    ${s.flags.length ? `<div class="msr-flags">${s.flags.map(f => flagBadge(f)).join(' ')}</div>` : ''}
                </td>
                <td class="msr-col-doc" title="${escapeHtml(s.document)}">
                    ${escapeHtml(s.document.length > 30 ? '...' + s.document.slice(-27) : s.document)}
                </td>
                <td class="msr-col-action">${escapeHtml(s.action_type || '—')}</td>
                <td class="msr-col-status">${statusBadge(s.review_status)}</td>
                <td class="msr-col-actions">
                    <button class="msr-btn msr-btn-icon msr-btn-edit" title="Edit statement" data-key="${escapeHtml(key)}">✏️</button>
                    <button class="msr-btn msr-btn-icon msr-btn-view" title="View in Document" data-key="${escapeHtml(key)}">📄</button>
                </td>
            </tr>`;
        }

        if (stmts.length > displayLimit) {
            html += `<tr><td colspan="7" class="msr-truncation-notice">
                Showing first ${displayLimit} of ${stmts.length} statements. Use filters to narrow results.
            </td></tr>`;
        }

        tbody.innerHTML = html;
        updateSelectionCount();
    }

    function updateSelectionCount() {
        const countEl = State.modal.querySelector('.msr-selection-count');
        if (countEl) {
            const count = State.selected.size;
            countEl.textContent = count > 0 ? `${count} selected` : '';
            countEl.style.display = count > 0 ? 'inline-block' : 'none';
        }

        // Show/hide bulk action bar
        const bulkBar = State.modal.querySelector('.msr-bulk-bar');
        if (bulkBar) {
            bulkBar.style.display = State.selected.size > 0 ? 'flex' : 'none';
        }
    }

    // ============================================================
    // CREATE MODAL
    // ============================================================

    function createModal() {
        State.isLightMode = detectThemeMode();

        const modal = document.createElement('div');
        modal.className = 'msr-overlay' + (State.isLightMode ? ' msr-light' : '');
        modal.innerHTML = `
            <div class="msr-modal">
                <div class="msr-header">
                    <h2 class="msr-title">Mass Statement Review</h2>
                    <div class="msr-header-actions">
                        <span class="msr-selection-count" style="display:none"></span>
                        <button class="msr-btn msr-btn-close" title="Close (Esc)">✕</button>
                    </div>
                </div>

                <div class="msr-summary-bar"></div>

                <div class="msr-toolbar">
                    <div class="msr-filters">
                        <input type="text" class="msr-filter-input msr-search-input"
                               placeholder="Search statements..." title="Search text" />
                        <select class="msr-filter-select msr-filter-status" title="Filter by status">
                            <option value="">All Statuses</option>
                            <option value="unreviewed">Unreviewed</option>
                            <option value="reviewed">Reviewed</option>
                            <option value="rejected">Rejected</option>
                            <option value="pending">Pending</option>
                        </select>
                        <input type="text" class="msr-filter-input msr-filter-role"
                               placeholder="Filter by role..." title="Role name filter" />
                        <input type="text" class="msr-filter-input msr-filter-doc"
                               placeholder="Filter by document..." title="Document name filter" />
                        <label class="msr-filter-check" title="Show only flagged statements">
                            <input type="checkbox" class="msr-flagged-only" /> Flagged Only
                        </label>
                        <button class="msr-btn msr-btn-sm msr-btn-refresh" title="Refresh">🔄 Refresh</button>
                    </div>
                </div>

                <div class="msr-bulk-bar" style="display:none">
                    <span class="msr-bulk-label">Bulk Actions:</span>
                    <button class="msr-btn msr-btn-sm msr-bulk-approve" title="Mark selected as Reviewed">✅ Approve</button>
                    <button class="msr-btn msr-btn-sm msr-bulk-reject" title="Mark selected as Rejected">❌ Reject</button>
                    <button class="msr-btn msr-btn-sm msr-bulk-delete" title="Delete selected statements">🗑️ Delete</button>
                    <button class="msr-btn msr-btn-sm msr-bulk-clear" title="Clear selection">Clear Selection</button>
                </div>

                <div class="msr-table-wrapper">
                    <table class="msr-table">
                        <thead>
                            <tr>
                                <th class="msr-col-check">
                                    <input type="checkbox" class="msr-select-all" title="Select all" />
                                </th>
                                <th class="msr-col-role msr-sortable" data-col="role_name">Role ▲</th>
                                <th class="msr-col-statement msr-sortable" data-col="text">Statement</th>
                                <th class="msr-col-doc msr-sortable" data-col="document">Document</th>
                                <th class="msr-col-action msr-sortable" data-col="action_type">Action</th>
                                <th class="msr-col-status msr-sortable" data-col="review_status">Status</th>
                                <th class="msr-col-actions">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="msr-table-body">
                            <tr><td colspan="7" class="msr-loading">Loading statements...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;
        attachEventListeners();
        return modal;
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    function attachEventListeners() {
        const modal = State.modal;

        // Close
        modal.querySelector('.msr-btn-close').addEventListener('click', close);
        modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

        // Keyboard
        document.addEventListener('keydown', handleKeyDown);

        // Filters
        let searchTimeout;
        modal.querySelector('.msr-search-input').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                State.filters.search = e.target.value.trim();
                reload();
            }, 300);
        });

        modal.querySelector('.msr-filter-status').addEventListener('change', (e) => {
            State.filters.status = e.target.value;
            reload();
        });

        let roleTimeout;
        modal.querySelector('.msr-filter-role').addEventListener('input', (e) => {
            clearTimeout(roleTimeout);
            roleTimeout = setTimeout(() => {
                State.filters.role = e.target.value.trim();
                reload();
            }, 300);
        });

        let docTimeout;
        modal.querySelector('.msr-filter-doc').addEventListener('input', (e) => {
            clearTimeout(docTimeout);
            docTimeout = setTimeout(() => {
                State.filters.document = e.target.value.trim();
                reload();
            }, 300);
        });

        modal.querySelector('.msr-flagged-only').addEventListener('change', (e) => {
            State.filters.flagged_only = e.target.checked;
            reload();
        });

        modal.querySelector('.msr-btn-refresh').addEventListener('click', () => reload());

        // Sort headers
        modal.querySelectorAll('.msr-sortable').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.col;
                if (State.sortColumn === col) {
                    State.sortDirection = State.sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    State.sortColumn = col;
                    State.sortDirection = 'asc';
                }
                updateSortIndicators();
                renderTable();
            });
        });

        // Select all
        modal.querySelector('.msr-select-all').addEventListener('change', (e) => {
            const checked = e.target.checked;
            State.filteredStatements.forEach(s => {
                const key = stmtKey(s);
                if (checked) State.selected.add(key);
                else State.selected.delete(key);
            });
            renderTable();
        });

        // Table body delegation
        modal.querySelector('.msr-table-body').addEventListener('click', handleTableClick);

        // Bulk actions
        modal.querySelector('.msr-bulk-approve')?.addEventListener('click', () => bulkAction('reviewed'));
        modal.querySelector('.msr-bulk-reject')?.addEventListener('click', () => bulkAction('rejected'));
        modal.querySelector('.msr-bulk-delete')?.addEventListener('click', bulkDelete);
        modal.querySelector('.msr-bulk-clear')?.addEventListener('click', () => {
            State.selected.clear();
            renderTable();
        });
    }

    function handleKeyDown(e) {
        if (!State.isOpen) return;
        if (e.key === 'Escape') {
            if (State.editingKey) {
                State.editingKey = null;
                renderTable();
            } else {
                close();
            }
        }
    }

    function handleTableClick(e) {
        const row = e.target.closest('.msr-row');
        if (!row) return;

        const idx = parseInt(row.dataset.idx);
        const key = row.dataset.key;
        const stmt = State.filteredStatements[idx];
        if (!stmt) return;

        // Checkbox click
        if (e.target.classList.contains('msr-checkbox')) {
            if (e.shiftKey && State.lastSelectedIndex >= 0) {
                // Shift-click range select
                const start = Math.min(State.lastSelectedIndex, idx);
                const end = Math.max(State.lastSelectedIndex, idx);
                for (let i = start; i <= end; i++) {
                    const s = State.filteredStatements[i];
                    if (s) State.selected.add(stmtKey(s));
                }
            } else {
                if (State.selected.has(key)) {
                    State.selected.delete(key);
                } else {
                    State.selected.add(key);
                }
            }
            State.lastSelectedIndex = idx;
            renderTable();
            return;
        }

        // Edit button
        if (e.target.closest('.msr-btn-edit')) {
            State.editingKey = key;
            renderTable();
            // Focus the textarea
            setTimeout(() => {
                const ta = State.modal.querySelector(`.msr-edit-textarea[data-key="${CSS.escape(key)}"]`);
                if (ta) ta.focus();
            }, 50);
            return;
        }

        // Save edit
        if (e.target.closest('.msr-btn-save')) {
            const ta = State.modal.querySelector(`.msr-edit-textarea[data-key="${CSS.escape(key)}"]`);
            if (ta) {
                saveEdit(stmt, ta.value.trim());
            }
            return;
        }

        // Cancel edit
        if (e.target.closest('.msr-btn-cancel')) {
            State.editingKey = null;
            renderTable();
            return;
        }

        // View in Document
        if (e.target.closest('.msr-btn-view')) {
            viewInDocument(stmt);
            return;
        }

        // Click on the statement text to toggle selection
        if (e.target.closest('.msr-stmt-text') || e.target.closest('.msr-role-name')) {
            if (State.selected.has(key)) {
                State.selected.delete(key);
            } else {
                State.selected.add(key);
            }
            State.lastSelectedIndex = idx;
            renderTable();
        }
    }

    function updateSortIndicators() {
        const headers = State.modal.querySelectorAll('.msr-sortable');
        headers.forEach(th => {
            const col = th.dataset.col;
            let label = th.textContent.replace(/[▲▼]/g, '').trim();
            if (col === State.sortColumn) {
                th.textContent = label + (State.sortDirection === 'asc' ? ' ▲' : ' ▼');
                th.classList.add('msr-sorted');
            } else {
                th.textContent = label;
                th.classList.remove('msr-sorted');
            }
        });
    }

    // ============================================================
    // ACTIONS
    // ============================================================

    async function saveEdit(stmt, newText) {
        if (!newText) {
            showToast('error', 'Statement text cannot be empty');
            return;
        }
        try {
            const result = await updateSingleStatement(
                stmt.role_name, stmt.document, stmt.statement_index,
                { text: newText }
            );
            if (result.success) {
                stmt.text = newText;
                stmt.word_count = newText.split(/\s+/).length;
                State.editingKey = null;
                renderTable();
                showToast('success', 'Statement updated');
            } else {
                showToast('error', result.error || 'Failed to update');
            }
        } catch (err) {
            showToast('error', 'Error: ' + err.message);
        }
    }

    async function bulkAction(newStatus) {
        const selectedStmts = getSelectedStatements();
        if (!selectedStmts.length) return;

        const msg = `Mark ${selectedStmts.length} statements as "${newStatus}"?`;
        if (!confirm(msg)) return;

        try {
            const result = await bulkUpdateStatements(
                selectedStmts.map(s => ({
                    role_name: s.role_name,
                    document: s.document,
                    statement_index: s.statement_index
                })),
                { review_status: newStatus }
            );
            if (result.success) {
                // Update local state
                selectedStmts.forEach(s => { s.review_status = newStatus; });
                State.selected.clear();
                renderTable();
                renderSummaryBar();
                showToast('success', `${result.updated} statements updated to "${newStatus}"`);
            } else {
                showToast('error', result.error || 'Bulk update failed');
            }
        } catch (err) {
            showToast('error', 'Error: ' + err.message);
        }
    }

    async function bulkDelete() {
        const selectedStmts = getSelectedStatements();
        if (!selectedStmts.length) return;

        const msg = `DELETE ${selectedStmts.length} statements? This cannot be undone.`;
        if (!confirm(msg)) return;

        try {
            const result = await bulkDeleteStatements(
                selectedStmts.map(s => ({
                    role_name: s.role_name,
                    document: s.document,
                    statement_index: s.statement_index
                }))
            );
            if (result.success) {
                showToast('success', `${result.deleted} statements deleted`);
                State.selected.clear();
                reload();
            } else {
                showToast('error', result.error || 'Bulk delete failed');
            }
        } catch (err) {
            showToast('error', 'Error: ' + err.message);
        }
    }

    function getSelectedStatements() {
        return State.filteredStatements.filter(s => State.selected.has(stmtKey(s)));
    }

    function viewInDocument(stmt) {
        // Use Statement Source Viewer (SSV) for statement-focused viewing
        if (TWR.StatementSourceViewer?.open) {
            TWR.StatementSourceViewer.open(stmt, {
                statements: State.filteredStatements || State.statements,
                currentIndex: (State.filteredStatements || State.statements).findIndex(s =>
                    s.role_name === stmt.role_name && s.document === stmt.document && s.statement_index === stmt.statement_index
                )
            });
        } else if (TWR.RoleSourceViewer?.open) {
            // Fallback to Role Source Viewer
            TWR.RoleSourceViewer.open(stmt.role_name, {
                searchText: stmt.text,
                sourceDocument: stmt.document
            });
            close();
        } else {
            showToast('info', 'Statement Source Viewer not available');
        }
    }

    function showToast(type, msg) {
        if (typeof window.showToast === 'function') {
            window.showToast(type, msg);
        } else {
            log(`Toast [${type}]: ${msg}`);
        }
    }

    // ============================================================
    // LOAD / RELOAD
    // ============================================================

    async function reload() {
        if (State.loading) return;
        State.loading = true;

        try {
            const data = await fetchStatements(State.filters);
            State.statements = data.statements || [];
            State.summary = data.summary || {};
            State.selected.clear();
            State.editingKey = null;

            getFilteredStatements();
            renderSummaryBar();
            renderTable();

            log(`Loaded ${State.statements.length} statements`);
        } catch (err) {
            log('Load error: ' + err.message, 'error');
            const tbody = State.modal?.querySelector('.msr-table-body');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="7" class="msr-error">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
            }
        } finally {
            State.loading = false;
        }
    }

    // ============================================================
    // OPEN / CLOSE
    // ============================================================

    async function open(options = {}) {
        if (State.isOpen) return;
        log('Opening Mass Statement Review');

        State.isOpen = true;

        if (!State.modal) {
            createModal();
        } else {
            State.isLightMode = detectThemeMode();
            if (State.isLightMode) State.modal.classList.add('msr-light');
            else State.modal.classList.remove('msr-light');
        }

        State.modal.classList.add('msr-visible');
        document.body.style.overflow = 'hidden';

        // Apply any initial filters from options
        if (options.flagged_only) {
            State.filters.flagged_only = true;
            const cb = State.modal.querySelector('.msr-flagged-only');
            if (cb) cb.checked = true;
        }

        await reload();
    }

    function close() {
        if (!State.isOpen) return;
        log('Closing Mass Statement Review');
        State.isOpen = false;
        if (State.modal) State.modal.classList.remove('msr-visible');
        document.body.style.overflow = '';
        document.removeEventListener('keydown', handleKeyDown);
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    return {
        VERSION,
        open,
        close,
        reload,
        getState: () => ({ ...State })
    };

})();

console.log('[TWR] MassStatementReview module loaded v' + TWR.MassStatementReview.VERSION);
