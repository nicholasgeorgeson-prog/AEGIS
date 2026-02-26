# AEGIS v6.2.9

**Aerospace Engineering Governance & Inspection System**

Enterprise-grade document analysis, compliance verification, and proposal comparison platform for aerospace, defense, and government technical documentation. Built for air-gapped classified networks with zero external dependencies at runtime.

---

## Key Capabilities

| Module | Description |
|--------|-------------|
| **Document Review** | 105+ quality checkers with severity scoring, Fix Assistant, and export suite |
| **Proposal Compare** | Multi-vendor financial analysis with multi-term comparison, red flags, and vendor scoring |
| **Hyperlink Validator** | 6,000+ URL batch validation with headless browser deep validate and Windows SSO |
| **Statement Forge** | Requirements extraction with history tracking, compare viewer, and bulk editing |
| **Roles Studio** | AI role extraction (99%+ recall), adjudication kanban, RACI matrix, D3.js graphs |
| **SharePoint Integration** | Connect & Scan with file selection, headless browser SSO, and subsite detection |
| **Metrics & Analytics** | 6-tab command center with cross-module dashboards and proposal metrics |
| **Pattern Learning** | 5-module local learning system that improves from user corrections |

---

## What's New in v6.x

### SharePoint Connect & Scan (v6.0 - v6.2)
- **One-click flow**: Paste SharePoint URL, auto-discover files, select which to scan
- **Headless browser SSO**: Playwright-powered Windows authentication for SharePoint Online GCC High
- **File selection**: Checkbox picker with extension filters after discovery
- **Subsite detection**: Automatically routes API calls to correct sub-web
- **Async progress dashboard**: Cinematic real-time progress with per-file phase tracking
- **SP link validation**: Full auth cascade for validating SharePoint URLs in documents

### Async Batch Scan with Cinematic Dashboard (v6.2)
- **Background processing**: Non-blocking batch scan with real-time polling
- **Per-file progress**: Phase indicators (Extracting, Checking, NLP, Complete) via `progress_callback`
- **ECD estimation**: Exponential Moving Average completion time prediction
- **Minimize-to-badge**: SVG progress ring badge when modal is minimized
- **Crash prevention**: Protected state updates, per-file gc.collect(), watchdog timer
- **Cancel support**: Stop scans mid-flight with graceful cleanup

### Unified Auth Service (v6.2)
- **Singleton pattern**: Shared authentication across all SharePoint and corporate modules
- **Session management**: 30-minute TTL with auto-refresh and thread-safe fresh sessions
- **Boot diagnostics**: Auth probe at startup with results in `/api/capabilities`
- **Multi-strategy cascade**: Negotiate SSO, preemptive SSPI, MSAL OAuth, headless browser

### Proposal Compare v2.0 (v5.9 - v6.0)
- **8-tab analysis**: Executive summary, comparison matrix, categories, red flags, heatmap, vendor scores, details, raw tables
- **Multi-term comparison**: Auto-detects contract terms (3-year, 5-year), groups and compares separately
- **Red flag detection**: Rate anomalies, missing data, cost outliers, FAR 15.404 compliance
- **Vendor scoring**: Letter grades A-F with weighted components (Price, Completeness, Risk, Data Quality)
- **Project management**: Named projects with proposal grouping and comparison history
- **Review phase**: Split-pane document viewer with click-to-populate and live editing
- **Pattern learning**: Learns from user corrections to improve extraction accuracy
- **Structure analyzer**: Privacy-safe diagnostic tool for parser tuning
- **Interactive HTML export**: Self-contained report with inline SVG charts and dark/light mode

### Hyperlink Validator Enhancements (v5.9 - v6.1)
- **Headless browser deep validate**: Playwright Chromium for bot-protected .mil/.gov sites
- **Multi-strategy SSL**: OS truststore integration, corporate CA bypass, fresh SSO sessions
- **Per-domain rate limiting**: Thread-safe semaphores prevent 429 errors
- **Multi-color Excel export**: Status-coded rows (green/yellow/orange/red) with summary sheet
- **Content-type mismatch detection**: Catches silent login redirects on document URLs
- **Windows SSO passthrough**: `--auth-server-allowlist` for corporate NTLM/Negotiate

### Pattern Learning System (v5.9)
- **5 modules**: Document Review, Statement Forge, Roles, Hyperlink Validator, Proposal Compare
- **Local-only**: All patterns stored on disk, never uploaded
- **Safety thresholds**: Requires 2+ observations before activating learned patterns
- **Settings UI**: View, export, clear patterns per module with global toggle

### Guided Tour & Demo System (v5.6 - v5.9)
- **79 overview scenes** across 11 sections with spotlight and narration
- **93 sub-demos** with 471 deep-dive scenes covering every feature
- **Voice narration**: Pre-generated MP3 clips (edge-tts JennyNeural) with Web Speech API fallback
- **Technology showcase**: Full-screen Canvas cinematic video (6 acts, 18 scenes)

