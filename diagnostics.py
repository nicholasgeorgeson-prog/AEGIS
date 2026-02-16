"""
AEGIS - Comprehensive Diagnostics Module
====================================================
ENH-009: Comprehensive logging for detailed bug reports.

Features:
- Circular buffer for recent logs (no disk I/O until export)
- Async logging queue for high-frequency events
- Performance-safe lazy evaluation helpers
- Log aggregation and export
- Frontend log collection API
- Troubleshooting window integration

Version: 1.0.0
Date: 2026-02-02
"""

import os
import sys
import json
import time
import queue
import threading
import traceback
import functools
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path

# Import existing logging infrastructure
try:
    from config_logging import get_logger, StructuredLogger, get_config
except ImportError:
    get_logger = None
    StructuredLogger = None
    get_config = None


# =============================================================================
# CONSTANTS
# =============================================================================

CIRCULAR_BUFFER_SIZE = 1000      # Number of recent logs to keep in memory
LOG_QUEUE_SIZE = 500             # Max queued logs before blocking
SAMPLING_THRESHOLD = 100         # Log every Nth occurrence for high-freq events
PERFORMANCE_LOG_THRESHOLD_MS = 100  # Log operations taking longer than this


# =============================================================================
# CIRCULAR LOG BUFFER
# =============================================================================

