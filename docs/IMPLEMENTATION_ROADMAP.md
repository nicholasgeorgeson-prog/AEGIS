# Detection Enhancement Implementation Roadmap

**Version:** 1.0.0
**Date:** 2026-02-01
**Purpose:** Modular implementation plan respecting context/session limits

---

## Context-Aware Implementation Strategy

### Session Limits Considered
- Each session can safely handle ~3-4 medium files or 1-2 large files
- Complex integrations should be split across sessions
- Each module should be self-contained and testable independently

### File Size Guidelines
- **Small module**: <150 lines (1 per session batch)
- **Medium module**: 150-300 lines (2-3 per session)
- **Large module**: 300-500 lines (dedicate session)

---

## Module Breakdown

### Directory Structure

```
AEGIS/
├── nlp/                          # NEW: NLP integration package
│   ├── __init__.py              # Package init, lazy loading
│   ├── config.py                # Configuration for all NLP tools
│   ├── base.py                  # Base classes for NLP integrations
│   │
│   ├── spacy/                   # spaCy integration (Session 1-2)
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Core SpacyAnalyzer class
│   │   └── checkers.py          # spaCy-based checkers
│   │
│   ├── languagetool/            # LanguageTool integration (Session 3)
│   │   ├── __init__.py
│   │   ├── client.py            # LanguageTool wrapper
│   │   └── checker.py           # Grammar checker
│   │
│   ├── spelling/                # Spelling tools (Session 4)
│   │   ├── __init__.py
│   │   ├── symspell.py          # SymSpellPy integration
│   │   ├── enchant.py           # PyEnchant integration
│   │   └── checker.py           # Combined spell checker
│   │
│   ├── readability/             # Readability enhancement (Session 5)
│   │   ├── __init__.py
│   │   └── enhanced.py          # Textstat integration
│   │
│   ├── style/                   # Style checking (Session 6)
│   │   ├── __init__.py
│   │   ├── proselint.py         # Proselint integration
│   │   └── checker.py           # Style checker
│   │
│   ├── verbs/                   # Verb analysis (Session 7)
│   │   ├── __init__.py
│   │   ├── pattern_en.py        # Pattern.en integration
│   │   └── checker.py           # Tense consistency checker
│   │
│   └── semantics/               # Semantic analysis (Session 8)
│       ├── __init__.py
│       ├── wordnet.py           # WordNet integration
│       └── checker.py           # Terminology consistency
│
├── dictionaries/                # NEW: Custom dictionaries
│   ├── aerospace.txt
│   ├── defense.txt
│   ├── software.txt
│   └── personal.txt
│
└── tests/
    └── nlp/                     # NEW: NLP integration tests
        ├── test_spacy.py
        ├── test_languagetool.py
        ├── test_spelling.py
        └── ...
```

---

## Implementation Sessions

### Session 1: Foundation & spaCy Core
**Files to create:** 4 small files
**Estimated lines:** ~250 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/__init__.py` | ~30 | Package init with lazy loading |
| `nlp/config.py` | ~60 | Centralized configuration |
| `nlp/base.py` | ~50 | Base classes |
| `nlp/spacy/__init__.py` | ~20 | spaCy package init |

**Deliverable:** NLP package skeleton ready for integrations

---

### Session 2: spaCy Analyzer & Checkers
**Files to create:** 2 medium files
**Estimated lines:** ~400 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/spacy/analyzer.py` | ~200 | Core SpacyAnalyzer class |
| `nlp/spacy/checkers.py` | ~200 | Enhanced subject-verb, dangling modifier, complexity checkers |

**Deliverable:** Full spaCy integration with 3 new checkers

---

### Session 3: LanguageTool Integration
**Files to create:** 3 small files
**Estimated lines:** ~300 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/languagetool/__init__.py` | ~20 | Package init |
| `nlp/languagetool/client.py` | ~150 | LanguageTool wrapper (singleton) |
| `nlp/languagetool/checker.py` | ~130 | Comprehensive grammar checker |

**Deliverable:** 3000+ grammar rules via LanguageTool

---

### Session 4: Spelling Enhancement
**Files to create:** 4 files
**Estimated lines:** ~400 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/spelling/__init__.py` | ~20 | Package init |
| `nlp/spelling/symspell.py` | ~150 | SymSpellPy integration |
| `nlp/spelling/enchant.py` | ~130 | PyEnchant + domain dictionaries |
| `nlp/spelling/checker.py` | ~100 | Combined enhanced spell checker |

**Plus dictionaries:**
| File | Lines | Purpose |
|------|-------|---------|
| `dictionaries/aerospace.txt` | ~200 | Aerospace terminology |
| `dictionaries/defense.txt` | ~150 | Defense terminology |
| `dictionaries/software.txt` | ~150 | Software terminology |

**Deliverable:** 500K+ word spelling with domain support

---

### Session 5: Readability Enhancement
**Files to create:** 2 small files
**Estimated lines:** ~200 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/readability/__init__.py` | ~20 | Package init |
| `nlp/readability/enhanced.py` | ~180 | Textstat integration with recommendations |

**Deliverable:** 5 additional readability metrics + recommendations

---

### Session 6: Style Checking (Proselint)
**Files to create:** 3 small files
**Estimated lines:** ~200 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/style/__init__.py` | ~20 | Package init |
| `nlp/style/proselint.py` | ~100 | Proselint wrapper |
| `nlp/style/checker.py` | ~80 | Style checker (non-overlapping rules) |

**Deliverable:** Professional editorial style rules

---

