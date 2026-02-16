"""
Unit Tests for Adaptive Learning System
=======================================
Version: 1.0.0
Date: 2026-02-03

Tests the AdaptiveLearner class for:
- Decision recording and pattern tracking
- Prediction generation
- Role/acronym-specific learning
- Custom dictionary management
- Export/import functionality
- Statistics tracking
"""

import unittest
import sys
import os
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adaptive_learner import (
    AdaptiveLearner, LearningDecision, get_adaptive_learner,
    make_role_pattern_key, make_acronym_pattern_key, make_grammar_pattern_key,
    record_role_decision, record_acronym_decision, record_grammar_decision,
    get_role_boost, is_learned_valid_role, is_learned_invalid_role
)


class TestPatternKeyGeneration(unittest.TestCase):
    """Test pattern key generation functions."""

    def test_role_pattern_key(self):
        """Test role pattern key generation."""
        key = make_role_pattern_key('Project Manager', 'table')
        self.assertEqual(key, 'role:project_manager:table')

    def test_role_pattern_key_special_chars(self):
        """Test role pattern key with special characters."""
        key = make_role_pattern_key('Sr. Engineer (Lead)', 'sentence')
        self.assertTrue(key.startswith('role:'))
        self.assertIn('sentence', key)

    def test_acronym_pattern_key(self):
        """Test acronym pattern key generation."""
        key = make_acronym_pattern_key('NASA', 'National Aeronautics and Space Administration')
        self.assertTrue(key.startswith('acronym:NASA:'))

    def test_grammar_pattern_key(self):
        """Test grammar pattern key generation."""
        key = make_grammar_pattern_key('Passive Voice', 'was written', 'wrote')
        self.assertTrue(key.startswith('grammar:passive voice:'))


class TestAdaptiveLearnerBasics(unittest.TestCase):
    """Test basic learner functionality."""

    def setUp(self):
        """Create fresh learner with temp database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_initialization(self):
        """Test learner initializes correctly."""
        self.assertIsNotNone(self.learner)
        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 0)

    def test_record_simple_decision(self):
        """Test recording a simple decision."""
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:project_manager:table',
            decision='accepted',
            original_value='Project Manager',
            context='The Project Manager is responsible...'
        )
        result = self.learner.record_decision(decision)
        self.assertTrue(result)

        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 1)
        self.assertEqual(stats.role_decisions, 1)

    def test_record_multiple_decisions(self):
        """Test recording multiple decisions."""
        for i in range(5):
            decision = LearningDecision(
                decision_type='role',
                pattern_key=f'role:engineer_{i}:sentence',
                decision='accepted' if i % 2 == 0 else 'rejected',
                original_value=f'Engineer {i}'
            )
            self.learner.record_decision(decision)

        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 5)

    def test_empty_pattern_key_rejected(self):
        """Test that empty pattern keys are rejected."""
        decision = LearningDecision(
            decision_type='role',
            pattern_key='',
            decision='accepted',
            original_value='Test'
        )
        result = self.learner.record_decision(decision)
        self.assertFalse(result)


class TestPredictions(unittest.TestCase):
    """Test prediction functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_no_prediction_without_history(self):
        """Test that no prediction is made without history."""
        prediction = self.learner.get_prediction('role:unknown_role:table')
        self.assertIsNone(prediction['prediction'])
        self.assertEqual(prediction['confidence'], 0.0)

    def test_no_prediction_with_few_decisions(self):
        """Test that no prediction is made with too few decisions."""
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:test_role:table',
            decision='accepted',
            original_value='Test Role'
        )
        self.learner.record_decision(decision)

        prediction = self.learner.get_prediction('role:test_role:table')
        self.assertIsNone(prediction['prediction'])
        self.assertIn('Not enough history', prediction['reason'])

    def test_accept_prediction(self):
        """Test accept prediction after multiple accepts."""
        pattern_key = 'role:project_manager:table'

        # Record 3 accepts
        for _ in range(3):
            decision = LearningDecision(
                decision_type='role',
                pattern_key=pattern_key,
                decision='accepted',
                original_value='Project Manager'
            )
            self.learner.record_decision(decision)

        prediction = self.learner.get_prediction(pattern_key)
        self.assertEqual(prediction['prediction'], 'accept')
        self.assertGreater(prediction['confidence'], 0.7)

    def test_reject_prediction(self):
        """Test reject prediction after multiple rejects."""
        pattern_key = 'role:false_positive:sentence'

        # Record 3 rejects
        for _ in range(3):
            decision = LearningDecision(
                decision_type='role',
                pattern_key=pattern_key,
                decision='rejected',
                original_value='False Positive'
            )
            self.learner.record_decision(decision)

        prediction = self.learner.get_prediction(pattern_key)
        self.assertEqual(prediction['prediction'], 'reject')
        self.assertGreater(prediction['confidence'], 0.7)

    def test_mixed_no_prediction(self):
        """Test no prediction with mixed decisions."""
        pattern_key = 'role:ambiguous_role:table'

        # Record mixed decisions
        decisions = ['accepted', 'rejected', 'accepted', 'rejected']
        for dec in decisions:
            decision = LearningDecision(
                decision_type='role',
                pattern_key=pattern_key,
                decision=dec,
                original_value='Ambiguous Role'
            )
            self.learner.record_decision(decision)

        prediction = self.learner.get_prediction(pattern_key)
        self.assertIsNone(prediction['prediction'])


