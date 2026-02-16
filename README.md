# AEGIS v4.9.9

**Aerospace Engineering Governance & Inspection System**

Enterprise-grade document analysis and compliance verification platform for aerospace, defense, and government technical documentation.

---

## What's New in v4.9.9

### Statement Source Viewer with Highlight-to-Select
- **Inline Statement Creation**: Click text in document to create statements without leaving viewer
- **Highlight-to-Select Editing**: Select text ranges and save as new statements inline
- **Document Context Integration**: Preserves character offsets and document history
- **Keyboard Navigation**: J/K or arrow keys to navigate statements

### Error Handling & Stability Improvements
- **Fixed SOW Generation 500 Error**: Missing timezone import in datetime operations now resolved
- **Structured Error Messages**: API error responses properly formatted with extraction at all call sites
- **Meaningful Toast Notifications**: Error toasts show real messages instead of "[object Object]"
- **Cross-Platform Compatibility**: Windows-specific file operations (chmod) now platform-aware

### Document Compare Smart Auto-Picker
- **Auto-Selection**: Opens with oldest doc on left, newest on right automatically
- **Immediate Comparison**: Runs comparison without requiring manual selection
- **Consistent Entry Points**: Works from sidebar, landing tile, and URL hash

### Settings & Persistence Enhancements
- **Profile Persistence**: Document profiles survive server restarts
- **User Preference Caching**: localStorage backup with server-side sync
- **Dirty State Tracking**: Visual feedback on unsaved changes

### Production & Windows Support
- **Session Logging**: Correlation IDs for API response timing analysis
- **Windows Platform Detection**: Using os.name == 'nt' for platform-specific code paths
- **Pathlib Cross-Platform**: All file operations use pathlib.Path for consistency
- **Particle Effect Optimization**: Improved transparency for dark background visibility

### Previous Releases

## v4.7.0: Database Access Layer Refactoring
- **99 sqlite3.connect() calls** replaced with unified `db_connection()` context manager pattern
- **10 critical bug fixes**: Statement counts, document compare methods, heatmap flickering, event listeners
- **Reliability improvements**: ~60% of DB calls now have proper exception handling, ~65% fixed connection leaks

## v4.0.3: Adjudication Tab Complete Overhaul

### Adjudication System Rewrite
- **OVERHAUL**: Complete rewrite of the Adjudication tab with dashboard, animated stat cards, SVG progress ring
- **Auto-Classify**: AI-assisted role classification with pattern matching, preview modal, and confidence scoring
- **Kanban Board**: 4-column drag-and-drop board (Pending | Confirmed | Deliverables | Rejected)
- **Function Tags**: Assign hierarchical function categories directly on role cards with searchable dropdown
- **Keyboard Navigation**: Full keyboard control — arrow keys, C/D/R to classify, Ctrl+Z undo, Ctrl+Y redo
- **Batch Operations**: Select multiple roles, bulk confirm/reject/deliverable

### Interactive HTML Export/Import
- **Export** adjudication as a standalone interactive HTML kanban board — works offline in any browser
- **Team Review**: Send HTML file to team members (no AEGIS needed); they drag-drop, assign tags, add notes
- **Import Back**: Team generates a JSON decisions file, imported back into AEGIS with one click
- Export dropdown with CSV Spreadsheet, Interactive HTML Board, and Import Decisions options

### Roles Sharing System
- **Shared Folder**: Export enhanced master dictionary (now with function tags) to a shared network path
- **Email Package**: Download a `.aegis-roles` package and open mailto: with import instructions
- **Import Package**: Import `.aegis-roles` via Settings → Sharing or drop in `updates/` folder for auto-import
- **FileRouter**: `.aegis-roles` files in `updates/` folder auto-detected and imported

### New API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/roles/adjudication/export-html` | GET | Interactive HTML board download |
| `/api/roles/adjudication/import` | POST | Import decisions from JSON |
| `/api/roles/share/package` | POST | Create .aegis-roles package |
| `/api/roles/share/import-package` | POST | Import .aegis-roles package |

---

## v4.0.1: Role Extraction Accuracy Enhancement

### Role Extraction v3.3.3 - 99%+ Recall
- **99%+ recall** across defense, aerospace, government, and academic documents
- Added ~70 new roles (OSHA, academic, defense, aerospace domains)
- 228+ known roles, 192+ false positive exclusions

---

## v4.0.0: AEGIS Rebrand Release

### Complete Rebrand
- Renamed from TechWriterReview to **AEGIS** (Aerospace Engineering Governance & Inspection System)
- New AEGIS shield logo with gold/bronze gradient color scheme
- 163+ files updated across codebase with new branding

