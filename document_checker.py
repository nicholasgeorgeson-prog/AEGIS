#!/usr/bin/env python3
"""
Document Structure Checker v2.0.0
=================================
Checks document structure and organization:
- Reference validation (sections, tables, figures)
- Heading hierarchy
- Table/figure captions and references
- Unresolved track changes and comments
- Missing standard sections
- Consistency checks (dates, numbers)
"""

import re
import os
import zipfile
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "2.5.0"


class ReferenceChecker(BaseChecker):
    """Validates document references (sections, tables, figures)."""
    
    CHECKER_NAME = "References"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.sections: Set[str] = set()
        self.tables: Set[str] = set()
        self.figures: Set[str] = set()
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        self.sections = set()
        self.tables = set()
        self.figures = set()
        
        # First pass: find all defined sections, tables, figures
        self._find_definitions(paragraphs, tables or [])
        
        # Second pass: find all references
        refs_made = defaultdict(list)  # type -> [(ref_id, para_idx), ...]
        
        ref_patterns = [
            (r'[Ss]ection\s+(\d+(?:\.\d+)*)', 'section'),
            (r'[Ss]ec\.\s*(\d+(?:\.\d+)*)', 'section'),
            (r'§\s*(\d+(?:\.\d+)*)', 'section'),
            (r'[Tt]able\s+(\d+(?:[.-]\d+)*)', 'table'),
            (r'[Ff]igure\s+(\d+(?:[.-]\d+)*)', 'figure'),
            (r'[Ff]ig\.\s*(\d+(?:[.-]\d+)*)', 'figure'),
        ]
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            for pattern, ref_type in ref_patterns:
                for match in re.finditer(pattern, text):
                    ref_id = match.group(1)
                    refs_made[ref_type].append((ref_id, idx, match.group()))
        
        # Check for broken references
        for ref_id, para_idx, full_match in refs_made.get('section', []):
            if ref_id not in self.sections:
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Reference to Section {ref_id} - section not found',
                    context=full_match,
                    paragraph_index=para_idx,
                    suggestion='Verify section number exists or update reference',
                    rule_id='REF001',
                    flagged_text=f'Section {ref_id}'
                ))
        
        for ref_id, para_idx, full_match in refs_made.get('table', []):
            if ref_id not in self.tables:
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Reference to Table {ref_id} - table not found',
                    context=full_match,
                    paragraph_index=para_idx,
                    suggestion='Verify table number exists or update reference',
                    rule_id='REF002',
                    flagged_text=f'Table {ref_id}'
                ))
        
        for ref_id, para_idx, full_match in refs_made.get('figure', []):
            if ref_id not in self.figures:
                issues.append(self.create_issue(
                    severity='High',
                    message=f'Reference to Figure {ref_id} - figure not found',
                    context=full_match,
                    paragraph_index=para_idx,
                    suggestion='Verify figure number exists or update reference',
                    rule_id='REF003',
                    flagged_text=f'Figure {ref_id}'
                ))
        
        return issues
    
    def _find_definitions(self, paragraphs: List[Tuple[int, str]], tables: List[Dict]):
        """Find all section, table, and figure definitions."""
        
        # Find section headings
        section_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s')
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            # Section numbers at start of paragraphs (headings)
            match = section_pattern.match(text.strip())
            if match:
                self.sections.add(match.group(1))
        
        # Tables from table list
        for i, table in enumerate(tables):
            table_num = str(table.get('number', i + 1))
            self.tables.add(table_num)
        
        # Also find table/figure numbers in text - improved patterns
        for idx, text in paragraphs:
            if not text:
                continue
            
            # Table definitions - multiple formats:
            # "Table X:" "Table X." "Table X -" "Table X—" "TABLE X" (standalone)
            # Also captures table captions that might just be "Table 1" at start of line
            for match in re.finditer(r'[Tt][Aa][Bb][Ll][Ee]\s+(\d+(?:[.-]\d+)?)\s*[:.—–\-]?', text):
                self.tables.add(match.group(1))
            
            # Also detect "Table X" at the start of a paragraph (likely a caption)
            start_match = re.match(r'^[Tt][Aa][Bb][Ll][Ee]\s+(\d+(?:[.-]\d+)?)\b', text.strip())
            if start_match:
                self.tables.add(start_match.group(1))
            
            # Figure definitions - similar patterns
            for match in re.finditer(r'[Ff][Ii][Gg][Uu][Rr][Ee]\s+(\d+(?:[.-]\d+)?)\s*[:.—–\-]?', text):
                self.figures.add(match.group(1))
            
            # Also detect "Figure X" at start of paragraph
            fig_start = re.match(r'^[Ff][Ii][Gg][Uu][Rr][Ee]\s+(\d+(?:[.-]\d+)?)\b', text.strip())
            if fig_start:
                self.figures.add(fig_start.group(1))


