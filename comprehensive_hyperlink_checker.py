#!/usr/bin/env python3
"""
Comprehensive Hyperlink Checker v4.0.0 (Production)
====================================================
Complete hyperlink and cross-reference validation for Word documents.

v4.0.0 - AEGIS v2.9.3 Features:
- F19: Advanced hyperlink validation (DNS, SSL, redirects, soft 404)
- F19a: Connected/Restricted mode toggle

VERIFICATION TYPES:
1. Internal document bookmarks (#bookmark)
2. File paths (relative/absolute) with existence check
3. Network UNC paths (\\\\server\\share) - format + accessibility test
4. Mailto links (RFC 5322 compliant validation)
5. URL syntax validation (comprehensive)
6. Cross-references (Section, Table, Figure, Appendix, Paragraph)
7. DOCX internal hyperlink extraction from relationships

VALIDATION MODES:
- RESTRICTED (default): Internal links only - for restricted networks
- CONNECTED: Full external validation when network permits

Author: AEGIS
Version: reads from version.json (module v4.0)
"""

import os
import re
import ssl
import socket
import time
import random
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, NamedTuple, Any
from xml.etree import ElementTree as ET
from urllib.parse import urlparse, unquote
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import string

# Optional imports for connected mode
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Windows SSO authentication support (v3.0.109)
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
try:
    # Try requests_negotiate_sspi first (Windows SSPI-based, most reliable)
    from requests_negotiate_sspi import HttpNegotiateAuth
    WINDOWS_AUTH_AVAILABLE = True
except ImportError:
    try:
        # Fallback to requests-ntlm
        from requests_ntlm import HttpNtlmAuth
        # Create a wrapper that works like HttpNegotiateAuth
        class HttpNegotiateAuth:
            """Wrapper for NTLM auth that uses current Windows user."""
            def __init__(self):
                import getpass
                import os
                # Get current Windows user credentials
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

# SharePoint-aware URL validation (v6.1.11)
SP_LINK_VALIDATOR_AVAILABLE = False
_validate_sp_url = None
_is_sp_url = None
try:
    from sharepoint_link_validator import validate_sharepoint_url as _validate_sp_url
    from sharepoint_link_validator import is_sharepoint_url as _is_sp_url
    SP_LINK_VALIDATOR_AVAILABLE = True
except ImportError:
    pass

try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Unknown"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._errors = []
        def create_issue(self, **kwargs):
            kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
            return kwargs
        def safe_check(self, *args, **kwargs):
            try:
                return self.check(*args, **kwargs)
            except Exception as e:
                self._errors.append(str(e))
                return []

__version__ = "4.0.0"

# XML namespaces for DOCX parsing
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
}


class ValidationMode(Enum):
    """Network validation mode."""
    RESTRICTED = "restricted"  # Internal links only - for restricted networks
    CONNECTED = "connected"    # Full validation - when external access available


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


@dataclass
class HyperlinkInfo:
    """Structured hyperlink information."""
    target: str
    display_text: str
    link_type: LinkType
    paragraph_index: int = 0
    context: str = ""
    anchor: str = ""
    rel_id: str = ""


@dataclass
class DocumentStructure:
    """Extracted document structure for cross-reference validation."""
    bookmarks: Set[str] = field(default_factory=set)
    sections: Set[str] = field(default_factory=set)
    tables: Set[str] = field(default_factory=set)
    figures: Set[str] = field(default_factory=set)
    appendices: Set[str] = field(default_factory=set)
    paragraphs: Set[str] = field(default_factory=set)
    headings: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of advanced URL validation."""
    url: str
    is_valid: bool
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    redirect_count: int = 0
    redirect_chain: List[Dict] = field(default_factory=list)
    dns_resolved: bool = False
    dns_ip_addresses: List[str] = field(default_factory=list)
    dns_response_time_ms: float = 0.0
    ssl_valid: bool = False
    ssl_issuer: str = ""
    ssl_expires: str = ""
    ssl_days_until_expiry: int = 0
    ssl_warning: Optional[str] = None
    is_soft_404: bool = False
    domain_category: str = "other"
    is_suspicious: bool = False
    suspicious_reasons: List[str] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 1
    validation_mode: str = "restricted"
    # v3.0.95: Additional fields for UI display
    link_text: str = ""
    link_type: Optional[Any] = None  # LinkType enum
    paragraph_index: int = 0
    error_message: Optional[str] = None
    response_time_ms: float = 0.0


# =============================================================================
# F19: ADVANCED VALIDATION FUNCTIONS
# =============================================================================

def check_dns_resolution(hostname: str, timeout: int = 5) -> Dict:
    """
    F19: Check if hostname resolves to an IP address.
    
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


