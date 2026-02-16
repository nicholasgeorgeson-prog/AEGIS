"""
Jobs and hyperlink health routes Blueprint.

Handles job management and hyperlink health validation endpoints.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file, g

from routes._shared import (
    require_csrf,
    handle_api_errors,
    config,
    logger,
    SessionManager,
    ValidationError
)
import routes._shared as _shared


# Import job-related utilities
try:
    from job_manager import get_job_manager, JobStatus
except ImportError:
    get_job_manager = None
    JobStatus = None

# Import hyperlink health utilities
try:
    from hyperlink_health import validate_document_links
    from hyperlink_health_export import (
        export_report_json,
        export_report_html,
        export_report_csv,
    )
except ImportError:
    validate_document_links = None


# Custom exceptions
class FileError(Exception):
    """Raised when file operations fail."""
    pass


class ProcessingError(Exception):
    """Raised when processing fails."""
    pass


jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/api/hyperlink-health/status', methods=['GET'])
@handle_api_errors
def hyperlink_health_status():
    """
    Get hyperlink health module status.
    
    Returns availability and configuration info.
    
    v3.0.37: Added ps1_validator mode and availability check
    """
    ps1_available = False
    ps1_path = None
    configured_mode = 'offline'
    if _shared.HYPERLINK_HEALTH_AVAILABLE:
        from hyperlink_health import HyperlinkHealthValidator
        validator = HyperlinkHealthValidator(mode='offline')
        ps1_path = validator._find_ps1_validator()
        ps1_available = ps1_path is not None
        config_file = config.base_dir / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    configured_mode = user_config.get('hyperlink_settings', {}).get('validation_mode', 'offline')
            except (IOError, json.JSONDecodeError):
                pass
    return jsonify({'available': _shared.HYPERLINK_HEALTH_AVAILABLE, 'version': '1.0.0' if _shared.HYPERLINK_HEALTH_AVAILABLE else None, 'modes': ['offline', 'validator', 'ps1_validator'] if _shared.HYPERLINK_HEALTH_AVAILABLE else [], 'default_mode': 'offline', 'configured_mode': configured_mode, 'ps1_validator': {'available': ps1_available, 'path': ps1_path}, 'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'})


@jobs_bp.route('/api/hyperlink-health/validate', methods=['POST'])
@require_csrf
@handle_api_errors
def validate_hyperlinks():
    """
    Validate hyperlinks in the current document.
    
    Request body (optional):
        mode: 'offline' (default), 'validator', or 'ps1_validator'
              If not specified, reads from config.json hyperlink_settings.validation_mode
        
    Returns:
        Full hyperlink health report with all link statuses
        
    v3.0.33 Chunk B: Added ps1_validator mode for PowerShell-based validation
    v3.0.37: Mode now reads from config if not specified in request
    """
    if not _shared.HYPERLINK_HEALTH_AVAILABLE:
        raise ProcessingError('Hyperlink Health module not available', stage='hyperlink_validation')
    else:
        session_data = SessionManager.get(g.session_id)
        if not session_data or not session_data.get('current_file'):
            raise ValidationError('No document loaded')
        else:
            filepath = Path(session_data['current_file'])
            if not filepath.exists():
                raise FileError('Document file not found')
            else:
                data = request.get_json(silent=True) or {}
                mode = data.get('mode')
                if not mode:
                    config_file = config.base_dir / 'config.json'
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                user_config = json.load(f)
                                mode = user_config.get('hyperlink_settings', {}).get('validation_mode', 'offline')
                        except (IOError, json.JSONDecodeError):
                            mode = 'offline'
                    else:
                        mode = 'offline'
                if mode not in ['offline', 'validator', 'ps1_validator']:
                    mode = 'offline'
                logger.info(f'Hyperlink validation starting with mode: {mode}')
                try:
                    report = validate_document_links(filepath=str(filepath), mode=mode, base_path=str(filepath.parent))
                    SessionManager.update(g.session_id, hyperlink_health_report=report)
                    return jsonify({'success': True, 'mode_used': mode, 'report': report})
                except Exception as e:
                    logger.error(f'Hyperlink validation failed: {e}')
                    raise ProcessingError(f'Hyperlink validation failed: {str(e)}', stage='hyperlink_validation')


@jobs_bp.route('/api/hyperlink-health/export/<format>', methods=['GET'])
@handle_api_errors
def export_hyperlink_report(format):
    """
    Export hyperlink health report in specified format.
    
    Formats: json, html, csv
    
    Must first run /api/hyperlink-health/validate to generate report.
    """
    if not _shared.HYPERLINK_HEALTH_AVAILABLE:
        raise ProcessingError('Hyperlink Health module not available', stage='hyperlink_export')
    else:
        if format not in ['json', 'html', 'csv']:
            raise ValidationError(f'Unsupported format: {format}. Use json, html, or csv.')
        else:
            session_data = SessionManager.get(g.session_id)
            if not session_data or not session_data.get('current_file'):
                raise ValidationError('No document loaded')
            else:
                filepath = Path(session_data['current_file'])
                report_data = validate_document_links(filepath=str(filepath), mode='offline', base_path=str(filepath.parent))
                export_filename = f"hyperlink_health_{filepath.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                export_path = config.temp_dir / export_filename
                try:
                    from hyperlink_health import HyperlinkHealthReport, LinkStatusRecord
                    report = HyperlinkHealthReport(document_path=report_data.get('document_path', ''), document_name=report_data.get('document_name', ''), generated_at=report_data.get('generated_at', ''), validation_mode=report_data.get('validation_mode', 'offline'))
                    for link_dict in report_data.get('links', []):
                        record = LinkStatusRecord.from_dict(link_dict)
                        report.links.append(record)
                    report.calculate_summary()
                    if format == 'json':
                        export_report_json(report, str(export_path))
                        mimetype = 'application/json'
                    else:
                        if format == 'html':
                            export_report_html(report, str(export_path))
                            mimetype = 'text/html'
                        else:
                            if format == 'csv':
                                export_report_csv(report, str(export_path))
                                mimetype = 'text/csv'
                    return send_file(export_path, mimetype=mimetype, as_attachment=True, download_name=export_filename)
                except Exception as e:
                    logger.error(f'Hyperlink export failed: {e}')
                    raise ProcessingError(f'Export failed: {str(e)}', stage='hyperlink_export')


@jobs_bp.route('/api/hyperlink-health/comments', methods=['POST'])
@require_csrf
@handle_api_errors
def insert_hyperlink_comments():
    """
    Insert comments at broken hyperlink locations in the document.
    
    v3.0.37 Batch G: Hyperlink comment insertion feature.
    
    Request body:
        mode: 'insert' (DOCX comments) or 'pack' (text file for manual use)
        author: Comment author name (default: 'AEGIS')
        
    Returns:
        success: True if operation completed
        output_path: Path to generated file
        broken_count: Number of broken links found
        comments_inserted: Number of comments inserted (insert mode only)
        
    Note: Must run /api/hyperlink-health/validate first to generate report.
    """
    session_data = SessionManager.get(g.session_id)
    if not session_data or not session_data.get('current_file'):
        raise ValidationError('No document loaded')
    else:
        filepath = Path(session_data['current_file'])
        if not filepath.exists():
            raise FileError('Document file not found')
        else:
            if filepath.suffix.lower() != '.docx':
                raise ValidationError('Comment insertion only supported for DOCX files')
            else:
                health_report = session_data.get('hyperlink_health_report')
                if not health_report:
                    raise ValidationError('No hyperlink health report found. Run /api/hyperlink-health/validate first.')
                else:
                    data = request.get_json() or {}
                    mode = data.get('mode', 'insert')
                    author = data.get('author', 'AEGIS')
                    if mode not in ['insert', 'pack']:
                        raise ValidationError('mode must be \'insert\' or \'pack\'')
                    else:
                        try:
                            from comment_inserter import process_hyperlink_health_results
                            temp_dir = Path(tempfile.gettempdir()) / 'twr_exports'
                            temp_dir.mkdir(exist_ok=True)
                            result = process_hyperlink_health_results(docx_path=str(filepath), health_report=health_report, mode=mode, author=author, output_dir=str(temp_dir))
                            if result.get('success'):
                                if result.get('output_path'):
                                    session_data['comment_export_path'] = result['output_path']
                                    SessionManager.update(g.session_id, comment_export_path=result['output_path'])
                                return jsonify({'success': True, 'mode': result['mode'], 'message': result['message'], 'broken_count': result['broken_count'], 'comments_inserted': result.get('comments_inserted', 0), 'output_available': bool(result.get('output_path'))})
                            else:
                                raise ProcessingError(result.get('error', 'Comment insertion failed'))
                        except ImportError:
                            raise ProcessingError('Comment inserter module not available')
                        except Exception as e:
                            logger.exception(f'Comment insertion failed: {e}')
                            raise ProcessingError(f'Comment insertion failed: {str(e)}')


@jobs_bp.route('/api/hyperlink-health/comments/download', methods=['GET'])
@handle_api_errors
def download_hyperlink_comments():
    """
    Download the generated comment file (DOCX or text pack).
    
    v3.0.37 Batch G: Download endpoint for comment files.
    
    Must run /api/hyperlink-health/comments first.
    """
    session_data = SessionManager.get(g.session_id)
    if not session_data:
        raise ValidationError('No active session')
    else:
        export_path = session_data.get('comment_export_path')
        if not export_path or not Path(export_path).exists():
            raise ValidationError('No comment file available. Run /api/hyperlink-health/comments first.')
        else:
            export_path = Path(export_path)
            if export_path.suffix.lower() == '.docx':
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                mimetype = 'text/plain'
            return send_file(export_path, mimetype=mimetype, as_attachment=True, download_name=export_path.name)


@jobs_bp.route('/api/job/status', methods=['GET'])
@handle_api_errors
def job_manager_status():
    """
    Get job manager status and capabilities.
    
    Returns:
        available: Whether job manager is available
        version: Module version
        active_jobs: Count of running jobs
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        return jsonify({'available': False, 'version': None, 'active_jobs': 0})
    else:
        manager = get_job_manager()
        running = manager.list_jobs(status=JobStatus.RUNNING)
        return jsonify({'available': True, 'version': '1.0.0', 'active_jobs': len(running), 'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'})


