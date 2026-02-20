"""
Hyperlink Validator Data Models
===============================
Dataclasses for validation requests, results, and summaries.

This module is designed to be independent and can be tested separately
from the rest of the validation system.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json


class ValidationStatus(Enum):
    """Status codes returned by URL validation."""
    WORKING = "WORKING"           # URL returned HTTP 200
    BROKEN = "BROKEN"             # URL returned 4xx/5xx or connection failed
    REDIRECT = "REDIRECT"         # URL returned 3xx redirect
    TIMEOUT = "TIMEOUT"           # Connection timed out
    BLOCKED = "BLOCKED"           # Access denied or filtered (403, connection refused)
    AUTH_REQUIRED = "AUTH_REQUIRED"  # Link exists but requires authentication (401/403)
    SSL_WARNING = "SSL_WARNING"   # Link works but has SSL certificate issues
    RATE_LIMITED = "RATE_LIMITED"  # Server rate-limited the request (429)
    DNSFAILED = "DNSFAILED"       # Could not resolve hostname
    SSLERROR = "SSLERROR"         # SSL/TLS certificate error
    INVALID = "INVALID"           # Invalid URL format
    UNKNOWN = "UNKNOWN"           # Could not determine status
    PENDING = "PENDING"           # Not yet validated
    SKIPPED = "SKIPPED"           # Skipped (e.g., unsupported protocol)


class ValidationMode(Enum):
    """Available validation modes."""
    OFFLINE = "offline"           # Format validation only
    VALIDATOR = "validator"       # Python requests with Windows SSO
    PS1_VALIDATOR = "ps1_validator"  # PowerShell HyperlinkValidator.ps1


class ScanDepth(Enum):
    """Scan depth/thoroughness levels."""
    QUICK = "quick"               # Format validation only (fastest)
    STANDARD = "standard"         # Basic HTTP check (default)
    THOROUGH = "thorough"         # Full validation: DNS, SSL, redirects, soft-404


class DomainCategory(Enum):
    """Domain categorization for metrics."""
    GOVERNMENT = "government"     # .gov, .mil
    EDUCATIONAL = "educational"   # .edu
    COMMERCIAL = "commercial"     # .com, .co, .biz, .io, .tech, .net
    ORGANIZATION = "organization" # .org
    INTERNAL = "internal"         # sharepoint, intranet, localhost
    OTHER = "other"


class LinkType(Enum):
    """Classification of link types for comprehensive validation."""
    WEB_URL = "web_url"               # http:// or https:// URLs
    MAILTO = "mailto"                 # mailto: email links
    FILE_PATH = "file_path"           # Local/relative file paths
    NETWORK_PATH = "network_path"     # UNC paths (\\server\share)
    INTERNAL_BOOKMARK = "bookmark"    # #bookmark links within document
    CROSS_REFERENCE = "cross_ref"     # Section 1.2, Table 3, Figure 4, etc.
    FTP = "ftp"                       # ftp:// links
    UNKNOWN = "unknown"               # Unclassified


@dataclass
class ExclusionRule:
    """
    Rule for excluding URLs from validation or marking them as OK.

    Attributes:
        pattern: URL pattern to match (exact, prefix, suffix, or regex)
        match_type: How to match ('exact', 'prefix', 'suffix', 'contains', 'regex')
        reason: Why this URL is excluded
        treat_as_valid: If True, treat matched URLs as WORKING; if False, skip them
        created_at: When rule was created
    """
    pattern: str
    match_type: str = "contains"  # exact, prefix, suffix, contains, regex
    reason: str = ""
    treat_as_valid: bool = True   # True = show as OK, False = skip entirely
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

    def matches(self, url: str) -> bool:
        """Check if URL matches this exclusion rule.

        v5.9.35: 'exact' match now also checks trailing-slash and protocol variants
        to handle common URL normalization differences.
        """
        import re
        url_lower = url.lower().strip()
        pattern_lower = self.pattern.lower().strip()

        if self.match_type == "exact":
            # v5.9.35: Also match trailing-slash variants and protocol variants
            url_norm = url_lower.rstrip('/')
            pattern_norm = pattern_lower.rstrip('/')
            if url_norm == pattern_norm:
                return True
            # Also check http↔https swap
            if url_norm.startswith('http://'):
                if url_norm.replace('http://', 'https://') == pattern_norm:
                    return True
            elif url_norm.startswith('https://'):
                if url_norm.replace('https://', 'http://') == pattern_norm:
                    return True
            return False
        elif self.match_type == "prefix":
            return url_lower.startswith(pattern_lower)
        elif self.match_type == "suffix":
            return url_lower.endswith(pattern_lower)
        elif self.match_type == "contains":
            return pattern_lower in url_lower
        elif self.match_type == "regex":
            try:
                return bool(re.search(self.pattern, url, re.IGNORECASE))
            except re.error:
                return False
        return False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExclusionRule':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


@dataclass
class ValidationRequest:
    """
    Request parameters for URL validation.

    Attributes:
        urls: List of URLs to validate
        mode: Validation mode (offline, validator, ps1_validator)
        scan_depth: Scan thoroughness (quick, standard, thorough)
        timeout: Request timeout in seconds
        retries: Number of retry attempts for failed requests
        use_windows_auth: Whether to use Windows SSO authentication
        follow_redirects: Whether to follow HTTP redirects
        check_ssl: Whether to validate SSL certificates
        check_dns: Whether to perform DNS resolution check
        detect_soft_404: Whether to detect soft 404 pages
        check_suspicious: Whether to check for suspicious URLs
        exclusions: List of exclusion rules
        batch_size: Number of URLs to process in each batch
        max_concurrent: Maximum concurrent validations (future use)
    """
    urls: List[str]
    mode: str = "validator"
    scan_depth: str = "standard"  # quick, standard, thorough
    timeout: int = 10
    retries: int = 3
    use_windows_auth: bool = True
    follow_redirects: bool = True
    check_ssl: bool = True
    check_dns: bool = False       # Only in thorough mode by default
    detect_soft_404: bool = False # Only in thorough mode by default
    check_suspicious: bool = False # Only in thorough mode by default
    exclusions: List[ExclusionRule] = field(default_factory=list)
    batch_size: int = 50
    max_concurrent: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert exclusions properly
        data['exclusions'] = [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.exclusions]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRequest':
        """Create from dictionary."""
        # Handle exclusions specially
        exclusions = []
        if 'exclusions' in data:
            for exc in data['exclusions']:
                if isinstance(exc, dict):
                    exclusions.append(ExclusionRule.from_dict(exc))
                elif isinstance(exc, ExclusionRule):
                    exclusions.append(exc)
            data = {k: v for k, v in data.items() if k != 'exclusions'}

        # Filter to only valid fields
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        valid_fields['exclusions'] = exclusions
        return cls(**valid_fields)

    def validate(self) -> List[str]:
        """
        Validate request parameters.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if not self.urls:
            errors.append("No URLs provided")
        if self.mode not in [m.value for m in ValidationMode]:
            errors.append(f"Invalid mode: {self.mode}")
        if self.scan_depth not in [s.value for s in ScanDepth]:
            errors.append(f"Invalid scan depth: {self.scan_depth}")
        if self.timeout < 1 or self.timeout > 120:
            errors.append("Timeout must be between 1 and 120 seconds")
        if self.retries < 0 or self.retries > 10:
            errors.append("Retries must be between 0 and 10")
        if self.batch_size < 1 or self.batch_size > 500:
            errors.append("Batch size must be between 1 and 500")
        return errors

    def apply_scan_depth_defaults(self):
        """Apply default settings based on scan depth."""
        if self.scan_depth == ScanDepth.QUICK.value:
            # Quick: format only, no network
            self.check_dns = False
            self.check_ssl = False
            self.detect_soft_404 = False
            self.check_suspicious = False
            self.retries = 0
        elif self.scan_depth == ScanDepth.THOROUGH.value:
            # Thorough: all checks enabled
            self.check_dns = True
            self.check_ssl = True
            self.detect_soft_404 = True
            self.check_suspicious = True
            self.retries = 3
        # Standard uses current settings

    def get_exclusion_for_url(self, url: str) -> Optional[ExclusionRule]:
        """Check if URL matches any exclusion rule."""
        for exclusion in self.exclusions:
            if exclusion.matches(url):
                return exclusion
        return None


