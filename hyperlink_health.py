#!/usr/bin/env python3
"""
Hyperlink Health Module v1.0.0
===============================
Thread 5: Hyperlink Health Modes for AEGIS v3.0.31

Features:
- LinkStatus model for tracking validation states
- Offline/Validator modes for different network environments
- Export report functionality for hyperlink health
- Integration with existing hyperlink checkers

Modes:
- OFFLINE: Format validation only, no network requests (default for air-gapped)
- VALIDATOR: Full validation with network access (when available)

Author: AEGIS
Version: reads from version.json (module v1.0)
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

__version__ = "1.0.0"


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class HealthMode(Enum):
    """Validation mode for hyperlink checking."""
    OFFLINE = "offline"           # Format validation only - for air-gapped networks
    VALIDATOR = "validator"       # Full validation with network access (Python requests)
    PS1_VALIDATOR = "ps1_validator"  # v3.0.33: Use PowerShell HyperlinkValidator script


class LinkStatus(Enum):
    """Status of a hyperlink after validation."""
    VALID = "valid"                  # Link passed all checks
    INVALID = "invalid"              # Link failed validation
    WARNING = "warning"              # Link has potential issues
    UNCHECKED = "unchecked"          # Link not yet validated
    SKIPPED = "skipped"              # Link skipped (e.g., offline mode)
    TIMEOUT = "timeout"              # Network timeout
    DNS_FAILED = "dns_failed"        # DNS resolution failed
    SSL_ERROR = "ssl_error"          # SSL certificate issue
    NOT_FOUND = "not_found"          # 404 or file not found
    REDIRECT = "redirect"            # Redirect detected (info)
    SOFT_404 = "soft_404"            # Page exists but returns soft 404
    # v3.0.33: Added for PS1 validator integration (Chunk B)
    WORKING = "working"              # PS1 validator confirmed working
    BROKEN = "broken"                # PS1 validator confirmed broken
    BLOCKED = "blocked"              # PS1 validator reported blocked/filtered
    UNKNOWN = "unknown"              # Status cannot be determined (offline web URLs)
    VALID_FORMAT = "valid_format"    # Format validated only (offline mode)


class LinkType(Enum):
    """Classification of hyperlink types."""
    INTERNAL_BOOKMARK = "internal_bookmark"
    CROSS_REFERENCE = "cross_reference"
    FILE_PATH = "file_path"
    NETWORK_PATH = "network_path"
    MAILTO = "mailto"
    WEB_URL = "web_url"
    EMPTY = "empty"
    UNKNOWN = "unknown"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class LinkStatusRecord:
    """
    Complete status record for a single hyperlink.
    
    This is the core data model for Thread 5, tracking all validation
    information for each link in a document.
    """
    # Identification
    id: str = ""                          # Unique ID for this link
    target: str = ""                      # Link target URL/path
    display_text: str = ""                # Visible link text
    link_type: str = "unknown"            # Type classification
    
    # Location
    paragraph_index: int = 0              # Paragraph containing link
    context: str = ""                     # Surrounding text
    document_path: str = ""               # Source document
    
    # Status
    status: str = "unchecked"             # Current validation status
    status_code: Optional[int] = None     # HTTP status if applicable
    status_message: str = ""              # Human-readable status
    
    # Validation details
    validation_mode: str = "offline"      # Mode used for validation
    validated_at: Optional[str] = None    # ISO timestamp
    validation_time_ms: float = 0.0       # Time taken to validate
    
    # URL-specific fields
    final_url: Optional[str] = None       # After redirects
    redirect_count: int = 0               # Number of redirects
    dns_resolved: bool = False            # DNS lookup success
    ssl_valid: bool = False               # SSL certificate valid
    ssl_expires: Optional[str] = None     # SSL expiry date
    ssl_warning: Optional[str] = None     # SSL warnings
    
    # File-specific fields
    file_exists: bool = False             # File found on disk
    file_path_resolved: str = ""          # Absolute resolved path
    
    # Issue tracking
    issues: List[Dict] = field(default_factory=list)  # Detailed issues
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LinkStatusRecord':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HyperlinkHealthReport:
    """
    Complete hyperlink health report for a document.
    
    Aggregates all link statuses and provides summary statistics.
    """
    # Document info
    document_path: str = ""
    document_name: str = ""
    generated_at: str = ""
    generator_version: str = __version__
    
    # Mode
    validation_mode: str = "offline"
    
    # Links
    links: List[LinkStatusRecord] = field(default_factory=list)
    
    # Summary counts
    total_links: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    warning_count: int = 0
    unchecked_count: int = 0
    skipped_count: int = 0
    
    # Type breakdown
    type_counts: Dict[str, int] = field(default_factory=dict)
    
    # Status breakdown
    status_counts: Dict[str, int] = field(default_factory=dict)
    
    # Issues summary
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    top_issues: List[Dict] = field(default_factory=list)
    
    def calculate_summary(self):
        """Calculate summary statistics from links."""
        self.total_links = len(self.links)
        
        # Status counts
        self.status_counts = {}
        self.valid_count = 0
        self.invalid_count = 0
        self.warning_count = 0
        self.unchecked_count = 0
        self.skipped_count = 0
        
        for link in self.links:
            status = link.status
            self.status_counts[status] = self.status_counts.get(status, 0) + 1
            
            if status == LinkStatus.VALID.value:
                self.valid_count += 1
            elif status in (LinkStatus.INVALID.value, LinkStatus.NOT_FOUND.value,
                          LinkStatus.DNS_FAILED.value, LinkStatus.SSL_ERROR.value):
                self.invalid_count += 1
            elif status == LinkStatus.WARNING.value:
                self.warning_count += 1
            elif status == LinkStatus.UNCHECKED.value:
                self.unchecked_count += 1
            elif status == LinkStatus.SKIPPED.value:
                self.skipped_count += 1
        
        # Type counts
        self.type_counts = {}
        for link in self.links:
            lt = link.link_type
            self.type_counts[lt] = self.type_counts.get(lt, 0) + 1
        
        # Issues summary
        self.issues_by_severity = {'high': 0, 'medium': 0, 'low': 0}
        issue_counts = {}
        
        for link in self.links:
            for issue in link.issues:
                sev = issue.get('severity', 'medium').lower()
                self.issues_by_severity[sev] = self.issues_by_severity.get(sev, 0) + 1
                
                msg = issue.get('message', 'Unknown issue')
                issue_counts[msg] = issue_counts.get(msg, 0) + 1
        
        # Top issues
        self.top_issues = [
            {'message': msg, 'count': count}
            for msg, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:10]
        ]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_path': self.document_path,
            'document_name': self.document_name,
            'generated_at': self.generated_at,
            'generator_version': self.generator_version,
            'validation_mode': self.validation_mode,
            'summary': {
                'total_links': self.total_links,
                'valid': self.valid_count,
                'invalid': self.invalid_count,
                'warning': self.warning_count,
                'unchecked': self.unchecked_count,
                'skipped': self.skipped_count,
            },
            'type_counts': self.type_counts,
            'status_counts': self.status_counts,
            'issues_by_severity': self.issues_by_severity,
            'top_issues': self.top_issues,
            'links': [link.to_dict() for link in self.links],
        }


# =============================================================================
# HYPERLINK HEALTH VALIDATOR
# =============================================================================

class HyperlinkHealthValidator:
    """
    Main validator class for hyperlink health checking.
    
    Supports two modes:
    - OFFLINE: Format validation only (default for air-gapped networks)
    - VALIDATOR: Full validation with network access
    """
    
    # URL patterns
    URL_PATTERN = re.compile(
        r'^https?://[^\s<>"{}|\\^`\[\]]+$',
        re.IGNORECASE
    )
    
    MAILTO_PATTERN = re.compile(
        r'^mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
        re.IGNORECASE
    )
    
    FILE_PATH_PATTERN = re.compile(
        r'^(?:[a-zA-Z]:|\.\.?)?[\\/]',
    )
    
    NETWORK_PATH_PATTERN = re.compile(
        r'^\\\\[^\\/]+\\',
    )
    
    BOOKMARK_PATTERN = re.compile(
        r'^#[\w-]+$',
    )
    
    def __init__(
        self,
        mode: HealthMode = HealthMode.OFFLINE,
        base_path: Optional[str] = None,
        timeout: int = 10,
        follow_redirects: bool = True,
        max_redirects: int = 10,
        check_ssl: bool = True,
        ssl_warning_days: int = 30,
    ):
        """
        Initialize the hyperlink health validator.
        
        Args:
            mode: Validation mode (OFFLINE or VALIDATOR)
            base_path: Base path for resolving relative file paths
            timeout: Network timeout in seconds
            follow_redirects: Whether to follow redirects
            max_redirects: Maximum number of redirects to follow
            check_ssl: Whether to validate SSL certificates
            ssl_warning_days: Days before SSL expiry to warn
        """
        self.mode = mode
        self.base_path = base_path
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.check_ssl = check_ssl
        self.ssl_warning_days = ssl_warning_days
        
        # Results storage
        self._links: List[LinkStatusRecord] = []
        self._link_counter = 0
        
        # Check if requests library is available for VALIDATOR mode
        self._requests_available = False
        if mode == HealthMode.VALIDATOR:
            try:
                import requests
                self._requests_available = True
            except ImportError:
                pass
    
    def classify_link(self, target: str) -> LinkType:
        """Classify a link by its type."""
        if not target or not target.strip():
            return LinkType.EMPTY
        
        target = target.strip()
        
        if self.BOOKMARK_PATTERN.match(target):
            return LinkType.INTERNAL_BOOKMARK
        
        if self.NETWORK_PATH_PATTERN.match(target):
            return LinkType.NETWORK_PATH
        
        if self.FILE_PATH_PATTERN.match(target):
            return LinkType.FILE_PATH
        
        if target.lower().startswith('mailto:'):
            return LinkType.MAILTO
        
        if self.URL_PATTERN.match(target):
            return LinkType.WEB_URL
        
        if target.startswith('http'):
            return LinkType.WEB_URL
        
        return LinkType.UNKNOWN
    
    def validate_link(
        self,
        target: str,
        display_text: str = "",
        paragraph_index: int = 0,
        context: str = "",
        document_path: str = "",
    ) -> LinkStatusRecord:
        """
        Validate a single hyperlink.
        
        Args:
            target: Link target URL/path
            display_text: Visible link text
            paragraph_index: Paragraph containing link
            context: Surrounding text
            document_path: Source document path
            
        Returns:
            LinkStatusRecord with validation results
        """
        self._link_counter += 1
        start_time = time.time()
        
        # Create record
        record = LinkStatusRecord(
            id=f"link_{self._link_counter}",
            target=target,
            display_text=display_text,
            paragraph_index=paragraph_index,
            context=context,
            document_path=document_path,
            validation_mode=self.mode.value,
            validated_at=datetime.now().isoformat(),
        )
        
        # Classify link type
        link_type = self.classify_link(target)
        record.link_type = link_type.value
        
        # Validate based on type
        if link_type == LinkType.EMPTY:
            record.status = LinkStatus.INVALID.value
            record.status_message = "Empty or missing link target"
            record.issues.append({
                'severity': 'high',
                'message': 'Empty link target',
                'rule_id': 'HH001'
            })
        
        elif link_type == LinkType.INTERNAL_BOOKMARK:
            self._validate_bookmark(record)
        
        elif link_type == LinkType.FILE_PATH:
            self._validate_file_path(record)
        
        elif link_type == LinkType.NETWORK_PATH:
            self._validate_network_path(record)
        
        elif link_type == LinkType.MAILTO:
            self._validate_mailto(record)
        
        elif link_type == LinkType.WEB_URL:
            self._validate_web_url(record)
        
        else:
            record.status = LinkStatus.WARNING.value
            record.status_message = "Unknown link type"
            record.issues.append({
                'severity': 'low',
                'message': f'Unrecognized link format: {target[:50]}',
                'rule_id': 'HH002'
            })
        
        record.validation_time_ms = round((time.time() - start_time) * 1000, 2)
        self._links.append(record)
        
        return record
    
    def _validate_bookmark(self, record: LinkStatusRecord):
        """Validate internal bookmark link."""
        # Bookmarks are format-validated only - actual existence
        # requires document structure which is checked elsewhere
        record.status = LinkStatus.VALID.value
        record.status_message = "Internal bookmark (format valid)"
    
    def _validate_file_path(self, record: LinkStatusRecord):
        """Validate file path link."""
        target = record.target
        
        try:
            # Resolve relative paths
            if self.base_path and not os.path.isabs(target):
                resolved = os.path.normpath(os.path.join(self.base_path, target))
            else:
                resolved = os.path.normpath(target)
            
            record.file_path_resolved = resolved
            
            # Check existence in OFFLINE mode
            if os.path.exists(resolved):
                record.file_exists = True
                record.status = LinkStatus.VALID.value
                record.status_message = "File exists"
            else:
                record.file_exists = False
                record.status = LinkStatus.NOT_FOUND.value
                record.status_message = f"File not found: {os.path.basename(resolved)}"
                record.issues.append({
                    'severity': 'high',
                    'message': f'Linked file not found: {resolved}',
                    'rule_id': 'HH010'
                })
        
        except (OSError, ValueError) as e:
            record.status = LinkStatus.INVALID.value
            record.status_message = f"Invalid file path: {e}"
            record.issues.append({
                'severity': 'high',
                'message': f'Invalid file path format: {str(e)[:50]}',
                'rule_id': 'HH011'
            })
    
    def _validate_network_path(self, record: LinkStatusRecord):
        """Validate network UNC path."""
        target = record.target
        
        # Format validation
        if not self.NETWORK_PATH_PATTERN.match(target):
            record.status = LinkStatus.INVALID.value
            record.status_message = "Invalid UNC path format"
            record.issues.append({
                'severity': 'high',
                'message': 'Invalid network path format',
                'rule_id': 'HH020'
            })
            return
        
        # In OFFLINE mode, skip actual network check
        if self.mode == HealthMode.OFFLINE:
            record.status = LinkStatus.SKIPPED.value
            record.status_message = "Network path (offline mode - not validated)"
            return
        
        # In VALIDATOR mode, try to check if accessible
        try:
            if os.path.exists(target):
                record.file_exists = True
                record.status = LinkStatus.VALID.value
                record.status_message = "Network path accessible"
            else:
                record.file_exists = False
                record.status = LinkStatus.NOT_FOUND.value
                record.status_message = "Network path not accessible"
                record.issues.append({
                    'severity': 'high',
                    'message': f'Network path not accessible: {target[:50]}',
                    'rule_id': 'HH021'
                })
        except (OSError, PermissionError) as e:
            record.status = LinkStatus.WARNING.value
            record.status_message = f"Cannot verify network path: {e}"
            record.issues.append({
                'severity': 'medium',
                'message': f'Network path verification failed: {str(e)[:50]}',
                'rule_id': 'HH022'
            })
    
    def _validate_mailto(self, record: LinkStatusRecord):
        """Validate mailto link."""
        target = record.target
        
        match = self.MAILTO_PATTERN.match(target)
        if match:
            email = match.group(1)
            
            # Basic format validation
            if '@' in email and '.' in email.split('@')[1]:
                record.status = LinkStatus.VALID.value
                record.status_message = f"Valid mailto format: {email}"
            else:
                record.status = LinkStatus.INVALID.value
                record.status_message = "Invalid email format"
                record.issues.append({
                    'severity': 'high',
                    'message': f'Invalid email address format: {email}',
                    'rule_id': 'HH030'
                })
        else:
            record.status = LinkStatus.INVALID.value
            record.status_message = "Invalid mailto link format"
            record.issues.append({
                'severity': 'high',
                'message': 'Malformed mailto link',
                'rule_id': 'HH031'
            })
    
    def _validate_web_url(self, record: LinkStatusRecord):
        """Validate web URL."""
        target = record.target
        
        # Basic format validation
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(target)
            
            # Check required components
            if not parsed.scheme:
                record.status = LinkStatus.INVALID.value
                record.status_message = "URL missing scheme (http/https)"
                record.issues.append({
                    'severity': 'medium',
                    'message': 'URL missing http:// or https:// prefix',
                    'rule_id': 'HH040'
                })
                return
            
            if parsed.scheme.lower() not in ('http', 'https'):
                record.status = LinkStatus.WARNING.value
                record.status_message = f"Non-standard URL scheme: {parsed.scheme}"
                record.issues.append({
                    'severity': 'low',
                    'message': f'Non-standard URL scheme: {parsed.scheme}',
                    'rule_id': 'HH041'
                })
            
            if not parsed.netloc:
                record.status = LinkStatus.INVALID.value
                record.status_message = "URL missing domain"
                record.issues.append({
                    'severity': 'high',
                    'message': 'URL missing domain name',
                    'rule_id': 'HH042'
                })
                return
            
            # Check for common issues
            if ' ' in target:
                record.status = LinkStatus.INVALID.value
                record.status_message = "URL contains spaces"
                record.issues.append({
                    'severity': 'high',
                    'message': 'URL contains unencoded spaces',
                    'rule_id': 'HH043'
                })
                return
            
            # In OFFLINE mode, stop at format validation
            # v3.0.33 Chunk B: Return VALID_FORMAT or UNKNOWN instead of VALID
            # to make it clear we haven't actually validated the URL
            if self.mode == HealthMode.OFFLINE:
                record.status = LinkStatus.VALID_FORMAT.value
                record.status_message = "URL format valid (network status unknown - offline mode)"
                return
            
            # In VALIDATOR mode, perform network validation
            self._validate_url_network(record)
        
        except Exception as e:
            record.status = LinkStatus.INVALID.value
            record.status_message = f"Cannot parse URL: {e}"
            record.issues.append({
                'severity': 'high',
                'message': f'URL parsing failed: {str(e)[:50]}',
                'rule_id': 'HH044'
            })
    
    def _validate_url_network(self, record: LinkStatusRecord):
        """Validate URL with network access (VALIDATOR mode only)."""
        if not self._requests_available:
            record.status = LinkStatus.SKIPPED.value
            record.status_message = "Network validation unavailable (requests not installed)"
            return
        
        import requests
        from urllib.parse import urlparse
        
        target = record.target
        parsed = urlparse(target)
        
        try:
            # DNS resolution check
            import socket
            try:
                socket.setdefaulttimeout(self.timeout)
                ips = socket.gethostbyname_ex(parsed.netloc)[2]
                record.dns_resolved = True
            except socket.gaierror as e:
                record.dns_resolved = False
                record.status = LinkStatus.DNS_FAILED.value
                record.status_message = f"DNS resolution failed: {parsed.netloc}"
                record.issues.append({
                    'severity': 'high',
                    'message': f'DNS lookup failed for {parsed.netloc}',
                    'rule_id': 'HH050'
                })
                return
            
            # SSL check for HTTPS
            if parsed.scheme.lower() == 'https' and self.check_ssl:
                self._check_ssl(record, parsed.netloc)
            
            # HTTP request
            response = requests.head(
                target,
                allow_redirects=self.follow_redirects,
                timeout=self.timeout,
                headers={'User-Agent': 'AEGIS/3.0.31 HyperlinkHealth'}
            )
            
            record.status_code = response.status_code
            
            # Track redirects
            if response.history:
                record.redirect_count = len(response.history)
                record.final_url = response.url
            
            # Evaluate status
            if response.status_code == 200:
                record.status = LinkStatus.VALID.value
                record.status_message = "URL accessible"
            elif response.status_code == 404:
                record.status = LinkStatus.NOT_FOUND.value
                record.status_message = "Page not found (404)"
                record.issues.append({
                    'severity': 'high',
                    'message': f'Page not found: HTTP 404',
                    'rule_id': 'HH051'
                })
            elif 300 <= response.status_code < 400:
                record.status = LinkStatus.REDIRECT.value
                record.status_message = f"Redirect: {response.status_code}"
            elif response.status_code >= 500:
                record.status = LinkStatus.WARNING.value
                record.status_message = f"Server error: {response.status_code}"
                record.issues.append({
                    'severity': 'medium',
                    'message': f'Server returned error: HTTP {response.status_code}',
                    'rule_id': 'HH052'
                })
            else:
                record.status = LinkStatus.WARNING.value
                record.status_message = f"HTTP {response.status_code}"
        
        except requests.Timeout:
            record.status = LinkStatus.TIMEOUT.value
            record.status_message = f"Connection timeout ({self.timeout}s)"
            record.issues.append({
                'severity': 'medium',
                'message': 'Connection timed out',
                'rule_id': 'HH053'
            })
        
        except requests.RequestException as e:
            record.status = LinkStatus.INVALID.value
            record.status_message = f"Request failed: {e}"
            record.issues.append({
                'severity': 'high',
                'message': f'HTTP request failed: {str(e)[:50]}',
                'rule_id': 'HH054'
            })
    
    def _check_ssl(self, record: LinkStatusRecord, hostname: str):
        """Check SSL certificate validity."""
        import ssl
        import socket
        from datetime import datetime
        
        context = ssl.create_default_context()
        
        try:
            with socket.create_connection((hostname, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    expires_str = cert.get('notAfter', '')
                    
                    try:
                        expires = datetime.strptime(expires_str, '%b %d %H:%M:%S %Y %Z')
                        days_until = (expires - datetime.now()).days
                        
                        record.ssl_valid = True
                        record.ssl_expires = expires.strftime('%Y-%m-%d')
                        
                        if days_until < 0:
                            record.ssl_warning = "Certificate has expired!"
                            record.issues.append({
                                'severity': 'high',
                                'message': 'SSL certificate expired',
                                'rule_id': 'HH060'
                            })
                        elif days_until < self.ssl_warning_days:
                            record.ssl_warning = f"Certificate expires in {days_until} days"
                            record.issues.append({
                                'severity': 'medium',
                                'message': f'SSL certificate expires in {days_until} days',
                                'rule_id': 'HH061'
                            })
                    except ValueError:
                        record.ssl_valid = True
        
        except ssl.SSLError as e:
            record.ssl_valid = False
            record.status = LinkStatus.SSL_ERROR.value
            record.status_message = f"SSL error: {e}"
            record.issues.append({
                'severity': 'high',
                'message': f'SSL certificate error: {str(e)[:50]}',
                'rule_id': 'HH062'
            })
        
        except Exception:
            # Non-fatal - SSL check failed but link might still work
            pass
    
    # =========================================================================
    # v3.0.33 Chunk B: PS1 VALIDATOR ADAPTER
    # =========================================================================
    
    def _validate_with_ps1(self, links: List[LinkStatusRecord]) -> List[LinkStatusRecord]:
        """
        Validate web URLs using external PowerShell HyperlinkValidator script.
        
        This method calls an external PS1 script and parses its JSON output
        to update link statuses with evidence-based validation results.
        
        Args:
            links: List of LinkStatusRecord objects with web URLs
            
        Returns:
            Updated list of LinkStatusRecord objects
        """
        # Filter to web URLs only
        web_links = [l for l in links if l.link_type == LinkType.WEB_URL.value]
        if not web_links:
            return links
        
        # Find the PS1 script
        ps1_path = self._find_ps1_validator()
        if not ps1_path:
            # Mark web URLs as UNKNOWN if validator not available
            for link in web_links:
                link.status = LinkStatus.UNKNOWN.value
                link.status_message = "PS1 validator not found - status unknown"
            return links
        
        try:
            # Prepare URLs for the validator
            urls = [l.target for l in web_links]
            
            # Run PS1 validator
            results = self._run_ps1_validator(ps1_path, urls)
            
            # Map results back to links
            url_to_result = {r.get('url', ''): r for r in results}
            
            for link in web_links:
                if link.target in url_to_result:
                    result = url_to_result[link.target]
                    self._apply_ps1_result(link, result)
                else:
                    link.status = LinkStatus.UNKNOWN.value
                    link.status_message = "URL not in validator results"
        
        except Exception as e:
            # On error, mark as UNKNOWN (don't mark BROKEN without evidence)
            for link in web_links:
                link.status = LinkStatus.UNKNOWN.value
                link.status_message = f"PS1 validation error: {str(e)[:50]}"
        
        return links
    
    def _find_ps1_validator(self) -> Optional[str]:
        """
        Find the HyperlinkValidator.ps1 script.
        
        Searches in common locations:
        1. tools/ folder relative to this module
        2. Same directory as this module
        3. Path specified in config
        
        Returns:
            Path to PS1 script or None if not found
        """
        search_paths = [
            os.path.join(os.path.dirname(__file__), 'tools', 'HyperlinkValidator.ps1'),
            os.path.join(os.path.dirname(__file__), 'HyperlinkValidator.ps1'),
        ]
        
        # Check config for custom path
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    custom_path = config.get('hyperlink_validator_path')
                    if custom_path:
                        search_paths.insert(0, custom_path)
        except Exception:
            pass
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _run_ps1_validator(self, ps1_path: str, urls: List[str]) -> List[Dict]:
        """
        Execute the PowerShell validator script and return results.
        
        Args:
            ps1_path: Path to the HyperlinkValidator.ps1 script
            urls: List of URLs to validate
            
        Returns:
            List of validation result dictionaries
        """
        import subprocess
        import tempfile
        
        # Create temp file with URLs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for url in urls:
                f.write(url + '\n')
            url_file = f.name
        
        try:
            # Build PowerShell command
            # The script should output JSON results
            cmd = [
                'powershell.exe', '-NoProfile', '-NonInteractive',
                '-ExecutionPolicy', 'Bypass',
                '-File', ps1_path,
                '-InputFile', url_file,
                '-OutputFormat', 'JSON'
            ]
            
            # Run with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * len(urls) + 30,  # Allow time per URL + overhead
                cwd=os.path.dirname(ps1_path)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON output
                return json.loads(result.stdout)
            else:
                # Script failed or no output
                return []
        
        except subprocess.TimeoutExpired:
            return []
        except json.JSONDecodeError:
            return []
        except FileNotFoundError:
            # PowerShell not available (Linux/Mac without PS)
            return []
        finally:
            # Cleanup temp file
            try:
                os.unlink(url_file)
            except OSError:
                pass
    
    def _apply_ps1_result(self, link: LinkStatusRecord, result: Dict):
        """
        Apply PS1 validator result to a link record.
        
        Args:
            link: LinkStatusRecord to update
            result: Result dictionary from PS1 validator
        """
        status = result.get('status', '').lower()
        status_code = result.get('statusCode')
        message = result.get('message', '')
        redirect_url = result.get('redirectUrl')
        
        # Map PS1 statuses to our LinkStatus enum
        status_map = {
            'working': LinkStatus.WORKING,
            'ok': LinkStatus.WORKING,
            'success': LinkStatus.WORKING,
            'broken': LinkStatus.BROKEN,
            'error': LinkStatus.BROKEN,
            'notfound': LinkStatus.NOT_FOUND,
            '404': LinkStatus.NOT_FOUND,
            'redirect': LinkStatus.REDIRECT,
            'timeout': LinkStatus.TIMEOUT,
            'blocked': LinkStatus.BLOCKED,
            'filtered': LinkStatus.BLOCKED,
            'sslerror': LinkStatus.SSL_ERROR,
            'dnsfailed': LinkStatus.DNS_FAILED,
        }
        
        link_status = status_map.get(status, LinkStatus.UNKNOWN)
        link.status = link_status.value
        
        if status_code:
            link.status_code = status_code
        
        if redirect_url:
            link.final_url = redirect_url
            link.redirect_count = result.get('redirectCount', 1)
        
        # Build status message
        if message:
            link.status_message = message
        elif link_status == LinkStatus.WORKING:
            link.status_message = f"Validated by PS1 validator (HTTP {status_code or 'OK'})"
        elif link_status == LinkStatus.BROKEN:
            link.status_message = f"Broken: HTTP {status_code}" if status_code else "Broken link"
            link.issues.append({
                'severity': 'high',
                'message': f'Link broken (validated by PS1): {message or status_code}',
                'rule_id': 'HH070'
            })
        elif link_status == LinkStatus.BLOCKED:
            link.status_message = f"Blocked/Filtered: {message or 'Access denied'}"
            link.issues.append({
                'severity': 'medium',
                'message': f'Link blocked or filtered: {message}',
                'rule_id': 'HH071'
            })
        else:
            link.status_message = f"PS1 validator: {status}"
    
    def validate_batch(
        self,
        links: List[Dict],
        document_path: str = "",
    ) -> List[LinkStatusRecord]:
        """
        Validate a batch of hyperlinks.
        
        Args:
            links: List of link dictionaries with 'target', 'display_text', etc.
            document_path: Source document path
            
        Returns:
            List of LinkStatusRecord results
        """
        results = []
        
        for link in links:
            record = self.validate_link(
                target=link.get('target', ''),
                display_text=link.get('display_text', ''),
                paragraph_index=link.get('paragraph_index', 0),
                context=link.get('context', ''),
                document_path=document_path,
            )
            results.append(record)
        
        # v3.0.33 Chunk B: Use PS1 validator for web URLs when in PS1_VALIDATOR mode
        if self.mode == HealthMode.PS1_VALIDATOR:
            results = self._validate_with_ps1(results)
        
        return results
    
    def generate_report(
        self,
        document_path: str = "",
        document_name: str = "",
    ) -> HyperlinkHealthReport:
        """
        Generate a hyperlink health report.
        
        Args:
            document_path: Full path to source document
            document_name: Display name for document
            
        Returns:
            HyperlinkHealthReport with all validation results
        """
        report = HyperlinkHealthReport(
            document_path=document_path,
            document_name=document_name or os.path.basename(document_path),
            generated_at=datetime.now().isoformat(),
            validation_mode=self.mode.value,
            links=self._links.copy(),
        )
        
        report.calculate_summary()
        
        return report
    
    def reset(self):
        """Reset validator state for new document."""
        self._links = []
        self._link_counter = 0


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_report_json(report: HyperlinkHealthReport, filepath: str):
    """
    Export hyperlink health report to JSON.
    
    Args:
        report: HyperlinkHealthReport to export
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)


