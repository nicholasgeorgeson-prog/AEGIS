"""
Spelling Enhancement for AEGIS
==========================================
Provides comprehensive spell checking with domain dictionaries.

Features:
- SymSpell: 500K+ word dictionary, ultra-fast
- PyEnchant: Domain-specific dictionaries
- Combined checker with technical term awareness

Requires: pip install symspellpy pyenchant
"""

__version__ = "1.0.0"

# Lazy imports
_symspell_checker = None
_domain_manager = None


def get_symspell_checker():
    """Get the shared SymSpellChecker instance (lazy loaded)."""
    global _symspell_checker
    if _symspell_checker is None:
        from .symspell import SymSpellChecker
        _symspell_checker = SymSpellChecker()
    return _symspell_checker


def get_domain_manager():
    """Get the shared DomainDictionaryManager instance (lazy loaded)."""
    global _domain_manager
    if _domain_manager is None:
        from .enchant import DomainDictionaryManager
        _domain_manager = DomainDictionaryManager()
    return _domain_manager


def is_available() -> bool:
    """Check if spelling enhancement is available."""
    try:
        checker = get_symspell_checker()
        return checker.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get spelling integration status."""
    status = {
        'available': False,
        'symspell': {'available': False},
        'enchant': {'available': False},
    }

    try:
        symspell = get_symspell_checker()
        status['symspell'] = symspell.get_status()
        status['available'] = symspell.is_available
    except Exception as e:
        status['symspell']['error'] = str(e)

    try:
        domain = get_domain_manager()
        status['enchant'] = domain.get_status()
    except Exception as e:
        status['enchant']['error'] = str(e)

    return status


def get_checker():
    """Get the EnhancedSpellingChecker class."""
    from .checker import EnhancedSpellingChecker
    return EnhancedSpellingChecker