@dataclass
class ValidationResult:
    """
    Result of validating a single URL.

    Attributes:
        url: The URL that was validated
        status: Validation status (WORKING, BROKEN, etc.)
        status_code: HTTP status code if applicable
        message: Human-readable status message
        redirect_url: Final URL after redirects (if applicable)
        redirect_count: Number of redirects followed
        redirect_chain: Full redirect chain (thorough mode)
        response_time_ms: Time taken for validation in milliseconds
        checked_at: ISO timestamp of when validation occurred
        dns_resolved: Whether DNS resolution succeeded
        dns_ip_addresses: Resolved IP addresses
        dns_response_time_ms: DNS resolution time
        ssl_valid: Whether SSL certificate is valid
        ssl_expires: SSL certificate expiration date (if checked)
        ssl_issuer: SSL certificate issuer
        ssl_days_until_expiry: Days until SSL expires
        ssl_warning: SSL warning message if any
        is_soft_404: Whether page is a soft 404
        domain_category: Category of the domain
        is_suspicious: Whether URL appears suspicious
        suspicious_reasons: List of reasons URL is suspicious
        auth_used: Authentication method used (none, windows_sso)
        attempts: Number of attempts made
        error_detail: Detailed error information (if failed)
        excluded: Whether URL was excluded
        exclusion_reason: Why URL was excluded
        original_status: Original status before exclusion override
    """
    url: str
    status: str = "PENDING"
    status_code: Optional[int] = None
    message: str = ""
    redirect_url: Optional[str] = None
    redirect_count: int = 0
    redirect_chain: List[Dict] = field(default_factory=list)
    response_time_ms: float = 0.0
    checked_at: str = ""
    dns_resolved: bool = False
    dns_ip_addresses: List[str] = field(default_factory=list)
    dns_response_time_ms: float = 0.0
    ssl_valid: bool = False
    ssl_expires: Optional[str] = None
    ssl_issuer: str = ""
    ssl_days_until_expiry: int = 0
    ssl_warning: Optional[str] = None
    is_soft_404: bool = False
    domain_category: str = "other"
    is_suspicious: bool = False
    suspicious_reasons: List[str] = field(default_factory=list)
    auth_used: str = "none"
    attempts: int = 0
    error_detail: Optional[str] = None
    # Exclusion fields
    excluded: bool = False
    exclusion_reason: str = ""
    original_status: Optional[str] = None

    def __post_init__(self):
        """Set checked_at if not provided."""
        if not self.checked_at:
            self.checked_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create from dictionary."""
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    @classmethod
    def from_ps1_result(cls, ps1_result: Dict[str, Any]) -> 'ValidationResult':
        """
        Create from PowerShell validator result.

        Maps PS1 output fields to ValidationResult fields.
        """
        return cls(
            url=ps1_result.get('url', ''),
            status=ps1_result.get('status', 'UNKNOWN').upper(),
            status_code=ps1_result.get('statusCode'),
            message=ps1_result.get('message', ''),
            redirect_url=ps1_result.get('redirectUrl'),
            redirect_count=ps1_result.get('redirectCount', 0),
            response_time_ms=ps1_result.get('responseTimeMs', 0.0),
            checked_at=ps1_result.get('checkedAt', datetime.utcnow().isoformat() + "Z")
        )

    @property
    def is_valid(self) -> bool:
        """Check if URL is valid/working."""
        return self.status in ['WORKING', 'REDIRECT', 'SSL_WARNING', 'AUTH_REQUIRED']

    @property
    def is_error(self) -> bool:
        """Check if URL has an error."""
        return self.status in ['BROKEN', 'TIMEOUT', 'DNSFAILED', 'SSLERROR', 'INVALID']

    @property
    def domain(self) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            return parsed.netloc or self.url
        except Exception:
            return self.url


@dataclass
class ValidationSummary:
    """
    Summary statistics for a validation run.

    Attributes:
        total: Total number of URLs validated
        working: Count of working URLs (HTTP 200)
        broken: Count of broken URLs (4xx/5xx errors)
        redirect: Count of redirecting URLs
        timeout: Count of timed out URLs
        blocked: Count of blocked URLs
        dns_failed: Count of DNS failures
        ssl_error: Count of SSL errors
        invalid: Count of invalid URL formats
        unknown: Count of unknown status
        skipped: Count of skipped URLs
        excluded: Count of excluded URLs (treated as OK)
        by_domain: Breakdown by domain
        by_domain_category: Breakdown by domain category
        by_status_code: Breakdown by HTTP status code
        ssl_warnings: Count of SSL certificate warnings
        soft_404_count: Count of soft 404 pages detected
        suspicious_count: Count of suspicious URLs
        average_response_ms: Average response time
        min_response_ms: Minimum response time
        max_response_ms: Maximum response time
        total_time_seconds: Total validation time
        scan_depth: Scan depth used
    """
    total: int = 0
    working: int = 0
    broken: int = 0
    redirect: int = 0
    timeout: int = 0
    blocked: int = 0
    dns_failed: int = 0
    ssl_error: int = 0
    invalid: int = 0
    unknown: int = 0
    skipped: int = 0
    pending: int = 0
    excluded: int = 0
    by_domain: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_domain_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_status_code: Dict[int, int] = field(default_factory=dict)
    ssl_warnings: int = 0
    soft_404_count: int = 0
    suspicious_count: int = 0
    average_response_ms: float = 0.0
    min_response_ms: float = 0.0
    max_response_ms: float = 0.0
    total_time_seconds: float = 0.0
    scan_depth: str = "standard"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_results(cls, results: List[ValidationResult], total_time: float = 0.0,
                     scan_depth: str = "standard") -> 'ValidationSummary':
        """
        Calculate summary from list of results.

        Args:
            results: List of ValidationResult objects
            total_time: Total validation time in seconds
            scan_depth: Scan depth used

        Returns:
            ValidationSummary with calculated statistics
        """
        summary = cls(total=len(results), total_time_seconds=total_time, scan_depth=scan_depth)

        response_times = []

        for result in results:
            # Count excluded URLs
            if result.excluded:
                summary.excluded += 1

            # Count by status
            status = result.status.upper()
            if status == 'WORKING':
                summary.working += 1
            elif status == 'BROKEN':
                summary.broken += 1
            elif status == 'REDIRECT':
                summary.redirect += 1
            elif status == 'TIMEOUT':
                summary.timeout += 1
            elif status == 'BLOCKED':
                summary.blocked += 1
            elif status == 'DNSFAILED':
                summary.dns_failed += 1
            elif status == 'SSLERROR':
                summary.ssl_error += 1
            elif status == 'INVALID':
                summary.invalid += 1
            elif status == 'SKIPPED':
                summary.skipped += 1
            elif status == 'PENDING':
                summary.pending += 1
            else:
                summary.unknown += 1

            # Count by domain
            domain = result.domain
            if domain:
                if domain not in summary.by_domain:
                    summary.by_domain[domain] = {'total': 0, 'working': 0, 'errors': 0}
                summary.by_domain[domain]['total'] += 1
                if result.is_valid:
                    summary.by_domain[domain]['working'] += 1
                elif result.is_error:
                    summary.by_domain[domain]['errors'] += 1

            # Count by domain category
            category = result.domain_category or 'other'
            if category not in summary.by_domain_category:
                summary.by_domain_category[category] = {'total': 0, 'working': 0, 'errors': 0}
            summary.by_domain_category[category]['total'] += 1
            if result.is_valid:
                summary.by_domain_category[category]['working'] += 1
            elif result.is_error:
                summary.by_domain_category[category]['errors'] += 1

            # Count by status code
            if result.status_code:
                code = result.status_code
                summary.by_status_code[code] = summary.by_status_code.get(code, 0) + 1

            # Count SSL warnings
            if result.ssl_warning:
                summary.ssl_warnings += 1

            # Count soft 404s
            if result.is_soft_404:
                summary.soft_404_count += 1

            # Count suspicious URLs
            if result.is_suspicious:
                summary.suspicious_count += 1

            # Collect response times
            if result.response_time_ms > 0:
                response_times.append(result.response_time_ms)

        # Calculate response time stats
        if response_times:
            summary.average_response_ms = sum(response_times) / len(response_times)
            summary.min_response_ms = min(response_times)
            summary.max_response_ms = max(response_times)

        return summary

    @property
    def error_count(self) -> int:
        """Total count of all error statuses."""
        return (self.broken + self.timeout + self.blocked +
                self.dns_failed + self.ssl_error + self.invalid)

    @property
    def success_rate(self) -> float:
        """Percentage of successful validations."""
        if self.total == 0:
            return 0.0
        return (self.working + self.redirect) / self.total * 100


@dataclass
class ValidationRun:
    """
    Complete record of a validation run.

    Attributes:
        run_id: Unique identifier for this run
        job_id: Associated job ID (for async operations)
        created_at: When the run was started
        completed_at: When the run finished (None if still running)
        mode: Validation mode used
        status: Run status (pending, running, complete, failed, cancelled)
        request: Original validation request
        results: List of validation results
        summary: Calculated summary statistics
        error: Error message if run failed
    """
    run_id: str
    job_id: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    mode: str = "validator"
    status: str = "pending"  # pending, running, complete, failed, cancelled
    request: Optional[ValidationRequest] = None
    results: List[ValidationResult] = field(default_factory=list)
    summary: Optional[ValidationSummary] = None
    error: Optional[str] = None

    def __post_init__(self):
        """Set created_at if not provided."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'run_id': self.run_id,
            'job_id': self.job_id,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'mode': self.mode,
            'status': self.status,
            'error': self.error
        }
        if self.request:
            data['request'] = self.request.to_dict()
        if self.results:
            data['results'] = [r.to_dict() for r in self.results]
        if self.summary:
            data['summary'] = self.summary.to_dict()
        return data

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRun':
        """Create from dictionary."""
        run = cls(
            run_id=data.get('run_id', ''),
            job_id=data.get('job_id'),
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at'),
            mode=data.get('mode', 'validator'),
            status=data.get('status', 'pending'),
            error=data.get('error')
        )
        if 'request' in data and data['request']:
            run.request = ValidationRequest.from_dict(data['request'])
        if 'results' in data:
            run.results = [ValidationResult.from_dict(r) for r in data['results']]
        if 'summary' in data and data['summary']:
            run.summary = ValidationSummary(**{k: v for k, v in data['summary'].items()
                                               if k in ValidationSummary.__dataclass_fields__})
        return run

    def complete(self, results: List[ValidationResult], total_time: float = 0.0):
        """
        Mark run as complete with results.

        Args:
            results: List of validation results
            total_time: Total validation time in seconds
        """
        self.status = "complete"
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.results = results
        self.summary = ValidationSummary.from_results(results, total_time)

    def fail(self, error: str):
        """Mark run as failed with error message."""
        self.status = "failed"
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.error = error

    def cancel(self):
        """Mark run as cancelled."""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow().isoformat() + "Z"


