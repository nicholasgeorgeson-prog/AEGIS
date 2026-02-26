"""
Configuration and System Endpoints Blueprint.
=============================================
v4.7.0: Extracted from app.py to support blueprint architecture.

Handles:
- API configuration management (/api/config, /api/config/acronyms, /api/config/hyperlinks)
- Style presets (/api/presets/*)
- NLP configuration (/api/nlp/*)
- Analyzer management (/api/analyzers/*)
- System health and diagnostics (/api/health, /api/version, /api/ready)
- Asset validation (/api/health/assets)
- PDF extraction capabilities (/api/docling/*, /api/extraction/*)
"""
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict

from flask import request, jsonify, session, g, Blueprint

from routes._shared import (
    require_csrf,
    handle_api_errors,
    api_error_response,
    config,
    logger,
    get_engine,
    VERSION,
    ValidationError
)
import routes._shared as _shared

from config_logging import verify_csrf_token, APP_NAME, get_version, log_production_error, ProcessingError

# Lazy imports for optional modules
try:
    from core import AEGISEngine
except ImportError:
    AEGISEngine = None

try:
    from diagnostic_export import DiagnosticCollector, get_ai_troubleshoot
except ImportError:
    DiagnosticCollector = None
    get_ai_troubleshoot = None

# Create blueprint
config_bp = Blueprint('config', __name__)

# Application start time for uptime tracking
_APP_START_TIME = time.time()


def _get_default_user_config() -> Dict:
    """Get default user configuration."""
    return {
        'reviewer_name': 'AEGIS',
        'default_checks': {
            'check_acronyms': True,
            'check_passive_voice': True,
            'check_weak_language': True,
            'check_wordy_phrases': True,
            'check_nominalization': True,
            'check_jargon': True,
            'check_ambiguous_pronouns': True,
            'check_requirements_language': True,
            'check_gender_language': True,
            'check_punctuation': True,
            'check_sentence_length': True,
            'check_repeated_words': True,
            'check_capitalization': True,
            'check_contractions': True,
            'check_references': True,
            'check_document_structure': True,
            'check_tables_figures': True,
            'check_track_changes': True,
            'check_consistency': True,
            'check_lists': True
        }
    }


@config_bp.route('/api/config', methods=['GET', 'POST'])
@handle_api_errors
def api_config():
    """Get or update user configuration.

    Response envelope standardized to { success, data } for consistency.

    POST accepts user preferences including:
    - reviewer_name (string)
    - max_sentence_length (number)
    - passive_voice_threshold (number/string)
    - essentials_mode (boolean)
    - page_size (number)
    - show_charts (boolean)
    - compact_mode (boolean)
    - auto_review (boolean)
    - And any other top-level settings
    """
    config_file = config.base_dir / 'config.json'
    if request.method == 'GET':
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.exception(f'Failed to read config: {e}')
                user_config = _get_default_user_config()
        else:
            user_config = _get_default_user_config()
        return jsonify({'success': True, 'data': user_config})
    else:
        if config.csrf_enabled:
            token = request.headers.get('X-CSRF-Token')
            if not token or not verify_csrf_token(token, session.get('csrf_token', '')):
                return (jsonify({'success': False, 'error': {'code': 'CSRF_ERROR', 'message': 'Invalid CSRF token'}}), 403)
        if config.auth_enabled:
            groups = getattr(g, 'authenticated_groups', [])
            if 'admin' not in groups and 'administrators' not in groups and (config.auth_provider!= 'api_key'):
                return (jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Admin access required'}}), 403)
        data = request.get_json() or {}
        current = _get_default_user_config()
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass

        # Normalize user preferences from camelCase (JavaScript) to snake_case (Python convention)
        normalized_data = {}
        for key, value in data.items():
            # Map common camelCase settings to normalized form
            key_mapping = {
                'autoReview': 'auto_review',
                'reviewerName': 'reviewer_name',
                'maxSentenceLength': 'max_sentence_length',
                'passiveThreshold': 'passive_voice_threshold',
                'essentialsMode': 'essentials_mode',
                'pageSize': 'page_size',
                'showCharts': 'show_charts',
                'compactMode': 'compact_mode',
                'learningEnabled': 'learning_enabled',
            }
            normalized_key = key_mapping.get(key, key)
            normalized_data[normalized_key] = value

        # Log what changed (for troubleshooting)
        changes = {}
        for key, new_val in normalized_data.items():
            old_val = current.get(key)
            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val,
                    'type': type(new_val).__name__
                }

        current.update(normalized_data)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2)
            # Log the configuration change with details
            if changes:
                logger.info(
                    'Configuration updated',
                    changed_keys=list(changes.keys()),
                    changes=changes,
                    user_agent=request.headers.get('User-Agent', 'unknown')[:100]
                )
            else:
                logger.debug('Configuration POST called but no changes detected')
        except IOError as e:
            logger.exception(f'Failed to write config: {e}')
            raise ProcessingError('Failed to save configuration')
        return jsonify({'success': True})
@config_bp.route('/api/presets', methods=['GET'])
@handle_api_errors
def api_presets_list():
    """List available style guide presets.

    v3.4.1: Added for style preset support.

    Returns:
        List of available presets with metadata
    """
    try:
        from style_presets import list_presets
        presets = list_presets()
        return jsonify({'success': True, 'data': presets})
    except ImportError:
        return (jsonify({'success': False, 'error': {'code': 'MODULE_NOT_FOUND', 'message': 'Style presets module not available'}}), 500)
