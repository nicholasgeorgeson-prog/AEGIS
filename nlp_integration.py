"""
NLP Integration Module for AEGIS v3.3.0
===================================================
Integrates all v3.3.0 NLP Enhancement Suite modules into the core review engine.

This module provides:
- Enhanced passive voice checking (dependency-based)
- Sentence fragment detection (syntactic parsing)
- Requirements analysis (atomicity, testability, escape clauses)
- Terminology consistency checking
- Cross-reference validation
- Technical dictionary integration
- Adaptive learning integration
- Enhanced NLP role extraction

All features are 100% offline-capable for air-gapped deployment.

Version: 3.3.0
Author: Nick / SAIC Systems Engineering
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import re

# Structured logging support
try:
    from config_logging import get_logger
    _logger = get_logger('nlp_integration')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[NLPIntegration] {level.upper()}: {message}")


# =============================================================================
# BASE CHECKER INTERFACE
# =============================================================================

class BaseEnhancedChecker:
    """Base class for v3.3.0 enhanced checkers."""

    CHECKER_NAME = "Base Enhanced Checker"
    CHECKER_VERSION = "3.3.0"

    def __init__(self):
        self._available = False
        self._error = None

    @property
    def is_available(self) -> bool:
        return self._available

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Run the check and return issues."""
        raise NotImplementedError

    def safe_check(self, paragraphs: List[Tuple[int, str]] = None, **kwargs) -> List[Dict]:
        """Safe wrapper that catches exceptions."""
        if not self._available:
            return []
        try:
            return self.check(paragraphs or [], **kwargs)
        except Exception as e:
            _log(f"Error in {self.CHECKER_NAME}: {e}", level='error')
            return []


# =============================================================================
# ENHANCED PASSIVE VOICE CHECKER
# =============================================================================