# Utility functions for URL parsing

def parse_url_list(text: str) -> List[str]:
    """
    Parse URLs from text input.

    Handles:
    - One URL per line
    - Comma-separated URLs
    - Mixed whitespace
    - Empty lines
    - Comments (lines starting with #)

    Args:
        text: Raw text containing URLs

    Returns:
        List of cleaned URLs
    """
    urls = []

    # Split by common delimiters
    lines = text.replace(',', '\n').replace(';', '\n').split('\n')

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Basic URL validation - must have scheme or look like URL
        if line.startswith(('http://', 'https://', 'ftp://')):
            urls.append(line)
        elif '.' in line and not line.startswith('.'):
            # Add https:// if missing scheme
            urls.append(f'https://{line}')

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def categorize_domain(url: str) -> str:
    """
    Categorize a URL's domain.

    Args:
        url: The URL to categorize

    Returns:
        Category string ('government', 'educational', 'commercial', 'internal', 'other')
    """
    from urllib.parse import urlparse

    DOMAIN_CATEGORIES = {
        'government': ['.gov', '.mil'],
        'educational': ['.edu'],
        'commercial': ['.com', '.co', '.biz', '.io', '.tech', '.net'],
        'organization': ['.org'],
        'internal': ['sharepoint.com', 'sharepoint.us', 'sharepoint',
                     'intranet', 'internal', 'localhost',
                     'myngc.com', 'northgrum.com', 'northropgrumman.com'],
    }

    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 'other'

    for category, patterns in DOMAIN_CATEGORIES.items():
        if any(pattern in domain for pattern in patterns):
            return category
    return 'other'


