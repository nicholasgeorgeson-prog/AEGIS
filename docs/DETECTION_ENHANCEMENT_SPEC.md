# AEGIS Detection Enhancement Specification

**Version:** 1.0.0
**Date:** 2026-02-01
**Status:** Draft

---

## Executive Summary

This document provides detailed technical specifications for enhancing AEGIS's document detection capabilities using non-LLM NLP tools. Each tool integration is designed to fill specific gaps in the current detection system without duplicating existing functionality.

---

## Current Capability Analysis

### What Already Exists

| Capability | Current Implementation | Coverage Level |
|------------|----------------------|----------------|
| Spelling | 100-word misspelling dictionary | Basic |
| Grammar | 15+ regex patterns | Limited |
| Readability | 7 metrics (Flesch, Fog, etc.) | Good |
| Weak Language | 150+ words with severity | Good |
| Wordy Phrases | 100+ phrase replacements | Good |
| Passive Voice | 4 pattern types | Good |
| Acronyms | 900+ word allowlists | Extensive |
| Requirements | SHALL/SHOULD detection | Good |
| Pronouns | Basic heuristic patterns | Limited |
| Sentence Structure | Regex-based fragment/run-on | Basic |

### Identified Gaps

1. **No linguistic parsing** - All detection is regex/dictionary-based
2. **No verb tense analysis** - No consistency checking across document
3. **No semantic analysis** - No synonym/meaning understanding
4. **No phonetic spelling** - Can't catch typos like "definately"
5. **No true coreference** - Pronoun detection is heuristic only
6. **No entity recognition** - Roles/systems not automatically extracted
7. **No domain dictionaries** - Can't customize for aerospace/defense
8. **Limited grammar depth** - Only common patterns, not linguistic rules

---

## Tool Integration Specifications

---

## 1. spaCy Integration

### Purpose
Add linguistic foundation for sentence parsing, dependency analysis, NER, and improved text understanding.

### What It Adds (Not Currently in Tool)
- ✅ **Dependency parsing** - Understand grammatical relationships
- ✅ **True sentence boundaries** - Better than period-splitting
- ✅ **Part-of-speech tagging** - Linguistic analysis not regex
- ✅ **Named Entity Recognition** - Detect ORG, PERSON, GPE, etc.
- ✅ **Lemmatization** - Normalize word forms properly
- ✅ **Noun phrase extraction** - Identify subject/object chunks

### What It Replaces/Enhances
| Current | Enhancement |
|---------|-------------|
| Regex sentence splitting | spaCy sentence boundaries |
| Heuristic pronoun detection | Dependency-based antecedent analysis |
| Pattern-based dangling modifiers | Dependency tree analysis |
| Regex subject-verb matching | POS + dependency agreement |

### Technical Specification

```python
# New module: spacy_integration.py

import spacy
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SpacyAnalysis:
    """Result of spaCy document analysis."""
    sentences: List[str]
    tokens: List[Dict]  # text, pos, dep, head, lemma
    entities: List[Dict]  # text, label, start, end
    noun_chunks: List[str]
    dependency_trees: List[Dict]

class SpacyAnalyzer:
    """
    spaCy-based linguistic analysis for AEGIS.

    Designed for air-gapped operation with local models.
    """

    # Use medium model for balance of speed/accuracy
    # Download with: python -m spacy download en_core_web_md
    DEFAULT_MODEL = "en_core_web_md"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._nlp = None
        self._load_model()

    def _load_model(self):
        """Load spaCy model with error handling."""
        try:
            self._nlp = spacy.load(self.model_name)
        except OSError:
            # Fallback to small model if medium not available
            try:
                self._nlp = spacy.load("en_core_web_sm")
                self.model_name = "en_core_web_sm"
            except OSError:
                raise RuntimeError(
                    "No spaCy model found. Install with: "
                    "python -m spacy download en_core_web_md"
                )

    def analyze(self, text: str) -> SpacyAnalysis:
        """Perform full linguistic analysis on text."""
        doc = self._nlp(text)

        return SpacyAnalysis(
            sentences=[sent.text for sent in doc.sents],
            tokens=[{
                'text': token.text,
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'head': token.head.text,
                'lemma': token.lemma_,
                'is_stop': token.is_stop
            } for token in doc],
            entities=[{
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            } for ent in doc.ents],
            noun_chunks=[chunk.text for chunk in doc.noun_chunks],
            dependency_trees=self._build_dep_trees(doc)
        )

    def _build_dep_trees(self, doc) -> List[Dict]:
        """Build dependency trees for each sentence."""
        trees = []
        for sent in doc.sents:
            tree = {
                'root': sent.root.text,
                'root_pos': sent.root.pos_,
                'children': self._get_children(sent.root)
            }
            trees.append(tree)
        return trees

    def _get_children(self, token, depth=0, max_depth=5) -> List[Dict]:
        """Recursively get token children."""
        if depth >= max_depth:
            return []
        return [{
            'text': child.text,
            'dep': child.dep_,
            'pos': child.pos_,
            'children': self._get_children(child, depth + 1, max_depth)
        } for child in token.children]

    # === CHECKER INTEGRATION METHODS ===

    def find_subject_verb_pairs(self, text: str) -> List[Tuple[str, str, bool]]:
        """
        Find subject-verb pairs and check agreement.

        Returns: List of (subject, verb, is_agreement_correct)
        """
        doc = self._nlp(text)
        pairs = []

        for token in doc:
            if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                subject = token.text
                verb = token.head.text

                # Check number agreement
                subj_number = "plural" if token.tag_ in ("NNS", "NNPS") else "singular"
                verb_number = self._get_verb_number(token.head)

                agrees = (subj_number == verb_number) or verb_number == "neutral"
                pairs.append((subject, verb, agrees))

        return pairs

    def _get_verb_number(self, verb_token) -> str:
        """Determine verb number from tag."""
        tag = verb_token.tag_
        if tag == "VBZ":  # 3rd person singular (runs, is)
            return "singular"
        elif tag == "VBP":  # Non-3rd person (run, are)
            return "plural"
        return "neutral"

    def find_dangling_modifiers(self, text: str) -> List[Dict]:
        """
        Detect dangling modifiers using dependency parsing.

        Returns issues where participial phrase doesn't attach to correct subject.
        """
        doc = self._nlp(text)
        issues = []

        for sent in doc.sents:
            # Look for sentence-initial participial phrases
            tokens = list(sent)
            if len(tokens) < 3:
                continue

            # Check if starts with VBG (gerund/present participle)
            if tokens[0].tag_ == "VBG":
                # Find the main subject
                main_subject = None
                for token in tokens:
                    if token.dep_ == "nsubj":
                        main_subject = token
                        break

                if main_subject:
                    # Check if subject could logically perform the action
                    # Inanimate subjects with -ing phrases are often dangling
                    if main_subject.ent_type_ not in ("PERSON", "ORG") and \
                       main_subject.text.lower() in self._inanimate_subjects():
                        issues.append({
                            'sentence': sent.text,
                            'modifier': tokens[0].text,
                            'subject': main_subject.text,
                            'message': f'Dangling modifier: "{tokens[0].text}" may not '
                                      f'correctly modify "{main_subject.text}"'
                        })

        return issues

    def _inanimate_subjects(self) -> set:
        """Common inanimate subjects that can't perform actions."""
        return {
            'system', 'data', 'document', 'report', 'table', 'figure',
            'section', 'requirement', 'process', 'procedure', 'result',
            'analysis', 'test', 'software', 'hardware', 'equipment',
            'interface', 'component', 'module', 'function', 'file'
        }

    def extract_entities_for_roles(self, text: str) -> List[Dict]:
        """
        Extract named entities relevant for role detection.

        Enhances existing role extraction with NER.
        """
        doc = self._nlp(text)

        role_entities = []
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PERSON", "GPE", "NORP"):
                role_entities.append({
                    'text': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'context': text[max(0, ent.start_char-50):ent.end_char+50]
                })

        return role_entities

    def analyze_sentence_complexity(self, text: str) -> List[Dict]:
        """
        Analyze sentence complexity using dependency depth and clause count.
        """
        doc = self._nlp(text)
        results = []

        for sent in doc.sents:
            # Calculate max dependency depth
            max_depth = self._max_dep_depth(sent.root)

            # Count clauses (verbs with subjects)
            clause_count = sum(1 for t in sent if t.dep_ == "nsubj")

            # Count coordination
            coord_count = sum(1 for t in sent if t.dep_ == "cc")

            results.append({
                'sentence': sent.text,
                'word_count': len([t for t in sent if not t.is_space]),
                'max_dep_depth': max_depth,
                'clause_count': clause_count,
                'coordination_count': coord_count,
                'is_complex': max_depth > 6 or clause_count > 3
            })

        return results

    def _max_dep_depth(self, token, current_depth=0) -> int:
        """Calculate maximum dependency tree depth."""
        if not list(token.children):
            return current_depth
        return max(self._max_dep_depth(child, current_depth + 1)
                   for child in token.children)
```

