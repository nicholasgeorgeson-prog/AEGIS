"""
Style Checking for AEGIS
===================================
Provides professional editorial style rules from Proselint.

Features:
- Editorial style rules from Strunk & White, Garner, etc.
- Cliché detection
- Jargon patterns
- Redundancy detection
- Weasel word detection

Requires: pip install proselint
"""

__version__ = "1.0.0"

# Lazy imports
_wrapper = None


def get_wrapper():
    """Get the shared ProselintWrapper instance (lazy loaded)."""
    global _wrapper
    if _wrapper is None:
        from .proselint import ProselintWrapper
        _wrapper = ProselintWrapper()
    return _wrapper


def is_available() -> bool:
    """Check if style checking is available."""
    try:
        wrapper = get_wrapper()
        return wrapper.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get style checking integration status."""
    try:
        wrapper = get_wrapper()
        return wrapper.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': f"proselint not installed: {e}",
            'checks_available': []
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'checks_available': []
        }


def check(text: str):
    """
    Check text for style issues.

    Args:
        text: Text to check

    Returns:
        List of style issues
    """
    wrapper = get_wrapper()
    return wrapper.check(text)


def get_checker():
    """Get the StyleChecker class."""
    from .checker import StyleChecker
    return StyleChecker
