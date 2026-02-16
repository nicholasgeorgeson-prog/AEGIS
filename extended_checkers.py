#!/usr/bin/env python3
"""
AEGIS v2.5 Extended Checkers
=======================================
This module contains all additional checkers added in v2.2:
- Spelling & Grammar
- Units & Numbers  
- Terminology & Consistency
- Enhanced Requirements
- Typography
- References
- Clarity
- Sentence Structure
- Standards Compliance
- Document Structure

v2.5.0: Added provenance tracking via create_validated_issue() for text-match based rules
"""

import re
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict

try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Unknown"
        
        # Boilerplate patterns to skip
        BOILERPLATE_PATTERNS = [
            r'^\s*Copyright\s*[©®]?\s*\d{4}',
            r'^\s*All rights reserved',
            r'^\s*No part of this publication',
            r'^\s*Page\s*\d+\s*(of|/)\s*\d+',
            r'^\s*EFFECTIVE\s*DATE',
            r'^\s*REVIEW\s*DATE',
            r'^\s*Issued\s+\d{4}',
            r'^\s*Revised\s+\d{4}',
            r'^\s*Superseding\s+',
            r'^\s*Licensee\s*=',
            r'^\s*No reproduction',
            r'^\s*Not for Resale',
            r'^\s*TO PLACE.*ORDER',
            r'^\s*Document Owner',
            r'^\s*Applies To:',
            r'^\s*SAE\s+(INTERNATIONAL|International)',
            r'provided by IHS',
            r'without license from',
            r'^\s*NOTE\s*\d+\s*:',
        ]
        
        COMMON_ORG_ACRONYMS = {
            'SAE', 'IEEE', 'ISO', 'ANSI', 'ASTM', 'DoD', 'DOD', 'NASA', 'FAA',
            'IHS', 'USA', 'UK', 'EU', 'UN', 'MDT', 'EST', 'PST', 'UTC',
        }
        
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._boilerplate_compiled = None
            
        def _get_boilerplate_patterns(self):
            if self._boilerplate_compiled is None:
                self._boilerplate_compiled = [re.compile(p, re.IGNORECASE) for p in self.BOILERPLATE_PATTERNS]
            return self._boilerplate_compiled
            
        def is_boilerplate(self, text: str) -> bool:
            if not text or len(text.strip()) < 5:
                return True
            for pattern in self._get_boilerplate_patterns():
                if pattern.search(text):
                    return True
            return False
            
        def filter_boilerplate(self, paragraphs):
            return [(idx, text) for idx, text in paragraphs if not self.is_boilerplate(text)]
            
        def create_issue(self, **kwargs):
            kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
            return kwargs

__version__ = "2.5.0"

# =============================================================================
# SPELLING & GRAMMAR CHECKERS
# =============================================================================

