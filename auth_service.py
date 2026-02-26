"""
AEGIS Auth Service v6.2.0
=========================
Unified authentication service for all SharePoint / corporate modules.

Singleton pattern — initialized once, shared across:
- SharePoint Connector (batch scan, file download)
- Hyperlink Validator (URL validation with Windows SSO)
- Comprehensive Hyperlink Checker (document-level link checking)
- SharePoint Link Validator (SP-aware link validation)

Consolidates 5 fragmented auth systems into one shared service with:
- Cached authenticated requests.Session (auto-refresh after TTL)
- Preemptive SSPI Negotiate token generation
- MSAL OAuth 2.0 token acquisition (zero-config for SharePoint Online)
- OS certificate store integration (truststore)
- Boot-time auth probe with diagnostic results

Author: AEGIS v6.2.0
"""

import os
import sys
import time
import base64
import json
import logging
import threading
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger('aegis.auth_service')
if not logger.handlers:
    try:
        from config_logging import get_logger
        logger = get_logger('auth_service')
    except Exception:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Platform detection & auth library imports
# ---------------------------------------------------------------------------
IS_WINDOWS = sys.platform == 'win32'

# Windows SSO (Negotiate / NTLM)
NEGOTIATE_SSPI_AVAILABLE = False
NTLM_AVAILABLE = False
_HttpNegotiateAuth = None
_auth_init_method = 'none'
_auth_init_error = None

try:
    if IS_WINDOWS:
        from requests_negotiate_sspi import HttpNegotiateAuth as _HttpNegotiateAuth
        NEGOTIATE_SSPI_AVAILABLE = True
        _auth_init_method = 'negotiate_sspi'
        logger.info('[AuthService] Windows SSO: requests-negotiate-sspi available')
except ImportError as e:
    logger.debug(f'[AuthService] requests-negotiate-sspi not available: {e}')
    try:
        if IS_WINDOWS:
            from requests_ntlm import HttpNtlmAuth as _RawNtlmAuth
            import getpass as _getpass

            class _NtlmAuthWrapper:
                """Wrapper for NTLM auth using current Windows user credentials."""
                def __init__(self):
                    username = os.environ.get('USERNAME', _getpass.getuser())
                    domain = os.environ.get('USERDOMAIN', '')
                    cred = f'{domain}\\{username}' if domain else username
                    self.auth = _RawNtlmAuth(cred, None)

                def __call__(self, r):
                    return self.auth(r)

            _HttpNegotiateAuth = _NtlmAuthWrapper
            NTLM_AVAILABLE = True
            _auth_init_method = 'ntlm'
            logger.info('[AuthService] Windows SSO: requests-ntlm available (NTLM fallback)')
    except ImportError as e2:
        _auth_init_error = f'negotiate-sspi: {e}, ntlm: {e2}'
        logger.warning(f'[AuthService] NO Windows SSO available: {_auth_init_error}')
except Exception as e:
    _auth_init_error = f'Unexpected: {e}'
    logger.error(f'[AuthService] Auth init error: {e}', exc_info=True)

WINDOWS_AUTH_AVAILABLE = NEGOTIATE_SSPI_AVAILABLE or NTLM_AVAILABLE

# SSPI Preemptive Negotiate token (Windows only)
SSPI_PREEMPTIVE_AVAILABLE = False
_sspi_module = None
_win32security_module = None
try:
    if IS_WINDOWS:
        import sspi as _sspi_module
        import win32security as _win32security_module
        SSPI_PREEMPTIVE_AVAILABLE = True
        logger.info('[AuthService] SSPI preemptive Negotiate available (pywin32)')
except ImportError:
    pass
except Exception:
    pass

# MSAL OAuth 2.0
MSAL_AVAILABLE = False
_msal_module = None
try:
    import msal as _msal_module
    MSAL_AVAILABLE = True
    logger.info('[AuthService] MSAL available — OAuth 2.0 / modern auth supported')
except ImportError:
    logger.debug('[AuthService] MSAL not installed — OAuth unavailable')

