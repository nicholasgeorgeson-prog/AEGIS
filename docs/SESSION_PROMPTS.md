# NLP Enhancement Session Prompts

Just say **"start session 2"** (or 3, 4, etc.) and Claude will know what to do.

---

## Session Status

- [x] Session 1: Foundation ✅ COMPLETE
- [ ] Session 2: spaCy Analyzer & Checkers
- [ ] Session 3: LanguageTool Integration
- [ ] Session 4: Spelling Enhancement
- [ ] Session 5: Readability Enhancement
- [ ] Session 6: Style Checking
- [ ] Session 7: Verb/Tense Analysis
- [ ] Session 8: Semantic Analysis
- [ ] Session 9: Core Integration
- [ ] Session 10: Testing & Documentation

---

## Session 1: Foundation ✅ COMPLETE

**Files created:**
- `nlp/__init__.py` - Package init with lazy loading
- `nlp/config.py` - Centralized configuration
- `nlp/base.py` - Base classes (NLPCheckerBase, NLPIssue)
- `nlp/spacy/__init__.py` - spaCy subpackage init

---

## Session 2: spaCy Analyzer & Checkers

**Goal:** Implement spaCy linguistic analysis with 3 new checkers.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "spaCy Integration")
- `nlp/base.py` (base classes to inherit from)

**Create:**

1. `nlp/spacy/analyzer.py` (~200 lines)
   - `SpacyAnalyzer` class with lazy model loading
   - Methods: `analyze()`, `find_subject_verb_pairs()`, `find_dangling_modifiers()`, `analyze_sentence_complexity()`, `extract_entities_for_roles()`
   - Property: `is_available`
   - Air-gap compatible (offline models)

2. `nlp/spacy/checkers.py` (~200 lines)
   - `EnhancedSubjectVerbChecker` - uses dependency parsing for agreement
   - `EnhancedDanglingModifierChecker` - detects dangling modifiers via parse tree
   - `SentenceComplexityChecker` - flags overly complex sentences
   - All inherit from `nlp.base.NLPCheckerBase`

**Verify:** `python3 -c "from nlp.spacy import get_analyzer; print(get_analyzer())"`

---

## Session 3: LanguageTool Integration

**Goal:** Add 3000+ grammar rules via LanguageTool.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "LanguageTool")
- `nlp/base.py`

**Create:**

1. `nlp/languagetool/__init__.py` (~20 lines)
   - `is_available()`, `get_status()` functions

2. `nlp/languagetool/client.py` (~150 lines)
   - `LanguageToolClient` class (singleton)
   - Wraps `language_tool_python` library
   - `SKIP_RULES` to avoid overlap with existing checkers
   - `TECHNICAL_WHITELIST` for aerospace/defense terms

3. `nlp/languagetool/checker.py` (~130 lines)
   - `ComprehensiveGrammarChecker` class
   - Inherits from `NLPCheckerBase`

**Verify:** `python3 -c "from nlp.languagetool import is_available; print(is_available())"`

---

## Session 4: Spelling Enhancement

**Goal:** Replace 100-word dictionary with 500K+ words + domain dictionaries.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "SymSpell" and "PyEnchant")
- `nlp/base.py`

**Create:**

1. `nlp/spelling/__init__.py` (~20 lines)

2. `nlp/spelling/symspell.py` (~150 lines)
   - `SymSpellChecker` class
   - `check_word()`, `check_text()`, `segment_compound()`

3. `nlp/spelling/enchant.py` (~130 lines)
   - `DomainDictionaryManager` class
   - Load aerospace/defense/software terms

4. `nlp/spelling/checker.py` (~100 lines)
   - `EnhancedSpellingChecker` class

5. `dictionaries/aerospace.txt` (~200 terms)
6. `dictionaries/defense.txt` (~150 terms)
7. `dictionaries/software.txt` (~150 terms)

**Verify:** `python3 -c "from nlp.spelling.checker import EnhancedSpellingChecker; print('OK')"`

---

## Session 5: Readability Enhancement

**Goal:** Add 5 new readability metrics beyond current 7.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "Textstat")

**Create:**