class SpellingChecker(BaseChecker):
    """Checks for common misspellings."""
    
    CHECKER_NAME = "Spelling"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    COMMON_MISSPELLINGS = {
        'recieve': 'receive', 'seperate': 'separate', 'occured': 'occurred',
        'occurence': 'occurrence', 'definately': 'definitely', 'accomodate': 'accommodate',
        'independant': 'independent', 'occassion': 'occasion', 'untill': 'until',
        'goverment': 'government', 'enviroment': 'environment', 'managment': 'management',
        'developement': 'development', 'maintainance': 'maintenance', 'performace': 'performance',
        'refered': 'referred', 'transfered': 'transferred', 'commited': 'committed',
        'begining': 'beginning', 'occuring': 'occurring', 'refering': 'referring',
        'sucessful': 'successful', 'neccessary': 'necessary', 'supercede': 'supersede',
        'liason': 'liaison', 'existance': 'existence', 'persistance': 'persistence',
        'consistant': 'consistent', 'dependant': 'dependent', 'equiptment': 'equipment',
        'fullfill': 'fulfill', 'gaurd': 'guard', 'gaurantee': 'guarantee',
        'hierachy': 'hierarchy', 'immediatly': 'immediately', 'knowlege': 'knowledge',
        'liesure': 'leisure', 'libary': 'library', 'lisense': 'license',
        'millenium': 'millennium', 'mispell': 'misspell', 'noticable': 'noticeable',
        'paralel': 'parallel', 'privelege': 'privilege', 'publically': 'publicly',
        'recomend': 'recommend', 'relevent': 'relevant', 'repitition': 'repetition',
        'similiar': 'similar', 'succesful': 'successful', 'therefor': 'therefore',
        'threshhold': 'threshold', 'tommorow': 'tomorrow', 'truely': 'truly',
        'wierd': 'weird', 'wether': 'whether', 'wich': 'which',
    }
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        # Filter out boilerplate content
        filtered_paras = self.filter_boilerplate(paragraphs) if hasattr(self, 'filter_boilerplate') else paragraphs
        for idx, text in filtered_paras:
            if not text:
                continue
            text_lower = text.lower()
            for misspelled, correct in self.COMMON_MISSPELLINGS.items():
                pattern = r'\b' + re.escape(misspelled) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Medium',
                        message=f'Possible misspelling: "{match.group()}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-20):match.end()+20],
                        suggestion=f'Did you mean "{correct}"?',
                        rule_id='SPL001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class GrammarChecker(BaseChecker):
    """Checks for common grammar issues."""

    CHECKER_NAME = "Grammar"
    CHECKER_VERSION = "2.6.0"  # v2.6.0: Fixed GRM002 capitalize I false positives

    # Patterns that use re.IGNORECASE
    GRAMMAR_PATTERNS = [
        (r'\b(data|criteria|media|phenomena) is\b', 'Medium', 'GRM001',
         'Subject-verb disagreement: Use "are" with plural noun'),
        (r'\bcould of\b|\bshould of\b|\bwould of\b', 'High', 'GRM003',
         'Use "could have", "should have", or "would have"'),
        (r'\btheir is\b|\btheir are\b', 'High', 'GRM004',
         'Use "there is" or "there are"'),
        (r'\bits\s+a\s+\w+\s+that\b', 'Low', 'GRM005',
         'Consider rephrasing "it\'s a...that" construction'),
    ]

    # v2.6.0: Separate pattern for lowercase 'i' - does NOT use IGNORECASE
    # This pattern ONLY matches lowercase 'i' as a standalone pronoun followed by a word
    # Uses \w (word character) boundaries to exclude 'i' inside words
    # Excludes: i inside words, capital I, (i) list items, Roman numerals
    LOWERCASE_I_PATTERN = r'(?<!\w)i(?!\w)(?=\s+[a-z])'

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue

            # Check standard patterns with IGNORECASE
            for pattern, severity, rule_id, suggestion in self.GRAMMAR_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    issue = self.create_validated_issue(
                        severity=severity,
                        message=suggestion,
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-20):match.end()+20],
                        suggestion=suggestion,
                        rule_id=rule_id
                    )
                    if issue:
                        issues.append(issue)

            # v2.6.0: Check lowercase 'i' WITHOUT IGNORECASE (case-sensitive)
            # This prevents matching already-capitalized 'I' and 'i' inside words
            for match in re.finditer(self.LOWERCASE_I_PATTERN, text):
                issue = self.create_validated_issue(
                    severity='Low',
                    message='Capitalize "I"',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[max(0,match.start()-20):match.end()+20],
                    suggestion='Capitalize "I"',
                    rule_id='GRM002'
                )
                if issue:
                    issues.append(issue)

        return issues


# =============================================================================
# UNITS & NUMBERS CHECKERS
# =============================================================================

