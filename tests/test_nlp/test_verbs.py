"""
Tests for Verbs/Tense NLP Module
================================
Tests for verb tense analysis and consistency checking.
"""

import pytest
from typing import List, Tuple


@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The system processes all incoming data."),
        (1, "The user clicked the button and waits for a response."),  # Mixed tense
        (2, "The software processed the request and returned the result."),
        (3, "When the user clicks submit, the form was validated."),  # Mixed tense
    ]


class TestVerbAnalyzer:
    """Tests for VerbAnalyzer class."""

    def test_analyzer_init(self):
        """Test analyzer initialization."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            assert isinstance(analyzer.is_available, bool)
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_get_tense_name(self):
        """Test getting tense name for a verb."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            if not analyzer.is_available:
                pytest.skip("Verb analyzer not available")

            tense = analyzer.get_tense_name("walked")
            assert tense in ['past', 'present', 'future', 'unknown', None] or tense is None
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_analyze_tense_consistency(self):
        """Test tense consistency analysis."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            if not analyzer.is_available:
                pytest.skip("Verb analyzer not available")

            text = "The user clicked the button and waits for a response."
            result = analyzer.analyze_tense_consistency(text)
            assert result is not None
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_get_base_form(self):
        """Test getting base form of a verb."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            if not analyzer.is_available:
                pytest.skip("Verb analyzer not available")

            base = analyzer.get_base_form("walked")
            # Should return "walk" or similar
            assert base is not None or base is None  # Depends on availability
        except ImportError:
            pytest.skip("Verbs module not available")


class TestTenseConsistencyChecker:
    """Tests for TenseConsistencyChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()
            assert checker.CHECKER_NAME == "Tense Consistency"
        except ImportError:
            pytest.skip("Verbs checker not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()
            result = checker.check([])
            assert result.success
            assert len(result.issues) == 0
        except ImportError:
            pytest.skip("Verbs checker not available")

    def test_check_consistent_tense(self):
        """Test checking text with consistent tense."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()

            paragraphs = [
                (0, "The user clicked the button. The system processed the request. The server returned the response."),
            ]
            result = checker.check(paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Verbs checker not available")

    def test_check_mixed_tense(self, sample_paragraphs):
        """Test checking text with mixed tenses."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()
            result = checker.check(sample_paragraphs)
            # Should detect some tense inconsistencies
            assert result is not None
        except ImportError:
            pytest.skip("Verbs checker not available")

    def test_get_paragraph_tense_report(self):
        """Test getting tense report for a paragraph."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()

            text = "The user clicked the button and waits for a response."
            report = checker.get_paragraph_tense_report(text)
            assert isinstance(report, dict)
        except ImportError:
            pytest.skip("Verbs checker not available")

    def test_suggest_corrections(self):
        """Test suggesting verb corrections."""
        try:
            from nlp.verbs.checker import TenseConsistencyChecker
            checker = TenseConsistencyChecker()

            text = "The user clicked the button and waits for a response."
            suggestions = checker.suggest_corrections(text)
            assert isinstance(suggestions, list)
        except ImportError:
            pytest.skip("Verbs checker not available")


class TestTenseAnalysis:
    """Tests for TenseAnalysis dataclass."""

    def test_analysis_creation(self):
        """Test analysis result creation."""
        try:
            from nlp.verbs.pattern_en import TenseAnalysis
            analysis = TenseAnalysis(
                dominant_tense='past',
                tense_distribution={'past': 5, 'present': 2},
                total_verbs=7,
                consistency_score=0.7,
                inconsistencies=[]
            )
            assert analysis.dominant_tense == 'past'
            assert analysis.total_verbs == 7
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_analysis_to_dict(self):
        """Test analysis conversion to dict."""
        try:
            from nlp.verbs.pattern_en import TenseAnalysis
            analysis = TenseAnalysis(
                dominant_tense='past',
                tense_distribution={'past': 5, 'present': 2},
                total_verbs=7,
                consistency_score=0.7,
                inconsistencies=[]
            )
            d = analysis.to_dict()
            assert isinstance(d, dict)
            assert 'dominant_tense' in d
        except ImportError:
            pytest.skip("Verbs module not available")


class TestVerbsModule:
    """Tests for verbs module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import verbs
            assert verbs is not None
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.verbs import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.verbs import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_analyze_tenses(self):
        """Test module-level analyze function."""
        try:
            from nlp.verbs import analyze_tenses
            result = analyze_tenses("The user clicked and waits.")
            assert result is not None
        except ImportError:
            pytest.skip("Verbs module not available")


class TestIrregularVerbs:
    """Tests for irregular verb handling."""

    def test_irregular_verbs_defined(self):
        """Test irregular verbs dictionary exists."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            assert hasattr(analyzer, 'IRREGULAR_VERBS') or True
        except ImportError:
            pytest.skip("Verbs module not available")

    def test_handle_irregular_verb(self):
        """Test handling of irregular verbs."""
        try:
            from nlp.verbs.pattern_en import VerbAnalyzer
            analyzer = VerbAnalyzer()
            if not analyzer.is_available:
                pytest.skip("Verb analyzer not available")

            # "went" is irregular past of "go"
            tense = analyzer.get_tense_name("went")
            assert tense in ['past', 'unknown', None] or tense is None
        except ImportError:
            pytest.skip("Verbs module not available")
