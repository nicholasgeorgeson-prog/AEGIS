#!/usr/bin/env python3
"""
Terminology Consistency Checker v1.0.0
=======================================
Uses spacy-wordnet to detect terminology inconsistencies in technical documents.

In aerospace/defense docs, the same concept being called different names is a
major quality issue:
- "aircraft" vs "vehicle" vs "platform" vs "system"
- "operator" vs "user" vs "pilot"
- "shall" vs "must" vs "will" (strength inconsistency)

This checker:
1. Builds a term frequency map of all noun phrases / key terms
2. Uses WordNet synonym sets to find terms that MIGHT be referring to the same concept
3. Flags inconsistencies where multiple synonymous terms are used
4. Tracks first-use of each term to show where inconsistency begins

Falls back to a curated synonym list when spacy-wordnet is unavailable.
"""

import re
from collections import defaultdict, Counter
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

# Curated synonym groups common in aerospace/defense technical writing
# These are groups where using multiple terms from the same group is inconsistent
AEROSPACE_SYNONYM_GROUPS = [
    {'aircraft', 'airplane', 'aeroplane', 'plane', 'vehicle', 'platform', 'air vehicle'},
    {'helicopter', 'rotorcraft', 'helo', 'chopper'},
    {'unmanned aerial vehicle', 'uav', 'drone', 'unmanned aircraft', 'uas', 'rpas'},
    {'operator', 'user', 'pilot', 'aviator', 'flight crew', 'aircrew'},
    {'maintainer', 'maintenance technician', 'maintenance personnel', 'mechanic'},
    {'component', 'part', 'assembly', 'subassembly', 'unit', 'module'},
    {'system', 'subsystem', 'equipment', 'apparatus'},
    {'test', 'evaluation', 'assessment', 'analysis', 'examination', 'inspection'},
    {'defect', 'fault', 'failure', 'malfunction', 'anomaly', 'discrepancy'},
    {'requirement', 'specification', 'criterion', 'standard', 'constraint'},
    {'document', 'report', 'record', 'file', 'publication'},
    {'procedure', 'process', 'method', 'technique', 'approach'},
    {'interface', 'connection', 'link', 'coupling', 'junction'},
    {'verify', 'validate', 'confirm', 'check', 'ensure'},
    {'design', 'architecture', 'configuration', 'layout'},
    {'schedule', 'timeline', 'timetable', 'plan', 'program'},
    {'contractor', 'vendor', 'supplier', 'subcontractor', 'provider'},
    {'review', 'audit', 'inspection', 'assessment', 'evaluation'},
    {'hazard', 'risk', 'threat', 'danger'},
    {'material', 'substance', 'compound', 'alloy'},
]

# Strength/obligation terms that should be used consistently
OBLIGATION_GROUPS = [
    {'shall', 'must'},  # Strong obligation — pick one
    {'should', 'ought to', 'is recommended'},  # Recommendation
    {'may', 'can', 'is permitted'},  # Permission
    {'will', 'is expected to'},  # Declaration of purpose
]