class UnitsChecker(BaseChecker):
    """Checks unit formatting and consistency."""
    
    CHECKER_NAME = "Units"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    UNITS = ['kg', 'g', 'mg', 'lb', 'oz', 'm', 'cm', 'mm', 'km', 'ft', 'in', 'mi',
             's', 'ms', 'min', 'hr', 'Hz', 'kHz', 'MHz', 'GHz', 'V', 'mV', 'kV',
             'A', 'mA', 'W', 'kW', 'MW', 'J', 'kJ', 'N', 'Pa', 'kPa', 'MPa',
             'K', 'C', 'F', 'psi', 'bar', 'dB', 'dBm', 'Bps', 'Mbps', 'Gbps']
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for missing space between number and unit
            for unit in self.UNITS:
                pattern = r'\d' + re.escape(unit) + r'\b'
                for match in re.finditer(pattern, text):
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Missing space between number and unit',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=match.group(),
                        suggestion=f'Add space: e.g., "10 {unit}" not "10{unit}"',
                        rule_id='UNT001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class NumberFormatChecker(BaseChecker):
    """Checks number formatting consistency."""
    
    CHECKER_NAME = "Number Format"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Skip if paragraph starts with section number (e.g., "4.1 Title")
            if re.match(r'^\s*\d+(\.\d+)*\s+[A-Z]', text):
                continue
            # Check for numbers that should be spelled out (1-9)
            for match in re.finditer(r'\b([1-9])\b(?!\.\d)', text):
                # Skip if part of section reference, version, date, or common patterns
                context_before = text[max(0, match.start()-20):match.start()]
                context_after = text[match.end():match.end()+10]
                
                # Skip patterns like "Section 4", "Table 1", "Figure 2", "Step 3", "v1", "1.0"
                skip_patterns = [
                    r'(Section|Table|Figure|Step|Item|Version|Rev|v|V)\s*$',
                    r'(page|Page|PAGE)\s*$',
                    r'\d+\.\d*$',  # Decimal numbers
                    r'[-/]\s*$',   # Date separators
                ]
                
                skip = False
                for pattern in skip_patterns:
                    if re.search(pattern, context_before):
                        skip = True
                        break
                
                # Also skip if followed by decimal or looks like section ref
                if re.match(r'\.\d', context_after):
                    skip = True
                    
                if not skip:
                    issue = self.create_validated_issue(
                        severity='Info',
                        message=f'Consider spelling out single-digit number: {match.group(1)}',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,
                        match_text=match.group(1),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-15):match.end()+15],
                        suggestion='Spell out numbers one through nine in prose',
                        rule_id='NUM001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


# =============================================================================
# TERMINOLOGY CHECKERS
# =============================================================================

class TerminologyChecker(BaseChecker):
    """Checks for terminology consistency."""
    
    CHECKER_NAME = "Terminology"
    TERM_VARIATIONS = {
        ('login', 'log-in', 'log in'): 'login',
        ('setup', 'set-up', 'set up'): 'setup (noun) or set up (verb)',
        ('email', 'e-mail'): 'email',
        ('online', 'on-line'): 'online',
        ('database', 'data base', 'data-base'): 'database',
        ('filename', 'file name', 'file-name'): 'filename',
        ('username', 'user name', 'user-name'): 'username',
        ('website', 'web site', 'web-site'): 'website',
        ('backup', 'back-up', 'back up'): 'backup (noun) or back up (verb)',
    }
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        term_usage = defaultdict(list)
        
        full_text = ' '.join(text for _, text in paragraphs if text)
        
        for variations, preferred in self.TERM_VARIATIONS.items():
            found = []
            for var in variations:
                if re.search(r'\b' + re.escape(var) + r'\b', full_text, re.IGNORECASE):
                    found.append(var)
            if len(found) > 1:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Inconsistent terminology: using both {", ".join(found)}',
                    context=f'Found variations: {", ".join(found)}',
                    paragraph_index=0,
                    suggestion=f'Use consistent form: {preferred}',
                    rule_id='TRM001',
                    flagged_text=found[0]
                ))
        return issues


