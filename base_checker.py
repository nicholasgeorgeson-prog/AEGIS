#!/usr/bin/env python3
"""
Base Checker Contract v2.1.0
============================
Defines the interface all checkers must implement.

v2.1.0 - Added provenance tracking fields for source location validation
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

__version__ = "2.5.0"


@dataclass
class SourceProvenance:
    """
    Tracks the exact source location of matched text in the original document.
    
    Used to validate that regex matches on normalized text actually exist
    in the original raw document content.
    """
    page: int = 0                    # Page number (1-indexed, 0 = unknown)
    paragraph_index: int = 0         # Paragraph index in document
    start_offset: int = -1           # Character offset in paragraph (-1 = not validated)
    end_offset: int = -1             # End offset in paragraph (-1 = not validated)
    original_text: str = ""          # The exact text as it appeared in source
    normalized_text: str = ""        # The normalized text that was matched
    is_validated: bool = False       # Whether match was verified in original
    validation_note: str = ""        # Notes from validation (e.g., "normalized whitespace")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'page': self.page,
            'paragraph_index': self.paragraph_index,
            'start_offset': self.start_offset,
            'end_offset': self.end_offset,
            'original_text': self.original_text,
            'normalized_text': self.normalized_text,
            'is_validated': self.is_validated,
            'validation_note': self.validation_note
        }


@dataclass
class ReviewIssue:
    """Represents a single review issue found in the document."""
    category: str
    severity: str  # Critical, High, Medium, Low, Info
    message: str
    context: str = ""
    paragraph_index: int = 0
    suggestion: str = ""
    rule_id: str = ""
    original_text: str = ""
    replacement_text: str = ""
    flagged_text: str = ""
    issue_id: str = ""  # Stable unique identifier
    # Provenance tracking (v2.1.0)
    source: Optional[SourceProvenance] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'issue_id': self.issue_id,
            'category': self.category,
            'severity': self.severity,
            'message': self.message,
            'context': self.context,
            'paragraph_index': self.paragraph_index,
            'suggestion': self.suggestion,
            'rule_id': self.rule_id,
            'original_text': self.original_text,
            'replacement_text': self.replacement_text,
            'flagged_text': self.flagged_text or self.context
        }
        if self.source:
            result['source'] = self.source.to_dict()
        return result


class BaseChecker:
    """
    Base class for all document checkers.
    
    All checkers must implement:
    - check() method that returns List[ReviewIssue]
    - CHECKER_NAME and CHECKER_VERSION class attributes
    """
    
    CHECKER_NAME = "Base"
    CHECKER_VERSION = "1.0.0"
    
    # Patterns that indicate boilerplate/disclaimer content to skip
    BOILERPLATE_PATTERNS = [
        r'^\s*Copyright\s*[©®]?\s*\d{4}',
        r'^\s*All rights reserved',
        r'^\s*No part of this publication',
        r'^\s*Page\s*\d+\s*(of|/)\s*\d+',
        r'^\s*EFFECTIVE\s*DATE\s*[:=]',
        r'^\s*REVIEW\s*DATE\s*[:=]',
        r'^\s*Issued\s+\d{4}',
        r'^\s*Revised\s+\d{4}',
        r'^\s*Superseding\s+',
        r'^\s*Licensee\s*=',
        r'^\s*No reproduction',
        r'^\s*Not for Resale',
        r'^\s*TO PLACE.*ORDER',
        r'^\s*Tel:\s*[\d\-\(\)\+]+',
        r'^\s*Fax:\s*[\d\-\(\)\+]+',
        r'^\s*Email:\s*\S+@\S+',
        r'^\s*Document Owner',
        r'^\s*Applies To:',
        r'^\s*Prepared by.*Committee',
        r'www\.\w+\.(com|org|gov)',
        r'https?://\S+',
        r'^\s*SAE\s+(INTERNATIONAL|International)',
        r'provided by IHS',
        r'without license from',
        r'^\s*--[`,\-]+--',  # PDF artifacts
        r'^\s*NOTE\s*\d+\s*:',  # Note sections
        r'^\s*RATIONALE\s*$',
        r'^\s*TABLE OF CONTENTS',
        r'^\.\.\.\.\d+$',  # TOC page numbers
    ]
    
    # Common organizational acronyms that don't need definition
    COMMON_ORG_ACRONYMS = {
        'SAE', 'IEEE', 'ISO', 'ANSI', 'ASTM', 'DoD', 'DOD', 'NASA', 'FAA',
        'IHS', 'USA', 'UK', 'EU', 'UN', 'NATO', 'OSHA', 'EPA', 'FDA',
        'Inc', 'LLC', 'Corp', 'Ltd', 'Co', 'PDF', 'HTML', 'XML', 'URL',
        'MDT', 'EST', 'PST', 'UTC', 'GMT',  # Time zones
    }
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._errors: List[str] = []
        self._boilerplate_patterns_compiled = None
    
    def _get_boilerplate_patterns(self):
        """Compile boilerplate patterns on first use."""
        import re
        if self._boilerplate_patterns_compiled is None:
            self._boilerplate_patterns_compiled = [
                re.compile(p, re.IGNORECASE) for p in self.BOILERPLATE_PATTERNS
            ]
        return self._boilerplate_patterns_compiled
    
    def is_boilerplate(self, text: str) -> bool:
        """Check if text appears to be boilerplate/disclaimer content."""
        if not text or len(text.strip()) < 5:
            return True
        
        for pattern in self._get_boilerplate_patterns():
            if pattern.search(text):
                return True
        return False
    
    def filter_boilerplate(self, paragraphs: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
        """Filter out boilerplate paragraphs."""
        return [(idx, text) for idx, text in paragraphs if not self.is_boilerplate(text)]
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List[ReviewIssue]:
        """
        Run the check on document content.
        
        Args:
            paragraphs: List of (index, text) tuples
            tables: List of table dictionaries with 'rows' key
            full_text: Complete document text
            filepath: Path to .docx file for XML extraction
            
        Returns:
            List of ReviewIssue objects
        """
        raise NotImplementedError("Subclasses must implement check()")
    
    def safe_check(self, *args, **kwargs) -> List[ReviewIssue]:
        """Safely run check with exception handling."""
        try:
            return self.check(*args, **kwargs)
        except Exception as e:
            self._errors.append(f"{self.CHECKER_NAME} error: {e}")
            return []
    
    def create_issue(
        self,
        severity: str,
        message: str,
        context: str = "",
        paragraph_index: int = 0,
        suggestion: str = "",
        rule_id: str = "",
        original_text: str = "",
        replacement_text: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a standardized issue dictionary.
        
        Args:
            severity: Issue severity (Critical, High, Medium, Low, Info)
            message: Human-readable issue description
            context: Surrounding text context
            paragraph_index: Index of paragraph in document
            suggestion: Recommended fix
            rule_id: Unique rule identifier
            original_text: Text to be replaced
            replacement_text: Suggested replacement
            **kwargs: Additional fields including:
                - flagged_text: Text that triggered the issue
                - source: SourceProvenance object for location tracking
                - start_offset: Character offset in paragraph (for provenance)
                - end_offset: End character offset (for provenance)
        
        Returns:
            dict for compatibility with existing code.
        """
        issue = {
            'category': self.CHECKER_NAME,
            'severity': severity,
            'message': message,
            'context': context,
            'paragraph_index': paragraph_index,
            'suggestion': suggestion,
            'rule_id': rule_id,
            'original_text': original_text,
            'replacement_text': replacement_text,
            'flagged_text': kwargs.get('flagged_text', context),
        }
        
        # Add provenance tracking if provided
        if 'source' in kwargs and kwargs['source']:
            issue['source'] = kwargs['source'].to_dict() if hasattr(kwargs['source'], 'to_dict') else kwargs['source']
        elif 'start_offset' in kwargs and kwargs['start_offset'] >= 0:
            # Create provenance from offset info
            issue['source'] = {
                'paragraph_index': paragraph_index,
                'start_offset': kwargs.get('start_offset', -1),
                'end_offset': kwargs.get('end_offset', -1),
                'original_text': kwargs.get('flagged_text', context),
                'is_validated': kwargs.get('is_validated', False),
            }
        
        return issue
    
    def validate_match_in_original(
        self,
        normalized_text: str,
        original_text: str,
        match_text: str,
        match_start: int,
        match_end: int
    ) -> Optional[SourceProvenance]:
        """
        Validate that a match found in normalized text exists in the original.

        This implements two-pass validation:
        1. First pass: Match on normalized text (already done by caller)
        2. Second pass: Verify match exists in original with exact offsets

        Args:
            normalized_text: The normalized text where match was found
            original_text: The original raw text from document
            match_text: The text that was matched
            match_start: Start offset in normalized text
            match_end: End offset in normalized text

        Returns:
            SourceProvenance if validated, None if match doesn't exist in original
        """
        import re

        # Try to find the match in original text
        # Handle common normalizations: whitespace, case
        pattern = re.escape(match_text)
        # Allow flexible whitespace
        pattern = re.sub(r'\\ ', r'\\s+', pattern)

        # FIX: For single-character matches, preserve word boundaries to prevent
        # matching characters inside words (e.g., "i" inside "question")
        if len(match_text.strip()) == 1:
            pattern = r'\b' + pattern + r'\b'

        match = re.search(pattern, original_text, re.IGNORECASE)
        
        if match:
            return SourceProvenance(
                start_offset=match.start(),
                end_offset=match.end(),
                original_text=match.group(),
                normalized_text=match_text,
                is_validated=True,
                validation_note="Direct match found in original"
            )
        
        # Try fuzzy match - look for similar text nearby
        # This handles cases where normalization changed punctuation or spacing
        words = match_text.split()
        if len(words) >= 2:
            # Search for first and last word together
            pattern = re.escape(words[0]) + r'.{0,20}' + re.escape(words[-1])
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                return SourceProvenance(
                    start_offset=match.start(),
                    end_offset=match.end(),
                    original_text=match.group(),
                    normalized_text=match_text,
                    is_validated=True,
                    validation_note="Fuzzy match (normalized spacing/punctuation)"
                )
        
        # Could not validate - return None to indicate potential false positive
        return None
    
    def create_validated_issue(
        self,
        severity: str,
        message: str,
        paragraph_index: int,
        original_paragraph: str,
        normalized_paragraph: str,
        match_text: str,
        match_start: int,
        match_end: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create an issue only if it validates against the original text.
        
        This is the recommended method for checkers that want provenance tracking.
        Returns None if the match cannot be validated in the original text.
        
        Args:
            severity: Issue severity
            message: Issue message
            paragraph_index: Paragraph index
            original_paragraph: Raw text from document
            normalized_paragraph: Normalized text that was searched
            match_text: Text that was matched
            match_start: Start offset in normalized text
            match_end: End offset in normalized text
            **kwargs: Additional issue fields
            
        Returns:
            Issue dict with provenance, or None if validation failed
        """
        provenance = self.validate_match_in_original(
            normalized_paragraph,
            original_paragraph,
            match_text,
            match_start,
            match_end
        )
        
        if not provenance:
            # Match doesn't exist in original - skip this issue
            return None
        
        provenance.paragraph_index = paragraph_index
        
        # Extract context from kwargs to avoid duplicate parameter
        context = kwargs.pop('context', match_text)
        
        return self.create_issue(
            severity=severity,
            message=message,
            context=context,
            paragraph_index=paragraph_index,
            source=provenance,
            flagged_text=provenance.original_text,  # Use original text, not normalized
            **kwargs
        )
    
    def clear_errors(self):
        """Clear accumulated errors."""
        self._errors = []
    
    def get_errors(self) -> List[str]:
        """Get accumulated errors."""
        return self._errors.copy()