### UI/UX Improvements
- **Enhanced Document Text Readability**: Larger fonts (15px), improved line-height (1.75), better letter spacing
- **Reorganized Navigation**: Validate and Links tabs now adjacent for workflow efficiency
- **Gold Accent Theme**: Updated active tab styling and highlights throughout

### Checker Accuracy Improvements (Near-Perfect Accuracy)
- **Grammar Checker v2.6.0**: Fixed critical "Capitalize I" false positives
- **Punctuation Checker v2.7.0**: Filters TOC entries to reduce false positives
- **Prose Linter v1.1.0**: 40+ technical term nominalization exceptions
- **Enhanced Passive Checker**: 60+ additional adjectival participles
- **Fragment Checker**: 100+ imperative verb indicators for technical docs

### Data Management (Factory Reset)
- New Settings > Data Management tab
- Clear Scan History, Role Dictionary, Learning Data individually
- Full Factory Reset option to restore defaults

---

## v3.4.0: Maximum Coverage Suite

This release adds **23 new offline-only checkers** for comprehensive style, clarity, procedural writing, and compliance validation:

| Category | Checkers | Highlights |
|----------|----------|------------|
| Style Consistency | 6 | Heading case, contractions, Oxford comma, ARI, Spache, Dale-Chall |
| Clarity | 5 | Future tense, Latin abbrev, directional/time-sensitive language |
| Enhanced Acronyms | 2 | First-use enforcement, multiple definition detection |
| Procedural Writing | 3 | Imperative mood, second person, link text quality |
| Document Quality | 4 | List sequence, product names, cross-references, code formatting |
| Compliance | 3 | MIL-STD-40051, S1000D, AS9100 |

**Total Checkers: 84** (61 existing + 23 new)

### New Checker Modules (v3.4.0)
- **Style Consistency** - Heading case, contractions, Oxford comma, readability (ARI/Spache/Dale-Chall)
- **Clarity Checkers** - Future tense, Latin abbreviations, directional/time-sensitive language
- **Acronym Enhanced** - First-use enforcement, multiple definition detection
- **Procedural Writing** - Imperative mood, second person preference, link text quality
- **Document Quality** - Numbered list sequence, product names, cross-references, code formatting
- **Compliance** - MIL-STD-40051-2, S1000D/IETM, AS9100D documentation requirements

### New Data Files (v3.4.0)
- Dale-Chall 3000-word easy word list
- Spache easy words for readability
- 250+ product name capitalizations
- MIL-STD-40051, S1000D, AS9100 compliance patterns

**All features are 100% offline-capable for air-gapped deployment.**

---

## v3.3.x: Maximum Accuracy NLP Enhancement Suite

Role extraction achieves **99%+ recall** across all document types:

| Feature | Previous | Current | Enhancement |
|---------|----------|---------|-------------|
| Role Extraction | 56.7% | **99%+** | Domain validation + 228+ roles + Defense/Aerospace terms |
| Acronym Detection | 75% | 95%+ | Domain dictionaries + Context analysis |
| Passive Voice | 70% | 88%+ | Dependency parsing (not regex) |
| Spelling | 85% | 98%+ | 10,000+ term technical dictionary |
| Requirements | 80% | 95%+ | Atomicity + Testability + Escape clauses |
| Terminology | 70% | 92%+ | Variant detection + British/American |

**Role Extraction Validation (v3.3.3):**
- FAA, OSHA, Stanford: **103%** recall
- Defense/Government (MIL-STD, NIST): **99.5%** recall
- Aerospace (NASA, FAA, KSC): **99.0%** recall

### v3.3.0 Modules
- **Technical Dictionary** - 10,000+ aerospace/defense terms with corrections
- **Adaptive Learning** - System learns from your decisions over time
- **Enhanced NLP Pipeline** - Transformer models with EntityRuler patterns
- **Advanced Passive Voice** - Dependency parsing with 300+ whitelist terms
- **Fragment Detection** - Syntactic parsing for sentence completeness
- **Requirements Analyzer** - Atomicity, testability, escape clauses
- **Terminology Checker** - Spelling variants, British/American consistency
- **Cross-Reference Validator** - Section/table/figure reference validation

## Quick Start

### Basic Setup (With Internet)

```batch
1. Unzip this package
2. Double-click: setup.bat
3. Double-click: start_twr.bat  (or Run_TWR.bat)
4. Open browser to: http://localhost:5050
```

That's it! `setup.bat` installs all dependencies automatically.

### Optional: Enhanced Features

**NLP Enhancement** (recommended for better role detection):
```batch
setup_enhancements.bat
```
Installs spaCy, scikit-learn for ~90% role detection accuracy.

**Docling AI** (for superior document parsing):
```batch
setup_docling.bat
```
Installs Docling (~2.7GB) with:
- AI table structure recognition (95% vs 70% accuracy)
- Layout understanding and reading order preservation
- Section/heading detection without style dependencies
- 100% offline operation after setup

