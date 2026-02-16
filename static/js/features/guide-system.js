/**
 * AEGIS Guide System v2.0.0 - Interactive Help, Guided Tours & Live Demos
 * ========================================================================
 * A comprehensive help system with:
 * - Floating pulsing "?" beacon (bottom-right)
 * - Contextual help slideout panel with real content
 * - Spotlight overlay guided tours (manual step-by-step)
 * - Cinematic auto-playing demo player (Watch Demo)
 * - Section-specific and full-app tours
 * - Settings integration (enable/disable globally)
 * - Covers every function and sub-function in AEGIS
 *
 * Version: 2.0.0
 */

'use strict';

const AEGISGuide = {
    // ─── Configuration ───────────────────────────────────────────────
    config: {
        beaconZIndex: 150000,
        spotlightZIndex: 149000,
        panelZIndex: 149500,
        demoBarZIndex: 149800,
        animationDuration: 300,
        spotlightAnimDuration: 400,
        demoStepDuration: 4500,
        demoTypeSpeed: 30,
        storageKey: 'aegis-guide-enabled',
        demoSeenKey: 'aegis-demo-seen'
    },

    // ─── State ───────────────────────────────────────────────────────
    state: {
        initialized: false,
        panelOpen: false,
        tourActive: false,
        currentTourIndex: 0,
        currentSection: null,
        currentTour: null,
        enabled: true
    },

    // ─── Demo Player State ───────────────────────────────────────────
    demo: {
        isPlaying: false,
        isPaused: false,
        currentStep: 0,
        currentSection: null,
        scenes: null,
        timer: null,
        typeTimer: null,
        speed: 1
    },

    // ─── DOM References ──────────────────────────────────────────────
    refs: {
        beacon: null,
        panel: null,
        spotlight: null,
        demoBar: null,
        panelContent: null
    },

    // ═════════════════════════════════════════════════════════════════
    // SECTION DEFINITIONS - Real content targeting actual DOM elements
    // ═════════════════════════════════════════════════════════════════

    sections: {
        // ─── Dashboard / Landing Page ────────────────────────────────
        landing: {
            id: 'landing',
            title: 'Dashboard',
            icon: 'layout-dashboard',
            whatIsThis: 'Your mission control center for document quality. The dashboard shows real-time statistics from your review database, quick-access tiles to every AEGIS feature, and recent scan activity. Drag a document onto the hero area to instantly begin a review, or click any feature tile to jump directly to that tool.',
            keyActions: [
                { icon: 'upload', text: 'Drag & drop a document onto the hero banner to start a review instantly' },
                { icon: 'layout-grid', text: 'Click any feature tile to jump to Document Review, Roles Studio, Statement Forge, etc.' },
                { icon: 'bar-chart-2', text: 'View real-time metrics: total documents scanned, average quality score, roles discovered' },
                { icon: 'clock', text: 'See recent scans and quickly re-open previous review results' },
                { icon: 'compass', text: 'Click "Getting Started" for a full guided tour of every feature' }
            ],
            proTips: [
                'The quality metrics update automatically each time you scan a document',
                'Each feature tile shows a live count pulled from your database',
                'Use keyboard shortcut Ctrl+O to quickly open a document from anywhere',
                'The Getting Started card launches a comprehensive walkthrough of all features',
                'You can return to the Dashboard at any time by clicking the AEGIS logo or pressing Escape'
            ],
            tourSteps: [
                {
                    target: '#lp-hero',
                    title: 'Document Drop Zone',
                    description: 'This is the fastest way to start a review. Drag any .docx, .doc, or .pdf file here and AEGIS will immediately begin scanning it against 100+ quality checkers. You can also click the "Open Document" button in the toolbar.',
                    position: 'bottom'
                },
                {
                    target: '#lp-metrics',
                    title: 'Live Dashboard Metrics',
                    description: 'These cards show real-time statistics from your review database: total documents scanned, average quality score, total roles discovered, and recent scan activity. Numbers update automatically after each review.',
                    position: 'bottom'
                },
                {
                    target: '#lp-tiles',
                    title: 'Feature Quick-Access Tiles',
                    description: 'Each tile represents a major AEGIS capability. Click to jump directly to Document Review, Roles Studio, Statement Forge, Hyperlink Validator, Metrics & Analytics, Scan History, Document Compare, or Portfolio view.',
                    position: 'top'
                },
                {
                    target: '#lp-getting-started',
                    title: 'Getting Started Guide',
                    description: 'Click this card to launch a comprehensive guided tour that walks you through every feature in AEGIS. Perfect for new users or when you want to discover capabilities you might have missed.',
                    position: 'top'
                }
            ],
            demoScenes: [
                {
                    target: '#aegis-landing-page',
                    narration: 'Welcome to AEGIS — your Aerospace Engineering Governance & Inspection System. This dashboard is your command center for document quality analysis.',
                    duration: 5000
                },
                {
                    target: '#lp-hero',
                    narration: 'Start by dragging a document here. AEGIS supports Word documents (.docx, .doc) and PDF files. The review begins automatically as soon as you drop a file.',
                    duration: 5500
                },
                {
                    target: '#lp-metrics',
                    narration: 'Your live metrics show the health of your document portfolio. Track total scans, average quality scores, and role discovery across all reviewed documents.',
                    duration: 5000
                },
                {
                    target: '#lp-tiles',
                    narration: 'Each tile links to a major feature. Let\'s explore them all — starting with Document Review, the core of AEGIS.',
                    duration: 4500
                }
            ]
        },

        // ─── Document Review ─────────────────────────────────────────
        review: {
            id: 'review',
            title: 'Document Review',
            icon: 'file-check',
            whatIsThis: 'The heart of AEGIS. Upload any technical document and run it through 100+ automated quality checkers covering grammar, clarity, consistency, aerospace-specific requirements (MIL-STD, DO-178C), role extraction, and more. Results are organized by severity with actionable fix suggestions. Export detailed reports in multiple formats.',
            keyActions: [
                { icon: 'file-plus', text: 'Click "Open" or drag-drop to load a document for review' },
                { icon: 'sliders-horizontal', text: 'Expand "Advanced Settings" in sidebar to toggle individual checkers on/off' },
                { icon: 'play', text: 'Click "Review" to run all enabled checkers against the loaded document' },
                { icon: 'filter', text: 'Use the filter bar to sort results by severity, category, or search text' },
                { icon: 'download', text: 'Click "Export" to save results as HTML report, CSV, or annotated DOCX' },
                { icon: 'target', text: 'Click any issue row to see full details, context, and suggested fixes' }
            ],
            proTips: [
                'The sidebar "Advanced Settings" panel lets you enable/disable any of the 100+ checkers individually',
                'Results are color-coded: Critical (red), High (orange), Medium (yellow), Low (blue), Info (gray)',
                'Click the quality score badge to see a detailed breakdown of how the grade was calculated',
                'Use Triage Mode to quickly accept/reject issues one-by-one with keyboard shortcuts',
                'The filter bar supports text search — type a keyword to find specific issues instantly',
                'Batch upload lets you scan multiple documents at once with progress tracking'
            ],
            tourSteps: [
                {
                    target: '#btn-open',
                    title: 'Open Document',
                    description: 'Click to browse for a document, or use Ctrl+O. AEGIS supports .docx, .doc, and .pdf files up to 100MB. The document loads into memory for analysis.',
                    position: 'bottom'
                },
                {
                    target: '#btn-batch-load',
                    title: 'Batch Upload',
                    description: 'Scan multiple documents at once. Select individual files, an entire folder, or enter a server folder path for recursive scanning of document repositories with hundreds of files.',
                    position: 'bottom'
                },
                {
                    target: '#btn-review',
                    title: 'Run Review',
                    description: 'Starts the quality analysis. AEGIS runs all enabled checkers against your document. Progress shows in real-time with an ETA. Average scan takes 5-30 seconds depending on document length.',
                    position: 'bottom'
                },
                {
                    target: '#btn-toggle-advanced',
                    title: 'Checker Configuration',
                    description: 'Expand this panel to see all 100+ quality checkers organized by category: Writing Quality, Grammar, Technical Writing, Clarity, Document Structure, Standards Compliance, Advanced NLP, and spaCy Deep Analysis.',
                    position: 'right'
                },
                {
                    target: '#unified-filter-bar',
                    title: 'Results Filter Bar',
                    description: 'Filter issues by severity level (Critical through Info), category, or free-text search. The severity pills show counts — click to toggle visibility of that severity level.',
                    position: 'bottom'
                },
                {
                    target: '#stats-bar',
                    title: 'Document Statistics',
                    description: 'Key metrics at a glance: word count, paragraph count, headings, tables, total issues found, Flesch-Kincaid readability score, and the overall quality grade (A+ through F).',
                    position: 'bottom'
                },
                {
                    target: '#btn-export',
                    title: 'Export Results',
                    description: 'Save your review in multiple formats: interactive HTML report (best for sharing), CSV (for spreadsheet analysis), or annotated DOCX (issues embedded as Word comments).',
                    position: 'bottom'
                }
            ],
            demoScenes: [
                {
                    target: '#btn-open',
                    narration: 'Start every review by clicking Open to load a document. AEGIS accepts Word documents and PDFs. You can also drag files directly onto the page.',
                    duration: 5000
                },
                {
                    target: '#btn-toggle-advanced',
                    narration: 'Before scanning, configure which checkers to run. The Advanced Settings panel shows all 100+ checkers organized by category. Toggle any checker on or off.',
                    duration: 5500
                },
                {
                    target: '#btn-review',
                    narration: 'Click Review to start the analysis. AEGIS processes your document through every enabled checker — grammar, clarity, requirements language, aerospace standards, and more.',
                    duration: 5000
                },
                {
                    target: '#unified-filter-bar',
                    narration: 'Results appear organized by severity. Use these filter pills to show or hide specific severity levels. The search bar lets you find specific issues by keyword.',
                    duration: 5000
                },
                {
                    target: '#stats-bar',
                    narration: 'The stats bar shows your document metrics: word count, readability scores, and the overall quality grade. Click the grade badge for a detailed score breakdown.',
                    duration: 5000
                },
                {
                    target: '#btn-export',
                    narration: 'When you\'re satisfied with the review, export results as an HTML report, CSV spreadsheet, or annotated Word document with issues embedded as comments.',
                    duration: 5000
                }
            ]
        },

        // ─── Batch Upload ────────────────────────────────────────────
        batch: {
            id: 'batch',
            title: 'Batch Scan',
            icon: 'folders',
            whatIsThis: 'Scan entire document repositories at once. Select multiple files, choose a folder, or enter a server path for recursive scanning. AEGIS processes documents in parallel with real-time progress tracking, then presents aggregate results with per-document breakdowns.',
            keyActions: [
                { icon: 'files', text: 'Select multiple files to scan them all in one batch' },
                { icon: 'folder', text: 'Choose a folder to scan all supported documents inside it' },
                { icon: 'hard-drive', text: 'Enter a server folder path for recursive scanning of large repositories' },
                { icon: 'eye', text: 'Use Preview to see what files will be scanned before committing' },
                { icon: 'activity', text: 'Monitor real-time progress with per-document status updates' }
            ],
            proTips: [
                'Folder scan traverses up to 10 levels of subdirectories automatically',
                'Files larger than 100MB are automatically skipped to prevent memory issues',
                'The Preview button shows you exactly what will be scanned before you commit',
                'AEGIS processes 3 documents simultaneously for faster batch completion',
                'If one document fails, the rest of the batch continues — no single-file failures stop the process',
                'Results show aggregate statistics plus individual document grades'
            ],
            tourSteps: [
                {
                    target: '#btn-batch-load',
                    title: 'Open Batch Upload',
                    description: 'Click to open the batch upload modal where you can select files, folders, or enter a server path for scanning.',
                    position: 'bottom'
                }
            ],
            demoScenes: [
                {
                    target: '#btn-batch-load',
                    narration: 'For large document repositories, use Batch Scan. Click the Batch button to open the batch upload interface.',
                    duration: 4500
                },
                {
                    target: '#btn-batch-load',
                    narration: 'You can select individual files, choose an entire folder, or enter a server path. AEGIS scans up to 500 documents across nested subdirectories with parallel processing.',
                    duration: 5500
                }
            ]
        },

        // ─── Roles Studio ────────────────────────────────────────────
        roles: {
            id: 'roles',
            title: 'Roles Studio',
            icon: 'users-round',
            whatIsThis: 'A comprehensive role analysis workbench. AEGIS extracts organizational roles from your documents and builds a complete picture: who is Responsible, Accountable, Consulted, and Informed (RACI) for each function. Explore role relationships through interactive graphs, adjudicate unclear roles, and build a verified role dictionary.',
            keyActions: [
                { icon: 'list', text: 'Overview tab: See all roles with mention counts and responsibility summaries' },
                { icon: 'git-branch', text: 'Graph tab: Visualize role relationships as an interactive network diagram' },
                { icon: 'table-2', text: 'RACI Matrix tab: See Responsible/Accountable/Consulted/Informed assignments' },
                { icon: 'check-square', text: 'Adjudication tab: Verify, merge, or split role definitions' },
                { icon: 'book-open', text: 'Dictionary tab: Build a curated role dictionary with descriptions' },
                { icon: 'file-text', text: 'Documents tab: See which documents reference each role' }
            ],
            proTips: [
                'The Overview shows aggregate statistics — click any role name to see full details',
                'In the Graph view, zoom with scroll wheel and drag nodes to rearrange the layout',
                'RACI Matrix cells are clickable — see the exact statements that generated each assignment',
                'Function Tags color-code roles by department (Engineering, Administration, Quality, etc.)',
                'Export the RACI matrix as CSV filtered by function category',
                'The Role-Document Matrix shows at a glance which roles appear in which documents',
                'Use Adjudication to resolve duplicate or ambiguous role names discovered during scanning'
            ],
            tourSteps: [
                {
                    target: '#tab-overview',
                    title: 'Overview Tab',
                    description: 'Shows all discovered roles ranked by mention frequency. Each role displays its document count, total mentions, and responsibility summary. Function tag colors indicate department assignments.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-graph',
                    title: 'Relationship Graph',
                    description: 'An interactive force-directed graph showing how roles relate to each other through shared documents and responsibilities. Drag nodes, zoom in/out, click a node to inspect.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-matrix',
                    title: 'RACI Matrix',
                    description: 'The Responsible-Accountable-Consulted-Informed matrix. Rows are roles, columns are function areas. Click any cell number to see the exact statements and action verbs that generated the assignment.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-roledocmatrix',
                    title: 'Role-Document Matrix',
                    description: 'Cross-reference showing which roles appear in which documents. Useful for identifying roles that span multiple documents versus those confined to a single spec.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-adjudication',
                    title: 'Role Adjudication',
                    description: 'Review and verify automatically discovered roles. Merge duplicates (e.g., "QA Engineer" and "Quality Assurance Engineer"), split combined roles, or mark roles as verified for your dictionary.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-dictionary',
                    title: 'Role Dictionary',
                    description: 'Your curated catalog of verified roles with descriptions, department assignments, and responsibility summaries. Export as a reference document for your organization.',
                    position: 'bottom',
                    navigate: 'roles'
                },
                {
                    target: '#tab-documents',
                    title: 'Documents Tab',
                    description: 'Lists all scanned documents with their role counts. Click any document to see which roles were found in it and how many times each appears.',
                    position: 'bottom',
                    navigate: 'roles'
                }
            ],
            demoScenes: [
                {
                    target: '#tab-overview',
                    narration: 'Roles Studio automatically extracts organizational roles from your documents. The Overview tab shows every role discovered, ranked by frequency.',
                    duration: 5000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-graph',
                    narration: 'The Graph tab visualizes role relationships as an interactive network. Connected roles share documents or responsibilities. Drag nodes to rearrange.',
                    duration: 5000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-matrix',
                    narration: 'The RACI Matrix shows who is Responsible, Accountable, Consulted, and Informed for each function. Click any cell to see the exact statements behind each assignment.',
                    duration: 5500,
                    navigate: 'roles'
                },
                {
                    target: '#tab-adjudication',
                    narration: 'Adjudication lets you verify, merge, or split roles. Clean up duplicates and build a verified role dictionary for your organization.',
                    duration: 5000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-dictionary',
                    narration: 'The Dictionary tab is your curated role catalog. Each verified role has descriptions, department tags, and responsibility summaries you can export.',
                    duration: 5000,
                    navigate: 'roles'
                }
            ]
        },

        // ─── Statement Forge ─────────────────────────────────────────
        forge: {
            id: 'forge',
            title: 'Statement Forge',
            icon: 'hammer',
            whatIsThis: 'Extract, search, and manage requirement statements across all your documents. Statement Forge identifies shall/must/should/will statements, categorizes them by type, and lets you edit, tag, reorder, and export them. Perfect for building requirements traceability matrices and compliance documentation.',
            keyActions: [
                { icon: 'scissors', text: 'Extract: Pull all requirement statements from the loaded document' },
                { icon: 'search', text: 'Search: Find statements by keyword across all extractions' },
                { icon: 'filter', text: 'Filter: Show only shall, must, should, may, will, or process statements' },
                { icon: 'edit', text: 'Edit: Modify statement text, add notes, or change classification' },
                { icon: 'undo', text: 'Undo/Redo: Full history with Ctrl+Z and Ctrl+Y' },
                { icon: 'download', text: 'Export: Save as CSV, DOCX, or JSON for traceability tools' }
            ],
            proTips: [
                'Filter chips at the top let you quickly show only "shall" or "must" statements',
                'The document type selector (Procedures vs Work Instructions) adjusts extraction rules',
                'Click any statement to expand it and see source context, section heading, and paragraph number',
                'Use Ctrl+Z / Ctrl+Y for undo/redo — the counters show available undo/redo actions',
                'Expand All / Collapse All buttons help manage large statement sets',
                'Statistics cards at the top show total, filtered, sections, and selected counts'
            ],
            tourSteps: [
                {
                    target: '#btn-sf-extract',
                    title: 'Extract Statements',
                    description: 'Parses the loaded document and extracts all requirement-type statements (shall, must, should, will, may). Results are organized by section with source tracking.',
                    position: 'bottom',
                    navigate: 'forge'
                },
                {
                    target: '#sf-search-input',
                    title: 'Search Statements',
                    description: 'Type any keyword to instantly filter statements. Search works across statement text, section headings, and notes. Results update as you type.',
                    position: 'bottom',
                    navigate: 'forge'
                },
                {
                    target: '#sf-btn-export',
                    title: 'Export Statements',
                    description: 'Export your extracted statements in multiple formats: CSV for spreadsheet analysis, DOCX for formal documentation, or JSON for integration with requirements management tools.',
                    position: 'bottom',
                    navigate: 'forge'
                }
            ],
            demoScenes: [
                {
                    target: '#btn-statement-forge',
                    narration: 'Statement Forge extracts requirement statements from your documents. Open it from the sidebar to begin working with shall, must, should, and will statements.',
                    duration: 5000
                },
                {
                    target: '#btn-sf-extract',
                    narration: 'Click Extract to pull all requirement statements from your loaded document. AEGIS identifies statement types and organizes them by section.',
                    duration: 5000,
                    navigate: 'forge'
                },
                {
                    target: '#sf-search-input',
                    narration: 'Use the search bar to find specific statements across your entire extraction. Filter chips let you show only "shall" or "must" type statements.',
                    duration: 5000,
                    navigate: 'forge'
                },
                {
                    target: '#sf-btn-export',
                    narration: 'Export your statements as CSV, DOCX, or JSON. Perfect for building requirements traceability matrices and compliance documentation.',
                    duration: 4500,
                    navigate: 'forge'
                }
            ]
        },

        // ─── Hyperlink Validator ─────────────────────────────────────
        validator: {
            id: 'validator',
            title: 'Hyperlink Validator',
            icon: 'link-2',
            whatIsThis: 'Validate hyperlinks in your documents for accessibility and correctness. Upload a document to extract and check all embedded URLs, or paste URLs manually. Supports SSL verification, redirect following, Windows SSO authentication, and configurable timeouts. Results show status, response time, and issue details.',
            keyActions: [
                { icon: 'upload', text: 'Upload a document to extract and validate all embedded links' },
                { icon: 'clipboard', text: 'Paste URLs directly — one per line — for quick validation' },
                { icon: 'settings', text: 'Configure timeout, retries, SSL verification, and exclusion rules' },
                { icon: 'play', text: 'Click Validate to check all URLs with real-time progress' },
                { icon: 'bar-chart', text: 'View results grouped by status: working, broken, redirect, timeout, blocked' }
            ],
            proTips: [
                'Two scan modes: Quick (HTTP HEAD only) and Thorough (full page download + content check)',
                'Add exclusion rules for known-good internal URLs that don\'t need checking',
                'Windows SSO mode helps validate intranet links that require corporate authentication',
                'The results table is sortable — click column headers to sort by status, URL, or response time',
                'Failed links show the specific HTTP error code and reason for the failure',
                'Link History (sidebar) tracks all previously validated URLs across sessions'
            ],
            tourSteps: [
                {
                    target: '#hv-mode',
                    title: 'Validation Mode',
                    description: 'Choose between Offline mode (extract links only, no HTTP requests) and Validator mode (actively check each URL for availability and correctness).',
                    position: 'bottom',
                    navigate: 'validator'
                },
                {
                    target: '#hv-scan-depth',
                    title: 'Scan Depth',
                    description: 'Quick: HTTP HEAD request only (fast). Standard: GET with redirect following. Thorough: Full page download with content verification.',
                    position: 'bottom',
                    navigate: 'validator'
                },
                {
                    target: '#hv-btn-validate',
                    title: 'Start Validation',
                    description: 'Click to begin checking all URLs. Progress updates in real-time showing working, broken, redirect, timeout, and blocked counts.',
                    position: 'bottom',
                    navigate: 'validator'
                }
            ],
            demoScenes: [
                {
                    target: '#nav-hyperlink-validator',
                    narration: 'The Hyperlink Validator checks all URLs in your documents. Upload a document or paste URLs directly.',
                    duration: 4500
                },
                {
                    target: '#hv-mode',
                    narration: 'Choose your validation mode. Offline extracts links without checking them. Validator mode actively tests each URL for availability.',
                    duration: 5000,
                    navigate: 'validator'
                },
                {
                    target: '#hv-btn-validate',
                    narration: 'Click Validate to start checking URLs. Results update in real-time showing working, broken, redirect, timeout, and authentication-required links.',
                    duration: 5000,
                    navigate: 'validator'
                }
            ]
        },

        // ─── Document Compare ────────────────────────────────────────
        compare: {
            id: 'compare',
            title: 'Document Compare',
            icon: 'git-compare',
            whatIsThis: 'Compare two documents side-by-side to identify differences in content, structure, and quality. AEGIS auto-selects the oldest and newest documents for version comparison. See added, removed, and modified content highlighted in real-time.',
            keyActions: [
                { icon: 'file-text', text: 'Select two documents from your scanned library to compare' },
                { icon: 'columns', text: 'View side-by-side comparison with color-coded differences' },
                { icon: 'diff', text: 'See added (green), removed (red), and modified (yellow) content' },
                { icon: 'download', text: 'Export the comparison report for documentation' }
            ],
            proTips: [
                'AEGIS auto-selects the oldest document on the left and newest on the right',
                'The comparison runs automatically when you open Document Compare — no manual button needed',
                'Color coding: green = added content, red = removed content, yellow = modified text',
                'Great for tracking changes between document versions or comparing similar specs'
            ],
            tourSteps: [
                {
                    target: '#nav-compare',
                    title: 'Open Document Compare',
                    description: 'Click to open the comparison view. AEGIS automatically selects your oldest and newest documents and begins comparison immediately.',
                    position: 'right'
                }
            ],
            demoScenes: [
                {
                    target: '#nav-compare',
                    narration: 'Document Compare lets you see differences between two documents side-by-side. AEGIS auto-selects the oldest and newest for version tracking.',
                    duration: 5000
                }
            ]
        },

        // ─── Metrics & Analytics ─────────────────────────────────────
        metrics: {
            id: 'metrics',
            title: 'Metrics & Analytics',
            icon: 'bar-chart-3',
            whatIsThis: 'Comprehensive analytics dashboard for your document portfolio. Track quality trends, issue severity distribution, category breakdown, role statistics, and acronym usage. Charts update automatically as you review more documents.',
            keyActions: [
                { icon: 'trending-up', text: 'View quality score trends across all scanned documents' },
                { icon: 'pie-chart', text: 'See issue distribution by severity level and category' },
                { icon: 'users', text: 'Track role discovery and distribution statistics' },
                { icon: 'book-a', text: 'Monitor acronym usage: defined vs. undefined vs. suppressed' },
                { icon: 'download', text: 'Export analytics data and charts' }
            ],
            proTips: [
                'Charts are interactive — hover over bars/slices to see exact values',
                'The severity chart helps identify which quality areas need the most attention',
                'Category distribution shows which checker types find the most issues',
                'Acronym metrics highlight where definitions are missing or inconsistent',
                'Score trends help you track improvement as you iteratively review and fix documents'
            ],
            tourSteps: [
                {
                    target: '#ma-tab-btn-overview',
                    title: 'Analytics Overview',
                    description: 'High-level metrics showing total documents, average quality score, issue counts by severity, and score trends over time.',
                    position: 'bottom',
                    navigate: 'metrics'
                },
                {
                    target: '#severity-chart-card',
                    title: 'Severity Distribution Chart',
                    description: 'Bar chart showing how issues are distributed across Critical, High, Medium, Low, and Info severity levels. Helps you focus on the most impactful problems.',
                    position: 'bottom',
                    navigate: 'metrics'
                },
                {
                    target: '#category-chart-card',
                    title: 'Category Distribution',
                    description: 'Shows which checker categories (Grammar, Clarity, Technical Writing, etc.) find the most issues. Identifies systemic quality patterns.',
                    position: 'bottom',
                    navigate: 'metrics'
                }
            ],
            demoScenes: [
                {
                    target: '#nav-metrics',
                    narration: 'Metrics & Analytics provides a comprehensive view of your document quality portfolio. Charts update automatically after each scan.',
                    duration: 5000
                },
                {
                    target: '#ma-tab-btn-overview',
                    narration: 'The Overview shows aggregate metrics: total documents scanned, average scores, severity breakdown, and quality trends over time.',
                    duration: 5000,
                    navigate: 'metrics'
                },
                {
                    target: '#severity-chart-card',
                    narration: 'The severity chart shows where your issues concentrate. Focus on Critical and High severity issues first for the biggest quality improvements.',
                    duration: 5000,
                    navigate: 'metrics'
                }
            ]
        },

        // ─── Scan History ────────────────────────────────────────────
        history: {
            id: 'history',
            title: 'Scan History',
            icon: 'history',
            whatIsThis: 'A complete audit trail of every document scan. See when each document was reviewed, what grade it received, how many issues were found, and track improvement over multiple scans. Reopen any previous review results instantly.',
            keyActions: [
                { icon: 'list', text: 'View chronological list of all previous scans' },
                { icon: 'eye', text: 'Click any scan to reopen its full review results' },
                { icon: 'trending-up', text: 'Track document quality improvement across multiple scans' },
                { icon: 'trash-2', text: 'Clear old scan records from the database' }
            ],
            proTips: [
                'Documents scanned multiple times show quality progression — watch grades improve',
                'The scan count column shows how many times each document has been reviewed',
                'Click any row to instantly reload that review\'s full results',
                'Use Data Management in Settings to selectively clear history'
            ],
            tourSteps: [
                {
                    target: '#nav-history',
                    title: 'Open Scan History',
                    description: 'View your complete scan history with dates, grades, and issue counts. Click any entry to reload its full review results.',
                    position: 'right'
                }
            ],
            demoScenes: [
                {
                    target: '#nav-history',
                    narration: 'Scan History keeps a complete audit trail of every review. Track quality improvements across multiple scans of the same document.',
                    duration: 5000
                }
            ]
        },

        // ─── Settings ────────────────────────────────────────────────
        settings: {
            id: 'settings',
            title: 'Settings',
            icon: 'settings',
            whatIsThis: 'Configure every aspect of AEGIS: reviewer name, default checker selections, review thresholds, document profiles, display preferences, data management, and troubleshooting. Changes are saved automatically and persist between sessions.',
            keyActions: [
                { icon: 'user', text: 'General: Set reviewer name, auto-review behavior, diagnostic email' },
                { icon: 'sliders-horizontal', text: 'Review Options: Configure sentence length, passive voice, and role extraction thresholds' },
                { icon: 'file-cog', text: 'Document Profiles: Create checker presets for different document types (PrOP, PAL, FGOST, SOW)' },
                { icon: 'monitor', text: 'Display: Toggle essentials mode, page size, compact layout' },
                { icon: 'database', text: 'Data Management: Clear scan history, statements, roles, or factory reset' },
                { icon: 'wrench', text: 'Troubleshooting: Export diagnostics, run health checks' }
            ],
            proTips: [
                'Document Profiles let you pre-configure which checkers run for specific document types',
                'Enable "Remember checker selections" to persist your checker toggles between sessions',
                'Essentials Mode hides advanced UI elements for a cleaner experience',
                'The troubleshooting tab exports a full diagnostic package if you need support',
                'Factory Reset in Data Management clears everything — use with caution',
                'Backup your data regularly using the export function in Data Management'
            ],
            tourSteps: [
                {
                    target: '#btn-settings',
                    title: 'Open Settings',
                    description: 'Access all AEGIS configuration options. Settings are organized into tabs: General, Review Options, Document Profiles, Sharing, Display, Updates, Troubleshooting, and Data Management.',
                    position: 'right'
                }
            ],
            demoScenes: [
                {
                    target: '#btn-settings',
                    narration: 'Settings lets you customize every aspect of AEGIS. Configure checkers, set thresholds, manage document profiles, and control data retention.',
                    duration: 5000
                },
                {
                    target: '#btn-settings',
                    narration: 'Document Profiles are especially powerful — create preset checker configurations for different document types like procedures, specifications, or SOWs.',
                    duration: 5000
                }
            ]
        },

        // ─── Portfolio ───────────────────────────────────────────────
        portfolio: {
            id: 'portfolio',
            title: 'Portfolio',
            icon: 'briefcase',
            whatIsThis: 'View your entire document collection as a portfolio. See aggregate quality metrics, document types, review status, and coverage gaps. Great for program-level quality oversight.',
            keyActions: [
                { icon: 'layout-grid', text: 'View all documents as cards with quality grades and status' },
                { icon: 'bar-chart', text: 'See portfolio-level quality metrics and trends' },
                { icon: 'search', text: 'Search and filter documents by name, type, or grade' }
            ],
            proTips: [
                'Portfolio view gives you a bird\'s eye view of your entire document collection',
                'Sort by grade to quickly find documents that need the most attention',
                'Use this view for program reviews and quality gate assessments'
            ],
            tourSteps: [
                {
                    target: '#nav-portfolio',
                    title: 'Open Portfolio',
                    description: 'See all your scanned documents as a portfolio with grades, metrics, and review status at a glance.',
                    position: 'right'
                }
            ],
            demoScenes: [
                {
                    target: '#nav-portfolio',
                    narration: 'Portfolio view shows your entire document collection with quality grades and review status. Perfect for program-level quality oversight.',
                    duration: 5000
                }
            ]
        }
    },

    // ═════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═════════════════════════════════════════════════════════════════

    init() {
        if (this.state.initialized) return;

        // Check if guide is enabled in settings
        this.state.enabled = this.isEnabled();

        console.log('[AEGIS Guide] Initializing v2.0.0...', this.state.enabled ? 'ENABLED' : 'DISABLED');

        // Create DOM elements
        this.createBeacon();
        this.createPanel();
        this.createSpotlight();
        this.createDemoBar();

        // Attach event listeners
        this.attachEventListeners();

        // Apply enabled state
        if (!this.state.enabled) {
            this.refs.beacon.style.display = 'none';
        }

        this.state.initialized = true;
        console.log('[AEGIS Guide] Initialization complete');
    },

    // ═════════════════════════════════════════════════════════════════
    // SETTINGS INTEGRATION
    // ═════════════════════════════════════════════════════════════════

    isEnabled() {
        return localStorage.getItem(this.config.storageKey) !== 'false';
    },

    enable() {
        localStorage.setItem(this.config.storageKey, 'true');
        this.state.enabled = true;
        if (this.refs.beacon) {
            this.refs.beacon.style.display = '';
        }
        console.log('[AEGIS Guide] Enabled');
    },

    disable() {
        localStorage.setItem(this.config.storageKey, 'false');
        this.state.enabled = false;
        this.closePanel();
        this.endTour();
        this.stopDemo();
        if (this.refs.beacon) {
            this.refs.beacon.style.display = 'none';
        }
        console.log('[AEGIS Guide] Disabled');
    },

    toggle() {
        if (this.state.enabled) {
            this.disable();
        } else {
            this.enable();
        }
        return this.state.enabled;
    },

    // ═════════════════════════════════════════════════════════════════
    // DOM CREATION
    // ═════════════════════════════════════════════════════════════════

    createBeacon() {
        const beacon = document.createElement('button');
        beacon.id = 'aegis-guide-beacon';
        beacon.className = 'aegis-guide-beacon';
        beacon.setAttribute('aria-label', 'Open help and guided tour');
        beacon.setAttribute('title', 'Need help? Click for guided tour');
        beacon.innerHTML = `
            <span class="beacon-icon">?</span>
            <span class="beacon-pulse"></span>
        `;
        document.body.appendChild(beacon);
        this.refs.beacon = beacon;
    },

    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'aegis-guide-panel';
        panel.className = 'aegis-guide-panel hidden';

        panel.innerHTML = `
            <div class="panel-header">
                <h2 class="panel-title" id="guide-panel-title">Help</h2>
                <button class="panel-close-btn" aria-label="Close help panel">
                    <svg class="close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>

            <div class="panel-body">
                <div class="panel-section what-is-this">
                    <p class="what-is-text" id="guide-panel-what-is-this"></p>
                </div>

                <div class="panel-section key-actions">
                    <h3 class="section-title">Key Actions</h3>
                    <ul class="actions-list" id="guide-panel-actions"></ul>
                </div>

                <div class="panel-section pro-tips">
                    <button class="tips-toggle" id="guide-tips-toggle">
                        <span class="toggle-icon">&#9660;</span>
                        <span>Pro Tips</span>
                    </button>
                    <ul class="tips-list hidden" id="guide-panel-tips"></ul>
                </div>
            </div>

            <div class="panel-footer">
                <button class="panel-btn demo-btn" id="guide-demo-btn">
                    <span class="btn-icon">&#9654;</span>
                    <span>Watch Demo</span>
                </button>
                <button class="panel-btn tour-btn" id="guide-tour-btn">
                    <span class="btn-icon">&#128204;</span>
                    <span>Take Tour</span>
                </button>
            </div>

            <div class="panel-section-nav">
                <h4 class="nav-title">All Sections</h4>
                <div class="section-nav-grid" id="guide-section-nav"></div>
            </div>
        `;

        document.body.appendChild(panel);
        this.refs.panel = panel;
        this.refs.panelContent = panel;

        // Build section nav
        this._buildSectionNav();
    },

    _buildSectionNav() {
        const nav = this.refs.panel.querySelector('#guide-section-nav');
        if (!nav) return;

        const sectionOrder = ['landing', 'review', 'batch', 'roles', 'forge', 'validator', 'compare', 'metrics', 'history', 'settings', 'portfolio'];
        nav.innerHTML = sectionOrder.map(id => {
            const s = this.sections[id];
            if (!s) return '';
            return `<button class="section-nav-btn" data-section="${id}" title="${s.title}">
                <span class="section-nav-icon" data-lucide="${s.icon}"></span>
                <span class="section-nav-label">${s.title}</span>
            </button>`;
        }).join('');
    },

    createSpotlight() {
        const spotlight = document.createElement('div');
        spotlight.id = 'aegis-guide-spotlight';
        spotlight.className = 'aegis-guide-spotlight hidden';

        spotlight.innerHTML = `
            <div class="spotlight-overlay"></div>
            <div class="spotlight-tooltip">
                <div class="tooltip-header">
                    <span class="step-counter" id="guide-step-counter">Step 1 of 1</span>
                    <button class="tooltip-close" aria-label="Close tour">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="tooltip-body">
                    <h3 class="tooltip-title" id="guide-tooltip-title"></h3>
                    <p class="tooltip-description" id="guide-tooltip-description"></p>
                </div>
                <div class="tooltip-controls">
                    <button class="control-btn skip-btn" id="guide-skip-btn">Skip</button>
                    <div class="dot-progress" id="guide-dot-progress"></div>
                    <div class="nav-buttons">
                        <button class="control-btn prev-btn" id="guide-prev-btn">&larr; Back</button>
                        <button class="control-btn next-btn" id="guide-next-btn">Next &rarr;</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(spotlight);
        this.refs.spotlight = spotlight;
    },

    createDemoBar() {
        const bar = document.createElement('div');
        bar.id = 'aegis-demo-bar';
        bar.className = 'aegis-demo-bar hidden';

        bar.innerHTML = `
            <div class="demo-bar-inner">
                <div class="demo-bar-header">
                    <span class="demo-bar-badge">LIVE DEMO</span>
                    <span class="demo-bar-section" id="demo-bar-section">Dashboard</span>
                </div>
                <div class="demo-bar-narration" id="demo-bar-narration"></div>
                <div class="demo-bar-controls">
                    <button class="demo-ctrl-btn" id="demo-prev" title="Previous">&laquo;</button>
                    <button class="demo-ctrl-btn demo-play-btn" id="demo-play" title="Pause">&#10074;&#10074;</button>
                    <button class="demo-ctrl-btn" id="demo-next" title="Next">&raquo;</button>
                    <div class="demo-progress-track">
                        <div class="demo-progress-fill" id="demo-progress-fill"></div>
                    </div>
                    <span class="demo-step-label" id="demo-step-label">1 / 1</span>
                    <select class="demo-speed-select" id="demo-speed" title="Playback speed">
                        <option value="0.5">0.5x</option>
                        <option value="1" selected>1x</option>
                        <option value="1.5">1.5x</option>
                        <option value="2">2x</option>
                    </select>
                    <button class="demo-ctrl-btn demo-stop-btn" id="demo-stop" title="Stop demo">&times;</button>
                </div>
            </div>
        `;

        document.body.appendChild(bar);
        this.refs.demoBar = bar;
    },

    // ═════════════════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ═════════════════════════════════════════════════════════════════

    attachEventListeners() {
        // Beacon click
        this.refs.beacon.addEventListener('click', (e) => {
            e.stopPropagation();
            this.togglePanel();
        });

        // Panel close
        this.refs.panel.querySelector('.panel-close-btn').addEventListener('click', () => this.closePanel());

        // Tips toggle
        this.refs.panel.querySelector('#guide-tips-toggle').addEventListener('click', () => this.toggleTips());

        // Demo button
        this.refs.panel.querySelector('#guide-demo-btn').addEventListener('click', () => {
            const section = this.state.currentSection || this.detectCurrentSection();
            this.closePanel();
            this.startDemo(section);
        });

        // Tour button
        this.refs.panel.querySelector('#guide-tour-btn').addEventListener('click', () => {
            this.closePanel();
            this.startTour();
        });

        // Section nav buttons — v5.7.1: Navigate to the actual section FIRST,
        // then open the help panel. Previously only updated panel content without
        // switching the visible modal/tab, so you'd see e.g. Statement Forge with
        // the Landing Page help walkthrough.
        this.refs.panel.querySelector('#guide-section-nav').addEventListener('click', async (e) => {
            const btn = e.target.closest('.section-nav-btn');
            if (btn) {
                const sectionId = btn.dataset.section;
                await this._navigateToSection(sectionId);
                // Wait for modal transition to complete before updating panel
                await this._wait(400);
                this.openPanel(sectionId);
            }
        });

        // Spotlight controls
        const spot = this.refs.spotlight;
        spot.querySelector('.tooltip-close').addEventListener('click', () => this.endTour());
        spot.querySelector('#guide-skip-btn').addEventListener('click', () => this.endTour());
        spot.querySelector('#guide-prev-btn').addEventListener('click', () => this.previousStep());
        spot.querySelector('#guide-next-btn').addEventListener('click', () => this.nextStep());

        // Demo bar controls
        this.refs.demoBar.querySelector('#demo-prev').addEventListener('click', () => this.demoPrev());
        this.refs.demoBar.querySelector('#demo-play').addEventListener('click', () => this.demoTogglePause());
        this.refs.demoBar.querySelector('#demo-next').addEventListener('click', () => this.demoNext());
        this.refs.demoBar.querySelector('#demo-stop').addEventListener('click', () => this.stopDemo());
        this.refs.demoBar.querySelector('#demo-speed').addEventListener('change', (e) => {
            this.demo.speed = parseFloat(e.target.value);
        });

        // Click outside panel to close
        document.addEventListener('click', (e) => {
            if (this.state.panelOpen &&
                !e.target.closest('#aegis-guide-beacon') &&
                !e.target.closest('#aegis-guide-panel')) {
                this.closePanel();
            }
        });

        // Keyboard: Escape closes tour/demo/panel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.demo.isPlaying) this.stopDemo();
                else if (this.state.tourActive) this.endTour();
                else if (this.state.panelOpen) this.closePanel();
            }
        });
    },

    // ═════════════════════════════════════════════════════════════════
    // PANEL METHODS
    // ═════════════════════════════════════════════════════════════════

    togglePanel(section = null) {
        if (this.state.panelOpen) {
            this.closePanel();
        } else {
            this.openPanel(section);
        }
    },

    openPanel(section = null) {
        if (!this.state.enabled) return;

        if (!section) section = this.detectCurrentSection();
        if (!section || !this.sections[section]) section = 'landing';

        const sectionData = this.sections[section];
        this.state.currentSection = section;

        // Populate content
        this.refs.panel.querySelector('#guide-panel-title').textContent = sectionData.title;
        this.refs.panel.querySelector('#guide-panel-what-is-this').textContent = sectionData.whatIsThis;

        // Actions
        const actionsList = this.refs.panel.querySelector('#guide-panel-actions');
        actionsList.innerHTML = sectionData.keyActions
            .map(a => `<li class="action-item">
                <span class="action-icon" data-lucide="${a.icon}"></span>
                <span class="action-text">${a.text}</span>
            </li>`).join('');

        // Tips
        const tipsList = this.refs.panel.querySelector('#guide-panel-tips');
        tipsList.innerHTML = sectionData.proTips
            .map(t => `<li class="tip-item"><span class="tip-bullet">&#128161;</span> ${t}</li>`).join('');
        tipsList.classList.add('hidden');
        this.refs.panel.querySelector('#guide-tips-toggle').classList.remove('expanded');

        // Highlight current section in nav
        this.refs.panel.querySelectorAll('.section-nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.section === section);
        });

        // Show
        this.refs.panel.classList.remove('hidden');
        this.state.panelOpen = true;

        // Re-render icons
        if (window.lucide) {
            try { window.lucide.createIcons(); } catch(e) {}
        }

        console.log('[AEGIS Guide] Panel opened:', section);
    },

    closePanel() {
        this.refs.panel.classList.add('hidden');
        this.state.panelOpen = false;
    },

    toggleTips() {
        const tipsList = this.refs.panel.querySelector('#guide-panel-tips');
        const toggle = this.refs.panel.querySelector('#guide-tips-toggle');
        tipsList.classList.toggle('hidden');
        toggle.classList.toggle('expanded');
    },

    // ═════════════════════════════════════════════════════════════════
    // TOUR METHODS (Manual step-by-step)
    // ═════════════════════════════════════════════════════════════════

    startTour(sectionId) {
        const section = sectionId || this.state.currentSection || this.detectCurrentSection();
        const sectionData = this.sections[section];

        if (!sectionData || !sectionData.tourSteps || sectionData.tourSteps.length === 0) {
            console.warn('[AEGIS Guide] No tour steps for:', section);
            if (window.showToast) window.showToast('No tour available for this section', 'info');
            return;
        }

        this.closePanel();
        this.state.tourActive = true;
        this.state.currentTourIndex = 0;
        this.state.currentTour = sectionData.tourSteps;

        this.showStep(0);
        console.log('[AEGIS Guide] Tour started:', section, '—', sectionData.tourSteps.length, 'steps');
    },

    startFullTour() {
        const tourOrder = ['landing', 'review', 'batch', 'roles', 'forge', 'validator', 'compare', 'metrics', 'history', 'settings', 'portfolio'];
        let fullTour = [];

        tourOrder.forEach(id => {
            const s = this.sections[id];
            if (s && s.tourSteps) {
                fullTour = fullTour.concat(s.tourSteps);
            }
        });

        if (fullTour.length === 0) {
            console.warn('[AEGIS Guide] No tour steps found');
            return;
        }

        this.closePanel();
        this.state.tourActive = true;
        this.state.currentTourIndex = 0;
        this.state.currentTour = fullTour;

        this.showStep(0);
        console.log('[AEGIS Guide] Full tour started:', fullTour.length, 'steps');
    },

    async showStep(index) {
        if (!this.state.currentTour || index < 0 || index >= this.state.currentTour.length) {
            this.endTour();
            return;
        }

        this.state.currentTourIndex = index;
        const step = this.state.currentTour[index];

        // Navigate to the right section if needed
        if (step.navigate) {
            await this._navigateToSection(step.navigate);
            await this._wait(400);
        }

        // Find target
        const target = document.querySelector(step.target);
        if (!target || target.offsetParent === null) {
            console.warn('[AEGIS Guide] Target not found/visible:', step.target);
            // Try next step
            if (index < this.state.currentTour.length - 1) {
                this.showStep(index + 1);
            } else {
                this.endTour();
            }
            return;
        }

        // Update tooltip
        this.refs.spotlight.querySelector('#guide-step-counter').textContent =
            `Step ${index + 1} of ${this.state.currentTour.length}`;
        this.refs.spotlight.querySelector('#guide-tooltip-title').textContent = step.title;
        this.refs.spotlight.querySelector('#guide-tooltip-description').textContent = step.description;

        // Update nav buttons
        const prevBtn = this.refs.spotlight.querySelector('#guide-prev-btn');
        const nextBtn = this.refs.spotlight.querySelector('#guide-next-btn');
        prevBtn.style.visibility = index > 0 ? 'visible' : 'hidden';
        nextBtn.textContent = index < this.state.currentTour.length - 1 ? 'Next \u2192' : 'Finish \u2713';

        // Update dots
        this.updateProgressDots(index);

        // Show spotlight
        this.showSpotlight(target, step.position || 'bottom');
        this.refs.spotlight.classList.remove('hidden');
    },

    showSpotlight(element, position = 'bottom') {
        const spotlight = this.refs.spotlight;
        const tooltip = spotlight.querySelector('.spotlight-tooltip');

        // Scroll into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(() => {
            const rect = element.getBoundingClientRect();
            const padding = 8;

            // Build SVG mask
            const w = window.innerWidth;
            const h = window.innerHeight;
            const cx = rect.left - padding;
            const cy = rect.top - padding;
            const cw = rect.width + padding * 2;
            const ch = rect.height + padding * 2;

            // Remove old SVG and hide CSS overlay (SVG mask handles dimming with cutout)
            const oldSvg = spotlight.querySelector('svg.spotlight-mask');
            if (oldSvg) oldSvg.remove();
            const cssOverlay = spotlight.querySelector('.spotlight-overlay');
            if (cssOverlay) cssOverlay.style.display = 'none';

            const svgNS = 'http://www.w3.org/2000/svg';
            const svg = document.createElementNS(svgNS, 'svg');
            svg.classList.add('spotlight-mask');
            svg.setAttribute('width', w);
            svg.setAttribute('height', h);
            svg.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;z-index:1;';

            const defs = document.createElementNS(svgNS, 'defs');
            const mask = document.createElementNS(svgNS, 'mask');
            mask.setAttribute('id', 'guideSpotlightMask');

            const bg = document.createElementNS(svgNS, 'rect');
            bg.setAttribute('width', '100%');
            bg.setAttribute('height', '100%');
            bg.setAttribute('fill', 'white');

            const cutout = document.createElementNS(svgNS, 'rect');
            cutout.setAttribute('x', cx);
            cutout.setAttribute('y', cy);
            cutout.setAttribute('width', cw);
            cutout.setAttribute('height', ch);
            cutout.setAttribute('fill', 'black');
            cutout.setAttribute('rx', '8');

            mask.appendChild(bg);
            mask.appendChild(cutout);
            defs.appendChild(mask);
            svg.appendChild(defs);

            const overlay = document.createElementNS(svgNS, 'rect');
            overlay.setAttribute('width', '100%');
            overlay.setAttribute('height', '100%');
            overlay.setAttribute('fill', 'rgba(0,0,0,0.75)');
            overlay.setAttribute('mask', 'url(#guideSpotlightMask)');
            overlay.style.pointerEvents = 'auto';
            overlay.addEventListener('click', (e) => e.stopPropagation());
            svg.appendChild(overlay);

            // v5.7.0: Add glowing highlight ring around the cutout for visibility on dark UIs
            const highlightRing = document.createElementNS(svgNS, 'rect');
            highlightRing.setAttribute('x', cx - 2);
            highlightRing.setAttribute('y', cy - 2);
            highlightRing.setAttribute('width', cw + 4);
            highlightRing.setAttribute('height', ch + 4);
            highlightRing.setAttribute('fill', 'none');
            highlightRing.setAttribute('stroke', '#58a6ff');
            highlightRing.setAttribute('stroke-width', '2.5');
            highlightRing.setAttribute('rx', '10');
            highlightRing.setAttribute('opacity', '0.9');
            svg.appendChild(highlightRing);

            // Outer glow ring for extra emphasis
            const glowRing = document.createElementNS(svgNS, 'rect');
            glowRing.setAttribute('x', cx - 5);
            glowRing.setAttribute('y', cy - 5);
            glowRing.setAttribute('width', cw + 10);
            glowRing.setAttribute('height', ch + 10);
            glowRing.setAttribute('fill', 'none');
            glowRing.setAttribute('stroke', '#58a6ff');
            glowRing.setAttribute('stroke-width', '1.5');
            glowRing.setAttribute('rx', '13');
            glowRing.setAttribute('opacity', '0.35');
            svg.appendChild(glowRing);

            spotlight.insertBefore(svg, spotlight.querySelector('.spotlight-tooltip'));

            // Position tooltip
            this.positionTooltip(tooltip, rect, position);
        }, 350);
    },

    positionTooltip(tooltip, targetRect, position) {
        const margin = 16;
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const pad = 12;

        // Reset position to measure natural size
        tooltip.style.position = 'fixed';
        tooltip.style.top = '0';
        tooltip.style.left = '0';
        tooltip.style.visibility = 'hidden';
        tooltip.style.display = 'block';
        tooltip.style.maxWidth = Math.min(420, vw - pad * 2) + 'px';

        const tRect = tooltip.getBoundingClientRect();
        const targetCenterX = targetRect.left + targetRect.width / 2;
        const targetCenterY = targetRect.top + targetRect.height / 2;
        let top, left;

        // ── Step 1: Calculate preferred position ──
        switch (position) {
            case 'top':
                top = targetRect.top - tRect.height - margin;
                left = targetCenterX - tRect.width / 2;
                break;
            case 'left':
                top = targetCenterY - tRect.height / 2;
                left = targetRect.left - tRect.width - margin;
                break;
            case 'right':
                top = targetCenterY - tRect.height / 2;
                left = targetRect.right + margin;
                break;
            default: // bottom
                top = targetRect.bottom + margin;
                left = targetCenterX - tRect.width / 2;
        }

        // ── Step 2: Horizontal — keep aligned with target, clamp to viewport ──
        // Prefer centering on target; if that overflows, anchor to target edge; final clamp to viewport
        if (left < pad) {
            // Try aligning tooltip's left edge with target's left edge
            left = Math.max(pad, targetRect.left);
        }
        if (left + tRect.width > vw - pad) {
            // Try aligning tooltip's right edge with target's right edge
            left = Math.min(vw - tRect.width - pad, targetRect.right - tRect.width);
            if (left < pad) left = pad; // safety
        }

        // ── Step 3: Vertical — flip if needed, then hard-clamp ──
        if (position === 'bottom' || position === 'top') {
            // If below overflows, try above
            if (top + tRect.height > vh - pad) {
                const aboveTop = targetRect.top - tRect.height - margin;
                top = aboveTop >= pad ? aboveTop : vh - tRect.height - pad;
            }
            // If above overflows, try below
            if (top < pad) {
                const belowTop = targetRect.bottom + margin;
                top = (belowTop + tRect.height <= vh - pad) ? belowTop : pad;
            }
        } else {
            // left/right positions — vertical center on target, clamp
            if (top < pad) top = pad;
            if (top + tRect.height > vh - pad) top = vh - tRect.height - pad;
        }

        // ── Step 4: Final safety clamp ──
        top = Math.max(pad, Math.min(top, vh - tRect.height - pad));
        left = Math.max(pad, Math.min(left, vw - tRect.width - pad));

        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
        tooltip.style.visibility = 'visible';
    },

    updateProgressDots(currentIndex) {
        const container = this.refs.spotlight.querySelector('#guide-dot-progress');
        if (!container) return;

        const total = this.state.currentTour.length;
        // For many steps, show abbreviated dots
        if (total > 15) {
            container.innerHTML = `<span class="dot-label">${currentIndex + 1} / ${total}</span>`;
            return;
        }

        container.innerHTML = '';
        for (let i = 0; i < total; i++) {
            const dot = document.createElement('span');
            dot.className = 'progress-dot' + (i === currentIndex ? ' active' : i < currentIndex ? ' done' : '');
            container.appendChild(dot);
        }
    },

    nextStep() {
        if (this.state.tourActive) {
            const next = this.state.currentTourIndex + 1;
            if (next >= this.state.currentTour.length) {
                this.endTour();
                if (window.showToast) window.showToast('Tour complete! Click the ? beacon anytime for help.', 'success');
            } else {
                this.showStep(next);
            }
        }
    },

    previousStep() {
        if (this.state.tourActive && this.state.currentTourIndex > 0) {
            this.showStep(this.state.currentTourIndex - 1);
        }
    },

    endTour() {
        this.state.tourActive = false;
        this.state.currentTourIndex = 0;
        this.state.currentTour = null;
        this.refs.spotlight.classList.add('hidden');
        // Clean up SVG and restore CSS overlay for next use
        const svg = this.refs.spotlight.querySelector('svg.spotlight-mask');
        if (svg) svg.remove();
        const cssOverlay = this.refs.spotlight.querySelector('.spotlight-overlay');
        if (cssOverlay) cssOverlay.style.display = '';
        console.log('[AEGIS Guide] Tour ended');
    },

    // ═════════════════════════════════════════════════════════════════
    // DEMO PLAYER (Auto-playing animated walkthrough)
    // ═════════════════════════════════════════════════════════════════

    startDemo(sectionId) {
        const section = sectionId || 'landing';
        const sectionData = this.sections[section];

        if (!sectionData || !sectionData.demoScenes || sectionData.demoScenes.length === 0) {
            console.warn('[AEGIS Guide] No demo scenes for:', section);
            if (window.showToast) window.showToast('No demo available for this section yet', 'info');
            return;
        }

        this.closePanel();
        this.endTour();

        this.demo.isPlaying = true;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.currentSection = section;
        this.demo.scenes = sectionData.demoScenes;

        // Show demo bar
        this.refs.demoBar.classList.remove('hidden');
        this.refs.demoBar.querySelector('#demo-bar-section').textContent = sectionData.title;
        this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';

        this._showDemoStep(0);
        console.log('[AEGIS Guide] Demo started:', section, '—', sectionData.demoScenes.length, 'scenes');
    },

    startFullDemo() {
        // Build combined demo from all sections
        const sectionOrder = ['landing', 'review', 'batch', 'roles', 'forge', 'validator', 'compare', 'metrics', 'history', 'settings', 'portfolio'];
        let allScenes = [];

        sectionOrder.forEach(id => {
            const s = this.sections[id];
            if (s && s.demoScenes) {
                // Add a section intro scene
                allScenes.push({
                    target: null,
                    narration: `Now let's explore: ${s.title}`,
                    duration: 2500,
                    sectionLabel: s.title,
                    navigate: id === 'landing' ? null : undefined
                });
                allScenes = allScenes.concat(s.demoScenes.map(scene => ({
                    ...scene,
                    sectionLabel: s.title
                })));
            }
        });

        this.closePanel();
        this.endTour();

        this.demo.isPlaying = true;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.currentSection = 'all';
        this.demo.scenes = allScenes;

        this.refs.demoBar.classList.remove('hidden');
        this.refs.demoBar.querySelector('#demo-bar-section').textContent = 'Full Application Demo';
        this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';

        this._showDemoStep(0);
        console.log('[AEGIS Guide] Full demo started:', allScenes.length, 'scenes');
    },

    async _showDemoStep(index) {
        if (!this.demo.isPlaying || !this.demo.scenes) return;
        if (index < 0 || index >= this.demo.scenes.length) {
            this.stopDemo();
            if (window.showToast) window.showToast('Demo complete! Click the ? beacon for more help.', 'success');
            return;
        }

        this.demo.currentStep = index;
        const scene = this.demo.scenes[index];
        const total = this.demo.scenes.length;

        // Update demo bar
        if (scene.sectionLabel) {
            this.refs.demoBar.querySelector('#demo-bar-section').textContent = scene.sectionLabel;
        }
        this.refs.demoBar.querySelector('#demo-step-label').textContent = `${index + 1} / ${total}`;
        this.refs.demoBar.querySelector('#demo-progress-fill').style.width =
            `${((index + 1) / total) * 100}%`;

        // Navigate if needed
        if (scene.navigate) {
            await this._navigateToSection(scene.navigate);
            await this._wait(500);
        }

        // Narration with typewriter effect
        this._typeNarration(scene.narration);

        // Spotlight target if present
        if (scene.target) {
            const el = document.querySelector(scene.target);
            if (el && el.offsetParent !== null) {
                this.refs.spotlight.classList.remove('hidden');
                // Hide the tooltip for demo (we use the demo bar instead)
                this.refs.spotlight.querySelector('.spotlight-tooltip').style.display = 'none';
                this.showSpotlight(el, 'bottom');
            } else {
                this.refs.spotlight.classList.add('hidden');
            }
        } else {
            this.refs.spotlight.classList.add('hidden');
        }

        // Schedule next step
        if (this.demo.timer) clearTimeout(this.demo.timer);
        const stepDuration = (scene.duration || this.config.demoStepDuration) / this.demo.speed;
        this.demo.timer = setTimeout(() => {
            if (this.demo.isPlaying && !this.demo.isPaused) {
                this._showDemoStep(index + 1);
            }
        }, stepDuration);
    },

    _typeNarration(text) {
        const el = this.refs.demoBar.querySelector('#demo-bar-narration');
        if (this.demo.typeTimer) clearInterval(this.demo.typeTimer);

        el.textContent = '';
        let i = 0;
        const speed = Math.max(10, this.config.demoTypeSpeed / this.demo.speed);

        this.demo.typeTimer = setInterval(() => {
            if (i < text.length) {
                el.textContent += text[i];
                i++;
            } else {
                clearInterval(this.demo.typeTimer);
                this.demo.typeTimer = null;
            }
        }, speed);
    },

    demoTogglePause() {
        if (this.demo.isPaused) {
            // Resume
            this.demo.isPaused = false;
            this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';
            // Re-trigger next step
            this._showDemoStep(this.demo.currentStep + 1);
        } else {
            // Pause
            this.demo.isPaused = true;
            this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#9654;';
            if (this.demo.timer) clearTimeout(this.demo.timer);
            if (this.demo.typeTimer) clearInterval(this.demo.typeTimer);
        }
    },

    demoPrev() {
        if (this.demo.timer) clearTimeout(this.demo.timer);
        const prev = Math.max(0, this.demo.currentStep - 1);
        this._showDemoStep(prev);
    },

    demoNext() {
        if (this.demo.timer) clearTimeout(this.demo.timer);
        this._showDemoStep(this.demo.currentStep + 1);
    },

    stopDemo() {
        this.demo.isPlaying = false;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.scenes = null;
        if (this.demo.timer) clearTimeout(this.demo.timer);
        if (this.demo.typeTimer) clearInterval(this.demo.typeTimer);

        this.refs.demoBar.classList.add('hidden');
        this.refs.spotlight.classList.add('hidden');
        // Re-show tooltip for tour mode
        const tooltip = this.refs.spotlight.querySelector('.spotlight-tooltip');
        if (tooltip) tooltip.style.display = '';
        // Clean up SVG
        const svg = this.refs.spotlight.querySelector('svg.spotlight-mask');
        if (svg) svg.remove();

        console.log('[AEGIS Guide] Demo stopped');
    },

    // ═════════════════════════════════════════════════════════════════
    // NAVIGATION HELPERS
    // ═════════════════════════════════════════════════════════════════

    async _navigateToSection(sectionId) {
        console.log('[AEGIS Guide] Navigating to section:', sectionId);

        // v5.7.1: Close all open modals first to prevent stacking.
        if (typeof closeModals === 'function') closeModals();

        // v5.7.1: Each handler uses the MOST DIRECT method to open its section.
        // Prefer showModal() or module.open() over clicking hidden nav buttons,
        // because nav buttons may have side effects or depend on other state.
        const _showModal = window.TWR?.Modals?.showModal || window.showModal;

        const navMap = {
            'landing': () => {
                // Return to landing page via the module API
                if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                    TWR.LandingPage.show();
                } else {
                    document.querySelector('#nav-dashboard')?.click();
                }
            },
            'review': () => {
                // Dismiss landing page to reveal the review view underneath
                const landing = document.getElementById('aegis-landing-page');
                if (landing && document.body.classList.contains('landing-active')) {
                    landing.classList.add('lp-exiting');
                    document.body.classList.remove('landing-active');
                }
            },
            'batch': () => {
                // Open batch upload modal directly
                if (_showModal) _showModal('batch-upload-modal');
                else document.querySelector('#btn-batch-load')?.click();
            },
            'roles': () => {
                // Use the override (loads data) > generic showModal (just shows it)
                if (window.showRolesModalOverride) window.showRolesModalOverride();
                else if (window.showRolesModal) window.showRolesModal();
                else if (_showModal) _showModal('modal-roles');
            },
            'forge': () => {
                if (_showModal) _showModal('modal-statement-forge');
                if (window.StatementForge) {
                    setTimeout(() => {
                        window.StatementForge.updateDocumentStatus();
                        window.StatementForge.loadFromSession();
                    }, 100);
                }
            },
            'validator': () => {
                if (window.HyperlinkValidator && typeof window.HyperlinkValidator.open === 'function') {
                    window.HyperlinkValidator.open();
                } else if (_showModal) _showModal('modal-hyperlink-validator');
            },
            'compare': () => {
                if (typeof openCompareFromNav === 'function') {
                    openCompareFromNav();
                } else {
                    document.querySelector('#nav-compare')?.click();
                }
            },
            'metrics': () => {
                // Open the full metrics modal, not just the sidebar accordion toggle
                if (_showModal) _showModal('modal-metrics-analytics');
                else document.querySelector('#nav-metrics')?.click();
            },
            'history': () => {
                if (_showModal) _showModal('modal-scan-history');
                else document.querySelector('#nav-history')?.click();
            },
            'settings': () => {
                if (typeof showSettingsModal === 'function') showSettingsModal();
                else document.querySelector('#btn-settings')?.click();
            },
            'portfolio': () => {
                if (window.Portfolio && typeof window.Portfolio.open === 'function') {
                    window.Portfolio.open();
                } else {
                    document.querySelector('#nav-portfolio')?.click();
                }
            }
        };

        const fn = navMap[sectionId];
        if (fn) fn();
    },

    _wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // ═════════════════════════════════════════════════════════════════
    // SECTION DETECTION
    // ═════════════════════════════════════════════════════════════════

    detectCurrentSection() {
        const checks = [
            { id: 'aegis-landing-page', section: 'landing', check: el => el.offsetParent !== null },
            { id: 'modal-roles', section: 'roles', check: el => el.classList.contains('active') },
            { id: 'modal-statement-forge', section: 'forge', check: el => el.classList.contains('active') || el.style.display !== 'none' },
            { id: 'modal-hyperlink-validator', section: 'validator', check: el => el.classList.contains('active') },
            { id: 'modal-doc-compare', section: 'compare', check: el => el.classList.contains('active') },
            { id: 'modal-metrics-analytics', section: 'metrics', check: el => el.classList.contains('active') },
            { id: 'modal-scan-history', section: 'history', check: el => el.classList.contains('active') },
            { id: 'modal-settings', section: 'settings', check: el => el.classList.contains('active') }
        ];

        for (const c of checks) {
            const el = document.getElementById(c.id);
            if (el && c.check(el)) return c.section;
        }

        // If issues are visible, we're in review mode
        const issuesContainer = document.getElementById('issues-container');
        if (issuesContainer && issuesContainer.children.length > 0) return 'review';

        return 'landing';
    },

    // ═════════════════════════════════════════════════════════════════
    // PUBLIC API: Help buttons for modals
    // ═════════════════════════════════════════════════════════════════

    addHelpButton(modalElement, sectionId) {
        if (!modalElement || !this.state.enabled) return;

        const header = modalElement.querySelector('.modal-header, .forge-header, .hv-header');
        if (!header) return;
        if (header.querySelector('.modal-help-btn')) return;

        const helpBtn = document.createElement('button');
        helpBtn.className = 'modal-help-btn';
        helpBtn.setAttribute('aria-label', 'Help for this section');
        helpBtn.setAttribute('title', 'Help');
        helpBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>`;

        helpBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.openPanel(sectionId);
        });

        const closeBtn = header.querySelector('.modal-close-btn, .forge-close-btn, .hv-btn-close');
        if (closeBtn) {
            header.insertBefore(helpBtn, closeBtn);
        } else {
            header.appendChild(helpBtn);
        }
    },

    openSectionHelp(sectionId) {
        this.openPanel(sectionId);
    }
};

// ═════════════════════════════════════════════════════════════════════
// AUTO-INITIALIZE
// ═════════════════════════════════════════════════════════════════════

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AEGISGuide.init());
} else {
    AEGISGuide.init();
}

// Export globally
window.AEGISGuide = AEGISGuide;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AEGISGuide;
}
