"""
Enhanced Readability Metrics v1.0.0
===================================
Date: 2026-02-04

Comprehensive readability analysis using py-readability-metrics
and additional custom metrics for technical documentation.

Features:
- 10+ readability formulas (Flesch-Kincaid, SMOG, Gunning Fog, etc.)
- Technical documentation specific metrics
- Sentence complexity analysis
- Grade level recommendations

Author: AEGIS NLP Enhancement Project
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VERSION = '1.0.0'

# Check if py-readability-metrics is available
PY_READABILITY_AVAILABLE = False
try:
    from readability import Readability
    PY_READABILITY_AVAILABLE = True
except ImportError:
    logger.warning("py-readability-metrics not installed. Install with: pip install py-readability-metrics")

# Fallback textstat
TEXTSTAT_AVAILABLE = False
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    pass


@dataclass
class ReadabilityScore:
    """Comprehensive readability score."""
    # Core metrics
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float
    coleman_liau: float
    automated_readability_index: float
    linsear_write: float
    dale_chall: float

    # Summary metrics
    average_grade_level: float
    recommended_audience: str

    # Text statistics
    word_count: int
    sentence_count: int
    syllable_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float

    # Technical documentation metrics
    technical_complexity: float
    sentence_variety: float

    # Source
    source: str


class EnhancedReadabilityChecker:
    """
    Enhanced readability checker with multiple metrics.

    Provides comprehensive readability analysis specifically
    tuned for technical documentation.
    """

    VERSION = VERSION

    # Target ranges for technical documentation
    TECH_DOC_TARGETS = {
        'flesch_reading_ease': (30, 50),  # Technical content is harder
        'flesch_kincaid_grade': (10, 14),  # College level
        'gunning_fog': (12, 16),
        'smog_index': (12, 16),
        'avg_words_per_sentence': (15, 25),
        'avg_syllables_per_word': (1.5, 2.0),
    }

    # Grade level to audience mapping
    AUDIENCE_MAP = {
        (0, 6): "Elementary school",
        (6, 9): "Middle school",
        (9, 12): "High school",
        (12, 16): "College/University",
        (16, 20): "Graduate level",
        (20, 100): "Professional/Expert"
    }

    def __init__(self):
        """Initialize the enhanced readability checker."""
        self.readability = None
        if PY_READABILITY_AVAILABLE:
            # py-readability-metrics doesn't need initialization
            pass

    def analyze(self, text: str) -> ReadabilityScore:
        """
        Perform comprehensive readability analysis.

        Args:
            text: Text to analyze

        Returns:
            ReadabilityScore with all metrics
        """
        # Clean text
        text = self._clean_text(text)

        if PY_READABILITY_AVAILABLE:
            return self._analyze_with_py_readability(text)
        elif TEXTSTAT_AVAILABLE:
            return self._analyze_with_textstat(text)
        else:
            return self._analyze_fallback(text)

    def _clean_text(self, text: str) -> str:
        """Clean text for analysis."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might confuse analysis
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
        return text.strip()

    def _analyze_with_py_readability(self, text: str) -> ReadabilityScore:
        """Analyze using py-readability-metrics."""
        try:
            r = Readability(text)

            # Get all metrics
            flesch = r.flesch()
            flesch_kincaid = r.flesch_kincaid()
            gunning_fog = r.gunning_fog()
            smog = r.smog()
            coleman_liau = r.coleman_liau()
            ari = r.ari()
            linsear = r.linsear_write()
            dale_chall = r.dale_chall()

            # Extract values (py-readability-metrics returns objects)
            fre = flesch.score if hasattr(flesch, 'score') else float(flesch)
            fkg = flesch_kincaid.score if hasattr(flesch_kincaid, 'score') else float(flesch_kincaid)
            gf = gunning_fog.score if hasattr(gunning_fog, 'score') else float(gunning_fog)
            smog_val = smog.score if hasattr(smog, 'score') else float(smog)
            cl = coleman_liau.score if hasattr(coleman_liau, 'score') else float(coleman_liau)
            ari_val = ari.score if hasattr(ari, 'score') else float(ari)
            lw = linsear.score if hasattr(linsear, 'score') else float(linsear)
            dc = dale_chall.score if hasattr(dale_chall, 'score') else float(dale_chall)

            # Calculate statistics
            stats = self._calculate_statistics(text)

            # Calculate average grade level
            grade_levels = [fkg, gf, smog_val, cl, ari_val]
            avg_grade = sum(grade_levels) / len(grade_levels)

            # Determine audience
            audience = self._determine_audience(avg_grade)

            # Technical complexity
            tech_complexity = self._calculate_technical_complexity(text)

            # Sentence variety
            sentence_variety = self._calculate_sentence_variety(text)

            return ReadabilityScore(
                flesch_reading_ease=round(fre, 2),
                flesch_kincaid_grade=round(fkg, 2),
                gunning_fog=round(gf, 2),
                smog_index=round(smog_val, 2),
                coleman_liau=round(cl, 2),
                automated_readability_index=round(ari_val, 2),
                linsear_write=round(lw, 2),
                dale_chall=round(dc, 2),
                average_grade_level=round(avg_grade, 2),
                recommended_audience=audience,
                word_count=stats['word_count'],
                sentence_count=stats['sentence_count'],
                syllable_count=stats['syllable_count'],
                avg_words_per_sentence=round(stats['avg_words_per_sentence'], 2),
                avg_syllables_per_word=round(stats['avg_syllables_per_word'], 2),
                technical_complexity=round(tech_complexity, 2),
                sentence_variety=round(sentence_variety, 2),
                source='py-readability-metrics'
            )

        except Exception as e:
            logger.error(f"py-readability-metrics analysis failed: {e}")
            if TEXTSTAT_AVAILABLE:
                return self._analyze_with_textstat(text)
            return self._analyze_fallback(text)

    def _analyze_with_textstat(self, text: str) -> ReadabilityScore:
        """Analyze using textstat (fallback)."""
        stats = self._calculate_statistics(text)

        fre = textstat.flesch_reading_ease(text)
        fkg = textstat.flesch_kincaid_grade(text)
        gf = textstat.gunning_fog(text)
        smog_val = textstat.smog_index(text)
        cl = textstat.coleman_liau_index(text)
        ari = textstat.automated_readability_index(text)
        lw = textstat.linsear_write_formula(text)
        dc = textstat.dale_chall_readability_score(text)

        grade_levels = [fkg, gf, smog_val, cl, ari]
        avg_grade = sum(grade_levels) / len(grade_levels)

        return ReadabilityScore(
            flesch_reading_ease=round(fre, 2),
            flesch_kincaid_grade=round(fkg, 2),
            gunning_fog=round(gf, 2),
            smog_index=round(smog_val, 2),
            coleman_liau=round(cl, 2),
            automated_readability_index=round(ari, 2),
            linsear_write=round(lw, 2),
            dale_chall=round(dc, 2),
            average_grade_level=round(avg_grade, 2),
            recommended_audience=self._determine_audience(avg_grade),
            word_count=stats['word_count'],
            sentence_count=stats['sentence_count'],
            syllable_count=stats['syllable_count'],
            avg_words_per_sentence=round(stats['avg_words_per_sentence'], 2),
            avg_syllables_per_word=round(stats['avg_syllables_per_word'], 2),
            technical_complexity=round(self._calculate_technical_complexity(text), 2),
            sentence_variety=round(self._calculate_sentence_variety(text), 2),
            source='textstat'
        )

    def _analyze_fallback(self, text: str) -> ReadabilityScore:
        """Basic fallback analysis without external libraries."""
        stats = self._calculate_statistics(text)

        # Simplified Flesch Reading Ease
        # 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        if stats['word_count'] > 0 and stats['sentence_count'] > 0:
            fre = 206.835 - 1.015 * stats['avg_words_per_sentence'] - 84.6 * stats['avg_syllables_per_word']
            fkg = 0.39 * stats['avg_words_per_sentence'] + 11.8 * stats['avg_syllables_per_word'] - 15.59
        else:
            fre = 0
            fkg = 0

        return ReadabilityScore(
            flesch_reading_ease=round(fre, 2),
            flesch_kincaid_grade=round(fkg, 2),
            gunning_fog=round(fkg * 1.1, 2),  # Approximation
            smog_index=round(fkg * 1.05, 2),
            coleman_liau=round(fkg * 0.95, 2),
            automated_readability_index=round(fkg, 2),
            linsear_write=round(fkg * 0.9, 2),
            dale_chall=round(fkg * 0.85, 2),
            average_grade_level=round(fkg, 2),
            recommended_audience=self._determine_audience(fkg),
            word_count=stats['word_count'],
            sentence_count=stats['sentence_count'],
            syllable_count=stats['syllable_count'],
            avg_words_per_sentence=round(stats['avg_words_per_sentence'], 2),
            avg_syllables_per_word=round(stats['avg_syllables_per_word'], 2),
            technical_complexity=round(self._calculate_technical_complexity(text), 2),
            sentence_variety=round(self._calculate_sentence_variety(text), 2),
            source='fallback'
        )

    def _calculate_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate basic text statistics."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        word_count = len(words)
        sentence_count = max(1, len(sentences))
        syllable_count = sum(self._count_syllables(word) for word in words)

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'syllable_count': syllable_count,
            'avg_words_per_sentence': word_count / sentence_count if sentence_count > 0 else 0,
            'avg_syllables_per_word': syllable_count / word_count if word_count > 0 else 0
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower().strip()
        if not word:
            return 0

        # Simple syllable counting
        vowels = 'aeiouy'
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1

        return max(1, count)

    def _determine_audience(self, grade_level: float) -> str:
        """Determine recommended audience based on grade level."""
        for (min_grade, max_grade), audience in self.AUDIENCE_MAP.items():
            if min_grade <= grade_level < max_grade:
                return audience
        return "Professional/Expert"

    def _calculate_technical_complexity(self, text: str) -> float:
        """
        Calculate technical complexity score (0-100).

        Based on:
        - Acronym density
        - Technical term frequency
        - Numeric content ratio
        """
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0

        # Acronym count (2-5 capital letters)
        acronyms = len(re.findall(r'\b[A-Z]{2,5}\b', text))

        # Numbers and measurements
        numbers = len(re.findall(r'\b\d+\.?\d*\b', text))

        # Technical patterns (units, equations)
        tech_patterns = len(re.findall(r'\b(?:mm|cm|m|km|kg|lb|Hz|MHz|GHz|V|A|W|dB)\b', text, re.IGNORECASE))

        # Calculate complexity
        acronym_ratio = acronyms / word_count * 100
        number_ratio = numbers / word_count * 100
        tech_ratio = tech_patterns / word_count * 100

        complexity = min(100, acronym_ratio * 5 + number_ratio * 3 + tech_ratio * 10)

        return complexity

    def _calculate_sentence_variety(self, text: str) -> float:
        """
        Calculate sentence variety score (0-100).

        Higher scores indicate more varied sentence structure.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 2:
            return 50.0  # Neutral score for short text

        # Calculate sentence length variance
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # Calculate sentence starter variety
        starters = [s.split()[0].lower() if s.split() else '' for s in sentences]
        unique_starters = len(set(starters))
        starter_variety = unique_starters / len(sentences) * 100

        # Combine metrics
        length_variety = min(50, variance)  # Cap at 50
        variety_score = (length_variety + starter_variety) / 2

        return variety_score

    def get_recommendations(self, score: ReadabilityScore) -> List[str]:
        """
        Get recommendations based on readability analysis.

        Args:
            score: ReadabilityScore from analysis

        Returns:
            List of improvement recommendations
        """
        recommendations = []

        # Check Flesch-Kincaid grade
        if score.flesch_kincaid_grade > 14:
            recommendations.append(
                f"Grade level ({score.flesch_kincaid_grade}) is high for general audiences. "
                "Consider simplifying complex sentences."
            )

        # Check sentence length
        if score.avg_words_per_sentence > 25:
            recommendations.append(
                f"Average sentence length ({score.avg_words_per_sentence} words) is high. "
                "Consider breaking long sentences into shorter ones."
            )
        elif score.avg_words_per_sentence < 10:
            recommendations.append(
                f"Average sentence length ({score.avg_words_per_sentence} words) is short. "
                "Consider combining some sentences for better flow."
            )

        # Check Flesch Reading Ease
        if score.flesch_reading_ease < 30:
            recommendations.append(
                "Text is very difficult to read. Consider using simpler words "
                "and shorter sentences."
            )

        # Check sentence variety
        if score.sentence_variety < 30:
            recommendations.append(
                "Low sentence variety detected. Try varying sentence length and structure."
            )

        # Check technical complexity for non-technical audiences
        if score.technical_complexity > 50 and score.average_grade_level < 12:
            recommendations.append(
                "High technical complexity may be difficult for the target audience. "
                "Consider defining acronyms and technical terms."
            )

        if not recommendations:
            recommendations.append("Text readability is within acceptable ranges.")

        return recommendations

    def compare_to_targets(self, score: ReadabilityScore) -> Dict[str, Dict[str, Any]]:
        """
        Compare readability scores to technical documentation targets.

        Returns:
            Dict with metric comparisons
        """
        comparisons = {}

        metrics = {
            'flesch_reading_ease': score.flesch_reading_ease,
            'flesch_kincaid_grade': score.flesch_kincaid_grade,
            'gunning_fog': score.gunning_fog,
            'smog_index': score.smog_index,
            'avg_words_per_sentence': score.avg_words_per_sentence,
            'avg_syllables_per_word': score.avg_syllables_per_word,
        }

        for metric, value in metrics.items():
            if metric in self.TECH_DOC_TARGETS:
                min_val, max_val = self.TECH_DOC_TARGETS[metric]
                status = 'within_range'
                if value < min_val:
                    status = 'below_range'
                elif value > max_val:
                    status = 'above_range'

                comparisons[metric] = {
                    'value': value,
                    'target_min': min_val,
                    'target_max': max_val,
                    'status': status
                }

        return comparisons


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_checker_instance: Optional[EnhancedReadabilityChecker] = None


def get_readability_checker() -> EnhancedReadabilityChecker:
    """Get or create singleton readability checker."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = EnhancedReadabilityChecker()
    return _checker_instance


