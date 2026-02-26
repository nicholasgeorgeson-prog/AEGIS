"""
SharePoint Online Connector for AEGIS Document Review.

Connects to SharePoint document libraries via REST API using Windows SSO
(Negotiate/NTLM authentication) or OAuth 2.0 (MSAL) for SharePoint Online.

v6.0.5 — Nicholas Georgeson

Features:
    - Windows SSO (Negotiate/NTLM) authentication with preemptive token
    - OAuth 2.0 / MSAL fallback for SharePoint Online (GCC High / commercial)
    - Multi-layer SSL fallback for corporate CA certificates
    - Auto-detection of default document library path
    - Recursive folder traversal with depth limit
    - SharePoint REST API throttle handling (429)

Usage:
    connector = SharePointConnector('https://ngc.sharepoint.us/sites/MyTeam')
    probe = connector.test_connection()
    if probe['success']:
        files = connector.list_files('/sites/MyTeam/Shared Documents')
        connector.download_file(files[0]['server_relative_url'], '/tmp/file.docx')
    connector.close()
"""

import os
import sys
import time
import logging
import tempfile
import json
import base64
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, unquote, quote

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Suppress urllib3 InsecureRequestWarning when using verify=False for corporate CAs
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except (ImportError, AttributeError):
    pass

# Logger MUST be created before auth init block (auth init logs messages)
logger = logging.getLogger('aegis.sharepoint')

# v6.1.4: Add file handler so SharePoint connector diagnostics go to logs/ dir
# Previously logger only wrote to stdout, making it invisible in exported logs
try:
    from pathlib import Path as _sp_Path
    from logging.handlers import RotatingFileHandler as _sp_RFH
    _sp_log_dir = _sp_Path(__file__).parent / 'logs'
    _sp_log_dir.mkdir(exist_ok=True)
    _sp_file_handler = _sp_RFH(
        _sp_log_dir / 'sharepoint.log',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=2,
        encoding='utf-8',
    )
    _sp_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    ))
    logger.addHandler(_sp_file_handler)
    if not logger.level:
        logger.setLevel(logging.DEBUG)
except Exception:
    pass  # Don't crash if log setup fails

# v6.2.0: Unified auth service — single initialization for all SPO modules
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
_sp_auth_init_error = None
_sp_auth_method = 'none'
SSPI_PREEMPTIVE_AVAILABLE = False
_sspi_module = None
_win32security_module = None
MSAL_AVAILABLE = False
_msal_module = None
HEADLESS_SP_AVAILABLE = False
_sp_sync_playwright = None

try:
    from auth_service import (
        AEGISAuthService as _AuthService,
        WINDOWS_AUTH_AVAILABLE,
        SSPI_PREEMPTIVE_AVAILABLE,
        MSAL_AVAILABLE,
        HEADLESS_AVAILABLE as HEADLESS_SP_AVAILABLE,
        NEGOTIATE_SSPI_AVAILABLE as _NEG_SSPI,
        NTLM_AVAILABLE as _NTLM_AVAIL,
        _auth_init_method as _sp_auth_method,
        _auth_init_error as _sp_auth_init_error,
        _sspi_module,
        _win32security_module,
        _msal_module,
        generate_preemptive_negotiate_token as _generate_preemptive_negotiate_token_unified,
        is_corporate_url,
        get_headless_auth_allowlist,
        CORPORATE_DOMAIN_PATTERNS,
        IDP_DOMAINS,
        HEADLESS_AUTH_DOMAINS,
    )
    HttpNegotiateAuth = _AuthService.get_negotiate_auth_class()
    # Playwright import still needed for HeadlessSPConnector
    if HEADLESS_SP_AVAILABLE:
        try:
            from playwright.sync_api import sync_playwright as _sp_sync_playwright
        except ImportError:
            HEADLESS_SP_AVAILABLE = False
    logger.info(f'[AEGIS SharePoint] Unified auth service loaded: '
                f'SSO={WINDOWS_AUTH_AVAILABLE} ({_sp_auth_method}), '
                f'SSPI={SSPI_PREEMPTIVE_AVAILABLE}, '
                f'MSAL={MSAL_AVAILABLE}, '
                f'Headless={HEADLESS_SP_AVAILABLE}')
except ImportError:
    logger.info('[AEGIS SharePoint] auth_service not available — using direct imports')
    # Fallback to direct imports (preserves backward compatibility)
    try:
        if sys.platform == 'win32':
            import sspi
            import win32security
            import pywintypes
            _sspi_module = sspi
            _win32security_module = win32security
            SSPI_PREEMPTIVE_AVAILABLE = True
    except (ImportError, Exception):
        pass
    try:
        import msal
        _msal_module = msal
        MSAL_AVAILABLE = True
    except ImportError:
        pass
    try:
        from playwright.sync_api import sync_playwright as _sp_sync_playwright
        HEADLESS_SP_AVAILABLE = True
    except ImportError:
        pass
    try:
        if sys.platform == 'win32':
            from requests_negotiate_sspi import HttpNegotiateAuth
            WINDOWS_AUTH_AVAILABLE = True
            _sp_auth_method = 'negotiate_sspi'
        else:
            _sp_auth_init_error = f'Platform is {sys.platform}, not win32'
    except ImportError as e:
        try:
            if sys.platform == 'win32':
                from requests_ntlm import HttpNtlmAuth as HttpNegotiateAuth
                WINDOWS_AUTH_AVAILABLE = True
                _sp_auth_method = 'ntlm'
        except ImportError as e2:
            _sp_auth_init_error = f'negotiate-sspi: {e}, ntlm: {e2}'
    except Exception as e:
        _sp_auth_init_error = f'Unexpected: {e}'


def _generate_preemptive_negotiate_token(target_host: str) -> Optional[str]:
    """
    v6.0.5: Generate a preemptive Negotiate (SPNEGO) token using Windows SSPI.

    This bypasses the normal challenge-response flow where the server must first
    send WWW-Authenticate: Negotiate in a 401 response. SharePoint Online
    (GCC High / commercial) may return 401 with an EMPTY WWW-Authenticate header,
    which causes requests-negotiate-sspi to never attempt authentication.

    By generating the initial token proactively and attaching it to the first
    request, we can authenticate even when the server doesn't advertise
    Negotiate support in the 401 response.

    Args:
        target_host: The hostname to authenticate against (e.g., ngc.sharepoint.us)

    Returns:
        Base64-encoded Negotiate token string, or None if generation fails
    """
    if not SSPI_PREEMPTIVE_AVAILABLE or not _sspi_module or not _win32security_module:
        return None

    try:
        # Build SPN (Service Principal Name) for HTTP service
        targetspn = f'HTTP/{target_host}'

        # Create client auth context for Negotiate scheme
        # scflags: request mutual auth + sequence detect + confidentiality
        pkg_info = _win32security_module.QuerySecurityPackageInfo('Negotiate')
        clientauth = _sspi_module.ClientAuth(
            'Negotiate',
            targetspn=targetspn,
            scflags=_win32security_module.ISC_REQ_MUTUAL_AUTH |
                    _win32security_module.ISC_REQ_SEQUENCE_DETECT |
                    _win32security_module.ISC_REQ_CONFIDENTIALITY,
        )

        # Generate initial (Type 1) token — no input buffer for first call
        err, out_buf = clientauth.authorize(None)
        # out_buf is a list of (buffer_data, buffer_type) tuples
        if out_buf and len(out_buf) > 0:
            token_data = out_buf[0].Buffer
            if token_data:
                token_b64 = base64.b64encode(token_data).decode('ascii')
                logger.info(f"SharePoint: Generated preemptive Negotiate token ({len(token_b64)} chars) "
                            f"for SPN={targetspn}")
                return token_b64

        logger.debug("SharePoint: SSPI authorize returned empty buffer")
        return None

    except Exception as e:
        logger.debug(f"SharePoint: Preemptive Negotiate token generation failed: {e}")
        return None