### New Checkers Using spaCy

```python
# New file: spacy_checkers.py

from base_checker import BaseChecker
from spacy_integration import SpacyAnalyzer

class EnhancedSubjectVerbChecker(BaseChecker):
    """
    Enhanced subject-verb agreement using spaCy dependency parsing.

    Replaces simple regex patterns with linguistic analysis.
    """

    CHECKER_NAME = "Subject-Verb Agreement (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._analyzer = None

    def _get_analyzer(self):
        if self._analyzer is None:
            self._analyzer = SpacyAnalyzer()
        return self._analyzer

    def check(self, paragraphs, **kwargs):
        if not self.enabled:
            return []

        issues = []
        analyzer = self._get_analyzer()

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            pairs = analyzer.find_subject_verb_pairs(text)

            for subject, verb, agrees in pairs:
                if not agrees:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Subject-verb disagreement: "{subject}" with "{verb}"',
                        paragraph_index=idx,
                        context=f'"{subject} ... {verb}"',
                        suggestion='Ensure subject and verb agree in number',
                        rule_id='SVA001'
                    ))

        return issues


class EnhancedDanglingModifierChecker(BaseChecker):
    """
    Detect dangling modifiers using dependency parsing.

    More accurate than regex pattern matching.
    """

    CHECKER_NAME = "Dangling Modifiers (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._analyzer = None

    def _get_analyzer(self):
        if self._analyzer is None:
            self._analyzer = SpacyAnalyzer()
        return self._analyzer

    def check(self, paragraphs, **kwargs):
        if not self.enabled:
            return []

        issues = []
        analyzer = self._get_analyzer()

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 20:
                continue

            danglers = analyzer.find_dangling_modifiers(text)

            for dangler in danglers:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=dangler['message'],
                    paragraph_index=idx,
                    context=dangler['sentence'][:100],
                    suggestion='Ensure the modifier clearly refers to the correct subject',
                    rule_id='DM001'
                ))

        return issues


class SentenceComplexityChecker(BaseChecker):
    """
    Analyze sentence complexity using linguistic metrics.

    NEW capability - not currently in tool.
    """

    CHECKER_NAME = "Sentence Complexity"
    CHECKER_VERSION = "1.0.0"

    # Thresholds
    MAX_WORDS = 40
    MAX_CLAUSES = 3
    MAX_DEP_DEPTH = 7

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._analyzer = None

    def _get_analyzer(self):
        if self._analyzer is None:
            self._analyzer = SpacyAnalyzer()
        return self._analyzer

    def check(self, paragraphs, **kwargs):
        if not self.enabled:
            return []

        issues = []
        analyzer = self._get_analyzer()

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 30:
                continue

            complexities = analyzer.analyze_sentence_complexity(text)

            for comp in complexities:
                reasons = []

                if comp['word_count'] > self.MAX_WORDS:
                    reasons.append(f"{comp['word_count']} words (max {self.MAX_WORDS})")

                if comp['clause_count'] > self.MAX_CLAUSES:
                    reasons.append(f"{comp['clause_count']} clauses (max {self.MAX_CLAUSES})")

                if comp['max_dep_depth'] > self.MAX_DEP_DEPTH:
                    reasons.append(f"depth {comp['max_dep_depth']} (max {self.MAX_DEP_DEPTH})")

                if reasons:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Complex sentence: {", ".join(reasons)}',
                        paragraph_index=idx,
                        context=comp['sentence'][:80] + '...',
                        suggestion='Consider breaking into shorter sentences',
                        rule_id='CPLX001'
                    ))

        return issues
```

### Installation & Configuration

```bash
# Installation (one-time, requires internet)
pip install spacy>=3.7.0
python -m spacy download en_core_web_md

# For air-gapped installation:
# 1. Download wheel on connected machine
# 2. Copy to air-gapped machine
# 3. pip install ./en_core_web_md-3.7.0.tar.gz
```

