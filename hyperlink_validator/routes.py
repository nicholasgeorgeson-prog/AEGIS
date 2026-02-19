"""
Hyperlink Validator Flask Routes
================================
API endpoints for standalone hyperlink validation.

Endpoints:
- POST /api/hyperlink-validator/validate - Start validation job
- GET  /api/hyperlink-validator/job/<job_id> - Poll job status/results
- POST /api/hyperlink-validator/cancel/<job_id> - Cancel running job
- GET  /api/hyperlink-validator/history - List validation runs
- GET  /api/hyperlink-validator/export/<job_id> - Export results
- GET  /api/hyperlink-validator/capabilities - Get available modes
- GET  /api/hyperlink-validator/health - Health check

v1.0.0: Initial implementation
"""

import json
import time
import hmac
import os
from functools import wraps
from flask import Blueprint, request, jsonify, session, g, Response
from typing import Optional

# Import logging and exceptions
try:
    from config_logging import get_logger, ValidationError, ProcessingError
    logger = get_logger('hyperlink_validator')
except ImportError:
    import logging
    logger = logging.getLogger('hyperlink_validator')

    class ValidationError(Exception):
        pass

    class ProcessingError(Exception):
        pass

# Import validator components
from .validator import (
    StandaloneHyperlinkValidator,
    validate_urls,
    validate_any_link,
    validate_docx_links,
    DOCX_EXTRACTION_AVAILABLE
)

# Check for Excel extraction support
try:
    from .excel_extractor import (
        ExcelExtractor,
        extract_excel_links,
        is_excel_available,
        OPENPYXL_AVAILABLE
    )
    EXCEL_EXTRACTION_AVAILABLE = OPENPYXL_AVAILABLE
except ImportError:
    EXCEL_EXTRACTION_AVAILABLE = False
from .models import (
    ValidationRequest,
    ValidationResult,
    ValidationSummary,
    ValidationRun,
    parse_url_list,
    classify_link_type,
    detect_url_typos
)

# Create blueprint
hv_blueprint = Blueprint('hyperlink_validator', __name__)


@hv_blueprint.before_request
def _hv_increase_upload_limit():
    """Raise upload limit to 200MB for export-highlighted endpoints.
    These endpoints receive the original file + full validation results JSON
    as multipart form data, which can exceed the default 50MB limit for
    large Excel workbooks with many hyperlinks."""
    if request.path.endswith(('/export-highlighted/excel', '/export-highlighted/docx')):
        request.max_content_length = 200 * 1024 * 1024  # 200MB


# =============================================================================
# STANDARDIZED ERROR HANDLING DECORATOR
# =============================================================================

