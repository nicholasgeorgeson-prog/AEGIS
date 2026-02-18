from flask import Blueprint, request, jsonify, g, send_file, make_response, current_app
import io
import os
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
    get_engine
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


def _cleanup_old_scans():
    """Remove completed scan state older than _FOLDER_SCAN_CLEANUP_AGE seconds."""
    now = time.time()
    with _folder_scan_state_lock:
        to_remove = [
            sid for sid, state in _folder_scan_state.items()
            if state.get('phase') in ('complete', 'error')
            and now - state.get('completed_at', now) > _FOLDER_SCAN_CLEANUP_AGE
        ]
        for sid in to_remove:
            del _folder_scan_state[sid]


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
    """Development endpoint to load a predefined test file for testing."""
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
    """Serve a file from the temp directory for development testing."""
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

    def _review_single_doc(fp_str):
        """Review a single document in its own thread with its own engine."""
        filepath = Path(fp_str)
        if not filepath.exists():
            return {'filename': filepath.name, 'error': 'File not found'}
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), options)
            issues = doc_results.get('issues', [])
            doc_roles = doc_results.get('roles', {})
            if not isinstance(doc_roles, dict):
                doc_roles = {}
            actual_roles = {k: v for k, v in doc_roles.items() if not isinstance(v, dict) or k not in ['success', 'error']}
            doc_info = doc_results.get('document_info', {})
            word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0
            return {
                'filename': filepath.name,
                'filepath': str(filepath),
                'issues': issues,
                'roles': actual_roles,
                'word_count': word_count,
                'score': doc_results.get('score', 0),
                'grade': doc_results.get('grade', 'N/A'),
                'doc_results': doc_results,
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

    def _review_single(file_info):
        """Review one document with its own engine instance."""
        filepath = Path(file_info['path'])
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), options)
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
            doc_info = doc_results.get('document_info', {})
            word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
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
                            filepath=result.get('relative_path', result['filename']),
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


def _human_size(size_bytes):
    """Convert bytes to human-readable size string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} TB'


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

    folder_path = Path(folder_path_str)
    if not folder_path.exists():
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
            scan_record_id = None
            if _shared.SCAN_HISTORY_AVAILABLE and flask_app:
                try:
                    with flask_app.app_context():
                        db = get_scan_history_db()
                        scan_record = db.record_scan(
                            filename=result['filename'],
                            filepath=result.get('relative_path', result['filename']),
                            results=doc_results_full,
                            options=options
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

        # Estimate remaining time
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

    def _review_single_async(file_info):
        """Review one document with its own engine instance."""
        filepath = Path(file_info['path'])
        try:
            engine = AEGISEngine()
            doc_results = engine.review_document(str(filepath), options)

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
            doc_info = doc_results.get('document_info', {})
            word_count = doc_info.get('word_count', 0) if isinstance(doc_info, dict) else 0

            return {
                'filename': file_info['filename'],
                'relative_path': file_info['relative_path'],
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
                'folder': file_info['folder'],
                'extension': file_info['extension'],
                'file_size': file_info['size'],
                'error': str(e),
                'status': 'error',
            }

    try:
        chunks = [discovered[i:i + FOLDER_SCAN_CHUNK_SIZE]
                  for i in range(0, len(discovered), FOLDER_SCAN_CHUNK_SIZE)]

        # v5.7.1: Per-file timeout — 5 minutes max per file to prevent hangs
        PER_FILE_TIMEOUT = 300

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
        if state['phase'] in ('reviewing',) and state.get('started_at'):
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
        response_data = {'issues': results.get('issues', []), 'issue_count': results.get('issue_count', 0), 'score': results.get('score', 100), 'grade': results.get('grade', 'N/A'), 'readability': results.get('readability', {}), 'document_info': doc_info, 'roles': results.get('roles', {}), 'full_text': results.get('full_text', ''), 'html_preview': results.get('html_preview', 0), 'hyperlink_results': results.get('hyperlink_results', 0), 'word_count': results.get('word_count', 0), 'paragraph_count': results.get('paragraph_count', 0), 'table_count': results.get('table_count', 0), 'heading_count': doc_info.get('heading_count', 0), 'by_severity': results.get('by_severity', {}), 'by_category': results.get('by_category', {})}
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
                    response_data = {'issues': results.get('issues', []), 'issue_count': results.get('issue_count', 0), 'score': results.get('score', 100), 'grade': results.get('grade', 'N/A'), 'readability': results.get('readability', {}), 'document_info': doc_info, 'roles': results.get('roles', {}), 'full_text': results.get('full_text', ''), 'html_preview': results.get('html_preview', 0), 'hyperlink_results': results.get('hyperlink_results', 0), 'word_count': results.get('word_count', 0), 'paragraph_count': results.get('paragraph_count', 0), 'table_count': results.get('table_count', 0), 'heading_count': doc_info.get('heading_count', 0), 'by_severity': results.get('by_severity', {}), 'by_category': results.get('by_category', {})}
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
                        reviewer_name = sanitize_filename(data.get('reviewer_name', 'TechWriter Review'))
                        apply_fixes = data.get('apply_fixes', False)
                        selected_fixes = data.get('selected_fixes', [])
                        comment_only_issues = data.get('comment_only_issues', [])
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