def check_ssl_certificate(hostname: str, port: int = 443, timeout: int = 10) -> Dict:
    """
    F19: Check SSL certificate validity and expiration.
    
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


def follow_redirects(url: str, max_redirects: int = 10, timeout: int = 10, use_windows_auth: bool = True) -> Dict:
    """
    F19: Follow redirect chain and track all hops.
    v3.0.109: Added Windows SSO authentication support.

    Args:
        url: Starting URL
        max_redirects: Maximum number of redirects to follow
        timeout: Request timeout
        use_windows_auth: Use Windows SSO authentication (default True)

    Returns:
        dict with 'final_url', 'redirect_count', 'chain'
    """
    if not REQUESTS_AVAILABLE:
        return {
            'final_url': url,
            'redirect_count': 0,
            'chain': [],
            'error': 'requests library not available'
        }

    chain = []
    current_url = url
    session = requests.Session()

    # v3.0.109: Set up Windows authentication if available
    if use_windows_auth and WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
        try:
            session.auth = HttpNegotiateAuth()
        except Exception:
            pass  # Fall back to no auth

    for i in range(max_redirects):
        try:
            response = session.head(
                current_url,
                allow_redirects=False,
                timeout=timeout,
                headers={'User-Agent': 'AEGIS/4.0 HyperlinkChecker'}
            )
            chain.append({
                'url': current_url, 
                'status': response.status_code,
                'hop': i + 1
            })
            
            if response.status_code in (301, 302, 303, 307, 308):
                next_url = response.headers.get('Location')
                if next_url:
                    # Handle relative redirects
                    if next_url.startswith('/'):
                        parsed = urlparse(current_url)
                        next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
                    current_url = next_url
                else:
                    break
            else:
                break
        except requests.exceptions.Timeout:
            chain.append({'url': current_url, 'error': 'Timeout', 'hop': i + 1})
            break
        except requests.exceptions.ConnectionError as e:
            chain.append({'url': current_url, 'error': 'Connection failed', 'hop': i + 1})
            break
        except Exception as e:
            chain.append({'url': current_url, 'error': str(e), 'hop': i + 1})
            break
    
    return {
        'final_url': current_url,
        'redirect_count': len(chain) - 1 if chain else 0,
        'chain': chain
    }


def detect_soft_404(response_text: str) -> bool:
    """
    F19: Detect soft 404 pages that return 200 but are actually error pages.
    
    Args:
        response_text: HTML content of the page
        
    Returns:
        True if this appears to be a soft 404 page
    """
    text_lower = response_text.lower()
    
    # Title check
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', text_lower)
    if title_match:
        title = title_match.group(1)
        error_indicators = ['not found', '404', 'error', 'page missing', 'unavailable']
        if any(phrase in title for phrase in error_indicators):
            return True
    
    # Body phrases indicating error pages
    soft_404_phrases = [
        'page not found',
        'page you requested could not be found',
        "this page doesn't exist",
        'this page does not exist',
        "we couldn't find",
        'we could not find',
        'no longer available',
        'has been removed',
        'has been deleted',
        'page has moved',
        'content is unavailable',
        'content not available',
        'sorry, we can\'t find',
        'the requested url was not found',
        'oops! page not found',
        '404 error',
        'error 404'
    ]
    
    return any(phrase in text_lower for phrase in soft_404_phrases)


# Domain categorization
DOMAIN_CATEGORIES = {
    'government': ['.gov', '.mil'],
    'educational': ['.edu'],
    'commercial': ['.com', '.co', '.biz', '.io', '.tech', '.net'],
    'organization': ['.org'],
    'internal': ['sharepoint.com', 'sharepoint', 'intranet', 'internal', 'localhost'],
}


def categorize_domain(url: str) -> str:
    """
    F19: Categorize a URL's domain.
    
    Args:
        url: The URL to categorize
        
    Returns:
        Category string ('government', 'educational', 'commercial', 'internal', 'other')
    """
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 'other'
    
    for category, patterns in DOMAIN_CATEGORIES.items():
        if any(pattern in domain for pattern in patterns):
            return category
    return 'other'


def detect_suspicious_url(url: str) -> Dict:
    """
    F19: Detect potentially suspicious URLs.
    
    Args:
        url: The URL to analyze
        
    Returns:
        dict with 'suspicious' (bool) and 'reasons' (list)
    """
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


def request_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: int = 10,
    method: str = 'HEAD',
    use_windows_auth: bool = True
) -> Dict:
    """
    F19: Make HTTP request with exponential backoff retry.
    v3.0.109: Added Windows SSO authentication support.

    Args:
        url: URL to request
        max_retries: Maximum retry attempts
        timeout: Request timeout
        method: HTTP method ('HEAD' or 'GET')
        use_windows_auth: Use Windows SSO authentication (default True)

    Returns:
        dict with 'success', 'status_code', 'attempts', 'error', 'auth_used'
    """
    if not REQUESTS_AVAILABLE:
        return {
            'success': False,
            'error': 'requests library not available',
            'attempts': 0
        }

    headers = {'User-Agent': 'AEGIS/4.0 HyperlinkChecker'}

    # v3.0.109: Set up Windows authentication if available and requested
    auth = None
    auth_used = 'none'
    if use_windows_auth and WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
        try:
            auth = HttpNegotiateAuth()
            auth_used = 'windows_sso'
        except Exception as e:
            # Fall back to no auth if SSO setup fails
            auth_used = f'none (SSO failed: {str(e)[:30]})'

    for attempt in range(max_retries):
        try:
            if method.upper() == 'HEAD':
                response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers, auth=auth)
            else:
                response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers, auth=auth)
            
            return {
                'success': True,
                'status_code': response.status_code,
                'attempts': attempt + 1,
                'response': response,
                'auth_used': auth_used
            }
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (random.random() * 0.1)
                time.sleep(wait_time)
            else:
                return {
                    'success': False,
                    'error': 'Connection timeout after retries',
                    'attempts': attempt + 1,
                    'auth_used': auth_used
                }
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (random.random() * 0.1)
                time.sleep(wait_time)
            else:
                return {
                    'success': False,
                    'error': 'Connection failed - host unreachable',
                    'attempts': attempt + 1,
                    'auth_used': auth_used
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'attempts': attempt + 1,
                'auth_used': auth_used
            }
    
    return {
        'success': False,
        'error': 'Max retries exceeded',
        'attempts': max_retries
    }


class ComprehensiveHyperlinkChecker(BaseChecker):
    """
    Production-grade hyperlink and cross-reference validator.
    
    v4.0.0 Features:
    - F19: Advanced validation (DNS, SSL, redirects, soft 404)
    - F19a: Connected/Restricted mode toggle
    
    Designed for accuracy with minimal false positives.
    Works in both restricted and connected network environments.
    """
    
    CHECKER_NAME = "Hyperlinks"
    CHECKER_VERSION = "4.0.0"
    
    # ==========================================================================
    # CROSS-REFERENCE PATTERNS (Carefully tuned for accuracy)
    # ==========================================================================
    
    # Section references: "Section 1.2", "Sect. 3.4.5", "§ 2.1"
    SECTION_REF_PATTERN = re.compile(
        r'\b(?:Section|Sect\.?|§)\s*(\d+(?:\.\d+)*)\b',
        re.IGNORECASE
    )
    
    # Table references: "Table 1", "Table 2-1", "Table A.1"
    TABLE_REF_PATTERN = re.compile(
        r'\bTable\s+(\d+(?:[.-]\d+)?|[A-Z](?:\.\d+)?)\b',
        re.IGNORECASE
    )
    
    # Figure references: "Figure 1", "Fig. 2-1", "Figure A.1"
    FIGURE_REF_PATTERN = re.compile(
        r'\b(?:Figure|Fig\.?)\s+(\d+(?:[.-]\d+)?|[A-Z](?:\.\d+)?)\b',
        re.IGNORECASE
    )
    
    # Appendix references: "Appendix A", "Appendix B.1"
    APPENDIX_REF_PATTERN = re.compile(
        r'\bAppendix\s+([A-Z](?:\.\d+(?:\.\d+)*)?)\b',
        re.IGNORECASE
    )
    
    # Paragraph references: "Paragraph 3.2.1", "Para. 4.5"
    PARAGRAPH_REF_PATTERN = re.compile(
        r'\b(?:Paragraph|Para\.?)\s+(\d+(?:\.\d+)+)\b',
        re.IGNORECASE
    )
    
    # Heading patterns for structure extraction
    HEADING_PATTERNS = [
        # Numbered sections: "1.0", "2.3.4", "1.2.3.4.5"
        re.compile(r'^(\d+(?:\.\d+)*)\s+[A-Z]'),
        re.compile(r'^(\d+(?:\.\d+)*)\s*[-–—]\s*[A-Z]'),
        re.compile(r'^Section\s+(\d+(?:\.\d+)*)', re.IGNORECASE),
    ]
    
    # Table caption patterns
    TABLE_CAPTION_PATTERNS = [
        re.compile(r'^Table\s+(\d+(?:[.-]\d+)?)', re.IGNORECASE),
        re.compile(r'^Table\s+([A-Z](?:\.\d+)?)', re.IGNORECASE),
    ]
    
    # Figure caption patterns
    FIGURE_CAPTION_PATTERNS = [
        re.compile(r'^(?:Figure|Fig\.?)\s+(\d+(?:[.-]\d+)?)', re.IGNORECASE),
        re.compile(r'^(?:Figure|Fig\.?)\s+([A-Z](?:\.\d+)?)', re.IGNORECASE),
    ]
    
    # Appendix heading patterns
    APPENDIX_HEADING_PATTERNS = [
        re.compile(r'^APPENDIX\s+([A-Z](?:\.\d+(?:\.\d+)*)?)', re.IGNORECASE),
        re.compile(r'^Appendix\s+([A-Z](?:\.\d+(?:\.\d+)*)?)\s*[-–—:]', re.IGNORECASE),
    ]
    
    # Valid URL schemes
    VALID_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'mailto', 'file'}
    
    # Email validation pattern (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Suspicious TLDs that might indicate typos
    SUSPICIOUS_TLDS = {'con', 'cmo', 'ocm', 'ogg', 'orgg', 'ent', 'eduu', 'gob'}
    
    # URL typo patterns
    URL_TYPO_PATTERNS = [
        (re.compile(r'https?://www\.\.'), 'Double dot after www'),
        (re.compile(r'https?://[^/]*\s+[^/]'), 'Space in domain'),
        (re.compile(r'https?://\d+\.\d+\.\d+\.\d+(?::\d+)?/.*\s'), 'Space in URL path'),
    ]
    
    # Document reference patterns (not file paths)
    DOCUMENT_REF_PATTERNS = [
        re.compile(r'^[A-Z]{2,4}\d+(?:/[A-Z]{0,4}\d+)+$', re.IGNORECASE),
        re.compile(r'^[A-Z]\d-\d{4}/\d+$', re.IGNORECASE),
        re.compile(r'^[\w-]+/(?:Rev|Ver|v|r)\w*$', re.IGNORECASE),
        re.compile(r'^[A-Z]{2,5}/[A-Z]{2,5}[\s-]?\d*$', re.IGNORECASE),
        re.compile(r'^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$', re.IGNORECASE),
        re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4}$'),
        re.compile(r'^\d+/\d+$'),
    ]
    
    def __init__(
        self,
        enabled: bool = True,
        check_file_exists: bool = True,
        check_network_paths: bool = True,
        validate_mailto: bool = True,
        validate_url_syntax: bool = True,
        check_cross_references: bool = True,
        min_confidence: float = 0.7,
        base_path: Optional[str] = None,
        # F19a: Validation mode
        validation_mode: ValidationMode = ValidationMode.RESTRICTED,
        # F19: Advanced validation options (connected mode only)
        check_dns: bool = True,
        check_ssl: bool = True,
        follow_redirect_chain: bool = True,
        detect_soft_404s: bool = True,
        check_suspicious_urls: bool = True,
        max_retries: int = 3,
        request_timeout: int = 10
    ):
        super().__init__(enabled)
        self.check_file_exists = check_file_exists
        self.check_network_paths = check_network_paths
        self.validate_mailto = validate_mailto
        self.validate_url_syntax = validate_url_syntax
        self.check_cross_references = check_cross_references
        self.min_confidence = min_confidence
        self.base_path = base_path
        
        # F19a: Validation mode
        self.validation_mode = validation_mode
        
        # F19: Advanced validation settings
        self.check_dns = check_dns
        self.check_ssl = check_ssl
        self.follow_redirect_chain = follow_redirect_chain
        self.detect_soft_404s = detect_soft_404s
        self.check_suspicious_urls = check_suspicious_urls
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        
        # Document structure cache
        self._structure = DocumentStructure()
        self._structure_built = False
        
        # Validation results cache for reporting
        self._validation_results: List[ValidationResult] = []
    
    def set_validation_mode(self, mode: ValidationMode):
        """F19a: Set the validation mode."""
        self.validation_mode = mode
    
    def get_validation_results(self) -> List[ValidationResult]:
        """Get detailed validation results for all checked URLs."""
        return self._validation_results
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """
        Comprehensive hyperlink and cross-reference check.
        
        Args:
            paragraphs: List of (index, text) tuples
            **kwargs: 
                - filepath: Path to DOCX file for hyperlink extraction
                - hyperlinks: Pre-extracted hyperlink list
                - bookmarks: Known document bookmarks
                - headings: Document headings
                - tables: Table information
                - figures: Figure information
                - validation_mode: Override validation mode
        
        Returns:
            List of issue dictionaries
        """
        if not self.enabled:
            return []
        
        issues = []
        filepath = kwargs.get('filepath', '')
        
        # F19a: Check for mode override
        if 'validation_mode' in kwargs:
            mode_str = kwargs['validation_mode']
            if mode_str == 'connected':
                self.validation_mode = ValidationMode.CONNECTED
            elif mode_str == 'restricted':
                self.validation_mode = ValidationMode.RESTRICTED
        
        # Clear validation results cache
        self._validation_results = []
        
        # Set base path for relative link resolution
        if filepath and os.path.exists(filepath) and not self.base_path:
            self.base_path = os.path.dirname(os.path.abspath(filepath))
        
        # Build document structure for cross-reference validation
        self._build_document_structure(paragraphs, kwargs)
        
        # Extract hyperlinks from DOCX
        docx_hyperlinks = []
        if filepath and os.path.exists(filepath):
            docx_hyperlinks = self._extract_docx_hyperlinks(filepath, paragraphs)
        
        # Validate each hyperlink
        for link_info in docx_hyperlinks:
            link_issues = self._validate_hyperlink(link_info)
            issues.extend(link_issues)
        
        # Check cross-references in text
        if self.check_cross_references:
            xref_issues = self._check_cross_references(paragraphs)
            issues.extend(xref_issues)
        
        return issues
    
    def _build_document_structure(
        self,
        paragraphs: List[Tuple[int, str]],
        kwargs: Dict
    ):
        """Build document structure map for cross-reference validation."""
        self._structure = DocumentStructure()
        
        # Add provided bookmarks
        self._structure.bookmarks = set(kwargs.get('bookmarks', []))
        
        # Scan paragraphs for structure elements
        for idx, text in paragraphs:
            text_stripped = text.strip()
            if not text_stripped:
                continue
            
            # Check for section headings
            for pattern in self.HEADING_PATTERNS:
                match = pattern.match(text_stripped)
                if match:
                    section_num = match.group(1)
                    self._structure.sections.add(section_num)
                    parts = section_num.split('.')
                    for i in range(1, len(parts)):
                        parent = '.'.join(parts[:i])
                        self._structure.sections.add(parent)
                    break
            
            # Check for table captions
            for pattern in self.TABLE_CAPTION_PATTERNS:
                match = pattern.match(text_stripped)
                if match:
                    self._structure.tables.add(match.group(1))
                    break
            
            # Check for figure captions
            for pattern in self.FIGURE_CAPTION_PATTERNS:
                match = pattern.match(text_stripped)
                if match:
                    self._structure.figures.add(match.group(1))
                    break
            
            # Check for appendix headings
            for pattern in self.APPENDIX_HEADING_PATTERNS:
                match = pattern.match(text_stripped)
                if match:
                    app_id = match.group(1).upper()
                    self._structure.appendices.add(app_id)
                    if '.' in app_id:
                        self._structure.appendices.add(app_id.split('.')[0])
                    break
        
        # Use pre-extracted structure if provided
        if 'tables' in kwargs:
            for t in kwargs['tables']:
                if isinstance(t, dict) and 'number' in t:
                    self._structure.tables.add(str(t['number']))
                elif isinstance(t, str):
                    self._structure.tables.add(t)
        
        if 'figures' in kwargs:
            for f in kwargs['figures']:
                if isinstance(f, dict) and 'number' in f:
                    self._structure.figures.add(str(f['number']))
                elif isinstance(f, str):
                    self._structure.figures.add(f)
        
        self._structure_built = True
    
    def _extract_docx_hyperlinks(
        self,
        filepath: str,
        paragraphs: List[Tuple[int, str]]
    ) -> List[HyperlinkInfo]:
        """
        Extract all hyperlinks from a DOCX file with context.
        
        v3.0.108: Enhanced to handle both:
        1. Standard <w:hyperlink> elements with relationship IDs
        2. HYPERLINK field codes (<w:fldSimple> and <w:instrText>)
        """
        hyperlinks = []
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                rels = {}
                rels_file = 'word/_rels/document.xml.rels'
                if rels_file in zf.namelist():
                    with zf.open(rels_file) as f:
                        rels_tree = ET.parse(f)
                        for rel in rels_tree.findall('.//{%s}Relationship' % NAMESPACES['rel']):
                            rel_id = rel.get('Id', '')
                            target = rel.get('Target', '')
                            rel_type = rel.get('Type', '')
                            if 'hyperlink' in rel_type.lower():
                                rels[rel_id] = target
                
                if 'word/document.xml' in zf.namelist():
                    with zf.open('word/document.xml') as f:
                        doc_tree = ET.parse(f)
                        
                        # Extract bookmarks
                        for bookmark in doc_tree.iter('{%s}bookmarkStart' % NAMESPACES['w']):
                            name = bookmark.get('{%s}name' % NAMESPACES['w'], '')
                            if name and not name.startswith('_'):
                                self._structure.bookmarks.add(name)
                        
                        para_idx = 0
                        for para in doc_tree.iter('{%s}p' % NAMESPACES['w']):
                            para_text_parts = []
                            for t in para.iter('{%s}t' % NAMESPACES['w']):
                                if t.text:
                                    para_text_parts.append(t.text)
                            para_text = ''.join(para_text_parts)
                            
                            # Method 1: Standard <w:hyperlink> elements
                            for hyperlink in para.iter('{%s}hyperlink' % NAMESPACES['w']):
                                link_info = self._parse_hyperlink_element(
                                    hyperlink, rels, para_idx, para_text
                                )
                                if link_info:
                                    hyperlinks.append(link_info)
                            
                            # Method 2: <w:fldSimple> HYPERLINK field codes
                            # These are common in older Word docs and pasted content
                            for fld_simple in para.iter('{%s}fldSimple' % NAMESPACES['w']):
                                instr = fld_simple.get('{%s}instr' % NAMESPACES['w'], '')
                                link_info = self._parse_field_code_hyperlink(
                                    instr, fld_simple, para_idx, para_text
                                )
                                if link_info:
                                    hyperlinks.append(link_info)
                            
                            # Method 3: Complex field codes using <w:instrText>
                            # Format: <w:fldChar type="begin"/> ... <w:instrText> HYPERLINK "url" </w:instrText> ... <w:fldChar type="end"/>
                            instr_texts = []
                            in_field = False
                            field_display_parts = []
                            
                            for elem in para.iter():
                                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                                
                                if tag_name == 'fldChar':
                                    fld_type = elem.get('{%s}fldCharType' % NAMESPACES['w'], '')
                                    if fld_type == 'begin':
                                        in_field = True
                                        instr_texts = []
                                        field_display_parts = []
                                    elif fld_type == 'end' and in_field:
                                        in_field = False
                                        full_instr = ''.join(instr_texts)
                                        if 'HYPERLINK' in full_instr.upper():
                                            display_text = ''.join(field_display_parts)
                                            link_info = self._parse_field_code_hyperlink(
                                                full_instr, None, para_idx, para_text, display_text
                                            )
                                            if link_info:
                                                hyperlinks.append(link_info)
                                
                                elif tag_name == 'instrText' and in_field:
                                    if elem.text:
                                        instr_texts.append(elem.text)
                                
                                elif tag_name == 't' and in_field:
                                    if elem.text:
                                        field_display_parts.append(elem.text)
                            
                            if para_text.strip():
                                para_idx += 1
        
        except Exception as e:
            self._errors.append(f"Error extracting hyperlinks from DOCX: {e}")
        
        return hyperlinks
    
    def _parse_field_code_hyperlink(
        self,
        instr: str,
        element: Optional[ET.Element],
        para_idx: int,
        para_text: str,
        display_text: str = ''
    ) -> Optional[HyperlinkInfo]:
        """
        Parse a HYPERLINK field code instruction.
        
        Field codes look like:
        - HYPERLINK "http://example.com"
        - HYPERLINK "http://example.com" \\l "anchor"
        - HYPERLINK \\l "BookmarkName"
        """
        if not instr:
            return None
        
        # Extract URL from field code instruction
        # Pattern: HYPERLINK "url" or HYPERLINK \l "bookmark"
        instr_upper = instr.upper().strip()
        if 'HYPERLINK' not in instr_upper:
            return None
        
        target = ''
        anchor = ''
        
        # Try to extract quoted URL
        url_match = re.search(r'HYPERLINK\s*"([^"]+)"', instr, re.IGNORECASE)
        if url_match:
            target = url_match.group(1)
        
        # Check for local anchor (\\l "anchor")
        anchor_match = re.search(r'\\l\s*"([^"]+)"', instr, re.IGNORECASE)
        if anchor_match:
            anchor = anchor_match.group(1)
            if not target:
                target = f'#{anchor}'
        
        if not target and not anchor:
            return None
        
        # Get display text from element if not provided
        if not display_text and element is not None:
            display_parts = []
            for t in element.iter('{%s}t' % NAMESPACES['w']):
                if t.text:
                    display_parts.append(t.text)
            display_text = ''.join(display_parts).strip()
        
        link_type = self._classify_link(target)
        
        return HyperlinkInfo(
            target=target,
            display_text=display_text,
            link_type=link_type,
            paragraph_index=para_idx,
            context=para_text[:80] if para_text else display_text[:80],
            anchor=anchor,
            rel_id=''  # Field codes don't use relationship IDs
        )
    
    def _parse_hyperlink_element(
        self,
        element: ET.Element,
        rels: Dict[str, str],
        para_idx: int,
        para_text: str
    ) -> Optional[HyperlinkInfo]:
        """Parse a hyperlink XML element into structured info."""
        rel_id = element.get('{%s}id' % NAMESPACES['r'], '')
        anchor = element.get('{%s}anchor' % NAMESPACES['w'], '')
        
        display_parts = []
        for t in element.iter('{%s}t' % NAMESPACES['w']):
            if t.text:
                display_parts.append(t.text)
        display_text = ''.join(display_parts).strip()
        
        target = ''
        link_type = LinkType.UNKNOWN
        
        if rel_id and rel_id in rels:
            target = rels[rel_id]
            link_type = self._classify_link(target)
        elif anchor:
            target = f'#{anchor}'
            link_type = LinkType.INTERNAL_BOOKMARK
        
        if not target and not anchor:
            return None
        
        return HyperlinkInfo(
            target=target,
            display_text=display_text,
            link_type=link_type,
            paragraph_index=para_idx,
            context=para_text[:80] if para_text else display_text[:80],
            anchor=anchor,
            rel_id=rel_id
        )
    
    def _is_document_reference(self, target: str) -> bool:
        """Check if target looks like a document reference rather than a file path."""
        for pattern in self.DOCUMENT_REF_PATTERNS:
            if pattern.match(target.strip()):
                return True
        
        if '/' in target and len(target) < 20:
            parts = target.split('/')
            if len(parts) == 2:
                has_extension = any('.' in p and len(p.split('.')[-1]) in range(1, 5) for p in parts)
                both_short_codes = all(len(p) < 12 and re.match(r'^[\w-]+$', p) for p in parts)
                if not has_extension and both_short_codes:
                    return True
        
        return False
    
    def _classify_link(self, target: str) -> LinkType:
        """Classify the type of hyperlink target."""
        if not target:
            return LinkType.EMPTY
        
        target_lower = target.lower().strip()
        
        if target.startswith('#'):
            return LinkType.INTERNAL_BOOKMARK
        elif target_lower.startswith('mailto:'):
            return LinkType.MAILTO
        elif target.startswith('\\\\') or target.startswith('//'):
            return LinkType.NETWORK_PATH
        elif target_lower.startswith(('http://', 'https://', 'ftp://')):
            return LinkType.WEB_URL
        elif target_lower.startswith('file:'):
            return LinkType.FILE_PATH
        elif re.match(r'^[a-zA-Z]:[/\\]', target):
            return LinkType.FILE_PATH
        elif re.match(r'^\.{0,2}[/\\]', target):
            return LinkType.FILE_PATH
        elif '/' in target or '\\' in target:
            if self._is_document_reference(target):
                return LinkType.CROSS_REFERENCE
            return LinkType.FILE_PATH
        else:
            return LinkType.UNKNOWN
    
    def _validate_hyperlink(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate a single hyperlink based on its type."""
        issues = []
        
        # v3.0.95: Always create a validation result to track all hyperlinks
        result = ValidationResult(
            url=link_info.target,
            link_text=link_info.display_text or '',
            link_type=link_info.link_type,
            is_valid=True,  # Assume valid until proven otherwise
            validation_mode=self.validation_mode.value,
            paragraph_index=link_info.paragraph_index
        )
        
        if link_info.link_type == LinkType.EMPTY:
            result.is_valid = False
            result.error_message = 'Empty hyperlink target'
            issues.append(self.create_issue(
                severity='High',
                message='Empty hyperlink target',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Add a valid link target or remove the hyperlink',
                rule_id='HL001',
                flagged_text=link_info.display_text or '[empty link]'
            ))
            self._validation_results.append(result)
            return issues
        
        if link_info.link_type == LinkType.INTERNAL_BOOKMARK:
            bookmark_issues = self._validate_internal_bookmark(link_info)
            if bookmark_issues:
                result.is_valid = False
                result.error_message = bookmark_issues[0].get('message', 'Invalid bookmark')
            issues.extend(bookmark_issues)
        
        elif link_info.link_type == LinkType.MAILTO:
            if self.validate_mailto:
                mailto_issues = self._validate_mailto(link_info)
                if mailto_issues:
                    result.is_valid = False
                    result.error_message = mailto_issues[0].get('message', 'Invalid email')
                issues.extend(mailto_issues)
        
        elif link_info.link_type == LinkType.NETWORK_PATH:
            if self.check_network_paths:
                network_issues = self._validate_network_path(link_info)
                if network_issues:
                    result.is_valid = False
                    result.error_message = network_issues[0].get('message', 'Invalid network path')
                issues.extend(network_issues)
        
        elif link_info.link_type == LinkType.FILE_PATH:
            if self.check_file_exists:
                file_issues = self._validate_file_path(link_info)
                if file_issues:
                    result.is_valid = False
                    result.error_message = file_issues[0].get('message', 'Invalid file path')
                issues.extend(file_issues)
        
        elif link_info.link_type == LinkType.WEB_URL:
            # F19a: Mode-dependent validation
            if self.validate_url_syntax:
                url_issues = self._validate_url(link_info)
                if url_issues:
                    result.is_valid = False
                    result.error_message = url_issues[0].get('message', 'Invalid URL syntax')
                issues.extend(url_issues)
            
            # F19: Advanced validation only in connected mode
            if self.validation_mode == ValidationMode.CONNECTED:
                # Note: _validate_url_advanced appends its own results
                advanced_issues = self._validate_url_advanced(link_info)
                issues.extend(advanced_issues)
                # Skip appending result here since _validate_url_advanced does it
                return issues
        
        # Check for missing display text (accessibility issue)
        if link_info.target and not link_info.display_text:
            issues.append(self.create_issue(
                severity='Low',
                message='Hyperlink has no display text (accessibility issue)',
                context=f'Link to: {link_info.target[:50]}',
                paragraph_index=link_info.paragraph_index,
                suggestion='Add descriptive text for screen readers',
                rule_id='HL002',
                flagged_text=link_info.target[:40]
            ))
        
        # v3.0.95: Always append validation result for tracking
        self._validation_results.append(result)
        
        return issues
    
    def _validate_internal_bookmark(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate internal document bookmark."""
        issues = []
        
        bookmark_name = link_info.anchor or link_info.target.lstrip('#')
        
        if bookmark_name.startswith(('_Toc', '_Ref', '_Hlt', '_GoBack')):
            return issues
        
        if bookmark_name not in self._structure.bookmarks:
            if not self._is_valid_generated_bookmark(bookmark_name):
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Broken internal link: bookmark "{bookmark_name}" not found in document',
                    context=link_info.context,
                    paragraph_index=link_info.paragraph_index,
                    suggestion='Verify the bookmark exists or update the link target',
                    rule_id='HL010',
                    flagged_text=link_info.display_text or link_info.target
                ))
        
        return issues
    
    def _is_valid_generated_bookmark(self, name: str) -> bool:
        """Check if bookmark might be a valid auto-generated reference."""
        if re.match(r'^\d+(?:_\d+)*$', name):
            section_num = name.replace('_', '.')
            return section_num in self._structure.sections
        return False
    
    def _validate_mailto(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate mailto link with RFC 5322 compliance."""
        issues = []
        
        target = link_info.target
        if target.lower().startswith('mailto:'):
            target = target[7:]
        
        email_address = target.split('?')[0].strip()
        
        if not email_address:
            issues.append(self.create_issue(
                severity='High',
                message='Empty mailto link - no email address specified',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Add a valid email address after mailto:',
                rule_id='HL020',
                flagged_text=link_info.display_text or 'mailto:'
            ))
            return issues
        
        if not self.EMAIL_PATTERN.match(email_address):
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Invalid email format: "{email_address}"',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Verify email address follows format: user@domain.tld',
                rule_id='HL021',
                flagged_text=email_address
            ))
        else:
            parts = email_address.split('@')
            if len(parts) == 2:
                domain = parts[1].lower()
                tld = domain.split('.')[-1] if '.' in domain else ''
                
                if tld in self.SUSPICIOUS_TLDS:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Suspicious email domain: ".{tld}" may be a typo',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Did you mean .com, .org, or .net?',
                        rule_id='HL022',
                        flagged_text=email_address
                    ))
        
        return issues
    
    def _validate_network_path(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate network UNC path."""
        issues = []
        
        path = link_info.target.replace('/', '\\')
        
        unc_pattern = re.compile(
            r'^\\\\[a-zA-Z0-9._-]+\\[a-zA-Z0-9._$\s-]+(?:\\.*)?$'
        )
        
        if not unc_pattern.match(path):
            issues.append(self.create_issue(
                severity='Medium',
                message='Invalid network path format',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Network paths should follow \\\\server\\share\\path format',
                rule_id='HL030',
                flagged_text=link_info.target[:50]
            ))
        else:
            try:
                if os.path.exists(path):
                    pass
                else:
                    issues.append(self.create_issue(
                        severity='High',
                        message='Network path not accessible or does not exist',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Verify the network share is available and path is correct',
                        rule_id='HL031',
                        flagged_text=link_info.target[:50]
                    ))
            except (OSError, PermissionError, Exception):
                issues.append(self.create_issue(
                    severity='Low',
                    message='Cannot verify network path accessibility',
                    context=link_info.context,
                    paragraph_index=link_info.paragraph_index,
                    suggestion='Manually verify the network path is accessible',
                    rule_id='HL032',
                    flagged_text=link_info.target[:50]
                ))
        
        return issues
    
    def _validate_file_path(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate file path link."""
        issues = []
        
        path = link_info.target
        
        if path.lower().startswith('file:'):
            path = path[5:]
            while path.startswith('/'):
                path = path[1:]
            path = unquote(path)
        
        path = path.replace('/', os.sep).replace('\\', os.sep)
        
        original_path = path
        if self.base_path and not os.path.isabs(path):
            path = os.path.join(self.base_path, path)
        
        try:
            path = os.path.normpath(path)
            
            if os.path.exists(path):
                if os.path.isfile(path) and not os.access(path, os.R_OK):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Linked file exists but is not readable',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Check file permissions',
                        rule_id='HL040',
                        flagged_text=os.path.basename(path)
                    ))
            else:
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Linked file not found: "{os.path.basename(original_path)}"',
                    context=link_info.context,
                    paragraph_index=link_info.paragraph_index,
                    suggestion=f'Verify file exists at: {path}',
                    rule_id='HL041',
                    flagged_text=link_info.display_text or original_path[:40]
                ))
        
        except (OSError, ValueError):
            issues.append(self.create_issue(
                severity='Medium',
                message='Invalid file path format',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Check the file path for invalid characters',
                rule_id='HL042',
                flagged_text=link_info.target[:40]
            ))
        
        return issues
    
    def _validate_url(self, link_info: HyperlinkInfo) -> List[Dict]:
        """Validate URL syntax comprehensively (no network calls)."""
        issues = []
        
        target = link_info.target
        
        try:
            parsed = urlparse(target)
            
            if parsed.scheme.lower() not in self.VALID_SCHEMES:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Unusual URL scheme: "{parsed.scheme}"',
                    context=link_info.context,
                    paragraph_index=link_info.paragraph_index,
                    suggestion='Standard schemes are http, https, ftp',
                    rule_id='HL050',
                    flagged_text=target[:40]
                ))
            
            if not parsed.netloc:
                issues.append(self.create_issue(
                    severity='High',
                    message='URL missing domain name',
                    context=link_info.context,
                    paragraph_index=link_info.paragraph_index,
                    suggestion='Add a valid domain name to the URL',
                    rule_id='HL051',
                    flagged_text=target[:40]
                ))
            else:
                domain = parsed.netloc.lower()
                
                if ' ' in parsed.netloc or ' ' in target:
                    issues.append(self.create_issue(
                        severity='High',
                        message='URL contains spaces (invalid)',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Remove spaces or encode as %20',
                        rule_id='HL052',
                        flagged_text=target[:40]
                    ))
                
                if '..' in domain:
                    issues.append(self.create_issue(
                        severity='High',
                        message='URL contains double dots in domain (invalid)',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Remove duplicate dots from domain',
                        rule_id='HL053',
                        flagged_text=target[:40]
                    ))
                
                tld = domain.split('.')[-1] if '.' in domain else ''
                if tld in self.SUSPICIOUS_TLDS:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Suspicious domain TLD: ".{tld}" may be a typo',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Did you mean .com, .org, or .net?',
                        rule_id='HL054',
                        flagged_text=target[:40]
                    ))
            
            for pattern, message in self.URL_TYPO_PATTERNS:
                if pattern.search(target):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=message,
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Review and correct the URL',
                        rule_id='HL055',
                        flagged_text=target[:40]
                    ))
                    break
            
            # F19: Check for suspicious URLs
            if self.check_suspicious_urls:
                suspicious = detect_suspicious_url(target)
                if suspicious['suspicious']:
                    for reason in suspicious['reasons']:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Suspicious URL: {reason}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='Verify this URL is legitimate',
                            rule_id='HL056',
                            flagged_text=target[:40]
                        ))
        
        except Exception:
            issues.append(self.create_issue(
                severity='Medium',
                message='Cannot parse URL: malformed format',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Verify the URL is properly formatted',
                rule_id='HL059',
                flagged_text=target[:40]
            ))
        
        return issues
    
    def _validate_url_advanced(self, link_info: HyperlinkInfo) -> List[Dict]:
        """
        F19: Advanced URL validation (connected mode only).
        Performs DNS, SSL, redirect tracking, and soft 404 detection.
        """
        issues = []
        target = link_info.target
        
        # Create validation result object
        result = ValidationResult(
            url=target,
            is_valid=True,
            validation_mode='connected',
            domain_category=categorize_domain(target)
        )
        
        try:
            parsed = urlparse(target)
            hostname = parsed.netloc.split(':')[0]  # Remove port if present
            
            # DNS Resolution Check
            if self.check_dns and hostname:
                dns_result = check_dns_resolution(hostname)
                result.dns_resolved = dns_result['resolved']
                result.dns_ip_addresses = dns_result.get('ip_addresses', [])
                result.dns_response_time_ms = dns_result.get('response_time_ms', 0)
                
                if not dns_result['resolved']:
                    result.is_valid = False
                    issues.append(self.create_issue(
                        severity='High',
                        message=f'DNS resolution failed for "{hostname}"',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Verify the domain name is correct and exists',
                        rule_id='HL070',
                        flagged_text=target[:40]
                    ))
                    # Can't proceed without DNS
                    self._validation_results.append(result)
                    return issues
            
            # SSL Certificate Check (for HTTPS)
            if self.check_ssl and parsed.scheme.lower() == 'https' and hostname:
                ssl_result = check_ssl_certificate(hostname)
                result.ssl_valid = ssl_result.get('valid', False)
                result.ssl_issuer = ssl_result.get('issuer', '')
                result.ssl_expires = ssl_result.get('expires', '')
                result.ssl_days_until_expiry = ssl_result.get('days_until_expiry', 0)
                result.ssl_warning = ssl_result.get('warning')
                
                if not ssl_result.get('valid'):
                    issues.append(self.create_issue(
                        severity='High',
                        message=f'SSL certificate validation failed: {ssl_result.get("error", "Unknown error")}',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='The site may have an invalid or expired certificate',
                        rule_id='HL071',
                        flagged_text=target[:40]
                    ))
                elif ssl_result.get('warning'):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'SSL certificate warning: {ssl_result["warning"]}',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion='Certificate will need renewal soon',
                        rule_id='HL072',
                        flagged_text=target[:40]
                    ))
            
            # Follow Redirects
            if self.follow_redirect_chain:
                redirect_result = follow_redirects(target, timeout=self.request_timeout)
                result.final_url = redirect_result.get('final_url', target)
                result.redirect_count = redirect_result.get('redirect_count', 0)
                result.redirect_chain = redirect_result.get('chain', [])
                
                if result.redirect_count > 3:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'URL has {result.redirect_count} redirects',
                        context=link_info.context,
                        paragraph_index=link_info.paragraph_index,
                        suggestion=f'Consider updating to final URL: {result.final_url[:60]}',
                        rule_id='HL073',
                        flagged_text=target[:40]
                    ))
            
            # v6.1.11: SharePoint-aware URL validation
            # Uses the same auth cascade as the Hyperlink Validator:
            # fresh SSO session + SSL bypass + REST API probe + content-type mismatch detection
            if SP_LINK_VALIDATOR_AVAILABLE and _is_sp_url and _is_sp_url(target):
                try:
                    sp_result = _validate_sp_url(target)
                    sp_status = sp_result.get('status', 'ERROR')
                    sp_msg = sp_result.get('message', '')
                    sp_code = sp_result.get('status_code')

                    if sp_status in ('WORKING', 'SSL_WARNING'):
                        # SharePoint link is accessible — no issue to report
                        result.is_valid = True
                        result.status_code = sp_code or 200
                        self._validation_results.append(result)
                        return issues
                    elif sp_status == 'AUTH_REQUIRED':
                        # Link exists but needs auth — info-level notice, not a broken link
                        issues.append(self.create_issue(
                            severity='Info',
                            message=f'SharePoint link requires authentication: {sp_msg}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='This link may require VPN or corporate SSO credentials',
                            rule_id='HL080',
                            flagged_text=target[:80]
                        ))
                        result.status_code = sp_code or 401
                        self._validation_results.append(result)
                        return issues
                    elif sp_status == 'TIMEOUT':
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'SharePoint link timed out: {sp_msg}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='SharePoint site may be temporarily unavailable or require VPN',
                            rule_id='HL081',
                            flagged_text=target[:80]
                        ))
                        self._validation_results.append(result)
                        return issues
                    elif sp_status == 'BROKEN':
                        url_display = target if len(target) <= 80 else target[:77] + '...'
                        issues.append(self.create_issue(
                            severity='High',
                            message=f'Broken SharePoint link ({sp_msg}): {url_display}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='Verify the SharePoint URL is correct and the resource exists',
                            rule_id='HL082',
                            flagged_text=target[:80]
                        ))
                        result.is_valid = False
                        result.status_code = sp_code
                        self._validation_results.append(result)
                        return issues
                    # If status is ERROR, fall through to generic validation
                except Exception as e:
                    # SP validator failed — fall through to generic request_with_retry
                    pass

            # HTTP Request with Retry
            if REQUESTS_AVAILABLE:
                http_result = request_with_retry(
                    target,
                    max_retries=self.max_retries,
                    timeout=self.request_timeout
                )
                result.attempts = http_result.get('attempts', 1)

                if http_result.get('success'):
                    result.status_code = http_result.get('status_code')

                    # Check for error status codes
                    if result.status_code >= 400:
                        result.is_valid = False
                        severity = 'High' if result.status_code in (404, 410, 500, 502, 503) else 'Medium'
                        # BUG-M10 FIX: Include full URL in message
                        url_display = target if len(target) <= 80 else target[:77] + '...'
                        issues.append(self.create_issue(
                            severity=severity,
                            message=f'Broken hyperlink (HTTP {result.status_code}): {url_display}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='The linked resource may be unavailable',
                            rule_id='HL074',
                            flagged_text=target[:80]
                        ))
                    
                    # Soft 404 Detection
                    elif self.detect_soft_404s and result.status_code == 200:
                        # Need to do a GET request to check content
                        get_result = request_with_retry(
                            target,
                            max_retries=1,
                            timeout=self.request_timeout,
                            method='GET'
                        )
                        if get_result.get('success') and 'response' in get_result:
                            try:
                                content = get_result['response'].text[:5000]  # First 5KB
                                if detect_soft_404(content):
                                    result.is_soft_404 = True
                                    issues.append(self.create_issue(
                                        severity='Medium',
                                        message='URL appears to be a soft 404 (page not found disguised as success)',
                                        context=link_info.context,
                                        paragraph_index=link_info.paragraph_index,
                                        suggestion='Verify the page content is what you expect',
                                        rule_id='HL075',
                                        flagged_text=target[:40]
                                    ))
                            except Exception:
                                pass
                else:
                    # Request failed
                    result.is_valid = False
                    result.error = http_result.get('error', 'Unknown error')
                    
                    # Check if it's a timeout/connection error vs a hard failure
                    error_msg = http_result.get('error', '')
                    if 'timeout' in error_msg.lower() or 'unreachable' in error_msg.lower():
                        # Graceful degradation - mark as unable to verify
                        # BUG-M10 FIX: Include full URL in message
                        url_display = target if len(target) <= 60 else target[:57] + '...'
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Unable to verify URL: {url_display} ({error_msg})',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='URL may be blocked by firewall or temporarily unavailable',
                            rule_id='HL076',
                            flagged_text=target[:80]
                        ))
                    else:
                        # BUG-M10 FIX: Include full URL in message
                        url_display = target if len(target) <= 60 else target[:57] + '...'
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'URL validation failed: {url_display} - {error_msg}',
                            context=link_info.context,
                            paragraph_index=link_info.paragraph_index,
                            suggestion='Verify the URL is accessible',
                            rule_id='HL077',
                            flagged_text=target[:80]
                        ))
        
        except Exception as e:
            result.is_valid = False
            result.error = str(e)
            issues.append(self.create_issue(
                severity='Low',
                message=f'Unable to validate URL: {str(e)[:50]}',
                context=link_info.context,
                paragraph_index=link_info.paragraph_index,
                suggestion='Manual verification recommended',
                rule_id='HL079',
                flagged_text=target[:40]
            ))
        
        # Store result for reporting
        self._validation_results.append(result)
        
        return issues
    
    def _check_cross_references(
        self,
        paragraphs: List[Tuple[int, str]]
    ) -> List[Dict]:
        """Check cross-references in document text."""
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text) < 5:
                continue
            
            issues.extend(self._check_section_refs(idx, text))
            issues.extend(self._check_table_refs(idx, text))
            issues.extend(self._check_figure_refs(idx, text))
            issues.extend(self._check_appendix_refs(idx, text))
            issues.extend(self._check_paragraph_refs(idx, text))
        
        return issues
    
    def _check_section_refs(self, idx: int, text: str) -> List[Dict]:
        """Check section references."""
        issues = []
        
        for match in self.SECTION_REF_PATTERN.finditer(text):
            section_num = match.group(1)
            
            if self._structure.sections:
                if section_num not in self._structure.sections:
                    parts = section_num.split('.')
                    parent = '.'.join(parts[:-1]) if len(parts) > 1 else None
                    
                    if not parent or parent not in self._structure.sections:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to undefined section: "{section_num}"',
                            context=text[max(0, match.start()-15):match.end()+25],
                            paragraph_index=idx,
                            suggestion='Verify section number exists or update reference',
                            rule_id='HL060',
                            flagged_text=match.group(0)
                        ))
        
        return issues
    
    def _check_table_refs(self, idx: int, text: str) -> List[Dict]:
        """Check table references."""
        issues = []
        
        for match in self.TABLE_REF_PATTERN.finditer(text):
            table_num = match.group(1)
            
            if self._structure.tables:
                if table_num not in self._structure.tables:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Reference to undefined table: "Table {table_num}"',
                        context=text[max(0, match.start()-15):match.end()+25],
                        paragraph_index=idx,
                        suggestion='Verify table exists in document',
                        rule_id='HL061',
                        flagged_text=match.group(0)
                    ))
        
        return issues
    
    def _check_figure_refs(self, idx: int, text: str) -> List[Dict]:
        """Check figure references."""
        issues = []
        
        for match in self.FIGURE_REF_PATTERN.finditer(text):
            fig_num = match.group(1)
            
            if self._structure.figures:
                if fig_num not in self._structure.figures:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Reference to undefined figure: "Figure {fig_num}"',
                        context=text[max(0, match.start()-15):match.end()+25],
                        paragraph_index=idx,
                        suggestion='Verify figure exists in document',
                        rule_id='HL062',
                        flagged_text=match.group(0)
                    ))
        
        return issues
    
    def _check_appendix_refs(self, idx: int, text: str) -> List[Dict]:
        """Check appendix references."""
        issues = []
        
        for match in self.APPENDIX_REF_PATTERN.finditer(text):
            app_id = match.group(1).upper()
            base_letter = app_id.split('.')[0] if '.' in app_id else app_id
            
            if self._structure.appendices:
                if app_id not in self._structure.appendices and base_letter not in self._structure.appendices:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Reference to undefined appendix: "Appendix {app_id}"',
                        context=text[max(0, match.start()-15):match.end()+25],
                        paragraph_index=idx,
                        suggestion='Verify appendix exists in document',
                        rule_id='HL063',
                        flagged_text=match.group(0)
                    ))
        
        return issues
    
    def _check_paragraph_refs(self, idx: int, text: str) -> List[Dict]:
        """Check paragraph references."""
        issues = []
        
        for match in self.PARAGRAPH_REF_PATTERN.finditer(text):
            para_num = match.group(1)
            
            if self._structure.sections:
                if para_num not in self._structure.sections:
                    parts = para_num.split('.')
                    parent = '.'.join(parts[:-1]) if len(parts) > 1 else None
                    
                    if not parent or parent not in self._structure.sections:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to undefined paragraph: "{para_num}"',
                            context=text[max(0, match.start()-15):match.end()+25],
                            paragraph_index=idx,
                            suggestion='Verify paragraph/section number exists',
                            rule_id='HL064',
                            flagged_text=match.group(0)
                        ))
        
        return issues
    
    def get_validation_summary(self) -> Dict:
        """
        Get summary statistics of URL validation results.
        Useful for the enhanced results display.
        """
        if not self._validation_results:
            return {
                'total': 0,
                'valid': 0,
                'broken': 0,
                'warnings': 0,
                'by_category': {},
                'mode': self.validation_mode.value
            }
        
        total = len(self._validation_results)
        valid = sum(1 for r in self._validation_results if r.is_valid)
        broken = sum(1 for r in self._validation_results if not r.is_valid)
        warnings = sum(1 for r in self._validation_results if r.ssl_warning or r.is_soft_404)
        
        # Group by category
        by_category = {}
        for result in self._validation_results:
            cat = result.domain_category
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'valid': 0}
            by_category[cat]['total'] += 1
            if result.is_valid:
                by_category[cat]['valid'] += 1
        
        return {
            'total': total,
            'valid': valid,
            'broken': broken,
            'warnings': warnings,
            'by_category': by_category,
            'mode': self.validation_mode.value,
            'results': [
                {
                    'url': r.url,
                    'is_valid': r.is_valid,
                    'status_code': r.status_code,
                    'dns_resolved': r.dns_resolved,
                    'ssl_valid': r.ssl_valid,
                    'ssl_warning': r.ssl_warning,
                    'redirect_count': r.redirect_count,
                    'category': r.domain_category,
                    'is_suspicious': r.is_suspicious,
                    'error': r.error
                }
                for r in self._validation_results
            ]
        }


