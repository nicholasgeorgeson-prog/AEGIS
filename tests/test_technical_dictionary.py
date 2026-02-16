"""
Unit Tests for Technical Dictionary System
==========================================
Version: 1.0.0
Date: 2026-02-03

Tests the TechnicalDictionary class for:
- Term validation
- Spelling corrections
- Acronym expansions
- Custom term management
- Search functionality
- Statistics tracking
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technical_dictionary import TechnicalDictionary, get_technical_dictionary, DictionaryStats


class TestTechnicalDictionaryBasics(unittest.TestCase):
    """Test basic dictionary functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_initialization(self):
        """Test dictionary initializes with embedded data."""
        self.assertIsNotNone(self.dict)
        stats = self.dict.get_stats()
        self.assertGreater(stats.total_terms, 1000)
        self.assertGreater(stats.corrections, 100)
        self.assertGreater(stats.acronyms, 100)

    def test_version(self):
        """Test version attribute exists."""
        self.assertEqual(self.dict.VERSION, '1.0.0')


class TestTermValidation(unittest.TestCase):
    """Test term validation functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_valid_aerospace_term(self):
        """Test valid aerospace terms are recognized."""
        self.assertTrue(self.dict.is_valid_term('avionics'))
        self.assertTrue(self.dict.is_valid_term('aerodynamic'))
        self.assertTrue(self.dict.is_valid_term('propulsion'))

    def test_valid_defense_term(self):
        """Test valid defense terms are recognized."""
        self.assertTrue(self.dict.is_valid_term('acquisition'))
        self.assertTrue(self.dict.is_valid_term('sustainment'))
        self.assertTrue(self.dict.is_valid_term('milestone'))

    def test_valid_software_term(self):
        """Test valid software terms are recognized."""
        self.assertTrue(self.dict.is_valid_term('backend'))
        self.assertTrue(self.dict.is_valid_term('api'))
        self.assertTrue(self.dict.is_valid_term('kubernetes'))

    def test_case_insensitivity(self):
        """Test term validation is case-insensitive."""
        self.assertTrue(self.dict.is_valid_term('AVIONICS'))
        self.assertTrue(self.dict.is_valid_term('Avionics'))
        self.assertTrue(self.dict.is_valid_term('avionics'))

    def test_invalid_term(self):
        """Test invalid terms return False."""
        self.assertFalse(self.dict.is_valid_term('xyznotaword'))
        self.assertFalse(self.dict.is_valid_term('asdfghjkl'))

    def test_empty_input(self):
        """Test empty and None inputs are handled."""
        self.assertFalse(self.dict.is_valid_term(''))
        self.assertFalse(self.dict.is_valid_term(None))
        self.assertFalse(self.dict.is_valid_term('   '))


class TestSpellingCorrections(unittest.TestCase):
    """Test spelling correction functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_common_misspelling(self):
        """Test common misspellings are corrected."""
        self.assertEqual(self.dict.get_correction('recieve'), 'receive')
        self.assertEqual(self.dict.get_correction('occured'), 'occurred')
        self.assertEqual(self.dict.get_correction('seperate'), 'separate')

    def test_technical_misspelling(self):
        """Test technical misspellings are corrected."""
        self.assertEqual(self.dict.get_correction('aquisition'), 'acquisition')
        self.assertEqual(self.dict.get_correction('developement'), 'development')
        self.assertEqual(self.dict.get_correction('implimentation'), 'implementation')

    def test_case_insensitivity(self):
        """Test corrections work case-insensitively."""
        self.assertEqual(self.dict.get_correction('RECIEVE'), 'receive')
        self.assertEqual(self.dict.get_correction('Recieve'), 'receive')

    def test_no_correction_needed(self):
        """Test correctly spelled words return None."""
        self.assertIsNone(self.dict.get_correction('receive'))
        self.assertIsNone(self.dict.get_correction('development'))

    def test_unknown_word(self):
        """Test unknown words return None."""
        self.assertIsNone(self.dict.get_correction('xyznotaword'))

    def test_empty_input(self):
        """Test empty inputs return None."""
        self.assertIsNone(self.dict.get_correction(''))
        self.assertIsNone(self.dict.get_correction(None))


