#!/usr/bin/env python3
"""
SharePoint Link Validator — Shared utility for validating SharePoint URLs
=========================================================================
Used by BOTH:
  - ComprehensiveHyperlinkChecker (document review)
  - HyperlinkValidator (standalone HV tool)

Provides the same SharePoint authentication cascade as the HV:
  1. Fresh SSO session + SSL bypass
  2. GET fallback (HEAD often rejected by SP)
  3. SharePoint REST API probe
  4. Content-Type mismatch detection (login redirect detection)

Thread-safe: creates fresh session per call, no shared state.

Author: AEGIS
Version: 1.0.0 (v6.1.11)
"""

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger('aegis.sp_link_validator')

# --- Optional imports with graceful fallback ---

REQUESTS_AVAILABLE = False
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    pass

# v6.2.0: Windows SSO via unified auth_service
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
_splv_auth_service_loaded = False
try:
    from auth_service import (
        AEGISAuthService as _AuthService,
        WINDOWS_AUTH_AVAILABLE,
        is_corporate_url as _is_corp_url,
    )
    HttpNegotiateAuth = _AuthService.get_negotiate_auth_class()

    # v6.2.1-hotfix: Safety net — if auth_service loaded but returned None
    # for HttpNegotiateAuth (e.g., Windows auth libs failed inside auth_service),
    # attempt direct imports as fallback. Without this, HttpNegotiateAuth stays
    # None, no auth is set on sessions, and SP URL validation gets 401. (Lesson 164)
    import sys as _sys
    if HttpNegotiateAuth is None and _sys.platform == 'win32':
        logger.warning('[SP LinkValidator] auth_service returned None for HttpNegotiateAuth — '
                       'attempting direct import fallback')
        try:
            from requests_negotiate_sspi import HttpNegotiateAuth
            WINDOWS_AUTH_AVAILABLE = True
            logger.info('[SP LinkValidator] Direct fallback: negotiate_sspi')
        except ImportError:
            try:
                from requests_ntlm import HttpNtlmAuth
                import getpass
                import os as _os
                class HttpNegotiateAuth:
                    """NTLM wrapper using current Windows user."""
                    def __init__(self):
                        username = _os.environ.get('USERNAME', getpass.getuser())
                        domain = _os.environ.get('USERDOMAIN', '')
                        if domain:
                            self.auth = HttpNtlmAuth(f'{domain}\\{username}', None)
                        else:
                            self.auth = HttpNtlmAuth(username, None)
                    def __call__(self, r):
                        return self.auth(r)
                WINDOWS_AUTH_AVAILABLE = True
                logger.info('[SP LinkValidator] Direct fallback: ntlm')
            except ImportError:
                pass

    if WINDOWS_AUTH_AVAILABLE:
        logger.info(f'[SP LinkValidator] Unified auth service: Windows SSO available '
                    f'(HttpNegotiateAuth={"available" if HttpNegotiateAuth else "NONE"})')
    _splv_auth_service_loaded = True
except ImportError:
    logger.info('[SP LinkValidator] auth_service not available — using direct imports')
except Exception as e:
    logger.warning(f'[SP LinkValidator] auth_service import error: {e} — using direct imports')

# Fallback to direct imports when auth_service is unavailable or broken
if not _splv_auth_service_loaded:
    try:
        from requests_negotiate_sspi import HttpNegotiateAuth
        WINDOWS_AUTH_AVAILABLE = True
    except ImportError:
        try:
            from requests_ntlm import HttpNtlmAuth
            import getpass
            import os as _os

            class HttpNegotiateAuth:
                """NTLM wrapper using current Windows user."""
                def __init__(self):
                    username = _os.environ.get('USERNAME', getpass.getuser())
                    domain = _os.environ.get('USERDOMAIN', '')
                    if domain:
                        self.auth = HttpNtlmAuth(f'{domain}\\{username}', None)
                    else:
                        self.auth = HttpNtlmAuth(username, None)
                def __call__(self, r):
                    return self.auth(r)
            WINDOWS_AUTH_AVAILABLE = True
        except ImportError:
            pass

SHAREPOINT_CONNECTOR_AVAILABLE = False
_SharePointConnector = None
_parse_sharepoint_url = None
try:
    from sharepoint_connector import SharePointConnector as _SharePointConnector
    from sharepoint_connector import parse_sharepoint_url as _parse_sharepoint_url
    SHAREPOINT_CONNECTOR_AVAILABLE = True
except ImportError:
    pass

# Suppress urllib3 InsecureRequestWarning for verify=False
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