def validate_url_format(url: str) -> tuple[bool, str]:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Must have scheme
        if not parsed.scheme:
            return False, "Missing URL scheme (http:// or https://)"

        # Scheme must be supported
        if parsed.scheme not in ['http', 'https', 'ftp']:
            return False, f"Unsupported scheme: {parsed.scheme}"

        # Must have host
        if not parsed.netloc:
            return False, "Missing hostname"

        return True, ""

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


# =============================================================================
# LINK TYPE CLASSIFICATION
# =============================================================================

def classify_link_type(link: str) -> str:
    """
    Classify a link into its type.

    Args:
        link: The link/URL to classify

    Returns:
        LinkType value string
    """
    import re

    link_stripped = link.strip()

    # Internal bookmark
    if link_stripped.startswith('#'):
        return LinkType.BOOKMARK.value

    # Mailto
    if link_stripped.lower().startswith('mailto:'):
        return LinkType.MAILTO.value

    # Network path (UNC)
    if link_stripped.startswith('\\\\') or link_stripped.startswith('//'):
        return LinkType.NETWORK_PATH.value

    # FTP
    if link_stripped.lower().startswith('ftp://'):
        return LinkType.FTP.value

    # Web URL
    if link_stripped.lower().startswith(('http://', 'https://')):
        return LinkType.WEB_URL.value

    # Cross-reference patterns (Section 1.2, Table 3, Figure 4, Appendix A)
    cross_ref_pattern = r'^(Section|Table|Figure|Appendix|Paragraph|Chapter)\s+[\dA-Za-z]'
    if re.match(cross_ref_pattern, link_stripped, re.IGNORECASE):
        return LinkType.CROSS_REFERENCE.value

    # File path patterns
    file_path_patterns = [
        r'^[A-Za-z]:\\',           # Windows absolute: C:\path
        r'^\.{1,2}[/\\]',          # Relative: ./ or ../
        r'^/[^/]',                 # Unix absolute: /path
        r'\.(docx?|xlsx?|pptx?|pdf|txt|html?|xml|json|csv)$',  # File extensions
    ]
    for pattern in file_path_patterns:
        if re.search(pattern, link_stripped, re.IGNORECASE):
            return LinkType.FILE_PATH.value

    return LinkType.UNKNOWN.value