class TestAcronymExpansions(unittest.TestCase):
    """Test acronym expansion functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_common_acronym(self):
        """Test common acronyms are expanded."""
        self.assertEqual(self.dict.get_acronym_expansion('NASA'),
                        'National Aeronautics and Space Administration')
        self.assertEqual(self.dict.get_acronym_expansion('FAA'),
                        'Federal Aviation Administration')

    def test_program_management_acronym(self):
        """Test program management acronyms are expanded."""
        self.assertEqual(self.dict.get_acronym_expansion('WBS'),
                        'Work Breakdown Structure')
        self.assertEqual(self.dict.get_acronym_expansion('EVM'),
                        'Earned Value Management')

    def test_systems_engineering_acronym(self):
        """Test systems engineering acronyms are expanded."""
        self.assertEqual(self.dict.get_acronym_expansion('CDR'),
                        'Critical Design Review')
        self.assertEqual(self.dict.get_acronym_expansion('PDR'),
                        'Preliminary Design Review')

    def test_case_handling(self):
        """Test acronyms are uppercased for lookup."""
        self.assertEqual(self.dict.get_acronym_expansion('nasa'),
                        'National Aeronautics and Space Administration')
        self.assertEqual(self.dict.get_acronym_expansion('Nasa'),
                        'National Aeronautics and Space Administration')

    def test_unknown_acronym(self):
        """Test unknown acronyms return None."""
        self.assertIsNone(self.dict.get_acronym_expansion('XYZABC'))

    def test_is_acronym(self):
        """Test acronym detection."""
        self.assertTrue(self.dict.is_acronym('NASA'))
        self.assertTrue(self.dict.is_acronym('FAA'))
        self.assertFalse(self.dict.is_acronym('NOTANACRONYM'))


class TestProperNouns(unittest.TestCase):
    """Test proper noun recognition."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_company_recognition(self):
        """Test company names are recognized."""
        self.assertTrue(self.dict.is_proper_noun('Boeing'))
        self.assertTrue(self.dict.is_proper_noun('Lockheed Martin'))
        self.assertTrue(self.dict.is_proper_noun('SpaceX'))

    def test_agency_recognition(self):
        """Test agency names are recognized."""
        self.assertTrue(self.dict.is_proper_noun('NASA'))
        self.assertTrue(self.dict.is_proper_noun('DARPA'))

    def test_term_validation_includes_proper_nouns(self):
        """Test proper nouns are valid terms."""
        self.assertTrue(self.dict.is_valid_term('Boeing'))
        self.assertTrue(self.dict.is_valid_term('NASA'))


class TestCustomTerms(unittest.TestCase):
    """Test custom term management."""

    def setUp(self):
        """Create fresh dictionary for each test."""
        self.dict = TechnicalDictionary(load_external=False)

    def test_add_custom_term(self):
        """Test adding custom terms."""
        self.assertFalse(self.dict.is_valid_term('mycustomterm'))
        self.assertTrue(self.dict.add_custom_term('mycustomterm'))
        self.assertTrue(self.dict.is_valid_term('mycustomterm'))

    def test_add_empty_term_fails(self):
        """Test adding empty terms fails."""
        self.assertFalse(self.dict.add_custom_term(''))
        self.assertFalse(self.dict.add_custom_term(None))
        self.assertFalse(self.dict.add_custom_term('   '))

    def test_remove_custom_term(self):
        """Test removing custom terms."""
        self.dict.add_custom_term('temporaryterm')
        self.assertTrue(self.dict.is_valid_term('temporaryterm'))
        self.assertTrue(self.dict.remove_custom_term('temporaryterm'))
        self.assertFalse(self.dict.is_valid_term('temporaryterm'))

    def test_remove_nonexistent_term(self):
        """Test removing non-existent term returns False."""
        self.assertFalse(self.dict.remove_custom_term('nonexistentterm'))

    def test_stats_update_after_add(self):
        """Test statistics update after adding terms."""
        initial_stats = self.dict.get_stats()
        initial_custom = initial_stats.custom_terms

        self.dict.add_custom_term('newterm1')
        self.dict.add_custom_term('newterm2')

        new_stats = self.dict.get_stats()
        self.assertEqual(new_stats.custom_terms, initial_custom + 2)


