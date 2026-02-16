#!/usr/bin/env python3
"""
AEGIS Diagnostic Export Module
==========================================
Comprehensive error logging and diagnostic export with sanitization
for secure troubleshooting support.

Version: reads from version.json (module v2.8)

Features:
- Detailed error capture with full stack traces
- Automatic sanitization of proprietary content
- System environment and configuration snapshots
- Request/response logging for debugging
- Single-file export for easy sharing
- Configurable sanitization patterns

Usage:
    from diagnostic_export import DiagnosticCollector, export_diagnostics
    
    # Automatic error capture
    collector = DiagnosticCollector.get_instance()
    collector.capture_error(exception, context={'request': '/api/review'})
    
    # Export sanitized diagnostics
    filepath = export_diagnostics(include_system_info=True)
"""

import os
import sys
import json
import re
import traceback
import platform
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
import logging

# Load version from central config
try:
    from config_logging import VERSION
    __version__ = VERSION
except ImportError:
    __version__ = "2.9.3"

# =============================================================================
# SANITIZATION PATTERNS
# =============================================================================

# Patterns that identify proprietary content to sanitize
DEFAULT_SANITIZE_PATTERNS = {
    # File paths - keep structure, anonymize names
    'file_paths': [
        (r'[A-Z]:\\[^"\s]+', lambda m: sanitize_path(m.group(0))),
        (r'/(?:home|Users)/[^/\s]+/[^"\s]*', lambda m: sanitize_path(m.group(0))),
    ],
    
    # Document content - redact but preserve structure
    'document_content': [
        # Quoted strings longer than 30 chars (likely document text)
        (r'"([^"]{30,})"', lambda m: f'"[CONTENT:{len(m.group(1))}chars]"'),
        (r"'([^']{30,})'", lambda m: f"'[CONTENT:{len(m.group(1))}chars]'"),
    ],
    
    # Personal identifiers
    'personal_info': [
        # Email addresses
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        # Phone numbers
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        # SSN
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    ],
    
    # Network/URLs
    'network': [
        # IP addresses (keep localhost)
        (r'\b(?!127\.0\.0\.1)(?!0\.0\.0\.0)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_ADDR]'),
        # Internal URLs (keep structure)
        (r'https?://(?!localhost)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s"\']*', lambda m: sanitize_url(m.group(0))),
    ],
    
    # Secrets/tokens
    'secrets': [
        # API keys / tokens (long hex or base64 strings)
        (r'\b[A-Fa-f0-9]{32,}\b', '[TOKEN_HEX]'),
        (r'\b[A-Za-z0-9+/]{40,}={0,2}\b', '[TOKEN_B64]'),
        # Bearer tokens
        (r'Bearer\s+[A-Za-z0-9._-]+', 'Bearer [REDACTED]'),
        # Secret key patterns
        (r'secret[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'secret_key: [REDACTED]'),
    ],
    
    # Company/project names in common patterns
    'company_info': [
        # Common proprietary document patterns
        (r'(?:CONFIDENTIAL|PROPRIETARY|INTERNAL)[:\s]+[^\n]+', lambda m: f'{m.group(0).split(":")[0] if ":" in m.group(0) else m.group(0).split()[0]}: [REDACTED]'),
    ],
}


def sanitize_path(path: str) -> str:
    """Sanitize file path while preserving structure for debugging."""
    parts = Path(path).parts
    if len(parts) <= 2:
        return path  # Too short to contain proprietary info
    
    # Keep drive/root and last 2 components (usually app-related)
    # Hash the middle parts
    sanitized = []
    for i, part in enumerate(parts):
        if i == 0:  # Drive letter or root
            sanitized.append(part)
        elif i >= len(parts) - 2:  # Last 2 parts (likely app folders/files)
            sanitized.append(part)
        else:
            # Hash middle parts but keep first 3 chars for context
            if len(part) > 3:
                h = hashlib.md5(part.encode()).hexdigest()[:6]
                sanitized.append(f"{part[:3]}_{h}")
            else:
                sanitized.append(part)
    
    return str(Path(*sanitized))


def sanitize_url(url: str) -> str:
    """Sanitize URL while preserving structure."""
    # Keep protocol and path structure, hash domain
    match = re.match(r'(https?://)([^/]+)(.*)', url)
    if match:
        protocol, domain, path = match.groups()
        # Hash domain but keep TLD hint
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            tld = domain_parts[-1]
            h = hashlib.md5(domain.encode()).hexdigest()[:8]
            return f"{protocol}[{h}].{tld}{path[:20] if len(path) > 20 else path}"
    return '[URL]'


def sanitize_text(text: str, patterns: Dict[str, List] = None) -> str:
    """Apply all sanitization patterns to text."""
    if patterns is None:
        patterns = DEFAULT_SANITIZE_PATTERNS
    
    result = text
    for category, pattern_list in patterns.items():
        for pattern_def in pattern_list:
            if len(pattern_def) == 2:
                pattern, replacement = pattern_def
                if callable(replacement):
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                else:
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


# =============================================================================
# ERROR ENTRY DATA STRUCTURE
# =============================================================================

@dataclass
class ErrorEntry:
    """Structured error entry with all debugging context."""
    
    # Error identification
    error_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Error details
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    
    # Context
    module: str = ""
    function: str = ""
    line_number: int = 0
    
    # Request context (for API errors)
    request_method: str = ""
    request_path: str = ""
    request_args: Dict[str, Any] = field(default_factory=dict)
    
    # Application state
    app_state: Dict[str, Any] = field(default_factory=dict)
    
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Severity
    severity: str = "ERROR"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def sanitize(self) -> 'ErrorEntry':
        """Return a sanitized copy of this error entry."""
        return ErrorEntry(
            error_id=self.error_id,
            timestamp=self.timestamp,
            error_type=self.error_type,
            error_message=sanitize_text(self.error_message),
            stack_trace=sanitize_text(self.stack_trace),
            module=self.module,
            function=self.function,
            line_number=self.line_number,
            request_method=self.request_method,
            request_path=self.request_path,
            request_args={k: sanitize_text(str(v)) for k, v in self.request_args.items()},
            app_state={k: sanitize_text(str(v)) for k, v in self.app_state.items()},
            context={k: sanitize_text(str(v)) for k, v in self.context.items()},
            severity=self.severity,
        )


@dataclass
class RequestLogEntry:
    """Log entry for HTTP requests."""
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    method: str = ""
    path: str = ""
    status_code: int = 0
    duration_ms: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class SystemInfo:
    """System environment snapshot."""
    
    # Python info
    python_version: str = ""
    python_executable: str = ""
    
    # Platform info
    platform_system: str = ""
    platform_release: str = ""
    platform_machine: str = ""
    
    # App info
    app_version: str = ""
    app_directory: str = ""
    
    # Dependencies
    installed_packages: Dict[str, str] = field(default_factory=dict)
    
    # Configuration (sanitized)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Resource info
    working_directory: str = ""
    temp_directory: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def capture(cls) -> 'SystemInfo':
        """Capture current system information."""
        from pathlib import Path
        
        # Get installed packages
        packages = {}
        try:
            import pkg_resources
            for pkg in pkg_resources.working_set:
                packages[pkg.key] = pkg.version
        except Exception:
            packages = {"error": "Could not enumerate packages"}
        
        # Get app directory
        app_dir = Path(__file__).parent
        
        # Get config (sanitized)
        config_snapshot = {}
        try:
            config_path = app_dir / 'config.json'
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    config_snapshot = json.load(f)
                # Remove any sensitive keys
                for key in ['secret_key', 'api_key', 'password']:
                    if key in config_snapshot:
                        config_snapshot[key] = '[REDACTED]'
        except Exception as e:
            config_snapshot = {"error": str(e)}
        
        return cls(
            python_version=platform.python_version(),
            python_executable=sanitize_path(sys.executable),
            platform_system=platform.system(),
            platform_release=platform.release(),
            platform_machine=platform.machine(),
            app_version=__version__,
            app_directory=sanitize_path(str(app_dir)),
            installed_packages=packages,
            config_snapshot=config_snapshot,
            working_directory=sanitize_path(os.getcwd()),
            temp_directory=sanitize_path(str(app_dir / 'temp')),
        )


# =============================================================================
# DIAGNOSTIC COLLECTOR (Singleton)
# =============================================================================

class DiagnosticCollector:
    """
    Singleton collector for errors, warnings, and diagnostic data.
    Thread-safe with automatic rotation and memory limits.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Limits
    MAX_ERRORS = 500
    MAX_REQUESTS = 1000
    MAX_WARNINGS = 200
    
    def __init__(self):
        self.errors: deque = deque(maxlen=self.MAX_ERRORS)
        self.warnings: deque = deque(maxlen=self.MAX_WARNINGS)
        self.request_log: deque = deque(maxlen=self.MAX_REQUESTS)
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start = datetime.now().isoformat()
        self._error_counts: Dict[str, int] = {}  # Track error frequency
        self._lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'DiagnosticCollector':
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the collector (for testing)."""
        with cls._lock:
            cls._instance = None
    
    def capture_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR",
        request_info: Optional[Dict[str, Any]] = None,
        app_state: Optional[Dict[str, Any]] = None,
    ) -> ErrorEntry:
        """
        Capture an error with full context.
        
        Args:
            exception: The exception that occurred
            context: Additional context about what was happening
            severity: ERROR, CRITICAL, WARNING
            request_info: HTTP request details if applicable
            app_state: Current application state snapshot
        
        Returns:
            The created ErrorEntry
        """
        # Extract stack trace
        tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
        stack_trace = ''.join(tb)
        
        # Extract location info from traceback
        module = ""
        function = ""
        line_number = 0
        if exception.__traceback__:
            tb_frame = exception.__traceback__
            while tb_frame.tb_next:
                tb_frame = tb_frame.tb_next
            module = tb_frame.tb_frame.f_code.co_filename
            function = tb_frame.tb_frame.f_code.co_name
            line_number = tb_frame.tb_lineno
        
        # Create entry
        entry = ErrorEntry(
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=stack_trace,
            module=module,
            function=function,
            line_number=line_number,
            request_method=request_info.get('method', '') if request_info else '',
            request_path=request_info.get('path', '') if request_info else '',
            request_args=request_info.get('args', {}) if request_info else {},
            app_state=app_state or {},
            context=context or {},
            severity=severity,
        )
        
        # Track error frequency
        error_key = f"{entry.error_type}:{entry.module}:{entry.line_number}"
        with self._lock:
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
            
            if severity in ("ERROR", "CRITICAL"):
                self.errors.append(entry)
            else:
                self.warnings.append(entry)
        
        return entry
    
    def capture_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorEntry:
        """Capture a warning (non-exception event)."""
        entry = ErrorEntry(
            error_type="Warning",
            error_message=message,
            context=context or {},
            severity="WARNING",
        )
        
        with self._lock:
            self.warnings.append(entry)
        
        return entry
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        """Log an HTTP request for diagnostics."""
        entry = RequestLogEntry(
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error,
        )
        
        with self._lock:
            self.request_log.append(entry)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of captured errors."""
        with self._lock:
            errors_by_type = {}
            for entry in self.errors:
                key = entry.error_type
                if key not in errors_by_type:
                    errors_by_type[key] = 0
                errors_by_type[key] += 1
            
            return {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'errors_by_type': errors_by_type,
                'most_frequent': sorted(
                    self._error_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
            }
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        with self._lock:
            if not self.request_log:
                return {'total_requests': 0}
            
            total = len(self.request_log)
            errors = sum(1 for r in self.request_log if r.status_code >= 400)
            durations = [r.duration_ms for r in self.request_log]
            
            return {
                'total_requests': total,
                'error_count': errors,
                'error_rate': f"{(errors/total)*100:.1f}%" if total else "0%",
                'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'status_codes': self._count_status_codes(),
            }
    
    def _count_status_codes(self) -> Dict[str, int]:
        """Count requests by status code category."""
        counts = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0}
        for entry in self.request_log:
            if 200 <= entry.status_code < 300:
                counts['2xx'] += 1
            elif 300 <= entry.status_code < 400:
                counts['3xx'] += 1
            elif 400 <= entry.status_code < 500:
                counts['4xx'] += 1
            elif entry.status_code >= 500:
                counts['5xx'] += 1
        return counts
    
    def export_diagnostics(
        self,
        include_system_info: bool = True,
        include_request_log: bool = True,
        sanitize: bool = True,
        max_errors: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Export all diagnostic data as a dictionary.
        
        Args:
            include_system_info: Include system/environment snapshot
            include_request_log: Include HTTP request log
            sanitize: Apply sanitization to remove proprietary content
            max_errors: Limit number of errors to include (None = all)
        
        Returns:
            Dictionary with all diagnostic data
        """
        with self._lock:
            # Get errors (optionally limited)
            errors = list(self.errors)
            if max_errors:
                errors = errors[-max_errors:]
            
            warnings = list(self.warnings)
            
            # Sanitize if requested
            if sanitize:
                errors = [e.sanitize().to_dict() for e in errors]
                warnings = [e.sanitize().to_dict() for e in warnings]
            else:
                errors = [e.to_dict() for e in errors]
                warnings = [e.to_dict() for e in warnings]
            
            result = {
                'diagnostic_export': {
                    'version': __version__,
                    'export_timestamp': datetime.now().isoformat(),
                    'session_id': self.session_id,
                    'session_start': self.session_start,
                    'sanitized': sanitize,
                },
                'summary': self.get_error_summary(),
                'errors': errors,
                'warnings': warnings,
            }
            
            if include_request_log:
                result['request_stats'] = self.get_request_stats()
                result['recent_requests'] = [
                    r.to_dict() for r in list(self.request_log)[-100:]
                ]
            
            if include_system_info:
                result['system_info'] = SystemInfo.capture().to_dict()
                # Add module availability and versions
                result['modules'] = self._get_module_info()
                # v3.0.114: Add database state for troubleshooting
                result['database_state'] = self._get_database_state()

            # v3.0.114: Include frontend console logs if available
            if hasattr(self, 'frontend_logs') and self.frontend_logs:
                result['frontend_logs'] = {
                    'session': getattr(self, 'frontend_session', {}),
                    'logs': list(self.frontend_logs)[-200:],  # Last 200 logs
                    'total_captured': len(self.frontend_logs),
                }

            return result
    
    def _get_module_info(self) -> Dict[str, Any]:
        """Get information about available TWR modules."""
        modules = {}

        # Core modules to check (v3.0.114: Added document_compare, statement_forge, fix_assistant)
        module_checks = [
            ('scan_history', 'ScanHistoryDB'),
            ('role_extractor_v3', 'RoleExtractor'),
            ('role_integration', 'RoleIntegration'),
            ('role_consolidation_engine', 'RoleConsolidationEngine'),
            ('role_management_studio_v3', 'RoleManagementStudio'),
            ('acronym_checker', 'AcronymChecker'),
            ('spell_checker', 'SpellChecker'),
            ('grammar_checker', 'GrammarChecker'),
            ('hyperlink_checker', 'HyperlinkChecker'),
            ('markup_engine', 'MarkupEngine'),
            ('export_module', 'ExportModule'),
            ('document_compare', 'dc_blueprint'),
            ('statement_forge', 'sf_blueprint'),
            ('docling_extractor', 'DoclingExtractor'),
            ('pdf_extractor_v2', 'PDFExtractor'),
        ]

        for module_name, class_name in module_checks:
            try:
                mod = __import__(module_name)
                version = getattr(mod, '__version__', getattr(mod, 'VERSION', 'unknown'))
                modules[module_name] = {
                    'available': True,
                    'version': str(version),
                    'has_class': hasattr(mod, class_name)
                }
            except ImportError:
                modules[module_name] = {
                    'available': False,
                    'version': None,
                    'error': 'Module not found'
                }
            except Exception as e:
                modules[module_name] = {
                    'available': False,
                    'version': None,
                    'error': str(e)
                }

        return modules

    def _get_database_state(self) -> Dict[str, Any]:
        """
        Get database state for troubleshooting (v3.0.114).
        Returns sanitized database statistics without actual content.
        """
        import sqlite3
        from contextlib import contextmanager

        @contextmanager
        def _db_conn(path):
            conn = sqlite3.connect(str(path))
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            cur = conn.cursor()
            try:
                yield (conn, cur)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        db_state = {
            'scan_history_db': {'available': False},
        }

        try:
            app_dir = Path(__file__).parent
            db_path = app_dir / 'scan_history.db'

            if db_path.exists():
                with _db_conn(db_path) as (conn, cursor):
                    # Get table stats
                    tables = {}
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    for (table_name,) in cursor.fetchall():
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        tables[table_name] = {'row_count': count}

                    # Get documents with scan counts
                    cursor.execute('''
                        SELECT
                            COUNT(*) as total_docs,
                            SUM(CASE WHEN scan_count >= 2 THEN 1 ELSE 0 END) as comparable_docs,
                            MAX(scan_count) as max_scans,
                            AVG(scan_count) as avg_scans
                        FROM documents
                    ''')
                    row = cursor.fetchone()

                    # Get recent scan info
                    cursor.execute('''
                        SELECT COUNT(*), MIN(scan_time), MAX(scan_time)
                        FROM scans
                    ''')
                    scan_row = cursor.fetchone()

                db_state['scan_history_db'] = {
                    'available': True,
                    'path': sanitize_path(str(db_path)),
                    'tables': tables,
                    'documents': {
                        'total': row[0] or 0,
                        'comparable': row[1] or 0,
                        'max_scans_per_doc': row[2] or 0,
                        'avg_scans_per_doc': round(row[3] or 0, 2),
                    },
                    'scans': {
                        'total': scan_row[0] or 0,
                        'oldest': scan_row[1],
                        'newest': scan_row[2],
                    }
                }
            else:
                db_state['scan_history_db'] = {
                    'available': False,
                    'error': 'Database file not found',
                    'expected_path': sanitize_path(str(db_path)),
                }
        except Exception as e:
            db_state['scan_history_db']['error'] = str(e)

        return db_state


# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def setup_flask_error_capture(app):
    """
    Set up automatic error capture for a Flask application.
    
    Usage:
        from diagnostic_export import setup_flask_error_capture
        setup_flask_error_capture(app)
    """
    from flask import request, g
    from functools import wraps
    import time
    
    collector = DiagnosticCollector.get_instance()
    
    @app.before_request
    def before_request():
        g.request_start = time.time()
    
    @app.after_request
    def after_request(response):
        # Log request
        # Handle both datetime and float types for request_start
        start = g.get('request_start', None)
        if start is None:
            duration_ms = 0
        elif isinstance(start, (int, float)):
            duration_ms = (time.time() - start) * 1000
        else:
            # Assume datetime object
            try:
                duration_ms = (datetime.now() - start).total_seconds() * 1000
            except Exception:
                duration_ms = 0
        collector.log_request(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            error=None if response.status_code < 400 else f"HTTP {response.status_code}",
        )
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Capture the error
        collector.capture_error(
            exception=e,
            severity="CRITICAL" if isinstance(e, (SystemError, MemoryError)) else "ERROR",
            request_info={
                'method': request.method,
                'path': request.path,
                'args': dict(request.args),
            },
            context={
                'endpoint': request.endpoint,
                'url': request.url,
            },
        )
        
        # Re-raise to let Flask handle the response
        raise e
    
    return collector


