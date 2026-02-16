#!/usr/bin/env python3
"""
PDF Extractor v2 for AEGIS
=====================================
Enhanced PDF extraction with:
- PDF quality detection (native text vs scanned vs OCR)
- Multi-column layout handling
- Better table extraction
- Metadata extraction
- Graceful fallback without PyMuPDF

Version: reads from version.json (module v2.9)
"""

import re
import statistics
import logging
from typing import List, Dict, Tuple, Optional, NamedTuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

__version__ = "2.9.1"  # Updated for enhanced table extraction

logger = logging.getLogger(__name__)


class PDFQuality(Enum):
    """PDF quality classification."""
    NATIVE_TEXT = "native_text"      # Text embedded in PDF (best quality)
    OCR_TEXT = "ocr_text"            # Text from OCR processing (good quality)
    SCANNED = "scanned"              # Image-based, no text layer (poor quality)
    MIXED = "mixed"                  # Combination of text and scanned pages
    UNKNOWN = "unknown"              # Could not determine


@dataclass
class PDFMetadata:
    """PDF document metadata."""
    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    modification_date: str = ""
    pdf_version: str = ""
    page_count: int = 0
    file_size_bytes: int = 0
    encrypted: bool = False


@dataclass  
class PDFQualityReport:
    """Detailed quality assessment of a PDF."""
    quality: PDFQuality = PDFQuality.UNKNOWN
    confidence: float = 0.0
    text_extraction_ratio: float = 0.0  # Chars extracted per page
    has_embedded_fonts: bool = False
    has_images: bool = False
    ocr_indicators: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    pages_by_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class TextBlock:
    """A block of text with position information."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int
    block_type: str = "text"  # text, table, image, heading
    font_name: str = ""
    font_size: float = 0.0
    is_bold: bool = False


# Try to import PDF libraries in order of preference
PDF_LIBRARY = None
PYMUPDF_AVAILABLE = False
PDFPLUMBER_AVAILABLE = False
PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "pymupdf"
    PYMUPDF_AVAILABLE = True
except ImportError:
    pass

if not PDF_LIBRARY:
    try:
        import pdfplumber
        PDF_LIBRARY = "pdfplumber"
        PDFPLUMBER_AVAILABLE = True
    except ImportError:
        pass

if not PDF_LIBRARY:
    try:
        from pypdf import PdfReader
        PDF_LIBRARY = "pypdf"
        PYPDF_AVAILABLE = True
    except ImportError:
        pass


class PDFExtractorV2:
    """
    Enhanced PDF content extractor with quality detection and layout handling.
    
    Features:
    - Detects PDF quality (native text, OCR, scanned)
    - Handles multi-column layouts
    - Extracts tables with structure
    - Provides quality warnings for frontend display
    """
    
    def __init__(self, filepath: str, analyze_quality: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            filepath: Path to PDF file
            analyze_quality: Whether to perform quality analysis (default True)
        """
        self.filepath = filepath
        self.paragraphs: List[Tuple[int, str]] = []
        self.tables: List[Dict] = []
        self.figures: List[Dict] = []
        self.comments: List[Dict] = []
        self.track_changes: List[Dict] = []
        self.headings: List[Dict] = []
        self.hyperlinks: List[Dict] = []  # v3.0.92: PDF embedded hyperlinks
        self.full_text: str = ""
        self.word_count: int = 0
        self.has_toc: bool = False
        self.sections: Dict[str, int] = {}
        self.page_count: int = 0
        
        # New v2 attributes
        self.metadata: PDFMetadata = PDFMetadata()
        self.quality_report: PDFQualityReport = PDFQualityReport()
        self._text_blocks: List[TextBlock] = []
        self._column_count: int = 1
        
        # v3.0.94: Page mapping for context tracking
        # Maps paragraph_index -> page_number (1-indexed)
        self.page_map: Dict[int, int] = {}
        
        # Extract content
        self._extract()
        
        # Optionally analyze quality
        if analyze_quality:
            self._analyze_quality()
    
    def _extract(self):
        """Extract content from PDF based on available library."""
        if PDF_LIBRARY == "pymupdf":
            self._extract_with_pymupdf()
        elif PDF_LIBRARY == "pdfplumber":
            self._extract_with_pdfplumber()
        elif PDF_LIBRARY == "pypdf":
            self._extract_with_pypdf()
        else:
            raise ImportError(
                "No PDF library available. Install one of: "
                "pymupdf (pip install pymupdf), "
                "pdfplumber (pip install pdfplumber), or "
                "pypdf (pip install pypdf)"
            )
        
        # v3.0.91+: OCR fallback for scanned PDFs
        # If we extracted very little text, try OCR
        total_text = sum(len(p[1]) for p in self.paragraphs)
        chars_per_page = total_text / max(self.page_count, 1)
        
        if chars_per_page < 200:  # Less than 200 chars per page suggests scanned PDF
            ocr_text = self._try_ocr_fallback()
            if ocr_text and len(ocr_text) > total_text:
                logger.info(f"Using OCR fallback: {len(ocr_text)} chars vs {total_text} from text extraction")
                self._parse_ocr_text(ocr_text)
    
    def _try_ocr_fallback(self) -> str:
        """Try OCR extraction as fallback for scanned PDFs."""
        try:
            from ocr_extractor import OCRExtractor
            
            extractor = OCRExtractor()
            if not extractor.is_available:
                logger.debug("OCR not available for fallback")
                return ""
            
            result = extractor.extract_from_pdf(self.filepath)
            
            if result.warnings:
                for warning in result.warnings:
                    logger.debug(f"OCR warning: {warning}")
            
            if result.confidence > 50:  # Only use if decent confidence
                return result.text
            else:
                logger.debug(f"OCR confidence too low: {result.confidence:.1f}%")
                return ""
                
        except ImportError:
            logger.debug("OCR extractor not available")
            return ""
        except Exception as e:
            logger.debug(f"OCR fallback failed: {e}")
            return ""
    
    def _parse_ocr_text(self, ocr_text: str):
        """Parse OCR-extracted text into paragraphs."""
        # Reset paragraphs
        self.paragraphs = []
        
        # Split into paragraphs by double newlines or significant gaps
        import re
        blocks = re.split(r'\n\s*\n', ocr_text)
        
        para_idx = 0
        for block in blocks:
            block = block.strip()
            if not block or len(block) < 3:
                continue
            
            # Clean up OCR artifacts
            block = re.sub(r'\s+', ' ', block)  # Normalize whitespace
            
            # Check for headings
            heading_level = self._detect_heading_level(block)
            if heading_level:
                self.headings.append({
                    'text': block[:100],
                    'level': heading_level,
                    'index': para_idx
                })
            
            cleaned = self._clean_text(block)
            if cleaned and len(cleaned) > 2:
                self.paragraphs.append((para_idx, cleaned))
                # v3.0.94: OCR doesn't provide page info, default to 1
                self.page_map[para_idx] = 1
                para_idx += 1
    
    def _extract_with_pymupdf(self):
        """Extract content using PyMuPDF (fitz) with enhanced layout handling."""
        import fitz
        
        pdf = fitz.open(self.filepath)
        self.page_count = len(pdf)
        
        # Extract metadata
        self._extract_metadata_pymupdf(pdf)
        
        all_text = []
        all_blocks: List[TextBlock] = []
        para_idx = 0
        table_count = 0
        figure_count = 0
        
        for page_num in range(self.page_count):
            page = pdf[page_num]
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Extract images/figures
            images = page.get_images()
            for img in images:
                figure_count += 1
                self.figures.append({
                    'index': figure_count,
                    'page': page_num + 1,
                    'type': 'image'
                })
            
            # v3.0.92: Extract hyperlinks from PDF
            try:
                links = page.get_links()
                for link in links:
                    link_type = link.get('kind', -1)
                    link_info = {
                        'page': page_num + 1,
                        'rect': link.get('from', []),
                    }
                    
                    # URI (external link)
                    if link_type == 2:  # LINK_URI
                        link_info['type'] = 'uri'
                        link_info['target'] = link.get('uri', '')
                        link_info['display_text'] = ''  # PDFs don't store display text separately
                        self.hyperlinks.append(link_info)
                    
                    # Internal link (goto)
                    elif link_type == 1:  # LINK_GOTO
                        link_info['type'] = 'internal'
                        link_info['target'] = f"page:{link.get('page', 0) + 1}"
                        self.hyperlinks.append(link_info)
                    
                    # File link
                    elif link_type == 3:  # LINK_GOTOR
                        link_info['type'] = 'file'
                        link_info['target'] = link.get('file', '')
                        self.hyperlinks.append(link_info)
                    
                    # Named destination
                    elif link_type == 4:  # LINK_NAMED
                        link_info['type'] = 'named'
                        link_info['target'] = link.get('name', '')
                        self.hyperlinks.append(link_info)
            except Exception as e:
                logger.debug(f"Error extracting links from page {page_num + 1}: {e}")
            
            # Use dict extraction for layout-aware processing
            page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            
            # Process blocks with position info
            for block in page_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    
                    # Extract text from lines and spans
                    block_text = ""
                    font_info = {"name": "", "size": 0, "bold": False}
                    
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            line_text += span_text
                            
                            # Capture font info from first non-empty span
                            if span_text.strip() and not font_info["name"]:
                                font_info["name"] = span.get("font", "")
                                font_info["size"] = span.get("size", 0)
                                flags = span.get("flags", 0)
                                font_info["bold"] = bool(flags & 2**4)  # Bold flag
                        
                        block_text += line_text + "\n"
                    
                    block_text = block_text.strip()
                    if block_text:
                        text_block = TextBlock(
                            text=block_text,
                            x0=bbox[0],
                            y0=bbox[1],
                            x1=bbox[2],
                            y1=bbox[3],
                            page=page_num + 1,
                            font_name=font_info["name"],
                            font_size=font_info["size"],
                            is_bold=font_info["bold"]
                        )
                        all_blocks.append(text_block)
                
                elif block.get("type") == 1:  # Image block
                    figure_count += 1
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    self.figures.append({
                        'index': figure_count,
                        'page': page_num + 1,
                        'type': 'embedded_image',
                        'bbox': bbox
                    })
        
        pdf.close()
        
        # Store raw blocks
        self._text_blocks = all_blocks
        
        # Detect column layout
        self._detect_columns(all_blocks)
        
        # Reorder blocks by reading order (handle multi-column)
        ordered_blocks = self._reorder_blocks_by_reading_order(all_blocks)
        
        # Process blocks into paragraphs
        for block in ordered_blocks:
            text = block.text.strip()
            if not text:
                continue
            
            # Skip headers/footers
            if self._is_header_footer(text):
                continue
            
            # Check if this looks like a table
            if self._looks_like_table(text):
                table_count += 1
                self.tables.append({
                    'index': table_count,
                    'page': block.page,
                    'content': text
                })
                continue
            
            # Check for headings
            heading_level = self._detect_heading_level(text, block.font_size, block.is_bold)
            if heading_level:
                self.headings.append({
                    'text': text[:100],
                    'level': heading_level,
                    'index': para_idx
                })
            
            # Clean and add paragraph
            cleaned = self._clean_text(text)
            if cleaned and len(cleaned) > 10:
                self.paragraphs.append((para_idx, cleaned))
                # v3.0.94: Track page number for this paragraph
                self.page_map[para_idx] = block.page
                all_text.append(cleaned)
                para_idx += 1
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
    def _extract_metadata_pymupdf(self, pdf):
        """Extract metadata using PyMuPDF."""
        meta = pdf.metadata or {}
        
        self.metadata = PDFMetadata(
            title=meta.get("title", "") or "",
            author=meta.get("author", "") or "",
            subject=meta.get("subject", "") or "",
            creator=meta.get("creator", "") or "",
            producer=meta.get("producer", "") or "",
            creation_date=meta.get("creationDate", "") or "",
            modification_date=meta.get("modDate", "") or "",
            pdf_version=f"{pdf.metadata.get('format', 'PDF')}" if pdf.metadata else "PDF",
            page_count=len(pdf),
            file_size_bytes=Path(self.filepath).stat().st_size,
            encrypted=pdf.is_encrypted
        )
    
    def _detect_columns(self, blocks: List[TextBlock]):
        """Detect if document has multi-column layout."""
        if not blocks:
            self._column_count = 1
            return
        
        # Group blocks by page
        pages = {}
        for block in blocks:
            if block.page not in pages:
                pages[block.page] = []
            pages[block.page].append(block)
        
        # Analyze x-positions to detect columns
        column_counts = []
        
        for page_num, page_blocks in pages.items():
            if len(page_blocks) < 3:
                continue
            
            # Get x-center of each block
            x_centers = [(b.x0 + b.x1) / 2 for b in page_blocks]
            
            if not x_centers:
                continue
            
            # Simple heuristic: if blocks cluster into 2+ distinct x regions
            x_centers_sorted = sorted(x_centers)
            
            # Look for gaps in x-positions
            gaps = []
            for i in range(1, len(x_centers_sorted)):
                gap = x_centers_sorted[i] - x_centers_sorted[i-1]
                if gap > 50:  # Significant gap
                    gaps.append(gap)
            
            if len(gaps) >= 1:
                # Calculate how many columns based on gap positions
                # This is simplified - real implementation would cluster
                if max(gaps) > 150:  # Large gap suggests multi-column
                    column_counts.append(2)
                else:
                    column_counts.append(1)
            else:
                column_counts.append(1)
        
        if column_counts:
            # Use mode (most common) column count
            self._column_count = max(set(column_counts), key=column_counts.count)
        else:
            self._column_count = 1
    
    def _reorder_blocks_by_reading_order(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """Reorder text blocks for natural reading order (handles multi-column)."""
        if not blocks:
            return []
        
        # Group by page
        pages = {}
        for block in blocks:
            if block.page not in pages:
                pages[block.page] = []
            pages[block.page].append(block)
        
        result = []
        
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            
            if self._column_count == 1:
                # Single column: sort by y position (top to bottom)
                sorted_blocks = sorted(page_blocks, key=lambda b: (b.y0, b.x0))
            else:
                # Multi-column: sort by column then y position
                # Determine column boundary
                all_x = [(b.x0 + b.x1) / 2 for b in page_blocks]
                if all_x:
                    mid_x = (max(all_x) + min(all_x)) / 2
                else:
                    mid_x = 300  # Default
                
                # Assign blocks to columns
                left_col = [b for b in page_blocks if (b.x0 + b.x1) / 2 < mid_x]
                right_col = [b for b in page_blocks if (b.x0 + b.x1) / 2 >= mid_x]
                
                # Sort each column by y, then combine (left first, then right)
                left_sorted = sorted(left_col, key=lambda b: b.y0)
                right_sorted = sorted(right_col, key=lambda b: b.y0)
                
                sorted_blocks = left_sorted + right_sorted
            
            result.extend(sorted_blocks)
        
        return result
    
    def _extract_with_pdfplumber(self):
        """Extract content using pdfplumber."""
        import pdfplumber
        
        all_text = []
        para_idx = 0
        table_count = 0
        
        with pdfplumber.open(self.filepath) as pdf:
            self.page_count = len(pdf.pages)
            
            # Extract metadata
            self.metadata = PDFMetadata(
                page_count=self.page_count,
                file_size_bytes=Path(self.filepath).stat().st_size
            )
            
            # Try enhanced multi-library table extraction first (v3.0.91)
            enhanced_tables = self._extract_tables_enhanced()
            if enhanced_tables:
                self.tables = enhanced_tables
                logger.debug(f"Enhanced extraction found {len(enhanced_tables)} tables")
            
            for page_num, page in enumerate(pdf.pages):
                # Only use pdfplumber tables if enhanced extraction failed
                if not enhanced_tables:
                    tables = page.extract_tables()
                    for table in tables:
                        table_count += 1
                        self.tables.append({
                            'index': table_count,
                            'page': page_num + 1,
                            'rows': table,
                            'structured': True
                        })
                
                # Extract text
                page_text = page.extract_text() or ""
                
                # Process text into paragraphs
                blocks = page_text.split('\n\n')
                
                for block in blocks:
                    block = block.strip()
                    if not block or self._is_header_footer(block):
                        continue
                    
                    heading_level = self._detect_heading_level(block)
                    if heading_level:
                        self.headings.append({
                            'text': block[:100],
                            'level': heading_level,
                            'index': para_idx
                        })
                    
                    cleaned = self._clean_text(block)
                    if cleaned and len(cleaned) > 2:
                        self.paragraphs.append((para_idx, cleaned))
                        # v3.0.94: Track page number for this paragraph
                        self.page_map[para_idx] = page_num + 1  # 1-indexed
                        all_text.append(cleaned)
                        para_idx += 1
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
    def _extract_with_pypdf(self):
        """Extract content using pypdf (basic fallback)."""
        from pypdf import PdfReader
        
        reader = PdfReader(self.filepath)
        self.page_count = len(reader.pages)
        
        # Extract metadata
        meta = reader.metadata or {}
        self.metadata = PDFMetadata(
            title=str(meta.get("/Title", "") or ""),
            author=str(meta.get("/Author", "") or ""),
            subject=str(meta.get("/Subject", "") or ""),
            creator=str(meta.get("/Creator", "") or ""),
            producer=str(meta.get("/Producer", "") or ""),
            page_count=self.page_count,
            file_size_bytes=Path(self.filepath).stat().st_size
        )
        
        all_text = []
        para_idx = 0
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            
            # Process text into paragraphs
            blocks = page_text.split('\n\n')
            
            for block in blocks:
                block = block.strip()
                if not block or self._is_header_footer(block):
                    continue
                
                heading_level = self._detect_heading_level(block)
                if heading_level:
                    self.headings.append({
                        'text': block[:100],
                        'level': heading_level,
                        'index': para_idx
                    })
                
                cleaned = self._clean_text(block)
                if cleaned and len(cleaned) > 2:
                    self.paragraphs.append((para_idx, cleaned))
                    # v3.0.94: Track page number for this paragraph
                    self.page_map[para_idx] = page_num + 1  # 1-indexed
                    all_text.append(cleaned)
                    para_idx += 1
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
    def _analyze_quality(self):
        """Analyze PDF quality and generate report."""
        report = PDFQualityReport()
        
        if self.page_count == 0:
            report.quality = PDFQuality.UNKNOWN
            report.warnings.append("Could not read PDF pages")
            self.quality_report = report
            return
        
        # Calculate text extraction ratio
        chars_per_page = len(self.full_text) / self.page_count if self.page_count > 0 else 0
        report.text_extraction_ratio = chars_per_page
        
        # Check for images
        report.has_images = len(self.figures) > 0
        
        # Analyze quality indicators
        ocr_indicators = []
        
        # Check for OCR software markers in metadata
        producer = self.metadata.producer.lower() if self.metadata.producer else ""
        creator = self.metadata.creator.lower() if self.metadata.creator else ""
        
        ocr_tools = ['ocr', 'abbyy', 'tesseract', 'omnipage', 'readiris', 'fine reader']
        for tool in ocr_tools:
            if tool in producer or tool in creator:
                ocr_indicators.append(f"OCR tool detected: {tool}")
        
        # Check text characteristics
        if self.full_text:
            # OCR text often has specific artifacts
            ocr_patterns = [
                (r'[Il1]{3,}', "Repeated I/l/1 sequences (common OCR confusion)"),
                (r'[0O]{3,}', "Repeated 0/O sequences (common OCR confusion)"),
                (r'\b[a-z][A-Z][a-z]', "Mixed case mid-word (OCR artifact)"),
                (r'[^\x00-\x7F]{5,}', "Extended non-ASCII sequences"),
            ]
            
            for pattern, description in ocr_patterns:
                if re.search(pattern, self.full_text[:5000]):
                    ocr_indicators.append(description)
        
        report.ocr_indicators = ocr_indicators
        
        # Determine quality classification
        pages_by_type = {"text": 0, "scanned": 0, "mixed": 0}
        
        if chars_per_page < 50:
            # Very little text - likely scanned
            report.quality = PDFQuality.SCANNED
            report.confidence = 0.9
            pages_by_type["scanned"] = self.page_count
            report.warnings.append("PDF appears to be scanned with no text layer")
            report.recommendations.append("Consider running OCR on this document for better analysis")
        elif chars_per_page < 500 and report.has_images:
            # Some text but image-heavy
            if ocr_indicators:
                report.quality = PDFQuality.OCR_TEXT
                report.confidence = 0.7
                pages_by_type["text"] = self.page_count
                report.warnings.append("PDF appears to contain OCR-processed text")
            else:
                report.quality = PDFQuality.MIXED
                report.confidence = 0.6
                pages_by_type["mixed"] = self.page_count
                report.warnings.append("PDF has mixed content (text and images)")
        elif ocr_indicators:
            report.quality = PDFQuality.OCR_TEXT
            report.confidence = 0.8
            pages_by_type["text"] = self.page_count
        else:
            report.quality = PDFQuality.NATIVE_TEXT
            report.confidence = 0.85
            pages_by_type["text"] = self.page_count
        
        report.pages_by_type = pages_by_type
        
        # Check for potential issues
        if self.word_count < 100 and self.page_count > 1:
            report.warnings.append(f"Low word count ({self.word_count}) for {self.page_count} pages")
        
        if len(self.figures) > self.page_count * 2:
            report.warnings.append(f"High image density ({len(self.figures)} images)")
        
        self.quality_report = report
    
    def _is_header_footer(self, text: str) -> bool:
        """Detect if text is a header or footer to skip."""
        text = text.strip()
        
        # Common header/footer patterns
        patterns = [
            r'^Page\s+\d+\s+(of|/)\s+\d+',
            r'^\d+\s+of\s+\d+$',
            r'^Copyright\s+',
            r'^Provided by\s+',
            r'^Licensee[=:]',
            r'^No reproduction',
            r'^All rights reserved',
            r'^Not for [Rr]esale',
            r'^--`,',  # IHS Markit watermark
            r'^\s*-{5,}\s*$',  # Horizontal lines
            r'^_{10,}$',  # Underscores
            r'^\d{1,3}$',  # Standalone page numbers
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Very short lines that are likely page numbers
        if len(text) < 10 and re.match(r'^[\d\s\-/]+$', text):
            return True
        
        return False
    
    def _extract_tables_enhanced(self) -> List[Dict]:
        """
        Extract tables using enhanced multi-library extraction (v3.0.91).
        
        Uses Camelot + Tabula + pdfplumber for maximum accuracy.
        Returns tables in standard format compatible with existing code.
        """
        try:
            from enhanced_table_extractor import EnhancedTableExtractor
            
            extractor = EnhancedTableExtractor(prefer_accuracy=True)
            result = extractor.extract_tables(self.filepath)
            
            if not result.tables:
                return []
            
            # Convert to existing format
            tables = []
            for t in result.tables:
                # Build rows with headers as first row for compatibility
                all_rows = [t.headers] + t.rows if t.headers else t.rows
                
                tables.append({
                    'index': t.index,
                    'page': t.page,
                    'rows': all_rows,
                    'headers': t.headers,
                    'structured': True,
                    'confidence': t.confidence,
                    'source': t.source,
                    'row_count': t.row_count,
                    'col_count': t.col_count
                })
            
            return tables
            
        except ImportError:
            return []
        except Exception as e:
            logger.debug(f"Enhanced table extraction failed: {e}")
            return []
    
    def _looks_like_table(self, text: str) -> bool:
        """Detect if text block looks like a table."""
        lines = text.split('\n')
        if len(lines) < 2:
            return False
        
        # Check for consistent tab or multiple space patterns
        tab_count = sum(1 for line in lines if '\t' in line or '  ' in line)
        if len(lines) > 0 and tab_count / len(lines) > 0.7:
            return True
        
        # Check for TOC-style dot leaders
        if re.search(r'\.{3,}\s*\d+', text):
            return True
        
        # Check for pipe-delimited tables
        if '|' in text:
            pipe_lines = sum(1 for line in lines if '|' in line)
            if len(lines) > 0 and pipe_lines / len(lines) > 0.5:
                return True
        
        return False
    
    def _detect_heading_level(self, text: str, font_size: float = 0, is_bold: bool = False) -> Optional[int]:
        """
        Detect if text is a heading and return its level.
        
        Args:
            text: The text to analyze
            font_size: Font size (from PyMuPDF) for better detection
            is_bold: Whether text is bold
        """
        text = text.strip()
        if not text or len(text) > 150:
            return None
        
        # Numbered heading patterns (common in technical documents)
        patterns = [
            # Standard numbered: "1. SCOPE", "1.0 SCOPE"
            (r'^(\d+)\.\s+[A-Z]', 1),
            (r'^(\d+)\.0\s+[A-Z]', 1),
            # Section numbered: "1.1 Overview", "1.1.0 Overview"
            (r'^(\d+\.\d+)\s+[A-Z]', 2),
            (r'^(\d+\.\d+)\.?\s+[A-Z][a-z]', 2),
            # Subsection: "1.1.1 Details"
            (r'^(\d+\.\d+\.\d+)\s+[A-Z]', 3),
            # Deep subsection: "1.1.1.1 Subdetails"
            (r'^(\d+\.\d+\.\d+\.\d+)\s+', 4),
            # Letter sections: "A. Introduction", "A.1 Background"
            (r'^[A-Z]\.\s+[A-Z]', 1),
            (r'^[A-Z]\.\d+\s+[A-Z]', 2),
            # MIL-STD style: "3.1.2.1"
            (r'^\d+\.\d+\.\d+\.\d+\s+', 4),
        ]
        
        for pattern, level in patterns:
            if re.match(pattern, text):
                return level
        
        # Use font size if available (larger = higher level heading)
        if font_size > 0:
            if font_size >= 16 and is_bold:
                return 1
            elif font_size >= 14 and is_bold:
                return 2
            elif font_size >= 12 and is_bold:
                return 3
        
        # All caps short text (often headings)
        words = text.split()
        if len(words) <= 6:
            if text.isupper():
                return 1
            # Title case with short length
            if len(words) <= 4 and all(w[0].isupper() for w in words if w):
                return 2
        
        # Common heading keywords at start
        heading_keywords = [
            'SECTION', 'CHAPTER', 'PART', 'APPENDIX', 'ANNEX', 'ATTACHMENT',
            'INTRODUCTION', 'SCOPE', 'PURPOSE', 'BACKGROUND', 'OVERVIEW',
            'REQUIREMENTS', 'REFERENCES', 'DEFINITIONS', 'ACRONYMS',
            'APPLICABLE DOCUMENTS', 'GENERAL', 'SPECIFIC', 'DETAILED',
            'SUMMARY', 'CONCLUSION', 'NOTES', 'RATIONALE',
            'RESPONSIBILITIES', 'PROCEDURES', 'PROCESS', 'TASKS'
        ]
        
        text_upper = text.upper()
        for keyword in heading_keywords:
            if text_upper.startswith(keyword):
                return 1
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text from PDF.
        
        v3.0.92 FIX: Reordered operations to remove multiple spaces LAST.
        Previously, spaces were removed before newline conversion, causing
        newlines like "word \\n next" to become "word  next" (double space).
        """
        # Remove soft hyphens and other special chars FIRST
        text = text.replace('\u00ad', '')  # Soft hyphen
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\ufeff', '')  # BOM
        text = text.replace('\u00a0', ' ')  # Non-breaking space -> regular space
        
        # Join hyphenated line breaks (word-\nbreak -> wordbreak)
        text = re.sub(r'-\s*\n\s*', '', text)
        
        # Normalize line breaks within paragraphs (single \n -> space)
        text = re.sub(r'\n(?!\n)', ' ', text)
        
        # Remove multiple spaces LAST (after newline conversion)
        text = re.sub(r' +', ' ', text)
        
        # Clean up whitespace
        text = text.strip()
        
        return text
    
    def _detect_toc(self):
        """Detect if document has table of contents."""
        toc_patterns = [
            r'table\s+of\s+contents',
            r'contents\s*\n',
            r'^\s*\d+\.\s+.*\.{3,}\s*\d+',  # TOC entry with dots
        ]
        
        for pattern in toc_patterns:
            if re.search(pattern, self.full_text[:5000], re.IGNORECASE):
                self.has_toc = True
                break
    
    def get_quality_summary(self) -> Dict:
        """
        Get a summary of PDF quality for frontend display.
        
        Returns:
            Dictionary with quality info for UI display
        """
        q = self.quality_report
        
        # Determine severity level for UI styling
        if q.quality == PDFQuality.NATIVE_TEXT:
            severity = "good"
            status = "Good Quality"
        elif q.quality == PDFQuality.OCR_TEXT:
            severity = "warning"
            status = "OCR Text"
        elif q.quality == PDFQuality.SCANNED:
            severity = "error"
            status = "Scanned (No Text)"
        elif q.quality == PDFQuality.MIXED:
            severity = "warning"
            status = "Mixed Content"
        else:
            severity = "info"
            status = "Unknown Quality"
        
        return {
            "quality": q.quality.value,
            "status": status,
            "severity": severity,
            "confidence": round(q.confidence * 100),
            "chars_per_page": round(q.text_extraction_ratio),
            "has_images": q.has_images,
            "warnings": q.warnings,
            "recommendations": q.recommendations,
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "pages": self.metadata.page_count,
                "size_kb": round(self.metadata.file_size_bytes / 1024)
            }
        }


# Module-level functions for backward compatibility

def is_pdf_available() -> bool:
    """Check if PDF extraction is available."""
    return PDF_LIBRARY is not None


def get_pdf_library() -> Optional[str]:
    """Get the name of the available PDF library."""
    return PDF_LIBRARY


def get_pdf_capabilities() -> Dict:
    """Get detailed capabilities of the installed PDF library."""
    return {
        "library": PDF_LIBRARY,
        "pymupdf": PYMUPDF_AVAILABLE,
        "pdfplumber": PDFPLUMBER_AVAILABLE,
        "pypdf": PYPDF_AVAILABLE,
        "features": {
            "quality_detection": PYMUPDF_AVAILABLE,
            "multi_column": PYMUPDF_AVAILABLE,
            "table_extraction": PYMUPDF_AVAILABLE or PDFPLUMBER_AVAILABLE,
            "metadata": True,
            "images": PYMUPDF_AVAILABLE or PDFPLUMBER_AVAILABLE
        }
    }


# Legacy alias for backward compatibility
PDFExtractor = PDFExtractorV2