def handle_hv_errors(f):
    """
    Decorator for standardized API error handling in Hyperlink Validator routes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)

            # Log slow operations
            elapsed = time.time() - start_time
            if elapsed > 5.0:
                logger.warning(f"Slow HV API call: {f.__name__} took {elapsed:.1f}s")

            return result

        except ValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 400
        except ProcessingError as e:
            logger.error(f"Processing error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROCESSING_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500
        except FileNotFoundError as e:
            logger.warning(f"File not found in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 404
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_JSON',
                    'message': f'Invalid JSON format: {e}',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 400
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500

    return decorated


# =============================================================================
# CSRF ENFORCEMENT FOR WRITE OPERATIONS
# =============================================================================

@hv_blueprint.before_request
def enforce_csrf_on_writes():
    """
    Enforce CSRF protection on all non-GET requests.
    """
    # Skip CSRF check for GET, HEAD, OPTIONS (safe methods)
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return None

    # Check if CSRF is enabled via config module
    try:
        from config_logging import get_config
        config = get_config()
        if not config.csrf_enabled:
            return None
    except (ImportError, AttributeError):
        # If config_logging not available, skip CSRF check
        return None

    # Get token from header or form
    token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    expected = session.get('csrf_token')

    if not token or not expected:
        logger.warning("CSRF validation failed on hyperlink_validator",
                       extra={'path': request.path, 'method': request.method})
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'Invalid or missing CSRF token'
            }
        }), 403

    # Compare tokens securely
    try:
        if not hmac.compare_digest(str(token), str(expected)):
            logger.warning("CSRF token mismatch on hyperlink_validator")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CSRF_ERROR',
                    'message': 'Invalid CSRF token'
                }
            }), 403
    except Exception:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'CSRF validation failed'
            }
        }), 403

    return None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@hv_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'module': 'hyperlink_validator',
        'version': '1.0.0'
    })


@hv_blueprint.route('/capabilities', methods=['GET'])
@handle_hv_errors
def get_capabilities():
    """
    Get available validation modes and capabilities.

    Returns:
        JSON with available modes, features, and their status
    """
    capabilities = StandaloneHyperlinkValidator.get_capabilities()

    return jsonify({
        'success': True,
        'capabilities': capabilities
    })


@hv_blueprint.route('/validate', methods=['POST'])
@handle_hv_errors
def start_validation():
    """
    Start a URL validation job.

    Request body:
    {
        "urls": ["https://example.com", ...] OR
        "url_text": "https://example.com\\nhttps://google.com",
        "mode": "validator",  // offline (format only) or validator (full HTTP)
        "options": {
            "timeout": 10,
            "retries": 3,
            "follow_redirects": true,
            "client_cert": ["/path/to/cert.pem", "/path/to/key.pem"],  // CAC/PIV auth
            "ca_bundle": "/path/to/ca-bundle.crt",  // Custom CA for .mil/.gov PKI
            "proxy": "http://proxy.corp.mil:8080",  // Enterprise proxy
            "verify_ssl": true
        },
        "async": true  // If false, returns results directly
    }

    Returns:
        JSON with job_id for async polling, or results if sync
    """
    data = request.get_json()

    if not data:
        raise ValidationError("Request body is required")

    # Parse URLs from either format
    urls = data.get('urls', [])
    url_text = data.get('url_text', '')

    if url_text:
        urls = parse_url_list(url_text)
    elif isinstance(urls, str):
        urls = parse_url_list(urls)

    if not urls:
        raise ValidationError("No valid URLs provided")

    # Validate URL count
    if len(urls) > 5000:
        raise ValidationError("Maximum 5000 URLs per request")

    # Deduplicate URLs: validate each unique URL once, map results back
    original_urls = urls
    seen = {}
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen[url] = True
            unique_urls.append(url)
    dedup_count = len(original_urls) - len(unique_urls)
    if dedup_count > 0:
        logger.info(f"Deduplicated {dedup_count} URLs: {len(original_urls)} -> {len(unique_urls)} unique")

    # Get options
    mode = data.get('mode', 'validator')
    options = data.get('options', {})
    is_async = data.get('async', True)

    # Validate mode - only two modes supported:
    # - 'offline': Format validation only (no network access)
    # - 'validator': Full HTTP validation with Windows integrated authentication
    valid_modes = ['offline', 'validator']
    if mode not in valid_modes:
        raise ValidationError(f"Invalid mode: {mode}. Must be one of: {', '.join(valid_modes)}")

    # Create validator with authentication options
    # Supports: Windows SSO, Client Certificates (CAC/PIV), Proxy, Custom CA
    client_cert = options.get('client_cert')
    if client_cert and isinstance(client_cert, list):
        client_cert = tuple(client_cert)  # Convert list to tuple for requests

    validator = StandaloneHyperlinkValidator(
        timeout=options.get('timeout', 10),
        retries=options.get('retries', 3),
        use_windows_auth=True,  # Always use Windows auth when available
        follow_redirects=options.get('follow_redirects', True),
        client_cert=client_cert,
        ca_bundle=options.get('ca_bundle'),
        proxy=options.get('proxy'),
        verify_ssl=options.get('verify_ssl', True)
    )

    if is_async:
        # Start async job with deduplicated URLs
        job_id = validator.start_validation_job(unique_urls, mode=mode, options=options)

        # Estimate time based on unique URL count and mode
        if mode == 'offline':
            estimated_time = len(unique_urls) * 0.01  # Very fast
        else:
            estimated_time = len(unique_urls) * 1.5  # ~1.5s per URL average

        return jsonify({
            'success': True,
            'job_id': job_id,
            'url_count': len(original_urls),
            'unique_url_count': len(unique_urls),
            'deduplicated': dedup_count,
            'mode': mode,
            'estimated_time_seconds': round(estimated_time, 1),
            'poll_url': f'/api/hyperlink-validator/job/{job_id}'
        })
    else:
        # Synchronous validation with deduplicated URLs
        run = validator.validate_urls_sync(unique_urls, mode=mode, options=options)

        # Map results back to all original URLs (duplicate results for duplicate URLs)
        result_map = {r.url: r for r in run.results}
        all_results = []
        for url in original_urls:
            r = result_map.get(url)
            if r:
                all_results.append(r.to_dict())

        return jsonify({
            'success': True,
            'run_id': run.run_id,
            'status': run.status,
            'results': all_results,
            'summary': run.summary.to_dict() if run.summary else None,
            'unique_url_count': len(unique_urls),
            'deduplicated': dedup_count
        })


@hv_blueprint.route('/job/<job_id>', methods=['GET'])
@handle_hv_errors
def get_job_status(job_id: str):
    """
    Get status and optionally results of a validation job.

    Query params:
        include_results: bool - Include full results (default: false for running, true for complete)
        include_domains: bool - Include per-domain breakdown in live_stats (default: true).
                                Set to false for lightweight polling.

    Returns:
        JSON with job status, progress, live_stats, and optionally results.

        When the job is running, the response includes job.live_stats with:
        - phase/phase_label: Current phase (extracting/validating/finalizing/complete)
        - Status counts: working, broken, blocked, timeout, redirect, ssl_error,
          dns_failed, auth_required, excluded, rate_limited, invalid, unknown
        - domains_checked: Per-domain health (domain -> {working, broken, total})
        - domain_count: Number of unique domains checked so far
        - avg_response_ms, min_response_ms, max_response_ms: Timing stats
        - urls_per_second: Throughput rate
        - last_completed_url, last_completed_status: Most recent completion
        - current_url: URL currently being validated
    """
    include_results = request.args.get('include_results', '').lower() == 'true'
    include_domains = request.args.get('include_domains', 'true').lower() != 'false'

    validator = StandaloneHyperlinkValidator()
    status = validator.get_job_status(job_id)

    if not status:
        return jsonify({
            'success': False,
            'error': {
                'code': 'JOB_NOT_FOUND',
                'message': f'Job {job_id} not found'
            }
        }), 404

    response = {
        'success': True,
        'job': status
    }

    # Optionally strip per-domain breakdown for lightweight polling
    if not include_domains and 'live_stats' in status and status['live_stats']:
        status['live_stats'].pop('domains_checked', None)

    # Include results for completed jobs
    if status['status'] == 'complete' and include_results:
        run = validator.get_job_results(job_id)
        if run and run.results:
            response['job']['results'] = [r.to_dict() for r in run.results]

    return jsonify(response)


@hv_blueprint.route('/cancel/<job_id>', methods=['POST'])
@handle_hv_errors
def cancel_job(job_id: str):
    """
    Cancel a running validation job.

    Returns:
        JSON with cancellation status
    """
    validator = StandaloneHyperlinkValidator()
    cancelled = validator.cancel_job(job_id)

    if cancelled:
        return jsonify({
            'success': True,
            'message': f'Job {job_id} cancelled'
        })
    else:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CANCEL_FAILED',
                'message': f'Could not cancel job {job_id}. Job may not exist or already completed.'
            }
        }), 400


@hv_blueprint.route('/history', methods=['GET'])
@handle_hv_errors
def get_history():
    """
    Get recent validation run history.

    Query params:
        limit: int - Maximum runs to return (default: 20)

    Returns:
        JSON with list of recent runs
    """
    limit = int(request.args.get('limit', 20))
    limit = min(max(limit, 1), 100)  # Clamp to 1-100

    history = StandaloneHyperlinkValidator.get_history(limit=limit)

    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


@hv_blueprint.route('/export/<job_id>', methods=['GET'])
@handle_hv_errors
def export_results(job_id: str):
    """
    Export validation results in various formats.

    Query params:
        format: str - Export format (csv, json, html). Default: csv

    Returns:
        File download with appropriate content type
    """
    export_format = request.args.get('format', 'csv').lower()

    if export_format not in ['csv', 'json', 'html']:
        raise ValidationError(f"Invalid format: {export_format}. Must be one of: csv, json, html")

    validator = StandaloneHyperlinkValidator()
    run = validator.get_job_results(job_id)

    if not run:
        return jsonify({
            'success': False,
            'error': {
                'code': 'JOB_NOT_FOUND',
                'message': f'Job {job_id} not found'
            }
        }), 404

    if run.status != 'complete':
        return jsonify({
            'success': False,
            'error': {
                'code': 'JOB_NOT_COMPLETE',
                'message': f'Job {job_id} is not complete (status: {run.status})'
            }
        }), 400

    # Import export functions
    from .export import export_csv, export_json, export_html

    timestamp = run.completed_at.replace(':', '-').replace('T', '_')[:19] if run.completed_at else 'unknown'

    if export_format == 'csv':
        content = export_csv(run.results, run.summary)
        filename = f'hyperlink_validation_{timestamp}.csv'
        mimetype = 'text/csv'

    elif export_format == 'json':
        content = export_json(run.results, run.summary, run)
        filename = f'hyperlink_validation_{timestamp}.json'
        mimetype = 'application/json'

    else:  # html
        content = export_html(run.results, run.summary, run)
        filename = f'hyperlink_validation_{timestamp}.html'
        mimetype = 'text/html'

    return Response(
        content,
        mimetype=mimetype,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@hv_blueprint.route('/clear-history', methods=['POST'])
@handle_hv_errors
def clear_history():
    """
    Clear all validation history.

    Returns:
        JSON with confirmation
    """
    StandaloneHyperlinkValidator.clear_history()

    return jsonify({
        'success': True,
        'message': 'Validation history cleared'
    })


@hv_blueprint.route('/validate-link', methods=['POST'])
@handle_hv_errors
def validate_single_link():
    """
    Validate a single link of any type.

    Request body:
    {
        "link": "https://example.com" or "mailto:test@example.com" or "#bookmark",
        "check_typos": true,
        "check_exists": false
    }

    Returns:
        JSON with validation result
    """
    data = request.get_json()

    if not data:
        raise ValidationError("Request body is required")

    link = data.get('link', '')
    if not link:
        raise ValidationError("Link is required")

    check_typos = data.get('check_typos', True)
    check_exists = data.get('check_exists', False)

    result = validate_any_link(link, check_typos=check_typos, check_exists=check_exists)

    return jsonify({
        'success': True,
        'result': result
    })


@hv_blueprint.route('/classify-link', methods=['POST'])
@handle_hv_errors
def classify_link():
    """
    Classify a link into its type.

    Request body:
    {
        "link": "https://example.com"
    }

    Returns:
        JSON with link type
    """
    data = request.get_json()

    if not data:
        raise ValidationError("Request body is required")

    link = data.get('link', '')
    if not link:
        raise ValidationError("Link is required")

    link_type = classify_link_type(link)

    return jsonify({
        'success': True,
        'link': link,
        'link_type': link_type
    })


@hv_blueprint.route('/check-typos', methods=['POST'])
@handle_hv_errors
def check_typos():
    """
    Check a URL for common typos.

    Request body:
    {
        "url": "https://gogle.com"
    }

    Returns:
        JSON with typo warnings and suggestions
    """
    data = request.get_json()

    if not data:
        raise ValidationError("Request body is required")

    url = data.get('url', '')
    if not url:
        raise ValidationError("URL is required")

    has_typos, issues = detect_url_typos(url)

    return jsonify({
        'success': True,
        'url': url,
        'has_typos': has_typos,
        'issues': issues
    })


@hv_blueprint.route('/validate-docx', methods=['POST'])
@handle_hv_errors
def validate_docx():
    """
    Extract and validate all hyperlinks from a DOCX file.

    Accepts multipart/form-data with a file upload.

    Form data:
        file: The DOCX file to process
        validate_web_urls: bool - Validate web URLs (default: true)
        check_bookmarks: bool - Validate internal bookmarks (default: true)
        check_cross_refs: bool - Validate cross-references (default: true)

    Returns:
        JSON with extracted links, validation results, and summary
    """
    if not DOCX_EXTRACTION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'DOCX extraction is not available'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send a DOCX file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    if not file.filename.lower().endswith('.docx'):
        raise ValidationError("File must be a DOCX document")

    # Get options from form data
    validate_web_urls = request.form.get('validate_web_urls', 'true').lower() == 'true'
    check_bookmarks = request.form.get('check_bookmarks', 'true').lower() == 'true'
    check_cross_refs = request.form.get('check_cross_refs', 'true').lower() == 'true'

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Validate the document
        result = validate_docx_links(
            tmp_path,
            validate_web_urls=validate_web_urls,
            check_bookmarks=check_bookmarks,
            check_cross_refs=check_cross_refs
        )

        if 'error' in result and result['error']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXTRACTION_ERROR',
                    'message': result['error']
                }
            }), 400

        return jsonify({
            'success': True,
            'filename': file.filename,
            **result
        })

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@hv_blueprint.route('/extract-docx', methods=['POST'])
@handle_hv_errors
def extract_docx():
    """
    Extract hyperlinks from a DOCX file without validation.

    Accepts multipart/form-data with a file upload.

    Form data:
        file: The DOCX file to process

    Returns:
        JSON with extracted links and document structure
    """
    if not DOCX_EXTRACTION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'DOCX extraction is not available'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send a DOCX file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    if not file.filename.lower().endswith('.docx'):
        raise ValidationError("File must be a DOCX document")

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Import extractor
        from .docx_extractor import DocxExtractor

        extractor = DocxExtractor()
        result = extractor.extract(tmp_path)

        if result.errors:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXTRACTION_ERROR',
                    'message': '; '.join(result.errors)
                }
            }), 400

        return jsonify({
            'success': True,
            'filename': file.filename,
            'links': [link.to_dict() for link in result.links],
            'structure': result.structure.to_dict(),
            'metadata': result.metadata,
            'link_count': len(result.links),
            'by_type': _count_links_by_type(result.links)
        })

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _count_links_by_type(links) -> dict:
    """Helper to count links by type."""
    counts = {}
    for link in links:
        link_type = link.link_type
        counts[link_type] = counts.get(link_type, 0) + 1
    return counts


# =============================================================================
# EXCEL FILE ENDPOINTS
# =============================================================================

@hv_blueprint.route('/validate-excel', methods=['POST'])
@handle_hv_errors
def validate_excel():
    """
    Extract and validate all hyperlinks from an Excel file.

    Accepts multipart/form-data with a file upload.

    Form data:
        file: The Excel file to process (.xlsx or .xls)
        validate_web_urls: bool - Validate web URLs (default: true)
        extract_from_values: bool - Extract URLs from cell values (default: true)
        extract_from_formulas: bool - Extract links from HYPERLINK() formulas (default: true)

    Returns:
        JSON with extracted links, validation results, and summary
    """
    if not EXCEL_EXTRACTION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'Excel extraction is not available. Install openpyxl: pip install openpyxl'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send an Excel file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in ['xlsx', 'xls']:
        raise ValidationError("File must be an Excel document (.xlsx or .xls)")

    # Get options from form data
    validate_web_urls = request.form.get('validate_web_urls', 'true').lower() == 'true'
    extract_from_values = request.form.get('extract_from_values', 'true').lower() == 'true'
    extract_from_formulas = request.form.get('extract_from_formulas', 'true').lower() == 'true'

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract links from Excel
        from .excel_extractor import ExcelExtractor

        extractor = ExcelExtractor(
            extract_from_values=extract_from_values,
            extract_from_formulas=extract_from_formulas
        )
        extraction_result = extractor.extract(tmp_path)

        if extraction_result.errors:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXTRACTION_ERROR',
                    'message': '; '.join(extraction_result.errors)
                }
            }), 400

        # Build response
        response_data = {
            'success': True,
            'filename': file.filename,
            'total_links': extraction_result.total_links,
            'sheets_processed': extraction_result.sheets_processed,
            'sheet_summaries': [s.to_dict() for s in extraction_result.sheet_summaries],
            'links': [link.to_dict() for link in extraction_result.links]
        }

        # Optionally validate web URLs
        if validate_web_urls and extraction_result.links:
            # Get unique web URLs
            web_urls = []
            for link in extraction_result.links:
                url = link.url
                if url.startswith(('http://', 'https://')) and url not in web_urls:
                    web_urls.append(url)

            if web_urls:
                # Create validator and run sync validation
                validator = StandaloneHyperlinkValidator(
                    timeout=10,
                    retries=2
                )
                run = validator.validate_urls_sync(web_urls, mode='validator')

                # Map results back to links
                url_results = {r.url: r.to_dict() for r in run.results}

                # Annotate each link with validation result
                for link_data in response_data['links']:
                    url = link_data['url']
                    if url in url_results:
                        link_data['validation'] = url_results[url]

                response_data['validation_summary'] = run.summary.to_dict() if run.summary else None
                response_data['validated_urls'] = len(web_urls)

        return jsonify(response_data)

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@hv_blueprint.route('/extract-excel', methods=['POST'])
@handle_hv_errors
def extract_excel():
    """
    Extract hyperlinks from an Excel file without validation.

    Accepts multipart/form-data with a file upload.

    Form data:
        file: The Excel file to process (.xlsx or .xls)
        extract_from_values: bool - Extract URLs from cell values (default: true)
        extract_from_formulas: bool - Extract links from HYPERLINK() formulas (default: true)

    Returns:
        JSON with extracted links and sheet summaries
    """
    if not EXCEL_EXTRACTION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'Excel extraction is not available. Install openpyxl: pip install openpyxl'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send an Excel file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in ['xlsx', 'xls']:
        raise ValidationError("File must be an Excel document (.xlsx or .xls)")

    # Get options from form data
    extract_from_values = request.form.get('extract_from_values', 'true').lower() == 'true'
    extract_from_formulas = request.form.get('extract_from_formulas', 'true').lower() == 'true'

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract links from Excel
        from .excel_extractor import ExcelExtractor

        extractor = ExcelExtractor(
            extract_from_values=extract_from_values,
            extract_from_formulas=extract_from_formulas
        )
        result = extractor.extract(tmp_path)

        if result.errors:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXTRACTION_ERROR',
                    'message': '; '.join(result.errors)
                }
            }), 400

        # Count links by source type
        by_source = {}
        for link in result.links:
            source = link.source.value
            by_source[source] = by_source.get(source, 0) + 1

        return jsonify({
            'success': True,
            'filename': file.filename,
            'total_links': result.total_links,
            'sheets_processed': result.sheets_processed,
            'sheet_summaries': [s.to_dict() for s in result.sheet_summaries],
            'links': [link.to_dict() for link in result.links],
            'by_source': by_source,
            'unique_urls': result.get_unique_urls()
        })

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@hv_blueprint.route('/excel-capabilities', methods=['GET'])
def get_excel_capabilities():
    """
    Get Excel extraction capabilities.

    Returns:
        JSON with supported formats and features
    """
    if EXCEL_EXTRACTION_AVAILABLE:
        from .excel_extractor import is_excel_available
        formats = is_excel_available()
    else:
        formats = {'xlsx': False, 'xls': False}

    return jsonify({
        'success': True,
        'excel_available': EXCEL_EXTRACTION_AVAILABLE,
        'formats': formats,
        'features': {
            'hyperlink_objects': True,
            'hyperlink_formulas': True,
            'cell_value_urls': True,
            'cell_value_emails': True,
            'comments': EXCEL_EXTRACTION_AVAILABLE
        }
    })


# =============================================================================
# PERSISTENT EXCLUSIONS ENDPOINTS
# =============================================================================

# Import storage module
try:
    from .storage import get_storage, StoredExclusion, LinkScanRecord
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


@hv_blueprint.route('/exclusions', methods=['GET'])
@handle_hv_errors
def get_exclusions():
    """
    Get all exclusion rules.

    Query params:
        active_only: bool - Only return active exclusions (default: true)

    Returns:
        JSON with list of exclusions
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    active_only = request.args.get('active_only', 'true').lower() == 'true'

    storage = get_storage()
    exclusions = storage.get_all_exclusions(active_only=active_only)

    return jsonify({
        'success': True,
        'exclusions': [exc.to_dict() for exc in exclusions],
        'count': len(exclusions)
    })


