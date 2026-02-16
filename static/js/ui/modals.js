/**
 * AEGIS - Modal Management Module
 * @version 3.0.32
 * 
 * Centralized modal show/hide, focus trapping, and accessibility.
 * 
 * v3.0.32: Added setLoadingPhase for job-based progress
 * 
 * Dependencies: TWR.Utils (for refreshIcons)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Modals = (function() {
    
    // Track which element opened the modal for focus restoration
    let modalOpenerElement = null;
    
    // Track focus trap state
    let focusTrapActive = false;
    let focusTrapHandler = null;
    
    // ========================================
    // CORE MODAL FUNCTIONS
    // ========================================
    
    /**
     * Show a modal by ID
     * @param {string} modalId - Modal element ID
     * @param {Object} options - Display options
     * @param {boolean} options.focusTrap - Enable focus trapping (default: true)
     * @param {Function} options.onOpen - Callback after modal opens
     */
    function showModal(modalId, options = {}) {
        // Store opener for focus restoration
        modalOpenerElement = document.activeElement;
        
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.warn(`[TWR Modals] Modal not found: ${modalId}`);
            return;
        }
        
        // Add active class
        modal.classList.add('active');
        document.body.classList.add('modal-open');
        
        // Refresh icons in modal
        if (window.TWR?.Utils?.refreshIcons) {
            TWR.Utils.refreshIcons();
        } else if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
        
        // Focus first focusable element in modal
        const focusable = modal.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable) {
            setTimeout(() => focusable.focus(), 50);
        }
        
        // Enable focus trap if requested (default: true)
        if (options.focusTrap !== false) {
            enableFocusTrap(modal);
        }
        
        // Call onOpen callback
        if (typeof options.onOpen === 'function') {
            options.onOpen(modal);
        }
        
        console.log(`[TWR Modals] Opened: ${modalId}`);
    }
    
    /**
     * Close all open modals
     * @param {Object} options - Close options
     * @param {Function} options.onClose - Callback after modals close
     */
    function closeModals(options = {}) {
        // v4.6.1: Track which modals were open before closing to decide dashboard return
        const openModals = Array.from(document.querySelectorAll('.modal.active'));
        const mainModuleIds = [
            'modal-statement-forge', 'modal-roles', 'modal-scan-history'
        ];
        const hadMainModule = openModals.some(m => mainModuleIds.includes(m.id));

        openModals.forEach(m => {
            m.classList.remove('active');
        });
        document.body.classList.remove('modal-open');

        // Disable focus trap
        disableFocusTrap();

        // Restore focus to opener element
        if (modalOpenerElement && document.body.contains(modalOpenerElement)) {
            modalOpenerElement.focus();
            modalOpenerElement = null;
        }

        // Call onClose callback
        if (typeof options.onClose === 'function') {
            options.onClose();
        }

        // v4.6.1: Return to dashboard if a main module was closed
        // skipDashboard: used when switching modules, or when dashboard/logo already triggered this
        if (!options.skipDashboard && hadMainModule) {
            if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                TWR.LandingPage.show();
            }
        }

        console.log('[TWR Modals] Closed all modals');
    }
    
    /**
     * Show a dynamic content modal (creates overlay on the fly)
     * v4.1.0: For modals that need title + HTML content without a pre-existing DOM element.
     * Used by RACI drilldown, RACI cell edit, and other dynamic content.
     * @param {string} title - Modal title text
     * @param {string} htmlContent - HTML string for the modal body
     * @param {Object} options - Display options
     * @param {string} options.size - 'small', 'medium', 'large' (default: 'medium')
     * @param {Function} options.onShown - Callback after modal is shown and in DOM
     * @param {Function} options.onClose - Callback when modal is closed
     */
    function showContentModal(title, htmlContent, options = {}) {
        // Remove any existing content modal
        const existing = document.getElementById('twr-content-modal-overlay');
        if (existing) existing.remove();

        const sizeClass = options.size === 'large' ? 'twr-cm-large' : options.size === 'small' ? 'twr-cm-small' : '';
        const isDark = document.body.classList.contains('dark-mode') || document.documentElement.getAttribute('data-theme') === 'dark';

        const overlay = document.createElement('div');
        overlay.id = 'twr-content-modal-overlay';
        overlay.className = 'twr-content-modal-overlay';
        overlay.innerHTML = `
            <div class="twr-content-modal ${sizeClass}">
                <div class="twr-cm-header">
                    <h3 class="twr-cm-title">${title}</h3>
                    <button class="twr-cm-close" title="Close (Esc)">&times;</button>
                </div>
                <div class="twr-cm-body">${htmlContent}</div>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.classList.add('modal-open');

        // Refresh icons if available
        if (window.TWR?.Utils?.refreshIcons) {
            TWR.Utils.refreshIcons();
        } else if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }

        // Close handlers
        const closeContentModal = () => {
            overlay.classList.add('twr-cm-closing');
            setTimeout(() => {
                overlay.remove();
                // Only remove modal-open if no other modals are active
                if (!document.querySelector('.modal.active') && !document.querySelector('.twr-content-modal-overlay')) {
                    document.body.classList.remove('modal-open');
                }
                if (typeof options.onClose === 'function') options.onClose();
            }, 200);
        };

        overlay.querySelector('.twr-cm-close').addEventListener('click', closeContentModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeContentModal();
        });

        // Escape key — stop propagation so parent modals don't also close
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation();
                e.stopImmediatePropagation();
                e.preventDefault();
                closeContentModal();
                document.removeEventListener('keydown', escHandler, true);
            }
        };
        document.addEventListener('keydown', escHandler, true);

        // Animate in
        requestAnimationFrame(() => {
            overlay.classList.add('twr-cm-active');
        });

        // onShown callback (after DOM insertion, for Chart.js etc.)
        if (typeof options.onShown === 'function') {
            setTimeout(() => options.onShown(), 50);
        }

        console.log(`[TWR Modals] Content modal opened: ${title}`);
    }

    /**
     * Close a specific modal by ID
     * @param {string} modalId - Modal element ID
     */
    function closeModal(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');

            // v4.6.1: Check if this was a main module modal
            const mainModuleIds = [
                'modal-statement-forge', 'modal-roles', 'modal-scan-history'
            ];
            const wasMainModule = mainModuleIds.includes(modalId);

            // Check if any other modals are still open
            const otherOpenModals = document.querySelectorAll('.modal.active');
            if (otherOpenModals.length === 0) {
                document.body.classList.remove('modal-open');
                disableFocusTrap();

                // Restore focus
                if (modalOpenerElement && document.body.contains(modalOpenerElement)) {
                    modalOpenerElement.focus();
                    modalOpenerElement = null;
                }

                // v4.6.1: Return to dashboard if main module was closed
                if (!options.skipDashboard && wasMainModule) {
                    if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                        TWR.LandingPage.show();
                    }
                }
            }

            console.log(`[TWR Modals] Closed: ${modalId}`);
        }
    }
    
    /**
     * Toggle modal visibility
     * @param {string} modalId - Modal element ID
     * @returns {boolean} - True if modal is now visible
     */
    function toggleModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return false;
        
        if (modal.classList.contains('active')) {
            closeModal(modalId);
            return false;
        } else {
            showModal(modalId);
            return true;
        }
    }
    
    /**
     * Check if a modal is open
     * @param {string} modalId - Modal element ID (optional, checks any if not provided)
     * @returns {boolean}
     */
    function isModalOpen(modalId = null) {
        if (modalId) {
            const modal = document.getElementById(modalId);
            return modal ? modal.classList.contains('active') : false;
        }
        return document.querySelectorAll('.modal.active').length > 0;
    }
    
    // ========================================
    // FOCUS TRAP
    // ========================================
    
    /**
     * Enable focus trapping within a modal
     * @param {HTMLElement} modal - Modal element
     */
    function enableFocusTrap(modal) {
        if (focusTrapActive) {
            disableFocusTrap();
        }
        
        const focusableSelector = 
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        
        focusTrapHandler = function(e) {
            if (e.key !== 'Tab') return;
            
            const focusables = Array.from(modal.querySelectorAll(focusableSelector))
                .filter(el => !el.disabled && el.offsetParent !== null);
            
            if (focusables.length === 0) return;
            
            const firstFocusable = focusables[0];
            const lastFocusable = focusables[focusables.length - 1];
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        };
        
        document.addEventListener('keydown', focusTrapHandler);
        focusTrapActive = true;
    }
    
    /**
     * Disable focus trapping
     */
    function disableFocusTrap() {
        if (focusTrapHandler) {
            document.removeEventListener('keydown', focusTrapHandler);
            focusTrapHandler = null;
        }
        focusTrapActive = false;
    }
    
    // ========================================
    // INITIALIZATION
    // ========================================
    
    /**
     * Initialize modal close handlers
     * Call once on DOMContentLoaded
     */
    function initModalCloseHandlers() {
        // Close button handlers
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', closeModals);
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isModalOpen()) {
                closeModals();
            }
        });
        
        // Click outside to close (on modal backdrop)
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                // Only close if clicking the modal backdrop itself, not content
                if (e.target === modal) {
                    closeModals();
                }
            });
        });
        
        console.log('[TWR Modals] Close handlers initialized');
    }
    
    /**
     * Initialize focus trap for all modals
     * @deprecated Use showModal with focusTrap option instead
     */
    function initModalFocusTrap() {
        // This is now handled automatically by showModal
        console.log('[TWR Modals] Focus trap auto-enabled on modal open');
    }
    
    // ========================================
    // TOAST NOTIFICATIONS
    // ========================================
    
    /**
     * Show a toast notification
     * @param {string} type - 'success'|'error'|'warning'|'info'
     * @param {string} message - Message to display
     * @param {number} duration - Duration in ms (default: 4000)
     */
    function toast(type, message, duration = 4000) {
        const container = getToastContainer();
        const toastEl = document.createElement('div');
        toastEl.className = `toast toast-${type}`;
        
        const icons = { 
            success: 'check-circle', 
            error: 'x-circle', 
            warning: 'alert-triangle', 
            info: 'info' 
        };
        
        // Escape message for safety
        const safeMessage = window.TWR?.Utils?.escapeHtml 
            ? TWR.Utils.escapeHtml(message)
            : message.replace(/[&<>"']/g, m => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[m]));
        
        // SAFE: message escaped via safeMessage above
        toastEl.innerHTML = `
            <i data-lucide="${icons[type] || 'info'}" class="toast-icon"></i>
            <span class="toast-message">${safeMessage}</span>
        `;
        
        container.appendChild(toastEl);
        
        // Refresh icons
        if (window.TWR?.Utils?.refreshIcons) {
            TWR.Utils.refreshIcons();
        } else if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
        
        // Auto-remove after duration
        setTimeout(() => {
            toastEl.classList.add('toast-exit');
            setTimeout(() => toastEl.remove(), 300);
        }, duration);
    }
    
    /**
     * Get or create toast container
     * @returns {HTMLElement}
     */
    function getToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    // ========================================
    // LOADING OVERLAY
    // ========================================
    
    /**
     * Show loading overlay
     * @param {string} message - Loading message
     * @param {Object} options - Options
     * @param {number} options.progress - Progress percentage (0-100)
     * @param {string} options.detail - Additional detail text
     * @param {boolean} options.showCancel - Show cancel button
     * @param {number} options.totalItems - Total items for ETA
     */
    function showLoading(message, options = {}) {
        const progress = options.progress || 0;
        
        // Initialize tracker if totalItems provided
        if (options.totalItems && window.LoadingTracker) {
            LoadingTracker.start(message, options.totalItems);
        }
        
        // Show cancel button if requested
        const cancelBtn = document.getElementById('loading-cancel');
        if (cancelBtn && options.showCancel) {
            cancelBtn.style.display = 'inline-flex';
        }
        
        setLoading(true, message || 'Loading...', progress);
        
        if (window.State) window.State.isLoading = true;
        console.log('[TWR] Loading:', message);
    }
    
    /**
     * Hide loading overlay
     */
    function hideLoading() {
        setLoading(false);
        
        if (window.LoadingTracker) {
            LoadingTracker.reset();
        }
        
        if (window.State) window.State.isLoading = false;
        console.log('[TWR] Loading hidden');
    }
    
    /**
     * Update loading message and progress
     * @param {string} message - New message
     * @param {Object} options - Options
     * @param {number} options.progress - Progress percentage
     * @param {number} options.currentItem - Current item number
     * @param {number} options.totalItems - Total items
     */
    function updateLoadingMessage(message, options = {}) {
        if (options.progress !== undefined) {
            updateProgress(options.progress, message);
        } else {
            const msgEl = document.querySelector('.loading-message, #loading-text');
            if (msgEl && message) msgEl.textContent = message;
        }
        
        // Update item progress if provided
        if (options.currentItem !== undefined && options.totalItems !== undefined) {
            if (window.LoadingTracker) {
                LoadingTracker.updateProgress(options.currentItem, options.totalItems);
            }
        }
        
        console.log('[TWR] Loading update:', message);
    }
    
    /**
     * Set loading state (internal helper)
     * @param {boolean} loading - Loading state
     * @param {string} message - Loading message
     * @param {number} progress - Progress percentage
     */
    function setLoading(loading, message = 'Loading...', progress = 0) {
        if (window.State) window.State.isLoading = loading;
        
        const overlay = document.getElementById('loading-overlay');
        const msgEl = document.getElementById('loading-text');
        const progressBar = document.getElementById('loading-progress-bar');
        const stepsContainer = document.getElementById('loading-steps');
        
        if (overlay) overlay.style.display = loading ? 'flex' : 'none';
        if (msgEl) msgEl.textContent = message;
        if (progressBar) progressBar.style.width = `${progress}%`;
        
        // Reset steps when loading starts/stops
        if (stepsContainer) {
            if (loading) {
                stepsContainer.style.display = 'flex';
                stepsContainer.querySelectorAll('.loading-step').forEach(step => {
                    step.classList.remove('active', 'complete');
                    const icon = step.querySelector('.step-icon');
                    if (icon) icon.setAttribute('data-lucide', 'circle');
                });
            } else {
                stepsContainer.style.display = 'none';
            }
            
            // Refresh icons
            if (window.TWR?.Utils?.refreshIcons) {
                TWR.Utils.refreshIcons();
            } else if (typeof lucide !== 'undefined') {
                try { lucide.createIcons(); } catch(e) {}
            }
        }
    }
    
    /**
     * Update loading step status
     * @param {string} stepName - Step name (data-step attribute)
     * @param {string} status - 'active'|'complete'
     */
    function setLoadingStep(stepName, status = 'active') {
        const stepsContainer = document.getElementById('loading-steps');
        if (!stepsContainer) return;
        
        const step = stepsContainer.querySelector(`[data-step="${stepName}"]`);
        if (!step) return;
        
        const icon = step.querySelector('.step-icon');
        
        if (status === 'active') {
            // Mark previous steps as complete
            let found = false;
            stepsContainer.querySelectorAll('.loading-step').forEach(s => {
                if (s === step) {
                    found = true;
                    s.classList.add('active');
                    s.classList.remove('complete');
                    if (icon) icon.setAttribute('data-lucide', 'loader');
                } else if (!found) {
                    s.classList.remove('active');
                    s.classList.add('complete');
                    const sIcon = s.querySelector('.step-icon');
                    if (sIcon) sIcon.setAttribute('data-lucide', 'check-circle');
                }
            });
        } else if (status === 'complete') {
            step.classList.remove('active');
            step.classList.add('complete');
            if (icon) icon.setAttribute('data-lucide', 'check-circle');
        }
        
        // Refresh icons
        if (window.TWR?.Utils?.refreshIcons) {
            TWR.Utils.refreshIcons();
        } else if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }
    
    /**
     * v3.0.32: Set loading phase from job progress data
     * Maps job phases to loading step names
     * @param {string} phase - Job phase name
     * @param {Object} progressData - Additional progress data
     */
    function setLoadingPhase(phase, progressData = {}) {
        // Map job phases to loading step names
        const phaseToStep = {
            'queued': 'upload',
            'uploading': 'upload',
            'extracting': 'extract',
            'parsing': 'extract',
            'checking': 'analyze',
            'postprocessing': 'roles',
            'exporting': 'render',
            'complete': 'render'
        };
        
        const stepName = phaseToStep[phase] || 'analyze';
        setLoadingStep(stepName, phase === 'complete' ? 'complete' : 'active');
        
        // Update progress bar
        if (progressData.overallProgress !== undefined) {
            updateProgress(progressData.overallProgress);
        }
        
        // Update message with checker info if in checking phase
        let message = progressData.lastLog || `Processing: ${phase}`;
        if (phase === 'checking' && progressData.currentChecker) {
            message = `Running ${progressData.currentChecker}`;
            if (progressData.checkersCompleted && progressData.checkersTotal) {
                message += ` (${progressData.checkersCompleted}/${progressData.checkersTotal})`;
            }
        }
        
        const msgEl = document.getElementById('loading-text');
        if (msgEl) msgEl.textContent = message;
        
        // Update ETA display
        const etaEl = document.getElementById('loading-eta');
        const etaContainer = document.getElementById('loading-eta-container');
        if (etaEl && etaContainer && progressData.eta) {
            etaContainer.style.display = 'flex';
            etaEl.textContent = progressData.eta;
        }
        
        // Update elapsed display
        const detailEl = document.getElementById('loading-detail');
        if (detailEl && progressData.elapsed) {
            detailEl.textContent = `Elapsed: ${progressData.elapsed}`;
        }
    }
    
    /**
     * Update progress bar and message
     * @param {number} progress - Progress percentage
     * @param {string} message - Optional message update
     */
    function updateProgress(progress, message) {
        const msgEl = document.getElementById('loading-text');
        const progressBar = document.getElementById('loading-progress-bar');
        
        if (msgEl && message) msgEl.textContent = message;
        if (progressBar) progressBar.style.width = `${progress}%`;
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // Core modal functions
        showModal,
        showContentModal,
        closeModals,
        closeModal,
        toggleModal,
        isModalOpen,
        
        // Focus trap
        enableFocusTrap,
        disableFocusTrap,
        
        // Initialization
        initModalCloseHandlers,
        initModalFocusTrap,
        
        // Toast notifications
        toast,
        
        // Loading overlay
        showLoading,
        hideLoading,
        updateLoadingMessage,
        setLoading,
        setLoadingStep,
        setLoadingPhase,  // v3.0.32
        updateProgress
    };
})();

// ========================================
// GLOBAL ALIASES (for backward compatibility)
// ========================================

window.showModal = TWR.Modals.showModal;
window.showContentModal = TWR.Modals.showContentModal;
window.closeModals = TWR.Modals.closeModals;
window.toast = TWR.Modals.toast;
window.showLoading = TWR.Modals.showLoading;
window.hideLoading = TWR.Modals.hideLoading;
window.updateLoadingMessage = TWR.Modals.updateLoadingMessage;
window.setLoading = TWR.Modals.setLoading;
window.setLoadingStep = TWR.Modals.setLoadingStep;
window.setLoadingPhase = TWR.Modals.setLoadingPhase;  // v3.0.32
window.updateProgress = TWR.Modals.updateProgress;
window.initModalFocusTrap = TWR.Modals.initModalFocusTrap;

console.log('[TWR] Modals module loaded');
