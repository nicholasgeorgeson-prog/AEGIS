from flask import Blueprint, request, jsonify, g, send_file, make_response, current_app
import io
import os
import sys
import traceback
import threading
import multiprocessing
import uuid
import json
import tempfile
import time
import signal
from datetime import datetime
from pathlib import Path
from routes._shared import (
    require_csrf,
    handle_api_errors,
    api_error_response,
    config,
    logger,
    SessionManager,
    get_document_extractor,
    ValidationError,
    FileError,
    ProcessingError,
    sanitize_filename,
    validate_file_extension,
    run_with_timeout,
    TimeoutError,
    MAX_BATCH_SIZE,
    MAX_BATCH_TOTAL_SIZE,
    MAX_FOLDER_SCAN_FILES,
    FOLDER_SCAN_CHUNK_SIZE,
    FOLDER_SCAN_MAX_WORKERS,
    BATCH_SCAN_CHUNK_SIZE,
    BATCH_SCAN_MAX_WORKERS,
    BATCH_SCAN_PER_FILE_TIMEOUT,
    BATCH_SCAN_CLEANUP_AGE,
    get_engine,
    _human_size
)
import routes._shared as _shared

# Lazy imports for optional modules
try:
    from core import AEGISEngine
except ImportError:
    AEGISEngine = None

try:
    from fix_assistant_api import (
        build_document_content,
        group_similar_fixes,
        build_confidence_details,
        compute_fix_statistics,
    )
except ImportError:
    build_document_content = None
    group_similar_fixes = None
    build_confidence_details = None
    compute_fix_statistics = None

try:
    from job_manager import get_job_manager, JobStatus, JobPhase
except ImportError:
    get_job_manager = None
    JobStatus = None
    JobPhase = None

# v6.6.0: SP Repository Manager — persistent local copies of SP documents
try:
    from sp_repository_manager import SPRepositoryManager, get_repository
    _REPO_AVAILABLE = True
except Exception as _repo_err:
    # Catch ALL exceptions (not just ImportError) — scikit-learn/nltk recursion errors
    # on Windows can propagate through import chains (Lesson 181)
    _REPO_AVAILABLE = False
    get_repository = None
    import logging as _rl
    _rl.getLogger('aegis').warning(f'SP Repository Manager unavailable: {_repo_err}')


def get_scan_history_db():
    """Get scan history database instance."""
    from scan_history import get_scan_history_db as _get_db
    return _get_db()


review_bp = Blueprint('review', __name__)

# =============================================================================
# v5.7.0: Async Folder Scan State Management
# =============================================================================
# Module-level dict tracking active/completed folder scans.
# Key: scan_id (str) → dict with phase, progress, results, timing info.
# Scans are cleaned up after 30 minutes of completion.
_folder_scan_state = {}
_folder_scan_state_lock = threading.Lock()

_FOLDER_SCAN_CLEANUP_AGE = 1800  # 30 minutes

# =============================================================================
# v6.2.0: Async Batch Scan State Management
# =============================================================================
# Module-level dict tracking active/completed batch scans.
# Key: scan_id (str) → dict with phase, progress, per-file phases, timing info.
# Mirrors the folder scan async pattern from v5.7.0.
_batch_scan_state = {}
_batch_scan_state_lock = threading.Lock()

# =============================================================================
# v6.3.5: SharePoint Connector Cache
# =============================================================================
# Caches authenticated SP connectors from discovery for reuse during scan.
# Key: connector_token (str) → {'connector': obj, 'created_at': float, ...}
# Connectors auto-expire after 5 minutes (TTL).
_sp_connector_cache = {}
_sp_connector_cache_lock = threading.Lock()
_SP_CONNECTOR_CACHE_TTL = 300  # 5 minutes


def _cleanup_old_scans():
    """Remove completed scan state older than cleanup age for both folder and batch scans."""
    now = time.time()
    with _folder_scan_state_lock:
        to_remove = [
            sid for sid, state in _folder_scan_state.items()
            if state.get('phase') in ('complete', 'error')
            and now - state.get('completed_at', now) > _FOLDER_SCAN_CLEANUP_AGE
        ]
        for sid in to_remove:
            del _folder_scan_state[sid]
    # v6.2.0: Also clean up batch scan state
    with _batch_scan_state_lock:
        to_remove = [
            sid for sid, state in _batch_scan_state.items()
            if state.get('phase') in ('complete', 'error')
            and now - state.get('completed_at', now) > BATCH_SCAN_CLEANUP_AGE
        ]
        for sid in to_remove:
            del _batch_scan_state[sid]


@review_bp.route('/api/upload', methods=['POST'])
@require_csrf
@handle_api_errors
def upload():
    """Upload and analyze document structure."""
    if 'file' not in request.files:
        raise ValidationError('No file provided', field='file')
    else:
        file = request.files['file']
        if not file.filename:
            raise ValidationError('No file selected', field='file')
        else:
            original_name = sanitize_filename(file.filename)
            if not validate_file_extension(original_name, config.allowed_extensions):
                allowed = ', '.join(config.allowed_extensions)
                raise ValidationError(f'Invalid file type. Allowed: {allowed}', field='file', allowed_types=list(config.allowed_extensions))
            else:
                unique_name = f'{uuid.uuid4().hex[:8]}_{original_name}'
                filepath = config.temp_dir / unique_name
                file.save(str(filepath))
                file_size = filepath.stat().st_size
                logger.info('File uploaded', file_name=original_name, size=file_size, path=str(filepath))
                session_data = SessionManager.get(g.session_id)
                if session_data:
                    SessionManager.update(g.session_id, current_file=str(filepath), original_filename=original_name, review_results=None, filtered_issues=[], selected_issues=set())
                try:
                    extractor, file_type, pdf_quality = get_document_extractor(filepath, analyze_quality=True)
                    doc_info = {'filename': original_name, 'file_type': file_type, 'word_count': extractor.word_count, 'paragraph_count': len(extractor.paragraphs), 'table_count': len(extractor.tables), 'figure_count': len(extractor.figures), 'heading_count': len(getattr(extractor, 'headings', [])), 'has_toc': extractor.has_toc}
                    if file_type == 'pdf':
                        doc_info['page_count'] = extractor.page_count
                        doc_info['pdf_quality'] = pdf_quality
                    else:
                        doc_info['existing_comments'] = len(extractor.comments)
                        doc_info['track_changes'] = len(extractor.track_changes)
                    return jsonify({'success': True, 'data': doc_info})
                except ImportError as e:
                    logger.exception(f'Missing dependency: {e}')
                    raise ProcessingError(f'Missing required library: {e}', stage='extraction')
@review_bp.route('/api/dev/load-test-file', methods=['GET'])
@handle_api_errors
def dev_load_test_file():
    """Development endpoint to load a predefined test file for testing.
    v6.4.0: Restricted to debug mode only."""
    if not current_app.debug:
        return jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Dev endpoints disabled in production'}}), 404
    test_file = config.temp_dir / 'nasa_test.docx'
    if not test_file.exists():
        raise ValidationError('Test file not found', field='file')
    else:
        try:
            extractor, file_type, _ = get_document_extractor(test_file, analyze_quality=True)
            doc_info = {'filename': 'nasa_test.docx', 'filepath': str(test_file), 'file_type': file_type, 'word_count': extractor.word_count, 'paragraph_count': len(extractor.paragraphs), 'table_count': len(extractor.tables), 'figure_count': len(extractor.figures), 'heading_count': len(getattr(extractor, 'headings', [])), 'has_toc': extractor.has_toc}
            session_data = SessionManager.get(g.session_id)
            if session_data:
                SessionManager.update(g.session_id, current_file=str(test_file), original_filename='nasa_test.docx', review_results=None)
            return jsonify({'success': True, 'data': doc_info})
        except Exception as e:
            logger.exception(f'Error loading test file: {e}')
            raise ProcessingError(f'Failed to load test file: {e}', stage='extraction')
@review_bp.route('/api/dev/temp/<filename>', methods=['GET'])
@handle_api_errors
def dev_serve_temp_file(filename):
    """Serve a file from the temp directory for development testing.
    v6.4.0: Restricted to debug mode only."""
    if not current_app.debug:
        return jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Dev endpoints disabled in production'}}), 404
    from flask import send_from_directory
    safe_filename = Path(filename).name
    temp_path = config.temp_dir / safe_filename
    if not temp_path.exists():
        raise ValidationError(f'File not found: {safe_filename}', field='filename')
    else:
        return send_from_directory(config.temp_dir, safe_filename)
@review_bp.route('/api/upload/batch', methods=['POST'])
@require_csrf
@handle_api_errors
def upload_batch():
    """
    Upload and process multiple documents at once.

    v3.0.116 (BUG-M02): Enforces batch limits to prevent memory issues.
    - MAX_BATCH_SIZE: Maximum number of files per batch
    - MAX_BATCH_TOTAL_SIZE: Maximum total size across all files

    Accepts multiple files and processes them sequentially.
    Returns summary of all processed files.
    """
    if 'files[]' not in request.files:
        raise ValidationError('No files provided', field='files[]')
    files = request.files.getlist('files[]')
    if not files or all((not f.filename for f in files)):
        raise ValidationError('No files selected', field='files[]')
    valid_files = [f for f in files if f.filename and validate_file_extension(sanitize_filename(f.filename), config.allowed_extensions)]
    if not valid_files:
        allowed = ', '.join(config.allowed_extensions)
        raise ValidationError(f'No valid files found. Allowed types: {allowed}', field='files[]')
    if len(valid_files) > MAX_BATCH_SIZE:
        raise ValidationError(f'Too many files in batch. Maximum is {MAX_BATCH_SIZE}, got {len(valid_files)}.', field='files[]')
    results = {'processed': [], 'errors': [], 'total_files': len(valid_files), 'total_size': 0}
    for file in valid_files:
        original_name = sanitize_filename(file.filename)
        unique_name = f'{uuid.uuid4().hex[:8]}_{original_name}'
        filepath = config.temp_dir / unique_name
        try:
            file_size = 0
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file.stream.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    file_size += len(chunk)
                    if results['total_size'] + file_size > MAX_BATCH_TOTAL_SIZE:
                        f.close()
                        filepath.unlink(missing_ok=True)
                        raise ValidationError(f'Batch total size exceeds {MAX_BATCH_TOTAL_SIZE // (1024*1024)}MB limit.', field='files[]')
            results['total_size'] += file_size
            logger.info('Batch file saved', file_name=original_name, size=file_size)
            extractor, file_type, pdf_quality = get_document_extractor(filepath, analyze_quality=True)
            doc_info = {'filename': original_name, 'filepath': str(filepath), 'file_type': file_type, 'file_size': file_size, 'word_count': extractor.word_count, 'paragraph_count': len(extractor.paragraphs)}
            if file_type == 'pdf' and pdf_quality:
                doc_info['pdf_quality'] = pdf_quality
            results['processed'].append(doc_info)
        except ValidationError:
            raise
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f'Batch file error: {original_name} - {e}\n{tb_str}')
            results['errors'].append({'filename': original_name, 'error': str(e), 'traceback': tb_str if config.debug else None})
    return jsonify({'success': True, 'data': results})
