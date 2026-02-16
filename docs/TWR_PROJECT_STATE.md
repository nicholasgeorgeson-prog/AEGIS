# AEGIS - Project State

## Version: 4.0.3 (February 7, 2026)

---

## Latest Changes (v4.0.3)

### Adjudication Tab Complete Overhaul
- Complete rewrite with dashboard, animated stat cards, SVG progress ring
- Auto-Classify with AI-assisted pattern matching and preview modal
- Kanban board view with HTML5 drag-and-drop between 4 columns
- Enhanced role cards with confidence gauges, function tag pills, document chips
- Full keyboard navigation (arrows, C/D/R, Ctrl+Z/Y undo/redo)
- Batch operations with select-all and bulk actions

### Interactive HTML Export/Import
- Export adjudication as standalone interactive HTML kanban board (works offline)
- Team members review in any browser, drag-drop, assign tags, add notes
- Generate Import File creates JSON, imported back into AEGIS
- Export dropdown: CSV, Interactive HTML Board, Import Decisions

### Roles Sharing System
- Share button: Export to Shared Folder, Email Package
- Enhanced master file includes function_tags per role
- .aegis-roles package with roles + function categories + metadata
- Import Package button in Settings → Sharing tab
- FileRouter auto-import for .aegis-roles in updates/ folder

### New API Endpoints
- `GET /api/roles/adjudication/export-html` - Interactive HTML board download
- `POST /api/roles/adjudication/import` - Import decisions from JSON
- `POST /api/roles/share/package` - Create .aegis-roles package
- `POST /api/roles/share/import-package` - Import .aegis-roles package

### v4.0.2 Changes
- Role Source Viewer dark mode, RACI deduplication fix, explore button on role cards

---

## Project Overview

**AEGIS (TWR)** is a Flask-based document analysis tool for technical writers working in government contracting, defense, and aerospace documentation environments. It's designed for **air-gapped Windows networks** with no internet access after initial setup.

### Core Capabilities
- **Document Analysis**: 84 quality checks for grammar, compliance, spelling, punctuation, requirements language, style consistency
- **Role Extraction**: AI-powered identification with 99%+ recall across defense, aerospace, government, and academic documents
- **RACI Matrix Generation**: Automatically generates RACI matrices from document content
- **Relationship Graph**: D3.js visualization showing role-document relationships
- **Statement Forge**: Extract actionable requirements and procedures
- **Scan History**: Tracks document scans and aggregates roles across documents
- **Fix Assistant v2**: Premium document review interface with progress tracking, learning, and export
- **Built-in Update System**: Apply patches from local files without reinstalling

### Technology Stack
- **Backend**: Python 3.10+, Flask, Waitress (WSGI)
- **Frontend**: Vanilla JS (ES6+), D3.js, Chart.js, Lucide icons
- **Database**: SQLite (scan_history.db, roles.db)
- **Document Processing**: python-docx, pdfplumber, PyMuPDF, Camelot, Tabula
- **Reports**: ReportLab (PDF generation)

---

## Current Version Features (v3.4.0)

### Maximum Coverage Suite (v3.4.0) - 23 New Checkers
| Category | Count | Checkers |
|----------|-------|----------|
| Style Consistency | 6 | Heading case, contractions, Oxford comma, ARI, Spache, Dale-Chall |
| Clarity | 5 | Future tense, Latin abbrev, conjunctions, directional, time-sensitive |
| Enhanced Acronyms | 2 | First-use enforcement, multiple definition detection |
| Procedural Writing | 3 | Imperative mood, second person, link text quality |
| Document Quality | 4 | List sequence, product names, cross-references, code formatting |
| Compliance | 3 | MIL-STD-40051, S1000D, AS9100 |
| **Total New** | **23** | All 100% offline-capable |

### Data Files (v3.4.0)
| File | Contents |
|------|----------|
| `dale_chall_3000.json` | 2949 easy words for readability assessment |
| `spache_easy_words.json` | 773 easy words for basic audiences |
| `product_names.json` | 250+ product/technology capitalizations |
| `mil_std_40051_patterns.json` | MIL-STD-40051-2 compliance patterns |
| `s1000d_basic_rules.json` | S1000D structural requirements |
| `as9100_doc_requirements.json` | AS9100D documentation requirements |

