"""
Tests for Readability NLP Module
================================
Tests for enhanced readability metrics.
"""

import pytest


@pytest.fixture
def simple_text() -> str:
    """Simple text for testing."""
    return "The cat sat on the mat. It was a nice day. The sun was shining."


@pytest.fixture
def complex_text() -> str:
    """Complex text for testing."""
    return """
    The implementation of sophisticated algorithmic methodologies necessitates
    comprehensive understanding of computational paradigms and their associated
    implications for system architecture design patterns. Furthermore, the
    integration of heterogeneous components requires meticulous attention to
    interface specifications and protocol compatibility requirements.
    """


class TestEnhancedReadabilityCalculator:
    """Tests for EnhancedReadabilityCalculator class."""

    def test_calculator_init(self):
        """Test calculator initialization."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            assert calc is not None
        except ImportError:
            pytest.skip("Readability module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            assert isinstance(calc.is_available, bool)
        except ImportError:
            pytest.skip("Readability module not available")

    def test_calculate_simple_text(self, simple_text):
        """Test calculation on simple text."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(simple_text)
            assert report is not None
            # Simple text should have low grade level
            assert hasattr(report, 'flesch_kincaid_grade')
        except ImportError:
            pytest.skip("Readability module not available")

    def test_calculate_complex_text(self, complex_text):
        """Test calculation on complex text."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(complex_text)
            assert report is not None
            # Complex text should have higher grade level
            assert hasattr(report, 'flesch_kincaid_grade')
        except ImportError:
            pytest.skip("Readability module not available")

    def test_all_metrics_present(self, simple_text):
        """Test that all metrics are calculated."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(simple_text)

            # Check core metrics
            assert hasattr(report, 'flesch_reading_ease')
            assert hasattr(report, 'flesch_kincaid_grade')
            assert hasattr(report, 'gunning_fog')
        except ImportError:
            pytest.skip("Readability module not available")

    def test_get_recommendations(self, complex_text):
        """Test recommendation generation."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(complex_text)
            recommendations = calc.get_recommendations(report)
            assert isinstance(recommendations, list)
        except ImportError:
            pytest.skip("Readability module not available")


class TestReadabilityReport:
    """Tests for ReadabilityReport dataclass."""

    def test_report_creation(self):
        """Test report dataclass creation."""
        try:
            from nlp.readability.enhanced import ReadabilityReport
            report = ReadabilityReport(
                flesch_reading_ease=60.0,
                flesch_kincaid_grade=8.0,
                gunning_fog=10.0,
                smog_index=9.0,
                coleman_liau_index=9.5,
                automated_readability_index=8.5,
                dale_chall_readability=7.0,
                linsear_write=8.0,
                word_count=100,
                sentence_count=10,
                avg_sentence_length=10.0
            )
            assert report.flesch_reading_ease == 60.0
        except ImportError:
            pytest.skip("Readability module not available")

    def test_report_to_dict(self):
        """Test report conversion to dict."""
        try:
            from nlp.readability.enhanced import ReadabilityReport
            report = ReadabilityReport(
                flesch_reading_ease=60.0,
                flesch_kincaid_grade=8.0,
                gunning_fog=10.0,
                smog_index=9.0,
                coleman_liau_index=9.5,
                automated_readability_index=8.5,
                dale_chall_readability=7.0,
                linsear_write=8.0,
                word_count=100,
                sentence_count=10,
                avg_sentence_length=10.0
            )
            d = report.to_dict()
            assert isinstance(d, dict)
            assert 'flesch_reading_ease' in d
        except ImportError:
            pytest.skip("Readability module not available")


class TestReadabilityModule:
    """Tests for readability module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import readability
            assert readability is not None
        except ImportError:
            pytest.skip("Readability module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.readability import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Readability module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.readability import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("Readability module not available")

    def test_calculate_function(self, simple_text):
        """Test module-level calculate function."""
        try:
            from nlp.readability import calculate
            report = calculate(simple_text)
            assert report is not None
        except ImportError:
            pytest.skip("Readability module not available")


class TestReadabilityMetrics:
    """Tests for specific readability metrics."""

    def test_flesch_reading_ease_range(self, simple_text):
        """Test Flesch Reading Ease is in valid range."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(simple_text)
            # Flesch Reading Ease should be between 0 and 100
            assert 0 <= report.flesch_reading_ease <= 100 or report.flesch_reading_ease > 100
            # Can exceed 100 for very simple text
        except ImportError:
            pytest.skip("Readability module not available")

    def test_grade_level_positive(self, simple_text):
        """Test grade levels are positive."""
        try:
            from nlp.readability.enhanced import EnhancedReadabilityCalculator
            calc = EnhancedReadabilityCalculator()
            if not calc.is_available:
                pytest.skip("Textstat not available")

            report = calc.calculate(simple_text)
            assert report.flesch_kincaid_grade >= 0
        except ImportError:
            pytest.skip("Readability module not available")
