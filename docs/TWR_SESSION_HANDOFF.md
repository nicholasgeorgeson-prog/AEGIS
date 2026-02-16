# AEGIS Session Handoff
## Current Version: 3.4.0 (February 3, 2026)

---

## Quick Context for New Session

**What is TWR?** A Flask-based document analysis tool for technical writers in air-gapped government/aerospace environments.

**What just happened?** Added 23 new offline-only checkers for comprehensive style, clarity, procedural writing, and compliance validation.

**Total Checkers: 84** (61 existing + 23 new)

---

## v3.4.0 Maximum Coverage Suite (23 New Checkers)

### Style Consistency Checkers (6)
| Checker | Purpose | Data File |
|---------|---------|-----------|
| `HeadingCaseConsistencyChecker` | Validates heading capitalization (title/sentence/all caps) | - |
| `ContractionConsistencyChecker` | Detects mixed contraction usage ("don't" vs "do not") | - |
| `OxfordCommaConsistencyChecker` | Validates serial comma consistency | - |
| `ARIProminenceChecker` | Automated Readability Index assessment | - |
| `SpacheReadabilityChecker` | Spache formula for basic audiences | `spache_easy_words.json` |
| `DaleChallEnhancedChecker` | Enhanced Dale-Chall with 3000-word list | `dale_chall_3000.json` |

### Clarity Checkers (5)
| Checker | Purpose |
|---------|---------|
| `FutureTenseChecker` | Flags "will display" patterns (prefer present tense) |
| `LatinAbbreviationChecker` | Warns about i.e., e.g., etc., et al. |
| `SentenceInitialConjunctionChecker` | Flags And, But, So at sentence start |
| `DirectionalLanguageChecker` | Flags above/below/left/right (fragile in responsive layouts) |
| `TimeSensitiveLanguageChecker` | Flags currently/now/recently (becomes stale) |

### Enhanced Acronym Checkers (2)
| Checker | Purpose |
|---------|---------|
| `AcronymFirstUseChecker` | Enforces definition on first use |
| `AcronymMultipleDefinitionChecker` | Flags acronyms defined multiple times |

### Procedural Writing Checkers (3)
| Checker | Purpose |
|---------|---------|
| `ImperativeMoodChecker` | Validates procedures use imperative mood |
| `SecondPersonChecker` | Prefers "you" over "the user" |
| `LinkTextQualityChecker` | Flags "click here" and vague link text |

### Document Quality Checkers (4)
| Checker | Purpose | Data File |
|---------|---------|-----------|
| `NumberedListSequenceChecker` | Validates 1, 2, 3 not 1, 2, 4 | - |
| `ProductNameConsistencyChecker` | Validates JavaScript not Javascript | `product_names.json` |
| `CrossReferenceTargetChecker` | Validates Table 5 exists | - |
| `CodeFormattingConsistencyChecker` | Flags unformatted code | - |

### Compliance Checkers (3)
| Checker | Purpose | Data File |
|---------|---------|-----------|
| `MILStd40051Checker` | MIL-STD-40051-2 technical manual compliance | `mil_std_40051_patterns.json` |
| `S1000DBasicChecker` | S1000D/IETM structural validation | `s1000d_basic_rules.json` |
| `AS9100DocChecker` | AS9100D documentation requirements | `as9100_doc_requirements.json` |

---

## v3.4.0 Data Files

| File | Contents | Size |
|------|----------|------|
| `data/dale_chall_3000.json` | 2949 easy words for readability | ~30KB |
| `data/spache_easy_words.json` | 773 easy words for basic audiences | ~8KB |
| `data/product_names.json` | 250+ product/technology capitalizations | ~15KB |
| `data/mil_std_40051_patterns.json` | MIL-STD-40051-2 compliance patterns | ~10KB |
| `data/s1000d_basic_rules.json` | S1000D structural requirements | ~8KB |
| `data/as9100_doc_requirements.json` | AS9100D documentation requirements | ~6KB |