class TBDChecker(BaseChecker):
    """Checks for TBD/TBR placeholders."""
    
    CHECKER_NAME = "TBD Placeholders"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    PLACEHOLDERS = ['TBD', 'TBR', 'TBS', 'TBC', 'TBA', 'XXX', 'FIXME', 'TODO', 
                   'PLACEHOLDER', 'INSERT', 'PENDING', 'N/A', '???', '...']
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            for placeholder in self.PLACEHOLDERS:
                pattern = r'\b' + re.escape(placeholder) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    issue = self.create_validated_issue(
                        severity='High',
                        message=f'Placeholder found: {match.group()}',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-20):match.end()+20],
                        suggestion='Replace with actual content before publication',
                        rule_id='TBD001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class RedundancyChecker(BaseChecker):
    """Checks for redundant phrases."""
    
    CHECKER_NAME = "Redundancy"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    REDUNDANT_PHRASES = {
        'advance planning': 'planning',
        'added bonus': 'bonus',
        'basic fundamentals': 'fundamentals',
        'close proximity': 'proximity',
        'completely eliminate': 'eliminate',
        'end result': 'result',
        'final outcome': 'outcome',
        'free gift': 'gift',
        'future plans': 'plans',
        'new innovation': 'innovation',
        'past history': 'history',
        'plan ahead': 'plan',
        'repeat again': 'repeat',
        'revert back': 'revert',
        'unexpected surprise': 'surprise',
        'very unique': 'unique',
        'completely unanimous': 'unanimous',
        'each and every': 'each or every',
        'first and foremost': 'first',
        'various different': 'various or different',
    }
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for phrase, replacement in self.REDUNDANT_PHRASES.items():
                # Use regex for word boundary matching
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Redundant phrase: "{phrase}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-10):match.end()+10],
                        suggestion=f'Consider using just "{replacement}"',
                        rule_id='RED001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


# =============================================================================
# ENHANCED REQUIREMENTS CHECKERS
# =============================================================================

class TestabilityChecker(BaseChecker):
    """Checks for untestable language in requirements."""
    
    CHECKER_NAME = "Testability"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    UNTESTABLE_TERMS = {
        'user-friendly': 'Define specific usability criteria',
        'easy to use': 'Define specific usability metrics',
        'intuitive': 'Define expected user actions',
        'robust': 'Specify reliability metrics (MTBF, etc.)',
        'flexible': 'Define required flexibility scenarios',
        'scalable': 'Specify scaling requirements with numbers',
        'fast': 'Specify response time in seconds/ms',
        'responsive': 'Specify response time thresholds',
        'secure': 'Reference specific security standards',
        'reliable': 'Specify reliability metrics',
        'efficient': 'Define efficiency metrics',
        'high-performance': 'Specify performance thresholds',
        'maintainable': 'Define maintenance requirements',
        'portable': 'List target platforms explicitly',
    }
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text or 'shall' not in text.lower():
                continue
            text_lower = text.lower()
            for term, suggestion in self.UNTESTABLE_TERMS.items():
                # Use regex for word boundary matching
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='High',
                        message=f'Untestable requirement: "{term}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-15):match.end()+15],
                        suggestion=suggestion,
                        rule_id='TST001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class AtomicityChecker(BaseChecker):
    """Checks for compound requirements that should be split."""
    
    CHECKER_NAME = "Atomicity"
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Count "shall" occurrences
            shall_count = len(re.findall(r'\bshall\b', text, re.IGNORECASE))
            if shall_count > 1:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Compound requirement: {shall_count} "shall" statements',
                    context=text[:60],
                    paragraph_index=idx,
                    suggestion='Split into separate atomic requirements',
                    rule_id='ATM001',
                    flagged_text=text[:40]
                ))
        return issues


