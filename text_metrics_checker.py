#!/usr/bin/env python3
"""
Text Descriptives / Quality Metrics Checker v1.0.0
===================================================
Uses textdescriptives (spaCy component) to compute 40+ text quality metrics
per document in a single pipeline pass, then flags documents/sections that
fall outside acceptable ranges for technical writing.

Metrics computed:
- Readability: Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, ARI, Lix, Rix
- Information density: dependency distance, prop_adjacent, noun/verb ratios
- Coherence: first/second order coherence between sentences
- Sentence complexity: tree depth, max/mean dependency distance
- Quality indicators: Type-Token Ratio, POS proportions

Falls back to textstat + custom calculations when textdescriptives unavailable.
"""

import re
import math
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


# Acceptable ranges for technical writing metrics
METRIC_THRESHOLDS = {
    'flesch_reading_ease': {'min': 20, 'max': 60, 'ideal_min': 30, 'ideal_max': 50,
                            'label': 'Flesch Reading Ease'},
    'flesch_kincaid_grade': {'min': 8, 'max': 18, 'ideal_min': 10, 'ideal_max': 14,
                             'label': 'Flesch-Kincaid Grade Level'},
    'gunning_fog': {'min': 8, 'max': 20, 'ideal_min': 10, 'ideal_max': 16,
                    'label': 'Gunning Fog Index'},
    'smog_index': {'min': 8, 'max': 18, 'ideal_min': 10, 'ideal_max': 14,
                   'label': 'SMOG Index'},
    'coleman_liau_index': {'min': 8, 'max': 18, 'ideal_min': 10, 'ideal_max': 15,
                           'label': 'Coleman-Liau Index'},
    'ari': {'min': 8, 'max': 18, 'ideal_min': 10, 'ideal_max': 14,
            'label': 'Automated Readability Index'},
    'avg_sentence_length': {'min': 8, 'max': 35, 'ideal_min': 12, 'ideal_max': 25,
                            'label': 'Average Sentence Length (words)'},
    'avg_word_length': {'min': 3.5, 'max': 7.0, 'ideal_min': 4.0, 'ideal_max': 6.0,
                        'label': 'Average Word Length (chars)'},
}


