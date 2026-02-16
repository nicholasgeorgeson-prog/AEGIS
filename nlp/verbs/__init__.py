"""
Verb/Tense Analysis for AEGIS
========================================
Provides verb conjugation analysis and tense consistency checking.

Features:
- Verb tense detection (past, present, future)
- Tense consistency checking across paragraphs
- Verb conjugation helpers
- Mood detection

Requires: pip install pattern
Note: pattern library may need: python -c "import pattern.en"
"""

__version__ = "1.0.0"

# Lazy imports
_analyzer = None


def get_analyzer():
    """Get the shared VerbAnalyzer instance (lazy loaded)."""
    global _analyzer
    if _analyzer is None:
        from .pattern_en import VerbAnalyzer
        _analyzer = VerbAnalyzer()
    return _analyzer


def is_available() -> bool:
    """Check if verb analysis is available."""
    try:
        analyzer = get_analyzer()
        return analyzer.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get verb analysis integration status."""
    try:
        analyzer = get_analyzer()
        return analyzer.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': f"pattern library not installed: {e}",
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
        }


def analyze_tenses(text: str):
    """
    Analyze verb tenses in text.

    Args:
        text: Text to analyze

    Returns:
        TenseAnalysis result
    """
    analyzer = get_analyzer()
    return analyzer.analyze_tense_consistency(text)


def get_checker():
    """Get the TenseConsistencyChecker class."""
    from .checker import TenseConsistencyChecker
    return TenseConsistencyChecker
