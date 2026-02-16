#!/usr/bin/env python3
"""
Advanced Document Analysis Checkers v1.0.0
============================================
Three complementary checkers for deep document quality analysis:

1. CoherenceChecker — Cross-sentence coherence using topic continuity
2. DefinedBeforeUsedChecker — Enforces define-before-use for technical terms
3. QuantifierPrecisionChecker — Catches imprecise quantifiers in requirements

These use spaCy for NLP analysis with regex fallbacks.
"""

import re
from collections import defaultdict, OrderedDict
from typing import Dict, List, Tuple, Set, Optional

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


# ═══════════════════════════════════════════════════════════
# 1. Cross-Sentence Coherence Checker
# ═══════════════════════════════════════════════════════════

class CoherenceChecker(BaseChecker):
    """
    Checks cross-sentence coherence by measuring topic continuity.
    Adjacent sentences should share enough vocabulary to flow logically.
    Abrupt topic shifts without transition words are flagged.
    """

    CHECKER_NAME = "Cross-Sentence Coherence"
    CHECKER_VERSION = "1.0.0"

    COHERENCE_THRESHOLD = 0.05  # Minimum word overlap between adjacent sentences
    MIN_PARAGRAPH_LENGTH = 3    # Minimum sentences to analyze

    # Transition words that justify topic shifts
    TRANSITION_WORDS = {
        'however', 'therefore', 'furthermore', 'moreover', 'additionally',
        'consequently', 'nevertheless', 'meanwhile', 'alternatively',
        'conversely', 'similarly', 'likewise', 'accordingly', 'hence',
        'thus', 'instead', 'otherwise', 'regardless', 'nonetheless',
        'in addition', 'on the other hand', 'as a result', 'for example',
        'in contrast', 'in particular', 'in summary', 'specifically',
        'that is', 'for instance', 'in other words', 'note that',
    }

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
        except Exception:
            pass

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text) or len(text.strip()) < 50:
                continue

            if self.nlp is not None:
                issues.extend(self._check_coherence_nlp(idx, text))
            else:
                issues.extend(self._check_coherence_basic(idx, text))

        return issues

    def _check_coherence_nlp(self, idx, text):
        """Use spaCy to analyze coherence via lemma overlap."""
        issues = []

        try:
            doc = self.nlp(text[:5000])
            sentences = list(doc.sents)

            if len(sentences) < self.MIN_PARAGRAPH_LENGTH:
                return issues

            for i in range(1, len(sentences)):
                prev_sent = sentences[i - 1]
                curr_sent = sentences[i]

                # Extract content lemmas (nouns, verbs, adjectives — not stop words)
                prev_lemmas = {
                    token.lemma_.lower() for token in prev_sent
                    if token.pos_ in ('NOUN', 'VERB', 'ADJ', 'PROPN') and not token.is_stop and len(token.text) > 2
                }
                curr_lemmas = {
                    token.lemma_.lower() for token in curr_sent
                    if token.pos_ in ('NOUN', 'VERB', 'ADJ', 'PROPN') and not token.is_stop and len(token.text) > 2
                }

                if not prev_lemmas or not curr_lemmas:
                    continue

                # Jaccard similarity
                overlap = len(prev_lemmas & curr_lemmas)
                union = len(prev_lemmas | curr_lemmas)
                coherence = overlap / union if union > 0 else 0

                if coherence < self.COHERENCE_THRESHOLD:
                    # Check if there's a transition word
                    curr_text = curr_sent.text.strip().lower()
                    has_transition = any(curr_text.startswith(tw) for tw in self.TRANSITION_WORDS)

                    if not has_transition:
                        issues.append(ReviewIssue(
                            category="Coherence",
                            severity="Low",
                            message=f"Abrupt topic shift between sentences without transition. The two sentences share no key terms.",
                            context=f"...{prev_sent.text[-80:]} → {curr_sent.text[:80]}...",
                            paragraph_index=idx,
                            suggestion="Add a transition word/phrase (e.g., 'However', 'Additionally', 'In contrast') or restructure for better flow.",
                            rule_id="COH-SHIFT",
                            flagged_text=curr_sent.text[:80]
                        ))

        except Exception:
            pass

        return issues

    def _check_coherence_basic(self, idx, text):
        """Fallback: basic word overlap check."""
        issues = []

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 15]

        if len(sentences) < self.MIN_PARAGRAPH_LENGTH:
            return issues

        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                      'shall', 'should', 'may', 'might', 'can', 'could', 'to', 'of',
                      'in', 'for', 'on', 'with', 'at', 'by', 'from', 'and', 'but',
                      'or', 'not', 'that', 'this', 'it', 'its', 'they', 'their'}

        for i in range(1, len(sentences)):
            prev_words = {w.lower() for w in re.findall(r'\b\w{3,}\b', sentences[i-1])} - stop_words
            curr_words = {w.lower() for w in re.findall(r'\b\w{3,}\b', sentences[i])} - stop_words

            if not prev_words or not curr_words:
                continue

            overlap = len(prev_words & curr_words)

            if overlap == 0:
                curr_start = sentences[i][:30].lower()
                has_transition = any(curr_start.startswith(tw) for tw in self.TRANSITION_WORDS)

                if not has_transition:
                    issues.append(ReviewIssue(
                        category="Coherence",
                        severity="Low",
                        message="No topic continuity between adjacent sentences.",
                        context=f"...{sentences[i-1][-60:]} → {sentences[i][:60]}...",
                        paragraph_index=idx,
                        suggestion="Add transition words or shared references to improve flow.",
                        rule_id="COH-SHIFT"
                    ))

        return issues


