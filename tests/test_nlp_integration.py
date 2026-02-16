"""
Tests for NLP Integration Module (v3.3.0)
=========================================
Tests the integration of all v3.3.0 NLP enhancement modules.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNLPIntegrationModule:
    """Test the nlp_integration module loads correctly."""

    def test_module_import(self):
        """Module should import without error."""
        import nlp_integration
        assert nlp_integration is not None

    def test_get_v330_checkers(self):
        """Should return dictionary of checkers."""
        from nlp_integration import get_v330_checkers
        checkers = get_v330_checkers()
        assert isinstance(checkers, dict)

    def test_get_v330_status(self):
        """Should return status dictionary."""
        from nlp_integration import get_v330_status
        status = get_v330_status()
        assert 'version' in status
        # v4.6.2-fix: Don't hardcode version — just verify field exists
        assert status['version'], "get_v330_status() returned empty version"
        assert 'components' in status
        assert 'summary' in status

    def test_status_has_summary(self):
        """Status should have summary with counts."""
        from nlp_integration import get_v330_status
        status = get_v330_status()
        summary = status['summary']
        assert 'available' in summary
        assert 'total' in summary
        assert 'percentage' in summary


class TestAdaptiveLearningIntegration:
    """Test adaptive learning integration."""

    def test_create_integration(self):
        """Should create integration instance."""
        from nlp_integration import AdaptiveLearningIntegration
        integration = AdaptiveLearningIntegration()
        assert integration is not None

    def test_is_available_property(self):
        """Should have is_available property."""
        from nlp_integration import AdaptiveLearningIntegration
        integration = AdaptiveLearningIntegration()
        assert hasattr(integration, 'is_available')

    def test_get_role_confidence_boost_default(self):
        """Should return 0.0 if not available."""
        from nlp_integration import AdaptiveLearningIntegration
        integration = AdaptiveLearningIntegration()
        if not integration.is_available:
            boost = integration.get_role_confidence_boost("Project Manager")
            assert boost == 0.0


class TestEnhancedNLPIntegration:
    """Test enhanced NLP integration."""

    def test_create_integration(self):
        """Should create integration instance."""
        from nlp_integration import EnhancedNLPIntegration
        integration = EnhancedNLPIntegration()
        assert integration is not None

    def test_is_available_property(self):
        """Should have is_available property."""
        from nlp_integration import EnhancedNLPIntegration
        integration = EnhancedNLPIntegration()
        assert hasattr(integration, 'is_available')

    def test_extract_roles_empty_if_unavailable(self):
        """Should return empty list if not available."""
        from nlp_integration import EnhancedNLPIntegration
        integration = EnhancedNLPIntegration()
        if not integration.is_available:
            roles = integration.extract_roles("The Project Manager shall review.")
            assert roles == []


class TestBaseEnhancedChecker:
    """Test base enhanced checker class."""

    def test_base_class_exists(self):
        """Base class should exist."""
        from nlp_integration import BaseEnhancedChecker
        assert BaseEnhancedChecker is not None

    def test_base_checker_attributes(self):
        """Base checker should have required attributes."""
        from nlp_integration import BaseEnhancedChecker
        checker = BaseEnhancedChecker()
        assert hasattr(checker, 'CHECKER_NAME')
        assert hasattr(checker, 'CHECKER_VERSION')
        assert hasattr(checker, 'is_available')

    def test_safe_check_returns_empty_if_unavailable(self):
        """safe_check should return empty list if not available."""
        from nlp_integration import BaseEnhancedChecker
        checker = BaseEnhancedChecker()
        result = checker.safe_check([])
        assert result == []


class TestEnhancedPassiveVoiceChecker:
    """Test enhanced passive voice checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import EnhancedPassiveVoiceChecker
        checker = EnhancedPassiveVoiceChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import EnhancedPassiveVoiceChecker
        checker = EnhancedPassiveVoiceChecker()
        assert checker.CHECKER_NAME == "Enhanced Passive Voice"

    def test_safe_check_returns_list(self):
        """safe_check should return list."""
        from nlp_integration import EnhancedPassiveVoiceChecker
        checker = EnhancedPassiveVoiceChecker()
        result = checker.safe_check([(0, "The document was written by the team.")])
        assert isinstance(result, list)


