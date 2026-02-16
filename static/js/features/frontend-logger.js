/**
 * AEGIS - Frontend Logger
 * ===================================
 * ENH-009: Comprehensive frontend logging for diagnostics.
 *
 * Features:
 * - Circular buffer for recent logs
 * - API call logging with timing
 * - User action tracking
 * - Error capture with stack traces
 * - Performance metrics
 * - Backend sync for bug reports
 *
 * Version: 1.0.0
 * Date: 2026-02-02
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Logger = (function() {
    const VERSION = '1.0.0';
    const LOG_PREFIX = '[TWR Logger]';

    // Configuration
    const CONFIG = {
        bufferSize: 500,          // Max logs in circular buffer
        syncInterval: 30000,      // Sync to backend every 30s
        syncBatchSize: 50,        // Max logs per sync
        enableConsole: true,      // Mirror to console
        captureErrors: true,      // Capture window.onerror
        capturePromiseRejections: true,
        performanceThreshold: 500 // Log operations > 500ms as warnings
    };

    // State
    const State = {
        buffer: [],
        syncTimer: null,
        errorCount: 0,
        warningCount: 0,
        totalCount: 0,
        sessionId: generateSessionId()
    };

    // ============================================================
    // UTILITIES
    // ============================================================

    function generateSessionId() {
        return 'fe-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 9);
    }

    function getTimestamp() {
        return new Date().toISOString();
    }

    function truncate(str, maxLength = 500) {
        if (!str) return '';
        if (str.length <= maxLength) return str;
        return str.substring(0, maxLength) + '...';
    }

    function safeStringify(obj, maxDepth = 3) {
        const seen = new WeakSet();
        return JSON.stringify(obj, (key, value) => {
            if (typeof value === 'object' && value !== null) {
                if (seen.has(value)) return '[Circular]';
                seen.add(value);
            }
            if (typeof value === 'function') return '[Function]';
            if (value instanceof Error) {
                return {
                    name: value.name,
                    message: value.message,
                    stack: value.stack
                };
            }
            return value;
        }, 2);
    }

    // ============================================================
    // CIRCULAR BUFFER
    // ============================================================

    function addToBuffer(entry) {
        // Add to buffer
        State.buffer.push(entry);
        State.totalCount++;

        // Update counters
        if (entry.level === 'ERROR') State.errorCount++;
        if (entry.level === 'WARNING') State.warningCount++;

        // Trim buffer if needed
        while (State.buffer.length > CONFIG.bufferSize) {
            State.buffer.shift();
        }
    }

    // ============================================================
    // CORE LOGGING FUNCTIONS
    // ============================================================

    function log(level, message, data = {}) {
        const entry = {
            timestamp: getTimestamp(),
            level: level.toUpperCase(),
            message: truncate(String(message), 1000),
            sessionId: State.sessionId,
            url: window.location.href,
            ...data
        };

        // Add to buffer
        addToBuffer(entry);

        // Console output
        if (CONFIG.enableConsole) {
            const consoleMethod = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warn',
                'ERROR': 'error'
            }[entry.level] || 'log';

            console[consoleMethod](
                `${LOG_PREFIX} [${entry.level}]`,
                message,
                Object.keys(data).length > 0 ? data : ''
            );
        }

        return entry;
    }

    function debug(message, data = {}) {
        return log('DEBUG', message, data);
    }

    function info(message, data = {}) {
        return log('INFO', message, data);
    }

    function warning(message, data = {}) {
        return log('WARNING', message, data);
    }

    function error(message, data = {}) {
        // Capture stack trace if not provided
        if (!data.stack) {
            try {
                throw new Error(message);
            } catch (e) {
                data.stack = e.stack;
            }
        }
        return log('ERROR', message, data);
    }

    // ============================================================
    // SPECIALIZED LOGGING
    // ============================================================

    /**
     * Log an API call with timing.
     */
    function logApiCall(method, url, options = {}) {
        const startTime = performance.now();
        const callId = 'api-' + Date.now().toString(36);

        // Log request
        debug(`API ${method} ${url}`, {
            type: 'api_request',
            callId,
            method,
            url: truncate(url, 200)
        });

        // Return a function to log the response
        return function logResponse(response, error = null) {
            const duration = performance.now() - startTime;
            const level = error ? 'ERROR' : (duration > CONFIG.performanceThreshold ? 'WARNING' : 'INFO');

            log(level, `API ${method} ${url} - ${error ? 'FAILED' : response?.status || 'OK'} (${duration.toFixed(0)}ms)`, {
                type: 'api_response',
                callId,
                method,
                url: truncate(url, 200),
                status: response?.status,
                duration_ms: Math.round(duration),
                error: error ? String(error) : null
            });
        };
    }

    /**
     * Log a user action.
     */
    function logAction(action, details = {}) {
        info(`User action: ${action}`, {
            type: 'user_action',
            action,
            ...details
        });
    }

    /**
     * Log a state change.
     */
    function logStateChange(component, change, details = {}) {
        debug(`State change in ${component}: ${change}`, {
            type: 'state_change',
            component,
            change,
            ...details
        });
    }

    /**
     * Log a performance metric.
     */
    function logPerformance(operation, durationMs, details = {}) {
        const level = durationMs > CONFIG.performanceThreshold ? 'WARNING' : 'DEBUG';
        log(level, `Performance: ${operation} took ${durationMs.toFixed(0)}ms`, {
            type: 'performance',
            operation,
            duration_ms: Math.round(durationMs),
            ...details
        });
    }

    /**
     * Create a timer for measuring operations.
     */
    function startTimer(operation) {
        const startTime = performance.now();
        return {
            operation,
            startTime,
            end: function(details = {}) {
                const duration = performance.now() - startTime;
                logPerformance(operation, duration, details);
                return duration;
            }
        };
    }

    // ============================================================
    // ERROR CAPTURE
    // ============================================================

    function setupErrorCapture() {
        if (!CONFIG.captureErrors) return;

        // Capture uncaught errors
        window.addEventListener('error', (event) => {
            error('Uncaught error', {
                type: 'uncaught_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // Capture unhandled promise rejections
        if (CONFIG.capturePromiseRejections) {
            window.addEventListener('unhandledrejection', (event) => {
                error('Unhandled promise rejection', {
                    type: 'unhandled_rejection',
                    reason: String(event.reason),
                    stack: event.reason?.stack
                });
            });
        }
    }

    // ============================================================
    // BACKEND SYNC
    // ============================================================

    async function syncToBackend() {
        if (State.buffer.length === 0) return;

        // Get logs to sync (oldest first, up to batch size)
        const logsToSync = State.buffer.slice(-CONFIG.syncBatchSize);

        try {
            const response = await fetch('/api/diagnostics/frontend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ logs: logsToSync })
            });

            if (response.ok) {
                debug('Synced logs to backend', { count: logsToSync.length });
            }
        } catch (e) {
            // Don't log this error to avoid loops
            console.warn(LOG_PREFIX, 'Failed to sync logs to backend:', e);
        }
    }

    function startBackendSync() {
        if (State.syncTimer) return;

        State.syncTimer = setInterval(syncToBackend, CONFIG.syncInterval);

        // Sync before page unload
        window.addEventListener('beforeunload', () => {
            // Use sendBeacon for reliability
            if (navigator.sendBeacon && State.buffer.length > 0) {
                const logsToSync = State.buffer.slice(-CONFIG.syncBatchSize);
                navigator.sendBeacon(
                    '/api/diagnostics/frontend',
                    JSON.stringify({ logs: logsToSync })
                );
            }
        });
    }

    function stopBackendSync() {
        if (State.syncTimer) {
            clearInterval(State.syncTimer);
            State.syncTimer = null;
        }
    }

    // ============================================================
    // EXPORT & DIAGNOSTICS
    // ============================================================

    function getStats() {
        return {
            totalCount: State.totalCount,
            errorCount: State.errorCount,
            warningCount: State.warningCount,
            bufferSize: State.buffer.length,
            bufferCapacity: CONFIG.bufferSize,
            sessionId: State.sessionId
        };
    }

    function getRecentLogs(count = 100, level = null) {
        let logs = State.buffer.slice(-count);
        if (level) {
            logs = logs.filter(l => l.level === level.toUpperCase());
        }
        return logs;
    }

    function exportLogs() {
        return {
            stats: getStats(),
            logs: State.buffer,
            userAgent: navigator.userAgent,
            timestamp: getTimestamp(),
            url: window.location.href
        };
    }

    function clear() {
        State.buffer = [];
        State.errorCount = 0;
        State.warningCount = 0;
        State.totalCount = 0;
        info('Log buffer cleared');
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================

    function init() {
        setupErrorCapture();
        startBackendSync();

        info('Frontend logger initialized', {
            version: VERSION,
            sessionId: State.sessionId,
            bufferSize: CONFIG.bufferSize
        });
    }

    // Auto-initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    return {
        VERSION,

        // Core logging
        debug,
        info,
        warning,
        error,
        log,

        // Specialized logging
        logApiCall,
        logAction,
        logStateChange,
        logPerformance,
        startTimer,

        // Management
        getStats,
        getRecentLogs,
        exportLogs,
        clear,
        syncToBackend,

        // Config
        configure: function(options) {
            Object.assign(CONFIG, options);
        }
    };
})();

console.log('[TWR Logger] Module loaded v' + TWR.Logger.VERSION);