# =============================================================================
# MAILTO VALIDATION (RFC 5322)
# =============================================================================

def validate_mailto(link: str) -> tuple[bool, str]:
    """
    Validate a mailto: link.

    Args:
        link: The mailto: link to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    from urllib.parse import urlparse, parse_qs, unquote

    if not link.lower().startswith('mailto:'):
        return False, "Not a mailto link"

    # Extract email part
    mailto_content = link[7:]  # Remove 'mailto:'

    # Handle mailto with query params (subject, body, etc.)
    if '?' in mailto_content:
        email_part = mailto_content.split('?')[0]
    else:
        email_part = mailto_content

    # URL decode
    email_part = unquote(email_part)

    # Handle multiple recipients
    emails = [e.strip() for e in email_part.split(',') if e.strip()]

    if not emails:
        return False, "No email address provided"

    # RFC 5322 simplified email pattern
    # More permissive than strict RFC 5322 but catches most errors
    email_pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'

    for email in emails:
        if not re.match(email_pattern, email):
            return False, f"Invalid email format: {email}"

        # Check for common typos
        typo_result = detect_email_typos(email)
        if typo_result:
            return False, typo_result

    return True, ""


def detect_email_typos(email: str) -> Optional[str]:
    """
    Detect common typos in email addresses.

    Args:
        email: Email address to check

    Returns:
        Error message if typo detected, None otherwise
    """
    if '@' not in email:
        return "Missing @ symbol"

    local, domain = email.rsplit('@', 1)

    # Common domain typos
    domain_typos = {
        'gmial.com': 'gmail.com',
        'gmai.com': 'gmail.com',
        'gamil.com': 'gmail.com',
        'gnail.com': 'gmail.com',
        'hotmial.com': 'hotmail.com',
        'hotmal.com': 'hotmail.com',
        'homail.com': 'hotmail.com',
        'outlok.com': 'outlook.com',
        'outloo.com': 'outlook.com',
        'yahooo.com': 'yahoo.com',
        'yaho.com': 'yahoo.com',
    }

    if domain.lower() in domain_typos:
        return f"Possible typo: did you mean {domain_typos[domain.lower()]}?"

    # Check for missing TLD
    if '.' not in domain:
        return "Domain appears to be missing TLD (e.g., .com)"

    return None


# =============================================================================
# FILE PATH VALIDATION
# =============================================================================

def validate_file_path(path: str, check_exists: bool = True, base_dir: str = None) -> tuple[bool, str]:
    """
    Validate a file path.

    Args:
        path: File path to validate
        check_exists: Whether to verify the file exists
        base_dir: Base directory for relative paths

    Returns:
        Tuple of (is_valid, error_message)
    """
    import os
    import re

    # Basic format validation
    if not path or not path.strip():
        return False, "Empty file path"

    path = path.strip()

    # Check for obvious URL (shouldn't be a file path)
    if path.lower().startswith(('http://', 'https://', 'ftp://', 'mailto:')):
        return False, "This is a URL, not a file path"

    # Check for invalid characters (Windows)
    invalid_chars = '<>"|?*'
    for char in invalid_chars:
        if char in path:
            return False, f"Invalid character in path: {char}"

    # Check for double slashes (except at start for UNC)
    if '//' in path and not path.startswith('//'):
        return False, "Double forward slashes in path"

    if '\\\\' in path and not path.startswith('\\\\'):
        return False, "Double backslashes in path (not a UNC path)"

    # Optional: Check if file exists
    if check_exists:
        check_path = path
        if base_dir and not os.path.isabs(path):
            check_path = os.path.join(base_dir, path)

        try:
            if os.path.exists(check_path):
                return True, ""
            else:
                # Distinguish: does the parent directory exist?
                parent = os.path.dirname(check_path)
                if parent and os.path.isabs(check_path) and not os.path.exists(parent):
                    return False, f"Parent directory not found: {parent}"
                return False, f"File not found: {path}"
        except PermissionError:
            return False, f"Permission denied accessing: {path} (check user/network credentials)"
        except OSError as e:
            return False, f"Cannot access file path: {path} ({e})"

    return True, ""


# =============================================================================
# NETWORK PATH (UNC) VALIDATION
# =============================================================================

def validate_network_path(path: str, check_accessible: bool = False) -> tuple[bool, str]:
    """
    Validate a UNC network path.

    Args:
        path: Network path to validate (e.g., \\\\server\\share)
        check_accessible: Whether to verify the path is accessible

    Returns:
        Tuple of (is_valid, error_message)
    """
    import os
    import re

    if not path:
        return False, "Empty network path"

    path = path.strip()

    # Must start with \\\\ or //
    if not (path.startswith('\\\\') or path.startswith('//')):
        return False, "Network path must start with \\\\ or //"

    # Normalize to backslashes for consistency
    normalized = path.replace('/', '\\')

    # UNC format: \\server\share[\path]
    # At minimum need \\server\share
    unc_pattern = r'^\\\\[^\\]+\\[^\\]+'
    if not re.match(unc_pattern, normalized):
        return False, "Invalid UNC format. Expected: \\\\server\\share"

    # Extract server name
    parts = normalized.lstrip('\\').split('\\')
    if len(parts) < 2:
        return False, "Missing share name"

    server = parts[0]
    share = parts[1]

    # Validate server name
    if not server or server.startswith('-') or server.endswith('-'):
        return False, "Invalid server name"

    # Server name shouldn't be too long
    if len(server) > 255:
        return False, "Server name too long"

    # Share name validation
    if not share:
        return False, "Missing share name"

    # Check for invalid share name characters
    invalid_share_chars = '<>:"|?*'
    for char in invalid_share_chars:
        if char in share:
            return False, f"Invalid character in share name: {char}"

    # Optional: Check if path is accessible using current user credentials
    if check_accessible:
        try:
            if os.path.exists(path):
                return True, ""
            else:
                # Try to distinguish server unreachable vs share inaccessible
                server_path = '\\\\' + server
                try:
                    server_reachable = os.path.exists(server_path)
                except Exception:
                    server_reachable = False

                if not server_reachable:
                    return False, f"Server unreachable: {server} (check network/VPN connection)"
                else:
                    return False, f"Network path not accessible: {path} (server '{server}' is reachable but share/path cannot be accessed — check permissions)"
        except PermissionError:
            return False, f"Permission denied: {path} (current user credentials lack access to this network share)"
        except OSError as e:
            error_msg = str(e)
            if 'network name' in error_msg.lower() or 'network path' in error_msg.lower():
                return False, f"Network error accessing {path}: {error_msg} (check network connectivity)"
            elif 'logon' in error_msg.lower() or 'credential' in error_msg.lower():
                return False, f"Authentication failed for {path}: {error_msg} (check Windows credentials)"
            else:
                return False, f"Cannot access network path {path}: {error_msg}"
        except Exception as e:
            return False, f"Cannot access network path: {str(e)}"

    return True, ""


# =============================================================================
# URL TYPO DETECTION
# =============================================================================

def detect_url_typos(url: str) -> tuple[bool, List[str]]:
    """
    Detect common typos and issues in URLs.

    Args:
        url: URL to check

    Returns:
        Tuple of (has_typos, list_of_issues)
    """
    import re
    from urllib.parse import urlparse

    issues = []

    # Double dots in domain (except for subdomains like co.uk)
    if '..' in url:
        issues.append("Contains double dots (..) - possible typo")

    # Spaces in URL
    if ' ' in url:
        issues.append("Contains spaces - URLs should not have spaces")

    # Missing colon after http/https
    if re.match(r'^https?[^:]', url.lower()):
        issues.append("Missing colon after http/https")

    # Triple slashes (http:/// instead of http://)
    if ':///' in url:
        issues.append("Triple slashes - should be ://")

    # Common protocol typos
    protocol_typos = {
        'htpp://': 'http://',
        'htps://': 'https://',
        'htp://': 'http://',
        'hhtp://': 'http://',
        'hhtps://': 'https://',
        'httpss://': 'https://',
    }
    for typo, correct in protocol_typos.items():
        if url.lower().startswith(typo):
            issues.append(f"Protocol typo: '{typo}' should be '{correct}'")

    # Try to parse and check domain
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Check for suspicious TLD typos
        tld_typos = detect_tld_typos(domain)
        if tld_typos:
            issues.extend(tld_typos)

        # Check for common domain typos
        domain_typo = detect_domain_typos(domain)
        if domain_typo:
            issues.append(domain_typo)

    except Exception:
        pass

    return len(issues) > 0, issues


def detect_tld_typos(domain: str) -> List[str]:
    """
    Detect common TLD (top-level domain) typos.

    Args:
        domain: Domain to check

    Returns:
        List of TLD typo warnings
    """
    issues = []

    # Common TLD typos
    tld_typos = {
        '.con': '.com',
        '.cmo': '.com',
        '.ocm': '.com',
        '.com,': '.com',
        '.ent': '.net',
        '.nte': '.net',
        '.nett': '.net',
        '.ogr': '.org',
        '.orgg': '.org',
        '.eduu': '.edu',
        '.goc': '.gov',
        '.goov': '.gov',
    }

    for typo, correct in tld_typos.items():
        if domain.endswith(typo):
            issues.append(f"Possible TLD typo: '{typo}' should be '{correct}'")

    return issues


def detect_domain_typos(domain: str) -> Optional[str]:
    """
    Detect common domain name typos.

    Args:
        domain: Domain to check

    Returns:
        Warning message if typo detected, None otherwise
    """
    # Common site typos
    domain_typos = {
        'gogle.com': 'google.com',
        'goggle.com': 'google.com',
        'googel.com': 'google.com',
        'gooogle.com': 'google.com',
        'microsft.com': 'microsoft.com',
        'mircosoft.com': 'microsoft.com',
        'microsfot.com': 'microsoft.com',
        'amazn.com': 'amazon.com',
        'amzon.com': 'amazon.com',
        'amazonn.com': 'amazon.com',
        'facebok.com': 'facebook.com',
        'facbook.com': 'facebook.com',
        'twtter.com': 'twitter.com',
        'twiiter.com': 'twitter.com',
        'linkdin.com': 'linkedin.com',
        'linkedinn.com': 'linkedin.com',
        'youtub.com': 'youtube.com',
        'youutube.com': 'youtube.com',
        'gitub.com': 'github.com',
        'guthub.com': 'github.com',
        'githb.com': 'github.com',
    }

    # Extract just the domain without subdomains
    parts = domain.split('.')
    if len(parts) >= 2:
        main_domain = '.'.join(parts[-2:])
        if main_domain in domain_typos:
            return f"Possible domain typo: '{main_domain}' should be '{domain_typos[main_domain]}'"

    return None


# =============================================================================
# CROSS-REFERENCE VALIDATION
# =============================================================================

def parse_cross_reference(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a cross-reference string.

    Args:
        text: Text like "Section 1.2.3" or "Table 5"

    Returns:
        Dict with ref_type, ref_number, or None if not a cross-reference
    """
    import re

    patterns = [
        (r'^Section\s+([\d.]+)', 'section'),
        (r'^Chapter\s+(\d+)', 'chapter'),
        (r'^Table\s+(\d+)', 'table'),
        (r'^Figure\s+(\d+)', 'figure'),
        (r'^Appendix\s+([A-Z])', 'appendix'),
        (r'^Paragraph\s+([\d.]+)', 'paragraph'),
    ]

    for pattern, ref_type in patterns:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match:
            return {
                'type': ref_type,
                'number': match.group(1),
                'original': text.strip()
            }

    return None


