#!/usr/bin/env python3
"""
Context Utilities v1.0.0
========================
Provides rich context generation for review issues.

Features:
- Full sentence extraction around flagged text
- Page number and section header tracking
- Highlight markers for frontend rendering
- Paragraph-to-page mapping support

Usage:
    from context_utils import ContextBuilder, extract_sentence, format_with_highlight

    # Build context for an issue
    ctx = ContextBuilder(paragraphs, page_map, headings)
    rich_context = ctx.build_context(
        para_idx=5,
        flagged_text="NASA",
        match_start=42,
        match_end=46
    )
    # Returns: {
    #     'context': 'The «NASA» program will deliver...',
    #     'sentence': 'The NASA program will deliver the payload by Q3.',
    #     'page': 3,
    #     'section': '2.1 Mission Overview',
    #     'flagged_text': 'NASA'
    # }
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

__version__ = "1.0.0"

# Highlight markers - frontend will convert these to <mark> tags
HIGHLIGHT_START = "«"
HIGHLIGHT_END = "»"


@dataclass
class RichContext:
    """Rich context information for a review issue."""
    context: str = ""              # Context with highlight markers
    sentence: str = ""             # Full sentence containing the issue
    page: Optional[int] = None     # Page number (1-indexed)
    section: Optional[str] = None  # Section header
    flagged_text: str = ""         # The specific text flagged
    char_offset: int = -1          # Character offset in paragraph
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'context': self.context,
            'sentence': self.sentence,
            'page': self.page,
            'section': self.section,
            'flagged_text': self.flagged_text,
            'char_offset': self.char_offset
        }


def extract_sentence(text: str, position: int, max_length: int = 300) -> str:
    """
    Extract the full sentence containing the given position.
    
    Args:
        text: The full paragraph text
        position: Character position within the text
        max_length: Maximum sentence length to return (truncate if longer)
    
    Returns:
        The sentence containing the position, or a context window if sentence is too long
    """
    if not text or position < 0:
        return text[:max_length] if text else ""
    
    # Clamp position to valid range
    position = min(position, len(text) - 1)
    
    # Sentence-ending patterns
    sentence_end = re.compile(r'[.!?](?:\s|$)|[.!?]["\')\]](?:\s|$)')
    
    # Find sentence start (look backwards for sentence end or start of text)
    start = 0
    for match in sentence_end.finditer(text[:position]):
        # The sentence starts after the previous sentence end
        potential_start = match.end()
        if potential_start <= position:
            start = potential_start
    
    # Skip leading whitespace
    while start < len(text) and text[start] in ' \t\n':
        start += 1
    
    # Find sentence end (look forwards for sentence end or end of text)
    end = len(text)
    for match in sentence_end.finditer(text[position:]):
        end = position + match.end()
        break
    
    sentence = text[start:end].strip()
    
    # If sentence is too long, create a window around the position
    if len(sentence) > max_length:
        # Calculate window around the position
        relative_pos = position - start
        half_window = max_length // 2
        
        window_start = max(0, relative_pos - half_window)
        window_end = min(len(sentence), relative_pos + half_window)
        
        result = sentence[window_start:window_end].strip()
        
        # Add ellipsis indicators
        if window_start > 0:
            result = "..." + result
        if window_end < len(sentence):
            result = result + "..."
        
        return result
    
    return sentence


def format_with_highlight(text: str, flagged_text: str, 
                         match_start: int = -1, match_end: int = -1) -> str:
    """
    Format text with highlight markers around the flagged portion.
    
    Args:
        text: The context text
        flagged_text: The text to highlight
        match_start: Start position of match in text (optional, for precision)
        match_end: End position of match in text (optional)
    
    Returns:
        Text with «highlight» markers around flagged portion
    """
    if not text or not flagged_text:
        return text or ""
    
    # If we have exact positions, use them
    if match_start >= 0 and match_end > match_start:
        if match_start < len(text) and match_end <= len(text):
            return (
                text[:match_start] + 
                HIGHLIGHT_START + text[match_start:match_end] + HIGHLIGHT_END + 
                text[match_end:]
            )
    
    # Otherwise, find the flagged text in the context
    # Use case-insensitive search but preserve original case in output
    pattern = re.compile(re.escape(flagged_text), re.IGNORECASE)
    match = pattern.search(text)
    
    if match:
        return (
            text[:match.start()] + 
            HIGHLIGHT_START + match.group() + HIGHLIGHT_END + 
            text[match.end():]
        )
    
    # Flagged text not found - return as-is
    return text


def find_section_for_paragraph(para_idx: int, headings: List[Dict]) -> Optional[str]:
    """
    Find the section header that applies to a given paragraph.
    
    Args:
        para_idx: Paragraph index
        headings: List of heading dicts with 'text', 'level', 'index' keys
    
    Returns:
        The section header text, or None if no section found
    """
    if not headings:
        return None
    
    # Find the most recent heading before this paragraph
    current_section = None
    for heading in headings:
        heading_idx = heading.get('index', 0)
        if heading_idx <= para_idx:
            current_section = heading.get('text', '')
        else:
            break  # Headings should be in order
    
    return current_section


class ContextBuilder:
    """
    Builds rich context for review issues.
    
    Tracks paragraph-to-page mapping and section headers to provide
    comprehensive context information.
    """
    
    def __init__(
        self,
        paragraphs: List[Tuple[int, str]] = None,
        page_map: Dict[int, int] = None,
        headings: List[Dict] = None,
        full_text: str = ""
    ):
        """
        Initialize the context builder.
        
        Args:
            paragraphs: List of (index, text) tuples
            page_map: Dict mapping paragraph index to page number
            headings: List of heading dicts with 'text', 'level', 'index'
            full_text: Complete document text (for fallback)
        """
        self.paragraphs = paragraphs or []
        self.page_map = page_map or {}
        self.headings = headings or []
        self.full_text = full_text
        
        # Build paragraph text lookup
        self._para_text = {idx: text for idx, text in self.paragraphs}
    
    def get_paragraph_text(self, para_idx: int) -> str:
        """Get the text for a paragraph index."""
        return self._para_text.get(para_idx, "")
    
    def get_page_number(self, para_idx: int) -> Optional[int]:
        """Get the page number for a paragraph index."""
        return self.page_map.get(para_idx)
    
    def get_section(self, para_idx: int) -> Optional[str]:
        """Get the section header for a paragraph index."""
        return find_section_for_paragraph(para_idx, self.headings)
    
    def build_context(
        self,
        para_idx: int,
        flagged_text: str,
        match_start: int = -1,
        match_end: int = -1,
        message: str = "",
        include_sentence: bool = True,
        max_context_length: int = 300
    ) -> RichContext:
        """
        Build rich context for a review issue.
        
        Args:
            para_idx: Paragraph index where issue was found
            flagged_text: The specific text being flagged
            match_start: Character offset where match starts in paragraph
            match_end: Character offset where match ends
            message: Optional message (unused, for future expansion)
            include_sentence: Whether to extract full sentence
            max_context_length: Maximum context string length
        
        Returns:
            RichContext object with all context information
        """
        para_text = self.get_paragraph_text(para_idx)
        
        # Extract the sentence containing the issue
        sentence = ""
        if include_sentence and para_text:
            # Use match_start if available, otherwise find flagged_text
            position = match_start
            if position < 0 and flagged_text:
                idx = para_text.lower().find(flagged_text.lower())
                position = idx if idx >= 0 else 0
            
            sentence = extract_sentence(para_text, position, max_context_length)
        
        # Format context with highlighting
        context_text = sentence if sentence else para_text[:max_context_length]
        
        # Calculate relative position within the sentence/context
        if match_start >= 0 and sentence:
            # Find where the sentence starts in the paragraph
            sentence_clean = sentence.lstrip('.')
            sentence_start = para_text.find(sentence_clean[:20]) if len(sentence_clean) >= 20 else 0
            if sentence_start < 0:
                sentence_start = 0
            
            # Adjust match position relative to sentence
            relative_start = match_start - sentence_start
            relative_end = match_end - sentence_start if match_end > 0 else relative_start + len(flagged_text)
            
            if 0 <= relative_start < len(context_text):
                highlighted = format_with_highlight(
                    context_text, flagged_text, 
                    relative_start, relative_end
                )
            else:
                highlighted = format_with_highlight(context_text, flagged_text)
        else:
            highlighted = format_with_highlight(context_text, flagged_text)
        
        return RichContext(
            context=highlighted,
            sentence=sentence,
            page=self.get_page_number(para_idx),
            section=self.get_section(para_idx),
            flagged_text=flagged_text,
            char_offset=match_start
        )
    
    def format_location_prefix(self, para_idx: int) -> str:
        """
        Format a location prefix string like "[Page 3, §2.1 Overview]"
        
        Args:
            para_idx: Paragraph index
        
        Returns:
            Formatted location string, or empty string if no location info
        """
        parts = []
        
        page = self.get_page_number(para_idx)
        if page:
            parts.append(f"Page {page}")
        
        section = self.get_section(para_idx)
        if section:
            # Truncate long section names
            if len(section) > 40:
                section = section[:37] + "..."
            parts.append(f"§{section}")
        
        if parts:
            return f"[{', '.join(parts)}] "
        return ""


def enhance_issue_context(
    issue: Dict[str, Any],
    context_builder: ContextBuilder
) -> Dict[str, Any]:
    """
    Enhance an existing issue dict with rich context.
    
    Args:
        issue: Issue dictionary with at least 'paragraph_index' and 'context' or 'flagged_text'
        context_builder: ContextBuilder instance with document data
    
    Returns:
        Enhanced issue dict with 'rich_context' field added
    """
    para_idx = issue.get('paragraph_index', 0)
    flagged = issue.get('flagged_text') or issue.get('context', '')
    
    # Get source provenance info if available
    source = issue.get('source', {})
    match_start = source.get('start_offset', -1) if source else -1
    match_end = source.get('end_offset', -1) if source else -1
    
    rich = context_builder.build_context(
        para_idx=para_idx,
        flagged_text=flagged,
        match_start=match_start,
        match_end=match_end
    )
    
    # Add rich context to issue
    issue['rich_context'] = rich.to_dict()
    
    # Also update the main context field with highlighted version
    if rich.context:
        issue['context'] = rich.context
    
    # Add page and section to top level for easy access
    if rich.page:
        issue['page'] = rich.page
    if rich.section:
        issue['section'] = rich.section
    
    return issue


# Convenience function for simple cases
def build_simple_context(
    text: str,
    flagged_text: str,
    position: int = -1,
    page: int = None,
    section: str = None
) -> Dict[str, Any]:
    """
    Build a simple context dict without full document info.
    
    Args:
        text: The paragraph or context text
        flagged_text: Text being flagged
        position: Character position in text
        page: Page number (optional)
        section: Section header (optional)
    
    Returns:
        Dict with context info
    """
    if position < 0 and flagged_text:
        idx = text.lower().find(flagged_text.lower())
        position = idx if idx >= 0 else 0
    
    sentence = extract_sentence(text, position)
    highlighted = format_with_highlight(sentence, flagged_text)
    
    result = {
        'context': highlighted,
        'sentence': sentence,
        'flagged_text': flagged_text
    }
    
    if page:
        result['page'] = page
    if section:
        result['section'] = section
    
    return result
