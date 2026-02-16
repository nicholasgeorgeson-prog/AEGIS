"""
STE-100 Simplified Technical English Checker v1.0.0
===================================================
Date: 2026-02-04

Validates text against ASD-STE100 (Simplified Technical English)
specifications for aerospace and defense documentation.

Features:
- Approved vocabulary checking
- Unapproved word detection with suggestions
- Writing rule validation (sentence length, active voice, etc.)
- Technical term handling
- Compliance scoring

Author: AEGIS NLP Enhancement Project
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

VERSION = '1.0.0'


@dataclass
class STEViolation:
    """Represents an STE-100 violation."""
    word: str
    sentence: str
    violation_type: str  # 'unapproved_word', 'sentence_length', 'passive_voice', etc.
    suggestion: Optional[str]
    rule_number: Optional[int]
    severity: str  # 'error', 'warning', 'info'
    position: int


@dataclass
class STEAnalysis:
    """Complete STE-100 analysis result."""
    text: str
    violations: List[STEViolation]
    compliance_score: float  # 0-100
    approved_word_count: int
    unapproved_word_count: int
    technical_term_count: int
    sentence_stats: Dict[str, Any]
    summary: Dict[str, Any]


class STE100Checker:
    """
    STE-100 Simplified Technical English compliance checker.

    Validates text against ASD-STE100 specifications used in
    aerospace and defense technical documentation.
    """

    VERSION = VERSION

    # Maximum sentence lengths per STE-100
    MAX_PROCEDURAL_SENTENCE_LENGTH = 20
    MAX_DESCRIPTIVE_SENTENCE_LENGTH = 25

    def __init__(self, dictionary_path: str = None):
        """
        Initialize the STE-100 checker.

        Args:
            dictionary_path: Path to STE-100 dictionary JSON file
        """
        self.dictionary = {}
        self.approved_verbs = set()
        self.approved_nouns = set()
        self.approved_adjectives = set()
        self.approved_adverbs = set()
        self.unapproved_words = {}
        self.writing_rules = []
        self.technical_terms = set()  # Technical names allowed per STE-100 Section 1.5

        # Load dictionary
        if dictionary_path is None:
            # Default path
            script_dir = Path(__file__).parent
            dictionary_path = script_dir / 'data' / 'dictionaries' / 'ste100_dictionary.json'

        self._load_dictionary(str(dictionary_path))

    def _load_dictionary(self, path: str):
        """Load STE-100 dictionary from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)

            # Extract word lists
            if 'approved_verbs' in self.dictionary:
                verbs = self.dictionary['approved_verbs'].get('words', {})
                if isinstance(verbs, dict):
                    self.approved_verbs = set(verbs.keys())
                else:
                    self.approved_verbs = set(verbs)

            if 'approved_nouns' in self.dictionary:
                nouns = self.dictionary['approved_nouns'].get('words', [])
                self.approved_nouns = set(nouns) if isinstance(nouns, list) else set(nouns.keys())

            if 'approved_adjectives' in self.dictionary:
                adj = self.dictionary['approved_adjectives'].get('words', [])
                self.approved_adjectives = set(adj) if isinstance(adj, list) else set(adj.keys())

            if 'approved_adverbs' in self.dictionary:
                adv = self.dictionary['approved_adverbs'].get('words', [])
                self.approved_adverbs = set(adv) if isinstance(adv, list) else set(adv.keys())

            if 'unapproved_words' in self.dictionary:
                self.unapproved_words = self.dictionary['unapproved_words'].get('words', {})

            if 'writing_rules' in self.dictionary:
                self.writing_rules = self.dictionary['writing_rules'].get('rules', [])

            # Load technical terms (allowed per STE-100 Section 1.5)
            if 'technical_terms' in self.dictionary:
                terms = self.dictionary['technical_terms'].get('words', [])
                self.technical_terms = set(w.lower() for w in terms)

            logger.info(f"Loaded STE-100 dictionary: {len(self.approved_verbs)} verbs, "
                       f"{len(self.approved_nouns)} nouns, {len(self.unapproved_words)} unapproved, "
                       f"{len(self.technical_terms)} technical terms")

        except FileNotFoundError:
            logger.warning(f"STE-100 dictionary not found: {path}")
            self._load_minimal_dictionary()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse STE-100 dictionary: {e}")
            self._load_minimal_dictionary()

    def _load_minimal_dictionary(self):
        """Load minimal fallback dictionary."""
        # Common unapproved words with alternatives
        self.unapproved_words = {
            'accomplish': 'complete, do',
            'achieve': 'get, do',
            'acquire': 'get, obtain',
            'activate': 'start, turn on',
            'adequate': 'sufficient, enough',
            'assist': 'help',
            'attempt': 'try',
            'cease': 'stop',
            'commence': 'start, begin',
            'comprise': 'include, contain',
            'conduct': 'do',
            'demonstrate': 'show',
            'determine': 'find, calculate',
            'eliminate': 'remove',
            'enable': 'let, permit',
            'ensure': 'make sure',
            'establish': 'make, set',
            'exhibit': 'show',
            'facilitate': 'help, make easy',
            'generate': 'make, produce',
            'implement': 'do, start',
            'indicate': 'show',
            'initiate': 'start',
            'modify': 'change',
            'obtain': 'get',
            'perform': 'do',
            'possess': 'have',
            'preclude': 'prevent',
            'proceed': 'go, continue',
            'procure': 'get, buy',
            'provide': 'give, supply',
            'purchase': 'buy, get',
            'require': 'need',
            'terminate': 'stop, end',
            'transmit': 'send',
            'utilize': 'use',
            'verify': 'make sure, check',
        }

    def analyze(self, text: str) -> STEAnalysis:
        """
        Perform comprehensive STE-100 analysis.

        Args:
            text: Text to analyze

        Returns:
            STEAnalysis with violations and statistics
        """
        violations = []

        # Get violations from different checks
        violations.extend(self._check_vocabulary(text))
        violations.extend(self._check_sentence_length(text))
        violations.extend(self._check_passive_voice(text))
        violations.extend(self._check_writing_rules(text))

        # Calculate statistics
        stats = self._calculate_statistics(text, violations)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(text, violations)

        return STEAnalysis(
            text=text,
            violations=violations,
            compliance_score=compliance_score,
            approved_word_count=stats['approved_count'],
            unapproved_word_count=stats['unapproved_count'],
            technical_term_count=stats['technical_count'],
            sentence_stats=stats['sentence_stats'],
            summary=stats['summary']
        )

    def _check_vocabulary(self, text: str) -> List[STEViolation]:
        """Check for unapproved vocabulary."""
        violations = []

        # Tokenize
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        # Split into sentences for context
        sentences = re.split(r'(?<=[.!?])\s+', text)
        word_to_sentence = {}

        for sentence in sentences:
            sent_words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
            for word in sent_words:
                word_to_sentence[word] = sentence

        # Check each word
        seen_words = set()
        for i, word in enumerate(words):
            if word in seen_words:
                continue

            word_lower = word.lower()

            # Skip if it's an allowed technical term (STE-100 Section 1.5)
            if word_lower in self.technical_terms:
                continue

            # Check unapproved list
            if word_lower in self.unapproved_words:
                suggestion = self.unapproved_words[word_lower]
                violations.append(STEViolation(
                    word=word,
                    sentence=word_to_sentence.get(word, ''),
                    violation_type='unapproved_word',
                    suggestion=f"Use instead: {suggestion}",
                    rule_number=2,  # Rule 2: Use approved words only
                    severity='warning',
                    position=i
                ))
                seen_words.add(word_lower)

        return violations

    def _check_sentence_length(self, text: str) -> List[STEViolation]:
        """Check sentence length against STE-100 limits."""
        violations = []

        sentences = re.split(r'(?<=[.!?])\s+', text)

        for i, sentence in enumerate(sentences):
            words = sentence.split()
            word_count = len(words)

            # Determine if procedural (starts with verb) or descriptive
            is_procedural = self._is_procedural_sentence(sentence)
            max_length = self.MAX_PROCEDURAL_SENTENCE_LENGTH if is_procedural else self.MAX_DESCRIPTIVE_SENTENCE_LENGTH

            if word_count > max_length:
                violations.append(STEViolation(
                    word='',
                    sentence=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    violation_type='sentence_length',
                    suggestion=f"{'Procedural' if is_procedural else 'Descriptive'} sentence has "
                              f"{word_count} words (max {max_length}). Consider splitting.",
                    rule_number=1,  # Rule 1: Keep sentences short
                    severity='warning',
                    position=i
                ))

        return violations

    def _is_procedural_sentence(self, sentence: str) -> bool:
        """Check if sentence is procedural (starts with imperative verb)."""
        words = sentence.strip().split()
        if not words:
            return False

        first_word = words[0].lower()

        # Common imperative verbs
        procedural_starters = {
            'install', 'remove', 'connect', 'disconnect', 'attach', 'detach',
            'open', 'close', 'turn', 'press', 'push', 'pull', 'move', 'adjust',
            'check', 'verify', 'inspect', 'test', 'measure', 'apply', 'clean',
            'replace', 'repair', 'lubricate', 'tighten', 'loosen', 'do', 'make',
            'use', 'put', 'set', 'get', 'start', 'stop', 'go', 'run', 'read',
            'write', 'calculate', 'record', 'note', 'refer', 'see', 'ensure',
            'confirm', 'position', 'align', 'calibrate', 'configure'
        }

        return first_word in procedural_starters

    def _check_passive_voice(self, text: str) -> List[STEViolation]:
        """Check for passive voice (STE-100 prefers active voice)."""
        violations = []

        # Simple passive patterns
        passive_patterns = [
            (r'\b(is|are|was|were|be|been|being)\s+(\w+ed)\b(?!\s+to\b)', 'simple passive'),
            (r'\b(is|are|was|were|be|been|being)\s+(\w+en)\b', 'past participle passive'),
        ]

        sentences = re.split(r'(?<=[.!?])\s+', text)

        for i, sentence in enumerate(sentences):
            for pattern, pattern_type in passive_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                if matches:
                    violations.append(STEViolation(
                        word='',
                        sentence=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        violation_type='passive_voice',
                        suggestion="Consider rewriting in active voice",
                        rule_number=4,  # Rule 4: Use active voice
                        severity='info',
                        position=i
                    ))
                    break  # One violation per sentence

        return violations

    def _check_writing_rules(self, text: str) -> List[STEViolation]:
        """Check additional STE-100 writing rules."""
        violations = []

        sentences = re.split(r'(?<=[.!?])\s+', text)

        for i, sentence in enumerate(sentences):
            # Rule 5: Check for missing articles
            if self._missing_article(sentence):
                violations.append(STEViolation(
                    word='',
                    sentence=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    violation_type='missing_article',
                    suggestion="Consider adding articles (the, a, an) where appropriate",
                    rule_number=5,
                    severity='info',
                    position=i
                ))

            # Rule 9: Check for multiple instructions in one sentence
            if self._multiple_instructions(sentence):
                violations.append(STEViolation(
                    word='',
                    sentence=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    violation_type='multiple_instructions',
                    suggestion="Consider separating into multiple sentences (one instruction per sentence)",
                    rule_number=9,
                    severity='warning',
                    position=i
                ))

        return violations

    def _missing_article(self, sentence: str) -> bool:
        """Check for potential missing articles."""
        # Patterns that might indicate missing articles
        patterns = [
            r'\b(Install|Remove|Connect|Check)\s+[A-Z][a-z]+\s+(?!the|a|an)',
            r'\bto\s+[a-z]+\s+[A-Z][a-z]+\s+(?!the|a|an)',
        ]

        for pattern in patterns:
            if re.search(pattern, sentence):
                return True
        return False

    def _multiple_instructions(self, sentence: str) -> bool:
        """Check for multiple instructions in one sentence."""
        # Count imperative verbs
        verbs = ['install', 'remove', 'connect', 'attach', 'open', 'close',
                 'turn', 'press', 'check', 'verify', 'apply', 'clean', 'and then']

        count = 0
        sentence_lower = sentence.lower()
        for verb in verbs:
            count += sentence_lower.count(verb)

        return count > 2

    def _calculate_statistics(self, text: str, violations: List[STEViolation]) -> Dict[str, Any]:
        """Calculate text statistics."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Count word types
        approved_count = 0
        unapproved_count = 0
        technical_count = 0

        all_approved = self.approved_verbs | self.approved_nouns | self.approved_adjectives | self.approved_adverbs

        for word in words:
            word_lower = word.lower()
            if word_lower in all_approved:
                approved_count += 1
            elif word_lower in self.unapproved_words:
                unapproved_count += 1
            elif re.match(r'^[A-Z]{2,}$', word):  # Acronyms
                technical_count += 1

        # Sentence statistics
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

        sentence_stats = {
            'count': len(sentences),
            'avg_length': sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0,
            'max_length': max(sentence_lengths) if sentence_lengths else 0,
            'min_length': min(sentence_lengths) if sentence_lengths else 0,
            'over_limit': len([l for l in sentence_lengths if l > self.MAX_DESCRIPTIVE_SENTENCE_LENGTH])
        }

        # Violation summary
        violation_types = defaultdict(int)
        for v in violations:
            violation_types[v.violation_type] += 1

        summary = {
            'total_violations': len(violations),
            'by_type': dict(violation_types),
            'errors': len([v for v in violations if v.severity == 'error']),
            'warnings': len([v for v in violations if v.severity == 'warning']),
            'info': len([v for v in violations if v.severity == 'info'])
        }

        return {
            'approved_count': approved_count,
            'unapproved_count': unapproved_count,
            'technical_count': technical_count,
            'sentence_stats': sentence_stats,
            'summary': summary
        }

    def _calculate_compliance_score(self, text: str, violations: List[STEViolation]) -> float:
        """
        Calculate STE-100 compliance score (0-100).

        Higher is better.
        """
        if not text.strip():
            return 100.0

        # Start with 100 and deduct for violations
        score = 100.0

        # Deduct for each violation type
        for violation in violations:
            if violation.severity == 'error':
                score -= 5.0
            elif violation.severity == 'warning':
                score -= 2.0
            elif violation.severity == 'info':
                score -= 0.5

        # Ensure score is in valid range
        return max(0.0, min(100.0, score))

    def check_word(self, word: str) -> Dict[str, Any]:
        """
        Check if a single word is STE-100 approved.

        Args:
            word: Word to check

        Returns:
            Dict with status and suggestion if unapproved
        """
        word_lower = word.lower()

        all_approved = self.approved_verbs | self.approved_nouns | self.approved_adjectives | self.approved_adverbs

        if word_lower in all_approved:
            return {'approved': True, 'word': word}

        if word_lower in self.unapproved_words:
            return {
                'approved': False,
                'word': word,
                'suggestion': self.unapproved_words[word_lower]
            }

        return {'approved': None, 'word': word, 'note': 'Not in dictionary (may be technical term)'}

    def get_alternatives(self, word: str) -> Optional[str]:
        """Get approved alternatives for an unapproved word."""
        return self.unapproved_words.get(word.lower())


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_checker_instance: Optional[STE100Checker] = None


def get_ste100_checker() -> STE100Checker:
    """Get or create singleton STE-100 checker."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = STE100Checker()
    return _checker_instance


