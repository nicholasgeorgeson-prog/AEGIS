#!/usr/bin/env python3
"""
Sentence Structure Checker v2.6.0
=================================
Analyzes sentence structure for clarity issues.

v2.6.0 IMPROVEMENTS:
- Migrated to provenance tracking for ambiguous reference detection
- Uses create_validated_issue() for SEN002 rule
- Validates flagged text exists in original document

v2.5.0 IMPROVEMENTS:
- Don't flag "This document" as ambiguous (it's specific)
- Don't flag "This section", "This table", etc.
- Better context detection for legitimate uses of "this/that/it"

v2.0.0 Features:
- Long sentence detection
- Ambiguous reference detection
- Sentence fragment detection
"""

import re
from typing import List, Tuple, Optional

# Import from core contracts
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

__version__ = "2.6.0"


class SentenceChecker(BaseChecker):
    """
    Checks for sentence structure issues.
    
    Detects:
    - Long sentences (configurable word limit)
    - Ambiguous references (this, that, it without clear antecedent)
    - Sentence fragments
    
    v2.6.0: Uses provenance tracking for ambiguous reference detection
    """
    
    CHECKER_NAME = "Sentence Structure"
    CHECKER_VERSION = "2.6.0"
    
    # Words that when followed by a specific noun are NOT ambiguous
    # "This document", "This section", "This table" etc. are specific references
    SPECIFIC_REFERENCE_NOUNS = {
        # Document parts
        'document', 'section', 'table', 'figure', 'appendix', 'attachment',
        'chapter', 'paragraph', 'page', 'report', 'plan', 'procedure',
        'process', 'requirement', 'specification', 'standard', 'guide',
        'manual', 'handbook', 'policy', 'form', 'template', 'list',
        'diagram', 'chart', 'graph', 'matrix', 'schedule', 'checklist',
        'contract', 'agreement', 'proposal', 'statement', 'memo',
        # Technical/engineering terms
        'approach', 'method', 'methodology', 'technique', 'strategy',
        'analysis', 'assessment', 'evaluation', 'review', 'study',
        'design', 'architecture', 'framework', 'model', 'concept',
        'system', 'subsystem', 'component', 'module', 'interface',
        'function', 'feature', 'capability', 'service', 'tool',
        # Process/workflow terms
        'step', 'phase', 'stage', 'activity', 'task', 'action',
        'effort', 'work', 'project', 'program', 'initiative',
        'implementation', 'execution', 'operation', 'maintenance',
        # Data/information terms
        'data', 'information', 'input', 'output', 'result', 'finding',
        'metric', 'measure', 'indicator', 'criterion', 'factor',
        # Generic but clear references
        'item', 'element', 'type', 'category', 'class', 'level',
        'option', 'alternative', 'solution', 'scenario', 'case',
    }
    
    def __init__(self, enabled: bool = True, max_sentence_words: int = 40):
        """
        Initialize the sentence structure checker.
        
        Args:
            enabled: Whether checker is active
            max_sentence_words: Maximum words before flagging as too long
        """
        super().__init__(enabled)
        self.max_sentence_words = max_sentence_words
        self._errors = []
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List = None,
        full_text: str = "",
        **kwargs
    ) -> List['ReviewIssue']:
        """
        Check paragraphs for sentence structure issues.
        
        Args:
            paragraphs: List of (index, text) tuples
            tables: Ignored
            full_text: Ignored
            
        Returns:
            List of ReviewIssue for structure issues
        """
        if not self.enabled:
            return []
        
        self._errors = []
        issues = []
        
        try:
            for idx, text in paragraphs:
                if not text or not isinstance(text, str):
                    continue
                
                # Split into sentences
                sentences = self._split_sentences(text)
                
                for sentence in sentences:
                    # Check for long sentences (no provenance needed - word count based)
                    word_count = len(sentence.split())
                    if word_count > self.max_sentence_words:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Long sentence: {word_count} words',
                            context=sentence[:60] + '...' if len(sentence) > 60 else sentence,
                            paragraph_index=idx,
                            suggestion=f'Consider breaking into shorter sentences (>{self.max_sentence_words} words)',
                            rule_id='SEN001',
                            flagged_text=sentence[:60] + '...' if len(sentence) > 60 else sentence
                        ))
                    
                    # Check for ambiguous "this/that/it" at start - use provenance tracking
                    ambig_issue = self._check_ambiguous_reference(sentence, text, idx)
                    if ambig_issue:
                        issues.append(ambig_issue)
        
        except Exception as e:
            self._errors.append(f"Sentence check error: {e}")
        
        return issues
    
    def _check_ambiguous_reference(self, sentence: str, original_paragraph: str, paragraph_index: int) -> Optional[dict]:
        """
        Check for ambiguous reference and create validated issue.
        
        Uses provenance tracking to validate the flagged word exists in original.
        
        Args:
            sentence: The sentence to check
            original_paragraph: Full original paragraph text
            paragraph_index: Index of paragraph
            
        Returns:
            Issue dict if ambiguous reference found and validated, None otherwise
        """
        if not self._has_ambiguous_reference(sentence):
            return None
        
        # Determine which word was actually used
        sentence_lower = sentence.lower().strip()
        ambig_word = None
        
        for word in ['this', 'that', 'it']:
            if sentence_lower.startswith(word + ' '):
                ambig_word = word
                break
        
        if not ambig_word:
            return None
        
        # Find the position of this word in the sentence for provenance
        # The ambiguous word is at the start
        match_start = 0
        match_end = len(ambig_word)
        
        # Get the actual word from sentence (preserves original case)
        actual_word = sentence[:len(ambig_word)]
        
        # Use provenance tracking to validate
        issue = self.create_validated_issue(
            severity='Medium',
            message=f'Starts with ambiguous "{ambig_word}"',
            paragraph_index=paragraph_index,
            original_paragraph=original_paragraph,
            normalized_paragraph=sentence,  # Sentence is already from original
            match_text=actual_word,
            match_start=match_start,
            match_end=match_end,
            context=sentence[:50] + '...' if len(sentence) > 50 else sentence,
            suggestion=f'Consider specifying what "{ambig_word}" refers to',
            rule_id='SEN002'
        )
        
        return issue
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter - split on . ! ? followed by space and capital
        # But not on abbreviations like "Dr." "Mr." "Inc." etc.
        
        # Protect common abbreviations
        protected = text
        abbrevs = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Jr.', 'Sr.', 'Inc.', 'Ltd.', 'Corp.', 
                   'etc.', 'e.g.', 'i.e.', 'vs.', 'No.', 'Fig.', 'Sec.', 'Rev.']
        for abbr in abbrevs:
            protected = protected.replace(abbr, abbr.replace('.', '###'))
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)
        
        # Restore abbreviations
        sentences = [s.replace('###', '.') for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _has_ambiguous_reference(self, sentence: str) -> bool:
        """Check if sentence starts with ambiguous this/that/it."""
        sentence_lower = sentence.lower().strip()
        
        # Skip very short text (likely table cells or labels)
        if len(sentence_lower) < 15 or len(sentence_lower.split()) < 4:
            return False
        
        # Check if starts with "this", "that", or "it" followed by a space
        # Must be at word boundary (start of sentence)
        starts_ambiguous = False
        ambig_word = None
        for word in ['this', 'that', 'it']:
            # Check for exact word at start followed by space
            if sentence_lower.startswith(word + ' '):
                starts_ambiguous = True
                ambig_word = word
                break
        
        if not starts_ambiguous:
            return False
        
        # Check if followed by a specific noun (not ambiguous)
        # Pattern: "This document", "This section", etc.
        words = sentence_lower.split()
        if len(words) >= 2:
            second_word = words[1].rstrip('.,;:')
            if second_word in self.SPECIFIC_REFERENCE_NOUNS:
                return False  # "This document" is NOT ambiguous
            
            # Also check for compound references like "This process document"
            if len(words) >= 3:
                third_word = words[2].rstrip('.,;:')
                if third_word in self.SPECIFIC_REFERENCE_NOUNS:
                    return False
        
        # Check for common specific patterns that aren't ambiguous
        specific_patterns = [
            r'^this\s+\w+\s+(document|section|table|figure)',  # "This important document"
            r'^this\s+is\s+(the|a|an)\s+',  # "This is the..." - usually clear
            r'^that\s+is\s+',  # "That is..." - usually clear
            r'^it\s+is\s+(important|necessary|essential|critical)',  # "It is important..."
            r'^it\s+is\s+(the|a|an)\s+',  # "It is the..." - usually clear
            r'^it\s+is\s+(applicable|available|intended|designed|recommended|required|expected|possible|necessary)',  # "It is applicable..."
            r'^it\s+(allows|provides|enables|supports|includes|contains|describes|defines|specifies|identifies|establishes|ensures|requires)',  # Definition pattern
            r'^it\s+(typically|generally|usually|often|commonly|normally|frequently)',  # Frequency adverbs
            r'^it\s+(can|could|may|might|shall|should|will|would|must)',  # Modal verbs
            r'^it\s+(also|further|additionally)',  # Continuation words
            r'^it\s+(covers|addresses|deals|handles|manages|controls|affects|impacts)',  # Action verbs
            r'^this\s+(typically|generally|usually|often|commonly)',  # This + frequency
            r'^this\s+(can|could|may|might|shall|should|will|would|must)',  # This + modal
        ]
        
        for pattern in specific_patterns:
            if re.match(pattern, sentence_lower):
                return False
        
        return True
    
    def safe_check(self, *args, **kwargs) -> List['ReviewIssue']:
        """Safely run check with exception handling."""
        try:
            return self.check(*args, **kwargs)
        except Exception as e:
            self._errors.append(f"Safe check error: {e}")
            return []
