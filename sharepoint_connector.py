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

# Windows SSO auth — same pattern as hyperlink_validator/validator.py
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
_sp_auth_init_error = None
_sp_auth_method = 'none'

# v6.0.5: SSPI preemptive auth — generate Negotiate token without waiting for challenge
SSPI_PREEMPTIVE_AVAILABLE = False
_sspi_module = None
_win32security_module = None
try:
    if sys.platform == 'win32':
        import sspi
        import win32security
        import pywintypes
        _sspi_module = sspi
        _win32security_module = win32security
        SSPI_PREEMPTIVE_AVAILABLE = True
except ImportError:
    pass
except Exception:
    pass

# v6.0.5: MSAL (Microsoft Authentication Library) for OAuth 2.0 / modern auth
# Required for SharePoint Online (GCC High, commercial) which has disabled legacy auth
MSAL_AVAILABLE = False
_msal_module = None
try:
    import msal
    _msal_module = msal
    MSAL_AVAILABLE = True
    logger.info('[AEGIS SharePoint] MSAL available — OAuth 2.0 / modern auth supported')
except ImportError:
    logger.info('[AEGIS SharePoint] MSAL not installed — OAuth 2.0 auth unavailable. '
                'Install with: pip install msal')

try:
    if sys.platform == 'win32':
        from requests_negotiate_sspi import HttpNegotiateAuth
        WINDOWS_AUTH_AVAILABLE = True
        _sp_auth_method = 'negotiate_sspi'
        logger.info('[AEGIS SharePoint] Windows SSO initialized via requests-negotiate-sspi')
    else:
        _sp_auth_init_error = f'Platform is {sys.platform}, not win32 — Windows SSO not applicable'
        logger.info(f'[AEGIS SharePoint] Skipping Windows auth: platform={sys.platform}')
except ImportError as e:
    logger.warning(f'[AEGIS SharePoint] requests-negotiate-sspi not available: {e}')
    try:
        if sys.platform == 'win32':
            from requests_ntlm import HttpNtlmAuth as HttpNegotiateAuth
            WINDOWS_AUTH_AVAILABLE = True
            _sp_auth_method = 'ntlm'
            logger.info('[AEGIS SharePoint] Windows SSO initialized via requests-ntlm (NTLM fallback)')
    except ImportError as e2:
        _sp_auth_init_error = f'negotiate-sspi: {e}, ntlm: {e2}'
        logger.error(f'[AEGIS SharePoint] NO Windows authentication available! '
                     f'SharePoint connections will fail on corporate networks. '
                     f'Errors: negotiate-sspi=[{e}], ntlm=[{e2}]')
except Exception as e:
    _sp_auth_init_error = f'Unexpected: {e}'
    logger.error(f'[AEGIS SharePoint] Auth init error: {e}', exc_info=True)


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