---

## v3.4.0 Option Mappings (core.py)

```python
# Style Consistency
'check_heading_case': 'heading_case_consistency',
'check_contraction_consistency': 'contraction_consistency',
'check_oxford_comma': 'oxford_comma_consistency',
'check_ari': 'ari_prominence',
'check_spache': 'spache_readability',
'check_dale_chall': 'dale_chall_enhanced',

# Clarity
'check_future_tense': 'future_tense',
'check_latin_abbreviations': 'latin_abbreviations',
'check_sentence_initial_conjunction': 'sentence_initial_conjunction',
'check_directional_language': 'directional_language',
'check_time_sensitive_language': 'time_sensitive_language',

# Enhanced Acronyms
'check_acronym_first_use': 'acronym_first_use',
'check_acronym_multiple_definition': 'acronym_multiple_definition',

# Procedural Writing
'check_imperative_mood': 'imperative_mood',
'check_second_person': 'second_person',
'check_link_text_quality': 'link_text_quality',

# Document Quality
'check_numbered_list_sequence': 'numbered_list_sequence',
'check_product_name_consistency': 'product_name_consistency',
'check_cross_reference_targets': 'cross_reference_target',
'check_code_formatting': 'code_formatting_consistency',

# Compliance
'check_mil_std_40051': 'mil_std_40051',
'check_s1000d': 's1000d_basic',
'check_as9100': 'as9100_doc',
```

---

## v3.4.0 Lessons Learned

### 1. JSON Data Structure Handling
Compliance checkers load rules from JSON files but need fallback structures. Handle both formats:
```python
prohibited = self.rules.get('prohibited_patterns', {})
if isinstance(prohibited, dict):
    patterns_list = prohibited.get('patterns', [])
elif isinstance(prohibited, list):
    patterns_list = prohibited
```

### 2. Option Mapping Naming
Option names in `core.py` must exactly match checker names from factory functions:
- **Wrong**: `'check_cross_reference_targets': 'cross_reference_targets'` (plural)
- **Right**: `'check_cross_reference_targets': 'cross_reference_target'` (singular)

### 3. Test Assertion Flexibility
Data files may have slightly different counts than expected:
```python
# Flexible assertion
self.assertGreater(len(words), 2900)  # Dale-Chall has 2949, not exactly 3000
```

### 4. BaseChecker Interface Pattern
All v3.4.0 checkers follow the same interface:
```python
class MyChecker(BaseChecker):
    name = 'my_checker'
    description = 'What this checker does'
    category = 'Category Name'

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        issues = []
        for para_idx, text in paragraphs:
            if problem_found:
                issues.append({
                    'type': self.name,
                    'category': self.category,
                    'severity': 'info|warning|error',
                    'message': 'Issue description',
                    'context': text[:100],
                    'paragraph': para_idx
                })
        return issues
```

---

## Previous Versions Reference

### v3.3.0 - Maximum Accuracy NLP Enhancement Suite
| Module | Purpose |
|--------|---------|
| `technical_dictionary.py` | 10,000+ aerospace/defense terms |
| `adaptive_learner.py` | Learning system with SQLite |
| `nlp_enhanced.py` | Enhanced NLP with EntityRuler |
| `enhanced_passive_checker.py` | Dependency parsing passive detection |
| `fragment_checker.py` | Sentence fragment detection |
| `requirements_analyzer.py` | Requirements quality analysis |
| `terminology_checker.py` | Terminology consistency |
| `cross_reference_validator.py` | Cross-reference validation |
| `nlp_integration.py` | Integration module for v3.3.0 |

### v3.2.x - Role Extraction & Adjudication
- Role Source Viewer with adjudication controls
- 94.7% precision role extraction
- Phone/numeric filtering, run-together word filtering
- FAA/Aviation and OSHA/Safety role definitions

### v3.1.x - Progress & UI
- Molten progress bars
- Cinematic loader
- Fix Assistant v2 with learning

