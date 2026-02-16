"""
AEGIS - Prose Linter Module
Version: 1.0.0
Created: February 3, 2026

Provides style guide enforcement and prose quality checking without external LLM dependencies.
Implements Vale-style rules for technical writing in aerospace/defense contexts.

Features:
- Custom rule definitions for technical writing
- Government/aerospace style guide compliance
- Passive voice detection
- Nominalization detection
- Sentence length and complexity analysis
- Jargon and acronym overuse detection
- Consistency checking (spelling variants, terminology)
- Air-gap compatible (no external API calls)

Usage:
    from prose_linter import ProseLinter

    linter = ProseLinter()
    results = linter.lint_text(document_text)

    # Or lint specific paragraphs
    issues = linter.lint_paragraphs(paragraphs)
"""

import re
import os
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum

# Optional spaCy integration
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class Severity(Enum):
    """Issue severity levels."""
    ERROR = "error"        # Must fix
    WARNING = "warning"    # Should fix
    SUGGESTION = "suggestion"  # Consider fixing
    INFO = "info"          # Informational


class Category(Enum):
    """Issue categories."""
    CLARITY = "clarity"
    CONSISTENCY = "consistency"
    GRAMMAR = "grammar"
    STYLE = "style"
    TERMINOLOGY = "terminology"
    READABILITY = "readability"
    GOVERNMENT = "government"  # Government writing standards


@dataclass
class LintIssue:
    """Represents a prose quality issue."""
    rule_id: str
    message: str
    severity: Severity
    category: Category
    text: str
    suggestion: Optional[str] = None
    position: int = 0
    line: int = 0
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'rule_id': self.rule_id,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'text': self.text,
            'suggestion': self.suggestion,
            'position': self.position,
            'line': self.line,
            'context': self.context
        }