def validate_cross_reference(
    ref: str,
    document_structure: Optional[Dict] = None
) -> tuple[bool, str]:
    """
    Validate a cross-reference.

    Args:
        ref: Cross-reference text (e.g., "Section 1.2")
        document_structure: Optional dict with sections, tables, figures, etc.

    Returns:
        Tuple of (is_valid, error_message)
    """
    parsed = parse_cross_reference(ref)
    if not parsed:
        return False, "Not a valid cross-reference format"

    # If we don't have document structure, just validate format
    if not document_structure:
        return True, ""

    ref_type = parsed['type']
    ref_number = parsed['number']

    # Check if reference exists in document structure
    structure_key = f"{ref_type}s"  # sections, tables, figures, etc.
    if structure_key in document_structure:
        available = document_structure[structure_key]
        if ref_number in available or str(ref_number) in available:
            return True, ""
        else:
            return False, f"{ref_type.capitalize()} {ref_number} not found in document"

    # Can't validate without structure
    return True, ""


# =============================================================================
# INTERNAL BOOKMARK VALIDATION
# =============================================================================

def validate_internal_bookmark(
    bookmark: str,
    available_bookmarks: Optional[List[str]] = None
) -> tuple[bool, str]:
    """
    Validate an internal bookmark reference.

    Args:
        bookmark: Bookmark reference (e.g., "#section-intro")
        available_bookmarks: List of valid bookmarks in the document

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not bookmark:
        return False, "Empty bookmark"

    # Must start with #
    if not bookmark.startswith('#'):
        return False, "Bookmark must start with #"

    bookmark_name = bookmark[1:]  # Remove #

    if not bookmark_name:
        return False, "Empty bookmark name"

    # Check for invalid characters
    import re
    if not re.match(r'^[A-Za-z][A-Za-z0-9_-]*$', bookmark_name):
        # This is a warning, not necessarily an error
        pass

    # If we have available bookmarks, check if this one exists
    if available_bookmarks is not None:
        # Case-insensitive comparison
        available_lower = [b.lower() for b in available_bookmarks]
        if bookmark_name.lower() not in available_lower:
            return False, f"Bookmark '{bookmark_name}' not found in document"

    return True, ""