class EscapeClauseChecker(BaseChecker):
    """Detects escape clauses that weaken requirements."""
    
    CHECKER_NAME = "Escape Clauses"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    ESCAPE_PATTERNS = [
        'unless otherwise', 'if applicable', 'when possible', 'as appropriate',
        'to the extent possible', 'if feasible', 'where practical', 
        'as needed', 'when required', 'subject to change', 'if available',
        'when available', 'to the maximum extent', 'within reason',
    ]
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for pattern in self.ESCAPE_PATTERNS:
                # Use regex for word boundary matching
                regex_pattern = r'\b' + re.escape(pattern) + r'\b'
                for match in re.finditer(regex_pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Medium',
                        message=f'Escape clause: "{pattern}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-15):match.end()+15],
                        suggestion='Remove ambiguity by specifying exact conditions',
                        rule_id='ESC001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


# =============================================================================
# TYPOGRAPHY CHECKERS
# =============================================================================

class HyphenationChecker(BaseChecker):
    """Checks compound modifier hyphenation."""
    
    CHECKER_NAME = "Hyphenation"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    COMPOUND_MODIFIERS = [
        'high level', 'low level', 'real time', 'end user', 'long term',
        'short term', 'high quality', 'full time', 'part time', 'on site',
        'off site', 'state of the art', 'up to date', 'built in', 'plug in',
        'sign in', 'log in', 'drop down', 'pop up', 'stand alone',
    ]
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for compound in self.COMPOUND_MODIFIERS:
                # Check if used as modifier (before a noun)
                pattern = r'\b' + re.escape(compound) + r'\s+\w+(?:ing|ed|tion|ment|ness|ity)?\b'
                for match in re.finditer(pattern, text_lower):
                    hyphenated = compound.replace(' ', '-')
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Consider hyphenating compound modifier',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[match.start():match.end()+10],
                        suggestion=f'Use "{hyphenated}" when modifying a noun',
                        rule_id='HYP001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class SerialCommaChecker(BaseChecker):
    """Checks for consistent serial comma usage."""
    
    CHECKER_NAME = "Serial Comma"
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        with_oxford = 0
        without_oxford = 0
        
        full_text = ' '.join(text for _, text in paragraphs if text)
        
        # Count Oxford comma usage
        with_oxford = len(re.findall(r',\s+\w+,\s+and\s+', full_text))
        without_oxford = len(re.findall(r',\s+\w+\s+and\s+', full_text))
        
        issues = []
        if with_oxford > 0 and without_oxford > 0:
            issues.append(self.create_issue(
                severity='Info',
                message=f'Inconsistent serial comma: {with_oxford} with, {without_oxford} without',
                context='Document-wide',
                paragraph_index=0,
                suggestion='Use consistent serial comma style throughout',
                rule_id='SER001'
            ))
        return issues


# =============================================================================
# REFERENCE CHECKERS
# =============================================================================

class EnhancedReferenceChecker(BaseChecker):
    """Checks cross-references."""
    
    CHECKER_NAME = "References"
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        
        refs = {'section': set(), 'table': set(), 'figure': set(), 'appendix': set()}
        defs = {'section': set(), 'table': set(), 'figure': set(), 'appendix': set()}
        
        full_text = ' '.join(text for _, text in paragraphs if text)
        
        # Find references
        for match in re.finditer(r'\b(Section|Table|Figure|Appendix)\s+(\d+(?:\.\d+)*|[A-Z])\b', full_text, re.IGNORECASE):
            ref_type = match.group(1).lower()
            ref_num = match.group(2)
            refs[ref_type].add(ref_num)
        
        # Find definitions (simplified - would need document structure)
        for match in re.finditer(r'^(\d+(?:\.\d+)*)\s+[A-Z]', full_text, re.MULTILINE):
            defs['section'].add(match.group(1))
        
        # Check for undefined references
        for ref_type in refs:
            for ref in refs[ref_type]:
                if ref_type == 'section' and ref not in defs['section']:
                    # Only flag if it looks like a real section number
                    if '.' in ref:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Reference to undefined {ref_type}: {ref}',
                            context=f'{ref_type.title()} {ref}',
                            paragraph_index=0,
                            suggestion='Verify this reference exists',
                            rule_id='REF001',
                            flagged_text=f'{ref_type} {ref}'
                        ))
        return issues


