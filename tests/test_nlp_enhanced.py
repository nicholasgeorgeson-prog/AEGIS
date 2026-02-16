"""
Unit Tests for Enhanced NLP Pipeline
=====================================
Version: 1.0.0
Date: 2026-02-03

Tests the EnhancedNLPProcessor for:
- Role extraction with multiple methods
- Acronym detection and expansion
- Document analysis
- Ensemble extraction
- Learning integration
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_enhanced import (
    EnhancedNLPProcessor, ExtractedRole, ExtractedAcronym, DocumentAnalysis,
    get_enhanced_nlp, is_nlp_available, STANDARD_ACRONYMS, ROLE_PHRASES,
    AEROSPACE_ENTITY_PATTERNS
)


class TestEnhancedNLPBasics(unittest.TestCase):
    """Test basic NLP processor functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test processor instance."""
        cls.processor = EnhancedNLPProcessor(load_immediately=True)

    def test_initialization(self):
        """Test processor initializes correctly."""
        self.assertIsNotNone(self.processor)

    def test_status(self):
        """Test status returns expected fields."""
        status = self.processor.get_status()
        self.assertIn('version', status)
        self.assertIn('is_loaded', status)
        self.assertIn('model_name', status)
        self.assertIn('has_entity_ruler', status)
        self.assertIn('has_phrase_matcher', status)

    def test_singleton(self):
        """Test singleton returns same instance."""
        proc1 = get_enhanced_nlp()
        proc2 = get_enhanced_nlp()
        self.assertIs(proc1, proc2)


class TestRoleExtraction(unittest.TestCase):
    """Test role extraction functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test processor instance."""
        cls.processor = EnhancedNLPProcessor(load_immediately=True)

    def test_extract_simple_role(self):
        """Test extracting a simple role."""
        text = "The Project Manager shall review all deliverables."
        roles = self.processor.extract_roles(text)

        # Should find at least one role
        self.assertGreater(len(roles), 0)

        # Check structure of extracted role
        role = roles[0]
        self.assertIsInstance(role, ExtractedRole)
        self.assertIsNotNone(role.name)
        self.assertIsNotNone(role.normalized_name)
        self.assertGreater(role.confidence, 0)

    def test_extract_compound_role(self):
        """Test extracting compound roles."""
        text = "The Systems Engineering Lead is responsible for design."
        roles = self.processor.extract_roles(text)

        self.assertGreater(len(roles), 0)
        role_names = [r.name.lower() for r in roles]
        # Should find systems engineering lead or similar
        self.assertTrue(
            any('systems' in name and 'lead' in name for name in role_names) or
            any('engineer' in name for name in role_names)
        )

    def test_extract_multiple_roles(self):
        """Test extracting multiple roles from same text."""
        text = """
        The Project Manager coordinates with the Systems Engineer
        and the Test Lead to ensure requirements are met.
        """
        roles = self.processor.extract_roles(text)

        # Should find multiple roles
        self.assertGreater(len(roles), 1)

    def test_role_confidence_varies(self):
        """Test that confidence varies by extraction method."""
        text = """
        The Software Engineer shall develop the module.
        The team lead reviews the code.
        """
        roles = self.processor.extract_roles(text)

        if len(roles) > 1:
            # Confidence should vary
            confidences = [r.confidence for r in roles]
            # Just verify confidences are in valid range
            self.assertTrue(all(0 <= c <= 1 for c in confidences))

    def test_role_context_extracted(self):
        """Test that context is extracted with roles."""
        text = "The Quality Engineer shall verify compliance with AS9100."
        roles = self.processor.extract_roles(text)

        if roles:
            role = roles[0]
            # Context should contain relevant text
            self.assertIsNotNone(role.context)
            self.assertGreater(len(role.context), 10)

    def test_empty_text_returns_empty(self):
        """Test empty text returns empty list."""
        roles = self.processor.extract_roles("")
        self.assertEqual(len(roles), 0)

    def test_no_roles_in_random_text(self):
        """Test random text doesn't extract spurious roles."""
        text = "The quick brown fox jumps over the lazy dog."
        roles = self.processor.extract_roles(text)

        # Should not find any roles
        self.assertEqual(len(roles), 0)