@hv_blueprint.route('/exclusions', methods=['POST'])
@handle_hv_errors
def add_exclusion():
    """
    Add a new exclusion rule.

    JSON body:
        pattern: str - Pattern to match
        match_type: str - How to match (exact, prefix, suffix, contains, regex)
        reason: str - Reason for exclusion
        treat_as_valid: bool - Whether to treat matched URLs as valid

    Returns:
        JSON with the created exclusion
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    pattern = data.get('pattern')
    if not pattern:
        raise ValidationError("Pattern is required")

    match_type = data.get('match_type', 'contains')
    if match_type not in ['exact', 'prefix', 'suffix', 'contains', 'regex']:
        raise ValidationError(f"Invalid match_type: {match_type}")

    storage = get_storage()
    exclusion_id = storage.add_exclusion(
        pattern=pattern,
        match_type=match_type,
        reason=data.get('reason', ''),
        treat_as_valid=data.get('treat_as_valid', True),
        created_by=data.get('created_by', 'user')
    )

    if exclusion_id is None:
        return jsonify({
            'success': False,
            'error': {'code': 'DUPLICATE', 'message': 'Exclusion with this pattern and match type already exists'}
        }), 409

    exclusion = storage.get_exclusion(exclusion_id)

    return jsonify({
        'success': True,
        'exclusion': exclusion.to_dict() if exclusion else {'id': exclusion_id}
    }), 201


@hv_blueprint.route('/exclusions/<int:exclusion_id>', methods=['GET'])
@handle_hv_errors
def get_exclusion(exclusion_id):
    """Get a single exclusion by ID."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    exclusion = storage.get_exclusion(exclusion_id)

    if not exclusion:
        return jsonify({
            'success': False,
            'error': {'code': 'NOT_FOUND', 'message': f'Exclusion {exclusion_id} not found'}
        }), 404

    return jsonify({
        'success': True,
        'exclusion': exclusion.to_dict()
    })


