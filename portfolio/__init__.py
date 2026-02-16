"""
Portfolio Module for AEGIS v3.0.114
==============================================
Visual tile-based dashboard for viewing batch results and document history.

Features:
- Batch groupings with cascade/expand view
- Document preview cards with scores and metrics
- Quick navigation back to main review
- Visual health indicators and trend charts
"""

from .routes import portfolio_blueprint

__all__ = ['portfolio_blueprint']
__version__ = '1.0.0'
