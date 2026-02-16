"""
DOCX Hyperlink Extractor
========================
Extract hyperlinks and document structure from DOCX files.

This module parses DOCX files to extract:
- All hyperlinks with their display text
- Internal bookmarks
- Section headings with numbers
- Table/Figure/Appendix captions
- Cross-references

Designed to work with the Hyperlink Validator for comprehensive document validation.
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


# XML namespaces used in DOCX files
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}


@dataclass
class ExtractedLink:
    """
    Represents a hyperlink extracted from a DOCX document.

    Attributes:
        url: The link target (URL, bookmark, or reference)
        display_text: The visible text of the link
        link_type: Type of link (web_url, mailto, bookmark, file_path, etc.)
        paragraph_index: Index of paragraph containing the link
        paragraph_text: Full text of the containing paragraph
        is_field_code: Whether link was from a HYPERLINK field code
    """
    url: str
    display_text: str = ""
    link_type: str = "unknown"
    paragraph_index: int = 0
    paragraph_text: str = ""
    is_field_code: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'display_text': self.display_text,
            'link_type': self.link_type,
            'paragraph_index': self.paragraph_index,
            'paragraph_text': self.paragraph_text,
            'is_field_code': self.is_field_code
        }


@dataclass
class DocumentStructure:
    """
    Document structure extracted from DOCX for validation.

    Attributes:
        bookmarks: List of bookmark names defined in the document
        sections: Dict mapping section numbers to titles
        tables: List of table numbers/captions
        figures: List of figure numbers/captions
        appendices: List of appendix letters/titles
        chapters: List of chapter numbers/titles
        paragraphs: List of paragraph numbers (if numbered)
    """
    bookmarks: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)
    appendices: List[str] = field(default_factory=list)
    chapters: List[str] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'bookmarks': self.bookmarks,
            'sections': self.sections,
            'tables': self.tables,
            'figures': self.figures,
            'appendices': self.appendices,
            'chapters': self.chapters,
            'paragraphs': self.paragraphs
        }


@dataclass
class DocxExtractionResult:
    """
    Complete result of DOCX extraction.

    Attributes:
        links: List of extracted hyperlinks
        structure: Document structure for validation
        metadata: Document metadata
        errors: Any errors encountered during extraction
    """
    links: List[ExtractedLink] = field(default_factory=list)
    structure: DocumentStructure = field(default_factory=DocumentStructure)
    metadata: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'links': [link.to_dict() for link in self.links],
            'structure': self.structure.to_dict(),
            'metadata': self.metadata,
            'errors': self.errors
        }


class DocxExtractor:
    """
    Extract hyperlinks and structure from DOCX files.

    Usage:
        extractor = DocxExtractor()
        result = extractor.extract("document.docx")

        for link in result.links:
            print(f"{link.url} ({link.link_type})")
    """

    def __init__(self):
        self.relationships = {}  # rId -> target URL mapping

    def extract(self, file_path: str) -> DocxExtractionResult:
        """
        Extract all hyperlinks and structure from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            DocxExtractionResult with links, structure, and any errors
        """
        result = DocxExtractionResult()

        try:
            # Verify file exists
            path = Path(file_path)
            if not path.exists():
                result.errors.append(f"File not found: {file_path}")
                return result

            # Verify it's a valid DOCX (ZIP file)
            if not zipfile.is_zipfile(file_path):
                result.errors.append("File is not a valid DOCX document")
                return result

            with zipfile.ZipFile(file_path, 'r') as docx:
                # Load relationships (maps rId to URLs)
                self._load_relationships(docx)

                # Extract from main document
                if 'word/document.xml' in docx.namelist():
                    doc_xml = docx.read('word/document.xml')
                    self._extract_from_document(doc_xml, result)

                # Extract metadata
                if 'docProps/core.xml' in docx.namelist():
                    core_xml = docx.read('docProps/core.xml')
                    self._extract_metadata(core_xml, result)

        except zipfile.BadZipFile:
            result.errors.append("Corrupted DOCX file (invalid ZIP format)")
        except Exception as e:
            result.errors.append(f"Extraction error: {str(e)}")

        return result

    def _load_relationships(self, docx: zipfile.ZipFile):
        """Load document relationships (rId to URL mapping)."""
        self.relationships = {}

        try:
            if 'word/_rels/document.xml.rels' in docx.namelist():
                rels_xml = docx.read('word/_rels/document.xml.rels')
                root = ET.fromstring(rels_xml)

                for rel in root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                    rid = rel.get('Id', '')
                    target = rel.get('Target', '')
                    rel_type = rel.get('Type', '')

                    # Only store hyperlink relationships
                    if 'hyperlink' in rel_type.lower():
                        self.relationships[rid] = target
        except Exception:
            pass

    def _extract_from_document(self, doc_xml: bytes, result: DocxExtractionResult):
        """Extract links and structure from document.xml."""
        try:
            root = ET.fromstring(doc_xml)
        except ET.ParseError as e:
            result.errors.append(f"XML parse error: {str(e)}")
            return

        # Register namespaces
        for prefix, uri in NAMESPACES.items():
            ET.register_namespace(prefix, uri)

        # Find body
        body = root.find('.//w:body', NAMESPACES)
        if body is None:
            result.errors.append("Could not find document body")
            return

        paragraph_index = 0

        for element in body:
            # Process paragraphs
            if element.tag == f"{{{NAMESPACES['w']}}}p":
                self._process_paragraph(element, paragraph_index, result)
                paragraph_index += 1

            # Process tables (they may contain hyperlinks too)
            elif element.tag == f"{{{NAMESPACES['w']}}}tbl":
                for row in element.findall('.//w:tr', NAMESPACES):
                    for cell in row.findall('.//w:tc', NAMESPACES):
                        for para in cell.findall('.//w:p', NAMESPACES):
                            self._process_paragraph(para, paragraph_index, result)
                            paragraph_index += 1

    def _process_paragraph(self, para: ET.Element, index: int, result: DocxExtractionResult):
        """Process a paragraph element for hyperlinks and structure."""
        # Get full paragraph text
        para_text = self._get_paragraph_text(para)

        # Extract hyperlinks from <w:hyperlink> elements
        for hyperlink in para.findall('.//w:hyperlink', NAMESPACES):
            link = self._extract_hyperlink_element(hyperlink, index, para_text)
            if link:
                result.links.append(link)

        # Extract HYPERLINK field codes
        field_links = self._extract_field_hyperlinks(para, index, para_text)
        result.links.extend(field_links)

        # Extract bookmarks
        for bookmark_start in para.findall('.//w:bookmarkStart', NAMESPACES):
            name = bookmark_start.get(f"{{{NAMESPACES['w']}}}name", '')
            if name and name not in result.structure.bookmarks:
                # Skip internal Word bookmarks
                if not name.startswith('_'):
                    result.structure.bookmarks.append(name)

        # Detect section headings, tables, figures
        self._detect_structure_elements(para_text, result.structure)

    def _get_paragraph_text(self, para: ET.Element) -> str:
        """Extract all text from a paragraph."""
        texts = []
        for text_elem in para.findall('.//w:t', NAMESPACES):
            if text_elem.text:
                texts.append(text_elem.text)
        return ''.join(texts)

    def _extract_hyperlink_element(
        self,
        hyperlink: ET.Element,
        para_index: int,
        para_text: str
    ) -> Optional[ExtractedLink]:
        """Extract link from a <w:hyperlink> element."""
        # Get relationship ID or anchor
        rid = hyperlink.get(f"{{{NAMESPACES['r']}}}id", '')
        anchor = hyperlink.get(f"{{{NAMESPACES['w']}}}anchor", '')

        # Determine URL
        url = ""
        if rid and rid in self.relationships:
            url = self.relationships[rid]
        elif anchor:
            url = f"#{anchor}"

        if not url:
            return None

        # Get display text
        display_text = ''
        for text_elem in hyperlink.findall('.//w:t', NAMESPACES):
            if text_elem.text:
                display_text += text_elem.text

        # Classify link type
        link_type = self._classify_link_type(url)

        return ExtractedLink(
            url=url,
            display_text=display_text,
            link_type=link_type,
            paragraph_index=para_index,
            paragraph_text=para_text[:200] if len(para_text) > 200 else para_text,
            is_field_code=False
        )

    def _extract_field_hyperlinks(
        self,
        para: ET.Element,
        para_index: int,
        para_text: str
    ) -> List[ExtractedLink]:
        """Extract hyperlinks from HYPERLINK field codes."""
        links = []

        # Look for field codes
        # HYPERLINK fields look like: HYPERLINK "url" or HYPERLINK \l "bookmark"
        field_code_text = ""
        in_field = False

        for elem in para.iter():
            # Field begin
            if elem.tag == f"{{{NAMESPACES['w']}}}fldChar":
                fld_type = elem.get(f"{{{NAMESPACES['w']}}}fldCharType", '')
                if fld_type == 'begin':
                    in_field = True
                    field_code_text = ""
                elif fld_type == 'end':
                    # Process the field code
                    if field_code_text.strip().upper().startswith('HYPERLINK'):
                        link = self._parse_hyperlink_field(field_code_text, para_index, para_text)
                        if link:
                            links.append(link)
                    in_field = False

            # Field instruction text
            if in_field and elem.tag == f"{{{NAMESPACES['w']}}}instrText":
                if elem.text:
                    field_code_text += elem.text

        return links

    def _parse_hyperlink_field(
        self,
        field_code: str,
        para_index: int,
        para_text: str
    ) -> Optional[ExtractedLink]:
        """Parse a HYPERLINK field code to extract URL."""
        # Examples:
        # HYPERLINK "https://example.com"
        # HYPERLINK \l "bookmark_name"
        # HYPERLINK "https://example.com" \t "_blank"

        # Check for local bookmark
        is_local = '\\l' in field_code.lower()

        # Extract URL from quotes
        url_match = re.search(r'"([^"]+)"', field_code)
        if not url_match:
            return None

        url = url_match.group(1)

        # If local bookmark, add # prefix
        if is_local and not url.startswith('#'):
            url = f"#{url}"

        link_type = self._classify_link_type(url)

        return ExtractedLink(
            url=url,
            display_text="",  # Field result text is separate
            link_type=link_type,
            paragraph_index=para_index,
            paragraph_text=para_text[:200] if len(para_text) > 200 else para_text,
            is_field_code=True
        )

    def _classify_link_type(self, url: str) -> str:
        """Classify a URL/link into its type."""
        url_lower = url.lower()

        if url.startswith('#'):
            return 'bookmark'
        elif url_lower.startswith('mailto:'):
            return 'mailto'
        elif url_lower.startswith(('http://', 'https://')):
            return 'web_url'
        elif url_lower.startswith('ftp://'):
            return 'ftp'
        elif url.startswith('\\\\') or url.startswith('//'):
            return 'network_path'
        elif re.match(r'^[A-Za-z]:\\', url):
            return 'file_path'
        elif url.startswith(('./','../')):
            return 'file_path'
        elif re.match(r'^(Section|Table|Figure|Appendix|Chapter)\s+', url, re.IGNORECASE):
            return 'cross_ref'
        else:
            return 'unknown'

    def _detect_structure_elements(self, text: str, structure: DocumentStructure):
        """Detect section headings, table captions, etc. from paragraph text."""
        if not text:
            return

        text_stripped = text.strip()

        # Section patterns (e.g., "1. Introduction", "1.2.3 Details")
        section_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', text_stripped)
        if section_match:
            num = section_match.group(1)
            title = section_match.group(2)
            structure.sections[num] = title

        # Chapter patterns
        chapter_match = re.match(r'^Chapter\s+(\d+)[\s:.]?\s*(.*)$', text_stripped, re.IGNORECASE)
        if chapter_match:
            num = chapter_match.group(1)
            structure.chapters.append(num)

        # Table patterns (e.g., "Table 1: Description", "Table 1 - Description")
        table_match = re.match(r'^Table\s+(\d+)[\s:.-]?\s*(.*)$', text_stripped, re.IGNORECASE)
        if table_match:
            num = table_match.group(1)
            if num not in structure.tables:
                structure.tables.append(num)

        # Figure patterns
        figure_match = re.match(r'^Figure\s+(\d+)[\s:.-]?\s*(.*)$', text_stripped, re.IGNORECASE)
        if figure_match:
            num = figure_match.group(1)
            if num not in structure.figures:
                structure.figures.append(num)

        # Appendix patterns
        appendix_match = re.match(r'^Appendix\s+([A-Z])[\s:.-]?\s*(.*)$', text_stripped, re.IGNORECASE)
        if appendix_match:
            letter = appendix_match.group(1).upper()
            if letter not in structure.appendices:
                structure.appendices.append(letter)

    def _extract_metadata(self, core_xml: bytes, result: DocxExtractionResult):
        """Extract document metadata from core.xml."""
        try:
            root = ET.fromstring(core_xml)

            # Common metadata fields
            dc_ns = 'http://purl.org/dc/elements/1.1/'
            cp_ns = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'

            # Title
            title = root.find(f'.//{{{dc_ns}}}title')
            if title is not None and title.text:
                result.metadata['title'] = title.text

            # Creator
            creator = root.find(f'.//{{{dc_ns}}}creator')
            if creator is not None and creator.text:
                result.metadata['author'] = creator.text

            # Last modified by
            last_mod = root.find(f'.//{{{cp_ns}}}lastModifiedBy')
            if last_mod is not None and last_mod.text:
                result.metadata['last_modified_by'] = last_mod.text

        except Exception:
            pass  # Metadata is optional


def extract_docx_links(file_path: str) -> Tuple[List[Dict], Dict, List[str]]:
    """
    Convenience function to extract links from a DOCX file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Tuple of (links_list, structure_dict, errors_list)
    """
    extractor = DocxExtractor()
    result = extractor.extract(file_path)

    links = [link.to_dict() for link in result.links]
    structure = result.structure.to_dict()
    errors = result.errors

    return links, structure, errors


def get_urls_from_docx(file_path: str) -> List[str]:
    """
    Get just the URLs from a DOCX file (for simple validation).

    Args:
        file_path: Path to the DOCX file

    Returns:
        List of URL strings
    """
    extractor = DocxExtractor()
    result = extractor.extract(file_path)

    return [link.url for link in result.links if link.url]