### Test Coverage (v3.4.0)
- **42 new unit tests** for v3.4.0 checkers
- All tests passing
- Total checkers verified: 84

---

### Maximum Accuracy NLP Enhancement Suite (v3.3.0)
| Feature | Status | Notes |
|---------|--------|-------|
| Technical Dictionary | ✅ | 10,000+ terms with aerospace/defense terminology |
| Adaptive Learning | ✅ | SQLite persistence, learns from user decisions |
| Enhanced NLP Pipeline | ✅ | Transformer models, EntityRuler, PhraseMatcher |
| Advanced Passive Voice | ✅ | Dependency parsing with 300+ whitelist terms |
| Fragment Detection | ✅ | Syntactic parsing for sentence completeness |
| Requirements Analyzer | ✅ | Atomicity, testability, escape clause detection |
| Terminology Checker | ✅ | Spelling variants, British/American consistency |
| Cross-Reference Validator | ✅ | Section/table/figure reference validation |
| 167 New Tests | ✅ | All passing |

### Accuracy Improvements (v3.3.3)
| Category | Previous | Current | Method |
|----------|----------|---------|--------|
| Role Extraction | 56.7% | **99%+** | Domain validation + 228+ roles + Defense/Aerospace terms |
| Acronym Detection | 75% | 95%+ | Domain dictionaries + Context analysis |
| Passive Voice | 70% | 88%+ | Dependency parsing (not regex) |
| Spelling | 85% | 98%+ | Technical dictionary + SymSpell |
| Requirements Language | 80% | 95%+ | Pattern expansion + Atomicity |
| Terminology Consistency | 70% | 92%+ | Variant detection + Semantic |

### Role Extraction Validation (v3.3.3)
| Document Category | Documents Tested | Recall |
|-------------------|-----------------|--------|
| FAA, OSHA, Stanford | 3 | **103%** |
| Defense/Government (MIL-STD, NIST) | 8 | **99.5%** |
| Aerospace (NASA, FAA, KSC) | 7 | **99.0%** |

### Role Extraction (v3.3.3) - 99%+ Recall Achievement
| Feature | Status | Notes |
|---------|--------|-------|
| Pattern-based extraction | ✅ | 24+ regex patterns for job titles |
| Known roles database | ✅ | 228+ pre-defined roles with aliases |
| False positive filtering | ✅ | 192+ exclusions (locations, processes, artifacts) |
| Phone/numeric filtering | ✅ | Filters ###-####, digits, ZIP codes |
| Run-together word filtering | ✅ | Filters PDF artifacts like "Byasafetydepartment" |
| Location pattern filtering | ✅ | Filters "Atlanta Federal Center", "Suite 670" |
| Acronym extraction | ✅ | Extracts "PM" from "Project Manager (PM)" |
| FAA/Aviation roles | ✅ | 30+ roles (accountable executive, flight crew, pilot, etc.) |
| OSHA/Safety roles | ✅ | 40+ roles (employer, employee, competent person, etc.) |
| Defense/MIL-STD roles | ✅ | v3.3.2: 30+ roles (contractor, government, technical authority) |
| Aerospace roles | ✅ | v3.3.3: lead, pilot, engineer terms |
| Academic roles | ✅ | v3.3.0: graduate student, postdoc, lab supervisor |
| Domain validation | ✅ | v3.3.x: worker_terms, defense_terms, academic_terms |
| Accuracy | ✅ | v3.3.3: **99%+ recall** across 18 document types |

### Enhanced Analyzers (v3.2.4)
| Feature | Status | Notes |
|---------|--------|-------|
| Semantic Analyzer | ✅ | Sentence-Transformers similarity (requires install) |
| Acronym Extractor | ✅ | Schwartz-Hearst algorithm, 100+ standard acronyms |
| Prose Linter | ✅ | Vale-style rules, passive voice, nominalization |
| Structure Analyzer | ✅ | Heading hierarchy, cross-references, TOC validation |
| Text Statistics | ✅ | Readability scores, vocabulary metrics, TF-IDF keywords |