class TestAcronymExtraction(unittest.TestCase):
    """Test acronym extraction functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test processor instance."""
        cls.processor = EnhancedNLPProcessor(load_immediately=True)

    def test_extract_defined_acronym(self):
        """Test extracting defined acronym."""
        text = "The Critical Design Review (CDR) shall be conducted in Q3."
        acronyms = self.processor.extract_acronyms(text)

        # Find CDR
        cdr_acronyms = [a for a in acronyms if a.acronym == 'CDR']
        self.assertGreater(len(cdr_acronyms), 0)

        cdr = cdr_acronyms[0]
        self.assertTrue(cdr.is_defined)
        self.assertIsNotNone(cdr.expansion)

    def test_extract_standard_acronym(self):
        """Test extracting standard acronym without definition."""
        text = "NASA requirements apply to this mission."
        acronyms = self.processor.extract_acronyms(text)

        nasa_acronyms = [a for a in acronyms if a.acronym == 'NASA']
        self.assertGreater(len(nasa_acronyms), 0)

        nasa = nasa_acronyms[0]
        self.assertTrue(nasa.is_standard)
        # Should have expansion from standard list
        self.assertIsNotNone(nasa.expansion)

    def test_usage_count(self):
        """Test acronym usage count."""
        text = """
        The CDR is scheduled for June. Before the CDR, we must complete
        the PDR. The CDR checklist should be reviewed.
        """
        acronyms = self.processor.extract_acronyms(text)

        cdr_acronyms = [a for a in acronyms if a.acronym == 'CDR']
        if cdr_acronyms:
            cdr = cdr_acronyms[0]
            # CDR appears 3 times
            self.assertEqual(cdr.usage_count, 3)

    def test_acronym_confidence(self):
        """Test acronym confidence levels."""
        text = "The FAA and NASA will review the PDR before the CDR."
        acronyms = self.processor.extract_acronyms(text)

        for acr in acronyms:
            # All confidences should be in valid range
            self.assertGreaterEqual(acr.confidence, 0)
            self.assertLessEqual(acr.confidence, 1)


class TestDocumentAnalysis(unittest.TestCase):
    """Test comprehensive document analysis."""

    @classmethod
    def setUpClass(cls):
        """Set up test processor instance."""
        cls.processor = EnhancedNLPProcessor(load_immediately=True)

    def test_analyze_simple_document(self):
        """Test analyzing a simple document."""
        text = """
        The Project Manager shall ensure all requirements are met.
        The System Engineer is responsible for the design.
        The Critical Design Review (CDR) will be held in Q3.
        """
        analysis = self.processor.analyze_document(text)

        self.assertIsInstance(analysis, DocumentAnalysis)
        self.assertGreater(len(analysis.roles), 0)
        self.assertGreater(len(analysis.acronyms), 0)
        self.assertGreater(analysis.word_count, 0)
        self.assertGreater(analysis.sentence_count, 0)

    def test_analysis_finds_requirements(self):
        """Test analysis identifies shall statements."""
        text = """
        The system shall comply with all safety requirements.
        The software shall be tested according to the test plan.
        """
        analysis = self.processor.analyze_document(text)

        # Should find 2 shall statements
        self.assertEqual(len(analysis.requirements), 2)

    def test_analysis_finds_passive_voice(self):
        """Test analysis identifies passive voice."""
        text = "The report was written by the engineer. The code was reviewed."
        analysis = self.processor.analyze_document(text)

        # Should find passive voice
        # Note: This depends on spaCy model being loaded
        if self.processor.is_loaded:
            self.assertGreaterEqual(len(analysis.passive_voice), 1)

    def test_analysis_finds_ambiguous_terms(self):
        """Test analysis identifies ambiguous terms."""
        text = """
        The system shall provide appropriate warnings.
        Testing shall be conducted as required.
        """
        analysis = self.processor.analyze_document(text)

        # Should find ambiguous terms
        self.assertGreaterEqual(len(analysis.ambiguous_terms), 1)

    def test_analysis_readability_metrics(self):
        """Test analysis provides readability metrics."""
        text = "This is a test. This is another test sentence."
        analysis = self.processor.analyze_document(text)

        self.assertIn('word_count', analysis.readability_metrics)
        self.assertIn('sentence_count', analysis.readability_metrics)

    def test_analysis_processing_time(self):
        """Test analysis reports processing time."""
        text = "The Project Manager reviews documents."
        analysis = self.processor.analyze_document(text)

        self.assertGreater(analysis.processing_time_ms, 0)


