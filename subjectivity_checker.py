#!/usr/bin/env python3
"""
Subjectivity & Tone Checker v1.0.0
====================================
Uses spacytextblob to detect subjective language in technical documents.

In requirements and specifications, subjective language is a quality issue:
- "The system should perform well" (subjective — what is "well"?)
- "The system shall process 100 transactions per second" (objective — measurable)

This checker flags:
1. Highly subjective sentences in requirement contexts
2. Emotional/opinion language in technical sections
3. Sentiment polarity in sections that should be neutral
4. Marketing-speak in engineering documents

Falls back to TextBlob directly when spacytextblob pipeline unavailable.
"""

import re
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    from .base_checker import BaseChecker, ReviewIssue

try:
    from nlp_utils import get_spacy_model
except ImportError:
    def get_spacy_model(name='en_core_web_sm'):
        try:
            import spacy
            return spacy.load(name)
        except Exception:
            return None

__version__ = "1.0.0"

# Marketing-speak / hype words that don't belong in technical docs
MARKETING_TERMS = {
    'best-in-class', 'world-class', 'cutting-edge', 'state-of-the-art',
    'game-changing', 'revolutionary', 'groundbreaking', 'innovative',
    'unparalleled', 'unprecedented', 'superior', 'excellent', 'outstanding',
    'exceptional', 'remarkable', 'incredible', 'amazing', 'fantastic',
    'tremendous', 'spectacular', 'impressive', 'leading-edge', 'next-generation',
    'best of breed', 'paradigm shift', 'synergy', 'leverage',
    'holistic', 'robust', 'seamless', 'turnkey', 'scalable',
    'mission-critical', 'enterprise-grade', 'bleeding-edge',
}

# Subjective adjectives that need quantification in requirements
SUBJECTIVE_ADJECTIVES = {
    'good', 'bad', 'better', 'worse', 'best', 'worst',
    'fast', 'slow', 'quick', 'rapid',
    'large', 'small', 'big', 'tiny', 'huge', 'massive',
    'easy', 'difficult', 'hard', 'simple', 'complex',
    'high', 'low', 'sufficient', 'adequate', 'appropriate',
    'reasonable', 'significant', 'substantial', 'considerable',
    'efficient', 'effective', 'reliable', 'accurate',
    'user-friendly', 'intuitive', 'responsive', 'performant',
    'lightweight', 'heavyweight', 'minimal', 'optimal',
}


