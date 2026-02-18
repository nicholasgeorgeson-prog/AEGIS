#!/usr/bin/env python3
"""
AEGIS API Extensions
===============================
Additional API endpoints for enhanced functionality.
Version: reads from version.json

Features:
- Export to Excel, CSV, PDF, JSON
- Role network analysis and visualization
- Document history and trends
- Issue baselines and suppressions
- Batch processing
- Configuration management
- Dashboard analytics

Created by Nicholas Georgeson
"""

import io
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps
from collections import defaultdict

from flask import Blueprint, request, jsonify, send_file, g

# Import configuration and logging
from config_logging import get_logger, ValidationError, ProcessingError, VERSION

logger = get_logger('api_ext')

# Module version from central config
__version__ = VERSION

# Try to import optional modules
DATABASE_AVAILABLE = False
EXPORT_AVAILABLE = False
EXCEL_AVAILABLE = False
PDF_AVAILABLE = False
ROLE_ANALYZER_AVAILABLE = False

try:
    from database import (
        DocumentRepository, AnalysisRepository, BaselineRepository,
        RoleRepository, ConfigRepository, CustomWordRepository,
        compute_file_hash, init_database
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database module not available: {e}")

try:
    from export_module import (
        ExcelExporter, CSVExporter, PDFExporter, JSONExporter,
        ComplianceMatrixExporter, EXCEL_AVAILABLE as _EXCEL, PDF_AVAILABLE as _PDF
    )
    EXPORT_AVAILABLE = True
    EXCEL_AVAILABLE = _EXCEL
    PDF_AVAILABLE = _PDF
except ImportError as e:
    logger.warning(f"Export module not available: {e}")

try:
    from role_analyzer import RoleRelationshipAnalyzer, generate_role_report
    ROLE_ANALYZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Role analyzer not available: {e}")


# Create blueprint
api_ext = Blueprint('api_ext', __name__, url_prefix='/api')


# =============================================================================
# CSRF ENFORCEMENT FOR WRITE OPERATIONS
# =============================================================================

def verify_csrf_token(token: str, expected: str) -> bool:
    """Verify CSRF token matches expected value (timing-safe comparison)."""
    import hmac
    if not token or not expected:
        return False
    return hmac.compare_digest(token, expected)


@api_ext.before_request
def enforce_csrf_on_writes():
    """Enforce CSRF protection on all non-GET requests to this blueprint.
    
    This provides consistent CSRF protection across all write endpoints
    without requiring individual decorators on each route.
    """
    from flask import session
    from config_logging import get_config
    
    # Skip CSRF check for GET, HEAD, OPTIONS (safe methods)
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return None
    
    # Check if CSRF is enabled via config module (same as app.py)
    config = get_config()
    if not config.csrf_enabled:
        return None
    
    # Get token from header or form
    token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    expected = session.get('csrf_token')
    
    if not token or not expected or not verify_csrf_token(token, expected):
        logger.warning("CSRF validation failed on api_ext",
                      path=request.path,
                      method=request.method,
                      client_ip=request.remote_addr)
        return jsonify({
            'success': False,
            'error': {
                'code': 'CSRF_ERROR',
                'message': 'Invalid or missing CSRF token'
            }
        }), 403
    
    return None  # Continue to route handler


# =============================================================================
# DECORATORS
# =============================================================================

def require_database(f):
    """Decorator to require database availability."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DATABASE_AVAILABLE:
            # v3.0.101 ISSUE-004: Standardized error response
            return jsonify({
                'success': False,
                'error': {
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'Database functionality not available. Install required packages.',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 501
        return f(*args, **kwargs)
    return decorated


def handle_errors(f):
    """Decorator for consistent error handling.
    
    v3.0.101 ISSUE-004: Updated to use standardized error response format.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 400
        except ProcessingError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PROCESSING_ERROR',
                    'message': str(e),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An internal error occurred',
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            }), 500
    return decorated


# =============================================================================
# CAPABILITY CHECK ENDPOINT
# =============================================================================

