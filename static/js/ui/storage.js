/**
 * AEGIS - Storage & Logger Module
 * @version 3.0.48
 *
 * Centralized localStorage management with unified key structure.
 * Consolidates scattered keys: twr-theme, twr_settings, twr_sidebar_collapsed,
 * twr_filters, twr_density, twr-panel-* into a single twr_state object.
 *
 * Also provides TWR.Logger for centralized console logging with debug mode.
 *
 * v3.0.48: Fixed corrupted localStorage handling - clear invalid entries on parse failure
 * v3.0.47: Added TWR.Logger, centralized debug mode control
 * v3.0.46: Initial release - localStorage consolidation
 *
 * Dependencies: None (loads first)
 */

'use strict';

window.TWR = window.TWR || {};

// ============================================================================
// TWR.Logger - Centralized logging with debug mode support
// ============================================================================
TWR.Logger = (function() {
    let _debugMode = false;
    const PREFIX = '[TWR]';
    
    /**
     * Enable/disable debug mode for verbose logging
     */
    function setDebugMode(enabled) {
        _debugMode = enabled;
        console.log(`${PREFIX} Debug mode ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    function isDebugMode() {
        return _debugMode;
    }
    
    /**
     * Standard log - always shown
     */
    function log(message, ...args) {
        console.log(`${PREFIX} ${message}`, ...args);
    }
    
    /**
     * Warning - always shown
     */
    function warn(message, ...args) {
        console.warn(`${PREFIX} ${message}`, ...args);
    }
    
    /**
     * Error - always shown
     */
    function error(message, ...args) {
        console.error(`${PREFIX} ${message}`, ...args);
    }
    
    /**
     * Debug - only shown when debug mode is enabled
     */
    function debug(message, ...args) {
        if (_debugMode) {
            console.log(`${PREFIX} [DEBUG] ${message}`, ...args);
        }
    }
    
    /**
     * Create a sub-logger with a specific module prefix
     * @param {string} moduleName - e.g., 'Storage', 'Events', 'API'
     */
    function createModuleLogger(moduleName) {
        const modulePrefix = `[TWR ${moduleName}]`;
        return {
            log: (msg, ...args) => console.log(`${modulePrefix} ${msg}`, ...args),
            warn: (msg, ...args) => console.warn(`${modulePrefix} ${msg}`, ...args),
            error: (msg, ...args) => console.error(`${modulePrefix} ${msg}`, ...args),
            debug: (msg, ...args) => {
                if (_debugMode) {
                    console.log(`${modulePrefix} [DEBUG] ${msg}`, ...args);
                }
            }
        };
    }
    
    return {
        setDebugMode,
        isDebugMode,
        log,
        warn,
        error,
        debug,
        createModuleLogger
    };
})();

// ============================================================================
// TWR.Storage - Centralized localStorage management
// ============================================================================
TWR.Storage = (function() {
    
    // ========================================
    // CONSTANTS
    // ========================================
    
    const STORAGE_KEY = 'twr_state';
    const STORAGE_VERSION = 1;
    
    // Use module-specific logger
    const logger = TWR.Logger.createModuleLogger('Storage');
    
    // Legacy keys to migrate from
    const LEGACY_KEYS = [
        'twr-theme',
        'twr_settings', 
        'twr_sidebar_collapsed',
        'twr_filters',
        'twr_density',
        'twr_validation_mode'
    ];
    
    // Default state structure
    const DEFAULT_STATE = {
        _version: STORAGE_VERSION,
        ui: {
            theme: 'dark',  // v5.0.0: Default to dark mode
            sidebarCollapsed: false,
            density: 'normal',
            panels: {}  // { panelId: 'collapsed' | 'expanded' }
        },
        filters: {
            severities: ['sev-critical', 'sev-high', 'sev-medium', 'sev-low', 'sev-info'],
            categories: [],
            validationFilter: null
        },
        preferences: {
            darkMode: false,
            compactMode: false,
            showCharts: false,
            autoReview: false,
            rememberChecks: true,
            pageSize: 50,
            essentialsMode: false
        }
    };
    
    // In-memory cache of state
    let _cache = null;
    
    // Debug mode flag
    let _debugMode = false;
    
    // ========================================
    // PRIVATE HELPERS
    // ========================================
    
    /**
     * Log message (respects debug mode via TWR.Logger)
     */
    function log(message, ...args) {
        logger.debug(message, ...args);
    }
    
    /**
     * Deep merge objects (target wins for primitives, recursive for objects)
     */
    function deepMerge(target, source) {
        const result = { ...target };
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = deepMerge(result[key] || {}, source[key]);
            } else if (source[key] !== undefined) {
                result[key] = source[key];
            }
        }
        return result;
    }
    
    /**
     * Read raw value from localStorage
     */
    function readRaw(key) {
        try {
            return localStorage.getItem(key);
        } catch (e) {
            log('Read failed:', key, e);
            return null;
        }
    }
    
    /**
     * Write raw value to localStorage
     */
    function writeRaw(key, value) {
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            log('Write failed:', key, e);
            return false;
        }
    }
    
    /**
     * Remove key from localStorage
     */
    function removeRaw(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            log('Remove failed:', key, e);
            return false;
        }
    }
    
    // ========================================
    // MIGRATION
    // ========================================
    
    /**
     * Migrate legacy localStorage keys to unified structure
     */
    function migrateLegacyKeys() {
        const migrated = {};
        
        // 1. twr-theme -> ui.theme
        const theme = readRaw('twr-theme');
        if (theme) {
            migrated.ui = migrated.ui || {};
            migrated.ui.theme = theme;
            migrated.preferences = migrated.preferences || {};
            migrated.preferences.darkMode = (theme === 'dark');
            log('Migrated twr-theme:', theme);
        }
        
        // 2. twr_sidebar_collapsed -> ui.sidebarCollapsed
        const sidebar = readRaw('twr_sidebar_collapsed');
        if (sidebar !== null) {
            migrated.ui = migrated.ui || {};
            migrated.ui.sidebarCollapsed = (sidebar === '1' || sidebar === 'true');
            log('Migrated twr_sidebar_collapsed:', sidebar);
        }
        
        // 3. twr_density -> ui.density
        const density = readRaw('twr_density');
        if (density) {
            migrated.ui = migrated.ui || {};
            migrated.ui.density = density;
            log('Migrated twr_density:', density);
        }
        
        // 4. twr_filters -> filters
        const filters = readRaw('twr_filters');
        if (filters) {
            try {
                const parsed = JSON.parse(filters);
                migrated.filters = {
                    severities: parsed.severities || DEFAULT_STATE.filters.severities,
                    categories: parsed.categories || [],
                    validationFilter: parsed.validationFilter || null
                };
                log('Migrated twr_filters:', parsed);
            } catch (e) {
                log('Failed to parse twr_filters:', e);
            }
        }
        
        // 5. twr_validation_mode -> filters.validationFilter
        const validationMode = readRaw('twr_validation_mode');
        if (validationMode) {
            migrated.filters = migrated.filters || {};
            migrated.filters.validationFilter = validationMode;
            log('Migrated twr_validation_mode:', validationMode);
        }
        
        // 6. twr_settings -> preferences
        const settings = readRaw('twr_settings');
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                migrated.preferences = {
                    darkMode: parsed.darkMode ?? DEFAULT_STATE.preferences.darkMode,
                    compactMode: parsed.compactMode ?? DEFAULT_STATE.preferences.compactMode,
                    showCharts: parsed.showCharts ?? DEFAULT_STATE.preferences.showCharts,
                    autoReview: parsed.autoReview ?? DEFAULT_STATE.preferences.autoReview,
                    rememberChecks: parsed.rememberChecks ?? DEFAULT_STATE.preferences.rememberChecks,
                    pageSize: parsed.pageSize ?? DEFAULT_STATE.preferences.pageSize,
                    essentialsMode: parsed.essentialsMode ?? DEFAULT_STATE.preferences.essentialsMode
                };
                // Sync darkMode with theme
                if (migrated.preferences.darkMode && (!migrated.ui || !migrated.ui.theme)) {
                    migrated.ui = migrated.ui || {};
                    migrated.ui.theme = 'dark';
                }
                log('Migrated twr_settings:', parsed);
            } catch (e) {
                log('Failed to parse twr_settings:', e);
            }
        }
        
        // 7. twr-panel-* -> ui.panels
        migrated.ui = migrated.ui || {};
        migrated.ui.panels = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('twr-panel-')) {
                const panelId = key.replace('twr-panel-', '');
                const value = readRaw(key);
                migrated.ui.panels[panelId] = value;
                log('Migrated panel state:', panelId, value);
            }
        }
        
        return migrated;
    }
    
    /**
     * Clean up legacy keys after successful migration
     */
    function cleanupLegacyKeys() {
        LEGACY_KEYS.forEach(key => removeRaw(key));
        
        // Also clean up twr-panel-* keys
        const panelKeys = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('twr-panel-')) {
                panelKeys.push(key);
            }
        }
        panelKeys.forEach(key => removeRaw(key));
        
        log('Cleaned up legacy keys');
    }
    
    // ========================================
    // CORE API
    // ========================================
    
    /**
     * Initialize storage - call on app startup
     * Handles migration from legacy keys if needed
     */
    function init() {
        log('Initializing storage...');
        
        // Check if we already have the new unified state
        const existing = readRaw(STORAGE_KEY);

        if (existing) {
            try {
                const parsed = JSON.parse(existing);
                if (parsed._version === STORAGE_VERSION) {
                    // Already migrated, use existing state
                    _cache = deepMerge(DEFAULT_STATE, parsed);
                    log('Loaded existing state (v' + parsed._version + ')');
                    return _cache;
                }
            } catch (e) {
                log('Failed to parse existing state:', e);
                // v3.0.48: Clear corrupted localStorage entry to prevent persistent errors
                removeRaw(STORAGE_KEY);
                log('Cleared corrupted state from localStorage');
            }
        }
        
        // Need to migrate from legacy keys
        log('Migrating from legacy keys...');
        const migrated = migrateLegacyKeys();
        _cache = deepMerge(DEFAULT_STATE, migrated);
        _cache._version = STORAGE_VERSION;
        
        // Save the new unified state
        save();
        
        // Clean up old keys
        cleanupLegacyKeys();
        
        log('Migration complete');
        return _cache;
    }
    
    /**
     * Get entire state object (or initialize if not loaded)
     */
    function getState() {
        if (!_cache) {
            init();
        }
        return _cache;
    }
    
    /**
     * Get a specific value by path (e.g., 'ui.theme', 'preferences.darkMode')
     */
    function get(path, defaultValue = undefined) {
        const state = getState();
        const parts = path.split('.');
        let value = state;
        
        for (const part of parts) {
            if (value && typeof value === 'object' && part in value) {
                value = value[part];
            } else {
                return defaultValue;
            }
        }
        
        return value;
    }
    
    /**
     * Set a specific value by path
     */
    function set(path, value) {
        const state = getState();
        const parts = path.split('.');
        let target = state;
        
        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!(part in target) || typeof target[part] !== 'object') {
                target[part] = {};
            }
            target = target[part];
        }
        
        target[parts[parts.length - 1]] = value;
        save();
        
        log('Set', path, '=', value);
    }
    
    /**
     * Save current state to localStorage
     */
    function save() {
        if (!_cache) return false;
        
        try {
            writeRaw(STORAGE_KEY, JSON.stringify(_cache));
            return true;
        } catch (e) {
            log('Save failed:', e);
            return false;
        }
    }
    
    /**
     * Reset state to defaults
     */
    function reset() {
        _cache = { ...DEFAULT_STATE };
        save();
        log('State reset to defaults');
    }
    
    /**
     * Enable/disable debug logging (proxies to TWR.Logger)
     */
    function setDebugMode(enabled) {
        _debugMode = enabled;
        TWR.Logger.setDebugMode(enabled);
    }
    
    /**
     * Get list of all localStorage keys used by TWR (for documentation)
     */
    function getDocumentation() {
        return {
            currentKey: STORAGE_KEY,
            legacyKeys: LEGACY_KEYS,
            structure: DEFAULT_STATE
        };
    }
    
    // ========================================
    // CONVENIENCE METHODS
    // ========================================
    
    // UI state
    const ui = {
        getTheme: () => get('ui.theme', 'dark'),  // v5.0.0: Default to dark
        setTheme: (theme) => {
            set('ui.theme', theme);
            set('preferences.darkMode', theme === 'dark');
        },
        
        isSidebarCollapsed: () => get('ui.sidebarCollapsed', false),
        setSidebarCollapsed: (collapsed) => set('ui.sidebarCollapsed', collapsed),
        
        getDensity: () => get('ui.density', 'normal'),
        setDensity: (density) => set('ui.density', density),
        
        getPanelState: (panelId) => get(`ui.panels.${panelId}`, 'expanded'),
        setPanelState: (panelId, state) => set(`ui.panels.${panelId}`, state)
    };
    
    // Filter state
    const filters = {
        getSeverities: () => get('filters.severities', DEFAULT_STATE.filters.severities),
        setSeverities: (severities) => set('filters.severities', severities),
        
        getCategories: () => get('filters.categories', []),
        setCategories: (categories) => set('filters.categories', categories),
        
        getValidationFilter: () => get('filters.validationFilter', null),
        setValidationFilter: (filter) => set('filters.validationFilter', filter),
        
        getAll: () => get('filters', DEFAULT_STATE.filters),
        setAll: (filters) => set('filters', filters),
        
        clear: () => set('filters', DEFAULT_STATE.filters)
    };
    
    // User preferences (mirrors State.settings for compatibility)
    const preferences = {
        get: (key) => get(`preferences.${key}`),
        set: (key, value) => set(`preferences.${key}`, value),
        getAll: () => get('preferences', DEFAULT_STATE.preferences),
        setAll: (prefs) => set('preferences', { ...DEFAULT_STATE.preferences, ...prefs })
    };
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // Core
        init,
        getState,
        get,
        set,
        save,
        reset,
        setDebugMode,
        getDocumentation,
        
        // Namespaced convenience methods
        ui,
        filters,
        preferences,
        
        // Constants for external reference
        STORAGE_KEY,
        DEFAULT_STATE
    };
})();

TWR.Logger.log('Logger + Storage modules loaded');
