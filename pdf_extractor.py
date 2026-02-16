#!/usr/bin/env python3
"""
PDF Extractor for AEGIS
==================================
Extracts content from PDF documents for analysis.
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

__version__ = "2.5.0"

# Try to import PDF libraries
PDF_LIBRARY = None
try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "pymupdf"
except ImportError:
    try:
        import pdfplumber
        PDF_LIBRARY = "pdfplumber"
    except ImportError:
        try:
            from pypdf import PdfReader
            PDF_LIBRARY = "pypdf"
        except ImportError:
            pass


class PDFExtractor:
    """Extracts content from PDF documents."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.paragraphs: List[Tuple[int, str]] = []
        self.tables: List[Dict] = []
        self.figures: List[Dict] = []
        self.comments: List[Dict] = []
        self.track_changes: List[Dict] = []
        self.headings: List[Dict] = []
        self.full_text: str = ""
        self.word_count: int = 0
        self.has_toc: bool = False
        self.sections: Dict[str, int] = {}
        self.page_count: int = 0
        self._extract()
    
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
    
    def _extract_with_pymupdf(self):
        """Extract content using PyMuPDF (fitz)."""
        import fitz
        
        pdf = fitz.open(self.filepath)
        self.page_count = len(pdf)
        
        all_text = []
        para_idx = 0
        table_count = 0
        figure_count = 0
        
        for page_num in range(self.page_count):
            page = pdf[page_num]
            page_text = page.get_text()
            
            # Extract images/figures
            images = page.get_images()
            for img in images:
                figure_count += 1
                self.figures.append({
                    'index': figure_count,
                    'page': page_num + 1,
                    'type': 'image'
                })
            
            # Process text into paragraphs
            # Split by double newlines first
            blocks = re.split(r'\n\s*\n', page_text)
            
            for block in blocks:
                block = block.strip()
                if not block:
                    continue
                
                # Skip common headers/footers
                if self._is_header_footer(block):
                    continue
                
                # For longer blocks, try to split by sentence endings followed by newlines
                # This helps preserve paragraph structure
                if len(block) > 200:
                    # Split on patterns like ". \n" or ".\n" where followed by capital
                    sub_blocks = re.split(r'(?<=\.)\s*\n(?=[A-Z0-9])', block)
                    for sub_block in sub_blocks:
                        sub_block = sub_block.strip()
                        if not sub_block or len(sub_block) < 5:
                            continue
                        if self._is_header_footer(sub_block):
                            continue
                        
                        cleaned = self._clean_text(sub_block)
                        if cleaned and len(cleaned) > 10:
                            # Check for heading
                            heading_level = self._detect_heading_level(cleaned)
                            if heading_level:
                                self.headings.append({
                                    'text': cleaned[:100],
                                    'level': heading_level,
                                    'index': para_idx
                                })
                            
                            self.paragraphs.append((para_idx, cleaned))
                            all_text.append(cleaned)
                            para_idx += 1
                else:
                    # Check if this looks like a table row
                    if self._looks_like_table(block):
                        table_count += 1
                        self.tables.append({
                            'index': table_count,
                            'page': page_num + 1,
                            'content': block
                        })
                        continue
                    
                    # Check for headings
                    heading_level = self._detect_heading_level(block)
                    if heading_level:
                        self.headings.append({
                            'text': block[:100],
                            'level': heading_level,
                            'index': para_idx
                        })
                    
                    # Clean up the text
                    cleaned = self._clean_text(block)
                    if cleaned and len(cleaned) > 10:
                        self.paragraphs.append((para_idx, cleaned))
                        all_text.append(cleaned)
                        para_idx += 1
        
        pdf.close()
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
    def _extract_with_pdfplumber(self):
        """Extract content using pdfplumber."""
        import pdfplumber
        
        all_text = []
        para_idx = 0
        table_count = 0
        figure_count = 0
        
        with pdfplumber.open(self.filepath) as pdf:
            self.page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    table_count += 1
                    self.tables.append({
                        'index': table_count,
                        'page': page_num + 1,
                        'rows': table
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
                            'text': block,
                            'level': heading_level,
                            'index': para_idx
                        })
                    
                    cleaned = self._clean_text(block)
                    if cleaned and len(cleaned) > 2:
                        self.paragraphs.append((para_idx, cleaned))
                        all_text.append(cleaned)
                        para_idx += 1
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
    def _extract_with_pypdf(self):
        """Extract content using pypdf."""
        from pypdf import PdfReader
        
        reader = PdfReader(self.filepath)
        self.page_count = len(reader.pages)
        
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
                        'text': block,
                        'level': heading_level,
                        'index': para_idx
                    })
                
                cleaned = self._clean_text(block)
                if cleaned and len(cleaned) > 2:
                    self.paragraphs.append((para_idx, cleaned))
                    all_text.append(cleaned)
                    para_idx += 1
        
        self.full_text = '\n\n'.join(all_text)
        self.word_count = len(self.full_text.split())
        self._detect_toc()
    
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
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Very short lines that are likely page numbers
        if len(text) < 10 and re.match(r'^[\d\s\-/]+$', text):
            return True
        
        return False
    
    def _looks_like_table(self, text: str) -> bool:
        """Detect if text block looks like a table."""
        lines = text.split('\n')
        if len(lines) < 2:
            return False
        
        # Check for consistent tab or multiple space patterns
        tab_count = sum(1 for line in lines if '\t' in line or '  ' in line)
        if tab_count / len(lines) > 0.7:
            return True
        
        # Check for TOC-style dot leaders
        if re.search(r'\.{3,}\s*\d+', text):
            return True
        
        return False
    
    def _detect_heading_level(self, text: str) -> Optional[int]:
        """Detect if text is a heading and return its level."""
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
        """Clean extracted text."""
        # Remove soft hyphens and other special chars first
        text = text.replace('\u00ad', '')
        text = text.replace('\u200b', '')
        text = text.replace('\u00a0', ' ')  # Non-breaking space

        # Fix PDF kerning issues: single letter followed by space then more letters
        # Common pattern: "N OTE" -> "NOTE", "W ARNING" -> "WARNING"
        # Match: single capital letter + space + 2+ capital letters at word boundary
        text = re.sub(r'\b([A-Z]) ([A-Z]{2,})\b', r'\1\2', text)

        # Also fix lowercase kerning: "in tro" -> "intro"
        text = re.sub(r'\b([a-z]) ([a-z]{2,})\b', r'\1\2', text)

        # Fix common broken document keywords (PDF kerning artifacts)
        # Organized by category for maintainability
        kerning_fixes = {
            # Document structure labels
            'N OTE': 'NOTE',
            'N OTES': 'NOTES',
            'W ARNING': 'WARNING',
            'C AUTION': 'CAUTION',
            'I MPORTANT': 'IMPORTANT',
            'T ABLE': 'TABLE',
            'F IGURE': 'FIGURE',
            'S ECTION': 'SECTION',
            'A PPENDIX': 'APPENDIX',
            'R EFERENCE': 'REFERENCE',
            'A CRONYM': 'ACRONYM',
            'A TTACHMENT': 'ATTACHMENT',
            'E XAMPLE': 'EXAMPLE',
            'D EFINITION': 'DEFINITION',
            'R ATIONALE': 'RATIONALE',
            'C HAPTER': 'CHAPTER',
            'P ARAGRAPH': 'PARAGRAPH',
            'S UMMARY': 'SUMMARY',
            'O VERVIEW': 'OVERVIEW',
            'I NTRODUCTION': 'INTRODUCTION',
            'C ONCLUSION': 'CONCLUSION',
            'B ACKGROUND': 'BACKGROUND',
            'P URPOSE': 'PURPOSE',
            'S COPE': 'SCOPE',

            # Technical/Aerospace terms
            'R EQUIREMENT': 'REQUIREMENT',
            'R EQUIREMENTS': 'REQUIREMENTS',
            'S PECIFICATION': 'SPECIFICATION',
            'S YSTEM': 'SYSTEM',
            'S YSTEMS': 'SYSTEMS',
            'S OFTWARE': 'SOFTWARE',
            'H ARDWARE': 'HARDWARE',
            'I NTERFACE': 'INTERFACE',
            'C OMPONENT': 'COMPONENT',
            'A SSEMBLY': 'ASSEMBLY',
            'M ODULE': 'MODULE',
            'T EST': 'TEST',
            'T ESTING': 'TESTING',
            'V ERIFICATION': 'VERIFICATION',
            'V ALIDATION': 'VALIDATION',
            'C ONFIGURATION': 'CONFIGURATION',
            'D ESIGN': 'DESIGN',
            'D EVELOPMENT': 'DEVELOPMENT',
            'A NALYSIS': 'ANALYSIS',
            'P ERFORMANCE': 'PERFORMANCE',
            'R ELIABILITY': 'RELIABILITY',
            'S AFETY': 'SAFETY',
            'Q UALITY': 'QUALITY',
            'M AINTENANCE': 'MAINTENANCE',
            'O PERATION': 'OPERATION',
            'O PERATIONS': 'OPERATIONS',
            'P ROCEDURE': 'PROCEDURE',
            'P ROCEDURES': 'PROCEDURES',
            'P ROCESS': 'PROCESS',
            'M ETHOD': 'METHOD',
            'T ECHNICAL': 'TECHNICAL',
            'E NGINEERING': 'ENGINEERING',
            'D OCUMENT': 'DOCUMENT',
            'D OCUMENTATION': 'DOCUMENTATION',
            'S TANDARD': 'STANDARD',
            'S TANDARDS': 'STANDARDS',
            'G UIDELINE': 'GUIDELINE',
            'G UIDELINES': 'GUIDELINES',
            'C OMPLIANCE': 'COMPLIANCE',
            'C ERTIFICATION': 'CERTIFICATION',
            'A PPROVAL': 'APPROVAL',
            'R EVIEW': 'REVIEW',
            'A UDIT': 'AUDIT',
            'I NSPECTION': 'INSPECTION',
            'M EASUREMENT': 'MEASUREMENT',
            'C ALIBRATION': 'CALIBRATION',
            'T RAINING': 'TRAINING',
            'P ERSONNEL': 'PERSONNEL',
            'E QUIPMENT': 'EQUIPMENT',
            'M ATERIAL': 'MATERIAL',
            'M ATERIALS': 'MATERIALS',
            'F ACILITY': 'FACILITY',
            'F ACILITIES': 'FACILITIES',
            'E NVIRONMENT': 'ENVIRONMENT',
            'E NVIRONMENTAL': 'ENVIRONMENTAL',
            'T EMPERATURE': 'TEMPERATURE',
            'P RESSURE': 'PRESSURE',
            'V OLTAGE': 'VOLTAGE',
            'C URRENT': 'CURRENT',
            'P OWER': 'POWER',
            'F REQUENCY': 'FREQUENCY',
            'A MPLITUDE': 'AMPLITUDE',
            'S IGNAL': 'SIGNAL',
            'D ATA': 'DATA',
            'D ATABASE': 'DATABASE',
            'N ETWORK': 'NETWORK',
            'C OMMUNICATION': 'COMMUNICATION',
            'C OMMUNICATIONS': 'COMMUNICATIONS',
            'P ROTOCOL': 'PROTOCOL',
            'S ECURITY': 'SECURITY',
            'A CCESS': 'ACCESS',
            'C ONTROL': 'CONTROL',
            'M ANAGEMENT': 'MANAGEMENT',
            'A DMINISTRATION': 'ADMINISTRATION',

            # Aerospace-specific
            'A IRCRAFT': 'AIRCRAFT',
            'A IRFRAME': 'AIRFRAME',
            'A VIONICS': 'AVIONICS',
            'P ROPULSION': 'PROPULSION',
            'N AVIGATION': 'NAVIGATION',
            'G UIDANCE': 'GUIDANCE',
            'F LIGHT': 'FLIGHT',
            'M ISSION': 'MISSION',
            'L AUNCH': 'LAUNCH',
            'O RBIT': 'ORBIT',
            'O RBITAL': 'ORBITAL',
            'S ATELLITE': 'SATELLITE',
            'S PACECRAFT': 'SPACECRAFT',
            'P AYLOAD': 'PAYLOAD',
            'S ENSOR': 'SENSOR',
            'S ENSORS': 'SENSORS',
            'A NTENNA': 'ANTENNA',
            'R ADAR': 'RADAR',
            'T ELEMETRY': 'TELEMETRY',
            'C OMMAND': 'COMMAND',
            'T RACKING': 'TRACKING',
            'G ROUND': 'GROUND',
            'S TATION': 'STATION',
            'S TATIONS': 'STATIONS',
            'V EHICLE': 'VEHICLE',
            'E NGINE': 'ENGINE',
            'E NGINES': 'ENGINES',
            'F UEL': 'FUEL',
            'O XIDIZER': 'OXIDIZER',
            'T HRUST': 'THRUST',
            'A LTITUDE': 'ALTITUDE',
            'V ELOCITY': 'VELOCITY',
            'A CCELERATION': 'ACCELERATION',
            'T RAJECTORY': 'TRAJECTORY',
            'A TTITUDE': 'ATTITUDE',
            'S TABILIZATION': 'STABILIZATION',
            'M ANEUVER': 'MANEUVER',
            'S IMULATION': 'SIMULATION',
            'M ODELING': 'MODELING',

            # Common abbreviations that might get kerning issues
            'S W': 'SW',
            'H W': 'HW',
            'S RS': 'SRS',
            'S DD': 'SDD',
            'I CD': 'ICD',
            'T RR': 'TRR',
            'P DR': 'PDR',
            'C DR': 'CDR',
            'S VD': 'SVD',
            'D ID': 'DID',
            'S OW': 'SOW',
            'W BS': 'WBS',
            'T BD': 'TBD',
            'T BR': 'TBR',
            'N A': 'N/A',
        }
        for broken, fixed in kerning_fixes.items():
            text = text.replace(broken, fixed)

        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)

        # Join hyphenated line breaks
        text = re.sub(r'-\s*\n\s*', '', text)

        # Normalize line breaks within paragraphs
        text = re.sub(r'\n(?!\n)', ' ', text)

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


def is_pdf_available() -> bool:
    """Check if PDF extraction is available."""
    return PDF_LIBRARY is not None


def get_pdf_library() -> Optional[str]:
    """Get the name of the available PDF library."""
    return PDF_LIBRARY