class TestRoleLearning(unittest.TestCase):
    """Test role-specific learning functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_role_confidence_boost_initial(self):
        """Test role confidence boost with no history."""
        boost = self.learner.get_role_confidence_boost('Unknown Role', 'table')
        self.assertEqual(boost, 0.0)

    def test_role_confidence_boost_after_accept(self):
        """Test role confidence boost increases after accept."""
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:test_manager:table',
            decision='accepted',
            original_value='Test Manager'
        )
        self.learner.record_decision(decision)

        boost = self.learner.get_role_confidence_boost('Test Manager', 'table')
        self.assertGreater(boost, 0.0)

    def test_role_confidence_boost_after_reject(self):
        """Test role confidence boost decreases after reject."""
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:false_role:sentence',
            decision='rejected',
            original_value='False Role'
        )
        self.learner.record_decision(decision)

        boost = self.learner.get_role_confidence_boost('False Role', 'sentence')
        self.assertLess(boost, 0.0)

    def test_known_valid_role_detection(self):
        """Test known valid role detection after multiple accepts."""
        # Record 3 accepts to mark as known valid
        for _ in range(3):
            decision = LearningDecision(
                decision_type='role',
                pattern_key='role:known_manager:table',
                decision='accepted',
                original_value='Known Manager'
            )
            self.learner.record_decision(decision)

        self.assertTrue(self.learner.is_known_valid_role('Known Manager'))
        self.assertFalse(self.learner.is_known_invalid_role('Known Manager'))

    def test_known_invalid_role_detection(self):
        """Test known invalid role detection after multiple rejects."""
        # Record 3 rejects to mark as known invalid
        for _ in range(3):
            decision = LearningDecision(
                decision_type='role',
                pattern_key='role:bad_detection:sentence',
                decision='rejected',
                original_value='Bad Detection'
            )
            self.learner.record_decision(decision)

        self.assertTrue(self.learner.is_known_invalid_role('Bad Detection'))
        self.assertFalse(self.learner.is_known_valid_role('Bad Detection'))


class TestCustomDictionary(unittest.TestCase):
    """Test custom dictionary functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_add_to_dictionary(self):
        """Test adding term to dictionary."""
        result = self.learner.add_to_dictionary('avionics')
        self.assertTrue(result)
        self.assertTrue(self.learner.is_in_dictionary('avionics'))

    def test_add_empty_term_fails(self):
        """Test that adding empty term fails."""
        result = self.learner.add_to_dictionary('')
        self.assertFalse(result)

    def test_case_insensitive_lookup(self):
        """Test dictionary lookup is case-insensitive."""
        self.learner.add_to_dictionary('TechTerm')
        self.assertTrue(self.learner.is_in_dictionary('techterm'))
        self.assertTrue(self.learner.is_in_dictionary('TECHTERM'))

    def test_remove_from_dictionary(self):
        """Test removing term from dictionary."""
        self.learner.add_to_dictionary('removeme')
        self.assertTrue(self.learner.is_in_dictionary('removeme'))

        result = self.learner.remove_from_dictionary('removeme')
        self.assertTrue(result)
        self.assertFalse(self.learner.is_in_dictionary('removeme'))

    def test_get_dictionary(self):
        """Test getting all dictionary terms."""
        self.learner.add_to_dictionary('term1')
        self.learner.add_to_dictionary('term2')
        self.learner.add_to_dictionary('term3')

        dictionary = self.learner.get_dictionary()
        self.assertEqual(len(dictionary), 3)