def create_error_capture_decorator():
    """
    Create a decorator for capturing errors in any function.
    
    Usage:
        @capture_errors
        def my_function():
            ...
    """
    collector = DiagnosticCollector.get_instance()
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                collector.capture_error(
                    exception=e,
                    context={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()),
                    },
                )
                raise
        return wrapper
    
    return decorator


# Convenience decorator
import functools
capture_errors = create_error_capture_decorator()


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_diagnostics(
    output_path: Optional[str] = None,
    include_system_info: bool = True,
    include_request_log: bool = True,
    sanitize: bool = True,
    format: str = 'json',
) -> str:
    """
    Export diagnostics to a file.
    
    Args:
        output_path: Path to save the export (default: auto-generated in logs/)
        include_system_info: Include system environment snapshot
        include_request_log: Include HTTP request log
        sanitize: Apply sanitization (recommended for sharing)
        format: 'json' or 'txt'
    
    Returns:
        Path to the exported file
    """
    collector = DiagnosticCollector.get_instance()
    
    # Get diagnostic data
    data = collector.export_diagnostics(
        include_system_info=include_system_info,
        include_request_log=include_request_log,
        sanitize=sanitize,
    )
    
    # Generate output path if not provided
    if not output_path:
        app_dir = Path(__file__).parent
        logs_dir = app_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagnostic_export_{timestamp}.{format}"
        output_path = str(logs_dir / filename)
    
    # Write the file
    if format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    else:
        # Text format for human readability
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(format_diagnostic_report(data))
    
    return output_path