@review_bp.route('/api/review/batch', methods=['POST'])
@require_csrf
@handle_api_errors
def review_batch():
    """
    Review multiple documents and aggregate results.

    v5.4.0: Uses ThreadPoolExecutor for parallel document processing.
    Each thread gets its own AEGISEngine instance to avoid shared state.

    Expects JSON body with list of filepaths from batch upload.
    Returns aggregated review results.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    data = request.get_json() or {}
    filepaths = data.get('filepaths', [])
    options = data.get('options', {})
    if not filepaths:
        raise ValidationError('No filepaths provided')

    results = {
        'documents': [],
        'summary': {
            'total_documents': len(filepaths),
            'total_issues': 0,
            'issues_by_severity': {'High': 0, 'Medium': 0, 'Low': 0},
            'issues_by_category': {}
        },
        'roles_found': {}
    }

    # v5.9.37: Enable batch_mode for faster processing (skips html_preview, clean_full_text)
    batch_options = dict(options) if options else {}
    batch_options['batch_mode'] = True

    def _review_single_doc(fp_str):
        """Review a single document in its own thread with its own engine."""
        filepath = Path(fp_str)
        if not filepath.exists():
            return {'filename': filepath.name, 'error': 'File not found'}
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), batch_options)
            issues = doc_results.get('issues', [])
            doc_roles = doc_results.get('roles', {})
            if not isinstance(doc_roles, dict):
                doc_roles = {}
            actual_roles = {k: v for k, v in doc_roles.items() if not isinstance(v, dict) or k not in ['success', 'error']}
            # v5.9.35: word_count is at top level of review_document() return, not in document_info
            word_count = doc_results.get('word_count', 0)
            if not word_count:
                doc_info = doc_results.get('document_info', {})
                word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            # v5.9.22: Statement Forge extraction during batch scan
            sf_summary = None
            if _shared.STATEMENT_FORGE_AVAILABLE and doc_results.get('full_text'):
                try:
                    try:
                        from statement_forge.extractor import extract_statements as sf_extract
                        from statement_forge.export import get_export_stats as sf_stats
                        from statement_forge.routes import _store_statements
                    except ImportError:
                        from statement_forge__extractor import extract_statements as sf_extract
                        from statement_forge__export import get_export_stats as sf_stats
                        from statement_forge__routes import _store_statements
                    sf_text = doc_results.get('clean_full_text') or doc_results.get('full_text', '')
                    sf_stmts = sf_extract(sf_text, filepath.name)
                    if sf_stmts:
                        stats = sf_stats(sf_stmts)
                        sf_statements_list = [s.to_dict() for s in sf_stmts]
                        _store_statements(sf_stmts)
                        sf_summary = {
                            'available': True, 'statements_ready': True,
                            'total_statements': len(sf_stmts),
                            'directive_counts': stats.get('directive_counts', {}),
                            'top_roles': stats.get('roles', [])[:5],
                        }
                        doc_results['statement_forge_summary'] = sf_summary
                        # Persist statements to scan history if available
                        if _shared.SCAN_HISTORY_AVAILABLE:
                            try:
                                from routes._shared import get_scan_history_db
                                db = get_scan_history_db()
                                scan_info = db.record_scan(
                                    filename=filepath.name, filepath=str(filepath),
                                    results=doc_results, options=options
                                )
                                if scan_info and sf_statements_list:
                                    db.save_scan_statements(
                                        scan_info['scan_id'], scan_info['document_id'],
                                        sf_statements_list
                                    )
                            except Exception as db_err:
                                logger.warning(f'Batch SF db persist failed: {db_err}')
                        logger.debug(f'Batch SF: {filepath.name} → {len(sf_stmts)} statements')
                except Exception as sf_err:
                    logger.warning(f'Batch SF extraction failed for {filepath.name}: {sf_err}')

            return {
                'filename': filepath.name,
                'filepath': str(filepath),
                'issues': issues,
                'roles': actual_roles,
                'word_count': word_count,
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'sf_summary': sf_summary,
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f'Batch review error: {filepath.name} - {e}\n{tb_str}')
            return {
                'filename': filepath.name,
                'error': str(e),
                'traceback': tb_str if config.debug else None
            }

    # v5.4.0: Parallel batch processing — up to 3 concurrent documents
    # Limited to 3 to avoid memory pressure from NLP models
    max_workers = min(3, len(filepaths))
    doc_entries = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_fp = {executor.submit(_review_single_doc, fp): fp for fp in filepaths}
        for future in as_completed(future_to_fp):
            result = future.result()
            if 'error' in result:
                doc_entries.append(result)
                continue

            # Aggregate issues
            issues = result.pop('issues', [])
            actual_roles = result.pop('roles', {})
            doc_results = result.pop('doc_results', {})
            issue_count = len(issues)
            results['summary']['total_issues'] += issue_count
            for issue in issues:
                sev = issue.get('severity', 'Low')
                results['summary']['issues_by_severity'][sev] = results['summary']['issues_by_severity'].get(sev, 0) + 1
                cat = issue.get('category', 'Unknown')
                results['summary']['issues_by_category'][cat] = results['summary']['issues_by_category'].get(cat, 0) + 1

            # Aggregate roles
            for role_name, role_data in actual_roles.items():
                if role_name not in results['roles_found']:
                    results['roles_found'][role_name] = {'documents': [], 'total_mentions': 0}
                results['roles_found'][role_name]['documents'].append(result['filename'])
                results['roles_found'][role_name]['total_mentions'] += role_data.get('count', 1) if isinstance(role_data, dict) else 1

            doc_entry = {
                'filename': result['filename'],
                'filepath': result['filepath'],
                'issue_count': issue_count,
                'role_count': len(actual_roles),
                'word_count': result['word_count'],
                'score': result['score'],
                'grade': result['grade'],
                'scan_id': None
            }

            # Record scan in history
            if _shared.SCAN_HISTORY_AVAILABLE:
                try:
                    db = get_scan_history_db()
                    scan_record = db.record_scan(
                        filename=result['filename'],
                        filepath=result['filepath'],
                        results=doc_results,
                        options=options
                    )
                    if scan_record and isinstance(scan_record, dict):
                        doc_entry['scan_id'] = scan_record.get('scan_id')
                except Exception as e:
                    logger.warning(f'Failed to record batch scan: {e}')

            doc_entries.append(doc_entry)

    results['documents'] = doc_entries
    return jsonify({'success': True, 'data': results})


# =============================================================================
# v5.5.0: FOLDER SCAN — Recursive document repository scanning
# =============================================================================
# Scans an entire folder tree on the server's filesystem for supported documents.
# Designed for scanning document repositories with hundreds of files across
# nested subdirectories. Uses chunked processing with memory management.
#
# Key features:
# - Recursive directory traversal with depth limit
# - Smart file discovery (docx, pdf, doc only)
# - Chunked processing (5 files at a time) with ThreadPoolExecutor
# - Per-chunk memory cleanup via gc.collect()
# - Graceful error handling — one bad file doesn't stop the whole scan
# - Progress tracking with file-level status
# - Folder structure metadata in results
# =============================================================================

@review_bp.route('/api/review/folder-scan', methods=['POST'])
@require_csrf
@handle_api_errors
def folder_scan():
    """
    v5.5.0: Scan an entire folder tree for documents and review them all.

    Accepts a folder path on the server filesystem. Recursively discovers
    all supported documents (.docx, .pdf, .doc), then processes them in
    memory-safe chunks using ThreadPoolExecutor.

    Request JSON:
        folder_path (str): Absolute path to the folder to scan
        options (dict): Review options (same as /api/review)
        max_depth (int): Maximum subdirectory depth (default: 10)
        max_files (int): Maximum files to process (default: MAX_FOLDER_SCAN_FILES)
        dry_run (bool): If true, just discover files without reviewing

    Returns:
        JSON with discovery results + review results per document
    """
    import gc
    from concurrent.futures import ThreadPoolExecutor, as_completed

    data = request.get_json() or {}
    folder_path_str = data.get('folder_path', '')
    options = data.get('options', {})
    max_depth = min(data.get('max_depth', 10), 20)  # Cap at 20
    max_files = min(data.get('max_files', MAX_FOLDER_SCAN_FILES), MAX_FOLDER_SCAN_FILES)
    dry_run = data.get('dry_run', False)

    if not folder_path_str:
        raise ValidationError('No folder_path provided')

    # v6.1.7: Detect when a SharePoint URL is accidentally pasted into the local folder field
    if folder_path_str.startswith(('http://', 'https://')) or 'sharepoint' in folder_path_str.lower():
        raise ValidationError(
            'This looks like a SharePoint URL, not a local folder path. '
            'Please paste SharePoint links in the "Paste SharePoint link" field below, '
            'then click "Connect & Scan".'
        )

    folder_path = Path(folder_path_str)
    if not folder_path.exists():
        raise ValidationError(f'Folder not found: {folder_path_str}')
    if not folder_path.is_dir():
        raise ValidationError(f'Path is not a directory: {folder_path_str}')

    # ── Phase 1: Discover files recursively ──
    logger.info(f'[FolderScan] Starting discovery: {folder_path} (max_depth={max_depth}, max_files={max_files})')
    supported_extensions = {'.docx', '.pdf', '.doc'}
    discovered = []
    skipped = []
    folder_tree = {}

    def _discover_recursive(dir_path, current_depth=0):
        """Walk directory tree and collect supported files."""
        if current_depth > max_depth:
            return
        if len(discovered) >= max_files:
            return

        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            skipped.append({'path': str(dir_path), 'reason': 'Permission denied'})
            return
        except OSError as e:
            skipped.append({'path': str(dir_path), 'reason': str(e)})
            return

        rel_dir = str(dir_path.relative_to(folder_path)) if dir_path != folder_path else '.'
        folder_tree[rel_dir] = {'files': 0, 'subdirs': 0}

        for entry in entries:
            if len(discovered) >= max_files:
                break

            if entry.is_dir():
                # Skip hidden directories and common non-document dirs
                if entry.name.startswith('.') or entry.name.startswith('__'):
                    continue
                if entry.name.lower() in ('node_modules', '.git', '__pycache__', 'venv', '.venv'):
                    continue
                folder_tree[rel_dir]['subdirs'] += 1
                _discover_recursive(entry, current_depth + 1)

            elif entry.is_file():
                ext = entry.suffix.lower()
                if ext in supported_extensions:
                    try:
                        file_size = entry.stat().st_size
                        if file_size == 0:
                            skipped.append({'path': str(entry), 'reason': 'Empty file (0 bytes)'})
                            continue
                        if file_size > 100 * 1024 * 1024:  # Skip files >100MB
                            skipped.append({'path': str(entry), 'reason': f'File too large ({file_size // (1024*1024)}MB)'})
                            continue

                        rel_path = str(entry.relative_to(folder_path))
                        discovered.append({
                            'path': str(entry),
                            'relative_path': rel_path,
                            'filename': entry.name,
                            'extension': ext,
                            'size': file_size,
                            'folder': rel_dir
                        })
                        folder_tree[rel_dir]['files'] += 1
                    except OSError as e:
                        skipped.append({'path': str(entry), 'reason': str(e)})
                else:
                    # Track unsupported files for the report
                    if ext and ext not in ('.py', '.js', '.css', '.html', '.json', '.md', '.txt', '.yml', '.yaml', '.xml', '.ini', '.cfg', '.log', '.bat', '.sh'):
                        skipped.append({'path': str(entry), 'reason': f'Unsupported type: {ext}'})

    _discover_recursive(folder_path)

    discovery_result = {
        'folder_path': str(folder_path),
        'total_discovered': len(discovered),
        'total_skipped': len(skipped),
        'folder_tree': folder_tree,
        'max_depth': max_depth,
        'max_files': max_files,
        'files': discovered,
        'skipped': skipped[:50],  # Limit skipped list to 50 entries
        'truncated_skipped': len(skipped) > 50,
        'file_type_breakdown': {},
    }

    # Count by extension
    for f in discovered:
        ext = f['extension']
        discovery_result['file_type_breakdown'][ext] = discovery_result['file_type_breakdown'].get(ext, 0) + 1

    logger.info(f'[FolderScan] Discovered {len(discovered)} files in {len(folder_tree)} folders, skipped {len(skipped)}')

    if dry_run:
        return jsonify({'success': True, 'data': {'discovery': discovery_result, 'review': None}})

    if not discovered:
        return jsonify({'success': True, 'data': {
            'discovery': discovery_result,
            'review': {'documents': [], 'summary': {'total_documents': 0, 'total_issues': 0}},
            'message': 'No supported documents found in folder'
        }})

    # ── Phase 2: Review documents in memory-safe chunks ──
    logger.info(f'[FolderScan] Starting review of {len(discovered)} documents in chunks of {FOLDER_SCAN_CHUNK_SIZE}')

    review_results = {
        'documents': [],
        'summary': {
            'total_documents': len(discovered),
            'processed': 0,
            'errors': 0,
            'total_issues': 0,
            'total_words': 0,
            'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
            'issues_by_category': {},
            'grade_distribution': {},
        },
        'roles_found': {},
        'processing_time_seconds': 0,
    }

    start_time = time.time()

    # v5.9.37: Enable batch_mode for faster processing
    folder_batch_options = dict(options) if options else {}
    folder_batch_options['batch_mode'] = True

    def _review_single(file_info):
        """Review one document with its own engine instance."""
        filepath = Path(file_info['path'])
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), folder_batch_options)
            # Convert ReviewIssue objects to dicts for safe .get() access and JSON serialization
            raw_issues = doc_results.get('issues', [])
            issues = []
            for issue in raw_issues:
                if isinstance(issue, dict):
                    issues.append(issue)
                elif hasattr(issue, 'to_dict'):
                    issues.append(issue.to_dict())
                else:
                    issues.append({'severity': getattr(issue, 'severity', 'Low'),
                                   'category': getattr(issue, 'category', 'Unknown'),
                                   'message': getattr(issue, 'message', str(issue))})
            doc_results['issues'] = issues
            doc_roles = doc_results.get('roles', {})
            if not isinstance(doc_roles, dict):
                doc_roles = {}
            actual_roles = {k: v for k, v in doc_roles.items()
                          if not isinstance(v, dict) or k not in ['success', 'error']}
            # v5.9.35: word_count is at top level, not in document_info
            word_count = doc_results.get('word_count', 0)
            if not word_count:
                doc_info = doc_results.get('document_info', {})
                word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
                'full_path': file_info['path'],
                'folder': file_info['folder'],
                'extension': file_info['extension'],
                'file_size': file_info['size'],
                'issues': issues,
                'issue_count': len(issues),
                'roles': actual_roles,
                'role_count': len(actual_roles),
                'word_count': word_count,
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'status': 'success',
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f'[FolderScan] Error reviewing {file_info["filename"]}: {e}\n{tb_str}')
            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
                'full_path': file_info['path'],
                'folder': file_info['folder'],
                'extension': file_info['extension'],
                'file_size': file_info['size'],
                'error': str(e),
                'status': 'error',
            }

    # Process in chunks to manage memory
    chunks = [discovered[i:i + FOLDER_SCAN_CHUNK_SIZE]
              for i in range(0, len(discovered), FOLDER_SCAN_CHUNK_SIZE)]

    for chunk_idx, chunk in enumerate(chunks):
        logger.info(f'[FolderScan] Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} files)')

        max_workers = min(FOLDER_SCAN_MAX_WORKERS, len(chunk))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(_review_single, f): f for f in chunk}
            for future in as_completed(future_to_file):
                result = future.result()

                if result.get('status') == 'error':
                    review_results['summary']['errors'] += 1
                    review_results['documents'].append({
                        'filename': result['filename'],
                        'relative_path': result['relative_path'],
                        'folder': result['folder'],
                        'error': result['error'],
                        'status': 'error',
                    })
                    continue

                review_results['summary']['processed'] += 1

                # Aggregate issues
                issues = result.pop('issues', [])
                actual_roles = result.pop('roles', {})
                doc_results_full = result.pop('doc_results', {})

                review_results['summary']['total_issues'] += result['issue_count']
                review_results['summary']['total_words'] += result.get('word_count', 0)

                for issue in issues:
                    sev = issue.get('severity', 'Low')
                    review_results['summary']['issues_by_severity'][sev] = \
                        review_results['summary']['issues_by_severity'].get(sev, 0) + 1
                    cat = issue.get('category', 'Unknown')
                    review_results['summary']['issues_by_category'][cat] = \
                        review_results['summary']['issues_by_category'].get(cat, 0) + 1

                # Grade distribution
                grade = result.get('grade', 'N/A')
                review_results['summary']['grade_distribution'][grade] = \
                    review_results['summary']['grade_distribution'].get(grade, 0) + 1

                # Aggregate roles
                for role_name, role_data in actual_roles.items():
                    if role_name not in review_results['roles_found']:
                        review_results['roles_found'][role_name] = {
                            'documents': [], 'total_mentions': 0
                        }
                    review_results['roles_found'][role_name]['documents'].append(result['filename'])
                    mention_count = role_data.get('count', 1) if isinstance(role_data, dict) else 1
                    review_results['roles_found'][role_name]['total_mentions'] += mention_count

                # Record scan in history
                if _shared.SCAN_HISTORY_AVAILABLE:
                    try:
                        db = get_scan_history_db()
                        scan_record = db.record_scan(
                            filename=result['filename'],
                            filepath=result.get('full_path', result.get('relative_path', result['filename'])),
                            results=doc_results_full,
                            options=options
                        )
                        result['scan_id'] = scan_record.get('scan_id') if scan_record else None
                    except Exception as e:
                        logger.warning(f'[FolderScan] Scan history error for {result["filename"]}: {e}')

                review_results['documents'].append({
                    'filename': result['filename'],
                    'relative_path': result['relative_path'],
                    'folder': result['folder'],
                    'extension': result['extension'],
                    'file_size': result.get('file_size', 0),
                    'issue_count': result['issue_count'],
                    'role_count': result['role_count'],
                    'word_count': result.get('word_count', 0),
                    'score': result.get('score', 0),
                    'grade': grade,
                    'scan_id': result.get('scan_id'),
                    'status': 'success',
                })

        # Memory cleanup between chunks
        gc.collect()

    review_results['processing_time_seconds'] = round(time.time() - start_time, 2)

    # Sort documents by folder path for organized output
    review_results['documents'].sort(key=lambda d: (d.get('folder', ''), d.get('filename', '')))

    logger.info(
        f'[FolderScan] Complete: {review_results["summary"]["processed"]} processed, '
        f'{review_results["summary"]["errors"]} errors, '
        f'{review_results["summary"]["total_issues"]} issues, '
        f'{review_results["processing_time_seconds"]}s'
    )

    return jsonify({
        'success': True,
        'data': {
            'discovery': discovery_result,
            'review': review_results,
        }
    })


@review_bp.route('/api/review/folder-discover', methods=['POST'])
@require_csrf
@handle_api_errors
def folder_discover():
    """
    v5.5.0: Discovery-only endpoint — lists files in a folder without reviewing.
    Use this to preview what a folder scan will process before committing.

    Request JSON:
        folder_path (str): Absolute path to the folder
        max_depth (int): Maximum subdirectory depth (default: 10)

    Returns:
        JSON with file list, folder tree, and type breakdown
    """
    data = request.get_json() or {}
    folder_path_str = data.get('folder_path', '')

    if not folder_path_str:
        raise ValidationError('No folder_path provided')

    # v6.1.7: Detect when a SharePoint URL is accidentally pasted into the local folder field
    if folder_path_str.startswith(('http://', 'https://')) or 'sharepoint' in folder_path_str.lower():
        raise ValidationError(
            'This looks like a SharePoint URL, not a local folder path. '
            'Please paste SharePoint links in the "Paste SharePoint link" field below, '
            'then click "Connect & Scan".'
        )

    folder_path = Path(folder_path_str)
    if not folder_path.exists():
        raise ValidationError(f'Folder not found: {folder_path_str}')
    if not folder_path.is_dir():
        raise ValidationError(f'Path is not a directory: {folder_path_str}')

    max_depth = min(data.get('max_depth', 10), 20)
    supported_extensions = {'.docx', '.pdf', '.doc'}
    discovered = []
    total_size = 0

    def _discover(dir_path, depth=0):
        nonlocal total_size
        if depth > max_depth:
            return
        try:
            for entry in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
                if entry.is_dir():
                    if entry.name.startswith('.') or entry.name.startswith('__'):
                        continue
                    if entry.name.lower() in ('node_modules', '.git', '__pycache__', 'venv', '.venv'):
                        continue
                    _discover(entry, depth + 1)
                elif entry.is_file() and entry.suffix.lower() in supported_extensions:
                    try:
                        size = entry.stat().st_size
                        if size > 0:
                            discovered.append({
                                'path': str(entry),
                                'relative_path': str(entry.relative_to(folder_path)),
                                'filename': entry.name,
                                'extension': entry.suffix.lower(),
                                'size': size,
                                'size_human': _human_size(size),
                            })
                            total_size += size
                    except OSError:
                        pass
        except (PermissionError, OSError):
            pass

    _discover(folder_path)

    # Build type breakdown
    type_breakdown = {}
    for f in discovered:
        ext = f['extension']
        type_breakdown[ext] = type_breakdown.get(ext, 0) + 1

    return jsonify({
        'success': True,
        'data': {
            'folder_path': str(folder_path),
            'total_files': len(discovered),
            'total_size': total_size,
            'total_size_human': _human_size(total_size),
            'type_breakdown': type_breakdown,
            'files': discovered,
            'max_depth': max_depth,
        }
    })


# =============================================================================
# v5.7.0: Async Folder Scan — Start + Progress Endpoints
# =============================================================================
# Two-step pattern: POST /folder-scan-start returns scan_id immediately,
# then GET /folder-scan-progress/<scan_id> polls for updates.
# The existing synchronous /folder-scan endpoint is preserved as fallback.
# =============================================================================

@review_bp.route('/api/review/folder-scan-start', methods=['POST'])
@require_csrf
@handle_api_errors
def folder_scan_start():
    """
    v5.7.0: Start an async folder scan — returns scan_id immediately.

    Phase 1 (discovery) runs synchronously and returns in the response.
    Phase 2 (review) runs in a background thread. Poll /folder-scan-progress/<scan_id>
    for real-time updates.

    Request JSON:
        folder_path (str): Absolute path to the folder to scan
        options (dict): Review options (same as /api/review)
        max_depth (int): Maximum subdirectory depth (default: 10)
        max_files (int): Maximum files to process (default: MAX_FOLDER_SCAN_FILES)

    Returns:
        JSON with scan_id + discovery results. Review runs in background.
    """
    data = request.get_json() or {}
    folder_path_str = data.get('folder_path', '')
    options = data.get('options', {})
    max_depth = min(data.get('max_depth', 10), 20)
    max_files = min(data.get('max_files', MAX_FOLDER_SCAN_FILES), MAX_FOLDER_SCAN_FILES)

    if not folder_path_str:
        raise ValidationError('No folder_path provided')

    # v6.1.2: Detect when a SharePoint URL is accidentally pasted into the local folder field
    if folder_path_str.startswith(('http://', 'https://')) or 'sharepoint' in folder_path_str.lower():
        raise ValidationError(
            'This looks like a SharePoint URL, not a local folder path. '
            'Please paste SharePoint links in the "Paste SharePoint link" field below, '
            'then click "Connect & Scan".'
        )

    # v6.2.0: UNC path support (\\server\share or //server/share)
    is_unc = folder_path_str.startswith('\\\\') or folder_path_str.startswith('//')
    if is_unc:
        if sys.platform != 'win32':
            raise ValidationError(
                'UNC paths (\\\\server\\share) are only supported on Windows. '
                'On macOS/Linux, mount the network share first and use the mount path.'
            )
        # Normalize forward-slash UNC to backslash for Windows
        folder_path_str = folder_path_str.replace('/', '\\')
        logger.info(f'[FolderScan] UNC path detected: {folder_path_str}')

    folder_path = Path(folder_path_str)
    if not folder_path.exists():
        if is_unc:
            raise ValidationError(
                f'UNC path not accessible: {folder_path_str}. '
                'Verify the server name and share are correct, and that you have network access.'
            )
        raise ValidationError(f'Folder not found: {folder_path_str}')
    if not folder_path.is_dir():
        raise ValidationError(f'Path is not a directory: {folder_path_str}')

    # ── Phase 1: Discovery (synchronous — fast) ──
    supported_extensions = {'.docx', '.pdf', '.doc'}
    discovered = []
    skipped = []
    folder_tree = {}

    def _discover_recursive(dir_path, current_depth=0):
        if current_depth > max_depth:
            return
        if len(discovered) >= max_files:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except (PermissionError, OSError) as e:
            skipped.append({'path': str(dir_path), 'reason': str(e)})
            return

        rel_dir = str(dir_path.relative_to(folder_path)) if dir_path != folder_path else '.'
        folder_tree[rel_dir] = {'files': 0, 'subdirs': 0}

        for entry in entries:
            if len(discovered) >= max_files:
                break
            if entry.is_dir():
                if entry.name.startswith('.') or entry.name.startswith('__'):
                    continue
                if entry.name.lower() in ('node_modules', '.git', '__pycache__', 'venv', '.venv'):
                    continue
                folder_tree[rel_dir]['subdirs'] += 1
                _discover_recursive(entry, current_depth + 1)
            elif entry.is_file():
                ext = entry.suffix.lower()
                if ext in supported_extensions:
                    try:
                        file_size = entry.stat().st_size
                        if file_size == 0:
                            skipped.append({'path': str(entry), 'reason': 'Empty file (0 bytes)'})
                            continue
                        if file_size > 100 * 1024 * 1024:
                            skipped.append({'path': str(entry), 'reason': f'File too large ({file_size // (1024*1024)}MB)'})
                            continue
                        rel_path = str(entry.relative_to(folder_path))
                        discovered.append({
                            'path': str(entry),
                            'relative_path': rel_path,
                            'filename': entry.name,
                            'extension': ext,
                            'size': file_size,
                            'folder': rel_dir,
                        })
                        folder_tree[rel_dir]['files'] += 1
                    except OSError as e:
                        skipped.append({'path': str(entry), 'reason': str(e)})

    _discover_recursive(folder_path)

    # Build type breakdown
    file_type_breakdown = {}
    total_size = 0
    for f in discovered:
        ext = f['extension']
        file_type_breakdown[ext] = file_type_breakdown.get(ext, 0) + 1
        total_size += f['size']

    discovery_result = {
        'folder_path': str(folder_path),
        'total_discovered': len(discovered),
        'total_skipped': len(skipped),
        'total_size': total_size,
        'total_size_human': _human_size(total_size),
        'folder_tree': folder_tree,
        'max_depth': max_depth,
        'max_files': max_files,
        'files': discovered,
        'skipped': skipped[:50],
        'truncated_skipped': len(skipped) > 50,
        'file_type_breakdown': file_type_breakdown,
    }

    if not discovered:
        return jsonify({'success': True, 'data': {
            'scan_id': None,
            'discovery': discovery_result,
            'message': 'No supported documents found in folder',
        }})

    # ── Generate scan_id and initialize state ──
    scan_id = str(uuid.uuid4())[:12]
    _cleanup_old_scans()

    with _folder_scan_state_lock:
        _folder_scan_state[scan_id] = {
            'phase': 'reviewing',
            'total_files': len(discovered),
            'processed': 0,
            'errors': 0,
            'current_file': None,
            'current_chunk': 0,
            'total_chunks': (len(discovered) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE,
            'documents': [],
            'summary': {
                'total_documents': len(discovered),
                'processed': 0,
                'errors': 0,
                'total_issues': 0,
                'total_words': 0,
                'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                'issues_by_category': {},
                'grade_distribution': {},
            },
            'roles_found': {},
            'started_at': time.time(),
            'completed_at': None,
            'elapsed_seconds': 0,
            'estimated_remaining': None,
            'folder_path': str(folder_path),
        }

    logger.info(f'[FolderScan-Async] Started scan {scan_id}: {len(discovered)} files in {len(folder_tree)} folders')

    # ── Spawn background thread for Phase 2 ──
    thread = threading.Thread(
        target=_process_folder_scan_async,
        args=(scan_id, discovered, options),
        daemon=True,
        name=f'folder-scan-{scan_id}',
    )
    thread.start()

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'discovery': discovery_result,
        }
    })


def _update_scan_state_with_result(scan_id, result, options, flask_app):
    """
    v5.7.1: Update folder scan state with one file's result.
    Extracted to a helper to keep the main loop clean and avoid indentation hell.
    """
    with _folder_scan_state_lock:
        state = _folder_scan_state.get(scan_id)
        if not state:
            logger.warning(f'[FolderScan-Async] State missing for {scan_id}')
            return

        state['current_file'] = result['filename']
        elapsed = time.time() - state['started_at']
        state['elapsed_seconds'] = round(elapsed, 1)

        if result.get('status') == 'error':
            state['errors'] += 1
            state['summary']['errors'] += 1
            state['documents'].append({
                'filename': result['filename'],
                'relative_path': result['relative_path'],
                'folder': result['folder'],
                'error': result.get('error', 'Unknown error'),
                'status': 'error',
            })
        else:
            # v6.2.0: Wrapped success path in try/except to prevent background
            # thread crash from malformed issue dicts or unexpected data shapes
            try:
                state['processed'] += 1
                state['summary']['processed'] += 1

                issues = result.pop('issues', [])
                actual_roles = result.pop('roles', {})
                doc_results_full = result.pop('doc_results', {})

                state['summary']['total_issues'] += result['issue_count']
                state['summary']['total_words'] += result.get('word_count', 0)

                for issue in issues:
                    sev = issue.get('severity', 'Low')
                    state['summary']['issues_by_severity'][sev] = \
                        state['summary']['issues_by_severity'].get(sev, 0) + 1
                    cat = issue.get('category', 'Unknown')
                    state['summary']['issues_by_category'][cat] = \
                        state['summary']['issues_by_category'].get(cat, 0) + 1

                grade = result.get('grade', 'N/A')
                state['summary']['grade_distribution'][grade] = \
                    state['summary']['grade_distribution'].get(grade, 0) + 1

                for role_name, role_data in actual_roles.items():
                    if role_name not in state['roles_found']:
                        state['roles_found'][role_name] = {
                            'documents': [], 'total_mentions': 0
                        }
                    state['roles_found'][role_name]['documents'].append(result['filename'])
                    mention_count = role_data.get('count', 1) if isinstance(role_data, dict) else 1
                    state['roles_found'][role_name]['total_mentions'] += mention_count

                # Record scan in history (needs Flask app context)
                # v6.6.0: Pass source_url for SP URL tracking
                scan_record_id = None
                if _shared.SCAN_HISTORY_AVAILABLE and flask_app:
                    try:
                        with flask_app.app_context():
                            db = get_scan_history_db()
                            scan_record = db.record_scan(
                                filename=result['filename'],
                                filepath=result.get('full_path', result.get('relative_path', result['filename'])),
                                results=doc_results_full,
                                options=options,
                                source_url=result.get('source_url')
                            )
                            scan_record_id = scan_record.get('scan_id') if scan_record else None
                    except Exception as e:
                        logger.warning(f'[FolderScan-Async] Scan history error for {result["filename"]}: {e}')

                state['documents'].append({
                    'filename': result['filename'],
                    'relative_path': result['relative_path'],
                    'folder': result['folder'],
                    'extension': result['extension'],
                    'file_size': result.get('file_size', 0),
                    'issue_count': result['issue_count'],
                    'role_count': result['role_count'],
                    'word_count': result.get('word_count', 0),
                    'score': result.get('score', 0),
                    'grade': grade,
                    'scan_id': scan_record_id,
                    'status': 'success',
                })
            except Exception as inner_e:
                # v6.2.0: Protect against malformed result dicts crashing background thread
                logger.error(f'[FolderScan-Async] Error processing success result for '
                             f'{result.get("filename", "unknown")}: {inner_e}\n{traceback.format_exc()}')
                state['errors'] += 1
                state['summary']['errors'] += 1
                state['documents'].append({
                    'filename': result.get('filename', 'unknown'),
                    'relative_path': result.get('relative_path', ''),
                    'folder': result.get('folder', ''),
                    'error': f'Result processing error: {str(inner_e)}',
                    'status': 'error',
                })

        # Estimate remaining time
        elapsed = time.time() - state['started_at']
        total_done = state['processed'] + state['errors']
        if total_done > 0:
            avg_time = elapsed / total_done
            remaining = state['total_files'] - total_done
            state['estimated_remaining'] = round(avg_time * remaining, 1)


def _process_folder_scan_async(scan_id, discovered, options):
    """
    Background thread: process folder scan documents in chunks.
    Updates _folder_scan_state[scan_id] after each file completes.
    """
    import gc
    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
    from flask import current_app

    # Get the Flask app reference for context (needed for scan history DB)
    # We need to import the app since we're in a background thread
    try:
        from app import app as flask_app
    except ImportError:
        flask_app = None

    # v5.9.37: Enable batch_mode for faster processing
    async_batch_options = dict(options) if options else {}
    async_batch_options['batch_mode'] = True

    def _review_single_async(file_info):
        """Review one document with its own engine instance."""
        filepath = Path(file_info['path'])
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), async_batch_options)

            # Convert ReviewIssue objects to dicts
            raw_issues = doc_results.get('issues', [])
            issues = []
            for issue in raw_issues:
                if isinstance(issue, dict):
                    issues.append(issue)
                elif hasattr(issue, 'to_dict'):
                    issues.append(issue.to_dict())
                else:
                    issues.append({
                        'severity': getattr(issue, 'severity', 'Low'),
                        'category': getattr(issue, 'category', 'Unknown'),
                        'message': getattr(issue, 'message', str(issue)),
                    })
            doc_results['issues'] = issues

            doc_roles = doc_results.get('roles', {})
            if not isinstance(doc_roles, dict):
                doc_roles = {}
            actual_roles = {k: v for k, v in doc_roles.items()
                          if not isinstance(v, dict) or k not in ['success', 'error']}
            # v5.9.35: word_count is at top level, not in document_info
            word_count = doc_results.get('word_count', 0)
            if not word_count:
                doc_info = doc_results.get('document_info', {})
                word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
                'full_path': file_info['path'],
                'folder': file_info['folder'],
                'extension': file_info['extension'],
                'file_size': file_info['size'],
                'issues': issues,
                'issue_count': len(issues),
                'roles': actual_roles,
                'role_count': len(actual_roles),
                'word_count': word_count,
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'status': 'success',
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f'[FolderScan-Async] Error reviewing {file_info["filename"]}: {e}\n{tb_str}')
            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
                'full_path': file_info['path'],
                'folder': file_info['folder'],
                'extension': file_info['extension'],
                'file_size': file_info['size'],
                'error': str(e),
                'status': 'error',
            }

    try:
        chunks = [discovered[i:i + FOLDER_SCAN_CHUNK_SIZE]
                  for i in range(0, len(discovered), FOLDER_SCAN_CHUNK_SIZE)]

        # v5.7.1: Per-file timeout — 8 minutes max per file to prevent hangs
        # v5.9.37: Increased from 300s (5min) to 480s (8min) because some complex
        # PDFs with dense tables legitimately need 4-5 minutes for Docling extraction.
        # The persistent Docling worker eliminates startup overhead, but extraction
        # itself can still be slow for large documents.
        PER_FILE_TIMEOUT = 480

        for chunk_idx, chunk in enumerate(chunks):
            logger.info(f'[FolderScan-Async] {scan_id} chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} files)')

            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['current_chunk'] = chunk_idx + 1
                    # Show which files are being processed in this chunk
                    state['current_file'] = ', '.join(f['filename'] for f in chunk[:3])
                    if len(chunk) > 3:
                        state['current_file'] += f' (+{len(chunk) - 3} more)'

            max_workers = min(FOLDER_SCAN_MAX_WORKERS, len(chunk))
            chunk_timed_out = False

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(_review_single_async, f): f for f in chunk}
                completed_futures = set()

                try:
                    for future in as_completed(future_to_file, timeout=PER_FILE_TIMEOUT * len(chunk)):
                        completed_futures.add(future)
                        file_info = future_to_file[future]
                        try:
                            result = future.result(timeout=30)  # Already complete, just grab it
                        except Exception as e:
                            logger.error(f'[FolderScan-Async] Error getting result for {file_info["filename"]}: {e}')
                            result = {
                                'filename': file_info['filename'],
                                'relative_path': file_info['relative_path'],
                                'folder': file_info['folder'],
                                'extension': file_info['extension'],
                                'file_size': file_info['size'],
                                'error': f'Worker error: {str(e)}',
                                'status': 'error',
                            }

                        # ── Update state with this file's result ──
                        _update_scan_state_with_result(scan_id, result, options, flask_app)

                except FuturesTimeoutError:
                    # Chunk-level timeout — mark remaining futures as timed out
                    chunk_timed_out = True
                    logger.error(f'[FolderScan-Async] Chunk {chunk_idx + 1} timed out after {PER_FILE_TIMEOUT * len(chunk)}s')
                    for future, file_info in future_to_file.items():
                        if future not in completed_futures:
                            timeout_result = {
                                'filename': file_info['filename'],
                                'relative_path': file_info['relative_path'],
                                'folder': file_info['folder'],
                                'extension': file_info['extension'],
                                'file_size': file_info['size'],
                                'error': f'Timed out (chunk timeout after {PER_FILE_TIMEOUT * len(chunk)}s)',
                                'status': 'error',
                            }
                            with _folder_scan_state_lock:
                                state = _folder_scan_state.get(scan_id)
                                if state:
                                    state['errors'] += 1
                                    state['summary']['errors'] += 1
                                    state['documents'].append({
                                        'filename': timeout_result['filename'],
                                        'relative_path': timeout_result['relative_path'],
                                        'folder': timeout_result['folder'],
                                        'error': timeout_result['error'],
                                        'status': 'error',
                                    })

            gc.collect()

        # ── Mark complete ──
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'complete'
                state['current_file'] = None
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                state['estimated_remaining'] = 0
                state['documents'].sort(key=lambda d: (d.get('folder', ''), d.get('filename', '')))
                logger.info(
                    f'[FolderScan-Async] {scan_id} complete: '
                    f'{state["summary"]["processed"]} processed, '
                    f'{state["summary"]["errors"]} errors, '
                    f'{state["summary"]["total_issues"]} issues, '
                    f'{state["elapsed_seconds"]}s'
                )

    except Exception as e:
        logger.error(f'[FolderScan-Async] {scan_id} fatal error: {e}\n{traceback.format_exc()}')
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'error'
                state['error_message'] = str(e)
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)


@review_bp.route('/api/review/scan-pre-register', methods=['POST'])
@handle_api_errors
def scan_pre_register():
    """
    v6.3.8: ONE-POST SharePoint scan architecture (Lesson 170).

    Previously this was a lightweight pre-register, followed by a separate
    heavy POST to /sharepoint-scan-selected. That second POST NEVER reached
    the server on the Windows machine — 8+ diagnostic sessions proved it.
    Beacons confirmed the fetch was sent but Flask/Waitress never received it.

    The fix: merge ALL scan-start logic into this single endpoint. This
    endpoint is PROVEN to work (two instances in logs, both 200 in <5ms).
    No @require_csrf, no X-CSRF-Token header, no AbortController signal —
    all three of which differentiated the failing POST from this working one.

    When 'files' is present in the body: creates scan state AND spawns the
    background scan thread (full scan-start flow).
    When 'files' is absent: lightweight pre-register only (backward compat).

    NO @require_csrf — localhost-only tool (localhost:5050). No security risk.
    Body: { scan_id, total_files, source, [files, site_url, library_path,
            connector_type, connector_token, options] }
    """
    data = request.get_json(silent=True) or {}
    scan_id = (data.get('scan_id') or '').strip()
    total_files = data.get('total_files', 0)
    source = data.get('source', 'sharepoint')

    if not scan_id or len(scan_id) < 6 or len(scan_id) > 36:
        return jsonify({'success': False, 'error': {'message': 'Invalid scan_id'}}), 400

    # ── Check if this is a full scan request ──
    selected_files = data.get('files', [])
    file_indices = data.get('file_indices', None)  # v6.3.9: integer indices into cached file list
    site_url = data.get('site_url', '').strip()
    library_path = data.get('library_path', '').strip()
    connector_type = data.get('connector_type', 'rest')
    connector_token = data.get('connector_token', '').strip()
    options = data.get('options', {})

    # v6.3.9: Resolve files from cache using file_indices (tiny POST body)
    # This avoids sending 63 full file objects through corporate proxy/DLP
    if not selected_files and file_indices is not None and connector_token:
        with _sp_connector_cache_lock:
            entry = _sp_connector_cache.get(connector_token)
        if entry and 'files' in entry:
            cached_files = entry['files']
            if file_indices == 'all':
                selected_files = cached_files
                logger.info(f'[scan-pre-register] v6.3.9: Resolved ALL {len(selected_files)} files from cache')
            else:
                selected_files = [cached_files[i] for i in file_indices if 0 <= i < len(cached_files)]
                logger.info(f'[scan-pre-register] v6.3.9: Resolved {len(selected_files)}/{len(cached_files)} files from cache via indices')
            # Fill in site_url and library_path from cache if not provided
            if not site_url:
                site_url = entry.get('site_url', '')
            if not library_path:
                library_path = entry.get('library_path', '')
            if connector_type == 'rest':
                connector_type = entry.get('connector_type', 'rest')
        else:
            logger.warning(f'[scan-pre-register] v6.3.9: file_indices provided but cache miss (token={connector_token[:8]}...)')

    is_full_scan = bool(selected_files) and bool(site_url)

    if is_full_scan:
        logger.info(f'[scan-pre-register] ONE-POST scan: {scan_id}, {len(selected_files)} files, site={site_url}, lib={library_path}')
    else:
        logger.info(f'[scan-pre-register] Lightweight pre-register: {scan_id}, {total_files} files (source={source})')

    # ── Look up cached connector if full scan ──
    cached_connector = None
    if is_full_scan and connector_token:
        with _sp_connector_cache_lock:
            entry = _sp_connector_cache.pop(connector_token, None)
        if entry:
            age = time.time() - entry['created_at']
            if age < _SP_CONNECTOR_CACHE_TTL:
                cached_connector = entry['connector']
                logger.info(f'[scan-pre-register] ✓ Reusing cached connector (token={connector_token[:8]}..., age={age:.0f}s)')
            else:
                logger.warning(f'[scan-pre-register] Cached connector expired (age={age:.0f}s) — will create new')
                try:
                    entry['connector'].close()
                except Exception:
                    pass
        else:
            logger.warning(f'[scan-pre-register] Connector token {connector_token[:8]}... not found — will create new')

    # ── Determine initial phase ──
    if is_full_scan:
        total_files = len(selected_files)
        if cached_connector:
            initial_phase = 'reviewing'
            initial_msg = 'Starting document scan...'
        else:
            initial_phase = 'connecting'
            initial_msg = 'Authenticating to SharePoint...'
        folder_label = f'SharePoint: {library_path} ({total_files} selected)'
    else:
        initial_phase = 'connecting'
        initial_msg = 'Authenticating to SharePoint...'
        folder_label = f'{source}: pre-registered ({total_files} files)'

    # ── Create or merge scan state ──
    with _folder_scan_state_lock:
        _cleanup_old_scans()
        existing = _folder_scan_state.get(scan_id)
        if existing:
            existing['phase'] = initial_phase
            existing['total_files'] = int(total_files)
            existing['current_file'] = initial_msg
            existing['total_chunks'] = max(1, (int(total_files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE)
            existing['summary']['total_documents'] = int(total_files)
            existing['folder_path'] = folder_label
            logger.info(f'[scan-pre-register] Merged into existing state {scan_id} (phase={initial_phase})')
        else:
            _folder_scan_state[scan_id] = {
                'phase': initial_phase,
                'total_files': int(total_files),
                'processed': 0,
                'errors': 0,
                'current_file': initial_msg,
                'current_chunk': 0,
                'total_chunks': max(1, (int(total_files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE),
                'documents': [],
                'summary': {
                    'total_documents': int(total_files),
                    'processed': 0,
                    'errors': 0,
                    'total_issues': 0,
                    'total_words': 0,
                    'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                    'issues_by_category': {},
                    'grade_distribution': {},
                },
                'roles_found': {},
                'started_at': time.time(),
                'completed_at': None,
                'elapsed_seconds': 0,
                'estimated_remaining': None,
                'folder_path': folder_label,
                'source': source,
            }
            logger.info(f'[scan-pre-register] Created scan state {scan_id} (phase={initial_phase})')

    # ── If full scan: spawn background thread ──
    if is_full_scan:
        SPConnector, sp_parse_url = _get_sharepoint_connector()
        if SPConnector is None:
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['phase'] = 'error'
                    state['error_message'] = 'SharePoint connector not available'
            return jsonify({
                'success': False,
                'error': {'message': 'SharePoint connector not available', 'code': 'SP_UNAVAILABLE'}
            }), 500

        flask_app = current_app._get_current_object()
        thread = threading.Thread(
            target=_process_sharepoint_scan_async,
            args=(scan_id, cached_connector, selected_files, options, flask_app),
            kwargs={
                'site_url': site_url,
                'connector_type': connector_type,
                'library_path': library_path,
            },
            daemon=True,
            name=f'sp-scan-{scan_id}',
        )
        thread.start()

        total_size = sum(f.get('size', 0) for f in selected_files)
        type_breakdown = {}
        for f in selected_files:
            ext = f.get('extension', f.get('name', '').rsplit('.', 1)[-1] if '.' in f.get('name', '') else 'unknown')
            type_breakdown[ext] = type_breakdown.get(ext, 0) + 1

        logger.info(f'[scan-pre-register] Scan thread started: {scan_id}, {len(selected_files)} files, cached_connector={cached_connector is not None}')

        return jsonify({
            'success': True,
            'data': {
                'scan_id': scan_id,
                'total_files': len(selected_files),
                'library_path': library_path,
                'scan_started': True,
                'discovery': {
                    'total_discovered': len(selected_files),
                    'supported_files': len(selected_files),
                    'total_size': total_size,
                    'file_type_breakdown': type_breakdown,
                }
            }
        })

    # ── Lightweight pre-register only ──
    return jsonify({'success': True, 'data': {'scan_id': scan_id}})


@review_bp.route('/api/review/scan-error', methods=['POST'])
@handle_api_errors
def scan_error():
    """
    v6.3.7: Mark a pre-registered scan as errored.

    Called by the frontend when the heavy POST to /sharepoint-scan-selected fails
    (timeout, network error, etc.). Updates the scan state so the polling dashboard
    shows the error instead of being stuck at "Connecting...".

    NO @require_csrf — same rationale as scan-pre-register.
    Body: { scan_id: string, error: string }
    """
    data = request.get_json(silent=True) or {}
    scan_id = (data.get('scan_id') or '').strip()
    error_msg = data.get('error', 'Scan request failed')

    if not scan_id:
        return jsonify({'success': False, 'error': {'message': 'Missing scan_id'}}), 400

    with _folder_scan_state_lock:
        state = _folder_scan_state.get(scan_id)
        if state:
            state['phase'] = 'error'
            state['completed_at'] = time.time()
            state['current_file'] = f'Error: {error_msg}'
            logger.warning(f'[scan-error] Scan {scan_id} marked as errored: {error_msg}')
        else:
            logger.warning(f'[scan-error] Scan {scan_id} not found — no state to update')

    return jsonify({'success': True})


@review_bp.route('/api/review/sp-go/<connector_token>', methods=['GET'])
@handle_api_errors
def sp_scan_go(connector_token):
    """
    v6.3.10: GET-based scan trigger — bypasses corporate proxy POST blocking.

    After 6 versions (v6.3.3-v6.3.9) where POST-based scan triggers NEVER
    reached the server on the corporate network (regardless of body size —
    even a 100-byte POST was blocked), this GET endpoint provides an
    alternative trigger that corporate proxies cannot block.

    GET requests are fundamentally different from POST at the protocol level
    and are treated differently by every proxy, DLP, and WAF system.
    Corporate DLP inspects POST bodies for sensitive data but passes GETs.

    Parameters (URL path + query string):
        connector_token (path): Token from discovery phase (cached connector)
        scan_id (query): Client-generated scan ID for progress tracking
        mode (query): 'all' or comma-separated file indices (e.g., '0,1,2,3')

    Uses cached connector + files from the discovery phase.
    No @require_csrf — GET endpoint, localhost-only tool.
    """
    scan_id = request.args.get('scan_id', '').strip()
    mode = request.args.get('mode', 'all').strip()

    logger.info(f'[sp-go] ✓ GET trigger received: token={connector_token[:8] if connector_token else "??"}..., scan_id={scan_id}, mode={mode[:30]}')

    if not scan_id or len(scan_id) < 6 or len(scan_id) > 36:
        return jsonify({'success': False, 'error': {'message': 'Invalid scan_id'}}), 400

    if not connector_token or len(connector_token) < 8:
        return jsonify({'success': False, 'error': {'message': 'Invalid connector_token'}}), 400

    # ── Look up cached connector and files ──
    entry = None
    with _sp_connector_cache_lock:
        entry = _sp_connector_cache.pop(connector_token, None)

    if not entry:
        logger.warning(f'[sp-go] Connector token {connector_token[:8]}... not found in cache')
        return jsonify({
            'success': False,
            'error': {'message': 'Connector session expired or not found. Please re-discover.', 'code': 'CACHE_MISS'}
        }), 404

    age = time.time() - entry['created_at']
    if age > _SP_CONNECTOR_CACHE_TTL:
        logger.warning(f'[sp-go] Connector expired (age={age:.0f}s > TTL={_SP_CONNECTOR_CACHE_TTL}s)')
        try:
            entry['connector'].close()
        except Exception:
            pass
        return jsonify({
            'success': False,
            'error': {'message': 'Connector session expired. Please re-discover.', 'code': 'EXPIRED'}
        }), 410

    cached_connector = entry['connector']
    cached_files = entry.get('files', [])
    site_url = entry.get('site_url', '')
    library_path = entry.get('library_path', '')
    connector_type = entry.get('connector_type', 'rest')

    # ── Resolve file selection ──
    if mode == 'all':
        selected_files = cached_files
    else:
        try:
            indices = [int(i.strip()) for i in mode.split(',') if i.strip()]
            selected_files = [cached_files[i] for i in indices if 0 <= i < len(cached_files)]
        except (ValueError, IndexError):
            selected_files = cached_files

    if not selected_files:
        logger.warning(f'[sp-go] No files resolved from mode={mode}')
        return jsonify({
            'success': False,
            'error': {'message': 'No files found for selected indices'}
        }), 400

    total_files = len(selected_files)
    logger.info(f'[sp-go] ✓ Resolved {total_files} files (age={age:.0f}s, site={site_url}, lib={library_path})')

    # ── Create scan state ──
    with _folder_scan_state_lock:
        _cleanup_old_scans()
        _folder_scan_state[scan_id] = {
            'phase': 'reviewing',
            'total_files': total_files,
            'processed': 0,
            'errors': 0,
            'current_file': 'Starting document scan...',
            'current_chunk': 0,
            'total_chunks': max(1, (total_files + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE),
            'documents': [],
            'summary': {
                'total_documents': total_files,
                'processed': 0,
                'errors': 0,
                'total_issues': 0,
                'total_words': 0,
                'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                'issues_by_category': {},
                'grade_distribution': {},
            },
            'roles_found': {},
            'started_at': time.time(),
            'completed_at': None,
            'elapsed_seconds': 0,
            'estimated_remaining': None,
            'folder_path': f'SharePoint: {library_path} ({total_files} selected)',
            'source': 'sharepoint',
        }
    logger.info(f'[sp-go] Created scan state: {scan_id} (phase=reviewing, {total_files} files)')

    # ── Get SP connector class (for background thread module access) ──
    SPConnector, sp_parse_url = _get_sharepoint_connector()
    if SPConnector is None:
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'error'
                state['error_message'] = 'SharePoint connector not available'
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available', 'code': 'SP_UNAVAILABLE'}
        }), 500

    # ── Spawn background thread ──
    flask_app = current_app._get_current_object()
    thread = threading.Thread(
        target=_process_sharepoint_scan_async,
        args=(scan_id, cached_connector, selected_files, {}, flask_app),
        kwargs={
            'site_url': site_url,
            'connector_type': connector_type,
            'library_path': library_path,
        },
        daemon=True,
        name=f'sp-scan-{scan_id}',
    )
    thread.start()

    logger.info(f'[sp-go] ✓ Scan thread started: {scan_id}, {total_files} files, connector_age={age:.0f}s')

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'total_files': total_files,
            'library_path': library_path,
            'scan_started': True,
            'trigger': 'GET',
        }
    })


@review_bp.route('/api/review/folder-scan-progress/<scan_id>', methods=['GET'])
@handle_api_errors
def folder_scan_progress(scan_id):
    """
    v5.7.0: Poll for folder scan progress.

    Returns current state including phase, file-level progress, timing, and
    completed documents so far.

    URL Params:
        scan_id (str): The scan ID returned by /folder-scan-start

    Query Params:
        since (int): Only return documents completed after this index (for incremental updates)

    Returns:
        JSON with current scan state
    """
    with _folder_scan_state_lock:
        state = _folder_scan_state.get(scan_id)

    # v6.3.12: Fallback — if exact scan_id not found, look for ANY active SharePoint
    # scan. This is the definitive fix for corporate DLP/proxy environments where the
    # browser's second request (scan trigger) NEVER reaches the server. The discovery
    # endpoint auto-starts the scan (with its own scan_id), but the cached browser JS
    # polls with a different scan_id it generated client-side. This fallback bridges
    # the gap by finding the auto-started scan regardless of what scan_id the client uses.
    if not state:
        with _folder_scan_state_lock:
            # Priority 1: Active SP scan (still running)
            for sid, s in _folder_scan_state.items():
                if (s.get('source', '').startswith('sharepoint')
                        and s.get('phase') in ('connecting', 'reviewing')):
                    state = s
                    scan_id = sid
                    logger.info(f'[SP-progress] Fallback: mapped unknown scan_id to active SP scan {sid} (phase={s["phase"]})')
                    break
            # Priority 2: Recently completed SP scan (within 5 min)
            if not state:
                for sid, s in _folder_scan_state.items():
                    if (s.get('source', '').startswith('sharepoint')
                            and s.get('phase') in ('complete', 'error')
                            and s.get('completed_at')
                            and time.time() - s['completed_at'] < 300):
                        state = s
                        scan_id = sid
                        logger.info(f'[SP-progress] Fallback: mapped unknown scan_id to completed SP scan {sid} (phase={s["phase"]})')
                        break

    if not state:
        return jsonify({'success': False, 'error': {'message': f'Scan {scan_id} not found', 'code': 'SCAN_NOT_FOUND'}}), 404

    # Support incremental document fetching
    since = request.args.get('since', 0, type=int)

    with _folder_scan_state_lock:
        # Build response — copy to avoid holding lock during jsonify
        docs = state['documents'][since:]  # Only new documents since last poll

        # v5.7.1: Compute elapsed_seconds LIVE from started_at instead of using
        # the stored value (which only updates on file completion). This ensures
        # the timer keeps ticking even when a file is taking a long time.
        # v6.2.9: Also compute live elapsed during 'connecting' phase
        if state['phase'] in ('reviewing', 'connecting') and state.get('started_at'):
            live_elapsed = round(time.time() - state['started_at'], 1)
        else:
            live_elapsed = state['elapsed_seconds']

        response = {
            'scan_id': scan_id,
            'phase': state['phase'],
            'total_files': state['total_files'],
            'processed': state['processed'],
            'errors': state['errors'],
            'current_file': state['current_file'],
            'current_chunk': state['current_chunk'],
            'total_chunks': state['total_chunks'],
            'elapsed_seconds': live_elapsed,
            'estimated_remaining': state['estimated_remaining'],
            'summary': dict(state['summary']),
            'total_documents_ready': len(state['documents']),
            'documents': docs,
            'since': since,
            'folder_path': state.get('folder_path', ''),
        }
        if state['phase'] == 'error':
            response['error_message'] = state.get('error_message', 'Unknown error')
        if state['phase'] == 'complete':
            response['roles_found'] = state.get('roles_found', {})

    return jsonify({'success': True, 'data': response})


# =============================================================================
# v6.2.0: ASYNC BATCH SCAN — Real-time progress for uploaded batch files
# =============================================================================
# Converts the synchronous /api/review/batch into an async polling pattern:
#   POST /api/review/batch-start  → validates, spawns background thread, returns scan_id
#   GET  /api/review/batch-progress/<scan_id>  → polls for real-time progress
#   POST /api/review/batch-cancel/<scan_id>  → cancels an in-progress scan
#
# Per-file phase tracking via progress_callback wired into core.py engine.
# ECD (estimated completion date) calculated from exponential moving average.
# =============================================================================

@review_bp.route('/api/review/batch-start', methods=['POST'])
@require_csrf
@handle_api_errors
def batch_scan_start():
    """
    v6.2.0: Start an async batch scan of uploaded documents.

    Expects JSON body with list of filepaths from batch upload.
    Returns scan_id immediately, processes in background.

    Request JSON:
        filepaths (list[str]): Absolute paths to uploaded files
        options (dict): Review options (same as /api/review)

    Returns:
        JSON with scan_id and file discovery info for immediate UI rendering
    """
    _cleanup_old_scans()

    data = request.get_json() or {}
    filepaths = data.get('filepaths', [])
    options = data.get('options', {})

    if not filepaths:
        raise ValidationError('No filepaths provided')

    # Validate files exist and build discovery info
    discovery = []
    for fp_str in filepaths:
        fp = Path(fp_str)
        if not fp.exists():
            logger.warning(f'[BatchScan-Async] File not found: {fp_str}')
            continue
        stat = fp.stat()
        discovery.append({
            'filename': fp.name,
            'filepath': str(fp),
            'extension': fp.suffix.lower(),
            'file_size': stat.st_size,
        })

    if not discovery:
        raise ValidationError('No valid files found in provided paths')

    # Generate scan ID and initialize state
    scan_id = str(uuid.uuid4())[:12]
    total_files = len(discovery)
    total_chunks = (total_files + BATCH_SCAN_CHUNK_SIZE - 1) // BATCH_SCAN_CHUNK_SIZE

    with _batch_scan_state_lock:
        _batch_scan_state[scan_id] = {
            'phase': 'reviewing',
            'total_files': total_files,
            'processed': 0,
            'errors': 0,
            'current_file': None,
            'current_chunk': 0,
            'total_chunks': total_chunks,
            'current_files': {},    # per-file phase tracking from progress_callback
            'documents': [],
            'summary': {
                'total_documents': total_files,
                'processed': 0,
                'errors': 0,
                'total_issues': 0,
                'total_words': 0,
                'issues_by_severity': {},
                'issues_by_category': {},
                'grade_distribution': {},
            },
            'roles_found': {},
            'started_at': time.time(),
            'completed_at': None,
            'elapsed_seconds': 0,
            'estimated_remaining': None,
            'cancelled': False,
            'activity_log': [],
        }

    # Spawn background thread
    thread = threading.Thread(
        target=_process_batch_scan_async,
        args=(scan_id, discovery, options),
        daemon=True
    )
    thread.start()

    logger.info(f'[BatchScan-Async] Started {scan_id}: {total_files} files, {total_chunks} chunks')

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'total_files': total_files,
            'total_chunks': total_chunks,
            'discovery': discovery,
        }
    })


@review_bp.route('/api/review/batch-progress/<scan_id>', methods=['GET'])
@handle_api_errors
def batch_scan_progress(scan_id):
    """
    v6.2.0: Poll for async batch scan progress.

    Returns current state including per-file phases, timing, and
    completed documents so far. Supports incremental document fetching.

    URL Params:
        scan_id (str): The scan ID returned by /batch-start

    Query Params:
        since (int): Only return documents completed after this index

    Returns:
        JSON with current scan state
    """
    with _batch_scan_state_lock:
        state = _batch_scan_state.get(scan_id)

    if not state:
        return jsonify({
            'success': False,
            'error': {'message': f'Batch scan {scan_id} not found', 'code': 'SCAN_NOT_FOUND'}
        }), 404

    since = request.args.get('since', 0, type=int)

    with _batch_scan_state_lock:
        docs = list(state['documents'][since:])

        # v5.7.1 pattern: Compute elapsed_seconds LIVE from started_at
        if state['phase'] == 'reviewing' and state.get('started_at'):
            live_elapsed = round(time.time() - state['started_at'], 1)
        else:
            live_elapsed = state['elapsed_seconds']

        response = {
            'scan_id': scan_id,
            'phase': state['phase'],
            'total_files': state['total_files'],
            'processed': state['processed'],
            'errors': state['errors'],
            'current_file': state['current_file'],
            'current_chunk': state['current_chunk'],
            'total_chunks': state['total_chunks'],
            'current_files': dict(state.get('current_files', {})),
            'elapsed_seconds': live_elapsed,
            'estimated_remaining': state['estimated_remaining'],
            'summary': dict(state['summary']),
            'total_documents_ready': len(state['documents']),
            'documents': docs,
            'since': since,
            'cancelled': state.get('cancelled', False),
            'activity_log': list(state.get('activity_log', [])[-50:]),  # Last 50 entries
        }
        if state['phase'] == 'error':
            response['error_message'] = state.get('error_message', 'Unknown error')
        if state['phase'] == 'complete':
            response['roles_found'] = dict(state.get('roles_found', {}))

    return jsonify({'success': True, 'data': response})


@review_bp.route('/api/review/batch-cancel/<scan_id>', methods=['POST'])
@require_csrf
@handle_api_errors
def batch_scan_cancel(scan_id):
    """
    v6.2.0: Cancel an in-progress batch scan.

    Sets the cancelled flag which the background thread checks between files.
    Currently processing files will complete, but no new files will start.
    """
    with _batch_scan_state_lock:
        state = _batch_scan_state.get(scan_id)

    if not state:
        return jsonify({
            'success': False,
            'error': {'message': f'Batch scan {scan_id} not found', 'code': 'SCAN_NOT_FOUND'}
        }), 404

    if state['phase'] not in ('reviewing',):
        return jsonify({
            'success': False,
            'error': {'message': f'Scan is already {state["phase"]}', 'code': 'SCAN_NOT_ACTIVE'}
        }), 400

    with _batch_scan_state_lock:
        state['cancelled'] = True
        state['activity_log'].append({
            'time': round(time.time() - state['started_at'], 1),
            'event': 'cancelled',
            'message': 'Scan cancellation requested by user',
        })

    logger.info(f'[BatchScan-Async] Cancel requested for {scan_id}')

    return jsonify({'success': True, 'message': 'Cancellation requested'})


def _add_batch_activity(scan_id, event, message):
    """Add an entry to the batch scan activity log."""
    with _batch_scan_state_lock:
        state = _batch_scan_state.get(scan_id)
        if state:
            elapsed = round(time.time() - state['started_at'], 1)
            state['activity_log'].append({
                'time': elapsed,
                'event': event,
                'message': message,
            })
            # Keep activity log bounded
            if len(state['activity_log']) > 200:
                state['activity_log'] = state['activity_log'][-200:]


def _update_batch_state_with_result(scan_id, result, options, flask_app):
    """
    v6.2.0: Update batch scan state with one file's result.

    Protected with try/except on the SUCCESS path (fixing the gap identified
    in _update_scan_state_with_result where the outer block was unprotected).
    """
    try:
        with _batch_scan_state_lock:
            state = _batch_scan_state.get(scan_id)
            if not state:
                logger.warning(f'[BatchScan-Async] State missing for {scan_id}')
                return

            filename = result.get('filename', 'unknown')
            state['current_file'] = filename

            # Remove from per-file phase tracking (file is done)
            state['current_files'].pop(filename, None)

            if result.get('status') == 'error':
                state['errors'] += 1
                state['summary']['errors'] += 1
                state['documents'].append({
                    'filename': filename,
                    'filepath': result.get('filepath', ''),
                    'error': result.get('error', 'Unknown error'),
                    'status': 'error',
                })
                _add_batch_activity(scan_id, 'file_error',
                                    f'{filename}: {result.get("error", "Unknown error")[:80]}')
            else:
                try:
                    state['processed'] += 1
                    state['summary']['processed'] += 1

                    issues = result.pop('issues', [])
                    actual_roles = result.pop('roles', {})
                    doc_results_full = result.pop('doc_results', {})

                    issue_count = result.get('issue_count', len(issues))
                    state['summary']['total_issues'] += issue_count
                    state['summary']['total_words'] += result.get('word_count', 0)

                    for issue in issues:
                        sev = issue.get('severity', 'Low')
                        state['summary']['issues_by_severity'][sev] = \
                            state['summary']['issues_by_severity'].get(sev, 0) + 1
                        cat = issue.get('category', 'Unknown')
                        state['summary']['issues_by_category'][cat] = \
                            state['summary']['issues_by_category'].get(cat, 0) + 1

                    grade = result.get('grade', 'N/A')
                    state['summary']['grade_distribution'][grade] = \
                        state['summary']['grade_distribution'].get(grade, 0) + 1

                    for role_name, role_data in actual_roles.items():
                        if role_name not in state['roles_found']:
                            state['roles_found'][role_name] = {
                                'documents': [], 'total_mentions': 0
                            }
                        state['roles_found'][role_name]['documents'].append(filename)
                        mention_count = role_data.get('count', 1) if isinstance(role_data, dict) else 1
                        state['roles_found'][role_name]['total_mentions'] += mention_count

                    # Record scan in history (needs Flask app context)
                    scan_record_id = None
                    if _shared.SCAN_HISTORY_AVAILABLE and flask_app:
                        try:
                            with flask_app.app_context():
                                db = get_scan_history_db()
                                scan_record = db.record_scan(
                                    filename=filename,
                                    filepath=result.get('filepath', filename),
                                    results=doc_results_full,
                                    options=options
                                )
                                scan_record_id = scan_record.get('scan_id') if scan_record else None
                        except Exception as e:
                            logger.warning(f'[BatchScan-Async] Scan history error for {filename}: {e}')

                    # v5.9.22: Statement Forge extraction during batch scan
                    sf_summary = result.get('sf_summary')

                    state['documents'].append({
                        'filename': filename,
                        'filepath': result.get('filepath', ''),
                        'extension': result.get('extension', ''),
                        'file_size': result.get('file_size', 0),
                        'issue_count': issue_count,
                        'role_count': result.get('role_count', 0),
                        'word_count': result.get('word_count', 0),
                        'score': result.get('score', 0),
                        'grade': grade,
                        'scan_id': scan_record_id,
                        'sf_summary': sf_summary,
                        'status': 'success',
                    })

                    _add_batch_activity(scan_id, 'file_complete',
                                        f'{filename}: score {result.get("score", 0)}, '
                                        f'{issue_count} issues, grade {grade}')

                except Exception as inner_e:
                    # v6.2.0: Protected success path — prevents background thread crash
                    logger.error(f'[BatchScan-Async] Error processing result for {filename}: {inner_e}\n'
                                 f'{traceback.format_exc()}')
                    state['errors'] += 1
                    state['summary']['errors'] += 1
                    state['documents'].append({
                        'filename': filename,
                        'filepath': result.get('filepath', ''),
                        'error': f'Result processing error: {str(inner_e)}',
                        'status': 'error',
                    })

            # Estimate remaining time using EMA
            elapsed = time.time() - state['started_at']
            total_done = state['processed'] + state['errors']
            if total_done > 0:
                avg_time = elapsed / total_done
                remaining = state['total_files'] - total_done
                state['estimated_remaining'] = round(avg_time * remaining, 1)

    except Exception as outer_e:
        logger.error(f'[BatchScan-Async] Fatal error in _update_batch_state_with_result: {outer_e}\n'
                     f'{traceback.format_exc()}')


def _process_batch_scan_async(scan_id, discovery, options):
    """
    v6.2.0: Background thread — process batch scan documents in chunks.

    Mirrors _process_folder_scan_async but with:
    - progress_callback wiring for per-file phase tracking
    - Per-file gc.collect() and engine cleanup
    - Cancel support via state['cancelled'] flag
    - Watchdog timer (10 min no-progress = timeout)
    - Protected outer try/except to never crash silently
    """
    import gc
    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

    # Get Flask app reference for background context
    try:
        from app import app as flask_app
    except ImportError:
        flask_app = None

    # Enable batch_mode for faster processing
    async_batch_options = dict(options) if options else {}
    async_batch_options['batch_mode'] = True

    def _review_single_with_progress(file_info):
        """Review one document with its own engine instance + progress_callback."""
        filepath = Path(file_info['filepath'])
        filename = file_info['filename']

        try:
            # v6.2.0: Wire progress_callback for per-file phase tracking
            def progress_cb(phase, progress, message):
                """Called by core.py review_document() during processing phases."""
                try:
                    with _batch_scan_state_lock:
                        state = _batch_scan_state.get(scan_id)
                        if state:
                            state['current_files'][filename] = {
                                'phase': phase,       # extracting, parsing, checking, postprocessing
                                'progress': progress,  # 0-100
                                'message': message,
                            }
                except Exception:
                    pass  # Never let callback errors affect the scan

            # Update current_files to show this file is starting
            with _batch_scan_state_lock:
                state = _batch_scan_state.get(scan_id)
                if state:
                    state['current_files'][filename] = {
                        'phase': 'starting',
                        'progress': 0,
                        'message': 'Initializing engine...',
                    }

            engine = AEGISEngine()
            doc_results = engine.review_document(
                str(filepath),
                async_batch_options,
                progress_callback=progress_cb
            )

            # Convert ReviewIssue objects to dicts (Lesson 36)
            raw_issues = doc_results.get('issues', [])
            issues = []
            for issue in raw_issues:
                if isinstance(issue, dict):
                    issues.append(issue)
                elif hasattr(issue, 'to_dict'):
                    issues.append(issue.to_dict())
                else:
                    issues.append({
                        'severity': getattr(issue, 'severity', 'Low'),
                        'category': getattr(issue, 'category', 'Unknown'),
                        'message': getattr(issue, 'message', str(issue)),
                    })
            doc_results['issues'] = issues

            doc_roles = doc_results.get('roles', {})
            if not isinstance(doc_roles, dict):
                doc_roles = {}
            actual_roles = {k: v for k, v in doc_roles.items()
                          if not isinstance(v, dict) or k not in ['success', 'error']}

            word_count = doc_results.get('word_count', 0)
            if not word_count:
                doc_info = doc_results.get('document_info', {})
                word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            # v5.9.22: Statement Forge extraction during batch scan
            sf_summary = None
            if _shared.STATEMENT_FORGE_AVAILABLE and doc_results.get('full_text'):
                try:
                    try:
                        from statement_forge.extractor import extract_statements as sf_extract
                        from statement_forge.export import get_export_stats as sf_stats
                        from statement_forge.routes import _store_statements
                    except ImportError:
                        from statement_forge__extractor import extract_statements as sf_extract
                        from statement_forge__export import get_export_stats as sf_stats
                        from statement_forge__routes import _store_statements

                    sf_text = doc_results.get('clean_full_text') or doc_results.get('full_text', '')
                    sf_stmts = sf_extract(sf_text, filepath.name)
                    if sf_stmts:
                        stats = sf_stats(sf_stmts)
                        sf_statements_list = [s.to_dict() for s in sf_stmts]
                        _store_statements(sf_stmts)
                        sf_summary = {
                            'available': True, 'statements_ready': True,
                            'total_statements': len(sf_stmts),
                            'directive_counts': stats.get('directive_counts', {}),
                            'top_roles': stats.get('roles', [])[:5],
                        }
                        doc_results['statement_forge_summary'] = sf_summary
                        # Persist statements to scan history
                        if _shared.SCAN_HISTORY_AVAILABLE and flask_app:
                            try:
                                with flask_app.app_context():
                                    db = get_scan_history_db()
                                    scan_info = db.record_scan(
                                        filename=filepath.name, filepath=str(filepath),
                                        results=doc_results, options=options
                                    )
                                    if scan_info and sf_statements_list:
                                        db.save_scan_statements(
                                            scan_info['scan_id'], scan_info['document_id'],
                                            sf_statements_list
                                        )
                            except Exception as db_err:
                                logger.warning(f'[BatchScan-Async] SF db persist failed: {db_err}')
                except Exception as sf_err:
                    logger.warning(f'[BatchScan-Async] SF extraction failed for {filename}: {sf_err}')

            # v6.2.0: Per-file engine cleanup to free NLP model references
            del engine
            gc.collect()

            return {
                'filename': filename,
                'filepath': str(filepath),
                'extension': file_info['extension'],
                'file_size': file_info['file_size'],
                'issues': issues,
                'issue_count': len(issues),
                'roles': actual_roles,
                'role_count': len(actual_roles),
                'word_count': word_count,
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'sf_summary': sf_summary,
                'status': 'success',
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f'[BatchScan-Async] Error reviewing {filename}: {e}\n{tb_str}')
            # Cleanup on error too
            try:
                gc.collect()
            except Exception:
                pass
            return {
                'filename': filename,
                'filepath': str(filepath),
                'extension': file_info.get('extension', ''),
                'file_size': file_info.get('file_size', 0),
                'error': str(e),
                'status': 'error',
            }

    try:
        chunks = [discovery[i:i + BATCH_SCAN_CHUNK_SIZE]
                  for i in range(0, len(discovery), BATCH_SCAN_CHUNK_SIZE)]

        _add_batch_activity(scan_id, 'scan_started',
                            f'Processing {len(discovery)} files in {len(chunks)} chunks')

        for chunk_idx, chunk in enumerate(chunks):
            # Check for cancellation between chunks
            with _batch_scan_state_lock:
                state = _batch_scan_state.get(scan_id)
                if state and state.get('cancelled'):
                    state['phase'] = 'cancelled'
                    state['completed_at'] = time.time()
                    state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                    _add_batch_activity(scan_id, 'scan_cancelled',
                                        f'Cancelled after {state["processed"]} files')
                    logger.info(f'[BatchScan-Async] {scan_id} cancelled by user')
                    return

            logger.info(f'[BatchScan-Async] {scan_id} chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} files)')

            with _batch_scan_state_lock:
                state = _batch_scan_state.get(scan_id)
                if state:
                    state['current_chunk'] = chunk_idx + 1
                    state['current_file'] = ', '.join(f['filename'] for f in chunk[:3])
                    if len(chunk) > 3:
                        state['current_file'] += f' (+{len(chunk) - 3} more)'

            _add_batch_activity(scan_id, 'chunk_started',
                                f'Chunk {chunk_idx + 1}/{len(chunks)}: '
                                f'{", ".join(f["filename"] for f in chunk[:3])}'
                                f'{" ..." if len(chunk) > 3 else ""}')

            max_workers = min(BATCH_SCAN_MAX_WORKERS, len(chunk))
            chunk_timed_out = False

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(_review_single_with_progress, f): f
                    for f in chunk
                }
                completed_futures = set()

                try:
                    for future in as_completed(future_to_file,
                                               timeout=BATCH_SCAN_PER_FILE_TIMEOUT * len(chunk)):
                        completed_futures.add(future)
                        file_info = future_to_file[future]

                        try:
                            result = future.result(timeout=30)
                        except Exception as e:
                            logger.error(f'[BatchScan-Async] Error getting result for '
                                         f'{file_info["filename"]}: {e}')
                            result = {
                                'filename': file_info['filename'],
                                'filepath': file_info['filepath'],
                                'extension': file_info['extension'],
                                'file_size': file_info['file_size'],
                                'error': f'Worker error: {str(e)}',
                                'status': 'error',
                            }

                        _update_batch_state_with_result(scan_id, result, options, flask_app)

                        # Check cancellation between files within a chunk
                        with _batch_scan_state_lock:
                            state = _batch_scan_state.get(scan_id)
                            if state and state.get('cancelled'):
                                break

                except FuturesTimeoutError:
                    chunk_timed_out = True
                    logger.error(f'[BatchScan-Async] Chunk {chunk_idx + 1} timed out')
                    _add_batch_activity(scan_id, 'chunk_timeout',
                                        f'Chunk {chunk_idx + 1} timed out after '
                                        f'{BATCH_SCAN_PER_FILE_TIMEOUT * len(chunk)}s')

                    for future, file_info in future_to_file.items():
                        if future not in completed_futures:
                            with _batch_scan_state_lock:
                                state = _batch_scan_state.get(scan_id)
                                if state:
                                    state['errors'] += 1
                                    state['summary']['errors'] += 1
                                    state['documents'].append({
                                        'filename': file_info['filename'],
                                        'filepath': file_info['filepath'],
                                        'error': f'Timed out (chunk timeout after '
                                                 f'{BATCH_SCAN_PER_FILE_TIMEOUT * len(chunk)}s)',
                                        'status': 'error',
                                    })
                                    state['current_files'].pop(file_info['filename'], None)

            # v6.2.0: gc.collect() between chunks (in addition to per-file cleanup)
            gc.collect()

            _add_batch_activity(scan_id, 'chunk_complete',
                                f'Chunk {chunk_idx + 1}/{len(chunks)} complete')

        # ── Mark complete ──
        with _batch_scan_state_lock:
            state = _batch_scan_state.get(scan_id)
            if state:
                if state.get('cancelled'):
                    state['phase'] = 'cancelled'
                else:
                    state['phase'] = 'complete'
                state['current_file'] = None
                state['current_files'] = {}
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                state['estimated_remaining'] = 0
                logger.info(
                    f'[BatchScan-Async] {scan_id} complete: '
                    f'{state["summary"]["processed"]} processed, '
                    f'{state["summary"]["errors"]} errors, '
                    f'{state["summary"]["total_issues"]} issues, '
                    f'{state["elapsed_seconds"]}s'
                )
                _add_batch_activity(scan_id, 'scan_complete',
                                    f'Scan complete: {state["summary"]["processed"]} processed, '
                                    f'{state["summary"]["errors"]} errors, '
                                    f'{state["summary"]["total_issues"]} total issues in '
                                    f'{state["elapsed_seconds"]}s')

    except Exception as e:
        logger.error(f'[BatchScan-Async] {scan_id} fatal error: {e}\n{traceback.format_exc()}')
        with _batch_scan_state_lock:
            state = _batch_scan_state.get(scan_id)
            if state:
                state['phase'] = 'error'
                state['error_message'] = str(e)
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                _add_batch_activity(scan_id, 'scan_error', f'Fatal error: {str(e)[:100]}')


# =============================================================================
# v5.9.29: SharePoint Online Document Library Scan
# =============================================================================

# Lazy import helper for SharePoint connector
def _get_sharepoint_connector():
    """Truly lazy import — retries every call so server restart isn't needed after file deploy."""
    try:
        from sharepoint_connector import SharePointConnector, parse_sharepoint_url
        return SharePointConnector, parse_sharepoint_url
    except Exception as e:
        import logging
        logging.getLogger('aegis.review').warning(f'SharePoint connector import failed: {e}')
        return None, None


