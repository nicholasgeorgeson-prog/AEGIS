"""
Enhanced Readability Calculator for AEGIS
====================================================
Comprehensive readability analysis using textstat.

Features:
- Standard metrics: Flesch Reading Ease, Flesch-Kincaid, Gunning Fog
- New metrics: Dale-Chall, SMOG, Linsear Write, Coleman-Liau, ARI
- Difficult word identification
- Reading time estimation
- Grade level interpretation
- Improvement recommendations

Requires: pip install textstat
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..base import NLPIntegrationBase


@dataclass
class ReadabilityReport:
    """Comprehensive readability analysis result."""

    # Standard metrics (already in tool)
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    gunning_fog: float = 0.0

    # NEW metrics
    dale_chall: float = 0.0
    smog_index: float = 0.0
    linsear_write: float = 0.0
    coleman_liau: float = 0.0
    automated_readability: float = 0.0

    # Summary
    consensus_grade: float = 0.0
    reading_time_minutes: float = 0.0

    # Word analysis
    difficult_words: List[str] = field(default_factory=list)
    difficult_word_count: int = 0
    lexicon_count: int = 0
    sentence_count: int = 0

    # Interpretation
    grade_level: str = ""
    difficulty_rating: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'flesch_reading_ease': self.flesch_reading_ease,
            'flesch_kincaid_grade': self.flesch_kincaid_grade,
            'gunning_fog': self.gunning_fog,
            'dale_chall': self.dale_chall,
            'smog_index': self.smog_index,
            'linsear_write': self.linsear_write,
            'coleman_liau': self.coleman_liau,
            'automated_readability': self.automated_readability,
            'consensus_grade': self.consensus_grade,
            'reading_time_minutes': self.reading_time_minutes,
            'difficult_words': self.difficult_words,
            'difficult_word_count': self.difficult_word_count,
            'lexicon_count': self.lexicon_count,
            'sentence_count': self.sentence_count,
            'grade_level': self.grade_level,
            'difficulty_rating': self.difficulty_rating,
        }


class EnhancedReadabilityCalculator(NLPIntegrationBase):
    """
    Enhanced readability analysis using textstat.

    Adds metrics not in current implementation.
    """

    INTEGRATION_NAME = "Textstat"
    INTEGRATION_VERSION = "1.0.0"

    # Grade level descriptions
    GRADE_LEVELS = {
        (0, 6): "Elementary (Grade 1-5)",
        (6, 8): "Middle School (Grade 6-8)",
        (8, 12): "High School (Grade 9-12)",
        (12, 14): "College",
        (14, 17): "College Graduate",
        (17, 100): "Professional/Academic"
    }

    # Flesch Reading Ease interpretations
    DIFFICULTY_RATINGS = {
        (90, 100): "Very Easy",
        (80, 90): "Easy",
        (70, 80): "Fairly Easy",
        (60, 70): "Standard",
        (50, 60): "Fairly Difficult",
        (30, 50): "Difficult",
        (0, 30): "Very Difficult"
    }

    # Target thresholds for technical documentation
    TECH_DOC_TARGETS = {
        'max_grade_level': 12,
        'min_flesch_ease': 40,
        'max_difficult_word_pct': 15,
        'max_sentence_length': 25,
    }

    def __init__(self):
        """Initialize the readability calculator."""
        super().__init__()
        self._textstat = None
        self._initialize()

    def _initialize(self):
        """Initialize textstat library."""
        try:
            import textstat
            self._textstat = textstat
            self._available = True
        except ImportError as e:
            self._error = f"textstat not installed: {e}"
            self._available = False

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the textstat integration."""
        status = {
            'available': self.is_available,
            'error': self._error,
        }

        if self.is_available:
            status['metrics_available'] = [
                'flesch_reading_ease',
                'flesch_kincaid_grade',
                'gunning_fog',
                'dale_chall',
                'smog_index',
                'linsear_write',
                'coleman_liau',
                'automated_readability',
            ]

        return status

    def analyze(self, text: str) -> ReadabilityReport:
        """
        Perform comprehensive readability analysis.

        Args:
            text: Text to analyze

        Returns:
            ReadabilityReport with all metrics
        """
        if not self.is_available:
            return ReadabilityReport()

        if not text or len(text.strip()) < 20:
            return ReadabilityReport()

        ts = self._textstat

        # Standard metrics
        flesch_ease = ts.flesch_reading_ease(text)
        flesch_grade = ts.flesch_kincaid_grade(text)
        gunning = ts.gunning_fog(text)

        # NEW metrics
        dale_chall = ts.dale_chall_readability_score(text)
        smog = ts.smog_index(text)
        linsear = ts.linsear_write_formula(text)
        coleman = ts.coleman_liau_index(text)
        ari = ts.automated_readability_index(text)

        # Word analysis
        try:
            difficult = ts.difficult_words_list(text)
        except Exception:
            difficult = []

        # Counts
        word_count = ts.lexicon_count(text, removepunct=True)
        sentence_count = ts.sentence_count(text)

        # Calculate consensus grade (average of grade-level metrics)
        grades = [g for g in [flesch_grade, gunning, linsear, coleman, ari] if g > 0]
        consensus = sum(grades) / len(grades) if grades else 0

        # Reading time (average 200 words per minute)
        reading_time = word_count / 200.0

        # Interpretations
        grade_level = self._get_grade_level(consensus)
        difficulty = self._get_difficulty(flesch_ease)

        return ReadabilityReport(
            flesch_reading_ease=round(flesch_ease, 1),
            flesch_kincaid_grade=round(flesch_grade, 1),
            gunning_fog=round(gunning, 1),
            dale_chall=round(dale_chall, 2),
            smog_index=round(smog, 1),
            linsear_write=round(linsear, 1),
            coleman_liau=round(coleman, 1),
            automated_readability=round(ari, 1),
            consensus_grade=round(consensus, 1),
            reading_time_minutes=round(reading_time, 1),
            difficult_words=difficult[:20],  # Top 20
            difficult_word_count=len(difficult),
            lexicon_count=word_count,
            sentence_count=sentence_count,
            grade_level=grade_level,
            difficulty_rating=difficulty
        )

    def _get_grade_level(self, consensus: float) -> str:
        """Convert numeric grade to description."""
        for (low, high), level in self.GRADE_LEVELS.items():
            if low <= consensus < high:
                return level
        return "Unknown"

    def _get_difficulty(self, flesch_score: float) -> str:
        """Convert Flesch score to difficulty rating."""
        for (low, high), rating in self.DIFFICULTY_RATINGS.items():
            if low <= flesch_score < high:
                return rating
        return "Unknown"

    def get_recommendations(self, report: ReadabilityReport) -> List[str]:
        """
        Generate readability improvement recommendations.

        Args:
            report: ReadabilityReport from analyze()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        targets = self.TECH_DOC_TARGETS

        # Grade level recommendations
        if report.consensus_grade > 16:
            recommendations.append(
                f"Grade level ({report.consensus_grade}) is very high. "
                "Consider simplifying for broader audience."
            )
        elif report.consensus_grade > targets['max_grade_level']:
            recommendations.append(
                f"Grade level ({report.consensus_grade}) exceeds target "
                f"({targets['max_grade_level']}). Consider simpler vocabulary."
            )

        # Flesch ease recommendations
        if report.flesch_reading_ease < 30:
            recommendations.append(
                f"Flesch Reading Ease ({report.flesch_reading_ease}) indicates "
                "very difficult text. Shorten sentences and use simpler words."
            )
        elif report.flesch_reading_ease < targets['min_flesch_ease']:
            recommendations.append(
                f"Flesch Reading Ease ({report.flesch_reading_ease}) is below "
                f"target ({targets['min_flesch_ease']}). Consider simplification."
            )

        # Difficult words
        if report.lexicon_count > 0:
            difficult_pct = (report.difficult_word_count / report.lexicon_count) * 100
            if difficult_pct > targets['max_difficult_word_pct']:
                recommendations.append(
                    f"Difficult word percentage ({difficult_pct:.1f}%) is high. "
                    "Consider defining technical terms or using simpler alternatives."
                )

        # Sentence length
        if report.sentence_count > 0:
            avg_sentence_length = report.lexicon_count / report.sentence_count
            if avg_sentence_length > targets['max_sentence_length']:
                recommendations.append(
                    f"Average sentence length ({avg_sentence_length:.1f} words) "
                    f"exceeds target ({targets['max_sentence_length']}). "
                    "Break long sentences into shorter ones."
                )

        # Specific difficult words
        if report.difficult_words:
            sample = report.difficult_words[:5]
            recommendations.append(
                f"Consider defining or simplifying these words: {', '.join(sample)}"
            )

        # Positive feedback if good
        if not recommendations:
            recommendations.append(
                "Readability is within acceptable ranges for technical documentation."
            )

        return recommendations

    def get_summary(self, report: ReadabilityReport) -> str:
        """
        Get a brief summary of readability.

        Args:
            report: ReadabilityReport from analyze()

        Returns:
            Summary string
        """
        return (
            f"Grade Level: {report.grade_level} ({report.consensus_grade}), "
            f"Difficulty: {report.difficulty_rating}, "
            f"Reading Time: {report.reading_time_minutes} min"
        )

    def compare_metrics(self, report: ReadabilityReport) -> Dict[str, str]:
        """
        Compare all grade-level metrics.

        Args:
            report: ReadabilityReport from analyze()

        Returns:
            Dict of metric names to formatted values
        """
        return {
            'Flesch-Kincaid': f"Grade {report.flesch_kincaid_grade}",
            'Gunning Fog': f"Grade {report.gunning_fog}",
            'Dale-Chall': f"{report.dale_chall} ({self._dale_chall_grade(report.dale_chall)})",
            'SMOG Index': f"Grade {report.smog_index}",
            'Linsear Write': f"Grade {report.linsear_write}",
            'Coleman-Liau': f"Grade {report.coleman_liau}",
            'ARI': f"Grade {report.automated_readability}",
            'Consensus': f"Grade {report.consensus_grade}",
        }

    def _dale_chall_grade(self, score: float) -> str:
        """Convert Dale-Chall score to grade level."""
        if score <= 4.9:
            return "Grade 4 and below"
        elif score <= 5.9:
            return "Grade 5-6"
        elif score <= 6.9:
            return "Grade 7-8"
        elif score <= 7.9:
            return "Grade 9-10"
        elif score <= 8.9:
            return "Grade 11-12"
        else:
            return "College"