@api_ext.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Return available capabilities.
    
    Returns comprehensive capability information for frontend feature detection.
    Schema: { success: bool, data: { version: str, capabilities: {...} } }
    """
    from pathlib import Path
    import json
    
    # Core capabilities
    capabilities = {
        # Export capabilities (for UI button states)
        'database': DATABASE_AVAILABLE,
        'export': EXPORT_AVAILABLE,
        'excel_export': EXCEL_AVAILABLE,
        'pdf_export': PDF_AVAILABLE,
        'role_analyzer': ROLE_ANALYZER_AVAILABLE,
        # Feature capabilities
        'roles_graph': DATABASE_AVAILABLE,
        'scan_history': DATABASE_AVAILABLE,
        'scan_profiles': DATABASE_AVAILABLE,
        'role_aggregation': DATABASE_AVAILABLE,
        'role_dictionary': DATABASE_AVAILABLE,
        'shareable_dictionary': DATABASE_AVAILABLE,
        'tracked_changes': True,
        'raci_matrix': True,
        'export_word': True,
        'export_csv': True,
        'export_json': True
    }
    
    # Add PDF capabilities
    try:
        from pdf_extractor_v2 import get_pdf_capabilities, is_pdf_available
        pdf_caps = get_pdf_capabilities()
        capabilities['pdf_support'] = is_pdf_available()
        capabilities['pdf_library'] = pdf_caps.get('library')
        capabilities['pdf_features'] = pdf_caps.get('features', {})
    except ImportError:
        try:
            from pdf_extractor import is_pdf_available, get_pdf_library
            capabilities['pdf_support'] = is_pdf_available()
            capabilities['pdf_library'] = get_pdf_library()
            capabilities['pdf_features'] = {
                'quality_detection': False,
                'multi_column': False,
                'table_extraction': True,
                'metadata': True
            }
        except ImportError:
            capabilities['pdf_support'] = False
            capabilities['pdf_library'] = None
            capabilities['pdf_features'] = {}
    
    # Try to load from version.json for any overrides
    try:
        version_file = Path(__file__).parent / 'version.json'
        if version_file.exists():
            with open(version_file, encoding='utf-8') as f:
                version_data = json.load(f)
                if 'capabilities' in version_data:
                    capabilities.update(version_data['capabilities'])
    except Exception:
        pass  # Use defaults if version.json unavailable
    
    return jsonify({
        'success': True,
        'data': {
            'version': __version__,
            'capabilities': capabilities
        }
    })


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@api_ext.route('/export/excel', methods=['POST'])
@handle_errors
def export_excel():
    """Export analysis results to Excel."""
    if not EXPORT_AVAILABLE or not EXCEL_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Excel export not available. Install openpyxl: pip install openpyxl'
        }), 501
    
    data = request.get_json() or {}
    results = data.get('results', {})
    options = data.get('options', {})
    
    if not results:
        raise ValidationError("No results provided for export")
    
    exporter = ExcelExporter()
    excel_bytes = exporter.export(
        results,
        include_charts=options.get('include_charts', True),
        include_roles=options.get('include_roles', True),
        include_readability=options.get('include_readability', True)
    )
    
    filename = options.get('filename', f'techwriter_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    
    return send_file(
        io.BytesIO(excel_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# v5.9.4: CSV, PDF, and JSON export routes moved to routes/review_routes.py
# with enhanced filtering, Fix Assistant integration, and AEGIS-branded reports.
# The old generic routes below are disabled to avoid conflicts.
#
# @api_ext.route('/export/csv', methods=['POST']) -> review_bp /api/export/csv
# @api_ext.route('/export/pdf', methods=['POST']) -> review_bp /api/export/pdf
# @api_ext.route('/export/json', methods=['POST']) -> review_bp /api/export/json


@api_ext.route('/export/compliance-matrix', methods=['POST'])
@handle_errors
def export_compliance_matrix():
    """Generate compliance matrix mapping issues to standards."""
    if not EXPORT_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Export module not available'
        }), 501
    
    data = request.get_json() or {}
    issues = data.get('issues', [])
    standard = data.get('standard')
    
    matrix = ComplianceMatrixExporter.generate_matrix(issues, standard)
    
    return jsonify({
        'success': True,
        'data': matrix
    })


# =============================================================================
# ROLE ANALYSIS ENDPOINTS
# =============================================================================

@api_ext.route('/roles/analyze', methods=['POST'])
@handle_errors
def analyze_roles():
    """Analyze role relationships for network visualization."""
    if not ROLE_ANALYZER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Role analyzer not available'
        }), 501
    
    data = request.get_json() or {}
    text = data.get('text', '')
    extracted_roles = data.get('roles', {})
    
    if not text and not extracted_roles:
        raise ValidationError("No text or roles provided for analysis")
    
    report = generate_role_report(text, extracted_roles)
    
    return jsonify({
        'success': True,
        'data': report
    })


@api_ext.route('/roles/network', methods=['POST'])
@handle_errors
def get_role_network():
    """Get role network data for D3.js visualization."""
    if not ROLE_ANALYZER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Role analyzer not available'
        }), 501
    
    data = request.get_json() or {}
    text = data.get('text', '')
    extracted_roles = data.get('roles', {})
    
    analyzer = RoleRelationshipAnalyzer(extracted_roles)
    if text:
        analyzer.analyze_text(text)
    
    network_data = analyzer.get_network_data()
    
    return jsonify({
        'success': True,
        'data': network_data
    })


@api_ext.route('/roles/summary', methods=['POST'])
@handle_errors
def get_role_summary():
    """Get role summary with relationship counts."""
    if not ROLE_ANALYZER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Role analyzer not available'
        }), 501
    
    data = request.get_json() or {}
    text = data.get('text', '')
    extracted_roles = data.get('roles', {})
    
    analyzer = RoleRelationshipAnalyzer(extracted_roles)
    if text:
        analyzer.analyze_text(text)
    
    summary = analyzer.get_role_summary()
    
    return jsonify({
        'success': True,
        'data': summary
    })


# =============================================================================
# DATABASE / HISTORY ENDPOINTS
# =============================================================================

@api_ext.route('/history/documents', methods=['GET'])
@require_database
@handle_errors
def get_document_history():
    """Get list of all analyzed documents."""
    limit = request.args.get('limit', 50, type=int)
    documents = DocumentRepository.get_all_documents(limit)
    
    return jsonify({
        'success': True,
        'data': documents
    })


@api_ext.route('/history/document/<int:doc_id>', methods=['GET'])
@require_database
@handle_errors
def get_document_analyses(doc_id: int):
    """Get analysis history for a specific document."""
    limit = request.args.get('limit', 10, type=int)
    history = DocumentRepository.get_history(doc_id, limit)
    
    return jsonify({
        'success': True,
        'data': history
    })


@api_ext.route('/history/trends/<int:doc_id>', methods=['GET'])
@require_database
@handle_errors
def get_document_trends(doc_id: int):
    """Get trend data for a document over time."""
    days = request.args.get('days', 30, type=int)
    trends = AnalysisRepository.get_trends(doc_id, days)
    
    return jsonify({
        'success': True,
        'data': trends
    })


@api_ext.route('/history/compare', methods=['POST'])
@require_database
@handle_errors
def compare_analyses():
    """Compare two analysis runs."""
    data = request.get_json() or {}
    analysis_id_1 = data.get('analysis_id_1')
    analysis_id_2 = data.get('analysis_id_2')
    
    if not analysis_id_1 or not analysis_id_2:
        raise ValidationError("Two analysis IDs required for comparison")
    
    comparison = AnalysisRepository.compare_analyses(analysis_id_1, analysis_id_2)
    
    return jsonify({
        'success': True,
        'data': comparison
    })


@api_ext.route('/history/save', methods=['POST'])
@require_database
@handle_errors
def save_analysis():
    """Save analysis results to history."""
    data = request.get_json() or {}
    filepath = data.get('filepath', '')
    filename = data.get('filename', 'unknown')
    results = data.get('results', {})
    duration_ms = data.get('duration_ms', 0)
    
    if not results:
        raise ValidationError("No results provided to save")
    
    # Get or create document
    if filepath and os.path.exists(filepath):
        doc_id = DocumentRepository.get_or_create(filename, filepath)
        doc_info = results.get('document_info', {})
        DocumentRepository.update_stats(
            doc_id,
            doc_info.get('word_count', 0),
            doc_info.get('paragraph_count', 0)
        )
    else:
        # Create with hash of filename
        doc_id = 0  # Placeholder
    
    if doc_id:
        # Save analysis
        analysis_id = AnalysisRepository.save_analysis(doc_id, results, duration_ms)

        # Save roles if available
        if results.get('roles'):
            RoleRepository.save_roles(doc_id, results['roles'])

        # Get analysis count for comparison prompt
        analysis_count = DocumentRepository.get_analysis_count(doc_id)

        return jsonify({
            'success': True,
            'data': {
                'document_id': doc_id,
                'analysis_id': analysis_id,
                'analysis_count': analysis_count
            }
        })
    
    return jsonify({
        'success': False,
        'error': 'Could not save analysis'
    })


# =============================================================================
# BASELINE ENDPOINTS
# =============================================================================

@api_ext.route('/baseline/add', methods=['POST'])
@require_database
@handle_errors
def add_baseline():
    """Add an issue to the baseline (suppress it)."""
    data = request.get_json() or {}
    doc_id = data.get('document_id')
    issue = data.get('issue', {})
    status = data.get('status', 'accepted')
    reason = data.get('reason', '')
    created_by = data.get('created_by', '')
    
    if not doc_id or not issue:
        raise ValidationError("Document ID and issue required")
    
    success = BaselineRepository.add_baseline(doc_id, issue, status, reason, created_by)
    
    return jsonify({
        'success': success,
        'message': 'Issue added to baseline' if success else 'Issue already in baseline'
    })


@api_ext.route('/baseline/remove', methods=['POST'])
@require_database
@handle_errors
def remove_baseline():
    """Remove an issue from the baseline."""
    data = request.get_json() or {}
    doc_id = data.get('document_id')
    issue = data.get('issue', {})
    
    if not doc_id or not issue:
        raise ValidationError("Document ID and issue required")
    
    success = BaselineRepository.remove_baseline(doc_id, issue)
    
    return jsonify({
        'success': success,
        'message': 'Issue removed from baseline' if success else 'Issue not found in baseline'
    })


@api_ext.route('/baseline/list/<int:doc_id>', methods=['GET'])
@require_database
@handle_errors
def list_baselines(doc_id: int):
    """Get all baselined issues for a document."""
    baselines = BaselineRepository.get_baselines(doc_id)
    
    return jsonify({
        'success': True,
        'data': baselines
    })


@api_ext.route('/baseline/filter', methods=['POST'])
@require_database
@handle_errors
def filter_baselined():
    """Filter out baselined issues from a list."""
    data = request.get_json() or {}
    doc_id = data.get('document_id')
    issues = data.get('issues', [])
    
    if not doc_id:
        raise ValidationError("Document ID required")
    
    filtered = BaselineRepository.filter_baselined(doc_id, issues)
    
    return jsonify({
        'success': True,
        'data': {
            'issues': filtered,
            'original_count': len(issues),
            'filtered_count': len(filtered),
            'baselined_count': len(issues) - len(filtered)
        }
    })


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@api_ext.route('/userconfig', methods=['GET'])
@require_database
@handle_errors
def get_config():
    """Get all user configurations.
    
    Note: This uses /api/userconfig to avoid collision with 
    /api/config/sharing handled by app.py.
    """
    config = ConfigRepository.get_all()
    return jsonify({
        'success': True,
        'data': config
    })


@api_ext.route('/userconfig/<key>', methods=['GET'])
@require_database
@handle_errors
def get_config_value(key: str):
    """Get a specific user configuration value."""
    value = ConfigRepository.get(key)
    return jsonify({
        'success': True,
        'data': {key: value}
    })


@api_ext.route('/userconfig', methods=['POST'])
@require_database
@handle_errors
def set_config():
    """Set user configuration values."""
    data = request.get_json() or {}
    
    for key, value in data.items():
        ConfigRepository.set(key, value)
    
    return jsonify({
        'success': True,
        'message': f'Updated {len(data)} configuration(s)'
    })


# =============================================================================
# CUSTOM WORD LIST ENDPOINTS
# =============================================================================

@api_ext.route('/words/<list_type>', methods=['GET'])
@require_database
@handle_errors
def get_word_list(list_type: str):
    """Get custom word list (acronyms, forbidden, etc.)."""
    words = CustomWordRepository.get_words(list_type)
    return jsonify({
        'success': True,
        'data': words
    })


@api_ext.route('/words/<list_type>', methods=['POST'])
@require_database
@handle_errors
def add_word(list_type: str):
    """Add word to custom list."""
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    definition = data.get('definition', '')
    
    if not word:
        raise ValidationError("Word is required")
    
    CustomWordRepository.add_word(list_type, word, definition)
    
    return jsonify({
        'success': True,
        'message': f'Added "{word}" to {list_type} list'
    })


@api_ext.route('/words/<list_type>/<word>', methods=['DELETE'])
@require_database
@handle_errors
def remove_word(list_type: str, word: str):
    """Remove word from custom list."""
    CustomWordRepository.remove_word(list_type, word)
    
    return jsonify({
        'success': True,
        'message': f'Removed "{word}" from {list_type} list'
    })


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@api_ext.route('/analytics/summary', methods=['POST'])
@handle_errors
def get_analytics_summary():
    """Get analytics summary for results."""
    data = request.get_json() or {}
    results = data.get('results', {})
    
    if not results:
        raise ValidationError("No results provided")
    
    issues = results.get('issues', [])
    
    # Calculate analytics
    by_severity = defaultdict(int)
    by_category = defaultdict(int)
    by_severity_category = defaultdict(lambda: defaultdict(int))
    
    for issue in issues:
        sev = issue.get('severity', 'Info')
        cat = issue.get('category', 'Other')
        by_severity[sev] += 1
        by_category[cat] += 1
        by_severity_category[sev][cat] += 1
    
    # Top issues by frequency
    message_counts = defaultdict(int)
    for issue in issues:
        msg = issue.get('message', '')[:50]
        message_counts[msg] += 1
    
    top_issues = sorted(message_counts.items(), key=lambda x: -x[1])[:10]
    
    return jsonify({
        'success': True,
        'data': {
            'total_issues': len(issues),
            'by_severity': dict(by_severity),
            'by_category': dict(by_category),
            'severity_category_matrix': {k: dict(v) for k, v in by_severity_category.items()},
            'top_issues': [{'message': m, 'count': c} for m, c in top_issues],
            'score': results.get('score', 100),
            'grade': results.get('grade', 'A')
        }
    })


@api_ext.route('/analytics/trends', methods=['POST'])
@handle_errors
def get_analytics_trends():
    """Get trend data from multiple analysis runs (in-memory)."""
    data = request.get_json() or {}
    history = data.get('history', [])  # List of past results
    
    if not history:
        return jsonify({
            'success': True,
            'data': {
                'dates': [],
                'scores': [],
                'issue_counts': []
            }
        })
    
    dates = []
    scores = []
    issue_counts = []
    
    for entry in history:
        dates.append(entry.get('date', ''))
        scores.append(entry.get('score', 100))
        issue_counts.append(entry.get('issue_count', 0))
    
    return jsonify({
        'success': True,
        'data': {
            'dates': dates,
            'scores': scores,
            'issue_counts': issue_counts
        }
    })


# =============================================================================
# BATCH PROCESSING ENDPOINT
# =============================================================================

@api_ext.route('/batch/status', methods=['GET'])
@handle_errors
def batch_status():
    """Get batch processing status (placeholder for future implementation)."""
    return jsonify({
        'success': True,
        'data': {
            'available': False,
            'message': 'Batch processing coming in future release'
        }
    })


# =============================================================================
# REGISTER BLUEPRINT FUNCTION
# =============================================================================

def register_api_extensions(app):
    """Register API extensions blueprint with Flask app."""
    app.register_blueprint(api_ext)
    logger.info("API extensions registered", 
                database=DATABASE_AVAILABLE,
                export=EXPORT_AVAILABLE,
                role_analyzer=ROLE_ANALYZER_AVAILABLE)