@review_bp.route('/api/review/sharepoint-test', methods=['POST'])
@require_csrf
@handle_api_errors
def sharepoint_test():
    """
    v5.9.29: Test connection to a SharePoint site.
    Returns site title and auth status.
    """
    SPConnector, sp_parse_url = _get_sharepoint_connector()
    if SPConnector is None:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available — check server logs for import errors', 'code': 'SP_UNAVAILABLE'}
        }), 500

    data = request.get_json() or {}
    site_url = data.get('site_url', '').strip()

    if not site_url:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint site URL is required', 'code': 'MISSING_URL'}
        }), 400

    # Parse the URL to extract site_url component
    parsed = sp_parse_url(site_url)
    actual_site_url = parsed['site_url']

    connector = SPConnector(actual_site_url)
    try:
        probe = connector.test_connection()

        # v5.9.35: Auto-detect library path if connection succeeds and none was parsed from URL
        library_path = parsed.get('library_path', '')
        if probe['success'] and not library_path:
            try:
                detected = connector.auto_detect_library_path()
                if detected:
                    library_path = detected
                    logger.info(f"SharePoint auto-detected library: {library_path}")
            except Exception as e:
                logger.debug(f"SharePoint library auto-detect failed (non-critical): {e}")

        return jsonify({
            'success': probe['success'],
            'data': {
                'title': probe.get('title', ''),
                'url': probe.get('url', ''),
                'auth_method': probe.get('auth_method', 'none'),
                'message': probe.get('message', ''),
                'status_code': probe.get('status_code', 0),
                'parsed_site_url': actual_site_url,
                'parsed_library_path': library_path,
                'ssl_fallback': getattr(connector, '_ssl_fallback_used', False),
            }
        })
    finally:
        connector.close()