### Configuration

```python
# In settings or config
SPACY_CONFIG = {
    'model': 'en_core_web_md',  # or 'en_core_web_lg' for better accuracy
    'disable': ['textcat'],      # Disable unused components for speed
    'batch_size': 1000,          # Batch processing for large documents
}
```

### Performance Considerations

- **Model size**: en_core_web_sm (12MB), en_core_web_md (40MB), en_core_web_lg (560MB)
- **Processing speed**: ~10,000 words/second on modern hardware
- **Memory**: ~500MB for md model loaded
- **Lazy loading**: Only load when spaCy checkers are enabled

---

## 2. LanguageTool Integration

### Purpose
Add comprehensive grammar and style checking with 3000+ rules, replacing limited regex patterns.

### What It Adds (Not Currently in Tool)
- ✅ **3000+ grammar rules** vs current 15 patterns
- ✅ **Context-aware corrections** - Understands sentence meaning
- ✅ **Style suggestions** - Beyond just errors
- ✅ **Punctuation rules** - Comprehensive checking
- ✅ **Agreement checking** - Noun-verb, noun-pronoun, etc.

### What It Replaces/Enhances
| Current | Enhancement |
|---------|-------------|
| 15 regex grammar patterns | 3000+ linguistic rules |
| "could of" detection only | All common grammar errors |
| Basic homophone patterns | Context-aware homophone detection |
| Limited punctuation | Full punctuation checking |

### Technical Specification

```python
# New module: languagetool_integration.py

import language_tool_python
from typing import List, Dict, Optional
from dataclasses import dataclass
import threading

@dataclass
class GrammarIssue:
    """Represents a grammar issue found by LanguageTool."""
    message: str
    context: str
    offset: int
    length: int
    replacements: List[str]
    rule_id: str
    category: str
    severity: str  # Mapped from LanguageTool issue type

class LanguageToolChecker:
    """
    LanguageTool integration for comprehensive grammar checking.

    Runs local Java server - no internet required after installation.
    """

    # Category to severity mapping
    SEVERITY_MAP = {
        'GRAMMAR': 'Medium',
        'TYPOS': 'Medium',
        'PUNCTUATION': 'Low',
        'STYLE': 'Low',
        'TYPOGRAPHY': 'Info',
        'CASING': 'Low',
        'REDUNDANCY': 'Low',
        'MISC': 'Low',
    }

    # Rules to skip (overlap with existing checkers)
    SKIP_RULES = {
        # Passive voice - we have our own checker
        'PASSIVE_VOICE',
        # Contractions - we have our own checker
        'CONTRACTION',
        # These may conflict with technical writing style
        'COMMA_COMPOUND_SENTENCE',
        'OXFORD_COMMA',
    }

    # Technical writing whitelist - don't flag these
    TECHNICAL_WHITELIST = {
        'shall', 'per', 'via', 'e.g.', 'i.e.', 'etc.',
        'aforementioned', 'hereafter', 'herein', 'thereof',
    }

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - only one LanguageTool server."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tool = None
        self._available = False
        self._init_tool()
        self._initialized = True

    def _init_tool(self):
        """Initialize LanguageTool (starts local Java server)."""
        try:
            # Use local server mode - no internet needed
            self._tool = language_tool_python.LanguageTool(
                'en-US',
                config={'cacheSize': 1000, 'pipelineCaching': True}
            )
            self._available = True
        except Exception as e:
            print(f"[LanguageTool] Initialization failed: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def check(self, text: str) -> List[GrammarIssue]:
        """
        Check text for grammar issues.

        Returns list of GrammarIssue objects.
        """
        if not self._available or not text:
            return []

        try:
            matches = self._tool.check(text)
        except Exception as e:
            print(f"[LanguageTool] Check failed: {e}")
            return []

        issues = []
        for match in matches:
            # Skip rules that overlap with existing checkers
            if match.ruleId in self.SKIP_RULES:
                continue

            # Skip if flagged word is in technical whitelist
            flagged = text[match.offset:match.offset + match.errorLength].lower()
            if flagged in self.TECHNICAL_WHITELIST:
                continue

            # Map category to severity
            category = match.category or 'MISC'
            severity = self.SEVERITY_MAP.get(category, 'Low')

            issues.append(GrammarIssue(
                message=match.message,
                context=match.context,
                offset=match.offset,
                length=match.errorLength,
                replacements=match.replacements[:3],  # Top 3 suggestions
                rule_id=match.ruleId,
                category=category,
                severity=severity
            ))

        return issues

    def get_correction(self, text: str) -> str:
        """
        Return corrected text with all fixes applied.

        Use cautiously - may change meaning.
        """
        if not self._available:
            return text

        try:
            return language_tool_python.utils.correct(text, self._tool.check(text))
        except Exception:
            return text

    def close(self):
        """Shut down the LanguageTool server."""
        if self._tool:
            self._tool.close()
            self._tool = None
            self._available = False
```

### Checker Integration

```python
# New checker: languagetool_checker.py

from base_checker import BaseChecker
from languagetool_integration import LanguageToolChecker, GrammarIssue

class ComprehensiveGrammarChecker(BaseChecker):
    """
    Comprehensive grammar checking using LanguageTool.

    Provides 3000+ grammar rules beyond basic regex patterns.
    """

    CHECKER_NAME = "Grammar (Comprehensive)"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._checker = None

    def _get_checker(self):
        if self._checker is None:
            self._checker = LanguageToolChecker()
        return self._checker

    def check(self, paragraphs, **kwargs):
        if not self.enabled:
            return []

        checker = self._get_checker()
        if not checker.is_available:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            grammar_issues = checker.check(text)

            for gi in grammar_issues:
                # Build suggestion text
                suggestion = gi.message
                if gi.replacements:
                    suggestion += f' Suggestions: {", ".join(gi.replacements)}'

                issues.append(self.create_issue(
                    severity=gi.severity,
                    message=f'Grammar: {gi.message}',
                    paragraph_index=idx,
                    context=gi.context,
                    suggestion=suggestion,
                    rule_id=f'LT-{gi.rule_id}',
                    category=f'Grammar/{gi.category}'
                ))

        return issues
```

### Installation

```bash
# LanguageTool requires Java 8+
pip install language-tool-python

# First run downloads LanguageTool JAR (~200MB)
# Subsequent runs use cached version
```

