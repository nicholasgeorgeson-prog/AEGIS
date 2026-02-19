"""
Hyperlink Validator Core Engine
===============================
Core validation logic for standalone hyperlink validation.

This module orchestrates URL validation across two modes:
- offline: Format validation only (no network access)
- validator: Full HTTP validation with Windows integrated authentication,
             optimized for government and enterprise sites

Features:
- Windows integrated authentication (NTLM/Negotiate SSO)
- Robust retry logic with exponential backoff
- Government site compatibility (handling auth challenges, redirects)
- SSL certificate validation
- Soft-404 detection
- DNS resolution checks
- Suspicious URL detection

Integrates with existing AEGIS infrastructure:
- JobManager for async progress tracking
- comprehensive_hyperlink_checker for Windows SSO support
"""

import os
import time
import threading
import socket
import ssl
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from urllib.parse import urlparse
import logging

# Import models from this package
from .models import (
    ValidationRequest,
    ValidationResult,
    ValidationSummary,
    ValidationRun,
    ValidationStatus,
    ValidationMode,
    ScanDepth,
    LinkType,
    ExclusionRule,
    parse_url_list,
    validate_url_format,
    categorize_domain,
    # New validation functions
    classify_link_type,
    validate_mailto,
    validate_file_path,
    validate_network_path,
    detect_url_typos,
    detect_tld_typos,
    validate_cross_reference,
    validate_internal_bookmark,
    parse_cross_reference
)

# Import DOCX extractor
try:
    from .docx_extractor import DocxExtractor, extract_docx_links, get_urls_from_docx
    DOCX_EXTRACTION_AVAILABLE = True
except ImportError:
    DOCX_EXTRACTION_AVAILABLE = False

# Import headless browser validator for .mil/.gov fallback
HEADLESS_VALIDATOR_AVAILABLE = False
HeadlessValidatorClass = None
try:
    from .headless_validator import HeadlessValidator as HeadlessValidatorClass, is_playwright_available
    HEADLESS_VALIDATOR_AVAILABLE = is_playwright_available()
except ImportError:
    pass

# Set up logging
logger = logging.getLogger(__name__)

# Optional imports for connected mode
REQUESTS_AVAILABLE = False
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    pass

# Windows SSO authentication support
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
try:
    from requests_negotiate_sspi import HttpNegotiateAuth
    WINDOWS_AUTH_AVAILABLE = True
except ImportError:
    try:
        from requests_ntlm import HttpNtlmAuth

        class HttpNegotiateAuth:
            """Wrapper for NTLM auth that uses current Windows user."""
            def __init__(self):
                import getpass
                username = os.environ.get('USERNAME', getpass.getuser())
                domain = os.environ.get('USERDOMAIN', '')
                if domain:
                    self.auth = HttpNtlmAuth(f'{domain}\\{username}', None)
                else:
                    self.auth = HttpNtlmAuth(username, None)

            def __call__(self, r):
                return self.auth(r)

        WINDOWS_AUTH_AVAILABLE = True
    except ImportError:
        pass

# Try to import JobManager
JobManager = None
try:
    from job_manager import JobManager, JobPhase, JobStatus
except ImportError:
    # Create minimal stub if not available
    class JobPhase:
        CHECKING = "checking"
        COMPLETE = "complete"
        FAILED = "failed"

    class JobStatus:
        RUNNING = "running"
        COMPLETE = "complete"