---

## API Endpoints Reference

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload document for analysis |
| `/api/review` | POST | Run analysis with checkers |
| `/api/export/xlsx` | POST | Enhanced Excel export |

### Role Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/roles/matrix` | GET | Cross-document role matrix |
| `/api/roles/graph` | GET | D3.js graph data |
| `/api/roles/adjudicate` | POST | Save adjudication decision |
| `/api/roles/dictionary` | GET/POST | Role dictionary CRUD |

### Analyzer Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyzers/status` | GET | Get status of all analyzers |
| `/api/analyzers/semantic/similar` | POST | Find similar sentences |
| `/api/analyzers/acronyms/extract` | POST | Extract acronyms |
| `/api/analyzers/statistics` | POST | Get text statistics |

### Learner Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/learner/record` | POST | Record review decisions |
| `/api/learner/predict` | POST | Get predictions |
| `/api/learner/patterns` | GET | Get learned patterns |
| `/api/learner/dictionary` | GET/POST/DELETE | Custom dictionary |

---

## File Structure (Key Files)

```
AEGIS/
├── app.py                    # Main Flask application
├── core.py                   # Document review engine (84 checkers)
├── version.json              # Version info
│
│   # v3.4.0 Maximum Coverage Suite
├── style_consistency_checkers.py    # 6 checkers
├── clarity_checkers.py              # 5 checkers
├── acronym_enhanced_checkers.py     # 2 checkers
├── procedural_writing_checkers.py   # 3 checkers
├── document_quality_checkers.py     # 4 checkers
├── compliance_checkers.py           # 3 checkers
│
│   # v3.3.0 NLP Enhancement Suite
├── technical_dictionary.py
├── adaptive_learner.py
├── nlp_enhanced.py
├── enhanced_passive_checker.py
├── fragment_checker.py
├── requirements_analyzer.py
├── terminology_checker.py
├── cross_reference_validator.py
├── nlp_integration.py
│
│   # Data Files
├── data/
│   ├── dale_chall_3000.json
│   ├── spache_easy_words.json
│   ├── product_names.json
│   ├── mil_std_40051_patterns.json
│   ├── s1000d_basic_rules.json
│   ├── as9100_doc_requirements.json
│   └── aerospace_patterns.json
│
│   # Tests
├── tests/
│   ├── test_v340_checkers.py        # 42 tests for v3.4.0
│   ├── test_technical_dictionary.py
│   ├── test_adaptive_learner.py
│   └── ...
│
│   # Documentation
├── docs/
│   ├── NEXT_SESSION_PROMPT.md
│   ├── TWR_SESSION_HANDOFF.md
│   └── TWR_PROJECT_STATE.md
│
└── static/js/help-docs.js    # In-app help documentation
```

---

## Testing

```bash
# Run v3.4.0 tests
python -m pytest tests/test_v340_checkers.py -v

# Run all tests
python -m pytest tests/ -v

# Quick syntax check
python -c "from core import DocumentReviewer; r = DocumentReviewer(); print(f'Loaded {len(r.checkers)} checkers')"
```

---

## Start Server

```bash
cd /Users/nick/Desktop/Work_Tools/AEGIS
TWR_CSRF=false python3 app.py
# If port conflict: lsof -ti:5050 | xargs kill -9
```

Open http://localhost:5050

---

## Documentation Update Checklist

When making changes, update these files together:
- [ ] `version.json` - version number
- [ ] `CHANGELOG.md` - detailed changelog
- [ ] `README.md` - user-facing documentation
- [ ] `docs/TWR_PROJECT_STATE.md` - project state
- [ ] `docs/TWR_SESSION_HANDOFF.md` - session context
- [ ] `docs/NEXT_SESSION_PROMPT.md` - next session prompt
- [ ] `static/js/help-docs.js` - in-app help (version history)
- [ ] `TWR_LESSONS_LEARNED.md` - development patterns (if applicable)

---

**Ready for the next task!**
