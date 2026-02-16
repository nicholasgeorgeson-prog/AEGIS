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


class HeadlessValidator:
    """
    Validates URLs using a headless Chromium browser.

    This bypasses most bot protection by acting as a real browser.
    Use as a fallback for URLs that fail regular HTTP validation.
    """

    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the headless validator.

        Args:
            timeout: Page load timeout in seconds
            headless: Run browser without visible window
            user_agent: Custom user agent string (optional)
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
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

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

        # Use "new headless" mode which is less detectable
        # channel="chrome" uses real Chrome instead of Chromium
        try:
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                channel="chrome",  # Use real Chrome if available
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-infobars',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            )
            logger.info("Headless browser started (Chrome channel)")
        except Exception:
            # Fall back to Chromium if Chrome not available
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            logger.info("Headless browser started (Chromium fallback)")

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
            context = self._browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=False,  # We want to catch SSL errors
                # Add realistic browser properties
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                color_scheme='light',
            )

            page = context.new_page()

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

                # Determine status based on response
                if result.status_code:
                    if 200 <= result.status_code < 300:
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

        Args:
            urls: List of URLs to validate
            progress_callback: Optional callback(current, total, url)

        Returns:
            List of HeadlessResult objects
        """
        results = []
        total = len(urls)

        # Start browser if not already running
        was_running = self._browser is not None
        if not was_running:
            self.start()

        try:
            for i, url in enumerate(urls):
                result = self.validate_url(url)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, total, url)

                # Small delay between requests to be polite
                if i < total - 1:
                    time.sleep(0.5)

        finally:
            # Only stop if we started it
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
        'use_case': 'Rescan URLs that return 403/blocked with regular HTTP requests'
    }
