"""
Terminology Consistency Checker for AEGIS
====================================================
NLP checker for detecting inconsistent terminology usage.

Features:
- Detects when synonyms are used for the same concept
- Reports synonym groups found in document
- Suggests using consistent terminology

Inherits from NLPCheckerBase for consistent interface.
"""

import re
from typing import List, Tuple, Dict, Set, Optional, Any
from collections import Counter

from ..base import NLPCheckerBase, NLPIssue
from .wordnet import SemanticAnalyzer


class TerminologyConsistencyChecker(NLPCheckerBase):
    """
    Check for inconsistent terminology using WordNet.

    Finds cases where synonyms are used for the same concept,
    which can confuse readers.
    """

    CHECKER_NAME = "Terminology Consistency"
    CHECKER_VERSION = "1.0.0"

    # Words that are acceptable to vary (function words)
    ALLOW_VARIATION: Set[str] = {
        # Articles and determiners
        'the', 'a', 'an', 'this', 'that', 'these', 'those',
        # Common verbs
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'done',
        'will', 'would', 'shall', 'should',
        'can', 'could', 'may', 'might', 'must',
        'get', 'got', 'getting', 'gets',
        # Prepositions
        'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from',
        'of', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'over',
        # Conjunctions
        'and', 'or', 'but', 'nor', 'so', 'yet', 'both', 'either',
        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'its', 'our', 'their',
        # Common adverbs
        'not', 'also', 'only', 'just', 'very', 'then', 'now',
        # Numbers
        'one', 'two', 'three', 'first', 'second', 'third',
    }

    # Minimum word length to consider
    MIN_WORD_LENGTH = 3

    # Minimum occurrences to report
    MIN_OCCURRENCES = 2

    def __init__(
        self,
        enabled: bool = True,
        similarity_threshold: float = 0.85,
        min_occurrences: int = 2
    ):
        """
        Initialize the terminology consistency checker.

        Args:
            enabled: Whether the checker is enabled
            similarity_threshold: Minimum similarity for synonym detection
            min_occurrences: Minimum times a word must appear to be considered
        """
        super().__init__(enabled)
        self._analyzer: Optional[SemanticAnalyzer] = None
        self.similarity_threshold = similarity_threshold
        self.min_occurrences = min_occurrences

    def _initialize(self) -> bool:
        """Initialize the SemanticAnalyzer."""
        try:
            self._analyzer = SemanticAnalyzer(
                similarity_threshold=self.similarity_threshold
            )
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
        Check for terminology inconsistency in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected inconsistencies
        """
        issues = []

        # Collect all significant words across the document
        all_words = []
        word_counts: Dict[str, int] = Counter()

        for _, text in paragraphs:
            words = self._extract_words(text)
            all_words.extend(words)
            for word in words:
                word_counts[word.lower()] += 1

        # Filter to words that appear multiple times
        significant_words = [
            w for w in set(all_words)
            if word_counts.get(w.lower(), 0) >= self.min_occurrences
        ]

        if len(significant_words) < 2:
            return issues

        # Find synonym groups
        groups = self._analyzer.find_synonym_groups(
            significant_words,
            word_counts
        )

        # Report groups as potential inconsistencies
        for group in groups:
            if len(group.words) < 2:
                continue

            # Sort by frequency (most common first)
            sorted_words = sorted(
                group.words,
                key=lambda w: group.occurrences.get(w, 0),
                reverse=True
            )

            primary_word = sorted_words[0]
            other_words = sorted_words[1:]

            # Find first paragraph where inconsistency appears
            first_para_idx = 0
            context = ""
            for para_idx, text in paragraphs:
                text_lower = text.lower()
                if any(w in text_lower for w in other_words):
                    first_para_idx = para_idx
                    context = text[:100] + ('...' if len(text) > 100 else '')
                    break

            issues.append(self.create_issue(
                severity='Low',
                message=(
                    f"Potential terminology inconsistency: "
                    f"'{primary_word}' and '{other_words[0]}' "
                    f"may refer to the same concept"
                ),
                paragraph_index=first_para_idx,
                context=context,
                suggestion=(
                    f"Consider using '{primary_word}' consistently "
                    f"(appears {group.occurrences.get(primary_word, 0)} times) "
                    f"instead of varying between synonyms."
                ),
                rule_id='TERM001',
                category='Consistency',
                confidence=group.similarity_score
            ))

        return issues

    def _extract_words(self, text: str) -> List[str]:
        """Extract significant words from text."""
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        # Filter
        return [
            w for w in words
            if len(w) >= self.MIN_WORD_LENGTH
            and w not in self.ALLOW_VARIATION
        ]

    def get_synonym_report(
        self,
        paragraphs: List[Tuple[int, str]]
    ) -> Dict[str, Any]:
        """
        Get a detailed synonym analysis report.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            Dict with synonym groups and statistics
        """
        if not self._initialized:
            self._initialized = self._initialize()

        if not self._initialized or not self._analyzer:
            return {'error': 'Analyzer not available'}

        # Collect words
        all_words = []
        word_counts: Dict[str, int] = Counter()

        for _, text in paragraphs:
            words = self._extract_words(text)
            all_words.extend(words)
            for word in words:
                word_counts[word] += 1

        significant_words = [
            w for w in set(all_words)
            if word_counts.get(w, 0) >= self.min_occurrences
        ]

        groups = self._analyzer.find_synonym_groups(
            significant_words,
            word_counts
        )

        return {
            'total_words': len(all_words),
            'unique_words': len(set(all_words)),
            'significant_words': len(significant_words),
            'synonym_groups': [g.to_dict() for g in groups],
            'potential_inconsistencies': len(groups)
        }

    def check_word_pair(self, word1: str, word2: str) -> Dict[str, Any]:
        """
        Check if two words are potential synonyms.

        Args:
            word1: First word
            word2: Second word

        Returns:
            Dict with similarity info
        """
        if not self._initialized:
            self._initialized = self._initialize()

        if not self._initialized or not self._analyzer:
            return {'error': 'Analyzer not available'}

        similarity = self._analyzer.similarity(word1, word2)
        are_synonyms = self._analyzer.are_synonyms(word1, word2)

        return {
            'word1': word1,
            'word2': word2,
            'similarity': similarity,
            'are_synonyms': are_synonyms,
            'threshold': self.similarity_threshold
        }
