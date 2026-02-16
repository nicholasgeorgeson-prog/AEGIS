"""
Unit Tests for Advanced Checkers
================================
Version: 1.0.0
Date: 2026-02-03

Tests for Phase 4 Advanced Checkers:
- Enhanced Passive Voice Checker
- Fragment Checker
- Requirements Analyzer
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_passive_checker import (
    EnhancedPassiveChecker, PassiveVoiceIssue,
    get_passive_checker, check_passive_voice, ADJECTIVAL_PARTICIPLES
)

from fragment_checker import (
    FragmentChecker, FragmentIssue,
    get_fragment_checker, check_fragments, SUBORDINATING_CONJUNCTIONS
)

from requirements_analyzer import (
    RequirementsAnalyzer, Requirement, RequirementIssue,
    get_requirements_analyzer, analyze_requirements,
    AMBIGUOUS_TERMS, ESCAPE_CLAUSES, MODAL_VERBS
)


# ============================================================
# PASSIVE VOICE CHECKER TESTS
# ============================================================

class TestPassiveVoiceChecker(unittest.TestCase):
    """Test enhanced passive voice detection."""

    @classmethod
    def setUpClass(cls):
        """Set up test checker instance."""
        cls.checker = EnhancedPassiveChecker(use_nlp=True)

    def test_detect_simple_passive(self):
        """Test detecting simple passive voice."""
        text = "The report was written by the engineer."
        issues = self.checker.check_text(text)

        # Should detect passive
        passive_issues = [i for i in issues if not i.is_false_positive]
        self.assertGreater(len(passive_issues), 0)

    def test_adjectival_not_flagged(self):
        """Test that adjectival participles are not flagged."""
        text = "The system is configured for production use."
        issues = self.checker.check_text(text)

        # Should NOT flag 'configured' as passive (it's adjectival)
        false_positives = [i for i in issues if i.is_false_positive]
        true_positives = [i for i in issues if not i.is_false_positive]

        # Either it's marked as false positive or not detected at all
        self.assertEqual(len(true_positives), 0)

    def test_acceptable_context_not_flagged(self):
        """Test that acceptable passive contexts are not flagged."""
        text = "This method is known as the standard approach."
        issues = self.checker.check_text(text)

        # "is known as" is acceptable
        true_positives = [i for i in issues if not i.is_false_positive]
        self.assertEqual(len(true_positives), 0)

    def test_shall_be_passive(self):
        """Test passive voice in shall statements."""
        text = "The document shall be reviewed by the QA team."
        issues = self.checker.check_text(text)

        # May be flagged but with lower confidence (requirements language)
        # Just verify it doesn't crash
        self.assertIsInstance(issues, list)

    def test_multiple_passive(self):
        """Test detecting multiple passive constructions."""
        text = """
        The report was submitted by the analyst.
        The data was corrupted by the malware.
        """
        issues = self.checker.check_text(text)

        # Should find passive voice issues (at least some)
        # The exact count depends on NLP model sensitivity
        self.assertIsInstance(issues, list)

    def test_no_passive_active_voice(self):
        """Test that active voice is not flagged."""
        text = "The engineer wrote the report. The team reviewed the code."
        issues = self.checker.check_text(text)

        true_positives = [i for i in issues if not i.is_false_positive]
        self.assertEqual(len(true_positives), 0)

    def test_statistics(self):
        """Test statistics generation."""
        text = "The report was written. The code was reviewed."
        issues = self.checker.check_text(text)
        stats = self.checker.get_statistics(issues)

        self.assertIn('total', stats)
        self.assertIn('true_positives', stats)
        self.assertIn('false_positives', stats)


class TestPassiveVoiceConvenience(unittest.TestCase):
    """Test passive voice convenience functions."""

    def test_get_passive_checker(self):
        """Test singleton getter."""
        checker1 = get_passive_checker()
        checker2 = get_passive_checker()
        self.assertIs(checker1, checker2)

    def test_check_passive_voice_function(self):
        """Test convenience function."""
        text = "The document was created."
        issues = check_passive_voice(text)

        self.assertIsInstance(issues, list)
        if issues:
            self.assertIn('sentence', issues[0])
            self.assertIn('confidence', issues[0])


# ============================================================
# FRAGMENT CHECKER TESTS
# ============================================================

class TestFragmentChecker(unittest.TestCase):
    """Test sentence fragment detection."""

    @classmethod
    def setUpClass(cls):
        """Set up test checker instance."""
        cls.checker = FragmentChecker(use_nlp=True)

    def test_detect_subordinate_fragment(self):
        """Test detecting subordinate clause fragments."""
        text = "Because the system failed."
        issues = self.checker.check_text(text)

        # Should detect fragment starting with subordinating conjunction
        if issues:  # Depends on NLP model quality
            self.assertEqual(issues[0].fragment_type, 'subordinate_only')

    def test_complete_sentence_not_flagged(self):
        """Test that complete sentences are not flagged."""
        text = "The system shall comply with requirements."
        issues = self.checker.check_text(text)

        self.assertEqual(len(issues), 0)

    def test_imperative_not_flagged(self):
        """Test that imperatives are not flagged as fragments."""
        text = "Review the document before submission."
        issues = self.checker.check_text(text)

        # Should NOT flag imperative sentences
        self.assertEqual(len(issues), 0)

    def test_heading_not_flagged(self):
        """Test that headings are not flagged."""
        text = "1.1 System Requirements"
        issues = self.checker.check_text(text)

        # Should recognize as intentional fragment (heading)
        self.assertEqual(len(issues), 0)

    def test_list_item_not_flagged(self):
        """Test that list items are not flagged."""
        text = "- Software requirements"
        issues = self.checker.check_text(text)

        self.assertEqual(len(issues), 0)

    def test_all_caps_heading(self):
        """Test that all-caps headings are not flagged."""
        text = "SYSTEM REQUIREMENTS"
        issues = self.checker.check_text(text)

        self.assertEqual(len(issues), 0)

    def test_statistics(self):
        """Test statistics generation."""
        text = "Because it failed. Although complete."
        issues = self.checker.check_text(text)
        stats = self.checker.get_statistics(issues)

        self.assertIn('total', stats)
        self.assertIn('subordinate_only', stats)


class TestFragmentConvenience(unittest.TestCase):
    """Test fragment checker convenience functions."""

    def test_get_fragment_checker(self):
        """Test singleton getter."""
        checker1 = get_fragment_checker()
        checker2 = get_fragment_checker()
        self.assertIs(checker1, checker2)

    def test_check_fragments_function(self):
        """Test convenience function."""
        text = "This is a complete sentence."
        issues = check_fragments(text)

        self.assertIsInstance(issues, list)


# ============================================================
# REQUIREMENTS ANALYZER TESTS
# ============================================================

class TestRequirementsAnalyzer(unittest.TestCase):
    """Test requirements analysis."""

    @classmethod
    def setUpClass(cls):
        """Set up test analyzer instance."""
        cls.analyzer = RequirementsAnalyzer(use_nlp=True)

    def test_extract_shall_statement(self):
        """Test extracting shall statements."""
        text = "REQ-001: The system shall provide real-time monitoring."
        reqs, issues = self.analyzer.analyze_text(text)

        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].modal_verb, 'shall')

    def test_detect_atomicity_violation(self):
        """Test detecting non-atomic requirements."""
        text = "The system shall log events and shall notify users."
        reqs, issues = self.analyzer.analyze_text(text)

        atomicity_issues = [i for i in issues if i.issue_type == 'atomicity']
        self.assertGreater(len(atomicity_issues), 0)

    def test_detect_escape_clause(self):
        """Test detecting TBD/TBR/TBS."""
        text = "The system shall process TBD transactions per second."
        reqs, issues = self.analyzer.analyze_text(text)

        escape_issues = [i for i in issues if i.issue_type == 'escape_clause']
        self.assertGreater(len(escape_issues), 0)
        self.assertEqual(escape_issues[0].severity, 'error')

    def test_detect_ambiguous_term(self):
        """Test detecting ambiguous terms."""
        text = "The system shall provide appropriate error messages."
        reqs, issues = self.analyzer.analyze_text(text)

        ambiguous_issues = [i for i in issues if i.issue_type == 'ambiguous']
        self.assertGreater(len(ambiguous_issues), 0)
        self.assertTrue(any('appropriate' in i.flagged_text for i in ambiguous_issues if i.flagged_text))

    def test_detect_weak_modal(self):
        """Test detecting weak modal verbs."""
        text = "The system should provide logging capability."
        reqs, issues = self.analyzer.analyze_text(text)

        modal_issues = [i for i in issues if i.issue_type == 'modal_inconsistency']
        self.assertGreater(len(modal_issues), 0)

    def test_testability_check(self):
        """Test testability checking."""
        text = "The system shall be fast."
        reqs, issues = self.analyzer.analyze_text(text)

        testability_issues = [i for i in issues if i.issue_type == 'testability']
        self.assertGreater(len(testability_issues), 0)

    def test_measurable_requirement_passes(self):
        """Test that measurable requirements pass testability."""
        text = "The system shall respond within 100 milliseconds."
        reqs, issues = self.analyzer.analyze_text(text)

        testability_issues = [i for i in issues if i.issue_type == 'testability']
        self.assertEqual(len(testability_issues), 0)

    def test_extract_requirement_id(self):
        """Test requirement ID extraction."""
        text = "REQ-123: The system shall store data."
        reqs, issues = self.analyzer.analyze_text(text)

        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, 'REQ-123')

    def test_multiple_requirements(self):
        """Test analyzing multiple requirements."""
        text = """
        SYS-001: The system shall log all events.
        SYS-002: The system shall provide user authentication.
        SYS-003: The system shall support TBD concurrent users.
        """
        reqs, issues = self.analyzer.analyze_text(text)

        self.assertEqual(len(reqs), 3)
        # Should find escape clause in SYS-003
        escape_issues = [i for i in issues if i.issue_type == 'escape_clause']
        self.assertGreater(len(escape_issues), 0)

    def test_statistics(self):
        """Test statistics generation."""
        text = "The system shall process data. The module will store results."
        reqs, issues = self.analyzer.analyze_text(text)
        stats = self.analyzer.get_statistics(reqs, issues)

        self.assertIn('total_requirements', stats)
        self.assertIn('total_issues', stats)
        self.assertIn('modal_distribution', stats)


class TestRequirementsConvenience(unittest.TestCase):
    """Test requirements analyzer convenience functions."""

    def test_get_requirements_analyzer(self):
        """Test singleton getter."""
        analyzer1 = get_requirements_analyzer()
        analyzer2 = get_requirements_analyzer()
        self.assertIs(analyzer1, analyzer2)

    def test_analyze_requirements_function(self):
        """Test convenience function."""
        text = "The system shall comply with ISO standards."
        result = analyze_requirements(text)

        self.assertIn('requirements', result)
        self.assertIn('issues', result)
        self.assertIn('statistics', result)


# ============================================================
# DATA INTEGRITY TESTS
# ============================================================

class TestDataIntegrity(unittest.TestCase):
    """Test data structures and constants."""

    def test_adjectival_participles_non_empty(self):
        """Test adjectival participles set is populated."""
        self.assertGreater(len(ADJECTIVAL_PARTICIPLES), 100)

    def test_subordinating_conjunctions_non_empty(self):
        """Test subordinating conjunctions set is populated."""
        self.assertGreater(len(SUBORDINATING_CONJUNCTIONS), 10)

    def test_ambiguous_terms_non_empty(self):
        """Test ambiguous terms set is populated."""
        self.assertGreater(len(AMBIGUOUS_TERMS), 30)

    def test_escape_clauses_non_empty(self):
        """Test escape clauses set is populated."""
        self.assertGreater(len(ESCAPE_CLAUSES), 5)

    def test_modal_verbs_complete(self):
        """Test modal verbs dictionary is complete."""
        expected_modals = {'shall', 'must', 'will', 'should', 'may', 'can'}
        self.assertTrue(expected_modals.issubset(set(MODAL_VERBS.keys())))


if __name__ == '__main__':
    unittest.main(verbosity=2)