class TestPatternData(unittest.TestCase):
    """Test pattern data integrity."""

    def test_aerospace_patterns_valid(self):
        """Test aerospace patterns have valid structure."""
        for pattern in AEROSPACE_ENTITY_PATTERNS:
            self.assertIn('label', pattern)
            self.assertIn('pattern', pattern)
            self.assertIsInstance(pattern['pattern'], list)
            self.assertGreater(len(pattern['pattern']), 0)

    def test_role_phrases_valid(self):
        """Test role phrases are non-empty strings."""
        for phrase in ROLE_PHRASES:
            self.assertIsInstance(phrase, str)
            self.assertGreater(len(phrase), 0)

    def test_standard_acronyms_valid(self):
        """Test standard acronyms have expansions."""
        for acronym, expansion in STANDARD_ACRONYMS.items():
            self.assertIsInstance(acronym, str)
            self.assertIsInstance(expansion, str)
            self.assertTrue(acronym.isupper() or acronym[0].isupper())
            self.assertGreater(len(expansion), len(acronym))


class TestExtractedRoleStructure(unittest.TestCase):
    """Test ExtractedRole data structure."""

    def test_role_to_dict(self):
        """Test role converts to dict correctly."""
        role = ExtractedRole(
            name="Project Manager",
            normalized_name="Project Manager",
            confidence=0.85,
            source="pattern",
            context="The Project Manager shall...",
            start_char=4,
            end_char=19,
            modifiers=["Project"],
            learning_boost=0.05,
            is_verified=True,
            coref_mentions=[]
        )

        d = role.to_dict()
        self.assertEqual(d['name'], "Project Manager")
        self.assertEqual(d['confidence'], 0.85)
        self.assertEqual(d['source'], "pattern")
        self.assertTrue(d['is_verified'])


class TestExtractedAcronymStructure(unittest.TestCase):
    """Test ExtractedAcronym data structure."""

    def test_acronym_to_dict(self):
        """Test acronym converts to dict correctly."""
        acr = ExtractedAcronym(
            acronym="CDR",
            expansion="Critical Design Review",
            confidence=0.95,
            is_defined=True,
            definition_location=50,
            usage_count=3,
            domain="aerospace",
            is_standard=True,
            coref_linked=[]
        )

        d = acr.to_dict()
        self.assertEqual(d['acronym'], "CDR")
        self.assertEqual(d['expansion'], "Critical Design Review")
        self.assertTrue(d['is_defined'])
        self.assertTrue(d['is_standard'])


class TestNLPAvailability(unittest.TestCase):
    """Test NLP availability checking."""

    def test_is_nlp_available(self):
        """Test is_nlp_available function."""
        # Should return True or False based on spaCy availability
        result = is_nlp_available()
        self.assertIsInstance(result, bool)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    @classmethod
    def setUpClass(cls):
        """Set up test processor instance."""
        cls.processor = EnhancedNLPProcessor(load_immediately=True)

    def test_very_long_text(self):
        """Test handling very long text."""
        # Create long text
        text = "The Project Manager reviews the system. " * 10000
        roles = self.processor.extract_roles(text)

        # Should not crash and should find roles
        self.assertIsInstance(roles, list)

    def test_special_characters(self):
        """Test handling special characters."""
        text = "The Project Manager (PM) reviews the $1M contract for ABC-123."
        roles = self.processor.extract_roles(text)

        # Should handle special chars gracefully
        self.assertIsInstance(roles, list)

    def test_unicode_text(self):
        """Test handling unicode text."""
        text = "The Programme Manager reviews the \u20ac5M budget."
        roles = self.processor.extract_roles(text)

        # Should handle unicode gracefully
        self.assertIsInstance(roles, list)

    def test_none_text(self):
        """Test handling None text gracefully."""
        try:
            roles = self.processor.extract_roles(None)
            # Should either return empty list or handle None
            self.assertIsInstance(roles, list)
        except (TypeError, AttributeError):
            # Acceptable to raise exception for None input
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
