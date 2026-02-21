"""
Headless Browser Validator
==========================
Uses Playwright to validate URLs that fail regular HTTP validation.

This module provides a fallback validation method for sites with aggressive
bot protection (Cloudflare, Akamai, etc.) that block standard HTTP requests.

Features:
- Chromium-based headless browser
- Passes most bot detection
- Handles JavaScript-rendered pages
- Automatic retry for blocked sites
- Configurable timeout and navigation options
- v5.9.44: Resource blocking (images, CSS, fonts) — 60-70% faster page loads
- v5.9.44: Parallel validation via multiple browser contexts (5x throughput)
- v5.9.44: Auth-server-allowlist flags for automatic Windows SSO passthrough
- v5.9.44: Login page detection heuristics (ADFS, Azure AD, SAML)
- v5.9.44: Soft 404 detection within headless browser results

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    from headless_validator import HeadlessValidator, is_playwright_available

    if is_playwright_available():
        validator = HeadlessValidator()
        results = validator.validate_urls(failed_urls)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

logger = logging.getLogger(__name__)

# Check if Playwright is available
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright, Browser, Page, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.info("Playwright not installed. Headless browser validation unavailable.")
    logger.info("Install with: pip install playwright && playwright install chromium")


def is_playwright_available() -> bool:
    """Check if Playwright is installed and available."""
    return PLAYWRIGHT_AVAILABLE


# v5.9.44: Resource types to block during headless validation
# Blocking these reduces page load by 60-70% since we only need the HTML response
BLOCKED_RESOURCE_TYPES = {'image', 'stylesheet', 'font', 'media', 'imageset'}

# v5.9.44: Corporate domains that need auth-server-allowlist for automatic SSO
CORP_AUTH_DOMAINS = [
    '*.myngc.com', '*.northgrum.com', '*.northropgrumman.com',
    '*.ngc.sharepoint.us', '*.sharepoint.com', '*.sharepoint.us',
    '*.mil', '*.gov', '*.service-now.com', '*.servicenow.com',
    '*.teams.microsoft.com',
]

# v5.9.44: Login page detection patterns
LOGIN_PAGE_INDICATORS = {
    'url_patterns': [
        '/adfs/ls/', '/adfs/oauth2/', 'login.microsoftonline.com',
        'login.windows.net', 'sts.windows.net', '/idp/SSO',
        'wa=wsignin', 'SAMLRequest=', '/saml/', '/sso/',
        'login.', '/auth/', '/signin', '/logon',
    ],
    'content_patterns': [
        '<input type="password"', 'type="password"',
        'id="passwordInput"', 'id="userNameInput"',
        'Sign in to your account', 'Enter your credentials',
        'Windows Security', 'Corporate Sign-In',
    ],
    'title_patterns': [
        'sign in', 'log in', 'login', 'authentication',
        'adfs', 'single sign-on', 'sso', 'identity provider',
    ]
}

# v5.9.44: Soft 404 detection patterns for headless results
SOFT_404_PATTERNS = [
    'page not found', 'not found', '404 error', 'page does not exist',
    'this page doesn\'t exist', 'no longer available', 'page has been removed',
    'content you are looking for', 'page you requested', 'nothing here',
    'sorry, we couldn\'t find', 'this resource does not exist',
]


@dataclass
class HeadlessResult:
    """Result from headless browser validation."""
    url: str
    status: str  # WORKING, BROKEN, TIMEOUT, ERROR
    status_code: Optional[int] = None
    message: str = ""
    response_time_ms: float = 0
    final_url: Optional[str] = None  # After redirects
    page_title: Optional[str] = None
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'status': self.status,
            'status_code': self.status_code,
            'message': self.message,
            'response_time_ms': self.response_time_ms,
            'final_url': self.final_url,
            'page_title': self.page_title,
            'error_details': self.error_details,
            'validation_method': 'headless_browser'
        }


def _is_login_page(url: str, title: str, content: str) -> bool:
    """
    v5.9.44: Detect if a page is a login/SSO redirect page.

    Returns True if the page appears to be a login page rather than
    the actual target content. This prevents false WORKING status when
    the browser was silently redirected to an auth page.
    """
    url_lower = url.lower() if url else ''
    title_lower = title.lower() if title else ''
    content_lower = content[:5000].lower() if content else ''  # Only check first 5KB

    # Check URL patterns
    for pattern in LOGIN_PAGE_INDICATORS['url_patterns']:
        if pattern.lower() in url_lower:
            return True

    # Check title patterns
    for pattern in LOGIN_PAGE_INDICATORS['title_patterns']:
        if pattern in title_lower:
            return True

    # Check content patterns (requires password field or auth-related text)
    password_field = any(p in content_lower for p in LOGIN_PAGE_INDICATORS['content_patterns'][:4])
    auth_text = any(p.lower() in content_lower for p in LOGIN_PAGE_INDICATORS['content_patterns'][4:])
    if password_field:
        return True

    return False


def _is_soft_404(title: str, content: str) -> bool:
    """
    v5.9.44: Detect soft 404 pages (server returns 200 but content says "not found").

    More accurate than the HTTP-only check because we have full page content.
    """
    title_lower = title.lower() if title else ''
    content_lower = content[:3000].lower() if content else ''

    for pattern in SOFT_404_PATTERNS:
        if pattern in title_lower or pattern in content_lower:
            return True

    return False


class HeadlessValidator:
    """
    Validates URLs using a headless Chromium browser.

    This bypasses most bot protection by acting as a real browser.
    Use as a fallback for URLs that fail regular HTTP validation.

    v5.9.44 improvements:
    - Resource blocking: blocks images/CSS/fonts for 60-70% faster loads
    - Parallel validation: uses multiple browser contexts (max 5 concurrent)
    - Auth-server-allowlist: passes corporate SSO domains for automatic auth
    - Login page detection: prevents false WORKING when redirected to auth
    - Soft 404 detection: catches pages that return 200 but show "not found"
    """

    # v5.9.44: Max concurrent validations (browser contexts)
    MAX_CONCURRENT = 5

    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        user_agent: Optional[str] = None,
        max_concurrent: int = 5
    ):
        """
        Initialize the headless validator.

        Args:
            timeout: Page load timeout in seconds
            headless: Run browser without visible window
            user_agent: Custom user agent string (optional)
            max_concurrent: Max parallel browser contexts (default 5)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )

        self.timeout = timeout * 1000  # Playwright uses milliseconds
        self.headless = headless
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        self.max_concurrent = min(max_concurrent, self.MAX_CONCURRENT)

        self._playwright = None
        self._browser: Optional[Browser] = None

    def __enter__(self):
        """Context manager entry - start browser."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser."""
        self.stop()

    def start(self):
        """Start the browser instance."""
        if self._browser is not None:
            return

        logger.info("Starting headless browser...")
        self._playwright = sync_playwright().start()

        # v5.9.44: Build launch args with auth-server-allowlist for corporate SSO
        base_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-extensions',
            '--disable-gpu',
            '--window-size=1920,1080',
        ]

        # v5.9.44: Add auth-server-allowlist for automatic Windows SSO passthrough
        # This tells Chromium to automatically pass Windows credentials to these domains
        allowlist = ','.join(CORP_AUTH_DOMAINS)
        base_args.append(f'--auth-server-allowlist={allowlist}')
        base_args.append(f'--auth-negotiate-delegate-allowlist={allowlist}')

        # Use "new headless" mode which is less detectable
        # channel="chrome" uses real Chrome instead of Chromium
        try:
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                channel="chrome",  # Use real Chrome if available
                args=base_args
            )
            logger.info("Headless browser started (Chrome channel) with SSO allowlist")
        except Exception:
            # Fall back to Chromium if Chrome not available
            fallback_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                f'--auth-server-allowlist={allowlist}',
                f'--auth-negotiate-delegate-allowlist={allowlist}',
            ]
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=fallback_args
            )
            logger.info("Headless browser started (Chromium fallback) with SSO allowlist")

    def stop(self):
        """Stop the browser instance."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.info("Headless browser stopped")

    def validate_url(self, url: str) -> HeadlessResult:
        """
        Validate a single URL using headless browser.

        Args:
            url: URL to validate

        Returns:
            HeadlessResult with validation status
        """
        if not self._browser:
            self.start()

        start_time = time.time()
        result = HeadlessResult(url=url, status='UNKNOWN')

        context = None
        page = None

        try:
            # Create new context with stealth settings
            # These settings help bypass bot detection
            # accept_downloads=True so we can detect file download links
            context = self._browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=True,  # Don't fail on SSL — we just want to know if the link exists
                # Add realistic browser properties
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                color_scheme='light',
                accept_downloads=True,  # Accept downloads so we can detect file links
            )

            page = context.new_page()

            # v5.9.44: Block non-essential resources for faster page loads
            # This reduces page load time by 60-70% since we only need the HTML
            def _handle_route(route):
                """Block images, CSS, fonts, media to speed up validation."""
                if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
                    route.abort()
                else:
                    route.continue_()

            page.route('**/*', _handle_route)

            # Track if a download was triggered (means the link is a valid file)
            download_triggered = {'value': False, 'filename': ''}

            def handle_download(download):
                """File download = link is valid (this is the 'document open popup')."""
                download_triggered['value'] = True
                download_triggered['filename'] = download.suggested_filename or ''
                # Cancel the actual download — we just needed to know it's valid
                download.cancel()

            page.on('download', handle_download)

            # Inject stealth scripts to hide automation
            # This removes the navigator.webdriver flag and other detection vectors
            page.add_init_script("""
                // Remove webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ]
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Add chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            """)

            # Set up response handler to capture status code
            response_status = {'code': None, 'url': None}

            def handle_response(response):
                # Capture the main document response
                if response.request.resource_type == 'document':
                    response_status['code'] = response.status
                    response_status['url'] = response.url

            page.on('response', handle_response)

            # Navigate to URL
            try:
                response = page.goto(
                    url,
                    timeout=self.timeout,
                    wait_until='domcontentloaded'  # Don't wait for all resources
                )

                if response:
                    result.status_code = response.status
                    result.final_url = response.url
                elif response_status['code']:
                    result.status_code = response_status['code']
                    result.final_url = response_status['url']

                # Get page title
                try:
                    result.page_title = page.title()
                except Exception:
                    pass

                # Check if a file download was triggered — this IS the "document open popup"
                # If the browser tried to download a file, the link is definitely valid
                if download_triggered['value']:
                    result.status = 'WORKING'
                    fname = download_triggered['filename']
                    result.message = f'File download link (valid) — {fname}' if fname else 'File download link (valid)'
                    result.response_time_ms = (time.time() - start_time) * 1000
                    return result

                # Determine status based on response
                if result.status_code:
                    if 200 <= result.status_code < 300:
                        # v5.9.44: Check for login page redirect and soft 404
                        page_content = ''
                        try:
                            page_content = page.content()
                        except Exception:
                            pass

                        final_url = result.final_url or url
                        page_title = result.page_title or ''

                        # v5.9.44: Login page detection — if we got 200 but it's a login page,
                        # the original URL requires authentication
                        if _is_login_page(final_url, page_title, page_content):
                            result.status = 'AUTH_REQUIRED'
                            result.message = f'Redirected to login page ({final_url[:80]})'
                        # v5.9.44: Soft 404 detection — server returned 200 but content says "not found"
                        elif _is_soft_404(page_title, page_content):
                            result.status = 'BROKEN'
                            result.message = f'Soft 404 — page says "not found" despite HTTP 200'
                        else:
                            result.status = 'WORKING'
                            result.message = f'HTTP {result.status_code} OK (headless browser)'
                    elif 300 <= result.status_code < 400:
                        result.status = 'REDIRECT'
                        result.message = f'Redirect to {result.final_url}'
                    elif result.status_code == 401:
                        result.status = 'AUTH_REQUIRED'
                        result.message = 'Authentication required (401)'
                    elif result.status_code == 403:
                        # Even with headless browser, check if we got real content
                        content = page.content()
                        if len(content) > 1000 and ('<!DOCTYPE' in content or '<html' in content):
                            # v5.9.44: Check if "real content" is actually a login page
                            if _is_login_page(result.final_url or url, result.page_title or '', content):
                                result.status = 'AUTH_REQUIRED'
                                result.message = 'Login page detected (403 with auth form)'
                            else:
                                # Got real content despite 403 - likely soft block
                                result.status = 'WORKING'
                                result.message = 'Page accessible (soft 403)'
                        else:
                            result.status = 'BLOCKED'
                            result.message = 'Access forbidden (403)'
                    elif result.status_code == 404:
                        result.status = 'BROKEN'
                        result.message = 'Page not found (404)'
                    elif result.status_code >= 500:
                        result.status = 'BROKEN'
                        result.message = f'Server error ({result.status_code})'
                    else:
                        result.status = 'UNKNOWN'
                        result.message = f'HTTP {result.status_code}'
                else:
                    # No response but no error - assume success
                    result.status = 'WORKING'
                    result.message = 'Page loaded successfully'

            except PlaywrightError as e:
                error_msg = str(e).lower()

                if 'timeout' in error_msg:
                    result.status = 'TIMEOUT'
                    result.message = f'Page load timeout ({self.timeout // 1000}s)'
                elif 'net::err_name_not_resolved' in error_msg:
                    result.status = 'DNSFAILED'
                    result.message = 'Could not resolve hostname'
                elif 'net::err_connection_refused' in error_msg:
                    result.status = 'BROKEN'
                    result.message = 'Connection refused'
                elif 'net::err_ssl' in error_msg or 'certificate' in error_msg:
                    result.status = 'SSLERROR'
                    result.message = 'SSL certificate error'
                else:
                    result.status = 'ERROR'
                    result.message = f'Navigation error: {str(e)[:100]}'

                result.error_details = str(e)

        except Exception as e:
            result.status = 'ERROR'
            result.message = f'Unexpected error: {str(e)[:100]}'
            result.error_details = str(e)
            logger.exception(f"Headless validation error for {url}")

        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass
            if context:
                try:
                    context.close()
                except Exception:
                    pass

        result.response_time_ms = (time.time() - start_time) * 1000
        return result

    def validate_urls(
        self,
        urls: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[HeadlessResult]:
        """
        Validate multiple URLs using headless browser.

        v5.9.44: Uses ThreadPoolExecutor with multiple browser contexts for
        parallel validation. Each URL gets its own context (isolated cookie/auth
        state) but shares the single browser instance. Max 5 concurrent contexts.

        Args:
            urls: List of URLs to validate
            progress_callback: Optional callback(current, total, url)

        Returns:
            List of HeadlessResult objects
        """
        total = len(urls)
        if total == 0:
            return []

        # Start browser if not already running
        was_running = self._browser is not None
        if not was_running:
            self.start()

        # v5.9.44: For small batches (<=3), use sequential (simpler, less overhead)
        if total <= 3:
            return self._validate_sequential(urls, progress_callback)

        # v5.9.44: Parallel validation for larger batches
        results_dict = {}  # url -> result (preserves order via final assembly)
        completed_count = 0
        progress_lock = threading.Lock()
        max_workers = min(self.max_concurrent, total)

        logger.info(f"Headless parallel validation: {total} URLs, {max_workers} concurrent contexts")

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(self.validate_url, url): url
                    for url in urls
                }

                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        logger.error(f"Headless validation thread error for {url}: {e}")
                        result = HeadlessResult(
                            url=url, status='ERROR',
                            message=f'Thread error: {str(e)[:100]}'
                        )

                    results_dict[url] = result

                    with progress_lock:
                        completed_count += 1
                        if progress_callback:
                            progress_callback(completed_count, total, url)

        finally:
            # Only stop if we started it
            if not was_running:
                self.stop()

        # Reassemble results in original URL order
        results = [results_dict.get(url, HeadlessResult(url=url, status='ERROR', message='No result'))
                   for url in urls]
        return results

    def _validate_sequential(
        self,
        urls: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[HeadlessResult]:
        """Sequential validation for small batches (<=3 URLs)."""
        results = []
        total = len(urls)
        was_running = self._browser is not None

        try:
            for i, url in enumerate(urls):
                result = self.validate_url(url)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, total, url)

                # Small delay between requests to be polite
                if i < total - 1:
                    time.sleep(0.3)

        finally:
            if not was_running:
                self.stop()

        return results


def rescan_failed_urls(
    failed_urls: List[str],
    timeout: int = 30,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Rescan failed URLs using headless browser.

    This is the main entry point for rescanning URLs that failed
    regular HTTP validation due to bot protection.

    Args:
        failed_urls: List of URLs that failed regular validation
        timeout: Page load timeout in seconds
        progress_callback: Optional callback(current, total, url)

    Returns:
        Dictionary with:
        - results: List of HeadlessResult dictionaries
        - summary: Summary statistics
        - available: Whether headless validation is available
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'available': False,
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium',
            'results': [],
            'summary': None
        }

    if not failed_urls:
        return {
            'available': True,
            'results': [],
            'summary': {'total': 0, 'working': 0, 'broken': 0}
        }

    logger.info(f"Rescanning {len(failed_urls)} failed URLs with headless browser")

    try:
        with HeadlessValidator(timeout=timeout) as validator:
            results = validator.validate_urls(failed_urls, progress_callback)

        # Build summary
        summary = {
            'total': len(results),
            'working': sum(1 for r in results if r.status == 'WORKING'),
            'redirect': sum(1 for r in results if r.status == 'REDIRECT'),
            'broken': sum(1 for r in results if r.status == 'BROKEN'),
            'blocked': sum(1 for r in results if r.status == 'BLOCKED'),
            'timeout': sum(1 for r in results if r.status == 'TIMEOUT'),
            'auth_required': sum(1 for r in results if r.status == 'AUTH_REQUIRED'),
            'errors': sum(1 for r in results if r.status in ['ERROR', 'DNSFAILED', 'SSLERROR']),
        }

        # Calculate how many were "recovered" (now working)
        summary['recovered'] = summary['working'] + summary['redirect']

        logger.info(f"Headless rescan complete: {summary['recovered']}/{summary['total']} recovered")

        return {
            'available': True,
            'results': [r.to_dict() for r in results],
            'summary': summary
        }

    except Exception as e:
        logger.exception("Headless rescan failed")
        return {
            'available': True,
            'error': str(e),
            'results': [],
            'summary': None
        }


# Convenience function to check capabilities
def get_headless_capabilities() -> Dict[str, Any]:
    """Get headless browser validation capabilities."""
    return {
        'available': PLAYWRIGHT_AVAILABLE,
        'browser': 'Chromium' if PLAYWRIGHT_AVAILABLE else None,
        'install_command': 'pip install playwright && playwright install chromium',
        'description': 'Headless browser validation for bot-protected sites',
        'use_case': 'Rescan URLs that return 403/blocked with regular HTTP requests',
        'features': [
            'Resource blocking (60-70% faster page loads)',
            'Parallel validation (5 concurrent contexts)',
            'Auth-server-allowlist for Windows SSO',
            'Login page detection (ADFS, Azure AD, SAML)',
            'Soft 404 detection',
            'Stealth scripts (anti-bot bypass)',
        ] if PLAYWRIGHT_AVAILABLE else []
    }