### Export Suite (v5.9)
- **5 formats**: DOCX (with comments), PDF Report (reportlab), XLSX, CSV, JSON
- **Pre-export filtering**: Severity and category chip-based multi-select
- **Fix Assistant**: Owner mode (track changes) and Reviewer mode (recommendation comments)

---

## Previous Major Releases

### v5.x Highlights
- **Statement History**: Overview dashboard, document viewer, unified compare viewer with diff detection
- **Folder Scan**: Server-side recursive scanning with async polling and progress dashboard
- **Responsive Design**: 4 standard CSS breakpoints (1366px, 1280px, 1024px, 768px)
- **Metrics & Analytics**: 6-tab command center with quality trends, heatmaps, and proposal metrics
- **Persistent Docling worker**: 3-6x batch scan performance improvement
- **OneClick installer**: Windows air-gapped deployment with embedded Python and 195 wheels

### v4.x Highlights
- **AEGIS rebrand** from TechWriterReview at v4.0.0
- **Adjudication overhaul**: Kanban board, function tags, interactive HTML export
- **Role Inheritance Map**: 4-view interactive HTML with inline editing
- **Landing page**: Full-page dashboard with particle animation and metric tiles
- **105 quality checkers** (up from 84 in v3.x)

---

## Quick Start

### OneClick Installer (Windows, Recommended)

```
1. Download Install_AEGIS_OneClick.bat from GitHub Releases
2. Double-click to run — installs Python, dependencies, and models automatically
3. Double-click Start_AEGIS.bat
4. Browser opens to http://localhost:5050
```

Works on air-gapped networks. All dependencies bundled as wheel files.

### Manual Setup (macOS/Linux)

```bash
# Clone the repository
git clone https://github.com/nicholasgeorgeson-prog/AEGIS.git
cd AEGIS

# Install dependencies
pip install -r requirements.txt

# Install spaCy model
pip install wheels/en_core_web_sm-3.8.0-py3-none-any.whl

# Start the server
python3 app.py --debug

# Open browser to http://localhost:5050
```

### Air-Gapped Deployment

For classified networks without internet access:

1. On a connected machine: Download the OneClick installer + wheels from GitHub Releases
2. Transfer to air-gapped machine via approved media
3. Run `Install_AEGIS_OneClick.bat` — installs from local wheel files only
4. All AI models (spaCy, Docling) run locally with zero network calls

---

## Architecture

```
AEGIS/
├── app.py                          # Flask entry point, middleware, server startup
├── core.py                         # AEGISEngine — 105+ checkers, extraction pipeline
├── auth_service.py                 # Unified auth singleton (SSO, MSAL, headless)
├── review_report.py                # PDF report generator (reportlab)
├── export_module.py                # Excel/CSV/PDF/JSON exporters
├── markup_engine.py                # DOCX comment insertion (lxml)
├── update_manager.py               # Update system with rollback support
│
├── routes/                         # Flask blueprints
│   ├── review_routes.py            # Document review, batch scan, folder scan, SharePoint
│   ├── config_routes.py            # Version, capabilities, health, learning endpoints
│   ├── data_routes.py              # Roles reports, data endpoints
│   └── roles_routes.py             # Roles API
│
├── proposal_compare/               # Proposal comparison module
│   ├── parser.py                   # Financial data extraction (DOCX/PDF/XLSX)
│   ├── analyzer.py                 # Red flags, heatmap, vendor scoring
│   ├── routes.py                   # 17 API endpoints
│   ├── projects.py                 # SQLite project management
│   ├── structure_analyzer.py       # Privacy-safe parser diagnostics
│   └── pattern_learner.py          # Local learning from user corrections
│
├── hyperlink_validator/            # URL validation module
│   ├── validator.py                # Multi-strategy validation engine
│   ├── headless_validator.py       # Playwright headless browser validation
│   ├── routes.py                   # Validation API endpoints
│   └── hv_learner.py              # Domain learning system
│
├── statement_forge/                # Statement extraction module
│   ├── extractor.py                # Requirements/work instruction extraction
│   ├── routes.py                   # Statement API endpoints
│   └── statement_learner.py        # Directive/role learning
│
├── static/
│   ├── js/
│   │   ├── app.js                  # Main application (~14,000 lines)
│   │   ├── features/               # Feature modules (IIFEs)
│   │   │   ├── proposal-compare.js # Proposal Compare UI (~2,700 lines)
│   │   │   ├── metrics-analytics.js# M&A Command Center (~1,762 lines)
│   │   │   ├── guide-system.js     # Guided tour + demo system
│   │   │   ├── landing-page.js     # Dashboard with particle animation
│   │   │   ├── hyperlink-validator.js # HV frontend
│   │   │   ├── batch-results.js    # Post-scan filter & results
│   │   │   ├── pdf-viewer.js       # PDF.js HiDPI viewer with zoom
│   │   │   └── technology-showcase.js # Canvas cinematic video
│   │   └── vendor/                 # D3.js, Chart.js, PDF.js, Lucide
│   └── css/features/              # Feature-specific stylesheets
│
├── templates/index.html            # Single-page application HTML
├── version.json                    # Version info + changelog
├── scan_history.db                 # SQLite database
├── wheels/                         # 195 offline wheel files
└── Install_AEGIS_OneClick.bat      # Windows installer
```

