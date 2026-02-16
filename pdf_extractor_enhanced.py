"""
Enhanced PDF Extractor v2.0.0
=============================
Date: 2026-02-04

Enhanced PDF extraction with multiple backends:
- pymupdf4llm: Structured markdown output (best for tables, headers)
- pdfplumber: Enhanced table detection
- PyMuPDF (fitz): Fast text extraction (existing)
- Docling: AI-powered extraction (existing)

Author: AEGIS NLP Enhancement Project
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VERSION = '2.0.0'

# Check available libraries
PYMUPDF4LLM_AVAILABLE = False
PDFPLUMBER_AVAILABLE = False
PYMUPDF_AVAILABLE = False

try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    logger.warning("pymupdf4llm not installed. Install with: pip install pymupdf4llm")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    logger.warning("PyMuPDF not installed. Install with: pip install pymupdf")


@dataclass
class PDFExtractionResult:
    """Result from PDF extraction."""
    text: str
    metadata: Dict[str, Any]
    tables: List[Dict[str, Any]]
    structure: Dict[str, Any]  # Headers, sections, etc.
    backend_used: str
    page_count: int
    extraction_quality: float  # 0-1 quality score


class EnhancedPDFExtractor:
    """
    Enhanced PDF extractor with multiple backends.

    Automatically selects the best backend based on document characteristics
    and available libraries.
    """

    VERSION = VERSION

    def __init__(self, preferred_backend: str = 'auto'):
        """
        Initialize the enhanced PDF extractor.

        Args:
            preferred_backend: 'auto', 'pymupdf4llm', 'pdfplumber', 'pymupdf'
        """
        self.preferred_backend = preferred_backend
        self._kerning_fixes = self._load_kerning_fixes()

    def _load_kerning_fixes(self) -> Dict[str, str]:
        """Load kerning fix dictionary."""
        # Import from existing pdf_extractor if available
        try:
            from pdf_extractor import PDFExtractor
            # Get kerning fixes from existing extractor
            extractor = PDFExtractor()
            # Access the fix dictionary (we'll define our own if not accessible)
        except:
            pass

        # Comprehensive kerning fixes for technical documents
        return {
            # Document structure
            'N OTE': 'NOTE', 'W ARNING': 'WARNING', 'C AUTION': 'CAUTION',
            'T ABLE': 'TABLE', 'F IGURE': 'FIGURE', 'S ECTION': 'SECTION',
            'A PPENDIX': 'APPENDIX', 'R EFERENCE': 'REFERENCE',
            'R EQUIREMENT': 'REQUIREMENT', 'S PECIFICATION': 'SPECIFICATION',
            'S YSTEM': 'SYSTEM', 'S OFTWARE': 'SOFTWARE', 'H ARDWARE': 'HARDWARE',
            'I NTERFACE': 'INTERFACE', 'C OMPONENT': 'COMPONENT',
            'V ERIFICATION': 'VERIFICATION', 'V ALIDATION': 'VALIDATION',
            # Abbreviations
            'S W': 'SW', 'H W': 'HW', 'S RS': 'SRS', 'S DD': 'SDD',
            'I CD': 'ICD', 'T RR': 'TRR', 'P DR': 'PDR', 'C DR': 'CDR',
            'T BD': 'TBD', 'T BR': 'TBR', 'N A': 'N/A',
        }

    def extract(self, pdf_path: str, backend: str = None) -> PDFExtractionResult:
        """
        Extract content from PDF using the specified or best backend.

        Args:
            pdf_path: Path to PDF file
            backend: Override backend selection ('auto', 'pymupdf4llm', 'pdfplumber', 'pymupdf')

        Returns:
            PDFExtractionResult with extracted content
        """
        backend = backend or self.preferred_backend

        if backend == 'auto':
            backend = self._select_best_backend(pdf_path)

        if backend == 'pymupdf4llm' and PYMUPDF4LLM_AVAILABLE:
            return self._extract_with_pymupdf4llm(pdf_path)
        elif backend == 'pdfplumber' and PDFPLUMBER_AVAILABLE:
            return self._extract_with_pdfplumber(pdf_path)
        elif PYMUPDF_AVAILABLE:
            return self._extract_with_pymupdf(pdf_path)
        else:
            raise RuntimeError("No PDF extraction backend available")

    def _select_best_backend(self, pdf_path: str) -> str:
        """Select the best backend based on document characteristics."""
        # If pymupdf4llm is available, prefer it for structured output
        if PYMUPDF4LLM_AVAILABLE:
            return 'pymupdf4llm'

        # If document has many tables, use pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    # Check first few pages for tables
                    table_count = 0
                    for i, page in enumerate(pdf.pages[:3]):
                        tables = page.find_tables()
                        table_count += len(tables)
                    if table_count > 0:
                        return 'pdfplumber'
            except:
                pass

        # Default to pymupdf for speed
        if PYMUPDF_AVAILABLE:
            return 'pymupdf'

        raise RuntimeError("No PDF backend available")

    def _extract_with_pymupdf4llm(self, pdf_path: str) -> PDFExtractionResult:
        """Extract using pymupdf4llm for structured markdown output."""
        logger.info(f"Extracting with pymupdf4llm: {pdf_path}")

        try:
            # pymupdf4llm extracts to markdown format
            md_text = pymupdf4llm.to_markdown(pdf_path)

            # Get page count and metadata using PyMuPDF
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            metadata = dict(doc.metadata) if doc.metadata else {}
            doc.close()

            # Parse structure from markdown
            structure = self._parse_markdown_structure(md_text)

            # Extract tables from markdown
            tables = self._extract_tables_from_markdown(md_text)

            # Apply kerning fixes
            text = self._apply_kerning_fixes(md_text)

            # Calculate quality score
            quality = self._calculate_quality(text, tables, structure)

            return PDFExtractionResult(
                text=text,
                metadata=metadata,
                tables=tables,
                structure=structure,
                backend_used='pymupdf4llm',
                page_count=page_count,
                extraction_quality=quality
            )

        except Exception as e:
            logger.error(f"pymupdf4llm extraction failed: {e}")
            # Fall back to pymupdf
            if PYMUPDF_AVAILABLE:
                return self._extract_with_pymupdf(pdf_path)
            raise

    def _extract_with_pdfplumber(self, pdf_path: str) -> PDFExtractionResult:
        """Extract using pdfplumber for enhanced table detection."""
        logger.info(f"Extracting with pdfplumber: {pdf_path}")

        text_parts = []
        tables = []
        structure = {'headers': [], 'sections': []}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                metadata = pdf.metadata or {}

                for i, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text() or ''
                    text_parts.append(page_text)

                    # Extract tables
                    page_tables = page.extract_tables()
                    for j, table in enumerate(page_tables):
                        tables.append({
                            'page': i + 1,
                            'table_index': j,
                            'data': table,
                            'rows': len(table) if table else 0,
                            'cols': len(table[0]) if table and table[0] else 0
                        })

            text = '\n\n'.join(text_parts)
            text = self._apply_kerning_fixes(text)

            # Parse headers from text
            structure = self._parse_text_structure(text)

            quality = self._calculate_quality(text, tables, structure)

            return PDFExtractionResult(
                text=text,
                metadata=metadata,
                tables=tables,
                structure=structure,
                backend_used='pdfplumber',
                page_count=page_count,
                extraction_quality=quality
            )

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            if PYMUPDF_AVAILABLE:
                return self._extract_with_pymupdf(pdf_path)
            raise

    def _extract_with_pymupdf(self, pdf_path: str) -> PDFExtractionResult:
        """Extract using PyMuPDF (fast, reliable)."""
        logger.info(f"Extracting with PyMuPDF: {pdf_path}")

        text_parts = []
        tables = []
        structure = {'headers': [], 'sections': []}

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            metadata = dict(doc.metadata) if doc.metadata else {}

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()

            text = '\n'.join(text_parts)
            text = self._apply_kerning_fixes(text)

            structure = self._parse_text_structure(text)

            quality = self._calculate_quality(text, tables, structure)

            return PDFExtractionResult(
                text=text,
                metadata=metadata,
                tables=tables,
                structure=structure,
                backend_used='pymupdf',
                page_count=page_count,
                extraction_quality=quality
            )

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise

    def _apply_kerning_fixes(self, text: str) -> str:
        """Apply kerning fixes to extracted text."""
        # Fix single letter + space + letters pattern
        text = re.sub(r'\b([A-Z]) ([A-Z]{2,})\b', r'\1\2', text)
        text = re.sub(r'\b([a-z]) ([a-z]{2,})\b', r'\1\2', text)

        # Apply dictionary fixes
        for broken, fixed in self._kerning_fixes.items():
            text = text.replace(broken, fixed)

        # Clean up multiple spaces
        text = re.sub(r' +', ' ', text)

        return text

    def _parse_markdown_structure(self, md_text: str) -> Dict[str, Any]:
        """Parse structure from markdown text."""
        structure = {'headers': [], 'sections': []}

        # Find headers (# syntax)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        for match in re.finditer(header_pattern, md_text, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            structure['headers'].append({
                'level': level,
                'text': text,
                'position': match.start()
            })

        return structure

    def _extract_tables_from_markdown(self, md_text: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown format."""
        tables = []

        # Markdown table pattern
        table_pattern = r'(\|.+\|\n)(\|[-:| ]+\|\n)((?:\|.+\|\n)+)'

        for i, match in enumerate(re.finditer(table_pattern, md_text)):
            header_row = match.group(1)
            data_rows = match.group(3)

            # Parse header
            headers = [cell.strip() for cell in header_row.strip().split('|') if cell.strip()]

            # Parse data
            rows = []
            for row in data_rows.strip().split('\n'):
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                rows.append(cells)

            tables.append({
                'table_index': i,
                'headers': headers,
                'data': rows,
                'rows': len(rows),
                'cols': len(headers)
            })

        return tables

    def _parse_text_structure(self, text: str) -> Dict[str, Any]:
        """Parse structure from plain text."""
        structure = {'headers': [], 'sections': []}

        # Common header patterns in technical documents
        patterns = [
            r'^(\d+\.)+\s+([A-Z][^\n]+)',  # 1.1 Section Title
            r'^([A-Z][A-Z ]{3,})$',  # ALL CAPS HEADERS
            r'^Section\s+\d+[:\s]+(.+)',  # Section 1: Title
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                structure['headers'].append({
                    'text': match.group(0).strip(),
                    'position': match.start()
                })

        return structure

    def _calculate_quality(self, text: str, tables: List, structure: Dict) -> float:
        """Calculate extraction quality score (0-1)."""
        score = 0.5  # Base score

        # Text content
        if len(text) > 100:
            score += 0.2
        if len(text) > 1000:
            score += 0.1

        # Tables extracted
        if tables:
            score += 0.1

        # Structure detected
        if structure.get('headers'):
            score += 0.1

        # Check for extraction artifacts
        artifact_patterns = [
            r'\x00',  # Null bytes
            r'[\uFFFD]',  # Replacement characters
            r'(?<=[a-z]) (?=[a-z]{2,})',  # Kerning issues
        ]

        artifact_count = 0
        for pattern in artifact_patterns:
            artifact_count += len(re.findall(pattern, text))

        if artifact_count > 10:
            score -= 0.2
        elif artifact_count > 5:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def extract_tables_only(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract only tables from PDF.

        Uses pdfplumber for best table detection.
        """
        if PDFPLUMBER_AVAILABLE:
            result = self._extract_with_pdfplumber(pdf_path)
            return result.tables

        # Fallback to pymupdf4llm
        if PYMUPDF4LLM_AVAILABLE:
            result = self._extract_with_pymupdf4llm(pdf_path)
            return result.tables

        return []

    def get_available_backends(self) -> List[str]:
        """Get list of available backends."""
        backends = []
        if PYMUPDF4LLM_AVAILABLE:
            backends.append('pymupdf4llm')
        if PDFPLUMBER_AVAILABLE:
            backends.append('pdfplumber')
        if PYMUPDF_AVAILABLE:
            backends.append('pymupdf')
        return backends


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_extractor_instance: Optional[EnhancedPDFExtractor] = None


def get_enhanced_extractor() -> EnhancedPDFExtractor:
    """Get or create singleton enhanced PDF extractor."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EnhancedPDFExtractor()
    return _extractor_instance


def extract_pdf(pdf_path: str, backend: str = 'auto') -> PDFExtractionResult:
    """
    Extract content from PDF.

    Args:
        pdf_path: Path to PDF file
        backend: 'auto', 'pymupdf4llm', 'pdfplumber', or 'pymupdf'

    Returns:
        PDFExtractionResult
    """
    extractor = get_enhanced_extractor()
    return extractor.extract(pdf_path, backend)


def extract_pdf_text(pdf_path: str) -> str:
    """Extract just the text from a PDF."""
    result = extract_pdf(pdf_path)
    return result.text


def extract_pdf_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract tables from a PDF."""
    extractor = get_enhanced_extractor()
    return extractor.extract_tables_only(pdf_path)


def get_available_backends() -> List[str]:
    """Get list of available PDF backends."""
    return get_enhanced_extractor().get_available_backends()


__all__ = [
    'EnhancedPDFExtractor',
    'PDFExtractionResult',
    'get_enhanced_extractor',
    'extract_pdf',
    'extract_pdf_text',
    'extract_pdf_tables',
    'get_available_backends',
    'VERSION',
    'PYMUPDF4LLM_AVAILABLE',
    'PDFPLUMBER_AVAILABLE',
    'PYMUPDF_AVAILABLE'
]
