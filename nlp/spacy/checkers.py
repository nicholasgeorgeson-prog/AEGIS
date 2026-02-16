"""
spaCy-based Checkers for AEGIS
=========================================
Enhanced grammar and style checkers using spaCy NLP.

Checkers:
- EnhancedSubjectVerbChecker: Dependency-based agreement checking
- EnhancedDanglingModifierChecker: Parse tree modifier analysis
- SentenceComplexityChecker: Linguistic complexity metrics

All checkers inherit from NLPCheckerBase for consistent interface.
"""

from typing import List, Tuple, Optional

from ..base import NLPCheckerBase, NLPIssue
from .analyzer import SpacyAnalyzer


# Shared analyzer instance (lazy loaded)
_shared_analyzer: Optional[SpacyAnalyzer] = None


def get_shared_analyzer() -> SpacyAnalyzer:
    """Get or create the shared SpacyAnalyzer instance."""
    global _shared_analyzer
    if _shared_analyzer is None:
        _shared_analyzer = SpacyAnalyzer()
    return _shared_analyzer


class EnhancedSubjectVerbChecker(NLPCheckerBase):
    """
    Enhanced subject-verb agreement using spaCy dependency parsing.

    Replaces simple regex patterns with linguistic analysis for more
    accurate detection of agreement errors.

    Examples detected:
    - "The list of items are incorrect" (should be "is")
    - "The team have decided" (should be "has" in American English)
    - "Neither the manager nor the employees was informed"
    """

    CHECKER_NAME = "Subject-Verb Agreement (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._analyzer: Optional[SpacyAnalyzer] = None

    def _initialize(self) -> bool:
        """Initialize the spaCy analyzer."""
        self._analyzer = get_shared_analyzer()
        if not self._analyzer.is_available:
            self._init_error = self._analyzer.error
            return False
        return True

    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Check for subject-verb agreement errors in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected errors
        """
        issues = []

        for para_idx, text in paragraphs:
            pairs = self._analyzer.find_subject_verb_pairs(text)

            for pair in pairs:
                if pair.is_agreement_error:
                    # Determine the correction
                    suggestion = self._get_suggestion(pair)

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=(
                            f"Subject-verb agreement error: '{pair.subject}' "
                            f"({pair.subject_number}) paired with '{pair.verb}' "
                            f"({pair.verb_number})"
                        ),
                        paragraph_index=para_idx,
                        context=pair.sentence,
                        suggestion=suggestion,
                        rule_id='SVA001',
                        category='Grammar',
                        original_text=pair.verb,
                        replacement_text=self._get_corrected_verb(pair),
                        confidence=0.85
                    ))

        return issues

    def _get_suggestion(self, pair) -> str:
        """Generate a helpful suggestion for fixing the error."""
        if pair.subject_number == 'singular':
            return f"Use singular verb form to agree with '{pair.subject}'"
        else:
            return f"Use plural verb form to agree with '{pair.subject}'"

    def _get_corrected_verb(self, pair) -> str:
        """Attempt to generate the corrected verb form."""
        verb = pair.verb.lower()

        # Common irregular verbs
        singular_to_plural = {
            'is': 'are',
            'was': 'were',
            'has': 'have',
            'does': 'do',
        }

        plural_to_singular = {v: k for k, v in singular_to_plural.items()}

        if pair.subject_number == 'singular':
            if verb in plural_to_singular:
                return plural_to_singular[verb]
            # Add 's' for regular verbs
            if not verb.endswith('s'):
                return verb + 's'
        else:
            if verb in singular_to_plural:
                return singular_to_plural[verb]
            # Remove 's' for regular verbs
            if verb.endswith('s') and not verb.endswith('ss'):
                return verb[:-1]

        return pair.verb  # Return original if unsure


class EnhancedDanglingModifierChecker(NLPCheckerBase):
    """
    Detects dangling modifiers using parse tree analysis.

    A dangling modifier is a phrase that doesn't clearly modify
    the intended word, often because the subject is missing or
    doesn't logically connect.

    Examples detected:
    - "Walking down the street, the trees were beautiful."
      (Trees can't walk - the modifier dangles)
    - "Having finished the report, the meeting was adjourned."
      (The meeting didn't finish the report)
    """

    CHECKER_NAME = "Dangling Modifier (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    # Minimum confidence to report (dangling modifiers are tricky)
    MIN_CONFIDENCE = 0.6

    def __init__(self, enabled: bool = True, min_confidence: float = 0.6):
        super().__init__(enabled)
        self._analyzer: Optional[SpacyAnalyzer] = None
        self.min_confidence = min_confidence

    def _initialize(self) -> bool:
        """Initialize the spaCy analyzer."""
        self._analyzer = get_shared_analyzer()
        if not self._analyzer.is_available:
            self._init_error = self._analyzer.error
            return False
        return True

    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Check for dangling modifiers in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected issues
        """
        issues = []

        for para_idx, text in paragraphs:
            modifiers = self._analyzer.find_dangling_modifiers(text)

            for mod in modifiers:
                if mod.confidence < self.min_confidence:
                    continue

                issues.append(self.create_issue(
                    severity='Medium',
                    message=(
                        f"Possible dangling modifier: '{mod.modifier}' "
                        f"may not clearly modify '{mod.actual_subject}'"
                    ),
                    paragraph_index=para_idx,
                    context=mod.sentence,
                    suggestion=(
                        "Rewrite to make the subject of the modifier clear. "
                        "Consider: 'After [someone] [action], [subject] [verb]...'"
                    ),
                    rule_id='DM001',
                    category='Clarity',
                    confidence=mod.confidence
                ))

        return issues


class SentenceComplexityChecker(NLPCheckerBase):
    """
    Flags overly complex sentences using linguistic metrics.

    Analyzes:
    - Word count per sentence
    - Clause count and nesting depth
    - Subordinate clause count
    - Overall complexity score

    Technical writing guidelines recommend sentences under 25 words
    for optimal readability.
    """

    CHECKER_NAME = "Sentence Complexity"
    CHECKER_VERSION = "1.0.0"

    # Default thresholds (can be adjusted)
    DEFAULT_MAX_WORDS = 40
    DEFAULT_MAX_DEPTH = 4
    DEFAULT_MAX_SUBORDINATES = 3
    DEFAULT_COMPLEXITY_THRESHOLD = 0.7

    def __init__(
        self,
        enabled: bool = True,
        max_words: int = 40,
        max_depth: int = 4,
        max_subordinates: int = 3,
        complexity_threshold: float = 0.7
    ):
        super().__init__(enabled)
        self._analyzer: Optional[SpacyAnalyzer] = None
        self.max_words = max_words
        self.max_depth = max_depth
        self.max_subordinates = max_subordinates
        self.complexity_threshold = complexity_threshold

    def _initialize(self) -> bool:
        """Initialize the spaCy analyzer."""
        self._analyzer = get_shared_analyzer()
        if not self._analyzer.is_available:
            self._init_error = self._analyzer.error
            return False
        return True

    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Check for overly complex sentences in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected issues
        """
        issues = []

        for para_idx, text in paragraphs:
            complexities = self._analyzer.analyze_sentence_complexity(text)

            for complexity in complexities:
                if not self._is_too_complex(complexity):
                    continue

                # Determine primary reason for complexity
                reasons = self._get_complexity_reasons(complexity)
                suggestion = self._get_suggestion(complexity, reasons)

                severity = 'Low' if complexity.complexity_score < 0.8 else 'Medium'

                issues.append(self.create_issue(
                    severity=severity,
                    message=(
                        f"Complex sentence ({complexity.word_count} words, "
                        f"{complexity.clause_count} clauses): {reasons}"
                    ),
                    paragraph_index=para_idx,
                    context=complexity.sentence[:200] + ('...' if len(complexity.sentence) > 200 else ''),
                    suggestion=suggestion,
                    rule_id='SC001',
                    category='Readability',
                    confidence=complexity.complexity_score
                ))

        return issues

    def _is_too_complex(self, complexity) -> bool:
        """Determine if a sentence exceeds complexity thresholds."""
        return (
            complexity.is_complex or
            complexity.complexity_score >= self.complexity_threshold
        )

    def _get_complexity_reasons(self, complexity) -> str:
        """Get human-readable reasons for complexity."""
        reasons = []

        if complexity.word_count > self.max_words:
            reasons.append(f"too long ({complexity.word_count} words)")

        if complexity.max_depth > self.max_depth:
            reasons.append(f"deeply nested ({complexity.max_depth} levels)")

        if complexity.subordinate_clauses > self.max_subordinates:
            reasons.append(
                f"too many subordinate clauses ({complexity.subordinate_clauses})"
            )

        return '; '.join(reasons) if reasons else "high overall complexity"

    def _get_suggestion(self, complexity, reasons: str) -> str:
        """Generate a helpful suggestion for simplifying."""
        suggestions = []

        if 'too long' in reasons:
            suggestions.append(
                "Break into 2-3 shorter sentences"
            )

        if 'nested' in reasons:
            suggestions.append(
                "Reduce nesting by using simpler sentence structure"
            )

        if 'subordinate' in reasons:
            suggestions.append(
                "Convert some subordinate clauses to separate sentences"
            )

        if suggestions:
            return '. '.join(suggestions) + '.'
        return "Consider simplifying this sentence for better readability."
