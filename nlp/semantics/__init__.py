"""
Semantic Analysis for AEGIS
======================================
Provides terminology consistency checking via WordNet.

Features:
- Synonym detection
- Semantic similarity calculation
- Terminology consistency checking
- Synonym group identification

Requires: pip install nltk
Data: python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
"""

__version__ = "1.0.0"

# Lazy imports
_analyzer = None


def get_analyzer():
    """Get the shared SemanticAnalyzer instance (lazy loaded)."""
    global _analyzer
    if _analyzer is None:
        from .wordnet import SemanticAnalyzer
        _analyzer = SemanticAnalyzer()
    return _analyzer


def is_available() -> bool:
    """Check if semantic analysis is available."""
    try:
        analyzer = get_analyzer()
        return analyzer.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get semantic analysis integration status."""
    try:
        analyzer = get_analyzer()
        return analyzer.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': f"nltk not installed: {e}",
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
        }


def get_synonyms(word: str):
    """
    Get synonyms for a word.

    Args:
        word: Word to find synonyms for

    Returns:
        Set of synonym strings
    """
    analyzer = get_analyzer()
    return analyzer.get_synonyms(word)


def similarity(word1: str, word2: str) -> float:
    """
    Calculate semantic similarity between two words.

    Args:
        word1: First word
        word2: Second word

    Returns:
        Similarity score 0.0 to 1.0
    """
    analyzer = get_analyzer()
    return analyzer.similarity(word1, word2)


def get_checker():
    """Get the TerminologyConsistencyChecker class."""
    from .checker import TerminologyConsistencyChecker
    return TerminologyConsistencyChecker