@config_bp.route('/api/presets/<preset_name>', methods=['GET'])
@handle_api_errors
def api_preset_get(preset_name):
    """Get a specific style preset configuration.

    v3.4.1: Added for style preset support.

    Args:
        preset_name: Name of the preset (microsoft, google, plain_language, etc.)

    Returns:
        Preset configuration with checker settings
    """
    try:
        from style_presets import get_preset
        preset = get_preset(preset_name)
        if preset:
            return jsonify({'success': True, 'data': preset.to_dict()})
        else:
            return (jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Preset \'{preset_name}\' not found'}}), 404)
    except ImportError:
        return (jsonify({'success': False, 'error': {'code': 'MODULE_NOT_FOUND', 'message': 'Style presets module not available'}}), 500)
@config_bp.route('/api/presets/<preset_name>/apply', methods=['POST'])
@require_csrf
@handle_api_errors
def api_preset_apply(preset_name):
    """Apply a style preset with optional custom overrides.

    v3.4.1: Added for style preset support.

    Args:
        preset_name: Name of the preset to apply

    Request body (optional):
        {
            \"custom_overrides\": {\"check_passive_voice\": false, ...}
        }

    Returns:
        Applied options dictionary
    """
    try:
        from style_presets import apply_preset
        data = request.get_json() or {}
        custom_overrides = data.get('custom_overrides')
        options = apply_preset(preset_name, custom_overrides)
        if options:
            return jsonify({'success': True, 'data': options})
        else:
            return (jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Preset \'{preset_name}\' not found'}}), 404)
    except ImportError:
        return (jsonify({'success': False, 'error': {'code': 'MODULE_NOT_FOUND', 'message': 'Style presets module not available'}}), 500)
@config_bp.route('/api/auto-fix/preview', methods=['POST'])
@require_csrf
@handle_api_errors
def api_auto_fix_preview():
    """Preview auto-fixes for document issues.

    v3.4.1: Added for auto-fix support.

    Request body:
        {
            \"issues\": [...list of issues from review...]
        }

    Returns:
        List of available fixes with preview
    """
    try:
        from auto_fixer import AutoFixer
        data = request.get_json() or {}
        issues = data.get('issues', [])
        if not issues:
            return (jsonify({'success': False, 'error': {'code': 'NO_ISSUES', 'message': 'No issues provided'}}), 400)
        else:
            fixer = AutoFixer()
            fixable = fixer.get_fixable_issues(issues)
            summary = fixer.get_fix_summary(issues)
            return jsonify({'success': True, 'data': {'fixable_issues': [{'type': i.get('type'), 'message': i.get('message'), 'fix': {'original': i['fix'].original, 'replacement': i['fix'].replacement, 'confidence': i['fix'].confidence, 'reason': i['fix'].reason} if i.get('fix') else None} for i in fixable], 'summary': summary}})
    except ImportError:
        return (jsonify({'success': False, 'error': {'code': 'MODULE_NOT_FOUND', 'message': 'Auto-fixer module not available'}}), 500)
@config_bp.route('/api/config/acronyms', methods=['GET', 'POST'])
@handle_api_errors
def api_config_acronyms():
    """Get or update acronym checker settings.
    
    v3.0.33: Added for strict mode control and transparency.
    
    GET: Returns current acronym settings
    POST: Updates ignore_common_acronyms setting
    """
    config_file = config.base_dir / 'config.json'
    if request.method == 'GET':
        current_settings = {'ignore_common_acronyms': False, 'strict_mode': True}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    acro_settings = user_config.get('acronym_settings', {})
                    ignore_common = acro_settings.get('ignore_common_acronyms', False)
                    current_settings = {'ignore_common_acronyms': ignore_common, 'strict_mode': not ignore_common}
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f'Failed to read acronym config: {e}')
        return jsonify({'success': True, 'data': current_settings})
    else:
        data = request.get_json() or {}
        current = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass
        if 'acronym_settings' not in current:
            current['acronym_settings'] = {}

        old_settings = current['acronym_settings'].copy()

        if 'ignore_common_acronyms' in data:
            current['acronym_settings']['ignore_common_acronyms'] = bool(data['ignore_common_acronyms'])
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2)
            # Log acronym setting changes
            if old_settings != current['acronym_settings']:
                logger.info(
                    'Acronym settings updated',
                    old_settings=old_settings,
                    new_settings=current['acronym_settings']
                )
        except IOError as e:
            logger.exception(f'Failed to write acronym config: {e}')
            raise ProcessingError('Failed to save acronym configuration')
        ignore_common = current['acronym_settings'].get('ignore_common_acronyms', False)
        return jsonify({'success': True, 'data': {'ignore_common_acronyms': ignore_common, 'strict_mode': not ignore_common}})
