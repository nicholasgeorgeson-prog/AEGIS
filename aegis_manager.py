#!/usr/bin/env python3
"""
AEGIS Manager v1.0.0
====================
One-stop install, update, repair, backup, and packaging tool for AEGIS.

This single file handles everything:
  1.  Update AEGIS         — Pull latest version from GitHub
  2.  Full Sync            — Download ALL source files
  3.  Health Check          — Verify packages & dependencies
  4.  Repair               — Fix broken packages (5-phase)
  5.  Backup               — Create timestamped snapshot
  6.  Restore              — Restore from backup
  7.  Server               — Start / Stop / Restart / Status
  8.  Fresh Install         — Full setup from scratch
  9.  Package              — Create distribution archive
  10. Diagnostics          — System info & export
  11. Self-Update           — Update this manager tool
  0.  Exit

Zero external dependencies — uses only Python standard library.
Works with embedded Python (python/python.exe) or system Python.

Created by Nicholas Georgeson for AEGIS deployment at NGC.
"""

import os
import sys
import ssl
import json
import glob
import time
import shutil
import hashlib
import zipfile
import logging
import platform
import subprocess
import importlib
import threading
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

MANAGER_VERSION = "1.0.0"

# GitHub
REPO_OWNER = "nicholasgeorgeson-prog"
REPO_NAME = "AEGIS"
REPO = f"{REPO_OWNER}/{REPO_NAME}"
BRANCH = "main"
BASE_RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
API_BASE = f"https://api.github.com/repos/{REPO}"

def _load_pat():
    """Load GitHub PAT from aegis_pat.txt, env var, or built-in fallback."""
    # Strategy 1: Local file (preferred — not committed to GitHub)
    for pat_file in ['aegis_pat.txt', os.path.join(os.path.dirname(__file__), 'aegis_pat.txt')]:
        try:
            with open(pat_file, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if token and token.startswith('ghp_'):
                    return token
        except (OSError, IOError):
            pass
    # Strategy 2: Environment variable
    token = os.environ.get('AEGIS_GITHUB_PAT', '').strip()
    if token and token.startswith('ghp_'):
        return token
    # Strategy 3: Built-in (will be placeholder on GitHub copy)
    return "YOUR_GITHUB_PAT_HERE"

PAT = _load_pat()

# Server
SERVER_HOST = "localhost"
SERVER_PORT = 5050
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Source file extensions to sync (exclude binaries, wheels, audio, images)
SOURCE_EXTENSIONS = {
    '.py', '.js', '.css', '.html', '.json', '.md', '.bat', '.ps1', '.sh',
    '.txt', '.cfg', '.ini', '.toml', '.yml', '.yaml', '.mjs',
}

# Files/directories to NEVER overwrite (user data)
USER_DATA_PRESERVE = {
    'scan_history.db',
    'config.json',
    'user_settings.json',
    'review_patterns.json',
    'roles_patterns.json',
    'statement_forge/statement_patterns.json',
    'hyperlink_validator/hv_patterns.json',
    'proposal_compare/parser_patterns.json',
    'hyperlink_exclusions.db',
}

# Directories to NEVER sync
PRESERVE_DIRS = {
    'wheels', 'packaging/wheels', 'temp', 'backups', 'updates', 'logs',
    'static/audio', 'static/img', 'static/images', 'test_docs',
    'test_documents', '__pycache__', '.git', 'docling_models',
    'nltk_data', 'nlp_offline', 'learner_data', 'custom_dictionaries',
    'node_modules', '.venv', 'venv',
}

# Directories to exclude from packaging
PACKAGE_EXCLUDE = {
    'logs', 'temp', '__pycache__', '.git', 'backups', '.DS_Store',
    'test_docs', 'test_documents', 'node_modules', '.venv', 'venv',
    '.mypy_cache', '.pytest_cache',
}

# Required directories for fresh install
REQUIRED_DIRS = [
    "routes", "proposal_compare", "hyperlink_validator", "statement_forge",
    "document_compare", "portfolio", "nlp", "nlp/languagetool",
    "nlp/readability", "nlp/semantics", "nlp/spacy", "nlp/spelling",
    "nlp/style", "nlp/verbs", "templates", "static/js", "static/js/ui",
    "static/js/api", "static/js/utils", "static/js/features",
    "static/js/vendor", "static/js/vendor/pdfjs", "static/css",
    "static/css/features", "dictionaries", "packaging", "logs", "temp",
    "backups", "updates",
]

# Critical packages (import_name, pip_name, description)
CRITICAL_PACKAGES = [
    ('pkg_resources', 'setuptools', 'Package Resources (setuptools)'),
    ('flask', 'flask', 'Core Web Framework'),
    ('waitress', 'waitress', 'Production Server'),
    ('docx', 'python-docx', 'Word Document Processing'),
    ('pptx', 'python-pptx', 'PowerPoint Processing'),
    ('openpyxl', 'openpyxl', 'Excel Processing'),
    ('pandas', 'pandas', 'Data Analysis'),
    ('numpy', 'numpy', 'Numerical Computing'),
    ('sklearn', 'scikit-learn', 'Machine Learning'),
    ('scipy', 'scipy', 'Scientific Computing'),
    ('spacy', 'spacy', 'NLP Engine'),
    ('nltk', 'nltk', 'Natural Language Toolkit'),
    ('bs4', 'beautifulsoup4', 'HTML Parser'),
    ('lxml', 'lxml', 'XML Parser'),
    ('mammoth', 'mammoth', 'DOCX-to-HTML Converter'),
    ('reportlab', 'reportlab', 'PDF Report Generator'),
    ('werkzeug', 'werkzeug', 'WSGI Utilities'),
    ('jinja2', 'jinja2', 'Template Engine'),
    ('requests', 'requests', 'HTTP Library'),
    ('PIL', 'Pillow', 'Image Processing'),
    ('yaml', 'pyyaml', 'YAML Parser'),
    ('dotenv', 'python-dotenv', 'Env File Loader'),
    ('flask_cors', 'flask-cors', 'CORS Support'),
    ('chardet', 'chardet', 'Encoding Detection'),
    ('sentence_transformers', 'sentence-transformers', 'Semantic Similarity'),
]

# Optional packages
OPTIONAL_PACKAGES = [
    ('torch', 'torch', 'AI/Deep Learning'),
    ('docling', 'docling', 'AI Document Extraction'),
    ('requests_negotiate_sspi', 'requests-negotiate-sspi', 'Windows SSO'),
    ('requests_ntlm', 'requests-ntlm', 'Windows Domain Auth'),
    ('sspi', 'pywin32', 'SSPI Preemptive Auth (SharePoint)'),
    ('msal', 'msal', 'SharePoint Online Auth (OAuth)'),
    ('truststore', 'truststore', 'OS Certificate Store Integration'),
    ('playwright', 'playwright', 'Headless Browser (Gov Sites)'),
    ('textstat', 'textstat', 'Readability Statistics'),
    ('proselint', 'proselint', 'Writing Style Checker'),
    ('symspellpy', 'symspellpy', 'Spelling Corrections'),
    ('enchant', 'pyenchant', 'Spell Check Dictionary'),
]

# spaCy dependency chain (install order matters)
SPACY_CHAIN = [
    'colorama', 'typer', 'cymem', 'murmurhash', 'preshed', 'blis',
    'srsly', 'thinc', 'wasabi', 'weasel', 'catalogue', 'confection', 'spacy',
]

# Packages that need subprocess-based import testing
SUBPROCESS_CHECK = {'torch', 'requests_negotiate_sspi'}

# NLTK datasets
NLTK_DATASETS = [
    ('corpora/wordnet', 'wordnet', 'corpora'),
    ('tokenizers/punkt', 'punkt', 'tokenizers'),
    ('tokenizers/punkt_tab', 'punkt_tab', 'tokenizers'),
    ('corpora/stopwords', 'stopwords', 'corpora'),
    ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger', 'taggers'),
    ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng', 'taggers'),
    ('corpora/omw-1.4', 'omw-1.4', 'corpora'),
    ('corpora/cmudict', 'cmudict', 'corpora'),
]

# Log file
LOG_FILE = "aegis_manager.log"


# ═══════════════════════════════════════════════════════════════════════
# class ColorOutput — ANSI terminal colors + logging
# ═══════════════════════════════════════════════════════════════════════

class ColorOutput:
    """ANSI color output with dual stdout + log file support."""

    # Enable ANSI on Windows 10+
    if sys.platform == 'win32':
        os.system('')

    RESET  = '\033[0m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    WHITE  = '\033[97m'
    GOLD   = '\033[38;2;214;168;74m'  # AEGIS gold #D6A84A

    _log_file = None

    @classmethod
    def init_log(cls, log_path):
        """Open log file for writing."""
        try:
            cls._log_file = open(log_path, 'a', encoding='utf-8', errors='replace')
            cls._log_file.write(f"\n{'='*60}\n")
            cls._log_file.write(f"AEGIS Manager v{MANAGER_VERSION} — {datetime.now().isoformat()}\n")
            cls._log_file.write(f"{'='*60}\n\n")
        except Exception:
            cls._log_file = None

    @classmethod
    def close_log(cls):
        if cls._log_file:
            try:
                cls._log_file.close()
            except Exception:
                pass
            cls._log_file = None

    @classmethod
    def _strip_ansi(cls, text):
        """Remove ANSI codes for log file."""
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)

    @classmethod
    def _write(cls, text, end='\n'):
        """Write to stdout and log file."""
        print(text, end=end, flush=True)
        if cls._log_file:
            try:
                cls._log_file.write(cls._strip_ansi(text) + end)
                cls._log_file.flush()
            except Exception:
                pass

    @classmethod
    def ok(cls, msg):
        cls._write(f"    {cls.GREEN}[OK]{cls.RESET} {msg}")

    @classmethod
    def fail(cls, msg):
        cls._write(f"    {cls.RED}[FAIL]{cls.RESET} {msg}")

    @classmethod
    def warn(cls, msg):
        cls._write(f"    {cls.YELLOW}[WARN]{cls.RESET} {msg}")

    @classmethod
    def info(cls, msg):
        cls._write(f"    {cls.CYAN}[INFO]{cls.RESET} {msg}")

    @classmethod
    def header(cls, msg):
        cls._write(f"\n  {cls.BOLD}{cls.GOLD}{msg}{cls.RESET}")
        cls._write(f"  {'─' * len(cls._strip_ansi(msg))}")

    @classmethod
    def banner(cls, title, subtitle='', width=60):
        cls._write('')
        cls._write(f"  {cls.GOLD}╔{'═' * (width - 2)}╗{cls.RESET}")
        pad = width - 4 - len(title)
        cls._write(f"  {cls.GOLD}║{cls.RESET}  {cls.BOLD}{cls.WHITE}{title}{cls.RESET}{' ' * pad}{cls.GOLD}║{cls.RESET}")
        if subtitle:
            pad2 = width - 4 - len(subtitle)
            cls._write(f"  {cls.GOLD}║{cls.RESET}  {cls.DIM}{subtitle}{cls.RESET}{' ' * pad2}{cls.GOLD}║{cls.RESET}")
        cls._write(f"  {cls.GOLD}╚{'═' * (width - 2)}╝{cls.RESET}")

    @classmethod
    def progress_bar(cls, current, total, label='', width=40):
        if total <= 0:
            return
        pct = min(current / total, 1.0)
        filled = int(width * pct)
        bar = f"{'█' * filled}{'░' * (width - filled)}"
        text = f"\r    {cls.GOLD}{bar}{cls.RESET} {current}/{total} {label}"
        print(text, end='', flush=True)
        if current >= total:
            print()  # newline at completion
        if cls._log_file and current >= total:
            cls._log_file.write(f"    Progress: {current}/{total} {label}\n")

    @classmethod
    def prompt(cls, message, choices=None, default=None):
        """Get user input with optional choices."""
        if choices:
            cls._write(f"\n  {message}")
            for i, c in enumerate(choices):
                marker = f"{cls.GOLD}>{cls.RESET}" if (default is not None and i == default) else ' '
                cls._write(f"    {marker} {i}. {c}")
            while True:
                try:
                    raw = input(f"\n  {cls.GOLD}Choice:{cls.RESET} ").strip()
                    if not raw and default is not None:
                        return default
                    idx = int(raw)
                    if 0 <= idx < len(choices):
                        return idx
                except (ValueError, EOFError):
                    pass
                cls._write(f"    {cls.YELLOW}Enter 0-{len(choices)-1}{cls.RESET}")
        else:
            try:
                return input(f"  {cls.GOLD}{message}{cls.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                return default or ''


C = ColorOutput  # shorthand


# ═══════════════════════════════════════════════════════════════════════
# class GitHubClient — GitHub REST API + raw downloads
# ═══════════════════════════════════════════════════════════════════════

class GitHubClient:
    """GitHub API client with SSL fallback for corporate networks."""

    def __init__(self):
        self._ssl_ctx = None
        self._rate_remaining = None
        self._rate_reset = None

    def _get_ssl_ctx(self):
        """Get SSL context with 3-strategy fallback."""
        if self._ssl_ctx is not None:
            return self._ssl_ctx

        # Strategy 1: certifi
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            self._ssl_ctx = ctx
            return ctx
        except Exception:
            pass

        # Strategy 2: system certs
        try:
            ctx = ssl.create_default_context()
            self._ssl_ctx = ctx
            return ctx
        except Exception:
            pass

        # Strategy 3: unverified (corporate proxy fallback)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self._ssl_ctx = ctx
        return ctx

    def _request(self, url, method='GET', data=None, timeout=30, accept=None):
        """Core HTTP request with PAT auth and SSL fallback."""
        headers = {
            'User-Agent': f'AEGIS-Manager/{MANAGER_VERSION}',
            'Authorization': f'token {PAT}',
        }
        if accept:
            headers['Accept'] = accept
        else:
            headers['Accept'] = 'application/vnd.github.v3+json'

        if data:
            body = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        else:
            body = None

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            ctx = self._get_ssl_ctx()
            resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)

            # Track rate limit
            self._rate_remaining = resp.headers.get('X-RateLimit-Remaining')
            self._rate_reset = resp.headers.get('X-RateLimit-Reset')

            return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 403 and 'rate limit' in str(e.read().decode('utf-8', 'replace')).lower():
                C.warn('GitHub API rate limit exceeded. Wait a minute and try again.')
            raise
        except Exception:
            # SSL fallback: try with CERT_NONE
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self._ssl_ctx = ctx
            resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)
            self._rate_remaining = resp.headers.get('X-RateLimit-Remaining')
            return resp.read()

    def _api_get(self, endpoint):
        """GET from GitHub API, return parsed JSON."""
        url = f"{API_BASE}/{endpoint}"
        data = self._request(url)
        return json.loads(data)

    def check_connectivity(self):
        """Quick connectivity check. Returns (ok, info_dict)."""
        try:
            # rate_limit is at API root, not under repos/
            raw = self._request('https://api.github.com/rate_limit')
            data = json.loads(raw)
            core = data.get('rate', {})
            return True, {
                'remaining': core.get('remaining', '?'),
                'limit': core.get('limit', '?'),
                'reset': core.get('reset', '?'),
            }
        except Exception as e:
            return False, {'error': str(e)[:120]}

    def get_remote_version(self):
        """Download and parse remote version.json."""
        try:
            url = f"{BASE_RAW_URL}/version.json"
            data = self._request(url, accept='*/*')
            return json.loads(data)
        except Exception as e:
            return None

    def get_head_sha(self):
        """Get current HEAD commit SHA."""
        try:
            data = self._api_get(f'git/refs/heads/{BRANCH}')
            return data['object']['sha']
        except Exception:
            return None

    def get_file_tree(self, sha=None):
        """Get recursive file tree from Git Trees API.

        Returns list of {path, size, sha} for all files.
        """
        if not sha:
            sha = self.get_head_sha()
        if not sha:
            return []

        try:
            # Get the commit to find tree SHA
            commit = self._api_get(f'git/commits/{sha}')
            tree_sha = commit['tree']['sha']

            # Get recursive tree
            tree = self._api_get(f'git/trees/{tree_sha}?recursive=1')
            files = []
            for item in tree.get('tree', []):
                if item['type'] == 'blob':
                    files.append({
                        'path': item['path'],
                        'size': item.get('size', 0),
                        'sha': item['sha'],
                    })
            return files
        except Exception as e:
            C.warn(f'Could not get file tree: {e}')
            return []

    def download_raw_file(self, filepath, dest):
        """Download a single file from raw.githubusercontent.com."""
        url = f"{BASE_RAW_URL}/{filepath}"
        try:
            data = self._request(url, accept='*/*', timeout=60)
            parent = os.path.dirname(dest)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False  # file not in repo
            raise
        except Exception:
            return False

    def get_rate_info(self):
        """Get current rate limit info."""
        return {
            'remaining': self._rate_remaining,
            'reset': self._rate_reset,
        }