class HyperlinkChecker(BaseChecker):
    """Checks URL formatting."""
    
    CHECKER_NAME = "Hyperlinks"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for URLs
            for match in re.finditer(r'https?://[^\s<>"\']+', text):
                url = match.group()
                # Check for trailing punctuation
                if url[-1] in '.,;:!?)':
                    issue = self.create_validated_issue(
                        severity='Low',
                        message='URL may have trailing punctuation',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,
                        match_text=url,
                        match_start=match.start(),
                        match_end=match.end(),
                        context=url,
                        suggestion='Verify URL doesn\'t include trailing punctuation',
                        rule_id='URL001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


# =============================================================================
# CLARITY CHECKERS
# =============================================================================

class HedgingChecker(BaseChecker):
    """Detects hedging language."""
    
    CHECKER_NAME = "Hedging"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    HEDGING_PHRASES = [
        'it seems', 'appears to be', 'may possibly', 'might be', 'could be',
        'sort of', 'kind of', 'in some cases', 'to some extent', 'rather',
        'somewhat', 'fairly', 'quite', 'relatively', 'arguably',
        'I think', 'I believe', 'in my opinion', 'presumably', 'apparently',
    ]
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for phrase in self.HEDGING_PHRASES:
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Hedging language: "{phrase}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-15):match.end()+15],
                        suggestion='State facts directly without hedging',
                        rule_id='HDG001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class WeaselWordChecker(BaseChecker):
    """Detects weasel words."""
    
    CHECKER_NAME = "Weasel Words"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    WEASEL_PATTERNS = [
        'some experts', 'many people', 'it is said', 'critics say',
        'studies show', 'research suggests', 'it is believed',
        'it is thought', 'widely considered', 'generally accepted',
        'commonly known', 'obviously', 'clearly', 'of course',
        'naturally', 'needless to say', 'everyone knows',
    ]
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for pattern in self.WEASEL_PATTERNS:
                regex_pattern = r'\b' + re.escape(pattern) + r'\b'
                for match in re.finditer(regex_pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Medium',
                        message=f'Weasel word/phrase: "{pattern}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-15):match.end()+15],
                        suggestion='Cite specific sources or remove claim',
                        rule_id='WSL001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


class ClicheChecker(BaseChecker):
    """Detects clichés."""
    
    CHECKER_NAME = "Clichés"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    CLICHES = [
        'at the end of the day', 'think outside the box', 'low-hanging fruit',
        'paradigm shift', 'synergy', 'leverage', 'game-changer', 'best practice',
        'move the needle', 'circle back', 'deep dive', 'bandwidth',
        'take offline', 'drill down', 'boil the ocean', 'drink the kool-aid',
    ]
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            text_lower = text.lower()
            for cliche in self.CLICHES:
                pattern = r'\b' + re.escape(cliche) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Cliché: "{cliche}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0,match.start()-10):match.end()+10],
                        suggestion='Use more precise, original language',
                        rule_id='CLI001'
                    )
                    if issue:
                        issues.append(issue)
        return issues


# =============================================================================
# SENTENCE STRUCTURE CHECKERS
# =============================================================================

class DanglingModifierChecker(BaseChecker):
    """Detects potential dangling modifiers."""
    
    CHECKER_NAME = "Dangling Modifiers"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for -ing phrase at start followed by comma, then non-person subject
            pattern = r'^[A-Z][a-z]+ing\s+[^,]{5,30},\s+(the\s+(?:system|data|document|process|software|equipment|device))\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                issue = self.create_validated_issue(
                    severity='Medium',
                    message='Possible dangling modifier',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[:60],
                    suggestion='Ensure the subject matches the modifier',
                    rule_id='DNG001'
                )
                if issue:
                    issues.append(issue)
        return issues


class RunOnSentenceChecker(BaseChecker):
    """Detects run-on sentences."""
    
    CHECKER_NAME = "Run-on Sentences"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for comma splice
            for match in re.finditer(r',\s+(however|therefore|thus|hence|consequently)\s+', text, re.IGNORECASE):
                issue = self.create_validated_issue(
                    severity='Medium',
                    message='Possible comma splice before conjunctive adverb',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[max(0,match.start()-15):match.end()+15],
                    suggestion='Use semicolon or period before conjunctive adverb',
                    rule_id='RUN001'
                )
                if issue:
                    issues.append(issue)
        return issues


class SentenceFragmentChecker(BaseChecker):
    """Detects sentence fragments."""
    
    CHECKER_NAME = "Sentence Fragments"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text or len(text) < 10:
                continue
            # Check for subordinate clause without main clause
            match = re.match(r'^(Although|Though|Because|Since|If|Unless|While|When)\s+', text, re.IGNORECASE)
            if match:
                if '.' in text and len(text.split('.')[0]) < 50:
                    if not re.search(r'\b(is|are|was|were|has|have|shall|will|can|could|should|would)\b', 
                                    text.split('.')[0], re.IGNORECASE):
                        issue = self.create_validated_issue(
                            severity='Low',
                            message='Possible sentence fragment',
                            paragraph_index=idx,
                            original_paragraph=text,
                            normalized_paragraph=text,
                            match_text=text.split('.')[0],
                            match_start=0,
                            match_end=len(text.split('.')[0]),
                            context=text[:60],
                            suggestion='Ensure sentence has a main clause',
                            rule_id='FRG001'
                        )
                        if issue:
                            issues.append(issue)
        return issues