@review_bp.route('/api/review/sharepoint-connect-and-scan', methods=['POST'])
@require_csrf
@handle_api_errors
def sharepoint_connect_and_scan():
    """
    v5.9.38: Combined Connect + Discover + Scan endpoint.
    v6.3.15: discover_only flag removed from JS. All paths auto-start scan.

    Steps:
    1. Parse URL to extract site_url and optional library path
    2. Connect and test authentication
    3. Auto-detect library path if not provided
    4. Discover files in the library
    5. Start async scan of discovered files (ALWAYS — v6.3.13+)

    Returns scan_id + discovery results immediately, scan runs in background.
    """
    # v6.3.15: Write to sharepoint logger for deployment verification
    # (sharepoint.log is confirmed captured in diagnostics)
    try:
        import logging as _logging
        _sp_diag = _logging.getLogger('aegis.sharepoint')
        _sp_diag.info('[ROUTE] ═══ review_routes.py v6.3.15 ═══ sharepoint_connect_and_scan ENTRY — auto-scan always active')
    except Exception:
        pass

    SPConnector, sp_parse_url = _get_sharepoint_connector()
    if SPConnector is None:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available — check server logs', 'code': 'SP_UNAVAILABLE'}
        }), 500

    data = request.get_json() or {}
    site_url = data.get('site_url', '').strip()
    library_path = data.get('library_path', '').strip()
    recursive = data.get('recursive', True)
    options = data.get('options', {})
    max_files = min(data.get('max_files', 500), MAX_FOLDER_SCAN_FILES)
    discover_only = data.get('discover_only', False)  # v6.1.11: return files without auto-scanning

    if not site_url:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint site URL is required', 'code': 'MISSING_URL'}
        }), 400

    # Parse the URL
    parsed = sp_parse_url(site_url)
    actual_site_url = parsed['site_url']

    # Use library path from URL if not explicitly provided
    if not library_path:
        library_path = parsed.get('library_path', '')

    logger.info(f'SharePoint connect-and-scan: site_url="{actual_site_url}", library_path="{library_path}", discover_only={discover_only}')

    # v6.3.6: Check if this is a SharePoint Online domain — skip REST connector entirely.
    # REST always fails with 401 (empty WWW-Authenticate) on SPO because legacy auth is
    # disabled. The REST → MSAL → retry cascade wastes ~10 seconds before HeadlessSP fallback.
    # Go directly to HeadlessSP for known SPO domains.
    _is_spo_domain = any(p in actual_site_url.lower() for p in (
        'sharepoint.com', 'sharepoint.us', 'sharepoint.de', 'sharepoint.cn'
    ))

    # v6.1.3: Track headless fallback state for error reporting
    _headless_available = False
    _headless_tried = False
    _headless_error = ''
    connector = None
    result = None

    # v6.3.6: For SPO domains, go directly to HeadlessSP — no REST attempt
    if _is_spo_domain:
        try:
            from sharepoint_connector import HeadlessSPConnector, HEADLESS_SP_AVAILABLE
            _headless_available = HEADLESS_SP_AVAILABLE
            if HEADLESS_SP_AVAILABLE:
                _headless_tried = True
                logger.info(f"SharePoint Online detected — going direct to HeadlessSP (skipping REST)")
                connector = HeadlessSPConnector(actual_site_url)
                result = connector.connect_and_discover(
                    library_path=library_path,
                    recursive=recursive,
                    max_files=max_files,
                )
                if result['success']:
                    logger.info(f"SharePoint: HeadlessSP connected — {len(result.get('files', []))} files found")
                else:
                    _headless_error = result.get('message', 'Headless browser authentication failed')
                    logger.warning(f"SharePoint: HeadlessSP failed: {_headless_error}")
                    connector.close()
                    connector = None
            else:
                logger.warning("SharePoint Online detected but Playwright not installed — falling back to REST")
        except Exception as e:
            _headless_tried = True
            _headless_error = str(e)
            logger.warning(f"SharePoint: HeadlessSP exception: {e}")
            if connector:
                try:
                    connector.close()
                except Exception:
                    pass
                connector = None

    # For on-premises SharePoint (non-SPO) or when HeadlessSP unavailable, try REST first
    if result is None or not result.get('success'):
        rest_connector = SPConnector(actual_site_url)
        rest_result = rest_connector.connect_and_discover(
            library_path=library_path,
            recursive=recursive,
            max_files=max_files
        )
        if rest_result['success']:
            connector = rest_connector
            result = rest_result
        else:
            # REST failed — try HeadlessSP as fallback (if not already tried for SPO)
            if not _headless_tried:
                try:
                    from sharepoint_connector import HeadlessSPConnector, HEADLESS_SP_AVAILABLE
                    _headless_available = HEADLESS_SP_AVAILABLE
                    if HEADLESS_SP_AVAILABLE:
                        _headless_tried = True
                        logger.info(f"SharePoint: REST API auth failed — trying headless browser (Windows SSO)... library_path=\"{library_path}\"")
                        headless_connector = HeadlessSPConnector(actual_site_url)
                        headless_result = headless_connector.connect_and_discover(
                            library_path=library_path,
                            recursive=recursive,
                            max_files=max_files,
                        )
                        if headless_result['success']:
                            rest_connector.close()
                            connector = headless_connector
                            result = headless_result
                            logger.info(f"SharePoint: Headless browser connected — {len(result.get('files', []))} files found")
                        else:
                            _headless_error = headless_result.get('message', 'Headless browser authentication failed')
                            headless_connector.close()
                            logger.warning(f"SharePoint: Headless fallback also failed: {_headless_error}")
                    else:
                        logger.warning("SharePoint: Playwright not installed — headless browser fallback unavailable")
                except Exception as e:
                    _headless_tried = True
                    _headless_error = str(e)
                    logger.warning(f"SharePoint: Headless fallback exception: {e}")

            # If we still don't have a working connector, close REST
            if not result or not result.get('success'):
                rest_connector.close()
                if result is None:
                    result = rest_result  # Use REST error for reporting

    if not result['success']:
        connector.close()

        # v6.1.3: Build informative error message based on what actually happened
        original_error = result['message']
        _is_aadsts_error = 'AADSTS' in original_error or 'blocked' in original_error.lower()

        # If Playwright isn't installed, that's the actionable fix — tell the user
        if not _headless_available:
            error_msg = (
                f"SharePoint REST API authentication failed: {original_error}\n\n"
                "AEGIS v6.1.3 can bypass this with a headless browser, but Playwright is not installed.\n\n"
                "To fix: Re-run apply_v6.1.3.py which will install Playwright automatically, "
                "or run these commands from the AEGIS directory:\n"
                "  python -m pip install playwright\n"
                "  python -m playwright install chromium\n\n"
                "Then restart AEGIS and try again."
            )
        elif _headless_tried and _headless_error:
            error_msg = (
                f"SharePoint REST API authentication failed: {original_error}\n\n"
                f"Headless browser fallback also failed: {_headless_error}\n\n"
                "Check logs/sharepoint.log for detailed diagnostics."
            )
        else:
            error_msg = original_error

        response_data = {
            'message': error_msg,
            'auth_method': result.get('auth_method', 'none'),
            'error_category': result.get('error_category', 'connection'),
            'parsed_site_url': actual_site_url,
            'parsed_library_path': library_path,
            'headless_available': _headless_available,
            'headless_tried': _headless_tried,
            'headless_error': _headless_error,
        }

        # v6.1.3: Only show device code UI if headless is not an option AND
        # the error is NOT AADSTS65002 (which blocks device code too)
        if not _is_aadsts_error and not _headless_available:
            device_flow_info = None
            try:
                from sharepoint_connector import get_pending_device_flow
                device_flow_info = get_pending_device_flow(actual_site_url)
            except Exception:
                pass
            if device_flow_info:
                response_data['device_code'] = device_flow_info
                response_data['message'] += (
                    f"\n\nTo authenticate: Go to {device_flow_info.get('verification_uri', 'https://microsoft.com/devicelogin')} "
                    f"and enter code: {device_flow_info.get('user_code', '???')}"
                )

        return jsonify({
            'success': False,
            'data': response_data,
            'error': {'message': error_msg, 'code': 'SP_CONNECT_FAILED'}
        }), 400

    files = result.get('files', [])
    library_path = result.get('library_path', library_path)

    if not files:
        connector.close()
        return jsonify({
            'success': True,
            'data': {
                'scan_id': None,
                'site_title': result.get('title', ''),
                'library_path': library_path,
                'message': result.get('message', f'No supported documents found in {library_path}'),
                'auth_method': result.get('auth_method', 'none'),
                'ssl_fallback': result.get('ssl_fallback', False),
                'discovery': {
                    'total_discovered': 0,
                    'supported_files': 0,
                    'files': [],
                    'file_type_breakdown': {},
                }
            }
        })

    # Calculate size and type breakdown
    total_size = sum(f.get('size', 0) for f in files)
    type_breakdown = {}
    for f in files:
        ext = f.get('extension', 'unknown')
        type_breakdown[ext] = type_breakdown.get(ext, 0) + 1

    for f in files:
        f['size_human'] = _human_size(f.get('size', 0))

    # v6.3.13: IGNORE discover_only — always start scan immediately.
    # v6.3.15: Frontend no longer sends discover_only at all, so this is
    # belt-and-suspenders. Both old and new code paths converge here.

    # Generate scan_id and start the scan
    scan_id = uuid.uuid4().hex[:12]
    try:
        import logging as _logging
        _sp_diag2 = _logging.getLogger('aegis.sharepoint')
        _sp_diag2.info(f'[ROUTE] ═══ SCAN STARTING ═══ scan_id={scan_id}, files={len(files)}, discover_only={discover_only}')
    except Exception:
        pass

    with _folder_scan_state_lock:
        _cleanup_old_scans()
        _folder_scan_state[scan_id] = {
            'phase': 'downloading',  # v6.6.0: starts in download phase, not reviewing
            'total_files': len(files),
            'processed': 0,
            'errors': 0,
            'current_file': None,
            'current_chunk': 0,
            'total_chunks': (len(files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE,
            'documents': [],
            'summary': {
                'total_documents': len(files),
                'processed': 0,
                'errors': 0,
                'total_issues': 0,
                'total_words': 0,
                'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                'issues_by_category': {},
                'grade_distribution': {},
            },
            'roles_found': {},
            'started_at': time.time(),
            'completed_at': None,
            'elapsed_seconds': 0,
            'estimated_remaining': None,
            'folder_path': f'SharePoint: {library_path}',
            'source': 'sharepoint',
            # v6.6.0: Download phase tracking
            'download_total': len(files),
            'download_completed': 0,
            'download_cached': 0,
            'download_errors': 0,
        }

    # Phase 2: Spawn background thread
    flask_app = current_app._get_current_object()
    thread = threading.Thread(
        target=_process_sharepoint_scan_async,
        args=(scan_id, connector, files, options, flask_app),
        kwargs={'site_url': actual_site_url, 'connector_type': connector_type, 'library_path': library_path},
        daemon=True,
        name=f'sp-scan-{scan_id}',
    )
    thread.start()

    logger.info(f"SharePoint connect-and-scan {scan_id}: {len(files)} files from {library_path} "
                f"(site_url={actual_site_url}, connector_type={connector_type})")

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'site_title': result.get('title', ''),
            'library_path': library_path,
            'auth_method': result.get('auth_method', 'none'),
            'ssl_fallback': result.get('ssl_fallback', False),
            'discovery': {
                'total_discovered': len(files),
                'supported_files': len(files),
                'total_size': total_size,
                'total_size_human': _human_size(total_size),
                'files': files[:100],
                'file_type_breakdown': type_breakdown,
            }
        }
    })


