/**
 * AEGIS - Issue Families Feature Module
 * 
 * Extracted in v3.0.21 from app.js (~350 LOC)
 * 
 * Contains:
 * - Issue family detection and grouping
 * - Pareto view (inline families panel)
 * - Bulk actions modal for family operations
 * - Family filtering and selection
 * - Modal creation for families UI
 * 
 * Dependencies:
 * - TWR.Utils (escapeHtml, truncate)
 * - TWR.State (State object)
 * - TWR.Modals (toast, showModal)
 * 
 * Used by:
 * - Families panel (inline Pareto view)
 * - Toolbar families button
 * - Triage mode (family info display)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Families = (function() {
    // ============================================================
    // HELPER FUNCTIONS (use modules or fallback)
    // ============================================================
    
    function escapeHtml(str) {
        if (typeof TWR?.Utils?.escapeHtml === 'function') {
            return TWR.Utils.escapeHtml(str);
        }
        if (typeof window.escapeHtml === 'function') {
            return window.escapeHtml(str);
        }
        // Inline fallback
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML; // SAFE: escapeHtml function output
    }
    
    function truncate(str, maxLen) {
        if (typeof TWR?.Utils?.truncate === 'function') {
            return TWR.Utils.truncate(str, maxLen);
        }
        if (typeof window.truncate === 'function') {
            return window.truncate(str, maxLen);
        }
        // Inline fallback
        if (!str || str.length <= maxLen) return str || '';
        return str.substring(0, maxLen - 1) + '…';
    }
    
    function toast(type, message) {
        if (typeof TWR?.Modals?.toast === 'function') {
            return TWR.Modals.toast(type, message);
        }
        if (typeof window.toast === 'function') {
            return window.toast(type, message);
        }
        console.log(`[${type}] ${message}`);
    }
    
    function showModal(id) {
        if (typeof TWR?.Modals?.showModal === 'function') {
            return TWR.Modals.showModal(id);
        }
        if (typeof window.showModal === 'function') {
            return window.showModal(id);
        }
        // Basic fallback
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    function getState() {
        return window.State || window.TWR?.State?.State || {};
    }
    
    // ============================================================
    // ISSUE FAMILY DETECTION
    // ============================================================
    
    /**
     * Extract a generic pattern from a message (for grouping similar messages)
     * @param {string} message - The issue message to extract pattern from
     * @returns {string|null} The extracted pattern or null
     */
    function extractMessagePattern(message) {
        if (!message || message.length < 10) return null;
        
        // Remove specific words/numbers, keep structure
        return message
            .replace(/["']([^"']+)["']/g, '"X"')  // Replace quoted text
            .replace(/\d+/g, 'N')                  // Replace numbers
            .replace(/\s+/g, ' ')                  // Normalize whitespace
            .trim()
            .substring(0, 60);
    }
    
    /**
     * Build issue families by detecting similar patterns
     * Groups issues by: flagged_text exact match, message pattern, rule_id
     * @returns {Map} The issue families map
     */
    function buildIssueFamilies() {
        const state = getState();
        
        if (!state.workflow) {
            console.warn('[TWR.Families] State.workflow not initialized');
            return new Map();
        }
        
        state.workflow.issueFamilies.clear();
        
        const families = {
            byFlaggedText: new Map(),  // exact flagged_text -> [issues]
            byPattern: new Map(),       // message pattern -> [issues]
            byRule: new Map()           // rule_id -> [issues]
        };
        
        state.issues.forEach((issue, idx) => {
            const issueRef = { idx, issue_id: issue.issue_id, issue };
            
            // Group by exact flagged text (most actionable)
            if (issue.flagged_text && issue.flagged_text.length > 2) {
                const key = issue.flagged_text.toLowerCase().trim();
                if (!families.byFlaggedText.has(key)) {
                    families.byFlaggedText.set(key, []);
                }
                families.byFlaggedText.get(key).push(issueRef);
            }
            
            // Group by rule_id if present
            if (issue.rule_id) {
                if (!families.byRule.has(issue.rule_id)) {
                    families.byRule.set(issue.rule_id, []);
                }
                families.byRule.get(issue.rule_id).push(issueRef);
            }
            
            // Group by message pattern (strip numbers and specifics)
            const pattern = extractMessagePattern(issue.message || '');
            if (pattern) {
                if (!families.byPattern.has(pattern)) {
                    families.byPattern.set(pattern, []);
                }
                families.byPattern.get(pattern).push(issueRef);
            }
        });
        
        // Only keep families with 2+ members (actual duplicates)
        families.byFlaggedText.forEach((members, key) => {
            if (members.length >= 2) {
                state.workflow.issueFamilies.set(`text:${key}`, {
                    type: 'flagged_text',
                    pattern: key,
                    displayName: `"${truncate(key, 30)}" (${members.length}×)`,
                    members,
                    count: members.length
                });
            }
        });
        
        families.byRule.forEach((members, key) => {
            if (members.length >= 3) { // Higher threshold for rule groups
                state.workflow.issueFamilies.set(`rule:${key}`, {
                    type: 'rule',
                    pattern: key,
                    displayName: `Rule ${key} (${members.length}×)`,
                    members,
                    count: members.length
                });
            }
        });
        
        return state.workflow.issueFamilies;
    }
    
    // ============================================================
    // FAMILY DISPLAY HELPERS
    // ============================================================
    
    /**
     * Get a clean display name for a family
     * @param {Object} family - The family object
     * @returns {string} The display name
     */
    function getFamilyDisplayName(family) {
        if (family.type === 'flagged_text') {
            return `"${truncate(family.pattern, 35)}"`;
        } else if (family.type === 'rule') {
            // Try to get a human-readable name from the first issue's category
            const sample = family.members[0]?.issue;
            if (sample?.category) {
                return sample.category.replace(/_/g, ' ');
            }
            return `Rule: ${family.pattern}`;
        }
        return family.displayName || family.pattern;
    }
    
    // ============================================================
    // INLINE FAMILIES PANEL (PARETO VIEW)
    // ============================================================
    
    /**
     * Show inline families panel above issue list (Pareto view)
     */
    function showInlineFamiliesPanel() {
        buildIssueFamilies();
        
        const state = getState();
        const panel = document.getElementById('families-panel');
        if (!panel) return;
        
        if (state.workflow.issueFamilies.size === 0) {
            panel.style.display = 'none';
            return;
        }
        
        // Sort families by count (most common first) - top 8 for inline view
        const sortedFamilies = [...state.workflow.issueFamilies.entries()]
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 8);
        
        // Update count badge
        const countBadge = document.getElementById('families-panel-count');
        if (countBadge) {
            countBadge.textContent = state.workflow.issueFamilies.size;
        }
        
        // Calculate summary stats
        const totalFamilies = state.workflow.issueFamilies.size;
        const totalIssuesInFamilies = [...state.workflow.issueFamilies.values()]
            .reduce((sum, f) => sum + f.count, 0);
        
        const summaryEl = document.getElementById('families-panel-summary');
        if (summaryEl) {
            const pct = Math.round((totalIssuesInFamilies / state.issues.length) * 100);
            summaryEl.textContent = `${totalIssuesInFamilies} issues (${pct}%) in ${totalFamilies} patterns`;
        }
        
        renderInlineFamilyList(sortedFamilies);
        panel.style.display = 'block';
    }
    
    /**
     * Render the inline family list (Pareto view)
     * @param {Array} families - Array of [key, family] entries
     */
    function renderInlineFamilyList(families) {
        const state = getState();
        const container = document.getElementById('families-inline-list');
        if (!container) return;
        
        const maxCount = families.length > 0 ? families[0][1].count : 1;
        
        // SAFE: all dynamic content escaped via escapeHtml()
        container.innerHTML = families.map(([key, family]) => {
            const action = state.workflow.familyActions.get(key);
            const actionClass = action ? `family-${action.action} family-actioned` : '';
            const sample = family.members[0]?.issue;
            const countClass = family.count >= 20 ? 'count-high' : family.count >= 10 ? 'count-medium' : '';
            const progressPct = Math.round((family.count / maxCount) * 100);
            
            const actionLabel = action ? `
                <span class="family-action-label action-${action.action}">
                    ${action.action === 'keep' ? '✓ Kept' : action.action === 'suppress' ? '⊘ Suppressed' : '✓ Fixed'}
                </span>
            ` : '';
            
            return `
                <div class="family-inline-row ${actionClass}" data-family-key="${escapeHtml(key)}">
                    <div class="family-inline-info" onclick="TWR.Families.filterByFamily('${escapeHtml(key)}')" title="Click to filter issue list">
                        <div class="family-inline-count ${countClass}">${family.count}×</div>
                        <div class="family-inline-details">
                            <div class="family-inline-pattern">${escapeHtml(getFamilyDisplayName(family))}</div>
                            <div class="family-inline-sample">${sample ? escapeHtml(truncate(sample.message || '', 60)) : ''}</div>
                            <div class="family-progress-bar">
                                <div class="family-progress-fill" style="width: ${progressPct}%"></div>
                            </div>
                        </div>
                    </div>
                    ${action ? actionLabel : `
                    <div class="family-inline-actions">
                        <button class="btn btn-xs btn-ghost btn-action-keep" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'keep'); event.stopPropagation();" title="Keep all">
                            <i data-lucide="check"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost btn-action-suppress" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'suppress'); event.stopPropagation();" title="Suppress all">
                            <i data-lucide="eye-off"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost btn-action-fixed" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'fixed'); event.stopPropagation();" title="Mark all fixed">
                            <i data-lucide="check-circle"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost btn-action-select" onclick="TWR.Families.selectFamily('${escapeHtml(key)}'); event.stopPropagation();" title="Select all">
                            <i data-lucide="list-plus"></i>
                        </button>
                    </div>
                    `}
                </div>
            `;
        }).join('');
        
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }
    
    // ============================================================
    // FAMILIES MODAL (FULL VIEW)
    // ============================================================
    
    /**
     * Create the families modal dynamically if needed
     */
    function createFamiliesModal() {
        if (document.getElementById('modal-families')) return;
        
        const modal = document.createElement('div');
        modal.className = 'modal modal-lg';
        modal.id = 'modal-families';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        // SAFE: static HTML structure
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i data-lucide="copy"></i> Issue Families (Bulk Actions)</h3>
                    <button class="btn btn-ghost modal-close" aria-label="Close"><i data-lucide="x"></i></button>
                </div>
                <div class="modal-body">
                    <p class="text-muted" id="family-summary">Loading...</p>
                    <div class="family-list" id="family-list"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-ghost modal-close">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    /**
     * Show issue families panel for bulk actions (full modal)
     */
    function showIssueFamilies() {
        buildIssueFamilies();
        
        const state = getState();
        
        if (state.workflow.issueFamilies.size === 0) {
            toast('info', 'No issue families detected (no repeated patterns)');
            return;
        }
        
        // Sort families by count (most common first)
        const sortedFamilies = [...state.workflow.issueFamilies.entries()]
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 20); // Top 20 families
        
        const familyList = document.getElementById('family-list');
        if (!familyList) {
            // Create the families modal if it doesn't exist
            createFamiliesModal();
        }
        
        renderFamilyList(sortedFamilies);
        showModal('modal-families');
    }
    
    /**
     * Render the list of issue families in the modal
     * @param {Array} families - Array of [key, family] entries
     */
    function renderFamilyList(families) {
        const state = getState();
        const container = document.getElementById('family-list');
        if (!container) return;
        
        // SAFE: all dynamic content escaped via escapeHtml()
        container.innerHTML = families.map(([key, family]) => {
            const action = state.workflow.familyActions.get(key);
            const actionClass = action ? `family-${action.action}` : '';
            const sample = family.members[0]?.issue;
            
            return `
                <div class="family-row ${actionClass}" data-family-key="${escapeHtml(key)}">
                    <div class="family-info">
                        <div class="family-header">
                            <span class="family-count">${family.count}×</span>
                            <span class="family-pattern">${escapeHtml(family.displayName)}</span>
                        </div>
                        <div class="family-sample text-muted">
                            ${sample ? escapeHtml(truncate(sample.message || '', 80)) : ''}
                        </div>
                    </div>
                    <div class="family-actions">
                        <button class="btn btn-xs btn-ghost" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'keep')" title="Keep all">
                            <i data-lucide="check"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'suppress')" title="Suppress all">
                            <i data-lucide="eye-off"></i>
                        </button>
                        <button class="btn btn-xs btn-ghost" onclick="TWR.Families.familyAction('${escapeHtml(key)}', 'fixed')" title="Mark all fixed">
                            <i data-lucide="check-circle"></i>
                        </button>
                        <button class="btn btn-xs btn-primary" onclick="TWR.Families.selectFamily('${escapeHtml(key)}')" title="Select all in list">
                            <i data-lucide="list-plus"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
        
        // Update summary
        const totalFamilies = families.length;
        const totalIssues = families.reduce((sum, [_, f]) => sum + f.count, 0);
        const summaryEl = document.getElementById('family-summary');
        if (summaryEl) {
            summaryEl.textContent = 
                `${totalFamilies} pattern${totalFamilies !== 1 ? 's' : ''} affecting ${totalIssues} issues`;
        }
    }
    
    // ============================================================
    // FAMILY ACTIONS
    // ============================================================
    
    /**
     * Apply action to all issues in a family
     * @param {string} familyKey - The family key
     * @param {string} action - 'keep' | 'suppress' | 'fixed'
     */
    function familyAction(familyKey, action) {
        const state = getState();
        const family = state.workflow.issueFamilies.get(familyKey);
        if (!family) return;
        
        // Record the family action
        state.workflow.familyActions.set(familyKey, { action, timestamp: new Date().toISOString() });
        
        // Apply to all members
        family.members.forEach(({ issue_id, issue, idx }) => {
            // Log the review decision if the function is available
            if (typeof window.logReviewDecision === 'function') {
                window.logReviewDecision(
                    issue_id || idx, 
                    action, 
                    `Bulk action on family: ${getFamilyDisplayName(family)}`, 
                    'Family'
                );
            }
            
            if (action === 'suppress') {
                // Add to baseline via toggleBaseline if available
                if (typeof window.toggleBaseline === 'function') {
                    window.toggleBaseline(idx);
                }
            }
        });
        
        toast('success', `${action === 'keep' ? 'Kept' : action === 'suppress' ? 'Suppressed' : 'Fixed'} ${family.count} issues`);
        
        // Refresh both the inline panel and modal
        const sortedFamilies = [...state.workflow.issueFamilies.entries()]
            .sort((a, b) => b[1].count - a[1].count);
        
        renderInlineFamilyList(sortedFamilies.slice(0, 8));
        renderFamilyList(sortedFamilies.slice(0, 20));
    }
    
    /**
     * Select all issues in a family (adds to main selection)
     * @param {string} familyKey - The family key
     */
    function selectFamily(familyKey) {
        const state = getState();
        const family = state.workflow.issueFamilies.get(familyKey);
        if (!family) return;
        
        family.members.forEach(({ issue_id, idx }) => {
            const id = issue_id || idx;
            state.selectedIssues.add(id);
        });
        
        // Update UI via app.js functions if available
        if (typeof window.updateSelectionUI === 'function') {
            window.updateSelectionUI();
        }
        if (typeof window.renderIssuesList === 'function') {
            window.renderIssuesList();
        }
        
        toast('success', `Selected ${family.count} issues`);
    }
    
    // ============================================================
    // FAMILY FILTERING
    // ============================================================
    
    /**
     * Filter issue list to show only issues from a specific family
     * @param {string} familyKey - The family key
     */
    function filterByFamily(familyKey) {
        const state = getState();
        const family = state.workflow.issueFamilies.get(familyKey);
        if (!family) return;
        
        // Get all issue indices in this family
        const familyIndices = new Set(family.members.map(m => m.idx));
        
        // Apply custom filter
        state.filters.customFilter = (issue, idx) => familyIndices.has(idx);
        state.filters.customFilterLabel = getFamilyDisplayName(family);
        
        // Apply filters and re-render via app.js functions if available
        if (typeof window.applyFilters === 'function') {
            window.applyFilters();
        }
        if (typeof window.renderIssuesList === 'function') {
            window.renderIssuesList();
        }
        
        // Show filter chip
        if (typeof window.updateFilterChips === 'function') {
            window.updateFilterChips();
        }
        toast('info', `Showing ${family.count} issues in pattern "${truncate(getFamilyDisplayName(family), 30)}"`);
    }
    
    /**
     * Clear custom family filter
     */
    function clearFamilyFilter() {
        const state = getState();
        state.filters.customFilter = null;
        state.filters.customFilterLabel = null;
        
        // Apply filters and re-render via app.js functions if available
        if (typeof window.applyFilters === 'function') {
            window.applyFilters();
        }
        if (typeof window.renderIssuesList === 'function') {
            window.renderIssuesList();
        }
        if (typeof window.updateFilterChips === 'function') {
            window.updateFilterChips();
        }
    }
    
    // ============================================================
    // INITIALIZATION
    // ============================================================
    
    /**
     * Initialize families panel toggle
     */
    function initFamiliesPanel() {
        const toggle = document.getElementById('families-panel-toggle');
        const panel = document.getElementById('families-panel');
        
        if (toggle && panel) {
            toggle.addEventListener('click', () => {
                panel.classList.toggle('expanded');
            });
        }
    }
    
    /**
     * Initialize families module (call on DOM ready)
     */
    function init() {
        initFamiliesPanel();
        createFamiliesModal();
    }
    
    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', init);
    
    // ============================================================
    // STATE ACCESSORS
    // ============================================================
    
    /**
     * Get the current issue families map
     * @returns {Map} The issue families map
     */
    function getIssueFamilies() {
        const state = getState();
        return state.workflow?.issueFamilies || new Map();
    }
    
    /**
     * Get family actions map
     * @returns {Map} The family actions map
     */
    function getFamilyActions() {
        const state = getState();
        return state.workflow?.familyActions || new Map();
    }
    
    /**
     * Get family count
     * @returns {number} Number of detected families
     */
    function getFamilyCount() {
        const state = getState();
        return state.workflow?.issueFamilies?.size || 0;
    }
    
    // ============================================================
    // PUBLIC API
    // ============================================================
    
    return {
        // Core family functions
        buildIssueFamilies: buildIssueFamilies,
        showIssueFamilies: showIssueFamilies,
        showInlineFamiliesPanel: showInlineFamiliesPanel,
        
        // Family actions
        familyAction: familyAction,
        selectFamily: selectFamily,
        
        // Filtering
        filterByFamily: filterByFamily,
        clearFamilyFilter: clearFamilyFilter,
        
        // Rendering
        renderFamilyList: renderFamilyList,
        renderInlineFamilyList: renderInlineFamilyList,
        
        // Helpers
        getFamilyDisplayName: getFamilyDisplayName,
        extractMessagePattern: extractMessagePattern,
        createFamiliesModal: createFamiliesModal,
        
        // State accessors
        getIssueFamilies: getIssueFamilies,
        getFamilyActions: getFamilyActions,
        getFamilyCount: getFamilyCount,
        
        // Initialization
        init: init,
        initFamiliesPanel: initFamiliesPanel
    };
})();

// ============================================================
// GLOBAL ALIASES FOR BACKWARD COMPATIBILITY
// ============================================================

// Core family functions
window.buildIssueFamilies = TWR.Families.buildIssueFamilies;
window.showIssueFamilies = TWR.Families.showIssueFamilies;
window.showInlineFamiliesPanel = TWR.Families.showInlineFamiliesPanel;

// Family actions
window.familyAction = TWR.Families.familyAction;
window.selectFamily = TWR.Families.selectFamily;

// Filtering
window.filterByFamily = TWR.Families.filterByFamily;
window.clearFamilyFilter = TWR.Families.clearFamilyFilter;

// Helpers
window.getFamilyDisplayName = TWR.Families.getFamilyDisplayName;
window.extractMessagePattern = TWR.Families.extractMessagePattern;
window.createFamiliesModal = TWR.Families.createFamiliesModal;

console.log('[TWR] Families module loaded');