def check_ste100_compliance(text: str) -> Dict[str, Any]:
    """
    Check text for STE-100 compliance.

    Args:
        text: Text to analyze

    Returns:
        Dict with compliance score and violations
    """
    checker = get_ste100_checker()
    analysis = checker.analyze(text)

    return {
        'compliance_score': analysis.compliance_score,
        'total_violations': len(analysis.violations),
        'violations': [{
            'word': v.word,
            'type': v.violation_type,
            'suggestion': v.suggestion,
            'severity': v.severity,
            'rule': v.rule_number
        } for v in analysis.violations],
        'approved_words': analysis.approved_word_count,
        'unapproved_words': analysis.unapproved_word_count,
        'sentence_stats': analysis.sentence_stats,
        'summary': analysis.summary
    }


def get_ste100_alternatives(word: str) -> Optional[str]:
    """Get STE-100 approved alternatives for a word."""
    checker = get_ste100_checker()
    return checker.get_alternatives(word)


def is_ste100_approved(word: str) -> bool:
    """Check if a word is STE-100 approved."""
    checker = get_ste100_checker()
    result = checker.check_word(word)
    return result.get('approved', False) is True


__all__ = [
    'STE100Checker',
    'STEViolation',
    'STEAnalysis',
    'get_ste100_checker',
    'check_ste100_compliance',
    'get_ste100_alternatives',
    'is_ste100_approved',
    'VERSION'
]