@config_bp.route('/api/config/hyperlinks', methods=['GET', 'POST'])
@handle_api_errors
def api_config_hyperlinks():
    """Get or update hyperlink validator settings.
    
    v3.0.37: Added for PS1 validator mode control.
    
    GET: Returns current hyperlink settings including validator mode
    POST: Updates validation_mode setting
    
    Modes:
        - \'offline\': Format validation only (default, safest)
        - \'validator\': Network validation using Python requests
        - \'ps1_validator\': PowerShell script validation (Windows)
    """
    config_file = config.base_dir / 'config.json'
    if request.method == 'GET':
        current_settings = {'validation_mode': 'offline', 'ps1_available': False, 'modes': ['offline', 'validator', 'ps1_validator']}
        if _shared.HYPERLINK_HEALTH_AVAILABLE:
            from hyperlink_health import HyperlinkHealthValidator
            validator = HyperlinkHealthValidator(mode='offline')
            ps1_path = validator._find_ps1_validator()
            current_settings['ps1_available'] = ps1_path is not None
            if ps1_path:
                current_settings['ps1_path'] = ps1_path
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    link_settings = user_config.get('hyperlink_settings', {})
                    current_settings['validation_mode'] = link_settings.get('validation_mode', 'offline')
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f'Failed to read hyperlink config: {e}')
        return jsonify({'success': True, 'data': current_settings})
    else:
        data = request.get_json() or {}
        current = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass
        if 'hyperlink_settings' not in current:
            current['hyperlink_settings'] = {}

        old_settings = current['hyperlink_settings'].copy()

        if 'validation_mode' in data:
            mode = data['validation_mode']
            if mode in ['offline', 'validator', 'ps1_validator']:
                current['hyperlink_settings']['validation_mode'] = mode
            else:
                raise ValidationError(f'Invalid validation mode: {mode}. Use \'offline\', \'validator\', or \'ps1_validator\'')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2)
            # Log hyperlink setting changes
            if old_settings != current['hyperlink_settings']:
                logger.info(
                    'Hyperlink validator settings updated',
                    old_settings=old_settings,
                    new_settings=current['hyperlink_settings']
                )
        except IOError as e:
            logger.exception(f'Failed to write hyperlink config: {e}')
            raise ProcessingError('Failed to save hyperlink configuration')
        return jsonify({'success': True, 'data': {'validation_mode': current['hyperlink_settings'].get('validation_mode', 'offline')}})