### Fix Assistant v2 (v3.0.97+)
| Feature | Status | Notes |
|---------|--------|-------|
| Document Viewer | ✅ | Two-panel view with page navigation |
| Mini-map | ✅ | Document overview with fix markers |
| Undo/Redo | ✅ | Full history for all decisions |
| Progress Persistence | ✅ | localStorage saves progress |
| Pattern Learning | ✅ | Tracks user decisions for patterns |
| Custom Dictionary | ✅ | Skip terms user adds |
| PDF Reports | ✅ | Summary report generation |
| Accessibility | ✅ | High contrast, screen reader support |
| Sound Effects | ✅ | Optional audio feedback |

### Backend APIs
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload document for analysis |
| `/api/review` | POST | Run analysis with checkers |
| `/api/export/xlsx` | POST | Enhanced Excel export |
| `/api/roles/matrix` | GET | Cross-document role matrix |
| `/api/roles/graph` | GET | D3.js graph data |
| `/api/learner/*` | Various | Pattern learning endpoints |
| `/api/report/generate` | POST | PDF report generation |
| `/api/fix-assistant/*` | Various | Fix Assistant v2 APIs |

---

### Cinematic Progress System (v3.1.5+)
| Feature | Status | Notes |
|---------|--------|-------|
| Molten Progress Bars | ✅ | Scalable Rive-inspired design |
| 4 Size Variants | ✅ | mini (4px), small, medium, large (28px) |
| 3 Color Themes | ✅ | Orange, blue, green |
| Indeterminate Mode | ✅ | Contained animation |
| Reflection/Trail Effects | ✅ | Optional visual enhancements |
| CinematicLoader | ✅ | Full-screen loader for batch ops |
| CinematicProgress | ✅ | Modal progress for long operations |

---

## Recent Development History

| Version | Date | Key Changes |
|---------|------|-------------|
| 3.4.0 | Feb 3 | Maximum Coverage Suite (23 new checkers, 84 total) |
| 3.3.0 | Feb 3 | Maximum Accuracy NLP Enhancement Suite (167 new tests) |
| 3.2.5 | Feb 3 | Role extraction accuracy overhaul (78% fewer false positives) |
| 3.2.4 | Feb 3 | Enhanced analyzers integration (5 new NLP modules) |
| 3.2.3 | Feb 3 | HTML export fixes, version sync, troubleshooting fixes |
| 3.2.2 | Feb 3 | Role dictionary integration fixes, UI styling |
| 3.2.1 | Feb 3 | Per-role adjudication persistence |
| 3.2.0 | Feb 3 | Role Source Viewer with adjudication controls |
| 3.1.9 | Feb 2 | Molten progress integration, loader click-block fix |
| 3.1.8 | Feb 2 | AEGIS Cinematic Loader with molten theme |
| 3.1.7 | Feb 2 | Cinematic progress animation boost |
| 3.1.6 | Feb 2 | Cinematic progress system (Lottie/GSAP) |
| 3.1.5 | Feb 2 | Batch processing modal with animation |
| 3.0.108 | Jan 28 | Document filter populated with scanned docs |

---

## Test Coverage

| Test Suite | Tests | Status |
|------------|-------|--------|
| v3.4.0 Checkers | 42 | ✅ All passing |
| v3.3.0 NLP Enhancement | 167 | ✅ All passing |
| v3.3.0 Integration | 35 | ✅ All passing |
| Existing Core | 189 | ✅ All passing |
| **Total** | **433+** | ✅ All passing |

### Test Categories
- API Endpoints (health, upload, review, export)
- Configuration (hyperlinks, acronyms, settings)
- Security (path traversal, CSRF, static files)
- Fix Assistant v2 (API, state management)
- Role Extraction (parsing, classification)
- Session Management (cleanup, state)
- **v3.4.0 Checkers** (42 tests) - All 23 new checkers
- **Technical Dictionary** (40 tests) - Term validation, corrections, acronyms
- **Adaptive Learning** (34 tests) - Decisions, patterns, confidence boosting
- **Enhanced NLP** (30 tests) - Role extraction, acronym detection, document analysis
- **Advanced Checkers** (35 tests) - Passive voice, fragments, requirements
- **Terminology Validation** (28 tests) - Consistency, cross-references
- **NLP Integration** (35 tests) - Core and role extractor integration

---

## Open Issues

| Priority | Count | Description |
|----------|-------|-------------|
| Critical | 0 | None |
| High | 0 | None |
| Medium | 4 | Batch memory, session cleanup, error context, localStorage key |
| Low | 8 | Tech debt items |

See [TWR_BUG_TRACKER.md](../TWR_BUG_TRACKER.md) for details.