# OS certificate store (truststore)
TRUSTSTORE_AVAILABLE = False
try:
    import truststore
    truststore.inject_into_ssl()
    TRUSTSTORE_AVAILABLE = True
    logger.info('[AuthService] truststore injected — using OS certificate store')
except ImportError:
    logger.debug('[AuthService] truststore not available — using certifi CA bundle')
except Exception as e:
    logger.debug(f'[AuthService] truststore injection failed: {e}')

# Headless browser (Playwright)
HEADLESS_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright as _sync_playwright
    HEADLESS_AVAILABLE = True
    logger.info('[AuthService] Playwright available — headless browser auth supported')
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Corporate domain patterns
# ---------------------------------------------------------------------------
CORPORATE_DOMAIN_PATTERNS = (
    '.myngc.com', '.northgrum.com', '.northropgrumman.com',
    'ngc.sharepoint.us', '.ngc.sharepoint.us',
    '.sharepoint.com', '.sharepoint.us',
    '.mil', '.gov',
)

IDP_DOMAINS = [
    '*.microsoftonline.com', '*.microsoftonline.us',
    '*.login.microsoftonline.com', '*.login.microsoftonline.us',
    '*.windows.net', '*.login.windows.net',
    '*.adfs.*',
]

HEADLESS_AUTH_DOMAINS = [
    '*.myngc.com', '*.northgrum.com', '*.northropgrumman.com',
    '*.ngc.sharepoint.us', '*.sharepoint.com', '*.sharepoint.us',
    '*.mil', '*.gov',
]


def is_corporate_url(url: str) -> bool:
    """Check if a URL is on a known corporate/internal domain."""
    try:
        domain = urlparse(url).netloc.lower()
        return any(p in domain for p in CORPORATE_DOMAIN_PATTERNS)
    except Exception:
        return False


def get_headless_auth_allowlist() -> str:
    """Build deduplicated auth-server-allowlist for Chromium."""
    seen = set()
    domains = []
    for d in HEADLESS_AUTH_DOMAINS + IDP_DOMAINS:
        if d not in seen:
            seen.add(d)
            domains.append(d)
    return ','.join(domains)


# ---------------------------------------------------------------------------
# SSPI Preemptive Negotiate Token
# ---------------------------------------------------------------------------
def generate_preemptive_negotiate_token(target_host: str) -> Optional[str]:
    """
    Generate a preemptive Negotiate (SPNEGO) token using Windows SSPI.

    Bypasses the normal challenge-response flow where the server must first
    send WWW-Authenticate: Negotiate in a 401 response. SharePoint Online
    (GCC High / commercial) may return 401 with EMPTY WWW-Authenticate,
    which causes requests-negotiate-sspi to never attempt authentication.
    """
    if not SSPI_PREEMPTIVE_AVAILABLE or not _sspi_module or not _win32security_module:
        return None
    try:
        targetspn = f'HTTP/{target_host}'
        clientauth = _sspi_module.ClientAuth(
            'Negotiate',
            targetspn=targetspn,
            scflags=(
                _win32security_module.ISC_REQ_MUTUAL_AUTH |
                _win32security_module.ISC_REQ_SEQUENCE_DETECT |
                _win32security_module.ISC_REQ_CONFIDENTIALITY
            ),
        )
        err, out_buf = clientauth.authorize(None)
        if out_buf and len(out_buf) > 0:
            token_data = out_buf[0].Buffer
            if token_data:
                token_b64 = base64.b64encode(token_data).decode('ascii')
                logger.debug(f'[AuthService] Generated preemptive Negotiate token '
                             f'({len(token_b64)} chars) for SPN={targetspn}')
                return token_b64
        return None
    except Exception as e:
        logger.debug(f'[AuthService] Preemptive Negotiate token failed: {e}')
        return None


