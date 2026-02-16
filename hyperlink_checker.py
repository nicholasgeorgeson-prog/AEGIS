#!/usr/bin/env python3
"""
Hyperlink Checker v2.0.0 (Comprehensive Offline)
================================================
Validates all types of hyperlinks in Word documents without external connections.

Checks:
- Internal document bookmarks (#bookmark)
- Cross-references (Section X.X, Table X, Figure X)
- File path links (relative and absolute)
- Network share paths (\\\\server\\share\\path)
- Mailto links (format validation)
- URL format validation (syntax only, no HTTP)
- Embedded hyperlinks in DOCX

Author: AEGIS
"""

import os
import re
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from xml.etree import ElementTree as ET
from urllib.parse import urlparse, unquote
import email.utils

try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Unknown"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._errors = []
        def create_issue(self, **kwargs):
            kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
            return kwargs
        def safe_check(self, *args, **kwargs):
            try:
                return self.check(*args, **kwargs)
            except Exception as e:
                self._errors.append(str(e))
                return []

__version__ = "2.5.0"

# XML namespaces for DOCX
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}


class HyperlinkChecker(BaseChecker):
    """
    Comprehensive hyperlink validation for Word documents.
    
    Validates:
    - Internal bookmarks and anchors
    - Cross-references to sections, tables, figures
    - File paths (local and network)
    - Mailto links
    - URL syntax
    """
    
    CHECKER_NAME = "Hyperlinks"
    CHECKER_VERSION = "2.0.0"
    
    # Patterns for cross-references
    SECTION_REF_PATTERN = re.compile(
        r'\b(?:Section|Sect\.?|§)\s*(\d+(?:\.\d+)*)',
        re.IGNORECASE
    )
    TABLE_REF_PATTERN = re.compile(
        r'\bTable\s+(\d+(?:\.\d+)?(?:-\d+)?)',
        re.IGNORECASE
    )
    FIGURE_REF_PATTERN = re.compile(
        r'\b(?:Figure|Fig\.?)\s+(\d+(?:\.\d+)?(?:-\d+)?)',
        re.IGNORECASE
    )
    APPENDIX_REF_PATTERN = re.compile(
        r'\bAppendix\s+([A-Z](?:\.\d+)?)',
        re.IGNORECASE
    )
    
    # Heading patterns for section detection
    HEADING_PATTERNS = [
        re.compile(r'^(\d+(?:\.\d+)*)\s+[A-Z]'),  # 1.2.3 Title
        re.compile(r'^(\d+(?:\.\d+)*)\.\s+[A-Z]'),  # 1.2.3. Title
        re.compile(r'^Section\s+(\d+(?:\.\d+)*)'),  # Section 1.2
    ]
    
    def __init__(
        self,
        enabled: bool = True,
        check_file_exists: bool = True,
        check_network_paths: bool = True,
        validate_mailto: bool = True,
        validate_url_syntax: bool = True,
        check_cross_references: bool = True,
        base_path: Optional[str] = None
    ):
        super().__init__(enabled)
        self.check_file_exists = check_file_exists
        self.check_network_paths = check_network_paths
        self.validate_mailto = validate_mailto
        self.validate_url_syntax = validate_url_syntax
        self.check_cross_references = check_cross_references
        self.base_path = base_path
        
        # Cache for document structure
        self._bookmarks: Set[str] = set()
        self._sections: Set[str] = set()
        self._tables: Set[str] = set()
        self._figures: Set[str] = set()
        self._appendices: Set[str] = set()
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """
        Check all hyperlinks and cross-references.
        
        Args:
            paragraphs: List of (index, text) tuples
            **kwargs: May include 'filepath' for DOCX analysis,
                     'hyperlinks' for pre-extracted links,
                     'bookmarks' for document bookmarks,
                     'headings' for section headings,
                     'tables' for table captions,
                     'figures' for figure captions
        """
        if not self.enabled:
            return []
        
        issues = []
        filepath = kwargs.get('filepath', '')
        
        # Set base path for relative link resolution
        if filepath and not self.base_path:
            self.base_path = os.path.dirname(os.path.abspath(filepath))
        
        # Build document structure from paragraphs
        self._build_document_structure(paragraphs, kwargs)
        
        # Extract hyperlinks from DOCX if filepath provided
        docx_hyperlinks = []
        if filepath and os.path.exists(filepath):
            docx_hyperlinks = self._extract_docx_hyperlinks(filepath)
        
        # Also use any pre-extracted hyperlinks
        pre_extracted = kwargs.get('hyperlinks', [])
        
        # Combine all hyperlinks
        all_hyperlinks = docx_hyperlinks + pre_extracted
        
        # Validate each hyperlink
        for link_info in all_hyperlinks:
            link_issues = self._validate_hyperlink(link_info, paragraphs)
            issues.extend(link_issues)
        
        # Check cross-references in text
        if self.check_cross_references:
            xref_issues = self._check_cross_references(paragraphs)
            issues.extend(xref_issues)
        
        return issues
    
    def _build_document_structure(
        self,
        paragraphs: List[Tuple[int, str]],
        kwargs: Dict
    ):
        """Build internal maps of document structure."""
        self._bookmarks = set(kwargs.get('bookmarks', []))
        self._sections = set()
        self._tables = set()
        self._figures = set()
        self._appendices = set()
        
        # Extract sections from headings
        headings = kwargs.get('headings', [])
        for heading in headings:
            if isinstance(heading, dict):
                text = heading.get('text', '')
            else:
                text = str(heading)
            
            for pattern in self.HEADING_PATTERNS:
                match = pattern.match(text)
                if match:
                    self._sections.add(match.group(1))
                    break
        
        # Also scan paragraphs for section numbers
        for idx, text in paragraphs:
            # Check for section headings
            for pattern in self.HEADING_PATTERNS:
                match = pattern.match(text.strip())
                if match:
                    self._sections.add(match.group(1))
            
            # Check for table captions
            table_match = re.match(r'^Table\s+(\d+(?:\.\d+)?(?:-\d+)?)[.:\s]', text, re.IGNORECASE)
            if table_match:
                self._tables.add(table_match.group(1))
            
            # Check for figure captions
            fig_match = re.match(r'^(?:Figure|Fig\.?)\s+(\d+(?:\.\d+)?(?:-\d+)?)[.:\s]', text, re.IGNORECASE)
            if fig_match:
                self._figures.add(fig_match.group(1))
            
            # Check for appendix headings
            app_match = re.match(r'^Appendix\s+([A-Z](?:\.\d+)?)[.:\s]', text, re.IGNORECASE)
            if app_match:
                self._appendices.add(app_match.group(1).upper())
        
        # Use pre-extracted tables/figures if provided
        if 'tables' in kwargs:
            for t in kwargs['tables']:
                if isinstance(t, dict) and 'number' in t:
                    self._tables.add(str(t['number']))
        
        if 'figures' in kwargs:
            for f in kwargs['figures']:
                if isinstance(f, dict) and 'number' in f:
                    self._figures.add(str(f['number']))
    
    def _extract_docx_hyperlinks(self, filepath: str) -> List[Dict]:
        """Extract all hyperlinks from a DOCX file."""
        hyperlinks = []
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Get relationships for hyperlink targets
                rels = {}
                if 'word/_rels/document.xml.rels' in zf.namelist():
                    with zf.open('word/_rels/document.xml.rels') as f:
                        rels_tree = ET.parse(f)
                        for rel in rels_tree.findall('.//{%s}Relationship' % NAMESPACES['rel']):
                            rel_id = rel.get('Id', '')
                            target = rel.get('Target', '')
                            rel_type = rel.get('Type', '')
                            if 'hyperlink' in rel_type.lower():
                                rels[rel_id] = target
                
                # Parse document.xml for hyperlinks
                if 'word/document.xml' in zf.namelist():
                    with zf.open('word/document.xml') as f:
                        doc_tree = ET.parse(f)
                        
                        # Find all hyperlink elements
                        for hyperlink in doc_tree.iter('{%s}hyperlink' % NAMESPACES['w']):
                            link_info = self._parse_hyperlink_element(hyperlink, rels)
                            if link_info:
                                hyperlinks.append(link_info)
                        
                        # Also extract bookmarks for internal link validation
                        for bookmark in doc_tree.iter('{%s}bookmarkStart' % NAMESPACES['w']):
                            name = bookmark.get('{%s}name' % NAMESPACES['w'], '')
                            if name and not name.startswith('_'):
                                self._bookmarks.add(name)
                
        except Exception as e:
            self._errors.append(f"Error extracting hyperlinks: {e}")
        
        return hyperlinks
    
    def _parse_hyperlink_element(self, element: ET.Element, rels: Dict) -> Optional[Dict]:
        """Parse a hyperlink XML element."""
        # Get relationship ID for external links
        rel_id = element.get('{%s}id' % NAMESPACES['r'], '')
        
        # Get anchor for internal links
        anchor = element.get('{%s}anchor' % NAMESPACES['w'], '')
        
        # Get display text
        display_text = ''
        for t in element.iter('{%s}t' % NAMESPACES['w']):
            if t.text:
                display_text += t.text
        
        target = ''
        link_type = 'unknown'
        
        if rel_id and rel_id in rels:
            target = rels[rel_id]
            link_type = self._classify_link(target)
        elif anchor:
            target = f'#{anchor}'
            link_type = 'internal_bookmark'
        
        if target or anchor:
            return {
                'target': target,
                'anchor': anchor,
                'display_text': display_text.strip(),
                'link_type': link_type,
                'rel_id': rel_id
            }
        
        return None
    
    def _classify_link(self, target: str) -> str:
        """Classify the type of hyperlink."""
        if not target:
            return 'empty'
        
        target_lower = target.lower()
        
        if target.startswith('#'):
            return 'internal_bookmark'
        elif target.startswith('mailto:'):
            return 'mailto'
        elif target.startswith('\\\\') or target.startswith('//'):
            return 'network_path'
        elif target_lower.startswith(('http://', 'https://')):
            return 'web_url'
        elif target_lower.startswith('file:'):
            return 'file_url'
        elif target_lower.startswith('ftp://'):
            return 'ftp_url'
        elif re.match(r'^[a-zA-Z]:[/\\]', target):
            return 'absolute_path'
        elif re.match(r'^\.{0,2}[/\\]', target) or '/' in target or '\\' in target:
            return 'relative_path'
        else:
            return 'other'
    
    def _validate_hyperlink(
        self,
        link_info: Dict,
        paragraphs: List[Tuple[int, str]]
    ) -> List[Dict]:
        """Validate a single hyperlink."""
        issues = []
        
        target = link_info.get('target', '')
        anchor = link_info.get('anchor', '')
        display_text = link_info.get('display_text', '')
        link_type = link_info.get('link_type', '')
        
        # Find paragraph containing this link for context
        para_idx = 0
        context = display_text[:50] if display_text else target[:50]
        for idx, text in paragraphs:
            if display_text and display_text in text:
                para_idx = idx
                context = text[:60]
                break
        
        # Validate based on link type
        if link_type == 'internal_bookmark':
            bookmark_name = anchor or target.lstrip('#')
            if bookmark_name and bookmark_name not in self._bookmarks:
                # Check if it might be a heading reference
                if not self._is_valid_heading_reference(bookmark_name):
                    issues.append(self.create_issue(
                        severity='High',
                        message=f'Broken internal link: bookmark "{bookmark_name}" not found',
                        context=context,
                        paragraph_index=para_idx,
                        suggestion='Verify the bookmark exists or update the link',
                        rule_id='HL001',
                        flagged_text=display_text or target
                    ))
        
        elif link_type == 'mailto':
            mailto_issues = self._validate_mailto(target, display_text, para_idx, context)
            issues.extend(mailto_issues)
        
        elif link_type == 'network_path':
            if self.check_network_paths:
                path_issues = self._validate_network_path(target, display_text, para_idx, context)
                issues.extend(path_issues)
        
        elif link_type in ('absolute_path', 'relative_path', 'file_url'):
            if self.check_file_exists:
                path_issues = self._validate_file_path(target, display_text, para_idx, context)
                issues.extend(path_issues)
        
        elif link_type == 'web_url':
            if self.validate_url_syntax:
                url_issues = self._validate_url_syntax(target, display_text, para_idx, context)
                issues.extend(url_issues)
        
        elif link_type == 'empty':
            issues.append(self.create_issue(
                severity='High',
                message='Empty hyperlink target',
                context=context,
                paragraph_index=para_idx,
                suggestion='Add a valid link target or remove the hyperlink',
                rule_id='HL002',
                flagged_text=display_text or '[empty link]'
            ))
        
        # Check for display text issues
        if target and not display_text:
            issues.append(self.create_issue(
                severity='Low',
                message='Hyperlink has no display text',
                context=f'Link to: {target[:40]}',
                paragraph_index=para_idx,
                suggestion='Add descriptive text for the hyperlink',
                rule_id='HL003',
                flagged_text=target[:30]
            ))
        
        return issues
    
    def _is_valid_heading_reference(self, bookmark_name: str) -> bool:
        """Check if bookmark might be a valid heading reference."""
        # Word often creates bookmarks like "_Toc123456" or "_Ref123456"
        if bookmark_name.startswith(('_Toc', '_Ref', '_Hlt')):
            return True
        
        # Check if it matches a section pattern
        if re.match(r'^\d+(?:\.\d+)*$', bookmark_name):
            return bookmark_name in self._sections
        
        return False
    
    def _validate_mailto(
        self,
        target: str,
        display_text: str,
        para_idx: int,
        context: str
    ) -> List[Dict]:
        """Validate a mailto link."""
        issues = []
        
        if not self.validate_mailto:
            return issues
        
        # Extract email from mailto:
        email_part = target[7:] if target.lower().startswith('mailto:') else target
        
        # Handle mailto with parameters (subject, body, etc.)
        email_address = email_part.split('?')[0]
        
        # Basic email format validation
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        if not email_address:
            issues.append(self.create_issue(
                severity='High',
                message='Empty mailto link',
                context=context,
                paragraph_index=para_idx,
                suggestion='Add a valid email address',
                rule_id='HL010',
                flagged_text=display_text or target
            ))
        elif not email_pattern.match(email_address):
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Invalid email format: "{email_address}"',
                context=context,
                paragraph_index=para_idx,
                suggestion='Verify the email address format',
                rule_id='HL011',
                flagged_text=email_address
            ))
        
        return issues
    
    def _validate_network_path(
        self,
        target: str,
        display_text: str,
        para_idx: int,
        context: str
    ) -> List[Dict]:
        """Validate a network path (UNC path)."""
        issues = []
        
        # Normalize path
        path = target.replace('/', '\\')
        
        # Check UNC path format
        unc_pattern = re.compile(r'^\\\\[a-zA-Z0-9._-]+\\[a-zA-Z0-9._$ -]+')
        
        if not unc_pattern.match(path):
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Invalid network path format: "{target[:40]}"',
                context=context,
                paragraph_index=para_idx,
                suggestion='Network paths should be \\\\server\\share\\path',
                rule_id='HL020',
                flagged_text=display_text or target[:30]
            ))
        else:
            # Try to check if path exists (may fail due to permissions)
            try:
                if os.path.exists(path):
                    pass  # Path exists, no issue
                else:
                    issues.append(self.create_issue(
                        severity='High',
                        message=f'Network path not accessible: "{target[:40]}"',
                        context=context,
                        paragraph_index=para_idx,
                        suggestion='Verify the network path exists and is accessible',
                        rule_id='HL021',
                        flagged_text=display_text or target[:30]
                    ))
            except (OSError, PermissionError):
                # Can't check, might be permission issue
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Cannot verify network path: "{target[:40]}"',
                    context=context,
                    paragraph_index=para_idx,
                    suggestion='Manually verify the network path is accessible',
                    rule_id='HL022',
                    flagged_text=display_text or target[:30]
                ))
        
        return issues
    
    def _validate_file_path(
        self,
        target: str,
        display_text: str,
        para_idx: int,
        context: str
    ) -> List[Dict]:
        """Validate a file path link."""
        issues = []
        
        # Handle file:// URLs
        path = target
        if target.lower().startswith('file:'):
            path = target[5:]
            if path.startswith('///'):
                path = path[3:]
            elif path.startswith('//'):
                path = path[2:]
            path = unquote(path)  # Decode URL encoding
        
        # Normalize path separators
        path = path.replace('/', os.sep).replace('\\', os.sep)
        
        # Resolve relative paths
        if self.base_path and not os.path.isabs(path):
            path = os.path.join(self.base_path, path)
        
        # Check if file exists
        try:
            path = os.path.normpath(path)
            if os.path.exists(path):
                pass  # File exists
            else:
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Linked file not found: "{os.path.basename(path)}"',
                    context=context,
                    paragraph_index=para_idx,
                    suggestion=f'Verify file exists at: {path[:60]}',
                    rule_id='HL030',
                    flagged_text=display_text or target[:30]
                ))
        except (OSError, ValueError) as e:
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Invalid file path: "{target[:40]}"',
                context=context,
                paragraph_index=para_idx,
                suggestion='Check the file path format',
                rule_id='HL031',
                flagged_text=display_text or target[:30]
            ))
        
        return issues
    
    def _validate_url_syntax(
        self,
        target: str,
        display_text: str,
        para_idx: int,
        context: str
    ) -> List[Dict]:
        """Validate URL syntax (without making HTTP requests)."""
        issues = []
        
        try:
            parsed = urlparse(target)
            
            # Check for required components
            if not parsed.scheme:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'URL missing scheme (http/https): "{target[:40]}"',
                    context=context,
                    paragraph_index=para_idx,
                    suggestion='Add http:// or https:// prefix',
                    rule_id='HL040',
                    flagged_text=display_text or target[:30]
                ))
            
            if not parsed.netloc:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'URL missing domain: "{target[:40]}"',
                    context=context,
                    paragraph_index=para_idx,
                    suggestion='Add a valid domain name',
                    rule_id='HL041',
                    flagged_text=display_text or target[:30]
                ))
            
            # Check for common URL typos
            if parsed.netloc:
                domain = parsed.netloc.lower()
                
                # Check for spaces (invalid)
                if ' ' in target:
                    issues.append(self.create_issue(
                        severity='High',
                        message='URL contains spaces (invalid)',
                        context=context,
                        paragraph_index=para_idx,
                        suggestion='Remove spaces or encode as %20',
                        rule_id='HL042',
                        flagged_text=display_text or target[:30]
                    ))
                
                # Check for double slashes (except after scheme)
                if '//' in parsed.path:
                    issues.append(self.create_issue(
                        severity='Low',
                        message='URL contains double slashes in path',
                        context=context,
                        paragraph_index=para_idx,
                        suggestion='Check for typos in the URL path',
                        rule_id='HL043',
                        flagged_text=display_text or target[:30]
                    ))
        
        except Exception as e:
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Cannot parse URL: "{target[:40]}"',
                context=context,
                paragraph_index=para_idx,
                suggestion='Verify the URL format',
                rule_id='HL044',
                flagged_text=display_text or target[:30]
            ))
        
        return issues
    
    def _check_cross_references(
        self,
        paragraphs: List[Tuple[int, str]]
    ) -> List[Dict]:
        """Check cross-references in document text."""
        issues = []
        
        for idx, text in paragraphs:
            # Check section references
            for match in self.SECTION_REF_PATTERN.finditer(text):
                section_num = match.group(1)
                if section_num not in self._sections:
                    # Check if it might be a partial match
                    if not any(s.startswith(section_num) or section_num.startswith(s) 
                              for s in self._sections):
                        issues.append(self.create_issue(
                            severity='High',
                            message=f'Reference to non-existent section: "{section_num}"',
                            context=text[max(0, match.start()-10):match.end()+20],
                            paragraph_index=idx,
                            suggestion='Verify section number exists in document',
                            rule_id='HL050',
                            flagged_text=match.group(0)
                        ))
            
            # Check table references
            for match in self.TABLE_REF_PATTERN.finditer(text):
                table_num = match.group(1)
                if table_num not in self._tables:
                    # Don't flag if we found no tables at all (might be external ref)
                    if self._tables:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to non-existent table: "Table {table_num}"',
                            context=text[max(0, match.start()-10):match.end()+20],
                            paragraph_index=idx,
                            suggestion='Verify table number exists in document',
                            rule_id='HL051',
                            flagged_text=match.group(0)
                        ))
            
            # Check figure references
            for match in self.FIGURE_REF_PATTERN.finditer(text):
                fig_num = match.group(1)
                if fig_num not in self._figures:
                    # Don't flag if we found no figures at all
                    if self._figures:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to non-existent figure: "Figure {fig_num}"',
                            context=text[max(0, match.start()-10):match.end()+20],
                            paragraph_index=idx,
                            suggestion='Verify figure number exists in document',
                            rule_id='HL052',
                            flagged_text=match.group(0)
                        ))
            
            # Check appendix references
            for match in self.APPENDIX_REF_PATTERN.finditer(text):
                app_id = match.group(1).upper()
                if app_id not in self._appendices:
                    if self._appendices:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to non-existent appendix: "Appendix {app_id}"',
                            context=text[max(0, match.start()-10):match.end()+20],
                            paragraph_index=idx,
                            suggestion='Verify appendix exists in document',
                            rule_id='HL053',
                            flagged_text=match.group(0)
                        ))
        
        return issues


# Convenience function
def check_hyperlinks(filepath: str, **kwargs) -> List[Dict]:
    """Check hyperlinks in a document file."""
    checker = HyperlinkChecker()
    
    # Extract paragraphs from file if not provided
    paragraphs = kwargs.get('paragraphs', [])
    if not paragraphs and os.path.exists(filepath):
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if 'word/document.xml' in zf.namelist():
                    with zf.open('word/document.xml') as f:
                        tree = ET.parse(f)
                        idx = 0
                        for para in tree.iter('{%s}p' % NAMESPACES['w']):
                            text_parts = []
                            for t in para.iter('{%s}t' % NAMESPACES['w']):
                                if t.text:
                                    text_parts.append(t.text)
                            if text_parts:
                                paragraphs.append((idx, ''.join(text_parts)))
                                idx += 1
        except Exception:
            pass
    
    kwargs['paragraphs'] = paragraphs
    kwargs['filepath'] = filepath
    
    return checker.check(paragraphs, **kwargs)


if __name__ == '__main__':
    # Test
    print("Hyperlink Checker v" + __version__)
    print("Run with a DOCX file to test hyperlink validation")