### Configuration Options

```python
LANGUAGETOOL_CONFIG = {
    'language': 'en-US',  # or 'en-GB'
    'enabled_rules': [],   # Empty = all rules
    'disabled_rules': [
        'PASSIVE_VOICE',   # We have our own
        'WHITESPACE_RULE', # Too noisy
    ],
    'enabled_categories': [
        'GRAMMAR',
        'TYPOS',
        'PUNCTUATION',
    ],
}
```

---

## 3. SymSpellPy Integration

### Purpose
Replace 100-word misspelling dictionary with comprehensive, ultra-fast spell checking.

### What It Adds (Not Currently in Tool)
- ✅ **500,000+ word dictionary** vs 100 words
- ✅ **Edit distance algorithm** - Catches phonetic errors
- ✅ **Word frequency ranking** - Suggests most common words first
- ✅ **Compound word splitting** - "writtenreport" → "written report"
- ✅ **1M times faster** than traditional algorithms

### What It Replaces
| Current | Enhancement |
|---------|-------------|
| 100 hardcoded misspellings | 500K+ word dictionary |
| Exact match only | Edit distance up to 2 |
| No phonetic matching | Handles typos like "definately" |
| No compound detection | Splits stuck-together words |

### Technical Specification

```python
# New module: symspell_integration.py

from symspellpy import SymSpell, Verbosity
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pkg_resources

class EnhancedSpellChecker:
    """
    SymSpell-based spell checker for AEGIS.

    1 million times faster than traditional algorithms.
    """

    # Default dictionary paths (bundled with symspellpy)
    FREQUENCY_DICT = "frequency_dictionary_en_82_765.txt"
    BIGRAM_DICT = "frequency_bigramdictionary_en_243_342.txt"

    def __init__(
        self,
        max_edit_distance: int = 2,
        prefix_length: int = 7,
        custom_dictionary: Optional[str] = None
    ):
        self.max_edit_distance = max_edit_distance
        self.prefix_length = prefix_length
        self.custom_dictionary = custom_dictionary

        self._sym_spell = SymSpell(
            max_dictionary_edit_distance=max_edit_distance,
            prefix_length=prefix_length
        )
        self._loaded = False
        self._custom_words = set()

        self._load_dictionaries()

    def _load_dictionaries(self):
        """Load frequency dictionaries."""
        try:
            # Load main dictionary
            dict_path = pkg_resources.resource_filename(
                "symspellpy", self.FREQUENCY_DICT
            )
            self._sym_spell.load_dictionary(
                dict_path,
                term_index=0,
                count_index=1
            )

            # Load bigram dictionary for compound word handling
            bigram_path = pkg_resources.resource_filename(
                "symspellpy", self.BIGRAM_DICT
            )
            self._sym_spell.load_bigram_dictionary(
                bigram_path,
                term_index=0,
                count_index=2
            )

            # Load custom dictionary if provided
            if self.custom_dictionary and Path(self.custom_dictionary).exists():
                self._load_custom_dictionary()

            self._loaded = True

        except Exception as e:
            print(f"[SymSpell] Failed to load dictionaries: {e}")
            self._loaded = False

    def _load_custom_dictionary(self):
        """Load custom technical terms dictionary."""
        with open(self.custom_dictionary, 'r') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    self._custom_words.add(word)
                    # Add to SymSpell with high frequency
                    self._sym_spell.create_dictionary_entry(word, 1000000)

    @property
    def is_available(self) -> bool:
        return self._loaded

    def check_word(self, word: str) -> List[Dict]:
        """
        Check a single word for spelling errors.

        Returns list of suggestions with distance and frequency.
        """
        if not self._loaded or not word:
            return []

        # Skip if in custom dictionary
        if word.lower() in self._custom_words:
            return []

        # Skip numbers, all-caps (acronyms), short words
        if word.isdigit() or word.isupper() or len(word) < 3:
            return []

        suggestions = self._sym_spell.lookup(
            word.lower(),
            Verbosity.CLOSEST,
            max_edit_distance=self.max_edit_distance,
            include_unknown=True
        )

        results = []
        for sug in suggestions:
            if sug.term != word.lower():
                results.append({
                    'suggestion': sug.term,
                    'distance': sug.distance,
                    'frequency': sug.count
                })

        return results[:5]  # Top 5 suggestions

    def check_text(self, text: str) -> List[Dict]:
        """
        Check text for spelling errors.

        Returns list of misspellings with suggestions.
        """
        if not self._loaded:
            return []

        import re
        words = re.findall(r'\b[a-zA-Z]+\b', text)

        misspellings = []
        seen = set()

        for word in words:
            if word.lower() in seen:
                continue

            suggestions = self.check_word(word)
            if suggestions and suggestions[0]['distance'] > 0:
                misspellings.append({
                    'word': word,
                    'suggestions': suggestions,
                    'best_suggestion': suggestions[0]['suggestion']
                })
                seen.add(word.lower())

        return misspellings

    def segment_compound(self, text: str) -> str:
        """
        Segment text that may have missing spaces.

        Example: "writtenreport" → "written report"
        """
        if not self._loaded:
            return text

        result = self._sym_spell.word_segmentation(text)
        return result.corrected_string

    def add_word(self, word: str):
        """Add word to custom dictionary."""
        self._custom_words.add(word.lower())
        self._sym_spell.create_dictionary_entry(word.lower(), 1000000)
```

### Checker Integration