class TestSearchFunctionality(unittest.TestCase):
    """Test search functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_substring_search(self):
        """Test substring search works."""
        results = self.dict.search_terms('aero')
        self.assertGreater(len(results), 0)
        self.assertTrue(all('aero' in term for term in results))

    def test_regex_search(self):
        """Test regex search works."""
        results = self.dict.search_terms('^aero.*ic$')
        self.assertGreater(len(results), 0)
        # Should match aerodynamic, aeronautic, etc.

    def test_search_limit(self):
        """Test search respects limit."""
        results = self.dict.search_terms('a', limit=10)
        self.assertLessEqual(len(results), 10)

    def test_search_empty_pattern(self):
        """Test search with empty pattern."""
        results = self.dict.search_terms('')
        self.assertIsInstance(results, list)


class TestSimilarSuggestions(unittest.TestCase):
    """Test similar word suggestions."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_suggest_similar(self):
        """Test similar word suggestions."""
        # 'avioncs' is close to 'avionics'
        suggestions = self.dict.suggest_similar('avioncs', max_distance=2)
        self.assertGreater(len(suggestions), 0)
        # Check format is (word, distance)
        self.assertIsInstance(suggestions[0], tuple)
        self.assertEqual(len(suggestions[0]), 2)

    def test_suggest_similar_empty(self):
        """Test suggestions for empty input."""
        suggestions = self.dict.suggest_similar('')
        self.assertEqual(len(suggestions), 0)


class TestStatistics(unittest.TestCase):
    """Test dictionary statistics."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_stats_structure(self):
        """Test statistics have expected structure."""
        stats = self.dict.get_stats()
        self.assertIsInstance(stats, DictionaryStats)
        self.assertIsInstance(stats.total_terms, int)
        self.assertIsInstance(stats.aerospace_terms, int)
        self.assertIsInstance(stats.corrections, int)
        self.assertIsInstance(stats.acronyms, int)

    def test_stats_values(self):
        """Test statistics have reasonable values."""
        stats = self.dict.get_stats()
        # Base embedded dictionary has ~1200 terms
        # External dictionaries would bring this to 10,000+
        self.assertGreater(stats.total_terms, 1000)
        self.assertGreater(stats.aerospace_terms, 100)
        self.assertGreater(stats.defense_terms, 100)
        self.assertGreater(stats.corrections, 100)
        self.assertGreater(stats.acronyms, 200)


class TestSingletonPattern(unittest.TestCase):
    """Test singleton pattern for dictionary."""

    def test_singleton_returns_same_instance(self):
        """Test get_technical_dictionary returns same instance."""
        dict1 = get_technical_dictionary()
        dict2 = get_technical_dictionary()
        self.assertIs(dict1, dict2)

    def test_singleton_is_initialized(self):
        """Test singleton is properly initialized."""
        dict = get_technical_dictionary()
        self.assertIsNotNone(dict)
        self.assertGreater(dict.get_stats().total_terms, 0)


class TestGetAllMethods(unittest.TestCase):
    """Test methods that return all data."""

    @classmethod
    def setUpClass(cls):
        """Set up test dictionary instance."""
        cls.dict = TechnicalDictionary(load_external=False)

    def test_get_all_corrections(self):
        """Test getting all corrections."""
        corrections = self.dict.get_all_corrections()
        self.assertIsInstance(corrections, dict)
        self.assertGreater(len(corrections), 100)
        # Verify it's a copy
        corrections['test'] = 'test'
        self.assertNotIn('test', self.dict.get_all_corrections())

    def test_get_all_acronyms(self):
        """Test getting all acronyms."""
        acronyms = self.dict.get_all_acronyms()
        self.assertIsInstance(acronyms, dict)
        self.assertGreater(len(acronyms), 100)
        # Verify it's a copy
        acronyms['TEST'] = 'Test Expansion'
        self.assertNotIn('TEST', self.dict.get_all_acronyms())


if __name__ == '__main__':
    unittest.main(verbosity=2)