class DocumentStructureChecker(BaseChecker):
    """Checks document structure and organization."""
    
    CHECKER_NAME = "Document Structure"
    CHECKER_VERSION = "2.0.0"
    
    EXPECTED_SECTIONS = {
        'scope', 'purpose', 'introduction', 'overview', 'background',
        'references', 'definitions', 'acronyms', 'applicable documents'
    }
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        full_text: str = "",
        headings: List[Dict] = None,
        **kwargs
    ) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        headings = headings or []
        
        # Check heading hierarchy
        prev_level = 0
        for heading in headings:
            level = heading.get('level', 0)
            if level > prev_level + 1 and prev_level > 0:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Heading level skipped: jumped from level {prev_level} to {level}',
                    context=heading.get('text', '')[:50],
                    paragraph_index=heading.get('index', 0),
                    suggestion=f'Use Heading {prev_level + 1} before Heading {level}',
                    rule_id='STR001'
                ))
            prev_level = level
        
        # Check for missing critical sections
        if full_text:
            text_lower = full_text.lower()
            
            for section in ['scope', 'purpose']:
                if section not in text_lower:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Document may be missing "{section.title()}" section',
                        context='',
                        paragraph_index=0,
                        suggestion=f'Consider adding a {section.title()} section',
                        rule_id='STR002'
                    ))
        
        return issues


class TableFigureChecker(BaseChecker):
    """Checks tables and figures for captions and references."""
    
    CHECKER_NAME = "Tables/Figures"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        figures: List[Dict] = None,
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        tables = tables or []
        figures = figures or []
        
        # Check tables
        for i, table in enumerate(tables):
            table_num = table.get('number', i + 1)
            start_para = table.get('start_para', 0)
            
            # Check for missing caption
            if not table.get('has_caption') and not table.get('is_acronym_table'):
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Table {table_num} may be missing a title/caption',
                    context=f'Table {table_num}',
                    paragraph_index=start_para,
                    suggestion='Add a descriptive title above the table',
                    rule_id='TBL001',
                    flagged_text=f'Table {table_num}'
                ))
            
            # Check for empty cells
            empty_cells = table.get('empty_cells', 0)
            if empty_cells > 0:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Table {table_num} has {empty_cells} empty cell(s)',
                    context=f'Table {table_num}',
                    paragraph_index=start_para,
                    suggestion='Fill empty cells with data, "N/A", or "-" as appropriate',
                    rule_id='TBL002',
                    flagged_text=f'Table {table_num}'
                ))
            
            # Check if table is referenced in text
            if full_text:
                pattern = rf'\b[Tt]able\s+{table_num}\b'
                if not re.search(pattern, full_text):
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Table {table_num} is not referenced in the text',
                        context=f'Table {table_num}',
                        paragraph_index=start_para,
                        suggestion='Add a reference to this table in the body text',
                        rule_id='TBL003',
                        flagged_text=f'Table {table_num}'
                    ))
        
        # Check figures
        for i, figure in enumerate(figures):
            fig_num = figure.get('number', i + 1)
            fig_para = figure.get('index', 0)
            
            # Check for missing caption
            if not figure.get('has_caption'):
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Figure {fig_num} may be missing a caption',
                    context=f'Figure {fig_num}',
                    paragraph_index=fig_para,
                    suggestion='Add a descriptive caption below the figure',
                    rule_id='FIG001',
                    flagged_text=f'Figure {fig_num}'
                ))
            
            # Check if figure is referenced
            if full_text:
                pattern = rf'\b[Ff]ig(?:ure)?\s*\.?\s*{fig_num}\b'
                if not re.search(pattern, full_text):
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Figure {fig_num} is not referenced in the text',
                        context=f'Figure {fig_num}',
                        paragraph_index=fig_para,
                        suggestion='Add a reference to this figure in the body text',
                        rule_id='FIG002',
                        flagged_text=f'Figure {fig_num}'
                    ))
        
        return issues