def export_report_html(report: HyperlinkHealthReport, filepath: str):
    """
    Export hyperlink health report to HTML.
    
    Args:
        report: HyperlinkHealthReport to export
        filepath: Output file path
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Hyperlink Health Report - {report.document_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .valid {{ color: #28a745; }}
        .invalid {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .skipped {{ color: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #1a1a2e; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.85em; }}
        .status-valid {{ background: #d4edda; color: #155724; }}
        .status-invalid {{ background: #f8d7da; color: #721c24; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-skipped {{ background: #e2e3e5; color: #383d41; }}
        .meta {{ color: #6c757d; font-size: 0.9em; }}
        .issues {{ margin-top: 30px; }}
        .issue {{ padding: 10px; margin: 5px 0; border-left: 4px solid; }}
        .issue-high {{ border-color: #dc3545; background: #fff5f5; }}
        .issue-medium {{ border-color: #ffc107; background: #fffef5; }}
        .issue-low {{ border-color: #17a2b8; background: #f5fdff; }}
    </style>
</head>
<body>
    <h1>Hyperlink Health Report</h1>
    
    <div class="meta">
        <p><strong>Document:</strong> {report.document_name}</p>
        <p><strong>Generated:</strong> {report.generated_at}</p>
        <p><strong>Mode:</strong> {report.validation_mode.upper()}</p>
        <p><strong>Generator:</strong> AEGIS Hyperlink Health v{report.generator_version}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="stat">
                <div class="stat-value">{report.total_links}</div>
                <div>Total Links</div>
            </div>
            <div class="stat">
                <div class="stat-value valid">{report.valid_count}</div>
                <div>Valid</div>
            </div>
            <div class="stat">
                <div class="stat-value invalid">{report.invalid_count}</div>
                <div>Invalid</div>
            </div>
            <div class="stat">
                <div class="stat-value warning">{report.warning_count}</div>
                <div>Warnings</div>
            </div>
            <div class="stat">
                <div class="stat-value skipped">{report.skipped_count}</div>
                <div>Skipped</div>
            </div>
        </div>
    </div>
    
    <h2>Link Types</h2>
    <table>
        <tr>
            <th>Type</th>
            <th>Count</th>
        </tr>
        {''.join(f'<tr><td>{t}</td><td>{c}</td></tr>' for t, c in report.type_counts.items())}
    </table>
    
    <h2>All Links</h2>
    <table>
        <tr>
            <th>Target</th>
            <th>Type</th>
            <th>Status</th>
            <th>Message</th>
        </tr>
        {''.join(_link_row_html(link) for link in report.links)}
    </table>
    
    <div class="issues">
        <h2>Issues ({sum(report.issues_by_severity.values())} total)</h2>
        <p>High: {report.issues_by_severity.get('high', 0)} | 
           Medium: {report.issues_by_severity.get('medium', 0)} | 
           Low: {report.issues_by_severity.get('low', 0)}</p>
        
        {''.join(_issue_html(issue) for link in report.links for issue in link.issues)}
    </div>
</body>
</html>
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def _link_row_html(link: LinkStatusRecord) -> str:
    """Generate HTML table row for a link."""
    status_class = {
        'valid': 'status-valid',
        'invalid': 'status-invalid',
        'not_found': 'status-invalid',
        'dns_failed': 'status-invalid',
        'ssl_error': 'status-invalid',
        'warning': 'status-warning',
        'skipped': 'status-skipped',
    }.get(link.status, 'status-warning')
    
    target_display = link.target[:60] + '...' if len(link.target) > 60 else link.target
    
    return f"""<tr>
        <td title="{link.target}">{target_display}</td>
        <td>{link.link_type}</td>
        <td><span class="status-badge {status_class}">{link.status}</span></td>
        <td>{link.status_message}</td>
    </tr>"""


def _issue_html(issue: Dict) -> str:
    """Generate HTML for an issue."""
    severity = issue.get('severity', 'medium').lower()
    return f"""<div class="issue issue-{severity}">
        <strong>[{issue.get('rule_id', 'HH000')}]</strong> {issue.get('message', '')}
    </div>"""


def export_report_csv(report: HyperlinkHealthReport, filepath: str):
    """
    Export hyperlink health report to CSV.
    
    Args:
        report: HyperlinkHealthReport to export
        filepath: Output file path
    """
    import csv
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'ID', 'Target', 'Display Text', 'Type', 'Status',
            'Status Code', 'Message', 'Paragraph', 'Issues Count'
        ])
        
        # Data rows
        for link in report.links:
            writer.writerow([
                link.id,
                link.target,
                link.display_text,
                link.link_type,
                link.status,
                link.status_code or '',
                link.status_message,
                link.paragraph_index,
                len(link.issues)
            ])


# =============================================================================
# INTEGRATION FUNCTIONS
# =============================================================================

def validate_document_links(
    filepath: str,
    mode: str = "offline",
    base_path: Optional[str] = None,
) -> Dict:
    """
    Validate all hyperlinks in a document.
    
    This is the main entry point for hyperlink health validation.
    
    Args:
        filepath: Path to document
        mode: "offline", "validator", or "ps1_validator"
        base_path: Base path for relative file resolution
        
    Returns:
        Dict with validation results and summary
    """
    # v3.0.33 Chunk B: Support ps1_validator mode
    mode_lower = mode.lower()
    if mode_lower == "offline":
        health_mode = HealthMode.OFFLINE
    elif mode_lower == "ps1_validator":
        health_mode = HealthMode.PS1_VALIDATOR
    else:
        health_mode = HealthMode.VALIDATOR
    
    validator = HyperlinkHealthValidator(
        mode=health_mode,
        base_path=base_path or os.path.dirname(filepath),
    )
    
    # Extract hyperlinks from document
    links = _extract_hyperlinks_from_docx(filepath)
    
    # Validate all links
    validator.validate_batch(links, document_path=filepath)
    
    # Generate report
    report = validator.generate_report(
        document_path=filepath,
        document_name=os.path.basename(filepath),
    )
    
    return report.to_dict()


def _extract_hyperlinks_from_docx(filepath: str) -> List[Dict]:
    """Extract hyperlinks from a DOCX file."""
    links = []
    
    try:
        import zipfile
        from xml.etree import ElementTree as ET
        
        NAMESPACES = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
        }
        
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Get relationships
            rels = {}
            if 'word/_rels/document.xml.rels' in zf.namelist():
                rels_xml = zf.read('word/_rels/document.xml.rels').decode('utf-8')
                rels_tree = ET.fromstring(rels_xml)
                for rel in rels_tree.iter('{%s}Relationship' % NAMESPACES['rel']):
                    rel_id = rel.get('Id')
                    target = rel.get('Target', '')
                    rel_type = rel.get('Type', '')
                    if 'hyperlink' in rel_type.lower():
                        rels[rel_id] = target
            
            # Parse document
            if 'word/document.xml' in zf.namelist():
                doc_xml = zf.read('word/document.xml').decode('utf-8')
                tree = ET.fromstring(doc_xml)
                
                para_idx = 0
                for para in tree.iter('{%s}p' % NAMESPACES['w']):
                    # Get paragraph text
                    para_texts = []
                    for t in para.iter('{%s}t' % NAMESPACES['w']):
                        if t.text:
                            para_texts.append(t.text)
                    para_text = ''.join(para_texts)
                    
                    # Find hyperlinks
                    for hyperlink in para.iter('{%s}hyperlink' % NAMESPACES['w']):
                        rel_id = hyperlink.get('{%s}id' % NAMESPACES['r'], '')
                        anchor = hyperlink.get('{%s}anchor' % NAMESPACES['w'], '')
                        
                        # Get display text
                        display_texts = []
                        for t in hyperlink.iter('{%s}t' % NAMESPACES['w']):
                            if t.text:
                                display_texts.append(t.text)
                        display_text = ''.join(display_texts)
                        
                        # Determine target
                        if rel_id and rel_id in rels:
                            target = rels[rel_id]
                        elif anchor:
                            target = f'#{anchor}'
                        else:
                            target = ''
                        
                        if target:
                            links.append({
                                'target': target,
                                'display_text': display_text,
                                'paragraph_index': para_idx,
                                'context': para_text[:100] if para_text else '',
                            })
                    
                    if para_texts:
                        para_idx += 1
    
    except Exception as e:
        # Return empty list on error
        pass
    
    return links


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print(f"Hyperlink Health Module v{__version__}")
    print("Use validate_document_links(filepath, mode) to validate a document")
    print("Modes: 'offline' (default) or 'validator'")