# Backwards compatibility alias
HyperlinkChecker = ComprehensiveHyperlinkChecker


if __name__ == '__main__':
    print(f"Comprehensive Hyperlink Checker v{__version__}")
    print("=" * 50)
    print(f"Features: DNS check, SSL validation, redirect tracking, soft 404 detection")
    print(f"Modes: RESTRICTED (default) / CONNECTED")
    print()
    
    # Test cases
    checker = ComprehensiveHyperlinkChecker(
        validation_mode=ValidationMode.RESTRICTED
    )
    
    test_paragraphs = [
        (0, "1.0 INTRODUCTION"),
        (1, "This document describes the system requirements."),
        (2, "See Section 2.1 for system overview."),
        (3, "Refer to Table 1 for the requirements matrix."),
        (4, "As shown in Figure 5, the architecture includes..."),
        (5, "2.0 SYSTEM OVERVIEW"),
        (6, "2.1 Scope"),
        (7, "Table 1. Requirements Traceability Matrix"),
        (8, "Contact support@example.com for assistance."),
        (9, "See Appendix A for additional information."),
        (10, "APPENDIX A - GLOSSARY"),
    ]
    
    print("Building document structure...")
    issues = checker.check(test_paragraphs)
    
    print(f"\nDocument Structure Found:")
    print(f"  Sections: {checker._structure.sections}")
    print(f"  Tables: {checker._structure.tables}")
    print(f"  Figures: {checker._structure.figures}")
    print(f"  Appendices: {checker._structure.appendices}")
    
    print(f"\nIssues Found (Restricted Mode): {len(issues)}")
    for issue in issues:
        print(f"  [{issue['severity']}] {issue['message']}")