### Session 7: Verb/Tense Analysis
**Files to create:** 3 small files
**Estimated lines:** ~250 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/verbs/__init__.py` | ~20 | Package init |
| `nlp/verbs/pattern_en.py` | ~130 | Pattern.en integration |
| `nlp/verbs/checker.py` | ~100 | Tense consistency checker |

**Deliverable:** Verb tense consistency checking

---

### Session 8: Semantic Analysis (WordNet)
**Files to create:** 3 small files
**Estimated lines:** ~250 total

| File | Lines | Purpose |
|------|-------|---------|
| `nlp/semantics/__init__.py` | ~20 | Package init |
| `nlp/semantics/wordnet.py` | ~130 | WordNet integration |
| `nlp/semantics/checker.py` | ~100 | Terminology consistency checker |

**Deliverable:** Semantic terminology consistency

---

### Session 9: Integration & Core.py Updates
**Files to modify:** 2 files
**Estimated changes:** ~150 lines

| File | Changes | Purpose |
|------|---------|---------|
| `core.py` | ~100 lines | Import and run NLP checkers |
| `app.py` | ~50 lines | Add NLP configuration endpoints |

**Deliverable:** Full integration with existing pipeline

---

### Session 10: Testing & Documentation
**Files to create:** 8 test files + docs
**Estimated lines:** ~400 total

| File | Lines | Purpose |
|------|-------|---------|
| `tests/nlp/test_spacy.py` | ~50 | spaCy tests |
| `tests/nlp/test_languagetool.py` | ~50 | LanguageTool tests |
| `tests/nlp/test_spelling.py` | ~50 | Spelling tests |
| ... | ... | ... |
| `docs/NLP_USAGE.md` | ~100 | User documentation |

**Deliverable:** Complete test coverage and documentation

---

## Session Execution Order

```
┌─────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASES                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1: FOUNDATION (Sessions 1-2)                         │
│  ┌─────────────┐    ┌─────────────┐                         │
│  │ Session 1   │───▶│ Session 2   │                         │
│  │ NLP Package │    │ spaCy Full  │                         │
│  │ Skeleton    │    │ Integration │                         │
│  └─────────────┘    └─────────────┘                         │
│         │                  │                                 │
│         ▼                  ▼                                 │
│  PHASE 2: HIGH-IMPACT (Sessions 3-4)                        │
│  ┌─────────────┐    ┌─────────────┐                         │
│  │ Session 3   │    │ Session 4   │  ← Can run parallel     │
│  │LanguageTool │    │ Spelling    │                         │
│  └─────────────┘    └─────────────┘                         │
│         │                  │                                 │
│         ▼                  ▼                                 │
│  PHASE 3: ENHANCEMENT (Sessions 5-8)                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │Session 5  │ │Session 6  │ │Session 7  │ │Session 8  │   │
│  │Readability│ │Proselint  │ │Verb/Tense │ │WordNet    │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│         │           │             │             │            │
│         └───────────┴─────────────┴─────────────┘            │
│                           │                                  │
│                           ▼                                  │
│  PHASE 4: FINALIZATION (Sessions 9-10)                      │
│  ┌─────────────┐    ┌─────────────┐                         │
│  │ Session 9   │───▶│ Session 10  │                         │
│  │ Integration │    │ Testing     │                         │
│  └─────────────┘    └─────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start: This Session

Given current context usage, we can safely complete **Session 1** now:

### Session 1 Deliverables
1. `nlp/__init__.py` - Package init with lazy loading
2. `nlp/config.py` - Centralized NLP configuration
3. `nlp/base.py` - Base classes for integrations
4. `nlp/spacy/__init__.py` - spaCy subpackage init

This creates the foundation for all subsequent integrations.

---

## Dependencies Installation Script

```bash
#!/bin/bash
# install_nlp_deps.sh

echo "Installing NLP dependencies for AEGIS..."

# Core NLP
pip install spacy>=3.7.0

# Download spaCy model (requires internet)
python -m spacy download en_core_web_md

# Grammar
pip install language-tool-python>=2.8.0

# Spelling
pip install symspellpy>=6.9.0
pip install pyenchant>=3.2.0

# Readability
pip install textstat>=0.7.3

# Style
pip install proselint>=0.14.0

# Verb analysis (may need special handling)
pip install pattern>=3.6

# Semantics
pip install nltk>=3.8.0
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt')"

echo "Done! All NLP dependencies installed."
```

---

## Rollback Strategy

Each session creates independent modules. If issues arise:

1. **Module-level rollback**: Delete problematic module, others still work
2. **Feature flags**: All integrations can be disabled via config
3. **Lazy loading**: Unused modules never import, no performance impact
4. **No core.py changes until Session 9**: Existing functionality untouched

---

## Success Criteria Per Session

| Session | Success Criteria |
|---------|-----------------|
| 1 | `from nlp import config` works |
| 2 | `SpacyAnalyzer().analyze("test")` works |
| 3 | `LanguageToolChecker().check("test")` works |
| 4 | `EnhancedSpellChecker().check_text("test")` works |
| 5 | `EnhancedReadabilityCalculator().analyze("test")` works |
| 6 | `ProselintChecker().check("test")` works |
| 7 | `TenseConsistencyChecker().check_paragraph("test")` works |
| 8 | `TerminologyConsistencyChecker().check_document([])` works |
| 9 | New checkers appear in review results |
| 10 | All tests pass |

---

## Recommended: Start Session 1 Now

We have enough context remaining to safely complete Session 1 (the foundation files). This will:

1. Create the `nlp/` package structure
2. Set up configuration system
3. Establish base classes
4. Prepare for spaCy integration

Shall I proceed with Session 1 implementation?
