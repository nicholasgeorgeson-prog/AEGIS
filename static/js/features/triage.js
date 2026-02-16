/**
 * AEGIS - Triage Feature Module
 * 
 * Extracted in v3.0.20 from app.js (~200 LOC)
 * 
 * Contains:
 * - Triage mode state management
 * - Triage modal display and navigation
 * - Keyboard controls for rapid issue review
 * - Issue family info display in triage mode
 * - Integration with review logging
 * 
 * Dependencies:
 * - TWR.Utils (escapeHtml)
 * - TWR.State (State, FilterState objects)
 * - TWR.Modals (toast, showModal, closeModals)
 * 
 * Used by:
 * - Toolbar triage button
 * - Keyboard shortcut (T)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Triage = (function() {
    // ============================================================
    // TRIAGE STATE
    // ============================================================
    
    const TriageState = {
        isActive: false,
        currentIndex: 0,
        issues: [],
        triaged: new Map() // index -> 'keep' | 'suppress' | 'fixed'
    };
    
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
    
    function closeModals() {
        if (typeof TWR?.Modals?.closeModals === 'function') {
            return TWR.Modals.closeModals();
        }
        if (typeof window.closeModals === 'function') {
            return window.closeModals();
        }
        // Basic fallback
        document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
        document.body.style.overflow = '';
    }
    
    function getState() {
        return window.State || window.TWR?.State?.State || {};
    }
    
    // ============================================================
    // TRIAGE MODE FUNCTIONS
    // ============================================================
    
    /**
     * Show the triage mode modal for rapid issue review
     */
    function showTriageMode() {
        const state = getState();
        
        if (!state.filteredIssues || state.filteredIssues.length === 0) {
            toast('warning', 'No issues to triage');
            return;
        }
        
        TriageState.isActive = true;
        TriageState.currentIndex = 0;
        TriageState.issues = [...state.filteredIssues];
        
        showModal('modal-triage');
        updateTriageDisplay();
        
        // Add keyboard listener
        document.addEventListener('keydown', handleTriageKeyboard);
    }
    
    /**
     * Close triage mode and clean up
     */
    function closeTriageMode() {
        TriageState.isActive = false;
        document.removeEventListener('keydown', handleTriageKeyboard);
        closeModals();
    }
    
    /**
     * Handle keyboard shortcuts in triage mode
     */
    function handleTriageKeyboard(e) {
        if (!TriageState.isActive) return;
        
        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                navigateTriage(-1);
                break;
            case 'ArrowRight':
                e.preventDefault();
                navigateTriage(1);
                break;
            case 'k':
            case 'K':
                e.preventDefault();
                triageAction('keep');
                break;
            case 's':
            case 'S':
                e.preventDefault();
                triageAction('suppress');
                break;
            case 'f':
            case 'F':
                e.preventDefault();
                triageAction('fixed');
                break;
            case 'Escape':
                e.preventDefault();
                closeTriageMode();
                break;
        }
    }
    
    /**
     * Navigate to previous/next issue in triage
     * @param {number} direction - -1 for previous, 1 for next
     */
    function navigateTriage(direction) {
        const newIndex = TriageState.currentIndex + direction;
        if (newIndex >= 0 && newIndex < TriageState.issues.length) {
            TriageState.currentIndex = newIndex;
            updateTriageDisplay();
        }
    }
    
    /**
     * Apply a triage action to the current issue
     * @param {string} action - 'keep' | 'suppress' | 'fixed'
     */
    function triageAction(action) {
        const issue = TriageState.issues[TriageState.currentIndex];
        if (!issue) return;
        
        // Log the review decision if the function is available
        if (typeof window.logReviewDecision === 'function') {
            window.logReviewDecision(
                issue.issue_id || TriageState.currentIndex,
                action,
                '',
                'Triage'
            );
        }
        
        TriageState.triaged.set(TriageState.currentIndex, action);
        
        if (action === 'suppress') {
            // Add to baseline via toggleBaseline if available
            const state = getState();
            if (typeof window.toggleBaseline === 'function' && state.issues) {
                const issueIndex = state.issues.indexOf(issue);
                if (issueIndex >= 0) {
                    window.toggleBaseline(issueIndex);
                }
            }
        } else if (action === 'fixed') {
            toast('success', 'Marked as fixed');
        }
        
        // Auto-advance to next issue
        if (TriageState.currentIndex < TriageState.issues.length - 1) {
            TriageState.currentIndex++;
            updateTriageDisplay();
        } else {
            // Completed all issues
            toast('success', `Triage complete! Reviewed ${TriageState.issues.length} issues.`);
            closeTriageMode();
        }
    }
    
    /**
     * Update the triage modal display with current issue
     */
    function updateTriageDisplay() {
        const issue = TriageState.issues[TriageState.currentIndex];
        if (!issue) return;
        
        // Update progress counter
        const currentEl = document.getElementById('triage-current');
        const totalEl = document.getElementById('triage-total');
        if (currentEl) currentEl.textContent = TriageState.currentIndex + 1;
        if (totalEl) totalEl.textContent = TriageState.issues.length;
        
        // Update progress bar
        const progress = ((TriageState.currentIndex + 1) / TriageState.issues.length) * 100;
        const progressFill = document.getElementById('triage-progress-fill');
        if (progressFill) progressFill.style.width = `${progress}%`;
        
        // Update severity badge
        const sevEl = document.getElementById('triage-severity');
        if (sevEl) {
            sevEl.textContent = issue.severity || 'Info';
            sevEl.className = `severity-badge ${(issue.severity || 'info').toLowerCase()}`;
        }
        
        // Update category
        const catEl = document.getElementById('triage-category');
        if (catEl) catEl.textContent = issue.category || '';
        
        // Update message
        const msgEl = document.getElementById('triage-message');
        if (msgEl) msgEl.textContent = issue.message || '';
        
        // Update context with highlighted flagged text
        const contextText = document.getElementById('triage-context-text');
        const contextSection = document.getElementById('triage-context');
        if (contextText && contextSection) {
            if (issue.flagged_text || issue.context) {
                const text = issue.context || '';
                const flagged = issue.flagged_text || '';
                
                if (flagged && text.includes(flagged)) {
                    // SAFE: text and flagged both escaped via escapeHtml()
                    contextText.innerHTML = escapeHtml(text).replace(
                        escapeHtml(flagged),
                        `<mark>${escapeHtml(flagged)}</mark>`
                    );
                } else {
                    contextText.textContent = flagged || text || 'No context available';
                }
                contextSection.style.display = 'block';
            } else {
                contextSection.style.display = 'none';
            }
        }
        
        // Update suggestion
        const suggSection = document.getElementById('triage-suggestion-section');
        const suggText = document.getElementById('triage-suggestion-text');
        if (suggSection && suggText) {
            if (issue.suggestion) {
                suggText.textContent = issue.suggestion;
                suggSection.style.display = 'block';
            } else {
                suggSection.style.display = 'none';
            }
        }
        
        // Update navigation buttons
        const prevBtn = document.getElementById('btn-triage-prev');
        const nextBtn = document.getElementById('btn-triage-next');
        if (prevBtn) prevBtn.disabled = TriageState.currentIndex <= 0;
        if (nextBtn) nextBtn.disabled = TriageState.currentIndex >= TriageState.issues.length - 1;
        
        // Show family info if this issue belongs to a family
        updateTriageFamilyInfo(issue);
    }
    
    /**
     * Show family info in triage mode if issue belongs to a pattern family
     * @param {Object} issue - The current issue being triaged
     */
    function updateTriageFamilyInfo(issue) {
        const familyInfo = document.getElementById('triage-family-info');
        if (!familyInfo) return;
        
        const state = getState();
        
        // Find if this issue belongs to a family
        let belongsTo = null;
        if (state.workflow?.issueFamilies) {
            for (const [key, family] of state.workflow.issueFamilies) {
                if (family.members && family.members.some(m => m.issue_id === issue.issue_id)) {
                    belongsTo = family;
                    break;
                }
            }
        }
        
        if (belongsTo && belongsTo.count > 1) {
            // SAFE: static HTML with numeric value only
            familyInfo.innerHTML = `
                <div class="family-badge" title="This issue is part of a pattern">
                    <i data-lucide="copy"></i>
                    ${belongsTo.count - 1} similar issue${belongsTo.count > 2 ? 's' : ''}
                </div>
            `;
            familyInfo.style.display = 'block';
            
            // Refresh Lucide icons if available
            if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch(e) {}
            }
        } else {
            familyInfo.style.display = 'none';
        }
    }
    
    // ============================================================
    // STATE ACCESSORS
    // ============================================================
    
    /**
     * Get the current triage state (for external access if needed)
     */
    function getTriageState() {
        return {
            isActive: TriageState.isActive,
            currentIndex: TriageState.currentIndex,
            totalIssues: TriageState.issues.length,
            triagedCount: TriageState.triaged.size
        };
    }
    
    /**
     * Check if triage mode is currently active
     */
    function isTriageActive() {
        return TriageState.isActive;
    }
    
    /**
     * Get triaged issues map
     */
    function getTriagedMap() {
        return new Map(TriageState.triaged);
    }
    
    /**
     * Reset triage state (useful for starting fresh)
     */
    function resetTriageState() {
        TriageState.isActive = false;
        TriageState.currentIndex = 0;
        TriageState.issues = [];
        TriageState.triaged.clear();
    }
    
    // ============================================================
    // PUBLIC API
    // ============================================================
    
    return {
        // Core triage functions
        showTriageMode: showTriageMode,
        closeTriageMode: closeTriageMode,
        navigateTriage: navigateTriage,
        triageAction: triageAction,
        updateTriageDisplay: updateTriageDisplay,
        updateTriageFamilyInfo: updateTriageFamilyInfo,
        
        // State accessors
        getTriageState: getTriageState,
        isTriageActive: isTriageActive,
        getTriagedMap: getTriagedMap,
        resetTriageState: resetTriageState,
        
        // Internal state reference (for debugging)
        _state: TriageState
    };
})();

// ============================================================
// GLOBAL ALIASES FOR BACKWARD COMPATIBILITY
// ============================================================

// Core triage functions
window.showTriageMode = TWR.Triage.showTriageMode;
window.closeTriageMode = TWR.Triage.closeTriageMode;
window.navigateTriage = TWR.Triage.navigateTriage;
window.triageAction = TWR.Triage.triageAction;
window.updateTriageDisplay = TWR.Triage.updateTriageDisplay;
window.updateTriageFamilyInfo = TWR.Triage.updateTriageFamilyInfo;

// Expose TriageState for backward compatibility with any code that accesses it directly
window.TriageState = TWR.Triage._state;

console.log('[TWR] Triage module loaded');