```python
# Enhanced spelling checker using SymSpell

from base_checker import BaseChecker
from symspell_integration import EnhancedSpellChecker

class EnhancedSpellingChecker(BaseChecker):
    """
    Comprehensive spelling checker using SymSpell.

    Replaces basic 100-word dictionary with 500K+ words.
    """

    CHECKER_NAME = "Spelling (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    # Words to never flag (technical terms, proper nouns, etc.)
    SKIP_WORDS = {
        # Aerospace/Defense
        'avionics', 'airframe', 'subsystem', 'datalink', 'waypoint',
        # Software
        'frontend', 'backend', 'microservice', 'kubernetes', 'nginx',
        # Acronym-like
        'docx', 'xlsx', 'pdf', 'html', 'xml', 'json', 'yaml',
    }

    def __init__(self, enabled: bool = True, custom_dict: str = None):
        super().__init__(enabled)
        self._checker = None
        self._custom_dict = custom_dict

    def _get_checker(self):
        if self._checker is None:
            self._checker = EnhancedSpellChecker(
                custom_dictionary=self._custom_dict
            )
        return self._checker

    def check(self, paragraphs, **kwargs):
        if not self.enabled:
            return []

        checker = self._get_checker()
        if not checker.is_available:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            misspellings = checker.check_text(text)

            for ms in misspellings:
                word = ms['word']

                # Skip technical terms
                if word.lower() in self.SKIP_WORDS:
                    continue

                # Skip if likely proper noun (capitalized mid-sentence)
                if word[0].isupper() and not text.startswith(word):
                    continue

                suggestions = [s['suggestion'] for s in ms['suggestions'][:3]]

                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Possible misspelling: "{word}"',
                    paragraph_index=idx,
                    context=self._get_word_context(text, word),
                    suggestion=f'Did you mean: {", ".join(suggestions)}?',
                    rule_id='SPELL001',
                    original_text=word,
                    replacement_text=ms['best_suggestion']
                ))

        return issues

    def _get_word_context(self, text: str, word: str) -> str:
        """Get context around misspelled word."""
        import re
        match = re.search(r'\b' + re.escape(word) + r'\b', text)
        if match:
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            return '...' + text[start:end] + '...'
        return word
```

### Custom Dictionary Format

```text
# custom_aerospace_dictionary.txt
# One word per line
avionics
datalink
waypoint
subsystem
airframe
fuselage
aileron
rudder
```

### Installation

```bash
pip install symspellpy
```

---

## 4. Textstat Enhancement

### Purpose
Enhance existing readability metrics with additional formulas and detailed analysis.

### What It Adds (Not Currently in Tool)
- ✅ **Dale-Chall Score** - Uses 3000 common words list
- ✅ **Linsear Write** - Different algorithm
- ✅ **SMOG Index** - Another readability measure
- ✅ **Difficult word identification** - List actual hard words
- ✅ **Reading time estimate** - Estimated minutes to read
- ✅ **Lexicon count** - Vocabulary diversity

### Current vs Enhanced

| Metric | Current | Enhanced |
|--------|---------|----------|
| Flesch Reading Ease | ✅ Basic | ✅ Same |
| Flesch-Kincaid | ✅ Basic | ✅ Same |
| Gunning Fog | ✅ Basic | ✅ Same |
| Dale-Chall | ❌ | ✅ Added |
| SMOG | ❌ | ✅ Added |
| Linsear Write | ❌ | ✅ Added |
| Coleman-Liau | ❌ | ✅ Added |
| Automated Readability | ❌ | ✅ Added |
| Difficult Words List | ❌ | ✅ Added |
| Reading Time | ❌ | ✅ Added |

### Technical Specification

```python
# New module: textstat_integration.py

import textstat
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ReadabilityReport:
    """Comprehensive readability analysis."""

    # Standard metrics (already in tool)
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float

    # NEW metrics
    dale_chall: float
    smog_index: float
    linsear_write: float
    coleman_liau: float
    automated_readability: float

    # Summary
    consensus_grade: float  # Average of all grade-level metrics
    reading_time_minutes: float

    # Vocabulary analysis
    difficult_words: List[str]
    difficult_word_count: int
    lexicon_count: int

    # Interpretation
    grade_level: str  # "Grade 8", "College", etc.
    difficulty_rating: str  # "Easy", "Standard", "Difficult", "Very Difficult"


class EnhancedReadabilityCalculator:
    """
    Enhanced readability analysis using textstat.

    Adds metrics not in current implementation.
    """

    GRADE_LEVELS = {
        (0, 6): "Elementary",
        (6, 8): "Middle School",
        (8, 12): "High School",
        (12, 14): "College",
        (14, 18): "Graduate",
        (18, 100): "Professional"
    }

    DIFFICULTY_RATINGS = {
        (90, 100): "Very Easy",
        (80, 90): "Easy",
        (70, 80): "Fairly Easy",
        (60, 70): "Standard",
        (50, 60): "Fairly Difficult",
        (30, 50): "Difficult",
        (0, 30): "Very Difficult"
    }

    def analyze(self, text: str) -> ReadabilityReport:
        """Perform comprehensive readability analysis."""

        # Standard metrics
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        gunning = textstat.gunning_fog(text)

        # NEW metrics
        dale_chall = textstat.dale_chall_readability_score(text)
        smog = textstat.smog_index(text)
        linsear = textstat.linsear_write_formula(text)
        coleman = textstat.coleman_liau_index(text)
        ari = textstat.automated_readability_index(text)

        # Difficult words
        difficult = textstat.difficult_words_list(text)

        # Calculate consensus grade
        grades = [flesch_grade, gunning, linsear, coleman, ari]
        consensus = sum(grades) / len(grades)

        # Reading time (average 200 words per minute)
        word_count = textstat.lexicon_count(text, removepunct=True)
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
            grade_level=grade_level,
            difficulty_rating=difficulty
        )

    def _get_grade_level(self, grade: float) -> str:
        for (low, high), level in self.GRADE_LEVELS.items():
            if low <= grade < high:
                return f"{level} (Grade {int(grade)})"
        return f"Grade {int(grade)}"

    def _get_difficulty(self, flesch_score: float) -> str:
        for (low, high), rating in self.DIFFICULTY_RATINGS.items():
            if low <= flesch_score < high:
                return rating
        return "Unknown"

    def get_recommendations(self, report: ReadabilityReport) -> List[str]:
        """Generate readability improvement recommendations."""
        recommendations = []

        # Grade level recommendations
        if report.consensus_grade > 14:
            recommendations.append(
                f"Document reads at graduate level (Grade {report.consensus_grade:.0f}). "
                "Consider simplifying for broader audience."
            )
        elif report.consensus_grade > 12:
            recommendations.append(
                "Document reads at college level. Appropriate for technical audience."
            )

        # Flesch ease recommendations
        if report.flesch_reading_ease < 30:
            recommendations.append(
                f"Very difficult to read (Flesch {report.flesch_reading_ease}). "
                "Use shorter sentences and simpler words."
            )
        elif report.flesch_reading_ease < 50:
            recommendations.append(
                f"Fairly difficult (Flesch {report.flesch_reading_ease}). "
                "Consider breaking up complex sentences."
            )

        # Difficult words
        if report.difficult_word_count > 50:
            sample = ", ".join(report.difficult_words[:5])
            recommendations.append(
                f"Found {report.difficult_word_count} difficult words. "
                f"Examples: {sample}. Consider defining technical terms."
            )

        # Gunning Fog
        if report.gunning_fog > 17:
            recommendations.append(
                f"High Gunning Fog Index ({report.gunning_fog}). "
                "Reduce percentage of complex words (3+ syllables)."
            )

        return recommendations
```

