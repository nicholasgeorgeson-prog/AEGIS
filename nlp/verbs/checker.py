"""
Tense Consistency Checker for AEGIS
==============================================
NLP checker for detecting mixed verb tenses in documents.

Features:
- Detects mixed tenses within sentences
- Reports dominant tense in paragraphs
- Provides suggestions for consistency

Inherits from NLPCheckerBase for consistent interface.
"""

from typing import List, Tuple, Optional

from ..base import NLPCheckerBase, NLPIssue
from .pattern_en import VerbAnalyzer


class TenseConsistencyChecker(NLPCheckerBase):
    """
    Checker for verb tense consistency in documents.

    Detects sentences with mixed verb tenses and reports
    the dominant tense for context.
    """

    CHECKER_NAME = "Tense Consistency"
    CHECKER_VERSION = "1.0.0"

    # Minimum verbs needed to flag inconsistency
    MIN_VERBS_FOR_FLAG = 2

    def __init__(self, enabled: bool = True, min_verbs: int = 2):
        """
        Initialize the tense consistency checker.

        Args:
            enabled: Whether the checker is enabled
            min_verbs: Minimum verbs in sentence to flag inconsistency
        """
        super().__init__(enabled)
        self._analyzer: Optional[VerbAnalyzer] = None
        self.min_verbs = min_verbs

    def _initialize(self) -> bool:
        """Initialize the VerbAnalyzer."""
        try:
            self._analyzer = VerbAnalyzer()
            if not self._analyzer.is_available:
                self._init_error = self._analyzer.error
                return False
            return True
        except Exception as e:
            self._init_error = str(e)
            return False

    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Check for tense inconsistencies in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected inconsistencies
        """
        issues = []

        for para_idx, text in paragraphs:
            if not text or len(text.strip()) < 20:
                continue

            analysis = self._analyzer.analyze_tense_consistency(text)

            # Skip if not enough verbs detected
            if analysis.total_verbs < self.min_verbs:
                continue

            for inc in analysis.inconsistencies:
                # Only flag if there are enough verbs in the sentence
                if inc.get('verb_count', 0) < self.min_verbs:
                    continue

                tenses_found = inc.get('tenses_found', [])
                tenses_str = ', '.join(tenses_found)

                issues.append(self.create_issue(
                    severity='Low',
                    message=f"Mixed verb tenses in sentence: {tenses_str}",
                    paragraph_index=para_idx,
                    context=inc.get('sentence', ''),
                    suggestion=self._get_suggestion(
                        tenses_found,
                        analysis.dominant_tense
                    ),
                    rule_id='TENSE001',
                    category='Consistency',
                    confidence=0.7  # Tense detection can be imperfect
                ))

        return issues

    def _get_suggestion(
        self,
        tenses_found: List[str],
        dominant_tense: str
    ) -> str:
        """Generate a helpful suggestion for fixing tense inconsistency."""
        if dominant_tense and dominant_tense != 'unknown':
            return (
                f"Consider using {dominant_tense} tense consistently. "
                f"The paragraph primarily uses {dominant_tense} tense."
            )
        else:
            return (
                "Review verb tenses for consistency. "
                "Choose either past or present tense and use it throughout."
            )

    def get_paragraph_tense_report(self, text: str) -> dict:
        """
        Get a detailed tense analysis for a paragraph.

        Args:
            text: Paragraph text

        Returns:
            Dict with tense analysis details
        """
        if not self._initialized:
            self._initialized = self._initialize()

        if not self._initialized or not self._analyzer:
            return {'error': 'Analyzer not available'}

        analysis = self._analyzer.analyze_tense_consistency(text)
        return analysis.to_dict()

    def suggest_corrections(self, text: str, target_tense: str = None) -> List[dict]:
        """
        Suggest verb corrections to achieve tense consistency.

        Args:
            text: Text to analyze
            target_tense: Target tense ('past', 'present', 'future')
                         If None, uses dominant tense

        Returns:
            List of suggested corrections
        """
        if not self._initialized:
            self._initialized = self._initialize()

        if not self._initialized or not self._analyzer:
            return []

        analysis = self._analyzer.analyze_tense_consistency(text)

        if target_tense is None:
            target_tense = analysis.dominant_tense

        if target_tense == 'unknown':
            return []

        suggestions = []
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', text)

        for word in words:
            current_tense = self._analyzer.get_tense_name(word)

            if current_tense and current_tense != target_tense:
                base_form = self._analyzer.get_base_form(word)
                corrected = self._analyzer.conjugate_verb(
                    base_form,
                    tense=target_tense
                )

                if corrected and corrected != word:
                    suggestions.append({
                        'original': word,
                        'suggested': corrected,
                        'current_tense': current_tense,
                        'target_tense': target_tense
                    })

        return suggestions