class ProseLinter:
    """
    Prose quality and style guide compliance checker.

    Implements Vale-style rules for technical writing without requiring
    Vale installation or external dependencies.
    """

    VERSION = '1.1.0'  # v1.1.0: Added nominalization exceptions for technical terms

    # ==========================================================================
    # PASSIVE VOICE PATTERNS
    # ==========================================================================

    PASSIVE_INDICATORS = [
        r'\b(is|are|was|were|been|being|be)\s+\w+ed\b',
        r'\b(is|are|was|were|been|being|be)\s+\w+en\b',
        r'\bhas been\s+\w+ed\b',
        r'\bhave been\s+\w+ed\b',
        r'\bhad been\s+\w+ed\b',
        r'\bwill be\s+\w+ed\b',
        r'\bshall be\s+\w+ed\b',
        r'\bmust be\s+\w+ed\b',
    ]

    # Exceptions - legitimate passive constructions
    PASSIVE_EXCEPTIONS = {
        'is required', 'are required', 'is defined', 'are defined',
        'is specified', 'are specified', 'is provided', 'are provided',
        'is used', 'are used', 'is shown', 'are shown',
        'is given', 'are given', 'is based', 'are based'
    }

    # ==========================================================================
    # NOMINALIZATIONS (verbs turned into nouns - weakens writing)
    # ==========================================================================

    NOMINALIZATIONS = {
        'utilization': 'use',
        'implementation': 'implement',
        'documentation': 'document',
        'modification': 'modify',
        'determination': 'determine',
        'establishment': 'establish',
        'authorization': 'authorize',
        'coordination': 'coordinate',
        'verification': 'verify',
        'validation': 'validate',
        'facilitation': 'facilitate',
        'optimization': 'optimize',
        'prioritization': 'prioritize',
        'finalization': 'finalize',
        'initialization': 'initialize',
        'maximization': 'maximize',
        'minimization': 'minimize',
        'examination': 'examine',
        'investigation': 'investigate',
        'consideration': 'consider',
        'demonstration': 'demonstrate',
        'administration': 'administer',
        'consolidation': 'consolidate',
        'elimination': 'eliminate',
        'formulation': 'formulate',
        'termination': 'terminate',
        'continuation': 'continue',
        'notification': 'notify',
        'submission': 'submit',
        'transmission': 'transmit',
        'acquisition': 'acquire',
        'distribution': 'distribute',
        'accumulation': 'accumulate',
        'acceleration': 'accelerate',
        'cancellation': 'cancel',
        'compilation': 'compile',
        'completion': 'complete',
        'preparation': 'prepare',
        'presentation': 'present',
        'preservation': 'preserve',
        'recommendation': 'recommend',
        'specification': 'specify',
        'accomplishment': 'accomplish',
        'achievement': 'achieve',
        'advancement': 'advance',
        'development': 'develop',
        'improvement': 'improve',
        'measurement': 'measure',
        'replacement': 'replace',
        'requirement': 'require',  # Common in technical docs, flag sparingly
        'assessment': 'assess',
        'assignment': 'assign',
        'establishment': 'establish',
        'management': 'manage',
        'procurement': 'procure',
        'arrangement': 'arrange',
        'deployment': 'deploy',
        'employment': 'employ',
        'involvement': 'involve',
    }

    # ==========================================================================
    # WORDY PHRASES
    # ==========================================================================

    WORDY_PHRASES = {
        'in order to': 'to',
        'in order that': 'so that',
        'due to the fact that': 'because',
        'owing to the fact that': 'because',
        'in light of the fact that': 'because',
        'on the grounds that': 'because',
        'for the reason that': 'because',
        'by virtue of the fact that': 'because',
        'in the event that': 'if',
        'in the event of': 'if',
        'on the occasion of': 'when',
        'at the present time': 'now',
        'at this point in time': 'now',
        'at the current time': 'now',
        'at this moment in time': 'now',
        'for the purpose of': 'to',
        'with the purpose of': 'to',
        'with a view to': 'to',
        'in connection with': 'about',
        'in relation to': 'about',
        'with regard to': 'about',
        'with respect to': 'about',
        'in reference to': 'about',
        'pertaining to': 'about',
        'concerning the matter of': 'about',
        'as a matter of fact': '',  # Delete
        'as a consequence of': 'because of',
        'as a result of': 'because of',
        'in spite of the fact that': 'although',
        'despite the fact that': 'although',
        'regardless of the fact that': 'although',
        'notwithstanding the fact that': 'although',
        'a large number of': 'many',
        'a majority of': 'most',
        'a number of': 'some',
        'a sufficient number of': 'enough',
        'an adequate number of': 'enough',
        'the majority of': 'most',
        'a great deal of': 'much',
        'a large amount of': 'much',
        'until such time as': 'until',
        'during the time that': 'while',
        'during the course of': 'during',
        'in the course of': 'during',
        'subsequent to': 'after',
        'prior to': 'before',
        'in advance of': 'before',
        'in the near future': 'soon',
        'in the not too distant future': 'soon',
        'take into consideration': 'consider',
        'give consideration to': 'consider',
        'make a decision': 'decide',
        'reach a decision': 'decide',
        'come to a conclusion': 'conclude',
        'make an assumption': 'assume',
        'is able to': 'can',
        'has the ability to': 'can',
        'has the capability to': 'can',
        'is in a position to': 'can',
        'is capable of': 'can',
        'be in compliance with': 'comply with',
        'in compliance with': 'per',
        'in accordance with': 'per',
        'in conformance with': 'per',
        'conduct an investigation': 'investigate',
        'conduct an analysis': 'analyze',
        'perform an analysis': 'analyze',
        'make a determination': 'determine',
        'make an attempt': 'try',
        'make reference to': 'refer to',
        'make mention of': 'mention',
        'have a tendency to': 'tend to',
        'exhibits a tendency to': 'tends to',
        'on a daily basis': 'daily',
        'on a weekly basis': 'weekly',
        'on a monthly basis': 'monthly',
        'on an annual basis': 'annually',
        'on a regular basis': 'regularly',
        'on a continuous basis': 'continuously',
        'it is important to note that': '',  # Delete
        'it should be noted that': '',  # Delete
        'it is worth noting that': '',  # Delete
        'it is interesting to note that': '',  # Delete
        'needless to say': '',  # Delete
        'it goes without saying': '',  # Delete
        'basically': '',  # Delete
        'actually': '',  # Delete
        'in actual fact': '',  # Delete
    }

    # ==========================================================================
    # WEASEL WORDS (vague qualifiers)
    # ==========================================================================

    WEASEL_WORDS = [
        'very', 'really', 'quite', 'fairly', 'rather', 'somewhat',
        'extremely', 'incredibly', 'amazingly', 'remarkably',
        'basically', 'essentially', 'fundamentally', 'actually',
        'generally', 'typically', 'usually', 'normally', 'commonly',
        'approximately', 'roughly', 'about', 'around',  # OK in some contexts
        'various', 'numerous', 'several', 'many', 'few',  # OK if specific number unavailable
        'significant', 'substantial', 'considerable', 'meaningful',
        'effective', 'efficient', 'optimal', 'appropriate',  # Vague without metrics
    ]

    # ==========================================================================
    # GOVERNMENT/AEROSPACE STYLE RULES
    # ==========================================================================

    # Plain language violations (GPO Style Manual, Plain Writing Act)
    GOVERNMENT_JARGON = {
        'aforementioned': 'this/that/these',
        'heretofore': 'until now',
        'hereafter': 'from now on',
        'herein': 'in this document',
        'hereinafter': 'later in this document',
        'hereto': 'to this',
        'herewith': 'with this',
        'thereby': 'by that',
        'therein': 'in that',
        'thereof': 'of that',
        'thereto': 'to that',
        'therefrom': 'from that',
        'therewith': 'with that',
        'wherein': 'in which',
        'whereof': 'of which',
        'whereby': 'by which',
        'whereunder': 'under which',
        'inter alia': 'among other things',
        'mutatis mutandis': 'with necessary changes',
        'ipso facto': 'by that fact',
        'prima facie': 'on first appearance',
        'per se': 'by itself',
        'viz.': 'namely',
        'i.e.': 'that is',  # OK but consider spelling out
        'e.g.': 'for example',  # OK but consider spelling out
        'etc.': 'and so on',  # Often lazy - be specific
        'effectuate': 'carry out',
        'promulgate': 'issue',
        'pursuant to': 'under',
        'commence': 'begin/start',
        'terminate': 'end',
        'utilize': 'use',
        'endeavor': 'try',
        'ascertain': 'find out',
        'expedite': 'speed up',
        'facilitate': 'help/enable',
        'implement': 'carry out',  # Sometimes OK
        'indicate': 'show/say',
        'initiate': 'begin/start',
        'procure': 'get/buy',
        'transmit': 'send',
        'deem': 'consider',
        'render': 'make/give',
        'furnish': 'give/provide',
        'obtain': 'get',
        'retain': 'keep',
        'remit': 'send/pay',
    }

    # Shall/will/must usage (government requirements language)
    SHALL_RULES = {
        'should': 'Use "shall" for mandatory requirements, "should" for recommendations',
        'will': 'Use "shall" for contractor obligations, "will" for government actions',
        'must': '"Must" is acceptable for mandatory requirements but "shall" is preferred in contracts',
    }

    # ==========================================================================
    # CONSISTENCY PATTERNS
    # ==========================================================================

    # Common spelling variants to check for consistency
    SPELLING_VARIANTS = [
        ('acknowledgement', 'acknowledgment'),
        ('cancelled', 'canceled'),
        ('colour', 'color'),
        ('grey', 'gray'),
        ('judgement', 'judgment'),
        ('licence', 'license'),
        ('programme', 'program'),
        ('towards', 'toward'),
        ('backwards', 'backward'),
        ('forwards', 'forward'),
        ('afterwards', 'afterward'),
        ('whilst', 'while'),
        ('amongst', 'among'),
        ('focussed', 'focused'),
        ('modelled', 'modeled'),
        ('labelled', 'labeled'),
        ('travelled', 'traveled'),
        ('behaviour', 'behavior'),
        ('favour', 'favor'),
        ('honour', 'honor'),
        ('labour', 'labor'),
        ('neighbour', 'neighbor'),
        ('analyse', 'analyze'),
        ('organise', 'organize'),
        ('realise', 'realize'),
        ('recognise', 'recognize'),
        ('defence', 'defense'),
        ('offence', 'offense'),
        ('centre', 'center'),
        ('metre', 'meter'),
        ('theatre', 'theater'),
        ('cheque', 'check'),
        ('catalogue', 'catalog'),
        ('dialogue', 'dialog'),
        ('analogue', 'analog'),
        ('aeroplane', 'airplane'),
        ('aluminium', 'aluminum'),
    ]

    # Number format consistency
    NUMBER_PATTERNS = [
        (r'\b(\d+)\s*%', 'percent_symbol'),      # 50%
        (r'\b(\d+)\s+percent\b', 'percent_word'), # 50 percent
        (r'\b(\d+)\s+per\s+cent\b', 'percent_two_words'), # 50 per cent
    ]

    # ==========================================================================
    # SENTENCE COMPLEXITY
    # ==========================================================================

    MAX_SENTENCE_LENGTH = 35  # Words
    MAX_PARAGRAPH_LENGTH = 150  # Words
    IDEAL_SENTENCE_LENGTH = 20  # Words

    # ==========================================================================
    # INITIALIZATION
    # ==========================================================================

    def __init__(self,
                 use_spacy: bool = True,
                 style: str = 'technical',
                 custom_rules: Optional[Dict] = None):
        """
        Initialize the prose linter.

        Args:
            use_spacy: Whether to use spaCy for enhanced analysis
            style: Style guide to use ('technical', 'government', 'plain')
            custom_rules: Additional custom rules to apply
        """
        self.style = style
        self.custom_rules = custom_rules or {}
        self.nlp = None

        # Initialize spaCy if requested and available
        if use_spacy and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                print("Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm")

        # Compile regex patterns for performance
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.passive_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PASSIVE_INDICATORS
        ]

        self.wordy_patterns = {
            phrase: (re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE), replacement)
            for phrase, replacement in self.WORDY_PHRASES.items()
        }

        self.nominalization_patterns = {
            word: (re.compile(r'\b' + word + r's?\b', re.IGNORECASE), replacement)
            for word, replacement in self.NOMINALIZATIONS.items()
        }

        self.jargon_patterns = {
            word: (re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE), replacement)
            for word, replacement in self.GOVERNMENT_JARGON.items()
        }

        self.weasel_pattern = re.compile(
            r'\b(' + '|'.join(self.WEASEL_WORDS) + r')\b',
            re.IGNORECASE
        )

    # ==========================================================================
    # MAIN LINTING METHODS
    # ==========================================================================

    def lint_text(self,
                  text: str,
                  include_categories: Optional[List[Category]] = None,
                  exclude_categories: Optional[List[Category]] = None,
                  min_severity: Severity = Severity.INFO) -> Dict[str, Any]:
        """
        Lint a text document for prose quality issues.

        Args:
            text: The text to analyze
            include_categories: Only check these categories (None = all)
            exclude_categories: Skip these categories
            min_severity: Minimum severity level to report

        Returns:
            Dictionary with issues, statistics, and suggestions
        """
        issues: List[LintIssue] = []

        # Split into paragraphs and sentences
        paragraphs = self._split_paragraphs(text)
        sentences = self._split_sentences(text)

        # Run checks
        if self._should_check(Category.STYLE, include_categories, exclude_categories):
            issues.extend(self._check_passive_voice(text))
            issues.extend(self._check_nominalizations(text))
            issues.extend(self._check_wordy_phrases(text))

        if self._should_check(Category.CLARITY, include_categories, exclude_categories):
            issues.extend(self._check_weasel_words(text))

        if self._should_check(Category.READABILITY, include_categories, exclude_categories):
            issues.extend(self._check_sentence_length(sentences))
            issues.extend(self._check_paragraph_length(paragraphs))

        if self._should_check(Category.CONSISTENCY, include_categories, exclude_categories):
            issues.extend(self._check_spelling_consistency(text))
            issues.extend(self._check_number_format_consistency(text))

        if self._should_check(Category.GOVERNMENT, include_categories, exclude_categories):
            issues.extend(self._check_government_jargon(text))
            issues.extend(self._check_shall_usage(text))

        if self._should_check(Category.TERMINOLOGY, include_categories, exclude_categories):
            issues.extend(self._check_terminology_consistency(text))

        # Apply spaCy-enhanced checks
        if self.nlp and text:
            if self._should_check(Category.GRAMMAR, include_categories, exclude_categories):
                issues.extend(self._check_subject_verb_agreement(text))

        # Filter by severity
        severity_order = [Severity.INFO, Severity.SUGGESTION, Severity.WARNING, Severity.ERROR]
        min_index = severity_order.index(min_severity)
        issues = [i for i in issues if severity_order.index(i.severity) >= min_index]

        # Calculate statistics
        statistics = self._calculate_statistics(text, sentences, paragraphs, issues)

        return {
            'issues': [i.to_dict() for i in issues],
            'issue_count': len(issues),
            'statistics': statistics,
            'by_category': self._group_by_category(issues),
            'by_severity': self._group_by_severity(issues)
        }

    def lint_paragraphs(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """
        Lint individual paragraphs.

        Args:
            paragraphs: List of paragraph texts

        Returns:
            List of results per paragraph
        """
        results = []
        for i, para in enumerate(paragraphs):
            result = self.lint_text(para)
            result['paragraph_index'] = i
            results.append(result)
        return results

    # ==========================================================================
    # INDIVIDUAL CHECKS
    # ==========================================================================

    def _check_passive_voice(self, text: str) -> List[LintIssue]:
        """Check for passive voice constructions."""
        issues = []

        for pattern in self.passive_patterns:
            for match in pattern.finditer(text):
                matched_text = match.group(0).lower()

                # Skip known exceptions
                if any(exc in matched_text for exc in self.PASSIVE_EXCEPTIONS):
                    continue

                # Get context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]

                issues.append(LintIssue(
                    rule_id='PASSIVE001',
                    message='Passive voice detected. Consider using active voice for clarity.',
                    severity=Severity.SUGGESTION,
                    category=Category.STYLE,
                    text=match.group(0),
                    suggestion='Rewrite in active voice (who does what)',
                    position=match.start(),
                    context=f"...{context}..."
                ))

        return issues

    # v1.1.0: Common technical document terms that are NOT weak writing
    # These are standard process nouns in aerospace/defense documents
    # v4.0.0: Expanded list of technical document terms that are standard nouns
    NOMINALIZATION_EXCEPTIONS = {
        # Core document/process nouns
        'documentation', 'verification', 'validation', 'modification',
        'specification', 'configuration', 'authorization', 'coordination',
        'certification', 'qualification', 'implementation', 'requirement',
        'assessment', 'management', 'development', 'measurement',
        'inspection', 'notification', 'preparation', 'recommendation',
        'determination', 'identification', 'classification', 'registration',
        'administration', 'operation', 'installation', 'maintenance',
        'calibration', 'evaluation', 'investigation', 'examination',
        'demonstration', 'presentation', 'organization', 'distribution',
        'transmission', 'communication', 'transportation', 'interpretation',
        'application', 'allocation', 'appropriation', 'consideration',
        # v4.0.0: Additional standard aerospace/defense terms
        'integration', 'optimization', 'utilization', 'fabrication',
        'simulation', 'automation', 'standardization', 'normalization',
        'customization', 'initialization', 'finalization', 'termination',
        'continuation', 'acceleration', 'deceleration', 'propulsion',
        'navigation', 'orientation', 'stabilization', 'oscillation',
        'vibration', 'radiation', 'isolation', 'separation', 'filtration',
        'regulation', 'modulation', 'amplification', 'attenuation',
        'encryption', 'decryption', 'authentication', 'authorization',
        'notification', 'publication', 'compilation', 'acquisition',
        'procurement', 'deployment', 'decommission', 'disposal',
        'preservation', 'restoration', 'remediation', 'mitigation',
        'escalation', 'resolution', 'correlation', 'aggregation',
        'consolidation', 'reconciliation', 'documentation', 'annotation',
    }

    def _check_nominalizations(self, text: str) -> List[LintIssue]:
        """Check for nominalizations (hidden verbs)."""
        issues = []

        for word, (pattern, verb) in self.nominalization_patterns.items():
            for match in pattern.finditer(text):
                matched_word = match.group(0).lower()

                # v1.1.0: Skip common technical document terms
                if matched_word in self.NOMINALIZATION_EXCEPTIONS:
                    continue

                # Get context
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]

                issues.append(LintIssue(
                    rule_id='NOMINAL001',
                    message=f'Nominalization detected: "{match.group(0)}" hides the action.',
                    severity=Severity.SUGGESTION,
                    category=Category.STYLE,
                    text=match.group(0),
                    suggestion=f'Consider using the verb form: "{verb}"',
                    position=match.start(),
                    context=f"...{context}..."
                ))

        return issues

    def _check_wordy_phrases(self, text: str) -> List[LintIssue]:
        """Check for wordy phrases that can be simplified."""
        issues = []

        for phrase, (pattern, replacement) in self.wordy_patterns.items():
            for match in pattern.finditer(text):
                suggestion = f'Replace with "{replacement}"' if replacement else 'Consider deleting'

                issues.append(LintIssue(
                    rule_id='WORDY001',
                    message=f'Wordy phrase: "{match.group(0)}"',
                    severity=Severity.SUGGESTION,
                    category=Category.STYLE,
                    text=match.group(0),
                    suggestion=suggestion,
                    position=match.start()
                ))

        return issues

    def _check_weasel_words(self, text: str) -> List[LintIssue]:
        """Check for vague qualifiers (weasel words)."""
        issues = []

        for match in self.weasel_pattern.finditer(text):
            word = match.group(0).lower()

            # Get context to determine if usage is legitimate
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].lower()

            # Skip some legitimate uses
            if word in ('about', 'approximately', 'roughly') and re.search(r'\d', context):
                continue  # OK with numbers

            issues.append(LintIssue(
                rule_id='WEASEL001',
                message=f'Vague qualifier: "{match.group(0)}". Can you be more specific?',
                severity=Severity.INFO,
                category=Category.CLARITY,
                text=match.group(0),
                suggestion='Consider using specific numbers or removing this word',
                position=match.start(),
                context=f"...{context}..."
            ))

        return issues

    def _check_sentence_length(self, sentences: List[str]) -> List[LintIssue]:
        """Check for overly long sentences."""
        issues = []

        position = 0
        for sentence in sentences:
            word_count = len(sentence.split())

            if word_count > self.MAX_SENTENCE_LENGTH:
                issues.append(LintIssue(
                    rule_id='LENGTH001',
                    message=f'Sentence too long ({word_count} words). Consider breaking into smaller sentences.',
                    severity=Severity.WARNING,
                    category=Category.READABILITY,
                    text=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    suggestion=f'Try to keep sentences under {self.MAX_SENTENCE_LENGTH} words',
                    position=position
                ))
            elif word_count > self.IDEAL_SENTENCE_LENGTH:
                issues.append(LintIssue(
                    rule_id='LENGTH002',
                    message=f'Consider shortening this sentence ({word_count} words).',
                    severity=Severity.INFO,
                    category=Category.READABILITY,
                    text=sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    suggestion=f'Ideal sentence length is around {self.IDEAL_SENTENCE_LENGTH} words',
                    position=position
                ))

            position += len(sentence)

        return issues

    def _check_paragraph_length(self, paragraphs: List[str]) -> List[LintIssue]:
        """Check for overly long paragraphs."""
        issues = []

        position = 0
        for para in paragraphs:
            word_count = len(para.split())

            if word_count > self.MAX_PARAGRAPH_LENGTH:
                issues.append(LintIssue(
                    rule_id='PARA001',
                    message=f'Paragraph too long ({word_count} words). Consider breaking into smaller paragraphs.',
                    severity=Severity.WARNING,
                    category=Category.READABILITY,
                    text=para[:150] + '...',
                    suggestion=f'Keep paragraphs under {self.MAX_PARAGRAPH_LENGTH} words for readability',
                    position=position
                ))

            position += len(para)

        return issues

    def _check_spelling_consistency(self, text: str) -> List[LintIssue]:
        """Check for inconsistent spelling variants."""
        issues = []
        found_variants = {}

        for variant1, variant2 in self.SPELLING_VARIANTS:
            pattern1 = re.compile(r'\b' + variant1 + r'\b', re.IGNORECASE)
            pattern2 = re.compile(r'\b' + variant2 + r'\b', re.IGNORECASE)

            matches1 = list(pattern1.finditer(text))
            matches2 = list(pattern2.finditer(text))

            if matches1 and matches2:
                # Both variants found - inconsistency
                all_matches = matches1 + matches2
                for match in all_matches[1:]:  # Skip first occurrence
                    issues.append(LintIssue(
                        rule_id='CONSIST001',
                        message=f'Inconsistent spelling: both "{variant1}" and "{variant2}" used.',
                        severity=Severity.WARNING,
                        category=Category.CONSISTENCY,
                        text=match.group(0),
                        suggestion=f'Choose one spelling and use it consistently',
                        position=match.start()
                    ))

        return issues

    def _check_number_format_consistency(self, text: str) -> List[LintIssue]:
        """Check for inconsistent number formatting."""
        issues = []
        formats_found = set()

        for pattern_str, format_name in self.NUMBER_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(text):
                formats_found.add(format_name)

        if len(formats_found) > 1:
            issues.append(LintIssue(
                rule_id='CONSIST002',
                message='Inconsistent percentage formatting (% symbol vs "percent" word).',
                severity=Severity.WARNING,
                category=Category.CONSISTENCY,
                text='Multiple formats found',
                suggestion='Use either "50%" or "50 percent" consistently'
            ))

        return issues

    def _check_government_jargon(self, text: str) -> List[LintIssue]:
        """Check for government/legal jargon that should be simplified."""
        issues = []

        for word, (pattern, replacement) in self.jargon_patterns.items():
            for match in pattern.finditer(text):
                issues.append(LintIssue(
                    rule_id='GOV001',
                    message=f'Government jargon: "{match.group(0)}"',
                    severity=Severity.SUGGESTION,
                    category=Category.GOVERNMENT,
                    text=match.group(0),
                    suggestion=f'Plain language alternative: "{replacement}"',
                    position=match.start()
                ))

        return issues

    def _check_shall_usage(self, text: str) -> List[LintIssue]:
        """Check shall/will/must usage for government documents."""
        issues = []

        # Check for "should" where "shall" might be needed
        should_pattern = re.compile(r'\b(should)\b(?!\s+not)', re.IGNORECASE)
        for match in should_pattern.finditer(text):
            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # Look for requirement indicators
            if any(word in context.lower() for word in ['contractor', 'requirement', 'comply', 'must', 'mandatory']):
                issues.append(LintIssue(
                    rule_id='GOV002',
                    message='Consider "shall" for mandatory requirements (government contracts).',
                    severity=Severity.INFO,
                    category=Category.GOVERNMENT,
                    text=match.group(0),
                    suggestion='"Should" implies recommendation; "shall" implies obligation',
                    position=match.start(),
                    context=f"...{context}..."
                ))

        return issues

    def _check_terminology_consistency(self, text: str) -> List[LintIssue]:
        """Check for inconsistent terminology usage."""
        issues = []

        # Common term pairs that should be consistent
        term_pairs = [
            (['program', 'programme'], 'program/programme'),
            (['data is', 'data are'], 'data is/are'),
            (['team is', 'team are'], 'team is/are'),
            (['staff is', 'staff are'], 'staff is/are'),
        ]

        for terms, description in term_pairs:
            found = []
            for term in terms:
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    found.append(term)

            if len(found) > 1:
                issues.append(LintIssue(
                    rule_id='TERM001',
                    message=f'Inconsistent terminology: {", ".join(found)}',
                    severity=Severity.WARNING,
                    category=Category.TERMINOLOGY,
                    text=description,
                    suggestion='Use one term consistently throughout the document'
                ))

        return issues

    def _check_subject_verb_agreement(self, text: str) -> List[LintIssue]:
        """Use spaCy to check for subject-verb agreement (enhanced)."""
        issues = []

        if not self.nlp:
            return issues

        doc = self.nlp(text)

        for sent in doc.sents:
            # Look for collective nouns with wrong verb form
            for token in sent:
                if token.dep_ == 'nsubj' and token.pos_ == 'NOUN':
                    verb = token.head
                    if verb.pos_ == 'VERB':
                        # Check for common agreement errors
                        # This is simplified - real grammar checking is complex
                        if token.text.lower() in ['data', 'criteria', 'media', 'phenomena']:
                            # These can be singular or plural - flag for review
                            issues.append(LintIssue(
                                rule_id='GRAM001',
                                message=f'Check subject-verb agreement with "{token.text}"',
                                severity=Severity.INFO,
                                category=Category.GRAMMAR,
                                text=sent.text,
                                suggestion=f'"{token.text}" can be treated as singular or plural. Check your style guide.',
                                position=token.idx
                            ))

        return issues

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Simple sentence splitting
            pattern = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(pattern, text)
            return [s.strip() for s in sentences if s.strip()]

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _should_check(self,
                      category: Category,
                      include: Optional[List[Category]],
                      exclude: Optional[List[Category]]) -> bool:
        """Determine if a category should be checked."""
        if include and category not in include:
            return False
        if exclude and category in exclude:
            return False
        return True

    def _calculate_statistics(self,
                             text: str,
                             sentences: List[str],
                             paragraphs: List[str],
                             issues: List[LintIssue]) -> Dict[str, Any]:
        """Calculate text statistics."""
        words = text.split()
        word_count = len(words)

        # Sentence statistics
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

        # Paragraph statistics
        para_lengths = [len(p.split()) for p in paragraphs]
        avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0

        # Passive voice count
        passive_count = len([i for i in issues if i.rule_id.startswith('PASSIVE')])
        passive_percentage = (passive_count / len(sentences) * 100) if sentences else 0

        return {
            'word_count': word_count,
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_paragraph_length': round(avg_para_length, 1),
            'longest_sentence': max(sentence_lengths) if sentence_lengths else 0,
            'passive_voice_percentage': round(passive_percentage, 1),
            'issue_density': round(len(issues) / word_count * 1000, 2) if word_count else 0  # Issues per 1000 words
        }

    def _group_by_category(self, issues: List[LintIssue]) -> Dict[str, int]:
        """Group issues by category."""
        counts = defaultdict(int)
        for issue in issues:
            counts[issue.category.value] += 1
        return dict(counts)

    def _group_by_severity(self, issues: List[LintIssue]) -> Dict[str, int]:
        """Group issues by severity."""
        counts = defaultdict(int)
        for issue in issues:
            counts[issue.severity.value] += 1
        return dict(counts)

    # ==========================================================================
    # RULE CUSTOMIZATION
    # ==========================================================================

    def add_custom_rule(self,
                       rule_id: str,
                       pattern: str,
                       message: str,
                       severity: Severity = Severity.SUGGESTION,
                       category: Category = Category.STYLE,
                       suggestion: Optional[str] = None):
        """
        Add a custom lint rule.

        Args:
            rule_id: Unique identifier for the rule
            pattern: Regex pattern to match
            message: Error message to display
            severity: Issue severity
            category: Issue category
            suggestion: Suggested fix
        """
        self.custom_rules[rule_id] = {
            'pattern': re.compile(pattern, re.IGNORECASE),
            'message': message,
            'severity': severity,
            'category': category,
            'suggestion': suggestion
        }

    def disable_rule(self, rule_id: str):
        """Disable a rule by ID."""
        # Implementation would track disabled rules
        pass

    def enable_rule(self, rule_id: str):
        """Enable a previously disabled rule."""
        pass

    # ==========================================================================
    # EXPORT METHODS
    # ==========================================================================

    def export_rules(self) -> Dict[str, Any]:
        """Export all rules for documentation."""
        return {
            'passive_patterns': len(self.PASSIVE_INDICATORS),
            'wordy_phrases': len(self.WORDY_PHRASES),
            'nominalizations': len(self.NOMINALIZATIONS),
            'government_jargon': len(self.GOVERNMENT_JARGON),
            'weasel_words': len(self.WEASEL_WORDS),
            'spelling_variants': len(self.SPELLING_VARIANTS),
            'custom_rules': len(self.custom_rules)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def lint_document(text: str,
                  style: str = 'technical',
                  min_severity: str = 'suggestion') -> Dict[str, Any]:
    """
    Quick function to lint a document.

    Args:
        text: Document text
        style: Style guide ('technical', 'government', 'plain')
        min_severity: Minimum severity ('error', 'warning', 'suggestion', 'info')

    Returns:
        Linting results
    """
    linter = ProseLinter(style=style)
    severity_map = {
        'error': Severity.ERROR,
        'warning': Severity.WARNING,
        'suggestion': Severity.SUGGESTION,
        'info': Severity.INFO
    }
    return linter.lint_text(text, min_severity=severity_map.get(min_severity, Severity.SUGGESTION))


def get_readability_score(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics.

    Args:
        text: Document text

    Returns:
        Dictionary of readability scores
    """
    try:
        import textstat
        return {
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
            'smog_index': textstat.smog_index(text),
            'coleman_liau_index': textstat.coleman_liau_index(text),
            'automated_readability_index': textstat.automated_readability_index(text),
            'dale_chall_readability_score': textstat.dale_chall_readability_score(text),
            'difficult_words': textstat.difficult_words(text),
            'linsear_write_formula': textstat.linsear_write_formula(text),
            'gunning_fog': textstat.gunning_fog(text),
            'reading_time_seconds': textstat.reading_time(text, ms_per_char=14.69)
        }
    except ImportError:
        # Fallback without textstat
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'note': 'Install textstat for detailed readability metrics'
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"Linting: {filepath}\n")
        results = lint_document(text)

        print(f"Found {results['issue_count']} issues:\n")

        for issue in results['issues'][:20]:  # Show first 20
            print(f"[{issue['severity'].upper()}] {issue['rule_id']}: {issue['message']}")
            if issue['suggestion']:
                print(f"  Suggestion: {issue['suggestion']}")
            print()

        print("\nStatistics:")
        for key, value in results['statistics'].items():
            print(f"  {key}: {value}")
    else:
        # Demo
        sample_text = """
        In order to effectuate the implementation of the new system, the team
        should take into consideration the various requirements that have been
        specified by the stakeholders. The documentation will be utilized by
        the contractor for the purpose of verification and validation activities.

        It should be noted that the data is being processed on a daily basis,
        and approximately 50% of the records require manual review. The program
        was cancelled due to the fact that the programme exceeded its budget.
        """

        print("Demo: Linting sample text\n")
        results = lint_document(sample_text)

        print(f"Found {results['issue_count']} issues:\n")
        for issue in results['issues']:
            print(f"[{issue['severity'].upper()}] {issue['rule_id']}: {issue['message']}")
            if issue['suggestion']:
                print(f"  Suggestion: {issue['suggestion']}")
            print()