def analyze_readability(text: str) -> Dict[str, Any]:
    """
    Analyze text readability.

    Args:
        text: Text to analyze

    Returns:
        Dict with readability metrics
    """
    checker = get_readability_checker()
    score = checker.analyze(text)

    return {
        'flesch_reading_ease': score.flesch_reading_ease,
        'flesch_kincaid_grade': score.flesch_kincaid_grade,
        'gunning_fog': score.gunning_fog,
        'smog_index': score.smog_index,
        'coleman_liau': score.coleman_liau,
        'automated_readability_index': score.automated_readability_index,
        'linsear_write': score.linsear_write,
        'dale_chall': score.dale_chall,
        'average_grade_level': score.average_grade_level,
        'recommended_audience': score.recommended_audience,
        'word_count': score.word_count,
        'sentence_count': score.sentence_count,
        'avg_words_per_sentence': score.avg_words_per_sentence,
        'avg_syllables_per_word': score.avg_syllables_per_word,
        'technical_complexity': score.technical_complexity,
        'sentence_variety': score.sentence_variety,
        'source': score.source
    }


def get_readability_recommendations(text: str) -> List[str]:
    """Get readability improvement recommendations."""
    checker = get_readability_checker()
    score = checker.analyze(text)
    return checker.get_recommendations(score)


def is_py_readability_available() -> bool:
    """Check if py-readability-metrics is available."""
    return PY_READABILITY_AVAILABLE


__all__ = [
    'EnhancedReadabilityChecker',
    'ReadabilityScore',
    'get_readability_checker',
    'analyze_readability',
    'get_readability_recommendations',
    'is_py_readability_available',
    'VERSION'
]