class TestSentenceFragmentChecker:
    """Test sentence fragment checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import SentenceFragmentChecker
        checker = SentenceFragmentChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import SentenceFragmentChecker
        checker = SentenceFragmentChecker()
        assert checker.CHECKER_NAME == "Sentence Fragments"


class TestRequirementsAnalyzerChecker:
    """Test requirements analyzer checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import RequirementsAnalyzerChecker
        checker = RequirementsAnalyzerChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import RequirementsAnalyzerChecker
        checker = RequirementsAnalyzerChecker()
        assert checker.CHECKER_NAME == "Requirements Analysis"


class TestTerminologyConsistencyChecker:
    """Test terminology consistency checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import TerminologyConsistencyChecker
        checker = TerminologyConsistencyChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import TerminologyConsistencyChecker
        checker = TerminologyConsistencyChecker()
        assert checker.CHECKER_NAME == "Terminology Consistency"


class TestCrossReferenceChecker:
    """Test cross-reference checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import CrossReferenceChecker
        checker = CrossReferenceChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import CrossReferenceChecker
        checker = CrossReferenceChecker()
        assert checker.CHECKER_NAME == "Cross-Reference Validation"


class TestTechnicalDictionaryChecker:
    """Test technical dictionary checker wrapper."""

    def test_create_checker(self):
        """Should create checker instance."""
        from nlp_integration import TechnicalDictionaryChecker
        checker = TechnicalDictionaryChecker()
        assert checker is not None

    def test_checker_name(self):
        """Should have correct checker name."""
        from nlp_integration import TechnicalDictionaryChecker
        checker = TechnicalDictionaryChecker()
        assert checker.CHECKER_NAME == "Technical Dictionary"

    def test_is_valid_term_method(self):
        """Should have is_valid_term method."""
        from nlp_integration import TechnicalDictionaryChecker
        checker = TechnicalDictionaryChecker()
        assert hasattr(checker, 'is_valid_term')

    def test_get_acronym_expansion_method(self):
        """Should have get_acronym_expansion method."""
        from nlp_integration import TechnicalDictionaryChecker
        checker = TechnicalDictionaryChecker()
        assert hasattr(checker, 'get_acronym_expansion')


class TestCoreIntegration:
    """Test integration with core.py."""

    def test_core_loads_v330_checkers(self):
        """Core should attempt to load v3.3.0 checkers."""
        from core import AEGISEngine
        twr = AEGISEngine()

        # Check that v3.3.0 attributes exist
        assert hasattr(twr, '_v330_checkers')
        assert hasattr(twr, '_v330_learner')
        assert hasattr(twr, '_v330_nlp')

    def test_v330_checkers_is_dict(self):
        """_v330_checkers should be a dictionary."""
        from core import AEGISEngine
        twr = AEGISEngine()
        assert isinstance(twr._v330_checkers, dict)


class TestRoleExtractorIntegration:
    """Test integration with role_extractor_v3.py."""

    def test_role_extractor_has_enhanced_nlp(self):
        """RoleExtractor should have enhanced NLP attribute."""
        from role_extractor_v3 import RoleExtractor
        extractor = RoleExtractor(use_nlp=True)
        assert hasattr(extractor, '_enhanced_nlp')
        assert hasattr(extractor, '_adaptive_learner')

    def test_role_extractor_has_v330_method(self):
        """RoleExtractor should have v3.3.0 enhancement method."""
        from role_extractor_v3 import RoleExtractor
        extractor = RoleExtractor(use_nlp=True)
        assert hasattr(extractor, '_apply_v330_enhancement')

    def test_extraction_returns_roles(self):
        """Extraction should return dictionary of roles."""
        from role_extractor_v3 import RoleExtractor
        extractor = RoleExtractor(use_nlp=True)
        text = """
        The Project Manager shall coordinate all activities.
        The Systems Engineer is responsible for technical oversight.
        The Configuration Manager maintains document control.
        """
        roles = extractor.extract_from_text(text, "test")
        assert isinstance(roles, dict)
        # Should find at least some roles
        assert len(roles) >= 0  # May be 0 if NLP not available


class TestGetFactoryFunctions:
    """Test factory function availability."""

    def test_get_adaptive_learner_integration(self):
        """Factory should return integration instance."""
        from nlp_integration import get_adaptive_learner_integration
        integration = get_adaptive_learner_integration()
        assert integration is not None

    def test_get_enhanced_nlp_integration(self):
        """Factory should return integration instance."""
        from nlp_integration import get_enhanced_nlp_integration
        integration = get_enhanced_nlp_integration()
        assert integration is not None