1. `nlp/readability/__init__.py` (~20 lines)

2. `nlp/readability/enhanced.py` (~180 lines)
   - `ReadabilityReport` dataclass
   - `EnhancedReadabilityCalculator` class
   - New metrics: Dale-Chall, SMOG, Linsear Write, Coleman-Liau, ARI
   - `get_recommendations()` method

**Verify:** `python3 -c "from nlp.readability.enhanced import EnhancedReadabilityCalculator; print('OK')"`

---

## Session 6: Style Checking

**Goal:** Add professional editorial style rules from Proselint.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "Proselint")

**Create:**

1. `nlp/style/__init__.py` (~20 lines)

2. `nlp/style/proselint.py` (~100 lines)
   - `ProselintWrapper` class
   - `SKIP_CHECKS` to avoid overlap

3. `nlp/style/checker.py` (~80 lines)
   - `StyleChecker` class

**Verify:** `python3 -c "from nlp.style.checker import StyleChecker; print('OK')"`

---

## Session 7: Verb/Tense Analysis

**Goal:** NEW capability - detect mixed verb tenses.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "Pattern.en")

**Create:**

1. `nlp/verbs/__init__.py` (~20 lines)

2. `nlp/verbs/pattern_en.py` (~130 lines)
   - `VerbAnalyzer` class
   - `get_verb_tense()`, `analyze_tense_consistency()`

3. `nlp/verbs/checker.py` (~100 lines)
   - `TenseConsistencyChecker` class

**Verify:** `python3 -c "from nlp.verbs.checker import TenseConsistencyChecker; print('OK')"`

---

## Session 8: Semantic Analysis

**Goal:** NEW capability - detect terminology inconsistency via synonyms.

**Read first:**
- `docs/DETECTION_ENHANCEMENT_SPEC.md` (search for "WordNet")

**Create:**

1. `nlp/semantics/__init__.py` (~20 lines)

2. `nlp/semantics/wordnet.py` (~130 lines)
   - `SemanticAnalyzer` class
   - `get_synonyms()`, `similarity()`, `find_synonym_groups()`

3. `nlp/semantics/checker.py` (~100 lines)
   - `TerminologyConsistencyChecker` class

**Verify:** `python3 -c "from nlp.semantics.checker import TerminologyConsistencyChecker; print('OK')"`

---

## Session 9: Core Integration

**Goal:** Wire NLP checkers into the main review pipeline.

**Read first:**
- `nlp/__init__.py` - see `get_available_checkers()`
- `nlp/base.py` - see `convert_to_legacy_issue()`
- `core.py` - find `review_document()` function

**Modify:**

1. `core.py` (~100 lines added)
   - Import `nlp` package
   - After existing checkers run, call NLP checkers
   - Convert `NLPIssue` to legacy format
   - Add NLP metrics to results

2. `app.py` (~50 lines added)
   - `GET /api/nlp/status`
   - `POST /api/nlp/config`
   - `GET /api/nlp/checkers`

**Verify:** Review a document and check for NLP-detected issues in results.

---

## Session 10: Testing & Documentation

**Goal:** Complete test coverage and user documentation.

**Create:**

1. `tests/nlp/__init__.py`
2. `tests/nlp/test_spacy.py`
3. `tests/nlp/test_languagetool.py`
4. `tests/nlp/test_spelling.py`
5. `tests/nlp/test_readability.py`
6. `tests/nlp/test_style.py`
7. `tests/nlp/test_verbs.py`
8. `tests/nlp/test_semantics.py`
9. `docs/NLP_USAGE.md` - Installation, configuration, air-gap setup

**Verify:** `python3 -m pytest tests/nlp/ -v`

---

## Quick Reference

**Install dependencies:**
```bash
pip3 install spacy language-tool-python symspellpy pyenchant textstat proselint pattern nltk
python3 -m spacy download en_core_web_md
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

**Key files:**
- Spec: `docs/DETECTION_ENHANCEMENT_SPEC.md`
- Roadmap: `docs/IMPLEMENTATION_ROADMAP.md`
- Base classes: `nlp/base.py`
- Config: `nlp/config.py`
