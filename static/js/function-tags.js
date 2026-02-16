/**
 * AEGIS - Function Tags & Document Categories Management
 * v4.4.0 - Hierarchical function tags, document categorization, role requirements
 *
 * Features:
 * - Manage organizational function categories (A-Administration, E-Engineering, etc.)
 * - Assign function tags to roles
 * - Auto-detect document categories from document numbers
 * - Display role required actions from Statement Forge
 * - Generate HTML reports by function, document, or owner
 */

'use strict';

window.TWR = window.TWR || {};

TWR.FunctionTags = (function() {
    // State
    const State = {
        categories: [],
        roleTags: [],
        documentCategories: [],
        documentTypes: [],
        roleActions: [],
        loaded: false
    };

    // Utility functions
    function getEscapeHtml() {
        return window.TWR?.Utils?.escapeHtml || function(str) {
            if (str == null) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        };
    }

    function getToast() {
        return window.TWR?.Modals?.toast || window.toast || function(t, m) { console.log(`[${t}] ${m}`); };
    }

    function getApi() {
        return window.TWR?.API?.api || window.api || async function(url, opts) {
            const res = await fetch(url, opts);
            return res.json();
        };
    }

    /**
     * Extract a readable error message from an API error response.
     * The handle_api_errors decorator returns error as an object {code, message},
     * so we need to extract the message string to avoid [object Object] in toasts.
     */
    function extractErrorMessage(error, fallback = 'An error occurred') {
        if (!error) return fallback;
        if (typeof error === 'string') return error;
        if (typeof error === 'object') return error.message || error.code || JSON.stringify(error);
        return String(error);
    }

    /**
     * Build hierarchical function options for select dropdowns.
     * Groups categories by parent and shows indentation.
     *
     * @param {string} selectedValue - Currently selected value
     * @returns {string} HTML options string
     */
    function buildHierarchicalFunctionOptions(selectedValue = '') {
        const escapeHtml = getEscapeHtml();

        // Group categories by parent
        const topLevel = State.categories.filter(c => !c.parent_code);
        const byParent = {};

        State.categories.forEach(cat => {
            if (cat.parent_code) {
                if (!byParent[cat.parent_code]) {
                    byParent[cat.parent_code] = [];
                }
                byParent[cat.parent_code].push(cat);
            }
        });

        let options = '';

        // Build hierarchical options
        topLevel.forEach(parent => {
            const isSelected = selectedValue === parent.code ? ' selected' : '';
            const colorStyle = parent.color ? `style="border-left: 3px solid ${parent.color}; padding-left: 8px;"` : '';

            // Add parent as optgroup if it has children, otherwise as option
            const children = byParent[parent.code] || [];

            if (children.length > 0) {
                // Parent with children - use optgroup
                options += `<optgroup label="${escapeHtml(parent.code)} - ${escapeHtml(parent.name)}">`;

                // Add parent itself as selectable option within group
                options += `<option value="${escapeHtml(parent.code)}"${isSelected} ${colorStyle}>📁 ${escapeHtml(parent.code)} - ${escapeHtml(parent.name)} (All)</option>`;

                // Add children
                children.forEach(child => {
                    const childSelected = selectedValue === child.code ? ' selected' : '';
                    const childColorStyle = child.color ? `style="border-left: 3px solid ${child.color}; padding-left: 8px;"` : '';

                    // Check if child has its own children (3rd level)
                    const grandchildren = byParent[child.code] || [];

                    if (grandchildren.length > 0) {
                        options += `<option value="${escapeHtml(child.code)}"${childSelected} ${childColorStyle}>  ├─ ${escapeHtml(child.code)} - ${escapeHtml(child.name)}</option>`;
                        grandchildren.forEach((gc, idx) => {
                            const gcSelected = selectedValue === gc.code ? ' selected' : '';
                            const isLast = idx === grandchildren.length - 1;
                            const prefix = isLast ? '  │  └─' : '  │  ├─';
                            options += `<option value="${escapeHtml(gc.code)}"${gcSelected}>${prefix} ${escapeHtml(gc.code)} - ${escapeHtml(gc.name)}</option>`;
                        });
                    } else {
                        options += `<option value="${escapeHtml(child.code)}"${childSelected} ${childColorStyle}>  ├─ ${escapeHtml(child.code)} - ${escapeHtml(child.name)}</option>`;
                    }
                });

                options += '</optgroup>';
            } else {
                // No children - just add as option
                options += `<option value="${escapeHtml(parent.code)}"${isSelected} ${colorStyle}>${escapeHtml(parent.code)} - ${escapeHtml(parent.name)}</option>`;
            }
        });

        return options;
    }

    // ============================================================
    // FUNCTION CATEGORIES MANAGEMENT
    // ============================================================

    async function loadFunctionCategories() {
        try {
            const res = await fetch('/api/function-categories');
            const data = await res.json();
            if (data.success) {
                State.categories = data.data.categories || [];
                return State.categories;
            }
        } catch (e) {
            console.error('[FunctionTags] Error loading categories:', e);
        }
        return [];
    }

    async function createFunctionCategory(categoryData) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/function-categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify(categoryData)
            });
            const data = await res.json();
            if (data.success) {
                toast('success', data.message);
                await loadFunctionCategories();
                return true;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to create category'));
            }
        } catch (e) {
            toast('error', 'Error creating category: ' + e.message);
        }
        return false;
    }

    async function updateFunctionCategory(code, categoryData) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch(`/api/function-categories/${code}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify(categoryData)
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Category updated');
                await loadFunctionCategories();
                return true;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to update category'));
            }
        } catch (e) {
            toast('error', 'Error updating category: ' + e.message);
        }
        return false;
    }

    async function deleteFunctionCategory(code) {
        const toast = getToast();
        if (!confirm(`Are you sure you want to deactivate function "${code}"?`)) {
            return false;
        }
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch(`/api/function-categories/${code}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': csrfToken }
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Category deactivated');
                await loadFunctionCategories();
                return true;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to delete category'));
            }
        } catch (e) {
            toast('error', 'Error deleting category: ' + e.message);
        }
        return false;
    }

    // ============================================================
    // ROLE FUNCTION TAG ASSIGNMENTS
    // ============================================================

    async function loadRoleFunctionTags(roleName = null) {
        try {
            const url = roleName
                ? `/api/role-function-tags?role_name=${encodeURIComponent(roleName)}`
                : '/api/role-function-tags';
            const res = await fetch(url);
            const data = await res.json();
            if (data.success) {
                State.roleTags = data.data.tags || [];
                return State.roleTags;
            }
        } catch (e) {
            console.error('[FunctionTags] Error loading role tags:', e);
        }
        return [];
    }

    async function assignRoleFunctionTag(roleName, functionCode) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/role-function-tags', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ role_name: roleName, function_code: functionCode })
            });
            const data = await res.json();
            if (data.success) {
                toast('success', `Assigned "${roleName}" to ${functionCode}`);
                return true;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to assign tag'));
            }
        } catch (e) {
            toast('error', 'Error assigning tag: ' + e.message);
        }
        return false;
    }

    async function removeRoleFunctionTag(tagId) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch(`/api/role-function-tags/${tagId}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': csrfToken }
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Tag removed');
                return true;
            }
        } catch (e) {
            toast('error', 'Error removing tag: ' + e.message);
        }
        return false;
    }

    // ============================================================
    // DOCUMENT CATEGORIES
    // ============================================================

    async function loadDocumentCategories(filters = {}) {
        try {
            const params = new URLSearchParams(filters);
            const res = await fetch(`/api/document-categories?${params}`);
            const data = await res.json();
            if (data.success) {
                State.documentCategories = data.data.categories || [];
                return State.documentCategories;
            }
        } catch (e) {
            console.error('[FunctionTags] Error loading document categories:', e);
        }
        return [];
    }

    async function autoDetectDocumentCategory(documentName, documentContent = '') {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/document-categories/auto-detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ document_name: documentName, document_content: documentContent })
            });
            const data = await res.json();
            if (data.success) {
                return data.data;
            }
        } catch (e) {
            console.error('[FunctionTags] Error auto-detecting category:', e);
        }
        return { detected: false };
    }

    async function assignDocumentCategory(docData) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/document-categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify(docData)
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Document category assigned');
                return true;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to assign category'));
            }
        } catch (e) {
            toast('error', 'Error assigning category: ' + e.message);
        }
        return false;
    }

    // ============================================================
    // ROLE REQUIRED ACTIONS
    // ============================================================

    async function loadRoleRequiredActions(roleName = null) {
        try {
            const url = roleName
                ? `/api/role-required-actions?role_name=${encodeURIComponent(roleName)}`
                : '/api/role-required-actions';
            const res = await fetch(url);
            const data = await res.json();
            if (data.success) {
                State.roleActions = data.data.actions || [];
                return State.roleActions;
            }
        } catch (e) {
            console.error('[FunctionTags] Error loading role actions:', e);
        }
        return [];
    }

    async function extractRoleActionsFromDocument(documentContent, documentName, documentId) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/role-required-actions/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    document_content: documentContent,
                    document_name: documentName,
                    document_id: documentId
                })
            });
            const data = await res.json();
            if (data.success) {
                const extracted = data.data.extracted || [];
                if (extracted.length > 0) {
                    toast('success', `Extracted ${extracted.length} role requirements`);
                }
                return extracted;
            }
        } catch (e) {
            toast('error', 'Error extracting role actions: ' + e.message);
        }
        return [];
    }

    async function addRoleRequiredAction(actionData) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/role-required-actions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify(actionData)
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Required action added');
                return data.data.id;
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to add action'));
            }
        } catch (e) {
            toast('error', 'Error adding action: ' + e.message);
        }
        return null;
    }

    async function verifyRoleRequiredAction(actionId) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch(`/api/role-required-actions/${actionId}/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({})
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Action verified');
                return true;
            }
        } catch (e) {
            toast('error', 'Error verifying action: ' + e.message);
        }
        return false;
    }

    async function deleteRoleRequiredAction(actionId) {
        const toast = getToast();
        if (!confirm('Delete this required action?')) return false;
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch(`/api/role-required-actions/${actionId}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': csrfToken }
            });
            const data = await res.json();
            if (data.success) {
                toast('success', 'Action deleted');
                return true;
            }
        } catch (e) {
            toast('error', 'Error deleting action: ' + e.message);
        }
        return false;
    }

    // ============================================================
    // HTML REPORT GENERATION
    // ============================================================

    async function downloadReport(reportType, filters = {}) {
        // v4.7.0-fix: Use window.toast directly to ensure toast renders above modals
        const toast = window.toast || window.TWR?.Modals?.toast || getToast();
        try {
            // First check if there's data available
            const checkParams = new URLSearchParams({ format: 'json', check_only: 'true', ...filters });
            let checkUrl, reportUrl;

            switch (reportType) {
                case 'roles-by-function':
                    checkUrl = `/api/roles/reports/by-function?${checkParams}`;
                    reportUrl = `/api/roles/reports/by-function?format=html`;
                    break;
                case 'docs-by-function':
                    checkUrl = `/api/roles/reports/by-document?${checkParams}`;
                    reportUrl = `/api/roles/reports/by-document?format=html`;
                    break;
                case 'docs-by-owner':
                    checkUrl = `/api/roles/reports/by-owner?${checkParams}`;
                    reportUrl = `/api/roles/reports/by-owner?format=html`;
                    break;
                default:
                    toast('error', 'Unknown report type');
                    return;
            }

            // Check for data first
            toast('info', 'Checking for data...');
            const checkRes = await fetch(checkUrl);
            const checkData = await checkRes.json();

            if (!checkData.success) {
                toast('error', extractErrorMessage(checkData.error, 'Error checking report data'));
                return;
            }

            // Check if there's actually data to report
            const hasData = checkData.data && (
                (checkData.data.functions && checkData.data.functions.length > 0) ||
                (checkData.data.documents && checkData.data.documents.length > 0) ||
                (checkData.data.owners && checkData.data.owners.length > 0) ||
                (checkData.data.total_roles > 0) ||
                (checkData.data.total_documents > 0)
            );

            if (!hasData) {
                // Show detailed message about what's missing
                let message = 'No data available for this report. ';
                if (reportType === 'roles-by-function') {
                    message += 'No roles have been assigned to function categories yet. Assign function tags to roles in the Role Dictionary first.';
                } else if (reportType === 'docs-by-function') {
                    message += 'No documents have been categorized yet. Categorize documents or scan documents to extract role data first.';
                } else if (reportType === 'docs-by-owner') {
                    message += 'No document owners have been identified. Document owner information is extracted from document content during scanning.';
                }
                toast('warning', message);
                return;
            }

            // Build final report URL with filters
            if (filters.function_code) {
                reportUrl += `&function_code=${encodeURIComponent(filters.function_code)}`;
            }
            if (filters.owner) {
                reportUrl += `&owner=${encodeURIComponent(filters.owner)}`;
            }

            // v4.7.0-fix: Use hidden iframe for download instead of window.open()
            // window.open() gets blocked by popup blockers after async operations
            toast('info', 'Generating report...');
            // Create a hidden iframe to trigger the download without navigating away
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = reportUrl;
            document.body.appendChild(iframe);
            // Clean up after a delay
            setTimeout(() => {
                document.body.removeChild(iframe);
            }, 30000);
            toast('success', 'Report download started');
        } catch (e) {
            toast('error', 'Error generating report: ' + e.message);
        }
    }

    // ============================================================
    // UI COMPONENTS
    // ============================================================

    function renderFunctionCategorySelect(targetId, selectedCode = null, options = {}) {
        const select = document.getElementById(targetId);
        if (!select) return;

        const escapeHtml = getEscapeHtml();
        const includeEmpty = options.includeEmpty !== false;
        const emptyLabel = options.emptyLabel || 'Select Function...';

        let html = includeEmpty ? `<option value="">${emptyLabel}</option>` : '';

        State.categories.forEach(cat => {
            const selected = cat.code === selectedCode ? 'selected' : '';
            html += `<option value="${escapeHtml(cat.code)}" ${selected}>
                ${escapeHtml(cat.code)} - ${escapeHtml(cat.name)}
            </option>`;
        });

        select.innerHTML = html;
    }

    function renderFunctionTagBadges(tags, containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const escapeHtml = getEscapeHtml();
        const editable = options.editable !== false;

        if (!tags || tags.length === 0) {
            container.innerHTML = '<span class="text-muted text-sm">No function tags assigned</span>';
            return;
        }

        const html = tags.map(tag => `
            <span class="function-tag-badge" style="background: ${tag.function_color || '#3b82f6'}20; border-color: ${tag.function_color || '#3b82f6'}; color: ${tag.function_color || '#3b82f6'}">
                <span class="function-tag-code">${escapeHtml(tag.function_code)}</span>
                <span class="function-tag-name">${escapeHtml(tag.function_name || '')}</span>
                ${editable ? `<button class="function-tag-remove" data-tag-id="${tag.id}" title="Remove tag">&times;</button>` : ''}
            </span>
        `).join('');

        container.innerHTML = html;

        // Add remove handlers if editable
        if (editable) {
            container.querySelectorAll('.function-tag-remove').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const tagId = btn.dataset.tagId;
                    if (await removeRoleFunctionTag(tagId)) {
                        btn.closest('.function-tag-badge').remove();
                    }
                });
            });
        }
    }

    function renderRoleRequiredActionsPanel(roleName, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const escapeHtml = getEscapeHtml();
        const actions = State.roleActions.filter(a => a.role_name === roleName);

        if (actions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="clipboard-list"></i>
                    <p>No required actions found for this role</p>
                    <p class="text-muted text-sm">Actions are extracted from documents when a role is mentioned with requirement language (shall, must, is responsible for)</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        const html = `
            <div class="role-actions-list">
                ${actions.map(action => `
                    <div class="role-action-item ${action.is_verified ? 'verified' : ''}">
                        <div class="role-action-content">
                            <p class="role-action-text">${escapeHtml(action.statement_text)}</p>
                            <div class="role-action-meta">
                                <span class="role-action-source">${escapeHtml(action.source_document_name || 'Unknown source')}</span>
                                ${action.is_verified ? '<span class="verified-badge"><i data-lucide="check-circle"></i> Verified</span>' : ''}
                            </div>
                        </div>
                        <div class="role-action-actions">
                            ${!action.is_verified ? `
                                <button class="btn btn-ghost btn-xs" onclick="TWR.FunctionTags.verifyRoleRequiredAction(${action.id})" title="Verify">
                                    <i data-lucide="check"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-ghost btn-xs btn-danger" onclick="TWR.FunctionTags.deleteRoleRequiredAction(${action.id})" title="Delete">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // ============================================================
    // FUNCTION TAGS MANAGEMENT MODAL
    // ============================================================

    function showFunctionTagsModal() {
        const escapeHtml = getEscapeHtml();

        // Remove existing modal if any
        document.getElementById('function-tags-modal')?.remove();

        const modalHtml = `
            <div class="modal active modal-lg" id="function-tags-modal">
                <div class="modal-content" style="max-width: 800px; max-height: 80vh;">
                    <div class="modal-header">
                        <h3><i data-lucide="tags"></i> Function Categories Management</h3>
                        <button class="btn btn-ghost" onclick="document.getElementById('function-tags-modal').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="overflow-y: auto;">
                        <p class="text-muted mb-4">Manage organizational function categories. Changes to codes will update all role assignments.</p>

                        <div class="function-tags-toolbar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <button class="btn btn-primary btn-sm" onclick="TWR.FunctionTags.showAddCategoryForm()">
                                <i data-lucide="plus"></i> Add Category
                            </button>
                        </div>

                        <div id="function-categories-list" class="function-categories-list" style="max-height: 50vh; overflow-y: auto; overflow-x: auto; padding-right: 8px;">
                            <div class="loading">Loading categories...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Load and render categories - use mind map view directly
        loadFunctionCategories().then(() => {
            renderMindMapView();
        });
    }

    function renderFunctionCategoriesList() {
        const container = document.getElementById('function-categories-list');
        if (!container) return;

        const escapeHtml = getEscapeHtml();

        if (State.categories.length === 0) {
            container.innerHTML = '<div class="empty-state">No function categories found</div>';
            return;
        }

        // Build lookup maps
        const childrenByParent = {};
        State.categories.forEach(cat => {
            if (cat.parent_code) {
                if (!childrenByParent[cat.parent_code]) {
                    childrenByParent[cat.parent_code] = [];
                }
                childrenByParent[cat.parent_code].push(cat);
            }
        });

        // Get all descendants recursively
        function getAllDescendants(code) {
            const direct = childrenByParent[code] || [];
            let all = [...direct];
            direct.forEach(child => {
                all = all.concat(getAllDescendants(child.code));
            });
            return all;
        }

        // Render a category item (recursive for nested children)
        function renderCategory(cat, depth = 0, parentColor = null) {
            const children = childrenByParent[cat.code] || [];
            const hasChildren = children.length > 0;
            const allDescendants = getAllDescendants(cat.code);
            const totalRoles = (cat.role_count || 0) + allDescendants.reduce((sum, c) => sum + (c.role_count || 0), 0);
            const totalDocs = (cat.doc_count || 0) + allDescendants.reduce((sum, c) => sum + (c.doc_count || 0), 0);
            const color = cat.color || parentColor || '#3b82f6';

            const isTopLevel = depth === 0;
            const isSecondLevel = depth === 1;
            const isDeepLevel = depth >= 2;

            // Render children recursively
            const childrenHtml = hasChildren ? children.map(child =>
                renderCategory(child, depth + 1, color)
            ).join('') : '';

            if (isTopLevel) {
                // Top-level parent category
                return `
                    <div class="func-tree-item" data-code="${escapeHtml(cat.code)}">
                        <div class="func-tree-parent ${hasChildren ? 'has-children' : ''}" onclick="${hasChildren ? `TWR.FunctionTags.toggleTreeItem('${escapeHtml(cat.code)}')` : ''}">
                            <div class="func-tree-expand">
                                ${hasChildren ? '<i data-lucide="chevron-right" class="expand-icon"></i>' : '<span class="expand-spacer"></span>'}
                            </div>
                            <div class="func-tree-color" style="background: ${color}"></div>
                            <div class="func-tree-content">
                                <span class="func-tree-code">${escapeHtml(cat.code)}</span>
                                <span class="func-tree-name">${escapeHtml(cat.name)}</span>
                                ${hasChildren ? `<span class="func-tree-count">${allDescendants.length}</span>` : ''}
                            </div>
                            <div class="func-tree-stats">
                                <span class="stat-pill">${totalRoles} <i data-lucide="user" class="stat-icon"></i></span>
                                <span class="stat-pill">${totalDocs} <i data-lucide="file-text" class="stat-icon"></i></span>
                            </div>
                            <div class="func-tree-actions" onclick="event.stopPropagation()">
                                <button class="btn-icon" onclick="TWR.FunctionTags.showEditCategoryForm('${escapeHtml(cat.code)}')" title="Edit">
                                    <i data-lucide="pencil"></i>
                                </button>
                                <button class="btn-icon btn-icon-danger" onclick="TWR.FunctionTags.deleteFunctionCategory('${escapeHtml(cat.code)}')" title="Delete">
                                    <i data-lucide="trash-2"></i>
                                </button>
                            </div>
                        </div>
                        ${hasChildren ? `
                            <div class="func-tree-children" id="children-${escapeHtml(cat.code)}" style="display: none;">
                                ${childrenHtml}
                            </div>
                        ` : ''}
                    </div>
                `;
            } else if (isSecondLevel) {
                // Second-level category (can also expand if it has children)
                return `
                    <div class="func-tree-child-expandable" data-code="${escapeHtml(cat.code)}">
                        <div class="func-tree-child ${hasChildren ? 'has-children' : ''}" onclick="${hasChildren ? `TWR.FunctionTags.toggleTreeItem('${escapeHtml(cat.code)}')` : ''}">
                            <div class="func-tree-branch"></div>
                            ${hasChildren ? '<i data-lucide="chevron-right" class="expand-icon-sm"></i>' : '<span class="expand-spacer-sm"></span>'}
                            <div class="func-tree-color-sm" style="background: ${color}"></div>
                            <div class="func-tree-content">
                                <span class="func-tree-code-sm">${escapeHtml(cat.code)}</span>
                                <span class="func-tree-name-sm">${escapeHtml(cat.name)}</span>
                                ${hasChildren ? `<span class="func-tree-count-sm">${children.length}</span>` : ''}
                            </div>
                            <div class="func-tree-stats">
                                <span class="stat-pill-sm">${totalRoles} <i data-lucide="user" class="stat-icon-sm"></i></span>
                                <span class="stat-pill-sm">${totalDocs} <i data-lucide="file-text" class="stat-icon-sm"></i></span>
                            </div>
                            <div class="func-tree-actions" onclick="event.stopPropagation()">
                                <button class="btn-icon-sm" onclick="TWR.FunctionTags.showEditCategoryForm('${escapeHtml(cat.code)}')" title="Edit">
                                    <i data-lucide="pencil"></i>
                                </button>
                                <button class="btn-icon-sm btn-icon-danger" onclick="TWR.FunctionTags.deleteFunctionCategory('${escapeHtml(cat.code)}')" title="Delete">
                                    <i data-lucide="trash-2"></i>
                                </button>
                            </div>
                        </div>
                        ${hasChildren ? `
                            <div class="func-tree-grandchildren" id="children-${escapeHtml(cat.code)}" style="display: none;">
                                ${childrenHtml}
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                // Deep-level category (third level and beyond)
                return `
                    <div class="func-tree-leaf" data-code="${escapeHtml(cat.code)}">
                        <div class="func-tree-leaf-indent"></div>
                        <div class="func-tree-color-xs" style="background: ${color}"></div>
                        <div class="func-tree-content">
                            <span class="func-tree-code-xs">${escapeHtml(cat.code)}</span>
                            <span class="func-tree-name-xs">${escapeHtml(cat.name)}</span>
                        </div>
                        <div class="func-tree-stats">
                            <span class="stat-pill-xs">${cat.role_count || 0} <i data-lucide="user" class="stat-icon-xs"></i></span>
                            <span class="stat-pill-xs">${cat.doc_count || 0} <i data-lucide="file-text" class="stat-icon-xs"></i></span>
                        </div>
                        <div class="func-tree-actions" onclick="event.stopPropagation()">
                            <button class="btn-icon-xs" onclick="TWR.FunctionTags.showEditCategoryForm('${escapeHtml(cat.code)}')" title="Edit">
                                <i data-lucide="pencil"></i>
                            </button>
                            <button class="btn-icon-xs btn-icon-danger" onclick="TWR.FunctionTags.deleteFunctionCategory('${escapeHtml(cat.code)}')" title="Delete">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        // Render only top-level categories
        const parentCategories = State.categories.filter(c => !c.parent_code);
        const html = parentCategories.map(parent => renderCategory(parent, 0)).join('');

        container.innerHTML = html;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function toggleTreeItem(code) {
        const childrenEl = document.getElementById(`children-${code}`);
        const parentRow = document.querySelector(`[data-code="${code}"] > .func-tree-parent, [data-code="${code}"] > .func-tree-child`);

        if (!childrenEl) return;

        const isExpanded = childrenEl.style.display !== 'none';
        childrenEl.style.display = isExpanded ? 'none' : 'block';

        if (parentRow) {
            parentRow.classList.toggle('expanded', !isExpanded);
        }
    }

    // View mode state - mind map is the only view now
    let currentViewMode = 'mindmap';

    function setViewMode(mode) {
        currentViewMode = 'mindmap';
        renderMindMapView();
    }

    function toggleMindMapNode(code, event) {
        if (event) event.stopPropagation();

        const nodeContent = document.querySelector(`[data-mindmap-code="${code}"] .func-mindmap-node-content`);
        const branches = document.getElementById(`mindmap-branches-${code}`);

        if (!branches) return;

        const isExpanded = branches.classList.contains('expanded');

        branches.classList.toggle('expanded', !isExpanded);
        if (nodeContent) {
            nodeContent.classList.toggle('expanded', !isExpanded);
        }
    }

    function renderMindMapView() {
        const container = document.getElementById('function-categories-list');
        if (!container) return;

        const escapeHtml = getEscapeHtml();

        if (State.categories.length === 0) {
            container.innerHTML = '<div class="empty-state">No function categories found</div>';
            return;
        }

        // Build lookup maps
        const childrenByParent = {};
        State.categories.forEach(cat => {
            if (cat.parent_code) {
                if (!childrenByParent[cat.parent_code]) {
                    childrenByParent[cat.parent_code] = [];
                }
                childrenByParent[cat.parent_code].push(cat);
            }
        });

        // Get all descendants recursively
        function getAllDescendants(code) {
            const direct = childrenByParent[code] || [];
            let all = [...direct];
            direct.forEach(child => {
                all = all.concat(getAllDescendants(child.code));
            });
            return all;
        }

        // Render a mind map node
        function renderMindMapNode(cat, depth = 0, parentColor = null) {
            const children = childrenByParent[cat.code] || [];
            const hasChildren = children.length > 0;
            const allDescendants = getAllDescendants(cat.code);
            const totalRoles = (cat.role_count || 0) + allDescendants.reduce((sum, c) => sum + (c.role_count || 0), 0);
            const totalDocs = (cat.doc_count || 0) + allDescendants.reduce((sum, c) => sum + (c.doc_count || 0), 0);
            const color = cat.color || parentColor || '#3b82f6';

            const isRoot = depth === 0;
            const isChild = depth === 1;
            const isGrandchild = depth >= 2;

            const nodeClass = isRoot ? 'root-node' : (isChild ? 'child-node' : 'grandchild-node');

            // Abbreviate code for badge
            const abbrevCode = cat.code.length > 3 ?
                (cat.code.includes('-') ?
                    cat.code.split('-').map(p => p[0]).join('').substring(0, 3) :
                    cat.code.substring(0, 3)) :
                cat.code;

            let html = `
                <div class="func-mindmap-node" data-mindmap-code="${escapeHtml(cat.code)}">
                    <div class="func-mindmap-node-content ${nodeClass}" style="--node-color: ${color};"
                         onclick="${hasChildren ? `TWR.FunctionTags.toggleMindMapNode('${escapeHtml(cat.code)}', event)` : ''}">
                        ${isRoot ? '' : `<div class="func-mindmap-color" style="background: ${color};" title="${escapeHtml(cat.code)}">${abbrevCode}</div>`}
                        <div style="flex: 1;">
                            ${cat.code === cat.name ?
                                `<span class="func-mindmap-code">${escapeHtml(cat.code)}</span>` :
                                `<span class="func-mindmap-code">${escapeHtml(cat.code)}</span><span class="func-mindmap-separator"> — </span><span class="func-mindmap-name">${escapeHtml(cat.name)}</span>`
                            }
                            ${hasChildren ? `<span class="func-mindmap-count">${allDescendants.length}</span>` : ''}
                        </div>
                        <div class="func-mindmap-stats">
                            <span class="func-mindmap-stat roles-stat" title="Roles assigned to this function${hasChildren ? ' (including sub-functions)' : ''}"><i data-lucide="user"></i> ${totalRoles}</span>
                            <span class="func-mindmap-stat docs-stat" title="Documents tagged to this function${hasChildren ? ' (including sub-functions)' : ''}"><i data-lucide="file-text"></i> ${totalDocs}</span>
                        </div>
                        ${hasChildren ? `
                            <div class="func-mindmap-expand">
                                <i data-lucide="chevron-right"></i>
                            </div>
                        ` : ''}
                        <div class="func-mindmap-actions" onclick="event.stopPropagation()">
                            <button onclick="TWR.FunctionTags.showEditCategoryForm('${escapeHtml(cat.code)}')" title="Edit">
                                <i data-lucide="pencil"></i>
                            </button>
                            <button class="btn-danger" onclick="TWR.FunctionTags.deleteFunctionCategory('${escapeHtml(cat.code)}')" title="Delete">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
            `;

            if (hasChildren) {
                html += `
                    <div class="func-mindmap-branches" id="mindmap-branches-${escapeHtml(cat.code)}" style="--node-color: ${color};">
                        ${children.map(child => `
                            <div class="func-mindmap-branch" style="--node-color: ${child.color || color};">
                                ${renderMindMapNode(child, depth + 1, color)}
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            html += '</div>';
            return html;
        }

        // Render top-level categories
        const parentCategories = State.categories.filter(c => !c.parent_code);
        const html = `
            <div class="func-mindmap-container">
                ${parentCategories.map(parent => `
                    <div class="func-mindmap-root">
                        ${renderMindMapNode(parent, 0)}
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function showAddCategoryForm() {
        const formHtml = `
            <div class="category-form" id="category-form">
                <h4>Add New Category</h4>
                <div class="form-row">
                    <label>Code (1-4 chars)</label>
                    <input type="text" id="cat-code" maxlength="4" placeholder="E" style="width: 80px;">
                </div>
                <div class="form-row">
                    <label>Name</label>
                    <input type="text" id="cat-name" placeholder="Engineering">
                </div>
                <div class="form-row">
                    <label>Description</label>
                    <input type="text" id="cat-desc" placeholder="Engineering functions">
                </div>
                <div class="form-row">
                    <label>Color</label>
                    <input type="color" id="cat-color" value="#3b82f6">
                </div>
                <div class="form-actions">
                    <button class="btn btn-ghost" onclick="document.getElementById('category-form').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="TWR.FunctionTags.submitCategoryForm()">Create</button>
                </div>
            </div>
        `;

        const container = document.getElementById('function-categories-list');
        container.insertAdjacentHTML('beforebegin', formHtml);
    }

    function showEditCategoryForm(code) {
        const cat = State.categories.find(c => c.code === code);
        if (!cat) return;

        const escapeHtml = getEscapeHtml();
        const formHtml = `
            <div class="category-form" id="category-form">
                <h4>Edit Category: ${escapeHtml(code)}</h4>
                <input type="hidden" id="cat-original-code" value="${escapeHtml(code)}">
                <div class="form-row">
                    <label>Code (1-4 chars)</label>
                    <input type="text" id="cat-code" maxlength="4" value="${escapeHtml(cat.code)}" style="width: 80px;">
                </div>
                <div class="form-row">
                    <label>Name</label>
                    <input type="text" id="cat-name" value="${escapeHtml(cat.name)}">
                </div>
                <div class="form-row">
                    <label>Description</label>
                    <input type="text" id="cat-desc" value="${escapeHtml(cat.description || '')}">
                </div>
                <div class="form-row">
                    <label>Color</label>
                    <input type="color" id="cat-color" value="${cat.color || '#3b82f6'}">
                </div>
                <div class="form-actions">
                    <button class="btn btn-ghost" onclick="document.getElementById('category-form').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="TWR.FunctionTags.submitCategoryForm(true)">Update</button>
                </div>
            </div>
        `;

        // Remove existing form if any
        document.getElementById('category-form')?.remove();

        const container = document.getElementById('function-categories-list');
        container.insertAdjacentHTML('beforebegin', formHtml);
    }

    async function submitCategoryForm(isEdit = false) {
        const code = document.getElementById('cat-code').value.trim().toUpperCase();
        const name = document.getElementById('cat-name').value.trim();
        const description = document.getElementById('cat-desc').value.trim();
        const color = document.getElementById('cat-color').value;

        if (!code || !name) {
            getToast()('error', 'Code and name are required');
            return;
        }

        const data = { code, name, description, color };
        let success;

        if (isEdit) {
            const originalCode = document.getElementById('cat-original-code').value;
            success = await updateFunctionCategory(originalCode, data);
        } else {
            success = await createFunctionCategory(data);
        }

        if (success) {
            document.getElementById('category-form')?.remove();
            renderMindMapView();
        }
    }

    // ============================================================
    // REPORTS MODAL
    // ============================================================

    function showReportsModal() {
        // Remove existing modal if any
        document.getElementById('reports-modal')?.remove();

        const modalHtml = `
            <div class="modal active modal-md" id="reports-modal">
                <div class="modal-content" style="max-width: 640px;">
                    <div class="modal-header">
                        <h3><i data-lucide="file-text"></i> Generate Reports</h3>
                        <button class="btn btn-ghost" onclick="document.getElementById('reports-modal').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="overflow: visible;">
                        <div class="report-options">
                            <div class="report-option" onclick="TWR.FunctionTags.downloadReportWithFilters('roles-by-function')">
                                <div class="report-icon" style="background: #3b82f620; color: #3b82f6;">
                                    <i data-lucide="users"></i>
                                </div>
                                <div class="report-info">
                                    <h4>Roles by Function</h4>
                                    <p>View roles organized by organizational function, with their document appearances and required actions</p>
                                </div>
                            </div>

                            <div class="report-option" onclick="TWR.FunctionTags.downloadReportWithFilters('docs-by-function')">
                                <div class="report-icon" style="background: #10b98120; color: #10b981;">
                                    <i data-lucide="file-stack"></i>
                                </div>
                                <div class="report-info">
                                    <h4>Documents by Function</h4>
                                    <p>View documents organized by organizational function, with roles found in each</p>
                                </div>
                            </div>

                            <div class="report-option" onclick="TWR.FunctionTags.downloadReportWithFilters('docs-by-owner')">
                                <div class="report-icon" style="background: #8b5cf620; color: #8b5cf6;">
                                    <i data-lucide="user-circle"></i>
                                </div>
                                <div class="report-info">
                                    <h4>Documents by Owner</h4>
                                    <p>View documents grouped by document owner</p>
                                </div>
                            </div>
                        </div>

                        <div class="report-filters mt-4">
                            <h4>Filter Options</h4>

                            <!-- Hierarchical Function Picker -->
                            <div class="form-row" style="align-items: flex-start;">
                                <label style="margin-top: 8px;">Function</label>
                                <div class="rpt-func-picker" id="report-function-picker">
                                    <div class="rpt-func-picker-selected" id="rpt-func-selected" onclick="TWR.FunctionTags._toggleFuncPicker()">
                                        <span class="rpt-func-selected-text">All Functions</span>
                                        <span class="rpt-func-arrow">▾</span>
                                    </div>
                                    <div class="rpt-func-dropdown" id="rpt-func-dropdown" style="display:none;">
                                        <div class="rpt-func-search-wrap">
                                            <input type="text" id="rpt-func-search" class="rpt-func-search" placeholder="Search functions..." autocomplete="off">
                                        </div>
                                        <div class="rpt-func-tree" id="rpt-func-tree">
                                            <!-- populated dynamically -->
                                        </div>
                                        <div class="rpt-func-actions">
                                            <button class="rpt-func-clear-btn" onclick="TWR.FunctionTags._clearFuncSelection()">Clear All</button>
                                            <button class="rpt-func-done-btn" onclick="TWR.FunctionTags._toggleFuncPicker()">Done</button>
                                        </div>
                                    </div>
                                    <input type="hidden" id="report-function-filter" value="">
                                </div>
                            </div>

                            <!-- Document Owner Combobox -->
                            <div class="form-row" style="align-items: flex-start;">
                                <label style="margin-top: 8px;">Document Owner</label>
                                <div class="rpt-owner-combo" id="report-owner-combo">
                                    <input type="text" id="report-owner-filter" class="rpt-owner-input" placeholder="Type or select an owner..." autocomplete="off">
                                    <div class="rpt-owner-dropdown" id="rpt-owner-dropdown" style="display:none;">
                                        <div class="rpt-owner-list" id="rpt-owner-list">
                                            <!-- populated dynamically -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Populate hierarchical function picker
        loadFunctionCategories().then(() => {
            _buildFunctionTree();
        });

        // Populate owner combobox
        _loadDocumentOwners();

        // Prevent clicks inside the function dropdown from propagating (portal to body means it needs its own stopper)
        document.getElementById('rpt-func-dropdown').addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Close dropdowns on outside click (use document level since dropdown may be portaled to body)
        const _closeDropdowns = (e) => {
            // Don't close if clicking on the picker button itself (toggle handles that)
            if (e.target.closest('.rpt-func-picker')) return;
            const dd = document.getElementById('rpt-func-dropdown');
            if (dd && dd.style.display !== 'none') {
                dd.style.display = 'none';
                const picker = document.getElementById('report-function-picker');
                if (dd.parentElement === document.body && picker) picker.appendChild(dd);
            }
            if (!e.target.closest('.rpt-owner-combo')) {
                const ownerDd = document.getElementById('rpt-owner-dropdown');
                if (ownerDd) ownerDd.style.display = 'none';
            }
        };
        document.addEventListener('click', _closeDropdowns);
        // Cleanup when modal is removed
        const reportsModal = document.getElementById('reports-modal');
        const observer = new MutationObserver(() => {
            if (!document.getElementById('reports-modal')) {
                document.removeEventListener('click', _closeDropdowns);
                observer.disconnect();
                const dd = document.getElementById('rpt-func-dropdown');
                if (dd && dd.parentElement === document.body) dd.remove();
            }
        });
        observer.observe(reportsModal.parentElement, { childList: true });
    }

    // Track multi-selected function codes
    const _selectedFunctions = new Set();

    /**
     * Collect filter values and trigger report download
     */
    function downloadReportWithFilters(reportType) {
        const funcVal = Array.from(_selectedFunctions).join(',');
        const ownerVal = document.getElementById('report-owner-filter')?.value || '';
        const filters = {};
        if (funcVal) filters.function_code = funcVal;
        if (ownerVal) filters.owner = ownerVal;
        downloadReport(reportType, filters);
    }

    /**
     * Toggle function picker dropdown
     */
    function _toggleFuncPicker() {
        const dd = document.getElementById('rpt-func-dropdown');
        if (!dd) return;
        const isOpen = dd.style.display !== 'none';
        if (isOpen) {
            dd.style.display = 'none';
            // Move back into picker if it was portaled to body
            const picker = document.getElementById('report-function-picker');
            if (dd.parentElement === document.body && picker) {
                picker.appendChild(dd);
            }
        } else {
            // Portal dropdown to body to avoid modal clipping/click issues
            const btn = document.getElementById('rpt-func-selected');
            if (btn) {
                const rect = btn.getBoundingClientRect();
                document.body.appendChild(dd);
                dd.style.position = 'fixed';
                dd.style.top = (rect.bottom + 4) + 'px';
                dd.style.left = rect.left + 'px';
                dd.style.width = rect.width + 'px';
                dd.style.right = 'auto';
            }
            dd.style.display = 'flex';
            const search = document.getElementById('rpt-func-search');
            if (search) { search.value = ''; search.focus(); _filterFuncTree(''); }
        }
    }

    /**
     * Build the hierarchical function tree with checkboxes for multi-select
     */
    function _buildFunctionTree() {
        const container = document.getElementById('rpt-func-tree');
        if (!container) return;
        const escapeHtml = getEscapeHtml();

        const topLevel = State.categories.filter(c => !c.parent_code);
        const byParent = {};
        State.categories.forEach(cat => {
            if (cat.parent_code) {
                if (!byParent[cat.parent_code]) byParent[cat.parent_code] = [];
                byParent[cat.parent_code].push(cat);
            }
        });

        let html = '';

        topLevel.forEach(parent => {
            const children = byParent[parent.code] || [];
            const colorDot = parent.color ? `<span class="rpt-func-dot" style="background:${parent.color}"></span>` : '';
            const displayName = `${escapeHtml(parent.code)} – ${escapeHtml(parent.name)}`;

            if (children.length > 0) {
                html += `<div class="rpt-func-group" data-code="${escapeHtml(parent.code)}">
                    <div class="rpt-func-group-header">
                        <span class="rpt-func-expand-icon" onclick="TWR.FunctionTags._toggleFuncGroup(this.closest('.rpt-func-group-header'))">▸</span>
                        <label class="rpt-func-check-label" onclick="event.stopPropagation();">
                            <input type="checkbox" class="rpt-func-cb" data-code="${escapeHtml(parent.code)}" data-is-parent="1" onchange="TWR.FunctionTags._toggleFuncCheck(this)">
                            ${colorDot}
                            <span class="rpt-func-item-label">${displayName}</span>
                        </label>
                        <span class="rpt-func-child-count" onclick="TWR.FunctionTags._toggleFuncGroup(this.closest('.rpt-func-group-header'))">${children.length}</span>
                    </div>
                    <div class="rpt-func-children" style="display:none;">`;
                children.forEach(child => {
                    const childColor = child.color ? `<span class="rpt-func-dot" style="background:${child.color}"></span>` : '';
                    const childDisplay = `${escapeHtml(child.code)} – ${escapeHtml(child.name)}`;
                    html += `<div class="rpt-func-item rpt-func-child-item" data-value="${escapeHtml(child.code)}">
                        <label class="rpt-func-check-label">
                            <input type="checkbox" class="rpt-func-cb" data-code="${escapeHtml(child.code)}" data-parent="${escapeHtml(parent.code)}" onchange="TWR.FunctionTags._toggleFuncCheck(this)">
                            ${childColor}
                            <span class="rpt-func-item-label">${childDisplay}</span>
                        </label>
                    </div>`;
                });
                html += `</div></div>`;
            } else {
                html += `<div class="rpt-func-item" data-value="${escapeHtml(parent.code)}">
                    <label class="rpt-func-check-label">
                        <input type="checkbox" class="rpt-func-cb" data-code="${escapeHtml(parent.code)}" onchange="TWR.FunctionTags._toggleFuncCheck(this)">
                        ${colorDot}
                        <span class="rpt-func-item-label">${displayName}</span>
                    </label>
                </div>`;
            }
        });

        container.innerHTML = html;

        // Wire up search
        const search = document.getElementById('rpt-func-search');
        if (search) {
            search.addEventListener('input', (e) => _filterFuncTree(e.target.value));
        }
    }

    /**
     * Handle checkbox toggle for multi-select
     */
    function _toggleFuncCheck(cb) {
        const code = cb.dataset.code;
        const isParent = cb.dataset.isParent === '1';

        if (cb.checked) {
            _selectedFunctions.add(code);
        } else {
            _selectedFunctions.delete(code);
        }

        // If parent checkbox toggled, also toggle all children
        if (isParent) {
            const group = cb.closest('.rpt-func-group');
            if (group) {
                const childCbs = group.querySelectorAll('.rpt-func-children .rpt-func-cb');
                childCbs.forEach(childCb => {
                    childCb.checked = cb.checked;
                    if (cb.checked) {
                        _selectedFunctions.add(childCb.dataset.code);
                    } else {
                        _selectedFunctions.delete(childCb.dataset.code);
                    }
                });
                // Auto-expand children when parent is checked
                if (cb.checked) {
                    const children = group.querySelector('.rpt-func-children');
                    const icon = group.querySelector('.rpt-func-expand-icon');
                    if (children && children.style.display === 'none') {
                        children.style.display = 'block';
                        if (icon) icon.textContent = '▾';
                    }
                }
            }
        } else {
            // Child toggled — update parent's indeterminate/checked state
            const parentCode = cb.dataset.parent;
            if (parentCode) {
                const group = cb.closest('.rpt-func-group');
                if (group) {
                    const parentCb = group.querySelector('.rpt-func-group-header .rpt-func-cb');
                    const childCbs = Array.from(group.querySelectorAll('.rpt-func-children .rpt-func-cb'));
                    const allChecked = childCbs.every(c => c.checked);
                    const someChecked = childCbs.some(c => c.checked);
                    if (parentCb) {
                        parentCb.checked = allChecked;
                        parentCb.indeterminate = someChecked && !allChecked;
                        if (allChecked) {
                            _selectedFunctions.add(parentCode);
                        } else {
                            _selectedFunctions.delete(parentCode);
                        }
                    }
                }
            }
        }

        _updateFuncPickerLabel();
        // Sync hidden input
        document.getElementById('report-function-filter').value = Array.from(_selectedFunctions).join(',');
    }

    /**
     * Update the picker button label to reflect selections
     */
    function _updateFuncPickerLabel() {
        const textEl = document.querySelector('.rpt-func-selected-text');
        if (!textEl) return;
        const count = _selectedFunctions.size;
        if (count === 0) {
            textEl.textContent = 'All Functions';
            textEl.title = '';
        } else if (count <= 3) {
            textEl.textContent = Array.from(_selectedFunctions).join(', ');
            textEl.title = textEl.textContent;
        } else {
            textEl.textContent = `${count} functions selected`;
            textEl.title = Array.from(_selectedFunctions).join(', ');
        }
    }

    /**
     * Clear all function selections
     */
    function _clearFuncSelection() {
        _selectedFunctions.clear();
        const tree = document.getElementById('rpt-func-tree');
        if (tree) {
            tree.querySelectorAll('.rpt-func-cb').forEach(cb => {
                cb.checked = false;
                cb.indeterminate = false;
            });
        }
        _updateFuncPickerLabel();
        document.getElementById('report-function-filter').value = '';
    }

    /**
     * Select a function from the tree (legacy single-select, kept for compatibility)
     */
    function _selectFunction(code, displayName) {
        document.getElementById('report-function-filter').value = code;
        const selectedText = document.querySelector('.rpt-func-selected-text');
        if (selectedText) selectedText.textContent = displayName || 'All Functions';
        document.getElementById('rpt-func-dropdown').style.display = 'none';
    }

    /**
     * Toggle a parent group open/closed
     */
    function _toggleFuncGroup(headerEl) {
        const group = headerEl.closest('.rpt-func-group');
        const children = group.querySelector('.rpt-func-children');
        const icon = headerEl.querySelector('.rpt-func-expand-icon');
        if (children.style.display === 'none') {
            children.style.display = 'block';
            icon.textContent = '▾';
        } else {
            children.style.display = 'none';
            icon.textContent = '▸';
        }
    }

    /**
     * Filter the function tree by search text
     */
    function _filterFuncTree(query) {
        const tree = document.getElementById('rpt-func-tree');
        if (!tree) return;
        const q = query.toLowerCase().trim();

        // Show all if empty
        tree.querySelectorAll('.rpt-func-item, .rpt-func-group').forEach(el => el.style.display = '');
        tree.querySelectorAll('.rpt-func-children').forEach(el => el.style.display = 'none');

        if (!q) return;

        // Hide non-matching items, expand groups with matches
        tree.querySelectorAll('.rpt-func-group').forEach(group => {
            const code = (group.dataset.code || '').toLowerCase();
            const headerLabel = group.querySelector('.rpt-func-group-label')?.textContent?.toLowerCase() || '';
            const children = group.querySelectorAll('.rpt-func-child-item');
            let hasMatchingChild = false;

            children.forEach(child => {
                const name = (child.dataset.name || '').toLowerCase();
                const val = (child.dataset.value || '').toLowerCase();
                if (name.includes(q) || val.includes(q)) {
                    child.style.display = '';
                    hasMatchingChild = true;
                } else {
                    child.style.display = 'none';
                }
            });

            if (hasMatchingChild || headerLabel.includes(q) || code.includes(q)) {
                group.style.display = '';
                if (hasMatchingChild) {
                    group.querySelector('.rpt-func-children').style.display = 'block';
                    group.querySelector('.rpt-func-expand-icon').textContent = '▾';
                }
            } else {
                group.style.display = 'none';
            }
        });

        // Also filter standalone items
        tree.querySelectorAll(':scope > .rpt-func-item').forEach(item => {
            if (item.classList.contains('rpt-func-item-all')) return; // keep "All Functions" visible
            const name = (item.dataset.name || '').toLowerCase();
            const val = (item.dataset.value || '').toLowerCase();
            item.style.display = (name.includes(q) || val.includes(q)) ? '' : 'none';
        });
    }

    /**
     * Load document owners grouped by function for the combobox
     */
    async function _loadDocumentOwners() {
        try {
            const res = await fetch('/api/roles/reports/by-document?format=json&check_only=false');
            const data = await res.json();
            if (!data.success || !data.data) return;

            const functions = data.data.functions || [];
            const ownerMap = {}; // owner -> Set of function codes
            const funcInfo = {}; // code -> {name, color}

            functions.forEach(func => {
                const code = func.function_code || 'Unassigned';
                funcInfo[code] = { name: func.function_name || code, color: func.function_color || '#6b7280' };
                (func.documents || []).forEach(doc => {
                    const owner = doc.document_owner;
                    if (owner && owner.trim()) {
                        if (!ownerMap[owner]) ownerMap[owner] = new Set();
                        ownerMap[owner].add(code);
                    }
                });
            });

            // Build grouped list
            const listEl = document.getElementById('rpt-owner-list');
            if (!listEl) return;
            const escapeHtml = getEscapeHtml();

            if (Object.keys(ownerMap).length === 0) {
                listEl.innerHTML = '<div class="rpt-owner-empty">No document owners found. Owners are extracted during document scanning.</div>';
            } else {
                // Group owners by their primary function
                const byFunc = {};
                Object.entries(ownerMap).forEach(([owner, funcs]) => {
                    const primaryFunc = [...funcs][0];
                    if (!byFunc[primaryFunc]) byFunc[primaryFunc] = [];
                    byFunc[primaryFunc].push({ owner, functions: [...funcs] });
                });

                let html = `<div class="rpt-owner-item" data-owner="" onclick="TWR.FunctionTags._selectOwner('')">
                    <span class="rpt-owner-item-name" style="color:var(--text-muted);">All Owners (no filter)</span>
                </div>`;

                Object.entries(byFunc).sort((a, b) => a[0].localeCompare(b[0])).forEach(([funcCode, owners]) => {
                    const fi = funcInfo[funcCode] || { name: funcCode, color: '#6b7280' };
                    html += `<div class="rpt-owner-func-header">
                        <span class="rpt-func-dot" style="background:${fi.color}"></span>
                        ${escapeHtml(funcCode)} – ${escapeHtml(fi.name)}
                    </div>`;
                    owners.sort((a, b) => a.owner.localeCompare(b.owner)).forEach(o => {
                        const funcBadges = o.functions.length > 1
                            ? o.functions.slice(1).map(f => `<span class="rpt-owner-func-badge" style="background:${(funcInfo[f]||{}).color||'#6b7280'}">${escapeHtml(f)}</span>`).join('')
                            : '';
                        html += `<div class="rpt-owner-item" data-owner="${escapeHtml(o.owner)}" onclick="TWR.FunctionTags._selectOwner('${escapeHtml(o.owner)}')">
                            <span class="rpt-owner-item-name">${escapeHtml(o.owner)}</span>
                            ${funcBadges ? `<span class="rpt-owner-also">also: ${funcBadges}</span>` : ''}
                        </div>`;
                    });
                });
                listEl.innerHTML = html;
            }

            // Wire up input events
            const input = document.getElementById('report-owner-filter');
            if (input) {
                input.addEventListener('focus', () => {
                    const dd = document.getElementById('rpt-owner-dropdown');
                    if (dd) dd.style.display = 'block';
                });
                input.addEventListener('input', (e) => _filterOwnerList(e.target.value));
            }
        } catch (err) {
            console.warn('[FunctionTags] Could not load document owners:', err);
        }
    }

    /**
     * Select an owner from the dropdown
     */
    function _selectOwner(owner) {
        const input = document.getElementById('report-owner-filter');
        if (input) input.value = owner;
        document.getElementById('rpt-owner-dropdown').style.display = 'none';
    }

    /**
     * Filter owner list by typed text
     */
    function _filterOwnerList(query) {
        const list = document.getElementById('rpt-owner-list');
        if (!list) return;
        const q = query.toLowerCase().trim();
        const dropdown = document.getElementById('rpt-owner-dropdown');
        if (dropdown && dropdown.style.display === 'none') {
            dropdown.style.display = 'block';
        }

        list.querySelectorAll('.rpt-owner-item, .rpt-owner-func-header').forEach(el => {
            el.style.display = '';
        });

        if (!q) return;

        // Hide non-matching owner items and their orphan headers
        const headers = list.querySelectorAll('.rpt-owner-func-header');
        headers.forEach(header => {
            let nextEl = header.nextElementSibling;
            let hasVisibleChild = false;
            while (nextEl && !nextEl.classList.contains('rpt-owner-func-header')) {
                if (nextEl.classList.contains('rpt-owner-item')) {
                    const name = (nextEl.dataset.owner || '').toLowerCase();
                    if (!nextEl.dataset.owner && nextEl.dataset.owner !== '') {
                        // "All Owners" item
                        nextEl.style.display = 'none';
                    } else if (name.includes(q)) {
                        nextEl.style.display = '';
                        hasVisibleChild = true;
                    } else {
                        nextEl.style.display = 'none';
                    }
                }
                nextEl = nextEl.nextElementSibling;
            }
            header.style.display = hasVisibleChild ? '' : 'none';
        });

        // Hide "All Owners" when searching
        const allItem = list.querySelector('.rpt-owner-item[data-owner=""]');
        if (allItem) allItem.style.display = 'none';
    }

    // ============================================================
    // DOCUMENT TAGS MODAL
    // ============================================================

    async function showDocumentTagsModal() {
        // Remove existing modal if any
        document.getElementById('document-tags-modal')?.remove();

        const escapeHtml = getEscapeHtml();

        const modalHtml = `
            <div class="modal active modal-lg" id="document-tags-modal">
                <div class="modal-content" style="max-width: 900px; max-height: 85vh;">
                    <div class="modal-header">
                        <h3><i data-lucide="tags"></i> Document Tags Management</h3>
                        <button class="btn btn-ghost" onclick="document.getElementById('document-tags-modal').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="overflow-y: auto;">
                        <p class="text-muted mb-4">Assign function categories and document types to analyzed documents. Tags help organize reports and are auto-detected from document names when possible.</p>

                        <div class="doc-tags-toolbar">
                            <div class="doc-tags-filters">
                                <input type="text" id="doc-tags-search" class="form-input" placeholder="Search documents..." style="max-width: 300px;">
                            </div>
                            <div class="doc-tags-actions">
                                <button class="btn btn-secondary btn-sm" onclick="TWR.FunctionTags.autoDetectAllTags()">
                                    <i data-lucide="wand-2"></i> Auto-detect All Untagged
                                </button>
                            </div>
                        </div>

                        <div id="document-tags-list" class="document-tags-list" style="max-height: 50vh; overflow-y: auto;">
                            <div class="loading">Loading documents...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Load and render documents
        await loadDocumentTagsData();

        // Setup search filter
        document.getElementById('doc-tags-search')?.addEventListener('input', function() {
            clearTimeout(this._debounce);
            this._debounce = setTimeout(() => renderDocumentTagsList(this.value), 300);
        });
    }

    let _documentTagsData = [];

    async function loadDocumentTagsData() {
        try {
            // Get unique documents from the documents table directly
            const res = await fetch('/api/documents?limit=500');
            const data = await res.json();

            let documents = [];
            if (data.success && data.data) {
                documents = Array.isArray(data.data) ? data.data : (data.data.documents || data.data || []);
            }

            // If no documents endpoint, fall back to scan history but de-duplicate
            if (documents.length === 0) {
                const scanRes = await fetch('/api/scan-history?limit=500');
                const scanData = await scanRes.json();

                let scans = [];
                if (scanData.success !== false && scanData.data) {
                    scans = Array.isArray(scanData.data) ? scanData.data : (scanData.data.documents || []);
                }

                // De-duplicate by document_id, keeping the most recent scan stats
                const docMap = {};
                scans.forEach(scan => {
                    const docId = scan.document_id;
                    if (!docMap[docId] || new Date(scan.scan_time) > new Date(docMap[docId].scan_time)) {
                        docMap[docId] = {
                            id: docId,
                            filename: scan.filename,
                            roles_count: scan.role_count || 0,
                            scan_time: scan.scan_time
                        };
                    }
                });

                documents = Object.values(docMap);
            } else {
                // Normalize document data structure
                documents = documents.map(doc => ({
                    id: doc.id || doc.document_id,
                    filename: doc.filename || doc.name,
                    roles_count: doc.role_count || doc.roles_count || 0,
                    scan_time: doc.last_scan || doc.scan_time || doc.created_at
                }));
            }

            _documentTagsData = documents;

            // Also get existing document categories
            try {
                const catRes = await fetch('/api/document-categories');
                const catData = await catRes.json();
                const existingCats = catData.success ? (catData.data?.categories || []) : [];

                // Merge category data into documents
                const catMap = {};
                existingCats.forEach(c => {
                    catMap[c.document_id] = c;
                });

                _documentTagsData.forEach(doc => {
                    const cat = catMap[doc.id];
                    if (cat) {
                        doc.function_code = cat.function_code;
                        doc.category_type = cat.category_type;
                        doc.document_owner = cat.document_owner;
                    }
                });
            } catch (catErr) {
                console.warn('[FunctionTags] Could not load document categories:', catErr);
            }

            // Sort by filename for easier browsing
            _documentTagsData.sort((a, b) => (a.filename || '').localeCompare(b.filename || ''));

            renderDocumentTagsList();
        } catch (e) {
            console.error('[FunctionTags] Error loading document tags:', e);
            const container = document.getElementById('document-tags-list');
            if (container) {
                container.innerHTML = '<div class="empty-state text-error">Error loading documents: ' + e.message + '</div>';
            }
        }
    }

    function renderDocumentTagsList(searchTerm = '') {
        const container = document.getElementById('document-tags-list');
        if (!container) return;

        const escapeHtml = getEscapeHtml();
        const term = searchTerm.toLowerCase();

        // Filter documents
        const filtered = _documentTagsData.filter(doc => {
            if (!term) return true;
            return (doc.filename || '').toLowerCase().includes(term) ||
                   (doc.function_code || '').toLowerCase().includes(term) ||
                   (doc.document_owner || '').toLowerCase().includes(term);
        });

        if (filtered.length === 0) {
            container.innerHTML = '<div class="empty-state">No documents found</div>';
            return;
        }

        const categoryTypes = ['Procedure', 'Work Instruction', 'Specification', 'Knowledgebase', 'Policy', 'Standard', 'Plan', 'Report', 'Drawing', 'Design Document', 'Other'];
        const typeOptions = categoryTypes.map(t =>
            `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`
        ).join('');

        const html = filtered.map(doc => {
            const funcSelected = doc.function_code || '';
            const typeSelected = doc.category_type || '';
            const owner = doc.document_owner || '';
            const hasTag = funcSelected || typeSelected || owner;
            const tagStatusClass = hasTag ? 'has-tag' : 'no-tag';
            const autoDetected = doc.auto_detected ? '<span class="auto-detect-badge" title="Auto-detected">Auto</span>' : '';

            // Build hierarchical function options for this document
            const funcOptions = buildHierarchicalFunctionOptions(funcSelected);

            return `
                <div class="doc-tag-row ${tagStatusClass}" data-doc-id="${doc.id}">
                    <div class="doc-tag-name">
                        <strong>${escapeHtml(doc.filename || 'Unknown')}</strong>
                        <div class="doc-tag-meta">
                            <span class="text-muted text-xs">${doc.roles_count || 0} roles</span>
                            ${autoDetected}
                        </div>
                    </div>
                    <div class="doc-tag-fields">
                        <select class="doc-tag-function" data-doc-id="${doc.id}" onchange="TWR.FunctionTags.updateDocumentTag(${doc.id}, 'function_code', this.value)">
                            <option value="">-- Function --</option>
                            ${funcOptions}
                        </select>
                        <select class="doc-tag-type" data-doc-id="${doc.id}" onchange="TWR.FunctionTags.updateDocumentTag(${doc.id}, 'category_type', this.value)">
                            <option value="">-- Type --</option>
                            ${typeOptions.replace(`value="${typeSelected}"`, `value="${typeSelected}" selected`)}
                        </select>
                        <input type="text" class="doc-tag-owner" data-doc-id="${doc.id}"
                               value="${escapeHtml(owner)}" placeholder="Owner..."
                               onchange="TWR.FunctionTags.updateDocumentTag(${doc.id}, 'document_owner', this.value)">
                        <button class="btn btn-ghost btn-xs btn-auto-detect" onclick="TWR.FunctionTags.autoDetectTag(${doc.id})" title="Auto-detect from filename">
                            <i data-lucide="wand-2"></i>
                        </button>
                        ${hasTag ? `<button class="btn btn-ghost btn-xs btn-danger" onclick="TWR.FunctionTags.removeDocumentTag(${doc.id})" title="Remove tag">
                            <i data-lucide="x"></i>
                        </button>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    async function updateDocumentTag(documentId, field, value) {
        const toast = getToast();
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

            // Find document data
            const doc = _documentTagsData.find(d => d.id === documentId);
            if (!doc) return;

            // Build update payload
            const payload = {
                document_id: documentId,
                document_name: doc.filename,
                function_code: doc.function_code || null,
                category_type: doc.category_type || null,
                document_owner: doc.document_owner || null,
                [field]: value || null
            };

            const res = await fetch('/api/document-categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.success) {
                // Update local data
                doc[field] = value;
                toast('success', 'Document tag updated');
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to update tag'));
            }
        } catch (e) {
            toast('error', 'Error updating tag: ' + e.message);
        }
    }

    async function removeDocumentTag(documentId) {
        const toast = getToast();
        const doc = _documentTagsData.find(d => d.id === documentId);
        if (!doc) return;

        if (!confirm(`Remove all tags from "${doc.filename}"?`)) {
            return;
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const encodedName = encodeURIComponent(doc.filename);

            const res = await fetch(`/api/document-categories/by-document/${encodedName}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': csrfToken }
            });

            const data = await res.json();
            if (data.success) {
                // Clear local data
                doc.function_code = null;
                doc.category_type = null;
                doc.document_owner = null;
                doc.auto_detected = false;

                // Re-render
                const searchInput = document.getElementById('doc-tags-search');
                renderDocumentTagsList(searchInput?.value || '');
                toast('success', data.message || 'Tag removed');

                // Refresh icons
                if (typeof lucide !== 'undefined') {
                    try { lucide.createIcons(); } catch(e) {}
                }
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to remove tag'));
            }
        } catch (e) {
            toast('error', 'Error removing tag: ' + e.message);
        }
    }

    async function autoDetectTag(documentId) {
        const toast = getToast();
        const doc = _documentTagsData.find(d => d.id === documentId);
        if (!doc) return;

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

            const res = await fetch('/api/document-categories/auto-detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    document_name: doc.filename
                })
            });

            const data = await res.json();
            if (data.success && data.data.detected) {
                const detected = data.data;

                // Auto-apply detected values
                if (detected.function_code) {
                    await updateDocumentTag(documentId, 'function_code', detected.function_code);
                }
                if (detected.category_type) {
                    await updateDocumentTag(documentId, 'category_type', detected.category_type);
                }
                if (detected.document_owner) {
                    await updateDocumentTag(documentId, 'document_owner', detected.document_owner);
                }

                // Reload and re-render
                await loadDocumentTagsData();
                const searchInput = document.getElementById('doc-tags-search');
                renderDocumentTagsList(searchInput?.value || '');

                toast('success', `Detected: ${detected.function_name || detected.function_code || 'No function'}, ${detected.category_type || 'No type'}`);

                // Refresh icons
                if (typeof lucide !== 'undefined') {
                    try { lucide.createIcons(); } catch(e) {}
                }
            } else {
                toast('info', 'Could not auto-detect tags from filename');
            }
        } catch (e) {
            toast('error', 'Error auto-detecting: ' + e.message);
        }
    }

    async function autoDetectAllTags() {
        const toast = getToast();
        const untagged = _documentTagsData.filter(d => !d.function_code && !d.category_type);

        if (untagged.length === 0) {
            toast('info', 'All documents already have tags');
            return;
        }

        toast('info', `Auto-detecting tags for ${untagged.length} documents...`);

        let detected = 0;
        for (const doc of untagged) {
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
                const res = await fetch('/api/document-categories/auto-detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ document_name: doc.filename })
                });

                const data = await res.json();
                if (data.success && data.data.detected) {
                    const detectedData = data.data;

                    // Apply detected values
                    if (detectedData.function_code || detectedData.category_type) {
                        await fetch('/api/document-categories', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-Token': csrfToken
                            },
                            body: JSON.stringify({
                                document_id: doc.id,
                                document_name: doc.filename,
                                function_code: detectedData.function_code,
                                category_type: detectedData.category_type,
                                document_owner: detectedData.document_owner,
                                auto_detected: 1
                            })
                        });
                        detected++;
                    }
                }
            } catch (e) {
                console.warn('[FunctionTags] Auto-detect failed for:', doc.filename, e);
            }
        }

        // Reload and re-render
        await loadDocumentTagsData();
        const searchInput = document.getElementById('doc-tags-search');
        renderDocumentTagsList(searchInput?.value || '');

        toast('success', `Auto-detected tags for ${detected} of ${untagged.length} documents`);

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }

    // ============================================================
    // DOCUMENT TAG PROMPT (After Scan Completion)
    // ============================================================

    /**
     * Show a prompt to tag a document after scanning.
     * Called from processReviewResults when a new document is scanned.
     *
     * @param {Object} scanInfo - Scan info from backend
     * @param {string} filename - Document filename
     */
    async function showDocumentTagPrompt(scanInfo, filename) {
        const toast = getToast();
        const escapeHtml = getEscapeHtml();

        // Check if document already has tags
        if (scanInfo && scanInfo.document_id) {
            try {
                const res = await fetch(`/api/document-categories?document_id=${scanInfo.document_id}`);
                const data = await res.json();
                if (data.success && data.data.categories && data.data.categories.length > 0) {
                    // Already tagged, skip prompt
                    console.log('[FunctionTags] Document already tagged, skipping prompt');
                    return;
                }
            } catch (e) {
                console.warn('[FunctionTags] Error checking existing tags:', e);
            }
        }

        // Try auto-detection first
        let autoDetected = null;
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/document-categories/auto-detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ document_name: filename })
            });
            const data = await res.json();
            if (data.success && data.data.detected) {
                autoDetected = data.data;
            }
        } catch (e) {
            console.warn('[FunctionTags] Auto-detect error:', e);
        }

        // Ensure categories are loaded
        if (State.categories.length === 0) {
            await loadFunctionCategories();
        }

        // Build hierarchical function options
        const funcOptions = buildHierarchicalFunctionOptions(autoDetected?.function_code || '');

        const categoryTypes = ['Procedure', 'Work Instruction', 'Specification', 'Knowledgebase', 'Policy', 'Standard', 'Plan', 'Report', 'Drawing', 'Design Document', 'Other'];
        const typeOptions = categoryTypes.map(t =>
            `<option value="${escapeHtml(t)}" ${autoDetected?.category_type === t ? 'selected' : ''}>${escapeHtml(t)}</option>`
        ).join('');

        const detectedBadge = autoDetected ? '<span class="auto-detect-badge">Auto-detected</span>' : '';

        const modalHtml = `
            <div class="modal active" id="doc-tag-prompt-modal">
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h3><i data-lucide="tag"></i> Tag This Document</h3>
                        <button class="btn btn-ghost" onclick="document.getElementById('doc-tag-prompt-modal').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted mb-4">Categorize this document to help organize reports and track roles by function.</p>

                        <div class="doc-tag-prompt-filename mb-4">
                            <strong>${escapeHtml(filename)}</strong>
                            ${detectedBadge}
                        </div>

                        <div class="form-group mb-3">
                            <label class="form-label">Function Code</label>
                            <div class="input-with-action">
                                <select id="prompt-function-code" class="form-select">
                                    <option value="">-- Select Function --</option>
                                    ${funcOptions}
                                </select>
                                <button class="btn btn-ghost btn-sm" onclick="TWR.FunctionTags.showAddCategoryInline('prompt-function-code')" title="Add New Function">
                                    <i data-lucide="plus"></i>
                                </button>
                            </div>
                        </div>

                        <div class="form-group mb-3">
                            <label class="form-label">Document Type</label>
                            <div class="input-with-action">
                                <select id="prompt-category-type" class="form-select">
                                    <option value="">-- Select Type --</option>
                                    ${typeOptions}
                                </select>
                                <button class="btn btn-ghost btn-sm" onclick="TWR.FunctionTags.showAddTypeInline('prompt-category-type')" title="Add Custom Type">
                                    <i data-lucide="plus"></i>
                                </button>
                            </div>
                        </div>

                        <div class="form-group mb-3">
                            <label class="form-label">Document Owner (optional)</label>
                            <input type="text" id="prompt-doc-owner" class="form-input" placeholder="e.g., Engineering, Quality, Safety..." value="${escapeHtml(autoDetected?.document_owner || '')}">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="document.getElementById('doc-tag-prompt-modal').remove()">
                            Skip for Now
                        </button>
                        <button class="btn btn-primary" onclick="TWR.FunctionTags.saveDocumentTagFromPrompt(${scanInfo?.document_id || 'null'}, '${escapeHtml(filename).replace(/'/g, "\\'")}')">
                            <i data-lucide="check"></i> Save Tag
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Remove existing prompt if any
        document.getElementById('doc-tag-prompt-modal')?.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    /**
     * Save the document tag from the prompt modal
     */
    async function saveDocumentTagFromPrompt(documentId, filename) {
        const toast = getToast();

        const functionCode = document.getElementById('prompt-function-code')?.value;
        const categoryType = document.getElementById('prompt-category-type')?.value;
        const docOwner = document.getElementById('prompt-doc-owner')?.value.trim();

        if (!functionCode && !categoryType) {
            toast('warning', 'Please select at least a function or document type');
            return;
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const res = await fetch('/api/document-categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    document_id: documentId,
                    document_name: filename,
                    function_code: functionCode || null,
                    category_type: categoryType || null,
                    document_owner: docOwner || null,
                    auto_detected: 0,
                    assigned_by: 'user'
                })
            });

            const data = await res.json();
            if (data.success) {
                toast('success', 'Document tagged successfully');
                document.getElementById('doc-tag-prompt-modal')?.remove();
            } else {
                toast('error', extractErrorMessage(data.error, 'Failed to save tag'));
            }
        } catch (e) {
            toast('error', 'Error saving tag: ' + e.message);
        }
    }

    /**
     * Show inline input to add a new function category
     */
    function showAddCategoryInline(selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        const escapeHtml = getEscapeHtml();

        // Check if inline form already exists
        if (document.getElementById('inline-add-category-form')) {
            document.getElementById('inline-add-category-form').remove();
            return;
        }

        // Build parent options (top-level categories only)
        const topLevelCats = State.categories.filter(c => !c.parent_code);
        const parentOptions = topLevelCats.map(cat =>
            `<option value="${escapeHtml(cat.code)}">${escapeHtml(cat.code)} - ${escapeHtml(cat.name)}</option>`
        ).join('');

        const formHtml = `
            <div id="inline-add-category-form" class="inline-add-form mt-2">
                <div class="inline-add-form-header text-muted text-xs mb-2">Add New Function Category</div>
                <div class="input-row mb-2">
                    <input type="text" id="inline-new-code" class="form-input form-input-sm" placeholder="Code (e.g., X)" style="width: 80px;" maxlength="8">
                    <input type="text" id="inline-new-name" class="form-input form-input-sm" placeholder="Name (e.g., External)" style="flex: 1;">
                </div>
                <div class="input-row">
                    <select id="inline-new-parent" class="form-select-sm" style="flex: 1;">
                        <option value="">-- No Parent (Top-level) --</option>
                        ${parentOptions}
                    </select>
                    <button class="btn btn-primary btn-sm" onclick="TWR.FunctionTags.addCategoryInline('${selectId}')">
                        <i data-lucide="plus"></i> Add
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="document.getElementById('inline-add-category-form').remove()">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            </div>
        `;

        select.parentElement.insertAdjacentHTML('afterend', formHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        document.getElementById('inline-new-code').focus();
    }

    /**
     * Add a new function category from inline form
     */
    async function addCategoryInline(selectId) {
        const toast = getToast();
        const code = document.getElementById('inline-new-code')?.value.trim().toUpperCase();
        const name = document.getElementById('inline-new-name')?.value.trim();
        const parentCode = document.getElementById('inline-new-parent')?.value || null;

        if (!code || !name) {
            toast('warning', 'Please enter both code and name');
            return;
        }

        const success = await createFunctionCategory({
            code,
            name,
            parent_code: parentCode,
            is_active: true
        });

        if (success) {
            // Reload categories to get updated hierarchy
            await loadFunctionCategories();

            // Rebuild select with new hierarchical options
            const select = document.getElementById(selectId);
            if (select) {
                const currentOptions = buildHierarchicalFunctionOptions(code);
                select.innerHTML = `<option value="">-- Select Function --</option>${currentOptions}`;
            }

            document.getElementById('inline-add-category-form')?.remove();
            toast('success', `Function "${code} - ${name}" added${parentCode ? ` under ${parentCode}` : ''}`);
        }
    }

    /**
     * Show inline input to add a custom document type
     */
    function showAddTypeInline(selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        // Check if inline form already exists
        if (document.getElementById('inline-add-type-form')) {
            document.getElementById('inline-add-type-form').remove();
            return;
        }

        const formHtml = `
            <div id="inline-add-type-form" class="inline-add-form mt-2">
                <div class="input-row">
                    <input type="text" id="inline-new-type" class="form-input form-input-sm" placeholder="Custom type name..." style="flex: 1;">
                    <button class="btn btn-primary btn-sm" onclick="TWR.FunctionTags.addTypeInline('${selectId}')">Add</button>
                    <button class="btn btn-ghost btn-sm" onclick="document.getElementById('inline-add-type-form').remove()">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            </div>
        `;

        select.parentElement.insertAdjacentHTML('afterend', formHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();
        document.getElementById('inline-new-type').focus();
    }

    /**
     * Add a custom document type from inline form
     */
    function addTypeInline(selectId) {
        const toast = getToast();
        const typeName = document.getElementById('inline-new-type')?.value.trim();

        if (!typeName) {
            toast('warning', 'Please enter a type name');
            return;
        }

        // Add to select and select it
        const select = document.getElementById(selectId);
        if (select) {
            const option = document.createElement('option');
            option.value = typeName;
            option.textContent = typeName;
            option.selected = true;
            select.insertBefore(option, select.options[1]); // After "Select" option
            toast('success', `Added "${typeName}" as document type`);
        }
        document.getElementById('inline-add-type-form')?.remove();
    }

    // ============================================================
    // BATCH DOCUMENT TAGGING
    // ============================================================

    /**
     * Show batch tagging modal after batch review completes.
     * Allows user to review and tag all documents in the batch.
     *
     * @param {Array} documents - List of documents from batch review
     */
    async function showBatchTaggingModal(documents) {
        const toast = getToast();
        const escapeHtml = getEscapeHtml();

        if (!documents || documents.length === 0) {
            return;
        }

        // Ensure categories are loaded
        if (State.categories.length === 0) {
            await loadFunctionCategories();
        }

        // Try auto-detect for each document
        const docsWithDetection = await Promise.all(documents.map(async (doc) => {
            let detected = null;
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
                const res = await fetch('/api/document-categories/auto-detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ document_name: doc.filename })
                });
                const data = await res.json();
                if (data.success && data.data.detected) {
                    detected = data.data;
                }
            } catch (e) {
                console.warn('[FunctionTags] Auto-detect failed for:', doc.filename, e);
            }
            return { ...doc, detected };
        }));

        // Build hierarchical function options (for bulk actions)
        const bulkFuncOptions = buildHierarchicalFunctionOptions('');

        const categoryTypes = ['Procedure', 'Work Instruction', 'Specification', 'Knowledgebase', 'Policy', 'Standard', 'Plan', 'Report', 'Drawing', 'Design Document', 'Other'];
        const typeOptions = categoryTypes.map(t =>
            `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`
        ).join('');

        // Build document rows with hierarchical function options per document
        const rows = docsWithDetection.map((doc, index) => {
            const detected = doc.detected;
            const detectedBadge = detected ? '<span class="auto-detect-badge" title="Auto-detected">Auto</span>' : '';
            const docFuncOptions = buildHierarchicalFunctionOptions(detected?.function_code || '');

            return `
                <div class="batch-tag-row" data-index="${index}">
                    <div class="batch-tag-checkbox">
                        <input type="checkbox" id="batch-tag-include-${index}" checked>
                    </div>
                    <div class="batch-tag-name">
                        <strong>${escapeHtml(doc.filename)}</strong>
                        ${detectedBadge}
                    </div>
                    <div class="batch-tag-fields">
                        <select id="batch-func-${index}" class="form-select-sm">
                            <option value="">-- Function --</option>
                            ${docFuncOptions}
                        </select>
                        <select id="batch-type-${index}" class="form-select-sm">
                            <option value="">-- Type --</option>
                            ${typeOptions.replace(`value="${detected?.category_type}"`, `value="${detected?.category_type}" selected`)}
                        </select>
                    </div>
                </div>
            `;
        }).join('');

        const modalHtml = `
            <div class="modal active modal-lg" id="batch-tag-modal">
                <div class="modal-content" style="max-width: 800px; max-height: 85vh;">
                    <div class="modal-header">
                        <h3><i data-lucide="tags"></i> Tag Batch Documents</h3>
                        <button class="btn btn-ghost" onclick="document.getElementById('batch-tag-modal').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="overflow-y: auto;">
                        <p class="text-muted mb-4">Review and tag the documents from your batch scan. Uncheck documents you want to skip.</p>

                        <div class="batch-tag-header mb-2">
                            <div class="batch-tag-checkbox">
                                <input type="checkbox" id="batch-tag-select-all" checked onchange="TWR.FunctionTags.toggleBatchSelectAll(this.checked)">
                            </div>
                            <div class="batch-tag-name"><strong>Document</strong></div>
                            <div class="batch-tag-fields"><strong>Function / Type</strong></div>
                        </div>

                        <div id="batch-tag-list" class="batch-tag-list" style="max-height: 50vh; overflow-y: auto;">
                            ${rows}
                        </div>

                        <div class="batch-tag-bulk-actions mt-4">
                            <label class="form-label">Apply to All Selected:</label>
                            <div class="input-row">
                                <select id="batch-bulk-function" class="form-select-sm">
                                    <option value="">-- Function --</option>
                                    ${bulkFuncOptions}
                                </select>
                                <select id="batch-bulk-type" class="form-select-sm">
                                    <option value="">-- Type --</option>
                                    ${typeOptions}
                                </select>
                                <button class="btn btn-secondary btn-sm" onclick="TWR.FunctionTags.applyBulkTags()">Apply</button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="document.getElementById('batch-tag-modal').remove()">
                            Skip All
                        </button>
                        <button class="btn btn-primary" onclick="TWR.FunctionTags.saveBatchTags(${JSON.stringify(docsWithDetection).replace(/"/g, '&quot;')})">
                            <i data-lucide="check"></i> Save Tags
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('batch-tag-modal')?.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function toggleBatchSelectAll(checked) {
        document.querySelectorAll('#batch-tag-list input[type="checkbox"]').forEach(cb => {
            cb.checked = checked;
        });
    }

    function applyBulkTags() {
        const bulkFunc = document.getElementById('batch-bulk-function')?.value;
        const bulkType = document.getElementById('batch-bulk-type')?.value;

        document.querySelectorAll('.batch-tag-row').forEach((row) => {
            const index = row.dataset.index;
            const checkbox = document.getElementById(`batch-tag-include-${index}`);
            if (checkbox?.checked) {
                if (bulkFunc) {
                    const funcSelect = document.getElementById(`batch-func-${index}`);
                    if (funcSelect) funcSelect.value = bulkFunc;
                }
                if (bulkType) {
                    const typeSelect = document.getElementById(`batch-type-${index}`);
                    if (typeSelect) typeSelect.value = bulkType;
                }
            }
        });

        const toast = getToast();
        toast('success', 'Bulk tags applied to selected documents');
    }

    async function saveBatchTags(documents) {
        const toast = getToast();
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

        let saved = 0;
        let skipped = 0;

        for (let i = 0; i < documents.length; i++) {
            const checkbox = document.getElementById(`batch-tag-include-${i}`);
            if (!checkbox?.checked) {
                skipped++;
                continue;
            }

            const funcCode = document.getElementById(`batch-func-${i}`)?.value;
            const catType = document.getElementById(`batch-type-${i}`)?.value;

            if (!funcCode && !catType) {
                skipped++;
                continue;
            }

            try {
                await fetch('/api/document-categories', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({
                        document_id: documents[i].document_id || documents[i].id,
                        document_name: documents[i].filename,
                        function_code: funcCode || null,
                        category_type: catType || null,
                        auto_detected: 0,
                        assigned_by: 'user'
                    })
                });
                saved++;
            } catch (e) {
                console.warn('[FunctionTags] Failed to save tag for:', documents[i].filename, e);
            }
        }

        document.getElementById('batch-tag-modal')?.remove();
        toast('success', `Tagged ${saved} documents, skipped ${skipped}`);
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================

    async function init() {
        console.log('[FunctionTags] Initializing...');
        await loadFunctionCategories();
        State.loaded = true;
        console.log('[FunctionTags] Initialized with', State.categories.length, 'categories');
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    return {
        // State access
        getState: () => State,
        getCategories: () => State.categories,

        // Categories
        loadFunctionCategories,
        createFunctionCategory,
        updateFunctionCategory,
        deleteFunctionCategory,

        // Role tags
        loadRoleFunctionTags,
        assignRoleFunctionTag,
        removeRoleFunctionTag,

        // Document categories
        loadDocumentCategories,
        autoDetectDocumentCategory,
        assignDocumentCategory,

        // Role actions
        loadRoleRequiredActions,
        extractRoleActionsFromDocument,
        addRoleRequiredAction,
        verifyRoleRequiredAction,
        deleteRoleRequiredAction,

        // Reports
        downloadReport,
        downloadReportWithFilters,
        _toggleFuncPicker,
        _selectFunction,
        _toggleFuncGroup,
        _toggleFuncCheck,
        _clearFuncSelection,
        _selectOwner,

        // UI
        renderFunctionCategorySelect,
        renderFunctionTagBadges,
        renderRoleRequiredActionsPanel,
        showFunctionTagsModal,
        showReportsModal,
        showDocumentTagsModal,
        updateDocumentTag,
        removeDocumentTag,
        autoDetectTag,
        autoDetectAllTags,
        showAddCategoryForm,
        showEditCategoryForm,
        submitCategoryForm,
        renderFunctionCategoriesList,
        toggleTreeItem,
        buildHierarchicalFunctionOptions,
        setViewMode,
        toggleMindMapNode,
        renderMindMapView,

        // Document tag prompts
        showDocumentTagPrompt,
        saveDocumentTagFromPrompt,
        showAddCategoryInline,
        addCategoryInline,
        showAddTypeInline,
        addTypeInline,

        // Batch tagging
        showBatchTaggingModal,
        toggleBatchSelectAll,
        applyBulkTags,
        saveBatchTags,

        // Init
        init
    };
})();