## Technology Stack

- **Backend**: Python 3.10, Flask, SQLite, spaCy, Docling, reportlab, openpyxl
- **Frontend**: Vanilla JavaScript (no framework), CSS3, HTML5 Canvas
- **Visualization**: D3.js (graphs), Chart.js (charts), PDF.js (document viewing)
- **Authentication**: requests-negotiate-sspi, MSAL, Playwright headless SSO
- **NLP**: spaCy (en_core_web_sm), sentence-transformers, NLTK
- **Deployment**: Waitress (production), Flask dev server (debug), embedded Python (OneClick)

## Requirements

- **Python**: 3.10+ (embedded Python included in OneClick installer)
- **OS**: Windows 10/11 (primary), macOS/Linux (development)
- **Disk**: ~500 MB base, ~2.7 GB with Docling AI models
- **Browser**: Chrome/Edge (recommended), Firefox, Safari
- **Network**: Zero network access required at runtime (100% offline capable)

## Security & Compliance

- **100% offline processing** — no data leaves the machine
- **Air-gapped certified** — deployed on NGC classified networks
- **No telemetry** — zero analytics, tracking, or phone-home
- **Local AI models** — spaCy, Docling, NLTK all run locally
- **Windows SSO** — uses existing domain credentials, no password storage
- **CSRF protection** — all API mutations require CSRF tokens

## API Reference

AEGIS exposes a comprehensive REST API on `http://localhost:5050/api/`:

| Category | Key Endpoints |
|----------|--------------|
| **Document Review** | POST `/api/review`, POST `/api/review/batch-start`, GET `/api/review/batch-progress/<id>` |
| **Folder Scan** | POST `/api/review/folder-scan-start`, GET `/api/review/folder-scan-progress/<id>` |
| **SharePoint** | POST `/api/review/sharepoint-connect-and-scan`, POST `/api/review/sharepoint-scan-selected` |
| **Proposal Compare** | POST `/api/proposal-compare/upload`, POST `/api/proposal-compare/compare` |
| **Hyperlink Validator** | POST `/api/hyperlink-validator/validate`, POST `/api/hyperlink-validator/rescan` |
| **Roles** | GET `/api/roles/dictionary`, POST `/api/roles/adjudication/batch` |
| **Metrics** | GET `/api/metrics/dashboard`, GET `/api/proposal-compare/metrics` |
| **System** | GET `/api/version`, GET `/api/capabilities`, GET `/api/health` |

See in-app Help for full API documentation.

## Troubleshooting

### Port Already in Use (5050)

**Windows:** `netstat -ano | findstr :5050` then `taskkill /PID <PID> /F`

**macOS:** `lsof -ti :5050 | xargs kill -9`

### Repair Tool (Windows)
Run `Repair_AEGIS.bat` for automated diagnostics — tests all imports, fixes missing dependencies, validates configuration.

### SharePoint Connection Issues
1. Check VPN connection (required for corporate SharePoint)
2. Verify Windows SSO is working (try opening the SharePoint URL in Chrome)
3. Check `logs/sharepoint.log` for detailed auth diagnostics
4. The auth badge in HV modal header shows current SSO status

### Update Issues
1. Settings > Updates > Check for Updates
2. If Apply fails, use the standalone `apply_v6.2.9.py` script
3. For rollback: Settings > Updates > Rollback to Previous Version

---

## Version History

Current: **v6.2.9** (2026-02-26) | See `version.json` for complete changelog.

| Version | Date | Highlights |
|---------|------|-----------|
| 6.2.9 | 2026-02-26 | SharePoint scan async fix, cinematic dashboard |
| 6.2.0 | 2026-02-26 | Unified auth service, async batch scan, responsive CSS, batch results IIFE |
| 6.1.x | 2026-02-25 | Headless browser SSO, subsite detection, file selection, SP link validation |
| 6.0.x | 2026-02-24 | Fix Assistant modes, US dictionary, multi-term comparison |
| 5.9.x | 2026-02-20 | Proposal Compare v2, pattern learning, guided tours, export suite |
| 5.5-5.8 | 2026-02-18 | Folder scan, statement history, persistent Docling, responsive design |
| 5.0-5.4 | 2026-02-15 | OneClick installer, HV enhancements, SSL strategies, air-gap deployment |
| 4.0-4.9 | 2026-02-10 | AEGIS rebrand, adjudication overhaul, landing page, 105 checkers |
| 3.x | 2026-01-27 | NLP suite, 99%+ role extraction, compliance checkers |

---

**Created by Nicholas Georgeson** | Runs on localhost:5050 | 100% offline capable
