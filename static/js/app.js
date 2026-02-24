/**
 * AEGIS v3.0.103 - Enterprise Document Analysis Tool
 * 
 * v3.0.103 Changes:
 * - innerHTML safety audit - all 143 usages verified and documented
 * - CSS modularized into 10 logical files for maintainability
 * - Test suite modernized with docstrings and FAV2 API tests
 * - Exception handling refined with specific catches
 * 
 * v3.0.101: Standardized API responses, centralized strings, JSDoc
 * v3.0.100: ReDoS protection, WAL mode, file size validation
 * v3.0.97: Fix Assistant v2 premium document review interface
 * 
 * Features:
 * - CSRF protection
 * - PDF and DOCX file support
 * - Real-time issue filtering and search
 * - Export to Word (with tracked changes), CSV, JSON
 * - D3.js interactive roles graph visualization
 * - Role extraction with alias merging and confidence scores
 * - Responsibility matrix (RACI-style)
 * - Issue baselines and suppression
 * - Dashboard analytics
 * - Keyboard shortcuts
 * - Dark mode support
 * - Scan history and profiles
 * 
 * Created by Nicholas Georgeson
 */

/**
 * AEGIS v3.0.19 - Enterprise Document Analysis Tool
 * 
 * v3.0.19 Changes:
 * - Extracted roles functionality to TWR.Roles module (~1,800 LOC)
 * - Module includes: RACI matrix, adjudication, D3 graph, role exports
 * - All modules: TWR.Utils, TWR.State, TWR.API, TWR.Modals, TWR.Events, TWR.Renderers, TWR.Roles
 * - ~5,450 LOC now in 7 modules
 * - app.js reduced from ~11,500 to ~8,800 LOC
 * 
 * v3.0.18 Changes:
 * - Extracted rendering functions to TWR.Renderers module (~1,200 LOC)
 * - Module includes: renderIssuesList, renderCharts, updateStats, dashboard components
 * - All modules: TWR.Utils, TWR.State, TWR.API, TWR.Modals, TWR.Events, TWR.Renderers
 * - ~3,660 LOC now in 6 modules
 * 
 * v3.0.17 Changes:
 * - Extracted event handling to TWR.Events module (~560 LOC)
 * - Module includes: initEventListeners, initDragDrop, initKeyboardShortcuts
 * - Keyboard navigation for issue list moved to module
 * - All modules: TWR.Utils, TWR.State, TWR.API, TWR.Modals, TWR.Events
 * - ~2,460 LOC now in 5 modules
 * 
 * v3.0.15 Fixes:
 * - Migrated all 40 inline onclick handlers to addEventListener
 * - All event bindings centralized in initEventListeners()
 * 
 * v3.0.12-v3.0.14:
 * - Role/Deliverable separation: exports now contain only roles (not deliverables)
 * - Fixed Statement Forge overwriting main review results
 * - Consolidated settings to single localStorage key
 * 
 * Features:
 * - CSRF protection with automatic refresh
 * - PDF and DOCX file support
 * - Real-time issue filtering and search
 * - Export to Word (with tracked changes), CSV, JSON
 * - D3.js interactive roles graph visualization
 * - Role extraction with alias merging and confidence scores
 * - Responsibility matrix (RACI-style)
 * - Issue baselines and suppression
 * - Dashboard analytics
 * - Keyboard shortcuts (? for help)
 * - Dark mode support
 * - Scan history and profiles
 * 
 * Created by Nicholas Georgeson
 */

'use strict';

// ============================================================
// MODULE DETECTION & FALLBACK SETUP
// ============================================================
// Modules are loaded before app.js in index.html
// If modules loaded successfully, we use them; otherwise inline fallback

(function() {
    const modules = {
        utils: typeof window.TWR?.Utils === 'object',
        state: typeof window.TWR?.State === 'object',
        api: typeof window.TWR?.API === 'object',
        modals: typeof window.TWR?.Modals === 'object',
        events: typeof window.TWR?.Events === 'object',
        renderers: typeof window.TWR?.Renderers === 'object',
        roles: typeof window.TWR?.Roles === 'object',
        triage: typeof window.TWR?.Triage === 'object',
        families: typeof window.TWR?.Families === 'object'
    };
    
    const loadedCount = Object.values(modules).filter(Boolean).length;
    console.log(`[TWR] Module check: ${loadedCount}/9 modules loaded`, modules);
    
    if (loadedCount === 9) {
        console.log('[TWR] All modules loaded - using modular architecture');
    } else if (loadedCount > 0) {
        console.warn('[TWR] Partial modules loaded - hybrid mode');
    } else {
        console.log('[TWR] No modules loaded - using inline fallback definitions');
    }
})();

// Global guard to prevent duplicate file processing
window._TWR_fileProcessing = false;
window._TWR_lastFileTime = 0;

/**
 * v5.9.2: Reset upload state so user can select a new file
 * Called after scan completes, HV validation completes, or any processing exit path
 */
function resetUploadState() {
    window._TWR_fileProcessing = false;
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';
    console.log('[TWR] Upload state reset — ready for new file');
}

// ============================================================
// GLOBAL STATE - Use module or inline fallback
// ============================================================
const State = window.State || window.TWR?.State?.State || {
    filename: null,
    fileType: null,
    filepath: null,
    documentId: null,
    issues: [],
    filteredIssues: [],
    selectedIssues: new Set(),
    reviewResults: null,
    roles: {},
    entities: {
        roles: [],
        deliverables: [],
        unknown: []
    },
    roleNetwork: null,
    isLoading: false,
    csrfToken: null,
    currentPage: 1,
    pageSize: 50,
    sortColumn: 'severity',
    sortDirection: 'asc',
    capabilities: {},
    currentText: null,
    currentFilename: null,
    settings: {
        darkMode: false,
        compactMode: false,
        showCharts: false,
        autoReview: false,
        rememberChecks: true,
        pageSize: 50,
        essentialsMode: false
    },
    filters: {
        customFilter: null,
        customFilterLabel: null
    },
    workflow: {
        reviewLog: [],
        issueFamilies: new Map(),
        familyActions: new Map()
    }
};

// Expose State globally for module compatibility
if (!window.State) window.State = State;

// Severity constants - use module or define inline
const SEVERITY_ORDER = window.SEVERITY_ORDER || window.TWR?.State?.SEVERITY_ORDER || 
    { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4 };
const SEVERITY_COLORS = window.SEVERITY_COLORS || window.TWR?.State?.SEVERITY_COLORS || {
    'Critical': '#DC3545',
    'High': '#FD7E14', 
    'Medium': '#FFC107',
    'Low': '#28A745',
    'Info': '#17A2B8'
};

// ============================================================
// v3.0.101 ISSUE-009: CENTRALIZED USER-FACING STRINGS
// ============================================================
// All user-facing messages are centralized here for consistency
// and easier future internationalization (i18n) support.
const STRINGS = window.STRINGS || {
    errors: {
        noFile: 'No file selected',
        uploadFailed: 'Upload failed. Please try again.',
        reviewFailed: 'Review failed. Check the console for details.',
        exportFailed: 'Export failed. Please try again.',
        networkError: 'Network error. Please check your connection.',
        sessionExpired: 'Session expired. Please refresh the page.',
        invalidFile: 'Invalid file type',
        fileTooLarge: 'File exceeds maximum size limit',
        serverError: 'Server error occurred',
        unknownError: 'An unexpected error occurred'
    },
    loading: {
        default: 'Loading...',
        processing: 'Processing document...',
        uploading: 'Uploading file...',
        analyzing: 'Analyzing document...',
        processingRoles: 'Processing roles...',
        generatingExport: 'Generating export...',
        savingChanges: 'Saving changes...',
        almostDone: 'almost done...'
    },
    success: {
        uploadComplete: 'File uploaded successfully',
        reviewComplete: 'Review completed',
        exportComplete: 'Export generated successfully',
        saved: 'Changes saved',
        copied: 'Copied to clipboard'
    },
    labels: {
        selectFile: 'Select a file',
        dragDropHint: 'or drag and drop here',
        noIssuesFound: 'No issues found',
        noResultsMatch: 'No results match your filters',
        loadingResults: 'Loading results...'
    },
    confirmations: {
        deleteAll: 'Are you sure you want to delete all items?',
        discardChanges: 'Discard unsaved changes?',
        clearHistory: 'Clear all history?'
    }
};

// Expose STRINGS globally
if (!window.STRINGS) window.STRINGS = STRINGS;

// ============================================================
// LOADING TRACKER - Use module or inline fallback
// ============================================================
const LoadingTracker = window.LoadingTracker || window.TWR?.State?.LoadingTracker || {
    startTime: null,
    totalItems: 0,
    processedItems: 0,
    operationType: null,
    abortController: null,
    
    start(operationType, totalItems = 0) {
        this.startTime = performance.now();
        this.totalItems = totalItems;
        this.processedItems = 0;
        this.operationType = operationType;
        this.abortController = new AbortController();
    },
    
    updateProgress(processed, total) {
        this.processedItems = processed;
        if (total) this.totalItems = total;
        this.updateETA();
        this.updateItemsDisplay();
    },
    
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
    
    updateItemsDisplay() {
        const itemsEl = document.getElementById('loading-items');
        if (itemsEl && this.totalItems > 0) {
            itemsEl.style.display = 'block';
            itemsEl.textContent = `Processing item ${this.processedItems} of ${this.totalItems}...`;
        }
    },
    
    reset() {
        this.startTime = null;
        this.totalItems = 0;
        this.processedItems = 0;
        this.operationType = null;
        this.abortController = null;
        
        const etaContainer = document.getElementById('loading-eta-container');
        const itemsEl = document.getElementById('loading-items');
        const cancelBtn = document.getElementById('loading-cancel');
        
        if (etaContainer) etaContainer.style.display = 'none';
        if (itemsEl) itemsEl.style.display = 'none';
        if (cancelBtn) cancelBtn.style.display = 'none';
    },
    
    getAbortSignal() {
        return this.abortController?.signal;
    },
    
    abort() {
        if (this.abortController) {
            this.abortController.abort();
        }
    }
};

if (!window.LoadingTracker) window.LoadingTracker = LoadingTracker;

// Cancel current operation
function cancelCurrentOperation() {
    LoadingTracker.abort();
    hideLoading();
    toast('warning', 'Operation cancelled');
}
window.cancelCurrentOperation = cancelCurrentOperation;

// ============================================================
// LOADING FUNCTIONS - Module wrappers with fallback
// ============================================================
function showLoading(message, options = {}) {
    // Use module if available
    if (window.TWR?.Modals?.showLoading) {
        return TWR.Modals.showLoading(message, options);
    }
    
    // Inline fallback
    const progress = options.progress || 0;
    
    if (options.totalItems) {
        LoadingTracker.start(message, options.totalItems);
    }
    
    const cancelBtn = document.getElementById('loading-cancel');
    if (cancelBtn && options.showCancel) {
        cancelBtn.style.display = 'inline-flex';
    }
    
    if (typeof setLoading === 'function') {
        setLoading(true, message || 'Loading...', progress);
    } else {
        let overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            const msgEl = overlay.querySelector('.loading-message, #loading-text');
            if (msgEl) msgEl.textContent = message || 'Loading...';
            const progressBar = overlay.querySelector('.loading-progress-bar, #loading-progress-bar');
            if (progressBar) progressBar.style.width = `${progress}%`;
        }
    }
    
    State.isLoading = true;
    console.log('[TWR] Loading:', message);
}

function updateLoadingMessage(message, options = {}) {
    if (window.TWR?.Modals?.updateLoadingMessage) {
        return TWR.Modals.updateLoadingMessage(message, options);
    }
    
    if (typeof updateProgress === 'function' && options.progress !== undefined) {
        updateProgress(options.progress, message);
    } else {
        const msgEl = document.querySelector('.loading-message, #loading-text');
        if (msgEl && message) msgEl.textContent = message;
        
        if (options.progress !== undefined) {
            const progressBar = document.querySelector('.loading-progress-bar, #loading-progress-bar');
            if (progressBar) progressBar.style.width = `${options.progress}%`;
        }
    }
    
    if (options.currentItem !== undefined && options.totalItems !== undefined) {
        LoadingTracker.updateProgress(options.currentItem, options.totalItems);
    }
    
    console.log('[TWR] Loading update:', message);
}

function hideLoading() {
    if (window.TWR?.Modals?.hideLoading) {
        return TWR.Modals.hideLoading();
    }
    
    if (typeof setLoading === 'function') {
        setLoading(false);
    } else {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
    
    LoadingTracker.reset();
    State.isLoading = false;
    console.log('[TWR] Loading hidden');
}

// Make loading functions globally available
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.updateLoadingMessage = updateLoadingMessage;
// ============================================================
// v2.9.1 FIX C5: STATE RESET FOR NEW DOCUMENT
// ============================================================
// DOCUMENT ID GENERATION (v3.0.109)
// ============================================================
/**
 * Generate a unique document ID for State.documentId
 * Used for triage baseline features and scan history correlation.
 * 
 * v3.0.109: Added to fix Issue #7 - documentId not being set after fresh review
 * 
 * @returns {string} Unique document identifier
 */
function generateGlobalDocumentId() {
    // Use available State fields
    const name = State.filename || State.currentFilename || `doc_${Date.now()}`;
    const fileType = State.fileType || 'unknown';
    // Use analysis timestamp to differentiate same-file reviews
    const timestamp = State.reviewResults?.analyzed_at || Date.now();
    
    // Create simple hash from combined values
    const combined = `${name}|${fileType}|${timestamp}`;
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
        const char = combined.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    
    // Return readable ID: filename_hash (truncated for readability)
    const hashStr = Math.abs(hash).toString(36).substring(0, 8);
    const safeName = name.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
    return `${safeName}_${hashStr}`;
}

// ============================================================
// STATE RESET
// ============================================================
/**
 * Reset application state when loading a new document.
 * This prevents app freeze/unresponsiveness on 2nd document scan.
 */
function resetStateForNewDocument() {
    console.log('[TWR] Resetting state for new document...');

    // v5.0.2: Force-clear any stuck loading overlays and scan progress dashboards
    setLoading(false);
    LoadingTracker.reset();
    if (typeof TWR !== 'undefined' && TWR.ScanProgress?.isActive()) {
        try { TWR.ScanProgress.destroy(); } catch(e) {}
    }
    // Reset the graph loading guard to prevent "already loading" blocks
    GraphState.isLoading = false;

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
    State.roleNetwork = null;
    State.currentPage = 1;
    State.sortColumn = 'severity';
    State.sortDirection = 'asc';
    State.adjudicatedRoles = null;
    
    // v3.0.100: Reset entities to prevent state pollution (ISSUE-006)
    State.entities = {
        roles: [],
        deliverables: [],
        unknown: []
    };
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
    if (typeof FilterState !== 'undefined' && FilterState.chartFilter !== undefined) {
        FilterState.chartFilter = null;
    }
    
    // Clear AdjudicationState if it exists
    if (typeof AdjudicationState !== 'undefined' && AdjudicationState.decisions) {
        AdjudicationState.decisions.clear();
    }
    
    // Clear any tooltips that might be lingering
    if (typeof d3 !== 'undefined' && d3) d3.selectAll('.graph-tooltip').remove();
    
    // Remove any existing graph content
    const graphSvg = document.getElementById('roles-graph-svg');
    if (graphSvg) {
        graphSvg.innerHTML = '';
    }

    // Reset document status indicator to "no document" state
    const statusIndicator = document.getElementById('doc-status-indicator');
    const statusText = document.getElementById('doc-status-text');
    if (statusIndicator && statusText) {
        statusIndicator.classList.remove('loaded', 'reviewed');
        statusText.classList.remove('loaded', 'reviewed');
        statusIndicator.innerHTML = '<i data-lucide="file-x"></i>';
        statusText.textContent = 'No document loaded';
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    console.log('[TWR] State reset complete');
}

// ============================================================
// INITIALIZATION
// ============================================================

// v3.1.9: Simplified initialization (removed initial AEGIS loader - app loads fast enough)
document.addEventListener('DOMContentLoaded', async () => {
    // v5.9.35: Report real boot progress to loading screen
    if (window._aegisBootProgress) window._aegisBootProgress('dom', 'DOM ready');

    await initCSRF();
    await checkCapabilities();
    await loadVersionLabel();
    if (window._aegisBootProgress) window._aegisBootProgress('core', 'Core systems loaded');

    initUI();
    initDragDrop();
    initEventListeners();
    initTopNav();  // v3.0.32: Initialize top nav bar
    initSidebarState();  // v3.0.44: Restore sidebar collapse state
    initScanHistoryEventDelegation();
    if (window._aegisBootProgress) window._aegisBootProgress('features', 'UI initialized');

    initKeyboardShortcuts();
    initThemeToggle();
    loadSettings();
    if (window._aegisBootProgress) window._aegisBootProgress('state', 'Settings loaded');

    // Try to restore previous session (for back button support)
    const sessionRestored = restoreSessionState();

    // Initialize document status indicator (if no session restored, ensure it shows "no document")
    if (!sessionRestored) {
        const statusIndicator = document.getElementById('doc-status-indicator');
        const statusText = document.getElementById('doc-status-text');
        if (statusIndicator && statusText) {
            statusIndicator.innerHTML = '<i data-lucide="file-x"></i>';
            statusText.textContent = 'No document loaded';
        }
    }

    // Safely call lucide - it may not be loaded yet (CDN)
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        try { lucide.createIcons(); } catch(e) { console.warn('[TWR] Lucide init deferred:', e); }
    }

    // v4.0.3: Pre-load adjudication cache for tool-wide badges
    if (window.AEGIS?.AdjudicationLookup) {
        AEGIS.AdjudicationLookup.ensureLoaded().catch(e => console.warn('[TWR] Adj cache preload:', e));
    }

    // v4.5.1: Show standalone landing page on load
    // Always show landing if no session restored; show() handles init() with proper await
    if (typeof TWR !== 'undefined' && TWR.LandingPage) {
        if (!sessionRestored) {
            TWR.LandingPage.show();
        } else {
            // Pre-initialize so tiles are ready if user navigates back to landing
            TWR.LandingPage.init();
        }
    }
    if (window._aegisBootProgress) window._aegisBootProgress('landing', 'Dashboard ready');

    // v5.9.35: Final boot progress + dismiss cinematic boot sequence
    if (window._aegisBootProgress) window._aegisBootProgress('ready', 'All systems online');

    // v5.9.30: Failsafe dismiss of cinematic boot sequence
    if (window._aegisBootDismiss) {
        window._aegisBootDismiss();
    } else {
        const ail = document.getElementById('aegis-init-loader');
        if (ail && !ail.classList.contains('ail-done')) { ail.classList.add('ail-done'); setTimeout(() => ail.remove(), 700); }
    }
});

// v3.0.32: Initialize top navigation bar
function initTopNav() {
    if (window.TWR?.Events?.initTopNav) {
        TWR.Events.initTopNav();
    }
}

// v3.0.44: Initialize sidebar state from localStorage
function initSidebarState() {
    if (window.TWR?.Events?.initSidebarState) {
        TWR.Events.initSidebarState();
    }
}

// Theme toggle functionality (v3.0.46: uses TWR.Storage)
// v5.0.0: Default to DARK mode. Instant dark applied via inline script in <head>
function initThemeToggle() {
    // v3.0.46: Use unified storage if available, fallback to direct localStorage
    const savedTheme = window.TWR?.Storage?.ui
        ? TWR.Storage.ui.getTheme()
        : localStorage.getItem('twr-theme');

    // v5.0.0: Default to DARK mode — only use light if explicitly saved as light
    const isDark = savedTheme !== 'light';

    if (isDark) {
        document.body.classList.add('dark-mode');
        document.documentElement.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
        document.documentElement.classList.remove('dark-mode');
        // v5.9.5: Clear FOUC inline styles that override CSS file light mode variables
        // The FOUC prevention script in index.html sets inline --text-primary, --bg-deep etc.
        // for dark mode. When light mode is stored, these must be cleared so base.css takes effect.
        const htmlEl = document.documentElement;
        const bodyEl = document.body;
        htmlEl.style.removeProperty('background-color');
        htmlEl.style.removeProperty('color');
        htmlEl.style.removeProperty('--bg-deep');
        htmlEl.style.removeProperty('--bg-primary');
        htmlEl.style.removeProperty('--text-primary');
        htmlEl.style.removeProperty('--bg-secondary');
        bodyEl.style.removeProperty('background-color');
        bodyEl.style.removeProperty('color');
    }
    // v5.9.1: Sync data-theme attribute on BOTH html and body
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
    updateThemeIcons(isDark);

    // Toggle button handler
    document.getElementById('btn-theme-toggle')?.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    // v5.0.0: Sync html element too (for instant dark mode on reload)
    document.documentElement.classList.toggle('dark-mode', isDark);
    // v5.9.5: Sync data-theme attribute on BOTH html and body (body gets data-theme="dark"
    // from FOUC script in index.html — must be cleared when toggling to light mode)
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');

    // v5.9.5: Clear/set FOUC inline styles — inline CSS variables on <html> have highest
    // specificity and override stylesheet values. Must be cleared when switching to light mode
    // or updated when switching to dark mode (originally set by FOUC prevention script in index.html)
    const htmlEl = document.documentElement;
    const bodyEl = document.body;
    if (isDark) {
        // Set dark mode inline vars for FOUC prevention on reload
        htmlEl.style.setProperty('background-color', '#0d1117');
        htmlEl.style.setProperty('color', '#e6edf3');
        htmlEl.style.setProperty('--bg-deep', '#0d1117');
        htmlEl.style.setProperty('--bg-primary', '#161b22');
        htmlEl.style.setProperty('--text-primary', '#e6edf3');
        htmlEl.style.setProperty('--bg-secondary', '#1c2128');
        // v5.9.18: Body stays transparent so particle canvas shows through gaps
        bodyEl.style.removeProperty('background-color');
        bodyEl.style.setProperty('color', '#e6edf3');
    } else {
        // Clear inline overrides so CSS file values take effect
        htmlEl.style.removeProperty('background-color');
        htmlEl.style.removeProperty('color');
        htmlEl.style.removeProperty('--bg-deep');
        htmlEl.style.removeProperty('--bg-primary');
        htmlEl.style.removeProperty('--text-primary');
        htmlEl.style.removeProperty('--bg-secondary');
        bodyEl.style.removeProperty('background-color');
        bodyEl.style.removeProperty('color');
    }

    // v3.0.46: Use unified storage if available
    if (window.TWR?.Storage?.ui) {
        TWR.Storage.ui.setTheme(isDark ? 'dark' : 'light');
    } else {
        localStorage.setItem('twr-theme', isDark ? 'dark' : 'light');
    }

    // v5.9.28: Update particle colors/opacity when theme toggles from nav bar
    if (window.TWR?.LandingPage?.updateParticleTheme) {
        TWR.LandingPage.updateParticleTheme(isDark);
    }

    updateThemeIcons(isDark);
}

function updateThemeIcons(isDark) {
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
    if (lightIcon && darkIcon) {
        lightIcon.style.display = isDark ? 'block' : 'none';
        darkIcon.style.display = isDark ? 'none' : 'block';
    }
}

async function initCSRF() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
        State.csrfToken = meta.getAttribute('content');
        // Export to window for IIFE modules (Dictionary, etc.)
        window.CSRF_TOKEN = State.csrfToken;
    }
    await fetchCSRFToken();
}

async function fetchCSRFToken() {
    try {
        const r = await fetch('/api/csrf-token');
        const data = await r.json();
        if (data.csrf_token) {
            State.csrfToken = data.csrf_token;
            // Export to window for IIFE modules (Dictionary, etc.)
            window.CSRF_TOKEN = data.csrf_token;
        }
    } catch (e) {
        console.warn('[TWR] Failed to fetch CSRF token:', e);
    }
}

async function checkCapabilities() {
    try {
        const r = await fetch('/api/capabilities');
        const data = await r.json();
        if (data.success && data.data) {
            // Handle nested structure: { version, capabilities: {...} }
            // Flatten capabilities into State.capabilities for easier access
            State.capabilities = data.data.capabilities || data.data;
            // Also store version if available
            if (data.data.version) {
                State.serverVersion = data.data.version;
            }
            updateCapabilityUI();
        }
    } catch (e) {
        console.warn('[TWR] Failed to check capabilities:', e);
    }
}

async function loadVersionLabel() {
    // v4.9.9: Use /api/version as primary (reads fresh from root version.json via get_version())
    // Falls back to /static/version.json if API unavailable
    let version = null;
    try {
        const r = await fetch('/api/version');
        if (r.ok) {
            const data = await r.json();
            version = data.app_version;
        }
    } catch (e) {
        // Fallback to static file
    }
    if (!version) {
        try {
            const r = await fetch('/static/version.json', {cache: 'no-store'});
            const data = await r.json();
            version = data.version;
        } catch (e) {
            console.warn('[AEGIS] Failed to load version:', e);
        }
    }
    if (version) {
        const els = {
            'version-label': `Enterprise v${version}`,
            'footer-version': `v${version}`,
            'help-version': `v${version}`
        };
        for (const [id, text] of Object.entries(els)) {
            const el = document.getElementById(id);
            if (el) el.textContent = text;
        }
    }
}

function updateCapabilityUI() {
    // Update export buttons based on capabilities
    const excelBtn = document.getElementById('btn-export-excel');
    const pdfBtn = document.getElementById('btn-export-pdf');
    
    if (excelBtn && !State.capabilities.excel_export) {
        excelBtn.disabled = true;
        excelBtn.title = 'Excel export not available (install openpyxl)';
    }
    if (pdfBtn && !State.capabilities.pdf_export) {
        pdfBtn.disabled = true;
        pdfBtn.title = 'PDF export not available (install reportlab)';
    }
}

function initUI() {
    show('empty-state');
    hide('loading-overlay');
    hide('analytics-accordion');  // v3.0.13
    hide('unified-filter-bar');   // v3.0.13
    hide('issues-container');
    hide('stats-bar');
    updateStats();
}

// ============================================================
// EVENT HANDLING - Delegated to TWR.Events module (v3.0.17)
// ============================================================

/**
 * Initialize all event listeners
 * Delegates to TWR.Events module if loaded, otherwise uses inline fallback
 */
function initEventListeners() {
    if (window.TWR?.Events?.initEventListeners) {
        TWR.Events.initEventListeners();
    } else {
        console.warn('[TWR] Events module not loaded - using inline fallback');
        // Inline fallback would go here, but module should always be loaded
        // For air-gapped deployment, ensure events.js is included in install
    }
}

/**
 * Initialize drag-and-drop handling
 */
function initDragDrop() {
    if (window.TWR?.Events?.initDragDrop) {
        TWR.Events.initDragDrop();
    } else {
        console.warn('[TWR] Events module not loaded for drag-drop');
    }
}

/**
 * Initialize global keyboard shortcuts
 */
function initKeyboardShortcuts() {
    if (window.TWR?.Events?.initKeyboardShortcuts) {
        TWR.Events.initKeyboardShortcuts();
    } else {
        console.warn('[TWR] Events module not loaded for keyboard shortcuts');
    }
}

// Category list filtering - delegate to module
function filterCategoryList() {
    if (window.TWR?.Events?.filterCategoryList) {
        TWR.Events.filterCategoryList();
    } else {
        // Inline fallback
        const search = (document.getElementById('category-search')?.value || '').toLowerCase().trim();
        const items = document.querySelectorAll('#category-list .checkbox-label');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = !search || text.includes(search) ? '' : 'none';
        });
    }
}

// Table density - delegate to module
function setTableDensity(density) {
    if (window.TWR?.Events?.setTableDensity) {
        TWR.Events.setTableDensity(density);
    } else {
        // Inline fallback
        const tableBody = document.getElementById('issues-list');
        if (!tableBody) return;
        tableBody.classList.remove('density-compact', 'density-comfortable');
        tableBody.classList.add(`density-${density}`);
        try { localStorage.setItem('twr_density', density); } catch (e) { /* ignore */ }
    }
}

// Keyboard navigation state - module handles this, but keep reference for compatibility
let keyboardSelectedIndex = -1;

function initIssueKeyboardNav() {
    if (window.TWR?.Events?.initIssueKeyboardNav) {
        TWR.Events.initIssueKeyboardNav();
    }
}

function updateKeyboardSelection(rows) {
    if (window.TWR?.Events?.updateKeyboardSelection) {
        TWR.Events.updateKeyboardSelection(rows);
    } else {
        // Inline fallback
        rows.forEach((row, i) => {
            row.classList.toggle('keyboard-selected', i === keyboardSelectedIndex);
            if (i === keyboardSelectedIndex) {
                row.scrollIntoView({ block: 'nearest' });
            }
        });
    }
}

// Modal focus trap - already in TWR.Modals, this is a legacy alias
function initModalFocusTrap() {
    if (window.TWR?.Modals?.initModalFocusTrap) {
        TWR.Modals.initModalFocusTrap();
    }
}

// ============================================================
// FILE HANDLING
// ============================================================
function isValidFileType(filename) {
    const ext = filename.toLowerCase();
    return ext.endsWith('.docx') || ext.endsWith('.pdf') || ext.endsWith('.doc');
}

function getFileType(filename) {
    if (filename.toLowerCase().endsWith('.pdf')) return 'pdf';
    if (filename.toLowerCase().endsWith('.docx')) return 'docx';
    if (filename.toLowerCase().endsWith('.doc')) return 'doc';
    return null;
}

async function handleFileUpload(file) {
    // Note: Guard moved to events.js to prevent race condition
    // The _TWR_fileProcessing flag is set by the caller (events.js)
    // so we don't check it here to avoid blocking legitimate calls

    if (!isValidFileType(file.name)) {
        toast('error', 'Invalid file type. Please upload a .docx, .doc, or .pdf file.');
        return;
    }

    // Only set the flag if not already set (for direct calls)
    if (!window._TWR_fileProcessing) {
        window._TWR_fileProcessing = true;
    }
    console.log('[TWR] Starting file upload:', file.name);
    
    // v2.9.1 FIX C5: Reset state before processing new document
    // This prevents app freeze when scanning 2nd document
    resetStateForNewDocument();
    
    setLoading(true, 'Uploading document...', 10);
    setLoadingStep('upload', 'active'); // B9

    const formData = new FormData();
    formData.append('file', file);

    try {
        const result = await api('/upload', 'POST', formData);

        if (result.success) {
            setLoadingStep('upload', 'complete'); // B9
            State.filename = result.data.filename;
            State.fileType = result.data.file_type;
            State.filepath = result.data.filepath;

            updateDocumentInfo(result.data);

            hide('empty-state');
            show('stats-bar');

            document.getElementById('btn-review').disabled = false;

            setLoading(false);
            toast('success', `Loaded: ${result.data.filename}`);

            // Auto-review if enabled
            if (State.settings.autoReview) {
                runReview();
            }
        } else {
            setLoading(false);
            toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Upload failed');
        }
    } catch (uploadErr) {
        // v4.9.9: Ensure loading overlay is always cleared on error
        console.error('[TWR] Upload error:', uploadErr);
        setLoading(false);
        toast('error', 'Upload failed: ' + (uploadErr.message || 'Unknown error'));
    } finally {
        // Reset file input and processing flag after a delay
        setTimeout(() => {
            window._TWR_fileProcessing = false;
            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.value = '';
        }, 500);
    }
}

function updateDocumentInfo(data) {
    const titleEl = document.getElementById('doc-title');
    const subtitleEl = document.getElementById('doc-subtitle');
    const statusIndicator = document.getElementById('doc-status-indicator');
    const statusText = document.getElementById('doc-status-text');

    if (titleEl) titleEl.textContent = data.filename || 'Document';
    if (subtitleEl) {
        const fileType = data.file_type?.toUpperCase() || 'Document';
        subtitleEl.textContent = `${fileType} • ${(data.word_count || 0).toLocaleString()} words`;
    }

    // Update document status indicator
    if (statusIndicator && statusText) {
        statusIndicator.classList.remove('loaded', 'reviewed');
        statusText.classList.remove('loaded', 'reviewed');
        statusIndicator.classList.add('loaded');
        statusText.classList.add('loaded');
        statusIndicator.innerHTML = '<i data-lucide="file-check"></i>';
        statusText.textContent = 'Document loaded';

        // Re-initialize lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // Update stats
    setStatValue('stat-words', data.word_count);
    setStatValue('stat-paragraphs', data.paragraph_count);
    setStatValue('stat-tables', data.table_count || 0);
    setStatValue('stat-headings', data.heading_count || '-');
}

// ============================================================
// REVIEW
// ============================================================
async function runReview() {
    if (!State.filename) {
        toast('error', 'Please upload a document first');
        return;
    }

    // v3.0.39: Check if job manager is available, use job-based review if so
    const jobStatus = await api('/job/status', 'GET');
    if (jobStatus.available) {
        return runReviewWithJobs();
    }
    
    // Fallback to synchronous review
    return runReviewSync();
}

/**
 * Run review using job-based async polling (v3.0.39 Batch I)
 * 
 * Shows real progress from backend phases:
 * - extracting: Document text extraction
 * - parsing: Structure parsing
 * - checking: Running quality checkers
 * - postprocessing: Finalizing results
 * - complete: Done
 */
async function runReviewWithJobs() {
    // v3.0.39: Job-based review with real progress polling
    LoadingTracker.start('review', 5);
    LoadingTracker.updateProgress(0, 5);
    
    setLoading(true, 'Starting document analysis...', 5);
    setLoadingStep('upload', 'complete'); // Already uploaded
    setLoadingStep('extract', 'active');
    const startTime = performance.now();

    // v4.5.0: Create enhanced scan progress dashboard overlay
    if (typeof TWR !== 'undefined' && TWR.ScanProgress) {
        TWR.ScanProgress.create(State.currentFile?.name || 'document');
    }

    // Show cancel button and wire it to job cancellation
    const cancelBtn = document.getElementById('loading-cancel');
    if (cancelBtn) {
        cancelBtn.style.display = 'inline-flex';
        cancelBtn.onclick = null; // Clear any existing handler
    }

    // Gather enabled checkers
    const options = {};
    document.querySelectorAll('[data-checker]').forEach(cb => {
        if (cb.checked !== undefined) {
            options[`check_${cb.dataset.checker}`] = cb.checked;
        }
    });

    // Start the async job
    const startResult = await api('/review/start', 'POST', { options });
    
    if (!startResult.success) {
        LoadingTracker.reset();
        setLoading(false);
        toast('error', startResult.error || 'Failed to start review');
        return;
    }
    
    const jobId = startResult.job_id;
    console.log(`[TWR] Review job started: ${jobId}`);
    
    // Wire cancel buttons to job cancellation (both overlay and persistent indicator)
    const cancelHandler = async () => {
        console.log(`[TWR] Cancelling job ${jobId}...`);
        const cancelResult = await api(`/job/${jobId}/cancel`, 'POST');
        if (cancelResult.success) {
            toast('info', 'Review cancelled');
        } else {
            toast('error', cancelResult.error || 'Failed to cancel');
        }
        // v4.6.1: Always clean up UI state on cancel attempt
        if (TWR.ScanProgress?.isActive()) TWR.ScanProgress.destroy();
        LoadingTracker.reset();
        setLoading(false);
        State.currentJobId = null;
        // v4.6.1: Remove global cancel hook
        window.cancelCurrentJob = null;
    };

    if (cancelBtn) {
        cancelBtn.onclick = cancelHandler;
    }

    // v3.0.43: Also wire up persistent run-state cancel button
    const runStateCancel = document.getElementById('run-state-cancel');
    if (runStateCancel) {
        runStateCancel.onclick = cancelHandler;
    }

    // v4.6.1: Expose global cancel function for ScanProgress dashboard cancel button
    window.cancelCurrentJob = cancelHandler;

    // Store job ID for potential external cancellation
    State.currentJobId = jobId;
    
    // Poll for job progress
    let pollCount = 0;
    const maxPolls = 600; // 5 minutes at 500ms intervals
    
    while (pollCount < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, 500)); // 500ms polling interval
        pollCount++;
        
        const jobResult = await api(`/job/${jobId}`, 'GET');
        
        if (!jobResult.success) {
            console.error(`[TWR] Job poll error:`, jobResult.error);
            continue; // Keep trying
        }
        
        const job = jobResult.job;
        const progress = job.progress;
        
        // Map phase to loading steps and update UI
        const phaseToStep = {
            'queued': 'extract',
            'uploading': 'extract',
            'extracting': 'extract',
            'parsing': 'extract',
            'checking': 'analyze',
            'postprocessing': 'roles',
            'exporting': 'render',
            'complete': 'render'
        };
        
        const currentStep = phaseToStep[progress.phase] || 'analyze';
        setLoadingStep(currentStep, 'active');
        
        // Build progress message
        let message = progress.last_log || `Processing (${progress.phase})...`;
        if (progress.current_checker) {
            message = `Checking: ${progress.current_checker} (${progress.checkers_completed}/${progress.checkers_total})`;
        }
        
        // Update progress bar
        updateProgress(progress.overall_progress, message);
        
        // Update ETA display if available
        if (job.eta) {
            const etaContainer = document.getElementById('loading-eta-container');
            const etaValue = document.getElementById('loading-eta');
            if (etaContainer && etaValue) {
                etaContainer.style.display = 'block';
                etaValue.textContent = job.eta;
            }
        }
        
        // v4.5.0: Feed scan progress dashboard
        // v4.6.1: Pass last_log (raw checker info) to dashboard for checker breakdown display
        if (typeof TWR !== 'undefined' && TWR.ScanProgress?.isActive()) {
            const dashMsg = progress.last_log || message;
            TWR.ScanProgress.onProgress(progress.phase, progress.phase_progress || progress.overall_progress, dashMsg);
        }

        console.log(`[TWR] Job ${jobId}: ${progress.phase} @ ${progress.overall_progress.toFixed(1)}% - ${message}`);

        // Check for completion states
        if (job.status === 'complete') {
            console.log(`[TWR] Job ${jobId} complete`);
            if (TWR.ScanProgress?.isActive()) TWR.ScanProgress.complete();
            window.cancelCurrentJob = null; // v4.6.1: Clean up global cancel hook
            break;
        } else if (job.status === 'failed') {
            console.error(`[TWR] Job ${jobId} failed:`, job.error);
            if (TWR.ScanProgress?.isActive()) TWR.ScanProgress.destroy();
            LoadingTracker.reset();
            setLoading(false);
            toast('error', job.error || 'Review failed');
            State.currentJobId = null;
            window.cancelCurrentJob = null; // v4.6.1
            resetUploadState(); // v5.9.2: Allow new file selection after failure
            return;
        } else if (job.status === 'cancelled') {
            console.log(`[TWR] Job ${jobId} cancelled`);
            if (TWR.ScanProgress?.isActive()) TWR.ScanProgress.destroy();
            LoadingTracker.reset();
            setLoading(false);
            State.currentJobId = null;
            window.cancelCurrentJob = null; // v4.6.1
            resetUploadState(); // v5.9.2: Allow new file selection after cancel
            return;
        }
    }
    
    // Get final results (v4.6.1: retry on 429 rate limit)
    let resultResponse = null;
    for (let retryAttempt = 0; retryAttempt < 10; retryAttempt++) {
        resultResponse = await api(`/review/result/${jobId}`, 'GET');
        if (resultResponse.success) break;
        // If rate-limited, wait and retry
        if (resultResponse.error && resultResponse.error.includes('Too many requests')) {
            console.log(`[TWR] Result fetch rate-limited, retry ${retryAttempt + 1}/10...`);
            await new Promise(r => setTimeout(r, 1000 + retryAttempt * 500));
            continue;
        }
        // Other error — don't retry
        break;
    }

    if (!resultResponse || !resultResponse.success) {
        LoadingTracker.reset();
        setLoading(false);
        toast('error', resultResponse?.error || 'Failed to get results');
        State.currentJobId = null;
        window.cancelCurrentJob = null; // v4.6.1
        resetUploadState(); // v5.9.2: Allow new file selection after error
        return;
    }

    // Process results (same as sync version)
    const result = { success: true, data: resultResponse.data };
    const duration = performance.now() - startTime;

    processReviewResults(result, duration);
    State.currentJobId = null;
    window.cancelCurrentJob = null; // v4.6.1
}

/**
 * Process review results and update UI.
 * Shared by both sync and async review functions.
 */
function processReviewResults(result, duration) {
    if (!result.success) {
        LoadingTracker.reset();
        setLoading(false);
        toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Review failed');
        return;
    }
    
    LoadingTracker.updateProgress(4, 5);
    setLoadingStep('render', 'active');
    updateProgress(90, 'Rendering results...');
    
    State.reviewResults = result.data;
    State.issues = result.data.issues || [];
    State.filteredIssues = [...State.issues];
    
    // v3.0.109: Generate documentId after fresh review for triage/baseline features
    // This was only being set when restoring from history, causing "Document must be 
    // saved to history" errors when using Keep/Suppress/Fixed in triage mode
    if (!State.documentId) {
        State.documentId = generateGlobalDocumentId();
        console.log(`[TWR] Generated document ID: ${State.documentId}`);
    }
    
    // v3.0.97b: Populate State.fixes for Fix Assistant v2
    // Filter to only issues that have actionable suggestions
    State.fixes = (State.issues || []).filter(issue => 
        issue.suggestion && 
        issue.suggestion !== '-' && 
        issue.suggestion.trim() !== '' &&
        issue.flagged_text
    );
    console.log(`[TWR] Fix Assistant: ${State.fixes.length} fixable issues identified`);
    
    // v2.9.4: Store full text for Statement Forge (#2, #4)
    State.currentText = result.data.full_text || '';
    State.currentFilename = State.filename || 'Unknown Document';
    
    // Handle roles - could be in result.data.roles or result.data.roles.roles
    if (result.data.roles) {
        State.roles = result.data.roles.roles || result.data.roles;
        // v3.0.12: Populate separated entities for proper export
        if (result.data.roles.entities) {
            State.entities = {
                roles: result.data.roles.entities.roles || [],
                deliverables: result.data.roles.entities.deliverables || [],
                unknown: result.data.roles.entities.unknown || []  // v3.0.12b
            };
        } else {
            // Fallback: filter from main roles object by entity_kind
            // v3.0.12b: Only include explicit 'role' kind, not unknown
            const allRoles = Object.values(State.roles);
            State.entities = {
                roles: allRoles.filter(r => r.entity_kind === 'role'),
                deliverables: allRoles.filter(r => r.entity_kind === 'deliverable'),
                unknown: allRoles.filter(r => !r.entity_kind || r.entity_kind === 'unknown')
            };
        }
        
        // v3.0.12b: Log entity audit for debugging
        console.log(`[TWR] Entity audit: ${State.entities.roles.length} roles, ${State.entities.deliverables.length} deliverables, ${State.entities.unknown.length} unknown`);
    } else {
        State.roles = {};
        State.entities = { roles: [], deliverables: [], unknown: [] };
    }
    
    State.selectedIssues.clear();

    // Update UI
    // v4.5.3: Ensure document title is shown in header after review
    if (State.filename) {
        updateDocumentInfo({
            filename: State.filename,
            file_type: State.fileType || '',
            word_count: result.data.word_count || 0,
            paragraph_count: result.data.paragraph_count || 0,
            table_count: result.data.table_count || 0,
            heading_count: result.data.heading_count || 0
        });
    }
    updateResultsUI(result.data);
    updateSeverityCounts(result.data.by_severity || {});
    updateValidationCounts(); // v3.0.29: Update validation filter counts
    updateCategoryFilters(result.data.by_category || {});
    renderIssuesList();
    
    // v3.0.13: Show analytics accordion and unified filter bar
    showAnalyticsAccordion(result.data);
    showUnifiedFilterBar(result.data);
    show('issues-container');

    // v4.0.2: Always show stats bar after processing results (includes score/grade)
    show('stats-bar');
    hide('empty-state');
    
    // Show inline families panel (Pareto view)
    showInlineFamiliesPanel();
    
    // Show roles if available
    if (Object.keys(State.roles).length > 0) {
        document.getElementById('roles-chart-card')?.style.setProperty('display', 'block');
        document.getElementById('btn-roles-report').disabled = false;
        renderRolesSummary();
    }

    document.getElementById('btn-export').disabled = false;

    LoadingTracker.updateProgress(5, 5);
    LoadingTracker.reset();
    setLoading(false);
    toast('success', `Analysis complete: ${State.issues.length} issues found in ${(duration/1000).toFixed(1)}s`);

    // v4.3.0: Initialize smart search autocomplete now that we have issues
    if (window.TWR?.Events?.initSmartSearchForIssues) {
        TWR.Events.initSmartSearchForIssues();
    }

    // v2.9.4: Auto-run Statement Forge extraction in background (#4)
    // v5.9.2: Added feedback toast so user knows extraction happened
    if (State.currentText && window.StatementForge) {
        setTimeout(async () => {
            try {
                console.log('[TWR] Auto-extracting statements in background...');
                await window.StatementForge.extractStatements(true); // silent mode
                // v5.9.2: Show feedback after auto-extraction
                const stmtCount = window.StatementForge?.getStatements?.()?.length;
                if (stmtCount !== undefined && stmtCount > 0) {
                    toast('info', `Statement Forge: ${stmtCount} statements auto-extracted`);
                } else if (stmtCount === 0) {
                    toast('info', 'Statement Forge: No statements found in document');
                }
            } catch (sfErr) {
                console.warn('[TWR] Statement Forge auto-extract failed:', sfErr);
                toast('warning', 'Statement extraction skipped: ' + (sfErr.message || 'module error'));
            }
        }, 500);
    }

    // Save to history if database available
    if (State.capabilities.database) {
        saveToHistory(duration);
    }

    // v3.0.111: Prompt for document comparison if this is a re-scan
    // Use scan_info from backend which has the correct document_id from scan_history.db
    const scanInfo = result.data.scan_info;
    // v4.2.0: Store scan info for Statement History sidebar button
    if (scanInfo) {
        window._sfCurrentDocumentId = scanInfo.document_id;
        window._sfCurrentScanId = scanInfo.scan_id;
    }
    if (scanInfo && scanInfo.is_rescan && scanInfo.scan_count >= 2 && window.showComparePromptAfterScan) {
        setTimeout(() => {
            window.showComparePromptAfterScan(scanInfo.document_id, State.filename, scanInfo.scan_count);
        }, 1500);
    }

    // v4.4.0: Prompt for document tagging after new scan (if not a re-scan)
    // This helps users organize documents with function codes and categories
    if (scanInfo && !scanInfo.is_rescan && window.TWR?.FunctionTags?.showDocumentTagPrompt) {
        setTimeout(() => {
            window.TWR.FunctionTags.showDocumentTagPrompt(scanInfo, State.filename);
        }, 2000); // Slight delay to let user see results first
    }

    // v5.0.2: Refresh landing page metrics so they show updated counts
    if (typeof TWR !== 'undefined' && TWR.LandingPage?.refresh) {
        TWR.LandingPage.refresh().catch(e => console.warn('[TWR] Landing refresh:', e));
    }

    // Save state to sessionStorage for back button support
    saveSessionState();

    // v5.9.2: Reset upload state so user can immediately select a new file
    resetUploadState();
}

/**
 * Synchronous review (fallback when job manager is unavailable)
 * v3.0.39: Refactored from original runReview
 */
async function runReviewSync() {
    // v2.9.9: Initialize LoadingTracker for ETA (#20)
    // Estimate ~5 steps: upload, extract, analyze, roles, render
    LoadingTracker.start('review', 5);
    LoadingTracker.updateProgress(0, 5);
    
    setLoading(true, 'Analyzing document...', 10);
    setLoadingStep('extract', 'active'); // B9
    const startTime = performance.now();

    // Show cancel button for long operations
    const cancelBtn = document.getElementById('loading-cancel');
    if (cancelBtn) cancelBtn.style.display = 'inline-flex';

    // Gather enabled checkers
    const options = {};
    document.querySelectorAll('[data-checker]').forEach(cb => {
        if (cb.checked !== undefined) {
            options[`check_${cb.dataset.checker}`] = cb.checked;
        }
    });

    LoadingTracker.updateProgress(1, 5);
    setLoadingStep('analyze', 'active'); // B9
    updateProgress(30, 'Running quality checks...');

    const result = await api('/review', 'POST', { options });

    if (result.success) {
        const duration = performance.now() - startTime;
        
        LoadingTracker.updateProgress(3, 5);
        setLoadingStep('roles', 'active'); // B9
        updateProgress(60, 'Processing roles...');
        
        processReviewResults(result, duration);
    } else {
        LoadingTracker.reset();
        setLoading(false);
        toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Review failed');
    }
}

function updateResultsUI(data) {
    // Update document status indicator to "reviewed"
    const statusIndicator = document.getElementById('doc-status-indicator');
    const statusText = document.getElementById('doc-status-text');
    if (statusIndicator && statusText) {
        statusIndicator.classList.remove('loaded');
        statusText.classList.remove('loaded');
        statusIndicator.classList.add('reviewed');
        statusText.classList.add('reviewed');
        statusIndicator.innerHTML = '<i data-lucide="check-circle"></i>';
        const issueCount = data.issue_count || 0;
        statusText.textContent = `Reviewed • ${issueCount} issue${issueCount !== 1 ? 's' : ''}`;

        // Re-initialize lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // Score
    const score = data.score ?? 100;
    const grade = data.grade || 'A';

    setStatValue('stat-issues', data.issue_count || 0);
    setStatValue('stat-score', score);
    setStatValue('stat-grade', grade);

    // Score ring animation
    const scoreRing = document.getElementById('score-ring-fill');
    if (scoreRing) {
        scoreRing.style.strokeDasharray = `${score}, 100`;
        scoreRing.style.stroke = getScoreColor(score);
    }

    // Grade styling
    const gradeEl = document.getElementById('stat-grade');
    if (gradeEl) {
        gradeEl.className = `stat-value grade grade-${grade.toLowerCase()}`;
    }

    // Readability - v4.0.2: Update mini gauge arcs
    const readability = data.readability || {};
    const flesch = readability.flesch_reading_ease;
    const fkGrade = readability.flesch_kincaid_grade;
    const fog = readability.gunning_fog_index;

    setStatValue('stat-flesch', flesch?.toFixed(1) ?? '--');
    setStatValue('stat-fk-grade', fkGrade?.toFixed(1) ?? '--');
    setStatValue('stat-fog', fog?.toFixed(1) ?? '--');

    // Animate gauge arcs (arc length is ~100 for full semicircle)
    const arcLength = 100;
    const fleschArc = document.getElementById('stat-flesch-arc');
    const fkArc = document.getElementById('stat-fk-arc');
    const fogArc = document.getElementById('stat-fog-arc');

    if (fleschArc && flesch != null) {
        // Flesch: 0-100 scale, higher is better
        const fleschPct = Math.min(100, Math.max(0, flesch)) / 100;
        fleschArc.setAttribute('stroke-dasharray', `${fleschPct * arcLength} ${arcLength}`);
    }
    if (fkArc && fkGrade != null) {
        // Grade Level: typically 1-20, normalize to percentage (20 = full)
        const gradePct = Math.min(20, Math.max(0, fkGrade)) / 20;
        fkArc.setAttribute('stroke-dasharray', `${gradePct * arcLength} ${arcLength}`);
    }
    if (fogArc && fog != null) {
        // Fog Index: typically 6-20+, normalize to percentage (20 = full)
        const fogPct = Math.min(20, Math.max(0, fog)) / 20;
        fogArc.setAttribute('stroke-dasharray', `${fogPct * arcLength} ${arcLength}`);
    }
    
    // PDF Quality Warning (v2.9.0 BATCH E1)
    displayPDFQualityWarning(data.pdf_quality);

    // v2.9.9: Removed renderHealthGauge call - gauge tile removed in v2.9.4.2, score shown in stats bar only (#14)
    // v4.0.2: Replaced Issues by Section carousel with inline Fix Impact Analyzer
    renderFixImpactAnalyzerInline(data);
    
    // v2.9.2 E2-E5: Render enhanced statistics panel
    if (data.enhanced_stats) {
        renderEnhancedStats(data.enhanced_stats);
    }
    
    // v3.0.33: Render acronym transparency metrics
    if (data.acronym_metrics) {
        renderAcronymMetrics(data.acronym_metrics);
    }
    
    // v3.0.33 Chunk C: Update Statement Forge ready badge
    if (data.statement_forge_summary) {
        updateStatementForgeBadge(data.statement_forge_summary);
    }
    
    // v3.0.33 Chunk E: Render issue heatmap (category × severity)
    if (data.issues && data.issues.length > 0) {
        renderIssueHeatmap(data.issues);
    }
    
    // v3.0.95: Render hyperlink status panel
    if (data.hyperlink_results) {
        renderHyperlinkStatus(data.hyperlink_results);
    }
    
    // v3.0.33 Chunk E: Fetch and render score trend sparkline
    if (data.document_info && data.document_info.filename) {
        fetchAndRenderScoreTrend(data.document_info.filename);
    }
    
    // Only show recommendations if not previously dismissed this session
    if (!sessionStorage.getItem('twr_recommendations_dismissed')) {
        renderSmartRecommendations(data);
    }
}

/**
 * Display PDF quality warning banner if quality issues detected.
 * Part of BATCH E1: Smart PDF Handling (v2.9.0)
 * 
 * @param {Object|null} pdfQuality - Quality report from pdf_extractor_v2
 */
function displayPDFQualityWarning(pdfQuality) {
    // Remove any existing warning
    const existingWarning = document.getElementById('pdf-quality-warning');
    if (existingWarning) {
        existingWarning.remove();
    }
    
    // No warning needed if not a PDF or quality is good
    if (!pdfQuality || pdfQuality.severity === 'good') {
        return;
    }
    
    // Build warning message based on quality
    let icon = 'alert-triangle';
    let title = 'PDF Quality Notice';
    let message = '';
    let cssClass = 'pdf-warning-info';
    
    if (pdfQuality.quality === 'scanned') {
        icon = 'alert-circle';
        title = 'Scanned PDF Detected';
        message = 'This PDF appears to be a scanned document with no text layer. ' +
                  'Text analysis may be limited or unavailable. Consider running OCR.';
        cssClass = 'pdf-warning-error';
    } else if (pdfQuality.quality === 'ocr_text') {
        icon = 'alert-triangle';
        title = 'OCR-Processed PDF';
        message = 'This PDF contains OCR-processed text. Some text may have ' +
                  'recognition errors that affect analysis accuracy.';
        cssClass = 'pdf-warning-warning';
    } else if (pdfQuality.quality === 'mixed') {
        icon = 'info';
        title = 'Mixed Content PDF';
        message = 'This PDF contains both text and image-based content. ' +
                  'Some sections may not be fully analyzed.';
        cssClass = 'pdf-warning-info';
    }
    
    // Add recommendations if available
    if (pdfQuality.recommendations && pdfQuality.recommendations.length > 0) {
        message += ' Recommendation: ' + pdfQuality.recommendations[0];
    }
    
    // Create warning banner
    const warningBanner = document.createElement('div');
    warningBanner.id = 'pdf-quality-warning';
    warningBanner.className = `pdf-quality-warning ${cssClass}`;
    // SAFE: title is hardcoded; message and pdfQuality values escaped
    warningBanner.innerHTML = `
        <i data-lucide="${icon}" class="warning-icon"></i>
        <div class="warning-content">
            <strong>${escapeHtml(title)}</strong>
            <span>${escapeHtml(message)}</span>
            <small>Quality confidence: ${pdfQuality.confidence || 0}% | ~${pdfQuality.chars_per_page || 0} chars/page</small>
        </div>
        <button class="warning-dismiss" onclick="this.parentElement.remove()" aria-label="Dismiss">
            <i data-lucide="x"></i>
        </button>
    `;
    
    // Insert at top of dashboard
    const dashboard = document.getElementById('dashboard-container');
    if (dashboard) {
        dashboard.insertBefore(warningBanner, dashboard.firstChild);
        // Refresh icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }
}

// ============================================================
// BATCH E2: ANALYTICS DASHBOARD UPGRADE (v2.9.0)
// ============================================================

// v2.9.9: Removed renderHealthGauge() - gauge tile removed in v2.9.4.2 (#14)
// Score is now displayed only in stats bar (score-ring element)

/**
 * Render Section Heatmap showing issue density by document section.
 * Delegates to TWR.Renderers module if available.
 * 
 * @param {Array} issues - List of issues with paragraph_index
 * @param {number} totalParagraphs - Total number of paragraphs in document
 */
function renderSectionHeatmap(issues, totalParagraphs) {
    if (window.TWR?.Renderers?.renderSectionHeatmap) {
        return TWR.Renderers.renderSectionHeatmap(issues, totalParagraphs);
    }
    // Fallback: basic hide if module not loaded
    const wrapper = document.getElementById('section-heatmap-container');
    if (wrapper) wrapper.style.display = 'none';
}

/**
 * Filter issues to show only those in a specific paragraph range.
 * Delegates to TWR.Renderers module if available.
 */
function filterIssuesByParagraphRange(start, end) {
    if (window.TWR?.Renderers?.filterIssuesByParagraphRange) {
        return TWR.Renderers.filterIssuesByParagraphRange(start, end);
    }
    // Fallback if module not loaded
    State.filteredIssues = State.issues.filter(issue => {
        const paraIdx = (issue.paragraph_index || 0) + 1;
        return paraIdx >= start && paraIdx <= end;
    });
    renderIssuesList();
}

/**
 * Generate and display smart recommendations based on analysis results.
 * Delegates to TWR.Renderers module if available.
 * 
 * @param {Object} data - Full review results object
 */
function renderSmartRecommendations(data) {
    if (window.TWR?.Renderers?.renderSmartRecommendations) {
        return TWR.Renderers.renderSmartRecommendations(data);
    }
    // Fallback: hide if module not loaded
    const wrapper = document.getElementById('smart-recommendations');
    if (wrapper) wrapper.style.display = 'none';
}

/**
 * Generate prioritized recommendations based on analysis patterns.
 * Delegates to TWR.Renderers module if available.
 * @param {Object} data - Review data
 * @returns {Array} Array of recommendation objects
 */
function generateRecommendations(data) {
    if (window.TWR?.Renderers?.generateRecommendations) {
        return TWR.Renderers.generateRecommendations(data);
    }
    return []; // Fallback: no recommendations
}

/**
 * Initialize dashboard event handlers.
 * Called once on page load.
 */
function initDashboardHandlers() {
    // Dismiss recommendations handler is set up in renderSmartRecommendations
    
    // Heatmap cell hover effects handled by CSS
}

// ============================================================
// v2.9.2 E2-E5: ENHANCED DASHBOARD STATISTICS (Delegated)
// ============================================================

/**
 * Render enhanced statistics panel.
 * Delegates to TWR.Renderers module if available.
 */
function renderEnhancedStats(enhancedStats) {
    if (window.TWR?.Renderers?.renderEnhancedStats) {
        return TWR.Renderers.renderEnhancedStats(enhancedStats);
    }
    // No fallback - panel just won't appear
}

/**
 * Render acronym transparency metrics panel.
 * v3.0.33: Added for strict mode visibility.
 * 
 * @param {Object} metrics - Acronym metrics from checker
 */
function renderAcronymMetrics(metrics) {
    if (!metrics) return;
    
    const card = document.getElementById('acronym-metrics-card');
    if (!card) return;
    
    // Show the card
    card.style.display = 'block';
    
    // Update mode badge
    const modeBadge = document.getElementById('acronym-mode-badge');
    const modeLabel = document.getElementById('acronym-mode-label');
    if (modeBadge && modeLabel) {
        if (metrics.strict_mode) {
            modeBadge.className = 'acronym-mode-badge strict-mode';
            modeLabel.textContent = 'Strict Mode';
            modeBadge.title = 'All acronyms must be defined in document. Click to learn more.';
        } else {
            modeBadge.className = 'acronym-mode-badge permissive-mode';
            modeLabel.textContent = 'Permissive';
            modeBadge.title = 'Common well-known acronyms are suppressed. Click to learn more.';
        }
    }
    
    // Update metric values
    setStatValue('acronym-total-count', metrics.total_acronyms_found || 0);
    setStatValue('acronym-defined-count', metrics.defined_count || 0);
    setStatValue('acronym-suppressed-count', metrics.suppressed_by_allowlist_count || 0);
    setStatValue('acronym-flagged-count', metrics.flagged_count || 0);
    
    // Show suppressed list if any
    const suppressedList = document.getElementById('acronym-suppressed-list');
    const suppressedItems = document.getElementById('acronym-suppressed-items');
    if (suppressedList && suppressedItems) {
        if (metrics.allowlist_matches && metrics.allowlist_matches.length > 0) {
            suppressedList.style.display = 'block';
            // Limit to first 10 to avoid clutter
            const displayItems = metrics.allowlist_matches.slice(0, 10);
            let text = displayItems.join(', ');
            if (metrics.allowlist_matches.length > 10) {
                text += ` (+${metrics.allowlist_matches.length - 10} more)`;
            }
            suppressedItems.textContent = text;
        } else {
            suppressedList.style.display = 'none';
        }
    }
    
    // Refresh icons if needed
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}

/**
 * Update Statement Forge ready badge based on review summary.
 * v3.0.33 Chunk C: Shows badge when statements are pre-extracted.
 * 
 * @param {Object} sfSummary - Statement Forge summary from review response
 */
function updateStatementForgeBadge(sfSummary) {
    const badge = document.getElementById('sf-ready-badge');
    const btn = document.getElementById('btn-statement-forge');
    
    if (!badge) return;
    
    if (sfSummary.statements_ready && sfSummary.total_statements > 0) {
        // Show badge with count
        badge.style.display = 'flex';
        badge.textContent = sfSummary.total_statements > 99 ? '99+' : sfSummary.total_statements;
        badge.title = `${sfSummary.total_statements} statements extracted and ready`;
        
        // Update button title
        if (btn) {
            btn.title = `Statement Forge (${sfSummary.total_statements} statements ready)`;
        }
        
        // Store summary for later use
        window.TWR = window.TWR || {};
        window.TWR.statementForgeSummary = sfSummary;
        
        console.log(`[SF] ${sfSummary.total_statements} statements pre-extracted and ready`);
    } else {
        // Hide badge
        badge.style.display = 'none';
        if (btn) {
            btn.title = 'Statement Forge';
        }
    }
}

/**
 * Render score trend sparkline.
 * v3.0.33 Chunk E: Shows quality score history as interactive sparkline.
 * 
 * @param {Array} trendData - Array of {scan_time, score, grade, issue_count}
 */
function renderScoreSparkline(trendData) {
    const card = document.getElementById('score-trend-card');
    const svg = document.getElementById('score-sparkline');
    const summaryEl = document.getElementById('trend-summary');
    
    if (!card || !svg || !trendData || trendData.length < 2) {
        if (card) card.style.display = 'none';
        return;
    }
    
    card.style.display = 'block';
    
    const width = svg.clientWidth || 280;
    const height = 60;
    const padding = { top: 10, right: 10, bottom: 10, left: 10 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Compute scales
    const scores = trendData.map(d => d.score);
    const minScore = Math.min(...scores, 0);
    const maxScore = Math.max(...scores, 100);
    const scoreRange = maxScore - minScore || 1;
    
    const xScale = (i) => padding.left + (i / (trendData.length - 1)) * chartWidth;
    const yScale = (s) => padding.top + chartHeight - ((s - minScore) / scoreRange) * chartHeight;
    
    // Build path
    const linePath = trendData.map((d, i) => 
        `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.score)}`
    ).join(' ');
    
    const areaPath = linePath + 
        ` L ${xScale(trendData.length - 1)} ${yScale(minScore)}` +
        ` L ${xScale(0)} ${yScale(minScore)} Z`;
    
    // Generate points
    const points = trendData.map((d, i) => ({
        cx: xScale(i),
        cy: yScale(d.score),
        data: d
    }));
    
    // Build SVG content
    svg.innerHTML = `
        <defs>
            <linearGradient id="sparkline-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
            </linearGradient>
        </defs>
        <path class="sparkline-area" d="${areaPath}"/>
        <path class="sparkline-line" d="${linePath}"/>
        ${points.map((p, i) => `
            <circle class="sparkline-point" 
                cx="${p.cx}" cy="${p.cy}" r="4"
                data-index="${i}"
                data-score="${p.data.score}"
                data-date="${p.data.scan_time}"
                data-grade="${p.data.grade}"/>
        `).join('')}
    `;
    
    // Add hover interactions
    const tooltip = document.getElementById('sparkline-tooltip');
    svg.querySelectorAll('.sparkline-point').forEach(point => {
        point.addEventListener('mouseenter', (e) => {
            const score = point.dataset.score;
            const date = new Date(point.dataset.date).toLocaleDateString();
            const grade = point.dataset.grade;
            tooltip.innerHTML = `
                <div class="tooltip-score">Score: ${score} (${grade})</div>
                <div class="tooltip-date">${date}</div>
            `;
            tooltip.style.display = 'block';
            tooltip.style.left = `${point.cx.baseVal.value}px`;
            tooltip.style.top = `${point.cy.baseVal.value - 40}px`;
        });
        point.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    });
    
    // Update trend summary
    const first = trendData[0].score;
    const last = trendData[trendData.length - 1].score;
    const diff = last - first;
    
    if (diff > 5) {
        summaryEl.className = 'trend-summary trend-up';
        summaryEl.textContent = `↑ +${diff.toFixed(0)} pts`;
    } else if (diff < -5) {
        summaryEl.className = 'trend-summary trend-down';
        summaryEl.textContent = `↓ ${diff.toFixed(0)} pts`;
    } else {
        summaryEl.className = 'trend-summary trend-stable';
        summaryEl.textContent = `→ Stable`;
    }
    
    // Refresh icons
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}

/**
 * Render issue heatmap by category × severity.
 * v3.0.33 Chunk E: Visual grid showing issue density.
 * 
 * @param {Array} issues - Array of issue objects with category and severity
 */
function renderIssueHeatmap(issues) {
    // v3.0.114: Use combined analytics panel
    const combinedPanel = document.getElementById('issue-analytics-combined');
    const grid = document.getElementById('issue-heatmap');

    if (!grid || !issues || issues.length === 0) {
        if (combinedPanel) combinedPanel.style.display = 'none';
        return;
    }

    if (combinedPanel) combinedPanel.style.display = 'block';
    
    // Build category × severity matrix
    const severities = ['Critical', 'High', 'Medium', 'Low', 'Info'];
    const categorySet = new Set();
    const matrix = {};
    
    issues.forEach(issue => {
        const cat = issue.category || 'Other';
        const sev = issue.severity || 'Info';
        categorySet.add(cat);
        
        if (!matrix[cat]) matrix[cat] = {};
        matrix[cat][sev] = (matrix[cat][sev] || 0) + 1;
    });
    
    // Sort categories by total issues - show ALL categories with issues (no limit)
    // v4.0.2: Removed the top 10 limit to ensure all flagged categories appear
    const categories = Array.from(categorySet).sort((a, b) => {
        const aTotal = Object.values(matrix[a] || {}).reduce((s, v) => s + v, 0);
        const bTotal = Object.values(matrix[b] || {}).reduce((s, v) => s + v, 0);
        return bTotal - aTotal;
    });
    
    // Get intensity class based on count
    const getIntensity = (count) => {
        if (count === 0) return 'intensity-0';
        if (count <= 2) return 'intensity-1';
        if (count <= 5) return 'intensity-2';
        if (count <= 10) return 'intensity-3';
        return 'intensity-4';
    };
    
    // Build grid - v4.0.2: Increased category column width to prevent label cutoff
    const cols = severities.length + 1;
    grid.style.gridTemplateColumns = `minmax(200px, 250px) repeat(${severities.length}, minmax(40px, 60px))`;
    
    let html = '';
    
    // Header row
    html += `<div class="heatmap-row">`;
    html += `<div class="heatmap-cell header-cell">Category</div>`;
    severities.forEach(sev => {
        html += `<div class="heatmap-cell header-cell">${sev}</div>`;
    });
    html += `</div>`;
    
    // Data rows
    categories.forEach(cat => {
        html += `<div class="heatmap-row">`;
        html += `<div class="heatmap-cell category-label" title="${cat}">${cat}</div>`;
        severities.forEach(sev => {
            const count = (matrix[cat] && matrix[cat][sev]) || 0;
            const intensity = getIntensity(count);
            html += `<div class="heatmap-cell ${intensity}" 
                data-category="${cat}" 
                data-severity="${sev}" 
                data-count="${count}"
                title="${cat}: ${count} ${sev} issue(s)">
                ${count || '-'}
            </div>`;
        });
        html += `</div>`;
    });
    
    grid.innerHTML = html;
    
    // v3.0.35 POL-1: Use event delegation instead of per-cell handlers for scalability
    // Single click handler on container using event bubbling
    // v3.0.95: Fixed to use setChartFilter (was applyChartFilter which doesn't exist)
    grid.onclick = (e) => {
        const cell = e.target.closest('.heatmap-cell:not(.header-cell):not(.category-label)');
        if (!cell) return;
        
        const cat = cell.dataset.category;
        const sev = cell.dataset.severity;
        const count = parseInt(cell.dataset.count);
        
        if (count > 0 && typeof window.setChartFilter === 'function') {
            // Apply combined filter - filter by both category and severity
            // First apply category filter, then severity
            window.setChartFilter('category', cat);
            
            // Visual feedback: highlight selected cell
            grid.querySelectorAll('.heatmap-cell').forEach(c => c.classList.remove('active'));
            cell.classList.add('active');
            
            // Show toast with filter info
            if (typeof toast === 'function') {
                toast('info', `Filtered to ${cat} - ${sev} issues (${count})`, 2000);
            }
        }
    };
    
    // Setup export button
    const exportBtn = document.getElementById('btn-export-heatmap');
    if (exportBtn) {
        exportBtn.onclick = () => exportHeatmapAsPNG();
    }
}

/**
 * Render hyperlink validation status panel.
 * v3.0.95: Shows all checked hyperlinks with their validation status.
 * v3.0.114: Also renders in the inline combined panel (3-column layout).
 *
 * @param {Object} hyperlinkResults - Results from hyperlink checker
 */
function renderHyperlinkStatus(hyperlinkResults) {
    // v3.0.114: Render in inline panel (part of Document Analytics)
    const inlineSummary = document.getElementById('hyperlink-summary-inline');
    const inlineList = document.getElementById('hyperlink-list-inline');
    const hyperlinksPanel = document.getElementById('hyperlinks-panel');

    // Check if we have results
    if (!hyperlinkResults || !hyperlinkResults.links || hyperlinkResults.links.length === 0) {
        // Show empty state in inline panel
        if (inlineSummary) inlineSummary.innerHTML = '';
        if (inlineList) {
            inlineList.innerHTML = '<div class="hyperlinks-empty">No hyperlinks found</div>';
        }
        return;
    }

    const { total, valid, invalid, links } = hyperlinkResults;

    // Render inline summary
    if (inlineSummary) {
        inlineSummary.innerHTML = `
            <span class="stat valid"><i data-lucide="check-circle"></i> ${valid}</span>
            <span class="stat invalid"><i data-lucide="x-circle"></i> ${invalid}</span>
            <span class="stat total">${total} total</span>
        `;
    }

    // Render inline list
    if (inlineList) {
        // Sort: invalid first, then by URL
        const sortedLinks = [...links].sort((a, b) => {
            if (a.is_valid !== b.is_valid) return a.is_valid ? 1 : -1;
            return (a.url || '').localeCompare(b.url || '');
        });

        let html = '';
        sortedLinks.forEach(link => {
            const statusClass = link.is_valid ? 'valid' : 'invalid';
            const statusIcon = link.is_valid ? 'check-circle' : 'x-circle';
            const linkText = link.link_text || 'Link';
            const displayUrl = (link.url || '').length > 30
                ? link.url.substring(0, 27) + '...'
                : link.url;
            const safeUrl = escapeHtml(link.url || '');

            html += `
                <div class="hyperlink-row clickable" title="Click to open: ${safeUrl}" data-url="${safeUrl}">
                    <span class="status-icon ${statusClass}"><i data-lucide="${statusIcon}"></i></span>
                    <span class="link-text">${escapeHtml(linkText)}</span>
                    <span class="link-url">${escapeHtml(displayUrl)}</span>
                    <span class="open-link-icon"><i data-lucide="external-link"></i></span>
                </div>
            `;
        });

        inlineList.innerHTML = html;

        // Add click handlers to open links in new tab
        inlineList.querySelectorAll('.hyperlink-row.clickable').forEach(row => {
            row.addEventListener('click', (e) => {
                const url = row.dataset.url;
                if (url) {
                    window.open(url, '_blank', 'noopener,noreferrer');
                }
            });
        });
    }

    // Refresh icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // v3.0.125: Render Domain Health Carousel in review tab
    const carouselContainer = document.getElementById('review-domain-carousel');
    if (carouselContainer && links.length > 0 && typeof HyperlinkVisualization !== 'undefined') {
        try {
            // Convert links to validation result format expected by carousel
            const validationResults = links.map(link => ({
                url: link.url,
                status: link.is_valid ? 'WORKING' : 'BROKEN',
                statusCode: link.status_code || (link.is_valid ? 200 : 404),
                message: link.message || '',
                responseTime: link.response_time || 0
            }));

            // Show the carousel container
            carouselContainer.style.display = 'block';

            // Create the domain health carousel
            HyperlinkVisualization.createDomainHealthCarousel(carouselContainer, validationResults);
        } catch (err) {
            console.warn('[TWR] Failed to render domain health carousel:', err);
            carouselContainer.style.display = 'none';
        }
    }
}

/**
 * Toggle hyperlink list expansion.
 */
function toggleHyperlinkList(btn) {
    const container = btn.closest('.hyperlink-status-body');
    const preview = container.querySelector('.hyperlink-preview');
    
    if (preview) {
        preview.classList.toggle('expanded');
        const isExpanded = preview.classList.contains('expanded');
        btn.innerHTML = isExpanded 
            ? '<i data-lucide="chevron-up"></i> Show less'
            : `<i data-lucide="chevron-down"></i> Show all links`;
        
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

/**
 * Export comprehensive Document Analytics Report as PNG image.
 * v4.0.2: Enhanced export with full metrics, matching UI color scheme.
 * Includes: heatmap, readability scores, document score, issue summary, recommendations.
 * Works offline in air-gapped environments.
 */
async function exportHeatmapAsPNG() {
    const grid = document.getElementById('issue-heatmap');

    if (!grid) {
        if (typeof toast === 'function') toast('warning', 'Analytics data not available');
        return;
    }

    try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // v4.0.2: Exact color scheme matching UI intensity classes
        const INTENSITY_COLORS = {
            0: { bg: '#f3f4f6', text: '#9ca3af', border: '#d1d5db' },           // intensity-0: gray
            1: { bg: '#86efac', text: '#14532d', border: '#4ade80' },           // intensity-1: green
            2: { bg: '#fde047', text: '#713f12', border: '#facc15' },           // intensity-2: yellow
            3: { bg: '#fdba74', text: '#7c2d12', border: '#fb923c' },           // intensity-3: orange
            4: { bg: '#fca5a5', text: '#7f1d1d', border: '#f87171' }            // intensity-4: red
        };

        const SEVERITY_ORDER = ['Critical', 'High', 'Medium', 'Low', 'Info'];
        const SEVERITY_COLORS = {
            'Critical': '#dc2626',
            'High': '#f97316',
            'Medium': '#3b82f6',
            'Low': '#22c55e',
            'Info': '#0ea5e9'
        };

        // Extract heatmap data from DOM
        const rows = grid.querySelectorAll('.heatmap-row');
        const categories = [];
        const dataMap = {};
        let totalIssues = 0;
        const severityTotals = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 };

        rows.forEach((row, rowIdx) => {
            if (rowIdx === 0) return;
            const catLabel = row.querySelector('.category-label');
            if (!catLabel) return;

            const category = catLabel.textContent.trim();
            categories.push(category);
            dataMap[category] = {};

            row.querySelectorAll('.heatmap-cell:not(.category-label)').forEach((cell, colIdx) => {
                const severity = SEVERITY_ORDER[colIdx];
                const count = parseInt(cell.dataset.count) || 0;
                dataMap[category][severity] = count;
                totalIssues += count;
                severityTotals[severity] += count;
            });
        });

        if (categories.length === 0) {
            if (typeof toast === 'function') toast('warning', 'No analytics data to export');
            return;
        }

        // Get additional metrics from State and DOM
        const docScore = State.reviewResults?.score ?? '--';
        const docGrade = State.reviewResults?.grade ?? '--';
        const readability = State.reviewResults?.readability || {};
        const flesch = readability.flesch_reading_ease;
        const fkGrade = readability.flesch_kincaid_grade;
        const fogIndex = readability.gunning_fog_index || readability.gunning_fog;
        const filename = State.filename || 'Document';

        // Find top issues by category
        const categoryTotals = categories.map(cat => ({
            name: cat,
            total: Object.values(dataMap[cat]).reduce((a, b) => a + b, 0)
        })).sort((a, b) => b.total - a.total);

        // Canvas dimensions - v4.0.2: Expanded for comprehensive report
        const padding = 30;
        const headerHeight = 120;
        const metricsHeight = 100;
        const severityBarHeight = 60;
        const heatmapCellSize = 50;
        const heatmapLabelWidth = 180;
        const legendHeight = 50;
        const recommendationsHeight = 140;
        const footerHeight = 40;

        const heatmapWidth = heatmapLabelWidth + (SEVERITY_ORDER.length * heatmapCellSize);
        const heatmapHeight = (categories.length + 1) * heatmapCellSize;

        canvas.width = Math.max(700, heatmapWidth + padding * 2);
        canvas.height = headerHeight + metricsHeight + severityBarHeight + heatmapHeight + legendHeight + recommendationsHeight + footerHeight + padding * 2;

        // Background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        let currentY = padding;

        // ========== HEADER SECTION ==========
        // Title bar with accent color
        ctx.fillStyle = '#1e3a5f';
        ctx.fillRect(0, 0, canvas.width, 8);

        // Document title
        ctx.fillStyle = '#1e3a5f';
        ctx.font = 'bold 22px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Document Analytics Report', padding, currentY + 30);

        // Filename
        ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#6b7280';
        ctx.fillText(filename, padding, currentY + 52);

        // AEGIS branding
        ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#0ea5e9';
        ctx.textAlign = 'right';
        ctx.fillText('AEGIS', canvas.width - padding, currentY + 30);
        ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#9ca3af';
        ctx.fillText('Aerospace Engineering Governance & Inspection System', canvas.width - padding, currentY + 44);

        currentY += 70;

        // Separator line
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, currentY);
        ctx.lineTo(canvas.width - padding, currentY);
        ctx.stroke();

        currentY += 20;

        // ========== KEY METRICS ROW ==========
        const metricBoxWidth = 130;
        const metricBoxHeight = 70;
        const metricsStartX = padding;
        const metrics = [
            { label: 'Total Issues', value: totalIssues.toString(), color: totalIssues > 50 ? '#dc2626' : totalIssues > 20 ? '#f97316' : '#22c55e' },
            { label: 'Quality Score', value: docScore.toString(), color: docScore >= 70 ? '#22c55e' : docScore >= 50 ? '#f97316' : '#dc2626' },
            { label: 'Grade', value: docGrade, color: ['A', 'B'].includes(docGrade) ? '#22c55e' : ['C', 'D'].includes(docGrade) ? '#f97316' : '#dc2626' },
            { label: 'Flesch Score', value: flesch?.toFixed(0) ?? '--', color: flesch >= 60 ? '#22c55e' : flesch >= 30 ? '#f97316' : '#dc2626' },
            { label: 'Grade Level', value: fkGrade?.toFixed(1) ?? '--', color: fkGrade <= 12 ? '#22c55e' : '#f97316' }
        ];

        metrics.forEach((metric, i) => {
            const x = metricsStartX + (i * (metricBoxWidth + 10));

            // Box background
            ctx.fillStyle = '#f9fafb';
            ctx.fillRect(x, currentY, metricBoxWidth, metricBoxHeight);
            ctx.strokeStyle = '#e5e7eb';
            ctx.strokeRect(x, currentY, metricBoxWidth, metricBoxHeight);

            // Value
            ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = metric.color;
            ctx.textAlign = 'center';
            ctx.fillText(metric.value, x + metricBoxWidth / 2, currentY + 35);

            // Label
            ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = '#6b7280';
            ctx.fillText(metric.label, x + metricBoxWidth / 2, currentY + 55);
        });

        currentY += metricBoxHeight + 25;

        // ========== SEVERITY DISTRIBUTION BAR ==========
        ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#374151';
        ctx.textAlign = 'left';
        ctx.fillText('SEVERITY DISTRIBUTION', padding, currentY);

        currentY += 15;

        const barWidth = canvas.width - padding * 2;
        const barHeight = 24;
        let barX = padding;

        // Draw severity bar segments
        SEVERITY_ORDER.forEach(sev => {
            const count = severityTotals[sev];
            const segWidth = totalIssues > 0 ? (count / totalIssues) * barWidth : 0;
            if (segWidth > 0) {
                ctx.fillStyle = SEVERITY_COLORS[sev];
                ctx.fillRect(barX, currentY, segWidth, barHeight);

                // Label inside segment if wide enough
                if (segWidth > 50) {
                    ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                    ctx.fillStyle = '#ffffff';
                    ctx.textAlign = 'center';
                    ctx.fillText(`${sev}: ${count}`, barX + segWidth / 2, currentY + 16);
                }
                barX += segWidth;
            }
        });

        // Bar outline
        ctx.strokeStyle = '#d1d5db';
        ctx.strokeRect(padding, currentY, barWidth, barHeight);

        currentY += barHeight + 25;

        // ========== HEATMAP SECTION ==========
        ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#374151';
        ctx.textAlign = 'left';
        ctx.fillText('ISSUES BY CATEGORY', padding, currentY);

        currentY += 15;

        const heatmapStartX = padding;
        const heatmapStartY = currentY;

        // Get intensity level based on count
        const getIntensity = (count) => {
            if (count === 0) return 0;
            if (count <= 2) return 1;
            if (count <= 5) return 2;
            if (count <= 10) return 3;
            return 4;
        };

        // Header row
        ctx.font = 'bold 10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#6b7280';
        ctx.textAlign = 'center';

        SEVERITY_ORDER.forEach((sev, i) => {
            const x = heatmapStartX + heatmapLabelWidth + (i * heatmapCellSize) + heatmapCellSize / 2;
            ctx.fillText(sev, x, heatmapStartY + 15);
        });

        currentY += 25;

        // Data rows
        categories.forEach((category, rowIdx) => {
            const rowY = heatmapStartY + 25 + (rowIdx * heatmapCellSize);

            // Category label
            ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = '#374151';
            ctx.textAlign = 'right';

            let catDisplay = category;
            const maxWidth = heatmapLabelWidth - 15;
            while (ctx.measureText(catDisplay).width > maxWidth && catDisplay.length > 3) {
                catDisplay = catDisplay.slice(0, -4) + '...';
            }
            ctx.fillText(catDisplay, heatmapStartX + heatmapLabelWidth - 10, rowY + heatmapCellSize / 2 + 4);

            // Cells
            SEVERITY_ORDER.forEach((sev, colIdx) => {
                const cellX = heatmapStartX + heatmapLabelWidth + (colIdx * heatmapCellSize);
                const count = dataMap[category][sev] || 0;
                const intensity = getIntensity(count);
                const colors = INTENSITY_COLORS[intensity];

                // Cell background
                ctx.fillStyle = colors.bg;
                ctx.fillRect(cellX + 2, rowY + 2, heatmapCellSize - 4, heatmapCellSize - 4);

                // Cell border
                ctx.strokeStyle = colors.border;
                ctx.lineWidth = 1;
                ctx.strokeRect(cellX + 2, rowY + 2, heatmapCellSize - 4, heatmapCellSize - 4);

                // Cell value
                ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = colors.text;
                ctx.textAlign = 'center';
                ctx.fillText(count > 0 ? count.toString() : '-', cellX + heatmapCellSize / 2, rowY + heatmapCellSize / 2 + 5);
            });
        });

        currentY = heatmapStartY + 25 + (categories.length * heatmapCellSize) + 15;

        // ========== LEGEND ==========
        ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#6b7280';
        ctx.textAlign = 'left';

        const legendItems = [
            { label: '0', intensity: 0 },
            { label: '1-2', intensity: 1 },
            { label: '3-5', intensity: 2 },
            { label: '6-10', intensity: 3 },
            { label: '10+', intensity: 4 }
        ];

        let legendX = padding;
        ctx.fillText('Legend:', legendX, currentY + 12);
        legendX += 50;

        legendItems.forEach(item => {
            const colors = INTENSITY_COLORS[item.intensity];

            ctx.fillStyle = colors.bg;
            ctx.fillRect(legendX, currentY, 20, 20);
            ctx.strokeStyle = colors.border;
            ctx.strokeRect(legendX, currentY, 20, 20);

            ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = '#6b7280';
            ctx.textAlign = 'left';
            ctx.fillText(item.label, legendX + 25, currentY + 14);

            legendX += 65;
        });

        currentY += 35;

        // ========== RECOMMENDATIONS SECTION ==========
        ctx.strokeStyle = '#e5e7eb';
        ctx.beginPath();
        ctx.moveTo(padding, currentY);
        ctx.lineTo(canvas.width - padding, currentY);
        ctx.stroke();

        currentY += 15;

        ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#374151';
        ctx.textAlign = 'left';
        ctx.fillText('KEY FINDINGS & RECOMMENDATIONS', padding, currentY);

        currentY += 20;

        // Generate recommendations
        const recommendations = [];

        if (categoryTotals.length > 0 && categoryTotals[0].total > 10) {
            recommendations.push(`• Focus on ${categoryTotals[0].name} issues (${categoryTotals[0].total} found) for maximum impact`);
        }

        if (severityTotals.Critical > 0 || severityTotals.High > 0) {
            recommendations.push(`• Address ${severityTotals.Critical + severityTotals.High} Critical/High severity issues before publication`);
        }

        if (flesch && flesch < 40) {
            recommendations.push(`• Readability is challenging (Flesch ${flesch?.toFixed(0)}). Consider simplifying sentence structure`);
        } else if (flesch && flesch >= 60) {
            recommendations.push(`• Good readability (Flesch ${flesch?.toFixed(0)}). Content is accessible to general audiences`);
        }

        if (fkGrade && fkGrade > 14) {
            recommendations.push(`• Grade level ${fkGrade?.toFixed(1)} suggests graduate-level complexity`);
        }

        if (docScore && docScore < 50) {
            recommendations.push(`• Quality score ${docScore} indicates significant revision needed`);
        } else if (docScore && docScore >= 80) {
            recommendations.push(`• Excellent quality score (${docScore}). Document is near publication-ready`);
        }

        if (recommendations.length === 0) {
            recommendations.push('• Document analysis complete. Review individual issues for detailed findings.');
        }

        ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#4b5563';

        recommendations.slice(0, 5).forEach((rec, i) => {
            ctx.fillText(rec, padding, currentY + (i * 18));
        });

        currentY += Math.min(recommendations.length, 5) * 18 + 20;

        // ========== FOOTER ==========
        ctx.strokeStyle = '#e5e7eb';
        ctx.beginPath();
        ctx.moveTo(padding, canvas.height - footerHeight);
        ctx.lineTo(canvas.width - padding, canvas.height - footerHeight);
        ctx.stroke();

        ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#9ca3af';
        ctx.textAlign = 'left';
        ctx.fillText(`Generated: ${new Date().toLocaleString()}`, padding, canvas.height - 15);

        ctx.textAlign = 'right';
        ctx.fillText('AEGIS Document Analytics', canvas.width - padding, canvas.height - 15);

        // Generate filename with date
        const dateStr = new Date().toISOString().split('T')[0];
        const safeFilename = filename.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30);
        downloadCanvasAsPNG(canvas, `AEGIS_Analytics_${safeFilename}_${dateStr}.png`);

        console.log('[Analytics] Comprehensive report exported as PNG');
        if (typeof toast === 'function') toast('success', 'Analytics report exported');

    } catch (err) {
        console.error('[Analytics] Failed to export analytics:', err);
        if (typeof toast === 'function') {
            toast('error', 'Failed to export: ' + err.message);
        }
    }
}

/**
 * Helper to download canvas as PNG.
 */
function downloadCanvasAsPNG(canvas, filename) {
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
}

/**
 * Fetch and render score trend for current document.
 * v3.0.33 Chunk E: Called after review completes.
 * 
 * @param {string} filename - Document filename
 */
async function fetchAndRenderScoreTrend(filename) {
    if (!filename) return;
    
    try {
        const response = await api(`/score-trend?filename=${encodeURIComponent(filename)}&limit=10`);
        if (response.success && response.data && response.data.trend) {
            renderScoreSparkline(response.data.trend);
        }
    } catch (err) {
        console.warn('[Analytics] Could not fetch score trend:', err);
        // Hide sparkline card on error
        const card = document.getElementById('score-trend-card');
        if (card) card.style.display = 'none';
    }
}

function getScoreColor(score) {
    if (window.TWR?.Renderers?.getScoreColor) {
        return TWR.Renderers.getScoreColor(score);
    }
    // Inline fallback
    if (score >= 90) return '#28A745';
    if (score >= 80) return '#17A2B8';
    if (score >= 70) return '#FFC107';
    if (score >= 60) return '#FD7E14';
    return '#DC3545';
}

// ============================================================
// FILTERING & SORTING
// ============================================================

// Filter state for persistence
const FilterState = {
    chartFilter: null,      // { type: 'severity'|'category', value: string }
    categorySearch: '',
    
    save() {
        try {
            localStorage.setItem('twr_filters', JSON.stringify({
                severities: Array.from(document.querySelectorAll('.sev-filter input:checked')).map(cb => cb.id),
                categories: Array.from(document.querySelectorAll('#category-list input:checked')).map(cb => cb.dataset.category)
            }));
        } catch (e) { /* ignore */ }
    },
    
    restore() {
        try {
            const saved = JSON.parse(localStorage.getItem('twr_filters'));
            if (saved?.severities) {
                document.querySelectorAll('.sev-filter input').forEach(cb => {
                    cb.checked = saved.severities.includes(cb.id);
                });
            }
        } catch (e) { /* ignore */ }
    }
};

function applyFilters() {
    const search = document.getElementById('issue-search')?.value.toLowerCase().trim() || '';
    const severities = new Set();
    const categories = new Set();

    // v3.0.13: Get severities from unified filter bar (primary) or sidebar (fallback)
    const unifiedToggles = document.querySelectorAll('#unified-severity-toggles .sev-toggle.active');
    if (unifiedToggles.length > 0) {
        unifiedToggles.forEach(btn => {
            const sev = btn.dataset.severity;
            severities.add(sev.charAt(0).toUpperCase() + sev.slice(1));
        });
    } else {
        // Fallback to sidebar filters
        document.querySelectorAll('.sev-filter input:checked').forEach(cb => {
            const sev = cb.id.replace('filter-', '');
            severities.add(sev.charAt(0).toUpperCase() + sev.slice(1));
        });
    }

    // v3.0.13: Get categories from unified dropdown (primary) or sidebar (fallback)
    const unifiedCats = document.querySelectorAll('#unified-category-list input:checked');
    if (unifiedCats.length > 0) {
        unifiedCats.forEach(cb => categories.add(cb.dataset.category));
    } else {
        // Fallback to sidebar category filters
        document.querySelectorAll('#category-list input:checked, #category-pinned input:checked').forEach(cb => {
            categories.add(cb.dataset.category);
        });
    }

    // Apply chart filter if active
    if (FilterState.chartFilter) {
        if (FilterState.chartFilter.type === 'severity') {
            severities.clear();
            severities.add(FilterState.chartFilter.value);
        } else if (FilterState.chartFilter.type === 'category') {
            categories.clear();
            categories.add(FilterState.chartFilter.value);
        }
    }

    // Filter issues
    State.filteredIssues = State.issues.filter((issue, idx) => {
        // Custom filter (from family selection)
        if (State.filters?.customFilter && !State.filters.customFilter(issue, idx)) {
            return false;
        }
        
        // Severity filter
        if (severities.size > 0 && !severities.has(issue.severity)) return false;

        // Category filter (if any selected - empty means all)
        if (categories.size > 0 && !categories.has(issue.category)) return false;

        // v3.0.29: Validation filter
        if (FilterState.passesValidationFilter && !FilterState.passesValidationFilter(issue)) {
            return false;
        }

        // Search filter
        if (search) {
            const searchable = [
                issue.category,
                issue.severity,
                issue.message,
                issue.flagged_text,
                issue.suggestion
            ].join(' ').toLowerCase();
            if (!searchable.includes(search)) return false;
        }

        return true;
    });

    // Sort
    sortIssues();

    // Reset pagination
    State.currentPage = 1;

    // Update UI
    renderIssuesList();
    updateStats();
    updateUnifiedFilterChips();  // v3.0.13: Use unified chips
    updateChartFilterNotice();
    updateFilterResultSummary(); // v3.0.13: Update summary

    // Update clear search button
    const clearBtn = document.getElementById('btn-clear-search');
    if (clearBtn) clearBtn.style.display = search ? 'block' : 'none';

    // Update filtered count
    const filteredCount = document.getElementById('filtered-count');
    if (filteredCount) {
        filteredCount.textContent = State.filteredIssues.length < State.issues.length
            ? `(${State.filteredIssues.length} of ${State.issues.length})`
            : '';
    }
    
    // Persist filters
    FilterState.save();
}

function updateFilterChips() {
    // v3.0.13: Delegate to unified filter chips
    updateUnifiedFilterChips();
}

function removeFilterChip(type, value) {
    if (type === 'severity') {
        const cb = document.getElementById(`filter-${value.toLowerCase()}`);
        if (cb) cb.checked = false;
    } else if (type === 'category') {
        document.querySelectorAll(`#category-list input[data-category="${value}"], #category-pinned input[data-category="${value}"]`).forEach(cb => {
            cb.checked = false;
        });
    } else if (type === 'chart') {
        FilterState.chartFilter = null;
    } else if (type === 'family') {
        clearFamilyFilter();
        return; // clearFamilyFilter already calls applyFilters
    }
    applyFilters();
}

function updateChartFilterNotice() {
    const notice = document.getElementById('chart-filter-notice');
    const valueSpan = document.getElementById('chart-filter-value');
    
    if (!notice) return;
    
    if (FilterState.chartFilter) {
        notice.style.display = 'flex';
        if (valueSpan) valueSpan.textContent = FilterState.chartFilter.value;
    } else {
        notice.style.display = 'none';
    }
}

function clearChartFilter() {
    FilterState.chartFilter = null;
    applyFilters();
}

function setChartFilter(type, value) {
    if (window.TWR?.Renderers?.setChartFilter) {
        return TWR.Renderers.setChartFilter(type, value);
    }
    // Fallback
    FilterState.chartFilter = { type, value };
    applyFilters();
}

function sortByColumn(column) {
    if (State.sortColumn === column) {
        State.sortDirection = State.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        State.sortColumn = column;
        State.sortDirection = 'asc';
    }

    // Update sort icons
    document.querySelectorAll('.sortable').forEach(col => {
        const icon = col.querySelector('.sort-icon');
        if (icon) {
            if (col.dataset.sort === column) {
                col.classList.add('sorted');
                icon.setAttribute('data-lucide', State.sortDirection === 'asc' ? 'chevron-up' : 'chevron-down');
            } else {
                col.classList.remove('sorted');
            }
        }
    });
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }

    sortIssues();
    renderIssuesList();
}

function sortIssues() {
    const col = State.sortColumn;
    const dir = State.sortDirection === 'asc' ? 1 : -1;

    State.filteredIssues.sort((a, b) => {
        if (col === 'severity') {
            return dir * (SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
        }
        const aVal = (a[col] || '').toString().toLowerCase();
        const bVal = (b[col] || '').toString().toLowerCase();
        return dir * aVal.localeCompare(bVal);
    });
}

// ============================================================
// ISSUE RENDERING (Delegated to TWR.Renderers)
// ============================================================
function renderIssuesList() {
    if (window.TWR?.Renderers?.renderIssuesList) {
        return TWR.Renderers.renderIssuesList();
    }
    // Minimal fallback
    const container = document.getElementById('issues-list');
    if (container) container.innerHTML = '<div class="empty-issues"><p>Renderers module not loaded</p></div>';
}

function updatePagination(start, end, total) {
    if (window.TWR?.Renderers?.updatePagination) {
        return TWR.Renderers.updatePagination(start, end, total);
    }
}

function changePage(delta) {
    if (window.TWR?.Renderers?.changePage) {
        return TWR.Renderers.changePage(delta);
    }
}

function navigateIssues(direction) {
    if (window.TWR?.Renderers?.navigateIssues) {
        return TWR.Renderers.navigateIssues(direction);
    }
}

// ============================================================
// SELECTION (Delegated to TWR.Renderers)
// ============================================================
function toggleIssueSelection(index) {
    if (window.TWR?.Renderers?.toggleIssueSelection) {
        return TWR.Renderers.toggleIssueSelection(index);
    }
    // Fallback - v3.0.35: Use centralized key helper
    const issue = State.filteredIssues[index];
    const issueId = getIssueKey(issue, index);
    if (State.selectedIssues.has(issueId)) {
        State.selectedIssues.delete(issueId);
    } else {
        State.selectedIssues.add(issueId);
    }
    updateSelectionUI();
}

function selectIssues(mode) {
    if (window.TWR?.Renderers?.selectIssues) {
        return TWR.Renderers.selectIssues(mode);
    }
    // Fallback - v3.0.35: Use centralized key helper
    if (mode === 'all') {
        State.filteredIssues.forEach((issue, i) => {
            const issueId = getIssueKey(issue, i);
            State.selectedIssues.add(issueId);
        });
    } else {
        State.selectedIssues.clear();
    }
    updateSelectionUI();
    renderIssuesList();
}

function isIssueSelected(index) {
    if (window.TWR?.Renderers?.isIssueSelected) {
        return TWR.Renderers.isIssueSelected(index);
    }
    // Fallback - v3.0.35: Use centralized key helper
    const issue = State.filteredIssues[index];
    const issueId = getIssueKey(issue, index);
    return State.selectedIssues.has(issueId);
}

function updateSelectionUI() {
    if (window.TWR?.Renderers?.updateSelectionUI) {
        return TWR.Renderers.updateSelectionUI();
    }
    // Fallback
    const selCount = document.getElementById('selection-count');
    if (selCount) selCount.textContent = `${State.selectedIssues.size} selected`;
}

// ============================================================
// CHARTS (Delegated to TWR.Renderers)
// ============================================================
function renderCharts(data) {
    if (window.TWR?.Renderers?.renderCharts) {
        return TWR.Renderers.renderCharts(data);
    }
    // No fallback - charts just won't render
}

// ============================================================
// ROLES (Delegated to TWR.Roles module)
// ============================================================
// All roles functionality has been extracted to features/roles.js
// Functions are accessed via TWR.Roles.* or global aliases

function renderRolesSummary() {
    if (window.TWR?.Roles?.renderRolesSummary) {
        return TWR.Roles.renderRolesSummary();
    }
}

async function showRolesModal() {
    if (window.TWR?.Roles?.showRolesModal) {
        return TWR.Roles.showRolesModal();
    }
}

function initRolesTabs() {
    if (window.TWR?.Roles?.initRolesTabs) {
        return TWR.Roles.initRolesTabs();
    }
}

function renderRolesOverview() {
    if (window.TWR?.Roles?.renderRolesOverview) {
        return TWR.Roles.renderRolesOverview();
    }
}

function renderRolesDetails() {
    if (window.TWR?.Roles?.renderRolesDetails) {
        return TWR.Roles.renderRolesDetails();
    }
}

function renderRolesMatrix() {
    if (window.TWR?.Roles?.renderRolesMatrix) {
        return TWR.Roles.renderRolesMatrix();
    }
}

function renderDocumentLog() {
    if (window.TWR?.Roles?.renderDocumentLog) {
        return TWR.Roles.renderDocumentLog();
    }
}

function initAdjudication() {
    if (window.TWR?.Roles?.initAdjudication) {
        return TWR.Roles.initAdjudication();
    }
}

function loadAdjudication() {
    if (window.TWR?.Roles?.loadAdjudication) {
        return TWR.Roles.loadAdjudication();
    }
}

async function renderRolesGraph(forceRefresh = false) {
    if (window.TWR?.Roles?.renderRolesGraph) {
        return TWR.Roles.renderRolesGraph(forceRefresh);
    }
}

function initGraphControls() {
    if (window.TWR?.Roles?.initGraphControls) {
        return TWR.Roles.initGraphControls();
    }
}

function resetGraphView() {
    if (window.TWR?.Roles?.resetGraphView) {
        return TWR.Roles.resetGraphView();
    }
}

function clearNodeSelection(force = false) {
    if (window.TWR?.Roles?.clearNodeSelection) {
        return TWR.Roles.clearNodeSelection(force);
    }
}

function updateGraphWithAdjudication() {
    if (window.TWR?.Roles?.updateGraphWithAdjudication) {
        return TWR.Roles.updateGraphWithAdjudication();
    }
}

async function exportRoles(format = 'csv') {
    if (window.TWR?.Roles?.exportRoles) {
        return TWR.Roles.exportRoles(format);
    }
}

async function exportDeliverables(format = 'csv') {
    if (window.TWR?.Roles?.exportDeliverables) {
        return TWR.Roles.exportDeliverables(format);
    }
}

function downloadBlob(blob, filename) {
    if (window.TWR?.Roles?.downloadBlob) {
        return TWR.Roles.downloadBlob(blob, filename);
    }
    // Fallback implementation
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Download CSV content as a file with Excel-compatible formatting.
 * Adds UTF-8 BOM and normalizes line endings to CRLF for Windows Excel compatibility.
 * @param {string} csvContent - The CSV content string
 * @param {string} filename - The download filename
 */
function downloadCSV(csvContent, filename) {
    const bom = '\uFEFF';
    const crlf = csvContent.replace(/\r?\n/g, '\r\n');
    const blob = new Blob([bom + crlf], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function getTimestamp() {
    if (window.TWR?.Roles?.getTimestamp) {
        return TWR.Roles.getTimestamp();
    }
    return new Date().toISOString().slice(0, 10).replace(/-/g, '');
}

// EXPORT
// ============================================================
function showExportModal() {
    if (!State.reviewResults) {
        toast('warning', 'Please run a review first');
        return;
    }

    // Handle PDF vs DOCX export options
    const isPDF = State.fileType === 'pdf';
    const docxCard = document.getElementById('format-docx-card');
    const docxRadio = document.querySelector('input[name="export-format"][value="docx"]');
    const pdfReportRadio = document.querySelector('input[name="export-format"][value="pdf"]');
    const pdfNotice = document.getElementById('export-pdf-notice');
    const applyFixesGroup = document.getElementById('apply-fixes-group');
    const applyFixesCheckbox = document.getElementById('export-apply-fixes');
    const launcher = document.getElementById('fix-assistant-launcher');

    if (isPDF) {
        // Disable DOCX export for PDF files
        if (docxCard) {
            docxCard.style.opacity = '0.5';
            docxCard.style.pointerEvents = 'none';
        }
        if (docxRadio) docxRadio.disabled = true;
        // v5.9.4: Default to PDF Report for PDF source files
        if (pdfReportRadio) pdfReportRadio.checked = true;
        if (pdfNotice) pdfNotice.style.display = 'block';
        if (applyFixesGroup) applyFixesGroup.style.display = 'none';
    } else {
        // Enable all options for DOCX files
        if (docxCard) {
            docxCard.style.opacity = '1';
            docxCard.style.pointerEvents = 'auto';
        }
        if (docxRadio) {
            docxRadio.disabled = false;
            docxRadio.checked = true;
        }
        if (pdfNotice) pdfNotice.style.display = 'none';
        if (applyFixesGroup) applyFixesGroup.style.display = 'block';

        // v3.0.96: Initialize Fix Assistant
        if (window.FixAssistant) {
            FixAssistant.init();
        }

        // v3.0.111: Always show launcher (consolidated UI)
        if (launcher) {
            launcher.style.display = 'flex';
        }

        // v5.9.4: Restore Fix Assistant stats if user already reviewed fixes
        if (window.FixAssistantState && FixAssistantState.isInitialized()) {
            const faStats = FixAssistantState.getStatistics();
            const selectedEl = document.getElementById('selected-fix-count');
            const fixableEl = document.getElementById('fixable-count');
            if (selectedEl) selectedEl.textContent = faStats.accepted || 0;
            if (fixableEl) fixableEl.textContent = (State.fixes || []).length;
            // Auto-check apply fixes if user previously accepted fixes
            if (applyFixesCheckbox && faStats.accepted > 0) {
                applyFixesCheckbox.checked = true;
            }
        }
    }

    // v6.0.2: Update apply fixes label based on review role mode
    const applyLabel = document.querySelector('label[for="export-apply-fixes"]');
    if (applyLabel) {
        const isReviewer = (window.FixAssistantState && typeof FixAssistantState.getReviewRole === 'function')
            ? FixAssistantState.getReviewRole() === 'reviewer'
            : false;
        applyLabel.textContent = isReviewer
            ? 'Add accepted fixes as recommendation comments'
            : 'Apply selected fixes (Track Changes)';
    }

    // v5.9.4: Populate export filter chips
    _populateExportFilterChips();

    updateSelectionUI();
    updateExportOptions();
    showModal('modal-export');
}

/**
 * Open Export Review modal with issues based on current export mode selection
 * v2.9.4 #22: Bridge function between export modal and review modal
 */
function openExportReview() {
    const mode = document.querySelector('input[name="export-mode"]:checked')?.value || 'all';
    
    let issuesToReview;
    switch (mode) {
        case 'filtered':
            issuesToReview = State.filteredIssues;
            break;
        case 'selected':
            // v3.0.35 Fix: Use centralized getIssueKey for consistent matching
            issuesToReview = State.filteredIssues.filter((issue, i) => {
                const key = getIssueKey(issue, i);
                return State.selectedIssues.has(key);
            });
            break;
        default:
            issuesToReview = State.issues;
    }
    
    if (!issuesToReview || issuesToReview.length === 0) {
        toast('warning', 'No issues to review');
        return;
    }
    
    // Close export modal and open review modal
    closeModals();
    
    if (window.ExportReview) {
        ExportReview.open(issuesToReview);
    } else {
        toast('error', 'Export Review module not loaded');
    }
}
window.openExportReview = openExportReview;

function updateExportOptions() {
    const format = document.querySelector('input[name="export-format"]:checked')?.value || 'docx';
    const applyFixesGroup = document.getElementById('apply-fixes-group');

    // Hide apply fixes for non-docx formats
    if (applyFixesGroup) {
        applyFixesGroup.style.display = format === 'docx' ? 'block' : 'none';
    }

    // Update fixable preview with checkboxes
    populateFixPreview();

    // v5.9.4: Update export filter preview count
    _updateExportFilterPreview();
}

async function executeExport() {
    const format = document.querySelector('input[name="export-format"]:checked')?.value || 'docx';
    const mode = document.querySelector('input[name="export-mode"]:checked')?.value || 'all';
    const reviewerName = document.getElementById('export-reviewer-name')?.value || 'AEGIS';
    const applyFixes = document.getElementById('export-apply-fixes')?.checked || false;

    // Get issues based on mode
    let issuesToExport;
    switch (mode) {
        case 'filtered':
            issuesToExport = State.filteredIssues;
            break;
        case 'selected':
            // v3.0.35 Fix: Use centralized getIssueKey for consistent matching
            issuesToExport = State.filteredIssues.filter((issue, i) => {
                const key = getIssueKey(issue, i);
                return State.selectedIssues.has(key);
            });
            break;
        default:
            issuesToExport = State.issues;
    }

    // v5.9.4: Apply export filter panel filters
    const exportFilters = _getExportFilters();
    if (exportFilters.severities.length > 0 || exportFilters.categories.length > 0) {
        if (exportFilters.severities.length > 0) {
            issuesToExport = issuesToExport.filter(i => exportFilters.severities.includes(i.severity || 'Info'));
        }
        if (exportFilters.categories.length > 0) {
            issuesToExport = issuesToExport.filter(i => exportFilters.categories.includes(i.category || ''));
        }
    }

    if (issuesToExport.length === 0) {
        toast('warning', 'No issues to export');
        return;
    }

    closeModals();

    // v5.9.4: Show export progress overlay
    _showExportProgress(format, issuesToExport.length);

    try {
        let endpoint, body;

        switch (format) {
            case 'xlsx':
            case 'excel':
                // v3.0.35: Use enhanced XLSX endpoint
                endpoint = '/export/xlsx';
                body = {
                    mode: mode,
                    severities: exportFilters.severities.length > 0 ? exportFilters.severities : null,
                    issues: issuesToExport,
                    results: {
                        score: State.reviewResults?.score,
                        document_info: State.reviewResults?.document_info
                    }
                };
                break;
            case 'csv':
                endpoint = '/export/csv';
                body = { issues: issuesToExport, type: 'issues' };
                break;
            case 'pdf': {
                // v5.9.4: Server-side PDF report via reportlab
                endpoint = '/export/pdf';
                body = {
                    issues: issuesToExport,
                    mode: mode,
                    reviewer_name: reviewerName,
                    filters: {
                        severities: exportFilters.severities.length > 0 ? exportFilters.severities : null,
                        categories: exportFilters.categories.length > 0 ? exportFilters.categories : null
                    }
                };
                break;
            }
            case 'json': {
                // v5.0.2: Client-side JSON export (no backend endpoint needed)
                const jsonData = JSON.stringify({
                    filename: State.filename,
                    exported: new Date().toISOString(),
                    score: State.reviewResults?.score,
                    grade: State.reviewResults?.grade,
                    issue_count: issuesToExport.length,
                    document_info: State.reviewResults?.document_info,
                    issues: issuesToExport,
                    filters_applied: (exportFilters.severities.length > 0 || exportFilters.categories.length > 0) ? exportFilters : null
                }, null, 2);
                const jsonBlob = new Blob([jsonData], { type: 'application/json' });
                downloadBlob(jsonBlob, `${State.filename}_review.json`);
                toast('success', `Exported ${issuesToExport.length} issues to JSON`);
                _hideExportProgress();
                return;
            }
            case 'docx':
            default:
                // v3.0.96: Get selected fixes from Fix Assistant if available
                let selectedFixes = [];
                let rejectedFixes = [];
                if (applyFixes && window.FixAssistant) {
                    selectedFixes = FixAssistant.getSelectedFixes();
                    // v5.9.4: Also get rejected fixes to add as comments
                    if (typeof FixAssistant.getRejectedFixes === 'function') {
                        rejectedFixes = FixAssistant.getRejectedFixes();
                    }
                }

                // v6.0.2: Review role mode determines how fixes are applied
                const reviewRole = (window.FixAssistantState && typeof FixAssistantState.getReviewRole === 'function')
                    ? FixAssistantState.getReviewRole()
                    : 'owner';

                endpoint = '/export';

                if (reviewRole === 'reviewer') {
                    // Reviewer mode: accepted fixes → recommendation comments (no text changes)
                    // Rejected fixes → skipped entirely (no action)
                    body = {
                        issues: issuesToExport.map((issue, i) => ({ ...issue, index: i })),
                        reviewer_name: reviewerName,
                        apply_fixes: false,
                        selected_fixes: [],
                        comment_only_issues: selectedFixes.map(f => ({
                            original_text: f.original_text || f.flagged_text || '',
                            suggestion: f.replacement_text || f.suggestion || '',
                            category: f.category || '',
                            paragraph_index: f.paragraph_index || 0,
                            reviewer_note: 'Reviewer recommendation: Accept this change'
                        })),
                        export_type: 'docx',
                        review_role: 'reviewer'
                    };
                } else {
                    // Owner mode (default): accepted → Track Changes, rejected → comments
                    body = {
                        issues: issuesToExport.map((issue, i) => ({ ...issue, index: i })),
                        reviewer_name: reviewerName,
                        apply_fixes: applyFixes && selectedFixes.length > 0,
                        selected_fixes: selectedFixes.map(f => ({
                            original_text: f.original_text || f.flagged_text || '',
                            replacement_text: f.replacement_text || f.suggestion || '',
                            category: f.category || '',
                            message: f.message || '',
                            paragraph_index: f.paragraph_index || 0
                        })),
                        comment_only_issues: rejectedFixes.map(f => ({
                            original_text: f.original_text || f.flagged_text || '',
                            suggestion: f.replacement_text || f.suggestion || '',
                            category: f.category || '',
                            paragraph_index: f.paragraph_index || 0,
                            reviewer_note: f.reviewer_note || f.note || ''
                        })),
                        export_type: 'docx',
                        review_role: 'owner'
                    };
                }
        }

        const response = await fetch(`/api${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': State.csrfToken
            },
            body: JSON.stringify(body)
        });

        if (response.ok) {
            const blob = await response.blob();
            // v5.9.2: Validate blob has content before downloading
            if (blob.size === 0) {
                toast('error', 'Export produced an empty file. The markup engine may need lxml installed.');
            } else {
                // v3.0.35: Get filename from Content-Disposition header if available
                const disposition = response.headers.get('Content-Disposition');
                let filename = `${State.filename}_review.${format === 'excel' ? 'xlsx' : format}`;
                if (disposition) {
                    const match = disposition.match(/filename="?([^";\n]+)"?/);
                    if (match) filename = match[1];
                }
                downloadBlob(blob, filename);
                toast('success', `Exported ${issuesToExport.length} issues to ${format.toUpperCase()}`);
            }
        } else {
            // v5.9.2: Safely parse error response (may not be JSON on 500)
            let errorMsg = 'Export failed';
            try {
                const error = await response.json();
                errorMsg = error.error || error.message || `Export failed (HTTP ${response.status})`;
            } catch (parseErr) {
                errorMsg = `Export failed with HTTP ${response.status}. Check server logs for details.`;
            }
            toast('error', errorMsg);
        }
    } catch (e) {
        console.error('[TWR] Export error:', e);
        toast('error', 'Export failed: ' + (e.message || 'Unknown error'));
    }

    _hideExportProgress();
}

// v5.0.2: Generate printable HTML report for PDF export via browser print
function generatePrintableReport(issues) {
    const severityColors = { critical: '#ef4444', high: '#ea580c', medium: '#ca8a04', low: '#16a34a', info: '#3b82f6' };
    const issueRows = issues.map(issue => {
        const sev = (issue.severity || 'info').toLowerCase();
        const color = severityColors[sev] || '#6b7280';
        return `<tr>
            <td><span style="background:${color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">${sev.toUpperCase()}</span></td>
            <td>${issue.category || '-'}</td>
            <td>${issue.message || '-'}</td>
            <td style="font-size:12px;color:#666;">${(issue.flagged_text || '').substring(0, 80)}${(issue.flagged_text || '').length > 80 ? '...' : ''}</td>
        </tr>`;
    }).join('');

    return `<!DOCTYPE html><html><head><meta charset="utf-8">
        <title>AEGIS Review Report</title>
        <style>
            body{font-family:'Segoe UI',Arial,sans-serif;margin:40px;color:#1a1a2e}
            h1{font-size:22px;margin-bottom:4px}
            .meta{color:#666;font-size:13px;margin-bottom:20px}
            .summary{display:flex;gap:24px;margin-bottom:24px}
            .stat{text-align:center;padding:12px 20px;background:#f8f9fa;border-radius:8px}
            .stat-val{font-size:28px;font-weight:700}.stat-lbl{font-size:11px;color:#666;text-transform:uppercase}
            table{width:100%;border-collapse:collapse;font-size:13px}
            th{background:#1a1a2e;color:#fff;padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase}
            td{padding:8px 12px;border-bottom:1px solid #e5e7eb;vertical-align:top}
            tr:nth-child(even){background:#f9fafb}
            @media print{body{margin:20px}.summary{page-break-inside:avoid}}
        </style>
    </head><body>
        <h1>AEGIS Document Review Report</h1>
        <p class="meta">${State.filename || 'Document'} &bull; ${new Date().toLocaleDateString()} &bull; ${issues.length} issues</p>
        <div class="summary">
            <div class="stat"><div class="stat-val">${State.reviewResults?.score ?? '-'}</div><div class="stat-lbl">Score</div></div>
            <div class="stat"><div class="stat-val">${State.reviewResults?.grade || '-'}</div><div class="stat-lbl">Grade</div></div>
            <div class="stat"><div class="stat-val">${issues.length}</div><div class="stat-lbl">Issues</div></div>
            <div class="stat"><div class="stat-val">${State.reviewResults?.word_count?.toLocaleString() || '-'}</div><div class="stat-lbl">Words</div></div>
        </div>
        <table><thead><tr><th>Severity</th><th>Category</th><th>Message</th><th>Flagged Text</th></tr></thead>
        <tbody>${issueRows}</tbody></table>
        <p style="margin-top:24px;font-size:11px;color:#999;">Generated by AEGIS</p>
    </body></html>`;
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ============================================================
// EXPORT FILTER PANEL (v5.9.4)
// ============================================================

/**
 * Populate severity and category filter chips in the export modal.
 * Called when the export modal opens.
 */
function _populateExportFilterChips() {
    const issues = State.issues || [];
    if (issues.length === 0) return;

    // Severity chips
    const sevContainer = document.getElementById('export-filter-severity-chips');
    if (sevContainer) {
        const sevCounts = {};
        issues.forEach(i => {
            const s = i.severity || 'Info';
            sevCounts[s] = (sevCounts[s] || 0) + 1;
        });

        sevContainer.innerHTML = '';
        ['Critical', 'High', 'Medium', 'Low', 'Info'].forEach(sev => {
            const count = sevCounts[sev] || 0;
            if (count === 0) return;
            const chip = document.createElement('span');
            chip.className = 'export-filter-chip';
            chip.dataset.severity = sev;
            chip.dataset.type = 'severity';
            chip.innerHTML = `${sev} <span class="chip-count">(${count})</span>`;
            chip.onclick = () => {
                chip.classList.toggle('active');
                _updateExportFilterPreview();
            };
            sevContainer.appendChild(chip);
        });
    }

    // Category chips
    const catContainer = document.getElementById('export-filter-category-chips');
    if (catContainer) {
        const catCounts = {};
        issues.forEach(i => {
            const c = i.category || 'Uncategorized';
            catCounts[c] = (catCounts[c] || 0) + 1;
        });

        // Sort by count descending
        const sortedCats = Object.entries(catCounts).sort((a, b) => b[1] - a[1]);

        catContainer.innerHTML = '';
        sortedCats.forEach(([cat, count]) => {
            const chip = document.createElement('span');
            chip.className = 'export-filter-chip';
            chip.dataset.category = cat;
            chip.dataset.type = 'category';
            chip.innerHTML = `${cat} <span class="chip-count">(${count})</span>`;
            chip.onclick = () => {
                chip.classList.toggle('active');
                _updateExportFilterPreview();
            };
            catContainer.appendChild(chip);
        });
    }

    // Reset filter panel state
    const panel = document.getElementById('export-filter-panel');
    if (panel) panel.classList.remove('expanded');
    const preview = document.getElementById('export-filter-preview');
    if (preview) preview.style.display = 'none';
}

/**
 * Toggle the export filter panel expanded/collapsed.
 */
function toggleExportFilterPanel() {
    const panel = document.getElementById('export-filter-panel');
    if (!panel) return;
    panel.classList.toggle('expanded');
    const toggleText = panel.querySelector('.export-filter-toggle span');
    if (toggleText) {
        toggleText.textContent = panel.classList.contains('expanded') ? 'Collapse' : 'Expand';
    }
}
window.toggleExportFilterPanel = toggleExportFilterPanel;

/**
 * Get currently active export filter selections.
 * @returns {{severities: string[], categories: string[]}}
 */
function _getExportFilters() {
    const severities = [];
    const categories = [];

    document.querySelectorAll('#export-filter-severity-chips .export-filter-chip.active').forEach(chip => {
        if (chip.dataset.severity) severities.push(chip.dataset.severity);
    });

    document.querySelectorAll('#export-filter-category-chips .export-filter-chip.active').forEach(chip => {
        if (chip.dataset.category) categories.push(chip.dataset.category);
    });

    return { severities, categories };
}

/**
 * Update the export filter preview count.
 */
function _updateExportFilterPreview() {
    const filters = _getExportFilters();
    const hasFilters = filters.severities.length > 0 || filters.categories.length > 0;
    const preview = document.getElementById('export-filter-preview');
    const countEl = document.getElementById('export-filter-count');

    if (!preview) return;

    if (!hasFilters) {
        preview.style.display = 'none';
        return;
    }

    // Count matching issues
    const mode = document.querySelector('input[name="export-mode"]:checked')?.value || 'all';
    let baseIssues;
    switch (mode) {
        case 'filtered': baseIssues = State.filteredIssues; break;
        case 'selected':
            baseIssues = (State.filteredIssues || []).filter((issue, i) => {
                const key = getIssueKey(issue, i);
                return State.selectedIssues?.has(key);
            });
            break;
        default: baseIssues = State.issues;
    }

    let filtered = baseIssues || [];
    if (filters.severities.length > 0) {
        filtered = filtered.filter(i => filters.severities.includes(i.severity || 'Info'));
    }
    if (filters.categories.length > 0) {
        filtered = filtered.filter(i => filters.categories.includes(i.category || ''));
    }

    if (countEl) countEl.textContent = filtered.length;
    preview.style.display = 'flex';
}

/**
 * Clear all export filter selections.
 */
function clearExportFilters() {
    document.querySelectorAll('.export-filter-chip.active').forEach(chip => {
        chip.classList.remove('active');
    });
    _updateExportFilterPreview();
}
window.clearExportFilters = clearExportFilters;

// ============================================================
// EXPORT PROGRESS OVERLAY (v5.9.4)
// ============================================================

/**
 * Show the export progress overlay with format-specific messaging.
 */
function _showExportProgress(format, issueCount) {
    const overlay = document.getElementById('export-progress-overlay');
    const title = document.getElementById('export-progress-title');
    const detail = document.getElementById('export-progress-detail');
    const barFill = document.getElementById('export-progress-bar-fill');

    if (!overlay) return;

    const formatLabels = {
        'docx': 'Word Document',
        'pdf': 'PDF Report',
        'xlsx': 'Excel Spreadsheet',
        'csv': 'CSV File',
        'json': 'JSON Data'
    };

    if (title) title.textContent = `Generating ${formatLabels[format] || format.toUpperCase()}...`;
    if (detail) detail.textContent = `Processing ${issueCount} issue${issueCount !== 1 ? 's' : ''}`;
    if (barFill) barFill.classList.remove('determinate');

    overlay.classList.add('active');
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/**
 * Hide the export progress overlay.
 */
function _hideExportProgress() {
    const overlay = document.getElementById('export-progress-overlay');
    if (overlay) overlay.classList.remove('active');
}

// ============================================================
// BASELINE
// ============================================================
async function toggleBaseline(index) {
    const issue = State.filteredIssues[index];
    if (!issue) return;

    if (!State.capabilities.database) {
        toast('info', 'Issue baseline requires database support. Enable the database in settings.');
        return;
    }

    if (!State.documentId) {
        toast('warning', 'Document must be saved to history before using baseline features');
        return;
    }

    try {
        // Create a hash of the issue for baseline matching
        const issueHash = btoa(JSON.stringify({
            category: issue.category,
            message: issue.message,
            flagged_text: issue.flagged_text?.substring(0, 100)
        })).substring(0, 32);

        const isBaselined = issue._baselined || false;
        
        if (isBaselined) {
            // Remove from baseline
            const result = await api('/baseline/remove', 'POST', {
                doc_id: State.documentId,
                issue_hash: issueHash
            });
            
            if (result.success) {
                issue._baselined = false;
                toast('success', 'Issue removed from baseline');
            }
        } else {
            // Add to baseline
            const result = await api('/baseline/add', 'POST', {
                doc_id: State.documentId,
                issue_hash: issueHash,
                issue_data: {
                    category: issue.category,
                    severity: issue.severity,
                    message: issue.message,
                    flagged_text: issue.flagged_text?.substring(0, 200)
                },
                reason: 'User accepted'
            });
            
            if (result.success) {
                issue._baselined = true;
                toast('success', 'Issue added to baseline - will be suppressed in future reviews');
            }
        }
        
        // Re-render the issue list to update the icon
        renderIssuesList();
        
    } catch (e) {
        toast('error', 'Failed to update baseline: ' + e.message);
    }
}

// ============================================================
// HISTORY
// ============================================================
async function saveToHistory(durationMs) {
    try {
        await api('/history/save', 'POST', {
            filepath: State.filepath,
            filename: State.filename,
            results: State.reviewResults,
            duration_ms: durationMs
        });
    } catch (e) {
        console.warn('[TWR] Failed to save to history:', e);
    }
}

// ============================================================
// SESSION STATE (Back Button Support)
// ============================================================
function saveSessionState() {
    try {
        const stateToSave = {
            filename: State.filename,
            filepath: State.filepath,
            reviewResults: State.reviewResults,
            issues: State.issues,
            roles: State.roles,
            documentId: State.documentId,
            timestamp: Date.now()
        };
        sessionStorage.setItem('twr_session_state', JSON.stringify(stateToSave));
        console.log('[TWR] Session state saved');
    } catch (e) {
        console.warn('[TWR] Could not save session state:', e);
    }
}

function restoreSessionState() {
    try {
        const saved = sessionStorage.getItem('twr_session_state');
        if (!saved) return false;
        
        const stateData = JSON.parse(saved);
        
        // Only restore if less than 30 minutes old
        if (Date.now() - stateData.timestamp > 30 * 60 * 1000) {
            sessionStorage.removeItem('twr_session_state');
            return false;
        }
        
        // Restore state
        State.filename = stateData.filename;
        State.filepath = stateData.filepath;
        State.reviewResults = stateData.reviewResults;
        State.issues = stateData.issues || [];
        State.filteredIssues = [...State.issues];
        State.roles = stateData.roles || {};
        State.documentId = stateData.documentId;

        // v3.0.111: Populate State.fixes for Fix Assistant (same logic as processReviewResults)
        State.fixes = (State.issues || []).filter(issue =>
            issue.suggestion &&
            issue.suggestion !== '-' &&
            issue.suggestion.trim() !== '' &&
            issue.flagged_text
        );
        console.log(`[TWR] Session restore: ${State.fixes.length} fixable issues identified`);

        // Restore UI
        if (State.reviewResults) {
            updateResultsUI(State.reviewResults);
            updateSeverityCounts(State.reviewResults.by_severity || {});
            updateValidationCounts(); // v3.0.29: Update validation filter counts
            updateCategoryFilters(State.reviewResults.by_category || {});
            renderIssuesList();
            
            // v3.0.13: Use analytics accordion and unified filter bar
            showAnalyticsAccordion(State.reviewResults);
            showUnifiedFilterBar(State.reviewResults);
            show('issues-container');
            hide('empty-state');  // v3.0.113: Hide empty state on session restore
            show('stats-bar');    // v4.0.2: Show stats bar on session restore
            
            if (Object.keys(State.roles).length > 0) {
                document.getElementById('roles-chart-card')?.style.setProperty('display', 'block');
                document.getElementById('btn-roles-report').disabled = false;
                renderRolesSummary();
            }
            
            document.getElementById('btn-export').disabled = false;
            
            // Update document info display
            const titleEl = document.getElementById('doc-title');
            if (titleEl) titleEl.textContent = State.filename || 'Document';
            
            toast('info', 'Previous session restored');
            console.log('[TWR] Session state restored');
            return true;
        }
    } catch (e) {
        console.warn('[TWR] Could not restore session state:', e);
    }
    return false;
}

function clearSessionState() {
    try {
        sessionStorage.removeItem('twr_session_state');
    } catch (e) { /* ignore */ }
}

// ============================================================
// SETTINGS (v3.0.46: Uses TWR.Storage for unified persistence)
// ============================================================
function loadSettings() {
    // v3.0.46: Try unified storage first, then fallback
    let saved = null;
    if (window.TWR?.Storage?.preferences) {
        saved = TWR.Storage.preferences.getAll();
    } else {
        const rawSaved = localStorage.getItem('twr_settings');
        if (rawSaved) {
            try {
                saved = JSON.parse(rawSaved);
            } catch (e) {
                console.warn('[TWR] Failed to parse settings:', e);
            }
        }
    }
    
    if (saved) {
        Object.assign(State.settings, saved);
        applySettings();
    }
}

function saveSettings() {
    // Gather all settings from form
    State.settings.autoReview = document.getElementById('settings-auto-review')?.checked || false;
    State.settings.reviewerName = document.getElementById('settings-reviewer')?.value || '';
    State.settings.rememberChecks = document.getElementById('settings-remember-checks')?.checked !== false;

    // Guide system toggle (v5.6.0)
    const guideEnabled = document.getElementById('settings-guide-enabled')?.checked !== false;
    if (window.AEGISGuide) {
        if (guideEnabled) window.AEGISGuide.enable();
        else window.AEGISGuide.disable();
    }
    State.settings.diagnosticsEmail = document.getElementById('settings-diagnostics-email')?.value || '';
    State.settings.maxSentenceLength = parseInt(document.getElementById('settings-max-sentence')?.value) || 40;
    State.settings.passiveThreshold = document.getElementById('settings-passive-threshold')?.value || 'moderate';
    State.settings.extractRoles = document.getElementById('settings-extract-roles')?.checked !== false;
    State.settings.hyperlinkMode = document.getElementById('settings-hyperlink-mode')?.value || 'offline';
    State.settings.pageSize = document.getElementById('settings-page-size')?.value || '50';
    State.settings.showCharts = document.getElementById('settings-show-charts')?.checked || false;
    State.settings.compactMode = document.getElementById('settings-compact-mode')?.checked || false;
    State.settings.essentialsMode = document.getElementById('settings-essentials-mode')?.checked || false;

    // Sharing settings
    const dictLocation = document.querySelector('input[name="dict-location"]:checked')?.value || 'local';
    State.settings.dictLocation = dictLocation;
    State.settings.sharedDictPath = document.getElementById('settings-shared-path')?.value || '';

    // Save shared path to server config
    if (dictLocation === 'shared' && State.settings.sharedDictPath) {
        saveSharedPathToServer(State.settings.sharedDictPath);
    } else if (dictLocation === 'local') {
        saveSharedPathToServer('');
    }

    // v3.0.46: Use unified storage if available
    if (window.TWR?.Storage?.preferences) {
        TWR.Storage.preferences.setAll(State.settings);
    } else {
        localStorage.setItem('twr_settings', JSON.stringify(State.settings));
    }

    // v4.8.0: Persist user preferences to backend via /api/config
    const backendSettings = {
        autoReview: State.settings.autoReview,
        reviewerName: State.settings.reviewerName,
        maxSentenceLength: State.settings.maxSentenceLength,
        passiveThreshold: State.settings.passiveThreshold,
        essentialsMode: State.settings.essentialsMode,
        pageSize: parseInt(State.settings.pageSize) || 50,
        showCharts: State.settings.showCharts,
        compactMode: State.settings.compactMode
    };

    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
        },
        body: JSON.stringify(backendSettings)
    }).then(resp => {
        if (!resp.ok) {
            console.warn('[TWR Settings] Failed to save settings to backend:', resp.status);
        }
    }).catch(err => {
        console.warn('[TWR Settings] Error posting to /api/config:', err);
    });

    applySettings();
    _settingsDirty = false;
    _updateSaveButtonState();
    closeModals();
    toast('success', 'Settings saved');
}

// v4.6.0: Settings dirty tracking
let _settingsDirty = false;
let _settingsTrackingInit = false;

function markSettingsDirty() {
    if (!_settingsDirty) {
        _settingsDirty = true;
        _updateSaveButtonState();
    }
}

function _updateSaveButtonState() {
    const btn = document.getElementById('btn-save-settings');
    if (!btn) return;
    if (_settingsDirty) {
        btn.classList.add('btn-pulse');
        btn.textContent = 'Save Settings *';
    } else {
        btn.classList.remove('btn-pulse');
        btn.textContent = 'Save Settings';
    }
}

function _initSettingsTracking() {
    if (_settingsTrackingInit) return;
    const modal = document.getElementById('modal-settings');
    if (!modal) return;
    _settingsTrackingInit = true;

    // Track changes on all inputs/selects within settings modal
    modal.addEventListener('change', (e) => {
        if (e.target.closest('.settings-content')) markSettingsDirty();
    });
    modal.addEventListener('input', (e) => {
        if (e.target.closest('.settings-content') && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
            markSettingsDirty();
        }
    });

    // Intercept Cancel / modal-close to warn about unsaved changes
    modal.querySelectorAll('.modal-close').forEach(btn => {
        const origHandler = btn.onclick;
        btn.onclick = function(e) {
            if (_settingsDirty) {
                if (!confirm('You have unsaved settings changes. Discard?')) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                _settingsDirty = false;
                _updateSaveButtonState();
            }
            if (origHandler) origHandler.call(this, e);
            else {
                const parentModal = this.closest('.modal');
                if (parentModal) {
                    parentModal.classList.remove('active');
                    if (!document.querySelector('.modal.active')) document.body.classList.remove('modal-open');
                }
            }
        };
    });
}

// Initialize tracking when settings modal opens
const _settingsModalObs = new MutationObserver((mutations) => {
    const modal = document.getElementById('modal-settings');
    if (modal?.classList.contains('active')) {
        _settingsDirty = false;
        _updateSaveButtonState();
        _initSettingsTracking();
    }
});
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modal-settings');
    if (modal) _settingsModalObs.observe(modal, { attributes: true, attributeFilter: ['class'] });
});

function applySettings() {
    document.body.classList.toggle('compact-mode', State.settings.compactMode);
    document.body.classList.toggle('dark-mode', State.settings.darkMode);
    document.body.classList.toggle('essentials-mode', State.settings.essentialsMode);
    
    // Update form values
    const autoReview = document.getElementById('settings-auto-review');
    if (autoReview) autoReview.checked = State.settings.autoReview;
    
    const showCharts = document.getElementById('settings-show-charts');
    if (showCharts) showCharts.checked = State.settings.showCharts;
    
    const compactMode = document.getElementById('settings-compact-mode');
    if (compactMode) compactMode.checked = State.settings.compactMode;
    
    const essentialsMode = document.getElementById('settings-essentials-mode');
    if (essentialsMode) essentialsMode.checked = State.settings.essentialsMode;
    
    const pageSize = document.getElementById('settings-page-size');
    if (pageSize) pageSize.value = State.settings.pageSize;

    // v3.0.109: Hyperlink validation mode
    const hyperlinkMode = document.getElementById('settings-hyperlink-mode');
    if (hyperlinkMode) hyperlinkMode.value = State.settings.hyperlinkMode || 'offline';

    // Save hyperlink mode to server config for backend use
    if (State.settings.hyperlinkMode) {
        saveHyperlinkModeToServer(State.settings.hyperlinkMode);
    }
}

/**
 * Save hyperlink validation mode to server config.
 * v3.0.109: Supports Windows SSO authentication in validator mode.
 */
async function saveHyperlinkModeToServer(mode) {
    try {
        const response = await fetch('/api/config/hyperlinks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ validation_mode: mode })
        });
        if (!response.ok) {
            console.warn('[TWR] Failed to save hyperlink mode to server');
        }
    } catch (e) {
        console.warn('[TWR] Error saving hyperlink mode:', e);
    }
}

function showSettingsModal() {
    showModal('modal-settings');
}

function switchSettingsTab(tabName) {
    // v5.9.3: Use class-based switching (no inline display styles — Lesson 2)
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-content').forEach(c => {
        c.classList.remove('active-tab');
        c.style.removeProperty('display'); // Clean up any legacy inline display
    });

    const activeTab = document.querySelector(`.settings-tab[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
        // v5.9.19: Scroll active tab into view
        activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
    const panel = document.getElementById(`settings-${tabName}`);
    if (panel) {
        panel.classList.add('active-tab');
        panel.style.removeProperty('display');
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// v5.9.19: Settings tabs scroll indicator — shows fade + arrow when tabs overflow
function _initSettingsTabsScroll() {
    const wrapper = document.getElementById('settings-tabs-wrapper');
    const tabs = document.getElementById('settings-tabs-scroll');
    const arrowLeft = document.getElementById('settings-arrow-left');
    const arrowRight = document.getElementById('settings-arrow-right');
    if (!wrapper || !tabs) return;

    function updateScrollIndicators() {
        const { scrollLeft, scrollWidth, clientWidth } = tabs;
        const canScrollLeft = scrollLeft > 2;
        const canScrollRight = scrollLeft + clientWidth < scrollWidth - 2;
        wrapper.classList.toggle('scroll-left', canScrollLeft);
        wrapper.classList.toggle('scroll-right', canScrollRight);
    }

    tabs.addEventListener('scroll', updateScrollIndicators);
    // Also check on resize
    window.addEventListener('resize', updateScrollIndicators);

    // Arrow button clicks
    if (arrowLeft) {
        arrowLeft.addEventListener('click', (e) => {
            e.stopPropagation();
            tabs.scrollBy({ left: -120, behavior: 'smooth' });
        });
    }
    if (arrowRight) {
        arrowRight.addEventListener('click', (e) => {
            e.stopPropagation();
            tabs.scrollBy({ left: 120, behavior: 'smooth' });
        });
    }

    // Initial check (delayed to let layout settle)
    requestAnimationFrame(updateScrollIndicators);
    // Also check when settings modal opens
    const obs = new MutationObserver(() => {
        const modal = document.getElementById('modal-settings');
        if (modal?.classList.contains('active')) {
            requestAnimationFrame(updateScrollIndicators);
        }
    });
    const settingsModal = document.getElementById('modal-settings');
    if (settingsModal) obs.observe(settingsModal, { attributes: true, attributeFilter: ['class'] });
}

document.addEventListener('DOMContentLoaded', _initSettingsTabsScroll);

// ============================================================
// HELP
// ============================================================
function showHelpModal() {
    showModal('modal-help');
}

function switchHelpTab(tabName) {
    document.querySelectorAll('.help-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.help-section').forEach(s => s.style.display = 'none');
    
    document.querySelector(`.help-tab[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`help-${tabName}`)?.style.setProperty('display', 'block');
}

// ============================================================
// PRESETS
// ============================================================
function applyPreset(preset) {
    const checkboxes = document.querySelectorAll('[data-checker]');

    // v3.0.110: Check for custom profiles first for document type presets
    const customizablePresets = ['prop', 'pal', 'fgost', 'sow'];
    if (customizablePresets.includes(preset) && typeof window.getCustomProfiles === 'function') {
        const profiles = window.getCustomProfiles();
        if (profiles[preset] && profiles[preset].checks) {
            checkboxes.forEach(cb => cb.checked = false);
            profiles[preset].checks.forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
            console.log(`[TWR] Applied custom profile: ${preset} (${profiles[preset].checks.length} checks)`);
            return;
        }
    }

    const presets = {
        all: () => checkboxes.forEach(cb => cb.checked = true),
        none: () => checkboxes.forEach(cb => cb.checked = false),
        reqs: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['passive_voice', 'weak_language', 'ambiguous_pronouns', 'requirements_language',
             'testability', 'atomicity', 'tbd', 'escape_clauses', 'acronyms'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        grammar: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['spelling', 'grammar', 'punctuation', 'capitalization', 'contractions',
             'sentence_length', 'repeated_words'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        technical: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['acronyms', 'requirements_language', 'units', 'terminology', 'references',
             'document_structure', 'tables_figures', 'mil_std', 'do178'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        // v2.9.4: Document type presets (fallback if no custom profile)
        prop: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['passive_voice', 'weak_language', 'requirements_language', 'roles',
             'document_structure', 'lists', 'orphan_headings', 'empty_sections',
             'ambiguous_pronouns', 'testability', 'atomicity'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        pal: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['spelling', 'grammar', 'punctuation', 'document_structure', 'references',
             'terminology', 'consistency', 'tables_figures', 'hyperlinks'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        fgost: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['requirements_language', 'tbd', 'roles', 'testability', 'atomicity',
             'escape_clauses', 'weak_language', 'ambiguous_pronouns', 'document_structure'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        },
        sow: () => {
            checkboxes.forEach(cb => cb.checked = false);
            ['requirements_language', 'passive_voice', 'weak_language', 'escape_clauses',
             'tbd', 'ambiguous_pronouns', 'testability', 'atomicity', 'roles',
             'acronyms', 'units', 'references'].forEach(c => {
                const el = document.querySelector(`[data-checker="${c}"]`);
                if (el) el.checked = true;
            });
        }
    };

    if (presets[preset]) presets[preset]();
}

// ============================================================
// SEVERITY / CATEGORY UI UPDATES
// ============================================================
function updateSeverityCounts(bySeverity) {
    Object.entries(bySeverity).forEach(([sev, count]) => {
        const el = document.getElementById(`count-${sev.toLowerCase()}`);
        if (el) el.textContent = count;
    });
}

/**
 * v3.0.29: Update validation filter counts
 * Called after review results are processed to show validated/unvalidated counts
 */
function updateValidationCounts() {
    let validated = 0;
    let unvalidated = 0;
    
    State.issues.forEach(issue => {
        if (issue?.source?.is_validated === true) {
            validated++;
        } else {
            unvalidated++;
        }
    });
    
    // Update count badges
    const validatedCountEl = document.getElementById('validation-count-validated');
    const unvalidatedCountEl = document.getElementById('validation-count-unvalidated');
    
    if (validatedCountEl) {
        validatedCountEl.textContent = validated;
        validatedCountEl.style.display = validated > 0 ? 'inline' : 'none';
    }
    if (unvalidatedCountEl) {
        unvalidatedCountEl.textContent = unvalidated;
        unvalidatedCountEl.style.display = unvalidated > 0 ? 'inline' : 'none';
    }
    
    // Update unified filter bar counts too
    const unifiedValidated = document.getElementById('unified-count-validated');
    const unifiedUnvalidated = document.getElementById('unified-count-unvalidated');
    if (unifiedValidated) unifiedValidated.textContent = validated;
    if (unifiedUnvalidated) unifiedUnvalidated.textContent = unvalidated;
    
    // Return counts for stats display
    return { validated, unvalidated, total: State.issues.length };
}

function updateCategoryFilters(byCategory) {
    // v5.9.3: Legacy containers (category-pinned, category-list) no longer exist.
    // Route to the unified category dropdown which has counts + click filtering.
    updateUnifiedCategoryDropdown(byCategory);
}

// ============================================================
// v3.0.13: ANALYTICS ACCORDION
// ============================================================

function showAnalyticsAccordion(data) {
    const accordion = document.getElementById('analytics-accordion');
    if (!accordion) return;
    
    // Show the accordion
    accordion.style.display = 'block';
    
    // Update inline stats summary
    const inlineStats = document.getElementById('analytics-inline-stats');
    if (inlineStats && data.by_severity) {
        const chips = [];
        const sevOrder = ['Critical', 'High', 'Medium', 'Low', 'Info'];
        for (const sev of sevOrder) {
            const count = data.by_severity[sev] || 0;
            if (count > 0 && sev !== 'Info') {
                chips.push(`<span class="stat-chip ${sev.toLowerCase()}">${count} ${sev}</span>`);
            }
        }
        if (chips.length === 0) {
            chips.push('<span class="stat-chip">No critical issues</span>');
        }
        inlineStats.innerHTML = chips.join('');
    }
    
    // Set initial expanded state based on settings
    if (State.settings.showCharts) {
        expandAnalytics();
    } else {
        collapseAnalytics();
    }
    
    // Render charts (they'll be visible when expanded)
    renderCharts(data);

    // v4.0.1: Render readability dashboard
    renderReadabilityDashboard(data);

    // v4.1.0: Render advanced analytics (hotspots, impact analyzer, correlation heatmap)
    renderAdvancedAnalytics(data);

    // v4.0.1: Show chart cards (were hidden in v3.0.49)
    document.getElementById('severity-chart-card')?.style.setProperty('display', 'block');
    document.getElementById('category-chart-card')?.style.setProperty('display', 'block');

    // Show roles if available
    if (Object.keys(State.roles).length > 0) {
        document.getElementById('roles-chart-card')?.style.setProperty('display', 'block');
        document.getElementById('btn-roles-report').disabled = false;
        renderRolesSummary();
    }
}

function expandAnalytics() {
    const accordion = document.getElementById('analytics-accordion');
    const body = document.getElementById('analytics-body');
    if (!accordion || !body) return;
    
    accordion.classList.add('expanded');
    body.style.display = 'flex';
    
    // Re-render charts when expanding (canvas might have been hidden)
    if (State.reviewResults) {
        setTimeout(() => renderCharts(State.reviewResults), 50);
    }
}

function collapseAnalytics() {
    const accordion = document.getElementById('analytics-accordion');
    const body = document.getElementById('analytics-body');
    if (!accordion || !body) return;
    
    accordion.classList.remove('expanded');
    body.style.display = 'none';
}

function toggleAnalytics() {
    const accordion = document.getElementById('analytics-accordion');
    if (!accordion) return;
    
    if (accordion.classList.contains('expanded')) {
        collapseAnalytics();
    } else {
        expandAnalytics();
    }
}

// ============================================================
// v4.0.1: READABILITY DASHBOARD
// ============================================================

function renderReadabilityDashboard(data) {
    const dashboard = document.getElementById('readability-dashboard');
    if (!dashboard) return;

    const readability = data.readability || {};

    // Check if we have readability data
    if (!readability.flesch_reading_ease && !readability.flesch_kincaid_grade) {
        dashboard.style.display = 'none';
        return;
    }

    dashboard.style.display = 'block';

    // Get values with fallbacks
    const flesch = readability.flesch_reading_ease ?? 0;
    const fog = readability.gunning_fog ?? readability.gunning_fog_index ?? 0;
    const grade = readability.flesch_kincaid_grade ?? 0;
    const ttr = readability.type_token_ratio ?? 0;

    // Update summary
    const summary = document.getElementById('readability-summary');
    if (summary) {
        const level = getReadabilityLevel(flesch);
        summary.textContent = level;
        summary.className = `readability-summary readability-${level.toLowerCase().replace(/\s+/g, '-')}`;
    }

    // Animate Flesch gauge (0-100 scale, higher is easier)
    animateGauge('flesch-arc', flesch, 100, true);
    updateGaugeText('flesch-value', flesch.toFixed(0));
    const fleschInterp = document.getElementById('flesch-interpretation');
    if (fleschInterp) {
        fleschInterp.textContent = getFleschInterpretation(flesch);
    }

    // Animate Gunning Fog gauge (typically 6-20, lower is easier)
    // Normalize to 0-100 where lower fog = higher score
    const fogNormalized = Math.max(0, Math.min(100, (20 - fog) * 7.14));
    animateGauge('fog-arc', fogNormalized, 100);
    updateGaugeText('fog-value', fog.toFixed(1));
    const fogInterp = document.getElementById('fog-interpretation');
    if (fogInterp) {
        fogInterp.textContent = `Grade Level: ${Math.round(fog)}`;
    }

    // Animate Grade Level gauge (typically 1-20)
    const gradeNormalized = Math.max(0, Math.min(100, grade * 5));
    animateGauge('grade-arc', gradeNormalized, 100);
    updateGaugeText('grade-value', grade.toFixed(1));
    const gradeInterp = document.getElementById('grade-interpretation');
    if (gradeInterp) {
        gradeInterp.textContent = getGradeInterpretation(grade);
    }

    // Animate Vocabulary (TTR typically 0-1, higher is more varied)
    const vocabNormalized = (ttr || 0.5) * 100;
    animateGauge('vocab-arc', vocabNormalized, 100);
    updateGaugeText('vocab-value', (ttr * 100).toFixed(0) + '%');
    const vocabInterp = document.getElementById('vocab-interpretation');
    if (vocabInterp) {
        vocabInterp.textContent = ttr > 0.5 ? 'Rich vocabulary' : ttr > 0.3 ? 'Moderate variety' : 'Limited variety';
    }

    // Update recommendation
    const recommendation = document.getElementById('readability-recommendation-text');
    if (recommendation) {
        recommendation.textContent = getReadabilityRecommendation(flesch, grade, fog);
    }
}

function animateGauge(arcId, value, max, reverse = false) {
    const arc = document.getElementById(arcId);
    if (!arc) return;

    // The arc path length is approximately 157 (half circle with radius 50)
    const arcLength = 157;
    const normalizedValue = Math.max(0, Math.min(1, value / max));
    const dashLength = normalizedValue * arcLength;

    // Animate using CSS transition (defined in CSS)
    arc.style.strokeDasharray = `${dashLength} ${arcLength}`;

    // Update color based on value
    const color = getGaugeColor(normalizedValue, reverse);
    arc.style.stroke = color;
}

function updateGaugeText(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = value;
}

function getGaugeColor(normalized, reverse = false) {
    const value = reverse ? normalized : 1 - normalized;
    if (value >= 0.7) return '#10b981'; // Green
    if (value >= 0.5) return '#f59e0b'; // Yellow
    if (value >= 0.3) return '#f97316'; // Orange
    return '#ef4444'; // Red
}

function getReadabilityLevel(flesch) {
    if (flesch >= 90) return 'Very Easy';
    if (flesch >= 80) return 'Easy';
    if (flesch >= 70) return 'Fairly Easy';
    if (flesch >= 60) return 'Standard';
    if (flesch >= 50) return 'Fairly Difficult';
    if (flesch >= 30) return 'Difficult';
    return 'Very Difficult';
}

function getFleschInterpretation(flesch) {
    if (flesch >= 90) return '5th grade';
    if (flesch >= 80) return '6th grade';
    if (flesch >= 70) return '7th grade';
    if (flesch >= 60) return '8th-9th grade';
    if (flesch >= 50) return '10th-12th grade';
    if (flesch >= 30) return 'College level';
    return 'Graduate level';
}

function getGradeInterpretation(grade) {
    if (grade <= 6) return 'Elementary';
    if (grade <= 8) return 'Middle school';
    if (grade <= 12) return 'High school';
    if (grade <= 16) return 'College';
    return 'Graduate';
}

function getReadabilityRecommendation(flesch, grade, fog) {
    if (flesch >= 60 && grade <= 14) {
        return '✓ Good readability for professional technical documents';
    }
    if (flesch < 30) {
        return '⚠ Consider simplifying: use shorter sentences and more common words';
    }
    if (grade > 16) {
        return '⚠ High complexity - aim for grade 12-16 for technical documents';
    }
    if (fog > 16) {
        return '⚠ Reduce jargon and shorten sentences for better clarity';
    }
    return '✓ Acceptable readability for technical audience';
}

// ============================================================
// v4.0.1: CHECKER CORRELATION HEATMAP
// ============================================================

function renderCheckerCorrelationHeatmap(data) {
    const container = document.getElementById('checker-correlation-container');
    const heatmapEl = document.getElementById('correlation-heatmap');
    if (!container || !heatmapEl) return;

    const issues = State.issues || [];
    if (issues.length < 10) {
        container.style.display = 'none';
        return;
    }

    // Calculate co-occurrence of categories
    const categories = {};
    const coOccurrence = {};  // Only off-diagonal pairs
    const selfCounts = {};    // Diagonal (self) counts

    // Group issues by their location (paragraph_index)
    // v4.0.2: Fixed to use correct field name 'paragraph_index' instead of 'paragraph'/'line'
    const locationGroups = {};
    issues.forEach(issue => {
        const location = issue.paragraph_index ?? issue.paragraph ?? issue.line ?? 'unknown';
        if (!locationGroups[location]) locationGroups[location] = [];
        locationGroups[location].push(issue.category || 'Other');
    });

    // v4.0.3: Improved correlation calculation
    // Only count TRUE co-occurrences (different categories in same location)
    // Diagonal shows total category count, off-diagonal shows co-occurrence
    Object.values(locationGroups).forEach(group => {
        const uniqueCats = [...new Set(group)];

        // Count each category occurrence
        uniqueCats.forEach(cat => {
            categories[cat] = (categories[cat] || 0) + 1;
            selfCounts[cat] = (selfCounts[cat] || 0) + 1;
        });

        // Count pairs - only DIFFERENT categories (true co-occurrence)
        for (let i = 0; i < uniqueCats.length; i++) {
            for (let j = i + 1; j < uniqueCats.length; j++) {  // j = i+1 to skip diagonal
                const key = [uniqueCats[i], uniqueCats[j]].sort().join('|');
                coOccurrence[key] = (coOccurrence[key] || 0) + 1;
            }
        }
    });

    // Get top categories (limit to 8 for readability)
    const topCategories = Object.entries(categories)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(e => e[0]);

    if (topCategories.length < 3) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    // Calculate max for normalization - only off-diagonal for proper scaling
    let maxCoOcc = 1;  // Minimum 1 to avoid division by zero
    topCategories.forEach(cat1 => {
        topCategories.forEach(cat2 => {
            if (cat1 !== cat2) {
                const key = [cat1, cat2].sort().join('|');
                maxCoOcc = Math.max(maxCoOcc, coOccurrence[key] || 0);
            }
        });
    });

    // Build SVG heatmap
    const cellSize = 45;
    const labelWidth = 100;
    const labelHeight = 80;
    const width = labelWidth + (topCategories.length * cellSize);
    const height = labelHeight + (topCategories.length * cellSize);

    const isDarkMode = document.body.classList.contains('dark-mode');
    const colors = isDarkMode
        ? ['#374151', '#1e3a5f', '#1e40af', '#2563eb']
        : ['#f3f4f6', '#dbeafe', '#93c5fd', '#3b82f6'];

    let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;

    // Column labels (rotated)
    topCategories.forEach((cat, i) => {
        const x = labelWidth + (i * cellSize) + cellSize / 2;
        const y = labelHeight - 5;
        const label = cat.length > 12 ? cat.substring(0, 12) + '…' : cat;
        svg += `<text x="${x}" y="${y}" text-anchor="start" font-size="10" fill="${isDarkMode ? '#9ca3af' : '#6b7280'}" transform="rotate(-45 ${x} ${y})">${label}</text>`;
    });

    // Row labels and cells
    topCategories.forEach((cat1, row) => {
        // Row label
        const y = labelHeight + (row * cellSize) + cellSize / 2 + 4;
        const label = cat1.length > 12 ? cat1.substring(0, 12) + '…' : cat1;
        svg += `<text x="${labelWidth - 5}" y="${y}" text-anchor="end" font-size="10" fill="${isDarkMode ? '#9ca3af' : '#6b7280'}">${label}</text>`;

        // Cells
        topCategories.forEach((cat2, col) => {
            const x = labelWidth + (col * cellSize);
            const cellY = labelHeight + (row * cellSize);
            const isDiagonal = cat1 === cat2;

            // v4.0.3: Different handling for diagonal vs off-diagonal
            let value, normalized, color, colorIndex;
            if (isDiagonal) {
                // Diagonal shows total count for this category
                value = selfCounts[cat1] || 0;
                // Use a distinct color for diagonal (gray/neutral)
                color = isDarkMode ? '#4b5563' : '#d1d5db';
                colorIndex = -1;  // Special marker for diagonal
            } else {
                // Off-diagonal shows co-occurrence count
                const key = [cat1, cat2].sort().join('|');
                value = coOccurrence[key] || 0;
                normalized = maxCoOcc > 0 ? value / maxCoOcc : 0;
                colorIndex = normalized === 0 ? 0 : normalized < 0.33 ? 1 : normalized < 0.66 ? 2 : 3;
                color = colors[colorIndex];
            }

            svg += `<rect class="correlation-cell" x="${x + 2}" y="${cellY + 2}" width="${cellSize - 4}" height="${cellSize - 4}" fill="${color}" rx="4" data-cat1="${cat1}" data-cat2="${cat2}" data-value="${value}" data-diagonal="${isDiagonal}"/>`;

            // Show value if > 0
            if (value > 0) {
                const textColor = isDiagonal
                    ? (isDarkMode ? '#e5e7eb' : '#374151')
                    : (colorIndex >= 2 ? '#fff' : (isDarkMode ? '#e5e7eb' : '#374151'));
                svg += `<text x="${x + cellSize / 2}" y="${cellY + cellSize / 2 + 4}" text-anchor="middle" font-size="11" font-weight="500" fill="${textColor}">${value}</text>`;
            }
        });
    });

    svg += '</svg>';
    heatmapEl.innerHTML = svg;

    // Add hover interaction
    const cells = heatmapEl.querySelectorAll('.correlation-cell');
    const insights = document.getElementById('correlation-insights');

    cells.forEach(cell => {
        cell.addEventListener('mouseenter', (e) => {
            const cat1 = e.target.dataset.cat1;
            const cat2 = e.target.dataset.cat2;
            const value = e.target.dataset.value;
            if (insights) {
                if (cat1 === cat2) {
                    insights.innerHTML = `<i data-lucide="info"></i><span><strong>${cat1}</strong>: ${value} issues total</span>`;
                } else {
                    insights.innerHTML = `<i data-lucide="link"></i><span><strong>${cat1}</strong> + <strong>${cat2}</strong>: appear together in ${value} locations</span>`;
                }
                lucide.createIcons({ icons: { info: lucide.icons.info, link: lucide.icons.link }, attrs: { 'stroke-width': 2 } });
            }
        });
        cell.addEventListener('mouseleave', () => {
            if (insights) {
                insights.innerHTML = '<i data-lucide="info"></i><span>Hover over cells to see details</span>';
                lucide.createIcons({ icons: { info: lucide.icons.info }, attrs: { 'stroke-width': 2 } });
            }
        });
    });
}

// ============================================================
// v4.1.0: ADVANCED ANALYTICS PANEL
// ============================================================

/**
 * Render the Issue Hotspot Flow visualization
 * Shows where issues cluster in the document by section/paragraph
 */
/**
 * Render Premium Issue Hotspots Visualization (v4.2.0)
 * Beautiful animated stacked bar chart with full interactivity
 */
function renderHotspotFlow(data) {
    const container = document.getElementById('advanced-analytics-panel');
    const svg = document.getElementById('hotspot-flow-svg');
    const insight = document.getElementById('hotspot-insight');
    const legend = document.getElementById('hotspot-legend');

    if (!container || !svg) return;

    const issues = State.issues || [];
    if (issues.length < 5) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    // Group issues by paragraph/section into bins
    const totalParagraphs = Math.max(...issues.map(i => i.paragraph_index || 0), 1);
    const binCount = Math.min(12, Math.max(6, Math.ceil(totalParagraphs / 8)));
    const binSize = Math.ceil(totalParagraphs / binCount);

    // Initialize bins with severity counts
    const bins = Array.from({ length: binCount }, (_, i) => ({
        index: i,
        start: i * binSize,
        end: Math.min((i + 1) * binSize, totalParagraphs),
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        total: 0,
        issues: []
    }));

    // Populate bins
    issues.forEach(issue => {
        const paraIdx = issue.paragraph_index || 0;
        const binIdx = Math.min(Math.floor(paraIdx / binSize), binCount - 1);
        const sev = (issue.severity || 'Low').toLowerCase();

        if (bins[binIdx]) {
            bins[binIdx][sev] = (bins[binIdx][sev] || 0) + 1;
            bins[binIdx].total++;
            bins[binIdx].issues.push(issue);
        }
    });

    // Find max for scaling
    const maxTotal = Math.max(...bins.map(b => b.total), 1);
    const hotspotBin = bins.reduce((max, bin) => bin.total > max.total ? bin : max, bins[0]);

    // SVG dimensions - premium sizing
    const width = 450;
    const height = 200;
    const padding = { top: 25, right: 25, bottom: 35, left: 45 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const barGap = 6;
    const barWidth = (chartWidth / binCount) - barGap;

    const isDarkMode = document.body.classList.contains('dark-mode');

    // Premium gradient colors with glow
    const colors = {
        critical: { main: '#ef4444', gradient: ['#f87171', '#dc2626'] },
        high: { main: '#f97316', gradient: ['#fb923c', '#ea580c'] },
        medium: { main: '#eab308', gradient: ['#facc15', '#ca8a04'] },
        low: { main: '#22c55e', gradient: ['#4ade80', '#16a34a'] }
    };

    // Build premium SVG
    let svgContent = `
        <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
        <defs>
            <!-- Gradient definitions -->
            <linearGradient id="grad-critical" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:${colors.critical.gradient[0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:${colors.critical.gradient[1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad-high" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:${colors.high.gradient[0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:${colors.high.gradient[1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad-medium" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:${colors.medium.gradient[0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:${colors.medium.gradient[1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad-low" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:${colors.low.gradient[0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:${colors.low.gradient[1]};stop-opacity:1" />
            </linearGradient>
            <!-- Glow filter -->
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <!-- Shadow filter -->
            <filter id="barShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.15"/>
            </filter>
        </defs>

        <!-- Background grid lines -->
        <g class="grid-lines" opacity="0.3">`;

    // Draw subtle grid lines
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        svgContent += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${isDarkMode ? '#374151' : '#e5e7eb'}" stroke-width="1"/>`;
    }

    svgContent += `</g>`;

    // Y-axis with animated appearance
    const yAxisValues = [0, Math.round(maxTotal * 0.5), maxTotal];
    yAxisValues.forEach((val, i) => {
        const y = height - padding.bottom - (val / maxTotal) * chartHeight;
        svgContent += `<text x="${padding.left - 10}" y="${y + 3}" font-size="10" font-weight="500" fill="${isDarkMode ? '#9ca3af' : '#6b7280'}" text-anchor="end" opacity="0.8">${val}</text>`;
    });

    // Draw stacked bars with premium styling
    bins.forEach((bin, i) => {
        const x = padding.left + i * (barWidth + barGap) + barGap / 2;
        const isHotspot = bin === hotspotBin;
        const animDelay = i * 0.05;

        // Stack the severities from bottom to top
        let yOffset = height - padding.bottom;

        ['low', 'medium', 'high', 'critical'].forEach(sev => {
            const count = bin[sev] || 0;
            if (count > 0) {
                const barHeight = Math.max(2, (count / maxTotal) * chartHeight);
                yOffset -= barHeight;

                svgContent += `
                    <rect
                        class="hotspot-bar hotspot-bar-animated"
                        x="${x}"
                        y="${yOffset}"
                        width="${barWidth}"
                        height="${barHeight}"
                        fill="url(#grad-${sev})"
                        rx="3"
                        ry="3"
                        data-bin="${i}"
                        data-severity="${sev}"
                        data-count="${count}"
                        data-total="${bin.total}"
                        data-start="${bin.start}"
                        data-end="${bin.end}"
                        filter="${isHotspot ? 'url(#glow)' : 'url(#barShadow)'}"
                        style="animation-delay: ${animDelay}s; cursor: pointer;"
                    />`;
            }
        });

        // Total count label above bar (for significant bars)
        if (bin.total > maxTotal * 0.3) {
            const topY = height - padding.bottom - (bin.total / maxTotal) * chartHeight - 8;
            svgContent += `<text x="${x + barWidth/2}" y="${topY}" font-size="10" font-weight="600" fill="${isDarkMode ? '#e5e7eb' : '#374151'}" text-anchor="middle">${bin.total}</text>`;
        }

        // X-axis labels
        const showLabel = i === 0 || i === binCount - 1 || i === Math.floor(binCount / 2) || isHotspot;
        if (showLabel) {
            const label = i === 0 ? 'Start' : i === binCount - 1 ? 'End' : `§${i + 1}`;
            svgContent += `<text x="${x + barWidth/2}" y="${height - padding.bottom + 18}" font-size="10" font-weight="${isHotspot ? '700' : '500'}" fill="${isHotspot ? colors.critical.main : (isDarkMode ? '#9ca3af' : '#6b7280')}" text-anchor="middle">${label}</text>`;
        }
    });

    // Hotspot threshold line with glow
    const hotspotThreshold = maxTotal * 0.7;
    const hotspotY = padding.top + chartHeight - (hotspotThreshold / maxTotal) * chartHeight;
    svgContent += `
        <line x1="${padding.left}" y1="${hotspotY}" x2="${width - padding.right}" y2="${hotspotY}"
              stroke="${isDarkMode ? '#f87171' : '#ef4444'}" stroke-width="1.5" stroke-dasharray="6,4" opacity="0.6"/>
        <text x="${width - padding.right - 5}" y="${hotspotY - 6}" font-size="9" font-weight="600" fill="${isDarkMode ? '#f87171' : '#ef4444'}" text-anchor="end">
            <tspan>⚠️ Hotspot Zone</tspan>
        </text>`;

    svgContent += '</svg>';
    svg.innerHTML = svgContent;

    // Premium interactivity
    const bars = svg.querySelectorAll('.hotspot-bar');
    let activeFilter = null;

    bars.forEach(bar => {
        bar.addEventListener('mouseenter', (e) => {
            e.target.style.filter = 'url(#glow) brightness(1.1)';
            e.target.style.transform = 'translateY(-2px)';

            const start = e.target.dataset.start;
            const end = e.target.dataset.end;
            const total = e.target.dataset.total;
            const sev = e.target.dataset.severity;
            const sevLabel = sev.charAt(0).toUpperCase() + sev.slice(1);

            if (insight) {
                insight.innerHTML = `<i data-lucide="crosshair"></i><span>§${parseInt(start/binSize)+1}: <strong>${total} issues</strong> • ${sevLabel}: ${e.target.dataset.count}</span>`;
                lucide.createIcons({ icons: { 'crosshair': lucide.icons['crosshair'] }, attrs: { 'stroke-width': 2 } });
            }
        });

        bar.addEventListener('mouseleave', (e) => {
            const isHotspot = parseInt(e.target.dataset.total) === hotspotBin.total;
            e.target.style.filter = isHotspot ? 'url(#glow)' : 'url(#barShadow)';
            e.target.style.transform = '';
            updateHotspotInsight();
        });

        bar.addEventListener('click', (e) => {
            const binIdx = parseInt(e.target.dataset.bin);
            const start = parseInt(e.target.dataset.start);
            const end = parseInt(e.target.dataset.end);
            const sev = e.target.dataset.severity;

            // Toggle active state
            bars.forEach(b => b.classList.remove('active'));

            if (activeFilter && activeFilter.bin === binIdx && activeFilter.sev === sev) {
                // Clear filter
                activeFilter = null;
                clearCustomFilter();
                showNotification('Filter cleared', 'info');
            } else {
                // Apply filter
                e.target.classList.add('active');
                activeFilter = { bin: binIdx, sev: sev };
                filterIssuesByParagraphRange(start, end, sev);
            }
        });
    });

    // Make legend items interactive
    if (legend) {
        legend.querySelectorAll('.legend-item').forEach(item => {
            const dot = item.querySelector('.legend-dot');
            const sev = dot?.classList.contains('critical') ? 'critical' :
                        dot?.classList.contains('high') ? 'high' :
                        dot?.classList.contains('medium') ? 'medium' : 'low';

            item.addEventListener('click', () => {
                // Filter by this severity across all bins
                const sevIssues = issues.filter(i => (i.severity || 'low').toLowerCase() === sev);
                if (sevIssues.length > 0) {
                    legend.querySelectorAll('.legend-item').forEach(li => li.classList.remove('active'));
                    item.classList.add('active');
                    filterIssuesBySeverity(sev);
                }
            });
        });
    }

    // Update insight with hotspot info
    function updateHotspotInsight() {
        if (insight && hotspotBin.total > 0) {
            const hotspotPercent = Math.round((hotspotBin.total / issues.length) * 100);
            insight.innerHTML = `<i data-lucide="flame"></i><span><strong>Hotspot:</strong> Section ${hotspotBin.index + 1} has ${hotspotPercent}% of all issues • Click to filter</span>`;
            lucide.createIcons({ icons: { flame: lucide.icons.flame }, attrs: { 'stroke-width': 2 } });
        }
    }
    updateHotspotInsight();
}

/**
 * Filter issues by paragraph range (for hotspot click)
 * @param {number} start - Start paragraph index
 * @param {number} end - End paragraph index
 * @param {string} [severity] - Optional severity filter
 */
function filterIssuesByParagraphRange(start, end, severity = null) {
    State.filters = State.filters || {};
    State.filters.customFilter = (issue) => {
        const idx = issue.paragraph_index || 0;
        const inRange = idx >= start && idx <= end;
        if (severity) {
            return inRange && (issue.severity || 'low').toLowerCase() === severity;
        }
        return inRange;
    };

    const sevLabel = severity ? ` (${severity})` : '';
    State.filters.customFilterLabel = `Section §${Math.floor(start / 10) + 1}${sevLabel}`;

    applyFilters();
    updateUnifiedFilterChips();

    const count = State.filteredIssues.length;
    showNotification(`Showing ${count} issues in section${sevLabel}`, 'info');
}

/**
 * Filter issues by severity (for legend click)
 */
function filterIssuesBySeverity(severity) {
    State.filters = State.filters || {};
    State.filters.customFilter = (issue) => {
        return (issue.severity || 'low').toLowerCase() === severity;
    };
    State.filters.customFilterLabel = `${severity.charAt(0).toUpperCase() + severity.slice(1)} severity`;

    applyFilters();
    updateUnifiedFilterChips();

    const count = State.filteredIssues.length;
    showNotification(`Showing ${count} ${severity} issues`, 'info');
}

/**
 * Clear custom filter
 */
function clearCustomFilter() {
    if (State.filters) {
        delete State.filters.customFilter;
        delete State.filters.customFilterLabel;
    }
    applyFilters();
    updateUnifiedFilterChips();
}

/**
 * Render Premium Fix Impact Analyzer (v4.2.0)
 * Animated score gauges with visual impact indicators and interactive fix list
 */
function renderFixImpactAnalyzer(data) {
    const container = document.getElementById('impact-analyzer-container');
    const currentScoreEl = document.getElementById('current-score-value');
    const projectedScoreEl = document.getElementById('projected-score-value');
    const currentGaugeFill = document.getElementById('current-gauge-fill');
    const projectedGaugeFill = document.getElementById('projected-gauge-fill');
    const improvementEl = document.getElementById('score-improvement');
    const topFixesList = document.getElementById('top-fixes-list');
    const insightEl = document.getElementById('impact-insight-text');

    if (!container || !topFixesList) return;

    const issues = State.issues || [];
    const currentScore = data?.score ?? State.lastScanData?.score ?? 0;

    // Calculate fixable issues and their impact
    const fixableIssues = issues.filter(i => i.is_fixable || i.original_text);

    // Weight by severity for impact calculation
    const severityWeights = { critical: 4, high: 3, medium: 2, low: 1 };

    // Calculate projected score improvement
    const totalWeight = issues.reduce((sum, i) => {
        const sev = (i.severity || 'low').toLowerCase();
        return sum + (severityWeights[sev] || 1);
    }, 0);

    const fixableWeight = fixableIssues.reduce((sum, i) => {
        const sev = (i.severity || 'low').toLowerCase();
        return sum + (severityWeights[sev] || 1);
    }, 0);

    // Project score improvement
    const potentialImprovement = totalWeight > 0 ? Math.min(20, Math.round((fixableWeight / totalWeight) * 25)) : 0;
    const projectedScore = Math.min(100, currentScore + potentialImprovement);

    // Animate score gauges
    const circumference = 2 * Math.PI * 42; // r=42

    // Update current score gauge with animation
    if (currentScoreEl) currentScoreEl.textContent = currentScore;
    if (currentGaugeFill) {
        const currentDash = (currentScore / 100) * circumference;
        setTimeout(() => {
            currentGaugeFill.style.strokeDasharray = `${currentDash} ${circumference}`;
        }, 100);
    }

    // Update projected score gauge with animation (delayed for effect)
    if (projectedScoreEl) projectedScoreEl.textContent = projectedScore;
    if (projectedGaugeFill) {
        const projectedDash = (projectedScore / 100) * circumference;
        setTimeout(() => {
            projectedGaugeFill.style.strokeDasharray = `${projectedDash} ${circumference}`;
        }, 400);
    }

    // Update improvement badge
    if (improvementEl) {
        improvementEl.textContent = potentialImprovement > 0 ? `+${potentialImprovement}` : '—';
        improvementEl.style.opacity = potentialImprovement > 0 ? '1' : '0.5';
    }

    // Apply color classes based on score
    const getGaugeColor = (score) => {
        if (score >= 80) return '#22c55e';
        if (score >= 60) return '#eab308';
        if (score >= 40) return '#f97316';
        return '#ef4444';
    };

    if (currentGaugeFill) currentGaugeFill.style.stroke = getGaugeColor(currentScore);
    if (projectedGaugeFill) projectedGaugeFill.style.stroke = getGaugeColor(projectedScore);

    // Get top impact issues (sorted by severity weight)
    // Include all high-severity issues, not just auto-fixable ones
    const topFixes = [...issues]
        .map((issue, originalIndex) => ({
            ...issue,
            originalIndex: originalIndex,
            impactWeight: severityWeights[(issue.severity || 'low').toLowerCase()] || 1
        }))
        .sort((a, b) => b.impactWeight - a.impactWeight)
        .slice(0, 5);

    // Render top fixes list
    if (topFixes.length === 0) {
        topFixesList.innerHTML = '<div class="no-fixes">No issues found</div>';
    } else {
        topFixesList.innerHTML = topFixes.map((fix, idx) => {
            const sev = (fix.severity || 'Low').toLowerCase();
            const category = fix.category || 'Other';
            const message = truncate(fix.message || 'Issue', 45);
            const impact = fix.impactWeight;

            return `
                <div class="fix-item" data-index="${idx}" data-issue-index="${fix.originalIndex}">
                    <div class="fix-priority">
                        <span class="priority-badge ${sev}">${idx + 1}</span>
                    </div>
                    <div class="fix-details">
                        <span class="fix-category">${escapeHtml(category)}</span>
                        <span class="fix-message">${escapeHtml(message)}</span>
                    </div>
                    <div class="fix-impact">
                        <span class="impact-dots">${'●'.repeat(impact)}${'○'.repeat(4 - impact)}</span>
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers to jump to issue and expand it
        topFixesList.querySelectorAll('.fix-item').forEach((item, fixIdx) => {
            item.addEventListener('click', () => {
                const issueIndex = parseInt(item.dataset.issueIndex);
                if (isNaN(issueIndex) || issueIndex < 0) {
                    console.warn('Invalid issue index:', item.dataset.issueIndex);
                    return;
                }

                // Visual feedback immediately
                topFixesList.querySelectorAll('.fix-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');

                // Get the target issue from our stored topFixes
                const targetIssue = topFixes[fixIdx];
                if (!targetIssue) {
                    console.warn('Could not find issue at index:', fixIdx);
                    return;
                }

                // Clear any custom filters first
                if (typeof clearCustomFilter === 'function') {
                    clearCustomFilter();
                }

                // Clear search filter
                const searchInput = document.getElementById('issue-search');
                if (searchInput && searchInput.value) {
                    searchInput.value = '';
                    if (typeof filterIssues === 'function') filterIssues();
                }

                // Find position in filtered issues and navigate to correct page
                const filteredIndex = State.filteredIssues.findIndex(i =>
                    i === targetIssue ||
                    (i.message === targetIssue.message &&
                     i.paragraph_index === targetIssue.paragraph_index &&
                     i.category === targetIssue.category)
                );

                if (filteredIndex >= 0) {
                    // Calculate which page this issue is on
                    const pageSize = State.settings.pageSize === 'all' ? State.filteredIssues.length : parseInt(State.settings.pageSize) || 50;
                    const targetPage = Math.floor(filteredIndex / pageSize) + 1;

                    // Navigate to correct page if needed
                    if (State.currentPage !== targetPage) {
                        State.currentPage = targetPage;
                        if (typeof renderIssuesList === 'function') {
                            renderIssuesList();
                        } else if (typeof TWR?.Renderers?.renderIssuesList === 'function') {
                            TWR.Renderers.renderIssuesList();
                        }
                    }

                    // Wait for DOM update then scroll to issue
                    setTimeout(() => {
                        const indexOnPage = filteredIndex % pageSize;
                        const issueRows = document.querySelectorAll('.issue-row');
                        const targetRow = issueRows[indexOnPage];

                        if (targetRow) {
                            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            targetRow.classList.add('highlight-pulse');
                            setTimeout(() => targetRow.classList.remove('highlight-pulse'), 2500);

                            // Auto-expand the issue
                            if (!targetRow.classList.contains('expanded')) {
                                const expandBtn = targetRow.querySelector('.expand-toggle, .issue-expand-btn');
                                if (expandBtn) {
                                    expandBtn.click();
                                } else if (typeof toggleIssueExpand === 'function') {
                                    toggleIssueExpand(filteredIndex);
                                }
                            }
                        }
                    }, 100);
                }
            });
        });
    }

    // Update insight
    if (insightEl) {
        const criticalCount = issues.filter(i => (i.severity || '').toLowerCase() === 'critical').length;
        const highCount = issues.filter(i => (i.severity || '').toLowerCase() === 'high').length;

        if (criticalCount > 0) {
            insightEl.textContent = `Fix ${criticalCount} critical issue${criticalCount > 1 ? 's' : ''} first for maximum impact`;
        } else if (highCount > 0) {
            insightEl.textContent = `${highCount} high-severity issue${highCount > 1 ? 's' : ''} should be prioritized`;
        } else if (fixableIssues.length > 0) {
            insightEl.textContent = `${fixableIssues.length} issues can be auto-fixed`;
        } else {
            insightEl.textContent = 'Review issues manually for best results';
        }
    }

    // Wire up "Select All" button
    const selectBtn = document.getElementById('btn-select-top-fixes');
    if (selectBtn) {
        selectBtn.onclick = () => {
            topFixes.forEach(fix => {
                if (fix.id !== undefined) {
                    State.selectedIssues = State.selectedIssues || new Set();
                    State.selectedIssues.add(fix.id);
                }
            });
            renderIssuesList();
            showNotification(`Selected ${topFixes.length} top impact issues`, 'success');
        };
    }
}

/**
 * Render Inline Fix Impact Analyzer — "Path to 100" (v4.5.3)
 *
 * Shows the FULL path from the current score to 100 by grouping issues
 * into category clusters. Each cluster shows its point impact and issue count.
 * Large groups are clumped to keep the list digestible (max ~8 rows).
 * Clicking a group filters the issues list to that category.
 */
function renderFixImpactAnalyzerInline(data) {
    const container = document.getElementById('impact-analyzer-inline');
    const currentScoreEl = document.getElementById('current-score-value-inline');
    const projectedScoreEl = document.getElementById('projected-score-value-inline');
    const currentGaugeFill = document.getElementById('current-gauge-fill-inline');
    const projectedGaugeFill = document.getElementById('projected-gauge-fill-inline');
    const improvementEl = document.getElementById('score-improvement-inline');
    const topFixesList = document.getElementById('top-fixes-list-inline');

    if (!container || !topFixesList) return;

    const issues = State.issues || [];
    const currentScore = data?.score ?? State.lastScanData?.score ?? 0;
    const pointsToGain = 100 - currentScore;

    // Severity weights matching the backend scoring algorithm (core.py _calculate_score)
    const backendWeights = { critical: 15, high: 5, medium: 2, low: 0.5, info: 0.1 };

    // Calculate total raw deduction (mirroring backend formula)
    const totalRawDeduction = issues.reduce((sum, i) => {
        const sev = (i.severity || 'low').toLowerCase();
        return sum + (backendWeights[sev] || 0.5);
    }, 0);

    // Backend normalization: if >20 issues, divide by log10(count+1)
    const issueCount = issues.length;
    const normalizedTotal = issueCount > 20
        ? totalRawDeduction / Math.log10(issueCount + 1)
        : totalRawDeduction;

    // Backend: deduction = min(80, normalizedTotal / 2), score = 100 - deduction
    // So each issue's share of the deduction = its weight / totalRawDeduction * actualDeduction
    const actualDeduction = Math.min(80, normalizedTotal / 2);

    // Group issues by category and calculate each group's point impact
    const categoryMap = new Map();
    issues.forEach((issue, idx) => {
        const cat = issue.category || 'Other';
        const sev = (issue.severity || 'low').toLowerCase();
        const weight = backendWeights[sev] || 0.5;

        if (!categoryMap.has(cat)) {
            categoryMap.set(cat, {
                category: cat,
                issues: [],
                totalWeight: 0,
                severityCounts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
            });
        }
        const group = categoryMap.get(cat);
        group.issues.push({ ...issue, originalIndex: idx });
        group.totalWeight += weight;
        group.severityCounts[sev] = (group.severityCounts[sev] || 0) + 1;
    });

    // Calculate each group's proportional score impact
    let groups = [...categoryMap.values()].map(g => {
        const proportion = totalRawDeduction > 0 ? g.totalWeight / totalRawDeduction : 0;
        const points = Math.round(proportion * actualDeduction * 10) / 10;
        return { ...g, points, proportion };
    }).sort((a, b) => b.points - a.points);

    // Clump tiny groups (<0.5 points each) into "Other Minor Issues"
    const significantGroups = [];
    const minorGroups = [];
    const MINOR_THRESHOLD = 0.5;

    groups.forEach(g => {
        if (g.points >= MINOR_THRESHOLD) {
            significantGroups.push(g);
        } else {
            minorGroups.push(g);
        }
    });

    if (minorGroups.length > 0) {
        const clumped = {
            category: `${minorGroups.length} Minor Categories`,
            issues: minorGroups.flatMap(g => g.issues),
            totalWeight: minorGroups.reduce((s, g) => s + g.totalWeight, 0),
            points: minorGroups.reduce((s, g) => s + g.points, 0),
            proportion: minorGroups.reduce((s, g) => s + g.proportion, 0),
            severityCounts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
            isClumped: true,
            subCategories: minorGroups.map(g => g.category)
        };
        minorGroups.forEach(g => {
            Object.keys(g.severityCounts).forEach(k => {
                clumped.severityCounts[k] += g.severityCounts[k];
            });
        });
        significantGroups.push(clumped);
    }

    // If still too many groups (>8), clump the bottom ones
    const MAX_ROWS = 8;
    let displayGroups = significantGroups;
    if (displayGroups.length > MAX_ROWS) {
        const top = displayGroups.slice(0, MAX_ROWS - 1);
        const rest = displayGroups.slice(MAX_ROWS - 1);
        const clumped = {
            category: `${rest.length} Other Categories`,
            issues: rest.flatMap(g => g.issues),
            totalWeight: rest.reduce((s, g) => s + g.totalWeight, 0),
            points: rest.reduce((s, g) => s + g.points, 0),
            proportion: rest.reduce((s, g) => s + g.proportion, 0),
            severityCounts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
            isClumped: true,
            subCategories: rest.map(g => g.category)
        };
        rest.forEach(g => {
            Object.keys(g.severityCounts).forEach(k => {
                clumped.severityCounts[k] += g.severityCounts[k];
            });
        });
        top.push(clumped);
        displayGroups = top;
    }

    // Projected score = 100 (fixing everything)
    const projectedScore = 100;

    // Animate score gauges
    const circumference = 2 * Math.PI * 42; // r=42

    if (currentScoreEl) currentScoreEl.textContent = currentScore;
    if (currentGaugeFill) {
        const currentDash = (currentScore / 100) * circumference;
        setTimeout(() => {
            currentGaugeFill.style.strokeDasharray = `${currentDash} ${circumference}`;
        }, 100);
    }

    if (projectedScoreEl) projectedScoreEl.textContent = projectedScore;
    if (projectedGaugeFill) {
        const projectedDash = (projectedScore / 100) * circumference;
        setTimeout(() => {
            projectedGaugeFill.style.strokeDasharray = `${projectedDash} ${circumference}`;
        }, 400);
    }

    if (improvementEl) {
        improvementEl.textContent = pointsToGain > 0 ? `+${Math.round(pointsToGain)}` : '100!';
        improvementEl.style.opacity = pointsToGain > 0 ? '1' : '0.5';
    }

    // Apply color classes based on score
    const getGaugeColor = (score) => {
        if (score >= 80) return '#22c55e';
        if (score >= 60) return '#eab308';
        if (score >= 40) return '#f97316';
        return '#ef4444';
    };
    if (currentGaugeFill) currentGaugeFill.style.stroke = getGaugeColor(currentScore);
    if (projectedGaugeFill) projectedGaugeFill.style.stroke = getGaugeColor(projectedScore);

    // Render the path-to-100 grouped list
    if (issues.length === 0) {
        topFixesList.innerHTML = '<div class="no-fixes" style="text-align:center;color:var(--text-muted);font-size:11px;padding:20px;">No issues found — score is 100!</div>';
    } else {
        // Build cumulative running score for the "step" indicator
        let runningScore = currentScore;

        topFixesList.innerHTML = displayGroups.map((group, idx) => {
            const count = group.issues.length;
            const pts = group.points;
            const stepStart = Math.round(runningScore);
            runningScore = Math.min(100, runningScore + pts);
            const stepEnd = Math.round(runningScore);

            // Severity badge breakdown (show only non-zero)
            const sevBadges = [];
            if (group.severityCounts.critical) sevBadges.push(`<span class="sev-pip critical">${group.severityCounts.critical}C</span>`);
            if (group.severityCounts.high) sevBadges.push(`<span class="sev-pip high">${group.severityCounts.high}H</span>`);
            if (group.severityCounts.medium) sevBadges.push(`<span class="sev-pip medium">${group.severityCounts.medium}M</span>`);
            if (group.severityCounts.low) sevBadges.push(`<span class="sev-pip low">${group.severityCounts.low}L</span>`);

            // Bar width as percentage of max group points
            const maxPoints = displayGroups[0].points || 1;
            const barPct = Math.max(5, Math.round((pts / maxPoints) * 100));

            return `
                <div class="fix-group-item" data-index="${idx}" data-categories="${escapeHtml(group.isClumped ? (group.subCategories || []).join(',') : group.category)}" title="Fix ${count} issues to gain ~${pts.toFixed(1)} points">
                    <div class="fix-group-bar" style="width:${barPct}%"></div>
                    <div class="fix-group-content">
                        <div class="fix-group-header">
                            <span class="fix-group-name">${escapeHtml(group.category)}</span>
                            <span class="fix-group-score-step">${stepStart} → ${stepEnd}</span>
                        </div>
                        <div class="fix-group-meta">
                            <span class="fix-group-count">${count} issue${count !== 1 ? 's' : ''}</span>
                            <span class="fix-group-points">+${pts.toFixed(1)} pts</span>
                            <span class="fix-group-sevs">${sevBadges.join(' ')}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Click handler: filter issues list to that category group
        topFixesList.querySelectorAll('.fix-group-item').forEach(item => {
            item.addEventListener('click', () => {
                const idx = parseInt(item.dataset.index);
                const group = displayGroups[idx];
                if (!group) return;

                // Visual feedback
                topFixesList.querySelectorAll('.fix-group-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');

                // Get the category names for this group
                const cats = group.isClumped
                    ? (group.subCategories || [])
                    : [group.category];

                // Filter issues to just this category group
                State.filteredIssues = State.issues.filter(i => cats.includes(i.category || 'Other'));
                State.currentPage = 1;

                if (typeof renderIssuesList === 'function') {
                    renderIssuesList();
                } else if (typeof TWR?.Renderers?.renderIssuesList === 'function') {
                    TWR.Renderers.renderIssuesList();
                }

                const label = group.isClumped ? `${cats.length} categories` : group.category;
                if (typeof toast === 'function') {
                    toast('info', `Showing ${group.issues.length} issues in ${label}`);
                }
            });
        });
    }

    // Wire up "Select Top" button — selects all issues in the top (biggest) group
    const selectBtn = document.getElementById('btn-select-top-fixes-inline');
    if (selectBtn) {
        selectBtn.onclick = () => {
            const topGroup = displayGroups[0];
            if (!topGroup) return;
            topGroup.issues.forEach(issue => {
                if (issue.issue_id !== undefined) {
                    State.selectedIssues = State.selectedIssues || new Set();
                    State.selectedIssues.add(issue.issue_id);
                }
            });
            renderIssuesList();
            if (typeof toast === 'function') {
                toast('success', `Selected ${topGroup.issues.length} issues in "${topGroup.category}"`);
            }
        };
    }

    // Initialize lucide icons for the new content
    if (typeof lucide !== 'undefined') {
        requestAnimationFrame(() => {
            try {
                lucide.createIcons();
            } catch (e) {
                // Ignore icon initialization errors
            }
        });
    }
}

/**
 * Helper to get score class for styling
 */
function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'fair';
    return 'poor';
}

/**
 * Render all advanced analytics components
 * v4.0.2: Removed Issue Hotspots, duplicate Fix Impact Analyzer, and Checker Correlation Matrix
 * Fix Impact Analyzer is now rendered inline in the Document Analytics panel
 */
function renderAdvancedAnalytics(data) {
    // Components removed in v4.0.2 - functionality moved to inline Fix Impact Analyzer
    // renderHotspotFlow(data);
    // renderFixImpactAnalyzer(data);
    // renderCheckerCorrelationHeatmap(data);
}

// ============================================================
// v3.0.13: UNIFIED FILTER BAR
// ============================================================

function showUnifiedFilterBar(data) {
    const filterBar = document.getElementById('unified-filter-bar');
    if (!filterBar) return;
    
    filterBar.style.display = 'flex';
    
    // Update severity counts
    if (data.by_severity) {
        Object.entries(data.by_severity).forEach(([sev, count]) => {
            const el = document.getElementById(`unified-count-${sev.toLowerCase()}`);
            if (el) el.textContent = count;
        });
    }
    
    // Populate category dropdown
    updateUnifiedCategoryDropdown(data.by_category || {});
    
    // Update filter result summary
    updateFilterResultSummary();
}

function updateUnifiedCategoryDropdown(byCategory) {
    const list = document.getElementById('unified-category-list');
    if (!list) return;
    
    const sorted = Object.entries(byCategory).sort((a, b) => b[1] - a[1]);
    
    list.innerHTML = sorted.map(([cat, count]) => `
        <label>
            <input type="checkbox" data-category="${escapeHtml(cat)}" checked>
            <span>${escapeHtml(cat)}</span>
            <span class="cat-count" style="margin-left:auto;color:var(--text-muted);font-size:11px;">${count}</span>
        </label>
    `).join('');
    
    // Add change handlers
    list.querySelectorAll('input').forEach(cb => {
        cb.addEventListener('change', () => {
            applyUnifiedFilters();
        });
    });
}

// v3.0.13: Alias for backwards compatibility - all filtering now goes through applyFilters()
function applyUnifiedFilters() {
    applyFilters();
}

function updateUnifiedFilterChips() {
    const container = document.getElementById('filter-chips-inline');
    const clearBtn = document.getElementById('btn-clear-filters');
    if (!container) return;
    
    const chips = [];
    
    // Chart filter chip
    if (FilterState.chartFilter) {
        chips.push({
            type: 'chart',
            value: FilterState.chartFilter.value,
            label: `Chart: ${FilterState.chartFilter.value}`
        });
    }
    
    // Family filter chip
    if (State.filters?.customFilter && State.filters?.customFilterLabel) {
        chips.push({
            type: 'family',
            value: 'custom',
            label: `Pattern: ${truncate(State.filters.customFilterLabel, 20)}`
        });
    }
    
    // v3.0.29: Validation filter chip (only show when not "all")
    if (FilterState.validationFilter) {
        chips.push({
            type: 'validation',
            value: FilterState.validationFilter,
            label: `Validation: ${FilterState.validationFilter === 'validated' ? 'Validated only' : 'Unvalidated only'}`
        });
    }
    
    // Render chips
    if (chips.length === 0) {
        container.innerHTML = '';
        if (clearBtn) clearBtn.style.display = 'none';
        return;
    }
    
    if (clearBtn) clearBtn.style.display = 'inline-flex';
    
    container.innerHTML = chips.map(chip => `
        <span class="filter-chip-inline" data-type="${chip.type}" data-value="${escapeHtml(chip.value)}">
            ${escapeHtml(chip.label)}
            <i data-lucide="x"></i>
        </span>
    `).join('');
    
    // Add click handlers
    container.querySelectorAll('.filter-chip-inline').forEach(chip => {
        chip.addEventListener('click', () => {
            const type = chip.dataset.type;
            if (type === 'chart') {
                FilterState.chartFilter = null;
            } else if (type === 'family') {
                clearFamilyFilter();
                return;
            } else if (type === 'validation') {
                // v3.0.29: Clear validation filter and reset UI
                FilterState.setValidationFilter(null);
                // Reset toggle button state
                document.querySelectorAll('.validation-filter-toggle .validation-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.validation === 'all');
                });
            }
            applyUnifiedFilters();
        });
    });
    
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

function updateFilterResultSummary() {
    const summary = document.getElementById('filter-result-summary');
    if (!summary) return;
    
    if (State.filteredIssues.length < State.issues.length) {
        summary.textContent = `Showing ${State.filteredIssues.length} of ${State.issues.length}`;
    } else {
        summary.textContent = '';
    }
}

function updateCategoryActiveCount() {
    const countEl = document.getElementById('category-active-count');
    const totalCategories = document.querySelectorAll('#unified-category-list input').length;
    const checkedCategories = document.querySelectorAll('#unified-category-list input:checked').length;
    
    if (countEl) {
        if (checkedCategories < totalCategories) {
            countEl.textContent = checkedCategories;
            countEl.style.display = 'inline-flex';
        } else {
            countEl.style.display = 'none';
        }
    }
}

function clearAllUnifiedFilters() {
    // Reset severity toggles to all active
    document.querySelectorAll('#unified-severity-toggles .sev-toggle').forEach(btn => {
        btn.classList.add('active');
    });
    
    // Check all categories
    document.querySelectorAll('#unified-category-list input').forEach(cb => {
        cb.checked = true;
    });
    
    // Clear search
    const searchInput = document.getElementById('issue-search');
    if (searchInput) searchInput.value = '';
    
    // Clear chart filter
    FilterState.chartFilter = null;
    
    // v3.0.29: Clear validation filter
    FilterState.setValidationFilter(null);
    document.querySelectorAll('.validation-filter-toggle .validation-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.validation === 'all');
    });
    
    // Clear family filter
    if (State.filters) {
        State.filters.customFilter = null;
        State.filters.customFilterLabel = null;
    }
    
    applyUnifiedFilters();
}

function setView(viewType) {
    document.getElementById('btn-view-table')?.classList.toggle('active', viewType === 'table');
    document.getElementById('btn-view-cards')?.classList.toggle('active', viewType === 'cards');
    
    const issuesList = document.getElementById('issues-list');
    if (issuesList) {
        issuesList.classList.toggle('card-view', viewType === 'cards');
    }
}

// ============================================================
// MODAL HELPERS
// ============================================================

// Track which element opened the modal for focus restoration
let modalOpenerElement = null;

function closeModals() {
    document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
    document.body.classList.remove('modal-open');
    
    // Restore focus to opener element
    if (modalOpenerElement && document.body.contains(modalOpenerElement)) {
        modalOpenerElement.focus();
        modalOpenerElement = null;
    }
}

function showModal(modalId) {
    // Store opener for focus restoration
    modalOpenerElement = document.activeElement;

    const modal = document.getElementById(modalId);
    if (modal) {
        // v4.6.2-fix: Clear any inline display:none left by close handlers
        modal.style.display = '';
        modal.style.visibility = '';
        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // Focus first focusable element in modal
        const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) {
            setTimeout(() => focusable.focus(), 50);
        }
    }
}

// ============================================================
// API HELPER
// ============================================================
async function api(endpoint, method = 'GET', body = null, _retried) {
    const opts = {
        method,
        headers: {}
    };

    if (method !== 'GET' && State.csrfToken) {
        opts.headers['X-CSRF-Token'] = State.csrfToken;
    }

    if (body && !(body instanceof FormData)) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    } else if (body) {
        if (State.csrfToken) {
            opts.headers['X-CSRF-Token'] = State.csrfToken;
        }
        opts.body = body;
    }

    try {
        const response = await fetch(`/api${endpoint}`, opts);

        const newToken = response.headers.get('X-CSRF-Token');
        if (newToken) {
            State.csrfToken = newToken;
            window.CSRF_TOKEN = newToken;
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) meta.setAttribute('content', newToken);
        }

        if (response.status === 403 && !_retried) {
            // v6.0.2: Auto-retry with fresh CSRF token instead of asking user to retry
            console.log('[TWR] CSRF 403 — refreshing token and retrying...');
            await fetchCSRFToken();
            // Update token in opts for retry
            if (method !== 'GET' && State.csrfToken) {
                opts.headers['X-CSRF-Token'] = State.csrfToken;
            }
            return api(endpoint, method, body, true);
        }

        if (response.status === 403) {
            // Second attempt also failed — report to user
            await fetchCSRFToken();
            toast('warning', 'Security token refreshed. Please try again.');
            return { success: false, error: 'CSRF token expired' };
        }

        if (response.status === 413) {
            return { success: false, error: 'File is too large. Maximum size is 50MB.' };
        }

        if (response.status === 429) {
            return { success: false, error: 'Too many requests. Please wait a moment.' };
        }

        return await response.json();
    } catch (e) {
        console.error('[TWR] API error:', e);
        return { success: false, error: e.message };
    }
}

// ============================================================
// UI HELPERS
// ============================================================
function show(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = '';
}

function hide(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

function setLoading(loading, message = STRINGS.loading.default, progress = 0) {
    State.isLoading = loading;
    const overlay = document.getElementById('loading-overlay');
    const msgEl = document.getElementById('loading-text');
    const progressBar = document.getElementById('loading-progress-bar');
    const stepsContainer = document.getElementById('loading-steps');
    
    // v3.0.43: Persistent run-state indicator
    const runStateIndicator = document.getElementById('run-state-indicator');
    const runStateText = document.getElementById('run-state-text');

    if (overlay) overlay.style.display = loading ? 'flex' : 'none';
    if (msgEl) msgEl.textContent = message;
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        // Update molten orb position
        const orbEl = document.getElementById('loading-progress-orb');
        if (orbEl) orbEl.style.left = `${progress}%`;
        // Handle complete state
        const moltenProgress = document.getElementById('loading-molten-progress');
        if (moltenProgress) {
            if (progress >= 100) {
                moltenProgress.classList.add('molten-complete');
            } else {
                moltenProgress.classList.remove('molten-complete');
            }
        }
    }
    
    // v3.0.43: Update run-state indicator
    if (runStateIndicator) {
        runStateIndicator.style.display = loading ? 'flex' : 'none';
    }
    if (runStateText && loading) {
        // Shorten message for indicator
        const shortMsg = message.length > 30 ? message.substring(0, 27) + '...' : message;
        runStateText.textContent = shortMsg;
    }
    
    // B9: Reset steps when loading starts/stops
    if (stepsContainer) {
        if (loading) {
            stepsContainer.style.display = 'flex';
            // Reset all steps
            stepsContainer.querySelectorAll('.loading-step').forEach(step => {
                step.classList.remove('active', 'complete');
                const icon = step.querySelector('.step-icon');
                if (icon) icon.setAttribute('data-lucide', 'circle');
            });
        } else {
            stepsContainer.style.display = 'none';
        }
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }
}

// B9: Update loading step status
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
    
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

function updateProgress(progress, message) {
    const msgEl = document.getElementById('loading-text');
    const progressBar = document.getElementById('loading-progress-bar');
    
    if (msgEl && message) msgEl.textContent = message;
    if (progressBar) progressBar.style.width = `${progress}%`;
    
    // v3.0.43: Update run-state indicator text with progress percentage
    const runStateText = document.getElementById('run-state-text');
    if (runStateText && message) {
        // Show shortened message with progress
        const shortMsg = message.length > 20 ? message.substring(0, 17) + '...' : message;
        runStateText.textContent = `${Math.round(progress)}% - ${shortMsg}`;
    }
}

function setStatValue(id, value) {
    if (window.TWR?.Renderers?.setStatValue) {
        return TWR.Renderers.setStatValue(id, value);
    }
    // Fallback
    const el = document.getElementById(id);
    if (el) el.textContent = typeof value === 'number' ? value.toLocaleString() : value;
}

function updateStats() {
    if (window.TWR?.Renderers?.updateStats) {
        return TWR.Renderers.updateStats();
    }
    // Fallback
    setStatValue('total-issues', State.issues.length);
    setStatValue('filtered-issues', State.filteredIssues.length);
    updateSelectionUI();
}

function toggleSection(titleEl) {
    const targetId = titleEl.dataset.target;
    const target = document.getElementById(targetId);
    if (!target) return;

    const isCollapsed = target.classList.toggle('collapsed');
    titleEl.classList.toggle('active', !isCollapsed);
}

// v2.9.8: Super-section toggle (v3.0.46: uses TWR.Storage)
function toggleSuperSection(headerEl) {
    const targetId = headerEl.dataset.target;
    const target = document.getElementById(targetId);
    if (!target) return;

    const isCollapsed = target.classList.toggle('collapsed');
    headerEl.classList.toggle('active', !isCollapsed);
    
    // Save state via unified storage
    const superSectionId = headerEl.closest('.super-section')?.id;
    if (superSectionId) {
        if (window.TWR?.Storage?.ui) {
            TWR.Storage.ui.setPanelState(superSectionId, isCollapsed ? 'collapsed' : 'expanded');
        }
    }
}

// v2.9.8: Restore super-section collapse state (v3.0.46: uses TWR.Storage)
function restoreSuperSectionState() {
    document.querySelectorAll('.super-section').forEach(section => {
        const sectionId = section.id;
        const header = section.querySelector('.super-section-header');
        const content = section.querySelector('.super-section-content');
        
        if (!header || !content) return;
        
        // v3.0.46: Use unified storage if available
        const savedState = window.TWR?.Storage?.ui
            ? TWR.Storage.ui.getPanelState(sectionId)
            : null;
            
        if (savedState === 'collapsed') {
            content.classList.add('collapsed');
            header.classList.remove('active');
        } else if (savedState === 'expanded') {
            content.classList.remove('collapsed');
            header.classList.add('active');
        } else {
            // Default state: Document and Analysis expanded, Tools collapsed
            if (sectionId === 'super-analysis' || sectionId === 'super-document') {
                content.classList.remove('collapsed');
                header.classList.add('active');
            }
        }
    });
}

function toast(type, message, duration = 4000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = { success: 'check-circle', error: 'x-circle', warning: 'alert-triangle', info: 'info' };
    toast.innerHTML = `
        <i data-lucide="${icons[type] || 'info'}" class="toast-icon"></i>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// ============================================================
// UTILITIES
// ============================================================
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function debounce(fn, delay) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
    };
}

function getTimestamp() {
    return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

// ============================================================
// SCAN HISTORY
// ============================================================
async function loadScanHistory() {
    try {
        const r = await api('/scan-history', 'GET');
        if (r.success && r.data) {
            renderScanHistory(r.data);
        } else {
            document.getElementById('scan-history-empty').style.display = 'block';
            document.querySelector('.scan-history-table').style.display = 'none';
        }
    } catch (e) {
        console.error('[TWR] Failed to load scan history:', e);
        document.getElementById('scan-history-empty').style.display = 'block';
    }
}

function renderScanHistory(history) {
    const tbody = document.getElementById('scan-history-body');
    const emptyMsg = document.getElementById('scan-history-empty');
    const table = document.querySelector('.scan-history-table');
    
    if (!history || history.length === 0) {
        emptyMsg.style.display = 'block';
        table.style.display = 'none';
        return;
    }
    
    emptyMsg.style.display = 'none';
    table.style.display = 'block';
    
    tbody.innerHTML = history.map(scan => {
        const scanDate = new Date(scan.scan_time);
        const dateStr = scanDate.toLocaleDateString() + ' ' + scanDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let changeHtml = '<span class="change-indicator unchanged">First scan</span>';
        if (scan.issues_added > 0 || scan.issues_removed > 0) {
            changeHtml = `
                <span class="change-indicator added">+${scan.issues_added}</span>
                <span class="change-indicator removed">-${scan.issues_removed}</span>
            `;
        }
        
        return `
            <tr data-scan-id="${scan.id}">
                <td><strong>${escapeHtml(scan.filename)}</strong></td>
                <td>${dateStr}</td>
                <td>${scan.issue_count}</td>
                <td>${scan.score}</td>
                <td><span class="grade-badge grade-${scan.grade}">${scan.grade}</span></td>
                <td>${changeHtml}</td>
                <td>
                    <button class="btn btn-ghost btn-sm btn-delete-scan" 
                            data-action="delete-scan"
                            data-scan-id="${scan.id}"
                            data-filename="${escapeHtml(scan.filename)}"
                            title="Delete this scan">
                        <i data-lucide="trash-2"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Refresh icons for the new buttons
    if (typeof lucide !== 'undefined') {
        try { lucide.createIcons(); } catch(e) {}
    }
}

async function deleteScanFromHistory(scanId, filename) {
    // Confirm deletion
    if (!confirm(`Delete scan record for "${filename}"?\n\nThis cannot be undone.`)) {
        return;
    }
    
    try {
        const result = await api(`/scan-history/${scanId}`, 'DELETE');
        
        if (result.success) {
            toast('success', 'Scan deleted successfully');
            // Refresh the history list
            await loadScanHistory();
        } else {
            toast('error', result.message || 'Failed to delete scan');
        }
    } catch (e) {
        console.error('[TWR] Error deleting scan:', e);
        toast('error', 'Failed to delete scan');
    }
}

// Event delegation for scan history table actions
// This avoids inline onclick handlers which are prone to quoting bugs
function initScanHistoryEventDelegation() {
    const tbody = document.getElementById('scan-history-body');
    if (!tbody) return;
    
    tbody.addEventListener('click', async (e) => {
        const button = e.target.closest('[data-action="delete-scan"]');
        if (button) {
            const scanId = parseInt(button.dataset.scanId, 10);
            const filename = button.dataset.filename;
            if (scanId && filename) {
                await deleteScanFromHistory(scanId, filename);
            }
        }
    });
}

function showScanHistoryModal() {
    loadScanHistory();
    showModal('modal-scan-history');
}

// ============================================================
// SCAN PROFILES
// ============================================================
async function loadScanProfiles() {
    try {
        const r = await api('/scan-profiles', 'GET');
        if (r.success && r.data) {
            renderProfileList(r.data);
            
            // Load default profile if exists
            const defaultProfile = r.data.find(p => p.is_default);
            if (defaultProfile && !State.reviewResults) {
                applyProfile(defaultProfile);
            }
        }
    } catch (e) {
        console.warn('[TWR] Failed to load scan profiles:', e);
    }
}

function renderProfileList(profiles) {
    const container = document.getElementById('profile-list');

    // BUG-M28 FIX: Check if container exists before accessing it
    if (!container) {
        console.warn('[TWR] Profile list container not found');
        return;
    }

    const emptyMsg = container.querySelector('.profile-empty');

    if (!profiles || profiles.length === 0) {
        if (emptyMsg) emptyMsg.style.display = 'block';
        return;
    }

    if (emptyMsg) emptyMsg.style.display = 'none';
    
    const profileHtml = profiles.map(p => `
        <div class="profile-item ${p.is_default ? 'default' : ''}" data-profile-id="${p.id}" onclick="applyProfileById(${p.id})">
            <span class="profile-item-name">${escapeHtml(p.name)}${p.is_default ? ' ★' : ''}</span>
            <div class="profile-item-actions">
                <button class="btn btn-xs btn-ghost" onclick="event.stopPropagation(); deleteProfile(${p.id})" title="Delete">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = profileHtml + '<p class="profile-empty" style="display:none;">No saved profiles</p>';
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

function applyProfile(profile) {
    if (!profile || !profile.options) return;
    
    // Apply the saved options to checkboxes
    Object.entries(profile.options).forEach(([key, value]) => {
        const checkbox = document.querySelector(`[data-checker="${key.replace('check_', '')}"]`);
        if (checkbox) {
            checkbox.checked = value;
        }
    });
    
    toast('success', `Profile "${profile.name}" applied`);
}

async function applyProfileById(id) {
    try {
        const r = await api('/scan-profiles', 'GET');
        if (r.success && r.data) {
            const profile = r.data.find(p => p.id === id);
            if (profile) {
                applyProfile(profile);
            }
        }
    } catch (e) {
        toast('error', 'Failed to load profile');
    }
}

function showSaveProfileModal() {
    // Populate settings preview
    const options = gatherCurrentOptions();
    const enabledChecks = Object.entries(options)
        .filter(([k, v]) => v)
        .map(([k]) => k.replace('check_', '').replace(/_/g, ' '));
    
    const preview = document.getElementById('profile-settings-preview');
    preview.innerHTML = enabledChecks.map(c => `<li>${c}</li>`).join('');
    
    document.getElementById('profile-name').value = '';
    document.getElementById('profile-description').value = '';
    document.getElementById('profile-set-default').checked = false;
    
    showModal('modal-save-profile');
}

async function saveCurrentProfile() {
    const name = document.getElementById('profile-name').value.trim();
    const description = document.getElementById('profile-description').value.trim();
    const setDefault = document.getElementById('profile-set-default').checked;
    
    if (!name) {
        toast('warning', 'Please enter a profile name');
        return;
    }
    
    const options = gatherCurrentOptions();
    
    try {
        const r = await api('/scan-profiles', 'POST', {
            name,
            description,
            options,
            set_default: setDefault
        });
        
        if (r.success) {
            toast('success', `Profile "${name}" saved`);
            closeModals();
            loadScanProfiles();
        } else {
            toast('error', 'Failed to save profile');
        }
    } catch (e) {
        toast('error', 'Failed to save profile');
    }
}

async function deleteProfile(id) {
    if (!confirm('Delete this profile?')) return;
    
    try {
        const r = await api(`/scan-profiles/${id}`, 'DELETE');
        if (r.success) {
            toast('success', 'Profile deleted');
            loadScanProfiles();
        }
    } catch (e) {
        toast('error', 'Failed to delete profile');
    }
}

function gatherCurrentOptions() {
    const options = {};
    document.querySelectorAll('[data-checker]').forEach(cb => {
        if (cb.checked !== undefined) {
            options[`check_${cb.dataset.checker}`] = cb.checked;
        }
    });
    return options;
}

// ============================================================
// FIX PREVIEW WITH APPROVAL
// ============================================================
// ============================================================
// BATCH 4: TIERED AUTO-FIX SYSTEM (F8, A11, E8)
// ============================================================

// Fix confidence tiers
const FixConfidenceTiers = {
    safe: {
        label: 'Safe Fixes',
        description: 'Low-risk changes that can be applied automatically',
        color: 'var(--success)',
        patterns: ['whitespace', 'double space', 'extra space', 'trailing space', 'punctuation spacing']
    },
    review: {
        label: 'Review Recommended', 
        description: 'Changes that should be reviewed before applying',
        color: 'var(--warning)',
        patterns: ['capitalize', 'passive voice', 'wordy', 'redundant', 'informal']
    },
    manual: {
        label: 'Manual Review Required',
        description: 'Complex changes requiring careful review',
        color: 'var(--error)',
        patterns: ['spelling', 'grammar', 'requirement', 'shall', 'will']
    }
};

// Classify a fix into a confidence tier
function classifyFixConfidence(issue) {
    const category = (issue.category || '').toLowerCase();
    const message = (issue.message || '').toLowerCase();
    
    for (const [tier, config] of Object.entries(FixConfidenceTiers)) {
        if (config.patterns.some(p => category.includes(p) || message.includes(p))) {
            return tier;
        }
    }
    return 'review'; // Default to review tier
}

// Group fixes by pattern for deduplication
function groupFixesByPattern(fixes) {
    const groups = new Map();
    
    fixes.forEach((fix, originalIdx) => {
        // Create a pattern key based on category + transformation type
        const category = fix.category || 'Other';
        const orig = (fix.flagged_text || '').toLowerCase().trim();
        const repl = (fix.suggestion || '').toLowerCase().trim();
        
        // Generalize the pattern (e.g., "extra space" type fixes)
        let patternKey;
        if (orig === repl.replace(/\s+/g, ' ')) {
            patternKey = `${category}|whitespace`;
        } else if (orig.length > 0 && repl.length === 0) {
            patternKey = `${category}|remove`;
        } else {
            // Use first 20 chars to group similar fixes
            patternKey = `${category}|${orig.substring(0, 20)}→${repl.substring(0, 20)}`;
        }
        
        if (!groups.has(patternKey)) {
            groups.set(patternKey, {
                category,
                representative: fix,
                fixes: [],
                indices: []
            });
        }
        groups.get(patternKey).fixes.push(fix);
        groups.get(patternKey).indices.push(originalIdx);
    });
    
    return groups;
}


// v3.0.97: Fix Assistant v2 - Integration Wiring Code
// WP6: Connects all Fix Assistant v2 modules
// ═══════════════════════════════════════════════════════════════════════════════
//
// This code replaces/enhances the existing FixAssistant module in app.js
// It wires together: DocumentViewer, MiniMap, FixAssistantState, LearnerClient,
// A11yManager, SoundEffects, PreviewModes, and ReportClient
//
// ═══════════════════════════════════════════════════════════════════════════════

const FixAssistant = (function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE STATE
    // ═══════════════════════════════════════════════════════════════════════════

    let isOpen = false;
    let _closingForFinish = false;  // v5.9.4: Flag to skip export modal re-show during handleFinishReview
    let _openedFromExport = false;  // v6.0.2: Track if FA was opened from export modal
    let sessionStartTime = null;
    let documentId = null;
    let documentScoreBefore = null;
    let unsubscribers = [];

    // Element references (cached on open)
    const els = {};

    // ═══════════════════════════════════════════════════════════════════════════
    // HELPER FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Generate unique document ID for localStorage persistence
     * Uses filename + file type + analysis timestamp to avoid key collisions when
     * reviewing the same filename multiple times
     * @param {Object} doc - Optional document object (not currently used)
     * @returns {string} Unique document identifier
     */
    function generateDocumentId(doc) {
        // Use available State fields
        const name = State.filename || doc?.name || `doc_${Date.now()}`;
        const fileType = State.fileType || 'unknown';
        // Use analysis timestamp to differentiate same-file reviews
        const timestamp = State.reviewResults?.analyzed_at || Date.now();
        
        // Create simple hash from combined values
        const combined = `${name}|${fileType}|${timestamp}`;
        let hash = 0;
        for (let i = 0; i < combined.length; i++) {
            const char = combined.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        
        // Return readable ID: filename_hash (truncated for readability)
        const hashStr = Math.abs(hash).toString(36).substring(0, 8);
        const safeName = name.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
        return `${safeName}_${hashStr}`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize Fix Assistant (called on page load)
     * Sets up global keyboard listener
     * v3.0.109: Enhanced initialization with better event binding
     */
    function init() {
        console.log('[TWR FixAssistant] Initializing v3.0.109');
        setupGlobalKeyboardShortcuts();
        
        // v3.0.109: Ensure modal close button is wired up even before first open
        const closeBtn = document.getElementById('fav2-btn-close');
        if (closeBtn && !closeBtn._fav2Initialized) {
            closeBtn._fav2Initialized = true;
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                close();
            });
        }
    }

    /**
     * Open the Fix Assistant modal
     * Initializes all modules and renders initial state
     * v3.0.109: Enhanced open with better error handling and UI feedback
     */
    function open() {
        if (isOpen) {
            console.log('[TWR FixAssistant] Already open');
            return;
        }

        console.log('[TWR FixAssistant] Opening v3.0.109...');

        // v6.0.2: Track if export modal was open when FA launched
        const exportModal = document.getElementById('modal-export');
        _openedFromExport = exportModal && exportModal.classList.contains('active');

        // Validate we have data
        if (!State.fixes || State.fixes.length === 0) {
            showNotification('No fixes available - scan a document first, or this document has no fixable issues', 'warning');
            return;
        }

        // Get document content and fix data from State
        const documentContent = State.reviewResults?.document_content;
        const fixes = State.fixes;
        const fixGroups = State.reviewResults?.fix_groups || [];
        const confidenceDetails = State.reviewResults?.confidence_details || {};

        // Generate unique document ID for persistence
        // Includes filename + size + upload timestamp to avoid key collisions
        documentId = generateDocumentId(State.currentDocument);
        sessionStartTime = Date.now();
        documentScoreBefore = State.reviewResults?.score || State.score || 70;

        // Cache element references
        cacheElements();

        // Initialize state manager
        const stateInitialized = FixAssistantState.init(fixes, fixGroups, {
            documentId: documentId,
            onReady: () => console.log('[TWR FixAssistant] State ready')
        });

        if (!stateInitialized) {
            console.error('[TWR FixAssistant] Failed to initialize state');
            return;
        }

        // Enrich fixes with confidence tier for minimap
        const enrichedFixes = fixes.map((fix, i) => ({
            ...fix,
            index: i,
            confidence_tier: confidenceDetails[String(i)]?.tier || 'review'
        }));

        // Check for saved progress
        if (FixAssistantState.hasProgress(documentId)) {
            const restored = FixAssistantState.restoreProgress(documentId);
            if (restored) {
                showNotification('Previous progress restored', 'info');
            }
        }

        // v6.0.2: Initialize review role mode toggle
        if (els.roleMode) {
            els.roleMode.value = FixAssistantState.getReviewRole();
            els.roleMode.addEventListener('change', function() {
                FixAssistantState.setReviewRole(els.roleMode.value);
                updateRoleModeHints();
            });
            updateRoleModeHints();
        }

        // Initialize document viewer
        const viewerContainer = els.documentViewer;
        // v6.0.2: Pass html_preview for rendered document view toggle
        const htmlPreview = State.reviewResults?.html_preview || null;
        if (viewerContainer && documentContent) {
            DocumentViewer.init(viewerContainer, documentContent, {
                onPageChange: handlePageChange,
                onParagraphClick: handleParagraphClick,
                htmlPreview: htmlPreview
            });
        } else if (!documentContent) {
            console.warn('[TWR FixAssistant] No document content available');
        }

        // Initialize mini-map
        const minimapContainer = els.minimap;
        if (minimapContainer) {
            console.log('[TWR FixAssistant] Initializing MiniMap with container:', minimapContainer);
            MiniMap.init(minimapContainer, {
                onNavigate: handleMinimapNavigate
            });
            const minimapFixes = enrichedFixes.map(f => ({
                index: f.index,
                paragraph_index: f.paragraph_index,
                page: f.page || 1,
                tier: f.confidence_tier,
                flagged_text: f.flagged_text
            }));
            console.log('[TWR FixAssistant] Setting MiniMap fixes:', minimapFixes.length, 'fixes');
            MiniMap.setFixes(minimapFixes);
            const totalParagraphs = documentContent?.paragraphs?.length || 100;
            const pageCount = documentContent?.page_count || 1;
            console.log('[TWR FixAssistant] Setting MiniMap document info:', { totalParagraphs, pageCount });
            MiniMap.setDocumentInfo(totalParagraphs, pageCount);
        } else {
            console.warn('[TWR FixAssistant] MiniMap container not found');
        }

        // Initialize preview modes
        PreviewModes.init({
            containerEl: viewerContainer,
            paragraphs: documentContent?.paragraphs || [],
            fixes: enrichedFixes,
            getDecisions: () => FixAssistantState.getAllDecisions()
        });

        // Initialize accessibility
        const modalEl = els.modal;
        if (modalEl) {
            A11yManager.init(modalEl);
        }

        // Initialize sounds (disabled by default, respects user preference)
        const soundEnabled = SoundEffects.init();
        updateSoundButton(soundEnabled);
        
        // Show one-time tooltip for sound effects discovery
        showSoundDiscoveryTip();

        // Register state change handlers
        unsubscribers.push(FixAssistantState.onChange(handleStateChange));
        unsubscribers.push(FixAssistantState.onDecision(handleDecision));

        // Setup UI event handlers
        setupUIEventHandlers();

        // Show modal
        showModal();
        isOpen = true;

        // Render initial state
        renderCurrentFix();
        updateStatistics();
        updateProgress();
        updateUndoRedoButtons();

        // Navigate to first fix
        const currentFix = FixAssistantState.getCurrentFix();
        if (currentFix) {
            scrollToCurrentFix();
        }

        console.log('[TWR FixAssistant] Opened with', fixes.length, 'fixes');
    }

    /**
     * Close the Fix Assistant modal
     */
    function close() {
        if (!isOpen) return;

        console.log('[TWR FixAssistant] Closing...');

        // Save progress before closing
        FixAssistantState.saveProgress();

        // Cleanup modules
        DocumentViewer.destroy();
        MiniMap.destroy();
        PreviewModes.destroy();
        A11yManager.destroy();

        // Unsubscribe from state events
        unsubscribers.forEach(unsub => {
            if (typeof unsub === 'function') unsub();
        });
        unsubscribers = [];

        // Remove UI event handlers
        removeUIEventHandlers();

        // Hide modal
        hideModal();
        isOpen = false;

        // v5.9.4: Re-show export modal (Fix Assistant's showModal() closed it on open)
        // Skip re-show if called from handleFinishReview() — it dispatches fixAssistantDone
        // which has its own re-show logic with stat updates
        // v6.0.2: Only re-show if FA was originally opened from the export modal
        if (!_closingForFinish && _openedFromExport) {
            setTimeout(() => {
                showModal('modal-export');
                // Restore Fix Assistant stats in launcher if state has decisions
                if (FixAssistantState.isInitialized()) {
                    const faStats = FixAssistantState.getStatistics();
                    const selectedEl = document.getElementById('selected-fix-count');
                    const fixableEl = document.getElementById('fixable-count');
                    if (selectedEl) selectedEl.textContent = faStats.accepted || 0;
                    if (fixableEl) fixableEl.textContent = (State.fixes || []).length;
                }
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }, 100);
        }
        _closingForFinish = false;
        _openedFromExport = false;

        console.log('[TWR FixAssistant] Closed');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // ELEMENT CACHING
    // ═══════════════════════════════════════════════════════════════════════════

    function cacheElements() {
        els.modal = document.getElementById('fav2-modal');
        els.documentViewer = document.getElementById('fav2-document-viewer');
        els.minimap = document.getElementById('fav2-minimap');

        // Header elements
        els.searchInput = document.getElementById('fav2-search-input');
        els.navMode = document.getElementById('fav2-nav-mode');
        els.progressFill = document.getElementById('fav2-progress-fill');
        els.progressText = document.getElementById('fav2-progress-text');
        els.counterCurrent = document.getElementById('fav2-counter-current');
        els.counterTotal = document.getElementById('fav2-counter-total');

        // Fix detail elements
        els.confidenceBadge = document.getElementById('fav2-confidence-badge');
        els.categoryBadge = document.getElementById('fav2-category-badge');
        els.counterCurrentDetail = document.getElementById('fav2-counter-current-detail');
        els.counterTotalDetail = document.getElementById('fav2-counter-total-detail');
        els.changeBefore = document.getElementById('fav2-change-before');
        els.changeAfter = document.getElementById('fav2-change-after');
        els.reason = document.getElementById('fav2-reason');
        els.confidenceDetails = document.getElementById('fav2-confidence-details');
        els.confidenceToggle = document.getElementById('fav2-confidence-toggle');
        els.reviewerNote = document.getElementById('fav2-reviewer-note');
        els.pageFixesList = document.getElementById('fav2-page-fixes-list');

        // Action buttons
        els.btnAccept = document.getElementById('fav2-btn-accept');
        els.btnReject = document.getElementById('fav2-btn-reject');
        els.btnSkip = document.getElementById('fav2-btn-skip');
        els.btnPrev = document.getElementById('fav2-btn-prev');
        els.btnNext = document.getElementById('fav2-btn-next');
        els.btnUndo = document.getElementById('fav2-btn-undo');
        els.btnRedo = document.getElementById('fav2-btn-redo');
        els.btnClose = document.getElementById('fav2-btn-close');
        els.btnDone = document.getElementById('fav2-btn-done');
        els.btnShortcuts = document.getElementById('fav2-btn-shortcuts');
        els.btnSound = document.getElementById('fav2-btn-sound');
        els.btnAcceptSafe = document.getElementById('fav2-btn-accept-safe');
        els.btnAcceptAll = document.getElementById('fav2-btn-accept-all');
        els.btnViewMode = document.getElementById('fav2-btn-view-mode');

        // Footer statistics
        els.statAccepted = document.getElementById('fav2-stat-accepted');
        els.statRejected = document.getElementById('fav2-stat-rejected');
        els.statPending = document.getElementById('fav2-stat-pending');

        // Panels
        els.shortcutsPanel = document.getElementById('fav2-shortcuts-panel');

        // v6.0.2: Review role mode toggle
        els.roleMode = document.getElementById('fav2-role-mode');
        els.roleHint = document.getElementById('fav2-role-hint');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // v6.0.2: REVIEW ROLE MODE
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Update UI hints (button tooltips) based on current review role mode.
     * Owner mode: Accept = text fix, Reject = comment
     * Reviewer mode: Accept = recommendation comment, Reject = skip
     */
    function updateRoleModeHints() {
        const isReviewer = FixAssistantState.getReviewRole() === 'reviewer';
        if (els.btnAccept) {
            els.btnAccept.title = isReviewer
                ? 'Add recommendation comment (A)'
                : 'Apply text fix (A)';
        }
        if (els.btnReject) {
            els.btnReject.title = isReviewer
                ? 'Skip - no action (R)'
                : 'Add rejection comment (R)';
        }
        // v6.0.2: Update contextual hint text below the role dropdown
        if (els.roleHint) {
            els.roleHint.textContent = isReviewer
                ? 'Accept = Comment only, Reject = No action'
                : 'Accept = Track Changes, Reject = Comment';
        }
        console.log('[TWR FixAssistant] Review role mode:', isReviewer ? 'reviewer' : 'owner');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UI EVENT HANDLERS
    // ═══════════════════════════════════════════════════════════════════════════

    function setupUIEventHandlers() {
        // v3.0.109: Enhanced event binding with null checks and logging
        console.log('[TWR FixAssistant] Setting up UI event handlers v3.0.109');
        
        // Action buttons
        if (els.btnAccept) {
            els.btnAccept.addEventListener('click', handleAcceptClick);
        } else {
            console.warn('[TWR FixAssistant] btnAccept not found');
        }
        
        if (els.btnReject) {
            els.btnReject.addEventListener('click', handleRejectClick);
        }
        
        if (els.btnSkip) {
            els.btnSkip.addEventListener('click', handleSkipClick);
        }
        
        if (els.btnPrev) {
            els.btnPrev.addEventListener('click', handlePrevClick);
        }
        
        if (els.btnNext) {
            els.btnNext.addEventListener('click', handleNextClick);
        }
        
        if (els.btnUndo) {
            els.btnUndo.addEventListener('click', handleUndoClick);
        }
        
        if (els.btnRedo) {
            els.btnRedo.addEventListener('click', handleRedoClick);
        }
        
        // v3.0.109: Critical - Close button with enhanced binding
        if (els.btnClose) {
            els.btnClose.addEventListener('click', handleCloseClick);
            console.log('[TWR FixAssistant] Close button bound successfully');
        } else {
            console.warn('[TWR FixAssistant] Close button (fav2-btn-close) not found!');
        }
        
        if (els.btnDone) {
            els.btnDone.addEventListener('click', handleDoneClick);
        }
        
        if (els.btnShortcuts) {
            els.btnShortcuts.addEventListener('click', handleShortcutsClick);
        }
        
        if (els.btnSound) {
            els.btnSound.addEventListener('click', handleSoundToggleClick);
        }
        
        if (els.btnAcceptSafe) {
            els.btnAcceptSafe.addEventListener('click', handleAcceptSafeClick);
        }
        
        if (els.btnAcceptAll) {
            els.btnAcceptAll.addEventListener('click', handleAcceptAllClick);
        }
        
        if (els.btnViewMode) {
            els.btnViewMode.addEventListener('click', handleViewModeClick);
        }

        // Search input
        els.searchInput?.addEventListener('input', debounce(handleSearchInput, 300));

        // Navigation mode select
        els.navMode?.addEventListener('change', handleNavModeChange);

        // Reviewer note
        els.reviewerNote?.addEventListener('blur', handleReviewerNoteBlur);

        // Confidence toggle
        els.confidenceToggle?.addEventListener('click', handleConfidenceToggle);

        // Page fixes list clicks
        els.pageFixesList?.addEventListener('click', handlePageFixClick);

        // Shortcuts panel close
        els.shortcutsPanel?.querySelector('.fav2-shortcuts-close')?.addEventListener('click', hideShortcutsPanel);
        
        // v3.0.109: Also bind click outside modal to close (optional but user-friendly)
        const modal = els.modal || document.getElementById('fav2-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                // Close only if clicking the backdrop (the modal itself, not its content)
                if (e.target === modal) {
                    close();
                }
            });
        }
    }

    function removeUIEventHandlers() {
        els.btnAccept?.removeEventListener('click', handleAcceptClick);
        els.btnReject?.removeEventListener('click', handleRejectClick);
        els.btnSkip?.removeEventListener('click', handleSkipClick);
        els.btnPrev?.removeEventListener('click', handlePrevClick);
        els.btnNext?.removeEventListener('click', handleNextClick);
        els.btnUndo?.removeEventListener('click', handleUndoClick);
        els.btnRedo?.removeEventListener('click', handleRedoClick);
        els.btnClose?.removeEventListener('click', handleCloseClick);
        els.btnDone?.removeEventListener('click', handleDoneClick);
        els.btnShortcuts?.removeEventListener('click', handleShortcutsClick);
        els.btnAcceptSafe?.removeEventListener('click', handleAcceptSafeClick);
        els.btnAcceptAll?.removeEventListener('click', handleAcceptAllClick);
        els.btnViewMode?.removeEventListener('click', handleViewModeClick);
        els.searchInput?.removeEventListener('input', handleSearchInput);
        els.navMode?.removeEventListener('change', handleNavModeChange);
        els.reviewerNote?.removeEventListener('blur', handleReviewerNoteBlur);
        els.confidenceToggle?.removeEventListener('click', handleConfidenceToggle);
        els.pageFixesList?.removeEventListener('click', handlePageFixClick);
    }

    // Button click handlers
    function handleAcceptClick() {
        const index = FixAssistantState.getCurrentIndex();
        const note = els.reviewerNote?.value?.trim() || '';
        FixAssistantState.accept(index, note);
        autoAdvance();
    }

    function handleRejectClick() {
        const index = FixAssistantState.getCurrentIndex();
        const note = els.reviewerNote?.value?.trim() || '';
        FixAssistantState.reject(index, note);
        autoAdvance();
    }

    function handleSkipClick() {
        FixAssistantState.goToNext(true);
        SoundEffects.play('skip');
    }

    function handlePrevClick() {
        FixAssistantState.goToPrevious();
    }

    function handleNextClick() {
        FixAssistantState.goToNext();
    }

    function handleUndoClick() {
        if (FixAssistantState.undo()) {
            SoundEffects.play('undo');
            A11yManager.announceUndoRedo('undo');
        }
    }

    function handleRedoClick() {
        if (FixAssistantState.redo()) {
            SoundEffects.play('undo');
            A11yManager.announceUndoRedo('redo');
        }
    }

    function handleCloseClick(e) {
        // v3.0.109: Enhanced close with event handling
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        console.log('[TWR FixAssistant] Close button clicked');
        close();
    }

    function handleDoneClick() {
        handleFinishReview();
    }

    function handleShortcutsClick() {
        toggleShortcutsPanel();
    }

    function handleSoundToggleClick() {
        const newState = !SoundEffects.isEnabled();
        SoundEffects.setEnabled(newState);
        updateSoundButton(newState);
        showNotification(newState ? 'Sound effects enabled' : 'Sound effects disabled', 'info');
    }

    function updateSoundButton(enabled) {
        if (!els.btnSound) return;
        els.btnSound.setAttribute('aria-pressed', String(enabled));
        els.btnSound.title = enabled ? 'Sound effects (on)' : 'Sound effects (off)';
        // Update icon
        const icon = els.btnSound.querySelector('i[data-lucide]');
        if (icon) {
            icon.setAttribute('data-lucide', enabled ? 'volume-2' : 'volume-x');
            // Re-render lucide icon
            if (window.lucide?.createIcons) {
                window.lucide.createIcons({ icons: { 'volume-2': true, 'volume-x': true } });
            }
        }
    }

    /**
     * Show one-time tooltip for sound effects discovery
     * Only shown if user hasn't seen it and sounds are disabled
     */
    function showSoundDiscoveryTip() {
        const STORAGE_KEY = 'twr_sound_tip_shown';
        
        // Don't show if already seen or sounds already enabled
        if (localStorage.getItem(STORAGE_KEY) === 'true' || SoundEffects.isEnabled()) {
            return;
        }
        
        // Mark as shown
        localStorage.setItem(STORAGE_KEY, 'true');
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'fav2-sound-tip';
        tooltip.innerHTML = `
            <span>💡 Tip: Enable sound effects for audio feedback!</span>
            <button type="button" class="fav2-sound-tip-close" aria-label="Dismiss tip">×</button>
        `;
        tooltip.style.cssText = `
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: var(--bg-card, #fff);
            border: 1px solid var(--border-color, #e0e0e0);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 100;
            white-space: nowrap;
            animation: fav2-tip-fadeIn 0.3s ease;
        `;
        
        // Position relative to sound button
        if (els.btnSound) {
            els.btnSound.style.position = 'relative';
            els.btnSound.appendChild(tooltip);
            
            // Close handler
            tooltip.querySelector('.fav2-sound-tip-close').addEventListener('click', () => {
                tooltip.remove();
            });
            
            // Auto-dismiss after 8 seconds
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.style.animation = 'fav2-tip-fadeOut 0.3s ease forwards';
                    setTimeout(() => tooltip.remove(), 300);
                }
            }, 8000);
        }
    }

    function handleAcceptSafeClick() {
        const count = FixAssistantState.acceptByTier('safe');
        if (count > 0) {
            showNotification(`Accepted ${count} safe fixes`, 'success');
            SoundEffects.play('accept');
        }
    }

    function handleAcceptAllClick() {
        if (confirm('Accept all remaining pending fixes?')) {
            const count = FixAssistantState.acceptAllPending();
            if (count > 0) {
                showNotification(`Accepted ${count} fixes`, 'success');
                SoundEffects.play('complete');
            }
        }
    }

    function handleViewModeClick() {
        const isEnabled = PreviewModes.isSplitScreenEnabled();
        PreviewModes.setSplitScreen(!isEnabled);
        els.btnViewMode?.setAttribute('aria-pressed', String(!isEnabled));
    }

    function handleSearchInput(e) {
        const query = e.target.value.trim();
        FixAssistantState.setSearchQuery(query);
        updatePageFixes();
    }

    function handleNavModeChange(e) {
        const mode = e.target.value;
        // Map select values to navigation modes
        const modeMap = {
            'all': 'sequential',
            'pending': 'sequential', // will filter
            'page': 'page',
            'category': 'category',
            'confidence': 'sequential' // will sort by tier
        };
        FixAssistantState.setNavigationMode(modeMap[mode] || 'sequential');

        // Apply filters based on mode
        if (mode === 'pending') {
            FixAssistantState.setFilters({ status: 'pending' });
        } else {
            FixAssistantState.clearFilters();
        }
    }

    function handleReviewerNoteBlur() {
        const index = FixAssistantState.getCurrentIndex();
        const note = els.reviewerNote?.value?.trim() || '';
        const decision = FixAssistantState.getDecision(index);
        if (decision && note !== (decision.note || '')) {
            FixAssistantState.setNote(index, note);
        }
    }

    function handleConfidenceToggle() {
        const isExpanded = els.confidenceToggle?.getAttribute('aria-expanded') === 'true';
        els.confidenceToggle?.setAttribute('aria-expanded', String(!isExpanded));
        if (els.confidenceDetails) {
            els.confidenceDetails.hidden = isExpanded;
        }
    }

    function handlePageFixClick(e) {
        const item = e.target.closest('.fav2-page-fix-item');
        if (!item) return;

        const fixIndex = parseInt(item.dataset.fixIndex, 10);
        if (!isNaN(fixIndex)) {
            FixAssistantState.goToIndex(fixIndex);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // STATE CHANGE HANDLERS
    // ═══════════════════════════════════════════════════════════════════════════

    function handleStateChange(data) {
        const { type, currentIndex, fix } = data;

        if (type === 'init' || type === 'reset') {
            renderCurrentFix();
            updateStatistics();
            updateProgress();
            return;
        }

        // Navigation or decision - update UI
        renderCurrentFix();
        updateProgress();
        updateUndoRedoButtons();

        // Scroll document viewer to current fix
        if (fix) {
            scrollToCurrentFix();

            // Update minimap
            MiniMap.setActiveFix(FixAssistantState.getCurrentIndex());

            // Update live preview if enabled
            if (PreviewModes.isLivePreviewEnabled()) {
                PreviewModes.showFixPreview(fix);
            }
        }
    }

    function handleDecision(data) {
        const { type, index } = data;

        // Play sound
        if (type === 'accepted' || type === 'accept_group') {
            SoundEffects.play('accept');
            A11yManager.announceDecision('accepted');
        } else if (type === 'rejected' || type === 'reject_group') {
            SoundEffects.play('reject');
            A11yManager.announceDecision('rejected');
        }

        // Record for learning (async, don't wait)
        const fix = State.fixes[index];
        if (fix && (type === 'accepted' || type === 'rejected')) {
            LearnerClient.recordDecision(fix, type, data.note || '', documentId);
        }

        // Update split screen if enabled
        if (PreviewModes.isSplitScreenEnabled()) {
            PreviewModes.updateSplitScreen();
        }

        // Update UI
        updateStatistics();
        updatePageFixes();

        // Auto-save progress
        FixAssistantState.saveProgress();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // NAVIGATION HANDLERS
    // ═══════════════════════════════════════════════════════════════════════════

    function handlePageChange(pageNum) {
        updatePageFixes();
        // Update minimap viewport would go here
    }

    function handleParagraphClick(data) {
        const { index: paraIndex } = data;
        // Find fix at this paragraph and navigate to it
        const fixes = State.fixes;
        const fixIndex = fixes.findIndex(f => f.paragraph_index === paraIndex);
        if (fixIndex >= 0) {
            FixAssistantState.goToIndex(fixIndex);
        }
    }

    function handleMinimapNavigate(data) {
        const { page, paragraphIndex, fixIndex } = data;

        if (fixIndex !== undefined) {
            FixAssistantState.goToIndex(fixIndex);
        } else {
            DocumentViewer.goToPage(page);
            if (paragraphIndex !== undefined) {
                DocumentViewer.scrollToParagraph(paragraphIndex);
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // KEYBOARD SHORTCUTS
    // ═══════════════════════════════════════════════════════════════════════════

    function setupGlobalKeyboardShortcuts() {
        document.addEventListener('keydown', handleGlobalKeydown);
    }

    function handleGlobalKeydown(e) {
        // Only when Fix Assistant is open
        if (!isOpen) return;

        // Don't intercept when typing in inputs (except Escape)
        const isTyping = e.target.matches('input, textarea, select');
        
        // v3.0.109: Always allow Escape to close
        if (e.key === 'Escape') {
            close();
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        
        // Skip other shortcuts when typing
        if (isTyping) return;

        // v3.0.109: Enhanced keyboard shortcuts with visual feedback
        switch (e.key.toLowerCase()) {
            case 'a':
                flashButton(els.btnAccept);
                handleAcceptClick();
                e.preventDefault();
                break;
            case 'r':
                flashButton(els.btnReject);
                handleRejectClick();
                e.preventDefault();
                break;
            case 's':
                flashButton(els.btnSkip);
                handleSkipClick();
                e.preventDefault();
                break;
            case 'arrowleft':
                flashButton(els.btnPrev);
                FixAssistantState.goToPrevious();
                e.preventDefault();
                break;
            case 'arrowright':
                flashButton(els.btnNext);
                FixAssistantState.goToNext();
                e.preventDefault();
                break;
            case 'u':
                if (e.shiftKey) {
                    handleRedoClick();
                } else {
                    handleUndoClick();
                }
                e.preventDefault();
                break;
            case '/':
                els.searchInput?.focus();
                e.preventDefault();
                break;
            case '?':
                toggleShortcutsPanel();
                e.preventDefault();
                break;
        }
    }
    
    // v3.0.109: Visual feedback for keyboard shortcuts
    function flashButton(btn) {
        if (!btn) return;
        btn.classList.add('fav2-flash');
        setTimeout(() => btn.classList.remove('fav2-flash'), 400);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UI RENDERING
    // ═══════════════════════════════════════════════════════════════════════════

    function renderCurrentFix() {
        const fix = FixAssistantState.getCurrentFix();
        const index = FixAssistantState.getCurrentIndex();
        const total = State.fixes?.length || 0;
        const decision = FixAssistantState.getDecision(index);
        const confidenceDetails = State.reviewResults?.confidence_details?.[String(index)];

        // Update counters
        if (els.counterCurrent) els.counterCurrent.textContent = index + 1;
        if (els.counterTotal) els.counterTotal.textContent = total;
        if (els.counterCurrentDetail) els.counterCurrentDetail.textContent = index + 1;
        if (els.counterTotalDetail) els.counterTotalDetail.textContent = total;

        if (!fix) {
            // No fix to display
            if (els.changeBefore) els.changeBefore.textContent = '—';
            if (els.changeAfter) els.changeAfter.textContent = '—';
            if (els.reason) els.reason.textContent = 'No fixes to review';
            return;
        }

        // Confidence badge
        const tier = confidenceDetails?.tier || fix.confidence_tier || 'review';
        if (els.confidenceBadge) {
            els.confidenceBadge.textContent = tier.toUpperCase();
            els.confidenceBadge.className = `fav2-confidence-badge fav2-confidence-${tier}`;
        }

        // Category badge
        if (els.categoryBadge) {
            els.categoryBadge.textContent = fix.category || 'Unknown';
        }

        // Change preview
        if (els.changeBefore) els.changeBefore.textContent = fix.flagged_text || '—';
        if (els.changeAfter) els.changeAfter.textContent = fix.suggestion || '(no suggestion)';

        // Reason
        if (els.reason) {
            els.reason.textContent = fix.message || fix.reason || 'No reason provided';
        }

        // Confidence details (expandable)
        if (els.confidenceDetails && confidenceDetails) {
            const detailHtml = `
                <dl class="fav2-confidence-list">
                    <dt>Confidence Score:</dt>
                    <dd><span class="fav2-confidence-score">${Math.round((confidenceDetails.score || 0) * 100)}%</span></dd>
                    <dt>Tier:</dt>
                    <dd>${tier}</dd>
                    ${confidenceDetails.reasons?.map(r => `<dt>•</dt><dd>${escapeHtml(r)}</dd>`).join('') || ''}
                </dl>
            `;
            els.confidenceDetails.innerHTML = detailHtml;
        }

        // Reviewer note
        if (els.reviewerNote) {
            els.reviewerNote.value = decision?.note || '';
        }

        // Update page fixes list
        updatePageFixes();

        // Announce for screen readers
        A11yManager.announceFix(
            { ...fix, confidence_tier: tier },
            index + 1,
            total
        );
    }

    function updatePageFixes() {
        if (!els.pageFixesList) return;

        const currentFix = FixAssistantState.getCurrentFix();
        const currentPage = currentFix?.page || 1;
        const currentIndex = FixAssistantState.getCurrentIndex();

        // Get fixes on current page
        const fixesOnPage = State.fixes.filter(f => (f.page || 1) === currentPage);

        if (fixesOnPage.length === 0) {
            els.pageFixesList.innerHTML = '<li class="fav2-page-fix-empty">No fixes on this page</li>';
            return;
        }

        const html = fixesOnPage.map(fix => {
            const idx = State.fixes.indexOf(fix);
            const decision = FixAssistantState.getDecision(idx);
            const isCurrent = idx === currentIndex;

            let statusClass = '';
            let statusText = '';
            if (decision?.decision === 'accepted') {
                statusClass = 'fav2-status-accepted';
                statusText = '✓';
            } else if (decision?.decision === 'rejected') {
                statusClass = 'fav2-status-rejected';
                statusText = '✗';
            }

            return `
                <li class="fav2-page-fix-item ${isCurrent ? 'fav2-page-fix-current' : ''} ${statusClass}"
                    role="option"
                    aria-selected="${isCurrent}"
                    data-fix-index="${idx}">
                    <span class="fav2-page-fix-text">${escapeHtml(fix.flagged_text || 'Fix')}</span>
                    ${statusText ? `<span class="fav2-page-fix-status">${statusText}</span>` : ''}
                    ${isCurrent ? '<span class="fav2-page-fix-indicator">(current)</span>' : ''}
                </li>
            `;
        }).join('');

        els.pageFixesList.innerHTML = html;

        // Update page fix count in heading
        const countEl = document.querySelector('.fav2-page-fix-count');
        if (countEl) countEl.textContent = fixesOnPage.length;
    }

    function updateStatistics() {
        const stats = FixAssistantState.getStatistics();

        if (els.statAccepted) els.statAccepted.textContent = stats.accepted || 0;
        if (els.statRejected) els.statRejected.textContent = stats.rejected || 0;
        if (els.statPending) els.statPending.textContent = stats.pending || 0;
    }

    function updateProgress() {
        const percent = FixAssistantState.getProgressPercent();
        const stats = FixAssistantState.getStatistics();
        const total = (stats.accepted || 0) + (stats.rejected || 0) + (stats.pending || 0);
        const reviewed = (stats.accepted || 0) + (stats.rejected || 0);

        // v3.0.109: Update progress bar width
        if (els.progressFill) {
            els.progressFill.style.width = `${percent}%`;
        }
        
        // v3.0.109: Update progress text
        if (els.progressText) {
            els.progressText.innerHTML = `<span id="fav2-counter-current">${reviewed}</span> of <span id="fav2-counter-total">${total}</span> reviewed`;
        }
        
        // v3.0.109: Update header counters (current position)
        const currentIndex = FixAssistantState.getCurrentIndex();
        if (els.counterCurrent) els.counterCurrent.textContent = currentIndex + 1;
        if (els.counterTotal) els.counterTotal.textContent = total;

        // Check for completion
        if (percent >= 100 && total > 0) {
            SoundEffects.play('complete');
            A11yManager.announce('Review complete! All fixes have been reviewed.');
            
            // v3.0.109: Add completion animation
            if (els.progressFill) {
                els.progressFill.classList.add('fav2-complete-animation');
            }
        }
    }

    function updateUndoRedoButtons() {
        if (els.btnUndo) {
            els.btnUndo.disabled = !FixAssistantState.canUndo();
        }
        if (els.btnRedo) {
            els.btnRedo.disabled = !FixAssistantState.canRedo();
        }
    }

    function scrollToCurrentFix() {
        const fix = FixAssistantState.getCurrentFix();
        if (!fix) {
            console.warn('[TWR FixAssistant] scrollToCurrentFix: No current fix');
            return;
        }

        // v3.0.112: Get decision status for highlight coloring
        // Note: fix doesn't have .index property, use getCurrentIndex() instead
        const currentIndex = FixAssistantState.getCurrentIndex();
        const decision = FixAssistantState.getDecision(currentIndex);
        const decisionStatus = decision?.decision || 'pending';

        console.log('[TWR FixAssistant] scrollToCurrentFix:', {
            paragraph_index: fix.paragraph_index,
            flagged_text: fix.flagged_text,
            currentIndex: currentIndex,
            decision: decisionStatus
        });

        // v3.0.112: Scroll document viewer to the fix with decision status
        if (typeof DocumentViewer !== 'undefined' && typeof DocumentViewer.scrollToParagraph === 'function') {
            const result = DocumentViewer.scrollToParagraph(fix.paragraph_index, fix.flagged_text, decisionStatus);
            console.log('[TWR FixAssistant] scrollToParagraph result:', result);
        } else {
            console.warn('[TWR FixAssistant] DocumentViewer.scrollToParagraph not available');
        }

        // v3.0.109: Also scroll the page fixes list to show current item
        scrollPageFixesListToCurrentItem();
    }
    
    // v3.0.109: Scroll the page fixes list to show the current item
    function scrollPageFixesListToCurrentItem() {
        if (!els.pageFixesList) return;
        
        const currentItem = els.pageFixesList.querySelector('.fav2-page-fix-current');
        if (currentItem) {
            currentItem.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }

    function autoAdvance() {
        // Automatically go to next pending fix after decision
        const stats = FixAssistantState.getStatistics();
        if (stats.pending > 0) {
            FixAssistantState.goToNext(true); // skip decided
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MODAL & PANEL MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════

    function showModal() {
        // v3.0.110: Enhanced modal display with fallback element selection
        const modal = els.modal || document.getElementById('fav2-modal');
        if (modal) {
            // v3.0.110: Close any other open modals first to prevent visual bleed-through
            document.querySelectorAll('.modal.active').forEach(otherModal => {
                if (otherModal.id !== 'fav2-modal') {
                    otherModal.classList.remove('active');
                    console.log('[TWR FixAssistant] Closed conflicting modal:', otherModal.id);
                }
            });

            // Force display first
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            modal.style.opacity = '1';
            modal.classList.add('fav2-modal-visible');
            document.body.classList.add('fav2-modal-open');
            
            // v3.0.109: Focus trap - focus the first actionable element
            setTimeout(() => {
                const firstFocusable = modal.querySelector('button:not([disabled]), input:not([disabled]), [tabindex="0"]');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }, 100);

            // Re-initialize Lucide icons if available
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            
            console.log('[TWR FixAssistant] Modal shown successfully');
        } else {
            console.error('[TWR FixAssistant] Modal element #fav2-modal not found!');
        }
    }

    function hideModal() {
        // v3.0.109: Enhanced modal hide with fallback element selection
        const modal = els.modal || document.getElementById('fav2-modal');
        if (modal) {
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.classList.remove('fav2-modal-visible');
            document.body.classList.remove('fav2-modal-open');
            console.log('[TWR FixAssistant] Modal hidden');
        }
    }

    function toggleShortcutsPanel() {
        if (els.shortcutsPanel) {
            const isHidden = els.shortcutsPanel.hidden;
            els.shortcutsPanel.hidden = !isHidden;
            els.btnShortcuts?.setAttribute('aria-pressed', String(isHidden));
        }
    }

    function hideShortcutsPanel() {
        if (els.shortcutsPanel) {
            els.shortcutsPanel.hidden = true;
            els.btnShortcuts?.setAttribute('aria-pressed', 'false');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // FINISH REVIEW & EXPORT
    // ═══════════════════════════════════════════════════════════════════════════

    function handleFinishReview() {
        const stats = FixAssistantState.getStatistics();

        // Check if there are pending fixes
        if (stats.pending > 0) {
            const proceed = confirm(
                `You have ${stats.pending} pending fixes.\n\n` +
                `• ${stats.accepted} accepted\n` +
                `• ${stats.rejected} rejected\n` +
                `• ${stats.pending} pending\n\n` +
                `Pending fixes will be left unchanged. Continue?`
            );
            if (!proceed) return;
        }

        // Offer report generation
        const generateReport = confirm(
            'Would you like to generate a PDF summary report?\n\n' +
            'The report includes statistics, accepted/rejected fixes, and any notes.'
        );

        if (generateReport) {
            generateSummaryReport();
        }

        // Close and trigger export
        // v5.9.4: Flag to skip close()'s export modal re-show (fixAssistantDone handles it)
        _closingForFinish = true;
        close();

        // v5.9.4: Update global State with selected fixes
        // getSelectedFixes() returns array of objects — use actual fix indices from decisions Map
        State.selectedFixes = new Set();
        const allFixes = State.fixes || [];
        allFixes.forEach((fix, originalIdx) => {
            const decision = FixAssistantState.getDecision(originalIdx);
            if (decision && decision.decision === 'accepted') {
                State.selectedFixes.add(originalIdx);
            }
        });

        // Emit event for export integration
        const selectedFixesList = getSelectedFixes();
        const rejectedFixesList = getRejectedFixes();
        document.dispatchEvent(new CustomEvent('fixAssistantDone', {
            detail: {
                selectedFixes: selectedFixesList,
                rejectedFixes: rejectedFixesList,
                statistics: stats,
                reviewRole: FixAssistantState.getReviewRole()  // v6.0.2
            }
        }));
    }

    async function generateSummaryReport() {
        try {
            showNotification('Generating report...', 'info');

            const reviewData = ReportClient.buildReviewData(
                FixAssistantState,
                sessionStartTime,
                documentScoreBefore
            );

            const result = await ReportClient.generateReport({
                documentName: State.filename || 'document',
                reviewerName: '', // Could prompt user
                reviewData: reviewData,
                onProgress: (msg) => console.log('[TWR Report]', msg),
                onError: (err) => showNotification(`Report error: ${err}`, 'error')
            });

            if (result.success) {
                showNotification('Report downloaded', 'success');
            }
        } catch (e) {
            console.error('[TWR FixAssistant] Report generation failed:', e);
            showNotification('Report generation failed', 'error');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // EXPORT API (for external integration)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Get accepted fixes formatted for the markup engine
     * This is the existing interface that other parts of the app call
     */
    function getSelectedFixes() {
        if (!FixAssistantState.isInitialized()) {
            // Fallback to legacy behavior
            return Array.from(State.selectedFixes || []).map(idx => State.fixes[idx]).filter(Boolean);
        }
        return FixAssistantState.getSelectedFixes();
    }

    /**
     * Get rejected fixes formatted for adding as comments (NEW for v2)
     */
    function getRejectedFixes() {
        if (!FixAssistantState.isInitialized()) {
            return [];
        }
        return FixAssistantState.getRejectedFixes();
    }

    /**
     * Get all export data (accepted, rejected, pending)
     */
    function getExportData() {
        if (!FixAssistantState.isInitialized()) {
            return { accepted: [], rejected: [], pending: [] };
        }
        return FixAssistantState.getExportData();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function showNotification(message, type = 'info') {
        // Use TWR's existing notification system if available
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else if (typeof Notifications !== 'undefined' && Notifications.show) {
            Notifications.show(message, type);
        } else {
            console.log(`[TWR Notification] ${type}: ${message}`);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    return {
        // Lifecycle
        init,
        open,
        close,

        // Export interface (existing API preserved)
        getSelectedFixes,

        // New v2 export methods
        getRejectedFixes,
        getExportData,

        // Status
        isOpen: () => isOpen,
        
        // v3.0.97b: Action methods for external button handlers
        acceptCurrent: () => { if (isOpen) handleAcceptClick(); },
        rejectCurrent: () => { if (isOpen) handleRejectClick(); },
        skipCurrent: () => { if (isOpen) handleSkipClick(); },
        goToPrevious: () => { if (isOpen) handlePrevClick(); },
        goToNext: () => { if (isOpen) handleNextClick(); },
        acceptAllSafe: () => { if (isOpen) handleAcceptSafeClick(); },
        acceptAll: () => { if (isOpen) handleAcceptAllClick(); },
        rejectAll: () => {
            // v3.0.97b: Reject all pending fixes
            if (!isOpen) return;
            if (confirm('Reject all remaining pending fixes?')) {
                const stats = FixAssistantState.getStatistics();
                let count = 0;
                // Get all pending fix indices and reject them
                const allFixes = State.fixes || [];
                allFixes.forEach((fix, idx) => {
                    const decision = FixAssistantState.getDecision(idx);
                    if (!decision) {
                        FixAssistantState.reject(idx, '');
                        count++;
                    }
                });
                if (count > 0) {
                    showNotification(`Rejected ${count} fixes`, 'info');
                    SoundEffects.play('reject');
                }
            }
        }
    };
})();

// Register globally
window.FixAssistant = FixAssistant;

// Render the tiered fix preview (legacy - now redirects to Fix Assistant)
function renderTieredFixPreview() {
    const fixable = State.issues.filter(i => i.suggestion && i.suggestion !== '-' && i.flagged_text);
    const container = document.getElementById('fixable-list');
    const countEl = document.getElementById('fixable-count');
    const totalEl = document.getElementById('total-fix-count');
    
    if (countEl) countEl.textContent = fixable.length;
    if (totalEl) totalEl.textContent = fixable.length;
    
    // v3.0.97: Guard against missing container (removed in Fix Assistant v2 refactor)
    if (!container) {
        console.log('[TWR Export] fixable-list container not found - using Fix Assistant launcher');
        return;
    }
    
    if (fixable.length === 0) {
        container.innerHTML = '<p class="fix-preview-empty">No auto-fixable issues found</p>';
        return;
    }
    
    // Store fixable issues and initialize selection
    State.fixableIssues = fixable;
    State.selectedFixes = new Set();
    
    // Classify fixes by tier
    const tiers = { safe: [], review: [], manual: [] };
    fixable.forEach((fix, idx) => {
        const tier = classifyFixConfidence(fix);
        tiers[tier].push({ fix, idx });
    });
    
    // Group fixes within each tier
    let html = '';
    
    for (const [tierName, tierConfig] of Object.entries(FixConfidenceTiers)) {
        const tierFixes = tiers[tierName];
        if (tierFixes.length === 0) continue;
        
        // Group similar fixes
        const groups = groupFixesByPattern(tierFixes.map(f => f.fix));
        
        // Select safe fixes by default
        if (tierName === 'safe') {
            tierFixes.forEach(f => State.selectedFixes.add(f.idx));
        }
        
        html += `
            <div class="fix-tier" data-tier="${tierName}">
                <div class="fix-tier-header" onclick="toggleFixTier('${tierName}')">
                    <div class="fix-tier-info">
                        <span class="fix-tier-indicator" style="background: ${tierConfig.color}"></span>
                        <span class="fix-tier-label">${tierConfig.label}</span>
                        <span class="fix-tier-count">${tierFixes.length}</span>
                    </div>
                    <div class="fix-tier-actions">
                        ${tierName === 'safe' ? `
                            <button class="btn btn-sm btn-success" onclick="selectTierFixes('${tierName}', true, event)">
                                <i data-lucide="check-circle"></i> Apply All Safe
                            </button>
                        ` : ''}
                        <i data-lucide="chevron-down" class="fix-tier-chevron"></i>
                    </div>
                </div>
                <div class="fix-tier-description">${tierConfig.description}</div>
                <div class="fix-tier-content">
        `;
        
        // Render grouped fixes
        let groupIdx = 0;
        for (const [patternKey, group] of groups) {
            const count = group.fixes.length;
            const rep = group.representative;
            const firstIdx = tierFixes.find(f => f.fix === rep)?.idx ?? 0;
            const allIndices = group.fixes.map(f => tierFixes.find(tf => tf.fix === f)?.idx).filter(i => i !== undefined);
            
            if (count > 1) {
                // Grouped display
                html += `
                    <div class="fix-group" data-indices="${allIndices.join(',')}">
                        <div class="fix-group-header">
                            <input type="checkbox" id="fix-group-${tierName}-${groupIdx}" 
                                   ${tierName === 'safe' ? 'checked' : ''} 
                                   onchange="toggleFixGroup(this, [${allIndices.join(',')}])">
                            <label for="fix-group-${tierName}-${groupIdx}">
                                <span class="fix-group-count">${count}×</span>
                                <span class="fix-group-category">${escapeHtml(group.category)}</span>
                            </label>
                        </div>
                        <div class="fix-group-example">
                            <span class="fix-from">${escapeHtml(truncate(rep.flagged_text, 25))}</span>
                            <span class="fix-arrow">→</span>
                            <span class="fix-to">${escapeHtml(truncate(rep.suggestion, 25))}</span>
                        </div>
                    </div>
                `;
            } else {
                // Single fix
                html += `
                    <div class="fix-preview-item">
                        <input type="checkbox" id="fix-${firstIdx}" 
                               ${tierName === 'safe' ? 'checked' : ''} 
                               onchange="toggleFix(${firstIdx})">
                        <label for="fix-${firstIdx}" class="fix-preview-item-text">
                            <span class="fix-from">${escapeHtml(truncate(rep.flagged_text, 30))}</span>
                            <span class="fix-arrow">→</span>
                            <span class="fix-to">${escapeHtml(truncate(rep.suggestion, 30))}</span>
                        </label>
                    </div>
                `;
            }
            groupIdx++;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    updateSelectedFixCount();
}

// Toggle tier collapse/expand
function toggleFixTier(tierName) {
    const tier = document.querySelector(`.fix-tier[data-tier="${tierName}"]`);
    if (tier) {
        tier.classList.toggle('collapsed');
    }
}

// Select/deselect all fixes in a tier
function selectTierFixes(tierName, select, event) {
    if (event) event.stopPropagation();
    
    const tier = document.querySelector(`.fix-tier[data-tier="${tierName}"]`);
    if (!tier) return;
    
    tier.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = select;
        // Extract indices from the checkbox
        const match = cb.id.match(/fix-(\d+)/);
        if (match) {
            const idx = parseInt(match[1]);
            if (select) State.selectedFixes.add(idx);
            else State.selectedFixes.delete(idx);
        }
    });
    
    // Also handle group checkboxes
    tier.querySelectorAll('.fix-group').forEach(group => {
        const indices = group.dataset.indices?.split(',').map(i => parseInt(i)) || [];
        indices.forEach(idx => {
            if (select) State.selectedFixes.add(idx);
            else State.selectedFixes.delete(idx);
        });
    });
    
    updateSelectedFixCount();
}

// Toggle a group of fixes
function toggleFixGroup(checkbox, indices) {
    indices.forEach(idx => {
        if (checkbox.checked) {
            State.selectedFixes.add(idx);
        } else {
            State.selectedFixes.delete(idx);
        }
    });
    updateSelectedFixCount();
}

// Legacy function - now calls tiered version
function populateFixPreview() {
    renderTieredFixPreview();
}

function toggleFix(idx) {
    if (State.selectedFixes.has(idx)) {
        State.selectedFixes.delete(idx);
    } else {
        State.selectedFixes.add(idx);
    }
    updateSelectedFixCount();
}

function selectAllFixes(select) {
    if (!State.fixableIssues) return;
    
    State.fixableIssues.forEach((_, idx) => {
        const checkbox = document.getElementById(`fix-${idx}`);
        if (checkbox) {
            checkbox.checked = select;
        }
        if (select) {
            State.selectedFixes.add(idx);
        } else {
            State.selectedFixes.delete(idx);
        }
    });
    
    // Also update group checkboxes
    document.querySelectorAll('.fix-group input[type="checkbox"]').forEach(cb => {
        cb.checked = select;
    });
    
    updateSelectedFixCount();
}

function updateSelectedFixCount() {
    const selectedEl = document.getElementById('selected-fix-count');
    if (selectedEl) {
        selectedEl.textContent = State.selectedFixes?.size || 0;
    }
}

// ============================================================
// v2.9.9: SCORE BREAKDOWN MODAL (#47 - Actionable Quality Score)
// ============================================================

/**
 * Show the score breakdown modal with component details and improvement suggestions.
 */
function showScoreBreakdown() {
    if (!State.reviewResults) {
        toast('info', 'Scan a document first to see score breakdown');
        return;
    }
    
    const healthScore = State.reviewResults.enhanced_stats?.health_score || 
                       State.reviewResults.health_score || 
                       { total: State.reviewResults.score || 0, breakdown: {}, grade: State.reviewResults.grade || 'N/A' };
    
    const score = healthScore.total ?? State.reviewResults.score ?? 0;
    const grade = healthScore.grade ?? State.reviewResults.grade ?? '--';
    const breakdown = healthScore.breakdown || {};
    
    // Update main score display
    const scoreEl = document.getElementById('score-breakdown-value');
    const gradeEl = document.getElementById('score-breakdown-grade');
    if (scoreEl) {
        scoreEl.textContent = Math.round(score);
        scoreEl.style.color = getScoreColor(score);
    }
    if (gradeEl) {
        gradeEl.textContent = `Grade: ${grade}`;
        gradeEl.style.color = getScoreColor(score);
    }
    
    // Update component bars
    const components = [
        { id: 'severity', max: 50, value: breakdown.severity_impact ?? 25 },
        { id: 'readability', max: 15, value: breakdown.readability ?? 10 },
        { id: 'structure', max: 20, value: breakdown.structure ?? 10 },
        { id: 'completeness', max: 15, value: breakdown.completeness ?? 10 }
    ];
    
    components.forEach(comp => {
        const valueEl = document.getElementById(`score-comp-${comp.id}`);
        const barEl = document.getElementById(`score-bar-${comp.id}`);
        if (valueEl) valueEl.textContent = `${Math.round(comp.value)}/${comp.max}`;
        if (barEl) barEl.style.width = `${(comp.value / comp.max) * 100}%`;
    });
    
    // Generate improvement suggestions based on data
    const suggestions = generateImprovementSuggestions(State.reviewResults, breakdown);
    const listEl = document.getElementById('score-improvements-list');
    if (listEl) {
        // SAFE: suggestions generated internally with hardcoded strings; escaped for defense
        listEl.innerHTML = suggestions.map(s => `
            <li style="display: flex; align-items: flex-start; gap: var(--space-2); padding: var(--space-2); background: var(--bg-secondary); border-radius: var(--radius-md);">
                <i data-lucide="${escapeHtml(s.icon)}" style="width: 16px; height: 16px; flex-shrink: 0; color: ${s.color};"></i>
                <div>
                    <strong style="font-size: var(--font-size-sm);">${escapeHtml(s.title)}</strong>
                    <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin: 0;">${escapeHtml(s.desc)}</p>
                </div>
            </li>
        `).join('');
    }
    
    showModal('modal-score-breakdown');
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

/**
 * Generate actionable improvement suggestions based on review data.
 */
function generateImprovementSuggestions(data, breakdown) {
    const suggestions = [];
    const bySeverity = data.by_severity || {};
    const byCategory = data.by_category || {};
    
    // Priority 1: Critical and High severity issues
    const criticalCount = bySeverity['Critical'] || 0;
    const highCount = bySeverity['High'] || 0;
    
    if (criticalCount > 0) {
        suggestions.push({
            icon: 'alert-octagon',
            color: 'var(--danger)',
            title: `Fix ${criticalCount} Critical issue${criticalCount > 1 ? 's' : ''}`,
            desc: 'Critical issues have the highest impact on your score. Address these first.'
        });
    }
    
    if (highCount > 0) {
        suggestions.push({
            icon: 'alert-triangle',
            color: 'var(--warning)',
            title: `Address ${highCount} High severity issue${highCount > 1 ? 's' : ''}`,
            desc: 'High severity issues should be resolved before publication.'
        });
    }
    
    // Priority 2: Top category
    const topCategories = Object.entries(byCategory).sort((a, b) => b[1] - a[1]).slice(0, 2);
    if (topCategories.length > 0 && topCategories[0][1] > 3) {
        suggestions.push({
            icon: 'layers',
            color: 'var(--info)',
            title: `Focus on ${topCategories[0][0]} (${topCategories[0][1]} issues)`,
            desc: 'This category has the most issues. Consider a targeted review.'
        });
    }
    
    // Priority 3: Structure suggestions
    if (breakdown.structure !== undefined && breakdown.structure < 15) {
        suggestions.push({
            icon: 'layout',
            color: 'var(--accent)',
            title: 'Improve document structure',
            desc: 'Add a table of contents, clear headings, and organize into sections.'
        });
    }
    
    // Priority 4: Readability
    const readability = data.readability || {};
    if (readability.flesch_kincaid_grade > 18) {
        suggestions.push({
            icon: 'book-open',
            color: 'var(--warning)',
            title: 'Simplify complex sentences',
            desc: `Current grade level (${readability.flesch_kincaid_grade?.toFixed(1)}) may be too complex. Aim for grade 12-16.`
        });
    }
    
    // Default if no specific suggestions
    if (suggestions.length === 0) {
        suggestions.push({
            icon: 'check-circle',
            color: 'var(--success)',
            title: 'Great job!',
            desc: 'Your document is in good shape. Continue reviewing medium and low severity issues.'
        });
    }
    
    return suggestions.slice(0, 4); // Max 4 suggestions
}

window.showScoreBreakdown = showScoreBreakdown;

// ============================================================
// TRIAGE MODE - Now in TWR.Triage module (features/triage.js)
// ============================================================

// ============================================================
// ISSUE FAMILIES - Now in TWR.Families module (features/families.js)
// ============================================================
// Functions moved to module:
// - buildIssueFamilies()
// - extractMessagePattern()
// - showInlineFamiliesPanel()
// - renderInlineFamilyList()
// - getFamilyDisplayName()
// - filterByFamily()
// - clearFamilyFilter()
// - initFamiliesPanel()
// - showIssueFamilies()
// - renderFamilyList()
// - familyAction()
// - selectFamily()
// - createFamiliesModal()

// updateTriageFamilyInfo - Now in TWR.Triage module (features/triage.js)

// ============================================================
// REVIEW LOG / AUDIT TRAIL
// ============================================================

/**
 * Log a review decision for audit trail
 */
function logReviewDecision(issueId, action, note = '', reviewer = 'Reviewer') {
    const entry = {
        issue_id: issueId,
        action,
        note,
        reviewer,
        timestamp: new Date().toISOString()
    };
    
    // Remove any existing entry for this issue (update, don't duplicate)
    State.workflow.reviewLog = State.workflow.reviewLog.filter(e => e.issue_id !== issueId);
    State.workflow.reviewLog.push(entry);
    
    // Update review log count in UI
    updateReviewLogBadge();
}

/**
 * Update the review log badge count
 */
function updateReviewLogBadge() {
    const badge = document.getElementById('review-log-badge');
    if (badge) {
        const count = State.workflow.reviewLog.length;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-flex' : 'none';
    }
}

/**
 * Show the review log modal
 */
function showReviewLog() {
    const container = document.getElementById('review-log-list');
    if (!container) return;
    
    if (State.workflow.reviewLog.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="clipboard-list"></i>
                <p>No review decisions logged yet.</p>
                <p class="text-muted">Use Triage Mode or Family Actions to log decisions.</p>
            </div>
        `;
    } else {
        // Group by action for summary
        const summary = { keep: 0, suppress: 0, fixed: 0 };
        State.workflow.reviewLog.forEach(e => {
            if (summary[e.action] !== undefined) summary[e.action]++;
        });
        
        container.innerHTML = `
            <div class="review-log-summary">
                <span class="log-stat keep"><i data-lucide="check"></i> ${summary.keep} kept</span>
                <span class="log-stat suppress"><i data-lucide="eye-off"></i> ${summary.suppress} suppressed</span>
                <span class="log-stat fixed"><i data-lucide="check-circle"></i> ${summary.fixed} fixed</span>
            </div>
            <div class="review-log-entries">
                ${State.workflow.reviewLog.slice().reverse().map(entry => {
                    const issue = State.issues.find(i => i.issue_id === entry.issue_id);
                    return `
                        <div class="log-entry log-${entry.action}">
                            <div class="log-action-badge ${entry.action}">${entry.action}</div>
                            <div class="log-details">
                                <div class="log-message">${escapeHtml(truncate(issue?.message || `Issue ${entry.issue_id}`, 60))}</div>
                                ${entry.note ? `<div class="log-note text-muted">${escapeHtml(entry.note)}</div>` : ''}
                                <div class="log-meta text-muted">${formatTimestamp(entry.timestamp)}</div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    showModal('modal-review-log');
}

/**
 * Export review log as CSV
 */
function exportReviewLog() {
    if (State.workflow.reviewLog.length === 0) {
        toast('warning', 'No review decisions to export');
        return;
    }
    
    const headers = ['Timestamp', 'Issue ID', 'Action', 'Message', 'Category', 'Severity', 'Note', 'Reviewer'];
    const rows = State.workflow.reviewLog.map(entry => {
        const issue = State.issues.find(i => i.issue_id === entry.issue_id) || {};
        return [
            entry.timestamp,
            entry.issue_id,
            entry.action,
            `"${(issue.message || '').replace(/"/g, '""')}"`,
            issue.category || '',
            issue.severity || '',
            `"${(entry.note || '').replace(/"/g, '""')}"`,
            entry.reviewer
        ].join(',');
    });
    
    const csv = [headers.join(','), ...rows].join('\n');
    downloadCSV(csv, `review_log_${State.filename || 'document'}_${new Date().toISOString().slice(0,10)}.csv`);
    toast('success', `Exported ${State.workflow.reviewLog.length} review decisions`);
}

/**
 * Clear the review log
 */
function clearReviewLog() {
    if (confirm('Clear all review decisions? This cannot be undone.')) {
        State.workflow.reviewLog = [];
        updateReviewLogBadge();
        showReviewLog();
        toast('info', 'Review log cleared');
    }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// createFamiliesModal - Now in TWR.Families module (features/families.js)

/**
 * Create the review log modal dynamically if needed
 */
function createReviewLogModal() {
    if (document.getElementById('modal-review-log')) return;
    
    const modal = document.createElement('div');
    modal.className = 'modal modal-lg';
    modal.id = 'modal-review-log';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3><i data-lucide="clipboard-list"></i> Review Log (Audit Trail)</h3>
                <button class="btn btn-ghost modal-close" aria-label="Close"><i data-lucide="x"></i></button>
            </div>
            <div class="modal-body">
                <div id="review-log-list"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="clearReviewLog()">
                    <i data-lucide="trash-2"></i> Clear
                </button>
                <button class="btn btn-primary" onclick="exportReviewLog()">
                    <i data-lucide="download"></i> Export CSV
                </button>
                <button class="btn btn-ghost modal-close">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Initialize workflow modals (families modal now handled by TWR.Families module)
document.addEventListener('DOMContentLoaded', () => {
    // createFamiliesModal() - handled by TWR.Families.init()
    createReviewLogModal();
});

// triageAction review logging - Now integrated in TWR.Triage module (features/triage.js)

// Export workflow functions (families functions now exported by TWR.Families module)
// window.showIssueFamilies = handled by TWR.Families
// window.familyAction = handled by TWR.Families
// window.selectFamily = handled by TWR.Families
window.showReviewLog = showReviewLog;
window.exportReviewLog = exportReviewLog;
window.clearReviewLog = clearReviewLog;

// ============================================================
// ENHANCED SELECTION CONTROLS
// ============================================================
function initSelectionDropdown() {
    const menuBtn = document.getElementById('btn-select-menu');
    const dropdown = document.getElementById('select-dropdown');
    
    if (!menuBtn || !dropdown) return;
    
    // Toggle dropdown
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    });
    
    // Close on outside click
    document.addEventListener('click', () => {
        dropdown.style.display = 'none';
    });
    
    // Selection actions
    document.getElementById('btn-select-page')?.addEventListener('click', () => {
        selectIssuesOnPage();
        dropdown.style.display = 'none';
    });
    
    document.getElementById('btn-select-filtered')?.addEventListener('click', () => {
        selectAllFiltered();
        dropdown.style.display = 'none';
    });
    
    document.getElementById('btn-select-none-menu')?.addEventListener('click', () => {
        selectIssues('none');
        dropdown.style.display = 'none';
    });
}

function selectIssuesOnPage() {
    const pageSize = State.settings.pageSize === 'all' ? State.filteredIssues.length : State.settings.pageSize;
    const start = (State.currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, State.filteredIssues.length);
    
    for (let i = start; i < end; i++) {
        const issue = State.filteredIssues[i];
        // v3.0.35 Fix: Use same key format as toggleIssueSelection
        const key = getIssueKey(issue, i);
        State.selectedIssues.add(key);
    }
    
    renderIssuesList();
    updateSelectionCount();
}

function selectAllFiltered() {
    const count = State.filteredIssues.length;
    
    // Show confirmation for large selections
    if (count > 500) {
        document.getElementById('bulk-count').textContent = count;
        showModal('modal-bulk-confirm');
        
        // Set up confirmation handler
        document.getElementById('btn-confirm-bulk').onclick = () => {
            doSelectAllFiltered();
            closeModals();
        };
    } else {
        doSelectAllFiltered();
    }
}

function doSelectAllFiltered() {
    State.filteredIssues.forEach((issue, i) => {
        // v3.0.35 Fix: Use same key format as toggleIssueSelection
        const key = getIssueKey(issue, i);
        State.selectedIssues.add(key);
    });
    
    renderIssuesList();
    updateSelectionCount();
}

/**
 * Get canonical selection key for an issue.
 * v3.0.35: Centralized to prevent key mismatch bugs.
 * 
 * @param {Object} issue - The issue object
 * @param {number} filteredIndex - Index in State.filteredIssues
 * @returns {string|number} - The canonical key for selection tracking
 */
function getIssueKey(issue, filteredIndex) {
    return issue?.issue_id ?? filteredIndex;
}

function updateSelectionCount() {
    const countEl = document.getElementById('selection-count');
    if (countEl) {
        countEl.textContent = `${State.selectedIssues.size} selected`;
    }
    
    const filteredTotal = document.getElementById('filtered-total');
    if (filteredTotal) {
        filteredTotal.textContent = State.filteredIssues.length;
    }
}

// ============================================================
// EXPANDABLE ISSUE ROWS (Delegated to TWR.Renderers)
// ============================================================
function toggleIssueExpand(index, event) {
    if (window.TWR?.Renderers?.toggleIssueExpand) {
        return TWR.Renderers.toggleIssueExpand(index, event);
    }
    // No fallback - expansion just won't work
}

/**
 * Get "Why it matters" explanation based on issue category and severity
 * Delegated to TWR.Renderers module.
 */
function getWhyItMatters(issue) {
    if (window.TWR?.Renderers?.getWhyItMatters) {
        return TWR.Renderers.getWhyItMatters(issue);
    }
    return null;
}

// ============================================================
// INIT EVENT LISTENERS FOR NEW FEATURES
// ============================================================
function initNewFeatureListeners() {
    // Scan History
    document.getElementById('btn-scan-history')?.addEventListener('click', showScanHistoryModal);
    document.getElementById('btn-refresh-history')?.addEventListener('click', loadScanHistory);
    
    // Scan Profiles
    document.getElementById('btn-save-profile')?.addEventListener('click', showSaveProfileModal);
    document.getElementById('btn-confirm-save-profile')?.addEventListener('click', saveCurrentProfile);
    
    // Fix preview controls (legacy - now handled by Fix Assistant)
    document.getElementById('btn-select-all-fixes')?.addEventListener('click', () => selectAllFixes(true));
    document.getElementById('btn-deselect-all-fixes')?.addEventListener('click', () => selectAllFixes(false));
    
    // v3.0.96: Fix Assistant event handlers
    document.getElementById('btn-open-fix-assistant')?.addEventListener('click', () => {
        console.log('[TWR] Fix Assistant button clicked, FixAssistant available:', !!window.FixAssistant);
        if (window.FixAssistant) {
            FixAssistant.open();
        } else {
            console.error('[TWR] FixAssistant not available on window');
            if (typeof toast === 'function') {
                toast('error', 'Fix Assistant not loaded');
            }
        }
    });
    document.getElementById('btn-fix-accept')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.acceptCurrent();
    });
    document.getElementById('btn-fix-reject')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.rejectCurrent();
    });
    document.getElementById('btn-fix-skip')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.skipCurrent();
    });
    document.getElementById('btn-fix-prev')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.goToPrevious();
    });
    document.getElementById('btn-fix-next')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.goToNext();
    });
    document.getElementById('btn-accept-all-safe')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.acceptAllSafe();
    });
    document.getElementById('btn-accept-all')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.acceptAll();
    });
    document.getElementById('btn-reject-all')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.rejectAll();
    });
    document.getElementById('btn-fix-assistant-done')?.addEventListener('click', () => {
        if (window.FixAssistant) FixAssistant.close();
    });
    
    // v3.0.111: Checkbox no longer controls launcher visibility (consolidated UI)
    // Launcher is always visible, checkbox controls whether fixes are applied on export
    document.getElementById('export-apply-fixes')?.addEventListener('change', (e) => {
        if (e.target.checked && window.FixAssistant) {
            FixAssistant.init();
        }
    });

    // v5.9.4: Export format radio change → update UI (show/hide fixes, update filter preview)
    document.querySelectorAll('input[name="export-format"]').forEach(radio => {
        radio.addEventListener('change', updateExportOptions);
    });

    // v5.9.4: Export mode radio change → update filter preview count
    document.querySelectorAll('input[name="export-mode"]').forEach(radio => {
        radio.addEventListener('change', _updateExportFilterPreview);
    });

    // v5.9.4: Fix Assistant Done → update export modal launcher stats and re-show export modal
    document.addEventListener('fixAssistantDone', (e) => {
        const detail = e.detail || {};
        const selectedCount = detail.selectedFixes?.length || 0;
        const rejectedCount = detail.rejectedFixes?.length || 0;
        const stats = detail.statistics || {};

        console.log('[TWR Export] Fix Assistant done:', { selectedCount, rejectedCount, stats });

        // Re-show the export modal (Fix Assistant's showModal() closes it on open)
        // Use setTimeout to ensure Fix Assistant modal is fully hidden first
        setTimeout(() => {
            showModal('modal-export');

            // Update launcher stat badges in export modal
            const selectedEl = document.getElementById('selected-fix-count');
            if (selectedEl) selectedEl.textContent = selectedCount;

            // Update fixable count to show total reviewed (accepted + rejected)
            const fixableEl = document.getElementById('fixable-count');
            if (fixableEl) {
                const totalFixes = (State.fixes || []).length;
                fixableEl.textContent = totalFixes;
            }

            // Auto-check the "Apply selected fixes" checkbox if fixes were selected
            const applyFixesCb = document.getElementById('export-apply-fixes');
            if (applyFixesCb && selectedCount > 0) {
                applyFixesCb.checked = true;
            }

            // Update the legacy State.selectedFixes count display
            updateSelectedFixCount();

            // Re-initialize Lucide icons in the export modal
            if (typeof lucide !== 'undefined') lucide.createIcons();

            // Show summary toast
            if (selectedCount > 0 || rejectedCount > 0) {
                toast('success', `Fix review complete: ${selectedCount} accepted, ${rejectedCount} rejected`);
            }
        }, 150);
    });
    
    // Triage mode buttons
    document.getElementById('btn-triage-mode')?.addEventListener('click', showTriageMode);
    document.getElementById('btn-triage-prev')?.addEventListener('click', () => navigateTriage(-1));
    document.getElementById('btn-triage-next')?.addEventListener('click', () => navigateTriage(1));
    document.getElementById('btn-triage-keep')?.addEventListener('click', () => triageAction('keep'));
    document.getElementById('btn-triage-suppress')?.addEventListener('click', () => triageAction('suppress'));
    document.getElementById('btn-triage-fixed')?.addEventListener('click', () => triageAction('fixed'));
    
    // Triage keyboard shortcuts handled by TWR.Triage module
    
    // Selection dropdown
    initSelectionDropdown();
    
    // Load profiles on startup
    loadScanProfiles();
}

// handleTriageKeyboard - Now in TWR.Triage module (features/triage.js)

// Call init for new features after DOM ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initNewFeatureListeners, 100);
});

// ============================================================
// GLOBAL EXPORTS
// ============================================================
window.toggleIssueSelection = toggleIssueSelection;
window.selectIssues = selectIssues;
// v3.0.35: getIssueKey exposed via TWR namespace for debug visibility only
window.TWR = window.TWR || {};
window.TWR.getIssueKey = getIssueKey;
window.applyPreset = applyPreset;
window.runReview = runReview;
window.showExportModal = showExportModal;
window.executeExport = executeExport;
window.applyFilters = applyFilters;
window.toggleBaseline = toggleBaseline;
// v3.0.49 FIX: Role functions are exported by TWR.Roles module in roles.js
// Removed broken references: showRoleDetails, exportRoles, viewDocumentRoles,
// showRolesModal, toggleMatrixCriticalFilter, changeMatrixSort, exportRaciMatrix,
// renderRolesGraph, clearNodeSelection, resetGraphView, filterFallbackTable, sortFallbackTable
window.applyProfileById = applyProfileById;
window.deleteProfile = deleteProfile;
window.toggleFix = toggleFix;
// toggleRoleCard removed - not defined
window.clearChartFilter = clearChartFilter;
window.setChartFilter = setChartFilter;
window.toggleIssueExpand = toggleIssueExpand;
// showTriageMode, closeTriageMode - Now exported by TWR.Triage module

// ============================================================
// DIAGNOSTIC EXPORT SYSTEM
// ============================================================

/**
 * Frontend error tracking - mirrors backend DiagnosticCollector
 */
const FrontendDiagnostics = {
    errors: [],
    warnings: [],
    maxErrors: 100,
    sessionStart: new Date().toISOString(),
    
    captureError(error, context = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            error_type: error.name || 'Error',
            message: error.message || String(error),
            stack: error.stack || '',
            context: {
                ...context,
                url: window.location.href,
                userAgent: navigator.userAgent,
            },
            severity: 'ERROR'
        };
        
        this.errors.push(entry);
        if (this.errors.length > this.maxErrors) {
            this.errors.shift();
        }
        
        // Also send to backend if available
        this.sendToBackend(entry);
        
        return entry;
    },
    
    captureWarning(message, context = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            message,
            context,
            severity: 'WARNING'
        };
        this.warnings.push(entry);
        if (this.warnings.length > this.maxErrors) {
            this.warnings.shift();
        }
    },
    
    async sendToBackend(entry) {
        try {
            await fetch('/api/diagnostics/capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': State.csrfToken
                },
                body: JSON.stringify(entry)
            });
        } catch (e) {
            // Silently fail - don't cause more errors
            console.debug('Could not send diagnostic to backend:', e);
        }
    },
    
    getState() {
        return {
            // App state (sanitized)
            filename: State.filename,
            fileType: State.fileType,
            issueCount: State.issues?.length || 0,
            filteredCount: State.filteredIssues?.length || 0,
            selectedCount: State.selectedIssues?.size || 0,
            currentPage: State.currentPage,
            sortColumn: State.sortColumn,
            sortDirection: State.sortDirection,
            settings: State.settings,
            
            // Workflow state
            reviewLogCount: State.workflow?.reviewLog?.length || 0,
            familyCount: State.workflow?.issueFamilies?.size || 0,
            
            // UI state
            activeModals: [...document.querySelectorAll('.modal.show')].map(m => m.id),
            activeTab: document.querySelector('.tab-btn.active')?.dataset?.tab || 'none',
            
            // Browser info
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            
            // Session
            sessionStart: this.sessionStart,
            errorCount: this.errors.length,
            warningCount: this.warnings.length,
        };
    }
};

// Global error handler
window.onerror = function(message, source, lineno, colno, error) {
    FrontendDiagnostics.captureError(error || new Error(message), {
        source,
        lineno,
        colno,
        type: 'uncaught'
    });
    return false; // Let default handler also run
};

// Promise rejection handler
window.onunhandledrejection = function(event) {
    FrontendDiagnostics.captureError(event.reason || new Error('Unhandled promise rejection'), {
        type: 'unhandled_rejection'
    });
};

/**
 * Show the diagnostics modal and load summary
 */
async function showDiagnosticsModal() {
    showModal('modal-diagnostics');
    
    // Load summary from backend
    try {
        const response = await fetch('/api/diagnostics/summary');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('diag-session-id').textContent = data.session_id || '-';
            document.getElementById('diag-error-count').textContent = data.error_count || 0;
            document.getElementById('diag-warning-count').textContent = data.warning_count || 0;
            document.getElementById('diag-request-count').textContent = data.request_count || 0;
        }
    } catch (e) {
        // Use frontend counts if backend unavailable
        document.getElementById('diag-session-id').textContent = 'frontend-only';
        document.getElementById('diag-error-count').textContent = FrontendDiagnostics.errors.length;
        document.getElementById('diag-warning-count').textContent = FrontendDiagnostics.warnings.length;
        document.getElementById('diag-request-count').textContent = '-';
    }
    
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

/**
 * Capture current frontend state (button in modal)
 */
function captureFrontendState() {
    const state = FrontendDiagnostics.getState();
    FrontendDiagnostics.captureWarning('Manual state capture', state);
    toast('success', 'Current state captured for diagnostics');
    
    // Update count
    document.getElementById('diag-warning-count').textContent = 
        parseInt(document.getElementById('diag-warning-count').textContent || 0) + 1;
}

/**
 * Export diagnostics file
 */
async function exportDiagnostics() {
    const format = document.getElementById('diag-format').value;
    const includeSystem = document.getElementById('diag-include-system').checked;
    const includeRequests = document.getElementById('diag-include-requests').checked;
    
    try {
        const response = await fetch('/api/diagnostics/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': State.csrfToken
            },
            body: JSON.stringify({
                format,
                include_system_info: includeSystem,
                include_request_log: includeRequests
            })
        });
        
        if (response.ok) {
            // Download the file
            const blob = await response.blob();
            const filename = response.headers.get('Content-Disposition')?.match(/filename="?(.+)"?/)?.[1] 
                || `diagnostic_export.${format}`;
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            
            toast('success', 'Diagnostic export downloaded');
            closeModals();
        } else {
            throw new Error(`Export failed: ${response.status}`);
        }
    } catch (e) {
        // Fallback: export frontend-only diagnostics
        console.error('[TWR] Backend export failed, using frontend fallback:', e);
        exportFrontendDiagnostics(format);
    }
}

/**
 * Fallback: export frontend-only diagnostics if backend unavailable
 */
function exportFrontendDiagnostics(format = 'json') {
    const data = {
        diagnostic_export: {
            version: '2.8.2',
            export_timestamp: new Date().toISOString(),
            source: 'frontend_only',
            note: 'Backend diagnostic endpoint unavailable, frontend data only'
        },
        frontend_state: FrontendDiagnostics.getState(),
        frontend_errors: FrontendDiagnostics.errors,
        frontend_warnings: FrontendDiagnostics.warnings,
        browser_info: {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            cookiesEnabled: navigator.cookieEnabled,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        }
    };
    
    let content, mimeType, extension;
    
    if (format === 'json') {
        content = JSON.stringify(data, null, 2);
        mimeType = 'application/json';
        extension = 'json';
    } else {
        // Text format
        content = formatFrontendDiagnosticReport(data);
        mimeType = 'text/plain';
        extension = 'txt';
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostic_export_frontend_${new Date().toISOString().slice(0,10)}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast('info', 'Frontend diagnostics exported (backend unavailable)');
    closeModals();
}

/**
 * Format frontend diagnostics as text report
 */
function formatFrontendDiagnosticReport(data) {
    const lines = [
        '=' .repeat(70),
        'TECHWRITERREVIEW FRONTEND DIAGNOSTIC REPORT',
        '=' .repeat(70),
        '',
        `Export Time: ${data.diagnostic_export.export_timestamp}`,
        `Source: ${data.diagnostic_export.source}`,
        '',
        '-'.repeat(70),
        'FRONTEND STATE',
        '-'.repeat(70),
        `File: ${data.frontend_state.filename || 'none'}`,
        `Issues: ${data.frontend_state.issueCount}`,
        `Filtered: ${data.frontend_state.filteredCount}`,
        `Selected: ${data.frontend_state.selectedCount}`,
        `Page: ${data.frontend_state.currentPage}`,
        `Errors captured: ${data.frontend_state.errorCount}`,
        `Warnings captured: ${data.frontend_state.warningCount}`,
        '',
        '-'.repeat(70),
        'BROWSER INFO',
        '-'.repeat(70),
        `User Agent: ${data.browser_info.userAgent}`,
        `Platform: ${data.browser_info.platform}`,
        `Viewport: ${data.browser_info.viewport.width}x${data.browser_info.viewport.height}`,
        '',
    ];
    
    if (data.frontend_errors.length > 0) {
        lines.push('-'.repeat(70));
        lines.push(`ERRORS (${data.frontend_errors.length})`);
        lines.push('-'.repeat(70));
        
        data.frontend_errors.slice(-20).forEach((err, i) => {
            lines.push(`[${i+1}] ${err.timestamp}`);
            lines.push(`    Type: ${err.error_type}`);
            lines.push(`    Message: ${err.message}`);
            if (err.stack) {
                lines.push(`    Stack: ${err.stack.split('\n').slice(0, 5).join('\n           ')}`);
            }
            lines.push('');
        });
    }
    
    lines.push('='.repeat(70));
    lines.push('END OF REPORT');
    lines.push('='.repeat(70));
    
    return lines.join('\n');
}

// Export diagnostic functions
window.showDiagnosticsModal = showDiagnosticsModal;
window.captureFrontendState = captureFrontendState;
window.exportDiagnostics = exportDiagnostics;
window.FrontendDiagnostics = FrontendDiagnostics;

// ============================================================
// UI FIXES v2.8.5-patch1 - Override toast function
// ============================================================

// Store original toast if it exists
if (typeof window._originalToast === 'undefined' && typeof toast === 'function') {
    window._originalToast = toast;
}

// Fixed toast function with close button and guaranteed removal
function toast(type, message, duration = 4000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    // Limit max toasts to prevent stacking
    const existingToasts = container.querySelectorAll('.toast:not(.toast-exit)');
    if (existingToasts.length >= 5) {
        // Remove oldest toast
        const oldest = existingToasts[0];
        oldest.classList.add('toast-exit');
        setTimeout(() => oldest.remove(), 300);
    }
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast toast-${type}`;

    const icons = { success: 'check-circle', error: 'x-circle', warning: 'alert-triangle', info: 'info' };
    toastEl.innerHTML = `
        <i data-lucide="${icons[type] || 'info'}" class="toast-icon"></i>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" onclick="this.parentElement.remove()" aria-label="Close">&times;</button>
    `;

    container.appendChild(toastEl);
    
    // Initialize lucide icons if available
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }

    // Auto-dismiss
    const dismissTimer = setTimeout(() => {
        if (toastEl.parentElement) {
            toastEl.classList.add('toast-exit');
            setTimeout(() => {
                if (toastEl.parentElement) {
                    toastEl.remove();
                }
            }, 300);
        }
    }, duration);
    
    // Clear timer if manually closed
    toastEl.querySelector('.toast-close').addEventListener('click', () => {
        clearTimeout(dismissTimer);
    });
}

function createToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

// v3.0.11: Simplified - settings now loaded via single loadSettings() call
// This handler just syncs UI checkboxes after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Sync checkbox states with loaded settings after DOM ready
    setTimeout(() => {
        if (typeof State !== 'undefined' && State.settings) {
            const autoReviewCb = document.getElementById('settings-auto-review');
            if (autoReviewCb) autoReviewCb.checked = State.settings.autoReview || false;
            
            const rememberChecksCb = document.getElementById('settings-remember-checks');
            if (rememberChecksCb) rememberChecksCb.checked = State.settings.rememberChecks !== false;
            
            const showChartsCb = document.getElementById('settings-show-charts');
            if (showChartsCb) showChartsCb.checked = State.settings.showCharts !== false;

            // Sync guide toggle with AEGISGuide state (v5.6.0)
            const guideCb = document.getElementById('settings-guide-enabled');
            if (guideCb && window.AEGISGuide) {
                guideCb.checked = window.AEGISGuide.isEnabled();
            }
            
            const compactModeCb = document.getElementById('settings-compact-mode');
            if (compactModeCb) compactModeCb.checked = State.settings.compactMode || false;
            
            const diagEmail = document.getElementById('settings-diagnostics-email');
            if (diagEmail && State.settings.diagnosticsEmail) {
                diagEmail.value = State.settings.diagnosticsEmail;
            }
        }
    }, 100);
});

// v3.0.11: Removed duplicate saveSettings - now defined once in SETTINGS section above

// v3.0.11: Removed legacy patch banner

// ============================================================
// DIAGNOSTICS MODAL FIXES v2.8.5-patch2
// ============================================================

// Ensure showDiagnosticsModal is globally available and works
window.showDiagnosticsModal = async function() {
    const modal = document.getElementById('modal-diagnostics');
    if (!modal) {
        console.error('[TWR] Diagnostics modal not found');
        toast('error', 'Diagnostics modal not found');
        return;
    }
    
    // Show modal
    modal.classList.add('active');
    document.body.classList.add('modal-open');
    
    // Load summary from backend
    try {
        const response = await fetch('/api/diagnostics/summary');
        if (response.ok) {
            const data = await response.json();
            const sessionEl = document.getElementById('diag-session-id');
            const errorEl = document.getElementById('diag-error-count');
            const warnEl = document.getElementById('diag-warning-count');
            const reqEl = document.getElementById('diag-request-count');
            
            if (sessionEl) sessionEl.textContent = data.session_id || '-';
            if (errorEl) errorEl.textContent = data.error_count || 0;
            if (warnEl) warnEl.textContent = data.warning_count || 0;
            if (reqEl) reqEl.textContent = data.request_count || 0;
        }
    } catch (e) {
        console.warn('[TWR] Could not load diagnostics summary:', e);
        // Use frontend counts if backend unavailable
        const sessionEl = document.getElementById('diag-session-id');
        if (sessionEl) sessionEl.textContent = 'frontend-only';
    }
    
    // Initialize icons
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }
};

// Ensure exportDiagnostics works
// v2.9.3 B20: Fixed export not working - improved error handling and response processing
window.exportDiagnostics = async function() {
    const formatEl = document.getElementById('diag-format');
    const systemEl = document.getElementById('diag-include-system');
    const requestsEl = document.getElementById('diag-include-requests');
    
    const format = formatEl?.value || 'json';
    const includeSystem = systemEl?.checked !== false;
    const includeRequests = requestsEl?.checked !== false;
    
    // Show loading indicator
    if (typeof showLoading === 'function') {
        showLoading('Exporting diagnostics...');
    }
    
    try {
        console.log('[TWR] Exporting diagnostics, format:', format);
        
        const response = await fetch('/api/diagnostics/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': (typeof State !== 'undefined' && State.csrfToken) || 
                               document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({
                format,
                include_system_info: includeSystem,
                include_request_log: includeRequests
            })
        });
        
        console.log('[TWR] Export response status:', response.status);
        
        if (!response.ok) {
            // Try to get error message from JSON response
            const errorText = await response.text();
            let errorMsg = `Export failed: HTTP ${response.status}`;
            try {
                const errorJson = JSON.parse(errorText);
                if (errorJson.error) {
                    errorMsg = errorJson.error;
                }
            } catch (e) {
                // Not JSON, use text
                if (errorText) errorMsg = errorText;
            }
            throw new Error(errorMsg);
        }
        
        // Check content type - v2.9.4 #20: Fixed double body consumption bug
        const contentType = response.headers.get('Content-Type') || '';
        
        // Clone response before checking JSON to avoid consuming body twice
        const responseClone = response.clone();
        
        // If JSON response, it might be an error
        if (contentType.includes('application/json')) {
            try {
                const jsonResp = await response.json();
                // If it's a JSON error response, throw
                if (jsonResp && !jsonResp.success && jsonResp.error) {
                    throw new Error(jsonResp.error);
                }
                // If JSON but success, it might be a filepath response from GET
                // Fall through to use clone for blob
            } catch (parseErr) {
                // Not valid JSON, continue with blob
            }
        }
        
        // Get as blob for file download (use clone to avoid consumed body issue)
        const blob = await responseClone.blob();
        
        // Get filename from Content-Disposition header or generate one
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `diagnostic_export_${new Date().toISOString().slice(0,19).replace(/[:-]/g, '')}.${format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (match && match[1]) {
                filename = match[1].replace(/['"]/g, '');
            }
        }
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('[TWR] Export downloaded:', filename);
        toast('success', 'Diagnostic export downloaded: ' + filename);
        closeModals();
    } catch (e) {
        console.error('[TWR] Backend export failed:', e);
        toast('error', 'Export failed: ' + e.message);
        // Try frontend-only fallback
        if (typeof exportFrontendDiagnostics === 'function') {
            console.log('[TWR] Trying frontend fallback export...');
            exportFrontendDiagnostics(format);
        }
    } finally {
        if (typeof hideLoading === 'function') {
            hideLoading();
        }
    }
};

// Ensure captureFrontendState works
window.captureFrontendState = function() {
    toast('success', 'Current state captured for diagnostics');
    const warnEl = document.getElementById('diag-warning-count');
    if (warnEl) {
        warnEl.textContent = (parseInt(warnEl.textContent) || 0) + 1;
    }
};

// Re-attach close handlers to all modal-close buttons on page load
document.addEventListener('DOMContentLoaded', function() {
    // Ensure all modal-close buttons work
    document.querySelectorAll('.modal-close').forEach(btn => {
        // Remove any existing listeners and add new one
        btn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            // Only close the specific modal containing this button, not all modals
            const parentModal = this.closest('.modal');
            if (parentModal) {
                parentModal.classList.remove('active');
                // Only remove modal-open if no other modals are active
                const otherActiveModals = document.querySelectorAll('.modal.active');
                if (otherActiveModals.length === 0) {
                    document.body.classList.remove('modal-open');
                }
            }
        };
    });

    // Also close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            // Only close if clicked directly on the modal backdrop (not its children)
            // and only close THIS modal, not any others
            if (e.target === modal) {
                e.stopPropagation(); // Prevent click from reaching modals beneath
                modal.classList.remove('active');
                // Only remove modal-open if no other modals are active
                const otherActiveModals = document.querySelectorAll('.modal.active');
                if (otherActiveModals.length === 0) {
                    document.body.classList.remove('modal-open');
                }
            }
        });
    });

    // Close on Escape key - close the topmost modal only
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Get all active modals and close only the topmost (last in DOM order or highest z-index)
            const activeModals = document.querySelectorAll('.modal.active');
            if (activeModals.length > 0) {
                // Close the last active modal (typically the one on top)
                const topmostModal = activeModals[activeModals.length - 1];
                topmostModal.classList.remove('active');
                // Only remove modal-open if no other modals are active
                if (activeModals.length === 1) {
                    document.body.classList.remove('modal-open');
                }
            }
        }
    });
});

// v3.0.11: Removed legacy patch banner

// ============================================================
// EMAIL DIAGNOSTICS VIA OUTLOOK v2.8.5-patch3
// ============================================================

// Get diagnostics email from settings
function getDiagnosticsEmail() {
    // Try from State first
    if (typeof State !== 'undefined' && State.settings && State.settings.diagnosticsEmail) {
        return State.settings.diagnosticsEmail;
    }
    // Try from localStorage
    try {
        const saved = localStorage.getItem('twr_settings');
        if (saved) {
            const settings = JSON.parse(saved);
            if (settings.diagnosticsEmail) {
                return settings.diagnosticsEmail;
            }
        }
    } catch (e) {}
    // Try from DOM
    const emailInput = document.getElementById('settings-diagnostics-email');
    if (emailInput && emailInput.value) {
        return emailInput.value;
    }
    // Default
    return 'Nicholas.georgeson@gmail.com';
}

// Collect diagnostic data for email
async function collectDiagnosticData() {
    const data = {
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        viewport: {
            width: window.innerWidth,
            height: window.innerHeight
        }
    };
    
    // Try to get backend diagnostics
    try {
        const response = await fetch('/api/diagnostics/summary');
        if (response.ok) {
            const summary = await response.json();
            data.backend = summary;
        }
    } catch (e) {
        data.backend = { error: 'Could not fetch backend diagnostics' };
    }
    
    // Add frontend state
    if (typeof State !== 'undefined') {
        data.frontend = {
            filename: State.filename || null,
            issueCount: State.issues?.length || 0,
            hasDocument: !!State.filename
        };
    }
    
    // Add any console errors if FrontendDiagnostics exists
    if (typeof FrontendDiagnostics !== 'undefined') {
        data.frontendErrors = FrontendDiagnostics.errors || [];
        data.frontendWarnings = FrontendDiagnostics.warnings || [];
    }
    
    return data;
}

// Format diagnostic data for email body
function formatDiagnosticsForEmail(data) {
    let body = `AEGIS Diagnostic Report
================================

Generated: ${data.timestamp}

SYSTEM INFORMATION
------------------
User Agent: ${data.userAgent}
URL: ${data.url}
Viewport: ${data.viewport.width}x${data.viewport.height}

`;

    if (data.backend && !data.backend.error) {
        body += `BACKEND STATUS
--------------
Session ID: ${data.backend.session_id || 'N/A'}
Errors: ${data.backend.error_count || 0}
Warnings: ${data.backend.warning_count || 0}
Requests: ${data.backend.request_count || 0}

`;
    }

    if (data.frontend) {
        body += `FRONTEND STATUS
---------------
Document Loaded: ${data.frontend.hasDocument ? 'Yes' : 'No'}
Filename: ${data.frontend.filename || 'None'}
Issues Found: ${data.frontend.issueCount}

`;
    }

    if (data.frontendErrors && data.frontendErrors.length > 0) {
        body += `FRONTEND ERRORS (${data.frontendErrors.length})
----------------
`;
        data.frontendErrors.slice(0, 10).forEach((err, i) => {
            body += `${i + 1}. ${err.message || err}\n`;
        });
        body += '\n';
    }

    if (data.frontendWarnings && data.frontendWarnings.length > 0) {
        body += `FRONTEND WARNINGS (${data.frontendWarnings.length})
-----------------
`;
        data.frontendWarnings.slice(0, 10).forEach((warn, i) => {
            body += `${i + 1}. ${warn.message || warn}\n`;
        });
        body += '\n';
    }

    body += `
================================
Please describe the issue you encountered:

[Describe the problem here]

Steps to reproduce:
1. 
2. 
3. 

Expected behavior:

Actual behavior:

`;

    return body;
}

// Email diagnostics via .eml file download
// v5.9.20: Rewritten to use server-generated .eml file with logs ATTACHED.
// The .eml format (RFC 2822) opens in Outlook/Apple Mail as a pre-composed
// draft with diagnostic JSON + aegis.log already attached. No more manual
// "drag the file from Downloads" workflow.
window.emailDiagnosticsViaOutlook = async function() {
    const toEmail = getDiagnosticsEmail();

    toast('info', 'Preparing diagnostic email with log attachments...');

    if (typeof showLoading === 'function') {
        showLoading('Generating email with attached logs...');
    }

    try {
        // Get fresh CSRF token
        let csrfToken = (typeof State !== 'undefined' && State.csrfToken) ||
                        document.querySelector('meta[name="csrf-token"]')?.content || '';
        try {
            const tokenResp = await fetch('/api/version', { credentials: 'same-origin' });
            const freshCsrf = tokenResp.headers.get('X-CSRF-Token');
            if (freshCsrf) csrfToken = freshCsrf;
        } catch (_) {}

        // Request .eml file from server (includes diagnostic JSON + log files as attachments)
        const response = await fetch('/api/diagnostics/email', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ to_email: toEmail })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData?.error?.message || `Server returned ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result?.error?.message || 'Failed to generate diagnostic email');
        }

        console.log('[TWR] Diagnostic .eml generated:', result.filename, '| Attachments:', result.attachments, '| Opened:', result.opened);

        if (result.opened) {
            toast('success', `Opening diagnostic email in Outlook with ${result.attachments} log files attached...`, 6000);
            // Show confirmation modal
            setTimeout(() => {
                showDiagnosticEmlModal(result.filename, result.attachments, result.opened);
            }, 500);
        } else {
            toast('warning', `Email file created but could not auto-open. File: ${result.path}`, 10000);
            setTimeout(() => {
                showDiagnosticEmlModal(result.filename, result.attachments, false);
            }, 500);
        }

    } catch (e) {
        console.error('[TWR] Error preparing diagnostic email:', e);
        toast('error', 'Failed to prepare email: ' + e.message);
    } finally {
        if (typeof hideLoading === 'function') {
            hideLoading();
        }
    }
};

// v5.9.20: Show modal confirming diagnostic email opened in Outlook
function showDiagnosticEmlModal(filename, attachmentCount, opened) {
    const existingModal = document.getElementById('diagnostic-filepath-modal');
    if (existingModal) existingModal.remove();

    const modal = document.createElement('div');
    modal.id = 'diagnostic-filepath-modal';
    modal.className = 'modal-overlay';
    modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:250000;';

    const statusIcon = opened ? 'check-circle' : 'alert-circle';
    const statusTitle = opened ? 'Email Opened in Outlook' : 'Email File Created';
    const statusMsg = opened
        ? `A diagnostic email with <strong>${attachmentCount || 'all'} log files attached</strong> has been opened in Outlook. Review the email and click <strong>Send</strong>.`
        : `The email file was created but could not auto-open in Outlook. You can find it and double-click to open:`;

    modal.innerHTML = `
        <div style="background:var(--bg-primary, white);border-radius:12px;padding:28px;max-width:520px;margin:20px;box-shadow:0 8px 32px rgba(0,0,0,0.3);border:1px solid var(--border-muted, #ddd6c9);">
            <div style="text-align:center;margin-bottom:20px;">
                <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg, #D6A84A 0%, #B8743A 100%);display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;">
                    <i data-lucide="${statusIcon}" style="width:28px;height:28px;color:white;"></i>
                </div>
                <h3 style="margin:0;color:var(--text-primary, #1a1a2e);font-size:18px;">
                    ${statusTitle}
                </h3>
            </div>
            <p style="margin:0 0 16px 0;color:var(--text-secondary, #666);text-align:center;line-height:1.5;">
                ${statusMsg}
            </p>
            ${!opened ? `<div style="background:var(--bg-secondary, #f5f5f5);padding:14px;border-radius:8px;font-family:'SF Mono',Monaco,monospace;font-size:13px;word-break:break-all;margin-bottom:20px;border:1px solid var(--border-default, #cfc7b8);text-align:center;">
                <i data-lucide="mail" style="width:14px;height:14px;vertical-align:middle;margin-right:4px;"></i> ${escapeHtml(filename)}
            </div>` : ''}
            <div style="background:linear-gradient(135deg, rgba(214,168,74,0.1), rgba(184,116,58,0.1));border-radius:8px;padding:14px;margin-bottom:20px;border:1px solid rgba(214,168,74,0.2);">
                <p style="margin:0;color:var(--text-primary, #1a1a2e);font-size:13px;line-height:1.6;">
                    <strong>Attached:</strong> Diagnostic JSON report, aegis.log, and ${attachmentCount ? attachmentCount - 2 : 'all other'} module log files.
                </p>
            </div>
            <div style="display:flex;gap:8px;justify-content:center;">
                <button onclick="this.closest('.modal-overlay').remove()" class="btn btn-primary" style="padding:8px 20px;border-radius:6px;">
                    ${opened ? 'Done' : 'Got It'}
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
}

// Legacy compatibility aliases
function showDiagnosticFileDownloadedModal(filename) { showDiagnosticEmlModal(filename); }
function showDiagnosticFilePathModal(filepath) {
    const filename = filepath.split(/[/\\]/).pop() || filepath;
    showDiagnosticEmlModal(filename);
}

// v3.0.11: Removed duplicate window.saveSettings override - now using single saveSettings() in SETTINGS section

// Save shared dictionary path to server config
async function saveSharedPathToServer(path) {
    try {
        const response = await fetch('/api/config/sharing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.CSRF_TOKEN || ''
            },
            body: JSON.stringify({ shared_dictionary_path: path })
        });
        const result = await response.json();
        if (!result.success) {
            console.warn('[TWR] Failed to save shared path to server:', result.error);
        }
    } catch (e) {
        console.warn('[TWR] Error saving shared path:', e);
    }
}

// Load diagnostics email setting on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load saved diagnostics email
    try {
        const saved = localStorage.getItem('twr_settings');
        if (saved) {
            const settings = JSON.parse(saved);
            const emailInput = document.getElementById('settings-diagnostics-email');
            if (emailInput && settings.diagnosticsEmail) {
                emailInput.value = settings.diagnosticsEmail;
            }
            // Also update State if available
            if (typeof State !== 'undefined' && State.settings) {
                State.settings.diagnosticsEmail = settings.diagnosticsEmail || '';
            }
            
            // Load sharing settings
            if (settings.dictLocation) {
                const radio = document.getElementById(`dict-location-${settings.dictLocation}`);
                if (radio) radio.checked = true;
                toggleSharedPathGroup(settings.dictLocation === 'shared');
            }
            if (settings.sharedDictPath) {
                const pathInput = document.getElementById('settings-shared-path');
                if (pathInput) pathInput.value = settings.sharedDictPath;
            }
        }
    } catch (e) {
        console.warn('[TWR] Could not load settings:', e);
    }
    
    // Initialize sharing settings UI
    initSharingSettings();

    // Initialize document profiles settings (v3.0.110)
    initDocumentProfilesSettings();

    // Check if first-time user needs to configure profiles (v3.0.115)
    checkFirstTimeProfileSetup();
});

// Initialize sharing settings UI
function initSharingSettings() {
    // Radio button toggle for shared path visibility
    document.querySelectorAll('input[name="dict-location"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            toggleSharedPathGroup(e.target.value === 'shared');
        });
    });
    
    // Test connection button
    document.getElementById('btn-test-shared')?.addEventListener('click', testSharedConnection);
    
    // Settings tab change - load status when Sharing tab shown
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            if (e.target.dataset?.tab === 'sharing') {
                loadSharingSettingsStatus();
            }
        });
    });
}

function toggleSharedPathGroup(show) {
    const group = document.getElementById('shared-path-group');
    if (group) {
        group.style.display = show ? 'block' : 'none';
    }
}

async function testSharedConnection() {
    const pathInput = document.getElementById('settings-shared-path');
    const statusEl = document.getElementById('shared-path-status');
    const statusText = document.getElementById('shared-path-status-text');
    const testBtn = document.getElementById('btn-test-shared');
    
    if (!pathInput?.value) {
        if (statusEl) {
            statusEl.style.display = 'flex';
            statusEl.className = 'path-status error';
            statusText.textContent = 'Please enter a path first';
        }
        return;
    }
    
    // Show loading
    if (testBtn) testBtn.disabled = true;
    if (statusEl) {
        statusEl.style.display = 'flex';
        statusEl.className = 'path-status checking';
        statusText.textContent = 'Testing connection...';
    }
    
    try {
        const response = await fetch('/api/config/sharing/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.CSRF_TOKEN || ''
            },
            body: JSON.stringify({ path: pathInput.value })
        });
        const result = await response.json();
        
        if (result.success && result.data?.accessible) {
            statusEl.className = 'path-status success';
            statusText.textContent = `Connected! ${result.data.has_master_file ? 'Master file found.' : 'No master file yet.'}`;
        } else {
            statusEl.className = 'path-status error';
            statusText.textContent = result.data?.error || 'Path not accessible';
        }
    } catch (e) {
        statusEl.className = 'path-status error';
        statusText.textContent = 'Connection test failed: ' + e.message;
    } finally {
        if (testBtn) testBtn.disabled = false;
    }
}

async function loadSharingSettingsStatus() {
    // v5.9.5: Show proper state indicators instead of staying stuck on "Checking..."
    const localEl = document.getElementById('status-local-db');
    const masterEl = document.getElementById('status-master-file');
    const sharedEl = document.getElementById('status-shared-location');

    try {
        const response = await fetch('/api/roles/dictionary/status');
        const result = await response.json();

        if (result.success) {
            const status = result.data;

            // Update local DB status with status indicator
            if (localEl) {
                if (status.database?.exists) {
                    localEl.textContent = `✓ Connected — ${status.database.role_count} roles`;
                    localEl.style.color = 'var(--success, #4ade80)';
                } else {
                    localEl.textContent = '○ Not created';
                    localEl.style.color = 'var(--text-secondary)';
                }
            }

            // Update master file status
            if (masterEl) {
                if (status.master_file?.exists) {
                    masterEl.textContent = `✓ Found — ${status.master_file.role_count} roles`;
                    masterEl.style.color = 'var(--success, #4ade80)';
                } else {
                    masterEl.textContent = '○ Not found';
                    masterEl.style.color = 'var(--text-secondary)';
                }
            }

            // Update shared location status
            if (sharedEl) {
                if (status.shared_folder?.configured) {
                    if (status.shared_folder.exists) {
                        sharedEl.textContent = `✓ Connected — ${status.shared_folder.role_count} roles`;
                        sharedEl.style.color = 'var(--success, #4ade80)';
                    } else {
                        sharedEl.textContent = '⚠ Configured but not accessible';
                        sharedEl.style.color = 'var(--warning, #f59e0b)';
                    }
                } else {
                    sharedEl.textContent = '○ Not configured';
                    sharedEl.style.color = 'var(--text-secondary)';
                }
            }
        } else {
            // API returned success: false
            if (localEl) { localEl.textContent = '✗ Status unavailable'; localEl.style.color = 'var(--error, #f87171)'; }
            if (masterEl) { masterEl.textContent = '✗ Status unavailable'; masterEl.style.color = 'var(--error, #f87171)'; }
            if (sharedEl) { sharedEl.textContent = '✗ Status unavailable'; sharedEl.style.color = 'var(--error, #f87171)'; }
        }
    } catch (e) {
        console.warn('[TWR] Error loading sharing status:', e);
        // v5.9.5: Show error state instead of leaving "Checking..."
        if (localEl) { localEl.textContent = '✗ Connection error'; localEl.style.color = 'var(--error, #f87171)'; }
        if (masterEl) { masterEl.textContent = '✗ Connection error'; masterEl.style.color = 'var(--error, #f87171)'; }
        if (sharedEl) { sharedEl.textContent = '✗ Connection error'; sharedEl.style.color = 'var(--error, #f87171)'; }
    }
}

// v3.0.11: Removed legacy patch banner


// ============================================================
// DOCUMENT PROFILES SETTINGS (v3.0.110)
// Allows users to customize which checks are performed for each
// document type (PrOP, PAL, FGOST, SOW) with localStorage persistence
// ============================================================

// Default presets for each document type (matches applyPreset defaults)
const DEFAULT_DOCUMENT_PROFILES = {
    prop: {
        name: 'PrOP',
        fullName: 'Procedure Operational',
        description: 'Focus on process clarity and step-by-step instructions.',
        checks: ['passive_voice', 'weak_language', 'requirements_language', 'roles',
                 'document_structure', 'lists', 'orphan_headings', 'empty_sections',
                 'ambiguous_pronouns', 'testability', 'atomicity']
    },
    pal: {
        name: 'PAL',
        fullName: 'Process Asset Library',
        description: 'Standard templates and assets - grammar and structure focus.',
        checks: ['spelling', 'grammar', 'punctuation', 'document_structure', 'references',
                 'terminology', 'consistency', 'tables_figures', 'hyperlinks']
    },
    fgost: {
        name: 'FGOST',
        fullName: 'Flow Gate/Stage Gate',
        description: 'Decision gates and milestones - requirements and completeness.',
        checks: ['requirements_language', 'tbd', 'roles', 'testability', 'atomicity',
                 'escape_clauses', 'weak_language', 'ambiguous_pronouns', 'document_structure']
    },
    sow: {
        name: 'SOW',
        fullName: 'Statement of Work',
        description: 'Contract-focused checks for legal and technical clarity.',
        checks: ['requirements_language', 'passive_voice', 'weak_language', 'escape_clauses',
                 'tbd', 'ambiguous_pronouns', 'testability', 'atomicity', 'roles',
                 'acronyms', 'units', 'references']
    }
};

// LocalStorage key for custom profiles
const PROFILES_STORAGE_KEY = 'twr_document_profiles';

// LocalStorage key to track if user has seen the first-time profile setup prompt
const PROFILES_SETUP_SEEN_KEY = 'twr_profiles_setup_seen';

// Currently selected profile in settings
let currentSettingsProfile = 'prop';

/**
 * Get custom profiles from localStorage (merged with defaults)
 */
function getCustomProfiles() {
    try {
        const saved = localStorage.getItem(PROFILES_STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            // Merge with defaults to ensure all profiles exist
            return {
                ...DEFAULT_DOCUMENT_PROFILES,
                ...parsed
            };
        }
    } catch (e) {
        console.warn('[TWR] Error reading custom profiles:', e);
    }
    return { ...DEFAULT_DOCUMENT_PROFILES };
}

/**
 * Save a profile to localStorage
 */
function saveCustomProfile(profileId, checks) {
    try {
        const profiles = getCustomProfiles();
        profiles[profileId] = {
            ...profiles[profileId],
            checks: checks
        };
        localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(profiles));
        showProfileSaveStatus();
        console.log(`[TWR] Saved custom profile: ${profileId} with ${checks.length} checks`);
        return true;
    } catch (e) {
        console.warn('[TWR] Error saving profile:', e);
        return false;
    }
}

/**
 * Reset a profile to its default
 */
function resetProfileToDefault(profileId) {
    try {
        const profiles = getCustomProfiles();
        if (DEFAULT_DOCUMENT_PROFILES[profileId]) {
            profiles[profileId] = { ...DEFAULT_DOCUMENT_PROFILES[profileId] };
            localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(profiles));
            showProfileSaveStatus('Reset to default');
            return true;
        }
    } catch (e) {
        console.warn('[TWR] Error resetting profile:', e);
    }
    return false;
}

/**
 * Show save status notification in profiles panel
 */
function showProfileSaveStatus(message = 'Profile saved') {
    const statusEl = document.getElementById('profile-save-status');
    if (statusEl) {
        const spanEl = statusEl.querySelector('span');
        if (spanEl) spanEl.textContent = message;
        statusEl.style.display = 'flex';
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 2000);
    }
}

/**
 * Load profile checks into the settings grid
 */
function loadProfileIntoGrid(profileId) {
    const profiles = getCustomProfiles();
    const profile = profiles[profileId];

    if (!profile) return;

    // Update description
    const descEl = document.getElementById('profile-description');
    if (descEl) {
        descEl.innerHTML = `<strong>${profile.name} (${profile.fullName})</strong> - ${profile.description}`;
    }

    // Update checkboxes
    const grid = document.getElementById('profile-checker-grid');
    if (!grid) return;

    const checkboxes = grid.querySelectorAll('input[type="checkbox"][data-check]');
    checkboxes.forEach(cb => {
        cb.checked = profile.checks.includes(cb.dataset.check);
    });
}

/**
 * Get current checks selected in the grid
 */
function getChecksFromGrid() {
    const grid = document.getElementById('profile-checker-grid');
    if (!grid) return [];

    const checks = [];
    grid.querySelectorAll('input[type="checkbox"][data-check]:checked').forEach(cb => {
        checks.push(cb.dataset.check);
    });
    return checks;
}

/**
 * Initialize Document Profiles settings UI
 */
function initDocumentProfilesSettings() {
    const profileBtns = document.querySelectorAll('.profile-btn-settings');
    const checkerGrid = document.getElementById('profile-checker-grid');

    if (!checkerGrid) {
        console.log('[TWR] Document profiles grid not found, skipping init');
        return;
    }

    console.log('[TWR] Initializing Document Profiles settings...');

    // Profile selector buttons
    profileBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Save current profile before switching
            if (currentSettingsProfile) {
                const checks = getChecksFromGrid();
                saveCustomProfile(currentSettingsProfile, checks);
            }

            // Update active state
            profileBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Load new profile
            currentSettingsProfile = btn.dataset.profile;
            loadProfileIntoGrid(currentSettingsProfile);
        });
    });

    // Checkbox changes auto-save
    checkerGrid.addEventListener('change', (e) => {
        if (e.target.matches('input[type="checkbox"][data-check]')) {
            const checks = getChecksFromGrid();
            saveCustomProfile(currentSettingsProfile, checks);
        }
    });

    // Select All button
    document.getElementById('btn-profile-select-all')?.addEventListener('click', () => {
        checkerGrid.querySelectorAll('input[type="checkbox"][data-check]').forEach(cb => cb.checked = true);
        const checks = getChecksFromGrid();
        saveCustomProfile(currentSettingsProfile, checks);
    });

    // Clear All button
    document.getElementById('btn-profile-clear-all')?.addEventListener('click', () => {
        checkerGrid.querySelectorAll('input[type="checkbox"][data-check]').forEach(cb => cb.checked = false);
        const checks = getChecksFromGrid();
        saveCustomProfile(currentSettingsProfile, checks);
    });

    // Reset to Default button
    document.getElementById('btn-profile-reset-default')?.addEventListener('click', () => {
        resetProfileToDefault(currentSettingsProfile);
        loadProfileIntoGrid(currentSettingsProfile);
    });

    // Load initial profile when settings tab is shown
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.dataset.tab === 'profiles') {
                loadProfileIntoGrid(currentSettingsProfile);
            }
        });
    });

    // Load the default profile (PrOP) initially
    loadProfileIntoGrid('prop');
}

// Make getCustomProfiles available globally for applyPreset
window.getCustomProfiles = getCustomProfiles;

/**
 * Check if this is the user's first time and show profile setup prompt
 */
function checkFirstTimeProfileSetup() {
    // Check if user has already seen the prompt or has configured profiles
    const hasSeenPrompt = localStorage.getItem(PROFILES_SETUP_SEEN_KEY);
    const hasCustomProfiles = localStorage.getItem(PROFILES_STORAGE_KEY);

    if (hasSeenPrompt || hasCustomProfiles) {
        return; // User has already configured or dismissed
    }

    // Show the first-time setup prompt after a short delay
    setTimeout(() => {
        showProfileSetupPrompt();
    }, 1500); // Wait for app to fully load
}

/**
 * Show the first-time document profile setup prompt
 */
function showProfileSetupPrompt() {
    // Create the prompt modal if it doesn't exist
    let modal = document.getElementById('modal-profile-setup');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-profile-setup';
        modal.className = 'modal modal-sm';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 500px;">
                <div class="modal-header">
                    <h3><i data-lucide="settings-2"></i> Configure Document Profiles</h3>
                    <button class="btn btn-ghost modal-close"><i data-lucide="x"></i></button>
                </div>
                <div class="modal-body" style="padding: 24px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <i data-lucide="file-check" style="width: 48px; height: 48px; color: var(--accent);"></i>
                    </div>
                    <p style="margin-bottom: 16px; color: var(--text-secondary); line-height: 1.6;">
                        Welcome! You can customize which quality checks are performed for each document type:
                    </p>
                    <div style="display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;">
                        <span class="badge" style="background: var(--accent-subtle); color: var(--accent); padding: 6px 12px;">PrOP</span>
                        <span class="badge" style="background: var(--accent-subtle); color: var(--accent); padding: 6px 12px;">PAL</span>
                        <span class="badge" style="background: var(--accent-subtle); color: var(--accent); padding: 6px 12px;">FGOST</span>
                        <span class="badge" style="background: var(--accent-subtle); color: var(--accent); padding: 6px 12px;">SOW</span>
                    </div>
                    <p style="margin-bottom: 8px; color: var(--text-secondary); font-size: 14px;">
                        Your custom settings will persist across sessions.
                    </p>
                </div>
                <div class="modal-footer" style="display: flex; gap: 12px; justify-content: flex-end; padding: 16px 24px; border-top: 1px solid var(--border-default);">
                    <button class="btn btn-ghost" id="btn-profile-setup-later">Maybe Later</button>
                    <button class="btn btn-primary" id="btn-profile-setup-now">
                        <i data-lucide="settings"></i>
                        Configure Now
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }

        // Wire up buttons
        document.getElementById('btn-profile-setup-later')?.addEventListener('click', () => {
            localStorage.setItem(PROFILES_SETUP_SEEN_KEY, 'true');
            closeProfileSetupModal();
        });

        document.getElementById('btn-profile-setup-now')?.addEventListener('click', () => {
            localStorage.setItem(PROFILES_SETUP_SEEN_KEY, 'true');
            closeProfileSetupModal();
            // Open settings modal and switch to profiles tab
            openSettingsToProfilesTab();
        });

        // Close button
        modal.querySelector('.modal-close')?.addEventListener('click', () => {
            localStorage.setItem(PROFILES_SETUP_SEEN_KEY, 'true');
            closeProfileSetupModal();
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                localStorage.setItem(PROFILES_SETUP_SEEN_KEY, 'true');
                closeProfileSetupModal();
            }
        });
    }

    // Show the modal
    modal.classList.add('active');
    document.body.classList.add('modal-open');
}

/**
 * Close the profile setup prompt modal
 */
function closeProfileSetupModal() {
    const modal = document.getElementById('modal-profile-setup');
    if (modal) {
        modal.classList.remove('active');
        document.body.classList.remove('modal-open');
    }
}

/**
 * Open Settings modal and switch to Document Profiles tab
 */
function openSettingsToProfilesTab() {
    // Open settings modal
    if (typeof showModal === 'function') {
        showModal('modal-settings');
    } else if (window.TWR?.Modals?.showModal) {
        window.TWR.Modals.showModal('modal-settings');
    } else {
        const settingsModal = document.getElementById('modal-settings');
        if (settingsModal) {
            settingsModal.classList.add('active');
            document.body.classList.add('modal-open');
        }
    }

    // Switch to profiles tab after a short delay for modal to render
    setTimeout(() => {
        const profilesTab = document.querySelector('.settings-tab[data-tab="profiles"]');
        if (profilesTab) {
            profilesTab.click();
        }
    }, 100);
}


// ============================================================
// TECHWRITERREVIEW v2.8.6 - COMPREHENSIVE FIXES
// All fixes properly integrated - replaces previous patch attempts
// ============================================================

(function() {
    'use strict';
    
    console.log('[TWR] Loading comprehensive fixes v2.8.6...');
    
    // ============================================================
    // GLOBAL FIX STATE
    // ============================================================
    const FixState = {
        fileSelectInProgress: false,
        lucideLoaded: false,
        chartJsLoaded: false,
        initialized: false
    };
    
    // ============================================================
    // FIX 1: LUCIDE ICONS - Load from CDN with proper handling
    // ============================================================
    function loadLucideIcons() {
        return new Promise((resolve) => {
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                console.log('[TWR] Lucide already available');
                FixState.lucideLoaded = true;
                resolve(true);
                return;
            }
            
            console.log('[TWR] Loading Lucide from local vendor...');
            const script = document.createElement('script');
            script.src = '/static/js/vendor/lucide.min.js';
            script.onload = function() {
                console.log('[TWR] Lucide loaded successfully');
                FixState.lucideLoaded = true;
                if (typeof lucide !== 'undefined') {
                    try {
                        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
                    } catch (e) {
                        console.warn('[TWR] Lucide createIcons error:', e);
                    }
                }
                resolve(true);
            };
            script.onerror = function() {
                console.error('[TWR] Failed to load Lucide');
                resolve(false);
            };
            document.head.appendChild(script);
        });
    }
    
    // ============================================================
    // FIX 2: CHART.JS - Load from CDN with proper handling
    // ============================================================
    function loadChartJs() {
        return new Promise((resolve) => {
            if (typeof Chart !== 'undefined') {
                console.log('[TWR] Chart.js already available');
                FixState.chartJsLoaded = true;
                resolve(true);
                return;
            }
            
            console.log('[TWR] Loading Chart.js from local vendor...');
            const script = document.createElement('script');
            script.src = '/static/js/vendor/chart.min.js';
            script.onload = function() {
                console.log('[TWR] Chart.js loaded successfully');
                FixState.chartJsLoaded = true;
                window.dispatchEvent(new Event('chartjs-ready'));
                resolve(true);
            };
            script.onerror = function() {
                console.error('[TWR] Failed to load Chart.js');
                resolve(false);
            };
            document.head.appendChild(script);
        });
    }
    
    // ============================================================
    // FIX 3: FILE SELECTION - Use global guards (main handler already fixed)
    // ============================================================
    function fixFileSelection() {
        // The main initEventListeners already has guards now via window._TWR_fileProcessing
        // This function just ensures the btn-open has proper guards too
        
        const btnOpen = document.getElementById('btn-open');
        if (!btnOpen) {
            console.warn('[TWR] Open button not found');
            return;
        }
        
        // Add a guard wrapper to the existing click behavior
        btnOpen.addEventListener('click', function(e) {
            if (window._TWR_fileProcessing) {
                console.log('[TWR] File processing in progress, ignoring open click');
                e.preventDefault();
                e.stopPropagation();
                return;
            }
        }, true); // Use capture phase to run first
        
        console.log('[TWR] File selection guards applied');
    }
    
    // ============================================================
    // FIX 4: CHARTS - Proper rendering with Chart.js
    // ============================================================
    window.renderCharts = function(data) {
        if (!data) {
            console.warn('[TWR] No data for charts');
            return;
        }
        
        console.log('[TWR] Rendering charts...');
        
        // Wait for Chart.js if not loaded
        if (typeof Chart === 'undefined') {
            console.log('[TWR] Chart.js not ready, waiting...');
            loadChartJs().then(() => {
                setTimeout(() => window.renderCharts(data), 100);
            });
            return;
        }
        
        renderSeverityChart(data.by_severity);
        renderCategoryChart(data.by_category);
    };
    
    function renderSeverityChart(severityData) {
        const canvas = document.getElementById('chart-severity');
        if (!canvas || !severityData) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing
        if (window.severityChartInstance) {
            window.severityChartInstance.destroy();
        }
        
        const labels = Object.keys(severityData);
        const values = Object.values(severityData);
        
        if (labels.length === 0 || values.every(v => v === 0)) {
            console.log('[TWR] No severity data to chart');
            return;
        }
        
        const colors = {
            'Critical': '#ef4444',
            'High': '#f97316',
            'Medium': '#eab308',
            'Low': '#22c55e',
            'Info': '#6366f1'
        };
        
        try {
            window.severityChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: labels.map(l => colors[l] || '#64748b'),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8',
                                padding: 8,
                                usePointStyle: true,
                                font: { size: 11 }
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = labels[index];
                            if (typeof setChartFilter === 'function') {
                                setChartFilter('severity', label);
                            }
                        }
                    }
                }
            });
            console.log('[TWR] Severity chart rendered');
        } catch (e) {
            console.error('[TWR] Severity chart error:', e);
        }
    }
    
    function renderCategoryChart(categoryData) {
        const canvas = document.getElementById('chart-categories');
        if (!canvas || !categoryData) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing
        if (window.categoryChartInstance) {
            window.categoryChartInstance.destroy();
        }
        
        // Sort and take top 8
        const sorted = Object.entries(categoryData)
            .filter(([, v]) => v > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8);
        
        if (sorted.length === 0) {
            console.log('[TWR] No category data to chart');
            return;
        }
        
        const fullLabels = sorted.map(([k]) => k); // Keep full labels for filtering
        const displayLabels = sorted.map(([k]) => k.length > 12 ? k.substring(0, 12) + '...' : k);
        const values = sorted.map(([, v]) => v);
        
        try {
            window.categoryChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: displayLabels,
                    datasets: [{
                        label: 'Issues',
                        data: values,
                        backgroundColor: 'rgba(99, 102, 241, 0.7)',
                        borderColor: 'rgba(99, 102, 241, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#94a3b8' }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', font: { size: 10 } }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = fullLabels[index]; // Use full label for filtering
                            if (typeof setChartFilter === 'function') {
                                setChartFilter('category', label);
                            }
                        }
                    }
                }
            });
            console.log('[TWR] Category chart rendered');
        } catch (e) {
            console.error('[TWR] Category chart error:', e);
        }
    }
    
    // ============================================================
    // FIX 5: ROLES BUTTON - Enable after review completes
    // ============================================================
    function enableRolesButton() {
        const btnRoles = document.getElementById('btn-roles');
        if (btnRoles) {
            btnRoles.disabled = false;
            btnRoles.classList.remove('disabled');
            console.log('[TWR] Roles button enabled');
        }
    }
    
    // ============================================================
    // FIX 6: HISTORY BUTTON - Use existing modal system
    // v3.0.0: Improved refresh button handling, proper icon refresh
    // ============================================================
    function fixHistoryButton() {
        // The main btn-scan-history already has a handler via initNewFeatureListeners
        // We just need to ensure btn-refresh-history inside the modal works
        const btnRefresh = document.getElementById('btn-refresh-history');
        if (btnRefresh && !btnRefresh._refreshFixed) {
            btnRefresh._refreshFixed = true;
            
            // v3.0.0: Don't clone - just add the handler directly
            // Cloning can break Lucide icons
            btnRefresh.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[TWR] Refresh history clicked');
                
                // Show loading state
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Loading...';
                this.disabled = true;
                
                try {
                    if (typeof loadScanHistory === 'function') {
                        await loadScanHistory();
                        toast('success', 'Scan history refreshed');
                    }
                } catch (err) {
                    console.error('[TWR] Refresh failed:', err);
                    toast('error', 'Failed to refresh history');
                } finally {
                    // Restore button
                    this.innerHTML = originalHTML;
                    this.disabled = false;
                    // Refresh icons
                    if (typeof lucide !== 'undefined') {
                        try { lucide.createIcons(); } catch(e) {}
                    }
                }
            });
            
            // Fix the cursor style
            btnRefresh.style.cursor = 'pointer';
        }
        
        // Also ensure the main scan history button works
        const btnScanHistory = document.getElementById('btn-scan-history');
        if (btnScanHistory && !btnScanHistory._historyFixed) {
            btnScanHistory._historyFixed = true;
            btnScanHistory.disabled = false;
        }
        
        console.log('[TWR] History buttons fixed');
    }
    
    // NOTE: Removed duplicate showScanHistory() - using existing loadScanHistory() from main code
    
    // ============================================================
    // FIX 7: DIAGNOSTICS EXPORT - Use existing function, just ensure button works
    // ============================================================
    // The exportDiagnostics function is already defined elsewhere and works correctly.
    // We just need to ensure the button triggers it.
    (function ensureDiagnosticsButton() {
        const btn = document.querySelector('#modal-diagnostics .btn-primary');
        if (btn && !btn._diagnosticsFixed) {
            btn._diagnosticsFixed = true;
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                if (typeof window.exportDiagnostics === 'function') {
                    window.exportDiagnostics();
                }
            });
        }
    })();
    
    // ============================================================
    // FIX 8: EMAIL DIAGNOSTICS - Include actual data
    // ============================================================
    window.emailDiagnostics = function() {
        console.log('[TWR] Creating diagnostic email...');
        
        const diagnostics = {
            timestamp: new Date().toISOString(),
            session_id: window.sessionId || 'unknown',
            version: '2.8.6',
            browser: navigator.userAgent,
            url: window.location.href,
            filename: typeof State !== 'undefined' ? State.filename : 'No document',
            issues_count: typeof State !== 'undefined' ? (State.issues?.length || 0) : 0,
            errors: (window.capturedErrors || []).slice(-10)
        };
        
        const body = `
DIAGNOSTIC SUMMARY
==================
Timestamp: ${diagnostics.timestamp}
Session ID: ${diagnostics.session_id}
Version: ${diagnostics.version}

FRONTEND STATE
==============
Document: ${diagnostics.filename}
Issues Found: ${diagnostics.issues_count}

BROWSER INFO
============
${diagnostics.browser}
URL: ${diagnostics.url}

RECENT ERRORS
=============
${diagnostics.errors.map(e => `- ${e.message || e}`).join('\n') || 'No errors captured'}

ISSUE DESCRIPTION
================
[Please describe the issue you encountered]

STEPS TO REPRODUCE
==================
1. 
2. 
3. 
        `.trim();
        
        const subject = encodeURIComponent(`AEGIS Bug Report - ${new Date().toLocaleDateString()}`);
        const encodedBody = encodeURIComponent(body);
        const email = 'nicholas.georgeson@gmail.com';
        
        window.location.href = `mailto:${email}?subject=${subject}&body=${encodedBody}`;
    };
    
    // ============================================================
    // FIX 9: UPDATE BUTTON IN UI - Add to settings modal
    // ============================================================
    function addUpdateButtonToSettings() {
        const settingsModal = document.getElementById('modal-settings');
        if (!settingsModal) return;
        
        // Check if updates tab already exists (check both possible IDs)
        if (document.getElementById('settings-tab-updates')) return;
        if (settingsModal.querySelector('[data-tab="updates"]')) return;
        
        // Add updates tab
        const tabList = settingsModal.querySelector('.settings-tabs');
        if (tabList) {
            const updateTab = document.createElement('button');
            updateTab.className = 'settings-tab';
            updateTab.id = 'settings-tab-updates';
            updateTab.textContent = 'Updates';
            updateTab.onclick = () => {
                showSettingsModal();
                setTimeout(() => switchSettingsTab('updates'), 100);
            };
            tabList.appendChild(updateTab);
        }
        
        // Add updates panel
        const tabContent = settingsModal.querySelector('.settings-content');
        if (tabContent) {
            const updatePanel = document.createElement('div');
            updatePanel.className = 'settings-panel';
            updatePanel.id = 'settings-panel-updates';
            updatePanel.style.display = 'none';
            updatePanel.innerHTML = `
                <h4>Software Updates</h4>
                <p>Check for and apply updates to AEGIS.</p>
                <div class="update-actions" style="margin-top: 16px;">
                    <button class="btn btn-primary" onclick="checkForUpdates()">
                        Check for Updates
                    </button>
                </div>
                <div id="update-status" style="margin-top: 16px;"></div>
                <div id="update-list" style="margin-top: 16px;"></div>
            `;
            tabContent.appendChild(updatePanel);
        }
        
        console.log('[TWR] Update button added to settings');
    }
    
    // ============================================================
    // FIX 9: UPDATE AND BACKUP FUNCTIONS
    // ============================================================
    window.checkForUpdates = async function() {
        const statusDiv = document.getElementById('update-status');
        if (statusDiv) {
            statusDiv.innerHTML = '<p><i data-lucide="loader" class="spin"></i> Checking for updates...</p>';
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }

        // v5.0.5: Add timeout to prevent infinite spinning
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);

        try {
            const result = await api('/updates/check', 'GET', null, { signal: controller.signal });
            clearTimeout(timeout);
            if (result && result.success) {
                const data = result.data || {};
                // Check has_updates boolean and updates array (backend property names)
                if (data.has_updates && data.updates && data.updates.length > 0) {
                    if (statusDiv) {
                        statusDiv.innerHTML = `
                            <div class="update-available" style="padding: 12px; background: var(--success-emphasis); border-radius: 8px; color: white;">
                                <strong>${data.count || data.updates.length} update(s) available</strong>
                                <button class="btn btn-sm" onclick="applyUpdates()" style="margin-left: 12px;">Apply Updates</button>
                            </div>
                        `;
                    }
                } else {
                    if (statusDiv) {
                        statusDiv.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px; color: var(--success);">
                                <i data-lucide="check-circle"></i>
                                <span>You're up to date. Last checked: ${new Date().toLocaleString()}</span>
                            </div>
                        `;
                        if (typeof lucide !== 'undefined') lucide.createIcons();
                    }
                }
            } else {
                clearTimeout(timeout);
                if (statusDiv) {
                    const errMsg = result?.error || 'Update check service not available';
                    statusDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 8px; color: var(--text-muted);">
                            <i data-lucide="info"></i>
                            <span>${escapeHtml(errMsg)}. Last checked: ${new Date().toLocaleString()}</span>
                        </div>
                    `;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
            }
        } catch (e) {
            clearTimeout(timeout);
            console.warn('[TWR] Update check failed:', e);
            if (statusDiv) {
                const msg = e.name === 'AbortError' ? 'Update check timed out' : 'Could not reach update server';
                statusDiv.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px; color: var(--text-muted);">
                        <i data-lucide="info"></i>
                        <span>${msg}. <a href="#" onclick="checkForUpdates(); return false;" style="color: var(--link);">Retry</a></span>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    };
    
    window.loadBackups = async function() {
        const backupList = document.getElementById('backup-list');
        const rollbackBtn = document.getElementById('btn-rollback');
        if (!backupList) return;
        
        backupList.innerHTML = '<p class="help-text">Loading backups...</p>';
        
        try {
            const result = await api('/updates/backups', 'GET');
            if (result && result.success && result.data) {
                const backups = result.data;
                if (backups.length === 0) {
                    backupList.innerHTML = '<p class="help-text">No backups available.</p>'; // SAFE: static HTML
                    // v3.0.109: Disable rollback button when no backups
                    if (rollbackBtn) rollbackBtn.disabled = true;
                } else {
                    // SAFE: b.name, b.created_at escaped via escapeHtml()
                    backupList.innerHTML = backups.map(b => `
                        <div class="backup-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-muted);">
                            <div>
                                <strong>${escapeHtml(b.name || 'Backup')}</strong>
                                <span class="help-text" style="margin-left: 8px;">${escapeHtml(b.created_at || '')}</span>
                            </div>
                            <button class="btn btn-xs btn-secondary" onclick="restoreBackup('${escapeHtml(b.name)}')">Restore</button>
                        </div>
                    `).join('');
                    // v3.0.109: Enable rollback button when backups exist
                    if (rollbackBtn) rollbackBtn.disabled = false;
                }
            } else {
                backupList.innerHTML = '<p class="help-text">No backups available.</p>';
                if (rollbackBtn) rollbackBtn.disabled = true;
            }
        } catch (e) {
            console.warn('[TWR] Failed to load backups:', e);
            backupList.innerHTML = '<p class="help-text">No backups available.</p>';
            if (rollbackBtn) rollbackBtn.disabled = true;
        }
    };
    
    window.restoreBackup = async function(backupName) {
        if (!confirm('Are you sure you want to restore this backup? Current files will be overwritten.')) {
            return;
        }
        
        try {
            // v3.0.109: Fixed endpoint - /api/updates/rollback is the correct backend route
            const result = await api('/updates/rollback', 'POST', { backup_name: backupName });
            if (result && result.success) {
                toast('success', 'Backup restored successfully. Restarting server...');
                // Trigger restart and poll for server
                try {
                    await api('/updates/restart', 'POST');
                } catch (e) {
                    // Expected - server is restarting
                }
                setTimeout(() => pollServerRestart(), 2000);
            } else {
                toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Failed to restore backup');
            }
        } catch (e) {
            toast('error', 'Failed to restore backup: ' + e.message);
        }
    };
    
    window.applyUpdates = async function() {
        if (!confirm('Apply all available updates? The server will restart automatically.')) return;
        
        const statusDiv = document.getElementById('update-status');
        
        try {
            // Step 1: Apply the updates
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                        <p><i data-lucide="loader" class="spin"></i> Applying updates...</p>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            const result = await api('/updates/apply', 'POST');
            if (!result || !result.success) {
                toast('error', result?.error || 'Failed to apply updates');
                if (statusDiv) statusDiv.innerHTML = '<p style="color: var(--danger);">Update failed. Please try again.</p>';
                return;
            }
            
            // Step 2: Trigger server restart
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                        <p><i data-lucide="loader" class="spin"></i> Updates applied. Restarting server...</p>
                        <p class="help-text" style="margin-top: 8px;">Please wait, this will take a few seconds.</p>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            // Call restart endpoint (will return before server exits)
            try {
                await api('/updates/restart', 'POST');
            } catch (e) {
                // Expected - server may close connection during restart
            }
            
            // Step 3: Poll until server is back
            await pollForServerRestart();
            
        } catch (e) {
            console.error('[TWR] Update error:', e);
            toast('error', 'Failed to apply updates');
            if (statusDiv) statusDiv.innerHTML = '<p style="color: var(--danger);">Update failed.</p>';
        }
    };
    
    /**
     * Poll the server health endpoint until it responds, then refresh the page.
     */
    async function pollForServerRestart(maxAttempts = 30, intervalMs = 1000) {
        const statusDiv = document.getElementById('update-status');
        let attempts = 0;
        
        // Wait a moment for server to actually stop
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        while (attempts < maxAttempts) {
            attempts++;
            
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                        <p><i data-lucide="loader" class="spin"></i> Waiting for server to restart...</p>
                        <p class="help-text" style="margin-top: 8px;">Attempt ${attempts}/${maxAttempts}</p>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            try {
                const response = await fetch('/api/updates/health', { 
                    method: 'GET',
                    cache: 'no-store'
                });
                
                if (response.ok) {
                    // Server is back! Show success and refresh
                    if (statusDiv) {
                        statusDiv.innerHTML = `
                            <div style="padding: 16px; background: var(--success-emphasis); border-radius: 8px; color: white;">
                                <p><i data-lucide="check-circle"></i> Server restarted successfully!</p>
                                <p style="margin-top: 8px;">Refreshing page...</p>
                            </div>
                        `;
                        if (typeof lucide !== 'undefined') lucide.createIcons();
                    }
                    
                    // Brief pause to show success message, then hard refresh
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    window.location.reload(true);
                    return;
                }
            } catch (e) {
                // Server not ready yet, continue polling
            }
            
            await new Promise(resolve => setTimeout(resolve, intervalMs));
        }
        
        // Max attempts reached
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div style="padding: 16px; background: var(--warning-emphasis); border-radius: 8px;">
                    <p><i data-lucide="alert-triangle"></i> Server is taking longer than expected.</p>
                    <p style="margin-top: 8px;">Please manually refresh the page or restart the server.</p>
                    <button class="btn btn-sm" onclick="location.reload(true)" style="margin-top: 12px;">Refresh Now</button>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }
    
    // Load backups when updates tab is shown
    const existingUpdateTab = document.querySelector('[data-tab="updates"]');
    if (existingUpdateTab) {
        existingUpdateTab.addEventListener('click', () => {
            setTimeout(loadBackups, 100);
        });
    }
    
    // ============================================================
    // FIX 10: LOADING STATE - Better handling
    // ============================================================
    window.setLoading = function(loading, message) {
        if (typeof State !== 'undefined') {
            State.isLoading = loading;
        }
        
        const btnReview = document.getElementById('btn-review');
        const loadingOverlay = document.getElementById('loading-overlay');
        
        if (btnReview) {
            btnReview.disabled = loading;
            btnReview.innerHTML = loading 
                ? '<span class="spinner"></span> Analyzing...'
                : '<span data-lucide="play" class="icon"></span> Run Review';
            
            // Refresh icons
            if (!loading && typeof lucide !== 'undefined') {
                setTimeout(() => lucide.createIcons(), 100);
            }
        }
        
        if (loadingOverlay) {
            loadingOverlay.style.display = loading ? 'flex' : 'none';
            if (message) {
                const msgEl = loadingOverlay.querySelector('.loading-message');
                if (msgEl) msgEl.textContent = message;
            }
        }
    };
    
    // ============================================================
    // FIX 11: ERROR CAPTURE - Store errors for diagnostics
    // ============================================================
    window.capturedErrors = [];
    window.consoleLog = [];
    
    const originalConsoleError = console.error;
    console.error = function(...args) {
        window.capturedErrors.push({
            timestamp: new Date().toISOString(),
            message: args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')
        });
        // Keep only last 50
        if (window.capturedErrors.length > 50) {
            window.capturedErrors.shift();
        }
        originalConsoleError.apply(console, args);
    };
    
    // ============================================================
    // FIX 12: REVIEW COMPLETION - Enable buttons and render data
    // ============================================================
    const originalRunReview = window.runReview;
    window.runReview = async function() {
        // Check if lucide is available
        if (typeof lucide === 'undefined') {
            console.error('[TWR] Lucide not loaded, loading now...');
            await loadLucideIcons();
        }
        
        // Call original if exists, otherwise do our own
        if (typeof originalRunReview === 'function') {
            return originalRunReview();
        }
    };
    
    // Hook into review completion
    function onReviewComplete(data) {
        console.log('[TWR] Review complete, enabling features...');
        
        // Enable roles button
        enableRolesButton();
        
        // Render charts
        if (data) {
            window.renderCharts(data);
        }
        
        // Refresh icons
        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons(), 100);
        }
    }
    
    // ============================================================
    // INITIALIZATION
    // ============================================================
    async function initFixes() {
        if (FixState.initialized) return;
        FixState.initialized = true;
        
        console.log('[TWR] Initializing comprehensive fixes...');
        
        // Load required libraries
        await loadLucideIcons();
        await loadChartJs();
        
        // Fix file selection (must wait for DOM)
        fixFileSelection();
        
        // Fix history button
        fixHistoryButton();
        
        // Add update button
        addUpdateButtonToSettings();
        
        // Fix search input (ensure it triggers applyFilters)
        fixSearchInput();
        
        // Initialize icons
        if (typeof lucide !== 'undefined') {
            try {
                if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
            } catch (e) {
                console.warn('[TWR] Initial icon creation failed:', e);
            }
        }
        
        console.log('[TWR] Comprehensive fixes initialized');
    }
    
    // Fix search input to ensure it works
    function fixSearchInput() {
        const searchInput = document.getElementById('issue-search');
        if (!searchInput) return;
        
        // Remove existing listeners by cloning
        const newInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newInput, searchInput);
        
        // Add fresh listener with debounce
        let searchTimeout;
        newInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (typeof applyFilters === 'function') {
                    applyFilters();
                }
            }, 300);
        });
        
        // Also handle Enter key
        newInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                if (typeof applyFilters === 'function') {
                    applyFilters();
                }
            }
        });
        
        console.log('[TWR] Search input fixed');
    }
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFixes);
    } else {
        // DOM already loaded, run after short delay to let other scripts run
        setTimeout(initFixes, 100);
    }
    
    // Also expose for manual triggering
    window.TWR_InitFixes = initFixes;
    window.TWR_OnReviewComplete = onReviewComplete;
    
})();

// v3.0.11: Initialization complete

// ============================================================
// BATCH UPLOAD FUNCTIONALITY
// ============================================================

(function() {
    'use strict';
    
    const BatchState = {
        files: [],
        processing: false,
        results: null
    };
    
    function initBatchUpload() {
        // Single file upload button
        document.getElementById('btn-upload-single')?.addEventListener('click', () => {
            document.getElementById('file-input')?.click();
        });
        
        // Batch upload button (v3.0.114: Fixed ID mismatch - was btn-upload-batch, HTML uses btn-batch-load)
        document.getElementById('btn-batch-load')?.addEventListener('click', openBatchModal);
        
        // Close modal
        document.getElementById('btn-close-batch-modal')?.addEventListener('click', closeBatchModal);
        document.getElementById('btn-cancel-batch')?.addEventListener('click', closeBatchModal);
        // v5.9.38: Minimize button
        document.getElementById('btn-minimize-batch-modal')?.addEventListener('click', minimizeBatchModal);
        
        // Batch dropzone
        const batchDropzone = document.getElementById('batch-dropzone');
        const batchInput = document.getElementById('batch-file-input');
        const batchFolderInput = document.getElementById('batch-folder-input');
        const btnSelectFiles = document.getElementById('btn-select-files');
        const btnSelectFolder = document.getElementById('btn-select-folder');

        if (batchDropzone) {
            // Don't trigger file dialog when clicking buttons
            batchDropzone.addEventListener('click', (e) => {
                if (e.target.closest('.batch-upload-buttons')) return;
                batchInput?.click();
            });
            batchDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                batchDropzone.classList.add('drag-over');
            });
            batchDropzone.addEventListener('dragleave', () => {
                batchDropzone.classList.remove('drag-over');
            });
            batchDropzone.addEventListener('drop', async (e) => {
                e.preventDefault();
                batchDropzone.classList.remove('drag-over');
                // Handle folder drops using DataTransferItem API
                if (e.dataTransfer.items) {
                    const files = await getFilesFromDataTransfer(e.dataTransfer.items);
                    handleBatchFiles(files);
                } else {
                    handleBatchFiles(e.dataTransfer.files);
                }
            });
        }

        // Select Files button
        if (btnSelectFiles) {
            btnSelectFiles.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchInput?.click();
            });
        }

        // Select Folder button
        if (btnSelectFolder) {
            btnSelectFolder.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchFolderInput?.click();
            });
        }

        if (batchInput) {
            batchInput.addEventListener('change', (e) => {
                handleBatchFiles(e.target.files);
            });
        }

        // Folder input handler
        if (batchFolderInput) {
            batchFolderInput.addEventListener('change', (e) => {
                handleBatchFiles(e.target.files);
            });
        }

        // v5.5.0: Server-side folder scan handlers
        const folderScanPath = document.getElementById('folder-scan-path');
        const btnFolderDiscover = document.getElementById('btn-folder-discover');
        const btnFolderScan = document.getElementById('btn-folder-scan');
        const folderScanPreview = document.getElementById('folder-scan-preview');

        if (btnFolderDiscover) {
            btnFolderDiscover.addEventListener('click', async () => {
                const folderPath = folderScanPath?.value?.trim();
                if (!folderPath) {
                    window.showToast?.('Please enter a folder path', 'warning');
                    return;
                }
                btnFolderDiscover.disabled = true;
                btnFolderDiscover.innerHTML = '<i data-lucide="loader" class="spin"></i> Scanning...';
                try {
                    const resp = await fetch('/api/review/folder-discover', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || ''
                        },
                        body: JSON.stringify({ folder_path: folderPath })
                    });
                    const json = await resp.json();
                    if (json.success && json.data) {
                        const d = json.data;
                        let html = `<div class="folder-scan-stats">`;
                        html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${d.total_files}</div><div class="folder-scan-stat-label">Documents</div></div>`;
                        html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${d.total_size_human}</div><div class="folder-scan-stat-label">Total Size</div></div>`;
                        // Type breakdown
                        const types = d.type_breakdown || {};
                        Object.entries(types).forEach(([ext, count]) => {
                            html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${count}</div><div class="folder-scan-stat-label">${ext}</div></div>`;
                        });
                        html += `</div>`;
                        // File list
                        if (d.files && d.files.length > 0) {
                            html += `<div class="folder-scan-file-list">`;
                            d.files.forEach(f => {
                                html += `<div class="folder-scan-file-item">
                                    <span class="folder-scan-file-path" title="${f.relative_path}">${f.relative_path}</span>
                                    <span class="folder-scan-file-size">${f.size_human}</span>
                                </div>`;
                            });
                            html += `</div>`;
                        }
                        folderScanPreview.innerHTML = html;
                        folderScanPreview.classList.remove('hidden');
                        window.showToast?.(`Found ${d.total_files} documents (${d.total_size_human})`, 'success');
                    } else {
                        window.showToast?.(json.error?.message || 'Discovery failed', 'error');
                    }
                } catch (err) {
                    console.error('[TWR] Folder discover error:', err);
                    window.showToast?.('Failed to scan folder: ' + err.message, 'error');
                } finally {
                    btnFolderDiscover.disabled = false;
                    btnFolderDiscover.innerHTML = '<i data-lucide="search"></i> Preview';
                    lucide?.createIcons?.();
                }
            });
        }

        // ====================================================================
        // v5.7.0: Async Folder Scan with Real-Time Progress Polling
        // ====================================================================
        if (btnFolderScan) {
            btnFolderScan.addEventListener('click', async () => {
                const folderPath = folderScanPath?.value?.trim();
                if (!folderPath) {
                    window.showToast?.('Please enter a folder path', 'warning');
                    return;
                }
                if (!confirm(`Scan all documents in:\n${folderPath}\n\nThis may take several minutes for large repositories.`)) {
                    return;
                }
                btnFolderScan.disabled = true;
                btnFolderDiscover.disabled = true;
                btnFolderScan.innerHTML = '<i data-lucide="loader" class="spin"></i> Starting...';
                folderScanPreview.classList.add('hidden');

                try {
                    // ── Step 1: Start async scan (returns scan_id + discovery immediately) ──
                    const startResp = await fetch('/api/review/folder-scan-start', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || ''
                        },
                        body: JSON.stringify({ folder_path: folderPath })
                    });
                    const startJson = await startResp.json();
                    if (!startJson.success || !startJson.data?.scan_id) {
                        const errMsg = startJson.data?.message || startJson.error?.message || 'Failed to start scan';
                        window.showToast?.(errMsg, startJson.data?.scan_id === null ? 'info' : 'error');
                        folderScanPreview.innerHTML = `<p style="color:var(--text-muted);">${escapeHtml(errMsg)}</p>`;
                        folderScanPreview.classList.remove('hidden');
                        return;
                    }

                    const scanId = startJson.data.scan_id;
                    const discovery = startJson.data.discovery;
                    const totalFiles = discovery.total_discovered;

                    console.log(`[TWR FolderScan] Started scan ${scanId}: ${totalFiles} files`);

                    // ── Step 2: Show progress dashboard (reuse bpd-* classes) ──
                    const dashEl = document.getElementById('folder-scan-dashboard');
                    const fsDocsComplete = document.getElementById('fs-docs-complete');
                    const fsDocsTotal = document.getElementById('fs-docs-total');
                    const fsPercent = document.getElementById('fs-percent');
                    const fsFill = document.getElementById('fs-progress-fill');
                    const fsGlow = document.getElementById('fs-progress-glow');
                    const fsElapsed = document.getElementById('fs-elapsed-time');
                    const fsRemaining = document.getElementById('fs-remaining-time');
                    const fsSpeed = document.getElementById('fs-speed');
                    const fsQueueStatus = document.getElementById('fs-queue-status');
                    const fsDocList = document.getElementById('fs-doc-list');
                    const fsIssueCount = document.getElementById('fs-issues-found');

                    if (dashEl) {
                        dashEl.classList.remove('hidden');
                        dashEl.classList.add('scanning');
                        folderScanPreview.classList.add('hidden');
                    }
                    if (fsDocsTotal) fsDocsTotal.textContent = totalFiles;
                    if (fsDocsComplete) fsDocsComplete.textContent = '0';
                    if (fsPercent) fsPercent.textContent = '0%';
                    if (fsIssueCount) fsIssueCount.textContent = '0';

                    // v5.9.39: Show minimize button when folder scan starts
                    const minBtnFS = document.getElementById('btn-minimize-batch-modal');
                    if (minBtnFS) minBtnFS.style.display = '';

                    // Build initial doc rows from discovery
                    if (fsDocList) {
                        fsDocList.innerHTML = discovery.files.map((f, i) => `
                            <div class="bpd-doc-row queued" id="fs-doc-${i}">
                                <div class="bpd-doc-icon"><div class="bpd-pending-dot"></div></div>
                                <div class="bpd-doc-content">
                                    <div class="bpd-doc-name">${escapeHtml(f.filename)}</div>
                                    <div class="bpd-doc-detail" id="fs-doc-meta-${i}">Queued — ${f.relative_path}</div>
                                </div>
                                <div class="bpd-doc-bar" id="fs-doc-progress-${i}">
                                    <div class="bpd-doc-bar-fill" id="fs-doc-fill-${i}" style="width:0%"></div>
                                </div>
                                <div class="bpd-doc-duration" id="fs-doc-duration-${i}"></div>
                            </div>
                        `).join('');
                    }
                    if (window.lucide) window.lucide.createIcons();

                    btnFolderScan.innerHTML = '<i data-lucide="loader" class="spin"></i> Scanning...';
                    if (window.lucide) window.lucide.createIcons();

                    // Build filename→index map for fast lookup
                    const fileIndexMap = {};
                    discovery.files.forEach((f, i) => { fileIndexMap[f.filename] = i; });

                    // ── Step 3: Poll for progress ──
                    let lastDocCount = 0;
                    let pollInterval = null;
                    let lastProcessedTimestamp = Date.now();

                    const _formatFSTime = (seconds) => {
                        if (!seconds || seconds < 0) return '--:--';
                        const m = Math.floor(seconds / 60);
                        const s = Math.floor(seconds % 60);
                        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                    };

                    const _updateFSDocRow = (idx, status, detail, grade, score, issueCount) => {
                        const row = document.getElementById(`fs-doc-${idx}`);
                        const metaEl = document.getElementById(`fs-doc-meta-${idx}`);
                        const fillEl = document.getElementById(`fs-doc-fill-${idx}`);
                        if (row) {
                            row.className = `bpd-doc-row ${status}`;
                            const iconDiv = row.querySelector('.bpd-doc-icon');
                            if (iconDiv) {
                                if (status === 'processing') {
                                    iconDiv.innerHTML = '<div class="bpd-spinner"></div>';
                                    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                                } else if (status === 'complete') {
                                    iconDiv.innerHTML = '<div class="bpd-check"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg></div>';
                                } else if (status === 'error') {
                                    iconDiv.innerHTML = '<div class="bpd-error-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></div>';
                                }
                            }
                        }
                        if (metaEl) metaEl.textContent = detail;
                        if (fillEl) fillEl.style.width = (status === 'complete' || status === 'error') ? '100%' : '50%';
                    };

                    const pollProgress = async () => {
                        try {
                            const resp = await fetch(`/api/review/folder-scan-progress/${scanId}?since=${lastDocCount}`);
                            const json = await resp.json();
                            if (!json.success) return;

                            const data = json.data;
                            const done = data.processed + data.errors;
                            const pct = totalFiles > 0 ? Math.round((done / totalFiles) * 100) : 0;

                            // Update stats
                            if (fsDocsComplete) fsDocsComplete.textContent = done;
                            if (fsPercent) fsPercent.textContent = pct + '%';
                            if (fsFill) fsFill.style.width = pct + '%';
                            if (fsGlow) fsGlow.style.width = pct + '%';
                            if (fsElapsed) fsElapsed.textContent = _formatFSTime(data.elapsed_seconds);
                            if (fsRemaining) fsRemaining.textContent = _formatFSTime(data.estimated_remaining);
                            if (fsIssueCount) fsIssueCount.textContent = data.summary?.total_issues || 0;

                            // Speed calc
                            if (fsSpeed && data.elapsed_seconds > 0 && done > 0) {
                                const docsPerMin = (done / data.elapsed_seconds * 60).toFixed(1);
                                fsSpeed.textContent = docsPerMin + '/min';
                            }

                            // Queue status
                            if (fsQueueStatus) {
                                if (data.phase === 'complete') {
                                    fsQueueStatus.textContent = 'Complete';
                                } else if (data.current_file) {
                                    fsQueueStatus.textContent = `Chunk ${data.current_chunk}/${data.total_chunks} — ${data.current_file}`;
                                } else {
                                    fsQueueStatus.textContent = `Processing chunk ${data.current_chunk}/${data.total_chunks}...`;
                                }
                            }

                            // Mark currently processing file
                            if (data.current_file && data.phase === 'reviewing') {
                                const idx = fileIndexMap[data.current_file];
                                if (idx !== undefined) {
                                    const row = document.getElementById(`fs-doc-${idx}`);
                                    if (row && !row.classList.contains('complete') && !row.classList.contains('error')) {
                                        _updateFSDocRow(idx, 'processing', `Analyzing ${data.current_file}...`);
                                    }
                                }
                            }

                            // Update newly completed documents
                            if (data.documents && data.documents.length > 0) {
                                data.documents.forEach(doc => {
                                    const idx = fileIndexMap[doc.filename];
                                    if (idx === undefined) return;
                                    if (doc.status === 'error') {
                                        _updateFSDocRow(idx, 'error', `Error: ${doc.error || 'Unknown'}`);
                                    } else {
                                        _updateFSDocRow(idx, 'complete',
                                            `${(doc.word_count || 0).toLocaleString()} words • ${doc.issue_count} issues • ${doc.role_count || 0} roles • Score: ${doc.score}%`,
                                            doc.grade, doc.score, doc.issue_count);
                                    }
                                });
                                lastDocCount = data.total_documents_ready;
                            }

                            // ── Check if done ──
                            if (data.phase === 'complete' || data.phase === 'error') {
                                clearInterval(pollInterval);
                                pollInterval = null;

                                if (dashEl) {
                                    dashEl.classList.remove('scanning');
                                    dashEl.classList.add('bpd-complete');
                                }

                                // Build final summary below the dashboard
                                const summary = data.summary || {};
                                const grades = summary.grade_distribution || {};
                                let summaryHtml = `<div class="folder-scan-stats" style="margin-top:12px;">`;
                                summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${totalFiles}</div><div class="folder-scan-stat-label">Discovered</div></div>`;
                                summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.processed || 0}</div><div class="folder-scan-stat-label">Scanned</div></div>`;
                                summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.errors || 0}</div><div class="folder-scan-stat-label">Errors</div></div>`;
                                summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.total_issues || 0}</div><div class="folder-scan-stat-label">Issues</div></div>`;
                                summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${_formatFSTime(data.elapsed_seconds)}</div><div class="folder-scan-stat-label">Time</div></div>`;
                                summaryHtml += `</div>`;

                                if (Object.keys(grades).length > 0) {
                                    summaryHtml += `<div style="margin-top:8px;"><strong style="font-size:12px;color:var(--text-muted);">Grade Distribution:</strong> `;
                                    Object.entries(grades).sort().forEach(([grade, count]) => {
                                        summaryHtml += `<span style="margin-right:12px;font-size:13px;">${grade}: <strong>${count}</strong></span>`;
                                    });
                                    summaryHtml += `</div>`;
                                }

                                folderScanPreview.innerHTML = summaryHtml;
                                folderScanPreview.classList.remove('hidden');

                                const msg = data.phase === 'error'
                                    ? `Folder scan failed: ${data.error_message || 'Unknown error'}`
                                    : `Folder scan complete: ${done} documents, ${summary.total_issues || 0} issues in ${_formatFSTime(data.elapsed_seconds)}`;
                                window.showToast?.(msg, data.phase === 'error' ? 'error' : 'success');

                                btnFolderScan.disabled = false;
                                btnFolderDiscover.disabled = false;
                                btnFolderScan.innerHTML = '<i data-lucide="scan-line"></i> Scan All';
                                if (window.lucide) window.lucide.createIcons();
                            }

                        } catch (pollErr) {
                            console.error('[TWR FolderScan] Poll error:', pollErr);
                        }
                    };

                    // Start polling every 1.5 seconds
                    pollInterval = setInterval(pollProgress, 1500);
                    // Also run immediately
                    pollProgress();

                } catch (err) {
                    console.error('[TWR FolderScan] Start error:', err);
                    window.showToast?.('Folder scan failed: ' + err.message, 'error');
                    folderScanPreview.innerHTML = `<p style="color:var(--danger);">Error: ${escapeHtml(err.message)}</p>`;
                    folderScanPreview.classList.remove('hidden');
                    btnFolderScan.disabled = false;
                    btnFolderDiscover.disabled = false;
                    btnFolderScan.innerHTML = '<i data-lucide="scan-line"></i> Scan All';
                    if (window.lucide) window.lucide.createIcons();
                }
            });
        }

        // ====================================================================
        // v5.9.29/v5.9.38: SharePoint Online Scan Handlers
        // v5.9.53: Fresh CSRF token helper — prevents stale token errors
        // ====================================================================
        async function _freshCSRF() {
            try {
                const r = await fetch('/api/csrf-token');
                const d = await r.json();
                if (d.csrf_token) {
                    window.CSRF_TOKEN = d.csrf_token;
                    return d.csrf_token;
                }
            } catch(e) { /* fall through */ }
            return window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
        }

        const btnSpTest = document.getElementById('btn-sp-test');
        const btnSpDiscover = document.getElementById('btn-sp-discover');
        const btnSpScan = document.getElementById('btn-sp-scan');
        const btnSpConnectScan = document.getElementById('btn-sp-connect-scan');
        const spSiteUrl = document.getElementById('sp-site-url');
        const spLibraryPath = document.getElementById('sp-library-path');
        const spRecursive = document.getElementById('sp-recursive');
        const spConnectionStatus = document.getElementById('sp-connection-status');
        const spFilePreview = document.getElementById('sp-file-preview');

        // v5.9.42: Don't split the URL client-side — send the full URL to the backend.
        // The server-side parse_sharepoint_url() handles all URL formats including
        // ?id=, ?RootFolder=, /:f:/s/, /Forms/AllItems.aspx, etc.
        // Just clean up obvious junk from the pasted URL.
        if (spSiteUrl) {
            const _spCleanUrl = () => {
                let url = spSiteUrl.value.trim();
                if (!url) return;
                // Remove trailing hash fragments (#) that SharePoint adds
                url = url.replace(/#.*$/, '').trim().replace(/\/+$/, '');
                spSiteUrl.value = url;
            };
            spSiteUrl.addEventListener('change', _spCleanUrl);
            spSiteUrl.addEventListener('paste', () => setTimeout(_spCleanUrl, 100));
        }

        // Test Connection button
        if (btnSpTest) {
            btnSpTest.addEventListener('click', async () => {
                const siteUrl = spSiteUrl?.value?.trim();
                if (!siteUrl) {
                    window.showToast?.('Please enter a SharePoint site URL', 'warning');
                    return;
                }
                btnSpTest.disabled = true;
                btnSpTest.innerHTML = '<i data-lucide="loader" class="spin"></i> Testing...';
                try {
                    const csrf = await _freshCSRF();
                    const resp = await fetch('/api/review/sharepoint-test', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': csrf
                        },
                        body: JSON.stringify({ site_url: siteUrl })
                    });
                    const json = await resp.json();
                    if (spConnectionStatus) {
                        spConnectionStatus.classList.remove('hidden');
                        if (json.success && json.data) {
                            spConnectionStatus.style.background = 'rgba(34,197,94,0.1)';
                            spConnectionStatus.style.border = '1px solid rgba(34,197,94,0.3)';
                            spConnectionStatus.style.color = 'var(--success, #22c55e)';
                            let connMsg = `<strong>✓ Connected</strong> — ${escapeHtml(json.data.title || 'SharePoint site')} (${json.data.auth_method})`;
                            if (json.data.ssl_fallback) connMsg += ' <span style="opacity:0.7;font-size:11px">[SSL bypass active]</span>';
                            spConnectionStatus.innerHTML = connMsg;
                            // v5.9.42: Auto-fill library path from server auto-detection
                            if (json.data.parsed_library_path) {
                                spLibraryPath.value = json.data.parsed_library_path;
                                const spLibVis = document.getElementById('sp-library-path-visible');
                                if (spLibVis) spLibVis.value = json.data.parsed_library_path;
                            }
                            if (btnSpDiscover) btnSpDiscover.disabled = false;
                            window.showToast?.(`Connected to "${json.data.title}"`, 'success');
                        } else {
                            spConnectionStatus.style.background = 'rgba(239,68,68,0.1)';
                            spConnectionStatus.style.border = '1px solid rgba(239,68,68,0.3)';
                            spConnectionStatus.style.color = 'var(--danger, #ef4444)';
                            spConnectionStatus.innerHTML = `<strong>✗ Failed</strong> — ${escapeHtml(json.data?.message || json.error?.message || 'Connection failed')}`;
                            window.showToast?.(json.data?.message || json.error?.message || 'Connection failed', 'error');
                        }
                    }
                } catch (err) {
                    console.error('[TWR SP] Test error:', err);
                    window.showToast?.('SharePoint test failed: ' + err.message, 'error');
                    if (spConnectionStatus) {
                        spConnectionStatus.classList.remove('hidden');
                        spConnectionStatus.style.background = 'rgba(239,68,68,0.1)';
                        spConnectionStatus.style.border = '1px solid rgba(239,68,68,0.3)';
                        spConnectionStatus.style.color = 'var(--danger, #ef4444)';
                        spConnectionStatus.innerHTML = `<strong>✗ Error</strong> — ${escapeHtml(err.message)}`;
                    }
                } finally {
                    btnSpTest.disabled = false;
                    btnSpTest.innerHTML = '<i data-lucide="plug"></i> Test';
                    lucide?.createIcons?.();
                }
            });
        }

        // v5.9.38: Connect & Scan button — one-click flow
        // Tests connection, auto-detects library, discovers files, and starts scan
        if (btnSpConnectScan) {
            btnSpConnectScan.addEventListener('click', async () => {
                const siteUrl = spSiteUrl?.value?.trim();
                if (!siteUrl) {
                    window.showToast?.('Please enter a SharePoint site URL', 'warning');
                    spSiteUrl?.focus();
                    return;
                }

                // Disable all SP buttons during operation
                [btnSpConnectScan, btnSpTest, btnSpDiscover, btnSpScan].forEach(b => { if (b) b.disabled = true; });
                btnSpConnectScan.innerHTML = '<i data-lucide="loader" class="spin"></i> Connecting...';
                lucide?.createIcons?.();

                try {
                    const csrf = await _freshCSRF();
                    const resp = await fetch('/api/review/sharepoint-connect-and-scan', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': csrf
                        },
                        body: JSON.stringify({
                            site_url: siteUrl,
                            library_path: spLibraryPath?.value?.trim() || '',
                            recursive: spRecursive?.checked ?? true,
                            max_files: 500,
                        })
                    });
                    const json = await resp.json();

                    if (spConnectionStatus) spConnectionStatus.classList.remove('hidden');

                    if (json.success && json.data) {
                        const d = json.data;

                        // Auto-fill the library path fields (hidden + visible advanced)
                        if (d.library_path && spLibraryPath) {
                            spLibraryPath.value = d.library_path;
                            const spLibVis = document.getElementById('sp-library-path-visible');
                            if (spLibVis) spLibVis.value = d.library_path;
                        }

                        // Show connection success
                        if (spConnectionStatus) {
                            spConnectionStatus.style.background = 'rgba(34,197,94,0.1)';
                            spConnectionStatus.style.border = '1px solid rgba(34,197,94,0.3)';
                            spConnectionStatus.style.color = 'var(--success, #22c55e)';
                            let connMsg = `<strong>✓ Connected</strong> — ${escapeHtml(d.site_title || 'SharePoint site')} (${d.auth_method || 'SSO'})`;
                            if (d.ssl_fallback) connMsg += ' <span style="opacity:0.7;font-size:11px">[SSL bypass]</span>';
                            spConnectionStatus.innerHTML = connMsg;
                        }

                        const disc = d.discovery;
                        if (disc && disc.supported_files > 0) {
                            // Show file preview
                            let html = `<div class="folder-scan-stats">`;
                            html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${disc.supported_files}</div><div class="folder-scan-stat-label">Documents</div></div>`;
                            html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${disc.total_size_human || '—'}</div><div class="folder-scan-stat-label">Total Size</div></div>`;
                            const types = disc.file_type_breakdown || {};
                            Object.entries(types).forEach(([ext, count]) => {
                                html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${count}</div><div class="folder-scan-stat-label">${ext}</div></div>`;
                            });
                            html += `</div>`;
                            if (spFilePreview) {
                                spFilePreview.innerHTML = html;
                                spFilePreview.classList.remove('hidden');
                            }

                            window.showToast?.(`Found ${disc.supported_files} documents — scan started!`, 'success');

                            // If scan_id exists, the scan is already running — go straight to dashboard
                            if (d.scan_id) {
                                // Store scan info
                                if (btnSpScan) {
                                    btnSpScan.dataset.scanId = d.scan_id;
                                    btnSpScan.dataset.totalFiles = disc.supported_files || 0;
                                    btnSpScan.dataset.discoveryFiles = JSON.stringify(disc.files || []);
                                }

                                // Auto-trigger scan dashboard display
                                setTimeout(() => {
                                    if (btnSpScan) {
                                        btnSpScan.style.display = '';
                                        btnSpScan.disabled = false;
                                        btnSpScan.click(); // Triggers the scan polling handler
                                    }
                                }, 300);
                            }
                        } else {
                            // Connected but no files
                            window.showToast?.(d.message || 'No supported documents found', 'info');
                            if (spFilePreview) {
                                spFilePreview.innerHTML = `<p style="color:var(--text-muted);font-size:12px;">${escapeHtml(d.message || 'No documents found')}</p>`;
                                spFilePreview.classList.remove('hidden');
                            }
                        }
                    } else {
                        // Connection failed
                        const errMsg = json.data?.message || json.error?.message || 'Connection failed';
                        if (spConnectionStatus) {
                            spConnectionStatus.style.background = 'rgba(239,68,68,0.1)';
                            spConnectionStatus.style.border = '1px solid rgba(239,68,68,0.3)';
                            spConnectionStatus.style.color = 'var(--danger, #ef4444)';
                            spConnectionStatus.innerHTML = `<strong>✗ Failed</strong> — ${escapeHtml(errMsg)}`;
                        }
                        window.showToast?.(errMsg, 'error');
                    }
                } catch (err) {
                    console.error('[TWR SP] Connect & Scan error:', err);
                    window.showToast?.('SharePoint connection failed: ' + err.message, 'error');
                    if (spConnectionStatus) {
                        spConnectionStatus.classList.remove('hidden');
                        spConnectionStatus.style.background = 'rgba(239,68,68,0.1)';
                        spConnectionStatus.style.border = '1px solid rgba(239,68,68,0.3)';
                        spConnectionStatus.style.color = 'var(--danger, #ef4444)';
                        spConnectionStatus.innerHTML = `<strong>✗ Error</strong> — ${escapeHtml(err.message)}`;
                    }
                } finally {
                    btnSpConnectScan.disabled = false;
                    btnSpConnectScan.innerHTML = '<i data-lucide="cloud"></i> Connect &amp; Scan';
                    if (btnSpTest) btnSpTest.disabled = false;
                    if (btnSpDiscover) btnSpDiscover.disabled = false;
                    lucide?.createIcons?.();
                }
            });
        }

        // Preview (Discover) button
        if (btnSpDiscover) {
            btnSpDiscover.addEventListener('click', async () => {
                const siteUrl = spSiteUrl?.value?.trim();
                const libPath = spLibraryPath?.value?.trim();
                if (!siteUrl) {
                    window.showToast?.('Please enter a SharePoint site URL', 'warning');
                    return;
                }
                if (!libPath) {
                    window.showToast?.('Please enter a document library path', 'warning');
                    return;
                }
                btnSpDiscover.disabled = true;
                btnSpDiscover.innerHTML = '<i data-lucide="loader" class="spin"></i> Scanning...';
                try {
                    const csrf = await _freshCSRF();
                    const resp = await fetch('/api/review/sharepoint-scan-start', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': csrf
                        },
                        body: JSON.stringify({
                            site_url: siteUrl,
                            library_path: libPath,
                            recursive: spRecursive?.checked ?? true,
                            max_files: 500,
                            // Discovery-only: we just want the file list, not a full scan
                            // But the API starts the scan — we'll cancel polling after showing preview
                        })
                    });
                    const json = await resp.json();
                    if (json.success && json.data?.discovery) {
                        const d = json.data.discovery;
                        let html = `<div class="folder-scan-stats">`;
                        html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${d.supported_files || d.total_discovered}</div><div class="folder-scan-stat-label">Documents</div></div>`;
                        html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${d.total_size_human || '—'}</div><div class="folder-scan-stat-label">Total Size</div></div>`;
                        const types = d.file_type_breakdown || {};
                        Object.entries(types).forEach(([ext, count]) => {
                            html += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${count}</div><div class="folder-scan-stat-label">${ext}</div></div>`;
                        });
                        html += `</div>`;
                        if (d.files && d.files.length > 0) {
                            html += `<div class="folder-scan-file-list">`;
                            d.files.forEach(f => {
                                html += `<div class="folder-scan-file-item">
                                    <span class="folder-scan-file-path" title="${f.relative_path || f.server_relative_url}">${escapeHtml(f.filename || f.name)}</span>
                                    <span class="folder-scan-file-size">${f.size_human || ''}</span>
                                </div>`;
                            });
                            html += `</div>`;
                        }
                        if (spFilePreview) {
                            spFilePreview.innerHTML = html;
                            spFilePreview.classList.remove('hidden');
                        }
                        // Enable Scan All since we now have a running scan
                        if (btnSpScan) btnSpScan.disabled = false;
                        // Store scan_id for the scan handler
                        if (btnSpScan) btnSpScan.dataset.scanId = json.data.scan_id || '';
                        if (btnSpScan) btnSpScan.dataset.totalFiles = d.supported_files || d.total_discovered || 0;

                        // If scan_id is set, the scan is ALREADY running from this call
                        // Store discovery files for dashboard initialization
                        if (btnSpScan) btnSpScan.dataset.discoveryFiles = JSON.stringify(d.files || []);

                        window.showToast?.(`Found ${d.supported_files || d.total_discovered} documents`, 'success');

                        if (json.data.scan_id) {
                            window.showToast?.('Scan has started — click "Scan All" to see live progress', 'info');
                        }
                    } else if (json.data?.message) {
                        window.showToast?.(json.data.message, 'info');
                        if (spFilePreview) {
                            spFilePreview.innerHTML = `<p style="color:var(--text-muted);font-size:12px;">${escapeHtml(json.data.message)}</p>`;
                            spFilePreview.classList.remove('hidden');
                        }
                    } else {
                        window.showToast?.(json.error?.message || 'Discovery failed', 'error');
                    }
                } catch (err) {
                    console.error('[TWR SP] Discover error:', err);
                    window.showToast?.('SharePoint discovery failed: ' + err.message, 'error');
                } finally {
                    btnSpDiscover.disabled = false;
                    btnSpDiscover.innerHTML = '<i data-lucide="search"></i> Preview';
                    lucide?.createIcons?.();
                }
            });
        }

        // Scan All button — starts polling the already-running scan
        if (btnSpScan) {
            btnSpScan.addEventListener('click', async () => {
                const scanId = btnSpScan.dataset.scanId;
                const totalFiles = parseInt(btnSpScan.dataset.totalFiles || '0', 10);

                if (!scanId) {
                    window.showToast?.('Please click Preview first to discover files', 'warning');
                    return;
                }

                btnSpScan.disabled = true;
                btnSpDiscover.disabled = true;
                btnSpTest.disabled = true;
                btnSpScan.innerHTML = '<i data-lucide="loader" class="spin"></i> Scanning...';
                if (spFilePreview) spFilePreview.classList.add('hidden');

                // Show progress dashboard
                const dashEl = document.getElementById('sp-scan-dashboard');
                const spDocsComplete = document.getElementById('sp-docs-complete');
                const spDocsTotal = document.getElementById('sp-docs-total');
                const spPercent = document.getElementById('sp-percent');
                const spFill = document.getElementById('sp-progress-fill');
                const spGlow = document.getElementById('sp-progress-glow');
                const spElapsed = document.getElementById('sp-elapsed-time');
                const spRemaining = document.getElementById('sp-remaining-time');
                const spSpeedEl = document.getElementById('sp-speed');
                const spQueueStatus = document.getElementById('sp-queue-status');
                const spDocList = document.getElementById('sp-doc-list');
                const spIssueCount = document.getElementById('sp-issues-found');

                if (dashEl) {
                    dashEl.classList.remove('hidden');
                    dashEl.classList.add('scanning');
                }
                if (spDocsTotal) spDocsTotal.textContent = totalFiles;
                if (spDocsComplete) spDocsComplete.textContent = '0';
                if (spPercent) spPercent.textContent = '0%';
                if (spIssueCount) spIssueCount.textContent = '0';

                // v5.9.39: Show minimize button when SharePoint scan starts
                const minBtnSP = document.getElementById('btn-minimize-batch-modal');
                if (minBtnSP) minBtnSP.style.display = '';

                // Build initial doc rows from stored discovery
                let discoveryFiles = [];
                try {
                    discoveryFiles = JSON.parse(btnSpScan.dataset.discoveryFiles || '[]');
                } catch (e) { /* ignore */ }

                const spFileIndexMap = {};
                if (spDocList && discoveryFiles.length > 0) {
                    spDocList.innerHTML = discoveryFiles.map((f, i) => {
                        spFileIndexMap[f.filename || f.name] = i;
                        return `
                            <div class="bpd-doc-row queued" id="sp-doc-${i}">
                                <div class="bpd-doc-icon"><div class="bpd-pending-dot"></div></div>
                                <div class="bpd-doc-content">
                                    <div class="bpd-doc-name">${escapeHtml(f.filename || f.name)}</div>
                                    <div class="bpd-doc-detail" id="sp-doc-meta-${i}">Queued — ${escapeHtml(f.relative_path || f.server_relative_url || '')}</div>
                                </div>
                                <div class="bpd-doc-bar" id="sp-doc-progress-${i}">
                                    <div class="bpd-doc-bar-fill" id="sp-doc-fill-${i}" style="width:0%"></div>
                                </div>
                                <div class="bpd-doc-duration" id="sp-doc-duration-${i}"></div>
                            </div>`;
                    }).join('');
                }
                if (window.lucide) window.lucide.createIcons();

                // Polling — reuses exact same folder-scan-progress endpoint
                let spLastDocCount = 0;
                let spPollInterval = null;

                const _formatSPTime = (seconds) => {
                    if (!seconds || seconds < 0) return '--:--';
                    const m = Math.floor(seconds / 60);
                    const s = Math.floor(seconds % 60);
                    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                };

                const _updateSPDocRow = (idx, status, detail) => {
                    const row = document.getElementById(`sp-doc-${idx}`);
                    const metaEl = document.getElementById(`sp-doc-meta-${idx}`);
                    const fillEl = document.getElementById(`sp-doc-fill-${idx}`);
                    if (row) {
                        row.className = `bpd-doc-row ${status}`;
                        const iconDiv = row.querySelector('.bpd-doc-icon');
                        if (iconDiv) {
                            if (status === 'processing') {
                                iconDiv.innerHTML = '<div class="bpd-spinner"></div>';
                                row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            } else if (status === 'complete') {
                                iconDiv.innerHTML = '<div class="bpd-check"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg></div>';
                            } else if (status === 'error') {
                                iconDiv.innerHTML = '<div class="bpd-error-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></div>';
                            }
                        }
                    }
                    if (metaEl) metaEl.textContent = detail;
                    if (fillEl) fillEl.style.width = (status === 'complete' || status === 'error') ? '100%' : '50%';
                };

                const pollSPProgress = async () => {
                    try {
                        const resp = await fetch(`/api/review/folder-scan-progress/${scanId}?since=${spLastDocCount}`);
                        const json = await resp.json();
                        if (!json.success) return;

                        const data = json.data;
                        const done = data.processed + data.errors;
                        const pct = totalFiles > 0 ? Math.round((done / totalFiles) * 100) : 0;

                        if (spDocsComplete) spDocsComplete.textContent = done;
                        if (spPercent) spPercent.textContent = pct + '%';
                        if (spFill) spFill.style.width = pct + '%';
                        if (spGlow) spGlow.style.width = pct + '%';
                        if (spElapsed) spElapsed.textContent = _formatSPTime(data.elapsed_seconds);
                        if (spRemaining) spRemaining.textContent = _formatSPTime(data.estimated_remaining);
                        if (spIssueCount) spIssueCount.textContent = data.summary?.total_issues || 0;

                        if (spSpeedEl && data.elapsed_seconds > 0 && done > 0) {
                            const docsPerMin = (done / data.elapsed_seconds * 60).toFixed(1);
                            spSpeedEl.textContent = docsPerMin + '/min';
                        }

                        if (spQueueStatus) {
                            if (data.phase === 'complete') {
                                spQueueStatus.textContent = 'Complete';
                            } else if (data.current_file) {
                                spQueueStatus.textContent = `Chunk ${data.current_chunk}/${data.total_chunks} — ${data.current_file}`;
                            } else {
                                spQueueStatus.textContent = `Processing chunk ${data.current_chunk}/${data.total_chunks}...`;
                            }
                        }

                        // Mark currently processing file
                        if (data.current_file && data.phase === 'reviewing') {
                            // current_file may contain multiple filenames separated by comma
                            const names = data.current_file.split(', ');
                            names.forEach(name => {
                                const idx = spFileIndexMap[name.trim()];
                                if (idx !== undefined) {
                                    const row = document.getElementById(`sp-doc-${idx}`);
                                    if (row && !row.classList.contains('complete') && !row.classList.contains('error')) {
                                        _updateSPDocRow(idx, 'processing', `Downloading & analyzing...`);
                                    }
                                }
                            });
                        }

                        // Update newly completed documents
                        if (data.documents && data.documents.length > 0) {
                            data.documents.forEach(doc => {
                                const idx = spFileIndexMap[doc.filename];
                                if (idx === undefined) return;
                                if (doc.status === 'error') {
                                    _updateSPDocRow(idx, 'error', `Error: ${doc.error || 'Unknown'}`);
                                } else {
                                    _updateSPDocRow(idx, 'complete',
                                        `${(doc.word_count || 0).toLocaleString()} words • ${doc.issue_count} issues • ${doc.role_count || 0} roles • Score: ${doc.score}%`);
                                }
                            });
                            spLastDocCount = data.total_documents_ready;
                        }

                        // Check if done
                        if (data.phase === 'complete' || data.phase === 'error') {
                            clearInterval(spPollInterval);
                            spPollInterval = null;

                            if (dashEl) {
                                dashEl.classList.remove('scanning');
                                dashEl.classList.add('bpd-complete');
                            }

                            // Build final summary
                            const summary = data.summary || {};
                            const grades = summary.grade_distribution || {};
                            let summaryHtml = `<div class="folder-scan-stats" style="margin-top:12px;">`;
                            summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${totalFiles}</div><div class="folder-scan-stat-label">Discovered</div></div>`;
                            summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.processed || 0}</div><div class="folder-scan-stat-label">Scanned</div></div>`;
                            summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.errors || 0}</div><div class="folder-scan-stat-label">Errors</div></div>`;
                            summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${summary.total_issues || 0}</div><div class="folder-scan-stat-label">Issues</div></div>`;
                            summaryHtml += `<div class="folder-scan-stat"><div class="folder-scan-stat-value">${_formatSPTime(data.elapsed_seconds)}</div><div class="folder-scan-stat-label">Time</div></div>`;
                            summaryHtml += `</div>`;

                            if (Object.keys(grades).length > 0) {
                                summaryHtml += `<div style="margin-top:8px;"><strong style="font-size:12px;color:var(--text-muted);">Grade Distribution:</strong> `;
                                Object.entries(grades).sort().forEach(([grade, count]) => {
                                    summaryHtml += `<span style="margin-right:12px;font-size:13px;">${grade}: <strong>${count}</strong></span>`;
                                });
                                summaryHtml += `</div>`;
                            }

                            if (spFilePreview) {
                                spFilePreview.innerHTML = summaryHtml;
                                spFilePreview.classList.remove('hidden');
                            }

                            const msg = data.phase === 'error'
                                ? `SharePoint scan failed: ${data.error_message || 'Unknown error'}`
                                : `SharePoint scan complete: ${done} documents, ${summary.total_issues || 0} issues in ${_formatSPTime(data.elapsed_seconds)}`;
                            window.showToast?.(msg, data.phase === 'error' ? 'error' : 'success');

                            btnSpScan.disabled = false;
                            btnSpDiscover.disabled = false;
                            btnSpTest.disabled = false;
                            btnSpScan.innerHTML = '<i data-lucide="scan-line"></i> Scan All';
                            if (window.lucide) window.lucide.createIcons();
                        }
                    } catch (pollErr) {
                        console.error('[TWR SP] Poll error:', pollErr);
                    }
                };

                // Start polling every 2 seconds (slightly slower than folder scan — remote downloads are slower)
                spPollInterval = setInterval(pollSPProgress, 2000);
                pollSPProgress();
            });
        }

        // Start batch processing
        document.getElementById('btn-start-batch')?.addEventListener('click', startBatchProcessing);
        
        // Back from results
        document.getElementById('btn-back-from-batch')?.addEventListener('click', () => {
            document.getElementById('batch-results').style.display = 'none';
            document.getElementById('empty-state').style.display = 'flex';
        });
        
        // Modal overlay click to close
        document.querySelector('#batch-upload-modal .modal-overlay')?.addEventListener('click', closeBatchModal);
    }
    
    function openBatchModal() {
        BatchState.files = [];
        document.getElementById('batch-file-list').innerHTML = '';
        document.getElementById('btn-start-batch').disabled = true;
        // v5.0.2: Reset batch progress dashboard
        const progressEl = document.getElementById('batch-progress');
        progressEl.classList.add('hidden');
        progressEl.classList.remove('bpd-complete');
        const progressFill = document.getElementById('batch-progress-fill');
        if (progressFill) progressFill.style.width = '0%';
        const glowEl = document.getElementById('batch-progress-glow');
        if (glowEl) glowEl.style.width = '0%';
        const docList = document.getElementById('batch-doc-list');
        if (docList) docList.innerHTML = '';
        // v5.9.35: Reset issues and roles counters
        const issuesEl = document.getElementById('batch-issues-count');
        const rolesEl = document.getElementById('batch-roles-count');
        if (issuesEl) issuesEl.textContent = '0';
        if (rolesEl) rolesEl.textContent = '0';
        document.getElementById('batch-upload-modal').style.display = 'flex';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    function closeBatchModal() {
        // v5.9.38: If any scan is running, minimize to floating badge instead of closing
        const batchRunning = BatchState.processing;
        const fsDash = document.getElementById('folder-scan-dashboard');
        const spDash = document.getElementById('sp-scan-dashboard');
        const batchDash = document.getElementById('batch-progress');
        const folderScanRunning = fsDash && !fsDash.classList.contains('hidden') && !fsDash.classList.contains('bpd-complete');
        const spScanRunning = spDash && !spDash.classList.contains('hidden') && !spDash.classList.contains('bpd-complete');
        const batchDashRunning = batchDash && !batchDash.classList.contains('hidden') && !batchDash.classList.contains('bpd-complete');

        if (batchRunning || folderScanRunning || spScanRunning || batchDashRunning) {
            minimizeBatchModal();
            return;
        }
        document.getElementById('batch-upload-modal').style.display = 'none';
        BatchState.files = [];
        // Hide minimize button when closing normally (scan complete)
        const minBtn = document.getElementById('btn-minimize-batch-modal');
        if (minBtn) minBtn.style.display = 'none';
    }

    // v5.9.38: Minimize/Restore pattern (same as HV cinematic progress)
    let _batchMiniBadgeInterval = null;

    function minimizeBatchModal() {
        const modal = document.getElementById('batch-upload-modal');
        if (modal) modal.style.display = 'none';

        // Determine which scan type is active for the label
        let scanLabel = 'Batch Scan';
        let scanIcon = 'layers';
        const fsDash = document.getElementById('folder-scan-dashboard');
        const spDash = document.getElementById('sp-scan-dashboard');
        if (spDash && !spDash.classList.contains('hidden')) {
            scanLabel = 'SharePoint Scan';
            scanIcon = 'cloud';
        } else if (fsDash && !fsDash.classList.contains('hidden')) {
            scanLabel = 'Folder Scan';
            scanIcon = 'folder-open';
        }

        // Create floating mini badge if it doesn't exist
        let badge = document.getElementById('batch-mini-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.className = 'batch-mini-badge';
            badge.id = 'batch-mini-badge';
            badge.innerHTML = `
                <div class="batch-mini-ring">
                    <svg viewBox="0 0 36 36">
                        <circle class="batch-mini-ring-bg" cx="18" cy="18" r="15.9"/>
                        <circle class="batch-mini-ring-fill" cx="18" cy="18" r="15.9" id="batch-mini-ring-fill"/>
                    </svg>
                </div>
                <div class="batch-mini-info">
                    <span class="batch-mini-pct" id="batch-mini-pct">0%</span>
                    <span class="batch-mini-text" id="batch-mini-text">${scanLabel}</span>
                </div>
            `;
            badge.addEventListener('click', restoreBatchModal);
            badge.title = 'Click to restore scan progress';
            document.body.appendChild(badge);
            requestAnimationFrame(() => badge.classList.add('batch-mini-badge-visible'));
        } else {
            // Update label if it changed
            const textEl = badge.querySelector('#batch-mini-text');
            if (textEl) textEl.textContent = scanLabel;
        }

        // Start mini badge update loop
        _startBatchMiniBadgeLoop();
    }

    function restoreBatchModal() {
        const modal = document.getElementById('batch-upload-modal');
        if (modal) modal.style.display = 'flex';

        // Remove the mini badge
        const badge = document.getElementById('batch-mini-badge');
        if (badge) {
            badge.classList.remove('batch-mini-badge-visible');
            setTimeout(() => badge.remove(), 300);
        }

        if (_batchMiniBadgeInterval) {
            clearInterval(_batchMiniBadgeInterval);
            _batchMiniBadgeInterval = null;
        }
    }

    function _isBatchScanStillRunning() {
        // Check all 3 scan types: batch upload, folder scan, SharePoint scan
        if (BatchState.processing) return true;
        const fsDash = document.getElementById('folder-scan-dashboard');
        if (fsDash && !fsDash.classList.contains('hidden') && !fsDash.classList.contains('bpd-complete')) return true;
        const spDash = document.getElementById('sp-scan-dashboard');
        if (spDash && !spDash.classList.contains('hidden') && !spDash.classList.contains('bpd-complete')) return true;
        const batchDash = document.getElementById('batch-progress');
        if (batchDash && !batchDash.classList.contains('hidden') && !batchDash.classList.contains('bpd-complete')) return true;
        return false;
    }

    function _startBatchMiniBadgeLoop() {
        if (_batchMiniBadgeInterval) clearInterval(_batchMiniBadgeInterval);
        _batchMiniBadgeInterval = setInterval(() => {
            if (!_isBatchScanStillRunning()) {
                // Scan finished — show completion briefly then remove badge
                _updateBatchMiniBadge();
                setTimeout(() => {
                    const badge = document.getElementById('batch-mini-badge');
                    if (badge) {
                        badge.classList.remove('batch-mini-badge-visible');
                        setTimeout(() => badge.remove(), 300);
                    }
                    // Hide minimize button since scan is done
                    const minBtn = document.getElementById('btn-minimize-batch-modal');
                    if (minBtn) minBtn.style.display = 'none';
                }, 3000);
                clearInterval(_batchMiniBadgeInterval);
                _batchMiniBadgeInterval = null;
                return;
            }
            _updateBatchMiniBadge();
        }, 1000);
    }

    function _updateBatchMiniBadge() {
        const pctEl = document.getElementById('batch-mini-pct');
        const ringFill = document.getElementById('batch-mini-ring-fill');
        if (!pctEl || !ringFill) return;

        // Try to get percentage from the various dashboard elements
        let pct = 0;
        // Check batch progress first, then folder scan, then SharePoint
        const batchPct = document.getElementById('batch-percent-animated');
        const fsPct = document.getElementById('fs-percent');
        const spPct = document.getElementById('sp-percent');

        if (batchPct && batchPct.textContent) {
            pct = parseInt(batchPct.textContent) || 0;
        } else if (fsPct && fsPct.textContent) {
            pct = parseInt(fsPct.textContent) || 0;
        } else if (spPct && spPct.textContent) {
            pct = parseInt(spPct.textContent) || 0;
        }

        pctEl.textContent = `${pct}%`;

        // Update SVG ring
        const circumference = 2 * Math.PI * 15.9;
        ringFill.style.strokeDasharray = `${circumference}`;
        ringFill.style.strokeDashoffset = `${circumference - (pct / 100) * circumference}`;

        // Change color on completion
        if (pct >= 100) {
            ringFill.style.stroke = '#22c55e';
            pctEl.textContent = 'Done';
            const textEl = document.getElementById('batch-mini-text');
            if (textEl) textEl.textContent = 'Scan Complete';
        }
    }

    // v5.9.38: Also clean up badge when batch processing finishes
    // This is called from the scan completion paths
    function _removeBatchMiniBadge() {
        const badge = document.getElementById('batch-mini-badge');
        if (badge) {
            badge.classList.remove('batch-mini-badge-visible');
            setTimeout(() => badge.remove(), 300);
        }
        if (_batchMiniBadgeInterval) {
            clearInterval(_batchMiniBadgeInterval);
            _batchMiniBadgeInterval = null;
        }
    }

    /**
     * Recursively get all files from a DataTransfer (supports folder drops)
     * @param {DataTransferItemList} items - The items from dataTransfer
     * @returns {Promise<File[]>} - Array of files
     */
    async function getFilesFromDataTransfer(items) {
        const files = [];
        const validExtensions = ['.docx', '.pdf', '.doc'];

        async function processEntry(entry) {
            if (entry.isFile) {
                return new Promise((resolve) => {
                    entry.file((file) => {
                        const ext = '.' + file.name.split('.').pop().toLowerCase();
                        if (validExtensions.includes(ext)) {
                            files.push(file);
                        }
                        resolve();
                    });
                });
            } else if (entry.isDirectory) {
                const reader = entry.createReader();
                return new Promise((resolve) => {
                    const readEntries = () => {
                        reader.readEntries(async (entries) => {
                            if (entries.length === 0) {
                                resolve();
                            } else {
                                for (const e of entries) {
                                    await processEntry(e);
                                }
                                readEntries(); // Continue reading (directories may have >100 entries)
                            }
                        });
                    };
                    readEntries();
                });
            }
        }

        const entries = [];
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.webkitGetAsEntry) {
                const entry = item.webkitGetAsEntry();
                if (entry) entries.push(entry);
            } else if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) {
                    const ext = '.' + file.name.split('.').pop().toLowerCase();
                    if (validExtensions.includes(ext)) {
                        files.push(file);
                    }
                }
            }
        }

        for (const entry of entries) {
            await processEntry(entry);
        }

        return files;
    }

    function handleBatchFiles(fileList) {
        const validExtensions = ['.docx', '.pdf', '.doc'];

        Array.from(fileList).forEach(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            if (validExtensions.includes(ext)) {
                // Use webkitRelativePath if available (from folder selection), otherwise just the name
                const displayPath = file.webkitRelativePath || file.name;
                // Avoid duplicates by checking both name and path
                const isDuplicate = BatchState.files.some(f => {
                    const existingPath = f.webkitRelativePath || f.name;
                    return existingPath === displayPath || f.name === file.name;
                });
                if (!isDuplicate) {
                    BatchState.files.push(file);
                }
            }
        });

        renderBatchFileList();
    }

    function renderBatchFileList() {
        const container = document.getElementById('batch-file-list');
        if (!container) return;

        if (BatchState.files.length === 0) {
            container.innerHTML = '<p class="text-muted">No files selected</p>';
            document.getElementById('btn-start-batch').disabled = true;
            return;
        }

        container.innerHTML = BatchState.files.map((file, idx) => {
            // Show relative path if from folder, otherwise just filename
            const displayPath = file.webkitRelativePath || file.name;
            const displayName = displayPath.includes('/') ? displayPath : file.name;
            return `
                <div class="batch-file-item">
                    <span class="batch-file-icon"><i data-lucide="${file.name.endsWith('.pdf') ? 'file-text' : 'file'}"></i></span>
                    <span class="batch-file-name" title="${escapeHtml(displayPath)}">${escapeHtml(displayName)}</span>
                    <span class="batch-file-size">${formatFileSize(file.size)}</span>
                    <button class="btn btn-ghost btn-xs" onclick="window.removeBatchFile(${idx})">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            `;
        }).join('');

        document.getElementById('btn-start-batch').disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    window.removeBatchFile = function(idx) {
        BatchState.files.splice(idx, 1);
        renderBatchFileList();
    };
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    
    // Batch processing constants (should match server-side limits)
    // v5.5.0: Increased from 10/100MB to support large document repositories
    const BATCH_LIMITS = {
        MAX_FILES_PER_BATCH: 50,
        MAX_BYTES_PER_BATCH: 500 * 1024 * 1024, // 500MB
        MAX_CONCURRENT_BATCHES: 3
    };

    /**
     * Split files into chunks that respect server limits
     * @param {File[]} files - Array of files to chunk
     * @returns {File[][]} - Array of file chunks
     */
    function chunkFilesIntoBatches(files) {
        const chunks = [];
        let currentChunk = [];
        let currentSize = 0;

        for (const file of files) {
            // Check if adding this file would exceed limits
            const wouldExceedCount = currentChunk.length >= BATCH_LIMITS.MAX_FILES_PER_BATCH;
            const wouldExceedSize = currentSize + file.size > BATCH_LIMITS.MAX_BYTES_PER_BATCH;

            if (wouldExceedCount || wouldExceedSize) {
                // Start a new chunk if current one has files
                if (currentChunk.length > 0) {
                    chunks.push(currentChunk);
                    currentChunk = [];
                    currentSize = 0;
                }
            }

            currentChunk.push(file);
            currentSize += file.size;
        }

        // Don't forget the last chunk
        if (currentChunk.length > 0) {
            chunks.push(currentChunk);
        }

        return chunks;
    }

    async function startBatchProcessing() {
        if (BatchState.files.length === 0 || BatchState.processing) return;

        BatchState.processing = true;
        const progressEl = document.getElementById('batch-progress');
        const progressFill = document.getElementById('batch-progress-fill');
        const progressText = document.getElementById('batch-progress-text');
        const progressPercent = document.getElementById('batch-progress-percent');
        const percentAnimated = document.getElementById('batch-percent-animated');
        const docsComplete = document.getElementById('batch-docs-complete');
        const docsTotal = document.getElementById('batch-docs-total');
        const queueStatus = document.getElementById('batch-queue-status');
        const docList = document.getElementById('batch-doc-list');
        const startBtn = document.getElementById('btn-start-batch');
        const elapsedTimeEl = document.getElementById('batch-elapsed-time');
        const remainingTimeEl = document.getElementById('batch-remaining-time');
        const speedEl = document.getElementById('batch-speed');
        const soundToggle = document.getElementById('cinematic-sound-toggle');
        const issuesCountEl = document.getElementById('batch-issues-count');
        const rolesCountEl = document.getElementById('batch-roles-count');

        // Running totals for issues and roles
        let runningIssues = 0;
        let runningRoles = 0;

        // Time tracking
        const startTime = Date.now();
        let elapsedInterval = null;
        let currentPercent = 0;
        let targetPercent = 0;
        let soundEnabled = localStorage.getItem('batchSoundEnabled') !== 'false';

        // v5.0.2: Batch progress dashboard initialized (no external animation dependencies)

        // Update sound toggle button state
        if (soundToggle) {
            const icon = soundToggle.querySelector('i');
            if (!soundEnabled) {
                soundToggle.classList.add('muted');
                if (icon) icon.setAttribute('data-lucide', 'volume-x');
            }
            soundToggle.onclick = () => {
                soundEnabled = !soundEnabled;
                localStorage.setItem('batchSoundEnabled', soundEnabled);
                soundToggle.classList.toggle('muted', !soundEnabled);
                const ico = soundToggle.querySelector('i');
                if (ico) {
                    ico.setAttribute('data-lucide', soundEnabled ? 'volume-2' : 'volume-x');
                    if (window.lucide) window.lucide.createIcons();
                }
            };
        }

        // Format time as MM:SS
        const formatTime = (ms) => {
            const totalSeconds = Math.floor(ms / 1000);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        };

        // Update elapsed time every second
        elapsedInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            if (elapsedTimeEl) elapsedTimeEl.textContent = formatTime(elapsed);
        }, 1000);

        // Animated percentage counter
        let percentAnimation = null;
        const animatePercent = (target) => {
            targetPercent = target;
            if (percentAnimation) return; // Already animating

            const animate = () => {
                if (currentPercent < targetPercent) {
                    currentPercent = Math.min(currentPercent + 1, targetPercent);
                    if (percentAnimated) {
                        percentAnimated.textContent = currentPercent + '%';
                        percentAnimated.classList.add('counting');
                        setTimeout(() => percentAnimated.classList.remove('counting'), 100);
                    }
                    percentAnimation = requestAnimationFrame(animate);
                } else {
                    percentAnimation = null;
                }
            };
            percentAnimation = requestAnimationFrame(animate);
        };

        // Play completion sound
        const playCompletionSound = () => {
            if (!soundEnabled) return;
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
                oscillator.frequency.setValueAtTime(1108.73, audioCtx.currentTime + 0.1); // C#6
                oscillator.frequency.setValueAtTime(1318.51, audioCtx.currentTime + 0.2); // E6
                gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
                oscillator.start(audioCtx.currentTime);
                oscillator.stop(audioCtx.currentTime + 0.4);
            } catch (e) {
                console.log('[TWR] Could not play sound:', e);
            }
        };

        // v5.0.2: Update main progress (ScanProgress-style dashboard)
        const updateProgress = (percent, text) => {
            if (progressFill) progressFill.style.width = percent + '%';
            const glowEl = document.getElementById('batch-progress-glow');
            if (glowEl) glowEl.style.width = percent + '%';
            if (text && progressText) progressText.textContent = text;
            animatePercent(Math.round(percent));

            // Update estimated time remaining
            if (percent > 0 && percent < 100) {
                const elapsed = Date.now() - startTime;
                const estimatedTotal = (elapsed / percent) * 100;
                const remaining = estimatedTotal - elapsed;
                if (remainingTimeEl) remainingTimeEl.textContent = formatTime(remaining);

                // Calculate speed (docs per minute)
                const docsProcessed = parseInt(docsComplete?.textContent || '0');
                const elapsedMinutes = elapsed / 60000;
                if (elapsedMinutes > 0 && speedEl) {
                    const speed = (docsProcessed / elapsedMinutes).toFixed(1);
                    speedEl.textContent = speed + ' docs/min';
                }
            } else if (percent >= 100) {
                if (remainingTimeEl) remainingTimeEl.textContent = '00:00';
                // Mark dashboard complete
                const dashEl = document.getElementById('batch-progress');
                if (dashEl) dashEl.classList.add('bpd-complete');
            }
        };

        // v5.0.2: Document row HTML matching ScanProgress step style
        const docStartTimes = {};
        const createDocRow = (file, index, status = 'queued', batchNum = null) => {
            const batchLabel = batchNum !== null ? `<span class="bpd-batch-label">Batch ${batchNum + 1}</span>` : '';
            const iconHTML = status === 'queued'
                ? '<div class="bpd-pending-dot"></div>'
                : '<div class="bpd-spinner"></div>';
            return `
                <div class="bpd-doc-row ${status}" id="batch-doc-${index}">
                    <div class="bpd-doc-icon">${iconHTML}</div>
                    <div class="bpd-doc-content">
                        <div class="bpd-doc-name">${escapeHtml(file.name)} ${batchLabel}</div>
                        <div class="bpd-doc-detail" id="batch-doc-meta-${index}">Queued for analysis</div>
                    </div>
                    <div class="bpd-doc-bar" id="batch-doc-progress-${index}">
                        <div class="bpd-doc-bar-fill" id="batch-doc-fill-${index}" style="width: 0%;"></div>
                    </div>
                    <div class="bpd-doc-duration" id="batch-doc-duration-${index}"></div>
                </div>
            `;
        };

        // v5.0.2: Update doc row to match ScanProgress style
        const updateDocRow = (index, status, meta, issues = null, progress = 0) => {
            const row = document.getElementById(`batch-doc-${index}`);
            const metaEl = document.getElementById(`batch-doc-meta-${index}`);
            const fillEl = document.getElementById(`batch-doc-fill-${index}`);
            const durationEl = document.getElementById(`batch-doc-duration-${index}`);

            if (row) {
                row.className = `bpd-doc-row ${status}`;
                const iconDiv = row.querySelector('.bpd-doc-icon');
                if (iconDiv) {
                    if (status === 'processing' || status === 'uploading') {
                        if (!docStartTimes[index]) docStartTimes[index] = Date.now();
                        iconDiv.innerHTML = '<div class="bpd-spinner"></div>';
                    } else if (status === 'complete') {
                        iconDiv.innerHTML = '<div class="bpd-check"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg></div>';
                        // Show duration
                        if (durationEl && docStartTimes[index]) {
                            const dur = ((Date.now() - docStartTimes[index]) / 1000).toFixed(1);
                            durationEl.textContent = dur + 's';
                        }
                    } else if (status === 'error') {
                        iconDiv.innerHTML = '<div class="bpd-error-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></div>';
                    } else {
                        iconDiv.innerHTML = '<div class="bpd-pending-dot"></div>';
                    }
                }
                // Auto-scroll to processing row
                if (status === 'processing' || status === 'uploading') {
                    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
            if (metaEl) {
                if (status === 'complete' && issues !== null) {
                    // v5.9.35: Show word count, roles, issues, and score in completion line
                    metaEl.textContent = meta || `Complete — ${issues} issues found`;
                } else {
                    metaEl.textContent = meta;
                }
            }
            if (fillEl) {
                fillEl.style.width = progress + '%';
            }
        };

        // Split files into batches
        const batches = chunkFilesIntoBatches(BatchState.files);
        const totalFiles = BatchState.files.length;
        const numBatches = batches.length;

        // Build a mapping from global index to batch info
        const fileIndexMap = [];
        let globalIndex = 0;
        batches.forEach((batch, batchIdx) => {
            batch.forEach((file, localIdx) => {
                fileIndexMap.push({ batchIdx, localIdx, file });
                globalIndex++;
            });
        });

        // Initialize UI
        progressEl.classList.remove('hidden');
        progressEl.classList.add('scanning');
        startBtn.disabled = true;
        docsTotal.textContent = totalFiles;
        docsComplete.textContent = '0';

        // v5.9.39: Show minimize button when scan starts
        const minBtn = document.getElementById('btn-minimize-batch-modal');
        if (minBtn) minBtn.style.display = '';

        // Create document rows with batch labels if multiple batches
        globalIndex = 0;
        docList.innerHTML = batches.map((batch, batchIdx) => {
            return batch.map((file) => {
                const html = createDocRow(file, globalIndex, 'queued', numBatches > 1 ? batchIdx : null);
                globalIndex++;
                return html;
            }).join('');
        }).join('');
        if (window.lucide) window.lucide.createIcons();

        // Show batch info if splitting
        if (numBatches > 1) {
            updateProgress(0, `Splitting into ${numBatches} batches...`);
            queueStatus.textContent = `Processing ${numBatches} batches concurrently`;
        }

        // Track overall progress
        let completedDocs = 0;
        const allResults = { documents: [], summary: { total_documents: 0, total_issues: 0, issues_by_severity: {} }, roles_found: {} };

        /**
         * Process a single batch
         * @param {File[]} batchFiles - Files in this batch
         * @param {number} batchIdx - Batch index
         * @param {number} startGlobalIdx - Starting global index for this batch's files
         */
        async function processBatch(batchFiles, batchIdx, startGlobalIdx) {
            const batchLabel = numBatches > 1 ? ` (Batch ${batchIdx + 1})` : '';

            try {
                // Mark files as uploading
                batchFiles.forEach((_, localIdx) => {
                    updateDocRow(startGlobalIdx + localIdx, 'uploading', `Uploading...${batchLabel}`, null, 20);
                });

                // Upload batch
                const formData = new FormData();
                batchFiles.forEach(file => {
                    formData.append('files[]', file);
                });

                const uploadResponse = await fetch('/api/upload/batch', {
                    method: 'POST',
                    headers: { 'X-CSRF-Token': window.CSRF_TOKEN || '' },
                    body: formData
                });

                const uploadResult = await uploadResponse.json();
                if (!uploadResult.success) {
                    throw new Error(uploadResult.error?.message || uploadResult.error || 'Upload failed');
                }

                // Mark files as processing
                batchFiles.forEach((_, localIdx) => {
                    updateDocRow(startGlobalIdx + localIdx, 'processing', `Analyzing...${batchLabel}`, null, 50);
                });

                // Review batch
                const filepaths = uploadResult.data.processed.map(f => f.filepath);
                const reviewResponse = await fetch('/api/review/batch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.CSRF_TOKEN || ''
                    },
                    body: JSON.stringify({ filepaths })
                });

                const reviewResult = await reviewResponse.json();
                if (!reviewResult.success) {
                    throw new Error(reviewResult.error?.message || reviewResult.error || 'Review failed');
                }

                // Update UI for each document in this batch
                if (reviewResult.data && reviewResult.data.documents) {
                    reviewResult.data.documents.forEach((doc, localIdx) => {
                        completedDocs++;
                        const globalIdx = startGlobalIdx + localIdx;
                        const pct = Math.round((completedDocs / totalFiles) * 100);
                        updateProgress(pct, `Processed ${completedDocs} of ${totalFiles}...`);
                        docsComplete.textContent = completedDocs;

                        if (doc.error) {
                            updateDocRow(globalIdx, 'error', `Error: ${doc.error}`, null, 100);
                        } else {
                            // v5.9.35: Rich completion line with word count, issues, roles, and score
                            const words = (doc.word_count || 0).toLocaleString();
                            const issues = doc.issue_count || 0;
                            const roles = doc.role_count || 0;
                            const score = doc.score || 0;
                            const metaLine = `${words} words • ${issues} issues • ${roles} roles • Score: ${score}%`;
                            updateDocRow(globalIdx, 'complete', metaLine, issues, 100);

                            // v5.9.35: Update running totals in stats row
                            runningIssues += issues;
                            runningRoles += roles;
                            if (issuesCountEl) issuesCountEl.textContent = runningIssues.toLocaleString();
                            if (rolesCountEl) rolesCountEl.textContent = runningRoles.toLocaleString();
                        }

                        // Merge into allResults
                        allResults.documents.push(doc);
                    });

                    // Merge summary
                    if (reviewResult.data.summary) {
                        allResults.summary.total_documents += reviewResult.data.summary.total_documents || 0;
                        allResults.summary.total_issues += reviewResult.data.summary.total_issues || 0;
                        for (const [sev, count] of Object.entries(reviewResult.data.summary.issues_by_severity || {})) {
                            allResults.summary.issues_by_severity[sev] = (allResults.summary.issues_by_severity[sev] || 0) + count;
                        }
                    }

                    // Merge roles
                    if (reviewResult.data.roles_found) {
                        Object.assign(allResults.roles_found, reviewResult.data.roles_found);
                    }
                }

                return { success: true, batchIdx };

            } catch (error) {
                console.error(`[TWR] Batch ${batchIdx + 1} error:`, error);
                // Mark remaining files in this batch as errored
                batchFiles.forEach((_, localIdx) => {
                    const globalIdx = startGlobalIdx + localIdx;
                    const row = document.getElementById(`batch-doc-${globalIdx}`);
                    if (row && !row.classList.contains('complete')) {
                        completedDocs++;
                        docsComplete.textContent = completedDocs;
                        updateDocRow(globalIdx, 'error', `Batch ${batchIdx + 1} failed: ${error.message}`, null, 100);
                    }
                });
                return { success: false, batchIdx, error: error.message };
            }
        }

        try {
            // Process batches concurrently with a limit
            const batchPromises = [];
            let startIdx = 0;

            for (let i = 0; i < batches.length; i += BATCH_LIMITS.MAX_CONCURRENT_BATCHES) {
                const concurrentBatches = batches.slice(i, i + BATCH_LIMITS.MAX_CONCURRENT_BATCHES);
                const promises = concurrentBatches.map((batch, offset) => {
                    const batchIdx = i + offset;
                    const batchStartIdx = batches.slice(0, batchIdx).reduce((sum, b) => sum + b.length, 0);
                    return processBatch(batch, batchIdx, batchStartIdx);
                });

                // Wait for this set of concurrent batches to complete
                const results = await Promise.all(promises);
                batchPromises.push(...results);

                // Update progress between concurrent sets
                if (i + BATCH_LIMITS.MAX_CONCURRENT_BATCHES < batches.length) {
                    queueStatus.textContent = `Processing batches ${i + BATCH_LIMITS.MAX_CONCURRENT_BATCHES + 1}-${Math.min(i + 2 * BATCH_LIMITS.MAX_CONCURRENT_BATCHES, batches.length)} of ${batches.length}...`;
                }
            }

            // Check if any batches failed
            const failedBatches = batchPromises.filter(r => !r.success);
            if (failedBatches.length > 0 && failedBatches.length === batches.length) {
                throw new Error('All batches failed');
            }

            // Stop elapsed time counter
            if (elapsedInterval) clearInterval(elapsedInterval);

            updateProgress(100, 'Analysis Complete!');
            queueStatus.textContent = failedBatches.length > 0
                ? `Completed with ${failedBatches.length} batch error(s)`
                : 'All documents processed';
            progressEl.classList.remove('scanning');

            // Play completion sound
            playCompletionSound();

            // Brief pause to show completion state
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Store results and display
            BatchState.results = allResults;
            displayBatchResults(allResults);

            closeBatchModal();

            // v4.4.0: Show batch tagging modal after batch processing
            // Extract document list from results for tagging
            if (window.TWR?.FunctionTags?.showBatchTaggingModal && allResults.documents) {
                setTimeout(() => {
                    const docs = allResults.documents.map(d => ({
                        id: d.scan_info?.document_id || null,
                        document_id: d.scan_info?.document_id || null,
                        filename: d.filename
                    }));
                    window.TWR.FunctionTags.showBatchTaggingModal(docs);
                }, 1000);
            }

        } catch (error) {
            console.error('[TWR] Batch processing error:', error);
            if (elapsedInterval) clearInterval(elapsedInterval);
            progressEl.classList.remove('scanning');
            const errorMsg = error.message || (typeof error === 'string' ? error : JSON.stringify(error));
            progressText.textContent = 'Error: ' + errorMsg;
            queueStatus.textContent = 'Processing failed';
            // Add error styling
            progressFill.style.background = 'linear-gradient(90deg, #c41e3a, #a01830, #c41e3a)';
            progressFill.style.boxShadow = '0 0 20px rgba(196, 30, 58, 0.6), 0 0 40px rgba(196, 30, 58, 0.4)';
            // Mark remaining docs as errored
            BatchState.files.forEach((_, i) => {
                const row = document.getElementById(`batch-doc-${i}`);
                if (row && !row.classList.contains('complete')) {
                    updateDocRow(i, 'error', 'Processing failed', null, 0);
                }
            });
        } finally {
            BatchState.processing = false;
            startBtn.disabled = false;
            if (elapsedInterval) clearInterval(elapsedInterval);
        }
    }
    
    function displayBatchResults(data) {
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('batch-results').style.display = 'block';
        
        // Summary cards
        const summaryEl = document.getElementById('batch-summary');
        summaryEl.innerHTML = `
            <div class="batch-summary-cards">
                <div class="stat-card">
                    <span class="stat-value">${data.summary.total_documents}</span>
                    <span class="stat-label">Documents</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">${data.summary.total_issues}</span>
                    <span class="stat-label">Issues Found</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">${Object.keys(data.roles_found || {}).length}</span>
                    <span class="stat-label">Unique Roles</span>
                </div>
                <div class="stat-card severity-high">
                    <span class="stat-value">${data.summary.issues_by_severity.High || 0}</span>
                    <span class="stat-label">High Severity</span>
                </div>
            </div>
        `;
        
        // Document list - v3.0.114: Added View button to load individual documents
        const docsEl = document.getElementById('batch-documents');
        docsEl.innerHTML = `
            <h4>Documents Processed</h4>
            <table class="batch-table">
                <thead>
                    <tr>
                        <th>Document</th>
                        <th>Score</th>
                        <th>Issues</th>
                        <th>Roles</th>
                        <th>Words</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.documents.map((doc, idx) => `
                        <tr class="${doc.error ? 'error-row' : ''}" data-doc-index="${idx}">
                            <td>
                                <span class="batch-doc-name">${escapeHtml(doc.filename)}</span>
                            </td>
                            <td>${doc.error ? '-' : `<span class="batch-score grade-${(doc.grade || 'C').toLowerCase()}">${doc.score || 0}%</span>`}</td>
                            <td>${doc.error ? '-' : doc.issue_count}</td>
                            <td>${doc.error ? '-' : doc.role_count}</td>
                            <td>${doc.error ? '-' : (doc.word_count || 0).toLocaleString()}</td>
                            <td>
                                ${doc.error
                                    ? `<span class="badge badge-error">Error</span>`
                                    : `<button class="btn btn-sm btn-primary batch-view-btn" data-filepath="${escapeHtml(doc.filepath)}" data-filename="${escapeHtml(doc.filename)}">
                                        <i data-lucide="eye" style="width:14px;height:14px;margin-right:4px;"></i>View
                                       </button>`
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Attach click handlers to View buttons
        docsEl.querySelectorAll('.batch-view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filepath = btn.dataset.filepath;
                const filename = btn.dataset.filename;
                loadBatchDocument(filepath, filename);
            });
        });

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // v3.0.114: Load individual document from batch results
    async function loadBatchDocument(filepath, filename) {
        try {
            // Show loading state
            const loadingToast = window.showToast ? window.showToast('Loading document...', 'info') : null;

            // Hide batch results
            document.getElementById('batch-results').style.display = 'none';

            // Use the existing review endpoint with the filepath
            const response = await fetch('/api/review/single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({ filepath, filename })
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Failed to load document');
            }

            // Store current state
            if (window.State) {
                window.State.currentFile = filepath;
                window.State.originalFilename = filename;
                window.State.filename = filename;
            }

            // Hide empty state and show stats bar
            const emptyState = document.getElementById('empty-state');
            const statsBar = document.getElementById('stats-bar');
            if (emptyState) emptyState.style.display = 'none';
            if (statsBar) statsBar.style.display = 'flex';

            // Use the main processReviewResults function to properly render
            if (typeof processReviewResults === 'function') {
                processReviewResults(result, 0);
            } else if (typeof window.processReviewResults === 'function') {
                window.processReviewResults(result, 0);
            } else {
                // Fallback: manually update state and render
                console.warn('[TWR] processReviewResults not found, using fallback');
                State.reviewResults = result.data;
                State.issues = result.data.issues || [];
                State.filteredIssues = [...State.issues];
                if (typeof updateResultsUI === 'function') updateResultsUI(result.data);
                if (typeof renderIssuesList === 'function') renderIssuesList();
            }

            // Show success
            if (window.showToast) {
                window.showToast(`Loaded: ${filename}`, 'success');
            }

        } catch (error) {
            console.error('[TWR] Failed to load batch document:', error);
            if (window.showToast) {
                window.showToast('Failed to load document: ' + error.message, 'error');
            }
            // Show batch results again on error
            document.getElementById('batch-results').style.display = 'block';
        }
    }
    
    // Helper - escape HTML (may already exist)
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;');
    }
    
    // Initialize when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBatchUpload);
    } else {
        initBatchUpload();
    }
    
})();

console.log('[TWR] Batch upload functionality loaded');

// ============================================================
// ROLE DICTIONARY MANAGEMENT
// ============================================================

(function() {
    'use strict';
    
    const DictState = {
        roles: [],
        filteredRoles: [],
        editingId: null,
        sharingStatus: null
    };
    
    function initRoleDictionary() {
        // Tab activation
        document.querySelectorAll('.roles-tab[data-tab="dictionary"]').forEach(tab => {
            tab.addEventListener('click', () => {
                loadRoleDictionary();
                loadSharingStatus();
            });
        });
        
        // Search and filters
        document.getElementById('dict-search')?.addEventListener('input', debounce(filterDictionary, 300));
        document.getElementById('dict-filter-source')?.addEventListener('change', filterDictionary);
        document.getElementById('dict-filter-category')?.addEventListener('change', filterDictionary);

        // v4.3.0: Initialize smart search autocomplete for dictionary
        initDictionarySmartSearch();
        
        // Action buttons
        document.getElementById('btn-seed-dictionary')?.addEventListener('click', seedDictionary);
        document.getElementById('btn-add-role')?.addEventListener('click', () => openRoleModal());
        document.getElementById('btn-export-dictionary')?.addEventListener('click', exportDictionary);
        // v4.1.0: Import button now handled by roles-dictionary-fix.js dropdown (CSV + SIPOC)
        // document.getElementById('btn-import-dictionary')?.addEventListener('click', openImportModal);
        
        // SHARING buttons
        document.getElementById('btn-sync-dictionary')?.addEventListener('click', syncDictionary);
        document.getElementById('btn-download-master')?.addEventListener('click', downloadMasterFile);
        
        // Edit modal
        document.getElementById('btn-close-role-modal')?.addEventListener('click', closeRoleModal);
        document.getElementById('btn-cancel-role')?.addEventListener('click', closeRoleModal);
        document.getElementById('btn-save-role')?.addEventListener('click', saveRole);
        
        // Import modal
        document.getElementById('btn-close-import-modal')?.addEventListener('click', closeImportModal);
        const importDropzone = document.getElementById('dict-import-dropzone');
        const importInput = document.getElementById('dict-import-file');
        
        if (importDropzone && importInput) {
            importDropzone.addEventListener('click', () => importInput.click());
            importDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                importDropzone.classList.add('drag-over');
            });
            importDropzone.addEventListener('dragleave', () => {
                importDropzone.classList.remove('drag-over');
            });
            importDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                importDropzone.classList.remove('drag-over');
                if (e.dataTransfer.files.length) {
                    importDictionaryFile(e.dataTransfer.files[0]);
                }
            });
            importInput.addEventListener('change', (e) => {
                if (e.target.files.length) {
                    importDictionaryFile(e.target.files[0]);
                }
            });
        }
        
        // Modal overlays
        document.querySelector('#edit-role-modal .modal-overlay')?.addEventListener('click', closeRoleModal);
        document.querySelector('#import-dict-modal .modal-overlay')?.addEventListener('click', closeImportModal);
    }
    
    async function loadRoleDictionary() {
        try {
            const response = await fetch('/api/roles/dictionary?include_inactive=true');
            const result = await response.json();
            
            if (result.success) {
                DictState.roles = result.data.roles || [];
                filterDictionary();
                updateDictStats();
            } else {
                console.error('[TWR] Failed to load dictionary:', result.error);
            }
        } catch (error) {
            console.error('[TWR] Error loading dictionary:', error);
        }
    }
    
    function filterDictionary() {
        const searchTerm = (document.getElementById('dict-search')?.value || '').toLowerCase();
        const sourceFilter = document.getElementById('dict-filter-source')?.value || '';
        const categoryFilter = document.getElementById('dict-filter-category')?.value || '';
        
        DictState.filteredRoles = DictState.roles.filter(role => {
            // Search
            if (searchTerm) {
                const searchFields = [
                    role.role_name,
                    role.category,
                    role.description,
                    ...(role.aliases || [])
                ].filter(Boolean).join(' ').toLowerCase();
                
                if (!searchFields.includes(searchTerm)) return false;
            }
            
            // Source filter
            if (sourceFilter && role.source !== sourceFilter) return false;
            
            // Category filter
            if (categoryFilter && role.category !== categoryFilter) return false;
            
            return true;
        });
        
        renderDictionary();
    }

    // v4.3.0: Initialize SmartSearch for dictionary search
    function initDictionarySmartSearch() {
        // Check if SmartSearch is available from roles module
        if (!window.TWR?.Roles?.SmartSearch) {
            console.log('[TWR Dict] SmartSearch not available, skipping autocomplete');
            return;
        }

        const SmartSearch = window.TWR.Roles.SmartSearch;

        SmartSearch.init('dict-search', {
            itemType: 'role',
            getItems: () => {
                if (!DictState.roles || DictState.roles.length === 0) return [];

                // Get unique categories and sources
                const categories = new Map();
                const sources = new Map();

                DictState.roles.forEach(role => {
                    const category = role.category || 'Unknown';
                    if (!categories.has(category)) {
                        const count = DictState.roles.filter(r => (r.category || 'Unknown') === category).length;
                        categories.set(category, {
                            label: category,
                            type: 'role',
                            meta: `${count} roles in this category`,
                            badge: count
                        });
                    }

                    const source = role.source || 'unknown';
                    if (!sources.has(source)) {
                        const count = DictState.roles.filter(r => (r.source || 'unknown') === source).length;
                        sources.set(source, {
                            label: source.charAt(0).toUpperCase() + source.slice(1),
                            type: 'role',
                            meta: `${count} roles from this source`,
                            badge: count
                        });
                    }
                });

                // Get sample roles
                const sampleRoles = DictState.roles.slice(0, 15).map(role => ({
                    label: role.role_name,
                    type: 'role',
                    meta: `${role.category || 'Unknown'} • ${role.source || 'unknown'}`
                }));

                return [
                    ...Array.from(categories.values()),
                    ...Array.from(sources.values()),
                    ...sampleRoles.slice(0, 8)
                ];
            },
            onSelect: (item, input) => {
                filterDictionary();
            },
            maxResults: 10
        });

        console.log('[TWR Dict] SmartSearch initialized for dict-search');
    }

    function renderDictionary() {
        const tbody = document.getElementById('dictionary-body');
        const emptyEl = document.getElementById('dict-empty');
        
        if (!tbody) return;
        
        if (DictState.filteredRoles.length === 0) {
            tbody.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'flex';
            return;
        }
        
        if (emptyEl) emptyEl.style.display = 'none';
        
        tbody.innerHTML = DictState.filteredRoles.map(role => {
            const aliases = (role.aliases || []).join(', ') || '-';
            const updatedAt = role.updated_at || role.created_at;
            const updatedBy = role.updated_by || role.created_by;
            const dateStr = updatedAt ? new Date(updatedAt).toLocaleDateString() : '-';
            
            return `
                <tr class="${!role.is_active ? 'inactive-row' : ''}" data-id="${role.id}">
                    <td>
                        <strong>${escapeHtml(role.role_name)}</strong>
                        ${aliases !== '-' ? `<br><small class="text-muted">aka: ${escapeHtml(aliases)}</small>` : ''}
                    </td>
                    <td><span class="category-badge category-${(role.category || '').toLowerCase()}">${escapeHtml(role.category || 'Unknown')}</span></td>
                    <td>
                        <span class="source-badge source-${role.source}">${escapeHtml(role.source)}</span>
                        ${role.source_document ? `<br><small class="text-muted">${escapeHtml(role.source_document)}</small>` : ''}
                    </td>
                    <td>
                        ${dateStr}
                        ${updatedBy ? `<br><small class="text-muted">by ${escapeHtml(updatedBy)}</small>` : ''}
                    </td>
                    <td>
                        ${role.is_active 
                            ? '<span class="status-badge active">Active</span>' 
                            : '<span class="status-badge inactive">Inactive</span>'}
                        ${role.is_deliverable ? '<br><small class="text-muted">(deliverable)</small>' : ''}
                    </td>
                    <td>
                        <button class="btn btn-ghost btn-xs" onclick="window.editDictRole(${role.id})" title="Edit">
                            <i data-lucide="edit-2"></i>
                        </button>
                        ${role.is_active 
                            ? `<button class="btn btn-ghost btn-xs" onclick="window.toggleDictRole(${role.id}, false)" title="Deactivate">
                                <i data-lucide="eye-off"></i>
                               </button>`
                            : `<button class="btn btn-ghost btn-xs" onclick="window.toggleDictRole(${role.id}, true)" title="Activate">
                                <i data-lucide="eye"></i>
                               </button>`
                        }
                        <button class="btn btn-ghost btn-xs btn-danger" onclick="window.deleteDictRole(${role.id})" title="Delete">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
        
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    function updateDictStats() {
        const total = DictState.roles.length;
        const active = DictState.roles.filter(r => r.is_active).length;
        const builtin = DictState.roles.filter(r => r.source === 'builtin').length;
        
        const totalEl = document.getElementById('dict-total');
        const activeEl = document.getElementById('dict-active');
        const builtinEl = document.getElementById('dict-builtin');
        
        if (totalEl) totalEl.textContent = total;
        if (activeEl) activeEl.textContent = active;
        if (builtinEl) builtinEl.textContent = builtin;
    }
    
    async function seedDictionary() {
        if (!confirm('Add built-in roles to the dictionary? This will not overwrite existing roles.')) return;
        
        try {
            const response = await fetch('/api/roles/dictionary/seed', {
                method: 'POST',
                headers: { 'X-CSRF-Token': window.CSRF_TOKEN || '' }
            });
            const result = await response.json();
            
            if (result.success) {
                toast('success', `Added ${result.data.added} roles, ${result.data.skipped} already existed`);
                await loadRoleDictionary();
            } else {
                toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Failed to seed dictionary');
            }
        } catch (error) {
            toast('error', 'Error seeding dictionary: ' + error.message);
        }
    }
    
    function openRoleModal(roleId = null) {
        DictState.editingId = roleId;
        const modal = document.getElementById('edit-role-modal');
        const title = document.getElementById('edit-role-title');
        
        // Clear form
        document.getElementById('edit-role-id').value = roleId || '';
        document.getElementById('edit-role-name').value = '';
        document.getElementById('edit-role-category').value = 'Custom';
        document.getElementById('edit-role-aliases').value = '';
        document.getElementById('edit-role-description').value = '';
        document.getElementById('edit-role-deliverable').checked = false;
        document.getElementById('edit-role-notes').value = '';
        
        if (roleId) {
            // Edit mode - populate form
            const role = DictState.roles.find(r => r.id === roleId);
            if (role) {
                title.textContent = 'Edit Role';
                document.getElementById('edit-role-name').value = role.role_name;
                document.getElementById('edit-role-category').value = role.category || 'Custom';
                document.getElementById('edit-role-aliases').value = (role.aliases || []).join(', ');
                document.getElementById('edit-role-description').value = role.description || '';
                document.getElementById('edit-role-deliverable').checked = role.is_deliverable;
                document.getElementById('edit-role-notes').value = role.notes || '';
            }
        } else {
            title.textContent = 'Add Role';
        }
        
        modal.style.display = 'flex';
        modal.offsetHeight;  // Force reflow
        modal.classList.add('active');
        document.getElementById('edit-role-name').focus();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function closeRoleModal() {
        const modal = document.getElementById('edit-role-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = 'none';
        }
        DictState.editingId = null;
    }
    
    async function saveRole() {
        const roleId = DictState.editingId;
        const roleName = document.getElementById('edit-role-name').value.trim();
        
        if (!roleName) {
            toast('error', 'Role name is required');
            return;
        }
        
        const aliasesStr = document.getElementById('edit-role-aliases').value;
        const aliases = aliasesStr ? aliasesStr.split(',').map(a => a.trim()).filter(Boolean) : [];
        
        const data = {
            role_name: roleName,
            category: document.getElementById('edit-role-category').value,
            aliases: aliases,
            description: document.getElementById('edit-role-description').value.trim(),
            is_deliverable: document.getElementById('edit-role-deliverable').checked,
            notes: document.getElementById('edit-role-notes').value.trim(),
            source: 'manual',
            updated_by: 'user'
        };
        
        try {
            let response;
            if (roleId) {
                // Update
                response = await fetch(`/api/roles/dictionary/${roleId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.CSRF_TOKEN || ''
                    },
                    body: JSON.stringify(data)
                });
            } else {
                // Create
                response = await fetch('/api/roles/dictionary', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.CSRF_TOKEN || ''
                    },
                    body: JSON.stringify(data)
                });
            }
            
            const result = await response.json();
            
            if (result.success) {
                toast('success', roleId ? 'Role updated' : 'Role added');
                closeRoleModal();
                await loadRoleDictionary();
            } else {
                toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Failed to save role');
            }
        } catch (error) {
            toast('error', 'Error saving role: ' + error.message);
        }
    }
    
    window.editDictRole = function(roleId) {
        openRoleModal(roleId);
    };
    
    window.toggleDictRole = async function(roleId, activate) {
        try {
            const response = await fetch(`/api/roles/dictionary/${roleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({ is_active: activate, updated_by: 'user' })
            });
            
            const result = await response.json();
            if (result.success) {
                toast('success', activate ? 'Role activated' : 'Role deactivated');
                await loadRoleDictionary();
            }
        } catch (error) {
            toast('error', 'Error: ' + error.message);
        }
    };
    
    window.deleteDictRole = async function(roleId) {
        if (!confirm('Delete this role from the dictionary?')) return;
        
        try {
            const response = await fetch(`/api/roles/dictionary/${roleId}?hard=true`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': window.CSRF_TOKEN || '' }
            });
            
            const result = await response.json();
            if (result.success) {
                toast('success', 'Role deleted');
                await loadRoleDictionary();
            }
        } catch (error) {
            toast('error', 'Error: ' + error.message);
        }
    };
    
    // ================================================================
    // v2.9.1 D2: SMART IMPORT WIZARD
    // ================================================================
    
    const ImportWizard = {
        step: 1,
        file: null,
        data: null,
        mapping: {},
        roles: []
    };
    
    function openImportModal() {
        ImportWizard.step = 1;
        ImportWizard.file = null;
        ImportWizard.data = null;
        ImportWizard.mapping = {};
        ImportWizard.roles = [];
        
        document.getElementById('import-dict-modal').style.display = 'flex';
        showImportWizardStep(1);
        document.getElementById('import-wizard-next').disabled = true;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    function closeImportModal() {
        document.getElementById('import-dict-modal').style.display = 'none';
    }
    
    function showImportWizardStep(step) {
        ImportWizard.step = step;
        
        // Hide all steps, show current
        for (let i = 1; i <= 5; i++) {
            const el = document.getElementById(`import-step-${i}`);
            if (el) el.style.display = i === step ? 'block' : 'none';
        }
        
        // Update progress
        document.querySelectorAll('.progress-step').forEach((el, i) => {
            el.classList.toggle('active', i + 1 <= step);
        });
        
        // Update title & buttons
        const titles = ['Select File', 'Analyze', 'Map Columns', 'Preview', 'Complete'];
        document.getElementById('import-wizard-title').textContent = `Import Roles - ${titles[step - 1]}`;
        document.getElementById('import-wizard-back').style.display = step > 1 && step < 5 ? 'inline-flex' : 'none';
        document.getElementById('import-wizard-next').style.display = step < 5 ? 'inline-flex' : 'none';
        document.getElementById('import-wizard-cancel').textContent = step === 5 ? 'Close' : 'Cancel';
        document.getElementById('import-wizard-next').innerHTML = step === 4 ? 
            '<i data-lucide="check"></i> Import' : 'Next <i data-lucide="arrow-right"></i>';
        
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    async function handleImportFile(file) {
        ImportWizard.file = file;
        const ext = file.name.split('.').pop().toLowerCase();
        
        try {
            // v2.9.4: Added Excel/xlsx support (#7)
            if (ext === 'xlsx' || ext === 'xls') {
                // Use SheetJS to parse Excel
                if (typeof XLSX === 'undefined') {
                    toast('error', 'Excel support not loaded. Please use CSV or JSON format.');
                    return;
                }
                const data = await file.arrayBuffer();
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
                
                if (jsonData.length < 2) {
                    toast('error', 'Excel file appears empty or has no data rows');
                    return;
                }
                
                const headers = jsonData[0].map(h => String(h || '').trim());
                const rows = jsonData.slice(1).map(row => {
                    const obj = {};
                    headers.forEach((h, i) => obj[h] = row[i] || '');
                    return obj;
                }).filter(r => Object.values(r).some(v => v)); // Filter empty rows
                
                ImportWizard.data = { rows, columns: headers };
            } else if (ext === 'json') {
                const text = await file.text();
                const parsed = JSON.parse(text);
                ImportWizard.data = {
                    rows: parsed.roles || (Array.isArray(parsed) ? parsed : []),
                    columns: Object.keys((parsed.roles || parsed)[0] || {})
                };
            } else if (ext === 'csv') {
                const text = await file.text();
                const lines = text.split(/\r?\n/).filter(l => l.trim());
                const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
                const rows = lines.slice(1).map(line => {
                    const vals = line.split(',').map(v => v.trim().replace(/"/g, ''));
                    const row = {};
                    headers.forEach((h, i) => row[h] = vals[i] || '');
                    return row;
                });
                ImportWizard.data = { rows, columns: headers };
            } else if (ext === 'txt') {
                const text = await file.text();
                const lines = text.split(/\r?\n/).filter(l => l.trim());
                ImportWizard.data = {
                    rows: lines.map(l => ({ role_name: l.trim() })),
                    columns: ['role_name']
                };
            } else {
                toast('error', `Unsupported file format: .${ext}. Use .xlsx, .csv, .json, or .txt`);
                return;
            }
            
            document.getElementById('import-wizard-next').disabled = false;
            showImportWizardStep(2);
            renderImportAnalysis();
        } catch (e) {
            console.error('[TWR] Import error:', e);
            toast('error', 'Failed to parse file: ' + e.message);
        }
    }
    
    function renderImportAnalysis() {
        const { rows, columns } = ImportWizard.data;
        document.getElementById('import-analysis-stats').innerHTML = `
            <p><strong>Rows:</strong> ${rows.length} | <strong>Columns:</strong> ${columns.join(', ')}</p>
        `;
        
        let preview = '<table class="data-table" style="font-size:11px;"><thead><tr>';
        columns.slice(0, 4).forEach(c => preview += `<th>${escapeHtml(c)}</th>`);
        preview += '</tr></thead><tbody>';
        rows.slice(0, 3).forEach(r => {
            preview += '<tr>';
            columns.slice(0, 4).forEach(c => preview += `<td>${escapeHtml(String(r[c] || '').slice(0, 25))}</td>`);
            preview += '</tr>';
        });
        preview += '</tbody></table>';
        document.getElementById('import-analysis-preview').innerHTML = preview;
    }
    
    function renderColumnMapping() {
        const { columns } = ImportWizard.data;
        const fields = ['role_name', 'category', 'aliases', 'description'];
        
        // Auto-detect
        const auto = {};
        columns.forEach(c => {
            const lc = c.toLowerCase();
            if (lc.includes('role') || lc.includes('name')) auto.role_name = c;
            else if (lc.includes('category') || lc.includes('type')) auto.category = c;
            else if (lc.includes('alias')) auto.aliases = c;
            else if (lc.includes('desc') || lc.includes('note')) auto.description = c;
        });
        if (columns.length === 1) auto.role_name = columns[0];
        ImportWizard.mapping = auto;
        
        let html = '';
        fields.forEach(f => {
            html += `<div style="margin-bottom:10px;display:flex;align-items:center;gap:10px;">
                <label style="width:100px;">${f.replace('_', ' ')}${f === 'role_name' ? ' *' : ''}:</label>
                <select class="form-select" data-field="${f}" onchange="ImportWizard.mapping['${f}']=this.value">
                    <option value="">-- Skip --</option>
                    ${columns.map(c => `<option value="${c}" ${auto[f] === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
                </select>
            </div>`;
        });
        document.getElementById('import-column-mapping').innerHTML = html;
    }
    
    function renderImportPreview() {
        const { rows } = ImportWizard.data;
        const { mapping } = ImportWizard;
        const roleCol = mapping.role_name;
        
        if (!roleCol) {
            document.getElementById('import-preview-summary').innerHTML = '<p class="text-danger">Please select a Role Name column</p>';
            ImportWizard.roles = [];
            return;
        }
        
        // Build roles list
        ImportWizard.roles = rows.map(r => ({
            role_name: r[roleCol] || '',
            category: r[mapping.category] || 'Imported',
            aliases: r[mapping.aliases] ? r[mapping.aliases].split(/[;,]/).map(a => a.trim()).filter(Boolean) : [],
            description: r[mapping.description] || ''
        })).filter(r => r.role_name.trim());
        
        document.getElementById('import-preview-summary').innerHTML = `
            <p><strong>${ImportWizard.roles.length}</strong> roles ready to import</p>
        `;
        
        let list = '<div style="font-size:12px;">';
        ImportWizard.roles.slice(0, 10).forEach(r => {
            list += `<div style="padding:4px 0;border-bottom:1px solid var(--border-color);">
                <strong>${escapeHtml(r.role_name)}</strong>
                <span class="text-muted" style="margin-left:8px;">${escapeHtml(r.category)}</span>
            </div>`;
        });
        if (ImportWizard.roles.length > 10) {
            list += `<p class="text-muted">...and ${ImportWizard.roles.length - 10} more</p>`;
        }
        list += '</div>';
        document.getElementById('import-preview-list').innerHTML = list;
    }
    
    async function executeImport() {
        if (ImportWizard.roles.length === 0) {
            toast('error', 'No roles to import');
            return;
        }
        
        try {
            const response = await fetch('/api/roles/dictionary/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({
                    roles: ImportWizard.roles,
                    source: 'wizard_import',
                    skip_duplicates: document.getElementById('import-skip-duplicates')?.checked !== false
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('import-complete-stats').innerHTML = `
                    <p><strong>${result.data?.added || 0}</strong> roles added</p>
                    <p><strong>${result.data?.skipped || 0}</strong> skipped (duplicates)</p>
                `;
                showImportWizardStep(5);
                await loadRoleDictionary();
            } else {
                toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Import failed');
            }
        } catch (e) {
            toast('error', 'Import error: ' + e.message);
        }
    }
    
    // Wire up wizard navigation
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('import-wizard-next')?.addEventListener('click', function() {
            if (ImportWizard.step === 2) {
                showImportWizardStep(3);
                renderColumnMapping();
            } else if (ImportWizard.step === 3) {
                showImportWizardStep(4);
                renderImportPreview();
            } else if (ImportWizard.step === 4) {
                executeImport();
            }
        });
        
        document.getElementById('import-wizard-back')?.addEventListener('click', function() {
            if (ImportWizard.step > 1) showImportWizardStep(ImportWizard.step - 1);
        });
        
        document.getElementById('import-wizard-cancel')?.addEventListener('click', closeImportModal);
        document.getElementById('btn-close-import-modal')?.addEventListener('click', closeImportModal);
        
        // File input handler
        const dropzone = document.getElementById('dict-import-dropzone');
        const fileInput = document.getElementById('dict-import-file');
        
        if (dropzone && fileInput) {
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
            dropzone.addEventListener('drop', e => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
                if (e.dataTransfer.files[0]) handleImportFile(e.dataTransfer.files[0]);
            });
            fileInput.addEventListener('change', () => {
                if (fileInput.files[0]) handleImportFile(fileInput.files[0]);
            });
        }
    });
    
    // Legacy function for backwards compatibility
    async function importDictionaryFile(file) {
        handleImportFile(file);
    }
    
    async function exportDictionary() {
        window.location.href = '/api/roles/dictionary/export?format=csv&include_inactive=true';
    }
    
    // ================================================================
    // SHARING FUNCTIONS
    // ================================================================
    
    async function loadSharingStatus() {
        try {
            const response = await fetch('/api/roles/dictionary/status');
            const result = await response.json();
            
            if (result.success) {
                DictState.sharingStatus = result.data;
                updateSharingStatusUI(result.data);
            }
        } catch (error) {
            console.error('[TWR] Error loading sharing status:', error);
        }
    }
    
    function updateSharingStatusUI(status) {
        const statusText = document.getElementById('dict-status-text');
        const statusInfo = document.getElementById('dict-sharing-info');
        
        if (!statusText || !statusInfo) return;
        
        const dbCount = status.database?.role_count || 0;
        const masterExists = status.master_file?.exists;
        const masterCount = status.master_file?.role_count || 0;
        const sharedConfigured = status.shared_folder?.configured;
        const sharedExists = status.shared_folder?.exists;
        
        let statusMsg = `${dbCount} roles in local database`;
        
        if (masterExists) {
            statusMsg += ` • Master file: ${masterCount} roles`;
        }
        
        if (sharedConfigured) {
            if (sharedExists) {
                statusMsg += ` • Shared folder connected`;
            } else {
                statusMsg += ` • Shared folder configured but not accessible`;
            }
        }
        
        statusText.textContent = statusMsg;
        statusInfo.style.display = 'flex';
    }
    
    async function syncDictionary() {
        const mergeMode = await showSyncDialog();
        if (!mergeMode) return;
        
        try {
            // v2.9.4: Add create_if_missing option to fix #9
            const response = await fetch('/api/roles/dictionary/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({ 
                    merge_mode: mergeMode,
                    create_if_missing: true  // v2.9.4: Auto-create master if not found
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // v2.9.4: Handle case where master was created
                if (result.created_new) {
                    toast('success', result.message || 'Created new master dictionary file');
                } else {
                    const msg = `Sync complete: ${result.added || 0} added, ${result.updated || 0} updated, ${result.skipped || 0} skipped`;
                    toast('success', msg);
                }
                await loadRoleDictionary();
                await loadSharingStatus();
            } else {
                // v2.9.4: Offer to create master if not found
                if (result.can_create) {
                    const createIt = confirm(
                        'No master dictionary file found.\n\n' +
                        'Would you like to create one from your current dictionary?\n' +
                        `Suggested location: ${result.suggested_path || 'role_dictionary_master.json'}`
                    );
                    if (createIt) {
                        await createMasterFromCurrent();
                    }
                } else {
                    toast('error', typeof result.error === 'string' ? result.error : result.error?.message || 'Sync failed');
                }
            }
        } catch (error) {
            toast('error', 'Sync error: ' + error.message);
        }
    }
    
    // v2.9.4: New function to create master from current dictionary (#9)
    async function createMasterFromCurrent() {
        try {
            showLoading('Creating master dictionary file...');
            
            const response = await fetch('/api/roles/dictionary/create-master', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                toast('success', `Master dictionary created with ${result.count || 0} roles`);
                await loadSharingStatus();
            } else {
                toast('error', result.error || 'Failed to create master file');
            }
        } catch (error) {
            toast('error', 'Error creating master: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function showSyncDialog() {
        return new Promise((resolve) => {
            const choice = confirm(
                'Sync from master dictionary file?\n\n' +
                'Options:\n' +
                '• OK = Add new roles only (keeps your existing roles)\n' +
                '• Cancel = Abort sync\n\n' +
                'For advanced options (replace all, update existing), use the API directly.'
            );
            
            resolve(choice ? 'add_new' : null);
        });
    }
    
    function downloadMasterFile() {
        // Download the shareable master file
        window.location.href = '/api/roles/dictionary/download-master?include_inactive=false';
        toast('success', 'Downloading role_dictionary_master.json - share this with your team!');
    }
    
    // Helper
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    
    function toast(type, message) {
        if (window.toast) {
            window.toast(type, message);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRoleDictionary);
    } else {
        initRoleDictionary();
    }
    
})();

console.log('[TWR] Role dictionary functionality loaded');

// =============================================================================
// STATEMENT FORGE MODULE (v3.0.111 - Full Parity Fullscreen)
// =============================================================================
// Extracts work statements for TIBCO Nimbus import
// v3.0.111: Complete rewrite for fullscreen layout with sidebar, edit panel, and all features

const StatementForge = (function() {
    'use strict';

    // Module state
    let statements = [];
    let selectedIds = new Set();
    let currentDocument = null;
    let focusedIndex = -1;
    let currentFilter = 'all';
    let currentSearch = '';
    let undoStack = [];
    let redoStack = [];
    let editingStatement = null;
    let sortable = null;

    // API base URL
    const API_BASE = '/api/statement-forge';

    // DOM element references
    const el = (id) => document.getElementById(id);

    // Initialize module
    function init() {
        console.log('[SF] Initializing Statement Forge v3.0.111...');

        // Initialize all event listeners for fullscreen layout
        initFullscreenListeners();
        initKeyboardShortcuts();
        initDragAndDrop();

        // v4.3.0: Initialize smart search autocomplete
        initStatementForgeSmartSearch();

        console.log('[TWR] Statement Forge v3.0.111 initialized');
    }

    // v4.3.0: Initialize SmartSearch for Statement Forge search input
    function initStatementForgeSmartSearch() {
        // Check if SmartSearch is available from roles module
        if (!window.TWR?.Roles?.SmartSearch) {
            console.log('[SF] SmartSearch not available, skipping autocomplete');
            return;
        }

        const SmartSearch = window.TWR.Roles.SmartSearch;

        SmartSearch.init('sf-search-input', {
            itemType: 'statement',
            getItems: () => {
                if (!statements || statements.length === 0) return [];

                // Get unique types and statuses
                const types = new Map();
                const statuses = new Map();

                statements.forEach(stmt => {
                    const type = stmt.type || 'unknown';
                    if (!types.has(type)) {
                        const count = statements.filter(s => (s.type || 'unknown') === type).length;
                        types.set(type, {
                            label: type.charAt(0).toUpperCase() + type.slice(1),
                            type: 'statement',
                            meta: `${count} statements of this type`,
                            badge: count,
                            searchType: 'type'
                        });
                    }

                    const status = stmt.status || 'pending';
                    if (!statuses.has(status)) {
                        const count = statements.filter(s => (s.status || 'pending') === status).length;
                        statuses.set(status, {
                            label: status.charAt(0).toUpperCase() + status.slice(1),
                            type: 'statement',
                            meta: `${count} statements with this status`,
                            badge: count,
                            searchType: 'status'
                        });
                    }
                });

                // Get sample statements (text content)
                const sampleStatements = statements.slice(0, 20).map(stmt => {
                    const text = stmt.text || stmt.content || '';
                    const truncated = text.length > 60 ? text.substring(0, 57) + '...' : text;
                    return {
                        label: truncated,
                        type: 'statement',
                        meta: `${stmt.type || 'unknown'} • ${stmt.number || ''}`,
                        searchType: 'text'
                    };
                });

                // Return types first, then statuses, then sample statements
                return [
                    ...Array.from(types.values()),
                    ...Array.from(statuses.values()),
                    ...sampleStatements.slice(0, 8)
                ];
            },
            onSelect: (item, input) => {
                currentSearch = input.value.toLowerCase();
                renderStatements();
                updateStats();
            },
            maxResults: 10,
            minChars: 1
        });

        console.log('[SF] SmartSearch initialized for sf-search-input');
    }

    // v3.0.111: Initialize fullscreen modal listeners
    function initFullscreenListeners() {
        // Extract button
        const extractBtn = el('btn-sf-extract');
        if (extractBtn && !extractBtn._initialized) {
            extractBtn._initialized = true;
            extractBtn.addEventListener('click', () => extractStatements(false));
        }

        // Select all checkbox
        const selectAll = el('sf-select-all');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const displayed = getDisplayedStatements();
                displayed.forEach(stmt => {
                    if (this.checked) {
                        selectedIds.add(stmt.id);
                    } else {
                        selectedIds.delete(stmt.id);
                    }
                });
                renderStatements();
                updateToolbarState();
            });
        }

        // Search input
        const searchInput = el('sf-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                currentSearch = this.value.toLowerCase();
                renderStatements();
                updateStats();
            }, 300));
        }

        // Search clear button
        const searchClear = el('sf-search-clear');
        if (searchClear) {
            searchClear.addEventListener('click', () => {
                const input = el('sf-search-input');
                if (input) {
                    input.value = '';
                    currentSearch = '';
                    searchClear.style.display = 'none';
                    renderStatements();
                    updateStats();
                }
            });
        }

        // Filter chips
        document.querySelectorAll('.sf-filter-chip').forEach(chip => {
            chip.addEventListener('click', function() {
                document.querySelectorAll('.sf-filter-chip').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                currentFilter = this.dataset.filter;
                renderStatements();
                updateStats();
            });
        });

        // Document type selector
        document.querySelectorAll('input[name="sfDocType"]').forEach(radio => {
            radio.addEventListener('change', function() {
                console.log('[SF] Document type changed to:', this.value);
            });
        });

        // Toolbar buttons - Primary
        el('sf-btn-export')?.addEventListener('click', toggleExportDropdown);
        el('sf-btn-undo')?.addEventListener('click', undo);
        el('sf-btn-redo')?.addEventListener('click', redo);
        el('sf-btn-expand-all')?.addEventListener('click', expandAll);
        el('sf-btn-collapse-all')?.addEventListener('click', collapseAll);

        // Toolbar buttons - Secondary
        el('sf-btn-add')?.addEventListener('click', () => showModal('modal-sf-add'));
        el('sf-btn-delete')?.addEventListener('click', deleteSelected);
        el('sf-btn-merge')?.addEventListener('click', () => showMergeModal());
        el('sf-btn-split')?.addEventListener('click', () => showSplitModal());
        el('sf-btn-move-up')?.addEventListener('click', moveSelectedUp);
        el('sf-btn-move-down')?.addEventListener('click', moveSelectedDown);
        el('sf-btn-indent-left')?.addEventListener('click', outdentSelected);
        el('sf-btn-indent-right')?.addEventListener('click', indentSelected);
        el('sf-btn-renumber')?.addEventListener('click', () => showModal('modal-sf-renumber'));
        el('sf-btn-view-source')?.addEventListener('click', openViewSourceMode);

        // Sidebar footer buttons
        el('sf-btn-history')?.addEventListener('click', async () => {
            if (typeof TWR !== 'undefined' && TWR.StatementHistory) {
                const docTitle = el('sf-doc-title')?.textContent || '';
                let docId = window._sfCurrentDocumentId || 0;
                let scanId = window._sfCurrentScanId || 0;
                let resolvedTitle = docTitle !== 'No Document Loaded' ? docTitle : '';

                // v4.2.0: Fallback — look up document from scan history
                if (!docId) {
                    try {
                        const histResp = await api('/scan-history');
                        if (histResp?.success && histResp?.data) {
                            const fname = State.filename || State.currentFilename;
                            // Try matching by filename first, then fall back to most recent with statements
                            let match = fname
                                ? histResp.data.find(s => s.filename === fname && s.document_id)
                                : null;
                            if (!match) {
                                match = histResp.data.find(s => s.document_id && s.statement_count > 0);
                            }
                            if (match) {
                                docId = match.document_id;
                                scanId = match.scan_id || scanId;
                                resolvedTitle = resolvedTitle || match.filename || '';
                                window._sfCurrentDocumentId = docId;
                                window._sfCurrentScanId = scanId;
                            }
                        }
                    } catch (e) {
                        console.warn('[SF] History lookup failed:', e);
                    }
                }

                if (!docId) {
                    toast('info', 'No documents with statement history found. Run a document scan first.');
                    return;
                }
                TWR.StatementHistory.open(docId, scanId, resolvedTitle);
            } else {
                toast('error', 'Statement History module not loaded');
            }
        });
        el('sf-btn-help')?.addEventListener('click', () => showModal('modal-sf-help'));

        // Export dropdown items
        document.querySelectorAll('#sf-export-menu .sf-dropdown-item').forEach(item => {
            item.addEventListener('click', function() {
                const format = this.dataset.format;
                exportAs(format);
                el('sf-export-menu').style.display = 'none';
            });
        });

        // File inputs
        el('sf-file-input')?.addEventListener('change', function() {
            handleFileUpload(this);
        });
        el('sf-file-input-empty')?.addEventListener('change', function() {
            handleFileUpload(this);
        });

        // Use current document button
        el('sf-btn-use-current')?.addEventListener('click', () => {
            extractStatements(false);
        });

        // Edit panel
        initEditPanel();

        // Modal action buttons
        initModalActions();

        // Help tabs
        document.querySelectorAll('.sf-help-tab-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.sf-help-tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sf-help-tab-content').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                const tabId = 'sf-help-' + this.dataset.helpTab;
                el(tabId)?.classList.add('active');
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.sf-export-dropdown')) {
                const menu = el('sf-export-menu');
                if (menu) menu.style.display = 'none';
            }
        });
    }

    // v3.0.111: Initialize edit panel
    function initEditPanel() {
        // Close edit button
        el('sf-btn-close-edit')?.addEventListener('click', closeEditPanel);
        el('sf-btn-cancel-edit')?.addEventListener('click', closeEditPanel);

        // Save edit button
        el('sf-btn-save-edit')?.addEventListener('click', saveEdit);

        // Level selector buttons
        document.querySelectorAll('.sf-level-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.sf-level-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // v3.0.111: Initialize modal action buttons
    function initModalActions() {
        // Add modal
        el('sf-btn-add-confirm')?.addEventListener('click', confirmAddStatement);

        // Renumber modal
        el('sf-btn-renumber-confirm')?.addEventListener('click', confirmRenumber);
        el('sf-renumber-strategy')?.addEventListener('change', function() {
            const hints = {
                'hierarchical': 'Maintains hierarchy: 1.0 → 1.1 → 1.1.1',
                'sequential': 'Simple sequence: 1.1, 1.2, 1.3...',
                'continue': 'Continues from last number in document'
            };
            el('sf-strategy-hint').textContent = hints[this.value] || '';
        });

        // Merge modal
        el('sf-btn-merge-confirm')?.addEventListener('click', confirmMerge);

        // Split modal
        el('sf-btn-split-confirm')?.addEventListener('click', confirmSplit);
        el('sf-split-by')?.addEventListener('change', updateSplitPreview);
    }
    
    // v3.0.111: Update document status in fullscreen header
    function updateDocumentStatus() {
        const titleEl = el('sf-doc-title');
        const subtitleEl = el('sf-doc-subtitle');
        const statusIndicator = el('sf-status-indicator');
        const statusText = el('sf-status-text');

        const hasDoc = window.State && (
            window.State.filename ||
            window.State.reviewResults?.document_info?.filename ||
            window.State.currentText ||
            window.State.reviewResults
        );

        const filename = window.State?.filename ||
            window.State?.currentFilename ||
            window.State?.reviewResults?.document_info?.filename ||
            window.State?.reviewResults?.filename;

        const wordCount = window.State?.reviewResults?.word_count ||
            window.State?.reviewResults?.document_info?.word_count ||
            (window.State?.currentText?.split(/\s+/).length || 0);

        const hasStatements = statements.length > 0;

        // Update status indicator
        if (statusIndicator && statusText) {
            statusIndicator.classList.remove('loaded', 'extracted');
            statusText.classList.remove('loaded', 'extracted');

            if (hasStatements) {
                // Statements extracted
                statusIndicator.classList.add('extracted');
                statusText.classList.add('extracted');
                statusIndicator.innerHTML = '<i data-lucide="check-circle"></i>';
                statusText.textContent = `${statements.length} statements extracted`;
            } else if (hasDoc) {
                // Document loaded but not extracted
                statusIndicator.classList.add('loaded');
                statusText.classList.add('loaded');
                statusIndicator.innerHTML = '<i data-lucide="file-check"></i>';
                statusText.textContent = 'Document loaded';
            } else {
                // No document
                statusIndicator.innerHTML = '<i data-lucide="file-x"></i>';
                statusText.textContent = 'No document';
            }

            // Re-initialize lucide icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }

        if (titleEl) {
            titleEl.textContent = filename || (hasDoc ? 'Document Loaded' : 'No Document Loaded');
        }

        if (subtitleEl) {
            if (hasStatements) {
                subtitleEl.textContent = `${statements.length} statements • Ready to export`;
            } else if (hasDoc && wordCount > 0) {
                subtitleEl.textContent = `~${wordCount.toLocaleString()} words • Ready for extraction`;
            } else if (hasDoc) {
                subtitleEl.textContent = 'Ready for extraction';
            } else {
                subtitleEl.textContent = 'Open a document or use current document to begin extraction';
            }
        }

        // Update empty state visibility
        const emptyState = el('sf-empty-state');
        if (emptyState) {
            emptyState.style.display = statements.length === 0 ? 'flex' : 'none';
        }
    }

    // v3.0.111: Initialize keyboard shortcuts
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle when Statement Forge modal is open
            const modal = el('modal-statement-forge');
            if (!modal || modal.style.display === 'none' || !modal.classList.contains('show')) {
                // Check if modal is visible via class or computed style
                const style = window.getComputedStyle(modal);
                if (style.display === 'none') return;
            }

            // Don't interfere with input fields
            if (e.target.matches('input, textarea, [contenteditable]')) {
                if (e.key === 'Escape') {
                    e.target.blur();
                    e.preventDefault();
                }
                return;
            }

            const ctrl = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;
            const alt = e.altKey;

            switch (e.key) {
                case 'Escape':
                    // v4.2.0: Don't steal Escape from Statement History modal
                    if (typeof TWR !== 'undefined' && TWR.StatementHistory?.isOpen?.()) return;
                    e.preventDefault();
                    if (el('sf-edit-panel')?.classList.contains('open')) {
                        closeEditPanel();
                    } else {
                        closeModal('modal-statement-forge');
                    }
                    break;

                case 'F1':
                    e.preventDefault();
                    showModal('modal-sf-help');
                    break;

                case 'o':
                    if (ctrl) {
                        e.preventDefault();
                        el('sf-file-input')?.click();
                    }
                    break;

                case 's':
                    if (ctrl) {
                        e.preventDefault();
                        if (statements.length > 0) exportAs('csv');
                    }
                    break;

                case 'f':
                    if (ctrl) {
                        e.preventDefault();
                        el('sf-search-input')?.focus();
                    }
                    break;

                case 'a':
                    if (ctrl) {
                        e.preventDefault();
                        selectAll();
                    }
                    break;

                case 'z':
                    if (ctrl && !shift) {
                        e.preventDefault();
                        undo();
                    } else if (ctrl && shift) {
                        e.preventDefault();
                        redo();
                    }
                    break;

                case 'y':
                    if (ctrl) {
                        e.preventDefault();
                        redo();
                    }
                    break;

                case 'm':
                    if (ctrl && selectedIds.size >= 2) {
                        e.preventDefault();
                        showMergeModal();
                    }
                    break;

                case 'e':
                    if (ctrl && !shift) {
                        e.preventDefault();
                        expandAll();
                    } else if (ctrl && shift) {
                        e.preventDefault();
                        collapseAll();
                    }
                    break;

                case 'Insert':
                    e.preventDefault();
                    showModal('modal-sf-add');
                    break;

                case 'Delete':
                    if (selectedIds.size > 0) {
                        e.preventDefault();
                        deleteSelected();
                    }
                    break;

                case 'ArrowUp':
                    e.preventDefault();
                    if (alt && selectedIds.size > 0) {
                        moveSelectedUp();
                    } else {
                        navigateRows(-1);
                    }
                    break;

                case 'ArrowDown':
                    e.preventDefault();
                    if (alt && selectedIds.size > 0) {
                        moveSelectedDown();
                    } else {
                        navigateRows(1);
                    }
                    break;

                case 'ArrowLeft':
                    if (alt && selectedIds.size > 0) {
                        e.preventDefault();
                        outdentSelected();
                    }
                    break;

                case 'ArrowRight':
                    if (alt && selectedIds.size > 0) {
                        e.preventDefault();
                        indentSelected();
                    }
                    break;

                case ' ':
                    e.preventDefault();
                    toggleFocusedSelection();
                    break;

                case 'Enter':
                    if (focusedIndex >= 0) {
                        e.preventDefault();
                        const displayed = getDisplayedStatements();
                        if (displayed[focusedIndex]) {
                            openEditPanel(displayed[focusedIndex]);
                        }
                    }
                    break;
            }
        });
    }

    // v3.0.111: Initialize drag and drop
    function initDragAndDrop() {
        const tableBody = el('sf-statements-table');
        if (!tableBody || typeof Sortable === 'undefined') {
            console.log('[SF] SortableJS not available, drag-drop disabled');
            return;
        }

        // Will be initialized after first render
    }

    // v3.0.111: Setup sortable after render
    function setupSortable() {
        const tableBody = el('sf-statements-table');
        if (!tableBody || typeof Sortable === 'undefined') return;

        if (sortable) {
            sortable.destroy();
        }

        sortable = new Sortable(tableBody, {
            handle: '.sf-col-drag',
            animation: 150,
            ghostClass: 'sf-drag-ghost',
            chosenClass: 'sf-drag-chosen',
            onEnd: function(evt) {
                const oldIndex = evt.oldIndex;
                const newIndex = evt.newIndex;
                if (oldIndex !== newIndex) {
                    saveUndoState('Reorder statements');
                    const item = statements.splice(oldIndex, 1)[0];
                    statements.splice(newIndex, 0, item);
                    renderStatements();
                }
            }
        });
    }
    
    // Extract statements from current document
    // v2.9.4: Added silent parameter for auto-extraction (#4)
    // v3.0.35: Added session-based extraction (works before review)
    async function extractStatements(silent = false) {
        // v3.0.35: Check for document using ACTUAL State properties
        // Primary: State.filename (set after upload)
        // Secondary: State.reviewResults.document_info.filename (set after review)
        const hasDoc = window.State && (
            window.State.filename || 
            window.State.reviewResults?.document_info?.filename
        );
        const hasText = window.State && (
            window.State.currentText || 
            window.State.reviewResults
        );
        
        if (!hasDoc && !hasText) {
            if (!silent) {
                toast('error', 'No document loaded. Please upload a document first.');
            }
            return;
        }
        
        if (!silent) {
            showLoading('Extracting statements...');
        }
        
        try {
            let response;
            
            // v3.0.35: Prefer session-based extraction (works without review)
            // Use this path when we have a filename but no text yet
            if (hasDoc && !hasText) {
                console.log('[SF] Using session-based extraction (no review yet)');
                response = await fetch(`${API_BASE}/extract-from-session`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.State?.csrfToken || ''
                    },
                    body: JSON.stringify({})
                });
            } else {
                // Fall back to text-based extraction (after review completed)
                const documentText = window.State.currentText || 
                    (window.State.reviewResults?.document_info?.paragraphs || [])
                        .map(p => p[1] || p).join('\n');
                
                if (!documentText || documentText.trim().length === 0) {
                    // Try session-based as fallback
                    console.log('[SF] No text available, trying session-based extraction');
                    response = await fetch(`${API_BASE}/extract-from-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': window.State?.csrfToken || ''
                        },
                        body: JSON.stringify({})
                    });
                } else {
                    // Get document name from available sources
                    const docName = window.State.filename || 
                        window.State.reviewResults?.document_info?.filename ||
                        'Unknown Document';
                    
                    response = await fetch(`${API_BASE}/extract`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': window.State?.csrfToken || ''
                        },
                        body: JSON.stringify({
                            text: documentText,
                            document_name: docName,
                            options: {
                                include_context: true,
                                detect_directives: true
                            }
                        })
                    });
                }
            }
            
            const result = await response.json();
            
            if (result.success) {
                // v3.0.35: Handle both response formats (data wrapper or direct)
                const data = result.data || result;
                statements = data.statements || [];
                updateStats(data);
                renderStatements();
                updateDocumentStatus(); // Update status indicator
                if (!silent) {
                    toast('success', `Extracted ${statements.length} statements`);
                } else {
                    console.log(`[SF] Auto-extracted ${statements.length} statements`);
                }

                // v3.0.114: Auto-map statements to roles (silently in background)
                // v3.0.115: Also extract roles directly from statements as fallback
                if (statements.length > 0) {
                    autoMapToRoles();
                    extractRolesFromStatements();
                }
            } else {
                throw new Error(result.error || 'Extraction failed');
            }
        } catch (error) {
            console.error('[SF] Extraction error:', error);
            if (!silent) {
                toast('error', `Extraction failed: ${error.message}`);
            }
        } finally {
            if (!silent) {
                hideLoading();
            }
        }
    }
    
    // v3.0.111: Update statistics display for fullscreen sidebar
    function updateStats(data = {}) {
        const displayed = getDisplayedStatements();
        const total = statements.length;
        const filtered = displayed.length;
        const sections = statements.filter(s => s.is_header || s.level <= 2).length;
        const selected = selectedIds.size;

        // Update sidebar stats
        const totalEl = el('sf-stat-total');
        const filteredEl = el('sf-stat-filtered');
        const sectionsEl = el('sf-stat-sections');
        const selectedEl = el('sf-stat-selected');

        if (totalEl) totalEl.textContent = total;
        if (filteredEl) filteredEl.textContent = filtered;
        if (sectionsEl) sectionsEl.textContent = sections;
        if (selectedEl) selectedEl.textContent = selected;

        // Update undo/redo counts
        const undoCountEl = el('sf-undo-count');
        const redoCountEl = el('sf-redo-count');
        if (undoCountEl) undoCountEl.textContent = undoStack.length;
        if (redoCountEl) redoCountEl.textContent = redoStack.length;

        // Update search clear visibility
        const searchClear = el('sf-search-clear');
        if (searchClear) {
            searchClear.style.display = currentSearch ? 'block' : 'none';
        }

        // Update selection info
        const selectionInfo = el('sf-selection-info');
        const selectionCount = el('sf-selection-count');
        if (selectionInfo && selectionCount) {
            selectionInfo.style.display = selected > 0 ? 'block' : 'none';
            selectionCount.textContent = selected;
        }
    }

    // v3.0.114: Check if a role name exists in the Role Dictionary
    function isRoleInDictionary(roleName) {
        if (!roleName || !window.State?.roles) return false;
        const roles = window.State.roles.roles || window.State.roles;
        if (!roles || typeof roles !== 'object') return false;

        // Case-insensitive match
        const normalizedRole = roleName.toLowerCase().trim();
        return Object.keys(roles).some(k => k.toLowerCase().trim() === normalizedRole);
    }

    // v3.0.111: Get statements filtered by current search and filter
    function getDisplayedStatements() {
        return statements.filter(stmt => {
            // Filter by directive
            if (currentFilter !== 'all') {
                const directive = (stmt.directive || '').toLowerCase();
                if (currentFilter === 'process') {
                    if (directive && directive !== '') return false;
                } else {
                    if (directive !== currentFilter) return false;
                }
            }

            // Filter by search
            if (currentSearch) {
                const text = (stmt.description || stmt.statement || stmt.title || '').toLowerCase();
                const number = (stmt.number || '').toLowerCase();
                const role = (stmt.role || '').toLowerCase();
                if (!text.includes(currentSearch) && !number.includes(currentSearch) && !role.includes(currentSearch)) {
                    return false;
                }
            }

            return true;
        });
    }
    
    // v3.0.111: Render statements in fullscreen table
    function renderStatements() {
        const tableBody = el('sf-statements-table');
        const emptyState = el('sf-empty-state');

        if (!tableBody) return;

        const displayStatements = getDisplayedStatements();

        // Show/hide empty state
        if (emptyState) {
            emptyState.style.display = statements.length === 0 ? 'flex' : 'none';
        }

        if (statements.length === 0) {
            tableBody.innerHTML = '';
            updateStats();
            updateToolbarState();
            return;
        }

        if (displayStatements.length === 0 && statements.length > 0) {
            tableBody.innerHTML = `
                <div class="sf-no-results" style="padding:40px;text-align:center;color:var(--text-muted);">
                    <p>No statements match current filters</p>
                    <button class="btn btn-secondary btn-sm" onclick="StatementForge.clearFilters()">Clear Filters</button>
                </div>
            `;
            updateStats();
            updateToolbarState();
            return;
        }

        // Render rows
        tableBody.innerHTML = displayStatements.map((stmt, idx) => {
            const stmtText = stmt.description || stmt.statement || stmt.title || '';
            const directive = (stmt.directive || '').toLowerCase();
            const level = stmt.level || 4;
            const isSelected = selectedIds.has(stmt.id);
            const isFocused = idx === focusedIndex;
            const isHeader = stmt.is_header || level <= 2;

            let directiveClass = directive || 'process';
            let directiveLabel = directive ? directive.charAt(0).toUpperCase() + directive.slice(1) : 'Process';

            return `
                <div class="sf-statement-row ${isSelected ? 'selected' : ''} ${isFocused ? 'focused' : ''} ${isHeader ? 'is-header' : ''}"
                     data-id="${stmt.id}" data-level="${level}" data-index="${idx}">
                    <div class="sf-col sf-col-drag"><i data-lucide="grip-vertical"></i></div>
                    <div class="sf-col sf-col-checkbox">
                        <input type="checkbox" data-id="${stmt.id}" ${isSelected ? 'checked' : ''}>
                    </div>
                    <div class="sf-col sf-col-expand">
                        ${isHeader ? '<button class="sf-expand-btn" data-id="' + stmt.id + '"><i data-lucide="chevron-down"></i></button>' : ''}
                    </div>
                    <div class="sf-col sf-col-number">${escapeHtml(stmt.number || '')}</div>
                    <div class="sf-col sf-col-description">${escapeHtml(truncate(stmtText, 200))}</div>
                    <div class="sf-col sf-col-role">
                        ${stmt.role ? `<span class="role-badge ${isRoleInDictionary(stmt.role) ? 'linked' : ''}" title="${isRoleInDictionary(stmt.role) ? 'Linked to Role Dictionary' : 'Not in Role Dictionary'}">${isRoleInDictionary(stmt.role) ? '<i data-lucide="link" style="width:12px;height:12px;margin-right:4px;"></i>' : ''}${escapeHtml(stmt.role)}</span>` : ''}
                    </div>
                    <div class="sf-col sf-col-directive">
                        <span class="sf-directive-badge ${directiveClass}">${directiveLabel}</span>
                    </div>
                    <div class="sf-col sf-col-level">
                        <span class="sf-level-badge">${level}</span>
                    </div>
                    <div class="sf-col sf-col-actions">
                        <button class="btn btn-ghost btn-xs" onclick="StatementForge.openEditPanel(StatementForge.getStatementById('${stmt.id}'))" title="Edit">
                            <i data-lucide="edit-2"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Add event listeners
        tableBody.querySelectorAll('.sf-statement-row').forEach(row => {
            // Click to select/focus
            row.addEventListener('click', function(e) {
                if (e.target.matches('input, button, button *, a')) return;

                const id = this.dataset.id;
                const idx = parseInt(this.dataset.index);
                focusedIndex = idx;

                // Toggle selection on click
                if (e.ctrlKey || e.metaKey) {
                    if (selectedIds.has(id)) {
                        selectedIds.delete(id);
                    } else {
                        selectedIds.add(id);
                    }
                } else if (e.shiftKey && focusedIndex >= 0) {
                    // Range select
                    const displayed = getDisplayedStatements();
                    const start = Math.min(focusedIndex, idx);
                    const end = Math.max(focusedIndex, idx);
                    for (let i = start; i <= end; i++) {
                        if (displayed[i]) selectedIds.add(displayed[i].id);
                    }
                } else {
                    // Single click - just focus, don't change selection
                }

                renderStatements();
                updateToolbarState();
            });

            // Double click to edit
            row.addEventListener('dblclick', function(e) {
                if (e.target.matches('input, button, button *, a')) return;
                const id = this.dataset.id;
                const stmt = statements.find(s => s.id === id);
                if (stmt) openEditPanel(stmt);
            });
        });

        // Checkbox change events
        tableBody.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', function(e) {
                e.stopPropagation();
                const id = this.dataset.id;
                if (this.checked) {
                    selectedIds.add(id);
                } else {
                    selectedIds.delete(id);
                }
                updateStats();
                updateToolbarState();
            });
        });

        // Initialize icons and sortable
        if (window.lucide) lucide.createIcons();
        setupSortable();
        updateStats();
        updateToolbarState();
    }

    // v3.0.111: Clear all filters
    function clearFilters() {
        currentFilter = 'all';
        currentSearch = '';
        const searchInput = el('sf-search-input');
        if (searchInput) searchInput.value = '';
        document.querySelectorAll('.sf-filter-chip').forEach(c => c.classList.remove('active'));
        document.querySelector('.sf-filter-chip[data-filter="all"]')?.classList.add('active');
        renderStatements();
    }

    // v3.0.111: Get statement by ID
    function getStatementById(id) {
        return statements.find(s => s.id === id);
    }
    
    // v3.0.111: Update toolbar button states
    function updateToolbarState() {
        const hasStatements = statements.length > 0;
        const hasSelection = selectedIds.size > 0;
        const hasSingleSelection = selectedIds.size === 1;
        const hasMultiSelection = selectedIds.size >= 2;
        const canUndo = undoStack.length > 0;
        const canRedo = redoStack.length > 0;

        // Export button
        const exportBtn = el('sf-btn-export');
        if (exportBtn) exportBtn.disabled = !hasStatements;

        // Undo/Redo
        const undoBtn = el('sf-btn-undo');
        const redoBtn = el('sf-btn-redo');
        if (undoBtn) undoBtn.disabled = !canUndo;
        if (redoBtn) redoBtn.disabled = !canRedo;

        // Selection-dependent buttons
        const deleteBtn = el('sf-btn-delete');
        const mergeBtn = el('sf-btn-merge');
        const splitBtn = el('sf-btn-split');
        const moveUpBtn = el('sf-btn-move-up');
        const moveDownBtn = el('sf-btn-move-down');
        const indentLeftBtn = el('sf-btn-indent-left');
        const indentRightBtn = el('sf-btn-indent-right');
        const renumberBtn = el('sf-btn-renumber');
        const viewSourceBtn = el('sf-btn-view-source');

        if (deleteBtn) deleteBtn.disabled = !hasSelection;
        if (mergeBtn) mergeBtn.disabled = !hasMultiSelection;
        if (splitBtn) splitBtn.disabled = !hasSingleSelection;
        if (moveUpBtn) moveUpBtn.disabled = !hasSelection;
        if (moveDownBtn) moveDownBtn.disabled = !hasSelection;
        if (indentLeftBtn) indentLeftBtn.disabled = !hasSelection;
        if (indentRightBtn) indentRightBtn.disabled = !hasSelection;
        if (renumberBtn) renumberBtn.disabled = !hasStatements;
        if (viewSourceBtn) viewSourceBtn.disabled = !hasSingleSelection;
    }

    // v3.0.111: Undo/Redo functionality
    function saveUndoState(description = '') {
        const state = {
            statements: JSON.parse(JSON.stringify(statements)),
            selectedIds: Array.from(selectedIds),
            description,
            timestamp: Date.now()
        };
        undoStack.push(state);
        if (undoStack.length > 100) undoStack.shift(); // Limit stack size
        redoStack = []; // Clear redo stack on new action
        updateStats();
    }

    function undo() {
        if (undoStack.length === 0) return;
        const current = {
            statements: JSON.parse(JSON.stringify(statements)),
            selectedIds: Array.from(selectedIds)
        };
        redoStack.push(current);

        const state = undoStack.pop();
        statements = state.statements;
        selectedIds = new Set(state.selectedIds);
        renderStatements();
        toast('info', `Undo: ${state.description || 'Action undone'}`);
    }

    function redo() {
        if (redoStack.length === 0) return;
        const current = {
            statements: JSON.parse(JSON.stringify(statements)),
            selectedIds: Array.from(selectedIds)
        };
        undoStack.push(current);

        const state = redoStack.pop();
        statements = state.statements;
        selectedIds = new Set(state.selectedIds);
        renderStatements();
        toast('info', 'Redo');
    }

    // v3.0.111: Navigation
    function navigateRows(direction) {
        const displayed = getDisplayedStatements();
        if (displayed.length === 0) return;

        if (focusedIndex < 0) {
            focusedIndex = direction > 0 ? 0 : displayed.length - 1;
        } else {
            focusedIndex += direction;
            if (focusedIndex < 0) focusedIndex = 0;
            if (focusedIndex >= displayed.length) focusedIndex = displayed.length - 1;
        }

        renderStatements();

        // Scroll focused row into view
        const row = document.querySelector(`.sf-statement-row[data-index="${focusedIndex}"]`);
        if (row) row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }

    function toggleFocusedSelection() {
        if (focusedIndex < 0) return;
        const displayed = getDisplayedStatements();
        if (!displayed[focusedIndex]) return;

        const id = displayed[focusedIndex].id;
        if (selectedIds.has(id)) {
            selectedIds.delete(id);
        } else {
            selectedIds.add(id);
        }
        renderStatements();
    }

    function selectAll() {
        const displayed = getDisplayedStatements();
        displayed.forEach(stmt => selectedIds.add(stmt.id));
        renderStatements();
    }

    // v3.0.111: Edit panel
    function openEditPanel(stmt) {
        if (!stmt) return;
        editingStatement = stmt;

        el('sf-edit-number').value = stmt.number || '';
        el('sf-edit-title').value = stmt.title || '';
        el('sf-edit-role').value = stmt.role || '';
        el('sf-edit-description').value = stmt.description || stmt.statement || '';
        el('sf-edit-directive').value = stmt.directive || '';

        // Set level button
        document.querySelectorAll('.sf-level-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.level) === (stmt.level || 4)) {
                btn.classList.add('active');
            }
        });

        el('sf-edit-panel')?.classList.add('open');
    }

    function closeEditPanel() {
        el('sf-edit-panel')?.classList.remove('open');
        editingStatement = null;
    }

    function saveEdit() {
        if (!editingStatement) return;

        saveUndoState('Edit statement');

        const idx = statements.findIndex(s => s.id === editingStatement.id);
        if (idx >= 0) {
            statements[idx].number = el('sf-edit-number')?.value || '';
            statements[idx].title = el('sf-edit-title')?.value || '';
            statements[idx].role = el('sf-edit-role')?.value || '';
            statements[idx].description = el('sf-edit-description')?.value || '';
            statements[idx].directive = el('sf-edit-directive')?.value || '';

            // Get level from active button
            const activeLevel = document.querySelector('.sf-level-btn.active');
            if (activeLevel) {
                statements[idx].level = parseInt(activeLevel.dataset.level);
            }

            statements[idx].modified = true;
        }

        closeEditPanel();
        renderStatements();
        toast('success', 'Statement updated');
    }

    // v3.0.111: Move statements
    function moveSelectedUp() {
        if (selectedIds.size === 0) return;
        saveUndoState('Move up');

        const ids = Array.from(selectedIds);
        const indices = ids.map(id => statements.findIndex(s => s.id === id)).filter(i => i >= 0).sort((a, b) => a - b);

        if (indices[0] === 0) return; // Already at top

        for (const idx of indices) {
            if (idx > 0) {
                [statements[idx - 1], statements[idx]] = [statements[idx], statements[idx - 1]];
            }
        }

        renderStatements();
    }

    function moveSelectedDown() {
        if (selectedIds.size === 0) return;
        saveUndoState('Move down');

        const ids = Array.from(selectedIds);
        const indices = ids.map(id => statements.findIndex(s => s.id === id)).filter(i => i >= 0).sort((a, b) => b - a);

        if (indices[0] === statements.length - 1) return; // Already at bottom

        for (const idx of indices) {
            if (idx < statements.length - 1) {
                [statements[idx], statements[idx + 1]] = [statements[idx + 1], statements[idx]];
            }
        }

        renderStatements();
    }

    // v3.0.111: Indent/Outdent
    function indentSelected() {
        if (selectedIds.size === 0) return;
        saveUndoState('Indent');

        selectedIds.forEach(id => {
            const stmt = statements.find(s => s.id === id);
            if (stmt && (stmt.level || 4) < 6) {
                stmt.level = (stmt.level || 4) + 1;
                stmt.modified = true;
            }
        });

        renderStatements();
    }

    function outdentSelected() {
        if (selectedIds.size === 0) return;
        saveUndoState('Outdent');

        selectedIds.forEach(id => {
            const stmt = statements.find(s => s.id === id);
            if (stmt && (stmt.level || 4) > 1) {
                stmt.level = (stmt.level || 4) - 1;
                stmt.modified = true;
            }
        });

        renderStatements();
    }

    // v3.0.111: Expand/Collapse
    function expandAll() {
        document.querySelectorAll('.sf-expand-btn').forEach(btn => {
            btn.classList.remove('collapsed');
        });
        // Show all rows
        document.querySelectorAll('.sf-statement-row').forEach(row => {
            row.style.display = 'flex';
        });
    }

    function collapseAll() {
        document.querySelectorAll('.sf-expand-btn').forEach(btn => {
            btn.classList.add('collapsed');
        });
        // Hide children of level 1-2 rows
        // This is a simplified version - full implementation would track parent-child relationships
    }

    // v3.0.111: Export dropdown toggle
    function toggleExportDropdown() {
        const menu = el('sf-export-menu');
        if (menu) {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        }
    }

    // v3.0.111: Modal helpers for SF sub-modals
    function showSFModal(modalId) {
        const modal = el(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.classList.add('modal-open');

            // Initialize modal-specific content
            if (modalId === 'modal-sf-renumber') {
                const count = selectedIds.size > 0 ? selectedIds.size : statements.length;
                const countEl = el('sf-renumber-count');
                if (countEl) countEl.textContent = count;
            }

            // Re-init icons
            if (window.lucide) lucide.createIcons();
        }
    }

    function closeSFModal(modalId) {
        const modal = el(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.classList.remove('modal-open');
        }
        // v4.6.1: Return to dashboard when closing main Statement Forge modal
        if (modalId === 'modal-statement-forge') {
            if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                TWR.LandingPage.show();
            }
        }
    }

    // Wrapper that uses global showModal if available, otherwise internal
    function showModal(modalId) {
        if (window.showModal && modalId !== 'modal-statement-forge') {
            window.showModal(modalId);
        } else {
            showSFModal(modalId);
        }
    }

    function closeModal(modalId) {
        if (window.closeModal) {
            window.closeModal(modalId);
        } else {
            closeSFModal(modalId);
        }
    }

    function showMergeModal() {
        if (selectedIds.size < 2) {
            toast('error', 'Select at least 2 statements to merge');
            return;
        }
        const countEl = el('sf-merge-count');
        if (countEl) countEl.textContent = selectedIds.size;
        showModal('modal-sf-merge');
    }

    function showSplitModal() {
        if (selectedIds.size !== 1) {
            toast('error', 'Select exactly 1 statement to split');
            return;
        }
        updateSplitPreview();
        showModal('modal-sf-split');
    }

    // v3.1.9: View Source Context - Opens Statement Review Mode
    function openViewSourceMode() {
        if (selectedIds.size !== 1) {
            toast('error', 'Select exactly 1 statement to view source');
            return;
        }

        const selectedId = Array.from(selectedIds)[0];
        const selectedIndex = statements.findIndex(s => s.id === selectedId);

        if (selectedIndex === -1) {
            toast('error', 'Statement not found');
            return;
        }

        // Use the StatementReviewMode if available
        if (window.TWR?.StatementReviewMode) {
            window.TWR.StatementReviewMode.openAtIndex(
                selectedIndex,
                statements,
                currentDocumentName || 'Document'
            );
        } else {
            // Fallback: show statement details in a toast
            const stmt = statements[selectedIndex];
            console.log('[StatementForge] Statement source context:', stmt);
            toast('info', `Source: ${stmt.source_section_title || stmt.section || 'Unknown section'}`);
        }
    }

    // v3.0.111: Modal confirm actions
    function confirmAddStatement() {
        const number = el('sf-add-number')?.value || '';
        const description = el('sf-add-description')?.value || '';
        const level = parseInt(el('sf-add-level')?.value || '4');
        const directive = el('sf-add-directive')?.value || '';

        if (!description.trim()) {
            toast('error', 'Description is required');
            return;
        }

        saveUndoState('Add statement');

        const newStmt = {
            id: `manual-${Date.now()}`,
            number: number,
            description: description,
            level: level,
            directive: directive,
            role: '',
            modified: true,
            source: 'manual'
        };

        // Insert after selected or at end
        if (selectedIds.size === 1) {
            const selectedId = Array.from(selectedIds)[0];
            const idx = statements.findIndex(s => s.id === selectedId);
            if (idx >= 0) {
                statements.splice(idx + 1, 0, newStmt);
            } else {
                statements.push(newStmt);
            }
        } else {
            statements.push(newStmt);
        }

        closeModal('modal-sf-add');
        // Clear form
        el('sf-add-number').value = '';
        el('sf-add-description').value = '';
        el('sf-add-level').value = '4';
        el('sf-add-directive').value = '';

        renderStatements();
        toast('success', 'Statement added');
    }

    function confirmRenumber() {
        const base = el('sf-renumber-base')?.value || '1';
        const strategy = el('sf-renumber-strategy')?.value || 'hierarchical';

        saveUndoState('Renumber statements');

        const toRenumber = selectedIds.size > 0
            ? statements.filter(s => selectedIds.has(s.id))
            : statements;

        let counters = [0, 0, 0, 0, 0, 0]; // For each level

        toRenumber.forEach((stmt, idx) => {
            const level = (stmt.level || 4) - 1;

            if (strategy === 'sequential') {
                stmt.number = `${base}.${idx + 1}`;
            } else if (strategy === 'hierarchical') {
                counters[level]++;
                // Reset lower level counters
                for (let i = level + 1; i < 6; i++) counters[i] = 0;

                const parts = [base];
                for (let i = 0; i <= level; i++) {
                    if (counters[i] > 0) parts.push(counters[i]);
                }
                stmt.number = parts.join('.');
            } else {
                // Continue - just increment from base
                stmt.number = `${base}.${idx + 1}`;
            }

            stmt.modified = true;
        });

        closeModal('modal-sf-renumber');
        renderStatements();
        toast('success', `Renumbered ${toRenumber.length} statements`);
    }

    function confirmMerge() {
        if (selectedIds.size < 2) return;

        const separator = el('sf-merge-separator')?.value || '\n\n';
        const actualSep = separator.replace(/\\n/g, '\n');

        saveUndoState('Merge statements');

        const ids = Array.from(selectedIds);
        const toMerge = statements.filter(s => ids.includes(s.id));
        const first = toMerge[0];

        // Merge descriptions
        first.description = toMerge.map(s => s.description || s.statement || '').join(actualSep);
        first.modified = true;

        // Remove other statements
        statements = statements.filter(s => s.id === first.id || !ids.includes(s.id));
        selectedIds.clear();
        selectedIds.add(first.id);

        closeModal('modal-sf-merge');
        renderStatements();
        toast('success', `Merged ${toMerge.length} statements`);
    }

    function confirmSplit() {
        if (selectedIds.size !== 1) return;

        const splitBy = el('sf-split-by')?.value || '\n\n';
        const actualSplit = splitBy.replace(/\\n/g, '\n');

        const id = Array.from(selectedIds)[0];
        const stmt = statements.find(s => s.id === id);
        if (!stmt) return;

        const text = stmt.description || stmt.statement || '';
        const parts = text.split(actualSplit).map(p => p.trim()).filter(Boolean);

        if (parts.length < 2) {
            toast('error', 'No split possible with that delimiter');
            return;
        }

        saveUndoState('Split statement');

        const idx = statements.indexOf(stmt);
        statements.splice(idx, 1);

        parts.forEach((part, i) => {
            statements.splice(idx + i, 0, {
                id: `split-${Date.now()}-${i}`,
                number: stmt.number ? `${stmt.number}.${i + 1}` : '',
                description: part,
                level: stmt.level || 4,
                directive: i === 0 ? stmt.directive : '',
                role: stmt.role,
                modified: true,
                source: 'split'
            });
        });

        selectedIds.clear();
        closeModal('modal-sf-split');
        renderStatements();
        toast('success', `Split into ${parts.length} statements`);
    }

    function updateSplitPreview() {
        const preview = el('sf-split-preview');
        if (!preview || selectedIds.size !== 1) return;

        const id = Array.from(selectedIds)[0];
        const stmt = statements.find(s => s.id === id);
        if (!stmt) {
            preview.innerHTML = '<p class="text-muted">Select a statement to see preview</p>';
            return;
        }

        const splitBy = el('sf-split-by')?.value || '\n\n';
        const actualSplit = splitBy.replace(/\\n/g, '\n');
        const text = stmt.description || stmt.statement || '';
        const parts = text.split(actualSplit).map(p => p.trim()).filter(Boolean);

        if (parts.length < 2) {
            preview.innerHTML = '<p class="text-muted">No split possible with this delimiter</p>';
        } else {
            preview.innerHTML = parts.map((part, i) =>
                `<div class="sf-split-preview-item">${i + 1}. ${escapeHtml(truncate(part, 100))}</div>`
            ).join('');
        }
    }
    
    // v3.0.111: Add manual statement (opens modal)
    function addStatement() {
        showModal('modal-sf-add');
    }

    // Update statement text (inline edit - legacy support)
    function updateStatement(element) {
        const id = element.dataset.id;
        const newText = element.textContent.trim();

        const stmt = statements.find(s => String(s.id) === id);
        if (stmt) {
            saveUndoState('Edit statement');
            stmt.description = newText;
            stmt.directive = detectDirective(newText);
            stmt.modified = true;
            toast('info', 'Statement updated');
        }
    }

    // Detect directive word in text
    function detectDirective(text) {
        const lower = text.toLowerCase();
        if (lower.includes('shall')) return 'shall';
        if (lower.includes('must')) return 'must';
        if (lower.includes('should')) return 'should';
        if (lower.includes('may')) return 'may';
        if (lower.includes('will')) return 'will';
        return '';
    }

    // Merge selected statements (shows modal)
    async function mergeSelected() {
        showMergeModal();
    }

    // Split statement (shows modal)
    function splitStatement(id) {
        selectedIds.clear();
        selectedIds.add(id);
        showSplitModal();
    }

    // Delete statement
    function deleteStatement(id) {
        if (!confirm('Delete this statement?')) return;
        saveUndoState('Delete statement');
        statements = statements.filter(s => String(s.id) !== String(id));
        selectedIds.delete(id);
        renderStatements();
        toast('success', 'Statement deleted');
    }

    // Delete selected statements
    function deleteSelected() {
        if (selectedIds.size === 0) return;
        if (!confirm(`Delete ${selectedIds.size} selected statement(s)?`)) return;

        saveUndoState('Delete statements');
        const ids = Array.from(selectedIds);
        statements = statements.filter(s => !ids.includes(s.id));
        selectedIds.clear();
        renderStatements();
        toast('success', 'Statements deleted');
    }
    
    // Export statements
    async function exportAs(format) {
        if (statements.length === 0) {
            toast('error', 'No statements to export');
            return;
        }

        // Map format to file extensions for display
        const formatLabels = {
            'nimbus_csv': 'CSV',
            'xlsx': 'Excel',
            'json': 'JSON',
            'docx': 'Word'
        };
        const formatExtensions = {
            'nimbus_csv': 'csv',
            'xlsx': 'xlsx',
            'json': 'json',
            'docx': 'docx'
        };

        showLoading(`Exporting to ${formatLabels[format] || format.toUpperCase()}...`);

        try {
            const response = await fetch(`${API_BASE}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || ''
                },
                body: JSON.stringify({
                    format: format,
                    scope: 'all',
                    source_document: window.State?.currentFilename || 'statements'
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(typeof err.error === 'string' ? err.error : err.error?.message || 'Export failed');
            }

            // Download the file
            const blob = await response.blob();
            const ext = formatExtensions[format] || format;
            const baseName = (window.State?.currentFilename || 'statements').replace(/\.[^/.]+$/, '');
            const filename = `${baseName}_statements.${ext}`;

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            toast('success', `Exported ${statements.length} statements to ${filename}`);
        } catch (error) {
            console.error('[SF] Export error:', error);
            toast('error', `Export failed: ${error.message}`);
        } finally {
            hideLoading();
        }
    }
    
    // Helper functions
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    
    function truncate(str, maxLen) {
        if (!str || str.length <= maxLen) return str;
        return str.substring(0, maxLen) + '...';
    }
    
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    
    function toast(type, message) {
        if (window.toast) {
            window.toast(type, message);
        } else {
            console.log(`[SF ${type}] ${message}`);
        }
    }
    
    function showLoading(msg) {
        if (window.showLoading) window.showLoading(msg);
    }
    
    function hideLoading() {
        if (window.hideLoading) window.hideLoading();
    }
    
    // v2.9.4 #3: Handle file upload directly in Statement Forge
    // v5.9.22: Added .txt/.md support, fresh CSRF token, better error handling
    async function handleFileUpload(inputElement) {
        const file = inputElement?.files?.[0];
        if (!file) {
            toast('error', STRINGS.errors.noFile);
            return;
        }

        // Check file type — v5.9.22: Added .txt and .md to match HTML accept attribute
        const validTypes = ['.docx', '.pdf', '.doc', '.txt', '.md'];
        const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        if (!validTypes.includes(ext)) {
            toast('error', 'Please upload a .docx, .doc, .pdf, .txt, or .md file');
            inputElement.value = '';
            return;
        }

        showLoading(`${STRINGS.loading.uploading.replace('...', '')} ${file.name}...`);

        try {
            // v5.9.22: Get fresh CSRF token (Lesson 18) to prevent stale token failures
            let csrfToken = window.State?.csrfToken || document.querySelector('meta[name="csrf-token"]')?.content || '';
            try {
                const tokenResp = await fetch('/api/version', { credentials: 'same-origin' });
                const freshCsrf = tokenResp.headers.get('X-CSRF-Token');
                if (freshCsrf) csrfToken = freshCsrf;
            } catch (e) { /* use existing token */ }

            // Upload the file
            const formData = new FormData();
            formData.append('file', file);

            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                body: formData
            });
            
            const uploadResult = await uploadResponse.json();
            
            if (!uploadResult.success) {
                throw new Error(uploadResult.error || STRINGS.errors.uploadFailed);
            }
            
            // Update global state
            if (window.State) {
                window.State.currentFilename = file.name;
                window.State.filename = file.name;
            }
            
            toast('success', `Loaded: ${file.name}`);
            
            // Now run a quick scan to get the text
            showLoading('Scanning document for statements...');
            
            const reviewResponse = await fetch('/api/review', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    options: {
                        // Minimal options for quick scan
                        check_grammar: false,
                        check_spelling: false,
                        check_acronyms: false,
                        extract_roles: false
                    }
                })
            });
            
            const reviewResult = await reviewResponse.json();
            
            if (reviewResult.success && reviewResult.data) {
                // Store text for extraction only - do NOT overwrite main review results
                // v3.0.11: Removed State.reviewResults assignment that was breaking acronym detection
                if (window.State) {
                    window.State.currentText = reviewResult.data.document_info?.text || 
                        (reviewResult.data.document_info?.paragraphs || []).map(p => p[1] || p).join('\n');
                    // Store SF-specific results separately if needed
                    window.State.sfQuickScanResults = reviewResult.data;
                }
                
                // Auto-extract statements
                await extractStatements(false);
            } else {
                toast('warning', 'Document loaded but text extraction limited');
            }
            
        } catch (error) {
            console.error('[SF] File upload error:', error);
            toast('error', `Upload failed: ${error.message}`);
        } finally {
            hideLoading();
            inputElement.value = ''; // Clear input for next upload
        }
    }
    
    // ==========================================================================
    // v3.0.41: Statement Forge → Role Mapping (Batch H)
    // ==========================================================================
    
    /**
     * Map extracted statements to detected roles.
     * Creates a bidirectional mapping showing which statements relate to which roles.
     */
    async function mapToRoles() {
        try {
            showLoading('Mapping statements to roles...');
            
            // Check prerequisites
            const statusResponse = await fetch(`${API_BASE}/role-mapping-status`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!statusResponse.ok) throw new Error(`Status check failed: ${statusResponse.status}`);

            const status = await statusResponse.json();

            if (!status.can_map) {
                let msg = 'Cannot map statements to roles: ';
                if (!status.statements_available) msg += 'No statements extracted. ';
                if (!status.roles_available) msg += 'No roles detected (run document review first).';
                toast('warning', msg);
                hideLoading();
                return null;
            }
            
            // Perform mapping
            const response = await fetch(`${API_BASE}/map-to-roles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || ''
                }
            });
            
            const result = await response.json();
            
            if (!result.success) {
                toast('error', result.error || 'Mapping failed');
                hideLoading();
                return null;
            }
            
            // Display the mapping
            displayRoleMapping(result);
            
            toast('success', `Mapped ${result.stats.mapped_statements}/${result.stats.total_statements} statements (${result.stats.coverage_percent}% coverage)`);
            hideLoading();
            
            return result;
            
        } catch (error) {
            console.error('[SF] Role mapping error:', error);
            toast('error', `Mapping failed: ${error.message}`);
            hideLoading();
            return null;
        }
    }

    /**
     * v3.0.114: Auto-map statements to roles silently after extraction.
     * Stores results in window.State.roleStatementMapping for use by Roles modal.
     */
    async function autoMapToRoles() {
        try {
            // Check if roles are available
            const statusResponse = await fetch(`${API_BASE}/role-mapping-status`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!statusResponse.ok) return null;

            const status = await statusResponse.json();

            if (!status.can_map) {
                console.log('[SF] Auto-mapping skipped: roles not available yet');
                return null;
            }

            // Perform mapping silently
            const response = await fetch(`${API_BASE}/map-to-roles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || ''
                }
            });

            const result = await response.json();

            if (result.success) {
                // Store mapping in global State for Roles modal to access
                window.State = window.State || {};
                window.State.roleStatementMapping = result;

                console.log(`[SF] Auto-mapped ${result.stats.mapped_statements}/${result.stats.total_statements} statements to roles`);

                // Update role dictionary entries with their statements
                updateRoleDictionaryWithStatements(result);

                return result;
            }
        } catch (error) {
            console.log('[SF] Auto-mapping silently failed:', error.message);
        }
        return null;
    }

    /**
     * v3.0.114: Update the role dictionary with mapped statements.
     * Adds statement data to each role so it can be displayed in the Roles modal.
     * v3.0.115: Also adds NEW roles from statements to the dictionary.
     */
    function updateRoleDictionaryWithStatements(mapping) {
        // Initialize State.roles if not present
        if (!window.State) window.State = {};
        if (!window.State.roles) window.State.roles = { roles: {} };

        const roleToStatements = mapping.role_to_statements || {};
        const roles = window.State.roles.roles || window.State.roles;
        let newRolesAdded = 0;

        // Add statements to each role (and create new roles if needed)
        for (const [roleName, stmts] of Object.entries(roleToStatements)) {
            // Find existing role in the dictionary (case-insensitive match)
            const roleKey = Object.keys(roles).find(
                k => k.toLowerCase() === roleName.toLowerCase()
            );

            if (roleKey && roles[roleKey]) {
                // Update existing role
                roles[roleKey].mapped_statements = stmts;
                roles[roleKey].statement_count = stmts.length;
            } else {
                // Create new role entry from extracted statements
                const directives = {};
                const sampleContexts = [];

                stmts.forEach(stmt => {
                    // Count directives
                    if (stmt.directive) {
                        directives[stmt.directive] = (directives[stmt.directive] || 0) + 1;
                    }
                    // Collect sample contexts
                    if (stmt.description && sampleContexts.length < 5) {
                        sampleContexts.push(stmt.description);
                    }
                });

                // Add new role to dictionary
                roles[roleName] = {
                    canonical_name: roleName,
                    frequency: stmts.length,
                    count: stmts.length,
                    source: 'statement_forge',
                    source_documents: [window.State.forgeFilename || 'Statement Forge'],
                    mapped_statements: stmts,
                    statement_count: stmts.length,
                    action_types: directives,
                    sample_contexts: sampleContexts,
                    responsibilities: stmts.map(s => s.description).slice(0, 10),
                    avg_confidence: 0.9,
                    added_from_statements: true
                };
                newRolesAdded++;
            }
        }

        // Ensure the roles object is properly structured
        if (window.State.roles && !window.State.roles.roles) {
            window.State.roles = { roles: roles };
        }

        console.log(`[SF] Updated role dictionary: ${Object.keys(roleToStatements).length} roles, ${newRolesAdded} new`);

        // Refresh adjudication if new roles were added
        if (newRolesAdded > 0 && window.TWR?.Roles?.initAdjudication) {
            console.log('[SF] Reinitializing adjudication with new roles');
            window.TWR.Roles.initAdjudication();
        }

        // Refresh roles display if modal is open
        if (document.getElementById('modal-roles')?.classList.contains('active')) {
            if (window.TWR?.Roles?.renderRolesDetails) {
                window.TWR.Roles.renderRolesDetails();
            }
            if (window.TWR?.Roles?.renderRolesOverview) {
                window.TWR.Roles.renderRolesOverview();
            }
        }
    }

    /**
     * v3.0.115: Extract roles directly from statements and add to Role Dictionary.
     * This is a fallback when API role mapping isn't available (no review run yet).
     */
    function extractRolesFromStatements() {
        if (statements.length === 0) return;

        // Initialize State.roles if not present
        if (!window.State) window.State = {};
        if (!window.State.roles) window.State.roles = { roles: {} };

        const roles = window.State.roles.roles || window.State.roles;
        const roleStatementsMap = {};

        // Collect statements by role
        statements.forEach(stmt => {
            if (stmt.role && stmt.role.trim()) {
                const roleName = stmt.role.trim();
                if (!roleStatementsMap[roleName]) {
                    roleStatementsMap[roleName] = [];
                }
                roleStatementsMap[roleName].push(stmt);
            }
        });

        let newRolesAdded = 0;

        // Add each role to the dictionary if not already present
        for (const [roleName, stmts] of Object.entries(roleStatementsMap)) {
            // Check if role already exists (case-insensitive)
            const existingKey = Object.keys(roles).find(
                k => k.toLowerCase() === roleName.toLowerCase()
            );

            if (!existingKey) {
                // Calculate directive counts
                const directives = {};
                stmts.forEach(stmt => {
                    if (stmt.directive) {
                        directives[stmt.directive] = (directives[stmt.directive] || 0) + 1;
                    }
                });

                // Create new role entry
                roles[roleName] = {
                    canonical_name: roleName,
                    frequency: stmts.length,
                    count: stmts.length,
                    source: 'statement_forge',
                    source_documents: [window.State.forgeFilename || 'Statement Forge'],
                    mapped_statements: stmts.map(s => ({
                        id: s.id,
                        number: s.number,
                        description: s.description,
                        directive: s.directive,
                        level: s.level
                    })),
                    statement_count: stmts.length,
                    action_types: directives,
                    sample_contexts: stmts.map(s => s.description).slice(0, 5),
                    responsibilities: stmts.map(s => s.description).slice(0, 10),
                    avg_confidence: 0.85,
                    added_from_statements: true
                };
                newRolesAdded++;
            } else {
                // Update existing role with statements
                if (!roles[existingKey].mapped_statements) {
                    roles[existingKey].mapped_statements = [];
                }
                const existingIds = new Set(roles[existingKey].mapped_statements.map(s => s.id));
                stmts.forEach(stmt => {
                    if (!existingIds.has(stmt.id)) {
                        roles[existingKey].mapped_statements.push({
                            id: stmt.id,
                            number: stmt.number,
                            description: stmt.description,
                            directive: stmt.directive,
                            level: stmt.level
                        });
                    }
                });
                roles[existingKey].statement_count = roles[existingKey].mapped_statements.length;
            }
        }

        if (newRolesAdded > 0) {
            console.log(`[SF] Extracted ${newRolesAdded} new roles from statements`);

            // Reinitialize adjudication with new roles
            if (window.TWR?.Roles?.initAdjudication) {
                window.TWR.Roles.initAdjudication();
            }

            // Update the role display indicator
            renderStatements();
        }
    }

    /**
     * Display role mapping results in the UI.
     * @param {Object} mapping - Mapping result from API
     */
    function displayRoleMapping(mapping) {
        const container = document.getElementById('sf-role-mapping-container');
        if (!container) {
            console.warn('[SF] Role mapping container not found');
            return;
        }
        
        const roleToStatements = mapping.role_to_statements || {};
        const stats = mapping.stats || {};
        
        // Build HTML
        let html = `
            <div class="sf-role-mapping-header">
                <h4>Role → Statement Mapping</h4>
                <span class="sf-mapping-stats">
                    ${stats.mapped_statements || 0}/${stats.total_statements || 0} statements mapped 
                    (${stats.coverage_percent || 0}% coverage)
                </span>
            </div>
            <div class="sf-role-mapping-list">
        `;
        
        const roleNames = Object.keys(roleToStatements).sort();
        
        if (roleNames.length === 0) {
            html += '<p class="sf-no-mapping">No role mappings found.</p>';
        } else {
            for (const roleName of roleNames) {
                const stmts = roleToStatements[roleName];
                const count = stmts.length;
                
                html += `
                    <div class="sf-role-mapping-item">
                        <div class="sf-role-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span class="sf-role-expand">▶</span>
                            <span class="sf-role-name">${escapeHtml(roleName)}</span>
                            <span class="sf-role-count">${count} statement${count !== 1 ? 's' : ''}</span>
                        </div>
                        <div class="sf-role-statements">
                `;
                
                if (count === 0) {
                    html += '<p class="sf-no-statements">No statements reference this role.</p>';
                } else {
                    for (const stmt of stmts) {
                        const directive = stmt.directive ? `<span class="sf-directive sf-directive-${stmt.directive}">${stmt.directive}</span>` : '';
                        html += `
                            <div class="sf-mapped-statement">
                                <span class="sf-stmt-number">${escapeHtml(stmt.number || '')}</span>
                                ${directive}
                                <span class="sf-stmt-desc">${escapeHtml(stmt.description || '')}</span>
                            </div>
                        `;
                    }
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // Show unmapped count
        const unmappedCount = (mapping.unmapped_statements || []).length;
        if (unmappedCount > 0) {
            html += `
                <div class="sf-unmapped-note">
                    <em>${unmappedCount} statement${unmappedCount !== 1 ? 's' : ''} not mapped to any role</em>
                </div>
            `;
        }
        
        html += '</div>';
        
        container.innerHTML = html;
        container.style.display = 'block';
    }
    
    // Helper for escaping HTML
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Toggle export menu helper
    function toggleExportMenu(menuId) {
        const menu = document.getElementById(menuId);
        if (menu) {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Load pre-extracted statements from server session.
     * v3.0.110: Called when modal opens to restore any auto-extracted statements.
     */
    async function loadFromSession() {
        try {
            // First check if statements are available in session
            const availResponse = await fetch(`${API_BASE}/availability`);
            const availData = await availResponse.json();

            if (availData.success && availData.statements_ready && availData.statement_count > 0) {
                console.log(`[SF] Found ${availData.statement_count} pre-extracted statements in session`);

                // Fetch the actual statements
                const stmtResponse = await fetch(`${API_BASE}/statements`);
                const stmtData = await stmtResponse.json();

                if (stmtData.success && stmtData.statements && stmtData.statements.length > 0) {
                    statements = stmtData.statements;
                    renderStatements();
                    updateStats({ total: statements.length, ...stmtData.stats });
                    updateDocumentStatus(); // Update status indicator
                    console.log(`[SF] Loaded ${statements.length} statements from session`);
                }
            } else {
                console.log('[SF] No pre-extracted statements in session');
                updateDocumentStatus(); // Update even when no statements
            }
        } catch (error) {
            console.error('[SF] Error loading statements from session:', error);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Public API
    return {
        // Core operations
        extractStatements,
        addStatement,
        updateStatement,
        mergeSelected,
        splitStatement,
        deleteStatement,
        deleteSelected,
        exportAs,
        handleFileUpload,

        // UI controls
        updateDocumentStatus,
        loadFromSession,
        openEditPanel,
        closeEditPanel,
        clearFilters,

        // v3.0.41: Role mapping
        mapToRoles,
        displayRoleMapping,

        // v3.0.111: New fullscreen features
        undo,
        redo,
        expandAll,
        collapseAll,
        moveSelectedUp,
        moveSelectedDown,
        indentSelected,
        outdentSelected,
        selectAll,
        showModal,
        closeModal,
        getStatementById,

        // State accessors
        getStatements: () => statements,
        setStatements: (stmts) => { statements = stmts; renderStatements(); },
        getSelectedIds: () => selectedIds
    };
})();

// Make globally available
window.StatementForge = StatementForge;

console.log('[TWR] Statement Forge module loaded');

// =============================================================================
// EXPORT REVIEW MODULE (v2.9.4 #22)
// =============================================================================

const ExportReview = (function() {
    'use strict';
    
    // Module state
    let issues = [];
    let reviewStatus = new Map(); // issue_id -> 'pending' | 'approved' | 'rejected'
    let filteredIndices = [];
    
    /**
     * Open the Export Review modal with issues to review
     */
    function open(issuesToReview) {
        issues = issuesToReview || [];
        reviewStatus.clear();
        
        // Initialize all as pending
        issues.forEach((issue, idx) => {
            const id = issue.issue_id || idx;
            reviewStatus.set(id, 'pending');
        });
        
        // Populate category filter
        populateCategoryFilter();
        
        // Render the list
        filterAndRender();
        
        // Update progress
        updateProgress();
        
        // Show modal
        showModal('modal-export-review');
    }
    
    /**
     * Populate the category dropdown filter
     */
    function populateCategoryFilter() {
        const select = document.getElementById('export-review-filter-category');
        if (!select) return;
        
        // Get unique categories
        const categories = [...new Set(issues.map(i => i.category).filter(Boolean))].sort();
        
        select.innerHTML = '<option value="">All</option>' +
            categories.map(cat => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`).join('');
    }
    
    /**
     * Filter and render issues based on current filter selections
     */
    function filterAndRender() {
        const severityFilter = document.getElementById('export-review-filter-severity')?.value || '';
        const categoryFilter = document.getElementById('export-review-filter-category')?.value || '';
        const statusFilter = document.getElementById('export-review-filter-status')?.value || '';
        
        filteredIndices = [];
        
        issues.forEach((issue, idx) => {
            const id = issue.issue_id || idx;
            const status = reviewStatus.get(id) || 'pending';
            
            // Apply filters
            if (severityFilter && issue.severity !== severityFilter) return;
            if (categoryFilter && issue.category !== categoryFilter) return;
            if (statusFilter && status !== statusFilter) return;
            
            filteredIndices.push(idx);
        });
        
        renderList();
    }
    
    /**
     * Render the issues list
     */
    function renderList() {
        const container = document.getElementById('export-review-list');
        if (!container) return;
        
        if (filteredIndices.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No issues match the current filters.</p></div>';
            return;
        }
        
        container.innerHTML = filteredIndices.map((idx, renderIdx) => {
            const issue = issues[idx];
            const id = issue.issue_id || idx;
            const status = reviewStatus.get(id) || 'pending';
            
            const severityClass = (issue.severity || 'info').toLowerCase();
            
            // v2.9.4.1: Add tabindex for keyboard navigation
            return `
                <div class="export-review-item ${status}" data-id="${id}" data-idx="${idx}" tabindex="0" role="listitem">
                    <div class="export-review-item-header">
                        <span class="severity-badge sev-${severityClass}">${escapeHtml(issue.severity || 'Info')}</span>
                        <span class="category">${escapeHtml(issue.category || 'General')}</span>
                        <div class="actions">
                            <button class="btn btn-sm ${status === 'approved' ? 'btn-success' : 'btn-ghost'}" 
                                    onclick="ExportReview.approve(${typeof id === 'string' ? `'${id}'` : id})" title="Approve (a)">
                                <i data-lucide="check"></i>
                            </button>
                            <button class="btn btn-sm ${status === 'rejected' ? 'btn-danger' : 'btn-ghost'}" 
                                    onclick="ExportReview.reject(${typeof id === 'string' ? `'${id}'` : id})" title="Reject (r)">
                                <i data-lucide="x"></i>
                            </button>
                        </div>
                    </div>
                    <div class="export-review-item-body">
                        <div class="message">${escapeHtml(issue.message || '')}</div>
                        ${issue.flagged_text || issue.suggestion ? `
                            <div class="context">
                                ${issue.flagged_text ? `
                                    <div>
                                        <div class="context-label">Original Text</div>
                                        <div class="context-box original">${escapeHtml(issue.flagged_text)}</div>
                                    </div>
                                ` : ''}
                                ${issue.suggestion ? `
                                    <div>
                                        <div class="context-label">Suggested Fix</div>
                                        <div class="context-box suggestion">${escapeHtml(issue.suggestion)}</div>
                                    </div>
                                ` : ''}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        // Re-initialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    /**
     * Approve an issue
     */
    function approve(id) {
        const current = reviewStatus.get(id);
        reviewStatus.set(id, current === 'approved' ? 'pending' : 'approved');
        updateItemUI(id);
        updateProgress();
    }
    
    /**
     * Reject an issue
     */
    function reject(id) {
        const current = reviewStatus.get(id);
        reviewStatus.set(id, current === 'rejected' ? 'pending' : 'rejected');
        updateItemUI(id);
        updateProgress();
    }
    
    /**
     * Update a single item's UI without re-rendering all
     */
    function updateItemUI(id) {
        const item = document.querySelector(`.export-review-item[data-id="${id}"]`);
        if (!item) return;
        
        const status = reviewStatus.get(id) || 'pending';
        item.className = `export-review-item ${status}`;
        
        // Update buttons
        const approveBtn = item.querySelector('button[title="Approve"]');
        const rejectBtn = item.querySelector('button[title="Reject"]');
        
        if (approveBtn) {
            approveBtn.className = `btn btn-sm ${status === 'approved' ? 'btn-success' : 'btn-ghost'}`;
        }
        if (rejectBtn) {
            rejectBtn.className = `btn btn-sm ${status === 'rejected' ? 'btn-danger' : 'btn-ghost'}`;
        }
    }
    
    /**
     * Approve all visible (filtered) issues
     */
    function approveAllVisible() {
        filteredIndices.forEach(idx => {
            const id = issues[idx].issue_id || idx;
            reviewStatus.set(id, 'approved');
        });
        renderList();
        updateProgress();
    }
    
    /**
     * Reject all visible (filtered) issues
     */
    function rejectAllVisible() {
        filteredIndices.forEach(idx => {
            const id = issues[idx].issue_id || idx;
            reviewStatus.set(id, 'rejected');
        });
        renderList();
        updateProgress();
    }
    
    /**
     * Update progress indicators
     */
    function updateProgress() {
        let approved = 0, rejected = 0, pending = 0;
        
        reviewStatus.forEach(status => {
            if (status === 'approved') approved++;
            else if (status === 'rejected') rejected++;
            else pending++;
        });
        
        const reviewed = approved + rejected;
        const total = issues.length;
        const percent = total > 0 ? (reviewed / total * 100) : 0;
        
        // Update progress text and bar
        const progressText = document.getElementById('export-review-progress-text');
        if (progressText) progressText.textContent = `${reviewed} of ${total} reviewed`;
        
        const progressBar = document.getElementById('export-review-progress-bar');
        if (progressBar) progressBar.style.width = `${percent}%`;
        
        // Update summary counts
        const el = (id) => document.getElementById(id);
        if (el('export-review-approved')) el('export-review-approved').textContent = approved;
        if (el('export-review-rejected')) el('export-review-rejected').textContent = rejected;
        if (el('export-review-pending')) el('export-review-pending').textContent = pending;
        if (el('export-review-approved-count')) el('export-review-approved-count').textContent = approved;
    }
    
    /**
     * Export only approved issues
     */
    async function exportApproved() {
        const approvedIssues = issues.filter((issue, idx) => {
            const id = issue.issue_id || idx;
            return reviewStatus.get(id) === 'approved';
        });
        
        if (approvedIssues.length === 0) {
            toast('warning', 'No approved issues to export');
            return;
        }
        
        closeModals();
        
        // Use the standard export flow with approved issues
        const reviewerName = document.getElementById('export-reviewer-name')?.value || 'AEGIS';
        
        setLoading(true, `Exporting ${approvedIssues.length} approved issues...`);
        
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': State.csrfToken
                },
                body: JSON.stringify({
                    issues: approvedIssues.map((issue, i) => ({ ...issue, index: i })),
                    reviewer_name: reviewerName,
                    apply_fixes: false,
                    export_type: 'docx'
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `${State.filename}_review.docx`);
                toast('success', `Exported ${approvedIssues.length} approved issues`);
            } else {
                // v2.9.4.1: Fix BUG-H02 - safe JSON parsing for error response
                try {
                    const error = await response.json();
                    toast('error', error.error || 'Export failed');
                } catch (parseErr) {
                    toast('error', `Export failed (HTTP ${response.status})`);
                }
            }
        } catch (e) {
            toast('error', 'Export failed: ' + e.message);
        } finally {
            setLoading(false);
        }
    }
    
    /**
     * Helper functions
     */
    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    
    function showModal(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('active');
            // v2.9.4.1: Add keyboard handler when modal opens
            document.addEventListener('keydown', handleKeyboard);
        }
    }
    
    function closeModals() {
        // v2.9.4.1: Remove keyboard handler when modal closes
        document.removeEventListener('keydown', handleKeyboard);
        document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
    }
    
    // v2.9.4.1: Keyboard shortcut handler for Export Review
    function handleKeyboard(e) {
        const modal = document.getElementById('modal-export-review');
        if (!modal || !modal.classList.contains('active')) return;
        
        // Get focused item
        const focused = document.activeElement;
        const item = focused?.closest('.export-review-item');
        
        if (item) {
            const id = item.dataset.id;
            const idNum = isNaN(parseInt(id)) ? id : parseInt(id);
            
            switch (e.key) {
                case 'Enter':
                case 'a':  // Approve
                    if (!e.ctrlKey && !e.metaKey) {
                        e.preventDefault();
                        approve(idNum);
                        const next = item.nextElementSibling;
                        if (next && next.classList.contains('export-review-item')) {
                            next.focus();
                            next.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }
                    }
                    break;
                case 'Delete':
                case 'Backspace':
                case 'r':  // Reject
                    if (!e.ctrlKey && !e.metaKey) {
                        e.preventDefault();
                        reject(idNum);
                        const nextItem = item.nextElementSibling;
                        if (nextItem && nextItem.classList.contains('export-review-item')) {
                            nextItem.focus();
                            nextItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }
                    }
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    const down = item.nextElementSibling;
                    if (down && down.classList.contains('export-review-item')) {
                        down.focus();
                        down.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    const up = item.previousElementSibling;
                    if (up && up.classList.contains('export-review-item')) {
                        up.focus();
                        up.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                    break;
            }
        }
        
        // Global shortcuts (Ctrl/Cmd)
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'a':  // Ctrl+A = Approve all visible
                    e.preventDefault();
                    approveAllVisible();
                    break;
                case 'Enter':  // Ctrl+Enter = Export
                    e.preventDefault();
                    exportApproved();
                    break;
            }
        }
        
        // Escape to close
        if (e.key === 'Escape') {
            closeModals();
        }
    }
    
    function toast(type, message) {
        if (window.toast) window.toast(type, message);
    }
    
    function setLoading(show, msg) {
        if (window.setLoading) window.setLoading(show, msg);
    }
    
    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    // Set up filter listeners
    document.addEventListener('DOMContentLoaded', function() {
        ['export-review-filter-severity', 'export-review-filter-category', 'export-review-filter-status'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', filterAndRender);
        });
    });
    
    // Public API
    return {
        open,
        approve,
        reject,
        approveAllVisible,
        rejectAllVisible,
        exportApproved,
        close: closeModals  // v2.9.4.1: Expose close for cleanup
    };
})();

window.ExportReview = ExportReview;

console.log('[TWR] Export Review module loaded');

// =============================================================================
// TROUBLESHOOTING SUPPORT (v2.9.4.2)
// =============================================================================
// Captures errors and user actions to create self-contained diagnostic packages
// for troubleshooting.

const AITroubleshoot = (function() {
    'use strict';
    
    let isCapturing = true;
    
    // Capture all console errors
    const originalConsoleError = console.error;
    console.error = function(...args) {
        // Call original
        originalConsoleError.apply(console, args);
        
        // Send to backend (if capturing enabled)
        if (isCapturing) {
            captureConsoleError({
                type: 'console.error',
                message: args.map(a => {
                    try {
                        return typeof a === 'object' ? JSON.stringify(a) : String(a);
                    } catch {
                        return String(a);
                    }
                }).join(' '),
                timestamp: new Date().toISOString()
            });
        }
    };
    
    // Capture unhandled errors
    window.addEventListener('error', function(event) {
        if (!isCapturing) return;
        
        captureConsoleError({
            type: 'window.error',
            message: event.message || 'Unknown error',
            source: event.filename || '',
            lineno: event.lineno || 0,
            colno: event.colno || 0,
            stack: event.error?.stack || '',
            timestamp: new Date().toISOString(),
            correlationId: window._lastCorrelationId || null
        });
    });
    
    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        if (!isCapturing) return;
        
        captureConsoleError({
            type: 'unhandledrejection',
            message: event.reason?.message || String(event.reason),
            stack: event.reason?.stack || '',
            timestamp: new Date().toISOString(),
            correlationId: window._lastCorrelationId || null
        });
    });
    
    // Send console error to backend
    function captureConsoleError(error) {
        // Include last correlation ID for backend correlation
        error.correlationId = error.correlationId || window._lastCorrelationId || null;
        
        try {
            fetch('/api/diagnostics/capture-console', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || window.CSRF_TOKEN || ''
                },
                body: JSON.stringify(error)
            }).catch(() => {}); // Silently fail - don't cause more errors
        } catch (e) {
            // Don't let diagnostic capture cause more errors
        }
    }
    
    // Log user action (call before operations that might fail)
    function logAction(action, details = {}) {
        // Include correlation ID
        details.correlationId = window._lastCorrelationId || null;
        
        try {
            // Also log locally for immediate access
            console.log(`[TWR Action] ${action}`, details);
            
            fetch('/api/diagnostics/user-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({ action, details })
            }).catch(() => {}); // Silent fail
        } catch (e) {
            // Silent fail
        }
    }
    
    // Export troubleshooting package
    async function exportPackage(format = 'json') {
        try {
            if (window.showLoading) showLoading('Generating diagnostic package...');

            const response = await fetch(`/api/diagnostics/ai-export?format=${format}`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': window.State?.csrfToken || window.CSRF_TOKEN || ''
                }
            });

            if (!response.ok) {
                throw new Error(`Export failed: ${response.status} ${response.statusText}`);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            const filename = contentDisposition?.match(/filename="?([^"]+)"?/)?.[1]
                || `TWR_DIAG_${Date.now()}.${format}`;

            // Download file
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            if (window.hideLoading) hideLoading();

            if (window.toast) {
                toast('success', 'Diagnostic package exported for troubleshooting.');
            }
            
            return filename;
        } catch (error) {
            if (window.hideLoading) hideLoading();
            console.error('[TWR] Failed to export diagnostic package:', error);
            if (window.toast) {
                toast('error', 'Failed to export diagnostics: ' + error.message);
            }
            throw error;
        }
    }
    
    // Enable/disable capturing (useful if causing issues)
    function setCapturing(enabled) {
        isCapturing = enabled;
        console.log(`[TWR] AI Troubleshoot capturing ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    // Public API
    return {
        logAction,
        exportPackage,
        captureError: captureConsoleError,
        setCapturing
    };
})();

// Make globally available
window.AITroubleshoot = AITroubleshoot;

// =============================================================================
// FETCH INTERCEPTOR FOR CORRELATION ID CAPTURE (v2.9.4.2)
// =============================================================================
// Wraps fetch to capture X-Correlation-ID from responses for error correlation

(function() {
    const originalFetch = window.fetch;
    
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            
            // Capture correlation ID from response headers
            const correlationId = response.headers.get('X-Correlation-ID');
            if (correlationId) {
                window._lastCorrelationId = correlationId;
            }
            
            return response;
        } catch (error) {
            // Still capture errors even if fetch fails
            AITroubleshoot.captureError({
                type: 'fetch_error',
                message: error.message,
                url: typeof args[0] === 'string' ? args[0] : args[0]?.url,
                correlationId: window._lastCorrelationId
            });
            throw error;
        }
    };
    
    console.log('[TWR] Fetch interceptor installed for correlation ID tracking');
})();

// =============================================================================
// INSTRUMENT KEY OPERATIONS WITH USER ACTION LOGGING
// =============================================================================

// Wrap the global handleFileUpload if it exists
(function() {
    const originalHandleFileUpload = window.handleFileUpload;
    if (typeof originalHandleFileUpload === 'function') {
        window.handleFileUpload = async function(file) {
            AITroubleshoot.logAction('file_upload_start', { 
                filename: file?.name, 
                size: file?.size,
                type: file?.type 
            });
            try {
                const result = await originalHandleFileUpload.apply(this, arguments);
                AITroubleshoot.logAction('file_upload_complete', { filename: file?.name });
                return result;
            } catch (error) {
                AITroubleshoot.logAction('file_upload_error', { 
                    filename: file?.name, 
                    error: error.message 
                });
                throw error;
            }
        };
    }
})();

// Add action logging on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Log when review button is clicked
    const reviewBtn = document.getElementById('btn-review');
    if (reviewBtn) {
        reviewBtn.addEventListener('click', function() {
            const checkers = [];
            document.querySelectorAll('[data-checker]').forEach(cb => {
                if (cb.checked) checkers.push(cb.dataset.checker);
            });
            AITroubleshoot.logAction('run_review', {
                filename: window.State?.filename,
                checkers_enabled: checkers
            });
        }, true); // Use capture phase to run before the actual handler
    }
    
    // Log when export is clicked
    const exportBtn = document.getElementById('btn-do-export');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            AITroubleshoot.logAction('export_document', {
                format: document.querySelector('input[name="export-format"]:checked')?.value,
                mode: document.querySelector('input[name="export-mode"]:checked')?.value,
                issue_count: window.State?.issues?.length || 0
            });
        }, true);
    }
    
    // Log settings changes
    document.querySelectorAll('#modal-settings input, #modal-settings select').forEach(el => {
        el.addEventListener('change', function() {
            AITroubleshoot.logAction('settings_change', {
                setting: this.id || this.name,
                value: this.type === 'checkbox' ? this.checked : this.value
            });
        });
    });
    
    // Log modal opens
    document.querySelectorAll('[onclick*="showModal"]').forEach(el => {
        el.addEventListener('click', function() {
            const match = this.getAttribute('onclick')?.match(/showModal\(['"]([^'"]+)['"]\)/);
            if (match) {
                AITroubleshoot.logAction('modal_open', { modal: match[1] });
            }
        });
    });
});

console.log('[TWR] AI Troubleshooting support loaded');

// =============================================================================
// v3.0.114: Sidebar Advanced Toggle
// =============================================================================
document.addEventListener('DOMContentLoaded', function() {
    const advancedBtn = document.getElementById('btn-toggle-advanced');
    const advancedPanel = document.getElementById('advanced-panel');

    if (advancedBtn && advancedPanel) {
        advancedBtn.addEventListener('click', function() {
            const isVisible = advancedPanel.style.display !== 'none';
            advancedPanel.style.display = isVisible ? 'none' : 'block';
            advancedBtn.classList.toggle('active', !isVisible);
        });
    }

    // Profile button selection
    document.querySelectorAll('.profile-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all profile buttons
            document.querySelectorAll('.profile-btn').forEach(b => b.classList.remove('active'));
            // Add active to clicked button
            this.classList.add('active');
        });
    });

    // Document type button selection - v4.0.2: Removed duplicate handler
    // These buttons are already handled by events.js which calls applyPreset()
    // and manages the active class. This duplicate was causing conflicts.

    // Checker category headers - toggle visibility
    document.querySelectorAll('.checker-category-header').forEach(header => {
        header.addEventListener('click', function() {
            const list = this.nextElementSibling;
            if (list && list.classList.contains('checker-list')) {
                list.style.display = list.style.display === 'none' ? 'block' : 'none';
            }
        });
    });
});

console.log('[TWR] Sidebar v3.0.114 loaded');

// =============================================================================
// v3.0.114: Diagnostic Export Handlers
// =============================================================================
document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('btn-diag-refresh');
    const exportJsonBtn = document.getElementById('btn-diag-export-json');
    const exportTxtBtn = document.getElementById('btn-diag-export-txt');
    const errorCountEl = document.getElementById('diag-error-count');
    const warningCountEl = document.getElementById('diag-warning-count');
    const requestCountEl = document.getElementById('diag-request-count');

    /**
     * Refresh diagnostic summary from server
     */
    async function refreshDiagnosticSummary() {
        try {
            // First, submit frontend logs to server
            if (window.ConsoleCapture && typeof ConsoleCapture.submitToServer === 'function') {
                try {
                    await ConsoleCapture.submitToServer();
                } catch (e) {
                    console.warn('[TWR] Could not submit frontend logs:', e);
                }
            }

            const response = await fetch('/api/diagnostics/summary');
            const data = await response.json();

            if (data.success) {
                if (errorCountEl) errorCountEl.textContent = data.error_count || 0;
                if (warningCountEl) warningCountEl.textContent = data.warning_count || 0;
                if (requestCountEl) requestCountEl.textContent = data.request_count || 0;
            }
        } catch (e) {
            console.error('[TWR] Failed to refresh diagnostic summary:', e);
        }
    }

    /**
     * Export diagnostics file
     */
    async function exportDiagnostics(format) {
        const btn = format === 'json' ? exportJsonBtn : exportTxtBtn;
        try {
            // Submit frontend logs first
            if (window.ConsoleCapture && typeof ConsoleCapture.submitToServer === 'function') {
                try {
                    await ConsoleCapture.submitToServer();
                } catch (e) {
                    console.warn('[TWR] Could not submit frontend logs:', e);
                }
            }

            // Show loading state
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i data-lucide="loader"></i> Exporting...';
            }

            // v5.0.5: Get fresh CSRF token from response header (Lesson 18: meta can be stale)
            let csrfToken = window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
            try {
                const tokenResp = await fetch('/api/version', { credentials: 'same-origin' });
                const freshCsrf = tokenResp.headers.get('X-CSRF-Token');
                if (freshCsrf) csrfToken = freshCsrf;
            } catch (csrfErr) {
                console.warn('[TWR] Could not refresh CSRF token for export:', csrfErr);
            }

            const response = await fetch('/api/diagnostics/export', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken,
                },
                body: JSON.stringify({
                    format: format,
                    include_system_info: true,
                    include_request_log: true
                }),
            });

            if (response.ok) {
                const contentType = response.headers.get('content-type') || '';
                // Check if backend returned an error JSON instead of a file
                if (contentType.includes('application/json') && format !== 'json') {
                    const data = await response.json();
                    if (!data.success) throw new Error(data.error || 'Export failed');
                }

                const blob = await response.blob();
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                const filename = `diagnostic_export_${timestamp}.${format}`;
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                if (typeof showToast === 'function') {
                    showToast('success', 'Diagnostic export downloaded');
                }
            } else {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `Export failed (${response.status})`);
            }
        } catch (e) {
            console.error('[TWR] Diagnostic export failed:', e);
            if (typeof showToast === 'function') {
                showToast('error', 'Export failed: ' + e.message);
            }
        } finally {
            // Reset button state
            if (exportJsonBtn) {
                exportJsonBtn.disabled = false;
                exportJsonBtn.innerHTML = '<i data-lucide="download"></i> Export JSON';
            }
            if (exportTxtBtn) {
                exportTxtBtn.disabled = false;
                exportTxtBtn.innerHTML = '<i data-lucide="file-text"></i> Export Text';
            }
            if (typeof refreshIcons === 'function') refreshIcons();
            else if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    // Attach event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDiagnosticSummary);
    }

    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', () => exportDiagnostics('json'));
    }

    if (exportTxtBtn) {
        exportTxtBtn.addEventListener('click', () => exportDiagnostics('txt'));
    }

    // v5.9.3: Email diagnostics via Outlook
    const emailBtn = document.getElementById('btn-diag-email');
    if (emailBtn) {
        emailBtn.addEventListener('click', () => {
            if (typeof window.emailDiagnosticsViaOutlook === 'function') {
                window.emailDiagnosticsViaOutlook();
            } else {
                showToast('error', 'Email function not available');
            }
        });
    }

    // v4.9.9: Dependency Health Check
    const healthCheckBtn = document.getElementById('btn-diag-health-check');
    if (healthCheckBtn) {
        healthCheckBtn.addEventListener('click', async () => {
            const resultsDiv = document.getElementById('health-check-results');
            const contentDiv = document.getElementById('health-check-content');
            if (!resultsDiv || !contentDiv) return;

            resultsDiv.classList.add('visible');
            resultsDiv.style.display = 'block'; // Fallback for legacy
            contentDiv.innerHTML = '<div style="display:flex;align-items:center;gap:8px;"><i data-lucide="loader" class="spin"></i> Running health check...</div>';
            if (typeof lucide !== 'undefined') lucide.createIcons();

            try {
                const resp = await fetch('/api/diagnostics/health');
                const json = await resp.json();
                if (json.success) {
                    const d = json.data;
                    const allHealthy = d.summary?.all_healthy;
                    const statusIcon = allHealthy ? 'check-circle' : 'alert-triangle';
                    const statusColor = allHealthy ? 'var(--success)' : 'var(--warning)';
                    const statusText = allHealthy ? 'All dependencies healthy' : 'Some dependencies missing';

                    let html = `<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                        <i data-lucide="${statusIcon}" style="color:${statusColor};width:20px;height:20px;"></i>
                        <strong style="color:${statusColor};">${statusText}</strong>
                        <span class="help-text" style="margin-left:auto;">${d.summary?.packages || ''} &bull; ${d.summary?.nlp_models || ''}</span>
                    </div>`;

                    // Packages table
                    html += '<div style="margin-bottom:12px;"><strong style="font-size:13px;">Python Packages</strong>';
                    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:4px;margin-top:6px;">';
                    for (const [name, info] of Object.entries(d.packages || {})) {
                        const ok = info.status === 'ok';
                        const color = ok ? 'var(--success)' : 'var(--error)';
                        const icon = ok ? 'check' : 'x';
                        const ver = ok ? `v${info.version}` : 'MISSING';
                        html += `<div style="display:flex;align-items:center;gap:6px;padding:4px 8px;font-size:12px;background:var(--bg-secondary);border-radius:4px;">
                            <i data-lucide="${icon}" style="width:14px;height:14px;color:${color};flex-shrink:0;"></i>
                            <span>${name}</span>
                            <span class="help-text" style="margin-left:auto;">${ver}</span>
                        </div>`;
                    }
                    html += '</div></div>';

                    // NLP Models table
                    html += '<div><strong style="font-size:13px;">NLP Models &amp; Data</strong>';
                    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:4px;margin-top:6px;">';
                    for (const [name, info] of Object.entries(d.nlp_models || {})) {
                        const ok = info.status === 'ok';
                        const color = ok ? 'var(--success)' : 'var(--error)';
                        const icon = ok ? 'check' : 'x';
                        const extra = info.version ? `v${info.version}` : (ok ? 'OK' : 'MISSING');
                        html += `<div style="display:flex;align-items:center;gap:6px;padding:4px 8px;font-size:12px;background:var(--bg-secondary);border-radius:4px;">
                            <i data-lucide="${icon}" style="width:14px;height:14px;color:${color};flex-shrink:0;"></i>
                            <span>${name}</span>
                            <span class="help-text" style="margin-left:auto;">${extra}</span>
                        </div>`;
                    }
                    html += '</div></div>';

                    contentDiv.innerHTML = html;
                } else {
                    contentDiv.innerHTML = `<span style="color:var(--error);">Health check failed: ${json.error?.message || 'Unknown error'}</span>`;
                }
            } catch (e) {
                contentDiv.innerHTML = `<span style="color:var(--error);">Health check error: ${e.message}</span>`;
            }
            if (typeof lucide !== 'undefined') lucide.createIcons();
        });
    }

    // Auto-refresh summary when settings modal opens
    const settingsModal = document.getElementById('modal-settings');
    if (settingsModal) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class' && settingsModal.classList.contains('active')) {
                    refreshDiagnosticSummary();
                    // v4.6.0: Load data counts for Data Management tab
                    _loadDataManagementCounts();
                }
            });
        });
        observer.observe(settingsModal, { attributes: true });
    }
});

console.log('[TWR] Diagnostic Export v3.0.114 loaded');

// v4.6.0: Load data counts for settings Data Management tab
// v5.9.22: Fixed — now populates ALL 4 stored data spans (scan history, statements, roles, learning)
async function _loadDataManagementCounts() {
    // 1. Scan History count
    try {
        const scanResp = await fetch('/api/scan-history');
        if (scanResp.ok) {
            const scanData = await scanResp.json();
            const span = document.getElementById('scan-history-count');
            if (span) {
                const scans = scanData.data?.scans || scanData.scans || [];
                const docs = scanData.data?.documents || [];
                span.textContent = `${scans.length} scans across ${docs.length || 'multiple'} documents`;
            }
        }
    } catch (e) {
        const span = document.getElementById('scan-history-count');
        if (span) span.textContent = 'No scan data';
    }
    // 2. Statement count
    try {
        const stmtResp = await fetch('/api/scan-history/statements/review-stats');
        if (stmtResp.ok) {
            const stmtData = await stmtResp.json();
            if (stmtData.success) {
                const span = document.getElementById('statement-data-count');
                if (span) {
                    const s = stmtData.data || {};
                    span.textContent = `${s.total || 0} statements (${s.reviewed || 0} reviewed, ${s.pending || 0} pending)`;
                }
            }
        }
    } catch (e) {
        const span = document.getElementById('statement-data-count');
        if (span) span.textContent = 'No statement data';
    }
    // 3. Role Dictionary count
    try {
        const roleResp = await fetch('/api/roles/dictionary');
        if (roleResp.ok) {
            const roleData = await roleResp.json();
            if (roleData.success) {
                const span = document.getElementById('role-dictionary-count');
                if (span) span.textContent = `${roleData.data?.total || roleData.data?.roles?.length || 0} roles`;
            }
        }
    } catch (e) {
        const span = document.getElementById('role-dictionary-count');
        if (span) span.textContent = 'No role data';
    }
    // 4. Learning Data count (function categories + tags)
    try {
        const tagResp = await fetch('/api/function-categories');
        if (tagResp.ok) {
            const tagData = await tagResp.json();
            const span = document.getElementById('learning-data-count');
            if (span) {
                const cats = tagData.data?.categories || tagData.categories || [];
                span.textContent = `${cats.length} function categories`;
            }
        }
    } catch (e) {
        const span = document.getElementById('learning-data-count');
        if (span) span.textContent = 'No learning data';
    }
}

// =============================================================================
// v4.0.0: Data Management Settings Handlers
// =============================================================================
// v5.0.5: Fresh CSRF helper for data management operations (Lesson 18)
async function _getFreshCsrf() {
    let token = window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
    try {
        const resp = await fetch('/api/version', { credentials: 'same-origin' });
        const fresh = resp.headers.get('X-CSRF-Token');
        if (fresh) token = fresh;
    } catch (_) {}
    return token;
}

document.addEventListener('DOMContentLoaded', function() {
    const clearHistoryBtn = document.getElementById('btn-clear-scan-history');
    const factoryResetBtn = document.getElementById('btn-factory-reset');

    // Clear Scan History
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to clear all scan history?\n\nThis cannot be undone.')) {
                return;
            }

            try {
                clearHistoryBtn.disabled = true;
                clearHistoryBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Clearing...';

                const csrfToken = await _getFreshCsrf();
                const response = await fetch('/api/scan-history/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ clear_all: true })
                });
                const result = await response.json();

                if (result.success) {
                    if (typeof window.toast === 'function') {
                        window.toast('success', result.message || 'Scan history cleared');
                    }
                    // Refresh history display if on that tab
                    if (typeof window.loadHistoryData === 'function') {
                        window.loadHistoryData();
                    }
                } else {
                    throw new Error(result.error || 'Failed to clear history');
                }
            } catch (e) {
                console.error('[TWR] Error clearing history:', e);
                if (typeof window.toast === 'function') {
                    window.toast('error', 'Failed to clear history: ' + e.message);
                }
            } finally {
                clearHistoryBtn.disabled = false;
                clearHistoryBtn.innerHTML = '<i data-lucide="trash-2"></i> Clear';
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        });
    }

    // v4.6.0: Clear Statement Data
    const clearStatementsBtn = document.getElementById('btn-clear-statements');
    if (clearStatementsBtn) {
        clearStatementsBtn.addEventListener('click', async function() {
            if (!confirm('Clear all extracted statements?\n\nScan results will be preserved but all statement data will be deleted.\nThis cannot be undone.')) {
                return;
            }
            try {
                clearStatementsBtn.disabled = true;
                clearStatementsBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Clearing...';
                const csrfToken = await _getFreshCsrf();
                const resp = await fetch('/api/data/clear-statements', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
                });
                const result = await resp.json();
                if (result.success) {
                    if (typeof showToast === 'function') showToast('success', `Cleared ${result.count || 0} statements`);
                    else if (typeof toast === 'function') toast('success', `Cleared ${result.count || 0} statements`);
                    const countSpan = document.getElementById('statement-data-count');
                    if (countSpan) countSpan.textContent = '0 statements';
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } catch (e) {
                if (typeof showToast === 'function') showToast('error', 'Failed: ' + e.message);
                else if (typeof toast === 'function') toast('error', 'Failed: ' + e.message);
            } finally {
                clearStatementsBtn.disabled = false;
                clearStatementsBtn.innerHTML = '<i data-lucide="trash-2"></i> Clear';
                if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
            }
        });
    }

    // v4.6.0: Clear Role Dictionary
    const clearRoleDictBtn = document.getElementById('btn-clear-role-dictionary');
    if (clearRoleDictBtn) {
        clearRoleDictBtn.addEventListener('click', async function() {
            if (!confirm('Clear all roles from the role dictionary?\n\nThis removes adjudicated roles, function tags, and relationships.\nThis cannot be undone.')) return;
            try {
                clearRoleDictBtn.disabled = true;
                clearRoleDictBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Clearing...';
                const csrfToken = await _getFreshCsrf();
                const resp = await fetch('/api/data/clear-roles', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
                });
                const result = await resp.json();
                if (result.success) {
                    (typeof showToast === 'function' ? showToast : toast)('success', 'Role dictionary cleared');
                    const countSpan = document.getElementById('role-dictionary-count');
                    if (countSpan) countSpan.textContent = '0 roles';
                    if (window.AEGIS?.AdjudicationLookup?.invalidate) AEGIS.AdjudicationLookup.invalidate();
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } catch (e) {
                (typeof showToast === 'function' ? showToast : toast)('error', 'Failed: ' + e.message);
            } finally {
                clearRoleDictBtn.disabled = false;
                clearRoleDictBtn.innerHTML = '<i data-lucide="trash-2"></i> Clear';
                if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
            }
        });
    }

    // v4.6.0: Clear Learning Data
    const clearLearningBtn = document.getElementById('btn-clear-learning-data');
    if (clearLearningBtn) {
        clearLearningBtn.addEventListener('click', async function() {
            if (!confirm('Clear all adaptive learning data?\n\nThis removes learned fix patterns and decision history.\nThis cannot be undone.')) return;
            try {
                clearLearningBtn.disabled = true;
                clearLearningBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Clearing...';
                const csrfToken = await _getFreshCsrf();
                // v5.9.52: Clear both legacy adaptive_learning.db AND v5.9.50 pattern files
                await fetch('/api/learning/patterns', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
                }).catch(function() {});
                const resp = await fetch('/api/data/clear-learning', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
                });
                const result = await resp.json();
                if (result.success) {
                    (typeof showToast === 'function' ? showToast : toast)('success', 'Learning data cleared');
                    const countSpan = document.getElementById('learning-data-count');
                    if (countSpan) countSpan.textContent = 'Cleared';
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } catch (e) {
                (typeof showToast === 'function' ? showToast : toast)('error', 'Failed: ' + e.message);
            } finally {
                clearLearningBtn.disabled = false;
                clearLearningBtn.innerHTML = '<i data-lucide="trash-2"></i> Clear';
                if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
            }
        });
    }

    // Factory Reset
    if (factoryResetBtn) {
        factoryResetBtn.addEventListener('click', async function() {
            if (!confirm('⚠️ FACTORY RESET\n\nThis will delete ALL user data:\n• Scan history\n• Role dictionary\n• Learning data\n• User preferences\n\nThis action cannot be undone. Are you sure?')) {
                return;
            }

            // Double confirm for destructive action
            if (!confirm('Please confirm once more:\n\nThis will completely reset AEGIS to its default state.')) {
                return;
            }

            try {
                factoryResetBtn.disabled = true;
                factoryResetBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Resetting...';

                const csrfToken = await _getFreshCsrf();
                const response = await fetch('/api/data/factory-reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    }
                });
                const result = await response.json();

                if (result.success) {
                    if (typeof window.toast === 'function') {
                        window.toast('success', 'Factory reset complete. Reloading...');
                    }
                    // Reload page after short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    throw new Error(result.error || 'Factory reset failed');
                }
            } catch (e) {
                console.error('[TWR] Factory reset error:', e);
                if (typeof window.toast === 'function') {
                    window.toast('error', 'Factory reset failed: ' + e.message);
                }
                factoryResetBtn.disabled = false;
                factoryResetBtn.innerHTML = '<i data-lucide="bomb"></i> Factory Reset';
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        });
    }
});

console.log('[TWR] Data Management v4.0.0 loaded');

// =============================================================================
// v5.9.52: Learning System Settings Tab
// =============================================================================
(function() {
    'use strict';

    var _MODULES = [
        { id: 'document_review', label: 'Document Review', icon: 'file-text', css: 'lm-review',
          desc: 'Dismissed issues, fix patterns, severity preferences' },
        { id: 'statement_forge', label: 'Statement Forge', icon: 'hammer', css: 'lm-forge',
          desc: 'Directive corrections, role assignments, deletion patterns' },
        { id: 'roles', label: 'Roles Studio', icon: 'users', css: 'lm-roles',
          desc: 'Category, deliverable, disposition, role type patterns' },
        { id: 'hyperlink_validator', label: 'Hyperlink Validator', icon: 'link-2', css: 'lm-hv',
          desc: 'Trusted domains, status overrides, headless routing' },
        { id: 'proposal_compare', label: 'Proposal Compare', icon: 'git-compare-arrows', css: 'lm-pc',
          desc: 'Category overrides, company patterns, table signatures' }
    ];

    var _statsCache = null;

    function _refreshIcons() {
        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }

    function _toast(type, msg) {
        if (typeof showToast === 'function') showToast(type, msg);
        else if (typeof toast === 'function') toast(type, msg);
    }

    async function _getCsrf() {
        if (typeof _getFreshCsrf === 'function') return _getFreshCsrf();
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    function _formatDate(iso) {
        if (!iso) return 'Never';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return 'Unknown';
            return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        } catch(e) { return 'Unknown'; }
    }

    function _isLearningEnabled() {
        var stored = localStorage.getItem('aegis-learning-enabled');
        return stored !== 'false'; // default true
    }

    function _setLearningEnabled(val) {
        localStorage.setItem('aegis-learning-enabled', val ? 'true' : 'false');
    }

    async function loadLearningStats() {
        try {
            var resp = await fetch('/api/learning/stats');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            if (data.success) {
                _statsCache = data.data;
                return data.data;
            }
        } catch(e) {
            console.warn('[TWR Learning] Failed to load stats:', e);
        }
        return { modules: {}, total_patterns: 0 };
    }

    function renderLearningTab(stats) {
        // Summary bar
        var summaryEl = document.getElementById('learning-summary-text');
        if (summaryEl) {
            var total = stats.total_patterns || 0;
            var activeCount = 0;
            Object.values(stats.modules || {}).forEach(function(m) {
                if ((m.total || 0) > 0) activeCount++;
            });
            if (total === 0) {
                summaryEl.textContent = 'No patterns learned yet. AEGIS will learn from your corrections as you work.';
            } else {
                summaryEl.textContent = total + ' pattern' + (total !== 1 ? 's' : '') +
                    ' across ' + activeCount + ' module' + (activeCount !== 1 ? 's' : '');
            }
        }

        // Toggle
        var toggle = document.getElementById('settings-learning-enabled');
        if (toggle) toggle.checked = _isLearningEnabled();

        // Module cards
        var grid = document.getElementById('learning-modules-grid');
        if (!grid) return;
        grid.innerHTML = '';

        _MODULES.forEach(function(mod) {
            var mStats = (stats.modules || {})[mod.id] || { total: 0 };
            var count = mStats.total || 0;
            var isActive = count > 0;
            var lastUpdated = mStats.last_updated || '';

            var card = document.createElement('div');
            card.className = 'learning-module-card' + (isActive ? '' : ' lm-empty');
            card.innerHTML =
                '<div class="lm-header">' +
                    '<div class="lm-icon-wrap ' + mod.css + '"><i data-lucide="' + mod.icon + '"></i></div>' +
                    '<div class="lm-title-group">' +
                        '<div class="lm-title">' + mod.label + '</div>' +
                        '<div class="lm-status ' + (isActive ? 'lm-active' : '') + '">' +
                            (isActive ? count + ' pattern' + (count !== 1 ? 's' : '') + ' learned' : 'No patterns yet') +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="lm-stats">' +
                    (isActive ? '<div class="lm-stat"><i data-lucide="clock"></i> ' + _formatDate(lastUpdated) + '</div>' : '') +
                '</div>' +
                '<div class="lm-actions">' +
                    '<button class="btn-sm" data-lm-action="view" data-lm-id="' + mod.id + '" data-lm-label="' + mod.label + '"' +
                        (isActive ? '' : ' disabled') + '>' +
                        '<i data-lucide="eye"></i> View' +
                    '</button>' +
                    '<button class="btn-sm" data-lm-action="export" data-lm-id="' + mod.id + '"' +
                        (isActive ? '' : ' disabled') + '>' +
                        '<i data-lucide="download"></i> Export' +
                    '</button>' +
                    '<button class="btn-sm btn-sm-danger" data-lm-action="clear" data-lm-id="' + mod.id + '" data-lm-label="' + mod.label + '"' +
                        (isActive ? '' : ' disabled') + '>' +
                        '<i data-lucide="trash-2"></i> Clear' +
                    '</button>' +
                '</div>';
            grid.appendChild(card);
        });
        _refreshIcons();
    }

    // Action handlers
    async function viewPatterns(moduleId, label) {
        var modal = document.getElementById('modal-learning-viewer');
        var nameEl = document.getElementById('learning-viewer-module-name');
        var contentEl = document.getElementById('learning-viewer-content');
        if (!modal || !contentEl) return;

        if (nameEl) nameEl.textContent = label + ' Patterns';
        contentEl.textContent = 'Loading...';
        modal.classList.add('active');
        _refreshIcons();

        try {
            var resp = await fetch('/api/learning/patterns/' + moduleId);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            if (data.success) {
                contentEl.textContent = JSON.stringify(data.data, null, 2);
            } else {
                contentEl.textContent = 'Error: ' + (data.error || 'Unknown');
            }
        } catch(e) {
            contentEl.textContent = 'Error loading patterns: ' + e.message;
        }
    }

    function exportPatterns(moduleId) {
        window.open('/api/learning/export/' + moduleId, '_blank');
    }

    function exportAllPatterns() {
        window.open('/api/learning/export', '_blank');
    }

    async function clearPatterns(moduleId, label) {
        if (!confirm('Clear all learned patterns for ' + label + '?\n\nThis cannot be undone.')) return;
        try {
            var csrf = await _getCsrf();
            var resp = await fetch('/api/learning/patterns/' + moduleId, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }
            });
            var result = await resp.json();
            if (result.success) {
                _toast('success', result.message || 'Patterns cleared');
                var stats = await loadLearningStats();
                renderLearningTab(stats);
            } else {
                throw new Error(result.error || 'Failed');
            }
        } catch(e) {
            _toast('error', 'Failed to clear patterns: ' + e.message);
        }
    }

    async function clearAllPatterns() {
        if (!confirm('Clear ALL learning data across all modules?\n\nThis removes all learned patterns from every module.\nThis cannot be undone.')) return;
        if (!confirm('Please confirm: Clear all learned patterns?')) return;
        try {
            var csrf = await _getCsrf();
            var resp = await fetch('/api/learning/patterns', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }
            });
            var result = await resp.json();
            if (result.success) {
                _toast('success', 'Cleared ' + (result.cleared || []).length + ' module(s)');
                var stats = await loadLearningStats();
                renderLearningTab(stats);
            } else {
                throw new Error(result.error || 'Failed');
            }
        } catch(e) {
            _toast('error', 'Failed to clear all patterns: ' + e.message);
        }
    }

    // Event delegation for module card buttons
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('[data-lm-action]');
        if (!btn || btn.disabled) return;
        var action = btn.getAttribute('data-lm-action');
        var moduleId = btn.getAttribute('data-lm-id');
        var label = btn.getAttribute('data-lm-label') || moduleId;

        if (action === 'view') viewPatterns(moduleId, label);
        else if (action === 'export') exportPatterns(moduleId);
        else if (action === 'clear') clearPatterns(moduleId, label);
    });

    // Global action buttons
    document.addEventListener('DOMContentLoaded', function() {
        var exportAllBtn = document.getElementById('btn-learning-export-all');
        if (exportAllBtn) {
            exportAllBtn.addEventListener('click', function() { exportAllPatterns(); });
        }
        var clearAllBtn = document.getElementById('btn-learning-clear-all');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function() { clearAllPatterns(); });
        }
        // Learning enabled toggle
        var toggle = document.getElementById('settings-learning-enabled');
        if (toggle) {
            toggle.checked = _isLearningEnabled();
            toggle.addEventListener('change', function() {
                var enabled = this.checked;
                _setLearningEnabled(enabled);
                // Persist to backend config.json so Python learners can check
                fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    body: JSON.stringify({ learningEnabled: enabled })
                }).catch(function(e) { console.warn('[TWR Learning] Failed to persist toggle:', e); });
                _toast('success', 'Pattern learning ' + (enabled ? 'enabled' : 'disabled'));
            });
        }
    });

    // Load data when Learning tab is activated
    document.addEventListener('click', function(e) {
        var tab = e.target.closest('.settings-tab[data-tab="learning"]');
        if (tab) {
            loadLearningStats().then(function(stats) {
                renderLearningTab(stats);
            });
        }
    });

    // Expose for external use
    window._loadLearningTab = function() {
        loadLearningStats().then(function(stats) {
            renderLearningTab(stats);
        });
    };

    // Also expose learning enabled check for learner modules
    window.isAEGISLearningEnabled = _isLearningEnabled;

    console.log('[TWR] Learning System Settings v5.9.52 loaded');
})();
