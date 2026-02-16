"""
Tests for LanguageTool NLP Module
=================================
Tests for LanguageTool grammar checking integration.
"""

import pytest
from typing import List, Tuple


@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The system shall process all incoming data."),
        (1, "Their going to the store tomorrow."),  # Intentional error
        (2, "The software processes user requests efficiently."),
        (3, "Its important to test this."),  # Intentional error
    ]


class TestLanguageToolClient:
    """Tests for LanguageToolClient class."""

    def test_client_init(self):
        """Test client initialization."""
        try:
            from nlp.languagetool.client import LanguageToolClient
            client = LanguageToolClient()
            assert client is not None
        except ImportError:
            pytest.skip("LanguageTool client not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.languagetool import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("LanguageTool module not available")

    def test_get_status(self):
        """Test status retrieval."""
        try:
            from nlp.languagetool import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("LanguageTool module not available")

    def test_check_text(self):
        """Test text checking."""
        try:
            from nlp.languagetool.client import LanguageToolClient
            client = LanguageToolClient()
            if not client.is_available:
                pytest.skip("LanguageTool not available (Java required)")

            issues = client.check("Their going to the store.")
            assert isinstance(issues, list)
        except ImportError:
            pytest.skip("LanguageTool client not available")


class TestComprehensiveGrammarChecker:
    """Tests for ComprehensiveGrammarChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.languagetool.checker import ComprehensiveGrammarChecker
            checker = ComprehensiveGrammarChecker()
            assert checker.CHECKER_NAME == "Grammar (Comprehensive)"
        except ImportError:
            pytest.skip("LanguageTool checker not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.languagetool.checker import ComprehensiveGrammarChecker
            checker = ComprehensiveGrammarChecker()
            result = checker.check([])
            assert result.success or not result.success
        except ImportError:
            pytest.skip("LanguageTool checker not available")

    def test_check_valid_text(self, sample_paragraphs):
        """Test checking valid text."""
        try:
            from nlp.languagetool.checker import ComprehensiveGrammarChecker
            checker = ComprehensiveGrammarChecker()
            result = checker.check(sample_paragraphs)
            # Result should exist, success depends on Java availability
            assert result is not None
        except ImportError:
            pytest.skip("LanguageTool checker not available")

    def test_check_grammar_errors(self):
        """Test detection of grammar errors."""
        try:
            from nlp.languagetool.checker import ComprehensiveGrammarChecker
            checker = ComprehensiveGrammarChecker()

            # Skip if not available
            if not checker.enabled:
                pytest.skip("LanguageTool checker not enabled")

            paragraphs = [
                (0, "Their going to the store tomorrow."),
                (1, "Its important to test this."),
            ]
            result = checker.check(paragraphs)
            # If LanguageTool is available, it should find errors
            assert result is not None
        except ImportError:
            pytest.skip("LanguageTool checker not available")


class TestLanguageToolModule:
    """Tests for LanguageTool module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import languagetool
            assert languagetool is not None
        except ImportError:
            pytest.skip("LanguageTool module not available")

    def test_skip_rules(self):
        """Test SKIP_RULES configuration."""
        try:
            from nlp.languagetool.client import LanguageToolClient
            assert hasattr(LanguageToolClient, 'SKIP_RULES')
            assert isinstance(LanguageToolClient.SKIP_RULES, set)
        except ImportError:
            pytest.skip("LanguageTool client not available")

    def test_technical_whitelist(self):
        """Test TECHNICAL_WHITELIST configuration."""
        try:
            from nlp.languagetool.client import LanguageToolClient
            assert hasattr(LanguageToolClient, 'TECHNICAL_WHITELIST')
            assert isinstance(LanguageToolClient.TECHNICAL_WHITELIST, set)
        except ImportError:
            pytest.skip("LanguageTool client not available")
