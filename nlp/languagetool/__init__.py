"""
LanguageTool Integration for AEGIS
==============================================
Provides comprehensive grammar checking with 3000+ rules.

Features:
- Grammar and style checking
- Spelling suggestions
- Rule-based corrections
- Local server mode (air-gap compatible)

Requires: pip install language-tool-python
Note: First run downloads LanguageTool JAR (~200MB)
"""

__version__ = "1.0.0"

# Lazy imports - only load when accessed
_client = None


def get_client():
    """Get the shared LanguageToolClient instance (lazy loaded)."""
    global _client
    if _client is None:
        from .client import LanguageToolClient
        _client = LanguageToolClient()
    return _client


def is_available() -> bool:
    """Check if LanguageTool is available and server is running."""
    try:
        client = get_client()
        return client.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get LanguageTool integration status."""
    try:
        client = get_client()
        return client.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': f"language-tool-python not installed: {e}",
            'language': None,
            'version': None
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'language': None,
            'version': None
        }


# Checker class - imported on demand
def get_checker():
    """Get the ComprehensiveGrammarChecker class."""
    from .checker import ComprehensiveGrammarChecker
    return ComprehensiveGrammarChecker
