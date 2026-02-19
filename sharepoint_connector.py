"""
SharePoint Online Connector for AEGIS Document Review.

Connects to SharePoint document libraries via REST API using Windows SSO
(Negotiate/NTLM authentication). Zero external dependencies beyond requests
and requests-negotiate-sspi (both already installed).

v5.9.29 — Nicholas Georgeson

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
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, unquote, quote

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Windows SSO auth — same pattern as hyperlink_validator/validator.py
WINDOWS_AUTH_AVAILABLE = False
HttpNegotiateAuth = None
try:
    if sys.platform == 'win32':
        from requests_negotiate_sspi import HttpNegotiateAuth
        WINDOWS_AUTH_AVAILABLE = True
except ImportError:
    try:
        if sys.platform == 'win32':
            from requests_ntlm import HttpNtlmAuth
            # Fallback: NTLM with empty creds (not as good as Negotiate)
    except ImportError:
        pass

logger = logging.getLogger('aegis.sharepoint')


def parse_sharepoint_url(url: str) -> Dict[str, str]:
    """
    Parse a SharePoint URL into site_url and library_path components.

    Handles various formats:
        https://ngc.sharepoint.us/sites/MyTeam/Shared Documents/Subfolder
        https://ngc.sharepoint.us/sites/MyTeam/Shared%20Documents
        https://ngc.sharepoint.us/:f:/s/MyTeam/Shared%20Documents
        https://ngc.sharepoint.us/sites/MyTeam

    Returns:
        {'site_url': str, 'library_path': str, 'host': str}
    """
    url = url.strip().rstrip('/')
    parsed = urlparse(url)
    host = parsed.netloc
    path = unquote(parsed.path)

    # Handle /:f:/s/ short URLs
    if '/:f:/s/' in path or '/:f:/r/' in path:
        # Extract site and path from short URL
        # e.g., /:f:/s/MyTeam/Shared Documents → /sites/MyTeam, /sites/MyTeam/Shared Documents
        short_match = path.split('/:f:/')
        if len(short_match) > 1:
            after = short_match[1].lstrip('/')
            parts = after.split('/', 1)
            site_name = parts[0].lstrip('s/')
            site_url = f"{parsed.scheme}://{host}/sites/{site_name}"
            lib_path = f"/sites/{site_name}/{parts[1]}" if len(parts) > 1 else ''
            return {'site_url': site_url, 'library_path': lib_path, 'host': host}

    # Standard URL: find the /sites/XXX or /teams/XXX boundary
    path_lower = path.lower()
    site_url = f"{parsed.scheme}://{host}"
    library_path = ''

    for prefix in ('/sites/', '/teams/'):
        idx = path_lower.find(prefix)
        if idx >= 0:
            # Find end of site name (next / after the site name)
            after_prefix = path[idx + len(prefix):]
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

    def __init__(self, site_url: str, timeout: int = 30):
        """
        Initialize SharePoint connector.

        Args:
            site_url: SharePoint site URL (e.g., https://ngc.sharepoint.us/sites/MyTeam)
            timeout: HTTP request timeout in seconds
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")

        self.site_url = site_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        # Configure Windows SSO auth
        if WINDOWS_AUTH_AVAILABLE and HttpNegotiateAuth:
            try:
                self.session.auth = HttpNegotiateAuth()
                self.auth_method = 'negotiate'
                logger.info(f"SharePoint connector: Windows SSO (Negotiate) configured")
            except Exception as e:
                logger.warning(f"SharePoint connector: SSO setup failed: {e}")
                self.auth_method = 'none'
        else:
            self.auth_method = 'none'
            logger.warning("SharePoint connector: No Windows auth available — will attempt anonymous access")

        # SharePoint REST API headers
        self.session.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'AEGIS/5.9.29 SharePointConnector',
        })

    def _api_get(self, endpoint: str, stream: bool = False) -> requests.Response:
        """
        Make a GET request to the SharePoint REST API with retry logic.

        Args:
            endpoint: API endpoint (appended to site_url)
            stream: Whether to stream the response (for file downloads)

        Returns:
            requests.Response object

        Raises:
            requests.RequestException on persistent failure
        """
        url = f"{self.site_url}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                resp = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=stream,
                    allow_redirects=True,
                )

                # Handle SharePoint throttling
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get('Retry-After', self.RETRY_DELAY * (attempt + 1)))
                    logger.warning(f"SharePoint throttled (429) — waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue

                return resp

            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_DELAY * (attempt + 1)
                    logger.warning(f"SharePoint request failed (attempt {attempt + 1}): {e} — retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise

        # Should not reach here, but just in case
        raise requests.exceptions.RequestException(f"Failed after {self.MAX_RETRIES} retries")

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
                    return {
                        'success': True,
                        'title': title,
                        'url': url,
                        'auth_method': self.auth_method,
                        'message': f'Connected to "{title}" via {self.auth_method}',
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
                return {
                    'success': False,
                    'title': '',
                    'url': self.site_url,
                    'auth_method': self.auth_method,
                    'message': f'Authentication failed (401) — Windows SSO credentials not accepted',
                    'status_code': 401,
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

        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'Cannot reach SharePoint server — check VPN/network connection',
                'status_code': 0,
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'Connection timed out after {self.timeout}s',
                'status_code': 0,
            }
        except Exception as e:
            return {
                'success': False,
                'title': '',
                'url': self.site_url,
                'auth_method': self.auth_method,
                'message': f'Connection error: {str(e)[:200]}',
                'status_code': 0,
            }

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

        # URL-encode the folder path for the REST API
        encoded_path = quote(folder_path, safe='/:')

        try:
            # Get files in this folder
            resp = self._api_get(
                f"/_api/web/GetFolderByServerRelativeUrl('{encoded_path}')/Files"
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
                    f"/_api/web/GetFolderByServerRelativeUrl('{encoded_path}')/Folders"
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

    def download_file(self, server_relative_url: str, dest_path: str) -> Dict[str, Any]:
        """
        Download a single file from SharePoint.

        Uses /_api/web/GetFileByServerRelativeUrl('url')/$value for binary content.

        Args:
            server_relative_url: Server-relative URL of the file
            dest_path: Local path to save the downloaded file

        Returns:
            {'success': bool, 'path': str, 'size': int, 'message': str}
        """
        encoded_url = quote(server_relative_url, safe='/:')

        try:
            resp = self._api_get(
                f"/_api/web/GetFileByServerRelativeUrl('{encoded_url}')/$value",
                stream=True
            )

            if resp.status_code == 200:
                # Ensure destination directory exists
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
                }

            elif resp.status_code in (401, 403):
                return {
                    'success': False,
                    'path': dest_path,
                    'size': 0,
                    'message': f'Access denied ({resp.status_code})',
                }
            elif resp.status_code == 404:
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
                    'message': f'Download failed: HTTP {resp.status_code}',
                }

        except Exception as e:
            return {
                'success': False,
                'path': dest_path,
                'size': 0,
                'message': f'Download error: {str(e)[:200]}',
            }

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
