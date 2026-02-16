#!/usr/bin/env python3
"""
Requirements Language Checker v2.0.0
====================================
Verifies proper use of requirements language:
- "shall" for mandatory requirements
- "will" for statements of fact
- "must" for external constraints
- Flags weak requirement language like "should", "need to"
"""

import re
from typing import List, Dict, Tuple

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "2.5.0"


class RequirementsLanguageChecker(BaseChecker):
    """
    Checks for proper use of requirements language.
    
    Standards-based requirements use specific imperative words:
    - SHALL: Mandatory requirement (the supplier/system MUST do this)
    - WILL: Statement of fact, declaration of purpose, or future action
    - MUST: External constraint (imposed by external standards, laws, physics)
    - SHOULD: Recommendation (often considered weak for requirements)
    - MAY: Permission (optional capability)
    """
    
    CHECKER_NAME = "Requirements Language"
    CHECKER_VERSION = "2.0.0"
    
    def __init__(self, enabled: bool = True, flag_should_in_reqs: bool = True):
        """
        Initialize the requirements language checker.
        
        Args:
            enabled: Whether checker is active
            flag_should_in_reqs: If True, flag "should" as weak requirement language
        """
        super().__init__(enabled)
        self.flag_should_in_reqs = flag_should_in_reqs
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue
            
            text_lower = text.lower()
            
            # Check for mixed shall/should in same paragraph
            shall_count = len(re.findall(r'\bshall\b', text_lower))
            should_count = len(re.findall(r'\bshould\b', text_lower))
            
            if shall_count > 0 and should_count > 0:
                issues.append(self.create_issue(
                    severity='Medium',
                    message='Mixed "shall" and "should" in same paragraph',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion='Use "shall" for mandatory requirements; avoid "should" in requirements documents',
                    rule_id='REQ001'
                ))
            
            # Check for weak "need to" / "needs to" language
            for match in re.finditer(r'\b(needs?\s+to)\b', text_lower):
                actual = text[match.start():match.end()]
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Weak requirement language: "{actual}"',
                    context=text[max(0, match.start()-20):match.end()+20],
                    paragraph_index=idx,
                    suggestion='Use "shall" for requirements instead of "need to"',
                    rule_id='REQ002',
                    flagged_text=actual
                ))
            
            # Check for "is required to" which should be "shall"
            for match in re.finditer(r'\b(is|are)\s+required\s+to\b', text_lower):
                actual = text[match.start():match.end()]
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Consider simplifying: "{actual}"',
                    context=text[max(0, match.start()-15):match.end()+15],
                    paragraph_index=idx,
                    suggestion='Consider using "shall" for clearer requirement statement',
                    rule_id='REQ003',
                    flagged_text=actual
                ))
            
            # Check for "has to" / "have to"
            for match in re.finditer(r'\b(has|have)\s+to\b', text_lower):
                actual = text[match.start():match.end()]
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Informal requirement language: "{actual}"',
                    context=text[max(0, match.start()-15):match.end()+15],
                    paragraph_index=idx,
                    suggestion='Use "shall" for formal requirements',
                    rule_id='REQ004',
                    flagged_text=actual
                ))
            
            # Check for "it is necessary" / "it is required"
            for match in re.finditer(r'\bit\s+is\s+(necessary|required|essential|mandatory)\b', text_lower):
                actual = text[match.start():match.end()]
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Passive requirement language: "{actual}"',
                    context=text[max(0, match.start()-10):match.end()+20],
                    paragraph_index=idx,
                    suggestion='Consider direct "shall" statement instead',
                    rule_id='REQ005',
                    flagged_text=actual
                ))
            
            # Check for "will" where "shall" might be intended (in apparent requirement sentences)
            # Look for patterns like "The system will..." or "The contractor will..."
            for match in re.finditer(r'\b(the\s+(?:system|contractor|vendor|supplier|provider|software|hardware|user|operator|administrator))\s+will\b', text_lower):
                actual = text[match.start():match.end()]
                issues.append(self.create_issue(
                    severity='Info',
                    message=f'Potential requirement using "will": "{actual}"',
                    context=text[max(0, match.start()-5):match.end()+30],
                    paragraph_index=idx,
                    suggestion='If this is a requirement, consider "shall" instead of "will"',
                    rule_id='REQ006',
                    flagged_text=actual
                ))
        
        return issues