def format_diagnostic_report(data: Dict[str, Any]) -> str:
    """Format diagnostic data as a human-readable text report."""
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append("TECHWRITERREVIEW DIAGNOSTIC REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Export info
    export_info = data.get('diagnostic_export', {})
    lines.append(f"Export Version:    {export_info.get('version', 'unknown')}")
    lines.append(f"Export Timestamp:  {export_info.get('export_timestamp', 'unknown')}")
    lines.append(f"Session ID:        {export_info.get('session_id', 'unknown')}")
    lines.append(f"Session Start:     {export_info.get('session_start', 'unknown')}")
    lines.append(f"Sanitized:         {export_info.get('sanitized', True)}")
    lines.append("")
    
    # Summary
    summary = data.get('summary', {})
    lines.append("-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Total Errors:      {summary.get('total_errors', 0)}")
    lines.append(f"Total Warnings:    {summary.get('total_warnings', 0)}")
    lines.append("")
    
    if summary.get('errors_by_type'):
        lines.append("Errors by Type:")
        for error_type, count in summary['errors_by_type'].items():
            lines.append(f"  - {error_type}: {count}")
        lines.append("")
    
    if summary.get('most_frequent'):
        lines.append("Most Frequent Errors:")
        for error_key, count in summary['most_frequent'][:5]:
            lines.append(f"  - {error_key}: {count}x")
        lines.append("")
    
    # Request stats
    if 'request_stats' in data:
        stats = data['request_stats']
        lines.append("-" * 70)
        lines.append("REQUEST STATISTICS")
        lines.append("-" * 70)
        lines.append(f"Total Requests:    {stats.get('total_requests', 0)}")
        lines.append(f"Error Count:       {stats.get('error_count', 0)}")
        lines.append(f"Error Rate:        {stats.get('error_rate', '0%')}")
        lines.append(f"Avg Duration:      {stats.get('avg_duration_ms', 0):.1f}ms")
        lines.append(f"Max Duration:      {stats.get('max_duration_ms', 0):.1f}ms")
        if stats.get('status_codes'):
            lines.append(f"Status Codes:      {stats['status_codes']}")
        lines.append("")
    
    # System info
    if 'system_info' in data:
        info = data['system_info']
        lines.append("-" * 70)
        lines.append("SYSTEM INFORMATION")
        lines.append("-" * 70)
        lines.append(f"App Version:       {info.get('app_version', 'unknown')}")
        lines.append(f"Python Version:    {info.get('python_version', 'unknown')}")
        lines.append(f"Platform:          {info.get('platform_system', '')} {info.get('platform_release', '')}")
        lines.append(f"Machine:           {info.get('platform_machine', 'unknown')}")
        lines.append(f"App Directory:     {info.get('app_directory', 'unknown')}")
        lines.append("")
        
        # Key packages
        packages = info.get('installed_packages', {})
        key_packages = ['flask', 'python-docx', 'pdfplumber', 'werkzeug', 'language-tool-python']
        lines.append("Key Packages:")
        for pkg in key_packages:
            version = packages.get(pkg, 'not installed')
            lines.append(f"  - {pkg}: {version}")
        lines.append("")
    
    # Errors (detailed)
    errors = data.get('errors', [])
    if errors:
        lines.append("-" * 70)
        lines.append(f"ERRORS ({len(errors)} total)")
        lines.append("-" * 70)
        
        for i, error in enumerate(errors[-20:], 1):  # Last 20 errors
            lines.append("")
            lines.append(f"[{i}] {error.get('severity', 'ERROR')}: {error.get('error_type', 'Unknown')}")
            lines.append(f"    ID:        {error.get('error_id', 'unknown')}")
            lines.append(f"    Timestamp: {error.get('timestamp', 'unknown')}")
            lines.append(f"    Message:   {error.get('error_message', '')[:100]}")
            lines.append(f"    Module:    {error.get('module', '')}:{error.get('line_number', 0)}")
            lines.append(f"    Function:  {error.get('function', '')}")
            
            if error.get('request_path'):
                lines.append(f"    Request:   {error.get('request_method', '')} {error.get('request_path', '')}")
            
            if error.get('context'):
                lines.append(f"    Context:   {json.dumps(error['context'], default=str)[:100]}")
            
            # Stack trace (truncated)
            if error.get('stack_trace'):
                trace_lines = error['stack_trace'].strip().split('\n')
                lines.append("    Stack Trace:")
                for trace_line in trace_lines[-10:]:  # Last 10 lines
                    lines.append(f"      {trace_line}")
    
    # Warnings
    warnings = data.get('warnings', [])
    if warnings:
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"WARNINGS ({len(warnings)} total)")
        lines.append("-" * 70)

        for warning in warnings[-10:]:  # Last 10 warnings
            lines.append(f"  [{warning.get('timestamp', '')}] {warning.get('error_message', '')[:80]}")

    # v3.0.114: Database State
    if 'database_state' in data:
        db_state = data['database_state']
        lines.append("")
        lines.append("-" * 70)
        lines.append("DATABASE STATE")
        lines.append("-" * 70)

        scan_db = db_state.get('scan_history_db', {})
        if scan_db.get('available'):
            lines.append(f"Path:              {scan_db.get('path', 'unknown')}")
            docs = scan_db.get('documents', {})
            lines.append(f"Total Documents:   {docs.get('total', 0)}")
            lines.append(f"Comparable Docs:   {docs.get('comparable', 0)} (with 2+ scans)")
            lines.append(f"Max Scans/Doc:     {docs.get('max_scans_per_doc', 0)}")
            scans = scan_db.get('scans', {})
            lines.append(f"Total Scans:       {scans.get('total', 0)}")
            lines.append(f"Oldest Scan:       {scans.get('oldest', 'N/A')}")
            lines.append(f"Newest Scan:       {scans.get('newest', 'N/A')}")
            tables = scan_db.get('tables', {})
            if tables:
                lines.append("Tables:")
                for table, info in tables.items():
                    lines.append(f"  - {table}: {info.get('row_count', 0)} rows")
        else:
            lines.append(f"Status:            NOT AVAILABLE")
            lines.append(f"Error:             {scan_db.get('error', 'Unknown')}")
        lines.append("")

    # v3.0.114: Frontend Console Logs
    if 'frontend_logs' in data:
        fe_data = data['frontend_logs']
        fe_logs = fe_data.get('logs', [])
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"FRONTEND CONSOLE LOGS ({len(fe_logs)} captured)")
        lines.append("-" * 70)

        session = fe_data.get('session', {})
        if session:
            stats = session.get('stats', {})
            lines.append(f"Session ID:        {stats.get('sessionId', 'unknown')}")
            lines.append(f"User Agent:        {session.get('userAgent', 'unknown')[:60]}...")
            by_level = stats.get('byLevel', {})
            if by_level:
                lines.append(f"Log Counts:        {by_level}")
            lines.append("")

        # Show errors and warnings from frontend
        fe_errors = [l for l in fe_logs if l.get('level') in ('ERROR', 'UNCAUGHT_ERROR', 'UNHANDLED_REJECTION')]
        fe_warns = [l for l in fe_logs if l.get('level') == 'WARN']

        if fe_errors:
            lines.append(f"Frontend Errors ({len(fe_errors)}):")
            for log in fe_errors[-10:]:  # Last 10
                lines.append(f"  [{log.get('timestamp', '')}] {log.get('level')}")
                lines.append(f"    {log.get('message', '')[:100]}")
                if log.get('location'):
                    lines.append(f"    at {log.get('location')}")
            lines.append("")

        if fe_warns:
            lines.append(f"Frontend Warnings ({len(fe_warns)}):")
            for log in fe_warns[-5:]:  # Last 5
                lines.append(f"  [{log.get('timestamp', '')}] {log.get('message', '')[:80]}")
            lines.append("")

    # v3.0.114: Module Availability
    if 'modules' in data:
        modules = data['modules']
        lines.append("")
        lines.append("-" * 70)
        lines.append("MODULE STATUS")
        lines.append("-" * 70)

        available = [(k, v) for k, v in modules.items() if v.get('available')]
        unavailable = [(k, v) for k, v in modules.items() if not v.get('available')]

        if available:
            lines.append("Available:")
            for name, info in available:
                lines.append(f"  [OK]   {name} v{info.get('version', '?')}")

        if unavailable:
            lines.append("Unavailable:")
            for name, info in unavailable:
                lines.append(f"  [--]   {name}: {info.get('error', 'Not found')}")
        lines.append("")

    # Footer
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF DIAGNOSTIC REPORT")
    lines.append("=" * 70)

    return '\n'.join(lines)


# =============================================================================
# API ENDPOINT FOR FRONTEND
# =============================================================================