def _auto_detect_oauth_config(site_url: str) -> Optional[Dict[str, str]]:
    """
    v6.0.8: Auto-detect OAuth configuration from the SharePoint site URL.

    Uses Microsoft's well-known Office client ID and discovers the tenant
    from the SharePoint domain name. This provides zero-config OAuth
    when no sharepoint_oauth section exists in config.json.

    For GCC High (ngc.sharepoint.us) → tenant = 'ngc', authority = login.microsoftonline.us
    For commercial (contoso.sharepoint.com) → tenant = 'contoso', authority = login.microsoftonline.com

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
        if '.sharepoint.us' in host:
            tenant_name = host.split('.sharepoint.us')[0]
        elif '.sharepoint.com' in host:
            tenant_name = host.split('.sharepoint.com')[0]

        if not tenant_name:
            return None

        # Remove any subdomain prefix (e.g., 'ngc-my' → 'ngc')
        # But keep as-is for the tenant discovery
        authority = _get_oauth_authority(tenant_name, site_url)

        logger.info(f"SharePoint OAuth auto-detect: tenant='{tenant_name}', "
                    f"authority='{authority}', client_id=Microsoft Office (well-known)")

        return {
            'client_id': _MS_OFFICE_CLIENT_ID,
            'tenant_id': tenant_name,
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


def _acquire_oauth_token(site_url: str) -> Optional[str]:
    """
    v6.0.8: Acquire an OAuth 2.0 Bearer token for SharePoint access via MSAL.

    Uses a multi-strategy approach to get a token using the user's existing
    Windows credentials — NO app registration required for most configurations.

    Strategy order:
    1. Explicit config (sharepoint_oauth in config.json) with client_secret → client credentials
    2. Explicit config without client_secret → IWA with user's Windows UPN
    3. Auto-detected config (well-known Microsoft Office client ID) → IWA
    4. Device code flow as last resort (requires user to open browser once)

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
            app = _msal_module.ConfidentialClientApplication(
                client_id,
                authority=authority,
                client_credential=client_secret,
            )
            result = app.acquire_token_for_client(scopes=[resource])
            if result and 'access_token' in result:
                logger.info(f"SharePoint: OAuth token acquired via client credentials")
                return result['access_token']
            elif result:
                logger.debug(f"SharePoint OAuth client credentials failed: "
                             f"{result.get('error', '?')} — {result.get('error_description', '')[:200]}")
        except Exception as e:
            logger.debug(f"SharePoint OAuth client credentials error: {e}")

    # Strategy 2: Integrated Windows Auth (IWA) — uses current Windows logon
    # Works on domain-joined machines without user interaction
    try:
        app = _msal_module.PublicClientApplication(
            client_id,
            authority=authority,
        )

        # Get the user's Windows UPN for IWA
        username = _get_windows_upn()
        if username:
            logger.info(f"SharePoint OAuth: Trying IWA for user '{username}'")

            # Try acquire_token_by_username_password with UPN (ROPC-like flow)
            # For domain-joined machines with federation, this can work without actual password
            # by redirecting to the organization's ADFS/federation endpoint
            scopes = [resource.replace('/.default', '/AllSites.Read')]

            # First try IWA if the method exists (MSAL <1.30)
            if hasattr(app, 'acquire_token_by_integrated_windows_auth'):
                try:
                    result = app.acquire_token_by_integrated_windows_auth(
                        scopes=scopes,
                        username=username,
                    )
                    if result and 'access_token' in result:
                        logger.info(f"SharePoint: OAuth token acquired via IWA")
                        return result['access_token']
                    elif result:
                        logger.debug(f"SharePoint OAuth IWA failed: "
                                     f"{result.get('error', '?')} — {result.get('error_description', '')[:200]}")
                except Exception as iwa_err:
                    logger.debug(f"SharePoint OAuth IWA exception: {iwa_err}")

    except Exception as e:
        logger.debug(f"SharePoint OAuth IWA setup error: {e}")

    # Strategy 3: Device code flow — requires one-time browser auth
    # This is the most reliable fallback for GCC High environments
    try:
        app = _msal_module.PublicClientApplication(
            client_id,
            authority=authority,
        )
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

        # v6.0.5: Try OAuth token acquisition if configured
        if MSAL_AVAILABLE:
            oauth_token = _acquire_oauth_token(site_url)
            if oauth_token:
                self._oauth_token = oauth_token
                if self.auth_method == 'none':
                    self.auth_method = 'oauth'
                logger.info(f"SharePoint connector: OAuth token acquired via MSAL")

        # SharePoint REST API headers
        self.session.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'AEGIS/6.0.5 SharePointConnector',
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

                for item in results:
                    if len(files) >= max_files:
                        break

                    name = item.get('Name', '')
                    ext = os.path.splitext(name)[1].lower()

                    # Only include AEGIS-supported document types
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue

                    server_rel_url = item.get('ServerRelativeUrl', '')

                    # Compute relative folder path within the library
                    rel_folder = folder_path
                    if folder_path.startswith('/'):
                        rel_folder = folder_path

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
        if recursive and len(files) < max_files:
            try:
                resp = self._api_get(
                    f"/_api/web/GetFolderByServerRelativePath(decodedUrl='{encoded_path}')/Folders"
                    f"?$select=Name,ServerRelativeUrl,ItemCount"
                )

                if resp.status_code == 200:
                    data = resp.json()
                    folders = data.get('d', {}).get('results', [])

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
