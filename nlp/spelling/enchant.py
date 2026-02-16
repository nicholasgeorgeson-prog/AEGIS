"""
Domain Dictionary Manager for AEGIS
==============================================
Provides domain-specific spelling support via PyEnchant.

Features:
- Aerospace/defense/software dictionaries
- Personal word list support
- Multiple dictionary stacking
- Hunspell compatibility

Requires: pip install pyenchant
Note: macOS may need: brew install enchant
"""

from typing import List, Dict, Set, Optional, Any
from pathlib import Path

from ..base import NLPIntegrationBase


class DomainDictionaryManager(NLPIntegrationBase):
    """
    Manages domain-specific dictionaries for spell checking.

    Supports aerospace, defense, and software terminology.
    """

    INTEGRATION_NAME = "PyEnchant"
    INTEGRATION_VERSION = "1.0.0"

    # Default dictionary directory (relative to project root)
    DEFAULT_DICT_DIR = Path(__file__).parent.parent.parent / "dictionaries"

    # Domain dictionary files
    DOMAIN_FILES = {
        'aerospace': 'aerospace.txt',
        'defense': 'defense.txt',
        'software': 'software.txt',
    }

    def __init__(
        self,
        language: str = 'en_US',
        domains: Optional[List[str]] = None,
        dict_dir: Optional[Path] = None,
        personal_dict: Optional[Path] = None
    ):
        """
        Initialize domain dictionary manager.

        Args:
            language: Base language (default: en_US)
            domains: List of domains to load ('aerospace', 'defense', 'software')
            dict_dir: Directory containing domain dictionaries
            personal_dict: Path to personal word list
        """
        super().__init__()
        self.language = language
        self.domains = domains or ['aerospace', 'defense', 'software']
        self.dict_dir = Path(dict_dir) if dict_dir else self.DEFAULT_DICT_DIR
        self.personal_dict = personal_dict

        self._enchant = None
        self._base_dict = None
        self._domain_words: Set[str] = set()
        self._personal_words: Set[str] = set()

        self._initialize()

    def _initialize(self):
        """Initialize PyEnchant and load dictionaries."""
        try:
            import enchant
            self._enchant = enchant

            # Create base dictionary
            self._base_dict = enchant.Dict(self.language)

            # Load domain dictionaries
            for domain in self.domains:
                self._load_domain_dictionary(domain)

            # Load personal dictionary
            if self.personal_dict and Path(self.personal_dict).exists():
                self._load_personal_dictionary()

            self._available = True

        except ImportError as e:
            self._error = f"pyenchant not installed: {e}"
            self._available = False

        except Exception as e:
            self._error = f"Failed to initialize: {e}"
            self._available = False

    def _load_domain_dictionary(self, domain: str):
        """Load a domain-specific dictionary file."""
        if domain not in self.DOMAIN_FILES:
            return

        dict_file = self.dict_dir / self.DOMAIN_FILES[domain]
        if not dict_file.exists():
            return

        try:
            with open(dict_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith('#'):
                        self._domain_words.add(word)
        except Exception:
            pass  # Domain dictionaries are optional

    def _load_personal_dictionary(self):
        """Load personal word list."""
        try:
            with open(self.personal_dict, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith('#'):
                        self._personal_words.add(word)
        except Exception:
            pass

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the PyEnchant integration."""
        status = {
            'available': self.is_available,
            'error': self._error,
            'language': self.language,
            'domains_loaded': self.domains if self.is_available else [],
            'domain_words_count': len(self._domain_words),
            'personal_words_count': len(self._personal_words),
        }

        if self.is_available and self._enchant:
            try:
                status['available_languages'] = self._enchant.list_languages()
            except Exception:
                status['available_languages'] = []

        return status

    def check(self, word: str) -> bool:
        """
        Check if a word is spelled correctly.

        Args:
            word: Word to check

        Returns:
            True if word is correct (in any dictionary)
        """
        word_lower = word.lower()

        # Check personal dictionary first
        if word_lower in self._personal_words:
            return True

        # Check domain dictionaries
        if word_lower in self._domain_words:
            return True

        # Check base dictionary
        if self.is_available and self._base_dict:
            try:
                return self._base_dict.check(word)
            except Exception:
                return True  # Assume correct on error

        return True  # Assume correct if unavailable

    def suggest(self, word: str) -> List[str]:
        """
        Get spelling suggestions for a word.

        Args:
            word: Misspelled word

        Returns:
            List of suggestions (up to 5)
        """
        if self.is_available and self._base_dict:
            try:
                return self._base_dict.suggest(word)[:5]
            except Exception:
                pass
        return []

    def add_word(self, word: str, domain: Optional[str] = None):
        """
        Add a word to a dictionary.

        Args:
            word: Word to add
            domain: Domain to add to (or personal if None)
        """
        word_lower = word.lower()

        if domain and domain in self.DOMAIN_FILES:
            self._domain_words.add(word_lower)
        else:
            self._personal_words.add(word_lower)

    def is_domain_term(self, word: str) -> bool:
        """
        Check if a word is a known domain term.

        Args:
            word: Word to check

        Returns:
            True if word is in domain dictionaries
        """
        return word.lower() in self._domain_words

    def is_personal_term(self, word: str) -> bool:
        """
        Check if a word is in personal dictionary.

        Args:
            word: Word to check

        Returns:
            True if word is in personal dictionary
        """
        return word.lower() in self._personal_words

    def get_domain_words(self, domain: Optional[str] = None) -> Set[str]:
        """
        Get all words from domain dictionaries.

        Args:
            domain: Specific domain (or all if None)

        Returns:
            Set of domain words
        """
        if domain is None:
            return self._domain_words.copy()

        # Reload specific domain
        words = set()
        if domain in self.DOMAIN_FILES:
            dict_file = self.dict_dir / self.DOMAIN_FILES[domain]
            if dict_file.exists():
                try:
                    with open(dict_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            word = line.strip().lower()
                            if word and not word.startswith('#'):
                                words.add(word)
                except Exception:
                    pass
        return words

    def check_text(self, text: str) -> List[dict]:
        """
        Check text for spelling errors.

        Args:
            text: Text to check

        Returns:
            List of dicts with word and suggestions
        """
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', text)

        errors = []
        seen: Set[str] = set()

        for word in words:
            if word.lower() in seen:
                continue

            if len(word) < 2:
                continue

            if not self.check(word):
                errors.append({
                    'word': word,
                    'suggestions': self.suggest(word),
                    'is_domain_term': False,
                    'is_personal_term': False,
                })
                seen.add(word.lower())

        return errors