def register_diagnostic_routes(app):
    """
    Register diagnostic API routes with a Flask app.
    
    Usage:
        from diagnostic_export import register_diagnostic_routes
        register_diagnostic_routes(app)
    
    v2.9.3 B20/B21/B25: Fixed export not working, improved error handling
    """
    from flask import jsonify, send_file, request
    import logging
    
    logger = logging.getLogger('diagnostic_export')
    
    @app.route('/api/diagnostics/summary')
    def get_diagnostic_summary():
        """Get diagnostic summary (no sensitive data)."""
        try:
            collector = DiagnosticCollector.get_instance()
            return jsonify({
                'success': True,
                'session_id': collector.session_id,
                'session_start': collector.session_start,
                'error_count': len(collector.errors),
                'warning_count': len(collector.warnings),
                'request_count': len(collector.request_log),
                'summary': collector.get_error_summary(),
            })
        except Exception as e:
            logger.exception(f"Error getting diagnostic summary: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/diagnostics/export', methods=['GET', 'POST'])
    def export_diagnostic_file():
        """
        Export diagnostic data to a downloadable file.
        
        v2.9.1 D4: Added GET method support and filepath in response
        v2.9.3 B20/B21/B25: Fixed export not working, added comprehensive error handling
        v2.9.5 #37-38: Added timeout protection to prevent server hangs
        
        GET: Returns JSON with filepath (for email attachment workflow)
        POST: Returns the file for direct download
        """
        import threading
        
        try:
            format = request.args.get('format', 'json') if request.method == 'GET' else (request.get_json() or {}).get('format', 'json')
            include_system = request.args.get('include_system', 'true').lower() == 'true' if request.method == 'GET' else (request.get_json() or {}).get('include_system_info', True)
            include_requests = request.args.get('include_requests', 'true').lower() == 'true' if request.method == 'GET' else (request.get_json() or {}).get('include_request_log', True)
            
            logger.info(f"{request.method} export request: format={format}")
            
            # v2.9.5: Run export with timeout to prevent blocking
            # BUG-C02 FIX: Increased timeout to 60s and limited errors to prevent huge exports
            result = [None]
            error = [None]

            def do_export():
                try:
                    collector = DiagnosticCollector.get_instance()
                    # BUG-C02 FIX: Limit to last 500 errors to prevent timeout on large exports
                    data = collector.export_diagnostics(
                        include_system_info=include_system,
                        include_request_log=include_requests,
                        sanitize=True,
                        max_errors=500,  # Limit errors to prevent timeout
                    )

                    # Generate output file
                    app_dir = Path(__file__).parent
                    logs_dir = app_dir / 'logs'
                    logs_dir.mkdir(exist_ok=True)

                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"diagnostic_export_{timestamp}.{format}"
                    output_path = str(logs_dir / filename)

                    if format == 'json':
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    else:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(format_diagnostic_report(data))

                    result[0] = output_path
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=do_export)
            thread.daemon = True
            thread.start()
            thread.join(timeout=60)  # BUG-C02 FIX: Increased to 60 second timeout

            if thread.is_alive():
                logger.error("Diagnostic export timed out after 60s")
                return jsonify({
                    'success': False,
                    'error': 'Export timed out after 60s. Try exporting with fewer options.'
                }), 504
            
            if error[0]:
                raise error[0]
            
            filepath = result[0]
            logger.info(f"Export file created: {filepath}")
            
            # Verify file exists before sending
            if not Path(filepath).exists():
                logger.error(f"Export file not found: {filepath}")
                return jsonify({
                    'success': False,
                    'error': 'Export file could not be created'
                }), 500
            
            if request.method == 'GET':
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'filename': Path(filepath).name
                })
            
            # POST: Return downloadable file
            return send_file(
                filepath,
                as_attachment=True,
                download_name=Path(filepath).name,
                mimetype='application/json' if format == 'json' else 'text/plain',
            )
        except Exception as e:
            logger.exception(f"Error exporting diagnostics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/diagnostics/capture', methods=['POST'])
    def capture_frontend_error():
        """Capture errors reported from the frontend."""
        try:
            data = request.get_json() or {}
            
            collector = DiagnosticCollector.get_instance()
            
            # Create a pseudo-exception for frontend errors
            class FrontendError(Exception):
                pass
            
            error = FrontendError(data.get('message', 'Unknown frontend error'))
            
            collector.capture_error(
                exception=error,
                context={
                    'source': 'frontend',
                    'component': data.get('component', ''),
                    'stack': data.get('stack', ''),
                    'userAgent': data.get('userAgent', ''),
                },
                severity=data.get('severity', 'ERROR'),
            )
            
            return jsonify({'success': True, 'captured': True})
        except Exception as e:
            logger.exception(f"Error capturing frontend error: {e}")
            return jsonify({
                'success': False,
                'captured': False,
                'error': str(e)
            }), 500

    @app.route('/api/diagnostics/frontend-logs', methods=['POST'])
    def receive_frontend_logs():
        """
        Receive console logs from the frontend for diagnostic export (v3.0.114).
        Called by ConsoleCapture.submitToServer().
        """
        try:
            data = request.get_json() or {}
            logs = data.get('logs', [])
            stats = data.get('stats', {})

            collector = DiagnosticCollector.get_instance()

            # Store frontend logs in collector
            if not hasattr(collector, 'frontend_logs'):
                collector.frontend_logs = []

            # Add the logs (limit to prevent memory issues)
            MAX_FRONTEND_LOGS = 500
            collector.frontend_logs.extend(logs)
            if len(collector.frontend_logs) > MAX_FRONTEND_LOGS:
                collector.frontend_logs = collector.frontend_logs[-MAX_FRONTEND_LOGS:]

            # Store metadata
            collector.frontend_session = {
                'stats': stats,
                'userAgent': data.get('userAgent', ''),
                'url': sanitize_text(data.get('url', '')),
                'received_at': datetime.now().isoformat(),
            }

            logger.info(f"Received {len(logs)} frontend logs (total: {len(collector.frontend_logs)})")

            return jsonify({
                'success': True,
                'received': len(logs),
                'total_stored': len(collector.frontend_logs),
            })
        except Exception as e:
            logger.exception(f"Error receiving frontend logs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


# =============================================================================
# TROUBLESHOOTING PACKAGE (v2.9.4.2+)
# =============================================================================
# Creates a self-contained diagnostic package for troubleshooting.

class AITroubleshootPackage:
    """
    Creates a comprehensive diagnostic package optimized for troubleshooting.

    The exported file is designed to be self-contained with all information
    needed to diagnose and fix issues.
    """
    
    def __init__(self):
        self.collector = DiagnosticCollector.get_instance()
        self.manifest = {}
        self.file_checksums = {}
        self.user_actions = []
        self.console_errors = []
        self.code_context = {}
        
    def load_manifest(self) -> Dict[str, Any]:
        """Load the MANIFEST.json if it exists."""
        try:
            manifest_path = Path(__file__).parent / 'MANIFEST.json'
            if manifest_path.exists():
                with open(manifest_path, encoding='utf-8') as f:
                    self.manifest = json.load(f)
            else:
                # Create basic manifest from version.json
                version_path = Path(__file__).parent / 'version.json'
                if version_path.exists():
                    with open(version_path, encoding='utf-8') as f:
                        v = json.load(f)
                        self.manifest = {
                            'tool_name': 'AEGIS',
                            'current_version': v.get('version', 'unknown'),
                            'last_updated': v.get('build_date', 'unknown'),
                            'codename': v.get('codename', '')
                        }
        except Exception as e:
            self.manifest = {'error': str(e)}
        
        return self.manifest
    
    def calculate_file_checksums(self, files: List[str] = None) -> Dict[str, str]:
        """
        Calculate MD5 checksums for critical files.
        This helps identify if files are corrupted or mismatched.
        """
        if files is None:
            # Default critical files
            files = [
                'app.py',
                'core.py',
                'static/js/app.js',
                'templates/index.html',
                'version.json',
                'update_manager.py',
                'diagnostic_export.py',
                'markup_engine.py',
                'scan_history.py'
            ]
        
        app_dir = Path(__file__).parent
        
        for file in files:
            file_path = app_dir / file
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        checksum = hashlib.md5(f.read()).hexdigest()
                    # Also get file size for reference
                    size = file_path.stat().st_size
                    self.file_checksums[file] = {
                        'md5': checksum,
                        'size': size
                    }
                except Exception as e:
                    self.file_checksums[file] = {'error': str(e)}
            else:
                self.file_checksums[file] = {'error': 'FILE_NOT_FOUND'}
        
        return self.file_checksums
    
    def capture_user_action(self, action: str, details: Dict[str, Any] = None):
        """
        Record a user action. Call this before operations that might fail.
        This creates a breadcrumb trail for troubleshooting.
        """
        self.user_actions.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {}
        })
        
        # Keep only last 50 actions
        if len(self.user_actions) > 50:
            self.user_actions = self.user_actions[-50:]
    
    def capture_console_error(self, error: Dict[str, Any]):
        """
        Capture a JavaScript console error from the frontend.
        Called via /api/diagnostics/capture-console endpoint.
        
        v2.9.4.2: Now includes correlationId for backend correlation.
        """
        self.console_errors.append({
            'timestamp': datetime.now().isoformat(),
            'message': error.get('message', ''),
            'source': error.get('source', ''),
            'lineno': error.get('lineno', 0),
            'colno': error.get('colno', 0),
            'stack': error.get('stack', ''),
            'type': error.get('type', 'error'),
            'correlationId': error.get('correlationId', None),  # v2.9.4.2: For backend correlation
            'url': error.get('url', '')  # v2.9.4.2: For fetch errors
        })
        
        # Keep only last 100 console errors
        if len(self.console_errors) > 100:
            self.console_errors = self.console_errors[-100:]
    
    def extract_code_context(self, file_path: str, line_number: int, context_lines: int = 10) -> str:
        """
        Extract code around an error location for context.
        """
        try:
            full_path = Path(__file__).parent / file_path
            if not full_path.exists():
                return f"[File not found: {file_path}]"
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            result = []
            for i in range(start, end):
                marker = ">>> " if i == line_number - 1 else "    "
                result.append(f"{i+1:4d}{marker}{lines[i].rstrip()}")
            
            return '\n'.join(result)
        except Exception as e:
            return f"[Error extracting code: {e}]"
    
    def _detect_known_patterns(self, errors: List) -> List[Dict[str, str]]:
        """
        Detect known error patterns that have documented solutions.
        """
        patterns = []
        
        for error in errors:
            if hasattr(error, 'error_message'):
                msg = str(error.error_message)
                error_type = error.error_type
            else:
                msg = str(error.get('error_message', ''))
                error_type = error.get('error_type', '')
            
            # JavaScript syntax errors
            if 'SyntaxError' in error_type and 'Unexpected token' in msg:
                patterns.append({
                    'pattern': 'JS_SYNTAX_ERROR',
                    'description': 'JavaScript syntax error - likely malformed JS file',
                    'suggested_fix': 'Check app.js for syntax errors. Run: node --check static/js/app.js',
                    'severity': 'CRITICAL'
                })
            
            # Import errors
            if 'ImportError' in error_type or 'ModuleNotFoundError' in error_type:
                patterns.append({
                    'pattern': 'MISSING_MODULE',
                    'description': f'Missing Python module: {msg}',
                    'suggested_fix': 'Run: pip install -r requirements.txt',
                    'severity': 'HIGH'
                })
            
            # Database errors
            if 'sqlite' in msg.lower() or 'database' in msg.lower():
                patterns.append({
                    'pattern': 'DATABASE_ERROR',
                    'description': 'Database access error',
                    'suggested_fix': 'Check database file permissions and integrity. Try deleting scan_history.db to reset.',
                    'severity': 'MEDIUM'
                })
            
            # COM errors (Windows Office)
            if 'COM' in msg or '-2147' in msg:
                patterns.append({
                    'pattern': 'COM_ERROR',
                    'description': 'Microsoft Office COM error',
                    'suggested_fix': 'Ensure Microsoft Word is installed, not running, and try running as Administrator',
                    'severity': 'MEDIUM'
                })
            
            # File not found
            if 'FileNotFoundError' in error_type or 'No such file' in msg:
                patterns.append({
                    'pattern': 'FILE_NOT_FOUND',
                    'description': 'Required file missing',
                    'suggested_fix': 'Check installation completeness. May need fresh install.',
                    'severity': 'HIGH'
                })
            
            # JSON decode errors
            if 'JSONDecodeError' in error_type or 'json' in msg.lower():
                patterns.append({
                    'pattern': 'JSON_ERROR',
                    'description': 'JSON parsing error - possibly corrupted config or response',
                    'suggested_fix': 'Check config.json for valid JSON. May be receiving HTML error page instead of JSON.',
                    'severity': 'MEDIUM'
                })
            
            # Permission errors
            if 'PermissionError' in error_type or 'Access is denied' in msg:
                patterns.append({
                    'pattern': 'PERMISSION_ERROR',
                    'description': 'File or resource access denied',
                    'suggested_fix': 'Run as Administrator or check file permissions',
                    'severity': 'MEDIUM'
                })
        
        # Deduplicate
        seen = set()
        unique_patterns = []
        for p in patterns:
            if p['pattern'] not in seen:
                seen.add(p['pattern'])
                unique_patterns.append(p)
        
        return unique_patterns
    
    def generate_ai_summary(self) -> Dict[str, Any]:
        """
        Generate a structured summary optimized for AI troubleshooting.
        """
        errors = list(self.collector.errors)
        warnings = list(self.collector.warnings)
        
        # Categorize errors
        error_categories = {}
        for error in errors:
            cat = error.error_type if hasattr(error, 'error_type') else error.get('error_type', 'Unknown')
            if cat not in error_categories:
                error_categories[cat] = []
            error_categories[cat].append(error)
        
        # Find most frequent errors
        error_frequency = {}
        for error in errors:
            if hasattr(error, 'error_type'):
                key = f"{error.error_type}:{error.module}:{error.line_number}"
            else:
                key = f"{error.get('error_type', 'unknown')}:{error.get('module', '')}:{error.get('line_number', 0)}"
            error_frequency[key] = error_frequency.get(key, 0) + 1
        
        top_errors = sorted(error_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Check for known patterns
        known_patterns = self._detect_known_patterns(errors)
        
        # Determine overall severity
        if any(p.get('severity') == 'CRITICAL' for p in known_patterns):
            overall_severity = 'CRITICAL'
        elif any(p.get('severity') == 'HIGH' for p in known_patterns):
            overall_severity = 'HIGH'
        elif known_patterns:
            overall_severity = 'MEDIUM'
        elif errors:
            overall_severity = 'LOW'
        else:
            overall_severity = 'NONE'
        
        return {
            'overall_severity': overall_severity,
            'total_errors': len(errors),
            'total_warnings': len(warnings),
            'error_categories': {k: len(v) for k, v in error_categories.items()},
            'most_frequent_errors': top_errors,
            'known_patterns_detected': known_patterns,
            'has_frontend_errors': len(self.console_errors) > 0,
            'console_error_count': len(self.console_errors),
            'recent_user_actions': self.user_actions[-10:] if self.user_actions else [],
            'action_count': len(self.user_actions)
        }
    
    def export(self, format: str = 'json') -> str:
        """
        Export the complete AI troubleshooting package.
        
        Returns:
            Path to the exported file
        """
        # Gather all data
        self.load_manifest()
        self.calculate_file_checksums()
        
        # Get code context for recent errors
        for error in list(self.collector.errors)[-5:]:
            if hasattr(error, 'module'):
                module = error.module
                line = error.line_number
            else:
                module = error.get('module', '')
                line = error.get('line_number', 0)
            
            if module and line:
                # Convert absolute path to relative
                try:
                    rel_path = Path(module).relative_to(Path(__file__).parent)
                    key = f"{rel_path}:{line}"
                    if key not in self.code_context:
                        self.code_context[key] = self.extract_code_context(str(rel_path), line)
                except Exception:
                    pass
        
        # Build the package
        package = {
            'TROUBLESHOOT_HEADER': {
                'description': 'AEGIS Diagnostic Package for Troubleshooting',
                'instructions': 'This file contains all diagnostic information needed to identify and resolve issues.',
                'generated_at': datetime.now().isoformat(),
                'tool_name': 'AEGIS',
                'tool_version': self.manifest.get('current_version', 'unknown'),
                'format_version': '1.0'
            },
            
            'MANIFEST': self.manifest,
            
            'PROBLEM_SUMMARY': self.generate_ai_summary(),
            
            'FILE_CHECKSUMS': self.file_checksums,
            
            'SYSTEM_INFO': SystemInfo.capture().to_dict(),
            
            'ERRORS': [
                e.sanitize().to_dict() if hasattr(e, 'sanitize') else e 
                for e in list(self.collector.errors)
            ],
            
            'WARNINGS': [
                e.sanitize().to_dict() if hasattr(e, 'sanitize') else e 
                for e in list(self.collector.warnings)[-20:]
            ],
            
            'CONSOLE_ERRORS': self.console_errors[-20:],
            
            'USER_ACTIONS': self.user_actions[-30:],
            
            'CODE_CONTEXT': self.code_context,
            
            'REQUEST_LOG': [
                r.to_dict() if hasattr(r, 'to_dict') else r 
                for r in list(self.collector.request_log)[-50:]
            ],
            
            'UPDATE_SYSTEM_INFO': {
                'flat_file_naming_convention': {
                    'description': 'Update files use underscore prefixes to encode destination paths',
                    'examples': {
                        'static_js_app.js.txt': 'static/js/app.js',
                        'statement_forge__export.py.txt': 'statement_forge/export.py',
                        'style.css.txt': 'static/css/style.css',
                        'index.html.txt': 'templates/index.html',
                        'app.py.txt': 'app.py (root level)'
                    }
                },
                'update_folder': 'updates/',
                'backup_folder': 'backups/'
            }
        }
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = self.manifest.get('current_version', 'unknown').replace('.', '_')
        
        # Ensure temp directory exists
        temp_dir = Path(__file__).parent / 'temp'
        temp_dir.mkdir(exist_ok=True)
        
        if format == 'json':
            filename = f"TWR_DIAG_{version}_{timestamp}.json"
            filepath = temp_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(package, f, indent=2, default=str, ensure_ascii=False)
        else:
            filename = f"TWR_DIAG_{version}_{timestamp}.txt"
            filepath = temp_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._format_as_text(package))
        
        return str(filepath)
    
    def _format_as_text(self, package: Dict) -> str:
        """Format the package as human-readable text."""
        lines = []

        lines.append("=" * 80)
        lines.append("TECHWRITERREVIEW DIAGNOSTIC PACKAGE FOR TROUBLESHOOTING")
        lines.append("=" * 80)
        lines.append("")
        lines.append("This file contains all diagnostic information needed to identify")
        lines.append("and resolve issues with AEGIS.")
        lines.append("")
        lines.append(f"Generated: {package['TROUBLESHOOT_HEADER']['generated_at']}")
        lines.append(f"Version:   {package['TROUBLESHOOT_HEADER']['tool_version']}")
        lines.append("")
        
        # Problem Summary
        lines.append("-" * 80)
        lines.append("PROBLEM SUMMARY")
        lines.append("-" * 80)
        summary = package['PROBLEM_SUMMARY']
        lines.append(f"Overall Severity: {summary['overall_severity']}")
        lines.append(f"Total Errors:     {summary['total_errors']}")
        lines.append(f"Total Warnings:   {summary['total_warnings']}")
        lines.append(f"Console Errors:   {summary['console_error_count']}")
        lines.append(f"User Actions:     {summary['action_count']}")
        lines.append("")
        
        if summary['known_patterns_detected']:
            lines.append("DETECTED PATTERNS (with suggested fixes):")
            for pattern in summary['known_patterns_detected']:
                lines.append(f"  [{pattern.get('severity', 'UNKNOWN')}] {pattern['pattern']}")
                lines.append(f"       Issue: {pattern['description']}")
                lines.append(f"       Fix:   {pattern['suggested_fix']}")
            lines.append("")
        
        if summary['most_frequent_errors']:
            lines.append("MOST FREQUENT ERRORS:")
            for error_key, count in summary['most_frequent_errors']:
                lines.append(f"  ({count}x) {error_key}")
            lines.append("")
        
        # Recent User Actions
        if summary['recent_user_actions']:
            lines.append("-" * 80)
            lines.append("RECENT USER ACTIONS (what happened before the error)")
            lines.append("-" * 80)
            for action in summary['recent_user_actions']:
                details = action.get('details', {})
                detail_str = ', '.join(f"{k}={v}" for k, v in details.items()) if details else ''
                lines.append(f"  [{action['timestamp']}] {action['action']}")
                if detail_str:
                    lines.append(f"       {detail_str}")
            lines.append("")
        
        # Console Errors
        if package['CONSOLE_ERRORS']:
            lines.append("-" * 80)
            lines.append("JAVASCRIPT CONSOLE ERRORS")
            lines.append("-" * 80)
            for error in package['CONSOLE_ERRORS'][-10:]:
                lines.append(f"  [{error['type']}] {error['message'][:150]}")
                if error.get('source'):
                    lines.append(f"       Source: {error['source']}:{error.get('lineno', '?')}:{error.get('colno', '?')}")
                if error.get('stack'):
                    # Show first 3 lines of stack
                    stack_lines = error['stack'].split('\n')[:3]
                    for sl in stack_lines:
                        lines.append(f"       {sl.strip()}")
            lines.append("")
        
        # Errors
        if package['ERRORS']:
            lines.append("-" * 80)
            lines.append(f"BACKEND ERRORS ({len(package['ERRORS'])} total, showing last 10)")
            lines.append("-" * 80)
            for i, error in enumerate(package['ERRORS'][-10:], 1):
                lines.append(f"\nError #{i}:")
                lines.append(f"  Type:     {error.get('error_type', 'Unknown')}")
                lines.append(f"  Message:  {error.get('error_message', '')[:200]}")
                lines.append(f"  Location: {error.get('module', '')}:{error.get('line_number', 0)}")
                lines.append(f"  Function: {error.get('function', '')}")
                lines.append(f"  Time:     {error.get('timestamp', '')}")
                if error.get('request_path'):
                    lines.append(f"  Request:  {error.get('request_method', '')} {error.get('request_path', '')}")
                if error.get('stack_trace'):
                    lines.append("  Stack Trace (last 10 lines):")
                    for trace_line in error['stack_trace'].split('\n')[-10:]:
                        if trace_line.strip():
                            lines.append(f"    {trace_line}")
            lines.append("")
        
        # Code Context
        if package['CODE_CONTEXT']:
            lines.append("-" * 80)
            lines.append("CODE CONTEXT (around error locations)")
            lines.append("-" * 80)
            for location, code in package['CODE_CONTEXT'].items():
                lines.append(f"\n>>> {location}:")
                lines.append(code)
            lines.append("")
        
        # File Checksums
        lines.append("-" * 80)
        lines.append("FILE CHECKSUMS (for integrity verification)")
        lines.append("-" * 80)
        for file, info in package['FILE_CHECKSUMS'].items():
            if isinstance(info, dict):
                if 'error' in info:
                    lines.append(f"  {file}: {info['error']}")
                else:
                    lines.append(f"  {file}: {info.get('md5', 'unknown')} ({info.get('size', 0)} bytes)")
            else:
                lines.append(f"  {file}: {info}")
        lines.append("")
        
        # System Info
        lines.append("-" * 80)
        lines.append("SYSTEM INFORMATION")
        lines.append("-" * 80)
        sysinfo = package['SYSTEM_INFO']
        lines.append(f"  Python:      {sysinfo.get('python_version', 'unknown')}")
        lines.append(f"  Platform:    {sysinfo.get('platform_system', '')} {sysinfo.get('platform_release', '')}")
        lines.append(f"  Machine:     {sysinfo.get('platform_machine', '')}")
        lines.append(f"  App Version: {sysinfo.get('app_version', '')}")
        lines.append(f"  App Dir:     {sysinfo.get('app_directory', '')}")
        lines.append("")
        
        # Manifest info
        if package.get('MANIFEST'):
            lines.append("-" * 80)
            lines.append("MANIFEST (version history)")
            lines.append("-" * 80)
            manifest = package['MANIFEST']
            lines.append(f"  Current Version: {manifest.get('current_version', 'unknown')}")
            lines.append(f"  Last Updated:    {manifest.get('last_updated', 'unknown')}")
            if manifest.get('version_history'):
                lines.append("  Recent Versions:")
                for vh in manifest['version_history'][:3]:
                    lines.append(f"    - {vh.get('version', '?')}: {vh.get('summary', '')}")
            lines.append("")
        
        # Update system info
        lines.append("-" * 80)
        lines.append("UPDATE SYSTEM")
        lines.append("-" * 80)
        lines.append("  To apply fixes, place update .txt files in the 'updates/' folder")
        lines.append("  and apply via Settings > Updates")
        lines.append("")
        lines.append("  File naming convention:")
        for src, dest in package['UPDATE_SYSTEM_INFO']['flat_file_naming_convention']['examples'].items():
            lines.append(f"    {src} -> {dest}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF DIAGNOSTIC PACKAGE")
        lines.append("=" * 80)
        
        return '\n'.join(lines)