class TestExportImport(unittest.TestCase):
    """Test export/import functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_export_empty_database(self):
        """Test exporting empty database."""
        data = self.learner.export_data()
        self.assertEqual(data['format'], 'twr_adaptive_learning')
        self.assertEqual(len(data['patterns']), 0)

    def test_export_with_data(self):
        """Test exporting database with data."""
        # Add some data
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:test:table',
            decision='accepted',
            original_value='Test'
        )
        self.learner.record_decision(decision)
        self.learner.add_to_dictionary('testword')

        data = self.learner.export_data()
        self.assertGreater(len(data['patterns']), 0)
        self.assertGreater(len(data['dictionary']), 0)

    def test_import_data(self):
        """Test importing data."""
        # Create export data
        export_data = {
            'version': '1.0.0',
            'format': 'twr_adaptive_learning',
            'patterns': [
                {
                    'pattern_key': 'role:imported_role:table',
                    'pattern_type': 'role',
                    'original_value': 'Imported Role',
                    'accept_count': 5,
                    'reject_count': 0,
                    'edit_count': 0,
                    'total_count': 5,
                    'confidence': 0.9,
                    'predicted_action': 'accept',
                    'first_seen': '2026-01-01',
                    'last_seen': '2026-02-01'
                }
            ],
            'role_patterns': [],
            'acronym_patterns': [],
            'context_patterns': [],
            'dictionary': [
                {'term': 'importedterm', 'term_type': 'word', 'category': 'custom'}
            ]
        }

        result = self.learner.import_data(export_data)
        self.assertTrue(result['success'])
        self.assertEqual(result['imported']['patterns'], 1)
        self.assertEqual(result['imported']['dictionary'], 1)

        # Verify imported data
        self.assertTrue(self.learner.is_in_dictionary('importedterm'))
        prediction = self.learner.get_prediction('role:imported_role:table')
        self.assertEqual(prediction['prediction'], 'accept')

    def test_import_invalid_format(self):
        """Test importing invalid data format."""
        result = self.learner.import_data({'invalid': 'data'})
        self.assertFalse(result['success'])


class TestStatistics(unittest.TestCase):
    """Test statistics functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_statistics_empty(self):
        """Test statistics on empty database."""
        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 0)
        self.assertEqual(stats.unique_patterns, 0)
        self.assertEqual(stats.dictionary_size, 0)

    def test_statistics_with_data(self):
        """Test statistics with various data."""
        # Add role decisions
        for i in range(5):
            decision = LearningDecision(
                decision_type='role',
                pattern_key=f'role:role_{i}:table',
                decision='accepted',
                original_value=f'Role {i}'
            )
            self.learner.record_decision(decision)

        # Add acronym decisions
        for i in range(3):
            decision = LearningDecision(
                decision_type='acronym',
                pattern_key=f'acronym:ACR{i}:expansion',
                decision='accepted',
                original_value=f'ACR{i}'
            )
            self.learner.record_decision(decision)

        # Add dictionary terms
        self.learner.add_to_dictionary('word1')
        self.learner.add_to_dictionary('word2')

        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 8)
        self.assertEqual(stats.role_decisions, 5)
        self.assertEqual(stats.acronym_decisions, 3)
        self.assertEqual(stats.unique_patterns, 8)
        self.assertEqual(stats.dictionary_size, 2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Reset singleton for clean tests."""
        import adaptive_learner
        adaptive_learner._learner_instance = None

        # Create temp database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()

    def tearDown(self):
        """Clean up."""
        import adaptive_learner
        adaptive_learner._learner_instance = None
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_record_role_decision_function(self):
        """Test record_role_decision convenience function."""
        import adaptive_learner
        adaptive_learner._learner_instance = AdaptiveLearner(db_path=self.temp_db.name)

        result = record_role_decision(
            role_name='Test Manager',
            decision='accepted',
            source='table',
            context='In a RACI matrix...'
        )
        self.assertTrue(result)

    def test_record_acronym_decision_function(self):
        """Test record_acronym_decision convenience function."""
        import adaptive_learner
        adaptive_learner._learner_instance = AdaptiveLearner(db_path=self.temp_db.name)

        result = record_acronym_decision(
            acronym='NASA',
            expansion='National Aeronautics and Space Administration',
            decision='accepted',
            context='NASA was founded...'
        )
        self.assertTrue(result)

    def test_get_role_boost_function(self):
        """Test get_role_boost convenience function."""
        import adaptive_learner
        adaptive_learner._learner_instance = AdaptiveLearner(db_path=self.temp_db.name)

        # Should return 0 with no history
        boost = get_role_boost('Unknown Role', 'table')
        self.assertEqual(boost, 0.0)


class TestMaintenance(unittest.TestCase):
    """Test maintenance functionality."""

    def setUp(self):
        """Create fresh learner with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.learner = AdaptiveLearner(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_reset_learning(self):
        """Test resetting all learning data."""
        # Add some data
        decision = LearningDecision(
            decision_type='role',
            pattern_key='role:test:table',
            decision='accepted',
            original_value='Test'
        )
        self.learner.record_decision(decision)

        stats = self.learner.get_statistics()
        self.assertGreater(stats.total_decisions, 0)

        # Reset
        result = self.learner.reset_learning()
        self.assertTrue(result)

        stats = self.learner.get_statistics()
        self.assertEqual(stats.total_decisions, 0)

    def test_reset_specific_type(self):
        """Test resetting specific pattern type."""
        # Add role and acronym decisions
        role_decision = LearningDecision(
            decision_type='role',
            pattern_key='role:test:table',
            decision='accepted',
            original_value='Test Role'
        )
        self.learner.record_decision(role_decision)

        acronym_decision = LearningDecision(
            decision_type='acronym',
            pattern_key='acronym:TEST:expansion',
            decision='accepted',
            original_value='TEST'
        )
        self.learner.record_decision(acronym_decision)

        # Reset only roles
        self.learner.reset_learning(['role'])

        stats = self.learner.get_statistics()
        self.assertEqual(stats.role_decisions, 0)
        self.assertEqual(stats.acronym_decisions, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