class EnhancedPassiveVoiceChecker(BaseEnhancedChecker):
    """
    Dependency parsing-based passive voice detection.
    Uses spaCy dependency trees instead of regex patterns.
    Includes 300+ adjectival participles whitelist.
    """

    CHECKER_NAME = "Enhanced Passive Voice"

    def __init__(self):
        super().__init__()
        try:
            from enhanced_passive_checker import (
                get_passive_checker,
                check_passive_voice as _check_pv
            )
            self._checker = get_passive_checker()
            self._check_func = _check_pv
            self._available = self._checker is not None
            if self._available:
                _log(f"Enhanced passive voice checker loaded (v3.3.0)")
        except ImportError as e:
            self._error = str(e)
            _log(f"Enhanced passive voice checker not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check for passive voice using dependency parsing."""
        if not self._available:
            return []

        issues = []
        full_text = kwargs.get('full_text', '')

        # Use the enhanced checker
        result = self._checker.check_text(full_text)

        for pv in result.passive_instances:
            # Find paragraph index
            para_idx = 0
            for idx, text in paragraphs:
                if pv.sentence in text or text in pv.sentence:
                    para_idx = idx
                    break

            issue = {
                'type': 'passive_voice',
                'category': 'grammar',
                'severity': 'low',
                'message': f"Passive voice: '{pv.passive_phrase}'",
                'paragraph': para_idx,
                'text': pv.sentence,
                'suggestion': pv.suggestion or "Consider using active voice",
                'confidence': pv.confidence,
                'source': 'enhanced_passive_v3.3.0'
            }
            issues.append(issue)

        return issues


# =============================================================================
# SENTENCE FRAGMENT CHECKER
# =============================================================================

class SentenceFragmentChecker(BaseEnhancedChecker):
    """
    Syntactic parsing for sentence fragment detection.
    Uses spaCy to detect missing subjects or finite verbs.
    """

    CHECKER_NAME = "Sentence Fragments"

    def __init__(self):
        super().__init__()
        try:
            from fragment_checker import (
                get_fragment_checker,
                check_fragments as _check_frags
            )
            self._checker = get_fragment_checker()
            self._check_func = _check_frags
            self._available = self._checker is not None
            if self._available:
                _log(f"Sentence fragment checker loaded (v3.3.0)")
        except ImportError as e:
            self._error = str(e)
            _log(f"Fragment checker not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check for sentence fragments."""
        if not self._available:
            return []

        issues = []

        for para_idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            result = self._checker.check_text(text)

            for frag in result.fragments:
                issue = {
                    'type': 'sentence_fragment',
                    'category': 'grammar',
                    'severity': 'medium',
                    'message': f"Possible sentence fragment: {frag.fragment_type}",
                    'paragraph': para_idx,
                    'text': frag.text,
                    'suggestion': frag.suggestion or "Ensure sentence has subject and verb",
                    'confidence': frag.confidence,
                    'source': 'fragment_checker_v3.3.0'
                }
                issues.append(issue)

        return issues


# =============================================================================
# REQUIREMENTS ANALYZER
# =============================================================================

class RequirementsAnalyzerChecker(BaseEnhancedChecker):
    """
    Technical document requirements analysis.
    Checks atomicity, testability, escape clauses, and ambiguous terms.
    """

    CHECKER_NAME = "Requirements Analysis"

    def __init__(self):
        super().__init__()
        try:
            from requirements_analyzer import (
                get_requirements_analyzer,
                analyze_requirements as _analyze_reqs
            )
            self._analyzer = get_requirements_analyzer()
            self._analyze_func = _analyze_reqs
            self._available = self._analyzer is not None
            if self._available:
                _log(f"Requirements analyzer loaded (v3.3.0)")
        except ImportError as e:
            self._error = str(e)
            _log(f"Requirements analyzer not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Analyze requirements for quality issues."""
        if not self._available:
            return []

        issues = []
        full_text = kwargs.get('full_text', '')

        # Analyze the full document
        result = self._analyzer.analyze_document(full_text)

        # Convert atomicity issues
        for atom_issue in result.atomicity_issues:
            para_idx = self._find_paragraph(paragraphs, atom_issue.text)
            issues.append({
                'type': 'atomicity',
                'category': 'requirements',
                'severity': 'medium',
                'message': f"Non-atomic requirement: contains {atom_issue.shall_count} 'shall' statements",
                'paragraph': para_idx,
                'text': atom_issue.text[:200] + "..." if len(atom_issue.text) > 200 else atom_issue.text,
                'suggestion': "Split into separate requirements, one 'shall' per requirement",
                'source': 'requirements_analyzer_v3.3.0'
            })

        # Convert testability issues
        for test_issue in result.testability_issues:
            para_idx = self._find_paragraph(paragraphs, test_issue.text)
            issues.append({
                'type': 'testability',
                'category': 'requirements',
                'severity': 'medium',
                'message': f"Testability concern: {test_issue.reason}",
                'paragraph': para_idx,
                'text': test_issue.text[:200] + "..." if len(test_issue.text) > 200 else test_issue.text,
                'suggestion': "Add measurable criteria or specific values",
                'source': 'requirements_analyzer_v3.3.0'
            })

        # Convert escape clause issues
        for escape in result.escape_clauses:
            para_idx = self._find_paragraph(paragraphs, escape.text)
            issues.append({
                'type': 'escape_clause',
                'category': 'requirements',
                'severity': 'high',
                'message': f"Escape clause found: '{escape.clause}'",
                'paragraph': para_idx,
                'text': escape.text[:200] + "..." if len(escape.text) > 200 else escape.text,
                'suggestion': f"Replace '{escape.clause}' with specific value or remove",
                'source': 'requirements_analyzer_v3.3.0'
            })

        # Convert ambiguous term issues
        for ambig in result.ambiguous_terms:
            para_idx = self._find_paragraph(paragraphs, ambig.text)
            issues.append({
                'type': 'ambiguous_term',
                'category': 'requirements',
                'severity': 'low',
                'message': f"Ambiguous term: '{ambig.term}'",
                'paragraph': para_idx,
                'text': ambig.text[:200] + "..." if len(ambig.text) > 200 else ambig.text,
                'suggestion': ambig.suggestion or f"Replace '{ambig.term}' with specific criteria",
                'source': 'requirements_analyzer_v3.3.0'
            })

        return issues

    def _find_paragraph(self, paragraphs: List[Tuple[int, str]], text: str) -> int:
        """Find paragraph index containing text."""
        text_lower = text.lower()[:100]
        for idx, para_text in paragraphs:
            if text_lower in para_text.lower():
                return idx
        return 0


# =============================================================================
# TERMINOLOGY CHECKER
# =============================================================================

class TerminologyConsistencyChecker(BaseEnhancedChecker):
    """
    Terminology consistency checking.
    Detects spelling variants, British/American differences, abbreviations.
    """

    CHECKER_NAME = "Terminology Consistency"

    def __init__(self):
        super().__init__()
        try:
            from terminology_checker import (
                get_terminology_checker,
                check_terminology as _check_term
            )
            self._checker = get_terminology_checker()
            self._check_func = _check_term
            self._available = self._checker is not None
            if self._available:
                _log(f"Terminology checker loaded (v3.3.0)")
        except ImportError as e:
            self._error = str(e)
            _log(f"Terminology checker not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check for terminology inconsistencies."""
        if not self._available:
            return []

        issues = []
        full_text = kwargs.get('full_text', '')

        result = self._checker.check_text(full_text)

        for inconsistency in result:
            # Find a paragraph containing one of the variants
            para_idx = 0
            sample_text = ""
            variants = inconsistency.variants_found if hasattr(inconsistency, 'variants_found') else getattr(inconsistency, 'variants', [])
            for idx, text in paragraphs:
                for variant in variants:
                    if variant.lower() in text.lower():
                        para_idx = idx
                        sample_text = text[:150]
                        break
                if para_idx:
                    break

            variants_str = ", ".join(f"'{v}'" for v in variants[:3])

            issue = {
                'type': 'terminology_inconsistency',
                'category': 'consistency',
                'severity': 'low',
                'message': f"Inconsistent terminology: {variants_str} ({inconsistency.issue_type})",
                'paragraph': para_idx,
                'text': sample_text,
                'suggestion': inconsistency.suggestion if hasattr(inconsistency, 'suggestion') else "Standardize on one form throughout the document",
                'details': {
                    'variants': variants,
                    'occurrences': inconsistency.occurrences if hasattr(inconsistency, 'occurrences') else {},
                    'issue_type': inconsistency.issue_type
                },
                'source': 'terminology_checker_v3.3.0'
            }
            issues.append(issue)

        return issues


# =============================================================================
# CROSS-REFERENCE VALIDATOR
# =============================================================================

class CrossReferenceChecker(BaseEnhancedChecker):
    """
    Document cross-reference validation.
    Validates section, table, figure, and requirement references.
    """

    CHECKER_NAME = "Cross-Reference Validation"

    def __init__(self):
        super().__init__()
        try:
            from cross_reference_validator import (
                get_cross_reference_validator,
                validate_cross_references as _validate_refs
            )
            self._validator = get_cross_reference_validator()
            self._validate_func = _validate_refs
            self._available = self._validator is not None
            if self._available:
                _log(f"Cross-reference validator loaded (v3.3.0)")
        except ImportError as e:
            self._error = str(e)
            _log(f"Cross-reference validator not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Validate cross-references in document."""
        if not self._available:
            return []

        issues = []
        full_text = kwargs.get('full_text', '')
        headings = kwargs.get('headings', [])
        tables = kwargs.get('tables', [])
        figures = kwargs.get('figures', [])

        ref_issues, statistics = self._validator.validate_text(full_text)

        # Process all reference issues from the flat list
        for ref_issue in ref_issues:
            para_idx = self._find_paragraph(paragraphs, ref_issue.context)

            if ref_issue.issue_type == 'broken':
                issues.append({
                    'type': 'broken_reference',
                    'category': 'references',
                    'severity': 'high',
                    'message': f"Broken reference: '{ref_issue.reference_text}' ({ref_issue.reference_type})",
                    'paragraph': para_idx,
                    'text': ref_issue.context[:150] if ref_issue.context else "",
                    'suggestion': ref_issue.suggestion or f"Verify that {ref_issue.reference_type} '{ref_issue.reference_text}' exists",
                    'source': 'cross_reference_v3.3.0'
                })
            elif ref_issue.issue_type == 'unreferenced':
                issues.append({
                    'type': 'unreferenced_item',
                    'category': 'references',
                    'severity': 'low',
                    'message': f"Unreferenced {ref_issue.reference_type}: '{ref_issue.reference_text}'",
                    'paragraph': para_idx,
                    'text': ref_issue.context[:150] if ref_issue.context else "",
                    'suggestion': ref_issue.suggestion or f"Add reference to {ref_issue.reference_type} or remove if not needed",
                    'source': 'cross_reference_v3.3.0'
                })
            elif ref_issue.issue_type == 'format_inconsistent':
                issues.append({
                    'type': 'reference_format',
                    'category': 'consistency',
                    'severity': 'low',
                    'message': f"Reference format inconsistency: {ref_issue.suggestion}",
                    'paragraph': para_idx,
                    'text': ref_issue.context[:150] if ref_issue.context else "",
                    'suggestion': ref_issue.suggestion or "Use consistent reference format",
                    'source': 'cross_reference_v3.3.0'
                })

        return issues

    def _find_paragraph(self, paragraphs: List[Tuple[int, str]], text: str) -> int:
        """Find paragraph index containing text."""
        if not text:
            return 0
        text_lower = text.lower()[:50]
        for idx, para_text in paragraphs:
            if text_lower in para_text.lower():
                return idx
        return 0


# =============================================================================
# TECHNICAL DICTIONARY INTEGRATION
# =============================================================================

class TechnicalDictionaryChecker(BaseEnhancedChecker):
    """
    Technical dictionary integration for spelling validation.
    Uses 10,000+ aerospace/defense terms.
    """

    CHECKER_NAME = "Technical Dictionary"

    def __init__(self):
        super().__init__()
        try:
            from technical_dictionary import get_technical_dictionary
            self._dict = get_technical_dictionary()
            self._available = self._dict is not None
            if self._available:
                stats = self._dict.get_stats()
                _log(f"Technical dictionary loaded: {stats.total_terms} terms")
        except ImportError as e:
            self._error = str(e)
            _log(f"Technical dictionary not available: {e}", level='debug')

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check for technical term corrections."""
        if not self._available:
            return []

        issues = []

        for para_idx, text in paragraphs:
            if not text or len(text.strip()) < 5:
                continue

            # Check each word for corrections
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
            for word in words:
                correction = self._dict.get_correction(word)
                if correction and correction.lower() != word.lower():
                    issues.append({
                        'type': 'technical_spelling',
                        'category': 'spelling',
                        'severity': 'low',
                        'message': f"Technical term correction: '{word}' → '{correction}'",
                        'paragraph': para_idx,
                        'text': text[:150],
                        'suggestion': f"Consider using '{correction}'",
                        'source': 'technical_dictionary_v3.3.0'
                    })

        return issues

    def is_valid_term(self, term: str) -> bool:
        """Check if a term is in the technical dictionary."""
        if not self._available:
            return False
        return self._dict.is_valid_term(term)

    def get_acronym_expansion(self, acronym: str) -> Optional[Dict]:
        """Get expansion for an acronym."""
        if not self._available:
            return None
        return self._dict.get_acronym_expansion(acronym)


# =============================================================================
# ADAPTIVE LEARNING INTEGRATION
# =============================================================================

class AdaptiveLearningIntegration:
    """
    Integrates adaptive learning into the review pipeline.
    Boosts confidence based on user decisions.
    """

    def __init__(self):
        self._available = False
        self._learner = None
        try:
            from adaptive_learner import get_adaptive_learner
            self._learner = get_adaptive_learner()
            self._available = self._learner is not None
            if self._available:
                stats = self._learner.get_statistics()
                _log(f"Adaptive learner loaded: {stats.total_decisions} decisions")
        except ImportError as e:
            _log(f"Adaptive learner not available: {e}", level='debug')

    @property
    def is_available(self) -> bool:
        return self._available

    def get_role_confidence_boost(self, role_name: str, context: str = "") -> float:
        """Get confidence boost for a role based on learning history."""
        if not self._available:
            return 0.0
        return self._learner.get_role_confidence_boost(role_name, context)

    def record_role_decision(self, role_name: str, decision: str, context: str = ""):
        """Record a role adjudication decision."""
        if not self._available:
            return
        from adaptive_learner import role_pattern_key
        pattern_key = role_pattern_key(role_name)
        self._learner.record_decision(
            pattern_key=pattern_key,
            decision=decision,
            category='role',
            context=context
        )

    def is_known_valid_role(self, role_name: str) -> bool:
        """Check if role has been consistently accepted."""
        if not self._available:
            return False
        return self._learner.is_known_valid_role(role_name)

    def is_known_invalid_role(self, role_name: str) -> bool:
        """Check if role has been consistently rejected."""
        if not self._available:
            return False
        return self._learner.is_known_invalid_role(role_name)


# =============================================================================
# ENHANCED NLP PROCESSOR INTEGRATION
# =============================================================================

class EnhancedNLPIntegration:
    """
    Integrates enhanced NLP processor for role/acronym extraction.
    Uses EntityRuler, PhraseMatcher, and transformer models.
    """

    def __init__(self):
        self._available = False
        self._processor = None
        try:
            from nlp_enhanced import get_enhanced_nlp_processor
            self._processor = get_enhanced_nlp_processor()
            self._available = self._processor is not None
            if self._available:
                _log(f"Enhanced NLP processor loaded (model: {self._processor.model_name})")
        except ImportError as e:
            _log(f"Enhanced NLP processor not available: {e}", level='debug')

    @property
    def is_available(self) -> bool:
        return self._available

    def extract_roles(self, text: str) -> List[Dict]:
        """Extract roles using enhanced NLP."""
        if not self._available:
            return []

        roles = self._processor.extract_roles(text)
        return [
            {
                'name': r.name,
                'confidence': r.confidence,
                'source': r.source,
                'context': r.context,
                'modifiers': r.modifiers
            }
            for r in roles
        ]

    def extract_acronyms(self, text: str) -> List[Dict]:
        """Extract acronyms using enhanced NLP."""
        if not self._available:
            return []

        acronyms = self._processor.extract_acronyms(text)
        return [
            {
                'acronym': a.acronym,
                'expansion': a.expansion,
                'confidence': a.confidence,
                'definition_location': a.definition_location,
                'usage_count': a.usage_count
            }
            for a in acronyms
        ]

    def analyze_document(self, text: str) -> Optional[Dict]:
        """Perform full document analysis."""
        if not self._available:
            return None

        analysis = self._processor.analyze_document(text)
        return {
            'roles': [r.__dict__ for r in analysis.roles],
            'acronyms': [a.__dict__ for a in analysis.acronyms],
            'requirements': analysis.requirements,
            'passive_voice_sentences': analysis.passive_voice_sentences,
            'ambiguous_terms': analysis.ambiguous_terms
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_v330_checkers() -> Dict[str, BaseEnhancedChecker]:
    """
    Get all v3.3.0 enhanced checkers.

    Returns:
        Dictionary of checker_name -> checker instance
    """
    checkers = {}

    # Enhanced passive voice
    pv_checker = EnhancedPassiveVoiceChecker()
    if pv_checker.is_available:
        checkers['enhanced_passive_voice'] = pv_checker

    # Sentence fragments
    frag_checker = SentenceFragmentChecker()
    if frag_checker.is_available:
        checkers['sentence_fragments_v2'] = frag_checker

    # Requirements analyzer
    req_checker = RequirementsAnalyzerChecker()
    if req_checker.is_available:
        checkers['requirements_analysis'] = req_checker

    # Terminology consistency
    term_checker = TerminologyConsistencyChecker()
    if term_checker.is_available:
        checkers['terminology_consistency'] = term_checker

    # Cross-reference validation
    xref_checker = CrossReferenceChecker()
    if xref_checker.is_available:
        checkers['cross_references'] = xref_checker

    # Technical dictionary
    dict_checker = TechnicalDictionaryChecker()
    if dict_checker.is_available:
        checkers['technical_dictionary'] = dict_checker

    _log(f"Loaded {len(checkers)} v3.3.0 enhanced checkers")
    return checkers


def get_adaptive_learner_integration() -> AdaptiveLearningIntegration:
    """Get adaptive learning integration instance."""
    return AdaptiveLearningIntegration()


def get_enhanced_nlp_integration() -> EnhancedNLPIntegration:
    """Get enhanced NLP integration instance."""
    return EnhancedNLPIntegration()


# =============================================================================
# STATUS AND INFO
# =============================================================================

def get_v330_status() -> Dict[str, Any]:
    """
    Get status of all v3.3.0 components.

    Returns:
        Dictionary with component availability and stats
    """
    # Get version from centralized config
    try:
        from config_logging import VERSION
        version = VERSION
    except ImportError:
        version = '4.0.0'

    status = {
        'version': version,
        'components': {}
    }

    # Check each component
    components = [
        ('technical_dictionary', 'technical_dictionary', 'get_technical_dictionary'),
        ('adaptive_learner', 'adaptive_learner', 'get_adaptive_learner'),
        ('enhanced_nlp', 'nlp_enhanced', 'get_enhanced_nlp_processor'),
        ('passive_checker', 'enhanced_passive_checker', 'get_passive_checker'),
        ('fragment_checker', 'fragment_checker', 'get_fragment_checker'),
        ('requirements_analyzer', 'requirements_analyzer', 'get_requirements_analyzer'),
        ('terminology_checker', 'terminology_checker', 'get_terminology_checker'),
        ('cross_reference_validator', 'cross_reference_validator', 'get_cross_reference_validator'),
    ]

    for name, module_name, factory_func in components:
        try:
            module = __import__(module_name)
            factory = getattr(module, factory_func)
            instance = factory()
            status['components'][name] = {
                'available': instance is not None,
                'module': module_name
            }

            # Get stats if available
            if hasattr(instance, 'get_stats'):
                status['components'][name]['stats'] = instance.get_stats()
        except Exception as e:
            status['components'][name] = {
                'available': False,
                'error': str(e)
            }

    # Summary
    available_count = sum(1 for c in status['components'].values() if c.get('available'))
    status['summary'] = {
        'available': available_count,
        'total': len(components),
        'percentage': round(available_count / len(components) * 100, 1)
    }

    return status


# Module initialization log
_log("NLP Integration module loaded (v3.3.0)")
