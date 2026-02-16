"""
AEGIS NLP Enhancement Package
=========================================
Version: 1.0.0
Date: 2026-02-01

Provides advanced NLP capabilities through modular integrations:
- spaCy: Linguistic analysis, NER, dependency parsing
- LanguageTool: Comprehensive grammar checking (3000+ rules)
- SymSpell/Enchant: Fast spelling with domain dictionaries
- Textstat: Enhanced readability metrics
- Proselint: Professional style checking
- Pattern.en: Verb tense analysis
- WordNet: Semantic terminology consistency

All integrations support air-gapped operation after initial setup.
Uses lazy loading - modules only import when accessed.
"""

__version__ = "1.0.0"
__author__ = "AEGIS"

# Lazy loading implementation
# Modules are only imported when first accessed

_MODULES = {
    'spacy': 'nlp.spacy',
    'languagetool': 'nlp.languagetool',
    'spelling': 'nlp.spelling',
    'readability': 'nlp.readability',
    'style': 'nlp.style',
    'verbs': 'nlp.verbs',
    'semantics': 'nlp.semantics',
}

_loaded_modules = {}


def __getattr__(name):
    """Lazy load submodules on first access."""
    if name in _MODULES:
        if name not in _loaded_modules:
            import importlib
            try:
                _loaded_modules[name] = importlib.import_module(_MODULES[name])
            except ImportError as e:
                raise ImportError(
                    f"NLP module '{name}' not available. "
                    f"Install dependencies with: pip install -r requirements-nlp.txt"
                ) from e
        return _loaded_modules[name]
    raise AttributeError(f"module 'nlp' has no attribute '{name}'")


def __dir__():
    """List available submodules."""
    return list(_MODULES.keys()) + ['config', 'base', 'get_status', 'get_available_checkers']


def get_status():
    """
    Get status of all NLP integrations.

    Returns dict with availability and version info for each module.
    """
    from . import config
    status = {
        'version': __version__,
        'modules': {}
    }

    for name in _MODULES:
        module_status = {
            'enabled': config.is_enabled(name),
            'available': False,
            'version': None,
            'error': None
        }

        if config.is_enabled(name):
            try:
                mod = __getattr__(name)
                module_status['available'] = True
                module_status['version'] = getattr(mod, '__version__', 'unknown')
            except ImportError as e:
                module_status['error'] = str(e)

        status['modules'][name] = module_status

    return status


def get_available_checkers():
    """
    Get list of all available NLP-enhanced checkers.

    Returns list of checker classes that can be instantiated.
    """
    from . import config
    checkers = []

    # spaCy checkers
    if config.is_enabled('spacy'):
        try:
            from .spacy.checkers import (
                EnhancedSubjectVerbChecker,
                EnhancedDanglingModifierChecker,
                SentenceComplexityChecker
            )
            checkers.extend([
                EnhancedSubjectVerbChecker,
                EnhancedDanglingModifierChecker,
                SentenceComplexityChecker
            ])
        except ImportError:
            pass

    # LanguageTool checker
    if config.is_enabled('languagetool'):
        try:
            from .languagetool.checker import ComprehensiveGrammarChecker
            checkers.append(ComprehensiveGrammarChecker)
        except ImportError:
            pass

    # Spelling checker
    if config.is_enabled('spelling'):
        try:
            from .spelling.checker import EnhancedSpellingChecker
            checkers.append(EnhancedSpellingChecker)
        except ImportError:
            pass

    # Style checker
    if config.is_enabled('style'):
        try:
            from .style.checker import StyleChecker
            checkers.append(StyleChecker)
        except ImportError:
            pass

    # Verb/tense checker
    if config.is_enabled('verbs'):
        try:
            from .verbs.checker import TenseConsistencyChecker
            checkers.append(TenseConsistencyChecker)
        except ImportError:
            pass

    # Semantics checker
    if config.is_enabled('semantics'):
        try:
            from .semantics.checker import TerminologyConsistencyChecker
            checkers.append(TerminologyConsistencyChecker)
        except ImportError:
            pass

    return checkers