class ParallelStructureChecker(BaseChecker):
    """Checks parallel structure."""
    
    CHECKER_NAME = "Parallel Structure"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check both...and, either...or, not only...but also
            match = re.search(r'\bboth\s+\w+ing\b.*\band\s+to\s+\w+\b', text, re.IGNORECASE)
            if match:
                issue = self.create_validated_issue(
                    severity='Low',
                    message='Parallel structure issue in "both...and"',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[match.start():min(len(text), match.end()+20)],
                    suggestion='Use same grammatical form after both and and',
                    rule_id='PAR001'
                )
                if issue:
                    issues.append(issue)
        return issues


# =============================================================================
# STANDARDS COMPLIANCE CHECKERS
# =============================================================================

class MILSTDChecker(BaseChecker):
    """Checks MIL-STD compliance."""
    
    CHECKER_NAME = "MIL-STD Compliance"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], full_text: str = "", **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs if text)
        
        # Only check if appears to be defense-related
        if not re.search(r'\b(MIL-STD|DoD|defense|military|contractor)\b', full_text, re.IGNORECASE):
            return []
        
        issues = []
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for TBD without tracking number
            for match in re.finditer(r'\bTBD\b(?!\s*[-#]\s*\d)', text):
                issue = self.create_validated_issue(
                    severity='Medium',
                    message='MIL-STD: TBD should have tracking number',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[max(0,match.start()-15):match.end()+15],
                    suggestion='Add tracking number: e.g., TBD-001',
                    rule_id='MIL001'
                )
                if issue:
                    issues.append(issue)
        return issues


class DO178Checker(BaseChecker):
    """Checks DO-178C compliance."""
    
    CHECKER_NAME = "DO-178C Compliance"
    
    def check(self, paragraphs: List[Tuple[int, str]], full_text: str = "", **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs if text)
        
        # Only check if appears to be airborne-related
        if not re.search(r'\b(DO-178|DAL|airborne|avionics|aircraft)\b', full_text, re.IGNORECASE):
            return []
        
        issues = []
        # Check for DAL level
        if not re.search(r'\b(DAL\s*[A-E]|Level\s*[A-E])\b', full_text, re.IGNORECASE):
            issues.append(self.create_issue(
                severity='High',
                message='DO-178C: Development Assurance Level not specified',
                context='Document-wide',
                paragraph_index=0,
                suggestion='Specify DAL level (A-E)',
                rule_id='DO178001'
            ))
        return issues


# =============================================================================
# DOCUMENT STRUCTURE CHECKERS
# =============================================================================

class OrphanHeadingChecker(BaseChecker):
    """Detects orphan headings."""
    
    CHECKER_NAME = "Orphan Headings"
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        
        headings = []
        for idx, text in paragraphs:
            if not text:
                continue
            match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', text.strip())
            if match:
                headings.append({
                    'idx': idx,
                    'number': match.group(1),
                    'title': match.group(2),
                    'level': match.group(1).count('.') + 1
                })
        
        # Check for single child sections
        for i, heading in enumerate(headings):
            parent_num = heading['number']
            children = [h for h in headings[i+1:] 
                       if h['number'].startswith(parent_num + '.') 
                       and h['number'].count('.') == heading['number'].count('.') + 1]
            
            if len(children) == 1:
                child = children[0]
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Orphan heading: "{child["number"]}" is only subsection',
                    context=f'Under {parent_num}',
                    paragraph_index=child['idx'],
                    suggestion='Add more subsections or merge with parent',
                    rule_id='ORH001',
                    flagged_text=f'{child["number"]} {child["title"][:20]}'
                ))
        return issues


