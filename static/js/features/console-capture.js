/**
 * Console Log Capture Module
 * ==========================
 * Captures console.log, console.warn, console.error messages
 * for diagnostic export. Sanitizes sensitive data automatically.
 *
 * @version 1.0.0 (v3.0.114)
 */

window.ConsoleCapture = (function() {
    'use strict';

    // =========================================================================
    // CONFIGURATION
    // =========================================================================

    const MAX_LOGS = 500;
    const MAX_MESSAGE_LENGTH = 2000;

    // Patterns to sanitize (similar to backend)
    const SANITIZE_PATTERNS = [
        // Email addresses
        { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi, replacement: '[EMAIL]' },
        // Phone numbers
        { pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: '[PHONE]' },
        // File paths with usernames
        { pattern: /\/Users\/[^\/\s]+/gi, replacement: '/Users/[USER]' },
        { pattern: /C:\\Users\\[^\\]+/gi, replacement: 'C:\\Users\\[USER]' },
        // API keys / long hex strings
        { pattern: /\b[A-Fa-f0-9]{32,}\b/g, replacement: '[TOKEN]' },
        // Bearer tokens
        { pattern: /Bearer\s+[A-Za-z0-9._-]+/gi, replacement: 'Bearer [REDACTED]' },
        // IP addresses (except localhost)
        { pattern: /\b(?!127\.0\.0\.1)(?!0\.0\.0\.0)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, replacement: '[IP]' },
    ];

    // =========================================================================
    // STATE
    // =========================================================================

    let logs = [];
    let originalConsole = {};
    let isCapturing = false;
    let sessionId = generateSessionId();

    // =========================================================================
    // HELPERS
    // =========================================================================

    function generateSessionId() {
        return 'fe-' + Math.random().toString(36).substring(2, 10);
    }

    function sanitize(text) {
        if (typeof text !== 'string') {
            try {
                text = JSON.stringify(text);
            } catch (e) {
                text = String(text);
            }
        }

        let result = text;
        SANITIZE_PATTERNS.forEach(({ pattern, replacement }) => {
            result = result.replace(pattern, replacement);
        });

        // Truncate long messages
        if (result.length > MAX_MESSAGE_LENGTH) {
            result = result.substring(0, MAX_MESSAGE_LENGTH) + `... [truncated, ${text.length} total chars]`;
        }

        return result;
    }

    function formatArgs(args) {
        return Array.from(args).map(arg => {
            if (arg instanceof Error) {
                return `${arg.name}: ${arg.message}\n${arg.stack || ''}`;
            }
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
    }

    function createLogEntry(level, args) {
        const message = formatArgs(args);
        const sanitizedMessage = sanitize(message);

        // Get call location
        const stack = new Error().stack || '';
        const stackLines = stack.split('\n');
        // Skip Error, createLogEntry, wrapper function, to get actual caller
        const callerLine = stackLines[4] || '';
        const locationMatch = callerLine.match(/at\s+(.+?)\s+\((.+):(\d+):(\d+)\)/) ||
                             callerLine.match(/at\s+(.+):(\d+):(\d+)/);

        let location = 'unknown';
        if (locationMatch) {
            if (locationMatch.length === 5) {
                location = `${locationMatch[1]} (${locationMatch[2]}:${locationMatch[3]})`;
            } else if (locationMatch.length === 4) {
                location = `${locationMatch[1]}:${locationMatch[2]}`;
            }
        }

        return {
            timestamp: new Date().toISOString(),
            level: level,
            message: sanitizedMessage,
            location: sanitize(location),
            sessionId: sessionId,
        };
    }

    function addLog(entry) {
        logs.push(entry);
        if (logs.length > MAX_LOGS) {
            logs.shift(); // Remove oldest
        }
    }

    // =========================================================================
    // CONSOLE INTERCEPTION
    // =========================================================================

    function startCapture() {
        if (isCapturing) return;

        // Store original console methods
        originalConsole = {
            log: console.log,
            warn: console.warn,
            error: console.error,
            info: console.info,
            debug: console.debug,
        };

        // Wrap console.log
        console.log = function(...args) {
            addLog(createLogEntry('LOG', args));
            originalConsole.log.apply(console, args);
        };

        // Wrap console.warn
        console.warn = function(...args) {
            addLog(createLogEntry('WARN', args));
            originalConsole.warn.apply(console, args);
        };

        // Wrap console.error
        console.error = function(...args) {
            addLog(createLogEntry('ERROR', args));
            originalConsole.error.apply(console, args);
        };

        // Wrap console.info
        console.info = function(...args) {
            addLog(createLogEntry('INFO', args));
            originalConsole.info.apply(console, args);
        };

        // Wrap console.debug
        console.debug = function(...args) {
            addLog(createLogEntry('DEBUG', args));
            originalConsole.debug.apply(console, args);
        };

        // Capture unhandled errors
        window.addEventListener('error', handleWindowError);
        window.addEventListener('unhandledrejection', handleUnhandledRejection);

        isCapturing = true;
        console.log('[TWR ConsoleCapture] Started capturing console logs');
    }

    function stopCapture() {
        if (!isCapturing) return;

        // Restore original console methods
        console.log = originalConsole.log;
        console.warn = originalConsole.warn;
        console.error = originalConsole.error;
        console.info = originalConsole.info;
        console.debug = originalConsole.debug;

        window.removeEventListener('error', handleWindowError);
        window.removeEventListener('unhandledrejection', handleUnhandledRejection);

        isCapturing = false;
    }

    function handleWindowError(event) {
        addLog({
            timestamp: new Date().toISOString(),
            level: 'UNCAUGHT_ERROR',
            message: sanitize(`${event.message} at ${event.filename}:${event.lineno}:${event.colno}`),
            location: sanitize(`${event.filename}:${event.lineno}`),
            sessionId: sessionId,
            stack: event.error?.stack ? sanitize(event.error.stack) : null,
        });
    }

    function handleUnhandledRejection(event) {
        const reason = event.reason;
        let message = 'Unhandled Promise Rejection';

        if (reason instanceof Error) {
            message = `${reason.name}: ${reason.message}`;
        } else if (typeof reason === 'string') {
            message = reason;
        } else {
            try {
                message = JSON.stringify(reason);
            } catch (e) {
                message = String(reason);
            }
        }

        addLog({
            timestamp: new Date().toISOString(),
            level: 'UNHANDLED_REJECTION',
            message: sanitize(message),
            location: 'Promise',
            sessionId: sessionId,
            stack: reason?.stack ? sanitize(reason.stack) : null,
        });
    }

    // =========================================================================
    // EXPORT
    // =========================================================================

    function getLogs(options = {}) {
        const { level, limit, since } = options;
        let result = [...logs];

        if (level) {
            const levels = Array.isArray(level) ? level : [level];
            result = result.filter(log => levels.includes(log.level));
        }

        if (since) {
            const sinceDate = new Date(since);
            result = result.filter(log => new Date(log.timestamp) >= sinceDate);
        }

        if (limit && limit < result.length) {
            result = result.slice(-limit);
        }

        return result;
    }

    function getStats() {
        const stats = {
            total: logs.length,
            byLevel: {},
            sessionId: sessionId,
            oldestLog: logs.length > 0 ? logs[0].timestamp : null,
            newestLog: logs.length > 0 ? logs[logs.length - 1].timestamp : null,
        };

        logs.forEach(log => {
            stats.byLevel[log.level] = (stats.byLevel[log.level] || 0) + 1;
        });

        return stats;
    }

    function clear() {
        logs = [];
        sessionId = generateSessionId();
    }

    async function submitToServer() {
        try {
            const response = await fetch('/api/diagnostics/frontend-logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.State?.csrfToken || document.querySelector('meta[name="csrf-token"]')?.content || '',
                },
                body: JSON.stringify({
                    logs: getLogs(),
                    stats: getStats(),
                    userAgent: navigator.userAgent,
                    url: window.location.href,
                }),
            });

            const data = await response.json();
            if (data.success) {
                console.log('[TWR ConsoleCapture] Logs submitted successfully');
            }
            return data;
        } catch (error) {
            console.error('[TWR ConsoleCapture] Failed to submit logs:', error);
            throw error;
        }
    }

    // =========================================================================
    // AUTO-START
    // =========================================================================

    // Auto-start capture when the module loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startCapture);
    } else {
        startCapture();
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        startCapture,
        stopCapture,
        getLogs,
        getStats,
        clear,
        submitToServer,
        isCapturing: () => isCapturing,
        getSessionId: () => sessionId,
    };
})();

console.log('[TWR ConsoleCapture] Module loaded v1.0.0');
