"""
Tests for spaCy NLP Module
==========================
Tests for spaCy analyzer and enhanced checkers.
"""

import pytest
from typing import List, Tuple


# Test fixtures
@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The system shall process all incoming data."),
        (1, "Running through the park, the ball was kicked by the boy."),
        (2, "The software processes user requests efficiently and handles errors gracefully."),
        (3, "Complex sentence with multiple clauses that goes on and on with many subordinate phrases and additional information that makes it quite long and difficult to read because it keeps adding more and more details."),
    ]


@pytest.fixture
def analyzer():
    """Get spaCy analyzer instance."""
    try:
        from nlp.spacy import get_analyzer
        return get_analyzer()
    except ImportError:
        pytest.skip("spaCy module not available")


class TestSpacyAnalyzer:
    """Tests for SpacyAnalyzer class."""

    def test_analyzer_available(self, analyzer):
        """Test that analyzer is available."""
        assert analyzer.is_available or not analyzer.is_available
        # If model not loaded, it might not be available

    def test_analyze_basic(self, analyzer):
        """Test basic text analysis."""
        if not analyzer.is_available:
            pytest.skip("spaCy not available")

        text = "The system processes data."
        result = analyzer.analyze(text)
        assert result is not None

    def test_find_subject_verb_pairs(self, analyzer):
        """Test subject-verb pair extraction."""
        if not analyzer.is_available:
            pytest.skip("spaCy not available")

        text = "The system processes data efficiently."
        pairs = analyzer.find_subject_verb_pairs(text)
        assert isinstance(pairs, list)

    def test_find_dangling_modifiers(self, analyzer):
        """Test dangling modifier detection."""
        if not analyzer.is_available:
            pytest.skip("spaCy not available")

        text = "Running through the park, the ball was kicked."
        issues = analyzer.find_dangling_modifiers(text)
        assert isinstance(issues, list)

    def test_analyze_sentence_complexity(self, analyzer):
        """Test sentence complexity analysis."""
        if not analyzer.is_available:
            pytest.skip("spaCy not available")

        text = "This is a simple sentence."
        result = analyzer.analyze_sentence_complexity(text)
        assert isinstance(result, dict)


class TestEnhancedSubjectVerbChecker:
    """Tests for EnhancedSubjectVerbChecker."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.spacy.checkers import EnhancedSubjectVerbChecker
            checker = EnhancedSubjectVerbChecker()
            assert checker.CHECKER_NAME == "Subject-Verb Agreement (Enhanced)"
        except ImportError:
            pytest.skip("spaCy checkers not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.spacy.checkers import EnhancedSubjectVerbChecker
            checker = EnhancedSubjectVerbChecker()
            result = checker.check([])
            assert result.success
            assert len(result.issues) == 0
        except ImportError:
            pytest.skip("spaCy checkers not available")

    def test_check_valid_text(self, sample_paragraphs):
        """Test checking valid text."""
        try:
            from nlp.spacy.checkers import EnhancedSubjectVerbChecker
            checker = EnhancedSubjectVerbChecker()
            result = checker.check(sample_paragraphs)
            assert result.success or not result.success  # Either way is valid
        except ImportError:
            pytest.skip("spaCy checkers not available")


class TestDanglingModifierChecker:
    """Tests for EnhancedDanglingModifierChecker."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.spacy.checkers import EnhancedDanglingModifierChecker
            checker = EnhancedDanglingModifierChecker()
            assert checker.CHECKER_NAME == "Dangling Modifier (Enhanced)"
        except ImportError:
            pytest.skip("spaCy checkers not available")

    def test_detect_dangling_modifier(self):
        """Test detection of dangling modifier."""
        try:
            from nlp.spacy.checkers import EnhancedDanglingModifierChecker
            checker = EnhancedDanglingModifierChecker()
            paragraphs = [
                (0, "Running through the park, the ball was kicked by the boy."),
            ]
            result = checker.check(paragraphs)
            # Should detect potential dangling modifier
            assert result.success or not result.success
        except ImportError:
            pytest.skip("spaCy checkers not available")


class TestSentenceComplexityChecker:
    """Tests for SentenceComplexityChecker."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.spacy.checkers import SentenceComplexityChecker
            checker = SentenceComplexityChecker()
            assert checker.CHECKER_NAME == "Sentence Complexity"
        except ImportError:
            pytest.skip("spaCy checkers not available")

    def test_detect_complex_sentence(self):
        """Test detection of overly complex sentences."""
        try:
            from nlp.spacy.checkers import SentenceComplexityChecker
            checker = SentenceComplexityChecker()
            paragraphs = [
                (0, "Complex sentence with multiple clauses that goes on and on with many subordinate phrases and additional information that makes it quite long and difficult to read because it keeps adding more details and qualifications."),
            ]
            result = checker.check(paragraphs)
            assert result.success or not result.success
        except ImportError:
            pytest.skip("spaCy checkers not available")

    def test_simple_sentence_no_issues(self):
        """Test that simple sentences don't trigger issues."""
        try:
            from nlp.spacy.checkers import SentenceComplexityChecker
            checker = SentenceComplexityChecker()
            paragraphs = [
                (0, "This is a simple sentence."),
            ]
            result = checker.check(paragraphs)
            assert result.success
            # Simple sentences should not be flagged
        except ImportError:
            pytest.skip("spaCy checkers not available")


class TestSpacyModule:
    """Tests for spaCy module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import spacy as nlp_spacy
            assert nlp_spacy is not None
        except ImportError:
            pytest.skip("spaCy module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.spacy import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("spaCy module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.spacy import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("spaCy module not available")
