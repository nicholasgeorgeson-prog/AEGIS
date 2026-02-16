"""
PassivePy Integration Module v1.0.0
===================================
Date: 2026-02-04

Integrates PassivePy library for enhanced passive voice detection.
PassivePy uses spaCy's dependency parsing with specialized passive detection rules.

This module:
- Provides PassivePy-based passive voice detection
- Compares results with existing checker for validation
- Offers a combined high-accuracy mode

Author: AEGIS NLP Enhancement Project
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VERSION = '1.0.0'

# Check if PassivePy is available
PASSIVEPY_AVAILABLE = False
try:
    # PassivePy installs as PassivePySrc, not passivepy
    from PassivePySrc import PassivePy
    PASSIVEPY_AVAILABLE = True
except ImportError:
    try:
        # Try alternate import
        from passivepy import PassivePy
        PASSIVEPY_AVAILABLE = True
    except ImportError:
        logger.warning("PassivePy not installed. Install with: pip install passivepy")


@dataclass
class PassiveDetection:
    """Represents a passive voice detection result."""
    sentence: str
    passive_match: str
    raw_passive_count: int
    binary_passive: bool  # True if sentence contains passive
    confidence: float
    source: str  # 'passivepy', 'spacy', or 'combined'


class PassivePyChecker:
    """
    Passive voice checker using PassivePy library.

    PassivePy uses dependency parsing rules specifically designed for
    passive voice detection, providing high accuracy (90%+).
    """

    VERSION = VERSION

    def __init__(self, spacy_model: str = 'en_core_web_sm'):
        """
        Initialize the PassivePy checker.

        Args:
            spacy_model: spaCy model to use (default: en_core_web_sm)
        """
        self.passivepy = None
        self.nlp = None
        self.spacy_model = spacy_model
        self._initialize()

    def _initialize(self):
        """Initialize PassivePy and spaCy."""
        if not PASSIVEPY_AVAILABLE:
            logger.warning("PassivePy not available - using fallback")
            return

        try:
            import spacy
            # Try models in order of preference
            models_to_try = [self.spacy_model, 'en_core_web_md', 'en_core_web_lg', 'en_core_web_sm']
            for model in models_to_try:
                try:
                    self.nlp = spacy.load(model)
                    self.spacy_model = model
                    break
                except OSError:
                    continue
            else:
                raise RuntimeError("No spaCy model available")

            # PassivePy uses PassivePyAnalyzer class
            self.passivepy = PassivePy.PassivePyAnalyzer(self.nlp)
            logger.info(f"PassivePy initialized with {self.spacy_model}")
        except Exception as e:
            logger.error(f"Failed to initialize PassivePy: {e}")
            self.passivepy = None

    @property
    def is_available(self) -> bool:
        """Check if PassivePy is available and initialized."""
        return self.passivepy is not None

    def detect_passive(self, text: str) -> List[PassiveDetection]:
        """
        Detect passive voice in text using PassivePy.

        Args:
            text: Text to analyze

        Returns:
            List of PassiveDetection objects
        """
        if not self.is_available:
            return self._fallback_detection(text)

        results = []

        try:
            import re
            # Split into sentences for better accuracy
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

            for sentence in sentences:
                # Use PassivePy's match_text method on each sentence
                df = self.passivepy.match_text(sentence, full_passive=True, truncated_passive=True)

                if df is not None and not df.empty:
                    row = df.iloc[0]
                    # Check for passive indicators
                    binary_full = row.get('binary', 0) or row.get('binary_passive', 0) or row.get('binary_full_passive', 0)
                    binary_truncated = row.get('binary_truncated_passive', 0)
                    passive_match = row.get('passive_match', '') or row.get('full_passive_match', '')
                    raw_count = row.get('raw_passive_count', 0) or row.get('raw_full_passive_count', 0)

                    # Consider it passive if either full or truncated passive is detected
                    if binary_full or binary_truncated or raw_count > 0:
                        results.append(PassiveDetection(
                            sentence=sentence,
                            passive_match=passive_match if passive_match else 'passive detected',
                            raw_passive_count=max(1, raw_count),
                            binary_passive=True,
                            confidence=0.90,  # PassivePy has ~90% accuracy
                            source='passivepy'
                        ))

        except Exception as e:
            logger.error(f"PassivePy detection error: {e}")
            return self._fallback_detection(text)

        return results

    def detect_passive_sentences(self, sentences: List[str]) -> List[PassiveDetection]:
        """
        Detect passive voice in a list of sentences.

        Args:
            sentences: List of sentences to analyze

        Returns:
            List of PassiveDetection objects
        """
        if not self.is_available:
            return [d for s in sentences for d in self._fallback_detection(s)]

        results = []

        try:
            # Process each sentence
            for sentence in sentences:
                detections = self.detect_passive(sentence)
                results.extend(detections)
        except Exception as e:
            logger.error(f"Batch detection error: {e}")

        return results

    def _fallback_detection(self, text: str) -> List[PassiveDetection]:
        """Fallback passive detection when PassivePy is unavailable."""
        import re

        results = []

        # Comprehensive passive patterns including modals
        passive_patterns = [
            # Basic be + past participle
            r'\b(is|are|was|were|be|been|being)\s+(\w+ed)\b',
            r'\b(is|are|was|were|be|been|being)\s+(\w+en)\b',
            # Modal + be + past participle (should be applied, will be met, etc.)
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+(\w+ed)\b',
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+(\w+en)\b',
            # Get passives
            r'\b(get|gets|got|gotten)\s+(\w+ed)\b',
            # Being + past participle (being offered, being used)
            r'\b(being)\s+(\w+ed)\b',
            # Irregular past participles
            r'\b(is|are|was|were|be|been)\s+(made|done|given|taken|put|met|set|held|built|found|known|shown|told|sent|brought|thought|sought|taught|caught|bought|fought|wrought)\b',
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+(made|done|given|taken|put|met|set|held|built|found|known|shown|told|sent|brought|thought|sought|taught|caught|bought|fought|wrought)\b',
        ]

        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            for pattern in passive_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    results.append(PassiveDetection(
                        sentence=sentence.strip(),
                        passive_match=match.group(0),
                        raw_passive_count=1,
                        binary_passive=True,
                        confidence=0.75,  # Improved confidence with better patterns
                        source='fallback'
                    ))
                    break  # Only one detection per sentence

        return results

    def get_passive_ratio(self, text: str) -> Dict[str, Any]:
        """
        Calculate the passive voice ratio in text.

        Args:
            text: Text to analyze

        Returns:
            Dict with total_sentences, passive_sentences, and ratio
        """
        import re

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        total = len(sentences)

        if total == 0:
            return {
                'total_sentences': 0,
                'passive_sentences': 0,
                'ratio': 0.0,
                'passive_percentage': 0.0
            }

        detections = self.detect_passive(text)
        passive_sentences = set(d.sentence for d in detections)
        passive_count = len(passive_sentences)

        return {
            'total_sentences': total,
            'passive_sentences': passive_count,
            'ratio': passive_count / total if total > 0 else 0.0,
            'passive_percentage': (passive_count / total * 100) if total > 0 else 0.0
        }


class CombinedPassiveChecker:
    """
    Combined passive voice checker that uses both PassivePy and
    the existing enhanced checker for maximum accuracy.
    """

    def __init__(self):
        """Initialize combined checker."""
        self.passivepy_checker = PassivePyChecker()
        self.enhanced_checker = None

        # Try to load enhanced checker
        try:
            from enhanced_passive_checker import EnhancedPassiveChecker
            self.enhanced_checker = EnhancedPassiveChecker()
        except ImportError:
            logger.warning("Enhanced passive checker not available")

    def detect_passive(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect passive voice using both checkers and combine results.

        Args:
            text: Text to analyze

        Returns:
            List of combined detection results
        """
        results = []

        # Get PassivePy results
        passivepy_results = []
        if self.passivepy_checker.is_available:
            passivepy_results = self.passivepy_checker.detect_passive(text)

        # Get enhanced checker results
        enhanced_results = []
        if self.enhanced_checker:
            enhanced_results = self.enhanced_checker.check_text(text)

        # Combine results
        seen_sentences = set()

        # First add PassivePy results (higher base accuracy)
        for detection in passivepy_results:
            if detection.sentence not in seen_sentences:
                seen_sentences.add(detection.sentence)

                # Check if enhanced checker agrees
                enhanced_agrees = any(
                    e.sentence == detection.sentence
                    for e in enhanced_results
                    if not e.is_false_positive
                )

                # Boost confidence if both agree
                confidence = detection.confidence
                if enhanced_agrees:
                    confidence = min(0.98, confidence + 0.08)

                results.append({
                    'sentence': detection.sentence,
                    'passive_match': detection.passive_match,
                    'confidence': confidence,
                    'source': 'combined' if enhanced_agrees else 'passivepy',
                    'both_checkers_agree': enhanced_agrees
                })

        # Add any enhanced results not found by PassivePy
        for enhanced in enhanced_results:
            if not enhanced.is_false_positive and enhanced.sentence not in seen_sentences:
                seen_sentences.add(enhanced.sentence)
                results.append({
                    'sentence': enhanced.sentence,
                    'passive_match': enhanced.passive_verb,
                    'confidence': enhanced.confidence * 0.95,  # Slight reduction since PassivePy missed it
                    'source': 'enhanced_only',
                    'both_checkers_agree': False,
                    'suggestion': enhanced.suggestion
                })

        return results

    def get_statistics(self, text: str) -> Dict[str, Any]:
        """Get detailed statistics about passive voice in text."""
        import re

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        detections = self.detect_passive(text)

        agreed = [d for d in detections if d.get('both_checkers_agree', False)]
        passivepy_only = [d for d in detections if d.get('source') == 'passivepy']
        enhanced_only = [d for d in detections if d.get('source') == 'enhanced_only']

        return {
            'total_sentences': len(sentences),
            'passive_sentences': len(detections),
            'passive_percentage': (len(detections) / len(sentences) * 100) if sentences else 0,
            'both_checkers_agreed': len(agreed),
            'passivepy_only': len(passivepy_only),
            'enhanced_only': len(enhanced_only),
            'average_confidence': sum(d['confidence'] for d in detections) / len(detections) if detections else 0
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_passivepy_instance: Optional[PassivePyChecker] = None
_combined_instance: Optional[CombinedPassiveChecker] = None


def get_passivepy_checker() -> PassivePyChecker:
    """Get or create singleton PassivePy checker."""
    global _passivepy_instance
    if _passivepy_instance is None:
        _passivepy_instance = PassivePyChecker()
    return _passivepy_instance


def get_combined_checker() -> CombinedPassiveChecker:
    """Get or create singleton combined checker."""
    global _combined_instance
    if _combined_instance is None:
        _combined_instance = CombinedPassiveChecker()
    return _combined_instance


def check_passive_voice(text: str, use_combined: bool = True) -> List[Dict[str, Any]]:
    """
    Check text for passive voice.

    Args:
        text: Text to analyze
        use_combined: Use combined checker for best accuracy (default: True)

    Returns:
        List of passive voice detections
    """
    if use_combined:
        checker = get_combined_checker()
        return checker.detect_passive(text)
    else:
        checker = get_passivepy_checker()
        detections = checker.detect_passive(text)
        return [{
            'sentence': d.sentence,
            'passive_match': d.passive_match,
            'confidence': d.confidence,
            'source': d.source
        } for d in detections]


def is_passivepy_available() -> bool:
    """Check if PassivePy is installed and working."""
    return PASSIVEPY_AVAILABLE and get_passivepy_checker().is_available


__all__ = [
    'PassivePyChecker',
    'CombinedPassiveChecker',
    'PassiveDetection',
    'get_passivepy_checker',
    'get_combined_checker',
    'check_passive_voice',
    'is_passivepy_available',
    'VERSION'
]
