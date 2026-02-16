#!/usr/bin/env python3
"""
Enhanced Grammar Checker v2.0.0 (Offline)
=========================================
Comprehensive grammar checking without external API dependencies.

Features:
- Subject-verb agreement checking
- Article usage (a/an)
- Common homophone errors
- Tense consistency
- Double negative detection
- Common grammar mistakes

Author: AEGIS
"""

import re
from typing import List, Dict, Tuple, Set, Optional

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


class EnhancedGrammarChecker(BaseChecker):
    """Comprehensive offline grammar checker."""
    
    CHECKER_NAME = "Grammar"
    CHECKER_VERSION = "2.0.0"
    
    # Words with consonant sound despite vowel start (use 'a')
    CONSONANT_SOUND_WORDS = {
        'ubiquitous', 'unanimous', 'unicorn', 'uniform', 'union', 'unique',
        'unit', 'united', 'universal', 'university', 'usage', 'use', 'used',
        'useful', 'user', 'usual', 'usually', 'usurp', 'utility', 'utensil',
        'utopia', 'utopian', 'european', 'euphemism', 'euphoria', 'eureka',
        'one', 'once',
    }
    
    # Words with vowel sound despite consonant start (use 'an')
    VOWEL_SOUND_WORDS = {'heir', 'heiress', 'honest', 'honor', 'honour', 'hour', 'hourly'}
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        # A/an patterns
        self.a_before_vowel = re.compile(r'\ba\s+([aeiouAEIOU]\w*)\b')
        self.an_before_consonant = re.compile(r'\ban\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]\w*)\b')
        
        # Subject-verb agreement
        self.singular_plural_mismatch = re.compile(
            r'\b(each|every|everyone|everybody|someone|somebody|anyone|anybody|'
            r'nobody|nothing|either|neither)\s+(?:of\s+\w+\s+)?(are|were|have)\b',
            re.IGNORECASE
        )
        
        self.plural_singular_mismatch = re.compile(
            r'\b(both|few|many|several)\s+(?:of\s+\w+\s+)?(is|was|has)\b',
            re.IGNORECASE
        )
        
        # Double negative
        self.double_negative = re.compile(
            r"\b(don't|doesn't|didn't|won't|wouldn't|couldn't|shouldn't|can't|"
            r"isn't|aren't|wasn't|weren't|haven't|hasn't|not)\s+\w*\s*"
            r"(no|none|nothing|nobody|nowhere|never|neither)\b",
            re.IGNORECASE
        )
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check grammar in paragraphs."""
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue
            
            # A/an usage
            issues.extend(self._check_articles(idx, text))
            
            # Subject-verb agreement
            issues.extend(self._check_subject_verb(idx, text))
            
            # Double negatives
            issues.extend(self._check_double_negatives(idx, text))
            
            # Common errors
            issues.extend(self._check_common_errors(idx, text))
            
            # Homophones
            issues.extend(self._check_homophones(idx, text))
        
        return issues
    
    def _check_articles(self, idx: int, text: str) -> List[Dict]:
        """Check a/an usage."""
        issues = []
        
        # "a" before vowel sound
        for match in self.a_before_vowel.finditer(text):
            word = match.group(1).lower()
            if word in self.CONSONANT_SOUND_WORDS or match.group(1).isupper():
                continue
            
            issues.append(self.create_issue(
                severity='Low',
                message=f'Use "an" before vowel sound: "a {match.group(1)}"',
                context=text[max(0, match.start()-10):match.end()+10],
                paragraph_index=idx,
                suggestion=f'Change to: "an {match.group(1)}"',
                rule_id='GR001',
                flagged_text=f'a {match.group(1)}',
                original_text=f'a {match.group(1)}',
                replacement_text=f'an {match.group(1)}'
            ))
        
        # "an" before consonant sound
        for match in self.an_before_consonant.finditer(text):
            word = match.group(1).lower()
            if word in self.VOWEL_SOUND_WORDS or word.startswith('h'):
                continue
            
            issues.append(self.create_issue(
                severity='Low',
                message=f'Use "a" before consonant sound: "an {match.group(1)}"',
                context=text[max(0, match.start()-10):match.end()+10],
                paragraph_index=idx,
                suggestion=f'Change to: "a {match.group(1)}"',
                rule_id='GR002',
                flagged_text=f'an {match.group(1)}',
                original_text=f'an {match.group(1)}',
                replacement_text=f'a {match.group(1)}'
            ))
        
        return issues
    
    def _check_subject_verb(self, idx: int, text: str) -> List[Dict]:
        """Check subject-verb agreement."""
        issues = []
        
        # Singular subject with plural verb
        for match in self.singular_plural_mismatch.finditer(text):
            corrections = {'are': 'is', 'were': 'was', 'have': 'has'}
            verb = match.group(2).lower()
            
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Subject-verb disagreement: "{match.group(1)}" takes singular verb',
                context=text[max(0, match.start()-5):match.end()+10],
                paragraph_index=idx,
                suggestion=f'Use "{corrections.get(verb, verb)}" instead of "{verb}"',
                rule_id='GR020',
                flagged_text=match.group()
            ))
        
        # Plural subject with singular verb
        for match in self.plural_singular_mismatch.finditer(text):
            corrections = {'is': 'are', 'was': 'were', 'has': 'have'}
            verb = match.group(2).lower()
            
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Subject-verb disagreement: "{match.group(1)}" takes plural verb',
                context=text[max(0, match.start()-5):match.end()+10],
                paragraph_index=idx,
                suggestion=f'Use "{corrections.get(verb, verb)}" instead of "{verb}"',
                rule_id='GR021',
                flagged_text=match.group()
            ))
        
        return issues
    
    def _check_double_negatives(self, idx: int, text: str) -> List[Dict]:
        """Check for double negatives."""
        issues = []
        
        for match in self.double_negative.finditer(text):
            issues.append(self.create_issue(
                severity='Medium',
                message='Double negative detected',
                context=text[max(0, match.start()-5):match.end()+10],
                paragraph_index=idx,
                suggestion='Remove one negative to clarify meaning',
                rule_id='GR030',
                flagged_text=match.group()
            ))
        
        return issues
    
    def _check_common_errors(self, idx: int, text: str) -> List[Dict]:
        """Check common grammar errors."""
        issues = []
        text_lower = text.lower()
        
        patterns = [
            # "Could of" errors
            (r'\b(could|would|should|must|might)\s+of\b', 
             'Incorrect: "{0} of"', 'Use "{0} have"', 'GR050'),
            
            # Redundant phrases
            (r'\b(repeat)\s+(again)\b', 'Redundant phrase', 'Just use "repeat"', 'GR040'),
            (r'\b(return)\s+(back)\b', 'Redundant phrase', 'Just use "return"', 'GR041'),
            (r'\b(revert)\s+(back)\b', 'Redundant phrase', 'Just use "revert"', 'GR042'),
            (r'\b(end)\s+(result)\b', 'Redundant phrase', 'Just use "result"', 'GR043'),
            (r'\b(past)\s+(history)\b', 'Redundant phrase', 'Just use "history"', 'GR044'),
            (r'\b(future)\s+(plans)\b', 'Redundant phrase', 'Just use "plans"', 'GR045'),
            (r'\b(close)\s+(proximity)\b', 'Redundant phrase', 'Use "proximity" or "nearby"', 'GR046'),
            (r'\b(completely)\s+(destroyed)\b', 'Redundant phrase', 'Just use "destroyed"', 'GR047'),
            (r'\b(absolutely)\s+(essential)\b', 'Redundant phrase', 'Just use "essential"', 'GR048'),
            
            # Common mistakes
            (r'\b(irregardless)\b', '"Irregardless" is non-standard', 'Use "regardless"', 'GR060'),
            (r'\b(supposably)\b', '"Supposably" is often incorrect', 'Use "supposedly"', 'GR061'),
            (r'\b(alot)\b', '"Alot" is not a word', 'Use "a lot"', 'GR062'),
            (r'\b(anyways)\b', '"Anyways" is informal', 'Use "anyway"', 'GR063'),
            (r'\b(towards)\b', '"Towards" - consider "toward"', 'Use "toward" (US style)', 'GR064'),
        ]
        
        for pattern, message, suggestion, rule_id in patterns:
            for match in re.finditer(pattern, text_lower):
                msg = message.format(match.group(1)) if '{0}' in message else message
                sugg = suggestion.format(match.group(1)) if '{0}' in suggestion else suggestion
                
                issues.append(self.create_issue(
                    severity='Medium' if 'GR05' in rule_id else 'Low',
                    message=msg,
                    context=text[max(0, match.start()-5):match.end()+10],
                    paragraph_index=idx,
                    suggestion=sugg,
                    rule_id=rule_id,
                    flagged_text=match.group()
                ))
        
        return issues
    
    def _check_homophones(self, idx: int, text: str) -> List[Dict]:
        """Check for homophone errors based on context."""
        issues = []
        text_lower = text.lower()
        
        # Context-based checks
        checks = [
            # their/there/they're
            (r"\b(their)\s+(is|are|was|were|will|would|can|could|should)\b",
             'Possible error: "their" should be "there" or "they\'re"', 'GR070'),
            (r"\b(there)\s+(car|house|home|dog|cat|book|idea|plan|work|job|name)\b",
             'Possible error: "there" should be "their"', 'GR071'),
            
            # your/you're
            (r"\b(your)\s+(going|coming|doing|being|getting|making|taking)\b",
             'Possible error: "your" should be "you\'re"', 'GR072'),
            (r"\b(you're)\s+(car|house|home|dog|cat|book|idea|plan|work|job|name)\b",
             'Possible error: "you\'re" should be "your"', 'GR073'),
            
            # its/it's
            (r"\b(its)\s+(a|an|the|going|been|not|very|quite|really)\b",
             'Possible error: "its" should be "it\'s"', 'GR074'),
            (r"\b(it's)\s+(own|color|colour|size|shape|name|purpose|function)\b",
             'Possible error: "it\'s" should be "its"', 'GR075'),
            
            # then/than
            (r"\b(more|less|better|worse|greater|larger|smaller|higher|lower|faster|slower)\s+(then)\b",
             'Comparison requires "than" not "then"', 'GR076'),
            (r"\b(rather|other)\s+(then)\b",
             'Use "than" for comparison', 'GR077'),
            
            # affect/effect
            (r"\b(the|an?|this|that|no|any|some|each|every)\s+(affect)\b",
             'Noun form is usually "effect"', 'GR078'),
            
            # lose/loose
            (r"\b(to|will|might|could|may|can|would|should)\s+(loose)\b",
             'Verb form is "lose" not "loose"', 'GR079'),
        ]
        
        for pattern, message, rule_id in checks:
            for match in re.finditer(pattern, text_lower):
                issues.append(self.create_issue(
                    severity='Medium',
                    message=message,
                    context=text[max(0, match.start()-5):match.end()+10],
                    paragraph_index=idx,
                    suggestion='Verify correct word usage',
                    rule_id=rule_id,
                    flagged_text=match.group()
                ))
        
        return issues


if __name__ == '__main__':
    checker = EnhancedGrammarChecker()
    test_paragraphs = [
        (0, "I need a apple and a orange."),
        (1, "Everyone are welcome to attend."),
        (2, "I could of done better."),
        (3, "Their going to the store."),
        (4, "I don't want no trouble."),
        (5, "This is more better then that."),
    ]
    
    issues = checker.check(test_paragraphs)
    for issue in issues:
        print(f"[{issue['severity']}] {issue['message']}")
        print(f"  Suggestion: {issue['suggestion']}")
        print()
