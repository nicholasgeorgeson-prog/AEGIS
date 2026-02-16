#!/usr/bin/env python3
"""
Punctuation Checker v2.6.0
==========================
Detects punctuation and spacing issues.

v2.6.0 CHANGES:
- Migrated to provenance tracking for extra space and comma splice detection
- Uses create_validated_issue() for PUN001 and PUN002 rules
- Validates flagged text exists in original document

v2.1.0 CHANGES:
- Report each extra space issue INDIVIDUALLY (not consolidated)
- This allows users to select/deselect individual fixes
- Provides context for each occurrence

v2.0.0 (Hardened):
- Validates all inputs
- Catches all exceptions
- Provides fixable issues with replacement text
"""

import re
from typing import List, Tuple, Optional

try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    try:
        from .base_checker import BaseChecker, ReviewIssue
    except ImportError:
        # Minimal fallback
        class BaseChecker:
            CHECKER_NAME = "Unknown"
            def __init__(self, enabled=True):
                self.enabled = enabled
                self._errors = []
            def create_issue(self, **kwargs):
                kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
                return kwargs
            def create_validated_issue(self, **kwargs):
                return self.create_issue(**kwargs)
            def clear_errors(self):
                self._errors = []
        class ReviewIssue:
            pass

__version__ = "2.9.0"