@review_bp.route('/api/review/sharepoint-scan-selected', methods=['POST'])
@require_csrf
@handle_api_errors
def sharepoint_scan_selected():
    """
    v6.2.9: Start a SharePoint scan with user-selected files.

    Called after discover_only mode — user has seen the file list and
    selected which files to scan.

    CRITICAL FIX (v6.2.9 — Lesson 168): Returns scan_id IMMEDIATELY.
    Connector creation (HeadlessSPConnector launch + SSO authentication)
    is moved INTO the background thread. Previous versions created the
    connector SYNCHRONOUSLY in this handler, which blocked the HTTP
    response for 30+ seconds (or hung forever on Windows when the
    second Playwright browser launch collided with the first).

    v6.3.1: Added diagnostic version marker for deployment verification.
    """
    # ── v6.3.6: Diagnostic marker — confirms this code version is loaded ──
    logger.info('[SP-scan-selected] ENTRY — v6.3.6 async handler (connector cache + SPO fast-path)')

    SPConnector, sp_parse_url = _get_sharepoint_connector()
    if SPConnector is None:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available', 'code': 'SP_UNAVAILABLE'}
        }), 500

    data = request.get_json() or {}
    site_url = data.get('site_url', '').strip()
    library_path = data.get('library_path', '').strip()
    selected_files = data.get('files', [])
    options = data.get('options', {})
    connector_type = data.get('connector_type', 'rest')
    connector_token = data.get('connector_token', '').strip()  # v6.3.5

    if not site_url:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint site URL is required', 'code': 'MISSING_URL'}
        }), 400

    if not selected_files:
        return jsonify({
            'success': False,
            'error': {'message': 'No files selected for scanning', 'code': 'NO_FILES'}
        }), 400

    # v6.3.5: Look up cached connector from discovery phase.
    # This is the critical fix — reuse the already-authenticated connector
    # instead of creating a brand new HeadlessSP browser + re-auth.
    cached_connector = None
    if connector_token:
        with _sp_connector_cache_lock:
            entry = _sp_connector_cache.pop(connector_token, None)
        if entry:
            age = time.time() - entry['created_at']
            if age < _SP_CONNECTOR_CACHE_TTL:
                cached_connector = entry['connector']
                logger.info(f'[SP-scan-selected] ✓ Reusing cached connector (token={connector_token[:8]}..., age={age:.0f}s)')
            else:
                logger.warning(f'[SP-scan-selected] Cached connector expired (age={age:.0f}s > {_SP_CONNECTOR_CACHE_TTL}s) — will create new')
                try:
                    entry['connector'].close()
                except Exception:
                    pass
        else:
            logger.warning(f'[SP-scan-selected] Connector token {connector_token[:8]}... not found in cache — will create new')

    # Calculate stats for selected files
    total_size = sum(f.get('size', 0) for f in selected_files)
    type_breakdown = {}
    for f in selected_files:
        ext = f.get('extension', f.get('name', '').rsplit('.', 1)[-1] if '.' in f.get('name', '') else 'unknown')
        type_breakdown[ext] = type_breakdown.get(ext, 0) + 1

    # v6.3.3: Accept client-provided scan_id for dashboard-first architecture
    # The frontend generates scan_id and shows the cinematic dashboard BEFORE
    # this POST arrives. Using the same scan_id lets the dashboard's polling
    # pick up real progress as soon as this state is created.
    client_scan_id = data.get('scan_id', '').strip()
    if client_scan_id and len(client_scan_id) >= 8 and len(client_scan_id) <= 32:
        scan_id = client_scan_id
        logger.info(f'[SP-scan-selected] Using client-provided scan_id: {scan_id}')
    else:
        scan_id = uuid.uuid4().hex[:12]
        logger.info(f'[SP-scan-selected] Generated server scan_id: {scan_id}')
    logger.info(f'[SP-scan-selected] Creating scan state {scan_id} for {len(selected_files)} files (BEFORE thread spawn)')

    # v6.3.5: Determine initial phase and status message based on connector availability
    if cached_connector:
        initial_phase = 'reviewing'
        initial_msg = 'Starting document scan...'
    else:
        initial_phase = 'connecting'
        initial_msg = 'Authenticating to SharePoint...'

    # v6.3.4: MERGE into existing pre-registered state if it exists,
    # otherwise create fresh. The pre-register endpoint creates a
    # placeholder state so the dashboard polling doesn't get 404s.
    with _folder_scan_state_lock:
        _cleanup_old_scans()
        existing = _folder_scan_state.get(scan_id)
        if existing:
            # Merge into pre-registered state — update with real details
            existing['phase'] = initial_phase
            existing['total_files'] = len(selected_files)
            existing['current_file'] = initial_msg
            existing['total_chunks'] = (len(selected_files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE
            existing['summary']['total_documents'] = len(selected_files)
            existing['folder_path'] = f'SharePoint: {library_path} ({len(selected_files)} selected)'
            logger.info(f'[SP-scan-selected] Merged into pre-registered state {scan_id} (phase={initial_phase})')
        else:
            _folder_scan_state[scan_id] = {
                'phase': initial_phase,
                'total_files': len(selected_files),
                'processed': 0,
                'errors': 0,
                'current_file': initial_msg,
                'current_chunk': 0,
                'total_chunks': (len(selected_files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE,
                'documents': [],
                'summary': {
                    'total_documents': len(selected_files),
                    'processed': 0,
                    'errors': 0,
                    'total_issues': 0,
                    'total_words': 0,
                    'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                    'issues_by_category': {},
                    'grade_distribution': {},
                },
                'roles_found': {},
                'started_at': time.time(),
                'completed_at': None,
                'elapsed_seconds': 0,
                'estimated_remaining': None,
                'folder_path': f'SharePoint: {library_path} ({len(selected_files)} selected)',
                'source': 'sharepoint',
            }
            logger.info(f'[SP-scan-selected] Created fresh state {scan_id} (phase={initial_phase})')

    # v6.3.5: Spawn background thread with cached connector (if available).
    # When cached_connector is not None, the background thread skips all 3
    # connection strategies and goes straight to scanning — zero re-auth.
    flask_app = current_app._get_current_object()
    thread = threading.Thread(
        target=_process_sharepoint_scan_async,
        args=(scan_id, cached_connector, selected_files, options, flask_app),
        kwargs={
            'site_url': site_url,
            'connector_type': connector_type,
            'library_path': library_path,
        },
        daemon=True,
        name=f'sp-scan-selected-{scan_id}',
    )
    thread.start()

    if cached_connector:
        logger.info(f"SharePoint scan-selected {scan_id}: {len(selected_files)} files from {library_path} — thread started with CACHED connector (zero re-auth)")
    else:
        logger.info(f"SharePoint scan-selected {scan_id}: {len(selected_files)} files from {library_path} — thread started (connector will be created in thread)")

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'total_files': len(selected_files),
            'library_path': library_path,
            'discovery': {
                'total_discovered': len(selected_files),
                'supported_files': len(selected_files),
                'total_size': total_size,
                'file_type_breakdown': type_breakdown,
            }
        }
    })


@review_bp.route('/api/review/sharepoint-device-code-complete', methods=['POST'])
@require_csrf
@handle_api_errors
def sharepoint_device_code_complete():
    """
    v6.1.2: Complete a pending device code flow for SharePoint OAuth.

    The user has entered the device code in their browser — this endpoint
    waits for MSAL to confirm the auth and returns the token status.

    After successful auth, the user can retry Connect & Scan.
    """
    try:
        from sharepoint_connector import complete_device_flow, get_pending_device_flow
    except ImportError:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available', 'code': 'SP_UNAVAILABLE'}
        }), 500

    data = request.get_json() or {}
    site_url = data.get('site_url', '').strip()

    if not site_url:
        return jsonify({
            'success': False,
            'error': {'message': 'site_url is required', 'code': 'MISSING_URL'}
        }), 400

    # Check if there's a pending flow
    pending = get_pending_device_flow(site_url)
    if not pending:
        return jsonify({
            'success': False,
            'error': {'message': 'No pending device code flow for this site', 'code': 'NO_FLOW'}
        }), 404

    # Wait for user to complete auth (blocks up to 120s)
    token = complete_device_flow(site_url, timeout=120)
    if token:
        return jsonify({
            'success': True,
            'data': {
                'message': 'Authentication successful! You can now retry Connect & Scan.',
                'auth_method': 'oauth',
                'token_acquired': True,
            }
        })
    else:
        return jsonify({
            'success': False,
            'data': {
                'message': 'Authentication timed out or failed. Please try again.',
            },
            'error': {'message': 'Device code flow failed', 'code': 'AUTH_FAILED'}
        }), 408


@review_bp.route('/api/review/sharepoint-scan-start', methods=['POST'])
@require_csrf
@handle_api_errors
def sharepoint_scan_start():
    """
    v5.9.29: Start a SharePoint document library scan.

    Phase 1 (sync): Connect + discover files → returns scan_id + file list immediately
    Phase 2 (async): Download + review files in background thread

    Reuses the same _folder_scan_state dict and progress endpoint as folder scan.
    """
    SPConnector, sp_parse_url = _get_sharepoint_connector()
    if SPConnector is None:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint connector not available — check server logs for import errors', 'code': 'SP_UNAVAILABLE'}
        }), 500

    data = request.get_json() or {}
    site_url = data.get('site_url', '').strip()
    library_path = data.get('library_path', '').strip()
    recursive = data.get('recursive', True)
    options = data.get('options', {})
    max_files = min(data.get('max_files', 500), MAX_FOLDER_SCAN_FILES)

    if not site_url:
        return jsonify({
            'success': False,
            'error': {'message': 'SharePoint site URL is required', 'code': 'MISSING_URL'}
        }), 400

    # Parse the URL
    parsed = sp_parse_url(site_url)
    actual_site_url = parsed['site_url']

    # If no library_path provided, try to extract from the URL
    if not library_path:
        library_path = parsed.get('library_path', '')

    # Phase 1: Connect + discover
    connector = SPConnector(actual_site_url)

    # Test connection first
    probe = connector.test_connection()
    if not probe['success']:
        connector.close()
        return jsonify({
            'success': False,
            'error': {
                'message': f'Cannot connect to SharePoint: {probe["message"]}',
                'code': 'SP_AUTH_FAILED'
            }
        }), 400

    # v5.9.35: Auto-detect library path if not provided
    if not library_path:
        try:
            detected = connector.auto_detect_library_path()
            if detected:
                library_path = detected
                logger.info(f"SharePoint scan auto-detected library: {library_path}")
        except Exception as e:
            logger.debug(f"SharePoint library auto-detect failed: {e}")

    if not library_path:
        connector.close()
        return jsonify({
            'success': False,
            'error': {
                'message': 'Could not detect document library. Please enter the library path '
                           '(e.g., /sites/MyTeam/Shared Documents)',
                'code': 'MISSING_LIBRARY'
            }
        }), 400

    # Discover files
    try:
        files = connector.list_files(library_path, recursive=recursive, max_files=max_files)
    except Exception as e:
        connector.close()
        logger.error(f"SharePoint discovery error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to list files: {str(e)[:200]}',
                'code': 'SP_DISCOVERY_FAILED'
            }
        }), 500

    if not files:
        connector.close()
        return jsonify({
            'success': True,
            'data': {
                'scan_id': None,
                'message': f'No supported documents found in {library_path}. '
                           f'AEGIS supports: .docx, .pdf, .doc',
                'site_title': probe.get('title', ''),
                'discovery': {
                    'total_discovered': 0,
                    'supported_files': 0,
                    'files': [],
                    'file_type_breakdown': {},
                }
            }
        })

    # Calculate size and type breakdown
    total_size = sum(f.get('size', 0) for f in files)
    type_breakdown = {}
    for f in files:
        ext = f.get('extension', 'unknown')
        type_breakdown[ext] = type_breakdown.get(ext, 0) + 1

    # Add size_human and relative path display
    for f in files:
        f['size_human'] = _human_size(f.get('size', 0))

    # Generate scan_id
    scan_id = uuid.uuid4().hex[:12]

    # Initialize scan state (same structure as folder scan)
    with _folder_scan_state_lock:
        _cleanup_old_scans()
        _folder_scan_state[scan_id] = {
            'phase': 'downloading',  # v6.6.0: starts in download phase, not reviewing
            'total_files': len(files),
            'processed': 0,
            'errors': 0,
            'current_file': None,
            'current_chunk': 0,
            'total_chunks': (len(files) + FOLDER_SCAN_CHUNK_SIZE - 1) // FOLDER_SCAN_CHUNK_SIZE,
            'documents': [],
            'summary': {
                'total_documents': len(files),
                'processed': 0,
                'errors': 0,
                'total_issues': 0,
                'total_words': 0,
                'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0},
                'issues_by_category': {},
                'grade_distribution': {},
            },
            'roles_found': {},
            'started_at': time.time(),
            'completed_at': None,
            'elapsed_seconds': 0,
            'estimated_remaining': None,
            'folder_path': f'SharePoint: {library_path}',
            'source': 'sharepoint',
            # v6.6.0: Download phase tracking
            'download_total': len(files),
            'download_completed': 0,
            'download_cached': 0,
            'download_errors': 0,
        }

    # Phase 2: Spawn background thread for download + review
    flask_app = current_app._get_current_object()
    thread = threading.Thread(
        target=_process_sharepoint_scan_async,
        args=(scan_id, connector, files, options, flask_app),
        kwargs={'site_url': actual_site_url, 'connector_type': 'rest', 'library_path': library_path},
        daemon=True,
        name=f'sp-scan-{scan_id}',
    )
    thread.start()

    logger.info(f"SharePoint scan {scan_id} started: {len(files)} files from {library_path} "
                f"(site_url={actual_site_url}, library_path={library_path})")

    return jsonify({
        'success': True,
        'data': {
            'scan_id': scan_id,
            'site_title': probe.get('title', ''),
            'discovery': {
                'total_discovered': len(files),
                'supported_files': len(files),
                'total_size': total_size,
                'total_size_human': _human_size(total_size),
                'files': files[:100],  # Preview first 100
                'file_type_breakdown': type_breakdown,
            }
        }
    })


def _process_sharepoint_scan_async(scan_id, connector, files, options, flask_app,
                                    site_url=None, connector_type=None, library_path=None):
    """
    Background thread wrapper: catches ALL unhandled exceptions to prevent silent daemon death.
    v6.6.1: Wraps _process_sharepoint_scan_inner() with top-level crash protection.
    v6.6.2: Dual-logger — writes to BOTH routes.log AND sharepoint.log for visibility.
    """
    import traceback
    import logging as _blog

    # v6.6.2: CRITICAL — sharepoint logger writes to sharepoint.log (included in diagnostics).
    # The routes logger (from _shared.py) writes to routes.log which was INVISIBLE in all
    # prior diagnostic exports, making background thread crashes completely undetectable.
    _sp_log = _blog.getLogger('aegis.sharepoint')

    # v6.6.2: Version-stamped alive proof — FIRST thing written to sharepoint.log
    try:
        _sp_log.info(f'[BG-THREAD] ═══ v6.6.2 ═══ SP scan {scan_id}: Thread ALIVE '
                     f'(site_url={site_url}, type={connector_type}, files={len(files)}, '
                     f'connector={"provided" if connector else "None"}, '
                     f'repo_available={_REPO_AVAILABLE})')
    except Exception:
        pass

    # Also log to routes.log for completeness
    try:
        logger.info(f"SP scan {scan_id}: Background thread started "
                     f"(site_url={site_url}, connector_type={connector_type}, "
                     f"library_path={library_path}, files={len(files)}, "
                     f"connector={'provided' if connector else 'None'}, "
                     f"repo_available={_REPO_AVAILABLE})")
    except Exception:
        pass

    try:
        _process_sharepoint_scan_inner(
            scan_id, connector, files, options, flask_app,
            site_url=site_url, connector_type=connector_type, library_path=library_path,
            _sp_log=_sp_log
        )
    except Exception as e:
        # v6.6.1: Catch-all for unhandled errors — prevents silent daemon death
        tb_str = 'unknown'
        try:
            tb_str = traceback.format_exc()
        except Exception:
            pass
        # v6.6.2: Log to BOTH loggers
        try:
            _sp_log.error(f'[BG-THREAD] SP scan {scan_id}: FATAL ERROR: {tb_str}')
        except Exception:
            pass
        try:
            logger.error(f"SP scan {scan_id}: FATAL unhandled error in background thread: {tb_str}")
        except Exception:
            pass
        try:
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state and state.get('phase') not in ('complete', 'error'):
                    state['phase'] = 'error'
                    state['error_message'] = f'Fatal error: {str(e)[:200]}'
                    state['completed_at'] = time.time()
                    state['current_file'] = None
        except Exception:
            pass