# ═══════════════════════════════════════════════════════════════════════
# class BackupManager — create, list, restore snapshots
# ═══════════════════════════════════════════════════════════════════════

class BackupManager:
    """Manages AEGIS backup snapshots with manifests."""

    def __init__(self, install_dir):
        self.install_dir = install_dir
        self.backups_dir = os.path.join(install_dir, 'backups')

    def create_backup(self, files=None, label='manual'):
        """Create a timestamped backup with manifest.

        Args:
            files: list of relative paths to back up. If None, backs up source files.
            label: label for backup folder name.

        Returns:
            (backup_dir, file_count)
        """
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Get current version
        version = 'unknown'
        vpath = os.path.join(self.install_dir, 'version.json')
        try:
            with open(vpath, 'r', encoding='utf-8', errors='replace') as f:
                version = json.load(f).get('version', 'unknown')
        except Exception:
            pass

        backup_name = f"v{version}_{label}_{ts}"
        backup_dir = os.path.join(self.backups_dir, backup_name)
        os.makedirs(backup_dir, exist_ok=True)

        # If no file list, find all source files
        if files is None:
            files = []
            for root, dirs, filenames in os.walk(self.install_dir):
                # Skip preserved dirs
                dirs[:] = [d for d in dirs if d not in PRESERVE_DIRS
                           and not d.startswith('.') and d != '__pycache__']
                rel_root = os.path.relpath(root, self.install_dir)
                if rel_root == '.':
                    rel_root = ''
                for fn in filenames:
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in SOURCE_EXTENSIONS:
                        rel = os.path.join(rel_root, fn) if rel_root else fn
                        files.append(rel)

        manifest_entries = []
        backed_up = 0

        for rel_path in files:
            src = os.path.join(self.install_dir, rel_path)
            if not os.path.isfile(src):
                continue

            # Flatten path for backup filename
            flat_name = rel_path.replace(os.sep, '_').replace('/', '_')
            dest = os.path.join(backup_dir, flat_name)

            try:
                shutil.copy2(src, dest)
                file_hash = self._file_hash(src)
                file_size = os.path.getsize(src)
                manifest_entries.append({
                    'path': rel_path,
                    'backup_name': flat_name,
                    'hash': file_hash,
                    'size': file_size,
                })
                backed_up += 1
            except Exception as e:
                C.warn(f'Could not backup {rel_path}: {e}')

        # Write manifest
        manifest = {
            'version': version,
            'created_at': datetime.now().isoformat(),
            'label': label,
            'file_count': backed_up,
            'files': manifest_entries,
        }
        manifest_path = os.path.join(backup_dir, 'manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        return backup_dir, backed_up

    def list_backups(self):
        """List all available backups with metadata.

        Returns list of dicts: {name, path, version, created_at, file_count, size_mb}
        """
        backups = []
        if not os.path.isdir(self.backups_dir):
            return backups

        for name in sorted(os.listdir(self.backups_dir), reverse=True):
            bdir = os.path.join(self.backups_dir, name)
            if not os.path.isdir(bdir):
                continue

            manifest_path = os.path.join(bdir, 'manifest.json')
            version = 'unknown'
            created_at = ''
            file_count = 0

            if os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8', errors='replace') as f:
                        m = json.load(f)
                    if isinstance(m, dict):
                        version = m.get('version', 'unknown')
                        created_at = m.get('created_at', '')
                        file_count = m.get('file_count', 0)
                    elif isinstance(m, list):
                        # Old list format
                        file_count = len(m)
                except Exception:
                    pass

            if not created_at:
                # Derive from folder name
                try:
                    stat = os.stat(bdir)
                    created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                except Exception:
                    created_at = 'unknown'

            if file_count == 0:
                # Count files in dir
                file_count = sum(1 for f in os.listdir(bdir) if f != 'manifest.json')

            # Calculate size
            total_size = sum(
                os.path.getsize(os.path.join(bdir, f))
                for f in os.listdir(bdir) if os.path.isfile(os.path.join(bdir, f))
            )

            backups.append({
                'name': name,
                'path': bdir,
                'version': version,
                'created_at': created_at[:19] if len(created_at) >= 19 else created_at,
                'file_count': file_count,
                'size_mb': round(total_size / (1024 * 1024), 1),
            })

        return backups

    def restore_backup(self, backup_name):
        """Restore files from a backup using its manifest.

        Returns (restored_count, error_count)
        """
        bdir = os.path.join(self.backups_dir, backup_name)
        if not os.path.isdir(bdir):
            C.fail(f'Backup not found: {backup_name}')
            return 0, 1

        manifest_path = os.path.join(bdir, 'manifest.json')
        entries = []

        if os.path.isfile(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8', errors='replace') as f:
                    m = json.load(f)
                if isinstance(m, dict):
                    entries = m.get('files', [])
                elif isinstance(m, list):
                    entries = m
            except Exception as e:
                C.fail(f'Could not read manifest: {e}')
                return 0, 1

        restored = 0
        errors = 0

        for entry in entries:
            if isinstance(entry, dict):
                rel_path = entry.get('path', '')
                backup_name_file = entry.get('backup_name', '')
                expected_hash = entry.get('hash', '')
            else:
                continue

            if not rel_path or not backup_name_file:
                continue

            src = os.path.join(bdir, backup_name_file)
            dest = os.path.join(self.install_dir, rel_path)

            if not os.path.isfile(src):
                C.warn(f'Missing from backup: {rel_path}')
                errors += 1
                continue

            try:
                parent = os.path.dirname(dest)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                shutil.copy2(src, dest)

                # Verify hash if available
                if expected_hash:
                    actual = self._file_hash(dest)
                    if actual != expected_hash:
                        C.warn(f'Hash mismatch after restore: {rel_path}')

                restored += 1
            except Exception as e:
                C.fail(f'Could not restore {rel_path}: {e}')
                errors += 1

        return restored, errors

    @staticmethod
    def _file_hash(path):
        """SHA-256 hash of a file."""
        h = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()[:16]
        except Exception:
            return ''


# ═══════════════════════════════════════════════════════════════════════
# class ServerManager — start, stop, restart, status
# ═══════════════════════════════════════════════════════════════════════

class ServerManager:
    """Manages the AEGIS Flask server process."""

    def __init__(self, install_dir):
        self.install_dir = install_dir

    def is_running(self):
        """Check if AEGIS server is running.

        Returns (running: bool, version_info: dict or None)
        """
        try:
            url = f"{SERVER_URL}/api/version"
            req = urllib.request.Request(url, headers={
                'User-Agent': f'AEGIS-Manager/{MANAGER_VERSION}',
            })
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            return True, data
        except Exception:
            return False, None

    def stop(self):
        """Stop the AEGIS server."""
        if sys.platform == 'win32':
            return self._stop_windows()
        else:
            return self._stop_unix()

    def _stop_windows(self):
        """Stop server on Windows using netstat + taskkill."""
        try:
            # Find PID using port
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True, text=True, timeout=10
            )
            pids = set()
            for line in result.stdout.splitlines():
                if f':{SERVER_PORT}' in line and 'LISTENING' in line:
                    parts = line.strip().split()
                    if parts:
                        try:
                            pids.add(int(parts[-1]))
                        except ValueError:
                            pass

            if not pids:
                C.info('No AEGIS process found on port 5050')
                return True

            killed = 0
            for pid in pids:
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(pid)],
                        capture_output=True, timeout=10
                    )
                    killed += 1
                except Exception:
                    pass

            time.sleep(1)
            C.ok(f'Stopped {killed} process(es)')
            return True
        except Exception as e:
            C.fail(f'Could not stop server: {e}')
            return False

    def _stop_unix(self):
        """Stop server on Mac/Linux using lsof + kill."""
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{SERVER_PORT}'],
                capture_output=True, text=True, timeout=10
            )
            pids = result.stdout.strip().split('\n')
            pids = [p.strip() for p in pids if p.strip()]

            if not pids:
                C.info('No AEGIS process found on port 5050')
                return True

            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], capture_output=True, timeout=10)
                except Exception:
                    pass

            time.sleep(1)
            C.ok(f'Stopped {len(pids)} process(es)')
            return True
        except Exception as e:
            C.fail(f'Could not stop server: {e}')
            return False

    def start(self):
        """Start the AEGIS server."""
        # Find the right Python executable
        python_exe = self._find_python()
        if not python_exe:
            C.fail('Could not find Python executable')
            return False

        app_py = os.path.join(self.install_dir, 'app.py')
        if not os.path.isfile(app_py):
            C.fail('app.py not found')
            return False

        # Strategy 1: Direct Python launch (preferred — works headless)
        C.info(f'Starting with: {python_exe} app.py')
        try:
            if sys.platform == 'win32':
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    [python_exe, app_py],
                    creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
                    cwd=self.install_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    [python_exe, app_py],
                    start_new_session=True,
                    cwd=self.install_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
            started = self._wait_for_server(30)
            if started:
                return True
            C.warn('Direct Python start did not respond — trying Start_AEGIS.bat...')
        except Exception as e:
            C.warn(f'Direct Python start failed: {e}')

        # Strategy 2: Start_AEGIS.bat with its own console window (Windows only)
        if sys.platform == 'win32':
            bat = os.path.join(self.install_dir, 'Start_AEGIS.bat')
            if os.path.isfile(bat):
                C.info('Launching Start_AEGIS.bat in new window...')
                try:
                    CREATE_NEW_CONSOLE = 0x00000010
                    subprocess.Popen(
                        ['cmd', '/c', bat],
                        creationflags=CREATE_NEW_CONSOLE,
                        cwd=self.install_dir,
                    )
                    return self._wait_for_server(30)
                except Exception as e:
                    C.fail(f'Start_AEGIS.bat also failed: {e}')
                    return False

        C.fail('Could not start server')
        return False

    def restart(self):
        """Restart the AEGIS server."""
        C.info('Stopping server...')
        stopped = self.stop()
        if not stopped:
            C.warn('Stop may not have completed cleanly')

        # Wait for port to be fully released before starting
        C.info('Waiting for port to clear...')
        for _ in range(5):
            time.sleep(1)
            running, _ = self.is_running()
            if not running:
                break
        else:
            C.warn('Port 5050 may still be in use — attempting start anyway')

        C.info('Starting server...')
        return self.start()

    def _wait_for_server(self, timeout=30):
        """Poll /api/version until server responds."""
        C.info(f'Waiting for server (up to {timeout}s)...')
        start = time.time()
        while time.time() - start < timeout:
            running, info = self.is_running()
            if running:
                ver = info.get('version', '?') if info else '?'
                C.ok(f'Server is running (v{ver})')
                return True
            time.sleep(1)
        C.warn('Server did not respond in time. It may still be starting.')
        return False

    def _find_python(self):
        """Find the correct Python executable."""
        # Check for embedded Python (OneClick installer)
        embedded = os.path.join(self.install_dir, 'python', 'python.exe')
        if os.path.isfile(embedded):
            return embedded

        # Use current interpreter
        return sys.executable


