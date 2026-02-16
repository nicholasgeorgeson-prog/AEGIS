#!/usr/bin/env python3
"""
Negation Detection Checker v1.0.0
==================================
Uses negspacy to detect negated entities and complex negation patterns
in requirements and technical documents.

In requirements engineering, negation scope is critical:
- "The system shall NOT fail" vs "The system shall not fail to operate"
  have very different meanings. This checker identifies:

1. Negated requirements (shall not / must not) with scope analysis
2. Double negatives that obscure meaning
3. Negation of safety-critical terms
4. Ambiguous negation scope (where it's unclear what is being negated)

Uses spaCy dependency tree for scope analysis + negspacy for entity negation.
Falls back to regex patterns when libraries unavailable.
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

# Negation cues for fallback regex
NEGATION_CUES = [
    'not', 'no', 'never', 'neither', 'nor', 'none', 'nowhere',
    'nothing', 'nobody', 'hardly', 'scarcely', 'barely', 'without',
    "n't", "cannot", "can't", "won't", "wouldn't", "shouldn't",
    "couldn't", "mustn't", "doesn't", "don't", "didn't", "isn't",
    "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't"
]

# Safety-critical terms that need special attention when negated
SAFETY_CRITICAL_TERMS = {
    'fail', 'failure', 'hazard', 'hazardous', 'danger', 'dangerous',
    'risk', 'unsafe', 'malfunction', 'error', 'fault', 'defect',
    'damage', 'loss', 'injury', 'harm', 'collision', 'crash',
    'overpressure', 'overload', 'overheat', 'explosion', 'fire',
    'leak', 'rupture', 'fracture', 'fatigue', 'corrosion',
    'contamination', 'toxic', 'lethal', 'critical'
}

# Double negative patterns
DOUBLE_NEGATIVE_PATTERNS = [
    r'\bnot\s+(?:un\w+|in\w+|im\w+|ir\w+|il\w+|dis\w+|non\w+)',
    r'\bno\s+(?:un\w+|in\w+|im\w+|ir\w+|il\w+|dis\w+|non\w+)',
    r'\bnever\s+(?:un\w+|in\w+|im\w+|ir\w+|il\w+|dis\w+|non\w+)',
    r"\bcan'?t\s+(?:un\w+|in\w+|im\w+|ir\w+|il\w+|dis\w+|non\w+)",
    r'\bnot\s+\w+\s+not\b',
    r'\bno\s+\w+\s+no\b',
    r'\bnot\s+without\b',
    r'\bnone\s+\w+\s+not\b',
]

# Ambiguous negation scope patterns
AMBIGUOUS_SCOPE_PATTERNS = [
    (r'\b(?:shall|must|will)\s+not\s+\w+\s+(?:and|or)\s+\w+',
     'Negation with "and/or" creates ambiguous scope — unclear which items are negated'),
    (r'\b(?:not|no)\s+(?:all|every|each|any)\b',
     'Negation with universal quantifier is ambiguous — "not all" vs "none"'),
    (r'\b(?:shall|must)\s+not\s+(?:be\s+)?(?:required|expected|necessary)\s+to\b',
     'Double-layer negation obscures the actual requirement'),
]


class NegationDetectionChecker(BaseChecker):
    """
    Detects and analyzes negation patterns in technical documents.

    Uses negspacy for entity-level negation detection and spaCy's
    dependency tree for scope analysis. Falls back to regex when
    NLP libraries are unavailable.
    """

    CHECKER_NAME = "Negation Detection"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        self.negex_available = False
        self._double_neg_patterns = [re.compile(p, re.IGNORECASE) for p in DOUBLE_NEGATIVE_PATTERNS]
        self._ambiguous_patterns = [(re.compile(p, re.IGNORECASE), msg) for p, msg in AMBIGUOUS_SCOPE_PATTERNS]
        self._init_nlp()

    def _init_nlp(self):
        """Initialize spaCy with negspacy pipeline component."""
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
            if self.nlp is not None:
                try:
                    from negspacy.negation import Negex
                    if 'negex' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("negex", config={"chunk_prefix": ["no"]})
                    self.negex_available = True
                except (ImportError, Exception) as e:
                    self.negex_available = False
        except Exception:
            self.nlp = None
            self.negex_available = False

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue
            if len(text.strip()) < 10:
                continue

            # Check for double negatives
            issues.extend(self._check_double_negatives(idx, text))

            # Check for ambiguous negation scope
            issues.extend(self._check_ambiguous_scope(idx, text))

            # Check for negated safety-critical terms
            issues.extend(self._check_safety_negation(idx, text))

            # NLP-powered negation scope analysis
            if self.nlp is not None:
                issues.extend(self._check_negation_scope_nlp(idx, text))
            else:
                issues.extend(self._check_negation_scope_regex(idx, text))

        return issues

    def _check_double_negatives(self, idx, text):
        """Detect double negatives that obscure meaning."""
        issues = []
        for pattern in self._double_neg_patterns:
            for match in pattern.finditer(text):
                matched = match.group()
                issues.append(ReviewIssue(
                    category="Negation",
                    severity="High",
                    message=f"Double negative detected: \"{matched}\" — this obscures the intended meaning. Rephrase positively.",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion="Rephrase using positive language. Example: 'not uncommon' → 'common', 'not without risk' → 'risky'",
                    rule_id="NEG-001",
                    flagged_text=matched
                ))
        return issues

    def _check_ambiguous_scope(self, idx, text):
        """Detect negation with ambiguous scope."""
        issues = []
        for pattern, message in self._ambiguous_patterns:
            for match in pattern.finditer(text):
                matched = match.group()
                issues.append(ReviewIssue(
                    category="Negation",
                    severity="Medium",
                    message=f"Ambiguous negation scope: \"{matched}\" — {message}",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion="Break into separate statements with clear negation scope for each item.",
                    rule_id="NEG-002",
                    flagged_text=matched
                ))
        return issues

    def _check_safety_negation(self, idx, text):
        """Flag negation of safety-critical terms for manual review."""
        issues = []
        text_lower = text.lower()

        for term in SAFETY_CRITICAL_TERMS:
            # Check if safety term appears near a negation cue
            for cue in ['not', 'no', 'never', 'without', "n't", 'cannot']:
                pattern = re.compile(
                    rf'\b{re.escape(cue)}\s+(?:\w+\s+){{0,3}}{re.escape(term)}\b',
                    re.IGNORECASE
                )
                for match in pattern.finditer(text):
                    matched = match.group()
                    issues.append(ReviewIssue(
                        category="Negation",
                        severity="High",
                        message=f"Negated safety-critical term: \"{matched}\" — verify the negation scope is correct and the intended safety constraint is clear.",
                        context=text[:200],
                        paragraph_index=idx,
                        suggestion=f"Consider rephrasing positively. Negating safety terms ('{term}') can create confusion about the actual safety requirement.",
                        rule_id="NEG-003",
                        flagged_text=matched
                    ))
        return issues

    def _check_negation_scope_nlp(self, idx, text):
        """Use spaCy dependency tree to analyze negation scope."""
        issues = []
        try:
            doc = self.nlp(text[:5000])  # Limit processing length

            for token in doc:
                if token.dep_ == 'neg':
                    # Found a negation — analyze what it modifies
                    head = token.head

                    # Check if negation modifies a verb in a requirement statement
                    if head.pos_ == 'VERB':
                        # Check for "shall not" type constructions
                        has_shall = any(
                            child.text.lower() in ('shall', 'must', 'will')
                            for child in head.children
                            if child.dep_ == 'aux'
                        )

                        if has_shall:
                            # Count how many objects/complements the negated verb has
                            objects = [
                                child for child in head.children
                                if child.dep_ in ('dobj', 'pobj', 'attr', 'acomp', 'xcomp', 'ccomp')
                            ]
                            conjuncts = [
                                child for child in head.children
                                if child.dep_ == 'conj'
                            ]

                            if len(objects) > 1 or len(conjuncts) > 0:
                                sent_text = head.sent.text[:150]
                                issues.append(ReviewIssue(
                                    category="Negation",
                                    severity="Medium",
                                    message=f"Negated requirement with multiple objects/clauses — scope may be ambiguous. Does the negation apply to all listed items?",
                                    context=sent_text,
                                    paragraph_index=idx,
                                    suggestion="Split into separate requirements with explicit negation for each, or add parentheses/restructure for clarity.",
                                    rule_id="NEG-004",
                                    flagged_text=head.sent.text[:100]
                                ))

            # If negex is available, check for negated entities
            if self.negex_available:
                for ent in doc.ents:
                    if hasattr(ent, 'negex') and ent.negex:  # negex attribute = True means negated
                        issues.append(ReviewIssue(
                            category="Negation",
                            severity="Info",
                            message=f"Negated entity detected: \"{ent.text}\" ({ent.label_}) — verify this is intentional.",
                            context=ent.sent.text[:200] if hasattr(ent, 'sent') else text[:200],
                            paragraph_index=idx,
                            suggestion="Ensure the negation of this entity is intentional and unambiguous.",
                            rule_id="NEG-005",
                            flagged_text=ent.text
                        ))
        except Exception:
            pass

        return issues

    def _check_negation_scope_regex(self, idx, text):
        """Fallback: regex-based negation scope analysis."""
        issues = []

        # Check for "shall not ... and ..." patterns
        pattern = re.compile(
            r'\b(?:shall|must|will)\s+not\s+[\w\s,]+(?:\band\b|\bor\b)[\w\s,]+',
            re.IGNORECASE
        )
        for match in pattern.finditer(text):
            matched = match.group()
            if len(matched.split()) > 5:  # Only flag substantial matches
                issues.append(ReviewIssue(
                    category="Negation",
                    severity="Medium",
                    message=f"Negated requirement with conjunctions — verify negation scope covers all intended items.",
                    context=text[:200],
                    paragraph_index=idx,
                    suggestion="Consider splitting into separate negated requirements for clarity.",
                    rule_id="NEG-004",
                    flagged_text=matched[:100]
                ))

        return issues


def get_negation_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning all negation detection checkers."""
    return {
        'negation_detection': NegationDetectionChecker()
    }
