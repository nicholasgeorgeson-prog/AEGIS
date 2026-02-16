"""
Tests for Semantics NLP Module
==============================
Tests for WordNet-based semantic analysis and terminology consistency.
"""

import pytest
from typing import List, Tuple


@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The application starts quickly. The program runs efficiently."),
        (1, "Users can configure the settings. Customers may adjust preferences."),
        (2, "Click the button to begin. Press the button to start."),
        (3, "The software processes data. The system handles information."),
    ]


class TestSemanticAnalyzer:
    """Tests for SemanticAnalyzer class."""

    def test_analyzer_init(self):
        """Test analyzer initialization."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            assert isinstance(analyzer.is_available, bool)
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_get_synonyms(self):
        """Test getting synonyms for a word."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            synonyms = analyzer.get_synonyms("car")
            assert isinstance(synonyms, (set, list))
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_similarity_identical_words(self):
        """Test similarity of identical words."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            sim = analyzer.similarity("car", "car")
            assert sim == 1.0
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_similarity_synonyms(self):
        """Test similarity of synonyms."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            sim = analyzer.similarity("car", "automobile")
            assert sim >= 0.8  # Should be high similarity
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_similarity_unrelated_words(self):
        """Test similarity of unrelated words."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            sim = analyzer.similarity("car", "banana")
            assert sim < 0.5  # Should be low similarity
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_are_synonyms(self):
        """Test synonym detection."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            assert analyzer.are_synonyms("big", "large")
            assert not analyzer.are_synonyms("big", "small")
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_find_synonym_groups(self):
        """Test finding synonym groups."""
        try:
            from nlp.semantics.wordnet import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            if not analyzer.is_available:
                pytest.skip("WordNet not available")

            words = ["car", "automobile", "vehicle", "banana", "fruit"]
            word_counts = {w: 1 for w in words}
            groups = analyzer.find_synonym_groups(words, word_counts)
            assert isinstance(groups, list)
        except ImportError:
            pytest.skip("Semantics module not available")


class TestTerminologyConsistencyChecker:
    """Tests for TerminologyConsistencyChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()
            assert checker.CHECKER_NAME == "Terminology Consistency"
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()
            result = checker.check([])
            assert result.success
            assert len(result.issues) == 0
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_check_consistent_terminology(self):
        """Test checking text with consistent terminology."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()

            paragraphs = [
                (0, "The system processes data. The system handles requests. The system returns results."),
            ]
            result = checker.check(paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_check_inconsistent_terminology(self, sample_paragraphs):
        """Test checking text with inconsistent terminology."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()
            result = checker.check(sample_paragraphs)
            # Should detect potential inconsistencies
            assert result is not None
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_get_synonym_report(self, sample_paragraphs):
        """Test getting synonym analysis report."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()

            report = checker.get_synonym_report(sample_paragraphs)
            assert isinstance(report, dict)
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_check_word_pair(self):
        """Test checking if two words are synonyms."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            checker = TerminologyConsistencyChecker()

            result = checker.check_word_pair("start", "begin")
            assert isinstance(result, dict)
            assert 'similarity' in result
        except ImportError:
            pytest.skip("Semantics checker not available")


class TestSynonymGroup:
    """Tests for SynonymGroup dataclass."""

    def test_group_creation(self):
        """Test synonym group creation."""
        try:
            from nlp.semantics.wordnet import SynonymGroup
            group = SynonymGroup(
                words=['car', 'automobile'],
                similarity_score=0.95,
                occurrences={'car': 5, 'automobile': 3}
            )
            assert len(group.words) == 2
            assert group.similarity_score == 0.95
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_group_to_dict(self):
        """Test synonym group conversion to dict."""
        try:
            from nlp.semantics.wordnet import SynonymGroup
            group = SynonymGroup(
                words=['car', 'automobile'],
                similarity_score=0.95,
                occurrences={'car': 5, 'automobile': 3}
            )
            d = group.to_dict()
            assert isinstance(d, dict)
            assert 'words' in d
        except ImportError:
            pytest.skip("Semantics module not available")


class TestSemanticsModule:
    """Tests for semantics module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import semantics
            assert semantics is not None
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.semantics import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.semantics import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_get_synonyms_function(self):
        """Test module-level get_synonyms function."""
        try:
            from nlp.semantics import get_synonyms
            synonyms = get_synonyms("car")
            assert isinstance(synonyms, (set, list))
        except ImportError:
            pytest.skip("Semantics module not available")

    def test_similarity_function(self):
        """Test module-level similarity function."""
        try:
            from nlp.semantics import similarity
            sim = similarity("car", "automobile")
            assert isinstance(sim, float)
            assert 0.0 <= sim <= 1.0
        except ImportError:
            pytest.skip("Semantics module not available")


class TestAllowVariation:
    """Tests for ALLOW_VARIATION word list."""

    def test_allow_variation_exists(self):
        """Test ALLOW_VARIATION set exists."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            assert hasattr(TerminologyConsistencyChecker, 'ALLOW_VARIATION')
            assert isinstance(TerminologyConsistencyChecker.ALLOW_VARIATION, set)
        except ImportError:
            pytest.skip("Semantics checker not available")

    def test_common_words_allowed(self):
        """Test common words are in ALLOW_VARIATION."""
        try:
            from nlp.semantics.checker import TerminologyConsistencyChecker
            allowed = TerminologyConsistencyChecker.ALLOW_VARIATION

            # Function words should be allowed to vary
            assert 'the' in allowed
            assert 'and' in allowed
            assert 'is' in allowed
        except ImportError:
            pytest.skip("Semantics checker not available")