@config_bp.route('/api/nlp/status', methods=['GET'])
@handle_api_errors
def api_nlp_status():
    """
    Get status of NLP-enhanced checkers.

    Returns availability and version info for each NLP module.
    """
    try:
        engine = AEGISEngine()
        status = engine.get_nlp_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        logger.exception(f'Error getting NLP status: {e}')
        return (jsonify({'success': False, 'error': {'code': 'NLP_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/nlp/checkers', methods=['GET'])
@handle_api_errors
def api_nlp_checkers():
    """
    Get list of available NLP checkers.

    Returns list of checker metadata including name, version, and enabled state.
    """
    try:
        engine = AEGISEngine()
        checkers = engine.get_nlp_checkers()
        return jsonify({'success': True, 'data': checkers})
    except Exception as e:
        logger.exception(f'Error getting NLP checkers: {e}')
        return (jsonify({'success': False, 'error': {'code': 'NLP_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/nlp/config', methods=['GET', 'POST'])
@handle_api_errors
def api_nlp_config():
    """
    Get or update NLP configuration.

    GET: Returns current NLP settings
    POST: Updates NLP settings (requires CSRF token)
    """
    config_file = config.base_dir / 'config.json'
    if request.method == 'GET':
        nlp_settings = {'enabled': True, 'checkers': {}}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    nlp_settings = user_config.get('nlp_settings', nlp_settings)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f'Failed to read NLP config: {e}')
        return jsonify({'success': True, 'data': nlp_settings})
    else:
        if config.csrf_enabled:
            token = request.headers.get('X-CSRF-Token')
            if not token or not verify_csrf_token(token, session.get('csrf_token', '')):
                return (jsonify({'success': False, 'error': {'code': 'CSRF_ERROR', 'message': 'Invalid CSRF token'}}), 403)
        data = request.get_json() or {}
        current = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass
        current['nlp_settings'] = data
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2)
        except IOError as e:
            logger.exception(f'Failed to write NLP config: {e}')
            raise ProcessingError('Failed to save NLP configuration')
        return jsonify({'success': True})
@config_bp.route('/api/analyzers/status', methods=['GET'])
@handle_api_errors
def api_analyzers_status():
    """
    Get status of enhanced analyzers (v3.2.4).

    Returns availability and metrics for:
    - semantic_analysis: Sentence-Transformers semantic similarity
    - enhanced_acronyms: Schwartz-Hearst acronym extraction
    - prose_linting: Vale-style prose quality checking
    - structure_analysis: Document structure validation
    - text_statistics: Comprehensive text metrics
    """
    try:
        from enhanced_analyzers import get_analyzer_status, get_enhanced_analyzers
        status = get_analyzer_status()
        analyzers = get_enhanced_analyzers()
        metrics = {}
        for name, analyzer in analyzers.items():
            if hasattr(analyzer, 'get_metrics'):
                try:
                    metrics[name] = analyzer.get_metrics()
                except Exception:
                    metrics[name] = {'available': False, 'error': 'Failed to get metrics'}
        return jsonify({'success': True, 'data': {'status': status, 'metrics': metrics, 'version': '3.2.4'}})
    except ImportError as e:
        return jsonify({'success': True, 'data': {'status': {}, 'metrics': {}, 'version': '3.2.4', 'note': f'Enhanced analyzers not available: {e}'}})
    except Exception as e:
        logger.exception(f'Error getting analyzer status: {e}')
        return (jsonify({'success': False, 'error': {'code': 'ANALYZER_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/analyzers/semantic/similar', methods=['POST'])
@require_csrf
@handle_api_errors
def api_semantic_similar():
    """
    Find semantically similar sentences in document.

    Request body:
    {
        \"paragraphs\": [\"text1\", \"text2\", ...],
        \"query\": \"search query\",
        \"top_k\": 5
    }

    Returns top_k most similar paragraphs to the query.
    """
    try:
        from enhanced_analyzers import SemanticAnalyzerChecker
        data = request.get_json() or {}
        paragraphs = data.get('paragraphs', [])
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        if not paragraphs or not query:
            return (jsonify({'success': False, 'error': {'code': 'INVALID_INPUT', 'message': 'Requires paragraphs and query'}}), 400)
        else:
            checker = SemanticAnalyzerChecker()
            if not checker.is_available():
                return (jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Semantic analyzer not available'}}), 503)
            else:
                results = checker.find_similar(paragraphs, query, top_k)
                return jsonify({'success': True, 'data': results})
    except Exception as e:
        logger.exception(f'Error in semantic search: {e}')
        return (jsonify({'success': False, 'error': {'code': 'SEMANTIC_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/analyzers/acronyms/extract', methods=['POST'])
@require_csrf
@handle_api_errors
def api_acronyms_extract():
    """
    Extract acronyms from text using Schwartz-Hearst algorithm.

    Request body:
    {
        \"text\": \"document text\"
    }

    Returns extracted acronyms with definitions.
    """
    try:
        from enhanced_analyzers import EnhancedAcronymChecker
        data = request.get_json() or {}
        text = data.get('text', '')
        if not text:
            return (jsonify({'success': False, 'error': {'code': 'INVALID_INPUT', 'message': 'Requires text'}}), 400)
        else:
            checker = EnhancedAcronymChecker()
            if not checker.is_available():
                return (jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Acronym extractor not available'}}), 503)
            else:
                results = checker.extract_all(text)
                return jsonify({'success': True, 'data': results})
    except Exception as e:
        logger.exception(f'Error in acronym extraction: {e}')
        return (jsonify({'success': False, 'error': {'code': 'ACRONYM_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/analyzers/statistics', methods=['POST'])
@require_csrf
@handle_api_errors
def api_text_statistics():
    """
    Get comprehensive text statistics.

    Request body:
    {
        \"text\": \"document text\"
    }

    Returns readability, vocabulary, keywords, and technical writing metrics.
    """
    try:
        from enhanced_analyzers import TextStatisticsChecker
        data = request.get_json() or {}
        text = data.get('text', '')
        if not text:
            return (jsonify({'success': False, 'error': {'code': 'INVALID_INPUT', 'message': 'Requires text'}}), 400)
        else:
            checker = TextStatisticsChecker()
            if not checker.is_available():
                return (jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Text statistics not available'}}), 503)
            else:
                checker.check(paragraphs=[], full_text=text)
                analysis = checker.get_analysis()
                return jsonify({'success': True, 'data': analysis})
    except Exception as e:
        logger.exception(f'Error in text statistics: {e}')
        return (jsonify({'success': False, 'error': {'code': 'STATISTICS_ERROR', 'message': str(e)}}), 500)
@config_bp.route('/api/analyzers/lint', methods=['POST'])
@require_csrf
@handle_api_errors
def api_prose_lint():
    """
    Lint prose for style and quality issues.

    Request body:
    {
        \"text\": \"document text\",
        \"style\": \"technical\"  // or \"government\", \"plain\"
    }

    Returns prose quality issues and suggestions.
    """
    try:
        from prose_linter import ProseLinter
        data = request.get_json() or {}
        text = data.get('text', '')
        style = data.get('style', 'technical')
        if not text:
            return (jsonify({'success': False, 'error': {'code': 'INVALID_INPUT', 'message': 'Requires text'}}), 400)
        else:
            linter = ProseLinter(style=style)
            results = linter.lint_text(text)
            return jsonify({'success': True, 'data': results})
    except ImportError:
        return (jsonify({'success': False, 'error': {'code': 'NOT_AVAILABLE', 'message': 'Prose linter not available'}}), 503)
    except Exception as e:
        logger.exception(f'Error in prose linting: {e}')
        return (jsonify({'success': False, 'error': {'code': 'LINT_ERROR', 'message': str(e)}}), 500)
_cached_checker_count = None


@config_bp.route('/api/capabilities', methods=['GET'])
@handle_api_errors
def capabilities():
    """
    Get server capabilities for UI feature gating (v5.9.40).
    Called during boot by app.js checkCapabilities().
    Returns what export/analysis features are available.
    """
    caps = {
        'excel_export': False,
        'pdf_export': False,
        'docling': False,
        'mammoth': False,
        'spacy': False,
        'proposal_compare': False,
        'sharepoint': False,
    }
    try:
        import openpyxl
        caps['excel_export'] = True
    except ImportError:
        pass
    try:
        from reportlab.lib.pagesizes import letter
        caps['pdf_export'] = True
    except ImportError:
        pass
    try:
        from docling_extractor import DoclingManager
        caps['docling'] = True
    except Exception:
        pass
    try:
        import mammoth
        caps['mammoth'] = True
    except ImportError:
        pass
    try:
        import spacy
        caps['spacy'] = True
    except ImportError:
        pass
    try:
        from proposal_compare.parser import ProposalParser
        caps['proposal_compare'] = True
    except Exception:
        pass
    try:
        from sharepoint_connector import SharePointConnector
        caps['sharepoint'] = True
    except Exception:
        pass

    # v6.2.0: Auth service diagnostics
    auth_info = None
    try:
        from auth_service import AEGISAuthService
        auth_info = AEGISAuthService.get_auth_summary()
    except ImportError:
        pass
    except Exception:
        pass

    return jsonify({
        'success': True,
        'data': {
            'version': get_version(),
            'capabilities': caps,
            'auth': auth_info
        }
    })


@config_bp.route('/api/learning/stats', methods=['GET'])
@handle_api_errors
def learning_stats():
    """
    Get learning pattern statistics across all AEGIS modules (v5.9.50).
    Returns pattern counts for each learner module.
    """
    stats = {}
    # Proposal Compare learner
    try:
        from proposal_compare.pattern_learner import get_pattern_stats
        stats['proposal_compare'] = get_pattern_stats()
    except Exception:
        stats['proposal_compare'] = {'total': 0}
    # Review learner
    try:
        from review_learner import get_pattern_stats as review_stats
        stats['document_review'] = review_stats()
    except Exception:
        stats['document_review'] = {'total': 0}
    # Statement learner
    try:
        from statement_forge.statement_learner import get_pattern_stats as stmt_stats
        stats['statement_forge'] = stmt_stats()
    except Exception:
        stats['statement_forge'] = {'total': 0}
    # Roles learner
    try:
        from roles_learner import get_pattern_stats as roles_stats
        stats['roles'] = roles_stats()
    except Exception:
        stats['roles'] = {'total': 0}
    # HV learner
    try:
        from hyperlink_validator.hv_learner import get_pattern_stats as hv_stats
        stats['hyperlink_validator'] = hv_stats()
    except Exception:
        stats['hyperlink_validator'] = {'total': 0}

    total_patterns = sum(m.get('total', 0) for m in stats.values())

    return jsonify({
        'success': True,
        'data': {
            'modules': stats,
            'total_patterns': total_patterns,
        }
    })


# v5.9.52: Learner module registry for pattern management endpoints
_LEARNER_MODULES = {
    'proposal_compare': {
        'import': 'proposal_compare.pattern_learner',
        'label': 'Proposal Compare',
    },
    'document_review': {
        'import': 'review_learner',
        'label': 'Document Review',
    },
    'statement_forge': {
        'import': 'statement_forge.statement_learner',
        'label': 'Statement Forge',
    },
    'roles': {
        'import': 'roles_learner',
        'label': 'Roles Adjudication',
    },
    'hyperlink_validator': {
        'import': 'hyperlink_validator.hv_learner',
        'label': 'Hyperlink Validator',
    },
}


def _get_learner_module(module_id):
    """Import and return a learner module by ID. Returns (module, error_msg)."""
    info = _LEARNER_MODULES.get(module_id)
    if not info:
        return None, f'Unknown module: {module_id}'
    try:
        import importlib
        mod = importlib.import_module(info['import'])
        return mod, None
    except Exception as e:
        return None, f'Module {module_id} not available: {e}'


@config_bp.route('/api/learning/patterns/<module_id>', methods=['GET'])
@handle_api_errors
def learning_patterns_get(module_id):
    """Get full pattern file contents for a specific learner module (v5.9.52)."""
    mod, err = _get_learner_module(module_id)
    if not mod:
        return api_error_response(err, 404)
    try:
        patterns = mod.load_patterns()
        return jsonify({'success': True, 'data': patterns})
    except Exception as e:
        logger.exception(f'Error loading patterns for {module_id}: {e}')
        return api_error_response(str(e), 500)


@config_bp.route('/api/learning/patterns/<module_id>', methods=['DELETE'])
@require_csrf
@handle_api_errors
def learning_patterns_clear(module_id):
    """Clear pattern file for a specific learner module (v5.9.52)."""
    mod, err = _get_learner_module(module_id)
    if not mod:
        return api_error_response(err, 404)
    try:
        import os
        if hasattr(mod, 'PATTERNS_FILE') and os.path.exists(mod.PATTERNS_FILE):
            os.unlink(mod.PATTERNS_FILE)
        if hasattr(mod, 'reload_learned_patterns'):
            mod.reload_learned_patterns()
        logger.info(f'[AEGIS Learning] Cleared patterns for {module_id}')
        return jsonify({'success': True, 'message': f'Cleared patterns for {_LEARNER_MODULES[module_id]["label"]}'})
    except Exception as e:
        logger.exception(f'Error clearing patterns for {module_id}: {e}')
        return api_error_response(str(e), 500)


@config_bp.route('/api/learning/patterns', methods=['DELETE'])
@require_csrf
@handle_api_errors
def learning_patterns_clear_all():
    """Clear ALL pattern files across all learner modules (v5.9.52)."""
    import os
    cleared = []
    errors = []
    for mid, info in _LEARNER_MODULES.items():
        try:
            mod, err = _get_learner_module(mid)
            if mod and hasattr(mod, 'PATTERNS_FILE') and os.path.exists(mod.PATTERNS_FILE):
                os.unlink(mod.PATTERNS_FILE)
                if hasattr(mod, 'reload_learned_patterns'):
                    mod.reload_learned_patterns()
                cleared.append(info['label'])
        except Exception as e:
            errors.append(f'{info["label"]}: {e}')
    logger.info(f'[AEGIS Learning] Cleared all patterns: {cleared}')
    return jsonify({
        'success': True,
        'message': f'Cleared {len(cleared)} module(s)',
        'cleared': cleared,
        'errors': errors,
    })


@config_bp.route('/api/learning/export/<module_id>', methods=['GET'])
@handle_api_errors
def learning_export_module(module_id):
    """Download pattern file for a specific module as JSON (v5.9.52)."""
    mod, err = _get_learner_module(module_id)
    if not mod:
        return api_error_response(err, 404)
    try:
        patterns = mod.load_patterns()
        from flask import Response
        import json as json_mod
        content = json_mod.dumps(patterns, indent=2, ensure_ascii=False)
        filename = f'aegis_{module_id}_patterns.json'
        return Response(
            content,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.exception(f'Error exporting patterns for {module_id}: {e}')
        return api_error_response(str(e), 500)


@config_bp.route('/api/learning/export', methods=['GET'])
@handle_api_errors
def learning_export_all():
    """Download all pattern files as combined JSON (v5.9.52)."""
    combined = {}
    for mid, info in _LEARNER_MODULES.items():
        try:
            mod, err = _get_learner_module(mid)
            if mod:
                combined[mid] = mod.load_patterns()
            else:
                combined[mid] = {}
        except Exception:
            combined[mid] = {}

    from flask import Response
    import json as json_mod
    content = json_mod.dumps({
        '_export_meta': {
            'tool': 'AEGIS Learning System',
            'version': get_version(),
            'exported': datetime.utcnow().isoformat() + 'Z',
            'modules': list(_LEARNER_MODULES.keys()),
        },
        'modules': combined,
    }, indent=2, ensure_ascii=False)
    return Response(
        content,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename="aegis_all_learning_patterns.json"'}
    )


@config_bp.route('/api/version', methods=['GET'])
@handle_api_errors
def version():
    """Get version information.
    v4.9.9: Uses get_version() for always-fresh reads from version.json.
    v5.9.27: Caches checker count to avoid re-creating AEGISEngine on every call
    (was causing 34-124s delays on startup and subsequent requests).
    """
    global _cached_checker_count
    _ver = get_version()
    checker_count = _cached_checker_count or 0
    if _cached_checker_count is None:
        try:
            engine = AEGISEngine()
            checker_count = len(engine.checkers)
            _cached_checker_count = checker_count
        except Exception as e:
            logger.warning(f'Error getting checker count: {e}')
    resp = jsonify({'app_name': APP_NAME, 'version': _ver, 'app_version': _ver, 'core_version': _ver, 'api_version': '2.0', 'checker_count': checker_count})
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp
@config_bp.route('/api/health', methods=['GET'])
@handle_api_errors
def health():
    """
    Liveness check with diagnostic info (v2.9.4.2 enhanced).
    
    Returns basic health + error counts for quick status assessment.
    """
    health_data = {'status': 'healthy', 'version': get_version(), 'uptime_seconds': round(time.time() - _APP_START_TIME, 1), 'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'}
    if _shared.DIAGNOSTICS_AVAILABLE:
        try:
            collector = DiagnosticCollector.get_instance()
            ai_pkg = get_ai_troubleshoot()
            health_data['diagnostics'] = {'error_count': len(collector.errors), 'warning_count': len(collector.warnings), 'request_count': len(collector.request_log), 'console_error_count': len(ai_pkg.console_errors) if ai_pkg else 0, 'user_action_count': len(ai_pkg.user_actions) if ai_pkg else 0, 'session_id': collector.session_id}
            if collector.errors:
                last_error = collector.errors[(-1)]
                health_data['diagnostics']['last_error_at'] = last_error.timestamp if hasattr(last_error, 'timestamp') else last_error.get('timestamp', 'unknown')
        except Exception as e:
            health_data['diagnostics'] = {'error': str(e)}
        return jsonify(health_data)
    else:
        return jsonify(health_data)
@config_bp.route('/api/ready', methods=['GET'])
@handle_api_errors
def ready():
    """Readiness check - is the application ready to serve requests?"""
    checks = {'temp_dir': config.temp_dir.exists(), 'index_html': (config.base_dir / 'templates' / 'index.html').exists(), 'core_module': True, 'diagnostics': _shared.DIAGNOSTICS_AVAILABLE}
    try:
        from core import AEGISEngine
        checks['core_module'] = True
    except ImportError:
        checks['core_module'] = False
    all_ready = all([checks['temp_dir'], checks['core_module']])
    return (jsonify({'ready': all_ready, 'checks': checks, 'version': get_version(), 'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'}), 200 if all_ready else 503)
@config_bp.route('/api/docling/status', methods=['GET'])
@handle_api_errors
def docling_status():
    """
    Get Docling document extraction status (v3.0.91).
    
    Returns information about:
    - Whether Docling is available
    - Current extraction backend
    - Offline mode configuration
    - Model status
    """
    status = {'available': False, 'backend': 'legacy', 'version': None, 'offline_mode': True, 'offline_ready': False, 'image_processing': False, 'models_path': None, 'pytorch_available': False, 'error': None}
    try:
        from docling_extractor import DoclingExtractor, DoclingManager
        manager_status = DoclingManager.check_installation()
        status['pytorch_available'] = manager_status.get('pytorch_available', False)
        status['available'] = manager_status.get('installed', False)
        status['version'] = manager_status.get('version')
        status['models_path'] = manager_status.get('models_path')
        status['offline_ready'] = manager_status.get('offline_ready', False)
        if status['available']:
            try:
                extractor = DoclingExtractor(fallback_to_legacy=True)
                status['backend'] = extractor.backend_name
                status['available'] = extractor.is_available
                extractor_status = extractor.get_status()
                status['table_mode'] = extractor_status.get('table_mode', 'accurate')
                status['ocr_enabled'] = extractor_status.get('ocr_enabled', False)
            except Exception as e:
                status['error'] = f'Extractor init error: {str(e)}'
                status['backend'] = 'legacy'
    except ImportError as e:
        status['error'] = f'docling_extractor not available: {str(e)}'
        status['backend'] = 'legacy'
    except Exception as e:
        status['error'] = str(e)
    return jsonify(status)
@config_bp.route('/api/extraction/capabilities', methods=['GET'])
@handle_api_errors
def extraction_capabilities():
    """
    Get comprehensive document extraction capabilities (v3.0.91+).
    
    Reports all available extraction methods:
    - PDF extraction (Docling, Camelot, Tabula, pdfplumber)
    - OCR support (Tesseract)
    - NLP enhancements (spaCy, sklearn)
    - Table extraction accuracy estimates
    """
    caps = {'version': '5.9.5', 'pdf': {'docling': False, 'camelot': False, 'tabula': False, 'pdfplumber': False, 'pymupdf': False, 'mammoth': False, 'pymupdf4llm': False}, 'ocr': {'tesseract': False, 'pdf2image': False}, 'nlp': {'spacy': False, 'sklearn': False, 'nltk': False, 'textstat': False, 'sentence_transformers': False, 'languagetool': False}, 'estimated_accuracy': {'table_extraction': 0.7, 'role_detection': 0.75, 'text_extraction': 0.8}, 'recommended_setup': []}
    try:
        from docling_extractor import DoclingManager
        if DoclingManager.check_installation().get('offline_ready'):
            caps['pdf']['docling'] = True
            caps['estimated_accuracy']['table_extraction'] = 0.95
    except Exception:
        pass
    try:
        import camelot
        caps['pdf']['camelot'] = True
        if not caps['pdf']['docling']:
            caps['estimated_accuracy']['table_extraction'] = max(caps['estimated_accuracy']['table_extraction'], 0.88)
    except Exception:
        pass
    try:
        import tabula
        caps['pdf']['tabula'] = True
        if not caps['pdf']['docling'] and (not caps['pdf']['camelot']):
                caps['estimated_accuracy']['table_extraction'] = max(caps['estimated_accuracy']['table_extraction'], 0.8)
    except Exception:
        pass
    try:
        import pdfplumber
        caps['pdf']['pdfplumber'] = True
    except Exception:
        pass
    try:
        import fitz
        caps['pdf']['pymupdf'] = True
        caps['estimated_accuracy']['text_extraction'] = 0.9
    except Exception:
        pass
    # v5.9.5: Added mammoth and pymupdf4llm detection (DOCX/PDF extractors)
    try:
        import mammoth
        caps['pdf']['mammoth'] = True
    except Exception:
        pass
    try:
        import pymupdf4llm
        caps['pdf']['pymupdf4llm'] = True
    except Exception:
        pass
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        caps['ocr']['tesseract'] = True
    except Exception:
        pass
    try:
        from pdf2image import convert_from_path
        caps['ocr']['pdf2image'] = True
    except Exception:
        pass
    try:
        import spacy
        spacy.load('en_core_web_sm')
        caps['nlp']['spacy'] = True
        caps['estimated_accuracy']['role_detection'] = min(caps['estimated_accuracy']['role_detection'] + 0.1, 0.95)
    except Exception:
        pass
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        caps['nlp']['sklearn'] = True
        caps['estimated_accuracy']['role_detection'] = min(caps['estimated_accuracy']['role_detection'] + 0.05, 0.95)
    except Exception:
        pass
    try:
        import nltk
        caps['nlp']['nltk'] = True
    except Exception:
        pass
    try:
        import textstat
        caps['nlp']['textstat'] = True
    except Exception:
        pass
    # v5.9.5: Added sentence-transformers and languagetool detection
    try:
        from sentence_transformers import SentenceTransformer
        caps['nlp']['sentence_transformers'] = True
    except Exception:
        pass
    try:
        import language_tool_python
        caps['nlp']['languagetool'] = True
    except Exception:
        pass
    if not caps['pdf']['docling'] and (not caps['pdf']['camelot']):
            caps['recommended_setup'].append('Install Camelot for better table extraction: pip install camelot-py')
    if not caps['ocr']['tesseract']:
        caps['recommended_setup'].append('Install Tesseract for scanned PDF support')
    if not caps['nlp']['spacy']:
        caps['recommended_setup'].append('Install spaCy for better role detection: pip install spacy && python -m spacy download en_core_web_sm')
    return jsonify(caps)
@config_bp.route('/api/health/assets', methods=['GET'])
@handle_api_errors
def health_assets():
    """
    Verify critical frontend assets exist and are accessible.
    
    Used by installer smoke test to verify complete installation.
    Returns 200 if all critical assets exist, 503 otherwise.
    
    v3.0.30: Added vendor JS files for offline-first UI
    """
    critical_assets = [('templates/index.html', 'index_html'), ('static/css/style.css', 'style_css'), ('static/js/app.js', 'app_js'), ('static/js/twr-loader.js', 'twr_loader_js'), ('static/js/utils/dom.js', 'utils_dom_js'), ('static/js/ui/state.js', 'ui_state_js'), ('static/js/ui/renderers.js', 'ui_renderers_js'), ('static/js/ui/events.js', 'ui_events_js'), ('static/js/ui/modals.js', 'ui_modals_js'), ('static/js/api/client.js', 'api_client_js'), ('static/js/features/roles.js', 'features_roles_js'), ('static/js/features/triage.js', 'features_triage_js'), ('static/js/features/families.js', 'features_families_js'), ('static/js/vendor/lucide.min.js', 'vendor_lucide_js'), ('static/js/vendor/chart.min.js', 'vendor_chart_js'), ('static/js/vendor/d3.v7.min.js', 'vendor_d3_js')]
    checks = {}
    missing = []
    for asset_path, check_name in critical_assets:
        full_path = config.base_dir / asset_path
        exists = full_path.exists()
        checks[check_name] = exists
        if not exists:
            missing.append(asset_path)
    all_present = len(missing) == 0
    response = {'status': 'ok' if all_present else 'missing_assets', 'success': all_present, 'checks': checks, 'version': get_version(), 'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'}
    if missing:
        response['missing'] = missing
    return (jsonify(response), 200 if all_present else 503)


# ═══════════════════════════════════════════════════════════════════════
# DEMO AUDIO GENERATION (v5.9.7 — Voice Narration Feature)
# ═══════════════════════════════════════════════════════════════════════

@config_bp.route('/api/demo/audio/status', methods=['GET'])
@handle_api_errors
def demo_audio_status():
    """Check TTS provider availability and existing audio files."""
    try:
        from demo_audio_generator import get_tts_status, get_demo_scenes_from_js
    except ImportError:
        return jsonify({
            'success': True,
            'providers': {},
            'has_audio': False,
            'scene_count': 0
        })

    status = get_tts_status()
    scenes = get_demo_scenes_from_js()
    scene_count = sum(len(steps) for steps in scenes.values())

    # Check if manifest exists
    manifest_path = config.base_dir / 'static' / 'audio' / 'demo' / 'manifest.json'
    has_audio = manifest_path.exists()
    manifest = None
    if has_audio:
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception:
            pass

    return jsonify({
        'success': True,
        'providers': status,
        'has_audio': has_audio,
        'scene_count': scene_count,
        'sections': list(scenes.keys()),
        'manifest_summary': {
            'provider': manifest.get('provider') if manifest else None,
            'voice': manifest.get('voice') if manifest else None,
            'section_count': len(manifest.get('sections', {})) if manifest else 0
        } if manifest else None
    })


@config_bp.route('/api/demo/audio/generate', methods=['POST'])
@require_csrf
@handle_api_errors
def demo_audio_generate():
    """Generate narration audio files from demo scene text."""
    try:
        from demo_audio_generator import generate_demo_audio, get_demo_scenes_from_js
    except ImportError:
        return api_error_response('Demo audio generator not available', 500)

    data = request.get_json(silent=True) or {}
    voice = data.get('voice', 'en-US-GuyNeural')
    force = data.get('force', False)

    scenes = get_demo_scenes_from_js()
    if not scenes:
        return api_error_response('No demo scenes found in guide-system.js', 404)

    output_dir = str(config.base_dir / 'static' / 'audio' / 'demo')
    result = generate_demo_audio(scenes, output_dir=output_dir, voice=voice, force=force)

    return jsonify({
        'success': result.get('success', False),
        'stats': result.get('stats', {}),
        'error': result.get('error'),
        'provider': result.get('manifest', {}).get('provider')
    })


@config_bp.route('/api/demo/audio/voices', methods=['GET'])
@handle_api_errors
def demo_audio_voices():
    """List available edge-tts voices."""
    voices = {
        'en-US-GuyNeural': {'name': 'Guy (US Male)', 'lang': 'en-US', 'gender': 'male'},
        'en-US-JennyNeural': {'name': 'Jenny (US Female)', 'lang': 'en-US', 'gender': 'female'},
        'en-GB-RyanNeural': {'name': 'Ryan (UK Male)', 'lang': 'en-GB', 'gender': 'male'},
        'en-GB-SoniaNeural': {'name': 'Sonia (UK Female)', 'lang': 'en-GB', 'gender': 'female'},
        'en-AU-WilliamNeural': {'name': 'William (AU Male)', 'lang': 'en-AU', 'gender': 'male'},
        'en-AU-NatashaNeural': {'name': 'Natasha (AU Female)', 'lang': 'en-AU', 'gender': 'female'},
    }
    return jsonify({'success': True, 'voices': voices})