@hv_blueprint.route('/exclusions/<int:exclusion_id>', methods=['PUT', 'PATCH'])
@handle_hv_errors
def update_exclusion(exclusion_id):
    """
    Update an exclusion rule.

    JSON body (all optional):
        pattern: str
        match_type: str
        reason: str
        treat_as_valid: bool
        is_active: bool
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    storage = get_storage()

    # Check if exists
    existing = storage.get_exclusion(exclusion_id)
    if not existing:
        return jsonify({
            'success': False,
            'error': {'code': 'NOT_FOUND', 'message': f'Exclusion {exclusion_id} not found'}
        }), 404

    success = storage.update_exclusion(
        exclusion_id,
        pattern=data.get('pattern'),
        match_type=data.get('match_type'),
        reason=data.get('reason'),
        treat_as_valid=data.get('treat_as_valid'),
        is_active=data.get('is_active')
    )

    if success:
        updated = storage.get_exclusion(exclusion_id)
        return jsonify({
            'success': True,
            'exclusion': updated.to_dict() if updated else None
        })
    else:
        return jsonify({
            'success': False,
            'error': {'code': 'UPDATE_FAILED', 'message': 'No changes applied'}
        }), 400


@hv_blueprint.route('/exclusions/<int:exclusion_id>', methods=['DELETE'])
@handle_hv_errors
def delete_exclusion(exclusion_id):
    """Delete an exclusion rule."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    success = storage.delete_exclusion(exclusion_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': {'code': 'NOT_FOUND', 'message': f'Exclusion {exclusion_id} not found'}
        }), 404


