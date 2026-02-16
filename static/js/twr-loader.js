/**
 * AEGIS - Module Loader
 * @version 3.2.4
 *
 * Handles loading IIFE modules in correct dependency order for air-gapped environments.
 * No bundler required - scripts are loaded sequentially via DOM insertion.
 *
 * This file should be loaded FIRST, before any other TWR modules.
 */

'use strict';

// Initialize global namespace
window.TWR = window.TWR || {
    version: '3.2.4',
    modulesLoaded: [],
    moduleLoadErrors: [],
    isReady: false
};

/**
 * Module loading configuration
 * Order matters - modules are loaded sequentially based on dependencies
 */
TWR.ModuleConfig = {
    // Base path for modules
    basePath: '/static/js',
    
    // Modules in dependency order
    // Each module is loaded only after its dependencies are ready
    modules: [
        // Layer 0: No dependencies
        { name: 'utils/dom', path: 'utils/dom.js', deps: [] },
        
        // Layer 1: Depends on utils
        { name: 'ui/state', path: 'ui/state.js', deps: ['utils/dom'] },
        { name: 'api/client', path: 'api/client.js', deps: ['utils/dom'] },
        
        // Layer 2: Depends on state and utils
        { name: 'ui/modals', path: 'ui/modals.js', deps: ['utils/dom', 'ui/state'] },
        
        // Layer 3+: Feature modules (to be added)
        // { name: 'ui/events', path: 'ui/events.js', deps: ['utils/dom', 'ui/state', 'ui/modals'] },
        // { name: 'ui/renderers', path: 'ui/renderers.js', deps: ['utils/dom', 'ui/state'] },
        // { name: 'features/roles', path: 'features/roles.js', deps: ['utils/dom', 'ui/state', 'api/client'] },
        // { name: 'features/triage', path: 'features/triage.js', deps: ['utils/dom', 'ui/state', 'ui/modals'] },
        // { name: 'features/families', path: 'features/families.js', deps: ['utils/dom', 'ui/state'] },
    ]
};

/**
 * Load a single script by URL
 * @param {string} url - Script URL
 * @returns {Promise<void>}
 */
TWR.loadScript = function(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.async = false; // Maintain order
        
        script.onload = () => {
            console.log(`[TWR Loader] Loaded: ${url}`);
            resolve();
        };
        
        script.onerror = () => {
            const error = new Error(`Failed to load: ${url}`);
            console.error(`[TWR Loader] ${error.message}`);
            reject(error);
        };
        
        document.head.appendChild(script);
    });
};

/**
 * Check if a module's dependencies are loaded
 * @param {Array<string>} deps - Dependency module names
 * @returns {boolean}
 */
TWR.checkDependencies = function(deps) {
    return deps.every(dep => TWR.modulesLoaded.includes(dep));
};

/**
 * Load all modules in dependency order
 * @returns {Promise<void>}
 */
TWR.loadModules = async function() {
    const config = TWR.ModuleConfig;
    
    console.log('[TWR Loader] Starting module load...');
    
    for (const module of config.modules) {
        // Check dependencies
        if (!TWR.checkDependencies(module.deps)) {
            const error = `Module ${module.name} has unmet dependencies: ${module.deps.filter(d => !TWR.modulesLoaded.includes(d)).join(', ')}`;
            console.error(`[TWR Loader] ${error}`);
            TWR.moduleLoadErrors.push({ module: module.name, error });
            continue;
        }
        
        try {
            const url = `${config.basePath}/${module.path}`;
            await TWR.loadScript(url);
            TWR.modulesLoaded.push(module.name);
        } catch (e) {
            TWR.moduleLoadErrors.push({ module: module.name, error: e.message });
            console.error(`[TWR Loader] Failed to load ${module.name}:`, e);
            // Continue loading other modules - graceful degradation
        }
    }
    
    TWR.isReady = true;
    console.log(`[TWR Loader] Module loading complete. Loaded: ${TWR.modulesLoaded.length}/${config.modules.length}`);
    
    if (TWR.moduleLoadErrors.length > 0) {
        console.warn('[TWR Loader] Some modules failed to load:', TWR.moduleLoadErrors);
    }
    
    // Dispatch ready event
    window.dispatchEvent(new CustomEvent('twr:ready', {
        detail: {
            loaded: TWR.modulesLoaded,
            errors: TWR.moduleLoadErrors
        }
    }));
};

/**
 * Initialize module loading
 * Can be called early in page load
 */
TWR.init = async function() {
    // Only run once
    if (TWR._initStarted) return;
    TWR._initStarted = true;
    
    console.log(`[TWR] AEGIS v${TWR.version} initializing...`);
    
    // Load modules
    await TWR.loadModules();
};

/**
 * Wait for TWR to be ready
 * @returns {Promise<void>}
 */
TWR.ready = function() {
    return new Promise((resolve) => {
        if (TWR.isReady) {
            resolve();
        } else {
            window.addEventListener('twr:ready', () => resolve(), { once: true });
        }
    });
};

// Export for debugging
window.TWR = TWR;

console.log('[TWR] Module loader initialized');
