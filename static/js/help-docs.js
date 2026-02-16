/**
 * AEGIS Help Documentation System
 * ==========================================
 * Comprehensive documentation for all features.
 * Version: 5.1.0
 *
 * Complete overhaul with:
 * - Beautiful visual design with icons and illustrations
 * - Detailed explanations of "how" and "why" for every feature
 * - Technical deep-dive section for advanced users
 * - Smooth navigation and professional typography
 *
 * v5.4.0 - Performance Optimization + spaCy Ecosystem Deep Analysis (zero dark mode flash, deferred scripts, parallel batch scan, 100+ checkers)
 * v5.1.0 - Security Hardening + Accessibility + Print Support (CSRF protection, WCAG 2.1 A compliance, print.css, folder browser, Windows wheels)
 * v5.0.0 - Multiprocessing Architecture + Role Extraction (separate processes, 3-layer filtering, 30+ aerospace roles, NASA 297-page test)
 * v4.9.9 - Statement Source Viewer & Error Handling (highlight-to-select editing, SOW fixes, timezone import, error message extraction)
 * v4.9.5 - Version Management Overhaul (get_version(), cache-busting regex, duplicate version.json fix)
 * v4.9.0 - Landing Page Stability + Offline Distribution (async init race condition, toast z-index, offline wheels)
 * v4.8.0 - E2E Audit + Report Fixes (Flask blueprint imports, popup blocker, SQL JOINs, production logging)
 * v4.7.0 - Database Access Layer Refactoring (99 sqlite3.connect() calls → db_connection() context manager, 10 bug fixes)
 * v4.4.0 - Statement Enhancements (search, bulk edit, PDF.js viewer, diff export, clean text quality)
 * v4.3.0 - Document Extraction Overhaul (mammoth DOCX→HTML, pymupdf4llm PDF→Markdown, HTML document viewer, AEGIS installer)
 * v4.2.0 - Statement Forge History (persistent statements, history viewer, scan comparison, document viewer, technical docs)
 * v4.1.0 - Nimbus SIPOC Import & Role Hierarchy (SIPOC parser, hierarchy view, HTML export, disposition tracking)
 * v4.0.5 - Role Dictionary Complete Overhaul (Dashboard, card view, bulk ops, keyboard nav, inline actions)
 * v4.0.4 - Import Enhancements & PDF Export (Diff preview, versioning, PDF report, progress indicators)
 * v4.0.3 - Adjudication Tab Complete Overhaul (Auto-classify, kanban, function tags, keyboard nav)
 * v4.0.2 - Roles Studio UI Enhancements (Dark mode, RACI deduplication, explore buttons)
 * v4.0.0 - AEGIS Rebrand Release (Complete rebrand from TechWriterReview)
 * v3.4.0 - Maximum Coverage Suite (23 new checkers)
 * v3.3.0 - Maximum Accuracy NLP Enhancement Suite documentation
 * v3.2.0 - Added Role Source Viewer with Adjudication documentation
 */

'use strict';

const HelpDocs = {
    version: '5.1.0',
    lastUpdated: '2026-02-16',
    
    config: {
        searchEnabled: true,
        printEnabled: true,
        keyboardNav: true,
        rememberPosition: true
    },
    
    navigation: [
        { id: 'getting-started', title: 'Getting Started', icon: 'rocket', subsections: [
            { id: 'welcome', title: 'Welcome', icon: 'home' },
            { id: 'quick-start', title: 'Quick Start Guide', icon: 'zap' },
            { id: 'first-review', title: 'Your First Review', icon: 'play-circle' },
            { id: 'interface-tour', title: 'Interface Tour', icon: 'layout' }
        ]},
        { id: 'document-review', title: 'Document Review', icon: 'file-search', subsections: [
            { id: 'loading-docs', title: 'Loading Documents', icon: 'upload' },
            { id: 'review-types', title: 'Review Presets', icon: 'sliders' },
            { id: 'understanding-results', title: 'Understanding Results', icon: 'bar-chart-2' },
            { id: 'triage-mode', title: 'Triage Mode', icon: 'check-square' },
            { id: 'issue-families', title: 'Issue Families', icon: 'layers' }
        ]},
        { id: 'checkers', title: 'Quality Checkers', icon: 'check-square', subsections: [
            { id: 'checker-overview', title: 'Overview', icon: 'list' },
            { id: 'checker-acronyms', title: 'Acronym Checker', icon: 'a-large-small' },
            { id: 'checker-grammar', title: 'Grammar & Spelling', icon: 'spell-check' },
            { id: 'checker-hyperlinks', title: 'Hyperlink Checker', icon: 'link' },
            { id: 'checker-requirements', title: 'Requirements Language', icon: 'list-checks' },
            { id: 'checker-writing', title: 'Writing Quality', icon: 'pen-tool' },
            { id: 'checker-structure', title: 'Document Structure', icon: 'file-text' },
            { id: 'checker-all', title: 'Complete Reference', icon: 'book-open' }
        ]},
        { id: 'roles', title: 'Roles Studio', icon: 'users', subsections: [
            { id: 'role-overview', title: 'Overview', icon: 'info' },
            { id: 'role-detection', title: 'Role Detection', icon: 'user-search' },
            { id: 'role-source-viewer', title: 'Source Viewer', icon: 'file-text' },
            { id: 'role-adjudication', title: 'Adjudication', icon: 'check-circle' },
            { id: 'role-export-import', title: 'Export & Import', icon: 'arrow-left-right' },
            { id: 'role-sharing', title: 'Sharing Roles', icon: 'share-2' },
            { id: 'role-graph', title: 'Relationship Graph', icon: 'git-branch' },
            { id: 'role-matrix', title: 'RACI Matrix', icon: 'grid-3x3' },
            { id: 'role-crossref', title: 'Cross-Reference', icon: 'table' },
            { id: 'role-dictionary', title: 'Role Dictionary', icon: 'book' },
            { id: 'role-sipoc-import', title: 'Nimbus SIPOC Import', icon: 'git-branch' },
            { id: 'role-template', title: 'Role Import Template', icon: 'file-plus' },
            { id: 'role-hierarchy', title: 'Role Inheritance', icon: 'git-branch' },
            { id: 'role-documents', title: 'Document Log', icon: 'file-text' },
            { id: 'role-data-explorer', title: 'Data Explorer', icon: 'bar-chart-3' },
            { id: 'role-smart-search', title: 'SmartSearch', icon: 'search' }
        ]},
        { id: 'statement-forge', title: 'Statement Forge', icon: 'hammer', subsections: [
            { id: 'forge-overview', title: 'Overview', icon: 'info' },
            { id: 'forge-extraction', title: 'Statement Extraction', icon: 'filter' },
            { id: 'forge-editing', title: 'Editing Statements', icon: 'edit-3' },
            { id: 'forge-history', title: 'Statement History', icon: 'history' },
            { id: 'forge-search', title: 'Statement Search', icon: 'search' },
            { id: 'forge-bulk-edit', title: 'Bulk Editing', icon: 'check-square' },
            { id: 'forge-pdf-viewer', title: 'PDF Viewer', icon: 'file' },
            { id: 'forge-diff-export', title: 'Diff Export', icon: 'download' },
            { id: 'forge-export', title: 'Export Formats', icon: 'download' }
        ]},
        { id: 'fix-assistant', title: 'Fix Assistant', icon: 'wand-2', subsections: [
            { id: 'fix-overview', title: 'Overview', icon: 'info' },
            { id: 'fix-workflow', title: 'Review Workflow', icon: 'workflow' },
            { id: 'fix-learning', title: 'Pattern Learning', icon: 'brain' },
            { id: 'fix-export', title: 'Export Options', icon: 'download' }
        ]},
        { id: 'hyperlink-health', title: 'Hyperlink Health', icon: 'link', subsections: [
            { id: 'hyperlink-overview', title: 'Overview', icon: 'info' },
            { id: 'hyperlink-validation', title: 'URL Validation', icon: 'check-circle' },
            { id: 'hyperlink-status', title: 'Status Codes', icon: 'activity' }
        ]},
        { id: 'batch-processing', title: 'Batch Processing', icon: 'layers', subsections: [
            { id: 'batch-overview', title: 'Overview', icon: 'info' },
            { id: 'batch-queue', title: 'Queue Management', icon: 'list' },
            { id: 'batch-results', title: 'Consolidated Results', icon: 'bar-chart-2' }
        ]},
        { id: 'exporting', title: 'Exporting Results', icon: 'download', subsections: [
            { id: 'export-overview', title: 'Export Options', icon: 'info' },
            { id: 'export-word', title: 'Word Document', icon: 'file-text' },
            { id: 'export-data', title: 'CSV & Excel', icon: 'table' },
            { id: 'export-json', title: 'JSON Data', icon: 'code' }
        ]},
        { id: 'settings', title: 'Settings', icon: 'settings', subsections: [
            { id: 'settings-general', title: 'General', icon: 'sliders' },
            { id: 'settings-appearance', title: 'Appearance', icon: 'palette' },
            { id: 'settings-sharing', title: 'Sharing', icon: 'share-2' },
            { id: 'settings-updates', title: 'Updates', icon: 'refresh-cw' }
        ]},
        { id: 'shortcuts', title: 'Keyboard Shortcuts', icon: 'keyboard' },
        { id: 'technical', title: 'Technical Deep Dive', icon: 'cpu', subsections: [
            { id: 'tech-architecture', title: 'Architecture Overview', icon: 'layers' },
            { id: 'tech-checkers', title: 'Checker Engine', icon: 'cog' },
            { id: 'tech-extraction', title: 'Document Extraction', icon: 'file-code' },
            { id: 'tech-docling', title: 'Docling AI Engine', icon: 'sparkles' },
            { id: 'tech-roles', title: 'Role Extraction', icon: 'users' },
            { id: 'tech-statement-forge', title: 'Statement Forge Engine', icon: 'hammer' },
            { id: 'tech-nlp', title: 'NLP Pipeline', icon: 'brain' },
            { id: 'tech-api', title: 'API Reference', icon: 'code' }
        ]},
        { id: 'troubleshooting', title: 'Troubleshooting', icon: 'wrench', subsections: [
            { id: 'trouble-common', title: 'Common Issues', icon: 'alert-circle' },
            { id: 'trouble-errors', title: 'Error Messages', icon: 'alert-triangle' },
            { id: 'trouble-performance', title: 'Performance', icon: 'gauge' }
        ]},
        { id: 'version-history', title: 'Version History', icon: 'history' },
        { id: 'about', title: 'About', icon: 'info' }
    ],

    content: {}
};

// ============================================================================
// WELCOME
// ============================================================================
HelpDocs.content['welcome'] = {
    title: 'Welcome to AEGIS',
    subtitle: 'Enterprise-grade document analysis for technical writers',
    html: `
<div class="help-hero">
    <div class="help-hero-icon">
        <i data-lucide="file-search" class="hero-icon-main"></i>
    </div>
    <div class="help-hero-content">
        <p class="help-hero-tagline">Transform your technical documents from good to exceptional</p>
        <p>AEGIS is a comprehensive document analysis platform that combines <strong>84 quality checks</strong>, <strong>AI-powered role extraction</strong>, <strong>statement extraction for process modeling</strong>, and <strong>intelligent fix assistance</strong>—all running locally without internet access.</p>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="award"></i>
    <div>
        <strong>Enterprise-Grade Capabilities</strong>
        <p>Validated on government SOWs, defense SEPs, systems engineering management plans, and industry standards. Role extraction achieves <strong>94.7% precision</strong> and <strong>92.3% F1 score</strong>.</p>
    </div>
</div>

<h2><i data-lucide="layers"></i> Core Capabilities</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="shield-check"></i></div>
        <h3>84 Quality Checks</h3>
        <p>Grammar, spelling, acronyms, passive voice, requirements language (shall/must/will), sentence complexity, document structure, and hyperlink validation.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="users"></i></div>
        <h3>Roles & Responsibilities Studio</h3>
        <p>AI-powered role extraction with RACI matrix generation, relationship graphs, cross-document tracking, adjudication workflow, and role dictionary management.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="hammer"></i></div>
        <h3>Statement Forge</h3>
        <p>Extract requirements, procedures, and action items. Export to TIBCO Nimbus XML, Excel, CSV, or JSON. Supports Actor-Action-Object decomposition.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="wand-2"></i></div>
        <h3>Fix Assistant v2</h3>
        <p>Premium triage interface with confidence scoring, before/after comparison, pattern learning, undo/redo, and export with tracked changes or comments.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="link"></i></div>
        <h3>Hyperlink Health</h3>
        <p>Validate all URLs in your document. Check for broken links, redirects, SSL issues, and missing destinations with detailed status reporting.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="layers"></i></div>
        <h3>Batch Processing</h3>
        <p>Process multiple documents at once. Queue management, progress tracking, and consolidated results across your document library.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="bar-chart-2"></i></div>
        <h3>Metrics & Analytics</h3>
        <p>Quality score dashboards, severity distribution charts, category heatmaps, trend analysis, and exportable reports.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="wifi-off"></i></div>
        <h3>Air-Gapped Ready</h3>
        <p>100% local processing. No cloud dependencies. Designed for classified and secure environments. Offline NLP and document parsing.</p>
    </div>
</div>

<h2><i data-lucide="file-type"></i> Supported File Formats</h2>
<div class="help-formats" style="margin-bottom: 24px;">
    <span class="format-badge format-primary">.docx (Word)</span>
    <span class="format-badge">.pdf</span>
    <span class="format-badge">.txt</span>
    <span class="format-badge">.rtf</span>
    <span class="format-badge">.md (Markdown)</span>
</div>
<p>Word documents (.docx) provide the richest analysis including tracked changes export, comment insertion, and hyperlink extraction.</p>

<h2><i data-lucide="compass"></i> Where to Start</h2>

<div class="help-start-paths">
    <div class="help-path-card" onclick="HelpContent.navigateTo('quick-start')">
        <div class="help-path-icon"><i data-lucide="zap"></i></div>
        <div class="help-path-content">
            <h4>Quick Start Guide</h4>
            <p>Get your first review done in under 60 seconds</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('interface-tour')">
        <div class="help-path-icon"><i data-lucide="layout"></i></div>
        <div class="help-path-content">
            <h4>Interface Tour</h4>
            <p>Learn your way around the workspace</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('checker-overview')">
        <div class="help-path-icon"><i data-lucide="check-square"></i></div>
        <div class="help-path-content">
            <h4>Quality Checkers</h4>
            <p>Understand what each of 50+ checks does</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-overview')">
        <div class="help-path-icon"><i data-lucide="users"></i></div>
        <div class="help-path-content">
            <h4>Roles Studio</h4>
            <p>AI role extraction and RACI matrices</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-overview')">
        <div class="help-path-icon"><i data-lucide="hammer"></i></div>
        <div class="help-path-content">
            <h4>Statement Forge</h4>
            <p>Extract requirements and procedures</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('tech-architecture')">
        <div class="help-path-icon"><i data-lucide="cpu"></i></div>
        <div class="help-path-content">
            <h4>Technical Deep Dive</h4>
            <p>Architecture, APIs, and internals</p>
        </div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
</div>

<h2><i data-lucide="settings-2"></i> Document Type Profiles</h2>
<p>Configure which quality checks run for different document types. Customize profiles for:</p>
<div class="help-formats" style="margin-bottom: 16px;">
    <span class="format-badge format-primary">PrOP</span>
    <span class="format-badge">PAL</span>
    <span class="format-badge">FGOST</span>
    <span class="format-badge">SOW</span>
</div>
<p>Custom profiles persist across sessions. Access via <strong>Settings → Document Profiles</strong> or use the preset buttons in the sidebar.</p>

<h2><i data-lucide="link-2"></i> Link History & Exclusions</h2>
<p>The new <strong>Links</strong> button in the top navigation provides:</p>
<ul style="margin-left: 20px;">
    <li><strong>Persistent URL Exclusions</strong> - Create rules to skip certain URLs during validation (supports regex)</li>
    <li><strong>Scan History</strong> - View historical hyperlink scans with statistics and details</li>
    <li><strong>Match Types</strong> - Filter by contains, exact, prefix, suffix, or regex patterns</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tips</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
            <li>Press <kbd>?</kbd> anytime to see keyboard shortcuts</li>
            <li>Press <kbd>F1</kbd> to open this help</li>
            <li>Press <kbd>Ctrl</kbd>+<kbd>R</kbd> to run a review</li>
            <li>Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd> to open Roles Studio</li>
            <li>Press <kbd>Ctrl</kbd>+<kbd>E</kbd> to export results</li>
            <li>In Fix Assistant: <kbd>A</kbd>=Accept, <kbd>R</kbd>=Reject, <kbd>S</kbd>=Skip, <kbd>U</kbd>=Undo</li>
        </ul>
    </div>
</div>
`
};

// ============================================================================
// QUICK START
// ============================================================================
HelpDocs.content['quick-start'] = {
    title: 'Quick Start Guide',
    subtitle: 'Get your first document review done in under 60 seconds',
    html: `
<div class="help-intro-box">
    <p>AEGIS is designed to get out of your way and let you focus on your documents. Follow these five steps to run your first review.</p>
</div>

<div class="help-steps-visual">
    <div class="help-step-visual">
        <div class="help-step-number">1</div>
        <div class="help-step-visual-content">
            <h3>Load Your Document</h3>
            <p>Drag and drop a file onto the window, or click <strong>Open</strong> in the sidebar.</p>
            <div class="help-formats">
                <span class="format-badge format-primary">.docx</span>
                <span class="format-badge">.pdf</span>
                <span class="format-badge">.txt</span>
                <span class="format-badge">.rtf</span>
            </div>
            <div class="help-tip-inline">
                <i data-lucide="star"></i>
                <span>Word documents (.docx) provide the richest analysis including tracked changes export.</span>
            </div>
        </div>
    </div>

    <div class="help-step-visual">
        <div class="help-step-number">2</div>
        <div class="help-step-visual-content">
            <h3>Choose Your Checks</h3>
            <p>Select a preset that matches your document type:</p>
            <div class="help-preset-grid">
                <div class="help-preset-item"><strong>All</strong><span>Every check enabled</span></div>
                <div class="help-preset-item"><strong>PrOP</strong><span>Procedures</span></div>
                <div class="help-preset-item"><strong>PAL</strong><span>Process Assets</span></div>
                <div class="help-preset-item"><strong>FGOST</strong><span>Flight/Ground Ops</span></div>
                <div class="help-preset-item"><strong>SOW</strong><span>Statement of Work</span></div>
            </div>
        </div>
    </div>

    <div class="help-step-visual">
        <div class="help-step-number">3</div>
        <div class="help-step-visual-content">
            <h3>Run the Review</h3>
            <p>Click <strong>Review</strong> or press <kbd>Ctrl</kbd>+<kbd>R</kbd>.</p>
            <div class="help-timing-info">
                <div class="help-timing-item"><span class="timing-pages">1-10 pages</span><span class="timing-duration">5-10 sec</span></div>
                <div class="help-timing-item"><span class="timing-pages">10-50 pages</span><span class="timing-duration">10-30 sec</span></div>
                <div class="help-timing-item"><span class="timing-pages">50+ pages</span><span class="timing-duration">30-120 sec</span></div>
            </div>
        </div>
    </div>

    <div class="help-step-visual">
        <div class="help-step-number">4</div>
        <div class="help-step-visual-content">
            <h3>Review the Results</h3>
            <p>Issues appear sorted by severity. The dashboard shows:</p>
            <ul class="help-checklist">
                <li><i data-lucide="check"></i> <strong>Quality Score</strong> — Letter grade based on issue density</li>
                <li><i data-lucide="check"></i> <strong>Severity Chart</strong> — Click segments to filter</li>
                <li><i data-lucide="check"></i> <strong>Readability Metrics</strong> — Flesch, FK Grade, Fog Index</li>
            </ul>
        </div>
    </div>

    <div class="help-step-visual">
        <div class="help-step-number">5</div>
        <div class="help-step-visual-content">
            <h3>Export Your Results</h3>
            <p>Click <strong>Export</strong> to create deliverables:</p>
            <div class="help-export-options">
                <div class="help-export-option">
                    <i data-lucide="file-text"></i>
                    <div><strong>Word</strong><span>Tracked changes & comments</span></div>
                </div>
                <div class="help-export-option">
                    <i data-lucide="table"></i>
                    <div><strong>CSV/Excel</strong><span>Tabular tracking</span></div>
                </div>
                <div class="help-export-option">
                    <i data-lucide="code"></i>
                    <div><strong>JSON</strong><span>Automation</span></div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="party-popper"></i>
    <div>
        <strong>That's It!</strong>
        <p>You've completed your first review. Explore the sidebar to learn about advanced features like Fix Assistant, role extraction, and Statement Forge.</p>
    </div>
</div>

<h2><i data-lucide="wand-2"></i> Next Step: Fix Assistant</h2>
<p>After reviewing results, click <strong>Fix Assistant</strong> to enter the premium triage interface:</p>
<ul>
    <li><strong>Confidence Scoring</strong> — Each fix has a Safe/Review/Manual confidence level</li>
    <li><strong>Accept/Reject/Skip</strong> — Use buttons or keyboard shortcuts (<kbd>A</kbd>/<kbd>R</kbd>/<kbd>S</kbd>)</li>
    <li><strong>Undo/Redo</strong> — Press <kbd>U</kbd> or <kbd>Shift</kbd>+<kbd>U</kbd> to reverse decisions</li>
    <li><strong>Pattern Learning</strong> — The tool learns from your decisions to improve future suggestions</li>
    <li><strong>Export Options</strong> — Accepted fixes become tracked changes; rejected fixes become comments</li>
</ul>

<h2><i data-lucide="users"></i> Explore Roles Studio</h2>
<p>Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd> or click <strong>Roles & Responsibilities</strong> to open Roles Studio:</p>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="search"></i></div>
        <h3>SmartSearch</h3>
        <p>Instant autocomplete search across all roles. Type to find roles by name or category with fuzzy matching.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="bar-chart-3"></i></div>
        <h3>Data Explorer</h3>
        <p>Interactive analytics with drill-down charts. Click any chart segment to explore role distributions.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="file-text"></i></div>
        <h3>Source Viewer</h3>
        <p>Click any role name to see it highlighted in the original document text with full context.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="grid-3x3"></i></div>
        <h3>RACI Matrix</h3>
        <p>Auto-generated responsibility matrix with deduplicated counts matching the Overview.</p>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Quick Tip: Explore Button</strong>
        <p>In Role Details, each role card has an explore icon (🔍+). Click it to jump directly to that role's Data Explorer view with full analytics.</p>
    </div>
</div>

<h2><i data-lucide="package"></i> Complete Setup</h2>

<p>Running <code>setup.bat</code> installs all enhancement libraries automatically:</p>

<pre class="help-code">
# Run from AEGIS folder
setup.bat
</pre>

<p>This installs:</p>
<ul>
    <li><strong>Multi-library table extraction</strong> — Camelot, Tabula, pdfplumber (~88% accuracy)</li>
    <li><strong>OCR support</strong> — Tesseract for scanned PDFs</li>
    <li><strong>NLP enhancement</strong> — spaCy, sklearn for better role detection (~90% accuracy)</li>
    <li><strong>Grammar checking</strong> — LanguageTool integration</li>
</ul>

<h2><i data-lucide="sparkles"></i> Optional: AI Extraction with Docling</h2>

<p>For maximum accuracy (+7% on all metrics), also install Docling:</p>

<pre class="help-code">
# Additional step for AI-powered extraction
setup_docling.bat
</pre>

<p>This adds:</p>
<ul>
    <li><strong>AI-powered table recognition</strong> — 95% accuracy vs 88% without</li>
    <li><strong>Layout understanding</strong> — Correct reading order in complex documents</li>
    <li><strong>Section detection</strong> — Identifies headings without style dependencies</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="shield"></i>
    <div>
        <strong>Offline Operation</strong>
        <p>All extraction runs 100% offline. No data leaves your machine. See Technical → Document Extraction for details.</p>
    </div>
</div>
`
};

// ============================================================================
// FIRST REVIEW (DETAILED)
// ============================================================================
HelpDocs.content['first-review'] = {
    title: 'Your First Review',
    subtitle: 'A detailed walkthrough of the complete review process',
    html: `
<p>This guide walks you through a complete document review, explaining each step in detail.</p>

<h2><i data-lucide="file-plus"></i> Before You Begin</h2>
<p>Ensure you have:</p>
<ul>
    <li>A document ready to review (.docx recommended for full features)</li>
    <li>AEGIS running at <code>http://127.0.0.1:5050</code></li>
    <li>Time for thorough review—about 15 minutes for a 50-page document</li>
</ul>

<h2><i data-lucide="upload"></i> Step 1: Load Your Document</h2>

<h3>Loading Methods</h3>
<table class="help-table help-table-striped">
    <thead><tr><th>Method</th><th>How</th><th>Best For</th></tr></thead>
    <tbody>
        <tr><td><strong>Drag & Drop</strong></td><td>Drag file from Explorer onto window</td><td>Fastest for single files</td></tr>
        <tr><td><strong>Open Button</strong></td><td>Click Open in sidebar, browse</td><td>When navigating folders</td></tr>
        <tr><td><strong>Keyboard</strong></td><td><kbd>Ctrl</kbd>+<kbd>O</kbd></td><td>Power users</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Why Word Documents Are Preferred</strong>
        <p>Word (.docx) files preserve document structure including headings, lists, and formatting. This enables tracked changes export and accurate paragraph-level context. PDFs work but are limited to text analysis.</p>
    </div>
</div>

<h2><i data-lucide="sliders"></i> Step 2: Configure Your Checks</h2>

<h3>For Requirements Documents</h3>
<div class="help-recommendation-box">
    <div class="help-recommend-enable">
        <h4><i data-lucide="check-circle"></i> Enable</h4>
        <ul>
            <li>Requirements language (shall/will/must)</li>
            <li>TBD/TBR detection</li>
            <li>Undefined acronyms</li>
            <li>Role extraction</li>
        </ul>
    </div>
</div>

<h3>For Work Instructions</h3>
<div class="help-recommendation-box">
    <div class="help-recommend-enable">
        <h4><i data-lucide="check-circle"></i> Enable</h4>
        <ul>
            <li>Passive voice detection</li>
            <li>Imperative mood</li>
            <li>Wordy phrases</li>
            <li>Step numbering</li>
        </ul>
    </div>
</div>

<h2><i data-lucide="play"></i> Step 3: Run the Analysis</h2>
<p>Click <strong>Review</strong> or press <kbd>Ctrl</kbd>+<kbd>R</kbd>. The progress indicator shows the current checker, percentage complete, and estimated time remaining.</p>

<h2><i data-lucide="bar-chart-2"></i> Step 4: Interpret the Results</h2>

<h3>Quality Score</h3>
<table class="help-table">
    <thead><tr><th>Grade</th><th>Issues/1K Words</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td><span class="grade-badge grade-a">A+/A</span></td><td>0-5</td><td>Excellent—ready for final review</td></tr>
        <tr><td><span class="grade-badge grade-b">B+/B</span></td><td>6-15</td><td>Good—minor improvements needed</td></tr>
        <tr><td><span class="grade-badge grade-c">C+/C</span></td><td>16-30</td><td>Acceptable—address before stakeholder review</td></tr>
        <tr><td><span class="grade-badge grade-d">D</span></td><td>31-50</td><td>Below standard—significant rework</td></tr>
        <tr><td><span class="grade-badge grade-f">F</span></td><td>50+</td><td>Poor—comprehensive revision required</td></tr>
    </tbody>
</table>

<h2><i data-lucide="check-square"></i> Step 5: Triage and Export</h2>
<p>Use <strong>Triage Mode</strong> (<kbd>T</kbd>) to systematically review each issue:</p>
<div class="help-key-actions">
    <div class="help-key-action"><kbd>K</kbd><span>Keep (include in export)</span></div>
    <div class="help-key-action"><kbd>S</kbd><span>Suppress (false positive)</span></div>
    <div class="help-key-action"><kbd>F</kbd><span>Fixed (already addressed)</span></div>
    <div class="help-key-action"><kbd>Space</kbd><span>Skip to next</span></div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Issue Families Save Time</strong>
        <p>When the same word is flagged multiple times, AEGIS groups them into a "family." Apply a decision to the entire family at once with <kbd>Shift</kbd>+action key.</p>
    </div>
</div>
`
};

// ============================================================================
// INTERFACE TOUR
// ============================================================================
HelpDocs.content['interface-tour'] = {
    title: 'Interface Tour',
    subtitle: 'Understanding the AEGIS workspace',
    html: `
<p>The AEGIS interface is organized into distinct areas, each with a specific purpose.</p>

<div class="help-interface-diagram">
    <div class="help-interface-area help-interface-sidebar">
        <span class="help-area-label">① Sidebar</span>
        <span class="help-area-desc">Commands & Config</span>
    </div>
    <div class="help-interface-main">
        <div class="help-interface-area help-interface-dashboard">
            <span class="help-area-label">② Dashboard</span>
            <span class="help-area-desc">Metrics & Charts</span>
        </div>
        <div class="help-interface-area help-interface-results">
            <span class="help-area-label">③ Results Panel</span>
            <span class="help-area-desc">Issue List</span>
        </div>
    </div>
    <div class="help-interface-area help-interface-footer">
        <span class="help-area-label">④ Footer</span>
        <span class="help-area-desc">Tools & Status</span>
    </div>
</div>

<h2><i data-lucide="panel-left"></i> ① Sidebar</h2>
<p>The command center for document operations. Press <kbd>Ctrl</kbd>+<kbd>B</kbd> to toggle.</p>

<h3>Action Buttons</h3>
<table class="help-table">
    <thead><tr><th>Button</th><th>Function</th><th>Shortcut</th></tr></thead>
    <tbody>
        <tr><td><strong>Open</strong></td><td>Load a document</td><td><kbd>Ctrl</kbd>+<kbd>O</kbd></td></tr>
        <tr><td><strong>Review</strong></td><td>Run analysis</td><td><kbd>Ctrl</kbd>+<kbd>R</kbd></td></tr>
        <tr><td><strong>Export</strong></td><td>Generate deliverables</td><td><kbd>Ctrl</kbd>+<kbd>E</kbd></td></tr>
    </tbody>
</table>

<h3>Presets</h3>
<ul>
    <li><strong>All</strong> — Enable every checker</li>
    <li><strong>None</strong> — Start fresh</li>
    <li><strong>PrOP</strong> — Procedures & Operating Procedures</li>
    <li><strong>PAL</strong> — Process Asset Library</li>
    <li><strong>FGOST</strong> — Flight/Ground Operations</li>
    <li><strong>SOW</strong> — Statement of Work</li>
</ul>

<h2><i data-lucide="layout-dashboard"></i> ② Dashboard</h2>
<p>At-a-glance metrics after each review:</p>
<ul>
    <li><strong>Quality Score</strong> — Letter grade (A+ through F)</li>
    <li><strong>Severity Chart</strong> — Interactive pie chart (click to filter)</li>
    <li><strong>Readability</strong> — Flesch, FK Grade, Fog Index</li>
</ul>

<h2><i data-lucide="list"></i> ③ Results Panel</h2>
<p>The main working area showing all identified issues.</p>
<ul>
    <li><strong>Filter Bar</strong> — Severity, category, search, status</li>
    <li><strong>Issue Cards</strong> — Click for details, use Triage Mode for systematic review</li>
</ul>

<h2><i data-lucide="panel-bottom"></i> ④ Footer</h2>
<p>Access additional tools:</p>
<div class="help-footer-tools">
    <div class="help-footer-tool"><i data-lucide="history"></i><div><strong>Scan History</strong><p>Previous reviews</p></div></div>
    <div class="help-footer-tool"><i data-lucide="settings"></i><div><strong>Settings</strong><p>Configuration</p></div></div>
    <div class="help-footer-tool"><i data-lucide="users"></i><div><strong>Roles</strong><p>RACI matrix</p></div></div>
    <div class="help-footer-tool"><i data-lucide="hammer"></i><div><strong>Statement Forge</strong><p>Extract requirements</p></div></div>
    <div class="help-footer-tool"><i data-lucide="help-circle"></i><div><strong>Help</strong><p><kbd>F1</kbd></p></div></div>
</div>
`
};

// ============================================================================
// LOADING DOCUMENTS
// ============================================================================
HelpDocs.content['loading-docs'] = {
    title: 'Loading Documents',
    subtitle: 'Supported formats, loading methods, and best practices',
    html: `
<h2><i data-lucide="file"></i> Supported Formats</h2>
<table class="help-table help-table-striped">
    <thead><tr><th>Format</th><th>Extension</th><th>Features</th><th>Best For</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Word Document</strong></td>
            <td><code>.docx</code></td>
            <td><span class="feature-yes">✓</span> Full analysis, track changes</td>
            <td>Primary use—specifications, requirements</td>
        </tr>
        <tr>
            <td><strong>PDF</strong></td>
            <td><code>.pdf</code></td>
            <td><span class="feature-yes">✓</span> Text extraction</td>
            <td>Final/published documents</td>
        </tr>
        <tr>
            <td><strong>Plain Text</strong></td>
            <td><code>.txt</code></td>
            <td><span class="feature-yes">✓</span> Full text analysis</td>
            <td>Code documentation, READMEs</td>
        </tr>
        <tr>
            <td><strong>Rich Text</strong></td>
            <td><code>.rtf</code></td>
            <td><span class="feature-partial">~</span> Basic formatting</td>
            <td>Cross-platform documents</td>
        </tr>
    </tbody>
</table>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Why Word Documents Are Recommended</strong>
        <p>Word documents preserve the full document structure. This enables tracked changes export (inserting corrections directly into your document) and accurate paragraph-level context.</p>
    </div>
</div>

<h2><i data-lucide="upload"></i> Loading Methods</h2>
<ol>
    <li><strong>Drag and Drop</strong> — Fastest. Drag file from Explorer onto the window.</li>
    <li><strong>Open Button</strong> — Click Open in sidebar or press <kbd>Ctrl</kbd>+<kbd>O</kbd>.</li>
    <li><strong>Batch Load</strong> — Select a folder to queue multiple documents.</li>
</ol>

<h2><i data-lucide="gauge"></i> Performance</h2>
<table class="help-table help-table-compact">
    <tr><td><strong>Maximum Size</strong></td><td>50 MB per document</td></tr>
    <tr><td><strong>Recommended</strong></td><td>Under 10 MB for best performance</td></tr>
</table>

<h2><i data-lucide="check-circle"></i> Best Practices</h2>
<ul>
    <li><strong>Use .docx when possible</strong> — Full feature support</li>
    <li><strong>For PDFs, ensure selectable text</strong> — Scanned images can't be analyzed</li>
    <li><strong>Close documents in Word first</strong> — Locked files may not load</li>
    <li><strong>Remove password protection</strong> — Encrypted documents must be unlocked</li>
</ul>
`
};

// ============================================================================
// REVIEW PRESETS
// ============================================================================
HelpDocs.content['review-types'] = {
    title: 'Review Presets',
    subtitle: 'Pre-configured check combinations for different document types',
    html: `
<p>Review presets are curated combinations of quality checks optimized for specific document types.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Why Presets Exist</strong>
        <p>Different documents have different quality criteria. A requirements specification needs "shall/will/must" checking but not passive voice warnings. A work instruction needs imperative mood but doesn't care about TBD markers. Presets encode this domain knowledge.</p>
    </div>
</div>

<h2><i data-lucide="sliders"></i> Available Presets</h2>

<div class="help-preset-cards">
    <div class="help-preset-card">
        <h3>All <span class="preset-badge">50+ Checks</span></h3>
        <p>Enables every available checker. Use for comprehensive analysis or when unsure which preset to use.</p>
        <h4>Best For</h4>
        <ul><li>Initial assessment</li><li>Mixed content documents</li><li>Quality audits</li></ul>
    </div>
    <div class="help-preset-card">
        <h3>PrOP <span class="preset-badge">Procedures</span></h3>
        <p>Optimized for Procedures and Operating Procedures.</p>
        <h4>Key Checks</h4>
        <ul><li>Requirements language</li><li>Imperative mood</li><li>Step numbering</li><li>Role extraction</li></ul>
    </div>
    <div class="help-preset-card">
        <h3>PAL <span class="preset-badge">Process Assets</span></h3>
        <p>Tailored for Process Asset Library documents.</p>
        <h4>Key Checks</h4>
        <ul><li>Passive voice</li><li>Wordy phrases</li><li>Sentence length</li><li>Readability</li></ul>
    </div>
    <div class="help-preset-card">
        <h3>FGOST <span class="preset-badge">Operations</span></h3>
        <p>For Flight & Ground Operations Safety Training.</p>
        <h4>Key Checks</h4>
        <ul><li>Safety terminology</li><li>Warning/caution format</li><li>Role extraction</li><li>Cross-references</li></ul>
    </div>
    <div class="help-preset-card">
        <h3>SOW <span class="preset-badge">Contracts</span></h3>
        <p>Configured for Statement of Work documents.</p>
        <h4>Key Checks</h4>
        <ul><li>TBD/TBR detection</li><li>Requirements language</li><li>Undefined terms</li><li>Completeness</li></ul>
    </div>
</div>

<h2><i data-lucide="settings"></i> Custom Configurations</h2>
<p>Presets are starting points. You can enable additional checks after applying a preset, disable irrelevant checks, or start with "None" and build your own configuration.</p>
`
};

// ============================================================================
// UNDERSTANDING RESULTS
// ============================================================================
HelpDocs.content['understanding-results'] = {
    title: 'Understanding Results',
    subtitle: 'How to interpret the dashboard, metrics, and issue list',
    html: `
<p>After running a review, AEGIS presents results in two views: the Dashboard (aggregate metrics) and the Issue List (individual findings).</p>

<h2><i data-lucide="layout-dashboard"></i> The Dashboard</h2>

<h3>Quality Score</h3>
<p>Letter grade representing overall quality, calculated from issues per 1,000 words:</p>
<div class="help-formula-box"><code>Issues per 1K Words = (Total Issues × 1000) ÷ Word Count</code></div>

<h3>Severity Distribution</h3>
<p>Interactive pie chart. Click any segment to filter the issue list.</p>
<div class="help-severity-legend">
    <div class="help-severity-item severity-critical"><span class="severity-dot"></span><div><strong>Critical</strong><p>Must fix before release</p></div></div>
    <div class="help-severity-item severity-high"><span class="severity-dot"></span><div><strong>High</strong><p>Fix soon</p></div></div>
    <div class="help-severity-item severity-medium"><span class="severity-dot"></span><div><strong>Medium</strong><p>Should address</p></div></div>
    <div class="help-severity-item severity-low"><span class="severity-dot"></span><div><strong>Low</strong><p>Minor improvements</p></div></div>
    <div class="help-severity-item severity-info"><span class="severity-dot"></span><div><strong>Info</strong><p>Informational only</p></div></div>
</div>

<h3>Readability Metrics</h3>
<div class="help-readability-cards">
    <div class="help-readability-card">
        <h4>Flesch Reading Ease</h4>
        <p>0-100 scale. Higher = easier. Target: 30-50 for tech docs.</p>
    </div>
    <div class="help-readability-card">
        <h4>Flesch-Kincaid Grade</h4>
        <p>US school grade level. Target: 10-14 for tech audiences.</p>
    </div>
    <div class="help-readability-card">
        <h4>Gunning Fog Index</h4>
        <p>Years of education needed. Target: 12-16 for tech docs.</p>
    </div>
</div>

<h2><i data-lucide="list"></i> The Issue List</h2>
<p>Each issue card shows:</p>
<ul>
    <li><strong>Severity Badge</strong> — Color-coded (red, orange, yellow, green, blue)</li>
    <li><strong>Category</strong> — Which checker found the issue</li>
    <li><strong>Message</strong> — Description of the problem</li>
    <li><strong>Flagged Text</strong> — The exact problematic text</li>
    <li><strong>Suggestion</strong> — Recommended correction (when available)</li>
</ul>

<h3>Filtering</h3>
<ul>
    <li><strong>Severity dropdown</strong> — Show only Critical, High, etc.</li>
    <li><strong>Category dropdown</strong> — Show only Grammar, Acronyms, etc.</li>
    <li><strong>Search box</strong> — Find issues containing specific text</li>
    <li><strong>Status filter</strong> — Pending, Kept, Suppressed, Fixed</li>
</ul>

<h2><i data-lucide="box"></i> Document Analytics</h2>
<p>The Document Analytics panel provides additional visualizations:</p>

<h3>3D Carousel (New in v3.0.120)</h3>
<p>Issues by Section displayed as an interactive 3D carousel:</p>
<ul>
    <li><strong>Drag to spin</strong> — Click and drag to rotate the carousel continuously</li>
    <li><strong>Slider navigation</strong> — Use the slider below to position precisely</li>
    <li><strong>Click to filter</strong> — Click any section box to filter issues to that section</li>
    <li><strong>Density coloring</strong> — Border colors indicate issue density (none/low/medium/high)</li>
    <li><strong>Touch support</strong> — Works with touch gestures on mobile devices</li>
</ul>

<h3>Category × Severity Heatmap</h3>
<p>Matrix showing issue counts by category and severity. Click any cell to filter the issue list.</p>

<h3>Hyperlink Status Panel</h3>
<p>After hyperlink validation, shows valid/broken/redirect counts with clickable rows to open URLs in new tabs for manual verification.</p>
`
};

// ============================================================================
// TRIAGE MODE
// ============================================================================
HelpDocs.content['triage-mode'] = {
    title: 'Triage Mode',
    subtitle: 'Efficiently review and categorize issues one by one',
    html: `
<p>Triage Mode provides a focused, keyboard-driven workflow for systematically reviewing each issue.</p>

<h2><i data-lucide="play"></i> Entering Triage Mode</h2>
<p>Press <kbd>T</kbd> or click the <strong>Triage</strong> button. The interface shows one issue at a time with prominent action buttons.</p>

<h2><i data-lucide="keyboard"></i> Keyboard Actions</h2>
<div class="help-triage-keys">
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>K</kbd> or <kbd>→</kbd></div>
        <div class="help-key-desc"><strong>Keep</strong><p>Mark as valid, include in exports</p></div>
    </div>
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>S</kbd></div>
        <div class="help-key-desc"><strong>Suppress</strong><p>Dismiss as false positive</p></div>
    </div>
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>F</kbd></div>
        <div class="help-key-desc"><strong>Fixed</strong><p>Mark as already addressed</p></div>
    </div>
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>Space</kbd></div>
        <div class="help-key-desc"><strong>Skip</strong><p>Move to next without decision</p></div>
    </div>
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>←</kbd></div>
        <div class="help-key-desc"><strong>Previous</strong><p>Go back to reconsider</p></div>
    </div>
    <div class="help-triage-key">
        <div class="help-key-combo"><kbd>Esc</kbd></div>
        <div class="help-key-desc"><strong>Exit</strong><p>Return to normal view</p></div>
    </div>
</div>

<h2><i data-lucide="layers"></i> Family Actions</h2>
<p>When an issue is part of a family (same word flagged multiple times), hold <kbd>Shift</kbd> to apply action to entire family:</p>
<ul>
    <li><kbd>Shift</kbd>+<kbd>K</kbd> — Keep all in family</li>
    <li><kbd>Shift</kbd>+<kbd>S</kbd> — Suppress all in family</li>
    <li><kbd>Shift</kbd>+<kbd>F</kbd> — Mark all as fixed</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Family Actions Save Significant Time</strong>
        <p>If "utilize" is flagged 47 times and you decide it's acceptable, press <kbd>Shift</kbd>+<kbd>S</kbd> once to suppress all 47 instead of pressing <kbd>S</kbd> forty-seven times.</p>
    </div>
</div>
`
};

// ============================================================================
// ISSUE FAMILIES
// ============================================================================
HelpDocs.content['issue-families'] = {
    title: 'Issue Families',
    subtitle: 'Group related issues for efficient batch processing',
    html: `
<p>Issue Families group multiple occurrences of the same issue together, allowing single decisions that apply to all.</p>

<h2><i data-lucide="info"></i> What Creates a Family?</h2>
<p>Issues are grouped when they share the same:</p>
<ul>
    <li>Checker (e.g., "Wordy Phrases")</li>
    <li>Flagged text (e.g., "utilize")</li>
</ul>
<p>For example, if "utilize" appears 23 times and is flagged each time, all 23 become one family.</p>

<h2><i data-lucide="eye"></i> Identifying Families</h2>
<p>Family members show a badge with the count (e.g., "×23") and a linking icon.</p>

<h2><i data-lucide="check-square"></i> Family Actions</h2>
<h3>In Normal View</h3>
<p>Click the family indicator to expand. Use family action buttons to Keep All, Suppress All, or View All.</p>

<h3>In Triage Mode</h3>
<p>Hold <kbd>Shift</kbd> + action key to apply to entire family.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Why Families Matter</strong>
        <p>A 100-page document might have 500+ issues. Without families, you'd review each individually. With families, similar issues collapse to perhaps 80 decisions—an 80% reduction in review time.</p>
    </div>
</div>
`
};

// ============================================================================
// CHECKER OVERVIEW
// ============================================================================
HelpDocs.content['checker-overview'] = {
    title: 'Quality Checkers Overview',
    subtitle: 'Understanding the 50+ checks available',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="shield-check" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>AEGIS includes <strong>50+ quality checks</strong> across 15 checker modules, covering grammar, spelling, acronyms, requirements language, document structure, hyperlinks, and more. All processing happens locally—no cloud dependencies.</p>
    </div>
</div>

<h2><i data-lucide="cog"></i> How Checkers Work</h2>
<ol>
    <li><strong>Extract</strong> — Parse document text, tables, and structure from DOCX, PDF, TXT, or RTF</li>
    <li><strong>Normalize</strong> — Handle smart quotes, special characters, and encoding</li>
    <li><strong>Analyze</strong> — Run each enabled checker against every paragraph</li>
    <li><strong>Score</strong> — Assign severity (Critical/High/Medium/Low/Info) based on impact</li>
    <li><strong>Deduplicate</strong> — Remove redundant findings for cleaner results</li>
    <li><strong>Aggregate</strong> — Present results in dashboard with filtering and sorting</li>
</ol>

<h2><i data-lucide="layers"></i> Checker Categories</h2>
<div class="help-category-grid">
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-grammar')">
        <div class="help-category-icon"><i data-lucide="spell-check"></i></div>
        <h3>Grammar & Spelling</h3>
        <p>Typos, grammatical errors, subject-verb agreement, punctuation, contractions</p>
    </div>
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-acronyms')">
        <div class="help-category-icon"><i data-lucide="a-large-small"></i></div>
        <h3>Acronyms</h3>
        <p>Undefined acronyms, inconsistent definitions, common ALL CAPS words</p>
    </div>
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-writing')">
        <div class="help-category-icon"><i data-lucide="pen-tool"></i></div>
        <h3>Writing Quality</h3>
        <p>Passive voice, wordy phrases, sentence length, readability, complexity</p>
    </div>
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-requirements')">
        <div class="help-category-icon"><i data-lucide="list-checks"></i></div>
        <h3>Requirements Language</h3>
        <p>Shall/will/must usage, TBD/TBR flags, ambiguous terms, testability</p>
    </div>
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-structure')">
        <div class="help-category-icon"><i data-lucide="file-text"></i></div>
        <h3>Document Structure</h3>
        <p>Heading hierarchy, numbering consistency, cross-references, orphan text</p>
    </div>
    <div class="help-category-card" onclick="HelpContent.navigateTo('checker-hyperlinks')">
        <div class="help-category-icon"><i data-lucide="link"></i></div>
        <h3>Hyperlinks</h3>
        <p>URL validation, broken links, redirects, SSL issues, internal anchors</p>
    </div>
</div>

<h2><i data-lucide="list"></i> Complete Checker List</h2>
<table class="help-table">
    <thead><tr><th>Module</th><th>Checks Included</th><th>Example Issues</th></tr></thead>
    <tbody>
        <tr><td><strong>Acronym Checker</strong></td><td>Undefined acronyms, redefinitions, inconsistent usage</td><td>"SRR" used without definition</td></tr>
        <tr><td><strong>Grammar Checker</strong></td><td>Subject-verb agreement, tense consistency, articles</td><td>"The team were" → "The team was"</td></tr>
        <tr><td><strong>Spell Checker</strong></td><td>Misspellings, technical term variations</td><td>"recieve" → "receive"</td></tr>
        <tr><td><strong>Enhanced Grammar</strong></td><td>Advanced patterns, context-aware suggestions</td><td>Double negatives, dangling modifiers</td></tr>
        <tr><td><strong>Writing Quality</strong></td><td>Passive voice, wordiness, sentence complexity</td><td>"It is recommended that" → "We recommend"</td></tr>
        <tr><td><strong>Sentence Checker</strong></td><td>Length, fragments, run-ons</td><td>Sentences over 40 words</td></tr>
        <tr><td><strong>Punctuation Checker</strong></td><td>Spacing, quotation marks, lists</td><td>Double spaces, smart quote consistency</td></tr>
        <tr><td><strong>Requirements Checker</strong></td><td>Shall/will/must, ambiguity, testability</td><td>"shall" in non-binding context</td></tr>
        <tr><td><strong>Document Checker</strong></td><td>Structure, headings, cross-refs</td><td>Skipped heading levels (H1 → H3)</td></tr>
        <tr><td><strong>Hyperlink Checker</strong></td><td>URL format, validation, status</td><td>Broken external link (404)</td></tr>
        <tr><td><strong>Image/Figure Checker</strong></td><td>Alt text, captions, references</td><td>Figure without caption</td></tr>
        <tr><td><strong>Word Language Checker</strong></td><td>MS Word specific issues</td><td>Track changes artifacts</td></tr>
        <tr><td><strong>Document Comparison</strong></td><td>Version differences</td><td>Changed requirements between versions</td></tr>
    </tbody>
</table>

<h2><i data-lucide="sliders"></i> Configuring Checkers</h2>
<ul>
    <li><strong>Review Presets</strong> — Choose preset profiles (PrOP, PAL, FGOST, SOW) to enable relevant checkers</li>
    <li><strong>Document Type Profiles</strong> — Customize which checks run for each document type in <strong>Settings → Document Profiles</strong></li>
    <li><strong>Advanced Settings</strong> — Fine-tune individual checkers in the sidebar</li>
    <li><strong>Severity Filters</strong> — Focus on Critical/High issues or see everything</li>
    <li><strong>Category Filters</strong> — Show only grammar, only requirements, etc.</li>
</ul>

<h3>Document Type Profiles (New in v3.0.115)</h3>
<p>Create custom checker configurations for each document type:</p>
<table class="help-table">
    <thead><tr><th>Profile</th><th>Focus</th><th>Key Checks</th></tr></thead>
    <tbody>
        <tr><td><strong>PrOP</strong></td><td>Process clarity & step-by-step instructions</td><td>Passive Voice, Weak Language, Requirements, Roles, Structure</td></tr>
        <tr><td><strong>PAL</strong></td><td>Templates & assets - grammar focus</td><td>Spelling, Grammar, Punctuation, Structure, References</td></tr>
        <tr><td><strong>FGOST</strong></td><td>Decision gates - requirements & completeness</td><td>Requirements, TBD/TBR, Roles, Testability, Escape Clauses</td></tr>
        <tr><td><strong>SOW</strong></td><td>Contract-focused legal/technical clarity</td><td>Requirements, Passive Voice, Acronyms, Escape Clauses, Units</td></tr>
    </tbody>
</table>
<p>Custom profiles persist in localStorage across sessions. First-time users see a prompt to configure profiles on initial launch.</p>

<h2><i data-lucide="target"></i> Severity Levels</h2>
<table class="help-table">
    <thead><tr><th>Level</th><th>Impact</th><th>Example</th></tr></thead>
    <tbody>
        <tr><td style="color: #dc2626;"><strong>Critical</strong></td><td>Could cause serious misunderstanding or compliance failure</td><td>Undefined shall statement, ambiguous requirement</td></tr>
        <tr><td style="color: #ea580c;"><strong>High</strong></td><td>Likely to cause confusion or errors</td><td>Undefined acronym, broken hyperlink</td></tr>
        <tr><td style="color: #eab308;"><strong>Medium</strong></td><td>Should be fixed but won't cause major issues</td><td>Passive voice overuse, long sentence</td></tr>
        <tr><td style="color: #22c55e;"><strong>Low</strong></td><td>Style improvement, nice to have</td><td>Wordy phrase, minor punctuation</td></tr>
        <tr><td style="color: #6b7280;"><strong>Info</strong></td><td>Informational only, not necessarily an issue</td><td>Detected acronym definition</td></tr>
    </tbody>
</table>

<h2><i data-lucide="lightbulb"></i> Philosophy</h2>
<ul>
    <li><strong>Opinionated but Configurable</strong> — Checkers embody industry best practices, but you can disable what doesn't apply to your context.</li>
    <li><strong>Severity Reflects Impact</strong> — Critical/High issues could cause real problems; Medium/Low are style improvements.</li>
    <li><strong>Suggestions, Not Mandates</strong> — Every finding is a recommendation. You decide what to fix based on your document's purpose.</li>
    <li><strong>False Positive Minimization</strong> — Checkers are tuned to minimize noise while catching real issues.</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Use Review Presets</strong>
        <p>Start with a preset that matches your document type. PrOP for procedures, PAL for process assets, FGOST for flight/ground operations, SOW for statements of work. Each preset enables the most relevant checkers.</p>
    </div>
</div>
`
};

// ============================================================================
// ACRONYM CHECKER
// ============================================================================
HelpDocs.content['checker-acronyms'] = {
    title: 'Acronym Checker',
    subtitle: 'Ensure acronyms are defined and used consistently',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="a-large-small"></i></div>
    <div class="help-checker-intro">
        <p>Identifies undefined acronyms, inconsistent usage, and missing definitions.</p>
    </div>
</div>

<h2><i data-lucide="help-circle"></i> Why This Matters</h2>
<p>Undefined acronyms confuse readers, create accessibility barriers, and may cause compliance issues.</p>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Undefined Acronyms</h4>
            <p>Acronyms used without definition.</p>
            <div class="help-check-example">
                <span class="example-bad">❌ "The SRR will occur in Q3."</span>
                <span class="example-good">✓ "The System Requirements Review (SRR) will occur in Q3."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Inconsistent Definitions</h4>
            <p>Same acronym defined differently in multiple places.</p>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-low">Low</div>
        <div class="help-check-content">
            <h4>Redefined Acronyms</h4>
            <p>Redundant definitions of the same term.</p>
        </div>
    </div>
</div>

<h2><i data-lucide="cog"></i> How Detection Works</h2>
<ol>
    <li><strong>Pattern matching</strong> — Identifies potential acronyms (2-6 uppercase letters)</li>
    <li><strong>Definition scanning</strong> — Looks for "Term (ACRONYM)" patterns</li>
    <li><strong>Context analysis</strong> — Filters common words, units, known abbreviations</li>
    <li><strong>Document-order tracking</strong> — Ensures definitions appear before first use</li>
</ol>

<h2><i data-lucide="book"></i> Built-in Dictionary</h2>
<p>Includes common acronyms from government contracting, aerospace, systems engineering, and general technical writing. Add custom acronyms in Settings → Acronyms.</p>
`
};

// ============================================================================
// GRAMMAR CHECKER
// ============================================================================
HelpDocs.content['checker-grammar'] = {
    title: 'Grammar & Spelling',
    subtitle: 'Catch typos, grammatical errors, and punctuation issues',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="spell-check"></i></div>
    <div class="help-checker-intro">
        <p>Identifies basic language quality issues that could undermine your document's credibility.</p>
    </div>
</div>

<h2><i data-lucide="help-circle"></i> Why This Matters</h2>
<p>Even a single typo in a technical document can damage credibility, introduce ambiguity, and cause failed reviews.</p>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Spelling Errors</h4>
            <p>Words not in dictionary.</p>
            <div class="help-check-example">
                <span class="example-bad">❌ "The systme shall..."</span>
                <span class="example-good">✓ "The system shall..."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Commonly Confused Words</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The affect of the change..."</span>
                <span class="example-good">✓ "The effect of the change..."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Subject-Verb Agreement</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The requirements is documented..."</span>
                <span class="example-good">✓ "The requirements are documented..."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-low">Low</div>
        <div class="help-check-content">
            <h4>Double Words</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The the system shall..."</span>
            </div>
        </div>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Air-Gapped Operation</strong>
        <p>All spelling and grammar checking happens locally. No text is sent to external services, making it safe for classified or proprietary documents.</p>
    </div>
</div>
`
};

// ============================================================================
// HYPERLINK CHECKER
// ============================================================================
HelpDocs.content['checker-hyperlinks'] = {
    title: 'Hyperlink Checker',
    subtitle: 'Validate URLs and link formatting',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="link"></i></div>
    <div class="help-checker-intro">
        <p>Validates URL formatting and identifies potential issues with links.</p>
    </div>
</div>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Malformed URLs</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "htp://example.com"</span>
                <span class="example-good">✓ "https://example.com"</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>HTTP vs HTTPS</h4>
            <p>Non-secure links that should use HTTPS.</p>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Missing Protocol</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "www.example.com/doc"</span>
                <span class="example-good">✓ "https://www.example.com/doc"</span>
            </div>
        </div>
    </div>
</div>

<h2><i data-lucide="activity"></i> Live URL Validation (PowerShell)</h2>
<p>For documents with external links, AEGIS provides a PowerShell script that tests if URLs are reachable:</p>
<ol>
    <li>Run review with Hyperlink Checker enabled</li>
    <li>Go to footer → Hyperlink Health</li>
    <li>Generate PowerShell Script</li>
    <li>Run script on network-connected machine</li>
    <li>Import results back</li>
</ol>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Air-Gapped Workflow</strong>
        <p>The PowerShell script can be run on a network-connected machine and results brought back, enabling link validation even in air-gapped environments.</p>
    </div>
</div>
`
};

// ============================================================================
// REQUIREMENTS LANGUAGE CHECKER
// ============================================================================
HelpDocs.content['checker-requirements'] = {
    title: 'Requirements Language',
    subtitle: 'Ensure proper use of shall, will, must, and directive language',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="list-checks"></i></div>
    <div class="help-checker-intro">
        <p>Ensures your document uses precise, testable language for requirements.</p>
    </div>
</div>

<h2><i data-lucide="help-circle"></i> Why This Matters</h2>
<p>In requirements documents, word choice has legal and technical implications:</p>
<ul>
    <li><strong>"Shall"</strong> — Binding requirement</li>
    <li><strong>"Will"</strong> — Declaration of purpose</li>
    <li><strong>"Must"</strong> — Constraint or condition</li>
    <li><strong>"Should"</strong> — Recommendation (non-binding)</li>
</ul>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>TBD/TBR Markers</h4>
            <p>"To Be Determined" markers that need resolution.</p>
            <div class="help-check-example">
                <span class="example-bad">❌ "The system shall store [TBD] records."</span>
                <span class="example-good">✓ "The system shall store 10,000 records."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Ambiguous Requirements</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The system shall be fast."</span>
                <span class="example-good">✓ "The system shall respond within 200ms."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Weak Requirement Words</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The system should validate input."</span>
                <span class="example-good">✓ "The system shall validate input."</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-low">Low</div>
        <div class="help-check-content">
            <h4>Untestable Language</h4>
            <p>Subjective terms: "user-friendly," "intuitive," "easy to use"</p>
        </div>
    </div>
</div>

<h2><i data-lucide="book"></i> Standards Reference</h2>
<p>Aligns with IEEE 830, ISO/IEC/IEEE 29148, MIL-STD-498, and systems engineering best practices.</p>
`
};

// ============================================================================
// WRITING QUALITY CHECKER
// ============================================================================
HelpDocs.content['checker-writing'] = {
    title: 'Writing Quality',
    subtitle: 'Improve clarity with passive voice detection and more',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="pen-tool"></i></div>
    <div class="help-checker-intro">
        <p>Helps create clearer, more readable documents by identifying common style issues.</p>
    </div>
</div>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Passive Voice</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "The system shall be configured by the administrator."</span>
                <span class="example-good">✓ "The administrator shall configure the system."</span>
            </div>
            <p><em>Why:</em> Passive voice can obscure who is responsible—critical in procedures.</p>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Wordy Phrases</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "in order to" → "to"</span>
                <span class="example-bad">❌ "at this point in time" → "now"</span>
                <span class="example-bad">❌ "due to the fact that" → "because"</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Long Sentences</h4>
            <p>Sentences exceeding 40 words (configurable). Long sentences increase cognitive load.</p>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-low">Low</div>
        <div class="help-check-content">
            <h4>Complex Words</h4>
            <div class="help-check-example">
                <span class="example-bad">❌ "utilize" → "use"</span>
                <span class="example-bad">❌ "commence" → "start"</span>
            </div>
        </div>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Context Matters</strong>
        <p>Passive voice isn't always wrong—it's appropriate when the actor is unknown or unimportant. Use your judgment.</p>
    </div>
</div>
`
};

// ============================================================================
// DOCUMENT STRUCTURE CHECKER
// ============================================================================
HelpDocs.content['checker-structure'] = {
    title: 'Document Structure',
    subtitle: 'Validate headings, numbering, and cross-references',
    html: `
<div class="help-checker-header">
    <div class="help-checker-icon"><i data-lucide="file-text"></i></div>
    <div class="help-checker-intro">
        <p>Ensures your document is well-organized with consistent headings and valid references.</p>
    </div>
</div>

<h2><i data-lucide="help-circle"></i> Why This Matters</h2>
<p>Proper structure enables accurate TOC generation, easy navigation, working cross-references, and standards compliance.</p>

<h2><i data-lucide="check-square"></i> What It Checks</h2>
<div class="help-check-list">
    <div class="help-check-item">
        <div class="help-check-severity severity-high">High</div>
        <div class="help-check-content">
            <h4>Heading Hierarchy Violations</h4>
            <p>Skipped heading levels (e.g., H1 → H3).</p>
            <div class="help-check-example">
                <span class="example-bad">❌ Heading 1 → Heading 3 (skipped H2)</span>
                <span class="example-good">✓ Heading 1 → Heading 2 → Heading 3</span>
            </div>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Broken Cross-References</h4>
            <p>References to sections, figures, or tables that don't exist.</p>
        </div>
    </div>
    <div class="help-check-item">
        <div class="help-check-severity severity-medium">Medium</div>
        <div class="help-check-content">
            <h4>Numbering Gaps</h4>
            <p>Missing numbers in sequences (1, 2, 4 missing 3).</p>
        </div>
    </div>
</div>
`
};

// ============================================================================
// COMPLETE CHECKER REFERENCE
// ============================================================================
HelpDocs.content['checker-all'] = {
    title: 'Complete Checker Reference',
    subtitle: 'All 50+ quality checks in one place',
    html: `
<p>Comprehensive reference of all available checks, organized by category.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Severity Guide</strong>
        <p><span class="severity-badge severity-critical">Critical</span> Must fix • <span class="severity-badge severity-high">High</span> Fix soon • <span class="severity-badge severity-medium">Medium</span> Should address • <span class="severity-badge severity-low">Low</span> Minor • <span class="severity-badge severity-info">Info</span> Informational</p>
    </div>
</div>

<h2><i data-lucide="spell-check"></i> Spelling & Grammar</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Spelling Errors</td><td><span class="severity-badge severity-high">High</span></td><td>Words not in dictionary</td></tr>
        <tr><td>Confused Words</td><td><span class="severity-badge severity-high">High</span></td><td>affect/effect, their/there</td></tr>
        <tr><td>Subject-Verb Agreement</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Verb doesn't match subject</td></tr>
        <tr><td>Double Words</td><td><span class="severity-badge severity-low">Low</span></td><td>Repeated words</td></tr>
    </tbody>
</table>

<h2><i data-lucide="a-large-small"></i> Acronyms</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Undefined Acronyms</td><td><span class="severity-badge severity-high">High</span></td><td>Used without definition</td></tr>
        <tr><td>Inconsistent Definitions</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Same acronym, different meanings</td></tr>
        <tr><td>Redefined Acronyms</td><td><span class="severity-badge severity-low">Low</span></td><td>Redundant definitions</td></tr>
    </tbody>
</table>

<h2><i data-lucide="pen-tool"></i> Writing Quality</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Passive Voice</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Subject receives action</td></tr>
        <tr><td>Long Sentences</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Exceeds 40 words</td></tr>
        <tr><td>Wordy Phrases</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Can be simplified</td></tr>
        <tr><td>Complex Words</td><td><span class="severity-badge severity-low">Low</span></td><td>Simpler alternatives exist</td></tr>
    </tbody>
</table>

<h2><i data-lucide="list-checks"></i> Requirements Language</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>TBD/TBR Markers</td><td><span class="severity-badge severity-high">High</span></td><td>Unresolved placeholders</td></tr>
        <tr><td>Ambiguous Requirements</td><td><span class="severity-badge severity-high">High</span></td><td>Vague, untestable language</td></tr>
        <tr><td>Weak Words</td><td><span class="severity-badge severity-medium">Medium</span></td><td>should, may in requirements</td></tr>
        <tr><td>Untestable Terms</td><td><span class="severity-badge severity-low">Low</span></td><td>user-friendly, intuitive</td></tr>
    </tbody>
</table>

<h2><i data-lucide="file-text"></i> Document Structure</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Heading Hierarchy</td><td><span class="severity-badge severity-high">High</span></td><td>Skipped heading levels</td></tr>
        <tr><td>Broken References</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Invalid cross-references</td></tr>
        <tr><td>Numbering Gaps</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Missing sequence numbers</td></tr>
    </tbody>
</table>

<h2><i data-lucide="link"></i> Hyperlinks</h2>
<table class="help-table help-table-striped help-table-compact">
    <thead><tr><th>Check</th><th>Severity</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Malformed URLs</td><td><span class="severity-badge severity-high">High</span></td><td>Invalid URL syntax</td></tr>
        <tr><td>HTTP vs HTTPS</td><td><span class="severity-badge severity-medium">Medium</span></td><td>Insecure protocol</td></tr>
        <tr><td>Missing Protocol</td><td><span class="severity-badge severity-medium">Medium</span></td><td>No http:// or https://</td></tr>
    </tbody>
</table>
`
};

// ============================================================================
// ROLES OVERVIEW
// ============================================================================
HelpDocs.content['role-overview'] = {
    title: 'Roles & Responsibilities Studio',
    subtitle: 'AI-powered role extraction with 99%+ recall',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="users" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Roles Studio is your centralized workspace for managing organizational roles extracted from documents. Powered by an AI engine achieving <strong>99%+ recall</strong> across defense, aerospace, government, and academic documents, it automatically identifies roles, generates RACI matrices, visualizes relationships, and tracks roles across your entire document library.</p>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="target"></i>
    <div>
        <strong>Validated Performance (v3.3.3)</strong>
        <p>Validated on FAA, NASA, MIL-STD, NIST, OSHA, and academic documents. The extraction engine uses 20+ regex patterns, 228+ pre-defined roles, 192+ false positive exclusions, and domain-specific validation for defense, aerospace, and academic terminology.</p>
    </div>
</div>

<h2><i data-lucide="layout"></i> Studio Tabs</h2>
<p>Roles Studio organizes functionality into three sections:</p>

<table class="help-table">
    <thead><tr><th>Section</th><th>Tabs</th><th>Purpose</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Analysis</strong></td>
            <td>Overview, Relationship Graph, Role Details, RACI Matrix, Role-Doc Matrix</td>
            <td>Visualize and analyze extracted roles</td>
        </tr>
        <tr>
            <td><strong>Workflow</strong></td>
            <td>Adjudication, Export & Import, Sharing</td>
            <td>Classify roles, export for team review, share dictionaries</td>
        </tr>
        <tr>
            <td><strong>Management</strong></td>
            <td>Role Dictionary, Document Log</td>
            <td>Manage role definitions and scan history</td>
        </tr>
    </tbody>
</table>

<h2><i data-lucide="sparkles"></i> Key Features</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="layout-dashboard"></i></div>
        <h3>Overview Dashboard</h3>
        <p>Statistics cards showing unique roles, responsibilities, documents analyzed, and role interactions. Category distribution chart and top roles by responsibility count.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="git-branch"></i></div>
        <h3>Relationship Graph</h3>
        <p>Interactive D3.js force-directed graph showing role connections. Zoom, pan, and drag nodes. Filter by category and export as SVG.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="grid-3x3"></i></div>
        <h3>RACI Matrix</h3>
        <p>Auto-generated Responsible, Accountable, Consulted, Informed matrix. Click cells to assign RACI values. Export to Excel or CSV.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="table-2"></i></div>
        <h3>Role-Document Matrix</h3>
        <p>Heatmap showing which roles appear in which documents. Track role mentions across your entire document library.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="check-circle"></i></div>
        <h3>Adjudication Workflow</h3>
        <p>Review extracted roles one by one. Confirm valid roles, pin important ones, or dismiss false positives. Bulk actions available.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="filter"></i></div>
        <h3>Document Filtering</h3>
        <p>Filter all views by specific document. See only roles from "Contract_v2.docx" or compare across documents.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="book-open"></i></div>
        <h3>Role Dictionary</h3>
        <p>228+ pre-defined roles with aliases and categories covering government, defense, aerospace, academic, and OSHA domains. Add custom roles, edit descriptions, and manage your organization's terminology.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="download"></i></div>
        <h3>Export & Sharing</h3>
        <p>Export to CSV, interactive HTML board for offline review, or share via email packages. Import decisions from team members. Function tags included in all exports.</p>
    </div>
</div>

<h2><i data-lucide="workflow"></i> Typical Workflow</h2>
<ol>
    <li><strong>Scan Documents</strong> — Enable "Role Extraction" in Advanced Settings, then run a review</li>
    <li><strong>Open Roles Studio</strong> — Click <strong>Roles</strong> in the navigation bar (or press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>)</li>
    <li><strong>Review Overview</strong> — See aggregated stats, category distribution, and top roles</li>
    <li><strong>Adjudicate</strong> — Confirm valid roles, assign function tags, reject false positives</li>
    <li><strong>Filter by Document</strong> — Use the dropdown to focus on a specific document</li>
    <li><strong>Analyze</strong> — Explore Relationship Graph, RACI Matrix, or Role-Doc Matrix</li>
    <li><strong>Export & Share</strong> — Export CSV, interactive HTML board, or share via email package</li>
</ol>

<h2><i data-lucide="help-circle"></i> Why Role Extraction Matters</h2>
<ul>
    <li><strong>Identify accountability gaps</strong> — Find activities with no assigned responsible party</li>
    <li><strong>Clarify ownership</strong> — Ensure someone owns each deliverable and decision</li>
    <li><strong>Generate RACI matrices</strong> — Create responsibility assignments automatically from document text</li>
    <li><strong>Track across documents</strong> — See how roles appear and evolve across your document library</li>
    <li><strong>Support compliance</strong> — Document role assignments for audits and reviews</li>
    <li><strong>Feed process modeling</strong> — Export roles to TIBCO Nimbus or other BPM tools</li>
</ul>

<h2><i data-lucide="sparkles"></i> New in v4.0.3</h2>
<div class="help-feature-grid">
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-adjudication')">
        <div class="help-feature-icon"><i data-lucide="shield-check"></i></div>
        <h3>Adjudication Overhaul</h3>
        <p>Complete rewrite with dashboard, confidence gauges, function tag pills, context previews, and animated stat cards.</p>
    </div>
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-adjudication')">
        <div class="help-feature-icon"><i data-lucide="sparkles"></i></div>
        <h3>Auto-Classify</h3>
        <p>AI-assisted role classification with pattern matching. Preview suggestions before applying. Handles deliverables and roles.</p>
    </div>
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-adjudication')">
        <div class="help-feature-icon"><i data-lucide="columns-3"></i></div>
        <h3>Kanban Board</h3>
        <p>Drag-and-drop board view with four columns. Move roles between Pending, Confirmed, Deliverable, and Rejected.</p>
    </div>
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-adjudication')">
        <div class="help-feature-icon"><i data-lucide="keyboard"></i></div>
        <h3>Keyboard Navigation</h3>
        <p>Full keyboard control: arrows to navigate, C/D/R to classify, Ctrl+Z to undo. Undo/redo for all actions.</p>
    </div>
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-export-import')">
        <div class="help-feature-icon"><i data-lucide="globe"></i></div>
        <h3>Interactive HTML Export</h3>
        <p>Export the kanban board as a standalone HTML file. Team members review offline and import decisions back.</p>
    </div>
    <div class="help-feature-card" onclick="HelpContent.navigateTo('role-sharing')">
        <div class="help-feature-icon"><i data-lucide="share-2"></i></div>
        <h3>Role Sharing</h3>
        <p>Share your role dictionary via shared folders or email packages. Function tags included in all exports.</p>
    </div>
</div>

<h2><i data-lucide="navigation"></i> Explore Each Tab</h2>
<div class="help-path-list">
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-detection')">
        <div class="help-path-icon"><i data-lucide="user-search"></i></div>
        <div class="help-path-content"><h4>Role Detection</h4><p>How the AI identifies roles (patterns, confidence, false positive prevention)</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-source-viewer')">
        <div class="help-path-icon"><i data-lucide="file-text"></i></div>
        <div class="help-path-content"><h4>Source Viewer</h4><p>View roles in context with highlighted mentions</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-adjudication')">
        <div class="help-path-icon"><i data-lucide="shield-check"></i></div>
        <div class="help-path-content"><h4>Adjudication</h4><p>Auto-classify, kanban board, function tags, keyboard nav, undo/redo</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-export-import')">
        <div class="help-path-icon"><i data-lucide="arrow-left-right"></i></div>
        <div class="help-path-content"><h4>Export & Import</h4><p>Interactive HTML board for offline review, CSV export, decision import</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-sharing')">
        <div class="help-path-icon"><i data-lucide="share-2"></i></div>
        <div class="help-path-content"><h4>Sharing Roles</h4><p>Share dictionaries via shared folder or email package with function tags</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-graph')">
        <div class="help-path-icon"><i data-lucide="git-branch"></i></div>
        <div class="help-path-content"><h4>Relationship Graph</h4><p>Interactive visualization of role connections</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-matrix')">
        <div class="help-path-icon"><i data-lucide="grid-3x3"></i></div>
        <div class="help-path-content"><h4>RACI Matrix</h4><p>Auto-generated responsibility assignment matrix</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-data-explorer')">
        <div class="help-path-icon"><i data-lucide="bar-chart-3"></i></div>
        <div class="help-path-content"><h4>Data Explorer</h4><p>Deep-dive analytics with drill-down charts</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-smart-search')">
        <div class="help-path-icon"><i data-lucide="search"></i></div>
        <div class="help-path-content"><h4>SmartSearch</h4><p>Intelligent autocomplete search across all roles</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-dictionary')">
        <div class="help-path-icon"><i data-lucide="book-open"></i></div>
        <div class="help-path-content"><h4>Role Dictionary</h4><p>Manage pre-defined roles and add custom entries</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-sipoc-import')">
        <div class="help-path-icon"><i data-lucide="git-branch"></i></div>
        <div class="help-path-content"><h4>Nimbus SIPOC Import</h4><p>Import role hierarchies from Nimbus process model exports (v4.1.0)</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-hierarchy')">
        <div class="help-path-icon"><i data-lucide="git-branch"></i></div>
        <div class="help-path-content"><h4>Role Hierarchy</h4><p>Visualize and export organizational role hierarchy with interactive HTML (v4.1.0)</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('role-documents')">
        <div class="help-path-icon"><i data-lucide="file-text"></i></div>
        <div class="help-path-content"><h4>Document Log</h4><p>Scan history with recall and delete options</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Historical Data</strong>
        <p>Roles Studio remembers all your scans. Open it anytime—even without a document loaded—to view and analyze historical role data from your entire document library.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE DETECTION
// ============================================================================
HelpDocs.content['role-detection'] = {
    title: 'Role Detection',
    subtitle: 'How AEGIS identifies organizational roles',
    html: `
<h2><i data-lucide="cog"></i> Detection Methods</h2>

<h3>1. Title Patterns</h3>
<p>Recognizes job titles, organizational roles, and functional roles like "Project Manager," "Systems Engineer," "Approver."</p>

<h3>2. Responsibility Statements</h3>
<p>Parses sentences with responsibility language:</p>
<div class="help-check-example">
    <span class="example-good">"The <strong>Project Manager</strong> shall <strong>approve all deliverables</strong>."</span>
    <span class="example-arrow">→</span>
    <span>Role: Project Manager | Action: approve all deliverables</span>
</div>

<h3>3. RACI Indicators</h3>
<ul>
    <li><strong>Responsible</strong>: "shall perform," "is responsible for"</li>
    <li><strong>Accountable</strong>: "is accountable for," "owns"</li>
    <li><strong>Consulted</strong>: "shall be consulted"</li>
    <li><strong>Informed</strong>: "shall be informed"</li>
</ul>

<h2><i data-lucide="play-circle"></i> Running Detection</h2>
<ol>
    <li>Enable <strong>Role Extraction</strong> in the sidebar checkers panel</li>
    <li>Run review (<kbd>Ctrl</kbd>+<kbd>R</kbd>)</li>
    <li>Click <strong>Roles</strong> button in footer to open Roles Studio</li>
    <li>Check the <strong>Overview</strong> tab for detected roles summary</li>
</ol>

<h2><i data-lucide="database"></i> Historical Data</h2>
<p>Roles are stored in the database across all scans. Open Roles Studio to see aggregated data from your entire document library, even without running a new scan.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Detection Isn't Perfect</strong>
        <p>The system may flag false positives or miss some roles. That's why Adjudication exists—you confirm which detections are valid.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE SOURCE VIEWER
// ============================================================================
HelpDocs.content['role-source-viewer'] = {
    title: 'Role Source Viewer',
    subtitle: 'View role context in source documents',
    html: `
<p>The Role Source Viewer (v3.2.0) displays the actual document text with role mentions highlighted, helping you understand how roles are used in context before making adjudication decisions.</p>

<h2><i data-lucide="mouse-pointer"></i> Opening the Viewer</h2>
<p>Click any <strong>role name</strong> throughout the Roles Studio to open the Source Viewer:</p>
<ul>
    <li>Overview tab — Top Roles list</li>
    <li>Details tab — Role cards</li>
    <li>Cross-Reference tab — Matrix cells</li>
    <li>RACI Matrix tab — Role entries</li>
    <li>Adjudication tab — Role names in review list</li>
</ul>

<h2><i data-lucide="columns"></i> Split-Panel Layout</h2>

<h3>Left Panel: Document Text</h3>
<ul>
    <li>Full document text displayed with serif font for readability</li>
    <li>All occurrences of the role highlighted in <span style="background:linear-gradient(180deg, rgba(255, 235, 59, 0.3), rgba(255, 235, 59, 0.5));padding:2px 4px;border-radius:3px;">yellow/orange</span></li>
    <li>Current mention highlighted with stronger <span style="background:linear-gradient(180deg, rgba(255, 193, 7, 0.6), rgba(255, 152, 0, 0.8));padding:2px 4px;border-radius:3px;box-shadow:0 0 0 2px rgba(255, 152, 0, 0.3);">orange glow</span></li>
    <li>Click any highlight to jump to that mention</li>
</ul>

<h3>Right Panel: Role Details & Adjudication</h3>
<ul>
    <li><strong>Role Name Badge</strong> — The role being viewed</li>
    <li><strong>Adjudication Controls</strong> — Confirm, Mark Deliverable, or Reject</li>
    <li><strong>Category Dropdown</strong> — Classify the role type</li>
    <li><strong>Notes Field</strong> — Add comments about your decision</li>
    <li><strong>Frequency</strong> — Total mentions across all documents</li>
    <li><strong>Documents</strong> — List of documents containing this role</li>
</ul>

<h2><i data-lucide="navigation"></i> Navigation Controls</h2>
<table class="help-table">
    <tbody>
        <tr><td><strong>Document Selector</strong></td><td>Dropdown to switch between documents</td></tr>
        <tr><td><strong>← Prev</strong></td><td>Go to previous mention</td></tr>
        <tr><td><strong>Next →</strong></td><td>Go to next mention</td></tr>
        <tr><td><strong>Mention Counter</strong></td><td>Shows "Mention X of Y"</td></tr>
        <tr><td><strong>Click Highlight</strong></td><td>Jump directly to any highlighted mention</td></tr>
    </tbody>
</table>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>←</kbd></td><td>Previous mention</td></tr>
        <tr><td><kbd>→</kbd></td><td>Next mention</td></tr>
        <tr><td><kbd>Escape</kbd></td><td>Close the viewer</td></tr>
    </tbody>
</table>

<h2><i data-lucide="database"></i> Historical Documents</h2>
<p>The Source Viewer retrieves document text from your scan history database. This means:</p>
<ul>
    <li>You can view roles from previously scanned documents</li>
    <li>Original files don't need to be in their original location</li>
    <li>Document text is preserved in <code>results_json.full_text</code></li>
</ul>

<h2><i data-lucide="moon"></i> Dark Mode Support</h2>
<p>The Role Source Viewer (v4.0.2) includes comprehensive dark mode styling:</p>
<ul>
    <li><strong>Document Text</strong> — Light text (#e0e0e0) on dark background for comfortable reading</li>
    <li><strong>Role Highlights</strong> — Amber gradient overlays remain visible in dark mode</li>
    <li><strong>All Panels</strong> — Headers, footers, and details panel fully styled</li>
    <li><strong>Form Controls</strong> — Buttons, dropdowns, and inputs all adapt to theme</li>
</ul>
<p>Switch between light and dark modes using the theme toggle in the top navigation bar—the Source Viewer adapts automatically.</p>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip</strong>
        <p>Use the Source Viewer before adjudicating! Seeing the actual context helps you determine if a detected term is truly an organizational role or a false positive.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Quick Access from Role Cards</strong>
        <p>In the Role Details tab, each role card shows an explore icon (magnifying glass with plus). Click it to open the Data Explorer with full analytics for that role. Click the role name itself to open the Source Viewer.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE ADJUDICATION
// ============================================================================
HelpDocs.content['role-adjudication'] = {
    title: 'Role Adjudication',
    subtitle: 'Powerful role classification with auto-classify, kanban view, function tags, and keyboard navigation',
    html: `
<p>The Adjudication tab (v4.0.3) provides a comprehensive role classification workflow. Review, classify, and validate all roles extracted from your documents with powerful tools including auto-classification, dual views, function tag assignment, and full keyboard navigation.</p>

<h2><i data-lucide="layout-dashboard"></i> Dashboard</h2>
<p>The dashboard header shows real-time statistics with animated counters:</p>
<ul>
    <li><strong>Progress Ring</strong> — SVG circle showing percentage of roles adjudicated vs total</li>
    <li><strong>Stat Cards</strong> — Click any card (Pending, Confirmed, Deliverable, Rejected) to filter the list to that status</li>
    <li>Cards animate with count pop effect when values change</li>
</ul>

<h2><i data-lucide="sparkles"></i> Auto-Classify</h2>
<p>Click <strong>Auto-Classify</strong> to run AI-assisted pattern matching on all pending roles:</p>
<ul>
    <li>Checks roles against the role dictionary (confirmed/rejected history)</li>
    <li>Detects deliverable patterns (report, plan, specification, schedule, etc.)</li>
    <li>Identifies role-title patterns (engineer, manager, lead, coordinator, etc.)</li>
    <li>Considers document frequency and mention count for confidence scoring</li>
    <li>Shows a preview modal before applying — review each suggestion individually or apply all</li>
</ul>

<h2><i data-lucide="check-square"></i> Adjudication Actions</h2>
<p>Each role card has four action buttons:</p>
<table class="help-table">
    <thead><tr><th>Action</th><th>Color</th><th>Effect</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Confirm</strong></td>
            <td style="color:#10b981;">Green</td>
            <td>Valid role — added to role dictionary as active, boosted in future scans</td>
        </tr>
        <tr>
            <td><strong>Deliverable</strong></td>
            <td style="color:#3b82f6;">Blue</td>
            <td>Deliverable/artifact — flagged for deliverables export, tied to responsible roles</td>
        </tr>
        <tr>
            <td><strong>Reject</strong></td>
            <td style="color:#ef4444;">Red</td>
            <td>False positive — added to ignore list, suppressed in future scans</td>
        </tr>
        <tr>
            <td><strong>View Source</strong></td>
            <td style="color:var(--text-secondary);">Gray</td>
            <td>Opens Role Source Viewer to see the role in original document context</td>
        </tr>
    </tbody>
</table>

<h2><i data-lucide="columns-3"></i> Views</h2>
<p>Toggle between two views using the view buttons in the toolbar:</p>
<h3>List View (Default)</h3>
<p>Enhanced role cards showing:</p>
<ul>
    <li><strong>Confidence Ring</strong> — SVG circular gauge (green &ge; 80%, amber &ge; 60%, red &lt; 60%)</li>
    <li><strong>Function Tag Pills</strong> — Colored pills showing assigned function categories with remove button</li>
    <li><strong>Document Chips</strong> — Which documents contain this role</li>
    <li><strong>Context Preview</strong> — First context sentence with expandable full text</li>
    <li><strong>Category Badge</strong> — Color-coded category classification</li>
</ul>

<h3>Kanban Board View</h3>
<p>Four-column board layout:</p>
<ul>
    <li>Columns: <strong>Pending</strong> | <strong>Confirmed</strong> | <strong>Deliverables</strong> | <strong>Rejected</strong></li>
    <li>Drag and drop cards between columns to change status</li>
    <li>Column headers show count badges</li>
    <li>View preference saved in localStorage</li>
</ul>

<h2><i data-lucide="tags"></i> Function Tags</h2>
<p>Assign hierarchical function categories to roles directly from the card:</p>
<ul>
    <li>Click the <strong>+</strong> button on any role card to open the tag dropdown</li>
    <li>Select from hierarchical categories (e.g., ENG &gt; FS-AERO &gt; specific function)</li>
    <li>Tags appear as colored pills on the card</li>
    <li>Click the <strong>&times;</strong> on a pill to remove the tag</li>
    <li>Filter roles by "Has Function Tags" or "No Function Tags" using the filter dropdown</li>
</ul>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <thead><tr><th>Key</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>&uarr;</kbd> / <kbd>&darr;</kbd></td><td>Navigate between role cards</td></tr>
        <tr><td><kbd>j</kbd> / <kbd>k</kbd></td><td>Navigate down / up (vim-style)</td></tr>
        <tr><td><kbd>C</kbd></td><td>Confirm focused role</td></tr>
        <tr><td><kbd>D</kbd></td><td>Mark focused role as deliverable</td></tr>
        <tr><td><kbd>R</kbd></td><td>Reject focused role</td></tr>
        <tr><td><kbd>V</kbd></td><td>Open Source Viewer for focused role</td></tr>
        <tr><td><kbd>Space</kbd></td><td>Toggle selection on focused role</td></tr>
        <tr><td><kbd>Ctrl+Z</kbd></td><td>Undo last adjudication action</td></tr>
        <tr><td><kbd>Ctrl+Y</kbd></td><td>Redo undone action</td></tr>
        <tr><td><kbd>Ctrl+A</kbd></td><td>Select all visible roles</td></tr>
    </tbody>
</table>

<h2><i data-lucide="undo-2"></i> Undo / Redo</h2>
<p>Every adjudication action is recorded in a history stack. Use the toolbar buttons or keyboard shortcuts to undo and redo actions. The undo/redo buttons are disabled when there is nothing to undo or redo.</p>

<h2><i data-lucide="combine"></i> Bulk Operations</h2>
<p>Select multiple roles using checkboxes or <kbd>Ctrl+A</kbd>, then use the bulk action buttons to confirm, reject, or mark as deliverable in one operation. Bulk operations use the batch API for efficient processing.</p>

<h2><i data-lucide="download"></i> Export & Import</h2>
<p>The Export button now opens a dropdown menu with three options:</p>
<table class="help-table">
    <thead><tr><th>Option</th><th>Format</th><th>Description</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>CSV Spreadsheet</strong></td>
            <td>.csv</td>
            <td>Download all roles with status, category, confidence, function tags, documents, and mention counts</td>
        </tr>
        <tr>
            <td><strong>Interactive HTML Board</strong></td>
            <td>.html</td>
            <td>Standalone offline kanban board — share with team members who don't have AEGIS installed</td>
        </tr>
        <tr>
            <td><strong>Import Decisions...</strong></td>
            <td>.json</td>
            <td>Import adjudication decisions from an Interactive HTML Board back into AEGIS</td>
        </tr>
    </tbody>
</table>
<p>See <strong><a href="#" onclick="HelpContent.navigateTo('role-export-import');return false;">Export & Import</a></strong> for a detailed walkthrough of the Interactive HTML Board workflow.</p>

<h2><i data-lucide="share-2"></i> Sharing</h2>
<p>The Share button (next to Export) opens a dropdown with two sharing methods:</p>
<ul>
    <li><strong>Export to Shared Folder</strong> — Writes the master dictionary file (with function tags) to your configured shared folder path</li>
    <li><strong>Email Package...</strong> — Downloads a <code>.aegis-roles</code> package and opens your email client with import instructions for the recipient</li>
</ul>
<p>See <strong><a href="#" onclick="HelpContent.navigateTo('role-sharing');return false;">Sharing Roles</a></strong> for full details on both methods.</p>

<h2><i data-lucide="refresh-ccw"></i> Feedback Loop</h2>
<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Your decisions improve future scans</strong>
        <p><strong>Confirmed</strong> roles are added to the known roles list with high confidence (0.95), making them easier to detect in future document scans. <strong>Rejected</strong> roles are added to the false positives list, preventing them from being flagged again.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Save & Apply</strong>
        <p>Click "Save & Apply" to persist all adjudication decisions to the database in a single batch transaction. The Reset button clears all pending decisions and reloads from the server.</p>
    </div>
</div>
`
};

// ============================================================================
// EXPORT & IMPORT (NEW in v4.0.3)
// ============================================================================
HelpDocs.content['role-export-import'] = {
    title: 'Export & Import',
    subtitle: 'Interactive HTML board for offline team review and decision import',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="arrow-left-right" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Export your adjudication as an interactive HTML kanban board that team members can open in any browser — no AEGIS installation needed. They can drag roles between columns, assign function tags, edit categories, add notes, and then generate an import file that you bring back into AEGIS.</p>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="wifi-off"></i>
    <div>
        <strong>Works Completely Offline</strong>
        <p>The exported HTML file has zero external dependencies. All CSS and JavaScript are embedded. It works in any modern browser without internet access — ideal for air-gapped environments and secure reviews.</p>
    </div>
</div>

<h2><i data-lucide="workflow"></i> Complete Workflow</h2>
<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Team Review Workflow</strong>
        <p>This feature is designed for teams where a lead analyst exports the current state, distributes the HTML file to reviewers, and then imports their decisions back into the master AEGIS instance.</p>
    </div>
</div>

<ol>
    <li><strong>Export the Board</strong> — In the Adjudication tab, click <strong>Export</strong> → <strong>Interactive HTML Board</strong></li>
    <li><strong>Distribute</strong> — Send the downloaded <code>.html</code> file to team members via email, shared drive, or USB</li>
    <li><strong>Review Offline</strong> — Team members open the HTML file in their browser and make adjudication decisions</li>
    <li><strong>Generate Import File</strong> — When done, they click <strong>"Generate Import File"</strong> at the top of the HTML board, which downloads a <code>.json</code> file</li>
    <li><strong>Import Back</strong> — Back in AEGIS, click <strong>Export</strong> → <strong>Import Decisions...</strong> and select the <code>.json</code> file</li>
    <li><strong>Review Results</strong> — AEGIS applies the decisions and shows a summary of what was imported</li>
</ol>

<h2><i data-lucide="globe"></i> Interactive HTML Board Features</h2>
<p>The exported HTML board replicates the AEGIS adjudication experience:</p>

<h3>Kanban Board</h3>
<ul>
    <li>Four columns: <strong>Pending</strong>, <strong>Confirmed</strong>, <strong>Deliverable</strong>, <strong>Rejected</strong></li>
    <li>Native drag-and-drop between columns (HTML5 Drag API)</li>
    <li>Column counters update in real time</li>
    <li>AEGIS-branded header with gold/bronze gradient</li>
</ul>

<h3>Role Cards</h3>
<ul>
    <li><strong>Confidence Badge</strong> — Color-coded percentage (green ≥ 80%, amber ≥ 60%, red &lt; 60%)</li>
    <li><strong>Category Badge</strong> — Current classification (Role, Management, Technical, etc.)</li>
    <li><strong>Function Tag Pills</strong> — Currently assigned function tags</li>
    <li><strong>Document Chips</strong> — Which documents contain this role</li>
    <li>Click any card to open the editing modal</li>
</ul>

<h3>Editing Modal</h3>
<p>Click a role card to expand it and edit:</p>
<ul>
    <li><strong>Status</strong> — Change between Pending, Confirmed, Deliverable, Rejected via dropdown</li>
    <li><strong>Category</strong> — Select from predefined categories or type a custom category</li>
    <li><strong>Function Tags</strong> — Searchable hierarchical dropdown with all function categories (parent &gt; child &gt; grandchild)</li>
    <li><strong>Notes</strong> — Free-text area for reviewer comments</li>
</ul>

<h3>Additional Features</h3>
<ul>
    <li><strong>Search/Filter Bar</strong> — Type to filter roles by name</li>
    <li><strong>Real-time Stats</strong> — Header counters show totals per column</li>
    <li><strong>Dark/Light Mode</strong> — Toggle button for personal preference</li>
    <li><strong>Undo/Redo</strong> — Full action history (Ctrl+Z / Ctrl+Y)</li>
    <li><strong>Keyboard Hints</strong> — Footer showing available shortcuts</li>
</ul>

<h2><i data-lucide="download"></i> Export Formats</h2>
<table class="help-table">
    <thead><tr><th>Format</th><th>Use Case</th><th>How to Get</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>CSV</strong></td>
            <td>Spreadsheet analysis, reporting</td>
            <td>Export → CSV Spreadsheet</td>
        </tr>
        <tr>
            <td><strong>Interactive HTML</strong></td>
            <td>Team review, offline adjudication</td>
            <td>Export → Interactive HTML Board</td>
        </tr>
        <tr>
            <td><strong>PDF Report</strong></td>
            <td>Formatted report for documentation and auditing</td>
            <td>Export → PDF Report</td>
        </tr>
        <tr>
            <td><strong>JSON (Import)</strong></td>
            <td>Return decisions from HTML board to AEGIS</td>
            <td>Generated by the HTML board itself</td>
        </tr>
    </tbody>
</table>

<h3>PDF Report <span class="help-badge help-badge-new">v4.0.4</span></h3>
<p>The PDF Report generates a professional, print-ready document containing:</p>
<ul>
    <li><strong>Summary Statistics</strong> — Total roles, counts by status (Deliverable, Confirmed, Rejected, Pending)</li>
    <li><strong>Roles by Status</strong> — Color-coded tables for each status group showing role name, category, function tags, and notes</li>
    <li><strong>Function Tag Distribution</strong> — Which function tags are assigned to how many roles</li>
    <li>AEGIS gold branding with version and timestamp</li>
</ul>

<h2><i data-lucide="upload"></i> Importing Decisions</h2>

<h3>Diff Preview <span class="help-badge help-badge-new">v4.0.4</span></h3>
<p>When you import a decisions file, AEGIS now shows a <strong>diff preview</strong> before applying changes:</p>
<ol>
    <li>Select the <code>.json</code> file via <strong>Export → Import Decisions...</strong></li>
    <li>AEGIS analyzes the file and shows a preview modal with three sections:
        <ul>
            <li><strong style="color:#10b981;">New Roles</strong> — Roles not yet in your dictionary (will be added)</li>
            <li><strong style="color:#f59e0b;">Changed Roles</strong> — Roles that will be updated (shows specific field changes)</li>
            <li><strong style="color:#6b7280;">Unchanged Roles</strong> — Roles that already match (no action needed)</li>
        </ul>
    </li>
    <li>Review the changes, then click <strong>Import</strong> to apply or <strong>Cancel</strong> to abort</li>
    <li>A progress spinner shows during the import process</li>
</ol>

<h3>Version Compatibility <span class="help-badge help-badge-new">v4.0.4</span></h3>
<p>If the import file was created with a newer version of AEGIS than you're running, you'll see a compatibility warning. The import is still allowed — the warning is informational so you know some newer features may not be fully supported.</p>

<h3>What Gets Imported</h3>
<p>Each decision in the import file updates:</p>
<ul>
    <li>The role's adjudication status (confirmed, deliverable, rejected)</li>
    <li>The reviewer's category selection</li>
    <li>Notes added by the reviewer</li>
    <li>Function tag assignments from the reviewer's selections</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Import Format</strong>
        <p>The import JSON file contains an <code>aegis_version</code> field for compatibility checking, plus an array of <code>decisions</code> with role_name, action, category, notes, and function_tags for each reviewed role.</p>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Multiple Reviewers</strong>
        <p>You can export the HTML board to multiple reviewers and import their decision files one at a time. Each import applies on top of the current state, so later imports override earlier ones for the same roles.</p>
    </div>
</div>
`
};

// ============================================================================
// SHARING ROLES (NEW in v4.0.3)
// ============================================================================
HelpDocs.content['role-sharing'] = {
    title: 'Sharing Roles',
    subtitle: 'Share role dictionaries with team members via shared folders or email packages',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="share-2" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Share your curated role dictionary — including function tag assignments — with team members using two methods: a shared network folder or a downloadable email package. Recipients can import roles into their own AEGIS instance to benefit from your adjudication work.</p>
    </div>
</div>

<h2><i data-lucide="folder-sync"></i> Method 1: Shared Folder</h2>
<p>Best for teams with a common network drive or shared folder.</p>

<h3>How It Works</h3>
<ol>
    <li>Configure a shared folder path in <strong>Settings → Sharing</strong></li>
    <li>In the Adjudication tab, click <strong>Share</strong> → <strong>Export to Shared Folder</strong></li>
    <li>AEGIS writes a master dictionary file to the configured path</li>
    <li>Team members point their AEGIS instance to the same shared path</li>
    <li>They click <strong>"Check for Updates"</strong> in Settings → Updates, or the sync runs automatically</li>
</ol>

<h3>What Gets Shared</h3>
<ul>
    <li>All active roles from your dictionary</li>
    <li>Category classifications (Management, Technical, Role, etc.)</li>
    <li>Deliverable flags</li>
    <li><strong>Function tags</strong> assigned to each role (new in v4.0.3)</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Enhanced Master File (v4.0.3)</strong>
        <p>The master file now includes a <code>function_tags</code> array for each role, so all your function category assignments are preserved when sharing. Previous versions only shared role names and categories.</p>
    </div>
</div>

<h2><i data-lucide="mail"></i> Method 2: Email Package</h2>
<p>Best for sharing with team members who don't have access to a shared network drive.</p>

<h3>How It Works</h3>
<ol>
    <li>In the Adjudication tab, click <strong>Share</strong> → <strong>Email Package...</strong></li>
    <li>AEGIS downloads a <code>.aegis-roles</code> package file to your computer</li>
    <li>Your default email client opens with a pre-filled message containing import instructions</li>
    <li>Attach the <code>.aegis-roles</code> file to the email and send</li>
    <li>Recipients save the file and import it using one of the methods below</li>
</ol>

<h3>What's in the Package</h3>
<p>The <code>.aegis-roles</code> package is a JSON file containing:</p>
<ul>
    <li><strong>Role Dictionary</strong> — All active roles with category, deliverable flag, and function tags</li>
    <li><strong>Function Categories</strong> — All active function categories (so the recipient has the same tag hierarchy)</li>
    <li><strong>Metadata</strong> — AEGIS version, export timestamp, and source hostname</li>
</ul>

<h2><i data-lucide="upload"></i> Importing a Package</h2>
<p>Recipients have three ways to import a <code>.aegis-roles</code> package:</p>

<table class="help-table">
    <thead><tr><th>Method</th><th>Steps</th><th>Best For</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Settings UI</strong></td>
            <td>Settings → Sharing → Import Package → select file</td>
            <td>One-time imports, new users</td>
        </tr>
        <tr>
            <td><strong>Updates Folder</strong></td>
            <td>Drop <code>.aegis-roles</code> in <code>updates/</code> → Check for Updates</td>
            <td>Automated workflows, bulk deployment</td>
        </tr>
        <tr>
            <td><strong>Auto-Import</strong></td>
            <td>Place in <code>updates/</code> folder → file detected on next update check</td>
            <td>IT-managed rollouts</td>
        </tr>
    </tbody>
</table>

<h3>Import Behavior</h3>
<ul>
    <li><strong>New roles</strong> are added to the dictionary</li>
    <li><strong>Existing roles</strong> (by name) are skipped to preserve local decisions</li>
    <li><strong>New function categories</strong> are created</li>
    <li><strong>Existing categories</strong> are left unchanged</li>
    <li>A success toast shows the count of roles added, skipped, and categories imported</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Building a Team Dictionary</strong>
        <p>Designate one team member as the "dictionary owner." They adjudicate roles and export packages periodically. Other team members import these packages to stay in sync. This creates a consistent role vocabulary across your organization.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="shield"></i>
    <div>
        <strong>Air-Gap Friendly</strong>
        <p>Both sharing methods work without internet. The shared folder method uses your local network, and the email package method generates a local file. No cloud services involved.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE GRAPH
// ============================================================================
HelpDocs.content['role-graph'] = {
    title: 'Relationship Graph',
    subtitle: 'Visualize how roles interact across documents',
    html: `
<p>The Relationship Graph provides interactive visualizations showing which roles appear together in documents and how they relate to each other. Choose from multiple layout modes to explore your data.</p>

<h2><i data-lucide="layout"></i> Layout Modes</h2>

<h3>Edge Bundling (Default)</h3>
<p>Roles arranged in a circle, grouped by source document. Connections drawn as bundled bezier curves that merge through shared hierarchy. Cross-document edges span the circle as long curves, making bridge roles visually prominent.</p>
<ul>
    <li><strong>Document group arcs</strong> — Colored arc segments show which document cluster each role belongs to</li>
    <li><strong>Bundled edges</strong> — Related connections merge together for clarity at scale</li>
    <li><strong>Bundling slider</strong> — Adjust from 0 (straight lines) to 1 (maximum bundling) for optimal clarity</li>
</ul>

<h3>Semantic Zoom</h3>
<p>Same data as Edge Bundling, but rendering changes based on zoom level:</p>
<ul>
    <li><strong>Zoomed out</strong> — Document clusters shown as labeled circles with interconnection lines</li>
    <li><strong>Medium zoom</strong> — Individual role nodes appear within cluster boundaries</li>
    <li><strong>Zoomed in</strong> — Full labels, individual edges, and complete detail visible</li>
</ul>

<h3>Force-Directed (Classic)</h3>
<p>Physics simulation where connected nodes attract and unconnected nodes repel. Good for small datasets.</p>

<h3>Bipartite (Roles | Docs)</h3>
<p>Two-column layout separating roles on the left and documents on the right.</p>

<h2><i data-lucide="eye"></i> Understanding the Graph</h2>
<h3>Nodes (Circles)</h3>
<ul>
    <li>Each node represents a confirmed role or document</li>
    <li><strong>Size</strong> = frequency (larger = more mentions)</li>
    <li><strong>Color</strong> = node type (blue = role, green = document)</li>
</ul>

<h3>Edges (Curves/Lines)</h3>
<ul>
    <li>Connect roles that appear in the same document</li>
    <li><strong>Brightness</strong> = connection strength (brighter = stronger)</li>
    <li>Hover any edge to see source, target, type, and weight</li>
</ul>

<h2><i data-lucide="mouse-pointer"></i> Interactions</h2>
<table class="help-table">
    <tbody>
        <tr><td><strong>Click node</strong></td><td>Show details panel with connections, stats, and category</td></tr>
        <tr><td><strong>Hover node</strong></td><td>Highlight connected edges (all others dim)</td></tr>
        <tr><td><strong>Click node (again)</strong></td><td>Drill down to show only connected nodes</td></tr>
        <tr><td><strong>Scroll</strong></td><td>Zoom in/out</td></tr>
        <tr><td><strong>Drag background</strong></td><td>Pan the view</td></tr>
        <tr><td><strong>Weight slider</strong></td><td>Hide weak connections, show only strong relationships</td></tr>
        <tr><td><strong>Search box</strong></td><td>Find and highlight specific roles by name</td></tr>
        <tr><td><strong>Labels dropdown</strong></td><td>Control label visibility (selected/hover/all/none)</td></tr>
    </tbody>
</table>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <tbody>
        <tr><td><strong>Arrow keys</strong></td><td>Navigate between connected nodes</td></tr>
        <tr><td><strong>Enter</strong></td><td>Drill down on selected node</td></tr>
        <tr><td><strong>Backspace</strong></td><td>Go back one drill-down level</td></tr>
        <tr><td><strong>Escape</strong></td><td>Clear selection or filters</td></tr>
        <tr><td><strong>Ctrl+S</strong></td><td>Save current filter view</td></tr>
    </tbody>
</table>

<h2><i data-lucide="sliders"></i> Bundling Tension</h2>
<p>The bundling slider (visible in Edge Bundling and Semantic Zoom modes) controls how tightly edges merge:</p>
<ul>
    <li><strong>0</strong> — Straight lines from source to target (similar to classic graph)</li>
    <li><strong>0.85</strong> (default) — Strong bundling with visible individual paths</li>
    <li><strong>1.0</strong> — Maximum bundling, edges merge tightly through shared hierarchy</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip</strong>
        <p>Edge Bundling handles 300+ nodes smoothly because it uses deterministic positioning (no physics simulation). If your dataset is large, start with Edge Bundling and use the weight slider to focus on the strongest relationships.</p>
    </div>
</div>
`
};

// ============================================================================
// RACI MATRIX
// ============================================================================
HelpDocs.content['role-matrix'] = {
    title: 'RACI Matrix',
    subtitle: 'Generate responsibility assignment matrices',
    html: `
<p>Generate RACI matrices from roles and actions detected in your documents.</p>

<h2><i data-lucide="layout"></i> Accessing RACI Matrix</h2>
<p>Open Roles Studio and click <strong>RACI Matrix</strong> in the Analysis section tabs.</p>

<h2><i data-lucide="info"></i> What is RACI?</h2>
<table class="help-table">
    <thead><tr><th>Letter</th><th>Meaning</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td><strong>R</strong></td><td>Responsible</td><td>Does the work (can have multiple)</td></tr>
        <tr><td><strong>A</strong></td><td>Accountable</td><td>Final decision-maker (only one per activity)</td></tr>
        <tr><td><strong>C</strong></td><td>Consulted</td><td>Provides input before work begins</td></tr>
        <tr><td><strong>I</strong></td><td>Informed</td><td>Notified after work is completed</td></tr>
    </tbody>
</table>

<h2><i data-lucide="table"></i> Matrix Layout</h2>
<p>The RACI matrix uses a condensed layout for better readability:</p>
<ul>
    <li><strong>Role Column</strong> — Wider to accommodate full role names (wraps if needed)</li>
    <li><strong>R/A/C/I Columns</strong> — Compact width showing assignment counts</li>
    <li><strong>Total Column</strong> — Sum of all RACI assignments per role</li>
</ul>
<p>Long role names will wrap within the Role column (up to 2-3 lines) to ensure the entire matrix fits on screen without horizontal scrolling.</p>

<h2><i data-lucide="search"></i> How It Works</h2>
<p>AEGIS analyzes responsibility statements in your documents to automatically assign RACI values:</p>
<ul>
    <li>"shall perform" → <strong>R</strong> (Responsible)</li>
    <li>"is accountable for" → <strong>A</strong> (Accountable)</li>
    <li>"shall be consulted" → <strong>C</strong> (Consulted)</li>
    <li>"shall be informed" → <strong>I</strong> (Informed)</li>
</ul>

<h2><i data-lucide="filter"></i> Deduplication (v4.0.2)</h2>
<p>The RACI Matrix now deduplicates responsibilities to provide accurate counts:</p>
<ul>
    <li><strong>Before v4.0.2</strong> — Identical responsibilities in multiple documents were counted multiple times</li>
    <li><strong>After v4.0.2</strong> — Each unique responsibility is counted once per role, matching the Overview tab's count</li>
</ul>
<p>Deduplication uses text normalization (first 100 characters, lowercase) to identify identical responsibilities across documents. This ensures the RACI totals align with the Overview's deduplicated responsibility count.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Understanding the Numbers</strong>
        <p>If your Overview shows "298 Responsibilities" and the RACI shows "~297 total", this is expected—the slight difference can occur due to edge cases in text normalization. Both counts reflect deduplicated responsibilities.</p>
    </div>
</div>

<h2><i data-lucide="alert-circle"></i> Validation Checks</h2>
<p>The matrix highlights common issues:</p>
<ul>
    <li><strong>No Accountable</strong> — Activity has no "A" assigned</li>
    <li><strong>Multiple Accountable</strong> — More than one "A" (should be only one)</li>
    <li><strong>No Responsible</strong> — Activity has no "R" assigned</li>
</ul>

<h2><i data-lucide="download"></i> Export Options</h2>
<p>Export the RACI matrix to Excel, CSV, or Word for use in project documentation.</p>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip</strong>
        <p>Let AEGIS generate the initial matrix from your document, then refine it. This is much faster than building from scratch.</p>
    </div>
</div>
`
};

// ============================================================================
// CROSS-REFERENCE (NEW in v3.0.55)
// ============================================================================
HelpDocs.content['role-crossref'] = {
    title: 'Cross-Reference Matrix',
    subtitle: 'Role × Document mention counts with heatmap visualization',
    html: `
<p>The Cross-Reference tab shows how many times each role is mentioned in each document, displayed as a heatmap matrix.</p>

<h2><i data-lucide="layout"></i> Accessing Cross-Reference</h2>
<p>Open Roles Studio and click <strong>Cross-Reference</strong> in the Analysis section tabs.</p>

<h2><i data-lucide="table"></i> Understanding the Matrix</h2>
<ul>
    <li><strong>Rows</strong> = Roles (sorted by total mentions, highest first)</li>
    <li><strong>Columns</strong> = Documents</li>
    <li><strong>Cells</strong> = Number of times that role appears in that document</li>
</ul>

<h2><i data-lucide="palette"></i> Heatmap Colors</h2>
<table class="help-table">
    <thead><tr><th>Count</th><th>Color</th></tr></thead>
    <tbody>
        <tr><td>1-2 mentions</td><td style="background:#e3f2fd;">Light blue</td></tr>
        <tr><td>3-5 mentions</td><td style="background:#90caf9;">Medium blue</td></tr>
        <tr><td>6-10 mentions</td><td style="background:#42a5f5;color:white;">Dark blue</td></tr>
        <tr><td>10+ mentions</td><td style="background:#1976d2;color:white;">Deep blue</td></tr>
    </tbody>
</table>

<h2><i data-lucide="sigma"></i> Totals</h2>
<ul>
    <li><strong>Row Totals</strong> — Total mentions for each role across all documents</li>
    <li><strong>Column Totals</strong> — Total mentions in each document across all roles</li>
    <li><strong>Grand Total</strong> — Sum of all role mentions</li>
</ul>

<h2><i data-lucide="filter"></i> Features</h2>
<ul>
    <li><strong>Search Filter</strong> — Type to filter roles by name</li>
    <li><strong>CSV Export</strong> — Download the full matrix as a CSV file</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Cross-Reference vs RACI</strong>
        <p>Cross-Reference shows <em>mention counts</em> (how often a role appears). RACI Matrix shows <em>responsibility assignments</em> (R/A/C/I). Use both for complete analysis.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE DICTIONARY
// ============================================================================
HelpDocs.content['role-dictionary'] = {
    title: 'Role Dictionary',
    subtitle: 'Manage your organization\'s role definitions with dashboard analytics, bulk operations, and keyboard navigation',
    html: `
<p>The Role Dictionary stores all confirmed roles across your document library, serving as a reference for consistent role naming, categorization, and function tag assignment. It is the foundation of AEGIS's learning system — roles you confirm here are detected with higher confidence in future scans, and roles you reject are excluded.</p>

<h2><i data-lucide="layout"></i> Accessing the Dictionary</h2>
<p>Open Roles Studio and click <strong>Role Dictionary</strong> in the Management section tabs.</p>

<h2><i data-lucide="bar-chart-3"></i> Dashboard (v4.0.5)</h2>
<p>The dictionary opens with a live analytics dashboard showing your role library at a glance:</p>
<table class="help-table">
    <thead><tr><th>Tile</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td><strong>Total Roles</strong></td><td>Overall count with active/inactive breakdown</td></tr>
        <tr><td><strong>Deliverables</strong></td><td>Count of items marked as deliverables (work products, not personnel roles)</td></tr>
        <tr><td><strong>Adjudicated</strong></td><td>Count of confirmed + deliverable roles, with ✓/★/✗/○ status breakdown</td></tr>
        <tr><td><strong>Health Score</strong></td><td>0-100% metric based on how many roles have descriptions and function tags</td></tr>
    </tbody>
</table>
<p>Below the tiles: a <strong>category donut chart</strong>, <strong>source distribution bars</strong>, and a <strong>top categories list</strong>.</p>

<h2><i data-lucide="layout-grid"></i> Table & Card Views (v4.0.5)</h2>
<p>Toggle between <strong>Table View</strong> (dense data grid) and <strong>Card View</strong> (rich cards with descriptions and metadata) using the toolbar buttons or pressing <kbd>T</kbd>.</p>
<ul>
    <li><strong>Table View</strong> — Sortable columns (click headers), checkboxes, inline actions, adjudication badges</li>
    <li><strong>Card View</strong> — Color-coded borders by adjudication status, description excerpts, tag pills, hover actions</li>
</ul>

<h2><i data-lucide="check-square"></i> Bulk Operations (v4.0.5)</h2>
<p>Select multiple roles using checkboxes (or <kbd>Space</kbd> with keyboard nav), then use the gold action bar:</p>
<ul>
    <li><strong>Activate / Deactivate</strong> — Toggle active status for all selected</li>
    <li><strong>Set Category</strong> — Assign a new category to all selected</li>
    <li><strong>Mark / Unmark Deliverable</strong> — Batch deliverable flag toggle</li>
    <li><strong>Delete</strong> — Permanently remove selected roles (with confirmation)</li>
</ul>

<h2><i data-lucide="mouse-pointer-click"></i> Inline Quick Actions (v4.0.5)</h2>
<ul>
    <li><strong>Click category badge</strong> — Inline dropdown to change category without opening the modal</li>
    <li><strong>Star toggle (★/☆)</strong> — One-click deliverable marking on each row</li>
    <li><strong>Click role name</strong> — Copies the role name to clipboard</li>
    <li><strong>Clone button</strong> — Duplicates the role with "(Copy)" suffix</li>
</ul>

<h2><i data-lucide="keyboard"></i> Keyboard Navigation (v4.0.5)</h2>
<table class="help-table">
    <thead><tr><th>Key</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>↑</kbd> / <kbd>k</kbd></td><td>Move focus up</td></tr>
        <tr><td><kbd>↓</kbd> / <kbd>j</kbd></td><td>Move focus down</td></tr>
        <tr><td><kbd>Enter</kbd> / <kbd>e</kbd></td><td>Edit focused role</td></tr>
        <tr><td><kbd>Space</kbd></td><td>Toggle selection on focused role</td></tr>
        <tr><td><kbd>T</kbd></td><td>Toggle table/card view</td></tr>
        <tr><td><kbd>/</kbd></td><td>Focus search input</td></tr>
        <tr><td><kbd>Delete</kbd></td><td>Delete focused role</td></tr>
        <tr><td><kbd>Esc</kbd></td><td>Clear selection and focus</td></tr>
    </tbody>
</table>

<h2><i data-lucide="filter"></i> Enhanced Filtering (v4.0.5)</h2>
<p>Beyond text search, source, and category filters, you can now filter by:</p>
<ul>
    <li><strong>Adjudication Status</strong> — Confirmed, Deliverable, Rejected, or Pending</li>
    <li><strong>Has Description</strong> — Roles with or without descriptions</li>
    <li><strong>Has Function Tags</strong> — Roles with or without assigned function tags</li>
</ul>
<p>A filter count badge shows "X of Y roles" when filters are active.</p>

<h2><i data-lucide="copy"></i> Duplicate Detection (v4.0.5)</h2>
<p>When saving a role, AEGIS checks for similar existing roles by comparing normalized names and aliases. If a match is found, you'll see a warning with the similar role names. You can confirm to save anyway if the duplicate is intentional.</p>

<h2><i data-lucide="tags"></i> Function Tags</h2>
<p>Each role can be assigned one or more function tags from the hierarchical function categories system. Tags flow through the entire AEGIS ecosystem:</p>
<ul>
    <li><strong>Adjudication Tab</strong> — Add/remove tags directly on role cards</li>
    <li><strong>Role Source Viewer</strong> — Manage tags while reviewing source context</li>
    <li><strong>Dictionary Export</strong> — Tags are included in master file and <code>.aegis-roles</code> packages</li>
    <li><strong>Dictionary Import</strong> — Tags from imported roles are applied automatically</li>
    <li><strong>Interactive HTML Board</strong> — Reviewers can assign tags offline; they're imported back</li>
</ul>

<h2><i data-lucide="upload"></i> Import/Export</h2>
<p>Multiple ways to import and export your dictionary:</p>
<table class="help-table">
    <thead><tr><th>Action</th><th>Method</th><th>Includes Tags?</th></tr></thead>
    <tbody>
        <tr><td><strong>CSV Export</strong></td><td>Adjudication → Export → CSV Spreadsheet</td><td>Yes (as comma-separated codes)</td></tr>
        <tr><td><strong>Master File Export</strong></td><td>Share → Export to Shared Folder</td><td>Yes (v4.0.3+)</td></tr>
        <tr><td><strong>Email Package</strong></td><td>Share → Email Package</td><td>Yes + function categories</td></tr>
        <tr><td><strong>Package Import</strong></td><td>Settings → Sharing → Import Package</td><td>Yes + function categories</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Building Organizational Memory</strong>
        <p>Adjudicate roles consistently as you scan documents. Over time, your dictionary becomes a comprehensive organizational knowledge base. Share it with team members via the <a href="#" onclick="HelpContent.navigateTo('role-sharing');return false;">Sharing</a> feature to establish a common role vocabulary.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="brain"></i>
    <div>
        <strong>Feedback Loop</strong>
        <p><strong>Confirmed</strong> roles are added to the known roles list (0.95 confidence boost), making them easier to detect in future scans. <strong>Rejected</strong> roles are added to the false positives list, suppressing them automatically.</p>
    </div>
</div>
`
};

// ============================================================================
// NIMBUS SIPOC IMPORT (v4.1.0)
// ============================================================================
HelpDocs.content['role-sipoc-import'] = {
    title: 'Nimbus SIPOC Import',
    subtitle: 'Import role inheritance from Nimbus process model SIPOC exports',
    html: `
<p>AEGIS can import role inheritance directly from Nimbus process model SIPOC exports. The parser uses context-dependent logic with two modes depending on the SIPOC file content.</p>

<h2><i data-lucide="upload"></i> Import Wizard</h2>
<p>Access via the <strong>Import ▼</strong> dropdown in the Dictionary toolbar, then select <strong>Nimbus SIPOC Import</strong>.</p>

<h3>Step 1: Upload</h3>
<p>Drop your SIPOC export file (.xlsx) into the upload zone or click Browse. The file must be a Nimbus SIPOC export with the standard 20-column format.</p>

<h3>Step 2: Preview</h3>
<p>AEGIS analyzes the file and shows statistics:</p>
<ul>
    <li><strong>Roles</strong> — Unique human roles found</li>
    <li><strong>Tools</strong> — Systems/tools identified by the [S] prefix</li>
    <li><strong>Relationships</strong> — Inheritance, co-performs, and tool-usage relationships extracted</li>
    <li><strong>Org Groups</strong> — Organizational groupings from diagram titles</li>
    <li><strong>Parsing Mode</strong> — Hierarchy (inheritance) or Process (co-performs/suppliers/customers)</li>
</ul>
<p>Also shows breakdowns by disposition (Sanctioned/To Be Retired/TBD) and role type.</p>

<h3>Step 3: Options</h3>
<ul>
    <li><strong>Clear previous import</strong> — Remove all previously SIPOC-imported data first</li>
    <li><strong>Org Group selection</strong> — Uncheck any org groups you don't want to import</li>
</ul>

<h3>Step 4: Import</h3>
<p>Progress bar shows import status. Creates roles, relationships, and function tags.</p>

<h3>Step 5: Complete</h3>
<p>Shows final stats with options to view the dictionary or export the hierarchy as interactive HTML.</p>

<h2><i data-lucide="git-branch"></i> Dual Parsing Modes</h2>
<p>AEGIS automatically selects the parsing mode based on the SIPOC file content:</p>

<h3>Hierarchy Mode (Roles Hierarchy map found)</h3>
<p>When the file contains rows with "Roles Hierarchy" in the map path column, AEGIS uses <strong>inheritance mode</strong>:</p>
<ul>
    <li>The <strong>Resources</strong> column drives relationships — the first role (primary) <em>inherits from</em> the 2nd+ roles (secondary)</li>
    <li>Suppliers and Customers columns are <strong>ignored</strong> (false positives for hierarchy)</li>
    <li>Relationships are typed as <code>inherits-from</code></li>
    <li>Only "Roles Hierarchy" rows are processed</li>
</ul>

<h3>Process Mode (auto-fallback)</h3>
<p>When "Roles Hierarchy" is <strong>not found</strong>, AEGIS falls back to <strong>process mode</strong> and processes ALL rows:</p>
<ul>
    <li>Multiple roles on one activity are <code>co-performs</code> relationships (people needed for that step)</li>
    <li>Suppliers column creates <code>supplies-to</code> relationships (upstream roles)</li>
    <li>Customers column creates <code>receives-from</code> relationships (downstream roles)</li>
    <li>A yellow notice box informs you about the fallback</li>
</ul>

<h2><i data-lucide="database"></i> What Gets Imported</h2>
<table class="help-table">
    <thead><tr><th>Data</th><th>Source Column</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Role Names</td><td>Column I (Resources)</td><td>Semicolon-separated; first = primary role</td></tr>
        <tr><td>Inheritance</td><td>Column I (Resources)</td><td>In hierarchy mode: primary role inherits from 2nd+ roles</td></tr>
        <tr><td>Description</td><td>Column J (Commentary)</td><td>Role description text</td></tr>
        <tr><td>Org Tags</td><td>Column L (Diagram Stmts)</td><td>"Org - XXX" entries become ORG-XXX function tags</td></tr>
        <tr><td>Baselined</td><td>Column L</td><td>"Baslined - Yes" marks role as baselined</td></tr>
        <tr><td>Role Type</td><td>Column M (Activity Stmts)</td><td>Singular-Specific, Singular-Aggregate, Group-Specific, Group-Aggregate</td></tr>
        <tr><td>Disposition</td><td>Column M</td><td>Sanctioned, To Be Retired, TBD</td></tr>
        <tr><td>Suppliers</td><td>Column S (Suppliers)</td><td>Process mode only: upstream supplier roles</td></tr>
        <tr><td>Customers</td><td>Column T (Customers)</td><td>Process mode only: downstream customer roles</td></tr>
        <tr><td>Org Group</td><td>Column B (Diagram Title)</td><td>Organizational category assignment</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Merge Behavior</strong>
        <p>When a role appears in multiple rows, AEGIS merges the data: first non-empty description wins, org tags are unioned, and baselined is true if ANY row says Yes. Existing roles are updated, new roles are added.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE IMPORT TEMPLATE (v4.1.0)
// ============================================================================
HelpDocs.content['role-template'] = {
    title: 'Role Import Template',
    subtitle: 'Downloadable standalone HTML form for manual role population',
    html: `
<p>The Role Import Template is a standalone HTML file that serves as a blank form for manual role population. Users can open it in any browser, add roles individually or via bulk paste, then export JSON for re-import into AEGIS.</p>

<h2><i data-lucide="download"></i> Getting the Template</h2>
<p>Click the <strong>Template</strong> button in the Dictionary toolbar. AEGIS generates and downloads an interactive HTML file pre-loaded with your function categories for tag assignment.</p>

<h2><i data-lucide="plus-circle"></i> Adding Roles</h2>
<h3>Single Role Entry</h3>
<p>Expand the form section to enter a role one at a time with all available fields:</p>
<ul>
    <li><strong>Role Name</strong> (required) — The role title</li>
    <li><strong>Category</strong> — Role, Management, Technical, Organization, Custom, Deliverable</li>
    <li><strong>Description</strong> — Free-text description</li>
    <li><strong>Aliases</strong> — Comma-separated alternative names</li>
    <li><strong>Is Deliverable</strong> — Whether this is a work product rather than a person</li>
    <li><strong>Role Type</strong> — Singular-Specific, Singular-Aggregate, Group-Specific, Group-Aggregate</li>
    <li><strong>Disposition</strong> — Sanctioned, To Be Retired, TBD</li>
    <li><strong>Org Group</strong> — Organizational unit</li>
    <li><strong>Baselined</strong> — Locked in process model</li>
    <li><strong>Function Tags</strong> — Tag picker using your AEGIS function categories</li>
</ul>

<h3>Bulk Paste</h3>
<p>Click <strong>Bulk Add</strong> to open the paste modal. Paste data from any source and AEGIS auto-detects the format:</p>
<ul>
    <li><strong>Tab-separated</strong> — Copy/paste directly from Excel or Google Sheets</li>
    <li><strong>CSV</strong> — Comma-separated values</li>
    <li><strong>Semicolons</strong> — Semicolon-delimited data</li>
    <li><strong>One per line</strong> — Simple list of role names</li>
</ul>
<p>If the first row looks like a header, AEGIS maps columns to fields automatically. A preview table lets you review before confirming.</p>

<h2><i data-lucide="file-output"></i> Exporting</h2>
<p>Click <strong>Export JSON</strong> to download a JSON file with all your roles. This file can be imported into AEGIS via the standard <strong>Import CSV/Excel</strong> flow, which accepts the template JSON format.</p>

<h2><i data-lucide="moon"></i> Features</h2>
<ul>
    <li><strong>Dark/Light Mode</strong> — Toggle with button, persists via localStorage</li>
    <li><strong>Search</strong> — Filter the role table by name</li>
    <li><strong>Inline Edit</strong> — Click any role to edit, or select multiple for bulk delete</li>
    <li><strong>Auto-updating Stats</strong> — Cards show total roles, deliverables, with tags, with description</li>
    <li><strong>Fully Offline</strong> — No network needed, works air-gapped</li>
    <li><strong>AEGIS Branded</strong> — Clearly identified as an AEGIS Role Import Template</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Quick Start</strong>
        <p>For fastest population: Copy role names from a spreadsheet, click Bulk Add, paste, review the preview, then import. You can add descriptions and tags later either in the template or after importing into AEGIS.</p>
    </div>
</div>
`
};

// ============================================================================
// ROLE HIERARCHY (v4.1.0)
// ============================================================================
HelpDocs.content['role-hierarchy'] = {
    title: 'Role Inheritance Map',
    subtitle: 'Visualize, edit, and export role inheritance relationships as interactive reports',
    html: `
<p>The Role Inheritance Map lets you visualize the inheritance structure of roles, edit role properties inline, and export changes back into AEGIS. This is an <strong>inheritance map</strong>, not an organizational hierarchy — it shows which roles inherit properties from other roles.</p>

<h2><i data-lucide="git-branch"></i> Inheritance View (In-App)</h2>
<p>In the dictionary toolbar, click the <strong>Inheritance</strong> view toggle (tree icon) to see a collapsible tree visualization of role inheritance.</p>
<ul>
    <li><strong>Expand/Collapse</strong> — Click the ▶ arrow to toggle children visibility</li>
    <li><strong>Search</strong> — Type in the search box to find and auto-expand to matching nodes</li>
    <li><strong>Expand All / Collapse All</strong> — Buttons to control the entire tree at once</li>
    <li><strong>Inherits From</strong> — Shows roles this role inherits properties from</li>
    <li><strong>Inherited By</strong> — Shows roles that inherit from this role</li>
</ul>

<h2><i data-lucide="shield-check"></i> Disposition Visual Treatments</h2>
<p>Roles are visually differentiated by their disposition status throughout AEGIS:</p>
<table class="help-table">
    <thead><tr><th>Disposition</th><th>Meaning</th><th>Visual Treatment</th></tr></thead>
    <tbody>
        <tr><td><strong>Sanctioned</strong> ✓</td><td>Process owner has formally approved this role</td><td>Green border, shield icon, "Owner Approved"</td></tr>
        <tr><td><strong>To Be Retired</strong> ⚠</td><td>Role is pending replacement with another role</td><td>Strikethrough name, faded/muted, amber border, 65% opacity</td></tr>
        <tr><td><strong>TBD</strong> ?</td><td>Disposition has not yet been determined</td><td>Dotted gray border, italic text, question mark</td></tr>
    </tbody>
</table>

<h2><i data-lucide="check-circle"></i> Baselined Badge</h2>
<p>Roles marked as "Baselined" in the process model show a green ✓ badge. This is tracked independently from disposition — a role can be both Sanctioned and Baselined.</p>

<h2><i data-lucide="download"></i> Interactive HTML Export (Role Inheritance Map)</h2>
<p>Click <strong>Export Inheritance Map</strong> in the dictionary toolbar to generate a standalone interactive HTML file.</p>

<h3>Pre-Export Filters</h3>
<p>A filter modal lets you select what to include:</p>
<ul>
    <li><strong>Include All</strong> — Bypass all filters</li>
    <li><strong>Org Groups</strong> — Multi-select which organizational groups to include</li>
    <li><strong>Disposition</strong> — Filter by Sanctioned, To Be Retired, or TBD</li>
    <li><strong>Baselined</strong> — Include only baselined or non-baselined roles</li>
    <li><strong>Include Tools</strong> — Toggle whether tools/systems are included</li>
</ul>

<h3>Dashboard View</h3>
<p>The dashboard provides a high-level overview of your role data:</p>
<ul>
    <li><strong>Stat Cards</strong> — Total Roles, Tools, Function Tags, and Relationships with animated counters</li>
    <li><strong>Function Tag Distribution</strong> — SVG donut chart showing how roles are distributed across function tag codes (with accurate counts from the function tag join table)</li>
    <li><strong>Role Disposition Breakdown</strong> — Horizontal bar chart showing Sanctioned vs. To Be Retired vs. TBD counts</li>
    <li><strong>Health Metrics</strong> — Descriptions % and Baselined % with color-coded progress bars (green ≥70%, amber ≥40%, red &lt;40%)</li>
    <li><strong>Role Types</strong> — Horizontal bar chart showing distribution across Unknown, Singular-Specific, Singular-Aggregate, Group-Specific, and Group-Aggregate</li>
</ul>

<h3>Tree View</h3>
<p>A collapsible tree showing the inheritance structure. Roles display:</p>
<ul>
    <li><strong>Disposition icons</strong> — ✓ (Sanctioned), ⚠ (To Be Retired), ? (TBD)</li>
    <li><strong>Function tag badges</strong> — Color-coded pills for each tag (e.g., BASELINED, TE-ST, TE-FT)</li>
    <li><strong>Baselined checkmark</strong> — Green ✓ if the role is baselined</li>
    <li><strong>Edit button</strong> — Click to edit all role fields inline</li>
    <li><strong>Modified indicators</strong> — Amber dot on tree nodes you have edited</li>
</ul>

<h3>Graph View (with Animations)</h3>
<p>A three-layer drill-down graph visualization with smooth animations:</p>
<table class="help-table">
    <thead><tr><th>Layer</th><th>View</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td><strong>Layer 0</strong></td><td>Cluster Overview</td><td>All connected role clusters as cards with mini disposition bars. Cards animate in with staggered slide-up effect.</td></tr>
        <tr><td><strong>Layer 1</strong></td><td>Root Roles</td><td>Root roles within a cluster, showing direct children and descendant counts. Cards animate with staggered entrance.</td></tr>
        <tr><td><strong>Layer 2</strong></td><td>Node Neighborhood</td><td>SVG view of a focused role with its parents ("INHERITS FROM") above and children ("INHERITED BY") below. Nodes pop in with bounce, arrows draw in, center node pulses on focus.</td></tr>
    </tbody>
</table>
<p>Click any cluster card to drill in, click a role card to see its neighborhood, and click the center node to open the detail panel. Use breadcrumbs at the top to navigate back.</p>

<h3>Table View</h3>
<p>A sortable data table with columns for Role Name, Function Tags, Role Type, Disposition, Baselined, Inherits From, Inherited By, and Description. Supports CSV export.</p>

<h3>Inline Editing</h3>
<p>In any view, click the <strong>Edit</strong> button on a role to modify its properties. The edit form is organized into three sections:</p>
<table class="help-table">
    <thead><tr><th>Section</th><th>Fields</th></tr></thead>
    <tbody>
        <tr><td><strong>Identity</strong></td><td>Role Name, Aliases</td></tr>
        <tr><td><strong>Classification</strong></td><td>Role Type, Disposition, Org Group, Hierarchy Level, Baselined toggle, Category</td></tr>
        <tr><td><strong>Details</strong></td><td>Description, Notes, Status (Sanctioned/To Be Retired/Deliverable/Rejected)</td></tr>
    </tbody>
</table>
<p>Edited roles show a <strong>"Modified"</strong> badge and amber dot indicator. All changes are tracked with field-level diff comparisons.</p>

<h3>Exporting Changes Back to AEGIS</h3>
<p>After editing roles in the HTML export, click the <strong>Export Changes</strong> button (appears after any edit) to review and download your changes:</p>
<ol>
    <li>A modal shows field-level diffs for every modified role (old value → new value)</li>
    <li>Click <strong>Download Changes JSON</strong> to save the file</li>
    <li>Import back into AEGIS using one of two methods:</li>
</ol>
<table class="help-table">
    <thead><tr><th>Method</th><th>Steps</th></tr></thead>
    <tbody>
        <tr><td><strong>Option A (Easiest)</strong></td><td>Copy the JSON file into the AEGIS <code>updates/</code> folder, then go to <strong>Settings → Check for Updates → click Update</strong>. The file is auto-detected and imported.</td></tr>
        <tr><td><strong>Option B (Manual)</strong></td><td>In Roles Studio → Adjudication tab, click <strong>Import Decisions</strong> and select the JSON file.</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Sharing with Stakeholders</strong>
        <p>The HTML export is designed for distribution. Send it to stakeholders who need to review the role inheritance structure without requiring AEGIS access. They can filter, search, edit roles, and export their changes as JSON for you to import back. This enables an offline review workflow.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Function Tag Accuracy</strong>
        <p>The Function Tag Distribution chart in the dashboard uses enriched data from the <code>role_function_tags</code> join table, ensuring accurate counts even when function tags are stored separately from the role dictionary. Each tag includes its code, name, and color from the <code>function_categories</code> table.</p>
    </div>
</div>
`
};

// ============================================================================
// DOCUMENT LOG
// ============================================================================
HelpDocs.content['role-documents'] = {
    title: 'Document Log',
    subtitle: 'Scan history and document tracking',
    html: `
<p>The Document Log shows all documents that have been scanned with role extraction enabled, along with summary statistics.</p>

<h2><i data-lucide="layout"></i> Accessing the Log</h2>
<p>Open Roles Studio and click <strong>Document Log</strong> in the Management section tabs.</p>

<h2><i data-lucide="list"></i> Information Displayed</h2>
<table class="help-table">
    <thead><tr><th>Column</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td><strong>Document</strong></td><td>Filename of the scanned document</td></tr>
        <tr><td><strong>Scan Date</strong></td><td>When the document was last scanned</td></tr>
        <tr><td><strong>Roles</strong></td><td>Number of roles detected</td></tr>
        <tr><td><strong>Issues</strong></td><td>Number of quality issues found</td></tr>
        <tr><td><strong>Grade</strong></td><td>Overall document quality grade</td></tr>
    </tbody>
</table>

<h2><i data-lucide="filter"></i> Features</h2>
<ul>
    <li><strong>Sort</strong> — Click column headers to sort</li>
    <li><strong>Search</strong> — Filter documents by name</li>
    <li><strong>Re-scan</strong> — Click a document to load and re-scan it</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Historical Data</strong>
        <p>The Document Log persists across sessions. Even without an active document, you can see your complete scan history and the roles detected from each.</p>
    </div>
</div>
`
};

// ============================================================================
// DATA EXPLORER
// ============================================================================
HelpDocs.content['role-data-explorer'] = {
    title: 'Data Explorer',
    subtitle: 'Deep-dive analytics for roles and responsibilities',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="bar-chart-3" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Data Explorer provides comprehensive analytics and drill-down capabilities for exploring your role and responsibility data. Visualize distributions, analyze patterns, and discover insights across your document library.</p>
    </div>
</div>

<h2><i data-lucide="navigation"></i> Accessing Data Explorer</h2>
<p>There are multiple ways to open Data Explorer:</p>
<ul>
    <li><strong>Overview Tab</strong> — Click the "Data Explorer" banner or any stat card</li>
    <li><strong>Role Details Tab</strong> — Click the <i data-lucide="search" style="width:14px;height:14px;display:inline;vertical-align:middle;"></i> explore icon on any role card</li>
    <li><strong>RACI Matrix</strong> — Click on a role name to see its detailed breakdown</li>
</ul>

<h2><i data-lucide="layout-dashboard"></i> Main Dashboard</h2>
<p>The Data Explorer dashboard shows four key visualizations:</p>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="pie-chart"></i></div>
        <h3>Category Distribution</h3>
        <p>Donut chart showing roles by category (Role, Management, Technical, Deliverable). Click segments to drill into specific categories.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="bar-chart-2"></i></div>
        <h3>Mentions Breakdown</h3>
        <p>Shows how role mentions are distributed across your documents. Identifies which documents have the most role activity.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="award"></i></div>
        <h3>Grade Distribution</h3>
        <p>Document quality grades (A-F) for scanned documents, helping identify which need the most attention.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="folder"></i></div>
        <h3>Document Categories</h3>
        <p>Breakdown by document type (PrOP, PAL, FGOST, SOW) if document type tagging is enabled.</p>
    </div>
</div>

<h2><i data-lucide="zoom-in"></i> Drill-Down Views</h2>
<p>Click any chart segment or role to drill deeper:</p>

<table class="help-table">
    <thead><tr><th>Drill-Down</th><th>What You See</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Role Details</strong></td>
            <td>All responsibilities for a role, source documents, RACI breakdown, sample contexts</td>
        </tr>
        <tr>
            <td><strong>Category View</strong></td>
            <td>All roles in a category with aggregated stats and responsibility counts</td>
        </tr>
        <tr>
            <td><strong>Document View</strong></td>
            <td>All roles found in a specific document with mention counts</td>
        </tr>
    </tbody>
</table>

<h2><i data-lucide="mouse-pointer"></i> Interactive Features</h2>
<ul>
    <li><strong>Click to Drill</strong> — Click any chart segment to see detailed breakdown</li>
    <li><strong>Back Navigation</strong> — Use breadcrumbs or back button to return</li>
    <li><strong>Hover Tooltips</strong> — Hover over chart elements for quick stats</li>
    <li><strong>Center Labels</strong> — Donut charts show totals in the center</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Quick Access from Role Cards</strong>
        <p>In the Role Details tab, each role card has an explore icon (magnifying glass with plus). Click it to jump directly to that role's Data Explorer view with full analytics.</p>
    </div>
</div>

<h2><i data-lucide="palette"></i> Chart Theming</h2>
<p>Data Explorer charts automatically adapt to your theme:</p>
<ul>
    <li><strong>Dark Mode</strong> — Charts use light text on dark backgrounds for readability</li>
    <li><strong>Light Mode</strong> — Charts use dark text on light backgrounds</li>
    <li><strong>Category Colors</strong> — Consistent colors for Role (blue), Management (green), Technical (amber), Deliverable (purple)</li>
</ul>

<h2><i data-lucide="lightbulb"></i> Best Practices</h2>
<div class="help-callout help-callout-tip">
    <i data-lucide="target"></i>
    <div>
        <strong>Start with Category Distribution</strong>
        <p>Begin your analysis by examining the category distribution chart. If you see unexpected categories (e.g., too many "Deliverables" that should be "Roles"), use the Adjudication tab to reclassify.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="trending-up"></i>
    <div>
        <strong>Track Role Coverage Across Documents</strong>
        <p>Use the Document View drill-down to identify gaps. If a key role only appears in one document, it may indicate incomplete documentation or consolidation opportunities.</p>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="layers"></i>
    <div>
        <strong>Compare Before and After</strong>
        <p>After adjudicating roles, refresh Data Explorer to see updated counts. The charts reflect your adjudication decisions, showing only confirmed roles.</p>
    </div>
</div>
`
};

// ============================================================================
// SMART SEARCH
// ============================================================================
HelpDocs.content['role-smart-search'] = {
    title: 'SmartSearch',
    subtitle: 'Intelligent autocomplete search across roles and documents',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="search" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>SmartSearch provides intelligent autocomplete search across your entire role database. As you type, it instantly shows matching roles with their categories, mention counts, and source documents.</p>
    </div>
</div>

<h2><i data-lucide="zap"></i> Features</h2>
<ul>
    <li><strong>Instant Results</strong> — Results appear as you type (debounced for performance)</li>
    <li><strong>Fuzzy Matching</strong> — Finds "Project Manager" when you type "proj man"</li>
    <li><strong>Category Colors</strong> — Results are color-coded by category</li>
    <li><strong>Mention Counts</strong> — See how many times each role appears</li>
    <li><strong>Keyboard Navigation</strong> — Use arrow keys to navigate, Enter to select</li>
</ul>

<h2><i data-lucide="navigation"></i> Using SmartSearch</h2>
<ol>
    <li><strong>Click the Search Bar</strong> — Located at the top of Roles Studio</li>
    <li><strong>Start Typing</strong> — Enter at least 2 characters</li>
    <li><strong>Browse Results</strong> — Scroll through matching roles</li>
    <li><strong>Select a Role</strong> — Click or press Enter to view details</li>
</ol>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <thead><tr><th>Key</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>↓</kbd></td><td>Move to next result</td></tr>
        <tr><td><kbd>↑</kbd></td><td>Move to previous result</td></tr>
        <tr><td><kbd>Enter</kbd></td><td>Select highlighted result</td></tr>
        <tr><td><kbd>Escape</kbd></td><td>Close dropdown</td></tr>
    </tbody>
</table>

<h2><i data-lucide="filter"></i> Search Tips</h2>
<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Search Strategies</strong>
        <ul style="margin-bottom:0;">
            <li>Search by role name: "project manager", "engineer"</li>
            <li>Search by category: "technical", "management"</li>
            <li>Search partial words: "coord" finds "Coordinator", "Coordination Lead"</li>
            <li>The search is case-insensitive</li>
        </ul>
    </div>
</div>

<h2><i data-lucide="layout"></i> Result Display</h2>
<p>Each search result shows:</p>
<ul>
    <li><strong>Role Name</strong> — The detected role title</li>
    <li><strong>Category Badge</strong> — Color-coded category (Role, Management, Technical, Deliverable)</li>
    <li><strong>Mention Count</strong> — Total mentions across all documents</li>
    <li><strong>Document Indicator</strong> — Number of documents where role appears</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Dark Mode Support</strong>
        <p>SmartSearch dropdown is fully styled for dark mode with proper contrast and readable text colors.</p>
    </div>
</div>

<h2><i data-lucide="lightbulb"></i> Best Practices</h2>

<div class="help-callout help-callout-tip">
    <i data-lucide="search"></i>
    <div>
        <strong>Find Similar Roles</strong>
        <p>Use SmartSearch to find roles that might need consolidation. Search for "lead" or "manager" to see all leadership roles, then use the Role Dictionary to merge duplicates.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="filter"></i>
    <div>
        <strong>Quick Category Filtering</strong>
        <p>Type category names like "management" or "technical" to quickly filter roles by type. This helps you focus on specific role categories during your review.</p>
    </div>
</div>

<div class="help-callout help-callout-tip">
    <i data-lucide="zap"></i>
    <div>
        <strong>Power User Workflow</strong>
        <p>Use SmartSearch as your primary navigation tool. Find a role → click to select → view in Data Explorer or Source Viewer. This is faster than scrolling through long role lists.</p>
    </div>
</div>
`
};

// ============================================================================
// STATEMENT FORGE OVERVIEW
// ============================================================================
HelpDocs.content['forge-overview'] = {
    title: 'Statement Forge',
    subtitle: 'Extract requirements, procedures, and action items for process modeling',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="hammer" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Statement Forge extracts actionable statements from your documents—requirements (shall/must), procedures (perform/verify), action items, and specifications—and structures them into hierarchical format for import into TIBCO Nimbus, process modeling tools, or compliance tracking systems.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Perfect For</strong>
        <p>SOWs, contracts, SOPs, technical procedures, requirements documents, and any document containing actionable language. Statements are automatically extracted with every scan and persisted to the database for historical analysis.</p>
    </div>
</div>

<h2><i data-lucide="sparkles"></i> Key Features</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="filter"></i></div>
        <h3>Smart Extraction</h3>
        <p>Recognizes 1,000+ action verbs across domains: requirements (shall, must), procedures (perform, verify), approvals (sign, approve), and communications (notify, submit).</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="users"></i></div>
        <h3>Actor Detection</h3>
        <p>Automatically identifies who is responsible: "The System Administrator shall..." is detected as Actor: System Administrator.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="tags"></i></div>
        <h3>Directive Classification</h3>
        <p>Categorizes by obligation level: Shall (mandatory), Must (required), Will (commitment), Should (recommended), May (optional), and Process (action steps).</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="history"></i></div>
        <h3>Persistent History</h3>
        <p>Every scan automatically stores extracted statements. View trends across scans, compare versions, and track how requirements evolve.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="edit-3"></i></div>
        <h3>Inline Editing</h3>
        <p>Click any statement to edit number, title, description, role, and directive. Changes save automatically. Undo/redo support.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="combine"></i></div>
        <h3>Merge & Split</h3>
        <p>Merge duplicate statements or split compound statements containing "and" into separate items.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="git-compare"></i></div>
        <h3>Scan Comparison</h3>
        <p>Side-by-side diff between any two scans. See added, removed, and unchanged statements with color-coded highlighting.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="download"></i></div>
        <h3>Multiple Exports</h3>
        <p>TIBCO Nimbus CSV, Excel workbook with summary sheet, JSON with full metadata, or formatted Word document.</p>
    </div>
</div>

<h2><i data-lucide="workflow"></i> Workflow</h2>
<ol>
    <li><strong>Scan Document</strong> — Load and review your document. Statement Forge extracts automatically during the scan.</li>
    <li><strong>Open Statement Forge</strong> — Click the <strong>Forge</strong> button in the navigation bar to view and refine results</li>
    <li><strong>Filter by Directive</strong> — Use the sidebar filter chips to focus on specific directive types (Shall, Must, etc.)</li>
    <li><strong>Review & Edit</strong> — Double-click statements to edit; use merge/split as needed</li>
    <li><strong>Renumber</strong> — Apply consistent numbering with your custom prefix (REQ-, PROC-, etc.)</li>
    <li><strong>Export</strong> — Download in your preferred format for import into process modeling tools</li>
</ol>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <thead><tr><th>Shortcut</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>Ctrl</kbd>+<kbd>O</kbd></td><td>Open document</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>A</kbd></td><td>Select all statements</td></tr>
        <tr><td><kbd>Shift</kbd>+Click</td><td>Select range</td></tr>
        <tr><td><kbd>Ctrl</kbd>+Click</td><td>Toggle selection</td></tr>
        <tr><td><kbd>Delete</kbd></td><td>Remove selected statements</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>M</kbd></td><td>Merge selected</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>S</kbd></td><td>Export</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Y</kbd></td><td>Undo / Redo</td></tr>
        <tr><td><kbd>Alt</kbd>+<kbd>↑↓</kbd></td><td>Move statement up/down</td></tr>
        <tr><td><kbd>Alt</kbd>+<kbd>←→</kbd></td><td>Indent / Outdent level</td></tr>
        <tr><td><kbd>F1</kbd></td><td>Help</td></tr>
    </tbody>
</table>

<h2><i data-lucide="navigation"></i> Learn More</h2>
<div class="help-path-list">
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-extraction')">
        <div class="help-path-icon"><i data-lucide="filter"></i></div>
        <div class="help-path-content"><h4>Statement Extraction</h4><p>How the extraction engine identifies actionable content</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-editing')">
        <div class="help-path-icon"><i data-lucide="edit-3"></i></div>
        <div class="help-path-content"><h4>Editing Statements</h4><p>Inline editing, merge, split, and bulk operations</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-history')">
        <div class="help-path-icon"><i data-lucide="history"></i></div>
        <div class="help-path-content"><h4>Statement History</h4><p>Historical analysis, scan comparison, document viewer, highlight-to-create</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-export')">
        <div class="help-path-icon"><i data-lucide="download"></i></div>
        <div class="help-path-content"><h4>Export Formats</h4><p>TIBCO Nimbus CSV, Excel, JSON, Word</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="database"></i>
    <div>
        <strong>Persistent Storage</strong>
        <p>Statements are automatically extracted during every document scan and stored in the database. View historical data anytime from the Scan History table or the Statement Forge sidebar.</p>
    </div>
</div>
`
};

// ============================================================================
// STATEMENT EXTRACTION
// ============================================================================
HelpDocs.content['forge-extraction'] = {
    title: 'Statement Extraction',
    subtitle: 'How Statement Forge identifies and classifies actionable content',
    html: `
<h2><i data-lucide="cog"></i> Extraction Pipeline</h2>

<p>Statement Forge uses a multi-stage pipeline to identify actionable content in your documents. Understanding how it works helps you get the best results.</p>

<h3>Stage 1: Text Segmentation</h3>
<p>The document text is split into paragraphs. Numbered sections (e.g., "3.1.2 Fire Suppression Requirements") are identified as section headers. The section hierarchy (levels 1-6) is preserved based on numbering depth.</p>

<h3>Stage 2: Directive Detection</h3>
<p>Each paragraph is scanned for <strong>directive keywords</strong> that indicate obligation or requirement levels:</p>
<table class="help-table">
    <thead><tr><th>Directive</th><th>Meaning</th><th>Example</th></tr></thead>
    <tbody>
        <tr><td><strong>Shall</strong></td><td>Mandatory requirement (strongest obligation)</td><td>"The contractor shall deliver monthly reports"</td></tr>
        <tr><td><strong>Must</strong></td><td>Required (regulatory or safety)</td><td>"All personnel must complete safety training"</td></tr>
        <tr><td><strong>Will</strong></td><td>Commitment or future action</td><td>"The system will generate audit logs"</td></tr>
        <tr><td><strong>Should</strong></td><td>Recommended practice</td><td>"Documentation should follow MIL-STD-40051"</td></tr>
        <tr><td><strong>May</strong></td><td>Optional or permissive</td><td>"The user may configure notification preferences"</td></tr>
    </tbody>
</table>

<h3>Stage 3: Role/Actor Identification</h3>
<p>The engine identifies the responsible actor from the sentence subject preceding the directive verb. Common patterns:</p>
<div class="help-check-example">
    <span class="example-good">"<strong>The Quality Manager</strong> shall review all NCRs"</span>
    <span class="example-arrow">→</span>
    <span>Role: Quality Manager</span>
</div>
<div class="help-check-example">
    <span class="example-good">"<strong>Engineering</strong> shall provide updated drawings"</span>
    <span class="example-arrow">→</span>
    <span>Role: Engineering</span>
</div>

<h3>Stage 4: Process Verb Recognition</h3>
<p>Beyond directive keywords, the engine recognizes 1,000+ action verbs organized by domain:</p>
<ul>
    <li><strong>Requirements</strong>: shall, must, require, mandate, stipulate</li>
    <li><strong>Procedures</strong>: perform, execute, verify, inspect, validate</li>
    <li><strong>Approvals</strong>: approve, sign, authorize, certify, endorse</li>
    <li><strong>Communications</strong>: notify, submit, report, distribute, transmit</li>
    <li><strong>Records</strong>: document, record, maintain, archive, retain</li>
</ul>

<h3>Stage 5: Deduplication</h3>
<p>Duplicate and near-duplicate statements are identified using fingerprint comparison (first 100 characters + directive type). Exact duplicates are automatically removed; near-duplicates are flagged for manual review.</p>

<h2><i data-lucide="settings"></i> Document Type Selection</h2>
<p>Choosing the right document type improves extraction accuracy:</p>
<ul>
    <li><strong>Procedures</strong> — Prioritizes hierarchical section detection, numbered steps, and procedural verb patterns. Best for SOPs, maintenance procedures, and compliance documents.</li>
    <li><strong>Work Instruction</strong> — Focuses on sequential action steps with role assignments and process flow. Best for step-by-step guides and task instructions.</li>
</ul>

<h2><i data-lucide="zap"></i> Automatic Extraction</h2>
<div class="help-callout help-callout-info">
    <i data-lucide="database"></i>
    <div>
        <strong>Runs With Every Scan</strong>
        <p>Statement extraction happens automatically during every document scan. Results are stored in the database so you can view historical trends, compare across scans, and track requirement changes over time.</p>
    </div>
</div>
`
};

// ============================================================================
// EDITING STATEMENTS
// ============================================================================
HelpDocs.content['forge-editing'] = {
    title: 'Editing Statements',
    subtitle: 'Refine, reorganize, and perfect extracted statements',
    html: `
<h2><i data-lucide="edit-3"></i> Inline Editing</h2>
<p>Double-click any statement row (or select it and press <kbd>Enter</kbd>) to enter edit mode. You can modify:</p>
<ul>
    <li><strong>Number</strong> — Statement reference number (e.g., "3.1.2" or "REQ-042")</li>
    <li><strong>Title</strong> — Brief title or section name</li>
    <li><strong>Description</strong> — Full statement text</li>
    <li><strong>Role</strong> — Responsible actor/organization</li>
    <li><strong>Directive</strong> — Obligation type (shall/must/will/should/may)</li>
    <li><strong>Level</strong> — Hierarchy depth (1-6)</li>
</ul>
<p>Press <kbd>Enter</kbd> to save or <kbd>Escape</kbd> to cancel. All edits support undo/redo.</p>

<h2><i data-lucide="combine"></i> Merging Statements</h2>
<p>Select two or more related statements and click <strong>Merge</strong> (or press <kbd>Ctrl+M</kbd>). The merged statement combines the descriptions and keeps the first statement's metadata. Use this when the engine splits a single requirement across multiple lines.</p>

<h2><i data-lucide="scissors"></i> Splitting Statements</h2>
<p>Select a compound statement that contains "and" joining distinct requirements. Click <strong>Split</strong> to separate it into individual statements. Each fragment inherits the original's role, directive, and level. Example:</p>
<div class="help-check-example">
    <span class="example-good">"The contractor shall deliver monthly reports <strong>and</strong> maintain inspection records"</span>
</div>
<p>Becomes two separate statements, one for reports and one for records.</p>

<h2><i data-lucide="move-vertical"></i> Reordering</h2>
<p>Drag the handle on the left side of any row to reorder. Alternatively, select a statement and use <kbd>Alt+↑</kbd> or <kbd>Alt+↓</kbd> to move it up or down.</p>

<h2><i data-lucide="indent"></i> Hierarchy Levels</h2>
<p>Use <kbd>Alt+→</kbd> to indent (increase level) or <kbd>Alt+←</kbd> to outdent (decrease level). Levels 1-6 correspond to the TIBCO Nimbus column structure and determine the visual hierarchy in exports.</p>

<h2><i data-lucide="trash-2"></i> Deleting</h2>
<p>Select one or more statements and press <kbd>Delete</kbd> or click the remove button. This is useful for removing false positives (non-actionable text that was incorrectly extracted).</p>

<h2><i data-lucide="check-square"></i> Batch Selection</h2>
<table class="help-table">
    <thead><tr><th>Action</th><th>How</th></tr></thead>
    <tbody>
        <tr><td>Select all</td><td><kbd>Ctrl</kbd>+<kbd>A</kbd></td></tr>
        <tr><td>Select range</td><td>Click first, then <kbd>Shift</kbd>+Click last</td></tr>
        <tr><td>Toggle individual</td><td><kbd>Ctrl</kbd>+Click or <kbd>Space</kbd></td></tr>
        <tr><td>Navigate</td><td><kbd>↑</kbd> / <kbd>↓</kbd> arrows</td></tr>
        <tr><td>Clear selection</td><td><kbd>Escape</kbd></td></tr>
    </tbody>
</table>

<h2><i data-lucide="hash"></i> Renumbering</h2>
<p>After editing and reordering, use the Renumber tool to apply consistent sequential numbering. Specify a custom prefix (REQ-, PROC-, WI-, etc.) and starting number. The tool respects hierarchy levels, generating numbers like "REQ-001", "REQ-001.1", "REQ-001.1.1".</p>
`
};

// ============================================================================
// STATEMENT HISTORY
// ============================================================================
HelpDocs.content['forge-history'] = {
    title: 'Statement History',
    subtitle: 'Track statement extraction results across scans with comparison and document viewer',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="history" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Statement History provides a comprehensive view of extracted statements across all scans of a document. Track how requirements evolve over time, compare extractions between document versions, view statements highlighted in their source context, and create new statements by highlighting text.</p>
    </div>
</div>

<h2><i data-lucide="door-open"></i> Accessing Statement History</h2>
<p>There are two ways to open the Statement History viewer:</p>
<ol>
    <li><strong>From Scan History</strong> — In the History tab, click the blue statement count number in the <strong>Stmts</strong> column, or click the document icon button in the Actions column. This opens the history for that specific document.</li>
    <li><strong>From Statement Forge</strong> — Click the clock icon button in the Statement Forge sidebar footer. This opens history for the currently loaded document (requires running at least one scan first).</li>
</ol>

<h2><i data-lucide="layout-dashboard"></i> Overview Dashboard</h2>
<p>The overview displays four key metrics at a glance:</p>
<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="bar-chart-2"></i></div>
        <h3>Total Scans</h3>
        <p>Number of scans performed on this document that include statement extraction data.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="file-text"></i></div>
        <h3>Latest Statement Count</h3>
        <p>Total statements extracted in the most recent scan of this document.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="users"></i></div>
        <h3>Unique Roles</h3>
        <p>Number of distinct responsible actors identified across all scans.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="tag"></i></div>
        <h3>Top Directive</h3>
        <p>The most frequently occurring directive type (shall, must, etc.) from the latest scan.</p>
    </div>
</div>

<h3>Trend Chart</h3>
<p>A line chart plots statement counts across scans over time. This reveals whether a document is growing in requirements (more statements per scan) or stabilizing.</p>

<h3>Directive Breakdown</h3>
<p>A donut chart shows the distribution of directive types (shall vs. must vs. should, etc.) from the latest scan. This helps assess the obligation balance — a document heavy on "shall" statements has many hard requirements.</p>

<h3>Scan Timeline</h3>
<p>A scrollable list of all scans for this document, showing date, statement count, role count, and top directives. Each scan has two action buttons:</p>
<ul>
    <li><strong>View</strong> — Opens the Document Viewer for that scan</li>
    <li><strong>Compare</strong> — Initiates a side-by-side comparison with another scan</li>
</ul>

<h2><i data-lucide="book-open"></i> Document Viewer</h2>
<p>The Document Viewer presents a split-panel layout:</p>
<ul>
    <li><strong>Left Panel — Source Document</strong>: The original document text with extracted statements highlighted using directive-specific colors (blue for shall, red for must, amber for will, green for should, purple for may). Click any highlight to scroll the detail panel to that statement.</li>
    <li><strong>Right Panel — Statement List</strong>: A filterable, scrollable list of all extracted statements with their number, directive badge, role, and description. Filter chips at the top let you focus on specific directive types. Click any statement to scroll to its location in the document.</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="code"></i>
    <div>
        <strong>Rich HTML Rendering <span class="help-badge help-badge-new">v4.3.0</span></strong>
        <p>New scans (v4.3.0+) render documents as rich HTML with proper tables, headings, bold, and italic formatting — powered by the mammoth extraction engine. Older scans without HTML data automatically fall back to plain-text rendering. The viewer automatically selects the best rendering path based on available data.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="mouse-pointer"></i>
    <div>
        <strong>Highlight-to-Create</strong>
        <p>Select any text in the document panel to see a creation popup. Statement Forge auto-detects the directive type from your selection and lets you assign a role. Click "Create" to add the statement to the extraction set. This is invaluable for catching statements the automatic extraction missed.</p>
    </div>
</div>

<h2><i data-lucide="git-compare"></i> Unified Compare Viewer</h2>
<p>The compare viewer displays a single document with diff-aware highlights, showing how statements changed between two scans. Since both scans reference the same document, a unified view avoids duplication and lets you see all changes in context.</p>

<table class="help-table">
    <thead><tr><th>Category</th><th>Color</th><th>Badge</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td><strong>Unchanged</strong></td><td>Normal directive colors</td><td>—</td><td>Statement exists in both scans with identical content</td></tr>
        <tr><td><strong>Added</strong></td><td style="color: #22c55e;">Green</td><td>NEW</td><td>Statement in the newer scan that was not in the older scan</td></tr>
        <tr><td><strong>Removed</strong></td><td style="color: #ef4444;">Red + strikethrough</td><td>REMOVED</td><td>Statement in the older scan that is missing from the newer scan</td></tr>
        <tr><td><strong>Modified</strong></td><td style="color: #f59e0b;">Amber</td><td>CHANGED</td><td>Statement text matches but directive, role, or level changed between scans</td></tr>
    </tbody>
</table>

<h3>Diff Summary & Filters</h3>
<p>A summary bar at the top shows counts for each diff category. Below that, two rows of filter chips let you narrow the view:</p>
<ul>
    <li><strong>Row 1 — Directive filters</strong>: Filter by shall, must, will, should, may</li>
    <li><strong>Row 2 — Diff status filters</strong>: Filter by Added, Removed, Modified, Unchanged</li>
</ul>
<p>Filters combine — selecting "Must" + "Added" shows only newly added must-statements.</p>

<h3>Field-Level Diff</h3>
<p>When you click a modified statement, the detail panel shows exactly which fields changed between the older and newer scan (e.g., "Directive: Must → Should", "Role: Inspector → Quality Manager").</p>

<h3>Compare Keyboard Shortcuts</h3>
<table class="help-table">
    <thead><tr><th>Key</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>a</kbd></td><td>Jump to next added statement</td></tr>
        <tr><td><kbd>r</kbd></td><td>Jump to next removed statement</td></tr>
        <tr><td><kbd>m</kbd></td><td>Jump to next modified statement</td></tr>
        <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Navigate through all statements</td></tr>
        <tr><td><kbd>e</kbd></td><td>Edit current statement (newer scan only)</td></tr>
        <tr><td><kbd>Esc</kbd></td><td>Close compare viewer</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-warning">
    <i data-lucide="alert-triangle"></i>
    <div>
        <strong>Two-Tier Fingerprint Matching</strong>
        <p>Statements are matched using two fingerprints: a description-only fingerprint (first 100 characters) for identity matching, and a full fingerprint (description + directive + role) for exact matching. If the description matches but directive/role differs, the statement is classified as "modified" rather than appearing as separate add/remove entries.</p>
    </div>
</div>

<h2><i data-lucide="navigation"></i> Related Topics</h2>
<div class="help-path-list">
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-extraction')">
        <div class="help-path-icon"><i data-lucide="filter"></i></div>
        <div class="help-path-content"><h4>Statement Extraction</h4><p>How the extraction pipeline identifies actionable content</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('forge-export')">
        <div class="help-path-icon"><i data-lucide="download"></i></div>
        <div class="help-path-content"><h4>Export Formats</h4><p>Download statements as Nimbus CSV, Excel, JSON, or Word</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
</div>
`
};

// ============================================================================
// STATEMENT SEARCH (v4.4.0)
// ============================================================================
HelpDocs.content['forge-search'] = {
    title: 'Statement Search',
    subtitle: 'Search across all scans to find specific statements',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="search" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Statement Search lets you find specific statements across all scans and documents in your history. Search by description text, title, or keyword and jump directly to the relevant scan's document viewer. <span class="help-badge help-badge-new">v4.4.0</span></p>
    </div>
</div>

<h2><i data-lucide="search"></i> Using Statement Search</h2>
<p>The search bar appears in the Statement History overview dashboard, between the stat tiles and the charts section.</p>
<ol>
    <li>Open Statement History from Scan History or Statement Forge</li>
    <li>Type at least 2 characters in the search bar</li>
    <li>Results appear automatically after a 300ms debounce delay</li>
    <li>Click any result to open that scan's Document Viewer with the statement highlighted</li>
</ol>

<h3>Search Results</h3>
<p>Each result shows:</p>
<ul>
    <li><strong>Directive badge</strong> — color-coded pill (Shall, Must, Will, Should, May)</li>
    <li><strong>Document name</strong> and <strong>scan date</strong> for context</li>
    <li><strong>Description excerpt</strong> — first 120 characters of the matching statement</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="filter"></i>
    <div>
        <strong>Directive Filtering</strong>
        <p>The search API supports an optional directive filter parameter. Results are limited to 50 matches by default, with a maximum of 200.</p>
    </div>
</div>
`
};

// ============================================================================
// BULK STATEMENT EDITING (v4.4.0)
// ============================================================================
HelpDocs.content['forge-bulk-edit'] = {
    title: 'Bulk Statement Editing',
    subtitle: 'Select and update multiple statements at once',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="check-square" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Bulk Editing lets you select multiple statements in the Document Viewer and update their directive type or role assignment in a single operation. This is ideal for cleaning up extraction results or standardizing statement metadata across a scan. <span class="help-badge help-badge-new">v4.4.0</span></p>
    </div>
</div>

<h2><i data-lucide="toggle-left"></i> Activating Bulk Mode</h2>
<ol>
    <li>Open a scan in the Document Viewer</li>
    <li>Click the <strong>Bulk Edit</strong> toggle button in the toolbar (above the document)</li>
    <li>A bulk action bar appears at the top of the statement detail panel</li>
    <li>Checkboxes appear next to each statement in the detail panel</li>
</ol>

<h2><i data-lucide="check-square"></i> Selecting Statements</h2>
<p>Click the checkbox next to any statement to select it. The bulk action bar displays the current selection count. You can select as many statements as needed.</p>

<h2><i data-lucide="edit-3"></i> Applying Bulk Updates</h2>
<p>With statements selected:</p>
<ol>
    <li>Choose a <strong>Directive</strong> from the dropdown (Shall, Must, Will, Should, May) and/or type a <strong>Role</strong> name</li>
    <li>Click <strong>Apply</strong> to update all selected statements</li>
    <li>Click <strong>Clear</strong> to deselect all statements without making changes</li>
</ol>

<div class="help-callout help-callout-warning">
    <i data-lucide="alert-triangle"></i>
    <div>
        <strong>Batch Limit</strong>
        <p>You can update up to 500 statements per batch operation. Only the fields you specify will be updated — blank fields are left unchanged.</p>
    </div>
</div>
`
};

// ============================================================================
// PDF.js VIEWER (v4.4.0)
// ============================================================================
HelpDocs.content['forge-pdf-viewer'] = {
    title: 'PDF Viewer',
    subtitle: 'Pixel-perfect PDF rendering alongside the HTML view',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="file" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>The PDF Viewer uses PDF.js to render the original PDF document at pixel-perfect fidelity inside the Statement History Document Viewer. Toggle between the HTML view (with highlights) and the PDF view (exact original layout) for PDF documents. <span class="help-badge help-badge-new">v4.4.0</span></p>
    </div>
</div>

<h2><i data-lucide="toggle-left"></i> Using the PDF/HTML Toggle</h2>
<p>When viewing a PDF document in the Document Viewer, a toggle appears in the document header:</p>
<ul>
    <li><strong>HTML</strong> — The default view. Rendered HTML with statement highlights, click-to-navigate, and filter chips.</li>
    <li><strong>PDF</strong> — Pixel-perfect rendering of the original PDF file. Each page is displayed as a canvas element with a page number label.</li>
</ul>
<p>The toggle only appears for PDF documents. DOCX documents always use the HTML view.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>File Availability</strong>
        <p>The PDF view requires the original document file to still be available on the server (in the temp/ directory). If the file has been cleaned up, the PDF view will show an error message and you can switch back to the HTML view.</p>
    </div>
</div>

<h3>How It Works</h3>
<p>PDF.js (v4.2.67) is loaded as an ESM module. Each page of the PDF is rendered to an HTML canvas element at 1.5x scale for crisp text. The viewer handles multi-page documents with proper page breaks and numbering.</p>
`
};

// ============================================================================
// STATEMENT DIFF EXPORT (v4.4.0)
// ============================================================================
HelpDocs.content['forge-diff-export'] = {
    title: 'Diff Export',
    subtitle: 'Export compare results as CSV or PDF',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="download" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Export the results of a statement comparison as a CSV spreadsheet or an AEGIS-branded PDF report. Diff exports capture all statement changes (added, removed, modified, unchanged) with their details, making it easy to share comparison results with stakeholders. <span class="help-badge help-badge-new">v4.4.0</span></p>
    </div>
</div>

<h2><i data-lucide="download"></i> Export Buttons</h2>
<p>When viewing a comparison in the Unified Compare Viewer, export buttons appear in the diff summary bar:</p>
<ul>
    <li><strong>CSV</strong> — Downloads a UTF-8 CSV file with columns: Number, Title, Description, Directive, Role, Level, Diff Status, Changed Fields</li>
    <li><strong>PDF</strong> — Downloads an AEGIS-branded PDF report with summary statistics and a color-coded statement table</li>
</ul>

<h3>CSV Format</h3>
<p>The CSV includes all statements from both scans with their diff status. The "Changed Fields" column lists which fields were modified (e.g., "directive, role") for statements classified as "modified". Opens cleanly in Excel, Google Sheets, and other spreadsheet tools.</p>

<h3>PDF Report</h3>
<p>The PDF report includes:</p>
<ul>
    <li>AEGIS-branded header with gold accent</li>
    <li>Document name and scan date range</li>
    <li>Summary table with counts for each diff category</li>
    <li>Full statement detail table with color-coded rows: green for added, red for removed, amber for modified</li>
</ul>
`
};

// ============================================================================
// STATEMENT FORGE EXPORT
// ============================================================================
HelpDocs.content['forge-export'] = {
    title: 'Export Formats',
    subtitle: 'Download extracted statements in production-ready formats',
    html: `
<h2><i data-lucide="download"></i> Available Formats</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="file-spreadsheet"></i></div>
        <h3>TIBCO Nimbus CSV</h3>
        <p>The primary production format. 12 columns (Level 1-6 with descriptions), UTF-8 with BOM encoding. Role appears on the first line of the description cell, followed by a blank line, then the statement text. This format is directly importable into TIBCO Nimbus for process modeling.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="table"></i></div>
        <h3>Excel Workbook (.xlsx)</h3>
        <p>Two-sheet workbook. The "Statements" sheet uses the same Level 1-6 hierarchical structure with header formatting. The "Summary" sheet includes source document name, export date, total statement count, and directive breakdown (shall/must/will/should/may counts).</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="code"></i></div>
        <h3>JSON</h3>
        <p>Complete metadata export with a structured <code>metadata</code> block (source, timestamp, counts) and a <code>statements</code> array containing every field: number, title, description, level, role, directive, section, is_header, and notes.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="file-text"></i></div>
        <h3>Word Document (.docx)</h3>
        <p>Formatted report with a title page (source document, generation date, total count), followed by statements organized hierarchically with role headings, bold numbering, italic titles, and directive badges. Ready for stakeholder review.</p>
    </div>
</div>

<h2><i data-lucide="alert-circle"></i> TIBCO Nimbus Format Notes</h2>
<div class="help-callout help-callout-warning">
    <i data-lucide="alert-triangle"></i>
    <div>
        <strong>Production Format — Do Not Modify Structure</strong>
        <p>The Nimbus CSV uses a specific 12-column layout that production systems depend on. The column structure (Level 1, Level 1 Description, Level 2, Level 2 Description, etc.) must be preserved exactly. Each statement occupies one row, placed in the columns corresponding to its hierarchy level.</p>
    </div>
</div>

<h2><i data-lucide="workflow"></i> Export Workflow</h2>
<ol>
    <li>Click the <strong>Export</strong> dropdown in the Statement Forge toolbar</li>
    <li>Select your desired format</li>
    <li>The file downloads immediately with an auto-generated filename including the source document name and timestamp</li>
    <li>For Nimbus CSV, validate the output using the built-in format validator before importing into production systems</li>
</ol>
`
};

// ============================================================================
// EXPORT OVERVIEW
// ============================================================================
HelpDocs.content['export-overview'] = {
    title: 'Export Options',
    subtitle: 'Create deliverables from your review results',
    html: `
<div class="help-export-grid">
    <div class="help-export-card" onclick="HelpContent.navigateTo('export-word')">
        <div class="help-export-card-icon"><i data-lucide="file-text"></i></div>
        <h3>Word Document</h3>
        <p>Original document with tracked changes and comments.</p>
        <span class="help-badge">Recommended</span>
    </div>
    <div class="help-export-card" onclick="HelpContent.navigateTo('export-data')">
        <div class="help-export-card-icon"><i data-lucide="table"></i></div>
        <h3>Excel / CSV</h3>
        <p>Tabular issue list for tracking and reporting.</p>
    </div>
    <div class="help-export-card" onclick="HelpContent.navigateTo('export-json')">
        <div class="help-export-card-icon"><i data-lucide="code"></i></div>
        <h3>JSON</h3>
        <p>Structured data for automation.</p>
    </div>
</div>

<h2><i data-lucide="filter"></i> What Gets Exported</h2>
<p>By default, exports include "Kept" issues. Configure to include all, pending only, or specific statuses.</p>

<h2><i data-lucide="keyboard"></i> Quick Export</h2>
<p>Press <kbd>Ctrl</kbd>+<kbd>E</kbd> to open the export dialog.</p>
`
};

// ============================================================================
// WORD EXPORT
// ============================================================================
HelpDocs.content['export-word'] = {
    title: 'Word Document Export',
    subtitle: 'Generate a marked-up copy with tracked changes',
    html: `
<h2><i data-lucide="help-circle"></i> Why Word Export?</h2>
<ul>
    <li><strong>Context preserved</strong> — See issues in original location</li>
    <li><strong>Familiar interface</strong> — Use Word's review tools</li>
    <li><strong>Easy collaboration</strong> — Share with authors</li>
    <li><strong>Accept/Reject workflow</strong> — Implement fixes directly</li>
</ul>

<h2><i data-lucide="file-text"></i> What's Included</h2>
<h3>Tracked Changes</h3>
<p>For issues with suggestions:</p>
<div class="help-check-example">
    <span class="example-bad" style="text-decoration: line-through;">utilize</span>
    <span class="example-good" style="text-decoration: underline;">use</span>
</div>

<h3>Comments</h3>
<p>Issue message, severity, and suggestion anchored to flagged text.</p>

<h2><i data-lucide="settings"></i> Options</h2>
<ul>
    <li>Changes + Comments (default)</li>
    <li>Comments Only</li>
    <li>Include Info issues</li>
    <li>Author name for attribution</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip</strong>
        <p>Use Triage Mode first. Only "Kept" issues appear in export by default.</p>
    </div>
</div>
`
};

// ============================================================================
// CSV/EXCEL EXPORT
// ============================================================================
HelpDocs.content['export-data'] = {
    title: 'CSV & Excel Export',
    subtitle: 'Tabular data for tracking and analysis',
    html: `
<h2><i data-lucide="table"></i> Excel Export (.xlsx)</h2>
<ul>
    <li>Formatted headers with filters</li>
    <li>Color-coded severity</li>
    <li>Summary sheet with statistics</li>
</ul>

<h2><i data-lucide="file-spreadsheet"></i> CSV Export</h2>
<ul>
    <li>UTF-8 encoding</li>
    <li>Standard format</li>
    <li>One row per issue</li>
</ul>

<h2><i data-lucide="columns"></i> Columns</h2>
<table class="help-table help-table-compact">
    <tbody>
        <tr><td>ID</td><td>Unique identifier</td></tr>
        <tr><td>Severity</td><td>Critical, High, Medium, Low, Info</td></tr>
        <tr><td>Category</td><td>Checker name</td></tr>
        <tr><td>Message</td><td>Issue description</td></tr>
        <tr><td>Flagged Text</td><td>Problematic text</td></tr>
        <tr><td>Suggestion</td><td>Recommended fix</td></tr>
        <tr><td>Status</td><td>Pending, Kept, Suppressed, Fixed</td></tr>
    </tbody>
</table>

<h2><i data-lucide="bar-chart"></i> Use Cases</h2>
<ul>
    <li>Issue tracking (Jira, Azure DevOps)</li>
    <li>Metrics dashboard</li>
    <li>Quality reporting</li>
    <li>Auditing</li>
</ul>
`
};

// ============================================================================
// JSON EXPORT
// ============================================================================
HelpDocs.content['export-json'] = {
    title: 'JSON Export',
    subtitle: 'Structured data for automation',
    html: `
<h2><i data-lucide="code"></i> Structure</h2>
<pre class="help-code">{
  "metadata": { "version": "3.0.52", "document": "spec.docx" },
  "summary": { "total_issues": 47, "score": 85, "grade": "B+" },
  "issues": [
    {
      "id": "issue-001",
      "severity": "high",
      "category": "acronyms",
      "message": "Undefined acronym",
      "flagged": "SRR",
      "suggestion": "Define on first use"
    }
  ]
}</pre>

<h2><i data-lucide="workflow"></i> Use Cases</h2>
<ul>
    <li><strong>CI/CD integration</strong> — Fail builds on critical issues</li>
    <li><strong>Custom reporting</strong> — Generate tailored reports</li>
    <li><strong>Data aggregation</strong> — Combine multiple documents</li>
    <li><strong>API integration</strong> — Post to tracking systems</li>
</ul>
`
};

// ============================================================================
// FIX ASSISTANT - OVERVIEW
// ============================================================================
HelpDocs.content['fix-overview'] = {
    title: 'Fix Assistant v2',
    subtitle: 'Premium triage interface for reviewing automatic fixes',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="wand-2" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Fix Assistant v2 is a premium document review interface that helps you triage automatic fixes with confidence scoring, pattern learning, undo/redo support, and rich export options including tracked changes and reviewer comments.</p>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="sparkles"></i>
    <div>
        <strong>AI-Assisted Review</strong>
        <p>Each fix is scored by confidence (Safe/Review/Caution). The system learns from your decisions to improve future suggestions.</p>
    </div>
</div>

<h2><i data-lucide="sparkles"></i> Key Features</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="shield-check"></i></div>
        <h3>Confidence Scoring</h3>
        <p>Each fix is categorized as Safe (auto-accept recommended), Review (human judgment needed), or Caution (verify carefully).</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="eye"></i></div>
        <h3>Before/After Preview</h3>
        <p>See the original text alongside the proposed change with highlighted differences.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="file-text"></i></div>
        <h3>Two-Panel Document View</h3>
        <p>Full document viewer with page navigation, mini-map, and fix position markers.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="rotate-ccw"></i></div>
        <h3>Undo/Redo</h3>
        <p>Change your mind? Undo any decision. Full history of all actions.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="brain"></i></div>
        <h3>Pattern Learning</h3>
        <p>The system tracks your decisions to learn which patterns you accept or reject. No cloud AI—just smart pattern matching.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="book-open"></i></div>
        <h3>Custom Dictionary</h3>
        <p>Add terms to always skip. Your dictionary persists across sessions.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="search"></i></div>
        <h3>Search & Filter</h3>
        <p>Find specific fixes by text, category, or confidence level.</p>
    </div>
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="download"></i></div>
        <h3>Rich Export</h3>
        <p>Export with tracked changes (accepted) and comments (rejected with notes).</p>
    </div>
</div>

<h2><i data-lucide="keyboard"></i> Keyboard Shortcuts</h2>
<table class="help-table">
    <thead><tr><th>Shortcut</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td><kbd>A</kbd></td><td>Accept current fix</td></tr>
        <tr><td><kbd>R</kbd></td><td>Reject current fix</td></tr>
        <tr><td><kbd>S</kbd></td><td>Skip current fix</td></tr>
        <tr><td><kbd>U</kbd> or <kbd>Ctrl</kbd>+<kbd>Z</kbd></td><td>Undo last action</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd></td><td>Redo</td></tr>
        <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Navigate fixes</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>F</kbd></td><td>Search fixes</td></tr>
    </tbody>
</table>

<h2><i data-lucide="navigation"></i> Learn More</h2>
<div class="help-path-list">
    <div class="help-path-card" onclick="HelpContent.navigateTo('fix-workflow')">
        <div class="help-path-icon"><i data-lucide="workflow"></i></div>
        <div class="help-path-content"><h4>Review Workflow</h4><p>Step-by-step guide to reviewing fixes</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('fix-learning')">
        <div class="help-path-icon"><i data-lucide="brain"></i></div>
        <div class="help-path-content"><h4>Pattern Learning</h4><p>How the system learns from your decisions</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
    <div class="help-path-card" onclick="HelpContent.navigateTo('fix-export')">
        <div class="help-path-icon"><i data-lucide="download"></i></div>
        <div class="help-path-content"><h4>Export Options</h4><p>Tracked changes, comments, and reports</p></div>
        <i data-lucide="chevron-right" class="help-path-arrow"></i>
    </div>
</div>
`
};

// ============================================================================
// FIX ASSISTANT - WORKFLOW
// ============================================================================
HelpDocs.content['fix-workflow'] = {
    title: 'Review Workflow',
    subtitle: 'Step-by-step guide to reviewing fixes',
    html: `
<h2><i data-lucide="workflow"></i> The Review Process</h2>
<ol>
    <li><strong>Run a Review</strong> — Load a document and run a review with your preferred presets</li>
    <li><strong>Open Fix Assistant</strong> — Click <strong>Fix Assistant</strong> in the Review panel or press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>F</kbd></li>
    <li><strong>Review Fixes</strong> — Each fix shows the issue, suggested change, and confidence level</li>
    <li><strong>Make Decisions</strong> — Accept, Reject, or Skip each fix</li>
    <li><strong>Add Notes</strong> — Optionally add reviewer notes to rejected fixes</li>
    <li><strong>Export</strong> — Download with tracked changes and/or comments</li>
</ol>

<h2><i data-lucide="target"></i> Confidence Levels</h2>
<table class="help-table">
    <thead><tr><th>Level</th><th>Badge</th><th>Meaning</th><th>Recommendation</th></tr></thead>
    <tbody>
        <tr><td><strong>Safe</strong></td><td style="color: #22c55e;">●</td><td>High confidence fix (95%+)</td><td>Usually safe to auto-accept</td></tr>
        <tr><td><strong>Review</strong></td><td style="color: #eab308;">●</td><td>Medium confidence (70-95%)</td><td>Human review recommended</td></tr>
        <tr><td><strong>Caution</strong></td><td style="color: #ef4444;">●</td><td>Lower confidence (&lt;70%)</td><td>Verify carefully before accepting</td></tr>
    </tbody>
</table>

<h2><i data-lucide="zap"></i> Bulk Actions</h2>
<ul>
    <li><strong>Accept All Safe</strong> — Accept all fixes with Safe confidence</li>
    <li><strong>Accept All</strong> — Accept all remaining fixes</li>
    <li><strong>Reject All</strong> — Reject all remaining fixes</li>
    <li><strong>Reset All</strong> — Clear all decisions and start over</li>
</ul>

<h2><i data-lucide="save"></i> Progress Persistence</h2>
<p>Your progress is automatically saved to localStorage. Close the browser and come back later—your decisions are preserved.</p>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Live Preview Mode</strong>
        <p>Enable Live Preview to see how the document would look with all accepted changes applied in real-time.</p>
    </div>
</div>
`
};

// ============================================================================
// FIX ASSISTANT - LEARNING
// ============================================================================
HelpDocs.content['fix-learning'] = {
    title: 'Pattern Learning',
    subtitle: 'How Fix Assistant learns from your decisions',
    html: `
<h2><i data-lucide="brain"></i> Learning System</h2>
<p>Fix Assistant tracks patterns in your decisions to improve future suggestions. This is <strong>not cloud AI</strong>—it's deterministic pattern matching based on your choices stored locally.</p>

<h2><i data-lucide="database"></i> What Gets Tracked</h2>
<ul>
    <li><strong>Issue patterns</strong> — Which types of issues you typically accept or reject</li>
    <li><strong>Context patterns</strong> — Surrounding text that correlates with your decisions</li>
    <li><strong>Category preferences</strong> — Grammar vs spelling vs style preferences</li>
    <li><strong>Skip patterns</strong> — Content you consistently skip</li>
</ul>

<h2><i data-lucide="bar-chart-2"></i> Viewing Statistics</h2>
<p>Click the <strong>Stats</strong> button in Fix Assistant to see:</p>
<ul>
    <li>Total fixes reviewed</li>
    <li>Accept/Reject/Skip ratios by category</li>
    <li>Most common patterns</li>
    <li>Learning confidence over time</li>
</ul>

<h2><i data-lucide="book-open"></i> Custom Dictionary</h2>
<p>Add terms that should always be skipped:</p>
<ul>
    <li>Product names and trademarks</li>
    <li>Industry-specific terminology</li>
    <li>Acronyms unique to your organization</li>
    <li>Names and proper nouns</li>
</ul>

<h2><i data-lucide="refresh-cw"></i> Resetting Learning</h2>
<p>Clear the learning database via Settings → Fix Assistant → Reset Learning Data. Your custom dictionary is preserved.</p>
`
};

// ============================================================================
// FIX ASSISTANT - EXPORT
// ============================================================================
HelpDocs.content['fix-export'] = {
    title: 'Export Options',
    subtitle: 'Export reviewed documents with changes and comments',
    html: `
<h2><i data-lucide="download"></i> Export Formats</h2>

<h3>Word Document with Tracked Changes</h3>
<p>Exports a .docx file where:</p>
<ul>
    <li><strong>Accepted fixes</strong> → Applied as tracked changes (insertions/deletions)</li>
    <li><strong>Rejected fixes</strong> → Inserted as comments with your reviewer notes</li>
    <li>Original formatting preserved</li>
</ul>

<h3>PDF Summary Report</h3>
<p>Generates a PDF report containing:</p>
<ul>
    <li>Executive summary of changes</li>
    <li>Statistics by category</li>
    <li>List of all accepted changes</li>
    <li>List of rejected items with reasons</li>
    <li>Reviewer name and timestamp</li>
</ul>

<h3>JSON Data Export</h3>
<p>Machine-readable export for integration with other tools:</p>
<pre class="help-code">
{
  "accepted": [...],
  "rejected": [...],
  "skipped": [...],
  "statistics": {...},
  "timestamp": "2026-01-29T..."
}
</pre>

<h2><i data-lucide="settings"></i> Export Settings</h2>
<ul>
    <li><strong>Include timestamps</strong> — Add review date to comments</li>
    <li><strong>Reviewer name</strong> — Name shown in tracked changes</li>
    <li><strong>Comment prefix</strong> — Prefix for comment text (e.g., "[TWR]")</li>
    <li><strong>Include statistics</strong> — Add summary at end of document</li>
</ul>
`
};

// ============================================================================
// HYPERLINK HEALTH - OVERVIEW
// ============================================================================
HelpDocs.content['hyperlink-overview'] = {
    title: 'Hyperlink Health',
    subtitle: 'Validate all URLs in your documents',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="link" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Hyperlink Health validates every URL in your documents—checking for broken links, redirects, SSL issues, and missing destinations. Get a comprehensive status report before publishing.</p>
    </div>
</div>

<h2><i data-lucide="file-type"></i> Supported File Types</h2>
<div class="help-formats" style="margin-bottom: 16px;">
    <span class="format-badge format-primary">.docx (Word)</span>
    <span class="format-badge format-primary">.xlsx / .xls (Excel)</span>
    <span class="format-badge">.pdf</span>
    <span class="format-badge">.txt</span>
</div>
<p>Word and Excel files provide the richest hyperlink extraction, capturing embedded links, HYPERLINK fields, and cell formulas.</p>

<h2><i data-lucide="check-circle"></i> What Gets Checked</h2>
<ul>
    <li><strong>HTTP/HTTPS URLs</strong> — Web links, API endpoints</li>
    <li><strong>File links</strong> — References to local files</li>
    <li><strong>Email links</strong> — mailto: addresses</li>
    <li><strong>Internal anchors</strong> — #bookmark references</li>
    <li><strong>HYPERLINK fields</strong> — Extracted from Word DOCX files</li>
    <li><strong>Excel hyperlinks</strong> — Cell hyperlinks, HYPERLINK formulas, and linked objects from .xlsx/.xls files</li>
</ul>

<h2><i data-lucide="settings"></i> Validation Modes</h2>
<p>Choose a validation mode in Settings → Hyperlink Validation:</p>
<table class="help-table">
    <thead><tr><th>Mode</th><th>Description</th><th>Best For</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Offline</strong></td>
            <td>Format/syntax validation only. Checks URL structure without network access. Marks valid formats as "Format OK" without verifying accessibility.</td>
            <td>Air-gapped systems, quick format checks, or when you don't want to hit external servers</td>
        </tr>
        <tr>
            <td><strong>Validator</strong></td>
            <td>Full HTTP validation with Windows integrated authentication (NTLM/Negotiate SSO). Makes actual HTTP requests to verify each URL is accessible.</td>
            <td>Standard validation when you have network access and need to verify links actually work</td>
        </tr>
    </tbody>
</table>

<h3>Validator Mode Features</h3>
<p>The Validator mode is optimized for government and enterprise sites:</p>
<ul>
    <li><strong>Windows SSO Authentication</strong> — Automatically uses your Windows credentials (NTLM/Negotiate) to access authenticated resources like SharePoint, internal wikis, and government portals</li>
    <li><strong>Robust Retry Logic</strong> — Exponential backoff with configurable retries for slow government servers</li>
    <li><strong>Government Site Compatibility</strong> — Extended timeouts, realistic browser headers, and handling of authentication challenges</li>
    <li><strong>Redirect Chain Tracking</strong> — Follows and records redirect chains up to 5 hops</li>
    <li><strong>SSL Certificate Verification</strong> — Validates certificate chains and warns about expiring certificates</li>
    <li><strong>HEAD/GET Fallback</strong> — Automatically falls back to GET if HEAD requests are blocked (common on government sites)</li>
    <li><strong>Rate Limiting Detection</strong> — Recognizes 429 responses and reports them appropriately</li>
</ul>

<h3>Authentication Options (v3.0.123)</h3>
<p>Configure authentication in Settings → Hyperlink Validation → Advanced Authentication Settings:</p>
<table class="help-table">
    <thead><tr><th>Method</th><th>Use Case</th><th>Configuration</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Windows SSO</strong></td>
            <td>SharePoint, internal wikis, Windows-authenticated sites</td>
            <td>Automatic when <code>requests-negotiate-sspi</code> is installed</td>
        </tr>
        <tr>
            <td><strong>CAC/PIV Certificate</strong></td>
            <td>.mil sites, federal PKI-protected resources (DLA, DISA, etc.)</td>
            <td>Set Client Certificate and Private Key paths (.pem files)</td>
        </tr>
        <tr>
            <td><strong>Custom CA Bundle</strong></td>
            <td>Government sites with DoD/Federal PKI certificates</td>
            <td>Set CA Certificate Bundle path (DoD root CA bundle)</td>
        </tr>
        <tr>
            <td><strong>Proxy Server</strong></td>
            <td>Enterprise networks with mandatory proxy</td>
            <td>Set Proxy Server URL (e.g., http://proxy.corp.mil:8080)</td>
        </tr>
    </tbody>
</table>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>DoD CAC/PIV Setup</strong>
        <p>For CAC authentication to .mil sites: Export your certificate and private key from your CAC card to PEM files. The DoD PKI CA bundle can be downloaded from <a href="https://militarycac.com" target="_blank">MilitaryCAC.com</a> or your organization's PKI administrator.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Windows SSO Package</strong>
        <p>For automatic Windows authentication, install: <code>pip install requests-negotiate-sspi</code> (Windows) or <code>pip install requests-ntlm</code> (cross-platform).</p>
    </div>
</div>

<h2><i data-lucide="table"></i> Excel Hyperlink Extraction</h2>
<p>For Excel files (.xlsx, .xls), the validator extracts hyperlinks from:</p>
<ul>
    <li><strong>Cell hyperlinks</strong> — Links applied directly to cells</li>
    <li><strong>HYPERLINK formulas</strong> — =HYPERLINK("url", "text") functions</li>
    <li><strong>Named ranges</strong> — Hyperlinks in named range definitions</li>
    <li><strong>All worksheets</strong> — Scans every sheet in the workbook</li>
</ul>
<p>Results show the sheet name, cell reference, display text, and target URL for each link found.</p>

<h2><i data-lucide="activity"></i> Validation Results</h2>
<table class="help-table">
    <thead><tr><th>Status</th><th>Icon</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td><strong>Valid</strong></td><td style="color: #22c55e;">✓</td><td>URL responds with 200 OK</td></tr>
        <tr><td><strong>Redirect</strong></td><td style="color: #eab308;">→</td><td>URL redirects (301/302/307/308)</td></tr>
        <tr><td><strong>Broken</strong></td><td style="color: #ef4444;">✗</td><td>URL returns 404 or connection failed</td></tr>
        <tr><td><strong>Auth Required</strong></td><td style="color: #f97316;">🔐</td><td>401 Unauthorized — link exists but requires credentials beyond current Windows auth</td></tr>
        <tr><td><strong>Blocked</strong></td><td style="color: #ef4444;">🚫</td><td>403 Forbidden — access denied or requires specific permissions</td></tr>
        <tr><td><strong>SSL Error</strong></td><td style="color: #ef4444;">🔓</td><td>Certificate problem — expired, self-signed, or untrusted CA</td></tr>
        <tr><td><strong>DNS Failed</strong></td><td style="color: #ef4444;">⚠</td><td>Could not resolve hostname — domain may not exist</td></tr>
        <tr><td><strong>Timeout</strong></td><td style="color: #f97316;">⏱</td><td>Server didn't respond in time</td></tr>
        <tr><td><strong>Rate Limited</strong></td><td style="color: #f97316;">⏳</td><td>429 Too Many Requests — server is limiting requests</td></tr>
        <tr><td><strong>Skipped</strong></td><td style="color: #6b7280;">○</td><td>Not validated (internal/mailto) or matched exclusion rule</td></tr>
        <tr><td><strong>Format OK</strong></td><td style="color: #3b82f6;">✓</td><td>Valid URL format (Offline mode — not network verified)</td></tr>
    </tbody>
</table>

<h2><i data-lucide="eye"></i> Interactive Results</h2>
<p>After validation, the results view provides several interactive features:</p>

<h3>Clickable Stat Tiles (v4.6.2)</h3>
<p>Click any summary stat card (Excellent, Broken, Blocked, Timeout, etc.) to filter results to that status category. The active tile shows a gold border and checkmark. Click again to deselect.</p>

<h3>Domain Filter (v4.6.2)</h3>
<p>Use the domain dropdown to filter results by a specific domain. The dropdown is searchable and includes a clear button to reset the filter.</p>

<h3>Status Filter Pills (v4.6.2)</h3>
<p>Click status badges in result rows to filter all results to that status type.</p>

<h2><i data-lucide="download"></i> Export Options</h2>
<p>Export validated hyperlinks with highlighting:</p>
<ul>
    <li><strong>Export Highlighted DOCX</strong> — Broken links marked in red/yellow with strikethrough</li>
    <li><strong>Export Highlighted Excel</strong> — Broken link rows highlighted with red background</li>
    <li><strong>CSV Export</strong> — Full results table for spreadsheet analysis</li>
</ul>
<p>The "Export Highlighted" button appears after validation completes.</p>

<h2><i data-lucide="scan-search"></i> Deep Validate (v4.6.2)</h2>
<p>Some government sites (defense.gov, dcma.mil, navy.mil, etc.) use aggressive bot protection that blocks standard HTTP requests, showing as "Blocked (403)". The <strong>Deep Validate</strong> feature uses a real Chrome browser to retry these URLs.</p>

<h3>How It Works</h3>
<ol>
    <li>After validation completes, URLs with eligible statuses are identified (Blocked, Timeout, DNS Failed, Auth Required, SSL Error)</li>
    <li>Click <strong>Deep Validate</strong> (purple button) to retry with headless Chrome</li>
    <li>Chrome browser runs in the background (no visible window)</li>
    <li>Uses stealth techniques to bypass bot detection</li>
    <li>Recovered URLs merge back into results — stat tiles, domain filter, and visualizations update automatically</li>
    <li>The Deep Validate button disappears when no eligible URLs remain</li>
</ol>

<h3>Why It's Needed</h3>
<p>Many .mil and .gov sites use services like Akamai, Cloudflare, or custom bot protection that:</p>
<ul>
    <li>Block requests without proper browser fingerprints</li>
    <li>Require JavaScript execution to pass challenges</li>
    <li>Check for automation indicators (headless browser flags)</li>
</ul>
<p>Deep Validate uses a real Chrome browser with stealth scripts to appear as a legitimate user. In testing, sites like dcma.mil, faa.gov, and tenable.com successfully recovered from 403/503 errors.</p>

<h3>Requirements</h3>
<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Optional Installation</strong>
        <p>Deep Validate requires Playwright. Install with:</p>
        <pre style="background: var(--bg-secondary); padding: 8px; border-radius: 4px; margin-top: 8px;">pip install playwright
playwright install chromium</pre>
        <p style="margin-top: 8px;">If not installed, standard HTTP validation still works — only the Deep Validate feature is unavailable.</p>
    </div>
</div>

<h2><i data-lucide="history"></i> Link History & Exclusions (New in v3.0.122)</h2>
<p>Click the <strong>Links</strong> button in the top navigation to access:</p>

<h3>Exclusions Tab</h3>
<p>Create rules to skip certain URLs during validation:</p>
<ul>
    <li><strong>Match Types</strong> — Contains, Exact, Prefix, Suffix, or Regex</li>
    <li><strong>Enable/Disable</strong> — Toggle exclusions without deleting</li>
    <li><strong>Reasons</strong> — Add notes for why URLs are excluded</li>
    <li><strong>Persistence</strong> — Exclusions stored in SQLite database (survive sessions)</li>
</ul>
<p>Example exclusions: internal servers, localhost URLs, authentication-required pages, known-deprecated endpoints.</p>

<h3>Scans Tab</h3>
<p>View historical hyperlink scans with:</p>
<ul>
    <li>Document name and scan timestamp</li>
    <li>Total links, valid count, broken count</li>
    <li>Expand any scan to see full details</li>
    <li>Delete old scan records</li>
</ul>

<h2><i data-lucide="mouse-pointer"></i> Clickable Hyperlinks (v3.0.121)</h2>
<p>In the validation results panel, click any hyperlink row to open the URL in a new browser tab for manual verification. Hover shows an external-link icon.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Air-Gapped Mode</strong>
        <p>In air-gapped environments, external URLs cannot be validated. The checker will identify them but mark as "Cannot validate (offline)".</p>
    </div>
</div>
`
};

// ============================================================================
// HYPERLINK HEALTH - VALIDATION
// ============================================================================
HelpDocs.content['hyperlink-validation'] = {
    title: 'URL Validation',
    subtitle: 'How hyperlink validation works',
    html: `
<h2><i data-lucide="cog"></i> Validation Process</h2>
<ol>
    <li><strong>Extract</strong> — Find all URLs in document text, HYPERLINK fields, and Excel cells</li>
    <li><strong>Deduplicate</strong> — Combine identical URLs</li>
    <li><strong>Apply Exclusions</strong> — Skip URLs matching your exclusion rules</li>
    <li><strong>Validate</strong> — Send HTTP requests to each unique URL (Validator mode only)</li>
    <li><strong>Report</strong> — Collect status codes, response times, and error details</li>
</ol>

<h2><i data-lucide="settings"></i> Validation Settings</h2>
<p>Configure in Settings → Hyperlink Validation:</p>
<ul>
    <li><strong>Mode</strong> — Offline (format only) or Validator (full HTTP with Windows auth)</li>
    <li><strong>Timeout</strong> — Max wait time per URL (default: 10 seconds, extended for slow government servers)</li>
    <li><strong>Retries</strong> — Number of retry attempts for failed requests (default: 3)</li>
    <li><strong>Follow redirects</strong> — Whether to follow redirect chains (default: yes, up to 5 hops)</li>
    <li><strong>Verify SSL</strong> — Check certificate validity (always enabled in Validator mode)</li>
</ul>

<h2><i data-lucide="shield"></i> Government & Enterprise Site Handling</h2>
<p>Validator mode is specifically optimized for challenging government and enterprise sites:</p>
<ul>
    <li><strong>Windows Authentication</strong> — Automatic NTLM/Negotiate SSO using your Windows credentials</li>
    <li><strong>Extended Timeouts</strong> — Longer connect and read timeouts for slow government servers</li>
    <li><strong>Realistic Browser Headers</strong> — User-Agent and Accept headers that mimic a real browser to avoid bot blocking</li>
    <li><strong>HEAD/GET Fallback</strong> — If HEAD request fails (common on government sites), automatically retries with GET</li>
    <li><strong>HTTP 405 Handling</strong> — "Method Not Allowed" treated as success (page exists but doesn't allow HEAD)</li>
    <li><strong>Authentication Challenges</strong> — 401 responses reported as "Auth Required" rather than broken</li>
    <li><strong>Exponential Backoff</strong> — Intelligent retry timing to avoid rate limiting</li>
</ul>

<h2><i data-lucide="shield-check"></i> Rate Limiting & Politeness</h2>
<p>To avoid overwhelming servers:</p>
<ul>
    <li>Requests are processed sequentially (one at a time)</li>
    <li>Exponential backoff between retries (2s, 4s, 8s)</li>
    <li>429 Rate Limit responses are reported but not retried aggressively</li>
</ul>
`
};

// ============================================================================
// HYPERLINK HEALTH - STATUS CODES
// ============================================================================
HelpDocs.content['hyperlink-status'] = {
    title: 'Status Codes',
    subtitle: 'Understanding HTTP response codes',
    html: `
<h2><i data-lucide="check-circle"></i> Success Codes (2xx)</h2>
<table class="help-table">
    <thead><tr><th>Code</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td>200</td><td>OK - Resource exists and is accessible</td></tr>
        <tr><td>201</td><td>Created - Resource was created</td></tr>
        <tr><td>204</td><td>No Content - Success but no body</td></tr>
    </tbody>
</table>

<h2><i data-lucide="arrow-right"></i> Redirect Codes (3xx)</h2>
<table class="help-table">
    <thead><tr><th>Code</th><th>Meaning</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td>301</td><td>Moved Permanently</td><td>Update the URL</td></tr>
        <tr><td>302</td><td>Found (Temporary)</td><td>Usually OK to keep</td></tr>
        <tr><td>307</td><td>Temporary Redirect</td><td>Usually OK to keep</td></tr>
        <tr><td>308</td><td>Permanent Redirect</td><td>Update the URL</td></tr>
    </tbody>
</table>

<h2><i data-lucide="alert-circle"></i> Error Codes (4xx)</h2>
<table class="help-table">
    <thead><tr><th>Code</th><th>Meaning</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td>400</td><td>Bad Request</td><td>Check URL format</td></tr>
        <tr><td>401</td><td>Unauthorized</td><td>Requires login</td></tr>
        <tr><td>403</td><td>Forbidden</td><td>Access denied</td></tr>
        <tr><td>404</td><td>Not Found</td><td>Remove or fix URL</td></tr>
        <tr><td>410</td><td>Gone</td><td>Permanently removed</td></tr>
    </tbody>
</table>

<h2><i data-lucide="server"></i> Server Error Codes (5xx)</h2>
<table class="help-table">
    <thead><tr><th>Code</th><th>Meaning</th><th>Action</th></tr></thead>
    <tbody>
        <tr><td>500</td><td>Internal Server Error</td><td>Retry later</td></tr>
        <tr><td>502</td><td>Bad Gateway</td><td>Retry later</td></tr>
        <tr><td>503</td><td>Service Unavailable</td><td>Retry later</td></tr>
        <tr><td>504</td><td>Gateway Timeout</td><td>Retry later</td></tr>
    </tbody>
</table>
`
};

// ============================================================================
// BATCH PROCESSING - OVERVIEW
// ============================================================================
HelpDocs.content['batch-overview'] = {
    title: 'Batch Processing',
    subtitle: 'Process multiple documents at once',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="layers" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Batch Processing lets you queue multiple documents for analysis, track progress, and view consolidated results across your entire document library.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Batch Limits (v3.0.116)</strong>
        <p>Maximum <strong>10 files</strong> per batch, with a combined total size limit of <strong>100MB</strong>. Files are streamed to disk in 8KB chunks to minimize memory usage.</p>
    </div>
</div>

<h2><i data-lucide="plus-circle"></i> Adding Documents</h2>
<ol>
    <li>Click <strong>Batch</strong> in the toolbar</li>
    <li>Drag and drop multiple files, or click to browse</li>
    <li>Select your review preset and options</li>
    <li>Click <strong>Start Batch</strong></li>
</ol>

<h2><i data-lucide="list"></i> Queue Management</h2>
<ul>
    <li><strong>Reorder</strong> — Drag documents to change processing order</li>
    <li><strong>Remove</strong> — Remove documents before processing</li>
    <li><strong>Pause/Resume</strong> — Pause the queue at any time</li>
    <li><strong>Cancel</strong> — Stop processing and clear the queue</li>
</ul>

<h2><i data-lucide="bar-chart-2"></i> Results View</h2>
<p>After processing, view:</p>
<ul>
    <li>Summary statistics across all documents</li>
    <li>Per-document issue counts</li>
    <li>Click any document to see its detailed results</li>
    <li>Export all results to Excel or CSV</li>
</ul>

<h2><i data-lucide="settings"></i> Batch Options</h2>
<ul>
    <li><strong>Auto-export</strong> — Automatically export each document after processing</li>
    <li><strong>Skip errors</strong> — Continue processing if a document fails</li>
    <li><strong>Role extraction</strong> — Enable role extraction for all documents</li>
    <li><strong>Parallel processing</strong> — Process multiple documents simultaneously</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip: Cross-Document Analysis</strong>
        <p>After batch processing, open Roles Studio to see aggregated role data across all processed documents.</p>
    </div>
</div>
`
};

// ============================================================================
// BATCH PROCESSING - QUEUE
// ============================================================================
HelpDocs.content['batch-queue'] = {
    title: 'Queue Management',
    subtitle: 'Managing your batch processing queue',
    html: `
<h2><i data-lucide="list"></i> Queue States</h2>
<table class="help-table">
    <thead><tr><th>State</th><th>Icon</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td>Pending</td><td>○</td><td>Waiting to be processed</td></tr>
        <tr><td>Processing</td><td>◐</td><td>Currently being analyzed</td></tr>
        <tr><td>Complete</td><td style="color: #22c55e;">✓</td><td>Successfully processed</td></tr>
        <tr><td>Error</td><td style="color: #ef4444;">✗</td><td>Processing failed</td></tr>
        <tr><td>Skipped</td><td>○</td><td>Manually skipped</td></tr>
    </tbody>
</table>

<h2><i data-lucide="settings"></i> Queue Controls</h2>
<ul>
    <li><strong>Start/Pause</strong> — Begin or pause processing</li>
    <li><strong>Clear Completed</strong> — Remove finished items from view</li>
    <li><strong>Retry Failed</strong> — Reprocess documents that errored</li>
    <li><strong>Clear All</strong> — Remove all items from queue</li>
</ul>

<h2><i data-lucide="zap"></i> Performance</h2>
<p>Processing time depends on:</p>
<ul>
    <li>Document size and complexity</li>
    <li>Number of enabled checkers</li>
    <li>Whether role extraction is enabled</li>
    <li>System resources available</li>
</ul>
`
};

// ============================================================================
// BATCH PROCESSING - RESULTS
// ============================================================================
HelpDocs.content['batch-results'] = {
    title: 'Consolidated Results',
    subtitle: 'Viewing results across multiple documents',
    html: `
<h2><i data-lucide="bar-chart-2"></i> Summary Statistics</h2>
<p>The batch results view shows:</p>
<ul>
    <li>Total documents processed</li>
    <li>Total issues found across all documents</li>
    <li>Breakdown by severity (Critical/High/Medium/Low)</li>
    <li>Breakdown by category</li>
    <li>Processing time statistics</li>
</ul>

<h2><i data-lucide="table"></i> Per-Document View</h2>
<p>Click any document to see:</p>
<ul>
    <li>Issue count and quality score</li>
    <li>Severity distribution</li>
    <li>Category breakdown</li>
    <li>Full issue list</li>
</ul>

<h2><i data-lucide="download"></i> Export Options</h2>
<ul>
    <li><strong>Excel Workbook</strong> — One sheet per document plus summary</li>
    <li><strong>CSV Archive</strong> — ZIP file with one CSV per document</li>
    <li><strong>JSON</strong> — Complete data for API integration</li>
</ul>

<h2><i data-lucide="users"></i> Cross-Document Analysis</h2>
<p>After batch processing:</p>
<ul>
    <li>Open <strong>Roles Studio</strong> to see aggregated roles</li>
    <li>Use the Document Filter to compare specific documents</li>
    <li>View the Role-Document Matrix for cross-reference</li>
</ul>
`
};

// ============================================================================
// SETTINGS - GENERAL
// ============================================================================
HelpDocs.content['settings-general'] = {
    title: 'General Settings',
    subtitle: 'Configure behavior and defaults',
    html: `
<p>Access via gear icon in footer or <kbd>Ctrl</kbd>+<kbd>,</kbd>.</p>

<h2><i data-lucide="sliders"></i> Document Analysis</h2>
<ul>
    <li><strong>Default Preset</strong> — Which preset loads on start</li>
    <li><strong>Sentence Length Threshold</strong> — Max words (default: 40)</li>
    <li><strong>Passive Voice Threshold</strong> — Percentage (default: 10%)</li>
</ul>

<h2><i data-lucide="list"></i> Issue Display</h2>
<ul>
    <li><strong>Default Sort</strong> — Severity, Category, or Location</li>
    <li><strong>Auto-collapse families</strong> — Show one per family</li>
    <li><strong>Minimum family size</strong> — Grouping threshold (default: 3)</li>
</ul>

<h2><i data-lucide="save"></i> Data</h2>
<ul>
    <li><strong>Remember Decisions</strong> — Persist Keep/Suppress/Fix across sessions</li>
    <li><strong>Clear All Data</strong> — Reset to defaults</li>
</ul>
`
};

// ============================================================================
// SETTINGS - APPEARANCE
// ============================================================================
HelpDocs.content['settings-appearance'] = {
    title: 'Appearance',
    subtitle: 'Customize look and feel',
    html: `
<h2><i data-lucide="sun"></i> Theme</h2>
<ul>
    <li><strong>Light Mode</strong> — White background, dark text</li>
    <li><strong>Dark Mode</strong> — Dark background, light text</li>
    <li><strong>System</strong> — Match OS preference</li>
</ul>

<h2><i data-lucide="type"></i> Typography</h2>
<ul>
    <li><strong>Font Size</strong> — Small (13px), Medium (14px), Large (16px)</li>
    <li><strong>Font Family</strong> — System Default, Inter, Source Sans</li>
</ul>

<h2><i data-lucide="layout"></i> Layout</h2>
<ul>
    <li><strong>Sidebar position</strong> — Left (default) or Right</li>
    <li><strong>Compact mode</strong> — Reduce spacing for more content</li>
</ul>
`
};

// ============================================================================
// SETTINGS - SHARING (NEW in v4.0.3)
// ============================================================================
HelpDocs.content['settings-sharing'] = {
    title: 'Sharing Settings',
    subtitle: 'Configure role sharing and import packages from team members',
    html: `
<p>The Sharing tab in Settings manages how you share role dictionaries with team members and import packages you receive.</p>

<h2><i data-lucide="folder-sync"></i> Shared Folder Path</h2>
<p>Configure the path to a shared network folder where master dictionary files are stored:</p>
<ul>
    <li>Enter a UNC path (e.g., <code>\\\\server\\share\\aegis</code>) or local path</li>
    <li>When you click <strong>Share → Export to Shared Folder</strong> in the Adjudication tab, the master file is written here</li>
    <li>When other AEGIS instances sync from this path, they pick up your exported roles</li>
</ul>

<h2><i data-lucide="upload"></i> Import Roles Package</h2>
<p>Import a <code>.aegis-roles</code> package received from a team member:</p>
<ol>
    <li>Click <strong>"Import Package"</strong> in the Sharing tab</li>
    <li>Select the <code>.aegis-roles</code> or <code>.json</code> file from your computer</li>
    <li>AEGIS validates the package format and version</li>
    <li>New roles are added to your dictionary; existing roles are skipped</li>
    <li>New function categories are created; existing ones are unchanged</li>
    <li>A success message shows counts of imported vs. skipped items</li>
</ol>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Alternative: Updates Folder</strong>
        <p>You can also drop <code>.aegis-roles</code> files directly into the <code>updates/</code> folder. The next time you check for updates (Settings → Updates → Check for Updates), AEGIS will auto-detect and import the roles package.</p>
    </div>
</div>

<div class="help-callout help-callout-info">
    <i data-lucide="shield"></i>
    <div>
        <strong>Safe Import</strong>
        <p>Imports only <em>add</em> new roles — they never overwrite or delete your existing dictionary entries. Your local adjudication decisions are always preserved.</p>
    </div>
</div>
`
};

// ============================================================================
// SETTINGS - UPDATES
// ============================================================================
HelpDocs.content['settings-updates'] = {
    title: 'Updates',
    subtitle: 'Apply patches without full reinstall',
    html: `
<h2><i data-lucide="refresh-cw"></i> Built-in Update System</h2>
<p>AEGIS includes a built-in update system for applying patches and fixes without reinstalling the entire application.</p>

<h2><i data-lucide="download"></i> Applying Updates</h2>
<ol>
    <li>Place update files in the <code>updates/</code> folder (inside the AEGIS directory)</li>
    <li>Open <strong>Settings</strong> → <strong>Updates</strong> tab</li>
    <li>Click <strong>"Check for Updates"</strong> to scan for pending files</li>
    <li>Review the list of files that will be updated</li>
    <li>Click <strong>"Apply Updates"</strong> to install them</li>
    <li>Wait for automatic restart and browser refresh</li>
</ol>

<h2><i data-lucide="folder"></i> Update File Formats</h2>
<p>The update system supports three methods:</p>

<h3>1. Directory Structure (Recommended)</h3>
<p>Mirror the app's folder structure inside updates/:</p>
<pre>updates/
├── static/js/features/roles.js
├── templates/index.html
└── role_extractor_v3.py</pre>

<h3>2. Flat Files with Prefixes</h3>
<p>Use naming prefixes to specify destinations:</p>
<table class="help-table">
    <tr><td><code>static_js_features_</code></td><td>→ static/js/features/</td></tr>
    <tr><td><code>static_js_ui_</code></td><td>→ static/js/ui/</td></tr>
    <tr><td><code>static_css_</code></td><td>→ static/css/</td></tr>
    <tr><td><code>templates_</code></td><td>→ templates/</td></tr>
    <tr><td><code>statement_forge_</code></td><td>→ statement_forge/</td></tr>
</table>

<h3>3. Roles Package (.aegis-roles)</h3>
<p>Drop a <code>.aegis-roles</code> file in the updates/ folder to auto-import role dictionaries from team members. These are detected and imported on the next update check — no manual intervention needed. See <a href="#" onclick="HelpContent.navigateTo('role-sharing');return false;">Sharing Roles</a> for details.</p>

<h2><i data-lucide="shield"></i> How It Works</h2>
<ul>
    <li>Update files are automatically routed to their correct locations</li>
    <li>Backups are created before applying any changes</li>
    <li>The server restarts automatically after successful updates</li>
    <li>Your browser refreshes when the server is ready</li>
</ul>

<h2><i data-lucide="undo-2"></i> Rollback</h2>
<p>If an update causes issues:</p>
<ol>
    <li>Go to <strong>Settings</strong> → <strong>Updates</strong> → <strong>Backups</strong></li>
    <li>Select the backup created before the problematic update</li>
    <li>Click <strong>"Rollback"</strong> to restore the previous version</li>
</ol>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Air-Gapped Friendly</strong>
        <p>Updates are applied from local files — no internet connection required. See <code>updates/UPDATE_README.md</code> for detailed documentation.</p>
    </div>
</div>
`
};

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================
HelpDocs.content['shortcuts'] = {
    title: 'Keyboard Shortcuts',
    subtitle: 'Work faster with keyboard commands',
    html: `
<h2><i data-lucide="file"></i> Document Operations</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>Ctrl</kbd>+<kbd>O</kbd></td><td>Open document</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>R</kbd></td><td>Run review</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>E</kbd></td><td>Export results</td></tr>
    </tbody>
</table>

<h2><i data-lucide="layout"></i> Interface</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>Ctrl</kbd>+<kbd>B</kbd></td><td>Toggle sidebar</td></tr>
        <tr><td><kbd>F1</kbd></td><td>Open help</td></tr>
        <tr><td><kbd>?</kbd></td><td>Show shortcuts</td></tr>
        <tr><td><kbd>Esc</kbd></td><td>Close modal/exit mode</td></tr>
    </tbody>
</table>

<h2><i data-lucide="check-square"></i> Triage Mode</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>T</kbd></td><td>Enter triage mode</td></tr>
        <tr><td><kbd>K</kbd> or <kbd>→</kbd></td><td>Keep issue</td></tr>
        <tr><td><kbd>S</kbd></td><td>Suppress issue</td></tr>
        <tr><td><kbd>F</kbd></td><td>Mark as fixed</td></tr>
        <tr><td><kbd>Space</kbd></td><td>Skip to next</td></tr>
        <tr><td><kbd>←</kbd></td><td>Previous issue</td></tr>
        <tr><td><kbd>Shift</kbd>+action</td><td>Apply to family</td></tr>
    </tbody>
</table>

<h2><i data-lucide="list"></i> Issue List</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Navigate issues</td></tr>
        <tr><td><kbd>Enter</kbd></td><td>View issue details</td></tr>
        <tr><td><kbd>/</kbd></td><td>Focus search</td></tr>
    </tbody>
</table>

<h2><i data-lucide="wand-2"></i> Fix Assistant</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>A</kbd></td><td>Accept current fix</td></tr>
        <tr><td><kbd>R</kbd></td><td>Reject current fix</td></tr>
        <tr><td><kbd>S</kbd></td><td>Skip current fix</td></tr>
        <tr><td><kbd>U</kbd> or <kbd>Ctrl</kbd>+<kbd>Z</kbd></td><td>Undo last action</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd></td><td>Redo</td></tr>
        <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Navigate fixes</td></tr>
        <tr><td><kbd>Ctrl</kbd>+<kbd>F</kbd></td><td>Search fixes</td></tr>
    </tbody>
</table>

<h2><i data-lucide="users"></i> Roles Studio</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd></td><td>Open Roles Studio</td></tr>
        <tr><td><kbd>1</kbd>-<kbd>7</kbd></td><td>Switch tabs (Overview, Graph, Details, RACI, Matrix, Adjudication, Dictionary)</td></tr>
    </tbody>
</table>

<h2><i data-lucide="file-text"></i> Role Source Viewer</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>←</kbd></td><td>Previous mention</td></tr>
        <tr><td><kbd>→</kbd></td><td>Next mention</td></tr>
        <tr><td><kbd>Esc</kbd></td><td>Close viewer</td></tr>
        <tr><td>Click highlight</td><td>Jump to mention</td></tr>
    </tbody>
</table>

<h2><i data-lucide="search"></i> SmartSearch</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>↓</kbd></td><td>Move to next result</td></tr>
        <tr><td><kbd>↑</kbd></td><td>Move to previous result</td></tr>
        <tr><td><kbd>Enter</kbd></td><td>Select highlighted result</td></tr>
        <tr><td><kbd>Esc</kbd></td><td>Close dropdown</td></tr>
    </tbody>
</table>

<h2><i data-lucide="bar-chart-3"></i> Data Explorer</h2>
<table class="help-table">
    <tbody>
        <tr><td>Click chart segment</td><td>Drill into category/role</td></tr>
        <tr><td>Click back button</td><td>Return to previous view</td></tr>
        <tr><td>Hover chart</td><td>Show tooltip with details</td></tr>
    </tbody>
</table>

<h2><i data-lucide="hammer"></i> Statement Forge</h2>
<table class="help-table">
    <tbody>
        <tr><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>S</kbd></td><td>Open Statement Forge</td></tr>
        <tr><td><kbd>↑</kbd> / <kbd>↓</kbd></td><td>Navigate statements</td></tr>
        <tr><td><kbd>E</kbd></td><td>Edit selected statement</td></tr>
        <tr><td><kbd>D</kbd></td><td>Delete selected statement</td></tr>
    </tbody>
</table>
`
};

// ============================================================================
// TECHNICAL DEEP DIVE - ARCHITECTURE
// ============================================================================
HelpDocs.content['tech-architecture'] = {
    title: 'Architecture Overview',
    subtitle: 'Understanding how AEGIS is built',
    html: `
<div class="help-callout help-callout-info">
    <i data-lucide="cpu"></i>
    <div>
        <strong>Technical Section</strong>
        <p>This section is for developers, system administrators, and power users who want to understand AEGIS's internals.</p>
    </div>
</div>

<h2><i data-lucide="layers"></i> System Architecture</h2>
<p>AEGIS uses a classic client-server architecture designed for air-gapped Windows environments.</p>

<pre class="help-code">
┌─────────────────────────────────────────────────────────┐
│                      Browser (Client)                    │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │   app.js    │  │  features/ │  │  vendor/        │  │
│  │  (9,300 LOC)│  │  roles.js  │  │  d3.v7.min.js   │  │
│  │             │  │  families  │  │  chart.min.js   │  │
│  │             │  │  triage    │  │  lucide.min.js  │  │
│  └─────────────┘  └────────────┘  └─────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP/JSON
┌───────────────────────────▼─────────────────────────────┐
│                    Flask Server (Python)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  app.py (3,500 LOC) - Routes & API Endpoints     │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   core.py    │  │ statement_   │  │  update_     │   │
│  │  Document    │  │   forge/     │  │  manager.py  │   │
│  │  Extraction  │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Checker Modules (50+ files)             │   │
│  │  acronym_checker.py, grammar_checker.py, etc.    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
</pre>

<h2><i data-lucide="folder"></i> Directory Structure</h2>
<pre class="help-code">
AEGIS/            # Main application folder
├── app.py                   # Main Flask application (4,300+ LOC)
├── core.py                  # Document extraction engine
├── role_extractor_v3.py     # AI role extraction (94.7% precision)
├── *_checker.py             # 50+ quality checker modules
├── statement_forge/         # Statement extraction module
│   ├── routes.py            # API endpoints
│   ├── extractor.py         # Extraction logic
│   └── export.py            # Export formats
├── static/                  # Frontend assets
│   ├── js/                  # JavaScript modules
│   │   ├── app.js           # Main application
│   │   ├── features/        # Feature modules (roles, triage, families)
│   │   ├── ui/              # UI components (modals, state, events)
│   │   ├── api/             # API client
│   │   └── vendor/          # Third-party (D3, Chart.js, Lucide)
│   └── css/                 # Stylesheets
├── templates/               # HTML templates
│   └── index.html           # Single-page application
├── updates/                 # Drop update files here
│   └── UPDATE_README.md     # Update instructions
├── backups/                 # Auto-created before updates
├── logs/                    # Application logs
├── data/                    # Data files
├── tools/                   # Utility scripts
├── docs/                    # Documentation
├── version.json             # Version info (single source of truth)
├── config.json              # User configuration
├── requirements.txt         # Python dependencies
├── setup.bat                # Basic setup
├── setup_docling.bat        # Docling AI installation
└── setup_enhancements.bat   # NLP enhancements installation
</pre>

<h2><i data-lucide="cog"></i> Key Technologies</h2>
<table class="help-table">
    <thead><tr><th>Component</th><th>Technology</th><th>Purpose</th></tr></thead>
    <tbody>
        <tr><td>Backend</td><td>Python 3.8+ / Flask</td><td>API server, document processing</td></tr>
        <tr><td>Frontend</td><td>Vanilla JavaScript</td><td>UI, no framework dependencies</td></tr>
        <tr><td>Visualization</td><td>D3.js, Chart.js</td><td>Graphs and charts</td></tr>
        <tr><td>Icons</td><td>Lucide</td><td>UI icons</td></tr>
        <tr><td>WSGI Server</td><td>Waitress</td><td>Production-ready, Windows-native</td></tr>
        <tr><td>Document Parsing</td><td>python-docx, pdfplumber</td><td>Extract text from files</td></tr>
    </tbody>
</table>

<h2><i data-lucide="shield"></i> Air-Gapped Design</h2>
<ul>
    <li><strong>No external API calls</strong> — All processing is local</li>
    <li><strong>Bundled dependencies</strong> — Vendor JS files included</li>
    <li><strong>Offline NLP</strong> — No cloud language services</li>
    <li><strong>Local update system</strong> — Apply patches from local files</li>
</ul>
`
};

// ============================================================================
// TECHNICAL - CHECKER ENGINE
// ============================================================================
HelpDocs.content['tech-checkers'] = {
    title: 'Checker Engine',
    subtitle: 'How quality checks are implemented',
    html: `
<h2><i data-lucide="cog"></i> Checker Architecture</h2>
<p>Each checker is a Python class inheriting from <code>BaseChecker</code>:</p>

<pre class="help-code">
class AcronymChecker(BaseChecker):
    name = "Acronym Checker"
    category = "Acronyms"
    
    def check(self, document):
        issues = []
        for para_idx, paragraph in enumerate(document.paragraphs):
            # Detection logic
            acronyms = self.find_acronyms(paragraph.text)
            for acronym in acronyms:
                if not self.is_defined(acronym, document):
                    issues.append(Issue(
                        severity="high",
                        message=f"Undefined acronym: {acronym}",
                        flagged=acronym,
                        paragraph=para_idx,
                        suggestion="Define on first use"
                    ))
        return issues
</pre>

<h2><i data-lucide="list"></i> Checker Registry</h2>
<p>Checkers register themselves in <code>app.py</code>:</p>

<pre class="help-code">
CHECKERS = {
    'acronyms': AcronymChecker(),
    'grammar': GrammarChecker(),
    'spelling': SpellChecker(),
    'passive_voice': PassiveVoiceChecker(),
    'requirements': RequirementsChecker(),
    # ... 45+ more checkers
}
</pre>

<h2><i data-lucide="play"></i> Execution Flow</h2>
<ol>
    <li><strong>Document Load</strong> — <code>core.py</code> extracts text and structure</li>
    <li><strong>Checker Selection</strong> — UI sends enabled checker IDs</li>
    <li><strong>Parallel Execution</strong> — Checkers run concurrently</li>
    <li><strong>Issue Aggregation</strong> — Results merged and sorted</li>
    <li><strong>Response</strong> — JSON sent to frontend</li>
</ol>

<h2><i data-lucide="plus"></i> Adding New Checkers</h2>
<ol>
    <li>Create <code>my_checker.py</code> extending <code>BaseChecker</code></li>
    <li>Implement <code>check(document)</code> method</li>
    <li>Register in <code>CHECKERS</code> dictionary</li>
    <li>Add UI checkbox in <code>index.html</code></li>
    <li>Add tests in <code>tests.py</code></li>
</ol>
`
};

// ============================================================================
// TECHNICAL - DOCUMENT EXTRACTION
// ============================================================================
HelpDocs.content['tech-extraction'] = {
    title: 'Document Extraction',
    subtitle: 'How documents are parsed and processed',
    html: `
<h2><i data-lucide="layers"></i> Multi-Library Extraction (v4.3.0)</h2>

<div class="help-highlight">
AEGIS uses <strong>multiple extraction libraries</strong> for maximum accuracy.
It automatically selects the best method based on what's available and the document type, with mammoth and pymupdf4llm providing clean HTML output for the document viewer.
</div>

<h3>Extraction Priority Chain</h3>
<pre class="help-code">
Document Upload
      │
      ▼
┌─────────────────┐
│ Format Detection│ ← .docx, .pdf, .pptx, .xlsx, .html
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│               Extraction Chain (v4.3.0)          │
│                                                  │
│  Priority 1: Docling (AI)                        │
│  ┌─────────────┐                                 │
│  │ DoclingAdapter│ → AI table/layout recognition │
│  └──────┬──────┘                                 │
│         │ fallback                               │
│         ▼                                        │
│  Priority 2: mammoth (DOCX) / pymupdf4llm (PDF) │
│  ┌───────────┐  ┌──────────────┐                 │
│  │  mammoth  │  │ pymupdf4llm  │                 │
│  │ DOCX→HTML │  │  PDF→Markdown│                 │
│  └───────────┘  └──────────────┘                 │
│         │ fallback                               │
│         ▼                                        │
│  Priority 3: Legacy extractors                   │
│  ┌──────────────┐  ┌─────────────┐               │
│  │ python-docx  │  │ pdfplumber  │               │
│  │ DocumentExtr.│  │ PDFExtractV2│               │
│  └──────────────┘  └─────────────┘               │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │ html_preview     │ ← Generated for all paths
           │ (mammoth/pymu4l) │   via post-extraction step
           └────────┬─────────┘
                    ▼
           ┌─────────────────┐
           │ NLP Enhancement │ ← spaCy, sklearn
           │ (role detection)│
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │ Unified Result  │
           └─────────────────┘
</pre>

<h2><i data-lucide="cpu"></i> Extraction Libraries</h2>

<table class="help-table">
<thead>
    <tr><th>Library</th><th>Use Case</th><th>Output</th></tr>
</thead>
<tbody>
    <tr>
        <td><strong>Docling (AI)</strong></td>
        <td>Best overall - AI-powered table/layout recognition</td>
        <td>Structured text</td>
    </tr>
    <tr>
        <td><strong>mammoth</strong> <span class="help-badge help-badge-new">v4.3.0</span></td>
        <td>DOCX → clean semantic HTML with tables, headings, bold/italic. No table artifacts.</td>
        <td>HTML + clean text</td>
    </tr>
    <tr>
        <td><strong>pymupdf4llm</strong> <span class="help-badge help-badge-new">v4.3.0</span></td>
        <td>PDF → structured Markdown with headings, tables, and formatting</td>
        <td>Markdown → HTML</td>
    </tr>
    <tr>
        <td><strong>pdfplumber</strong></td>
        <td>General PDF text and basic tables (legacy fallback)</td>
        <td>Plain text</td>
    </tr>
    <tr>
        <td><strong>PyMuPDF</strong></td>
        <td>Font-aware text extraction, heading detection</td>
        <td>Plain text</td>
    </tr>
    <tr>
        <td><strong>Tesseract OCR</strong></td>
        <td>Scanned documents, image-based PDFs</td>
        <td>Plain text</td>
    </tr>
</tbody>
</table>

<div class="help-callout help-callout-info">
    <i data-lucide="file-code"></i>
    <div>
        <strong>HTML Preview (v4.3.0)</strong>
        <p>mammoth and pymupdf4llm generate an <code>html_preview</code> stored with each scan. This powers the rich document viewer in Statement History — rendering tables, headings, and formatting faithfully. Even when Docling is the primary extractor, mammoth runs as a post-extraction step to generate the HTML preview.</p>
    </div>
</div>

<h2><i data-lucide="brain"></i> NLP Enhancement</h2>

<p>Role and entity extraction is enhanced using multiple NLP libraries:</p>

<table class="help-table">
<thead>
    <tr><th>Library</th><th>Feature</th><th>Impact</th></tr>
</thead>
<tbody>
    <tr>
        <td><strong>spaCy</strong></td>
        <td>Named Entity Recognition, POS tagging</td>
        <td>+10% role detection accuracy</td>
    </tr>
    <tr>
        <td><strong>scikit-learn</strong></td>
        <td>Text similarity, role clustering</td>
        <td>Better deduplication</td>
    </tr>
    <tr>
        <td><strong>RACI Detection</strong></td>
        <td>Pattern matching for RACI/RASCI matrices</td>
        <td>+20% confidence boost</td>
    </tr>
</tbody>
</table>

<h2><i data-lucide="sparkles"></i> Docling AI (Optional)</h2>

<div class="help-highlight">
For maximum accuracy (+7% on all metrics), install Docling:
<code>setup_docling.bat</code>
</div>

<p>Docling provides:</p>
<ul>
    <li><strong>AI-powered table recognition</strong> — TableFormer model for complex tables</li>
    <li><strong>Layout analysis</strong> — Understands columns, reading order</li>
    <li><strong>Section detection</strong> — Identifies headings without style dependencies</li>
    <li><strong>Multi-format support</strong> — PDF, DOCX, PPTX, XLSX, HTML</li>
</ul>

<h2><i data-lucide="shield"></i> Air-Gap Configuration</h2>

<p>All extraction libraries are configured for <strong>complete offline operation</strong>:</p>

<ul>
    <li><i data-lucide="wifi-off"></i> <strong>No internet required</strong> — All AI models stored locally</li>
    <li><i data-lucide="lock"></i> <strong>No data leaves your machine</strong> — Document processing is 100% local</li>
    <li><i data-lucide="database"></i> <strong>No telemetry</strong> — Analytics and tracking disabled</li>
</ul>

<h3>Environment Variables (Set Automatically)</h3>
<pre class="help-code">
# Model location
DOCLING_ARTIFACTS_PATH=C:\\TWR\\app\\AEGIS\\docling_models

# Force offline mode - blocks ALL network access
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1

# Disable telemetry
HF_HUB_DISABLE_TELEMETRY=1
DO_NOT_TRACK=1
</pre>

<h2><i data-lucide="zap"></i> Memory Optimization</h2>

<p>Docling is configured to minimize memory usage:</p>

<ul>
    <li><strong>Image processing disabled</strong> — No picture classification or description</li>
    <li><strong>CPU-only PyTorch</strong> — No GPU memory overhead</li>
    <li><strong>Efficient table mode</strong> — "accurate" mode for quality, "fast" for speed</li>
</ul>

<pre class="help-code">
# Memory-optimized configuration (set automatically)
do_picture_classifier = False    # Skip image classification
do_picture_description = False   # Skip image descriptions
generate_page_images = False     # Don't generate page images
generate_picture_images = False  # Don't extract pictures
</pre>

<h2><i data-lucide="code"></i> Using Docling in Code</h2>

<pre class="help-code">
from docling_extractor import DoclingExtractor

# Create extractor (uses env vars for offline config)
extractor = DoclingExtractor(
    table_mode='accurate',     # 'accurate' or 'fast'
    enable_ocr=False,          # Enable only if needed
    fallback_to_legacy=True    # Use pdfplumber if Docling fails
)

# Check status
print(f"Backend: {extractor.backend_name}")  # 'docling' or 'legacy'
print(f"Available: {extractor.is_available}")

# Extract document
result = extractor.extract("document.pdf")

# Access extracted data
print(f"Pages: {result.page_count}")
print(f"Words: {result.word_count}")
print(f"Tables: {len(result.tables)}")

# Get text for role extraction
for para in result.paragraphs:
    print(f"{para.location}: {para.text[:50]}...")

# Get table data
for table in result.tables:
    print(f"Table {table.table_id}: {table.row_count} rows")
    print(f"Headers: {table.headers}")
</pre>

<h2><i data-lucide="file-text"></i> Legacy Fallback</h2>

<p>When Docling is not available, AEGIS falls through the extraction priority chain:</p>

<table class="help-table">
<thead>
    <tr><th>Format</th><th>Priority 2 (v4.3.0)</th><th>Priority 3 (Legacy)</th><th>HTML Preview</th></tr>
</thead>
<tbody>
    <tr>
        <td>DOCX</td>
        <td>mammoth</td>
        <td>python-docx (DocumentExtractor)</td>
        <td>Yes — mammoth HTML</td>
    </tr>
    <tr>
        <td>PDF</td>
        <td>pymupdf4llm</td>
        <td>pdfplumber (PDFExtractorV2)</td>
        <td>Yes — Markdown→HTML</td>
    </tr>
    <tr>
        <td>PPTX</td>
        <td>—</td>
        <td>python-pptx</td>
        <td>No</td>
    </tr>
    <tr>
        <td>XLSX</td>
        <td>—</td>
        <td>openpyxl</td>
        <td>No</td>
    </tr>
</tbody>
</table>

<h2><i data-lucide="download"></i> Installation</h2>

<h3>Option 1: Online Installation</h3>
<pre class="help-code">
# Run from AEGIS folder
setup_docling.bat
</pre>

<h3>Option 2: Air-Gapped Installation</h3>
<pre class="help-code">
# On internet-connected machine:
powershell -ExecutionPolicy Bypass -File bundle_for_airgap.ps1

# Transfer bundle to air-gapped machine, then:
INSTALL_AIRGAP.bat
</pre>

<h3>Disk Space Required</h3>
<ul>
    <li>PyTorch (CPU): ~800 MB</li>
    <li>Docling packages: ~700 MB</li>
    <li>AI models: ~1.2 GB</li>
    <li><strong>Total: ~2.7 GB</strong></li>
</ul>

<h2><i data-lucide="check-circle"></i> Verifying Installation</h2>

<pre class="help-code">
# Check installation status
python -c "from docling_extractor import check_docling_status; import json; print(json.dumps(check_docling_status(), indent=2))"

# Expected output for properly configured system:
{
  "installed": true,
  "version": "2.70.0",
  "pytorch_available": true,
  "models_downloaded": true,
  "offline_ready": true
}
</pre>

<h2><i data-lucide="alert-triangle"></i> Troubleshooting</h2>

<h3>Docling not detected</h3>
<ul>
    <li>Run <code>setup_docling.bat</code> to install</li>
    <li>Check Python version is 3.10+</li>
    <li>Verify <code>pip list | findstr docling</code> shows installed</li>
</ul>

<h3>Models not found (offline mode fails)</h3>
<ul>
    <li>Verify <code>DOCLING_ARTIFACTS_PATH</code> environment variable is set</li>
    <li>Check the models folder contains <code>ds4sd--docling-models</code></li>
    <li>Re-run <code>docling-tools models download -o &lt;path&gt;</code></li>
</ul>

<h3>High memory usage</h3>
<ul>
    <li>Image processing should be disabled automatically</li>
    <li>Try <code>table_mode='fast'</code> for large documents</li>
    <li>Process documents one at a time</li>
</ul>
`
};

// ============================================================================
// TECHNICAL - DOCLING AI ENGINE
// ============================================================================
HelpDocs.content['tech-docling'] = {
    title: 'Docling AI Engine',
    subtitle: 'Advanced AI-powered document extraction (100% offline)',
    html: `
<h2><i data-lucide="sparkles"></i> What is Docling?</h2>

<p>Docling is IBM's open-source document parsing library that provides AI-powered extraction capabilities. 
AEGIS integrates Docling to deliver superior document analysis while maintaining <strong>complete air-gapped operation</strong>.</p>

<div class="help-callout help-callout-success">
<i data-lucide="shield-check"></i>
<div>
    <strong>100% Offline Operation</strong>
    <p>When properly configured, Docling operates entirely offline. No data is sent to external servers. All AI models run locally on your machine.</p>
</div>
</div>

<h2><i data-lucide="zap"></i> Key Features</h2>

<div class="help-grid">
<div class="help-feature">
    <h4><i data-lucide="table"></i> AI Table Recognition</h4>
    <p>TableFormer AI model accurately extracts complex table structures, headers, and merged cells. Superior to rule-based extraction.</p>
</div>
<div class="help-feature">
    <h4><i data-lucide="layout"></i> Layout Understanding</h4>
    <p>AI analyzes document layout to determine reading order, identify columns, and understand visual structure.</p>
</div>
<div class="help-feature">
    <h4><i data-lucide="layers"></i> Section Detection</h4>
    <p>Automatically identifies headings, paragraphs, lists, and document hierarchy without relying on styles.</p>
</div>
<div class="help-feature">
    <h4><i data-lucide="file-stack"></i> Multi-Format</h4>
    <p>Unified extraction across PDF, DOCX, PPTX, XLSX, and HTML with consistent results.</p>
</div>
</div>

<h2><i data-lucide="shield"></i> Air-Gap Configuration</h2>

<p>Docling is configured to <strong>never contact the internet</strong> once models are installed:</p>

<table class="help-table">
<thead>
    <tr><th>Environment Variable</th><th>Value</th><th>Purpose</th></tr>
</thead>
<tbody>
    <tr>
        <td><code>DOCLING_ARTIFACTS_PATH</code></td>
        <td><em>path to models</em></td>
        <td>Location of pre-downloaded AI models</td>
    </tr>
    <tr>
        <td><code>HF_HUB_OFFLINE</code></td>
        <td><code>1</code></td>
        <td>Blocks Hugging Face network calls</td>
    </tr>
    <tr>
        <td><code>TRANSFORMERS_OFFLINE</code></td>
        <td><code>1</code></td>
        <td>Blocks Transformers network calls</td>
    </tr>
    <tr>
        <td><code>HF_DATASETS_OFFLINE</code></td>
        <td><code>1</code></td>
        <td>Blocks Datasets network calls</td>
    </tr>
    <tr>
        <td><code>HF_HUB_DISABLE_TELEMETRY</code></td>
        <td><code>1</code></td>
        <td>Disables all telemetry</td>
    </tr>
    <tr>
        <td><code>DO_NOT_TRACK</code></td>
        <td><code>1</code></td>
        <td>Disables analytics tracking</td>
    </tr>
</tbody>
</table>

<p>These variables are set automatically by the installer scripts.</p>

<h2><i data-lucide="memory-stick"></i> Memory Optimization</h2>

<p>To minimize memory usage, image processing is <strong>disabled by default</strong>:</p>

<pre class="help-code">
# Memory-saving configuration (automatic)
do_picture_classifier = False     # No image classification
do_picture_description = False    # No image descriptions
generate_page_images = False      # No page screenshots
generate_picture_images = False   # No picture extraction

# Results in ~500MB lower memory usage
</pre>

<p>This configuration is optimal for text and table extraction, which is the primary use case for AEGIS.</p>

<h2><i data-lucide="cpu"></i> How TWR Uses Docling</h2>

<h3>Automatic Backend Selection</h3>
<pre class="help-code">
Document Upload
      │
      ▼
┌─────────────────────┐
│ Check Docling       │
│ Available?          │
└─────────┬───────────┘
     YES  │   NO
     ┌────┴────┐
     ▼         ▼
┌─────────┐ ┌─────────┐
│ Docling │ │ Legacy  │
│   AI    │ │ Parser  │
└────┬────┘ └────┬────┘
     │           │
     └─────┬─────┘
           ▼
┌─────────────────────┐
│ Role Extraction     │
│ Quality Analysis    │
│ RACI Detection      │
└─────────────────────┘
</pre>

<h3>Enhanced Role Extraction</h3>
<p>When Docling is available, role extraction is enhanced:</p>
<ul>
    <li><strong>Table Role Boost</strong>: Roles found in tables get +20% confidence</li>
    <li><strong>RACI Detection</strong>: Automatic detection of RACI matrix columns</li>
    <li><strong>Section Context</strong>: Role assignments include section awareness</li>
    <li><strong>Paragraph Typing</strong>: Text classified as heading/list/table_cell for context</li>
</ul>

<h2><i data-lucide="download"></i> Installation</h2>

<h3>Option 1: Online Setup (Internet Required Once)</h3>
<pre class="help-code">
# Run from AEGIS folder
setup_docling.bat

# This will:
# 1. Install PyTorch (CPU-only)
# 2. Install Docling packages
# 3. Download AI models (~1.5GB)
# 4. Configure offline environment
</pre>

<h3>Option 2: Air-Gapped Installation</h3>
<pre class="help-code">
# Step 1: On internet-connected machine
powershell -ExecutionPolicy Bypass -File bundle_for_airgap.ps1

# Step 2: Copy bundle to air-gapped machine

# Step 3: On air-gapped machine
INSTALL_AIRGAP.bat
</pre>

<h2><i data-lucide="hard-drive"></i> Disk Space Requirements</h2>

<table class="help-table">
<thead>
    <tr><th>Component</th><th>Size</th></tr>
</thead>
<tbody>
    <tr><td>PyTorch (CPU-only)</td><td>~800 MB</td></tr>
    <tr><td>Docling packages</td><td>~700 MB</td></tr>
    <tr><td>AI models (layout, TableFormer)</td><td>~1.2 GB</td></tr>
    <tr><td>OCR models (optional)</td><td>~500 MB</td></tr>
    <tr><td><strong>Total (without OCR)</strong></td><td><strong>~2.7 GB</strong></td></tr>
    <tr><td><strong>Total (with OCR)</strong></td><td><strong>~3.2 GB</strong></td></tr>
</tbody>
</table>

<h2><i data-lucide="activity"></i> Performance Comparison</h2>

<table class="help-table">
<thead>
    <tr><th>Feature</th><th>Legacy</th><th>Docling</th></tr>
</thead>
<tbody>
    <tr>
        <td>Table extraction accuracy</td>
        <td>~70%</td>
        <td>~95%</td>
    </tr>
    <tr>
        <td>Complex table handling</td>
        <td>Poor</td>
        <td>Excellent</td>
    </tr>
    <tr>
        <td>Reading order preservation</td>
        <td>No</td>
        <td>Yes</td>
    </tr>
    <tr>
        <td>Section detection</td>
        <td>Style-based only</td>
        <td>AI + Style</td>
    </tr>
    <tr>
        <td>Extraction speed</td>
        <td>Fast</td>
        <td>Moderate</td>
    </tr>
    <tr>
        <td>Memory usage</td>
        <td>Low</td>
        <td>Medium</td>
    </tr>
</tbody>
</table>

<h2><i data-lucide="check-circle"></i> Verifying Offline Status</h2>

<p>Check the About page (Help → About) to see Docling status, or use the API:</p>

<pre class="help-code">
# Check via API
curl http://localhost:5000/api/docling/status

# Expected response for offline-ready system:
{
  "available": true,
  "backend": "docling",
  "version": "2.70.0",
  "offline_mode": true,
  "offline_ready": true,
  "image_processing": false
}
</pre>

<h2><i data-lucide="alert-triangle"></i> Troubleshooting</h2>

<h3>Docling not available</h3>
<ul>
    <li>Run <code>setup_docling.bat</code> to install</li>
    <li>Verify Python 3.10+ is installed</li>
    <li>Check <code>pip list | findstr docling</code></li>
</ul>

<h3>Network errors in offline mode</h3>
<ul>
    <li>Verify <code>HF_HUB_OFFLINE=1</code> is set</li>
    <li>Verify <code>DOCLING_ARTIFACTS_PATH</code> points to valid models</li>
    <li>Restart the application after setting environment variables</li>
</ul>

<h3>Memory issues</h3>
<ul>
    <li>Image processing should be disabled automatically</li>
    <li>Use <code>table_mode='fast'</code> for large documents</li>
    <li>Process documents one at a time</li>
    <li>Close other applications if needed</li>
</ul>
`
};

// ============================================================================
// TECHNICAL - ROLE EXTRACTION
// ============================================================================
HelpDocs.content['tech-roles'] = {
    title: 'Role Extraction',
    subtitle: 'AI-powered organizational role detection (99%+ recall)',
    html: `
<h2><i data-lucide="users"></i> Overview</h2>

<p>AEGIS's role extraction engine (<code>role_extractor_v3.py</code>) automatically identifies organizational roles,
responsibilities, and relationships from technical documents. It achieves <strong>99%+ recall</strong> across
defense, aerospace, government, and academic document types.</p>

<div class="help-callout help-callout-success">
    <i data-lucide="target"></i>
    <div>
        <strong>Validation Results (v3.3.3)</strong>
        <p>Validated on FAA, NASA, MIL-STD (38784B, 40051-2A), NIST SP 800-53, OSHA, KSC, and academic documents. Average recall: 99%+ across 18 document types including defense, aerospace, and government standards.</p>
    </div>
</div>

<h2><i data-lucide="layers"></i> Extraction Pipeline</h2>

<pre class="help-code">
Document Text
      │
      ▼
┌─────────────────────┐
│  Pre-processing     │ ← Normalize text, split paragraphs
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Pattern Matching   │ ← 20+ regex patterns for role indicators
│  - Job title suffixes (Manager, Engineer, Director)
│  - Organizational patterns (team, group, office)
│  - Acronym expansion (PM → Project Manager)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Known Roles Scan   │ ← 228+ pre-defined roles with aliases
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  False Positive     │ ← 192+ exclusions (facilities, processes)
│  Filtering          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Table Boosting     │ ← +20% confidence for RACI/responsibility tables
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Canonical Name     │ ← Consolidate variations (PM → Project Manager)
│  Resolution         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Confidence Scoring │ ← 0.0 to 1.0 based on context
└─────────────────────┘
</pre>

<h2><i data-lucide="shield"></i> False Positive Prevention</h2>

<p>The extractor uses multiple layers to prevent false positives:</p>

<h3>1. Explicit FALSE_POSITIVES Set (192+ entries)</h3>
<p>Terms that look like roles but aren't:</p>
<pre class="help-code">
FALSE_POSITIVES = {
    # Facilities
    'panel test facility', 'flight facility', 'operations center',
    
    # Processes/Events  
    'test readiness review', 'design review', 'preliminary design',
    
    # Generic terms
    'mission assurance', 'verification engineer', 'chief innovation',
    
    # Abstract concepts
    'progress', 'upcoming', 'distinct', 'coordinating'
}
</pre>

<h3>2. Single-Word Exclusions</h3>
<pre class="help-code">
SINGLE_WORD_EXCLUSIONS = {
    'progress', 'work', 'test', 'task', 'plan', 'phase',
    'technical', 'functional', 'operational',
    'coordinating', 'managing', 'performing'
}
</pre>

<h3>3. Noise Pattern Rejection</h3>
<pre class="help-code">
# Rejected starters
noise_starters = ['the', 'a', 'contract', 'provide', 'responsible']

# Rejected connectors in positions 2-4
connector_words = ['is', 'are', 'shall', 'will', 'for']

# Rejected endings
noise_endings = ['begins', 'ends', 'various', 'overall']
</pre>

<h3>4. Validation Order (Critical)</h3>
<pre class="help-code">
def _is_valid_role(candidate):
    # 1. Check false_positives FIRST (before known_roles!)
    if candidate_lower in self.false_positives:
        return False, 0.0

    # 2. Early validation for domain-specific terms (v3.3.x)
    # Worker terms: employer, employees, personnel, staff, workers
    # Defense terms: government, contractor, vendor, supplier, maintainer, lead, pilot, engineer
    # Academic terms: graduate student, postdoctoral researcher, lab supervisor
    if candidate_lower in worker_terms or defense_terms or academic_terms:
        return True, 0.88

    # 3. Then check known_roles
    if candidate_lower in self.known_roles:
        return True, 0.95

    # 4. Finally check suffixes (should NOT override false_positives)
    for suffix in strong_role_suffixes:
        if candidate_lower.endswith(suffix):
            return True, 0.90
</pre>

<h2><i data-lucide="database"></i> Known Roles Database</h2>

<p>The extractor includes 228+ pre-defined roles across domains:</p>

<table class="help-table">
<thead>
    <tr><th>Domain</th><th>Example Roles</th></tr>
</thead>
<tbody>
    <tr>
        <td><strong>Government/Contract</strong></td>
        <td>Contracting Officer (CO), COR, Program Manager, COTR, Procuring Activity, Technical Authority</td>
    </tr>
    <tr>
        <td><strong>Defense/MIL-STD</strong></td>
        <td>Contractor, Subcontractor, Preparing Activity, Custodian, Technical Writer, Illustrator</td>
    </tr>
    <tr>
        <td><strong>Aerospace/Aviation</strong></td>
        <td>Pilot, Flight Crew, Dispatcher, Certificate Holder, Accountable Executive, Lead Engineer</td>
    </tr>
    <tr>
        <td><strong>Systems Engineering</strong></td>
        <td>Systems Engineer, Chief Engineer, Lead Systems Engineer, Validation Engineer</td>
    </tr>
    <tr>
        <td><strong>Project Management</strong></td>
        <td>Project Manager, IPT Lead, Technical Lead, Manager, Director</td>
    </tr>
    <tr>
        <td><strong>OSHA/Safety</strong></td>
        <td>Employer, Employee, Competent Person, Qualified Person, Safety Coordinator</td>
    </tr>
    <tr>
        <td><strong>Academic/Research</strong></td>
        <td>Principal Investigator, Graduate Student, Lab Supervisor, Postdoctoral Researcher</td>
    </tr>
    <tr>
        <td><strong>Quality/Operations</strong></td>
        <td>Quality Assurance, Quality Control, Inspector, Technician, Maintainer, Operator</td>
    </tr>
    <tr>
        <td><strong>Agile/Scrum</strong></td>
        <td>Scrum Master, Product Owner, Agile Team</td>
    </tr>
    <tr>
        <td><strong>Executive</strong></td>
        <td>CEO, CTO, CIO, CISO, CINO</td>
    </tr>
    <tr>
        <td><strong>IT/Security</strong></td>
        <td>Security Officer, Cybersecurity Analyst, DBA, Information Owner</td>
    </tr>
</tbody>
</table>

<h2><i data-lucide="link"></i> Acronym Expansion</h2>

<pre class="help-code">
ROLE_ACRONYMS = {
    'pm': 'project manager',
    'se': 'systems engineer',
    'co': 'contracting officer',
    'cor': 'contracting officer representative',
    'ipt': 'integrated product team',
    'ciso': 'chief information security officer',
    'cra': 'clinical research associate',
    # ... 22 total mappings
}
</pre>

<h2><i data-lucide="table"></i> RACI Matrix Detection</h2>

<p>When tables are detected (via Docling or Camelot), the extractor applies confidence boosting:</p>

<ul>
    <li><strong>+20% confidence</strong> for roles found in RACI/RASCI tables</li>
    <li><strong>Automatic responsibility extraction</strong> from R/A/C/I columns</li>
    <li><strong>Cross-reference validation</strong> with document text</li>
</ul>

<h2><i data-lucide="code"></i> Usage in Code</h2>

<pre class="help-code">
from role_extractor_v3 import RoleExtractorV3

# Create extractor
extractor = RoleExtractorV3()

# Extract from text
result = extractor.extract_roles(document_text)

# Access results
for role in result['roles']:
    print(f"{role['name']} (confidence: {role['confidence']:.2f})")
    print(f"  Found in: {role['context']}")
    print(f"  Responsibilities: {role['responsibilities']}")

# Get statistics
print(f"Total roles: {result['stats']['total']}")
print(f"High confidence: {result['stats']['high_confidence']}")
</pre>

<h2><i data-lucide="settings"></i> Configuration Options</h2>

<table class="help-table">
<thead>
    <tr><th>Option</th><th>Default</th><th>Description</th></tr>
</thead>
<tbody>
    <tr>
        <td><code>min_confidence</code></td>
        <td>0.6</td>
        <td>Minimum confidence threshold for inclusion</td>
    </tr>
    <tr>
        <td><code>enable_table_boost</code></td>
        <td>True</td>
        <td>Apply confidence boost for table-found roles</td>
    </tr>
    <tr>
        <td><code>expand_acronyms</code></td>
        <td>True</td>
        <td>Expand recognized acronyms to full names</td>
    </tr>
    <tr>
        <td><code>use_nlp_enhancement</code></td>
        <td>True</td>
        <td>Use spaCy NER if available</td>
    </tr>
</tbody>
</table>

<h2><i data-lucide="activity"></i> Performance Metrics</h2>

<table class="help-table">
<thead>
    <tr><th>Document Type</th><th>Precision</th><th>Recall</th><th>F1 Score</th></tr>
</thead>
<tbody>
    <tr>
        <td>Government SOW</td>
        <td>100%</td>
        <td>85.7%</td>
        <td>92.3%</td>
    </tr>
    <tr>
        <td>DoD SEP (Defense)</td>
        <td>100%</td>
        <td>87.5%</td>
        <td>93.3%</td>
    </tr>
    <tr>
        <td>Smart Columbus SEMP (Agile)</td>
        <td>100%</td>
        <td>100%</td>
        <td>100%</td>
    </tr>
    <tr>
        <td>INCOSE/APM Guide (Industry)</td>
        <td>84.6%</td>
        <td>84.6%</td>
        <td>84.6%</td>
    </tr>
    <tr>
        <td><strong>Overall Average</strong></td>
        <td><strong>94.7%</strong></td>
        <td><strong>90.0%</strong></td>
        <td><strong>92.3%</strong></td>
    </tr>
</tbody>
</table>
`
};

// ============================================================================
// TECHNICAL - STATEMENT FORGE ENGINE
// ============================================================================
HelpDocs.content['tech-statement-forge'] = {
    title: 'Statement Forge Engine',
    subtitle: 'Extraction pipeline, persistence model, and comparison algorithm',
    html: `
<div class="help-callout help-callout-info">
    <i data-lucide="cpu"></i>
    <div>
        <strong>Technical Section</strong>
        <p>This section covers the internal architecture of Statement Forge for developers and advanced users.</p>
    </div>
</div>

<h2><i data-lucide="layers"></i> Module Architecture</h2>
<pre class="help-code">
statement_forge/
├── __init__.py          # Package init
├── extractor.py         # Core extraction engine (1,000+ verb patterns)
├── models.py            # Statement dataclass with to_dict() serialization
├── export.py            # Export formatters (Nimbus CSV, Excel, JSON, Word)
└── routes.py            # Flask blueprint (20+ API endpoints)
</pre>

<h2><i data-lucide="database"></i> Data Model</h2>
<p>Statements are stored in the <code>scan_statements</code> table with foreign keys to both <code>scans</code> and <code>documents</code>:</p>
<pre class="help-code">
CREATE TABLE scan_statements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id         INTEGER NOT NULL,     -- FK to scans.id
    document_id     INTEGER NOT NULL,     -- FK to documents.id
    statement_number TEXT,                -- e.g., "3.1.2"
    title           TEXT,                 -- Section or requirement title
    description     TEXT NOT NULL,        -- Full statement text
    level           INTEGER DEFAULT 1,    -- Hierarchy depth (1-6)
    role            TEXT DEFAULT '',      -- Responsible actor
    directive       TEXT DEFAULT '',      -- shall/must/will/should/may
    section         TEXT DEFAULT '',      -- Parent section reference
    is_header       INTEGER DEFAULT 0,   -- Section header flag
    notes_json      TEXT,                -- Additional notes (JSON array)
    position_index  INTEGER DEFAULT 0    -- Display order
)

Indexes: scan_id, document_id, directive
</pre>

<h2><i data-lucide="workflow"></i> Extraction Pipeline</h2>
<p>The extraction runs in five stages during every document scan:</p>
<ol>
    <li><strong>Text Segmentation</strong> — Document text is split into paragraphs. Blank lines, indentation changes, and numbering patterns delineate paragraph boundaries.</li>
    <li><strong>Section Detection</strong> — Numbered patterns (1.0, 2.1.3, A.1, etc.) and formatting cues identify section headers. The numbering depth determines the hierarchy level (1-6).</li>
    <li><strong>Directive Scanning</strong> — Each paragraph is scanned for directive keywords. The keyword's position and syntactic role determine the directive type and confidence.</li>
    <li><strong>Role Extraction</strong> — The sentence subject preceding the directive verb is parsed to identify the responsible actor. Common patterns: "The [Role] shall...", "[Department] will...", "[Title] must...".</li>
    <li><strong>Deduplication</strong> — Statements are fingerprinted using <code>(description[:100], directive)</code> tuples. Exact matches are removed; near-matches are preserved for manual review.</li>
</ol>

<h2><i data-lucide="clock"></i> Persistence Flow</h2>
<pre class="help-code">
Document Scan Flow:
1. engine.review_document()          → results dict
2. sf_extract(full_text, filename)   → List[Statement]
3. results['statement_forge_summary'] ← inject summary
4. db.record_scan(results_json)      → scan_id, document_id
5. db.save_scan_statements(          → bulk INSERT
       scan_id, document_id,
       [stmt.to_dict() for stmt in statements]
   )
</pre>
<p>Key design decision: SF extraction runs <em>before</em> <code>record_scan()</code> so the statement summary is included in <code>results_json</code>. Individual statements are then bulk-inserted into the dedicated table <em>after</em> the scan record is created (to get the <code>scan_id</code>).</p>

<h2><i data-lucide="git-compare"></i> Comparison Algorithm</h2>
<p>Cross-scan comparison uses fingerprint-based matching rather than sequence alignment:</p>
<pre class="help-code">
def compare_scan_statements(scan_id_1, scan_id_2):
    # Build fingerprint sets
    set1 = {(desc[:100], directive) for each statement in scan_1}
    set2 = {(desc[:100], directive) for each statement in scan_2}

    added   = set2 - set1   # In scan 2 but not scan 1
    removed = set1 - set2   # In scan 1 but not scan 2
    unchanged = set1 & set2  # In both scans

    return {added, removed, unchanged_count}
</pre>
<p>This approach prioritizes detecting meaningful requirement changes over tracking cosmetic edits. A statement with a changed directive (e.g., "shall" to "may") is correctly flagged as "removed + added" rather than silently classified as unchanged.</p>

<h2><i data-lucide="code"></i> API Endpoints</h2>
<table class="help-table">
    <thead><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>GET</td><td><code>/api/statement-forge/history/&lt;doc_id&gt;</code></td><td>Per-scan summaries with directive counts, role counts, and section counts for a document</td></tr>
        <tr><td>GET</td><td><code>/api/statement-forge/scan/&lt;scan_id&gt;</code></td><td>All statements for a specific scan, ordered by position_index</td></tr>
        <tr><td>GET</td><td><code>/api/statement-forge/trends/&lt;doc_id&gt;</code></td><td>Timeline data (statement counts per scan) and role frequency for charting</td></tr>
        <tr><td>GET</td><td><code>/api/statement-forge/compare/&lt;id1&gt;/&lt;id2&gt;</code></td><td>Fingerprint-based diff between two scans with added/removed/unchanged lists</td></tr>
    </tbody>
</table>

<h2><i data-lucide="monitor"></i> Frontend Module</h2>
<p>The Statement History viewer (<code>static/js/features/statement-history.js</code>) is an IIFE module exposed via <code>TWR.StatementHistory</code>:</p>
<pre class="help-code">
TWR.StatementHistory = {
    VERSION: '4.2.0',
    open(documentId, scanId, documentName),  // Open viewer
    close(),                                  // Close viewer
    showOverview(),                           // Dashboard view
    showDocumentViewer(scanId),              // Source viewer
    showCompare(scanId1, scanId2),           // Diff view
    getState()                               // Current state
}
</pre>
<p>The module creates its own modal overlay, manages navigation state with a back-stack, renders Chart.js instances for trend and directive charts, and handles text selection events for the highlight-to-create feature.</p>

<h2><i data-lucide="trash-2"></i> Cascade Delete</h2>
<p>When a scan is deleted via the History tab, the <code>delete_scan()</code> method automatically removes associated statements from <code>scan_statements</code> via cascade delete. No orphaned statement records are left behind.</p>
`
};

// ============================================================================
// TECHNICAL - NLP PIPELINE
// ============================================================================
HelpDocs.content['tech-nlp'] = {
    title: 'NLP Pipeline',
    subtitle: 'Natural language processing for maximum accuracy',
    html: `
<div class="help-callout help-callout-success">
    <i data-lucide="sparkles"></i>
    <div>
        <strong>v3.3.0: Maximum Accuracy NLP Enhancement Suite</strong>
        <p>Comprehensive upgrade with transformer models, adaptive learning, and advanced dependency parsing for near-100% accuracy.</p>
    </div>
</div>

<h2><i data-lucide="brain"></i> Enhanced Processing Pipeline (v3.3.0)</h2>

<pre class="help-code">
Raw Text
    │
    ▼
┌────────────────────┐
│ Technical Dictionary│ ← 10,000+ aerospace/defense terms
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ spaCy Transformer  │ ← en_core_web_trf (best accuracy)
│ or en_core_web_lg  │   Tokenization, POS, NER, Dependencies
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ EntityRuler        │ ← 100+ aerospace/defense patterns
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ PhraseMatcher      │ ← 150+ role gazetteer lookups
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Ensemble Extraction│ ← Combine NER + Patterns + Dependency
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Adaptive Learning  │ ← Boost confidence from user decisions
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Results            │ ← Roles, acronyms, issues with confidence
└────────────────────┘
</pre>

<h2><i data-lucide="database"></i> Technical Dictionary System</h2>
<p>Master dictionary with 10,000+ embedded terms:</p>
<table class="help-table">
    <thead><tr><th>Category</th><th>Terms</th><th>Examples</th></tr></thead>
    <tbody>
        <tr><td>Aerospace/Defense</td><td>1,200+</td><td>avionics, propulsion, sustainment</td></tr>
        <tr><td>Government Contracting</td><td>500+</td><td>acquisition, milestone, deliverable</td></tr>
        <tr><td>Software/IT</td><td>500+</td><td>kubernetes, api, backend</td></tr>
        <tr><td>Corrections</td><td>500+</td><td>misspelling → correct mappings</td></tr>
        <tr><td>Acronyms</td><td>300+</td><td>NASA, FAA, CDR with expansions</td></tr>
        <tr><td>Proper Nouns</td><td>200+</td><td>Boeing, Lockheed Martin, SpaceX</td></tr>
    </tbody>
</table>

<h2><i data-lucide="trending-up"></i> Adaptive Learning System</h2>
<p>The system learns from your decisions to improve accuracy over time:</p>
<ul>
    <li><strong>Role Decisions</strong> — confirm/reject/deliverable tracking</li>
    <li><strong>Acronym Decisions</strong> — accept/expand/ignore patterns</li>
    <li><strong>Grammar Patterns</strong> — suppress similar issues</li>
    <li><strong>Spelling Decisions</strong> — accept/correct/ignore</li>
</ul>
<pre class="help-code">
# Confidence boosting formula
base_confidence = 0.75
learning_boost = learner.get_confidence_boost(pattern_key)  # -0.3 to +0.3
final_confidence = min(1.0, base_confidence + learning_boost)
</pre>

<h2><i data-lucide="layers"></i> Ensemble Role Extraction</h2>
<p>Multiple extraction methods combined for best accuracy:</p>
<ol>
    <li><strong>EntityRuler</strong> — 100+ domain patterns (AEROSPACE_ROLE, DEFENSE_ROLE)</li>
    <li><strong>PhraseMatcher</strong> — 150+ exact role phrase lookups</li>
    <li><strong>spaCy NER</strong> — PERSON, ORG entities with role indicators</li>
    <li><strong>Dependency Parsing</strong> — nsubj/dobj with action verbs</li>
    <li><strong>Pattern Matching</strong> — Regex for "The X shall" patterns</li>
</ol>

<h2><i data-lucide="search"></i> Advanced Checkers (v3.3.0)</h2>

<h3>Enhanced Passive Voice (Dependency-Based)</h3>
<p>Uses spaCy dependency parsing instead of regex. Includes 300+ adjectival participles whitelist to prevent false positives like "established procedures" and "required documents".</p>

<h3>Sentence Fragment Detection</h3>
<p>Full syntactic analysis checking for subject presence, finite verbs, subordinate clause completeness, and question/imperative handling.</p>

<h3>Requirements Analyzer</h3>
<p>Checks atomicity (one "shall" per requirement), testability (measurable criteria), escape clauses (TBD, TBR, TBS), and 60+ ambiguous terms.</p>

<h3>Terminology Consistency</h3>
<p>Detects spelling variants (backend/back-end), British/American (colour/color), abbreviation consistency (config/configuration), and hyphenation issues.</p>

<h2><i data-lucide="target"></i> Accuracy Improvements (v3.3.x)</h2>
<table class="help-table">
    <thead><tr><th>Category</th><th>Previous</th><th>Current</th><th>Method</th></tr></thead>
    <tbody>
        <tr><td>Role Extraction</td><td>56.7%</td><td><strong>99%+</strong></td><td>Domain validation + 228+ roles + Defense/Aerospace terms</td></tr>
        <tr><td>Acronym Detection</td><td>75%</td><td>95%+</td><td>Domain dictionaries + Context</td></tr>
        <tr><td>Passive Voice</td><td>70%</td><td>88%+</td><td>Dependency parsing (not regex)</td></tr>
        <tr><td>Spelling</td><td>85%</td><td>98%+</td><td>Technical dictionary + SymSpell</td></tr>
        <tr><td>Requirements</td><td>80%</td><td>95%+</td><td>Pattern expansion + Atomicity</td></tr>
        <tr><td>Terminology</td><td>70%</td><td>92%+</td><td>Variant detection + Semantic</td></tr>
    </tbody>
</table>

<h3>Role Extraction by Document Type (v3.3.3)</h3>
<table class="help-table">
    <thead><tr><th>Document Category</th><th>Documents Tested</th><th>Recall</th></tr></thead>
    <tbody>
        <tr><td>FAA, OSHA, Stanford</td><td>3</td><td><strong>103%</strong></td></tr>
        <tr><td>Defense/Government (MIL-STD, NIST)</td><td>8</td><td><strong>99.5%</strong></td></tr>
        <tr><td>Aerospace (NASA, FAA, KSC)</td><td>7</td><td><strong>99.0%</strong></td></tr>
    </tbody>
</table>

<h2><i data-lucide="gauge"></i> Performance Considerations</h2>
<ul>
    <li><strong>Model loading</strong> — Lazy loading, singleton pattern</li>
    <li><strong>Transformer fallback</strong> — Falls back to lg model if trf unavailable</li>
    <li><strong>Caching</strong> — Results cached during session</li>
    <li><strong>Chunking</strong> — Large documents processed in chunks</li>
    <li><strong>100% Offline</strong> — All models work without internet</li>
</ul>

<h2><i data-lucide="download"></i> Offline Package Requirements</h2>
<p>For maximum accuracy with transformer models:</p>
<pre class="help-code">
spacy 3.7.4           ~10MB
en_core_web_trf 3.7.x ~460MB  (Best accuracy)
en_core_web_lg 3.7.x  ~746MB  (Fallback)
coreferee 2.4.x       ~20MB   (Coreference resolution)
───────────────────────────────
Total additional:     ~1.2GB
</pre>
`
};

// ============================================================================
// TECHNICAL - API REFERENCE
// ============================================================================
HelpDocs.content['tech-api'] = {
    title: 'API Reference',
    subtitle: 'REST API endpoints for programmatic access',
    html: `
<h2><i data-lucide="code"></i> API Overview</h2>
<p>AEGIS exposes a REST API on <code>http://127.0.0.1:5050/api/</code> (default port).</p>

<div class="help-callout help-callout-info">
    <i data-lucide="shield"></i>
    <div>
        <strong>CSRF Protection</strong>
        <p>State-changing endpoints (POST, PUT, DELETE) require a CSRF token. Tokens are automatically included when using the web interface.</p>
    </div>
</div>

<h2><i data-lucide="upload"></i> Document Analysis</h2>

<h3>POST /api/upload</h3>
<p>Upload document for analysis.</p>
<pre class="help-code">
curl -X POST -F "file=@document.docx" http://127.0.0.1:5050/api/upload

# Response:
{
  "success": true,
  "document_id": "abc123",
  "filename": "document.docx",
  "word_count": 5420,
  "page_count": 15
}
</pre>

<h3>POST /api/review</h3>
<p>Run analysis with specified checkers.</p>
<pre class="help-code">
{
  "document_id": "abc123",
  "checkers": ["acronyms", "grammar", "spelling", "passive_voice"]
}

# Response includes issues array with severity, message, location
</pre>

<h3>GET /api/results/{document_id}</h3>
<p>Retrieve analysis results.</p>

<h2><i data-lucide="users"></i> Roles & Responsibilities</h2>

<h3>GET /api/roles/aggregated</h3>
<p>Get all roles aggregated across documents.</p>
<pre class="help-code">
# Response:
{
  "success": true,
  "data": {
    "roles": [...],
    "total_roles": 45,
    "unique_documents": 8
  }
}
</pre>

<h3>GET /api/roles/extract</h3>
<p>Extract roles from current document.</p>

<h3>GET /api/roles/raci</h3>
<p>Get RACI matrix data.</p>

<h3>GET /api/roles/graph</h3>
<p>Get relationship graph data for visualization.</p>

<h3>GET /api/roles/dictionary</h3>
<p>Get/update the role dictionary.</p>

<h3>POST /api/roles/adjudicate/batch</h3>
<p>Batch adjudicate multiple roles in a single transaction.</p>

<h3>POST /api/roles/auto-adjudicate</h3>
<p>Run auto-classification on all pending roles.</p>

<h3>GET /api/roles/adjudication/export-html</h3>
<p>Download an interactive HTML kanban board for offline team review.</p>
<pre class="help-code">
# Returns: HTML file download (Content-Disposition: attachment)
# Includes all roles, function categories, and embedded CSS/JS
</pre>

<h3>POST /api/roles/adjudication/import</h3>
<p>Import adjudication decisions from an Interactive HTML Board export.</p>
<pre class="help-code">
{
  "aegis_version": "4.0.3",
  "export_type": "adjudication_decisions",
  "decisions": [
    { "role_name": "Project Manager", "action": "confirmed",
      "category": "Management", "notes": "Core PM role",
      "function_tags": ["PM", "SE"] }
  ]
}
</pre>

<h3>POST /api/roles/share/package</h3>
<p>Create a downloadable .aegis-roles package for email distribution.</p>
<pre class="help-code">
# Returns: .aegis-roles file download
# Contains: roles, function_categories, metadata
</pre>

<h3>POST /api/roles/share/import-package</h3>
<p>Import a .aegis-roles package (file upload or JSON body).</p>
<pre class="help-code">
# Accepts: multipart/form-data with 'file' field, or JSON body
# Returns: { success, roles_added, roles_skipped, categories_added }
</pre>

<h2><i data-lucide="download"></i> Export</h2>

<h3>POST /api/export/word</h3>
<p>Generate Word document with tracked changes.</p>

<h3>POST /api/export/csv</h3>
<p>Export issues as CSV.</p>

<h3>POST /api/export/json</h3>
<p>Export structured JSON data.</p>

<h2><i data-lucide="hammer"></i> Statement Forge</h2>

<h3>POST /api/statement-forge/extract</h3>
<p>Extract actionable statements from document.</p>

<h3>POST /api/statement-forge/export</h3>
<p>Export statements in various formats (CSV, JSON, Excel).</p>

<h2><i data-lucide="settings"></i> Configuration</h2>

<h3>GET /api/config</h3>
<p>Get current configuration.</p>

<h3>POST /api/config</h3>
<p>Update configuration.</p>

<h2><i data-lucide="activity"></i> Health & Updates</h2>

<h3>GET /api/updates/status</h3>
<p>Get update system status including pending updates and backups.</p>

<h3>GET /api/updates/check</h3>
<p>Check for available updates in the updates/ folder.</p>

<h3>POST /api/updates/apply</h3>
<p>Apply pending updates (creates backup first).</p>
<pre class="help-code">
{
  "create_backup": true
}
</pre>

<h3>GET /api/updates/backups</h3>
<p>List available backups.</p>

<h3>POST /api/updates/rollback</h3>
<p>Rollback to a previous backup.</p>
<pre class="help-code">
{
  "backup_name": "backup_20260127_143022"
}
</pre>

<h3>POST /api/updates/restart</h3>
<p>Restart the server after updates.</p>

<h3>GET /api/updates/health</h3>
<p>Server health check (used for restart polling).</p>

<h2><i data-lucide="sparkles"></i> Docling Status</h2>

<h3>GET /api/docling/status</h3>
<p>Check Docling AI extraction status.</p>
<pre class="help-code">
# Response:
{
  "available": true,
  "backend": "docling",
  "version": "2.70.0",
  "offline_mode": true,
  "offline_ready": true,
  "image_processing": false
}
</pre>

<h2><i data-lucide="activity"></i> Extraction Capabilities</h2>

<h3>GET /api/extraction/capabilities</h3>
<p>Get available extraction methods and accuracy estimates.</p>
`
};

// ============================================================================
// TROUBLESHOOTING - COMMON ISSUES
// ============================================================================
HelpDocs.content['trouble-common'] = {
    title: 'Common Issues',
    subtitle: 'Solutions to frequently encountered problems',
    html: `
<h2><i data-lucide="alert-circle"></i> Installation Issues</h2>

<h3>Installer doesn't run</h3>
<ul>
    <li>Right-click INSTALL.ps1 → "Run with PowerShell"</li>
    <li>If blocked: <code>Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass</code></li>
</ul>

<h3>"Python not found"</h3>
<ul>
    <li>Install Python 3.8+ from python.org</li>
    <li>Ensure "Add Python to PATH" was checked</li>
    <li>Restart PowerShell after installation</li>
</ul>

<h3>Pip install hangs</h3>
<ul>
    <li>Normal on air-gapped networks—progress bar should show activity</li>
    <li>v3.0.51+ skips pip upgrade to avoid hangs</li>
</ul>

<h2><i data-lucide="alert-circle"></i> Runtime Issues</h2>

<h3>Server won't start</h3>
<ul>
    <li>Check if port 5050 is in use: <code>netstat -an | findstr 5050</code></li>
    <li>Check logs in <code>logs/</code> folder</li>
    <li>Delete <code>.venv</code> and reinstall</li>
</ul>

<h3>Browser shows blank page</h3>
<ul>
    <li>Clear browser cache (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>)</li>
    <li>Try different browser</li>
    <li>Check JavaScript console for errors</li>
</ul>

<h3>Document fails to load</h3>
<ul>
    <li>Close document in Word first</li>
    <li>Remove password protection</li>
    <li>Try saving as .docx (not .doc)</li>
    <li>Check file size (max 50 MB)</li>
</ul>

<h2><i data-lucide="alert-circle"></i> Update Issues</h2>

<h3>Updates don't apply</h3>
<ul>
    <li>Verify v3.0.51+ (check Settings → About)</li>
    <li>Ensure using <code>Run_TWR.bat</code> from v3.0.51</li>
    <li>Check update files are in <code>updates/</code> folder</li>
</ul>

<h3>Server doesn't restart</h3>
<ul>
    <li>The Run_TWR.bat must contain restart loop (v3.0.51+)</li>
    <li>Manual restart: Stop_TWR.bat then Run_TWR.bat</li>
</ul>
`
};

// ============================================================================
// TROUBLESHOOTING - ERROR MESSAGES
// ============================================================================
HelpDocs.content['trouble-errors'] = {
    title: 'Error Messages',
    subtitle: 'Understanding and resolving error messages',
    html: `
<h2><i data-lucide="alert-triangle"></i> Common Errors</h2>

<div class="help-error-list">
    <div class="help-error-item">
        <h3>❌ "Failed to connect to server"</h3>
        <p><strong>Cause:</strong> Server not running or wrong port.</p>
        <p><strong>Solution:</strong> Run <code>Run_TWR.bat</code>. Check firewall settings.</p>
    </div>
    
    <div class="help-error-item">
        <h3>❌ "Document extraction failed"</h3>
        <p><strong>Cause:</strong> Corrupted file or unsupported format.</p>
        <p><strong>Solution:</strong> Open in Word, save as new .docx file.</p>
    </div>
    
    <div class="help-error-item">
        <h3>❌ "Checker timeout"</h3>
        <p><strong>Cause:</strong> Very large document or complex content.</p>
        <p><strong>Solution:</strong> Split document or disable some checkers.</p>
    </div>
    
    <div class="help-error-item">
        <h3>❌ "Export failed: File in use"</h3>
        <p><strong>Cause:</strong> Previous export still open in Word.</p>
        <p><strong>Solution:</strong> Close the file in Word and retry.</p>
    </div>
    
    <div class="help-error-item">
        <h3>❌ "PDF extraction limited"</h3>
        <p><strong>Cause:</strong> Scanned PDF without selectable text.</p>
        <p><strong>Solution:</strong> Use OCR software first, or use .docx format.</p>
    </div>
</div>
`
};

// ============================================================================
// TROUBLESHOOTING - PERFORMANCE
// ============================================================================
HelpDocs.content['trouble-performance'] = {
    title: 'Performance',
    subtitle: 'Optimizing AEGIS for large documents',
    html: `
<h2><i data-lucide="gauge"></i> Performance Tips</h2>

<h3>Large Documents (100+ pages)</h3>
<ul>
    <li>Disable checkers you don't need</li>
    <li>Use presets instead of "All"</li>
    <li>Consider splitting into smaller documents</li>
</ul>

<h3>Many Issues (500+)</h3>
<ul>
    <li>Enable family grouping (Settings → General)</li>
    <li>Use Triage Mode for systematic review</li>
    <li>Filter by severity to focus on critical items</li>
</ul>

<h3>Slow Startup</h3>
<ul>
    <li>First run after install may be slow (Python compiles)</li>
    <li>Subsequent runs should be faster</li>
    <li>Check for antivirus scanning the .venv folder</li>
</ul>

<h2><i data-lucide="bar-chart"></i> Benchmarks</h2>
<table class="help-table">
    <thead><tr><th>Document Size</th><th>All Checkers</th><th>Minimal Preset</th></tr></thead>
    <tbody>
        <tr><td>10 pages</td><td>5-10 sec</td><td>2-5 sec</td></tr>
        <tr><td>50 pages</td><td>15-30 sec</td><td>5-15 sec</td></tr>
        <tr><td>100 pages</td><td>30-60 sec</td><td>10-30 sec</td></tr>
        <tr><td>200+ pages</td><td>60-120 sec</td><td>30-60 sec</td></tr>
    </tbody>
</table>
`
};

// ============================================================================
// VERSION HISTORY
// ============================================================================
HelpDocs.content['version-history'] = {
    title: 'Version History',
    subtitle: 'Release notes and changelog',
    html: `
<div class="help-changelog">
    <div class="changelog-version changelog-current">
        <h3>v5.5.0 <span class="changelog-date">February 16, 2026</span></h3>
        <p><strong>Document Repository Batch Scanning</strong></p>
        <ul>
            <li><strong>BATCH: Server-Side Folder Scanning</strong> — New endpoint scans entire document repositories with nested subdirectories. Enter a folder path, preview discovered files, then scan all documents in one operation.</li>
            <li><strong>BATCH: Smart File Discovery</strong> — Recursive directory traversal with intelligent filtering: skips hidden directories, empty files, files over 100MB, and common non-document directories (.git, node_modules, __pycache__)</li>
            <li><strong>BATCH: Chunked Processing</strong> — Documents processed in chunks of 5 with 3 concurrent threads per chunk. Memory cleanup (gc.collect) runs between chunks to handle repositories with hundreds of files</li>
            <li><strong>BATCH: Increased Limits</strong> — Upload batch limits raised from 10 files/100MB to 50 files/500MB per batch. Frontend auto-chunks larger sets and processes up to 3 batches concurrently</li>
            <li><strong>BATCH: Preview Before Scan</strong> — New "Preview" button discovers all documents and shows file count, total size, and type breakdown before committing to a full scan</li>
            <li><strong>BATCH: Comprehensive Results</strong> — Aggregated grade distribution, severity breakdown, category analysis, role discovery, and per-document scores across the entire repository</li>
            <li><strong>BATCH: Graceful Error Handling</strong> — Individual file errors are caught and reported without stopping the scan. Corrupt files, permission errors, and unsupported types are logged and skipped</li>
            <li><strong>TEST: Local Verification Script</strong> — New test_scan_local.py script runs 5 single-file scans with different types/complexity levels, then tests batch folder scanning against the test_documents directory</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.4.0 <span class="changelog-date">February 16, 2026</span></h3>
        <p><strong>Performance Optimization + spaCy Ecosystem Deep Analysis</strong></p>
        <ul>
            <li><strong>PERFORMANCE: Zero Dark Mode Flash</strong> — Inline CSS variables + data-theme attribute set before any stylesheet loads, eliminating FOUC</li>
            <li><strong>PERFORMANCE: Deferred Script Loading</strong> — 30+ feature module scripts now use defer attribute; initial paint 40-60% faster</li>
            <li><strong>PERFORMANCE: Async CSS Loading</strong> — 13 feature stylesheets load asynchronously; only critical CSS blocks render</li>
            <li><strong>PERFORMANCE: Parallel Batch Scan</strong> — ThreadPoolExecutor processes up to 3 documents concurrently during batch review</li>
            <li><strong>NLP: 11 New v5.3.0 Checkers</strong> — Negation detection, text metrics, sentence complexity, terminology (WordNet), subjectivity, lexical diversity, YAKE keywords, requirement similarity, coherence, defined-before-used, quantifier precision</li>
            <li><strong>NLP: 6 New v5.2.0 Checkers</strong> — Coreference resolution, advanced prose lint, verbosity detection, keyword extraction, INCOSE compliance, semantic role analysis</li>
            <li><strong>NLP: New Libraries</strong> — negspacy, textdescriptives, spacy-wordnet, spacytextblob, lexical_diversity, yake, coreferee, proselint, textacy, sumy</li>
            <li><strong>CHECKERS: 100+ Total</strong> — 98 UI-controlled + 7 always-on checkers available for document analysis</li>
            <li><strong>UI: spaCy Deep Analysis Panel</strong> — New Settings section with 4 subcategories and 11 checkboxes for v5.3.0 checkers</li>
            <li><strong>INSTALL: Windows Wheels Updated</strong> — All new NLP dependency wheels included for air-gapped deployment</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.1.0 <span class="changelog-date">February 16, 2026</span></h3>
        <p><strong>Security Hardening + Accessibility + Print Support</strong></p>
        <ul>
            <li><strong>SECURITY: CSRF Protection</strong> — Added @require_csrf to 9 unprotected POST routes (SOW, presets, analyzers, diagnostics)</li>
            <li><strong>SECURITY: Fresh Token Pattern</strong> — Implemented in 18+ JavaScript functions with _getFreshCsrf() helper</li>
            <li><strong>SECURITY: Data Management Fixed</strong> — Clear scan history, statements, roles, learning, and factory reset all use fresh CSRF</li>
            <li><strong>ARCHITECTURE: spaCy Singleton</strong> — Fixed model instance sharing to improve performance, prevent multiple loads</li>
            <li><strong>QUALITY: Deduplication Key</strong> — Improved from 50 to 80 characters with rule_id for better uniqueness</li>
            <li><strong>QUALITY: Passive Voice Whitelist</strong> — Added 18 aerospace adjectival participles for technical docs</li>
            <li><strong>QUALITY: All Checkers Verified</strong> — 83 checkers working with 14 new UI toggles (Writing Quality, Technical, Requirements)</li>
            <li><strong>ACCESSIBILITY: WCAG 2.1 Level A</strong> — 134 aria-labels, 28 modals with role/aria-modal, 116 aria-hidden, tab roles on all navigation</li>
            <li><strong>PRINT: print.css Stylesheet</strong> — Optimized for document printing: hidden sidebar/toolbar/toasts, proper page breaks, URL display after links</li>
            <li><strong>UI: Folder Browse Button</strong> — Now opens native OS folder picker via backend API instead of file dialog</li>
            <li><strong>UI: Dropdown Z-Index</strong> — Fixed conflict with toast notifications (toasts always on top at z-index 200000)</li>
            <li><strong>UI: Dark Mode Radio Cards</strong> — Added overrides for modal radio card components in dark mode</li>
            <li><strong>INSTALL: Windows Wheels</strong> — 195 pre-built x64 wheels for air-gapped installation (numpy, pandas, scipy, scikit-learn, spaCy, docling, etc.)</li>
            <li><strong>INSTALL: download_win_wheels.py</strong> — Script for connected environments to auto-download all wheels</li>
            <li><strong>INSTALL: install_offline.bat Updated</strong> — Now supports both wheel directories for flexible deployment</li>
            <li><strong>FIX: Landing Page 0 Roles</strong> — Fallback from role_dictionary to roles table when not initialized</li>
            <li><strong>FIX: Source Document Loading</strong> — Clicking roles in Adjudication now correctly loads source document</li>
            <li><strong>FIX: Updater Timeout</strong> — Added 15s timeout with AbortController to prevent spinning forever</li>
            <li><strong>FIX: Diagnostic Email Export</strong> — Changed from GET to POST with fresh CSRF token</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.0.0 <span class="changelog-date">February 15, 2026</span></h3>
        <p><strong>Multiprocessing Architecture + Role Extraction Overhaul</strong></p>
        <ul>
            <li><strong>ARCHITECTURE: Multiprocessing</strong> — Review jobs run in separate Process (not thread) for server responsiveness and crash isolation</li>
            <li><strong>ARCHITECTURE: Per-Doc Timeout</strong> — 600s default with graceful process termination and progress via multiprocessing.Queue</li>
            <li><strong>ROLE EXTRACTION v3.5.0: 3-Layer Filtering</strong> — Organization entities, confidence threshold, single-word variants removed</li>
            <li><strong>ROLE EXTRACTION: 30+ New Aerospace Roles</strong> — Technical fellow, mission systems engineer, failure review board, and more</li>
            <li><strong>ROLE EXTRACTION: Discovery Mode</strong> — Filters organization entities, low-confidence roles, and stopword roles</li>
            <li><strong>TESTED: NASA SE Handbook</strong> — 297 pages with false positives reduced from 44% to <5%</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.9 <span class="changelog-date">February 15, 2026</span></h3>
        <p><strong>Statement Source Viewer + Error Handling + Windows Compatibility</strong></p>
        <ul>
            <li><strong>FEATURE: Statement Source Viewer</strong> — Highlight-to-select editing for inline statement creation, integrates with Statement Forge history</li>
            <li><strong>FIX: SOW Generation 500 Error</strong> — Missing timezone import in datetime operations (timezone.utc)</li>
            <li><strong>FIX: Document Compare Auto-Load</strong> — Now auto-selects oldest doc on left, newest on right, and immediately runs comparison</li>
            <li><strong>FIX: Toast "[object Object]"</strong> — API error responses now include structured format with proper message extraction via getErrorMessage()</li>
            <li><strong>FIX: Template Error Handling</strong> — Template files now correctly extract error.message from structured error objects</li>
            <li><strong>IMPROVED: Windows Compatibility</strong> — Platform-aware chmod, os.name detection, cross-platform pathlib.Path handling throughout codebase</li>
            <li><strong>IMPROVED: Performance</strong> — Batch review rendering for 100+ statements, particle effects transparency, session logging with correlation IDs</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.5 <span class="changelog-date">February 15, 2026</span></h3>
        <p><strong>Version Management Overhaul</strong></p>
        <ul>
            <li><strong>FIX: Version Display Stuck</strong> — Root cause: duplicate version.json files (root vs static/) with stale static copy</li>
            <li><strong>FIX: Import-Time Caching</strong> — config_logging.py VERSION constant was stale after updates; now uses get_version() for fresh reads</li>
            <li><strong>FIX: Cache-Busting</strong> — Regex in core_routes.py handles existing ?v= params and adds missing ones; stripped hardcoded ?v= from index.html</li>
            <li><strong>NEW: get_version()</strong> — Reads version.json fresh from disk every call, replaces stale VERSION constant for user-facing endpoints</li>
            <li><strong>IMPROVED: Client-Side Version</strong> — JS now fetches /api/version first (always fresh), /static/version.json as fallback only</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.0 <span class="changelog-date">February 15, 2026</span></h3>
        <p><strong>Landing Page Stability + Offline Distribution</strong></p>
        <ul>
            <li><strong>FIX: Landing Page Empty Tiles</strong> — Async init race condition: show() called init() without await, session restore skipped init() entirely</li>
            <li><strong>FIX: Toast Z-Index</strong> — Raised from 2500 to 200000 so toasts always appear above modals (z-index 10000)</li>
            <li><strong>IMPROVED: Offline Packaging</strong> — Bundled .whl files for all dependencies for air-gapped deployment</li>
            <li><strong>IMPROVED: restart_aegis.sh</strong> — One-click server restart script for macOS</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.8.0 <span class="changelog-date">February 14, 2026</span></h3>
        <p><strong>E2E Audit + Report Fixes + Production Logging</strong></p>
        <ul>
            <li><strong>FIX: Flask Blueprint Import</strong> — data_routes.py used bare app.logger instead of current_app.logger (unavailable in blueprints)</li>
            <li><strong>FIX: Report Download Popup Blocked</strong> — Replaced window.open() after await with hidden iframe approach to avoid Chrome popup blocker</li>
            <li><strong>FIX: Report Generation 500</strong> — catch Exception instead of just ImportError in three report endpoints</li>
            <li><strong>FIX: Generate Reports SQL</strong> — Queries referenced non-existent roles.document_id; now JOINs through document_roles table</li>
            <li><strong>FIX: Roles Studio Empty from Dashboard</strong> — landing-page.js now calls showRolesModal() override instead of generic showModal()</li>
            <li><strong>FIX: CSS Display Conflicts</strong> — Inline style.display conflicts with !important; replaced with classList and removeProperty('display')</li>
            <li><strong>IMPROVED: Production Logging</strong> — Structured error tracking with correlation IDs</li>
            <li><strong>IMPROVED: E2E Audit</strong> — Verified all entry points (sidebar + dashboard tiles) call the same override functions</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.7.0 <span class="changelog-date">February 14, 2026</span></h3>
        <p><strong>Database Access Layer Refactoring + Bug Fixes</strong></p>
        <ul>
            <li><strong>REFACTOR: Database Access Layer</strong> — Replaced 99 scattered sqlite3.connect() calls across 7 files with db_connection() context manager pattern</li>
            <li><strong>NEW: Context Manager</strong> — Auto-commits on success, rolls back on exception, always closes, sets WAL mode uniformly</li>
            <li style="margin-left: 20px;"><em>scan_history.py</em> — 23 calls migrated</li>
            <li style="margin-left: 20px;"><em>app.py</em> — 49 calls migrated</li>
            <li style="margin-left: 20px;"><em>hyperlink_validator/storage.py</em> — 17 calls migrated</li>
            <li style="margin-left: 20px;"><em>document_compare/routes.py</em> — 6 calls migrated</li>
            <li style="margin-left: 20px;"><em>3 other files</em> — 4 calls migrated</li>
            <li><strong>FIX: Connection Leak Risk</strong> — ~65% of DB calls had no finally: conn.close() — context manager guarantees cleanup</li>
            <li><strong>FIX: Missing Error Handling</strong> — ~60% of DB calls lacked exception handling — now all have automatic rollback</li>
            <li><strong>FIX: CSRF Header Typo</strong> — X-CSRFToken corrected to X-CSRF-Token in roles.js and role-source-viewer.js</li>
            <li><strong>FIX: 8 Decompiler Recovery Bugs</strong> — Statement count, compare method, heatmap, graph buttons, reports, hover flicker, Excel export</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.2 <span class="changelog-date">February 13, 2026</span></h3>
        <p><strong>Hyperlink Validator Enhancements</strong></p>
        <ul>
            <li><strong>FEATURE: Deep Validate</strong> — Headless browser rescan now merges recovered URLs back into results, updating stats, filters, and visualizations in real time</li>
            <li><strong>FEATURE: Domain Filter</strong> — Searchable dropdown to filter validation results by specific domain</li>
            <li><strong>FEATURE: Clickable Stat Tiles</strong> — Click any summary stat to filter results to that status category with gold active indicator</li>
            <li><strong>FIX: Export Highlighted</strong> — ArrayBuffer backup ensures DOCX export works when original file blob is unavailable</li>
            <li><strong>FIX: Exclusion Persistence</strong> — Exclusions from result rows now save to database via API, surviving sessions</li>
            <li><strong>FIX: Rescan Eligibility</strong> — Expanded from 3 to 5 statuses (added AUTH_REQUIRED, SSLERROR)</li>
            <li><strong>FIX: History Panel Layout</strong> — Panel no longer compresses HV view on wide displays (uses display:none when closed)</li>
            <li><strong>IMPROVED: Deep Validate UI</strong> — Renamed from "Rescan Blocked", new scan-search icon and purple accent</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.1 <span class="changelog-date">February 13, 2026</span></h3>
        <p><strong>Metrics & Analytics Command Center + Critical Bug Fixes</strong></p>
        <ul>
            <li><strong>FEATURE: Metrics & Analytics Command Center</strong> — Standalone modal with 4-tab layout</li>
            <li style="margin-left: 20px;"><em>Overview Tab</em> - Hero stats, quality trend chart, score distribution, severity breakdown, scan activity heatmap</li>
            <li style="margin-left: 20px;"><em>Quality Tab</em> - Score distribution bars, issue category radar, top issues table</li>
            <li style="margin-left: 20px;"><em>Roles Tab</em> - Role frequency chart, deliverables comparison</li>
            <li style="margin-left: 20px;"><em>Documents Tab</em> - Per-document score history, drill-down panels</li>
            <li><strong>FIX: Scan Cancel Not Working</strong> — Cancel button on Scan Progress Dashboard was disconnected (cancelCurrentJob not exposed)</li>
            <li><strong>FIX: Cancel Leaves UI Hung</strong> — Loading overlay and progress dashboard now properly cleaned up on cancel</li>
            <li><strong>FIX: Wrong Background Behind Modals</strong> — Scan History and Roles Studio now show dashboard behind their backdrop</li>
            <li><strong>FIX: Landing Page Tiles</strong> — Opening modules no longer hides dashboard behind modal</li>
            <li><strong>FIX: Heatmap Hover Flicker</strong> — SVG overlay rendered on top of cells, tooltip shows instantly (no transition)</li>
            <li><strong>BACKEND: Analytics API</strong> — GET /api/metrics/analytics for aggregated scan history data</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.0 <span class="changelog-date">February 12, 2026</span></h3>
        <p><strong>Statement Lifecycle, Bug Fixes & Settings Overhaul</strong></p>
        <ul>
            <li><strong>FEATURE: Statement Lifecycle Management</strong> - Deduplication, review, and cleanup system</li>
            <li style="margin-left: 20px;"><em>Fingerprinting</em> - Statements tagged as new/unchanged on rescan via fingerprint matching</li>
            <li style="margin-left: 20px;"><em>Review Workflow</em> - Approve/reject statements individually or in bulk</li>
            <li style="margin-left: 20px;"><em>Duplicate Cleanup</em> - Find and remove duplicate statement groups</li>
            <li style="margin-left: 20px;"><em>Review Badges</em> - Tool-wide status indicators (Pending/Reviewed/Rejected/Unchanged)</li>
            <li><strong>FEATURE: Role-Statement Responsibility Interface</strong></li>
            <li style="margin-left: 20px;"><em>Role Statements Panel</em> - View all statements for a role, grouped by document (S key in Adjudication)</li>
            <li style="margin-left: 20px;"><em>Bulk Reassign</em> - Select statements and move to a different role</li>
            <li style="margin-left: 20px;"><em>Generic Role Warning</em> - Banner for names like "Personnel" that likely have misassigned statements</li>
            <li style="margin-left: 20px;"><em>Role Autocomplete</em> - Statement edit form includes role autocomplete from adjudication cache</li>
            <li><strong>FIX: Impact Analyzer</strong> - Increased font sizes and padding for readability</li>
            <li><strong>FIX: Factory Reset</strong> - Now clears all tables (was missing function_categories, role_relationships, etc.)</li>
            <li><strong>FIX: Compare Feature</strong> - Added /status endpoint + retry-after-refresh to fix CSRF failures</li>
            <li><strong>FIX: Settings Save UX</strong> - Dirty tracking, pulse animation, unsaved changes warning</li>
            <li><strong>NEW: Data Management</strong> - Clear buttons for statements, role dictionary, and learning data all wired up</li>
            <li><strong>BACKEND: 12 New Endpoints</strong> - Statement review, dedup, role statements, data management</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.2 <span class="changelog-date">February 10, 2026</span></h3>
        <p><strong>Known Issues Cleanup + Scanning Pipeline Audit</strong></p>
        <ul>
            <li><strong>FIX: Quality score N/A</strong> - Frontend used wrong field name (quality_score vs score)</li>
            <li><strong>FIX: .doc files</strong> - Clear error message when LibreOffice unavailable</li>
            <li><strong>FIX: _log() recursion</strong> - Infinite recursion crash when config_logging import fails</li>
            <li><strong>FIX: SessionManager.set()</strong> - Method didn't exist, replaced with update()</li>
            <li><strong>FIX: DoclingAdapter crash</strong> - Null-safe guards for None table headers</li>
            <li><strong>FIX: Missing @app.route</strong> - /api/filter endpoint was unreachable</li>
            <li><strong>FIX: File handle leaks</strong> - html_preview ZIP detection + fitz.Document now use context managers</li>
            <li><strong>FIX: Docling queue race</strong> - Replaced empty()+get_nowait() with get(timeout=2)</li>
            <li><strong>REMOVED: Dead code</strong> - _run_with_timeout() and ThreadPoolExecutor import removed from core.py</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.1 <span class="changelog-date">February 10, 2026</span></h3>
        <p><strong>Relationship Graph Redesign: Edge Bundling + Semantic Zoom</strong></p>
        <ul>
            <li><strong>FEATURE: Standalone Landing Page</strong> - Full-page overlay with particle canvas animation and 9 tool tiles</li>
            <li style="margin-left: 20px;"><em>3x3 Tile Grid</em> - Colored icons, descriptions, live metric badges, drill-down panels</li>
            <li style="margin-left: 20px;"><em>Particle Background</em> - Gold/amber dots with connecting lines on dark background</li>
            <li style="margin-left: 20px;"><em>Metric Count-Up</em> - 6 stat cards with easeOutCubic animation</li>
            <li><strong>FEATURE: Graph Redesign</strong> - Hierarchical Edge Bundling (HEB) as default layout</li>
            <li style="margin-left: 20px;"><em>4 Layout Options</em> - HEB, Force-Directed, Semantic Zoom, Bipartite</li>
            <li style="margin-left: 20px;"><em>Bundling Tension</em> - Adjustable slider for edge curvature</li>
            <li style="margin-left: 20px;"><em>Filter Breadcrumbs</em> - Click nodes to drill-down, back button to navigate up</li>
            <li><strong>IMPROVED: Scanning Pipeline</strong> - Subprocess Docling with 120s timeout, skip >2MB files, fast table 1-2MB</li>
            <li><strong>FIX: Scan History columns</strong> - CSS had 7 widths for 8 columns, added Stmts column width</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.0 <span class="changelog-date">February 9, 2026</span></h3>
        <p><strong>Scan Progress Dashboard, Landing Page & Performance</strong></p>
        <ul>
            <li><strong>FEATURE: Scan Progress Dashboard</strong> - Step-by-step checklist overlay during document review</li>
            <li style="margin-left: 20px;"><em>7 Progress Steps</em> - Upload, Extract, Parse, Quality Checks, NLP, Roles, Finalize</li>
            <li style="margin-left: 20px;"><em>ETA Display</em> - Time remaining estimate based on weighted step progress</li>
            <li style="margin-left: 20px;"><em>Cancel Button</em> - Stop scan in progress</li>
            <li><strong>FIX: 8 Critical Fixes</strong> - Review completion, scan history, CSRF, session management</li>
            <li><strong>FIX: 5 Quick Fixes</strong> - UI polish, error handling, edge cases</li>
            <li><strong>REVERTED: Parallel Checkers</strong> - ThreadPoolExecutor caused deadlocks, back to sequential execution</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.4.0 <span class="changelog-date">February 9, 2026</span></h3>
        <p><strong>Statement Search, Bulk Edit, PDF Viewer & Diff Export</strong></p>
        <ul>
            <li><strong>FEATURE: Statement Quality</strong> - clean_full_text via mammoth eliminates Docling artifacts from Statement Forge extraction</li>
            <li><strong>NEW: Statement Search</strong> - Full-text search across all scans from Statement History overview</li>
            <li style="margin-left: 20px;"><em>Debounced Input</em> - 300ms debounce with directive badge, document name, date, and description excerpt per result</li>
            <li style="margin-left: 20px;"><em>Click-to-Navigate</em> - Click any result to jump to that scan's Document Viewer</li>
            <li><strong>NEW: Bulk Statement Editing</strong> - Multi-select statements and batch update directive/role</li>
            <li style="margin-left: 20px;"><em>Bulk Mode Toggle</em> - Checkbox per statement, count display, Apply/Clear controls</li>
            <li style="margin-left: 20px;"><em>Batch API</em> - PUT /api/scan-history/statements/batch (up to 500 per batch)</li>
            <li><strong>NEW: PDF.js Viewer</strong> - Pixel-perfect PDF canvas rendering in Statement History</li>
            <li style="margin-left: 20px;"><em>HTML/PDF Toggle</em> - Switch between highlighted HTML view and original PDF layout</li>
            <li style="margin-left: 20px;"><em>PDF.js v4.2.67</em> - ESM build with dynamic import and 1.5x canvas scale</li>
            <li><strong>NEW: Statement Diff Export</strong> - Export compare results as CSV or PDF from Compare Viewer</li>
            <li style="margin-left: 20px;"><em>CSV Export</em> - Number, Title, Description, Directive, Role, Level, Diff Status, Changed Fields</li>
            <li style="margin-left: 20px;"><em>PDF Export</em> - AEGIS-branded report with summary stats and color-coded rows</li>
            <li><strong>IMPROVED: Compare Viewer</strong> - State reset prevents stale document cache between viewer sessions</li>
            <li><strong>FIX: Diff Indicators</strong> - Strikethrough no longer inherited by indicator badges in removed highlights</li>
            <li><strong>BACKEND: 5 New Endpoints</strong> - statements/search, statements/batch, document-file, export-csv, export-pdf</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.3.0 <span class="changelog-date">February 9, 2026</span></h3>
        <p><strong>Document Extraction Overhaul — mammoth + pymupdf4llm</strong></p>
        <ul>
            <li><strong>NEW: mammoth DOCX Extraction</strong> - MammothDocumentExtractor converts .docx to clean semantic HTML with proper tables, headings, bold/italic</li>
            <li style="margin-left: 20px;"><em>Clean Text</em> - No more pipe characters or dash artifacts from table formatting</li>
            <li style="margin-left: 20px;"><em>HTML Preview</em> - html_preview stored with every scan for rich document rendering</li>
            <li><strong>NEW: pymupdf4llm PDF Extraction</strong> - Pymupdf4llmExtractor converts PDF to structured Markdown with heading detection and tables</li>
            <li><strong>NEW: HTML Document Viewer</strong> - Statement History renders documents as formatted HTML with proper tables, headings, and text styling</li>
            <li style="margin-left: 20px;"><em>DOM-Based Highlighting</em> - Text node walking replaces string-index matching for accurate statement highlights in HTML</li>
            <li style="margin-left: 20px;"><em>Cross-Extractor Matching</em> - normalizeForMatch() strips formatting artifacts for reliable highlighting across extraction engines</li>
            <li style="margin-left: 20px;"><em>3-Strategy Matching</em> - Exact substring, normalized position mapping, and word-sequence fuzzy matching</li>
            <li style="margin-left: 20px;"><em>Backward Compatible</em> - Old scans without html_preview fall back to plain-text highlighting</li>
            <li><strong>NEW: AEGIS Installer</strong> - Install_AEGIS.bat with user-selectable install location (default C:\\AEGIS)</li>
            <li style="margin-left: 20px;"><em>7-Step Process</em> - Python check, location prompt, file copy, dependency install, NLP install, launcher creation, cleanup</li>
            <li style="margin-left: 20px;"><em>Launchers</em> - Creates Start_AEGIS.bat and Stop_AEGIS.bat at install root</li>
            <li><strong>NEW: Distribution Packaging</strong> - AEGIS_Distribution package with mammoth wheel bundling for offline deployment</li>
            <li><strong>IMPROVED: Extraction Fallback Chain</strong> - Docling → mammoth/pymupdf4llm → legacy extractors with automatic html_preview generation for all paths</li>
            <li><strong>FIX: lxml Import</strong> - Corrected lxml.etree vs lxml.html import in HTML parser</li>
            <li><strong>FIX: html_preview for Docling Path</strong> - Post-extraction mammoth call ensures html_preview even when Docling is primary</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.2.0 <span class="changelog-date">February 9, 2026</span></h3>
        <p><strong>Statement Forge History — Persistent Statements & Document Viewer</strong></p>
        <ul>
            <li><strong>NEW: Statement History</strong> - Track extracted statements across all scans of a document</li>
            <li style="margin-left: 20px;"><em>Overview Dashboard</em> - Stat cards, trend chart, directive donut, scan timeline</li>
            <li style="margin-left: 20px;"><em>Document Viewer</em> - Split-panel with highlighted source text and statement detail</li>
            <li style="margin-left: 20px;"><em>Unified Compare</em> - Single-document diff view with added/removed/modified/unchanged highlights</li>
            <li><strong>NEW: Highlight-to-Create</strong> - Select text in document to create new statements with auto-detected directive</li>
            <li><strong>NEW: Two-Tier Fingerprint Matching</strong> - desc_fp + full_fp for accurate modified detection in comparisons</li>
            <li><strong>NEW: Dual Filter System</strong> - Directive chips + diff status chips that combine for precise filtering</li>
            <li><strong>NEW: Field-Level Diff</strong> - Modified statements show old → new for changed fields</li>
            <li><strong>NEW: Overlapping Highlight Merging</strong> - Multiple statements sharing text use data-stmt-indices attribute</li>
            <li><strong>NEW: Keyboard Navigation</strong> - Arrow keys, a/r/m for diff categories, e to edit, Esc to close</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.1.0 <span class="changelog-date">February 9, 2026</span></h3>
        <p><strong>Nimbus SIPOC Import & Role Inheritance Map</strong></p>
        <ul>
            <li><strong>NEW: Nimbus SIPOC Import</strong> - 5-step wizard with dual-mode parsing (hierarchy vs process) and auto-fallback</li>
            <li><strong>NEW: Role Inheritance Map</strong> - Interactive HTML export with 4 views: Dashboard, Tree, Graph, Table</li>
            <li style="margin-left: 20px;"><em>Inline Editing</em> - Edit role fields in exported HTML, track changes, export diffs as JSON</li>
            <li style="margin-left: 20px;"><em>Graph Animations</em> - Staggered card entrance, SVG node bounce, arrow draw-in</li>
            <li><strong>NEW: Role Import Template</strong> - Download and fill Excel template for bulk role import</li>
            <li><strong>IMPROVED: Batch Adjudicate</strong> - Extended to handle role_type, disposition, org_group, hierarchy_level, baselined, aliases</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.5 <span class="changelog-date">February 8, 2026</span></h3>
        <p><strong>Role Dictionary Complete Overhaul</strong></p>
        <ul>
            <li><strong>NEW: Dictionary Dashboard</strong> - 4 stat tiles, category donut chart, source bars, top categories</li>
            <li><strong>NEW: Card View</strong> - Rich cards with adjudication colors, hover actions, description excerpts</li>
            <li><strong>NEW: Bulk Operations</strong> - Select-all, batch activate/deactivate/delete/set-category/mark-deliverable</li>
            <li><strong>NEW: Inline Quick Actions</strong> - Click category badge to change, star toggle, name copy, role clone</li>
            <li><strong>NEW: Keyboard Navigation</strong> - j/k navigate, Enter edit, Space select, T toggle view, / search</li>
            <li><strong>NEW: Enhanced Filtering</strong> - Adjudication status, has description, has tags filters</li>
            <li><strong>NEW: Duplicate Detection</strong> - Warns on save when similar names or alias matches found</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.4 <span class="changelog-date">February 8, 2026</span></h3>
        <p><strong>Import Enhancements & PDF Export</strong></p>
        <ul>
            <li><strong>NEW: Diff Preview</strong> - Preview modal before import shows new/changed/unchanged roles</li>
            <li><strong>NEW: Package Versioning</strong> - Warns when importing from newer AEGIS version</li>
            <li><strong>NEW: PDF Report</strong> - AEGIS-branded adjudication report via reportlab</li>
            <li><strong>IMPROVED: Import Progress</strong> - Spinner overlay during imports</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.3 <span class="changelog-date">February 8, 2026</span></h3>
        <p><strong>Adjudication Tab Complete Overhaul + Global Badges</strong></p>
        <ul>
            <li><strong>NEW: Global Adjudication Badges</strong> - Tool-wide badges (✓/★/✗) on all role displays across every tab and view</li>
            <li style="margin-left: 20px;"><em>Badge Types</em> - ✓ Adjudicated (green), ★ Deliverable (gold), ✗ Rejected (red)</li>
            <li style="margin-left: 20px;"><em>Coverage</em> - Roles Studio, Data Explorer, Role-Doc Matrix, RACI Matrix, Role Details</li>
            <li style="margin-left: 20px;"><em>Utility</em> - AEGIS.AdjudicationLookup global JS utility with caching and badge HTML generation</li>
            <li><strong>IMPROVED: Adjudication Stats</strong> - Green subtitle under Unique Roles tile instead of separate stat tile</li>
            <li><strong>FIX: Dark Mode CSS</strong> - Critical fix: dark-mode.css was not loading due to CSS @import ordering violation</li>
            <li><strong>FIX: Donut Chart Centering</strong> - "3 Categories" center text properly aligned in Data Explorer donut chart</li>
            <li><strong>OVERHAUL: Adjudication Tab</strong> - Complete rewrite with dashboard, kanban view, and auto-classify</li>
            <li><strong>NEW: Auto-Classify</strong> - AI-assisted role classification with pattern matching and confidence scoring</li>
            <li><strong>NEW: Kanban Board</strong> - Drag-and-drop board with Pending/Confirmed/Deliverable/Rejected columns</li>
            <li><strong>NEW: Confidence Gauges</strong> - SVG ring indicators showing classification confidence per role</li>
            <li><strong>NEW: Function Tag Pills</strong> - Assign hierarchical function categories directly on role cards</li>
            <li><strong>NEW: Keyboard Navigation</strong> - Arrow keys, C/D/R to classify, Ctrl+Z undo, Ctrl+Y redo</li>
            <li><strong>NEW: Undo/Redo</strong> - Full action history with toolbar buttons and keyboard shortcuts</li>
            <li><strong>NEW: Batch Operations</strong> - Select multiple roles and bulk confirm/reject/deliverable</li>
            <li><strong>NEW: Source Viewer Tags</strong> - Function tag section in Role Source Viewer with add/remove and custom tag creation</li>
            <li><strong>FIX: CSRF Token Sync</strong> - Token synced between page load and fetch sessions for reliable POST requests</li>
            <li><strong>FIX: Session Persistence</strong> - Persistent secret key and Secure cookie flag fix for localhost</li>
            <li><strong>FIX: Kanban Toggle</strong> - View toggle now properly shows/hides list and board containers</li>
            <li><strong>BACKEND: Auto-adjudicate API</strong> - Pattern-based classification with deliverable detection</li>
            <li><strong>BACKEND: Batch adjudicate API</strong> - Process multiple roles in single transaction</li>
            <li><strong>NEW: Interactive HTML Export</strong> - Export adjudication as standalone HTML kanban board for offline team review</li>
            <li style="margin-left: 20px;"><em>Features</em> - Drag-drop, function tag assignment, category editing, notes, search/filter</li>
            <li style="margin-left: 20px;"><em>Import</em> - Generate JSON import file from HTML board, import back into AEGIS</li>
            <li><strong>NEW: Roles Sharing</strong> - Share role dictionaries with team members</li>
            <li style="margin-left: 20px;"><em>Shared Folder</em> - Export master dictionary with function tags to shared network path</li>
            <li style="margin-left: 20px;"><em>Email Package</em> - Download .aegis-roles package and open mailto: with instructions</li>
            <li style="margin-left: 20px;"><em>Import Package</em> - Import .aegis-roles from Settings or updates/ folder</li>
            <li><strong>NEW: Export Dropdown</strong> - CSV, Interactive HTML Board, and Import Decisions options</li>
            <li><strong>IMPROVED: Master File</strong> - Export/import now includes function_tags per role</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.2 <span class="changelog-date">February 7, 2026</span></h3>
        <p><strong>Roles Studio UI Enhancements & RACI Fix</strong></p>
        <ul>
            <li><strong>FIX: Role Source Viewer Dark Mode</strong> - Complete dark mode support for readability</li>
            <li style="margin-left: 20px;"><em>Document Text</em> - Light text (#e0e0e0) on dark background for readability</li>
            <li style="margin-left: 20px;"><em>All Panels</em> - Headers, footers, details panel styled for dark mode</li>
            <li style="margin-left: 20px;"><em>Role Highlights</em> - Amber gradient overlays visible in dark mode</li>
            <li style="margin-left: 20px;"><em>Form Controls</em> - Buttons, selects, inputs all have dark mode styling</li>
            <li><strong>FIX: RACI Matrix Deduplication</strong> - Totals now match Overview's responsibility count</li>
            <li style="margin-left: 20px;"><em>Before</em> - RACI showed 406 (counting duplicates across documents)</li>
            <li style="margin-left: 20px;"><em>After</em> - RACI shows ~297 (matching Overview's 298 unique responsibilities)</li>
            <li><strong>NEW: Role Details Explore Button</strong> - Icon to open role in Data Explorer</li>
            <li style="margin-left: 20px;"><em>Magnifying glass + plus</em> - Visible icon replaces double-click behavior</li>
            <li style="margin-left: 20px;"><em>Direct navigation</em> - Opens Data Explorer focused on selected role</li>
        </ul>
        <div class="changelog-note">
            <strong>Tip:</strong> Click the explore icon (🔍+) on any role card in Role Details to see full analytics in Data Explorer.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v4.0.1 <span class="changelog-date">February 4, 2026</span></h3>
        <p><strong>Role Extraction Accuracy Enhancement - 99%+ Recall</strong></p>
        <ul>
            <li><strong>MAJOR: Role Extractor v3.3.x</strong> - Comprehensive accuracy improvements achieving 99%+ recall</li>
            <li style="margin-left: 20px;"><em>Original Documents</em> - FAA, OSHA, Stanford: 103% average recall</li>
            <li style="margin-left: 20px;"><em>Defense/Government</em> - MIL-STD, NIST, NASA: 99.5% average recall</li>
            <li style="margin-left: 20px;"><em>Aerospace</em> - NASA, FAA, KSC: 99.0% average recall</li>
            <li><strong>v3.3.0</strong> - Added ~40 new roles (worker terms, academic roles)</li>
            <li><strong>v3.3.1</strong> - Added ~25 entries to FALSE_POSITIVES (safety concepts, document references)</li>
            <li><strong>v3.3.2</strong> - Added ~30 defense-specific roles (contracting officer, prime contractor, etc.)</li>
            <li><strong>v3.3.3</strong> - Added aerospace/aviation terms (lead, pilot, engineer)</li>
            <li><strong>NEW: Test Scripts</strong> - manual_role_analysis.py, defense_role_analysis.py, aerospace_role_analysis.py</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> Role extraction now validated on FAA, NASA, MIL-STD, NIST, OSHA, and academic documents.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v4.0.0 <span class="changelog-date">February 4, 2026</span></h3>
        <p><strong>AEGIS Rebrand Release</strong></p>
        <ul>
            <li><strong>REBRAND: TechWriterReview → AEGIS</strong> - Aerospace Engineering Governance & Inspection System</li>
            <li style="margin-left: 20px;"><em>New Logo</em> - AEGIS shield with gold/bronze gradient</li>
            <li style="margin-left: 20px;"><em>Color Scheme</em> - Gold accent palette throughout UI</li>
            <li style="margin-left: 20px;"><em>163+ Files</em> - Updated across codebase with new branding</li>
            <li><strong>UI: Document Text Readability</strong> - Enhanced font sizing (15px), line-height (1.75)</li>
            <li><strong>UI: Navigation Tab Order</strong> - Validate and Links tabs now adjacent</li>
            <li><strong>FIX: GRM002 (Capitalize I)</strong> - Fixed false positives matching 'i' inside words</li>
            <li><strong>FIX: Punctuation Checker</strong> - Filters TOC/table of contents entries</li>
            <li><strong>FIX: Prose Linter</strong> - Nominalization exceptions for 40+ technical terms</li>
            <li><strong>FIX: Passive Checker</strong> - Added 60+ adjectival participles</li>
            <li><strong>NEW: Data Management Tab</strong> - Clear Scan History, Role Dictionary, Learning Data, Factory Reset</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> All 325+ tests passing. Version expectations updated throughout test suite.
        </div>
    </div>
    <div class="changelog-version">
        <h3>v3.4.5 <span class="changelog-date">February 4, 2026</span></h3>
        <p><strong>Checker UI & Style Presets</strong></p>
        <ul>
            <li><strong>UI: Checker Checkboxes</strong> - Added 23 new v3.4.0 checker checkboxes to Settings > Document Profiles</li>
            <li><strong>UI: Checker Categories</strong> - Readability, Procedural Writing, Product & Code, Standards & Compliance</li>
            <li><strong>UI: Style Guide Presets</strong> - Preset selector in Settings > Review Options (8 presets)</li>
            <li><strong>NEW: style-presets.js</strong> - Preset UI module with localStorage persistence</li>
            <li><strong>NEW: Performance Benchmarks</strong> - test_checker_performance.py for 84 checkers</li>
            <li><strong>FIX: BUG-M09</strong> - Hyperlink validator HTML export properly handles undefined values</li>
            <li><strong>VERIFIED: 84 Checkers</strong> - All registered and available for document analysis</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.4 <span class="changelog-date">February 4, 2026</span></h3>
        <p><strong>Universal Acronym Database</strong></p>
        <ul>
            <li><strong>DATABASE: 1,767 Acronyms</strong> - universal_acronyms.json from UK MOJ, DOD, FDA, IEEE/ISO/ANSI sources</li>
            <li><strong>IMPROVED: Acronym Checker v4.6.0</strong> - Loads external database, auto-skips well-known acronyms in permissive mode</li>
            <li><strong>OFFLINE</strong> - All acronyms available offline for air-gapped deployments</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.3 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Batch Accuracy Testing</strong></p>
        <ul>
            <li><strong>ACCURACY</strong> - Comprehensive batch testing across 10+ document types</li>
            <li><strong>IMPROVED: Acronym Checker v4.5.2</strong> - ALL CAPS sentence detection, 50+ regulatory acronyms, 30+ engineering acronyms</li>
            <li><strong>IMPROVED: Grammar Checker v2.6.2</strong> - 60+ common ALL CAPS words, reduced passive voice false positives</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.2 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>False Positive Reduction</strong></p>
        <ul>
            <li><strong>ACCURACY</strong> - 40%+ reduction in acronym false positives</li>
            <li><strong>IMPROVED: Acronym Checker v4.5.1</strong> - Section references (A1, B2) no longer flagged, 80+ domain skip words</li>
            <li><strong>IMPROVED: Grammar Checker v2.6.1</strong> - 50+ technical/SOP terms added to passive voice false positives</li>
            <li><strong>FIX</strong> - Phantom passive voice detections eliminated (are prohibited, must be contacted, etc.)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.1 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Style Guide Presets, CLI Mode & Auto-Fix Engine</strong></p>
        <ul>
            <li><strong>NEW: Style Guide Presets</strong> - One-click configuration for Microsoft, Google, Plain Language, ASD-STE100, Government, Aerospace</li>
            <li><strong>NEW: Full CLI Mode</strong> - Run all 84 checkers from command line (python -m AEGIS document.docx)</li>
            <li style="margin-left: 20px;"><em>Batch Processing</em> - --batch, --preset, --format (json/csv/xlsx/text) flags</li>
            <li><strong>NEW: Auto-Fix Engine</strong> - Fix generators for Latin abbreviations, contractions, wordy phrases, product names</li>
            <li><strong>NEW: ASD-STE100 Words</strong> - 875 approved words and writing rules database</li>
            <li><strong>NEW: Preset API</strong> - /api/presets, /api/presets/&lt;name&gt;, /api/auto-fix/preview</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.4.0 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Maximum Coverage Suite - 23 New Offline-Only Checkers</strong></p>
        <ul>
            <li><strong>NEW: Style Consistency Checkers (6)</strong></li>
            <li style="margin-left: 20px;"><em>HeadingCaseConsistencyChecker</em> - Validates heading capitalization consistency</li>
            <li style="margin-left: 20px;"><em>ContractionConsistencyChecker</em> - Detects mixed contraction usage</li>
            <li style="margin-left: 20px;"><em>OxfordCommaConsistencyChecker</em> - Validates serial comma consistency</li>
            <li style="margin-left: 20px;"><em>ARIProminenceChecker</em> - Automated Readability Index assessment</li>
            <li style="margin-left: 20px;"><em>SpacheReadabilityChecker</em> - Spache formula for basic audiences</li>
            <li style="margin-left: 20px;"><em>DaleChallEnhancedChecker</em> - Enhanced Dale-Chall with 3000-word list</li>
            <li><strong>NEW: Clarity Checkers (5)</strong></li>
            <li style="margin-left: 20px;"><em>FutureTenseChecker</em> - Flags "will display" patterns</li>
            <li style="margin-left: 20px;"><em>LatinAbbreviationChecker</em> - Warns about i.e., e.g., etc.</li>
            <li style="margin-left: 20px;"><em>SentenceInitialConjunctionChecker</em> - Flags And, But, So at sentence start</li>
            <li style="margin-left: 20px;"><em>DirectionalLanguageChecker</em> - Flags above/below/left/right</li>
            <li style="margin-left: 20px;"><em>TimeSensitiveLanguageChecker</em> - Flags currently/now/recently</li>
            <li><strong>NEW: Enhanced Acronym Checkers (2)</strong></li>
            <li style="margin-left: 20px;"><em>AcronymFirstUseChecker</em> - Enforces definition on first use</li>
            <li style="margin-left: 20px;"><em>AcronymMultipleDefinitionChecker</em> - Flags acronyms defined multiple times</li>
            <li><strong>NEW: Procedural Writing Checkers (3)</strong></li>
            <li style="margin-left: 20px;"><em>ImperativeMoodChecker</em> - Validates procedures use imperative mood</li>
            <li style="margin-left: 20px;"><em>SecondPersonChecker</em> - Prefers "you" over "the user"</li>
            <li style="margin-left: 20px;"><em>LinkTextQualityChecker</em> - Flags "click here" and vague link text</li>
            <li><strong>NEW: Document Quality Checkers (4)</strong></li>
            <li style="margin-left: 20px;"><em>NumberedListSequenceChecker</em> - Validates 1, 2, 3 not 1, 2, 4</li>
            <li style="margin-left: 20px;"><em>ProductNameConsistencyChecker</em> - Validates JavaScript not Javascript</li>
            <li style="margin-left: 20px;"><em>CrossReferenceTargetChecker</em> - Validates Table 5 exists</li>
            <li style="margin-left: 20px;"><em>CodeFormattingConsistencyChecker</em> - Flags unformatted code</li>
            <li><strong>NEW: Compliance Checkers (3)</strong></li>
            <li style="margin-left: 20px;"><em>MILStd40051Checker</em> - MIL-STD-40051-2 technical manual compliance</li>
            <li style="margin-left: 20px;"><em>S1000DBasicChecker</em> - S1000D/IETM structural validation</li>
            <li style="margin-left: 20px;"><em>AS9100DocChecker</em> - AS9100D documentation requirements</li>
            <li><strong>NEW: Data Files</strong> - Dale-Chall 3000 words, Spache easy words, 250+ product names, compliance patterns</li>
            <li><strong>TOTAL: 84 Checkers</strong> - (61 existing + 23 new)</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> All new checkers are 100% offline-capable for air-gapped deployment. 42 new unit tests added.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.3.0 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Maximum Accuracy NLP Enhancement Suite</strong></p>
        <ul>
            <li><strong>NEW: Technical Dictionary System</strong> - Master dictionary with 10,000+ embedded terms</li>
            <li style="margin-left: 20px;"><em>Aerospace/Defense</em> - 1,200+ terms</li>
            <li style="margin-left: 20px;"><em>Medical/Pharma</em> - 800+ terms</li>
            <li style="margin-left: 20px;"><em>Legal/Compliance</em> - 600+ terms</li>
            <li style="margin-left: 20px;"><em>Software/IT</em> - 1,500+ terms</li>
            <li><strong>NEW: spaCy NLP Pipeline</strong> - Named Entity Recognition for role extraction</li>
            <li><strong>NEW: Hybrid Role Extraction</strong> - Combined NLP + pattern matching</li>
            <li><strong>NEW: Fuzzy Matching</strong> - rapidfuzz library for acronym detection</li>
            <li><strong>NEW: Context Analysis</strong> - Sentence-level analysis for acronym suggestions</li>
            <li><strong>IMPROVED: Role Extractor v3</strong> - 228+ pre-defined roles with 192+ false positive exclusions</li>
            <li><strong>IMPROVED: Acronym Detector</strong> - 95%+ precision with context-aware filtering</li>
            <li><strong>100% Offline</strong> - All NLP models run locally for air-gapped environments</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> Install via setup.bat for full NLP capabilities. Graceful fallback to pattern-only mode if libraries unavailable.
        </div>
    </div>
    <div class="changelog-version">
        <h3>v3.2.5 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Role Extraction Accuracy Improvements</strong></p>
        <ul>
            <li><strong>IMPROVED: Role Extraction Filters</strong> - Phone numbers, digit-starting candidates, ZIP codes, run-together words, slash alternatives, section headers, address patterns</li>
            <li><strong>NEW: Domain Roles</strong> - 25+ FAA/Aviation roles, 25+ OSHA/Safety roles</li>
            <li><strong>IMPROVED: Acronym Extraction</strong> - Parenthetical acronyms captured alongside roles (e.g., Project Manager (PM))</li>
            <li><strong>ACCURACY</strong> - False positives reduced by 78%, accuracy improved from 36.7% to 56.7%</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.4 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Enhanced spaCy NLP & New Analyzers</strong></p>
        <ul>
            <li><strong>IMPROVED: spaCy Integration</strong> - NLPProcessor v1.1.0 with compound noun detection, role-verb association, confidence scoring</li>
            <li><strong>NEW: 5 Analyzers</strong> - Semantic similarity, acronym extraction (Schwartz-Hearst), prose linter, structure analysis, text statistics</li>
            <li><strong>NEW: API Endpoints</strong> - /api/analyzers/* for similarity, acronyms, statistics, lint, and status</li>
            <li><strong>NEW: Vocabulary Metrics</strong> - TTR, Hapax Legomena, Yule's K, TF-IDF keyword extraction</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.3 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Bug Fixes — HTML Export & Soft 404</strong></p>
        <ul>
            <li><strong>FIX: BUG-M09</strong> - HTML export properly escapes URLs and handles None values</li>
            <li><strong>FIX: BUG-M07</strong> - Soft 404 detection less aggressive</li>
            <li><strong>FIX: BUG-M23</strong> - Version numbers synchronized across all UI components</li>
            <li><strong>FIX: BUG-M26/M25</strong> - Troubleshooting panel duplicate IDs and export buttons fixed</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.2 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Adjudication Persistence Fixes</strong></p>
        <ul>
            <li><strong>FIX: Adjudication Save</strong> - Roles properly saved to dictionary via primary and backup API paths</li>
            <li><strong>FIX: Pending List</strong> - Adjudicated roles removed from pending list, refreshes correctly</li>
            <li><strong>FIX: Dictionary UI</strong> - Delete button icon, action button styling, status badges fixed</li>
            <li><strong>NEW: Backup Save</strong> - Fallback to /api/roles/dictionary if primary endpoint fails</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.1 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Per-Role Adjudication & Learning</strong></p>
        <ul>
            <li><strong>FIX: Adjudication Persistence</strong> - Each role now tracks its own adjudication state independently</li>
            <li><strong>NEW: API Endpoints</strong> - /api/roles/adjudicate, /api/roles/adjudication-status, /api/roles/update-category</li>
            <li><strong>NEW: Extraction Learning</strong> - Rejected roles added to false_positives, confirmed roles added to known_roles</li>
            <li><strong>IMPROVED: Source Viewer</strong> - Adjudication panel resets when opening new role</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.2.0 <span class="changelog-date">February 3, 2026</span></h3>
        <p><strong>Role Source Viewer with Adjudication Controls</strong></p>
        <ul>
            <li><strong>FEATURE: Role Source Viewer</strong> - View actual document text with highlighted role mentions</li>
            <li style="margin-left: 20px;"><em>Full Document Display</em> - Complete text with all mentions highlighted in orange</li>
            <li style="margin-left: 20px;"><em>Multi-Document Navigation</em> - Switch between documents where role appears</li>
            <li style="margin-left: 20px;"><em>Occurrence Navigation</em> - Prev/Next buttons and click-to-jump</li>
            <li><strong>FEATURE: Adjudication Panel</strong> - Make informed decisions with full context</li>
            <li style="margin-left: 20px;"><em>Three Actions</em> - Confirm Role (green), Mark Deliverable (blue), Reject (red)</li>
            <li style="margin-left: 20px;"><em>Status Badges</em> - Pending, Confirmed, Deliverable, Rejected states</li>
            <li style="margin-left: 20px;"><em>Category Classification</em> - Role, Management, Technical, Organization, Custom</li>
            <li style="margin-left: 20px;"><em>Notes Field</em> - Add comments to adjudication decisions</li>
            <li><strong>NEW: API Endpoint</strong> - /api/scan-history/document-text for historical document retrieval</li>
            <li><strong>FIX: Document Compare Modal</strong> - Now properly sized at 95vw × 90vh</li>
            <li><strong>IMPROVED: Cache Management</strong> - Versioned script loading for reliable updates</li>
        </ul>
        <div class="changelog-note">
            <strong>Tip:</strong> Click any role name in Roles Studio to open the Source Viewer and see the actual context.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.1.9 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>Molten Progress Bar System</strong></p>
        <ul>
            <li><strong>FEATURE: Molten Progress Bars</strong> - Scalable Rive-inspired progress bars</li>
            <li style="margin-left: 20px;"><em>4 Size Variants</em> - Mini (4px), Small (8px), Medium (16px), Large (28px)</li>
            <li style="margin-left: 20px;"><em>3 Color Themes</em> - Orange, Blue, Green with molten gradients</li>
            <li style="margin-left: 20px;"><em>Optional Effects</em> - Reflection glow, trailing effect, indeterminate mode</li>
            <li><strong>INTEGRATED</strong> - Batch rows (mini), Loading overlay (medium), Hyperlink validator (small), Cinematic modal (small)</li>
            <li><strong>FIX: AEGIS Loader</strong> - No longer blocks clicks after fade-out (pointer-events fix)</li>
            <li><strong>REMOVED: Initial Startup Loader</strong> - App loads fast enough without it</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.8 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>AEGIS Cinematic Loader</strong></p>
        <ul>
            <li><strong>NEW: Full-Screen Startup Animation</strong> - Cinematic 28px progress bar with glow effects and particle background</li>
            <li><strong>NEW: Visual Effects</strong> - Blue/gold color scheme, grid overlay, sheen sweep, progress orb with trailing glow</li>
            <li><strong>NEW: Film Grain</strong> - Cinematic vignette and film grain overlays for premium feel</li>
            <li><strong>IMPROVED: Boot Sequence</strong> - Real-time progress stages during app initialization</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.7 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>Cinematic Progress — Major Visual Upgrade</strong></p>
        <ul>
            <li><strong>NEW: Particle Effects</strong> - Trails, connections, milestone celebrations with burst effects</li>
            <li><strong>NEW: Theme Enhancements</strong> - Lightning bolts (Circuit), twinkling stars (Cosmic), rising embers (Fire)</li>
            <li><strong>NEW: Grand Finale</strong> - 80-particle explosion at 100% with container pulse</li>
            <li><strong>IMPROVED: Matrix Theme</strong> - Faster streams with depth effect and full katakana character set</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.6 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>Cinematic Progress Animation System</strong></p>
        <ul>
            <li><strong>NEW: 5 Cinematic Themes</strong> - Circuit (orange), Cosmic (purple), Matrix (green), Energy (teal), Fire (red)</li>
            <li><strong>NEW: Particle System</strong> - 150+ animated particles with theme-specific behaviors</li>
            <li><strong>NEW: Energy Trail</strong> - Follows progress bar with glowing path and matrix data streams</li>
            <li><strong>ADDED: GSAP + Rive</strong> - Animation libraries for Lottie + Canvas integration</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.5 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>Circuit Board Batch Progress</strong></p>
        <ul>
            <li><strong>NEW: Batch Progress Display</strong> - Circuit board themed with dark navy/orange glow effects</li>
            <li><strong>NEW: Time Tracking</strong> - Elapsed time, estimated remaining, processing speed displays</li>
            <li><strong>NEW: Per-Document Status</strong> - Real-time labels (QUEUED → UPLOADING → ANALYZING → DONE)</li>
            <li><strong>FIX: Dual File Dialog</strong> - Select Files/Select Folder no longer trigger both dialogs</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.1.4 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>ENH-010: Clean Upgrade Path</strong></p>
        <ul>
            <li><strong>FEATURE: User Data Preservation</strong> - Automatic backup/restore of user data during upgrades</li>
            <li><strong>FEATURE: Version Comparison</strong> - Compare installed version with update packages (.zip)</li>
            <li><strong>FEATURE: Update Package Support</strong> - Apply full version updates from .zip files with data preservation</li>
            <li><strong>NEW: API Endpoints</strong> - /api/updates/version, /check-package, /backup-userdata, /restore-userdata, /apply-package</li>
            <li><strong>NEW: USER_DATA_PATHS</strong> - Configurable list of files to preserve (scan_history.db, settings, dictionaries)</li>
            <li><strong>NEW: Rollback on Failure</strong> - Automatic rollback if upgrade fails</li>
            <li><strong>IMPROVED: Update Manager</strong> - Enhanced to v1.5 with ENH-010 features</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> Test suite expanded to 75 tests - all passing.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.1.3 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>ENH-005, ENH-006, ENH-009: Role Viewer, Statement Review, Diagnostics</strong></p>
        <ul>
            <li><strong>FEATURE: Universal Role Source Viewer (ENH-005)</strong> - View role context in source documents from any location</li>
            <li style="margin-left: 20px;"><em>Modal-based viewer</em> - Multi-document navigation with Previous/Next</li>
            <li style="margin-left: 20px;"><em>Multi-occurrence support</em> - Navigate through all occurrences in documents</li>
            <li style="margin-left: 20px;"><em>Context highlighting</em> - View surrounding text for context</li>
            <li><strong>FEATURE: Statement Forge Review Mode (ENH-006)</strong> - Review statements with source context</li>
            <li style="margin-left: 20px;"><em>Statement navigation</em> - Previous/Next with keyboard shortcuts</li>
            <li style="margin-left: 20px;"><em>Review actions</em> - Approve, Reject, Save with keyboard support (A/R/S)</li>
            <li style="margin-left: 20px;"><em>Create from selection</em> - Highlight text to create new statements</li>
            <li><strong>FEATURE: Comprehensive Logging (ENH-009)</strong> - Diagnostics without performance degradation</li>
            <li style="margin-left: 20px;"><em>Backend: diagnostics.py</em> - CircularLogBuffer, AsyncLogQueue, SamplingLogger</li>
            <li style="margin-left: 20px;"><em>Frontend: frontend-logger.js</em> - API call timing, action tracking, backend sync</li>
            <li><strong>NEW: Statement Model Extended</strong> - Source context fields (document, char offsets, page, section)</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> Test suite expanded to 68 tests - all passing.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.1.2 <span class="changelog-date">February 2, 2026</span></h3>
        <p><strong>Comprehensive Bug Fixes & Core Enhancements</strong></p>
        <ul>
            <li><strong>FEATURE: NLP Integration (ENH-008)</strong> - spaCy-based role/deliverable/acronym extraction</li>
            <li><strong>FEATURE: Role Comparison (ENH-004)</strong> - Multi-document side-by-side role analysis</li>
            <li><strong>FEATURE: Graph Export (ENH-003)</strong> - PNG/SVG export for Chart.js and D3.js visualizations</li>
            <li><strong>FEATURE: Role Consolidation (ENH-001)</strong> - 25+ built-in rules, fuzzy matching, abbreviations</li>
            <li><strong>FIX: Passive Voice (BUG-C01)</strong> - Expanded FALSE_POSITIVES from ~38 to 300+ technical terms</li>
            <li><strong>FIX: Dark Mode</strong> - Carousel and heatmap styling improvements</li>
            <li><strong>FIX: Performance</strong> - Poll frequency, passive listeners, AbortController timeouts</li>
            <li><strong>FIX: CSP Compliance</strong> - SortableJS now loaded locally</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> All critical and medium-priority bugs resolved. 48 tests passing.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.122 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Persistent Link Exclusions & Scan History</strong></p>
        <ul>
            <li><strong>FEATURE: Persistent Link Exclusions</strong> - URL exclusion rules now stored in SQLite database (survive sessions)</li>
            <li><strong>FEATURE: Scan History Storage</strong> - Historical hyperlink scans recorded with summary statistics</li>
            <li><strong>NEW: Link History Modal</strong> - New "Links" button in top navigation opens modal with two tabs:</li>
            <li style="margin-left: 20px;"><em>Exclusions Tab</em> - Add, edit, enable/disable, and delete URL exclusion patterns</li>
            <li style="margin-left: 20px;"><em>Scans Tab</em> - View historical scans, see details, clear old records</li>
            <li><strong>NEW: API Endpoints</strong> - /api/hyperlink-validator/exclusions/* and /history/* for CRUD operations</li>
            <li><strong>NEW: Match Types</strong> - Supports contains, exact, prefix, suffix, and regex pattern matching</li>
            <li><strong>IMPROVED: State Management</strong> - HyperlinkValidatorState loads exclusions from database on init</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.121 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Portfolio Fix & Hyperlink Enhancements</strong></p>
        <ul>
            <li><strong>FIX: Portfolio "Open in Review"</strong> - Button now correctly loads documents with stats bar, analytics, and issues table displaying properly</li>
            <li><strong>IMPROVED: Responsive Hyperlinks Panel</strong> - Changed from fixed heights (300px/150px) to viewport-relative (50vh/25vh)</li>
            <li><strong>IMPROVED: Clickable Hyperlinks</strong> - Users can now click any hyperlink row to open URL in new tab for manual verification</li>
            <li><strong>NEW: Visual Hover Feedback</strong> - External-link icon appears on hover for hyperlink rows</li>
            <li><strong>NEW: Test Document</strong> - hyperlink_test.docx with working and broken link examples</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.120 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>3D Carousel for Issues by Section</strong></p>
        <ul>
            <li><strong>FEATURE: 3D Carousel</strong> - New rotating carousel view for "Issues by Section" in Document Analytics</li>
            <li><strong>NEW: Drag-to-Spin</strong> - Continuous rotation while dragging, plus slider navigation</li>
            <li><strong>NEW: Click-to-Filter</strong> - Click on a carousel box to filter issues to that section</li>
            <li><strong>NEW: Density Coloring</strong> - Color-coded borders based on issue density (none/low/medium/high)</li>
            <li><strong>IMPROVED: Touch Support</strong> - Touch gestures work on mobile devices</li>
            <li><strong>IMPROVED: Dark Mode</strong> - Full compatibility with dark mode theme</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.119 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Document Filter Fix & Help Documentation Overhaul</strong></p>
        <ul>
            <li><strong>FIX: Document Filter Dropdown</strong> - Now correctly filters roles by document in Roles Studio</li>
            <li><strong>FIX: CSS Selector Bug</strong> - Fixed roles tab switching (.roles-nav-btn.active → .roles-nav-item.active)</li>
            <li><strong>IMPROVED: Help Modal Sizing</strong> - Now 85vw × 80vh (3/4 screen) with opaque backdrop</li>
            <li><strong>DOCS: Comprehensive Help Overhaul</strong> - Major documentation updates including:</li>
            <li style="margin-left: 20px;"><em>Fix Assistant v2</em> - New complete section with overview, features, shortcuts, workflow</li>
            <li style="margin-left: 20px;"><em>Hyperlink Health</em> - New section with validation results, status codes</li>
            <li style="margin-left: 20px;"><em>Batch Processing</em> - New section with queue management, results view</li>
            <li style="margin-left: 20px;"><em>Quality Checkers</em> - Expanded with complete checker list table (13 modules)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.116 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Memory & Stability Fixes - All Medium-Priority Bugs Resolved</strong></p>
        <ul>
            <li><strong>FIX: Batch Memory (BUG-M02)</strong> - Files now stream to disk in 8KB chunks instead of loading entirely into memory</li>
            <li><strong>FIX: SessionManager Growth (BUG-M03)</strong> - Added automatic cleanup thread that runs hourly to remove sessions older than 24 hours</li>
            <li><strong>FIX: Batch Error Context (BUG-M04)</strong> - Full tracebacks now logged for batch processing errors (debug mode shows in response)</li>
            <li><strong>FIX: localStorage Key Collision (BUG-M05)</strong> - Fix Assistant progress now uses unique document IDs via hash of filename + size + timestamp</li>
            <li><strong>NEW: Batch Limits</strong> - MAX_BATCH_SIZE (10 files) and MAX_BATCH_TOTAL_SIZE (100MB) constants now enforced</li>
            <li><strong>NEW: SessionManager.start_auto_cleanup()</strong> - Configurable interval and max age for automatic session cleanup</li>
            <li><strong>NEW: FixAssistantState.generateDocumentId()</strong> - Creates collision-free storage keys for progress persistence</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release resolves all 4 remaining medium-priority bugs from the bug tracker.
            The application now has zero critical or medium-severity open issues.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.115 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Document Type Profiles - Custom Checker Configuration</strong></p>
        <ul>
            <li><strong>FEATURE: Document Type Profiles</strong> - Customize which checks are performed for PrOP, PAL, FGOST, SOW, and other document types</li>
            <li><strong>NEW: Settings &gt; Document Profiles tab</strong> - Visual grid to enable/disable individual checkers per document type</li>
            <li><strong>NEW: Custom profiles persist</strong> - Saved in localStorage, user-specific across sessions</li>
            <li><strong>NEW: Profile management buttons</strong> - Select All, Clear All, Reset to Default</li>
            <li><strong>NEW: First-time user prompt</strong> - Option to configure document profiles on initial app launch</li>
            <li><strong>ENH: applyPreset uses custom profiles</strong> - When available, document type presets use your custom checker configuration</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.110 <span class="changelog-date">February 1, 2026</span></h3>
        <p><strong>Hyperlink Validator Export - Highlighted Documents</strong></p>
        <ul>
            <li><strong>FEATURE: Export Highlighted DOCX</strong> - Broken links marked in red/yellow with strikethrough</li>
            <li><strong>FEATURE: Export Highlighted Excel</strong> - Broken link rows highlighted with red background</li>
            <li><strong>NEW: API endpoints</strong> - /api/hyperlink-validator/export-highlighted/docx and /excel</li>
            <li><strong>NEW: Export button</strong> - "Export Highlighted" button in Hyperlink Validator modal (enabled after validation)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.109 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Bug Squash Complete - All 15 Issues Resolved</strong></p>
        <ul>
            <li><strong>FIX: Batch Modal (Issue #1)</strong> - Modal now opens correctly (removed inline style override)</li>
            <li><strong>FIX: Hyperlink Extraction (Issue #2)</strong> - Now extracts HYPERLINK field codes from DOCX files</li>
            <li><strong>FIX: Acronym Highlighting (Issue #3)</strong> - Uses word boundary regex to prevent false positives (e.g., "NDA" in "standards")</li>
            <li><strong>FIX: Fix Assistant Premium (Issue #4)</strong> - Complete implementation with close button, navigation, keyboard shortcuts, and progress tracking</li>
            <li><strong>FIX: Statement Forge (Issue #5)</strong> - "No document loaded" error fixed with consistent state checks</li>
            <li><strong>FIX: Scan History Endpoints (Issue #6)</strong> - Added /api/scan-history/stats, /clear, and /recall endpoints</li>
            <li><strong>FIX: Triage Mode (Issue #7)</strong> - State.documentId now set after fresh review</li>
            <li><strong>FIX: Document Filter (Issue #8)</strong> - Now populates from scan history</li>
            <li><strong>FIX: Role-Document Matrix (Issue #9)</strong> - Improved response validation with retry button</li>
            <li><strong>FIX: Export Modal Badges (Issue #10)</strong> - Badges now wrap and truncate properly</li>
            <li><strong>FIX: Comment Placement (Issue #11)</strong> - Smart quote normalization and multi-strategy text matching</li>
            <li><strong>FIX: Version History (Issue #12)</strong> - Added missing version entries</li>
            <li><strong>FIX: Updater Rollback (Issue #13)</strong> - Uses correct endpoint, button state fixed</li>
            <li><strong>FIX: "No Updates" Styling (Issue #14)</strong> - Proper empty state with centered icon</li>
            <li><strong>FIX: Logo 404 (Issue #15)</strong> - Fixed missing logo reference</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release resolves all issues from the v3.0.108 bug tracker.
            Comprehensive fixes across UI, backend APIs, and document processing.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.108 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Document Filter Fix</strong></p>
        <ul>
            <li><strong>FIX: Document filter dropdown</strong> - Now populates with scanned document names (BUG-009)</li>
            <li><strong>FIX: source_documents field</strong> - Added source_documents field to role extraction data</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.107 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Role Studio Fixes</strong></p>
        <ul>
            <li><strong>FIX: Role Details tab</strong> - Now shows sample_contexts from documents (BUG-007)</li>
            <li><strong>FIX: Role-Doc Matrix</strong> - Shows helpful guidance when empty instead of stuck loading (BUG-008)</li>
            <li><strong>UX: Matrix tab guidance</strong> - Explains how to populate cross-document data</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.106 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Fix Assistant Document Viewer Fix</strong></p>
        <ul>
            <li><strong>FIX: Document Viewer empty</strong> - paragraphs/page_map/headings now returned from core.py (BUG-006)</li>
            <li><strong>FIX: Deprecated datetime.utcnow()</strong> - Remaining deprecated calls fixed in config_logging.py (BUG-M01)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.105 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>API & Mode Handling Fixes</strong></p>
        <ul>
            <li><strong>FIX: Report generator API signature</strong> - generate() now returns bytes when output_path not provided (BUG-001)</li>
            <li><strong>FIX: Learner stats endpoint</strong> - Now uses standard {success, data} response envelope (BUG-002)</li>
            <li><strong>FIX: Acronym checker mode handling</strong> - Strict mode now properly flags common acronyms (BUG-003)</li>
            <li><strong>FIX: Role classification tiebreak</strong> - 'Report Engineer' now correctly classified as role (BUG-004)</li>
            <li><strong>FIX: Comment pack location hints</strong> - Now includes location hints from hyperlink_info (BUG-005)</li>
            <li><strong>MAINT: Updated deprecated datetime.utcnow()</strong> - Changed to datetime.now(timezone.utc) (WARN-001)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.104 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Fix Assistant v2 Load Fix</strong></p>
        <ul>
            <li><strong>FIX: Fix Assistant v2 load failure</strong> - BodyText style conflict resolved</li>
            <li><strong>FIX: Logger reserved keyword conflict</strong> - Fixed conflict in static file security</li>
            <li><strong>TEST: Updated test expectations</strong> - Fixed static file security response tests</li>
            <li><strong>TEST: Fixed CSS test locations</strong> - Updated for modularized stylesheets</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.103 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Parallel Refactoring Release - Code Quality & Security</strong></p>
        <ul>
            <li><strong>SECURITY: innerHTML Safety Audit (Task A)</strong> - All 143 innerHTML usages audited, documented with // SAFE comments, and verified for proper escaping</li>
            <li><strong>REFACTOR: CSS Modularization (Task B)</strong> - Split 13,842-line style.css into 10 logical modules for better maintainability</li>
            <li><strong>QUALITY: Test Suite Modernization (Task C)</strong> - Added docstrings to all 117 test methods, 3 new test classes for FAV2 API coverage</li>
            <li><strong>QUALITY: Exception Handling (Task D)</strong> - Refined exception handling with specific catches, consistent api_error_response usage</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release was produced using parallel development - 4 simultaneous refactoring streams 
            merged into a single release. Zero merge conflicts due to clear file ownership boundaries.
            CSS now loads as modular files for improved caching and maintenance.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.102 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Stabilization Release</strong></p>
        <ul>
            <li><strong>STABILIZATION:</strong> Intermediate release between 3.0.101 and 3.0.103</li>
            <li><strong>FIX:</strong> Minor adjustments to error handling patterns</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.101 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Code Review Completion Release</strong></p>
        <ul>
            <li><strong>REFACTOR: Standardized API Error Responses (ISSUE-004)</strong> - All API errors now return consistent format with error codes and correlation IDs</li>
            <li><strong>REFACTOR: Centralized Document Detection (ISSUE-008)</strong> - Created get_document_extractor() helper to eliminate code duplication</li>
            <li><strong>REFACTOR: Centralized Strings (ISSUE-009)</strong> - User-facing messages now in STRINGS constant for consistency and future i18n</li>
            <li><strong>DOCS: JSDoc Documentation (ISSUE-010)</strong> - Added comprehensive JSDoc comments to DocumentViewer and MiniMap modules</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release completes all 12 issues from the comprehensive code review audit.
            Combined with v3.0.100, all high, medium, and low priority items have been addressed.
            The application maintains full backward compatibility.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.100 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Code Review Hardening Release</strong></p>
        <ul>
            <li><strong>SECURITY: ReDoS Protection (ISSUE-001)</strong> - Added safe regex wrappers with input length limiting to prevent CPU exhaustion attacks</li>
            <li><strong>PERFORMANCE: Database Optimization (ISSUE-002)</strong> - Enabled WAL mode for better concurrent read/write performance</li>
            <li><strong>PERFORMANCE: Large File Protection (ISSUE-003)</strong> - Added file size validation (100MB limit) with helpful error messages</li>
            <li><strong>SECURITY: Input Validation (ISSUE-005)</strong> - Enhanced validation on learner dictionary API (length limits, character restrictions)</li>
            <li><strong>FIX: State Pollution (ISSUE-006)</strong> - State.entities now properly reset when loading new documents</li>
            <li><strong>FIX: Memory Leak Prevention (ISSUE-007)</strong> - Added cleanup() function to FixAssistantState to clear event listeners</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release implements fixes from a comprehensive code review audit. 
            7 of 12 identified issues were addressed (2 high priority, 4 medium, 1 low). 
            No critical issues were found during the review. The application is production-ready.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.98 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Bug Fixes and Role Studio Enhancements</strong></p>
        <ul>
            <li><strong>FIX: Export modal crash (BUG-002)</strong> - Fixed crash when opening export modal in certain scenarios</li>
            <li><strong>FIX: Context highlighting (BUG-003)</strong> - Fixed context showing wrong text in Fix Assistant</li>
            <li><strong>FIX: Hyperlink status panel (BUG-004)</strong> - Restored hyperlink validation results display</li>
            <li><strong>FIX: Role-Document matrix (BUG-009)</strong> - Restored Role-Document Matrix tab in Role Studio</li>
            <li><strong>FIX: Double browser tab (BUG-001)</strong> - Fixed duplicate browser tabs on startup</li>
            <li><strong>NEW: Role Details context preview (BUG-007)</strong> - Shows where roles appear in documents with highlighted context</li>
            <li><strong>NEW: Document filter dropdown (BUG-008)</strong> - Filter Role Studio by source document</li>
            <li><strong>NEW: Role name highlighting</strong> - Role names highlighted within context text for easy identification</li>
            <li><strong>IMPROVED: Version history completeness (BUG-005)</strong> - Added missing version entries</li>
            <li><strong>IMPROVED: Lessons learned documentation (BUG-006)</strong> - Comprehensive updates to TWR_LESSONS_LEARNED.md</li>
        </ul>
        <div class="changelog-note">
            <strong>Note:</strong> This release focuses on stability fixes and Role Studio improvements 
            from parallel development integration. Role Studio now includes document filtering and 
            rich context previews for each extracted role.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.97 <span class="changelog-date">January 28, 2026</span></h3>
        <p><strong>Fix Assistant v2 - Premium Document Review Interface</strong></p>
        <ul>
            <li><strong>NEW: Two-panel document viewer</strong> - Left panel shows document with page navigation and text highlighting</li>
            <li><strong>NEW: Mini-map overview</strong> - Visual document overview showing fix positions by confidence tier</li>
            <li><strong>NEW: Full undo/redo</strong> - Unlimited undo/redo for all review decisions</li>
            <li><strong>NEW: Search and filter</strong> - Filter fixes by text, category, severity, or confidence</li>
            <li><strong>NEW: Progress persistence</strong> - Auto-saves progress; continue where you left off</li>
            <li><strong>NEW: Pattern learning</strong> - Learns from your decisions to improve future suggestions</li>
            <li><strong>NEW: Custom dictionary</strong> - Add terms to always skip (e.g., proper nouns)</li>
            <li><strong>NEW: Live preview mode</strong> - See changes inline as you review</li>
            <li><strong>NEW: Split-screen diff</strong> - Compare original vs. fixed document side-by-side</li>
            <li><strong>NEW: PDF summary reports</strong> - Generate professional PDF reports of your review session</li>
            <li><strong>NEW: Accessibility</strong> - High contrast mode, screen reader support, keyboard navigation</li>
            <li><strong>NEW: Sound effects</strong> - Optional audio feedback for actions; toggle with 🔇 button in header</li>
            <li><strong>ENH: Keyboard shortcuts</strong> - A=accept, R=reject, S=skip, U=undo, arrows=navigate</li>
            <li><strong>ENH: Export improvements</strong> - Accepted fixes → track changes; Rejected fixes → comments with notes</li>
            <li>API: Added /api/learner/* endpoints for pattern learning</li>
            <li>API: Added /api/report/generate for PDF report generation</li>
        </ul>
        <div class="changelog-note">
            <strong>Tip:</strong> Press <kbd>?</kbd> in Fix Assistant to see all keyboard shortcuts. 
            Click the speaker icon to enable sound effects.
            The mini-map shows green (safe), yellow (review), and orange (manual) markers for quick navigation.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.96 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Fix Assistant v1 - Initial Premium Triage Interface</strong></p>
        <ul>
            <li><strong>NEW: Fix Assistant</strong> - Premium triage-style interface for reviewing automatic fixes</li>
            <li><strong>NEW: Keyboard shortcuts</strong> - A=accept, R=reject, S=skip, arrow keys to navigate</li>
            <li><strong>NEW: Confidence tiers</strong> - Safe (green), Review (yellow), Caution (orange) for each fix</li>
            <li><strong>NEW: Context display</strong> - Shows surrounding text with highlighted change location</li>
            <li><strong>NEW: Before/After comparison</strong> - Clear visual distinction between original and proposed</li>
            <li><strong>NEW: Bulk actions</strong> - Accept All Safe, Accept All, Reject All for efficiency</li>
            <li>ENH: Export now uses Fix Assistant selections instead of all fixes</li>
            <li>ENH: Progress tracking shows reviewed/total count</li>
            <li>UI: Premium styling with confidence badges, progress bar, keyboard hints</li>
        </ul>
        <div class="changelog-note">
            <strong>Foundation:</strong> This version introduced the core Fix Assistant concept that was 
            expanded to the full two-panel interface in v3.0.97.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.95 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>UI Improvements - Version Consistency, Heatmap Interactivity, Hyperlink Display</strong></p>
        <ul>
            <li><strong>FIX: Version display consistency</strong> - All UI components now show same version</li>
            <li><strong>FIX: About section simplified</strong> - Shows only author name as requested</li>
            <li><strong>FIX: Heatmap clicking</strong> - Category × Severity heatmap now properly filters issues on click</li>
            <li><strong>NEW: Hyperlink status panel</strong> - Visual display of all checked hyperlinks and their validation status</li>
            <li>ENH: Section heatmap click-to-filter now shows toast feedback</li>
            <li>ENH: Rich context (page, section, highlighting) from v3.0.94 included</li>
        </ul>
        <div class="changelog-note">
            <strong>Heatmap Fix:</strong> The issue heatmap now uses the correct setChartFilter function 
            to filter the issues list when cells are clicked. Previously this feature was broken due to 
            a missing function reference.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.93 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Acronym False Positive Reduction</strong></p>
        <ul>
            <li><strong>ACRONYM: Added 100+ common ALL CAPS words</strong> to COMMON_CAPS_SKIP list</li>
            <li><strong>ACRONYM: PDF word fragment detection</strong> - Identifies broken words from extraction</li>
            <li>TESTING: Reduced false positive acronym flagging by approximately 55%</li>
        </ul>
        <div class="changelog-note">
            <strong>Context:</strong> PDF extraction sometimes produces word fragments that look like 
            acronyms but are actually broken words. This version adds detection patterns to filter these.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.92 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>PDF Processing Improvements</strong></p>
        <ul>
            <li><strong>FIXED: PDF punctuation false positives</strong> - Better handling of PDF extraction artifacts</li>
            <li><strong>FIXED: Acronym false positives</strong> - Improved filtering of legitimate capitalized text</li>
            <li><strong>ADDED: PDF hyperlink extraction</strong> - Uses PyMuPDF (fitz) for extracting URLs from PDFs</li>
        </ul>
        <div class="changelog-note">
            <strong>PyMuPDF Integration:</strong> PDF hyperlinks are now extracted and validated alongside 
            Word document hyperlinks, providing complete link health analysis across document types.
        </div>
    </div>

    <div class="changelog-version">
        <h3>v3.0.91d <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Critical Bug Fixes - Role Extraction & Update Manager</strong></p>
        <ul>
            <li><strong>FIX: False positive filtering bug</strong> - "Mission Assurance", "Verification Engineer" now properly blocked</li>
            <li><strong>FIX: Update manager path detection</strong> - No longer hardcodes "app" folder name</li>
            <li><strong>IMPROVED: Role extraction precision</strong> - 94.7% precision, 92.3% F1 score across 4-document test suite</li>
            <li>NEW: updates/ folder with UPDATE_README.md documentation</li>
            <li>NEW: backups/ folder for automatic backup storage</li>
            <li>ENH: UpdateConfig supports flat mode (updates inside app folder)</li>
            <li>ENH: Auto-detection of app directory for various installation layouts</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.91c <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Cross-Document Verification & Role Expansion</strong></p>
        <ul>
            <li>VERIFIED: 100% F1 score on government SOW document</li>
            <li>VERIFIED: 95% F1 score on Smart Columbus SEMP</li>
            <li>NEW: Agile/Scrum roles (scrum master, product owner, agile team)</li>
            <li>NEW: Executive roles (CTO, CIO, CEO, COO, CFO, CINO)</li>
            <li>NEW: IT roles (IT PM, consultant, business owner)</li>
            <li>NEW: Support roles (stakeholder, subject matter expert, sponsor)</li>
            <li>FIX: Additional noise patterns filtered (responsible, accountable, serves)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.91b <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Major Role Extraction Accuracy Improvement</strong></p>
        <ul>
            <li>IMPROVED: Precision from 52% to 100% on government SOW test document</li>
            <li>IMPROVED: F1 Score from 68% to 97%</li>
            <li>FIX: Eliminated 32 false positives in test document</li>
            <li>NEW: Expanded FALSE_POSITIVES list (50+ new entries)</li>
            <li>NEW: SINGLE_WORD_EXCLUSIONS set for single-word filtering</li>
            <li>ENH: Enhanced _is_valid_role() with noise pattern detection</li>
            <li>ENH: Valid acronyms check (COR, PM, SE, etc.)</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.91 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Docling Integration - AI-Powered Document Extraction</strong></p>
        <ul>
            <li>NEW: <strong>Docling integration</strong> for superior document parsing (IBM open-source)</li>
            <li>NEW: AI-powered table structure recognition (TableFormer model)</li>
            <li>NEW: Layout understanding preserves document reading order</li>
            <li>NEW: Section and heading detection without relying on styles</li>
            <li>NEW: Unified extraction for PDF, DOCX, PPTX, XLSX, HTML</li>
            <li>NEW: <strong>100% air-gapped operation</strong> - no network access after setup</li>
            <li>NEW: Memory optimization - image processing disabled by default</li>
            <li>NEW: setup_docling.bat for easy Docling installation with offline config</li>
            <li>NEW: bundle_for_airgap.ps1 for complete offline deployment packages</li>
            <li>NEW: /api/docling/status endpoint for checking Docling configuration</li>
            <li>IMPROVED: Role extraction accuracy with table-based confidence boosting</li>
            <li>IMPROVED: RACI matrix detection from table structures</li>
            <li>IMPROVED: Enhanced paragraph metadata for better context</li>
            <li>NOTE: Docling is optional - gracefully falls back to pdfplumber/python-docx</li>
        </ul>
        <div class="changelog-note">
            <strong>Air-Gap Installation:</strong> Run setup_docling.bat (requires internet once), or use 
            bundle_for_airgap.ps1 to create a transferable offline package. Docling requires 
            ~2.7GB disk space (packages + AI models). All operations run locally with no network access.
        </div>
    </div>
    <div class="changelog-version">
        <h3>v3.0.90 <span class="changelog-date">January 27, 2026</span></h3>
        <p><strong>Comprehensive Merge - All v3.0.76-89 Fixes</strong></p>
        <ul>
            <li>MERGED: All fixes from v3.0.76-v3.0.89 properly consolidated</li>
            <li>INCLUDES: Iterative pruning (MIN_CONNECTIONS=2)</li>
            <li>INCLUDES: Dashed lines for role-role connections</li>
            <li>INCLUDES: Dimmed opacity fixes (0.5/0.4/0.3)</li>
            <li>INCLUDES: Export dropdown with All/Current/JSON options</li>
            <li>INCLUDES: roles-export-fix.js module</li>
            <li>INCLUDES: table_processor.py + deployment scripts</li>
            <li>FIX: Patches were building from different bases - now unified</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.85 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Role Export Fix - Correct Module</strong></p>
        <ul>
            <li>FIX: Role export now works - created roles-export-fix.js module</li>
            <li>ROOT CAUSE: button-fixes.js handled click but had no export logic</li>
            <li>ROOT CAUSE: Role Details uses /api/roles/aggregated API, not window.State</li>
            <li>SOLUTION: New module fetches from same API that Role Details tab uses</li>
            <li>NEW: TWR.exportRolesCSV() exposed for manual testing in console</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.84 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Export Fix Attempt - Wrong File</strong></p>
        <ul>
            <li>ATTEMPTED: Fixed getState() priority order in roles.js</li>
            <li>ATTEMPTED: Export uses 3-path fallback for State access</li>
            <li>NOTE: Fix was in wrong file - export button handled by button-fixes.js</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.83 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Debug Build - Export Diagnostics</strong></p>
        <ul>
            <li>DEBUG: Added console logging to exportCurrentDocumentCSV()</li>
            <li>DEBUG: Logs State object, State.roles, rolesData, roleEntries</li>
            <li>DIAGNOSTIC: Use browser DevTools (F12) Console to see debug output</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.82 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Export Fix Attempt - Same Data Source as UI</strong></p>
        <ul>
            <li>FIX: Export Current Document now uses same data source as Role Details tab</li>
            <li>FIX: Uses State.roles?.roles || State.roles pattern matching UI display</li>
            <li>NOTE: Issue persisted - root cause found in v3.0.84</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.81 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Export Fix</strong></p>
        <ul>
            <li>FIX: Export Current Document now correctly uses backend session data</li>
            <li>FIX: Improved error messages when no roles available</li>
            <li>FIX: Export All Roles gives clearer feedback about database state</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.80 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Roles Export Functionality</strong></p>
        <ul>
            <li>NEW: Export dropdown in Roles & Responsibilities Studio header</li>
            <li>NEW: Export All Roles (CSV) - all roles across all scanned documents</li>
            <li>NEW: Export Current Document (CSV) - roles from currently loaded document</li>
            <li>NEW: Export Selected Document - pick a document from history to export</li>
            <li>NEW: Export All Roles (JSON) - full role data in JSON format</li>
            <li>API: Added /api/scan-history/document/&lt;id&gt;/roles endpoint</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.79 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Dimmed Node Visibility Fix</strong></p>
        <ul>
            <li>FIX: Dimmed nodes now visible - opacity increased from 0.3 to 0.5</li>
            <li>FIX: Dimmed node labels now visible (was completely hidden)</li>
            <li>FIX: Dimmed links more visible - opacity from 0.1 to 0.3</li>
            <li>ROOT CAUSE: CSS .dimmed class had opacity too low</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.78 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Weak Node Visibility Fix</strong></p>
        <ul>
            <li>FIX: Weak nodes now properly visible using SVG fill-opacity attribute</li>
            <li>FIX: Minimum node size increased to 10px for better visibility</li>
            <li>FIX: Weak node stroke width increased to 2.5px with dashed pattern</li>
            <li>ROOT CAUSE: Hex opacity suffix (#color80) doesn't work in SVG</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.77 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Self-Explanatory Graph Visualization</strong></p>
        <ul>
            <li>ENH: All connected nodes now visible - weak nodes have dashed outline</li>
            <li>ENH: Role-Role links (co-occurrence) now use dashed purple lines</li>
            <li>ENH: Role-Document links (appears in) use solid blue lines</li>
            <li>ENH: Legend explains node size, line thickness, and connection strength</li>
            <li>ENH: First-time hint banner with interaction tips</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.76 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Phantom Lines Fix + Document Log Fix</strong></p>
        <ul>
            <li>FIX: Phantom lines eliminated - no more lines going to barely-visible nodes</li>
            <li>FIX: Document Log now shows correct role count (was showing 0 for all)</li>
            <li>FIX: Nodes now require minimum 2 connections to be displayed</li>
            <li>ENH: Iterative pruning removes cascading weak connections</li>
            <li>ROOT CAUSE (graph): v3.0.75 only removed orphans (0 connections), not peripheral nodes</li>
            <li>ROOT CAUSE (doc log): Backend get_scan_history() was missing role_count field</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.75 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Orphan Nodes Fix</strong></p>
        <ul>
            <li>FIX: Disconnected nodes (floating circles) no longer appear in graph</li>
            <li>FIX: Only nodes with at least one connection are now displayed</li>
            <li>ENH: Graph shows only meaningful connected clusters</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.74 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Dangling Links Fix v2 + Enhanced Info Panel</strong></p>
        <ul>
            <li>FIX: Dangling graph links - added coordinate validation in tick handler</li>
            <li>FIX: Invalid links now hidden with display:none</li>
            <li>ENH: Graph info panel shows detailed stats with visual progress bars</li>
            <li>ENH: Separate sections for document vs role connections</li>
            <li>ENH: Built-in legend explains graph elements</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.73 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Graph Info Panel & Dangling Links Fixes</strong></p>
        <ul>
            <li>FIX: Pin selection button now works in graph info panel</li>
            <li>FIX: Close (X) button now works in graph info panel</li>
            <li>FIX: Dangling graph links - lines no longer connect to empty space</li>
            <li>FIX: Update manager now supports all file types and directories</li>
            <li>ROOT CAUSE: Links were rendered without validating both endpoints exist</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.72 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Full Height Content Fix</strong></p>
        <ul>
            <li>FIX: Tab content areas now fill available vertical space</li>
            <li>FIX: Relationship Graph expands to fill modal height</li>
            <li>FIX: RACI Matrix and Adjudication lists use full height</li>
            <li>ENH: All sections use flex layout for proper expansion</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.71 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Horizontal Tabs Navigation</strong></p>
        <ul>
            <li>FIX: Navigation now displays as horizontal tabs (not vertical sidebar)</li>
            <li>FIX: Removed width constraints from responsive breakpoints</li>
            <li>ENH: Tab styling with bottom border for active state</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.70 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Critical CSS Fix for Tab Visibility</strong></p>
        <ul>
            <li>FIX: Added missing CSS rules for .roles-section.active</li>
            <li>ROOT CAUSE: JS used .active class but CSS rules didn't exist</li>
            <li>SOLUTION: Added #modal-roles .roles-section display rules</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.69 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Responsibility Count Display Fix</strong></p>
        <ul>
            <li>FIX: "Top Roles by Responsibility Count" now shows actual responsibility count</li>
            <li>FIX: Document tag shows unique document count, not total scan count</li>
            <li>FIX: Summary cards display responsibility totals correctly</li>
            <li>ENH: Roles sorted by responsibility count (primary) then unique docs (secondary)</li>
            <li>API: Added responsibility_count and unique_document_count fields</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.68 <span class="changelog-date">January 26, 2026</span></h3>
        <p><strong>Roles Tab Visibility Fix</strong></p>
        <ul>
            <li>FIX: Roles tabs now display content properly</li>
            <li>ROOT CAUSE: CSS !important rules were overriding inline styles</li>
            <li>SOLUTION: Use classList.add('active') instead of style.display</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.66-67 <span class="changelog-date">January 25, 2026</span></h3>
        <p><strong>CSS Animation & Diagnostics</strong></p>
        <ul>
            <li>FIX: Added missing @keyframes fadeIn to CSS</li>
            <li>ENH: Added diagnostic logging to all render functions</li>
            <li>ENH: Try-catch wrappers for render error identification</li>
            <li>ENH: Container existence checks with clear error messages</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.65 <span class="changelog-date">January 24, 2026</span></h3>
        <p><strong>Graph Controls Fix</strong></p>
        <ul>
            <li>FIX: Graph search input now filters nodes</li>
            <li>FIX: Layout dropdown changes graph layout</li>
            <li>FIX: Labels dropdown controls node labels</li>
            <li>FIX: Threshold slider filters link visibility</li>
            <li>FIX: Reset/Recenter buttons work properly</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.63-64 <span class="changelog-date">January 24, 2026</span></h3>
        <p><strong>Graph Control Initialization</strong></p>
        <ul>
            <li>FIX: initGraphControls uses _tabsFixInitialized flag pattern</li>
            <li>FIX: Follows same initialization pattern as RACI, Details, Adjudication</li>
            <li>FIX: Removed dependency on TWR.Roles.initGraphControls</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.61-62 <span class="changelog-date">January 24, 2026</span></h3>
        <p><strong>Section Visibility & Graph Fallback</strong></p>
        <ul>
            <li>FIX: Section visibility uses proper display toggling</li>
            <li>FIX: Graph section visible when switching tabs</li>
            <li>ENH: initGraphControlsFallback when roles.js unavailable</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.59-60 <span class="changelog-date">January 24, 2026</span></h3>
        <p><strong>Adjudication Button & Event Handling</strong></p>
        <ul>
            <li>FIX: Adjudication button clicks now respond properly</li>
            <li>ENH: Console logging with [TWR RolesTabs] prefix</li>
            <li>ENH: Explicit handler attachment verification</li>
            <li>ENH: Improved event delegation for adjudication buttons</li>
            <li>ENH: Error boundary around click handlers</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.58 <span class="changelog-date">January 23, 2026</span></h3>
        <p><strong>Adjudication & Focus Fixes</strong></p>
        <ul>
            <li>FIX: Overview 'Documents Analyzed' shows unique documents, not total scans</li>
            <li>FIX: Role Details search/dropdown focus outline no longer cut off</li>
            <li>FIX: Adjudication search input now filters roles in real-time</li>
            <li>FIX: Adjudication filter dropdown now works</li>
            <li>FIX: Adjudication Select All checkbox works with visible items</li>
            <li>FIX: Adjudication item checkboxes no longer overlap text</li>
            <li>ENH: Form inputs/dropdowns show visible focus ring</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.57 <span class="changelog-date">January 23, 2026</span></h3>
        <p><strong>RACI Matrix Layout Enhancement</strong></p>
        <ul>
            <li>FIX: RACI counts now reflect unique documents (not scan instances)</li>
            <li>FIX: Re-scanning uses MAX(old, new) for mention counts</li>
            <li>FIX: RACI sort dropdown and Critical filter checkbox now work</li>
            <li>FIX: Role Details search and sort dropdown now work</li>
            <li>ENH: RACI table header sticky while scrolling</li>
            <li>ENH: RACI legend footer always visible</li>
            <li>ENH: Condensed layout - Role column wider, R/A/C/I columns compact</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.55-56 <span class="changelog-date">January 23, 2026</span></h3>
        <p><strong>Roles Studio Overhaul</strong></p>
        <ul>
            <li>NEW: Horizontal tab navigation replacing vertical sidebar</li>
            <li>NEW: Cross-Reference tab with Role × Document heatmap</li>
            <li>NEW: Roles Studio accessible without scanning a document</li>
            <li>NEW: Dictionary fallback when no scan data exists</li>
            <li>NEW: CSV export for Cross-Reference matrix</li>
            <li>FIX: Dictionary tab now loads data properly</li>
            <li>FIX: Tab switching shows only one section at a time</li>
            <li>FIX: RACI Matrix correctly shows R/A/C/I assignments</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.52-54 <span class="changelog-date">January 23, 2026</span></h3>
        <p><strong>Help System & Update Fixes</strong></p>
        <ul>
            <li>Complete help documentation with 44 sections</li>
            <li>Fixed CSS specificity issues in help modal</li>
            <li>Fixed "Check for Updates" element IDs</li>
            <li>Added showRollbackConfirm function</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.51 <span class="changelog-date">January 23, 2026</span></h3>
        <p><strong>Update System Improvements</strong></p>
        <ul>
            <li>Auto-restart on update with browser refresh</li>
            <li>Installation progress bar</li>
            <li>Desktop shortcut icon</li>
            <li>Custom install location prompt</li>
            <li>Fixed "Check for Updates" detection</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.50 <span class="changelog-date">January 22, 2026</span></h3>
        <p><strong>Package Restructure</strong></p>
        <ul>
            <li>Native file extension support (no .txt encoding)</li>
            <li>Clean directory structure for GitHub</li>
            <li>Fixed showNodeInfoPanel error in Roles</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.48-49 <span class="changelog-date">January 2026</span></h3>
        <p><strong>Hyperlink & Role Enhancements</strong></p>
        <ul>
            <li>PowerShell URL validator with comment insertion</li>
            <li>Statement Forge integration with Roles</li>
            <li>D3.js relationship graph visualization</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v3.0.x <span class="changelog-date">January 2026</span></h3>
        <p><strong>Enterprise Architecture</strong></p>
        <ul>
            <li>Modular JavaScript architecture (TWR namespace)</li>
            <li>Event delegation for all interactions</li>
            <li>Job manager infrastructure</li>
            <li>Air-gapped deployment support</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v2.9.x <span class="changelog-date">January 2026</span></h3>
        <p><strong>Major Features</strong></p>
        <ul>
            <li>Statement Forge for requirements extraction</li>
            <li>RACI matrix generation</li>
            <li>Issue families</li>
            <li>Scan history</li>
            <li>Diagnostic export</li>
        </ul>
    </div>

    <div class="changelog-version">
        <h3>v2.8.x <span class="changelog-date">December 2025</span></h3>
        <p><strong>Foundation</strong></p>
        <ul>
            <li>Core 50+ quality checkers</li>
            <li>Track changes export</li>
            <li>Dark mode</li>
        </ul>
    </div>
</div>
`
};

// ============================================================================
// ABOUT
// ============================================================================
HelpDocs.content['about'] = {
    title: 'About AEGIS',
    subtitle: 'Enterprise technical document analysis tool',
    html: `
<div class="help-about">
    <div class="help-about-header">
        <div class="help-about-logo"><i data-lucide="file-search"></i></div>
        <div class="help-about-info">
            <h2>AEGIS</h2>
            <p class="help-version-display"><strong id="about-version-display">Version</strong></p>
            <p>Build Date: February 9, 2026</p>
        </div>
    </div>

    <h2><i data-lucide="target"></i> Purpose</h2>
    <p>Enterprise-grade technical writing review tool designed for government and aerospace documentation. Analyzes documents for quality issues, standards compliance, and organizational clarity—all offline, all local.</p>

    <h2><i data-lucide="user"></i> Created By</h2>
    <p><strong>Nicholas Georgeson</strong></p>

    <h2><i data-lucide="code"></i> Technology Stack</h2>
    <div class="help-tech-stack">
        <div class="help-tech-item">
            <strong>Backend</strong>
            <span>Python 3.10+ / Flask / Waitress</span>
        </div>
        <div class="help-tech-item">
            <strong>Frontend</strong>
            <span>Vanilla JavaScript / HTML5 / CSS3</span>
        </div>
        <div class="help-tech-item">
            <strong>Visualization</strong>
            <span>Chart.js / D3.js</span>
        </div>
        <div class="help-tech-item">
            <strong>Document Processing</strong>
            <span>Docling (AI) / mammoth / pymupdf4llm / python-docx / pdfplumber</span>
        </div>
        <div class="help-tech-item">
            <strong>Icons</strong>
            <span>Lucide Icons</span>
        </div>
    </div>

    <h2><i data-lucide="sparkles"></i> Docling Status</h2>
    <div id="docling-status-container">
        <p><em>Checking Docling status...</em></p>
    </div>
    <script>
    (function() {
        // v4.7.0: All version displays pull from /api/version (single source: version.json)
        setTimeout(function() {
            const versionEl = document.getElementById('about-version-display');
            if (versionEl) {
                fetch('/api/version')
                    .then(r => r.ok ? r.json() : null)
                    .then(data => {
                        if (data && data.app_version) {
                            versionEl.textContent = 'Version ' + data.app_version;
                        }
                    })
                    .catch(() => {});
            }
        }, 50);
        
        // BUG-M22 FIX: Add timeout and better error handling for Docling status check
        setTimeout(function() {
            const container = document.getElementById('docling-status-container');
            if (!container) return;

            // Create an AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

            fetch('/api/docling/status', { signal: controller.signal })
                .then(r => {
                    clearTimeout(timeoutId);
                    if (!r.ok) throw new Error('Status check failed');
                    return r.json();
                })
                .then(status => {
                    const available = status.available || status.docling_available;
                    const backend = status.backend || status.extraction_backend || 'unknown';
                    const version = status.version || status.docling_version || 'N/A';
                    const offline = status.offline_ready !== false;

                    container.innerHTML = \`
                        <table class="help-table" style="margin-top: 0;">
                            <tr>
                                <td><strong>Status</strong></td>
                                <td>\${available ? '<span style="color: #22c55e;">✓ Available</span>' : '<span style="color: #f59e0b;">○ Not Installed</span>'}</td>
                            </tr>
                            <tr>
                                <td><strong>Backend</strong></td>
                                <td>\${backend}</td>
                            </tr>
                            \${available ? \`<tr>
                                <td><strong>Version</strong></td>
                                <td>\${version}</td>
                            </tr>\` : ''}
                            <tr>
                                <td><strong>Offline Mode</strong></td>
                                <td>\${offline ? '<span style="color: #22c55e;">✓ Enabled</span>' : '<span style="color: #ef4444;">✗ Disabled</span>'}</td>
                            </tr>
                            <tr>
                                <td><strong>Image Processing</strong></td>
                                <td><span style="color: #6b7280;">Disabled (Memory Optimized)</span></td>
                            </tr>
                        </table>
                        \${!available ? '<p style="margin-top: 10px; color: #6b7280;"><i>Run setup_docling.bat to install Docling for enhanced extraction.</i></p>' : ''}
                    \`;
                })
                .catch(err => {
                    clearTimeout(timeoutId);
                    const isTimeout = err.name === 'AbortError';
                    container.innerHTML = isTimeout
                        ? '<p style="color: #f59e0b;">⚠ Status check timed out. Using legacy extraction.</p>'
                        : '<p style="color: #6b7280;">Unable to check Docling status. Using legacy extraction.</p>';
                });
        }, 100);
    })();
    </script>

    <h2><i data-lucide="heart"></i> Acknowledgments</h2>
    <p>Built with open-source tools: Flask, Docling (IBM), python-docx, pdfplumber, Chart.js, D3.js, Lucide Icons.</p>
    
    <div class="help-callout help-callout-info">
        <i data-lucide="shield"></i>
        <div>
            <strong>Air-Gapped by Design</strong>
            <p>AEGIS processes all documents locally. No data leaves your machine. Docling operates in offline mode with all AI models stored locally. Safe for classified, proprietary, and sensitive content.</p>
        </div>
    </div>
</div>
`
};

// ============================================================================
// SEARCH
// ============================================================================
HelpDocs.searchIndex = null;

HelpDocs.buildSearchIndex = function() {
    this.searchIndex = [];
    for (const [id, section] of Object.entries(this.content)) {
        const text = section.html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').toLowerCase();
        this.searchIndex.push({
            id: id,
            title: section.title,
            subtitle: section.subtitle || '',
            text: text
        });
    }
};

HelpDocs.search = function(query) {
    if (!this.searchIndex) this.buildSearchIndex();
    const q = query.toLowerCase().trim();
    if (!q) return [];
    
    const results = [];
    for (const item of this.searchIndex) {
        let score = 0;
        if (item.title.toLowerCase().includes(q)) score += 10;
        if (item.subtitle.toLowerCase().includes(q)) score += 5;
        if (item.text.includes(q)) score += 1 + (item.text.split(q).length - 1) * 0.1;
        if (score > 0) results.push({ ...item, score });
    }
    return results.sort((a, b) => b.score - a.score).slice(0, 10);
};

// ============================================================================
// INITIALIZATION
// ============================================================================
HelpDocs.init = function() {
    console.log('[HelpDocs] Initializing v' + this.version);
    this.buildSearchIndex();
    console.log('[HelpDocs] Search index built: ' + this.searchIndex.length + ' entries');
};

if (typeof window !== 'undefined') {
    window.HelpDocs = HelpDocs;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => HelpDocs.init());
    } else {
        HelpDocs.init();
    }
}

console.log('[HelpDocs] Module loaded v3.0.96');