### Installation

```bash
pip install textstat
```

---

## 5. PyEnchant Integration

### Purpose
Add custom dictionary support for domain-specific terminology.

### What It Adds (Not Currently in Tool)
- ✅ **Hunspell dictionaries** - Same as Chrome/Firefox/LibreOffice
- ✅ **Personal word lists** - Per-user custom terms
- ✅ **Domain dictionaries** - Aerospace, defense, IT, etc.
- ✅ **Morphological analysis** - Understand word forms
- ✅ **Multiple dictionary stacking** - Combine dictionaries

### Technical Specification

```python
# New module: pyenchant_integration.py

import enchant
from enchant.checker import SpellChecker
from typing import List, Set, Optional
from pathlib import Path

class DomainDictionaryManager:
    """
    Manages domain-specific dictionaries for technical writing.

    Supports Hunspell dictionaries (same as LibreOffice, Chrome, Firefox).
    """

    # Built-in domain dictionaries
    DOMAIN_DICTIONARIES = {
        'aerospace': 'aerospace_terms.txt',
        'defense': 'defense_terms.txt',
        'software': 'software_terms.txt',
        'systems_engineering': 'systems_engineering_terms.txt',
        'requirements': 'requirements_terms.txt',
    }

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent / 'dictionaries'
        self._dictionaries: dict = {}
        self._personal_words: Set[str] = set()
        self._checker = None

        self._init_base_dictionary()

    def _init_base_dictionary(self):
        """Initialize base English dictionary."""
        try:
            self._base_dict = enchant.Dict("en_US")
            self._checker = SpellChecker("en_US")
        except enchant.errors.DictNotFoundError:
            # Try en_GB as fallback
            try:
                self._base_dict = enchant.Dict("en_GB")
                self._checker = SpellChecker("en_GB")
            except:
                self._base_dict = None
                self._checker = None

    def load_domain_dictionary(self, domain: str) -> bool:
        """Load a domain-specific dictionary."""
        if domain in self._dictionaries:
            return True

        dict_file = self.DOMAIN_DICTIONARIES.get(domain)
        if not dict_file:
            return False

        dict_path = self.base_path / dict_file
        if not dict_path.exists():
            return False

        words = set()
        with open(dict_path, 'r') as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith('#'):
                    words.add(word)

        self._dictionaries[domain] = words
        return True

    def add_personal_word(self, word: str):
        """Add word to personal dictionary."""
        self._personal_words.add(word.lower())

    def is_valid_word(self, word: str) -> bool:
        """Check if word is valid in any loaded dictionary."""
        word_lower = word.lower()

        # Check personal words first
        if word_lower in self._personal_words:
            return True

        # Check domain dictionaries
        for domain_words in self._dictionaries.values():
            if word_lower in domain_words:
                return True

        # Check base dictionary
        if self._base_dict and self._base_dict.check(word):
            return True

        return False

    def suggest(self, word: str) -> List[str]:
        """Get spelling suggestions for a word."""
        if self._base_dict:
            return self._base_dict.suggest(word)[:5]
        return []

    def check_text(self, text: str) -> List[dict]:
        """Check text and return unknown words."""
        if not self._checker:
            return []

        self._checker.set_text(text)

        unknown = []
        for error in self._checker:
            word = error.word

            # Skip if in our extended dictionaries
            if self.is_valid_word(word):
                continue

            unknown.append({
                'word': word,
                'position': error.wordpos,
                'suggestions': self.suggest(word)
            })

        return unknown

    def save_personal_dictionary(self, path: str):
        """Save personal dictionary to file."""
        with open(path, 'w') as f:
            for word in sorted(self._personal_words):
                f.write(word + '\n')

    def load_personal_dictionary(self, path: str):
        """Load personal dictionary from file."""
        if Path(path).exists():
            with open(path, 'r') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        self._personal_words.add(word.lower())
```

### Sample Domain Dictionary

```text
# dictionaries/aerospace_terms.txt
# Aerospace and aviation terminology

# Aircraft components
aileron
fuselage
empennage
nacelle
fairing
winglet
strut

# Systems
avionics
autopilot
transponder
altimeter
gyroscope
pitot

# Operations
deicing
preflight
postflight
taxiing
pushback

# Requirements terms
testability
traceability
verification
validation
airworthiness
certifiable
```

### Installation

```bash
pip install pyenchant

# On macOS with Homebrew:
brew install enchant

# On Ubuntu/Debian:
sudo apt-get install libenchant-2-dev
```

---

## 6. Proselint Integration

### Purpose
Add professional writing style rules from world-class writers and editors.

### What It Adds (Not Currently in Tool)
- ✅ **Editorial style rules** - From Strunk & White, Garner, etc.
- ✅ **Cliché detection** - Beyond current 15 phrases
- ✅ **Jargon patterns** - Additional business jargon
- ✅ **Sexism detection** - Gender bias in language
- ✅ **Redundancy patterns** - Additional redundant phrases
- ✅ **Weasel word detection** - Enhanced from current

### Overlap Analysis

| Proselint Rule | Current Status | Action |
|---------------|----------------|--------|
| Clichés | Have 15, proselint has 50+ | **Add unique ones** |
| Redundancy | Have 20+ | **Add unique ones** |
| Jargon | Have 50+ | **Add unique ones** |
| Weasel words | Have 15+ | **Add unique ones** |
| Sexism | Have 20 gender terms | **Add patterns** |
| Hedging | Have 15+ | **Add unique ones** |

### Technical Specification

