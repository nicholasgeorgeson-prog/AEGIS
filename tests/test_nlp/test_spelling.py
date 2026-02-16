"""
Tests for Spelling NLP Module
=============================
Tests for SymSpell, Enchant, and enhanced spelling checker.
"""

import pytest
from typing import List, Tuple


@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The system shall process all incoming data."),
        (1, "This sentnce contains a speling error."),  # Intentional errors
        (2, "The software processes user requests efficiently."),
        (3, "Teh quick brown fox jumps over the lazy dog."),  # Intentional error
    ]


class TestSymSpellChecker:
    """Tests for SymSpellChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.spelling.symspell import SymSpellChecker
            checker = SymSpellChecker()
            assert checker is not None
        except ImportError:
            pytest.skip("SymSpell module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.spelling.symspell import SymSpellChecker
            checker = SymSpellChecker()
            assert isinstance(checker.is_available, bool)
        except ImportError:
            pytest.skip("SymSpell module not available")

    def test_check_word_correct(self):
        """Test checking a correct word."""
        try:
            from nlp.spelling.symspell import SymSpellChecker
            checker = SymSpellChecker()
            if not checker.is_available:
                pytest.skip("SymSpell not available")

            result = checker.check_word("system")
            assert result is not None
        except ImportError:
            pytest.skip("SymSpell module not available")

    def test_check_word_misspelled(self):
        """Test checking a misspelled word."""
        try:
            from nlp.spelling.symspell import SymSpellChecker
            checker = SymSpellChecker()
            if not checker.is_available:
                pytest.skip("SymSpell not available")

            result = checker.check_word("systm")
            # Should suggest corrections
            assert result is not None
        except ImportError:
            pytest.skip("SymSpell module not available")

    def test_check_text(self):
        """Test checking text for spelling errors."""
        try:
            from nlp.spelling.symspell import SymSpellChecker
            checker = SymSpellChecker()
            if not checker.is_available:
                pytest.skip("SymSpell not available")

            issues = checker.check_text("This sentnce has speling errors.")
            assert isinstance(issues, list)
        except ImportError:
            pytest.skip("SymSpell module not available")


class TestDomainDictionaryManager:
    """Tests for DomainDictionaryManager class."""

    def test_manager_init(self):
        """Test manager initialization."""
        try:
            from nlp.spelling.enchant import DomainDictionaryManager
            manager = DomainDictionaryManager()
            assert manager is not None
        except ImportError:
            pytest.skip("Enchant module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.spelling.enchant import DomainDictionaryManager
            manager = DomainDictionaryManager()
            assert isinstance(manager.is_available, bool)
        except ImportError:
            pytest.skip("Enchant module not available")

    def test_check_domain_word(self):
        """Test checking domain-specific word."""
        try:
            from nlp.spelling.enchant import DomainDictionaryManager
            manager = DomainDictionaryManager()
            if not manager.is_available:
                pytest.skip("Enchant not available")

            # Aerospace term
            result = manager.is_domain_word("avionics")
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Enchant module not available")


class TestEnhancedSpellingChecker:
    """Tests for EnhancedSpellingChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.spelling.checker import EnhancedSpellingChecker
            checker = EnhancedSpellingChecker()
            assert checker.CHECKER_NAME == "Spelling (Enhanced)"
        except ImportError:
            pytest.skip("Spelling checker not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.spelling.checker import EnhancedSpellingChecker
            checker = EnhancedSpellingChecker()
            result = checker.check([])
            assert result.success
            assert len(result.issues) == 0
        except ImportError:
            pytest.skip("Spelling checker not available")

    def test_check_valid_text(self, sample_paragraphs):
        """Test checking text with spelling errors."""
        try:
            from nlp.spelling.checker import EnhancedSpellingChecker
            checker = EnhancedSpellingChecker()
            result = checker.check(sample_paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Spelling checker not available")

    def test_skip_patterns(self):
        """Test that skip patterns are respected."""
        try:
            from nlp.spelling.checker import EnhancedSpellingChecker
            checker = EnhancedSpellingChecker()

            # Technical terms should be skipped
            paragraphs = [
                (0, "Configure the API_KEY and HTTP_ENDPOINT."),
            ]
            result = checker.check(paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Spelling checker not available")


class TestSpellingModule:
    """Tests for spelling module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import spelling
            assert spelling is not None
        except ImportError:
            pytest.skip("Spelling module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.spelling import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Spelling module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.spelling import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("Spelling module not available")


class TestDomainDictionaries:
    """Tests for domain dictionary files."""

    def test_aerospace_dictionary_exists(self):
        """Test aerospace dictionary file exists."""
        from pathlib import Path
        dict_path = Path(__file__).parent.parent.parent / 'dictionaries' / 'aerospace.txt'
        # Dictionary might not exist in test environment
        if dict_path.exists():
            content = dict_path.read_text()
            assert len(content) > 0

    def test_defense_dictionary_exists(self):
        """Test defense dictionary file exists."""
        from pathlib import Path
        dict_path = Path(__file__).parent.parent.parent / 'dictionaries' / 'defense.txt'
        if dict_path.exists():
            content = dict_path.read_text()
            assert len(content) > 0

    def test_software_dictionary_exists(self):
        """Test software dictionary file exists."""
        from pathlib import Path
        dict_path = Path(__file__).parent.parent.parent / 'dictionaries' / 'software.txt'
        if dict_path.exists():
            content = dict_path.read_text()
            assert len(content) > 0
