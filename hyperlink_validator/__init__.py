"""
Hyperlink Validator Module
==========================
Standalone hyperlink validation feature for AEGIS.

This module provides a standalone UI for validating URLs independently
of document review, with support for multiple validation modes:
- offline: Format validation only
- validator: Python requests with optional Windows SSO
- ps1_validator: PowerShell HyperlinkValidator.ps1 script

Features (v2.1.0):
- URL validation with DNS, SSL, soft-404 detection
- Link type classification (web, mailto, file, UNC, bookmark, cross-ref)
- Mailto RFC 5322 validation
- File and network path validation
- URL typo and TLD typo detection
- Cross-reference validation (Section, Table, Figure, Appendix)
- Internal bookmark validation
- DOCX hyperlink extraction and validation
- Excel (.xlsx, .xls) hyperlink extraction and validation
- Exclusion rules with pattern matching

Version: reads from version.json (module v2.1)
"""

__version__ = "2.1.0"  # module version
__author__ = "AEGIS"

from .models import (
    ValidationRequest,
    ValidationResult,
    ValidationSummary,
    ValidationRun,
    ValidationStatus,
    ValidationMode,
    ScanDepth,
    LinkType,
    ExclusionRule,
    # Validation functions
    classify_link_type,
    validate_url_format,
    validate_mailto,
    validate_file_path,
    validate_network_path,
    detect_url_typos,
    validate_cross_reference,
    validate_internal_bookmark,
    categorize_domain,
    parse_url_list
)

from .validator import (
    StandaloneHyperlinkValidator,
    validate_urls,
    validate_any_link,
    validate_docx_links,
    check_dns_resolution,
    check_ssl_certificate,
    detect_soft_404,
    detect_suspicious_url,
    DOCX_EXTRACTION_AVAILABLE
)

# DOCX extractor (optional)
try:
    from .docx_extractor import (
        DocxExtractor,
        extract_docx_links,
        get_urls_from_docx,
        ExtractedLink,
        DocumentStructure,
        DocxExtractionResult
    )
    _docx_exports = [
        'DocxExtractor',
        'extract_docx_links',
        'get_urls_from_docx',
        'ExtractedLink',
        'DocumentStructure',
        'DocxExtractionResult'
    ]
except ImportError:
    _docx_exports = []

# Excel extractor (optional - requires openpyxl)
try:
    from .excel_extractor import (
        ExcelExtractor,
        extract_excel_links,
        get_urls_from_excel,
        is_excel_available,
        ExtractedExcelLink,
        ExcelExtractionResult,
        SheetSummary,
        LinkSource,
        OPENPYXL_AVAILABLE
    )
    EXCEL_EXTRACTION_AVAILABLE = OPENPYXL_AVAILABLE
    _excel_exports = [
        'ExcelExtractor',
        'extract_excel_links',
        'get_urls_from_excel',
        'is_excel_available',
        'ExtractedExcelLink',
        'ExcelExtractionResult',
        'SheetSummary',
        'LinkSource',
        'EXCEL_EXTRACTION_AVAILABLE'
    ]
except ImportError:
    EXCEL_EXTRACTION_AVAILABLE = False
    _excel_exports = ['EXCEL_EXTRACTION_AVAILABLE']

__all__ = [
    # Models
    'ValidationRequest',
    'ValidationResult',
    'ValidationSummary',
    'ValidationRun',
    'ValidationStatus',
    'ValidationMode',
    'ScanDepth',
    'LinkType',
    'ExclusionRule',
    # Validation functions
    'classify_link_type',
    'validate_url_format',
    'validate_mailto',
    'validate_file_path',
    'validate_network_path',
    'detect_url_typos',
    'validate_cross_reference',
    'validate_internal_bookmark',
    'categorize_domain',
    'parse_url_list',
    # Validator
    'StandaloneHyperlinkValidator',
    'validate_urls',
    'validate_any_link',
    'validate_docx_links',
    'check_dns_resolution',
    'check_ssl_certificate',
    'detect_soft_404',
    'detect_suspicious_url',
    'DOCX_EXTRACTION_AVAILABLE',
    # Version
    '__version__'
] + _docx_exports + _excel_exports