# =============================================================================
# AI TROUBLESHOOT SINGLETON & HELPERS
# =============================================================================

_ai_troubleshoot_instance = None
_ai_troubleshoot_lock = threading.Lock()

def get_ai_troubleshoot() -> AITroubleshootPackage:
    """Get or create the AI troubleshoot package instance."""
    global _ai_troubleshoot_instance
    if _ai_troubleshoot_instance is None:
        with _ai_troubleshoot_lock:
            if _ai_troubleshoot_instance is None:
                _ai_troubleshoot_instance = AITroubleshootPackage()
    return _ai_troubleshoot_instance


def export_ai_troubleshoot_package(format: str = 'json') -> str:
    """
    Export a diagnostic package optimized for troubleshooting.

    Args:
        format: 'json' or 'txt'

    Returns:
        Path to the exported file
    """
    return get_ai_troubleshoot().export(format)


def log_user_action(action: str, details: Dict[str, Any] = None):
    """
    Log a user action for troubleshooting breadcrumbs.
    Call this before operations that might fail.
    """
    get_ai_troubleshoot().capture_user_action(action, details)


def capture_console_error(error: Dict[str, Any]):
    """Capture a JavaScript console error."""
    get_ai_troubleshoot().capture_console_error(error)


# =============================================================================
# ENHANCED API ROUTES FOR TROUBLESHOOTING
# =============================================================================

