"""
spaCy Integration for AEGIS
======================================
Provides linguistic analysis capabilities:
- Dependency parsing
- Named Entity Recognition (NER)
- Part-of-speech tagging
- Sentence boundary detection
- Lemmatization

Requires: pip install spacy && python -m spacy download en_core_web_md
"""

__version__ = "1.0.0"

# Lazy imports - only load when accessed
_analyzer = None
_checkers_loaded = False


def get_analyzer():
    """Get the shared SpacyAnalyzer instance (lazy loaded)."""
    global _analyzer
    if _analyzer is None:
        from .analyzer import SpacyAnalyzer
        _analyzer = SpacyAnalyzer()
    return _analyzer


def is_available() -> bool:
    """Check if spaCy is available and model is loaded."""
    try:
        analyzer = get_analyzer()
        return analyzer.is_available
    except ImportError:
        return False


def get_status() -> dict:
    """Get spaCy integration status."""
    try:
        analyzer = get_analyzer()
        return analyzer.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': str(e),
            'model': None,
            'version': None
        }


# Checker classes - imported on demand
def get_checkers():
    """Get all spaCy-based checker classes."""
    from .checkers import (
        EnhancedSubjectVerbChecker,
        EnhancedDanglingModifierChecker,
        SentenceComplexityChecker
    )
    return [
        EnhancedSubjectVerbChecker,
        EnhancedDanglingModifierChecker,
        SentenceComplexityChecker
    ]