# ═══════════════════════════════════════════════════════════════════════
# class PackageManager — pip install, health check, repair
# ═══════════════════════════════════════════════════════════════════════

class PackageManager:
    """Manages pip packages, health checks, and repairs."""

    def __init__(self, install_dir):
        self.install_dir = install_dir
        self._python_exe = self._find_python()

    def _find_python(self):
        """Find the correct Python executable."""
        embedded = os.path.join(self.install_dir, 'python', 'python.exe')
        if os.path.isfile(embedded):
            return embedded
        return sys.executable

    def find_wheels_dirs(self):
        """Find all wheel directories."""
        dirs = []
        candidates = [
            os.path.join(self.install_dir, 'wheels'),
            os.path.join(self.install_dir, 'packaging', 'wheels'),
        ]
        for d in candidates:
            if os.path.isdir(d):
                whl_count = len(glob.glob(os.path.join(d, '*.whl')))
                if whl_count > 0:
                    dirs.append(d)
        return dirs

    def pip_install(self, packages, force=False):
        """Install packages with offline-first + online fallback.

        Args:
            packages: string or list of package specs
            force: use --force-reinstall

        Returns:
            (success: bool, method: str)
        """
        if isinstance(packages, str):
            packages = [packages]

        wheels_dirs = self.find_wheels_dirs()

        # Strategy 1: Offline install from wheels
        if wheels_dirs:
            cmd = [self._python_exe, '-m', 'pip', 'install',
                   '--no-warn-script-location']
            for wd in wheels_dirs:
                cmd.extend(['--no-index', '--find-links', wd])
            if force:
                cmd.append('--force-reinstall')
            cmd.extend(packages)

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    return True, 'offline'
            except Exception:
                pass

        # Strategy 2: Hybrid (local wheels + online for missing deps)
        if wheels_dirs:
            cmd = [self._python_exe, '-m', 'pip', 'install',
                   '--no-warn-script-location']
            for wd in wheels_dirs:
                cmd.extend(['--find-links', wd])
            if force:
                cmd.append('--force-reinstall')
            cmd.extend(packages)

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    return True, 'hybrid'
            except Exception:
                pass

        # Strategy 3: Online only
        cmd = [self._python_exe, '-m', 'pip', 'install',
               '--no-warn-script-location']
        if force:
            cmd.append('--force-reinstall')
        cmd.extend(packages)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                return True, 'online'
            return False, result.stderr[:200] if result.stderr else 'unknown error'
        except subprocess.TimeoutExpired:
            return False, 'timeout'
        except Exception as e:
            return False, str(e)[:200]

    def check_import(self, module_name):
        """Test if a module can be imported.

        Returns (success: bool, error_msg: str)
        """
        # Some packages need subprocess for clean import testing
        if module_name in SUBPROCESS_CHECK:
            return self._check_import_subprocess(module_name)

        try:
            # Clear from cache if present
            if module_name in sys.modules:
                del sys.modules[module_name]
            importlib.import_module(module_name)
            return True, ''
        except Exception as e:
            return False, str(e)[:200]

    def _check_import_subprocess(self, module_name):
        """Test import in a clean subprocess."""
        try:
            result = subprocess.run(
                [self._python_exe, '-c', f'import {module_name}; print("OK")'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and 'OK' in result.stdout:
                return True, ''
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'import failed'
            return False, err[:200]
        except subprocess.TimeoutExpired:
            return False, 'import timed out'
        except Exception as e:
            return False, str(e)[:200]

    def check_spacy_model(self):
        """Check if spaCy en_core_web_sm model is available."""
        try:
            result = subprocess.run(
                [self._python_exe, '-c',
                 'import spacy; nlp=spacy.load("en_core_web_sm"); '
                 'print("OK:" + nlp.meta.get("version", "?"))'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip().startswith('OK:'):
                ver = result.stdout.strip().split(':')[1]
                return True, ver
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            return False, err[:200]
        except Exception as e:
            return False, str(e)[:200]

    def preflight_setuptools(self):
        """Fix setuptools v82+ (removed pkg_resources)."""
        C.info('Checking setuptools / pkg_resources...')
        ok, err = self.check_import('pkg_resources')
        if ok:
            C.ok('pkg_resources available')
            return

        C.warn('pkg_resources missing (setuptools v82+ removed it)')
        C.info('Attempting to install setuptools<81...')

        # Try wheel directories first
        wheels_dirs = self.find_wheels_dirs()
        if wheels_dirs:
            for wd in wheels_dirs:
                whls = glob.glob(os.path.join(wd, 'setuptools-8*.whl'))
                whls.extend(glob.glob(os.path.join(wd, 'setuptools-7*.whl')))
                whls.extend(glob.glob(os.path.join(wd, 'setuptools-6*.whl')))
                for whl in sorted(whls, reverse=True):
                    C.info(f'Trying wheel: {os.path.basename(whl)}')
                    try:
                        result = subprocess.run(
                            [self._python_exe, '-m', 'pip', 'install',
                             '--force-reinstall', '--no-warn-script-location', whl],
                            capture_output=True, text=True, timeout=120
                        )
                        if result.returncode == 0:
                            ok2, _ = self.check_import('pkg_resources')
                            if ok2:
                                C.ok('setuptools fixed from wheel')
                                return
                    except Exception:
                        pass

        # Online fallback
        success, method = self.pip_install(['setuptools<81'], force=True)
        if success:
            ok2, _ = self.check_import('pkg_resources')
            if ok2:
                C.ok(f'setuptools fixed ({method})')
                return

        C.fail('Could not fix pkg_resources. spaCy model loading will fail.')

    def health_check(self):
        """Quick health check of all packages.

        Returns (critical_pass, critical_fail, optional_pass, optional_fail, details)
        """
        details = {'critical': [], 'optional': [], 'model': None, 'nltk': None}

        c_pass = c_fail = 0
        for imp, pip_name, desc in CRITICAL_PACKAGES:
            ok, err = self.check_import(imp)
            status = 'ok' if ok else 'fail'
            details['critical'].append((desc, pip_name, status, err))
            if ok:
                c_pass += 1
            else:
                c_fail += 1

        o_pass = o_fail = 0
        for imp, pip_name, desc in OPTIONAL_PACKAGES:
            ok, err = self.check_import(imp)
            status = 'ok' if ok else 'missing'
            details['optional'].append((desc, pip_name, status, err))
            if ok:
                o_pass += 1
            else:
                o_fail += 1

        # spaCy model
        m_ok, m_info = self.check_spacy_model()
        details['model'] = ('ok' if m_ok else 'fail', m_info)

        return c_pass, c_fail, o_pass, o_fail, details

    def check_nltk_data(self):
        """Check and fix NLTK data packages."""
        try:
            import nltk
        except ImportError:
            C.warn('NLTK not available, skipping data check')
            return

        # Set local path
        local_dir = os.path.join(self.install_dir, 'nltk_data')
        if os.path.isdir(local_dir):
            os.environ['NLTK_DATA'] = local_dir
            if local_dir not in nltk.data.path:
                nltk.data.path.insert(0, local_dir)

        ok_count = 0
        fix_count = 0
        for path, name, category in NLTK_DATASETS:
            try:
                nltk.data.find(path)
                ok_count += 1
            except LookupError:
                # Try extracting bundled ZIP
                fixed = False
                if os.path.isdir(local_dir):
                    try:
                        zip_path = os.path.join(local_dir, category, f'{name}.zip')
                        extract_dir = os.path.join(local_dir, category, name)
                        if os.path.exists(zip_path) and not os.path.isdir(extract_dir):
                            zipfile.ZipFile(zip_path).extractall(
                                os.path.join(local_dir, category))
                            if os.path.isdir(extract_dir):
                                C.ok(f'{name} (extracted from bundled ZIP)')
                                fixed = True
                                fix_count += 1
                    except Exception:
                        pass

                if not fixed:
                    try:
                        nltk.download(name, quiet=True)
                        C.ok(f'{name} (downloaded)')
                        fix_count += 1
                    except Exception:
                        C.fail(f'{name} — missing')

        return ok_count, fix_count

    def full_repair(self):
        """Full 5-phase repair (from repair_aegis.py pattern)."""
        C.header('[Phase 0] Pre-flight: setuptools')
        self.preflight_setuptools()

        C.header('[Phase 1] Environment Check')
        C.info(f'Python: {sys.version.split()[0]}')
        C.info(f'Executable: {self._python_exe}')
        C.info(f'Install dir: {self.install_dir}')
        wheels = self.find_wheels_dirs()
        if wheels:
            for wd in wheels:
                C.ok(f'Wheels directory: {wd}')
        else:
            C.warn('No wheels directory found. Will try online only.')

        C.header('[Phase 2] Diagnosing packages')
        failed = []
        optional_failed = []

        for imp, pip_name, desc in CRITICAL_PACKAGES:
            ok, err = self.check_import(imp)
            if ok:
                C.ok(desc)
            else:
                C.fail(f'{desc} ({pip_name})')
                failed.append((pip_name, err))

        m_ok, m_info = self.check_spacy_model()
        if m_ok:
            C.ok(f'en_core_web_sm ({m_info})')
        else:
            C.fail('en_core_web_sm')
            failed.append(('en_core_web_sm', m_info))

        for imp, pip_name, desc in OPTIONAL_PACKAGES:
            ok, err = self.check_import(imp)
            if ok:
                C.ok(desc)
            else:
                C.warn(f'{desc} ({pip_name}) — optional')
                optional_failed.append((pip_name, err))

        if not failed and not optional_failed:
            C.ok('All packages working! Checking NLTK data...')
            self.check_nltk_data()
            return 0

        C.header(f'[Phase 3] Repairing {len(failed) + len(optional_failed)} package(s)')
        failed_names = [n for n, _ in failed]

        # Step 3a: setuptools
        if 'setuptools' in failed_names:
            self.pip_install(['setuptools<81'], force=True)

        # Step 3b: Priority deps (colorama, typer)
        priority = [n for n in ['colorama', 'typer'] if n in failed_names]
        if priority:
            C.info(f'Installing priority deps: {", ".join(priority)}')
            self.pip_install(priority)

        # Step 3c: spaCy chain
        spacy_deps = [n for n in failed_names if n.lower() in
                      {'spacy', 'typer', 'cymem', 'murmurhash', 'preshed',
                       'blis', 'srsly', 'thinc'}]
        if spacy_deps:
            C.info('Reinstalling spaCy + all C dependencies...')
            self.pip_install(SPACY_CHAIN, force=True)

        # Step 3d: Remaining critical
        skip = {'setuptools', 'colorama', 'typer', 'spacy', 'cymem',
                'murmurhash', 'preshed', 'blis', 'srsly', 'thinc', 'en_core_web_sm'}
        for pip_name, _ in failed:
            if pip_name.lower() in skip:
                continue
            C.info(f'Reinstalling {pip_name}...')
            ok, method = self.pip_install(pip_name, force=True)
            if ok:
                C.ok(f'{pip_name} ({method})')
            else:
                C.fail(f'{pip_name}: {method}')

        # Step 3e: spaCy model
        if 'en_core_web_sm' in failed_names:
            C.info('Reinstalling spaCy English model...')
            installed = False
            for wd in self.find_wheels_dirs():
                for whl in glob.glob(os.path.join(wd, 'en_core_web_sm*.whl')):
                    ok, _ = self.pip_install(whl, force=True)
                    if ok:
                        installed = True
                        break
                if installed:
                    break
            if not installed:
                try:
                    subprocess.run(
                        [self._python_exe, '-m', 'spacy', 'download', 'en_core_web_sm'],
                        capture_output=True, text=True, timeout=120
                    )
                except Exception:
                    pass

        # Step 3f: Optional packages
        if optional_failed:
            C.info('Installing optional packages...')
            # sspilib before Windows auth
            opt_names = {n for n, _ in optional_failed}
            if 'requests-ntlm' in opt_names or 'requests-negotiate-sspi' in opt_names:
                self.pip_install('sspilib')
            if 'pywin32' in opt_names:
                self.pip_install('pywin32')
            if 'msal' in opt_names:
                self.pip_install('PyJWT')

            for pip_name, _ in optional_failed:
                ok, method = self.pip_install(pip_name, force=True)
                if ok:
                    C.ok(f'{pip_name} ({method})')
                else:
                    C.warn(f'{pip_name} — not available')

        C.header('[Phase 4] NLTK Data')
        self.check_nltk_data()

        C.header('[Phase 5] Final Verification')
        final_fail = 0
        for imp, pip_name, desc in CRITICAL_PACKAGES:
            ok, err = self.check_import(imp)
            if ok:
                C.ok(desc)
            else:
                C.fail(f'{desc} — STILL BROKEN')
                final_fail += 1

        m_ok, m_info = self.check_spacy_model()
        if m_ok:
            C.ok(f'en_core_web_sm ({m_info})')
        else:
            C.fail('en_core_web_sm — STILL BROKEN')
            final_fail += 1

        return final_fail


# ═══════════════════════════════════════════════════════════════════════
# class AEGISManager — Main orchestrator (menu + all features)
# ═══════════════════════════════════════════════════════════════════════

class AEGISManager:
    """Main AEGIS Manager — menu system and all feature implementations."""

    def __init__(self):
        self.install_dir = self._find_install_dir()
        self.github = GitHubClient()
        self.backup = BackupManager(self.install_dir)
        self.server = ServerManager(self.install_dir)
        self.packages = PackageManager(self.install_dir)

        # Init log
        log_path = os.path.join(self.install_dir, LOG_FILE)
        C.init_log(log_path)

    def _find_install_dir(self):
        """Find the AEGIS installation directory."""
        # Check current directory
        cwd = os.getcwd()
        if os.path.isfile(os.path.join(cwd, 'app.py')) and os.path.isdir(os.path.join(cwd, 'static')):
            return cwd

        # Check script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isfile(os.path.join(script_dir, 'app.py')) and os.path.isdir(os.path.join(script_dir, 'static')):
            return script_dir

        # Check known locations
        known = [
            r"C:\Users\M26402\OneDrive - NGC\Desktop\Doc Review\AEGIS",
            os.path.expanduser("~/Desktop/Work_Tools/TechWriterReview"),
        ]
        for path in known:
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'app.py')):
                return path

        # Fall back to script directory
        return script_dir

    def _get_local_version(self):
        """Get installed AEGIS version."""
        vpath = os.path.join(self.install_dir, 'version.json')
        try:
            with open(vpath, 'r', encoding='utf-8', errors='replace') as f:
                return json.load(f).get('version', 'unknown')
        except Exception:
            return 'not installed'

    def _is_source_file(self, path):
        """Check if a path is a syncable source file."""
        ext = os.path.splitext(path)[1].lower()
        return ext in SOURCE_EXTENSIONS

    def _should_preserve(self, rel_path):
        """Check if a file should be preserved (user data)."""
        norm = rel_path.replace('\\', '/')
        # Check exact matches
        if norm in USER_DATA_PRESERVE:
            return True
        # Check directory prefixes
        for pdir in PRESERVE_DIRS:
            if norm.startswith(pdir + '/') or norm == pdir:
                return True
        return False

    # ──────────────────────────────────────────────────────────────
    # MENU
    # ──────────────────────────────────────────────────────────────

    def run(self):
        """Main menu loop."""
        while True:
            self._show_menu()
            choice = C.prompt('Choice: ')

            actions = {
                '1': self.update_aegis,
                '2': self.full_sync,
                '3': self.health_check,
                '4': self.repair,
                '5': self.create_backup,
                '6': self.restore_backup,
                '7': self.server_menu,
                '8': self.fresh_install,
                '9': self.package_distribution,
                '10': self.diagnostics,
                '11': self.self_update,
                '0': self._exit,
            }

            action = actions.get(choice)
            if action:
                try:
                    if action == self._exit:
                        break
                    action()
                except KeyboardInterrupt:
                    C._write(f'\n\n  {C.YELLOW}Interrupted.{C.RESET}')
                except Exception as e:
                    C.fail(f'Error: {e}')
                C._write('')
                try:
                    input(f'  {C.DIM}Press Enter to continue...{C.RESET}')
                except (EOFError, KeyboardInterrupt):
                    pass
            else:
                C.warn('Invalid choice. Enter 0-11.')

    def _show_menu(self):
        """Display the main menu."""
        version = self._get_local_version()
        running, _ = self.server.is_running()
        server_status = f'{C.GREEN}Running{C.RESET}' if running else f'{C.RED}Stopped{C.RESET}'
        date_str = datetime.now().strftime('%Y-%m-%d')

        # Clear screen (optional)
        if sys.platform == 'win32':
            os.system('cls')
        else:
            os.system('clear')

        C._write('')
        C._write(f'  {C.GOLD}╔══════════════════════════════════════════════════════════════╗{C.RESET}')
        C._write(f'  {C.GOLD}║{C.RESET}  {C.BOLD}{C.WHITE}AEGIS Manager v{MANAGER_VERSION}{C.RESET}                                      {C.GOLD}║{C.RESET}')
        C._write(f'  {C.GOLD}║{C.RESET}  Installed: {C.CYAN}v{version}{C.RESET}  │  Server: {server_status}  │  {date_str}  {C.GOLD}║{C.RESET}')
        C._write(f'  {C.GOLD}╚══════════════════════════════════════════════════════════════╝{C.RESET}')
        C._write('')
        C._write(f'   {C.BOLD}1.{C.RESET}  Update AEGIS          {C.DIM}Pull latest from GitHub{C.RESET}')
        C._write(f'   {C.BOLD}2.{C.RESET}  Full Sync              {C.DIM}Download ALL source files{C.RESET}')
        C._write(f'   {C.BOLD}3.{C.RESET}  Health Check           {C.DIM}Verify packages & deps{C.RESET}')
        C._write(f'   {C.BOLD}4.{C.RESET}  Repair                 {C.DIM}Fix broken packages{C.RESET}')
        C._write(f'   {C.BOLD}5.{C.RESET}  Backup                 {C.DIM}Create snapshot{C.RESET}')
        C._write(f'   {C.BOLD}6.{C.RESET}  Restore                {C.DIM}Restore from backup{C.RESET}')
        C._write(f'   {C.BOLD}7.{C.RESET}  Server                 {C.DIM}Start / Stop / Restart{C.RESET}')
        C._write(f'   {C.BOLD}8.{C.RESET}  Fresh Install           {C.DIM}Full setup from scratch{C.RESET}')
        C._write(f'   {C.BOLD}9.{C.RESET}  Package                {C.DIM}Create distribution archive{C.RESET}')
        C._write(f'  {C.BOLD}10.{C.RESET}  Diagnostics            {C.DIM}System info & export{C.RESET}')
        C._write(f'  {C.BOLD}11.{C.RESET}  Self-Update             {C.DIM}Update this manager{C.RESET}')
        C._write(f'   {C.BOLD}0.{C.RESET}  Exit')
        C._write('')

    def _exit(self):
        C.close_log()

    # ──────────────────────────────────────────────────────────────
    # 1. UPDATE AEGIS
    # ──────────────────────────────────────────────────────────────

    def update_aegis(self):
        """Pull latest version from GitHub."""
        C.banner('Update AEGIS', 'Pull changed files from GitHub')

        # Check connectivity
        C.info('Checking GitHub connectivity...')
        ok, info = self.github.check_connectivity()
        if not ok:
            C.fail(f'Cannot reach GitHub: {info.get("error", "unknown")}')
            return
        C.ok(f'Connected (API calls remaining: {info.get("remaining", "?")})')

        # Get remote version
        C.info('Fetching remote version...')
        remote_ver = self.github.get_remote_version()
        local_ver = self._get_local_version()

        if remote_ver:
            rv = remote_ver.get('version', '?')
            C.info(f'Local:  v{local_ver}')
            C.info(f'Remote: v{rv}')

            if rv == local_ver:
                C._write(f'\n    {C.GREEN}Already up to date!{C.RESET}')
                inp = C.prompt('Force re-download anyway? (y/N): ')
                if inp.lower() != 'y':
                    return
        else:
            C.warn('Could not fetch remote version. Proceeding anyway...')

        # Get file tree via Git Trees API
        C.info('Fetching file tree from GitHub...')
        sha = self.github.get_head_sha()
        if not sha:
            C.fail('Could not get HEAD commit SHA')
            return

        tree = self.github.get_file_tree(sha)
        if not tree:
            C.fail('Could not get file tree')
            return

        C.info(f'Repository has {len(tree)} total files')

        # Filter to source files, exclude preserved
        to_download = []
        for f in tree:
            path = f['path']
            if not self._is_source_file(path):
                continue
            if self._should_preserve(path):
                continue
            to_download.append(path)

        C.info(f'{len(to_download)} source files to check')

        # Build SHA lookup from tree for comparison
        tree_sha_map = {}
        for f in tree:
            tree_sha_map[f['path']] = f['sha']

        # Compare local files against Git blob SHAs
        C.info('Comparing local files with remote...')
        changed = []
        new_files = []
        up_to_date = 0
        for path in to_download:
            local = os.path.join(self.install_dir, path)
            if not os.path.isfile(local):
                new_files.append(path)
            else:
                # Compute Git blob SHA for local file: sha1("blob {size}\0{content}")
                try:
                    with open(local, 'rb') as lf:
                        content = lf.read()
                    header = f'blob {len(content)}\0'.encode('utf-8')
                    local_sha = hashlib.sha1(header + content).hexdigest()
                    if local_sha != tree_sha_map.get(path, ''):
                        changed.append(path)
                    else:
                        up_to_date += 1
                except Exception:
                    changed.append(path)  # If we can't read it, re-download

        total = len(changed) + len(new_files)
        C.ok(f'{up_to_date} files already up to date')
        if new_files:
            C.info(f'{len(new_files)} new files')
        if changed:
            C.info(f'{len(changed)} changed files')

        if total == 0:
            C._write(f'\n    {C.GREEN}Everything is up to date!{C.RESET}')
            return

        C.info(f'Downloading {total} files...')

        # Backup changed files before overwriting
        files_to_download = changed + new_files
        C.info('Creating pre-update backup...')
        bdir, bcount = self.backup.create_backup(
            files=[p for p in changed if os.path.isfile(os.path.join(self.install_dir, p))],
            label='pre_update'
        )
        C.ok(f'Backed up {bcount} files to {os.path.basename(bdir)}')

        # Download only changed + new files
        success = 0
        failed = 0
        for i, path in enumerate(files_to_download):
            C.progress_bar(i + 1, total, os.path.basename(path)[:30])
            dest = os.path.join(self.install_dir, path)
            if self.github.download_raw_file(path, dest):
                success += 1
            else:
                failed += 1

        C._write('')
        C.ok(f'Downloaded: {success}/{total}')
        if failed:
            C.warn(f'{failed} files failed to download')

        # Ensure __init__.py in Python package dirs
        self._ensure_init_files()

        # Auto-restart server if Python files were updated
        python_updated = any(p.endswith('.py') for p in files_to_download)
        self._auto_restart_if_needed(python_updated, success)

    # ──────────────────────────────────────────────────────────────
    # 2. FULL SYNC
    # ──────────────────────────────────────────────────────────────

    def full_sync(self):
        """Download ALL source files from GitHub."""
        C.banner('Full Sync', 'Download every source file from GitHub')

        C.warn('This will download ALL source files from the repository.')
        C.warn('User data (scan_history.db, config.json, patterns, etc.) is preserved.')
        inp = C.prompt('Continue? (y/N): ')
        if inp.lower() != 'y':
            return

        C.info('Fetching complete file tree...')
        tree = self.github.get_file_tree()
        if not tree:
            C.fail('Could not get file tree')
            return

        # Filter to source files
        to_download = []
        for f in tree:
            path = f['path']
            if not self._is_source_file(path):
                continue
            if self._should_preserve(path):
                continue
            to_download.append(path)

        C.info(f'{len(to_download)} source files to download')

        # Backup
        C.info('Creating pre-sync backup...')
        bdir, bcount = self.backup.create_backup(label='pre_full_sync')
        C.ok(f'Backed up {bcount} files')

        # Create directories
        C.info('Creating directory structure...')
        for d in REQUIRED_DIRS:
            full = os.path.join(self.install_dir, d)
            os.makedirs(full, exist_ok=True)

        # Download all
        total = len(to_download)
        success = 0
        failed = 0
        for i, path in enumerate(to_download):
            C.progress_bar(i + 1, total, os.path.basename(path)[:30])
            dest = os.path.join(self.install_dir, path)
            if self.github.download_raw_file(path, dest):
                success += 1
            else:
                failed += 1

        C._write('')
        C.ok(f'Downloaded: {success}/{total}')
        if failed:
            C.warn(f'{failed} files failed')

        self._ensure_init_files()

        # Full sync always includes Python files — auto-restart
        self._auto_restart_if_needed(True, success)

    # ──────────────────────────────────────────────────────────────
    # 3. HEALTH CHECK
    # ──────────────────────────────────────────────────────────────

    def health_check(self):
        """Quick health check."""
        C.banner('Health Check', 'Verify packages & dependencies')

        c_pass, c_fail, o_pass, o_fail, details = self.packages.health_check()

        C.header('Critical Packages')
        for desc, pip_name, status, err in details['critical']:
            if status == 'ok':
                C.ok(desc)
            else:
                C.fail(f'{desc} ({pip_name})')
                if err:
                    C._write(f'         {C.RED}{err[:100]}{C.RESET}')

        C.header('spaCy Model')
        m_status, m_info = details['model']
        if m_status == 'ok':
            C.ok(f'en_core_web_sm ({m_info})')
        else:
            C.fail(f'en_core_web_sm: {m_info}')

        C.header('Optional Packages')
        for desc, pip_name, status, err in details['optional']:
            if status == 'ok':
                C.ok(desc)
            else:
                C.warn(f'{desc} ({pip_name})')

        C.header('Server Status')
        running, vinfo = self.server.is_running()
        if running:
            sv = vinfo.get('version', '?') if vinfo else '?'
            C.ok(f'AEGIS server running (v{sv})')
        else:
            C.warn('AEGIS server not running')

        C.header('GitHub Connectivity')
        ok, info = self.github.check_connectivity()
        if ok:
            C.ok(f'GitHub reachable (API calls remaining: {info.get("remaining", "?")})')
        else:
            C.warn(f'GitHub not reachable: {info.get("error", "?")}')

        # Summary
        C._write('')
        total_pass = c_pass + o_pass
        total_fail = c_fail + o_fail
        if c_fail == 0:
            C._write(f'  {C.GREEN}{C.BOLD}All {c_pass} critical packages working!{C.RESET}')
        else:
            C._write(f'  {C.RED}{c_fail} critical package(s) broken — run Repair (option 4){C.RESET}')
        if o_fail > 0:
            C._write(f'  {C.YELLOW}{o_fail} optional package(s) not available{C.RESET}')

    # ──────────────────────────────────────────────────────────────
    # 4. REPAIR
    # ──────────────────────────────────────────────────────────────

    def repair(self):
        """Full 5-phase repair."""
        C.banner('Repair', 'Full 5-phase package repair')

        final_fail = self.packages.full_repair()

        C._write('')
        if final_fail == 0:
            C._write(f'  {C.GREEN}{C.BOLD}All packages repaired successfully!{C.RESET}')
        else:
            C._write(f'  {C.RED}{final_fail} critical package(s) still broken.{C.RESET}')
            C._write(f'  Common fixes:')
            C._write(f'    1. Missing wheel → download .whl to wheels/ and re-run')
            C._write(f'    2. DLL error → install Visual C++ Redistributable')
            C._write(f'    3. Corrupted → delete python/Lib/site-packages and re-run OneClick')

    # ──────────────────────────────────────────────────────────────
    # 5. BACKUP
    # ──────────────────────────────────────────────────────────────

    def create_backup(self):
        """Create a manual backup snapshot."""
        C.banner('Backup', 'Create snapshot of current installation')

        label = C.prompt('Backup label (default: manual): ') or 'manual'
        label = label.replace(' ', '_')[:30]

        C.info('Scanning source files...')
        bdir, bcount = self.backup.create_backup(label=label)

        C.ok(f'Backed up {bcount} files')
        C.info(f'Location: {bdir}')

    # ──────────────────────────────────────────────────────────────
    # 6. RESTORE
    # ──────────────────────────────────────────────────────────────

    def restore_backup(self):
        """Restore from a previous backup."""
        C.banner('Restore', 'Restore from backup snapshot')

        backups = self.backup.list_backups()
        if not backups:
            C.warn('No backups found')
            return

        C._write(f'\n  Available backups:')
        C._write(f'  {"#":>3}  {"Version":>8}  {"Files":>5}  {"Size":>6}  {"Date":<20}  Name')
        C._write(f'  {"─"*3}  {"─"*8}  {"─"*5}  {"─"*6}  {"─"*20}  {"─"*30}')

        for i, b in enumerate(backups):
            C._write(f'  {i+1:>3}  {b["version"]:>8}  {b["file_count"]:>5}  '
                     f'{b["size_mb"]:>5.1f}M  {b["created_at"]:<20}  {b["name"]}')

        choice = C.prompt(f'\nRestore which backup? (1-{len(backups)}, 0=cancel): ')
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(backups):
                return
        except ValueError:
            return

        selected = backups[idx]
        C.warn(f'This will restore {selected["file_count"]} files from v{selected["version"]}')
        confirm = C.prompt('Are you sure? (y/N): ')
        if confirm.lower() != 'y':
            return

        restored, errors = self.backup.restore_backup(selected['name'])
        C.ok(f'Restored {restored} files')
        if errors:
            C.warn(f'{errors} files had errors')

        self._show_restart_reminder()

    # ──────────────────────────────────────────────────────────────
    # 7. SERVER MANAGEMENT
    # ──────────────────────────────────────────────────────────────

    def server_menu(self):
        """Server management sub-menu."""
        C.banner('Server Management')

        running, vinfo = self.server.is_running()
        if running:
            sv = vinfo.get('version', '?') if vinfo else '?'
            C.ok(f'Server is running (v{sv})')
        else:
            C.info('Server is not running')

        C._write('')
        C._write(f'  1. Start')
        C._write(f'  2. Stop')
        C._write(f'  3. Restart')
        C._write(f'  4. Status')
        C._write(f'  0. Back')

        choice = C.prompt('Choice: ')

        if choice == '1':
            self.server.start()
        elif choice == '2':
            self.server.stop()
        elif choice == '3':
            self.server.restart()
        elif choice == '4':
            running, vinfo = self.server.is_running()
            if running:
                C.ok(f'Server is running')
                if vinfo:
                    for k, v in vinfo.items():
                        C.info(f'  {k}: {v}')
            else:
                C.warn('Server is not running')

    # ──────────────────────────────────────────────────────────────
    # 8. FRESH INSTALL
    # ──────────────────────────────────────────────────────────────

    def fresh_install(self):
        """Complete fresh install from scratch."""
        C.banner('Fresh Install', 'Full AEGIS setup from scratch')

        C.warn('This will download ALL source files and install all packages.')
        C.warn('Existing user data (scan_history.db, config.json) will be preserved.')
        confirm = C.prompt('Continue? (y/N): ')
        if confirm.lower() != 'y':
            return

        # Step 1: Create directories
        C.header('Step 1: Creating directory structure')
        for d in REQUIRED_DIRS:
            full = os.path.join(self.install_dir, d)
            os.makedirs(full, exist_ok=True)
            # Add __init__.py for Python packages
            if not d.startswith('static') and not d.startswith('templates') \
                    and not d.startswith('dictionaries') and not d.startswith('packaging') \
                    and not d == 'logs' and not d == 'temp' and not d == 'backups' \
                    and not d == 'updates':
                init = os.path.join(full, '__init__.py')
                if not os.path.isfile(init):
                    with open(init, 'w') as f:
                        f.write('')
        C.ok(f'Created {len(REQUIRED_DIRS)} directories')

        # Step 2: Download all source files
        C.header('Step 2: Downloading source files from GitHub')
        C.info('Fetching file tree...')
        tree = self.github.get_file_tree()
        if not tree:
            C.fail('Could not get file tree. Check internet connection.')
            return

        to_download = [f['path'] for f in tree
                       if self._is_source_file(f['path'])
                       and not self._should_preserve(f['path'])]

        total = len(to_download)
        C.info(f'{total} files to download')

        success = 0
        failed = 0
        for i, path in enumerate(to_download):
            C.progress_bar(i + 1, total, os.path.basename(path)[:30])
            dest = os.path.join(self.install_dir, path)
            if self.github.download_raw_file(path, dest):
                success += 1
            else:
                failed += 1

        C._write('')
        C.ok(f'Downloaded {success}/{total} files')

        # Step 3: Install packages
        C.header('Step 3: Installing Python packages')
        self.packages.preflight_setuptools()

        # Install from requirements.txt if available
        req_file = os.path.join(self.install_dir, 'requirements.txt')
        if os.path.isfile(req_file):
            C.info('Installing from requirements.txt...')
            wheels = self.packages.find_wheels_dirs()
            cmd = [self.packages._python_exe, '-m', 'pip', 'install',
                   '-r', req_file, '--no-warn-script-location']
            for wd in wheels:
                cmd.extend(['--find-links', wd])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    C.ok('Requirements installed')
                else:
                    C.warn('Some requirements failed — will repair individually')
            except Exception as e:
                C.warn(f'Requirements install error: {e}')

        # Step 4: NLTK data
        C.header('Step 4: NLTK data')
        self.packages.check_nltk_data()

        # Step 5: Verification
        C.header('Step 5: Verification')
        c_pass, c_fail, _, _, _ = self.packages.health_check()
        if c_fail > 0:
            C.warn(f'{c_fail} packages need repair. Run Repair (option 4).')
        else:
            C.ok('All critical packages verified!')

        # Create Start_AEGIS.bat if missing on Windows
        if sys.platform == 'win32':
            bat_path = os.path.join(self.install_dir, 'Start_AEGIS.bat')
            if not os.path.isfile(bat_path):
                C.info('Creating Start_AEGIS.bat...')
                self._create_start_bat(bat_path)

        C._write('')
        C._write(f'  {C.GREEN}{C.BOLD}Fresh install complete!{C.RESET}')
        self._show_restart_reminder()

    # ──────────────────────────────────────────────────────────────
    # 9. PACKAGE FOR DISTRIBUTION
    # ──────────────────────────────────────────────────────────────

    def package_distribution(self):
        """Create a ZIP archive for distribution."""
        C.banner('Package', 'Create distribution archive')

        version = self._get_local_version()
        default_name = f'AEGIS_v{version}_{datetime.now().strftime("%Y%m%d")}.zip'

        # Choose output location
        if sys.platform == 'win32':
            default_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        else:
            default_dir = os.path.expanduser('~/Desktop')

        C.info(f'Default output: {os.path.join(default_dir, default_name)}')
        custom = C.prompt('Custom filename (Enter for default): ')
        if custom:
            default_name = custom if custom.endswith('.zip') else custom + '.zip'

        output_path = os.path.join(default_dir, default_name)

        # Collect files
        C.info('Scanning installation...')
        files_to_pack = []
        total_size = 0

        for root, dirs, filenames in os.walk(self.install_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in PACKAGE_EXCLUDE
                       and not d.startswith('.')]

            rel_root = os.path.relpath(root, self.install_dir)
            if rel_root == '.':
                rel_root = ''

            for fn in filenames:
                if fn.startswith('.') or fn.endswith('.pyc'):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.join(rel_root, fn) if rel_root else fn
                size = os.path.getsize(full)
                files_to_pack.append((full, rel, size))
                total_size += size

        C.info(f'{len(files_to_pack)} files, {total_size / (1024*1024):.1f} MB total')
        confirm = C.prompt('Create archive? (y/N): ')
        if confirm.lower() != 'y':
            return

        # Create ZIP
        C.info('Creating archive...')
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, (full, rel, _) in enumerate(files_to_pack):
                C.progress_bar(i + 1, len(files_to_pack), '')
                zf.write(full, os.path.join('AEGIS', rel))

        archive_size = os.path.getsize(output_path)
        C._write('')
        C.ok(f'Archive created: {output_path}')
        C.info(f'Archive size: {archive_size / (1024*1024):.1f} MB')

    # ──────────────────────────────────────────────────────────────
    # 10. DIAGNOSTICS
    # ──────────────────────────────────────────────────────────────

    def diagnostics(self):
        """System diagnostics and info export."""
        C.banner('Diagnostics')

        C._write(f'  1. System Info')
        C._write(f'  2. Installed Packages')
        C._write(f'  3. Auth Capabilities')
        C._write(f'  4. GitHub Connectivity')
        C._write(f'  5. Export All to JSON')
        C._write(f'  0. Back')

        choice = C.prompt('Choice: ')

        if choice == '1':
            self._diag_system_info()
        elif choice == '2':
            self._diag_packages()
        elif choice == '3':
            self._diag_auth()
        elif choice == '4':
            self._diag_github()
        elif choice == '5':
            self._diag_export()

    def _diag_system_info(self):
        """Show system information."""
        C.header('System Information')
        C.info(f'Platform:       {platform.platform()}')
        C.info(f'Python:         {sys.version.split()[0]}')
        C.info(f'Python exe:     {sys.executable}')
        C.info(f'Architecture:   {platform.machine()}')
        C.info(f'AEGIS version:  {self._get_local_version()}')
        C.info(f'Install dir:    {self.install_dir}')

        # Disk space
        try:
            if hasattr(shutil, 'disk_usage'):
                usage = shutil.disk_usage(self.install_dir)
                C.info(f'Disk free:      {usage.free / (1024**3):.1f} GB')
                C.info(f'Disk total:     {usage.total / (1024**3):.1f} GB')
        except Exception:
            pass

        # Install size
        total = 0
        for root, dirs, files in os.walk(self.install_dir):
            dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', 'node_modules'}]
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        C.info(f'Install size:   {total / (1024**2):.0f} MB')

    def _diag_packages(self):
        """List installed packages."""
        C.header('Installed Packages (pip list)')
        try:
            result = subprocess.run(
                [self.packages._python_exe, '-m', 'pip', 'list', '--format=columns'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[:50]:
                    C._write(f'    {line}')
                total_lines = len(result.stdout.strip().split('\n'))
                if total_lines > 50:
                    C._write(f'    ... ({total_lines - 50} more)')
        except Exception as e:
            C.fail(f'Could not list packages: {e}')

    def _diag_auth(self):
        """Check authentication capabilities."""
        C.header('Authentication Capabilities')

        checks = [
            ('requests_negotiate_sspi', 'Windows SSO (Negotiate)'),
            ('requests_ntlm', 'Windows Domain Auth (NTLM)'),
            ('sspi', 'SSPI Preemptive Auth'),
            ('msal', 'SharePoint Online OAuth (MSAL)'),
            ('truststore', 'OS Certificate Store (truststore)'),
            ('playwright', 'Headless Browser (Playwright)'),
        ]

        for module, desc in checks:
            ok, err = self.packages.check_import(module)
            if ok:
                C.ok(desc)
            else:
                C.warn(f'{desc} — not available')

    def _diag_github(self):
        """Check GitHub connectivity."""
        C.header('GitHub Connectivity')
        ok, info = self.github.check_connectivity()
        if ok:
            C.ok(f'GitHub API reachable')
            C.info(f'Rate limit: {info.get("remaining", "?")}/{info.get("limit", "?")}')
            reset = info.get('reset')
            if reset:
                try:
                    reset_time = datetime.fromtimestamp(int(reset))
                    C.info(f'Resets at: {reset_time.strftime("%H:%M:%S")}')
                except Exception:
                    pass
        else:
            C.fail(f'Cannot reach GitHub: {info.get("error", "?")}')

        # Test raw download
        C.info('Testing raw file download...')
        remote_ver = self.github.get_remote_version()
        if remote_ver:
            C.ok(f'Raw download works (remote version: {remote_ver.get("version", "?")})')
        else:
            C.fail('Raw file download failed')

    def _diag_export(self):
        """Export diagnostics to JSON file."""
        C.header('Exporting Diagnostics')

        diag = {
            'timestamp': datetime.now().isoformat(),
            'manager_version': MANAGER_VERSION,
            'system': {
                'platform': platform.platform(),
                'python': sys.version,
                'executable': sys.executable,
                'architecture': platform.machine(),
            },
            'aegis': {
                'version': self._get_local_version(),
                'install_dir': self.install_dir,
            },
        }

        # Server status
        running, vinfo = self.server.is_running()
        diag['server'] = {
            'running': running,
            'version_info': vinfo,
        }

        # GitHub
        ok, ginfo = self.github.check_connectivity()
        diag['github'] = {
            'reachable': ok,
            'info': ginfo,
        }

        # Package health
        c_pass, c_fail, o_pass, o_fail, details = self.packages.health_check()
        diag['packages'] = {
            'critical_pass': c_pass,
            'critical_fail': c_fail,
            'optional_pass': o_pass,
            'optional_fail': o_fail,
        }

        # Disk
        try:
            usage = shutil.disk_usage(self.install_dir)
            diag['disk'] = {
                'free_gb': round(usage.free / (1024**3), 1),
                'total_gb': round(usage.total / (1024**3), 1),
            }
        except Exception:
            pass

        output = os.path.join(self.install_dir,
                              f'aegis_diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(diag, f, indent=2, default=str)

        C.ok(f'Diagnostics exported: {output}')

    # ──────────────────────────────────────────────────────────────
    # 11. SELF-UPDATE
    # ──────────────────────────────────────────────────────────────

    def self_update(self):
        """Update this manager tool from GitHub."""
        C.banner('Self-Update', 'Update AEGIS Manager from GitHub')

        C.info('Checking for new version...')

        # Download latest aegis_manager.py
        try:
            url = f"{BASE_RAW_URL}/aegis_manager.py"
            data = self.github._request(url, accept='*/*')
            new_content = data.decode('utf-8', errors='replace')
        except Exception as e:
            C.fail(f'Could not download: {e}')
            return

        # Extract version from new file
        new_version = MANAGER_VERSION
        for line in new_content.split('\n')[:50]:
            if line.strip().startswith('MANAGER_VERSION'):
                try:
                    new_version = line.split('=')[1].strip().strip('"').strip("'")
                except Exception:
                    pass
                break

        # Compare
        current_path = os.path.abspath(__file__)
        current_hash = BackupManager._file_hash(current_path)

        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w',
                                          encoding='utf-8')
        tmp.write(new_content)
        tmp.close()
        new_hash = BackupManager._file_hash(tmp.name)

        if current_hash == new_hash:
            C.ok(f'Already up to date (v{MANAGER_VERSION})')
            os.unlink(tmp.name)
            return

        C.info(f'Current: v{MANAGER_VERSION}')
        C.info(f'New:     v{new_version}')
        confirm = C.prompt('Update? (y/N): ')
        if confirm.lower() != 'y':
            os.unlink(tmp.name)
            return

        # Backup current
        backup_path = current_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        try:
            shutil.copy2(current_path, backup_path)
            C.ok(f'Backed up current to: {os.path.basename(backup_path)}')
        except Exception as e:
            C.warn(f'Could not backup: {e}')

        # Replace
        try:
            shutil.move(tmp.name, current_path)
            C.ok(f'Updated to v{new_version}!')
            C._write(f'\n  {C.YELLOW}Please restart AEGIS Manager for changes to take effect.{C.RESET}')
        except Exception as e:
            C.fail(f'Could not replace file: {e}')
            C.info(f'New version saved at: {tmp.name}')

    # ──────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ──────────────────────────────────────────────────────────────

    def _ensure_init_files(self):
        """Ensure __init__.py exists in all Python package directories."""
        python_dirs = [
            'routes', 'proposal_compare', 'hyperlink_validator',
            'statement_forge', 'document_compare', 'portfolio',
            'nlp', 'nlp/languagetool', 'nlp/readability', 'nlp/semantics',
            'nlp/spacy', 'nlp/spelling', 'nlp/style', 'nlp/verbs',
        ]
        for d in python_dirs:
            full = os.path.join(self.install_dir, d)
            if os.path.isdir(full):
                init = os.path.join(full, '__init__.py')
                if not os.path.isfile(init):
                    with open(init, 'w') as f:
                        f.write('')

    def _auto_restart_if_needed(self, python_updated, files_downloaded):
        """Auto-restart the AEGIS server after updates that include Python files.

        Args:
            python_updated: True if any .py files were in the download set
            files_downloaded: Number of files successfully downloaded
        """
        if files_downloaded == 0:
            C.info('No files were downloaded — no restart needed.')
            return

        if not python_updated:
            C._write('')
            C.ok('Update complete (CSS/JS/HTML only — no restart needed).')
            C.info('Refresh your browser to see changes.')
            return

        # Python files were updated — server MUST restart for changes to take effect
        C._write('')
        C._write(f'  {C.GOLD}╔══════════════════════════════════════════════════════╗{C.RESET}')
        C._write(f'  {C.GOLD}║{C.RESET}                                                      {C.GOLD}║{C.RESET}')
        C._write(f'  {C.GOLD}║{C.RESET}   {C.BOLD}Python files updated — restarting server...{C.RESET}        {C.GOLD}║{C.RESET}')
        C._write(f'  {C.GOLD}║{C.RESET}                                                      {C.GOLD}║{C.RESET}')
        C._write(f'  {C.GOLD}╚══════════════════════════════════════════════════════╝{C.RESET}')
        C._write('')

        running, _ = self.server.is_running()
        if not running:
            C.info('Server is not currently running — starting it now...')
            started = self.server.start()
            if started:
                C.ok('Server started successfully with updated code!')
            else:
                C.warn('Could not start server automatically.')
                C.info('Start manually: double-click Start_AEGIS.bat')
            return

        # Server is running — restart it
        C.info('Stopping current server...')
        self.server.stop()

        # Wait for port to fully release
        C.info('Waiting for port to clear...')
        for i in range(5):
            time.sleep(1)
            running, _ = self.server.is_running()
            if not running:
                break
        else:
            C.warn('Port 5050 may still be in use — attempting start anyway')
            time.sleep(1)

        C.info('Starting server with updated code...')
        started = self.server.start()
        if started:
            C.ok('Server restarted successfully with updated code!')
            C._write('')
            C.info('Refresh your browser to see changes.')
        else:
            C.warn('Server did not respond after restart.')
            C.info('Try starting manually: double-click Start_AEGIS.bat')

    def _show_restart_reminder(self):
        """Legacy: Show server restart reminder (kept for backward compat)."""
        # Replaced by _auto_restart_if_needed() in v6.3.1
        # Kept as a no-op in case any external code calls it
        self._auto_restart_if_needed(True, 1)

    def _create_start_bat(self, path):
        """Create a basic Start_AEGIS.bat for Windows."""
        content = '''@echo off
title AEGIS
echo Starting AEGIS...
cd /d "%~dp0"

if exist "python\\python.exe" (
    set PYTHON=python\\python.exe
) else (
    set PYTHON=python
)

REM Kill any existing process on port 5050
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5050" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Starting server...
start "" "%PYTHON%" app.py

REM Wait for server to start
set /a count=0
:wait_loop
set /a count+=1
if %count% gtr 30 goto timeout
timeout /t 1 /nobreak >nul
curl -s http://localhost:5050/api/version >nul 2>&1
if errorlevel 1 goto wait_loop

echo Server started!
start "" "http://localhost:5050"
exit /b 0

:timeout
echo Server did not start in 30 seconds.
echo Check the terminal for errors.
pause
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        C.ok('Created Start_AEGIS.bat')


# ═══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main():
    try:
        manager = AEGISManager()
        manager.run()
    except KeyboardInterrupt:
        print(f'\n\n  Goodbye!')
    except Exception as e:
        print(f'\n  FATAL ERROR: {e}')
        import traceback
        traceback.print_exc()
        input('\n  Press Enter to exit...')
    finally:
        ColorOutput.close_log()


if __name__ == '__main__':
    main()
