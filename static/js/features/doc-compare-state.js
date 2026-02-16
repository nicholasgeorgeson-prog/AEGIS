/**
 * Document Comparison State Management
 * =====================================
 * State management module for document comparison feature.
 * Follows the IIFE pattern used by fix-assistant-state.js.
 *
 * @version 1.0.0
 * @requires TWR.API (api function)
 */

window.DocCompareState = (function() {
    'use strict';

    // =========================================================================
    // PRIVATE STATE
    // =========================================================================

    let initialized = false;

    // Document and scan selection
    let documentId = null;
    let documentInfo = null;
    let scans = [];
    let oldScanId = null;
    let newScanId = null;

    // Diff data
    let diff = null;
    let issueComparison = null;

    // Navigation state
    let currentChangeIndex = 0;
    let navigationOrder = [];  // Indices of rows that are changes

    // Filter state
    let filters = {
        showAdded: true,
        showDeleted: true,
        showModified: true,
        showMoved: true
    };

    // UI state
    let issuesPanelCollapsed = false;
    let isLoading = false;

    // Event listeners
    const listeners = {
        change: [],
        navigate: [],
        load: [],
        error: []
    };

    // =========================================================================
    // EVENT SYSTEM
    // =========================================================================

    /**
     * Emit an event to all registered listeners.
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    function emit(event, data) {
        if (listeners[event]) {
            listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`[TWR DocCompare] Error in ${event} listener:`, e);
                }
            });
        }
    }

    /**
     * Subscribe to an event.
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    function subscribe(event, callback) {
        if (!listeners[event]) {
            listeners[event] = [];
        }
        listeners[event].push(callback);

        // Return unsubscribe function
        return () => {
            const idx = listeners[event].indexOf(callback);
            if (idx > -1) {
                listeners[event].splice(idx, 1);
            }
        };
    }

    // =========================================================================
    // API HELPERS
    // =========================================================================

    /**
     * Make API request with error handling.
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    async function apiRequest(endpoint, options = {}) {
        // Use TWR.API if available, otherwise use fetch
        const baseUrl = '/api/compare';
        const url = `${baseUrl}${endpoint}`;

        console.log('[TWR DocCompare] API request:', url, options.method || 'GET');

        // v4.5.0: Use standardized CSRF token retrieval (window.CSRF_TOKEN → meta tag)
        const csrfToken = window.CSRF_TOKEN
            || document.querySelector('meta[name="csrf-token"]')?.content
            || '';

        const fetchOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken,
                ...options.headers
            }
        };

        if (options.body && typeof options.body === 'object') {
            fetchOptions.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, fetchOptions);
            console.log('[TWR DocCompare] API response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                // v4.7.0-fix: Only log validation errors as warnings, not errors
                if (response.status === 400) {
                    console.warn('[TWR DocCompare] API validation error:', errorText);
                    // Parse error message for cleaner throw
                    try {
                        const errData = JSON.parse(errorText);
                        throw new Error(errData?.error?.message || `Validation error`);
                    } catch (parseErr) {
                        if (parseErr.message && !parseErr.message.includes('JSON')) throw parseErr;
                        throw new Error(`Validation error: ${errorText}`);
                    }
                }
                console.error('[TWR DocCompare] API error response:', errorText);
                if (response.status === 403) {
                    // v4.6.0: Refresh CSRF token and retry the original request
                    try {
                        const refreshResp = await fetch('/api/compare/status');
                        const refreshToken = refreshResp.headers.get('X-CSRF-Token');
                        if (refreshToken) {
                            window.CSRF_TOKEN = refreshToken;
                            // Also update meta tag for other modules
                            const meta = document.querySelector('meta[name="csrf-token"]');
                            if (meta) meta.setAttribute('content', refreshToken);
                            // Retry the original request with fresh token
                            fetchOptions.headers['X-CSRF-Token'] = refreshToken;
                            const retryResp = await fetch(url, fetchOptions);
                            if (retryResp.ok) {
                                const retryData = await retryResp.json();
                                if (retryData.success) return retryData;
                            }
                        }
                    } catch (_) { /* best effort */ }
                    throw new Error('Session expired. Please refresh the page and try again.');
                }
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();

            // v4.5.0: Sync CSRF token from successful GET responses
            if (fetchOptions.method === 'GET' || !fetchOptions.method) {
                const newToken = response.headers.get('X-CSRF-Token');
                if (newToken) window.CSRF_TOKEN = newToken;
            }

            if (!data.success) {
                const error = data.error || { message: 'Unknown error' };
                console.error('[TWR DocCompare] API returned error:', error);
                throw new Error(error.message || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('[TWR DocCompare] API request failed:', error);
            throw error;
        }
    }

    // =========================================================================
    // NAVIGATION HELPERS
    // =========================================================================

    /**
     * Build navigation order based on current filters.
     */
    function buildNavigationOrder() {
        navigationOrder = [];

        if (!diff || !diff.rows) {
            return;
        }

        diff.rows.forEach((row, index) => {
            if (!row.is_change) return;

            // Apply filters
            if (row.status === 'added' && !filters.showAdded) return;
            if (row.status === 'deleted' && !filters.showDeleted) return;
            if (row.status === 'modified' && !filters.showModified) return;
            if ((row.status === 'moved_from' || row.status === 'moved_to') && !filters.showMoved) return;

            navigationOrder.push(index);
        });

        // Reset current index if out of bounds
        if (currentChangeIndex >= navigationOrder.length) {
            currentChangeIndex = Math.max(0, navigationOrder.length - 1);
        }
    }

    /**
     * Get the current change row index.
     * @returns {number} Row index of current change, or -1 if none
     */
    function getCurrentRowIndex() {
        if (navigationOrder.length === 0) {
            return -1;
        }
        return navigationOrder[currentChangeIndex] || -1;
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        // =====================================================================
        // INITIALIZATION
        // =====================================================================

        /**
         * Initialize state for a document.
         * @param {number} docId - Document ID
         */
        init(docId) {
            documentId = docId;
            documentInfo = null;
            scans = [];
            oldScanId = null;
            newScanId = null;
            diff = null;
            issueComparison = null;
            currentChangeIndex = 0;
            navigationOrder = [];
            filters = {
                showAdded: true,
                showDeleted: true,
                showModified: true,
                showMoved: true
            };
            issuesPanelCollapsed = false;
            isLoading = false;
            initialized = true;

            emit('change', { type: 'init', documentId: docId });
        },

        /**
         * Reset all state.
         */
        reset() {
            this.init(null);
            initialized = false;
        },

        /**
         * Check if state is initialized.
         * @returns {boolean}
         */
        isInitialized() {
            return initialized;
        },

        // =====================================================================
        // DATA LOADING
        // =====================================================================

        /**
         * Load scans for a document.
         * @param {number} docId - Document ID
         * @returns {Promise<Array>} List of scans
         */
        async loadScans(docId) {
            console.log('[TWR DocCompare] loadScans called with docId:', docId);

            if (!docId) {
                const error = 'Document ID is required';
                console.error('[TWR DocCompare] loadScans error:', error);
                emit('error', { type: 'loadScans', error });
                throw new Error(error);
            }

            isLoading = true;
            emit('change', { type: 'loading', isLoading: true });

            try {
                console.log('[TWR DocCompare] Fetching scans from API...');
                const data = await apiRequest(`/scans/${docId}`);
                console.log('[TWR DocCompare] API response:', {
                    success: data.success,
                    scanCount: data.scans?.length || 0,
                    document: data.document
                });

                documentId = docId;
                documentInfo = data.document;
                scans = data.scans || [];

                emit('load', { type: 'scans', scans, document: documentInfo });
                return scans;

            } catch (error) {
                console.error('[TWR DocCompare] loadScans error:', error.message);
                emit('error', { type: 'loadScans', error: error.message });
                throw error;

            } finally {
                isLoading = false;
                emit('change', { type: 'loading', isLoading: false });
            }
        },

        /**
         * Set the old (baseline) scan ID.
         * @param {number} scanId - Scan ID
         */
        setOldScan(scanId) {
            oldScanId = scanId;
            emit('change', { type: 'scanSelection', oldScanId, newScanId });
        },

        /**
         * Set the new (current) scan ID.
         * @param {number} scanId - Scan ID
         */
        setNewScan(scanId) {
            newScanId = scanId;
            emit('change', { type: 'scanSelection', oldScanId, newScanId });
        },

        /**
         * Load diff between selected scans.
         * @returns {Promise<Object>} Diff result
         */
        async loadDiff() {
            if (!oldScanId || !newScanId) {
                throw new Error('Both old and new scans must be selected');
            }

            isLoading = true;
            emit('change', { type: 'loading', isLoading: true });

            try {
                const data = await apiRequest('/diff', {
                    method: 'POST',
                    body: {
                        old_scan_id: oldScanId,
                        new_scan_id: newScanId
                    }
                });

                diff = data.diff;
                currentChangeIndex = 0;
                buildNavigationOrder();

                emit('load', { type: 'diff', diff });
                return diff;

            } catch (error) {
                emit('error', { type: 'loadDiff', error: error.message });
                throw error;

            } finally {
                isLoading = false;
                emit('change', { type: 'loading', isLoading: false });
            }
        },

        /**
         * Load issue comparison between selected scans.
         * @returns {Promise<Object>} Issue comparison
         */
        async loadIssueComparison() {
            if (!oldScanId || !newScanId) {
                throw new Error('Both old and new scans must be selected');
            }

            try {
                const data = await apiRequest(`/issues/${oldScanId}/${newScanId}`);
                issueComparison = data.comparison;

                emit('load', { type: 'issues', comparison: issueComparison });
                return issueComparison;

            } catch (error) {
                emit('error', { type: 'loadIssues', error: error.message });
                throw error;
            }
        },

        // =====================================================================
        // NAVIGATION
        // =====================================================================

        /**
         * Get current change index (within filtered changes).
         * @returns {number}
         */
        getCurrentChangeIndex() {
            return currentChangeIndex;
        },

        /**
         * Get total number of filtered changes.
         * @returns {number}
         */
        getFilteredChangeCount() {
            return navigationOrder.length;
        },

        /**
         * Get the current change row.
         * @returns {Object|null} Current change row
         */
        getCurrentChange() {
            const rowIndex = getCurrentRowIndex();
            if (rowIndex < 0 || !diff || !diff.rows) {
                return null;
            }
            return diff.rows[rowIndex];
        },

        /**
         * Navigate to next change.
         * @returns {Object|null} New current change
         */
        goToNextChange() {
            if (navigationOrder.length === 0) return null;

            currentChangeIndex = Math.min(
                currentChangeIndex + 1,
                navigationOrder.length - 1
            );

            const change = this.getCurrentChange();
            emit('navigate', {
                type: 'next',
                index: currentChangeIndex,
                rowIndex: getCurrentRowIndex(),
                change
            });

            return change;
        },

        /**
         * Navigate to previous change.
         * @returns {Object|null} New current change
         */
        goToPreviousChange() {
            if (navigationOrder.length === 0) return null;

            currentChangeIndex = Math.max(currentChangeIndex - 1, 0);

            const change = this.getCurrentChange();
            emit('navigate', {
                type: 'previous',
                index: currentChangeIndex,
                rowIndex: getCurrentRowIndex(),
                change
            });

            return change;
        },

        /**
         * Navigate to first change.
         * @returns {Object|null} First change
         */
        goToFirstChange() {
            if (navigationOrder.length === 0) return null;

            currentChangeIndex = 0;

            const change = this.getCurrentChange();
            emit('navigate', {
                type: 'first',
                index: currentChangeIndex,
                rowIndex: getCurrentRowIndex(),
                change
            });

            return change;
        },

        /**
         * Navigate to last change.
         * @returns {Object|null} Last change
         */
        goToLastChange() {
            if (navigationOrder.length === 0) return null;

            currentChangeIndex = navigationOrder.length - 1;

            const change = this.getCurrentChange();
            emit('navigate', {
                type: 'last',
                index: currentChangeIndex,
                rowIndex: getCurrentRowIndex(),
                change
            });

            return change;
        },

        /**
         * Navigate to specific change by index.
         * @param {number} index - Change index (0-based)
         * @returns {Object|null} New current change
         */
        goToChange(index) {
            if (navigationOrder.length === 0) return null;

            currentChangeIndex = Math.max(0, Math.min(index, navigationOrder.length - 1));

            const change = this.getCurrentChange();
            emit('navigate', {
                type: 'jump',
                index: currentChangeIndex,
                rowIndex: getCurrentRowIndex(),
                change
            });

            return change;
        },

        /**
         * Navigate to a specific row index.
         * @param {number} rowIndex - Row index in diff.rows
         * @returns {Object|null} Change at that row
         */
        goToRow(rowIndex) {
            const navIndex = navigationOrder.indexOf(rowIndex);
            if (navIndex >= 0) {
                return this.goToChange(navIndex);
            }
            return null;
        },

        // =====================================================================
        // FILTERS
        // =====================================================================

        /**
         * Set a filter value.
         * @param {string} type - Filter type ('showAdded', 'showDeleted', 'showModified')
         * @param {boolean} value - Filter value
         */
        setFilter(type, value) {
            if (filters.hasOwnProperty(type)) {
                filters[type] = value;
                buildNavigationOrder();
                emit('change', { type: 'filter', filters: { ...filters } });
            }
        },

        /**
         * Get current filters.
         * @returns {Object} Filter state
         */
        getFilters() {
            return { ...filters };
        },

        /**
         * Set all filters at once.
         * @param {Object} newFilters - New filter values
         */
        setFilters(newFilters) {
            filters = { ...filters, ...newFilters };
            buildNavigationOrder();
            emit('change', { type: 'filter', filters: { ...filters } });
        },

        // =====================================================================
        // UI STATE
        // =====================================================================

        /**
         * Toggle issues panel collapsed state.
         * @returns {boolean} New collapsed state
         */
        toggleIssuesPanel() {
            issuesPanelCollapsed = !issuesPanelCollapsed;
            emit('change', { type: 'issuesPanel', collapsed: issuesPanelCollapsed });
            return issuesPanelCollapsed;
        },

        /**
         * Check if issues panel is collapsed.
         * @returns {boolean}
         */
        isIssuesPanelCollapsed() {
            return issuesPanelCollapsed;
        },

        /**
         * Check if currently loading.
         * @returns {boolean}
         */
        isLoading() {
            return isLoading;
        },

        // =====================================================================
        // GETTERS
        // =====================================================================

        /**
         * Get document info.
         * @returns {Object|null}
         */
        getDocument() {
            return documentInfo;
        },

        /**
         * Get document ID.
         * @returns {number|null}
         */
        getDocumentId() {
            return documentId;
        },

        /**
         * Get list of scans.
         * @returns {Array}
         */
        getScans() {
            return scans;
        },

        /**
         * Get selected scan IDs.
         * @returns {Object} { oldScanId, newScanId }
         */
        getSelectedScans() {
            return { oldScanId, newScanId };
        },

        /**
         * Get a scan by ID.
         * @param {number} scanId - Scan ID
         * @returns {Object|null} Scan data
         */
        getScan(scanId) {
            return scans.find(s => s.id === scanId) || null;
        },

        /**
         * Get diff result.
         * @returns {Object|null}
         */
        getDiff() {
            return diff;
        },

        /**
         * Get diff statistics.
         * @returns {Object|null}
         */
        getStats() {
            return diff ? diff.stats : null;
        },

        /**
         * Get issue comparison.
         * @returns {Object|null}
         */
        getIssueComparison() {
            return issueComparison;
        },

        /**
         * Get all rows.
         * @returns {Array}
         */
        getRows() {
            return diff ? diff.rows : [];
        },

        /**
         * Get filtered rows (only changes that match current filters).
         * @returns {Array}
         */
        getFilteredRows() {
            if (!diff || !diff.rows) return [];

            return diff.rows.filter(row => {
                if (!row.is_change) return true;  // Always include unchanged
                if (row.status === 'added') return filters.showAdded;
                if (row.status === 'deleted') return filters.showDeleted;
                if (row.status === 'modified') return filters.showModified;
                if (row.status === 'moved_from' || row.status === 'moved_to') return filters.showMoved;
                return true;
            });
        },

        // =====================================================================
        // EVENTS
        // =====================================================================

        /**
         * Subscribe to change events.
         * @param {Function} callback
         * @returns {Function} Unsubscribe function
         */
        onChange(callback) {
            return subscribe('change', callback);
        },

        /**
         * Subscribe to navigation events.
         * @param {Function} callback
         * @returns {Function} Unsubscribe function
         */
        onNavigate(callback) {
            return subscribe('navigate', callback);
        },

        /**
         * Subscribe to load events.
         * @param {Function} callback
         * @returns {Function} Unsubscribe function
         */
        onLoad(callback) {
            return subscribe('load', callback);
        },

        /**
         * Subscribe to error events.
         * @param {Function} callback
         * @returns {Function} Unsubscribe function
         */
        onError(callback) {
            return subscribe('error', callback);
        },

        // =====================================================================
        // CLEANUP
        // =====================================================================

        /**
         * Clean up state for modal close.
         * v4.6.1: Only reset data state, preserve event listeners.
         * Listeners are set up once in DocCompare.init() and must persist
         * across open/close cycles.
         */
        cleanup() {
            this.reset();
            // v4.6.1: Do NOT clear listeners here — they are registered once
            // in DocCompare.init() and must survive across modal open/close cycles.
            // Previously this cleared all listeners, causing the modal to be
            // blank/broken on second open.
        }
    };
})();

// Log initialization
console.log('[TWR DocCompare] Module loaded');
