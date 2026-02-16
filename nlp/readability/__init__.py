"""
Readability Enhancement for AEGIS
=============================================
Provides comprehensive readability analysis with additional metrics.

Features:
- 5 new metrics: Dale-Chall, SMOG, Linsear Write, Coleman-Liau, ARI
- Difficult word identification
- Reading time estimation
- Grade level interpretation
- Improvement recommendations

Requires: pip install textstat
"""

__version__ = "1.0.0"

# Lazy imports
_calculator = None


def get_calculator():
    """Get the shared EnhancedReadabilityCalculator instance (lazy loaded)."""
    global _calculator
    if _calculator is None:
        from .enhanced import EnhancedReadabilityCalculator
        _calculator = EnhancedReadabilityCalculator()
    return _calculator


def is_available() -> bool:
    """Check if readability enhancement is available."""
    try:
        calculator = get_calculator()
        return calculator.is_available
    except ImportError:
        return False
    except Exception:
        return False


def get_status() -> dict:
    """Get readability integration status."""
    try:
        calculator = get_calculator()
        return calculator.get_status()
    except ImportError as e:
        return {
            'available': False,
            'error': f"textstat not installed: {e}",
            'metrics_available': []
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'metrics_available': []
        }


def analyze(text: str):
    """
    Analyze text readability.

    Args:
        text: Text to analyze

    Returns:
        ReadabilityReport with all metrics
    """
    calculator = get_calculator()
    return calculator.analyze(text)


def get_recommendations(text: str):
    """
    Get readability improvement recommendations.

    Args:
        text: Text to analyze

    Returns:
        List of recommendation strings
    """
    calculator = get_calculator()
    report = calculator.analyze(text)
    return calculator.get_recommendations(report)
