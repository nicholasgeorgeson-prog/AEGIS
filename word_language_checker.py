#!/usr/bin/env python3
"""
Word-Integrated Language Checker v1.0.0
=======================================
Uses Microsoft Word's spell and grammar checking via COM automation.
Falls back to enhanced pattern-based checking when Word is unavailable.

FEATURES:
- Word 365 spell checking integration
- Word 365 grammar checking integration
- Custom dictionary support
- Fallback to offline checking
- Tense consistency analysis
- Advanced grammar patterns

REQUIREMENTS:
- Windows with Microsoft Word installed (for COM integration)
- pywin32 package (pip install pywin32)
- Falls back gracefully on non-Windows or when Word unavailable

Author: AEGIS
Version: reads from version.json (module v1.0)
"""

import os
import re
import sys
import tempfile
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

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

# Try to import Windows COM automation
WORD_AVAILABLE = False
try:
    if sys.platform == 'win32':
        import win32com.client
        from win32com.client import constants
        WORD_AVAILABLE = True
except ImportError:
    pass


class IssueType(Enum):
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    STYLE = "style"


@dataclass
class LanguageIssue:
    """Structured language issue."""
    issue_type: IssueType
    text: str
    suggestion: str
    context: str
    paragraph_index: int
    start_pos: int = 0
    end_pos: int = 0
    rule_id: str = ""