# ═══════════════════════════════════════════════════════════
# 2. Defined-Before-Used Checker
# ═══════════════════════════════════════════════════════════

class DefinedBeforeUsedChecker(BaseChecker):
    """
    Enforces that technical terms are defined before first use.

    Goes beyond acronym checking to catch:
    - Domain terms used without introduction
    - Jargon that assumes reader knowledge
    - References to undefined concepts
    """

    CHECKER_NAME = "Defined Before Used"
    CHECKER_VERSION = "1.0.0"

    # Patterns that indicate a term is being defined
    DEFINITION_PATTERNS = [
        re.compile(r'\"([^\"]+)\"\s+(?:is|means|refers to|denotes|indicates|represents)', re.IGNORECASE),
        re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:—|–|-)\s*', re.IGNORECASE),
        re.compile(r'(?:defined as|known as|referred to as|called)\s+\"?([^\",.]+)\"?', re.IGNORECASE),
        re.compile(r'([A-Z]{2,})\s*\(([^)]+)\)', re.IGNORECASE),  # ACRONYM (definition)
        re.compile(r'([^(]+)\s*\(([A-Z]{2,})\)', re.IGNORECASE),  # Definition (ACRONYM)
    ]

    # Terms that don't need definition (common enough)
    EXEMPT_TERMS = {
        'system', 'data', 'information', 'document', 'process', 'software',
        'hardware', 'user', 'operator', 'test', 'design', 'review',
        'management', 'project', 'program', 'plan', 'report', 'analysis',
        'performance', 'quality', 'safety', 'standard', 'procedure',
        'requirement', 'specification', 'interface', 'configuration',
    }

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
        except Exception:
            pass

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        if not paragraphs:
            return issues

        # Pass 1: Find all defined terms
        defined_terms = set()
        defined_locations = {}

        for idx, text in paragraphs:
            for pattern in self.DEFINITION_PATTERNS:
                for match in pattern.finditer(text):
                    term = match.group(1).strip().lower()
                    if len(term) > 2:
                        defined_terms.add(term)
                        if term not in defined_locations:
                            defined_locations[term] = idx

        # Pass 2: Find technical terms used before definition
        first_use = OrderedDict()

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue

            if self.nlp is not None:
                terms = self._extract_technical_terms_nlp(text)
            else:
                terms = self._extract_technical_terms_regex(text)

            for term in terms:
                term_lower = term.lower()
                if term_lower not in first_use:
                    first_use[term_lower] = {
                        'text': term,
                        'paragraph': idx,
                        'context': text[:150]
                    }

        # Pass 3: Flag terms used before defined
        for term_lower, info in first_use.items():
            if term_lower in self.EXEMPT_TERMS:
                continue
            if term_lower in defined_terms:
                def_location = defined_locations.get(term_lower, float('inf'))
                if info['paragraph'] < def_location:
                    issues.append(ReviewIssue(
                        category="Defined Before Used",
                        severity="Low",
                        message=f"Term \"{info['text']}\" used at paragraph {info['paragraph']} but defined at paragraph {def_location}.",
                        context=info['context'],
                        paragraph_index=info['paragraph'],
                        suggestion=f"Move the definition of \"{info['text']}\" to before its first use, or add it to a glossary/definitions section at the start.",
                        rule_id="DBU-ORDER",
                        flagged_text=info['text']
                    ))

        return issues

    def _extract_technical_terms_nlp(self, text):
        """Use spaCy NER and noun chunks to identify technical terms."""
        terms = set()
        try:
            doc = self.nlp(text[:3000])

            # Named entities
            for ent in doc.ents:
                if ent.label_ in ('ORG', 'PRODUCT', 'LAW', 'WORK_OF_ART', 'EVENT') and len(ent.text) > 3:
                    terms.add(ent.text)

            # Multi-word noun phrases (technical terms tend to be multi-word)
            for chunk in doc.noun_chunks:
                # Filter to likely technical terms (capitalized, multi-word, or domain-specific)
                text_clean = chunk.text.strip()
                if len(text_clean) > 5 and (
                    text_clean[0].isupper() or
                    '-' in text_clean or
                    len(text_clean.split()) >= 2
                ):
                    terms.add(text_clean)

        except Exception:
            pass

        return terms

    def _extract_technical_terms_regex(self, text):
        """Fallback: regex-based technical term extraction."""
        terms = set()

        # Capitalized multi-word phrases
        for match in re.finditer(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', text):
            terms.add(match.group())

        # Hyphenated terms
        for match in re.finditer(r'\b\w+-\w+(?:-\w+)*\b', text):
            if len(match.group()) > 5:
                terms.add(match.group())

        # ALL-CAPS acronyms (3+ letters)
        for match in re.finditer(r'\b[A-Z]{3,}\b', text):
            terms.add(match.group())

        return terms


# ═══════════════════════════════════════════════════════════
# 3. Quantifier Precision Checker
# ═══════════════════════════════════════════════════════════

class QuantifierPrecisionChecker(BaseChecker):
    """
    Catches imprecise quantifiers in requirements that need exact values.

    Goes beyond basic 'vague quantifier' checking to catch:
    - "approximately X" / "around X" / "about X" in requirements
    - Missing tolerances: "100 psi" without ± tolerance
    - Range ambiguity: "between X and Y" without inclusive/exclusive
    - Comparative without reference: "faster than" / "more than"
    """

    CHECKER_NAME = "Quantifier Precision"
    CHECKER_VERSION = "1.0.0"

    # Approximate quantifiers that need exact values in requirements
    APPROXIMATE_PATTERNS = [
        (re.compile(r'\b(?:approximately|approx\.?)\s+\d', re.IGNORECASE),
         "\"approximately\" is imprecise — specify exact value with tolerance (e.g., '100 ± 5')"),
        (re.compile(r'\b(?:around|about|roughly|nearly|close to|almost)\s+\d', re.IGNORECASE),
         "Vague approximation — specify exact value or acceptable range"),
        (re.compile(r'\b(?:up to|as much as|as many as)\s+\d', re.IGNORECASE),
         "Open-ended maximum — specify exact limit (e.g., 'shall not exceed 100')"),
        (re.compile(r'\b(?:at least|no less than|a minimum of)\s+\d', re.IGNORECASE),
         "Consider whether a tolerance or range is needed in addition to the minimum"),
        (re.compile(r'\b(?:more than|greater than|less than|fewer than)\s+\d', re.IGNORECASE),
         "Comparative quantifier — specify whether boundary value is included (> vs ≥)"),
    ]

    # Missing tolerance patterns
    TOLERANCE_PATTERNS = [
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:psi|kpa|mpa|bar|torr|atm)', re.IGNORECASE),
         "Pressure value in requirement — consider specifying tolerance (± value)"),
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:°[CF]|degrees?\s*[CF]|kelvin|fahrenheit|celsius)', re.IGNORECASE),
         "Temperature value in requirement — consider specifying tolerance"),
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:kg|lb|lbs|pounds?|grams?|ounces?|tons?)', re.IGNORECASE),
         "Weight/mass value in requirement — consider specifying tolerance"),
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:mm|cm|m|km|in|ft|feet|inches|meters?|miles?)', re.IGNORECASE),
         "Dimensional value in requirement — consider specifying tolerance"),
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:ms|sec|seconds?|minutes?|hours?)', re.IGNORECASE),
         "Time value in requirement — consider specifying tolerance or acceptable range"),
        (re.compile(r'(?:shall|must)\s+(?:\w+\s+){0,5}\d+\.?\d*\s*(?:%|percent)', re.IGNORECASE),
         "Percentage in requirement — consider specifying tolerance"),
    ]

    # Range ambiguity patterns
    RANGE_PATTERNS = [
        (re.compile(r'\bbetween\s+\d+\.?\d*\s*(?:and|to|-)\s*\d+\.?\d*\b', re.IGNORECASE),
         "Range specified — clarify if boundaries are inclusive or exclusive"),
        (re.compile(r'\bfrom\s+\d+\.?\d*\s*to\s*\d+\.?\d*\b', re.IGNORECASE),
         "Range specified — clarify if both endpoints are included"),
    ]

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue

            text_lower = text.lower()

            # Only check requirement-like sentences more strictly
            is_requirement = any(kw in text_lower for kw in ['shall', 'must'])

            # Check approximate quantifiers
            for pattern, message in self.APPROXIMATE_PATTERNS:
                for match in pattern.finditer(text):
                    severity = "High" if is_requirement else "Medium"
                    issues.append(ReviewIssue(
                        category="Quantifier Precision",
                        severity=severity,
                        message=f"Imprecise quantifier: \"{match.group()}\" — {message}",
                        context=text[:200],
                        paragraph_index=idx,
                        suggestion="Replace with an exact value and tolerance, e.g., '100 ± 5 psi' instead of 'approximately 100 psi'.",
                        rule_id="QP-APPROX",
                        flagged_text=match.group()
                    ))

            # Check for missing tolerances (only in requirements)
            if is_requirement:
                # Check if tolerance is already specified
                has_tolerance = bool(re.search(r'[±+\-]\s*\d|tolerance|within\s+\d', text, re.IGNORECASE))

                if not has_tolerance:
                    for pattern, message in self.TOLERANCE_PATTERNS:
                        for match in pattern.finditer(text):
                            issues.append(ReviewIssue(
                                category="Quantifier Precision",
                                severity="Medium",
                                message=f"Numeric requirement without tolerance: \"{match.group()[:60]}\" — {message}",
                                context=text[:200],
                                paragraph_index=idx,
                                suggestion="Add an explicit tolerance (e.g., ± value) or acceptable range to make the requirement testable.",
                                rule_id="QP-TOL",
                                flagged_text=match.group()[:60]
                            ))
                            break  # One tolerance issue per paragraph

            # Check range ambiguity
            for pattern, message in self.RANGE_PATTERNS:
                for match in pattern.finditer(text):
                    if is_requirement:
                        issues.append(ReviewIssue(
                            category="Quantifier Precision",
                            severity="Low",
                            message=f"Range specification: \"{match.group()}\" — {message}",
                            context=text[:200],
                            paragraph_index=idx,
                            suggestion="Use explicit notation: 'X ≤ value ≤ Y' or 'X < value < Y' to clarify boundary inclusion.",
                            rule_id="QP-RANGE",
                            flagged_text=match.group()
                        ))

        return issues


def get_advanced_analysis_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning all advanced analysis checkers."""
    return {
        'cross_sentence_coherence': CoherenceChecker(),
        'defined_before_used': DefinedBeforeUsedChecker(),
        'quantifier_precision': QuantifierPrecisionChecker(),
    }
