/**
 * AEGIS - API Client Module
 * @version 3.0.17
 *
 * Centralized API communication with CSRF handling, error management,
 * and response normalization.
 *
 * v3.0.17: Added response.ok validation and safe JSON parsing with error handling
 *
 * Dependencies: TWR.State (for CSRF token storage)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.API = (function() {
    
    // ========================================
    // CSRF TOKEN MANAGEMENT
    // ========================================
    
    /**
     * Initialize CSRF token from meta tag
     */
    async function initCSRF() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) {
            const token = meta.getAttribute('content');
            if (window.State) window.State.csrfToken = token;
            window.CSRF_TOKEN = token;
        }
        await fetchCSRFToken();
    }
    
    /**
     * Fetch fresh CSRF token from server
     * @returns {Promise<string|null>}
     */
    async function fetchCSRFToken() {
        try {
            const response = await fetch('/api/csrf-token');
            // v3.0.17: Check response.ok before parsing
            if (!response.ok) {
                console.warn('[TWR API] CSRF token fetch failed:', response.status);
                return null;
            }
            const data = await response.json();
            if (data.csrf_token) {
                if (window.State) window.State.csrfToken = data.csrf_token;
                window.CSRF_TOKEN = data.csrf_token;
                // v4.0.3: Also update meta tag so all code paths use the synced token
                const meta = document.querySelector('meta[name="csrf-token"]');
                if (meta) meta.setAttribute('content', data.csrf_token);
                return data.csrf_token;
            }
        } catch (e) {
            console.warn('[TWR API] Failed to fetch CSRF token:', e);
        }
        return null;
    }
    
    /**
     * Get current CSRF token
     * @returns {string|null}
     */
    function getCSRFToken() {
        return window.State?.csrfToken || window.CSRF_TOKEN || null;
    }
    
    // ========================================
    // CORE API FUNCTION
    // ========================================
    
    /**
     * Make API request with automatic CSRF handling
     * @param {string} endpoint - API endpoint (without /api prefix)
     * @param {string} method - HTTP method
     * @param {Object|FormData|null} body - Request body
     * @param {Object} options - Additional options
     * @param {AbortSignal} options.signal - Abort signal for cancellation
     * @returns {Promise<Object>}
     */
    async function api(endpoint, method = 'GET', body = null, options = {}) {
        const opts = {
            method,
            headers: {}
        };
        
        // Add abort signal if provided
        if (options.signal) {
            opts.signal = options.signal;
        }
        
        // Add CSRF token for non-GET requests
        const csrfToken = getCSRFToken();
        if (method !== 'GET' && csrfToken) {
            opts.headers['X-CSRF-Token'] = csrfToken;
        }
        
        // Handle body
        if (body && !(body instanceof FormData)) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        } else if (body) {
            // FormData - let browser set Content-Type with boundary
            if (csrfToken) {
                opts.headers['X-CSRF-Token'] = csrfToken;
            }
            opts.body = body;
        }
        
        try {
            const response = await fetch(`/api${endpoint}`, opts);
            
            // Update CSRF token if provided in response
            const newToken = response.headers.get('X-CSRF-Token');
            if (newToken) {
                if (window.State) window.State.csrfToken = newToken;
                window.CSRF_TOKEN = newToken;
                // v4.0.3: Keep meta tag in sync
                const meta = document.querySelector('meta[name="csrf-token"]');
                if (meta) meta.setAttribute('content', newToken);
            }
            
            // Handle specific error codes
            if (response.status === 403) {
                await fetchCSRFToken();
                if (typeof toast === 'function') {
                    toast('warning', 'Security token refreshed. Please try again.');
                }
                return { success: false, error: 'CSRF token expired' };
            }
            
            if (response.status === 413) {
                return { success: false, error: 'File is too large. Maximum size is 50MB.' };
            }
            
            if (response.status === 429) {
                return { success: false, error: 'Too many requests. Please wait a moment.' };
            }

            // v3.0.17: Check response.ok before parsing JSON to catch HTTP errors
            if (!response.ok) {
                console.warn('[TWR API] HTTP error:', response.status, response.statusText);
                return { success: false, error: `Server error: ${response.status} ${response.statusText}` };
            }

            // v3.0.17: Safely parse JSON response with error handling
            try {
                return await response.json();
            } catch (jsonErr) {
                console.error('[TWR API] JSON parse error:', jsonErr);
                return { success: false, error: 'Invalid response from server (not JSON)' };
            }

        } catch (e) {
            // Handle abort
            if (e.name === 'AbortError') {
                console.log('[TWR API] Request aborted:', endpoint);
                return { success: false, error: 'Request cancelled', aborted: true };
            }
            
            console.error('[TWR API] Request error:', e);
            return { success: false, error: e.message };
        }
    }
    
    // ========================================
    // CONVENIENCE METHODS
    // ========================================
    
    /**
     * GET request
     * @param {string} endpoint
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    function get(endpoint, options = {}) {
        return api(endpoint, 'GET', null, options);
    }
    
    /**
     * POST request
     * @param {string} endpoint
     * @param {Object} body
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    function post(endpoint, body = null, options = {}) {
        return api(endpoint, 'POST', body, options);
    }
    
    /**
     * PUT request
     * @param {string} endpoint
     * @param {Object} body
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    function put(endpoint, body = null, options = {}) {
        return api(endpoint, 'PUT', body, options);
    }
    
    /**
     * DELETE request
     * @param {string} endpoint
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    function del(endpoint, options = {}) {
        return api(endpoint, 'DELETE', null, options);
    }
    
    // ========================================
    // FILE UPLOAD
    // ========================================
    
    /**
     * Upload file for analysis
     * @param {File} file - File to upload
     * @param {Object} options - Upload options
     * @param {AbortSignal} options.signal - Abort signal
     * @param {Function} options.onProgress - Progress callback (0-100)
     * @returns {Promise<Object>}
     */
    async function uploadFile(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add any additional form fields from options
        if (options.checks) {
            formData.append('checks', JSON.stringify(options.checks));
        }
        
        return post('/upload', formData, { signal: options.signal });
    }
    
    /**
     * Run review on uploaded file
     * @param {string} filepath - Server filepath
     * @param {Object} checks - Check configuration
     * @param {Object} options - Request options
     * @returns {Promise<Object>}
     */
    async function runReview(filepath, checks = {}, options = {}) {
        return post('/review', { filepath, checks }, options);
    }
    
    // ========================================
    // VERSION & CAPABILITIES
    // ========================================
    
    /**
     * Get server version
     * @returns {Promise<Object>}
     */
    async function getVersion() {
        return get('/version');
    }
    
    /**
     * Get server capabilities
     * @returns {Promise<Object>}
     */
    async function getCapabilities() {
        return get('/capabilities');
    }
    
    /**
     * Check for updates
     * @returns {Promise<Object>}
     */
    async function checkUpdates() {
        return get('/updates/check');
    }
    
    // ========================================
    // EXPORT
    // ========================================
    
    /**
     * Export issues to specified format
     * @param {Object} params - Export parameters
     * @param {string} params.format - 'csv'|'json'|'word'|'excel'
     * @param {Array} params.issues - Issues to export
     * @param {string} params.filename - Original filename
     * @param {boolean} params.applyFixes - Apply suggested fixes
     * @returns {Promise<Object>}
     */
    async function exportIssues(params) {
        return post('/export', params);
    }
    
    /**
     * Export roles
     * @param {Object} roles - Roles data
     * @param {string} format - Export format
     * @returns {Promise<Object>}
     */
    async function exportRoles(roles, format = 'csv') {
        return post('/export-roles', { roles, format });
    }
    
    // ========================================
    // SCAN HISTORY
    // ========================================
    
    /**
     * Get scan history
     * @returns {Promise<Object>}
     */
    async function getScanHistory() {
        return get('/scan-history');
    }
    
    /**
     * Save scan to history
     * @param {Object} scanData - Scan data
     * @returns {Promise<Object>}
     */
    async function saveScanHistory(scanData) {
        return post('/scan-history', scanData);
    }
    
    /**
     * Delete scan from history
     * @param {number} scanId - Scan ID
     * @returns {Promise<Object>}
     */
    async function deleteScanHistory(scanId) {
        return del(`/scan-history/${scanId}`);
    }
    
    // ========================================
    // PROFILES
    // ========================================
    
    /**
     * Get scan profiles
     * @returns {Promise<Object>}
     */
    async function getProfiles() {
        return get('/scan-profiles');
    }
    
    /**
     * Save profile
     * @param {Object} profile - Profile data
     * @returns {Promise<Object>}
     */
    async function saveProfile(profile) {
        return post('/scan-profiles', profile);
    }
    
    /**
     * Delete profile
     * @param {number} profileId - Profile ID
     * @returns {Promise<Object>}
     */
    async function deleteProfile(profileId) {
        return del(`/scan-profiles/${profileId}`);
    }
    
    // ========================================
    // ROLES
    // ========================================
    
    /**
     * Extract roles from document
     * @param {string} filepath - Document filepath
     * @param {Object} options - Extraction options
     * @returns {Promise<Object>}
     */
    async function extractRoles(filepath, options = {}) {
        return post('/extract-roles', { filepath, ...options });
    }
    
    /**
     * Get role dictionary
     * @returns {Promise<Object>}
     */
    async function getRoleDictionary() {
        return get('/role-dictionary');
    }
    
    /**
     * Update role dictionary
     * @param {Object} dictionary - Dictionary data
     * @returns {Promise<Object>}
     */
    async function updateRoleDictionary(dictionary) {
        return post('/role-dictionary', dictionary);
    }
    
    // ========================================
    // STATEMENT FORGE
    // ========================================
    
    /**
     * Extract statements from document
     * @param {string} text - Document text
     * @param {Object} options - Extraction options
     * @returns {Promise<Object>}
     */
    async function extractStatements(text, options = {}) {
        return post('/statement-forge/extract', { text, ...options });
    }
    
    /**
     * Export statements
     * @param {Array} statements - Statements to export
     * @param {string} format - Export format
     * @returns {Promise<Object>}
     */
    async function exportStatements(statements, format) {
        return post('/statement-forge/export', { statements, format });
    }
    
    // ========================================
    // DIAGNOSTICS
    // ========================================
    
    /**
     * Get diagnostic information
     * @returns {Promise<Object>}
     */
    async function getDiagnostics() {
        return get('/diagnostics');
    }
    
    /**
     * Export diagnostic package
     * @param {Object} data - Diagnostic data
     * @returns {Promise<Object>}
     */
    async function exportDiagnostics(data) {
        return post('/diagnostics/export', data);
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // CSRF
        initCSRF,
        fetchCSRFToken,
        getCSRFToken,
        
        // Core
        api,
        get,
        post,
        put,
        del,
        
        // File operations
        uploadFile,
        runReview,
        
        // Version & capabilities
        getVersion,
        getCapabilities,
        checkUpdates,
        
        // Export
        exportIssues,
        exportRoles,
        
        // Scan history
        getScanHistory,
        saveScanHistory,
        deleteScanHistory,
        
        // Profiles
        getProfiles,
        saveProfile,
        deleteProfile,
        
        // Roles
        extractRoles,
        getRoleDictionary,
        updateRoleDictionary,
        
        // Statement Forge
        extractStatements,
        exportStatements,
        
        // Diagnostics
        getDiagnostics,
        exportDiagnostics
    };
})();

// ========================================
// GLOBAL ALIASES (for backward compatibility)
// ========================================

window.api = TWR.API.api;
window.initCSRF = TWR.API.initCSRF;
window.fetchCSRFToken = TWR.API.fetchCSRFToken;

console.log('[TWR] API module loaded');
