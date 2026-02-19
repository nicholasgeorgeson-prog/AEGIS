/**
 * AEGIS Guide System v2.3.0 - Interactive Help, Guided Tours & Narrated Live Demos
 * ==================================================================================
 * A comprehensive help system with:
 * - Floating pulsing "?" beacon (bottom-right)
 * - Contextual help slideout panel with real content
 * - Spotlight overlay guided tours (manual step-by-step)
 * - Cinematic auto-playing demo player (Watch Demo) with 79 overview scenes
 * - Deep-dive sub-demo system with ~58 sub-demos covering every sub-function
 * - Demo picker UI with overview card + sub-demo grid in help panel
 * - Section-specific and full-app tours across all 11 AEGIS modules
 * - Voice narration system (Web Speech API + pre-generated audio)
 * - Settings integration (enable/disable globally)
 * - Full demo runs ~10 minutes with narration at 1x speed
 *
 * Version: 2.3.0
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
        currentSubDemo: null,       // v2.3.0: Active sub-demo ID (null = overview)
        scenes: null,
        timer: null,
        typeTimer: null,
        speed: 1
    },

    // ─── Voice Narration State ────────────────────────────────────────
    narration: {
        enabled: false,
        volume: 0.8,
        audioElement: null,           // Reusable <audio> element for pre-gen clips
        currentUtterance: null,       // Web Speech API utterance
        preferredVoice: null,         // Selected system voice
        voices: [],                   // Available TTS voices
        voicesLoaded: false,
        manifest: null,               // Pre-generated audio manifest
        manifestLoaded: false,
        provider: 'auto',             // 'auto' | 'pregenerated' | 'webspeech' | 'off'
        storageKey: 'aegis-narration-enabled',
        volumeKey: 'aegis-narration-volume',
        voiceKey: 'aegis-narration-voice'
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
                    narration: 'Welcome to AEGIS — the Aerospace Engineering Governance and Inspection System. This is your mission control center for document quality. Everything you need to analyze, track, and improve technical documentation starts right here on this dashboard.',
                    duration: 7000
                },
                {
                    target: '#lp-hero',
                    narration: 'This is the document drop zone — the fastest way to start a review. Simply drag any Word document or PDF right onto this area, and AEGIS will immediately begin scanning it through over one hundred quality checkers. You can also click here to browse for files on your computer.',
                    duration: 8000
                },
                {
                    target: '#lp-metrics',
                    narration: 'These six metric cards give you a real-time snapshot of your document portfolio. Total scans completed, number of unique documents reviewed, roles discovered across all documents, requirement statements extracted, your average quality score, and the total number of active quality checkers. Every number updates automatically after each scan.',
                    duration: 9000
                },
                {
                    target: '#lp-tiles',
                    narration: 'Below the metrics, you will find quick-access tiles for every major AEGIS feature. Each tile shows a live count badge pulled from your database. Click any tile to jump directly into that tool — Document Review, Statement Forge, Roles Studio, Metrics and Analytics, Scan History, Document Compare, Link Validator, Portfolio, Statement Review, and SOW Generator.',
                    duration: 10000
                },
                {
                    target: '#lp-getting-started',
                    narration: 'If you are new to AEGIS, this Getting Started card is your best friend. Click it to launch a comprehensive guided tour that walks you through every single feature step by step. The question mark beacon in the bottom right corner gives you instant contextual help from any screen.',
                    duration: 8000
                },
                {
                    target: '#lp-recent',
                    narration: 'The Recent Documents section at the bottom shows your latest scans with their quality grades and timestamps. Click any entry to instantly reload those review results. This is perfect for picking up where you left off or revisiting a previous analysis.',
                    duration: 7500
                },
                {
                    target: '#aegis-landing-page',
                    narration: 'You can return to this dashboard at any time by clicking the AEGIS logo in the top left corner, or by pressing the Escape key. Now let us explore each feature in detail — starting with the heart of AEGIS: Document Review.',
                    duration: 7000
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                metric_cards: {
                    id: 'metric_cards',
                    title: 'Metric Cards',
                    icon: 'bar-chart-2',
                    description: 'Dashboard statistics and drill-down cards',
                    preAction: async () => {
                        // Ensure landing page is visible
                        if (!document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.show) window.TWR.LandingPage.show();
                            await AEGISGuide._wait(400);
                        }
                    },
                    scenes: [
                        { target: '#lp-metrics', narration: 'The metric cards row displays six key performance indicators pulled live from your scan history database. Each card updates automatically after every document review.', duration: 7000 },
                        { target: '#lp-metrics', narration: 'Total Scans shows the cumulative number of review sessions completed. Documents Reviewed counts unique files analyzed. Roles Discovered tracks the total number of organizational roles extracted across all scans.', duration: 8000 },
                        { target: '#lp-metrics', narration: 'Statements Extracted shows the count of requirement statements found by Statement Forge. Average Score displays your mean quality grade across all reviewed documents. Active Checkers shows how many quality rules are currently enabled in your configuration.', duration: 8500 },
                        { target: '#lp-metrics', narration: 'Click any metric card to expand a drill-down panel showing historical trends and detailed breakdowns. The expanded card spans two columns and provides deeper context for that particular metric.', duration: 7000 },
                        { target: '#lp-metrics', narration: 'Numbers animate with a count-up effect when the dashboard loads, giving you visual feedback that data is being refreshed from the database in real time.', duration: 6000 }
                    ]
                },
                feature_tiles: {
                    id: 'feature_tiles',
                    title: 'Feature Tiles',
                    icon: 'layout-grid',
                    description: 'Quick-access tiles with live badges',
                    preAction: async () => {
                        if (!document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.show) window.TWR.LandingPage.show();
                            await AEGISGuide._wait(400);
                        }
                    },
                    scenes: [
                        { target: '#lp-tiles', narration: 'The feature tiles provide one-click access to every major AEGIS tool. Each tile displays an icon, title, description, and a live count badge showing relevant data from your database.', duration: 7500 },
                        { target: '#lp-tiles', narration: 'Document Review is the primary analysis tool. Roles Studio manages extracted roles. Statement Forge handles requirement statements. Each tile badge reflects real counts — documents scanned, roles found, statements extracted.', duration: 8000 },
                        { target: '#lp-tiles', narration: 'Metrics and Analytics opens a command center with quality trends. Scan History shows your complete review archive. Document Compare lets you diff two scans of the same document side by side.', duration: 8000 },
                        { target: '#lp-tiles', narration: 'Hyperlink Validator checks URLs in your documents. Portfolio View provides a bird-eye overview of all documents with quality gates. SOW Generator creates statement of work templates from your role and requirement data.', duration: 8000 },
                        { target: '#lp-tiles', narration: 'Click any tile to jump directly into that feature. The tile opens the corresponding modal or view while preserving your dashboard state. You can return to the dashboard at any time using the AEGIS logo or Escape key.', duration: 7000 }
                    ]
                },
                getting_started: {
                    id: 'getting_started',
                    title: 'Getting Started',
                    icon: 'compass',
                    description: 'Onboarding guide and recent activity',
                    preAction: async () => {
                        if (!document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.show) window.TWR.LandingPage.show();
                            await AEGISGuide._wait(400);
                        }
                    },
                    scenes: [
                        { target: '#lp-getting-started', narration: 'The Getting Started card is designed for new users. Click it to launch a comprehensive guided tour that walks you step by step through every feature in AEGIS. The tour highlights each interactive element with a spotlight overlay and explains its purpose.', duration: 8000 },
                        { target: '#lp-recent', narration: 'The Recent Documents section shows your latest scans in reverse chronological order. Each entry displays the filename, quality grade, issue count, and timestamp of when the scan was performed.', duration: 7500 },
                        { target: '#lp-recent', narration: 'Click any recent entry to instantly reload that review session — all issues, statistics, and the quality grade are restored from your database. This makes it easy to pick up exactly where you left off.', duration: 7000 },
                        { target: '#lp-hero', narration: 'The quickest way to start a review is the drag-and-drop zone at the top of the dashboard. Simply drag a docx, doc, or PDF file from your file explorer directly onto this area. AEGIS immediately begins the upload and analysis process.', duration: 7500 }
                    ]
                },
                // v5.9.10: Help system and keyboard shortcuts
                keyboard_shortcuts: {
                    id: 'keyboard_shortcuts',
                    title: 'Keyboard Shortcuts',
                    icon: 'keyboard',
                    description: 'All keyboard shortcuts across AEGIS',
                    preAction: async () => {
                        try {
                            // v5.9.15: Open Help & Docs modal to show shortcuts in context
                            const helpModal = document.getElementById('modal-help');
                            if (helpModal) {
                                helpModal.classList.add('active');
                                helpModal.style.display = 'flex';
                                helpModal.style.zIndex = '148000';
                                AEGISGuide._helpCleanup = () => {
                                    helpModal.classList.remove('active');
                                    helpModal.style.display = '';
                                    helpModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-help', narration: 'AEGIS supports comprehensive keyboard shortcuts throughout the application. Press F1 from anywhere to open the Help panel for the current section. Press Escape to close any open modal, panel, or overlay.', duration: 7500 },
                        { target: '#modal-help', narration: 'In Document Review, press Control-B to toggle the sidebar, Control-O to open a file dialog, and Control-S to export results. Arrow keys navigate between issues in the results table. Enter expands issue details and Escape collapses them.', duration: 8000 },
                        { target: '#modal-help', narration: 'In Triage Mode, K keeps the current issue, S suppresses it, and F marks it as fixed. Left and right arrows navigate between issues. These single-key shortcuts enable rapid issue processing without touching the mouse.', duration: 7500 },
                        { target: '#modal-help', narration: 'In Roles Studio Dictionary, J and K navigate between role cards, Enter opens the editor, Space toggles selection, T switches between table and card view, and forward-slash focuses the search input. These vim-inspired shortcuts accelerate bulk role management.', duration: 8500 },
                        { target: '#modal-help', narration: 'In Statement Forge, Control-A selects all visible statements and Control-S exports to CSV. Adjudication supports Control-Z for undo and Control-Y for redo. The question mark key opens the shortcut reference modal from any section.', duration: 8000 }
                    ]
                },
                help_navigation: {
                    id: 'help_navigation',
                    title: 'Help System',
                    icon: 'help-circle',
                    description: 'Context-sensitive help and demo picker',
                    preAction: async () => {
                        try {
                            // v5.9.15: Open Help & Docs modal to show the help system
                            const helpModal = document.getElementById('modal-help');
                            if (helpModal) {
                                helpModal.classList.add('active');
                                helpModal.style.display = 'flex';
                                helpModal.style.zIndex = '148000';
                                AEGISGuide._helpCleanup = () => {
                                    helpModal.classList.remove('active');
                                    helpModal.style.display = '';
                                    helpModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-help', narration: 'Every major section in AEGIS has a pulsing question mark beacon in the bottom right corner of the screen. Click this beacon to open the contextual help panel. The panel automatically detects which section you are viewing and shows relevant help content.', duration: 8000 },
                        { target: '.help-sidebar', narration: 'The help panel sidebar provides organized navigation through all help topics. What Is This provides a high-level description of each feature. Key Actions lists the primary things you can do with step-by-step instructions.', duration: 8500 },
                        { target: '#help-search-input', narration: 'The search bar lets you find help topics by keyword. Type any term and the results filter in real time. The Watch Demo button at the bottom opens the Demo Picker showing overview and deep-dive sub-demo cards.', duration: 8000 },
                        { target: '#btn-help-print', narration: 'The print button generates a printable version of the current help documentation. Navigation buttons at the bottom of the help panel let you browse between sections. The comprehensive documentation covers every AEGIS feature.', duration: 7500 }
                    ]
                },
                accessibility_features: {
                    id: 'accessibility_features',
                    title: 'Accessibility',
                    icon: 'eye',
                    description: 'Screen readers, keyboard nav, and themes',
                    preAction: async () => {
                        try {
                            // v5.9.15: Open settings to display tab to show accessibility-related options
                            document.querySelector('#btn-settings')?.click();
                            await AEGISGuide._wait(500);
                            document.querySelector('[data-tab="display"]')?.click();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#settings-display', narration: 'AEGIS is built with accessibility in mind. The Display settings tab provides visual options including compact mode, essentials mode, and chart visibility toggles. All interactive elements have ARIA labels for screen reader compatibility.', duration: 8000, navigate: 'settings' },
                        { target: '#settings-display', narration: 'Full keyboard navigation is supported throughout the application. Every button, link, and interactive control is reachable via the Tab key. Focus indicators clearly show which element is active. Escape closes any modal or overlay.', duration: 7500, navigate: 'settings' },
                        { target: '#settings-display', narration: 'The dark mode and light mode themes provide different visual options. Dark mode reduces eye strain in low-light environments with a carefully chosen color palette. Light mode offers maximum contrast for bright environments. Toggle with the theme button in the navigation bar.', duration: 8000, navigate: 'settings' },
                        { target: '#settings-display', narration: 'Live regions using aria-live attributes announce dynamic updates like toast notifications, loading states, and progress changes to screen readers. Decorative icons are hidden from assistive technology with aria-hidden to prevent noise.', duration: 8000, navigate: 'settings' }
                    ]
                }
            }
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
                    narration: 'Document Review is the heart of AEGIS. Start by clicking the Open button in the toolbar, or drag and drop a file directly onto the page. AEGIS supports Word documents in dot-docx and dot-doc formats, as well as PDF files up to one hundred megabytes.',
                    duration: 8000
                },
                {
                    target: '#btn-batch-load',
                    narration: 'Need to review multiple documents at once? The Batch button opens a powerful batch upload interface. You can select individual files, choose an entire folder, or enter a server file path. AEGIS scans up to five hundred documents across nested subdirectories using parallel processing — three files at a time for optimal performance.',
                    duration: 9000
                },
                {
                    target: '#btn-toggle-advanced',
                    narration: 'Before scanning, you may want to customize which quality checkers are active. Click Advanced Settings to reveal over one hundred individual checkers organized into eight categories: Writing Quality, Grammar, Technical Writing, Clarity, Document Structure, Standards Compliance, Advanced NLP, and spaCy Deep Analysis. Toggle any checker on or off to tailor the review to your document type.',
                    duration: 10000
                },
                {
                    target: '#btn-review',
                    narration: 'When you are ready, click the Review button to begin analysis. AEGIS processes your document through every enabled checker. You will see a real-time progress dashboard showing each analysis phase — text extraction, grammar checks, style analysis, requirements verification, role detection, and more. Most documents complete in five to thirty seconds.',
                    duration: 9000
                },
                {
                    target: '#unified-filter-bar',
                    narration: 'Once the scan completes, your results appear here in the filter bar. Issues are categorized by severity — Critical in red, High in orange, Medium in yellow, Low in blue, and Info in gray. Each severity pill shows a count. Click any pill to toggle that severity level on or off. The search box lets you find specific issues by keyword.',
                    duration: 9500
                },
                {
                    target: '#stats-bar',
                    narration: 'The statistics bar gives you essential document metrics at a glance: total word count, paragraph count, heading count, number of tables detected, total issues found, the Flesch-Kincaid readability score, and your overall quality grade from A-plus through F. Click the grade badge to see a detailed breakdown of exactly how the score was calculated.',
                    duration: 9500
                },
                {
                    target: '#issues-container',
                    narration: 'The issues table shows every quality finding with its severity level, category, the flagged text, and a suggested fix. Click any row to expand the full details including context, the checker that found it, and the specific rule that was triggered. Each issue includes an actionable recommendation for how to improve the text.',
                    duration: 9000
                },
                {
                    target: '#btn-open-fix-assistant',
                    narration: 'The Fix Assistant reviews your issues and suggests specific text replacements. Step through each suggestion one by one, accepting or rejecting changes. When you are done, the Export modal shows how many fixes you have selected to apply. This workflow makes it easy to systematically address every finding in your document.',
                    duration: 9000
                },
                {
                    target: '#btn-export',
                    narration: 'When your review is complete, click Export to save your results. AEGIS offers five export formats: an annotated Word document with issues embedded as comments, a professionally formatted PDF report with executive summary, an Excel spreadsheet for detailed analysis, a CSV file for data processing, and raw JSON for integration with other tools. You can also filter which issues to include by severity or category before exporting.',
                    duration: 10000
                },
                {
                    target: '#btn-open',
                    narration: 'Every scan is automatically saved to your Scan History database. You can reopen any previous review at any time, compare results across multiple scans of the same document, and track quality improvement over time. Document Review is the foundation that feeds data to every other AEGIS feature.',
                    duration: 8000
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                file_loading: {
                    id: 'file_loading',
                    title: 'File Loading',
                    icon: 'file-plus',
                    description: 'Opening, drag-drop, and document formats',
                    preAction: async () => {
                        // Ensure we're in review mode (dismiss landing if needed)
                        if (document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                            await AEGISGuide._wait(400);
                        }
                    },
                    scenes: [
                        { target: '#btn-open', narration: 'The Open button launches a file browser dialog where you can select any supported document. AEGIS supports three formats: Word documents in dot-docx format, legacy Word documents in dot-doc format, and PDF files. The maximum supported file size is one hundred megabytes.', duration: 8000 },
                        { target: '#dropzone', narration: 'You can also drag and drop files directly onto the page from your file explorer. The entire document area becomes a drop zone. When a file is detected, AEGIS shows a visual indicator confirming the drop target. This is the fastest way to start a review.', duration: 7500 },
                        { target: '#stats-bar', narration: 'After loading, AEGIS displays the filename and file size in the toolbar. For Word documents, AEGIS uses an intelligent extraction chain: first Docling for maximum fidelity, then Mammoth for semantic HTML, with a legacy fallback. For PDFs, pymupdf4llm provides structured Markdown extraction.', duration: 9000 },
                        { target: '#btn-review', narration: 'Large files over two megabytes automatically skip the Docling extractor to prevent memory issues and use fast table mode instead. Files between one and two megabytes use a balanced extraction approach. This adaptive behavior ensures consistent performance across all document sizes.', duration: 8000 }
                    ]
                },
                checker_config: {
                    id: 'checker_config',
                    title: 'Checker Configuration',
                    icon: 'sliders-horizontal',
                    description: 'Toggle and configure quality checkers',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.16-fix: Expand the sidebar first so checker toggles are visible
                            const sidebar = document.getElementById('sidebar');
                            if (sidebar && sidebar.classList.contains('collapsed')) {
                                document.querySelector('#btn-sidebar-collapse')?.click();
                                await AEGISGuide._wait(400);
                            }
                            // Then expand the advanced panel
                            const advPanel = document.getElementById('advanced-panel');
                            if (advPanel && window.getComputedStyle(advPanel).display === 'none') {
                                document.querySelector('#btn-toggle-advanced')?.click();
                                await AEGISGuide._wait(300);
                            }
                            // Scroll the advanced panel into view within the sidebar
                            if (advPanel) advPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#advanced-panel', narration: 'The Advanced Settings panel reveals over one hundred individual quality checkers organized into eight categories. Each category has a master toggle to enable or disable all checkers in that group at once.', duration: 7000 },
                        { target: '[data-checker="grammar"]', narration: 'Writing Quality covers style and readability. Grammar handles spelling, punctuation, and sentence structure. Technical Writing checks for passive voice, nominalization, and clarity issues. Each checker has its own toggle — click to enable or disable.', duration: 8000 },
                        { target: '[data-checker="weak_language"]', narration: 'The Clarity category flags vague language, ambiguous pronouns, and unclear references. Document Structure checks headings, numbering, and formatting consistency. Standards Compliance verifies requirements against MIL-STD, DO-178C, and other aerospace standards.', duration: 8500 },
                        { target: '[data-checker="complexity_analysis"]', narration: 'Advanced NLP uses natural language processing for semantic analysis — detecting terminology inconsistencies, acronym issues, and cross-reference problems. spaCy Deep Analysis provides entity recognition, dependency parsing, and sophisticated readability metrics.', duration: 8500 },
                        { target: '#btn-toggle-advanced', narration: 'Individual toggles let you fine-tune exactly which rules to apply. Your configuration persists across sessions via local storage. Click Advanced Settings again to collapse the panel when you are done configuring.', duration: 7500 }
                    ]
                },
                review_progress: {
                    id: 'review_progress',
                    title: 'Review Process',
                    icon: 'play',
                    description: 'Running a review and progress tracking',
                    preAction: async () => {
                        if (document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                            await AEGISGuide._wait(400);
                        }
                        // Inject simulated progress dashboard so users can see what it looks like
                        if (typeof DemoSimulator !== 'undefined') {
                            DemoSimulator.showProgressDashboard();
                            await AEGISGuide._wait(300);
                        }
                    },
                    scenes: [
                        { target: '#btn-review', narration: 'Once your document is loaded and checkers configured, click the Review button to begin analysis. The button is disabled until a document is loaded. AEGIS validates the file and starts the multi-phase review pipeline.', duration: 7500 },
                        { target: '#dropzone', narration: 'During the review, a real-time progress dashboard appears in this area showing each analysis phase: text extraction, grammar checks, style analysis, requirements verification, role detection, standards compliance, and NLP deep analysis. Each phase shows its completion status with animated checkmarks.', duration: 8500 },
                        { target: '#dropzone', narration: 'The progress dashboard displays an overall percentage bar, estimated time remaining, and the name of the current checker being executed. If any phase encounters an error, it logs the issue and continues with the remaining checkers.', duration: 7500 },
                        { target: '#btn-review', narration: 'You can cancel the review at any time using the Cancel button in the progress overlay. Most documents complete in five to thirty seconds depending on length and the number of enabled checkers. Longer documents with all checkers enabled may take up to a minute.', duration: 8000 },
                        { target: '#issues-container', narration: 'When the review completes, results populate immediately — the issues table, filter bar, statistics bar, and quality grade all appear at once. The results are also automatically saved to your Scan History database for future reference.', duration: 7000 }
                    ]
                },
                results_filtering: {
                    id: 'results_filtering',
                    title: 'Results & Filtering',
                    icon: 'filter',
                    description: 'Issue table, severity filtering, and search',
                    preAction: async () => {
                        if (document.body.classList.contains('landing-active')) {
                            if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                            await AEGISGuide._wait(400);
                        }
                        // Inject simulated results so filter bar and issues table have content
                        if (typeof DemoSimulator !== 'undefined') {
                            DemoSimulator.showSimulatedResults();
                            DemoSimulator.populateSeverityCounts();
                            await AEGISGuide._wait(300);
                        }
                    },
                    scenes: [
                        { target: '#unified-filter-bar', narration: 'The filter bar sits above the issues table and provides powerful tools for narrowing down your results. Severity pills show counts for each level — Critical, High, Medium, Low, and Info. Click any pill to toggle that severity on or off.', duration: 8000 },
                        { target: '#unified-filter-bar', narration: 'The category dropdown lets you filter by issue type — Grammar, Style, Technical, Standards Compliance, and more. You can combine severity and category filters to zero in on exactly the issues you care about.', duration: 7000 },
                        { target: '#unified-filter-bar', narration: 'The search box provides instant free-text search across all issue fields — the flagged text, the suggestion, the category name, and the checker that found it. Results update as you type with debounced performance.', duration: 7500 },
                        { target: '#stats-bar', narration: 'The statistics bar shows essential document metrics: word count, paragraph count, heading count, table count, total issues found, the Flesch-Kincaid readability score, and the overall quality grade. Click the grade badge to see a detailed scoring breakdown.', duration: 8000 },
                        { target: '#issues-container', narration: 'The issues table lists every finding with its severity indicator, category, flagged text excerpt, and suggested fix. Click any row to expand full details including the source context, the specific checker and rule, and the complete recommendation.', duration: 8000 },
                        { target: '#issues-container', narration: 'Issues are sortable by clicking column headers. The severity column sorts from Critical to Info. You can also use the keyboard — arrow keys navigate between issues, Enter expands details, and Escape collapses them.', duration: 7000 }
                    ]
                },
                fix_assistant: {
                    id: 'fix_assistant',
                    title: 'Fix Assistant',
                    icon: 'wand-2',
                    description: 'Step-through guided issue fixing',
                    preAction: async () => {
                        try {
                            // v5.9.14: Show the FA modal structure for demo purposes
                            // FixAssistant.open() requires scan data, so we show the modal directly
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            const faModal = document.getElementById('fav2-modal');
                            if (faModal) {
                                faModal.style.display = 'flex';
                                faModal.style.zIndex = '148000';
                                // Store cleanup function for when demo ends
                                AEGISGuide._faCleanup = () => {
                                    faModal.style.display = 'none';
                                    faModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#fav2-modal', narration: 'The Fix Assistant is a full-screen review interface for stepping through fixable issues one at a time. It opens from the review toolbar when fixes are available. The two-panel layout shows your document on the left with highlighted fix locations, and the fix details panel on the right.', duration: 8500 },
                        { target: '#fav2-change-before', narration: 'The change preview shows the original text on top and the suggested replacement below, with a clear visual diff highlighting exactly what will change. Each fix includes a confidence badge indicating how safe the change is, and a category label showing the type of issue.', duration: 8000 },
                        { target: '#fav2-btn-accept', narration: 'For each fix, you choose Accept, Reject, or Skip using the action buttons or keyboard shortcuts. Press A to accept, R to reject, S to skip. Accepted fixes are queued for application. Rejected items are excluded. Skip moves to the next issue without deciding, so you can return later.', duration: 8000 },
                        { target: '#fav2-progress-bar', narration: 'The progress bar at the top tracks how many fixes you have reviewed out of the total. When you finish, the assistant returns you to the Export modal with your selections ready. The export can then apply accepted text corrections directly to your document.', duration: 7500 }
                    ]
                },
                export_suite: {
                    id: 'export_suite',
                    title: 'Export Suite',
                    icon: 'download',
                    description: 'Five export formats with pre-export filtering',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.15: Open the export modal so scenes can target content inside it
                            const exportModal = document.getElementById('modal-export');
                            if (exportModal) {
                                exportModal.classList.add('active');
                                exportModal.style.display = 'flex';
                                exportModal.style.zIndex = '148000';
                                AEGISGuide._exportCleanup = () => {
                                    exportModal.classList.remove('active');
                                    exportModal.style.display = '';
                                    exportModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-export', narration: 'The Export modal presents all five export formats as clickable cards. Each card shows the format icon, name, and a brief description of what it produces. Select your desired format, then click Export to generate and download the file.', duration: 7500 },
                        { target: '#format-docx-card', narration: 'The annotated DOCX format creates a copy of your original document with every issue embedded as a Word comment at the exact location of the flagged text. Reviewers can see issues in context using the familiar Track Changes interface in Microsoft Word.', duration: 8500 },
                        { target: '#format-pdf-card', narration: 'The PDF Report generates a professionally formatted document using AEGIS branding. It includes a cover page, executive summary, severity and category breakdown tables, and detailed issue listings grouped by category. Perfect for formal review deliverables.', duration: 8500 },
                        { target: '#format-xlsx-card', narration: 'Excel format creates a multi-sheet workbook with issues, statistics, and metadata. CSV provides a flat table for data processing. JSON gives you structured data for integration with other tools like DOORS, Jama, or custom workflows.', duration: 8000 },
                        { target: '#export-filter-panel', narration: 'Before exporting, you can apply filters. The collapsible filter panel lets you select specific severity levels and categories using chip-based multi-select toggles. A live preview count updates as you change filters, showing exactly how many issues will be included.', duration: 8000 },
                        { target: '#btn-do-export', narration: 'Click the Export button to generate your file. A progress overlay shows a format-specific animation and the current issue count being processed. The export runs in the background. A toast notification confirms completion and the file downloads automatically.', duration: 7500 }
                    ]
                },
                // v5.9.10: Deep-dive sub-demos for complete feature coverage
                review_presets: {
                    id: 'review_presets',
                    title: 'Review Presets & Profiles',
                    icon: 'bookmark',
                    description: 'Quick-configure checkers by document type',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-preset-reqs', narration: 'AEGIS provides four review presets that instantly configure your checkers for common scenarios. The Requirements preset enables aerospace-specific checks like MIL-STD compliance, testability verification, escape clause detection, and requirement traceability — essential for technical requirements documents.', duration: 8500 },
                        { target: '#btn-preset-grammar', narration: 'The Grammar preset focuses on language quality: spelling, punctuation, capitalization, sentence structure, passive voice, and readability. This is ideal for general business documents, memos, and reports where technical compliance checks are not needed.', duration: 8000 },
                        { target: '#btn-preset-technical', narration: 'Technical Documentation mode enables checks for document structure, cross-references, acronym consistency, terminology verification, table and figure numbering, and heading hierarchy. Perfect for technical manuals, user guides, and system descriptions.', duration: 8000 },
                        { target: '#btn-preset-all', narration: 'The All preset activates every available checker — over one hundred quality rules running simultaneously. This comprehensive scan takes longer but catches everything. Use this when you want maximum coverage and do not mind a higher volume of findings.', duration: 7500 },
                        { target: '#btn-preset-prop', narration: 'Document Type presets go further — they map to specific organizational document standards. PrOP for Procedure Operational documents, PAL for Process Asset Library items, FGOST for Flow Gate and Stage Gate documents, and SOW for Statements of Work. Each preset configures both which checkers run and what severity thresholds apply.', duration: 9000 }
                    ]
                },
                triage_mode: {
                    id: 'triage_mode',
                    title: 'Triage Mode',
                    icon: 'crosshair',
                    description: 'One-at-a-time rapid issue review',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.15: Show the triage modal so scenes can target content inside it
                            const triageModal = document.getElementById('modal-triage');
                            if (triageModal) {
                                triageModal.classList.add('active');
                                triageModal.style.display = 'flex';
                                triageModal.style.zIndex = '148000';
                                AEGISGuide._triageCleanup = () => {
                                    triageModal.classList.remove('active');
                                    triageModal.style.display = '';
                                    triageModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-triage', narration: 'Triage Mode transforms the review interface into a focused, one-issue-at-a-time workflow. Click the crosshair button in the toolbar to enter Triage Mode. Instead of scrolling through a long table, you see a single issue card filling the screen with all its details, context, and suggested action.', duration: 8500 },
                        { target: '#triage-message', narration: 'Each issue card shows the flagged text highlighted in context, the severity level, the category, the specific checker that found it, and the recommended fix. Large fonts and clear layout make rapid decision-making easy.', duration: 7500 },
                        { target: '#btn-triage-keep', narration: 'Three action buttons decide the fate of each issue. Keep marks it as a valid finding to address — the issue stays in your results. Suppress baselines the issue so it will not appear in future scans. Mark as Fixed records that you have already resolved it manually.', duration: 8000 },
                        { target: '#triage-progress-fill', narration: 'Keyboard shortcuts accelerate the workflow: press K to keep, S to suppress, F to mark as fixed. Use left and right arrow keys or the navigation buttons to move between issues without touching the mouse. A progress bar shows how many issues remain.', duration: 7500 },
                        { target: '#btn-triage-next', narration: 'Triage Mode works with your current filters — if you have filtered to only High severity issues, triage will step through only those. Combined with Family Patterns, you can triage entire groups of similar issues at once. Exit triage with the close button or press Escape.', duration: 7500 }
                    ]
                },
                family_patterns: {
                    id: 'family_patterns',
                    title: 'Family Patterns',
                    icon: 'git-merge',
                    description: 'Detect and batch-fix repeated issues',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-families', narration: 'The Families button analyzes your review results to detect repeated patterns — the same issue appearing multiple times across different locations. Click the Families button in the toolbar to run the pattern analysis.', duration: 8000 },
                        { target: '#families-inline-list', narration: 'The inline families panel appears below the filter bar, showing each pattern family as a compact card. Each card displays the pattern text, the number of matching issues, a percentage bar showing what fraction of total issues this family represents, and the severity level.', duration: 8500 },
                        { target: '#families-inline-list', narration: 'Click any family card to instantly filter the issues table to show only that family. This lets you review all instances of the same problem together. A Select All button on each card checks every issue in that family for bulk operations like export or suppression.', duration: 8000 },
                        { target: '#btn-families', narration: 'Families are detected three ways: by exact flagged text match, by the same checker rule being triggered, and by fuzzy text similarity. The top twenty families are shown sorted by frequency. Clear the family filter with the reset button to return to the full issue list.', duration: 8500 }
                    ]
                },
                score_breakdown: {
                    id: 'score_breakdown',
                    title: 'Score & Grading',
                    icon: 'award',
                    description: 'How quality grades are calculated',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.15: Show the score breakdown modal so scenes can target content inside it
                            const scoreModal = document.getElementById('modal-score-breakdown');
                            if (scoreModal) {
                                scoreModal.classList.add('active');
                                scoreModal.style.display = 'flex';
                                scoreModal.style.zIndex = '148000';
                                AEGISGuide._scoreCleanup = () => {
                                    scoreModal.classList.remove('active');
                                    scoreModal.style.display = '';
                                    scoreModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-score-breakdown', narration: 'The Score Breakdown modal reveals exactly how the quality grade is calculated. The grade ranges from A-plus through F and represents overall document quality. Critical issues carry the heaviest penalty, followed by High, Medium, Low, and Info severity levels.', duration: 8000 },
                        { target: '#score-breakdown-value', narration: 'The numeric score starts at one hundred points and each issue deducts points based on severity. Critical issues deduct the most, Info issues the least. The breakdown shows the base score, then lists each severity deduction separately so you can see exactly what drives the grade.', duration: 8500 },
                        { target: '#score-breakdown-grade', narration: 'The letter grade maps from the numeric score. A-plus for ninety-seven and above, A for ninety-three, A-minus for ninety, B-plus for eighty-seven, and so on down to F for below sixty. Document length provides a slight curve — longer documents get a more generous allowance.', duration: 8500 },
                        { target: '#score-improvements-list', narration: 'The improvement suggestions section shows specific actions to raise the grade. Each suggestion identifies the highest-impact issues to address first. Fixing all Critical issues before Medium ones typically yields the biggest grade improvement for the least effort.', duration: 8000 }
                    ]
                },
                selection_tools: {
                    id: 'selection_tools',
                    title: 'Selection & Bulk Actions',
                    icon: 'check-square',
                    description: 'Multi-select, view modes, and pagination',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-select-menu', narration: 'The Selection menu provides powerful multi-select capabilities. Choose Select This Page to check all visible issues, Select All Filtered to check every issue matching your current filters, or Deselect All to clear your selection. A counter shows how many issues are currently selected.', duration: 8500 },
                        { target: '#btn-view-table', narration: 'Toggle between Table View and Card View to change how issues are displayed. Table View shows a compact data grid ideal for quickly scanning many issues. Card View shows each issue as a rich card with more detail visible at a glance — better for thorough individual review.', duration: 8000 },
                        { target: '#btn-prev-page', narration: 'When you have many issues, pagination keeps the interface responsive. Navigate between pages using the Previous and Next buttons. The current page indicator shows where you are in the result set. Page size can be configured in Settings under Display Options.', duration: 7500 },
                        { target: '#btn-select-top-fixes-inline', narration: 'The Select Top Fixes button intelligently selects the most impactful issues to address first. It prioritizes by severity and fixability — focusing on Critical and High severity issues that have clear automated fix suggestions. This gives you the biggest quality improvement for the least effort.', duration: 8500 }
                    ]
                },
                export_docx: {
                    id: 'export_docx',
                    title: 'DOCX Export',
                    icon: 'file-text',
                    description: 'Word document with embedded comments',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.16-fix: Force-show export modal (btn-export only works with loaded doc)
                            const exportModal = document.getElementById('modal-export');
                            if (exportModal) {
                                exportModal.classList.add('active');
                                exportModal.style.display = 'flex';
                                exportModal.style.zIndex = '148000';
                                AEGISGuide._exportCleanup = () => {
                                    exportModal.classList.remove('active');
                                    exportModal.style.display = '';
                                    exportModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-export', narration: 'The Export modal presents all five export formats as clickable cards. DOCX export creates a copy of your original Word document with every quality issue embedded as a Track Changes comment. Each comment is placed at the exact location of the flagged text.', duration: 8500 },
                        { target: '#format-docx-card', narration: 'Click the DOCX format card to select it. Comments include the severity level, category, the specific issue description, and the suggested fix. Reviewers can accept, reject, or reply to each comment using the standard Word review workflow — no special tools required.', duration: 8000 },
                        { target: '#export-apply-fixes', narration: 'When Fix Assistant selections are available, the Apply Selected Fixes checkbox appears. Check it to include automated text corrections directly in the document body alongside the review comments. This combines markup and corrections in one deliverable.', duration: 8500 },
                        { target: '#btn-do-export', narration: 'Click the Export button to generate the DOCX. The format preserves your original document formatting, tables, images, and styles. Only the comment layer and any applied fixes are modified. A progress overlay shows generation status.', duration: 8000 }
                    ]
                },
                export_pdf: {
                    id: 'export_pdf',
                    title: 'PDF Report Export',
                    icon: 'file-type',
                    description: 'Branded professional report',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.16-fix: Force-show export modal
                            const exportModal = document.getElementById('modal-export');
                            if (exportModal) {
                                exportModal.classList.add('active');
                                exportModal.style.display = 'flex';
                                exportModal.style.zIndex = '148000';
                                AEGISGuide._exportCleanup = () => {
                                    exportModal.classList.remove('active');
                                    exportModal.style.display = '';
                                    exportModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#format-pdf-card', narration: 'Click the PDF Report card to select server-side PDF generation. The report is created with AEGIS branding — a professional cover page with the document title, reviewer name, scan date, and the AEGIS gold and bronze color scheme.', duration: 7500 },
                        { target: '#modal-export', narration: 'The executive summary section provides an at-a-glance overview: overall quality grade, total issues by severity, and a severity distribution breakdown table. Stakeholders can immediately understand the document quality status without reading individual issues.', duration: 8000 },
                        { target: '#modal-export', narration: 'Issues are grouped by category with a dedicated section for each checker group. Within each section, issues are listed from highest to lowest severity with the flagged text, location, and recommended action. Color-coded severity indicators carry through the entire report.', duration: 8500 },
                        { target: '#btn-do-export', narration: 'When export filters are active, a prominent filter notice banner appears at the top of the report indicating which severity levels and categories were included. Click Export to generate the PDF on the server — a progress overlay tracks generation.', duration: 7500 }
                    ]
                },
                export_excel_csv: {
                    id: 'export_excel_csv',
                    title: 'Excel & CSV Export',
                    icon: 'table',
                    description: 'Spreadsheet and data formats',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.16-fix: Force-show export modal
                            const exportModal = document.getElementById('modal-export');
                            if (exportModal) {
                                exportModal.classList.add('active');
                                exportModal.style.display = 'flex';
                                exportModal.style.zIndex = '148000';
                                AEGISGuide._exportCleanup = () => {
                                    exportModal.classList.remove('active');
                                    exportModal.style.display = '';
                                    exportModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#format-xlsx-card', narration: 'Click the Excel card to select XLSX export. The Excel export creates a multi-sheet workbook using the openpyxl library. The primary Issues sheet contains every finding with columns for severity, category, flagged text, suggestion, paragraph location, and the specific checker rule. Cells are color-coded by severity.', duration: 9000 },
                        { target: '#modal-export', narration: 'Additional sheets include a Statistics summary with document metrics and grade information, and a Metadata sheet with scan parameters, enabled checkers, and timestamp. This makes Excel exports ideal for detailed analysis and reporting.', duration: 7500 },
                        { target: '#format-csv-card', narration: 'CSV export produces a flat comma-separated file with the same columns as the Excel Issues sheet. This format is universally compatible — import it into any spreadsheet application, database, or data analysis tool. Perfect for integration with external quality management systems.', duration: 8000 },
                        { target: '#format-json-card', narration: 'The JSON export provides structured data with full metadata, nested issue objects, and document statistics. Use this for programmatic integration with tools like DOORS, Jama, Polarion, or custom quality dashboards. The JSON schema is consistent across all scans.', duration: 8000 }
                    ]
                },
                export_filters: {
                    id: 'export_filters',
                    title: 'Export Filters',
                    icon: 'filter',
                    description: 'Pre-export severity and category filtering',
                    preAction: async () => {
                        try {
                            if (document.body.classList.contains('landing-active')) {
                                if (window.TWR?.LandingPage?.hide) window.TWR.LandingPage.hide();
                                await AEGISGuide._wait(400);
                            }
                            // v5.9.16-fix: Force-show export modal
                            const exportModal = document.getElementById('modal-export');
                            if (exportModal) {
                                exportModal.classList.add('active');
                                exportModal.style.display = 'flex';
                                exportModal.style.zIndex = '148000';
                                AEGISGuide._exportCleanup = () => {
                                    exportModal.classList.remove('active');
                                    exportModal.style.display = '';
                                    exportModal.style.zIndex = '';
                                };
                            }
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-export', narration: 'The export modal offers three issue selection modes at the top. All Issues exports everything from your review. Filtered exports only the issues matching your current filter bar selections. Selected exports only the issues you have manually checked.', duration: 8000 },
                        { target: '#export-filter-panel', narration: 'Below the mode selector, the collapsible Filter Panel provides additional fine-tuning. Click the filter header to expand it. Severity chips let you include or exclude specific severity levels — for example, export only Critical and High issues for an executive summary.', duration: 8500 },
                        { target: '#export-filter-category-chips', narration: 'Category filter chips work the same way — click to toggle each category on or off. Only categories that have issues in your current review are shown. You can combine severity and category filters to create highly targeted export subsets.', duration: 7500 },
                        { target: '#export-filter-preview', narration: 'The live preview bar at the bottom of the filter panel updates in real-time as you toggle chips. It shows exactly how many issues will be included in the export out of the total available. The Clear Filters button resets all chips to their default state.', duration: 7500 },
                        { target: '#export-filter-severity-chips', narration: 'Export filters stack on top of the mode selection. If you choose Filtered mode with severity chips set to Critical only, only the Critical issues from your filtered view will be exported. This layered approach gives you complete control over exactly what appears in your deliverables.', duration: 8500 }
                    ]
                }
            }
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
                    narration: 'Batch Scan lets you review dozens or hundreds of documents at once. Click the Batch button in the toolbar to open the batch upload interface. Let us take a look inside.',
                    duration: 7000
                },
                {
                    target: '#batch-dropzone',
                    narration: 'The drop zone accepts multiple files at once. Drag and drop documents here, or use the Select Files and Select Folder buttons below. AEGIS supports DOCX, DOC, and PDF formats.',
                    duration: 8000,
                    navigate: 'batch'
                },
                {
                    target: '#folder-scan-section',
                    narration: 'For server-side scanning, enter a file path directly. AEGIS recursively discovers all documents up to ten levels deep, automatically skipping hidden directories, files over one hundred megabytes, and non-document folders.',
                    duration: 9000,
                    navigate: 'batch'
                },
                {
                    target: '#btn-folder-discover',
                    narration: 'Use the Preview button to see exactly which files will be included before committing to a full scan. AEGIS shows the file count, total size, and a list of every discovered document.',
                    duration: 8000,
                    navigate: 'batch'
                },
                {
                    target: '#batch-file-list',
                    narration: 'During the scan, each document shows its current status — queued, processing, complete, or error. Individual failures do not stop the batch. AEGIS processes three documents simultaneously for optimal throughput.',
                    duration: 9000,
                    navigate: 'batch'
                },
                {
                    target: '#btn-folder-scan',
                    narration: 'When the batch completes, you get aggregate statistics — grade distribution, severity breakdown, top issue categories, and roles discovered. Every document receives its own quality grade, all saved to Scan History for later review.',
                    duration: 8500,
                    navigate: 'batch'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                file_input: {
                    id: 'file_input',
                    title: 'File & Folder Input',
                    icon: 'folder-input',
                    description: 'Three methods to load documents for batch scanning',
                    preAction: async () => {
                        // Click batch button to open modal if not already open
                        const modal = document.getElementById('batch-upload-modal');
                        if (!modal || !modal.classList.contains('active')) {
                            document.querySelector('#btn-batch-load')?.click();
                            await AEGISGuide._wait(600);
                        }
                    },
                    scenes: [
                        { target: '#batch-dropzone', narration: 'The batch upload modal provides three input methods. The File Selector lets you pick individual documents using a standard file browser. Hold Control or Shift to select multiple files at once. Supported formats are docx, doc, and PDF.', duration: 8000 },
                        { target: '#batch-dropzone', narration: 'The Folder Selector lets you choose an entire directory. AEGIS will discover all supported documents inside that folder, including nested subdirectories up to ten levels deep. Hidden directories and common non-document folders are automatically excluded.', duration: 8000 },
                        { target: '#folder-scan-path', narration: 'The Server Path input accepts a filesystem path string for scanning remote or mapped drives. This is ideal for enterprise environments where documents live on network shares or server directories that the browser file dialog cannot access.', duration: 8000 },
                        { target: '#batch-file-list', narration: 'The file count and total size are displayed as you add documents. AEGIS enforces limits — up to five hundred files and five hundred megabytes total. Individual files larger than one hundred megabytes are flagged and can be excluded before scanning.', duration: 7500 }
                    ]
                },
                preview_discovery: {
                    id: 'preview_discovery',
                    title: 'Preview & Discovery',
                    icon: 'eye',
                    description: 'Preview files before committing to scan',
                    preAction: async () => {
                        const modal = document.getElementById('batch-upload-modal');
                        if (!modal || !modal.classList.contains('active')) {
                            document.querySelector('#btn-batch-load')?.click();
                            await AEGISGuide._wait(600);
                        }
                    },
                    scenes: [
                        { target: '#btn-folder-discover', narration: 'Before starting a scan, always use the Preview button. This runs the discovery phase without any actual document processing. AEGIS shows you the complete list of files it found, their sizes, and whether they meet the scanning criteria.', duration: 8000 },
                        { target: '#batch-file-list', narration: 'The preview list highlights potential issues — oversized files, unsupported formats, and empty files are flagged with warning indicators. You can remove individual files from the batch before committing to the full scan.', duration: 7500 },
                        { target: '#btn-folder-scan', narration: 'For folder scans, the discovery phase is nearly instant — it only reads file metadata, not content. This lets you verify the scope of a large repository scan in seconds before spending minutes on the actual review.', duration: 7000 }
                    ]
                },
                progress_dashboard: {
                    id: 'progress_dashboard',
                    title: 'Progress Dashboard',
                    icon: 'activity',
                    description: 'Real-time monitoring during batch scan',
                    preAction: async () => {
                        try {
                            const modal = document.getElementById('batch-upload-modal');
                            if (!modal || !modal.classList.contains('active')) {
                                document.querySelector('#btn-batch-load')?.click();
                                await AEGISGuide._wait(600);
                            }
                            // Inject simulated batch results to show what the dashboard looks like
                            if (typeof DemoSimulator !== 'undefined') {
                                DemoSimulator.showBatchResults();
                                await AEGISGuide._wait(300);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#batch-upload-modal', narration: 'During a batch scan, the progress dashboard updates in real time. Each document has its own row showing the filename, current status — queued, processing, complete, or error — and the quality grade once scanning finishes.', duration: 8000, navigate: 'batch' },
                        { target: '#batch-file-list', narration: 'The overall progress bar shows percentage completion across the entire batch. Statistics include elapsed time, estimated time remaining, processing speed in documents per minute, and the current processing chunk number.', duration: 7500, navigate: 'batch' },
                        { target: '#batch-upload-modal', narration: 'AEGIS processes documents in chunks of five, with three parallel workers per chunk. Between chunks, memory is cleaned up to prevent accumulation. This chunked approach allows scanning hundreds of documents without running out of memory.', duration: 8000, navigate: 'batch' },
                        { target: '#batch-file-list', narration: 'Each document has a five-minute timeout. If a single file hangs — due to corruption, extreme size, or complex formatting — it is marked as an error and processing continues with the next file. The batch never stalls.', duration: 7500, navigate: 'batch' }
                    ]
                },
                results_aggregation: {
                    id: 'results_aggregation',
                    title: 'Results & Aggregation',
                    icon: 'bar-chart-3',
                    description: 'Aggregate statistics and per-document results',
                    preAction: async () => {
                        try {
                            const modal = document.getElementById('batch-upload-modal');
                            if (!modal || !modal.classList.contains('active')) {
                                document.querySelector('#btn-batch-load')?.click();
                                await AEGISGuide._wait(600);
                            }
                            // Inject simulated batch result cards
                            if (typeof DemoSimulator !== 'undefined') {
                                DemoSimulator.showBatchResults();
                                await AEGISGuide._wait(300);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#batch-upload-modal', narration: 'When the batch completes, the results view replaces the progress dashboard. You see aggregate statistics at the top — total documents processed, pass and fail rates, average quality grade, and the grade distribution chart.', duration: 7500, navigate: 'batch' },
                        { target: '#batch-file-list', narration: 'Below the summary, each document is listed with its individual grade, issue count by severity, and a click-to-expand detail view. The documents are ranked from lowest quality to highest, making it easy to identify files that need attention.', duration: 8000, navigate: 'batch' },
                        { target: '#batch-upload-modal', narration: 'Every individual scan result is saved to your Scan History database. You can reopen any specific document review, compare it against previous scans, or view it in the Portfolio for a cross-document quality overview.', duration: 7500, navigate: 'batch' },
                        { target: '#batch-file-list', narration: 'Role discovery runs during batch scanning as well. Any new organizational roles found across the batch are added to your Roles Studio database. Statement extraction populates Statement Forge. The entire AEGIS ecosystem benefits from batch scanning.', duration: 8000, navigate: 'batch' }
                    ]
                },
                // v5.9.10: Server folder scan deep-dive
                folder_scan: {
                    id: 'folder_scan',
                    title: 'Server Folder Scan',
                    icon: 'hard-drive',
                    description: 'Scan entire document repositories by server path',
                    preAction: async () => {
                        try {
                            const modal = document.getElementById('batch-upload-modal');
                            if (!modal || !modal.classList.contains('active')) {
                                document.querySelector('#btn-batch-load')?.click();
                                await AEGISGuide._wait(600);
                            }
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#folder-scan-path', narration: 'Server Folder Scan lets you point AEGIS at any directory on the server filesystem. Enter a full path in the folder path input — for example, a shared network drive or a local document repository. AEGIS recursively discovers all supported documents in that directory tree.', duration: 8500 },
                        { target: '#btn-folder-discover', narration: 'Click Preview to run the Discovery phase first — it scans the directory structure without processing any files. You see the total file count, combined size, breakdown by file type, and a scrollable list of every file found. Hidden directories and common non-document folders are automatically excluded.', duration: 8500 },
                        { target: '#btn-folder-scan', narration: 'After reviewing the discovery results, click Scan All to begin the review phase. This runs asynchronously in the background — AEGIS processes files in chunks of five, with three parallel workers per chunk. Garbage collection runs between chunks to prevent memory buildup.', duration: 8500 },
                        { target: '#folder-scan-dashboard', narration: 'The progress display polls every one and a half seconds, showing per-file status transitions from queued to processing to complete or error. You see elapsed time, estimated time remaining, processing speed in files per minute, and the current chunk progress.', duration: 8000 },
                        { target: '#folder-scan-path', narration: 'Server Folder Scan supports up to five hundred files per scan with a depth limit on directory traversal. Files over one hundred megabytes are automatically skipped. Per-file timeouts of five minutes prevent any single file from blocking the entire scan.', duration: 7500 }
                    ]
                }
            }
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
                    narration: 'Roles Studio is one of the most powerful features in AEGIS. It automatically extracts every organizational role mentioned in your documents and builds a comprehensive database. The Overview tab shows all discovered roles ranked by mention frequency, along with document count, total mentions, and responsibility summaries.',
                    duration: 9000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-overview',
                    narration: 'Each role card displays color-coded function tags that indicate department assignments — Engineering, Quality, Administration, Program Management, and more. Click any role name to expand its full details including all responsibility statements, the documents it appears in, and its adjudication status.',
                    duration: 8500,
                    navigate: 'roles'
                },
                {
                    target: '#tab-graph',
                    narration: 'The Graph tab creates an interactive force-directed network visualization of role relationships. Roles that share documents or responsibilities are connected by edges. You can drag nodes to rearrange the layout, zoom in with your scroll wheel, and click any node to inspect that role. The graph reveals organizational structures that are not immediately obvious from reading documents.',
                    duration: 10000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-matrix',
                    narration: 'The RACI Matrix is essential for governance analysis. It shows who is Responsible, Accountable, Consulted, and Informed for each organizational function. Rows represent roles, columns represent function areas. Each cell shows a count of statements supporting that assignment. Click any cell number to see the exact requirement statements and action verbs that generated the classification.',
                    duration: 10000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-roledocmatrix',
                    narration: 'The Role-Document Matrix provides a cross-reference showing which roles appear in which documents. This is invaluable for identifying roles that span multiple specifications versus those confined to a single document. Hover over any cell to see the exact mention count and context.',
                    duration: 8000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-adjudication',
                    narration: 'The Adjudication tab is where you verify and clean up automatically discovered roles. Roles can be verified, rejected, or merged. For example, if AEGIS finds both "QA Engineer" and "Quality Assurance Engineer," you can merge them into a single canonical role. The kanban-style interface makes bulk adjudication fast and intuitive.',
                    duration: 9000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-adjudication',
                    narration: 'You can also export your adjudication decisions as an interactive HTML board for offline review by colleagues. They can make changes in their browser and export their decisions as JSON, which you then import back into AEGIS. This round-trip workflow enables collaborative role governance across teams.',
                    duration: 8500,
                    navigate: 'roles'
                },
                {
                    target: '#tab-dictionary',
                    narration: 'The Dictionary tab is your curated, authoritative role catalog. Each verified role has rich metadata: descriptions, department assignments, hierarchy level, disposition status, organizational group, and aliases. You can filter, search, and bulk-edit roles. The dashboard view shows category distributions and adjudication statistics.',
                    duration: 9000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-documents',
                    narration: 'The Documents tab lists every scanned document with its role discovery results. Click any document to see which roles were found, how many times each appears, and the specific responsibility statements extracted. This is the source-level evidence behind all of the role data in AEGIS.',
                    duration: 8000,
                    navigate: 'roles'
                },
                {
                    target: '#tab-overview',
                    narration: 'Roles Studio also supports function tag management, role inheritance mapping, and full export capabilities. You can export roles as CSV, PDF reports, interactive HTML boards, or sharing packages that other AEGIS installations can import. The entire role lifecycle — from extraction to adjudication to dictionary — is managed here.',
                    duration: 9000,
                    navigate: 'roles'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                overview_tab: {
                    id: 'overview_tab',
                    title: 'Overview Tab',
                    icon: 'list',
                    description: 'Role cards, function tags, and search',
                    preAction: async () => {
                        document.querySelector('#tab-overview')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#roles-overview', narration: 'The Overview tab is the landing view of Roles Studio. It displays all discovered roles as cards sorted by mention frequency. Each card shows the role name, document count, total mentions, and a truncated list of responsibilities.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'Color-coded function tags appear on each role card indicating department assignments — Engineering in blue, Quality in green, Administration in purple, Program Management in orange, and more. These tags are assigned during the adjudication process.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'The search bar at the top filters roles by name in real time as you type. Below it, aggregate statistics show the total number of roles, documents, mentions, and responsibility statements in your database.', duration: 7000, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'Click any role card to expand it and see the full details — every responsibility statement extracted, the source documents, adjudication status, function tags, and category. The expanded view also shows the raw extraction data for verification.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'The Overview tab also displays adjudication badges on each role card — a green checkmark for verified roles, a gold star for deliverables, and a red X for rejected roles. This visual status helps you quickly identify which roles still need review.', duration: 7500, navigate: 'roles' }
                    ]
                },
                graph_view: {
                    id: 'graph_view',
                    title: 'Graph View',
                    icon: 'git-branch',
                    description: 'Interactive relationship network visualization',
                    preAction: async () => {
                        document.querySelector('#tab-graph')?.click();
                        await AEGISGuide._wait(1500);
                        // Simulate a graph node drag interaction
                        if (typeof DemoSimulator !== 'undefined') {
                            DemoSimulator.simulateGraphDrag();
                        }
                    },
                    scenes: [
                        { target: '#roles-graph-container', narration: 'The Graph view creates an interactive force-directed network diagram using D3.js. Roles appear as nodes sized by mention count. Edges connect roles that share documents or have explicit relationships like inheritance or collaboration.', duration: 8500, navigate: 'roles' },
                        { target: '#graph-layout', narration: 'The Layout selector switches between four visualization modes. Force-directed naturally clusters related roles. Edge Bundling groups connection lines. Semantic Zoom adds hierarchical detail as you zoom in. Bipartite separates nodes into two columns.', duration: 8000, navigate: 'roles' },
                        { target: '#graph-max-nodes', narration: 'Node colors reflect function tag categories. Cluster patterns reveal organizational structures — roles in the same department tend to group together because they share documents. Adjust the Max Nodes slider to control how many roles appear.', duration: 8000, navigate: 'roles' },
                        { target: '#graph-info-panel', narration: 'Click any node to select it and open the Info Panel. The panel shows the selected role details, its connections, mention count, and source documents. Edge types include inherits-from, uses-tool, co-performs, supplies-to, and receives-from.', duration: 7500, navigate: 'roles' },
                        { target: '#graph-weight-filter', narration: 'The Weight Filter slider adjusts the minimum relationship strength shown. Moving it right hides weak connections, revealing only the strongest role relationships. You can also export the graph as an image for use in reports and presentations.', duration: 7000, navigate: 'roles' }
                    ]
                },
                details_source: {
                    id: 'details_source',
                    title: 'Details & Source Viewer',
                    icon: 'file-search',
                    description: 'Role details panel and source document viewer',
                    preAction: async () => {
                        document.querySelector('#tab-overview')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#roles-overview', narration: 'When you click a role name anywhere in Roles Studio, the Role Details panel opens. This panel shows comprehensive information — the canonical role name, all known aliases, the description, department assignment, hierarchy level, and disposition status.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'The Responsibilities section lists every extracted statement where this role was identified. Each statement shows the original text, the document it came from, the section heading, and the RACI classification derived from the action verbs used.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'The Source Viewer lets you see the original document context around each responsibility statement. Click the source icon next to any statement to open a highlighted view of the surrounding paragraphs, confirming the extraction accuracy.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-overview', narration: 'Function tags on the details panel are interactive. Click any tag to see all other roles that share that function category. This cross-reference helps you understand the organizational groupings that AEGIS has identified.', duration: 7000, navigate: 'roles' }
                    ]
                },
                raci_matrix: {
                    id: 'raci_matrix',
                    title: 'RACI Matrix',
                    icon: 'table-2',
                    description: 'Responsibility assignment matrix with drill-down',
                    preAction: async () => {
                        document.querySelector('#tab-matrix')?.click();
                        await AEGISGuide._wait(500);
                    },
                    scenes: [
                        { target: '#roles-matrix', narration: 'The RACI Matrix tab displays a formal Responsible-Accountable-Consulted-Informed assignment matrix. Rows represent organizational roles discovered across your documents. Columns represent function categories from the AEGIS function taxonomy.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-matrix', narration: 'Each cell contains a count of supporting statements. AEGIS classifies actions into RACI categories based on verb analysis — active verbs like "shall design" indicate Responsible, oversight verbs like "shall approve" indicate Accountable, review verbs map to Consulted, and notification verbs map to Informed.', duration: 9000, navigate: 'roles' },
                        { target: '#roles-matrix', narration: 'Click any cell number to drill down and see the exact requirement statements that generated that RACI assignment. The popup shows each statement, its source document, and the specific action verbs that triggered the classification.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-matrix', narration: 'The matrix supports filtering by function category using the dropdown at the top. You can also filter by RACI type to show only cells with Responsible assignments, for example. Export the filtered matrix as CSV for use in governance documents.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-matrix', narration: 'Color intensity in cells indicates the strength of the assignment — darker colors mean more supporting statements. Cells with zero statements are empty. This heat-map-like visual makes it easy to spot gaps in your responsibility assignments.', duration: 7500, navigate: 'roles' }
                    ]
                },
                role_doc_matrix: {
                    id: 'role_doc_matrix',
                    title: 'Role-Document Matrix',
                    icon: 'grid-3x3',
                    description: 'Cross-reference of roles across documents',
                    preAction: async () => {
                        document.querySelector('#tab-roledocmatrix')?.click();
                        await AEGISGuide._wait(500);
                    },
                    scenes: [
                        { target: '#roles-roledocmatrix', narration: 'The Role-Document Matrix provides a cross-reference grid showing which roles appear in which documents. Rows are roles and columns are document names. Each cell shows the mention count for that role in that document.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-roledocmatrix', narration: 'This matrix is invaluable for identifying roles that span multiple documents versus those confined to a single specification. A role appearing in many documents is likely a key organizational role that needs consistent definition across your document suite.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-roledocmatrix', narration: 'Hover over any cell to see additional context — the exact mention count and a preview of the responsibility statements found in that specific document for that role. Click the cell to navigate to the detailed view.', duration: 7000, navigate: 'roles' },
                        { target: '#roles-roledocmatrix', narration: 'The matrix can be sorted by total mentions across all documents, or by mentions in a specific document. Column headers are clickable for sorting. This helps you identify the most frequently referenced roles in any given document.', duration: 7500, navigate: 'roles' }
                    ]
                },
                adjudication: {
                    id: 'adjudication',
                    title: 'Adjudication',
                    icon: 'check-square',
                    description: 'Verify, merge, and classify discovered roles',
                    preAction: async () => {
                        document.querySelector('#tab-adjudication')?.click();
                        await AEGISGuide._wait(500);
                    },
                    scenes: [
                        { target: '#roles-adjudication', narration: 'Adjudication is where you verify and clean up automatically discovered roles. The interface presents roles in a kanban-style layout with columns for Pending, Verified, Rejected, and Merged. Drag cards between columns or use keyboard shortcuts.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'For each pending role, you can verify it as a legitimate organizational role, reject it as a false extraction, or merge it with another role. Merging is common — AEGIS might discover both "QA Engineer" and "Quality Assurance Engineer" as separate entries.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'The auto-classify feature uses pattern matching and contextual analysis to suggest adjudication decisions. It identifies likely duplicates, probable tools versus roles, and deliverables versus people. You can accept or override each suggestion.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'You can assign function tags to roles during adjudication — categorizing them by department like Engineering, Quality, Safety, Program Management, or Logistics. These tags flow through to the RACI matrix, graph view, and all exports.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'The export button creates an interactive HTML kanban board that works offline. You can share this board with colleagues who do not have AEGIS. They review and adjudicate roles in their browser, then export a JSON file that you import back into AEGIS.', duration: 8500, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'Full undo and redo support means every adjudication decision can be reversed. The keyboard shortcut Control-Z undoes the last action. Bulk operations let you select multiple roles and apply the same decision to all of them at once.', duration: 7500, navigate: 'roles' }
                    ]
                },
                dictionary: {
                    id: 'dictionary',
                    title: 'Role Dictionary',
                    icon: 'book-open',
                    description: 'Curated role catalog with rich metadata',
                    preAction: async () => {
                        document.querySelector('#tab-dictionary')?.click();
                        await AEGISGuide._wait(500);
                    },
                    scenes: [
                        { target: '#roles-dictionary', narration: 'The Dictionary tab is your authoritative, curated role catalog. Only roles that have been verified through adjudication appear here. Each entry has rich metadata — descriptions, department assignments, hierarchy level, disposition status, aliases, and organizational group.', duration: 9000, navigate: 'roles' },
                        { target: '#roles-dictionary', narration: 'The Dashboard view at the top shows statistics: total dictionary entries, category distribution as a donut chart, adjudication completion rate, and source document coverage. These metrics help you track how complete your role governance data is.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-dictionary', narration: 'Switch between Card view and Table view. Card view shows rich role cards with all metadata visible. Table view provides a compact, sortable grid for working with many roles at once. Both views support search and filtering.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-dictionary', narration: 'Inline editing lets you update any role field directly — click the description to edit it, click the category badge to change it, or use the star toggle to mark a role as a deliverable. All changes save immediately to the database.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-dictionary', narration: 'Bulk operations support selecting multiple roles and applying batch changes — activate, deactivate, delete, set category, or mark as deliverable. The Select All checkbox and keyboard shortcut Space make bulk selection fast.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-dictionary', narration: 'Duplicate detection warns you when saving a role that has a similar name or alias to an existing dictionary entry. This prevents the same role from being added twice under slightly different names.', duration: 7000, navigate: 'roles' }
                    ]
                },
                documents_tab: {
                    id: 'documents_tab',
                    title: 'Documents Tab',
                    icon: 'file-text',
                    description: 'Source documents and per-document role details',
                    preAction: async () => {
                        document.querySelector('#tab-documents')?.click();
                        await AEGISGuide._wait(500);
                    },
                    scenes: [
                        { target: '#roles-documents', narration: 'The Documents tab lists every document in your scan history that contained role mentions. Each entry shows the filename, scan date, total roles found, and total responsibility statements extracted from that specific document.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-documents', narration: 'Click any document to expand its role breakdown — a list of every role found in that file with mention counts and key responsibility excerpts. This is the source-level evidence behind all the aggregate role data in Roles Studio.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-documents', narration: 'The document list is sortable by name, date, role count, or statement count. A search filter helps you find specific documents. Documents with more roles are highlighted to indicate they are key governance documents in your repository.', duration: 7500, navigate: 'roles' },
                        { target: '#roles-documents', narration: 'From the expanded document view, you can navigate directly to Statement Forge to see the full statement extraction for that document, or to Document Compare to see how roles have changed between scans.', duration: 7000, navigate: 'roles' }
                    ]
                },
                // v5.9.10: Deep-dive sub-demos for complete Roles Studio coverage
                adjudication_exports: {
                    id: 'adjudication_exports',
                    title: 'Adjudication Exports',
                    icon: 'download',
                    description: 'CSV, HTML kanban, PDF report, and import',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-adjudication')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-export-adjudication', narration: 'The Adjudication tab has a powerful export dropdown. Click the Export button in the toolbar to reveal four format options. Each format serves a different workflow need — from simple data files to interactive collaboration boards.', duration: 8000, navigate: 'roles' },
                        { target: '#adj-export-dropdown', narration: 'CSV export creates a spreadsheet-compatible file with every role, its adjudication status, category, description, function tags, and metadata. This is ideal for importing into project management tools, DOORS, or organizational charts.', duration: 7500, navigate: 'roles' },
                        { target: '#adj-export-dropdown', narration: 'The Interactive HTML export generates a standalone kanban board that works entirely offline. It includes four views: a Dashboard with statistics, a Tree view showing role hierarchy, a Graph view with interactive relationships, and a sortable Table view. No AEGIS installation required.', duration: 9000, navigate: 'roles' },
                        { target: '#btn-export-adjudication', narration: 'The PDF Report creates an AEGIS-branded document using the gold and bronze color scheme. It includes an executive summary of adjudication progress, role counts by status, and a detailed listing of all roles organized by category. Perfect for governance review meetings.', duration: 8000, navigate: 'roles' },
                        { target: '#roles-adjudication', narration: 'The Import Decisions option reads a JSON file exported from an interactive HTML board. This completes the offline collaboration workflow — share the HTML board, colleagues make decisions, export their changes as JSON, and import those decisions back into your AEGIS instance.', duration: 8500, navigate: 'roles' }
                    ]
                },
                adjudication_sharing: {
                    id: 'adjudication_sharing',
                    title: 'Sharing & Collaboration',
                    icon: 'share-2',
                    description: 'Shared folder, email packages, save and reset',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-adjudication')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-share-adjudication', narration: 'The Share button opens a dropdown with two sharing options. Export to Shared Folder saves your role data to a network location configured in Settings. Other AEGIS users can then import from the same shared folder to synchronize role dictionaries.', duration: 8500, navigate: 'roles' },
                        { target: '#adj-share-dropdown', narration: 'The Email Package option creates a dot-aegis-roles file that bundles all your adjudication data, dictionary entries, and function tags into a single portable file. Attach this to an email for colleagues who are not on the same network.', duration: 8000, navigate: 'roles' },
                        { target: '#btn-save-adjudication', narration: 'The Save button persists all adjudication decisions to the database immediately. AEGIS auto-saves periodically, but clicking Save gives you a confirmed checkpoint. The Reset button reverts all unsaved changes back to the last saved state.', duration: 7500, navigate: 'roles' },
                        { target: '#btn-reset-adjudication', narration: 'In Settings under the Sharing tab, you can configure the shared folder path, test the connection, and import role packages from other AEGIS users. Package imports show a preview diff of what will change before you commit.', duration: 7500, navigate: 'roles' }
                    ]
                },
                auto_adjudicate: {
                    id: 'auto_adjudicate',
                    title: 'Auto-Classify & Undo',
                    icon: 'zap',
                    description: 'One-click classification with full undo support',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-adjudication')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-auto-adjudicate', narration: 'The Auto-Classify button uses pattern matching and contextual analysis to suggest adjudication decisions for all pending roles at once. It identifies likely tools versus people roles, probable deliverables, and duplicates that should be merged.', duration: 8500, navigate: 'roles' },
                        { target: '#btn-bulk-confirm', narration: 'After auto-classification runs, roles are moved to their suggested status columns. You can review each suggestion and override any you disagree with. This dramatically speeds up the adjudication process for large role sets — hundreds of roles can be triaged in minutes.', duration: 8000, navigate: 'roles' },
                        { target: '#btn-undo-adj', narration: 'The Undo button reverts the last adjudication action — whether it was a single role decision or a bulk operation. Use keyboard shortcut Control-Z for speed. The Redo button or Control-Y reapplies a reverted action. The undo stack maintains full history for the current session.', duration: 8500, navigate: 'roles' },
                        { target: '#adj-select-all', narration: 'The Select All checkbox and bulk action buttons work together for batch operations. Check Select All, then click Bulk Confirm to verify all selected roles at once, Bulk Deliverable to mark them as deliverables, or Bulk Reject to dismiss them. The selection count indicator shows how many are selected.', duration: 8500, navigate: 'roles' }
                    ]
                },
                dictionary_imports: {
                    id: 'dictionary_imports',
                    title: 'Dictionary Imports',
                    icon: 'upload',
                    description: 'CSV, SIPOC, and package import wizards',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-dictionary')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-import-dictionary', narration: 'The Import button in the Dictionary toolbar opens a dropdown with multiple import options. CSV and Excel import accepts standard spreadsheet files with columns for role name, category, description, and other fields. A mapping wizard helps align your columns to AEGIS fields.', duration: 8500, navigate: 'roles' },
                        { target: '#btn-import-dictionary', narration: 'Before import commits, a preview modal shows a diff of what will change — new roles being added, existing roles being updated, and roles that remain unchanged. You can deselect specific roles from the import and only bring in the ones you want.', duration: 8000, navigate: 'roles' },
                        { target: '#dict-content-area', narration: 'SIPOC Import is a specialized five-step wizard for Nimbus-format Excel files. SIPOC stands for Suppliers, Inputs, Process, Outputs, and Customers. The wizard auto-detects whether your file uses hierarchy mode or process flow mode, with automatic fallback between the two.', duration: 9000, navigate: 'roles' },
                        { target: '#dict-search', narration: 'During CSV import, the wizard maps your spreadsheet columns to AEGIS role fields. The preview shows a role list with new, updated, and unchanged indicators. Select which roles to include and click Import to commit the changes to your dictionary.', duration: 8000, navigate: 'roles' },
                        { target: '#btn-import-dictionary', narration: 'Package Import reads dot-aegis-roles files created by the Share workflow. When importing a package from another AEGIS user, the system compares versions and warns if the package was created by a newer version of AEGIS that may have additional data fields.', duration: 8000, navigate: 'roles' }
                    ]
                },
                dictionary_exports: {
                    id: 'dictionary_exports',
                    title: 'Dictionary Exports',
                    icon: 'download',
                    description: 'CSV, template, and Role Inheritance Map',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-dictionary')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-export-dictionary', narration: 'The Export CSV button downloads your entire role dictionary as a spreadsheet-compatible file. Every field is included — role name, category, description, adjudication status, function tags, hierarchy level, disposition, organization group, and aliases.', duration: 8000, navigate: 'roles' },
                        { target: '#btn-download-template', narration: 'Download Template creates a blank CSV file with all the correct column headers and sample data rows. This template makes it easy for team members to prepare role data offline that can be imported later. Share this template at project kickoff.', duration: 7500, navigate: 'roles' },
                        { target: '#btn-export-hierarchy', narration: 'The Export Role Inheritance Map button generates an interactive standalone HTML file showing role relationships as a hierarchy. The exported file contains four views: a statistics Dashboard, a collapsible Tree view, an interactive Graph visualization, and a sortable data Table.', duration: 8500, navigate: 'roles' },
                        { target: '#btn-export-hierarchy', narration: 'The Hierarchy Map export supports inline editing — open the HTML file in any browser, modify role fields directly, and export your changes as a JSON diff file. Drop that JSON into the AEGIS updates folder, and Settings will auto-detect and offer to import it.', duration: 8500, navigate: 'roles' },
                        { target: '#btn-export-dictionary', narration: 'Seed Dictionary adds built-in organizational roles from common aerospace and engineering frameworks. This jumpstarts your dictionary with standard roles like Program Manager, Systems Engineer, Quality Assurance Lead, and Safety Officer with pre-populated descriptions and categories.', duration: 8000, navigate: 'roles' }
                    ]
                },
                function_tags: {
                    id: 'function_tags',
                    title: 'Function Tags & Reports',
                    icon: 'tags',
                    description: 'Tag management and three report types',
                    preAction: async () => {
                        try {
                            // v5.9.15: Click Overview tab where function tag buttons live
                            document.querySelector('#tab-overview')?.click();
                            await AEGISGuide._wait(400);
                            // Open the function tags modal so scenes target actual content
                            if (window.TWR?.FunctionTags?.showModal) {
                                window.TWR.FunctionTags.showModal();
                                await AEGISGuide._wait(500);
                            } else {
                                // Fallback: click the button directly
                                document.querySelector('#btn-function-tags')?.click();
                                await AEGISGuide._wait(500);
                            }
                            AEGISGuide._funcTagsCleanup = () => {
                                const ftModal = document.getElementById('function-tags-modal');
                                if (ftModal) { ftModal.remove(); }
                            };
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#function-tags-modal', narration: 'Function Tags categorize roles into organizational departments and functional areas. The tag management modal displays all categories in a hierarchical tree. The tag system uses three levels: parent categories like Engineering, child categories like Systems Engineering, and grandchild specializations.', duration: 9000, navigate: 'roles' },
                        { target: '#function-categories-list', narration: 'The category tree shows each tag with its code, name, and color indicator. Expand any parent category to reveal its children. Each category displays a stat pill showing how many roles and documents are tagged with it. Changes propagate immediately to all role displays throughout AEGIS.', duration: 8000, navigate: 'roles' },
                        { target: '#function-tags-modal', narration: 'Use the Add Category button to create new function tags. Each category has a code, name, color, and optional parent category. Edit and delete buttons appear on each category row. The hierarchy is fully customizable to match your organizational structure.', duration: 8000, navigate: 'roles' },
                        { target: '#function-tags-modal', narration: 'The Generate Reports feature offers three report types. Roles by Function groups all roles by their tags. Documents by Function shows which roles appear in each scanned document. Documents by Owner inverts the view — starting from each role, listing responsibilities and documents.', duration: 8500, navigate: 'roles' },
                        { target: '#function-tags-modal', narration: 'When editing a role in the Dictionary, you can assign function tags from a dropdown that shows all available categories with their color indicators. Each role can have multiple function tags, reflecting that many organizational roles span multiple functional areas.', duration: 7500, navigate: 'roles' }
                    ]
                },
                graph_controls: {
                    id: 'graph_controls',
                    title: 'Graph Controls & Layout',
                    icon: 'settings',
                    description: 'Layout options, filters, and info panel',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-graph')?.click();
                            await AEGISGuide._wait(1500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#graph-max-nodes', narration: 'The Graph view toolbar offers several controls to customize the visualization. The Max Nodes dropdown limits how many roles appear — useful when your database has hundreds of roles and you want to focus on the most connected ones.', duration: 7500, navigate: 'roles' },
                        { target: '#graph-layout', narration: 'The Layout selector switches between force-directed, hierarchical, and circular arrangements. Force-directed naturally clusters related roles. Hierarchical shows reporting chains. Circular places all nodes evenly around a ring, useful for seeing connection density.', duration: 8500, navigate: 'roles' },
                        { target: '#graph-labels', narration: 'The Labels dropdown controls what text appears on nodes: role name, category, document count, or none. Reducing label clutter helps when viewing the big picture of organizational relationships.', duration: 7000, navigate: 'roles' },
                        { target: '#graph-weight-filter', narration: 'The Weight Filter slider adjusts the minimum relationship strength shown. Moving it right hides weak connections, revealing only the strongest role relationships. This is excellent for identifying core organizational dependencies.', duration: 7500, navigate: 'roles' },
                        { target: '#graph-info-panel', narration: 'Click any node to select it and open the Info Panel on the right. The panel shows the selected role details, its connections, mention count, and source documents. The Clear Selection and Reset View buttons restore the default state. Refresh reloads the graph data.', duration: 8500, navigate: 'roles' }
                    ]
                },
                edit_role: {
                    id: 'edit_role',
                    title: 'Role Editing',
                    icon: 'edit',
                    description: 'Full role editing with tags and metadata',
                    preAction: async () => {
                        try {
                            document.querySelector('#tab-dictionary')?.click();
                            await AEGISGuide._wait(500);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#dict-content-area', narration: 'Click any role name in the Dictionary to open the Edit Role modal. This full-screen editor provides complete control over every role field: name, description, category, role type, disposition, organization group, hierarchy level, aliases, and whether the role is baselined.', duration: 8500, navigate: 'roles' },
                        { target: '#dict-filter-category', narration: 'The Category dropdown offers all your defined categories with color indicators. Changing the category updates the role badge color throughout the entire application — in the Overview, Graph, RACI Matrix, and all exports.', duration: 7500, navigate: 'roles' },
                        { target: '#btn-function-tags', narration: 'Function Tags are managed in the edit modal via a dropdown selector and an Add button. Each role can have multiple function tags. Tags appear as colored chips below the dropdown, with an X button to remove any tag. These tags power the function category reports.', duration: 8000, navigate: 'roles' },
                        { target: '#dict-content-area', narration: 'The Save button validates all fields and persists changes to the database immediately. If a similar role name or alias already exists, a duplicate detection warning appears. Cancel discards changes and returns to the Dictionary view. All saved changes are reflected instantly across every Roles Studio tab.', duration: 8000, navigate: 'roles' }
                    ]
                }
            }
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
                    narration: 'Statement Forge is your requirements extraction and management tool. It intelligently identifies and extracts shall, must, should, will, and may statements from technical documents. Open Statement Forge from the sidebar or click its tile on the dashboard.',
                    duration: 8000
                },
                {
                    target: '#btn-sf-extract',
                    narration: 'After loading a document, click Extract to begin the statement extraction process. AEGIS uses a sophisticated multi-pass pipeline to identify requirement statements. It detects the directive verb, determines the responsible role, classifies the statement level — system, subsystem, or component — and maps it to its source section and paragraph.',
                    duration: 10000,
                    navigate: 'forge'
                },
                {
                    target: '.sf-sidebar',
                    narration: 'The sidebar shows two document modes. Requirements mode looks for formal shall and must statements typical of specifications and standards. Work Instructions mode targets procedural language with should, will, and process-oriented phrasing. AEGIS auto-detects the mode based on your document content, but you can override it manually.',
                    duration: 9000,
                    navigate: 'forge'
                },
                {
                    target: '#sf-search-input',
                    narration: 'Use the search bar to instantly filter statements by any keyword. The search works across statement text, section headings, role names, and notes. Results update as you type with debounced performance for smooth interaction even with thousands of statements.',
                    duration: 7500,
                    navigate: 'forge'
                },
                {
                    target: '#sf-statements-table',
                    narration: 'The filter chips below the search bar let you show only specific directive types. Click "Shall" to see only shall-statements, or combine multiple filters. The statistics cards above show your total count, filtered count, section count, and how many statements you have selected.',
                    duration: 8000,
                    navigate: 'forge'
                },
                {
                    target: '#sf-btn-undo',
                    narration: 'Click any statement to expand its full details — the complete source text, the section heading it came from, the paragraph number, the extracted role, and the directive classification. You can edit any field inline. Changes are tracked with full undo and redo support using Control-Z and Control-Y.',
                    duration: 8500,
                    navigate: 'forge'
                },
                {
                    target: '#sf-select-all',
                    narration: 'Select multiple statements using the checkboxes for bulk operations. You can batch-update the directive type or responsible role across all selected statements at once. The Select All button and keyboard shortcut make it easy to work with large statement sets efficiently.',
                    duration: 8000,
                    navigate: 'forge'
                },
                {
                    target: '#sf-btn-export',
                    narration: 'Export your extracted statements in four formats: CSV for spreadsheet analysis and requirements traceability matrices, Word document for formal documentation packages, JSON for integration with requirements management tools like DOORS or Jama, and a formatted report view. Statement Forge also has a full history system — you can view statements from previous scans, compare extractions between document versions, and track how requirements evolve over time.',
                    duration: 10000,
                    navigate: 'forge'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                extraction: {
                    id: 'extraction',
                    title: 'Extraction Pipeline',
                    icon: 'scissors',
                    description: 'How statements are extracted and classified',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#btn-sf-extract', narration: 'The extraction pipeline uses a multi-pass approach. First, AEGIS identifies all sentences containing directive verbs — shall, must, should, will, and may. Then it analyzes the grammatical context to extract the responsible role and the action being required.', duration: 8500, navigate: 'forge' },
                        { target: '.sf-sidebar', narration: 'Two document modes drive the extraction. Requirements mode targets formal shall and must statements found in specifications, standards, and interface documents. Work Instructions mode captures procedural should, will, and process-oriented language.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-statements-table', narration: 'AEGIS auto-detects the document mode based on the frequency of directive verbs. Documents with predominantly shall statements are classified as Requirements. Documents with mostly should or will are classified as Work Instructions. You can override the auto-detection manually.', duration: 8500, navigate: 'forge' },
                        { target: '#sf-search-input', narration: 'Each extracted statement receives metadata: the directive verb type, the identified role, the requirement level — system, subsystem, or component — the source section heading, and the paragraph number. This metadata enables rich filtering and traceability.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-btn-export', narration: 'The extraction also identifies the statement context — the surrounding paragraph text that provides additional meaning. This context is stored alongside the statement for reference when reviewing or exporting requirements.', duration: 7000, navigate: 'forge' }
                    ]
                },
                search_filtering: {
                    id: 'search_filtering',
                    title: 'Search & Filtering',
                    icon: 'search',
                    description: 'Find and filter statements by any criteria',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#sf-search-input', narration: 'The search bar provides instant full-text search across all extracted statements. Type any keyword and results filter in real time. The search covers statement text, section headings, role names, notes, and directive types.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-statements-table', narration: 'Filter chips below the search bar provide one-click filtering by directive type. Click Shall to see only shall-statements. Click Must to see must-statements. You can activate multiple chips simultaneously to show several directive types together.', duration: 7500, navigate: 'forge' },
                        { target: '.sf-sidebar', narration: 'The statistics cards above show dynamic counts: Total Statements, Filtered Count (matching current filters), Sections (unique headings), and Selected (checkmarked statements). These numbers update instantly as you change filters.', duration: 7000, navigate: 'forge' },
                        { target: '#sf-btn-history', narration: 'Search supports cross-scan capability — you can search across statements from all previously scanned documents, not just the current one. This makes it easy to find related requirements across your entire document portfolio.', duration: 7500, navigate: 'forge' }
                    ]
                },
                inline_editing: {
                    id: 'inline_editing',
                    title: 'Editing & Bulk Ops',
                    icon: 'edit',
                    description: 'Inline editing, selections, and batch updates',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#sf-edit-panel', narration: 'Click any statement row to expand the edit panel on the right side. Every field is editable — the statement number, title, description text, directive type, and responsible role. Click a field to enter inline edit mode, make changes, and click Save to apply.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-btn-undo', narration: 'Changes are tracked with full undo and redo support. Press Control-Z or click the Undo button to revert the last edit. Control-Y or the Redo button restores it. The undo and redo counters in the toolbar show how many operations are available in each direction.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-select-all', narration: 'Use checkboxes to select multiple statements for bulk operations. The Select All checkbox selects every visible statement matching your current filters. With selections active, you can batch-update the directive type or responsible role across all selected items.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-btn-expand-all', narration: 'The Expand All and Collapse All buttons control the visibility of all statement detail panels at once. This is useful when you want to scan through complete statement text without clicking each one individually.', duration: 7000, navigate: 'forge' }
                    ]
                },
                history_overview: {
                    id: 'history_overview',
                    title: 'Statement History',
                    icon: 'clock',
                    description: 'View statement extractions across scans',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#sf-btn-history', narration: 'Statement Forge maintains a complete history of every extraction. Click the History button in the toolbar to open the Statement History viewer. It shows all previous scan sessions with their document name, scan date, statement count, and directive distribution.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-statements-table', narration: 'Click any history entry to load that extraction into the main statements table. You can compare statements between different scans of the same document to see how requirements have changed over time — additions, removals, and modifications.', duration: 8000, navigate: 'forge' },
                        { target: '.sf-sidebar', narration: 'The sidebar statistics update to show the loaded extraction data — total statements, filtered count, sections, and selected items. This helps you track your requirements extraction activity over time.', duration: 7000, navigate: 'forge' }
                    ]
                },
                document_viewer: {
                    id: 'document_viewer',
                    title: 'Document Viewer',
                    icon: 'file-text',
                    description: 'View source document with highlighted statements',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#sf-btn-view-source', narration: 'The Document Viewer provides a split-panel interface. Click the View Source button to open it. The left panel shows the full source document text with extracted statements highlighted in color. The right panel shows the selected statement details.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-statements-table', narration: 'Click any highlighted statement in the document to select it. The right panel updates with that statement metadata, directive type, role, and context. Conversely, clicking a statement in the table scrolls the document viewer to its location.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-btn-add', narration: 'The Highlight-to-Create feature lets you select text directly in the document viewer to create a new statement. The selected text auto-fills the Add Statement form with the directive type auto-detected from the text content.', duration: 7500, navigate: 'forge' },
                        { target: '#modal-statement-forge', narration: 'For PDF documents, the viewer uses a canvas-based renderer. For Word documents, AEGIS renders the semantic HTML generated by the Mammoth extraction library. Both formats support full statement highlighting and interactive navigation.', duration: 7500, navigate: 'forge' }
                    ]
                },
                compare_viewer: {
                    id: 'compare_viewer',
                    title: 'Compare Viewer',
                    icon: 'diff',
                    description: 'Diff statements between document versions',
                    preAction: async () => {
                        document.querySelector('#btn-statement-forge')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#sf-btn-history', narration: 'The Compare Viewer lets you diff requirement statements between two scans of the same document. Open Statement History, select two scans, and click Compare. AEGIS shows what changed — added statements, removed statements, and modified statements.', duration: 8500, navigate: 'forge' },
                        { target: '#sf-statements-table', narration: 'The unified view uses color coding: green for added statements, red for removed, yellow for modified, and gray for unchanged. A two-tier fingerprinting system detects modifications — description-only changes versus directive or role changes.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-edit-panel', narration: 'Modified statements show field-level diffs — you can see exactly which fields changed between versions: the directive verb, the responsible role, or the statement text itself. Old values appear with strikethrough, new values appear highlighted.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-search-input', narration: 'Filter chips let you show only specific diff types — click Added to see only new requirements, or Removed to focus on deleted ones. Combine with directive filters to show, for example, only new shall-statements added in the latest revision.', duration: 7500, navigate: 'forge' }
                    ]
                },
                // v5.9.10: Statement Forge advanced operations and SOW
                forge_sub_modals: {
                    id: 'forge_sub_modals',
                    title: 'Advanced Operations',
                    icon: 'layers',
                    description: 'Add, renumber, merge, split, and role mapping',
                    preAction: async () => {
                        try {
                            document.querySelector('#btn-statement-forge')?.click();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#sf-btn-add', narration: 'Statement Forge includes several advanced operations accessed through toolbar buttons. The Add Statement button opens a modal where you manually create a new requirement statement — entering the text, selecting a directive verb, assigning a responsible role, and setting a requirement ID.', duration: 8500, navigate: 'forge' },
                        { target: '#sf-btn-renumber', narration: 'The Renumber operation reassigns requirement IDs to your selected statements. This is essential when statements are reordered, split, or merged. You choose a starting number and prefix, and AEGIS sequentially numbers the selected items.', duration: 7500, navigate: 'forge' },
                        { target: '#sf-btn-merge', narration: 'Merge combines two or more selected statements into a single consolidated requirement. This is useful when the extractor split a compound requirement into fragments. The merged statement inherits the highest priority directive and combines the text.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-btn-split', narration: 'Split takes a single statement and breaks it into multiple individual requirements. This is common when a paragraph contains multiple shall-statements that should be tracked separately. AEGIS suggests split points based on directive verb detection.', duration: 8000, navigate: 'forge' },
                        { target: '#sf-btn-add', narration: 'Role Mapping opens a modal that lets you assign responsible roles to multiple statements at once. Select the statements, choose a role from the dropdown populated from your Roles Studio dictionary, and apply. This batch assignment powers the RACI matrix integration.', duration: 8000, navigate: 'forge' }
                    ]
                },
                // SOW Generator has been moved to its own guide section (v5.9.16)
                // See sections.sow for the full SOW Generator demo content
            }
        },

        // ─── SOW Generator ─────────────────────────────────────────────
        sow: {
            id: 'sow',
            title: 'SOW Generator',
            icon: 'file-output',
            whatIsThis: 'Generate professional Statement of Work documents from your extracted requirements. Configure document metadata, select directive types, choose formatting templates, and optionally upload a company template that gets populated automatically. The output includes title pages, numbered requirements, role annotations, and compliance matrices.',
            keyActions: [
                { icon: 'file-text', text: 'Configure SOW title, document number, version, and effective date' },
                { icon: 'check-square', text: 'Select which directive types to include (shall, must, should, will, may)' },
                { icon: 'upload', text: 'Upload a company template to auto-populate with extracted statements' },
                { icon: 'download', text: 'Generate and download the formatted SOW document' }
            ],
            proTips: [
                'Extract statements in Statement Forge first, then open the SOW Generator to create the document',
                'Use the directive type checkboxes to include only formal shall-statements for contractual SOWs',
                'The generated output includes section headers, requirement numbering, and source traceability',
                'Upload your company template to maintain consistent branding and formatting'
            ],
            tourSteps: [
                {
                    target: '#modal-sow-generator',
                    title: 'SOW Generator',
                    description: 'Configure and generate formatted Statement of Work documents from your extracted requirements.',
                    position: 'center'
                }
            ],
            demoScenes: [
                {
                    target: '#modal-sow-generator',
                    narration: 'The Statement of Work Generator creates professional SOW documents from your extracted requirements. It opens as a standalone modal where you configure the document metadata and formatting options before generating the output.',
                    duration: 8000,
                    navigate: 'sow'
                },
                {
                    target: '#sow-title',
                    narration: 'Start by setting the SOW title, document number, version, and effective date. These fields populate the title page and running headers of the generated document. Default values are auto-filled based on your loaded document.',
                    duration: 8000,
                    navigate: 'sow'
                },
                {
                    target: '#sow-doc-number',
                    narration: 'Select which directive types to include using the checkboxes. For formal contractual SOWs, include only shall-statements. For broader scope documents, add should and will directives. Style presets control the formatting template.',
                    duration: 8500,
                    navigate: 'sow'
                },
                {
                    target: '#sow-btn-generate',
                    narration: 'Click Generate to create the SOW as a downloadable Word document. The output includes a title page, scope section, requirements section with auto-numbered statements, responsible role annotations in brackets, and a compliance matrix mapping each statement to its source.',
                    duration: 9000,
                    navigate: 'sow'
                },
                {
                    target: '#modal-sow-generator',
                    narration: 'The generated document uses professional formatting with section headers, requirement IDs, directive verb highlighting, and source traceability back to the original document paragraph. This saves hours of manual document assembly for technical writers.',
                    duration: 8500,
                    navigate: 'sow',
                    preAction: async () => { if (typeof DemoSimulator !== 'undefined') DemoSimulator.showSowOutputPreview(); await AEGISGuide._wait(300); }
                }
            ],
            subDemos: {
                document_config: {
                    id: 'document_config',
                    title: 'Document Configuration',
                    icon: 'settings',
                    description: 'Title, number, version, and metadata fields',
                    preAction: async () => {
                        try {
                            if (window.SowGenerator?.open) window.SowGenerator.open();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#sow-title', narration: 'The SOW title field sets the main document heading that appears on the title page and in document headers. Enter a descriptive title like "Statement of Work for Flight Control Software Verification and Validation."', duration: 8000, navigate: 'sow' },
                        { target: '#sow-doc-number', narration: 'The document number follows your organization\'s numbering convention. This field appears in the header and is used for traceability. The version field tracks document revisions.', duration: 7500, navigate: 'sow' },
                        { target: '#sow-version', narration: 'The effective date sets when this SOW becomes active. All metadata fields carry through to the generated document headers, title page, and compliance matrix footnotes.', duration: 7000, navigate: 'sow' },
                        { target: '#sow-btn-generate', narration: 'Once all fields are configured, the Generate button creates the formatted output. A progress indicator shows generation status. The completed document downloads automatically as a Word file.', duration: 7500, navigate: 'sow' }
                    ]
                },
                output_preview: {
                    id: 'output_preview',
                    title: 'Output Preview',
                    icon: 'eye',
                    description: 'Preview and download the generated SOW',
                    preAction: async () => {
                        try {
                            if (window.SowGenerator?.open) window.SowGenerator.open();
                            await AEGISGuide._wait(600);
                            if (typeof DemoSimulator !== 'undefined') DemoSimulator.showSowOutputPreview();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-sow-generator', narration: 'Here is a preview of the generated SOW output. The document starts with a professional title page showing the document title, number, version, and effective date in your configured formatting style.', duration: 8000, navigate: 'sow' },
                        { target: '#modal-sow-generator', narration: 'The requirements section lists each extracted statement with automatic numbering. Directive verbs are highlighted — shall in bold, must underlined. The responsible role appears in brackets after each statement for clear accountability.', duration: 8500, navigate: 'sow' },
                        { target: '#modal-sow-generator', narration: 'Source traceability is built in. Each requirement maps back to its original document, section heading, and paragraph number. The compliance matrix at the end provides a cross-reference table for verification and validation activities.', duration: 8500, navigate: 'sow' }
                    ]
                },
                template_upload: {
                    id: 'template_upload',
                    title: 'Company Template',
                    icon: 'upload',
                    description: 'Upload company template for auto-population',
                    preAction: async () => {
                        try {
                            if (window.SowGenerator?.open) window.SowGenerator.open();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-sow-generator', narration: 'The Template Upload feature lets you provide your company\'s SOW template as a Word document. AEGIS identifies placeholder fields in the template and automatically populates them with your extracted requirements.', duration: 8500, navigate: 'sow' },
                        { target: '#modal-sow-generator', narration: 'Supported placeholders include curly-brace markers like title, document number, version, date, and requirements. AEGIS scans the template for these markers and replaces them with the corresponding data from your configuration and extracted statements.', duration: 8500, navigate: 'sow' },
                        { target: '#modal-sow-generator', narration: 'This approach lets you maintain consistent branding, headers, footers, and formatting across all SOW documents your organization produces. The template only needs to be uploaded once — AEGIS remembers it for future sessions.', duration: 8000, navigate: 'sow' }
                    ]
                }
            }
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
                    narration: 'The Hyperlink Validator ensures every URL in your documents is live, accessible, and pointing to the right destination. In regulated industries, broken links in controlled documents can be audit findings. AEGIS catches them before reviewers do.',
                    duration: 8000
                },
                {
                    target: '#hv-mode',
                    narration: 'Start by choosing your validation mode. Offline mode extracts all links from your document without making any network requests — useful for cataloging URLs on air-gapped systems. Validator mode actively tests each URL by sending HTTP requests and checking responses.',
                    duration: 8500,
                    navigate: 'validator'
                },
                {
                    target: '#hv-scan-depth',
                    narration: 'Configure the scan depth here. Quick mode sends a lightweight HEAD request for fast checking. Standard mode follows redirects and checks final destinations. Thorough mode downloads full pages and verifies content is actually present. Choose based on your speed versus thoroughness needs.',
                    duration: 8500,
                    navigate: 'validator'
                },
                {
                    target: '#hv-btn-validate',
                    narration: 'Click Validate to begin checking. Results update in real-time with animated status indicators. Each URL receives a status: Working in green, Redirect in blue, Broken in red, Timeout in orange, Blocked in purple, DNS Failed, SSL Error, or Authentication Required. Summary statistics update live as results come in.',
                    duration: 9000,
                    navigate: 'validator'
                },
                {
                    target: '#hv-stats-grid',
                    narration: 'The results table is fully interactive. Click any column header to sort. Click a status badge to filter results by that status type. The domain filter dropdown lets you focus on links from a specific website. And the clickable summary stat cards at the top let you jump to just the broken links or just the redirects with a single click.',
                    duration: 9000,
                    navigate: 'validator'
                },
                {
                    target: '#hv-results-table',
                    narration: 'For URLs that are blocked by firewalls or require authentication, the Deep Validate feature uses a headless browser to retry them. It simulates a real Chrome browser with JavaScript execution, cookie handling, and stealth techniques to get past bot-detection systems. This recovers many links that simple HTTP requests cannot reach.',
                    duration: 9000,
                    navigate: 'validator'
                },
                {
                    target: '#hv-filter-domain',
                    narration: 'You can add exclusion rules for known-good internal URLs that do not need checking. Right-click any result to exclude it by URL or by domain pattern. Exclusions persist across sessions. The Link History sidebar tracks all previously validated URLs so you can see validation trends over time. Export your results as a detailed report for compliance documentation.',
                    duration: 9500,
                    navigate: 'validator'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                upload_paste: {
                    id: 'upload_paste',
                    title: 'Upload & Paste',
                    icon: 'upload',
                    description: 'Load URLs from documents or paste them directly',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-mode', narration: 'The Hyperlink Validator accepts URLs from two sources. Upload a Word or PDF document and AEGIS automatically extracts every embedded hyperlink. Or switch to the paste tab and enter URLs manually, one per line.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-tab-upload', narration: 'When uploading a document, AEGIS extracts not just visible hyperlinks but also links embedded in bookmarks, cross-references, and table of contents entries. For Excel files, it finds URLs in cell values and hyperlink formulas.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-url-input', narration: 'The paste input accepts any URL format — with or without the http prefix. AEGIS normalizes URLs, removes duplicates, and validates the format before scanning. You can paste hundreds of URLs at once for bulk validation.', duration: 7000, navigate: 'validator' },
                        { target: '#hv-btn-validate', narration: 'After loading, a summary shows the total link count and a preview of the first several URLs. Review this before clicking Validate to confirm the correct document was processed.', duration: 6500, navigate: 'validator' }
                    ]
                },
                modes_settings: {
                    id: 'modes_settings',
                    title: 'Modes & Settings',
                    icon: 'settings',
                    description: 'Validation mode, scan depth, and network options',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-mode', narration: 'Two validation modes are available. Offline mode extracts and catalogs all links without sending any network requests. This is useful for air-gapped environments or when you just need a link inventory. Validator mode actively tests every URL.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-scan-depth', narration: 'Scan depth controls how thoroughly each URL is tested. Quick mode sends a lightweight HEAD request — fast but may miss content issues. Standard follows redirects to the final destination. Thorough downloads the full page and verifies content is present.', duration: 8500, navigate: 'validator' },
                        { target: '#hv-timeout', narration: 'Network settings let you configure the request timeout in seconds, the number of retries for failed requests, and whether to verify SSL certificates. Disabling SSL verification helps test internal servers with self-signed certificates.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-settings', narration: 'The Windows SSO option enables integrated authentication for corporate intranet links. When enabled, AEGIS passes Windows credentials with each request, allowing it to validate links behind corporate single sign-on systems.', duration: 7500, navigate: 'validator' }
                    ]
                },
                results_filtering_hv: {
                    id: 'results_filtering_hv',
                    title: 'Results & Filtering',
                    icon: 'filter',
                    description: 'Results table, status filtering, and domain filter',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-results-table', narration: 'The results table shows every validated URL with its status, HTTP response code, response time, and the source location in the document. Status indicators use color coding — green for working, red for broken, blue for redirect, orange for timeout, and purple for blocked.', duration: 8500, navigate: 'validator' },
                        { target: '#hv-stats-grid', narration: 'Summary stat cards at the top show counts for each status category. These cards are clickable — click the Broken card to filter the table to show only broken links. A gold active indicator shows which filter is currently applied.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-filter-domain', narration: 'The domain filter dropdown provides a searchable list of all unique domains found in your results. Select a domain to show only links from that specific website. A clear button removes the domain filter.', duration: 7000, navigate: 'validator' },
                        { target: '#hv-filter-status', narration: 'Click any status badge in a result row to filter by that specific status type. The status filter dropdown provides the same filtering. Column headers are sortable — click to sort by URL, status, response code, or response time.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-filter-search', narration: 'The URL search input lets you find specific links by typing any part of the URL. Combined with status and domain filters, you can zero in on problem links efficiently. The table also shows source context — cell address in Excel or paragraph location in Word.', duration: 7000, navigate: 'validator' }
                    ]
                },
                deep_validate: {
                    id: 'deep_validate',
                    title: 'Deep Validate',
                    icon: 'scan-search',
                    description: 'Headless browser retry for blocked links',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-rescan-section', narration: 'Deep Validate is a headless browser feature that retries links that failed during the initial scan. It targets URLs with specific failure statuses: blocked, timeout, DNS failed, authentication required, and SSL error.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-btn-rescan', narration: 'The headless browser uses Playwright to launch a real Chrome instance with JavaScript execution, cookie handling, and stealth techniques. It simulates a human browsing experience, which bypasses bot detection systems that block simple HTTP requests.', duration: 8500, navigate: 'validator' },
                        { target: '#hv-blocked-count', narration: 'After the initial scan completes, a purple Deep Validate button appears if any eligible links were found. The count shows how many links can be retried. Click to start the headless browser scan with progress updates.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-results-table', narration: 'Recovered links are merged back into the main results table with their status updated. The summary statistics refresh to reflect the new results. Links that are truly broken remain flagged even after Deep Validate retries.', duration: 7000, navigate: 'validator' }
                    ]
                },
                domain_analytics: {
                    id: 'domain_analytics',
                    title: 'Domain Analytics',
                    icon: 'globe',
                    description: 'Per-domain breakdown and health scoring',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-domain-carousel-section', narration: 'Domain analytics groups your validation results by website. The domain carousel shows each domain as a card with its total link count, working count, broken count, and an overall health percentage. This helps identify websites that are consistently problematic.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-domain-heatmap-section', narration: 'The domain heatmap provides a visual overview of link health across all domains. Domains are ranked from worst to best health. A domain with many broken links appears prominently, alerting you to potential issues with that website.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-filter-domain', narration: 'Click any domain card or use the domain filter dropdown to filter the main results table to show only links from that domain. This drill-down workflow helps you systematically address link issues one website at a time.', duration: 7000, navigate: 'validator' }
                    ]
                },
                exclusions: {
                    id: 'exclusions',
                    title: 'Exclusions',
                    icon: 'shield-off',
                    description: 'Exclude known-good URLs and domain patterns',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-settings', narration: 'Exclusion rules let you skip URLs that you know are valid but consistently fail automated checks. Open the settings panel to manage exclusions. Common examples include intranet sites, VPN-only resources, or dynamically generated URLs.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-btn-add-exclusion', narration: 'Click Add Exclusion Rule to create a new exclusion. You can also add exclusions by right-clicking any result row and selecting Exclude This URL or Exclude This Domain. URL exclusions match the exact URL. Domain exclusions match all URLs from that website.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-exclusions-list', narration: 'Exclusions are saved to the database and persist across sessions. They apply automatically to future scans. The exclusions list shows all active rules with their pattern, type, and reason. Remove any rule by clicking the delete button.', duration: 7000, navigate: 'validator' }
                    ]
                },
                link_history_export: {
                    id: 'link_history_export',
                    title: 'History & Export',
                    icon: 'history',
                    description: 'Link history tracking and result exports',
                    preAction: async () => {
                        document.querySelector('#nav-hyperlink-validator')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#hv-btn-show-history', narration: 'The Link History sidebar tracks all previously validated URLs across sessions. Click the Show History button to open the panel. Each entry shows the URL, last validation date, current status, and response time.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-history-panel', narration: 'Link History supports searching by URL or domain, and filtering by status. You can see the complete validation history for any specific URL — when it was first checked, how its status has changed, and the most recent result.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-btn-export-csv', narration: 'Export your validation results in multiple formats. CSV for spreadsheet analysis, JSON for programmatic integration, HTML report for stakeholder review, and highlighted DOCX with embedded comments. These reports are commonly used as evidence in document quality audits.', duration: 8000, navigate: 'validator' }
                    ]
                },
                // v5.9.10: Hyperlink Validator export formats deep-dive
                hv_export_formats: {
                    id: 'hv_export_formats',
                    title: 'Export Formats',
                    icon: 'download',
                    description: 'CSV, JSON, HTML report, and highlighted DOCX',
                    preAction: async () => {
                        try {
                            document.querySelector('#nav-hyperlink-validator')?.click();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#hv-btn-export-csv', narration: 'The Hyperlink Validator offers four export formats in the toolbar. CSV export creates a flat spreadsheet with columns for URL, status, response code, response time, source location in the document, and the cell address if from a spreadsheet.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-btn-export-json', narration: 'JSON export provides a structured data file with the full result metadata — including redirect chains, SSL certificate details, and validation timestamps. Use this for integration with automated quality pipelines or dashboards.', duration: 7500, navigate: 'validator' },
                        { target: '#hv-btn-export-html', narration: 'HTML Report generates a standalone interactive page with summary charts, status distribution, domain health rankings, and the full results table. This is the most popular format for sharing validation results with stakeholders who need a visual overview.', duration: 8000, navigate: 'validator' },
                        { target: '#hv-btn-export-highlighted', narration: 'Highlighted Export creates a copy of your source document — Word or Excel — with broken links highlighted in red and yellow. Each broken link gets a comment annotation with the failure reason, status code, and validation timestamp. The original document formatting is fully preserved.', duration: 9000, navigate: 'validator' },
                        { target: '#hv-btn-export-csv', narration: 'The Highlighted Export button is only enabled when a source document was uploaded for validation. If you pasted URLs manually, this option is disabled since there is no source file to annotate. All other formats work regardless of input method.', duration: 7500, navigate: 'validator' }
                    ]
                }
            }
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
                    narration: 'Document Compare is essential for version control in technical documentation. It lets you compare two scans of the same document — or even two different documents — side by side with color-coded difference highlighting. Click the Document Compare nav button or dashboard tile to open it.',
                    duration: 8500
                },
                {
                    target: '#dc-doc-select',
                    narration: 'When Document Compare opens, it automatically selects the oldest scan on the left and the newest scan on the right, then immediately runs the comparison. No manual button clicks required. You can also use the document selector dropdown at the top to switch to a different document without closing the modal.',
                    duration: 8500,
                    navigate: 'compare'
                },
                {
                    target: '#dc-stats',
                    narration: 'The comparison view highlights differences using intuitive color coding. Added content appears in green, removed content in red, and modified sections in yellow. AEGIS compares not just the raw text, but the structure — headings, paragraphs, tables, and lists are all tracked separately for precise difference detection.',
                    duration: 9000,
                    navigate: 'compare'
                },
                {
                    target: '#modal-doc-compare',
                    narration: 'For Statement Forge users, Document Compare integrates with your requirement extractions. It tracks which statements were added, removed, or modified between scans. You can filter the view to show only statement-level changes — perfect for tracking requirements evolution across document revisions.',
                    duration: 8500,
                    navigate: 'compare'
                },
                {
                    target: '#dc-old-scan',
                    narration: 'The comparison also shows quality score progression. See how the document grade changed between scans, which issue categories improved or regressed, and the net change in total findings. This gives you quantified evidence of document quality improvement over time.',
                    duration: 8000,
                    navigate: 'compare'
                },
                {
                    target: '#dc-btn-compare',
                    narration: 'Export your comparison as a CSV report with color-coded diff rows, or as a PDF with AEGIS branding suitable for formal review packages. The comparison data is invaluable for change control boards and document approval workflows.',
                    duration: 7500,
                    navigate: 'compare'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                document_selection: {
                    id: 'document_selection',
                    title: 'Document Selection',
                    icon: 'files',
                    description: 'Choosing documents and scans to compare',
                    preAction: async () => {
                        // v5.9.18: Use _navigateToSection to auto-open DocCompare with real document
                        await AEGISGuide._navigateToSection('compare');
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#dc-doc-select', narration: 'Document Compare opens with a document selector dropdown at the top. It lists all documents in your scan history that have multiple scans available. Select a document to see its available scan versions.', duration: 7500, navigate: 'compare' },
                        { target: '#dc-old-scan', narration: 'Two scan selectors appear below the document picker — one for the older scan on the left and one for the newer scan on the right. AEGIS auto-selects the oldest and newest scans by default for maximum diff coverage.', duration: 7500, navigate: 'compare' },
                        { target: '#dc-new-scan', narration: 'Each scan option shows the date, quality grade, and issue count. When you change the selection, the comparison runs automatically — no manual compare button needed. Results appear instantly for most documents.', duration: 7000, navigate: 'compare' },
                        { target: '#dc-btn-compare', narration: 'You can switch documents without closing the modal. The document dropdown repopulates the scan selectors and re-runs the comparison. This makes it easy to review changes across your entire document portfolio.', duration: 7000, navigate: 'compare' }
                    ]
                },
                diff_views: {
                    id: 'diff_views',
                    title: 'Diff Views',
                    icon: 'columns-2',
                    description: 'Visual comparison and color-coded changes',
                    preAction: async () => {
                        await AEGISGuide._navigateToSection('compare');
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#dc-stats', narration: 'The comparison view uses intuitive color coding for changes. Green highlighting marks content that was added in the newer scan. Red marks content that was removed. Yellow indicates modified sections where the text changed but the issue category remained.', duration: 8000, navigate: 'compare' },
                        { target: '#dc-stats', narration: 'The summary bar at the top shows statistics — total issues in each scan, net change, and counts of added, removed, and modified findings. The quality score delta shows whether the document improved or regressed.', duration: 7500, navigate: 'compare' },
                        { target: '#modal-doc-compare', narration: 'Issues are listed in a unified view with change indicators next to each row. Unchanged issues appear in their normal style. Click any issue to expand its details and see the full context from both scan versions.', duration: 7500, navigate: 'compare' },
                        { target: '#dc-minimap', narration: 'For modified issues, the detail panel shows a field-by-field comparison — what changed in the severity, message, flagged text, or suggestion between the two scans.', duration: 7000, navigate: 'compare' }
                    ]
                },
                change_navigation: {
                    id: 'change_navigation',
                    title: 'Change Navigation',
                    icon: 'navigation',
                    description: 'Navigate between changes and filter by type',
                    preAction: async () => {
                        await AEGISGuide._navigateToSection('compare');
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#dc-stats', narration: 'Filter chips at the top let you show only specific change types. Click Added to see only new issues found in the newer scan. Click Removed to see issues that were fixed. Click Modified to see issues that changed.', duration: 7500, navigate: 'compare' },
                        { target: '#modal-doc-compare', narration: 'The change navigation buttons let you jump between changes — Next Change and Previous Change skip over unchanged items to quickly review all differences. Keyboard arrows also navigate between items.', duration: 7000, navigate: 'compare' },
                        { target: '#dc-minimap', narration: 'The comparison integrates with Statement Forge if statement extractions exist for both scans. You can filter to show only statement-level changes, tracking how requirements evolved between document revisions.', duration: 7500, navigate: 'compare' }
                    ]
                },
                compare_export: {
                    id: 'compare_export',
                    title: 'Comparison Export',
                    icon: 'download',
                    description: 'Export comparison results as CSV or PDF',
                    preAction: async () => {
                        await AEGISGuide._navigateToSection('compare');
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#dc-btn-compare', narration: 'Export your comparison as a CSV file with color-coded change indicators. The CSV includes both scan dates, all issues from both versions, their change status (added, removed, modified, unchanged), and detailed metadata.', duration: 7500, navigate: 'compare' },
                        { target: '#modal-doc-compare', narration: 'The PDF export generates an AEGIS-branded comparison report suitable for formal review packages. It includes an executive summary of changes, quality score progression, and detailed issue-level diffs with color coding.', duration: 7500, navigate: 'compare' },
                        { target: '#dc-doc-select', narration: 'Comparison data is particularly valuable for change control boards. The exported reports provide evidence of document quality improvements between revisions, supporting approval workflows and audit trails.', duration: 7000, navigate: 'compare' }
                    ]
                },
                // v5.9.10: Document switcher deep-dive
                compare_doc_switcher: {
                    id: 'compare_doc_switcher',
                    title: 'Document Switcher',
                    icon: 'repeat',
                    description: 'Switch documents and scan versions',
                    preAction: async () => {
                        await AEGISGuide._navigateToSection('compare');
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#dc-doc-select', narration: 'The Document Compare modal features a master document selector in the header. This dropdown lists every document in your scan history that has been scanned at least twice — since comparison requires two different scan versions of the same file.', duration: 8000, navigate: 'compare' },
                        { target: '#dc-old-scan', narration: 'When you switch documents, the scan version dropdowns automatically update to show all available scans for that file. The left dropdown selects the older scan version. AEGIS auto-selects the oldest scan here, then immediately runs the comparison.', duration: 8000, navigate: 'compare' },
                        { target: '#dc-new-scan', narration: 'The right dropdown selects the newer scan version. You can choose any two scans to compare — not just oldest and newest. This is useful when you want to see what changed between two specific revisions, such as before and after a particular review cycle.', duration: 7500, navigate: 'compare' },
                        { target: '#dc-btn-compare', narration: 'When opened from the Scan History table, the Compare button pre-selects the relevant document and scans. When opened from the navigation bar, it defaults to the most recently scanned multi-version document. Click Compare to re-run the comparison with different scan selections.', duration: 8000, navigate: 'compare' }
                    ]
                }
            }
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
                    narration: 'Metrics and Analytics is your comprehensive data intelligence dashboard. It aggregates quality data across every document you have ever scanned and presents it through interactive charts and visualizations. Think of it as your program-level quality command center.',
                    duration: 8000
                },
                {
                    target: '#ma-overview-hero',
                    narration: 'The Overview tab shows your high-level portfolio health. Hero statistics display total documents scanned, average quality score across all documents, total issues found, and scan activity trends. Below that, you will find a quality trend line chart tracking how your scores have changed over time, and a scan activity heatmap showing your review patterns.',
                    duration: 9500,
                    navigate: 'metrics'
                },
                {
                    target: '#severity-chart-card',
                    narration: 'The severity distribution chart reveals where your issues concentrate. A bar chart shows the breakdown across Critical, High, Medium, Low, and Info levels. The doughnut chart beside it shows the proportional split. Focus your improvement efforts on Critical and High severity issues first — they have the biggest impact on document quality.',
                    duration: 9000,
                    navigate: 'metrics'
                },
                {
                    target: '#category-chart-card',
                    narration: 'The category distribution chart shows which checker types find the most issues. If Grammar dominates, your authors may need writing training. If Standards Compliance is high, your templates may need updating. If Clarity issues are prevalent, sentences may be too complex. These patterns help you address systemic quality problems at their root cause.',
                    duration: 9500,
                    navigate: 'metrics'
                },
                {
                    target: '#ma-tab-btn-quality',
                    narration: 'The Quality tab dives deeper into score analysis. See the distribution of quality grades across your portfolio — how many documents scored A, B, C, D, or F. Track score trends over weeks and months. Identify your best and worst performing documents and the specific categories dragging down scores.',
                    duration: 8500,
                    navigate: 'metrics'
                },
                {
                    target: '#ma-tab-btn-roles',
                    narration: 'The Roles tab presents role analytics — total unique roles discovered, the most frequently mentioned roles, role distribution across documents, and function tag coverage statistics. This data powers organizational governance analysis and helps ensure role clarity across your documentation suite.',
                    duration: 8500,
                    navigate: 'metrics'
                },
                {
                    target: '#ma-tab-btn-documents',
                    narration: 'The Documents tab shows per-document analytics. See every scanned document with its grade history, issue breakdown, scan frequency, and word count trends. Sort by any column to find outliers. All charts in Metrics and Analytics are interactive — hover for exact values, and the data refreshes automatically after every new scan.',
                    duration: 9000,
                    navigate: 'metrics'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                overview_dashboard: {
                    id: 'overview_dashboard',
                    title: 'Overview Dashboard',
                    icon: 'layout-dashboard',
                    description: 'Hero stats, trends, and scan activity heatmap',
                    preAction: async () => {
                        document.querySelector('#ma-tab-btn-overview')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#ma-overview-hero', narration: 'The Overview tab is the main analytics dashboard. Hero stat cards at the top show key metrics — total documents scanned, average quality score, total issues found, and total roles discovered. Click any card to drill down into its data.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-chart-score-trend', narration: 'The quality trend line chart shows how your average document quality has changed over time. Data points represent individual scans. The trend line helps identify whether quality is improving, declining, or stable across your scanning activity.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-chart-grade-dist', narration: 'The score distribution doughnut chart shows how many documents fall into each grade bucket — A-plus through F. This gives you a quick visual of your overall portfolio quality. Hover over any segment to see the exact count and percentage.', duration: 7500, navigate: 'metrics' },
                        { target: '#severity-chart-card', narration: 'The severity breakdown shows the distribution of issues across Critical, High, Medium, Low, and Info categories. This helps prioritize your remediation efforts — focus on Critical and High severity findings first.', duration: 7000, navigate: 'metrics' },
                        { target: '#category-chart-card', narration: 'The scan activity heatmap uses a calendar-style grid to visualize your scanning frequency. Darker cells indicate more scans on that date. Hover over any cell to see the exact count and the documents reviewed that day.', duration: 7500, navigate: 'metrics' }
                    ]
                },
                quality_tab: {
                    id: 'quality_tab',
                    title: 'Quality Tab',
                    icon: 'award',
                    description: 'Score distribution, trends, and grade analysis',
                    preAction: async () => {
                        // v5.9.14: Use switchTab API directly (click() doesn't trigger IIFE event delegation)
                        if (window.MetricsAnalytics?.switchTab) window.MetricsAnalytics.switchTab('quality');
                        else document.querySelector('#ma-tab-btn-quality')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#ma-quality-hero', narration: 'The Quality tab provides deep analysis of document scores. The grade distribution chart shows a detailed breakdown of all quality grades with counts and percentages for each grade level from A-plus through F.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-score-dist', narration: 'The score trend chart tracks how individual documents improve over repeated scans. Each line represents a document, showing its quality grade at each scan point. This makes it easy to verify that your editing efforts are paying off.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-chart-issue-cats', narration: 'Category analysis shows which issue categories contribute most to score reductions. Common offenders like Grammar, Clarity, and Standards Compliance are ranked by total impact, helping you prioritize checker configuration.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-quality-docs-table', narration: 'Top and bottom performers sections highlight your best and worst documents. Best performers can serve as templates. Worst performers should be prioritized for remediation.', duration: 6500, navigate: 'metrics' }
                    ]
                },
                statements_tab: {
                    id: 'statements_tab',
                    title: 'Statements Tab',
                    icon: 'file-text',
                    description: 'Statement analytics and directive distribution',
                    preAction: async () => {
                        // v5.9.14: Use switchTab API directly
                        if (window.MetricsAnalytics?.switchTab) window.MetricsAnalytics.switchTab('statements');
                        else document.querySelector('#ma-tab-btn-statements')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#ma-chart-directive-dist', narration: 'The Statements tab analyzes extracted requirement statements across your entire portfolio. The directive distribution chart shows the proportion of shall, must, should, will, and may statements found in your documents.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-stmts-by-doc', narration: 'The statements-per-document chart shows how requirement density varies across your document portfolio. Documents with high statement density are typically formal specifications. Low density may indicate procedural or descriptive documents.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-chart-role-assign', narration: 'Trend data tracks how your total statement count grows over time as you scan more documents. This metric is useful for tracking the scope of your requirements database.', duration: 6500, navigate: 'metrics' }
                    ]
                },
                roles_analytics: {
                    id: 'roles_analytics',
                    title: 'Roles Analytics',
                    icon: 'users-round',
                    description: 'Role distribution and coverage analysis',
                    preAction: async () => {
                        // v5.9.14: Use switchTab API directly
                        if (window.MetricsAnalytics?.switchTab) window.MetricsAnalytics.switchTab('roles');
                        else document.querySelector('#ma-tab-btn-roles')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#ma-chart-adj-status', narration: 'The Roles tab presents analytics on organizational roles discovered across all your documents. The top roles chart shows the most frequently mentioned roles ranked by total mention count across all scans.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-role-cats', narration: 'Role distribution across documents shows which roles span many documents versus those confined to a single specification. Widely referenced roles are key organizational roles that need consistent governance.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-adj-status', narration: 'Function tag coverage shows what percentage of discovered roles have been tagged with departmental categories. Low coverage indicates roles that need attention in the Adjudication tab.', duration: 7000, navigate: 'metrics' },
                        { target: '#ma-chart-rel-types', narration: 'The adjudication status chart shows the breakdown of verified, pending, rejected, and merged roles. This tracks your progress toward complete role governance across your document portfolio.', duration: 7000, navigate: 'metrics' }
                    ]
                },
                documents_analytics: {
                    id: 'documents_analytics',
                    title: 'Documents Tab',
                    icon: 'file-bar-chart',
                    description: 'Per-document analytics and scan frequency',
                    preAction: async () => {
                        // v5.9.14: Use switchTab API directly
                        if (window.MetricsAnalytics?.switchTab) window.MetricsAnalytics.switchTab('documents');
                        else document.querySelector('#ma-tab-btn-documents')?.click();
                        await AEGISGuide._wait(400);
                    },
                    scenes: [
                        { target: '#ma-chart-word-dist', narration: 'The Documents tab shows analytics for each individual document in your scan history. Every document is listed with its current quality grade, total scans completed, last scan date, word count, and issue count.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-doc-cats', narration: 'The table is fully sortable — click any column header to sort by that metric. Sort by grade to find your weakest documents. Sort by scan count to find documents that have been reviewed most frequently.', duration: 7000, navigate: 'metrics' },
                        { target: '#ma-docs-portfolio-table', narration: 'Click any document row to see its grade history chart — a timeline of quality scores across all scans. This tells you whether repeated editing and rescanning has improved the document over time.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-doc-funcs', narration: 'Word count trends help identify document growth or reduction over time. Documents that are growing rapidly may need architectural review. Documents that are shrinking may have important content being removed.', duration: 7000, navigate: 'metrics' }
                    ]
                },
                // v5.9.10: Metrics deep-dive sub-demos
                chart_interactions: {
                    id: 'chart_interactions',
                    title: 'Chart Drill-Down',
                    icon: 'mouse-pointer-click',
                    description: 'Interactive charts with click-to-explore',
                    preAction: async () => {
                        try {
                            // v5.9.14: switchTab API ensures overview tab is active
                            if (window.MetricsAnalytics?.switchTab) window.MetricsAnalytics.switchTab('overview');
                            else document.querySelector('#ma-tab-btn-overview')?.click();
                            await AEGISGuide._wait(400);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#ma-overview-hero', narration: 'The Overview tab features hero stat cards at the top — Total Scans, Documents, Average Grade, and Total Issues. Each card is clickable. Click any stat to drill down into a detailed breakdown of that metric.', duration: 7500, navigate: 'metrics' },
                        { target: '#ma-chart-score-trend', narration: 'The Quality Trend line chart shows your average document grade over time. Hover over any data point to see the exact date, grade, and document count for that period. This reveals whether your organization quality is improving or declining.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-chart-grade-dist', narration: 'The Score Distribution doughnut chart breaks down grades across all scans. Click any slice to filter the view to only documents with that grade. Hover to see the percentage and count for each grade band from A-plus through F.', duration: 7500, navigate: 'metrics' },
                        { target: '#severity-chart-card', narration: 'The Severity Breakdown doughnut shows issue distribution by severity level. This helps you understand your quality profile — are most issues minor style suggestions, or do you have a high proportion of critical compliance failures?', duration: 7500, navigate: 'metrics' },
                        { target: '#category-chart-card', narration: 'The Scan Activity Heatmap uses a calendar grid to show when scans occurred. Darker cells indicate more scans on that date. Hover over any cell to see the exact date and scan count. This visualization reveals review patterns and cadence.', duration: 8000, navigate: 'metrics' }
                    ]
                },
                metrics_export: {
                    id: 'metrics_export',
                    title: 'Metrics & Insights',
                    icon: 'pie-chart',
                    description: 'Per-tab insights and analytics',
                    preAction: async () => {
                        // No additional tab switching needed — this sub-demo targets tab buttons themselves
                    },
                    scenes: [
                        { target: '#ma-tab-btn-quality', narration: 'The Quality tab provides deeper analysis of your document grades. It shows grade distribution as a bar chart, score trends per individual document, category-level analysis showing which checker groups find the most issues, and a top and bottom performers ranking.', duration: 8500, navigate: 'metrics' },
                        { target: '#ma-tab-btn-statements', narration: 'The Statements tab analyzes requirement extraction data. It shows the distribution of directive types — how many shall versus should versus must versus will statements exist across your repository. Statements-per-document charts reveal document complexity trends.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-tab-btn-roles', narration: 'The Roles tab provides organizational analytics. See the top roles by mention count across all documents, role distribution showing how roles spread across your document corpus, function tag coverage metrics, and the adjudication status breakdown.', duration: 8000, navigate: 'metrics' },
                        { target: '#ma-tab-btn-documents', narration: 'The Documents tab lists every scanned document with sortable columns for grade, scan count, issue count, word count, and last scanned date. Click any row for a grade history timeline. This is your single pane of glass for all document quality data.', duration: 8000, navigate: 'metrics' }
                    ]
                }
            }
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
                    narration: 'Scan History is your complete audit trail. Every document scan is automatically recorded with the date, time, filename, quality grade, issue count, word count, and statement count. Click Scan History in the navigation to open it.',
                    duration: 8000
                },
                {
                    target: '#scan-history-body',
                    narration: 'The history table shows all your scans in chronological order with sortable columns. The scan count column reveals how many times each document has been reviewed — documents scanned multiple times show quality progression over their revision history.',
                    duration: 8000,
                    navigate: 'history'
                },
                {
                    target: '#history-search',
                    narration: 'Use the search field to filter scan records by document name. Click any scan entry to instantly reload its complete review results. Every finding, statistic, and analysis from that scan is preserved exactly as it was — you can always go back without re-scanning.',
                    duration: 7500,
                    navigate: 'history'
                },
                {
                    target: '#modal-scan-history',
                    narration: 'The history system also feeds into Document Compare. When you open Compare, it pulls available scan pairs from your history database. This is how AEGIS tracks changes between document versions — by comparing the stored results from different scans.',
                    duration: 7500,
                    navigate: 'history'
                },
                {
                    target: '#scan-history-body',
                    narration: 'Each row has action buttons: Reload opens the full review results in the main view. Delete removes that specific scan record. If a document has multiple scans, the Compare button opens Document Compare pre-loaded with that document. Always export important results before clearing history.',
                    duration: 8000,
                    navigate: 'history'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                history_table: {
                    id: 'history_table',
                    title: 'History Table',
                    icon: 'table-2',
                    description: 'Browse, sort, and search scan records',
                    preAction: async () => {
                        document.querySelector('#nav-history')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#scan-history-body', narration: 'The Scan History table displays every review session you have performed. Each row shows the document filename, scan date and time, quality grade, total issues found, word count, and statement count.', duration: 7500, navigate: 'history' },
                        { target: '#scan-history-body', narration: 'All columns are sortable — click any header to sort ascending or descending. Sort by grade to find your lowest-quality documents. Sort by date to see your most recent scans. Sort by issues to find documents with the most findings.', duration: 7500, navigate: 'history' },
                        { target: '#history-search', narration: 'The search bar filters the table by document name. Start typing to instantly narrow the results. This is essential when you have hundreds of scan records and need to find a specific document.', duration: 7000, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'Each row has action buttons: Reload opens the full review results in the main view. Delete removes that specific scan record. If a document has multiple scans, the compare button opens Document Compare pre-loaded with that document.', duration: 8000, navigate: 'history' }
                    ]
                },
                reload_compare: {
                    id: 'reload_compare',
                    title: 'Reload & Compare',
                    icon: 'refresh-cw',
                    description: 'Restore past results and compare scans',
                    preAction: async () => {
                        document.querySelector('#nav-history')?.click();
                        await AEGISGuide._wait(600);
                    },
                    scenes: [
                        { target: '#scan-history-body', narration: 'Click the Reload button on any scan entry to instantly restore those review results. The issues table, filter bar, statistics, and quality grade all repopulate exactly as they were when that scan was performed.', duration: 7500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'When a document has been scanned multiple times, a Compare button appears. This opens Document Compare pre-loaded with that document and auto-selects the two most recent scans for comparison.', duration: 7500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'The reload feature preserves everything — not just issues, but also the extracted text, HTML preview, statement extractions, and role discoveries. This means Statement Forge and Roles Studio data is also available from historical scans.', duration: 7500, navigate: 'history' }
                    ]
                },
                data_management: {
                    id: 'data_management',
                    title: 'Data Management',
                    icon: 'database',
                    description: 'Database maintenance and cleanup',
                    preAction: async () => {
                        try {
                            document.querySelector('#nav-history')?.click();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-scan-history', narration: 'The Scan History modal shows all previously scanned documents with their dates, issue counts, quality grades, and statement counts. Each row represents a completed scan that can be reloaded or compared.', duration: 8000, navigate: 'history' },
                        { target: '#history-search', narration: 'Use the search field to filter scan history by document name. The search filters in real time as you type. The refresh button reloads the latest data from the database.', duration: 7000, navigate: 'history' },
                        { target: '#scan-history-body', narration: 'Action buttons on each row let you reload results into Document Review, delete individual scan records, or compare scans of the same document. The Changes column shows diff indicators when multiple scans exist for a document.', duration: 7500, navigate: 'history' }
                    ]
                },
                // v5.9.10: Scan History actions and integration deep-dives
                history_actions: {
                    id: 'history_actions',
                    title: 'Scan Actions',
                    icon: 'mouse-pointer-click',
                    description: 'Reload, delete, compare, and navigate',
                    preAction: async () => {
                        try {
                            document.querySelector('#nav-history')?.click();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-scan-history', narration: 'Each row in the Scan History table has an Actions column with buttons for key operations. The Reload button restores a past scan result into the main Document Review interface — all issues, statistics, and the quality grade load exactly as they were when originally scanned.', duration: 8500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'The Compare button appears only for documents that have been scanned multiple times. Click it to open Document Compare with that document pre-selected, showing the differences between the most recent and previous scan versions.', duration: 7500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'The Delete button removes a specific scan record from the database. A confirmation dialog prevents accidental deletion. Deleting a scan is permanent — the document file itself is not affected, only the AEGIS review data for that particular scan.', duration: 7500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'The Open in Folder button navigates to the original file location. The Refresh button at the top of the history table reloads all records from the database. Sorting is available on every column — click headers to sort by filename, date, grade, issue count, or statement count.', duration: 8000, navigate: 'history' }
                    ]
                },
                statement_integration: {
                    id: 'statement_integration',
                    title: 'Statement History Link',
                    icon: 'link',
                    description: 'Navigate from scans to Statement History',
                    preAction: async () => {
                        try {
                            document.querySelector('#nav-history')?.click();
                            await AEGISGuide._wait(600);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#modal-scan-history', narration: 'The Issues and Statements columns in the Scan History table are clickable links. Click the issue count to load that scan result in Document Review. Click the statement count to open Statement History, which shows all extracted requirement statements from that scan.', duration: 8500, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'Statement History opens as a modal with three views: Overview shows extraction statistics, Document Viewer shows statements highlighted in the source text, and Compare Viewer shows differences between statement sets from different scans.', duration: 8000, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'From Statement History, you can navigate to Statement Forge for editing, to Roles Studio to see the roles associated with those statements, or to Document Compare for a full quality comparison. Scan History is the central hub connecting all AEGIS modules.', duration: 8000, navigate: 'history' },
                        { target: '#modal-scan-history', narration: 'The grade column uses color-coded letter grades from green for A through red for F. Hovering over the grade shows the exact numeric score. Documents with improving grades across scans display a trend indicator showing the direction of change.', duration: 7500, navigate: 'history' }
                    ]
                }
            }
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
                    narration: 'The Settings panel gives you complete control over every aspect of AEGIS. Click the gear icon in the top right corner to open Settings. The panel is organized into nine tabs, each covering a different configuration area.',
                    duration: 7500
                },
                {
                    target: '#settings-reviewer',
                    narration: 'The General tab lets you set your reviewer name, which appears on exported reports and scan records. You can also configure auto-review behavior — whether AEGIS should automatically start scanning when a document is loaded — and toggle the guide system that powers these demos.',
                    duration: 8500,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="review"]',
                    narration: 'Review Options controls the analysis thresholds. Set the maximum recommended sentence length, passive voice percentage threshold, and role extraction sensitivity. You can also configure hyperlink validation defaults, SSL verification, and proxy settings for corporate network environments.',
                    duration: 8500,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="profiles"]',
                    narration: 'Document Profiles are one of the most powerful settings. Create preset checker configurations for different document types — Procedures, Policies, Specifications, Statements of Work, and more. When you scan a document, select the appropriate profile to automatically enable the right set of checkers. This eliminates manual toggling and ensures consistent reviews.',
                    duration: 9500,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="display"]',
                    narration: 'The Display tab controls visual preferences. Toggle Essentials Mode for a cleaner, simplified interface. Set the number of issues per page, enable compact layout mode, and choose whether Metrics and Analytics opens by default when launching AEGIS.',
                    duration: 7500,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="updates"]',
                    narration: 'The Updates tab checks for new AEGIS versions. Click Check for Updates to scan for available patches. If updates are found, you can apply them with one click. AEGIS creates automatic backups before applying updates, and you can roll back to any previous version if needed.',
                    duration: 8000,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="troubleshoot"]',
                    narration: 'The Diagnostics tab is your troubleshooting toolkit. Run a comprehensive health check that verifies all system dependencies, database integrity, and NLP model availability. Export a full diagnostic package as JSON for technical support. You can even email the diagnostics directly to your support team.',
                    duration: 8500,
                    navigate: 'settings'
                },
                {
                    target: '[data-tab="data-management"]',
                    narration: 'Finally, Data Management handles cleanup and reset operations. Clear scan history, statements, roles, or learning data individually. The Factory Reset option returns AEGIS to its initial state. Every destructive operation requires a double confirmation to prevent accidental data loss. Always export your data before performing any cleanup.',
                    duration: 9000,
                    navigate: 'settings'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                general_tab: {
                    id: 'general_tab',
                    title: 'General Settings',
                    icon: 'user',
                    description: 'Reviewer name, auto-review, and guide system',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="general"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '#settings-reviewer', narration: 'The General tab is the first settings screen. Set your reviewer name, which appears on all exported reports, annotated documents, and scan records. This helps identify who performed each review in a multi-user environment.', duration: 7500, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Auto-review can be enabled to start scanning immediately when a document is loaded, skipping the manual Review button click. This is ideal for power users who always want immediate analysis.', duration: 7000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The Guide System toggle controls the help beacon, demo player, and guided tours that you are watching right now. Disable it for a cleaner interface once you are familiar with all features. Re-enable it anytime from this settings tab.', duration: 7500, navigate: 'settings' },
                        { target: '#settings-reviewer', narration: 'The diagnostic email field is used by the troubleshooting system. If configured, you can send diagnostic reports directly to your technical support team with one click.', duration: 6500, navigate: 'settings' }
                    ]
                },
                review_options: {
                    id: 'review_options',
                    title: 'Review Options',
                    icon: 'sliders-horizontal',
                    description: 'Analysis thresholds and checker behavior',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="review"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="review"]', narration: 'Review Options controls the analysis thresholds that determine how checkers evaluate your documents. The sentence length threshold sets the maximum recommended words per sentence — sentences exceeding this limit are flagged.', duration: 8000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The passive voice percentage threshold controls when AEGIS flags excessive passive voice usage. In technical writing, some passive voice is acceptable, but too much reduces clarity. Adjust this based on your document standards.', duration: 7500, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Role extraction sensitivity controls how aggressively AEGIS identifies organizational roles in documents. Higher sensitivity finds more roles but may include false positives. Lower sensitivity is more conservative but may miss legitimate roles.', duration: 8000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Remember Checker Selections persists your checker toggle states between sessions. Without this enabled, checkers reset to defaults each time AEGIS starts. Enable this if you consistently use a specific checker configuration.', duration: 7000, navigate: 'settings' }
                    ]
                },
                network_auth: {
                    id: 'network_auth',
                    title: 'Network & Auth',
                    icon: 'wifi',
                    description: 'Proxy, SSL, and authentication settings',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="network"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="network"]', narration: 'Network settings configure how AEGIS connects to the internet for hyperlink validation and update checks. You can set a proxy server URL if your corporate network requires it. Both HTTP and SOCKS proxies are supported.', duration: 7500, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'SSL verification can be toggled off for environments with self-signed certificates or corporate SSL inspection proxies. While disabling SSL verification reduces security, it may be necessary in certain enterprise network configurations.', duration: 7500, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Windows SSO authentication enables integrated Windows authentication for hyperlink validation. When enabled, AEGIS passes your Windows credentials with HTTP requests to validate intranet links behind corporate single sign-on systems.', duration: 7500, navigate: 'settings' }
                    ]
                },
                profiles: {
                    id: 'profiles',
                    title: 'Document Profiles',
                    icon: 'file-cog',
                    description: 'Preset checker configurations by document type',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="profiles"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="profiles"]', narration: 'Document Profiles let you save and load checker configurations for different document types. Create a profile for Procedures with one set of active checkers, another for Specifications with stricter standards compliance checks, and another for SOWs with role and requirements focus.', duration: 9000, navigate: 'settings' },
                        { target: '#btn-profile-reset-default', narration: 'Each profile stores the complete state of all checker toggles. When you select a profile before scanning, it applies all the saved toggles instantly. This eliminates the tedious process of manually configuring dozens of checkers for each review.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-save-profile', narration: 'Built-in profiles include PrOP (Procedures), PAL (Policies), FGOST (Flight Ground Operations), and SOW (Statement of Work). You can create custom profiles for your organization specific document types and share them with colleagues.', duration: 8000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The profile manager lets you rename, duplicate, delete, and export profiles. Exported profiles are JSON files that can be imported into other AEGIS installations for consistent review standards across teams.', duration: 7000, navigate: 'settings' }
                    ]
                },
                sharing_settings: {
                    id: 'sharing_settings',
                    title: 'Sharing & Import',
                    icon: 'share-2',
                    description: 'Import roles, packages, and shared folder setup',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="sharing"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="sharing"]', narration: 'The Sharing tab manages data exchange between AEGIS installations. Configure a shared folder path where exported role packages and review data are stored for team access.', duration: 7000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Import functions accept multiple file types: dot-aegis-roles packages (complete role dictionaries), JSON adjudication decisions from interactive HTML boards, and role dictionary backups. Each import is previewed before applying.', duration: 8000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The import preview shows what will change — new roles to be added, existing roles to be updated, and any conflicts that need resolution. This prevents accidental overwrites and gives you full control over incoming data.', duration: 7500, navigate: 'settings' }
                    ]
                },
                display_settings: {
                    id: 'display_settings',
                    title: 'Display Options',
                    icon: 'monitor',
                    description: 'Visual preferences and interface modes',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="display"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="display"]', narration: 'Essentials Mode is a simplified interface that hides advanced features for users who only need basic document review. It reduces visual clutter while maintaining full scanning capability.', duration: 7000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The issues per page setting controls how many review findings are shown at once in the results table. Lower values improve scrolling performance for very large result sets. Higher values show more context at once.', duration: 7000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'Dark mode and light mode can be toggled here or using the theme switch in the navigation bar. AEGIS remembers your theme preference across sessions. All features, charts, and exports respect the active theme.', duration: 7000, navigate: 'settings' }
                    ]
                },
                updates_tab: {
                    id: 'updates_tab',
                    title: 'Updates',
                    icon: 'download-cloud',
                    description: 'Version checking and automatic updates',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="updates"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="updates"]', narration: 'The Updates tab shows your current AEGIS version and checks for available updates. Click Check for Updates to scan the configured update server for new releases.', duration: 7000, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'When updates are available, a changelog shows what changed. Apply updates with one click — AEGIS creates an automatic backup first. If an update causes issues, the rollback feature restores the previous version.', duration: 7500, navigate: 'settings' },
                        { target: '#modal-settings', narration: 'The Check for Updates button also detects imported configuration files. If you drop a JSON file in the configured updates folder, AEGIS can auto-detect and import role adjudication decisions and dictionary updates.', duration: 7500, navigate: 'settings' }
                    ]
                },
                diagnostics_tab: {
                    id: 'diagnostics_tab',
                    title: 'Diagnostics',
                    icon: 'stethoscope',
                    description: 'Health checks and diagnostic exports',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="troubleshoot"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '#btn-diag-health-check', narration: 'The Diagnostics tab runs a comprehensive health check on your AEGIS installation. It verifies all Python dependencies, NLP model availability, database integrity, file system permissions, and network connectivity.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-diag-refresh', narration: 'Each diagnostic check shows a pass or fail status with details. Common issues include missing NLP models, insufficient disk space, or database corruption. The health check provides specific remediation steps for each failure.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-diag-export-json', narration: 'The Export Diagnostics button generates a complete JSON report containing system information, dependency versions, database statistics, and error logs. Share this with your technical support team for troubleshooting assistance.', duration: 7500, navigate: 'settings' }
                    ]
                },
                data_mgmt: {
                    id: 'data_mgmt',
                    title: 'Data Management',
                    icon: 'database',
                    description: 'Database cleanup, export, and factory reset',
                    preAction: async () => {
                        document.querySelector('#btn-settings')?.click();
                        await AEGISGuide._wait(500);
                        document.querySelector('[data-tab="data-management"]')?.click();
                        await AEGISGuide._wait(300);
                    },
                    scenes: [
                        { target: '[data-tab="data-management"]', narration: 'Data Management provides fine-grained control over your AEGIS database. View the current database size and record counts for each data type — scan history, roles, statements, function tags, and link validation records.', duration: 7500, navigate: 'settings' },
                        { target: '#btn-clear-scan-history', narration: 'Selective cleanup lets you clear specific data types independently. Clear only scan history while preserving your role dictionary. Clear only statement data while keeping scan records. This granular approach prevents unnecessary data loss.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-load-backups', narration: 'The Export Database button creates a complete backup of all AEGIS data as a JSON file. Import this backup on another machine or after a factory reset to restore your complete data set.', duration: 7000, navigate: 'settings' },
                        { target: '#btn-factory-reset', narration: 'Factory Reset erases everything — all scans, roles, statements, settings, and configurations. This returns AEGIS to its initial out-of-the-box state. A double confirmation dialog prevents accidental resets. Always export your data first.', duration: 7500, navigate: 'settings' }
                    ]
                },
                // v5.9.10: Settings deep-dive sub-demos
                checker_categories: {
                    id: 'checker_categories',
                    title: 'Checker Categories',
                    icon: 'list-checks',
                    description: 'Ninety-eight quality checkers in six groups',
                    preAction: async () => {
                        try {
                            document.querySelector('#btn-settings')?.click();
                            await AEGISGuide._wait(500);
                            document.querySelector('[data-tab="review"]')?.click();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#settings-review', narration: 'The Review tab in Settings reveals all ninety-eight quality checker toggles organized into six main categories. Style guide presets at the top let you quickly configure for Microsoft, Google, or aerospace standards. Below them are the individual checker toggle groups.', duration: 9000, navigate: 'settings' },
                        { target: '#settings-review', narration: 'Grammar and Spelling checkers cover spelling errors with an aerospace-aware dictionary, grammar rules, punctuation, capitalization, contractions, dangling modifiers, run-on sentences, and sentence fragments. Each checker runs independently and can be toggled on or off.', duration: 8000, navigate: 'settings' },
                        { target: '#settings-review', narration: 'Technical Writing checkers are the AEGIS specialty — undefined acronym detection, requirements language verification, TBD and TBR placeholder flagging, testability assessment, atomicity checks, escape clause detection, number and unit format validation, and cross-reference verification.', duration: 9000, navigate: 'settings' },
                        { target: '#settings-max-sentence', narration: 'Configuration controls let you tune checker thresholds. The maximum sentence length slider sets the word count limit before a sentence is flagged. The passive voice threshold controls what percentage of passive constructions triggers a warning.', duration: 8000, navigate: 'settings' },
                        { target: '#settings-review', narration: 'Standards Compliance includes MIL-STD, DO-178C, and accessibility compliance checkers. Seven additional always-on checkers run regardless of toggle state, including role extraction, gender-neutral language, and consistency analysis.', duration: 8000, navigate: 'settings' }
                    ]
                },
                profile_management: {
                    id: 'profile_management',
                    title: 'Profile Save & Load',
                    icon: 'save',
                    description: 'Create and manage checker profiles',
                    preAction: async () => {
                        try {
                            document.querySelector('#btn-settings')?.click();
                            await AEGISGuide._wait(500);
                            document.querySelector('[data-tab="profiles"]')?.click();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '[data-tab="profiles"]', narration: 'The Profiles tab lets you save and load checker configurations. Document profile pills at the top — PrOP, Academic, Regulatory, SOW, and Custom — each represent a pre-configured set of checker toggles optimized for that document type.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-profile-reset-default', narration: 'Click any profile pill to instantly load that configuration. All checker toggles in the Review tab update to match the profile settings. This is faster than manually toggling individual checkers when switching between document types.', duration: 7500, navigate: 'settings' },
                        { target: '#btn-save-profile', narration: 'The Save Profile button captures your current checker configuration under a custom name. The save dialog lets you name the profile and add an optional description. Saved profiles appear alongside the built-in presets.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-profile-reset-default', narration: 'Reset to Default restores the factory checker configuration. Select All enables every checker. Clear All disables all optional checkers, leaving only the seven always-on checkers active. Your profile selection persists across sessions.', duration: 7500, navigate: 'settings' }
                    ]
                },
                diagnostics_deep: {
                    id: 'diagnostics_deep',
                    title: 'Diagnostics Workflow',
                    icon: 'stethoscope',
                    description: 'Health checks, exports, and dependency verification',
                    preAction: async () => {
                        try {
                            document.querySelector('#btn-settings')?.click();
                            await AEGISGuide._wait(500);
                            document.querySelector('[data-tab="troubleshoot"]')?.click();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#btn-diag-refresh', narration: 'The Diagnostics tab is your troubleshooting command center. The Refresh button gathers a comprehensive diagnostic summary: Python version, installed packages, database status, available disk space, memory usage, and the status of all AEGIS modules.', duration: 8500, navigate: 'settings' },
                        { target: '#btn-diag-health-check', narration: 'The Health Check button verifies all AEGIS dependencies: spaCy model availability, NLP pipeline status, database connectivity, file system permissions, and optional modules like Docling and Playwright. Each check reports pass, warning, or fail.', duration: 8500, navigate: 'settings' },
                        { target: '#btn-diag-export-json', narration: 'Export Diagnostics as JSON creates a machine-readable file suitable for automated analysis or sharing with support. The JSON includes the full diagnostic summary, health check results, dependency versions, and recent error logs.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-diag-export-txt', narration: 'Export as Text creates a human-readable formatted report. Both JSON and Text formats capture the same information, but the text version is easier to read in a plain text editor or paste into an email.', duration: 7500, navigate: 'settings' },
                        { target: '#btn-diag-email', narration: 'The Email button creates a pre-formatted diagnostic email in Microsoft Outlook with the diagnostic report attached. This streamlines the support workflow — one click gathers all the information needed to troubleshoot an issue.', duration: 7500, navigate: 'settings' }
                    ]
                },
                data_operations: {
                    id: 'data_operations',
                    title: 'Backup & Recovery',
                    icon: 'shield',
                    description: 'Backup, restore, selective cleanup, and reset',
                    preAction: async () => {
                        try {
                            document.querySelector('#btn-settings')?.click();
                            await AEGISGuide._wait(500);
                            document.querySelector('[data-tab="data-management"]')?.click();
                            await AEGISGuide._wait(300);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '[data-tab="data-management"]', narration: 'The Data Management tab shows your database at a glance: total size on disk, record counts for scan history, roles, statements, function tags, and link validation data. Each data type shows its individual storage contribution.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-load-backups', narration: 'The Load Backups button scans for available backup files and displays them with timestamps and sizes. Select any backup to preview its contents before restoring. The Rollback button restores the selected backup, replacing current data.', duration: 8000, navigate: 'settings' },
                        { target: '#btn-clear-scan-history', narration: 'Four selective cleanup buttons let you clear specific data types independently: Clear Scan History removes all review records. Clear Statements removes extracted requirements. Clear Role Dictionary removes adjudicated roles. Clear Learning Data removes adaptive threshold data.', duration: 9000, navigate: 'settings' },
                        { target: '#btn-rollback', narration: 'Each cleanup button shows a confirmation dialog with the specific data that will be removed and the record count. This prevents accidental data loss. The operation is irreversible — always export a backup first using the Load Backups export feature.', duration: 7500, navigate: 'settings' },
                        { target: '#btn-factory-reset', narration: 'Factory Reset is the nuclear option — it removes all data, resets all settings to defaults, and returns AEGIS to its initial state. A double confirmation dialog requires you to type a specific phrase before proceeding. This is designed for clean reinstalls or troubleshooting.', duration: 8500, navigate: 'settings' }
                    ]
                }
            }
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
                    target: '.pf-header',
                    narration: 'The Portfolio view gives you a bird\'s eye view of your entire document collection. Every document you have scanned appears as a card tile with its quality grade, last scan date, issue count, and review status. This is designed for program managers and quality leads who need to track documentation health across an entire project.',
                    duration: 9000,
                    navigate: 'portfolio'
                },
                {
                    target: '#pf-stats-mini',
                    narration: 'The header stats chips show total document count, number of batches, and average quality score across your portfolio. These metrics update automatically as you scan more documents. The view toggle switches between grid and list layouts.',
                    duration: 8000,
                    navigate: 'portfolio'
                },
                {
                    target: '#pf-batch-grid',
                    narration: 'Batch scan groups appear as collapsible cards showing the scan date, document count, aggregate grade, and mini preview tiles of documents inside. Each batch card uses color-coded grade badges — green for A and B grades, yellow for C, orange for D, and red for F.',
                    duration: 8500,
                    navigate: 'portfolio'
                },
                {
                    target: '#pf-singles-grid',
                    narration: 'Individual document scans appear below batches in the Singles section. Each tile shows the filename, quality grade glow effect, issue count, word count, and scan date. Click any tile to open a detailed preview panel with severity breakdown and top issues.',
                    duration: 8000,
                    navigate: 'portfolio'
                },
                {
                    target: '#pf-activity-feed',
                    narration: 'The activity sidebar shows your most recent scan activity. Each entry displays the document name, quality score, and timestamp. This provides a quick timeline of your review activity across the portfolio. Combined with Metrics and Analytics, you get the complete quality picture.',
                    duration: 8500,
                    navigate: 'portfolio'
                }
            ],
            // v2.3.0: Deep-dive sub-demos
            subDemos: {
                overview_cards: {
                    id: 'overview_cards',
                    title: 'Portfolio Overview',
                    icon: 'layout-grid',
                    description: 'Document cards with quality grades and status',
                    preAction: async () => {
                        try {
                            // v5.9.15: Use Portfolio.open() to show actual portfolio content
                            if (window.Portfolio?.open) window.Portfolio.open();
                            else document.querySelector('#nav-portfolio')?.click();
                            await AEGISGuide._wait(800);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '.pf-header', narration: 'The Portfolio view presents all your scanned documents in a rich card grid. The header displays the Portfolio title, subtitle, and navigation controls. The view toggle button switches between grid and list layout modes.', duration: 8500, navigate: 'portfolio' },
                        { target: '#pf-stats-mini', narration: 'Stats chips show the total document count, number of batch sessions, and average quality score across the portfolio. These aggregate metrics update automatically as you scan more documents.', duration: 7500, navigate: 'portfolio' },
                        { target: '#pf-batch-grid', narration: 'Batch session cards show documents scanned together as a group. Each batch card displays the scan date, document count, aggregate grade with color coding, and mini preview tiles. Click Expand to see all documents inside a batch.', duration: 8000, navigate: 'portfolio' },
                        { target: '#pf-singles-grid', narration: 'Individual document tiles below the batches show standalone scans. Each tile has a grade-colored glow effect, filename, issue count, word count, and scan timestamp. Click any tile to open the preview panel with detailed information.', duration: 7500, navigate: 'portfolio' }
                    ]
                },
                sorting_filtering: {
                    id: 'sorting_filtering',
                    title: 'Sorting & Filtering',
                    icon: 'arrow-up-down',
                    description: 'Sort, search, and filter portfolio documents',
                    preAction: async () => {
                        try {
                            if (window.Portfolio?.open) window.Portfolio.open();
                            else document.querySelector('#nav-portfolio')?.click();
                            await AEGISGuide._wait(800);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#pf-stats-mini', narration: 'The sort dropdown provides multiple ordering options: sort by quality grade to see weakest documents first, by scan date to find stale reviews, by name for alphabetical browsing, by word count to find your largest documents, or by issue count to prioritize remediation.', duration: 8500, navigate: 'portfolio' },
                        { target: '#pf-activity-feed', narration: 'The activity sidebar provides a chronological view of recent scans. Use it to quickly find recently reviewed documents. Each activity item shows the document name, quality score, and how long ago it was scanned.', duration: 7000, navigate: 'portfolio' },
                        { target: '#pf-batch-grid', narration: 'Grade filter chips let you show only documents with specific quality grades. Click the A chip to see only your highest-quality documents. Click F to see documents that need immediate attention. Combine multiple grade filters to focus your view.', duration: 7000, navigate: 'portfolio' }
                    ]
                },
                quality_gates: {
                    id: 'quality_gates',
                    title: 'Quality Gates',
                    icon: 'shield-check',
                    description: 'Gate assessments and program readiness',
                    preAction: async () => {
                        try {
                            if (window.Portfolio?.open) window.Portfolio.open();
                            else document.querySelector('#nav-portfolio')?.click();
                            await AEGISGuide._wait(800);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#pf-stats-mini', narration: 'The Portfolio view is designed for quality gate assessments. The stats chips show your portfolio health at a glance — total documents reviewed, batch count, and average score. Before program milestones, use this to assess documentation readiness.', duration: 8000, navigate: 'portfolio' },
                        { target: '#pf-batch-grid', narration: 'Quality gates can be defined by minimum grade thresholds. Batch cards show aggregate grades — quickly identify which batches pass and which contain documents below threshold. The color-coded badges make pass and fail status immediately visible.', duration: 7500, navigate: 'portfolio' },
                        { target: '#pf-singles-grid', narration: 'The portfolio data integrates with Metrics and Analytics for trend analysis. Track whether your overall portfolio quality is improving over time as documents are revised and rescanned. Use this data in quality review boards and milestone assessments.', duration: 8000, navigate: 'portfolio' }
                    ]
                },
                // v5.9.10: Portfolio deep-dive sub-demos
                batch_grouping: {
                    id: 'batch_grouping',
                    title: 'Batch Groups',
                    icon: 'layers',
                    description: 'Grouped scans and aggregate metrics',
                    preAction: async () => {
                        try {
                            if (window.Portfolio?.open) window.Portfolio.open();
                            else document.querySelector('#nav-portfolio')?.click();
                            await AEGISGuide._wait(800);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#pf-batch-grid', narration: 'Documents scanned in a batch appear together in the Portfolio as a collapsible group card. The card header shows the batch scan date, total document count, aggregate grade with color coding, and mini preview tiles of documents inside the batch.', duration: 8000, navigate: 'portfolio' },
                        { target: '.pf-batch-card', narration: 'Each batch card displays three stat columns — document count, total issues, and letter grade. Click the View All Documents button to expand the batch and reveal individual document cards with their own grades and metrics.', duration: 7500, navigate: 'portfolio' },
                        { target: '#pf-stats-mini', narration: 'Aggregate metrics in the header show the total batch count and average score across all documents. The batch count chip updates as you add new batch sessions. This gives you a quick portfolio health indicator.', duration: 7500, navigate: 'portfolio' },
                        { target: '#pf-singles-grid', narration: 'Individual document scans that were not part of a batch appear as standalone tiles in the Singles section. These are sorted by most recent scan date. The Portfolio provides a unified view of both batch and individual scan results.', duration: 7500, navigate: 'portfolio' }
                    ]
                },
                portfolio_actions: {
                    id: 'portfolio_actions',
                    title: 'Portfolio Actions',
                    icon: 'external-link',
                    description: 'Open, rescan, and compare from portfolio',
                    preAction: async () => {
                        try {
                            if (window.Portfolio?.open) window.Portfolio.open();
                            else document.querySelector('#nav-portfolio')?.click();
                            await AEGISGuide._wait(800);
                        } catch(e) { console.warn('[AEGIS Guide] preAction error:', e); }
                    },
                    scenes: [
                        { target: '#pf-singles-grid', narration: 'Click any document tile in the Portfolio to open a preview panel on the right side. The preview shows the document quality grade, severity breakdown bars, top issues list, and a text preview. An Open in Review button loads the full scan results.', duration: 8000, navigate: 'portfolio' },
                        { target: '#pf-batch-grid', narration: 'For batch groups, click any batch card to expand it and see all documents inside. Each document within the batch has its own grade and can be previewed individually. Compare buttons let you diff scans between versions.', duration: 7500, navigate: 'portfolio' },
                        { target: '#pf-activity-feed', narration: 'The activity feed provides quick access to recent scans. Click any activity item to jump directly to that document. Use the sorting and filtering controls to focus on specific areas — low-graded documents, recently scanned files, or documents above a certain word count.', duration: 7500, navigate: 'portfolio' }
                    ]
                }
            }
        }
    },

    // ═════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═════════════════════════════════════════════════════════════════

    init() {
        if (this.state.initialized) return;

        // Check if guide is enabled in settings
        this.state.enabled = this.isEnabled();

        console.log('[AEGIS Guide] Initializing v2.3.0...', this.state.enabled ? 'ENABLED' : 'DISABLED');

        // Create DOM elements
        this.createBeacon();
        this.createPanel();
        this.createSpotlight();
        this.createDemoBar();

        // Attach event listeners
        this.attachEventListeners();

        // v2.1.0: Initialize voice narration system
        this.initNarration();

        // Apply enabled state
        if (!this.state.enabled) {
            this.refs.beacon.style.display = 'none';
        }

        this.state.initialized = true;
        console.log('[AEGIS Guide] Initialization complete (narration:',
            this.narration.enabled ? 'ON' : 'OFF', ')');
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
                <div class="panel-help-content" id="guide-panel-help-content">
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

                <div class="demo-picker hidden" id="guide-demo-picker">
                    <button class="demo-picker-back" id="demo-picker-back">
                        <span>&#8592;</span> Back to Help
                    </button>
                    <div class="demo-picker-content" id="demo-picker-content"></div>
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
                    <div class="demo-narration-controls">
                        <button class="demo-ctrl-btn demo-narration-btn" id="demo-narration-toggle" title="Enable voice narration">
                            <i data-lucide="volume-x"></i>
                        </button>
                        <input type="range" class="demo-volume-slider" id="demo-volume"
                               min="0" max="1" step="0.1" value="0.8" title="Narration volume">
                    </div>
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

        // Demo button — v2.3.0: Show picker if sub-demos exist, else direct play
        this.refs.panel.querySelector('#guide-demo-btn').addEventListener('click', () => {
            const section = this.state.currentSection || this.detectCurrentSection();
            const sectionData = this.sections[section];
            if (sectionData && sectionData.subDemos && Object.keys(sectionData.subDemos).length > 0) {
                this._showDemoPicker(section);
            } else {
                this.closePanel();
                this.startDemo(section);
            }
        });

        // Demo picker back button
        this.refs.panel.querySelector('#demo-picker-back').addEventListener('click', () => {
            this._hideDemoPicker();
        });

        // Demo picker card clicks (delegated)
        this.refs.panel.querySelector('#demo-picker-content').addEventListener('click', (e) => {
            const card = e.target.closest('.demo-picker-card, .demo-picker-overview-card');
            if (!card) return;
            const sectionId = card.dataset.section;
            const subDemoId = card.dataset.subdemo;
            if (subDemoId === '__overview__') {
                this.closePanel();
                this.startDemo(sectionId);
            } else if (subDemoId) {
                this.closePanel();
                this.startSubDemo(sectionId, subDemoId);
            }
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
            const newSpeed = parseFloat(e.target.value);
            const oldSpeed = this.demo.speed;
            this.demo.speed = newSpeed;

            // BUG #9 fix: Sync all active narration/timers to new speed
            // 1. Sync pre-generated audio playbackRate
            if (this.narration.audioElement && !this.narration.audioElement.paused) {
                this.narration.audioElement.playbackRate = newSpeed;
            }

            // 2. Restart Web Speech with new rate (can't change queued utterance rates)
            if (this.narration.enabled && this.narration.currentUtterance && 'speechSynthesis' in window && speechSynthesis.speaking) {
                // Cancel current speech and let the step timer handle re-advancement
                speechSynthesis.cancel();
                this.narration.currentUtterance = null;
            }

            // 3. Reschedule pending step timer with adjusted remaining time
            if (this.demo.timer && this.demo.isPlaying && !this.demo.isPaused) {
                clearTimeout(this.demo.timer);
                // Recalculate remaining time scaled to new speed
                const speedRatio = oldSpeed / newSpeed;
                const adjustedDelay = Math.max(200, 800 * speedRatio / newSpeed);
                this.demo.timer = setTimeout(() => {
                    if (this.demo.isPlaying && !this.demo.isPaused) {
                        this._showDemoStep(this.demo.currentStep + 1);
                    }
                }, adjustedDelay);
            }

            // 4. Restart typewriter at new speed
            if (this.demo.typeTimer) {
                const el = this.refs.demoBar.querySelector('#demo-bar-narration');
                const currentText = el?.textContent || '';
                const scenes = this.demo.scenes;
                if (scenes && scenes[this.demo.currentStep]) {
                    const fullText = scenes[this.demo.currentStep].narration || '';
                    if (currentText.length < fullText.length) {
                        // Still typing — restart from current position
                        clearInterval(this.demo.typeTimer);
                        const remaining = fullText.substring(currentText.length);
                        let i = 0;
                        const typeSpeed = Math.max(10, this.config.demoTypeSpeed / newSpeed);
                        this.demo.typeTimer = setInterval(() => {
                            if (i < remaining.length) {
                                el.textContent += remaining[i];
                                i++;
                            } else {
                                clearInterval(this.demo.typeTimer);
                                this.demo.typeTimer = null;
                            }
                        }, typeSpeed);
                    }
                }
            }
        });

        // v2.1.0: Narration controls
        this.refs.demoBar.querySelector('#demo-narration-toggle').addEventListener('click', () => {
            this.toggleNarration();
        });
        const volumeSlider = this.refs.demoBar.querySelector('#demo-volume');
        if (volumeSlider) {
            volumeSlider.value = this.narration.volume;
            volumeSlider.addEventListener('input', (e) => {
                this.setNarrationVolume(parseFloat(e.target.value));
            });
        }
        // Initialize narration button state
        this._updateNarrationButton();

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

        // v2.3.0: Ensure demo picker is hidden and help content is visible
        this._hideDemoPicker();

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
        // v5.9.16-fix: Never show tooltip during live demo — the demo bar handles narration
        if (this.demo && this.demo.isPlaying) {
            tooltip.style.visibility = 'hidden';
            tooltip.style.display = 'none';
        } else {
            tooltip.style.visibility = 'visible';
        }
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
    // VOICE NARRATION SYSTEM (v2.1.0)
    // Provider chain: Pre-generated MP3 → Web Speech API → Silent
    // ═════════════════════════════════════════════════════════════════

    initNarration() {
        console.log('[AEGIS Guide] Initializing voice narration system');

        // Restore saved preferences
        const saved = localStorage.getItem(this.narration.storageKey);
        this.narration.enabled = saved === 'true';
        const savedVol = localStorage.getItem(this.narration.volumeKey);
        if (savedVol) this.narration.volume = parseFloat(savedVol);

        // Create reusable audio element for pre-generated clips
        this.narration.audioElement = document.createElement('audio');
        this.narration.audioElement.preload = 'auto';
        this.narration.audioElement.volume = this.narration.volume;

        // Initialize Web Speech API voices
        if ('speechSynthesis' in window) {
            const loadVoices = () => {
                const voices = speechSynthesis.getVoices();
                if (voices.length > 0) {
                    this.narration.voices = voices;
                    this.narration.voicesLoaded = true;
                    this._selectPreferredVoice();
                    console.log('[AEGIS Guide] Loaded', voices.length, 'TTS voices');
                }
            };
            loadVoices();
            speechSynthesis.onvoiceschanged = loadVoices;
        }

        // Try loading pre-generated audio manifest
        this._loadAudioManifest();
    },

    _selectPreferredVoice() {
        const voices = this.narration.voices;
        const savedVoiceName = localStorage.getItem(this.narration.voiceKey);

        // Try saved preference first
        if (savedVoiceName) {
            const saved = voices.find(v => v.name === savedVoiceName);
            if (saved) { this.narration.preferredVoice = saved; return; }
        }

        // v5.9.30: Priority order for natural-sounding FEMALE English voices
        // Windows neural voices (Online = neural, high quality) > macOS premium > Google > fallback
        const priorities = [
            // Windows 10/11 Neural voices — natural female, best quality
            v => v.name.includes('Microsoft') && v.name.includes('Online') && /Aria|Jenny|Sonia|Libby/i.test(v.name),
            // Windows standard female voices
            v => v.name.includes('Microsoft Zira'),
            v => v.name.includes('Microsoft') && /Aria|Jenny|Hazel|Susan/i.test(v.name),
            // macOS premium female voices
            v => v.name === 'Samantha',             // macOS high quality female
            v => v.name === 'Karen',                // macOS Australian female
            v => v.name === 'Moira',                // macOS Irish female
            v => v.name === 'Tessa',                // macOS South African female
            // Google female voices
            v => v.name.includes('Google US English') && v.name.includes('Female'),
            v => v.name.includes('Google UK English') && v.name.includes('Female'),
            // Cloud/remote female voices (higher quality than local)
            v => v.lang.startsWith('en') && !v.localService && /female|woman/i.test(v.name),
            // Any cloud English voice (usually better than local)
            v => v.lang.startsWith('en-US') && !v.localService,
            // Google voices (decent quality fallback)
            v => v.name.includes('Google US English'),
            v => v.name.includes('Google UK English'),
            // Any en-US voice
            v => v.lang.startsWith('en-US'),
            v => v.lang.startsWith('en'),
        ];

        for (const test of priorities) {
            const match = voices.find(test);
            if (match) {
                this.narration.preferredVoice = match;
                console.log('[AEGIS Guide] Selected voice:', match.name);
                return;
            }
        }

        // Fallback to first available
        if (voices.length > 0) {
            this.narration.preferredVoice = voices[0];
        }
    },

    async _loadAudioManifest() {
        try {
            const resp = await fetch('/static/audio/demo/manifest.json', { cache: 'no-cache' });
            if (resp.ok) {
                this.narration.manifest = await resp.json();
                this.narration.manifestLoaded = true;
                console.log('[AEGIS Guide] Audio manifest loaded —',
                    Object.keys(this.narration.manifest.sections || {}).length, 'sections');
            }
        } catch (e) {
            // No pre-generated audio available — that's fine, fall back to Web Speech
            console.log('[AEGIS Guide] No pre-generated audio manifest found (will use Web Speech API)');
        }
    },

    /**
     * Play narration for a demo step.
     * Provider chain: Pre-generated MP3 → Web Speech API → Silent (timer)
     * Returns a Promise that resolves when narration completes.
     */
    async _playNarration(text, sectionId, stepIndex) {
        if (!this.narration.enabled || !text) return false;

        // Try pre-generated audio first
        if (this.narration.manifestLoaded && this.narration.manifest) {
            const audioFile = this._getPregenAudioFile(sectionId, stepIndex);
            if (audioFile) {
                try {
                    const played = await this._playAudioClip(audioFile);
                    if (played) return true;
                } catch (e) {
                    console.warn('[AEGIS Guide] Pre-gen audio failed:', e.message);
                }
            }
        }

        // Fall back to Web Speech API
        if ('speechSynthesis' in window && this.narration.voicesLoaded) {
            try {
                await this._speakText(text);
                return true;
            } catch (e) {
                console.warn('[AEGIS Guide] Web Speech failed:', e.message);
            }
        }

        return false; // No audio provider available
    },

    _getPregenAudioFile(sectionId, stepIndex) {
        if (!this.narration.manifest || !this.narration.manifest.sections) return null;
        const section = this.narration.manifest.sections[sectionId];
        if (!section || !section.steps || !section.steps[stepIndex]) return null;
        return '/static/audio/demo/' + section.steps[stepIndex].file;
    },

    /**
     * Play a pre-generated audio clip.
     * Returns Promise<boolean> — true if played successfully.
     */
    _playAudioClip(url) {
        return new Promise((resolve) => {
            const audio = this.narration.audioElement;
            audio.src = url;
            audio.volume = this.narration.volume;
            audio.playbackRate = this.demo.speed;

            const cleanup = () => {
                audio.onended = null;
                audio.onerror = null;
            };

            audio.onended = () => { cleanup(); resolve(true); };
            audio.onerror = () => { cleanup(); resolve(false); };

            audio.play().catch(() => { cleanup(); resolve(false); });
        });
    },

    /**
     * Speak text using Web Speech API with Chrome 15-second bug workaround.
     * Splits long text into sentences and chains them.
     */
    _speakText(text) {
        return new Promise((resolve) => {
            if (!('speechSynthesis' in window)) { resolve(); return; }

            speechSynthesis.cancel(); // Stop any current speech

            // Split into sentences to avoid Chrome's 15-second timeout bug
            const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
            let index = 0;

            const speakNext = () => {
                if (index >= sentences.length || !this.demo.isPlaying || !this.narration.enabled) {
                    resolve();
                    return;
                }

                const utterance = new SpeechSynthesisUtterance(sentences[index].trim());
                if (this.narration.preferredVoice) {
                    utterance.voice = this.narration.preferredVoice;
                }
                utterance.rate = Math.min(2, Math.max(0.5, this.demo.speed));
                utterance.volume = this.narration.volume;
                utterance.pitch = 1.05;  // v5.9.30: Slightly higher pitch for more natural female tone

                utterance.onend = () => { index++; speakNext(); };
                utterance.onerror = () => { index++; speakNext(); };

                this.narration.currentUtterance = utterance;
                speechSynthesis.speak(utterance);
            };

            speakNext();
        });
    },

    _stopNarration() {
        // Stop pre-generated audio
        if (this.narration.audioElement) {
            this.narration.audioElement.pause();
            this.narration.audioElement.currentTime = 0;
        }
        // Stop Web Speech
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        this.narration.currentUtterance = null;
    },

    _pauseNarration() {
        if (this.narration.audioElement && !this.narration.audioElement.paused) {
            this.narration.audioElement.pause();
        }
        if ('speechSynthesis' in window && speechSynthesis.speaking) {
            speechSynthesis.pause();
        }
    },

    _resumeNarration() {
        if (this.narration.audioElement && this.narration.audioElement.paused &&
            this.narration.audioElement.currentTime > 0) {
            this.narration.audioElement.play().catch(() => {});
        }
        if ('speechSynthesis' in window && speechSynthesis.paused) {
            speechSynthesis.resume();
        }
    },

    toggleNarration() {
        this.narration.enabled = !this.narration.enabled;
        localStorage.setItem(this.narration.storageKey, this.narration.enabled);

        // Update UI
        this._updateNarrationButton();

        if (!this.narration.enabled) {
            this._stopNarration();
        }

        if (window.showToast) {
            showToast(this.narration.enabled ? 'Voice narration enabled' : 'Voice narration disabled',
                this.narration.enabled ? 'success' : 'info');
        }
        console.log('[AEGIS Guide] Narration:', this.narration.enabled ? 'ON' : 'OFF');
    },

    setNarrationVolume(vol) {
        this.narration.volume = Math.min(1, Math.max(0, vol));
        localStorage.setItem(this.narration.volumeKey, this.narration.volume);
        if (this.narration.audioElement) {
            this.narration.audioElement.volume = this.narration.volume;
        }
    },

    _updateNarrationButton() {
        const btn = this.refs.demoBar?.querySelector('#demo-narration-toggle');
        if (!btn) return;
        const icon = this.narration.enabled ? 'volume-2' : 'volume-x';
        btn.innerHTML = `<i data-lucide="${icon}"></i>`;
        btn.classList.toggle('narration-active', this.narration.enabled);
        btn.title = this.narration.enabled ? 'Mute narration' : 'Enable narration';
        // Refresh lucide icon
        if (typeof lucide !== 'undefined') {
            requestAnimationFrame(() => {
                try { lucide.createIcons({ attrs: { class: 'lucide-icon' } }); } catch (e) {}
            });
        }
    },

    /**
     * Get list of available voices for settings UI
     */
    getAvailableVoices() {
        return this.narration.voices
            .filter(v => v.lang.startsWith('en'))
            .map(v => ({ name: v.name, lang: v.lang, local: v.localService }));
    },

    setVoice(voiceName) {
        const voice = this.narration.voices.find(v => v.name === voiceName);
        if (voice) {
            this.narration.preferredVoice = voice;
            localStorage.setItem(this.narration.voiceKey, voiceName);
            console.log('[AEGIS Guide] Voice set to:', voiceName);
        }
    },

    // ═════════════════════════════════════════════════════════════════
    // DEMO PLAYER (Auto-playing animated walkthrough)
    // ═════════════════════════════════════════════════════════════════

    async startDemo(sectionId) {
        // Guard against double-start (e.g., rapid double-click on Watch Demo)
        if (this.demo.isPlaying) {
            console.log('[AEGIS Guide] Demo already playing, ignoring startDemo call');
            return;
        }

        const section = sectionId || 'landing';
        const sectionData = this.sections[section];

        if (!sectionData || !sectionData.demoScenes || sectionData.demoScenes.length === 0) {
            console.warn('[AEGIS Guide] No demo scenes for:', section);
            if (window.showToast) window.showToast('No demo available for this section yet', 'info');
            return;
        }

        this.closePanel();
        this.endTour();

        // v5.9.16-fix: Navigate to the correct section BEFORE playing scenes.
        // Without this, starting a demo from the landing page leaves the landing
        // overlay active, hiding all spotlight targets behind it.
        await this._navigateToSection(section);
        await this._wait(600);

        this.demo.isPlaying = true;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.currentSection = section;
        this.demo.scenes = sectionData.demoScenes;
        // v5.9.18: Hide help beacon during demo playback so it doesn't overlay controls
        if (this.refs.beacon) this.refs.beacon.style.display = 'none';

        // Show demo bar
        this.refs.demoBar.classList.remove('hidden');
        this.refs.demoBar.querySelector('#demo-bar-section').textContent = sectionData.title;
        this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';

        this._showDemoStep(0);
        console.log('[AEGIS Guide] Demo started:', section, '—', sectionData.demoScenes.length, 'scenes');
    },

    startFullDemo() {
        // Guard against double-start
        if (this.demo.isPlaying) return;
        // Build combined demo from all sections
        const sectionOrder = ['landing', 'review', 'batch', 'roles', 'forge', 'validator', 'compare', 'metrics', 'history', 'settings', 'portfolio'];
        let allScenes = [];

        sectionOrder.forEach(id => {
            const s = this.sections[id];
            if (s && s.demoScenes) {
                // Add a section intro scene
                // v5.9.16-fix: Use navigate: id (not undefined) so _showDemoStep()
                // calls _navigateToSection() to open the correct modal/view
                allScenes.push({
                    target: null,
                    narration: `Now let's explore: ${s.title}`,
                    duration: 2500,
                    sectionLabel: s.title,
                    navigate: id
                });
                allScenes = allScenes.concat(s.demoScenes.map((scene, idx) => ({
                    ...scene,
                    sectionLabel: s.title,
                    _sectionId: id,
                    _stepIndex: idx
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
        // v5.9.18: Hide help beacon during demo playback
        if (this.refs.beacon) this.refs.beacon.style.display = 'none';

        this.refs.demoBar.classList.remove('hidden');
        this.refs.demoBar.querySelector('#demo-bar-section').textContent = 'Full Application Demo';
        this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';

        this._showDemoStep(0);
        console.log('[AEGIS Guide] Full demo started:', allScenes.length, 'scenes');
    },

    // ═════════════════════════════════════════════════════════════════
    // SUB-DEMO SYSTEM (v2.3.0 - Hierarchical drill-down demos)
    // ═════════════════════════════════════════════════════════════════

    /**
     * Start a specific sub-demo within a section.
     * Navigates to the section, runs the sub-demo's preAction, then plays its scenes.
     */
    async startSubDemo(sectionId, subDemoId) {
        if (this.demo.isPlaying) {
            console.log('[AEGIS Guide] Demo already playing, ignoring startSubDemo call');
            return;
        }

        const sectionData = this.sections[sectionId];
        if (!sectionData || !sectionData.subDemos || !sectionData.subDemos[subDemoId]) {
            console.warn('[AEGIS Guide] No sub-demo found:', sectionId, subDemoId);
            if (window.showToast) window.showToast('Sub-demo not available yet', 'info');
            return;
        }

        const subDemo = sectionData.subDemos[subDemoId];
        if (!subDemo.scenes || subDemo.scenes.length === 0) {
            console.warn('[AEGIS Guide] Sub-demo has no scenes:', subDemoId);
            return;
        }

        this.closePanel();
        this.endTour();

        // Navigate to the parent section first
        await this._navigateToSection(sectionId);
        await this._wait(600);

        // Run the sub-demo's preAction (e.g., click specific tab)
        if (subDemo.preAction) {
            try {
                await subDemo.preAction();
            } catch (e) {
                console.warn('[AEGIS Guide] Sub-demo preAction error:', e);
            }
        }

        // Tag scenes with metadata for voice narration & breadcrumb
        const taggedScenes = subDemo.scenes.map((scene, idx) => ({
            ...scene,
            sectionLabel: `${sectionData.title} › ${subDemo.title}`,
            _sectionId: sectionId,
            _subDemoId: subDemoId,
            _stepIndex: idx
        }));

        this.demo.isPlaying = true;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.currentSection = sectionId;
        this.demo.currentSubDemo = subDemoId;
        this.demo.scenes = taggedScenes;
        // v5.9.18: Hide help beacon during demo playback
        if (this.refs.beacon) this.refs.beacon.style.display = 'none';

        // Show demo bar with breadcrumb title
        this.refs.demoBar.classList.remove('hidden');
        this.refs.demoBar.querySelector('#demo-bar-section').textContent =
            `${sectionData.title} › ${subDemo.title}`;
        this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#10074;&#10074;';

        this._showDemoStep(0);
        console.log('[AEGIS Guide] Sub-demo started:', sectionId, '>', subDemoId,
            '—', subDemo.scenes.length, 'scenes');
    },

    /**
     * Show the demo picker UI in the help panel.
     * Displays overview demo card + grid of sub-demo cards.
     */
    _showDemoPicker(sectionId) {
        const sectionData = this.sections[sectionId];
        if (!sectionData) return;

        const helpContent = this.refs.panel.querySelector('#guide-panel-help-content');
        const picker = this.refs.panel.querySelector('#guide-demo-picker');
        const pickerContent = this.refs.panel.querySelector('#demo-picker-content');

        // Calculate overview duration
        const overviewScenes = sectionData.demoScenes ? sectionData.demoScenes.length : 0;
        const overviewDuration = this._calculateEstimatedDuration(sectionData.demoScenes || []);

        // Build overview card
        let html = `
            <div class="demo-picker-overview-card" data-section="${sectionId}" data-subdemo="__overview__">
                <div class="demo-picker-overview-icon">&#9654;</div>
                <div class="demo-picker-overview-info">
                    <div class="demo-picker-overview-title">Watch Overview</div>
                    <div class="demo-picker-overview-meta">${overviewScenes} scenes &middot; ~${overviewDuration}</div>
                    <div class="demo-picker-overview-desc">High-level tour of ${sectionData.title}</div>
                </div>
            </div>
        `;

        // Build sub-demo cards grid
        const subDemos = sectionData.subDemos || {};
        const subDemoKeys = Object.keys(subDemos);

        if (subDemoKeys.length > 0) {
            html += `<div class="demo-picker-divider"><span>Deep Dive Demos</span></div>`;
            html += `<div class="demo-picker-grid">`;

            subDemoKeys.forEach(key => {
                const sub = subDemos[key];
                const sceneCount = sub.scenes ? sub.scenes.length : 0;
                const duration = this._calculateEstimatedDuration(sub.scenes || []);
                const iconName = sub.icon || 'play-circle';
                html += `
                    <div class="demo-picker-card" data-section="${sectionId}" data-subdemo="${key}">
                        <div class="demo-picker-card-icon" data-lucide="${iconName}"></div>
                        <div class="demo-picker-card-title">${sub.title}</div>
                        <div class="demo-picker-card-desc">${sub.description || ''}</div>
                        <div class="demo-picker-card-meta">${sceneCount} scenes &middot; ~${duration}</div>
                    </div>
                `;
            });

            html += `</div>`;
        }

        pickerContent.innerHTML = html;

        // Show picker, hide help content
        helpContent.classList.add('hidden');
        picker.classList.remove('hidden');

        // Scroll panel to top so picker is immediately visible
        const panelBody = this.refs.panel.querySelector('.panel-body') || this.refs.panel;
        panelBody.scrollTop = 0;

        // Hide footer buttons when picker is showing
        const footer = this.refs.panel.querySelector('.panel-footer');
        if (footer) footer.classList.add('hidden');

        // Render lucide icons in cards
        if (window.lucide) {
            try { window.lucide.createIcons(); } catch(e) {}
        }

        console.log('[AEGIS Guide] Demo picker shown:', sectionId, '—', subDemoKeys.length, 'sub-demos');
    },

    /**
     * Hide the demo picker and restore normal help panel content.
     */
    _hideDemoPicker() {
        const helpContent = this.refs.panel.querySelector('#guide-panel-help-content');
        const picker = this.refs.panel.querySelector('#guide-demo-picker');

        if (helpContent) helpContent.classList.remove('hidden');
        if (picker) picker.classList.add('hidden');

        // Restore footer buttons
        const footer = this.refs.panel.querySelector('.panel-footer');
        if (footer) footer.classList.remove('hidden');
    },

    /**
     * Calculate estimated duration string from scenes array.
     * Returns e.g. "2 min", "45 sec", "3.5 min"
     */
    _calculateEstimatedDuration(scenes) {
        if (!scenes || scenes.length === 0) return '0 sec';
        let totalMs = 0;
        scenes.forEach(s => {
            totalMs += (s.duration || this.config.demoStepDuration);
        });
        const totalSec = Math.round(totalMs / 1000);
        if (totalSec < 60) return `${totalSec} sec`;
        const mins = (totalSec / 60).toFixed(1);
        return mins.endsWith('.0') ? `${Math.round(totalSec / 60)} min` : `${mins} min`;
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

        // Stop any playing narration from previous step
        this._stopNarration();

        // Update demo bar
        if (scene.sectionLabel) {
            this.refs.demoBar.querySelector('#demo-bar-section').textContent = scene.sectionLabel;
        }
        this.refs.demoBar.querySelector('#demo-step-label').textContent = `${index + 1} / ${total}`;
        this.refs.demoBar.querySelector('#demo-progress-fill').style.width =
            `${((index + 1) / total) * 100}%`;

        // Navigate if needed — but skip if sub-demo already navigated to this section
        // (sub-demo preAction handles tab-level navigation; re-navigating resets to Overview)
        if (scene.navigate) {
            const alreadyInSection = this.demo.currentSubDemo && scene.navigate === this.demo.currentSection;
            if (!alreadyInSection) {
                await this._navigateToSection(scene.navigate);
                await this._wait(500);
            }
        }

        // Narration with typewriter effect
        this._typeNarration(scene.narration);

        // v2.1.0: Start voice narration (parallel with typewriter)
        const sectionId = scene._sectionId || this.demo.currentSection;
        const stepIdx = scene._stepIndex ?? index;
        const narrationPromise = this._playNarration(scene.narration, sectionId, stepIdx);

        // Spotlight target if present
        if (scene.target) {
            const el = document.querySelector(scene.target);
            if (el && el.getBoundingClientRect().width > 0) {
                this.refs.spotlight.classList.remove('hidden');
                this.showSpotlight(el, 'bottom');
                // Hide the tooltip for demo (we use the demo bar instead)
                // Must run AFTER showSpotlight's 350ms setTimeout which sets display:block + visibility:visible
                setTimeout(() => {
                    const tt = this.refs.spotlight.querySelector('.spotlight-tooltip');
                    if (tt) { tt.style.display = 'none'; tt.style.visibility = 'hidden'; }
                }, 400);
            } else {
                this.refs.spotlight.classList.add('hidden');
            }
        } else {
            this.refs.spotlight.classList.add('hidden');
        }

        // Schedule next step — if narration is playing, wait for it to finish
        // (with a minimum display time for short audio clips)
        if (this.demo.timer) clearTimeout(this.demo.timer);
        const baseDuration = (scene.duration || this.config.demoStepDuration) / this.demo.speed;

        if (this.narration.enabled) {
            // Wait for narration to complete, then add a small pause before advancing
            narrationPromise.then((audioPlayed) => {
                if (!this.demo.isPlaying || this.demo.isPaused) return;
                if (this.demo.currentStep !== index) return; // Step changed while waiting

                if (audioPlayed) {
                    // Audio finished — advance after a brief pause
                    this.demo.timer = setTimeout(() => {
                        if (this.demo.isPlaying && !this.demo.isPaused) {
                            this._showDemoStep(index + 1);
                        }
                    }, 800 / this.demo.speed); // 800ms pause between narrated steps
                } else {
                    // No audio played — use standard timer
                    this.demo.timer = setTimeout(() => {
                        if (this.demo.isPlaying && !this.demo.isPaused) {
                            this._showDemoStep(index + 1);
                        }
                    }, baseDuration);
                }
            });
        } else {
            // No narration — use standard timer-based advancement
            this.demo.timer = setTimeout(() => {
                if (this.demo.isPlaying && !this.demo.isPaused) {
                    this._showDemoStep(index + 1);
                }
            }, baseDuration);
        }
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
            this._resumeNarration();
            // Re-trigger next step
            this._showDemoStep(this.demo.currentStep + 1);
        } else {
            // Pause
            this.demo.isPaused = true;
            this.refs.demoBar.querySelector('#demo-play').innerHTML = '&#9654;';
            if (this.demo.timer) clearTimeout(this.demo.timer);
            if (this.demo.typeTimer) clearInterval(this.demo.typeTimer);
            this._pauseNarration();
        }
    },

    demoPrev() {
        if (this.demo.timer) clearTimeout(this.demo.timer);
        this._stopNarration();
        const prev = Math.max(0, this.demo.currentStep - 1);
        this._showDemoStep(prev);
    },

    demoNext() {
        if (this.demo.timer) clearTimeout(this.demo.timer);
        this._stopNarration();
        this._showDemoStep(this.demo.currentStep + 1);
    },

    stopDemo() {
        this.demo.isPlaying = false;
        this.demo.isPaused = false;
        this.demo.currentStep = 0;
        this.demo.currentSubDemo = null;
        this.demo.scenes = null;
        if (this.demo.timer) clearTimeout(this.demo.timer);
        if (this.demo.typeTimer) clearInterval(this.demo.typeTimer);

        // v2.1.0: Stop any playing narration
        this._stopNarration();

        // v5.9.14: Cleanup Fix Assistant modal if it was shown for demo
        if (this._faCleanup) {
            this._faCleanup();
            this._faCleanup = null;
        }
        // v5.9.15: Cleanup other force-shown modals from sub-demos
        if (this._exportCleanup) { this._exportCleanup(); this._exportCleanup = null; }
        if (this._triageCleanup) { this._triageCleanup(); this._triageCleanup = null; }
        if (this._scoreCleanup) { this._scoreCleanup(); this._scoreCleanup = null; }
        if (this._funcTagsCleanup) { this._funcTagsCleanup(); this._funcTagsCleanup = null; }
        if (this._helpCleanup) { this._helpCleanup(); this._helpCleanup = null; }

        // v5.9.16-fix: Close ALL open modals when demo stops.
        // This prevents modals opened by demos (e.g., Settings, Roles Studio)
        // from persisting after stop, blocking subsequent demos.
        if (typeof closeModals === 'function') closeModals();

        // v5.9.16: Cleanup all DemoSimulator injected elements
        if (typeof DemoSimulator !== 'undefined') DemoSimulator.cleanupAll();

        this.refs.demoBar.classList.add('hidden');
        this.refs.spotlight.classList.add('hidden');
        // Re-show tooltip for tour mode
        const tooltip = this.refs.spotlight.querySelector('.spotlight-tooltip');
        if (tooltip) tooltip.style.display = '';
        // Clean up SVG
        const svg = this.refs.spotlight.querySelector('svg.spotlight-mask');
        if (svg) svg.remove();

        // v5.9.18: Re-show help beacon after demo ends
        if (this.refs.beacon) this.refs.beacon.style.display = '';

        console.log('[AEGIS Guide] Demo stopped');
    },

    // ═════════════════════════════════════════════════════════════════
    // NAVIGATION HELPERS
    // ═════════════════════════════════════════════════════════════════

    async _navigateToSection(sectionId) {
        console.log('[AEGIS Guide] Navigating to section:', sectionId);

        // v5.9.16: Cleanup DemoSimulator injected elements on section change
        if (typeof DemoSimulator !== 'undefined') DemoSimulator.cleanupAll();

        // v5.7.1: Close all open modals first to prevent stacking.
        if (typeof closeModals === 'function') closeModals();

        // v5.9.16-fix: Close the Document Compare picker overlay which is
        // not a regular .modal.active and survives closeModals()
        const comparePicker = document.getElementById('compare-picker-overlay');
        if (comparePicker) comparePicker.style.display = 'none';

        // v5.9.14: Cleanup Fix Assistant modal if it was shown for demo
        if (this._faCleanup) {
            this._faCleanup();
            this._faCleanup = null;
        }
        // v5.9.15: Cleanup other force-shown modals from sub-demos
        if (this._exportCleanup) { this._exportCleanup(); this._exportCleanup = null; }
        if (this._triageCleanup) { this._triageCleanup(); this._triageCleanup = null; }
        if (this._scoreCleanup) { this._scoreCleanup(); this._scoreCleanup = null; }
        if (this._funcTagsCleanup) { this._funcTagsCleanup(); this._funcTagsCleanup = null; }
        if (this._helpCleanup) { this._helpCleanup(); this._helpCleanup = null; }

        // v5.7.1: Dismiss the landing page for any non-landing section.
        // Without this, modals open BEHIND the landing page overlay.
        if (sectionId !== 'landing' && document.body.classList.contains('landing-active')) {
            const landing = document.getElementById('aegis-landing-page');
            if (landing) {
                landing.classList.add('lp-exiting');
                document.body.classList.remove('landing-active');
            }
        }

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
                // Landing page already dismissed above — review view is now visible
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
            'sow': () => {
                if (window.SowGenerator?.open) window.SowGenerator.open();
                else if (_showModal) _showModal('modal-sow-generator');
            },
            'validator': () => {
                if (window.HyperlinkValidator && typeof window.HyperlinkValidator.open === 'function') {
                    window.HyperlinkValidator.open();
                } else if (_showModal) _showModal('modal-hyperlink-validator');
            },
            'compare': async () => {
                // Close any leftover picker overlays
                document.querySelectorAll('.compare-picker-overlay').forEach(el => el.remove());
                // Try to open DocCompare with a real document (auto-pick first comparable doc)
                if (window.DocCompare?.open) {
                    try {
                        const resp = await fetch('/api/scan-history?limit=100');
                        const data = await resp.json();
                        const scans = data.data || data.scans || [];
                        // Find a document with 2+ scans
                        const docCounts = {};
                        scans.forEach(s => {
                            const k = s.document_id;
                            if (!docCounts[k]) docCounts[k] = { id: k, count: 0 };
                            docCounts[k].count++;
                        });
                        const comparableDoc = Object.values(docCounts).find(d => d.count >= 2 && d.id);
                        if (comparableDoc) {
                            window.DocCompare.open(comparableDoc.id);
                            return;
                        }
                    } catch (e) {
                        console.warn('[AEGIS Guide] Could not auto-open DocCompare:', e);
                    }
                }
                // Fallback to picker if no comparable doc found
                if (typeof openCompareFromNav === 'function') {
                    openCompareFromNav();
                } else {
                    document.querySelector('#nav-compare')?.click();
                }
            },
            'metrics': () => {
                // v5.9.14: Use MetricsAnalytics.open() to properly load data + render
                if (window.MetricsAnalytics?.open) window.MetricsAnalytics.open();
                else if (_showModal) _showModal('modal-metrics-analytics');
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
            { id: 'aegis-landing-page', section: 'landing', check: () => document.body.classList.contains('landing-active') },
            { id: 'modal-roles', section: 'roles', check: el => el.classList.contains('active') },
            { id: 'modal-statement-forge', section: 'forge', check: el => el.classList.contains('active') },
            { id: 'batch-upload-modal', section: 'batch', check: el => el.classList.contains('active') },
            { id: 'modal-sow-generator', section: 'sow', check: el => el.classList.contains('active') || el.style.display === 'flex' },
            { id: 'modal-hyperlink-validator', section: 'validator', check: el => el.classList.contains('active') },
            { id: 'modal-doc-compare', section: 'compare', check: el => el.classList.contains('active') },
            { id: 'modal-metrics-analytics', section: 'metrics', check: el => el.classList.contains('active') },
            { id: 'modal-scan-history', section: 'history', check: el => el.classList.contains('active') },
            { id: 'modal-settings', section: 'settings', check: el => el.classList.contains('active') },
            { id: 'modal-portfolio', section: 'portfolio', check: el => el.classList.contains('active') }
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