class CircularLogBuffer:
    """
    Thread-safe circular buffer for recent log entries.
    Keeps logs in memory to avoid disk I/O overhead.
    """

    def __init__(self, max_size: int = CIRCULAR_BUFFER_SIZE):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.lock = threading.Lock()
        self.error_count = 0
        self.warning_count = 0
        self.total_count = 0

    def append(self, entry: Dict[str, Any]):
        """Add a log entry to the buffer."""
        with self.lock:
            self.buffer.append(entry)
            self.total_count += 1

            level = entry.get('level', '').upper()
            if level == 'ERROR':
                self.error_count += 1
            elif level == 'WARNING':
                self.warning_count += 1

    def get_recent(self, count: int = 100, level: Optional[str] = None,
                   module: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries with optional filtering."""
        with self.lock:
            result = []
            for entry in reversed(self.buffer):
                if level and entry.get('level', '').upper() != level.upper():
                    continue
                if module and entry.get('logger', '') != module:
                    continue
                result.append(entry)
                if len(result) >= count:
                    break
            return list(reversed(result))

    def search(self, query: str, count: int = 100) -> List[Dict[str, Any]]:
        """Search logs for a query string."""
        with self.lock:
            query_lower = query.lower()
            result = []
            for entry in reversed(self.buffer):
                msg = str(entry.get('message', '')).lower()
                if query_lower in msg:
                    result.append(entry)
                    if len(result) >= count:
                        break
            return list(reversed(result))

    def export_all(self) -> List[Dict[str, Any]]:
        """Export all log entries for bug reports."""
        with self.lock:
            return list(self.buffer)

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        with self.lock:
            return {
                'total_logged': self.total_count,
                'buffer_size': len(self.buffer),
                'buffer_capacity': self.max_size,
                'error_count': self.error_count,
                'warning_count': self.warning_count
            }

    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()
            self.error_count = 0
            self.warning_count = 0
            self.total_count = 0


# =============================================================================
# ASYNC LOG QUEUE
# =============================================================================

class AsyncLogQueue:
    """
    Async queue for batching log writes.
    Prevents main thread blocking on disk I/O.
    """

    def __init__(self, max_size: int = LOG_QUEUE_SIZE, flush_interval: float = 1.0):
        self.queue = queue.Queue(maxsize=max_size)
        self.flush_interval = flush_interval
        self.running = False
        self.worker_thread = None
        self.handlers: List[Callable[[Dict[str, Any]], None]] = []

    def add_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add a log handler function."""
        self.handlers.append(handler)

    def enqueue(self, entry: Dict[str, Any]):
        """Add log entry to queue (non-blocking)."""
        try:
            self.queue.put_nowait(entry)
        except queue.Full:
            # Drop oldest if full
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(entry)
            except queue.Empty:
                pass

    def start(self):
        """Start the async worker thread."""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        """Stop the async worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)

    def _worker(self):
        """Worker thread that processes the queue."""
        batch = []
        last_flush = time.time()

        while self.running:
            try:
                # Get with timeout to allow periodic flushing
                entry = self.queue.get(timeout=0.1)
                batch.append(entry)
            except queue.Empty:
                pass

            # Flush periodically or when batch is large
            if batch and (len(batch) >= 50 or time.time() - last_flush >= self.flush_interval):
                self._flush_batch(batch)
                batch = []
                last_flush = time.time()

        # Flush remaining on shutdown
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[Dict[str, Any]]):
        """Flush a batch of log entries to handlers."""
        for entry in batch:
            for handler in self.handlers:
                try:
                    handler(entry)
                except Exception:
                    pass  # Don't let handler errors crash the worker


# =============================================================================
# SAMPLING LOGGER
# =============================================================================

class SamplingLogger:
    """
    Logger that samples high-frequency events.
    Only logs every Nth occurrence to reduce overhead.
    """

    def __init__(self, threshold: int = SAMPLING_THRESHOLD):
        self.threshold = threshold
        self.counters: Dict[str, int] = {}
        self.lock = threading.Lock()

    def should_log(self, event_key: str) -> tuple:
        """
        Check if this event should be logged.
        Returns (should_log, skipped_count).
        """
        with self.lock:
            count = self.counters.get(event_key, 0) + 1
            self.counters[event_key] = count

            if count % self.threshold == 0:
                skipped = self.threshold - 1
                return (True, skipped)
            elif count == 1:
                return (True, 0)  # Always log first occurrence
            else:
                return (False, 0)

    def reset(self, event_key: str = None):
        """Reset counter(s)."""
        with self.lock:
            if event_key:
                self.counters.pop(event_key, None)
            else:
                self.counters.clear()


# =============================================================================
# DIAGNOSTIC LOGGER
# =============================================================================

class DiagnosticLogger:
    """
    Enhanced logger with diagnostics features.
    Wraps the existing StructuredLogger with additional capabilities.
    """

    def __init__(self, name: str):
        self.name = name
        self.base_logger = get_logger(name) if get_logger else None

        # Initialize shared resources
        if not hasattr(DiagnosticLogger, '_buffer'):
            DiagnosticLogger._buffer = CircularLogBuffer()
            DiagnosticLogger._async_queue = AsyncLogQueue()
            DiagnosticLogger._sampler = SamplingLogger()
            DiagnosticLogger._async_queue.add_handler(DiagnosticLogger._buffer.append)
            DiagnosticLogger._async_queue.start()

    def _format_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Format a log entry."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': level,
            'logger': self.name,
            'message': message,
            **kwargs
        }

        # Add correlation ID if available
        if StructuredLogger:
            entry['correlation_id'] = StructuredLogger.get_correlation_id()

        return entry

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        if self.base_logger:
            self.base_logger.debug(message, **kwargs)
        entry = self._format_entry('DEBUG', message, **kwargs)
        DiagnosticLogger._async_queue.enqueue(entry)

    def info(self, message: str, **kwargs):
        """Log info message."""
        if self.base_logger:
            self.base_logger.info(message, **kwargs)
        entry = self._format_entry('INFO', message, **kwargs)
        DiagnosticLogger._async_queue.enqueue(entry)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        if self.base_logger:
            self.base_logger.warning(message, **kwargs)
        entry = self._format_entry('WARNING', message, **kwargs)
        DiagnosticLogger._async_queue.enqueue(entry)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with optional exception info."""
        if exc_info:
            kwargs['traceback'] = traceback.format_exc()

        if self.base_logger:
            self.base_logger.error(message, **kwargs)
        entry = self._format_entry('ERROR', message, **kwargs)
        DiagnosticLogger._async_queue.enqueue(entry)

    def sampled(self, event_key: str, level: str, message: str, **kwargs):
        """Log with sampling for high-frequency events."""
        should_log, skipped = DiagnosticLogger._sampler.should_log(event_key)
        if should_log:
            if skipped > 0:
                message = f"{message} (skipped {skipped} similar events)"
            getattr(self, level.lower())(message, **kwargs)

    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metric if above threshold."""
        if duration_ms >= PERFORMANCE_LOG_THRESHOLD_MS:
            self.warning(
                f"Slow operation: {operation} took {duration_ms:.1f}ms",
                operation=operation,
                duration_ms=duration_ms,
                **kwargs
            )
        else:
            self.debug(
                f"Operation: {operation} completed in {duration_ms:.1f}ms",
                operation=operation,
                duration_ms=duration_ms,
                **kwargs
            )

    @classmethod
    def get_buffer(cls) -> CircularLogBuffer:
        """Get the shared log buffer."""
        if not hasattr(cls, '_buffer'):
            cls._buffer = CircularLogBuffer()
        return cls._buffer

    @classmethod
    def export_diagnostics(cls) -> Dict[str, Any]:
        """Export complete diagnostics for bug reports."""
        buffer = cls.get_buffer()

        # Collect system info
        system_info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Get config if available
        config_info = {}
        if get_config:
            try:
                cfg = get_config()
                config_info = {
                    'log_level': cfg.log_level,
                    'debug': cfg.debug,
                    'auth_enabled': cfg.auth_enabled
                }
            except Exception:
                pass

        return {
            'system': system_info,
            'config': config_info,
            'stats': buffer.get_stats(),
            'logs': buffer.export_all()
        }


# =============================================================================
# PERFORMANCE TIMER
# =============================================================================

@dataclass
class PerformanceTimer:
    """Context manager for timing operations."""

    operation: str
    logger: Optional[DiagnosticLogger] = None
    threshold_ms: float = PERFORMANCE_LOG_THRESHOLD_MS
    start_time: float = field(default=0, init=False)
    end_time: float = field(default=0, init=False)

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        if self.logger:
            self.logger.performance(self.operation, duration_ms)

        return False

    @property
    def duration_ms(self) -> float:
        if self.end_time == 0:
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000


def timed(operation: str = None, threshold_ms: float = PERFORMANCE_LOG_THRESHOLD_MS):
    """Decorator to time function execution."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            logger = DiagnosticLogger(func.__module__ or 'diagnostics')

            with PerformanceTimer(op_name, logger, threshold_ms):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def create_diagnostics_blueprint():
    """Create Flask blueprint for diagnostics API."""
    from flask import Blueprint, jsonify, request

    bp = Blueprint('diagnostics', __name__)

    @bp.route('/api/diagnostics/logs', methods=['GET'])
    def get_logs():
        """Get recent logs."""
        count = request.args.get('count', 100, type=int)
        level = request.args.get('level')
        module = request.args.get('module')
        query = request.args.get('q')

        buffer = DiagnosticLogger.get_buffer()

        if query:
            logs = buffer.search(query, count)
        else:
            logs = buffer.get_recent(count, level, module)

        return jsonify({
            'success': True,
            'logs': logs,
            'stats': buffer.get_stats()
        })

    @bp.route('/api/diagnostics/export', methods=['GET'])
    def export_diagnostics():
        """Export full diagnostics for bug report."""
        data = DiagnosticLogger.export_diagnostics()
        return jsonify({
            'success': True,
            'data': data
        })

    @bp.route('/api/diagnostics/stats', methods=['GET'])
    def get_stats():
        """Get logging statistics."""
        buffer = DiagnosticLogger.get_buffer()
        return jsonify({
            'success': True,
            'stats': buffer.get_stats()
        })

    @bp.route('/api/diagnostics/frontend', methods=['POST'])
    def receive_frontend_logs():
        """Receive logs from frontend JavaScript."""
        data = request.get_json() or {}
        logs = data.get('logs', [])

        buffer = DiagnosticLogger.get_buffer()
        for log in logs:
            log['source'] = 'frontend'
            buffer.append(log)

        return jsonify({'success': True, 'received': len(logs)})

    @bp.route('/api/diagnostics/clear', methods=['POST'])
    def clear_logs():
        """Clear the log buffer."""
        buffer = DiagnosticLogger.get_buffer()
        buffer.clear()
        return jsonify({'success': True})

    return bp


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_diagnostic_logger(name: str) -> DiagnosticLogger:
    """Get a diagnostic logger for a module."""
    return DiagnosticLogger(name)


def log_startup_info():
    """Log system information at startup."""
    logger = get_diagnostic_logger('startup')

    logger.info("AEGIS starting up", **{
        'python_version': sys.version,
        'platform': sys.platform,
        'cwd': os.getcwd()
    })

    # Log loaded modules
    nlp_available = False
    try:
        import spacy
        nlp_available = True
    except ImportError:
        pass

    logger.info("Module availability", **{
        'spacy': nlp_available
    })


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DiagnosticLogger',
    'CircularLogBuffer',
    'AsyncLogQueue',
    'SamplingLogger',
    'PerformanceTimer',
    'timed',
    'get_diagnostic_logger',
    'create_diagnostics_blueprint',
    'log_startup_info'
]