class StandaloneHyperlinkValidator:
    """
    Main validator orchestrator for standalone URL validation.

    This class provides a unified interface for validating URLs across
    different modes (offline, validator) with progress tracking and
    result aggregation.

    Authentication Support:
    - Windows SSO (NTLM/Negotiate) - automatic with requests-negotiate-sspi
    - Client Certificates (mTLS) - for CAC/PIV and PKI-authenticated sites
    - Proxy authentication - for enterprise networks

    Usage:
        validator = StandaloneHyperlinkValidator()

        # Synchronous validation
        results = validator.validate_urls_sync(urls, mode='validator')

        # With client certificate (CAC/PIV)
        validator = StandaloneHyperlinkValidator(
            client_cert=('/path/to/cert.pem', '/path/to/key.pem')
        )

        # With proxy
        validator = StandaloneHyperlinkValidator(
            proxy='http://proxy.corp.mil:8080'
        )

        # Async validation with job tracking
        job_id = validator.start_validation_job(urls, mode='validator', options={})
        status = validator.get_job_status(job_id)
    """

    # Class-level job manager and result storage
    _job_manager = None
    _validation_runs: Dict[str, 'ValidationRun'] = {}
    _live_stats: Dict[str, Dict[str, Any]] = {}  # job_id -> live stats dict
    _lock = threading.RLock()

    def __init__(
        self,
        timeout: int = 10,
        retries: int = 3,
        use_windows_auth: bool = True,
        follow_redirects: bool = True,
        batch_size: int = 50,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        # New: Client certificate for CAC/PIV authentication
        client_cert: Optional[tuple] = None,
        # New: CA bundle for custom certificate authorities
        ca_bundle: Optional[str] = None,
        # New: Proxy server URL
        proxy: Optional[str] = None,
        # New: Skip SSL verification (use with caution)
        verify_ssl: bool = True,
        # Concurrent validation workers
        max_concurrent: int = 20
    ):
        """
        Initialize the validator.

        Args:
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            use_windows_auth: Whether to use Windows SSO (NTLM/Negotiate)
            follow_redirects: Whether to follow redirects
            batch_size: URLs to process per batch
            progress_callback: Optional callback(completed, total, current_url)
            client_cert: Tuple of (cert_path, key_path) for client certificate auth (CAC/PIV)
                         Can also be a single path to a combined PEM file
            ca_bundle: Path to custom CA certificate bundle (for .mil/.gov PKI)
            proxy: Proxy server URL (e.g., 'http://proxy.corp.mil:8080')
            verify_ssl: Whether to verify SSL certificates (default True)
            max_concurrent: Maximum concurrent validation workers (default 20)
        """
        self.timeout = timeout
        self.retries = retries
        self.use_windows_auth = use_windows_auth
        self.follow_redirects = follow_redirects
        self.batch_size = batch_size
        self.progress_callback = progress_callback
        self.max_concurrent = max_concurrent

        # Client certificate authentication (CAC/PIV/PKI)
        self.client_cert = client_cert
        self.ca_bundle = ca_bundle
        self.proxy = proxy
        self.verify_ssl = verify_ssl

        # Initialize job manager if available
        if JobManager and StandaloneHyperlinkValidator._job_manager is None:
            StandaloneHyperlinkValidator._job_manager = JobManager(max_jobs=50, job_ttl=3600)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        """
        Get current validation capabilities.

        Returns:
            Dictionary describing available modes and features
        """
        return {
            'modes': {
                'offline': {
                    'available': True,
                    'description': 'Format validation only — checks URL syntax without network access. '
                                   'Use in air-gapped environments or for quick format checks.'
                },
                'validator': {
                    'available': REQUESTS_AVAILABLE,
                    'description': 'Full HTTP validation with multiple authentication options. '
                                   'Optimized for government (.mil/.gov) and enterprise sites.',
                    'windows_auth': WINDOWS_AUTH_AVAILABLE,
                    'features': [
                        'Windows SSO (NTLM/Negotiate)',
                        'Client Certificate auth (CAC/PIV/PKI)',
                        'Custom CA bundle support',
                        'Proxy server support',
                        'Automatic retry with exponential backoff',
                        'Government site compatibility',
                        'SSL certificate validation',
                        'Redirect chain tracking',
                        'Soft-404 detection',
                        'DNS resolution checks'
                    ]
                }
            },
            'authentication': {
                'windows_sso': {
                    'available': WINDOWS_AUTH_AVAILABLE,
                    'description': 'Windows integrated authentication (NTLM/Negotiate)',
                    'install': 'pip install requests-negotiate-sspi (Windows) or requests-ntlm'
                },
                'client_cert': {
                    'available': True,
                    'description': 'Client certificate authentication for CAC/PIV/PKI sites',
                    'usage': 'Provide cert and key paths, or path to combined PEM file',
                    'common_use': '.mil sites, federal PKI-protected resources'
                },
                'proxy': {
                    'available': True,
                    'description': 'HTTP/HTTPS proxy support for enterprise networks',
                    'usage': 'Set proxy URL (e.g., http://proxy.corp.mil:8080)'
                }
            },
            'scan_depths': {
                'quick': {
                    'description': 'Format validation only (fastest)',
                    'features': ['format_check']
                },
                'standard': {
                    'description': 'Basic HTTP validation (default)',
                    'features': ['format_check', 'http_check', 'redirect_follow', 'windows_auth', 'client_cert']
                },
                'thorough': {
                    'description': 'Full validation with DNS, SSL, soft-404 detection',
                    'features': ['format_check', 'http_check', 'redirect_follow', 'windows_auth', 'client_cert',
                                'dns_check', 'ssl_check', 'soft_404_detection',
                                'suspicious_url_detection']
                }
            },
            'features': {
                'windows_sso': WINDOWS_AUTH_AVAILABLE,
                'client_cert_auth': True,
                'proxy_support': True,
                'custom_ca_bundle': True,
                'async_jobs': JobManager is not None,
                'requests_available': REQUESTS_AVAILABLE,
                'exclusions': True,
                'domain_categorization': True,
                'docx_extraction': DOCX_EXTRACTION_AVAILABLE,
                'mailto_validation': True,
                'file_path_validation': True,
                'network_path_validation': True,
                'url_typo_detection': True,
                'cross_reference_validation': True,
                'bookmark_validation': True
            },
            'link_types': [lt.value for lt in LinkType]
        }


    def validate_urls_sync(
        self,
        urls: List[str],
        mode: str = 'validator',
        options: Optional[Dict[str, Any]] = None
    ) -> ValidationRun:
        """
        Validate URLs synchronously (blocking).

        Args:
            urls: List of URLs to validate
            mode: Validation mode (offline, validator, ps1_validator)
            options: Additional options (timeout, retries, etc.)

        Returns:
            ValidationRun with results
        """
        import uuid

        # Merge options with defaults
        opts = {
            'timeout': self.timeout,
            'retries': self.retries,
            'use_windows_auth': self.use_windows_auth,
            'follow_redirects': self.follow_redirects
        }
        if options:
            opts.update(options)

        # Create run record
        run = ValidationRun(
            run_id=str(uuid.uuid4())[:8],
            mode=mode,
            status='running',
            request=ValidationRequest(urls=urls, mode=mode, **{k: v for k, v in opts.items()
                                                               if k in ValidationRequest.__dataclass_fields__})
        )

        start_time = time.time()

        try:
            # Route to appropriate validator
            # Two modes: 'offline' (format only) or 'validator' (full HTTP with Windows auth)
            if mode == 'offline':
                results = self._validate_offline(urls)
            else:  # 'validator' - default, full HTTP validation with Windows auth
                results = self._validate_with_requests(urls, opts)

            total_time = time.time() - start_time
            run.complete(results, total_time)

        except Exception as e:
            logger.exception(f"Validation failed: {e}")
            run.fail(str(e))

        return run

    def start_validation_job(
        self,
        urls: List[str],
        mode: str = 'validator',
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start asynchronous validation job.

        Args:
            urls: List of URLs to validate
            mode: Validation mode
            options: Additional options

        Returns:
            Job ID for tracking progress
        """
        import uuid

        if not self._job_manager:
            # Fallback: run synchronously and store result
            run = self.validate_urls_sync(urls, mode, options)
            with self._lock:
                self._validation_runs[run.run_id] = run
            return run.run_id

        # Create job
        job_id = self._job_manager.create_job(
            'hyperlink_validation',
            metadata={
                'url_count': len(urls),
                'mode': mode,
                'options': options or {}
            }
        )

        # Create run record
        run = ValidationRun(
            run_id=str(uuid.uuid4())[:8],
            job_id=job_id,
            mode=mode,
            status='pending',
            request=ValidationRequest(urls=urls, mode=mode)
        )

        with self._lock:
            self._validation_runs[job_id] = run

        # Start worker thread
        worker = threading.Thread(
            target=self._run_validation_job,
            args=(job_id, urls, mode, options or {}),
            daemon=True,
            name=f"hv-worker-{job_id}"
        )
        worker.start()

        return job_id

    @classmethod
    def _create_live_stats(cls, total_urls: int) -> Dict[str, Any]:
        """
        Create a fresh live_stats dict for tracking validation progress.

        This dict is updated atomically from the as_completed loop and read
        by the job status endpoint to provide cinematic progress data.

        Args:
            total_urls: Total number of URLs being validated

        Returns:
            Initial live_stats dictionary
        """
        return {
            # Phase info
            'phase': 'extracting',  # extracting -> validating -> finalizing
            'phase_label': 'Preparing URLs',
            # Status counts
            'total': total_urls,
            'completed': 0,
            'working': 0,
            'broken': 0,
            'blocked': 0,
            'timeout': 0,
            'redirect': 0,
            'ssl_error': 0,
            'dns_failed': 0,
            'auth_required': 0,
            'excluded': 0,
            'rate_limited': 0,
            'invalid': 0,
            'unknown': 0,
            # Domain tracking
            'domains_checked': {},  # domain -> {working: N, broken: N, total: N}
            # Timing data
            'avg_response_ms': 0.0,
            'min_response_ms': None,
            'max_response_ms': None,
            'total_response_ms': 0.0,
            'urls_per_second': 0.0,
            'start_time': time.time(),
            # Current activity
            'last_completed_url': None,
            'last_completed_status': None,
            'current_url': None,
        }

    @classmethod
    def _update_live_stats(cls, live_stats: Dict[str, Any], result: 'ValidationResult', stats_lock: threading.Lock):
        """
        Update the live_stats dict after a URL completes validation.

        Thread-safe: uses stats_lock to serialize updates.

        Args:
            live_stats: The shared live_stats dict
            result: The completed ValidationResult
            stats_lock: Lock for thread-safe updates
        """
        with stats_lock:
            live_stats['completed'] += 1

            # Map result status to a counter key
            status_map = {
                'WORKING': 'working',
                'BROKEN': 'broken',
                'BLOCKED': 'blocked',
                'TIMEOUT': 'timeout',
                'REDIRECT': 'redirect',
                'SSLERROR': 'ssl_error',
                'DNSFAILED': 'dns_failed',
                'AUTH_REQUIRED': 'auth_required',
                'SKIPPED': 'excluded',
                'RATE_LIMITED': 'rate_limited',
                'INVALID': 'invalid',
                'UNKNOWN': 'unknown',
            }
            counter_key = status_map.get(result.status, 'unknown')
            live_stats[counter_key] = live_stats.get(counter_key, 0) + 1

            # Domain tracking
            try:
                parsed = urlparse(result.url)
                domain = parsed.netloc or result.url[:50]
            except Exception:
                domain = result.url[:50]

            if domain not in live_stats['domains_checked']:
                live_stats['domains_checked'][domain] = {'working': 0, 'broken': 0, 'total': 0}
            domain_entry = live_stats['domains_checked'][domain]
            domain_entry['total'] += 1
            if result.status == 'WORKING':
                domain_entry['working'] += 1
            elif result.status in ('BROKEN', 'TIMEOUT', 'DNSFAILED', 'SSLERROR'):
                domain_entry['broken'] += 1

            # Timing data
            response_ms = getattr(result, 'response_time_ms', None) or 0
            if response_ms > 0:
                live_stats['total_response_ms'] += response_ms
                # Count only URLs with valid response times for average
                timed_count = live_stats['completed'] - live_stats.get('excluded', 0) - live_stats.get('invalid', 0)
                if timed_count > 0:
                    live_stats['avg_response_ms'] = round(live_stats['total_response_ms'] / timed_count, 1)
                if live_stats['min_response_ms'] is None or response_ms < live_stats['min_response_ms']:
                    live_stats['min_response_ms'] = round(response_ms, 1)
                if live_stats['max_response_ms'] is None or response_ms > live_stats['max_response_ms']:
                    live_stats['max_response_ms'] = round(response_ms, 1)

            # URLs per second
            elapsed = time.time() - live_stats['start_time']
            if elapsed > 0:
                live_stats['urls_per_second'] = round(live_stats['completed'] / elapsed, 2)

            # Current activity
            live_stats['last_completed_url'] = result.url
            live_stats['last_completed_status'] = result.status

    def _run_validation_job(
        self,
        job_id: str,
        urls: List[str],
        mode: str,
        options: Dict[str, Any]
    ):
        """
        Worker thread for async validation.

        Args:
            job_id: Job ID for progress tracking
            urls: URLs to validate
            mode: Validation mode
            options: Validation options
        """
        start_time = time.time()

        # Create live_stats and register it for this job
        total_urls = len(urls)
        live_stats = self._create_live_stats(total_urls)

        with self._lock:
            self._live_stats[job_id] = live_stats

        try:
            # Start job
            if self._job_manager:
                self._job_manager.start_job(job_id)
                self._job_manager.update_phase(job_id, JobPhase.CHECKING, "Starting URL validation")

            # Update run status and phase
            with self._lock:
                if job_id in self._validation_runs:
                    self._validation_runs[job_id].status = 'running'

            # Transition to validating phase
            live_stats['phase'] = 'validating'
            live_stats['phase_label'] = 'Validating URLs'

            # Create progress callback for job manager updates
            def update_progress(completed: int, current_url: str = ''):
                if self._job_manager:
                    progress = (completed / total_urls * 100) if total_urls > 0 else 100
                    self._job_manager.update_phase_progress(
                        job_id, progress,
                        f"Validating: {current_url[:50]}..." if current_url else None
                    )
                # Update current_url in live_stats (non-locking, single assignment is atomic)
                live_stats['current_url'] = current_url[:80] if current_url else None

            # Store original callback
            original_callback = self.progress_callback
            self.progress_callback = lambda c, t, u: update_progress(c, u)

            try:
                # Route to appropriate validator
                # Two modes: 'offline' (format only) or 'validator' (full HTTP with Windows auth)
                if mode == 'offline':
                    results = self._validate_offline(urls)
                else:  # 'validator' - default
                    results = self._validate_with_requests(urls, options, live_stats=live_stats)
            finally:
                self.progress_callback = original_callback

            # Transition to finalizing phase
            live_stats['phase'] = 'finalizing'
            live_stats['phase_label'] = 'Generating results'

            total_time = time.time() - start_time

            # Complete job
            with self._lock:
                if job_id in self._validation_runs:
                    run = self._validation_runs[job_id]
                    run.complete(results, total_time)

            # Mark live_stats as complete
            live_stats['phase'] = 'complete'
            live_stats['phase_label'] = 'Validation complete'

            if self._job_manager:
                self._job_manager.complete_job(job_id, {
                    'run_id': self._validation_runs.get(job_id, {}).run_id if job_id in self._validation_runs else job_id,
                    'results_count': len(results),
                    'total_time': total_time
                })

        except Exception as e:
            logger.exception(f"Validation job {job_id} failed: {e}")

            live_stats['phase'] = 'failed'
            live_stats['phase_label'] = f'Error: {str(e)[:80]}'

            with self._lock:
                if job_id in self._validation_runs:
                    self._validation_runs[job_id].fail(str(e))

            if self._job_manager:
                self._job_manager.fail_job(job_id, str(e))

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a validation job.

        Includes live_stats when available, providing real-time progress data:
        - Status counts (working, broken, blocked, timeout, etc.)
        - Per-domain health tracking
        - Response time statistics (avg, min, max, urls/sec)
        - Current activity and phase info

        Args:
            job_id: Job ID

        Returns:
            Job status dictionary or None if not found
        """
        with self._lock:
            run = self._validation_runs.get(job_id)
            live_stats = self._live_stats.get(job_id)

        if not run:
            return None

        result = {
            'job_id': job_id,
            'run_id': run.run_id,
            'status': run.status,
            'mode': run.mode,
            'created_at': run.created_at,
            'completed_at': run.completed_at
        }

        # Add job manager info if available
        if self._job_manager:
            job = self._job_manager.get_job(job_id)
            if job:
                result['progress'] = job.progress.to_dict()
                result['elapsed'] = job.elapsed_formatted
                result['eta'] = job.eta_formatted

        # Add live_stats for cinematic progress dashboard
        if live_stats:
            # Build a safe snapshot (avoid mutation during serialization)
            # Shallow copy domain dict keys to avoid RuntimeError: dict changed size
            try:
                domains_snapshot = {}
                for domain, counts in list(live_stats.get('domains_checked', {}).items()):
                    domains_snapshot[domain] = dict(counts)

                result['live_stats'] = {
                    'phase': live_stats.get('phase', 'unknown'),
                    'phase_label': live_stats.get('phase_label', ''),
                    'total': live_stats.get('total', 0),
                    'completed': live_stats.get('completed', 0),
                    'working': live_stats.get('working', 0),
                    'broken': live_stats.get('broken', 0),
                    'blocked': live_stats.get('blocked', 0),
                    'timeout': live_stats.get('timeout', 0),
                    'redirect': live_stats.get('redirect', 0),
                    'ssl_error': live_stats.get('ssl_error', 0),
                    'dns_failed': live_stats.get('dns_failed', 0),
                    'auth_required': live_stats.get('auth_required', 0),
                    'excluded': live_stats.get('excluded', 0),
                    'rate_limited': live_stats.get('rate_limited', 0),
                    'invalid': live_stats.get('invalid', 0),
                    'unknown': live_stats.get('unknown', 0),
                    'domains_checked': domains_snapshot,
                    'domain_count': len(domains_snapshot),
                    'avg_response_ms': live_stats.get('avg_response_ms', 0),
                    'min_response_ms': live_stats.get('min_response_ms'),
                    'max_response_ms': live_stats.get('max_response_ms'),
                    'urls_per_second': live_stats.get('urls_per_second', 0),
                    'last_completed_url': live_stats.get('last_completed_url'),
                    'last_completed_status': live_stats.get('last_completed_status'),
                    'current_url': live_stats.get('current_url'),
                    # v5.0.5: Retest phase tracking
                    'retest_total': live_stats.get('retest_total', 0),
                    'retest_completed': live_stats.get('retest_completed', 0),
                }
            except Exception as e:
                logger.debug(f"Error building live_stats snapshot: {e}")
                result['live_stats'] = None

        # Add summary if complete
        if run.status == 'complete' and run.summary:
            result['summary'] = run.summary.to_dict()

        if run.error:
            result['error'] = run.error

        return result

    def get_job_results(self, job_id: str) -> Optional[ValidationRun]:
        """
        Get full results of a validation job.

        Args:
            job_id: Job ID

        Returns:
            ValidationRun with full results or None
        """
        with self._lock:
            return self._validation_runs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running validation job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found or already complete
        """
        with self._lock:
            run = self._validation_runs.get(job_id)
            if run and run.status == 'running':
                run.cancel()

        if self._job_manager:
            job = self._job_manager.get_job(job_id)
            if job:
                job.cancel()
                return True

        return run is not None and run.status == 'cancelled'

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def _validate_offline(self, urls: List[str]) -> List[ValidationResult]:
        """
        Validate URLs in offline mode (format only).

        Args:
            urls: URLs to validate

        Returns:
            List of ValidationResult objects
        """
        results = []

        for i, url in enumerate(urls):
            is_valid, error = validate_url_format(url)

            if is_valid:
                result = ValidationResult(
                    url=url,
                    status='WORKING',  # Format is valid
                    message='Format valid (offline mode - not verified)',
                    checked_at=datetime.utcnow().isoformat() + "Z"
                )
            else:
                result = ValidationResult(
                    url=url,
                    status='INVALID',
                    message=error,
                    checked_at=datetime.utcnow().isoformat() + "Z"
                )

            results.append(result)

            # Progress callback
            if self.progress_callback:
                self.progress_callback(i + 1, len(urls), url)

        return results

    # =========================================================================
    # v5.9.29: Robust auth methods for internal/corporate link validation
    # =========================================================================

    @staticmethod
    def _is_login_page_redirect(response) -> bool:
        """
        Detect if a response chain redirected to a login/authentication page.

        SharePoint, ADFS, Okta, and other SSO systems redirect unauthenticated
        users to login pages. These redirects mean the resource EXISTS but
        requires auth — they should be AUTH_REQUIRED, not REDIRECT or WORKING.
        """
        LOGIN_URL_PATTERNS = (
            '/_layouts/15/authenticate',    # SharePoint
            '/_layouts/15/Authenticate',    # SharePoint (case variant)
            '/adfs/ls/',                     # ADFS (Active Directory Federation Services)
            '/adfs/oauth2/',                 # ADFS OAuth
            '/oauth2/authorize',             # Generic OAuth
            'login.microsoftonline.com',     # Azure AD
            'login.microsoftonline.us',      # Azure AD Gov
            'login.windows.net',             # Azure AD legacy
            'sts.windows.net',               # Azure STS
            '/federation/',                  # Federation services
            '/CookieAuth.dll',               # IIS Forms auth
            '/saml/sso',                     # SAML SSO
            '/sso/login',                    # Generic SSO
        )

        # Check redirect chain
        if hasattr(response, 'history') and response.history:
            for hist_resp in response.history:
                location = hist_resp.headers.get('Location', '').lower()
                if any(pattern.lower() in location for pattern in LOGIN_URL_PATTERNS):
                    return True

        # Check final URL
        final_url = ''
        if hasattr(response, 'url') and response.url:
            final_url = response.url.lower()
        if any(pattern.lower() in final_url for pattern in LOGIN_URL_PATTERNS):
            return True

        return False

    def _probe_windows_auth(self, urls: List[str], headers: Dict[str, str],
                            verify_ssl=True, ca_bundle=None) -> Dict[str, Any]:
        """
        Pre-validation auth probe: test Windows SSO against internal URLs.

        Before bulk validation, test if Windows SSO actually works by hitting
        a known-good internal URL. This tells us whether the auth environment
        is functional and informs the per-URL auth retry strategy.

        Returns:
            {
                'auth_working': bool or None (None = no internal URLs found),
                'probe_url': str or None,
                'auth_scheme': str or None,
                'message': str,
                'probe_time_ms': float
            }
        """
        if not WINDOWS_AUTH_AVAILABLE or not HttpNegotiateAuth:
            return {
                'auth_working': False,
                'probe_url': None,
                'auth_scheme': None,
                'message': 'Windows SSO library not available (requests-negotiate-sspi not installed)',
                'probe_time_ms': 0
            }

        # Internal/corporate domain indicators
        INTERNAL_INDICATORS = (
            '.myngc.com', '.northgrum.com', '.northropgrumman.com',
            'ngc.sharepoint.us', '.ngc.sharepoint.us',
            'sharepoint', 'intranet', 'internal',
            '.mil', '.gov', 'teams.microsoft'
        )

        # Extract candidate internal URLs for probing
        candidate_urls = []
        seen_domains = set()
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain in seen_domains:
                    continue
                if any(ind in domain for ind in INTERNAL_INDICATORS):
                    seen_domains.add(domain)
                    candidate_urls.append(url)
                    # Also try root of the domain
                    root_url = f"{parsed.scheme}://{parsed.netloc}/"
                    if root_url not in candidate_urls:
                        candidate_urls.append(root_url)
            except Exception:
                continue

        if not candidate_urls:
            return {
                'auth_working': None,
                'probe_url': None,
                'auth_scheme': None,
                'message': 'No internal/corporate URLs found for auth probe',
                'probe_time_ms': 0
            }

        # Try each candidate with a fresh session + SSO
        for probe_url in candidate_urls[:6]:  # Try max 6 probes
            start = time.time()
            probe_session = None
            try:
                probe_session = requests.Session()
                probe_session.auth = HttpNegotiateAuth()
                if ca_bundle:
                    probe_session.verify = ca_bundle
                else:
                    probe_session.verify = verify_ssl

                # Use GET (not HEAD) — NTLM/Negotiate needs full request
                resp = probe_session.get(
                    probe_url,
                    timeout=(15, 30),
                    allow_redirects=True,
                    headers=headers,
                    stream=True
                )
                resp.close()

                probe_time = (time.time() - start) * 1000

                # Check for login page redirect — doesn't count as success
                if self._is_login_page_redirect(resp):
                    logger.debug(f"Auth probe: {probe_url} redirected to login page")
                    continue

                if 200 <= resp.status_code < 400:
                    # Extract auth scheme from the request that was sent
                    auth_header = resp.request.headers.get('Authorization', '') if resp.request else ''
                    scheme = auth_header.split()[0] if auth_header else 'Negotiate'
                    logger.info(f"Auth probe SUCCESS: {probe_url} -> HTTP {resp.status_code} ({scheme})")
                    return {
                        'auth_working': True,
                        'probe_url': probe_url,
                        'auth_scheme': scheme,
                        'message': f'Windows SSO confirmed working (HTTP {resp.status_code} via {scheme})',
                        'probe_time_ms': probe_time
                    }

                if resp.status_code == 401:
                    www_auth = resp.headers.get('WWW-Authenticate', '')
                    logger.debug(f"Auth probe 401 at {probe_url}: server offers [{www_auth[:80]}]")
                    continue

                if resp.status_code == 403:
                    logger.debug(f"Auth probe 403 at {probe_url}: access denied")
                    continue

            except Exception as e:
                logger.debug(f"Auth probe failed for {probe_url}: {e}")
            finally:
                if probe_session:
                    try:
                        probe_session.close()
                    except Exception:
                        pass

        return {
            'auth_working': False,
            'probe_url': candidate_urls[0] if candidate_urls else None,
            'auth_scheme': None,
            'message': 'Windows SSO auth probe failed on all candidates — internal links may show AUTH_REQUIRED',
            'probe_time_ms': 0
        }

    def _retry_with_fresh_auth(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: int,
        verify_ssl=True,
        ca_bundle=None
    ) -> Optional[Dict[str, Any]]:
        """
        Retry a URL with a completely fresh session and Windows SSO.

        NTLM/Negotiate auth is connection-specific. The multi-step handshake
        (challenge -> response) requires the same TCP connection throughout.
        A shared session across threads corrupts this. Fresh session per retry
        guarantees clean auth state — just like Chrome's per-tab connection pool.

        Uses GET (not HEAD) because NTLM challenge-response requires full HTTP.
        Uses stream=True to avoid downloading large file bodies.

        Returns:
            Dict with 'status_code', 'status', 'message', 'redirect_url'
            or None if retry failed or auth unavailable
        """
        if not WINDOWS_AUTH_AVAILABLE or not HttpNegotiateAuth:
            return None

        connect_timeout = min(timeout, 20)
        read_timeout = timeout * 3
        fresh_session = None

        try:
            # Create completely fresh session — critical for NTLM
            fresh_session = requests.Session()
            fresh_session.auth = HttpNegotiateAuth()
            if ca_bundle:
                fresh_session.verify = ca_bundle
            else:
                fresh_session.verify = verify_ssl

            # Use GET, not HEAD — NTLM handshake needs full request
            resp = fresh_session.get(
                url,
                timeout=(connect_timeout, read_timeout),
                allow_redirects=True,
                headers=headers,
                stream=True
            )

            status_code = resp.status_code
            final_url = resp.url if resp.url else url
            redirect_count = len(resp.history) if resp.history else 0

            # Check for login page redirect (SharePoint/ADFS/Azure AD)
            is_login_redirect = self._is_login_page_redirect(resp)

            # Check for document download
            content_disp = resp.headers.get('Content-Disposition', '')
            content_type = resp.headers.get('Content-Type', '')
            is_download = (
                'attachment' in content_disp.lower() or
                any(ct in content_type.lower() for ct in (
                    'application/pdf', 'application/msword',
                    'application/vnd.openxmlformats', 'application/vnd.ms-excel',
                    'application/vnd.ms-powerpoint', 'application/octet-stream',
                    'application/zip', 'application/vnd.oasis.opendocument'
                ))
            )

            resp.close()

            if is_login_redirect:
                return {
                    'status_code': status_code,
                    'status': 'AUTH_REQUIRED',
                    'message': f'Redirected to login page — SSO insufficient for this resource',
                    'redirect_url': final_url
                }

            if 200 <= status_code < 300:
                msg = f'HTTP {status_code} OK (authenticated with Windows SSO)'
                if is_download:
                    fname = ''
                    if 'filename=' in content_disp:
                        fname = content_disp.split('filename=')[-1].strip('"\'').strip()
                    msg = f'File download link (valid, authenticated) — {fname or content_type}'
                return {
                    'status_code': status_code,
                    'status': 'WORKING',
                    'message': msg,
                    'redirect_url': final_url if redirect_count > 0 else None
                }

            if 300 <= status_code < 400:
                location = resp.headers.get('Location', final_url) if hasattr(resp, 'headers') else final_url
                return {
                    'status_code': status_code,
                    'status': 'REDIRECT',
                    'message': f'Redirect to {location} (after auth)',
                    'redirect_url': final_url
                }

            if status_code == 401:
                # Still 401 after fresh SSO → user's credentials genuinely insufficient
                return {
                    'status_code': 401,
                    'status': 'AUTH_REQUIRED',
                    'message': 'Authentication required — Windows SSO credentials insufficient for this resource',
                    'redirect_url': None
                }

            if status_code == 403:
                # 403 after auth → permission-based, not broken
                return {
                    'status_code': 403,
                    'status': 'AUTH_REQUIRED',
                    'message': 'Access forbidden (403) — authenticated but insufficient permissions',
                    'redirect_url': None
                }

            # Other status codes (404, 500, etc.) — let original flow handle
            return None

        except requests.exceptions.SSLError:
            return None  # Let original SSL handling take over
        except requests.exceptions.Timeout:
            return None  # Let original timeout handling take over
        except requests.exceptions.ConnectionError:
            return None  # Let original connection error handling take over
        except Exception as e:
            logger.debug(f"Fresh auth retry failed for {url}: {e}")
            return None
        finally:
            if fresh_session:
                try:
                    fresh_session.close()
                except Exception:
                    pass

    def _validate_single_url(
        self,
        url: str,
        session: 'requests.Session',
        headers: Dict[str, str],
        auth_used: str,
        timeout: int,
        retries: int,
        follow_redirects: bool,
        exclusions: List,
        check_dns: bool,
        check_ssl: bool,
        detect_soft_404_flag: bool,
        check_suspicious: bool
    ) -> ValidationResult:
        """
        Validate a single URL using the provided session.

        This method is thread-safe: each call uses the shared session
        (requests.Session is thread-safe for concurrent requests) but
        creates its own ValidationResult with no shared mutable state.

        Args:
            url: The URL to validate
            session: Configured requests.Session (thread-safe)
            headers: Request headers dict
            auth_used: Authentication description string
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            follow_redirects: Whether to follow redirects
            exclusions: List of ExclusionRule objects
            check_dns: Whether to perform DNS resolution check
            check_ssl: Whether to perform SSL certificate check
            detect_soft_404_flag: Whether to detect soft 404 pages
            check_suspicious: Whether to detect suspicious URLs

        Returns:
            ValidationResult for this URL
        """
        start_time = time.time()
        result = ValidationResult(url=url, auth_used=auth_used)

        # Set domain category
        result.domain_category = categorize_domain(url)

        # Check exclusions first
        matched_exclusion = None
        for exc in exclusions:
            if exc.matches(url):
                matched_exclusion = exc
                break

        if matched_exclusion:
            result.excluded = True
            result.exclusion_reason = matched_exclusion.reason or f"Matched pattern: {matched_exclusion.pattern}"
            if matched_exclusion.treat_as_valid:
                result.status = 'WORKING'
                result.message = f'Excluded (treated as OK): {result.exclusion_reason}'
            else:
                result.status = 'SKIPPED'
                result.message = f'Excluded: {result.exclusion_reason}'
            result.response_time_ms = (time.time() - start_time) * 1000
            return result

        # Check for suspicious URL (thorough mode)
        if check_suspicious:
            suspicious = detect_suspicious_url(url)
            if suspicious['suspicious']:
                result.is_suspicious = True
                result.suspicious_reasons = suspicious['reasons']

        # Format validation first
        is_valid, error = validate_url_format(url)
        if not is_valid:
            result.status = 'INVALID'
            result.message = error
            result.response_time_ms = (time.time() - start_time) * 1000
            return result

        # Try to validate with retries
        # Government sites often need more patience - use longer connect timeout
        connect_timeout = min(timeout, 20)  # Connect timeout (gov sites need 20s+)
        read_timeout = timeout * 3  # Read timeout (gov/intranet sites can be very slow)
        last_error = None
        head_failed = False

        for attempt in range(retries + 1):
            try:
                # First try HEAD request (faster, less server load)
                if not head_failed:
                    try:
                        response = session.head(
                            url,
                            timeout=(connect_timeout, read_timeout),
                            allow_redirects=follow_redirects,
                            headers=headers,
                            verify=True  # Verify SSL certificates
                        )
                        # Check if HEAD returned an error - many gov sites block HEAD
                        # but work fine with GET (returns 404/405/403 for HEAD only)
                        if response.status_code in [404, 405, 403, 501]:
                            head_failed = True
                            # Don't count this as a real attempt - retry with GET
                            continue
                    except requests.exceptions.RequestException:
                        # Some government sites block HEAD requests - fall back to GET
                        head_failed = True
                        continue  # Retry with GET instead of re-raising

                # Fall back to GET if HEAD failed or returned error
                if head_failed:
                    response = session.get(
                        url,
                        timeout=(connect_timeout, read_timeout),
                        allow_redirects=follow_redirects,
                        headers=headers,
                        verify=True,
                        stream=True  # Don't download full content
                    )
                    # Close the response body without reading it
                    response.close()

                result.status_code = response.status_code
                result.response_time_ms = (time.time() - start_time) * 1000
                result.attempts = attempt + 1
                result.dns_resolved = True

                # ===== Document download detection =====
                # When a link points to a downloadable file (.docx, .pdf, .xlsx etc),
                # the server returns Content-Disposition: attachment. This means the
                # link is VALID — it's offering a file download. The OS would show a
                # "Open file?" dialog, which is the "document open popup" the user sees.
                # Mark these as WORKING immediately.
                content_disp = response.headers.get('Content-Disposition', '')
                content_type = response.headers.get('Content-Type', '')
                download_content_types = (
                    'application/pdf', 'application/msword',
                    'application/vnd.openxmlformats', 'application/vnd.ms-excel',
                    'application/vnd.ms-powerpoint', 'application/octet-stream',
                    'application/zip', 'application/x-zip',
                    'application/vnd.oasis.opendocument'
                )
                is_download = (
                    'attachment' in content_disp.lower() or
                    any(ct in content_type.lower() for ct in download_content_types)
                )
                if is_download and response.status_code in (200, 206):
                    result.status = 'WORKING'
                    fname = ''
                    if 'filename=' in content_disp:
                        fname = content_disp.split('filename=')[-1].strip('"\'').strip()
                    result.message = f'File download link (valid) — {fname or content_type}'
                    result.response_time_ms = (time.time() - start_time) * 1000
                    break  # No need to check further

                # Check for redirects
                if response.history:
                    result.redirect_count = len(response.history)
                    result.redirect_url = response.url

                # Map status code to status
                # Special handling for government/enterprise authentication
                if 200 <= response.status_code < 300:
                    result.status = 'WORKING'
                    result.message = f'HTTP {response.status_code} OK'

                    # Thorough mode: check for soft 404
                    if detect_soft_404_flag and response.status_code == 200:
                        try:
                            # Need GET to check content
                            get_response = session.get(url, timeout=(connect_timeout, read_timeout), headers=headers)
                            if detect_soft_404(get_response.text):
                                result.is_soft_404 = True
                                result.status = 'BROKEN'
                                result.message = 'Soft 404 detected (page exists but shows error)'
                        except Exception:
                            pass  # Couldn't check, keep WORKING status

                elif 300 <= response.status_code < 400:
                    # v5.9.29: Check if redirect leads to a login page (SharePoint/ADFS/Azure AD)
                    if self._is_login_page_redirect(response):
                        result.status = 'AUTH_REQUIRED'
                        result.message = f'Redirected to login page ({response.url[:80] if response.url else "unknown"})'
                        break
                    result.status = 'REDIRECT'
                    result.message = f'Redirect to {response.headers.get("Location", "unknown")}'

                elif response.status_code == 401:
                    # v5.9.29: Retry with fresh Windows SSO session before giving up
                    # NTLM/Negotiate auth is connection-specific — shared session across
                    # threads corrupts the multi-step handshake. Fresh session fixes this.
                    www_auth = response.headers.get('WWW-Authenticate', '')
                    auth_retry = self._retry_with_fresh_auth(
                        url, headers, timeout,
                        verify_ssl=session.verify if hasattr(session, 'verify') else True
                    )
                    if auth_retry:
                        result.status = auth_retry['status']
                        result.status_code = auth_retry['status_code']
                        result.message = auth_retry['message']
                        if auth_retry.get('redirect_url'):
                            result.redirect_url = auth_retry['redirect_url']
                        break
                    # Fresh auth retry failed or unavailable
                    result.status = 'AUTH_REQUIRED'
                    result.message = f'Authentication required (401) — {("server offers: " + www_auth[:60]) if www_auth else "link exists but requires credentials"}'

                elif response.status_code == 403:
                    # v5.9.29: 403 Forbidden — distinguish auth-related from bot-block
                    www_auth = response.headers.get('WWW-Authenticate', '')

                    if www_auth:
                        # Server sent WWW-Authenticate → this IS an auth challenge
                        auth_retry = self._retry_with_fresh_auth(
                            url, headers, timeout,
                            verify_ssl=session.verify if hasattr(session, 'verify') else True
                        )
                        if auth_retry:
                            result.status = auth_retry['status']
                            result.status_code = auth_retry['status_code']
                            result.message = auth_retry['message']
                            if auth_retry.get('redirect_url'):
                                result.redirect_url = auth_retry['redirect_url']
                            break

                    # No WWW-Authenticate header or auth retry failed
                    # Try without auth to see if it's bot-blocking vs permission
                    if attempt < retries:
                        try:
                            no_auth_resp = requests.get(url, timeout=(connect_timeout, read_timeout),
                                                         allow_redirects=follow_redirects, headers=headers,
                                                         verify=session.verify, stream=True)
                            no_auth_resp.close()
                            if 200 <= no_auth_resp.status_code < 400:
                                result.status = 'WORKING'
                                result.status_code = no_auth_resp.status_code
                                result.message = f'HTTP {no_auth_resp.status_code} OK (no-auth fallback)'
                                break
                        except Exception:
                            pass

                    # v5.9.29: Also try fresh auth even without WWW-Authenticate
                    # Some corporate servers return bare 403 without the header
                    if not www_auth:
                        auth_retry = self._retry_with_fresh_auth(
                            url, headers, timeout,
                            verify_ssl=session.verify if hasattr(session, 'verify') else True
                        )
                        if auth_retry and auth_retry['status'] == 'WORKING':
                            result.status = auth_retry['status']
                            result.status_code = auth_retry['status_code']
                            result.message = auth_retry['message']
                            if auth_retry.get('redirect_url'):
                                result.redirect_url = auth_retry['redirect_url']
                            break

                    result.status = 'AUTH_REQUIRED'
                    result.message = 'Access forbidden (403) — requires specific permissions or VPN'

                elif response.status_code == 404:
                    result.status = 'BROKEN'
                    result.message = 'Page not found (404)'

                elif response.status_code == 405:
                    # Method Not Allowed - HEAD blocked, but page likely exists
                    # Retry with GET
                    if not head_failed:
                        head_failed = True
                        continue  # Retry with GET
                    result.status = 'WORKING'
                    result.message = 'HTTP 405 - page exists (HEAD not allowed)'

                elif response.status_code == 429:
                    # Rate limited - don't mark as broken
                    result.status = 'RATE_LIMITED'
                    result.message = 'Rate limited (429) - too many requests'

                elif 400 <= response.status_code < 500:
                    result.status = 'BROKEN'
                    result.message = f'Client error: HTTP {response.status_code}'

                elif response.status_code >= 500:
                    # Server errors might be temporary - retry
                    if attempt < retries:
                        continue
                    result.status = 'BROKEN'
                    result.message = f'Server error: HTTP {response.status_code}'
                else:
                    result.status = 'UNKNOWN'
                    result.message = f'HTTP {response.status_code}'

                # Thorough mode: DNS check
                if check_dns and result.status == 'WORKING':
                    try:
                        hostname = urlparse(url).netloc
                        dns_result = check_dns_resolution(hostname)
                        result.dns_resolved = dns_result['resolved']
                        result.dns_ip_addresses = dns_result.get('ip_addresses', [])
                        result.dns_response_time_ms = dns_result.get('response_time_ms', 0)
                    except Exception:
                        pass

                # Thorough mode: SSL check
                if check_ssl and url.startswith('https://') and result.status == 'WORKING':
                    try:
                        hostname = urlparse(url).netloc
                        ssl_result = check_ssl_certificate(hostname)
                        result.ssl_valid = ssl_result.get('valid', False)
                        result.ssl_issuer = ssl_result.get('issuer', '')
                        result.ssl_expires = ssl_result.get('expires')
                        result.ssl_days_until_expiry = ssl_result.get('days_until_expiry', 0)
                        result.ssl_warning = ssl_result.get('warning')
                    except Exception:
                        pass

                break  # Success, no retry needed

            except requests.exceptions.SSLError as e:
                # SSL error: try once more without verification to confirm link exists
                result.ssl_valid = False
                last_error = e
                try:
                    fallback_resp = session.head(url, timeout=(connect_timeout, read_timeout),
                                                  allow_redirects=follow_redirects, headers=headers,
                                                  verify=False)
                    if 200 <= fallback_resp.status_code < 400:
                        result.status = 'SSL_WARNING'
                        result.status_code = fallback_resp.status_code
                        result.message = f'Link exists but SSL certificate invalid: {str(e)[:80]}'
                        break
                except Exception:
                    pass
                result.status = 'SSLERROR'
                result.message = f'SSL certificate error: {str(e)[:80]}'
                break  # Don't retry SSL errors further

            except requests.exceptions.Timeout:
                last_error = 'timeout'
                if attempt == retries:
                    result.status = 'TIMEOUT'
                    result.message = f'Connection timed out after {timeout}s'

            except requests.exceptions.ConnectionError as e:
                error_str = str(e).lower()
                if 'name or service not known' in error_str or 'getaddrinfo failed' in error_str:
                    result.dns_resolved = False
                    last_error = e
                    if attempt == retries:
                        result.status = 'DNSFAILED'
                        result.message = 'Could not resolve hostname (tried multiple times)'
                    # Allow retry — DNS can be transient on enterprise networks
                elif 'connection refused' in error_str:
                    last_error = e
                    if attempt == retries:
                        result.status = 'BLOCKED'
                        result.message = 'Connection refused (tried multiple times)'
                    # Allow retry instead of immediate break
                else:
                    last_error = e
                    if attempt == retries:
                        # v5.9.1: Better classify connection errors by error string
                        if 'timed out' in error_str or 'timeout' in error_str:
                            result.status = 'TIMEOUT'
                            result.message = f'Connection timed out: {str(e)[:50]}'
                        elif 'reset by peer' in error_str or 'broken pipe' in error_str:
                            result.status = 'BLOCKED'
                            result.message = f'Connection reset: {str(e)[:50]}'
                        else:
                            result.status = 'BROKEN'
                            result.message = f'Connection error: {str(e)[:50]}'

            except requests.RequestException as e:
                last_error = e
                if attempt == retries:
                    result.status = 'BROKEN'
                    result.message = f'Request error: {str(e)[:50]}'

            # Exponential backoff before retry
            if attempt < retries:
                import random
                wait_time = (2 ** attempt) + (random.random() * 0.1)
                time.sleep(wait_time)

        result.response_time_ms = (time.time() - start_time) * 1000
        result.attempts = min(attempt + 1, retries + 1) if 'attempt' in dir() else 1

        # v5.9.29: DNS-only corporate domain downgrade
        # After Tier 2 fresh auth retry, HTTP errors (BROKEN, TIMEOUT, BLOCKED) are genuine.
        # The ONLY exception: DNSFAILED on corporate domains means internal DNS doesn't resolve
        # from outside the VPN — that's a network access issue, not a broken link.
        # Previous blanket downgrades (v5.0.5-v5.9.1) masked real broken links by converting
        # BROKEN/TIMEOUT/BLOCKED to AUTH_REQUIRED for corporate domains and document URLs.
        # Those are now removed — Tier 2 auth retry handles auth-related failures properly.
        if result.status == 'DNSFAILED':
            CORPORATE_NETWORK_DOMAINS = (
                '.myngc.com', '.northgrum.com', '.northropgrumman.com',
                'ngc.sharepoint.us', '.ngc.sharepoint.us',
                '.mil', '.gov',
            )
            try:
                domain = urlparse(url).netloc.lower()
                is_corporate = any(
                    domain.endswith(d.lstrip('.')) or domain == d.lstrip('.')
                    for d in CORPORATE_NETWORK_DOMAINS
                )
                if is_corporate:
                    result.status = 'AUTH_REQUIRED'
                    result.message = (
                        f'Corporate/government domain — DNS does not resolve from this network. '
                        f'This link likely works from within the corporate network or VPN.'
                    )
            except Exception:
                pass

        return result

    def _validate_with_requests(
        self,
        urls: List[str],
        options: Dict[str, Any],
        live_stats: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Validate URLs using Python requests library with concurrent execution.

        Uses ThreadPoolExecutor for concurrent validation. Each URL validation
        is an independent HTTP request with no shared mutable state, making
        this safe for concurrent execution. The requests.Session object is
        thread-safe for concurrent requests.

        Includes built-in deduplication: each unique URL is validated only once,
        and results are copied for any duplicate URLs.

        Optimized for government (.mil/.gov) and enterprise sites with:
        - Windows integrated authentication (NTLM/Negotiate SSO)
        - Client certificate authentication (CAC/PIV/PKI)
        - Custom CA bundle support for federal PKI
        - Proxy server support for enterprise networks
        - Robust retry logic with exponential backoff
        - Handling of auth challenges and redirects
        - SSL certificate verification
        - Configurable timeouts for slow government servers

        Args:
            urls: URLs to validate
            options: Validation options including:
                - client_cert: (cert_path, key_path) or combined PEM path
                - ca_bundle: Path to custom CA bundle
                - proxy: Proxy server URL
                - verify_ssl: Whether to verify SSL (default True)
            live_stats: Optional shared dict for real-time progress tracking.
                        When provided, updated after each URL completes with
                        status counts, domain health, timing data, and activity.

        Returns:
            List of ValidationResult objects (one per input URL, preserving order)
        """
        if not REQUESTS_AVAILABLE:
            # Fallback to offline mode
            logger.warning("requests library not available, falling back to offline mode")
            return self._validate_offline(urls)

        timeout = options.get('timeout', self.timeout)
        retries = options.get('retries', self.retries)
        follow_redirects = options.get('follow_redirects', self.follow_redirects)

        # Authentication options
        client_cert = options.get('client_cert', self.client_cert)
        ca_bundle = options.get('ca_bundle', self.ca_bundle)
        proxy = options.get('proxy', self.proxy)
        verify_ssl = options.get('verify_ssl', self.verify_ssl)

        # Scan depth settings
        scan_depth = options.get('scan_depth', 'standard')

        # Quick mode = format validation only (no HTTP requests)
        if scan_depth == 'quick':
            logger.info("Quick scan mode: performing format validation only")
            return self._validate_offline(urls)

        check_dns = options.get('check_dns', scan_depth == 'thorough')
        check_ssl_opt = options.get('check_ssl', scan_depth == 'thorough')
        detect_soft_404_flag = options.get('detect_soft_404', scan_depth == 'thorough')
        check_suspicious = options.get('check_suspicious', scan_depth == 'thorough')

        # Exclusion rules
        exclusion_dicts = options.get('exclusions', [])
        exclusions = []
        for exc in exclusion_dicts:
            if isinstance(exc, dict):
                exclusions.append(ExclusionRule.from_dict(exc))
            elif isinstance(exc, ExclusionRule):
                exclusions.append(exc)

        # Set up session with authentication
        session = requests.Session()
        auth_methods = []

        # 1. Configure client certificate authentication (CAC/PIV/PKI)
        if client_cert:
            session.cert = client_cert
            auth_methods.append('client_cert')
            logger.info(f"Client certificate authentication configured")

        # 2. Configure custom CA bundle (for .mil/.gov PKI)
        if ca_bundle:
            session.verify = ca_bundle
            logger.info(f"Custom CA bundle configured: {ca_bundle}")
        elif verify_ssl:
            session.verify = True
        else:
            session.verify = False
            logger.warning("SSL verification disabled - use with caution")

        # 3. Configure proxy server
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
            auth_methods.append('proxy')
            logger.info(f"Proxy configured: {proxy}")

        # 4. Configure Windows SSO (NTLM/Negotiate) if available and no client cert
        # Note: Windows auth and client cert can conflict, client cert takes precedence
        if WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth and not client_cert:
            try:
                session.auth = HttpNegotiateAuth()
                auth_methods.append('windows_sso')
                logger.debug("Windows SSO authentication configured")
            except Exception as e:
                logger.warning(f"Windows SSO setup failed: {e}")

        # Determine auth description for results
        if auth_methods:
            auth_used = '+'.join(auth_methods)
        else:
            auth_used = 'none'
            logger.info("No authentication configured - using anonymous requests")

        # v5.9.22: Updated headers — modern Chrome 131 UA, added Sec-Fetch headers
        # to look like a genuine browser navigation (fixes YouTube, wikis, .mil/.gov)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }

        # v5.9.29: Pre-validation auth probe — test Windows SSO before bulk validation
        auth_probe_result = self._probe_windows_auth(
            urls, headers,
            verify_ssl=verify_ssl,
            ca_bundle=ca_bundle
        )
        logger.info(f"Auth probe: {auth_probe_result['message']}")
        if auth_probe_result.get('auth_working'):
            auth_methods.append('windows_sso_verified')

        # Deduplicate URLs: validate unique URLs only, then map results back
        seen = {}
        unique_urls = []
        url_indices = {}  # Maps each unique URL to its first index in the original list
        for i, url in enumerate(urls):
            if url not in seen:
                seen[url] = True
                url_indices[url] = len(unique_urls)
                unique_urls.append(url)

        total_unique = len(unique_urls)
        total_original = len(urls)
        if total_unique < total_original:
            logger.info(f"Deduplication: {total_original} URLs -> {total_unique} unique for validation")

        # Validate unique URLs concurrently using ThreadPoolExecutor
        # Each URL validation is independent (separate HTTP request, no shared mutable state)
        # requests.Session is thread-safe for concurrent requests
        unique_results: Dict[str, ValidationResult] = {}
        completed_count = 0
        progress_lock = threading.Lock()
        stats_lock = threading.Lock()  # Separate lock for live_stats updates

        # Shared validation parameters for the worker
        shared_params = dict(
            session=session,
            headers=headers,
            auth_used=auth_used,
            timeout=timeout,
            retries=retries,
            follow_redirects=follow_redirects,
            exclusions=exclusions,
            check_dns=check_dns,
            check_ssl=check_ssl_opt,
            detect_soft_404_flag=detect_soft_404_flag,
            check_suspicious=check_suspicious
        )

        max_workers = min(self.max_concurrent, total_unique)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all unique URLs
            future_to_url = {
                executor.submit(self._validate_single_url, url, **shared_params): url
                for url in unique_urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    unique_results[url] = result
                except Exception as e:
                    logger.error(f"Unexpected error validating {url}: {e}")
                    error_result = ValidationResult(url=url, auth_used=auth_used)
                    error_result.status = 'BROKEN'
                    error_result.message = f'Validation error: {str(e)[:50]}'
                    unique_results[url] = error_result
                    result = error_result

                # Update live_stats with this result (thread-safe)
                if live_stats is not None:
                    self._update_live_stats(live_stats, result, stats_lock)

                # Progress callback (reports progress based on total original URL count)
                with progress_lock:
                    completed_count += 1
                    if self.progress_callback:
                        # Scale progress to original URL count
                        scaled = int(completed_count / total_unique * total_original)
                        self.progress_callback(scaled, total_original, url)

        session.close()

        # =================================================================
        # RE-TEST PHASE: Retry all broken/timeout/error links with deeper scan
        # This dramatically reduces false positives on slow or flaky sites
        # =================================================================
        # v5.9.29: Added AUTH_REQUIRED to retest — internal links that got AUTH_REQUIRED
        # during primary validation should be retried with fresh SSO in the retest phase
        retest_statuses = {'BROKEN', 'TIMEOUT', 'DNSFAILED', 'BLOCKED', 'SSLERROR', 'AUTH_REQUIRED'}
        broken_urls = [url for url, r in unique_results.items() if r.status in retest_statuses]

        if broken_urls:
            logger.info(f"Re-test phase: retrying {len(broken_urls)} broken/failed links with deeper scan")
            # v5.0.5: Update live_stats and progress to show retesting phase
            if live_stats is not None:
                live_stats['phase'] = 'retesting'
                live_stats['phase_label'] = f'Re-testing {len(broken_urls)} failed links'
                live_stats['retest_total'] = len(broken_urls)
                live_stats['retest_completed'] = 0
            retest_results = self._retest_broken_links(
                broken_urls, unique_results, options, headers, auth_used,
                live_stats=live_stats, stats_lock=stats_lock
            )
            # Merge retest results — only update if retest found the link working
            for url, retest_result in retest_results.items():
                if retest_result.status in ('WORKING', 'REDIRECT', 'SSL_WARNING', 'AUTH_REQUIRED'):
                    old_status = unique_results[url].status
                    unique_results[url] = retest_result
                    logger.info(f"Re-test upgraded {url}: {old_status} -> {retest_result.status}")
                    # Update live_stats if tracking
                    if live_stats is not None:
                        self._update_live_stats(live_stats, retest_result, stats_lock)

        # Map results back to original URL order, creating copies for duplicates
        results = []
        for url in urls:
            original_result = unique_results.get(url)
            if original_result:
                # First occurrence gets the original result; duplicates get a copy
                if not results or results[-1] is not original_result or url != results[-1].url:
                    # Check if we already added this exact object
                    already_added = any(r is original_result for r in results)
                    if already_added:
                        # Create a copy for duplicate URLs
                        dup_result = copy.copy(original_result)
                        results.append(dup_result)
                    else:
                        results.append(original_result)
                else:
                    dup_result = copy.copy(original_result)
                    results.append(dup_result)
            else:
                # Should not happen, but handle gracefully
                fallback = ValidationResult(url=url, auth_used=auth_used)
                fallback.status = 'BROKEN'
                fallback.message = 'Validation result missing'
                results.append(fallback)

        return results

    def _retest_broken_links(
        self,
        broken_urls: List[str],
        original_results: Dict[str, 'ValidationResult'],
        options: Dict[str, Any],
        headers: Dict[str, str],
        auth_used: str,
        live_stats: Optional[Dict[str, Any]] = None,
        stats_lock=None
    ) -> Dict[str, 'ValidationResult']:
        """
        Re-test links that were initially marked broken using more aggressive settings.

        Strategy for each broken link:
        1. Fresh session (no connection reuse issues)
        2. Longer timeouts (45s connect, 90s read)
        3. More retries (5 attempts)
        4. Try without SSL verification for SSL errors
        5. Try without auth headers for 403/blocked
        6. Try GET-only (skip HEAD entirely)
        7. Check if domain resolves even if page doesn't respond (DNS validation)
        8. Verify Content-Type header to confirm real response vs error page

        Returns:
            Dict mapping URL -> new ValidationResult (only for links that improved)
        """
        if not REQUESTS_AVAILABLE or not broken_urls:
            return {}

        retest_results = {}
        verify_ssl = options.get('verify_ssl', self.verify_ssl)
        ca_bundle = options.get('ca_bundle', self.ca_bundle)

        # Create a fresh session with extended timeouts
        retest_session = requests.Session()

        # Configure auth same as primary
        client_cert = options.get('client_cert', self.client_cert)
        if client_cert:
            retest_session.cert = client_cert
        if ca_bundle:
            retest_session.verify = ca_bundle
        elif verify_ssl:
            retest_session.verify = True
        else:
            retest_session.verify = False

        if WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth and not client_cert:
            try:
                retest_session.auth = HttpNegotiateAuth()
            except Exception:
                pass

        # Extended timeouts for retest
        connect_timeout = 30
        read_timeout = 60

        def _retest_single(url: str) -> Optional['ValidationResult']:
            """Retest a single URL with multiple fallback strategies."""
            original = original_results[url]
            result = ValidationResult(url=url, auth_used=auth_used)
            result.domain_category = original.domain_category

            strategies = []

            # Strategy 1: Standard GET with extended timeout (always try this)
            strategies.append(('get_extended', {'verify': retest_session.verify, 'auth': retest_session.auth}))

            # Strategy 2: For SSL errors, try without verification
            if original.status in ('SSLERROR', 'BROKEN') and url.startswith('https://'):
                strategies.append(('get_no_ssl', {'verify': False, 'auth': retest_session.auth}))

            # Strategy 3: For auth/blocked, try without auth headers
            if original.status in ('BLOCKED', 'AUTH_REQUIRED', 'BROKEN'):
                strategies.append(('get_no_auth', {'verify': retest_session.verify, 'auth': None}))

            # Strategy 3b: For internal links, try with explicit NTLM if available
            if original.status in ('BLOCKED', 'AUTH_REQUIRED', 'BROKEN', 'TIMEOUT'):
                parsed_url = urlparse(url)
                # v5.9.29: Expanded to include NGC corporate domains
                is_internal = any(d in parsed_url.netloc.lower()
                                  for d in ('.mil', '.gov', 'intranet', 'internal',
                                            'sharepoint', 'teams.microsoft',
                                            '.myngc.com', '.northgrum.com',
                                            '.northropgrumman.com', 'ngc.sharepoint.us'))
                if is_internal and WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
                    strategies.append(('get_fresh_auth', {'verify': retest_session.verify, 'auth': 'fresh_sso'}))

            # Strategy 4: For timeouts, try with much longer timeout
            if original.status == 'TIMEOUT':
                strategies.append(('get_ultra_timeout', {'verify': retest_session.verify, 'auth': retest_session.auth, 'timeout': (45, 90)}))

            for strategy_name, strategy_opts in strategies:
                try:
                    s_verify = strategy_opts.get('verify', True)
                    s_auth = strategy_opts.get('auth', None)
                    s_timeout = strategy_opts.get('timeout', (connect_timeout, read_timeout))

                    # Use a one-off session for auth override strategies
                    if s_auth == 'fresh_sso':
                        # Create a brand new session with fresh Windows SSO auth
                        fresh_session = requests.Session()
                        fresh_session.verify = s_verify
                        try:
                            fresh_session.auth = HttpNegotiateAuth()
                        except Exception:
                            continue  # SSO setup failed, skip this strategy
                        resp = fresh_session.get(
                            url, timeout=s_timeout, allow_redirects=True,
                            headers=headers, stream=True
                        )
                        fresh_session.close()
                    elif s_auth is None and retest_session.auth is not None:
                        resp = requests.get(
                            url, timeout=s_timeout, allow_redirects=True,
                            headers=headers, verify=s_verify, stream=True
                        )
                    else:
                        resp = retest_session.get(
                            url, timeout=s_timeout, allow_redirects=True,
                            headers=headers, verify=s_verify, stream=True
                        )

                    result.status_code = resp.status_code

                    # Check Content-Type to verify real response
                    content_type = resp.headers.get('Content-Type', '')

                    resp.close()

                    if 200 <= resp.status_code < 300:
                        if strategy_name == 'get_no_ssl':
                            result.status = 'SSL_WARNING'
                            result.ssl_valid = False
                            result.message = f'Link works but SSL certificate invalid (retest strategy: {strategy_name})'
                        else:
                            result.status = 'WORKING'
                            result.message = f'HTTP {resp.status_code} OK (confirmed on retest)'
                        return result

                    elif 300 <= resp.status_code < 400:
                        result.status = 'REDIRECT'
                        result.message = f'Redirect (confirmed on retest) to {resp.headers.get("Location", "unknown")}'
                        return result

                    elif resp.status_code == 401:
                        # 401 means server responded — link exists, just needs auth
                        result.status = 'AUTH_REQUIRED'
                        result.message = 'Link exists - authentication required (confirmed on retest)'
                        return result

                    elif resp.status_code == 403:
                        if strategy_name == 'get_no_auth':
                            # Still 403 without auth — likely permission-based, not broken
                            result.status = 'AUTH_REQUIRED'
                            result.message = 'Link exists - access restricted (confirmed on retest)'
                            return result

                except requests.exceptions.SSLError:
                    if strategy_name != 'get_no_ssl':
                        continue  # Try next strategy
                except requests.exceptions.Timeout:
                    continue  # Try next strategy
                except requests.exceptions.ConnectionError:
                    continue  # Try next strategy
                except Exception as e:
                    logger.debug(f"Retest strategy {strategy_name} failed for {url}: {e}")
                    continue

            # DNS-only check: if all HTTP strategies failed, at least check if hostname resolves
            try:
                parsed = urlparse(url)
                hostname = parsed.netloc.split(':')[0] if parsed.netloc else ''
                if hostname:
                    socket.setdefaulttimeout(10)
                    ip = socket.gethostbyname(hostname)
                    if ip:
                        # Domain resolves but server doesn't respond properly
                        # Don't upgrade to WORKING, but note DNS is valid
                        result.dns_resolved = True
                        result.dns_ip_addresses = [ip]
            except Exception:
                pass

            return None  # No improvement found

        # Run retests concurrently but with fewer workers (gentler on servers)
        max_retest_workers = min(5, len(broken_urls))

        with ThreadPoolExecutor(max_workers=max_retest_workers) as executor:
            future_to_url = {
                executor.submit(_retest_single, url): url
                for url in broken_urls
            }
            retest_completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    retest_result = future.result()
                    if retest_result is not None:
                        retest_results[url] = retest_result
                except Exception as e:
                    logger.debug(f"Retest failed for {url}: {e}")
                # v5.0.5: Update retest progress in live_stats
                retest_completed += 1
                if live_stats is not None:
                    live_stats['retest_completed'] = retest_completed
                    live_stats['current_url'] = url[:80] if url else None

        retest_session.close()

        # =====================================================================
        # HEADLESS BROWSER FALLBACK for .mil/.gov and stubborn sites
        # If playwright is available, try a real browser for remaining failures
        # This handles bot protection, JavaScript-required pages, and sites that
        # reject all programmatic requests (like dcma.mil)
        # =====================================================================
        if HEADLESS_VALIDATOR_AVAILABLE and HeadlessValidatorClass:
            still_broken = [url for url in broken_urls if url not in retest_results]
            if still_broken:
                # Prioritize .mil/.gov and internal sites for headless
                priority_urls = [u for u in still_broken
                                 if any(d in u.lower() for d in ('.mil', '.gov', '.mil/', '.gov/',
                                                                  'intranet', 'internal', 'sharepoint',
                                                                  'teams.microsoft'))]
                # Also include remaining broken URLs up to a cap
                other_broken = [u for u in still_broken if u not in priority_urls]
                headless_urls = priority_urls + other_broken[:50]  # Cap at 50 to avoid long waits

                if headless_urls:
                    logger.info(f"Headless browser fallback: trying {len(headless_urls)} URLs "
                                f"({len(priority_urls)} .mil/.gov priority)")
                    try:
                        headless_val = HeadlessValidatorClass(timeout=45, headless=True)
                        with headless_val:
                            for h_url in headless_urls:
                                try:
                                    h_result = headless_val.validate_url(h_url)
                                    if h_result.status in ('WORKING', 'REDIRECT'):
                                        # Headless browser confirmed the link works!
                                        upgraded_result = ValidationResult(url=h_url, auth_used=auth_used)
                                        upgraded_result.status = h_result.status
                                        upgraded_result.status_code = h_result.status_code
                                        upgraded_result.message = h_result.message
                                        upgraded_result.response_time_ms = h_result.response_time_ms
                                        if h_result.final_url:
                                            upgraded_result.redirect_url = h_result.final_url
                                        retest_results[h_url] = upgraded_result
                                        logger.info(f"Headless recovered: {h_url} -> {h_result.status}")
                                    elif h_result.status == 'AUTH_REQUIRED':
                                        upgraded_result = ValidationResult(url=h_url, auth_used=auth_used)
                                        upgraded_result.status = 'AUTH_REQUIRED'
                                        upgraded_result.status_code = h_result.status_code
                                        upgraded_result.message = f'Link exists, requires auth (headless confirmed)'
                                        retest_results[h_url] = upgraded_result
                                except Exception as e:
                                    logger.debug(f"Headless validation failed for {h_url}: {e}")
                    except Exception as e:
                        logger.warning(f"Headless browser fallback failed: {e}")

        upgraded = len(retest_results)
        if upgraded > 0:
            logger.info(f"Re-test complete: {upgraded}/{len(broken_urls)} links upgraded from broken")
        else:
            logger.info(f"Re-test complete: all {len(broken_urls)} broken links confirmed broken")

        return retest_results

    # =========================================================================
    # HISTORY MANAGEMENT
    # =========================================================================

    @classmethod
    def get_history(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent validation run history.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summaries (most recent first)
        """
        with cls._lock:
            runs = list(cls._validation_runs.values())

        # Sort by created_at descending
        runs.sort(key=lambda r: r.created_at, reverse=True)

        # Return summaries only
        history = []
        for run in runs[:limit]:
            entry = {
                'run_id': run.run_id,
                'job_id': run.job_id,
                'created_at': run.created_at,
                'completed_at': run.completed_at,
                'mode': run.mode,
                'status': run.status,
                'url_count': len(run.results) if run.results else 0
            }
            if run.summary:
                entry['summary'] = {
                    'working': run.summary.working,
                    'broken': run.summary.broken,
                    'total': run.summary.total
                }
            history.append(entry)

        return history

    @classmethod
    def clear_history(cls):
        """Clear all validation history."""
        with cls._lock:
            cls._validation_runs.clear()


# =============================================================================
# THOROUGH VALIDATION FUNCTIONS
# =============================================================================

def check_dns_resolution(hostname: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Check if hostname resolves to an IP address.

    Args:
        hostname: The hostname to resolve
        timeout: Socket timeout in seconds

    Returns:
        dict with 'resolved', 'ip_addresses', 'response_time_ms'
    """
    start = time.time()
    try:
        socket.setdefaulttimeout(timeout)
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        return {
            'resolved': True,
            'ip_addresses': ip_addresses,
            'response_time_ms': round((time.time() - start) * 1000, 2)
        }
    except socket.gaierror as e:
        return {
            'resolved': False,
            'ip_addresses': [],
            'response_time_ms': round((time.time() - start) * 1000, 2),
            'error': str(e)
        }
    except Exception as e:
        return {
            'resolved': False,
            'ip_addresses': [],
            'response_time_ms': round((time.time() - start) * 1000, 2),
            'error': str(e)
        }


def check_ssl_certificate(hostname: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """
    Check SSL certificate validity and expiration.

    Args:
        hostname: The hostname to check
        port: SSL port (default 443)
        timeout: Connection timeout

    Returns:
        dict with 'valid', 'issuer', 'expires', 'days_until_expiry', 'warning'
    """
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expires_str = cert.get('notAfter', '')

                # Parse expiration date
                try:
                    expires = datetime.strptime(expires_str, '%b %d %H:%M:%S %Y %Z')
                except ValueError:
                    expires = datetime.now()

                days_until = (expires - datetime.now()).days

                # Extract issuer info
                issuer_info = cert.get('issuer', ())
                issuer_name = 'Unknown'
                for item in issuer_info:
                    for key, value in item:
                        if key == 'organizationName':
                            issuer_name = value
                            break

                warning = None
                if days_until < 30:
                    warning = f'Certificate expires in {days_until} days'
                elif days_until < 0:
                    warning = 'Certificate has expired!'

                return {
                    'valid': True,
                    'issuer': issuer_name,
                    'expires': expires.strftime('%Y-%m-%d'),
                    'days_until_expiry': days_until,
                    'warning': warning
                }
    except ssl.SSLError as e:
        return {
            'valid': False,
            'error': f'SSL Error: {str(e)}'
        }
    except socket.timeout:
        return {
            'valid': False,
            'error': 'Connection timeout'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }


def detect_soft_404(response_text: str) -> bool:
    """
    Detect soft 404 pages that return 200 but are actually error pages.
    Uses a scoring system to require multiple signals before flagging as soft-404.
    This reduces false positives on pages that casually mention "not found" etc.

    Args:
        response_text: HTML content of the page

    Returns:
        True if this appears to be a soft 404 page
    """
    import re
    text_lower = response_text.lower()
    score = 0

    # Very short response body is suspicious (real pages have content)
    # Strip HTML tags for length check
    stripped = re.sub(r'<[^>]+>', '', text_lower).strip()
    if len(stripped) < 500:
        score += 1  # Short pages more likely to be error pages

    # Title check — strongest signal
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', text_lower)
    if title_match:
        title = title_match.group(1)
        title_error_phrases = ['not found', '404', 'page missing', 'page unavailable', 'page does not exist']
        if any(phrase in title for phrase in title_error_phrases):
            score += 3  # Title match is a very strong signal

    # Body phrases — require in prominent context (headings, first 2000 chars)
    # Only check first 2000 chars to avoid matching phrases deep in page content
    early_text = text_lower[:2000]
    strong_body_phrases = [
        'page not found',
        'page you requested could not be found',
        "this page doesn't exist",
        'this page does not exist',
        'the requested url was not found',
        'oops! page not found',
        '404 error',
        'error 404'
    ]

    weak_body_phrases = [
        "we couldn't find",
        'we could not find',
        'no longer available',
        'has been removed',
        'has been deleted',
        'content is unavailable',
        'content not available',
        "sorry, we can't find",
    ]

    # Strong phrases in early content
    for phrase in strong_body_phrases:
        if phrase in early_text:
            score += 2
            break  # One match is enough

    # Weak phrases only count if also short page
    for phrase in weak_body_phrases:
        if phrase in early_text:
            score += 1
            break

    # Check for 404 in heading tags (strong signal)
    heading_404 = re.search(r'<h[1-3][^>]*>[^<]*(?:404|not found|page missing)[^<]*</h[1-3]>', text_lower)
    if heading_404:
        score += 2

    # Require score >= 3 to flag as soft-404 (reduces false positives significantly)
    return score >= 3


def detect_suspicious_url(url: str) -> Dict[str, Any]:
    """
    Detect potentially suspicious URLs.

    Args:
        url: The URL to analyze

    Returns:
        dict with 'suspicious' (bool) and 'reasons' (list)
    """
    import re
    reasons = []

    try:
        parsed = urlparse(url)
        domain = parsed.netloc
    except Exception:
        return {'suspicious': True, 'reasons': ['Invalid URL format']}

    # IP address instead of domain
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
        reasons.append('Uses IP address instead of domain name')

    # URL shorteners
    shorteners = [
        'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
        'is.gd', 'buff.ly', 'j.mp', 'tiny.cc', 'rb.gy'
    ]
    if any(s in domain.lower() for s in shorteners):
        reasons.append('URL shortener - destination unknown')

    # @ symbol in URL (potential credential harvesting)
    if '@' in url.split('?')[0]:  # Before query string
        reasons.append('Contains @ symbol (potential phishing)')

    # Very long subdomain chains
    subdomain_count = domain.count('.')
    if subdomain_count > 4:
        reasons.append(f'Unusual subdomain depth ({subdomain_count} levels)')

    # Numeric-heavy domain
    domain_without_tld = '.'.join(domain.split('.')[:-1])
    if domain_without_tld:
        digit_ratio = sum(c.isdigit() for c in domain_without_tld) / len(domain_without_tld)
        if digit_ratio > 0.5:
            reasons.append('Domain is mostly numeric')

    # Very long domain name
    if len(domain) > 50:
        reasons.append('Unusually long domain name')

    # Port in URL (often suspicious for http/https)
    if parsed.port and parsed.port not in (80, 443, None):
        reasons.append(f'Non-standard port ({parsed.port})')

    return {
        'suspicious': len(reasons) > 0,
        'reasons': reasons
    }


# =============================================================================
# COMPREHENSIVE LINK VALIDATION
# =============================================================================

def validate_any_link(
    link: str,
    check_typos: bool = True,
    check_exists: bool = False,
    document_structure: Optional[Dict] = None,
    available_bookmarks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate any type of link (URL, mailto, file path, UNC, bookmark, cross-ref).

    Args:
        link: The link to validate
        check_typos: Whether to check for common typos
        check_exists: Whether to verify file/network paths exist
        document_structure: Document structure for cross-reference validation
        available_bookmarks: List of valid bookmarks for bookmark validation

    Returns:
        Dictionary with validation results
    """
    result = {
        'link': link,
        'link_type': classify_link_type(link),
        'is_valid': False,
        'message': '',
        'warnings': [],
        'suggestions': []
    }

    link_type = result['link_type']

    # Check for typos first (for web URLs)
    if check_typos and link_type == LinkType.WEB_URL.value:
        has_typos, typo_issues = detect_url_typos(link)
        if has_typos:
            result['warnings'].extend(typo_issues)

    # Validate based on type
    if link_type == LinkType.WEB_URL.value:
        is_valid, error = validate_url_format(link)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid URL format'

    elif link_type == LinkType.MAILTO.value:
        is_valid, error = validate_mailto(link)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid mailto link'

    elif link_type == LinkType.FILE_PATH.value:
        is_valid, error = validate_file_path(link, check_exists=check_exists)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid file path'

    elif link_type == LinkType.NETWORK_PATH.value:
        is_valid, error = validate_network_path(link, check_accessible=check_exists)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid network path'

    elif link_type == LinkType.BOOKMARK.value:
        is_valid, error = validate_internal_bookmark(link, available_bookmarks)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid bookmark'

    elif link_type == LinkType.CROSS_REFERENCE.value:
        is_valid, error = validate_cross_reference(link, document_structure)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid cross-reference'

    elif link_type == LinkType.FTP.value:
        # Basic FTP URL validation
        is_valid, error = validate_url_format(link)
        result['is_valid'] = is_valid
        result['message'] = error if error else 'Valid FTP URL (not network verified)'

    else:
        result['message'] = 'Unknown link type'

    return result


def validate_docx_links(
    file_path: str,
    validate_web_urls: bool = True,
    check_bookmarks: bool = True,
    check_cross_refs: bool = True
) -> Dict[str, Any]:
    """
    Extract and validate all hyperlinks from a DOCX file.

    Args:
        file_path: Path to the DOCX file
        validate_web_urls: Whether to validate web URLs (requires network)
        check_bookmarks: Whether to validate internal bookmarks
        check_cross_refs: Whether to validate cross-references

    Returns:
        Dictionary with extraction results, validation results, and summary
    """
    if not DOCX_EXTRACTION_AVAILABLE:
        return {
            'error': 'DOCX extraction not available',
            'links': [],
            'structure': {},
            'validation_results': []
        }

    # Extract links and structure
    extractor = DocxExtractor()
    extraction = extractor.extract(file_path)

    if extraction.errors:
        return {
            'error': '; '.join(extraction.errors),
            'links': [],
            'structure': {},
            'validation_results': []
        }

    # Prepare document structure for validation
    doc_structure = extraction.structure.to_dict()
    available_bookmarks = extraction.structure.bookmarks

    # Validate each link
    validation_results = []
    web_urls = []  # Collect for batch web validation

    for link in extraction.links:
        link_type = link.link_type

        if link_type == 'web_url' and validate_web_urls:
            web_urls.append(link.url)
            # Will validate later in batch
            continue

        elif link_type == 'bookmark' and check_bookmarks:
            result = validate_any_link(
                link.url,
                check_typos=False,
                available_bookmarks=available_bookmarks
            )

        elif link_type == 'cross_ref' and check_cross_refs:
            result = validate_any_link(
                link.url,
                check_typos=False,
                document_structure=doc_structure
            )

        else:
            result = validate_any_link(link.url, check_typos=True)

        validation_results.append({
            'link': link.to_dict(),
            'validation': result
        })

    # Batch validate web URLs
    if web_urls and validate_web_urls:
        validator = StandaloneHyperlinkValidator()
        run = validator.validate_urls_sync(web_urls, mode='validator')

        for vr in run.results:
            # Find matching link
            matching_link = next(
                (l for l in extraction.links if l.url == vr.url),
                None
            )
            validation_results.append({
                'link': matching_link.to_dict() if matching_link else {'url': vr.url},
                'validation': {
                    'link': vr.url,
                    'link_type': 'web_url',
                    'is_valid': vr.is_valid,
                    'message': vr.message,
                    'status': vr.status,
                    'status_code': vr.status_code,
                    'warnings': []
                }
            })

    # Generate summary
    total = len(validation_results)
    valid = sum(1 for r in validation_results if r['validation'].get('is_valid', False))
    invalid = total - valid

    return {
        'file_path': file_path,
        'links': [link.to_dict() for link in extraction.links],
        'structure': doc_structure,
        'metadata': extraction.metadata,
        'validation_results': validation_results,
        'summary': {
            'total_links': total,
            'valid': valid,
            'invalid': invalid,
            'by_type': {}
        }
    }


# Convenience function for simple validation
def validate_urls(
    urls: List[str],
    mode: str = 'validator',
    scan_depth: str = 'standard',
    timeout: int = 10,
    use_windows_auth: bool = True,
    exclusions: Optional[List[Dict]] = None
) -> ValidationRun:
    """
    Convenience function for simple URL validation.

    Args:
        urls: List of URLs to validate
        mode: Validation mode (offline, validator, ps1_validator)
        scan_depth: Scan depth (quick, standard, thorough)
        timeout: Request timeout in seconds
        use_windows_auth: Whether to use Windows SSO
        exclusions: List of exclusion rule dicts

    Returns:
        ValidationRun with results
    """
    validator = StandaloneHyperlinkValidator(
        timeout=timeout,
        use_windows_auth=use_windows_auth
    )

    options = {
        'scan_depth': scan_depth,
        'exclusions': exclusions or []
    }

    return validator.validate_urls_sync(urls, mode=mode, options=options)
