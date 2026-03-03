#!/usr/bin/env python3
"""
SharePoint Document Repository Manager v1.0
============================================
Manages a persistent local repository of documents downloaded from SharePoint.
Replaces the volatile "download → scan → delete" pattern with persistent local storage.

Features:
- Persistent local copies in sp_repository/ mirroring SP folder structure
- Manifest tracking with download metadata, hashes, and version history
- Version archiving when documents are updated on SharePoint
- Rescan from local cache without SP connection
- Thread-safe manifest operations with atomic writes
- Delta sync: only download new/modified files

Architecture:
    sp_repository/
    ├── manifest.json                    (master tracking file)
    ├── ngc.sharepoint.us/
    │   └── sites/
    │       └── AS-ENG/
    │           └── PAL/
    │               └── yyRelease/
    │                   └── T&E/
    │                       ├── Document1.docx
    │                       └── Document2.pdf
    └── .versions/
        └── ngc.sharepoint.us/
            └── sites/...
                └── Document1.2026-03-03T100000.docx

Author: AEGIS
"""

import os
import json
import hashlib
import shutil
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

try:
    from config_logging import get_logger
    _logger = get_logger('sp_repository')
except ImportError:
    _logger = logging.getLogger('sp_repository')


# ============================================================
# REPOSITORY MANAGER
# ============================================================