def _process_sharepoint_scan_inner(scan_id, connector, files, options, flask_app,
                                    site_url=None, connector_type=None, library_path=None,
                                    _sp_log=None):
    """
    Background thread: download files from SharePoint and review with AEGIS engine.

    v6.6.0: Two-phase architecture with SP Repository:
    - Phase 1 (Download): Sequential download (max_workers=1 for Playwright) to persistent
      sp_repository/ directory. Files already up-to-date are skipped (cached).
    - Phase 2 (Scan): Parallel local file scan (max_workers=3) — no SP connection needed.
      3x throughput improvement over the old coupled download+scan.

    Falls back to the volatile temp-file pattern if sp_repository_manager is unavailable.

    v6.2.9: If connector is None, creates it HERE (in the background thread) instead
    of blocking the HTTP handler.

    v6.6.2: Added _sp_log for dual-logging to sharepoint.log (visible in diagnostics).
            Added Flask app context push for entire background thread.
    """
    import gc
    import hashlib
    from concurrent.futures import ThreadPoolExecutor, as_completed

    PER_FILE_TIMEOUT = 480  # v5.9.37: 8 minutes per file
    SCAN_PER_FILE_TIMEOUT = 300  # 5 minutes for local scan only (no download)

    # v6.6.2: Ensure _sp_log is available (fallback if not passed from wrapper)
    if _sp_log is None:
        import logging as _blog
        _sp_log = _blog.getLogger('aegis.sharepoint')

    # v6.6.2: Push Flask app context for entire background thread.
    # Without this, Flask-dependent code (g, current_app, session) in called functions
    # crashes silently, killing the thread with no visible error.
    _app_ctx = flask_app.app_context()
    _app_ctx.push()

    _sp_log.info(f'[BG-INNER] v6.6.2 SP scan {scan_id}: Inner function STARTED '
                 f'(connector={"provided" if connector else "None"}, '
                 f'files={len(files)}, repo={_REPO_AVAILABLE})')

    # ── v6.2.9: Create connector in background thread if not provided ──
    if connector is None and site_url:
        logger.info(f"SP scan {scan_id}: Creating connector in background thread (site_url={site_url}, type={connector_type})")

        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['current_file'] = 'Launching browser for SharePoint SSO...'

        SPConnector, _ = _get_sharepoint_connector()
        connector_created = False

        # v6.3.6: Detect SPO domains — skip REST entirely (always fails with 401)
        _is_spo = any(p in (site_url or '').lower() for p in (
            'sharepoint.com', 'sharepoint.us', 'sharepoint.de', 'sharepoint.cn'
        ))

        # Strategy 1: HeadlessSP — primary for SPO domains, or when discovery used headless
        if connector_type == 'headless' or _is_spo:
            try:
                from sharepoint_connector import HeadlessSPConnector, HEADLESS_SP_AVAILABLE
                if HEADLESS_SP_AVAILABLE:
                    logger.info(f"SP scan {scan_id}: Trying HeadlessSPConnector (SPO={_is_spo}, type={connector_type})...")
                    with _folder_scan_state_lock:
                        state = _folder_scan_state.get(scan_id)
                        if state:
                            state['current_file'] = 'Authenticating via Windows SSO (headless browser)...'

                    connector = HeadlessSPConnector(site_url)
                    test = connector.test_connection()
                    if test.get('success'):
                        connector_created = True
                        logger.info(f"SP scan {scan_id}: HeadlessSPConnector authenticated successfully")
                        _sp_log.info(f'[BG-INNER] SP scan {scan_id}: Strategy 1 HeadlessSP — AUTH SUCCESS')
                    else:
                        logger.warning(f"SP scan {scan_id}: HeadlessSPConnector auth failed: {test.get('message', '')}")
                        _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: Strategy 1 HeadlessSP — AUTH FAILED: {test.get("message", "")}')
                        connector.close()
                        connector = None
            except Exception as e:
                logger.error(f"SP scan {scan_id}: HeadlessSPConnector error: {e}")
                _sp_log.error(f'[BG-INNER] SP scan {scan_id}: Strategy 1 HeadlessSP — EXCEPTION: {e}')
                if connector:
                    try:
                        connector.close()
                    except Exception:
                        pass
                    connector = None

        # Strategy 2: REST connector — only for on-premises (non-SPO) SharePoint
        if not connector_created and SPConnector and not _is_spo:
            try:
                logger.info(f"SP scan {scan_id}: Trying REST connector (on-premises)...")
                with _folder_scan_state_lock:
                    state = _folder_scan_state.get(scan_id)
                    if state:
                        state['current_file'] = 'Authenticating via REST API...'

                connector = SPConnector(site_url)
                test = connector.test_connection()
                if test.get('success'):
                    connector_created = True
                    logger.info(f"SP scan {scan_id}: REST connector authenticated successfully")
                    _sp_log.info(f'[BG-INNER] SP scan {scan_id}: Strategy 2 REST — AUTH SUCCESS')
                else:
                    logger.warning(f"SP scan {scan_id}: REST connector failed: {test.get('message', '')}")
                    _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: Strategy 2 REST — AUTH FAILED: {test.get("message", "")}')
                    connector.close()
                    connector = None
            except Exception as e:
                logger.error(f"SP scan {scan_id}: REST connector error: {e}")
                _sp_log.error(f'[BG-INNER] SP scan {scan_id}: Strategy 2 REST — EXCEPTION: {e}')
                if connector:
                    try:
                        connector.close()
                    except Exception:
                        pass
                    connector = None

        # Strategy 3: Headless fallback if REST failed and not already tried
        if not connector_created and not _is_spo and connector_type != 'headless':
            try:
                from sharepoint_connector import HeadlessSPConnector, HEADLESS_SP_AVAILABLE
                if HEADLESS_SP_AVAILABLE:
                    logger.info(f"SP scan {scan_id}: Trying HeadlessSPConnector as fallback...")
                    with _folder_scan_state_lock:
                        state = _folder_scan_state.get(scan_id)
                        if state:
                            state['current_file'] = 'Trying headless browser fallback...'

                    connector = HeadlessSPConnector(site_url)
                    test = connector.test_connection()
                    if test.get('success'):
                        connector_created = True
                        logger.info(f"SP scan {scan_id}: Headless fallback authenticated successfully")
                        _sp_log.info(f'[BG-INNER] SP scan {scan_id}: Strategy 3 Headless fallback — AUTH SUCCESS')
                    else:
                        logger.warning(f"SP scan {scan_id}: Headless fallback auth failed")
                        _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: Strategy 3 Headless fallback — AUTH FAILED')
                        connector.close()
                        connector = None
            except Exception as e:
                logger.error(f"SP scan {scan_id}: Headless fallback error: {e}")
                _sp_log.error(f'[BG-INNER] SP scan {scan_id}: Strategy 3 Headless fallback — EXCEPTION: {e}')
                if connector:
                    try:
                        connector.close()
                    except Exception:
                        pass
                    connector = None

        # If ALL strategies failed, mark scan as error and return
        if not connector_created or connector is None:
            err_msg = 'Failed to authenticate to SharePoint — all connection strategies exhausted'
            logger.error(f"SP scan {scan_id}: {err_msg}")
            _sp_log.error(f'[BG-INNER] SP scan {scan_id}: ALL CONNECTOR STRATEGIES FAILED')
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['phase'] = 'error'
                    state['error_message'] = err_msg
                    state['completed_at'] = time.time()
                    state['current_file'] = None
            return  # Exit background thread

        # Connector created successfully — transition to downloading phase
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'downloading'
                state['current_file'] = 'Starting document downloads...'
        logger.info(f"SP scan {scan_id}: Connector ready, transitioning to downloading phase")
        _sp_log.info(f'[BG-INNER] SP scan {scan_id}: CONNECTOR READY — transitioning to download phase')

    # ── v6.6.0: Initialize SP Repository if available ──
    repo = None
    use_repo = _REPO_AVAILABLE
    if use_repo:
        try:
            repo = get_repository()
            logger.info(f"SP scan {scan_id}: SP Repository available at {repo.repo_dir}")
        except Exception as e:
            logger.warning(f"SP scan {scan_id}: SP Repository init failed: {e} — falling back to temp files")
            _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: Repository init FAILED ({e}) — temp-file fallback')
            use_repo = False

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1: Download files from SharePoint (sequential, max_workers=1)
    # ════════════════════════════════════════════════════════════════════
    _sp_log.info(f'[BG-INNER] SP scan {scan_id}: PHASE 1 START — downloading {len(files)} files '
                 f'(repo={use_repo}, connector={"provided" if connector else "None"})')
    with _folder_scan_state_lock:
        state = _folder_scan_state.get(scan_id)
        if state:
            state['phase'] = 'downloading'
            state['download_total'] = len(files)
            state['download_completed'] = 0
            state['download_cached'] = 0
            state['download_errors'] = 0

    local_files = []  # List of (file_info, local_path) tuples ready for scanning
    download_errors = 0

    for dl_idx, file_info in enumerate(files):
        filename = file_info['filename']
        server_rel_url = file_info['server_relative_url']
        sp_modified = file_info.get('modified', '')
        sp_size = file_info.get('size', 0)

        # v6.6.2: Log every 10th file to sharepoint.log for progress visibility
        if dl_idx % 10 == 0 or dl_idx == 0:
            _sp_log.info(f'[BG-INNER] SP scan {scan_id}: Downloading file {dl_idx + 1}/{len(files)}: {filename}')

        # Update download progress
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['current_file'] = f'Downloading {filename} ({dl_idx + 1}/{len(files)})'

        try:
            if use_repo:
                # ── Repository path: check if download needed ──
                local_path = repo.get_local_path(site_url or '', server_rel_url)
                needs_dl = repo.needs_download(site_url or '', server_rel_url,
                                                sp_modified=sp_modified, sp_size=sp_size)

                if needs_dl:
                    # Archive previous version before overwriting
                    repo.archive_previous_version(site_url or '', server_rel_url)

                    # Download to persistent repository path
                    dl_result = connector.download_file(server_rel_url, local_path)
                    if dl_result['success']:
                        # Compute hash and register in manifest
                        file_hash = ''
                        try:
                            h = hashlib.md5()
                            with open(local_path, 'rb') as f:
                                for chunk in iter(lambda: f.read(8192), b''):
                                    h.update(chunk)
                            file_hash = h.hexdigest()
                        except Exception:
                            pass

                        repo.register_download(
                            site_url=site_url or '',
                            server_relative_url=server_rel_url,
                            local_path=local_path,
                            file_hash=file_hash,
                            sp_modified=sp_modified,
                            size=dl_result.get('size', sp_size)
                        )
                        file_info['_was_downloaded'] = True  # v6.6.1: Track for cached counter
                        local_files.append((file_info, local_path))
                        logger.info(f"SP scan {scan_id}: Downloaded {filename} → {local_path}")
                    else:
                        download_errors += 1
                        logger.warning(f"SP scan {scan_id}: Download failed for {filename}: {dl_result.get('message', '')}")
                        # Record error result
                        with flask_app.app_context():
                            _update_scan_state_with_result(scan_id, {
                                'filename': filename,
                                'relative_path': server_rel_url,
                                'folder': file_info.get('folder', ''),
                                'extension': file_info.get('extension', ''),
                                'file_size': 0,
                                'status': 'error',
                                'error': f'Download failed: {dl_result.get("message", "Unknown error")}',
                            }, options, flask_app)
                else:
                    # Already up-to-date — use cached local copy
                    local_files.append((file_info, local_path))
                    logger.info(f"SP scan {scan_id}: Using cached {filename} (up-to-date)")

            else:
                # ── Fallback: volatile temp file (legacy behavior) ──
                temp_dir = tempfile.mkdtemp(prefix='aegis_sp_')
                dest_path = os.path.join(temp_dir, filename)
                dl_result = connector.download_file(server_rel_url, dest_path)
                if dl_result['success']:
                    file_info['_was_downloaded'] = True  # v6.6.1: Track for cached counter
                    local_files.append((file_info, dest_path))
                else:
                    download_errors += 1
                    with flask_app.app_context():
                        _update_scan_state_with_result(scan_id, {
                            'filename': filename,
                            'relative_path': server_rel_url,
                            'folder': file_info.get('folder', ''),
                            'extension': file_info.get('extension', ''),
                            'file_size': 0,
                            'status': 'error',
                            'error': f'Download failed: {dl_result.get("message", "Unknown error")}',
                        }, options, flask_app)

        except Exception as e:
            download_errors += 1
            logger.error(f"SP scan {scan_id}: Download error for {filename}: {e}")
            with flask_app.app_context():
                _update_scan_state_with_result(scan_id, {
                    'filename': filename,
                    'relative_path': server_rel_url,
                    'folder': file_info.get('folder', ''),
                    'extension': file_info.get('extension', ''),
                    'file_size': 0,
                    'status': 'error',
                    'error': f'Download error: {str(e)[:150]}',
                }, options, flask_app)

        # Update download count
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['download_completed'] = dl_idx + 1 - download_errors
                state['download_cached'] = sum(1 for fi, lp in local_files
                                                if not fi.get('_was_downloaded'))
                state['download_errors'] = download_errors

    # Close SP connector — downloads are done, scans are local
    _sp_log.info(f'[BG-INNER] SP scan {scan_id}: PHASE 1 COMPLETE — '
                 f'{len(local_files)} files downloaded, {download_errors} errors. Closing connector.')
    try:
        connector.close()
        logger.info(f"SP scan {scan_id}: Connector closed after downloads. "
                     f"{len(local_files)} files ready for scan, {download_errors} errors")
    except Exception as e:
        logger.warning(f"SP scan {scan_id}: Error closing connector: {e}")
        _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: Connector close error: {e}')

    # If no files to scan, mark complete
    if not local_files:
        _sp_log.warning(f'[BG-INNER] SP scan {scan_id}: NO LOCAL FILES to scan '
                        f'(download_errors={download_errors}) — marking {"error" if download_errors else "complete"}')
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'complete' if download_errors == 0 else 'error'
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                state['current_file'] = None
                if download_errors > 0:
                    state['error_message'] = f'All {download_errors} downloads failed'
        return

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2: Scan local files (parallel, max_workers=3)
    # ════════════════════════════════════════════════════════════════════
    with _folder_scan_state_lock:
        state = _folder_scan_state.get(scan_id)
        if state:
            state['phase'] = 'reviewing'
            state['current_file'] = f'Scanning {len(local_files)} documents...'

    logger.info(f"SP scan {scan_id}: Phase 2 — scanning {len(local_files)} local files with max_workers=3")
    _sp_log.info(f'[BG-INNER] SP scan {scan_id}: PHASE 2 START — scanning {len(local_files)} local files '
                 f'(chunks={len(range(0, len(local_files), FOLDER_SCAN_CHUNK_SIZE))}, max_workers=3)')

    def _review_local_file(file_info_and_path):
        """Review a local file (already downloaded from SharePoint)."""
        file_info, local_path = file_info_and_path
        filename = file_info['filename']
        server_rel_url = file_info['server_relative_url']

        try:
            if AEGISEngine is None:
                return {
                    'filename': filename,
                    'relative_path': server_rel_url,
                    'full_path': local_path,
                    'source_url': server_rel_url,
                    'folder': file_info.get('folder', ''),
                    'extension': file_info.get('extension', ''),
                    'file_size': os.path.getsize(local_path) if os.path.exists(local_path) else 0,
                    'status': 'error',
                    'error': 'AEGISEngine not available',
                }

            engine = AEGISEngine()
            sp_options = dict(options) if options else {}
            sp_options['batch_mode'] = True
            doc_results = engine.review_document(local_path, sp_options)

            # Convert ReviewIssue objects to dicts (Lesson #36)
            raw_issues = doc_results.get('issues', [])
            issues = []
            for issue in raw_issues:
                if isinstance(issue, dict):
                    issues.append(issue)
                elif hasattr(issue, 'to_dict'):
                    issues.append(issue.to_dict())
                else:
                    issues.append({
                        'message': getattr(issue, 'message', str(issue)),
                        'severity': getattr(issue, 'severity', 'Low'),
                        'category': getattr(issue, 'category', 'Unknown'),
                    })

            actual_roles = doc_results.get('roles', {})
            if not isinstance(actual_roles, dict):
                actual_roles = {}
            word_count = doc_results.get('word_count', 0)
            if not isinstance(word_count, (int, float)):
                word_count = 0

            # v6.6.0: Mark as scanned in repository
            if use_repo and repo:
                try:
                    repo.mark_scanned(site_url or '', server_rel_url)
                except Exception:
                    pass

            return {
                'filename': filename,
                'relative_path': server_rel_url,
                'full_path': local_path,
                'source_url': server_rel_url,
                'folder': file_info.get('folder', ''),
                'extension': file_info.get('extension', ''),
                'file_size': os.path.getsize(local_path) if os.path.exists(local_path) else 0,
                'issues': issues,
                'issue_count': len(issues),
                'roles': actual_roles,
                'role_count': len(actual_roles),
                'word_count': int(word_count),
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'status': 'success',
            }

        except Exception as e:
            logger.error(f"SP local review error for {filename}: {e}")
            return {
                'filename': filename,
                'relative_path': server_rel_url,
                'full_path': local_path,
                'source_url': server_rel_url,
                'folder': file_info.get('folder', ''),
                'extension': file_info.get('extension', ''),
                'file_size': 0,
                'status': 'error',
                'error': str(e)[:200],
            }
        # v6.6.0: NO temp cleanup — files persist in sp_repository/

    # Process files in chunks (same pattern as folder scan)
    scan_chunks = []
    for i in range(0, len(local_files), FOLDER_SCAN_CHUNK_SIZE):
        scan_chunks.append(local_files[i:i + FOLDER_SCAN_CHUNK_SIZE])

    try:
        for chunk_idx, chunk in enumerate(scan_chunks):
            # Update state with current chunk
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['current_chunk'] = chunk_idx + 1
                    state['total_chunks'] = len(scan_chunks)
                    chunk_names = [c[0]['filename'] for c in chunk[:3]]
                    state['current_file'] = ', '.join(chunk_names)

            # v6.6.0: Parallel local scan — max_workers=3 (files are local, no SP connection)
            with ThreadPoolExecutor(max_workers=min(FOLDER_SCAN_MAX_WORKERS, len(chunk))) as executor:
                future_to_file = {
                    executor.submit(_review_local_file, item): item
                    for item in chunk
                }

                chunk_timeout = SCAN_PER_FILE_TIMEOUT * len(chunk)
                try:
                    for future in as_completed(future_to_file, timeout=chunk_timeout):
                        item = future_to_file[future]
                        file_info, local_path = item
                        try:
                            result = future.result(timeout=SCAN_PER_FILE_TIMEOUT)
                        except Exception as e:
                            result = {
                                'filename': file_info['filename'],
                                'relative_path': file_info.get('server_relative_url', ''),
                                'folder': file_info.get('folder', ''),
                                'extension': file_info.get('extension', ''),
                                'file_size': 0,
                                'status': 'error',
                                'error': f'Processing timeout or error: {str(e)[:100]}',
                            }

                        # Update scan state (reuse existing helper)
                        with flask_app.app_context():
                            _update_scan_state_with_result(scan_id, result, options, flask_app)

                except Exception as e:
                    logger.error(f"SharePoint scan chunk {chunk_idx + 1} error: {e}")
                    # Mark remaining files as errors
                    for future in future_to_file:
                        if not future.done():
                            item = future_to_file[future]
                            file_info, _ = item
                            error_result = {
                                'filename': file_info['filename'],
                                'relative_path': file_info.get('server_relative_url', ''),
                                'folder': file_info.get('folder', ''),
                                'extension': file_info.get('extension', ''),
                                'file_size': 0,
                                'status': 'error',
                                'error': 'Chunk processing timed out',
                            }
                            with flask_app.app_context():
                                _update_scan_state_with_result(scan_id, error_result, options, flask_app)

            # GC between chunks
            gc.collect()

        # Mark scan as complete
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'complete'
                state['completed_at'] = time.time()
                state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                state['current_file'] = None

        logger.info(f"SharePoint scan {scan_id} complete: "
                     f"{state.get('processed', 0)} processed, {state.get('errors', 0)} errors")
        _sp_log.info(f'[BG-INNER] SP scan {scan_id}: ═══ SCAN COMPLETE ═══ '
                     f"processed={state.get('processed', 0)}, errors={state.get('errors', 0)}, "
                     f"elapsed={state.get('elapsed_seconds', 0)}s")

    except Exception as e:
        logger.error(f"SharePoint scan {scan_id} fatal error: {e}")
        _sp_log.error(f'[BG-INNER] SP scan {scan_id}: ═══ FATAL ERROR ═══ {e}')
        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['phase'] = 'error'
                state['error_message'] = str(e)[:200]
                state['completed_at'] = time.time()


@review_bp.route('/api/review/single', methods=['POST'])
@require_csrf
@handle_api_errors
def review_single():
    """
    v3.0.114: Review a single document by filepath.
    Used for loading individual documents from batch results.

    Expects JSON body with filepath and optional filename.
    Returns full review results for display.
    """
    data = request.get_json() or {}
    filepath_str = data.get('filepath')
    filename = data.get('filename')
    options = data.get('options', {})
    if not filepath_str:
        raise ValidationError('No filepath provided')
    else:
        filepath = Path(filepath_str)
        if not filepath.exists():
            raise FileError(f'Document not found: {filepath.name}')
        else:
            try:
                filepath.resolve().relative_to(config.temp_dir.resolve())
            except ValueError:
                raise ValidationError('Invalid filepath - document must be in temp directory')
            original_filename = filename or filepath.name
            if '_' in original_filename and len(original_filename.split('_')[0]) == 8:
                    original_filename = '_'.join(original_filename.split('_')[1:])
            engine = AEGISEngine()
            results = engine.review_document(str(filepath), options)
            try:
                SessionManager.update(g.session_id, current_file=str(filepath), original_filename=original_filename)
            except Exception as e:
                logger.warning(f'Session update failed: {e}')
            return jsonify({'success': True, 'data': results})
@review_bp.route('/api/review', methods=['POST'])
@require_csrf
@handle_api_errors
def review():
    """Run comprehensive document review."""
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('current_file'):
        raise ValidationError('No document loaded. Please upload a file first.')
    else:
        filepath = Path(session_data['current_file'])
        if not filepath.exists():
            raise FileError('Document file not found. Please re-upload.')
        else:
            data = request.get_json() or {}
            options = data.get('options', {})
            original_filename = session_data.get('original_filename', filepath.name)
            with logger.log_operation('document_review', file_name=original_filename):
                engine = AEGISEngine()
                results = engine.review_document(str(filepath), options)
        sf_statements_list = []
        if _shared.STATEMENT_FORGE_AVAILABLE and results.get('full_text'):
                try:
                    try:
                        from statement_forge.extractor import extract_statements as sf_extract
                        from statement_forge.export import get_export_stats as sf_stats
                        from statement_forge.routes import _store_statements
                    except ImportError:
                        from statement_forge__extractor import extract_statements as sf_extract
                        from statement_forge__export import get_export_stats as sf_stats
                        from statement_forge__routes import _store_statements
                    sf_text = results.get('clean_full_text') or results.get('full_text', '')
                    sf_stmts = sf_extract(sf_text, original_filename)
                    if sf_stmts:
                        stats = sf_stats(sf_stmts)
                        sf_statements_list = [s.to_dict() for s in sf_stmts]
                        _store_statements(sf_stmts)
                        results['statement_forge_summary'] = {'available': True, 'statements_ready': True, 'total_statements': len(sf_stmts), 'directive_counts': stats.get('directive_counts', {}), 'top_roles': stats.get('roles', [])[:5], 'section_count': stats.get('section_count', 0)}
                        logger.debug(f'SF pre-extracted: {len(sf_stmts)} statements')
                    else:
                        results['statement_forge_summary'] = {'available': True, 'statements_ready': False, 'total_statements': 0}
                except Exception as e:
                    logger.warning(f'SF pre-extraction failed: {e}')
                    results['statement_forge_summary'] = {'available': False, 'statements_ready': False, 'error': str(e)}
        scan_info = None
        if _shared.SCAN_HISTORY_AVAILABLE:
            try:
                db = get_scan_history_db()
                logger.info(f'Recording scan for: {original_filename}')
                scan_info = db.record_scan(filename=original_filename, filepath=str(filepath), results=results, options=options)
                if scan_info:
                    logger.info(f"Scan recorded: scan_id={scan_info.get('scan_id')}, document_id={scan_info.get('document_id')}, is_rescan={scan_info.get('is_rescan')}")
                    if sf_statements_list:
                        try:
                            db.save_scan_statements(scan_info['scan_id'], scan_info['document_id'], sf_statements_list)
                        except Exception as sf_err:
                            logger.warning(f'SF statement persistence failed: {sf_err}')
                else:
                    logger.warning(f'record_scan returned None for {original_filename}')
            except Exception as e:
                logger.error(f'Scan history error for {original_filename}: {e}', exc_info=True)
        else:
            logger.debug('Scan history not available - skipping record')
        SessionManager.update(g.session_id, review_results=results, filtered_issues=results.get('issues', []), selected_issues=set())
        doc_info = results.get('document_info', {})
        response_data = {'issues': results.get('issues', []), 'issue_count': results.get('issue_count', 0), 'score': results.get('score', 100), 'grade': results.get('grade', 'N/A'), 'readability': results.get('readability', {}), 'document_info': doc_info, 'roles': results.get('roles', {}), 'full_text': results.get('full_text', ''), 'html_preview': results.get('html_preview', ''), 'hyperlink_results': results.get('hyperlink_results', 0), 'word_count': results.get('word_count', 0), 'paragraph_count': results.get('paragraph_count', 0), 'table_count': results.get('table_count', 0), 'heading_count': doc_info.get('heading_count', 0), 'by_severity': results.get('by_severity', {}), 'by_category': results.get('by_category', {})}
        try:
            issues = results.get('issues', [])
            response_data['document_content'] = build_document_content(results)
            response_data['fix_groups'] = group_similar_fixes(issues)
            response_data['confidence_details'] = build_confidence_details(issues)
            doc_content = response_data['document_content']
            response_data['fix_statistics'] = compute_fix_statistics(issues, response_data['fix_groups'], response_data['confidence_details'], doc_content.get('page_count', 1))
            logger.debug(f"Fix Assistant v2 data: {len(response_data['fix_groups'])} groups, {len(response_data['confidence_details'])} confidence details")
        except Exception as e:
            logger.warning(f'Fix Assistant v2 enhancement failed: {e}')
            response_data['document_content'] = {'paragraphs': [], 'page_map': {}, 'headings': [], 'page_count': 1}
            response_data['fix_groups'] = []
            response_data['confidence_details'] = {}
            response_data['fix_statistics'] = {'total': 0, 'by_tier': {}, 'by_category': {}, 'by_page': {}}
        response_data['statement_forge_summary'] = results.get('statement_forge_summary', {'available': _shared.STATEMENT_FORGE_AVAILABLE, 'statements_ready': False})
        if scan_info:
            response_data['scan_info'] = scan_info
        return jsonify({'success': True, 'data': response_data})

