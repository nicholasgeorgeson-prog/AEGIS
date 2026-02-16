"""
Document Comparison Module v1.0.0
=================================
Side-by-side document comparison with line-level alignment
and word-level diff highlighting.

Features:
- Compare historical scans of the same document
- Line-level alignment with placeholder rows
- Word-level diff highlighting within modified lines
- Issue comparison between scans
- Navigation between changes

Author: AEGIS
"""

from .routes import dc_blueprint
from .differ import DocumentDiffer
from .models import (
    WordChange,
    AlignedRow,
    DiffResult,
    IssueComparison
)

__version__ = "1.0.0"
__all__ = [
    'dc_blueprint',
    'DocumentDiffer',
    'WordChange',
    'AlignedRow',
    'DiffResult',
    'IssueComparison'
]