class SPRepositoryManager:
    """
    Manages a persistent local repository of SharePoint documents.

    Thread-safe: all manifest operations are protected by a Lock.
    Atomic writes: manifest.json is written to .tmp then os.replace()'d.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the repository manager.

        Args:
            base_dir: Base directory for the AEGIS project. If None, uses the
                      directory containing this file.
        """
        if base_dir is None:
            base_dir = str(Path(__file__).parent)

        self.base_dir = Path(base_dir)
        self.repo_dir = self.base_dir / 'sp_repository'
        self.versions_dir = self.repo_dir / '.versions'
        self.manifest_path = self.repo_dir / 'manifest.json'
        self._lock = threading.Lock()

        # Ensure directories exist
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize manifest
        self._manifest = self._load_manifest()

    # ── Manifest I/O ──────────────────────────────────────────

    def _load_manifest(self) -> Dict:
        """Load manifest from disk, or return empty structure."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'libraries' in data:
                        return data
            except Exception as e:
                _logger.warning(f'Failed to load manifest: {e}')

        return {
            'version': '1.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'libraries': {}
        }

    def _save_manifest(self):
        """Atomically save manifest to disk (write .tmp then os.replace)."""
        self._manifest['last_updated'] = datetime.utcnow().isoformat() + 'Z'

        tmp_path = self.manifest_path.with_suffix('.json.tmp')
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self._manifest, f, indent=2, ensure_ascii=False)
            os.replace(str(tmp_path), str(self.manifest_path))
        except Exception as e:
            _logger.error(f'Failed to save manifest: {e}')
            # Clean up temp file on failure
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    # ── Path Utilities ────────────────────────────────────────

    def _normalize_library_key(self, library_path: str) -> str:
        """Normalize a library path for use as a manifest key."""
        # Strip leading/trailing slashes and whitespace
        return library_path.strip().strip('/')

    def _get_host_from_url(self, site_url: str) -> str:
        """Extract hostname from a site URL."""
        try:
            parsed = urlparse(site_url)
            return parsed.hostname or 'unknown_host'
        except Exception:
            return 'unknown_host'

    def get_local_path(self, site_url: str, server_relative_url: str) -> Path:
        """
        Compute the persistent local path for a SharePoint file.

        Maps SP structure to local:
            sp_repository/{host}/{server_relative_path}

        Args:
            site_url: SharePoint site URL (e.g., 'https://ngc.sharepoint.us/sites/AS-ENG')
            server_relative_url: Server-relative URL (e.g., '/sites/AS-ENG/PAL/yyRelease/T&E/Doc.docx')

        Returns:
            Path object for the local file location
        """
        host = self._get_host_from_url(site_url)

        # Remove leading slash and sanitize path components
        rel_path = server_relative_url.lstrip('/')

        # Sanitize individual path components (remove chars illegal on Windows)
        parts = rel_path.split('/')
        safe_parts = []
        for part in parts:
            # Replace Windows-illegal characters but keep & and other valid chars
            safe = part.replace('<', '_').replace('>', '_').replace('"', '_')
            safe = safe.replace('|', '_').replace('?', '_').replace('*', '_')
            safe = safe.replace(':', '_') if len(safe) > 1 else safe  # Keep drive letters
            safe_parts.append(safe)

        local_path = self.repo_dir / host / '/'.join(safe_parts)
        return local_path

    # ── Core Operations ───────────────────────────────────────

    def needs_download(self, site_url: str, server_relative_url: str,
                       sp_modified: Optional[str] = None,
                       sp_size: Optional[int] = None) -> bool:
        """
        Check if a file needs to be downloaded (new, modified, or missing locally).

        Args:
            site_url: SharePoint site URL
            server_relative_url: Server-relative URL of the file
            sp_modified: SharePoint last-modified timestamp (ISO 8601)
            sp_size: File size on SharePoint

        Returns:
            True if file should be downloaded, False if local copy is current
        """
        local_path = self.get_local_path(site_url, server_relative_url)

        # File doesn't exist locally → needs download
        if not local_path.exists():
            return True

        # Check manifest for tracking info
        with self._lock:
            library_key = self._find_library_key_for_file(server_relative_url)
            if library_key is None:
                # File exists on disk but not in manifest → re-register needed
                return True

            lib_data = self._manifest['libraries'].get(library_key, {})
            filename = Path(server_relative_url).name
            file_entry = lib_data.get('files', {}).get(filename)

            if file_entry is None:
                return True

            # If SP provides modification date, compare
            if sp_modified and file_entry.get('sp_modified'):
                try:
                    sp_dt = datetime.fromisoformat(sp_modified.replace('Z', '+00:00'))
                    local_dt = datetime.fromisoformat(
                        file_entry['sp_modified'].replace('Z', '+00:00')
                    )
                    if sp_dt > local_dt:
                        return True
                except (ValueError, TypeError):
                    pass  # Can't compare dates — download to be safe

            # If SP provides file size, compare
            if sp_size is not None and file_entry.get('size'):
                if sp_size != file_entry['size']:
                    return True

            # File exists, is in manifest, and no evidence of changes
            return False

    def register_download(self, site_url: str, library_path: str,
                          server_relative_url: str, local_path: str,
                          sp_modified: Optional[str] = None,
                          sp_size: Optional[int] = None) -> Dict:
        """
        Register a downloaded file in the manifest.

        Args:
            site_url: SharePoint site URL
            library_path: Library path on SP (e.g., '/sites/AS-ENG/PAL/yyRelease/T&E')
            server_relative_url: Server-relative URL of the file
            local_path: Path where the file was saved locally
            sp_modified: SharePoint last-modified timestamp
            sp_size: File size

        Returns:
            Dict with registration status
        """
        local_path_obj = Path(local_path)

        # Compute file hash
        file_hash = self._compute_file_hash(str(local_path_obj))
        actual_size = local_path_obj.stat().st_size if local_path_obj.exists() else 0

        filename = local_path_obj.name
        now_iso = datetime.utcnow().isoformat() + 'Z'

        lib_key = self._normalize_library_key(library_path)

        with self._lock:
            # Ensure library entry exists
            if lib_key not in self._manifest['libraries']:
                self._manifest['libraries'][lib_key] = {
                    'site_url': site_url,
                    'last_sync': now_iso,
                    'files': {}
                }

            lib_data = self._manifest['libraries'][lib_key]
            lib_data['last_sync'] = now_iso

            # Check for existing entry (for version tracking)
            existing = lib_data['files'].get(filename)
            version_count = 1
            if existing:
                version_count = existing.get('version_count', 1) + 1

            # Create/update file entry
            lib_data['files'][filename] = {
                'server_relative_url': server_relative_url,
                'local_path': str(local_path_obj),
                'file_hash': file_hash,
                'size': sp_size or actual_size,
                'sp_modified': sp_modified or '',
                'downloaded_at': now_iso,
                'last_scanned': None,
                'scan_count': existing.get('scan_count', 0) if existing else 0,
                'version_count': version_count,
            }

            self._save_manifest()

        _logger.info(f'Registered download: {filename} → {local_path} '
                      f'(hash={file_hash[:8]}, size={actual_size}, v{version_count})')

        return {
            'success': True,
            'filename': filename,
            'local_path': str(local_path_obj),
            'file_hash': file_hash,
            'size': actual_size,
            'version_count': version_count,
            'is_update': version_count > 1,
        }

    def archive_previous_version(self, site_url: str, server_relative_url: str) -> Optional[str]:
        """
        Archive the current local copy before overwriting with a new version.

        Moves the file to .versions/ with a timestamp suffix.

        Args:
            site_url: SharePoint site URL
            server_relative_url: Server-relative URL of the file

        Returns:
            Path to archived version, or None if no previous version exists
        """
        local_path = self.get_local_path(site_url, server_relative_url)

        if not local_path.exists():
            return None

        # Build archive path: .versions/{host}/{rel_path_dir}/{filename}.{timestamp}.{ext}
        host = self._get_host_from_url(site_url)
        rel_path = server_relative_url.lstrip('/')
        rel_dir = str(Path(rel_path).parent)
        filename = local_path.name
        stem = local_path.stem
        suffix = local_path.suffix

        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H%M%S')
        archive_name = f'{stem}.{timestamp}{suffix}'

        archive_dir = self.versions_dir / host / rel_dir
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / archive_name

        try:
            shutil.copy2(str(local_path), str(archive_path))
            _logger.info(f'Archived previous version: {filename} → {archive_path}')
            return str(archive_path)
        except Exception as e:
            _logger.warning(f'Failed to archive {filename}: {e}')
            return None

    def mark_scanned(self, library_path: str, filename: str):
        """Update manifest to record that a file was scanned."""
        lib_key = self._normalize_library_key(library_path)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        with self._lock:
            lib_data = self._manifest['libraries'].get(lib_key)
            if lib_data and filename in lib_data.get('files', {}):
                lib_data['files'][filename]['last_scanned'] = now_iso
                lib_data['files'][filename]['scan_count'] = \
                    lib_data['files'][filename].get('scan_count', 0) + 1
                self._save_manifest()

    # ── Query Operations ──────────────────────────────────────

    def get_scannable_files(self, library_path: str) -> List[Dict]:
        """
        Get all locally-cached files for a library (for rescan without SP connection).

        Args:
            library_path: Library path to list files for

        Returns:
            List of dicts with filename, local_path, file_hash, size, etc.
        """
        lib_key = self._normalize_library_key(library_path)

        with self._lock:
            lib_data = self._manifest['libraries'].get(lib_key)
            if not lib_data:
                return []

            result = []
            for filename, entry in lib_data.get('files', {}).items():
                local_path = Path(entry['local_path'])
                if local_path.exists():
                    result.append({
                        'filename': filename,
                        'local_path': str(local_path),
                        'server_relative_url': entry.get('server_relative_url', ''),
                        'file_hash': entry.get('file_hash', ''),
                        'size': entry.get('size', 0),
                        'downloaded_at': entry.get('downloaded_at', ''),
                        'last_scanned': entry.get('last_scanned'),
                        'scan_count': entry.get('scan_count', 0),
                        'version_count': entry.get('version_count', 1),
                    })
                else:
                    _logger.warning(f'File missing from repository: {local_path}')

            return result

    def get_all_libraries(self) -> List[Dict]:
        """
        Get summary of all cached libraries.

        Returns:
            List of dicts with library_path, site_url, file_count, total_size, etc.
        """
        with self._lock:
            result = []
            for lib_key, lib_data in self._manifest.get('libraries', {}).items():
                files = lib_data.get('files', {})
                total_size = sum(f.get('size', 0) for f in files.values())

                # Count files that still exist on disk
                files_on_disk = sum(
                    1 for f in files.values()
                    if Path(f.get('local_path', '')).exists()
                )

                result.append({
                    'library_path': lib_key,
                    'site_url': lib_data.get('site_url', ''),
                    'last_sync': lib_data.get('last_sync', ''),
                    'file_count': len(files),
                    'files_on_disk': files_on_disk,
                    'total_size': total_size,
                })

            return result

    def get_library_status(self, library_path: str) -> Optional[Dict]:
        """
        Get detailed status for a specific library.

        Returns:
            Dict with file details, or None if library not found
        """
        lib_key = self._normalize_library_key(library_path)

        with self._lock:
            lib_data = self._manifest['libraries'].get(lib_key)
            if not lib_data:
                return None

            files = lib_data.get('files', {})
            total_size = sum(f.get('size', 0) for f in files.values())
            scanned_count = sum(1 for f in files.values() if f.get('last_scanned'))

            return {
                'library_path': lib_key,
                'site_url': lib_data.get('site_url', ''),
                'last_sync': lib_data.get('last_sync', ''),
                'file_count': len(files),
                'total_size': total_size,
                'scanned_count': scanned_count,
                'files': [
                    {
                        'filename': fname,
                        'size': entry.get('size', 0),
                        'downloaded_at': entry.get('downloaded_at', ''),
                        'last_scanned': entry.get('last_scanned'),
                        'scan_count': entry.get('scan_count', 0),
                        'version_count': entry.get('version_count', 1),
                        'exists_on_disk': Path(entry.get('local_path', '')).exists(),
                    }
                    for fname, entry in files.items()
                ]
            }

    def get_file_history(self, site_url: str, server_relative_url: str) -> List[Dict]:
        """
        Get version history for a specific file (archived versions).

        Returns:
            List of dicts with archive_path, timestamp, size
        """
        host = self._get_host_from_url(site_url)
        rel_path = server_relative_url.lstrip('/')
        rel_dir = str(Path(rel_path).parent)
        filename = Path(server_relative_url).name
        stem = Path(filename).stem
        suffix = Path(filename).suffix

        archive_dir = self.versions_dir / host / rel_dir

        if not archive_dir.exists():
            return []

        versions = []
        # Look for files matching pattern: {stem}.{timestamp}{suffix}
        for f in archive_dir.iterdir():
            if f.name.startswith(stem + '.') and f.name.endswith(suffix) and f.name != filename:
                try:
                    # Extract timestamp from filename
                    ts_part = f.name[len(stem) + 1:-len(suffix)] if suffix else f.name[len(stem) + 1:]
                    versions.append({
                        'archive_path': str(f),
                        'filename': f.name,
                        'timestamp': ts_part,
                        'size': f.stat().st_size,
                    })
                except Exception:
                    pass

        # Sort by timestamp descending (newest first)
        versions.sort(key=lambda v: v['timestamp'], reverse=True)
        return versions

    def get_stale_files(self, library_path: str, sp_files: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare SP file list with local manifest to find files needing download.

        Args:
            library_path: Library path
            sp_files: List of file dicts from SP discovery (must have 'filename',
                      'server_relative_url', optionally 'modified', 'size')

        Returns:
            Tuple of (needs_download_list, up_to_date_list)
        """
        lib_key = self._normalize_library_key(library_path)
        needs_download = []
        up_to_date = []

        with self._lock:
            lib_data = self._manifest['libraries'].get(lib_key, {})
            local_files = lib_data.get('files', {})

        for sp_file in sp_files:
            filename = sp_file.get('filename', '')
            local_entry = local_files.get(filename)

            if local_entry is None:
                # New file — not in local repo
                needs_download.append(sp_file)
                continue

            # Check if local file still exists on disk
            if not Path(local_entry.get('local_path', '')).exists():
                needs_download.append(sp_file)
                continue

            # Check modification date
            sp_modified = sp_file.get('modified') or sp_file.get('sp_modified')
            local_modified = local_entry.get('sp_modified')

            if sp_modified and local_modified:
                try:
                    sp_dt = datetime.fromisoformat(str(sp_modified).replace('Z', '+00:00'))
                    local_dt = datetime.fromisoformat(str(local_modified).replace('Z', '+00:00'))
                    if sp_dt > local_dt:
                        needs_download.append(sp_file)
                        continue
                except (ValueError, TypeError):
                    pass

            # Check size
            sp_size = sp_file.get('size')
            local_size = local_entry.get('size')
            if sp_size is not None and local_size is not None:
                if int(sp_size) != int(local_size):
                    needs_download.append(sp_file)
                    continue

            # File appears up to date
            up_to_date.append(sp_file)

        return needs_download, up_to_date

    # ── Cleanup Operations ────────────────────────────────────

    def cleanup_library(self, library_path: str, include_versions: bool = False) -> Dict:
        """
        Remove a library's local files and manifest entries.

        Args:
            library_path: Library path to clean up
            include_versions: Also delete archived versions

        Returns:
            Dict with cleanup results
        """
        lib_key = self._normalize_library_key(library_path)
        removed_files = 0
        removed_versions = 0
        freed_bytes = 0

        with self._lock:
            lib_data = self._manifest['libraries'].get(lib_key)
            if not lib_data:
                return {'success': False, 'message': 'Library not found in manifest'}

            # Remove files
            for filename, entry in lib_data.get('files', {}).items():
                local_path = Path(entry.get('local_path', ''))
                if local_path.exists():
                    try:
                        freed_bytes += local_path.stat().st_size
                        local_path.unlink()
                        removed_files += 1
                    except Exception as e:
                        _logger.warning(f'Could not remove {local_path}: {e}')

            # Clean up empty directories
            try:
                site_url = lib_data.get('site_url', '')
                host = self._get_host_from_url(site_url)
                host_dir = self.repo_dir / host
                if host_dir.exists():
                    self._cleanup_empty_dirs(host_dir)
            except Exception:
                pass

            # Remove versions if requested
            if include_versions:
                site_url = lib_data.get('site_url', '')
                host = self._get_host_from_url(site_url)
                for filename, entry in lib_data.get('files', {}).items():
                    rel_url = entry.get('server_relative_url', '')
                    if rel_url:
                        versions = self.get_file_history(site_url, rel_url)
                        for v in versions:
                            try:
                                vpath = Path(v['archive_path'])
                                freed_bytes += vpath.stat().st_size
                                vpath.unlink()
                                removed_versions += 1
                            except Exception:
                                pass

            # Remove from manifest
            del self._manifest['libraries'][lib_key]
            self._save_manifest()

        _logger.info(f'Cleaned up library {lib_key}: {removed_files} files, '
                      f'{removed_versions} versions, {freed_bytes} bytes freed')

        return {
            'success': True,
            'removed_files': removed_files,
            'removed_versions': removed_versions,
            'freed_bytes': freed_bytes,
        }

    # ── Internal Helpers ──────────────────────────────────────

    def _compute_file_hash(self, filepath: str) -> str:
        """Compute MD5 hash of a file."""
        try:
            md5 = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            _logger.warning(f'Could not hash {filepath}: {e}')
            return ''

    def _find_library_key_for_file(self, server_relative_url: str) -> Optional[str]:
        """Find which library a server_relative_url belongs to (by checking manifest entries)."""
        for lib_key, lib_data in self._manifest.get('libraries', {}).items():
            for filename, entry in lib_data.get('files', {}).items():
                if entry.get('server_relative_url') == server_relative_url:
                    return lib_key
        return None

    def _cleanup_empty_dirs(self, root_dir: Path):
        """Recursively remove empty directories under root_dir."""
        for dirpath, dirnames, filenames in os.walk(str(root_dir), topdown=False):
            if not dirnames and not filenames:
                try:
                    p = Path(dirpath)
                    if p != root_dir and p != self.repo_dir:
                        p.rmdir()
                except Exception:
                    pass


# ============================================================
# MODULE-LEVEL SINGLETON
# ============================================================

_repo_instance = None
_repo_lock = threading.Lock()


def get_repository() -> SPRepositoryManager:
    """Get or create the singleton SPRepositoryManager instance."""
    global _repo_instance
    if _repo_instance is None:
        with _repo_lock:
            if _repo_instance is None:
                _repo_instance = SPRepositoryManager()
    return _repo_instance