# --- SharePoint URL Detection ---

SP_DOMAIN_PATTERNS = (
    'sharepoint.com', 'sharepoint.us',
    '.ngc.sharepoint.us', 'ngc.sharepoint.us',
)

# Document extensions that should return non-HTML content types
DOC_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats',
    '.xls': 'application/vnd.ms-excel',
    '.pptx': 'application/vnd.openxmlformats',
    '.ppt': 'application/vnd.ms-powerpoint',
}


def is_sharepoint_url(url: str) -> bool:
    """Check if a URL points to a SharePoint domain."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return any(p in host for p in SP_DOMAIN_PATTERNS)
    except Exception:
        return False


def _create_fresh_sso_session(verify_ssl: bool = False) -> 'requests.Session':
    """Create a brand-new requests.Session with Windows SSO auth.

    Fresh session is critical for NTLM/Negotiate — auth state is
    connection-specific and cannot be shared across threads.
    """
    session = requests.Session()
    session.verify = verify_ssl
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
    })
    if WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
        try:
            session.auth = HttpNegotiateAuth()
        except Exception as e:
            logger.debug(f"SSO auth setup failed: {e}")
    return session


def _check_content_type_mismatch(url: str, response) -> bool:
    """Detect if a document URL returned HTML (likely login redirect).

    When SharePoint redirects to a login page, the response is HTTP 200
    with Content-Type: text/html — but the URL implies a document.
    """
    try:
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        content_type = response.headers.get('Content-Type', '').lower()

        for ext in DOC_EXTENSIONS:
            if path_lower.endswith(ext):
                if 'text/html' in content_type:
                    return True  # Document URL returning HTML = login redirect
                break
    except Exception:
        pass
    return False


def _check_login_redirect(url: str, response) -> bool:
    """Check if the final URL after redirects is a login page."""
    try:
        final_url = response.url.lower() if hasattr(response, 'url') else ''
        login_patterns = (
            '/adfs/ls/', 'login.microsoftonline', '/saml2/',
            '/oauth2/authorize', '/_forms/default.aspx',
            'login.windows.net', 'autologon.microsoftazuread-sso'
        )
        return any(p in final_url for p in login_patterns)
    except Exception:
        return False


def validate_sharepoint_url(url: str) -> dict:
    """
    Validate a SharePoint URL using the full auth cascade.

    Returns:
        dict with keys:
            - status: 'WORKING', 'SSL_WARNING', 'AUTH_REQUIRED', 'BROKEN', 'TIMEOUT', 'ERROR'
            - message: Human-readable explanation
            - status_code: HTTP status code (int or None)
            - auth_method: Which auth method succeeded (str)
    """
    if not REQUESTS_AVAILABLE:
        return {
            'status': 'ERROR',
            'message': 'requests library not available',
            'status_code': None,
            'auth_method': 'none'
        }

    result = {
        'status': 'BROKEN',
        'message': 'SharePoint URL validation failed',
        'status_code': None,
        'auth_method': 'none'
    }

    # --- Strategy 1: HEAD with fresh SSO + SSL bypass ---
    try:
        session = _create_fresh_sso_session(verify_ssl=False)
        try:
            resp = session.head(url, timeout=(15, 30), allow_redirects=True)
            result['status_code'] = resp.status_code

            if 200 <= resp.status_code < 400:
                # Check for login redirect
                if _check_login_redirect(url, resp):
                    result['status'] = 'AUTH_REQUIRED'
                    result['message'] = 'SharePoint redirected to login page'
                    result['auth_method'] = 'sso_head'
                    return result

                result['status'] = 'SSL_WARNING'
                result['message'] = 'SharePoint link accessible (SSL bypass, HEAD verified)'
                result['auth_method'] = 'sso_head'
                return result

            # HEAD returned 4xx/5xx — try GET (many SP servers reject HEAD)
            if resp.status_code in (401, 403, 405, 501):
                pass  # Fall through to Strategy 2
            elif resp.status_code == 404:
                result['status'] = 'BROKEN'
                result['message'] = f'SharePoint resource not found (HTTP {resp.status_code})'
                result['auth_method'] = 'sso_head'
                return result
            elif resp.status_code >= 500:
                result['status'] = 'BROKEN'
                result['message'] = f'SharePoint server error (HTTP {resp.status_code})'
                result['auth_method'] = 'sso_head'
                # Don't return yet — try GET fallback
        finally:
            session.close()
    except requests.exceptions.Timeout:
        result['status'] = 'TIMEOUT'
        result['message'] = 'SharePoint connection timed out'
        # Fall through to try GET
    except requests.exceptions.SSLError as e:
        logger.debug(f"SSL error on HEAD for {url}: {e}")
        # SSL error even with verify=False is unusual — continue to GET
    except requests.exceptions.ConnectionError as e:
        logger.debug(f"Connection error on HEAD for {url}: {e}")
        # Fall through to GET
    except Exception as e:
        logger.debug(f"HEAD request failed for {url}: {e}")

    # --- Strategy 2: GET with fresh SSO + SSL bypass ---
    try:
        session = _create_fresh_sso_session(verify_ssl=False)
        try:
            resp = session.get(url, timeout=(15, 30), allow_redirects=True, stream=True)
            result['status_code'] = resp.status_code

            if 200 <= resp.status_code < 400:
                # Check for content-type mismatch (document URL returning HTML = login redirect)
                if _check_content_type_mismatch(url, resp):
                    result['status'] = 'AUTH_REQUIRED'
                    result['message'] = 'SharePoint document URL returned HTML (likely login redirect)'
                    result['auth_method'] = 'sso_get'
                    return result

                # Check for login page redirect
                if _check_login_redirect(url, resp):
                    result['status'] = 'AUTH_REQUIRED'
                    result['message'] = 'SharePoint redirected to login page'
                    result['auth_method'] = 'sso_get'
                    return result

                # Check if it's a file download
                content_disp = resp.headers.get('Content-Disposition', '')
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'attachment' in content_disp or any(
                    mt in content_type for mt in (
                        'pdf', 'msword', 'openxmlformats', 'excel',
                        'powerpoint', 'octet-stream', 'zip'
                    )
                ):
                    result['status'] = 'SSL_WARNING'
                    result['message'] = 'SharePoint file download link (valid, SSL bypass)'
                    result['auth_method'] = 'sso_get'
                    return result

                result['status'] = 'SSL_WARNING'
                result['message'] = 'SharePoint link accessible (SSL bypass, GET verified)'
                result['auth_method'] = 'sso_get'
                return result

            elif resp.status_code in (401, 403):
                result['status'] = 'AUTH_REQUIRED'
                result['message'] = f'SharePoint requires authentication (HTTP {resp.status_code})'
                result['auth_method'] = 'sso_get'
                # Don't return — try REST API probe
            elif resp.status_code == 404:
                result['status'] = 'BROKEN'
                result['message'] = 'SharePoint resource not found (HTTP 404)'
                result['auth_method'] = 'sso_get'
                return result
            else:
                result['status'] = 'BROKEN'
                result['message'] = f'SharePoint returned HTTP {resp.status_code}'
                result['auth_method'] = 'sso_get'
                # Fall through to REST API
        finally:
            session.close()
    except requests.exceptions.Timeout:
        result['status'] = 'TIMEOUT'
        result['message'] = 'SharePoint connection timed out (GET)'
    except requests.exceptions.ConnectionError as e:
        error_str = str(e).lower()
        if 'name or service not known' in error_str or 'getaddrinfo' in error_str:
            result['status'] = 'BROKEN'
            result['message'] = 'SharePoint domain DNS resolution failed'
            return result
        result['status'] = 'BROKEN'
        result['message'] = f'SharePoint connection failed: {str(e)[:80]}'
    except Exception as e:
        logger.debug(f"GET request failed for {url}: {e}")

    # --- Strategy 3: SharePoint REST API probe ---
    if SHAREPOINT_CONNECTOR_AVAILABLE and _parse_sharepoint_url:
        try:
            sp_parsed = _parse_sharepoint_url(url)
            sp_site = sp_parsed.get('site_url', '')
            if sp_site:
                connector = _SharePointConnector(sp_site)
                probe = connector.test_connection()
                if probe.get('success'):
                    site_title = probe.get('title', 'SharePoint')
                    result['status'] = 'SSL_WARNING'
                    result['message'] = f'SharePoint site accessible — "{site_title}" (REST API verified)'
                    result['status_code'] = probe.get('status_code', 200)
                    result['auth_method'] = 'rest_api'
                    if connector._ssl_fallback_used:
                        result['message'] += ' [SSL bypass]'
                    return result
                elif probe.get('status_code') == 401:
                    # Site exists but auth failed — at least we know it's real
                    result['status'] = 'AUTH_REQUIRED'
                    result['message'] = 'SharePoint site exists — authentication required'
                    result['status_code'] = 401
                    result['auth_method'] = 'rest_api'
                    return result
        except Exception as e:
            logger.debug(f"SharePoint REST API probe failed for {url}: {e}")

    return result