```python
# New module: proselint_integration.py

import proselint
from typing import List, Dict, Set

class ProselintChecker:
    """
    Proselint integration for professional writing style.

    Provides rules from Strunk & White, Garner, Orwell, etc.
    """

    # Rules to skip (overlap with existing checkers)
    SKIP_CHECKS = {
        'passive_voice',      # We have our own
        'contractions',       # We have our own
    }

    # Map proselint severity to our severity
    SEVERITY_MAP = {
        'error': 'High',
        'warning': 'Medium',
        'suggestion': 'Low',
    }

    def check(self, text: str) -> List[Dict]:
        """
        Check text for style issues.

        Returns list of issues with rule info.
        """
        try:
            suggestions = proselint.tools.lint(text)
        except Exception as e:
            print(f"[Proselint] Check failed: {e}")
            return []

        issues = []
        for sug in suggestions:
            check_name = sug[0]

            # Skip overlapping checks
            if any(skip in check_name for skip in self.SKIP_CHECKS):
                continue

            issues.append({
                'check': check_name,
                'message': sug[1],
                'line': sug[2],
                'column': sug[3],
                'start': sug[4],
                'end': sug[5],
                'severity': self.SEVERITY_MAP.get(sug[6], 'Low'),
                'replacement': sug[7]
            })

        return issues

    @staticmethod
    def get_available_checks() -> List[str]:
        """List all available proselint checks."""
        from proselint import checks
        return [name for name in dir(checks) if not name.startswith('_')]
```

### Installation

```bash
pip install proselint
```

---

## 7. Pattern.en Integration

### Purpose
Add verb conjugation analysis and tense consistency checking.

### What It Adds (Not Currently in Tool)
- ✅ **Verb tense detection** - Identify past, present, future
- ✅ **Tense consistency** - Flag mixed tenses in paragraph
- ✅ **Verb conjugation** - Proper verb forms
- ✅ **Mood detection** - Indicative, subjunctive, imperative
- ✅ **Singularization/pluralization** - Noun form checking

### Technical Specification

```python
# New module: pattern_integration.py

from pattern.en import conjugate, lemma, tenses
from pattern.en import INFINITIVE, PRESENT, PAST, FUTURE
from pattern.en import FIRST, SECOND, THIRD
from pattern.en import SINGULAR, PLURAL
from typing import List, Dict, Tuple, Set

class VerbAnalyzer:
    """
    Verb analysis using pattern.en library.

    Provides tense detection and consistency checking.
    """

    TENSE_NAMES = {
        'infinitive': INFINITIVE,
        'present': PRESENT,
        'past': PAST,
        'future': FUTURE,
    }

    def get_verb_tense(self, verb: str) -> List[str]:
        """
        Get the tense(s) of a verb.

        Returns list of possible tenses.
        """
        return list(tenses(verb))

    def get_base_form(self, verb: str) -> str:
        """Get the infinitive/base form of a verb."""
        return lemma(verb)

    def conjugate_verb(
        self,
        verb: str,
        tense: str = 'present',
        person: int = 3,
        number: str = 'singular'
    ) -> str:
        """
        Conjugate a verb to specified form.

        Args:
            verb: Base form of verb
            tense: 'infinitive', 'present', 'past', 'future'
            person: 1, 2, or 3
            number: 'singular' or 'plural'
        """
        tense_const = self.TENSE_NAMES.get(tense, PRESENT)
        number_const = SINGULAR if number == 'singular' else PLURAL

        return conjugate(verb, tense_const, person, number_const)

    def analyze_tense_consistency(self, sentences: List[str]) -> Dict:
        """
        Analyze tense consistency across sentences.

        Returns dominant tense and any inconsistencies.
        """
        import re

        tense_counts = {'past': 0, 'present': 0, 'future': 0}
        inconsistencies = []

        for i, sent in enumerate(sentences):
            # Find verbs (simplified - in practice use spaCy)
            words = re.findall(r'\b\w+\b', sent.lower())

            sent_tenses = set()
            for word in words:
                word_tenses = tenses(word)
                for t in word_tenses:
                    if t[0] in ('past', 'present', 'future'):
                        sent_tenses.add(t[0])
                        tense_counts[t[0]] += 1

            if len(sent_tenses) > 1:
                inconsistencies.append({
                    'sentence_index': i,
                    'sentence': sent[:80],
                    'tenses_found': list(sent_tenses)
                })

        # Determine dominant tense
        dominant = max(tense_counts, key=tense_counts.get)

        return {
            'dominant_tense': dominant,
            'tense_distribution': tense_counts,
            'inconsistencies': inconsistencies
        }


class TenseConsistencyChecker:
    """Checker for verb tense consistency in documents."""

    def __init__(self):
        self._analyzer = VerbAnalyzer()

    def check_paragraph(self, text: str) -> List[Dict]:
        """Check a paragraph for tense inconsistencies."""
        import re

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 2:
            return []

        analysis = self._analyzer.analyze_tense_consistency(sentences)

        issues = []
        for inc in analysis['inconsistencies']:
            issues.append({
                'message': f"Mixed tenses in sentence: {', '.join(inc['tenses_found'])}",
                'context': inc['sentence'],
                'dominant_tense': analysis['dominant_tense'],
                'severity': 'Low'
            })

        return issues
```

### Installation

```bash
pip install pattern
```

**Note:** Pattern requires some setup. On some systems:
```bash
pip install pattern
python -c "import pattern.en"  # Downloads required data
```

---

## 8. WordNet Integration

### Purpose
Add semantic analysis for terminology consistency.

### What It Adds (Not Currently in Tool)
- ✅ **Synonym detection** - Find terminology variations
- ✅ **Semantic similarity** - How related are two terms
- ✅ **Hypernym/hyponym** - Category relationships
- ✅ **Terminology consistency** - Same concept, different words

### Technical Specification

