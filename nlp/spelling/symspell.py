"""
SymSpell Spell Checker for AEGIS
===========================================
Ultra-fast spell checking with 500K+ word dictionary.

Features:
- Edit distance algorithm for phonetic errors
- Word frequency ranking for suggestions
- Compound word segmentation
- Custom dictionary support

Requires: pip install symspellpy
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path

from ..base import NLPIntegrationBase


@dataclass
class SpellingSuggestion:
    """A spelling suggestion with metadata."""
    suggestion: str
    distance: int
    frequency: int


@dataclass
class Misspelling:
    """A detected misspelling with suggestions."""
    word: str
    suggestions: List[SpellingSuggestion]
    best_suggestion: str


class SymSpellChecker(NLPIntegrationBase):
    """
    SymSpell-based spell checker for AEGIS.

    1 million times faster than traditional algorithms.
    """

    INTEGRATION_NAME = "SymSpell"
    INTEGRATION_VERSION = "1.0.0"

    # Default dictionary filenames (bundled with symspellpy)
    FREQUENCY_DICT = "frequency_dictionary_en_82_765.txt"
    BIGRAM_DICT = "frequency_bigramdictionary_en_243_342.txt"

    def __init__(
        self,
        max_edit_distance: int = 2,
        prefix_length: int = 7,
        custom_dictionary: Optional[Path] = None
    ):
        """
        Initialize SymSpell checker.

        Args:
            max_edit_distance: Maximum edit distance for corrections (1-3)
            prefix_length: Length of prefix to use for lookup
            custom_dictionary: Path to custom words file
        """
        super().__init__()
        self.max_edit_distance = max_edit_distance
        self.prefix_length = prefix_length
        self.custom_dictionary = custom_dictionary

        self._sym_spell = None
        self._custom_words: Set[str] = set()
        self._load_dictionaries()

    def _load_dictionaries(self):
        """Load frequency dictionaries."""
        try:
            from symspellpy import SymSpell, Verbosity
            self._Verbosity = Verbosity

            self._sym_spell = SymSpell(
                max_dictionary_edit_distance=self.max_edit_distance,
                prefix_length=self.prefix_length
            )

            # Load main dictionary
            import pkg_resources
            dict_path = pkg_resources.resource_filename(
                "symspellpy", self.FREQUENCY_DICT
            )
            self._sym_spell.load_dictionary(
                dict_path,
                term_index=0,
                count_index=1
            )

            # Load bigram dictionary for compound word handling
            bigram_path = pkg_resources.resource_filename(
                "symspellpy", self.BIGRAM_DICT
            )
            self._sym_spell.load_bigram_dictionary(
                bigram_path,
                term_index=0,
                count_index=2
            )

            # Load custom dictionary if provided
            if self.custom_dictionary and Path(self.custom_dictionary).exists():
                self._load_custom_dictionary()

            self._available = True

        except ImportError as e:
            self._error = f"symspellpy not installed: {e}"
            self._available = False

        except Exception as e:
            self._error = f"Failed to load dictionaries: {e}"
            self._available = False

    def _load_custom_dictionary(self):
        """Load custom technical terms dictionary."""
        try:
            with open(self.custom_dictionary, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith('#'):
                        self._custom_words.add(word)
                        # Add to SymSpell with high frequency
                        self._sym_spell.create_dictionary_entry(word, 1000000)
        except Exception:
            pass  # Custom dictionary is optional

    def add_word(self, word: str, frequency: int = 1000000):
        """
        Add a word to the dictionary.

        Args:
            word: Word to add
            frequency: Word frequency (higher = more likely suggestion)
        """
        if self._sym_spell:
            self._custom_words.add(word.lower())
            self._sym_spell.create_dictionary_entry(word.lower(), frequency)

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the SymSpell integration."""
        status = {
            'available': self.is_available,
            'error': self._error,
            'max_edit_distance': self.max_edit_distance,
            'custom_words_count': len(self._custom_words),
        }

        if self.is_available and self._sym_spell:
            status['dictionary_size'] = len(self._sym_spell.words)

        return status

    def check_word(self, word: str) -> List[SpellingSuggestion]:
        """
        Check a single word for spelling errors.

        Args:
            word: Word to check

        Returns:
            List of suggestions (empty if word is correct)
        """
        if not self.is_available or not word:
            return []

        # Skip very short words and numbers
        if len(word) < 2 or word.isdigit():
            return []

        # Skip if in custom dictionary
        if word.lower() in self._custom_words:
            return []

        suggestions = self._sym_spell.lookup(
            word.lower(),
            self._Verbosity.CLOSEST,
            max_edit_distance=self.max_edit_distance,
            include_unknown=True
        )

        results = []
        for suggestion in suggestions:
            # If the top suggestion matches the word, it's correct
            if suggestion.term == word.lower() and suggestion.distance == 0:
                return []

            results.append(SpellingSuggestion(
                suggestion=suggestion.term,
                distance=suggestion.distance,
                frequency=suggestion.count
            ))

        return results[:5]  # Top 5 suggestions

    def check_text(self, text: str) -> List[Misspelling]:
        """
        Check text for spelling errors.

        Args:
            text: Text to check

        Returns:
            List of Misspelling objects
        """
        if not self.is_available:
            return []

        import re
        words = re.findall(r'\b[a-zA-Z]+\b', text)

        misspellings = []
        seen: Set[str] = set()

        for word in words:
            # Skip already checked words
            if word.lower() in seen:
                continue

            # Skip very short words
            if len(word) < 2:
                continue

            suggestions = self.check_word(word)

            # If we have suggestions and the best one isn't the word itself
            if suggestions and suggestions[0].distance > 0:
                misspellings.append(Misspelling(
                    word=word,
                    suggestions=suggestions,
                    best_suggestion=suggestions[0].suggestion
                ))
                seen.add(word.lower())

        return misspellings

    def segment_compound(self, text: str) -> str:
        """
        Segment text that may have missing spaces.

        Args:
            text: Text like "thequickbrown"

        Returns:
            Segmented text like "the quick brown"
        """
        if not self.is_available:
            return text

        try:
            result = self._sym_spell.word_segmentation(text.lower())
            return result.corrected_string
        except Exception:
            return text

    def is_word_known(self, word: str) -> bool:
        """
        Check if a word is in the dictionary.

        Args:
            word: Word to check

        Returns:
            True if word is known
        """
        if not self.is_available:
            return True  # Assume correct if unavailable

        if word.lower() in self._custom_words:
            return True

        suggestions = self.check_word(word)
        if not suggestions:
            return True

        return suggestions[0].distance == 0
