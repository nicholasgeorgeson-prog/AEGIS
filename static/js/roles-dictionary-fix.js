/**
 * AEGIS - Role Dictionary Tab (Complete Overhaul)
 * v4.0.5 - Dashboard, Card View, Bulk Ops, Inline Actions, Keyboard Nav,
 *          Adjudication Badges, Enhanced Filtering, Audit Trail,
 *          Duplicate Detection, Role Cloning
 *
 * ROOT CAUSE: In app.js line 6977, the event listener is attached to:
 *   document.querySelectorAll('.roles-tab[data-tab="dictionary"]')
 * But the HTML uses:
 *   <button class="roles-nav-item" data-tab="dictionary">
 *
 * FIX: Add correct event listener using capturing phase.
 */

(function() {
    'use strict';

    console.log('[TWR DictV5] Role Dictionary overhaul loading...');

    // =====================================================================
    // STATE
    // =====================================================================
    const DictState = {
        roles: [],
        filteredRoles: [],
        loaded: false,
        functionCategories: [],
        editingTags: [],
        customCategories: new Set(),
        viewMode: localStorage.getItem('dict-view-mode') || 'table', // 'table' | 'card'
        selectedRoles: new Set(),     // Selected role IDs for bulk ops
        focusIndex: -1,               // Keyboard nav focus
        sortField: 'role_name',
        sortDir: 'asc',
        adjCache: null,               // Adjudication lookup cache
        // Enhanced filters
        filterHasDescription: '',     // '' | 'yes' | 'no'
        filterHasTags: '',            // '' | 'yes' | 'no'
        filterAdjStatus: '',          // '' | 'confirmed' | 'deliverable' | 'rejected' | 'pending'
        dashboardChart: null          // Chart.js instance
    };

    // Prevent duplicate init
    let _dictV5Init = false;

    // =====================================================================
    // UTILITIES
    // =====================================================================
    function getCSRFToken() {
        return window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function showToast(type, message) {
        if (typeof window.showToast === 'function') window.showToast(type, message);
        else if (typeof window.toast === 'function') window.toast(type, message);
        else if (window.TWR?.Modals?.toast) window.TWR.Modals.toast(type, message);
        else console.log(`[${type}] ${message}`);
    }

    function refreshIcons() {
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }

    function timeAgo(dateStr) {
        if (!dateStr) return '-';
        const d = new Date(dateStr);
        const now = new Date();
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        const diffHr = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHr / 24);
        if (diffDay > 30) return d.toLocaleDateString();
        if (diffDay > 0) return `${diffDay}d ago`;
        if (diffHr > 0) return `${diffHr}h ago`;
        if (diffMin > 0) return `${diffMin}m ago`;
        return 'just now';
    }

    function normalizeRoleName(name) {
        return (name || '').toLowerCase().trim().replace(/[^a-z0-9\s]/g, '');
    }

    // =====================================================================
    // DATA LOADING
    // =====================================================================
    async function loadDictionary(forceReload) {
        if (DictState.loaded && DictState.roles.length > 0 && !forceReload) {
            renderCurrentView();
            return;
        }

        // Show loading state
        const container = document.getElementById('dict-content-area');
        if (container) {
            container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">
                <div style="margin:0 auto 12px;width:32px;height:32px;border:3px solid var(--border-default);border-top-color:#D6A84A;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
                Loading role dictionary...
            </div>`;
        }

        try {
            // Load dictionary and adjudication cache in parallel
            const [dictResp] = await Promise.all([
                fetch('/api/roles/dictionary?include_inactive=true'),
                loadAdjudicationCache(),
                loadFunctionCategories()
            ]);

            const result = await dictResp.json();

            if (result.success) {
                DictState.roles = result.data.roles || [];
                DictState.loaded = true;
                applyFilters();
                renderDashboard();
                renderCurrentView();
                updateBulkBar();
                // Show export hierarchy button if SIPOC roles exist
                const exportHierBtn = document.getElementById('btn-export-hierarchy');
                if (exportHierBtn) {
                    exportHierBtn.style.display = DictState.roles.some(r => r.source === 'sipoc') ? '' : 'none';
                }
                console.log('[TWR DictV5] Dictionary loaded:', DictState.roles.length, 'roles');
            } else {
                showDictError('Failed to load dictionary: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[TWR DictV5] Error loading dictionary:', error);
            showDictError('Error loading dictionary: ' + error.message);
        }
    }

    async function loadAdjudicationCache() {
        if (window.AEGIS?.AdjudicationLookup) {
            DictState.adjCache = await AEGIS.AdjudicationLookup.ensureLoaded();
        }
    }

    async function loadFunctionCategories() {
        if (DictState.functionCategories.length > 0) return;
        try {
            const resp = await fetch('/api/function-categories');
            if (resp.ok) {
                const data = await resp.json();
                DictState.functionCategories = data?.data?.categories || data?.categories || [];
            }
        } catch (e) {
            console.warn('[TWR DictV5] Could not load function categories:', e);
        }
    }

    async function loadRoleTags(roleName) {
        try {
            const resp = await fetch(`/api/role-function-tags?role_name=${encodeURIComponent(roleName)}`);
            if (resp.ok) {
                const data = await resp.json();
                const tags = data?.data?.tags || [];
                return tags.map(t => ({
                    id: t.id,
                    code: t.function_code || t.code || '',
                    name: t.function_name || t.name || t.function_code || t.code || '',
                    color: t.function_color || t.color || '#3b82f6'
                }));
            }
        } catch (e) {
            console.warn('[TWR DictV5] Could not load tags for', roleName, e);
        }
        return [];
    }

    // =====================================================================
    // FILTERING & SORTING
    // =====================================================================
    function applyFilters() {
        const searchTerm = (document.getElementById('dict-search')?.value || '').toLowerCase();
        const sourceFilter = document.getElementById('dict-filter-source')?.value || '';
        const categoryFilter = document.getElementById('dict-filter-category')?.value || '';

        DictState.filteredRoles = DictState.roles.filter(role => {
            // Text search
            if (searchTerm) {
                const searchFields = [
                    role.role_name, role.category, role.description,
                    role.notes, ...(role.aliases || [])
                ].filter(Boolean).join(' ').toLowerCase();
                if (!searchFields.includes(searchTerm)) return false;
            }
            // Basic filters
            if (sourceFilter && role.source !== sourceFilter) return false;
            if (categoryFilter && role.category !== categoryFilter) return false;

            // Enhanced filters
            if (DictState.filterHasDescription === 'yes' && !role.description) return false;
            if (DictState.filterHasDescription === 'no' && role.description) return false;

            if (DictState.filterHasTags === 'yes' && !(role.function_tags?.length > 0)) return false;
            if (DictState.filterHasTags === 'no' && role.function_tags?.length > 0) return false;

            // Adjudication status filter
            if (DictState.filterAdjStatus) {
                const adjStatus = getAdjStatus(role);
                if (DictState.filterAdjStatus !== adjStatus) return false;
            }

            return true;
        });

        // Sort
        const field = DictState.sortField;
        const dir = DictState.sortDir === 'asc' ? 1 : -1;
        DictState.filteredRoles.sort((a, b) => {
            let va = a[field] || '', vb = b[field] || '';
            if (typeof va === 'string') va = va.toLowerCase();
            if (typeof vb === 'string') vb = vb.toLowerCase();
            if (va < vb) return -1 * dir;
            if (va > vb) return 1 * dir;
            return 0;
        });

        // Update filter count badge
        const countEl = document.getElementById('dict-filter-count');
        if (countEl) {
            const total = DictState.roles.length;
            const filtered = DictState.filteredRoles.length;
            countEl.textContent = filtered === total ? `${total} roles` : `${filtered} of ${total} roles`;
        }
    }

    function getAdjStatus(role) {
        if (!role.is_active) return 'rejected';
        if (role.is_deliverable) return 'deliverable';
        if (role.source === 'adjudication' || role.source === 'builtin') return 'confirmed';
        return 'pending';
    }

    function getAdjBadgeHtml(role) {
        const status = getAdjStatus(role);
        switch (status) {
            case 'deliverable':
                return '<span class="adj-badge adj-deliverable adj-badge-sm" title="Deliverable">★</span>';
            case 'confirmed':
                return '<span class="adj-badge adj-confirmed adj-badge-sm" title="Confirmed">✓</span>';
            case 'rejected':
                return '<span class="adj-badge adj-rejected adj-badge-sm" title="Rejected">✗</span>';
            default:
                return '<span class="dict-pending-dot" title="Pending review"></span>';
        }
    }

    // =====================================================================
    // DASHBOARD
    // =====================================================================
    function renderDashboard() {
        const dashEl = document.getElementById('dict-dashboard');
        if (!dashEl) return;

        const roles = DictState.roles;
        const total = roles.length;
        const active = roles.filter(r => r.is_active).length;
        const inactive = total - active;
        const deliverable = roles.filter(r => r.is_deliverable).length;
        const withDesc = roles.filter(r => r.description?.trim()).length;
        const withTags = roles.filter(r => r.function_tags?.length > 0).length;
        const healthPct = total > 0 ? Math.round(((withDesc + withTags) / (total * 2)) * 100) : 0;

        // Category distribution
        const catCounts = {};
        roles.forEach(r => {
            const cat = r.category || 'Uncategorized';
            catCounts[cat] = (catCounts[cat] || 0) + 1;
        });
        const catEntries = Object.entries(catCounts).sort((a, b) => b[1] - a[1]);

        // Source distribution
        const srcCounts = {};
        roles.forEach(r => {
            const src = r.source || 'manual';
            srcCounts[src] = (srcCounts[src] || 0) + 1;
        });

        const adjStats = { confirmed: 0, deliverable: 0, rejected: 0, pending: 0 };
        roles.forEach(r => { adjStats[getAdjStatus(r)]++; });

        dashEl.innerHTML = `
            <div class="dict-dash-grid">
                <div class="dict-dash-tile dict-dash-tile-total">
                    <div class="dict-dash-icon"><i data-lucide="book-open"></i></div>
                    <div class="dict-dash-value">${total}</div>
                    <div class="dict-dash-label">Total Roles</div>
                    <div class="dict-dash-sub">${active} active · ${inactive} inactive</div>
                </div>
                <div class="dict-dash-tile dict-dash-tile-deliverable">
                    <div class="dict-dash-icon"><i data-lucide="star"></i></div>
                    <div class="dict-dash-value">${deliverable}</div>
                    <div class="dict-dash-label">Deliverables</div>
                    <div class="dict-dash-sub">${total > 0 ? Math.round(deliverable/total*100) : 0}% of dictionary</div>
                </div>
                <div class="dict-dash-tile dict-dash-tile-adj">
                    <div class="dict-dash-icon"><i data-lucide="shield-check"></i></div>
                    <div class="dict-dash-value">${adjStats.confirmed + adjStats.deliverable}</div>
                    <div class="dict-dash-label">Adjudicated</div>
                    <div class="dict-dash-sub">
                        <span style="color:#10b981;">✓${adjStats.confirmed}</span>
                        <span style="color:#D6A84A;">★${adjStats.deliverable}</span>
                        <span style="color:#ef4444;">✗${adjStats.rejected}</span>
                        <span style="color:#6b7280;">○${adjStats.pending}</span>
                    </div>
                </div>
                <div class="dict-dash-tile dict-dash-tile-health">
                    <div class="dict-dash-icon"><i data-lucide="heart-pulse"></i></div>
                    <div class="dict-dash-value">${healthPct}%</div>
                    <div class="dict-dash-label">Health Score</div>
                    <div class="dict-dash-sub">${withDesc} described · ${withTags} tagged</div>
                    <div class="dict-health-bar">
                        <div class="dict-health-fill" style="width:${healthPct}%;"></div>
                    </div>
                </div>
            </div>
            <div class="dict-dash-charts">
                <div class="dict-chart-box">
                    <div class="dict-chart-title">Category Distribution</div>
                    <canvas id="dict-category-chart" width="180" height="180"></canvas>
                </div>
                <div class="dict-chart-box">
                    <div class="dict-chart-title">Source Breakdown</div>
                    <div class="dict-source-bars">
                        ${Object.entries(srcCounts).map(([src, cnt]) => {
                            const pct = total > 0 ? Math.round(cnt / total * 100) : 0;
                            const colors = { builtin: '#3b82f6', manual: '#8b5cf6', adjudication: '#10b981', upload: '#f59e0b', history: '#06b6d4' };
                            const color = colors[src] || '#6b7280';
                            return `<div class="dict-src-row">
                                <span class="dict-src-label"><span class="dict-src-dot" style="background:${color}"></span>${escapeHtml(src)}</span>
                                <div class="dict-src-bar-track"><div class="dict-src-bar-fill" style="width:${pct}%;background:${color};"></div></div>
                                <span class="dict-src-count">${cnt}</span>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
                <div class="dict-chart-box">
                    <div class="dict-chart-title">Top Categories</div>
                    <div class="dict-cat-list">
                        ${catEntries.slice(0, 8).map(([cat, cnt]) => {
                            const pct = total > 0 ? Math.round(cnt / total * 100) : 0;
                            return `<div class="dict-cat-row">
                                <span class="dict-cat-name">${escapeHtml(cat)}</span>
                                <div class="dict-cat-bar-track"><div class="dict-cat-bar-fill" style="width:${pct}%;"></div></div>
                                <span class="dict-cat-count">${cnt}</span>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;

        refreshIcons();

        // Render donut chart
        setTimeout(() => renderCategoryDonut(catEntries), 50);
    }

    function renderCategoryDonut(catEntries) {
        const canvas = document.getElementById('dict-category-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        // Destroy existing chart
        if (DictState.dashboardChart) {
            DictState.dashboardChart.destroy();
            DictState.dashboardChart = null;
        }

        const topCats = catEntries.slice(0, 7);
        const otherCount = catEntries.slice(7).reduce((s, e) => s + e[1], 0);
        if (otherCount > 0) topCats.push(['Other', otherCount]);

        const catColors = [
            '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
            '#06b6d4', '#ec4899', '#6b7280'
        ];

        DictState.dashboardChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: topCats.map(e => e[0]),
                datasets: [{
                    data: topCats.map(e => e[1]),
                    backgroundColor: catColors.slice(0, topCats.length),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: false,
                cutout: '65%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${ctx.raw} roles`
                        }
                    }
                }
            }
        });

        // Center text
        setTimeout(() => {
            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            const total = topCats.reduce((s, e) => s + e[1], 0);
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            ctx.save();
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--text-primary').trim() || '#1e293b';
            ctx.font = 'bold 22px -apple-system, sans-serif';
            ctx.fillText(total, centerX, centerY - 6);
            ctx.font = '10px -apple-system, sans-serif';
            ctx.fillStyle = '#6b7280';
            ctx.fillText('roles', centerX, centerY + 12);
            ctx.restore();
        }, 100);
    }

    // =====================================================================
    // TABLE VIEW RENDERING
    // =====================================================================
    function renderTableView() {
        const container = document.getElementById('dict-content-area');
        if (!container) return;

        const emptyEl = document.getElementById('dict-empty');

        if (DictState.filteredRoles.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'flex';
            return;
        }
        if (emptyEl) emptyEl.style.display = 'none';

        const allChecked = DictState.filteredRoles.every(r => DictState.selectedRoles.has(r.id));

        let html = `<div class="dictionary-table-container">
            <table class="data-table dict-enhanced-table" id="dictionary-table">
                <thead>
                    <tr>
                        <th style="width:36px;" class="dict-th-check">
                            <input type="checkbox" class="dict-select-all" ${allChecked && DictState.filteredRoles.length > 0 ? 'checked' : ''} title="Select all">
                        </th>
                        <th class="dict-th-sortable" data-sort="role_name" style="width:24%;">
                            Role Name ${sortArrow('role_name')}
                        </th>
                        <th class="dict-th-sortable" data-sort="category" style="width:12%;">
                            Category ${sortArrow('category')}
                        </th>
                        <th style="width:8%;">Source</th>
                        <th class="dict-th-sortable" data-sort="updated_at" style="width:12%;">
                            Modified ${sortArrow('updated_at')}
                        </th>
                        <th style="width:8%;">Status</th>
                        <th style="width:10%;">Adj.</th>
                        <th style="width:18%;">Actions</th>
                    </tr>
                </thead>
                <tbody id="dictionary-body">`;

        DictState.filteredRoles.forEach((role, idx) => {
            const aliases = (role.aliases || []).join(', ');
            const updatedAt = role.updated_at || role.created_at;
            const dateStr = timeAgo(updatedAt);
            const fullDate = updatedAt ? new Date(updatedAt).toLocaleString() : '';
            const updatedBy = role.updated_by || role.created_by || '';
            const statusClass = role.is_active ? 'status-active' : 'status-inactive';
            const statusText = role.is_active ? 'Active' : 'Inactive';
            const isSelected = DictState.selectedRoles.has(role.id);
            const isFocused = idx === DictState.focusIndex;
            const adjBadge = getAdjBadgeHtml(role);
            const hasTags = role.function_tags?.length > 0;
            const hasDesc = !!role.description?.trim();

            html += `<tr data-role-id="${role.id}" data-idx="${idx}" class="dict-row${isSelected ? ' dict-row-selected' : ''}${isFocused ? ' dict-row-focused' : ''}">
                <td class="dict-td-check">
                    <input type="checkbox" class="dict-row-check" data-id="${role.id}" ${isSelected ? 'checked' : ''}>
                </td>
                <td class="dict-td-name">
                    <div class="dict-name-wrap">
                        <strong class="dict-role-name-text" title="Click to view details" data-name="${escapeHtml(role.role_name)}" data-role-id="${role.id}">${escapeHtml(role.role_name)}</strong>
                        ${adjBadge}
                    </div>
                    ${aliases ? `<div class="text-muted text-xs dict-aliases">aka: ${escapeHtml(aliases)}</div>` : ''}
                    ${hasDesc ? `<div class="text-muted text-xs dict-desc-preview" title="${escapeHtml(role.description)}">${escapeHtml(role.description.substring(0, 60))}${role.description.length > 60 ? '...' : ''}</div>` : ''}
                    ${hasTags ? `<div class="dict-inline-tags">${role.function_tags.map(t => `<span class="dict-mini-tag">${escapeHtml(typeof t === 'string' ? t : t.code || t)}</span>`).join('')}</div>` : ''}
                </td>
                <td>
                    <span class="category-badge dict-cat-inline" data-id="${role.id}" title="Click to change">${escapeHtml(role.category || 'Role')}</span>
                </td>
                <td><span class="source-badge source-${escapeHtml(role.source || 'manual')}">${escapeHtml(role.source || 'manual')}</span></td>
                <td class="dict-td-date" title="${escapeHtml(fullDate)}${updatedBy ? ' by ' + escapeHtml(updatedBy) : ''}">
                    <span class="dict-date-text">${dateStr}</span>
                    ${updatedBy ? `<span class="dict-by-text">by ${escapeHtml(updatedBy)}</span>` : ''}
                </td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td class="dict-td-adj">${adjBadge}</td>
                <td class="dict-td-actions">
                    <button class="btn btn-ghost btn-xs" data-action="edit" data-id="${role.id}" title="Edit (Enter)">
                        <i data-lucide="edit-2"></i>
                    </button>
                    <button class="btn btn-ghost btn-xs" data-action="clone" data-id="${role.id}" title="Clone role">
                        <i data-lucide="copy"></i>
                    </button>
                    <button class="btn btn-ghost btn-xs" data-action="toggle" data-id="${role.id}" title="${role.is_active ? 'Deactivate' : 'Activate'}">
                        <i data-lucide="${role.is_active ? 'eye-off' : 'eye'}"></i>
                    </button>
                    <label class="dict-deliv-toggle" title="${role.is_deliverable ? 'Unmark deliverable' : 'Mark as deliverable'}">
                        <input type="checkbox" class="dict-deliv-check" data-id="${role.id}" ${role.is_deliverable ? 'checked' : ''}>
                        <span class="dict-deliv-icon">${role.is_deliverable ? '★' : '☆'}</span>
                    </label>
                    <button class="btn btn-ghost btn-xs btn-danger" data-action="delete" data-id="${role.id}" title="Delete">
                        <i data-lucide="trash-2"></i>
                    </button>
                </td>
            </tr>`;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [container] }); } catch (_) { refreshIcons(); }
        }
    }

    function sortArrow(field) {
        if (DictState.sortField !== field) return '<span class="dict-sort-arrow">⇅</span>';
        return DictState.sortDir === 'asc'
            ? '<span class="dict-sort-arrow dict-sort-active">↑</span>'
            : '<span class="dict-sort-arrow dict-sort-active">↓</span>';
    }

    // =====================================================================
    // CARD VIEW RENDERING
    // =====================================================================
    function renderCardView() {
        const container = document.getElementById('dict-content-area');
        if (!container) return;

        const emptyEl = document.getElementById('dict-empty');

        if (DictState.filteredRoles.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'flex';
            return;
        }
        if (emptyEl) emptyEl.style.display = 'none';

        let html = '<div class="dict-card-grid">';

        DictState.filteredRoles.forEach((role, idx) => {
            const adjStatus = getAdjStatus(role);
            const adjBadge = getAdjBadgeHtml(role);
            const aliases = (role.aliases || []).join(', ');
            const hasTags = role.function_tags?.length > 0;
            const hasDesc = !!role.description?.trim();
            const isSelected = DictState.selectedRoles.has(role.id);
            const updatedAt = role.updated_at || role.created_at;
            const dateStr = timeAgo(updatedAt);
            const updatedBy = role.updated_by || role.created_by || '';

            const adjStatusColors = {
                confirmed: '#10b981', deliverable: '#D6A84A', rejected: '#ef4444', pending: '#6b7280'
            };
            const borderColor = adjStatusColors[adjStatus] || '#6b7280';

            html += `<div class="dict-card${isSelected ? ' dict-card-selected' : ''}" data-role-id="${role.id}" data-idx="${idx}" style="border-left: 3px solid ${borderColor};">
                <div class="dict-card-header">
                    <input type="checkbox" class="dict-row-check" data-id="${role.id}" ${isSelected ? 'checked' : ''}>
                    <div class="dict-card-title-row">
                        <strong class="dict-card-name" data-role-id="${role.id}" data-name="${escapeHtml(role.role_name)}" title="Click to view details">${escapeHtml(role.role_name)}</strong>
                        ${adjBadge}
                    </div>
                    <div class="dict-card-actions">
                        <button class="btn btn-ghost btn-xs" data-action="edit" data-id="${role.id}" title="Edit"><i data-lucide="edit-2"></i></button>
                        <button class="btn btn-ghost btn-xs" data-action="clone" data-id="${role.id}" title="Clone"><i data-lucide="copy"></i></button>
                        <button class="btn btn-ghost btn-xs btn-danger" data-action="delete" data-id="${role.id}" title="Delete"><i data-lucide="trash-2"></i></button>
                    </div>
                </div>
                <div class="dict-card-meta">
                    <span class="category-badge">${escapeHtml(role.category || 'Role')}</span>
                    <span class="source-badge source-${escapeHtml(role.source || 'manual')}">${escapeHtml(role.source || 'manual')}</span>
                    <span class="status-badge ${role.is_active ? 'status-active' : 'status-inactive'}">${role.is_active ? 'Active' : 'Inactive'}</span>
                    ${role.is_deliverable ? '<span class="dict-card-star" title="Deliverable">★</span>' : ''}
                </div>
                ${hasDesc ? `<div class="dict-card-desc">${escapeHtml(role.description)}</div>` : ''}
                ${aliases ? `<div class="dict-card-aliases"><span class="text-muted">Aliases:</span> ${escapeHtml(aliases)}</div>` : ''}
                ${hasTags ? `<div class="dict-card-tags">${role.function_tags.map(t => `<span class="dict-mini-tag">${escapeHtml(typeof t === 'string' ? t : t.code || t)}</span>`).join('')}</div>` : ''}
                ${role.notes ? `<div class="dict-card-notes"><i data-lucide="sticky-note" style="width:12px;height:12px;"></i> ${escapeHtml(role.notes.substring(0, 80))}${role.notes.length > 80 ? '...' : ''}</div>` : ''}
                <div class="dict-card-footer">
                    <span class="dict-card-date" title="${updatedBy ? 'by ' + updatedBy : ''}">${dateStr}${updatedBy ? ' · ' + updatedBy : ''}</span>
                    <div class="dict-card-quick">
                        <label class="dict-deliv-toggle" title="${role.is_deliverable ? 'Unmark deliverable' : 'Mark as deliverable'}">
                            <input type="checkbox" class="dict-deliv-check" data-id="${role.id}" ${role.is_deliverable ? 'checked' : ''}>
                            <span class="dict-deliv-icon">${role.is_deliverable ? '★' : '☆'}</span>
                        </label>
                        <button class="btn btn-ghost btn-xs" data-action="toggle" data-id="${role.id}" title="${role.is_active ? 'Deactivate' : 'Activate'}">
                            <i data-lucide="${role.is_active ? 'eye-off' : 'eye'}"></i>
                        </button>
                    </div>
                </div>
            </div>`;
        });

        html += '</div>';
        container.innerHTML = html;
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [container] }); } catch (_) { refreshIcons(); }
        }
    }

    // =====================================================================
    // VIEW SWITCHING
    // =====================================================================
    function renderCurrentView() {
        if (DictState.viewMode === 'card') {
            renderCardView();
        } else if (DictState.viewMode === 'hierarchy') {
            renderHierarchyView();
        } else {
            renderTableView();
        }
        updateBulkBar();
    }

    function setViewMode(mode) {
        DictState.viewMode = mode;
        localStorage.setItem('dict-view-mode', mode);
        document.querySelectorAll('.dict-view-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.view === mode);
        });
        // Show/hide export hierarchy button based on whether SIPOC data exists
        const exportHierBtn = document.getElementById('btn-export-hierarchy');
        if (exportHierBtn) {
            exportHierBtn.style.display = DictState.roles.some(r => r.source === 'sipoc') ? '' : 'none';
        }
        renderCurrentView();
    }

    // =====================================================================
    // BULK OPERATIONS
    // =====================================================================
    function updateBulkBar() {
        const bar = document.getElementById('dict-bulk-bar');
        if (!bar) return;

        const count = DictState.selectedRoles.size;
        if (count === 0) {
            bar.style.display = 'none';
            return;
        }

        bar.style.display = 'flex';
        const countEl = bar.querySelector('.dict-bulk-count');
        if (countEl) countEl.textContent = `${count} selected`;
    }

    function selectAll(checked) {
        if (checked) {
            DictState.filteredRoles.forEach(r => DictState.selectedRoles.add(r.id));
        } else {
            DictState.selectedRoles.clear();
        }
        renderCurrentView();
    }

    function toggleSelect(roleId, checked) {
        if (checked) {
            DictState.selectedRoles.add(roleId);
        } else {
            DictState.selectedRoles.delete(roleId);
        }
        updateBulkBar();
        // Update select-all checkbox
        const selectAllCb = document.querySelector('.dict-select-all');
        if (selectAllCb) {
            selectAllCb.checked = DictState.filteredRoles.every(r => DictState.selectedRoles.has(r.id));
        }
    }

    async function bulkAction(action) {
        if (action === 'clear') {
            DictState.selectedRoles.clear();
            renderCurrentView();
            return;
        }

        const ids = Array.from(DictState.selectedRoles);
        if (ids.length === 0) return;

        if (action === 'delete') {
            if (!confirm(`Delete ${ids.length} roles permanently? This cannot be undone.`)) return;
        }

        if (action === 'set-category') {
            const cat = prompt('Enter category for selected roles:');
            if (!cat) return;
            await bulkSetCategory(ids, cat);
            return;
        }

        const csrfToken = getCSRFToken();

        for (const id of ids) {
            try {
                if (action === 'activate') {
                    await fetch(`/api/roles/dictionary/${id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ is_active: true })
                    });
                } else if (action === 'deactivate') {
                    await fetch(`/api/roles/dictionary/${id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ is_active: false })
                    });
                } else if (action === 'delete') {
                    await fetch(`/api/roles/dictionary/${id}?hard=true`, {
                        method: 'DELETE', headers: { 'X-CSRF-Token': csrfToken }
                    });
                } else if (action === 'mark-deliverable') {
                    await fetch(`/api/roles/dictionary/${id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ is_deliverable: true })
                    });
                } else if (action === 'unmark-deliverable') {
                    await fetch(`/api/roles/dictionary/${id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ is_deliverable: false })
                    });
                }
            } catch (e) {
                console.warn('[TWR DictV5] Bulk action error for id', id, e);
            }
        }

        DictState.selectedRoles.clear();
        showToast('success', `Bulk ${action}: ${ids.length} roles updated`);
        DictState.loaded = false;
        if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
        await loadDictionary(true);
    }

    async function bulkSetCategory(ids, category) {
        const csrfToken = getCSRFToken();
        for (const id of ids) {
            try {
                await fetch(`/api/roles/dictionary/${id}`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ category })
                });
            } catch (e) {
                console.warn('[TWR DictV5] Bulk category error for id', id, e);
            }
        }
        DictState.selectedRoles.clear();
        showToast('success', `Category set to "${category}" for ${ids.length} roles`);
        DictState.loaded = false;
        await loadDictionary(true);
    }

    // =====================================================================
    // INLINE ACTIONS
    // =====================================================================
    async function inlineToggleDeliverable(roleId, isDeliverable) {
        const csrfToken = getCSRFToken();
        try {
            const resp = await fetch(`/api/roles/dictionary/${roleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ is_deliverable: isDeliverable })
            });
            const result = await resp.json();
            if (result.success) {
                const role = DictState.roles.find(r => r.id === roleId);
                if (role) role.is_deliverable = isDeliverable;
                showToast('success', isDeliverable ? 'Marked as deliverable' : 'Unmarked deliverable');
                renderDashboard();
                if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
            }
        } catch (e) {
            showToast('error', 'Failed to update: ' + e.message);
        }
    }

    function copyRoleName(name) {
        navigator.clipboard?.writeText(name).then(() => {
            showToast('success', `Copied "${name}"`);
        }).catch(() => {
            showToast('info', name);
        });
    }

    async function inlineChangeCategory(roleId) {
        const role = DictState.roles.find(r => r.id === roleId);
        if (!role) return;

        const categories = ['Role', 'Management', 'Technical', 'Organization', 'Governance',
            'Engineering', 'Quality', 'Safety', 'Operations', 'Support', 'Compliance',
            'Procurement', 'Leadership', 'Deliverable'];

        // Create inline dropdown
        const el = document.querySelector(`.dict-cat-inline[data-id="${roleId}"]`);
        if (!el) return;

        const select = document.createElement('select');
        select.className = 'form-select dict-inline-cat-select';
        select.style.cssText = 'font-size:11px;padding:2px 4px;width:110px;';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            if (cat === (role.category || 'Role')) opt.selected = true;
            select.appendChild(opt);
        });

        el.replaceWith(select);
        select.focus();

        const finish = async () => {
            const newCat = select.value;
            if (newCat !== role.category) {
                const csrfToken = getCSRFToken();
                try {
                    await fetch(`/api/roles/dictionary/${roleId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ category: newCat })
                    });
                    role.category = newCat;
                    showToast('success', `Category changed to ${newCat}`);
                    renderDashboard();
                } catch (e) {
                    showToast('error', 'Failed: ' + e.message);
                }
            }
            // Replace select back with badge
            const badge = document.createElement('span');
            badge.className = 'category-badge dict-cat-inline';
            badge.dataset.id = roleId;
            badge.title = 'Click to change';
            badge.textContent = role.category || 'Role';
            select.replaceWith(badge);
        };

        select.addEventListener('change', finish);
        select.addEventListener('blur', finish);
    }

    // =====================================================================
    // CLONE ROLE
    // =====================================================================
    async function cloneRole(roleId) {
        const role = DictState.roles.find(r => r.id === roleId);
        if (!role) return;

        const newName = role.role_name + ' (Copy)';
        const csrfToken = getCSRFToken();

        try {
            const resp = await fetch('/api/roles/dictionary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({
                    role_name: newName,
                    category: role.category,
                    aliases: [],
                    description: role.description || '',
                    is_deliverable: role.is_deliverable,
                    notes: role.notes || '',
                    source: 'manual'
                })
            });

            const result = await resp.json();
            if (result.success) {
                showToast('success', `Cloned as "${newName}"`);
                DictState.loaded = false;
                await loadDictionary(true);
            } else {
                showToast('error', result.error || 'Clone failed');
            }
        } catch (e) {
            showToast('error', 'Clone error: ' + e.message);
        }
    }

    // =====================================================================
    // DUPLICATE DETECTION
    // =====================================================================
    function findDuplicates(roleName, currentId) {
        const normalized = normalizeRoleName(roleName);
        if (!normalized) return [];

        return DictState.roles.filter(r => {
            if (currentId && r.id === parseInt(currentId)) return false;
            const rNorm = normalizeRoleName(r.role_name);
            if (rNorm === normalized) return true;
            // Fuzzy: check if one contains the other
            if (normalized.length > 4 && rNorm.length > 4) {
                if (rNorm.includes(normalized) || normalized.includes(rNorm)) return true;
            }
            // Check aliases
            const aliases = (r.aliases || []).map(a => normalizeRoleName(a));
            return aliases.some(a => a === normalized);
        });
    }

    // =====================================================================
    // EDIT MODAL (Enhanced with duplicate detection)
    // =====================================================================
    function populateTagSelect() {
        const select = document.getElementById('edit-role-tag-select');
        if (!select) return;

        const cats = DictState.functionCategories;
        if (!cats.length) {
            select.innerHTML = '<option value="">No function categories available</option>';
            return;
        }

        const childMap = {};
        cats.forEach(c => {
            if (c.parent_code) {
                if (!childMap[c.parent_code]) childMap[c.parent_code] = [];
                childMap[c.parent_code].push(c);
            }
        });

        const topLevel = cats.filter(c => !c.parent_code);
        let html = '<option value="">Select a function tag...</option>';

        topLevel.forEach(parent => {
            html += `<option value="${escapeHtml(parent.code)}" data-color="${escapeHtml(parent.color || '#3b82f6')}">${escapeHtml(parent.name)} (${escapeHtml(parent.code)})</option>`;
            (childMap[parent.code] || []).forEach(child => {
                html += `<option value="${escapeHtml(child.code)}" data-color="${escapeHtml(child.color || parent.color || '#3b82f6')}">&nbsp;&nbsp;${escapeHtml(child.name)} (${escapeHtml(child.code)})</option>`;
                (childMap[child.code] || []).forEach(gc => {
                    html += `<option value="${escapeHtml(gc.code)}" data-color="${escapeHtml(gc.color || child.color || '#3b82f6')}">&nbsp;&nbsp;&nbsp;&nbsp;${escapeHtml(gc.name)} (${escapeHtml(gc.code)})</option>`;
                });
            });
        });

        select.innerHTML = html;
    }

    function renderModalTags() {
        const container = document.getElementById('edit-role-tags-container');
        const emptyMsg = document.getElementById('edit-role-tags-empty');
        if (!container) return;

        container.querySelectorAll('.dict-tag-pill').forEach(el => el.remove());

        if (DictState.editingTags.length === 0) {
            if (emptyMsg) emptyMsg.style.display = '';
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';

        DictState.editingTags.forEach((tag, idx) => {
            const pill = document.createElement('span');
            pill.className = 'dict-tag-pill';
            pill.style.cssText = `display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:500;background:${tag.color || '#3b82f6'}18;color:${tag.color || '#3b82f6'};border:1px solid ${tag.color || '#3b82f6'}30;`;
            pill.innerHTML = `${escapeHtml(tag.name || tag.code)}
                <span style="cursor:pointer;margin-left:2px;font-size:14px;line-height:1;opacity:0.7;"
                      onclick="TWR.DictFix.removeEditTag(${idx})" title="Remove tag">&times;</span>`;
            container.appendChild(pill);
        });
    }

    function removeEditTag(idx) {
        DictState.editingTags.splice(idx, 1);
        renderModalTags();
    }

    function addFunctionTag() {
        const select = document.getElementById('edit-role-tag-select');
        if (!select || !select.value) {
            showToast('info', 'Select a function tag first');
            return;
        }
        const code = select.value;
        if (DictState.editingTags.some(t => t.code === code)) {
            showToast('info', 'Tag already assigned');
            select.value = '';
            return;
        }
        const cat = DictState.functionCategories.find(c => c.code === code);
        const selectedOption = select.options[select.selectedIndex];
        const color = selectedOption?.dataset?.color || cat?.color || '#3b82f6';
        DictState.editingTags.push({ code, name: cat?.name || code, color });
        renderModalTags();
        select.value = '';
    }

    function handleCategoryChange(value) {
        const customDiv = document.getElementById('edit-role-custom-category');
        if (value === '__custom__') {
            if (customDiv) {
                customDiv.style.display = 'block';
                const input = document.getElementById('edit-role-custom-category-input');
                if (input) { input.value = ''; input.focus(); }
            }
        } else {
            if (customDiv) customDiv.style.display = 'none';
        }
    }

    function applyCustomCategory() {
        const input = document.getElementById('edit-role-custom-category-input');
        const select = document.getElementById('edit-role-category');
        const customDiv = document.getElementById('edit-role-custom-category');
        if (!input || !select) return;
        const val = input.value.trim();
        if (!val) { showToast('error', 'Enter a category name'); return; }

        let optionExists = false;
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === val) { optionExists = true; break; }
        }
        if (!optionExists) {
            const opt = document.createElement('option');
            opt.value = val; opt.textContent = val;
            const customOpt = select.querySelector('option[value="__custom__"]');
            if (customOpt) select.insertBefore(opt, customOpt);
            else select.appendChild(opt);
            DictState.customCategories.add(val);
        }
        select.value = val;
        if (customDiv) customDiv.style.display = 'none';
    }

    function cancelCustomCategory() {
        const select = document.getElementById('edit-role-category');
        const customDiv = document.getElementById('edit-role-custom-category');
        if (customDiv) customDiv.style.display = 'none';
        if (select && select.value === '__custom__') select.value = 'Role';
    }

    async function editRole(roleId) {
        const role = DictState.roles.find(r => r.id === roleId);
        if (!role) { showToast('error', 'Role not found'); return; }

        const modal = document.getElementById('edit-role-modal');
        if (!modal) { showToast('error', 'Edit modal not available'); return; }

        await loadFunctionCategories();
        populateTagSelect();
        DictState.editingTags = await loadRoleTags(role.role_name);

        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) { el.type === 'checkbox' ? el.checked = !!val : el.value = val || ''; }
        };

        setVal('edit-role-id', roleId);
        setVal('edit-role-name', role.role_name);

        const catSelect = document.getElementById('edit-role-category');
        const category = role.category || 'Role';
        if (catSelect) {
            let found = false;
            for (let i = 0; i < catSelect.options.length; i++) {
                if (catSelect.options[i].value === category) { found = true; break; }
            }
            if (!found && category !== '__custom__') {
                const opt = document.createElement('option');
                opt.value = category; opt.textContent = category;
                const customOpt = catSelect.querySelector('option[value="__custom__"]');
                if (customOpt) catSelect.insertBefore(opt, customOpt);
                else catSelect.appendChild(opt);
            }
            catSelect.value = category;
        }

        const customDiv = document.getElementById('edit-role-custom-category');
        if (customDiv) customDiv.style.display = 'none';

        setVal('edit-role-aliases', (role.aliases || []).join(', '));
        setVal('edit-role-description', role.description);
        setVal('edit-role-deliverable', role.is_deliverable);
        setVal('edit-role-notes', role.notes);

        renderModalTags();

        const title = document.getElementById('edit-role-title');
        if (title) title.textContent = 'Edit Role';

        // Clear any previous duplicate warning
        const dupWarn = document.getElementById('dict-dup-warning');
        if (dupWarn) dupWarn.style.display = 'none';

        modal.style.display = 'flex';
        modal.offsetHeight;
        modal.classList.add('active');
        document.getElementById('edit-role-name')?.focus();
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [modal] }); } catch (_) { refreshIcons(); }
        }
    }

    // =================================================================
    // Role Detail Card — Rich inline-editable detail view
    // =================================================================
    let rdDirty = false;
    let rdCurrentId = null;

    async function viewRoleDetail(roleId) {
        const role = DictState.roles.find(r => r.id === roleId);
        if (!role) { showToast('error', 'Role not found'); return; }

        rdCurrentId = roleId;
        rdDirty = false;

        // Fetch function tags
        const tags = await loadRoleTags(role.role_name);
        // Fetch relationships from DictState if available
        const parents = role.parents || [];
        const children = role.children || [];

        const modal = document.getElementById('role-detail-modal');
        const body = document.getElementById('role-detail-body');
        if (!modal || !body) return;

        const esc = (s) => { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; };
        const adjStatus = role.is_active ? (role.is_deliverable ? 'deliverable' : 'confirmed') : 'rejected';
        const adjLabel = role.is_active ? (role.is_deliverable ? '★ Deliverable' : '✓ Adjudicated') : '✗ Inactive';
        const statusBadgeClass = role.is_active ? (role.is_deliverable ? 'rd-badge-deliverable' : 'rd-badge-active') : 'rd-badge-inactive';

        // Role type options
        const roleTypes = ['', 'Singular - Specific', 'Singular - Aggregate', 'Group - Specific', 'Group - Aggregate'];
        const roleTypeOpts = roleTypes.map(t => `<option value="${esc(t)}"${(role.role_type||'') === t ? ' selected' : ''}>${t || '—'}</option>`).join('');

        // Disposition options
        const dispositions = ['', 'Sanctioned', 'To Be Retired', 'TBD'];
        const dispOpts = dispositions.map(d => `<option value="${esc(d)}"${(role.role_disposition||'') === d ? ' selected' : ''}>${d || '—'}</option>`).join('');

        // Function tags HTML
        const tagsHtml = tags.map(t => {
            const code = typeof t === 'string' ? t : (t.code || t.function_code || '');
            const name = t.name || code;
            const color = t.color || '#6366f1';
            return `<span class="rd-tag" style="background:${color}15;color:${color};border:1px solid ${color}30;" data-code="${esc(code)}">
                ${esc(name)} <span class="rd-tag-x" data-code="${esc(code)}">&times;</span>
            </span>`;
        }).join('') || '<span id="rd-tags-empty" style="color:var(--text-muted);font-size:12px;">No tags assigned</span>';

        // Inheritance tree
        let inheritHtml = '<div class="rd-inherit" id="rd-inherit-container">';
        if (parents.length) {
            inheritHtml += '<div class="rd-inherit-label">Inherits From</div><div class="rd-inherit-group" id="rd-inherit-parents">';
            parents.forEach(p => { inheritHtml += `<span class="rd-inherit-node rd-inherit-removable" data-name="${esc(p)}" data-direction="parent" title="Click to remove">${esc(p)} <span class="rd-inherit-x">&times;</span></span>`; });
            inheritHtml += '</div><div class="rd-inherit-arrow">↓</div>';
        } else {
            inheritHtml += '<div class="rd-inherit-label">Inherits From</div><div class="rd-inherit-group" id="rd-inherit-parents"><span class="rd-inherit-empty">None</span></div><div class="rd-inherit-arrow">↓</div>';
        }
        inheritHtml += `<div class="rd-inherit-group"><span class="rd-inherit-node rd-self">${esc(role.role_name)}</span></div>`;
        if (children.length) {
            inheritHtml += '<div class="rd-inherit-arrow">↓</div><div class="rd-inherit-label">Inherited By</div><div class="rd-inherit-group" id="rd-inherit-children">';
            children.forEach(c => { inheritHtml += `<span class="rd-inherit-node rd-inherit-removable" data-name="${esc(c)}" data-direction="child" title="Click to remove">${esc(c)} <span class="rd-inherit-x">&times;</span></span>`; });
            inheritHtml += '</div>';
        } else {
            inheritHtml += '<div class="rd-inherit-arrow">↓</div><div class="rd-inherit-label">Inherited By</div><div class="rd-inherit-group" id="rd-inherit-children"><span class="rd-inherit-empty">None</span></div>';
        }
        inheritHtml += '</div>';
        // Smart search to add relationship
        inheritHtml += `<div class="rd-inherit-add-wrap">
            <div class="rd-inherit-search-row">
                <input type="text" class="rd-inherit-search" id="rd-inherit-search" placeholder="Search roles to link..." autocomplete="off">
                <select class="rd-inherit-direction" id="rd-inherit-direction">
                    <option value="parent">as Parent</option>
                    <option value="child">as Child</option>
                </select>
            </div>
            <div class="rd-inherit-results" id="rd-inherit-results"></div>
        </div>`;

        // Nimbus Model Locations (tracings from SIPOC import)
        let nimbusHtml = '';
        if (role.tracings && role.tracings.length > 0) {
            nimbusHtml = `<div class="rd-section-title" style="margin-top:24px;">Nimbus Model Locations (${role.tracings.length})</div>
                <ul class="rd-nimbus-list">
                    ${role.tracings.map(t => {
                        const title = esc(t.title || 'Nimbus Location');
                        const url = t.url || '#';
                        return `<li class="rd-nimbus-item">
                            <a href="${esc(url)}" target="_blank" rel="noopener" class="rd-nimbus-link" title="Open in Nimbus model">
                                <span class="rd-nimbus-icon">&#128279;</span>${title}
                            </a>
                        </li>`;
                    }).join('')}
                </ul>`;
        }

        // Dates
        const createdAt = role.created_at ? new Date(role.created_at).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'}) : '—';
        const updatedAt = role.updated_at ? new Date(role.updated_at).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'}) : '—';

        body.innerHTML = `
            <div class="rd-hero">
                <div class="rd-hero-top">
                    <div>
                        <h2 class="rd-hero-name">${esc(role.role_name)}</h2>
                        <div class="rd-hero-badges">
                            <span class="rd-hero-badge ${statusBadgeClass}">${adjLabel}</span>
                            ${role.source ? `<span class="rd-hero-badge rd-badge-adj">${esc(role.source)}</span>` : ''}
                            ${role.baselined ? '<span class="rd-hero-badge" style="background:rgba(16,185,129,0.35);">Baselined</span>' : ''}
                        </div>
                    </div>
                    <button class="rd-hero-close" id="rd-close-top" title="Close"><i data-lucide="x" style="width:18px;height:18px;"></i></button>
                </div>
            </div>

            <div class="rd-stats-row">
                <div class="rd-stat">
                    <div class="rd-stat-value">${esc(role.category || 'Role')}</div>
                    <div class="rd-stat-label">Category</div>
                </div>
                <div class="rd-stat">
                    <div class="rd-stat-value">${esc(role.source || 'manual')}</div>
                    <div class="rd-stat-label">Source</div>
                </div>
                <div class="rd-stat">
                    <div class="rd-stat-value" style="color:${role.is_active ? 'var(--success,#22c55e)' : 'var(--error,#ef4444)'}">${role.is_active ? 'Active' : 'Inactive'}</div>
                    <div class="rd-stat-label">Status</div>
                </div>
                <div class="rd-stat">
                    <div class="rd-stat-value" style="color:${role.is_deliverable ? 'var(--info,#3b82f6)' : 'var(--text-muted,#94a3b8)'};">${role.is_deliverable ? '★ Yes' : '☆ No'}</div>
                    <div class="rd-stat-label">Deliverable</div>
                </div>
            </div>

            <div class="rd-body">
                <div class="rd-col">
                    <div class="rd-section-title">Details</div>
                    <div class="rd-field">
                        <div class="rd-field-label">Description</div>
                        <textarea class="rd-editable rd-track" id="rd-description" rows="3" placeholder="Add a description...">${esc(role.description || '')}</textarea>
                    </div>
                    <div class="rd-field">
                        <div class="rd-field-label">Aliases</div>
                        <input class="rd-editable rd-track" id="rd-aliases" type="text" value="${esc((role.aliases||[]).join(', '))}" placeholder="None">
                    </div>
                    <div class="rd-field">
                        <div class="rd-field-label">Role Type</div>
                        <select class="rd-editable rd-track" id="rd-role-type">${roleTypeOpts}</select>
                    </div>
                    <div class="rd-field">
                        <div class="rd-field-label">Disposition</div>
                        <select class="rd-editable rd-track" id="rd-disposition">${dispOpts}</select>
                    </div>
                    <div class="rd-field">
                        <div class="rd-field-label">Org Group</div>
                        <div class="rd-field-value">${esc(role.org_group || '—')}</div>
                    </div>
                    <div class="rd-field">
                        <div class="rd-field-label">Notes</div>
                        <textarea class="rd-editable rd-track" id="rd-notes" rows="2" placeholder="Add notes...">${esc(role.notes || '')}</textarea>
                    </div>
                </div>
                <div class="rd-col">
                    <div class="rd-section-title">Function Tags</div>
                    <div class="rd-tags-wrap" id="rd-tags-container">${tagsHtml}</div>
                    <div class="rd-tag-add-wrap">
                        <span class="rd-tag-add" id="rd-add-tag">+ Add Tag</span>
                        <div class="rd-tag-dropdown" id="rd-tag-dropdown">
                            <div class="rd-tag-dd-search-wrap">
                                <input type="text" class="rd-tag-dd-search" id="rd-tag-dd-search" placeholder="Search tags..." autocomplete="off">
                            </div>
                            <div class="rd-tag-dd-list" id="rd-tag-dd-list"></div>
                        </div>
                    </div>

                    <div class="rd-section-title" style="margin-top:24px;">Inheritance</div>
                    ${inheritHtml}

                    ${nimbusHtml}
                </div>
            </div>

            <div class="rd-timeline">
                <span>Created ${createdAt}${role.created_by ? ' by ' + esc(role.created_by) : ''}</span>
                <span>Updated ${updatedAt}${role.updated_by ? ' by ' + esc(role.updated_by) : ''}</span>
            </div>

            <div class="rd-footer">
                <button class="btn btn-primary btn-sm rd-save-btn" id="rd-save-btn" disabled>
                    <i data-lucide="save"></i> Save Changes
                </button>
                <button class="btn btn-secondary btn-sm" id="rd-close-btn">Close</button>
            </div>
        `;

        // Open modal
        modal.style.display = 'flex';
        modal.offsetHeight;
        modal.classList.add('active');
        refreshIcons();

        // Close helper
        let _escHandler = null;
        const closeModal = () => {
            if (rdDirty && !confirm('You have unsaved changes. Close anyway?')) return;
            modal.style.display = 'none';
            modal.classList.remove('active');
            rdDirty = false;
            rdCurrentId = null;
            if (_escHandler) document.removeEventListener('keydown', _escHandler, true);
        };

        // --- Event delegation on the modal (single handler, robust click targets) ---
        // Remove previous handler if exists, then add fresh
        if (modal._rdHandler) modal.removeEventListener('click', modal._rdHandler);
        modal._rdHandler = async function(e) {
            const target = e.target;

            // Close tag dropdown if clicking outside it
            if (!target.closest('.rd-tag-add-wrap')) {
                document.getElementById('rd-tag-dropdown')?.classList.remove('rd-dd-open');
            }

            // Close button (× in hero or Close in footer)
            if (target.closest('.rd-hero-close') || target.closest('#rd-close-btn')) {
                e.stopPropagation();
                closeModal();
                return;
            }

            // Click on modal background (outside modal-content) → close
            if (target === modal || target.classList.contains('modal-overlay')) {
                closeModal();
                return;
            }

            // Save button
            if (target.closest('#rd-save-btn')) {
                e.stopPropagation();
                saveRoleDetail(roleId);
                return;
            }

            // Remove tag (× on tag pill)
            const tagX = target.closest('.rd-tag-x');
            if (tagX) {
                e.stopPropagation();
                const code = tagX.dataset.code;
                const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                try {
                    await fetch(`/api/role-function-tags/${encodeURIComponent(role.role_name)}/${encodeURIComponent(code)}`, {
                        method: 'DELETE', headers: { 'X-CSRF-Token': csrf }
                    });
                    tagX.closest('.rd-tag')?.remove();
                    showToast('success', `Tag "${code}" removed`);
                } catch(err) { showToast('error', 'Failed to remove tag'); }
                return;
            }

            // Add tag button — toggle dropdown
            if (target.closest('.rd-tag-add') || target.closest('#rd-add-tag')) {
                e.stopPropagation();
                const dropdown = document.getElementById('rd-tag-dropdown');
                if (!dropdown) return;
                const isOpen = dropdown.classList.contains('rd-dd-open');
                if (isOpen) {
                    dropdown.classList.remove('rd-dd-open');
                    return;
                }
                await loadFunctionCategories();
                const cats = DictState.functionCategories || [];
                if (!cats.length) { showToast('info', 'No function categories available'); return; }
                _rdPopulateTagDropdown(cats, role);
                dropdown.classList.add('rd-dd-open');
                setTimeout(() => document.getElementById('rd-tag-dd-search')?.focus(), 50);
                return;
            }

            // Tag dropdown item click — add the selected tag
            const ddItem = target.closest('.rd-tag-dd-item');
            if (ddItem && !ddItem.classList.contains('rd-tag-dd-group')) {
                e.stopPropagation();
                const code = ddItem.dataset.code;
                if (!code) return;
                // Check if already assigned
                const existing = document.querySelector(`#rd-tags-container .rd-tag[data-code="${code}"]`);
                if (existing) { showToast('info', 'Tag already assigned'); return; }
                const cats = DictState.functionCategories || [];
                const cat = cats.find(c => c.code === code);
                const color = cat?.color || '#6366f1';
                const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                try {
                    const resp = await fetch('/api/role-function-tags', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
                        body: JSON.stringify({ role_name: role.role_name, function_code: code })
                    });
                    if (resp.ok) {
                        const container = document.getElementById('rd-tags-container');
                        // Hide "No tags assigned" placeholder
                        const emptyMsg = document.getElementById('rd-tags-empty');
                        if (emptyMsg) emptyMsg.remove();
                        const pill = document.createElement('span');
                        pill.className = 'rd-tag';
                        pill.style.cssText = `background:${color}15;color:${color};border:1px solid ${color}30;`;
                        pill.dataset.code = code;
                        pill.innerHTML = `${esc(cat?.name || code)} <span class="rd-tag-x" data-code="${esc(code)}">&times;</span>`;
                        container.appendChild(pill);
                        showToast('success', `Tag "${cat?.name || code}" added`);
                        // Close dropdown
                        document.getElementById('rd-tag-dropdown')?.classList.remove('rd-dd-open');
                    } else { showToast('error', 'Failed to add tag'); }
                } catch(err) { showToast('error', 'Failed to add tag'); }
                return;
            }

            // Inheritance search result click — add relationship
            const inheritResult = target.closest('.rd-inherit-result-item');
            if (inheritResult) {
                e.stopPropagation();
                const targetName = inheritResult.dataset.name;
                if (!targetName) return;
                const direction = document.getElementById('rd-inherit-direction')?.value || 'parent';
                const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                // Direction: if "parent", the selected role is a parent (role inherits FROM it)
                // source=current role, target=selected role (inherits-from)
                const sourceRole = direction === 'parent' ? role.role_name : targetName;
                const targetRole = direction === 'parent' ? targetName : role.role_name;
                try {
                    const resp = await fetch('/api/roles/relationships', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
                        body: JSON.stringify({ source_role: sourceRole, target_role: targetRole, type: 'inherits-from' })
                    });
                    if (resp.ok) {
                        // Add node to the correct group
                        const groupId = direction === 'parent' ? 'rd-inherit-parents' : 'rd-inherit-children';
                        const group = document.getElementById(groupId);
                        if (group) {
                            // Remove "None" placeholder
                            const empty = group.querySelector('.rd-inherit-empty');
                            if (empty) empty.remove();
                            const node = document.createElement('span');
                            node.className = 'rd-inherit-node rd-inherit-removable';
                            node.dataset.name = targetName;
                            node.dataset.direction = direction;
                            node.title = 'Click to remove';
                            node.innerHTML = `${esc(targetName)} <span class="rd-inherit-x">&times;</span>`;
                            group.appendChild(node);
                        }
                        showToast('success', `Added ${direction}: ${targetName}`);
                        // Clear search
                        const searchInput = document.getElementById('rd-inherit-search');
                        if (searchInput) searchInput.value = '';
                        const resultsDiv = document.getElementById('rd-inherit-results');
                        if (resultsDiv) { resultsDiv.innerHTML = ''; resultsDiv.style.display = 'none'; }
                    } else { showToast('error', 'Failed to add relationship'); }
                } catch(err) { showToast('error', 'Failed to add relationship'); }
                return;
            }

            // Remove inheritance relationship (click × on node)
            const inheritX = target.closest('.rd-inherit-x');
            if (inheritX) {
                e.stopPropagation();
                const node = inheritX.closest('.rd-inherit-removable');
                if (!node) return;
                const linkedName = node.dataset.name;
                const direction = node.dataset.direction;
                if (!linkedName) return;
                const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                const sourceRole = direction === 'parent' ? role.role_name : linkedName;
                const targetRole = direction === 'parent' ? linkedName : role.role_name;
                try {
                    const resp = await fetch('/api/roles/relationships/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
                        body: JSON.stringify({ source_role: sourceRole, target_role: targetRole, type: 'inherits-from' })
                    });
                    if (resp.ok) {
                        node.remove();
                        // Check if group is now empty, add placeholder
                        const groupId = direction === 'parent' ? 'rd-inherit-parents' : 'rd-inherit-children';
                        const group = document.getElementById(groupId);
                        if (group && !group.querySelector('.rd-inherit-node')) {
                            group.innerHTML = '<span class="rd-inherit-empty">None</span>';
                        }
                        showToast('success', `Removed ${direction}: ${linkedName}`);
                    } else { showToast('error', 'Failed to remove relationship'); }
                } catch(err) { showToast('error', 'Failed to remove relationship'); }
                return;
            }
        };
        modal.addEventListener('click', modal._rdHandler);

        // Tag dropdown search filter
        document.getElementById('rd-tag-dd-search')?.addEventListener('input', (evt) => {
            const query = evt.target.value.toLowerCase().trim();
            const items = document.querySelectorAll('#rd-tag-dd-list .rd-tag-dd-item');
            items.forEach(item => {
                if (item.classList.contains('rd-tag-dd-group')) {
                    // Group headers: show if any child matches
                    let nextEl = item.nextElementSibling;
                    let anyVisible = false;
                    while (nextEl && !nextEl.classList.contains('rd-tag-dd-group')) {
                        const text = (nextEl.dataset.name || '').toLowerCase() + ' ' + (nextEl.dataset.code || '').toLowerCase();
                        const match = !query || text.includes(query);
                        nextEl.style.display = match ? '' : 'none';
                        if (match) anyVisible = true;
                        nextEl = nextEl.nextElementSibling;
                    }
                    item.style.display = anyVisible ? '' : 'none';
                } else if (!query) {
                    item.style.display = '';
                }
            });
        });

        // Inheritance smart search
        let _inheritDebounce = null;
        document.getElementById('rd-inherit-search')?.addEventListener('input', (evt) => {
            clearTimeout(_inheritDebounce);
            const query = evt.target.value.toLowerCase().trim();
            const resultsDiv = document.getElementById('rd-inherit-results');
            if (!resultsDiv) return;
            if (query.length < 2) { resultsDiv.innerHTML = ''; resultsDiv.style.display = 'none'; return; }
            _inheritDebounce = setTimeout(() => {
                const matches = DictState.roles
                    .filter(r => r.role_name.toLowerCase().includes(query) && r.role_name !== role.role_name)
                    .slice(0, 8);
                if (!matches.length) {
                    resultsDiv.innerHTML = '<div class="rd-inherit-result-empty">No matching roles</div>';
                } else {
                    resultsDiv.innerHTML = matches.map(m =>
                        `<div class="rd-inherit-result-item" data-name="${escapeHtml(m.role_name)}" data-id="${m.id}">
                            <span class="rd-inherit-result-name">${escapeHtml(m.role_name)}</span>
                            <span class="rd-inherit-result-cat">${escapeHtml(m.category || 'Role')}</span>
                        </div>`
                    ).join('');
                }
                resultsDiv.style.display = 'block';
            }, 150);
        });

        // Track dirty state on editable fields
        body.querySelectorAll('.rd-track').forEach(el => {
            el.addEventListener('input', () => {
                rdDirty = true;
                const saveBtn = document.getElementById('rd-save-btn');
                if (saveBtn) { saveBtn.disabled = false; saveBtn.classList.add('rd-dirty'); }
            });
        });

        // Escape key to close (capture phase + stopPropagation so parent studio doesn't also close)
        _escHandler = (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation();
                e.preventDefault();
                closeModal();
            }
        };
        document.addEventListener('keydown', _escHandler, true);
    }

    // Populate the tag dropdown with hierarchical categories
    function _rdPopulateTagDropdown(cats, role) {
        const list = document.getElementById('rd-tag-dd-list');
        if (!list) return;

        // Build parent-child map
        const childMap = {};
        cats.forEach(c => {
            if (c.parent_code) {
                if (!childMap[c.parent_code]) childMap[c.parent_code] = [];
                childMap[c.parent_code].push(c);
            }
        });

        // Get already-assigned tags
        const assigned = new Set();
        document.querySelectorAll('#rd-tags-container .rd-tag').forEach(t => {
            if (t.dataset.code) assigned.add(t.dataset.code);
        });

        const topLevel = cats.filter(c => !c.parent_code);
        let html = '';

        topLevel.forEach(parent => {
            const children = childMap[parent.code] || [];
            // Group header
            html += `<div class="rd-tag-dd-item rd-tag-dd-group" data-name="${escapeHtml(parent.name)}" data-code="${escapeHtml(parent.code)}">
                <span class="rd-tag-dd-dot" style="background:${escapeHtml(parent.color || '#6366f1')}"></span>
                ${escapeHtml(parent.name)}
            </div>`;
            // Parent as selectable item
            const pAssigned = assigned.has(parent.code);
            html += `<div class="rd-tag-dd-item rd-tag-dd-leaf${pAssigned ? ' rd-tag-dd-disabled' : ''}" data-code="${escapeHtml(parent.code)}" data-name="${escapeHtml(parent.name)}" data-color="${escapeHtml(parent.color || '#6366f1')}">
                <span class="rd-tag-dd-dot" style="background:${escapeHtml(parent.color || '#6366f1')}"></span>
                <span class="rd-tag-dd-name">${escapeHtml(parent.code)}</span>
                <span class="rd-tag-dd-desc">${escapeHtml(parent.name)}</span>
                ${pAssigned ? '<span class="rd-tag-dd-check">✓</span>' : ''}
            </div>`;

            children.forEach(child => {
                const cAssigned = assigned.has(child.code);
                html += `<div class="rd-tag-dd-item rd-tag-dd-leaf rd-tag-dd-child${cAssigned ? ' rd-tag-dd-disabled' : ''}" data-code="${escapeHtml(child.code)}" data-name="${escapeHtml(child.name)}" data-color="${escapeHtml(child.color || parent.color || '#6366f1')}">
                    <span class="rd-tag-dd-dot" style="background:${escapeHtml(child.color || parent.color || '#6366f1')}"></span>
                    <span class="rd-tag-dd-name">${escapeHtml(child.code)}</span>
                    <span class="rd-tag-dd-desc">${escapeHtml(child.name)}</span>
                    ${cAssigned ? '<span class="rd-tag-dd-check">✓</span>' : ''}
                </div>`;

                // Grandchildren
                (childMap[child.code] || []).forEach(gc => {
                    const gAssigned = assigned.has(gc.code);
                    html += `<div class="rd-tag-dd-item rd-tag-dd-leaf rd-tag-dd-grandchild${gAssigned ? ' rd-tag-dd-disabled' : ''}" data-code="${escapeHtml(gc.code)}" data-name="${escapeHtml(gc.name)}" data-color="${escapeHtml(gc.color || child.color || '#6366f1')}">
                        <span class="rd-tag-dd-dot" style="background:${escapeHtml(gc.color || child.color || '#6366f1')}"></span>
                        <span class="rd-tag-dd-name">${escapeHtml(gc.code)}</span>
                        <span class="rd-tag-dd-desc">${escapeHtml(gc.name)}</span>
                        ${gAssigned ? '<span class="rd-tag-dd-check">✓</span>' : ''}
                    </div>`;
                });
            });
        });

        list.innerHTML = html;
        // Clear search
        const search = document.getElementById('rd-tag-dd-search');
        if (search) search.value = '';
    }

    async function saveRoleDetail(roleId) {
        const desc = document.getElementById('rd-description')?.value || '';
        const aliasStr = document.getElementById('rd-aliases')?.value || '';
        const roleType = document.getElementById('rd-role-type')?.value || '';
        const disp = document.getElementById('rd-disposition')?.value || '';
        const notes = document.getElementById('rd-notes')?.value || '';
        const aliases = aliasStr.split(',').map(a => a.trim()).filter(Boolean);

        const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
        try {
            const resp = await fetch(`/api/roles/dictionary/${roleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
                body: JSON.stringify({
                    description: desc,
                    aliases: aliases,
                    role_type: roleType,
                    role_disposition: disp,
                    notes: notes,
                })
            });
            const data = await resp.json();
            if (data.success) {
                showToast('success', 'Role updated');
                rdDirty = false;
                const saveBtn = document.getElementById('rd-save-btn');
                if (saveBtn) { saveBtn.disabled = true; saveBtn.classList.remove('rd-dirty'); }
                // Update local state
                const role = DictState.roles.find(r => r.id === roleId);
                if (role) {
                    role.description = desc;
                    role.aliases = aliases;
                    role.role_type = roleType;
                    role.role_disposition = disp;
                    role.notes = notes;
                }
                renderDictionary();
            } else {
                showToast('error', data.error || 'Save failed');
            }
        } catch(err) {
            showToast('error', 'Save failed: ' + err.message);
        }
    }

    async function saveRole() {
        const roleId = document.getElementById('edit-role-id')?.value;
        const roleName = document.getElementById('edit-role-name')?.value?.trim();

        if (!roleName) { showToast('error', 'Role name is required'); return; }

        // Duplicate detection
        const dupes = findDuplicates(roleName, roleId);
        if (dupes.length > 0) {
            const dupeNames = dupes.map(d => d.role_name).join(', ');
            if (!confirm(`Similar role(s) already exist: ${dupeNames}\n\nContinue saving anyway?`)) {
                return;
            }
        }

        const aliasesStr = document.getElementById('edit-role-aliases')?.value || '';
        const aliases = aliasesStr ? aliasesStr.split(',').map(a => a.trim()).filter(Boolean) : [];
        let category = document.getElementById('edit-role-category')?.value || 'Role';
        if (category === '__custom__') category = 'Role';

        const data = {
            role_name: roleName,
            category: category,
            aliases: aliases,
            description: document.getElementById('edit-role-description')?.value?.trim() || '',
            is_deliverable: document.getElementById('edit-role-deliverable')?.checked || false,
            notes: document.getElementById('edit-role-notes')?.value?.trim() || ''
        };

        try {
            const csrfToken = getCSRFToken();
            let response;

            if (roleId) {
                response = await fetch(`/api/roles/dictionary/${roleId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify(data)
                });
            } else {
                response = await fetch('/api/roles/dictionary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify(data)
                });
            }

            const result = await response.json();

            if (result.success) {
                await saveFunctionTags(roleName);
                closeRoleModal();
                DictState.loaded = false;
                if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
                await loadDictionary(true);
                showToast('success', roleId ? 'Role updated' : 'Role created');
            } else {
                showToast('error', 'Failed to save: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            showToast('error', 'Error saving role: ' + error.message);
        }
    }

    async function saveFunctionTags(roleName) {
        const csrfToken = getCSRFToken();
        const currentTags = await loadRoleTags(roleName);
        const currentCodes = new Set(currentTags.map(t => t.code));
        const editingCodes = new Set(DictState.editingTags.map(t => t.code));

        const toAdd = DictState.editingTags.filter(t => !currentCodes.has(t.code));
        const toRemove = currentTags.filter(t => !editingCodes.has(t.code));

        for (const tag of toAdd) {
            try {
                await fetch('/api/role-function-tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ role_name: roleName, function_code: tag.code })
                });
            } catch (e) { console.warn('[TWR DictV5] Failed to add tag', tag.code, e); }
        }

        for (const tag of toRemove) {
            if (tag.id) {
                try {
                    await fetch(`/api/role-function-tags/${tag.id}`, {
                        method: 'DELETE', headers: { 'X-CSRF-Token': csrfToken }
                    });
                } catch (e) { console.warn('[TWR DictV5] Failed to remove tag', tag.code, e); }
            }
        }
    }

    async function toggleRole(roleId) {
        const role = DictState.roles.find(r => r.id === roleId);
        if (!role) return;

        try {
            const csrfToken = getCSRFToken();
            const response = await fetch(`/api/roles/dictionary/${roleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ is_active: !role.is_active })
            });
            const result = await response.json();
            if (result.success) {
                role.is_active = !role.is_active;
                applyFilters();
                renderCurrentView();
                renderDashboard();
                showToast('success', `Role ${role.is_active ? 'activated' : 'deactivated'}`);
                if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
            } else {
                showToast('error', 'Failed: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            showToast('error', 'Error: ' + error.message);
        }
    }

    async function deleteRole(roleId) {
        if (!confirm('Are you sure you want to delete this role? This cannot be undone.')) return;

        try {
            const csrfToken = getCSRFToken();
            const response = await fetch(`/api/roles/dictionary/${roleId}?hard=true`, {
                method: 'DELETE', headers: { 'X-CSRF-Token': csrfToken }
            });
            const result = await response.json();
            if (result.success) {
                DictState.roles = DictState.roles.filter(r => r.id !== roleId);
                DictState.selectedRoles.delete(roleId);
                applyFilters();
                renderCurrentView();
                renderDashboard();
                showToast('success', 'Role deleted');
                if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
            } else {
                showToast('error', 'Failed: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            showToast('error', 'Error: ' + error.message);
        }
    }

    function closeRoleModal() {
        const modal = document.getElementById('edit-role-modal');
        if (modal) { modal.classList.remove('active'); modal.style.display = 'none'; }
        DictState.editingTags = [];
        const customDiv = document.getElementById('edit-role-custom-category');
        if (customDiv) customDiv.style.display = 'none';
    }

    function showDictError(message) {
        const container = document.getElementById('dict-content-area');
        if (container) {
            container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-error);">
                <i data-lucide="alert-circle"></i> ${message}
            </div>`;
        }
        refreshIcons();
    }

    // =====================================================================
    // KEYBOARD NAVIGATION
    // =====================================================================
    function initKeyboard() {
        const dictSection = document.getElementById('roles-dictionary');
        if (!dictSection) return;

        document.addEventListener('keydown', (e) => {
            // Only act when dictionary tab is visible
            if (dictSection.style.display === 'none') return;

            // Don't intercept when typing in inputs
            const active = document.activeElement;
            if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT')) {
                if (e.key === 'Escape') { active.blur(); return; }
                return;
            }

            // Don't intercept when a modal is open
            const editModal = document.getElementById('edit-role-modal');
            if (editModal && editModal.style.display !== 'none') return;

            const maxIdx = DictState.filteredRoles.length - 1;

            switch (e.key) {
                case 'ArrowDown':
                case 'j':
                    e.preventDefault();
                    DictState.focusIndex = Math.min(DictState.focusIndex + 1, maxIdx);
                    updateFocusHighlight();
                    scrollToFocused();
                    break;
                case 'ArrowUp':
                case 'k':
                    e.preventDefault();
                    DictState.focusIndex = Math.max(DictState.focusIndex - 1, 0);
                    updateFocusHighlight();
                    scrollToFocused();
                    break;
                case 'Enter':
                case 'e':
                    if (DictState.focusIndex >= 0 && DictState.focusIndex <= maxIdx) {
                        e.preventDefault();
                        editRole(DictState.filteredRoles[DictState.focusIndex].id);
                    }
                    break;
                case ' ':
                    if (DictState.focusIndex >= 0 && DictState.focusIndex <= maxIdx) {
                        e.preventDefault();
                        const role = DictState.filteredRoles[DictState.focusIndex];
                        const isSelected = DictState.selectedRoles.has(role.id);
                        toggleSelect(role.id, !isSelected);
                        renderCurrentView();
                    }
                    break;
                case 'Delete':
                case 'Backspace':
                    if (DictState.focusIndex >= 0 && DictState.focusIndex <= maxIdx) {
                        e.preventDefault();
                        deleteRole(DictState.filteredRoles[DictState.focusIndex].id);
                    }
                    break;
                case '/':
                    e.preventDefault();
                    document.getElementById('dict-search')?.focus();
                    break;
                case 'Escape':
                    DictState.focusIndex = -1;
                    DictState.selectedRoles.clear();
                    renderCurrentView();
                    break;
                case 't':
                    e.preventDefault();
                    setViewMode(DictState.viewMode === 'table' ? 'card' : 'table');
                    break;
            }
        });
    }

    function updateFocusHighlight() {
        // Remove all focused
        document.querySelectorAll('.dict-row-focused, .dict-card-focused').forEach(el => {
            el.classList.remove('dict-row-focused', 'dict-card-focused');
        });

        const focusEl = document.querySelector(`[data-idx="${DictState.focusIndex}"]`);
        if (focusEl) {
            focusEl.classList.add(DictState.viewMode === 'card' ? 'dict-card-focused' : 'dict-row-focused');
        }
    }

    let _dictLastNavTime = 0;
    function scrollToFocused() {
        const focusEl = document.querySelector('.dict-row-focused, .dict-card-focused');
        if (focusEl) {
            // Use instant scroll when navigating rapidly (< 200ms between keypresses)
            const now = Date.now();
            const isRapid = (now - _dictLastNavTime) < 200;
            _dictLastNavTime = now;
            focusEl.scrollIntoView({ block: 'nearest', behavior: isRapid ? 'auto' : 'smooth' });
        }
    }

    // =====================================================================
    // SIPOC IMPORT WIZARD (v4.1.0)
    // =====================================================================
    let sipocPreviewData = null;
    let sipocCurrentStep = 1;

    function showSipocImportModal() {
        const modal = document.getElementById('sipoc-import-modal');
        if (!modal) return;
        // Move to body to escape Roles Studio stacking context (transform)
        if (modal.parentElement !== document.body) {
            document.body.appendChild(modal);
        }
        modal.style.display = 'flex';
        modal.classList.add('active');
        sipocCurrentStep = 1;
        sipocPreviewData = null;
        // Reset file input and dropzone to initial state
        const fi = document.getElementById('sipoc-file-input');
        if (fi) fi.value = '';
        const dz = document.getElementById('sipoc-dropzone');
        if (dz) {
            // Use <label for="..."> to natively trigger the file input — no JS .click() needed
            dz.innerHTML = '<i data-lucide="git-branch" style="width:48px;height:48px;color:#D6A84A;"></i>' +
                '<p><strong>Upload Nimbus SIPOC Export</strong></p>' +
                '<p class="text-muted">Drag and drop your SIPOC export file here, or click to browse</p>' +
                '<input type="file" id="sipoc-file-input" accept=".xlsx,.xls" style="display:none;">' +
                '<label for="sipoc-file-input" class="btn btn-secondary btn-sm" style="margin-top:12px;cursor:pointer;">' +
                '<i data-lucide="folder-open"></i> Browse Files</label>';
            // Re-bind change event on recreated file input
            const newFi = document.getElementById('sipoc-file-input');
            if (newFi) {
                newFi.addEventListener('change', () => {
                    const nextBtn = document.getElementById('sipoc-wizard-next');
                    const hasFile = newFi.files?.length > 0;
                    if (nextBtn) nextBtn.disabled = !hasFile;
                    if (dz && hasFile) {
                        const file = newFi.files[0];
                        const sizeKB = (file.size / 1024).toFixed(0);
                        dz.innerHTML = '<i data-lucide="file-check" style="width:48px;height:48px;color:#10b981;"></i>' +
                            '<p style="margin-top:8px;"><strong>' + file.name + '</strong></p>' +
                            '<p class="text-muted" style="font-size:12px;">' + sizeKB + ' KB</p>' +
                            '<label for="sipoc-file-input" class="btn btn-secondary btn-sm" style="margin-top:8px;cursor:pointer;">' +
                            '<i data-lucide="folder-open"></i> Change File</label>';
                        // Re-append the file input so it stays in the DOM with its file reference
                        dz.appendChild(newFi);
                        if (typeof lucide !== 'undefined') lucide.createIcons();
                    }
                });
            }
        }
        showSipocStep(1);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function closeSipocModal() {
        const modal = document.getElementById('sipoc-import-modal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
        }
    }

    function showSipocStep(step) {
        sipocCurrentStep = step;
        for (let i = 1; i <= 5; i++) {
            const el = document.getElementById(`sipoc-step-${i}`);
            if (el) el.style.display = i === step ? '' : 'none';
        }
        // Update step indicators
        document.querySelectorAll('#sipoc-import-modal .progress-step').forEach(s => {
            const sn = parseInt(s.dataset.step);
            s.classList.toggle('active', sn <= step);
        });
        // Update title
        const titles = ['Upload', 'Preview', 'Options', 'Importing...', 'Complete'];
        const titleEl = document.getElementById('sipoc-wizard-title');
        if (titleEl) titleEl.innerHTML = `<i data-lucide="git-branch"></i> Nimbus SIPOC Import - ${titles[step - 1]}`;
        // Button states
        const nextBtn = document.getElementById('sipoc-wizard-next');
        const backBtn = document.getElementById('sipoc-wizard-back');
        const cancelBtn = document.getElementById('sipoc-wizard-cancel');
        if (nextBtn) {
            nextBtn.style.display = step >= 4 ? 'none' : '';
            nextBtn.disabled = step === 1 && !document.getElementById('sipoc-file-input')?.files?.length;
            nextBtn.innerHTML = step === 3 ? '<i data-lucide="download"></i> Import Now' : 'Next <i data-lucide="arrow-right"></i>';
        }
        if (backBtn) backBtn.style.display = step > 1 && step < 4 ? '' : 'none';
        // On step 5 (Done), change Cancel to a prominent Done button
        if (cancelBtn) {
            if (step === 5) {
                cancelBtn.className = 'btn btn-primary';
                cancelBtn.innerHTML = '<i data-lucide="check-circle"></i> Done';
            } else {
                cancelBtn.className = 'btn btn-secondary';
                cancelBtn.textContent = 'Cancel';
            }
        }
        // v5.9.22: Make step 5 "Done" label in the step indicator also clickable
        const stepLabels = document.querySelectorAll('.sipoc-steps-indicator .progress-step');
        stepLabels.forEach(label => {
            const labelStep = parseInt(label.dataset.step);
            if (labelStep === 5 && step === 5) {
                label.style.cursor = 'pointer';
                label.style.textDecoration = 'underline';
                label.onclick = () => {
                    const modal = document.getElementById('sipoc-import-modal');
                    if (modal) {
                        modal.classList.remove('active');
                        modal.style.display = 'none';
                    }
                };
            } else {
                label.style.cursor = '';
                label.style.textDecoration = '';
                label.onclick = null;
            }
        });
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function sipocUploadAndPreview() {
        const fileInput = document.getElementById('sipoc-file-input');
        if (!fileInput?.files?.length) return;

        showSipocStep(2);
        // Reset loading div content (may contain old error HTML from a previous attempt)
        const loadingDiv = document.getElementById('sipoc-loading');
        if (loadingDiv) {
            loadingDiv.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner-border"></div><p style="margin-top:16px;">Parsing SIPOC file...</p></div>';
            loadingDiv.style.display = '';
        }
        document.getElementById('sipoc-preview-content').style.display = 'none';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
            console.log('[TWR SIPOC] Starting preview upload...');
            const resp = await fetch('/api/roles/dictionary/import-sipoc', {
                method: 'POST',
                headers: { 'X-CSRF-Token': csrf },
                body: formData
            });
            console.log('[TWR SIPOC] Response status:', resp.status);
            const data = await resp.json();
            console.log('[TWR SIPOC] Response data.success:', data.success, 'error type:', typeof data.error, 'error:', data.error);
            if (!data.success) {
                const errMsg = typeof data.error === 'string' ? data.error : (data.error?.message || JSON.stringify(data.error) || 'Preview failed');
                throw new Error(errMsg);
            }

            sipocPreviewData = data.data;
            renderSipocPreview(data.data);
            document.getElementById('sipoc-loading').style.display = 'none';
            document.getElementById('sipoc-preview-content').style.display = '';
            const nextBtn = document.getElementById('sipoc-wizard-next');
            if (nextBtn) nextBtn.disabled = false;
            console.log('[TWR SIPOC] Preview rendered successfully');
        } catch (err) {
            // Bulletproof error message extraction — never show [object Object]
            let errMsg = 'Preview failed';
            if (err && typeof err.message === 'string' && err.message !== '[object Object]') {
                errMsg = err.message;
            } else if (err && typeof err === 'string') {
                errMsg = err;
            } else if (err) {
                try { errMsg = JSON.stringify(err); } catch (_) { errMsg = String(err); }
            }
            console.error('[TWR SIPOC] Preview error:', err, '| Display message:', errMsg);
            document.getElementById('sipoc-loading').innerHTML = `
                <div style="color:#e53e3e;text-align:center;">
                    <i data-lucide="alert-circle" style="width:40px;height:40px;"></i>
                    <p style="margin-top:12px;">${errMsg}</p>
                    <button class="btn btn-secondary btn-sm" onclick="document.getElementById('sipoc-step-2').style.display='none';document.getElementById('sipoc-step-1').style.display='';document.getElementById('sipoc-wizard-next').disabled=false;" style="margin-top:12px;">Try Again</button>
                </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    function renderSipocPreview(data) {
        const stats = data.stats || {};
        const statsGrid = document.getElementById('sipoc-stats-grid');
        if (statsGrid) {
            statsGrid.innerHTML = `
                <div class="sipoc-stat-card"><div class="sipoc-stat-value">${stats.unique_roles || 0}</div><div class="sipoc-stat-label">Roles</div></div>
                <div class="sipoc-stat-card"><div class="sipoc-stat-value">${stats.unique_tools || 0}</div><div class="sipoc-stat-label">Tools</div></div>
                <div class="sipoc-stat-card"><div class="sipoc-stat-value">${stats.total_relationships || 0}</div><div class="sipoc-stat-label">Relationships</div></div>
                <div class="sipoc-stat-card"><div class="sipoc-stat-value">${stats.roles_with_tags || 0}</div><div class="sipoc-stat-label">Tagged Roles</div></div>
            `;
        }

        // Show fallback notice if Roles Hierarchy map path was not found
        const noticeDiv = document.getElementById('sipoc-fallback-notice');
        if (noticeDiv) {
            if (stats.map_path_found === false) {
                noticeDiv.innerHTML = `
                    <div style="padding:10px 16px;background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;color:#92400e;font-size:13px;margin:8px 0;display:flex;align-items:center;gap:8px;">
                        <i data-lucide="alert-triangle" style="width:16px;height:16px;flex-shrink:0;color:#f59e0b;"></i>
                        <span><strong>Note:</strong> "Roles Hierarchy" map path not found. Processing all ${stats.hierarchy_rows || stats.total_rows_in_file || 0} rows in <strong>${stats.parsing_mode || 'process'}</strong> mode.</span>
                    </div>`;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            } else {
                noticeDiv.innerHTML = stats.parsing_mode === 'hierarchy'
                    ? `<div style="padding:8px 14px;background:#dcfce7;border:1px solid #86efac;border-radius:8px;color:#166534;font-size:12px;margin:8px 0;">
                        ✓ Roles Hierarchy map detected. Using <strong>inheritance</strong> mode (${stats.hierarchy_rows || 0} of ${stats.total_rows_in_file || 0} rows).
                    </div>`
                    : '';
            }
        }

        const breakdown = document.getElementById('sipoc-breakdown');
        if (breakdown) {
            let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
            // Disposition breakdown
            html += '<div><h5 style="margin:0 0 8px;">Disposition</h5>';
            const disp = data.dispositions || {};
            for (const [k, v] of Object.entries(disp)) {
                const color = k === 'Sanctioned' ? '#10b981' : k === 'To Be Retired' ? '#f59e0b' : '#9ca3af';
                html += `<div style="display:flex;align-items:center;gap:6px;margin:4px 0;"><span style="width:10px;height:10px;border-radius:50%;background:${color};"></span>${k}: <strong>${v}</strong></div>`;
            }
            html += '</div>';
            // Role type breakdown
            html += '<div><h5 style="margin:0 0 8px;">Role Types</h5>';
            const rt = data.role_types || {};
            for (const [k, v] of Object.entries(rt)) {
                html += `<div style="margin:4px 0;">${k}: <strong>${v}</strong></div>`;
            }
            html += '</div></div>';
            breakdown.innerHTML = html;
        }

        // Sample roles
        const sampleDiv = document.getElementById('sipoc-sample-roles');
        if (sampleDiv && data.sample_roles?.length) {
            let html = '<h5 style="margin:0 0 8px;">Sample Roles</h5><table class="dict-table" style="font-size:12px;"><thead><tr><th>Role</th><th>Function Area</th><th>Type</th><th>Disposition</th></tr></thead><tbody>';
            for (const r of data.sample_roles) {
                const dispClass = r.role_disposition === 'Sanctioned' ? 'color:#10b981' : r.role_disposition === 'To Be Retired' ? 'color:#f59e0b' : '';
                html += `<tr><td>${r.is_tool ? '🔧 ' : ''}${r.role_name}</td><td>${r.function_area || '-'}</td><td>${r.role_type || '-'}</td><td style="${dispClass}">${r.role_disposition || '-'}</td></tr>`;
            }
            html += '</tbody></table>';
            sampleDiv.innerHTML = html;
        }
    }

    function showSipocOptions() {
        showSipocStep(3);
        // Populate function area checkboxes (from resolved Col L/M names)
        const container = document.getElementById('sipoc-org-checkboxes');
        if (container && sipocPreviewData?.categories) {
            container.innerHTML = sipocPreviewData.categories.map(c =>
                `<label class="checkbox-label" style="break-inside:avoid;margin:2px 0;font-size:13px;"><input type="checkbox" value="${c}" checked> ${c}</label>`
            ).join('');
        }
    }

    async function executeSipocImport() {
        showSipocStep(4);
        const progressBar = document.getElementById('sipoc-progress-bar');
        const progressText = document.getElementById('sipoc-progress-text');
        if (progressBar) progressBar.style.width = '30%';
        if (progressText) progressText.textContent = 'Uploading and parsing file...';

        const fileInput = document.getElementById('sipoc-file-input');
        if (!fileInput?.files?.length) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        // Upsert mode — never clear existing data
        formData.append('clear_existing', 'false');

        try {
            if (progressBar) progressBar.style.width = '50%';
            if (progressText) progressText.textContent = 'Importing roles and relationships...';

            const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
            const resp = await fetch('/api/roles/dictionary/import-sipoc?confirm=true', {
                method: 'POST',
                headers: { 'X-CSRF-Token': csrf },
                body: formData
            });
            const data = await resp.json();

            if (progressBar) progressBar.style.width = '100%';

            if (!data.success) {
                const errMsg = typeof data.error === 'string' ? data.error : (data.error?.message || JSON.stringify(data.error) || 'Import failed');
                throw new Error(errMsg);
            }

            if (progressText) progressText.textContent = 'Complete!';

            setTimeout(() => {
                showSipocStep(5);
                renderSipocComplete(data.data);
            }, 500);
        } catch (err) {
            let errMsg = 'Import failed';
            if (err && typeof err.message === 'string' && err.message !== '[object Object]') {
                errMsg = err.message;
            } else if (err && typeof err === 'string') {
                errMsg = err;
            } else if (err) {
                try { errMsg = JSON.stringify(err); } catch (_) { errMsg = String(err); }
            }
            console.error('[TWR SIPOC] Import error:', err, '| Display message:', errMsg);
            if (progressText) progressText.textContent = `Error: ${errMsg}`;
            if (progressBar) progressBar.style.background = '#e53e3e';
        }
    }

    function renderSipocComplete(data) {
        const statsDiv = document.getElementById('sipoc-complete-stats');
        const adjudicatedCount = (data.roles_added || 0) + (data.roles_updated || 0);
        if (statsDiv) {
            const removed = (data.roles_removed || 0);
            statsDiv.innerHTML = `
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;max-width:400px;margin:0 auto;">
                    <div class="sipoc-stat-card"><div class="sipoc-stat-value">${data.roles_added || 0}</div><div class="sipoc-stat-label">Roles Added</div></div>
                    <div class="sipoc-stat-card"><div class="sipoc-stat-value">${data.roles_updated || 0}</div><div class="sipoc-stat-label">Roles Updated</div></div>
                    <div class="sipoc-stat-card"><div class="sipoc-stat-value">${data.relationships_created || 0}</div><div class="sipoc-stat-label">Relationships</div></div>
                    <div class="sipoc-stat-card"><div class="sipoc-stat-value">${data.tags_assigned || 0}</div><div class="sipoc-stat-label">Tags Assigned</div></div>
                    ${adjudicatedCount > 0 ? `<div class="sipoc-stat-card" style="border-color:#10b981;grid-column:span 2;"><div class="sipoc-stat-value" style="color:#10b981;">${adjudicatedCount}</div><div class="sipoc-stat-label">Auto-Adjudicated</div><div style="font-size:10px;color:var(--text-muted);margin-top:4px;">SIPOC roles auto-confirmed as source of truth</div></div>` : ''}
                    ${removed > 0 ? `<div class="sipoc-stat-card" style="border-color:var(--error,#e53e3e);grid-column:span 2;"><div class="sipoc-stat-value" style="color:var(--error,#e53e3e);">${removed}</div><div class="sipoc-stat-label">Stale Roles Removed</div><div style="font-size:10px;color:var(--text-muted);margin-top:4px;">Previously imported roles no longer in SIPOC</div></div>` : ''}
                </div>
            `;
        }
        // Show export button if hierarchy data exists
        const exportBtn = document.getElementById('btn-sipoc-export-hierarchy');
        if (exportBtn) exportBtn.style.display = '';
        // Show the export hierarchy button in toolbar
        const toolbarExportBtn = document.getElementById('btn-export-hierarchy');
        if (toolbarExportBtn) toolbarExportBtn.style.display = '';
        // Invalidate adjudication cache so badges update with SIPOC-confirmed roles
        if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
        // Reload dictionary
        loadDictionary();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function handleSipocWizardNext() {
        if (sipocCurrentStep === 1) {
            sipocUploadAndPreview();
        } else if (sipocCurrentStep === 2) {
            showSipocOptions();
        } else if (sipocCurrentStep === 3) {
            executeSipocImport();
        }
    }

    function handleSipocWizardBack() {
        if (sipocCurrentStep === 2) showSipocStep(1);
        else if (sipocCurrentStep === 3) showSipocStep(2);
    }

    // =====================================================================
    // HIERARCHY VIEW (v4.1.0) - In-app tree visualization
    // =====================================================================
    let hierarchyData = null;

    async function renderHierarchyView() {
        const container = document.getElementById('dict-content-area');
        if (!container) return;

        if (!hierarchyData) {
            container.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner-border"></div><p>Loading hierarchy...</p></div>';
            try {
                const resp = await fetch('/api/roles/hierarchy');
                const data = await resp.json();
                if (data.success) {
                    hierarchyData = data.data;
                } else {
                    container.innerHTML = `<div style="text-align:center;padding:40px;color:#666;">
                        <i data-lucide="git-branch" style="width:48px;height:48px;opacity:0.3;"></i>
                        <p style="margin-top:12px;">No hierarchy data available.</p>
                        <p class="text-muted">Import a Nimbus SIPOC file first to view the role hierarchy.</p>
                    </div>`;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                    return;
                }
            } catch (err) {
                container.innerHTML = `<div style="text-align:center;padding:40px;color:#e53e3e;">Error loading hierarchy: ${err.message}</div>`;
                return;
            }
        }

        const { nodes, edges, roots, children_map, stats } = hierarchyData;
        if (!nodes || nodes.length === 0) {
            container.innerHTML = `<div style="text-align:center;padding:40px;color:#666;">
                <i data-lucide="git-branch" style="width:48px;height:48px;opacity:0.3;"></i>
                <p style="margin-top:12px;">No inheritance data. Import a SIPOC file first.</p>
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        // Build a lookup for roles by name
        const roleMap = {};
        for (const r of DictState.roles) {
            roleMap[r.role_name?.toLowerCase()] = r;
        }

        // Build tree HTML
        let html = `<div class="hier-toolbar" style="display:flex;gap:8px;margin-bottom:12px;align-items:center;">
            <input type="text" id="hier-search" class="form-input" placeholder="Search roles..." style="width:200px;">
            <button class="btn btn-ghost btn-xs" onclick="document.querySelectorAll('.hier-children').forEach(c=>c.style.display='');">Expand All</button>
            <button class="btn btn-ghost btn-xs" onclick="document.querySelectorAll('.hier-children').forEach(c=>c.style.display='none');">Collapse All</button>
            <span class="text-muted" style="margin-left:auto;font-size:12px;">${stats?.total_nodes || nodes.length} nodes · ${stats?.total_edges || edges.length} relationships · ${(roots||[]).length} root nodes</span>
        </div>`;
        html += '<div class="hier-tree-container" style="max-height:600px;overflow:auto;border:1px solid var(--border-color,#ddd);border-radius:8px;padding:16px;">';

        function buildTreeNode(name, depth) {
            if (depth > 10) return '';
            const role = roleMap[name?.toLowerCase()];
            const kids = children_map?.[name] || [];
            const hasKids = kids.length > 0;
            const disp = role?.role_disposition || '';
            const baselined = role?.baselined;
            const isTool = role?.source === 'sipoc' && role?.category === 'Tools & Systems';

            let dispClass = '';
            let dispBadge = '';
            if (disp === 'Sanctioned') { dispClass = 'hier-sanctioned'; dispBadge = '<span class="hier-disp-badge hier-disp-sanctioned" title="Sanctioned">✓</span>'; }
            else if (disp === 'To Be Retired') { dispClass = 'hier-retiring'; dispBadge = '<span class="hier-disp-badge hier-disp-retiring" title="To Be Retired">⚠</span>'; }
            else if (disp === 'TBD') { dispClass = 'hier-tbd'; dispBadge = '<span class="hier-disp-badge hier-disp-tbd" title="TBD">?</span>'; }

            const baselinedBadge = baselined ? '<span class="hier-baselined" title="Baselined">✓</span>' : '';
            const toolIcon = isTool ? '🔧 ' : '';
            const orgBadge = role?.org_group ? `<span class="hier-org-badge">${role.org_group}</span>` : '';

            let nodeHtml = `<div class="hier-node ${dispClass}" data-name="${name}" style="margin-left:${depth * 20}px;">`;
            nodeHtml += `<span class="hier-toggle">${hasKids ? '▶' : '·'}</span>`;
            nodeHtml += `<span class="hier-name">${toolIcon}${name}</span>`;
            nodeHtml += dispBadge + baselinedBadge + orgBadge;
            if (hasKids) nodeHtml += `<span class="hier-count">(${kids.length})</span>`;
            nodeHtml += '</div>';

            if (hasKids) {
                nodeHtml += `<div class="hier-children" style="display:none;">`;
                for (const kid of kids) {
                    nodeHtml += buildTreeNode(kid, depth + 1);
                }
                nodeHtml += '</div>';
            }
            return nodeHtml;
        }

        if (roots && roots.length > 0) {
            for (const root of roots) {
                html += buildTreeNode(root, 0);
            }
        } else {
            html += '<p class="text-muted">No root nodes found in hierarchy.</p>';
        }

        html += '</div>';
        container.innerHTML = html;

        // Toggle handlers for tree
        container.querySelectorAll('.hier-toggle').forEach(toggle => {
            toggle.addEventListener('click', function() {
                const node = this.closest('.hier-node');
                const children = node.nextElementSibling;
                if (children && children.classList.contains('hier-children')) {
                    const isOpen = children.style.display !== 'none';
                    children.style.display = isOpen ? 'none' : '';
                    this.textContent = isOpen ? '▶' : '▼';
                }
            });
        });

        // Search
        const searchInput = document.getElementById('hier-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const q = this.value.toLowerCase();
                container.querySelectorAll('.hier-node').forEach(node => {
                    const name = node.dataset.name?.toLowerCase() || '';
                    if (q && name.includes(q)) {
                        node.classList.add('hier-highlight');
                        // Expand parents
                        let parent = node.parentElement;
                        while (parent) {
                            if (parent.classList?.contains('hier-children')) {
                                parent.style.display = '';
                                const prevToggle = parent.previousElementSibling?.querySelector('.hier-toggle');
                                if (prevToggle) prevToggle.textContent = '▼';
                            }
                            parent = parent.parentElement;
                        }
                    } else {
                        node.classList.remove('hier-highlight');
                    }
                });
            });
        }

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // =====================================================================
    // HIERARCHY EXPORT FILTER (v4.1.0)
    // =====================================================================
    async function showHierarchyExportModal() {
        const modal = document.getElementById('hierarchy-export-modal');
        if (!modal) return;
        // Move to body to escape Roles Studio stacking context (transform)
        if (modal.parentElement !== document.body) {
            document.body.appendChild(modal);
        }
        modal.style.display = 'flex';
        modal.classList.add('active');

        // Populate full function category hierarchy checkboxes
        await loadFunctionCategories();
        const cats = DictState.functionCategories;

        // Build parent → children map
        const childMap = {};
        cats.forEach(c => {
            if (c.parent_code) {
                if (!childMap[c.parent_code]) childMap[c.parent_code] = [];
                childMap[c.parent_code].push(c);
            }
        });
        // Sort children alphabetically
        Object.values(childMap).forEach(arr => arr.sort((a, b) => (a.name || a.code).localeCompare(b.name || b.code)));

        const topLevel = cats.filter(c => !c.parent_code).sort((a, b) => (a.name || a.code).localeCompare(b.name || b.code));

        const container = document.getElementById('hier-org-checkboxes');
        if (container) {
            let html = '';
            const makeLabel = (c, indent) => {
                const dotColor = c.color || '#3b82f6';
                const label = c.name || c.code;
                const pad = indent * 16;
                const fw = indent === 0 ? 'font-weight:600;' : '';
                const fs = indent === 0 ? '13px' : indent === 1 ? '12px' : '11px';
                return `<label class="checkbox-label hier-func-cb" style="break-inside:avoid;margin:1px 0;font-size:${fs};display:flex;align-items:center;gap:4px;padding-left:${pad}px;${fw}">` +
                    `<input type="checkbox" class="hier-func-check" value="${escapeHtml(c.code)}" data-level="${indent}" checked>` +
                    `<span style="display:inline-block;width:8px;height:8px;min-width:8px;max-width:8px;border-radius:50%;background:${dotColor};flex-shrink:0;"></span> ${escapeHtml(label)}</label>`;
            };

            topLevel.forEach(parent => {
                html += makeLabel(parent, 0);
                const children = childMap[parent.code] || [];
                children.forEach(child => {
                    html += makeLabel(child, 1);
                    const grandchildren = childMap[child.code] || [];
                    grandchildren.forEach(gc => {
                        html += makeLabel(gc, 2);
                    });
                });
            });
            container.innerHTML = html;
            // Override columns layout — use flex column for proper hierarchy display
            container.style.columns = 'unset';
            container.style.columnCount = 'unset';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.overflowX = 'hidden';

            // Smart cascading: parent toggle cascades to children/grandchildren
            container.addEventListener('change', (e) => {
                const cb = e.target;
                if (!cb.matches('input[type="checkbox"]')) return;
                const code = cb.value;
                const checked = cb.checked;
                // Find all children of this code
                const childCodes = (childMap[code] || []).map(c => c.code);
                const allDescendants = [...childCodes];
                childCodes.forEach(cc => {
                    (childMap[cc] || []).forEach(gc => allDescendants.push(gc.code));
                });
                // Cascade check state to all descendants
                allDescendants.forEach(dc => {
                    const dcCb = container.querySelector(`input[value="${dc}"]`);
                    if (dcCb) dcCb.checked = checked;
                });
                updateHierExportPreview();
            });
        }

        // Update preview count based on current filter state
        function updateHierExportPreview() {
            const previewEl = document.getElementById('hier-preview-count');
            if (!previewEl) return;
            const includeAll = document.getElementById('hier-include-all')?.checked;
            if (includeAll) {
                previewEl.textContent = 'All roles';
            } else {
                const selectedFuncs = document.querySelectorAll('#hier-org-checkboxes input:checked').length;
                const totalFuncs = document.querySelectorAll('#hier-org-checkboxes input').length;
                if (selectedFuncs === totalFuncs) {
                    previewEl.textContent = 'All functions selected';
                } else if (selectedFuncs === 0) {
                    previewEl.textContent = 'No functions selected';
                } else {
                    previewEl.textContent = selectedFuncs + ' of ' + totalFuncs + ' functions';
                }
            }
        }

        // Toggle filter options based on include-all checkbox
        const includeAll = document.getElementById('hier-include-all');
        const filterOptions = document.getElementById('hier-filter-options');
        if (includeAll && filterOptions) {
            includeAll.onchange = () => {
                filterOptions.style.opacity = includeAll.checked ? '0.4' : '1';
                filterOptions.style.pointerEvents = includeAll.checked ? 'none' : '';
                updateHierExportPreview();
            };
        }

        // Also listen for any change event on container to update preview (catches All/None dispatches)
        if (container) {
            container.addEventListener('change', () => updateHierExportPreview());
        }

        // Initial preview update
        updateHierExportPreview();

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function executeHierarchyExport() {
        const includeAll = document.getElementById('hier-include-all')?.checked;
        let url = '/api/roles/hierarchy/export-html?';
        const params = [];

        if (includeAll) {
            params.push('include_all=true');
        } else {
            // Function categories
            const selectedFunctions = [];
            document.querySelectorAll('#hier-org-checkboxes input:checked').forEach(cb => {
                selectedFunctions.push(cb.value);
            });
            if (selectedFunctions.length > 0) params.push('functions=' + encodeURIComponent(selectedFunctions.join(',')));

            // Dispositions
            const selectedDisps = [];
            document.querySelectorAll('.hier-disp-check:checked').forEach(cb => {
                selectedDisps.push(cb.value);
            });
            if (selectedDisps.length > 0 && selectedDisps.length < 3) params.push('disposition=' + encodeURIComponent(selectedDisps.join(',')));

            // Baselined
            const baselined = document.getElementById('hier-baselined-filter')?.value;
            if (baselined) params.push('baselined=' + baselined);

            // Include tools
            const includeTools = document.getElementById('hier-include-tools')?.checked;
            params.push('include_tools=' + (includeTools ? 'true' : 'false'));
        }

        url += params.join('&');

        try {
            if (typeof showToast === 'function') showToast('info', 'Generating hierarchy export...');
            const resp = await fetch(url);
            if (!resp.ok) throw new Error('Export failed');

            const blob = await resp.blob();
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `AEGIS_Role_Hierarchy_${new Date().toISOString().slice(0,10)}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);

            document.getElementById('hierarchy-export-modal').style.display = 'none';
            if (typeof showToast === 'function') showToast('success', 'Hierarchy export downloaded!');
        } catch (err) {
            if (typeof showToast === 'function') showToast('error', 'Export failed: ' + err.message);
        }
    }

    // =====================================================================
    // IMPORT DROPDOWN MENU
    // =====================================================================
    function toggleImportMenu() {
        const menu = document.getElementById('dict-import-menu');
        if (!menu) return;
        // v4.7.1: Use class toggle with CSS transition instead of display toggle to avoid flicker
        menu.classList.toggle('visible');
    }

    // =====================================================================
    // EVENT DELEGATION
    // =====================================================================
    function initEventDelegation() {
        const dictSection = document.getElementById('roles-dictionary');
        if (!dictSection) return;

        dictSection.addEventListener('click', (e) => {
            const target = e.target;

            // Action buttons
            const actionBtn = target.closest('[data-action]');
            if (actionBtn) {
                const action = actionBtn.dataset.action;
                const id = parseInt(actionBtn.dataset.id);
                if (action === 'edit') editRole(id);
                else if (action === 'clone') cloneRole(id);
                else if (action === 'toggle') toggleRole(id);
                else if (action === 'delete') deleteRole(id);
                return;
            }

            // Open role detail card — click on name text, name wrap, or card title row
            const nameEl = target.closest('.dict-role-name-text, .dict-card-name');
            if (nameEl) {
                const roleId = parseInt(nameEl.dataset.roleId);
                if (roleId) viewRoleDetail(roleId);
                return;
            }
            const nameWrap = target.closest('.dict-name-wrap, .dict-card-title-row');
            if (nameWrap) {
                const inner = nameWrap.querySelector('.dict-role-name-text, .dict-card-name');
                if (inner) {
                    const roleId = parseInt(inner.dataset.roleId);
                    if (roleId) viewRoleDetail(roleId);
                    return;
                }
            }

            // Inline category change
            const catBadge = target.closest('.dict-cat-inline');
            if (catBadge) {
                inlineChangeCategory(parseInt(catBadge.dataset.id));
                return;
            }

            // Card body click → open detail (card view only, skip badges/meta clicks that didn't match above)
            const cardEl = target.closest('.dict-card');
            if (cardEl && !target.closest('.dict-card-meta, .dict-card-footer, .dict-inline-star, .dict-inline-gear')) {
                const roleId = parseInt(cardEl.dataset.roleId);
                if (roleId) { viewRoleDetail(roleId); return; }
            }

            // View mode buttons
            const viewBtn = target.closest('.dict-view-btn');
            if (viewBtn) {
                setViewMode(viewBtn.dataset.view);
                return;
            }

            // Sort headers
            const sortTh = target.closest('.dict-th-sortable');
            if (sortTh) {
                const field = sortTh.dataset.sort;
                if (DictState.sortField === field) {
                    DictState.sortDir = DictState.sortDir === 'asc' ? 'desc' : 'asc';
                } else {
                    DictState.sortField = field;
                    DictState.sortDir = 'asc';
                }
                applyFilters();
                renderCurrentView();
                return;
            }

            // Bulk action buttons
            const bulkBtn = target.closest('[data-bulk]');
            if (bulkBtn) {
                bulkAction(bulkBtn.dataset.bulk);
                return;
            }

            // Import dropdown toggle
            if (target.closest('#btn-import-dictionary')) {
                toggleImportMenu();
                return;
            }

            // Import menu options
            const importOpt = target.closest('.dict-import-option');
            if (importOpt) {
                const type = importOpt.dataset.import;
                document.getElementById('dict-import-menu').classList.remove('visible');
                if (type === 'sipoc') {
                    showSipocImportModal();
                } else if (type === 'csv') {
                    // Trigger existing import modal
                    const existingModal = document.getElementById('import-dict-modal');
                    if (existingModal) existingModal.style.display = 'flex';
                }
                return;
            }

            // Export hierarchy button
            if (target.closest('#btn-export-hierarchy')) {
                showHierarchyExportModal();
                return;
            }

            // Download blank template for manual role entry
            if (target.closest('#btn-download-template')) {
                window.location.href = '/api/roles/dictionary/export-template';
                return;
            }
        });

        // Change events (checkboxes, selects)
        dictSection.addEventListener('change', (e) => {
            const target = e.target;

            // Select all checkbox
            if (target.classList.contains('dict-select-all')) {
                selectAll(target.checked);
                return;
            }

            // Individual row checkbox
            if (target.classList.contains('dict-row-check')) {
                toggleSelect(parseInt(target.dataset.id), target.checked);
                return;
            }

            // Deliverable toggle
            if (target.classList.contains('dict-deliv-check')) {
                inlineToggleDeliverable(parseInt(target.dataset.id), target.checked);
                return;
            }

            // Enhanced filter changes
            if (target.id === 'dict-filter-has-desc') {
                DictState.filterHasDescription = target.value;
                applyFilters(); renderCurrentView();
                return;
            }
            if (target.id === 'dict-filter-has-tags') {
                DictState.filterHasTags = target.value;
                applyFilters(); renderCurrentView();
                return;
            }
            if (target.id === 'dict-filter-adj-status') {
                DictState.filterAdjStatus = target.value;
                applyFilters(); renderCurrentView();
                return;
            }
        });
    }

    // =====================================================================
    // INITIALIZATION
    // =====================================================================
    function init() {
        if (_dictV5Init) return;
        _dictV5Init = true;

        console.log('[TWR DictV5] Initializing dictionary overhaul...');

        // Tab click listener
        const dictTab = document.querySelector('.roles-nav-item[data-tab="dictionary"]');
        if (dictTab) {
            dictTab.addEventListener('click', () => loadDictionary(), true);
        }

        // Search input (debounced)
        document.getElementById('dict-search')?.addEventListener('input', function() {
            if (DictState.loaded) {
                clearTimeout(this._debounce);
                this._debounce = setTimeout(() => {
                    applyFilters();
                    renderCurrentView();
                }, 300);
            }
        });

        // Basic filter changes
        document.getElementById('dict-filter-source')?.addEventListener('change', () => {
            if (DictState.loaded) { applyFilters(); renderCurrentView(); }
        });
        document.getElementById('dict-filter-category')?.addEventListener('change', () => {
            if (DictState.loaded) { applyFilters(); renderCurrentView(); }
        });

        // Save button
        const saveBtn = document.getElementById('btn-save-role');
        if (saveBtn) {
            const newBtn = saveBtn.cloneNode(true);
            saveBtn.parentNode.replaceChild(newBtn, saveBtn);
            newBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); saveRole(); });
        }

        // Modal buttons
        document.getElementById('btn-cancel-role')?.addEventListener('click', (e) => { e.stopPropagation(); closeRoleModal(); });
        document.getElementById('btn-close-role-modal')?.addEventListener('click', (e) => { e.stopPropagation(); closeRoleModal(); });

        const modalOverlay = document.querySelector('#edit-role-modal .modal-overlay');
        if (modalOverlay) modalOverlay.addEventListener('click', (e) => { e.stopPropagation(); closeRoleModal(); });

        const editModal = document.getElementById('edit-role-modal');
        if (editModal) editModal.addEventListener('click', (e) => e.stopPropagation());

        // Event delegation for all dynamic elements
        initEventDelegation();

        // Keyboard navigation
        initKeyboard();

        // SIPOC import wizard events (v4.1.0)
        // Note: file input change listeners are set up in showSipocImportModal() since
        // the dropzone innerHTML (including the file input) is recreated each time.
        // Only drag-drop is handled here; click-to-browse uses a <label> wrapping the button.
        const sipocDropzone = document.getElementById('sipoc-dropzone');
        if (sipocDropzone) {
            sipocDropzone.addEventListener('dragover', (e) => { e.preventDefault(); sipocDropzone.classList.add('drag-over'); });
            sipocDropzone.addEventListener('dragleave', () => sipocDropzone.classList.remove('drag-over'));
            sipocDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                sipocDropzone.classList.remove('drag-over');
                const fi = document.getElementById('sipoc-file-input');
                if (e.dataTransfer?.files?.length && fi) {
                    fi.files = e.dataTransfer.files;
                    fi.dispatchEvent(new Event('change'));
                }
            });
        }
        document.getElementById('sipoc-wizard-next')?.addEventListener('click', handleSipocWizardNext);
        document.getElementById('sipoc-wizard-back')?.addEventListener('click', handleSipocWizardBack);
        // When Done/Cancel is clicked on step 5, also refresh the dictionary
        document.getElementById('sipoc-wizard-cancel')?.addEventListener('click', () => {
            if (sipocCurrentStep === 5 && typeof loadDictionary === 'function') {
                loadDictionary();
            }
        });
        document.getElementById('btn-sipoc-export-hierarchy')?.addEventListener('click', () => {
            document.getElementById('sipoc-import-modal').style.display = 'none';
            showHierarchyExportModal();
        });

        // Hierarchy export modal events (v4.1.0)
        document.getElementById('btn-confirm-hierarchy-export')?.addEventListener('click', executeHierarchyExport);

        // Close import menu on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dict-import-dropdown')) {
                const menu = document.getElementById('dict-import-menu');
                if (menu) menu.classList.remove('visible');
            }
        });

        // Enhanced filter - adj status
        document.getElementById('dict-filter-adj-status')?.addEventListener('change', () => {
            if (DictState.loaded) { applyFilters(); renderCurrentView(); }
        });
        document.getElementById('dict-filter-has-desc')?.addEventListener('change', () => {
            if (DictState.loaded) { applyFilters(); renderCurrentView(); }
        });
        document.getElementById('dict-filter-has-tags')?.addEventListener('change', () => {
            if (DictState.loaded) { applyFilters(); renderCurrentView(); }
        });

        console.log('[TWR DictV5] Dictionary overhaul initialized');
    }

    // Init on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose API
    window.TWR = window.TWR || {};
    window.TWR.DictFix = {
        loadDictionary,
        renderDictionary: renderCurrentView,
        editRole,
        toggleRole,
        deleteRole,
        saveRole,
        closeRoleModal,
        handleCategoryChange,
        applyCustomCategory,
        cancelCustomCategory,
        addFunctionTag,
        removeEditTag,
        cloneRole,
        setViewMode,
        bulkAction,
        showSipocImportModal,
        closeSipocModal,
        showHierarchyExportModal,
        executeHierarchyExport
    };

})();