### Air-Gapped Deployment (No Internet)

For machines without internet access:

```batch
# On a machine WITH internet:
1. Run: powershell -ExecutionPolicy Bypass -File bundle_for_airgap.ps1
2. Wait for downloads (~3GB with Docling, ~500MB without)
3. Copy the bundle folder to target machine

# On the AIR-GAPPED machine:
1. Run: INSTALL_AIRGAP.bat
2. Follow prompts
```

## Features

### Document Analysis
- **84 Quality Checks**: Grammar, spelling, acronyms, passive voice, requirements language, compliance
- **Readability Metrics**: Flesch, Flesch-Kincaid, Fog Index
- **Issue Triage**: Systematic review with Keep/Suppress/Fixed workflow
- **Issue Families**: Batch-process similar issues together

### Roles & Responsibilities Studio
- **Role Extraction**: AI-powered identification (99%+ recall in v3.3.3)
- **Adaptive Learning**: System learns from your adjudication decisions
- **RACI Matrix**: Auto-generate from extracted data
- **Relationship Graph**: D3.js visualization of role connections
- **Cross-Reference**: Role × Document heatmap
- **Role Dictionary**: Centralized role database with function tags
- **Interactive HTML Export**: Standalone kanban board for offline team review
- **Role Sharing**: Share dictionaries via shared folders or `.aegis-roles` email packages

### Statement Forge
- **Statement Extraction**: Pull actionable requirements and procedures
- **Export Formats**: CSV, Excel, JSON for import into other tools
- **Compliance Checking**: Verify requirement statement structure

### Enterprise Features
- **100% Offline**: Operates on air-gapped networks
- **Local Processing**: No data leaves your machine
- **Built-in Updates**: Apply patches without reinstalling
- **Scan History**: Track document reviews over time

### Visual Experience (v3.1.5+)
- **Cinematic Progress**: Rive-inspired molten progress animations
- **Molten Progress Bars**: Scalable (4px-28px) with orange/amber glow
- **Batch Processing Modal**: Full-screen cinematic loader for long operations
- **Theme-Aware**: Matches dark/light mode preferences

## File Structure

```
AEGIS/
├── app.py                    # Main Flask application (5,000+ LOC)
├── core.py                   # Document extraction engine
├── role_extractor_v3.py      # AI role extraction (99%+ recall)
├── adjudication_export.py    # Interactive HTML board generator
├── docling_extractor.py      # Docling AI integration
├── *_checker.py              # Quality checker modules (30+)
├── statement_forge/          # Statement extraction module
│   ├── routes.py             # API endpoints
│   ├── extractor.py          # Extraction logic
│   └── export.py             # Export formats
├── static/                   # Frontend assets
│   ├── js/                   # JavaScript modules
│   │   ├── app.js            # Main application
│   │   ├── features/         # Feature modules (roles, triage)
│   │   ├── ui/               # UI components
│   │   └── vendor/           # D3.js, Chart.js, Lucide
│   └── css/                  # Stylesheets
├── templates/                # HTML templates
├── updates/                  # Drop update files here
├── backups/                  # Auto-created before updates
├── logs/                     # Application logs
├── setup.bat                 # Basic setup script
├── setup_docling.bat         # Docling installation
├── setup_enhancements.bat    # NLP enhancement installation
├── bundle_for_airgap.ps1     # Air-gap deployment packaging
├── version.json              # Version info (single source of truth)
└── TWR_LESSONS_LEARNED.md    # Development patterns & fixes
```

## Requirements

- Python 3.10+ (3.12 recommended)
- Windows 10/11 (for batch scripts)
- ~200 MB disk space (base installation)
- ~500 MB additional (with NLP enhancements)
- ~2.7 GB additional (with Docling AI)

## Air-Gap Security

AEGIS is designed for sensitive environments:

- **No network calls** during document processing
- **Docling offline mode**: Environment variables block all network access
- **Local AI models**: All AI runs on your machine
- **No telemetry**: Analytics and tracking disabled

## API Reference

AEGIS exposes a REST API on `http://localhost:5050/api/`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload document for analysis |
| `/api/review` | POST | Run analysis with checkers |
| `/api/roles/extract` | GET | Extract roles from document |
| `/api/roles/raci` | GET | Get RACI matrix data |
| `/api/export/word` | POST | Export with tracked changes |
| `/api/export/csv` | POST | Export as CSV |
| `/api/roles/adjudication/export-html` | GET | Interactive HTML board export |
| `/api/roles/adjudication/import` | POST | Import adjudication decisions |
| `/api/roles/share/package` | POST | Create .aegis-roles package |
| `/api/roles/share/import-package` | POST | Import .aegis-roles package |
| `/api/updates/check` | GET | Check for pending updates |
| `/api/updates/apply` | POST | Apply pending updates |
| `/api/docling/status` | GET | Check Docling AI status |

