/**
 * AEGIS - State Management Module
 * @version 3.0.47
 *
 * Centralized application state and filter state management.
 *
 * v3.0.47: Fixed memory leak - clear existing poll interval before creating new one
 * v3.0.46: Migrated filter persistence to TWR.Storage
 * v3.0.32: Added job-based progress polling to LoadingTracker
 * v3.0.29: Added validation filter UI support
 *
 * Dependencies: TWR.Storage (for persistence), TWR.Utils (optional, for storage helpers)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.State = (function() {
    
    // ========================================
    // CONSTANTS
    // ========================================
    
    const SEVERITY_ORDER = { 
        'Critical': 0, 
        'High': 1, 
        'Medium': 2, 
        'Low': 3, 
        'Info': 4 
    };
    
    const SEVERITY_COLORS = {
        'Critical': '#DC3545',
        'High': '#FD7E14',
        'Medium': '#FFC107',
        'Low': '#28A745',
        'Info': '#17A2B8'
    };
    
    // ========================================
    // MAIN APPLICATION STATE
    // ========================================
    
    const State = {
        // Document info
        filename: null,
        fileType: null,
        filepath: null,
        documentId: null,
        
        // Issues
        issues: [],
        filteredIssues: [],
        selectedIssues: new Set(),
        reviewResults: null,
        
        // Roles
        roles: {},
        entities: {
            roles: [],        // kind === 'role' only
            deliverables: [], // kind === 'deliverable' only
            unknown: []       // needs manual review
        },
        roleNetwork: null,
        adjudicatedRoles: null,
        
        // UI state
        isLoading: false,
        csrfToken: null,
        currentPage: 1,
        pageSize: 50,
        sortColumn: 'severity',
        sortDirection: 'asc',
        
        // Server info
        capabilities: {},
        serverVersion: null,
        
        // Statement Forge support
        currentText: null,
        currentFilename: null,
        
        // User settings
        settings: {
            darkMode: false,
            compactMode: false,
            showCharts: false,  // Analytics collapsed by default
            autoReview: false,
            rememberChecks: true,
            pageSize: 50
        },
        
        // Custom filters
        filters: {
            customFilter: null,       // Function: (issue, idx) => boolean
            customFilterLabel: null   // String label for the filter
        },
        
        // Workflow state
        workflow: {
            reviewLog: [],           // Array of {issue_id, action, note, timestamp, reviewer}
            issueFamilies: new Map(), // pattern -> [issue_ids]
            familyActions: new Map()  // pattern -> {action, note}
        }
    };
    
    // ========================================
    // FILTER STATE
    // ========================================
    
    const FilterState = {
        chartFilter: null,      // { type: 'severity'|'category', value: string }
        categorySearch: '',
        validationFilter: null, // null = all, 'validated' = only validated, 'unvalidated' = only unvalidated
        
        /**
         * Save current filter state to storage
         * v3.0.46: Uses TWR.Storage for unified persistence
         */
        save() {
            const filterData = {
                severities: Array.from(document.querySelectorAll('.sev-filter input:checked')).map(cb => cb.id),
                categories: Array.from(document.querySelectorAll('#category-list input:checked')).map(cb => cb.dataset.category),
                validationFilter: this.validationFilter
            };
            
            if (window.TWR?.Storage?.filters) {
                TWR.Storage.filters.setAll(filterData);
            }
        },
        
        /**
         * Restore filter state from storage
         * v3.0.46: Uses TWR.Storage for unified persistence
         */
        restore() {
            const saved = window.TWR?.Storage?.filters?.getAll();
            if (saved?.severities) {
                document.querySelectorAll('.sev-filter input').forEach(cb => {
                    cb.checked = saved.severities.includes(cb.id);
                });
            }
            if (saved?.validationFilter !== undefined) {
                this.validationFilter = saved.validationFilter;
            }
        },
        
        /**
         * Clear all filter state
         */
        clear() {
            this.chartFilter = null;
            this.categorySearch = '';
            this.validationFilter = null;
            
            if (window.TWR?.Storage?.filters) {
                TWR.Storage.filters.clear();
            }
        },
        
        /**
         * Set validation filter
         * @param {string|null} filter - 'validated', 'unvalidated', or null for all
         */
        setValidationFilter(filter) {
            this.validationFilter = filter;
            this.save();
        },
        
        /**
         * Check if an issue passes the validation filter
         * @param {Object} issue - Issue object with optional source.is_validated
         * @returns {boolean} True if issue passes filter
         */
        passesValidationFilter(issue) {
            if (this.validationFilter === null) return true;
            
            const isValidated = issue?.source?.is_validated === true;
            
            if (this.validationFilter === 'validated') {
                return isValidated;
            } else if (this.validationFilter === 'unvalidated') {
                return !isValidated;
            }
            return true;
        }
    };
    
    // ========================================
    // GRAPH STATE (D3 Visualization)
    // ========================================
    
    const GraphState = {
        svg: null,
        simulation: null,
        data: null,
        selectedNode: null,
        highlightedNodes: new Set(),
        isPinned: false,
        fallbackRows: [],
        fallbackData: null
    };
    
    // ========================================
    // LOADING TRACKER (v3.0.32: Job-based progress)
    // ========================================
    
    const LoadingTracker = {
        startTime: null,
        totalItems: 0,
        processedItems: 0,
        operationType: null,
        abortController: null,
        
        // v3.0.32: Job-based progress
        // BUG-M16 FIX: Increased from 500ms to 2000ms to avoid rate limiting
        currentJobId: null,
        pollInterval: null,
        pollFrequency: 2000, // ms - was 500ms, caused "Too many requests" errors
        
        /**
         * Start tracking a new operation
         * @param {string} operationType - Description of operation
         * @param {number} totalItems - Expected total items (for ETA)
         */
        start(operationType, totalItems = 0) {
            this.startTime = performance.now();
            this.totalItems = totalItems;
            this.processedItems = 0;
            this.operationType = operationType;
            this.abortController = new AbortController();
            this.currentJobId = null;
        },
        
        /**
         * v3.0.32: Start job-based progress tracking
         * v3.0.47: Fixed memory leak - clear existing interval before creating new one
         * @param {string} jobId - Job ID to track
         * @param {Function} onProgress - Callback with progress data
         * @param {Function} onComplete - Callback when job completes
         * @param {Function} onError - Callback on error
         */
        startJobPolling(jobId, onProgress, onComplete, onError) {
            // v3.0.47: Prevent interval accumulation - clear any existing interval first
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }

            this.currentJobId = jobId;
            this.startTime = performance.now();

            const poll = async () => {
                try {
                    const response = await fetch(`/api/job/${jobId}`);
                    const data = await response.json();
                    
                    if (!data.success) {
                        if (onError) onError(data.error);
                        this.stopJobPolling();
                        return;
                    }
                    
                    const job = data.job;
                    
                    // Update progress callback
                    if (onProgress) {
                        onProgress({
                            phase: job.progress.phase,
                            phaseProgress: job.progress.phase_progress,
                            overallProgress: job.progress.overall_progress,
                            currentChecker: job.progress.current_checker,
                            checkersCompleted: job.progress.checkers_completed,
                            checkersTotal: job.progress.checkers_total,
                            lastLog: job.progress.last_log,
                            elapsed: job.elapsed,
                            eta: job.eta
                        });
                    }
                    
                    // Check if complete
                    if (job.status === 'complete') {
                        this.stopJobPolling();
                        if (onComplete) {
                            // Fetch with result
                            const resultResp = await fetch(`/api/job/${jobId}?include_result=true`);
                            const resultData = await resultResp.json();
                            onComplete(resultData.job);
                        }
                    } else if (job.status === 'failed' || job.status === 'cancelled') {
                        this.stopJobPolling();
                        if (onError) onError(job.error || `Job ${job.status}`);
                    }
                    
                } catch (err) {
                    console.error('[TWR] Job poll error:', err);
                    if (onError) onError(err.message);
                    this.stopJobPolling();
                }
            };
            
            // Start polling
            this.pollInterval = setInterval(poll, this.pollFrequency);
            poll(); // Initial poll
        },
        
        /**
         * v3.0.32: Stop job polling
         */
        stopJobPolling() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
            this.currentJobId = null;
        },
        
        /**
         * Update progress and recalculate ETA
         * @param {number} processed - Items processed so far
         * @param {number} total - Total items (optional update)
         */
        updateProgress(processed, total) {
            this.processedItems = processed;
            if (total) this.totalItems = total;
            this.updateETA();
            this.updateItemsDisplay();
        },
        
        /**
         * Update ETA display
         */
        updateETA() {
            if (!this.startTime || this.processedItems === 0) return;
            
            const elapsed = performance.now() - this.startTime;
            const avgTimePerItem = elapsed / this.processedItems;
            const remainingItems = this.totalItems - this.processedItems;
            const estimatedRemaining = avgTimePerItem * remainingItems;
            
            const etaEl = document.getElementById('loading-eta');
            const etaContainer = document.getElementById('loading-eta-container');
            
            if (etaEl && etaContainer && this.totalItems > 0) {
                etaContainer.style.display = 'flex';
                if (estimatedRemaining < 1000) {
                    etaEl.textContent = 'almost done...';
                } else if (estimatedRemaining < 60000) {
                    etaEl.textContent = `~${Math.ceil(estimatedRemaining / 1000)} seconds`;
                } else {
                    const mins = Math.floor(estimatedRemaining / 60000);
                    const secs = Math.ceil((estimatedRemaining % 60000) / 1000);
                    etaEl.textContent = `~${mins}m ${secs}s`;
                }
            }
        },
        
        /**
         * Update items progress display
         */
        updateItemsDisplay() {
            const itemsEl = document.getElementById('loading-items');
            if (itemsEl && this.totalItems > 0) {
                itemsEl.style.display = 'block';
                itemsEl.textContent = `Processing item ${this.processedItems} of ${this.totalItems}...`;
            }
        },
        
        /**
         * Reset tracker state
         */
        reset() {
            this.stopJobPolling();
            this.startTime = null;
            this.totalItems = 0;
            this.processedItems = 0;
            this.operationType = null;
            if (this.abortController) {
                this.abortController = null;
            }
            
            const etaContainer = document.getElementById('loading-eta-container');
            const itemsEl = document.getElementById('loading-items');
            const cancelBtn = document.getElementById('loading-cancel');
            
            if (etaContainer) etaContainer.style.display = 'none';
            if (itemsEl) itemsEl.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
        },
        
        /**
         * Get abort signal for cancellable fetch requests
         * @returns {AbortSignal|undefined}
         */
        getAbortSignal() {
            return this.abortController?.signal;
        },
        
        /**
         * Abort current operation
         */
        abort() {
            if (this.abortController) {
                this.abortController.abort();
            }
            this.stopJobPolling();
            
            // Cancel job on server if we have one
            if (this.currentJobId) {
                fetch(`/api/job/${this.currentJobId}/cancel`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': State.csrfToken
                    }
                }).catch(() => {});
            }
        }
    };
    
    // ========================================
    // ADJUDICATION STATE
    // ========================================
    
    const AdjudicationState = {
        decisions: new Map(),  // roleId -> decision
        notes: new Map(),      // roleId -> notes
        
        /**
         * Set decision for a role
         * @param {string} roleId - Role identifier
         * @param {string} decision - 'confirmed'|'deliverable'|'rejected'|'pending'
         * @param {string} note - Optional note
         */
        setDecision(roleId, decision, note = '') {
            this.decisions.set(roleId, decision);
            if (note) this.notes.set(roleId, note);
        },
        
        /**
         * Get decision for a role
         * @param {string} roleId - Role identifier
         * @returns {string|undefined}
         */
        getDecision(roleId) {
            return this.decisions.get(roleId);
        },
        
        /**
         * Clear all decisions
         */
        clear() {
            this.decisions.clear();
            this.notes.clear();
        },
        
        /**
         * Export decisions as array
         * @returns {Array}
         */
        toArray() {
            return Array.from(this.decisions.entries()).map(([id, decision]) => ({
                roleId: id,
                decision,
                note: this.notes.get(id) || ''
            }));
        }
    };
    
    // ========================================
    // STATE RESET
    // ========================================
    
    /**
     * Reset application state for new document
     * Preserves settings and capabilities
     */
    function resetForNewDocument() {
        console.log('[TWR] Resetting state for new document...');
        
        // Stop any running D3 simulation
        if (GraphState.simulation) {
            GraphState.simulation.stop();
            GraphState.simulation = null;
        }
        
        // Clear GraphState
        GraphState.data = null;
        GraphState.svg = null;
        GraphState.selectedNode = null;
        GraphState.highlightedNodes.clear();
        GraphState.isPinned = false;
        GraphState.fallbackRows = [];
        GraphState.fallbackData = null;
        
        // Clear main State (preserve settings and capabilities)
        State.filename = null;
        State.fileType = null;
        State.filepath = null;
        State.documentId = null;
        State.issues = [];
        State.filteredIssues = [];
        State.selectedIssues.clear();
        State.reviewResults = null;
        State.roles = {};
        State.entities = { roles: [], deliverables: [], unknown: [] };
        State.roleNetwork = null;
        State.currentPage = 1;
        State.sortColumn = 'severity';
        State.sortDirection = 'asc';
        State.adjudicatedRoles = null;
        State.currentText = null;
        State.currentFilename = null;
        
        // Clear filters
        State.filters.customFilter = null;
        State.filters.customFilterLabel = null;
        
        // Clear workflow state
        State.workflow.reviewLog = [];
        State.workflow.issueFamilies.clear();
        State.workflow.familyActions.clear();
        
        // Clear FilterState chart filter
        FilterState.chartFilter = null;
        
        // Clear AdjudicationState
        AdjudicationState.clear();
        
        // Clear any tooltips that might be lingering
        if (typeof d3 !== 'undefined' && d3) {
            d3.selectAll('.graph-tooltip').remove();
        }
        
        // Remove any existing graph content
        const graphSvg = document.getElementById('roles-graph-svg');
        if (graphSvg) {
            graphSvg.innerHTML = ''; // SAFE: clearing element
        }
        
        console.log('[TWR] State reset complete');
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // Constants
        SEVERITY_ORDER,
        SEVERITY_COLORS,
        
        // State objects
        State,
        FilterState,
        GraphState,
        LoadingTracker,
        AdjudicationState,
        
        // Methods
        resetForNewDocument
    };
})();

// ========================================
// GLOBAL ALIASES (for backward compatibility)
// ========================================

window.State = TWR.State.State;
window.FilterState = TWR.State.FilterState;
window.GraphState = TWR.State.GraphState;
window.LoadingTracker = TWR.State.LoadingTracker;
window.AdjudicationState = TWR.State.AdjudicationState;
window.SEVERITY_ORDER = TWR.State.SEVERITY_ORDER;
window.SEVERITY_COLORS = TWR.State.SEVERITY_COLORS;
window.resetStateForNewDocument = TWR.State.resetForNewDocument;

console.log('[TWR] State module loaded');