class TextMetricsChecker(BaseChecker):
    """
    Computes comprehensive text quality metrics using textdescriptives
    or falls back to textstat for basic readability scores.
    """

    CHECKER_NAME = "Text Quality Metrics"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        self.td_available = False
        self.textstat_available = False
        self._init_nlp()

    def _init_nlp(self):
        """Initialize spaCy with textdescriptives pipeline."""
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
            if self.nlp is not None:
                try:
                    import textdescriptives as td
                    # Add textdescriptives components if not already present
                    if 'textdescriptives/readability' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("textdescriptives/readability")
                    if 'textdescriptives/dependency_distance' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("textdescriptives/dependency_distance")
                    if 'textdescriptives/pos_proportions' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("textdescriptives/pos_proportions")
                    if 'textdescriptives/coherence' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("textdescriptives/coherence")
                    if 'textdescriptives/quality' not in self.nlp.pipe_names:
                        self.nlp.add_pipe("textdescriptives/quality")
                    self.td_available = True
                except (ImportError, Exception):
                    self.td_available = False
        except Exception:
            self.nlp = None

        # Textstat fallback
        try:
            import textstat
            self.textstat_available = True
        except ImportError:
            self.textstat_available = False

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        # Use full_text for document-level metrics
        text = full_text if full_text else "\n".join(t for _, t in paragraphs)

        if len(text.strip()) < 100:
            return issues

        if self.td_available and self.nlp is not None:
            issues.extend(self._check_with_textdescriptives(text, paragraphs))
        elif self.textstat_available:
            issues.extend(self._check_with_textstat(text, paragraphs))
        else:
            issues.extend(self._check_basic(text, paragraphs))

        return issues

    def _check_with_textdescriptives(self, text, paragraphs):
        """Full analysis using textdescriptives spaCy component."""
        issues = []
        try:
            # Process in chunks if text is very long
            chunk = text[:50000]  # textdescriptives can be slow on huge texts
            doc = self.nlp(chunk)

            # Extract readability metrics
            metrics = {}
            if hasattr(doc._, 'readability'):
                rd = doc._.readability
                if isinstance(rd, dict):
                    metrics.update(rd)

            # Extract dependency distance metrics
            if hasattr(doc._, 'dependency_distance'):
                dd = doc._.dependency_distance
                if isinstance(dd, dict):
                    metrics['dep_distance_mean'] = dd.get('dependency_distance_mean', None)

            # Extract coherence
            if hasattr(doc._, 'coherence'):
                coh = doc._.coherence
                if isinstance(coh, dict):
                    metrics['coherence_first_order'] = coh.get('first_order_coherence', None)
                    metrics['coherence_second_order'] = coh.get('second_order_coherence', None)

            # Extract POS proportions
            if hasattr(doc._, 'pos_proportions'):
                pos = doc._.pos_proportions
                if isinstance(pos, dict):
                    metrics['noun_ratio'] = pos.get('NOUN', 0)
                    metrics['verb_ratio'] = pos.get('VERB', 0)
                    metrics['adj_ratio'] = pos.get('ADJ', 0)
                    metrics['adv_ratio'] = pos.get('ADV', 0)

            # Quality metrics
            if hasattr(doc._, 'quality'):
                qual = doc._.quality
                if isinstance(qual, dict):
                    metrics.update(qual)

            # Now generate issues based on metrics
            issues.extend(self._evaluate_readability_metrics(metrics))
            issues.extend(self._evaluate_coherence(metrics))
            issues.extend(self._evaluate_pos_proportions(metrics))

        except Exception as e:
            issues.append(ReviewIssue(
                category="Text Metrics",
                severity="Info",
                message=f"Text metrics analysis partially completed (textdescriptives error: {str(e)[:100]})",
                context="",
                paragraph_index=0,
                rule_id="TM-ERR"
            ))

        return issues

    def _check_with_textstat(self, text, paragraphs):
        """Fallback analysis using textstat library."""
        issues = []
        try:
            import textstat

            metrics = {
                'flesch_reading_ease': textstat.flesch_reading_ease(text),
                'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
                'gunning_fog': textstat.gunning_fog(text),
                'smog_index': textstat.smog_index(text),
                'coleman_liau_index': textstat.coleman_liau_index(text),
                'ari': textstat.automated_readability_index(text),
            }

            # Calculate additional metrics manually
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            words = text.split()

            if sentences:
                metrics['avg_sentence_length'] = len(words) / len(sentences)
            if words:
                metrics['avg_word_length'] = sum(len(w) for w in words) / len(words)

            issues.extend(self._evaluate_readability_metrics(metrics))

        except Exception:
            pass

        return issues

    def _check_basic(self, text, paragraphs):
        """Minimal fallback with no external libraries."""
        issues = []
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()

        if not sentences or not words:
            return issues

        avg_sent_len = len(words) / len(sentences)
        avg_word_len = sum(len(w) for w in words) / len(words)

        if avg_sent_len > 35:
            issues.append(ReviewIssue(
                category="Text Metrics",
                severity="Medium",
                message=f"Average sentence length is very high ({avg_sent_len:.1f} words). Technical writing should average 12-25 words per sentence.",
                context="",
                paragraph_index=0,
                suggestion="Break long sentences into shorter, more focused statements.",
                rule_id="TM-SENT"
            ))

        if avg_word_len > 7.0:
            issues.append(ReviewIssue(
                category="Text Metrics",
                severity="Low",
                message=f"Average word length is high ({avg_word_len:.1f} chars). This may indicate overly complex vocabulary.",
                context="",
                paragraph_index=0,
                suggestion="Consider whether simpler terms could replace some multi-syllable words.",
                rule_id="TM-WORD"
            ))

        return issues

    def _evaluate_readability_metrics(self, metrics):
        """Evaluate readability metrics against thresholds."""
        issues = []

        for key, thresholds in METRIC_THRESHOLDS.items():
            value = metrics.get(key)
            if value is None:
                continue

            try:
                value = float(value)
            except (ValueError, TypeError):
                continue

            label = thresholds['label']

            # Flesch Reading Ease is inverse — higher = easier
            if key == 'flesch_reading_ease':
                if value < thresholds['min']:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Medium",
                        message=f"{label}: {value:.1f} — extremely difficult to read. Technical writing should typically score {thresholds['ideal_min']}-{thresholds['ideal_max']}.",
                        context="",
                        paragraph_index=0,
                        suggestion="Simplify sentence structures, reduce syllable count, and break complex sentences.",
                        rule_id=f"TM-{key.upper()}"
                    ))
                elif value > thresholds['max']:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Low",
                        message=f"{label}: {value:.1f} — unusually simple for technical writing. Verify technical precision is maintained.",
                        context="",
                        paragraph_index=0,
                        suggestion="Ensure the document uses appropriate technical terminology.",
                        rule_id=f"TM-{key.upper()}"
                    ))
            else:
                # For grade-level metrics, higher = harder
                if value > thresholds['max']:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Medium",
                        message=f"{label}: {value:.1f} — above recommended range for technical writing ({thresholds['ideal_min']}-{thresholds['ideal_max']}).",
                        context="",
                        paragraph_index=0,
                        suggestion="Consider simplifying sentence structures and using more common terms where precision allows.",
                        rule_id=f"TM-{key.upper()}"
                    ))
                elif value < thresholds['min']:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Low",
                        message=f"{label}: {value:.1f} — below expected range for technical documentation ({thresholds['ideal_min']}-{thresholds['ideal_max']}).",
                        context="",
                        paragraph_index=0,
                        suggestion="Document may be oversimplified for technical audience.",
                        rule_id=f"TM-{key.upper()}"
                    ))

        return issues

    def _evaluate_coherence(self, metrics):
        """Evaluate text coherence metrics."""
        issues = []

        coh1 = metrics.get('coherence_first_order')
        if coh1 is not None:
            try:
                coh1 = float(coh1)
                if coh1 < 0.3:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Medium",
                        message=f"Low first-order coherence ({coh1:.2f}) — adjacent sentences may lack logical flow.",
                        context="",
                        paragraph_index=0,
                        suggestion="Add transition words and ensure each sentence connects logically to the next.",
                        rule_id="TM-COH1"
                    ))
            except (ValueError, TypeError):
                pass

        coh2 = metrics.get('coherence_second_order')
        if coh2 is not None:
            try:
                coh2 = float(coh2)
                if coh2 < 0.2:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Low",
                        message=f"Low second-order coherence ({coh2:.2f}) — paragraphs may not flow logically across sections.",
                        context="",
                        paragraph_index=0,
                        suggestion="Review document structure for logical progression of ideas.",
                        rule_id="TM-COH2"
                    ))
            except (ValueError, TypeError):
                pass

        return issues

    def _evaluate_pos_proportions(self, metrics):
        """Evaluate POS distribution for technical writing quality."""
        issues = []

        noun_ratio = metrics.get('noun_ratio')
        verb_ratio = metrics.get('verb_ratio')

        if noun_ratio is not None and verb_ratio is not None:
            try:
                noun_ratio = float(noun_ratio)
                verb_ratio = float(verb_ratio)

                # High noun-to-verb ratio indicates nominalization (dense, hard to read)
                if verb_ratio > 0 and noun_ratio / verb_ratio > 4.0:
                    issues.append(ReviewIssue(
                        category="Text Metrics",
                        severity="Low",
                        message=f"High noun-to-verb ratio ({noun_ratio/verb_ratio:.1f}:1) — text may be overly nominalized and dense.",
                        context="",
                        paragraph_index=0,
                        suggestion="Consider converting noun phrases back to verb forms. Example: 'perform an investigation' → 'investigate'.",
                        rule_id="TM-NV"
                    ))
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        return issues


