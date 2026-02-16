/**
 * AEGIS - DOM Utilities Module
 * @version 3.0.16
 * 
 * Pure utility functions with no dependencies on other TWR modules.
 * These are foundational helpers used throughout the application.
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Utils = (function() {
    
    // ========================================
    // STRING UTILITIES
    // ========================================
    
    /**
     * Escape HTML special characters to prevent XSS
     * @param {string} str - Input string
     * @returns {string} - Escaped string
     */
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    /**
     * Truncate string to max length with ellipsis
     * @param {string} str - Input string
     * @param {number} maxLen - Maximum length
     * @returns {string} - Truncated string
     */
    function truncate(str, maxLen) {
        if (!str) return '';
        return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
    }
    
    /**
     * Generate ISO timestamp for filenames (no colons/special chars)
     * @returns {string} - Timestamp string like "2025-01-20T14-30-00"
     */
    function getTimestamp() {
        return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    }
    
    // ========================================
    // FUNCTION UTILITIES
    // ========================================
    
    /**
     * Debounce function execution
     * @param {Function} fn - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} - Debounced function
     */
    function debounce(fn, delay) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn.apply(this, args), delay);
        };
    }
    
    /**
     * Throttle function execution
     * @param {Function} fn - Function to throttle
     * @param {number} limit - Minimum time between calls in milliseconds
     * @returns {Function} - Throttled function
     */
    function throttle(fn, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                fn.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // ========================================
    // DOM ELEMENT UTILITIES
    // ========================================
    
    /**
     * Show element by ID
     * @param {string} id - Element ID
     */
    function show(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = '';
    }
    
    /**
     * Hide element by ID
     * @param {string} id - Element ID
     */
    function hide(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }
    
    /**
     * Toggle element visibility by ID
     * @param {string} id - Element ID
     * @returns {boolean} - True if element is now visible
     */
    function toggle(id) {
        const el = document.getElementById(id);
        if (el) {
            const isHidden = el.style.display === 'none';
            el.style.display = isHidden ? '' : 'none';
            return isHidden;
        }
        return false;
    }
    
    /**
     * Safely get element by ID with optional fallback
     * @param {string} id - Element ID
     * @param {*} fallback - Fallback value if element not found
     * @returns {HTMLElement|*} - Element or fallback
     */
    function getEl(id, fallback = null) {
        return document.getElementById(id) || fallback;
    }
    
    /**
     * Set text content of element by ID
     * @param {string} id - Element ID
     * @param {string|number} value - Value to set
     */
    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = typeof value === 'number' ? value.toLocaleString() : value;
    }
    
    /**
     * Set innerHTML of element by ID (use with caution - prefer setText for user data)
     * @param {string} id - Element ID
     * @param {string} html - HTML to set
     */
    function setHtml(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }
    
    /**
     * Add event listener with null safety
     * @param {string} id - Element ID
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     * @param {Object} options - addEventListener options
     */
    function on(id, event, handler, options) {
        const el = typeof id === 'string' ? document.getElementById(id) : id;
        if (el) el.addEventListener(event, handler, options);
    }
    
    /**
     * Query selector with null safety
     * @param {string} selector - CSS selector
     * @param {Element} context - Context element (default: document)
     * @returns {Element|null}
     */
    function qs(selector, context = document) {
        return context.querySelector(selector);
    }
    
    /**
     * Query selector all with array return
     * @param {string} selector - CSS selector
     * @param {Element} context - Context element (default: document)
     * @returns {Element[]}
     */
    function qsa(selector, context = document) {
        return Array.from(context.querySelectorAll(selector));
    }
    
    // ========================================
    // CLASS UTILITIES
    // ========================================
    
    /**
     * Add class to element by ID
     * @param {string} id - Element ID
     * @param {string} className - Class name to add
     */
    function addClass(id, className) {
        const el = document.getElementById(id);
        if (el) el.classList.add(className);
    }
    
    /**
     * Remove class from element by ID
     * @param {string} id - Element ID
     * @param {string} className - Class name to remove
     */
    function removeClass(id, className) {
        const el = document.getElementById(id);
        if (el) el.classList.remove(className);
    }
    
    /**
     * Toggle class on element by ID
     * @param {string} id - Element ID
     * @param {string} className - Class name to toggle
     * @param {boolean} force - Force add (true) or remove (false)
     * @returns {boolean} - True if class is now present
     */
    function toggleClass(id, className, force) {
        const el = document.getElementById(id);
        if (el) return el.classList.toggle(className, force);
        return false;
    }
    
    /**
     * Check if element has class
     * @param {string} id - Element ID
     * @param {string} className - Class name to check
     * @returns {boolean}
     */
    function hasClass(id, className) {
        const el = document.getElementById(id);
        return el ? el.classList.contains(className) : false;
    }
    
    // ========================================
    // FORMATTING UTILITIES
    // ========================================
    
    /**
     * Format number with thousands separator
     * @param {number} num - Number to format
     * @returns {string}
     */
    function formatNumber(num) {
        return typeof num === 'number' ? num.toLocaleString() : String(num);
    }
    
    /**
     * Format date for display
     * @param {Date|string} date - Date to format
     * @returns {string}
     */
    function formatDate(date) {
        const d = date instanceof Date ? date : new Date(date);
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    /**
     * Format file size in human readable form
     * @param {number} bytes - Size in bytes
     * @returns {string}
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    /**
     * Format duration in human readable form
     * @param {number} ms - Duration in milliseconds
     * @returns {string}
     */
    function formatDuration(ms) {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        const mins = Math.floor(ms / 60000);
        const secs = Math.ceil((ms % 60000) / 1000);
        return `${mins}m ${secs}s`;
    }
    
    // ========================================
    // STORAGE UTILITIES
    // ========================================
    
    /**
     * Safely get item from localStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if not found
     * @returns {*}
     */
    function storageGet(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn(`Failed to read ${key} from localStorage:`, e);
            return defaultValue;
        }
    }
    
    /**
     * Safely set item in localStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     * @returns {boolean} - True if successful
     */
    function storageSet(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn(`Failed to write ${key} to localStorage:`, e);
            return false;
        }
    }
    
    /**
     * Safely remove item from localStorage
     * @param {string} key - Storage key
     */
    function storageRemove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn(`Failed to remove ${key} from localStorage:`, e);
        }
    }
    
    // ========================================
    // ASYNC UTILITIES
    // ========================================
    
    /**
     * Sleep for specified duration
     * @param {number} ms - Duration in milliseconds
     * @returns {Promise<void>}
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Create a deferred promise
     * @returns {{promise: Promise, resolve: Function, reject: Function}}
     */
    function deferred() {
        let resolve, reject;
        const promise = new Promise((res, rej) => {
            resolve = res;
            reject = rej;
        });
        return { promise, resolve, reject };
    }
    
    // ========================================
    // LUCIDE ICON HELPER
    // ========================================
    
    /**
     * Safely refresh Lucide icons
     * Call after dynamically adding elements with data-lucide attributes
     */
    function refreshIcons() {
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            try {
                lucide.createIcons();
            } catch (e) {
                console.warn('[TWR] Failed to refresh Lucide icons:', e);
            }
        }
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // String utilities
        escapeHtml,
        truncate,
        getTimestamp,
        
        // Function utilities
        debounce,
        throttle,
        
        // DOM utilities
        show,
        hide,
        toggle,
        getEl,
        setText,
        setHtml,
        on,
        qs,
        qsa,
        
        // Class utilities
        addClass,
        removeClass,
        toggleClass,
        hasClass,
        
        // Formatting utilities
        formatNumber,
        formatDate,
        formatFileSize,
        formatDuration,
        
        // Storage utilities
        storageGet,
        storageSet,
        storageRemove,
        
        // Async utilities
        sleep,
        deferred,
        
        // Icon helper
        refreshIcons
    };
})();

// ========================================
// GLOBAL ALIASES (for backward compatibility)
// ========================================
// These allow existing code to continue working while migration proceeds

window.escapeHtml = TWR.Utils.escapeHtml;
window.truncate = TWR.Utils.truncate;
window.debounce = TWR.Utils.debounce;
window.getTimestamp = TWR.Utils.getTimestamp;

console.log('[TWR] Utils module loaded');