@hv_blueprint.route('/exclusions/stats', methods=['GET'])
@handle_hv_errors
def get_exclusion_stats():
    """Get exclusion statistics."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    stats = storage.get_exclusion_stats()

    return jsonify({
        'success': True,
        'stats': stats
    })


# =============================================================================
# SCAN HISTORY ENDPOINTS
# =============================================================================

@hv_blueprint.route('/history', methods=['GET'])
@handle_hv_errors
def get_scan_history():
    """
    Get scan history.

    Query params:
        limit: int - Max records to return (default: 20)
        start_date: str - Filter by start date (ISO format)
        end_date: str - Filter by end date (ISO format)

    Returns:
        JSON with list of scan records
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    limit = request.args.get('limit', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    storage = get_storage()

    if start_date:
        scans = storage.get_scans_by_date_range(start_date, end_date)
    else:
        scans = storage.get_recent_scans(limit=limit)

    return jsonify({
        'success': True,
        'scans': [scan.to_dict() for scan in scans],
        'count': len(scans)
    })


@hv_blueprint.route('/history/<int:scan_id>', methods=['GET'])
@handle_hv_errors
def get_scan_record(scan_id):
    """Get a single scan record with full results."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    scan = storage.get_scan(scan_id)

    if not scan:
        return jsonify({
            'success': False,
            'error': {'code': 'NOT_FOUND', 'message': f'Scan {scan_id} not found'}
        }), 404

    # Get full results
    results = storage.get_scan_results(scan_id)

    return jsonify({
        'success': True,
        'scan': scan.to_dict(),
        'results': results
    })


@hv_blueprint.route('/history/<int:scan_id>', methods=['DELETE'])
@handle_hv_errors
def delete_scan_record(scan_id):
    """Delete a scan record."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    success = storage.delete_scan(scan_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': {'code': 'NOT_FOUND', 'message': f'Scan {scan_id} not found'}
        }), 404