class TerminologyConsistencyChecker(BaseChecker):
    """
    Detects terminology inconsistencies using WordNet synonym sets
    and curated aerospace/defense term groups.
    """

    CHECKER_NAME = "Terminology Consistency"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        self.wordnet_available = False
        self._init_nlp()

    def _init_nlp(self):
        """Initialize spaCy with wordnet pipeline."""
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
            if self.nlp is not None:
                try:
                    from spacy_wordnet.wordnet_annotator import WordnetAnnotator
                    if 'spacy_wordnet' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("spacy_wordnet", after='tagger', config={'lang': 'en'})
                    self.wordnet_available = True
                except (ImportError, Exception):
                    self.wordnet_available = False
        except Exception:
            self.nlp = None

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        if not paragraphs:
            return issues

        # Build term frequency map
        term_locations = defaultdict(list)  # term -> [(paragraph_idx, context)]

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue
            text_lower = text.lower()
            words = re.findall(r'\b[a-z]+(?:\s+[a-z]+)?\b', text_lower)
            for word in words:
                if len(word) > 2 and word not in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out'}:
                    term_locations[word].append((idx, text[:100]))

        # Check curated synonym groups
        issues.extend(self._check_curated_groups(term_locations, paragraphs))

        # Check obligation term consistency
        issues.extend(self._check_obligation_consistency(term_locations, paragraphs))

        # If WordNet available, do deeper analysis
        if self.wordnet_available and self.nlp is not None:
            issues.extend(self._check_wordnet_synonyms(paragraphs))

        return issues

    def _check_curated_groups(self, term_locations, paragraphs):
        """Check for inconsistencies in curated aerospace synonym groups."""
        issues = []

        for group in AEROSPACE_SYNONYM_GROUPS:
            found_terms = {}
            for term in group:
                if term in term_locations and len(term_locations[term]) >= 2:
                    found_terms[term] = len(term_locations[term])

            # If multiple terms from same group are used significantly
            if len(found_terms) >= 2:
                # Find the dominant term (most used)
                dominant = max(found_terms, key=found_terms.get)
                others = {t: c for t, c in found_terms.items() if t != dominant}

                for other_term, count in others.items():
                    if count >= 2:  # Only flag if used multiple times
                        first_loc = term_locations[other_term][0]
                        issues.append(ReviewIssue(
                            category="Terminology Consistency",
                            severity="Medium",
                            message=f"Inconsistent terminology: \"{other_term}\" used {count} times, but \"{dominant}\" is used {found_terms[dominant]} times. Consider standardizing.",
                            context=first_loc[1],
                            paragraph_index=first_loc[0],
                            suggestion=f"Choose one term consistently. The document primarily uses \"{dominant}\" — consider replacing \"{other_term}\" throughout.",
                            rule_id="TC-SYN",
                            flagged_text=other_term
                        ))

        return issues

    def _check_obligation_consistency(self, term_locations, paragraphs):
        """Check that obligation terms are used consistently."""
        issues = []

        for group in OBLIGATION_GROUPS:
            found_terms = {}
            for term in group:
                if term in term_locations:
                    found_terms[term] = len(term_locations[term])

            if len(found_terms) >= 2:
                dominant = max(found_terms, key=found_terms.get)
                others = {t: c for t, c in found_terms.items() if t != dominant}

                for other_term, count in others.items():
                    if count >= 3:  # Higher threshold for obligation words
                        first_loc = term_locations[other_term][0]
                        issues.append(ReviewIssue(
                            category="Terminology Consistency",
                            severity="High",
                            message=f"Obligation strength inconsistency: \"{other_term}\" used {count} times alongside \"{dominant}\" ({found_terms[dominant]} times). In requirements, these have different legal/contractual meanings.",
                            context=first_loc[1],
                            paragraph_index=first_loc[0],
                            suggestion=f"Standardize obligation language. \"shall\" = mandatory, \"should\" = recommended, \"may\" = permitted, \"will\" = declaration of purpose.",
                            rule_id="TC-OBL",
                            flagged_text=other_term
                        ))

        return issues

    def _check_wordnet_synonyms(self, paragraphs):
        """Use WordNet to find additional synonym inconsistencies."""
        issues = []

        try:
            # Extract key nouns from each paragraph using spaCy
            noun_locations = defaultdict(list)  # lemma -> [(idx, surface_form, context)]

            for idx, text in paragraphs:
                if self.is_boilerplate(text) or len(text.strip()) < 20:
                    continue

                doc = self.nlp(text[:3000])

                for token in doc:
                    if token.pos_ == 'NOUN' and len(token.text) > 3 and not token.is_stop:
                        lemma = token.lemma_.lower()
                        noun_locations[lemma].append((idx, token.text, text[:100]))

            # For each noun, check if any other nouns in the document are synonyms
            checked_pairs = set()
            nouns = list(noun_locations.keys())

            for i, noun1 in enumerate(nouns[:100]):  # Limit for performance
                if len(noun_locations[noun1]) < 2:
                    continue

                try:
                    doc1 = self.nlp(noun1)
                    if not doc1 or not doc1[0]._.wordnet:
                        continue
                    synsets1 = set()
                    for s in doc1[0]._.wordnet.synsets():
                        for lemma in s.lemma_names():
                            synsets1.add(lemma.lower().replace('_', ' '))
                except Exception:
                    continue

                for noun2 in nouns[i+1:100]:
                    if noun2 == noun1:
                        continue
                    pair = tuple(sorted([noun1, noun2]))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    if len(noun_locations[noun2]) < 2:
                        continue

                    # Check if noun2 is in noun1's synset
                    if noun2 in synsets1:
                        count1 = len(noun_locations[noun1])
                        count2 = len(noun_locations[noun2])

                        # Only flag if both are used substantially
                        if count1 >= 3 and count2 >= 3:
                            dominant = noun1 if count1 >= count2 else noun2
                            other = noun2 if dominant == noun1 else noun1
                            other_count = count2 if dominant == noun1 else count1
                            dom_count = count1 if dominant == noun1 else count2

                            first_loc = noun_locations[other][0]
                            issues.append(ReviewIssue(
                                category="Terminology Consistency",
                                severity="Low",
                                message=f"Possible synonym inconsistency (WordNet): \"{other}\" ({other_count}×) and \"{dominant}\" ({dom_count}×) may refer to the same concept.",
                                context=first_loc[2],
                                paragraph_index=first_loc[0],
                                suggestion=f"If these refer to the same concept, standardize on one term (suggested: \"{dominant}\").",
                                rule_id="TC-WN",
                                flagged_text=other
                            ))

        except Exception:
            pass

        return issues


def get_terminology_consistency_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning terminology consistency checkers."""
    return {
        'terminology_consistency': TerminologyConsistencyChecker()
    }