class WordLanguageChecker(BaseChecker):
    """
    Word-integrated spell and grammar checker.
    
    Uses Microsoft Word's proofing tools when available,
    falls back to pattern-based checking otherwise.
    """
    
    CHECKER_NAME = "Language"
    CHECKER_VERSION = "1.0.0"
    
    # Technical terms to whitelist (won't be flagged as misspellings)
    TECHNICAL_WHITELIST = {
        # Aerospace/Defense
        'airframe', 'airspeed', 'avionics', 'fuselage', 'nacelle', 'empennage',
        'subsonic', 'supersonic', 'hypersonic', 'turbofan', 'turbojet',
        # Systems Engineering
        'subsystem', 'subsystems', 'traceability', 'flowdown', 'decomposition',
        'conops', 'tradespace', 'tradeoff', 'tradeoffs', 'baselined',
        # Software/IT
        'codebase', 'backend', 'frontend', 'fullstack', 'devops', 'cicd',
        'middleware', 'microservice', 'microservices', 'api', 'apis',
        # Standards
        'milspec', 'milstd', 'nadcap', 'cmmi', 'itar', 'dfars',
        # Common technical
        'lifecycle', 'runtime', 'plugin', 'plugins', 'config', 'configs',
        'metadata', 'dataset', 'datasets', 'timestamp', 'timestamps',
        'workflow', 'workflows', 'checkbox', 'dropdown', 'tooltip',
    }
    
    # Common grammar error patterns (for fallback)
    GRAMMAR_PATTERNS = [
        # Subject-verb agreement
        (r'\b(everyone|everybody|someone|somebody|anyone|anybody|nobody|nothing|each|every)\s+(are|were|have)\b',
         'Subject-verb disagreement: singular subject with plural verb', 'GR001'),
        (r'\b(both|few|many|several)\s+(is|was|has)\b',
         'Subject-verb disagreement: plural subject with singular verb', 'GR002'),
        
        # Article usage
        (r'\ba\s+([aeiou]\w+)\b',
         'Consider using "an" before vowel sound', 'GR010'),
        (r'\ban\s+([bcdfghjklmnpqrstvwxyz]\w+)\b',
         'Consider using "a" before consonant sound', 'GR011'),
        
        # Common errors
        (r'\b(could|would|should|must|might)\s+of\b',
         'Use "have" not "of" after modal verbs', 'GR020'),
        (r'\b(irregardless)\b',
         '"Irregardless" is non-standard; use "regardless"', 'GR021'),
        (r'\b(supposably)\b',
         '"Supposably" should be "supposedly"', 'GR022'),
        (r'\balot\b',
         '"Alot" should be "a lot"', 'GR023'),
        
        # Double negatives
        (r"\b(don't|doesn't|didn't|won't|wouldn't|couldn't|can't|isn't|aren't|wasn't|weren't)\s+\w*\s*(no|none|nothing|nobody|nowhere|never)\b",
         'Double negative detected', 'GR030'),
        
        # Homophones (context-based)
        (r'\b(their)\s+(is|are|was|were|will|would)\b',
         'Possible homophone error: "their" vs "there/they\'re"', 'GR040'),
        (r'\b(your)\s+(going|coming|doing|being)\b',
         'Possible homophone error: "your" vs "you\'re"', 'GR041'),
        (r'\b(its)\s+(a|an|the|going|been|not)\b',
         'Possible homophone error: "its" vs "it\'s"', 'GR042'),
        (r'\b(more|less|better|worse|greater|larger|smaller)\s+then\b',
         'Use "than" for comparisons, not "then"', 'GR043'),
        
        # Redundant phrases
        (r'\b(repeat)\s+(again)\b', 'Redundant: "repeat again"', 'GR050'),
        (r'\b(return)\s+(back)\b', 'Redundant: "return back"', 'GR051'),
        (r'\b(revert)\s+(back)\b', 'Redundant: "revert back"', 'GR052'),
        (r'\b(end)\s+(result)\b', 'Redundant: "end result"', 'GR053'),
        (r'\b(past)\s+(history)\b', 'Redundant: "past history"', 'GR054'),
        (r'\b(future)\s+(plans)\b', 'Redundant: "future plans"', 'GR055'),
        (r'\b(advance)\s+(planning|warning|notice)\b', 'Potentially redundant', 'GR056'),
        (r'\b(completely|totally|entirely)\s+(destroyed|eliminated|annihilated)\b',
         'Redundant intensifier', 'GR057'),
    ]
    
    # Tense markers for consistency checking
    PAST_MARKERS = {'was', 'were', 'had', 'did', 'went', 'came', 'made', 'said', 'took', 'got'}
    PRESENT_MARKERS = {'is', 'are', 'has', 'does', 'goes', 'comes', 'makes', 'says', 'takes', 'gets'}
    FUTURE_MARKERS = {'will', 'shall', 'going to'}
    
    def __init__(
        self,
        enabled: bool = True,
        use_word: bool = True,
        check_spelling: bool = True,
        check_grammar: bool = True,
        check_tense_consistency: bool = True,
        custom_dictionary: Optional[Set[str]] = None
    ):
        super().__init__(enabled)
        self.use_word = use_word and WORD_AVAILABLE
        self.check_spelling = check_spelling
        self.check_grammar = check_grammar
        self.check_tense_consistency = check_tense_consistency
        self.custom_dictionary = custom_dictionary or set()
        
        # Add technical whitelist to custom dictionary
        self.custom_dictionary.update(self.TECHNICAL_WHITELIST)
        
        # Word application instance (lazy initialization)
        self._word_app = None
        self._word_initialized = False
    
    def _init_word(self) -> bool:
        """Initialize Word COM automation."""
        if self._word_initialized:
            return self._word_app is not None
        
        self._word_initialized = True
        
        if not WORD_AVAILABLE:
            return False
        
        try:
            self._word_app = win32com.client.Dispatch("Word.Application")
            self._word_app.Visible = False
            return True
        except Exception as e:
            self._errors.append(f"Could not initialize Word: {e}")
            self._word_app = None
            return False
    
    def _cleanup_word(self):
        """Clean up Word COM resources."""
        if self._word_app:
            try:
                self._word_app.Quit()
            except Exception:  # Intentionally ignored
                pass
            self._word_app = None
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """
        Check spelling and grammar in paragraphs.
        
        Uses Word when available, falls back to pattern-based checking.
        """
        if not self.enabled:
            return []
        
        issues = []
        
        # Try Word-based checking first
        if self.use_word and self._init_word():
            word_issues = self._check_with_word(paragraphs, kwargs)
            issues.extend(word_issues)
        else:
            # Fallback to pattern-based checking
            if self.check_spelling:
                issues.extend(self._check_spelling_patterns(paragraphs, kwargs))
            if self.check_grammar:
                issues.extend(self._check_grammar_patterns(paragraphs, kwargs))
        
        # Always check tense consistency (not covered by Word)
        if self.check_tense_consistency:
            issues.extend(self._check_tense_consistency(paragraphs))
        
        return issues
    
    def _check_with_word(
        self,
        paragraphs: List[Tuple[int, str]],
        kwargs: Dict
    ) -> List[Dict]:
        """Check text using Word's proofing tools."""
        issues = []
        
        try:
            # Create a temporary document with the text
            doc = self._word_app.Documents.Add()
            
            # Build paragraph map for issue tracking
            para_map = {}  # char_offset -> paragraph_index
            full_text = ""
            
            for idx, text in paragraphs:
                if text.strip():
                    para_map[len(full_text)] = idx
                    full_text += text + "\n"
            
            # Insert text into document
            doc.Content.Text = full_text
            
            # Check spelling errors
            if self.check_spelling:
                for error in doc.SpellingErrors:
                    word = error.Text
                    
                    # Skip whitelisted terms
                    if word.lower() in self.custom_dictionary:
                        continue
                    
                    # Find paragraph index
                    start_pos = error.Start
                    para_idx = self._find_paragraph(para_map, start_pos)
                    
                    # Get suggestions
                    suggestions = []
                    try:
                        spell_suggestions = self._word_app.GetSpellingSuggestions(word)
                        suggestions = [s.Name for s in spell_suggestions][:3]
                    except Exception:  # Intentionally ignored
                        pass
                    
                    suggestion = f'Did you mean: {", ".join(suggestions)}' if suggestions else 'Check spelling'
                    
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Possible misspelling: "{word}"',
                        context=self._get_context(full_text, start_pos),
                        paragraph_index=para_idx,
                        suggestion=suggestion,
                        rule_id='SP001',
                        flagged_text=word,
                        original_text=word,
                        replacement_text=suggestions[0] if suggestions else ''
                    ))
            
            # Check grammar errors
            if self.check_grammar:
                for error in doc.GrammaticalErrors:
                    text = error.Text
                    start_pos = error.Start
                    para_idx = self._find_paragraph(para_map, start_pos)
                    
                    # Get grammar suggestions
                    suggestions = []
                    try:
                        for suggestion in error.GetRange().GetSpellingSuggestions():
                            suggestions.append(suggestion.Name)
                    except Exception:  # Intentionally ignored
                        pass
                    
                    # Word provides error descriptions in the range info
                    message = f'Grammar issue: "{text[:30]}..."' if len(text) > 30 else f'Grammar issue: "{text}"'
                    
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=message,
                        context=self._get_context(full_text, start_pos),
                        paragraph_index=para_idx,
                        suggestion=suggestions[0] if suggestions else 'Review grammar',
                        rule_id='GR100',
                        flagged_text=text[:50]
                    ))
            
            # Close document without saving
            doc.Close(SaveChanges=False)
        
        except Exception as e:
            self._errors.append(f"Word checking error: {e}")
            # Fall back to pattern-based checking
            if self.check_spelling:
                issues.extend(self._check_spelling_patterns(paragraphs, kwargs))
            if self.check_grammar:
                issues.extend(self._check_grammar_patterns(paragraphs, kwargs))
        
        return issues
    
    def _find_paragraph(self, para_map: Dict[int, int], char_pos: int) -> int:
        """Find paragraph index for a character position."""
        best_match = 0
        for offset, idx in sorted(para_map.items()):
            if offset <= char_pos:
                best_match = idx
            else:
                break
        return best_match
    
    def _get_context(self, text: str, pos: int, width: int = 40) -> str:
        """Get context around a position."""
        start = max(0, pos - width)
        end = min(len(text), pos + width)
        return text[start:end].replace('\n', ' ')
    
    def _check_spelling_patterns(
        self,
        paragraphs: List[Tuple[int, str]],
        kwargs: Dict
    ) -> List[Dict]:
        """Pattern-based spell checking fallback."""
        # This is a simplified fallback - the enhanced spell checker handles this better
        # Import and delegate to the enhanced spell checker
        try:
            from spell_checker import EnhancedSpellChecker
            checker = EnhancedSpellChecker(enabled=True)
            checker.add_to_dictionary(self.custom_dictionary)
            return checker.check(paragraphs, **kwargs)
        except ImportError:
            return []
    
    def _check_grammar_patterns(
        self,
        paragraphs: List[Tuple[int, str]],
        kwargs: Dict
    ) -> List[Dict]:
        """Pattern-based grammar checking fallback."""
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text) < 10:
                continue
            
            text_lower = text.lower()
            
            for pattern, message, rule_id in self.GRAMMAR_PATTERNS:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    # Skip if in special section
                    special_sections = kwargs.get('special_sections', {})
                    skip = False
                    for section_indices in special_sections.values():
                        if idx in section_indices:
                            skip = True
                            break
                    if skip:
                        continue
                    
                    context = text[max(0, match.start()-10):match.end()+20]
                    
                    # Determine severity
                    severity = 'Medium'
                    if 'GR05' in rule_id:  # Redundant phrases are Low
                        severity = 'Low'
                    elif 'GR02' in rule_id:  # Common errors are Medium
                        severity = 'Medium'
                    elif 'GR00' in rule_id:  # Agreement errors are High
                        severity = 'High'
                    
                    issues.append(self.create_issue(
                        severity=severity,
                        message=message,
                        context=context,
                        paragraph_index=idx,
                        suggestion='Review and correct',
                        rule_id=rule_id,
                        flagged_text=match.group()
                    ))
        
        return issues
    
    def _check_tense_consistency(
        self,
        paragraphs: List[Tuple[int, str]]
    ) -> List[Dict]:
        """Check for tense consistency within paragraphs."""
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text) < 20:
                continue
            
            words = text.lower().split()
            
            # Count tense markers
            past_count = sum(1 for w in words if w in self.PAST_MARKERS)
            present_count = sum(1 for w in words if w in self.PRESENT_MARKERS)
            future_count = sum(1 for w in words if w in self.FUTURE_MARKERS)
            
            total = past_count + present_count + future_count
            
            # Flag if significant mix of tenses
            if total >= 3:
                max_count = max(past_count, present_count, future_count)
                if max_count < total * 0.7:  # Less than 70% dominant tense
                    dominant = 'past' if past_count == max_count else ('present' if present_count == max_count else 'future')
                    
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Mixed verb tenses detected (mostly {dominant})',
                        context=text[:60] + '...' if len(text) > 60 else text,
                        paragraph_index=idx,
                        suggestion='Consider using consistent tense throughout paragraph',
                        rule_id='GR200',
                        flagged_text='[multiple verbs]'
                    ))
        
        return issues


# Convenience function
def check_language(paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
    """Check spelling and grammar in paragraphs."""
    checker = WordLanguageChecker()
    return checker.check(paragraphs, **kwargs)


if __name__ == '__main__':
    print(f"Word-Integrated Language Checker v{__version__}")
    print(f"Word Available: {WORD_AVAILABLE}")
    print("=" * 50)
    
    checker = WordLanguageChecker()
    
    test_paragraphs = [
        (0, "This document describes the system requiremens."),
        (1, "Everyone are welcome to attend the review meeting."),
        (2, "I could of done this better if I tried."),
        (3, "The system was updated. The changes are deployed. The tests were run."),
        (4, "We will return back to this topic in the future plans."),
    ]
    
    issues = checker.check(test_paragraphs)
    
    print(f"\nIssues Found: {len(issues)}")
    for issue in issues:
        print(f"  [{issue['severity']}] {issue['message']}")
        if issue.get('suggestion'):
            print(f"    -> {issue['suggestion']}")
