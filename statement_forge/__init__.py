"""Statement Forge Module

v3.0.49: Package initialization for Statement Forge functionality.

This module provides requirement extraction and analysis capabilities
for technical documents. It identifies actionable statements, directives,
and responsibilities from document text.

Components:
- extractor: Core extraction logic for identifying statements
- models: Data models for statements and extraction results  
- routes: Flask blueprint with API endpoints
- export: Export functionality for extracted statements
"""

from typing import List, Dict, Any, Optional

__version__ = "3.0.49"
__all__ = ['extractor', 'models', 'routes', 'export']