# ===========================================================================
# AEGISAuthService — Singleton
# ===========================================================================
class AEGISAuthService:
    """
    Singleton auth service — initialized once, shared across all AEGIS modules.

    Provides:
    - get_rest_session(target_url) → authenticated requests.Session
    - create_fresh_session(target_url) → NEW session for thread-safe NTLM
    - probe_auth() → diagnostic info for /api/capabilities
    - get_auth_summary() → human-readable auth state
    """

    _instance = None
    _lock = threading.Lock()

    # Session cache
    SESSION_TTL = 1800  # 30 minutes before auto-refresh
    _rest_session: Optional['requests.Session'] = None
    _session_created_at: float = 0
    _session_target: Optional[str] = None

    # Auth state
    _probe_result: Optional[Dict[str, Any]] = None
    _probe_timestamp: float = 0

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'AEGISAuthService':
        """Get or create the singleton instance."""
        return cls()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    @classmethod
    def get_rest_session(cls, target_url: Optional[str] = None,
                         ssl_verify: Optional[bool] = None) -> 'requests.Session':
        """
        Get an authenticated requests.Session.

        For NTLM/Negotiate: reuses a cached session if TTL hasn't expired
        and target domain matches. Otherwise creates a new one.

        Args:
            target_url: Optional URL to tailor auth for (e.g., corporate domain → disable SSL)
            ssl_verify: Override SSL verification (None = auto-detect from domain)

        Returns:
            Authenticated requests.Session
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError('requests library not available')

        instance = cls.get_instance()

        # Auto-detect SSL verification
        if ssl_verify is None:
            if target_url and is_corporate_url(target_url):
                ssl_verify = False
            else:
                ssl_verify = True

        # Check if cached session is still valid
        now = time.time()
        target_domain = urlparse(target_url).netloc.lower() if target_url else None

        if (instance._rest_session is not None
                and (now - instance._session_created_at) < cls.SESSION_TTL
                and instance._session_target == target_domain):
            return instance._rest_session

        # Create new session
        with cls._lock:
            session = requests.Session()
            session.verify = ssl_verify

            session.headers.update({
                'User-Agent': 'AEGIS/6.2 AuthService',
                'Accept': 'application/json;odata=verbose',
            })

            # Attach Windows SSO auth
            if WINDOWS_AUTH_AVAILABLE and _HttpNegotiateAuth:
                try:
                    session.auth = _HttpNegotiateAuth()
                    logger.debug(f'[AuthService] Session created with {_auth_init_method} auth')
                except Exception as e:
                    logger.warning(f'[AuthService] SSO setup failed: {e}')

            instance._rest_session = session
            instance._session_created_at = now
            instance._session_target = target_domain

        return session

    @classmethod
    def create_fresh_session(cls, target_url: Optional[str] = None,
                              ssl_verify: Optional[bool] = None,
                              include_preemptive: bool = False) -> 'requests.Session':
        """
        Create a BRAND NEW session for thread-safe NTLM/Negotiate.

        CRITICAL: NTLM/Negotiate auth is connection-specific — the multi-step
        handshake requires the SAME TCP connection. When using ThreadPoolExecutor,
        each worker thread MUST have its own session. Never share sessions across
        threads for NTLM auth. (Lessons 75, 134)

        Args:
            target_url: URL to tailor auth for
            ssl_verify: Override SSL verification
            include_preemptive: Include preemptive SSPI token in headers

        Returns:
            Fresh authenticated requests.Session (caller owns it — close when done)
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError('requests library not available')

        # Auto-detect SSL
        if ssl_verify is None:
            if target_url and is_corporate_url(target_url):
                ssl_verify = False
            else:
                ssl_verify = True

        session = requests.Session()
        session.verify = ssl_verify
        session.headers.update({
            'User-Agent': 'AEGIS/6.2 AuthService',
            'Accept': 'application/json;odata=verbose',
        })

        # Attach Windows SSO
        if WINDOWS_AUTH_AVAILABLE and _HttpNegotiateAuth:
            try:
                session.auth = _HttpNegotiateAuth()
            except Exception as e:
                logger.warning(f'[AuthService] Fresh session SSO failed: {e}')

        # Optionally add preemptive Negotiate token
        if include_preemptive and target_url:
            host = urlparse(target_url).hostname
            if host:
                token = generate_preemptive_negotiate_token(host)
                if token:
                    session.headers['Authorization'] = f'Negotiate {token}'

        return session

    @classmethod
    def invalidate_session(cls):
        """Force session refresh on next get_rest_session() call."""
        instance = cls.get_instance()
        with cls._lock:
            if instance._rest_session:
                try:
                    instance._rest_session.close()
                except Exception:
                    pass
            instance._rest_session = None
            instance._session_created_at = 0
            instance._session_target = None

    # ------------------------------------------------------------------
    # Auth probing
    # ------------------------------------------------------------------
    @classmethod
    def probe_auth(cls, test_urls: Optional[list] = None,
                   force: bool = False) -> Dict[str, Any]:
        """
        Test current auth state. Returns diagnostic info for /api/capabilities.

        Results are cached for 5 minutes unless force=True.

        Args:
            test_urls: Optional list of URLs to probe against
            force: Force re-probe even if cached results exist

        Returns:
            Dict with auth diagnostic information
        """
        instance = cls.get_instance()

        # Return cached result if fresh
        now = time.time()
        if not force and instance._probe_result and (now - instance._probe_timestamp) < 300:
            return instance._probe_result

        result = {
            'platform': sys.platform,
            'windows_auth_available': WINDOWS_AUTH_AVAILABLE,
            'auth_method': _auth_init_method,
            'auth_init_error': _auth_init_error,
            'sspi_preemptive_available': SSPI_PREEMPTIVE_AVAILABLE,
            'msal_available': MSAL_AVAILABLE,
            'truststore_available': TRUSTSTORE_AVAILABLE,
            'headless_available': HEADLESS_AVAILABLE,
            'probe_time': None,
            'probe_url': None,
            'probe_success': None,
            'probe_message': 'Not probed',
        }

        # Probe a URL if provided
        if test_urls and WINDOWS_AUTH_AVAILABLE and _HttpNegotiateAuth:
            for url in test_urls[:3]:  # Try up to 3 URLs
                probe_session = None
                try:
                    start = time.time()
                    probe_session = cls.create_fresh_session(target_url=url)
                    resp = probe_session.get(
                        url,
                        timeout=(10, 20),
                        allow_redirects=True,
                        stream=True,
                    )
                    resp.close()
                    elapsed = (time.time() - start) * 1000

                    if 200 <= resp.status_code < 400:
                        result['probe_success'] = True
                        result['probe_url'] = url
                        result['probe_time'] = elapsed
                        result['probe_message'] = (
                            f'Windows SSO confirmed working '
                            f'(HTTP {resp.status_code}, {elapsed:.0f}ms)'
                        )
                        break
                    elif resp.status_code == 401:
                        result['probe_message'] = f'Auth challenge (401) at {url}'
                    elif resp.status_code == 403:
                        result['probe_message'] = f'Access forbidden (403) at {url}'
                except Exception as e:
                    result['probe_message'] = f'Probe failed: {str(e)[:100]}'
                finally:
                    if probe_session:
                        try:
                            probe_session.close()
                        except Exception:
                            pass

        instance._probe_result = result
        instance._probe_timestamp = now
        return result

    @classmethod
    def get_auth_summary(cls) -> Dict[str, Any]:
        """Get a concise auth state summary for UI display."""
        return {
            'windows_sso': WINDOWS_AUTH_AVAILABLE,
            'method': _auth_init_method,
            'sspi': SSPI_PREEMPTIVE_AVAILABLE,
            'oauth': MSAL_AVAILABLE,
            'truststore': TRUSTSTORE_AVAILABLE,
            'headless': HEADLESS_AVAILABLE,
            'error': _auth_init_error,
        }

    # ------------------------------------------------------------------
    # Convenience: public references to module-level auth objects
    # ------------------------------------------------------------------
    @staticmethod
    def get_negotiate_auth_class():
        """Get the HttpNegotiateAuth class (or NTLM wrapper) for direct use."""
        return _HttpNegotiateAuth

    @staticmethod
    def get_msal_module():
        """Get the msal module if available."""
        return _msal_module

    @staticmethod
    def get_sspi_modules():
        """Get (sspi, win32security) modules if available."""
        return _sspi_module, _win32security_module