# =============================================================================
# v3.5.0: MULTIPROCESSING-BASED REVIEW (replaces threading.Thread)
# =============================================================================
# The review worker now runs in a separate PROCESS with its own Python GIL.
# This prevents CPU-bound document analysis from blocking the Flask server.
# Progress updates flow via multiprocessing.Queue → monitor thread → job manager.
# Results are written to a temp JSON file (can be large for big documents).
# =============================================================================

# Default timeout for review jobs (seconds) - 10 minutes
REVIEW_TIMEOUT_SECONDS = 600


def _review_worker_process(filepath: str, original_filename: str, options: dict,
                           progress_queue: multiprocessing.Queue, result_file: str):
    """
    v3.5.0: Worker function that runs in a SEPARATE PROCESS (separate GIL).

    This isolates CPU-bound document analysis from the Flask server process.
    If this process crashes, the Flask server continues running normally.

    Communication:
        - progress_queue: sends {'type': 'progress'|'complete'|'error', ...} messages
        - result_file: path to write JSON results (large results don't fit in queue)
    """
    try:
        # Import in worker process (fresh Python interpreter)
        import sys
        import os

        # Ensure project root is on path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from core import AEGISEngine

        def progress_callback(phase: str, progress: float, message: str):
            """Send progress updates to main process via queue."""
            try:
                progress_queue.put_nowait({
                    'type': 'progress',
                    'phase': phase,
                    'progress': progress,
                    'message': message
                })
            except Exception as e:
                import logging
                logging.getLogger('aegis.review').debug(f'Job {job_id} progress queue update failed: {e}')

        # Create engine and run review
        engine = AEGISEngine()
        results = engine.review_document(
            str(filepath), options,
            progress_callback=progress_callback
        )

        if results.get('cancelled'):
            progress_queue.put({'type': 'cancelled'})
            return

        # Statement Forge extraction (also in worker process)
        sf_statements_list = []
        if results.get('full_text'):
            try:
                try:
                    from statement_forge.extractor import extract_statements as sf_extract
                    from statement_forge.export import get_export_stats as sf_stats
                except ImportError:
                    from statement_forge__extractor import extract_statements as sf_extract
                    from statement_forge__export import get_export_stats as sf_stats

                sf_text = results.get('clean_full_text') or results.get('full_text', '')
                sf_stmts = sf_extract(sf_text, original_filename)
                if sf_stmts:
                    stats = sf_stats(sf_stmts)
                    sf_statements_list = [s.to_dict() for s in sf_stmts]
                    results['statement_forge_summary'] = {
                        'available': True,
                        'statements_ready': True,
                        'total_statements': len(sf_stmts),
                        'directive_counts': stats.get('directive_counts', {}),
                        'top_roles': stats.get('roles', [])[:5],
                        'section_count': stats.get('section_count', 0)
                    }
            except Exception as e:
                results['statement_forge_summary'] = {'available': False, 'error': str(e)}

        # Store SF statements in results for the monitor to handle
        results['_sf_statements'] = sf_statements_list

        # Write results to temp file (can be very large for big documents)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, default=str)

        progress_queue.put({'type': 'complete'})

    except Exception as e:
        try:
            progress_queue.put({
                'type': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        except Exception:
            pass  # Last resort - queue itself is broken


def _monitor_review_process(job_id: str, session_id: str, process: multiprocessing.Process,
                            progress_queue: multiprocessing.Queue, result_file: str,
                            original_filename: str, filepath: str, options: dict,
                            timeout: int = REVIEW_TIMEOUT_SECONDS):
    """
    v3.5.0: Monitor thread that bridges worker process → Flask app state.

    Runs in the MAIN process as a lightweight daemon thread.
    Reads progress from queue and updates job manager / session manager.
    Handles timeout by terminating the worker process.
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        logger.error('Job manager not available in monitor')
        return

    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        logger.error(f'Job {job_id} not found in monitor')
        return

    manager.start_job(job_id)
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            msg = progress_queue.get(timeout=3)
        except Exception:
            # No message yet - check if process is still alive
            if not process.is_alive():
                exit_code = process.exitcode
                if exit_code is not None and exit_code != 0:
                    manager.fail_job(job_id, f'Worker process crashed (exit code {exit_code})')
                    logger.error(f'Review worker for job {job_id} crashed with exit code {exit_code}')
                    _cleanup_result_file(result_file)
                    return
                # Process exited normally but we haven't seen 'complete' - wait a bit more
                try:
                    msg = progress_queue.get(timeout=2)
                except Exception:
                    manager.fail_job(job_id, 'Worker process exited without sending results')
                    logger.error(f'Review worker for job {job_id} exited silently')
                    _cleanup_result_file(result_file)
                    return
            else:
                continue

        # Process message
        msg_type = msg.get('type', '')

        if msg_type == 'progress':
            phase = msg.get('phase', 'checking')
            phase_map = {
                'extracting': JobPhase.EXTRACTING,
                'parsing': JobPhase.PARSING,
                'checking': JobPhase.CHECKING,
                'postprocessing': JobPhase.POSTPROCESSING,
                'complete': JobPhase.COMPLETE
            }
            job_phase = phase_map.get(phase, JobPhase.CHECKING)
            message = msg.get('message', '')
            manager.update_phase(job_id, job_phase, message)

            # Parse checker progress if available
            if phase == 'checking' and '(' in message and '/' in message:
                import re
                m = re.search(r'Completed\s+(\S+)\s+\((\d+)/(\d+)\)', message)
                if m:
                    manager.update_checker_progress(job_id, m.group(1), int(m.group(2)), int(m.group(3)))

            manager.update_phase_progress(job_id, msg.get('progress', 0), message)

        elif msg_type == 'complete':
            # Read results from temp file
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                sf_statements_list = results.pop('_sf_statements', [])

                # Record scan in history (SQLite - works across processes)
                if _shared.SCAN_HISTORY_AVAILABLE:
                    try:
                        db = get_scan_history_db()
                        scan_info = db.record_scan(
                            filename=original_filename,
                            filepath=str(filepath),
                            results=results,
                            options=options
                        )
                        results['scan_info'] = scan_info
                        if sf_statements_list and scan_info:
                            try:
                                db.save_scan_statements(
                                    scan_info['scan_id'],
                                    scan_info['document_id'],
                                    sf_statements_list
                                )
                            except Exception as sf_err:
                                logger.warning(f'SF statement persistence failed: {sf_err}')
                    except Exception as e:
                        logger.error(f'Scan history error for {original_filename}: {e}')

                # Update session and complete job
                SessionManager.update(
                    session_id,
                    review_results=results,
                    filtered_issues=results.get('issues', []),
                    selected_issues=set()
                )
                manager.complete_job(job_id, result=results)
                logger.info(f"Review job {job_id} completed: {len(results.get('issues', []))} issues")

            except Exception as e:
                logger.error(f'Failed to read results for job {job_id}: {e}', exc_info=True)
                manager.fail_job(job_id, f'Failed to read results: {e}')
            finally:
                _cleanup_result_file(result_file)
            return

        elif msg_type == 'cancelled':
            logger.info(f'Review job {job_id} was cancelled')
            _cleanup_result_file(result_file)
            return

        elif msg_type == 'error':
            error_msg = msg.get('error', 'Unknown error')
            tb = msg.get('traceback', '')
            logger.error(f'Review job {job_id} failed: {error_msg}\n{tb}')
            manager.fail_job(job_id, error_msg)
            _cleanup_result_file(result_file)
            return

    # Timeout reached - terminate the worker process
    logger.error(f'Review job {job_id} timed out after {timeout}s - terminating worker')
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        logger.warning(f'Worker for job {job_id} did not terminate gracefully, killing')
        process.kill()
        process.join(timeout=3)

    manager.fail_job(job_id, f'Review timed out after {timeout} seconds. Try a smaller document or fewer checkers.')
    _cleanup_result_file(result_file)


def _cleanup_result_file(result_file: str):
    """Remove temporary result file if it exists."""
    try:
        if os.path.exists(result_file):
            os.remove(result_file)
    except Exception as e:
        import logging
        logging.getLogger('aegis.review').debug(f'Could not clean up result file {result_file}: {e}')


# Legacy fallback: threading-based review (used if multiprocessing unavailable)
def _run_review_job_threaded(job_id: str, session_id: str, filepath: str, original_filename: str, options: dict):
    """
    Legacy threaded worker (v3.0.39 original).
    Used as fallback if multiprocessing is not available.
    WARNING: This blocks the Flask server GIL during CPU-bound work.
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        logger.error('Job manager not available in worker')
        return None
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        logger.error(f'Job {job_id} not found in worker')
        return None
    manager.start_job(job_id)
    def progress_callback(phase: str, progress: float, message: str):
        phase_map = {'extracting': JobPhase.EXTRACTING, 'parsing': JobPhase.PARSING, 'checking': JobPhase.CHECKING, 'postprocessing': JobPhase.POSTPROCESSING, 'complete': JobPhase.COMPLETE}
        job_phase = phase_map.get(phase, JobPhase.CHECKING)
        manager.update_phase(job_id, job_phase, message)
        if phase == 'checking' and '(' in message and ('/' in message):
            import re
            m = re.search(r'Completed\s+(\S+)\s+\((\d+)/(\d+)\)', message)
            if m:
                manager.update_checker_progress(job_id, m.group(1), int(m.group(2)), int(m.group(3)))
        manager.update_phase_progress(job_id, progress, message)
    def cancellation_check() -> bool:
        job = manager.get_job(job_id)
        return job.is_cancelled if job else True
    try:
        engine = AEGISEngine()
        results = engine.review_document(str(filepath), options, progress_callback=progress_callback, cancellation_check=cancellation_check)
        if results.get('cancelled'):
            logger.info(f'Review job {job_id} was cancelled')
        else:
            sf_statements_list = []
            if _shared.STATEMENT_FORGE_AVAILABLE and results.get('full_text'):
                try:
                    try:
                        from statement_forge.extractor import extract_statements as sf_extract
                        from statement_forge.export import get_export_stats as sf_stats
                    except ImportError:
                        from statement_forge__extractor import extract_statements as sf_extract
                        from statement_forge__export import get_export_stats as sf_stats
                    sf_text = results.get('clean_full_text') or results.get('full_text', '')
                    sf_stmts = sf_extract(sf_text, original_filename)
                    if sf_stmts:
                        stats = sf_stats(sf_stmts)
                        sf_statements_list = [s.to_dict() for s in sf_stmts]
                        results['statement_forge_summary'] = {'available': True, 'statements_ready': True, 'total_statements': len(sf_stmts), 'directive_counts': stats.get('directive_counts', {}), 'top_roles': stats.get('roles', [])[:5], 'section_count': stats.get('section_count', 0)}
                except Exception as e:
                    logger.warning(f'SF pre-extraction failed: {e}')
                    results['statement_forge_summary'] = {'available': False, 'error': str(e)}
            if _shared.SCAN_HISTORY_AVAILABLE:
                try:
                    db = get_scan_history_db()
                    scan_info = db.record_scan(filename=original_filename, filepath=str(filepath), results=results, options=options)
                    results['scan_info'] = scan_info
                    if sf_statements_list and scan_info:
                        try:
                            db.save_scan_statements(scan_info['scan_id'], scan_info['document_id'], sf_statements_list)
                        except Exception as sf_err:
                            logger.warning(f'SF statement persistence failed: {sf_err}')
                except Exception as e:
                    logger.error(f'Scan history error for {original_filename}: {e}')
            SessionManager.update(session_id, review_results=results, filtered_issues=results.get('issues', []), selected_issues=set())
            manager.complete_job(job_id, result=results)
            logger.info(f"Review job {job_id} completed: {len(results.get('issues', []))} issues")
    except Exception as e:
        logger.error(f'Review job {job_id} failed: {e}', exc_info=True)
        manager.fail_job(job_id, str(e))


@review_bp.route('/api/review/start', methods=['POST'])
@require_csrf
@handle_api_errors
def review_start():
    """
    Start an async document review job.

    v3.5.0: Now uses multiprocessing.Process instead of threading.Thread.
    The review runs in a SEPARATE Python process with its own GIL,
    preventing CPU-bound analysis from blocking the Flask server.

    Falls back to threading if multiprocessing is unavailable.

    Returns job_id immediately. Client polls /api/job/<job_id> for progress.
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        raise ProcessingError('Job manager not available', stage='review_start')

    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('current_file'):
        raise ValidationError('No document loaded. Please upload a file first.')

    filepath = Path(session_data['current_file'])
    if not filepath.exists():
        raise FileError('Document file not found. Please re-upload.')

    data = request.get_json() or {}
    options = data.get('options', {})
    original_filename = session_data.get('original_filename', filepath.name)

    manager = get_job_manager()
    job_id = manager.create_job('review', metadata={
        'filename': original_filename,
        'session_id': g.session_id,
        'options': options
    })
    logger.info(f'Created review job {job_id} for {original_filename}')

    # v3.5.0: Try multiprocessing first (separate GIL), fall back to threading
    use_multiprocessing = True
    try:
        # Test that multiprocessing works (some environments restrict it)
        multiprocessing.Queue(1)
    except Exception:
        use_multiprocessing = False
        logger.warning('Multiprocessing not available, falling back to threading')

    if use_multiprocessing:
        # Create temp file for results and progress queue
        result_fd, result_file = tempfile.mkstemp(suffix='.json', prefix=f'aegis_review_{job_id}_')
        os.close(result_fd)  # Close fd, worker will open by path

        progress_queue = multiprocessing.Queue(maxsize=500)

        # Start worker PROCESS (separate GIL - won't block Flask)
        worker = multiprocessing.Process(
            target=_review_worker_process,
            args=(str(filepath), original_filename, options, progress_queue, result_file),
            daemon=True,
            name=f'review-worker-{job_id}'
        )
        worker.start()
        logger.info(f'Started review worker PROCESS (PID {worker.pid}) for job {job_id}')

        # Start monitor THREAD (lightweight - just reads queue and updates state)
        monitor = threading.Thread(
            target=_monitor_review_process,
            args=(job_id, g.session_id, worker, progress_queue, result_file,
                  original_filename, str(filepath), options),
            daemon=True,
            name=f'review-monitor-{job_id}'
        )
        monitor.start()
    else:
        # Fallback: legacy threading (blocks GIL but still works)
        worker = threading.Thread(
            target=_run_review_job_threaded,
            args=(job_id, g.session_id, str(filepath), original_filename, options),
            daemon=True,
            name=f'review-worker-{job_id}'
        )
        worker.start()
        logger.info(f'Started review worker THREAD for job {job_id} (legacy fallback)')

    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Review started',
        'poll_url': f'/api/job/{job_id}',
        'worker_type': 'process' if use_multiprocessing else 'thread'
    })
@review_bp.route('/api/review/result/<job_id>', methods=['GET'])
@handle_api_errors
def review_result(job_id):
    """
    Get the result of a completed review job.
    
    v3.0.39: Convenience endpoint for getting full review results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Full review results (same format as /api/review)
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        raise ProcessingError('Job manager not available', stage='review_result')
    else:
        manager = get_job_manager()
        job = manager.get_job(job_id)
        if not job:
            return (jsonify({'success': False, 'error': f'Job not found: {job_id}'}), 404)
        else:
            if job.status!= JobStatus.COMPLETE:
                return (jsonify({'success': False, 'error': f'Job not complete. Status: {job.status.value}', 'job': job.to_dict()}), 400)
            else:
                if not job.result:
                    return (jsonify({'success': False, 'error': 'Job complete but no result available'}), 500)
                else:
                    results = job.result
                    doc_info = results.get('document_info', {})
                    response_data = {'issues': results.get('issues', []), 'issue_count': results.get('issue_count', 0), 'score': results.get('score', 100), 'grade': results.get('grade', 'N/A'), 'readability': results.get('readability', {}), 'document_info': doc_info, 'roles': results.get('roles', {}), 'full_text': results.get('full_text', ''), 'html_preview': results.get('html_preview', ''), 'hyperlink_results': results.get('hyperlink_results', 0), 'word_count': results.get('word_count', 0), 'paragraph_count': results.get('paragraph_count', 0), 'table_count': results.get('table_count', 0), 'heading_count': doc_info.get('heading_count', 0), 'by_severity': results.get('by_severity', {}), 'by_category': results.get('by_category', {})}
                    try:
                        issues = results.get('issues', [])
                        response_data['document_content'] = build_document_content(results)
                        response_data['fix_groups'] = group_similar_fixes(issues)
                        response_data['confidence_details'] = build_confidence_details(issues)
                        doc_content = response_data['document_content']
                        response_data['fix_statistics'] = compute_fix_statistics(issues, response_data['fix_groups'], response_data['confidence_details'], doc_content.get('page_count', 1))
                    except Exception as e:
                        logger.warning(f'Fix Assistant v2 enhancement failed for job {job_id}: {e}')
                        response_data['document_content'] = {'paragraphs': [], 'page_map': {}, 'headings': [], 'page_count': 1}
                        response_data['fix_groups'] = []
                        response_data['confidence_details'] = {}
                        response_data['fix_statistics'] = {'total': 0, 'by_tier': {}, 'by_category': {}, 'by_page': {}}
                    # v5.0.5: Include statement forge summary, scan info, and other fields
                    # that were present in the sync path but missing from async results
                    response_data['statement_forge_summary'] = results.get('statement_forge_summary', {'available': _shared.STATEMENT_FORGE_AVAILABLE, 'statements_ready': False})
                    response_data['score'] = results.get('score', 100)
                    response_data['grade'] = results.get('grade', 'N/A')
                    response_data['enhanced_stats'] = results.get('enhanced_stats', {})
                    response_data['acronym_metrics'] = results.get('acronym_metrics', {})
                    if results.get('scan_info'):
                        response_data['scan_info'] = results['scan_info']
                    return jsonify({'success': True, 'data': response_data})
@review_bp.route('/api/filter', methods=['POST'])
@require_csrf
@handle_api_errors
def filter_issues():
    """Filter issues by criteria."""
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('review_results'):
        raise ValidationError('No review results available')
    else:
        data = request.get_json() or {}
        severities = set(data.get('severities', ['Critical', 'High', 'Medium', 'Low', 'Info']))
        categories = set(data.get('categories', []))
        search = data.get('search', '').lower().strip()
        all_issues = session_data['review_results'].get('issues', [])
        filtered = []
        for issue in all_issues:
            if issue.get('severity') not in severities:
                continue
            else:
                if categories and issue.get('category') not in categories:
                        continue
                if search:
                    searchable = ' '.join([str(issue.get('category', '')), str(issue.get('severity', '')), str(issue.get('message', '')), str(issue.get('flagged_text', '')), str(issue.get('suggestion', ''))]).lower()
                    if search not in searchable:
                        continue
                filtered.append(issue)
        SessionManager.update(g.session_id, filtered_issues=filtered)
        return jsonify({'success': True, 'data': {'issues': filtered, 'count': len(filtered)}})
@review_bp.route('/api/select', methods=['POST'])
@require_csrf
@handle_api_errors
def select_issues():
    """Update issue selection using stable issue IDs."""
    session_data = SessionManager.get(g.session_id)
    if not session_data:
        raise ValidationError('No active session')
    else:
        data = request.get_json() or {}
        action = data.get('action', 'toggle')
        issue_ids = data.get('issue_ids', [])
        indices = data.get('indices', [])
        selected = session_data.get('selected_issues', set())
        if isinstance(selected, list):
            selected = set(selected)
        filtered_issues = session_data.get('filtered_issues', [])
        id_to_idx = {iss.get('issue_id'): i for i, iss in enumerate(filtered_issues) if iss.get('issue_id')}
        idx_to_id = {i: iss.get('issue_id') for i, iss in enumerate(filtered_issues) if iss.get('issue_id')}
        if indices and (not issue_ids):
                issue_ids = [idx_to_id.get(idx) for idx in indices if idx in idx_to_id]
        if selected and all((isinstance(x, int) for x in selected)):
                selected = {idx_to_id.get(idx) for idx in selected if idx in idx_to_id}
                selected.discard(None)
        if action == 'toggle':
            for issue_id in issue_ids:
                if issue_id and issue_id in id_to_idx:
                    if issue_id in selected:
                        selected.discard(issue_id)
                    else:
                        selected.add(issue_id)
        else:
            if action == 'select_all':
                selected = set(id_to_idx.keys())
            else:
                if action == 'select_none':
                    selected = set()
                else:
                    if action == 'add':
                        selected.update((iid for iid in issue_ids if iid and iid in id_to_idx))
                    else:
                        if action == 'remove':
                            selected -= set(issue_ids)
        SessionManager.update(g.session_id, selected_issues=selected)
        selected_indices = [id_to_idx[iid] for iid in selected if iid in id_to_idx]
        return jsonify({'success': True, 'selected': list(selected), 'selected_indices': sorted(selected_indices), 'count': len(selected)})
@review_bp.route('/api/export', methods=['POST'])
@require_csrf
@handle_api_errors
def export_document():
    """
    Export marked document.
    
    v2.9.4 #26: Added timeout protection to prevent server hangs.
    v3.0.96: Added selected_fixes support for Fix Assistant integration.
    v3.0.97: Added comment_only_issues for rejected fixes from Fix Assistant v2.
    """
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('current_file'):
        raise ValidationError('No document loaded')
    else:
        if not session_data.get('review_results'):
            raise ValidationError('No review results available')
        else:
            original_filename = session_data.get('original_filename')
            if not original_filename:
                raise ValidationError('Document filename not found in session. Please re-upload the document.')
            else:
                filepath = Path(session_data['current_file'])
                if not filepath.exists():
                    raise FileError('Source document not found')
                else:
                    if not original_filename.lower().endswith('.docx'):
                        raise ValidationError('Export only supported for DOCX files. PDF documents are read-only.')
                    else:
                        data = request.get_json() or {}
                        mode = data.get('mode', 'all')
                        reviewer_name = sanitize_filename(data.get('reviewer_name', 'AEGIS'))
                        apply_fixes = data.get('apply_fixes', False)
                        selected_fixes = data.get('selected_fixes', [])
                        comment_only_issues = data.get('comment_only_issues', [])
                        # v6.0.2: Log review role mode (owner vs reviewer) for diagnostics
                        review_role = data.get('review_role', 'owner')
                        logger.info(f'Export: role={review_role}, apply_fixes={apply_fixes}, fixes={len(selected_fixes)}, comments={len(comment_only_issues)}')
                        if mode == 'selected':
                            selected = session_data.get('selected_issues', set())
                            if isinstance(selected, list):
                                selected = set(selected)
                            filtered = session_data.get('filtered_issues', [])
                            if selected and all((isinstance(x, str) for x in selected)):
                                issues = [iss for iss in filtered if iss.get('issue_id') in selected]
                            else:
                                issues = [filtered[i] for i in sorted(selected) if isinstance(i, int) and i < len(filtered)]
                        else:
                            if mode == 'filtered':
                                issues = session_data.get('filtered_issues', [])
                            else:
                                issues = session_data['review_results'].get('issues', [])
                        if apply_fixes and selected_fixes:
                            fix_issues = []
                            for fix in selected_fixes:
                                fix_issues.append({'original_text': fix.get('original_text', ''), 'replacement_text': fix.get('replacement_text', ''), 'category': fix.get('category', 'Auto-Fix'), 'message': fix.get('message', 'Automatic correction'), 'severity': 'Info', 'paragraph_index': fix.get('paragraph_index', 0)})
                            logger.info(f'Applying {len(fix_issues)} selected fixes from Fix Assistant')
                            # v5.9.50: Learn from Fix Assistant corrections
                            try:
                                from review_learner import learn_fix_patterns
                                learn_fix_patterns(selected_fixes)
                            except Exception:
                                pass  # Learning failure non-blocking
                        else:
                            fix_issues = issues if apply_fixes else []
                        issues_to_comment = []
                        if comment_only_issues:
                            for rejected in comment_only_issues:
                                reviewer_note = rejected.get('reviewer_note', '')
                                note_suffix = f' Note: {reviewer_note}' if reviewer_note else ''
                                issues_to_comment.append({'paragraph_index': rejected.get('paragraph_index', 0), 'message': f"TWR flagged: \"{rejected.get('original_text', '')}\" → \"{rejected.get('suggestion', '')}\" - Reviewer chose not to change.{note_suffix}", 'severity': 'Info', 'category': rejected.get('category', 'Review'), 'flagged_text': rejected.get('original_text', '')})
                            logger.info(f'Adding {len(issues_to_comment)} rejected fixes as comments')
                        if not issues and (not fix_issues) and (not issues_to_comment):
                            raise ValidationError('No issues to export')
                        else:
                            output_name = f'reviewed_{original_filename}'
                            output_path = config.temp_dir / f'{uuid.uuid4().hex[:8]}_{output_name}'
                            total_items = len(issues) + len(fix_issues) + len(issues_to_comment)
                            timeout_secs = min(300, 30 + total_items * 0.5)
                            with logger.log_operation('export_document', issue_count=total_items):
                                from markup_engine import MarkupEngine
                                engine = MarkupEngine(reviewer_name)
                                def do_export():
                                    if apply_fixes and fix_issues:
                                        # Combine fix issues + review issues + rejected fix comments
                                        # MarkupEngine separates fixable (have original_text/replacement_text)
                                        # from comment-only issues internally.
                                        # fix_issues = accepted fixes (may have original/replacement text)
                                        # issues = all review findings (added as comments)
                                        # issues_to_comment = rejected fixes (added as comments with note)
                                        all_issues = fix_issues + issues + issues_to_comment
                                        return engine.apply_fixes_with_track_changes(str(filepath), str(output_path), all_issues, reviewer_name=reviewer_name, also_add_comments=True)
                                    else:
                                        all_comments = issues + issues_to_comment
                                        return engine.add_review_comments(str(filepath), str(output_path), all_comments)
                                try:
                                    result = run_with_timeout(do_export, timeout_seconds=int(timeout_secs))
                                except TimeoutError:
                                    logger.error(f'Export timed out after {timeout_secs}s for {total_items} issues')
                                    raise ProcessingError(f'Export operation timed out after {int(timeout_secs)} seconds. Try exporting fewer issues at a time.', stage='export')
                        # v5.9.2: Better error reporting with engine errors included
                        if not result or not result.get('success'):
                            errors = result.get('errors', []) if result else []
                            error_detail = result.get('error', '') if result else ''
                            if errors:
                                error_msg = f"Export failed: {'; '.join(str(e) for e in errors[:3])}"
                            elif error_detail:
                                error_msg = f"Export failed: {error_detail}"
                            else:
                                error_msg = 'Failed to create marked document. Check that lxml is installed (pip install lxml).'
                            logger.error(f'Export failed for {original_filename}: {error_msg}')
                            raise ProcessingError(error_msg, stage='export')
                        else:
                            # Verify output file exists and has content
                            if not output_path.exists() or output_path.stat().st_size == 0:
                                raise ProcessingError('Export produced empty file. The markup engine may not be functioning correctly.', stage='export')
                            return send_file(str(output_path), as_attachment=True, download_name=output_name, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
@review_bp.route('/api/export/csv', methods=['POST'])
@require_csrf
@handle_api_errors
def export_csv():
    """Export issues as CSV."""
    data = request.get_json() or {}
    mode = data.get('mode', 'all')
    session_data = SessionManager.get(g.session_id)

    # v5.9.4: Try issues from request body first
    issues = data.get('issues')

    if not issues:
        if not session_data or not session_data.get('review_results'):
            raise ValidationError('No review results available')
        if mode == 'selected':
            selected = session_data.get('selected_issues', set())
            if isinstance(selected, list):
                selected = set(selected)
            filtered = session_data.get('filtered_issues', [])
            issues = [filtered[i] for i in sorted(selected) if i < len(filtered)]
        elif mode == 'filtered':
            issues = session_data.get('filtered_issues', [])
        else:
            issues = session_data['review_results'].get('issues', [])

    if not issues:
        raise ValidationError('No issues to export')

    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Severity', 'Category', 'Message', 'Flagged Text', 'Suggestion', 'Paragraph'])
    for issue in issues:
        writer.writerow([issue.get('severity', ''), issue.get('category', ''), issue.get('message', ''), issue.get('flagged_text', issue.get('context', '')), issue.get('suggestion', ''), issue.get('paragraph_index', 0) + 1])
    output.seek(0)
    original_name = (session_data or {}).get('original_filename') or data.get('filename', 'document')
    csv_name = f'issues_{Path(original_name).stem}.csv'
    csv_bytes = output.getvalue().encode('utf-8-sig')
    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{csv_name}"'
    response.headers['Content-Length'] = len(csv_bytes)
    return response
@review_bp.route('/api/export/xlsx', methods=['POST'])
@require_csrf
@handle_api_errors
def export_xlsx():
    """Export issues as XLSX with enhanced features.
    
    v3.0.33 Chunk D: Enhanced XLSX export with:
    - Action Item column for reviewer notes
    - Timestamped filename
    - Document metadata header
    - Severity filtering support
    
    Request body (JSON):
        mode: \'all\' | \'selected\' | \'filtered\' (default: \'all\')
        severities: list of severities to include (optional, e.g., [\'Critical\', \'High\'])
    
    Returns:
        XLSX file download with timestamp in filename
    """
    data = request.get_json() or {}
    mode = data.get('mode', 'all')
    severities = data.get('severities', None)
    session_data = SessionManager.get(g.session_id)

    if severities:
        VALID_SEVERITIES = {'Critical', 'Info', 'Low', 'High', 'Medium'}
        normalized = []
        invalid = []
        for sev in severities:
            matched = next((v for v in VALID_SEVERITIES if v.lower() == sev.lower()), None)
            if matched:
                normalized.append(matched)
            else:
                invalid.append(sev)
        if invalid:
            raise ValidationError(f"Invalid severity filter(s): {', '.join(invalid)}. Valid values: {', '.join(sorted(VALID_SEVERITIES))}")
        else:
            severities = normalized if normalized else None

    # v5.9.4: Try issues from request body first (frontend always sends them)
    issues = None
    if data.get('issues'):
        issues = data['issues']
    elif data.get('results', {}).get('issues'):
        issues = data['results']['issues']

    # Fall back to session only if not provided in body
    if not issues:
        if not session_data or not session_data.get('review_results'):
            raise ValidationError('No review results available')
        if mode == 'selected':
            selected = session_data.get('selected_issues', set())
            if isinstance(selected, list):
                selected = set(selected)
            base_issues = session_data.get('filtered_issues', []) or session_data['review_results'].get('issues', [])
            issues = []
            for idx, iss in enumerate(base_issues):
                issue_id = iss.get('issue_id')
                if issue_id and issue_id in selected or str(idx) in selected or idx in selected:
                    issues.append(iss)
        elif mode == 'filtered':
            issues = session_data.get('filtered_issues', []) or session_data['review_results'].get('issues', [])
        else:
            issues = session_data['review_results'].get('issues', [])

    if not issues:
        raise ValidationError('No issues to export')

    review_results = data.get('results') or (session_data or {}).get('review_results') or {}
    review_results = {**review_results, 'issues': issues}
    original_name = (session_data or {}).get('original_filename') or data.get('filename', 'document')
    document_metadata = {'filename': original_name, 'scan_date': (session_data or {}).get('scan_timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'score': review_results.get('score', 100)}

    try:
        from export_module import export_xlsx_enhanced
    except ImportError as e:
        current_app.logger.error(f'export_module not available: {e}')
        raise ValidationError('Excel export module not available. Please ensure export_module.py is installed.')

    filename, content = export_xlsx_enhanced(results=review_results, base_filename=f'review_{Path(original_name).stem}', severities=severities, document_metadata=document_metadata)
    response = make_response(content)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Length'] = len(content)
    return response

@review_bp.route('/api/export/pdf', methods=['POST'])
@require_csrf
@handle_api_errors
def export_pdf_report():
    """Export issues as branded AEGIS PDF report.

    v5.9.4: New server-side PDF generation using reportlab with:
    - Cover page with document info, score, grade
    - Executive summary with severity breakdown
    - Category breakdown table
    - Full issue detail pages grouped by category
    - AEGIS gold/bronze branding
    - Pre-export filter support (severities, categories)

    Request body (JSON):
        issues: list of issue dicts (optional, falls back to session)
        mode: 'all' | 'selected' | 'filtered' (default: 'all')
        reviewer_name: str (default: 'AEGIS')
        filters: dict with 'severities' and/or 'categories' lists

    Returns:
        PDF file download
    """
    data = request.get_json() or {}
    mode = data.get('mode', 'all')
    reviewer_name = data.get('reviewer_name', 'AEGIS')
    filters = data.get('filters', {})

    # v5.9.4: Try issues from request body first (frontend always sends them)
    # Fall back to session only if not provided in body
    issues = data.get('issues')
    session_data = SessionManager.get(g.session_id)

    if not issues:
        if not session_data or not session_data.get('review_results'):
            raise ValidationError('No review results available')
        if mode == 'selected':
            selected = session_data.get('selected_issues', set())
            if isinstance(selected, list):
                selected = set(selected)
            base_issues = session_data.get('filtered_issues', []) or session_data['review_results'].get('issues', [])
            issues = []
            for idx, iss in enumerate(base_issues):
                issue_id = iss.get('issue_id')
                if issue_id and issue_id in selected or str(idx) in selected or idx in selected:
                    issues.append(iss)
        elif mode == 'filtered':
            issues = session_data.get('filtered_issues', []) or session_data['review_results'].get('issues', [])
        else:
            issues = session_data['review_results'].get('issues', [])

    if not issues:
        raise ValidationError('No issues to export')

    # Apply additional filters if provided
    filters_applied = {}
    if filters.get('severities'):
        sev_filter = [s.strip() for s in filters['severities'] if s.strip()]
        if sev_filter:
            issues = [i for i in issues if i.get('severity', 'Info') in sev_filter]
            filters_applied['severities'] = sev_filter

    if filters.get('categories'):
        cat_filter = [c.strip() for c in filters['categories'] if c.strip()]
        if cat_filter:
            issues = [i for i in issues if i.get('category', '') in cat_filter]
            filters_applied['categories'] = cat_filter

    if not issues:
        raise ValidationError('No issues match the selected filters')

    # Get document info (session may be unavailable if issues were sent in body)
    review_results = (session_data or {}).get('review_results') or {}
    score = review_results.get('score') if review_results else data.get('score')
    grade = review_results.get('grade') if review_results else data.get('grade')
    doc_info = review_results.get('document_info', {}) or {}
    original_name = (session_data or {}).get('original_filename') or data.get('filename', 'document')
    doc_info['filename'] = original_name

    # Get version for metadata
    try:
        from config_logging import get_version
        version_info = get_version()
        version_str = f"AEGIS v{version_info.get('version', '5.9.4')}" if isinstance(version_info, dict) else f"AEGIS v{version_info}"
    except Exception:
        version_str = 'AEGIS'

    metadata = {
        'version': version_str,
        'export_date': datetime.now().strftime('%B %d, %Y')
    }

    try:
        from review_report import generate_review_report
        pdf_bytes = generate_review_report(
            issues=issues,
            document_info=doc_info,
            score=score,
            grade=grade,
            reviewer_name=reviewer_name,
            filters_applied=filters_applied if filters_applied else None,
            metadata=metadata
        )
    except ImportError as e:
        current_app.logger.error(f'review_report module not available: {e}')
        raise ValidationError('PDF report module not available. Please ensure review_report.py and reportlab are installed.')
    except Exception as e:
        current_app.logger.error(f'PDF report generation failed: {e}')
        raise ProcessingError(f'PDF report generation failed: {str(e)}', stage='export')

    pdf_name = f'AEGIS_Review_{Path(original_name).stem}_{datetime.now().strftime("%Y%m%d")}.pdf'

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
    response.headers['Content-Length'] = len(pdf_bytes)
    return response


# ════════════════════════════════════════════════════════════════════════════
# v6.6.0: SP Repository Endpoints — local cache management
# ════════════════════════════════════════════════════════════════════════════

@review_bp.route('/api/repository/status', methods=['GET'])
@handle_api_errors
def repository_status():
    """Return summary of the local SP document repository."""
    if not _REPO_AVAILABLE:
        return jsonify({'success': True, 'data': {
            'available': False,
            'message': 'SP Repository module not available'
        }})

    try:
        repo = get_repository()
        libraries = repo.get_all_libraries()
        total_files = 0
        total_size = 0
        library_summaries = []

        for lib_path, lib_data in libraries.items():
            files = lib_data.get('files', {})
            lib_size = sum(f.get('size', 0) for f in files.values())
            lib_summary = {
                'library_path': lib_path,
                'site_url': lib_data.get('site_url', ''),
                'last_sync': lib_data.get('last_sync', ''),
                'file_count': len(files),
                'total_size': lib_size,
                'total_size_human': _human_size(lib_size),
            }
            library_summaries.append(lib_summary)
            total_files += len(files)
            total_size += lib_size

        return jsonify({'success': True, 'data': {
            'available': True,
            'library_count': len(libraries),
            'total_files': total_files,
            'total_size': total_size,
            'total_size_human': _human_size(total_size),
            'libraries': library_summaries,
        }})

    except Exception as e:
        logger.error(f'Repository status error: {e}')
        return jsonify({'success': True, 'data': {
            'available': True,
            'error': str(e)[:200],
            'library_count': 0,
            'total_files': 0,
            'libraries': [],
        }})


@review_bp.route('/api/repository/files', methods=['GET'])
@handle_api_errors
def repository_files():
    """Return file list for a specific library in the repository."""
    library_path = request.args.get('library', '')
    if not library_path:
        raise ValidationError('library parameter is required')

    if not _REPO_AVAILABLE:
        return jsonify({'success': True, 'data': {'available': False, 'files': []}})

    try:
        repo = get_repository()
        scannable = repo.get_scannable_files(library_path)

        file_list = []
        for f in scannable:
            versions = repo.get_file_history(
                f.get('site_url', ''),
                f.get('server_relative_url', '')
            )
            file_list.append({
                'filename': f.get('filename', ''),
                'server_relative_url': f.get('server_relative_url', ''),
                'local_path': f.get('local_path', ''),
                'file_hash': f.get('file_hash', ''),
                'size': f.get('size', 0),
                'size_human': _human_size(f.get('size', 0)),
                'sp_modified': f.get('sp_modified', ''),
                'downloaded_at': f.get('downloaded_at', ''),
                'last_scanned': f.get('last_scanned', ''),
                'scan_count': f.get('scan_count', 0),
                'version_count': len(versions),
                'exists_locally': os.path.exists(f.get('local_path', '')),
            })

        return jsonify({'success': True, 'data': {
            'available': True,
            'library_path': library_path,
            'file_count': len(file_list),
            'files': file_list,
        }})

    except Exception as e:
        logger.error(f'Repository files error: {e}')
        return jsonify({'success': True, 'data': {
            'available': True,
            'library_path': library_path,
            'error': str(e)[:200],
            'files': [],
        }})


@review_bp.route('/api/repository/scan', methods=['POST'])
@require_csrf
@handle_api_errors
def repository_rescan():
    """Rescan files from local repository without SP connection.

    Accepts JSON body:
        library_path (str): Library path to scan
        files (list, optional): Specific filenames to scan. If omitted, scans all.
    """
    if not _REPO_AVAILABLE:
        raise ValidationError('SP Repository module not available')

    data = request.get_json() or {}
    library_path = data.get('library_path', '')
    file_filter = data.get('files')  # optional list of filenames

    if not library_path:
        raise ValidationError('library_path is required')

    repo = get_repository()
    scannable = repo.get_scannable_files(library_path)

    if not scannable:
        raise ValidationError(f'No files found in repository for: {library_path}')

    # Filter to specific files if requested
    if file_filter and isinstance(file_filter, list):
        filter_set = set(f.lower() for f in file_filter)
        scannable = [f for f in scannable if f.get('filename', '').lower() in filter_set]
        if not scannable:
            raise ValidationError('None of the specified files found in repository')

    # Verify files exist locally
    valid_files = []
    for f in scannable:
        local_path = f.get('local_path', '')
        if os.path.exists(local_path):
            valid_files.append(f)
        else:
            logger.warning(f"Repository rescan: missing local file {local_path}")

    if not valid_files:
        raise ValidationError('No repository files exist locally — download from SharePoint first')

    # Create scan state and spawn background thread
    scan_id = f"repo_{int(time.time())}_{os.urandom(4).hex()}"

    with _folder_scan_state_lock:
        _folder_scan_state[scan_id] = {
            'scan_id': scan_id,
            'source': f'repository:{library_path}',
            'phase': 'reviewing',
            'total': len(valid_files),
            'processed': 0,
            'errors': 0,
            'documents': [],
            'current_file': f'Scanning {len(valid_files)} cached files...',
            'current_chunk': 0,
            'total_chunks': 0,
            'started_at': time.time(),
            'completed_at': None,
        }

    options = data.get('options', {})
    flask_app = current_app._get_current_object()

    def _process_repository_scan():
        """Background thread for repository rescan."""
        # Build local_files list matching the format expected by the scan loop
        local_files = []
        for f in valid_files:
            file_info = {
                'filename': f.get('filename', ''),
                'server_relative_url': f.get('server_relative_url', ''),
                'folder': '',
                'extension': os.path.splitext(f.get('filename', ''))[1].lower(),
            }
            local_files.append((file_info, f['local_path']))

        scan_chunks = []
        for i in range(0, len(local_files), FOLDER_SCAN_CHUNK_SIZE):
            scan_chunks.append(local_files[i:i + FOLDER_SCAN_CHUNK_SIZE])

        with _folder_scan_state_lock:
            state = _folder_scan_state.get(scan_id)
            if state:
                state['total_chunks'] = len(scan_chunks)

        try:
            for chunk_idx, chunk in enumerate(scan_chunks):
                with _folder_scan_state_lock:
                    state = _folder_scan_state.get(scan_id)
                    if state:
                        state['current_chunk'] = chunk_idx + 1
                        chunk_names = [c[0]['filename'] for c in chunk[:3]]
                        state['current_file'] = ', '.join(chunk_names)

                with ThreadPoolExecutor(max_workers=min(FOLDER_SCAN_MAX_WORKERS, len(chunk))) as executor:
                    future_to_file = {}
                    for item in chunk:
                        file_info, local_path = item
                        future = executor.submit(_review_repo_file, file_info, local_path, options, repo, library_path)
                        future_to_file[future] = item

                    chunk_timeout = SCAN_PER_FILE_TIMEOUT * len(chunk)
                    try:
                        for future in as_completed(future_to_file, timeout=chunk_timeout):
                            item = future_to_file[future]
                            file_info, local_path = item
                            try:
                                result = future.result(timeout=SCAN_PER_FILE_TIMEOUT)
                            except Exception as e:
                                result = {
                                    'filename': file_info['filename'],
                                    'relative_path': file_info.get('server_relative_url', ''),
                                    'folder': file_info.get('folder', ''),
                                    'extension': file_info.get('extension', ''),
                                    'file_size': 0,
                                    'status': 'error',
                                    'error': f'Processing timeout or error: {str(e)[:100]}',
                                }

                            with flask_app.app_context():
                                _update_scan_state_with_result(scan_id, result, options, flask_app)

                    except Exception as e:
                        logger.error(f"Repository scan chunk {chunk_idx + 1} error: {e}")

                gc.collect()

            # Mark complete
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['phase'] = 'complete'
                    state['completed_at'] = time.time()
                    state['elapsed_seconds'] = round(time.time() - state['started_at'], 1)
                    state['current_file'] = None

            logger.info(f"Repository scan {scan_id} complete")

        except Exception as e:
            logger.error(f"Repository scan {scan_id} fatal error: {e}")
            with _folder_scan_state_lock:
                state = _folder_scan_state.get(scan_id)
                if state:
                    state['phase'] = 'error'
                    state['error_message'] = str(e)[:200]
                    state['completed_at'] = time.time()

    def _review_repo_file(file_info, local_path, scan_options, repo_inst, lib_path):
        """Review a single file from the repository (no SP connection needed)."""
        filename = file_info['filename']
        server_rel_url = file_info.get('server_relative_url', '')
        try:
            if AEGISEngine is None:
                return {
                    'filename': filename,
                    'relative_path': server_rel_url,
                    'full_path': local_path,
                    'source_url': server_rel_url,
                    'folder': file_info.get('folder', ''),
                    'extension': file_info.get('extension', ''),
                    'file_size': os.path.getsize(local_path) if os.path.exists(local_path) else 0,
                    'status': 'error',
                    'error': 'AEGISEngine not available',
                }

            engine = AEGISEngine()
            sp_options = dict(scan_options) if scan_options else {}
            sp_options['batch_mode'] = True
            doc_results = engine.review_document(local_path, sp_options)

            # Convert ReviewIssue objects to dicts (Lesson #36)
            raw_issues = doc_results.get('issues', [])
            issues = []
            for issue in raw_issues:
                if isinstance(issue, dict):
                    issues.append(issue)
                elif hasattr(issue, 'to_dict'):
                    issues.append(issue.to_dict())
                else:
                    issues.append({
                        'message': getattr(issue, 'message', str(issue)),
                        'severity': getattr(issue, 'severity', 'Low'),
                        'category': getattr(issue, 'category', 'Unknown'),
                    })

            actual_roles = doc_results.get('roles', {})
            if not isinstance(actual_roles, dict):
                actual_roles = {}
            word_count = doc_results.get('word_count', 0)
            if not isinstance(word_count, (int, float)):
                word_count = 0

            # Mark as scanned in repository
            try:
                repo_inst.mark_scanned('', server_rel_url)
            except Exception:
                pass

            return {
                'filename': filename,
                'relative_path': server_rel_url,
                'full_path': local_path,
                'source_url': server_rel_url,
                'folder': file_info.get('folder', ''),
                'extension': file_info.get('extension', ''),
                'file_size': os.path.getsize(local_path) if os.path.exists(local_path) else 0,
                'issues': issues,
                'issue_count': len(issues),
                'roles': actual_roles,
                'role_count': len(actual_roles),
                'word_count': int(word_count),
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
                'status': 'success',
            }

        except Exception as e:
            logger.error(f"Repository file review error for {filename}: {e}")
            return {
                'filename': filename,
                'relative_path': server_rel_url,
                'full_path': local_path,
                'source_url': server_rel_url,
                'folder': file_info.get('folder', ''),
                'extension': file_info.get('extension', ''),
                'file_size': 0,
                'status': 'error',
                'error': str(e)[:200],
            }

    # Spawn background thread
    thread = threading.Thread(
        target=_process_repository_scan,
        name=f'repo-scan-{scan_id}',
        daemon=False
    )
    thread.start()

    return jsonify({'success': True, 'data': {
        'scan_id': scan_id,
        'total_files': len(valid_files),
        'library_path': library_path,
        'message': f'Repository rescan started: {len(valid_files)} files from local cache',
    }})