def _get_oauth_config() -> Optional[Dict[str, str]]:
    """
    v6.0.8: Read OAuth / MSAL configuration from config.json OR auto-detect.

    If 'sharepoint_oauth' exists in config.json with client_id + tenant_id → use that.
    Otherwise, returns None (caller should use _auto_detect_oauth_config for auto-setup).

    Expected keys under 'sharepoint_oauth':
        client_id:  Azure AD / Entra app registration client ID
        tenant_id:  Azure AD / Entra tenant ID (GUID or domain)
        client_secret: (optional) App secret — only for non-interactive flows
        authority:  (optional) Override login endpoint (default: auto-detected from domain)

    Returns:
        Dict with OAuth config, or None if not configured
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if not os.path.exists(config_path):
            return None
        with open(config_path, 'r') as f:
            config = json.load(f)
        oauth = config.get('sharepoint_oauth', {})
        if oauth.get('client_id') and oauth.get('tenant_id'):
            return oauth
        return None
    except Exception:
        return None


# v6.0.8: Well-known Microsoft first-party client IDs that support delegated access
# These are pre-registered by Microsoft and available in ALL tenants without admin setup.
# Microsoft Office (works for SharePoint, OneDrive, etc.)
_MS_OFFICE_CLIENT_ID = 'd3590ed6-52b3-4102-aeff-aad2292ab01c'


def _discover_tenant_guid(tenant_name: str, site_url: str) -> Optional[str]:
    """
    v6.1.0: Discover the Azure AD tenant GUID from the SharePoint URL.

    Uses two strategies:
    1. OpenID Connect discovery endpoint (most reliable, public, works for all clouds)
    2. SharePoint 401 response WWW-Authenticate realm (fallback)

    Args:
        tenant_name: Short tenant name extracted from URL (e.g., 'ngc')
        site_url: Full SharePoint site URL

    Returns:
        Tenant GUID string, or None if discovery fails
    """
    import re as _re

    is_gcc_high = '.sharepoint.us' in site_url.lower()
    login_host = 'login.microsoftonline.us' if is_gcc_high else 'login.microsoftonline.com'
    onmicrosoft_tld = 'onmicrosoft.us' if is_gcc_high else 'onmicrosoft.com'

    # Strategy 1: OpenID Configuration endpoint (public, no auth needed)
    # This is the most reliable method, especially for GCC High where
    # SharePoint returns empty WWW-Authenticate headers
    oidc_url = f'https://{login_host}/{tenant_name}.{onmicrosoft_tld}/.well-known/openid-configuration'
    try:
        logger.info(f"SharePoint tenant discovery: Trying OIDC endpoint at {oidc_url}")
        # v6.1.1: Use verify=False because corporate SSL inspection replaces certs
        # with internal CA that Python's certifi doesn't trust
        resp = requests.get(oidc_url, timeout=10, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            issuer = data.get('issuer', '')
            # Extract GUID from issuer URL like:
            # https://login.microsoftonline.us/aaaabbbb-0000-cccc-1111-dddd2222eeee/v2.0
            guid_match = _re.search(
                r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
                issuer
            )
            if guid_match:
                tenant_guid = guid_match.group(1)
                logger.info(f"SharePoint tenant discovery: Found tenant GUID via OIDC: {tenant_guid}")
                return tenant_guid
            else:
                logger.debug(f"SharePoint tenant discovery: OIDC returned issuer but no GUID: {issuer}")
        else:
            logger.debug(f"SharePoint tenant discovery: OIDC returned status {resp.status_code}")
    except Exception as e:
        logger.debug(f"SharePoint tenant discovery: OIDC request failed: {e}")

    # Strategy 2: SharePoint 401 Bearer realm (fallback)
    # Send an unauthenticated request to SharePoint's client.svc — the 401
    # response may contain WWW-Authenticate: Bearer realm="{tenant_guid}"
    # Note: GCC High often returns empty WWW-Authenticate, so this is a fallback only
    try:
        svc_url = f'{site_url.rstrip("/")}/_vti_bin/client.svc'
        logger.debug(f"SharePoint tenant discovery: Trying Bearer realm at {svc_url}")
        resp = requests.get(
            svc_url,
            headers={'Authorization': 'Bearer'},
            verify=False,
            timeout=15,
            allow_redirects=False,
        )
        www_auth = resp.headers.get('WWW-Authenticate', '')
        if www_auth:
            realm_match = _re.search(
                r'realm="([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"',
                www_auth
            )
            if realm_match:
                tenant_guid = realm_match.group(1)
                logger.info(f"SharePoint tenant discovery: Found tenant GUID via 401 realm: {tenant_guid}")
                return tenant_guid
            else:
                logger.debug(f"SharePoint tenant discovery: WWW-Authenticate has no GUID realm: "
                             f"{www_auth[:100]}")
        else:
            logger.debug(f"SharePoint tenant discovery: Empty WWW-Authenticate header (expected for GCC High)")
    except Exception as e:
        logger.debug(f"SharePoint tenant discovery: Bearer realm request failed: {e}")

    return None


def _auto_detect_oauth_config(site_url: str) -> Optional[Dict[str, str]]:
    """
    v6.1.0: Auto-detect OAuth configuration from the SharePoint site URL.

    Uses Microsoft's well-known Office client ID and discovers the tenant
    from the SharePoint domain name. Resolves the full tenant identifier
    using either '{tenant}.onmicrosoft.us' domain format (for GCC High)
    or the discovered tenant GUID via OIDC discovery.

    v6.0.9 FIX: The bare tenant name (e.g., 'ngc') is NOT a valid Azure AD
    tenant identifier. MSAL needs either:
    - The tenant GUID (e.g., 'aaaabbbb-0000-cccc-1111-dddd2222eeee')
    - The full domain (e.g., 'ngc.onmicrosoft.us')

    Returns:
        Dict with auto-detected OAuth config, or None if URL doesn't match SharePoint Online patterns
    """
    try:
        parsed = urlparse(site_url)
        host = parsed.hostname or ''

        # Extract tenant name from SharePoint domain
        # ngc.sharepoint.us → tenant_name = 'ngc'
        # contoso.sharepoint.com → tenant_name = 'contoso'
        tenant_name = None
        is_gcc_high = False
        if '.sharepoint.us' in host:
            tenant_name = host.split('.sharepoint.us')[0]
            is_gcc_high = True
        elif '.sharepoint.com' in host:
            tenant_name = host.split('.sharepoint.com')[0]

        if not tenant_name:
            return None

        # Remove '-my' suffix from personal OneDrive URLs (e.g., 'ngc-my' → 'ngc')
        if tenant_name.endswith('-my'):
            tenant_name = tenant_name[:-3]

        # v6.1.0 FIX: Build a valid Azure AD tenant identifier
        # The bare name (e.g., 'ngc') doesn't work for MSAL authority discovery.
        # Use '{tenant}.onmicrosoft.us' for GCC High or '{tenant}.onmicrosoft.com' for commercial
        onmicrosoft_tld = 'onmicrosoft.us' if is_gcc_high else 'onmicrosoft.com'
        tenant_domain = f'{tenant_name}.{onmicrosoft_tld}'

        # Try to discover the actual tenant GUID for maximum reliability
        tenant_guid = _discover_tenant_guid(tenant_name, site_url)

        # Use GUID if discovered, otherwise use the .onmicrosoft domain format
        tenant_id = tenant_guid or tenant_domain
        authority = _get_oauth_authority(tenant_id, site_url)

        logger.info(f"SharePoint OAuth auto-detect: tenant_name='{tenant_name}', "
                    f"tenant_id='{tenant_id}' ({'GUID' if tenant_guid else 'domain'}), "
                    f"authority='{authority}', client_id=Microsoft Office (well-known)")

        return {
            'client_id': _MS_OFFICE_CLIENT_ID,
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'authority': authority,
            'auto_detected': True,
        }
    except Exception as e:
        logger.debug(f"SharePoint OAuth auto-detect failed: {e}")
        return None


def _get_oauth_authority(tenant_id: str, site_url: str) -> str:
    """
    v6.0.5: Determine the correct OAuth authority URL based on the SharePoint domain.

    GCC High (.sharepoint.us) uses login.microsoftonline.us
    Commercial (.sharepoint.com) uses login.microsoftonline.com

    Args:
        tenant_id: Valid Azure AD tenant identifier (GUID or domain like 'ngc.onmicrosoft.us')
        site_url: SharePoint site URL (used to determine cloud instance)
    """
    if '.sharepoint.us' in site_url.lower():
        return f'https://login.microsoftonline.us/{tenant_id}'
    else:
        return f'https://login.microsoftonline.com/{tenant_id}'


def _get_oauth_resource(site_url: str) -> str:
    """
    v6.0.5: Get the OAuth resource/scope for the SharePoint site.

    For SharePoint REST API, the scope is the root site URL + /.default
    """
    parsed = urlparse(site_url)
    return f'{parsed.scheme}://{parsed.netloc}/.default'


def _try_msal_app_creation(client_id: str, authority: str, label: str, ssl_verify: bool = False):
    """
    v6.1.1: Try to create an MSAL PublicClientApplication with the given authority.

    CRITICAL for GCC High / US Government cloud:
    - instance_discovery=False: MSAL by default contacts the COMMERCIAL cloud's
      instance discovery endpoint (login.microsoftonline.com) to validate the authority.
      For GCC High (.microsoftonline.us), this validation FAILS because the commercial
      endpoint doesn't know about government cloud authorities. Setting this to False
      tells MSAL to trust the authority URL we give it without validation.
    - verify=False: Corporate SSL inspection (proxy/WAF) replaces TLS certificates
      with internal CA certs that Python's certifi bundle doesn't trust. MSAL uses
      requests internally, and without verify=False, its HTTPS calls to
      login.microsoftonline.us fail with SSL certificate errors.

    Returns the app instance or None if creation fails.
    """
    try:
        # v6.1.1 FIX: Both parameters are CRITICAL for GCC High environments
        # Without instance_discovery=False → "Unable to get authority configuration"
        # Without verify=False → SSL errors on corporate networks
        kwargs = {
            'client_id': client_id,
            'authority': authority,
        }

        # instance_discovery=False — skip commercial cloud authority validation
        # This parameter was added in MSAL Python 1.12.0
        try:
            kwargs['instance_discovery'] = False
        except Exception:
            pass  # Older MSAL versions may not support this kwarg

        # verify=False — bypass corporate SSL inspection
        # This parameter was added in MSAL Python 1.20.0
        try:
            kwargs['verify'] = ssl_verify
        except Exception:
            pass  # Older MSAL versions may not support this kwarg

        logger.info(f"SharePoint OAuth: Creating MSAL app ({label}) with "
                    f"instance_discovery=False, verify={ssl_verify}")
        app = _msal_module.PublicClientApplication(**kwargs)
        logger.info(f"SharePoint OAuth: MSAL app created successfully ({label})")
        return app
    except TypeError as te:
        # If MSAL version doesn't support instance_discovery or verify kwargs,
        # retry without them
        logger.debug(f"SharePoint OAuth: MSAL kwargs not supported ({label}): {te} — "
                     f"retrying with minimal params")
        try:
            app = _msal_module.PublicClientApplication(
                client_id,
                authority=authority,
            )
            logger.info(f"SharePoint OAuth: MSAL app created (minimal params, {label})")
            return app
        except Exception as e2:
            logger.debug(f"SharePoint OAuth: MSAL app creation failed even with minimal params ({label}): {e2}")
            return None
    except Exception as e:
        logger.warning(f"SharePoint OAuth: MSAL app creation failed ({label}): {e}")
        return None


def _acquire_oauth_token(site_url: str) -> Optional[str]:
    """
    v6.1.0: Acquire an OAuth 2.0 Bearer token for SharePoint access via MSAL.

    Uses a multi-strategy approach to get a token using the user's existing
    Windows credentials — NO app registration required for most configurations.

    Strategy order:
    1. Explicit config (sharepoint_oauth in config.json) with client_secret → client credentials
    2. IWA (Integrated Windows Auth) — seamless SSO using current Windows logon
    3. Device code flow — one-time browser auth (interactive, last resort)

    v6.1.0 FIX: Uses proper tenant identifier format:
    - Tenant GUID (discovered via OIDC endpoint) — most reliable
    - {tenant}.onmicrosoft.us for GCC High — domain format fallback
    - {tenant}.onmicrosoft.com for commercial — domain format fallback

    v6.1.1 FIX: MSAL app creation uses instance_discovery=False (skip commercial
    cloud authority validation for GCC High) and verify=False (bypass corporate SSL).

    For GCC High environments (.sharepoint.us), uses login.microsoftonline.us authority.

    Returns:
        Bearer token string, or None if acquisition fails
    """
    if not MSAL_AVAILABLE or not _msal_module:
        return None

    # Try explicit config first, then auto-detect from SharePoint URL
    oauth_config = _get_oauth_config()
    config_source = 'config.json'
    if not oauth_config:
        oauth_config = _auto_detect_oauth_config(site_url)
        config_source = 'auto-detected'
    if not oauth_config:
        logger.debug("SharePoint OAuth: No config available (explicit or auto-detected)")
        return None

    client_id = oauth_config['client_id']
    tenant_id = oauth_config['tenant_id']
    client_secret = oauth_config.get('client_secret', '')
    authority = oauth_config.get('authority', '') or _get_oauth_authority(tenant_id, site_url)
    resource = _get_oauth_resource(site_url)
    is_auto = oauth_config.get('auto_detected', False)

    logger.info(f"SharePoint OAuth: Using {config_source} config — "
                f"client_id={'Microsoft Office (well-known)' if is_auto else client_id[:8] + '...'}, "
                f"tenant={tenant_id}, authority={authority}")

    # Strategy 1: Client credentials (only with explicit config + secret)
    if client_secret and not is_auto:
        try:
            # v6.1.1: ConfidentialClientApplication also needs instance_discovery=False
            # and verify=False for GCC High / corporate networks
            cca_kwargs = {
                'client_id': client_id,
                'authority': authority,
                'client_credential': client_secret,
            }
            try:
                cca_kwargs['instance_discovery'] = False
                cca_kwargs['verify'] = False
            except Exception:
                pass
            app = _msal_module.ConfidentialClientApplication(**cca_kwargs)
            result = app.acquire_token_for_client(scopes=[resource])
            if result and 'access_token' in result:
                logger.info(f"SharePoint: OAuth token acquired via client credentials")
                return result['access_token']
            elif result:
                logger.debug(f"SharePoint OAuth client credentials failed: "
                             f"{result.get('error', '?')} — {result.get('error_description', '')[:200]}")
        except Exception as e:
            logger.debug(f"SharePoint OAuth client credentials error: {e}")

    # v6.1.1: Try to create MSAL app — validate authority is correct
    # ssl_verify=False is critical for corporate networks with SSL inspection
    app = _try_msal_app_creation(client_id, authority, f'authority={authority}', ssl_verify=False)

    # v6.1.0: If MSAL app creation fails (bad authority), try fallback authorities
    if app is None and is_auto:
        tenant_name = oauth_config.get('tenant_name', '')
        if tenant_name:
            # Build fallback authority list
            is_gcc_high = '.sharepoint.us' in site_url.lower()
            login_host = 'login.microsoftonline.us' if is_gcc_high else 'login.microsoftonline.com'
            onmicrosoft_tld = 'onmicrosoft.us' if is_gcc_high else 'onmicrosoft.com'

            fallback_authorities = []
            # If we used a GUID, try domain format; if domain, try other formats
            domain_authority = f'https://{login_host}/{tenant_name}.{onmicrosoft_tld}'
            if authority != domain_authority:
                fallback_authorities.append(domain_authority)
            # Try 'organizations' as last resort (multi-tenant)
            fallback_authorities.append(f'https://{login_host}/organizations')

            for fb_authority in fallback_authorities:
                logger.info(f"SharePoint OAuth: Trying fallback authority: {fb_authority}")
                app = _try_msal_app_creation(client_id, fb_authority, f'fallback={fb_authority}', ssl_verify=False)
                if app:
                    authority = fb_authority
                    break

    if app is None:
        logger.warning(f"SharePoint OAuth: Could not create MSAL app with any authority. "
                       f"Tenant discovery may have failed.")
        return None

    # v6.1.1: Note — acquire_token_by_integrated_windows_auth() does NOT exist in
    # MSAL Python. It only exists in MSAL.NET. The hasattr check always returned False,
    # making this entire block dead code in v6.0.5 through v6.1.0.
    # For zero-config SSO, we rely on:
    #   1. Preemptive SSPI Negotiate token (Strategy 1 in __init__)
    #   2. Device code flow (Strategy 3 below) for one-time interactive auth
    #   3. Silent token from cache (checked at top of Strategy 3)
    username = _get_windows_upn()
    if username:
        logger.info(f"SharePoint OAuth: Windows user detected: '{username}' — "
                     f"will use device code flow (IWA not available in MSAL Python)")
    else:
        logger.info("SharePoint OAuth: No Windows UPN available (expected on non-Windows)")

    # Strategy 3: Device code flow — requires one-time browser auth
    # This is the most reliable fallback for GCC High environments
    try:
        scopes = [resource.replace('/.default', '/AllSites.Read')]

        # Check cache first (from previous device code auth)
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and 'access_token' in result:
                logger.info(f"SharePoint: OAuth token acquired from cache (silent)")
                return result['access_token']

        # Device code flow — log the user_code so the user can see it
        flow = app.initiate_device_flow(scopes=scopes)
        if 'user_code' in flow:
            logger.info(f"SharePoint OAuth device code flow: {flow.get('message', '')}")
            # Store the flow info for the UI to display
            _device_code_flows[site_url] = {
                'message': flow.get('message', ''),
                'user_code': flow.get('user_code', ''),
                'verification_uri': flow.get('verification_uri', ''),
                'flow': flow,
                'app': app,
            }
            # Don't block here — return None and let the UI handle the device code flow
            logger.info(f"SharePoint OAuth: Device code flow initiated — user must complete auth in browser")
            return None
        else:
            error = flow.get('error', 'unknown')
            desc = flow.get('error_description', '')
            logger.warning(f"SharePoint OAuth device code initiation failed: {error} — {desc[:200]}")

    except Exception as e:
        logger.warning(f"SharePoint OAuth device code error: {e}")

    return None


# Module-level storage for device code flows (keyed by site URL)
_device_code_flows: Dict[str, Any] = {}


def get_pending_device_flow(site_url: str) -> Optional[Dict[str, str]]:
    """
    v6.1.2: Check if a device code flow is pending for a given site URL.
    Returns the user-visible info (message, user_code, verification_uri) or None.
    """
    flow = _device_code_flows.get(site_url)
    if flow:
        return {
            'message': flow.get('message', ''),
            'user_code': flow.get('user_code', ''),
            'verification_uri': flow.get('verification_uri', ''),
        }
    # Also check if any flow matches by site_url prefix (in case of URL normalization)
    for key, flow in _device_code_flows.items():
        if key.rstrip('/') == site_url.rstrip('/'):
            return {
                'message': flow.get('message', ''),
                'user_code': flow.get('user_code', ''),
                'verification_uri': flow.get('verification_uri', ''),
            }
    return None


def complete_device_flow(site_url: str, timeout: int = 120) -> Optional[str]:
    """
    v6.1.2: Complete a pending device code flow by waiting for the user
    to enter the code in their browser.

    Args:
        site_url: The site URL used when initiating the flow
        timeout: Max seconds to wait for user to complete auth

    Returns:
        Bearer token string, or None if flow failed/timed out
    """
    flow_info = None
    for key in list(_device_code_flows.keys()):
        if key.rstrip('/') == site_url.rstrip('/'):
            flow_info = _device_code_flows[key]
            break

    if not flow_info:
        logger.warning(f"SharePoint: No pending device code flow for {site_url}")
        return None

    app = flow_info.get('app')
    flow = flow_info.get('flow')
    if not app or not flow:
        logger.warning(f"SharePoint: Invalid device code flow state for {site_url}")
        return None

    try:
        # This blocks until the user enters the code or timeout
        logger.info(f"SharePoint: Waiting for device code flow completion (timeout={timeout}s)...")
        result = app.acquire_token_by_device_flow(flow, exit_condition=lambda flow: flow.get('interval', 5))
        if result and 'access_token' in result:
            logger.info(f"SharePoint: Device code flow completed — token acquired!")
            # Clean up the pending flow
            for key in list(_device_code_flows.keys()):
                if key.rstrip('/') == site_url.rstrip('/'):
                    del _device_code_flows[key]
            return result['access_token']
        else:
            error = result.get('error', 'unknown') if result else 'no_result'
            desc = result.get('error_description', '') if result else ''
            logger.warning(f"SharePoint: Device code flow failed: {error} — {desc[:200]}")
            return None
    except Exception as e:
        logger.error(f"SharePoint: Device code flow error: {e}")
        return None


def _get_windows_upn() -> Optional[str]:
    """
    v6.0.8: Get the current Windows user's UPN (User Principal Name).

    Tries multiple approaches:
    1. win32api.GetUserNameEx(8) — NameUserPrincipal → user@domain.com
    2. Environment variables USERNAME + USERDNSDOMAIN → user@domain.com
    3. getpass.getuser() — plain username (may work for ADFS federation)

    Returns:
        UPN string or None
    """
    if sys.platform != 'win32':
        return None

    # Try win32api first (most reliable)
    try:
        import win32api
        # NameUserPrincipal = 8 → returns user@domain.com format
        upn = win32api.GetUserNameEx(8)
        if upn and '@' in upn:
            return upn
    except Exception:
        pass

    try:
        import win32api
        # NameSamCompatible = 2 → returns DOMAIN\user format
        sam = win32api.GetUserNameEx(2)
        if sam:
            # Convert DOMAIN\user to user@domain
            parts = sam.split('\\')
            if len(parts) == 2:
                dns_domain = os.environ.get('USERDNSDOMAIN', '')
                if dns_domain:
                    return f"{parts[1]}@{dns_domain}"
    except Exception:
        pass

    # Fallback to environment variables
    try:
        username = os.environ.get('USERNAME', '')
        dns_domain = os.environ.get('USERDNSDOMAIN', '')
        if username and dns_domain:
            return f"{username}@{dns_domain}"
    except Exception:
        pass

    # Last resort — plain username
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return None


def parse_sharepoint_url(url: str) -> Dict[str, str]:
    """
    v5.9.42: Parse a SharePoint URL into site_url and library_path components.

    Handles various formats users might copy from their browser:
        https://ngc.sharepoint.us/sites/MyTeam/Shared Documents/Subfolder
        https://ngc.sharepoint.us/sites/MyTeam/Shared%20Documents
        https://ngc.sharepoint.us/:f:/s/MyTeam/Shared%20Documents
        https://ngc.sharepoint.us/sites/MyTeam
        https://ngc.sharepoint.us/sites/MyTeam/Shared%20Documents/Forms/AllItems.aspx?...
        https://ngc.sharepoint.us/:f:/r/sites/MyTeam/Shared%20Documents/Subfolder?csf=1&web=1

    Returns:
        {'site_url': str, 'library_path': str, 'host': str}
    """
    url = url.strip().rstrip('/')
    parsed = urlparse(url)
    host = parsed.netloc
    path = unquote(parsed.path)

    # Strip query params and fragments — they're SharePoint UI state, not path
    # But first check for ?id= or ?RootFolder= params which contain the actual folder path
    query_path = ''
    if parsed.query:
        from urllib.parse import parse_qs
        qp = parse_qs(parsed.query)
        # SharePoint modern UI: ?id=/sites/Team/Shared Documents/Subfolder
        if 'id' in qp:
            query_path = unquote(qp['id'][0])
        # SharePoint classic UI: ?RootFolder=/sites/Team/Shared Documents/Subfolder
        elif 'RootFolder' in qp:
            query_path = unquote(qp['RootFolder'][0])

    # Handle /:f:/s/ and /:f:/r/ short URLs (SharePoint sharing links)
    # Format: /:f:/[s|r|g]/sites/SiteName/LibraryName/SubFolder
    #      or /:f:/[s|r|g]/SiteName/LibraryName/SubFolder  (legacy)
    if '/:f:/s/' in path or '/:f:/r/' in path or '/:f:/g/' in path:
        short_match = path.split('/:f:/')
        if len(short_match) > 1:
            after = short_match[1].lstrip('/')
            # Remove the leading type indicator (s/, r/, g/)
            if '/' in after:
                type_prefix, rest = after.split('/', 1)
                if type_prefix in ('s', 'r', 'g'):
                    after = rest
            # Now after might be "sites/MyTeam/Shared Documents" or just "MyTeam/Shared Documents"
            site_prefix = '/sites/'
            if after.lower().startswith('sites/'):
                after = after[len('sites/'):]  # strip "sites/" → "MyTeam/Shared Documents"
            elif after.lower().startswith('teams/'):
                site_prefix = '/teams/'
                after = after[len('teams/'):]
            parts = after.split('/', 1)
            site_name = parts[0]
            site_url = f"{parsed.scheme}://{host}{site_prefix}{site_name}"
            lib_path = f"{site_prefix}{site_name}/{parts[1]}" if len(parts) > 1 else ''
            # Clean up: remove /Forms/AllItems.aspx if present
            if '/Forms/' in lib_path:
                lib_path = lib_path[:lib_path.index('/Forms/')]
            return {'site_url': site_url, 'library_path': lib_path, 'host': host}

    # Clean up the path — remove SharePoint UI artifacts
    # /sites/MyTeam/Shared Documents/Forms/AllItems.aspx → /sites/MyTeam/Shared Documents
    clean_path = path
    if '/Forms/AllItems.aspx' in clean_path:
        clean_path = clean_path[:clean_path.index('/Forms/AllItems.aspx')]
    elif '/Forms/' in clean_path and clean_path.endswith('.aspx'):
        clean_path = clean_path[:clean_path.index('/Forms/')]

    # Standard URL: find the /sites/XXX or /teams/XXX boundary
    path_lower = clean_path.lower()
    site_url = f"{parsed.scheme}://{host}"
    library_path = ''

    for prefix in ('/sites/', '/teams/'):
        idx = path_lower.find(prefix)
        if idx >= 0:
            # Find end of site name (next / after the site name)
            after_prefix = clean_path[idx + len(prefix):]
            slash_idx = after_prefix.find('/')
            if slash_idx >= 0:
                site_name = after_prefix[:slash_idx]
                site_url = f"{parsed.scheme}://{host}{prefix}{site_name}"
                remainder = after_prefix[slash_idx:]
                if remainder and remainder != '/':
                    library_path = f"{prefix}{site_name}{remainder}"
            else:
                site_name = after_prefix
                site_url = f"{parsed.scheme}://{host}{prefix}{site_name}"
            break

    # If we got a folder path from query params (?id= or ?RootFolder=), prefer that
    if query_path and not library_path:
        library_path = query_path
    elif query_path and library_path:
        # query_path is usually more specific (deeper subfolder)
        if len(query_path) > len(library_path):
            library_path = query_path

    return {'site_url': site_url, 'library_path': library_path, 'host': host}


class SharePointConnector:
    """
    Connect to SharePoint Online via REST API with Windows SSO.

    Uses the SharePoint REST API (/_api/web/...) with HttpNegotiateAuth
    for transparent Windows credential passthrough — same auth mechanism
    that Chrome uses when auto-authenticating on corporate SharePoint sites.
    """

    # Supported document extensions for AEGIS review
    SUPPORTED_EXTENSIONS = {'.docx', '.pdf', '.doc'}

    # SharePoint REST API throttling — respect 429 responses
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds between retries

    # v5.9.35: Default document library names to try when auto-detecting
    DEFAULT_LIBRARIES = [
        'Shared Documents',
        'Documents',
        'Shared%20Documents',
    ]

    def __init__(self, site_url: str, timeout: int = 45):
        """
        Initialize SharePoint connector.

        v6.0.5: Multi-strategy auth — tries Negotiate SSO (preemptive), then OAuth/MSAL.
        SharePoint Online (GCC High / commercial) has disabled legacy auth (NTLM/Negotiate)
        as of Feb 2026, returning 401 with empty WWW-Authenticate header. The preemptive
        Negotiate token bypasses the empty header issue, and OAuth provides a modern auth
        fallback for environments that only accept Bearer tokens.

        Args:
            site_url: SharePoint site URL (e.g., https://ngc.sharepoint.us/sites/MyTeam)
            timeout: HTTP request timeout in seconds (v5.9.38: increased from 30→45 for corporate networks)
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")

        self.site_url = site_url.rstrip('/')
        self.timeout = timeout

        # v5.9.41: Auto-detect corporate domains and bypass SSL verification
        # Corporate CAs are not in Python's certifi bundle (Lesson 81)
        _corp_patterns = ('sharepoint.us', 'sharepoint.com', '.ngc.', '.myngc.',
                          '.northgrum.', '.northropgrumman.')
        _is_corp = any(p in site_url.lower() for p in _corp_patterns)
        self.ssl_verify = not _is_corp
        self._ssl_fallback_used = _is_corp
        if _is_corp:
            logger.info(f"SharePoint connector: Corporate domain detected — SSL verification disabled (certifi CA mismatch)")

        # v6.0.5: Detect if this is SharePoint Online (requires modern auth)
        _online_patterns = ('sharepoint.us', 'sharepoint.com', 'sharepoint-df.com')
        self._is_sharepoint_online = any(p in site_url.lower() for p in _online_patterns)
        if self._is_sharepoint_online:
            logger.info(f"SharePoint connector: SharePoint Online detected — will try preemptive Negotiate + OAuth fallback")

        self._last_error_detail = ''  # v5.9.38: detailed error for diagnostics
        self._oauth_token = None  # v6.0.5: cached OAuth bearer token
        self.session = requests.Session()

        # v6.0.8: Multi-strategy auth configuration (zero-config — auto-detects from URL)
        # Strategy 1: Windows SSO with preemptive Negotiate token (pywin32 SSPI)
        # Strategy 2: OAuth 2.0 via MSAL (auto-detected tenant + well-known client ID)
        # Strategy 3: Standard requests-negotiate-sspi (reactive, needs WWW-Authenticate)
        self.auth_method = 'none'
        self._preemptive_token = None

        # Try preemptive SSPI token generation first
        if SSPI_PREEMPTIVE_AVAILABLE and sys.platform == 'win32':
            parsed = urlparse(site_url)
            token = _generate_preemptive_negotiate_token(parsed.hostname)
            if token:
                self._preemptive_token = token
                self.auth_method = 'negotiate_preemptive'
                logger.info(f"SharePoint connector: Preemptive Negotiate token generated for {parsed.hostname}")

        # Also set up standard SSO auth as fallback (for the challenge-response flow)
        if WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
            try:
                self.session.auth = HttpNegotiateAuth()
                if self.auth_method == 'none':
                    self.auth_method = 'negotiate'
                logger.info(f"SharePoint connector: Windows SSO (Negotiate) configured")
            except Exception as e:
                logger.warning(f"SharePoint connector: SSO setup failed: {e}")
                if self.auth_method == 'none':
                    self.auth_method = 'none'
        else:
            if sys.platform == 'win32' and self.auth_method == 'none':
                logger.warning("SharePoint connector: Windows auth packages missing — install requests-negotiate-sspi")
            elif sys.platform != 'win32':
                logger.info("SharePoint connector: Non-Windows platform — SSO not available (expected on Mac dev)")

        # v6.1.0: Try OAuth token acquisition if configured
        if MSAL_AVAILABLE:
            oauth_token = _acquire_oauth_token(site_url)
            if oauth_token:
                self._oauth_token = oauth_token
                if self.auth_method == 'none':
                    self.auth_method = 'oauth'
                logger.info(f"SharePoint connector: OAuth token acquired via MSAL")
        elif self._is_sharepoint_online:
            logger.warning(f"SharePoint connector: MSAL not installed — OAuth unavailable for SharePoint Online. "
                           f"Install with: pip install msal")

        # v6.1.0: Auth strategy summary for diagnostics
        strategies = []
        if self._preemptive_token:
            strategies.append('Preemptive-SSPI')
        if self._oauth_token:
            strategies.append('OAuth-Bearer')
        if WINDOWS_AUTH_AVAILABLE:
            strategies.append('Negotiate-SSO')
        if not strategies:
            strategies.append('NONE')
        logger.info(f"SharePoint connector: Auth strategies active: {', '.join(strategies)} | "
                    f"Primary method: {self.auth_method} | "
                    f"Online={self._is_sharepoint_online} | SSL-verify={self.ssl_verify}")

        # SharePoint REST API headers
        self.session.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'AEGIS/6.1.0 SharePointConnector',
        })

    @staticmethod
    def _encode_sp_path(path: str) -> str:
        """
        v6.0.3: Encode a SharePoint server-relative path for use inside
        GetFolderByServerRelativePath(decodedUrl='...') and
        GetFileByServerRelativePath(decodedUrl='...') OData function parameters.

        Uses Microsoft's recommended ResourcePath API (decodedUrl) instead of
        the legacy ServerRelativeUrl API. The decodedUrl parameter automatically
        decodes percent-encoded values before using them as paths, so:
          - & → %26 (decoded back to & by SharePoint)
          - # → %23 (decoded back to # by SharePoint)
          - % → %25 (decoded back to % by SharePoint)
          - ' → '' (OData single-quote escaping, NOT percent-encoded)

        Reference: https://learn.microsoft.com/en-us/sharepoint/dev/
        solution-guidance/supporting-and-in-file-and-folder-with-the-resourcepath-api
        """
        # Percent-encode everything except path separators (/)
        # The decodedUrl parameter auto-decodes %26→&, %23→#, etc.
        encoded = quote(path, safe='/')
        # OData single-quote escaping: ' must be doubled inside '...' strings
        encoded = encoded.replace("'", "''")
        return encoded

    def _api_get(self, endpoint: str, stream: bool = False) -> requests.Response:
        """
        Make a GET request to the SharePoint REST API with retry logic.

        v6.0.5: Multi-strategy authentication:
        1. Preemptive Negotiate token (bypasses empty WWW-Authenticate)
        2. Standard requests-negotiate-sspi (reactive, needs WWW-Authenticate in 401)
        3. OAuth Bearer token (MSAL, for SharePoint Online modern auth)

        v5.9.35: Added multi-layer SSL fallback for corporate CA certificates.
        Python's requests/certifi doesn't trust corporate CAs (same as Lesson 81).
        Strategy: try with SSL verification → retry with verify=False → retry with
        fresh session + verify=False + SSO auth.

        Args:
            endpoint: API endpoint (appended to site_url)
            stream: Whether to stream the response (for file downloads)

        Returns:
            requests.Response object

        Raises:
            requests.RequestException on persistent failure
        """
        url = f"{self.site_url}{endpoint}"
        ssl_retried = False  # Track if we already tried SSL fallback (doesn't count as a retry)
        preemptive_tried = False  # v6.0.5: track if we tried preemptive Negotiate
        oauth_tried = False  # v6.0.5: track if we tried OAuth Bearer

        attempt = 0
        while attempt < self.MAX_RETRIES:
            try:
                # v6.0.5: Build request headers — may include preemptive auth token
                extra_headers = {}
                if self._preemptive_token and not preemptive_tried:
                    extra_headers['Authorization'] = f'Negotiate {self._preemptive_token}'
                    preemptive_tried = True
                    logger.debug(f"SharePoint: Using preemptive Negotiate token for {endpoint}")
                elif self._oauth_token and not oauth_tried:
                    extra_headers['Authorization'] = f'Bearer {self._oauth_token}'
                    oauth_tried = True
                    logger.debug(f"SharePoint: Using OAuth Bearer token for {endpoint}")

                resp = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=stream,
                    allow_redirects=True,
                    verify=self.ssl_verify,
                    headers=extra_headers if extra_headers else None,
                )

                # Handle SharePoint throttling
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get('Retry-After', self.RETRY_DELAY * (attempt + 1)))
                    logger.warning(f"SharePoint throttled (429) — waiting {retry_after}s")
                    time.sleep(retry_after)
                    attempt += 1
                    continue

                # v6.0.5: If 401 with preemptive token, try OAuth before giving up
                if resp.status_code == 401:
                    www_auth = resp.headers.get('WWW-Authenticate', '')
                    logger.debug(f"SharePoint 401: WWW-Authenticate='{www_auth[:200]}', "
                                 f"preemptive_tried={preemptive_tried}, oauth_tried={oauth_tried}")

                    # If preemptive Negotiate failed, try OAuth
                    if preemptive_tried and not oauth_tried and self._oauth_token:
                        logger.info(f"SharePoint: Preemptive Negotiate rejected — trying OAuth Bearer")
                        continue  # Loop will use OAuth token on next iteration

                    # If we haven't tried OAuth yet and have a token, try it
                    if not oauth_tried and self._oauth_token:
                        continue  # Loop will use OAuth token on next iteration

                    # If we haven't tried preemptive but standard negotiate also got 401
                    # and the WWW-Authenticate is empty, try preemptive on next loop
                    if not preemptive_tried and self._preemptive_token and not www_auth:
                        logger.info(f"SharePoint: Standard Negotiate got 401 with empty WWW-Authenticate "
                                    f"— retrying with preemptive token")
                        continue  # Loop will use preemptive token on next iteration

                return resp

            except requests.exceptions.SSLError as ssl_err:
                # v5.9.35: Corporate CA cert not trusted by Python's certifi bundle
                # Fallback: disable SSL verification (same pattern as hyperlink_validator)
                if self.ssl_verify and not ssl_retried:
                    logger.warning(f"SharePoint SSL error (corporate CA?) — retrying with verify=False: {ssl_err}")
                    self.ssl_verify = False
                    self._ssl_fallback_used = True
                    ssl_retried = True
                    continue  # Retry immediately — does NOT increment attempt
                elif attempt < self.MAX_RETRIES - 1:
                    # Already using verify=False but still SSL error — try fresh session
                    logger.warning(f"SharePoint SSL error even with verify=False — trying fresh session")
                    self._create_fresh_session()
                    wait = self.RETRY_DELAY * (attempt + 1)
                    time.sleep(wait)
                    attempt += 1
                else:
                    raise

            except requests.exceptions.ConnectionError as conn_err:
                # v5.9.38: ConnectionError can wrap SSL errors on some platforms
                err_str = str(conn_err).lower()
                is_ssl = any(kw in err_str for kw in ['ssl', 'certificate', 'handshake', 'tls', 'cert'])

                if is_ssl and self.ssl_verify and not ssl_retried:
                    logger.warning(f"SharePoint connection error (SSL-related) — retrying with verify=False: {conn_err}")
                    self.ssl_verify = False
                    self._ssl_fallback_used = True
                    ssl_retried = True
                    continue  # Retry immediately — does NOT increment attempt
                elif not ssl_retried and self.ssl_verify:
                    # v5.9.38: Some corporate networks wrap non-SSL connection errors
                    # Try with verify=False anyway as it sometimes resolves proxy/intercept issues
                    logger.warning(f"SharePoint connection error — trying verify=False as fallback: {conn_err}")
                    self.ssl_verify = False
                    self._ssl_fallback_used = True
                    ssl_retried = True
                    continue  # Retry immediately
                elif attempt < self.MAX_RETRIES - 1:
                    # v5.9.38: On connection errors, try fresh session with increased timeout
                    logger.warning(f"SharePoint request failed (attempt {attempt + 1}): {conn_err}")
                    self._create_fresh_session()
                    wait = self.RETRY_DELAY * (attempt + 1)
                    time.sleep(wait)
                    attempt += 1
                else:
                    raise

            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_DELAY * (attempt + 1)
                    logger.warning(f"SharePoint request failed (attempt {attempt + 1}): {e} — retrying in {wait}s")
                    time.sleep(wait)
                    attempt += 1
                else:
                    raise

        # Should not reach here, but just in case
        raise requests.exceptions.RequestException(f"Failed after {self.MAX_RETRIES} retries")

    def _create_fresh_session(self):
        """Create a fresh requests session with SSL bypass + Windows SSO auth."""
        try:
            self.session.close()
        except Exception:
            pass

        self.session = requests.Session()
        self.ssl_verify = False
        self._ssl_fallback_used = True

        # v6.0.5: If OAuth is our primary auth method, use that
        if self.auth_method == 'oauth' and self._oauth_token:
            self.session.headers['Authorization'] = f'Bearer {self._oauth_token}'
        elif WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
            try:
                self.session.auth = HttpNegotiateAuth()
            except Exception as e:
                logger.warning(f"SharePoint: Fresh session SSO setup failed: {e}")

        self.session.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'AEGIS/6.0.5 SharePointConnector',
        })

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to SharePoint site using Windows SSO.

        Probes /_api/web to verify authentication works.

        Returns:
            {
                'success': bool,
                'title': str (site title),
                'url': str (site URL),
                'auth_method': str,
                'message': str,
                'status_code': int
            }
        """
        try:
            resp = self._api_get('/_api/web')

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # OData verbose format: data is in 'd' key
                    d = data.get('d', data)
                    title = d.get('Title', 'Unknown')
                    url = d.get('Url', self.site_url)
                    ssl_note = ' (SSL bypass: corporate CA)' if self._ssl_fallback_used else ''
                    return {
                        'success': True,
                        'title': title,
                        'url': url,
                        'auth_method': self.auth_method,
                        'message': f'Connected to "{title}" via {self.auth_method}{ssl_note}',
                        'status_code': 200,
                    }
                except (ValueError, KeyError) as e:
                    return {
                        'success': True,
                        'title': 'Connected',
                        'url': self.site_url,
                        'auth_method': self.auth_method,
                        'message': f'Connected (could not parse site title: {e})',
                        'status_code': 200,
                    }

            elif resp.status_code == 401:
                # v5.9.43: Capture WWW-Authenticate header for diagnostics
                www_auth = resp.headers.get('WWW-Authenticate', '')
                resp_headers_diag = {
                    'www_authenticate': www_auth[:200] if www_auth else '(none)',
                    'server': resp.headers.get('Server', '(none)'),
                    'x_ms_diagnostics': resp.headers.get('X-MS-Diagnostics', '')[:200],
                    'location': resp.headers.get('Location', '')[:200],
                }
                logger.error(f"SharePoint 401 for {self.site_url}: "
                             f"WWW-Authenticate={www_auth[:200]}, "
                             f"Server={resp.headers.get('Server', '?')}, "
                             f"X-MS-Diagnostics={resp.headers.get('X-MS-Diagnostics', '?')[:200]}")

                # v6.0.8: Enhanced auth hint with actionable guidance (no config editing required)
                auth_hint = ''
                is_online = self._is_sharepoint_online
                if 'bearer' in www_auth.lower():
                    auth_hint = ' Server requires OAuth2/Bearer token (modern auth).'
                elif 'negotiate' in www_auth.lower() or 'ntlm' in www_auth.lower():
                    auth_hint = ' Server accepts Negotiate/NTLM but credentials were rejected — check domain trust.'
                elif not www_auth and is_online:
                    auth_hint = (' SharePoint Online has disabled legacy auth (NTLM/Negotiate) as of Feb 2026. '
                                 'This site requires OAuth 2.0 modern authentication via MSAL.')
                elif not www_auth:
                    auth_hint = ' Server sent no WWW-Authenticate header — may require pre-authentication or modern auth.'

                # v5.9.43: Try fresh session as auth retry before giving up
                try:
                    logger.info("SharePoint 401: Trying fresh SSO session...")
                    self._create_fresh_session()

                    # v6.0.5: On fresh session retry, try preemptive token again
                    retry_headers = {}
                    if self._preemptive_token:
                        retry_headers['Authorization'] = f'Negotiate {self._preemptive_token}'
                        logger.info("SharePoint 401: Fresh session retry with preemptive Negotiate token")
                    retry_resp = self.session.get(
                        f"{self.site_url}/_api/web",
                        timeout=self.timeout,
                        verify=self.ssl_verify,
                        headers=retry_headers if retry_headers else None,
                    )
                    if retry_resp.status_code == 200:
                        try:
                            data = retry_resp.json()
                            d = data.get('d', data)
                            title = d.get('Title', 'Unknown')
                            url = d.get('Url', self.site_url)
                            return {
                                'success': True,
                                'title': title,
                                'url': url,
                                'auth_method': self.auth_method,
                                'message': f'Connected to "{title}" via {self.auth_method} (fresh session retry)',
                                'status_code': 200,
                            }
                        except (ValueError, KeyError):
                            pass

                    # v6.0.5: If fresh SSO also failed AND we have OAuth, try that
                    if self._oauth_token:
                        logger.info("SharePoint 401: SSO retries exhausted — trying OAuth Bearer token")
                        oauth_resp = self.session.get(
                            f"{self.site_url}/_api/web",
                            timeout=self.timeout,
                            verify=self.ssl_verify,
                            headers={'Authorization': f'Bearer {self._oauth_token}'},
                        )
                        if oauth_resp.status_code == 200:
                            try:
                                data = oauth_resp.json()
                                d = data.get('d', data)
                                title = d.get('Title', 'Unknown')
                                url = d.get('Url', self.site_url)
                                # OAuth worked — switch to it as primary auth method
                                self.auth_method = 'oauth'
                                self.session.auth = None  # Remove SSO handler
                                self.session.headers['Authorization'] = f'Bearer {self._oauth_token}'
                                logger.info(f"SharePoint: Switched to OAuth auth — SSO not supported by this server")
                                return {
                                    'success': True,
                                    'title': title,
                                    'url': url,
                                    'auth_method': 'oauth',
                                    'message': f'Connected to "{title}" via OAuth 2.0 (modern auth)',
                                    'status_code': 200,
                                }
                            except (ValueError, KeyError):
                                pass

                except Exception as retry_e:
                    logger.debug(f"SharePoint 401 fresh session retry failed: {retry_e}")

                # v6.0.8: Include MSAL availability in diagnostics (zero-config — auto-detects from URL)
                msal_note = ''
                if not MSAL_AVAILABLE:
                    msal_note = ' MSAL not installed — install msal package for modern auth support.'
                elif not _get_oauth_config() and not _auto_detect_oauth_config(self.site_url):
                    msal_note = ' MSAL available but could not auto-detect tenant from URL.'
                elif MSAL_AVAILABLE:
                    msal_note = ' MSAL available — OAuth token acquisition may have failed (check network/domain trust).'

                return {
                    'success': False,
                    'title': '',
                    'url': self.site_url,
                    'auth_method': self.auth_method,
                    'message': f'Authentication failed (401) — Windows SSO credentials not accepted.{auth_hint}{msal_note}',
                    'status_code': 401,
                    'diagnostics': resp_headers_diag,
                    'is_sharepoint_online': is_online,
                    'msal_available': MSAL_AVAILABLE,
                    'oauth_configured': (_get_oauth_config() or _auto_detect_oauth_config(self.site_url)) is not None,
                    'preemptive_attempted': self._preemptive_token is not None,
                }

            elif resp.status_code == 403:
                return {
                    'success': False,
                    'title': '',
                    'url': self.site_url,
                    'auth_method': self.auth_method,
                    'message': f'Access denied (403) — you may not have permission to this site',
                    'status_code': 403,
                }

            else:
                return {
                    'success': False,
                    'title': '',
                    'url': self.site_url,
                    'auth_method': self.auth_method,
                    'message': f'Unexpected response: HTTP {resp.status_code}',
                    'status_code': resp.status_code,
                }

        except requests.exceptions.SSLError as e:
            # v5.9.35: SSL error that persisted even after verify=False fallback
            logger.error(f"SharePoint SSLError for {self.site_url}: {str(e)[:300]}")
            self._last_error_detail = str(e)[:500]
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'ssl_bypassed': self._ssl_fallback_used,
                'message': f'SSL certificate error — corporate CA not trusted. Details: {str(e)[:150]}',
                'status_code': 0,
                'error_category': 'ssl',
            }
        except requests.exceptions.ConnectionError as e:
            # v5.9.38: Enhanced error diagnostics with categorized messages
            err_str = str(e)
            err_lower = err_str.lower()

            # Log the full error for server-side diagnosis
            logger.error(f"SharePoint ConnectionError for {self.site_url}: {err_str[:500]}")
            self._last_error_detail = err_str[:500]

            if any(kw in err_lower for kw in ['ssl', 'certificate', 'handshake', 'tls']):
                detail = 'SSL/certificate issue — corporate CA certificate may not be trusted by Python'
            elif 'name or service not known' in err_lower or 'getaddrinfo' in err_lower:
                detail = 'DNS resolution failed — check if VPN is connected and SharePoint URL is correct'
            elif 'connection refused' in err_lower:
                detail = 'Connection refused — SharePoint server may be blocking this connection'
            elif 'timed out' in err_lower or 'timeout' in err_lower:
                detail = f'Connection timed out — server may be slow or network is blocking the connection'
            elif 'proxy' in err_lower:
                detail = 'Proxy error — corporate proxy may be blocking the connection'
            elif 'reset by peer' in err_lower or 'broken pipe' in err_lower:
                detail = 'Connection reset — server actively rejected the connection'
            elif 'max retries' in err_lower:
                # Extract the inner reason from urllib3's MaxRetryError
                import re
                inner = re.search(r"Caused by (\w+Error)\(([^)]{0,200})\)", err_str)
                if inner:
                    detail = f'Connection failed after retries — {inner.group(1)}: {inner.group(2)[:100]}'
                else:
                    detail = 'Connection failed after multiple retries — check VPN and URL'
            else:
                detail = 'Cannot reach server — check VPN/network connection and URL'

            # v5.9.38: Include auth method in message for diagnostics
            auth_note = f' [auth: {self.auth_method}]' if self.auth_method != 'negotiate' else ''
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'{detail}{auth_note}. Error: {err_str[:150]}',
                'status_code': 0,
                'error_category': 'connection',
            }
        except requests.exceptions.Timeout:
            logger.error(f"SharePoint Timeout for {self.site_url} after {self.timeout}s")
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'Connection timed out after {self.timeout}s — server may be slow or blocked by firewall',
                'status_code': 0,
                'error_category': 'timeout',
            }
        except Exception as e:
            logger.error(f"SharePoint unexpected error for {self.site_url}: {type(e).__name__}: {e}")
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'Connection error ({type(e).__name__}): {str(e)[:200]}',
                'status_code': 0,
                'error_category': 'unknown',
            }

    def connect_and_discover(self, library_path: str = '', recursive: bool = True, max_files: int = 500) -> Dict[str, Any]:
        """
        v5.9.38: Combined test + auto-detect + discover in one call.
        Reduces the multi-step flow to a single operation.

        Returns:
            {
                'success': bool,
                'title': str,
                'auth_method': str,
                'library_path': str,
                'files': list,
                'message': str,
                'ssl_fallback': bool,
            }
        """
        # Step 1: Test connection
        probe = self.test_connection()
        if not probe['success']:
            return {
                'success': False,
                'title': '',
                'auth_method': self.auth_method,
                'library_path': '',
                'files': [],
                'message': probe.get('message', 'Connection failed'),
                'ssl_fallback': self._ssl_fallback_used,
                'error_category': probe.get('error_category', 'connection'),
            }

        title = probe.get('title', '')

        # Step 2: Resolve library path
        # Priority: provided path (from URL parse or user) → validate it → auto-detect
        if library_path:
            # Validate the URL-parsed path actually exists
            if not self.validate_folder_path(library_path):
                logger.info(f"SharePoint URL path '{library_path}' not found as folder, trying auto-detect")
                # The URL path might be the library root — try trimming subdirectories
                parts = library_path.rstrip('/').split('/')
                found = False
                for i in range(len(parts), 2, -1):
                    candidate = '/'.join(parts[:i])
                    if self.validate_folder_path(candidate):
                        library_path = candidate
                        found = True
                        logger.info(f"SharePoint validated truncated path: {library_path}")
                        break
                if not found:
                    logger.info(f"SharePoint URL path not valid, falling back to auto-detect")
                    library_path = ''

        if not library_path:
            try:
                detected = self.auto_detect_library_path()
                if detected:
                    library_path = detected
                    logger.info(f"SharePoint auto-detected library: {library_path}")
            except Exception as e:
                logger.debug(f"SharePoint library auto-detect failed: {e}")

        if not library_path:
            return {
                'success': True,
                'title': title,
                'auth_method': self.auth_method,
                'library_path': '',
                'files': [],
                'message': f'Connected to "{title}" but could not detect document library. '
                           'Please enter the library path (e.g., /sites/MyTeam/Shared Documents)',
                'ssl_fallback': self._ssl_fallback_used,
            }

        # Step 2b: Detect subsites in the library path (v6.1.9)
        try:
            subweb_url = self._detect_subweb(library_path)
            if subweb_url:
                old_site = self.site_url
                self.site_url = subweb_url
                logger.info(
                    f'[SharePoint] *** SUBWEB RE-ROUTE: site_url changed from '
                    f'"{old_site}" to "{self.site_url}" ***'
                )
        except Exception as e:
            logger.warning(f'[SharePoint] Subweb detection failed (non-fatal): {e}')

        # Step 3: Discover files
        try:
            files = self.list_files(library_path, recursive=recursive, max_files=max_files)
        except Exception as e:
            logger.error(f"SharePoint discovery error: {e}")
            return {
                'success': True,  # Connection worked, discovery failed
                'title': title,
                'auth_method': self.auth_method,
                'library_path': library_path,
                'files': [],
                'message': f'Connected to "{title}" but failed to list files: {str(e)[:200]}',
                'ssl_fallback': self._ssl_fallback_used,
            }

        return {
            'success': True,
            'title': title,
            'auth_method': self.auth_method,
            'library_path': library_path,
            'files': files,
            'message': f'Connected to "{title}" — found {len(files)} document(s)',
            'ssl_fallback': self._ssl_fallback_used,
        }

    def _detect_subweb(self, library_path: str) -> Optional[str]:
        """
        v6.1.9: Detect if the library_path contains a SharePoint subsite (sub-web).

        Same logic as HeadlessSPConnector._detect_subweb but uses requests.Session
        instead of page.evaluate for the probe.

        See HeadlessSPConnector._detect_subweb for full documentation.
        """
        parsed = urlparse(self.site_url)
        current_site_path = parsed.path.rstrip('/')
        lib_path = library_path.rstrip('/')

        if not lib_path.lower().startswith(current_site_path.lower()):
            logger.info(f'[SharePoint] _detect_subweb: library_path does not start with site_path — skipping')
            return None

        remainder = lib_path[len(current_site_path):].strip('/')
        parts = remainder.split('/')
        logger.info(f'[SharePoint] _detect_subweb: checking {len(parts)} path segments: {parts}')

        if len(parts) <= 1:
            logger.info(f'[SharePoint] _detect_subweb: only 1 segment — library name, no subweb possible')
            return None

        for i in range(len(parts) - 1, 0, -1):
            candidate_path = current_site_path + '/' + '/'.join(parts[:i])
            candidate_url = f'{parsed.scheme}://{parsed.netloc}{candidate_path}'

            logger.info(f'[SharePoint] _detect_subweb: probing "{candidate_path}" as potential subweb...')

            try:
                resp = self.session.get(
                    f'{candidate_url}/_api/web?$select=Title,Url',
                    timeout=self.timeout,
                    verify=self.ssl_verify,
                    headers={'Accept': 'application/json;odata=verbose'},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    web_title = data.get('d', {}).get('Title', '?')
                    web_url = data.get('d', {}).get('Url', candidate_url)
                    logger.info(
                        f'[SharePoint] _detect_subweb: ✓ SUBWEB FOUND at "{candidate_path}" '
                        f'(Title="{web_title}", Url="{web_url}")'
                    )
                    return candidate_url
                else:
                    logger.info(f'[SharePoint] _detect_subweb: ✗ "{candidate_path}" not a subweb (HTTP {resp.status_code})')
            except Exception as e:
                logger.debug(f'[SharePoint] _detect_subweb: probe error for "{candidate_path}": {e}')
                continue

        logger.info(f'[SharePoint] _detect_subweb: no subwebs found')
        return None

    def auto_detect_library_path(self) -> Optional[str]:
        """
        v5.9.42: Enhanced auto-detect — tries 3 strategies:
        1. Query SharePoint Lists API to discover ALL document libraries
        2. Probe common library names (Shared Documents, Documents)
        3. Fall back to None (caller should use URL-parsed path)

        Returns the server-relative path if found, or None.
        """
        parsed = urlparse(self.site_url)
        site_path = parsed.path.rstrip('/')  # e.g., /sites/MyTeam

        # Strategy 1: Query Lists API for all document libraries
        try:
            lists_url = (
                f"{self.site_url}/_api/web/Lists"
                f"?$filter=BaseTemplate eq 101 and Hidden eq false"
                f"&$select=Title,RootFolder/ServerRelativeUrl"
                f"&$expand=RootFolder"
            )
            resp = self.session.get(
                lists_url,
                timeout=self.timeout,
                verify=self.ssl_verify,
                headers={**self.session.headers, 'Accept': 'application/json;odata=verbose'}
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('d', {}).get('results', [])
                if results:
                    # Return the first document library (usually "Shared Documents" or "Documents")
                    for lib in results:
                        root = lib.get('RootFolder', {})
                        srv_url = root.get('ServerRelativeUrl', '')
                        if srv_url:
                            logger.info(f"SharePoint Lists API detected library: {srv_url} ({lib.get('Title', '')})")
                            return srv_url
        except Exception as e:
            logger.debug(f"SharePoint Lists API query failed: {e}")

        # Strategy 2: Probe common library names
        for lib_name in self.DEFAULT_LIBRARIES:
            test_path = f"{site_path}/{lib_name}"
            encoded = self._encode_sp_path(test_path)

            try:
                resp = self.session.get(
                    f"{self.site_url}/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded}')",
                    timeout=self.timeout,
                    verify=self.ssl_verify,
                )
                if resp.status_code == 200:
                    logger.info(f"SharePoint probe detected library: {test_path}")
                    return test_path
            except Exception as e:
                logger.debug(f"SharePoint library probe failed for {lib_name}: {e}")
                continue

        logger.info(f"SharePoint: No library found via Lists API or probing")
        return None

    def validate_folder_path(self, folder_path: str) -> bool:
        """
        v5.9.42: Check if a folder path exists on this SharePoint site.
        Used to validate URL-extracted paths before scanning.

        v6.0.3: Uses GetFolderByServerRelativePath(decodedUrl=...) API with
        percent-encoded path. The decodedUrl parameter auto-decodes %26→&,
        %23→#, etc., solving the T&E/R&D folder name issue. Falls back to
        legacy GetFolderByServerRelativeUrl for older SharePoint versions.

        v6.0.6: Uses _api_get() instead of raw session.get() so that
        preemptive SSPI tokens and OAuth Bearer tokens are included.
        Without this, validate_folder_path always got 401 on SharePoint
        Online where legacy auth is disabled.

        Reference: https://learn.microsoft.com/en-us/sharepoint/dev/
        solution-guidance/supporting-and-in-file-and-folder-with-the-resourcepath-api
        """
        encoded = self._encode_sp_path(folder_path)

        # Strategy 1: Modern ResourcePath API (recommended by Microsoft)
        try:
            resp = self._api_get(
                f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded}')"
            )
            if resp.status_code == 200:
                return True
        except Exception:
            pass

        # Strategy 2: Legacy API fallback for older SharePoint versions
        # Uses un-encoded path (literal chars) since this API auto-detects encoding
        try:
            legacy_encoded = quote(folder_path, safe='/:')
            resp = self._api_get(
                f"/_api/web/GetFolderByServerRelativeUrl('{legacy_encoded}')"
            )
            if resp.status_code == 200:
                return True
        except Exception:
            pass

        return False

    def list_files(
        self,
        folder_path: str,
        recursive: bool = True,
        max_files: int = 500
    ) -> List[Dict[str, Any]]:
        """
        List documents in a SharePoint folder via REST API.

        Args:
            folder_path: Server-relative path to the folder
                (e.g., /sites/MyTeam/Shared Documents/Specs)
            recursive: Whether to recurse into subfolders
            max_files: Maximum number of files to return

        Returns:
            List of file dicts with: name, server_relative_url, size, modified,
            extension, folder (relative path within the library)
        """
        files = []
        self._list_files_recursive(folder_path, files, recursive, max_files, depth=0)
        return files[:max_files]

    def _list_items_fallback_rest(
        self,
        folder_path: str,
        files: List[Dict],
        max_files: int,
    ):
        """
        v6.1.8: Fallback file discovery using the List Items API (REST connector version).

        Same logic as HeadlessSPConnector._list_items_fallback but using requests-based
        _api_get which returns requests.Response objects.
        """
        logger.info(f'[SharePoint] *** List Items API fallback for "{folder_path}" ***')

        # Strategy 1: Try GetList(folder_path)/Items
        encoded = self._encode_sp_path(folder_path)
        try:
            resp = self._api_get(
                f"/_api/web/GetList('{encoded}')/Items"
                f"?$select=FileLeafRef,FileRef,File_x0020_Size,Modified,FSObjType"
                f"&$expand=File"
                f"&$filter=FSObjType eq 0"
                f"&$top={max_files}"
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('d', {}).get('results', [])
                logger.info(f'[SharePoint] GetList Items returned {len(results)} items')
                self._parse_list_items_rest(results, files, max_files, folder_path)
                if files:
                    logger.info(f'[SharePoint] List Items fallback found {len(files)} supported files')
                    return
        except Exception as e:
            logger.debug(f'[SharePoint] GetList Items failed: {e}')

        # Strategy 2: Walk up the path to find the library root
        parts = folder_path.rstrip('/').split('/')
        logger.info(f'[SharePoint] GetList failed for full path, walking up: {parts}')

        for i in range(len(parts) - 1, 3, -1):
            candidate = '/'.join(parts[:i])
            candidate_encoded = self._encode_sp_path(candidate)
            logger.info(f'[SharePoint] Trying parent as library root: "{candidate}"')

            try:
                resp = self._api_get(
                    f"/_api/web/GetList('{candidate_encoded}')?$select=Title,Id,ItemCount"
                )
                if resp.status_code != 200:
                    continue

                list_data = resp.json()
                list_title = list_data.get('d', {}).get('Title', '?')
                logger.info(f'[SharePoint] Found library root: "{candidate}" (Title="{list_title}")')

                resp = self._api_get(
                    f"/_api/web/GetList('{candidate_encoded}')/Items"
                    f"?$select=FileLeafRef,FileRef,File_x0020_Size,Modified,FSObjType,FileDirRef"
                    f"&$expand=File"
                    f"&$filter=FSObjType eq 0"
                    f"&$top={max_files}"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get('d', {}).get('results', [])
                    logger.info(f'[SharePoint] Library root Items returned {len(results)} total items')

                    target_lower = folder_path.rstrip('/').lower()
                    filtered = [
                        item for item in results
                        if (item.get('FileDirRef') or '').lower().startswith(target_lower)
                        or os.path.dirname(item.get('FileRef', '')).lower().startswith(target_lower)
                    ]
                    logger.info(f'[SharePoint] After filtering to "{folder_path}": {len(filtered)} items')

                    self._parse_list_items_rest(filtered, files, max_files, folder_path)
                    if files:
                        logger.info(f'[SharePoint] List Items fallback (via parent) found {len(files)} supported files')
                        return
            except Exception as e:
                logger.debug(f'[SharePoint] Parent probe "{candidate}" failed: {e}')

    def _parse_list_items_rest(
        self,
        items: List[Dict],
        files: List[Dict],
        max_files: int,
        folder_path: str,
    ):
        """Parse list items into file dicts (REST connector version)."""
        for item in items:
            if len(files) >= max_files:
                break

            file_data = item.get('File', {}) or {}
            name = file_data.get('Name') or item.get('FileLeafRef', '')
            if not name:
                continue

            ext = os.path.splitext(name)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            server_rel_url = file_data.get('ServerRelativeUrl') or item.get('FileRef', '')
            size = file_data.get('Length') or item.get('File_x0020_Size') or 0
            modified = file_data.get('TimeLastModified') or item.get('Modified', '')

            files.append({
                'name': name,
                'filename': name,
                'server_relative_url': server_rel_url,
                'size': int(size) if size else 0,
                'modified': modified,
                'extension': ext,
                'folder': os.path.dirname(server_rel_url) if server_rel_url else folder_path,
                'relative_path': server_rel_url,
            })

    def _list_files_recursive(
        self,
        folder_path: str,
        files: List[Dict],
        recursive: bool,
        max_files: int,
        depth: int = 0
    ):
        """Recursively list files in a SharePoint folder."""
        if len(files) >= max_files or depth > 10:
            return

        # v6.0.3: Use ResourcePath API (decodedUrl) with percent-encoded path.
        # The decodedUrl parameter auto-decodes %26→&, %23→# etc.
        encoded_path = self._encode_sp_path(folder_path)

        files_found = 0
        try:
            # Get files in this folder
            resp = self._api_get(
                f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded_path}')/Files"
                f"?$select=Name,ServerRelativeUrl,Length,TimeLastModified"
                f"&$top={max_files - len(files)}"
            )

            if resp.status_code == 200:
                data = resp.json()
                results = data.get('d', {}).get('results', [])
                files_found = len(results)

                for item in results:
                    if len(files) >= max_files:
                        break

                    name = item.get('Name', '')
                    ext = os.path.splitext(name)[1].lower()

                    # Only include AEGIS-supported document types
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue

                    server_rel_url = item.get('ServerRelativeUrl', '')

                    files.append({
                        'name': name,
                        'filename': name,
                        'server_relative_url': server_rel_url,
                        'size': int(item.get('Length', 0)),
                        'modified': item.get('TimeLastModified', ''),
                        'extension': ext,
                        'folder': os.path.dirname(server_rel_url),
                        'relative_path': server_rel_url,
                    })

            elif resp.status_code in (401, 403):
                logger.warning(f"SharePoint: Access denied to {folder_path}")
                return
            else:
                logger.warning(f"SharePoint: Failed to list {folder_path}: HTTP {resp.status_code}")
                return

        except Exception as e:
            logger.error(f"SharePoint: Error listing {folder_path}: {e}")
            return

        # Recurse into subfolders
        folders_found = 0
        if recursive and len(files) < max_files:
            try:
                resp = self._api_get(
                    f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded_path}')/Folders"
                    f"?$select=Name,ServerRelativeUrl,ItemCount"
                )

                if resp.status_code == 200:
                    data = resp.json()
                    folders = data.get('d', {}).get('results', [])
                    folders_found = len(folders)

                    for subfolder in folders:
                        if len(files) >= max_files:
                            break

                        subfolder_name = subfolder.get('Name', '')
                        # Skip system folders
                        if subfolder_name.startswith('_') or subfolder_name == 'Forms':
                            continue

                        subfolder_url = subfolder.get('ServerRelativeUrl', '')
                        if subfolder_url:
                            self._list_files_recursive(
                                subfolder_url, files, recursive, max_files, depth + 1
                            )

            except Exception as e:
                logger.error(f"SharePoint: Error listing subfolders of {folder_path}: {e}")

        # v6.1.8: List Items API fallback — same as HeadlessSP version
        if depth == 0 and files_found == 0 and folders_found == 0 and len(files) == 0:
            logger.info(
                f'[SharePoint] /Files and /Folders both empty at root — '
                f'trying List Items API fallback for "{folder_path}"'
            )
            self._list_items_fallback_rest(folder_path, files, max_files)

    def _create_download_session(self):
        """
        Create a fresh requests.Session for a single file download.

        v6.0.3: NTLM/Negotiate auth is connection-specific — the multi-step
        challenge→response handshake requires the same TCP connection. When
        multiple threads share self.session during batch scans (ThreadPoolExecutor
        with 3 workers), the NTLM handshake state gets corrupted, causing 401
        errors. Each download must use its own session for a clean handshake.
        (Lesson 134, same pattern as hyperlink_validator._retry_with_fresh_auth)
        """
        fresh = requests.Session()
        fresh.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'AEGIS/6.0.5 SharePointConnector',
        })

        # v6.0.5: Use OAuth if that's our primary auth method
        if self.auth_method == 'oauth' and self._oauth_token:
            fresh.headers['Authorization'] = f'Bearer {self._oauth_token}'
        elif WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
            try:
                fresh.auth = HttpNegotiateAuth()
            except Exception as e:
                logger.warning(f"SharePoint: Download session SSO setup failed: {e}")
            # v6.0.5: Also attach preemptive token for first request
            if self._preemptive_token:
                fresh.headers['Authorization'] = f'Negotiate {self._preemptive_token}'
        return fresh

    def _download_with_session(self, session, encoded_url, dest_path):
        """
        Execute the actual download using the given session.

        Returns:
            {'success': bool, 'path': str, 'size': int, 'message': str, 'status_code': int}
        """
        url = f"{self.site_url}/_api/web/GetFileByServerRelativePath(decodedUrl='{encoded_url}')/$value"
        resp = session.get(
            url,
            timeout=self.timeout,
            verify=self.ssl_verify,
            stream=True,
            allow_redirects=True,
        )

        if resp.status_code == 200:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            total_bytes = 0
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
            return {
                'success': True,
                'path': dest_path,
                'size': total_bytes,
                'message': f'Downloaded {total_bytes:,} bytes',
                'status_code': 200,
            }
        else:
            return {
                'success': False,
                'path': dest_path,
                'size': 0,
                'message': '',
                'status_code': resp.status_code,
            }

    def download_file(self, server_relative_url: str, dest_path: str) -> Dict[str, Any]:
        """
        Download a single file from SharePoint.

        Uses /_api/web/GetFileByServerRelativePath(decodedUrl='...')/$value for
        binary content. The decodedUrl parameter auto-decodes percent-encoded
        special characters (%26→&, %23→#) in folder/file names.

        v6.0.3: Each download creates its own requests.Session for thread-safe
        NTLM/Negotiate auth. Shared sessions corrupt the multi-step handshake
        when used across ThreadPoolExecutor workers during batch scans (Lesson 134).
        401/403 errors now retry with a second fresh session before giving up.

        Args:
            server_relative_url: Server-relative URL of the file
            dest_path: Local path to save the downloaded file

        Returns:
            {'success': bool, 'path': str, 'size': int, 'message': str}
        """
        # v6.0.3: Percent-encode for ResourcePath API (decodedUrl auto-decodes)
        encoded_url = self._encode_sp_path(server_relative_url)

        # v6.0.3: Use a fresh session per download for thread-safe NTLM auth
        session = self._create_download_session()

        try:
            result = self._download_with_session(session, encoded_url, dest_path)

            if result['success']:
                return result

            status_code = result['status_code']

            if status_code in (401, 403):
                # v6.0.3: Retry once with a brand-new session — NTLM handshake
                # may have been corrupted by thread contention or session reuse.
                # Same pattern as hyperlink_validator._retry_with_fresh_auth (Lesson 75)
                logger.info(f"SharePoint {status_code} for {server_relative_url} — retrying with fresh auth session")
                try:
                    session.close()
                except Exception:
                    pass

                try:
                    retry_session = self._create_download_session()
                    retry_result = self._download_with_session(retry_session, encoded_url, dest_path)

                    if retry_result['success']:
                        retry_result['message'] += f' (retry after {status_code})'
                        return retry_result

                    retry_session.close()
                    logger.warning(f"SharePoint auth retry also failed ({retry_result['status_code']}) for {server_relative_url}")
                except Exception as retry_e:
                    logger.debug(f"SharePoint {status_code} retry error: {retry_e}")

                return {
                    'success': False,
                    'path': dest_path,
                    'size': 0,
                    'message': f'Access denied ({status_code}) — retry also failed',
                }

            elif status_code == 404:
                # v5.9.41: Retry once with fresh session — SP returns transient 404s
                logger.info(f"SharePoint 404 for {server_relative_url} — retrying with fresh session")
                try:
                    session.close()
                except Exception:
                    pass

                try:
                    retry_session = self._create_download_session()
                    retry_result = self._download_with_session(retry_session, encoded_url, dest_path)

                    if retry_result['success']:
                        retry_result['message'] += ' (retry after transient 404)'
                        return retry_result

                    retry_session.close()
                except Exception as retry_e:
                    logger.debug(f"SharePoint 404 retry also failed: {retry_e}")

                return {
                    'success': False,
                    'path': dest_path,
                    'size': 0,
                    'message': f'File not found (404)',
                }
            else:
                return {
                    'success': False,
                    'path': dest_path,
                    'size': 0,
                    'message': f'Download failed: HTTP {status_code}',
                }

        except Exception as e:
            return {
                'success': False,
                'path': dest_path,
                'size': 0,
                'message': f'Download error: {str(e)[:200]}',
            }
        finally:
            try:
                session.close()
            except Exception:
                pass

    def get_file_type_breakdown(self, files: List[Dict]) -> Dict[str, int]:
        """Get count of files by extension."""
        breakdown = {}
        for f in files:
            ext = f.get('extension', 'unknown')
            breakdown[ext] = breakdown.get(ext, 0) + 1
        return breakdown

    def close(self):
        """Close the HTTP session."""
        try:
            self.session.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ============================================================================
# HeadlessSPConnector — Playwright-based SharePoint access via Windows SSO
# ============================================================================

class HeadlessSPConnector:
    """
    v6.1.3: Headless browser SharePoint connector.

    Uses Playwright + Windows SSO to access SharePoint REST API endpoints
    through an authenticated browser session. Bypasses MSAL/OAuth entirely —
    uses the same Windows credentials that Chrome uses.

    This is the fallback connector when REST API auth fails (e.g., AADSTS65002
    on GCC High where first-party client IDs are blocked).

    Architecture:
        - Launches headless Chromium with --auth-server-allowlist for automatic SSO
        - Navigates to SharePoint site to establish authenticated session
        - Uses page.evaluate(fetch(...)) to call SharePoint REST API from
          the browser's authenticated JavaScript context
        - Returns identical data formats to SharePointConnector for polymorphism

    Thread safety:
        - Playwright sync API is single-threaded
        - All browser operations must happen on the same thread
        - Batch scans should use max_workers=1 when using this connector
    """

    SUPPORTED_EXTENSIONS = {'.docx', '.pdf', '.doc'}

    # Same resource types blocked as headless_validator.py for speed
    BLOCKED_RESOURCE_TYPES = {'image', 'stylesheet', 'font', 'media', 'imageset'}

    def __init__(self, site_url: str, timeout: int = 45):
        self.site_url = site_url.rstrip('/')
        self.timeout = timeout * 1000  # Playwright uses milliseconds
        self.auth_method = 'headless_browser'
        self._ssl_fallback_used = False

        # Playwright objects — lazy-initialized
        # v6.1.6: Uses launchPersistentContext instead of launch+new_context
        # so that ambient auth (NTLM/Negotiate) is enabled (regular profile,
        # not incognito-like). Chrome 81+ disables ambient auth in incognito.
        self._playwright = None
        self._browser = None       # Not used with persistent context, kept for close()
        self._context = None       # The persistent browser context
        self._page = None
        self._authenticated = False
        self._user_data_dir = None  # Temp dir for persistent context

        # Import CORP_AUTH_DOMAINS from headless_validator if available
        try:
            from hyperlink_validator.headless_validator import CORP_AUTH_DOMAINS
            self._corp_domains = CORP_AUTH_DOMAINS
        except ImportError:
            self._corp_domains = [
                '*.myngc.com', '*.northgrum.com', '*.northropgrumman.com',
                '*.ngc.sharepoint.us', '*.sharepoint.com', '*.sharepoint.us',
                '*.mil', '*.gov',
            ]

        logger.info(f'[HeadlessSP] Connector created for {self.site_url}')

    def _ensure_browser(self):
        """
        Lazy-start Playwright browser with SSO auth passthrough.

        v6.1.6: THREE critical changes from v6.1.3-v6.1.5:

        1. Uses launchPersistentContext() instead of launch() + new_context().
           Chrome 81+ disabled ambient auth (NTLM/Negotiate) in incognito-like
           profiles. Playwright's new_context() creates ephemeral contexts that
           behave like incognito — ambient credentials are NOT passed.
           launchPersistentContext() with a user_data_dir creates a "regular"
           profile where ambient auth IS enabled by default.
           (Source: Playwright issue #1707, Chromium issue #458369)

        2. Tries channel='msedge' first (not 'chrome'). Microsoft Edge ships
           with Windows 10/11 and is always available. When using a channel,
           Playwright uses the REAL browser binary with the NEW headless mode
           (full browser, full SSPI/Negotiate support). The bundled
           chrome-headless-shell is a stripped-down binary that may lack full
           SSPI auth integration.
           (Source: Chromium bug #741872, Chrome docs on headless-shell)

        3. Adds --enable-features=EnableAmbientAuthenticationInIncognito as
           belt-and-suspenders — explicitly enables ambient auth even if the
           profile is somehow treated as private/incognito.
        """
        if self._context is not None:
            return

        if not HEADLESS_SP_AVAILABLE:
            raise RuntimeError('Playwright is not installed — headless SP connector unavailable')

        logger.info('[HeadlessSP] Starting Playwright browser...')
        self._playwright = _sp_sync_playwright().start()

        # Build auth allowlist — deduplicate domains
        _idp_extras = [
            '*.microsoftonline.com', '*.microsoftonline.us',
            '*.login.microsoftonline.com', '*.login.microsoftonline.us',
            '*.windows.net', '*.login.windows.net',
            '*.adfs.*',
        ]
        _seen = set()
        _auth_domains = []
        for d in list(self._corp_domains) + _idp_extras:
            if d not in _seen:
                _seen.add(d)
                _auth_domains.append(d)
        allowlist = ','.join(_auth_domains)
        logger.info(f'[HeadlessSP] Auth allowlist: {allowlist}')

        # v6.1.6: Common args for all browser channels
        base_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-gpu',
            f'--auth-server-allowlist={allowlist}',
            f'--auth-negotiate-delegate-allowlist={allowlist}',
            # v6.1.6: Enable ambient auth in private/incognito-like contexts
            '--enable-features=EnableAmbientAuthenticationInIncognito',
        ]

        # v6.1.6: Create a temp user_data_dir for persistent context
        # This ensures the browser uses a "regular" profile (not incognito),
        # which enables ambient NTLM/Negotiate authentication by default.
        import tempfile
        self._user_data_dir = tempfile.mkdtemp(prefix='aegis_sp_browser_')
        logger.info(f'[HeadlessSP] User data dir: {self._user_data_dir}')

        # Common kwargs for launchPersistentContext
        _ctx_kwargs = dict(
            user_data_dir=self._user_data_dir,
            headless=True,
            args=base_args,
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
            ),
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            ignore_https_errors=True,
            locale='en-US',
            timezone_id='America/New_York',
            accept_downloads=True,
        )

        # v6.1.6: Try branded browsers first — they use the NEW headless mode
        # (full browser binary with full SSPI/Negotiate/Kerberos support).
        # The bundled chrome-headless-shell is stripped down and may lack auth.
        #
        # Priority: msedge (always on Win10/11) → chrome → bundled chromium
        _channels_to_try = [
            ('msedge', 'Microsoft Edge (new headless, full SSPI)'),
            ('chrome', 'Google Chrome (new headless, full SSPI)'),
            (None, 'Bundled Chromium (headless shell)'),
        ]

        for channel, desc in _channels_to_try:
            try:
                kwargs = dict(_ctx_kwargs)
                if channel:
                    kwargs['channel'] = channel
                self._context = self._playwright.chromium.launch_persistent_context(**kwargs)
                logger.info(f'[HeadlessSP] Browser started: {desc} with SSO allowlist')
                break
            except Exception as e:
                logger.info(f'[HeadlessSP] Channel {channel or "bundled"} failed: {str(e)[:100]}')
                self._context = None
                continue

        if self._context is None:
            raise RuntimeError(
                'Could not launch any browser for headless SP connector. '
                'Ensure Microsoft Edge or Chrome is installed, or run: '
                'python -m playwright install chromium'
            )

        # With persistent context, pages[0] is created automatically
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        # Block non-essential resources for speed
        def _handle_route(route):
            if route.request.resource_type in self.BLOCKED_RESOURCE_TYPES:
                route.abort()
            else:
                route.continue_()

        self._page.route('**/*', _handle_route)
        logger.info('[HeadlessSP] Browser context and page created')

    def _authenticate(self) -> Dict[str, Any]:
        """
        Establish an authenticated browser session with SharePoint.

        v6.1.4: Rewritten to handle federated SSO (Azure AD + ADFS) properly.

        SharePoint Online (GCC High) uses federated authentication:
            1. Browser navigates to SharePoint site
            2. SharePoint redirects to Azure AD (login.microsoftonline.us)
            3. Azure AD redirects to org's ADFS for Windows Integrated Auth
            4. ADFS authenticates via Negotiate/Kerberos (--auth-server-allowlist)
            5. ADFS returns SAML token → Azure AD → SharePoint cookie set

        The key insight: we navigate to the SITE HOMEPAGE (not /_api/web) and
        let the full redirect chain complete. Then we check where the browser
        ended up — if back on SharePoint, auth succeeded. Only if the browser
        is STILL on a login page after the full timeout does auth fail.

        Returns:
            {success: bool, title: str, message: str}
        """
        if self._authenticated:
            return {'success': True, 'title': '', 'message': 'Already authenticated'}

        self._ensure_browser()

        parsed = urlparse(self.site_url)
        sp_host = parsed.hostname or ''

        try:
            # Phase 1: Navigate to the site HOMEPAGE — triggers the full federated
            # SSO redirect chain (SharePoint → Azure AD → ADFS → back to SharePoint)
            # DO NOT navigate to /_api/web — that returns JSON and some auth flows
            # don't handle it correctly
            site_url = self.site_url
            logger.info(f'[HeadlessSP] Phase 1: Navigating to {site_url} (triggers SSO)')

            response = self._page.goto(
                site_url,
                timeout=self.timeout,
                wait_until='domcontentloaded',  # Don't wait for all resources
            )

            # Log the initial response and URL
            initial_url = self._page.url
            initial_status = response.status if response else 'None'
            logger.info(f'[HeadlessSP] Initial response: HTTP {initial_status}, URL: {initial_url[:200]}')

            # Phase 2: Wait for the federated SSO redirect chain to complete.
            # The browser will bounce through login.microsoftonline.us → ADFS → back.
            # We wait for the URL to return to a SharePoint domain, or timeout.
            final_url = self._page.url.lower()

            # If we're still on a login/auth page, wait for SSO to complete
            _login_patterns = [
                'login.microsoftonline', 'login.windows.net',
                '/adfs/', '/saml/', 'wa=wsignin', '/oauth2/',
            ]
            is_on_login = any(p in final_url for p in _login_patterns)

            if is_on_login:
                logger.info(f'[HeadlessSP] Phase 2: On login page, waiting for SSO redirect chain...')
                logger.info(f'[HeadlessSP]   Current URL: {final_url[:200]}')

                # Wait for the URL to change back to the SharePoint domain
                # The --auth-server-allowlist flag should auto-handle the Negotiate challenge
                try:
                    # Wait up to 30 seconds for the browser to land on the SP domain
                    self._page.wait_for_url(
                        f'**{sp_host}**',
                        timeout=30000,
                        wait_until='domcontentloaded',
                    )
                    final_url = self._page.url.lower()
                    logger.info(f'[HeadlessSP] SSO redirect completed — now at: {final_url[:200]}')
                except Exception as wait_err:
                    # Timeout or error waiting for redirect — check where we are now
                    final_url = self._page.url.lower()
                    logger.warning(
                        f'[HeadlessSP] SSO wait timeout/error: {str(wait_err)[:100]}. '
                        f'Current URL: {final_url[:200]}'
                    )

                    # If STILL on login page after waiting, SSO truly failed
                    still_on_login = any(p in final_url for p in _login_patterns)
                    if still_on_login:
                        # Check for ADFS login form — indicates Kerberos/Negotiate failed
                        page_content = ''
                        try:
                            page_content = self._page.content()[:2000]
                        except Exception:
                            pass

                        _has_password_field = (
                            'type="password"' in page_content
                            or 'passwordInput' in page_content
                            or 'loginButton' in page_content
                        )

                        if _has_password_field:
                            msg = (
                                'SSO redirect did not auto-authenticate — '
                                'landed on a login form with password field. '
                                'Windows Integrated Auth (Kerberos) may not be '
                                'configured for this ADFS server. '
                                f'Final URL: {final_url[:150]}'
                            )
                        else:
                            msg = (
                                'SSO redirect timed out — still on auth page after 30s. '
                                f'Final URL: {final_url[:150]}'
                            )
                        logger.error(f'[HeadlessSP] Auth failed: {msg}')
                        return {'success': False, 'title': '', 'message': msg}

            # Phase 3: We should be on the SharePoint site now.
            # Navigate to the REST API to verify authentication and get site title.
            logger.info(f'[HeadlessSP] Phase 3: Verifying auth via /_api/web')
            final_url = self._page.url.lower()

            # If we ended up on the SP site (even a redirect to a subpage), try API
            if sp_host in final_url or 'sharepoint' in final_url:
                # Use page.evaluate(fetch()) to call the API — this uses the
                # browser's authenticated session cookies
                try:
                    api_result = self._page.evaluate('''async (url) => {
                        try {
                            const resp = await fetch(url, {
                                method: 'GET',
                                headers: {
                                    'Accept': 'application/json;odata=verbose',
                                },
                                credentials: 'include',
                            });
                            if (resp.ok) {
                                const data = await resp.json();
                                return { success: true, status: resp.status, data: data };
                            }
                            return {
                                success: false,
                                status: resp.status,
                                error: await resp.text().catch(() => 'no body')
                            };
                        } catch (e) {
                            return { success: false, status: 0, error: e.message || String(e) };
                        }
                    }''', f'{self.site_url}/_api/web')

                    if api_result and api_result.get('success'):
                        data = api_result.get('data', {})
                        title = data.get('d', {}).get('Title', '')
                        self._authenticated = True
                        logger.info(f'[HeadlessSP] Authenticated successfully — site: "{title}"')
                        return {
                            'success': True,
                            'title': title,
                            'message': f'Authenticated to "{title}" via headless browser SSO',
                        }
                    else:
                        api_status = api_result.get('status', 0) if api_result else 0
                        api_error = (api_result.get('error', '')[:200]) if api_result else ''
                        logger.warning(
                            f'[HeadlessSP] API check returned HTTP {api_status}: {api_error}'
                        )
                        # If we got a 401/403 from the API even though we're on SP,
                        # the session cookies may not have been set correctly
                        if api_status in (401, 403):
                            return {
                                'success': False,
                                'title': '',
                                'message': (
                                    f'Reached SharePoint site but REST API returned HTTP {api_status}. '
                                    'The browser session may not have the correct auth cookies.'
                                ),
                            }
                        # For other errors, still mark as authenticated since we're on SP
                        self._authenticated = True
                        return {
                            'success': True,
                            'title': '',
                            'message': f'On SharePoint site (API check: HTTP {api_status})',
                        }

                except Exception as api_err:
                    logger.warning(f'[HeadlessSP] API verify exception: {api_err}')
                    # We're on the SP site, API call failed — still try to proceed
                    self._authenticated = True
                    return {
                        'success': True,
                        'title': '',
                        'message': 'On SharePoint site (API verify failed, will try anyway)',
                    }

            else:
                # Ended up somewhere unexpected
                logger.error(
                    f'[HeadlessSP] Ended up on unexpected URL: {final_url[:200]}'
                )
                return {
                    'success': False,
                    'title': '',
                    'message': (
                        f'Browser navigated to unexpected URL after auth flow: '
                        f'{final_url[:150]}'
                    ),
                }

        except Exception as e:
            err_msg = str(e)[:300]
            logger.error(f'[HeadlessSP] Auth exception: {err_msg}')

            # Check for common Playwright errors
            if 'timeout' in err_msg.lower():
                return {
                    'success': False,
                    'title': '',
                    'message': (
                        f'Navigation timed out after {self.timeout // 1000}s. '
                        'SharePoint or the auth server may be unreachable. '
                        f'Error: {err_msg[:150]}'
                    ),
                }

            return {
                'success': False,
                'title': '',
                'message': f'Browser navigation failed: {err_msg[:200]}',
            }

    def _api_get(self, endpoint: str) -> Optional[Dict]:
        """
        Call a SharePoint REST API endpoint via page.evaluate(fetch(...)).

        This executes a fetch() call within the browser's authenticated JavaScript
        context, so the request automatically includes the SSO credentials.

        Args:
            endpoint: REST API path, e.g., '/_api/web' or '/_api/web/GetFolderBy...'

        Returns:
            Parsed JSON response dict, or None on failure.
        """
        if not self._page:
            self._ensure_browser()

        # Build full URL if endpoint is relative
        if endpoint.startswith('/'):
            full_url = f'{self.site_url}{endpoint}'
        else:
            full_url = endpoint

        logger.debug(f'[HeadlessSP] _api_get: {full_url[:300]}')

        try:
            # Use page.evaluate to call fetch() in the browser context
            result = self._page.evaluate('''async (url) => {
                try {
                    const resp = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json;odata=verbose',
                            'Content-Type': 'application/json;odata=verbose',
                        },
                        credentials: 'include',
                    });
                    const status = resp.status;
                    if (status === 200 || status === 201) {
                        const data = await resp.json();
                        return { success: true, status: status, data: data };
                    } else {
                        const text = await resp.text().catch(() => '');
                        return { success: false, status: status, error: text.substring(0, 500) };
                    }
                } catch (e) {
                    return { success: false, status: 0, error: e.message || String(e) };
                }
            }''', full_url)

            if result and result.get('success'):
                return result.get('data')
            else:
                status = result.get('status', 0) if result else 0
                error = result.get('error', 'Unknown error') if result else 'evaluate returned None'
                logger.warning(f'[HeadlessSP] API GET {endpoint}: HTTP {status} — {error[:200]}')
                return None

        except Exception as e:
            logger.error(f'[HeadlessSP] API GET {endpoint} exception: {e}')
            return None

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection via headless browser SSO."""
        auth_result = self._authenticate()
        if not auth_result['success']:
            return {
                'success': False,
                'message': auth_result['message'],
                'auth_method': 'headless_browser',
            }

        # Try the REST API via evaluate
        data = self._api_get('/_api/web')
        if data:
            title = data.get('d', {}).get('Title', auth_result.get('title', ''))
            return {
                'success': True,
                'title': title,
                'auth_method': 'headless_browser',
                'message': f'Connected via headless browser (Windows SSO) — site: {title}',
            }
        else:
            # Auth succeeded but API call failed — maybe JSON didn't parse
            # Still return success if authenticate() worked
            return {
                'success': True,
                'title': auth_result.get('title', ''),
                'auth_method': 'headless_browser',
                'message': 'Connected via headless browser (Windows SSO)',
            }

    def validate_folder_path(self, folder_path: str) -> bool:
        """Check if a folder path exists on SharePoint."""
        encoded = SharePointConnector._encode_sp_path(folder_path)
        endpoint = (
            f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded}')"
            f"?$select=Name,ServerRelativeUrl,ItemCount"
        )
        logger.info(f'[HeadlessSP] validate_folder_path: "{folder_path}" → encoded: "{encoded}"')
        data = self._api_get(endpoint)
        if data:
            name = data.get('d', {}).get('Name', '?')
            item_count = data.get('d', {}).get('ItemCount', '?')
            logger.info(f'[HeadlessSP] validate_folder_path: ✓ FOUND — Name="{name}", ItemCount={item_count}')
        else:
            logger.info(f'[HeadlessSP] validate_folder_path: ✗ NOT FOUND')
        return data is not None

    def _detect_subweb(self, library_path: str) -> Optional[str]:
        """
        v6.1.9: Detect if the library_path contains a SharePoint subsite (sub-web).

        SharePoint has a hierarchy: Site Collection → Subsites → Libraries.
        The REST API (/_api/web/...) only operates within the CURRENT web context.
        If self.site_url is the parent site (e.g., /sites/AS-ENG) but the library
        lives under a subsite (e.g., /sites/AS-ENG/PAL/SITE), then ALL API calls
        go to the wrong web — GetList returns 500, /Files returns empty, etc.

        This method probes each path segment between the current site_url path and
        the library_path by calling /_api/web. If a segment responds successfully,
        it's a subweb and we need to re-route self.site_url.

        Example:
            site_url = https://ngc.sharepoint.us/sites/AS-ENG
            library_path = /sites/AS-ENG/PAL/SITE
            → probe /sites/AS-ENG/PAL/_api/web → SUCCESS (PAL is a subsite)
            → update site_url to https://ngc.sharepoint.us/sites/AS-ENG/PAL
            → now _api_get calls go to the correct web context

        Args:
            library_path: Server-relative path to the document library

        Returns:
            New site_url if a subweb was detected, or None if no subweb found
        """
        parsed = urlparse(self.site_url)
        current_site_path = parsed.path.rstrip('/')
        lib_path = library_path.rstrip('/')

        # Only search between the current site path and the library path
        # e.g., site=/sites/AS-ENG, lib=/sites/AS-ENG/PAL/SITE
        # → candidates: /sites/AS-ENG/PAL (one level deeper, the last part SITE is the library)
        if not lib_path.lower().startswith(current_site_path.lower()):
            logger.info(f'[HeadlessSP] _detect_subweb: library_path "{lib_path}" '
                        f'does not start with site_path "{current_site_path}" — skipping')
            return None

        # Get the path segments between the current site and the library
        remainder = lib_path[len(current_site_path):].strip('/')
        parts = remainder.split('/')
        logger.info(f'[HeadlessSP] _detect_subweb: checking {len(parts)} path segments '
                    f'between site and library: {parts}')

        if len(parts) <= 1:
            # Only one segment = that's the library name itself, not a subsite
            logger.info(f'[HeadlessSP] _detect_subweb: only 1 segment — library name, no subweb possible')
            return None

        # Check each intermediate path (not the final segment which is the library itself)
        # Deepest first, so we find the closest subweb to the library
        for i in range(len(parts) - 1, 0, -1):
            candidate_path = current_site_path + '/' + '/'.join(parts[:i])
            candidate_url = f'{parsed.scheme}://{parsed.netloc}{candidate_path}'

            logger.info(f'[HeadlessSP] _detect_subweb: probing "{candidate_path}" as potential subweb...')

            # Probe: call /_api/web on the candidate path
            # If it returns successfully, this is a subweb
            probe_url = f'{candidate_url}/_api/web?$select=Title,Url'
            try:
                result = self._page.evaluate('''async (url) => {
                    try {
                        const resp = await fetch(url, {
                            method: 'GET',
                            headers: {
                                'Accept': 'application/json;odata=verbose',
                            },
                            credentials: 'include',
                        });
                        if (resp.ok) {
                            const data = await resp.json();
                            return { success: true, data: data };
                        }
                        return { success: false, status: resp.status };
                    } catch (e) {
                        return { success: false, error: e.message || String(e) };
                    }
                }''', probe_url)

                if result and result.get('success'):
                    web_title = result.get('data', {}).get('d', {}).get('Title', '?')
                    web_url = result.get('data', {}).get('d', {}).get('Url', candidate_url)
                    logger.info(
                        f'[HeadlessSP] _detect_subweb: ✓ SUBWEB FOUND at "{candidate_path}" '
                        f'(Title="{web_title}", Url="{web_url}")'
                    )
                    return candidate_url
                else:
                    status = result.get('status', '?') if result else '?'
                    logger.info(f'[HeadlessSP] _detect_subweb: ✗ "{candidate_path}" is not a subweb (HTTP {status})')

            except Exception as e:
                logger.debug(f'[HeadlessSP] _detect_subweb: probe error for "{candidate_path}": {e}')
                continue

        logger.info(f'[HeadlessSP] _detect_subweb: no subwebs found between site and library')
        return None

    def auto_detect_library_path(self) -> Optional[str]:
        """Auto-detect the default document library path."""
        parsed = urlparse(self.site_url)
        site_path = parsed.path.rstrip('/')

        # Strategy 1: Query Lists API
        data = self._api_get(
            f"/_api/web/Lists?$filter=BaseTemplate eq 101 and Hidden eq false"
            f"&$select=Title,RootFolder/ServerRelativeUrl&$expand=RootFolder"
        )
        if data:
            results = data.get('d', {}).get('results', [])
            for lib in results:
                root = lib.get('RootFolder', {})
                srv_url = root.get('ServerRelativeUrl', '')
                if srv_url:
                    logger.info(f'[HeadlessSP] Lists API detected library: {srv_url}')
                    return srv_url

        # Strategy 2: Probe common names
        for lib_name in SharePointConnector.DEFAULT_LIBRARIES:
            test_path = f'{site_path}/{lib_name}'
            if self.validate_folder_path(test_path):
                logger.info(f'[HeadlessSP] Probe detected library: {test_path}')
                return test_path

        return None

    def list_files(
        self,
        folder_path: str,
        recursive: bool = True,
        max_files: int = 500,
    ) -> List[Dict[str, Any]]:
        """List documents in a SharePoint folder via headless browser REST API."""
        files = []
        self._list_files_recursive(folder_path, files, recursive, max_files, depth=0)
        return files[:max_files]

    def _list_items_fallback(
        self,
        folder_path: str,
        files: List[Dict],
        max_files: int,
    ):
        """
        v6.1.8: Fallback file discovery using the List Items API.

        When GetFolderByServerRelativePath(...)/Files returns 0 results but the folder
        has ItemCount > 0, the content may be stored as list items rather than traditional
        file-system files. This happens with certain SharePoint site templates, document
        sets, and list configurations.

        The List Items API (/_api/web/GetList(...)/Items) returns ALL items regardless of
        storage pattern. We try the folder_path as a list URL first; if that fails (404),
        we walk up the path to find the library root and filter by FileDirRef.
        """
        logger.info(f'[HeadlessSP] *** List Items API fallback for "{folder_path}" ***')

        # Strategy 1: Try GetList(folder_path)/Items — works if folder_path IS the library root
        encoded = SharePointConnector._encode_sp_path(folder_path)
        items_endpoint = (
            f"/_api/web/GetList('{encoded}')/Items"
            f"?$select=FileLeafRef,FileRef,File_x0020_Size,Modified,FSObjType"
            f"&$expand=File"
            f"&$filter=FSObjType eq 0"
            f"&$top={max_files}"
        )
        logger.info(f'[HeadlessSP] Trying GetList Items: {items_endpoint[:250]}')
        data = self._api_get(items_endpoint)

        if data:
            results = data.get('d', {}).get('results', [])
            logger.info(f'[HeadlessSP] GetList Items returned {len(results)} items')
            self._parse_list_items_into_files(results, files, max_files, folder_path)
            if files:
                logger.info(f'[HeadlessSP] List Items fallback found {len(files)} supported files')
                return

        # Strategy 2: Walk up the path to find the library root
        # e.g., /sites/AS-ENG/PAL/SITE → try /sites/AS-ENG/PAL, then /sites/AS-ENG
        parts = folder_path.rstrip('/').split('/')
        logger.info(f'[HeadlessSP] GetList failed for full path, walking up: {parts}')

        # Need at least /sites/SiteName/LibraryName (4 parts: '', 'sites', 'SiteName', 'LibName')
        for i in range(len(parts) - 1, 3, -1):
            candidate = '/'.join(parts[:i])
            candidate_encoded = SharePointConnector._encode_sp_path(candidate)
            logger.info(f'[HeadlessSP] Trying parent as library root: "{candidate}"')

            # Check if this is a valid list
            list_check = self._api_get(
                f"/_api/web/GetList('{candidate_encoded}')?$select=Title,Id,ItemCount"
            )
            if not list_check:
                continue

            list_title = list_check.get('d', {}).get('Title', '?')
            list_count = list_check.get('d', {}).get('ItemCount', 0)
            logger.info(f'[HeadlessSP] Found library root: "{candidate}" (Title="{list_title}", ItemCount={list_count})')

            # Query items, filtering by FileDirRef to scope to our subfolder
            # FileDirRef is the folder path without the file name
            items_endpoint = (
                f"/_api/web/GetList('{candidate_encoded}')/Items"
                f"?$select=FileLeafRef,FileRef,File_x0020_Size,Modified,FSObjType,FileDirRef"
                f"&$expand=File"
                f"&$filter=FSObjType eq 0"
                f"&$top={max_files}"
            )
            logger.info(f'[HeadlessSP] Querying items from library root: {items_endpoint[:250]}')
            data = self._api_get(items_endpoint)

            if data:
                results = data.get('d', {}).get('results', [])
                logger.info(f'[HeadlessSP] Library root Items returned {len(results)} total items')

                # Filter to items within our target folder (and subfolders)
                target_lower = folder_path.rstrip('/').lower()
                filtered = [
                    item for item in results
                    if (item.get('FileDirRef') or item.get('FileRef', '')).lower().startswith(target_lower)
                    or (item.get('FileRef', '') and os.path.dirname(item.get('FileRef', '')).lower().startswith(target_lower))
                ]
                logger.info(f'[HeadlessSP] After filtering to "{folder_path}": {len(filtered)} items')

                self._parse_list_items_into_files(filtered, files, max_files, folder_path)
                if files:
                    logger.info(f'[HeadlessSP] List Items fallback (via parent) found {len(files)} supported files')
                    return

        # Strategy 3: Try RenderListDataAsStream as last resort (POST request)
        logger.info(f'[HeadlessSP] Strategies 1-2 failed, trying RenderListDataAsStream...')
        self._render_list_data_fallback(folder_path, files, max_files)

    def _parse_list_items_into_files(
        self,
        items: List[Dict],
        files: List[Dict],
        max_files: int,
        folder_path: str,
    ):
        """Parse list items (from Items API) into file dicts matching the standard format."""
        for item in items:
            if len(files) >= max_files:
                break

            # Items API returns file info in nested File object or top-level fields
            file_data = item.get('File', {}) or {}
            name = file_data.get('Name') or item.get('FileLeafRef', '')
            if not name:
                continue

            ext = os.path.splitext(name)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            server_rel_url = file_data.get('ServerRelativeUrl') or item.get('FileRef', '')
            size = file_data.get('Length') or item.get('File_x0020_Size') or 0
            modified = file_data.get('TimeLastModified') or item.get('Modified', '')

            files.append({
                'name': name,
                'filename': name,
                'server_relative_url': server_rel_url,
                'size': int(size) if size else 0,
                'modified': modified,
                'extension': ext,
                'folder': os.path.dirname(server_rel_url) if server_rel_url else folder_path,
                'relative_path': server_rel_url,
            })

    def _render_list_data_fallback(
        self,
        folder_path: str,
        files: List[Dict],
        max_files: int,
    ):
        """
        v6.1.8: Last-resort fallback using RenderListDataAsStream POST API.

        This is the API that the SharePoint web UI itself uses internally.
        It requires an X-RequestDigest token obtained from /_api/contextinfo.
        """
        if not self._page:
            return

        try:
            # Get the request digest (CSRF-like token for POST requests)
            digest_result = self._page.evaluate('''async (siteUrl) => {
                try {
                    const resp = await fetch(siteUrl + '/_api/contextinfo', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json;odata=verbose',
                            'Content-Type': 'application/json;odata=verbose',
                        },
                        credentials: 'include',
                    });
                    if (resp.ok) {
                        const data = await resp.json();
                        return { success: true, digest: data.d.GetContextWebInformation.FormDigestValue };
                    }
                    return { success: false, error: 'HTTP ' + resp.status };
                } catch (e) {
                    return { success: false, error: e.message || String(e) };
                }
            }''', self.site_url)

            if not digest_result or not digest_result.get('success'):
                logger.warning(f'[HeadlessSP] Failed to get request digest: {digest_result}')
                return

            digest = digest_result['digest']
            encoded = SharePointConnector._encode_sp_path(folder_path)
            logger.info(f'[HeadlessSP] RenderListDataAsStream with digest, folder="{folder_path}"')

            # Call RenderListDataAsStream with RecursiveAll scope
            render_result = self._page.evaluate('''async ([siteUrl, listPath, digest, maxFiles]) => {
                try {
                    const resp = await fetch(
                        siteUrl + "/_api/web/GetList('" + listPath + "')/RenderListDataAsStream",
                        {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json;odata=verbose',
                                'Content-Type': 'application/json;odata=verbose',
                                'X-RequestDigest': digest,
                            },
                            credentials: 'include',
                            body: JSON.stringify({
                                parameters: {
                                    RenderOptions: 2,
                                    FolderServerRelativeUrl: listPath,
                                    ViewXml: "<View Scope='RecursiveAll'><Query><Where><Eq><FieldRef Name='FSObjType'/><Value Type='Integer'>0</Value></Eq></Where></Query><RowLimit Paged='TRUE'>" + maxFiles + "</RowLimit></View>"
                                }
                            }),
                        }
                    );
                    if (resp.ok) {
                        const data = await resp.json();
                        return { success: true, data: data };
                    }
                    return { success: false, error: 'HTTP ' + resp.status };
                } catch (e) {
                    return { success: false, error: e.message || String(e) };
                }
            }''', [self.site_url, encoded, digest, str(max_files)])

            if render_result and render_result.get('success'):
                data = render_result.get('data', {})
                rows = data.get('ListData', {}).get('Row', [])
                logger.info(f'[HeadlessSP] RenderListDataAsStream returned {len(rows)} rows')

                for row in rows:
                    if len(files) >= max_files:
                        break

                    name = row.get('FileLeafRef', '')
                    if not name:
                        continue

                    ext = os.path.splitext(name)[1].lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue

                    file_ref = row.get('FileRef', '')
                    size = row.get('File_x0020_Size') or row.get('FileSizeDisplay') or 0
                    modified = row.get('Modified', '')

                    files.append({
                        'name': name,
                        'filename': name,
                        'server_relative_url': file_ref,
                        'size': int(size) if size else 0,
                        'modified': modified,
                        'extension': ext,
                        'folder': os.path.dirname(file_ref) if file_ref else folder_path,
                        'relative_path': file_ref,
                    })

                if files:
                    logger.info(f'[HeadlessSP] RenderListDataAsStream found {len(files)} supported files')
            else:
                err = render_result.get('error', '?') if render_result else 'None'
                logger.warning(f'[HeadlessSP] RenderListDataAsStream failed: {err}')

        except Exception as e:
            logger.error(f'[HeadlessSP] RenderListDataAsStream exception: {e}')

    def _list_files_recursive(
        self,
        folder_path: str,
        files: List[Dict],
        recursive: bool,
        max_files: int,
        depth: int = 0,
    ):
        """Recursively list files in a SharePoint folder."""
        if len(files) >= max_files or depth > 10:
            return

        encoded_path = SharePointConnector._encode_sp_path(folder_path)
        logger.info(f'[HeadlessSP] list_files depth={depth}: "{folder_path}" → encoded: "{encoded_path}"')

        # Get files in this folder
        files_endpoint = (
            f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded_path}')/Files"
            f"?$select=Name,ServerRelativeUrl,Length,TimeLastModified"
            f"&$top={max_files - len(files)}"
        )
        logger.info(f'[HeadlessSP] Fetching files: {files_endpoint[:200]}')
        data = self._api_get(files_endpoint)

        files_found = 0
        if data:
            results = data.get('d', {}).get('results', [])
            all_file_names = [item.get('Name', '?') for item in results]
            supported_count = sum(
                1 for item in results
                if os.path.splitext(item.get('Name', ''))[1].lower() in self.SUPPORTED_EXTENSIONS
            )
            logger.info(
                f'[HeadlessSP] Files API returned {len(results)} items, '
                f'{supported_count} supported. All files: {all_file_names[:20]}'
            )
            files_found = len(results)

            for item in results:
                if len(files) >= max_files:
                    break

                name = item.get('Name', '')
                ext = os.path.splitext(name)[1].lower()

                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                server_rel_url = item.get('ServerRelativeUrl', '')
                files.append({
                    'name': name,
                    'filename': name,
                    'server_relative_url': server_rel_url,
                    'size': int(item.get('Length', 0)),
                    'modified': item.get('TimeLastModified', ''),
                    'extension': ext,
                    'folder': os.path.dirname(server_rel_url),
                    'relative_path': server_rel_url,
                })
        else:
            logger.warning(f'[HeadlessSP] Files API returned None for "{folder_path}"')

        # Recurse into subfolders
        folders_found = 0
        if recursive and len(files) < max_files:
            folders_endpoint = (
                f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded_path}')/Folders"
                f"?$select=Name,ServerRelativeUrl,ItemCount"
            )
            folder_data = self._api_get(folders_endpoint)
            if folder_data:
                folders = folder_data.get('d', {}).get('results', [])
                folder_names = [f.get('Name', '?') for f in folders]
                logger.info(f'[HeadlessSP] Subfolders at depth={depth}: {folder_names}')
                folders_found = len(folders)
                for subfolder in folders:
                    if len(files) >= max_files:
                        break

                    subfolder_name = subfolder.get('Name', '')
                    if subfolder_name.startswith('_') or subfolder_name == 'Forms':
                        continue

                    subfolder_url = subfolder.get('ServerRelativeUrl', '')
                    if subfolder_url:
                        self._list_files_recursive(
                            subfolder_url, files, recursive, max_files, depth + 1
                        )

        # v6.1.8: List Items API fallback — if /Files and /Folders both returned empty
        # but the folder has items (ItemCount > 0 from validate_folder_path), the content
        # is likely stored as list items, not file-system files. Try the Items API.
        if depth == 0 and files_found == 0 and folders_found == 0 and len(files) == 0:
            logger.info(
                f'[HeadlessSP] /Files and /Folders both empty at root — '
                f'trying List Items API fallback for "{folder_path}"'
            )
            self._list_items_fallback(folder_path, files, max_files)

    def download_file(self, server_relative_url: str, dest_path: str) -> Dict[str, Any]:
        """
        Download a file from SharePoint via the headless browser.

        Strategy A: Use page.evaluate(fetch()) to get file as base64
        Strategy B: Navigate to file URL and use Playwright's download API

        Args:
            server_relative_url: Server-relative path (e.g., /sites/Team/Docs/file.docx)
            dest_path: Local filesystem path to save the file

        Returns:
            {success: bool, path: str, size: int, message: str}
        """
        if not self._page:
            return {
                'success': False,
                'path': dest_path,
                'size': 0,
                'message': 'Browser not initialized',
            }

        encoded_path = SharePointConnector._encode_sp_path(server_relative_url)
        file_api_url = (
            f"{self.site_url}/_api/web/"
            f"GetFileByServerRelativePath(decodedUrl='{encoded_path}')/$value"
        )

        filename = os.path.basename(server_relative_url)

        # Strategy A: Fetch as base64 via page.evaluate
        try:
            logger.info(f'[HeadlessSP] Downloading (fetch): {filename}')
            result = self._page.evaluate('''async (url) => {
                try {
                    const resp = await fetch(url, {
                        method: 'GET',
                        credentials: 'include',
                    });
                    if (!resp.ok) {
                        return { success: false, status: resp.status, error: 'HTTP ' + resp.status };
                    }
                    const blob = await resp.blob();
                    return await new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve({
                            success: true,
                            data: reader.result,
                            size: blob.size,
                        });
                        reader.onerror = () => reject(reader.error);
                        reader.readAsDataURL(blob);
                    });
                } catch (e) {
                    return { success: false, status: 0, error: e.message || String(e) };
                }
            }''', file_api_url)

            if result and result.get('success'):
                data_url = result.get('data', '')
                # data_url format: "data:application/octet-stream;base64,AAAA..."
                if ';base64,' in data_url:
                    b64_data = data_url.split(';base64,', 1)[1]
                    file_bytes = base64.b64decode(b64_data)

                    # Ensure parent directory exists
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    with open(dest_path, 'wb') as f:
                        f.write(file_bytes)

                    size = len(file_bytes)
                    logger.info(f'[HeadlessSP] Downloaded {filename}: {size:,} bytes')
                    return {
                        'success': True,
                        'path': dest_path,
                        'size': size,
                        'message': f'Downloaded via headless browser ({size:,} bytes)',
                    }
                else:
                    logger.warning(f'[HeadlessSP] Unexpected data URL format for {filename}')
                    # Fall through to Strategy B

        except Exception as e:
            logger.warning(f'[HeadlessSP] Strategy A (fetch) failed for {filename}: {e}')

        # Strategy B: Navigate directly and use Playwright's download handler
        try:
            logger.info(f'[HeadlessSP] Downloading (navigate): {filename}')

            with self._page.expect_download(timeout=self.timeout) as download_info:
                self._page.goto(file_api_url, timeout=self.timeout)

            download = download_info.value
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            download.save_as(dest_path)

            size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
            logger.info(f'[HeadlessSP] Downloaded (navigate) {filename}: {size:,} bytes')
            return {
                'success': True,
                'path': dest_path,
                'size': size,
                'message': f'Downloaded via headless browser navigate ({size:,} bytes)',
            }

        except Exception as e:
            logger.warning(f'[HeadlessSP] Strategy B (navigate) failed for {filename}: {e}')

            # Final fallback: try direct page.goto without expect_download
            try:
                response = self._page.goto(file_api_url, timeout=self.timeout)
                if response and response.status == 200:
                    body = response.body()
                    if body and len(body) > 0:
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        with open(dest_path, 'wb') as f:
                            f.write(body)
                        size = len(body)
                        logger.info(f'[HeadlessSP] Downloaded (body) {filename}: {size:,} bytes')
                        return {
                            'success': True,
                            'path': dest_path,
                            'size': size,
                            'message': f'Downloaded via headless browser body ({size:,} bytes)',
                        }
            except Exception as e2:
                logger.error(f'[HeadlessSP] All download strategies failed for {filename}: {e2}')

        return {
            'success': False,
            'path': dest_path,
            'size': 0,
            'message': f'All download strategies failed for {filename}',
        }

    def connect_and_discover(
        self,
        library_path: str = '',
        recursive: bool = True,
        max_files: int = 500,
    ) -> Dict[str, Any]:
        """
        Combined authenticate + test + discover — same interface as SharePointConnector.

        Returns identical dict format for polymorphic use.
        """
        # Step 1: Test connection (authenticates via browser SSO)
        probe = self.test_connection()
        if not probe['success']:
            return {
                'success': False,
                'title': '',
                'auth_method': 'headless_browser',
                'library_path': '',
                'files': [],
                'message': probe.get('message', 'Headless browser authentication failed'),
                'ssl_fallback': False,
                'error_category': 'auth',
            }

        title = probe.get('title', '')

        # Step 2: Resolve library path
        # Defensive: ensure library_path is URL-decoded (parse_sharepoint_url should handle this,
        # but if the path arrives percent-encoded, decode it here)
        if library_path and '%' in library_path:
            from urllib.parse import unquote
            decoded = unquote(library_path)
            if decoded != library_path:
                logger.info(f'[HeadlessSP] URL-decoded library_path: "{library_path}" → "{decoded}"')
                library_path = decoded
        logger.info(f'[HeadlessSP] connect_and_discover: library_path="{library_path}", recursive={recursive}')
        if library_path:
            logger.info(f'[HeadlessSP] Validating provided library path: "{library_path}"')
            if not self.validate_folder_path(library_path):
                logger.info(f'[HeadlessSP] Path "{library_path}" not found, trying truncation...')
                parts = library_path.rstrip('/').split('/')
                logger.info(f'[HeadlessSP] Path parts for truncation: {parts}')
                found = False
                for i in range(len(parts), 2, -1):
                    candidate = '/'.join(parts[:i])
                    logger.info(f'[HeadlessSP] Trying truncated path ({i} parts): "{candidate}"')
                    if self.validate_folder_path(candidate):
                        logger.info(f'[HeadlessSP] ✓ Truncated path validated: "{candidate}"')
                        library_path = candidate
                        found = True
                        break
                if not found:
                    logger.warning('[HeadlessSP] ✗ ALL truncated paths failed — falling back to auto-detect')
                    library_path = ''
            else:
                logger.info(f'[HeadlessSP] ✓ Library path validated directly: "{library_path}"')

        if not library_path:
            logger.info('[HeadlessSP] No library path — attempting auto-detect...')
            try:
                detected = self.auto_detect_library_path()
                if detected:
                    library_path = detected
                    logger.info(f'[HeadlessSP] Auto-detected library: {library_path}')
                else:
                    logger.warning('[HeadlessSP] Auto-detect returned None')
            except Exception as e:
                logger.warning(f'[HeadlessSP] Library auto-detect failed: {e}')

        if not library_path:
            return {
                'success': True,
                'title': title,
                'auth_method': 'headless_browser',
                'library_path': '',
                'files': [],
                'message': f'Connected to "{title}" but could not detect document library. '
                           'Please enter the library path.',
                'ssl_fallback': False,
            }

        # Step 2b: Detect subsites in the library path (v6.1.9)
        # If the library lives under a subsite (e.g., /sites/AS-ENG/PAL/SITE
        # where PAL is a subsite), we need to re-route self.site_url to the
        # subsite's URL so that _api_get calls go to the correct web context.
        try:
            subweb_url = self._detect_subweb(library_path)
            if subweb_url:
                old_site = self.site_url
                self.site_url = subweb_url
                logger.info(
                    f'[HeadlessSP] *** SUBWEB RE-ROUTE: site_url changed from '
                    f'"{old_site}" to "{self.site_url}" ***'
                )
        except Exception as e:
            logger.warning(f'[HeadlessSP] Subweb detection failed (non-fatal): {e}')

        # Step 3: Discover files
        logger.info(f'[HeadlessSP] Step 3: Listing files in "{library_path}" (recursive={recursive})')
        try:
            files = self.list_files(library_path, recursive=recursive, max_files=max_files)
            logger.info(f'[HeadlessSP] list_files returned {len(files)} file(s)')
            if files:
                for f in files[:5]:
                    logger.info(f'[HeadlessSP]   → {f.get("name")} ({f.get("size", 0):,} bytes)')
                if len(files) > 5:
                    logger.info(f'[HeadlessSP]   ... and {len(files) - 5} more')
        except Exception as e:
            logger.error(f'[HeadlessSP] Discovery error: {e}')
            return {
                'success': True,
                'title': title,
                'auth_method': 'headless_browser',
                'library_path': library_path,
                'files': [],
                'message': f'Connected to "{title}" but failed to list files: {str(e)[:200]}',
                'ssl_fallback': False,
            }

        return {
            'success': True,
            'title': title,
            'auth_method': 'headless_browser',
            'library_path': library_path,
            'files': files,
            'message': f'Connected to "{title}" via headless browser (Windows SSO) — '
                       f'found {len(files)} document(s)',
            'ssl_fallback': False,
        }

    def close(self):
        """Close browser and Playwright, clean up temp user data dir."""
        try:
            if self._page:
                self._page.close()
                self._page = None
        except Exception:
            pass
        try:
            # v6.1.6: With persistent context, closing context closes browser
            if self._context:
                self._context.close()
                self._context = None
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
                self._browser = None
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
        except Exception:
            pass
        # v6.1.6: Clean up temp user data directory
        try:
            if self._user_data_dir and os.path.isdir(self._user_data_dir):
                import shutil
                shutil.rmtree(self._user_data_dir, ignore_errors=True)
                self._user_data_dir = None
        except Exception:
            pass
        logger.info('[HeadlessSP] Browser closed')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
