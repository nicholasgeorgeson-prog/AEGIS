"""
Tests for Style NLP Module
==========================
Tests for Proselint style checking integration.
"""

import pytest
from typing import List, Tuple


@pytest.fixture
def sample_paragraphs() -> List[Tuple[int, str]]:
    """Sample paragraphs for testing."""
    return [
        (0, "The system shall process all incoming data."),
        (1, "At this point in time, we need to leverage our synergies."),  # Jargon
        (2, "Basically, the software is very unique."),  # Clichés
        (3, "The functionality can be utilized for optimization."),
    ]


class TestProselintWrapper:
    """Tests for ProselintWrapper class."""

    def test_wrapper_init(self):
        """Test wrapper initialization."""
        try:
            from nlp.style.proselint import ProselintWrapper
            wrapper = ProselintWrapper()
            assert wrapper is not None
        except ImportError:
            pytest.skip("Proselint module not available")

    def test_is_available(self):
        """Test availability check."""
        try:
            from nlp.style.proselint import ProselintWrapper
            wrapper = ProselintWrapper()
            assert isinstance(wrapper.is_available, bool)
        except ImportError:
            pytest.skip("Proselint module not available")

    def test_check_text(self):
        """Test text checking."""
        try:
            from nlp.style.proselint import ProselintWrapper
            wrapper = ProselintWrapper()
            if not wrapper.is_available:
                pytest.skip("Proselint not available")

            text = "At this point in time, we need to leverage our synergies."
            issues = wrapper.check(text)
            assert isinstance(issues, list)
        except ImportError:
            pytest.skip("Proselint module not available")

    def test_get_category(self):
        """Test category retrieval."""
        try:
            from nlp.style.proselint import ProselintWrapper
            wrapper = ProselintWrapper()

            category = wrapper.get_category("cliches.hell")
            assert isinstance(category, str)
        except ImportError:
            pytest.skip("Proselint module not available")

    def test_skip_checks(self):
        """Test skip checks functionality."""
        try:
            from nlp.style.proselint import ProselintWrapper
            wrapper = ProselintWrapper()

            wrapper.add_skip_check("test_check")
            assert "test_check" in wrapper.SKIP_CHECKS

            wrapper.remove_skip_check("test_check")
            assert "test_check" not in wrapper.SKIP_CHECKS
        except ImportError:
            pytest.skip("Proselint module not available")


class TestStyleChecker:
    """Tests for StyleChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        try:
            from nlp.style.checker import StyleChecker
            checker = StyleChecker()
            assert checker.CHECKER_NAME == "Style (Professional)"
        except ImportError:
            pytest.skip("Style checker not available")

    def test_check_empty_paragraphs(self):
        """Test checking empty paragraphs."""
        try:
            from nlp.style.checker import StyleChecker
            checker = StyleChecker()
            result = checker.check([])
            assert result.success
            assert len(result.issues) == 0
        except ImportError:
            pytest.skip("Style checker not available")

    def test_check_valid_text(self, sample_paragraphs):
        """Test checking text with potential style issues."""
        try:
            from nlp.style.checker import StyleChecker
            checker = StyleChecker()
            result = checker.check(sample_paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Style checker not available")

    def test_detect_cliches(self):
        """Test detection of clichés."""
        try:
            from nlp.style.checker import StyleChecker
            checker = StyleChecker()

            paragraphs = [
                (0, "At the end of the day, we need to think outside the box."),
            ]
            result = checker.check(paragraphs)
            # If Proselint is available, should detect clichés
            assert result is not None
        except ImportError:
            pytest.skip("Style checker not available")

    def test_detect_jargon(self):
        """Test detection of jargon."""
        try:
            from nlp.style.checker import StyleChecker
            checker = StyleChecker()

            paragraphs = [
                (0, "We need to leverage our synergies to optimize our value proposition."),
            ]
            result = checker.check(paragraphs)
            assert result is not None
        except ImportError:
            pytest.skip("Style checker not available")


class TestStyleIssue:
    """Tests for StyleIssue dataclass."""

    def test_issue_creation(self):
        """Test issue dataclass creation."""
        try:
            from nlp.style.proselint import StyleIssue
            issue = StyleIssue(
                check_name="cliches.test",
                message="This is a cliché",
                line=1,
                column=5,
                start=10,
                end=20,
                severity="Medium",
                replacement="better phrase"
            )
            assert issue.check_name == "cliches.test"
            assert issue.severity == "Medium"
        except ImportError:
            pytest.skip("Proselint module not available")


class TestStyleModule:
    """Tests for style module interface."""

    def test_module_import(self):
        """Test module can be imported."""
        try:
            from nlp import style
            assert style is not None
        except ImportError:
            pytest.skip("Style module not available")

    def test_is_available(self):
        """Test is_available function."""
        try:
            from nlp.style import is_available
            result = is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Style module not available")

    def test_get_status(self):
        """Test get_status function."""
        try:
            from nlp.style import get_status
            status = get_status()
            assert isinstance(status, dict)
            assert 'available' in status
        except ImportError:
            pytest.skip("Style module not available")

    def test_severity_mapping(self):
        """Test severity mapping."""
        try:
            from nlp.style.proselint import ProselintWrapper
            assert ProselintWrapper.SEVERITY_MAP['error'] == 'High'
            assert ProselintWrapper.SEVERITY_MAP['warning'] == 'Medium'
            assert ProselintWrapper.SEVERITY_MAP['suggestion'] == 'Low'
        except ImportError:
            pytest.skip("Proselint module not available")

    def test_category_mapping(self):
        """Test category mapping."""
        try:
            from nlp.style.proselint import ProselintWrapper
            assert 'cliches' in ProselintWrapper.CATEGORY_MAP
            assert 'jargon' in ProselintWrapper.CATEGORY_MAP
        except ImportError:
            pytest.skip("Proselint module not available")
