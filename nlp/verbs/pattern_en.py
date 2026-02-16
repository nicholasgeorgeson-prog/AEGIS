"""
Verb Analyzer for AEGIS
==================================
Provides verb tense detection and conjugation analysis.

Uses multiple backends:
1. pattern.en (if available)
2. spaCy (fallback)
3. NLTK + heuristics (final fallback)

Features:
- Verb tense detection (past, present, future)
- Base form extraction (lemmatization)
- Tense consistency analysis
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from ..base import NLPIntegrationBase


@dataclass
class TenseAnalysis:
    """Result of tense consistency analysis."""
    dominant_tense: str = ""
    tense_distribution: Dict[str, int] = field(default_factory=dict)
    inconsistencies: List[Dict] = field(default_factory=list)
    total_verbs: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'dominant_tense': self.dominant_tense,
            'tense_distribution': self.tense_distribution,
            'inconsistencies': self.inconsistencies,
            'total_verbs': self.total_verbs,
        }


class VerbAnalyzer(NLPIntegrationBase):
    """
    Verb analysis with multiple backend support.

    Provides tense detection and consistency checking.
    Falls back through pattern.en -> spaCy -> NLTK/heuristics.
    """

    INTEGRATION_NAME = "VerbAnalyzer"
    INTEGRATION_VERSION = "1.0.0"

    # Common irregular verbs with tense mappings
    IRREGULAR_VERBS = {
        # past -> base
        'was': ('be', 'past'), 'were': ('be', 'past'),
        'had': ('have', 'past'), 'did': ('do', 'past'),
        'went': ('go', 'past'), 'came': ('come', 'past'),
        'saw': ('see', 'past'), 'made': ('make', 'past'),
        'said': ('say', 'past'), 'took': ('take', 'past'),
        'got': ('get', 'past'), 'gave': ('give', 'past'),
        'found': ('find', 'past'), 'thought': ('think', 'past'),
        'told': ('tell', 'past'), 'became': ('become', 'past'),
        'left': ('leave', 'past'), 'felt': ('feel', 'past'),
        'brought': ('bring', 'past'), 'began': ('begin', 'past'),
        'kept': ('keep', 'past'), 'held': ('hold', 'past'),
        'wrote': ('write', 'past'), 'stood': ('stand', 'past'),
        'heard': ('hear', 'past'), 'let': ('let', 'past'),
        'meant': ('mean', 'past'), 'set': ('set', 'past'),
        'met': ('meet', 'past'), 'ran': ('run', 'past'),
        'paid': ('pay', 'past'), 'sat': ('sit', 'past'),
        'spoke': ('speak', 'past'), 'lay': ('lie', 'past'),
        'led': ('lead', 'past'), 'read': ('read', 'past'),
        'grew': ('grow', 'past'), 'lost': ('lose', 'past'),
        'knew': ('know', 'past'), 'sent': ('send', 'past'),
        'built': ('build', 'past'), 'fell': ('fall', 'past'),
        'cut': ('cut', 'past'), 'put': ('put', 'past'),
        # present -> base
        'is': ('be', 'present'), 'am': ('be', 'present'), 'are': ('be', 'present'),
        'has': ('have', 'present'), 'does': ('do', 'present'),
        'goes': ('go', 'present'), 'comes': ('come', 'present'),
        'sees': ('see', 'present'), 'makes': ('make', 'present'),
        'says': ('say', 'present'), 'takes': ('take', 'present'),
        'gets': ('get', 'present'), 'gives': ('give', 'present'),
    }

    # Verb endings that indicate tense
    PAST_ENDINGS = ('ed', 'ought', 'ught')
    PRESENT_ENDINGS = ('s', 'es', 'ing')
    FUTURE_MARKERS = ('will', 'shall', "'ll", 'going to')

    def __init__(self):
        """Initialize the verb analyzer."""
        super().__init__()
        self._backend = None
        self._spacy_nlp = None
        self._initialize()

    def _initialize(self):
        """Initialize with best available backend."""
        # Try pattern.en first
        try:
            from pattern.en import tenses, lemma, conjugate
            self._backend = 'pattern'
            self._pattern_tenses = tenses
            self._pattern_lemma = lemma
            self._pattern_conjugate = conjugate
            self._available = True
            return
        except ImportError:
            pass
        except Exception:
            pass

        # Try spaCy as fallback
        try:
            import spacy
            try:
                self._spacy_nlp = spacy.load('en_core_web_md')
            except OSError:
                try:
                    self._spacy_nlp = spacy.load('en_core_web_sm')
                except OSError:
                    pass

            if self._spacy_nlp:
                self._backend = 'spacy'
                self._available = True
                return
        except ImportError:
            pass

        # Use heuristics as final fallback
        self._backend = 'heuristics'
        self._available = True

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the verb analyzer."""
        return {
            'available': self.is_available,
            'backend': self._backend,
            'error': self._error,
            'features': ['tense_detection', 'consistency_analysis']
        }

    def get_verb_tense(self, verb: str) -> List[Tuple[str, ...]]:
        """
        Get the tense(s) of a verb.

        Args:
            verb: Verb to analyze

        Returns:
            List of tense tuples
        """
        if not self.is_available:
            return []

        verb_lower = verb.lower()

        # Check irregular verbs first
        if verb_lower in self.IRREGULAR_VERBS:
            base, tense = self.IRREGULAR_VERBS[verb_lower]
            return [(tense,)]

        if self._backend == 'pattern':
            try:
                return list(self._pattern_tenses(verb))
            except Exception:
                pass

        if self._backend == 'spacy' and self._spacy_nlp:
            try:
                doc = self._spacy_nlp(verb)
                for token in doc:
                    if token.pos_ == 'VERB':
                        tag = token.tag_
                        if tag in ('VBD', 'VBN'):  # Past tense, past participle
                            return [('past',)]
                        elif tag in ('VBZ', 'VBP', 'VBG'):  # Present forms
                            return [('present',)]
                        elif tag == 'VB':  # Base form
                            return [('infinitive',)]
            except Exception:
                pass

        # Heuristic fallback
        return self._heuristic_tense(verb_lower)

    def _heuristic_tense(self, verb: str) -> List[Tuple[str, ...]]:
        """Determine tense using heuristics."""
        # Past tense indicators
        if verb.endswith('ed') and len(verb) > 3:
            return [('past',)]

        # Present tense indicators (3rd person singular)
        if verb.endswith(('s', 'es')) and len(verb) > 2:
            if not verb.endswith(('ss', 'us', 'is')):  # Exclude nouns
                return [('present',)]

        # Progressive (-ing)
        if verb.endswith('ing') and len(verb) > 4:
            return [('present',)]

        return []

    def get_base_form(self, verb: str) -> str:
        """
        Get the infinitive/base form of a verb.

        Args:
            verb: Verb to lemmatize

        Returns:
            Base form of the verb
        """
        verb_lower = verb.lower()

        # Check irregular verbs
        if verb_lower in self.IRREGULAR_VERBS:
            return self.IRREGULAR_VERBS[verb_lower][0]

        if self._backend == 'pattern':
            try:
                return self._pattern_lemma(verb)
            except Exception:
                pass

        if self._backend == 'spacy' and self._spacy_nlp:
            try:
                doc = self._spacy_nlp(verb)
                for token in doc:
                    if token.pos_ == 'VERB':
                        return token.lemma_
            except Exception:
                pass

        # Heuristic lemmatization
        if verb_lower.endswith('ed') and len(verb_lower) > 3:
            # walked -> walk, studied -> study
            if verb_lower.endswith('ied'):
                return verb_lower[:-3] + 'y'
            elif verb_lower[-3] == verb_lower[-4] and verb_lower[-3] not in 'aeiou':
                # stopped -> stop
                return verb_lower[:-3]
            else:
                return verb_lower[:-2] if not verb_lower.endswith('eed') else verb_lower[:-1]

        if verb_lower.endswith('ing') and len(verb_lower) > 4:
            # running -> run, walking -> walk
            base = verb_lower[:-3]
            if len(base) > 1 and base[-1] == base[-2]:
                return base[:-1]
            return base + 'e' if base.endswith(('ak', 'av', 'iz', 'rit')) else base

        if verb_lower.endswith('s') and len(verb_lower) > 2:
            if verb_lower.endswith('ies'):
                return verb_lower[:-3] + 'y'
            elif verb_lower.endswith('es'):
                return verb_lower[:-2]
            else:
                return verb_lower[:-1]

        return verb

    def analyze_tense_consistency(self, text: str) -> TenseAnalysis:
        """
        Analyze tense consistency across sentences in text.

        Args:
            text: Text to analyze

        Returns:
            TenseAnalysis with dominant tense and inconsistencies
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return TenseAnalysis()

        tense_counts = {'past': 0, 'present': 0, 'future': 0}
        inconsistencies = []
        total_verbs = 0

        for i, sent in enumerate(sentences):
            # Check for future markers
            sent_lower = sent.lower()
            has_future = any(marker in sent_lower for marker in self.FUTURE_MARKERS)

            # Extract words
            words = re.findall(r'\b[a-zA-Z]+\b', sent_lower)

            sent_tenses: Set[str] = set()
            sent_verb_count = 0

            if has_future:
                sent_tenses.add('future')
                tense_counts['future'] += 1
                sent_verb_count += 1
                total_verbs += 1

            for word in words:
                # Skip common non-verbs
                if len(word) < 2 or word in ('the', 'a', 'an', 'is', 'are', 'to'):
                    continue

                tenses = self.get_verb_tense(word)
                for t in tenses:
                    if t and len(t) > 0:
                        tense_name = t[0]
                        if tense_name in ('past', 'present', 'future'):
                            sent_tenses.add(tense_name)
                            tense_counts[tense_name] += 1
                            sent_verb_count += 1
                            total_verbs += 1

            # Check for mixed tenses in single sentence
            if len(sent_tenses) > 1:
                inconsistencies.append({
                    'sentence_index': i,
                    'sentence': sent[:100] + ('...' if len(sent) > 100 else ''),
                    'tenses_found': list(sent_tenses),
                    'verb_count': sent_verb_count
                })

        # Determine dominant tense
        if sum(tense_counts.values()) > 0:
            dominant = max(tense_counts, key=tense_counts.get)
        else:
            dominant = 'unknown'

        return TenseAnalysis(
            dominant_tense=dominant,
            tense_distribution=tense_counts,
            inconsistencies=inconsistencies,
            total_verbs=total_verbs
        )

    def get_tense_name(self, verb: str) -> Optional[str]:
        """
        Get the primary tense name for a verb.

        Args:
            verb: Verb to analyze

        Returns:
            Tense name ('past', 'present', 'future') or None
        """
        tenses = self.get_verb_tense(verb)
        if tenses:
            for t in tenses:
                if t and len(t) > 0:
                    if t[0] in ('past', 'present', 'future', 'infinitive'):
                        return t[0]
        return None
