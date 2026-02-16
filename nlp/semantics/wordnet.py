"""
Semantic Analyzer using WordNet for AEGIS
====================================================
Provides semantic analysis for terminology consistency.

Features:
- Synonym detection via WordNet
- Semantic similarity calculation
- Antonym detection
- Synonym group identification for consistency checking

Requires: pip install nltk
Data: python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
"""

from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field

from ..base import NLPIntegrationBase


@dataclass
class SynonymGroup:
    """A group of synonyms found in text."""
    words: Set[str] = field(default_factory=set)
    similarity_score: float = 0.0
    occurrences: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'words': list(self.words),
            'similarity_score': self.similarity_score,
            'occurrences': self.occurrences,
        }


class SemanticAnalyzer(NLPIntegrationBase):
    """
    WordNet-based semantic analysis.

    Detects terminology inconsistency through synonym detection.
    """

    INTEGRATION_NAME = "WordNet"
    INTEGRATION_VERSION = "1.0.0"

    # Similarity threshold for grouping synonyms
    DEFAULT_SIMILARITY_THRESHOLD = 0.8

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the semantic analyzer.

        Args:
            similarity_threshold: Minimum similarity to consider words synonyms
        """
        super().__init__()
        self._wn = None
        self._similarity_threshold = similarity_threshold
        self._initialize()

    def _initialize(self):
        """Initialize WordNet."""
        try:
            from nltk.corpus import wordnet as wn
            import nltk

            # Try to use WordNet - download if needed
            try:
                wn.synsets('test')
            except LookupError:
                # v5.0.0: Attempt local-only NLTK data load (no internet)
                # NLTK_DATA env var is set at startup to point to bundled data
                try:
                    nltk.download('wordnet', quiet=True, raise_on_error=False)
                    nltk.download('omw-1.4', quiet=True, raise_on_error=False)
                except Exception:
                    pass  # Data not available locally — WordNet will be disabled

            self._wn = wn
            self._available = True

        except ImportError as e:
            self._error = f"nltk not installed: {e}"
            self._available = False
        except Exception as e:
            self._error = f"Failed to initialize WordNet: {e}"
            self._available = False

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the WordNet integration."""
        return {
            'available': self.is_available,
            'error': self._error,
            'similarity_threshold': self._similarity_threshold,
            'features': ['synonyms', 'antonyms', 'similarity', 'synonym_groups']
            if self.is_available else []
        }

    def get_synonyms(self, word: str) -> Set[str]:
        """
        Get all synonyms for a word.

        Args:
            word: Word to find synonyms for

        Returns:
            Set of synonym strings
        """
        if not self.is_available:
            return set()

        synonyms = set()
        try:
            for syn in self._wn.synsets(word):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ')
                    if synonym.lower() != word.lower():
                        synonyms.add(synonym.lower())
        except Exception:
            pass

        return synonyms

    def get_antonyms(self, word: str) -> Set[str]:
        """
        Get all antonyms for a word.

        Args:
            word: Word to find antonyms for

        Returns:
            Set of antonym strings
        """
        if not self.is_available:
            return set()

        antonyms = set()
        try:
            for syn in self._wn.synsets(word):
                for lemma in syn.lemmas():
                    for ant in lemma.antonyms():
                        antonyms.add(ant.name().replace('_', ' ').lower())
        except Exception:
            pass

        return antonyms

    def similarity(self, word1: str, word2: str) -> float:
        """
        Calculate semantic similarity between two words.

        Uses Wu-Palmer similarity measure.

        Args:
            word1: First word
            word2: Second word

        Returns:
            Similarity score 0.0 to 1.0 (1.0 = identical meaning)
        """
        if not self.is_available:
            return 0.0

        if word1.lower() == word2.lower():
            return 1.0

        try:
            synsets1 = self._wn.synsets(word1)
            synsets2 = self._wn.synsets(word2)

            if not synsets1 or not synsets2:
                return 0.0

            max_sim = 0.0
            for s1 in synsets1[:3]:  # Limit to top 3 senses for performance
                for s2 in synsets2[:3]:
                    try:
                        sim = s1.wup_similarity(s2)
                        if sim and sim > max_sim:
                            max_sim = sim
                    except Exception:
                        continue

            return max_sim

        except Exception:
            return 0.0

    def are_synonyms(self, word1: str, word2: str) -> bool:
        """
        Check if two words are synonyms.

        Args:
            word1: First word
            word2: Second word

        Returns:
            True if words are synonyms (above similarity threshold)
        """
        # Direct synonym check
        synonyms1 = self.get_synonyms(word1)
        if word2.lower() in synonyms1:
            return True

        # Similarity check
        sim = self.similarity(word1, word2)
        return sim >= self._similarity_threshold

    def find_synonym_groups(
        self,
        words: List[str],
        word_counts: Optional[Dict[str, int]] = None
    ) -> List[SynonymGroup]:
        """
        Group words that are synonyms of each other.

        Useful for detecting terminology inconsistency.

        Args:
            words: List of words to analyze
            word_counts: Optional dict of word occurrence counts

        Returns:
            List of SynonymGroup objects
        """
        if not self.is_available:
            return []

        if not words:
            return []

        # Deduplicate and lowercase
        unique_words = list(set(w.lower() for w in words if len(w) > 2))

        groups = []
        used = set()

        for i, word1 in enumerate(unique_words):
            if word1 in used:
                continue

            group_words = {word1}
            group_sim = 0.0
            sim_count = 0

            for j, word2 in enumerate(unique_words):
                if i >= j or word2 in used:
                    continue

                sim = self.similarity(word1, word2)
                if sim >= self._similarity_threshold:
                    group_words.add(word2)
                    group_sim += sim
                    sim_count += 1

            if len(group_words) >= 2:
                avg_sim = group_sim / sim_count if sim_count > 0 else 0.0

                # Get occurrence counts
                occurrences = {}
                if word_counts:
                    for w in group_words:
                        occurrences[w] = word_counts.get(w, 0)

                groups.append(SynonymGroup(
                    words=group_words,
                    similarity_score=avg_sim,
                    occurrences=occurrences
                ))
                used.update(group_words)

        return groups

    def get_hypernyms(self, word: str) -> Set[str]:
        """
        Get hypernyms (broader terms) for a word.

        Args:
            word: Word to find hypernyms for

        Returns:
            Set of hypernym strings
        """
        if not self.is_available:
            return set()

        hypernyms = set()
        try:
            for syn in self._wn.synsets(word)[:3]:
                for hyper in syn.hypernyms():
                    for lemma in hyper.lemmas():
                        hypernyms.add(lemma.name().replace('_', ' ').lower())
        except Exception:
            pass

        return hypernyms

    def get_hyponyms(self, word: str) -> Set[str]:
        """
        Get hyponyms (narrower terms) for a word.

        Args:
            word: Word to find hyponyms for

        Returns:
            Set of hyponym strings
        """
        if not self.is_available:
            return set()

        hyponyms = set()
        try:
            for syn in self._wn.synsets(word)[:3]:
                for hypo in syn.hyponyms():
                    for lemma in hypo.lemmas():
                        hyponyms.add(lemma.name().replace('_', ' ').lower())
        except Exception:
            pass

        return hyponyms