@jobs_bp.route('/api/job/<job_id>', methods=['GET'])
@handle_api_errors
def get_job(job_id):
    """
    Get status and progress of a specific job.
    
    Args:
        job_id: Job identifier
        
    Query params:
        include_result: If 'true', include full result data (for completed jobs)
        
    Returns:
        Job status, progress, elapsed time, ETA
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        raise ProcessingError('Job manager not available', stage='job_status')
    else:
        include_result = request.args.get('include_result', 'false').lower() == 'true'
        manager = get_job_manager()
        job = manager.get_job(job_id)
        if not job:
            return (jsonify({'success': False, 'error': f'Job not found: {job_id}'}), 404)
        else:
            return jsonify({'success': True, 'job': job.to_dict(include_result=include_result)})


@jobs_bp.route('/api/job/<job_id>/cancel', methods=['POST'])
@require_csrf
@handle_api_errors
def cancel_job(job_id):
    """
    Cancel a running job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Success status
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        raise ProcessingError('Job manager not available', stage='job_cancel')
    else:
        manager = get_job_manager()
        success = manager.cancel_job(job_id)
        if not success:
            job = manager.get_job(job_id)
            if not job:
                return (jsonify({'success': False, 'error': f'Job not found: {job_id}'}), 404)
            else:
                return (jsonify({'success': False, 'error': f'Cannot cancel job in state: {job.status.value}'}), 400)
        else:
            return jsonify({'success': True, 'message': f'Job {job_id} cancelled'})


@jobs_bp.route('/api/job/list', methods=['GET'])
@handle_api_errors
def list_jobs():
    """
    List jobs with optional filtering.
    
    Query params:
        status: Filter by status (pending, running, complete, failed, cancelled)
        type: Filter by job type (review, export, etc.)
        limit: Maximum results (default 20)
        
    Returns:
        List of jobs
    """
    if not _shared.JOB_MANAGER_AVAILABLE:
        raise ProcessingError('Job manager not available', stage='job_list')
    else:
        status_filter = request.args.get('status')
        job_type = request.args.get('type')
        limit = min(int(request.args.get('limit', 20)), 100)
        status = None
        if status_filter:
            try:
                status = JobStatus(status_filter)
            except ValueError:
                pass
        manager = get_job_manager()
        jobs = manager.list_jobs(status=status, job_type=job_type, limit=limit)
        return jsonify({'success': True, 'jobs': jobs, 'count': len(jobs)})