class PunctuationChecker(BaseChecker):
    """
    Detects punctuation and spacing issues.

    Thread-safe and stateless.

    v2.9.0: Consolidated reporting, section number filtering, improved context highlighting
    v2.8.0: Enhanced filtering for tables, lists, code blocks, and leading indentation
    v2.6.0: Uses provenance tracking for issue validation
    """

    CHECKER_NAME = "Punctuation"
    CHECKER_VERSION = "2.9.0"  # v2.9.0: Consolidated reporting, section number filtering
    
    def __init__(
        self,
        enabled: bool = True,
        min_paragraph_length: int = 10,
        check_double_spaces: bool = True,
        check_comma_splices: bool = True
    ):
        super().__init__(enabled)
        self.min_paragraph_length = min_paragraph_length
        self.check_double_spaces = check_double_spaces
        self.check_comma_splices = check_comma_splices
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[ReviewIssue]:
        """
        Check for punctuation issues.
        
        Returns:
            List of ReviewIssue for issues found
        """
        issues = []
        
        if not paragraphs:
            return issues
        
        try:
            for idx, text in paragraphs:
                if not text or not isinstance(text, str):
                    continue
                
                if len(text.strip()) < self.min_paragraph_length:
                    continue
                
                # Check for double/extra spaces - report EACH occurrence individually
                if self.check_double_spaces:
                    space_issues = self._find_extra_spaces(idx, text)
                    issues.extend(space_issues)
                
                # Check comma splices (individual) with provenance tracking
                if self.check_comma_splices:
                    splice_issue = self._check_comma_splice(idx, text)
                    if splice_issue:
                        issues.append(splice_issue)
        
        except Exception as e:
            self._errors.append(f"Punctuation check error: {e}")
        
        return issues
    
    # v2.7.0: Patterns that indicate TOC/table of contents or similar formatted content
    # where extra spacing is intentional and should not be flagged
    TOC_PATTERNS = [
        re.compile(r'\.{3,}'),           # Dotted leaders (...)
        re.compile(r'_{3,}'),            # Underline leaders (___)
        re.compile(r'-{3,}'),            # Dash leaders (---)
        re.compile(r'^\s*\d+\s*$'),      # Standalone page numbers
        re.compile(r'^\s*[A-Z\s]+\s*\.{2,}'),  # ALL CAPS heading with dots
        re.compile(r'\s+\d+\s*$'),       # Trailing page number
    ]

    # v2.8.0: Patterns that indicate formatted/structured content where spacing is intentional
    STRUCTURED_CONTENT_PATTERNS = [
        re.compile(r'^\s{2,}[\•\-\*\→\►\●\○\◆\◇\▪\▫]'),  # Indented bullet lists
        re.compile(r'^\s{2,}\d+[\.\)]\s'),  # Indented numbered lists
        re.compile(r'^\s{2,}[a-z][\.\)]\s'),  # Indented lettered lists
        re.compile(r'^\s{4,}'),           # Code-like indentation (4+ spaces at start)
        re.compile(r'\s{4,}\$[\d,]+'),    # Right-aligned currency
        re.compile(r'\s{4,}\d+[\.\d]*\s*$'),  # Right-aligned numbers at end
        re.compile(r'^[A-Za-z\s]+\s{3,}[A-Za-z\s]+\s{3,}[A-Za-z]'),  # Table headers (3+ cols)
        re.compile(r'\|\s+\w+\s+\|'),     # Table cells with pipes
        re.compile(r'^\s*\|'),            # Lines starting with pipe (table)
    ]

    # v2.9.0: Patterns for section headers where double space after number is intentional
    SECTION_HEADER_PATTERNS = [
        re.compile(r'^\d+\.\d+(\.\d+)*\s{2,}[A-Z]'),  # "4.1  DEVELOP" or "4.1.2  TITLE"
        re.compile(r'^[A-Z]\.\d+\s{2,}[A-Z]'),        # "A.1  APPENDIX TITLE"
        re.compile(r'^\d+\s{2,}[A-Z][A-Z\s]+$'),     # "4  CHAPTER TITLE"
        re.compile(r'^Chapter\s+\d+\s{2,}', re.IGNORECASE),  # "Chapter 4  Title"
        re.compile(r'^Section\s+\d+\s{2,}', re.IGNORECASE),  # "Section 4  Title"
        re.compile(r'^Figure\s+\d+[\.\-]?\d*\s{2,}', re.IGNORECASE),  # "Figure 4.1  Caption"
        re.compile(r'^Table\s+\d+[\.\-]?\d*\s{2,}', re.IGNORECASE),   # "Table 4.1  Caption"
    ]

    def _find_extra_spaces(self, para_idx: int, text: str) -> List[dict]:
        """
        Find extra space occurrences in a paragraph.
        Uses provenance tracking to validate each match.

        Returns list of validated issues.

        v2.9.0: Consolidated reporting - one issue per paragraph with count
        v2.8.0: Enhanced filtering for tables, lists, and code blocks
        """
        issues = []

        # v2.7.0: Skip TOC/table of contents entries where spacing is intentional
        for toc_pattern in self.TOC_PATTERNS:
            if toc_pattern.search(text):
                return issues  # Skip this paragraph entirely

        # v2.8.0: Skip structured content (tables, indented lists, code)
        for struct_pattern in self.STRUCTURED_CONTENT_PATTERNS:
            if struct_pattern.search(text):
                return issues  # Skip this paragraph entirely

        # v2.9.0: Skip section headers where double space is intentional formatting
        for header_pattern in self.SECTION_HEADER_PATTERNS:
            if header_pattern.search(text):
                return issues  # Skip this paragraph entirely

        # Find all double+ space occurrences
        # Pattern matches 2 or more spaces
        pattern = re.compile(r'  +')
        matches = list(pattern.finditer(text))

        # v2.8.0: Filter out leading indentation (spaces at very start of text)
        # These are typically intentional formatting
        filtered_matches = []
        for match in matches:
            # Skip if this is leading whitespace (starts at position 0 or after only whitespace)
            if match.start() == 0:
                continue
            # Skip if everything before this match is whitespace (it's just indentation)
            if text[:match.start()].strip() == '':
                continue
            filtered_matches.append(match)

        matches = filtered_matches

        if not matches:
            return issues

        total_occurrences = len(matches)

        # v2.9.0: CONSOLIDATED REPORTING - Create one issue per paragraph
        # with the first occurrence highlighted but count shown in message
        first_match = matches[0]
        space_count = first_match.end() - first_match.start()

        # Get context around the FIRST match with visible highlighting
        # Use Unicode visible space character or brackets to show the extra space
        chunk_start = max(0, first_match.start() - 25)
        chunk_end = min(len(text), first_match.end() + 25)

        # Build context with visible marker for the extra space
        before_space = text[chunk_start:first_match.start()]
        after_space = text[first_match.end():chunk_end]

        # Use «␣␣» to make the double space visible (␣ is a visible space character)
        visible_spaces = '·' * space_count  # Middle dot to show each extra space
        context_with_highlight = f"...{before_space.strip()}«{visible_spaces}»{after_space.strip()}..."

        # Also provide the raw context for the fix
        original_chunk = text[chunk_start:chunk_end]
        fixed_chunk = re.sub(r'  +', ' ', original_chunk)

        # Create message based on count
        if total_occurrences == 1:
            message = f'Extra space ({space_count} spaces instead of 1)'
        else:
            message = f'Extra spaces found ({total_occurrences} occurrences in this paragraph)'

        # Use provenance tracking to validate
        issue = self.create_validated_issue(
            severity='Low',
            message=message,
            paragraph_index=para_idx,
            original_paragraph=text,
            normalized_paragraph=text,  # No normalization for space detection
            match_text=first_match.group(),
            match_start=first_match.start(),
            match_end=first_match.end(),
            context=context_with_highlight,
            suggestion=f'Remove extra space{"s" if total_occurrences > 1 else ""} ({total_occurrences} total)',
            original_text=original_chunk,
            replacement_text=fixed_chunk,
            rule_id='PUN001',
            extra_space_count=total_occurrences  # Custom field for UI
        )

        if issue:
            issues.append(issue)

        return issues
    
    def _check_comma_splice(self, para_idx: int, text: str) -> Optional[dict]:
        """
        Find potential comma splice and create validated issue.
        
        Uses provenance tracking to validate the flagged text.
        
        Args:
            para_idx: Paragraph index
            text: Paragraph text
            
        Returns:
            Issue dict if comma splice found and validated, None otherwise
        """
        # Pattern: comma + pronoun/conjunctive adverb + verb
        patterns = [
            (r',\s+(he|she|it|they|we|I)\s+\w+s?\b', 'pronoun'),
            (r',\s+(however|therefore|thus|hence|moreover)\b', 'conjunctive adverb'),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Use provenance tracking to validate
                issue = self.create_validated_issue(
                    severity='Low',
                    message=f'Possible comma splice ({pattern_type})',
                    paragraph_index=para_idx,
                    original_paragraph=text,
                    normalized_paragraph=text,  # No normalization
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=self._get_splice_context(text, match),
                    suggestion='Use semicolon, period, or conjunction',
                    rule_id='PUN002'
                )
                
                if issue:
                    return issue
        
        return None
    
    def _get_splice_context(self, text: str, match: re.Match) -> str:
        """Get context around a comma splice match."""
        start = max(0, match.start() - 10)
        end = min(len(text), match.end() + 10)
        return text[start:end].strip()
    
    def safe_check(self, *args, **kwargs) -> List['ReviewIssue']:
        """Safely run check with exception handling."""
        try:
            return self.check(*args, **kwargs)
        except Exception as e:
            self._errors.append(f"Safe check error: {e}")
            return []