class TrackChangesChecker(BaseChecker):
    """Detects unresolved track changes and comments."""
    
    CHECKER_NAME = "Unresolved Changes"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]] = None,
        track_changes: List[Dict] = None,
        comments: List[Dict] = None,
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        track_changes = track_changes or []
        comments = comments or []
        
        # If we have a filepath but no track_changes/comments provided, extract them
        if filepath and not track_changes and not comments:
            track_changes, comments = self._extract_from_file(filepath)
        
        # Check track changes
        if track_changes:
            ins_count = sum(1 for tc in track_changes if tc.get('type') == 'insertion')
            del_count = sum(1 for tc in track_changes if tc.get('type') == 'deletion')
            
            if ins_count > 0 or del_count > 0:
                issues.append(self.create_issue(
                    severity='Critical',
                    message=f'Document has unresolved track changes: {ins_count} insertion(s), {del_count} deletion(s)',
                    context='Track Changes',
                    paragraph_index=0,
                    suggestion='Accept or reject all track changes before finalizing document',
                    rule_id='TRK001',
                    flagged_text='Track Changes'
                ))
        
        # Check comments
        if comments:
            issues.append(self.create_issue(
                severity='High',
                message=f'Document has {len(comments)} unresolved comment(s)',
                context='Comments',
                paragraph_index=0,
                suggestion='Resolve or delete all comments before finalizing document',
                rule_id='TRK002',
                flagged_text='Comments'
            ))
            
            # List first few comments
            for i, comment in enumerate(comments[:3]):
                author = comment.get('author', 'Unknown')
                text = comment.get('text', '')[:40]
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Comment by {author}: "{text}..."' if len(comment.get('text', '')) > 40 else f'Comment by {author}: "{text}"',
                    context=f'Comment {i+1}',
                    paragraph_index=0,
                    suggestion='Resolve this comment',
                    rule_id='TRK003',
                    flagged_text=f'Comment {i+1}'
                ))
        
        return issues
    
    def _extract_from_file(self, filepath: str) -> Tuple[List[Dict], List[Dict]]:
        """Extract track changes and comments from docx file."""
        track_changes = []
        comments = []
        
        if not filepath or not os.path.exists(filepath):
            return track_changes, comments
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Extract track changes from document.xml
                if 'word/document.xml' in zf.namelist():
                    doc_xml = zf.read('word/document.xml').decode('utf-8')
                    
                    # Find insertions
                    for match in re.finditer(r'<w:ins\s[^>]*w:author="([^"]*)"', doc_xml):
                        track_changes.append({'type': 'insertion', 'author': match.group(1)})
                    
                    # Find deletions
                    for match in re.finditer(r'<w:del\s[^>]*w:author="([^"]*)"', doc_xml):
                        track_changes.append({'type': 'deletion', 'author': match.group(1)})
                
                # Extract comments from comments.xml
                if 'word/comments.xml' in zf.namelist():
                    comments_xml = zf.read('word/comments.xml').decode('utf-8')
                    
                    comment_pattern = re.compile(
                        r'<w:comment[^>]*w:author="([^"]*)"[^>]*>(.*?)</w:comment>',
                        re.DOTALL
                    )
                    
                    for match in comment_pattern.finditer(comments_xml):
                        author = match.group(1)
                        content = match.group(2)
                        # Extract text from <w:t> tags
                        text = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content))
                        comments.append({'author': author, 'text': text})
        
        except Exception as e:
            self._errors.append(f"Error extracting track changes: {e}")
        
        return track_changes, comments