class SubjectivityChecker(BaseChecker):
    """
    Detects subjective language in technical documents using
    spacytextblob sentiment/subjectivity analysis.
    """

    CHECKER_NAME = "Subjectivity Detection"
    CHECKER_VERSION = "1.0.0"

    SUBJECTIVITY_THRESHOLD = 0.6  # Sentences above this are flagged
    POLARITY_THRESHOLD = 0.5      # Sentences with strong sentiment

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        self.textblob_available = False
        self._init_nlp()

    def _init_nlp(self):
        """Initialize spaCy with spacytextblob pipeline."""
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
            if self.nlp is not None:
                try:
                    from spacytextblob.spacytextblob import SpacyTextBlob
                    if 'spacytextblob' not in self.nlp.pipe_names:
                        self.nlp.add_pipe('spacytextblob')
                    self.textblob_available = True
                except (ImportError, Exception):
                    self.textblob_available = False
        except Exception:
            self.nlp = None

        # Direct TextBlob fallback
        if not self.textblob_available:
            try:
                from textblob import TextBlob
                self.textblob_available = True
            except ImportError:
                pass

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text) or len(text.strip()) < 20:
                continue

            # Check for marketing-speak
            issues.extend(self._check_marketing_speak(idx, text))

            # Check for subjective adjectives in requirement contexts
            issues.extend(self._check_subjective_adjectives(idx, text))

            # NLP-based subjectivity/sentiment analysis
            if self.nlp is not None and 'spacytextblob' in self.nlp.pipe_names:
                issues.extend(self._check_subjectivity_nlp(idx, text))
            elif self.textblob_available:
                issues.extend(self._check_subjectivity_textblob(idx, text))

        return issues

    def _check_marketing_speak(self, idx, text):
        """Detect marketing/hype language in technical documents."""
        issues = []
        text_lower = text.lower()

        for term in MARKETING_TERMS:
            if term in text_lower:
                issues.append(ReviewIssue(
                    category="Subjectivity",
                    severity="Medium",
                    message=f"Marketing language detected: \"{term}\" — replace with specific, measurable terms in technical documents.",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion=f"Replace \"{term}\" with a quantifiable or objectively verifiable statement.",
                    rule_id="SUB-MKT",
                    flagged_text=term
                ))

        return issues

    def _check_subjective_adjectives(self, idx, text):
        """Check for subjective adjectives in requirement sentences."""
        issues = []
        text_lower = text.lower()

        # Only flag in requirement-like sentences
        is_requirement = any(kw in text_lower for kw in ['shall', 'must', 'will', 'should'])

        if not is_requirement:
            return issues

        for adj in SUBJECTIVE_ADJECTIVES:
            # Look for the adjective as a whole word
            pattern = re.compile(rf'\b{re.escape(adj)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                # Check if it's followed by a quantifier (which would make it OK)
                after = text[match.end():match.end()+30].strip()
                has_quantifier = bool(re.match(r'(?:than|of|at\s+least|or\s+more|or\s+less|\d)', after))

                if not has_quantifier:
                    issues.append(ReviewIssue(
                        category="Subjectivity",
                        severity="Medium",
                        message=f"Subjective adjective \"{adj}\" in requirement — needs quantification or measurable criteria.",
                        context=text[:200],
                        paragraph_index=idx,
                        suggestion=f"Replace \"{adj}\" with a measurable criterion. Example: 'fast response' → 'response within 100ms'.",
                        rule_id="SUB-ADJ",
                        flagged_text=match.group()
                    ))
                    break  # One issue per adjective per paragraph

        return issues

    def _check_subjectivity_nlp(self, idx, text):
        """Use spacytextblob for sentence-level subjectivity scoring."""
        issues = []
        try:
            doc = self.nlp(text[:5000])

            # Document-level subjectivity
            if hasattr(doc._, 'blob'):
                subjectivity = doc._.blob.subjectivity
                polarity = doc._.blob.polarity

                if subjectivity > self.SUBJECTIVITY_THRESHOLD:
                    issues.append(ReviewIssue(
                        category="Subjectivity",
                        severity="Low",
                        message=f"Paragraph has high subjectivity score ({subjectivity:.2f}/1.0) — technical writing should be objective.",
                        context=text[:200],
                        paragraph_index=idx,
                        suggestion="Review for opinion-based language and replace with factual, measurable statements.",
                        rule_id="SUB-SCORE"
                    ))

                if abs(polarity) > self.POLARITY_THRESHOLD:
                    direction = "positive" if polarity > 0 else "negative"
                    issues.append(ReviewIssue(
                        category="Subjectivity",
                        severity="Low",
                        message=f"Strong {direction} sentiment detected (polarity: {polarity:.2f}) — technical docs should maintain neutral tone.",
                        context=text[:200],
                        paragraph_index=idx,
                        suggestion="Rephrase to remove emotional language and maintain a neutral, factual tone.",
                        rule_id="SUB-SENT"
                    ))

        except Exception:
            pass

        return issues

    def _check_subjectivity_textblob(self, idx, text):
        """Fallback: use TextBlob directly for subjectivity analysis."""
        issues = []
        try:
            from textblob import TextBlob
            blob = TextBlob(text[:5000])

            if blob.sentiment.subjectivity > self.SUBJECTIVITY_THRESHOLD:
                issues.append(ReviewIssue(
                    category="Subjectivity",
                    severity="Low",
                    message=f"Paragraph has high subjectivity ({blob.sentiment.subjectivity:.2f}/1.0) — consider rephrasing for objectivity.",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion="Replace subjective statements with factual, verifiable claims.",
                    rule_id="SUB-SCORE"
                ))

            if abs(blob.sentiment.polarity) > self.POLARITY_THRESHOLD:
                direction = "positive" if blob.sentiment.polarity > 0 else "negative"
                issues.append(ReviewIssue(
                    category="Subjectivity",
                    severity="Low",
                    message=f"Strong {direction} sentiment ({blob.sentiment.polarity:.2f}) — maintain neutral tone in technical writing.",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion="Rephrase emotionally charged language to be neutral and factual.",
                    rule_id="SUB-SENT"
                ))

        except Exception:
            pass

        return issues


def get_subjectivity_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning subjectivity/tone checkers."""
    return {
        'subjectivity_detection': SubjectivityChecker()
    }
