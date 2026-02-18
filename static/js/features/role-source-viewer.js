/**
 * AEGIS - Role Source Viewer
 * =====================================
 * ENH-005: Review mode for viewing role source context in documents.
 *
 * Features:
 * - Split-panel design matching Statement Review Mode
 * - Left panel: Source document with highlighted role mentions
 * - Right panel: Role details, variants, and statistics
 * - Multi-document navigation with dropdown selector
 * - Per-document mention navigation (Previous/Next)
 * - Keyboard shortcuts for navigation
 * - Actual document text display with context highlighting
 * - Full adjudication panel with Confirm/Deliverable/Reject actions
 * - Per-role adjudication state persistence via API
 * - Integration with Role Dictionary for extraction improvement
 *
 * Version: 3.2.2
 * Date: 2026-02-03
 */

'use strict';

window.TWR = window.TWR || {};

TWR.RoleSourceViewer = (function() {
    const VERSION = '3.2.2';
    const LOG_PREFIX = '[TWR RoleSourceViewer]';
    const CONTEXT_CHARS = 400; // Characters of context before/after each mention

    // ============================================================
    // STATE
    // ============================================================

    const State = {
        isOpen: false,
        currentRole: null,
        documents: [],
        currentDocIndex: 0,
        currentMentionIndex: 0,
        mentionsInCurrentDoc: [],
        modal: null,
        roleData: null,
        documentText: '', // Full document text for display
        highlightedText: '', // Document text with highlights
        documentTextCache: {} // v4.5.2: Per-document text cache keyed by filename
    };

    // ============================================================
    // UTILITY FUNCTIONS
    // ============================================================

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Find all occurrences of a role in document text with surrounding context.
     */
    function findRoleInText(text, roleName) {
        if (!text || !roleName) return [];

        const occurrences = [];
        const regex = new RegExp(escapeRegex(roleName), 'gi');
        let match;

        while ((match = regex.exec(text)) !== null) {
            const startIndex = match.index;
            const endIndex = startIndex + match[0].length;

            // Get context before
            const contextStart = Math.max(0, startIndex - CONTEXT_CHARS);
            let contextBefore = text.substring(contextStart, startIndex);
            if (contextStart > 0) {
                // Find word boundary for cleaner display
                const firstSpace = contextBefore.indexOf(' ');
                if (firstSpace > 0) {
                    contextBefore = '...' + contextBefore.substring(firstSpace + 1);
                }
            }

            // Get context after
            const contextEnd = Math.min(text.length, endIndex + CONTEXT_CHARS);
            let contextAfter = text.substring(endIndex, contextEnd);
            if (contextEnd < text.length) {
                const lastSpace = contextAfter.lastIndexOf(' ');
                if (lastSpace > 0) {
                    contextAfter = contextAfter.substring(0, lastSpace) + '...';
                }
            }

            occurrences.push({
                matchedText: match[0],
                contextBefore: contextBefore,
                contextAfter: contextAfter,
                startIndex: startIndex,
                endIndex: endIndex,
                lineNumber: (text.substring(0, startIndex).match(/\n/g) || []).length + 1
            });
        }

        return occurrences;
    }

    // ============================================================
    // DATA RETRIEVAL
    // ============================================================

    /**
     * Get role data from in-memory State (current document).
     */
    function getRoleDataFromState(roleName) {
        const AppState = window.TWR?.State?.State || window.State;

        if (!AppState || !AppState.roles || Object.keys(AppState.roles).length === 0) {
            return null;
        }

        const roleNameLower = roleName.toLowerCase();
        let roleData = null;
        let canonicalName = roleName;

        for (const [name, data] of Object.entries(AppState.roles)) {
            if (name.toLowerCase() === roleNameLower) {
                roleData = data;
                canonicalName = name;
                break;
            }
            if (data.variants) {
                const variants = Array.isArray(data.variants) ? data.variants : Object.keys(data.variants);
                for (const variant of variants) {
                    if (variant.toLowerCase() === roleNameLower) {
                        roleData = data;
                        canonicalName = name;
                        break;
                    }
                }
            }
        }

        if (!roleData) return null;

        // Get document text to find actual occurrences
        const documentText = AppState.currentText || '';
        const documentName = AppState.filename || AppState.currentFilename || 'Current Document';

        if (documentText) {
            const textOccurrences = findRoleInText(documentText, canonicalName);
            if (textOccurrences.length > 0) {
                const occurrencesByDoc = {};
                occurrencesByDoc[documentName] = textOccurrences;

                return {
                    name: canonicalName,
                    variants: roleData.variants || [],
                    responsibilities: roleData.responsibilities || [],
                    frequency: textOccurrences.length,
                    documents: [documentName],
                    occurrencesByDoc: occurrencesByDoc,
                    hasRealContext: true
                };
            }
        }

        return null;
    }

    /**
     * Fetch role context data from the API.
     */
    async function fetchRoleDataFromAPI(roleName) {
        try {
            console.log(LOG_PREFIX, `Fetching role context from API for: ${roleName}`);

            // Try dedicated context endpoint first
            let response = await fetch(`/api/roles/context?role=${encodeURIComponent(roleName)}`);

            if (response.ok) {
                const data = await response.json();
                // v5.0.5: Accept roles with documents even if occurrences (responsibility text) are empty
                if (data && data.role_name && ((data.occurrences && data.occurrences.length > 0) || (data.documents && data.documents.length > 0))) {
                    return transformContextResponse(data, roleName);
                }
            }

            // Fallback to aggregated endpoint
            console.log(LOG_PREFIX, 'Trying aggregated endpoint...');
            response = await fetch('/api/roles/aggregated');

            if (!response.ok) {
                console.warn(LOG_PREFIX, `Aggregated API returned ${response.status}`);
                return null;
            }

            const data = await response.json();
            if (!data || !data.success || !data.data) {
                return null;
            }

            const roleNameLower = roleName.toLowerCase();
            const roleEntry = data.data.find(r =>
                r.role_name?.toLowerCase() === roleNameLower ||
                r.normalized_name?.toLowerCase() === roleNameLower
            );

            if (!roleEntry) {
                console.warn(LOG_PREFIX, `Role "${roleName}" not found`);
                return null;
            }

            return await fetchDocumentContexts(roleEntry);

        } catch (error) {
            console.error(LOG_PREFIX, 'Error fetching role data:', error);
            return null;
        }
    }

    /**
     * Fetch document texts and find role occurrences.
     * v3.1.10: Enhanced to try partial matches and show stored context when exact match fails.
     */
    async function fetchDocumentContexts(roleData) {
        const occurrencesByDoc = {};
        const roleName = roleData.role_name;

        // Get stored sample contexts if available
        const storedContexts = roleData.sample_contexts || [];

        if (roleData.documents && roleData.documents.length > 0) {
            for (const docName of roleData.documents) {
                try {
                    const response = await fetch(`/api/scan-history/document-text?filename=${encodeURIComponent(docName)}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success && data.text) {
                            // Try exact match first
                            let textOccurrences = findRoleInText(data.text, roleName);

                            // If no exact match, try case-insensitive word boundary match
                            if (textOccurrences.length === 0) {
                                // Try searching for key words from the role name
                                const words = roleName.split(/\s+/).filter(w => w.length > 3);
                                if (words.length >= 2) {
                                    // Search for the most specific word
                                    const searchWord = words.sort((a, b) => b.length - a.length)[0];
                                    textOccurrences = findRoleInText(data.text, searchWord);
                                    // Mark these as partial matches
                                    textOccurrences.forEach(occ => occ.partialMatch = true);
                                }
                            }

                            if (textOccurrences.length > 0) {
                                occurrencesByDoc[docName] = textOccurrences;
                                continue;
                            }
                        }
                    }
                } catch (e) {
                    console.log(LOG_PREFIX, `Could not fetch text for ${docName}:`, e);
                }

                // v4.6.1 Fix 7: Skip documents where role text isn't actually found
                // instead of creating misleading placeholder entries
                continue;
            }
        }

        return {
            name: roleName,
            variants: roleData.aliases || [],
            responsibilities: roleData.responsibilities || [],
            frequency: roleData.total_mentions || roleData.document_count || 1,
            // v4.6.1: Only include documents where we actually found the role in text
            documents: Object.keys(occurrencesByDoc),
            occurrencesByDoc: occurrencesByDoc,
            hasRealContext: Object.keys(occurrencesByDoc).length > 0,
            storedContexts: storedContexts
        };
    }

    /**
     * Transform context API response to internal format.
     */
    function transformContextResponse(data, roleName) {
        const occurrencesByDoc = {};

        if (data.occurrences && Array.isArray(data.occurrences)) {
            for (const occ of data.occurrences) {
                const docName = occ.document || occ.location || 'Unknown Document';
                if (!occurrencesByDoc[docName]) {
                    occurrencesByDoc[docName] = [];
                }

                occurrencesByDoc[docName].push({
                    matchedText: roleName,
                    contextBefore: occ.context_before || '',
                    contextAfter: occ.context_after || '',
                    startIndex: 0,
                    endIndex: roleName.length,
                    lineNumber: occ.line || 0,
                    responsibility: occ.responsibility || '',
                    section: occ.section || ''
                });
            }
        }

        // v5.0.5: Use data.documents as fallback when occurrencesByDoc is empty
        // (roles may have documents in DB but no extracted responsibility text)
        const docKeys = Object.keys(occurrencesByDoc);
        const documentsList = docKeys.length > 0 ? docKeys : (data.documents || []);

        return {
            name: data.role_name,
            variants: data.aliases || data.variants || [],
            responsibilities: data.responsibilities || [],
            frequency: data.total_mentions || Object.values(occurrencesByDoc).reduce((sum, arr) => sum + arr.length, 0),
            documents: documentsList,
            occurrencesByDoc: occurrencesByDoc,
            hasRealContext: docKeys.length > 0
        };
    }

    // ============================================================
    // MODAL CREATION
    // ============================================================

    function createModal() {
        if (State.modal) return State.modal;

        const modal = document.createElement('div');
        modal.id = 'role-source-review-modal';
        modal.className = 'rsv-modal';
        modal.innerHTML = `
            <div class="rsv-overlay"></div>
            <div class="rsv-container">
                <div class="rsv-header">
                    <h2>Role Source Viewer</h2>
                    <div class="rsv-nav">
                        <button class="rsv-btn rsv-prev-mention" title="Previous Mention">
                            <span class="arrow">&larr;</span> Previous
                        </button>
                        <span class="rsv-counter">
                            Mention <span class="current">0</span> of <span class="total">0</span>
                        </span>
                        <button class="rsv-btn rsv-next-mention" title="Next Mention">
                            Next <span class="arrow">&rarr;</span>
                        </button>
                    </div>
                    <button class="rsv-close" title="Close (Esc)">&times;</button>
                </div>

                <div class="rsv-body">
                    <!-- Left Panel: Document Source -->
                    <div class="rsv-source-panel">
                        <div class="rsv-source-header">
                            <h3>Source Document</h3>
                            <div class="rsv-doc-selector-wrap">
                                <select class="rsv-doc-selector"></select>
                            </div>
                        </div>
                        <div class="rsv-source-info">
                            <span class="rsv-doc-name"></span>
                            <span class="rsv-line-info"></span>
                        </div>
                        <div class="rsv-source-content">
                            <div class="rsv-document-text"></div>
                        </div>
                        <div class="rsv-source-actions">
                            <span class="rsv-context-status"></span>
                        </div>
                    </div>

                    <!-- Right Panel: Role Details & Adjudication -->
                    <div class="rsv-details-panel">
                        <div class="rsv-details-header">
                            <h3>Role Details</h3>
                            <div class="rsv-role-badge" title="Click to rename this role" style="cursor:pointer;">
                                <span class="rsv-role-name"></span>
                                <svg class="rsv-role-edit-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-left:6px;opacity:0.6;flex-shrink:0;"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                            </div>
                            <div class="rsv-role-rename-row" style="display:none;">
                                <input type="text" class="rsv-role-rename-input" placeholder="New role name..." />
                                <button class="rsv-role-rename-save" title="Save new name">Save</button>
                                <button class="rsv-role-rename-cancel" title="Cancel">Cancel</button>
                            </div>
                        </div>

                        <div class="rsv-details-content">
                            <!-- Adjudication Section -->
                            <div class="rsv-adjudication-section">
                                <label>Adjudication</label>
                                <div class="rsv-status-indicator">
                                    <span class="rsv-status-badge" data-status="pending">Pending Review</span>
                                </div>
                                <div class="rsv-adjudication-actions">
                                    <button class="rsv-adj-btn rsv-adj-confirm" title="Confirm as valid role">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>
                                        Confirm Role
                                    </button>
                                    <button class="rsv-adj-btn rsv-adj-deliverable" title="Mark as deliverable (artifact/output)">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
                                        Mark Deliverable
                                    </button>
                                    <button class="rsv-adj-btn rsv-adj-reject" title="Reject - not a valid role">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                                        Reject
                                    </button>
                                </div>

                                <!-- Category Selection -->
                                <div class="rsv-category-section">
                                    <label>Category</label>
                                    <select class="rsv-category-select">
                                        <option value="Role">Role</option>
                                        <option value="Management">Management</option>
                                        <option value="Technical">Technical</option>
                                        <option value="Organization">Organization</option>
                                        <option value="Governance">Governance</option>
                                        <option value="Engineering">Engineering</option>
                                        <option value="Quality">Quality</option>
                                        <option value="Safety">Safety</option>
                                        <option value="Operations">Operations</option>
                                        <option value="Support">Support</option>
                                        <option value="Compliance">Compliance</option>
                                        <option value="Procurement">Procurement</option>
                                        <option value="Deliverable">Deliverable</option>
                                        <option value="__custom__">+ Add Custom...</option>
                                    </select>
                                    <input type="text" class="rsv-category-custom-input" placeholder="Type custom category..." style="display:none;" />
                                </div>

                                <!-- Notes -->
                                <div class="rsv-notes-section">
                                    <label>Notes</label>
                                    <textarea class="rsv-notes-input" placeholder="Add notes about this role..."></textarea>
                                </div>

                                <!-- Function Tags -->
                                <div class="rsv-tags-section">
                                    <label>Function Tags</label>
                                    <div class="rsv-tags-container">
                                        <div class="rsv-tag-pills" id="rsv-tag-pills"></div>
                                        <button class="rsv-add-tag-btn" id="rsv-add-tag-btn" title="Add function tag">
                                            <i data-lucide="tag" style="width:13px;height:13px;"></i> Add Tag
                                        </button>
                                    </div>
                                    <div class="rsv-tag-dropdown-anchor" id="rsv-tag-dropdown-anchor" style="position:relative;"></div>
                                </div>
                            </div>

                            <div class="rsv-divider"></div>

                            <div class="rsv-detail-section">
                                <label title="Number of times this exact role name appears in the document text">Text Occurrences</label>
                                <div class="rsv-detail-value rsv-frequency"></div>
                            </div>

                            <div class="rsv-detail-section">
                                <label>Found in Documents</label>
                                <div class="rsv-detail-value rsv-doc-count"></div>
                            </div>

                            <div class="rsv-detail-section rsv-variants-section">
                                <label>Also Known As</label>
                                <div class="rsv-detail-value rsv-variants"></div>
                            </div>

                            <div class="rsv-detail-section rsv-responsibilities-section">
                                <label>Responsibilities</label>
                                <div class="rsv-detail-value rsv-responsibilities"></div>
                            </div>

                            <div class="rsv-detail-section">
                                <label>All Documents</label>
                                <div class="rsv-doc-list"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="rsv-footer">
                    <div class="rsv-shortcuts">
                        <span><kbd>&larr;</kbd> Previous</span>
                        <span><kbd>&rarr;</kbd> Next</span>
                        <span><kbd>Shift+&larr;</kbd> Prev Doc</span>
                        <span><kbd>Shift+&rarr;</kbd> Next Doc</span>
                        <span><kbd>Esc</kbd> Close</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;

        attachEventListeners(modal);

        return modal;
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    function attachEventListeners(modal) {
        modal.querySelector('.rsv-close').addEventListener('click', close);
        modal.querySelector('.rsv-overlay').addEventListener('click', close);

        modal.querySelector('.rsv-prev-mention').addEventListener('click', previousMention);
        modal.querySelector('.rsv-next-mention').addEventListener('click', nextMention);

        modal.querySelector('.rsv-doc-selector').addEventListener('change', (e) => {
            State.currentDocIndex = parseInt(e.target.value, 10);
            State.currentMentionIndex = 0;
            updateMentionsForCurrentDoc();
            updateUI();
        });

        // Role rename handlers
        const roleBadge = modal.querySelector('.rsv-role-badge');
        const renameRow = modal.querySelector('.rsv-role-rename-row');
        const renameInput = modal.querySelector('.rsv-role-rename-input');
        const renameSave = modal.querySelector('.rsv-role-rename-save');
        const renameCancel = modal.querySelector('.rsv-role-rename-cancel');

        if (roleBadge && renameRow) {
            roleBadge.addEventListener('click', () => {
                renameInput.value = State.roleData?.name || '';
                roleBadge.style.display = 'none';
                renameRow.style.display = 'flex';
                renameInput.focus();
                renameInput.select();
            });
            renameCancel.addEventListener('click', () => {
                renameRow.style.display = 'none';
                roleBadge.style.display = 'flex';
            });
            renameSave.addEventListener('click', () => handleRoleRename());
            renameInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); handleRoleRename(); }
                if (e.key === 'Escape') { renameRow.style.display = 'none'; roleBadge.style.display = 'flex'; }
            });
        }

        // Adjudication button handlers
        modal.querySelector('.rsv-adj-confirm').addEventListener('click', () => handleAdjudication('confirmed'));
        modal.querySelector('.rsv-adj-deliverable').addEventListener('click', () => handleAdjudication('deliverable'));
        modal.querySelector('.rsv-adj-reject').addEventListener('click', () => handleAdjudication('rejected'));

        // Category change handler (with custom input support)
        const catSelect = modal.querySelector('.rsv-category-select');
        const catCustomInput = modal.querySelector('.rsv-category-custom-input');
        catSelect.addEventListener('change', (e) => {
            if (e.target.value === '__custom__') {
                catCustomInput.style.display = 'block';
                catCustomInput.value = '';
                catCustomInput.focus();
            } else {
                catCustomInput.style.display = 'none';
                handleCategoryChange(e.target.value);
            }
        });
        if (catCustomInput) {
            catCustomInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const val = catCustomInput.value.trim();
                    if (val) {
                        // Add the custom category to the dropdown for future use
                        const existing = catSelect.querySelector(`option[value="${val}"]`);
                        if (!existing) {
                            const opt = document.createElement('option');
                            opt.value = val;
                            opt.textContent = val;
                            catSelect.insertBefore(opt, catSelect.querySelector('option[value="__custom__"]'));
                        }
                        catSelect.value = val;
                        catCustomInput.style.display = 'none';
                        handleCategoryChange(val);
                    }
                }
                if (e.key === 'Escape') {
                    catCustomInput.style.display = 'none';
                    catSelect.value = 'Role';
                }
            });
            catCustomInput.addEventListener('blur', () => {
                const val = catCustomInput.value.trim();
                if (val) {
                    const existing = catSelect.querySelector(`option[value="${val}"]`);
                    if (!existing) {
                        const opt = document.createElement('option');
                        opt.value = val;
                        opt.textContent = val;
                        catSelect.insertBefore(opt, catSelect.querySelector('option[value="__custom__"]'));
                    }
                    catSelect.value = val;
                    handleCategoryChange(val);
                }
                catCustomInput.style.display = 'none';
            });
        }

        // Function tag add button
        const addTagBtn = modal.querySelector('#rsv-add-tag-btn');
        if (addTagBtn) {
            addTagBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showRsvTagDropdown();
            });
        }

        document.addEventListener('keydown', handleKeydown);
    }

    // ============================================================
    // ROLE RENAME
    // ============================================================

    /**
     * Handle renaming the current role via the rename input.
     */
    async function handleRoleRename() {
        const renameInput = State.modal?.querySelector('.rsv-role-rename-input');
        const renameRow = State.modal?.querySelector('.rsv-role-rename-row');
        const roleBadge = State.modal?.querySelector('.rsv-role-badge');
        const roleNameEl = State.modal?.querySelector('.rsv-role-name');
        if (!renameInput || !State.roleData?.name) return;

        const newName = renameInput.value.trim();
        const oldName = State.roleData.name;

        if (!newName || newName === oldName) {
            renameRow.style.display = 'none';
            roleBadge.style.display = 'flex';
            return;
        }

        try {
            const resp = await fetch('/api/roles/rename', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify({ old_name: oldName, new_name: newName })
            });
            const data = await resp.json();

            if (data.success) {
                // Update local state
                State.roleData.name = newName;
                roleNameEl.textContent = newName;
                renameRow.style.display = 'none';
                roleBadge.style.display = 'flex';

                if (typeof showToast === 'function') {
                    showToast('success', `Role renamed: "${oldName}" → "${newName}"`);
                }
                console.log(LOG_PREFIX, `Renamed role: "${oldName}" → "${newName}"`);
            } else {
                if (typeof showToast === 'function') {
                    showToast('error', data.error || 'Rename failed');
                }
            }
        } catch (e) {
            console.error(LOG_PREFIX, 'Rename error:', e);
            if (typeof showToast === 'function') {
                showToast('error', 'Rename failed: ' + e.message);
            }
        }
    }

    // ============================================================
    // ADJUDICATION FUNCTIONS
    // ============================================================

    /**
     * Handle adjudication action for the current role.
     */
    async function handleAdjudication(action) {
        if (!State.roleData || !State.roleData.name) {
            console.warn(LOG_PREFIX, 'No role data to adjudicate');
            return;
        }

        const roleName = State.roleData.name;
        const notes = State.modal.querySelector('.rsv-notes-input')?.value || '';
        const category = State.modal.querySelector('.rsv-category-select')?.value || 'Role';

        console.log(LOG_PREFIX, `Adjudicating role "${roleName}" as ${action}`);

        // Update UI immediately for feedback
        updateStatusBadge(action);
        updateAdjudicationButtons(action);

        let apiSuccess = false;

        try {
            // Call the API to save adjudication to role dictionary
            const response = await fetch('/api/roles/adjudicate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify({
                    role_name: roleName,
                    action: action,
                    category: category,
                    notes: notes,
                    is_deliverable: action === 'deliverable'
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log(LOG_PREFIX, `Role "${roleName}" saved to dictionary as ${action}`, data);
                    apiSuccess = true;
                } else {
                    console.warn(LOG_PREFIX, 'API returned error:', data.error);
                }
            } else {
                console.warn(LOG_PREFIX, 'API response not OK:', response.status);
            }
        } catch (error) {
            console.warn(LOG_PREFIX, 'Adjudication API error:', error);
        }

        // Always sync with Roles Studio adjudication system (updates in-memory state and UI)
        syncWithRolesAdjudication(roleName, action);

        // Show appropriate toast message
        const actionLabel = action === 'confirmed' ? 'confirmed and added to dictionary' :
                           action === 'deliverable' ? 'marked as deliverable and added to dictionary' :
                           'rejected and added to exclusion list';

        if (apiSuccess) {
            showToast(`Role "${roleName}" ${actionLabel}`, 'success');
        } else {
            // If API failed, also try the roles.js dictionary endpoint as backup
            try {
                await addRoleToDictionaryBackup(roleName, action, category, notes);
                showToast(`Role "${roleName}" ${actionLabel}`, 'success');
            } catch (e) {
                console.warn(LOG_PREFIX, 'Backup dictionary save also failed:', e);
                showToast(`Role "${roleName}" adjudicated (local only)`, 'info');
            }
        }
    }

    /**
     * Backup method to add role to dictionary via the roles.js endpoint.
     */
    async function addRoleToDictionaryBackup(roleName, action, category, notes) {
        const State = window.TWR?.State?.State || window.State;
        const response = await fetch('/api/roles/dictionary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.CSRF_TOKEN || State?.csrfToken || getCSRFToken()
            },
            body: JSON.stringify({
                role_name: roleName,
                source: 'adjudication',
                source_document: State?.filename || '',
                is_deliverable: action === 'deliverable',
                is_active: action !== 'rejected',
                category: category || (action === 'deliverable' ? 'Deliverable' : 'Role'),
                notes: notes || `Adjudicated as ${action} on ${new Date().toLocaleDateString()}`
            })
        });

        if (!response.ok) {
            throw new Error(`Dictionary API returned ${response.status}`);
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to add to dictionary');
        }

        console.log(LOG_PREFIX, `Backup: Added "${roleName}" to dictionary via /api/roles/dictionary`);
        return data;
    }

    /**
     * Sync adjudication with the Roles Studio system (TWR.Roles).
     * This directly updates the AdjudicationState.decisions map and refreshes the UI.
     *
     * Key behavior:
     * - Updates the in-memory AdjudicationState.decisions Map
     * - Triggers renderAdjudicationList() which filters based on current filter
     * - Default filter is "pending", so adjudicated items disappear from list
     * - Updates stats counters and graph visualization
     */
    function syncWithRolesAdjudication(roleName, action) {
        try {
            // Directly update the AdjudicationState if available
            const AdjudicationState = window.TWR?.Roles?.AdjudicationState;
            if (AdjudicationState && AdjudicationState.decisions) {
                const decision = AdjudicationState.decisions.get(roleName);
                if (decision) {
                    // Update existing decision - set directly, don't toggle
                    decision.status = action;
                    console.log(LOG_PREFIX, `Updated AdjudicationState for "${roleName}" to "${action}"`);
                } else {
                    // Create new decision entry
                    AdjudicationState.decisions.set(roleName, {
                        status: action,
                        originalName: roleName,
                        editedName: roleName,
                        suggestedType: action === 'deliverable' ? 'deliverable' : 'role',
                        confidence: 1.0, // High confidence since user explicitly adjudicated
                        notes: '',
                        contexts: []
                    });
                    console.log(LOG_PREFIX, `Created AdjudicationState entry for "${roleName}" with status "${action}"`);
                }
            } else {
                console.log(LOG_PREFIX, 'AdjudicationState not available - Roles Studio may not be loaded');
            }

            // Get the global State object
            const State = window.TWR?.State?.State || window.State;

            // Update State.adjudicatedRoles for graph and other visualizations
            if (State && AdjudicationState && AdjudicationState.decisions) {
                const confirmed = [], deliverables = [], rejected = [];
                AdjudicationState.decisions.forEach((dec, name) => {
                    switch (dec.status) {
                        case 'confirmed': confirmed.push(name); break;
                        case 'deliverable': deliverables.push(name); break;
                        case 'rejected': rejected.push(name); break;
                    }
                });
                State.adjudicatedRoles = { confirmed, deliverables, rejected, timestamp: new Date().toISOString() };
                console.log(LOG_PREFIX, `Updated State.adjudicatedRoles: ${confirmed.length} confirmed, ${deliverables.length} deliverables, ${rejected.length} rejected`);
            }

            // Refresh the adjudication list - this will filter out non-pending items if filter is "pending"
            if (window.TWR?.Roles?.renderAdjudicationList) {
                console.log(LOG_PREFIX, 'Refreshing adjudication list...');
                window.TWR.Roles.renderAdjudicationList();
            }

            // Update the stats counters
            if (window.TWR?.Roles?.updateAdjudicationStats) {
                window.TWR.Roles.updateAdjudicationStats();
            }

            // Update graph visualization with new adjudication status
            if (window.TWR?.Roles?.updateGraphWithAdjudication) {
                window.TWR.Roles.updateGraphWithAdjudication();
            }

            console.log(LOG_PREFIX, 'Synced adjudication with Roles Studio successfully');
        } catch (e) {
            console.warn(LOG_PREFIX, 'Could not sync with Roles module:', e);
        }
    }

    /**
     * Handle category change for the current role.
     */
    async function handleCategoryChange(category) {
        if (!State.roleData || !State.roleData.name) return;

        console.log(LOG_PREFIX, `Changing category to "${category}" for role "${State.roleData.name}"`);

        try {
            const response = await fetch('/api/roles/update-category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify({
                    role_name: State.roleData.name,
                    category: category
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    showToast(`Category updated to "${category}"`, 'success');
                }
            }
        } catch (error) {
            console.log(LOG_PREFIX, 'Category update error:', error);
            showToast('Failed to update category', 'error');
        }
    }

    // ============================================================
    // FUNCTION TAG MANAGEMENT (v4.0.3)
    // ============================================================

    /** Cache of function categories for the dropdown */
    let _rsvFunctionCategories = null;
    let _rsvCurrentTags = [];

    /** Load function categories once, cache for reuse */
    async function loadFunctionCategories() {
        if (_rsvFunctionCategories) return _rsvFunctionCategories;
        try {
            const resp = await fetch('/api/function-categories');
            if (resp.ok) {
                const data = await resp.json();
                _rsvFunctionCategories = data?.data?.categories || data?.categories || (Array.isArray(data) ? data : []);
            }
        } catch (e) {
            console.warn(LOG_PREFIX, 'Could not fetch function categories:', e);
        }
        return _rsvFunctionCategories || [];
    }

    /** Load tags for the current role and render pills */
    async function loadRoleTags(roleName) {
        _rsvCurrentTags = [];
        try {
            const resp = await fetch(`/api/role-function-tags?role_name=${encodeURIComponent(roleName)}`);
            if (resp.ok) {
                const data = await resp.json();
                _rsvCurrentTags = data?.data?.tags || (Array.isArray(data) ? data : []);
            }
        } catch (e) { /* silent */ }
        renderRsvTagPills();
    }

    /** Render tag pills in the Source Viewer */
    function renderRsvTagPills() {
        const container = State.modal?.querySelector('#rsv-tag-pills');
        if (!container) return;
        if (!_rsvCurrentTags.length) {
            container.innerHTML = '<span style="color:var(--text-muted);font-size:11px;">No tags assigned</span>';
            return;
        }
        container.innerHTML = _rsvCurrentTags.map(t => {
            const cat = (_rsvFunctionCategories || []).find(c => c.code === t.function_code);
            const color = cat?.color || '#3b82f6';
            return `<span class="rsv-tag-pill" style="background:${color}18;color:${color};border:1px solid ${color}30;">
                ${escapeHtml(cat?.name || t.function_code)}
                <span class="rsv-tag-remove" data-tag-id="${t.id}" data-code="${escapeHtml(t.function_code)}" title="Remove">&times;</span>
            </span>`;
        }).join('');

        // Remove handlers
        container.querySelectorAll('.rsv-tag-remove').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const tagId = btn.dataset.tagId;
                await removeRsvTag(tagId);
            });
        });
    }

    /** Show the tag dropdown in the Source Viewer */
    async function showRsvTagDropdown() {
        // Close existing
        const existing = State.modal?.querySelector('.rsv-tag-dropdown-active');
        if (existing) { existing.remove(); return; }

        const cats = await loadFunctionCategories();
        if (!cats || !cats.length) {
            if (typeof showToast === 'function') showToast('No function categories available', 'info');
            return;
        }

        // Build hierarchy
        const childMap = {};
        cats.forEach(c => {
            if (c.parent_code) {
                if (!childMap[c.parent_code]) childMap[c.parent_code] = [];
                childMap[c.parent_code].push(c);
            }
        });
        const topLevel = cats.filter(c => !c.parent_code);

        let itemsHtml = '';
        topLevel.forEach(parent => {
            const pColor = parent.color || '#3b82f6';
            itemsHtml += `<div class="adj-tag-dropdown-header">${escapeHtml(parent.name)}</div>`;
            itemsHtml += `<div class="adj-tag-dropdown-item" data-code="${escapeHtml(parent.code)}">
                <span class="adj-tag-dot" style="background:${pColor}"></span>
                <span>${escapeHtml(parent.code)} - ${escapeHtml(parent.name)}</span>
            </div>`;
            (childMap[parent.code] || []).forEach(child => {
                const cColor = child.color || pColor;
                itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-2" data-code="${escapeHtml(child.code)}">
                    <span class="adj-tag-dot" style="background:${cColor}"></span>
                    <span>${escapeHtml(child.code)} - ${escapeHtml(child.name)}</span>
                </div>`;
                (childMap[child.code] || []).forEach(gc => {
                    const gColor = gc.color || cColor;
                    itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-3" data-code="${escapeHtml(gc.code)}">
                        <span class="adj-tag-dot" style="background:${gColor}"></span>
                        <span>${escapeHtml(gc.code)} - ${escapeHtml(gc.name)}</span>
                    </div>`;
                });
            });
        });

        // Add "Create Custom" option at bottom
        itemsHtml += `<div class="adj-tag-dropdown-header" style="margin-top:8px;border-top:1px solid var(--border-default);padding-top:8px;">Custom</div>`;
        itemsHtml += `<div class="adj-tag-dropdown-item rsv-create-custom-tag" style="color:var(--accent);">
            <span style="font-size:14px;">+</span>
            <span>Create New Tag...</span>
        </div>`;

        const dropdown = document.createElement('div');
        dropdown.className = 'adj-tag-dropdown rsv-tag-dropdown-active';
        dropdown.innerHTML = `
            <div class="adj-tag-dropdown-search">
                <input type="text" class="adj-tag-search-input" placeholder="Search tags..." autocomplete="off">
            </div>
            <div class="adj-tag-dropdown-list">${itemsHtml}</div>`;

        const anchor = State.modal?.querySelector('#rsv-tag-dropdown-anchor');
        if (anchor) anchor.appendChild(dropdown);

        // Search filter
        const searchInput = dropdown.querySelector('.adj-tag-search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.addEventListener('input', () => {
                const q = searchInput.value.toLowerCase();
                dropdown.querySelectorAll('.adj-tag-dropdown-item, .adj-tag-dropdown-header').forEach(el => {
                    const text = el.textContent.toLowerCase();
                    el.style.display = (!q || text.includes(q)) ? '' : 'none';
                });
            });
            searchInput.addEventListener('click', (e) => e.stopPropagation());
        }

        // Item click
        dropdown.addEventListener('click', async (e) => {
            // Create custom tag
            if (e.target.closest('.rsv-create-custom-tag')) {
                dropdown.remove();
                showCreateCustomTagDialog();
                return;
            }
            const item = e.target.closest('.adj-tag-dropdown-item');
            if (!item) return;
            const code = item.dataset.code;
            if (code) {
                await assignRsvTag(code);
                dropdown.remove();
            }
        });

        // Close on outside click
        setTimeout(() => {
            const closer = (e) => {
                if (!dropdown.contains(e.target) && e.target.id !== 'rsv-add-tag-btn' && !e.target.closest('#rsv-add-tag-btn')) {
                    dropdown.remove();
                    document.removeEventListener('click', closer);
                }
            };
            document.addEventListener('click', closer);
        }, 10);
    }

    /** Assign a function tag to the current role */
    async function assignRsvTag(functionCode) {
        if (!State.roleData?.name) return;
        try {
            const resp = await fetch('/api/role-function-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
                body: JSON.stringify({ role_name: State.roleData.name, function_code: functionCode, assigned_by: 'source-viewer' })
            });
            const result = await resp.json();
            if (result.success) {
                if (typeof showToast === 'function') showToast(`Tag "${functionCode}" assigned`, 'success');
                await loadRoleTags(State.roleData.name);
            } else {
                const msg = typeof result.error === 'object' ? (result.error?.message || 'Failed') : (result.error || 'Failed');
                if (typeof showToast === 'function') showToast(msg, 'info');
            }
        } catch (e) {
            console.warn(LOG_PREFIX, 'Tag assignment error:', e);
        }
    }

    /** Remove a tag from the current role */
    async function removeRsvTag(tagId) {
        if (!tagId) return;
        try {
            const resp = await fetch(`/api/role-function-tags/${tagId}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': getCSRFToken() }
            });
            if (resp.ok) {
                if (typeof showToast === 'function') showToast('Tag removed', 'success');
                if (State.roleData?.name) await loadRoleTags(State.roleData.name);
            }
        } catch (e) {
            console.warn(LOG_PREFIX, 'Tag removal error:', e);
            if (typeof showToast === 'function') showToast('Failed to remove tag', 'error');
        }
    }

    /** Show dialog to create a custom function tag */
    function showCreateCustomTagDialog() {
        const overlay = document.createElement('div');
        overlay.className = 'rsv-custom-tag-overlay';
        overlay.innerHTML = `
            <div class="rsv-custom-tag-dialog">
                <h4 style="margin:0 0 12px;font-size:14px;color:var(--text-primary);">Create Custom Tag</h4>
                <div style="margin-bottom:8px;">
                    <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Tag Code (short)</label>
                    <input type="text" id="rsv-new-tag-code" placeholder="e.g., AERO" maxlength="12"
                           style="width:100%;padding:6px 10px;border-radius:6px;border:1px solid var(--border-default);background:var(--bg-secondary);color:var(--text-primary);font-size:12px;">
                </div>
                <div style="margin-bottom:8px;">
                    <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Tag Name</label>
                    <input type="text" id="rsv-new-tag-name" placeholder="e.g., Aerodynamics"
                           style="width:100%;padding:6px 10px;border-radius:6px;border:1px solid var(--border-default);background:var(--bg-secondary);color:var(--text-primary);font-size:12px;">
                </div>
                <div style="margin-bottom:12px;">
                    <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Parent Category (optional)</label>
                    <select id="rsv-new-tag-parent" style="width:100%;padding:6px 10px;border-radius:6px;border:1px solid var(--border-default);background:var(--bg-secondary);color:var(--text-primary);font-size:12px;">
                        <option value="">(Top Level)</option>
                    </select>
                </div>
                <div style="margin-bottom:12px;">
                    <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Color</label>
                    <input type="color" id="rsv-new-tag-color" value="#3b82f6" style="width:40px;height:28px;border:none;background:none;cursor:pointer;">
                </div>
                <div style="display:flex;gap:8px;justify-content:flex-end;">
                    <button class="rsv-custom-tag-cancel" style="padding:6px 14px;border-radius:6px;border:1px solid var(--border-default);background:var(--bg-secondary);color:var(--text-primary);cursor:pointer;font-size:12px;">Cancel</button>
                    <button class="rsv-custom-tag-save" style="padding:6px 14px;border-radius:6px;border:none;background:var(--accent,#3b82f6);color:#fff;cursor:pointer;font-size:12px;font-weight:500;">Create & Assign</button>
                </div>
            </div>`;

        // Populate parent dropdown
        const parentSelect = overlay.querySelector('#rsv-new-tag-parent');
        if (_rsvFunctionCategories) {
            _rsvFunctionCategories.filter(c => !c.parent_code).forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.code;
                opt.textContent = `${c.code} - ${c.name}`;
                parentSelect.appendChild(opt);
            });
        }

        State.modal.appendChild(overlay);

        overlay.querySelector('.rsv-custom-tag-cancel').addEventListener('click', () => overlay.remove());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

        overlay.querySelector('.rsv-custom-tag-save').addEventListener('click', async () => {
            const code = overlay.querySelector('#rsv-new-tag-code').value.trim().toUpperCase();
            const name = overlay.querySelector('#rsv-new-tag-name').value.trim();
            const parent = overlay.querySelector('#rsv-new-tag-parent').value;
            const color = overlay.querySelector('#rsv-new-tag-color').value;

            if (!code || !name) {
                if (typeof showToast === 'function') showToast('Code and Name are required', 'error');
                return;
            }

            // Create the new category via API
            try {
                const csrfToken = getCSRFToken();
                const createResp = await fetch('/api/function-categories', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ code, name, parent_code: parent || null, color, description: name })
                });
                const createResult = await createResp.json();
                if (createResult.success || createResp.ok) {
                    // Invalidate cache
                    _rsvFunctionCategories = null;
                    await loadFunctionCategories();
                    // Assign to current role
                    await assignRsvTag(code);
                    overlay.remove();
                } else {
                    const msg = typeof createResult.error === 'object' ? (createResult.error?.message || 'Failed') : (createResult.error || 'Failed to create tag');
                    if (typeof showToast === 'function') showToast(msg, 'error');
                }
            } catch (e) {
                console.warn(LOG_PREFIX, 'Create custom tag error:', e);
                if (typeof showToast === 'function') showToast('Failed to create tag', 'error');
            }
        });

        // Focus code input
        setTimeout(() => overlay.querySelector('#rsv-new-tag-code')?.focus(), 50);
    }

    /**
     * Update the status badge display.
     */
    function updateStatusBadge(status) {
        const badge = State.modal.querySelector('.rsv-status-badge');
        if (!badge) return;

        badge.dataset.status = status;

        const labels = {
            'pending': 'Pending Review',
            'confirmed': 'Confirmed Role',
            'deliverable': 'Deliverable',
            'rejected': 'Rejected'
        };

        badge.textContent = labels[status] || 'Pending Review';
    }

    /**
     * Update adjudication button states after an action.
     */
    function updateAdjudicationButtons(activeAction) {
        const confirmBtn = State.modal.querySelector('.rsv-adj-confirm');
        const deliverableBtn = State.modal.querySelector('.rsv-adj-deliverable');
        const rejectBtn = State.modal.querySelector('.rsv-adj-reject');

        // Reset all buttons
        [confirmBtn, deliverableBtn, rejectBtn].forEach(btn => {
            btn.classList.remove('rsv-adj-active');
        });

        // Highlight the active action
        if (activeAction === 'confirmed') {
            confirmBtn.classList.add('rsv-adj-active');
        } else if (activeAction === 'deliverable') {
            deliverableBtn.classList.add('rsv-adj-active');
        } else if (activeAction === 'rejected') {
            rejectBtn.classList.add('rsv-adj-active');
        }
    }

    /**
     * Get CSRF token for API calls.
     */
    function getCSRFToken() {
        // v4.0.3: Prefer synced token (window.CSRF_TOKEN) which stays in sync with the
        // server session, over the meta tag which may have a stale page-load token
        if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
        if (window.State?.csrfToken) return window.State.csrfToken;
        if (window.TWR?.State?.csrfToken) return window.TWR.State.csrfToken;

        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) return metaTag.content;

        return '';
    }

    /**
     * Show a toast notification.
     */
    function showToast(message, type = 'info') {
        // Try to use the app's toast system
        if (window.TWR?.Toast?.show) {
            window.TWR.Toast.show(message, type);
            return;
        }
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }

        // Fallback: simple notification
        const toast = document.createElement('div');
        toast.className = `rsv-toast rsv-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('rsv-toast-show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('rsv-toast-show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function handleKeydown(e) {
        if (!State.isOpen) return;

        // Ignore if typing in input
        if (e.target.matches('input, textarea, select')) {
            if (e.key === 'Escape') {
                e.target.blur();
            }
            return;
        }

        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                if (e.shiftKey) {
                    previousDocument();
                } else {
                    previousMention();
                }
                break;
            case 'ArrowRight':
                e.preventDefault();
                if (e.shiftKey) {
                    nextDocument();
                } else {
                    nextMention();
                }
                break;
            case 'Escape':
                e.preventDefault();
                close();
                break;
        }
    }

    // ============================================================
    // NAVIGATION
    // ============================================================

    function previousMention() {
        if (State.currentMentionIndex > 0) {
            State.currentMentionIndex--;
            updateUI();
        } else if (State.currentDocIndex > 0) {
            // Move to previous document, last mention
            State.currentDocIndex--;
            updateMentionsForCurrentDoc();
            State.currentMentionIndex = State.mentionsInCurrentDoc.length - 1;
            updateUI();
        }
    }

    function nextMention() {
        if (State.currentMentionIndex < State.mentionsInCurrentDoc.length - 1) {
            State.currentMentionIndex++;
            updateUI();
        } else if (State.currentDocIndex < State.documents.length - 1) {
            // Move to next document, first mention
            State.currentDocIndex++;
            State.currentMentionIndex = 0;
            updateMentionsForCurrentDoc();
            updateUI();
        }
    }

    function previousDocument() {
        if (State.currentDocIndex > 0) {
            State.currentDocIndex--;
            State.currentMentionIndex = 0;
            updateMentionsForCurrentDoc();
            updateUI();
        }
    }

    function nextDocument() {
        if (State.currentDocIndex < State.documents.length - 1) {
            State.currentDocIndex++;
            State.currentMentionIndex = 0;
            updateMentionsForCurrentDoc();
            updateUI();
        }
    }

    function updateMentionsForCurrentDoc() {
        const currentDoc = State.documents[State.currentDocIndex];
        State.mentionsInCurrentDoc = State.roleData?.occurrencesByDoc?.[currentDoc] || [];
    }

    /**
     * Render the full document text with all role mentions highlighted.
     * Scrolls to the currently selected mention.
     *
     * v4.5.2: Fixed bug where AppState.currentText was used for ALL documents,
     * causing every document tab to show the same content. Now always fetches
     * per-document text from the API with a per-document cache.
     */
    async function renderDocumentText(roleName, mentions, currentIndex) {
        const container = State.modal.querySelector('.rsv-document-text');
        if (!container) return;

        const currentDoc = State.documents[State.currentDocIndex];
        let documentText = '';

        // v4.5.2: Use per-document cache instead of AppState.currentText
        // AppState.currentText is the currently-loaded document in the main app,
        // NOT necessarily the document selected in the Role Source Viewer.
        if (currentDoc && State.documentTextCache[currentDoc]) {
            documentText = State.documentTextCache[currentDoc];
        } else if (currentDoc && currentDoc !== 'No documents found') {
            // Fetch from API for this specific document
            container.innerHTML = `
                <div class="rsv-loading">
                    <p>Loading document text...</p>
                </div>
            `;

            try {
                const response = await fetch(`/api/scan-history/document-text?filename=${encodeURIComponent(currentDoc)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.text) {
                        documentText = data.text;
                        // v4.5.2: Cache per document filename
                        State.documentTextCache[currentDoc] = documentText;
                    }
                }
            } catch (e) {
                console.log(LOG_PREFIX, 'Could not fetch document text:', e);
            }

            // v4.5.2: If API didn't have it, try AppState.currentText as last resort
            // but ONLY if this document matches the currently loaded filename
            if (!documentText) {
                const AppState = window.TWR?.State?.State || window.State;
                const currentFilename = AppState?.filename || AppState?.currentFilename || '';
                if (currentFilename && currentDoc && currentDoc === currentFilename) {
                    documentText = AppState?.currentText || '';
                    if (documentText) {
                        State.documentTextCache[currentDoc] = documentText;
                    }
                }
            }
        }

        if (!documentText) {
            // No document text available - show placeholder with context snippets
            if (mentions.length > 0 && !mentions[0].placeholder) {
                const currentMention = mentions[currentIndex] || mentions[0];
                container.innerHTML = `
                    <div class="rsv-context-snippet">
                        <span class="rsv-context-before">${escapeHtml(currentMention.contextBefore || '')}</span>
                        <mark class="rsv-role-highlight" data-mention-index="${currentIndex}">${escapeHtml(currentMention.matchedText || roleName)}</mark>
                        <span class="rsv-context-after">${escapeHtml(currentMention.contextAfter || '')}</span>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="rsv-no-document">
                        <p>No document text available.</p>
                        <p class="rsv-hint">The original document file may have been moved or deleted.</p>
                    </div>
                `;
            }
            return;
        }

        // Build highlighted document text
        // Find all occurrences of the role in the text
        const regex = new RegExp(escapeRegex(roleName), 'gi');
        let lastIndex = 0;
        let mentionIdx = 0;
        let html = '';
        let match;

        while ((match = regex.exec(documentText)) !== null) {
            // Add text before this match
            const textBefore = documentText.substring(lastIndex, match.index);
            html += escapeHtml(textBefore);

            // Add the highlighted match
            const isCurrentMention = mentionIdx === currentIndex;
            html += `<mark class="rsv-role-highlight ${isCurrentMention ? 'rsv-current' : ''}" data-mention-index="${mentionIdx}">${escapeHtml(match[0])}</mark>`;

            lastIndex = match.index + match[0].length;
            mentionIdx++;
        }

        // Add remaining text
        html += escapeHtml(documentText.substring(lastIndex));

        // Convert newlines to line breaks for proper display
        html = html.replace(/\n/g, '<br>');

        container.innerHTML = html;

        // Add click handlers to all highlights for quick navigation
        container.querySelectorAll('.rsv-role-highlight').forEach(el => {
            el.addEventListener('click', (e) => {
                const idx = parseInt(e.target.dataset.mentionIndex, 10);
                if (!isNaN(idx) && idx !== State.currentMentionIndex) {
                    State.currentMentionIndex = idx;
                    updateUI();
                }
            });
        });

        // v4.9.3: If a statement search is pending, find the nearest role mention
        // and navigate to it. highlightStatementInDoc uses the ORIGINAL document text
        // (not the DOM) to find the match position, then navigates to the closest mention.
        if (State._pendingSearchText) {
            console.log(LOG_PREFIX, 'renderDocumentText: handling pending statement search');
            const searchText = State._pendingSearchText;
            // Clear flag FIRST to prevent infinite loop (highlightStatementInDoc calls updateUI)
            State._pendingSearchText = null;
            // Use setTimeout to let this render complete before triggering navigation
            setTimeout(() => {
                highlightStatementInDoc(searchText);
            }, 100);
        } else {
            // Default: scroll to the current mention
            requestAnimationFrame(() => {
                const currentHighlight = container.querySelector('.rsv-role-highlight.rsv-current');
                if (currentHighlight) {
                    currentHighlight.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            });
        }
    }

    // ============================================================
    // UI UPDATES
    // ============================================================

    function updateUI() {
        const modal = State.modal;
        const roleData = State.roleData;

        if (!roleData) return;

        const currentDoc = State.documents[State.currentDocIndex];
        const mentions = State.mentionsInCurrentDoc;
        const currentMention = mentions[State.currentMentionIndex] || {};

        // Calculate total mentions across all docs
        const totalMentions = Object.values(roleData.occurrencesByDoc || {})
            .reduce((sum, arr) => sum + arr.length, 0);

        // Calculate current mention number across all docs
        let currentMentionNumber = 0;
        for (let i = 0; i < State.currentDocIndex; i++) {
            const doc = State.documents[i];
            currentMentionNumber += (roleData.occurrencesByDoc?.[doc]?.length || 0);
        }
        currentMentionNumber += State.currentMentionIndex + 1;

        // Update counter
        modal.querySelector('.rsv-counter .current').textContent = currentMentionNumber;
        modal.querySelector('.rsv-counter .total').textContent = totalMentions;

        // Update navigation buttons
        const isFirst = State.currentDocIndex === 0 && State.currentMentionIndex === 0;
        const isLast = State.currentDocIndex === State.documents.length - 1 &&
                       State.currentMentionIndex === mentions.length - 1;
        modal.querySelector('.rsv-prev-mention').disabled = isFirst;
        modal.querySelector('.rsv-next-mention').disabled = isLast;

        // Update document selector
        const selector = modal.querySelector('.rsv-doc-selector');
        selector.innerHTML = State.documents.map((doc, i) =>
            `<option value="${i}" ${i === State.currentDocIndex ? 'selected' : ''}>
                ${escapeHtml(doc)} (${roleData.occurrencesByDoc?.[doc]?.length || 0})
            </option>`
        ).join('');

        // Update source panel info
        modal.querySelector('.rsv-doc-name').textContent = currentDoc;
        modal.querySelector('.rsv-line-info').textContent =
            currentMention.lineNumber ? `Line ${currentMention.lineNumber}` : '';

        // Update context status
        const contextStatus = modal.querySelector('.rsv-context-status');

        if (currentMention.inferredRole) {
            contextStatus.innerHTML = `
                <span style="color: var(--warning, #f59e0b);">
                    ⓘ This role was inferred from document analysis. The exact phrase may not appear verbatim in the text.
                </span>
            `;
        } else if (currentMention.storedContext) {
            contextStatus.innerHTML = `
                <span style="color: var(--info, #3b82f6);">
                    ⓘ Showing stored context from when this document was scanned.
                </span>
            `;
        } else if (currentMention.partialMatch) {
            contextStatus.innerHTML = `
                <span style="color: var(--info, #3b82f6);">
                    ⓘ Showing partial match. The full role name may appear in different form.
                </span>
            `;
        } else if (currentMention.placeholder) {
            contextStatus.innerHTML = `
                <span style="color: var(--text-muted, #9ca3af);">
                    ⓘ Document text not available. Scan this document with "Role Extraction" enabled to see full context.
                </span>
            `;
        } else {
            contextStatus.textContent = currentMention.responsibility
                ? `Responsibility: ${currentMention.responsibility}`
                : '';
        }

        // Render full document text with highlights
        renderDocumentText(roleData.name, mentions, State.currentMentionIndex);

        // Update role details panel
        modal.querySelector('.rsv-role-name').textContent = roleData.name;
        // v3.4.0: Clarify that this is text occurrences (times the name appears), not responsibility count
        modal.querySelector('.rsv-frequency').textContent =
            `${totalMentions} text occurrence${totalMentions !== 1 ? 's' : ''}`;
        modal.querySelector('.rsv-doc-count').textContent =
            `${State.documents.length} document${State.documents.length !== 1 ? 's' : ''}`;

        // Update variants
        const variants = Array.isArray(roleData.variants)
            ? roleData.variants
            : Object.keys(roleData.variants || {});
        const uniqueVariants = [...new Set(variants.filter(v =>
            v.toLowerCase() !== roleData.name.toLowerCase()
        ))];
        const variantsSection = modal.querySelector('.rsv-variants-section');
        const variantsEl = modal.querySelector('.rsv-variants');

        if (uniqueVariants.length > 0) {
            variantsSection.style.display = 'block';
            variantsEl.innerHTML = uniqueVariants.slice(0, 5).map(v =>
                `<span class="rsv-variant-tag">${escapeHtml(v)}</span>`
            ).join('');
        } else {
            variantsSection.style.display = 'none';
        }

        // Update responsibilities
        const responsibilities = roleData.responsibilities || [];
        const responsibilitiesSection = modal.querySelector('.rsv-responsibilities-section');
        const responsibilitiesEl = modal.querySelector('.rsv-responsibilities');

        if (responsibilities.length > 0) {
            responsibilitiesSection.style.display = 'block';
            responsibilitiesEl.innerHTML = `<ul>${responsibilities.slice(0, 5).map(r =>
                `<li>${escapeHtml(r)}</li>`
            ).join('')}</ul>`;
        } else {
            responsibilitiesSection.style.display = 'none';
        }

        // Load function tags for this role (v4.0.3)
        loadFunctionCategories().then(() => loadRoleTags(roleData.name));

        // Update document list
        const docList = modal.querySelector('.rsv-doc-list');
        docList.innerHTML = State.documents.map((doc, i) => `
            <div class="rsv-doc-item ${i === State.currentDocIndex ? 'active' : ''}"
                 data-doc-index="${i}">
                <span class="rsv-doc-icon">📄</span>
                <span class="rsv-doc-name-text">${escapeHtml(doc)}</span>
                <span class="rsv-doc-mentions">${roleData.occurrencesByDoc?.[doc]?.length || 0}</span>
            </div>
        `).join('');

        // Add click handlers to doc items
        docList.querySelectorAll('.rsv-doc-item').forEach(item => {
            item.addEventListener('click', () => {
                State.currentDocIndex = parseInt(item.dataset.docIndex, 10);
                State.currentMentionIndex = 0;
                updateMentionsForCurrentDoc();
                updateUI();
            });
        });
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    /**
     * Open the Role Source Viewer for a specific role.
     */
    async function open(roleName, options) {
        console.log(LOG_PREFIX, 'Opening viewer for role:', roleName, options ? '(with options)' : '');

        createModal();

        // Show loading state
        State.modal.classList.add('open');
        State.isOpen = true;
        document.body.style.overflow = 'hidden';

        // Reset adjudication panel for new role
        resetAdjudicationPanel();

        // Update loading UI — v5.9.0: null guards on querySelector results
        const roleNameEl = State.modal.querySelector('.rsv-role-name');
        if (roleNameEl) roleNameEl.textContent = roleName;
        const docTextEl = State.modal.querySelector('.rsv-document-text');
        if (docTextEl) {
            docTextEl.innerHTML = `<div class="rsv-loading"><p>Loading "${roleName}"...</p><p>Searching for mentions...</p></div>`;
        }
        const ctxStatusEl = State.modal.querySelector('.rsv-context-status');
        if (ctxStatusEl) ctxStatusEl.textContent = '';

        // Try to get role data from State first
        let roleData = getRoleDataFromState(roleName);

        // If not available, try API
        if (!roleData) {
            roleData = await fetchRoleDataFromAPI(roleName);
        }

        if (!roleData || roleData.documents.length === 0) {
            // Show "no context" message
            State.roleData = {
                name: roleName,
                variants: [],
                responsibilities: [],
                frequency: 0,
                documents: ['No documents found'],
                occurrencesByDoc: {
                    'No documents found': [{
                        matchedText: roleName,
                        contextBefore: '',
                        contextAfter: '',
                        placeholder: true
                    }]
                }
            };
            State.documents = ['No documents found'];
            State.currentDocIndex = 0;
            State.currentMentionIndex = 0;
            State.mentionsInCurrentDoc = State.roleData.occurrencesByDoc['No documents found'];

            updateUI();

            const ctxEl = State.modal.querySelector('.rsv-context-status');
            if (ctxEl) ctxEl.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-muted, #6b7280);">
                    <p style="margin-bottom: 10px;">No source context available for this role.</p>
                    <p style="font-size: 0.85rem;">To see role context, scan a document with "Role Extraction" enabled.</p>
                </div>
            `;

            // Still load adjudication status even for roles without context
            await loadAdjudicationStatus(roleName);
            return;
        }

        // Initialize state
        State.roleData = roleData;
        State.documents = roleData.documents;
        State.currentDocIndex = 0;
        State.currentMentionIndex = 0;

        // v4.8.4: If opened with searchText/sourceDocument options (from Statement Explorer),
        // navigate to the right document and find the matching mention
        if (options?.sourceDocument) {
            const targetDoc = options.sourceDocument;
            const docIdx = State.documents.findIndex(d => d === targetDoc || d.includes(targetDoc) || targetDoc.includes(d));
            if (docIdx >= 0) {
                State.currentDocIndex = docIdx;
                console.log(LOG_PREFIX, `Statement Explorer: navigated to doc index ${docIdx}: "${State.documents[docIdx]}"`);
            }
        }

        updateMentionsForCurrentDoc();

        // If we have searchText, try to find the mention that best matches
        if (options?.searchText && State.mentionsInCurrentDoc?.length > 0) {
            const searchLower = options.searchText.toLowerCase().substring(0, 80);
            let bestIdx = 0;
            let bestScore = 0;
            State.mentionsInCurrentDoc.forEach((mention, idx) => {
                // Check if the responsibility text appears near this mention
                const context = ((mention.contextBefore || '') + ' ' + (mention.matchedText || '') + ' ' + (mention.contextAfter || '')).toLowerCase();
                // Simple overlap scoring
                const words = searchLower.split(/\s+/).filter(w => w.length > 3);
                let score = 0;
                words.forEach(w => { if (context.includes(w)) score++; });
                if (score > bestScore) {
                    bestScore = score;
                    bestIdx = idx;
                }
            });
            if (bestScore > 0) {
                State.currentMentionIndex = bestIdx;
                console.log(LOG_PREFIX, `Statement Explorer: matched mention index ${bestIdx} (score: ${bestScore})`);
            }
        }

        // v4.9.1: Set pending search flag BEFORE updateUI so renderDocumentText
        // handles highlighting as part of its own render cycle (can't be overwritten)
        if (options?.searchText) {
            State._pendingSearchText = options.searchText;
        }

        // Update UI (renderDocumentText will handle the search highlight if _pendingSearchText is set)
        updateUI();

        // Load adjudication status for this role from the database
        await loadAdjudicationStatus(roleName);

        console.log(LOG_PREFIX, 'Viewer opened successfully');
    }

    /**
     * v4.8.4: Highlight a specific statement text in the document view.
     * Called by Statement Explorer to show where a responsibility came from.
     */
    function highlightStatementInDoc(searchText) {
        // v4.9.3: Completely rewritten. Instead of trying to insert DOM markers (which fails
        // because the document text is rendered as flat text with <br> and <mark> elements
        // and character-position-to-DOM mapping is unreliable across 950K chars),
        // we find the statement in the ORIGINAL document text, determine which role mention
        // is nearest, and navigate to that mention using the RSV's own navigation system.

        const roleName = State.roleData?.name;
        const currentDoc = State.documents?.[State.currentDocIndex];
        const rawText = currentDoc ? State.documentTextCache?.[currentDoc] : null;

        console.log(LOG_PREFIX, 'highlightStatementInDoc v4.9.3 called',
            'roleName:', roleName,
            'rawTextLen:', rawText?.length,
            'searchTextLen:', searchText?.length);

        if (!rawText || !searchText || !roleName) return;

        const searchNorm = searchText.trim().toLowerCase().replace(/\s+/g, ' ');
        const rawNorm = rawText.toLowerCase();
        if (searchNorm.length < 5) return;

        // Find where the statement text appears in the raw document
        let matchPos = -1;
        const searchChunks = [
            searchNorm.substring(0, 80),
            searchNorm.substring(0, 60),
            searchNorm.substring(0, 40),
            searchNorm.substring(0, 25)
        ];

        for (const chunk of searchChunks) {
            if (chunk.length < 5) continue;
            matchPos = rawNorm.indexOf(chunk);
            if (matchPos >= 0) {
                console.log(LOG_PREFIX, `Direct match in raw text at pos ${matchPos} (chunk len ${chunk.length})`);
                break;
            }
        }

        // Fuzzy fallback: find cluster of significant words
        if (matchPos < 0) {
            const words = searchNorm.split(/\s+/).filter(w => w.length > 4
                && !['that', 'this', 'with', 'from', 'have', 'been', 'will', 'shall',
                     'should', 'their', 'which', 'other'].includes(w));
            if (words.length >= 3) {
                let positions = [];
                for (const w of words) {
                    let idx = rawNorm.indexOf(w);
                    while (idx >= 0) {
                        positions.push(idx);
                        idx = rawNorm.indexOf(w, idx + 1);
                    }
                }
                if (positions.length > 0) {
                    positions.sort((a, b) => a - b);
                    let bestStart = 0, bestCount = 0;
                    for (let i = 0; i < positions.length; i++) {
                        let count = 0;
                        for (let j = i; j < positions.length && positions[j] < positions[i] + 500; j++) count++;
                        if (count > bestCount) { bestCount = count; bestStart = positions[i]; }
                    }
                    if (bestCount >= 3) {
                        matchPos = bestStart;
                        console.log(LOG_PREFIX, `Fuzzy match at pos ${matchPos} (${bestCount} word hits)`);
                    }
                }
            }
        }

        if (matchPos < 0) {
            console.log(LOG_PREFIX, 'Statement highlight: no match found');
            return;
        }

        // Now find all positions of the role name in the raw text
        const roleRegex = new RegExp(escapeRegex(roleName), 'gi');
        let rolePositions = [];
        let m;
        while ((m = roleRegex.exec(rawText)) !== null) {
            rolePositions.push(m.index);
        }

        console.log(LOG_PREFIX, `Found ${rolePositions.length} role mentions, statement at pos ${matchPos}`);

        if (rolePositions.length === 0) return;

        // Find the role mention closest to (and preferably just before) the statement text
        let bestMentionIdx = 0;
        let bestDist = Infinity;
        for (let i = 0; i < rolePositions.length; i++) {
            const dist = Math.abs(rolePositions[i] - matchPos);
            // Prefer mentions just before the statement (within 500 chars)
            const bonus = (rolePositions[i] <= matchPos && matchPos - rolePositions[i] < 500) ? -1000 : 0;
            if (dist + bonus < bestDist) {
                bestDist = dist + bonus;
                bestMentionIdx = i;
            }
        }

        console.log(LOG_PREFIX, `Navigating to mention ${bestMentionIdx} (rolePos: ${rolePositions[bestMentionIdx]}, dist: ${Math.abs(rolePositions[bestMentionIdx] - matchPos)})`);

        // Navigate to that mention using the RSV's own system
        if (bestMentionIdx !== State.currentMentionIndex) {
            State.currentMentionIndex = bestMentionIdx;
            updateUI();
        } else {
            // Already at the right mention — just scroll to it
            const docTextEl = State.modal?.querySelector('.rsv-document-text');
            const currentMark = docTextEl?.querySelector('.rsv-role-highlight.rsv-current');
            if (currentMark) {
                currentMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    /**
     * Reset the adjudication panel to default state.
     */
    function resetAdjudicationPanel() {
        if (!State.modal) return;

        // Reset status badge
        updateStatusBadge('pending');

        // Reset button states
        const confirmBtn = State.modal.querySelector('.rsv-adj-confirm');
        const deliverableBtn = State.modal.querySelector('.rsv-adj-deliverable');
        const rejectBtn = State.modal.querySelector('.rsv-adj-reject');
        [confirmBtn, deliverableBtn, rejectBtn].forEach(btn => {
            if (btn) btn.classList.remove('rsv-adj-active');
        });

        // Reset category to default
        const categorySelect = State.modal.querySelector('.rsv-category-select');
        if (categorySelect) categorySelect.value = 'Role';

        // Clear notes
        const notesInput = State.modal.querySelector('.rsv-notes-input');
        if (notesInput) notesInput.value = '';
    }

    /**
     * Load adjudication status for a role from the database.
     */
    async function loadAdjudicationStatus(roleName) {
        try {
            const response = await fetch(`/api/roles/adjudication-status?role_name=${encodeURIComponent(roleName)}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log(LOG_PREFIX, `Loaded adjudication status for "${roleName}":`, data.status);

                    // Update status badge
                    updateStatusBadge(data.status);

                    // Update button states
                    if (data.status !== 'pending') {
                        updateAdjudicationButtons(data.status);
                    }

                    // Update category (add dynamic option if not in list)
                    const categorySelect = State.modal.querySelector('.rsv-category-select');
                    if (categorySelect && data.category) {
                        const cat = data.category;
                        if (!categorySelect.querySelector(`option[value="${cat}"]`)) {
                            const opt = document.createElement('option');
                            opt.value = cat;
                            opt.textContent = cat;
                            const customOpt = categorySelect.querySelector('option[value="__custom__"]');
                            if (customOpt) categorySelect.insertBefore(opt, customOpt);
                            else categorySelect.appendChild(opt);
                        }
                        categorySelect.value = cat;
                    }

                    // Update notes
                    const notesInput = State.modal.querySelector('.rsv-notes-input');
                    if (notesInput && data.notes) {
                        notesInput.value = data.notes;
                    }
                }
            }
        } catch (error) {
            console.log(LOG_PREFIX, 'Could not load adjudication status:', error);
            // Not critical - just use default pending state
        }
    }

    /**
     * Close the Role Source Viewer.
     */
    function close() {
        if (State.modal) {
            State.modal.classList.remove('open');
        }
        State.isOpen = false;
        State.documentTextCache = {}; // v4.5.2: Clear per-document cache on close
        State.documentText = '';
        document.body.style.overflow = '';
        console.log(LOG_PREFIX, 'Viewer closed');
    }

    /**
     * Initialize the module.
     */
    function init() {
        console.log(LOG_PREFIX, `Initializing v${VERSION}`);

        // Inject CSS
        injectStyles();

        // Create modal
        createModal();

        // Global click handler with capturing phase
        document.addEventListener('click', (e) => {
            const roleElement = e.target.closest('[data-role-source]');
            if (roleElement) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                const roleName = roleElement.getAttribute('data-role-source');
                if (roleName) {
                    console.log(LOG_PREFIX, `Click captured for role: ${roleName}`);
                    open(roleName);
                }
            }
        }, true);

        console.log(LOG_PREFIX, 'Initialized successfully');
    }

    // ============================================================
    // CSS STYLES
    // ============================================================

    function injectStyles() {
        if (document.getElementById('role-source-viewer-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'role-source-viewer-styles';
        styles.textContent = `
/* Role Source Viewer - Split Panel Review Mode */
.rsv-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10000;
}

.rsv-modal.open {
    display: flex;
    align-items: center;
    justify-content: center;
}

.rsv-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
}

.rsv-container {
    position: relative;
    width: 95%;
    max-width: 1400px;
    height: 90%;
    max-height: 900px;
    background: var(--bg-primary, #fff);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Header */
.rsv-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.rsv-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary, #333);
}

.rsv-nav {
    display: flex;
    align-items: center;
    gap: 16px;
}

.rsv-counter {
    font-size: 0.875rem;
    color: var(--text-secondary, #666);
}

.rsv-close {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: var(--text-secondary, #666);
    padding: 4px 8px;
    line-height: 1;
}

.rsv-close:hover {
    color: var(--text-primary, #333);
}

/* Body - Split Panel */
.rsv-body {
    flex: 1;
    display: flex;
    overflow: hidden;
}

/* Source Panel (Left) */
.rsv-source-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border-color, #e0e0e0);
    min-width: 0;
}

.rsv-source-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rsv-source-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.rsv-doc-selector-wrap {
    flex-shrink: 0;
}

.rsv-doc-selector {
    padding: 6px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    font-size: 0.85rem;
    max-width: 300px;
    cursor: pointer;
}

.rsv-source-info {
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    font-size: 0.813rem;
    color: var(--text-secondary, #666);
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f9f9f9);
}

.rsv-source-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1rem;
    line-height: 1.8;
    color: var(--text-primary, #333);
}

.rsv-document-text {
    white-space: pre-wrap;
    word-wrap: break-word;
}

.rsv-role-highlight {
    background: linear-gradient(180deg, rgba(255, 235, 59, 0.3) 0%, rgba(255, 235, 59, 0.5) 100%);
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 600;
    color: var(--text-primary, #333);
    cursor: pointer;
    transition: all 0.2s;
}

.rsv-role-highlight:hover {
    background: linear-gradient(180deg, rgba(255, 235, 59, 0.5) 0%, rgba(255, 235, 59, 0.7) 100%);
}

.rsv-role-highlight.rsv-current {
    background: linear-gradient(180deg, rgba(255, 193, 7, 0.6) 0%, rgba(255, 152, 0, 0.8) 100%);
    box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.3);
    animation: rsv-pulse 1.5s ease-in-out;
}

@keyframes rsv-pulse {
    0%, 100% { box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.3); }
    50% { box-shadow: 0 0 0 6px rgba(255, 152, 0, 0.2); }
}

.rsv-context-snippet {
    padding: 20px;
    background: var(--bg-secondary, #f9f9f9);
    border-radius: 8px;
    line-height: 1.8;
}

.rsv-context-before,
.rsv-context-after {
    color: var(--text-secondary, #666);
}

.rsv-no-document,
.rsv-loading {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted, #9ca3af);
}

.rsv-no-document p,
.rsv-loading p {
    margin: 0 0 8px 0;
}

.rsv-hint {
    font-size: 0.85rem;
    font-style: italic;
}

.rsv-loading {
    animation: rsv-fade 1s ease-in-out infinite alternate;
}

@keyframes rsv-fade {
    from { opacity: 0.5; }
    to { opacity: 1; }
}

.rsv-source-actions {
    padding: 12px 16px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
    font-size: 0.85rem;
    color: var(--text-secondary, #666);
}

/* Details Panel (Right) */
.rsv-details-panel {
    width: 380px;
    display: flex;
    flex-direction: column;
    background: var(--bg-secondary, #f9f9f9);
    flex-shrink: 0;
}

.rsv-details-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rsv-details-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.rsv-role-badge {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    transition: opacity 0.15s;
}
.rsv-role-badge:hover { opacity: 0.9; }
.rsv-role-badge:hover .rsv-role-edit-icon { opacity: 1; }

.rsv-role-rename-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
}
.rsv-role-rename-input {
    flex: 1;
    padding: 5px 10px;
    border: 1px solid var(--border-default, #ccc);
    border-radius: 6px;
    font-size: 0.85rem;
    background: var(--bg-surface, #fff);
    color: var(--text-primary, #333);
}
.rsv-role-rename-save, .rsv-role-rename-cancel {
    padding: 4px 10px;
    border: none;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
    font-weight: 500;
}
.rsv-role-rename-save {
    background: #22c55e;
    color: white;
}
.rsv-role-rename-save:hover { background: #16a34a; }
.rsv-role-rename-cancel {
    background: var(--bg-hover, #e5e5e5);
    color: var(--text-secondary, #666);
}
.rsv-role-rename-cancel:hover { background: var(--bg-surface, #d4d4d4); }

.rsv-category-custom-input {
    margin-top: 6px;
    padding: 5px 10px;
    border: 1px solid var(--border-default, #ccc);
    border-radius: 6px;
    font-size: 0.85rem;
    width: 100%;
    background: var(--bg-surface, #fff);
    color: var(--text-primary, #333);
    box-sizing: border-box;
}

.rsv-details-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
}

.rsv-detail-section {
    margin-bottom: 20px;
}

.rsv-detail-section label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.rsv-detail-value {
    font-size: 0.95rem;
    color: var(--text-primary, #333);
}

.rsv-variant-tag {
    display: inline-block;
    background: var(--bg-tertiary, #e5e7eb);
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    margin: 2px 4px 2px 0;
}

.rsv-responsibilities ul {
    margin: 0;
    padding-left: 18px;
}

.rsv-responsibilities li {
    margin-bottom: 4px;
    font-size: 0.9rem;
}

.rsv-doc-list {
    max-height: 200px;
    overflow-y: auto;
}

.rsv-doc-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
}

.rsv-doc-item:hover {
    background: var(--bg-hover, #e5e7eb);
}

.rsv-doc-item.active {
    background: var(--accent-light, #dbeafe);
    border: 1px solid var(--accent-primary, #3b82f6);
}

.rsv-doc-icon {
    font-size: 1rem;
}

.rsv-doc-name-text {
    flex: 1;
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.rsv-doc-mentions {
    background: var(--bg-tertiary, #e5e7eb);
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Buttons */
.rsv-btn {
    padding: 8px 16px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.rsv-btn:hover:not(:disabled) {
    background: var(--bg-secondary, #f5f5f5);
}

.rsv-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* Footer */
.rsv-footer {
    padding: 12px 24px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.rsv-shortcuts {
    display: flex;
    gap: 24px;
    font-size: 0.75rem;
    color: var(--text-secondary, #666);
}

.rsv-shortcuts kbd {
    display: inline-block;
    padding: 2px 6px;
    margin-right: 4px;
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
}

/* Clickable role styling */
.role-clickable {
    cursor: pointer;
    text-decoration: underline;
    text-decoration-style: dotted;
    text-underline-offset: 2px;
}

.role-clickable:hover {
    color: var(--accent-primary, #4f46e5);
    text-decoration-style: solid;
}

/* Adjudication Section */
.rsv-adjudication-section {
    background: var(--bg-tertiary, #f3f4f6);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.rsv-adjudication-section > label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}

.rsv-status-indicator {
    margin-bottom: 12px;
}

.rsv-status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.rsv-status-badge[data-status="pending"] {
    background: #fef3c7;
    color: #92400e;
}

.rsv-status-badge[data-status="confirmed"] {
    background: #d1fae5;
    color: #065f46;
}

.rsv-status-badge[data-status="deliverable"] {
    background: #dbeafe;
    color: #1e40af;
}

.rsv-status-badge[data-status="rejected"] {
    background: #fee2e2;
    color: #991b1b;
}

.rsv-adjudication-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 14px;
}

.rsv-adj-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--text-secondary, #555);
}

.rsv-adj-btn:hover {
    border-color: var(--accent-primary, #4f46e5);
}

.rsv-adj-btn svg {
    flex-shrink: 0;
}

.rsv-adj-confirm:hover,
.rsv-adj-confirm.rsv-adj-active {
    background: #d1fae5;
    border-color: #10b981;
    color: #065f46;
}

.rsv-adj-deliverable:hover,
.rsv-adj-deliverable.rsv-adj-active {
    background: #dbeafe;
    border-color: #3b82f6;
    color: #1e40af;
}

.rsv-adj-reject:hover,
.rsv-adj-reject.rsv-adj-active {
    background: #fee2e2;
    border-color: #ef4444;
    color: #991b1b;
}

.rsv-category-section,
.rsv-notes-section {
    margin-top: 12px;
}

.rsv-category-section label,
.rsv-notes-section label {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted, #999);
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
}

.rsv-category-select {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    font-size: 0.85rem;
    cursor: pointer;
}

.rsv-notes-input {
    width: 100%;
    min-height: 60px;
    padding: 8px 10px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    font-size: 0.85rem;
    resize: vertical;
    font-family: inherit;
}

.rsv-notes-input:focus,
.rsv-category-select:focus {
    outline: none;
    border-color: var(--accent-primary, #4f46e5);
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

/* Function Tags Section (v4.0.3) */
.rsv-tags-section {
    margin-top: 12px;
}
.rsv-tags-section label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.rsv-tags-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
}
.rsv-tag-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.rsv-tag-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}
.rsv-tag-remove {
    cursor: pointer;
    margin-left: 2px;
    font-size: 14px;
    opacity: 0.6;
    transition: opacity 0.15s;
}
.rsv-tag-remove:hover { opacity: 1; }
.rsv-add-tag-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 500;
    color: var(--accent, #3b82f6);
    background: transparent;
    border: 1px dashed var(--accent, #3b82f6);
    cursor: pointer;
    transition: all 0.2s;
}
.rsv-add-tag-btn:hover {
    color: #fff;
    background: var(--accent, #3b82f6);
    border-style: solid;
}
.rsv-add-tag-btn i { width: 13px; height: 13px; }

/* Custom Tag Dialog Overlay */
.rsv-custom-tag-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
    border-radius: 12px;
}
.rsv-custom-tag-dialog {
    background: var(--bg-surface, #fff);
    border: 1px solid var(--border-default, #ddd);
    border-radius: 10px;
    padding: 20px;
    width: 320px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.rsv-divider {
    height: 1px;
    background: var(--border-color, #e0e0e0);
    margin: 16px 0;
}

/* Toast notifications */
.rsv-toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10001;
    opacity: 0;
    transition: all 0.3s ease;
}

.rsv-toast-show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.rsv-toast-success {
    background: #10b981;
    color: white;
}

.rsv-toast-error {
    background: #ef4444;
    color: white;
}

.rsv-toast-info {
    background: #3b82f6;
    color: white;
}

/* Dark Mode Support */
.dark-mode .rsv-container,
[data-theme="dark"] .rsv-container {
    background: #1e1e1e;
    color: #e0e0e0;
}

.dark-mode .rsv-header,
.dark-mode .rsv-footer,
.dark-mode .rsv-source-header,
.dark-mode .rsv-source-actions,
[data-theme="dark"] .rsv-header,
[data-theme="dark"] .rsv-footer,
[data-theme="dark"] .rsv-source-header,
[data-theme="dark"] .rsv-source-actions {
    background: #252525;
    border-color: #3a3a3a;
}

.dark-mode .rsv-details-panel,
[data-theme="dark"] .rsv-details-panel {
    background: #1a1a1a;
    border-color: #3a3a3a;
}

.dark-mode .rsv-header h2,
.dark-mode .rsv-details-header h3,
.dark-mode .rsv-source-header h3,
[data-theme="dark"] .rsv-header h2,
[data-theme="dark"] .rsv-details-header h3,
[data-theme="dark"] .rsv-source-header h3 {
    color: #e0e0e0;
}

.dark-mode .rsv-counter,
.dark-mode .rsv-close,
[data-theme="dark"] .rsv-counter,
[data-theme="dark"] .rsv-close {
    color: #aaa;
}

.dark-mode .rsv-close:hover,
[data-theme="dark"] .rsv-close:hover {
    color: #fff;
}

/* Source Panel Dark Mode */
.dark-mode .rsv-source-panel,
[data-theme="dark"] .rsv-source-panel {
    border-color: #3a3a3a;
}

.dark-mode .rsv-source-info,
[data-theme="dark"] .rsv-source-info {
    background: #1a1a1a;
    border-color: #3a3a3a;
    color: #aaa;
}

/* Document Content Area - CRITICAL for readability */
.dark-mode .rsv-source-content,
[data-theme="dark"] .rsv-source-content {
    background: #1e1e1e;
    color: #e0e0e0;
}

.dark-mode .rsv-document-text,
[data-theme="dark"] .rsv-document-text {
    color: #e0e0e0;
}

.dark-mode .rsv-context-snippet,
[data-theme="dark"] .rsv-context-snippet {
    background: #252525;
    color: #e0e0e0;
}

.dark-mode .rsv-context-before,
.dark-mode .rsv-context-after,
[data-theme="dark"] .rsv-context-before,
[data-theme="dark"] .rsv-context-after {
    color: #aaa;
}

/* Role Highlights in Dark Mode */
.dark-mode .rsv-role-highlight,
[data-theme="dark"] .rsv-role-highlight {
    background: linear-gradient(180deg, rgba(255, 193, 7, 0.25) 0%, rgba(255, 193, 7, 0.4) 100%);
    color: #fff;
}

.dark-mode .rsv-role-highlight:hover,
[data-theme="dark"] .rsv-role-highlight:hover {
    background: linear-gradient(180deg, rgba(255, 193, 7, 0.4) 0%, rgba(255, 193, 7, 0.6) 100%);
}

.dark-mode .rsv-role-highlight.rsv-current,
[data-theme="dark"] .rsv-role-highlight.rsv-current {
    background: linear-gradient(180deg, rgba(255, 152, 0, 0.5) 0%, rgba(255, 152, 0, 0.7) 100%);
    box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.4);
    color: #fff;
}

.dark-mode .rsv-doc-selector,
[data-theme="dark"] .rsv-doc-selector {
    background: #2a2a2a;
    border-color: #444;
    color: #e0e0e0;
}

.dark-mode .rsv-highlight,
[data-theme="dark"] .rsv-highlight {
    background: linear-gradient(180deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 193, 7, 0.3) 100%);
}

.dark-mode .rsv-variant-tag,
.dark-mode .rsv-doc-mentions,
[data-theme="dark"] .rsv-variant-tag,
[data-theme="dark"] .rsv-doc-mentions {
    background: #3a3a3a;
    color: #ddd;
}

/* Details Panel Dark Mode */
.dark-mode .rsv-details-content,
[data-theme="dark"] .rsv-details-content {
    color: #e0e0e0;
}

.dark-mode .rsv-detail-section label,
[data-theme="dark"] .rsv-detail-section label {
    color: #888;
}

.dark-mode .rsv-detail-value,
[data-theme="dark"] .rsv-detail-value {
    color: #e0e0e0;
}

.dark-mode .rsv-responsibilities ul,
.dark-mode .rsv-responsibilities li,
[data-theme="dark"] .rsv-responsibilities ul,
[data-theme="dark"] .rsv-responsibilities li {
    color: #d0d0d0;
}

/* Document List Dark Mode */
.dark-mode .rsv-doc-item,
[data-theme="dark"] .rsv-doc-item {
    color: #d0d0d0;
}

.dark-mode .rsv-doc-item:hover,
[data-theme="dark"] .rsv-doc-item:hover {
    background: #2a2a2a;
}

.dark-mode .rsv-doc-item.active,
[data-theme="dark"] .rsv-doc-item.active {
    background: rgba(59, 130, 246, 0.15);
    border-color: #3b82f6;
}

/* Buttons Dark Mode */
.dark-mode .rsv-btn,
[data-theme="dark"] .rsv-btn {
    background: #2a2a2a;
    border-color: #444;
    color: #e0e0e0;
}

.dark-mode .rsv-btn:hover:not(:disabled),
[data-theme="dark"] .rsv-btn:hover:not(:disabled) {
    background: #3a3a3a;
}

/* Adjudication Section Dark Mode */
.dark-mode .rsv-adjudication-section,
[data-theme="dark"] .rsv-adjudication-section {
    background: #252525;
}

.dark-mode .rsv-adjudication-section label,
[data-theme="dark"] .rsv-adjudication-section label {
    color: #888;
}

.dark-mode .rsv-adj-btn,
[data-theme="dark"] .rsv-adj-btn {
    background: #2a2a2a;
    border-color: #444;
    color: #d0d0d0;
}

.dark-mode .rsv-category-select,
.dark-mode .rsv-notes-input,
[data-theme="dark"] .rsv-category-select,
[data-theme="dark"] .rsv-notes-input {
    background: #2a2a2a;
    border-color: #444;
    color: #e0e0e0;
}

.dark-mode .rsv-category-section label,
.dark-mode .rsv-notes-section label,
.dark-mode .rsv-tags-section label,
[data-theme="dark"] .rsv-category-section label,
[data-theme="dark"] .rsv-notes-section label,
[data-theme="dark"] .rsv-tags-section label {
    color: #777;
}

.dark-mode .rsv-custom-tag-dialog,
[data-theme="dark"] .rsv-custom-tag-dialog {
    background: #1e1e1e;
    border-color: #444;
}
.dark-mode .rsv-custom-tag-dialog input,
.dark-mode .rsv-custom-tag-dialog select,
[data-theme="dark"] .rsv-custom-tag-dialog input,
[data-theme="dark"] .rsv-custom-tag-dialog select {
    background: #2a2a2a;
    border-color: #444;
    color: #e0e0e0;
}

.dark-mode .rsv-divider,
[data-theme="dark"] .rsv-divider {
    background: #3a3a3a;
}

/* Shortcuts/Footer Dark Mode */
.dark-mode .rsv-shortcuts,
[data-theme="dark"] .rsv-shortcuts {
    color: #888;
}

.dark-mode .rsv-shortcuts kbd,
[data-theme="dark"] .rsv-shortcuts kbd {
    background: #2a2a2a;
    border-color: #444;
    color: #ccc;
}

/* No Document / Loading States Dark Mode */
.dark-mode .rsv-no-document,
.dark-mode .rsv-loading,
[data-theme="dark"] .rsv-no-document,
[data-theme="dark"] .rsv-loading {
    color: #888;
}

.dark-mode .rsv-hint,
[data-theme="dark"] .rsv-hint {
    color: #777;
}

/* Context Status Dark Mode */
.dark-mode .rsv-context-status,
[data-theme="dark"] .rsv-context-status {
    color: #aaa;
}
        `;

        document.head.appendChild(styles);
    }

    // ============================================================
    // AUTO-INITIALIZE
    // ============================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================================
    // PUBLIC INTERFACE
    // ============================================================

    return {
        VERSION,
        open,
        close,
        init
    };
})();

console.log('[TWR RoleSourceViewer] Module loaded v' + TWR.RoleSourceViewer.VERSION);