class ConsistencyChecker(BaseChecker):
    """Checks for consistency issues (date formats, number formats)."""
    
    CHECKER_NAME = "Consistency"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]] = None,
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        if not full_text:
            full_text = '\n'.join(text for _, text in (paragraphs or []) if text)
        
        # Check date format consistency
        date_formats = {
            'mm/dd/yyyy': re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', full_text),
            'yyyy-mm-dd': re.findall(r'\b\d{4}-\d{2}-\d{2}\b', full_text),
            'month dd, yyyy': re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', full_text),
            'dd month yyyy': re.findall(r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', full_text),
        }
        
        formats_used = {k: v for k, v in date_formats.items() if v}
        if len(formats_used) > 1:
            format_list = ', '.join(f'{k} ({len(v)})' for k, v in formats_used.items())
            issues.append(self.create_issue(
                severity='Low',
                message=f'Multiple date formats used: {format_list}',
                context='Date formats',
                paragraph_index=0,
                suggestion='Use a consistent date format throughout the document',
                rule_id='CON001',
                flagged_text='Date formats'
            ))
        
        # Check number format consistency (1000 vs 1,000)
        numbers_no_comma = re.findall(r'\b\d{4,}\b', full_text)
        numbers_with_comma = re.findall(r'\b\d{1,3}(?:,\d{3})+\b', full_text)
        
        # Filter to only numbers >= 1000 (excluding years)
        large_no_comma = [n for n in numbers_no_comma 
                          if int(n) >= 1000 and not re.match(r'(?:19|20)\d{2}', n)]
        
        if large_no_comma and numbers_with_comma:
            issues.append(self.create_issue(
                severity='Low',
                message='Inconsistent number formatting (some with commas, some without)',
                context='Number formatting',
                paragraph_index=0,
                suggestion='Use consistent number formatting (recommend commas for numbers >= 1,000)',
                rule_id='CON002',
                flagged_text='Number formatting'
            ))
        
        return issues


class ListFormattingChecker(BaseChecker):
    """Checks list formatting for parallel structure and consistency."""
    
    CHECKER_NAME = "List Formatting"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        in_list = False
        list_items = []
        list_start_para = 0
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            text_stripped = text.strip()
            
            # Check if this looks like a list item
            is_list_item = bool(re.match(r'^(?:[-•*]|\d+[.)]|[a-z][.)]|\([a-z]\)|\([0-9]+\))\s', text_stripped))
            
            if is_list_item:
                if not in_list:
                    in_list = True
                    list_start_para = idx
                    list_items = []
                
                # Extract item text without bullet/number
                item_text = re.sub(r'^(?:[-•*]|\d+[.)]|[a-z][.)]|\([a-z]\)|\([0-9]+\))\s*', '', text_stripped)
                list_items.append(item_text)
            else:
                if in_list and len(list_items) >= 2:
                    # Check the completed list
                    list_issues = self._check_list(list_items, list_start_para)
                    issues.extend(list_issues)
                
                in_list = False
                list_items = []
        
        # Check final list if document ends with one
        if in_list and len(list_items) >= 2:
            list_issues = self._check_list(list_items, list_start_para)
            issues.extend(list_issues)
        
        return issues
    
    def _check_list(self, items: List[str], para_idx: int) -> List[Dict]:
        """Check a list for formatting issues."""
        issues = []
        
        if not items:
            return issues
        
        # Get first word of each item
        first_words = []
        for item in items:
            words = item.split()
            if words:
                first_words.append(words[0].lower())
        
        if not first_words:
            return issues
        
        # Check parallel structure (all start with same word form)
        has_ing = sum(1 for w in first_words if w.endswith('ing'))
        if 0 < has_ing < len(first_words):
            issues.append(self.create_issue(
                severity='Low',
                message='List items may not have parallel structure',
                context=', '.join(first_words[:3]),
                paragraph_index=para_idx,
                suggestion='Start each list item with the same grammatical form (e.g., all verbs or all nouns)',
                rule_id='LST001',
                flagged_text=', '.join(first_words[:3])
            ))
        
        # Check punctuation consistency
        ends_with_period = [item.strip().endswith('.') for item in items]
        if any(ends_with_period) and not all(ends_with_period):
            issues.append(self.create_issue(
                severity='Low',
                message='Inconsistent punctuation at end of list items',
                context='List punctuation',
                paragraph_index=para_idx,
                suggestion='Use consistent punctuation (all with periods or none with periods)',
                rule_id='LST002',
                flagged_text='List punctuation'
            ))
        
        return issues