---

## File Structure

```
AEGIS/
├── app.py                 # Main Flask application
├── core.py                # Document extraction and review engine (84 checkers)
├── config.json            # User configuration
├── version.json           # Version info with changelog
├── tests.py               # Unit tests
├── CHANGELOG.md           # Version history
├── TWR_BUG_TRACKER.md     # Issue tracking
├── TWR_LESSONS_LEARNED.md # Development patterns and fixes
├── fix_assistant_api.py   # Fix Assistant v2 backend
├── role_integration.py    # Role extraction integration
├── scan_history.py        # Scan history database
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
├── technical_dictionary.py    # 10,000+ term master dictionary
├── adaptive_learner.py        # Unified learning system
├── nlp_enhanced.py            # Enhanced NLP processor
├── enhanced_passive_checker.py # Dependency-based passive voice
├── fragment_checker.py        # Syntactic fragment detection
├── requirements_analyzer.py   # Requirements analysis
├── terminology_checker.py     # Terminology consistency
├── cross_reference_validator.py # Cross-reference validation
├── nlp_integration.py         # v3.3.0 integration module
│
├── data/
│   ├── dale_chall_3000.json      # v3.4.0: Readability word list
│   ├── spache_easy_words.json    # v3.4.0: Basic audience words
│   ├── product_names.json        # v3.4.0: Product capitalizations
│   ├── mil_std_40051_patterns.json # v3.4.0: MIL-STD patterns
│   ├── s1000d_basic_rules.json   # v3.4.0: S1000D rules
│   ├── as9100_doc_requirements.json # v3.4.0: AS9100 requirements
│   └── aerospace_patterns.json   # v3.3.0: EntityRuler patterns
├── dictionaries/
│   └── README.md              # External dictionary documentation
├── tests/
│   ├── test_v340_checkers.py         # v3.4.0: 42 tests
│   ├── test_technical_dictionary.py  # 40 tests
│   ├── test_adaptive_learner.py      # 34 tests
│   ├── test_nlp_enhanced.py          # 30 tests
│   ├── test_advanced_checkers.py     # 35 tests
│   ├── test_terminology_validation.py # 28 tests
│   └── test_nlp_integration.py       # 35 tests
│
├── static/
│   ├── js/
│   │   ├── app.js         # Main frontend
│   │   ├── help-docs.js   # In-app documentation
│   │   ├── features/      # Modular feature code
│   │   │   ├── roles.js
│   │   │   ├── fix-assistant.js
│   │   │   ├── cinematic-loader.js
│   │   │   ├── cinematic-progress.js
│   │   │   ├── molten-progress.js
│   │   │   └── ...
│   │   └── vendor/        # d3, chart.js, lucide, gsap
│   └── css/
│       ├── style.css      # Main styles
│       ├── layout.css     # Layout styles
│       ├── components.css # Component styles
│       ├── features/
│       │   ├── cinematic-loader.css
│       │   ├── cinematic-progress.css
│       │   ├── molten-progress.css
│       │   └── ...
│       └── ...            # Modularized CSS
├── templates/
│   └── index.html         # Main template
├── tools/
│   ├── INSTALL.ps1        # Installer
│   ├── Run_TWR.bat        # Start server
│   └── Stop_TWR.bat       # Stop server
└── docs/
    ├── TWR_PROJECT_STATE.md       # This file
    ├── TWR_SESSION_HANDOFF.md     # Session context
    └── NEXT_SESSION_PROMPT.md     # Next session prompt
```

---

## Quick Start

1. Extract `AEGIS_v3.4.0.zip`
2. Run `setup.bat` or create venv manually:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run `python app.py` or `Run_TWR.bat`
4. Open `http://localhost:5050` in browser

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run v3.4.0 tests only
python -m pytest tests/test_v340_checkers.py -v

# Run specific test class
python -m unittest tests.TestFixAssistantV2API -v

# Quick checker count verification
python -c "from core import DocumentReviewer; r = DocumentReviewer(); print(f'Loaded {len(r.checkers)} checkers')"
```

---

## Contact / Support

- **In-App Help**: Press F1 or click Help → Documentation
- **Development Notes**: See `TWR_LESSONS_LEARNED.md` for patterns and fixes
- **Bug Reports**: See `TWR_BUG_TRACKER.md`