@hv_blueprint.route('/history/stats', methods=['GET'])
@handle_hv_errors
def get_scan_stats():
    """Get overall scan statistics."""
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    storage = get_storage()
    stats = storage.get_scan_stats()

    return jsonify({
        'success': True,
        'stats': stats
    })


@hv_blueprint.route('/history/record', methods=['POST'])
@handle_hv_errors
def record_scan():
    """
    Record a completed scan.

    JSON body:
        source_type: str - paste, file, docx, excel
        source_name: str - Filename or description
        total_urls: int
        summary: dict - {working, broken, redirect, timeout, blocked, unknown, excluded}
        validation_mode: str
        scan_depth: str
        duration_ms: int
        results: list - Optional detailed results

    Returns:
        JSON with the created scan record
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    storage = get_storage()
    scan_id = storage.record_scan(
        source_type=data.get('source_type', 'paste'),
        source_name=data.get('source_name', ''),
        total_urls=data.get('total_urls', 0),
        summary=data.get('summary', {}),
        validation_mode=data.get('validation_mode', 'validator'),
        scan_depth=data.get('scan_depth', 'standard'),
        duration_ms=data.get('duration_ms', 0),
        results=data.get('results')
    )

    scan = storage.get_scan(scan_id)

    return jsonify({
        'success': True,
        'scan': scan.to_dict() if scan else {'id': scan_id}
    }), 201


@hv_blueprint.route('/history/clear', methods=['POST'])
@handle_hv_errors
def clear_old_scans():
    """
    Clear old scan records.

    JSON body:
        days_to_keep: int - Keep scans from last N days (default: 90)

    Returns:
        JSON with count of deleted records
    """
    if not STORAGE_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {'code': 'STORAGE_UNAVAILABLE', 'message': 'Storage module not available'}
        }), 501

    data = request.get_json() or {}
    days_to_keep = data.get('days_to_keep', 90)

    storage = get_storage()
    deleted = storage.clear_old_scans(days_to_keep=days_to_keep)

    return jsonify({
        'success': True,
        'deleted': deleted,
        'message': f'Deleted {deleted} scan records older than {days_to_keep} days'
    })


# =============================================================================
# HEADLESS BROWSER RESCAN ENDPOINTS (v3.0.123)
# =============================================================================

# Import headless validator
try:
    from .headless_validator import (
        is_playwright_available,
        rescan_failed_urls,
        get_headless_capabilities,
        HeadlessValidator
    )
    HEADLESS_AVAILABLE = is_playwright_available()
except ImportError:
    HEADLESS_AVAILABLE = False

    def get_headless_capabilities():
        return {
            'available': False,
            'install_command': 'pip install playwright && playwright install chromium'
        }

    def rescan_failed_urls(*args, **kwargs):
        return {'available': False, 'error': 'Headless module not available'}


@hv_blueprint.route('/rescan/capabilities', methods=['GET'])
@handle_hv_errors
def get_rescan_capabilities():
    """
    Get headless browser rescan capabilities.

    Returns:
        JSON with availability and installation instructions
    """
    caps = get_headless_capabilities()

    return jsonify({
        'success': True,
        'capabilities': caps
    })


@hv_blueprint.route('/rescan', methods=['POST'])
@handle_hv_errors
def rescan_failed():
    """
    Rescan failed/blocked URLs using headless browser.

    This endpoint uses a real Chromium browser to validate URLs that
    failed regular HTTP validation due to bot protection (403 Forbidden,
    Cloudflare blocks, etc.).

    Request body:
    {
        "urls": ["https://blocked-site.mil/", ...],
        "timeout": 30  // Optional, default 30 seconds
    }

    Returns:
        JSON with rescan results and summary showing how many URLs
        were "recovered" (now accessible via headless browser)
    """
    if not HEADLESS_AVAILABLE:
        caps = get_headless_capabilities()
        return jsonify({
            'success': False,
            'error': {
                'code': 'HEADLESS_UNAVAILABLE',
                'message': 'Headless browser not available',
                'install_command': caps.get('install_command', 'pip install playwright && playwright install chromium')
            }
        }), 501

    data = request.get_json()

    if not data:
        raise ValidationError("Request body is required")

    urls = data.get('urls', [])
    if not urls:
        raise ValidationError("No URLs provided for rescan")

    if len(urls) > 50:
        raise ValidationError("Maximum 50 URLs per rescan request (headless browser is slower)")

    timeout = data.get('timeout', 30)

    # Run headless rescan
    result = rescan_failed_urls(urls, timeout=timeout)

    if result.get('error'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RESCAN_ERROR',
                'message': result['error']
            }
        }), 500

    return jsonify({
        'success': True,
        'results': result.get('results', []),
        'summary': result.get('summary'),
        'message': f"Recovered {result.get('summary', {}).get('recovered', 0)} of {len(urls)} URLs"
    })


@hv_blueprint.route('/rescan/job/<job_id>', methods=['POST'])
@handle_hv_errors
def rescan_job_failures(job_id: str):
    """
    Rescan all failed/blocked URLs from a previous validation job.

    Automatically extracts URLs with BLOCKED, BROKEN (403), or similar
    statuses from the job results and rescans them with headless browser.

    Returns:
        JSON with rescan results and updated summary
    """
    if not HEADLESS_AVAILABLE:
        caps = get_headless_capabilities()
        return jsonify({
            'success': False,
            'error': {
                'code': 'HEADLESS_UNAVAILABLE',
                'message': 'Headless browser not available',
                'install_command': caps.get('install_command')
            }
        }), 501

    # Get the original job results
    validator = StandaloneHyperlinkValidator()
    run = validator.get_job_results(job_id)

    if not run:
        return jsonify({
            'success': False,
            'error': {
                'code': 'JOB_NOT_FOUND',
                'message': f'Job {job_id} not found'
            }
        }), 404

    if run.status != 'complete':
        return jsonify({
            'success': False,
            'error': {
                'code': 'JOB_NOT_COMPLETE',
                'message': f'Job {job_id} is not complete'
            }
        }), 400

    # Extract URLs that might benefit from headless rescan
    # These are typically bot-blocked URLs
    rescan_statuses = ['BLOCKED', 'AUTH_REQUIRED', 'BROKEN']
    failed_urls = []

    for result in run.results:
        if result.status in rescan_statuses:
            # Only rescan if it looks like bot protection (403) or connection issues
            if result.status_code in [403, 401, None] or result.status == 'BLOCKED':
                failed_urls.append(result.url)

    if not failed_urls:
        return jsonify({
            'success': True,
            'message': 'No URLs eligible for headless rescan',
            'results': [],
            'summary': {'total': 0, 'recovered': 0}
        })

    # Limit to 50 URLs
    if len(failed_urls) > 50:
        failed_urls = failed_urls[:50]
        logger.warning(f"Limiting rescan to first 50 of {len(failed_urls)} failed URLs")

    # Get timeout from request or use default
    data = request.get_json() or {}
    timeout = data.get('timeout', 30)

    # Run headless rescan
    result = rescan_failed_urls(failed_urls, timeout=timeout)

    if result.get('error'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RESCAN_ERROR',
                'message': result['error']
            }
        }), 500

    return jsonify({
        'success': True,
        'job_id': job_id,
        'original_failures': len(failed_urls),
        'results': result.get('results', []),
        'summary': result.get('summary'),
        'message': f"Recovered {result.get('summary', {}).get('recovered', 0)} of {len(failed_urls)} URLs"
    })


# =============================================================================
# HIGHLIGHTED DOCUMENT EXPORT ENDPOINTS (v3.0.110)
# =============================================================================

@hv_blueprint.route('/export-highlighted/capabilities', methods=['GET'])
@handle_hv_errors
def get_highlighted_export_capabilities():
    """
    Check which highlighted export formats are available.

    Returns:
        JSON with available formats (docx, excel)
    """
    from .export import is_highlighted_export_available

    capabilities = is_highlighted_export_available()

    return jsonify({
        'success': True,
        'capabilities': capabilities,
        'message': 'Highlighted export creates a copy of the original document with broken links visually marked.'
    })


@hv_blueprint.route('/export-highlighted/docx', methods=['POST'])
@handle_hv_errors
def export_highlighted_docx_endpoint():
    """
    Create a highlighted copy of a DOCX file with broken links marked.

    Broken links are highlighted with:
    - Red text color
    - Yellow background highlight
    - Strikethrough formatting

    Accepts multipart/form-data with:
        file: The original DOCX file
        results: JSON string of validation results (from /validate-docx or /job/<id>)

    Returns:
        The highlighted DOCX file as a download
    """
    from .export import export_highlighted_docx, DOCX_AVAILABLE

    if not DOCX_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'python-docx library not installed. Cannot create highlighted DOCX.'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send a DOCX file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    if not file.filename.lower().endswith('.docx'):
        raise ValidationError("File must be a DOCX document")

    # Get validation results from form data
    results_json = request.form.get('results', '')
    if not results_json:
        raise ValidationError("Validation results required. Provide 'results' as JSON string.")

    try:
        results_data = json.loads(results_json)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in results: {e}")

    # Convert results to ValidationResult objects
    from .models import ValidationResult
    results = []
    for r in results_data:
        if isinstance(r, dict):
            results.append(ValidationResult.from_dict(r))

    if not results:
        raise ValidationError("No validation results provided")

    # Save file temporarily
    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # v5.9.29: Log result stats for debugging export issues
        status_counts = {}
        for r in results:
            s = r.status.upper() if r.status else 'NONE'
            status_counts[s] = status_counts.get(s, 0) + 1
        logger.info(f"Export highlighted DOCX: {len(results)} results received, status breakdown: {status_counts}")

        # Create highlighted document
        success, message, file_bytes = export_highlighted_docx(tmp_path, results)

        logger.info(f"Export highlighted DOCX result: success={success}, message={message}, bytes={len(file_bytes)}")

        if not success:
            logger.warning(f"Export highlighted DOCX failed: {message}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXPORT_FAILED',
                    'message': message
                }
            }), 400

        # Generate output filename
        base_name = os.path.splitext(file.filename)[0]
        output_filename = f"{base_name}_broken_links_highlighted.docx"

        return Response(
            file_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                'Content-Disposition': f'attachment; filename="{output_filename}"',
                'X-Highlight-Count': message  # Include count in header
            }
        )

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@hv_blueprint.route('/export-highlighted/excel', methods=['POST'])
@handle_hv_errors
def export_highlighted_excel_endpoint():
    """
    Create a highlighted copy of an Excel file with broken link rows marked.

    Broken link rows are highlighted with:
    - Light red background fill on the entire row
    - Darker red fill and bold text on the URL cell
    - Comment on URL cell with error details

    Accepts multipart/form-data with:
        file: The original Excel file (.xlsx)
        results: JSON string of validation results
        link_column: Optional column number (1-based) containing URLs

    Returns:
        The highlighted Excel file as a download
    """
    from .export import export_highlighted_excel, OPENPYXL_AVAILABLE

    if not OPENPYXL_AVAILABLE:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FEATURE_UNAVAILABLE',
                'message': 'openpyxl library not installed. Cannot create highlighted Excel.'
            }
        }), 501

    # Check for file in request
    if 'file' not in request.files:
        raise ValidationError("No file provided. Send an Excel file as 'file' in multipart/form-data")

    file = request.files['file']

    if not file.filename:
        raise ValidationError("No file selected")

    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise ValidationError("File must be an Excel document (.xlsx or .xls)")

    # Get validation results from form data
    results_json = request.form.get('results', '')
    if not results_json:
        raise ValidationError("Validation results required. Provide 'results' as JSON string.")

    try:
        results_data = json.loads(results_json)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in results: {e}")

    # Convert results to ValidationResult objects
    from .models import ValidationResult
    results = []
    for r in results_data:
        if isinstance(r, dict):
            results.append(ValidationResult.from_dict(r))

    if not results:
        raise ValidationError("No validation results provided")

    # Get optional link column
    link_column_str = request.form.get('link_column', '')
    link_column = int(link_column_str) if link_column_str else None

    # Save file temporarily
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file.filename)[1], delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Create highlighted document
        success, message, file_bytes = export_highlighted_excel(tmp_path, results, link_column=link_column)

        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXPORT_FAILED',
                    'message': message
                }
            }), 400

        # Generate output filename
        base_name = os.path.splitext(file.filename)[0]
        ext = os.path.splitext(file.filename)[1]
        output_filename = f"{base_name}_broken_links_highlighted{ext}"

        return Response(
            file_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{output_filename}"',
                'X-Highlight-Count': message  # Include count in header
            }
        )

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