```python
# New module: wordnet_integration.py

from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from typing import List, Dict, Set, Tuple
import nltk

class SemanticAnalyzer:
    """
    WordNet-based semantic analysis.

    Detects terminology inconsistency through synonym detection.
    """

    def __init__(self):
        # Ensure WordNet data is available
        try:
            wn.synsets('test')
        except LookupError:
            nltk.download('wordnet')
            nltk.download('omw-1.4')

    def get_synonyms(self, word: str) -> Set[str]:
        """Get all synonyms for a word."""
        synonyms = set()
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word.lower():
                    synonyms.add(synonym)
        return synonyms

    def get_antonyms(self, word: str) -> Set[str]:
        """Get all antonyms for a word."""
        antonyms = set()
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                for ant in lemma.antonyms():
                    antonyms.add(ant.name().replace('_', ' '))
        return antonyms

    def similarity(self, word1: str, word2: str) -> float:
        """
        Calculate semantic similarity between two words.

        Returns score 0.0 to 1.0 (1.0 = identical meaning).
        """
        synsets1 = wn.synsets(word1)
        synsets2 = wn.synsets(word2)

        if not synsets1 or not synsets2:
            return 0.0

        max_sim = 0.0
        for s1 in synsets1:
            for s2 in synsets2:
                sim = s1.wup_similarity(s2)
                if sim and sim > max_sim:
                    max_sim = sim

        return max_sim

    def find_synonym_groups(self, words: List[str]) -> List[Set[str]]:
        """
        Group words that are synonyms of each other.

        Useful for detecting terminology inconsistency.
        """
        # Build similarity matrix
        n = len(words)
        groups = []
        used = set()

        for i, word1 in enumerate(words):
            if word1 in used:
                continue

            group = {word1}
            for j, word2 in enumerate(words):
                if i != j and word2 not in used:
                    if self.similarity(word1, word2) > 0.8:
                        group.add(word2)

            if len(group) > 1:
                groups.append(group)
                used.update(group)

        return groups


class TerminologyConsistencyChecker:
    """
    Check for inconsistent terminology using WordNet.

    Finds cases where synonyms are used for the same concept.
    """

    # Words that are acceptable to vary
    ALLOW_VARIATION = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were',
        'have', 'has', 'had', 'do', 'does', 'did',
    }

    def __init__(self):
        self._analyzer = SemanticAnalyzer()

    def check_document(self, paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """
        Check document for terminology inconsistency.

        Returns list of synonym groups that may be inconsistent.
        """
        # Collect all significant words
        all_words = []
        for idx, text in paragraphs:
            tokens = word_tokenize(text.lower())
            words = [w for w in tokens if w.isalpha() and len(w) > 3
                     and w not in self.ALLOW_VARIATION]
            all_words.extend(words)

        # Find unique words
        unique_words = list(set(all_words))

        # Find synonym groups
        groups = self._analyzer.find_synonym_groups(unique_words)

        issues = []
        for group in groups:
            if len(group) >= 2:
                words = sorted(group)
                issues.append({
                    'message': f"Potential terminology inconsistency: "
                              f"both '{words[0]}' and '{words[1]}' used",
                    'synonyms': list(group),
                    'severity': 'Low',
                    'suggestion': f"Consider using one term consistently"
                })

        return issues
```

### Installation

```bash
pip install nltk
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **spaCy Integration**
   - Install and configure models
   - Implement SpacyAnalyzer class
   - Create enhanced subject-verb checker
   - Create enhanced dangling modifier checker
   - Add sentence complexity checker

### Phase 2: Grammar Enhancement (Week 2-3)
2. **LanguageTool Integration**
   - Install and configure local server
   - Implement wrapper class
   - Create comprehensive grammar checker
   - Configure rule exclusions

3. **SymSpellPy Integration**
   - Install and load dictionaries
   - Implement enhanced spell checker
   - Create custom dictionary loader

### Phase 3: Analysis Enhancement (Week 3-4)
4. **Textstat Enhancement**
   - Install and configure
   - Add new readability metrics
   - Create recommendation engine

5. **PyEnchant Integration**
   - Install and configure
   - Create domain dictionary manager
   - Build aerospace/defense dictionaries

### Phase 4: Style Enhancement (Week 4-5)
6. **Proselint Integration**
   - Install and configure
   - Create wrapper avoiding overlaps
   - Add unique style rules

7. **Pattern.en Integration**
   - Install and configure
   - Implement verb analyzer
   - Create tense consistency checker

8. **WordNet Integration**
   - Install and download data
   - Implement semantic analyzer
   - Create terminology consistency checker

---

## Configuration Schema

```python
# config/detection_config.py

DETECTION_CONFIG = {
    # spaCy settings
    'spacy': {
        'enabled': True,
        'model': 'en_core_web_md',  # sm, md, or lg
        'disable': ['textcat'],
    },

    # LanguageTool settings
    'languagetool': {
        'enabled': True,
        'language': 'en-US',
        'disabled_rules': ['PASSIVE_VOICE', 'WHITESPACE_RULE'],
    },

    # SymSpell settings
    'symspell': {
        'enabled': True,
        'max_edit_distance': 2,
        'custom_dictionary': 'dictionaries/custom.txt',
    },

    # Textstat settings
    'textstat': {
        'enabled': True,
        'target_grade_level': 12,  # Flag if above this
    },

    # PyEnchant settings
    'pyenchant': {
        'enabled': True,
        'domains': ['aerospace', 'defense', 'software'],
        'personal_dict': 'dictionaries/personal.txt',
    },

    # Proselint settings
    'proselint': {
        'enabled': True,
        'skip_checks': ['passive_voice', 'contractions'],
    },

    # Pattern.en settings
    'pattern': {
        'enabled': True,
        'check_tense_consistency': True,
    },

    # WordNet settings
    'wordnet': {
        'enabled': True,
        'similarity_threshold': 0.8,
    },
}
```

---

## Dependencies

```text
# requirements-nlp.txt

# Core NLP
spacy>=3.7.0
en_core_web_md @ https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.7.0/en_core_web_md-3.7.0.tar.gz

# Grammar checking
language-tool-python>=2.8.0

# Spelling
symspellpy>=6.9.0
pyenchant>=3.2.0

# Readability
textstat>=0.7.3

# Style
proselint>=0.14.0

# Verb analysis
pattern>=3.6

# Semantics
nltk>=3.8.0
```

---

## Testing Strategy

Each integration should have:

1. **Unit tests** - Test individual functions
2. **Integration tests** - Test with AEGIS pipeline
3. **Performance tests** - Ensure acceptable speed
4. **Accuracy tests** - Validate detection quality
5. **Overlap tests** - Ensure no duplicate issues

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Grammar patterns | 15 | 3000+ |
| Spelling dictionary | 100 words | 500K+ |
| Readability metrics | 7 | 12+ |
| False positive rate | Unknown | <5% |
| Processing speed | Baseline | <2x slower |
| Issue confidence | None | 0.0-1.0 scores |

---

## Appendix: Air-Gap Considerations

All tools support offline operation:

| Tool | Offline Mode | Setup Required |
|------|-------------|----------------|
| spaCy | ✅ | Download model once |
| LanguageTool | ✅ | Downloads JAR first run |
| SymSpellPy | ✅ | Bundled dictionaries |
| Textstat | ✅ | No external data |
| PyEnchant | ✅ | Hunspell dictionaries |
| Proselint | ✅ | Rules bundled |
| Pattern.en | ✅ | Data bundled |
| WordNet | ✅ | Download data once |

For air-gapped installation, pre-download all models and data on connected machine, then transfer.