class AmbiguousPronounsChecker(BaseChecker):
    """
    Checks for ambiguous pronouns that may lack clear antecedents.
    
    v2.0 IMPROVEMENTS:
    - Don't flag "This document", "This section", "This table", etc.
    - Don't flag common clear patterns like "It is important..."
    - Better context detection
    """
    
    CHECKER_NAME = "Ambiguous Pronouns"
    CHECKER_VERSION = "2.0.0"
    
    # Words that when followed by these nouns are NOT ambiguous
    SPECIFIC_REFERENCE_NOUNS = {
        'document', 'section', 'table', 'figure', 'appendix', 'attachment',
        'chapter', 'paragraph', 'page', 'report', 'plan', 'procedure',
        'process', 'requirement', 'specification', 'standard', 'guide',
        'manual', 'handbook', 'policy', 'form', 'template', 'list',
        'diagram', 'chart', 'graph', 'matrix', 'schedule', 'checklist',
        'contract', 'agreement', 'proposal', 'statement', 'memo',
        'approach', 'method', 'methodology', 'technique', 'strategy',
        'analysis', 'assessment', 'evaluation', 'review', 'study',
        'design', 'architecture', 'framework', 'model', 'concept',
        'system', 'subsystem', 'component', 'module', 'interface',
        'function', 'feature', 'capability', 'service', 'tool',
        'step', 'phase', 'stage', 'activity', 'task', 'action',
        'effort', 'work', 'project', 'program', 'initiative',
        'implementation', 'execution', 'operation', 'maintenance',
        'data', 'information', 'input', 'output', 'result', 'finding',
        'metric', 'measure', 'indicator', 'criterion', 'factor',
        'item', 'element', 'type', 'category', 'class', 'level',
        'option', 'alternative', 'solution', 'scenario', 'case',
    }
    
    # Patterns that are NOT ambiguous even though they start with this/that/it
    CLEAR_PATTERNS = [
        r'^this\s+\w+\s+(?:document|section|table|figure)',
        r'^this\s+is\s+(?:the|a|an)\s+',
        r'^that\s+is\s+',
        r'^it\s+is\s+(?:important|necessary|essential|critical|recommended|required|expected)',
        r'^it\s+is\s+(?:the|a|an)\s+',
        r'^it\s+is\s+(?:applicable|available|intended|designed|possible)',
        r'^it\s+(?:allows|provides|enables|supports|includes|contains|describes|defines|specifies)',
        r'^it\s+(?:typically|generally|usually|often|commonly|normally)',
        r'^it\s+(?:can|could|may|might|shall|should|will|would|must)',
        r'^it\s+(?:also|further|additionally)',
        r'^it\s+(?:covers|addresses|deals|handles|manages|controls|affects)',
        r'^this\s+(?:typically|generally|usually|often|commonly)',
        r'^this\s+(?:can|could|may|might|shall|should|will|would|must)',
    ]
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 15:
                continue
            
            # Check if paragraph starts with ambiguous pronoun
            text_lower = text.lower().strip()
            words = text_lower.split()
            
            if len(words) < 4:  # Too short to be a real sentence
                continue
            
            # Check for sentence-starting ambiguous pronouns
            ambiguous_starters = {'it', 'this', 'that', 'these', 'those'}
            
            # Check paragraph start
            first_word = words[0].rstrip('.,;:')
            if first_word in ambiguous_starters:
                if not self._is_clear_reference(text_lower, first_word, words):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Paragraph starts with potentially ambiguous "{first_word}"',
                        context=text[:60],
                        paragraph_index=idx,
                        suggestion=f'Consider specifying what "{first_word}" refers to',
                        rule_id='AMB001',
                        flagged_text=first_word
                    ))
            
            # Check sentences within paragraph
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sentence in sentences[1:]:  # Skip first sentence (already checked)
                if not sentence or len(sentence) < 15:
                    continue
                
                sent_lower = sentence.lower().strip()
                sent_words = sent_lower.split()
                
                if not sent_words:
                    continue
                
                first = sent_words[0].rstrip('.,;:')
                if first in ambiguous_starters:
                    if not self._is_clear_reference(sent_lower, first, sent_words):
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Sentence starts with potentially ambiguous "{first}"',
                            context=sentence[:60],
                            paragraph_index=idx,
                            suggestion=f'Consider specifying what "{first}" refers to',
                            rule_id='AMB002',
                            flagged_text=first
                        ))
        
        return issues
    
    def _is_clear_reference(self, text_lower: str, pronoun: str, words: List[str]) -> bool:
        """Check if the pronoun usage is actually clear (not ambiguous)."""
        
        # Check if followed by a specific noun
        if len(words) >= 2:
            second_word = words[1].rstrip('.,;:')
            if second_word in self.SPECIFIC_REFERENCE_NOUNS:
                return True  # "This document" is clear
            
            # Check third word for compound references
            if len(words) >= 3:
                third_word = words[2].rstrip('.,;:')
                if third_word in self.SPECIFIC_REFERENCE_NOUNS:
                    return True  # "This important document" is clear
        
        # Check against clear patterns
        for pattern in self.CLEAR_PATTERNS:
            if re.match(pattern, text_lower):
                return True
        
        return False