def register_ai_troubleshoot_routes(app):
    """
    Register enhanced diagnostic routes for troubleshooting.
    Call this in addition to register_diagnostic_routes().
    """
    from flask import jsonify, send_file, request
    import logging

    logger = logging.getLogger('troubleshoot')

    @app.route('/api/diagnostics/ai-export', methods=['GET', 'POST'])
    def export_ai_package():
        """
        Export troubleshooting package.

        v2.9.5 #37-38: Added timeout protection to prevent hangs.
        """
        import threading

        try:
            format = request.args.get('format', 'json')

            # v2.9.5: Run export with timeout to prevent blocking
            result = [None]
            error = [None]

            def do_export():
                try:
                    result[0] = export_ai_troubleshoot_package(format)
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=do_export)
            thread.daemon = True
            thread.start()
            thread.join(timeout=30)  # 30 second timeout

            if thread.is_alive():
                logger.error("Export timed out after 30s")
                return jsonify({
                    'success': False,
                    'error': 'Export timed out. Please try again.'
                }), 504

            if error[0]:
                raise error[0]

            filepath = result[0]
            logger.info(f"Troubleshoot package exported: {filepath}")

            if request.method == 'GET':
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'filename': Path(filepath).name,
                    'instructions': 'This file contains all diagnostic information needed for troubleshooting.'
                })
            else:
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=Path(filepath).name,
                    mimetype='application/json' if format == 'json' else 'text/plain'
                )
        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/diagnostics/capture-console', methods=['POST'])
    def capture_console():
        """Capture JavaScript console errors from frontend."""
        try:
            data = request.get_json() or {}
            capture_console_error(data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/diagnostics/user-action', methods=['POST'])
    def log_action():
        """Log a user action for troubleshooting breadcrumbs."""
        try:
            data = request.get_json() or {}
            log_user_action(
                data.get('action', 'unknown'),
                data.get('details', {})
            )
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("AI Troubleshoot routes registered")


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == '__main__':
    # Test the diagnostic collector
    collector = DiagnosticCollector.get_instance()
    
    # Capture a test error
    try:
        raise ValueError("Test error with some proprietary info: C:\\Users\\JohnDoe\\Documents\\secret.docx")
    except Exception as e:
        collector.capture_error(
            e,
            context={'test': True, 'email': 'john.doe@company.com'},
        )
    
    # Capture a test warning
    collector.capture_warning("Test warning message")
    
    # Log some requests
    collector.log_request('GET', '/api/review', 200, 150.5)
    collector.log_request('POST', '/api/upload', 500, 2500.0, error="Internal error")
    
    # Export
    filepath = export_diagnostics(format='txt')
    print(f"Exported diagnostics to: {filepath}")
    
    # Print the report
    with open(filepath, encoding='utf-8') as f:
        print(f.read())