class SentenceComplexityChecker(BaseChecker):
    """
    Analyzes syntactic complexity using dependency tree depth.
    A 15-word sentence can be harder than a 25-word one if deeply nested.
    """

    CHECKER_NAME = "Sentence Complexity"
    CHECKER_VERSION = "1.0.0"

    MAX_TREE_DEPTH = 8  # Sentences with parse tree deeper than this are flagged
    MAX_CLAUSES = 4     # Sentences with more than this many clausal complements

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.nlp = None
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
        except Exception:
            pass

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        if self.nlp is None:
            return issues

        for idx, text in paragraphs:
            if self.is_boilerplate(text) or len(text.strip()) < 20:
                continue

            try:
                doc = self.nlp(text[:5000])

                for sent in doc.sents:
                    if len(list(sent)) < 5:
                        continue

                    # Calculate tree depth
                    depth = self._tree_depth(sent.root)

                    # Count clausal complements
                    clauses = sum(1 for tok in sent if tok.dep_ in (
                        'ccomp', 'xcomp', 'advcl', 'relcl', 'acl'
                    ))

                    if depth > self.MAX_TREE_DEPTH:
                        issues.append(ReviewIssue(
                            category="Sentence Complexity",
                            severity="Medium",
                            message=f"Deeply nested sentence (tree depth: {depth}) — may be difficult to parse. Consider restructuring.",
                            context=sent.text[:200],
                            paragraph_index=idx,
                            suggestion="Break into shorter sentences or reduce embedding depth by pulling out subordinate clauses.",
                            rule_id="SC-DEPTH",
                            flagged_text=sent.text[:100]
                        ))

                    if clauses > self.MAX_CLAUSES:
                        issues.append(ReviewIssue(
                            category="Sentence Complexity",
                            severity="Medium",
                            message=f"Sentence has {clauses} dependent clauses — cognitive load is high.",
                            context=sent.text[:200],
                            paragraph_index=idx,
                            suggestion="Split into multiple sentences, each containing one main idea.",
                            rule_id="SC-CLAUSE",
                            flagged_text=sent.text[:100]
                        ))

            except Exception:
                continue

        return issues

    def _tree_depth(self, token, current_depth=0):
        """Calculate the maximum depth of a dependency tree."""
        children = list(token.children)
        if not children:
            return current_depth
        return max(self._tree_depth(child, current_depth + 1) for child in children)


def get_text_metrics_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning all text metrics checkers."""
    return {
        'text_quality_metrics': TextMetricsChecker(),
        'sentence_complexity': SentenceComplexityChecker(),
    }