class EmptySectionChecker(BaseChecker):
    """Detects empty sections."""
    
    CHECKER_NAME = "Empty Sections"
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        
        heading_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+)$')
        section_starts = []
        
        for i, (idx, text) in enumerate(paragraphs):
            if text and heading_pattern.match(text.strip()):
                section_starts.append((i, idx, text.strip()))
        
        for i, (para_i, idx, heading_text) in enumerate(section_starts):
            end_para = section_starts[i + 1][0] if i + 1 < len(section_starts) else len(paragraphs)
            
            word_count = 0
            has_subheading = False
            for j in range(para_i + 1, end_para):
                if j < len(paragraphs) and paragraphs[j][1]:
                    if heading_pattern.match(paragraphs[j][1].strip()):
                        has_subheading = True
                        break
                    word_count += len(paragraphs[j][1].split())
            
            if not has_subheading and word_count < 10:
                issues.append(self.create_issue(
                    severity='Medium' if word_count == 0 else 'Low',
                    message=f'Empty section: "{heading_text}"' if word_count == 0 else f'Near-empty section ({word_count} words)',
                    context=heading_text,
                    paragraph_index=idx,
                    suggestion='Add content or remove section',
                    rule_id='EMP001',
                    flagged_text=heading_text[:40]
                ))
        return issues


class AccessibilityChecker(BaseChecker):
    """Basic accessibility checks."""
    
    CHECKER_NAME = "Accessibility"
    CHECKER_VERSION = "2.5.0"  # v2.5.0: Added provenance tracking
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        issues = []
        
        for idx, text in paragraphs:
            if not text:
                continue
            # Check for color-only references
            for match in re.finditer(r'\b(red|green|blue|yellow)\s+(text|item|section|area)\b', text, re.IGNORECASE):
                issue = self.create_validated_issue(
                    severity='Low',
                    message='Color-only reference may not be accessible',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[max(0,match.start()-15):match.end()+15],
                    suggestion='Add text labels or symbols in addition to color',
                    rule_id='ACC001'
                )
                if issue:
                    issues.append(issue)
        return issues


# =============================================================================
# EXPORT ALL CHECKERS
# =============================================================================

def get_all_v22_checkers():
    """Returns a dictionary of all v2.2 checker instances."""
    return {
        # Spelling & Grammar
        'spelling': SpellingChecker(),
        'grammar': GrammarChecker(),
        
        # Units & Numbers
        'units': UnitsChecker(),
        'number_format': NumberFormatChecker(),
        
        # Terminology
        'terminology': TerminologyChecker(),
        'tbd': TBDChecker(),
        'redundancy': RedundancyChecker(),
        
        # Enhanced Requirements
        'testability': TestabilityChecker(),
        'atomicity': AtomicityChecker(),
        'escape_clauses': EscapeClauseChecker(),
        
        # Typography
        'hyphenation': HyphenationChecker(),
        'serial_comma': SerialCommaChecker(),
        
        # References
        'enhanced_references': EnhancedReferenceChecker(),
        'hyperlinks': HyperlinkChecker(),
        
        # Clarity
        'hedging': HedgingChecker(),
        'weasel_words': WeaselWordChecker(),
        'cliches': ClicheChecker(),
        
        # Sentence Structure
        'dangling_modifiers': DanglingModifierChecker(),
        'run_on_sentences': RunOnSentenceChecker(),
        'sentence_fragments': SentenceFragmentChecker(),
        'parallel_structure': ParallelStructureChecker(),
        
        # Standards
        'mil_std': MILSTDChecker(),
        'do178': DO178Checker(),
        
        # Document Structure
        'orphan_headings': OrphanHeadingChecker(),
        'empty_sections': EmptySectionChecker(),
        'accessibility': AccessibilityChecker(),
    }


if __name__ == "__main__":
    print(f"AEGIS v2.2 Extended Checkers")
    print("=" * 50)
    checkers = get_all_v22_checkers()
    print(f"Total checkers: {len(checkers)}")
    for name, checker in checkers.items():
        print(f"  - {name}: {checker.CHECKER_NAME}")
