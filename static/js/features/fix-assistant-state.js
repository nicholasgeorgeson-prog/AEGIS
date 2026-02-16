// v3.0.97: Fix Assistant v2 - Complete State Management
// WP5a + WP5b: Decisions, Undo/Redo, Navigation, Groups, Search, Filter, Persistence, Statistics

const FixAssistantState = (function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE STATE
    // ═══════════════════════════════════════════════════════════════════════════

    let initialized = false;
    let fixes = [];
    let fixGroups = [];
    let groupMap = new Map();           // groupId → group object
    let fixToGroupMap = new Map();      // fixIndex → group object
    let decisions = new Map();          // index → { decision, note, timestamp }
    let history = { past: [], future: [] };
    let currentIndex = 0;
    let navigationMode = 'sequential';
    let navigationOrder = [];
    let options = {};

    // WP5b additions
    let searchQuery = '';
    let filters = {
        category: null,     // string or null
        severity: null,     // string or null
        status: null,       // 'pending' | 'accepted' | 'rejected' | null
        tier: null          // 'safe' | 'review' | 'manual' | null
    };
    let documentId = null;
    let sessionStartTime = Date.now();
    let lastSaveTime = null;

    const listeners = {
        change: [],
        decision: [],
        navigate: []
    };

    const MAX_HISTORY = 100;
    const SEVERITY_ORDER = { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4 };

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Utilities
    // ═══════════════════════════════════════════════════════════════════════════

    function log(...args) {
        console.log('[TWR FAState]', ...args);
    }

    function warn(...args) {
        console.warn('[TWR FAState]', ...args);
    }

    function error(...args) {
        console.error('[TWR FAState]', ...args);
    }

    function validateIndex(index) {
        if (typeof index !== 'number' || !Number.isInteger(index)) {
            warn('Invalid index type:', typeof index);
            return false;
        }
        if (index < 0 || index >= fixes.length) {
            warn('Index out of bounds:', index, '(max:', fixes.length - 1 + ')');
            return false;
        }
        return true;
    }

    function requireInitialized(methodName) {
        if (!initialized) {
            error(`${methodName}() called before init()`);
            return false;
        }
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Events
    // ═══════════════════════════════════════════════════════════════════════════

    function emit(event, data) {
        if (!listeners[event]) return;
        listeners[event].forEach(cb => {
            try {
                cb(data);
            } catch (e) {
                error('Listener error on', event + ':', e);
            }
        });
    }

    function subscribe(event, callback) {
        if (!listeners[event]) {
            warn('Unknown event type:', event);
            return () => {};
        }
        if (typeof callback !== 'function') {
            warn('Callback must be a function');
            return () => {};
        }
        listeners[event].push(callback);
        return () => {
            const idx = listeners[event].indexOf(callback);
            if (idx > -1) listeners[event].splice(idx, 1);
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - History
    // ═══════════════════════════════════════════════════════════════════════════

    function pushHistory(action) {
        history.past.push({ ...action, timestamp: Date.now() });
        history.future = [];  // Clear redo stack on new action
        if (history.past.length > MAX_HISTORY) {
            history.past.shift();
        }
    }

    function restoreState(idx, prevState) {
        if (prevState) {
            decisions.set(idx, prevState);
        } else {
            decisions.delete(idx);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Decisions
    // ═══════════════════════════════════════════════════════════════════════════

    function makeDecision(index, decision, note = '', recordHistory = true) {
        const prevState = decisions.get(index) || null;
        const newState = { decision, note, timestamp: Date.now() };

        decisions.set(index, newState);

        if (recordHistory) {
            pushHistory({
                type: decision === 'accepted' ? 'accept' : 'reject',
                index,
                prevState
            });
        }

        emit('decision', { type: decision, index, decision: newState, note });
        emit('change', { type: 'decision', index, fix: fixes[index], decision: newState });
    }

    function makeBulkDecision(indices, decision, note = '', actionType) {
        const prevStates = {};
        indices.forEach(idx => {
            prevStates[idx] = decisions.get(idx) || null;
        });

        const timestamp = Date.now();
        indices.forEach(idx => {
            decisions.set(idx, { decision, note, timestamp });
        });

        pushHistory({
            type: actionType,
            indices: [...indices],
            prevStates
        });

        indices.forEach(idx => {
            emit('decision', { type: decision, index: idx, decision: decisions.get(idx), note });
        });
        emit('change', { type: 'bulk_decision', indices, decision });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Navigation
    // ═══════════════════════════════════════════════════════════════════════════

    function computeNavigationOrder(mode) {
        const indices = fixes.map((_, i) => i);

        switch (mode) {
            case 'sequential':
                navigationOrder = indices;
                break;

            case 'severity':
                navigationOrder = [...indices].sort((a, b) => {
                    const sevA = SEVERITY_ORDER[fixes[a].severity] ?? 5;
                    const sevB = SEVERITY_ORDER[fixes[b].severity] ?? 5;
                    if (sevA !== sevB) return sevA - sevB;
                    return a - b;  // Stable sort by index
                });
                break;

            case 'category':
                navigationOrder = [...indices].sort((a, b) => {
                    const catA = (fixes[a].category || '').toLowerCase();
                    const catB = (fixes[b].category || '').toLowerCase();
                    const cmp = catA.localeCompare(catB);
                    if (cmp !== 0) return cmp;
                    return a - b;  // Stable sort by index
                });
                break;

            case 'page':
                navigationOrder = [...indices].sort((a, b) => {
                    const pageA = fixes[a].page || 0;
                    const pageB = fixes[b].page || 0;
                    if (pageA !== pageB) return pageA - pageB;
                    return a - b;  // Stable sort by index
                });
                break;

            default:
                warn('Unknown navigation mode:', mode);
                navigationOrder = indices;
        }

        return navigationOrder;
    }

    function findPositionInOrder(fixIndex) {
        return navigationOrder.indexOf(fixIndex);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Groups
    // ═══════════════════════════════════════════════════════════════════════════

    function buildGroupMaps() {
        groupMap.clear();
        fixToGroupMap.clear();

        fixGroups.forEach(group => {
            groupMap.set(group.group_id, group);
            (group.fix_indices || []).forEach(idx => {
                fixToGroupMap.set(idx, group);
            });
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS - Search & Filter (WP5b)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Check if a fix matches the current search query
     * @param {Object} fix
     * @returns {boolean}
     */
    function matchesSearch(fix) {
        if (!searchQuery) return true;
        
        const q = searchQuery.toLowerCase().trim();
        if (!q) return true;
        
        const searchable = [
            fix.flagged_text,
            fix.suggestion,
            fix.message,
            fix.context,
            fix.category
        ].filter(Boolean).join(' ').toLowerCase();
        
        return searchable.includes(q);
    }

    /**
     * Check if a fix matches current filters
     * @param {Object} fix
     * @param {number} index
     * @returns {boolean}
     */
    function matchesFilters(fix, index) {
        // Category filter
        if (filters.category && fix.category !== filters.category) {
            return false;
        }
        
        // Severity filter
        if (filters.severity && fix.severity !== filters.severity) {
            return false;
        }
        
        // Tier filter
        if (filters.tier && fix.confidence_tier !== filters.tier) {
            return false;
        }
        
        // Status filter
        if (filters.status) {
            const decision = decisions.get(index);
            const status = decision ? decision.decision : 'pending';
            
            if (filters.status === 'pending' && decision) return false;
            if (filters.status === 'accepted' && status !== 'accepted') return false;
            if (filters.status === 'rejected' && status !== 'rejected') return false;
        }
        
        return true;
    }

    /**
     * Get localStorage key for a document.
     * v3.0.116 (BUG-M05): Now uses a unique identifier to prevent key collision
     * when the same filename is reviewed multiple times.
     * @param {string} docId - The document identifier
     * @returns {string}
     */
    function getStorageKey(docId) {
        return `twr_fav2_${docId || documentId}`;
    }

    /**
     * Generate a unique document ID from file metadata to prevent localStorage key collisions.
     * v3.0.116 (BUG-M05): Uses filename + file size + upload timestamp hash.
     * @param {string} filename - The document filename
     * @param {number} fileSize - The file size in bytes
     * @param {number} uploadTimestamp - The upload timestamp (optional, uses current time if not provided)
     * @returns {string} A unique document identifier
     */
    function generateDocumentId(filename, fileSize, uploadTimestamp) {
        // Use provided timestamp or current time
        const timestamp = uploadTimestamp || Date.now();

        // Create a simple hash from the combination
        const raw = `${filename}_${fileSize || 0}_${timestamp}`;

        // Simple string hash (djb2 algorithm) - fast and good distribution
        let hash = 5381;
        for (let i = 0; i < raw.length; i++) {
            hash = ((hash << 5) + hash) + raw.charCodeAt(i);
            hash = hash & hash; // Convert to 32-bit integer
        }

        // Convert to hex and combine with sanitized filename for readability
        const hashHex = Math.abs(hash).toString(16);
        const safeName = filename.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);

        return `${safeName}_${hashHex}`;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Initialization
    // ═══════════════════════════════════════════════════════════════════════════

    function init(fixesArray, groups = [], opts = {}) {
        if (!Array.isArray(fixesArray)) {
            error('init() requires an array of fixes');
            return false;
        }

        fixes = fixesArray;
        fixGroups = Array.isArray(groups) ? groups : [];
        options = opts || {};
        decisions.clear();
        history = { past: [], future: [] };
        currentIndex = 0;
        navigationMode = 'sequential';
        
        // WP5b: Reset search/filter state
        searchQuery = '';
        filters = { category: null, severity: null, status: null, tier: null };
        sessionStartTime = Date.now();

        buildGroupMaps();
        navigationOrder = computeNavigationOrder(navigationMode);

        initialized = true;
        log('Initialized with', fixes.length, 'fixes and', fixGroups.length, 'groups');

        if (typeof options.onReady === 'function') {
            try {
                options.onReady();
            } catch (e) {
                error('onReady callback error:', e);
            }
        }

        emit('change', { type: 'init', fixCount: fixes.length, groupCount: fixGroups.length });
        return true;
    }

    function reset() {
        fixes = [];
        fixGroups = [];
        groupMap.clear();
        fixToGroupMap.clear();
        decisions.clear();
        history = { past: [], future: [] };
        currentIndex = 0;
        navigationMode = 'sequential';
        navigationOrder = [];
        options = {};
        
        // WP5b: Reset search/filter state
        searchQuery = '';
        filters = { category: null, severity: null, status: null, tier: null };
        documentId = null;
        sessionStartTime = Date.now();
        lastSaveTime = null;
        
        initialized = false;

        log('State reset');
        emit('change', { type: 'reset' });
    }

    /**
     * v3.0.100: Cleanup event listeners to prevent memory leaks (ISSUE-007)
     * Call this when the Fix Assistant modal is closed to clear all subscriptions.
     */
    function cleanup() {
        // Clear all event listener arrays
        listeners.change = [];
        listeners.decision = [];
        listeners.navigate = [];
        
        log('Event listeners cleared');
    }

    function isInitialized() {
        return initialized;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Decisions
    // ═══════════════════════════════════════════════════════════════════════════

    function accept(index, note = '') {
        if (!requireInitialized('accept')) return;
        if (!validateIndex(index)) return;
        makeDecision(index, 'accepted', note);
        log('Accepted fix', index);
    }

    function reject(index, note = '') {
        if (!requireInitialized('reject')) return;
        if (!validateIndex(index)) return;
        makeDecision(index, 'rejected', note);
        log('Rejected fix', index);
    }

    function clearDecision(index) {
        if (!requireInitialized('clearDecision')) return;
        if (!validateIndex(index)) return;

        const prevState = decisions.get(index) || null;
        if (!prevState) {
            log('Fix', index, 'already pending');
            return;
        }

        decisions.delete(index);
        pushHistory({ type: 'clear', index, prevState });

        emit('decision', { type: 'cleared', index, decision: null, note: '' });
        emit('change', { type: 'decision', index, fix: fixes[index], decision: null });
        log('Cleared decision for fix', index);
    }

    function getDecision(index) {
        if (!requireInitialized('getDecision')) return null;
        if (!validateIndex(index)) return null;
        return decisions.get(index) || null;
    }

    function getAllDecisions() {
        if (!requireInitialized('getAllDecisions')) return new Map();
        return new Map(decisions);
    }

    function setNote(index, note) {
        if (!requireInitialized('setNote')) return;
        if (!validateIndex(index)) return;

        const current = decisions.get(index);
        if (!current) {
            warn('Cannot set note on pending fix', index);
            return;
        }

        const prevState = { ...current };
        const newNote = String(note || '');
        current.note = newNote;
        current.timestamp = Date.now();

        pushHistory({ type: 'set_note', index, prevState, newNote });
        emit('change', { type: 'note', index, fix: fixes[index], decision: current });
        log('Updated note for fix', index);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Undo / Redo
    // ═══════════════════════════════════════════════════════════════════════════

    function undo() {
        if (!requireInitialized('undo')) return false;
        if (history.past.length === 0) return false;

        const action = history.past.pop();

        if (action.type === 'accept' || action.type === 'reject' || action.type === 'clear') {
            restoreState(action.index, action.prevState);
            emit('decision', {
                type: action.prevState?.decision || 'cleared',
                index: action.index,
                decision: action.prevState,
                note: action.prevState?.note || ''
            });
        } else if (action.type === 'set_note') {
            restoreState(action.index, action.prevState);
        } else if (action.indices && action.prevStates) {
            // Bulk operation (group or tier)
            Object.entries(action.prevStates).forEach(([idx, prevState]) => {
                restoreState(parseInt(idx), prevState);
            });
        }

        history.future.push(action);
        emit('change', { type: 'undo', action });
        log('Undo:', action.type);
        return true;
    }

    function redo() {
        if (!requireInitialized('redo')) return false;
        if (history.future.length === 0) return false;

        const action = history.future.pop();
        const timestamp = Date.now();

        if (action.type === 'accept' || action.type === 'reject') {
            const decision = action.type === 'accept' ? 'accepted' : 'rejected';
            decisions.set(action.index, { decision, note: '', timestamp });
            emit('decision', { type: decision, index: action.index, decision: decisions.get(action.index), note: '' });
        } else if (action.type === 'clear') {
            decisions.delete(action.index);
            emit('decision', { type: 'cleared', index: action.index, decision: null, note: '' });
        } else if (action.type === 'set_note') {
            const current = decisions.get(action.index);
            if (current) {
                current.note = action.newNote;
                current.timestamp = timestamp;
            }
        } else if (action.indices && action.prevStates) {
            // Bulk operation - determine decision from action type
            const decision = action.type.includes('accept') ? 'accepted' : 'rejected';
            action.indices.forEach(idx => {
                decisions.set(idx, { decision, note: '', timestamp });
            });
        }

        history.past.push(action);
        emit('change', { type: 'redo', action });
        log('Redo:', action.type);
        return true;
    }

    function canUndo() {
        return initialized && history.past.length > 0;
    }

    function canRedo() {
        return initialized && history.future.length > 0;
    }

    function getHistory() {
        return {
            past: [...history.past],
            future: [...history.future]
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Navigation
    // ═══════════════════════════════════════════════════════════════════════════

    function setNavigationMode(mode) {
        if (!requireInitialized('setNavigationMode')) return;

        const validModes = ['sequential', 'severity', 'category', 'page'];
        if (!validModes.includes(mode)) {
            warn('Invalid navigation mode:', mode);
            return;
        }

        navigationMode = mode;
        navigationOrder = computeNavigationOrder(mode);
        log('Navigation mode set to:', mode);
        emit('change', { type: 'navigation_mode', mode });
    }

    function getNavigationMode() {
        return navigationMode;
    }

    function getNavigationOrder() {
        if (!requireInitialized('getNavigationOrder')) return [];
        return [...navigationOrder];
    }

    function getCurrentIndex() {
        return currentIndex;
    }

    function getCurrentFix() {
        if (!requireInitialized('getCurrentFix')) return null;
        if (currentIndex < 0 || currentIndex >= fixes.length) return null;
        return fixes[currentIndex];
    }

    function goToNext(skipDecided = true) {
        if (!requireInitialized('goToNext')) return false;
        if (navigationOrder.length === 0) return false;

        const currentPos = findPositionInOrder(currentIndex);
        for (let i = currentPos + 1; i < navigationOrder.length; i++) {
            const idx = navigationOrder[i];
            if (skipDecided && decisions.has(idx)) continue;
            return goToIndex(idx);
        }

        log('No more fixes in navigation order');
        return false;
    }

    function goToPrevious(skipDecided = false) {
        if (!requireInitialized('goToPrevious')) return false;
        if (navigationOrder.length === 0) return false;

        const currentPos = findPositionInOrder(currentIndex);
        for (let i = currentPos - 1; i >= 0; i--) {
            const idx = navigationOrder[i];
            if (skipDecided && decisions.has(idx)) continue;
            return goToIndex(idx);
        }

        log('At beginning of navigation order');
        return false;
    }

    function goToIndex(index) {
        if (!requireInitialized('goToIndex')) return false;
        if (!validateIndex(index)) return false;

        const fromIndex = currentIndex;
        currentIndex = index;

        emit('navigate', { fromIndex, toIndex: index, fix: fixes[index] });
        emit('change', { type: 'navigate', fromIndex, toIndex: index, currentIndex: index, fix: fixes[index] });
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Groups
    // ═══════════════════════════════════════════════════════════════════════════

    function getGroups() {
        if (!requireInitialized('getGroups')) return [];
        return [...fixGroups];
    }

    function acceptGroup(groupId, note = '') {
        if (!requireInitialized('acceptGroup')) return;
        const group = groupMap.get(groupId);
        if (!group) {
            warn('Group not found:', groupId);
            return;
        }

        const indices = group.fix_indices || [];
        if (indices.length === 0) return;

        makeBulkDecision(indices, 'accepted', note, 'accept_group');
        log('Accepted group', groupId, '(' + indices.length + ' fixes)');
    }

    function rejectGroup(groupId, note = '') {
        if (!requireInitialized('rejectGroup')) return;
        const group = groupMap.get(groupId);
        if (!group) {
            warn('Group not found:', groupId);
            return;
        }

        const indices = group.fix_indices || [];
        if (indices.length === 0) return;

        makeBulkDecision(indices, 'rejected', note, 'reject_group');
        log('Rejected group', groupId, '(' + indices.length + ' fixes)');
    }

    function getGroupForFix(fixIndex) {
        if (!requireInitialized('getGroupForFix')) return null;
        if (!validateIndex(fixIndex)) return null;
        return fixToGroupMap.get(fixIndex) || null;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Bulk Operations
    // ═══════════════════════════════════════════════════════════════════════════

    function acceptByTier(tier) {
        if (!requireInitialized('acceptByTier')) return;
        const validTiers = ['safe', 'review', 'manual'];
        if (!validTiers.includes(tier)) {
            warn('Invalid tier:', tier);
            return;
        }

        const indices = fixes
            .map((f, i) => ({ fix: f, index: i }))
            .filter(({ fix, index }) => fix.confidence_tier === tier && !decisions.has(index))
            .map(({ index }) => index);

        if (indices.length === 0) {
            log('No pending fixes in tier:', tier);
            return;
        }

        makeBulkDecision(indices, 'accepted', '', 'accept_bulk');
        log('Accepted', indices.length, 'fixes in tier:', tier);
    }

    function acceptAllPending() {
        if (!requireInitialized('acceptAllPending')) return;

        const indices = fixes
            .map((_, i) => i)
            .filter(i => !decisions.has(i));

        if (indices.length === 0) {
            log('No pending fixes to accept');
            return;
        }

        makeBulkDecision(indices, 'accepted', '', 'accept_bulk');
        log('Accepted all', indices.length, 'pending fixes');
    }

    function rejectAllPending() {
        if (!requireInitialized('rejectAllPending')) return;

        const indices = fixes
            .map((_, i) => i)
            .filter(i => !decisions.has(i));

        if (indices.length === 0) {
            log('No pending fixes to reject');
            return;
        }

        makeBulkDecision(indices, 'rejected', '', 'reject_bulk');
        log('Rejected all', indices.length, 'pending fixes');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Search & Filter (WP5b)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Set search query (searches flagged_text, suggestion, message, context, category)
     * @param {string} query
     */
    function setSearchQuery(query) {
        const oldQuery = searchQuery;
        searchQuery = String(query || '');
        
        if (oldQuery !== searchQuery) {
            // Recompute navigation order if filtering affects it
            computeNavigationOrder(navigationMode);
            emit('change', { type: 'search', query: searchQuery });
        }
    }

    /**
     * Get current search query
     * @returns {string}
     */
    function getSearchQuery() {
        return searchQuery;
    }

    /**
     * Set filters (partial update supported)
     * @param {Object} newFilters - { category?, severity?, status?, tier? }
     */
    function setFilters(newFilters) {
        const oldFilters = { ...filters };
        
        if (newFilters.hasOwnProperty('category')) {
            filters.category = newFilters.category || null;
        }
        if (newFilters.hasOwnProperty('severity')) {
            filters.severity = newFilters.severity || null;
        }
        if (newFilters.hasOwnProperty('status')) {
            filters.status = newFilters.status || null;
        }
        if (newFilters.hasOwnProperty('tier')) {
            filters.tier = newFilters.tier || null;
        }
        
        // Check if anything actually changed
        const changed = Object.keys(filters).some(k => filters[k] !== oldFilters[k]);
        
        if (changed) {
            computeNavigationOrder(navigationMode);
            emit('change', { type: 'filter', filters: { ...filters } });
        }
    }

    /**
     * Get current filters
     * @returns {Object}
     */
    function getFilters() {
        return { ...filters };
    }

    /**
     * Clear all filters and search
     */
    function clearFilters() {
        const hadFilters = searchQuery || 
            filters.category || filters.severity || 
            filters.status || filters.tier;
        
        searchQuery = '';
        filters = { category: null, severity: null, status: null, tier: null };
        
        if (hadFilters) {
            computeNavigationOrder(navigationMode);
            emit('change', { type: 'clearFilters' });
        }
    }

    /**
     * Get fix indices matching current search and filters
     * @returns {Array<number>}
     */
    function getFilteredIndices() {
        return fixes
            .map((fix, index) => ({ fix, index }))
            .filter(({ fix, index }) => matchesSearch(fix) && matchesFilters(fix, index))
            .map(({ index }) => index);
    }

    /**
     * Get count of filtered fixes
     * @returns {number}
     */
    function getFilteredCount() {
        return getFilteredIndices().length;
    }

    /**
     * Get unique categories from all fixes (for filter dropdown)
     * @returns {Array<string>}
     */
    function getCategories() {
        const categories = new Set();
        fixes.forEach(fix => {
            if (fix.category) categories.add(fix.category);
        });
        return Array.from(categories).sort();
    }

    /**
     * Get unique severities from all fixes
     * @returns {Array<string>}
     */
    function getSeverities() {
        const severities = new Set();
        fixes.forEach(fix => {
            if (fix.severity) severities.add(fix.severity);
        });
        // Sort by severity level if possible
        const order = ['Critical', 'High', 'Medium', 'Low', 'Info'];
        return Array.from(severities).sort((a, b) => {
            const aIdx = order.indexOf(a);
            const bIdx = order.indexOf(b);
            if (aIdx === -1 && bIdx === -1) return a.localeCompare(b);
            if (aIdx === -1) return 1;
            if (bIdx === -1) return -1;
            return aIdx - bIdx;
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Persistence (WP5b)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Set document ID for persistence key
     * @param {string} id
     */
    function setDocumentId(id) {
        documentId = id || null;
    }

    /**
     * Save current progress to localStorage
     * @returns {boolean} - Success
     */
    function saveProgress() {
        if (!documentId) {
            warn('Cannot save: no documentId set');
            return false;
        }
        
        try {
            const saveData = {
                version: 1,
                documentId: documentId,
                savedAt: Date.now(),
                
                // Core state - convert Map to plain object
                decisions: Object.fromEntries(decisions),
                currentIndex: currentIndex,
                navigationMode: navigationMode,
                
                // Filters
                searchQuery: searchQuery,
                filters: filters,
                
                // History (for undo/redo)
                history: history,
                
                // Session
                sessionStartTime: sessionStartTime
            };
            
            localStorage.setItem(getStorageKey(), JSON.stringify(saveData));
            lastSaveTime = saveData.savedAt;
            
            log('Progress saved for', documentId);
            return true;
        } catch (err) {
            // Handle quota exceeded, private browsing, etc.
            error('Save failed:', err.message);
            return false;
        }
    }

    /**
     * Restore progress from localStorage
     * @param {string} docId - Document ID to restore
     * @returns {boolean} - True if progress was found and restored
     */
    function restoreProgress(docId) {
        const key = getStorageKey(docId);
        
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return false;
            
            const saved = JSON.parse(raw);
            
            // Version check
            if (!saved || saved.version !== 1) {
                warn('Incompatible save version');
                return false;
            }
            
            // Restore state
            decisions = new Map(Object.entries(saved.decisions || {}).map(
                ([k, v]) => [parseInt(k, 10), v]  // Keys were stringified
            ));
            currentIndex = saved.currentIndex || 0;
            navigationMode = saved.navigationMode || 'sequential';
            searchQuery = saved.searchQuery || '';
            filters = saved.filters || { category: null, severity: null, status: null, tier: null };
            history = saved.history || { past: [], future: [] };
            sessionStartTime = saved.sessionStartTime || Date.now();
            lastSaveTime = saved.savedAt;
            documentId = docId;
            
            // Recompute navigation
            computeNavigationOrder(navigationMode);
            
            log('Progress restored for', docId);
            emit('change', { type: 'restore', documentId: docId });
            
            return true;
        } catch (err) {
            error('Restore failed:', err.message);
            return false;
        }
    }

    /**
     * Check if saved progress exists
     * @param {string} docId
     * @returns {boolean}
     */
    function hasProgress(docId) {
        try {
            const raw = localStorage.getItem(getStorageKey(docId));
            if (!raw) return false;
            const saved = JSON.parse(raw);
            return saved && saved.version === 1;
        } catch {
            return false;
        }
    }

    /**
     * Clear saved progress
     * @param {string} docId
     */
    function clearProgress(docId) {
        try {
            localStorage.removeItem(getStorageKey(docId));
            log('Progress cleared for', docId);
        } catch (err) {
            error('Clear failed:', err.message);
        }
    }

    /**
     * Get timestamp of last save
     * @returns {number|null}
     */
    function getLastSaveTime() {
        return lastSaveTime;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Statistics (WP5b)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Get comprehensive statistics (computed fresh each call)
     * @returns {Object}
     */
    function getStatistics() {
        const stats = {
            total: fixes.length,
            accepted: 0,
            rejected: 0,
            pending: 0,
            byCategory: {},
            bySeverity: {},
            byTier: {},
            progressPercent: 0
        };
        
        // Initialize category/severity/tier buckets
        fixes.forEach((fix, index) => {
            const cat = fix.category || 'Uncategorized';
            const sev = fix.severity || 'Unknown';
            const tier = fix.confidence_tier || 'unknown';
            
            // Initialize buckets if needed
            if (!stats.byCategory[cat]) {
                stats.byCategory[cat] = { total: 0, accepted: 0, rejected: 0, pending: 0 };
            }
            if (!stats.bySeverity[sev]) {
                stats.bySeverity[sev] = { total: 0, accepted: 0, rejected: 0, pending: 0 };
            }
            if (!stats.byTier[tier]) {
                stats.byTier[tier] = { total: 0, accepted: 0, rejected: 0, pending: 0 };
            }
            
            // Increment totals
            stats.byCategory[cat].total++;
            stats.bySeverity[sev].total++;
            stats.byTier[tier].total++;
            
            // Get decision status
            const decision = decisions.get(index);
            const status = decision ? decision.decision : 'pending';
            
            // Increment status counts
            stats[status]++;
            stats.byCategory[cat][status]++;
            stats.bySeverity[sev][status]++;
            stats.byTier[tier][status]++;
        });
        
        // Calculate progress
        stats.progressPercent = fixes.length > 0 
            ? Math.round(((stats.accepted + stats.rejected) / fixes.length) * 1000) / 10
            : 0;
        
        return stats;
    }

    /**
     * Get progress as percentage (0-100)
     * @returns {number}
     */
    function getProgressPercent() {
        if (fixes.length === 0) return 100;
        const decided = decisions.size;
        return Math.round((decided / fixes.length) * 1000) / 10;
    }

    /**
     * Get estimated time remaining in seconds
     * Based on user's actual review speed this session
     * @returns {number}
     */
    function getEstimatedTimeRemaining() {
        const decidedCount = decisions.size;
        const pendingCount = fixes.length - decidedCount;
        
        if (pendingCount === 0) return 0;
        
        if (decidedCount === 0 || !sessionStartTime) {
            // Default: 4 seconds per fix
            return pendingCount * 4;
        }
        
        const elapsedSeconds = (Date.now() - sessionStartTime) / 1000;
        const avgSecondsPerFix = elapsedSeconds / decidedCount;
        
        // Cap at reasonable bounds (1-30 seconds per fix)
        const bounded = Math.max(1, Math.min(30, avgSecondsPerFix));
        
        return Math.round(pendingCount * bounded);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Export (WP5b)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Get all data formatted for export
     * @returns {Object}
     */
    function getExportData() {
        const accepted = [];
        const rejected = [];
        const pending = [];
        const reviewerNotes = [];
        
        const fixesWithDecisions = fixes.map((fix, index) => {
            const decision = decisions.get(index);
            const enriched = {
                ...fix,
                _index: index,
                _decision: decision ? decision.decision : 'pending',
                _note: decision?.note || null,
                _timestamp: decision?.timestamp || null
            };
            
            // Sort into buckets
            if (decision) {
                if (decision.decision === 'accepted') {
                    accepted.push(enriched);
                } else {
                    rejected.push(enriched);
                }
                
                // Collect notes
                if (decision.note) {
                    reviewerNotes.push({
                        fixIndex: index,
                        category: fix.category,
                        flaggedText: fix.flagged_text,
                        note: decision.note,
                        decision: decision.decision
                    });
                }
            } else {
                pending.push(enriched);
            }
            
            return enriched;
        });
        
        return {
            fixes: fixesWithDecisions,
            accepted,
            rejected,
            pending,
            statistics: getStatistics(),
            reviewerNotes
        };
    }

    /**
     * Get accepted fixes in format expected by markup engine
     * @returns {Array}
     */
    function getSelectedFixes() {
        return fixes
            .map((fix, index) => ({ fix, index }))
            .filter(({ index }) => {
                const decision = decisions.get(index);
                return decision && decision.decision === 'accepted';
            })
            .map(({ fix }) => ({
                original_text: fix.flagged_text,
                replacement_text: fix.suggestion,
                category: fix.category,
                message: fix.message,
                paragraph_index: fix.paragraph_index
            }));
    }

    /**
     * Get rejected fixes for adding as comments
     * @returns {Array}
     */
    function getRejectedFixes() {
        return fixes
            .map((fix, index) => ({ fix, index }))
            .filter(({ index }) => {
                const decision = decisions.get(index);
                return decision && decision.decision === 'rejected';
            })
            .map(({ fix, index }) => {
                const decision = decisions.get(index);
                return {
                    original_text: fix.flagged_text,
                    suggestion: fix.suggestion,
                    category: fix.category,
                    message: fix.message,
                    paragraph_index: fix.paragraph_index,
                    reviewer_note: decision?.note || null
                };
            });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API - Events
    // ═══════════════════════════════════════════════════════════════════════════

    function onChange(callback) {
        return subscribe('change', callback);
    }

    function onDecision(callback) {
        return subscribe('decision', callback);
    }

    function onNavigate(callback) {
        return subscribe('navigate', callback);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // RETURN PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    return {
        // Initialization
        init,
        reset,
        isInitialized,

        // Decisions
        accept,
        reject,
        clearDecision,
        getDecision,
        getAllDecisions,
        setNote,

        // Undo / Redo
        undo,
        redo,
        canUndo,
        canRedo,
        getHistory,

        // Navigation
        setNavigationMode,
        getNavigationMode,
        getNavigationOrder,
        getCurrentIndex,
        getCurrentFix,
        goToNext,
        goToPrevious,
        goToIndex,

        // Groups
        getGroups,
        acceptGroup,
        rejectGroup,
        getGroupForFix,

        // Bulk Operations
        acceptByTier,
        acceptAllPending,
        rejectAllPending,

        // WP5b: Search & Filter
        setSearchQuery,
        getSearchQuery,
        setFilters,
        getFilters,
        clearFilters,
        getFilteredIndices,
        getFilteredCount,
        getCategories,
        getSeverities,

        // WP5b: Persistence
        setDocumentId,
        generateDocumentId,  // v3.0.116 (BUG-M05): Generate unique doc ID to prevent key collision
        saveProgress,
        restoreProgress,
        hasProgress,
        clearProgress,
        getLastSaveTime,

        // WP5b: Statistics
        getStatistics,
        getProgressPercent,
        getEstimatedTimeRemaining,

        // WP5b: Export
        getExportData,
        getSelectedFixes,
        getRejectedFixes,

        // Events
        onChange,
        onDecision,
        onNavigate,
        
        // v3.0.100: Cleanup (ISSUE-007)
        cleanup
    };
})();

// Export to window for browser usage
if (typeof window !== 'undefined') {
    window.FixAssistantState = FixAssistantState;
}

console.log('[TWR FixAssistantState] Module loaded v3.0.116 (WP5a+WP5b complete, BUG-M05 key collision fix)');

// === WP5a + WP5b COMPLETE ===