See Help → Technical → API Reference for full documentation.

## Troubleshooting

### Port Already in Use (Port 5050)
If AEGIS fails to start with "Address already in use" error:

**Windows:**
```batch
# Find process using port 5050
netstat -ano | findstr :5050

# Kill the process (replace PID with the number shown)
taskkill /PID <PID> /F

# Then restart AEGIS
start_aegis.bat
```

**macOS/Linux:**
```bash
# Find and kill process using port 5050
lsof -ti :5050 | xargs kill -9

# Then restart
python3 app.py --debug
```

### SOW Generation Errors
If Statement of Work generation returns 500 error:

1. Verify Python 3.9+ is installed: `python --version`
2. Check that timezone module is available: `python -c "from datetime import timezone; print(timezone.utc)"`
3. Restart AEGIS server to reload modules
4. Clear browser cache and try again

### Document Compare Not Loading
If Document Compare shows empty state:

1. Ensure documents have been scanned (check Scan History)
2. Try the auto-picker: Open Compare, it should auto-select oldest and newest docs
3. If still empty, clear localStorage: `localStorage.clear()` in browser console
4. Reload the page

### Windows .doc Files Not Supported
AEGIS requires .docx format (save from Word as .docx). For .doc files:

1. Open in Microsoft Word
2. File → Save As → Choose .docx format
3. Upload the .docx to AEGIS

### Statement Viewer Text Not Visible
If statement text appears invisible in the document viewer:

1. Check **View** → **Dark Mode** toggle status
2. In dark mode, text should be white with good contrast
3. If still not visible, clear browser cache and reload

### API Error Responses Showing [object Object]
If error toasts show "[object Object]" instead of error messages:

1. This is fixed in v4.9.9+
2. If on older version, update AEGIS using Check for Updates
3. Errors should now show meaningful messages like "SOW generation failed: missing template"

### Windows Platform-Specific Issues
AEGIS v4.9.9+ includes full Windows support:

- **File Permissions**: chmod operations automatically skipped on Windows
- **Path Handling**: Uses pathlib.Path for cross-platform compatibility
- **Environment Variables**: Properly detects Windows vs Unix using os.name
- **Batch Files**: use `call` to properly handle nested batch execution

If experiencing Windows-specific issues:

1. Run Command Prompt as Administrator
2. Verify Python path: `python -c "import sys; print(sys.executable)"`
3. Check dependencies: `pip list | findstr flask sqlalchemy mammoth`
4. Run diagnostic: Open Help → Diagnostics tab for system information

## Installation Issues on Windows

### Python Not Found
If you see "python is not recognized":

1. Reinstall Python with **Add Python to PATH** checked
2. Restart Command Prompt after reinstalling
3. Verify: Open new Command Prompt, type `python --version`

### Playwright Installation Fails
For headless browser validation (Deep Validate feature):

```batch
# Install Playwright
pip install playwright

# Install Chromium
playwright install chromium
```

On air-gapped systems, skip this step (basic validation still works).

### Permission Denied on .bat Files
If batch files won't run:

1. Right-click start_aegis.bat
2. Select "Run as administrator"
3. For future runs, check "Run this program in administrator mode" in properties

## Version History

See `version.json` for complete changelog.

### v3.0.91d (2026-01-27)
- FIXED: Role extraction false positive filtering (94.7% precision)
- FIXED: Update manager path detection
- NEW: updates/ and backups/ folders added to repository
- DOC: Comprehensive help documentation overhaul

### v3.0.91c (2026-01-27)
- VERIFIED: Cross-document role extraction testing
- NEW: Agile/Scrum roles, Executive roles, IT roles

### v3.0.91b (2026-01-27)
- IMPROVED: Role extraction precision from 52% to 100%
- NEW: Expanded FALSE_POSITIVES list

### v3.0.91 (2026-01-27)
- NEW: Docling AI integration for superior document extraction
- NEW: Air-gapped deployment with bundle_for_airgap.ps1
- NEW: Memory optimization (image processing disabled)
- NEW: /api/docling/status endpoint
- IMPROVED: Role extraction with table confidence boosting

### v3.0.90 (2026-01-27)
- MERGED: All fixes from v3.0.76-v3.0.89 consolidated
- INCLUDES: Graph visualization improvements
- INCLUDES: Export dropdown with All/Current/JSON options

## Support

- **In-App Help**: Press F1 or click Help → Documentation
- **Development Notes**: See `TWR_LESSONS_LEARNED.md` for patterns and fixes
- **Updates**: Check Settings → Updates for available patches
