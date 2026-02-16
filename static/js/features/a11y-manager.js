// v3.0.97: Fix Assistant v2 - Accessibility Manager
// WP8: Focus management, screen reader support, keyboard navigation
// ═══════════════════════════════════════════════════════════════════════════════

const A11yManager = (function() {
    'use strict';
    
    let modalEl = null;
    let previousFocus = null;
    let announcer = null;
    let focusableElements = [];
    let firstFocusable = null;
    let lastFocusable = null;
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Initialize accessibility features for modal
     * @param {HTMLElement} modal - The modal element
     */
    function init(modal) {
        modalEl = modal;
        previousFocus = document.activeElement;
        
        // Create live region for announcements
        createAnnouncer();
        
        // Setup focus trap
        updateFocusableElements();
        setupFocusTrap();
        
        // Focus first element
        focusFirst();
        
        // Announce modal opened
        announce('Fix Assistant opened. Use arrow keys to navigate fixes, A to accept, R to reject.');
    }
    
    /**
     * Clean up and restore focus
     */
    function destroy() {
        // Remove focus trap listener
        if (modalEl) {
            modalEl.removeEventListener('keydown', handleFocusTrap);
        }
        
        // Remove announcer
        if (announcer && announcer.parentNode) {
            announcer.parentNode.removeChild(announcer);
        }
        announcer = null;
        
        // Restore focus to previous element
        if (previousFocus && previousFocus.focus) {
            previousFocus.focus();
        }
        
        // Reset state
        modalEl = null;
        focusableElements = [];
        firstFocusable = null;
        lastFocusable = null;
    }
    
    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     * @param {string} priority - 'polite' (default) or 'assertive'
     */
    function announce(message, priority = 'polite') {
        if (!announcer) return;
        
        announcer.setAttribute('aria-live', priority);
        
        // Clear and set (ensures announcement even if same text)
        announcer.textContent = '';
        setTimeout(() => {
            announcer.textContent = message;
        }, 50);
        
        // Clear after delay to avoid stale announcements
        setTimeout(() => {
            announcer.textContent = '';
        }, 3000);
    }
    
    /**
     * Announce current fix details for screen readers
     * @param {Object} fix - Fix object with category, flagged_text, suggestion, confidence_tier
     * @param {number} current - Current index (1-based)
     * @param {number} total - Total count
     */
    function announceFix(fix, current, total) {
        const parts = [
            `Fix ${current} of ${total}.`,
            `${fix.category} issue.`,
            `"${fix.flagged_text}" should be "${fix.suggestion}".`,
            `Confidence: ${fix.confidence_tier}.`
        ];
        announce(parts.join(' '), 'polite');
    }
    
    /**
     * Announce decision result
     * @param {string} decision - 'accepted' | 'rejected' | 'skipped'
     */
    function announceDecision(decision) {
        const messages = {
            accepted: 'Fix accepted.',
            rejected: 'Fix rejected.',
            skipped: 'Fix skipped.'
        };
        announce(messages[decision] || decision, 'assertive');
    }
    
    /**
     * Announce undo/redo action
     * @param {string} action - 'undo' | 'redo'
     */
    function announceUndoRedo(action) {
        announce(action === 'undo' ? 'Action undone.' : 'Action redone.', 'assertive');
    }
    
    /**
     * Update list of focusable elements (call after DOM changes)
     */
    function updateFocusableElements() {
        if (!modalEl) return;
        
        const selector = [
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            'a[href]'
        ].join(', ');
        
        focusableElements = Array.from(modalEl.querySelectorAll(selector));
        firstFocusable = focusableElements[0];
        lastFocusable = focusableElements[focusableElements.length - 1];
    }
    
    /**
     * Focus first focusable element in modal
     */
    function focusFirst() {
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }
    
    /**
     * Focus the accept button (common action after navigation)
     */
    function focusAcceptButton() {
        const btn = modalEl?.querySelector('#fav2-btn-accept');
        if (btn) btn.focus();
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Create invisible live region for screen reader announcements
     */
    function createAnnouncer() {
        announcer = document.createElement('div');
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'fav2-sr-only';
        // CSS: position:absolute; width:1px; height:1px; 
        //      overflow:hidden; clip:rect(0,0,0,0);
        document.body.appendChild(announcer);
    }
    
    /**
     * Setup keyboard focus trap within modal
     */
    function setupFocusTrap() {
        if (!modalEl) return;
        modalEl.addEventListener('keydown', handleFocusTrap);
    }
    
    /**
     * Handle Tab key for focus trapping
     */
    function handleFocusTrap(e) {
        if (e.key !== 'Tab') return;
        
        updateFocusableElements();
        
        if (focusableElements.length === 0) {
            e.preventDefault();
            return;
        }
        
        if (e.shiftKey) {
            // Shift+Tab: wrap from first to last
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab: wrap from last to first
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // EXPORTS
    // ═══════════════════════════════════════════════════════════════════════════
    
    return {
        init,
        destroy,
        announce,
        announceFix,
        announceDecision,
        announceUndoRedo,
        updateFocusableElements,
        focusFirst,
        focusAcceptButton
    };
})();

// Register global
window.A11yManager = A11yManager;
console.log('[TWR A11yManager] Module loaded v3.0.97');
