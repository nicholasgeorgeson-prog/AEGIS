"""
spaCy Analyzer for AEGIS
===================================
Provides linguistic analysis using spaCy NLP.

Features:
- Lazy model loading
- Air-gap compatible (offline models)
- Dependency parsing
- Named Entity Recognition
- Sentence boundary detection
- Subject-verb pair extraction
- Dangling modifier detection
- Sentence complexity analysis

Requires: pip install spacy && python -m spacy download en_core_web_md
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from ..base import NLPIntegrationBase


@dataclass
class SpacyAnalysis:
    """Result of spaCy document analysis."""
    sentences: List[str] = field(default_factory=list)
    tokens: List[Dict] = field(default_factory=list)  # text, pos, dep, head, lemma
    entities: List[Dict] = field(default_factory=list)  # text, label, start, end
    noun_chunks: List[str] = field(default_factory=list)
    dependency_trees: List[Dict] = field(default_factory=list)


@dataclass
class SubjectVerbPair:
    """A subject-verb pair found in text."""
    subject: str
    verb: str
    subject_number: str  # 'singular' or 'plural'
    verb_number: str  # 'singular' or 'plural'
    sentence: str
    sentence_index: int
    is_agreement_error: bool = False


@dataclass
class DanglingModifier:
    """A potential dangling modifier found in text."""
    modifier: str
    expected_subject: str
    actual_subject: str
    sentence: str
    sentence_index: int
    confidence: float = 0.8


@dataclass
class SentenceComplexity:
    """Complexity metrics for a sentence."""
    sentence: str
    sentence_index: int
    word_count: int
    clause_count: int
    max_depth: int
    subordinate_clauses: int
    is_complex: bool = False
    complexity_score: float = 0.0


class SpacyAnalyzer(NLPIntegrationBase):
    """
    spaCy-based linguistic analysis for AEGIS.

    Designed for air-gapped operation with local models.
    """

    INTEGRATION_NAME = "spaCy"
    INTEGRATION_VERSION = "1.0.0"

    # Model preference order (try medium first for balance of speed/accuracy)
    DEFAULT_MODEL = "en_core_web_md"
    FALLBACK_MODELS = ["en_core_web_sm", "en_core_web_lg"]

    # Complexity thresholds
    MAX_WORDS_PER_SENTENCE = 40
    MAX_CLAUSE_DEPTH = 4
    MAX_SUBORDINATE_CLAUSES = 3

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize SpacyAnalyzer with specified or default model.

        Args:
            model_name: spaCy model to load (e.g., 'en_core_web_md')
        """
        super().__init__()
        self.model_name = model_name or self.DEFAULT_MODEL
        self._nlp = None
        self._load_model()

    def _load_model(self):
        """Load spaCy model with fallback support."""
        try:
            import spacy
            self._spacy = spacy
        except ImportError:
            self._error = "spaCy not installed. Run: pip install spacy"
            return

        # Try primary model
        models_to_try = [self.model_name] + [
            m for m in self.FALLBACK_MODELS if m != self.model_name
        ]

        for model in models_to_try:
            try:
                self._nlp = self._spacy.load(model)
                self.model_name = model
                self._available = True
                return
            except OSError:
                continue

        self._error = (
            "No spaCy model found. Install with: "
            "python -m spacy download en_core_web_md"
        )

    @property
    def is_available(self) -> bool:
        """Check if spaCy is available and model is loaded."""
        return self._available and self._nlp is not None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the spaCy integration."""
        status = {
            'available': self.is_available,
            'model': self.model_name if self.is_available else None,
            'version': self._spacy.__version__ if self._available else None,
            'error': self._error,
        }

        if self.is_available:
            status['pipeline'] = list(self._nlp.pipe_names)
            status['vocab_size'] = len(self._nlp.vocab)

        return status

    def analyze(self, text: str) -> SpacyAnalysis:
        """
        Perform full linguistic analysis on text.

        Args:
            text: The text to analyze

        Returns:
            SpacyAnalysis with sentences, tokens, entities, noun chunks
        """
        if not self.is_available:
            return SpacyAnalysis()

        doc = self._nlp(text)

        return SpacyAnalysis(
            sentences=[sent.text for sent in doc.sents],
            tokens=[
                {
                    'text': token.text,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'dep': token.dep_,
                    'head': token.head.text,
                    'lemma': token.lemma_,
                    'is_stop': token.is_stop,
                }
                for token in doc
            ],
            entities=[
                {
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                }
                for ent in doc.ents
            ],
            noun_chunks=[chunk.text for chunk in doc.noun_chunks],
            dependency_trees=[
                self._build_dep_tree(sent) for sent in doc.sents
            ]
        )

    def _build_dep_tree(self, sent) -> Dict:
        """Build a dependency tree structure for a sentence."""
        root = [token for token in sent if token.dep_ == 'ROOT']
        if not root:
            return {}

        root_token = root[0]
        return {
            'text': root_token.text,
            'pos': root_token.pos_,
            'dep': root_token.dep_,
            'children': [self._build_subtree(child) for child in root_token.children]
        }

    def _build_subtree(self, token) -> Dict:
        """Recursively build subtree for a token."""
        return {
            'text': token.text,
            'pos': token.pos_,
            'dep': token.dep_,
            'children': [self._build_subtree(child) for child in token.children]
        }

    def find_subject_verb_pairs(self, text: str) -> List[SubjectVerbPair]:
        """
        Find subject-verb pairs and check for agreement errors.

        Uses dependency parsing to identify nominal subjects (nsubj)
        and their governing verbs, then checks number agreement.

        Args:
            text: Text to analyze

        Returns:
            List of SubjectVerbPair objects
        """
        if not self.is_available:
            return []

        doc = self._nlp(text)
        pairs = []

        for sent_idx, sent in enumerate(doc.sents):
            for token in sent:
                # Find subjects
                if token.dep_ in ('nsubj', 'nsubjpass'):
                    verb = token.head

                    # Get number from morphology
                    subject_number = self._get_number(token)
                    verb_number = self._get_verb_number(verb)

                    # Check for agreement error
                    is_error = (
                        subject_number in ('singular', 'plural') and
                        verb_number in ('singular', 'plural') and
                        subject_number != verb_number
                    )

                    pairs.append(SubjectVerbPair(
                        subject=token.text,
                        verb=verb.text,
                        subject_number=subject_number,
                        verb_number=verb_number,
                        sentence=sent.text,
                        sentence_index=sent_idx,
                        is_agreement_error=is_error
                    ))

        return pairs

    def _get_number(self, token) -> str:
        """Get grammatical number from token morphology."""
        morph = token.morph.to_dict()
        number = morph.get('Number', '')

        if number == 'Sing':
            return 'singular'
        elif number == 'Plur':
            return 'plural'

        # Heuristic fallback for nouns
        if token.pos_ == 'NOUN':
            if token.text.endswith('s') and not token.text.endswith('ss'):
                return 'plural'
            return 'singular'

        return 'unknown'

    def _get_verb_number(self, token) -> str:
        """Get grammatical number from verb morphology."""
        morph = token.morph.to_dict()
        number = morph.get('Number', '')

        if number == 'Sing':
            return 'singular'
        elif number == 'Plur':
            return 'plural'

        # Heuristic for common verb forms
        if token.tag_ == 'VBZ':  # 3rd person singular present
            return 'singular'
        elif token.tag_ == 'VBP':  # Non-3rd person singular present
            return 'plural'

        return 'unknown'

    def find_dangling_modifiers(self, text: str) -> List[DanglingModifier]:
        """
        Detect potential dangling modifiers using parse tree analysis.

        A dangling modifier occurs when a participial phrase doesn't
        logically modify the subject of the main clause.

        Args:
            text: Text to analyze

        Returns:
            List of DanglingModifier objects
        """
        if not self.is_available:
            return []

        doc = self._nlp(text)
        modifiers = []

        for sent_idx, sent in enumerate(doc.sents):
            tokens = list(sent)
            if not tokens:
                continue

            # Check for sentence-initial participial phrases
            first_token = tokens[0]

            # Look for -ing or -ed forms at sentence start
            if first_token.tag_ in ('VBG', 'VBN'):
                # Find the main subject
                main_subject = None
                for token in sent:
                    if token.dep_ == 'nsubj':
                        main_subject = token
                        break

                if main_subject:
                    # Get the implied subject of the participle
                    participle_phrase = self._get_phrase(first_token)

                    # Check if there's a mismatch
                    # (simplified heuristic - real analysis would be more complex)
                    if self._is_potential_dangle(first_token, main_subject, sent):
                        modifiers.append(DanglingModifier(
                            modifier=participle_phrase,
                            expected_subject="(implied agent of action)",
                            actual_subject=main_subject.text,
                            sentence=sent.text,
                            sentence_index=sent_idx,
                            confidence=0.7
                        ))

        return modifiers

    def _get_phrase(self, token) -> str:
        """Get the full phrase headed by a token."""
        phrase_tokens = [token]
        for child in token.children:
            if child.dep_ in ('advmod', 'dobj', 'prep', 'pobj', 'aux'):
                phrase_tokens.append(child)
                for grandchild in child.children:
                    phrase_tokens.append(grandchild)

        phrase_tokens.sort(key=lambda t: t.i)
        return ' '.join(t.text for t in phrase_tokens)

    def _is_potential_dangle(self, participle, subject, sent) -> bool:
        """
        Check if a participle potentially dangles.

        This is a simplified heuristic. Real dangling modifier detection
        requires semantic analysis.
        """
        # If the participle has no direct object and the subject is
        # inanimate or abstract, it might be a dangle
        participle_has_object = any(
            child.dep_ in ('dobj', 'pobj') for child in participle.children
        )

        # Check for common inanimate subject indicators
        inanimate_indicators = {'it', 'this', 'that', 'the'}
        subject_text = subject.text.lower()

        # If subject is pronoun 'it' or determiner-led, potential dangle
        if subject_text in inanimate_indicators:
            return True

        # If participle phrase has no object, more likely to dangle
        if not participle_has_object:
            return True

        return False

    def analyze_sentence_complexity(self, text: str) -> List[SentenceComplexity]:
        """
        Analyze sentence complexity using linguistic features.

        Measures:
        - Word count
        - Clause count (via conjunctions and relative pronouns)
        - Maximum dependency depth
        - Subordinate clause count

        Args:
            text: Text to analyze

        Returns:
            List of SentenceComplexity objects
        """
        if not self.is_available:
            return []

        doc = self._nlp(text)
        results = []

        for sent_idx, sent in enumerate(doc.sents):
            tokens = list(sent)
            word_count = len([t for t in tokens if not t.is_punct])

            # Count clauses via clause-introducing elements
            clause_count = 1  # Main clause
            subordinate_count = 0

            for token in sent:
                # Subordinating conjunctions
                if token.dep_ == 'mark':
                    subordinate_count += 1
                    clause_count += 1
                # Coordinating conjunctions before verbs
                elif token.dep_ == 'cc' and any(
                    child.pos_ == 'VERB' for child in token.head.children
                ):
                    clause_count += 1
                # Relative pronouns
                elif token.dep_ == 'relcl':
                    subordinate_count += 1
                    clause_count += 1

            # Calculate max dependency depth
            max_depth = self._max_dep_depth(sent.root, 0)

            # Calculate complexity score (0-1)
            complexity_score = min(1.0, (
                (word_count / self.MAX_WORDS_PER_SENTENCE) * 0.4 +
                (max_depth / self.MAX_CLAUSE_DEPTH) * 0.3 +
                (subordinate_count / self.MAX_SUBORDINATE_CLAUSES) * 0.3
            ))

            is_complex = (
                word_count > self.MAX_WORDS_PER_SENTENCE or
                max_depth > self.MAX_CLAUSE_DEPTH or
                subordinate_count > self.MAX_SUBORDINATE_CLAUSES
            )

            results.append(SentenceComplexity(
                sentence=sent.text,
                sentence_index=sent_idx,
                word_count=word_count,
                clause_count=clause_count,
                max_depth=max_depth,
                subordinate_clauses=subordinate_count,
                is_complex=is_complex,
                complexity_score=complexity_score
            ))

        return results

    def _max_dep_depth(self, token, current_depth: int) -> int:
        """Calculate maximum dependency tree depth from a token."""
        children = list(token.children)
        if not children:
            return current_depth
        return max(self._max_dep_depth(child, current_depth + 1) for child in children)

    def extract_entities_for_roles(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities grouped by their semantic roles.

        Useful for technical writing to identify people, organizations,
        products, and technical terms mentioned.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping entity types to lists of entity texts
        """
        if not self.is_available:
            return {}

        doc = self._nlp(text)
        entities_by_type = {}

        for ent in doc.ents:
            label = ent.label_
            if label not in entities_by_type:
                entities_by_type[label] = []
            if ent.text not in entities_by_type[label]:
                entities_by_type[label].append(ent.text)

        return entities_by_type
